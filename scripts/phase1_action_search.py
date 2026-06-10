#!/usr/bin/env python3
"""Experimental action-level Phase1 search.

This keeps the proven floor-level Dijkstra/Pareto search, but replaces the
hand-written 4F-9F milestone order with a small A*-style action scheduler.
The heuristic only controls expansion order; pruning still uses real Pareto
dimensions so key/door tradeoffs are not collapsed into a hard HP estimate.
"""

from __future__ import annotations

import heapq
import json
import os
import sys
import time
import argparse
from collections import defaultdict
from itertools import combinations


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.chdir(ROOT)

from src.solver import gen_walkthrough as gw


OUT_JSON = os.path.join("outputs", "results", "phase1_action_search.json")
OUT_MD = os.path.join("outputs", "reports", "phase1_action_search.md")

FLOOR_NO = {
    "MT4": 4,
    "MT5": 5,
    "MT6": 6,
    "MT7": 7,
    "MT8": 8,
    "MT9": 9,
}

FLOOR_ID = {v: k for k, v in FLOOR_NO.items()}

PROGRESSION = {
    4: ("MT4", ["upFloor"]),
    5: ("MT5", ["upFloor"]),
    6: ("MT6", ["upFloor"]),
    7: ("MT7", ["upFloor"]),
    8: ("MT8", ["upFloor"]),
}

PHASE1_MAJOR_TARGETS = {"sword1", "shield1", "redGem", "blueGem"}
PHASE1_RESOURCE_TARGETS = {"yellowKey", "blueKey", "redPotion", "bluePotion"}
PHASE1_ACTION_TARGETS = PHASE1_MAJOR_TARGETS | PHASE1_RESOURCE_TARGETS

TARGET_ORDER = {
    "upFloor": -1,
    "sword1": 0,
    "shield1": 1,
    "redGem": 2,
    "blueGem": 3,
    "blueKey": 4,
    "yellowKey": 5,
    "bluePotion": 6,
    "redPotion": 7,
}

FIXED_EXACT = {
    "hp": 148,
    "atk": 23,
    "def": 21,
    "yk": 2,
    "bk": 1,
    "rk": 0,
    "dmg": 928,
    "yd": 23,
    "bd": 0,
    "rd": 0,
}

DELAYED_SHAPE = {
    "atk": 22,
    "def": 21,
    "yk": 2,
    "bk": 1,
    "rk": 0,
}


def state_text(e):
    return (
        f"HP={e['hp']} ATK={e['atk']} DEF={e['def']} "
        f"YK={e['yk']} BK={e['bk']} RK={e['rk']}"
    )


def metric_text(e):
    return (
        f"{state_text(e)} dmg={e.get('_dmg', 0)} "
        f"door={e.get('_yd', 0)}/{e.get('_bd', 0)}/{e.get('_rd', 0)}"
    )


def item_positions(fid, eid):
    return frozenset(
        (b[0], b[1])
        for b in gw.maps[fid]["bl"]
        if b[3] == eid
    )


MT9_SHIELD = item_positions("MT9", "shield1")
MT9_RED = item_positions("MT9", "redGem")
MT9_BLUE = item_positions("MT9", "blueGem")
MAJOR_TARGETS = {"sword1", "shield1", "redGem", "blueGem", "greenGem"}


def collected_for(e, fid):
    positions = set(e.get("collected", {}).get(fid, frozenset()))
    if fid in gw.FLOOR_13_COLLECTED:
        positions.update(gw.FLOOR_13_COLLECTED[fid])
    return frozenset(positions)


def has_item(e, fid, eid):
    return bool(item_positions(fid, eid) & collected_for(e, fid))


def has_uncollected_target(e, fid, target):
    if target == "upFloor":
        return True
    already = collected_for(e, fid)
    return any(
        (b[0], b[1]) not in already and b[3] == target
        for b in gw.maps[fid]["bl"]
    )


def floor_targets(fid, allowed=PHASE1_ACTION_TARGETS):
    targets = {
        b[3]
        for b in gw.maps[fid]["bl"]
        if b[3] in allowed
    }
    return sorted(targets, key=lambda t: TARGET_ORDER.get(t, 99))


def ordered_targets(targets):
    return sorted(dict.fromkeys(targets), key=lambda t: TARGET_ORDER.get(t, 99))


def target_combinations(targets, max_size=3):
    ordered = ordered_targets(targets)
    for size in range(1, min(max_size, len(ordered)) + 1):
        for combo in combinations(ordered, size):
            yield list(combo)


