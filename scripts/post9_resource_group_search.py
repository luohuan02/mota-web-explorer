#!/usr/bin/env python3
"""Post-9F action search with resource-group ranking.

The legacy post9_action_search.py is intentionally left untouched.  This
experiment reuses its real map mechanics and floor searches, but ranks sources,
beam entries, and final goals with a dynamic resource-group score.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from typing import Any


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.chdir(ROOT)

from src.solver import gen_walkthrough as gw
from src.solver.full_search import calc_dmg
from scripts import post9_action_search as base


OUT_JSON = os.path.join("outputs", "results", "post9_resource_group_search.json")
OUT_MD = os.path.join("outputs", "reports", "post9_resource_group_search.md")
OUT_WALK = os.path.join("outputs", "walkthroughs", "walkthrough_post9_resource_group_best.md")

YK_VALUE = 50
BK_VALUE = 200
ATK_GEM_VALUE = 260
DEF_GEM_VALUE = 280
RED_KEY_VALUE = 420
REDKEY_HP_BUDGET = 420


@dataclass(frozen=True)
class ResourceGroup:
    name: str
    fid: str
    items: tuple[tuple[int, int], ...] = ()
    doors: tuple[tuple[int, int], ...] = ()
    monsters: tuple[tuple[int, int], ...] = ()


def item_pos(fid: str, eid: str) -> tuple[tuple[int, int], ...]:
    return tuple((x, y) for x, y, _t, item in gw.maps[fid]["bl"] if item == eid)


def pos_eid(fid: str, pos: tuple[int, int]) -> str | None:
    for x, y, _t, eid in gw.maps[fid]["bl"]:
        if (x, y) == pos:
            return eid
    return None


# These are intentionally small and auditable.  Groups with shared access cost
# are merged so an individually negative connector can still be valued together
# with its downstream resources.
RESOURCE_GROUPS: tuple[ResourceGroup, ...] = (
    # 1F
    ResourceGroup("1F x10y11 蓝血瓶", "MT1", items=((10, 11),), doors=((10, 9),), monsters=((10, 10),)),
    ResourceGroup(
        "1F 红蓝宝石+右侧钥匙/血瓶",
        "MT1",
        items=tuple(sorted(set(item_pos("MT1", "redGem") + item_pos("MT1", "blueGem") + ((8, 3), (8, 4))))),
        doors=((6, 6), (9, 5)),
        monsters=((7, 6), (8, 6), (9, 6)),
    ),
    ResourceGroup("1F x1y3 红血瓶", "MT1", items=((1, 3),), doors=((4, 3),)),
    ResourceGroup(
        "1F 左下钥匙/血瓶链",
        "MT1",
        items=((1, 6), (1, 10), (1, 11), (3, 10), (3, 11), (5, 10)),
        doors=((2, 5), (2, 8)),
        monsters=((1, 7), (1, 9)),
    ),
    # 3F
    ResourceGroup("3F x11y1 红血瓶", "MT3", items=((11, 1),), doors=((9, 2),)),
    ResourceGroup("3F x11y8 资源", "MT3", items=((11, 7), (11, 8)), doors=((9, 8),), monsters=((10, 8),)),
    ResourceGroup(
        "3F x2y1 蓝宝石资源组",
        "MT3",
        items=((1, 1), (2, 1), (2, 2)),
        doors=((1, 4),),
        monsters=((3, 5), (1, 3)),
    ),
    ResourceGroup(
        "3F x2y9 红宝石资源组",
        "MT3",
        items=((2, 8), (2, 9), (1, 9)),
        doors=((1, 6),),
        monsters=((3, 5), (1, 7), (1, 8)),
    ),
    ResourceGroup("3F 中央蓝钥匙资源", "MT3", items=((4, 1), (4, 2), (4, 3), (5, 1), (5, 2), (5, 3), (6, 1), (6, 2), (6, 3))),
    # 4F/5F/6F
    ResourceGroup("4F 左上蓝钥匙", "MT4", items=((1, 2), (2, 1), (3, 2)), doors=((2, 4),), monsters=((2, 5),)),
    ResourceGroup("4F 右上资源", "MT4", items=((9, 2), (11, 2)), doors=((4, 5), (10, 4)), monsters=((10, 3),)),
    ResourceGroup("5F x1y9 蓝宝石", "MT5", items=((1, 9), (2, 9), (3, 9)), monsters=((2, 7),)),
    ResourceGroup("6F x9y1 黄钥匙", "MT6", items=((9, 1),), monsters=((7, 1),)),
    ResourceGroup("6F x4y9 蓝宝石", "MT6", items=((4, 9), (8, 11), (9, 11)), doors=((1, 10),), monsters=((5, 11), (2, 11), (2, 9))),
    ResourceGroup("6F x8y3 redPotion", "MT6", items=((8, 3),), doors=((11, 2),), monsters=((10, 1), (11, 4))),
    # 7F/8F/9F/10F
    ResourceGroup("7F 左侧两黄钥匙", "MT7", items=((5, 10), (5, 11)), doors=((5, 7),), monsters=((5, 9),)),
    ResourceGroup("7F 右侧黄钥匙/蓝血瓶", "MT7", items=((9, 1), (9, 2), (9, 9), (9, 10), (9, 11)), monsters=((9, 3), (9, 5), (9, 7))),
    ResourceGroup("7F x7y11 蓝血瓶", "MT7", items=((7, 11),), doors=((7, 7),), monsters=((7, 9), (7, 10))),
    ResourceGroup("8F 红钥匙区", "MT8", items=((9, 1), (9, 3), (10, 2), (11, 1), (11, 3)), doors=((10, 7),), monsters=((8, 8), (9, 5), (11, 5))),
    ResourceGroup("8F x1y5 红血瓶", "MT8", items=((1, 5),), doors=((1, 3),)),
    ResourceGroup("8F 左下黄钥匙", "MT8", items=((4, 11), (5, 10), (7, 10), (7, 11)), doors=((3, 11), (5, 7), (9, 11))),
    ResourceGroup("9F x2y2 黄钥匙", "MT9", items=((2, 2),), monsters=((1, 3),)),
    ResourceGroup("9F x9y9 黄钥匙+右下血瓶", "MT9", items=((9, 9), (11, 11)), doors=((11, 8),), monsters=((11, 9),)),
    ResourceGroup("10F x2y6 蓝宝石", "MT10", items=((2, 6),), doors=((1, 9),), monsters=((1, 6),)),
    ResourceGroup("10F x10y6 红宝石", "MT10", items=((10, 6),), doors=((9, 9), (11, 9)), monsters=((9, 6),)),
    ResourceGroup("10F x11y11 蓝血瓶", "MT10", items=((11, 11),), doors=((11, 9),)),
)


def collected_for(ent: dict[str, Any], fid: str) -> set[tuple[int, int]]:
    got = set(ent.get("collected", {}).get(fid, frozenset()))
    got.update(gw.FLOOR_13_COLLECTED.get(fid, frozenset()))
    return got


def item_value(eid: str | None, ent: dict[str, Any]) -> int:
    if eid == "yellowKey":
        return YK_VALUE
    if eid == "blueKey":
        return BK_VALUE
    if eid == "redPotion":
        return 50
    if eid == "bluePotion":
        return 200
    if eid == "redKey":
        return RED_KEY_VALUE if ent["rk"] < 1 else 0
    if eid == "redGem":
        return ATK_GEM_VALUE if ent["atk"] < 27 else 0
    if eid == "blueGem":
        return DEF_GEM_VALUE if ent["def"] < 27 else 0
    return 0


def door_cost(eid: str | None) -> int:
    if eid == "yellowDoor":
        return YK_VALUE
    if eid == "blueDoor":
        return BK_VALUE
    return 0


def group_value(
    group: ResourceGroup,
    ent: dict[str, Any],
    ignore_monster_damage: bool = False,
) -> tuple[int, str | None]:
    used = collected_for(ent, group.fid)
    reward = 0
    door = 0
    damage = 0
    left_items = []
    for pos in group.items:
        if pos in used:
            continue
        eid = pos_eid(group.fid, pos)
        val = item_value(eid, ent)
        reward += val
        if val:
            left_items.append(f"{pos}:{eid}")
    if reward <= 0:
        return 0, None
    for pos in group.doors:
        if pos not in used:
            door += door_cost(pos_eid(group.fid, pos))
    if not ignore_monster_damage:
        for pos in group.monsters:
            if pos not in used:
                eid = pos_eid(group.fid, pos)
                if eid:
                    damage += calc_dmg(eid, ent["atk"], ent["def"])
    value = reward - door - damage
    if value <= 0:
        return 0, None
    note = f"{group.name}: +{value} ({' '.join(left_items)})"
    return value, note


def residual_resource_breakdown(
    ent: dict[str, Any],
    ignore_monster_damage: bool = False,
    include_zero: bool = False,
) -> list[dict[str, Any]]:
    """Return auditable positive residual resource groups.

    When ignore_monster_damage is true this is meant for final-state comparison:
    remaining monsters are treated as zero-cost, while unopened doors still
    consume key value.
    """
    rows = []
    for group in RESOURCE_GROUPS:
        used = collected_for(ent, group.fid)
        items = []
        reward = 0
        for pos in group.items:
            if pos in used:
                continue
            eid = pos_eid(group.fid, pos)
            val = item_value(eid, ent)
            if val <= 0:
                continue
            reward += val
            items.append({"pos": f"x{pos[0]}y{pos[1]}", "eid": eid, "value": val})
        if reward <= 0:
            continue

        doors = []
        door = 0
        for pos in group.doors:
            if pos in used:
                continue
            eid = pos_eid(group.fid, pos)
            cost = door_cost(eid)
            if cost <= 0:
                continue
            door += cost
            doors.append({"pos": f"x{pos[0]}y{pos[1]}", "eid": eid, "cost": cost})

        monsters = []
        damage = 0
        for pos in group.monsters:
            if pos in used:
                continue
            eid = pos_eid(group.fid, pos)
            if not eid:
                continue
            cost = 0 if ignore_monster_damage else calc_dmg(eid, ent["atk"], ent["def"])
            damage += cost
            monsters.append({"pos": f"x{pos[0]}y{pos[1]}", "eid": eid, "damage": cost})

        value = reward - door - damage
        if value < 0 or (value == 0 and not include_zero):
            continue
        rows.append({
            "fid": group.fid,
            "floor": int(group.fid[2:]),
            "group": group.name,
            "items": items,
            "reward": reward,
            "doors": doors,
            "door_cost": door,
            "monsters": monsters,
            "monster_damage": damage,
            "value": value,
        })
    return rows


def residual_resource_value(
    ent: dict[str, Any],
    ignore_monster_damage: bool = False,
) -> tuple[int, list[str]]:
    total = 0
    notes = []
    for group in RESOURCE_GROUPS:
        value, note = group_value(group, ent, ignore_monster_damage=ignore_monster_damage)
        if value > 0:
            total += value
            if note:
                notes.append(note)
    return total, notes


def final_residual_resource_value(ent: dict[str, Any]) -> int:
    residual, _notes = residual_resource_value(ent, ignore_monster_damage=True)
    return residual


def final_resource_stock(ent: dict[str, Any]) -> int:
    return (
        ent["hp"]
        + ent["yk"] * YK_VALUE
        + ent["bk"] * BK_VALUE
        + final_residual_resource_value(ent)
    )


def resource_group_score(ent: dict[str, Any]) -> int:
    residual, _notes = residual_resource_value(ent)
    stat_penalty = max(0, 27 - ent["atk"]) * ATK_GEM_VALUE + max(0, 27 - ent["def"]) * DEF_GEM_VALUE
    rk_penalty = 300 if ent["rk"] < 1 else 0
    hp_need = 634 if ent["rk"] >= 1 and ent["atk"] >= 27 and ent["def"] >= 27 else 0
    hp_penalty = max(0, hp_need - ent["hp"])
    return (
        ent.get("_dmg", 0)
        - ent["hp"]
        - ent["yk"] * YK_VALUE
        - ent["bk"] * BK_VALUE
        + stat_penalty
        + rk_penalty
        + hp_penalty
        - residual
    )


def old_score(ent: dict[str, Any]) -> int:
    return (
        ent.get("_dmg", 0)
        + ent.get("_yd", 0) * YK_VALUE
        + ent.get("_bd", 0) * BK_VALUE
        - ent["hp"]
        - ent["yk"] * YK_VALUE
        - ent["bk"] * BK_VALUE
    )


def score_key(ent: dict[str, Any]) -> tuple[int, int, int, int, int]:
    return (
        resource_group_score(ent),
        old_score(ent),
        ent.get("_dmg", 0),
        ent.get("_yd", 0),
        -ent["hp"],
    )


def key_pocket_substitute_rank(ent: dict[str, Any]) -> tuple[int, int, int, int, int]:
    """Representative rank for routes that use a clean key source.

    This is intentionally about the resource-pocket signature, not a final
    objective.  It preserves candidates that took the cheaper 6F key pocket and
    did not consume the expensive 9F x2y2 key while entering MT10.
    """
    mt6_key = (9, 1) in collected_for(ent, "MT6")
    mt9_key = (2, 2) in collected_for(ent, "MT9")
    if mt6_key and not mt9_key:
        bucket = 0
    elif not mt9_key:
        bucket = 1
    else:
        bucket = 2
    return (
        bucket,
        -ent["yk"],
        -ent["bk"],
        resource_group_score(ent),
        ent.get("_dmg", 0),
        ent.get("_yd", 0),
        -ent["hp"],
    )


def stat_balance_rank(ent: dict[str, Any]) -> tuple[int, int, int, int, int, int, int]:
    """Prefer stat paths that raise DEF before equivalent ATK-only gains.

    Many post-shield actions are commutable.  If one order gives DEF before
    taking the next guarded gem, it can shave a few points of damage while
    ending at the same ATK/DEF.  This rank preserves those representatives
    during the stat27 stage.
    """
    return (
        max(0, 27 - ent["def"]),
        max(0, 27 - ent["atk"]),
        resource_group_score(ent),
        ent.get("_dmg", 0),
        ent.get("_yd", 0),
        ent.get("_bd", 0),
        -ent["hp"],
    )


def jit_def_before_supply_rank(ent: dict[str, Any]) -> tuple[int, int, int, int, int, int, int, int, int]:
    """Representative rank for delaying non-critical supply until after stats.

    This is a scheduling hint, not a dominance rule: real floor replay still
    decides legality and cost.  It keeps routes like "take reachable DEF gems,
    then fight a key-pocket monster" from being crowded out by earlier but more
    expensive key pickups.
    """
    return (
        max(0, 27 - ent["def"]),
        max(0, 27 - ent["atk"]),
        -ent["def"],
        -ent["atk"],
        ent.get("_dmg", 0),
        ent.get("_yd", 0),
        ent.get("_bd", 0),
        -ent["yk"],
        -ent["hp"],
    )


def redkey_survival_deficit(ent: dict[str, Any]) -> int:
    if ent["atk"] < 27 or ent["def"] < 27 or ent["rk"] >= 1:
        return 10**9
    return max(0, REDKEY_HP_BUDGET - ent["hp"])


ORIGINAL_SELECT_SOURCES = base.select_sources
ORIGINAL_TRIM_ENTRIES = base.trim_entries
ORIGINAL_BEST_GOALS = base.best_goals
ORIGINAL_ENSURE_MT10 = base.ensure_mt10
ORIGINAL_APPLY_ACTION = base.apply_action

STAT_ACTIONS = []
for _spec in base.STAT_ACTIONS:
    if _spec == ("MT7", "yellowKey") and ("MT6", "yellowKey") not in STAT_ACTIONS:
        STAT_ACTIONS.append(("MT6", "yellowKey"))
    if _spec == ("MT8", "blueGem"):
        STAT_ACTIONS.append(("MT7_SKEL_KEY", "yellowKey"))
    STAT_ACTIONS.append(_spec)
    if _spec == ("MT5", "blueGem"):
        STAT_ACTIONS.append(("MT5_DIRECT", "blueGem"))
    if _spec == ("MT4", "blueKey"):
        STAT_ACTIONS.append(("MT4_DIRECT", "blueKey"))
    if _spec == ("MT10", "blueGem"):
        STAT_ACTIONS.append(("MT9_BLUE_UP", "upFloor"))
        STAT_ACTIONS.append(("MT10_DIRECT", "blueGem"))
    if _spec == ("MT7", "yellowKey"):
        STAT_ACTIONS.append(("MT7_RIGHT_KEY", "yellowKey"))


SPECIAL_ACTION_REAL_FID = {
    "MT7_SKEL_KEY": "MT7",
    "MT7_RIGHT_KEY": "MT7",
    "MT5_DIRECT": "MT5",
    "MT4_DIRECT": "MT4",
    "MT9_BLUE_UP": "MT9",
    "MT10_DIRECT": "MT10",
}


def special_real_fid(fid: str) -> str:
    return SPECIAL_ACTION_REAL_FID.get(fid, fid)


def special_action_allowed(ent: dict[str, Any], fid: str, target: str) -> bool:
    if fid == "MT7_SKEL_KEY":
        got = collected_for(ent, "MT7")
        return (
            (3, 1) in got
            and (9, 1) not in got
            and (9, 2) not in got
            and base.target_available(ent, "MT7", "yellowKey")
        )
    if fid == "MT7_RIGHT_KEY":
        got = collected_for(ent, "MT7")
        return (
            (9, 10) not in got
            and (9, 11) not in got
            and ent["atk"] >= 25
            and ent["def"] >= 26
            and base.target_available(ent, "MT7", "yellowKey")
        )
    if fid == "MT5_DIRECT":
        return (
            target == "blueGem"
            and ent["atk"] >= 25
            and ent["def"] >= 25
            and base.target_available(ent, "MT5", target)
        )
    if fid == "MT4_DIRECT":
        return (
            target == "blueKey"
            and ent["bk"] < 1
            and ent["atk"] >= 25
            and ent["def"] >= 25
            and base.target_available(ent, "MT4", target)
        )
    if fid == "MT9_BLUE_UP":
        return (
            ent["bk"] >= 1
            and ent["atk"] >= 25
            and ent["def"] >= 26
            and "MT10" not in ent.get("collected", {})
        )
    if fid == "MT10_DIRECT":
        got9 = collected_for(ent, "MT9")
        return (
            target == "blueGem"
            and (1, 11) in got9
            and ent["yk"] >= 1
            and base.target_available(ent, "MT10", target)
        )
    return base.action_allowed(ent, fid, target) and base.target_available(ent, fid, target)


def select_sources(entries, fid, target, limit):
    real_fid = special_real_fid(fid)
    if fid in SPECIAL_ACTION_REAL_FID:
        src = [e for e in entries if special_action_allowed(e, fid, target)]
    else:
        src = [
            e for e in entries
            if base.action_allowed(e, fid, target) and base.target_available(e, fid, target)
        ]
    if not src:
        return []
    selected = []
    seen = set()

    def add(items):
        for e in items:
            if e["_id"] in seen:
                continue
            seen.add(e["_id"])
            selected.append(e)
            if len(selected) >= limit:
                return

    selectors = [
        lambda e: (resource_group_score(e), base.action_score_key(e, real_fid, target)),
        lambda e: (key_pocket_substitute_rank(e), base.action_score_key(e, real_fid, target)),
        lambda e: (stat_balance_rank(e), base.action_score_key(e, real_fid, target)),
        lambda e: (jit_def_before_supply_rank(e), base.action_score_key(e, real_fid, target)),
        lambda e: (base.phase_survival_deficit(e), resource_group_score(e), -e["hp"]),
        lambda e: (redkey_survival_deficit(e), resource_group_score(e), -e["yk"], -e["hp"]),
        lambda e: (base.boss_survival_deficit(e), resource_group_score(e), -e["yk"], -e["hp"]),
        lambda e: (-residual_resource_value(e)[0], resource_group_score(e), e.get("_dmg", 0)),
    ]
    per_selector = max(2, limit // (len(selectors) + 1))
    for selector in selectors:
        add(sorted(src, key=selector)[:per_selector])
        if len(selected) >= limit:
            return selected[:limit]
    if fid not in SPECIAL_ACTION_REAL_FID:
        add(ORIGINAL_SELECT_SOURCES(entries, fid, target, limit))
    return selected[:limit]


def add_unique(chosen, seen, items, quota):
    added = 0
    for e in items:
        if e["_id"] in seen:
            continue
        seen.add(e["_id"])
        chosen.append(e)
        added += 1
        if added >= quota:
            break


def trim_entries(entries, limit):
    filtered = base.filter_entries(entries)
    if len(filtered) <= limit:
        return filtered
    chosen = []
    seen = set()

    goals = [e for e in filtered if base.goal(e)]
    add_unique(chosen, seen, sorted(goals, key=score_key), limit)
    if len(chosen) >= limit:
        return chosen[:limit]

    phases = [
        [e for e in filtered if e["atk"] < 27 or e["def"] < 27],
        [e for e in filtered if e["atk"] >= 27 and e["def"] >= 27 and e["rk"] < 1],
        [e for e in filtered if e["atk"] >= 27 and e["def"] >= 27 and e["rk"] >= 1],
    ]
    for phase in phases:
        if not phase:
            continue
        add_unique(chosen, seen, sorted(phase, key=score_key), max(20, limit // 5))
        add_unique(chosen, seen, sorted(phase, key=key_pocket_substitute_rank), max(16, limit // 7))
        add_unique(chosen, seen, sorted(phase, key=stat_balance_rank), max(16, limit // 7))
        add_unique(chosen, seen, sorted(phase, key=jit_def_before_supply_rank), max(16, limit // 7))
        add_unique(chosen, seen, sorted(phase, key=lambda e: (-residual_resource_value(e)[0], resource_group_score(e))), max(12, limit // 8))
        add_unique(chosen, seen, sorted(phase, key=lambda e: (base.boss_survival_deficit(e), score_key(e))), max(12, limit // 8))
        add_unique(chosen, seen, sorted(phase, key=lambda e: (-e["yk"], -e["bk"], resource_group_score(e))), max(12, limit // 8))
        if len(chosen) >= limit:
            return chosen[:limit]

    # Preserve the original search's representatives as a backstop.  This keeps
    # the experiment from becoming narrower than the legacy strategy.
    add_unique(chosen, seen, ORIGINAL_TRIM_ENTRIES(filtered, limit), limit)
    if len(chosen) >= limit:
        return chosen[:limit]

    add_unique(chosen, seen, sorted(filtered, key=score_key), limit)
    return chosen[:limit]


def best_goals(entries):
    return sorted(
        [e for e in entries if base.goal(e)],
        key=lambda e: (-final_resource_stock(e), resource_group_score(e), old_score(e), e.get("_dmg", 0)),
    )


def target_positions(fid: str, target: str) -> frozenset[tuple[int, int]]:
    return frozenset((x, y) for x, y, _t, eid in gw.maps[fid]["bl"] if eid == target)


def floor_action_variant(
    ent: dict[str, Any],
    fid: str,
    target: str,
    *,
    flyback: bool,
    require: set[tuple[int, int]] | None = None,
    forbid: set[tuple[int, int]] | None = None,
    max_iter: int = 250000,
    source_label: str | None = None,
) -> list[dict[str, Any]]:
    """Run one floor action and keep only variants with required/forbidden nodes.

    This keeps path choice and resource-pocket choice separated.  For example,
    entering 10F may first take the 6F x9y1 key pocket and then use an MT9
    up-floor path that does not consume 9F x2y2.
    """
    require = require or set()
    forbid = forbid or set()
    if target != "upFloor" and not base.target_available(ent, fid, target):
        return []

    pareto, _it, _nodes = gw.search_floor(
        gw.maps,
        fid,
        ent,
        [target],
        max_iter=max_iter,
        flyback=flyback,
    )
    if not pareto:
        return []

    already = base.collected_for(ent, fid)
    needed = target_positions(fid, target) - already
    results: list[dict[str, Any]] = []
    for hp, yk, bk, rk, atk, def_, _hs, vis, dc in pareto:
        if require and not require <= vis:
            continue
        if forbid and (forbid & vis):
            continue
        if target != "upFloor" and needed and not (vis & needed):
            continue
        nc = dict(ent.get("collected", {}))
        nc[fid] = already | vis
        r = gw._make_result(
            hp, yk, bk, rk, atk, def_, nc, ent["_id"],
            (fid, [target], flyback), dmg_cost=dc,
        )
        if source_label:
            r["_source"] = source_label
            gw._entry_store[r["_id"]]["_source"] = source_label
        results.append(r)
    return results


def prefer_low_cost(entries: list[dict[str, Any]], limit: int = 4) -> list[dict[str, Any]]:
    return sorted(
        entries,
        key=lambda e: (
            resource_group_score(e),
            e.get("_dmg", 0),
            e.get("_yd", 0),
            e.get("_bd", 0),
            -e["yk"],
            -e["bk"],
            -e["hp"],
        ),
    )[:limit]


def prefer_key_refill(entries: list[dict[str, Any]], limit: int = 4) -> list[dict[str, Any]]:
    return sorted(
        entries,
        key=lambda e: (
            -e["yk"],
            -e["bk"],
            resource_group_score(e),
            e.get("_dmg", 0),
            e.get("_yd", 0),
            -e["hp"],
        ),
    )[:limit]


def ensure_mt10(ent: dict[str, Any]) -> list[dict[str, Any]]:
    """Generate MT10 entry variants, including explicit key-pocket substitutes."""
    if "MT10" in ent.get("collected", {}):
        return [ent]

    variants: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()

    def add(items: list[dict[str, Any]]) -> None:
        for item in items:
            sig = (
                item["hp"], item["atk"], item["def"], item["yk"], item["bk"], item["rk"],
                item.get("_dmg", 0), item.get("_yd", 0), item.get("_bd", 0),
                tuple(sorted(item.get("collected", {}).get("MT6", frozenset()))),
                tuple(sorted(item.get("collected", {}).get("MT9", frozenset()))),
            )
            if sig in seen:
                continue
            seen.add(sig)
            variants.append(item)

    # Baseline: preserve the legacy direct MT9 up-floor behavior.
    add(ORIGINAL_ENSURE_MT10(ent))

    mt6_done = (9, 1) in base.collected_for(ent, "MT6")
    mt9_x2y2_done = (2, 2) in base.collected_for(ent, "MT9")

    # Key-pocket alternative: explicitly take 6F x9y1, then enter MT10 using an
    # MT9 path that avoids the expensive x2y2 key pocket.
    if not mt6_done and not mt9_x2y2_done and ent["atk"] >= 25 and ent["def"] >= 25:
        key_entries = floor_action_variant(
            ent,
            "MT6",
            "yellowKey",
            flyback=True,
            require={(9, 1)},
            max_iter=120000,
            source_label="MT6:x9y1-key-pocket",
        )
        pre_entry_sources = prefer_key_refill(key_entries, limit=4)

        # Some MT10 routes only become globally good if the cheap key is paired
        # with the 7F key pocket before entering 10F.  Generate both depths so
        # the outer search can compare "enter now" vs "refill then enter".
        for key_ent in list(pre_entry_sources):
            mt7_keys = floor_action_variant(
                key_ent,
                "MT7",
                "yellowKey",
                flyback=True,
                max_iter=120000,
                source_label="MT7:key-pocket-before-MT10",
            )
            pre_entry_sources.extend(prefer_key_refill(mt7_keys, limit=4))

        for key_ent in prefer_key_refill(pre_entry_sources, limit=8):
            up_entries = floor_action_variant(
                key_ent,
                "MT9",
                "upFloor",
                flyback=True,
                forbid={(2, 2)},
                max_iter=120000,
                source_label="MT9:upFloor-without-x2y2",
            )
            add(prefer_low_cost(up_entries, limit=4))

    # If a previous action has already taken the 6F key, still expose the clean
    # MT9 up-floor variant so it can compete with the incidental x2y2 path.
    if mt6_done and not mt9_x2y2_done:
        pre_entry_sources = [ent]
        mt7_keys = floor_action_variant(
            ent,
            "MT7",
            "yellowKey",
            flyback=True,
            max_iter=120000,
            source_label="MT7:key-pocket-before-MT10",
        )
        pre_entry_sources.extend(prefer_key_refill(mt7_keys, limit=4))
        for key_ent in prefer_key_refill(pre_entry_sources, limit=8):
            clean_up = floor_action_variant(
                key_ent,
                "MT9",
                "upFloor",
                flyback=True,
                forbid={(2, 2)},
                max_iter=120000,
                source_label="MT9:upFloor-without-x2y2",
            )
            add(prefer_low_cost(clean_up, limit=4))

    return prefer_low_cost(variants, limit=8)


def apply_action(ent: dict[str, Any], fid: str, target: str) -> list[dict[str, Any]]:
    if fid in SPECIAL_ACTION_REAL_FID and not special_action_allowed(ent, fid, target):
        return []
    if fid == "MT7_SKEL_KEY":
        return floor_action_variant(
            ent,
            "MT7",
            "yellowKey",
            flyback=True,
            require={(9, 1), (9, 2)},
            forbid={(9, 7), (9, 9), (9, 10), (9, 11)},
            max_iter=160000,
            source_label="MT7:skeleton-key-pocket",
        )
    if fid == "MT7_RIGHT_KEY":
        return floor_action_variant(
            ent,
            "MT7",
            "yellowKey",
            flyback=True,
            require={(9, 10), (9, 11)},
            max_iter=160000,
            source_label="MT7:right-key-pocket",
        )
    if fid == "MT5_DIRECT":
        return floor_action_variant(
            ent,
            "MT5",
            "blueGem",
            flyback=True,
            max_iter=250000,
            source_label="MT5:direct-blueGem-atk25",
        )
    if fid == "MT4_DIRECT":
        return floor_action_variant(
            ent,
            "MT4",
            "blueKey",
            flyback=True,
            max_iter=250000,
            source_label="MT4:direct-blueKey-early",
        )
    if fid == "MT9_BLUE_UP":
        return floor_action_variant(
            ent,
            "MT9",
            "upFloor",
            flyback=True,
            require={(3, 11)},
            max_iter=160000,
            source_label="MT9:blue-door-up",
        )
    if fid == "MT10_DIRECT":
        return floor_action_variant(
            ent,
            "MT10",
            target,
            flyback=("MT10" in ent.get("collected", {})),
            max_iter=250000,
            source_label=f"MT10:direct-{target}",
        )
    results = list(ORIGINAL_APPLY_ACTION(ent, fid, target))
    if (
        fid == "MT6"
        and target == "yellowKey"
        and ent["atk"] >= 25
        and ent["def"] >= 25
        and (9, 1) not in collected_for(ent, "MT6")
    ):
        results.extend(
            floor_action_variant(
                ent,
                "MT6",
                "yellowKey",
                flyback=True,
                require={(9, 1)},
                max_iter=120000,
                source_label="MT6:x9y1-key-pocket",
            )
        )
    return results


def compact(ent: dict[str, Any]) -> dict[str, Any]:
    residual, notes = residual_resource_value(ent)
    final_residual = final_residual_resource_value(ent)
    return {
        "hp": ent["hp"],
        "atk": ent["atk"],
        "def": ent["def"],
        "yk": ent["yk"],
        "bk": ent["bk"],
        "rk": ent["rk"],
        "dmg": ent.get("_dmg", 0),
        "yd": ent.get("_yd", 0),
        "bd": ent.get("_bd", 0),
        "rd": ent.get("_rd", 0),
        "old_score": old_score(ent),
        "resource_group_score": resource_group_score(ent),
        "residual_value": residual,
        "residual_notes": notes[:6],
        "final_residual_value": final_residual,
        "final_resource_stock": ent["hp"] + ent["yk"] * YK_VALUE + ent["bk"] * BK_VALUE + final_residual,
        "mt10_stage": base.mt10_stage(ent),
    }


def write_report(data: dict[str, Any]) -> None:
    goals = data.get("_goal_entries_obj", [])
    top_old = sorted(goals, key=old_score)[:10]
    top_new = sorted(goals, key=score_key)[:10]
    top_stock = sorted(goals, key=lambda e: (-final_resource_stock(e), resource_group_score(e), old_score(e)))[:10]
    data["top_old_score"] = [compact(e) for e in top_old]
    data["top_resource_group_score"] = [compact(e) for e in top_new]
    data["top_final_stock"] = [compact(e) for e in top_stock]
    data.pop("_goal_entries_obj", None)

    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    lines = [
        "# Post-9 Resource Group Search",
        "",
        "从固定攻略前缀 `9F 红蓝宝石后` 开始，复用旧 post9 action search 的真实寻路，只替换外层排序/选源。",
        "",
        "`old_score = dmg + yd*50 + bd*200 - hp - yk*50 - bk*200`",
        "",
        "`resource_group_score = dmg - hp - yk*50 - bk*200 + 阶段缺口惩罚 - 剩余资源组动态净值`",
        "",
        f"- elapsed: {data['elapsed']:.1f}s",
        f"- final entry count: {data['entry_count']}",
        f"- goal count: {data['goal_count']}",
    ]
    if data.get("best"):
        b = data["best"]
        lines.append(
            f"- best by final stock: HP={b['hp']} ATK={b['atk']} DEF={b['def']} "
            f"YK={b['yk']} BK={b['bk']} RK={b['rk']} dmg={b['dmg']} "
            f"door={b['yd']}/{b['bd']}/{b['rd']} score={b.get('resource_group_score')} "
            f"finalStock={b.get('final_resource_stock')}"
        )
    lines.extend([
        "",
        "## Top By Final Stock",
        "",
        "| # | finalStock | finalResidual0dmg | rgScore | oldScore | state | notes |",
        "|---:|---:|---:|---:|---:|---|---|",
    ])
    for idx, row in enumerate(data["top_final_stock"], 1):
        notes = "; ".join(row["residual_notes"]) or "-"
        lines.append(
            f"| {idx} | {row['final_resource_stock']} | {row['final_residual_value']} | "
            f"{row['resource_group_score']} | {row['old_score']} | "
            f"HP={row['hp']} ATK={row['atk']} DEF={row['def']} YK={row['yk']} BK={row['bk']} RK={row['rk']} "
            f"dmg={row['dmg']} door={row['yd']}/{row['bd']}/{row['rd']} | {notes} |"
        )
    lines.extend([
        "",
        "## Top By Resource Group Score",
        "",
        "| # | rgScore | oldScore | residual | state | notes |",
        "|---:|---:|---:|---:|---|---|",
    ])
    for idx, row in enumerate(data["top_resource_group_score"], 1):
        notes = "; ".join(row["residual_notes"]) or "-"
        lines.append(
            f"| {idx} | {row['resource_group_score']} | {row['old_score']} | {row['residual_value']} | "
            f"HP={row['hp']} ATK={row['atk']} DEF={row['def']} YK={row['yk']} BK={row['bk']} RK={row['rk']} "
            f"dmg={row['dmg']} door={row['yd']}/{row['bd']}/{row['rd']} | {notes} |"
        )
    lines.extend([
        "",
        "## Top By Old Score",
        "",
        "| # | oldScore | rgScore | residual | state | notes |",
        "|---:|---:|---:|---:|---|---|",
    ])
    for idx, row in enumerate(data["top_old_score"], 1):
        notes = "; ".join(row["residual_notes"]) or "-"
        lines.append(
            f"| {idx} | {row['old_score']} | {row['resource_group_score']} | {row['residual_value']} | "
            f"HP={row['hp']} ATK={row['atk']} DEF={row['def']} YK={row['yk']} BK={row['bk']} RK={row['rk']} "
            f"dmg={row['dmg']} door={row['yd']}/{row['bd']}/{row['rd']} | {notes} |"
        )

    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")


def run(rounds: int, entry_limit: int, source_limit: int) -> dict[str, Any]:
    base.select_sources = select_sources
    base.trim_entries = trim_entries
    base.best_goals = best_goals
    base.ensure_mt10 = ensure_mt10
    base.apply_action = apply_action
    base.redkey_survival_deficit = redkey_survival_deficit
    base.OUT_JSON = OUT_JSON
    base.OUT_MD = OUT_MD
    base.OUT_WALK = OUT_WALK

    t0 = time.time()
    start = base.seed_fixed_prefix()
    stat_entries, stat_rows = base.run_stage(
        "stat27", [start], STAT_ACTIONS, base.stat_goal,
        max(6, rounds), entry_limit, source_limit,
    )
    redkey_entries, redkey_rows = base.run_stage(
        "redkey", stat_entries, base.REDKEY_ACTIONS, base.redkey_goal,
        max(4, rounds // 2), entry_limit, source_limit,
    )
    final_entries, boss_rows = base.run_stage(
        "boss", redkey_entries, base.BOSS_PREP_ACTIONS, base.goal,
        max(4, rounds // 2), entry_limit, source_limit, include_boss=True,
    )
    goals = best_goals(final_entries)
    best = goals[0] if goals else None
    if best:
        best["_resource_group_score"] = resource_group_score(best)
        base.write_walk(best)
    data = {
        "elapsed": time.time() - t0,
        "rounds": stat_rows + redkey_rows + boss_rows,
        "entry_count": len(final_entries),
        "goal_count": len(goals),
        "best": compact(best) if best else None,
        "top_goals": [compact(e) for e in goals[:10]],
        "_goal_entries_obj": goals,
    }
    # Preserve the existing report writer output path, then overwrite with a
    # richer experiment report that includes both score orderings.
    write_report(data)
    return data


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds", type=int, default=12)
    parser.add_argument("--entry-limit", type=int, default=360)
    parser.add_argument("--source-limit", type=int, default=28)
    args = parser.parse_args()
    data = run(args.rounds, args.entry_limit, args.source_limit)
    if data.get("best"):
        b = data["best"]
        print(
            f"best HP={b['hp']} ATK={b['atk']} DEF={b['def']} YK={b['yk']} "
            f"BK={b['bk']} RK={b['rk']} dmg={b['dmg']} door={b['yd']}/{b['bd']}/{b['rd']} "
            f"rgScore={b['resource_group_score']}"
        )
    print(f"wrote {OUT_JSON}")
    print(f"wrote {OUT_MD}")
    print(f"wrote {OUT_WALK}")


if __name__ == "__main__":
    main()
