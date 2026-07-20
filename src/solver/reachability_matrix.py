#!/usr/bin/env python3
"""跨层钥匙门感知资源组可达矩阵（upgrade zone2 component_cells）。

与 zone2 ``component_cells`` 的区别：
- 门**不**当通行：黄/蓝/红门消耗对应钥匙，存量不足则挡住（component_cells 把门当通行）。
- 怪按**可杀性**挡：``enemy_damage`` 无穷或打完致死则挡（component_cells 把怪当通行）。
- 楼层内**拾取钥匙后重试门**：多吃一轮钥匙可能开新门。
- 多路径按**到达成本集**分组。
- 跨层：经 fly/楼梯可达的楼层都参与。

A* 的**快速预筛**（邻居候选生成 + 补充成本估算），不 clone、不模拟战斗。
A* 边仍用 ``go_to_decomposed`` 精确执行。宽松估计宁可过估（A* 边精确拒绝假阳），
不可漏估（漏估丢真解）。

骨架节点（A* 邻居）= 宝石/商店购买/装备/飞行器/boss。
补充资源（非节点）= 全部钥匙 + 药瓶：在路径 auto + 缺口时压缩查询补。
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any

from src.solver.game_route import Game, Block, STAIRS, floor_no


SKELETON_ITEM_EIDS = {
    "redGem", "blueGem", "greenGem",
    "sword1", "sword2", "sword3", "sword4", "sword5",
    "shield1", "shield2", "shield3", "shield4", "shield5",
    "pickaxe", "bomb", "centerFly", "centerFly3", "cross",
    "superPotion", "earthquake", "coin", "magicImmune", "snow", "knife",
    "fly",
}
SHOP_EIDS = {"blueShop", "redShop", "yellowShop", "shop"}
SUPPLEMENT_KEY_EIDS = {"yellowKey", "blueKey", "redKey"}
SUPPLEMENT_POTION_EIDS = {"redPotion", "bluePotion"}

# 钥匙商人(trader): 花金币换钥匙,贴邻点击买(不可踩)。zone2 ZONE2_TRADERS + web 验证。
# (fid, (x,y)): (cost, yk_gain, bk_gain, rk_gain, key_eid) -- key_eid 匹配 _fetch_keys_until 过滤。
TRADER_KEY_MAP = {
    ("MT6", (8, 4)): (50, 0, 1, 0, "blueKey"),    # 6F 50G -> 1 BK
    ("MT7", (6, 1)): (50, 5, 0, 0, "yellowKey"),  # 7F 50G -> 5 YK
}


@dataclass(frozen=True)
class ReachableEntry:
    fid: str
    pos: tuple[int, int]
    eid: str
    kind: str            # "skeleton" | "shop" | "supplement_key" | "supplement_potion"
    access_dmg: int      # 路径上怪的估算伤害（不扣 HP，仅估）
    path_len: int        # 估算步数
    doors_on_path: int = 0   # 路径上门数（粗估成本）


@dataclass(frozen=True)
class Blocker:
    fid: str
    pos: tuple[int, int]
    eid: str
    kind: str            # "door" | "enemy"
    need: tuple[int, int, int] = (0, 0, 0)   # 门：缺 (yk,bk,rk)
    need_atk: int = 0    # 怪需更高 ATK（>0 表示当前打不动/致死）


@dataclass
class FloorReachability:
    fid: str
    reachable_cells: set[tuple[int, int]] = field(default_factory=set)
    entries: list[ReachableEntry] = field(default_factory=list)
    blockers: list[Blocker] = field(default_factory=list)
    collected_keys: tuple[int, int, int] = (0, 0, 0)  # 楼层内可拾钥匙增量


def _entry_starts(g: Game, fid: str) -> list[tuple[int, int]]:
    """楼层 flood 起点：当前楼层=英雄位置；其它已访问楼层=楼梯落地点四邻。

    当前楼层**只**用英雄位置，不加楼梯落点起点：后者是跨层 flood 的乐观假设
    （假设英雄能到楼梯落点），对当前楼层会过估楼梯可达性--_find_stair 会误报
    楼梯可达（reachable 含楼梯落点起点，但英雄实际被怪/门挡到不了），导致
    acquire_resource 反复 _tx_go_to 失败 + back-collect，慢且不收敛
    （zone1 MT9 upFloor 被 skeletonSoldier+blueDoor 挡，_find_stair 误报可达）。
    """
    starts: list[tuple[int, int]] = []
    if g.state["floor"] == fid:
        starts.append((g.state["x"], g.state["y"]))
    else:
        floor = g.floors[fid]
        for (x, y), block in floor.blocks.items():
            if block.eid in STAIRS:
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if 0 <= nx < floor.width and 0 <= ny < floor.height and not g.is_wall(fid, (nx, ny)):
                        starts.append((nx, ny))
    seen = set()
    out = []
    for s in starts:
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out


def _enter_cost(g: Game, fid: str, pos: tuple[int, int], block: Block | None,
                budget_yk: int, budget_bk: int, budget_rk: int,
                hp: int, break_fakewalls: bool = False):
    """返回 (enter, delta_dmg, blocker_or_None, opens_door)。

    门有预算钥匙就开（不扣，过估），怪按可杀性，terrain target-only。
    """
    if block is None:
        return True, 0, None, False
    if block.kind == "terrain":
        if block.eid in {"fakeWall", "fakeWall2"}:
            if break_fakewalls:
                # 可破墙当可通行：安全过估（fakeWall 可破，A* 边 go_to 精确执行/拒绝假阳）
                return True, 0, None, False
            return False, 0, None, False
        if block.eid in STAIRS:
            return False, 0, None, False
        if block.eid == "flower":
            return True, 0, None, False
        return False, 0, None, False
    if block.kind == "item":
        return True, 0, None, False
    if block.kind == "enemy":
        if (fid, pos[0], pos[1]) in g.retreat_wizards:
            return False, 0, Blocker(fid, pos, block.eid, "enemy", need_atk=1), False
        d = g.enemy_damage(block.eid)
        if d == float("inf") or hp - int(d) <= 0:
            return False, 0, Blocker(fid, pos, block.eid, "enemy", need_atk=1), False
        return True, int(d), None, False
    if block.kind == "door":
        if block.eid == "yellowDoor":
            if budget_yk <= 0:
                return False, 0, Blocker(fid, pos, block.eid, "door", need=(1, 0, 0)), False
            return True, 0, None, True
        if block.eid == "blueDoor":
            if budget_bk <= 0:
                return False, 0, Blocker(fid, pos, block.eid, "door", need=(0, 1, 0)), False
            return True, 0, None, True
        if block.eid == "redDoor":
            if budget_rk <= 0:
                return False, 0, Blocker(fid, pos, block.eid, "door", need=(0, 0, 1)), False
            return True, 0, None, True
    return False, 0, None, False


def _flood_floor(g: Game, fid: str, break_fakewalls: bool = False) -> FloorReachability:
    """对单层做 key-aware flood：拾钥匙后重试门，怪按可杀性，宽松过估。

    多轮：预算=携带钥匙 + 上一轮楼层内已拾钥匙。门有预算钥匙就开（**不扣**，
    过估，pre-filter 安全）。轮次直到 reached 不再增长。
    """
    floor = g.floors[fid]
    fr = FloorReachability(fid=fid)
    starts = _entry_starts(g, fid)
    if not starts:
        return fr

    yk0 = int(g.state["yk"]); bk0 = int(g.state["bk"]); rk0 = int(g.state["rk"])
    hp = int(g.state["hp"])

    reached: set[tuple[int, int]] = set()
    access_dmg: dict[tuple[int, int], int] = {}
    access_len: dict[tuple[int, int], int] = {}
    door_count: dict[tuple[int, int], int] = {}
    blocked_doors: dict[tuple[int, int], Blocker] = {}
    blocked_enemies: dict[tuple[int, int], Blocker] = {}

    budget_yk, budget_bk, budget_rk = yk0, bk0, rk0
    for _ in range(40):
        before_size = len(reached)
        queue: deque[tuple[int, int, int, int]] = deque()
        for s in starts:
            if s not in reached and not g.is_wall(fid, s):
                reached.add(s)
                access_dmg[s] = 0; access_len[s] = 0; door_count[s] = 0
                queue.append((s[0], s[1], 0, 0))
        while queue:
            cx, cy, dmg, length = queue.popleft()
            for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                pos = (nx, ny)
                if pos in reached or g.is_wall(fid, pos):
                    continue
                block = g.block_at(fid, pos)
                enter, ndmg, blocker, opens_door = _enter_cost(
                    g, fid, pos, block, budget_yk, budget_bk, budget_rk, hp, break_fakewalls
                )
                if blocker is not None:
                    if blocker.kind == "door":
                        blocked_doors.setdefault(pos, blocker)
                    else:
                        blocked_enemies.setdefault(pos, blocker)
                    continue
                if not enter:
                    continue
                reached.add(pos)
                access_dmg[pos] = dmg + ndmg
                access_len[pos] = length + 1
                door_count[pos] = door_count.get((cx, cy), 0) + (1 if opens_door else 0)
                queue.append((nx, ny, dmg + ndmg, length + 1))
        ky = kb = kr = 0
        for pos in reached:
            b = g.block_at(fid, pos)
            if not b:
                continue
            if b.eid == "yellowKey": ky += 1
            elif b.eid == "blueKey": kb += 1
            elif b.eid == "redKey": kr += 1
        new_yk, new_bk, new_rk = yk0 + ky, bk0 + kb, rk0 + kr
        converged = (len(reached) == before_size and (new_yk, new_bk, new_rk) == (budget_yk, budget_bk, budget_rk))
        budget_yk, budget_bk, budget_rk = new_yk, new_bk, new_rk
        if converged:
            break

    fr.reachable_cells = reached
    fr.collected_keys = (budget_yk - yk0, budget_bk - bk0, budget_rk - rk0)

    for pos in sorted(reached):
        b = g.block_at(fid, pos)
        if not b or (fid, pos[0], pos[1]) in g.blocked_items:
            continue
        if (fid, pos[0], pos[1]) in g.retreat_wizards:
            continue
        kind = _classify_entry(b.eid)
        if kind is None:
            # 可杀+正金币怪当 click 目标（monster 入口）
            if b.kind == "enemy":
                d = g.enemy_damage(b.eid)
                money = int(g.enemies.get(b.eid, {}).get("money", 0))
                if d != float("inf") and money > 0:
                    kind = "monster"
                else:
                    continue
            else:
                continue
        fr.entries.append(ReachableEntry(
            fid=fid, pos=pos, eid=b.eid, kind=kind,
            access_dmg=access_dmg.get(pos, 0),
            path_len=access_len.get(pos, 0),
            doors_on_path=door_count.get(pos, 0),
        ))
    # npc 商店（blueShop 等）不可踩（真实游戏贴邻点击）：若四邻在 reached 内则登记为 shop 入口
    for pos, block in floor.blocks.items():
        if block.kind != "npc" or block.eid not in SHOP_EIDS:
            continue
        if (fid, pos[0], pos[1]) in g.blocked_items:
            continue
        best_n = None
        for nx, ny in ((pos[0]+1, pos[1]), (pos[0]-1, pos[1]), (pos[0], pos[1]+1), (pos[0], pos[1]-1)):
            n = (nx, ny)
            if n in reached:
                cand = (access_dmg.get(n, 0), access_len.get(n, 0), door_count.get(n, 0))
                if best_n is None or cand < best_n[0]:
                    best_n = (cand, n)
        if best_n is None:
            continue
        (dmg, steps, doors), _n = best_n
        fr.entries.append(ReachableEntry(
            fid=fid, pos=pos, eid=block.eid, kind="shop",
            access_dmg=dmg, path_len=steps + 1, doors_on_path=doors,
        ))
    # 钥匙商人(trader): 不可踩,贴邻点击买钥匙。四邻在 reached 内则登记为 trader_buy 源。
    # 买过(trader_flag)跳过。未建模 trader(MT15/12/28/31/45/47)不登记(非 zone1 钥匙源)。
    for pos, block in floor.blocks.items():
        if block.kind != "npc" or block.eid != "trader":
            continue
        spec = TRADER_KEY_MAP.get((fid, pos))
        if spec is None:
            continue
        if g.flags.get(Game.trader_flag(fid, pos[0], pos[1])):
            continue
        if (fid, pos[0], pos[1]) in g.blocked_items:
            continue
        best_n = None
        for nx, ny in ((pos[0]+1, pos[1]), (pos[0]-1, pos[1]), (pos[0], pos[1]+1), (pos[0], pos[1]-1)):
            n = (nx, ny)
            if n in reached:
                cand = (access_dmg.get(n, 0), access_len.get(n, 0), door_count.get(n, 0))
                if best_n is None or cand < best_n[0]:
                    best_n = (cand, n)
        if best_n is None:
            continue
        (dmg, steps, doors), _n = best_n
        _cost, _yk, _bk, _rk, key_eid = spec
        fr.entries.append(ReachableEntry(
            fid=fid, pos=pos, eid=key_eid, kind="trader_buy",
            access_dmg=dmg, path_len=steps + 1, doors_on_path=doors,
        ))
    fr.blockers = list(blocked_doors.values()) + list(blocked_enemies.values())
    return fr


def cross_floor_reachable(g: Game, *, break_fakewalls: bool = True) -> set[tuple[str, int, int]]:
    """从当前英雄出发跨层 flood，返回所有可达 (fid, x, y)。

    预筛骨架/钥匙资源可达性：skeleton_actions 只对可达资源生成 acquire，
    _search_resource 只试可达钥匙组，避免远楼层 acquire 的贵跨层 go_to 浪费。

    跨层：当前楼层从英雄位置起 flood；可达楼梯（四邻在 reachable）延伸到目标
    楼层，目标楼层再 flood（_entry_starts 把楼梯落点当起点，乐观过估）。
    门有钥匙预算就开（不扣，过估），怪按可杀性。宁可多生成（A* 边 go_to 精确
    拒绝假阳），不可漏估（漏估丢真解）。
    """
    reachable: set[tuple[str, int, int]] = set()
    done: set[str] = set()
    stack = [g.state["floor"]]
    while stack:
        fid = stack.pop()
        if fid in done:
            continue
        done.add(fid)
        fr = _flood_floor(g, fid, break_fakewalls=break_fakewalls)
        for pos in fr.reachable_cells:
            reachable.add((fid, pos[0], pos[1]))
        floor = g.floors[fid]
        for (x, y), block in floor.blocks.items():
            if block.eid not in STAIRS:
                continue
            # 楼梯格本身 terrain 不可踩，四邻可达 = 能上/下楼
            if any(n in fr.reachable_cells for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))):
                tgt_n = floor_no(fid) + (1 if block.eid == "upFloor" else -1)
                tgt = f"MT{tgt_n}"
                if tgt in g.floors and tgt not in done:
                    stack.append(tgt)
    return reachable


def _classify_entry(eid: str) -> str | None:
    if eid in SHOP_EIDS:
        return "shop"
    if eid in SKELETON_ITEM_EIDS:
        return "skeleton"
    if eid in SUPPLEMENT_KEY_EIDS:
        return "supplement_key"
    if eid in SUPPLEMENT_POTION_EIDS:
        return "supplement_potion"
    return None


@dataclass
class ReachabilityMatrix:
    floors: dict[str, FloorReachability] = field(default_factory=dict)
    skeleton_entries: list[ReachableEntry] = field(default_factory=list)
    shop_entries: list[ReachableEntry] = field(default_factory=list)
    monster_entries: list[ReachableEntry] = field(default_factory=list)
    supplement_keys: list[ReachableEntry] = field(default_factory=list)
    supplement_potions: list[ReachableEntry] = field(default_factory=list)
    blockers: list[Blocker] = field(default_factory=list)

    def summary(self) -> str:
        return (
            f"floors={len(self.floors)} skeleton={len(self.skeleton_entries)} "
            f"shop={len(self.shop_entries)} monster={len(self.monster_entries)} "
            f"keys={len(self.supplement_keys)} potions={len(self.supplement_potions)} blockers={len(self.blockers)}"
        )


def compute_matrix(g: Game, *, min_floor: int = 1, only_visited: bool = True) -> ReachabilityMatrix:
    """计算当前 Game 状态下的可达矩阵。only_visited 与 _visited_floor_ids 一致。"""
    rm = ReachabilityMatrix()
    floor_ids = set(g.visited) if only_visited else set(g.floors)
    floor_ids.add(g.state["floor"])
    for fid in sorted(floor_ids, key=lambda f: floor_no(f) if f.startswith("MT") and f[2:].isdigit() else 0):
        if fid not in g.floors or floor_no(fid) < min_floor:
            continue
        fr = _flood_floor(g, fid)
        rm.floors[fid] = fr
        for e in fr.entries:
            if e.kind == "skeleton":
                rm.skeleton_entries.append(e)
            elif e.kind == "shop":
                rm.shop_entries.append(e)
            elif e.kind == "monster":
                rm.monster_entries.append(e)
            elif e.kind in ("supplement_key", "trader_buy"):
                rm.supplement_keys.append(e)
            elif e.kind == "supplement_potion":
                rm.supplement_potions.append(e)
        rm.blockers.extend(fr.blockers)
    return rm


def group_by_access(entries: list[ReachableEntry]) -> list[list[ReachableEntry]]:
    """多路径分组：相同 (fid, eid, access_dmg, doors_on_path) 归并。"""
    groups: dict[tuple, list[ReachableEntry]] = {}
    for e in entries:
        key = (e.fid, e.eid, e.access_dmg, e.doors_on_path)
        groups.setdefault(key, []).append(e)
    return list(groups.values())


def supplement_lookup(rm: ReachabilityMatrix, kinds: set[str]) -> list[ReachableEntry]:
    """压缩可达查询：给补充子搜索用。按 (access_dmg, path_len) 升序。"""
    out: list[ReachableEntry] = []
    if "key" in kinds:
        out.extend(rm.supplement_keys)
    if "potion" in kinds:
        out.extend(rm.supplement_potions)
    out.sort(key=lambda e: (e.access_dmg, e.path_len, e.fid))
    return out