def unintended_major_positions(fid, targets, visited):
    allowed = set(targets)
    return [
        (b[0], b[1], b[3])
        for b in gw.maps[fid]["bl"]
        if b[3] in MAJOR_TARGETS and b[3] not in allowed and (b[0], b[1]) in visited
    ]


def collected_signature(e):
    return tuple(
        (fid, tuple(sorted(pos)))
        for fid, pos in sorted((e.get("collected") or {}).items())
        if pos
    )


def archive_bucket(e):
    return (e.get("_max_floor", 4), collected_signature(e))


def dominates(a, b):
    if not (
        a.get("_dmg", 0) <= b.get("_dmg", 0) and
        a.get("_yd", 0) <= b.get("_yd", 0) and
        a.get("_bd", 0) <= b.get("_bd", 0) and
        a.get("_rd", 0) <= b.get("_rd", 0) and
        a["atk"] >= b["atk"] and
        a["def"] >= b["def"] and
        a["yk"] >= b["yk"] and
        a["bk"] >= b["bk"] and
        a["rk"] >= b["rk"]
    ):
        return False
    strict = (
        a.get("_dmg", 0) < b.get("_dmg", 0) or
        a.get("_yd", 0) < b.get("_yd", 0) or
        a.get("_bd", 0) < b.get("_bd", 0) or
        a.get("_rd", 0) < b.get("_rd", 0) or
        a["atk"] > b["atk"] or
        a["def"] > b["def"] or
        a["yk"] > b["yk"] or
        a["bk"] > b["bk"] or
        a["rk"] > b["rk"]
    )
    same_core = (
        a.get("_dmg", 0) == b.get("_dmg", 0) and
        a.get("_yd", 0) == b.get("_yd", 0) and
        a.get("_bd", 0) == b.get("_bd", 0) and
        a.get("_rd", 0) == b.get("_rd", 0) and
        a["atk"] == b["atk"] and
        a["def"] == b["def"] and
        a["yk"] == b["yk"] and
        a["bk"] == b["bk"] and
        a["rk"] == b["rk"]
    )
    return strict or (same_core and a["hp"] >= b["hp"])


def add_to_archive(archive, e):
    bucket = archive_bucket(e)
    items = archive[bucket]
    if any(dominates(old, e) for old in items):
        return False
    archive[bucket] = [old for old in items if not dominates(e, old)]
    archive[bucket].append(e)
    return True


def is_goal(e):
    if e.get("_max_floor", 4) < 9:
        return False
    mt9 = collected_for(e, "MT9")
    return bool(MT9_SHIELD <= mt9 and MT9_RED <= mt9 and MT9_BLUE <= mt9)


def fixed_exact_match(e):
    return (
        e["hp"] == FIXED_EXACT["hp"] and
        e["atk"] == FIXED_EXACT["atk"] and
        e["def"] == FIXED_EXACT["def"] and
        e["yk"] == FIXED_EXACT["yk"] and
        e["bk"] == FIXED_EXACT["bk"] and
        e["rk"] == FIXED_EXACT["rk"] and
        e.get("_dmg", 0) == FIXED_EXACT["dmg"] and
        e.get("_yd", 0) == FIXED_EXACT["yd"] and
        e.get("_bd", 0) == FIXED_EXACT["bd"] and
        e.get("_rd", 0) == FIXED_EXACT["rd"]
    )


def delayed_shape_match(e):
    return (
        e["atk"] == DELAYED_SHAPE["atk"] and
        e["def"] == DELAYED_SHAPE["def"] and
        e["yk"] == DELAYED_SHAPE["yk"] and
        e["bk"] == DELAYED_SHAPE["bk"] and
        e["rk"] == DELAYED_SHAPE["rk"]
    )


def phase1_yk_demand(e):
    """Small demand estimate for optional yellow-key actions.

    It is intentionally only a demand signal: real reachability and Pareto
    pruning still decide whether the resource pickup is worth keeping.
    """
    max_floor = e.get("_max_floor", 4)
    demand = 2
    if not has_item(e, "MT5", "sword1"):
        demand = max(demand, 3)
    if max_floor <= 6:
        demand = max(demand, 4)
    elif max_floor <= 7:
        demand = max(demand, 3)
    return demand


def phase1_bk_demand(e):
    # Preserve one blue key as a reachability resource for the post-shield
    # continuation.  Door counters still prevent key-heavy routes from hiding
    # lower-consumption alternatives.
    return 1


def phase1_hp_demand(e):
    if not has_item(e, "MT9", "shield1"):
        return 140
    return 0


