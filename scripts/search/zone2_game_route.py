#!/usr/bin/env python3
"""2区通用 Game 类重放（auto ON，strict live model）。

从 save1 跑 1区(current_best) + 10F boss 后补给 + 2区 canonical (best_after_mt10_boss_supply)，
auto 全开，生成 walk 供 web 验证。zone2 walk seed 来自 best/zone2_canonical_replay.json
result[1] (best_after_mt10_boss_supply, 起点 MT10 HP=722 ATK=30 DEF=30 G=305 YK=3)。

go_to 内部 auto_sweep 自动处理可达零伤怪/道具/暗墙，因此离线推导与实机 auto ON 一致。
zone2 起点 G=313（zone1 auto_sweep 多清 +8G）vs replay G=305，walk 用 Game 算的 after。
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from src.solver.game_route import Game, RouteError, go_to_decomposed, read_json, state_line, floor_no
from scripts.search.zone1_game_route import run_zone1, SAVE1

ZONE2_REPLAY = ROOT / "best" / "zone2_canonical_replay.json"
OUT_JSON = ROOT / "outputs" / "results" / "zone2_game_route.json"
OUT_MD = ROOT / "outputs" / "reports" / "zone2_game_route.md"

# 阶段性存档：1区 web 验证全过后，把浏览器存到专用槽并用
# `node scripts/live/export_save_slot_cdp.js --slot <N> --out <path>` 导出。
# zone1_end_save = boss 后、补给前（hero MT10 [6,1] HP=122 ATK=27 DEF=27 G=313）。
# --from-checkpoint 加载它可跳过 run_zone1（每会话不再从 4F 重跑 1区）。
CHECKPOINT_DIR = ROOT / "best" / "checkpoints"
ZONE1_END_CHECKPOINT = CHECKPOINT_DIR / "zone1_end_save.json"

# MT10 boss 后补给区：click [1,2] 破墙后 auto_sweep 一次清完（BFS 连通整个 MT10）
SUPPLY = [
    ((1, 3), "redGem"), ((2, 3), "redGem"), ((3, 3), "redGem"),
    ((9, 3), "blueGem"), ((10, 3), "blueGem"), ((11, 3), "blueGem"),
    ((1, 4), "bluePotion"), ((2, 4), "bluePotion"), ((3, 4), "bluePotion"),
    ((9, 4), "yellowKey"), ((10, 4), "yellowKey"), ((11, 4), "yellowKey"),
]

SHOP_KIND_MAP = {"attack": "atk", "defense": "def", "hp": "hp"}

# zone2 商人：7F/6F/15F 不在 Game.talk_trader 支持（只支持 47/45/31F），单独处理
ZONE2_TRADERS = {
    ("MT7", (6, 1)): {"cost": 50, "yk": 5, "bk": 0, "eid": "yellowKey5"},
    ("MT6", (8, 4)): {"cost": 50, "yk": 0, "bk": 1, "eid": "blueKey1"},
    ("MT15", (11, 11)): {"cost": 200, "yk": 0, "bk": 1, "eid": "blueKey1"},
    ("MT12", (1, 1)): {"cost": 800, "yk": 0, "bk": 0, "rk": 1, "eid": "redKey1"},
}


def move_adjacent_decomposed(g: Game, fid: str, x: int, y: int, note: str) -> None:
    """Reach any cardinal merchant neighbour through strict real-click blockers."""
    best = None
    before = g.snapshot()
    for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
        if not (0 <= nx < g.floors[fid].width and 0 <= ny < g.floors[fid].height):
            continue
        cand = g.clone()
        try:
            go_to_decomposed(cand, fid, nx, ny, note)
        except RouteError:
            continue
        rank = (
            before["hp"] - cand.state["hp"],
            before["yk"] - cand.state["yk"],
            before["bk"] - cand.state["bk"],
            len(cand.steps) - len(g.steps),
        )
        if best is None or rank < best[0]:
            best = (rank, cand)
    if best is None:
        g.fail(f"cannot reach merchant neighbour at {fid} x{x}y{y}")
    g.__dict__.update(best[1].__dict__)


def _find_stair(g: Game, fid: str, eid: str) -> tuple[int, int]:
    for p, b in g.floors[fid].blocks.items():
        if b and b.kind == "terrain" and b.eid == eid:
            return p
    g.fail(f"cannot find {eid} on {fid}")
    raise AssertionError("unreachable")


def _route_visited_floors(g: Game) -> set[str]:
    floors = {g.state["floor"]}
    for step in g.steps:
        before = step.get("before") or {}
        after = step.get("after") or {}
        if before.get("floor"):
            floors.add(before["floor"])
        if after.get("floor"):
            floors.add(after["floor"])
    return floors


def fly_or_walk_to_floor(g: Game, fid: str) -> None:
    """Use fly for visited floors; reach first-time floors through real stairs."""
    route_visited = _route_visited_floors(g)
    if fid in route_visited:
        g.fly(fid)
        return

    target_no = floor_no(fid)
    visited_nos = sorted(floor_no(v) for v in route_visited if v.startswith("MT"))
    lower = [n for n in visited_nos if n < target_no]
    upper = [n for n in visited_nos if n > target_no]
    lower_start = max(lower) if lower else None
    upper_start = min(upper) if upper else None
    if lower_start is None and upper_start is None:
        g.fail(f"cannot route transfer to unvisited {fid}")
        return

    use_lower = upper_start is None or (
        lower_start is not None and target_no - lower_start <= upper_start - target_no
    )
    if use_lower:
        start = lower_start
        start_fid = f"MT{start}"
        if g.state["floor"] != start_fid:
            g.fly(start_fid)
        for no in range(start, target_no):
            from_fid = f"MT{no}"
            to_fid = f"MT{no + 1}"
            stair = _find_stair(g, from_fid, "upFloor")
            g.go_to(from_fid, stair[0], stair[1], "through upFloor")
            g.transition(to_fid, f"{from_fid} -> {to_fid}")
    else:
        start = upper_start
        start_fid = f"MT{start}"
        if g.state["floor"] != start_fid:
            g.fly(start_fid)
        for no in range(start, target_no, -1):
            from_fid = f"MT{no}"
            to_fid = f"MT{no - 1}"
            stair = _find_stair(g, from_fid, "downFloor")
            g.go_to(from_fid, stair[0], stair[1], "through downFloor")
            g.transition(to_fid, f"{from_fid} -> {to_fid}")


def apply_mt10_supply(g: Game) -> None:
    """10F boss 后：click [6,9] thief 事件自动吃补给区 12 资源 + 开 11F 楼梯。
    hero [6,1] HP=122 -> [6,2] HP=722 ATK=30 DEF=30 YK=3。事件 auto-eat，不是 [1,2] 破墙。
    Game 类 MT10 地图未加载补给区资源（lazy），手动 set_block+apply；boss 后 [6,3] 事件墙
    开（spawned 清完触发），打通 [6,2]<->[6,9] 路径。run_zone2 跳过 replay step0 (事件 [6,9] thief)。"""
    # boss 后 [6,3] 事件墙开（spawned 清完触发），打通 [6,2]<->[6,9] 路径
    if g.block_at("MT10", (6, 3)) is not None:
        g.set_ground("MT10", (6, 3))
    g.set_segment("10F boss 后补给 (auto ON)")
    before = g.snapshot()
    # web 实机 click [6,9] thief 事件自动吃完整个补给区（6gem+3bluePotion+3yellowKey）。
    for pos, eid in SUPPLY:
        g.set_block("MT10", pos, "item", eid)
        g.apply_item("MT10", eid)
        g.set_ground("MT10", pos)
    g.state["x"], g.state["y"] = 6, 9  # live click leaves hero on the thief event tile
    g.record("事件", (6, 9), "thief", before,
             "10F 小偷事件：自动吃补给 6gem+3bluePotion+3yellowKey + 开 11F 楼梯")


def run_zone2(g: Game, steps: list[dict] | None = None) -> None:
    if steps is None:
        data = json.loads(ZONE2_REPLAY.read_text(encoding="utf-8"))
        steps = data["results"][1]["steps"]  # best_after_mt10_boss_supply
    g.set_segment("2区 canonical (auto ON)")
    for s in steps:
        action = s["action"]
        fid = s["floor"]
        x, y = s["pos"]
        eid = s.get("eid")
        note = s.get("note", "")
        if action == "已清理":
            continue
        if action == "事件开门":
            # specialDoor 由 after_action 在杀怪时自动开（如 MT17 yellowGuard / MT11 redPriest），
            # 不单独 step；live auto 也是杀完即开。
            continue
        if action == "事件" and fid == "MT10" and (x, y) == (6, 9):
            # 10F 小偷事件（自动吃补给 + 开 11F 楼梯）已由 apply_mt10_supply 处理
            continue
        if action == "事件奖励":
            # MT14 三兽人武士掉红钥匙：after_action set_block (1,3) redKey，hero go_to 拾取
            if fid == "MT14" and eid == "redKey":
                if g.block_at("MT14", (1, 3)) is not None:
                    g.go_to("MT14", 1, 3, "事件奖励 redKey")
                continue
            before = g.snapshot()
            g.apply_item(fid, eid)
            g.record("事件奖励", (x, y), eid, before, note)
            continue
        if action == "换层":
            # zone2 replay step.floor 是 to_floor（新楼层）。replier CHANGE_FLOOR 不 click，
            # 只校验 after floor；需先 "通过 upFloor/downFloor" 让 hero 走楼梯换层。
            if g.state["floor"] != fid:
                from_fid = g.state["floor"]
                want = "upFloor" if floor_no(fid) > floor_no(from_fid) else "downFloor"
                stair = None
                for p, b in g.floors[from_fid].blocks.items():
                    if b and b.kind == "terrain" and b.eid == want:
                        stair = p
                        break
                if stair:
                    g.go_to(from_fid, stair[0], stair[1], f"通过 {want}")
                g.transition(fid, f"{from_fid} -> {fid}")
            continue
        if action == "传送":
            # 楼层传送器（zone2 获得后可到未访问楼层，如首次 MT15）；fly 限制 visited，故先标记
            g.visited.add(fid)
            fly_or_walk_to_floor(g, fid)
            continue
        if g.state["floor"] != fid:
            g.fly(fid)
        if action in ("击杀", "拾取"):
            if g.block_at(fid, (x, y)) is None:
                continue  # canSkipMissingTarget (auto_sweep 已清)
            # 20F vampire 有伤，go_to strict_click 寻路不通，直接 apply_block（hero 站到 target）
            if fid == "MT20" and eid == "vampire":
                block = g.block_at("MT20", (x, y))
                before = g.snapshot()
                g.state["x"], g.state["y"] = x, y
                g.apply_block("MT20", (x, y), block, f"击杀 {eid}")
                continue
            # 0-dmg 敌人显式击杀：web 点击目标，hero 走到 target 击杀。不用 go_to 的
            # strict_auto_enemy_target（会 route 到相邻 + auto_sweep 清目标，记录成 "到达 [相邻]"
            # 被 converter drop，导致 web 没点目标——如 MT12 [4,11] bat 商店后没动不触发 auto，
            # 目标存活挡路）。直接 apply_block：hero 站到 target，显式 kill，record "击杀 [target]"。
            # web auto 不会在站定后多清（没动），故不补 auto_sweep，匹配 web。
            if action == "击杀":
                block = g.block_at(fid, (x, y))
                if block and block.kind == "enemy" and g.enemy_damage(eid) == 0:
                    before = g.snapshot()
                    g.state["x"], g.state["y"] = x, y
                    g.apply_block(fid, (x, y), block, f"击杀 {eid}")
                    continue
            if action == "击杀" and fid == "MT19" and (x, y) == (7, 6) and eid == "rock":
                # Live auto after the 19F rock takes the nearby keys but does
                # not break the two fakeWalls in front of the cross. Preserve
                # those explicit pass steps for web replay.
                old_wall = g.auto_flags.get("wall")
                g.auto_flags["wall"] = False
                try:
                    g.go_to(fid, x, y, f"{action} {eid}")
                finally:
                    g.auto_flags["wall"] = old_wall
                continue
            g.go_to(fid, x, y, f"{action} {eid}")
        elif action == "开门":
            g.go_to(fid, x, y, f"开门 {eid}")
        elif action in ("通过", "破墙"):
            if g.block_at(fid, (x, y)) is None:
                continue  # auto_sweep 已破 fakeWall
            g.go_to(fid, x, y, f"通过 {eid}")
        elif action == "事件":
            # NPC 事件（thief 小偷等）：hero 已相邻（前序 "对话" move_adjacent），不站到 target；
            # record 事件（地图变化如开墙由事件触发，hero 位置不变）
            if fid == "MT20" and eid == "vampire":
                # 20F 触发吸血鬼：hero 踩 [6,8] 触发事件，vampire 出现在 [6,6]。
                # web: click [6,8] → hero 走到 [6,8] → 事件触发 → vampire 生成，hero 停 [6,8]。
                before = g.snapshot()
                g.state["x"], g.state["y"] = x, y
                # The trigger is one-shot in live.  Remove its event shell now
                # so the bluePotion spawned back onto x6y8 after the boss is a
                # normal auto-pickup tile on the walk to 21F.
                g.floors["MT20"].events.pop("6,8", None)
                g.set_block("MT20", (6, 6), "enemy", "vampire")
                g.record("事件", (x, y), eid, before, note or "20F 触发吸血鬼")
                continue
            if fid == "MT15" and eid == "thief":
                # 15F 小偷事件开右上墙（[8,2] yellowWall），打通到 upFloor [6,1] 路径
                if g.block_at("MT15", (8, 2)) is not None:
                    g.set_ground("MT15", (8, 2))
            if fid == "MT16" and eid == "superPotion":
                # 16F 老人给圣水：hero 已在 [11,11]（前序 通过暗墙），superPotion +1
                before = g.snapshot()
                g.state["x"], g.state["y"] = x, y
                g.state["superPotion"] += 1
                g.set_ground("MT16", (x, y))
                g.record("老人", (x, y), "superPotion", before, note or "16F 圣水")
                continue
            hx, hy = g.state["x"], g.state["y"]
            if abs(hx - x) + abs(hy - y) > 1:
                g.move_adjacent(fid, x, y, f"事件 {eid}")
                # 改 last step action "事件"，pos 用 target (x,y)（replier pressDirection 走向 target）
                if g.steps and g.steps[-1].get("action") == "到达":
                    g.steps[-1]["action"] = "事件"
                    g.steps[-1]["eid"] = eid
                    g.steps[-1]["pos"] = [x, y]
            else:
                before = g.snapshot()
                g.record("事件", (x, y), eid, before, note or f"事件 {eid}")
        elif action == "商店":
            # 商店：hero 走到 shop 相邻（不触发 auto_sweep，避免 atk 升高后多清零伤怪导致 gold 偏移）
            hx, hy = g.state["x"], g.state["y"]
            if abs(hx - x) + abs(hy - y) > 1:
                for adj in [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]:
                    try:
                        if g.path_to(fid, adj, strict_click=True):
                            before = g.snapshot()
                            g.state["x"], g.state["y"] = adj
                            g.record("到达", adj, None, before, f"商店 {eid} 相邻")
                            break
                    except Exception:
                        continue
            kind_raw = eid.split(":")[1] if eid and ":" in eid else "attack"
            kind = SHOP_KIND_MAP.get(kind_raw, kind_raw)
            g.buy_shop(kind, 1, (x, y))
        elif action == "商人":
            spec = ZONE2_TRADERS.get((fid, (x, y)))
            if spec:
                move_adjacent_decomposed(g, fid, x, y, f"商人 {eid}")
                before = g.snapshot()
                if g.state["gold"] < spec["cost"]:
                    g.fail(f"not enough gold for trader {fid} {x},{y}: have={g.state['gold']}")
                g.state["gold"] -= spec["cost"]
                g.state["yk"] += spec["yk"]
                g.state["bk"] += spec["bk"]
                g.state["rk"] += spec.get("rk", 0)
                g.record("商人", (x, y), spec["eid"], before, note or f"{fid} 商人 {spec['cost']}G")
            else:
                g.talk_trader(fid, x, y, note)
        elif action == "对话":
            g.move_adjacent(fid, x, y, f"对话 {eid}")
        elif action == "使用道具":
            # .md "使用道具 圣水"：用 superPotion（HP += floor((atk+def)*0.74+0.5)*10）。
            # hero 走到 target 相邻（target 可能是 use 站位，非道具格）。
            hx, hy = g.state["x"], g.state["y"]
            if abs(hx - x) + abs(hy - y) > 1:
                g.move_adjacent(fid, x, y, f"使用道具 {eid}")
            if eid == "superPotion":
                g.use_super_potion(note or "16F 圣水 +HP")
            else:
                g.fail(f"未支持的 使用道具 eid: {eid} {fid} {x},{y}")
        else:
            print(f"UNKNOWN action: {action} {fid} {x},{y} {eid}")


def _parse_checkpoint_arg() -> Path | None:
    """--from-checkpoint PATH：从 1区末阶段性存档恢复，跳过 run_zone1。"""
    for i, a in enumerate(sys.argv):
        if a == "--from-checkpoint" and i + 1 < len(sys.argv):
            return Path(sys.argv[i + 1])
        if a.startswith("--from-checkpoint="):
            return Path(a.split("=", 1)[1])
    return None


def main() -> int:
    checkpoint = _parse_checkpoint_arg()
    if checkpoint is not None:
        # 阶段性存档恢复：跳过 run_zone1，从 1区末存档直接 apply_mt10_supply + run_zone2。
        g = Game(read_json(checkpoint))
        g.strict_live_model = True
        g.auto_flags = {"battle": True, "item": True, "wall": True}
        print(f"from-checkpoint={checkpoint} (skip run_zone1)")
        try:
            apply_mt10_supply(g)
            run_zone2(g)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"EXCEPTION: {type(e).__name__}: {e}")
    else:
        g = Game(read_json(SAVE1))
        g.strict_live_model = True
        g.auto_flags = {"battle": True, "item": True, "wall": True}
        try:
            run_zone1(g)
            apply_mt10_supply(g)
            run_zone2(g)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"EXCEPTION: {type(e).__name__}: {e}")
    print(f"ok={not g.errors}")
    print(
        f"final={state_line(g.state)} {g.state['floor']} "
        f"x{g.state['x']}y{g.state['y']} dmg={g.state['dmg']} "
        f"door={g.state['yd']}/{g.state['bd']}/{g.state['rd']}"
    )
    if g.errors:
        for e in g.errors[:20]:
            print("ERR", e)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(
        json.dumps(
            {
                "ok": not g.errors,
                "final": g.snapshot(),
                "steps": g.steps,
                "errors": g.errors,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"json={OUT_JSON} steps={len(g.steps)}")
    return 0 if not g.errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
