#!/usr/bin/env python3
"""Phase1 4F-9F action search with resource-group scheduling.

The original phase1_action_search.py is left untouched.  This experiment reuses
its real map mechanics, action generation, floor searches, and archive Pareto
filter, but expands entries through several priority queues so low-damage,
low-door, fixed-prefix, and delayed-resource branches can all get turns.
"""

from __future__ import annotations

import argparse
import heapq
import json
import os
import sys
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Callable


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.chdir(ROOT)

from src.solver import gen_walkthrough as gw
from src.solver.full_search import calc_dmg
from scripts import phase1_action_search as base


OUT_JSON = os.path.join("outputs", "results", "phase1_resource_group_search.json")
OUT_MD = os.path.join("outputs", "reports", "phase1_resource_group_search.md")

YK_VALUE = 50
BK_VALUE = 200
ATK_VALUE = 210
DEF_VALUE = 190
SWORD_VALUE = 900
SHIELD_VALUE = 1200


@dataclass(frozen=True)
class ResourceGroup:
    name: str
    fid: str
    items: tuple[tuple[int, int], ...] = ()
    doors: tuple[tuple[int, int], ...] = ()
    monsters: tuple[tuple[int, int], ...] = ()


def pos_eid(fid: str, pos: tuple[int, int]) -> str | None:
    for x, y, _t, eid in gw.maps[fid]["bl"]:
        if (x, y) == pos:
            return eid
    return None


def collected_for(ent: dict[str, Any], fid: str) -> set[tuple[int, int]]:
    got = set(ent.get("collected", {}).get(fid, frozenset()))
    got.update(gw.FLOOR_13_COLLECTED.get(fid, frozenset()))
    return got


RESOURCE_GROUPS: tuple[ResourceGroup, ...] = (
    ResourceGroup("4F left blue-key pocket", "MT4", items=((1, 2), (2, 1), (3, 2)), doors=((2, 4),), monsters=((2, 5),)),
    ResourceGroup("4F center red gem and keys", "MT4", items=((7, 10), (3, 11), (5, 10), (5, 11)), doors=((4, 8), (8, 8)), monsters=((4, 9), (9, 10))),
    ResourceGroup("4F right-top resources", "MT4", items=((9, 2), (11, 2)), doors=((10, 4),), monsters=((10, 3),)),
    ResourceGroup("5F sword pocket", "MT5", items=((11, 11),), doors=((11, 8),), monsters=((6, 8), (7, 6), (8, 9), (9, 11))),
    ResourceGroup("5F top-right keys", "MT5", items=((8, 3), (8, 4), (9, 3), (9, 4)), doors=((10, 1),), monsters=((11, 2),)),
    ResourceGroup("5F left keys", "MT5", items=((1, 5), (1, 6)), doors=((4, 4),), monsters=((4, 1), (4, 6), (3, 3), (2, 3))),
    ResourceGroup("5F blue gem pocket", "MT5", items=((1, 9), (2, 9), (3, 9)), monsters=((2, 7),)),
    ResourceGroup("6F lower route resources", "MT6", items=((6, 6),), doors=((7, 8), (8, 8), (10, 8)), monsters=((3, 6), (4, 6))),
    ResourceGroup("6F left key block", "MT6", items=((3, 1), (3, 2), (4, 1), (4, 2)), doors=((5, 4),), monsters=((4, 3),)),
    ResourceGroup("6F x9y1 yellow key", "MT6", items=((9, 1),), monsters=((7, 1),)),
    ResourceGroup("6F blue gem pocket", "MT6", items=((4, 9), (8, 11), (9, 11)), doors=((1, 10),), monsters=((5, 11), (2, 11), (2, 9))),
    ResourceGroup("7F delayed red gem", "MT7", items=((3, 1), (3, 2)), doors=((3, 5),), monsters=((3, 3), (2, 6))),
    ResourceGroup("7F left yellow keys", "MT7", items=((5, 10), (5, 11)), doors=((5, 7),), monsters=((5, 9),)),
    ResourceGroup("7F right key/potion block", "MT7", items=((9, 1), (9, 2), (9, 9), (9, 10), (9, 11)), monsters=((9, 3), (9, 5), (9, 7))),
    ResourceGroup("8F early up path keys", "MT8", items=((3, 4), (4, 4), (5, 4)), doors=((3, 1), (4, 1), (6, 3))),
    ResourceGroup("8F red/blue gem pocket", "MT8", items=((4, 10), (5, 10), (5, 11), (7, 10), (7, 11)), doors=((3, 11),), monsters=((4, 8), (6, 8), (7, 7), (7, 5))),
    ResourceGroup("8F red-key side resources", "MT8", items=((9, 1), (9, 3), (10, 2), (11, 1), (11, 3)), doors=((10, 7),), monsters=((8, 8), (9, 5), (11, 5))),
    ResourceGroup("9F shield and red/blue gems", "MT9", items=((9, 7), (6, 5), (1, 5)), doors=((8, 1), (9, 4), (8, 4)), monsters=((9, 1), (11, 1), (10, 5), (9, 7), (9, 4), (8, 4), (7, 4), (5, 4), (4, 5), (3, 5), (2, 4))),
    ResourceGroup("9F right-bottom resources", "MT9", items=((9, 9), (11, 11)), doors=((11, 8),), monsters=((11, 9),)),
)