def phase1_resource_needed(e, target):
    if target == "yellowKey":
        return e["yk"] < phase1_yk_demand(e)
    if target == "blueKey":
        return e["bk"] < phase1_bk_demand(e)
    if target in {"redPotion", "bluePotion"}:
        return e["hp"] < phase1_hp_demand(e)
    return False


def phase1_target_allowed(e, fid, target):
    if not has_uncollected_target(e, fid, target):
        return False
    max_floor = e.get("_max_floor", 4)
    if FLOOR_NO[fid] > max_floor:
        return False

    sword_done = has_item(e, "MT5", "sword1")
    if target == "sword1":
        return fid == "MT5" and max_floor >= 5 and not sword_done
    if not sword_done:
        return False
    if target == "shield1":
        return fid == "MT9" and max_floor >= 9
    if target == "redGem":
        # MT8's gem pocket belongs to the post-shield resource phase; pulling
        # it into the 4-9 shield comparison spends the blue-key budget before
        # the phase boundary.
        return e["atk"] < 23 and fid != "MT8"
    if target == "blueGem":
        return e["def"] < 21 and fid == "MT9"
    if target in PHASE1_RESOURCE_TARGETS:
        return phase1_resource_needed(e, target)
    return False


def action_targets_with_incidental(e, fid, required_targets):
    """Allow useful same-floor resources to be picked while pursuing a target."""
    targets = list(required_targets)
    for target in floor_targets(fid, PHASE1_RESOURCE_TARGETS):
        if target == "yellowKey":
            pass
        elif target == "redPotion" and fid != "MT9":
            pass
        elif not phase1_resource_needed(e, target):
            continue
        if target not in targets and has_uncollected_target(e, fid, target):
            targets.append(target)
    return sorted(targets, key=lambda t: TARGET_ORDER.get(t, 99))


def action_sort_token(action):
    fid, targets, flyback, new_floor, must_targets = action_parts(action)
    return (
        fid,
        tuple(targets),
        bool(flyback),
        new_floor,
        tuple(must_targets),
    )


def heuristic(e, target_atk=23, atk_weight=140):
    score = 0
    max_floor = e.get("_max_floor", 4)
    score += max(0, 9 - max_floor) * 160
    if not has_item(e, "MT5", "sword1"):
        score += 900
    if e["atk"] < 21 and has_uncollected_target(e, "MT4", "redGem"):
        score += 700
    # A small attack-threshold hint keeps the early-red branch represented, but
    # is deliberately weaker than the old hard bias so delayed-after-shield
    # variants can survive too.
    if max_floor >= 7 and e["atk"] < 22 and has_uncollected_target(e, "MT7", "redGem"):
        score += 120
    if not has_item(e, "MT9", "shield1"):
        score += 300
    if not has_item(e, "MT9", "redGem"):
        score += 90
    if not has_item(e, "MT9", "blueGem"):
        score += 90
    projected_atk = e["atk"]
    projected_def = e["def"]
    if max_floor >= 7:
        if has_uncollected_target(e, "MT9", "redGem"):
            projected_atk += 1
        if has_uncollected_target(e, "MT9", "shield1"):
            projected_def += 10
        if has_uncollected_target(e, "MT9", "blueGem"):
            projected_def += 1
    score += max(0, target_atk - projected_atk) * atk_weight
    score += max(0, 21 - projected_def) * 80
    needed_yk = 2
    if max_floor == 6:
        needed_yk = 4
    elif max_floor == 7:
        needed_yk = 3
    score += max(0, needed_yk - e["yk"]) * 85
    score += max(0, 1 - e["bk"]) * 180
    return score


def priority(e):
    resource_bonus = (
        e["yk"] * 18 +
        e["bk"] * 90 +
        max(0, e["atk"] - 21) * 70 +
        max(0, e["def"] - 20) * 35
    )
    return (
        e.get("_dmg", 0) + heuristic(e) +
        e.get("_yd", 0) * 14 + e.get("_bd", 0) * 80 + e.get("_rd", 0) * 120 -
        resource_bonus,
        -e.get("_max_floor", 4),
        max(0, phase1_yk_demand(e) - e["yk"]),
        max(0, phase1_bk_demand(e) - e["bk"]),
        e.get("_dmg", 0),
        e.get("_yd", 0),
        e.get("_bd", 0),
        -e["atk"],
        -e["def"],
        -e["yk"],
        -e["bk"],
        -e["hp"],
    )


def dmg_first_priority(e):
    return (
        e.get("_dmg", 0) + heuristic(e, target_atk=22, atk_weight=80) +
        e.get("_yd", 0) * 10 + e.get("_bd", 0) * 45 + e.get("_rd", 0) * 120,
        -e.get("_max_floor", 4),
        e.get("_dmg", 0),
        e.get("_yd", 0),
        e.get("_bd", 0),
        -e["atk"],
        -e["def"],
        -e["yk"],
        -e["bk"],
        -e["hp"],
    )


