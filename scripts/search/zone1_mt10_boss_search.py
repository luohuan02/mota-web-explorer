#!/usr/bin/env python3
"""zone1 MT10 boss 搜索（GameAStar + 可达矩阵）。

从 save1(MT4) 起，搜到 MT10 boss 击败，top-K 按累计 dmg（从 MT4 起）排序。
对照当前最优：HP=122 ATK=27 DEF=27 dmg=2454 final-score=1376.5（MT10 boss 后补给前）。

动作词表（与 zone2 同构，去掉 MT12 属性商店，加 MT10 boss 触发终态）：
  1) 当前楼层骨架/商店/怪 click（怪按 access_dmg 升序前 12）
  2) 楼梯换层（upFloor/downFloor）
  3) MT10 boss 触发：go_to(6,5) + 生成 SPAWNED_BOSS + clear_mt10_boss_dyn（终态）

dmg 语义：state["dmg"] 从 MT4 起累计（save1 dmg=0），A* cost=增量累加=final.dmg，
故 top-K 按 cost 排序 = 按从 MT4 累计 dmg 排序。
"""
from __future__ import annotations

import os, sys, json, time, math
from collections import deque
import heapq
from pathlib import Path
from typing import Callable, Iterable

ROOT = Path("D:/claude/mota-web-explorer")
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from src.solver.game_route import Game, RouteError, go_to_decomposed, read_json, state_line, STAIRS
from src.solver.game_astar import GameAStar, GameAction
from src.solver.reachability_matrix import _flood_floor, cross_floor_reachable, compute_matrix, SKELETON_ITEM_EIDS, SUPPLEMENT_KEY_EIDS, TRADER_KEY_MAP
from scripts.baseline.replay_user_post9_route import SPAWNED_BOSS

SAVE1 = ROOT / "outputs" / "results" / "save1_current_snapshot.json"
BOSS_TRIGGER = (6, 5)
OUT_JSON = ROOT / "outputs" / "results" / "zone1_mt10_boss_search.json"

_T0 = 0.0
_N = {"n": 0}
# Pareto 多目标模式(实验): state_key 去 atk/def + Pareto frontier (dmg,-atk,-def)
# 保留非支配,让刷宝石分支不被 dmg-min 剪。由 --pareto 开启。
_PARETO = False
# boss 段 phase: 钥匙/药水跨层 acquire 仅 boss 段开启。sword1/shield1/gem 段 YK 低,
# 加钥匙 acquire 会让动作空间爆炸 6x(shield1 213s vs 35s)。run_boss_subgoals 开。
_BOSS_PHASE = False


def _floor_n(fid: str) -> int:
    return int(fid[2:]) if fid.startswith("MT") else 0


def _boss_cleared(game: Game) -> bool:
    for pos in SPAWNED_BOSS:
        b = game.block_at("MT10", pos)
        if b and b.kind == "enemy":
            return False
    return True


_STATIC_SKELETON: list[tuple[str, int, int, str]] | None = None


_ZONE1_SKELETON_EIDS = (
    {"redGem", "blueGem", "greenGem"}
    | {f"sword{n}" for n in range(1, 6)}
    | {f"shield{n}" for n in range(1, 6)}
)


def _static_skeleton(g: Game) -> list[tuple[str, int, int, str]]:
    """枚举 MT1-10 静态骨架资源（宝石/剑/盾），位置不随状态变。排除 fly 等工具。"""
    global _STATIC_SKELETON
    if _STATIC_SKELETON is None:
        out: list[tuple[str, int, int, str]] = []
        for fid in sorted(g.floors, key=lambda f: int(f[2:]) if f.startswith("MT") else 0):
            if not (fid.startswith("MT") and 1 <= int(fid[2:]) <= 10):
                continue
            for (x, y), block in g.floors[fid].blocks.items():
                if block.eid in _ZONE1_SKELETON_EIDS:
                    out.append((fid, x, y, block.eid))
        _STATIC_SKELETON = out
    return _STATIC_SKELETON


_STATIC_KEYS: list[tuple[str, int, int, str]] | None = None


def _static_keys(g: Game) -> list[tuple[str, int, int, str]]:
    """枚举 MT1-10 静态钥匙道具（地图上的 yellowKey/blueKey/redKey），位置不随状态变。"""
    global _STATIC_KEYS
    if _STATIC_KEYS is None:
        out: list[tuple[str, int, int, str]] = []
        for fid in sorted(g.floors, key=lambda f: int(f[2:]) if f.startswith("MT") else 0):
            if not (fid.startswith("MT") and 1 <= int(fid[2:]) <= 10):
                continue
            for (x, y), block in g.floors[fid].blocks.items():
                if block.eid in ("yellowKey", "blueKey", "redKey"):
                    out.append((fid, x, y, block.eid))
        _STATIC_KEYS = out
    return _STATIC_KEYS


_STATIC_POTIONS: list[tuple[str, int, int, str]] | None = None


def _static_potions(g: Game) -> list[tuple[str, int, int, str]]:
    """枚举 MT1-10 静态药水(redPotion/bluePotion),位置不随状态变。"""
    global _STATIC_POTIONS
    if _STATIC_POTIONS is None:
        out: list[tuple[str, int, int, str]] = []
        for fid in sorted(g.floors, key=lambda f: int(f[2:]) if f.startswith("MT") else 0):
            if not (fid.startswith("MT") and 1 <= int(fid[2:]) <= 10):
                continue
            for (x, y), block in g.floors[fid].blocks.items():
                if block.eid in ("redPotion", "bluePotion"):
                    out.append((fid, x, y, block.eid))
        _STATIC_POTIONS = out
    return _STATIC_POTIONS


def _find_stair(g: Game, fid: str, direction: str) -> tuple[int, int] | None:
    floor = g.floors[fid]
    cf = _flood_floor(g, fid, break_fakewalls=True)
    for (x, y), block in floor.blocks.items():
        if block.eid != direction:
            continue
        if any(n in cf.reachable_cells for n in ((x+1, y), (x-1, y), (x, y+1), (x, y-1))):
            return (x, y)
    return None


def _break_one_reachable_fakewall(g: Game, fid: str) -> bool:
    """破一个邻接可达格的 fakeWall（go_to 到 fakeWall 格即破），返回是否破了。"""
    cf = _flood_floor(g, fid, break_fakewalls=True)
    floor = g.floors[fid]
    for (x, y), block in floor.blocks.items():
        if block.eid not in ("fakeWall", "fakeWall2"):
            continue
        if any(n in cf.reachable_cells for n in ((x+1, y), (x-1, y), (x, y+1), (x, y-1))):
            go_to_decomposed(g, fid, x, y, f"break fakeWall x{x}y{y}")
            return True
    return False


def _break_neighbor_monster(g: Game, fid: str, tx: int, ty: int) -> bool:
    """打 target 邻居的 cheap 怪清路: target 被静态怪围时(go_to 到 item 格需先打
    邻居怪进)。如 MT10 redGem(10,6) 被 (9,6)/(11,6) skeleton + (10,7) skeletonSoldier
    围,需打 1 个进。按 access_dmg 升序打最便宜的。事务化。"""
    cf = _flood_floor(g, fid, break_fakewalls=True)
    cheap: list[tuple[int, int, tuple[int, int], str]] = []
    for (nx, ny) in ((tx - 1, ty), (tx + 1, ty), (tx, ty - 1), (tx, ty + 1)):
        b = g.block_at(fid, (nx, ny))
        if not b or b.kind != "enemy":
            continue
        for e in cf.entries:
            if e.kind == "monster" and e.pos == (nx, ny):
                cheap.append((e.access_dmg, e.path_len, (nx, ny), e.eid))
                break
    if not cheap:
        return False
    cheap.sort()
    for _dmg, _pl, pos, eid in cheap[:2]:
        if _tx_go_to(g, fid, pos[0], pos[1], f"kill neighbor {eid} for {tx},{ty}"):
            return True
    return False


def _fetch_deficit_key_on_floor(g: Game, fid: str) -> bool:
    """若该楼层有钥匙门挡路缺钥匙，取一把可达的对应钥匙，返回是否取了。
    钥匙是地图道具(supplement_key)；个别怪(如 bluePriest)杀后也掉钥匙，作 fallback。
    事务化：go_to 失败回滚，避免开门扣钥匙等副作用污染重试。"""
    cf = _flood_floor(g, fid, break_fakewalls=True)
    need = _deficit_keys(g, cf)
    if not need:
        return False
    # 1) supplement_key 道具（地图上的钥匙）
    for e in cf.entries:
        if e.kind == "supplement_key" and e.eid in need:
            if _tx_go_to(g, fid, e.pos[0], e.pos[1], f"supplement {e.eid}"):
                return True
    # 2) fallback: cheap 怪杀后掉钥匙（bluePriest 等）
    cheap = sorted([e for e in cf.entries if e.kind == "monster"],
                   key=lambda e: (e.access_dmg, e.path_len))[:3]
    yk0 = g.state["yk"]; bk0 = g.state["bk"]; rk0 = g.state["rk"]
    for e in cheap:
        if _tx_go_to(g, fid, e.pos[0], e.pos[1], f"kill {e.eid} for keys"):
            if g.state["yk"] > yk0 or g.state["bk"] > bk0 or g.state["rk"] > rk0:
                return True
    return False


