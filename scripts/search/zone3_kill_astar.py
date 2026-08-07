#!/usr/bin/env python3
"""zone3 KILL 线 Game 搜索 (GameAStar, 替代手建 walk, 优化 final-score)。

从 slot32 (MT20) 桥到 MT31, 再 A* 搜 MT31->MT41。改策略(不买hp/延后swordsman/
省钱zone4)必须重新 Game 搜索--手挪 walk 会断门断键(用户判断)。本脚本用通用 Game
合法性找路线, 分析只指定搜索方向。

桥 MT20->MT31: 回放已验证 kill walk 前缀(forced stairs + MT29 thief + MT30 slimes)。
搜索 MT31->MT41:
  - 资源 click (fly + go_to_decomposed): 怪/宝石/钥匙/药瓶/装备, 按 value 排序前 N。
  - 开门 (go_to_decomposed): 可达且有钥匙的门 (含 MT39 trigger doors)。
  - 楼梯 change_by_stair (forward progression)。
  - 商店 move_adjacent + buy_shop, kind ∈ {atk, def} (不 hp, 用户点1)。
  - zone3 事件 (Zone3Game 方法): MT32 yellowKnight / MT33 swordTrap / MT2 oldman+thief /
    MT35 thief / MT38 buy keys / MT39 centerFly3 spawn / MT40 centerFly3 use + boss。
  - 策略剪枝: swordsman ATK<150 不生成击杀(延后, 用户点3: 150攻0伤); 不买 hp。

edge_cost = max(0, after.dmg - before.dmg)            # 战斗/陷阱 HP 损失 (药瓶免费)
          + 0.001 * potion_pickup                      # 药瓶微罚 -> 只在扛伤时拾 (HP 紧)
          + max(0, before.gold - after.gold) * 1.25    # 花金机会成本 (省钱 zone4, 用户点2)
dmg-delta == hp_potential-loss (dmg 跟踪全部 HP 损失; 药瓶 1:1), O(1)。

goal: floor=="MT41" and flags.get("402") (MT40 boss 完成)。
评估: comparison_score (HP+钥匙+剩余资源+gold×溢价) 排序 top-K 候选。

不声明全局最优: max_expansions 达上限只写"该预算未发现提升"。
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.solver.game_route import (  # noqa: E402
    Game, RouteError, STAIRS, floor_no, go_to_decomposed, read_json, state_line,
)
from src.solver.game_astar import GameAStar, GameAction  # noqa: E402
from src.solver.reachability_matrix import compute_matrix, comparison_score  # noqa: E402
from scripts.search.zone3_game_route import Zone3Game, run_zone3  # noqa: E402

CHECKPOINT = ROOT / "best" / "checkpoints" / "zone2_2atk0def_kill_end_save.json"
KILL_WALK = ROOT / "best" / "zone3_2atk0def_kill_walk.json"
DEFAULT_OUT_JSON = ROOT / "outputs" / "results" / "zone3_kill_astar_walk.json"
DEFAULT_OUT_MD = ROOT / "outputs" / "reports" / "zone3_kill_astar.md"

# 1 gold 的 zone4 等价 HP (GOLD_FACE_VALUE 0.5 × zone4_premium 2.5 = 1.25)。
GOLD_PREMIUM = 1.25
POTION_PENALTY = 0.001  # 药瓶微罚, 让搜索只在扛伤时拾 -> HP 紧
SWORDSMAN_ATK_THRESHOLD = 150  # ATK>=150 一击秒 swordsman (turns=1, damage=0)

# 资源静态估值 (排序用; 怪用 money - access_dmg)
ITEM_VALUE = {
    "redGem": 500, "blueGem": 550, "greenGem": 520,
    "sword3": 2000, "shield3": 2000, "pickaxe": 300, "cross": 800,
    "centerFly3": 1500, "centerFly": 800,
    "yellowKey": 100, "blueKey": 400, "redKey": 420,
    "redPotion": 50, "bluePotion": 200,
}
POTION_EIDS = {"redPotion", "bluePotion"}
GEM_EIDS = {"redGem", "blueGem", "greenGem"}

# zone3 事件 trigger 位置
MT32_YK_EVENT = "6,10"
MT33_SWORDTRAP_EVENT = "10,5"

_T0 = 0.0
_N = {"n": 0}
_MAX_FLOOR = {"f": 0}


def _floor_n(fid: str) -> int:
    return int(fid[2:]) if fid.startswith("MT") and fid[2:].isdigit() else 0


def build_start() -> Zone3Game:
    """load checkpoint (MT20) + 回放 kill walk 桥前缀到 MT31 (forced)。"""
    g = Zone3Game(read_json(CHECKPOINT))
    g.strict_live_model = True
    g.auto_flags = {"battle": True, "item": "nopotion", "wall": True}
    walk = json.loads(KILL_WALK.read_text(encoding="utf-8"))
    steps = walk["steps"]
    cut = next(i for i, s in enumerate(steps) if s.get("floor") == "MT31")
    prefix = {**walk, "steps": steps[: cut + 1]}
    run_zone3(g, sell_deficit=[0], walk_data=prefix)
    if g.errors:
        raise RuntimeError(f"bridge replay errors: {g.errors[:5]}")
    return g


def _entry_value(entry, g: Game) -> float:
    """资源 entry 排序估值: 宝石/装备/钥匙用面值; 怪用 money - access_dmg; 药瓶用面值。"""
    if entry.eid in ITEM_VALUE:
        v = ITEM_VALUE[entry.eid]
    elif entry.kind == "monster":
        money = int(g.enemies.get(entry.eid, {}).get("money", 0))
        v = money - entry.access_dmg
    else:
        v = 0.0
    # 优先宝石(减伤) > 钥匙 > 装备 > 怪(金) > 药瓶
    if entry.eid in GEM_EIDS:
        v += 1000
    elif entry.eid in ("yellowKey", "blueKey", "redKey"):
        v += 300
    return v


def _resource_targets(g: Game, rm, cap: int = 18) -> list:
    """compute_matrix entries -> 排序前 cap 的资源目标 (fid, pos, eid, kind, is_potion)。"""
    rows = []
    for fr in rm.floors.values():
        for e in fr.entries:
            if e.kind in ("skeleton", "monster", "supplement_key", "supplement_potion"):
                # swordsman 延后: ATK<150 不生成击杀 (1842 dmg@ATK76, 致死)
                if e.eid == "swordsman" and g.state["atk"] < SWORDSMAN_ATK_THRESHOLD:
                    continue
                is_potion = e.eid in POTION_EIDS
                rows.append((e, _entry_value(e, g), is_potion))
    rows.sort(key=lambda r: -r[1])
    return rows[:cap]


def _door_targets(g: Game, rm, cap: int = 8) -> list:
    """可达且有钥匙的门 -> 开门目标。含 MT39 trigger doors (4,2)+(6,4)。"""
    key_attr = {"yellowDoor": "yk", "blueDoor": "bk", "redDoor": "rk"}
    rows = []
    for fid, fr in rm.floors.items():
        for pos in fr.reachable_cells:
            for nb in ((pos[0] + 1, pos[1]), (pos[0] - 1, pos[1]), (pos[0], pos[1] + 1), (pos[0], pos[1] - 1)):
                blk = g.block_at(fid, nb)
                if not blk or blk.kind != "door":
                    continue
                attr = key_attr.get(blk.eid)
                if not attr or g.state.get(attr, 0) <= 0:
                    continue
                rows.append((fid, nb, blk.eid))
    # dedup
    seen = set()
    out = []
    for r in rows:
        k = (r[0], r[1])
        if k in seen:
            continue
        seen.add(k)
        out.append(r)
    return out[:cap]


def _stair_targets(g: Game, rm) -> list:
    """当前层可达楼梯 -> 换层目标 (to_fid, stair_x, stair_y)。"""
    cur = g.state["floor"]
    fr = rm.floors.get(cur)
    if not fr:
        return []
    cur_n = _floor_n(cur)
    out = []
    for (x, y), block in g.floors[cur].blocks.items():
        if block.eid not in STAIRS:
            continue
        adj = any(n in fr.reachable_cells for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
        if not adj:
            continue
        to_fid = f"MT{cur_n + 1}" if block.eid == "upFloor" else f"MT{cur_n - 1}"
        if to_fid not in g.floors:
            continue
        out.append((to_fid, x, y))
    return out


def _shop_targets(g: Game, rm) -> list:
    """可达商店 -> atk/def 购买 (不 hp)。返回 (shop_pos, kind)。

    只生成 zone3 商店 (MT31-40, ratio4): 同 times1 成本下 zone3 +8atk/+16def 严格
    优于 zone2 ratio2 (+4/+8), 用户点4"3区买防优于2区"。zone4 ratio5 在 goal 之后。
    阈值上限 (atk<150, def<170) 防商店组合爆炸: ATK>=150 swordsman 0伤无需再买 atk,
    DEF>=170 够用无需再买 def。"""
    out = []
    for fr in rm.floors.values():
        fn = _floor_n(fr.fid)
        if fn < 31 or fn > 40:
            continue
        for e in fr.entries:
            if e.kind != "shop":
                continue
            cost = 20 + 10 * (g.state["times1"] + 1) * g.state["times1"]
            if g.state["gold"] < cost:
                continue
            if g.state["atk"] < SWORDSMAN_ATK_THRESHOLD:
                out.append((e.fid, e.pos, "atk"))
            if g.state["def"] < 170:
                out.append((e.fid, e.pos, "def"))
    return out


def _event_actions(g: Game) -> list:
    """zone3 事件 action (precondition -> Zone3Game 方法)。defensive: 失败则该 action apply 抛 RouteError 被跳过。"""
    acts = []

    def make(name, fn, meta=None):
        return GameAction(name=name, apply=fn, metadata=meta or {})

    # MT32 yellowKnight
    mt32 = g.floors.get("MT32")
    if mt32 and MT32_YK_EVENT in mt32.events:
        def apply_yk(game):
            if game.state["floor"] != "MT32":
                game.fly("MT32")
            game.state["x"], game.state["y"] = 6, 10
            game.event_mt32_yellow_knight()
        acts.append(make("event MT32 yellowKnight", apply_yk, {"kind": "event"}))

    # MT33 swordTrap
    mt33 = g.floors.get("MT33")
    if mt33 and MT33_SWORDTRAP_EVENT in mt33.events:
        def apply_st(game):
            if game.state["floor"] != "MT33":
                game.fly("MT33")
            game.event_mt33_sword_trap()
        acts.append(make("event MT33 swordTrap", apply_st, {"kind": "event"}))

    # MT2 oldman (11,4) +1000G -- 经 blueDoor(3,1) [需 BK] 入右半区, fly 回 origin。
    # MT2 左右半区被 steelDoor 隔开, 只能经顶部 blueDoor(3,1) 过; build_start BK=0 不可达,
    # zone3 拿 BK 后 go_to_decomposed 自动开 blueDoor en route。fly 回 origin 避 floor 启发式困 MT2。
    if g.block_at("MT2", (11, 4)) is not None and g.block_at("MT2", (11, 4)).eid == "oldman" and g.state["bk"] >= 1:
        origin = g.state["floor"]
        def apply_oldman(game, origin=origin):
            if game.state["floor"] != "MT2":
                game.fly("MT2")
            go_to_decomposed(game, "MT2", 10, 4, "2F 老人 (经 blueDoor)")  # (10,4) 邻 oldman(11,4)
            game.oldman_mt2_1000g()
            if game.state["floor"] != origin and origin in game.visited:
                game.fly(origin)
        acts.append(make("event MT2 oldman +1000G", apply_oldman, {"kind": "event"}))

    # MT2 thief (10,11) 开 35F 暗道 (清 MT35 (4,9), MT36 楼梯前置) -- 经 blueDoor(3,1), fly 回 origin
    if g.block_at("MT2", (10, 11)) is not None and g.block_at("MT2", (10, 11)).eid == "thief" and g.state["bk"] >= 1:
        origin = g.state["floor"]
        def apply_t2(game, origin=origin):
            if game.state["floor"] != "MT2":
                game.fly("MT2")
            go_to_decomposed(game, "MT2", 11, 11, "2F 小偷 (经 blueDoor)")  # (11,11) 邻 thief(10,11)
            game.thief_mt2_open_35()
            if game.state["floor"] != origin and origin in game.visited:
                game.fly(origin)
        acts.append(make("event MT2 thief open35", apply_t2, {"kind": "event"}))

    # MT35 thief (5,10)
    if g.block_at("MT35", (5, 10)) is not None and g.block_at("MT35", (5, 10)).eid == "thief":
        def apply_t35(game):
            if game.state["floor"] != "MT35":
                game.fly("MT35")
            game.move_adjacent("MT35", 5, 10, "35F 小偷")
            game.thief_mt35_depart()
        acts.append(make("event MT35 thief depart", apply_t35, {"kind": "event"}))

    # MT38 buy yellow keys (5,2)
    b38 = g.block_at("MT38", (5, 2))
    if b38 is not None and b38.kind == "npc" and g.state["gold"] >= 200:
        def apply_b38(game):
            if game.state["floor"] != "MT38":
                game.fly("MT38")
            game.move_adjacent("MT38", 5, 2, "38F 买黄钥匙")
            game.buy_mt38_yellow_keys()
        acts.append(make("event MT38 buy 3YK", apply_b38, {"kind": "event"}))

    # MT39 centerFly3 spawn: doors (4,2)+(6,4) 已开 + (4,4) 未生成
    mt39 = g.floors.get("MT39")
    if mt39 is not None:
        d42 = g.block_at("MT39", (4, 2))
        d64 = g.block_at("MT39", (6, 4))
        c44 = g.block_at("MT39", (4, 4))
        spawned = c44 is not None and c44.eid == "centerFly3"
        if d42 is None and d64 is None and not spawned:
            def apply_cf3(game):
                if game.state["floor"] != "MT39":
                    game.fly("MT39")
                before = game.snapshot()
                game.set_block("MT39", (4, 4), "item", "centerFly3", 331)
                game.record("事件奖励", (4, 4), "centerFly3", before,
                            "39F 开门后生成中心对称飞行器")
            acts.append(make("event MT39 spawn centerFly3", apply_cf3, {"kind": "event"}))

    # MT40 use centerFly3 (进 boss 区) + MT40 boss
    if g.state["floor"] == "MT40" and not g.state.get("usedCenterFly40") and g.state.get("centerFly3"):
        def apply_use_cf3(game):
            # 中心对称飞行 (x,y)->(12-x,12-y)
            before = game.snapshot()
            game.state["x"], game.state["y"] = 12 - game.state["x"], 12 - game.state["y"]
            game.state["centerFly3"] = False
            game.state["usedCenterFly40"] = True
            game.record("事件", (game.state["x"], game.state["y"]), "centerFly3", before,
                        "40F 使用中心对称飞行器进入Boss区域")
        acts.append(make("event MT40 use centerFly3", apply_use_cf3, {"kind": "event"}))

    if g.state["floor"] == "MT40" and g.state.get("usedCenterFly40") and not g.flags.get("402"):
        def apply_boss(game):
            # 到 (6,7) 触发 boss (event_mt40_boss 处理残余怪+奖励+楼梯+flags[402])
            before = game.snapshot()
            game.state["x"], game.state["y"] = 6, 7
            game.event_mt40_boss()
        acts.append(make("event MT40 boss", apply_boss, {"kind": "event"}))

    return acts


def skeleton_actions(game: Game) -> Iterable[GameAction]:
    _N["n"] += 1
    if _N["n"] % 50 == 0:
        el = time.perf_counter() - _T0
        s = game.state
        print(f"  [prog] exp={_N['n']} {s['floor']} HP={s['hp']} ATK={s['atk']} DEF={s['def']} "
              f"G={s['gold']} t1={s.get('times1', 0)} dmg={s['dmg']} {el:.1f}s", flush=True)
    acts: list[GameAction] = []
    rm = compute_matrix(game)
    cur = game.state["floor"]
    fn = _floor_n(cur)
    if fn > _MAX_FLOOR["f"]:
        _MAX_FLOOR["f"] = fn
        print(f"  [MAXFLOOR] reached {cur} (fn={fn}) HP={game.state['hp']} ATK={game.state['atk']} "
              f"DEF={game.state['def']} BK={game.state['bk']} G={game.state['gold']} t1={game.state.get('times1',0)} "
              f"dmg={game.state['dmg']} exp={_N['n']}", flush=True)

    # 1) 资源 click (fly + go_to_decomposed)
    for e, _v, is_potion in _resource_targets(game, rm):
        fid, (x, y), eid = e.fid, e.pos, e.eid

        def make_apply(fid=fid, x=x, y=y, eid=eid):
            def apply(game: Game) -> None:
                if game.state["floor"] != fid:
                    game.fly(fid)
                go_to_decomposed(game, fid, x, y, f"click {eid}")
            return apply
        acts.append(GameAction(
            name=f"click {fid} x{x}y{y} {eid}",
            apply=make_apply(),
            metadata={"kind": "resource", "is_potion": is_potion},
        ))

    # 2) 开门 (go_to_decomposed)
    for fid, (x, y), eid in _door_targets(game, rm):
        def make_door(fid=fid, x=x, y=y, eid=eid):
            def apply(game: Game) -> None:
                if game.state["floor"] != fid:
                    game.fly(fid)
                go_to_decomposed(game, fid, x, y, f"开门 {eid}")
            return apply
        acts.append(GameAction(name=f"door {fid} x{x}y{y} {eid}", apply=make_door(),
                               metadata={"kind": "door"}))

    # 3) 楼梯换层 (go_to_decomposed 清挡路怪/门 + transition, 不用 change_by_stair
    #    因其 go_to strict 遇挡路怪 fail; zone3 MT31 (6,2)->(6,11) 被 zombieKnight 挡)
    cur = game.state["floor"]
    for to_fid, x, y in _stair_targets(game, rm):
        def make_stair(cur=cur, to_fid=to_fid, x=x, y=y):
            def apply(game: Game) -> None:
                go_to_decomposed(game, cur, x, y, f"stair ->{to_fid}")
                game.transition(to_fid, f"stair ->{to_fid}")
            return apply
        acts.append(GameAction(name=f"stair ->{to_fid} x{x}y{y}", apply=make_stair(),
                               metadata={"kind": "stair"}))

    # 4) 商店 atk/def (不 hp)
    for fid, pos, kind in _shop_targets(game, rm):
        sx, sy = pos[0], pos[1]

        def make_shop(fid=fid, sx=sx, sy=sy, kind=kind):
            def apply(game: Game) -> None:
                if game.state["floor"] != fid:
                    game.fly(fid)
                game.move_adjacent(fid, sx, sy, f"approach shop {kind}")
                game.buy_shop(kind, 1, shop_pos=(sx, sy))
            return apply
        acts.append(GameAction(name=f"buy {kind} {fid} x{sx}y{sy}", apply=make_shop(),
                               metadata={"kind": "shop"}))

    # 5) zone3 事件
    acts.extend(_event_actions(game))
    return acts


def goal(game: Game) -> bool:
    s = game.state
    if s["hp"] <= 0:
        return False
    return s["floor"] == "MT41" and game.flags.get("402")


def heuristic(game: Game) -> float:
    """向 MT41 引导。floor 距离用大系数 (500) 压过 zone1-2 0-cost 收集 churn + 战斗成本,
    让搜索优先 forward progression (zone3 战斗 ~100-420 dmg/场, 一层进度 > 任一单场)。
    atk 缺口小系数 (3) 拉向 150 (swordsman 0伤门槛), 不压过 floor (否则搜索沉迷升 atk
    不前进, MT35 thief child 被高 atk_deficit 延后, MT36 不可达)。
    前置缺口: MT2 thief (开 MT35 走廊->MT36) 需 BK 开 blueDoor(3,1); BK=0 时强拉收集 BK。"""
    s = game.state
    fn = _floor_n(s["floor"])
    h = max(0.0, float(41 - fn)) * 500.0
    if s["atk"] < SWORDSMAN_ATK_THRESHOLD:
        h += (SWORDSMAN_ATK_THRESHOLD - s["atk"]) * 3.0
    # MT2 thief 前置: 需 BK (开 blueDoor) -- BK=0 且 MT2 thief 未做时强拉收集 BK
    mt2_thief = game.block_at("MT2", (10, 11))
    if mt2_thief is not None and s["bk"] < 1:
        h += 800.0
    return h


def edge_cost(before: Game, after: Game, action: GameAction) -> float:
    """HP 损失 (dmg-delta, == hp_potential-loss) + 花金×0.3 (机会成本, 省钱 zone4) + 每步微罚 + 药瓶微罚。

    gold×0.3 (非 1.25): 商店花金有小成本让搜索 economize (不买不减伤的商店, 避商店组合爆炸),
    但不全堵 (1.25 堵死 forward progression); 商店减伤 > 花金×0.3 才买。"省钱 zone4" 由
    comparison_score 排 top-K 候选补充。dmg-delta == hp_potential-loss (药瓶 1:1)。"""
    dmg_delta = max(0, after.state["dmg"] - before.state["dmg"])
    gold_spent = max(0, before.state["gold"] - after.state["gold"])
    potion = POTION_PENALTY if action.metadata.get("is_potion") else 0.0
    return float(dmg_delta + gold_spent * 0.3 + 0.5 + potion)


def _event_sig(game: Game):
    """事件进度签名: 捕获只改地图不改 state 的事件 (否则 state_key+cost 向量不变被 A* 当 no-op 丢弃)。

    MT35 thief / MT39 centerFly3 spawn / MT2 thief / MT33 swordTrap 等事件只改地图
    (清 fakeWall / spawn 道具 / 清 NPC), 不改 HP/ATK/DEF/gold/keys/pos -> 与父节点
    同 state_key 同 cost 向量 -> 被去重跳过 -> MT36 等后续楼梯永远不可达。
    """
    mt32 = game.floors.get("MT32")
    mt33 = game.floors.get("MT33")
    b510 = game.block_at("MT35", (5, 10))
    c44 = game.block_at("MT39", (4, 4))
    return (
        ("6,10" in mt32.events) if mt32 else False,   # MT32 yellowKnight pending
        ("10,5" in mt33.events) if mt33 else False,   # MT33 swordTrap pending
        b510 is not None,                             # MT35 thief present
        (c44 is not None and c44.eid == "centerFly3"),  # MT39 centerFly3 spawned
        game.block_at("MT2", (11, 4)) is not None,    # MT2 oldman present
        game.block_at("MT2", (10, 11)) is not None,   # MT2 thief present
    )


def state_key(game: Game):
    s = game.state
    cf3 = s.get("centerFly3", 0)
    return (
        s["floor"], s["x"], s["y"], s["atk"], s["def"], s["hp"] // 20,
        s["times1"], s["gold"] // 10, s["yk"], s["bk"], s["rk"],
        bool(game.flags.get("402")), bool(s.get("usedCenterFly40")),
        int(cf3) if isinstance(cf3, int) else 0,
        len(game.blocked_items),
        _event_sig(game),
    )


def main() -> int:
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--max-expansions", type=int, default=1500)
    p.add_argument("--weight", type=float, default=3.0)
    p.add_argument("--top-k", type=int, default=3)
    p.add_argument("--upper-bound", type=float, default=13000.0)
    p.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    args = p.parse_args()

    global _T0
    g = build_start()
    print(f"start (MT31): {state_line(g.state)} {g.state['floor']} "
          f"x{g.state['x']}y{g.state['y']} dmg={g.state['dmg']} t1={g.state.get('times1', 0)}", flush=True)
    # incumbent 参照 (现有 kill walk, 无 hp shop)
    print("incumbent: HP=609 ATK=166 DEF=174 G=2285 dmg=8806 (existing kill walk, has hp shop)", flush=True)
    print(f"  target: MT41+flags402 | weight={args.weight} max_exp={args.max_expansions} "
          f"ub={args.upper_bound} top_k={args.top_k}", flush=True)

    _T0 = time.perf_counter()
    astar = GameAStar(
        actions=skeleton_actions,
        goal=goal,
        heuristic=heuristic,
        edge_cost=edge_cost,
        state_key=state_key,
        weight=args.weight,
        max_expansions=args.max_expansions,
        upper_bound=args.upper_bound,
        top_k=args.top_k,
    )
    res = astar.search(g)
    el = time.perf_counter() - _T0
    print(f"\nfound={res.found} cost={res.cost:.0f} expansions={res.expansions} "
          f"generated={res.generated} reason={res.reason} {el:.1f}s", flush=True)

    candidates = []
    if res.top_goals:
        for i, (c, gm, _rt) in enumerate(res.top_goals):
            rm = compute_matrix(gm)
            cs = comparison_score(gm, rm)
            candidates.append((c, gm, cs))
    elif res.found and res.game:
        rm = compute_matrix(res.game)
        candidates.append((res.cost, res.game, comparison_score(res.game, rm)))

    if candidates:
        print(f"\n=== {len(candidates)} goal candidate(s) ===", flush=True)
        for i, (c, gm, cs) in enumerate(candidates):
            s = gm.state
            print(f"  #{i + 1} cost={c:.0f} HP={s['hp']} ATK={s['atk']} DEF={s['def']} "
                  f"YK={s['yk']} BK={s['bk']} RK={s['rk']} G={s['gold']} dmg={s['dmg']} "
                  f"t1={s['times1']} {s['floor']} | final-score={cs['total']:.0f} "
                  f"(gold_val={cs['gold_value']:.0f} remain={cs['remaining']['total']:.0f})", flush=True)
        # 选 final-score 最高的
        best_cost, best_gm, best_cs = max(candidates, key=lambda t: t[2]["total"])
        s = best_gm.state
        print(f"\nBEST by final-score: HP={s['hp']} ATK={s['atk']} DEF={s['def']} "
              f"G={s['gold']} dmg={s['dmg']} final-score={best_cs['total']:.0f}", flush=True)
        args.out_json.parent.mkdir(parents=True, exist_ok=True)
        args.out_json.write_text(json.dumps({
            "ok": not best_gm.errors,
            "variant": "zone3_kill_astar",
            "source_slot": 32,
            "start_checkpoint": str(CHECKPOINT),
            "goal": "MT41+flags402",
            "final": best_gm.snapshot(),
            "steps": best_gm.steps,
            "errors": best_gm.errors,
            "search": {
                "expansions": res.expansions, "generated": res.generated,
                "reason": res.reason, "cost": res.cost, "weight": args.weight,
                "max_expansions": args.max_expansions, "upper_bound": args.upper_bound,
            },
            "comparison_score": best_cs,
            "all_candidates": [
                {"cost": c, "final": gm.snapshot(), "final_score": cs["total"]}
                for c, gm, cs in candidates
            ],
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"walk.json={args.out_json} steps={len(best_gm.steps)}", flush=True)
        return 0 if not best_gm.errors else 1
    print("\nno goal candidate reached within budget.", flush=True)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