def action_rank(e, action):
    fid, targets, _flyback, _new_floor, _must_targets = action_parts(action)
    target_set = set(targets)
    rank = 100
    if "upFloor" in target_set:
        rank = 10 + max(0, FLOOR_NO[fid] - 4)
        if target_set - {"upFloor"}:
            rank -= 3
    elif "sword1" in target_set:
        rank = 1
    elif "shield1" in target_set:
        rank = 6 if len(target_set) > 1 else 8
    elif "blueGem" in target_set and "redGem" in target_set:
        rank = 18
    elif "blueGem" in target_set:
        rank = 20
    elif "redGem" in target_set:
        if fid == "MT4" and e["atk"] < 21:
            rank = 2
        elif fid == "MT7" and e["atk"] < 22:
            rank = 24
        else:
            rank = 32
    elif "blueKey" in target_set:
        rank = 42 if e["bk"] < phase1_bk_demand(e) else 80
    elif "yellowKey" in target_set:
        rank = 45 if e["yk"] < phase1_yk_demand(e) else 75
    elif any(t.endswith("Potion") for t in target_set):
        rank = 65 if e["hp"] < phase1_hp_demand(e) else 95
    return (
        rank,
        FLOOR_NO.get(fid, 99),
        -len(target_set),
        e.get("_dmg", 0),
    )


def possible_actions(e):
    actions = []
    seen = set()
    max_floor = e.get("_max_floor", 4)

    sword_done = has_item(e, "MT5", "sword1")

    def add_action(fid, targets, flyback, new_max_floor, must_targets=None):
        targets = ordered_targets(targets)
        must_targets = ordered_targets(must_targets or targets)
        action = (fid, targets, flyback, new_max_floor, must_targets)
        key = action_sort_token(action)
        if key in seen:
            return
        seen.add(key)
        actions.append(action)

    def add_major_combos(fid, flyback, new_max_floor, include_upfloor=False):
        allowed_major = [
            target for target in floor_targets(fid, PHASE1_MAJOR_TARGETS)
            if phase1_target_allowed(e, fid, target)
        ]
        if include_upfloor:
            for combo in target_combinations(allowed_major, max_size=3):
                targets = combo + ["upFloor"]
                add_action(fid, targets, flyback, new_max_floor, targets)
            return
        for combo in target_combinations(allowed_major, max_size=3):
            add_action(fid, combo, flyback, new_max_floor, combo)

    if max_floor < 9 and (max_floor < 5 or sword_done):
        fid, targets = PROGRESSION[max_floor]
        add_action(fid, targets, False, max_floor + 1, targets)
        if sword_done:
            add_major_combos(fid, False, max_floor + 1, include_upfloor=True)

    if max_floor < 5:
        return actions

    if not sword_done:
        if has_uncollected_target(e, "MT5", "sword1"):
            flyback = "MT5" in e.get("collected", {}) or max_floor > 5
            add_action("MT5", ["sword1"], flyback, max_floor)
        actions.sort(key=lambda action: action_rank(e, action))
        return actions[:3]

    reached = [fid for fid, no in FLOOR_NO.items() if no <= max_floor]
    for fid in reached:
        flyback = fid in e.get("collected", {}) or FLOOR_NO[fid] < max_floor
        add_major_combos(fid, flyback, max_floor)

    actions.sort(key=lambda action: action_rank(e, action))
    return actions[:12]


def action_parts(action):
    if len(action) == 4:
        fid, targets, flyback, new_max_floor = action
        return fid, targets, flyback, new_max_floor, list(targets)
    fid, targets, flyback, new_max_floor, must_targets = action
    return fid, targets, flyback, new_max_floor, list(must_targets)


