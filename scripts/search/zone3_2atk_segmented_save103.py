#!/usr/bin/env python3
"""zone3 4区2攻 分段参考引导搜索（SEGMENTS 模式，从 save103 省门前缀起）。

背景 (2026-08-29)：一次性 A* (zone3_2atk_astar_save103.py) 从 MT31 搜到 MT41 视野太长，
在 MT31-35 振荡到不了 MT36+（记忆 zone4_2atk_lessdoors_2420_safe 三次复现）。
且 save103 省门前缀 + 39529 body 直接重放被实证级联断裂（BK差1→MT2事件丢失→金币缺口650，
见 splice_state_divergence_cascade）——组合线必须重搜 zone3。

本脚本 = 参考里程碑分段：把参考 walk（41228 全防 / 39529 4区2攻）的 zone3 宏顺序切成
4 段，每段独立 GameAStar（短视野不振荡），段间前段 best goal 作为后段 start：

  SEG1 shop_done    : MT32 商店 6def+2atk 买齐（4区2攻 分配锚定 39529）
  SEG2 mt2_events   : MT2 oldman(+1000G) + thief(开35F暗道) 两个事件都消费
  SEG3 mt35_thief   : MT35 thief depart + ATK>=150（swordsman 0伤门槛）
  SEG4 mt40_boss    : MT40 boss(flags402) + 到达 MT41

复用 zone3_2atk_astar_save103 的 skeleton_actions / edge_cost / state_key / 事件 action
（zone3_2atk_astar_save103 import 后直接传 GameAStar）。

用法：
  python scripts/search/zone3_2atk_segmented_save103.py \
      --seg-expansions 800 --out-json outputs/results/zone3_2atk_segmented.json
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.solver.game_astar import GameAStar  # noqa: E402
from src.solver.game_route import Game, RouteError, go_to_decomposed, state_line  # noqa: E402
from src.solver.reachability_matrix import compute_matrix, comparison_score  # noqa: E402
import zone3_2atk_astar_save103 as base  # noqa: E402

DEFAULT_OUT = ROOT / "outputs" / "results" / "zone3_2atk_segmented.json"


# ---------------------------------------------------------------- segments

def seg1_shop_done(g) -> bool:
    """SEG1 只买 6 def（1780G，352+1485怪金+1000 oldman=2837 够，无需卖 yk）。
    atk×2(1660G) 留到 SEG2——参考线 times=9/10 在 MT34-38 金币之后才买，
    且 MT34 中心 8 怪 autoEvent 需要 ~8 yk（每怪封一扇黄门），资金段卖 yk 会饿死 SEG2。"""
    return g.state.get("z3_def", 0) >= base.ZONE3_DEF_CAP


def seg2_atk_rk_done(g) -> bool:
    """SEG2(拆分版): 爬升目标 = MT35 thief + ATK>=142 + HP>=300 + 资源保留
    （y>=3/G>=200：dmg-min 爬升会把钥匙/金币花光，SEG2b 的 RK 链(MT37 门/MT38 商人3yk)
    无资源可用——参考线到 MT37 时 YK6 G2153）。"""
    return (g.block_at("MT35", (5, 10)) is None
            and g.state["atk"] >= 142
            and g.state["hp"] >= 300
            and g.state["yk"] >= 3
            and g.state["gold"] >= 200)


def seg2b_rk_done(g) -> bool:
    """SEG2b: RK>=1 单目标（MT37(2,4) 附近红钥匙 auto_sweep / MT34 中心集群 /
    MT25 blackMagician——同前缀参考线 41228 用 MT14/MT37 红钥匙开 MT38 redDoor）。"""
    return g.state["rk"] >= 1 and g.state["hp"] > 0


def seg2_mt2_events(g) -> bool:
    oldman_gone = g.block_at("MT2", (11, 4)) is None
    thief_gone = g.block_at("MT2", (10, 11)) is None
    return oldman_gone and thief_gone


def seg3_mt35_ready(g) -> bool:
    """thief 离开 + ATK>=142（参考线 39529 在 MT35 入口即 ATK142，非 0伤秒杀的 150 便利阈值；
    142 下 swordsman 有伤但可生存，与参考一致）+ HP>=300 生存储备 + RK>=1
    （MT38 (3,1) redDoor 硬挡上走廊到 (11,1) 楼梯；RK 唯一来源=MT34[2,6] redKey，缺它 SEG3 必 exhausted）。"""
    thief_gone = g.block_at("MT35", (5, 10)) is None
    return (thief_gone and g.state["atk"] >= 142 and g.state["hp"] >= 300
            and g.state["rk"] >= 1)


def seg3_cf3_spawned(g) -> bool:
    """MT39 centerFly3 已获取（块仍在地图 或 已拾取 centerFly>=3——
    auto_sweep 可能在同步拾取，goal 必须两种终态都认）。"""
    c44 = g.block_at("MT39", (4, 4))
    return (c44 is not None and c44.eid == "centerFly3") or g.state.get("centerFly", 0) >= 3


def seg4_boss(g) -> bool:
    s = g.state
    return s["hp"] > 0 and s["floor"] == "MT41" and g.flags.get("402")


def h_floor(target_no: int):
    def h(g) -> float:
        fn = base._floor_n(g.state["floor"])
        return max(0.0, float(target_no - fn)) * 500.0
    return h


def h_shop(g) -> float:
    """SEG1 启发：6def 剩余阶梯成本缺口（cost(n)=20+10n(n+1)）+ oldman 资金桥预期
    + yk 储备不足罚 + MT2 事件罚。"""
    d_need = max(0, base.ZONE3_DEF_CAP - g.state.get("z3_def", 0))
    if d_need == 0:
        h = 0.0
    else:
        t = g.state.get("times1", 0)
        total_cost = 0
        for _ in range(d_need):
            t += 1
            total_cost += 20 + 10 * t * (t - 1)
        gold_gap = max(0, total_cost - g.state["gold"]) - 1000  # oldman +1000G 可预期
        h = d_need * 400.0 + max(0.0, gold_gap) * 1.0
    if g.state["yk"] < 5:
        h += (5 - g.state["yk"]) * 200.0
    if g.block_at("MT2", (11, 4)) is not None:
        h += 500.0
    if g.block_at("MT2", (10, 11)) is not None:
        h += 500.0
    return h


def h_mt2(g) -> float:
    """SEG2 启发：两个事件未做各罚；BK 缺口大罚。"""
    penalty = 0.0
    if g.block_at("MT2", (11, 4)) is not None:
        penalty += 500.0
    if g.block_at("MT2", (10, 11)) is not None:
        penalty += 500.0
    if g.state["bk"] < 1:
        penalty += 800.0
    if g.state["def"] < 150:
        penalty += (150 - g.state["def"]) * 2.0
    return penalty


def h_mt35(g) -> float:
    """SEG2(爬升) 启发：thief + ATK142(强梯度) + HP300 + yk/金币保留梯度。"""
    penalty = 0.0
    if g.block_at("MT35", (5, 10)) is not None:
        penalty += 600.0
    if g.state["atk"] < 142:
        penalty += (142 - g.state["atk"]) * 30.0
    if g.state["hp"] < 300:
        penalty += (300 - g.state["hp"]) * 0.5
    if g.state["yk"] < 3:
        penalty += (3 - g.state["yk"]) * 300.0
    if g.state["gold"] < 200:
        penalty += (200 - g.state["gold"]) * 0.5
    return penalty


def h_rk(g) -> float:
    """SEG2b(RK单目标) 启发：RK 缺口 + MT14 方向引导（已证最便宜源 = MT14 三连杀
    zombieKnight (2,2)(1,1)(3,1) → (1,3) spawn redKey，0 伤）。"""
    h = 0.0
    if g.state["rk"] < 1:
        h += 2000.0
        fn = base._floor_n(g.state["floor"])
        h += abs(14 - fn) * 150.0
    return h


def seg1_funding_done(g) -> bool:
    """6def + MT2 两事件（oldman 资金桥 / thief 开35F），且保留 >=5 yk
    （MT34 中心 8 怪各封一扇黄门，参考线在 MT34 前留 8 yk；资金段卖 yk=饿死 SEG2）。"""
    return (seg1_shop_done(g) and seg2_mt2_events(g) and g.state["yk"] >= 5)


def h_boss(g) -> float:
    """SEG4 启发：boss 链需 ~1400 HP 垫底（实测 ATK148/DEF172/HP531 打 boss 事件
    守卫+boss 共 -785 必死；参考线 HP7300+ 才打）。
    MT39/40 上先垫血（喝血梯度），HP 够后 boss 链 h=0 置顶。"""
    s = g.state
    fn = base._floor_n(s["floor"])
    if fn >= 39:
        if s["floor"] == "MT40" and s.get("centerFly", 0) >= 1 and s["hp"] >= 1400:
            return 0.0
        if s["hp"] < 1400:
            return (1400 - s["hp"]) * 0.2 + 50.0
        return max(0.0, float(41 - fn)) * 100.0
    return max(0.0, float(41 - fn)) * 500.0


SEGMENTS = [
    {"name": "SEG1 6def+MT2事件+yk5储备", "goal": seg1_funding_done, "heuristic": h_shop,
     "floors": {"MT2", "MT28", "MT31", "MT32", "MT33"}},
    {"name": "SEG2 thief+ATK142+HP300", "goal": seg2_atk_rk_done, "heuristic": h_mt35,
     "floors": {"MT31", "MT32", "MT33", "MT34", "MT35", "MT36", "MT37", "MT38"}},
    {"name": "SEG2b RK单目标(MT14三连杀)", "goal": seg2b_rk_done, "heuristic": h_rk,
     "floors": {"MT14", "MT25", "MT31", "MT32", "MT33", "MT34", "MT35", "MT36", "MT37", "MT38"}},
    {"name": "SEG3 MT39 centerFly3", "goal": seg3_cf3_spawned, "heuristic": h_floor(39),
     "floors": {"MT25", "MT31", "MT32", "MT33", "MT34", "MT38", "MT39"}},
    {"name": "SEG4 MT40 boss->MT41", "goal": seg4_boss, "heuristic": h_boss,
     "floors": {"MT25", "MT31", "MT32", "MT33", "MT34", "MT38", "MT39", "MT40", "MT41"}},
]

_FID_RE = None


def _action_fid(name: str) -> str | None:
    """从 action name 提取目标楼层 token（click/door/stair/buy/event 首个 MTxx）。"""
    import re
    global _FID_RE
    if _FID_RE is None:
        _FID_RE = re.compile(r"MT\d+")
    m = _FID_RE.search(name)
    return m.group(0) if m else None


def constrained_actions(allowed: set[str] | None):
    """楼层白名单包装：跳过目标楼层不在 allowed 的动作（SEG 收敛空间，防 zone1-2 漫游）。
    另注入两类 base 骨架缺失的动作：
    1. "MT28 卖 1yk"（省门富余 yk = 资金桥，base 无 trader 动作）。
    2. "显式喝血瓶"（item=nopotion 下 Game.go_to 拒绝以血瓶为目标 → A* 无法垫血，
       致死战(如 MT36 (11,5) swordsman dmg~494 > HP395) 不可达。实机语义=真实点击
       血瓶格即拾取（auto 只影响远距 BFS sweep），故显式 fly+相邻+apply_item 合法）。"""
    from src.solver.game_astar import GameAction

    def actions(game):
        if allowed and "MT28" in allowed and game.state["yk"] >= 1:
            def apply_sell(game: Game) -> None:
                if game.state["floor"] != "MT28":
                    game.fly("MT28")
                game.talk_trader("MT28", 8, 4, "SEG 卖1yk (省门资金桥)")
            yield GameAction(name="sell yk MT28 x8y4", apply=apply_sell,
                             metadata={"kind": "trader_sell"})
        # 第 3 次 atk 商店（MT40 boss 守卫链门槛：3×swordsman 在 ATK<150 各 ~500 伤必死，
        # ATK>=150 一击秒杀 0 伤。省门宝石流差 2 点，一次 atk(+8) 是等价杠杆；
        # base _shop_targets 的 z3_atk<=2 cap 会挡它，这里定向注入绕过）
        if allowed and "MT32" in allowed and game.state["atk"] < 150:
            _cost = 20 + 10 * (game.state.get("times1", 0) + 1) * game.state.get("times1", 0)
            if game.state["gold"] >= _cost:
                from src.solver.game_astar import GameAction as _GA3

                def make_atk():
                    def apply(game: Game) -> None:
                        if game.state["floor"] != "MT32":
                            game.fly("MT32")
                        game.move_adjacent("MT32", 10, 10, "接近 atk 商店")
                        game.buy_shop("atk", 1, shop_pos=(10, 10))
                        game.state["z3_atk"] = game.state.get("z3_atk", 0) + 1
                    return apply
                yield _GA3(name="buy atk3 MT32 x10y10 (boss守卫门槛)",
                           apply=make_atk(), metadata={"kind": "shop"})

        # MT40 boss mega 复合动作（区域适配层；参考线 39529 实证：DEF222 使 redKnight/
        # soldier 全变 0 伤，ATK150 秒杀 swordsman，事件仅剩奖励）：
        # 买 atk3(G>=1120) -> 吃 MT38/39 血瓶 -> 抓 2 blueGem(DEF->224) -> MT40 -> cf3
        # -> 清 12 守卫+(6,1) -> (6,7) 事件(flags402+奖励) -> (6,1) 上 MT41。
        if allowed and "MT40" in allowed and game.state.get("centerFly", 0) >= 1:
            # 注: RK 此时可能已花在 MT38 redDoor（SEG3 谜题链内），门已开故无需 RK
            from src.solver.game_astar import GameAction as _GA4

            def apply_boss(game: Game) -> None:
                # 属性化过 boss（参考 39529: ATK150 秒杀 swordsman + DEF222 ≥ redKnight
                # 攻击 → 12 守卫全 0 伤；血瓶一个不吃, dmg 口径最优）
                _cost = 20 + 10 * (game.state.get("times1", 0) + 1) * game.state.get("times1", 0)
                if game.state["atk"] < 150 and game.state["gold"] >= _cost:
                    if game.state["floor"] != "MT32":
                        game.fly("MT32")
                    game.move_adjacent("MT32", 10, 10, "接近 atk 商店")
                    game.buy_shop("atk", 1, shop_pos=(10, 10))
                    game.state["z3_atk"] = game.state.get("z3_atk", 0) + 1
                # 补 yk: MT38 商人 3YK（蓝宝石多在黄门后）
                if game.state["gold"] >= 200:
                    try:
                        game.fly("MT38")
                        game.talk_trader("MT38", 5, 2, "商人 3YK (宝石门钥匙)")
                    except RouteError:
                        pass
                # DEF 宝石清扫: 所有可达 blueGem（跳过 access_dmg>600 的致死路径）
                from src.solver.reachability_matrix import compute_matrix as _cm
                _rm = _cm(game)
                for fid, fr in list(_rm.floors.items()):
                    if base._floor_n(fid) < 31:
                        continue
                    for e in list(fr.entries):
                        blk = game.block_at(fid, e.pos)
                        if blk is None:
                            continue
                        if e.eid == "blueGem" and e.access_dmg <= 600:
                            try:
                                game.fly(fid)
                                go_to_decomposed(game, fid, e.pos[0], e.pos[1], f"bossDEF {e.eid}")
                            except RouteError:
                                continue
                # MT40 -> cf3 -> 清守卫 -> 事件
                game.fly("MT39")
                go_to_decomposed(game, "MT39", 11, 11, "MT39 upFloor")
                game.transition("MT40", "MT39->MT40")
                before = game.snapshot()
                game.state["x"], game.state["y"] = 12 - game.state["x"], 12 - game.state["y"]
                game.state["centerFly3"] = False
                game.state["usedCenterFly40"] = True
                game.record("事件", (game.state["x"], game.state["y"]), "centerFly3",
                            before, "40F cf3")
                for epos in [(5, 4), (4, 4), (3, 4), (7, 4), (8, 4), (9, 4), (4, 2),
                             (3, 2), (2, 2), (8, 2), (9, 2), (10, 2), (6, 1)]:
                    b = game.block_at("MT40", epos)
                    if b is None or b.kind != "enemy":
                        continue
                    go_to_decomposed(game, "MT40", epos[0], epos[1], f"清守卫 {b.eid}")
                go_to_decomposed(game, "MT40", 6, 7, "踩 (6,7) 事件")
                # (6,1) 已变 upFloor -> MT41
                go_to_decomposed(game, "MT40", 6, 1, "(6,1) upFloor")
                game.transition("MT41", "MT40->MT41")

            yield _GA4(name="event MT40 boss chain (atk3+DEF224+guards+event->MT41)",
                       apply=apply_boss, metadata={"kind": "event"})

        # MT39 谜题链复合动作（区域适配层；参考线 41228 [724]-[808] 步序实证）：
        # 补 BK(MT14(1,11)/MT19(8,1) 0伤蓝钥匙) -> MT37 左列(杀(1,9)+蓝门(1,3)+(1,1)上)
        # -> MT38 redDoor(3,1)RK + (9,1)黄门 + (11,1)上 -> MT39 (10,4)/(10,8)/(8,10)/(4,10)
        # /(2,8)蓝/(4,2)/(6,4) -> base 的 spawn centerFly3 事件随之触发。
        if allowed and "MT39" in allowed and game.state["rk"] >= 1:
            from src.solver.game_astar import GameAction as _GA2

            def apply_puzzle(game: Game) -> None:
                # 补 BK: 每个 0 伤蓝钥匙 +1（按需）
                for fid, pos in (("MT14", (1, 11)), ("MT19", (8, 1))):
                    blk = game.block_at(fid, pos)
                    if blk is not None and blk.eid == "blueKey" and game.state["bk"] < 2:
                        game.fly(fid)
                        go_to_decomposed(game, fid, pos[0], pos[1], f"补BK {fid}{pos}")
                # MT37 左列
                game.fly("MT37")
                b = game.block_at("MT37", (1, 9))
                if b is not None and b.kind == "enemy":
                    go_to_decomposed(game, "MT37", 1, 9, "杀 (1,9) soldier")
                b = game.block_at("MT37", (1, 3))
                if b is not None and b.kind == "door":
                    go_to_decomposed(game, "MT37", 1, 3, "开 (1,3) 蓝门")
                go_to_decomposed(game, "MT37", 1, 1, "上 (1,1)")
                game.transition("MT38", "MT37->MT38")
                # MT38 redDoor + 上走廊
                b = game.block_at("MT38", (3, 1))
                if b is not None and b.kind == "door":
                    go_to_decomposed(game, "MT38", 3, 1, "开 redDoor(3,1)")
                # 商人 3YK/200G（(5,2) 在 redDoor 内侧；MT39 谜题需 6 yk，省门自带 ~4 不够）
                b = game.block_at("MT38", (5, 2))
                if b is not None and b.kind == "npc" and game.state["gold"] >= 200:
                    game.talk_trader("MT38", 5, 2, "商人 3YK (谜题钥匙补给)")
                b = game.block_at("MT38", (9, 1))
                if b is not None and b.kind == "door":
                    go_to_decomposed(game, "MT38", 9, 1, "开 (9,1) 黄门")
                go_to_decomposed(game, "MT38", 11, 1, "上 (11,1)")
                game.transition("MT39", "MT38->MT39")
                # MT39 谜题门（(6,4) 先于 (4,2)：开 (4,2) 后英雄停 (4,3)，
                # 从那里 (6,4) 不可达——spawn 只要求两门都开，顺序无拘）
                for pos, need in [((10, 4), "yk"), ((10, 8), "yk"), ((8, 10), "yk"),
                                  ((4, 10), "yk"), ((2, 8), "bk"), ((6, 4), "yk"), ((4, 2), "yk")]:
                    blk = game.block_at("MT39", pos)
                    if blk is not None and blk.kind == "door":
                        go_to_decomposed(game, "MT39", pos[0], pos[1], f"开谜题门 {pos}")
                # centerFly3 spawn 由 base._check_auto_events 在 go_to 内触发；拾取:
                blk = game.block_at("MT39", (4, 4))
                if blk is not None and blk.eid == "centerFly3":
                    go_to_decomposed(game, "MT39", 4, 4, "拾取 centerFly3")

            yield _GA2(name="event MT39 puzzle chain (RK->centerFly3)",
                       apply=apply_puzzle, metadata={"kind": "event"})

        # MT14 zombieKnight 三连杀（RK 源，value=30 被 _resource_targets cap=18 挤掉，
        # 定向注入：三杀 -> (1,3) spawn redKey -> auto_sweep 拾取 -> RK=1）
        if allowed and "MT14" in allowed:
            from src.solver.game_astar import GameAction as _GA
            for _p in [(2, 2), (1, 1), (3, 1)]:
                _blk = game.block_at("MT14", _p)
                if _blk is not None and _blk.kind == "enemy":

                    def make_kill(p=_p):
                        def apply(game: Game) -> None:
                            if game.state["floor"] != "MT14":
                                game.fly("MT14")
                            go_to_decomposed(game, "MT14", p[0], p[1],
                                             f"kill zombieKnight {p} (RK源)")
                        return apply
                    yield _GA(name=f"click MT14 x{_p[0]}y{_p[1]} zombieKnight",
                              apply=make_kill(), metadata={"kind": "resource"})
        # 显式喝血瓶（每个可达血瓶一个动作）
        if allowed:
            from src.solver.reachability_matrix import compute_matrix
            rm = compute_matrix(game)
            for fid, fr in rm.floors.items():
                if fid not in allowed:
                    continue
                for e in fr.entries:
                    if e.kind != "supplement_potion":
                        continue
                    x, y = e.pos

                    def make_drink(fid=fid, x=x, y=y, eid=e.eid):
                        def apply(game: Game) -> None:
                            if game.state["floor"] != fid:
                                game.fly(fid)
                            if (game.state["x"], game.state["y"]) != (x, y):
                                game.move_adjacent(fid, x, y, f"接近 {eid}")
                            blk = game.block_at(fid, (x, y))
                            if blk is None:
                                return  # 已被其它分支喝掉
                            before = game.snapshot()
                            game.state["x"], game.state["y"] = x, y
                            game.apply_item(fid, eid)
                            game.set_ground(fid, (x, y))
                            game.record("拾取", (x, y), eid, before, f"显式喝 {eid} (垫血)")
                        return apply
                    yield GameAction(name=f"drink {fid} x{x}y{y} {e.eid}",
                                     apply=make_drink(), metadata={"kind": "potion"})
        for a in base.skeleton_actions(game):
            fid = _action_fid(a.name)
            if allowed is None or fid is None or fid in allowed:
                yield a
    return actions


def run() -> int:
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--seg-expansions", type=int, default=800)
    p.add_argument("--weight", type=float, default=3.0)
    p.add_argument("--out-json", type=Path, default=DEFAULT_OUT)
    p.add_argument("--load-game-pkl", type=Path, default=None,
                   help="从 pickle 恢复 Game 状态(精确无重放偏差), 配合 --skip-segments")
    p.add_argument("--skip-segments", type=int, default=0,
                   help="跳过前 N 段(与 --load-game-pkl 连用)")
    p.add_argument("--save-game-pkl", type=Path, default=None,
                   help="每段成功后把 Game pickle 到该路径(供续跑)")
    args = p.parse_args()

    g = base.build_start()
    print(f"start (save103 MT31): {state_line(g.state)} x{g.state['x']}y{g.state['y']} "
          f"dmg={g.state['dmg']} t1={g.state.get('times1', 0)}", flush=True)

    all_steps: list = []
    skip = args.skip_segments
    if args.load_game_pkl and skip > 0:
        import pickle
        g = pickle.loads(args.load_game_pkl.read_bytes())
        print(f"loaded game from {args.load_game_pkl}, skip {skip} segments: "
              f"{state_line(g.state)} {g.state['floor']} "
              f"dmg={g.state['dmg']} t1={g.state.get('times1', 0)}", flush=True)

    total_exp = 0
    t0 = time.perf_counter()
    ok = True
    for si, seg in enumerate(SEGMENTS):
        if si < skip:
            continue
        astar = GameAStar(
            actions=constrained_actions(seg["floors"]),
            goal=seg["goal"],
            heuristic=seg["heuristic"],
            edge_cost=base.edge_cost,
            state_key=base.state_key,
            weight=args.weight,
            max_expansions=args.seg_expansions,
            upper_bound=13000.0,
            top_k=1,
        )
        res = astar.search(g)
        total_exp += res.expansions
        el = time.perf_counter() - t0
        s = g.state
        print(f"[{seg['name']}] found={res.found} reason={res.reason} "
              f"exp={res.expansions} cost={res.cost:.0f} {el:.1f}s | "
              f"HP={s['hp']} ATK={s['atk']} DEF={s['def']} G={s['gold']} "
              f"YK={s['yk']} BK={s['bk']} {s['floor']}", flush=True)
        if not res.found or res.game is None:
            print(f"  !! 段未达成，停在第 {si + 1} 段。", flush=True)
            ok = False
            break
        g = res.game
        all_steps.extend(g.steps)
        if args.save_game_pkl:
            import pickle
            args.save_game_pkl.write_bytes(pickle.dumps(g))

    el = time.perf_counter() - t0
    print(f"\n{'=' * 20} 结果 {'=' * 20}\nok={ok} total_expansions={total_exp} {el:.1f}s", flush=True)
    print(f"final={state_line(g.state)} {g.state['floor']} x{g.state['x']}y{g.state['y']} "
          f"dmg={g.state['dmg']} door={g.state['yd']}/{g.state['bd']}/{g.state['rd']} "
          f"t1={g.state.get('times1', 0)} z3def={g.state.get('z3_def', 0)} "
          f"z3atk={g.state.get('z3_atk', 0)}", flush=True)
    if ok:
        rm = compute_matrix(g)
        cs = comparison_score(g, rm)
        print(f"final-score={cs['total']:.0f} (gold_val={cs['gold_value']:.0f} "
              f"remain={cs['remaining']['total']:.0f})", flush=True)
    if g.errors:
        for e in g.errors[:10]:
            print("ERR", str(e)[:120])
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps({
        "ok": ok,
        "variant": "zone3_2atk_segmented_save103",
        "source_slot": 103,
        "start_checkpoint": str(base.CHECKPOINT),
        "segments": [seg["name"] for seg in SEGMENTS],
        "final": g.snapshot(),
        "steps": g.steps,
        "errors": g.errors,
        "search": {"total_expansions": total_exp, "seg_expansions": args.seg_expansions,
                   "weight": args.weight, "elapsed_s": round(el, 1)},
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"json={args.out_json} steps={len(g.steps)}", flush=True)
    return 0 if ok and not g.errors else 1


if __name__ == "__main__":
    raise SystemExit(run())