def item_value(eid: str | None, ent: dict[str, Any]) -> int:
    if eid == "yellowKey":
        return YK_VALUE
    if eid == "blueKey":
        return BK_VALUE
    if eid == "redPotion":
        return 50
    if eid == "bluePotion":
        return 200
    if eid == "sword1":
        return SWORD_VALUE if not base.has_item(ent, "MT5", "sword1") else 0
    if eid == "shield1":
        return SHIELD_VALUE if not base.has_item(ent, "MT9", "shield1") else 0
    if eid == "redGem":
        return ATK_VALUE if ent["atk"] < 23 else 60
    if eid == "blueGem":
        return DEF_VALUE if ent["def"] < 21 else 50
    return 0


def door_cost(eid: str | None) -> int:
    if eid == "yellowDoor":
        return YK_VALUE
    if eid == "blueDoor":
        return BK_VALUE
    return 0


def group_value(group: ResourceGroup, ent: dict[str, Any]) -> tuple[int, str | None]:
    used = collected_for(ent, group.fid)
    reward = 0
    door = 0
    damage = 0
    left = []
    for pos in group.items:
        if pos in used:
            continue
        eid = pos_eid(group.fid, pos)
        val = item_value(eid, ent)
        reward += val
        if val:
            left.append(f"{pos}:{eid}")
    if reward <= 0:
        return 0, None
    for pos in group.doors:
        if pos not in used:
            door += door_cost(pos_eid(group.fid, pos))
    for pos in group.monsters:
        if pos not in used:
            eid = pos_eid(group.fid, pos)
            if eid:
                damage += calc_dmg(eid, ent["atk"], ent["def"])
    value = reward - door - damage
    if value <= 0:
        return 0, None
    return value, f"{group.name}: +{value} ({' '.join(left)})"


def residual_resource_value(ent: dict[str, Any]) -> tuple[int, list[str]]:
    total = 0
    notes = []
    for group in RESOURCE_GROUPS:
        value, note = group_value(group, ent)
        if value > 0:
            total += value
            if note:
                notes.append(note)
    return total, notes


def old_score(ent: dict[str, Any]) -> int:
    return (
        ent.get("_dmg", 0)
        + ent.get("_yd", 0) * YK_VALUE
        + ent.get("_bd", 0) * BK_VALUE
        - ent["hp"]
        - ent["yk"] * YK_VALUE
        - ent["bk"] * BK_VALUE
    )