def expand_action(e, action):
    fid, targets, flyback, new_max_floor, must_targets = action_parts(action)
    already = collected_for(e, fid)
    pareto, _iters, _nodes = gw.search_floor(
        gw.maps,
        fid,
        e,
        targets,
        max_iter=120000,
        flyback=flyback,
    )
    if not pareto:
        return []
    results = []
    need = frozenset()
    for target in must_targets:
        need |= frozenset(
            (b[0], b[1])
            for b in gw.maps[fid]["bl"]
            if b[3] == target and (b[0], b[1]) not in already
        )
    for hp, yk, bk, rk, atk, def_, _hs, vis, dc in pareto:
        if need and not need <= vis:
            continue
        if unintended_major_positions(fid, targets, vis):
            continue
        nc = dict(e.get("collected", {}))
        nc[fid] = already | vis
        r = gw._make_result(
            hp,
            yk,
            bk,
            rk,
            atk,
            def_,
            nc,
            e["_id"],
            (fid, targets, flyback),
            dmg_cost=dc,
        )
        r["_max_floor"] = new_max_floor
        r["_action_depth"] = e.get("_action_depth", 0) + 1
        r["_last_action"] = f"{fid}:{'+'.join(targets)}:{'fb' if flyback else 'new'}"
        gw._entry_store[r["_id"]].update({
            "_max_floor": r["_max_floor"],
            "_action_depth": r["_action_depth"],
            "_last_action": r["_last_action"],
        })
        results.append(r)
    return cap_action_results(results)


def cap_action_results(results, limit=96):
    if len(results) <= limit:
        return results
    chosen = []
    seen = set()

    def key_for(e):
        return (
            e["atk"], e["def"], e["yk"], e["bk"], e["rk"],
            e.get("_yd", 0), e.get("_bd", 0), e.get("_rd", 0),
            collected_signature(e),
        )

    def add(items, quota):
        added = 0
        for e in items:
            key = key_for(e)
            if key in seen:
                continue
            seen.add(key)
            chosen.append(e)
            added += 1
            if len(chosen) >= limit or added >= quota:
                return

    add(sorted(results, key=lambda e: (e.get("_dmg", 0), e.get("_yd", 0), e.get("_bd", 0), -e["hp"])), 12)
    add(sorted(results, key=lambda e: (e.get("_yd", 0), e.get("_bd", 0), e.get("_rd", 0), e.get("_dmg", 0), -e["yk"], -e["bk"], -e["hp"])), 14)
    add(sorted(results, key=lambda e: (e.get("_bd", 0), e.get("_yd", 0), e.get("_rd", 0), e.get("_dmg", 0), -e["yk"], -e["bk"], -e["hp"])), 12)
    add(sorted(results, key=lambda e: (e.get("_bd", 0), -e["bk"], e.get("_yd", 0), e.get("_dmg", 0), -e["hp"])), 12)
    add(sorted(results, key=lambda e: (-e["bk"], e.get("_bd", 0), e.get("_dmg", 0), e.get("_yd", 0), -e["hp"])), 10)
    add(sorted(results, key=lambda e: (-e["yk"], -e["bk"], e.get("_bd", 0), e.get("_yd", 0), e.get("_dmg", 0), -e["hp"])), 14)
    add(sorted(results, key=lambda e: (-(e["atk"] + e["def"]), e.get("_dmg", 0), -e["yk"], -e["hp"])), 8)
    add(sorted(results, key=lambda e: (-e["hp"], e.get("_dmg", 0), -e["yk"])), 8)
    return chosen[:limit]


def select_representatives(entries, limit=20):
    chosen = []
    seen = set()

    def add(items, quota):
        added = 0
        for e in items:
            key = (
                e["atk"], e["def"], e["yk"], e["bk"], e["rk"],
                e.get("_yd", 0), e.get("_bd", 0), e.get("_rd", 0),
                collected_signature(e),
            )
            if key in seen:
                continue
            seen.add(key)
            chosen.append(e)
            added += 1
            if len(chosen) >= limit or added >= quota:
                return

    add(sorted(entries, key=lambda e: (e.get("_dmg", 0), e.get("_yd", 0), e.get("_bd", 0), e.get("_rd", 0), -e["hp"])), 5)
    add(sorted(entries, key=lambda e: (e.get("_bd", 0), -e["bk"], e.get("_yd", 0), e.get("_dmg", 0), -e["hp"])), 5)
    add(sorted(entries, key=lambda e: (e.get("_yd", 0), e.get("_bd", 0), e.get("_dmg", 0), -e["yk"], -e["bk"], -e["hp"])), 4)
    add(sorted(
        [
            e for e in entries
            if e.get("_bd", 0) == 0 and e["bk"] >= 1 and
            not has_item(e, "MT7", "redGem")
        ],
        key=lambda e: (e.get("_dmg", 0), e.get("_yd", 0), -e["yk"], -e["hp"]),
    ), 4)
    add(sorted(entries, key=lambda e: (-e["yk"], -e["bk"], e.get("_dmg", 0), e.get("_yd", 0), -e["hp"])), 4)
    add(sorted(entries, key=lambda e: (-(e["atk"] + e["def"]), e.get("_dmg", 0), e.get("_yd", 0), -e["hp"])), 4)
    add(sorted(entries, key=lambda e: (-e["hp"], e.get("_dmg", 0), e.get("_yd", 0), -e["yk"])), 4)
    return chosen[:limit]


