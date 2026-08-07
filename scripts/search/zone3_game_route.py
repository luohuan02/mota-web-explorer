#!/usr/bin/env python3
"""3区通用 Game 类重放（auto ON, item=nopotion）。

从 zone3 桥存档 (MT31, save38) 起，回放 guide walk (best/zone3_guide_slot36_to_40_walk.json)
的 MT31-40 段，auto = {battle, wall} + item="nopotion"（4区半血陷阱前控血）。

guide walk 起点 MT31 HP=1276 ATK=78 DEF=64 G=864 YK=8（guide baseline）；
current_best 起点 MT31 HP=1403 ATK=78 DEF=64 G=1011 YK=6（HP+127 G+147 YK-2）。
ATK/DEF 同 → 怪物伤害同；YK-2 + zone2 清理差异 → 可能在黄门/飞回拾取处发散。
本脚本探查发散点，为 MT31-40 适配/重搜提供依据。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.solver.game_route import Game, go_to_decomposed, read_json, state_line, floor_no

GUIDE_WALK = ROOT / "best" / "zone3_guide_slot36_to_40_walk.json"
CHECKPOINT_DIR = ROOT / "best" / "checkpoints"
ZONE3_BRIDGE_CHECKPOINT = CHECKPOINT_DIR / "zone3_bridge_mt31_save.json"
OUT_JSON = ROOT / "outputs" / "results" / "zone3_game_route.json"
OUT_MD = ROOT / "outputs" / "reports" / "zone3_game_route.md"

SHOP_KIND_MAP = {"attack": "atk", "defense": "def", "hp": "hp"}

# 事件战斗特殊：事件脚本在战前 setEnemy special，战后再复位。静态 enemy 数据
# 此时仍是 special=0，需 override 才能匹配实机 getDamageInfo。
# MT32 (6,10) yellowKnight 事件：setEnemy special=1 (先攻)，怪物先打一次，
# damage = init_damage(per) + (turn-1)*per = turn*per。
EVENT_BATTLE_SPECIAL = {
    ("MT32", "yellowKnight"): 1,
}

# guide walk 商人 (MT28 specialTrader 卖黄钥匙, MT38 trader 黄钥匙)
ZONE3_TRADERS = {
    ("MT28", (8, 4)): {"cost": -100, "yk": -1, "bk": 0, "eid": "sellYellowKey", "note": "卖黄钥匙 +100G"},  # sell: +100G, -1YK
    ("MT38", (5, 2)): {"cost": 200, "yk": 3, "bk": 0, "eid": "yellowKey3", "note": "黄钥匙 200G 买3把"},
}


class Zone3Game(Game):
    """通用 Game 的 3 区事件适配层。

    这里只实现真实楼层脚本中的显式事件动作；路径、auto、战斗、商店、门和
    after_action 地图变化仍统一由 :class:`Game` 处理。搜索代码不得再依赖旧的
    ``GuideReplay`` 或为单条 walk 添加坐标跳过补丁。
    """

    def event_mt32_yellow_knight(self) -> None:
        before = self.snapshot()
        dmg = self.enemy_damage("yellowKnight", special_override=1)
        if dmg == float("inf"):
            self.fail("32F 骑士队长无法破防")
        self.state["hp"] -= int(dmg)
        self.state["dmg"] += int(dmg)
        gain = int(self.enemies["yellowKnight"].get("money", 0))
        self.state["gold"] += gain * (2 if self.state.get("coin") else 1)
        self.set_ground("MT32", (6, 10))
        self.set_ground("MT32", (6, 2))
        self.set_ground("MT32", (6, 9))
        # The live event ends with hide(remove=true).  Keeping the stale event
        # shell makes strict click routing unable to leave x6y10 even though
        # the hero is visibly standing on ordinary ground.
        self.floors["MT32"].events.pop("6,10", None)
        self.record("事件战斗", (6, 10), "yellowKnight", before, "32F 初见骑士队长")

    def event_mt33_sword_trap(self) -> None:
        before = self.snapshot()
        self.state["x"], self.state["y"] = 10, 5
        self.floors["MT33"].events.pop("10,5", None)
        self.set_block("MT33", (11, 4), "wall", "yellowWall", 1)
        self.set_block("MT33", (10, 4), "door", "specialDoor", 85)
        self.set_block("MT33", (10, 8), "door", "specialDoor", 85)
        self.record("事件", (10, 5), "swordTrap", before, "33F 骑士剑机关")

    def oldman_mt2_1000g(self) -> None:
        before = self.snapshot()
        self.state["gold"] += 1000
        self.set_ground("MT2", (11, 4))
        self.record("事件奖励", (11, 4), "oldman", before, "2F 老人给 1000G")

    def thief_mt2_open_35(self) -> None:
        before = self.snapshot()
        self.set_ground("MT35", (4, 9))
        self.set_ground("MT2", (10, 11))
        self.record("事件", (10, 11), "thief", before, "2F 小偷开通 35F 暗道")

    def thief_mt35_depart(self) -> None:
        before = self.snapshot()
        self.set_ground("MT35", (5, 10))
        for pos, block in list(self.floors["MT35"].blocks.items()):
            if block.eid in {"fakeWall", "fakeWall2"}:
                self.set_ground("MT35", pos)
        self.record("事件", (5, 10), "thief", before, "35F 小偷离开并打开暗道")

    def thief_mt29_open_passage(self) -> None:
        """Resolve the real 29F thief event and open its centre passage."""
        self.move_adjacent("MT29", 6, 2, "29F 小偷事件")
        before = self.snapshot()
        self.set_ground("MT29", (6, 2))
        self.set_ground("MT29", (6, 3))
        self.record("事件", (6, 2), "thief", before, "29F 小偷挖通中心暗道")

    def buy_mt38_yellow_keys(self) -> None:
        before = self.snapshot()
        if self.state["gold"] < 200:
            self.fail(f"38F 买黄钥匙金币不足: have={self.state['gold']}")
        self.state["gold"] -= 200
        self.state["yk"] += 3
        self.set_ground("MT38", (5, 2))
        self.record("商人", (5, 2), "yellowKey3", before, "38F 花200G买3黄钥匙")

    def event_mt40_boss(self, note: str = "") -> None:
        """执行 MT40 x6y7 真实 Boss 事件并生成奖励。

        地图事件会把仍存在的 12 守卫和 x6y1 yellowKnight 依次拉到
        x6y7 战斗，随后生成 3 黄钥匙、3 红宝石、3 蓝宝石和 x6y1
        上楼梯。当前路线预先主动清掉 12 守卫，因此这里只剩队长，
        但实现按真实剩余块通用处理。
        """
        before = self.snapshot()
        order = [
            (5, 4), (4, 4), (3, 4), (7, 4), (8, 4), (9, 4),
            (4, 2), (3, 2), (2, 2), (8, 2), (9, 2), (10, 2), (6, 1),
        ]
        for pos in order:
            block = self.block_at("MT40", pos)
            if not block or block.kind != "enemy":
                continue
            dmg = self.enemy_damage(block.eid, special_override=1)
            if dmg == float("inf"):
                self.fail(f"40F Boss事件无法击杀 {block.eid} at {pos}")
            self.state["hp"] -= int(dmg)
            self.state["dmg"] += int(dmg)
            self.state["gold"] += int(self.enemies[block.eid].get("money", 0))
            if self.state["hp"] <= 0:
                self.fail(f"40F Boss事件死亡 {block.eid} at {pos}")
            self.set_ground("MT40", pos)
        for pos in [(2, 2), (3, 2), (4, 2)]:
            self.set_block("MT40", pos, "item", "yellowKey", 21)
        for pos in [(8, 2), (9, 2), (10, 2)]:
            self.set_block("MT40", pos, "item", "redGem", 27)
        for pos in [(7, 4), (8, 4), (9, 4)]:
            self.set_block("MT40", pos, "item", "blueGem", 28)
        self.set_block("MT40", (6, 1), "terrain", "upFloor", 87)
        self.set_ground("MT40", (6, 7))
        self.flags["402"] = True
        self.record("事件奖励", (6, 7), "yellowKnight", before,
                    note or "40F Boss事件：主动清怪后生成楼梯与奖励")


def _adaptive_go_to(g: Game, fid: str, x: int, y: int, note: str) -> bool:
    """go_to + 自适应补开拦路门（适配 current_best zone2 残留差异）。

    guide walk 为 guide baseline 构建，假设某些门在 zone2 已开（guide baseline 清理过）。
    current_best zone2 清理范围不同 → 这些门仍关闭。strict_live_model 下 path_to 用
    can_enter_click_path，不路由穿关闭门 → no path。本 helper 在 no-path 时用
    doors-passable 路径(can_enter, 门有钥匙即可穿)找到路径，沿路补开关闭门，再重试。
    """
    try:
        g.go_to(fid, x, y, note)
        return True
    except Exception:
        # go_to 在 path 为空时 fail() 先 append 错误再 raise；恢复前 pop 掉误报
        if g.errors:
            g.errors.pop()
    target = (x, y)
    path = g.path_to(fid, target, strict_click=False)
    if not path:
        g.fail(f"不可达目标 {fid} x{x}y{y}: {note}")
    key_attr = {"yellowDoor": "yk", "blueDoor": "bk", "redDoor": "rk"}
    for pos in path[1:]:
        blk = g.block_at(fid, pos)
        if blk and blk.kind == "door":
            attr = key_attr.get(blk.eid)
            if attr and g.state.get(attr, 0) > 0:
                try:
                    g.go_to(fid, pos[0], pos[1], f"补开门 {blk.eid} (current_best zone2 残留适配)")
                except Exception:
                    pass
            else:
                break  # 无对应钥匙，开不了
    try:
        g.go_to(fid, x, y, note)
    except Exception:
        if g.errors:
            g.errors.pop()
        g.fail(f"补开门后仍不可达 {fid} x{x}y{y}: {note}")
    return True


def run_zone3(g: Game, sell_deficit: list[int] | None = None, walk_path: Path | None = None,
              walk_data: dict | None = None) -> None:
    data = walk_data or json.loads((walk_path or GUIDE_WALK).read_text(encoding="utf-8"))
    steps = data["steps"]
    g.set_segment("3区 guide walk MT31-40 (auto ON, nopotion)")
    skipped_missing = 0
    for idx, s in enumerate(steps):
        action = s["action"]
        fid = s["floor"]
        x, y = s["pos"]
        eid = s.get("eid")
        note = s.get("note", "")
        # Old human walks may spell out every empty waypoint of a fake-wall
        # corridor.  Live needs exactly one movement click to settle wall=true
        # and remove the reachable fake walls; after that, a second click can
        # route directly to the stair.  Keep the first ``到达`` in such a run
        # and discard only its later waypoints.  This is action-order based,
        # not an MT35 coordinate exception.
        if action == "到达" and g.state["floor"] == fid:
            follow = idx + 1
            while follow < len(steps) and steps[follow].get("action") == "到达" \
                    and steps[follow].get("floor") == fid:
                follow += 1
            if follow < len(steps):
                target_step = steps[follow]
                tx, ty = target_step.get("pos", [None, None])
                previous_is_waypoint = (
                    idx > 0 and steps[idx - 1].get("action") == "到达"
                    and steps[idx - 1].get("floor") == fid
                )
                if (previous_is_waypoint and target_step.get("floor") == fid
                        and target_step.get("action") == "通过"):
                    try:
                        if tx is not None and g.path_to(fid, (int(tx), int(ty)), strict_click=True):
                            skipped_missing += 1
                            continue
                    except Exception:
                        pass
        if action == "校验":
            continue
        if action == "已清理":
            continue
        if action == "换层":
            if g.state["floor"] != fid:
                from_fid = g.state["floor"]
                want = "upFloor" if floor_no(fid) > floor_no(from_fid) else "downFloor"
                stair = None
                for p, b in g.floors[from_fid].blocks.items():
                    if b and b.kind == "terrain" and b.eid == want:
                        stair = p
                        break
                if stair:
                    try:
                        g.go_to(from_fid, stair[0], stair[1], f"通过 {want}")
                    except Exception:
                        pass
                g.transition(fid, f"{from_fid} -> {fid}")
            continue
        if action == "飞行":
            g.fly(fid)
            continue
        if g.state["floor"] != fid:
            g.fly(fid)
        if action in ("击杀", "拾取"):
            if g.block_at(fid, (x, y)) is None:
                skipped_missing += 1
                if g.steps:
                    g.steps[-1].setdefault("_skipped", []).append(f"{action} {fid} {x},{y} {eid} (已清)")
                continue
            # 所有敌人（包括 0 伤怪）统一走 Game.go_to 的真实点击语义；禁止直接
            # 写 hero 坐标或手工 apply_block。完整战后 auto（含 nopotion 物品）也
            # 必须由 Game 在同一动作结算，不能只补 battle-only sweep。
            go_to_decomposed(g, fid, x, y, f"{action} {eid}")
        elif action == "开门":
            if g.block_at(fid, (x, y)) is None:
                skipped_missing += 1
                continue
            # A distant door can have still-live enemies on its only corridor.
            # Re-plan with one real target click per settled battle, then click
            # the door; a synthetic far click cannot path through blockers.
            go_to_decomposed(g, fid, x, y, f"开门 {eid}")
        elif action == "通过":
            # block_at None 时格子已清（如 thief 事件后 fakeWall 走廊 set_ground），
            # 仍需 go_to 移动英雄到该格，不能 skip——否则英雄不前进。
            g.go_to(fid, x, y, f"通过 {eid}")
        elif action in ("用镐", "使用镐"):
            # 道具使用必须经过通用 Game 的合法性检查：同层、目标相邻、目标确为
            # 可破墙，并真实消耗 pickaxe。不能把墙直接 set_ground。
            g.use_pickaxe(fid, x, y, note or "使用镐")
        elif action == "到达":
            go_to_decomposed(g, fid, x, y, f"到达 {eid or ''}")
        elif action == "事件战斗":
            block = g.block_at(fid, (x, y))
            before = g.snapshot()
            g.state["x"], g.state["y"] = x, y
            if block is not None:
                g.apply_block(fid, (x, y), block, f"事件战斗 {eid}")
            elif eid:
                # event-spawned enemy (no map block): apply battle by eid.
                # e.g. MT32 (6,10) yellowKnight 骑士队长事件 — knight spawned at (10,1),
                # moves to (6,10), battles, then event removes whiteWall2 at (6,2)+(6,9)
                # to open the x=6 column (bottom->top path, bypassing (2,9)/(3,10)).
                # 事件脚本战前 setEnemy special（见 EVENT_BATTLE_SPECIAL），需 override。
                sp_override = EVENT_BATTLE_SPECIAL.get((fid, eid))
                dmg = g.enemy_damage(eid, special_override=sp_override)
                if dmg != float("inf"):
                    g.state["hp"] -= int(dmg)
                    g.state["dmg"] += int(dmg)
                    gain = int(g.enemies[eid].get("money", 0))
                    if g.state.get("coin"):
                        gain *= 2
                    g.state["gold"] += gain
                if fid == "MT32" and eid == "yellowKnight":
                    g.set_ground(fid, (6, 2))
                    g.set_ground(fid, (6, 9))
                g.record("事件战斗", (x, y), eid, before, f"事件战斗 {eid}")
            else:
                skipped_missing += 1
                continue
        elif action == "事件奖励":
            if fid == "MT40" and eid == "yellowKnight":
                g.event_mt40_boss(note)
                continue
            if fid == "MT39" and eid == "centerFly3":
                # 39F 谜题正确开门后在 (4,4) 生成中心对称飞行器。事件奖励
                # 只负责生成，下一条拾取仍通过 Game.go_to/auto 合法处理。
                before = g.snapshot()
                g.set_block("MT39", (4, 4), "item", "centerFly3", 331)
                g.record("事件奖励", (4, 4), "centerFly3", before,
                         note or "39F 谜题生成中心对称飞行器")
                continue
            # MT2 老人 (11,4) 给 1000G 是固定金币事件，apply_item 不识别 oldman，
            # 必须特殊处理，否则后续 atk 商店金币短缺。
            if eid == "oldman" and "1000" in (note or ""):
                g.move_adjacent(fid, x, y, f"对话 {eid}")
                before = g.snapshot()
                g.state["gold"] += 1000
                g.record("事件奖励", (x, y), eid, before, note or "老人 1000G")
                continue
            # MT34 中心 8 怪事件：杀完 8 怪生成 4黄1红钥匙在 (2,6)/(1,5)/(3,5)/(1,7)/(3,7)。
            # (2,6) 初始是 unbreakableWall(noPass tile=330)，事件奖励后替换为 redKey，
            # 否则后续"拾取 (2,6) redKey"不可达（path_to 被 noPass 阻断）。
            if fid == "MT34" and eid == "redKey" and (x, y) == (2, 6):
                before = g.snapshot()
                g.set_block(fid, (2, 6), "item", "redKey", 23)
                g.set_block(fid, (1, 5), "item", "yellowKey", 21)
                g.set_block(fid, (3, 5), "item", "yellowKey", 21)
                g.set_block(fid, (1, 7), "item", "yellowKey", 21)
                g.set_block(fid, (3, 7), "item", "yellowKey", 21)
                g.record("事件奖励", (x, y), eid, before, note or "MT34 中心 4黄1红")
                continue
            # 其它事件奖励（39F centerFly3、40F yellowKnight 等）：
            # 道具由 after_action 自动生成，英雄不动，只 record。
            # 后续"拾取"步骤才 go_to 拾取。回放时若 go_to 会错误移动英雄。
            before = g.snapshot()
            g.record("事件奖励", (x, y), eid, before, note or f"事件奖励 {eid}")
            continue
        elif action == "事件":
            # MT40 centerFly3：中心对称飞行 (x,y) -> (12-x, 12-y)，不 move_adjacent。
            # 与 zone3_event_actions.use_center_fly_to_mt40_boss_area 一致。
            if fid == "MT40" and eid == "centerFly3":
                before = g.snapshot()
                g.state["x"], g.state["y"] = 12 - g.state["x"], 12 - g.state["y"]
                g.state["centerFly3"] = False
                g.state["usedCenterFly40"] = True
                g.record("事件", (g.state["x"], g.state["y"]), eid, before, note or "40F 中心对称飞行")
                continue
            # MT29 小偷 (6,2) 事件：挖通中心暗道 (6,2)/(6,3)，否则 (6,11) 上楼梯不可达。
            # thief_mt29_open_passage 内部 move_adjacent+set_ground，走通用 Game 合法性。
            if fid == "MT29" and eid == "thief":
                g.thief_mt29_open_passage()
                continue
            # generic event: move adjacent + record (floor-specific side effects not modeled)
            hx, hy = g.state["x"], g.state["y"]
            if abs(hx - x) + abs(hy - y) > 1:
                try:
                    g.move_adjacent(fid, x, y, f"事件 {eid}")
                except Exception:
                    pass
            # MT2 小偷 (10,11) 事件开通 35F 暗道入口：set_ground MT35 (4,9) yellowWall。
            # (4,9) 是下块到走廊中列 (3,9) 的唯一入口，不开则走廊不可达。
            # 对应实机 MT2 小偷事件脚本。
            if fid == "MT2" and eid == "thief":
                g.set_ground("MT35", (4, 9))
            # MT35 thief (5,10) 事件后：thief 离开 (5,10)变空 + 整条 fakeWall 走廊打开。
            # 走廊是左边 U 形，从入口 (3,9)（经 (4,9)）到出口 (4,2)（相邻 (5,2)）。
            # set_ground 全部 fakeWall（替代 guide 生成时的 break_secret 逐格破墙）。
            if fid == "MT35" and eid == "thief":
                g.set_ground("MT35", (5, 10))  # thief 离开
                f = g.floors[fid]
                for p, blk in list(f.blocks.items()):
                    if blk and blk.eid in ("fakeWall", "fakeWall2"):
                        g.set_ground(fid, p)
            # MT33 swordTrap (10,5) 事件：spawn specialDoor at (10,4)+(10,8)（关闭）。
            # 杀完 4 守卫 (9,5)(11,5)(9,7)(11,7) 后由 Game.after_action 开门。
            # 对应 guide baseline event_mt33_sword_trap。未 spawn 则 (10,8) 视为空地，
            # auto_sweep 会在杀第 1 个守卫后就拿到 sword3（实机要等 4 个全死开门后显式拾取）。
            if fid == "MT33" and eid == "swordTrap":
                g.event_mt33_sword_trap()
                continue
            before = g.snapshot()
            g.record("事件", (x, y), eid, before, note or f"事件 {eid}")
        elif action == "对话":
            if abs(g.state["x"] - x) + abs(g.state["y"] - y) > 1:
                g.move_adjacent(fid, x, y, f"对话 {eid}")
        elif action == "商店":
            # eid 形如 "def"/"atk"/"hp"（guide walk 直接用短名），或 "shop:def"。
            # 无 ":" 时直接用 eid 本身，不能默认 "attack"——否则买 def 商店会错加 ATK。
            kind_raw = (eid.split(":")[1] if eid and ":" in eid else eid) or "attack"
            kind = SHOP_KIND_MAP.get(kind_raw, kind_raw)
            # move adjacent first (avoid auto_sweep clearing 0-dmg and shifting gold)
            hx, hy = g.state["x"], g.state["y"]
            if abs(hx - x) + abs(hy - y) > 1:
                for adj in [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]:
                    try:
                        # 相邻格必须可站(can_enter)：blueShop-left/right 等 noPass terrain 不能站。
                        # strict_click 路径不能穿过尚存敌人；若商店相邻格不可由一次真实
                        # 地图点击到达，路线必须先显式击杀阻挡敌人，再重新规划点击。
                        if g.can_enter(fid, adj, adj) and g.path_to(fid, adj, strict_click=True):
                            g.go_to(fid, adj[0], adj[1], f"商店 {eid} 相邻")
                            break
                    except Exception:
                        continue
            g.buy_shop(kind, 1, (x, y))
        elif action in ("商人", "merchant"):
            spec = ZONE3_TRADERS.get((fid, (x, y)))
            if spec:
                click_before = g.snapshot()
                click_step_start = len(g.steps)
                # current_best 起点YK=6（guide baseline 8，deficit 2）。
                # guide walk 卖 6 YK，current_best 全程少 2 YK，到 MT34/39 黄门会不够。
                # 跳过前 deficit 次 sellYellowKey，让 YK 路径与 guide 对齐。
                if spec["eid"] == "sellYellowKey" and sell_deficit and sell_deficit[0] > 0:
                    sell_deficit[0] -= 1
                    g.move_adjacent(fid, x, y, f"商人 {eid}")
                    before = g.snapshot()
                    g.record("商人", (x, y), spec["eid"] + "-SKIP", before,
                             f"跳过卖钥匙保留YK (deficit剩{sell_deficit[0]}) YK={g.state['yk']}")
                    print(f"  [SKIP-SELL] {fid} ({x},{y}) preserve YK={g.state['yk']}")
                    continue
                if abs(g.state["x"] - x) + abs(g.state["y"] - y) > 1:
                    g.move_adjacent(fid, x, y, f"商人 {eid}")
                # Walking to an NPC and selecting the choice are one real target
                # click. Merge any synthetic approach records into that click.
                del g.steps[click_step_start:]
                before = click_before
                # sell (cost<0) gains gold; buy (cost>0) spends gold. 单次加减。
                g.state["gold"] += -spec["cost"]
                g.state["yk"] += spec["yk"]
                g.state["bk"] += spec["bk"]
                g.record("商人", (x, y), spec["eid"], before, note or spec["note"])
            else:
                g.talk_trader(fid, x, y, note)
        else:
            print(f"UNKNOWN action #{idx}: {action} {fid} {x},{y} {eid}")
        if g.errors:
            print(f"ERR at step #{idx} {action} {fid} {x},{y} {eid}: {g.errors[-1]}")
            break
    print(f"skipped_missing={skipped_missing}")


def _parse_checkpoint_arg() -> Path | None:
    for i, a in enumerate(sys.argv):
        if a == "--from-checkpoint" and i + 1 < len(sys.argv):
            return Path(sys.argv[i + 1])
        if a.startswith("--from-checkpoint="):
            return Path(a.split("=", 1)[1])
    return None


def _parse_out_json_arg() -> Path:
    for i, a in enumerate(sys.argv):
        if a == "--out-json" and i + 1 < len(sys.argv):
            return Path(sys.argv[i + 1])
        if a.startswith("--out-json="):
            return Path(a.split("=", 1)[1])
    return OUT_JSON


def _parse_auto_flags() -> dict:
    """auto_flags 覆盖：默认 auto ON (item=nopotion) 用于规划/对账；
    `--auto-off` 切全关，用于 web 验证（auto OFF 显式分步，after 不含 auto_sweep 合并）。
    """
    if "--auto-off" in sys.argv:
        return {"battle": False, "item": False, "wall": False}
    return {"battle": True, "item": "nopotion", "wall": True}


def _parse_walk_arg() -> Path | None:
    for i, a in enumerate(sys.argv):
        if a == "--walk" and i + 1 < len(sys.argv):
            return Path(sys.argv[i + 1])
        if a.startswith("--walk="):
            return Path(a.split("=", 1)[1])
    return None


def main() -> int:
    checkpoint = _parse_checkpoint_arg() or ZONE3_BRIDGE_CHECKPOINT
    walk_path = _parse_walk_arg()
    g = Zone3Game(read_json(checkpoint))
    g.strict_live_model = True
    g.auto_flags = _parse_auto_flags()
    # 最低血 walk 删除的血瓶仍存在于地图；把它们声明为不可自动拾取资源，
    # 让 Game.auto_sweep(item=nopotion) 与固定动作序列压缩结果一致。
    if walk_path:
        walk_meta = read_json(walk_path)
        for row in walk_meta.get("removed_potions", []):
            pos = row.get("pos") or []
            if len(pos) == 2 and row.get("floor"):
                g.blocked_items.add((row["floor"], int(pos[0]), int(pos[1])))
    # current_best 起点YK=6 vs guide baseline 8：少卖 deficit 把黄钥匙，保留给 MT34/39 黄门。
    GUIDE_BASELINE_YK = 8
    if walk_path and walk_path.resolve() != GUIDE_WALK.resolve():
        # non-guide walk (e.g. slot26)：不套用 guide 的 sell_deficit，按 walk 自身步序卖。
        sell_deficit = [0]
    else:
        sell_deficit = [max(0, GUIDE_BASELINE_YK - g.state["yk"])]
    print(f"from-checkpoint={checkpoint}")
    print(f"walk={walk_path or GUIDE_WALK}")
    print(f"start={state_line(g.state)} {g.state['floor']} x{g.state['x']}y{g.state['y']} sell_deficit={sell_deficit[0]}")
    try:
        run_zone3(g, sell_deficit, walk_path)
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
    out_json = _parse_out_json_arg()
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(
        json.dumps({"ok": not g.errors, "final": g.snapshot(), "steps": g.steps, "errors": g.errors}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"json={out_json} steps={len(g.steps)}")
    return 0 if not g.errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