def _key_groups(g: Game, fid: str) -> list[dict]:
    """fid 楼层钥匙资源组：被关闭门分隔的连通分量内的钥匙归为一组。

    "在一起"的钥匙（同一口袋、不穿关闭门互达）合并成一组，一次取（开 1 道 entry
    门即扫光整组）。不同门/不同怪后的钥匙分属不同组，不一起搜。组的 entry 门 =
    邻接该连通分量的关闭门。用乐观 flood 发现所有可达钥匙，再按关闭门分隔做连通
    分量。hero_in=True 表示英雄当前在该分量内（无门，直接扫）。
    """
    cf = _flood_floor(g, fid, break_fakewalls=True)
    reachable = cf.reachable_cells

    def is_closed_door(pos: tuple[int, int]) -> bool:
        b = g.block_at(fid, pos)
        return b is not None and b.kind == "door"

    visited: set[tuple[int, int]] = set()
    groups: list[dict] = []
    for cell in reachable:
        if cell in visited or is_closed_door(cell):
            continue
        comp: set[tuple[int, int]] = set()
        queue = [cell]
        while queue:
            c = queue.pop()
            if c in comp:
                continue
            comp.add(c)
            visited.add(c)
            cx, cy = c
            for n in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                if n in reachable and not is_closed_door(n) and n not in comp:
                    queue.append(n)
        keys = []
        for p in comp:
            b = g.block_at(fid, p)
            if b and b.eid in SUPPLEMENT_KEY_EIDS:
                keys.append((p[0], p[1], b.eid))
        if not keys:
            continue
        entries = set()
        for (cx, cy) in comp:
            for n in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                if is_closed_door(n):
                    entries.add(n)
        hero_in = (g.state["floor"] == fid and (g.state["x"], g.state["y"]) in comp)
        groups.append({
            "fid": fid, "keys": sorted(keys), "entries": sorted(entries),
            "yield": len(keys), "hero_in": hero_in,
        })
    return groups


def _acquire_key_group(g: Game, group: dict) -> bool:
    """获取一个钥匙组：导航到组楼层(事务化楼梯)，开一道 entry 门，扫光组内钥匙。
    返回是否取到≥1把钥匙。entry 门需英雄有对应钥匙(或组 hero_in 无门)。"""
    fid = group["fid"]
    # 1) 导航到组楼层: 已访问 transition 直达(匹配 walk 下楼直达);首次访问逐层楼梯。
    if g.state["floor"] != fid:
        if fid in g.visited:
            g.transition(fid, f"nav fly->{fid}")
        else:
            for _ in range(20):
                if g.state["floor"] == fid:
                    break
                cur = g.state["floor"]
                cur_n = _floor_n(cur)
                tgt_n = _floor_n(fid)
                d = "upFloor" if tgt_n > cur_n else "downFloor"
                stair = _find_stair(g, cur, d)
                if stair is None or not _tx_go_to(g, cur, stair[0], stair[1], f"nav {cur}"):
                    return False
                g.transition(f"MT{cur_n + (1 if tgt_n > cur_n else -1)}", f"nav {cur}")
            if g.state["floor"] != fid:
                return False
    # 2) 开一道 entry 门（事务化；hero_in 组无门跳过）
    if group["entries"]:
        for door in group["entries"]:
            if _tx_go_to(g, fid, door[0], door[1], f"open entry {door}"):
                break
    # 3) 扫光组内钥匙（事务化 go_to 每个；auto-sweep 已拾的跳过）
    got = False
    for (kx, ky, keid) in group["keys"]:
        if g.block_at(fid, (kx, ky)) is None:
            got = True
            continue
        if _tx_go_to(g, fid, kx, ky, f"sweep {keid}"):
            got = True
    return got


def _search_resource(g: Game, need_keys: set[str]) -> bool:
    """跨层搜钥匙资源组（back-collect）：按收益(yield)排序，一次取整组。
    不再把散落钥匙逐个取。need_keys=_ALL_KEYS 时全保留；否则只取含所需类型的组。
    事务化：每组 clone 试，成功(取到≥1把)才写回。"""
    if not need_keys:
        return False
    cur_n = _floor_n(g.state["floor"])
    broad = (need_keys == _ALL_KEYS)
    # 收集全 MT1-10 的钥匙组（不再 ±2 截断：远楼层钥匙会被漏，back-collect 补不到）。
    # 可达性由 _acquire_key_group 内部 go_to 精确判断，事务化失败跳过下一组。
    all_groups: list[dict] = []
    for fid in g.floors:
        if not (fid.startswith("MT") and 1 <= _floor_n(fid) <= 10):
            continue
        all_groups.extend(_key_groups(g, fid))
    if not broad:
        all_groups = [grp for grp in all_groups
                      if any(k[2] in need_keys for k in grp["keys"])]
    if not all_groups:
        return False
    # 排序：yield 降序；hero_in 优先(当前楼层无门组，最快起手)；楼层距离升序
    all_groups.sort(key=lambda x: (-x["yield"], 0 if x["hero_in"] else 1,
                                   abs(_floor_n(x["fid"]) - cur_n)))
    for grp in all_groups:
        c = g.clone()
        if _acquire_key_group(c, grp):
            # 确认确实取到≥1把（组内至少一把已不在）
            if any(c.block_at(grp["fid"], (k[0], k[1])) is None for k in grp["keys"]):
                g.__dict__.update(c.__dict__)
                return True
    return False


_ALL_KEYS = {"yellowKey", "blueKey", "redKey"}


def _tx_go_to(g: Game, fid: str, x: int, y: int, note: str) -> bool:
    """事务化 go_to_decomposed：clone 后试，失败回滚。

    go_to_decomposed 失败时会留部分副作用（开门扣钥匙、移动 hero、杀怪扣 HP），
    del errors 只清错误不回滚状态。导航重试必须在干净态上做，否则越试越劣化
    （如 MT6 开了第 1 道门 YK->0 后，第 2 道门再也开不了，回搜也因 YK=0 失败）。
    成功才把 clone 状态写回 g；失败保持 g 不变，返回 False。"""
    c = g.clone()
    err0 = len(c.errors)
    try:
        go_to_decomposed(c, fid, x, y, note)
        del c.errors[err0:]
        g.__dict__.update(c.__dict__)
        return True
    except RouteError:
        return False


def _stair_pos(g: Game, fid: str, direction: str) -> tuple[int, int] | None:
    """地图 fid 楼层 direction(upFloor/downFloor)stair block 位置(不管可达)。
    _find_stair 保守(要求邻居 reachable,enemy/door 挡时返回 None);这里直接给
    stair 位置,让 go_to_decomposed 处理路径 door 开门 + enemy 杀。"""
    floor = g.floors[fid]
    for (x, y), b in floor.blocks.items():
        if b.eid == direction:
            return (x, y)
    return None


def _open_reachable_door(g: Game, fid: str) -> bool:
    """开 fid 楼层可达的 door(hero 有钥匙),连通 stair 区。
    逐层上楼时 _find_stair 返回 None(出口 door 挡,如 MT7 (11,7) yellowDoor
    挡 upFloor 区,hero 在 downFloor 区到不了 stair)。事务化。"""
    cf = _flood_floor(g, fid, break_fakewalls=True)
    for b in cf.blockers:
        if b.kind != "door":
            continue
        yk, bk, rk = b.need
        if yk and g.state["yk"] <= 0:
            continue
        if bk and g.state["bk"] <= 0:
            continue
        if rk and g.state["rk"] <= 0:
            continue
        if _tx_go_to(g, fid, b.pos[0], b.pos[1], f"open door {b.pos}"):
            return True
    return False