def chain_labels(e):
    labels = []
    current = e
    while current:
        label = current.get("_last_action")
        if label:
            labels.append(label)
        parent_id = current.get("_parent_id")
        current = gw._entry_store.get(parent_id)
    labels.reverse()
    return labels


def chain_records(e):
    records = []
    chain = []
    current = e
    while current:
        chain.append(current)
        parent_id = current.get("_parent_id")
        current = gw._entry_store.get(parent_id)
    chain.reverse()
    for item in chain:
        label = item.get("_last_action")
        if not label:
            continue
        records.append({
            "action": label,
            "hp": item["hp"],
            "atk": item["atk"],
            "def": item["def"],
            "yk": item["yk"],
            "bk": item["bk"],
            "rk": item["rk"],
            "dmg": item.get("_dmg", 0),
            "yd": item.get("_yd", 0),
            "bd": item.get("_bd", 0),
            "rd": item.get("_rd", 0),
        })
    return records


def result_record(e):
    return {
        "id": e.get("_id"),
        "hp": e["hp"],
        "atk": e["atk"],
        "def": e["def"],
        "yk": e["yk"],
        "bk": e["bk"],
        "rk": e["rk"],
        "dmg": e.get("_dmg", 0),
        "yd": e.get("_yd", 0),
        "bd": e.get("_bd", 0),
        "rd": e.get("_rd", 0),
        "max_floor": e.get("_max_floor", 4),
        "depth": e.get("_action_depth", 0),
        "fixed_exact": fixed_exact_match(e),
        "delayed_shape": delayed_shape_match(e),
        "mt7_red_taken": has_item(e, "MT7", "redGem"),
        "actions": chain_labels(e),
        "chain": chain_records(e),
    }


def best_record(entries, key_fn):
    if not entries:
        return None
    return result_record(sorted(entries, key=key_fn)[0])


def representative_buckets(goal_entries):
    profiles = {
        "bk1_bd0": lambda e: e["bk"] >= 1 and e.get("_bd", 0) == 0,
        "atk23_def21_yk2_bk1": lambda e: (
            e["atk"] == 23 and e["def"] == 21 and e["yk"] == 2 and
            e["bk"] == 1 and e["rk"] == 0
        ),
        "atk23_def21_yk2_bk1_bd0": lambda e: (
            e["atk"] == 23 and e["def"] == 21 and e["yk"] == 2 and
            e["bk"] == 1 and e["rk"] == 0 and e.get("_bd", 0) == 0
        ),
        "delayed_bd0": lambda e: delayed_shape_match(e) and e.get("_bd", 0) == 0,
        "delayed_7f_red_bd0": lambda e: (
            e["atk"] == 22 and e["def"] == 21 and e["yk"] >= 2 and
            e["bk"] >= 1 and e["rk"] == 0 and e.get("_bd", 0) == 0 and
            not has_item(e, "MT7", "redGem")
        ),
        "atk23_def21_yk2_bk1_bd0_7f_red_left": lambda e: (
            e["atk"] == 23 and e["def"] == 21 and e["yk"] == 2 and
            e["bk"] == 1 and e["rk"] == 0 and e.get("_bd", 0) == 0 and
            not has_item(e, "MT7", "redGem")
        ),
        "fixed_exact_loose_hp": lambda e: (
            e["atk"] == FIXED_EXACT["atk"] and
            e["def"] == FIXED_EXACT["def"] and
            e["yk"] == FIXED_EXACT["yk"] and
            e["bk"] == FIXED_EXACT["bk"] and
            e["rk"] == FIXED_EXACT["rk"] and
            e.get("_dmg", 0) == FIXED_EXACT["dmg"] and
            e.get("_yd", 0) == FIXED_EXACT["yd"] and
            e.get("_bd", 0) == FIXED_EXACT["bd"] and
            e.get("_rd", 0) == FIXED_EXACT["rd"]
        ),
    }
    out = {}
    for name, pred in profiles.items():
        matches = [e for e in goal_entries if pred(e)]
        out[name] = {
            "count": len(matches),
            "best": best_record(
                matches,
                lambda e: (e.get("_dmg", 0), e.get("_yd", 0), e.get("_bd", 0), e.get("_rd", 0), -e["hp"]),
            ),
        }
    counts = defaultdict(int)
    for e in goal_entries:
        counts[f"bd{e.get('_bd', 0)}_bk{e['bk']}"] += 1
    out["bd_bk_counts"] = dict(sorted(counts.items()))
    return out


