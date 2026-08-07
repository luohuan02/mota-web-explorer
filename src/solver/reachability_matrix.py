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

    飞行：fly(fid) 免费传送到 visited 楼层（transition 上楼梯时加入 visited，
    除 MT49/50）。已访问楼层直接作为起点 flood，不再依赖楼梯边--用户规则：
    上楼楼梯只在未上楼时计入，上楼后可直接飞达已访问楼层。

    楼梯解锁新楼层：楼梯四邻可达且无法师致命陷阱（special 15/16）在必经邻位。
    若楼梯旁唯一可达邻位落在法师掉血陷阱且致死（check_damage_at >= hp），
    该楼梯不可用（无法站到楼梯旁解锁上一层）。

    门有钥匙预算就开（不扣，过估），怪按可杀性。宁可多生成（A* 边 go_to 精确
    拒绝假阳），不可漏估（漏估丢真解）。
    """
    reachable: set[tuple[str, int, int]] = set()
    done: set[str] = set()
    # 起点：当前层 + 所有飞行可达的已访问楼层。fly(fid) 免费传送到 visited
    # 楼层（transition 上楼梯时加入 visited，除 MT49/50）。用户规则：上楼楼梯
    # 只在未上楼时计入，上楼后可直接飞达已访问楼层，不再依赖楼梯边。
    stack = [g.state["floor"]]
    for fid in g.visited:
        if fid in g.floors and fid not in done and fid not in stack:
            stack.append(fid)
    hp = int(g.state.get("hp", 0))
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
            # 楼梯格本身 terrain 不可踩，四邻可达 = 能上/下楼。但若必经邻位
            # 落在法师掉血陷阱(special 15 魔法场 / special 16 半血)且致死，
            # 楼梯不可用（无法站到楼梯旁解锁上一层）。用户规则：法师陷阱在
            # 必经之路则不可飞/上楼。
            usable = False
            for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if n not in fr.reachable_cells:
                    continue
                if hp > 0:
                    try:
                        if g.check_damage_at(fid, n) >= hp:
                            continue  # 法师陷阱致死，该邻位不可站
                    except Exception:
                        pass
                usable = True
                break
            if usable:
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


# ---------------------------------------------------------------------------
# 属性增量 + 剩余资源估值 + zone-local comparison_score（2攻0防 zone 优化）
#
# 服务两个用途：
# (a) comparison_score 的剩余资源估值（zone1+zone2 剩余 entries 按 HP 等价估值）。
# (b) 骨架交换的等价分组/替换候选（small-opt，后续）。
#
# 口径对齐 scripts/search/post9_resource_group_search.py 的 VALUE 常量
# （YK=50/BK=200/RK=420/ATK_GEM=260/DEF_GEM=280，zone1 post9 调校）。ATK/DEF 宝石
# 估值是 zone1 基线，zone2+ 主观可调。gold 口袋值（带到 zone4）用 zone4 溢价，
# 不用面值（post9 不含 gold 因 zone1 全花商店了）。
# ---------------------------------------------------------------------------

YK_VALUE = 50
BK_VALUE = 200
RK_VALUE = 420
ATK_GEM_VALUE = 260   # 每 ATK 点 HP 等价（zone1 post9 基线，主观可调）
DEF_GEM_VALUE = 280   # 每 DEF 点 HP 等价
GOLD_FACE_VALUE = 0.5  # 每 gold 面值（100G=50HP），剩余怪金币用

_SWORD_ATK = {"sword1": 10, "sword2": 20, "sword3": 40, "sword4": 50, "sword5": 100}
_SHIELD_DEF = {"shield1": 10, "shield2": 20, "shield3": 40, "shield4": 50, "shield5": 100}
_KEY_EID_FIELD = {"yellowKey": "yk", "blueKey": "bk", "redKey": "rk"}


@dataclass(frozen=True)
class AttrDelta:
    """单个资源的属性增量。flags 是非 stat 效果（cross/magicImmune 等）。"""
    atk: int = 0
    defense: int = 0   # 'def' 是关键字
    hp: int = 0
    yk: int = 0
    bk: int = 0
    rk: int = 0
    gold: int = 0      # 正=掉落金币，负=购买花费
    flags: tuple = ()

    def stat_key(self) -> tuple:
        """等价分组键（stat 增量，不含 gold/flags）-- 宝石替换用。"""
        return (self.atk, self.defense, self.hp, self.yk, self.bk, self.rk)


def attribute_delta(entry: ReachableEntry, g: Game) -> list[AttrDelta]:
    """获取该 entry 的属性增量列表。商店返回多选项（atk/def 买型），其它单项。

    用途：comparison_score 剩余资源估值 + 骨架交换等价分组（small-opt）。
    未建模的资源（fly/工具计数器/未在 TRADER_KEY_MAP 的 zone2 商人）返回 []。
    """
    eid = entry.eid
    ratio = g.floors[entry.fid].ratio if entry.fid in g.floors else 1
    if eid == "redGem":
        return [AttrDelta(atk=ratio)]
    if eid == "blueGem":
        return [AttrDelta(defense=ratio)]
    if eid == "greenGem":
        return [AttrDelta(atk=ratio, defense=ratio)]
    if eid in _SWORD_ATK:
        return [AttrDelta(atk=_SWORD_ATK[eid])]
    if eid in _SHIELD_DEF:
        flags = ("magicImmune",) if eid == "shield5" else ()
        return [AttrDelta(defense=_SHIELD_DEF[eid], flags=flags)]
    if eid == "cross":
        return [AttrDelta(flags=("cross",))]
    if eid in _KEY_EID_FIELD:
        return [AttrDelta(**{_KEY_EID_FIELD[eid]: 1})]
    if eid == "redPotion":
        return [AttrDelta(hp=50 * ratio)]
    if eid == "bluePotion":
        return [AttrDelta(hp=200 * ratio)]
    if eid in SHOP_EIDS:
        # atk 买 = +2*ratio，def 买 = +4*ratio（hp 买依赖 times1，状态相关，暂略）
        return [AttrDelta(atk=2 * ratio), AttrDelta(defense=4 * ratio)]
    if entry.kind == "monster":
        money = int(g.enemies.get(eid, {}).get("money", 0))
        return [AttrDelta(gold=money)]
    if entry.kind == "trader_buy":
        spec = TRADER_KEY_MAP.get((entry.fid, entry.pos))
        if spec:
            cost, yk, bk, rk, _keid = spec
            return [AttrDelta(yk=yk, bk=bk, rk=rk, gold=-cost)]
        return []
    # fly / pickaxe / bomb / centerFly / ... : 无 stat 增量
    return []


def delta_value(d: AttrDelta) -> float:
    """单个增量的 HP 等价面值。口袋 gold 的 zone4 溢价在 comparison_score 单独算。"""
    return (
        d.atk * ATK_GEM_VALUE
        + d.defense * DEF_GEM_VALUE
        + d.hp
        + d.yk * YK_VALUE
        + d.bk * BK_VALUE
        + d.rk * RK_VALUE
        + d.gold * GOLD_FACE_VALUE
    )


def entry_value(entry: ReachableEntry, g: Game) -> float:
    """单个剩余 entry 的估值 = 其最佳增量选项的面值（商店取 max 选项）。"""
    deltas = attribute_delta(entry, g)
    if not deltas:
        return 0.0
    return max(delta_value(d) for d in deltas)


def remaining_resource_value(rm: ReachabilityMatrix, g: Game) -> dict[str, float]:
    """zone1+zone2 剩余（未获取）entries 的 HP 等价估值，按 kind 拆分。"""
    by_kind: dict[str, float] = {}
    for kind, entries in (
        ("skeleton", rm.skeleton_entries),
        ("shop", rm.shop_entries),
        ("monster", rm.monster_entries),
        ("supplement_key", rm.supplement_keys),
        ("supplement_potion", rm.supplement_potions),
    ):
        by_kind[kind] = sum(entry_value(e, g) for e in entries)
    by_kind["total"] = sum(by_kind.values())
    return by_kind


def comparison_score(
    g: Game,
    rm: ReachabilityMatrix,
    *,
    zone4_gold_premium: float = 2.5,   # 口袋 gold 相对面值的倍数（zone4 ratio5 vs zone2 ratio2）
    times1_penalty: int = 0,          # 每 times1 的惩罚（2攻0防下 times1=2 常量，默认 0）
) -> dict:
    """zone1+zone2 终态比较口径。

    score = HP + 钥匙值 + (1+2区剩余资源面值) + 口袋gold×zone4溢价 - times1×惩罚

    - HP/钥匙/剩余：zone-local（post9 口径）。
    - 口袋 gold：主观 zone4 溢价（后移到 zone4 买 ratio5 属性），非面值。
      zone4_gold_premium=2.5 = ratio5/ratio2；可调（敏感度见报告）。
    - times1：2攻0防下 = 2 常量；跨策略（vs 2ATK1DEF=3）才差异化，默认不罚。
    """
    s = g.state
    hp = int(s["hp"]); yk = int(s["yk"]); bk = int(s["bk"]); rk = int(s["rk"])
    gold = int(s["gold"]); times1 = int(s.get("times1", 0))
    keys_val = yk * YK_VALUE + bk * BK_VALUE + rk * RK_VALUE
    remain = remaining_resource_value(rm, g)
    remain_total = remain["total"]
    # 口袋 gold 按 zone4 溢价估值（非面值）：gold × 面值 × 溢价
    gold_val = gold * GOLD_FACE_VALUE * zone4_gold_premium
    total = hp + keys_val + remain_total + gold_val - times1 * times1_penalty
    return {
        "total": total,
        "hp": hp,
        "atk": int(s["atk"]), "def": int(s["def"]),
        "keys_value": keys_val,
        "yk": yk, "bk": bk, "rk": rk,
        "gold": gold,
        "gold_value": gold_val,
        "zone4_gold_premium": zone4_gold_premium,
        "remaining": remain,
        "times1": times1,
        "times1_penalty": times1_penalty,
    }


# --- 骨架交换等价分组/替换候选（small-opt，后续用）---

def equivalence_groups(rm: ReachabilityMatrix, g: Game) -> dict[tuple, list[ReachableEntry]]:
    """按 stat_key 分组可达 entries（同 delta 可互相替换）。商店按买型拆。"""
    groups: dict[tuple, list[ReachableEntry]] = {}
    for e in rm.skeleton_entries + rm.shop_entries + rm.supplement_keys + rm.supplement_potions:
        for d in attribute_delta(e, g):
            if d.stat_key() == (0, 0, 0, 0, 0, 0):
                continue  # 纯金币/无 stat 不进等价组
            groups.setdefault(d.stat_key(), []).append(e)
    return groups


def substitution_candidates(
    rm: ReachabilityMatrix, visited: ReachableEntry, g: Game
) -> list[ReachableEntry]:
    """给一个已访问节点，返回同 stat_key 的未拾取等价项，按获取成本升序。"""
    vds = attribute_delta(visited, g)
    if not vds:
        return []
    target_keys = {d.stat_key() for d in vds}
    out: list[ReachableEntry] = []
    for e in rm.skeleton_entries + rm.shop_entries + rm.supplement_keys + rm.supplement_potions:
        if (e.fid, e.pos) == (visited.fid, visited.pos):
            continue
        for d in attribute_delta(e, g):
            if d.stat_key() in target_keys and d.stat_key() != (0, 0, 0, 0, 0, 0):
                out.append(e)
                break
    out.sort(key=lambda e: (e.access_dmg, e.doors_on_path, e.path_len))
    return out