def acquire_resource(g: Game, target_fid: str, x: int, y: int, eid: str,
                     allow_resource_search: bool = True) -> None:
    """获取 target_fid 资源：多楼层导航(经楼梯，内部步骤)+事务化 go_to。

    下楼/上楼只是取资源的手段，不是搜索目标。失败抛 RouteError（搜索剪枝）。
    导航 go_to 事务化(clone+回滚)：失败后在干净态回搜钥匙补 deficit 再试。
    deficit 用广集 _ALL_KEYS：flood 乐观(开门不扣钥匙预算)报不出 deficit
    （有 ≥1 把钥匙时所有门都"能开"，blockers 为空），go_to 失败本身就证明缺
    钥匙，故失败/stair 不可达时跨层回搜全钥匙类型。回搜后 hero 可能在别的
    楼层，外层循环重定位重新导航。目标被 fakeWall 挡 -> 破可达 fakeWall 重试。"""
    # 导航到 target 楼层: 已访问楼层 transition 直达(一步到 fly_points 落地点,
    # 匹配 walk 下楼直达 MT9->MT7 -- walk.md 下楼不记 pass downFloor,只 ### 楼层标题,
    # 因为下楼是 transition record "换层" 被 gen_zone_walk_md 跳过)。
    # 首次访问楼层必须走楼梯(web 禁 fly 到未访问楼层):逐层 _find_stair+transition。
    # 逐层楼梯会因中间楼层楼梯被门/怪挡而回搜失败(RouteError 假阴性),但目标楼层
    # 已访问时 transition 直达绕过中间层(可达矩阵 cross_floor_reachable 已证跨层可达)。
    if g.state["floor"] != target_fid:
        if target_fid in g.visited:
            g.transition(target_fid, f"nav fly->{target_fid}")
        else:
            for _round in range(80):
                if g.state["floor"] == target_fid:
                    break
                cur = g.state["floor"]
                cur_n = _floor_n(cur)
                tgt_n = _floor_n(target_fid)
                direction = "upFloor" if tgt_n > cur_n else "downFloor"
                stair = _find_stair(g, cur, direction)
                if stair is not None and _tx_go_to(g, cur, stair[0], stair[1], f"nav {cur}"):
                    next_fid = f"MT{cur_n + (1 if tgt_n > cur_n else -1)}"
                    g.transition(next_fid, f"nav {cur}->{next_fid}")
                    continue
                # _find_stair None(出口 door/enemy 挡,保守) 或 go_to 失败:
                # 直接 go_to 地图 stair 位置(go_to_decomposed 处理路径 door+enemy)。
                # 如 MT7 upFloor (1,1) 被 (11,7) yellowDoor + (9,7) skeletonSoldier 挡。
                pos = _stair_pos(g, cur, direction)
                if pos is not None and _tx_go_to(g, cur, pos[0], pos[1], f"nav {cur} direct"):
                    next_fid = f"MT{cur_n + (1 if tgt_n > cur_n else -1)}"
                    g.transition(next_fid, f"nav {cur}->{next_fid}")
                    continue
                # 楼梯走不通或不可达: 先开可达 door(有钥匙,连通 stair 区),再补钥匙
                if _open_reachable_door(g, cur):
                    continue
                # 当前楼层补钥匙，再跨层回搜全钥匙类型
                got = _fetch_deficit_key_on_floor(g, cur)
                if not got and allow_resource_search:
                    got = _search_resource(g, _ALL_KEYS)
                if not got:
                    raise RouteError(f"cannot reach {direction} stair on {cur} -> {target_fid}")
                # 回搜成功(可能换楼层)，外层循环重新导航
            else:
                raise RouteError(f"nav to {target_fid} exceeded rounds")
    # 取资源：事务化 go_to；fakeWall 挡破之，钥匙不够跨层回搜，邻居怪挡打之。
    # 顺序: fakeWall -> 搜钥匙(YK 不够开门时先拿) -> 邻居怪(target 被静态怪围)。
    # 搜钥匙在打邻居怪前: 如 MT10 redGem 路径需 2 yellowDoor 但 YK=1,需先回搜
    # MT7 yellowKey 拿 YK,否则打邻居怪(go_to (9,6) 也需开门)失败无法继续。
    for _ in range(10):
        if _tx_go_to(g, target_fid, x, y, f"acquire {eid}"):
            return
        if _break_one_reachable_fakewall(g, target_fid):
            continue
        if allow_resource_search and _search_resource(g, _ALL_KEYS):
            continue
        if _break_neighbor_monster(g, target_fid, x, y):
            continue
        raise RouteError(f"cannot reach {target_fid} x{x}y{y} {eid}")
    raise RouteError(f"acquire {eid} exceeded retry attempts")


def _deficit_keys(game: Game, cf) -> set[str]:
    """当前楼层骨架资源被钥匙门挡时，返回所需钥匙 eid 集合（按需补）。"""
    need: set[str] = set()
    for b in cf.blockers:
        if b.kind != "door":
            continue
        yk, bk, rk = b.need
        if yk and game.state["yk"] <= 0:
            need.add("yellowKey")
        if bk and game.state["bk"] <= 0:
            need.add("blueKey")
        if rk and game.state["rk"] <= 0:
            need.add("redKey")
    return need


def skeleton_actions(game: Game) -> Iterable[GameAction]:
    _N["n"] += 1
    if _N["n"] % 10 == 0:
        el = time.perf_counter() - _T0
        s = game.state
        print(f"  [progress] exp={_N['n']} {s['floor']} HP={s['hp']} ATK={s['atk']} "
              f"DEF={s['def']} G={s['gold']} dmg={s['dmg']} {el:.1f}s", flush=True)
    # 死亡/出错状态剪枝
    if game.state["hp"] <= 0 or game.errors:
        return []
    acts: list[GameAction] = []
    cur = game.state["floor"]
    cf = _flood_floor(game, cur, break_fakewalls=True)
    # 1) 骨架资源 acquire(全 MT1-10 未拾取的宝石/剑/盾): acquire_resource 内部跨层
    #    导航(经楼梯),A* 一步到远楼层刷资源。不用 stair 动作: stair 换层和 state_key
    #    去 floor 冲突(child_key==key 被 A* 当 no-op 跳过),加 floor 又让 sword1/shield1
    #    去重弱慢 3x。动作空间靠 state_key 去 x/y + hp//20 强去重收敛(同楼层位置合并,扩展少)。
    #    可达性由 acquire_resource 内部 go_to 精确判断,失败抛 RouteError 由 A* 剪枝。
    for fid, x, y, eid in _static_skeleton(game):
        if game.block_at(fid, (x, y)) is None:
            continue  # 已拾取
        if _is_reserved(fid, eid):
            continue  # 本段不碰(留给后续段)
        def make_acq(fid=fid, x=x, y=y, eid=eid):
            def apply(g: Game) -> None:
                acquire_resource(g, fid, x, y, eid)
            return apply
        acts.append(GameAction(name=f"acquire {fid} x{x}y{y} {eid}", apply=make_acq()))
    # 1b) 钥匙 acquire(跨层,存量低时,仅 boss 段): boss 段需 YK=3(MT10 blueGem 1门+
    #    redGem 2门) + RK=1(redDoor(6,9) 开 boss 路径)。低楼层就近补,避免上 MT10 后
    #    下楼耗 YK。sword1/shield1/gem 段不加(动作空间爆炸 6x)。
    if _seg_flag("acquire_keys"):
        for fid, x, y, eid in _static_keys(game):
            if game.block_at(fid, (x, y)) is None:
                continue
            if eid == "yellowKey" and game.state["yk"] >= 4:
                continue
            if eid == "blueKey" and game.state["bk"] >= 2:
                continue
            if eid == "redKey" and game.state["rk"] >= 1:
                continue
            def make_key_acq(fid=fid, x=x, y=y, eid=eid):
                def apply(g: Game) -> None:
                    acquire_resource(g, fid, x, y, eid)
                return apply
            acts.append(GameAction(name=f"acquire {fid} x{x}y{y} {eid}", apply=make_key_acq()))
    # shop（商店购买也是骨架节点；NPC 不可踩，用 move_adjacent 贴邻）。
    # boss 段不买属性商店(27/27 后不需,减动作空间加速)。
    if not _seg_flag("acquire_keys"):
        for e in [e for e in cf.entries if e.kind == "shop"]:
            x, y, eid = e.pos[0], e.pos[1], e.eid
            def make_shop(fid=cur, x=x, y=y, eid=eid):
                def apply(g: Game) -> None:
                    g.move_adjacent(fid, x, y, f"shop {eid}")
                return apply
            acts.append(GameAction(name=f"shop {cur} x{x}y{y} {eid}", apply=make_shop()))
    # 2) 按需补充：当前楼层 gem 被钥匙门挡时补对应钥匙；HP 低时补药水。
    #    （钥匙/药水不作常态目标，只在缺口时补，避免 cheap 下探 flailing）
    need_keys = _deficit_keys(game, cf)
    for e in [e for e in cf.entries if e.kind == "supplement_key" and e.eid in need_keys]:
        x, y, eid = e.pos[0], e.pos[1], e.eid
        def make_key(fid=cur, x=x, y=y, eid=eid):
            def apply(g: Game) -> None:
                go_to_decomposed(g, fid, x, y, f"supplement {eid}")
            return apply
        acts.append(GameAction(name=f"supplement {cur} x{x}y{y} {eid}", apply=make_key()))
    # 缺钥匙时，cheap 怪（杀掉掉钥匙）也作补充目标——钥匙就是搜索目标
    if game.state["yk"] < 4 or need_keys:
        # cheap 怪(杀掉掉钥匙/金币 + auto_sweep 拾附近 yellowKey):YK<4 或缺钥匙时
        # 主动探索 kill 怪得 YK 分支(walk 7F atk=23 kill skeleton 得 YK+2 补刷 gem)。
        # flood optimistic 开门不扣钥匙报不出 deficit,故不能只 need_keys 触发。
        # 筛 cheap top-5(打怪少掉血)避免动作空间爆炸。
        cheap_monsters = sorted([e for e in cf.entries if e.kind == "monster"],
                                key=lambda e: (e.access_dmg, e.path_len))[:5]
        for e in cheap_monsters:
            x, y, eid = e.pos[0], e.pos[1], e.eid
            def make_mon(fid=cur, x=x, y=y, eid=eid):
                def apply(g: Game) -> None:
                    go_to_decomposed(g, fid, x, y, f"kill {eid} for keys/gold")
                return apply
            acts.append(GameAction(name=f"kill {cur} x{x}y{y} {eid}", apply=make_mon()))
    if game.state["hp"] < 250:
        for e in [e for e in cf.entries if e.kind == "supplement_potion"]:
            x, y, eid = e.pos[0], e.pos[1], e.eid
            def make_pot(fid=cur, x=x, y=y, eid=eid):
                def apply(g: Game) -> None:
                    go_to_decomposed(g, fid, x, y, f"supplement {eid}")
                return apply
            acts.append(GameAction(name=f"supplement {cur} x{x}y{y} {eid}", apply=make_pot()))
    # 2b) 跨层药水 acquire(仅 boss 段,全 A*): HP<634 才加(boss 清场 634 dmg,够了不补,
    #    避免动作爆炸)。acquire_resource 跨层经门/怪(锁区药水),A* 发现补 HP 调度。
    if _seg_flag("acquire_potions") and game.state["hp"] < 634:
        for fid, x, y, eid in _static_potions(game):
            if game.block_at(fid, (x, y)) is None:
                continue
            def make_pot_acq(fid=fid, x=x, y=y, eid=eid):
                def apply(g: Game) -> None:
                    acquire_resource(g, fid, x, y, eid)
                return apply
            acts.append(GameAction(name=f"acquire {fid} x{x}y{y} {eid}", apply=make_pot_acq()))
    # 2c) buy trader(钥匙商人,仅 boss 段): MT6 50G->1BK / MT7 50G->5YK。
    #     一次性(flag)。A* 发现买 trader 替代 kill 怪/绕路补钥匙(5YK=250HP 价值 -50G,优于 kill)。
    if _seg_flag("acquire_keys"):
        for (tfid, tpos), spec in TRADER_KEY_MAP.items():
            _cost, yk_g, bk_g, rk_g, tkey_eid = spec
            if tkey_eid == "yellowKey" and game.state["yk"] >= 4:
                continue
            if tkey_eid == "blueKey" and game.state["bk"] >= 2:
                continue
            if game.state["gold"] < _cost:
                continue
            if game.flags.get(Game.trader_flag(tfid, tpos[0], tpos[1])):
                continue
            def make_trader(tfid=tfid, tpos=tpos, tkey_eid=tkey_eid):
                def apply(g: Game) -> None:
                    if g.state["floor"] != tfid and tfid in g.visited:
                        g.transition(tfid, f"nav fly->{tfid} (trader)")
                    g.talk_trader(tfid, tpos[0], tpos[1], f"buy {tkey_eid} from trader")
                return apply
            acts.append(GameAction(name=f"buy trader {tfid} {tpos} {tkey_eid}", apply=make_trader()))
    # 3) MT10 boss 触发（终态）：(6,5) 可达且 boss 未清时。仅 boss 段(goal boss)触发,
    #    避免宝石段误打 boss。
    if (cur == "MT10" and not _boss_cleared(game)
            and BOSS_TRIGGER in cf.reachable_cells
            and _CUR_SEG and _CUR_SEG["goal"].get("boss")):
        def apply_boss(game: Game) -> None:
            game.go_to("MT10", BOSS_TRIGGER[0], BOSS_TRIGGER[1], "10F boss 触发")
            if game.steps and game.steps[-1].get("action") == "到达":
                game.steps[-1]["action"] = "事件"
                game.steps[-1]["eid"] = "bossEvent"
            for sp_pos, sp_eid in SPAWNED_BOSS.items():
                game.set_block("MT10", sp_pos, "enemy", sp_eid)
            cleared = game.clear_mt10_boss_dyn()
            if game.state["hp"] <= 0 or game.errors:
                raise RouteError(f"MT10 boss death/error cleared={cleared}")
            if cleared and game.steps:
                game.refresh_last_step(
                    game.steps[-1]["before"],
                    "clearMt10BossDyn 动态清: " + ", ".join(cleared),
                )
        acts.append(GameAction(name="trigger MT10 boss", apply=apply_boss))
    return acts