def run(max_expansions=220, goal_limit=80, include_entries=False, queue_mode="resource"):
    gw.PHASE1_BUCKETS_ENABLED = True
    gw._entry_store.clear()
    gw._next_id[0] = 1
    start = {
        "hp": gw.hero["h"],
        "atk": gw.hero["a"],
        "def": gw.hero["d"],
        "yk": gw.hero["yk"],
        "bk": gw.hero["bk"],
        "rk": 0,
        "collected": gw.initial_collected_state(),
        "_id": 1,
        "_parent_id": None,
        "_step_info": None,
        "_dmg": 0,
        "_yd": 0,
        "_bd": 0,
        "_rd": 0,
        "_max_floor": 4,
        "_action_depth": 0,
    }
    gw._entry_store[1] = dict(start)

    archive = defaultdict(list)
    add_to_archive(archive, start)
    primary_heap = []
    dmg_heap = []
    seq = 0
    if queue_mode in {"resource", "dual"}:
        heapq.heappush(primary_heap, (priority(start), seq, start))
    if queue_mode in {"dmg", "dual"}:
        heapq.heappush(dmg_heap, (dmg_first_priority(start), seq, start))
    goals = []
    expansions = 0
    generated = 0
    t0 = time.time()

    goal_seen = set()
    expanded_ids = set()

    def pop_next(prefer_dmg):
        if queue_mode == "resource":
            heaps = [primary_heap]
        elif queue_mode == "dmg":
            heaps = [dmg_heap]
        else:
            heaps = [dmg_heap, primary_heap] if prefer_dmg else [primary_heap, dmg_heap]
        for heap in heaps:
            while heap:
                _prio, _seq, item = heapq.heappop(heap)
                if item["_id"] not in expanded_ids:
                    return item
        return None

    while (primary_heap or dmg_heap) and expansions < max_expansions:
        entry = pop_next(prefer_dmg=(expansions % 3 == 2))
        if entry is None:
            break
        expanded_ids.add(entry["_id"])
        expansions += 1
        if expansions % 25 == 0:
            print(
                f"expanded={expansions} heap={len(primary_heap) + len(dmg_heap)} goals={len(goals)} "
                f"entry={metric_text(entry)} maxF={entry.get('_max_floor', 4)}",
                flush=True,
            )
        if is_goal(entry) and entry["_id"] not in goal_seen:
            goal_seen.add(entry["_id"])
            goals.append(entry)
        if entry.get("_action_depth", 0) >= 14:
            continue
        for action in possible_actions(entry):
            for child in expand_action(entry, action):
                generated += 1
                if not add_to_archive(archive, child):
                    continue
                seq += 1
                if queue_mode in {"resource", "dual"}:
                    heapq.heappush(primary_heap, (priority(child), seq, child))
                if queue_mode in {"dmg", "dual"}:
                    heapq.heappush(dmg_heap, (dmg_first_priority(child), seq, child))

    elapsed = time.time() - t0
    all_archive = [e for items in archive.values() for e in items]
    goal_entries = goals + [e for e in all_archive if is_goal(e)]
    representatives = select_representatives(goal_entries, limit=20)
    representatives.sort(key=lambda e: (e.get("_dmg", 0), e.get("_yd", 0), e.get("_bd", 0), e.get("_rd", 0), -e["hp"]))
    fixed_matches = [e for e in goal_entries if fixed_exact_match(e)]
    delayed_matches = [e for e in goal_entries if delayed_shape_match(e)]
    result = {
        "elapsed": elapsed,
        "expansions": expansions,
        "generated": generated,
        "archive_entries": len(all_archive),
        "goal_entries": len(goal_entries),
        "frontier_left": len(primary_heap) + len(dmg_heap),
        "queue_mode": queue_mode,
        "fixed_exact_count": len(fixed_matches),
        "delayed_shape_count": len(delayed_matches),
        "top": [result_record(e) for e in representatives],
        "best_fixed_exact": result_record(sorted(fixed_matches, key=lambda e: (e.get("_dmg", 0), -e["hp"]))[0]) if fixed_matches else None,
        "best_delayed_shape": result_record(sorted(delayed_matches, key=lambda e: (e.get("_dmg", 0), e.get("_yd", 0), -e["hp"]))[0]) if delayed_matches else None,
        "buckets": representative_buckets(goal_entries),
    }
    if include_entries:
        result["_goal_entries"] = goal_entries
        result["_archive_entries_obj"] = all_archive
    return result