def phase_penalty(ent: dict[str, Any]) -> int:
    penalty = 0
    if not base.has_item(ent, "MT5", "sword1"):
        penalty += 900
    if not base.has_item(ent, "MT9", "shield1"):
        penalty += 700
    if not base.has_item(ent, "MT9", "redGem"):
        penalty += 180
    if not base.has_item(ent, "MT9", "blueGem"):
        penalty += 180
    penalty += max(0, 9 - ent.get("_max_floor", 4)) * 120
    penalty += max(0, 21 - ent["atk"]) * 120
    penalty += max(0, 21 - ent["def"]) * 80
    penalty += max(0, 1 - ent["bk"]) * 100
    return penalty


def resource_group_score(ent: dict[str, Any]) -> int:
    residual, _notes = residual_resource_value(ent)
    return (
        ent.get("_dmg", 0)
        - ent["hp"]
        - ent["yk"] * YK_VALUE
        - ent["bk"] * BK_VALUE
        + phase_penalty(ent)
        - residual
    )


def score_key(ent: dict[str, Any]) -> tuple[int, int, int, int, int]:
    return (
        resource_group_score(ent),
        old_score(ent),
        ent.get("_dmg", 0),
        ent.get("_bd", 0),
        ent.get("_yd", 0),
    )


def delayed_red_key(ent: dict[str, Any]) -> tuple[int, int, int, int, int, int]:
    red_left = not base.has_item(ent, "MT7", "redGem")
    return (
        0 if red_left else 1,
        ent.get("_bd", 0),
        -ent["bk"],
        abs(ent["atk"] - 22),
        ent.get("_dmg", 0),
        ent.get("_yd", 0),
    )


def low_blue_door_key(ent: dict[str, Any]) -> tuple[int, int, int, int, int]:
    return (
        ent.get("_bd", 0),
        -ent["bk"],
        ent.get("_yd", 0),
        ent.get("_dmg", 0),
        -ent["hp"],
    )


def init_start() -> dict[str, Any]:
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
    return start


def push_all(heaps: list[tuple[str, Callable[[dict[str, Any]], tuple]]], stores, seq: int, ent: dict[str, Any]) -> None:
    for idx, (_name, key_fn) in enumerate(heaps):
        heapq.heappush(stores[idx], (key_fn(ent), seq, ent))


def pop_next(stores, order: list[int], expanded_ids: set[int]) -> dict[str, Any] | None:
    for idx in order:
        heap = stores[idx]
        while heap:
            _key, _seq, ent = heapq.heappop(heap)
            if ent["_id"] not in expanded_ids:
                return ent
    return None