def goal(game: Game) -> bool:
    s = game.state
    if s["hp"] <= 0:
        return False
    return s["floor"] == "MT10" and _boss_cleared(game)


def heuristic(game: Game) -> float:
    """估到 boss cleared 的剩余成本(dmg)。全 A* boss 段引导:27/27 -> RK -> HP -> boss。
    每步估成本,让 A* 愿扩展中间步(buy trader/visit MT10 虽 dmg 增但减 h)。"""
    s = game.state
    fn = _floor_n(s["floor"])
    if fn >= 10 and _boss_cleared(game):
        return 0.0
    h = max(0, 27 - s["atk"]) * 150.0 + max(0, 27 - s["def"]) * 150.0  # 刷 gem(150 dmg/gem)
    if s["atk"] < 27 or s["def"] < 27:
        if "MT10" not in game.visited:
            h += 200.0  # 需 visit MT10(4黄门绕路/BK 短路)
            if s["bk"] < 1:
                h += 50.0  # 需买 BK(MT6)或 4 YK 绕路
    else:
        h += float(max(0, 10 - fn)) * 10.0  # 上 MT10
        if s["rk"] < 1:
            h += 400.0  # 需拿 redKey(MT8 yellowGuard 378 + 路径)
        if s["hp"] < 634:
            h += float(max(0, 634 - s["hp"]))  # 需补 HP(boss 634 dmg)
    return h


# ---- 可配置里程碑分段(Req4: 可注入线路压缩搜索空间 + 引导生存序)----
# 每段声明式 dict: goal spec + reserve + acquire_keys/acquire_potions + weight。
# goal spec: pick(资源组,全拿)/ atk_ge,def_ge(属性达标)/ floor(到达楼层)/ boss。
# pick item: "fid:eid" / "fid:*"(该层所有 skeleton) / "*" / 裸 eid(sword1 唯一)。
# reserve: 本段不碰的资源(过滤 skeleton_actions 的 acquire),留给后续段。
# 段内 sub-goal 拆分(每轮拿一个未拿 pick 资源,近 goal 避免 width-first)。
# 段间 _key_value(BK=200HP)衔接。剑->盾9F->1-8F->10F(27/27)->boss。
SEGMENTS = [
    {"name": "sword1", "goal": {"pick": ["sword1"]}},
    {"name": "shield_9f",
     "goal": {"pick": ["shield1", "MT9:redGem", "MT9:blueGem"]},
     "reserve": ["MT10:*"],
     "single_astar": True,
     "enemy_h": True,
     "weight": 1.0},  # L2 必经怪预计算启用(Dijkstra 最小伤害路径怪, 避 skeletonSoldier 选绕路)。weight=1 reserve MT10: dmg 932(达 goal, 但 over-eat MT6 blueGem+MT7 redGem 不拿 MT4 redGem)。reserve MT5-8: weight=1/2 exhausted(卡低层不上楼), weight=3 dmg 1166(拿 MT4 redGem 但杀 skeletonSoldier 补钥匙)。未达最优 754, 剩余瓶颈=MT7 redGem 顺路优先 + 钥匙搜索杀 skeletonSoldier, 非 enemy_h。
    {"name": "gems_1_8",
     "goal": {"pick": ["MT1:*", "MT3:*", "MT4:*", "MT5:*",
                      "MT6:*", "MT7:*", "MT8:*"]},
     "reserve": ["MT9:*", "MT10:*"]},
    {"name": "gems_10",
     "goal": {"pick": ["MT10:redGem", "MT10:blueGem"]},
     "acquire_keys": True},  # 需 buy trader/补 YK 上 10F
    {"name": "boss", "goal": {"boss": True},
     "acquire_keys": True, "acquire_potions": True, "weight": 0.0},
]

# 当前段配置(skeleton_actions 读 reserve/acquire_*)。run_segment 入口设。
_CUR_SEG: dict | None = None
# 段起点楼层(L2 enemy_h: lo 固定段起点, 不随 cur 变; 回头拿 gem 不让低层怪入 h 惩罚回头)。
_CUR_START_FLOOR_N: int = 0


def _match_pick(item: str, fid: str, eid: str) -> bool:
    """pick/reserve item 匹配: 'fid:eid' / 'fid:*' / '*' / 裸 eid。"""
    if item == "*":
        return True
    if ":" in item:
        pf, pe = item.split(":", 1)
        return (pf == fid or pf == "*") and (pe == eid or pe == "*")
    return item == eid


def _is_reserved(fid: str, eid: str) -> bool:
    if not _CUR_SEG:
        return False
    return any(_match_pick(r, fid, eid) for r in _CUR_SEG.get("reserve", []))


def _seg_flag(name: str) -> bool:
    """段 flag(acquire_keys/acquire_potions),兼容旧 _BOSS_PHASE。"""
    return bool(_CUR_SEG and _CUR_SEG.get(name)) or _BOSS_PHASE


def _pick_items(goal_spec: dict) -> list[str]:
    return goal_spec.get("pick", [])


def _pick_missing(game: Game, pick: list[str]) -> int:
    """pick 中未拾取的资源数(用于 goal 判定 + sub-goal 计数)。"""
    n = 0
    for item in pick:
        for fid, x, y, eid in _static_skeleton(game):
            if _match_pick(item, fid, eid) and game.block_at(fid, (x, y)) is not None:
                n += 1
    return n