def write_outputs(result):
    mode = result.get("queue_mode", "resource")
    if mode == "resource":
        out_json, out_md = OUT_JSON, OUT_MD
    else:
        out_json = os.path.join("outputs", "results", f"phase1_action_search_{mode}.json")
        out_md = os.path.join("outputs", "reports", f"phase1_action_search_{mode}.md")
    result["_out_json"] = out_json
    result["_out_md"] = out_md

    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    os.makedirs(os.path.dirname(out_md), exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    lines = [
        "# Phase1 Action Search",
        "",
        "Experimental 4F-9F action-level search. A* priority is used only for expansion order; pruning still uses real Pareto dimensions.",
        "",
        f"- elapsed: {result['elapsed']:.1f}s",
        f"- expansions: {result['expansions']}",
        f"- generated: {result['generated']}",
        f"- archive entries: {result['archive_entries']}",
        f"- goal entries: {result['goal_entries']}",
        f"- queue mode: {result.get('queue_mode', 'resource')}",
        f"- fixed exact count: {result['fixed_exact_count']}",
        f"- delayed shape count: {result['delayed_shape_count']}",
        "",
    ]
    if result["best_fixed_exact"]:
        e = result["best_fixed_exact"]
        lines.append(
            f"- best fixed exact: HP={e['hp']} ATK={e['atk']} DEF={e['def']} "
            f"YK={e['yk']} BK={e['bk']} RK={e['rk']} dmg={e['dmg']} door={e['yd']}/{e['bd']}/{e['rd']}"
        )
    else:
        lines.append("- best fixed exact: NOT FOUND")
    if result["best_delayed_shape"]:
        e = result["best_delayed_shape"]
        lines.append(
            f"- best delayed shape: HP={e['hp']} ATK={e['atk']} DEF={e['def']} "
            f"YK={e['yk']} BK={e['bk']} RK={e['rk']} dmg={e['dmg']} door={e['yd']}/{e['bd']}/{e['rd']}"
        )
    else:
        lines.append("- best delayed shape: NOT FOUND")
    lines.append("")
    lines.append("## Diagnostic Buckets")
    lines.append("")
    for name, data in result.get("buckets", {}).items():
        if name == "bd_bk_counts":
            continue
        best = data.get("best")
        if best:
            lines.append(
                f"- {name}: count={data['count']} best HP={best['hp']} ATK={best['atk']} "
                f"DEF={best['def']} YK={best['yk']} BK={best['bk']} RK={best['rk']} "
                f"dmg={best['dmg']} door={best['yd']}/{best['bd']}/{best['rd']}"
            )
        else:
            lines.append(f"- {name}: count={data['count']} best=NONE")
    if result.get("buckets", {}).get("bd_bk_counts"):
        counts = result["buckets"]["bd_bk_counts"]
        lines.append("- bd/bk counts: " + ", ".join(f"{k}={v}" for k, v in counts.items()))
    lines.extend([
        "",
        "| # | state | dmg | doors | depth | fixed | delayed | actions |",
        "|---:|---|---:|---:|---:|---|---|---|",
    ])
    for idx, e in enumerate(result["top"], 1):
        actions = " -> ".join(e["actions"])
        lines.append(
            f"| {idx} | HP={e['hp']} ATK={e['atk']} DEF={e['def']} "
            f"YK={e['yk']} BK={e['bk']} RK={e['rk']} | "
            f"{e['dmg']} | {e['yd']}/{e['bd']}/{e['rd']} | {e['depth']} | "
            f"{'Y' if e['fixed_exact'] else 'N'} | {'Y' if e['delayed_shape'] else 'N'} | {actions} |"
        )
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-expansions", type=int, default=220)
    parser.add_argument("--goal-limit", type=int, default=80)
    parser.add_argument("--queue-mode", choices=["resource", "dmg", "dual"], default="resource")
    args = parser.parse_args()
    result = run(max_expansions=args.max_expansions, goal_limit=args.goal_limit, queue_mode=args.queue_mode)
    write_outputs(result)
    print(
        f"elapsed={result['elapsed']:.1f}s expansions={result['expansions']} "
        f"goals={result['goal_entries']} fixed={result['fixed_exact_count']} "
        f"delayed={result['delayed_shape_count']}"
    )
    if result["top"]:
        best = result["top"][0]
        print(
            f"best HP={best['hp']} ATK={best['atk']} DEF={best['def']} "
            f"YK={best['yk']} BK={best['bk']} RK={best['rk']} "
            f"dmg={best['dmg']} door={best['yd']}/{best['bd']}/{best['rd']}"
        )
    print(f"wrote {result.get('_out_json', OUT_JSON)}")
    print(f"wrote {result.get('_out_md', OUT_MD)}")


if __name__ == "__main__":
    main()