def unique_rows(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    best = {}
    for ent in entries:
        key = (
            ent["hp"], ent["atk"], ent["def"], ent["yk"], ent["bk"], ent["rk"],
            ent.get("_dmg", 0), ent.get("_yd", 0), ent.get("_bd", 0), ent.get("_rd", 0),
            base.has_item(ent, "MT7", "redGem"),
        )
        prev = best.get(key)
        if prev is None or score_key(ent) < score_key(prev):
            best[key] = ent
    return list(best.values())


def compact(ent: dict[str, Any]) -> dict[str, Any]:
    residual, notes = residual_resource_value(ent)
    rec = base.result_record(ent)
    rec.update({
        "old_score": old_score(ent),
        "resource_group_score": resource_group_score(ent),
        "residual_value": residual,
        "residual_notes": notes[:5],
        "mt7_red_left": not base.has_item(ent, "MT7", "redGem"),
    })
    return rec


def row_key(row: dict[str, Any]) -> tuple[int, ...]:
    return (
        row["hp"], row["atk"], row["def"], row["yk"], row["bk"], row["rk"],
        row["dmg"], row["yd"], row["bd"], row["rd"], int(row["mt7_red_left"]),
    )


def dominates(a: dict[str, Any], b: dict[str, Any]) -> bool:
    if not (
        a["dmg"] <= b["dmg"]
        and a["yd"] <= b["yd"]
        and a["bd"] <= b["bd"]
        and a["rd"] <= b["rd"]
        and a["atk"] >= b["atk"]
        and a["def"] >= b["def"]
        and a["yk"] >= b["yk"]
        and a["bk"] >= b["bk"]
        and a["rk"] >= b["rk"]
    ):
        return False
    strict = (
        a["dmg"] < b["dmg"]
        or a["yd"] < b["yd"]
        or a["bd"] < b["bd"]
        or a["rd"] < b["rd"]
        or a["atk"] > b["atk"]
        or a["def"] > b["def"]
        or a["yk"] > b["yk"]
        or a["bk"] > b["bk"]
        or a["rk"] > b["rk"]
    )
    same_core = (
        a["dmg"] == b["dmg"]
        and a["yd"] == b["yd"]
        and a["bd"] == b["bd"]
        and a["rd"] == b["rd"]
        and a["atk"] == b["atk"]
        and a["def"] == b["def"]
        and a["yk"] == b["yk"]
        and a["bk"] == b["bk"]
        and a["rk"] == b["rk"]
    )
    return strict or (same_core and a["hp"] >= b["hp"] and row_key(a) != row_key(b))


def pareto_front(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if not any(dominates(other, row) for other in rows)]


def rank_map(rows: list[dict[str, Any]], name: str) -> dict[tuple[int, ...], int]:
    if name == "old":
        ranked = sorted(rows, key=lambda r: (r["old_score"], r["resource_group_score"], r["dmg"], r["bd"], r["yd"], -r["hp"]))
    elif name == "new":
        ranked = sorted(rows, key=lambda r: (r["resource_group_score"], r["old_score"], r["dmg"], r["bd"], r["yd"], -r["hp"]))
    else:
        raise ValueError(name)
    return {row_key(row): idx for idx, row in enumerate(ranked, 1)}


def run_multi_queue(max_expansions: int = 380) -> dict[str, Any]:
    start = init_start()
    archive = defaultdict(list)
    base.add_to_archive(archive, start)

    heaps = [
        ("resource_group", score_key),
        ("legacy_resource", base.priority),
        ("legacy_dmg", base.dmg_first_priority),
        ("low_blue_door", low_blue_door_key),
        ("delayed_red", delayed_red_key),
        ("high_hp", lambda e: (-e["hp"], e.get("_dmg", 0), e.get("_yd", 0), e.get("_bd", 0))),
    ]
    stores = [[] for _ in heaps]
    seq = 0
    push_all(heaps, stores, seq, start)
    expanded_ids = set()
    goals = []
    goal_seen = set()
    generated = 0
    t0 = time.time()
    # This pattern intentionally gives every objective regular turns.
    queue_pattern = [0, 2, 3, 4, 1, 0, 2, 5]

    for expansion in range(max_expansions):
        order = list(range(len(heaps)))
        first = queue_pattern[expansion % len(queue_pattern)]
        order = [first] + [idx for idx in order if idx != first]
        ent = pop_next(stores, order, expanded_ids)
        if ent is None:
            break
        expanded_ids.add(ent["_id"])
        if base.is_goal(ent) and ent["_id"] not in goal_seen:
            goal_seen.add(ent["_id"])
            goals.append(ent)
        if ent.get("_action_depth", 0) >= 14:
            continue
        for action in base.possible_actions(ent):
            for child in base.expand_action(ent, action):
                generated += 1
                if not base.add_to_archive(archive, child):
                    continue
                seq += 1
                push_all(heaps, stores, seq, child)
        if (expansion + 1) % 50 == 0:
            print(
                f"expanded={expansion + 1} heap={sum(len(h) for h in stores)} goals={len(goals)} "
                f"entry={base.metric_text(ent)} rg={resource_group_score(ent)}",
                flush=True,
            )

    all_archive = [e for items in archive.values() for e in items]
    goal_entries = goals + [e for e in all_archive if base.is_goal(e)]
    unique_entries = unique_rows(goal_entries)
    rows = [compact(e) for e in unique_entries]
    front = pareto_front(rows)
    old_ranks = rank_map(front, "old")
    new_ranks = rank_map(front, "new")
    for row in front:
        key = row_key(row)
        row["old_rank"] = old_ranks[key]
        row["new_rank"] = new_ranks[key]

    fixed_matches = [e for e in goal_entries if base.fixed_exact_match(e)]
    delayed_matches = [e for e in goal_entries if base.delayed_shape_match(e)]
    delayed_red_left = [
        e for e in goal_entries
        if e["atk"] == 22 and e["def"] == 21 and e["yk"] >= 2 and e["bk"] >= 1
        and e.get("_bd", 0) == 0 and not base.has_item(e, "MT7", "redGem")
    ]

    top_new = sorted(front, key=lambda r: (r["resource_group_score"], r["old_score"], r["dmg"], r["bd"], r["yd"], -r["hp"]))[:10]
    top_old = sorted(front, key=lambda r: (r["old_score"], r["resource_group_score"], r["dmg"], r["bd"], r["yd"], -r["hp"]))[:10]
    return {
        "scheduler": "multi_queue",
        "elapsed": time.time() - t0,
        "max_expansions": max_expansions,
        "generated": generated,
        "archive_entries": len(all_archive),
        "raw_goal_count": len(goal_entries),
        "unique_goal_count": len(unique_entries),
        "pareto_count": len(front),
        "fixed_exact_count": len(fixed_matches),
        "delayed_shape_count": len(delayed_matches),
        "delayed_red_left_count": len(delayed_red_left),
        "best_fixed_exact": compact(sorted(fixed_matches, key=lambda e: (e.get("_dmg", 0), e.get("_yd", 0), -e["hp"]))[0]) if fixed_matches else None,
        "best_delayed_shape": compact(sorted(delayed_matches, key=lambda e: (e.get("_dmg", 0), e.get("_yd", 0), -e["hp"]))[0]) if delayed_matches else None,
        "best_delayed_red_left": compact(sorted(delayed_red_left, key=lambda e: (e.get("_dmg", 0), e.get("_yd", 0), -e["hp"]))[0]) if delayed_red_left else None,
        "top_by_resource_group": top_new,
        "top_by_old": top_old,
    }


def rows_from_goal_entries(entries: list[dict[str, Any]], source_queue: str) -> list[dict[str, Any]]:
    rows = []
    for ent in entries:
        row = compact(ent)
        row["source_queue"] = source_queue
        rows.append(row)
    return rows


def unique_compact_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    best = {}
    for row in rows:
        key = row_key(row)
        prev = best.get(key)
        if prev is None:
            best[key] = row
            continue
        prev_key = (
            prev["resource_group_score"], prev["old_score"], prev["dmg"],
            prev["bd"], prev["yd"], -prev["hp"],
        )
        row_score_key = (
            row["resource_group_score"], row["old_score"], row["dmg"],
            row["bd"], row["yd"], -row["hp"],
        )
        if row_score_key < prev_key:
            best[key] = row
    return list(best.values())


def finish_rows(
    rows: list[dict[str, Any]],
    elapsed: float,
    max_expansions: int,
    generated: int,
    archive_entries: int,
    raw_goal_count: int,
    scheduler: str,
    lane_summaries: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    unique = unique_compact_rows(rows)
    front = pareto_front(unique)
    old_ranks = rank_map(front, "old")
    new_ranks = rank_map(front, "new")
    for row in front:
        key = row_key(row)
        row["old_rank"] = old_ranks[key]
        row["new_rank"] = new_ranks[key]

    fixed_matches = [row for row in rows if row["fixed_exact"]]
    delayed_matches = [row for row in rows if row["delayed_shape"]]
    delayed_red_left = [
        row for row in rows
        if row["atk"] == 22 and row["def"] == 21 and row["yk"] >= 2 and row["bk"] >= 1
        and row["bd"] == 0 and row["mt7_red_left"]
    ]
    top_new = sorted(front, key=lambda r: (r["resource_group_score"], r["old_score"], r["dmg"], r["bd"], r["yd"], -r["hp"]))[:10]
    top_old = sorted(front, key=lambda r: (r["old_score"], r["resource_group_score"], r["dmg"], r["bd"], r["yd"], -r["hp"]))[:10]
    return {
        "scheduler": scheduler,
        "lane_summaries": lane_summaries or [],
        "elapsed": elapsed,
        "max_expansions": max_expansions,
        "generated": generated,
        "archive_entries": archive_entries,
        "raw_goal_count": raw_goal_count,
        "unique_goal_count": len(unique),
        "pareto_count": len(front),
        "fixed_exact_count": len(fixed_matches),
        "delayed_shape_count": len(delayed_matches),
        "delayed_red_left_count": len(delayed_red_left),
        "best_fixed_exact": sorted(fixed_matches, key=lambda r: (r["dmg"], r["yd"], r["bd"], -r["hp"]))[0] if fixed_matches else None,
        "best_delayed_shape": sorted(delayed_matches, key=lambda r: (r["dmg"], r["yd"], r["bd"], -r["hp"]))[0] if delayed_matches else None,
        "best_delayed_red_left": sorted(delayed_red_left, key=lambda r: (r["dmg"], r["yd"], r["bd"], -r["hp"]))[0] if delayed_red_left else None,
        "top_by_resource_group": top_new,
        "top_by_old": top_old,
    }


def run_lanes(max_expansions: int = 300, queue_modes: tuple[str, ...] = ("resource", "dmg")) -> dict[str, Any]:
    t0 = time.time()
    rows: list[dict[str, Any]] = []
    generated = 0
    archive_entries = 0
    raw_goal_count = 0
    lane_summaries = []
    for mode in queue_modes:
        lane = base.run(
            max_expansions=max_expansions,
            include_entries=True,
            queue_mode=mode,
        )
        entries = lane.get("_goal_entries", [])
        rows.extend(rows_from_goal_entries(entries, mode))
        generated += lane.get("generated", 0)
        archive_entries += lane.get("archive_entries", 0)
        raw_goal_count += len(entries)
        lane_summaries.append({
            "queue_mode": mode,
            "elapsed": lane.get("elapsed", 0),
            "generated": lane.get("generated", 0),
            "archive_entries": lane.get("archive_entries", 0),
            "goal_entries": len(entries),
            "fixed_exact_count": lane.get("fixed_exact_count", 0),
            "delayed_shape_count": lane.get("delayed_shape_count", 0),
        })
    return finish_rows(
        rows=rows,
        elapsed=time.time() - t0,
        max_expansions=max_expansions,
        generated=generated,
        archive_entries=archive_entries,
        raw_goal_count=raw_goal_count,
        scheduler="lanes:" + ",".join(queue_modes),
        lane_summaries=lane_summaries,
    )


def state_text(row: dict[str, Any]) -> str:
    return (
        f"HP={row['hp']} ATK={row['atk']} DEF={row['def']} "
        f"YK={row['yk']} BK={row['bk']} RK={row['rk']} "
        f"dmg={row['dmg']} door={row['yd']}/{row['bd']}/{row['rd']}"
    )


def write_report(data: dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    lines = [
        "# Phase1 Resource Group Search",
        "",
        "Experimental 4F-9F search. Legacy action search is untouched; this run only changes outer scheduling and ranking.",
        "",
        "- old_score = `dmg + yd*50 + bd*200 - hp - yk*50 - bk*200`",
        "- resource_group_score = `dmg - hp - yk*50 - bk*200 + phase_penalty - residual_group_value`",
        f"- elapsed: {data['elapsed']:.1f}s",
        f"- scheduler: {data.get('scheduler', 'multi_queue')}",
        f"- max expansions: {data['max_expansions']}",
        f"- generated: {data['generated']}",
        f"- archive entries: {data['archive_entries']}",
        f"- raw goals: {data['raw_goal_count']}",
        f"- unique goals: {data['unique_goal_count']}",
        f"- pareto front: {data['pareto_count']}",
        f"- fixed exact count: {data['fixed_exact_count']}",
        f"- delayed shape count: {data['delayed_shape_count']}",
        f"- delayed red-left count: {data['delayed_red_left_count']}",
        "",
    ]
    if data.get("lane_summaries"):
        lines.extend([
            "",
            "## Lane Summaries",
            "",
            "| queue | elapsed | goals | fixed | delayed | generated | archive |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ])
        for lane in data["lane_summaries"]:
            lines.append(
                f"| {lane['queue_mode']} | {lane['elapsed']:.1f}s | {lane['goal_entries']} | "
                f"{lane['fixed_exact_count']} | {lane['delayed_shape_count']} | "
                f"{lane['generated']} | {lane['archive_entries']} |"
            )
        lines.append("")
    for label, key in [
        ("best fixed exact", "best_fixed_exact"),
        ("best delayed shape", "best_delayed_shape"),
        ("best delayed red-left", "best_delayed_red_left"),
    ]:
        row = data.get(key)
        if row:
            lines.append(f"- {label}: {state_text(row)} rg={row['resource_group_score']} old={row['old_score']}")
        else:
            lines.append(f"- {label}: NOT FOUND")
    lines.extend([
        "",
        "## Top 10 By Resource Group Score After Pareto Filter",
        "",
        "| # | newRank | oldRank | rgScore | oldScore | residual | src | redLeft | state |",
        "|---:|---:|---:|---:|---:|---:|---|---|---|",
    ])
    for idx, row in enumerate(data["top_by_resource_group"], 1):
        lines.append(
            f"| {idx} | {row['new_rank']} | {row['old_rank']} | {row['resource_group_score']} | "
            f"{row['old_score']} | {row['residual_value']} | {row.get('source_queue', '-')} | "
            f"{'Y' if row['mt7_red_left'] else 'N'} | {state_text(row)} |"
        )
    lines.extend([
        "",
        "## Top 10 By Old Score After Pareto Filter",
        "",
        "| # | oldRank | newRank | oldScore | rgScore | residual | src | redLeft | state |",
        "|---:|---:|---:|---:|---:|---:|---|---|---|",
    ])
    for idx, row in enumerate(data["top_by_old"], 1):
        lines.append(
            f"| {idx} | {row['old_rank']} | {row['new_rank']} | {row['old_score']} | "
            f"{row['resource_group_score']} | {row['residual_value']} | {row.get('source_queue', '-')} | "
            f"{'Y' if row['mt7_red_left'] else 'N'} | {state_text(row)} |"
        )
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-expansions", type=int, default=300)
    parser.add_argument("--scheduler", choices=["lanes", "multi"], default="lanes")
    parser.add_argument("--queue-modes", default="resource,dmg")
    args = parser.parse_args()
    if args.scheduler == "multi":
        data = run_multi_queue(args.max_expansions)
    else:
        modes = tuple(m.strip() for m in args.queue_modes.split(",") if m.strip())
        data = run_lanes(args.max_expansions, modes)
    write_report(data)
    print(
        f"elapsed={data['elapsed']:.1f}s goals={data['raw_goal_count']} unique={data['unique_goal_count']} "
        f"pareto={data['pareto_count']} fixed={data['fixed_exact_count']} delayed={data['delayed_shape_count']}"
    )
    best = data["top_by_resource_group"][0] if data["top_by_resource_group"] else None
    if best:
        print(
            f"best HP={best['hp']} ATK={best['atk']} DEF={best['def']} YK={best['yk']} BK={best['bk']} "
            f"dmg={best['dmg']} door={best['yd']}/{best['bd']}/{best['rd']} rg={best['resource_group_score']}"
        )
    print(f"wrote {OUT_JSON}")
    print(f"wrote {OUT_MD}")


if __name__ == "__main__":
    main()