def _state_key(game: Game):
    s = game.state
    # 保留 floor: stair 换层状态不能合并,否则 stair 动作 child_key==key 被 A* 当 no-op
    # 跳过(line 219),A* 无法换层(gem 段卡在无骨架宝石的楼层 exhausted)。
    # 去 x/y(同楼层内位置合并,强去重) + hp//20(dmg 隐含)。
    # 保留 yd/bd/rd(累计门消耗,影响 final-score/Pareto 支配,不可去)。
    # sword/shield 拾取指纹: 区分是否已拿装备(未拿的还能拿,后续可选动作不同)。
    # gem 拾取隐含在 atk/def(同 atk/def 后续打怪 dmg 一样,不用单独存)。
    ss = frozenset(
        eid for fid, x, y, eid in _static_skeleton(game)
        if (eid.startswith("sword") or eid.startswith("shield"))
        and game.block_at(fid, (x, y)) is None
    )
    base = (s["floor"], s["yk"], s["bk"], s["rk"],
            s["yd"], s["bd"], s["rd"], s["gold"] // 50, ss)
    if _PARETO:
        # Pareto 模式: state_key 去 atk/def,让不同 atk/def 的状态同 key,
        # Pareto frontier (dmg,-atk,-def) 保留非支配(刷宝石分支 dmg+atk+ 不被
        # dmg-min 分支 dmg-atk- 剪掉)。atk/def 由 Pareto 向量而非 state_key 区分。
        return base
    return (s["atk"], s["def"]) + base


def _key_value(g: Game) -> int:
    """钥匙+金币的 HP 估值(分数模型:1YK=50,1BK=4YK=200,1RK>=500,100G=1YK=50)。
    链式衔接排序用此替代 yk+bk+rk 简单计数(BK 当 1 低估 4x,和 YK=50HP 对齐)。"""
    s = g.state
    return 100 * s["yk"] + 500 * s["bk"] + 500 * s["rk"] + s["gold"]


def _pareto_metrics():
    """Pareto 多目标向量(越小越好)。主分量 dmg 用于 priority/upper_bound,
    副分量 -atk/-def 让刷宝石分支(atk/def 高)不被 dmg-min 分支支配。"""
    if not _PARETO:
        return None
    return (
        lambda g: int(g.state["dmg"]),
        lambda g: -int(g.state["atk"]),
        lambda g: -int(g.state["def"]),
    )


def make_goal(goal_spec: dict):
    """goal spec -> predicate。pick(全拿)/atk_ge/def_ge/floor/boss,可 AND 组合。"""
    if goal_spec.get("boss"):
        return goal
    pick = _pick_items(goal_spec)
    atk_ge = goal_spec.get("atk_ge")
    def_ge = goal_spec.get("def_ge")
    flr = goal_spec.get("floor")

    def _g(game: Game) -> bool:
        if game.state["hp"] <= 0:
            return False
        s = game.state
        if pick and _pick_missing(game, pick) > 0:
            return False
        if atk_ge is not None and s["atk"] < atk_ge:
            return False
        if def_ge is not None and s["def"] < def_ge:
            return False
        if flr is not None and s["floor"] != flr:
            return False
        return True
    return _g


def make_heuristic(goal_spec: dict):
    """朝未拿 pick / 属性缺口 / 楼层 / boss 的剩余成本估计。"""
    if goal_spec.get("boss"):
        return heuristic
    pick = _pick_items(goal_spec)
    atk_ge = goal_spec.get("atk_ge")
    def_ge = goal_spec.get("def_ge")
    flr = goal_spec.get("floor")

    def _h(game: Game) -> float:
        s = game.state
        h = 0.0
        if pick:
            # 楼层差*100 + 同层曼哈顿(跨层导航朝 pick); 旧 pick_missing*80 无楼层方向会卡低层
            h += _pick_heuristic(game, pick)
            # L2 倒推(enemy_h 段): 必经楼层活怪总伤害, gem 价值隐含
            # (没拿段内 redGem 时 atk 低 -> 怪伤害高 -> h 高, 推动 A* 回头拿 gem 降 h)。
            if _CUR_SEG and _CUR_SEG.get("enemy_h"):
                h += _seg_enemy_h(game, pick)
        if atk_ge is not None:
            h += max(0, atk_ge - s["atk"]) * 3.0
        if def_ge is not None:
            h += max(0, def_ge - s["def"]) * 3.0
        if flr is not None:
            h += abs(_floor_n(flr) - _floor_n(s["floor"])) * 30.0
        return h
    return _h


def run_segment(seg: dict, start_g: Game, max_exp: int, top_k: int,
                weight: float | None = None) -> tuple[Game, bool]:
    """段执行器。pick 多资源 -> sub-goal 拆分(每轮拿一个未拿,近 goal 避免 width-first);
    单资源/属性/floor/boss -> 单次 A*。返回 (best_game, ok)。"""
    global _CUR_SEG, _CUR_START_FLOOR_N, _CUR_MUST_KILL
    _CUR_SEG = seg
    _CUR_START_FLOOR_N = _floor_n(start_g.state["floor"])
    _CUR_MUST_KILL = (_precompute_must_kill(start_g, _pick_items(seg["goal"]))
                      if seg.get("enemy_h") else None)
    try:
        gs = seg["goal"]
        pick = _pick_items(gs)
        if pick and len(pick) > 1 and not gs.get("boss") and not seg.get("single_astar"):
            cur = run_pick_subgoals(seg, start_g, max_exp, top_k)
            return cur, _pick_missing(cur, pick) == 0
        res = _run_segment_one(seg, start_g, max_exp, top_k, weight)
        cur = res.top_goals[0][1] if res.top_goals else start_g
        return cur, res.found
    finally:
        _CUR_SEG = None


def _run_segment_one(seg, start_g, max_exp, top_k, weight=None):
    _T0_seg = time.perf_counter()
    _N["n"] = 0
    if seg.get("enemy_h") and _CUR_MUST_KILL:
        for fid, must in sorted(_CUR_MUST_KILL.items()):
            print(f"  [must_kill {fid}] {[(x,y,eid) for x,y,eid in must]}", flush=True)
    w = seg.get("weight", weight if weight is not None else 3.0)
    astar = GameAStar(
        actions=skeleton_actions,
        goal=make_goal(seg["goal"]),
        heuristic=make_heuristic(seg["goal"]),
        edge_cost=lambda b, a, _act: float(max(0, a.state["dmg"] - b.state["dmg"])),
        state_key=_state_key,
        weight=w,
        max_expansions=max_exp,
        top_k=top_k,
        pareto_metrics=_pareto_metrics(),
    )
    res = astar.search(start_g)
    el = time.perf_counter() - _T0_seg
    name = seg["name"]
    s = start_g.state
    print(f"\n[seg {name}] start {s['floor']} HP={s['hp']} ATK={s['atk']} DEF={s['def']} "
          f"YK={s['yk']} dmg={s['dmg']}", flush=True)
    print(f"[seg {name}] found={res.found} cost={res.cost} exp={res.expansions} "
          f"gen={res.generated} reason={res.reason} {el:.1f}s", flush=True)
    if res.top_goals:
        for i, (c, gm, _rt) in enumerate(res.top_goals[:10]):
            st = gm.state
            print(f"  #{i+1} dmg={st['dmg']}(cost={c:.0f}) HP={st['hp']} ATK={st['atk']} DEF={st['def']} "
                  f"YK={st['yk']} BK={st['bk']} RK={st['rk']} G={st['gold']} {st['floor']}", flush=True)
    return res


_ALL_ENEMIES: list[tuple[str, int, int, str]] | None = None


def _all_enemies(g: Game) -> list[tuple[str, int, int, str]]:
    """MT1-10 所有静态怪位置(位置不随状态变,杀怪只改 block)。缓存。"""
    global _ALL_ENEMIES
    if _ALL_ENEMIES is None:
        out: list[tuple[str, int, int, str]] = []
        for fid in sorted(g.floors, key=lambda f: int(f[2:]) if f.startswith("MT") else 0):
            if not (fid.startswith("MT") and 1 <= int(fid[2:]) <= 10):
                continue
            for (x, y), block in g.floors[fid].blocks.items():
                if block.kind == "enemy":
                    out.append((fid, x, y, block.eid))
        _ALL_ENEMIES = out
    return _ALL_ENEMIES


_CUR_MUST_KILL: dict[str, list[tuple[int, int, str]]] | None = None


def _find_upstair(g: Game, fid: str):
    """该层 upFloor 楼梯块位置(上到上层的出口)。"""
    for (x, y), blk in g.floors[fid].blocks.items():
        if blk.eid == "upFloor":
            return (x, y)
    return None


def _pick_main_pos(g: Game, pick: list[str], fid: str):
    """pick 中该层首个未拿 skeleton 位置(目标层出口, 如 shield1)。"""
    for item in pick:
        for sfid, x, y, eid in _static_skeleton(g):
            if sfid == fid and _match_pick(item, fid, eid) and g.block_at(fid, (x, y)) is not None:
                return (x, y)
    return None


def _pick_target_floor(g: Game, pick: list[str]) -> str:
    """pick 中最高楼层(段目标楼层, 如 MT9)。"""
    floors = []
    for item in pick:
        for fid, x, y, eid in _static_skeleton(g):
            if _match_pick(item, fid, eid):
                floors.append(fid)
    if not floors:
        return g.state["floor"]
    return max(floors, key=lambda f: _floor_n(f))


def _dijkstra_path(g: Game, fid: str, start, goal):
    """最小伤害路径(Dijkstra, 怪伤害为边权, 用 g 当前 atk/def 预计算=段起点)。
    避高伤怪(skeletonSoldier)选绕路, bat/bluePriest 低伤入选。
    BFS 最短格子会经 skeletonSoldier(格子少但伤高)误当必经; Dijkstra 按伤害选才符合最优绕路。"""
    atk = g.state["atk"]
    def_ = g.state["def"]
    dist = {start: 0.0}
    prev = {}
    pq = [(0.0, start)]
    while pq:
        d, cur = heapq.heappop(pq)
        if cur == goal:
            path = [cur]
            while cur in prev:
                cur = prev[cur]
                path.append(cur)
            return list(reversed(path))
        if d > dist.get(cur, float("inf")):
            continue
        x, y = cur
        for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            nx, ny = x + dx, y + dy
            if g.is_wall(fid, (nx, ny)):
                continue
            blk = g.block_at(fid, (nx, ny))
            cost = 0.0
            if blk and blk.kind == "enemy":
                try:
                    ed = g.enemy_damage(blk.eid)
                except Exception:
                    ed = 0.0
                if ed == float("inf") or ed != ed or ed < 0:
                    ed = 0.0  # 不可杀视 0(乐观, Dijkstra 可选但 h 实际算 inf 跳过)
                cost = float(ed)
            nd = d + cost
            if nd < dist.get((nx, ny), float("inf")):
                dist[(nx, ny)] = nd
                prev[(nx, ny)] = cur
                heapq.heappush(pq, (nd, (nx, ny)))
    return None


def _precompute_must_kill(g: Game, pick: list[str]):
    """预计算 start_floor..target_floor 每层上楼必经怪。
    起点层落点=hero 位置; 中间层落点=fly_points downFloor; 目标层出口=pick 主资源(shield1),
    其余层出口=upFloor 楼梯。BFS 最短格子路径上的活怪 = 必经怪(用户 bat×5+bluePriest 即此)。
    只算必经怪(非全怪), 避免 over-eat(拿非路径 gem) + 卡低层(杀非必经怪净0扩展)。"""
    out: dict[str, list[tuple[int, int, str]]] = {}
    target_floor = _pick_target_floor(g, pick)
    s_fn = _floor_n(g.state["floor"])
    t_fn = _floor_n(target_floor)
    for fid in g.floors:
        if not (fid.startswith("MT") and s_fn <= _floor_n(fid) <= t_fn):
            continue
        if fid == g.state["floor"]:
            landing = (g.state["x"], g.state["y"])
        else:
            lp = g.fly_points.get(fid, {}).get("downFloor")
            landing = tuple(lp) if lp else None
        if fid == target_floor:
            exit_pos = _pick_main_pos(g, pick, fid)
        else:
            exit_pos = _find_upstair(g, fid)
        if landing is None or exit_pos is None:
            continue
        path = _dijkstra_path(g, fid, landing, exit_pos)
        if not path:
            continue
        must = []
        for (x, y) in path:
            blk = g.block_at(fid, (x, y))
            if blk and blk.kind == "enemy":
                must.append((x, y, blk.eid))
        out[fid] = must
    return out


def _seg_enemy_h(game: Game, pick: list[str]) -> float:
    """L2 倒推(必经怪版): 预计算的必经怪(每层落点->出口 BFS 最短路径怪)在当前 atk/def 下的伤害。
    gem 价值隐含--没拿段内 redGem 时 atk 低、必经 bat/bluePriest 伤害高、h 高; 拿了 redGem
    atk+1、这些必经怪伤害降(bat×5×28 + bluePriest 55≈195)、h 降, A* 偏好回头拿 redGem。
    只算必经怪(非全 MT5-9 怪): 不 over-eat(非路径 gem 不降必经怪外 h) + 不卡低层(杀非必经怪不降 h)。"""
    if not pick or not _CUR_MUST_KILL:
        return 0.0
    total = 0.0
    for fid, must in _CUR_MUST_KILL.items():
        for (x, y, eid) in must:
            if game.block_at(fid, (x, y)) is None:
                continue  # 已杀
            try:
                d = game.enemy_damage(eid)
            except Exception:
                continue
            if d == float("inf") or d != d or d < 0:
                continue
            total += float(d)
    return total


def _pick_heuristic(game: Game, pick: list[str]) -> float:
    """到最近未拿 pick 资源的启发距离: 楼层差*100 + 同楼层曼哈顿。
    纯 Dijkstra(heuristic=0)会卡在低伤怪楼层盲目杀怪,不朝 pick 走;
    旧 atk 涨 sub-goal 实际充当探索引导,去掉后必须靠 heuristic 指向 pick。"""
    cur_floor = _floor_n(game.state["floor"])
    cx, cy = game.state["x"], game.state["y"]
    best = float("inf")
    for item in pick:
        for fid, x, y, eid in _static_skeleton(game):
            if _match_pick(item, fid, eid) and game.block_at(fid, (x, y)) is not None:
                fd = abs(_floor_n(fid) - cur_floor) * 100
                mh = abs(x - cx) + abs(y - cy) if fid == game.state["floor"] else 0
                d = fd + mh
                if d < best:
                    best = d
    return best if best != float("inf") else 0.0


def run_pick_subgoals(seg, start_g, max_exp, top_k):
    """pick 多资源 sub-goal 拆分: 每轮 goal=拿一个未拿 pick 资源(_pick_missing 减),
    Dijkstra 近 goal 避免 width-first。HP 不够补血 sub-goal 再重试。
    链式衔接 HP 截断 250(生存)+ _key_value(BK=200HP)+ dmg 最低。"""
    cur = start_g
    pick = _pick_items(seg["goal"])
    rounds = 0
    heals = 0
    _N["n"] = 0
    name = seg["name"]
    while _pick_missing(cur, pick) > 0:
        rounds += 1
        if rounds > 40:
            print(f"!! {name} subgoal 超 40 轮 (missing={_pick_missing(cur, pick)})", flush=True)
            break
        miss0 = _pick_missing(cur, pick)

        def make_subgoal(miss0=miss0, cf=_floor_n(cur.state["floor"])):
            def _g(game: Game) -> bool:
                if game.state["hp"] <= 0:
                    return False
                # 拿一个未拿 pick,或上楼推进(朝 MT9 pick,不绕吃宝石涨属性)。
                # 旧 atk 涨 sub-goal 让 A* 绕 MT3/4/5/6 吃宝石(HP144 dmg1732 vs 最优 754);
                # 去 atk 涨后纯 Dijkstra 卡低层无方向,上楼给楼层导向。
                return (_pick_missing(game, pick) < miss0
                        or _floor_n(game.state["floor"]) > cf)
            return _g

        astar = GameAStar(
            actions=skeleton_actions,
            goal=make_subgoal(),
            heuristic=lambda g: _pick_heuristic(g, pick),
            edge_cost=lambda b, a, _act: float(max(0, a.state["dmg"] - b.state["dmg"])),
            state_key=_state_key,
            weight=0.5,
            max_expansions=max_exp,
            top_k=top_k,
            pareto_metrics=_pareto_metrics(),
        )
        res = astar.search(cur)
        ns = res.game.state if res.game else cur.state
        miss1 = _pick_missing(res.game, pick) if res.game else miss0
        print(f"[{name} sub {rounds}] missing {miss0}->{miss1} found={res.found} "
              f"exp={res.expansions} HP={ns['hp']} ATK={ns['atk']} DEF={ns['def']} "
              f"YK={ns['yk']} dmg={ns['dmg']} {ns['floor']}", flush=True)
        if not res.top_goals:
            if cur.state["hp"] < 250 and heals < 8:
                heals += 1
                cur = _heal_subgoal(cur, max_exp, top_k, rounds)
                if cur.state["hp"] > 0:
                    continue
            print(f"!! {name} subgoal 未达,停止", flush=True)
            break
        cur = max(res.top_goals, key=lambda t: (
            min(t[1].state["hp"], 250), t[1].state["atk"], t[1].state["def"],
            _key_value(t[1]), -t[0]))[1]
    print(f"[{name} done] rounds={rounds} heals={heals} missing={_pick_missing(cur, pick)} "
          f"ATK={cur.state['atk']} DEF={cur.state['def']} HP={cur.state['hp']} "
          f"YK={cur.state['yk']} BK={cur.state['bk']} dmg={cur.state['dmg']}", flush=True)
    return cur


def _heal_subgoal(cur: Game, max_exp: int, top_k: int, rnd: int) -> Game:
    """补血 sub-goal: 拿药水使 HP 净涨 50+(打怪掉血 + 拿药水仍需净涨)。
    药水有限,找不到时返回原状态(上层 break)。"""
    sh = cur.state["hp"]

    def goal(game: Game) -> bool:
        if game.state["hp"] <= 0:
            return False
        return game.state["hp"] > sh + 50  # 净涨 50+(拿药水,非空走)

    astar = GameAStar(
        actions=skeleton_actions,
        goal=goal,
        heuristic=lambda _g: 0.0,
        edge_cost=lambda b, a, _act: float(max(0, a.state["dmg"] - b.state["dmg"])),
        state_key=_state_key,
        weight=0.0,
        max_expansions=max_exp,
        top_k=top_k,
        pareto_metrics=_pareto_metrics(),
    )
    res = astar.search(cur)
    if res.top_goals:
        before = cur.state["hp"]
        cur = max(res.top_goals, key=lambda t: (t[1].state["hp"], -t[0]))[1]
        print(f"  [heal {rnd}] HP {before}->{cur.state['hp']} dmg={cur.state['dmg']} "
              f"{cur.state['floor']}", flush=True)
    else:
        print(f"  [heal {rnd}] 无可达药水补血", flush=True)
    return cur


def run_gem_subgoals(start_g: Game, target_atk: int, target_def: int,
                    max_exp: int, top_k: int) -> Game:
    """gem 段拆 sub-goal: 每轮目标=刷一颗宝石(atk 或 def 涨),Dijkstra 朝近 target。

    远 goal(27/27)下发散:Dijkstra 按 dmg 扩展,dmg-min 分支(不刷宝石)先扩展到死
    仍到不了 27/27。拆成"刷一颗"近 goal,Dijkstra 扩展少量 dmg-min(当前楼层周围)
    后即到刷宝石分支(dmg 稍高但满足 goal)。每轮自主选 dmg 最低的宝石路径。
    链式衔接选 HP 截断 250 优先(生存第一,刷宝石掉血多,HP 太低下轮刷不动)+
    钥匙最多+dmg 最低。HP 不够刷下一颗时,先补血 sub-goal(拿药水)再重试。
    """
    cur = start_g
    rounds = 0
    heals = 0
    _N["n"] = 0
    while cur.state["atk"] < target_atk or cur.state["def"] < target_def:
        rounds += 1
        if rounds > 30:
            print(f"!! gem subgoal 超过 30 轮,停止 (atk={cur.state['atk']} def={cur.state['def']})", flush=True)
            break
        sa, sd = cur.state["atk"], cur.state["def"]

        def make_goal(sa=sa, sd=sd, ta=target_atk, td=target_def):
            def _g(game: Game) -> bool:
                if game.state["hp"] <= 0:
                    return False
                # 平衡 atk/def: 缺口不等时优先刷缺口大的属性,避免一个先到 27
                # 另一个卡在不可达宝石。缺口相等时任刷一颗(让 Dijkstra 选可达的,
                # 不论红蓝),下一轮 imbalance 会再引导平衡。
                atk_gap = ta - sa
                def_gap = td - sd
                if atk_gap > def_gap:
                    return game.state["atk"] > sa  # 缺 atk 多 -> 只刷 redGem
                if def_gap > atk_gap:
                    return game.state["def"] > sd  # 缺 def 多 -> 只刷 blueGem
                return game.state["atk"] > sa or game.state["def"] > sd  # 相等任意
            return _g

        astar = GameAStar(
            actions=skeleton_actions,
            goal=make_goal(),
            heuristic=lambda _g: 0.0,  # Dijkstra(weight=0): 近 goal 朝刷宝石
            edge_cost=lambda b, a, _act: float(max(0, a.state["dmg"] - b.state["dmg"])),
            state_key=_state_key,
            weight=0.0,
            max_expansions=max_exp,
            top_k=top_k,
            pareto_metrics=_pareto_metrics(),
        )
        res = astar.search(cur)
        ns = res.game.state if res.game else cur.state
        print(f"[gem subgoal {rounds}] atk {sa}->{ns['atk']} def {sd}->{ns['def']} "
              f"found={res.found} cost={res.cost} exp={res.expansions} "
              f"HP={ns['hp']} YK={ns['yk']} BK={ns['bk']} dmg={ns['dmg']} {ns['floor']}", flush=True)
        if not res.top_goals:
            # HP 不够刷下一颗(打怪死): 补血 sub-goal 再重试。药水有限,防死循环。
            if cur.state["hp"] < 250 and heals < 8:
                heals += 1
                cur = _heal_subgoal(cur, max_exp, top_k, rounds)
                if cur.state["hp"] > 0:
                    continue
            print("!! gem subgoal 未达目标,停止", flush=True)
            break
        # 链式衔接: HP 截断 250(够生存即可,不盲目堆 HP)+ 钥匙最多 + dmg 最低
        cur = max(res.top_goals, key=lambda t: (
            min(t[1].state["hp"], 250),
            _key_value(t[1]),
            -t[0]))[1]
    print(f"[gem done] rounds={rounds} heals={heals} final atk={cur.state['atk']} "
          f"def={cur.state['def']} HP={cur.state['hp']} dmg={cur.state['dmg']} "
          f"YK={cur.state['yk']} BK={cur.state['bk']}", flush=True)
    return cur


KEY_ATTR = {"yellowKey": "yk", "blueKey": "bk", "redKey": "rk"}


def _fetch_keys_until(cur: Game, key_eid: str, target: int) -> Game:
    """直接 acquire yellowKey/blueKey/redKey 到 target(不用 Dijkstra,就近拿)。
    Dijkstra 在 boss phase 动作空间大(钥匙+药水+gem+supplement+boss ~30 动作)慢
    (27s/exp)。直接 acquire 遍历可达 yellowKey,clone 试,成功(存量增)才写回。

    用可达矩阵筛 0 消耗可达(access_dmg=0, doors_on_path=0 = 路径无怪无门,匹配
    auto_sweep 能拾的 0 消耗资源):不试锁区(doors>0)/未访问楼层的,避免
    acquire_resource 跨层试错失败(如 MT2 x3y4 锁区、MT8 x9y1 锁区)假阴性。"""
    attr = KEY_ATTR[key_eid]
    rounds = 0
    while cur.state[attr] < target:
        rounds += 1
        if rounds > 20:
            break
        got = False
        rm = compute_matrix(cur)
        zero = [e for e in rm.supplement_keys
                if e.eid == key_eid and e.access_dmg == 0 and e.doors_on_path == 0
                and cur.block_at(e.fid, e.pos) is not None]
        zero.sort(key=lambda e: abs(_floor_n(e.fid) - _floor_n(cur.state["floor"])))
        for e in zero:
            fid, x, y, eid = e.fid, e.pos[0], e.pos[1], e.eid
            c = cur.clone()
            try:
                if e.kind == "trader_buy":
                    # 钥匙商人: 跨层 transition(已访问)到 trader 楼层,贴邻 talk_trader 买。
                    if c.state["floor"] != fid:
                        if fid not in c.visited:
                            continue
                        c.transition(fid, f"nav fly->{fid} (trader)")
                    c.talk_trader(fid, x, y, f"buy {eid} from trader")
                else:
                    acquire_resource(c, fid, x, y, eid)
            except RouteError as exc:
                print(f"  [fetch {key_eid}] {fid} x{x}y{y} FAIL: {exc}", flush=True)
                continue
            if c.state[attr] > cur.state[attr]:
                cur.__dict__.update(c.__dict__)
                got = True
                tag = " (trader)" if e.kind == "trader_buy" else ""
                print(f"  [fetch {key_eid}] {fid} x{x}y{y}{tag} -> {attr}={cur.state[attr]} "
                      f"HP={cur.state['hp']} G={cur.state['gold']} {cur.state['floor']}", flush=True)
                break
        if not got:
            # trader 买钥匙: compute_matrix(cur 不在 trader 楼层)起点=楼梯落点,
            # 到 trader 邻居路径有门/怪(dmg>0/doors>0),不匹配 zero 过滤。但 transition
            # 到 trader 楼层后(英雄=fly_points 落地点),trader 邻居常 0 消耗可达。故单独试:
            # transition + _flood_floor(trader 楼层,起点=英雄)查邻居可达 + talk_trader。
            for (tfid, tpos), spec in TRADER_KEY_MAP.items():
                _cost, yk_g, bk_g, rk_g, tkey_eid = spec
                if tkey_eid != key_eid:
                    continue
                c = cur.clone()
                try:
                    if c.state["floor"] != tfid:
                        if tfid not in c.visited:
                            continue
                        c.transition(tfid, f"nav fly->{tfid} (trader)")
                    if c.state["gold"] < _cost:
                        continue
                    cf_t = _flood_floor(c, tfid, break_fakewalls=True)
                    nx, ny = tpos
                    if not any(n in cf_t.reachable_cells for n in
                               ((nx + 1, ny), (nx - 1, ny), (nx, ny + 1), (nx, ny - 1))):
                        continue
                    c.talk_trader(tfid, nx, ny, f"buy {tkey_eid} from trader")
                except RouteError:
                    continue
                if c.state[attr] > cur.state[attr]:
                    cur.__dict__.update(c.__dict__)
                    got = True
                    print(f"  [fetch {key_eid} via trader] {tfid} {tpos} -> {attr}={cur.state[attr]} "
                          f"G={cur.state['gold']} HP={cur.state['hp']} {cur.state['floor']}", flush=True)
                    break
        if not got:
            # 0 消耗不够: 试 1 门锁区钥匙(access_dmg=0, doors=1,开门耗 YK)。
            # 如 MT4 blueKey(2,1) 需开 (2,4) yellowDoor;MT8 yellowKey 等。
            one_door = [e for e in rm.supplement_keys
                        if e.eid == key_eid and e.access_dmg == 0 and e.doors_on_path == 1
                        and cur.block_at(e.fid, e.pos) is not None]
            one_door.sort(key=lambda e: abs(_floor_n(e.fid) - _floor_n(cur.state["floor"])))
            for e in one_door:
                fid, x, y, eid = e.fid, e.pos[0], e.pos[1], e.eid
                c = cur.clone()
                try:
                    acquire_resource(c, fid, x, y, eid)
                except RouteError as exc:
                    print(f"  [fetch {key_eid}] {fid} x{x}y{y} FAIL(1door): {exc}", flush=True)
                    continue
                if c.state[attr] > cur.state[attr]:
                    cur.__dict__.update(c.__dict__)
                    got = True
                    print(f"  [fetch {key_eid} via 1door] {fid} x{x}y{y} -> {attr}={cur.state[attr]} "
                          f"HP={cur.state['hp']} {cur.state['floor']}", flush=True)
                    break
        if not got:
            # 0 消耗 + 1 门都不够: kill cheap monster(掉/附近 yellowKey auto 拾)补 YK。
            # walk 7F kill skeleton 得 YK+2;monster 不一定掉 YK,但 auto_sweep 拾附近
            # 零伤 yellowKey(kill 开路后可达)。筛 access_dmg 低(打怪少掉血)跨层 acquire。
            monsters = sorted(rm.monster_entries, key=lambda e: (e.access_dmg, e.path_len))
            print(f"  [fetch {key_eid} kill-fallback] {len(monsters)} monsters "
                  f"top={[(e.eid,e.fid,e.pos,e.access_dmg) for e in monsters[:30]]}", flush=True)
            for e in monsters[:30]:
                if e.access_dmg > 200:
                    break
                c = cur.clone()
                yk0 = c.state[attr]
                try:
                    acquire_resource(c, e.fid, e.pos[0], e.pos[1], e.eid)
                except RouteError as exc:
                    print(f"    kill {e.fid} x{e.pos[0]}y{e.pos[1]} {e.eid} FAIL: {exc}", flush=True)
                    continue
                if c.state[attr] > yk0:
                    cur.__dict__.update(c.__dict__)
                    got = True
                    print(f"  [fetch {key_eid} via kill] {e.fid} x{e.pos[0]}y{e.pos[1]} {e.eid} "
                          f"-> {attr}={cur.state[attr]} HP={cur.state['hp']} "
                          f"{cur.state['floor']}", flush=True)
                    break
                else:
                    print(f"    kill {e.fid} x{e.pos[0]}y{e.pos[1]} {e.eid} no gain "
                          f"({yk0}->{c.state[attr]})", flush=True)
        if not got:
            print(f"  [fetch {key_eid}] no 0-cost or kill source "
                  f"(have {cur.state[attr]}/{target})", flush=True)
            break
    return cur


def _fetch_potions_until(cur: Game, hp_target: int) -> Game:
    """直接 acquire 药水到 HP>=hp_target(不用 Dijkstra)。27 攻防后补(属性高打怪少掉血)。
    优先 bluePotion(+200)后 redPotion(+50)。用可达矩阵筛 0 消耗可达药水(匹配
    _fetch_keys_until):不试锁区/未访问楼层的。"""
    rounds = 0
    while cur.state["hp"] < hp_target:
        rounds += 1
        if rounds > 20:
            break
        got = False
        rm = compute_matrix(cur)
        # 0 消耗可达药水;优先 bluePotion(+200)后 redPotion(+50),就近楼层
        zero = [e for e in rm.supplement_potions
                if e.access_dmg == 0 and e.doors_on_path == 0
                and cur.block_at(e.fid, e.pos) is not None]
        zero.sort(key=lambda e: (0 if e.eid == "bluePotion" else 1,
                                 abs(_floor_n(e.fid) - _floor_n(cur.state["floor"]))))
        for e in zero:
            fid, x, y, eid = e.fid, e.pos[0], e.pos[1], e.eid
            c = cur.clone()
            try:
                acquire_resource(c, fid, x, y, eid)
            except RouteError as exc:
                print(f"  [fetch {eid}] {fid} x{x}y{y} FAIL: {exc}", flush=True)
                continue
            if c.state["hp"] > cur.state["hp"]:
                cur.__dict__.update(c.__dict__)
                got = True
                print(f"  [fetch {eid}] {fid} x{x}y{y} -> HP={cur.state['hp']} "
                      f"dmg={cur.state['dmg']} {cur.state['floor']}", flush=True)
                break
        if not got:
            print(f"  [fetch potion] no 0-cost potion reachable "
                  f"(HP={cur.state['hp']}/{hp_target})", flush=True)
            break
    return cur


def _acquire_gem(cur: Game, fid: str, x: int, y: int, eid: str) -> Game:
    """直接 acquire 单个 gem(不用 Dijkstra)。clone 试,成功写回。"""
    c = cur.clone()
    try:
        acquire_resource(c, fid, x, y, eid)
        cur.__dict__.update(c.__dict__)
        print(f"  [acquire {eid}] {fid} x{x}y{y} OK HP={cur.state['hp']} "
              f"ATK={cur.state['atk']} DEF={cur.state['def']} YK={cur.state['yk']} "
              f"dmg={cur.state['dmg']} {cur.state['floor']}", flush=True)
    except RouteError as e:
        print(f"  [acquire {eid}] FAIL: {e}", flush=True)
    return cur


def run_boss_subgoals(start_g: Game, max_exp: int, top_k: int) -> tuple[Game, bool]:
    """boss 段全 A* Pareto(从 start_g 起,goal=boss cleared)。
    动作空间 skeleton_actions: acquire gem/key/potion + buy trader(MT6/MT7) +
    kill monster + boss trigger。A* 自己发现最优调度(买trader vs 4黄门绕路 vs
    留(9,7)给redGem + 补YK/HP + redKey(yellowGuard) + boss),替代旧线性 sub-goal
    (YK>=4->27/27->RK->HP->boss)。后者 sub-goal 间不回溯,无法发现买 trader BK
    短路 + 留 (9,7) 给 redGem 的更优调度(HP=213 > walk 122)。Pareto (dmg,-atk,-def)
    保留非支配分支(刷宝石/买trader/补HP 不被 dmg-min 剪)。"""
    global _BOSS_PHASE
    _BOSS_PHASE = True  # 开启钥匙/药水/trader 跨层 acquire(boss 段资源规划)
    cur = start_g
    st = cur.state
    print(f"[boss start] HP={st['hp']} ATK={st['atk']} DEF={st['def']} "
          f"YK={st['yk']} BK={st['bk']} RK={st['rk']} G={st['gold']} "
          f"dmg={st['dmg']} {st['floor']}", flush=True)
    astar = GameAStar(
        actions=skeleton_actions,
        goal=goal,
        heuristic=heuristic,
        edge_cost=lambda b, a, _act: float(max(0, a.state["dmg"] - b.state["dmg"])),
        state_key=_state_key,
        weight=1.0,
        max_expansions=max_exp,
        top_k=top_k,
        pareto_metrics=_pareto_metrics(),
    )
    res = astar.search(cur)
    ns = res.game.state if res.game else cur.state
    print(f"[boss A*] found={res.found} cost={res.cost} exp={res.expansions} "
          f"HP={ns['hp']} ATK={ns['atk']} DEF={ns['def']} YK={ns['yk']} "
          f"BK={ns['bk']} RK={ns['rk']} G={ns['gold']} dmg={ns['dmg']} {ns['floor']}", flush=True)
    if not res.top_goals:
        print("!! boss A* 未达 boss cleared,停止", flush=True)
        return cur, False
    cur = res.top_goals[0][1]
    return cur, goal(cur)


def main() -> int:
    global _T0
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--diag", action="store_true")
    p.add_argument("--max-expansions", type=int, default=8000, help="每段最大扩展数")
    p.add_argument("--weight", type=float, default=3.0)
    p.add_argument("--top-k", type=int, default=5, help="每段收集 top-K goal 状态")
    p.add_argument("--out-json", type=Path, default=OUT_JSON)
    p.add_argument("--segments", default="sword1,shield1,gem,boss", help="里程碑序列")
    p.add_argument("--pareto", action="store_true",
                   help="Pareto 多目标(dmg,-atk,-def): state_key 去 atk/def,刷宝石分支不被剪")
    args = p.parse_args()

    global _PARETO
    _PARETO = args.pareto

    g = Game(read_json(SAVE1))
    g.strict_live_model = True
    g.auto_flags = {"battle": True, "item": True, "wall": True}
    _drop = [k for k in g.floors if not (k.startswith("MT") and 1 <= int(k[2:]) <= 10)]
    for k in _drop:
        del g.floors[k]
    print(f"start: {state_line(g.state)} {g.state['floor']} x{g.state['x']}y{g.state['y']} "
          f"dmg={g.state['dmg']} floors={len(g.floors)}", flush=True)

    if args.diag:
        cf = _flood_floor(g, g.state["floor"])
        print(f"[diag] {g.state['floor']} reached={len(cf.reachable_cells)} entries={len(cf.entries)}")
        for e in cf.entries:
            print(f"[diag]   kind={e.kind} pos={e.pos} eid={e.eid} "
                  f"access_dmg={getattr(e,'access_dmg','?')} path_len={getattr(e,'path_len','?')}")
        return 0

    _T0 = time.perf_counter()
    seg_names = [s["name"] for s in SEGMENTS]
    print(f"  segments: {' -> '.join(seg_names)} | weight={args.weight} "
          f"max_exp/seg={args.max_expansions} top_k={args.top_k}", flush=True)

    cur = g
    for seg in SEGMENTS:
        cur, ok = run_segment(seg, cur, args.max_expansions, args.top_k)
        if not ok:
            print(f"\n!! seg {seg['name']} 未达目标,停止", flush=True)
            return 1

    # 输出最终段(boss)的 walk
    el = time.perf_counter() - _T0
    print(f"\n=== 全部 {len(SEGMENTS)} 段完成 {el:.1f}s ===", flush=True)
    best = cur
    steps = best.steps if hasattr(best, "steps") else []
    print(f"final: {state_line(best.state)} {best.state['floor']} x{best.state['x']}y{best.state['y']} "
          f"steps={len(steps)}", flush=True)
    print(f"对照当前最优: HP=122 ATK=27 DEF=27 dmg=2454 final-score=1376.5", flush=True)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps({
        "ok": not best.errors,
        "variant": "zone1_mt10_boss_search_milestones",
        "source_checkpoint": "save1(MT4 start)",
        "segments": seg_names,
        "goal": "MT10 boss defeated",
        "final": best.snapshot(),
        "steps": steps,
        "errors": best.errors,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"walk.json={args.out_json}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
