#!/usr/bin/env python3
"""Search post-9 continuation with compressed resource-group edges.

This prototype starts from the delayed 9F red/blue gem prefix.  It differs from
the atomic Dijkstra experiment by treating a zero-cost connected resource pocket
as one high-level node: a floor path only pays the cost up to the first resource
in the pocket, then all resources reachable from that resource without crossing
a fresh door or monster are collected together.
"""

from __future__ import annotations

import argparse
import heapq
import json
import os
import sys
import time
from collections import defaultdict
from typing import Any, Iterable


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.chdir(ROOT)

from scripts import continue_delayed_phase1_with_post9_resource as delayed
from scripts import gen_delayed_phase1_detailed_walk as detail_walk
from scripts import post9_action_search as p9
from scripts import post9_atomic_resource_dijkstra as atomic
from scripts import post9_auto_resource_group_pareto as auto
from scripts import post9_resource_group_search as rg
from scripts import report_post9_atomic_resource_graph as graph
from scripts import report_post9_compressed_resource_topology as topo
from src.solver.full_search import calc_dmg
from src.solver import gen_walkthrough as gw


OUT_JSON = os.path.join("outputs", "results", "post9_compressed_resource_dijkstra.json")
OUT_MD = os.path.join("outputs", "reports", "post9_compressed_resource_dijkstra.md")
OUT_WALK = os.path.join("outputs", "walkthroughs", "walkthrough_post9_compressed_resource_dijkstra_best.md")
OUT_WALK_DETAIL = os.path.join("outputs", "walkthroughs", "walkthrough_post9_compressed_resource_dijkstra_best_detailed.md")

RESOURCE_IDS = {
    "redGem",
    "blueGem",
    "yellowKey",
    "blueKey",
    "redKey",
    "redPotion",
    "bluePotion",
}

DYNAMIC_VALUE_CAP = 1600
MONSTER_SAVE_CAP = 220
MAJOR_VIA_IDS = {"redGem", "blueGem", "redKey", "upFloor", "redDoor"}


def finite_damage(eid: str, atk: int, def_: int) -> int:
    dmg = calc_dmg(eid, atk, def_)
    if dmg == float("inf"):
        return 10000
    return int(dmg)


def remaining_monster_eids(ent: dict[str, Any]) -> list[str]:
    monsters: list[str] = []
    for fid, data in gw.maps.items():
        collected = auto.collected_for(ent, fid)
        for x, y, t, eid in data["bl"]:
            if t == 1 and (x, y) not in collected:
                monsters.append(eid)
    return monsters


def damage_saving_for_stats(base: dict[str, Any], after: dict[str, Any], atk: int, def_: int) -> int:
    total = 0
    for eid in remaining_monster_eids(after):
        before = finite_damage(eid, base["atk"], base["def"])
        new = finite_damage(eid, atk, def_)
        if before <= new:
            continue
        total += min(MONSTER_SAVE_CAP, before - new)
        if total >= DYNAMIC_VALUE_CAP:
            return DYNAMIC_VALUE_CAP
    return total


def attack_threshold_bonus(base: dict[str, Any], after: dict[str, Any], atk: int) -> int:
    bonus = 0
    for eid in set(remaining_monster_eids(after)):
        before = finite_damage(eid, base["atk"], base["def"])
        new = finite_damage(eid, atk, base["def"])
        if before >= 10000 and new < 10000:
            bonus += 260
    return min(500, bonus)


def future_damage_saving(base: dict[str, Any], after: dict[str, Any]) -> int:
    """Estimate how much the stat delta helps on monsters still alive after edge.

    This is a queue heuristic only.  It deliberately does not participate in
    Pareto dominance, because the value of a gem depends on later route choices.
    """
    atk_delta = max(0, after["atk"] - base["atk"])
    def_delta = max(0, after["def"] - base["def"])
    if atk_delta == 0 and def_delta == 0:
        return 0
    def_saving = 0
    if def_delta:
        def_saving = damage_saving_for_stats(base, after, base["atk"], base["def"] + def_delta)
    atk_saving = 0
    if atk_delta:
        atk_saving = damage_saving_for_stats(base, after, base["atk"] + atk_delta, base["def"])
    combo = damage_saving_for_stats(base, after, after["atk"], after["def"])
    synergy = max(0, combo - def_saving - atk_saving)
    atk_bonus = attack_threshold_bonus(base, after, base["atk"] + atk_delta) if atk_delta else 0
    atk_weight = 0.6 if atk_bonus or atk_saving >= 700 else 0.1
    total = int(def_saving * 1.2 + atk_saving * atk_weight + synergy * 0.5 + atk_bonus)
    if after["def"] > base["def"]:
        total += 25 * (after["def"] - base["def"])
    if after["atk"] > base["atk"]:
        total += 10 * (after["atk"] - base["atk"])
    return min(DYNAMIC_VALUE_CAP, total)


def ensure_delta_fields(base: dict[str, Any], edge: dict[str, Any]) -> None:
    fields = {
        "_delta_hp": edge["hp"] - base["hp"],
        "_delta_dmg": edge.get("_dmg", 0) - base.get("_dmg", 0),
        "_delta_yd": edge.get("_yd", 0) - base.get("_yd", 0),
        "_delta_bd": edge.get("_bd", 0) - base.get("_bd", 0),
        "_delta_rd": edge.get("_rd", 0) - base.get("_rd", 0),
        "_delta_yk": edge["yk"] - base["yk"],
        "_delta_bk": edge["bk"] - base["bk"],
        "_delta_rk": edge["rk"] - base["rk"],
        "_delta_atk": edge["atk"] - base["atk"],
        "_delta_def": edge["def"] - base["def"],
    }
    for key, value in fields.items():
        edge.setdefault(key, value)


def dynamic_transition_value(base: dict[str, Any], edge: dict[str, Any]) -> int:
    stat_value = future_damage_saving(base, edge)
    key_value = (
        max(0, edge.get("_delta_yk", 0)) * rg.YK_VALUE
        + max(0, edge.get("_delta_bk", 0)) * rg.BK_VALUE
        + max(0, edge.get("_delta_rk", 0)) * rg.RED_KEY_VALUE
    )
    potion_value = int(max(0, edge.get("_delta_hp", 0)) * 0.35)
    progress_value = 0
    if edge.get("_edge_kind") == "progress" and "MT10" not in base.get("collected", {}):
        progress_value = 120
    return min(DYNAMIC_VALUE_CAP, stat_value + key_value + potion_value + progress_value)


def dynamic_transition_cost(edge: dict[str, Any]) -> int:
    return (
        max(0, edge.get("_delta_dmg", 0))
        + max(0, edge.get("_delta_yd", 0)) * rg.YK_VALUE
        + max(0, edge.get("_delta_bd", 0)) * rg.BK_VALUE
        + max(0, edge.get("_delta_rd", 0)) * rg.RED_KEY_VALUE
    )


def annotate_dynamic(base: dict[str, Any], edge: dict[str, Any]) -> None:
    ensure_delta_fields(base, edge)
    cost = dynamic_transition_cost(edge)
    value = dynamic_transition_value(base, edge)
    if cost == 0 and (
        edge.get("_delta_hp", 0) > 0
        or edge.get("_delta_yk", 0) > 0
        or edge.get("_delta_bk", 0) > 0
        or edge.get("_delta_atk", 0) > 0
        or edge.get("_delta_def", 0) > 0
    ):
        value = min(DYNAMIC_VALUE_CAP, value + 1500)
    edge["_dynamic_value"] = value
    edge["_dynamic_cost"] = cost
    edge["_dynamic_net"] = value - cost
    edge["_dynamic_efficiency"] = (edge["_dynamic_net"] * 100) // (cost + 50)
    edge["_dynamic_total"] = base.get("_dynamic_total", 0) + value


def major_code(edge: dict[str, Any]) -> str:
    via = sorted(set(edge.get("_via_targets", [])) & MAJOR_VIA_IDS)
    if not via:
        return ""
    fid = edge.get("_edge_fid")
    if not fid:
        step = edge.get("_step_info")
        if step:
            fid = step[0]
    return f"{fid or '?'}:{'+'.join(via)}"


def annotate_major_order(base: dict[str, Any], edge: dict[str, Any]) -> None:
    order = list(base.get("_major_order", ()))
    code = major_code(edge)
    if code and (not order or order[-1] != code):
        order.append(code)
    edge["_major_order"] = tuple(order[:8])


def lane_key(ent: dict[str, Any]) -> tuple[Any, ...]:
    """Coarse lane key for fair expansion of different resource orders."""
    order = tuple(ent.get("_major_order", ())[:4])
    return (
        auto.label_stage(ent),
        p9.stat_deficit(ent) // 3,
        order,
    )


def lane_priority(ent: dict[str, Any]) -> tuple[int, ...]:
    """Prefer a cheap representative from each order lane.

    The main heap follows the aggregate resource score.  This side queue keeps
    low immediate-cost alternatives moving so a large resource pocket cannot
    hide a slightly better ordering of smaller pockets.
    """
    stat_deficit = p9.stat_deficit(ent)
    return (
        0 if stat_deficit > 0 else 1,
        stat_deficit // 4 if stat_deficit > 0 else auto.label_stage(ent),
        0 if ent.get("_dynamic_cost", 0) == 0 else 1,
        ent.get("_dynamic_cost", 0),
        ent.get("_dmg", 0),
        ent.get("_yd", 0),
        ent.get("_bd", 0),
        -ent["hp"],
        -ent["yk"],
        -ent["bk"],
    )


def state_text(ent: dict[str, Any]) -> str:
    return atomic.state_text(ent)


def add_item_to_state(hp: int, yk: int, bk: int, rk: int, atk: int, def_: int, eid: str) -> tuple[int, int, int, int, int, int]:
    if eid == "yellowKey":
        yk += 1
    elif eid == "blueKey":
        bk += 1
    elif eid == "redKey":
        rk += 1
    elif eid == "redPotion":
        hp += 50
    elif eid == "bluePotion":
        hp += 200
    elif eid == "redGem":
        atk += 1
    elif eid == "blueGem":
        def_ += 1
    return hp, yk, bk, rk, atk, def_


def group_label(fid: str, items: list[topo.ResourceItem]) -> str:
    return f"{fid} " + "+".join(topo.item_label(item) for item in sorted(items, key=lambda it: it.pos))


def group_via_targets(items: list[topo.ResourceItem]) -> list[str]:
    return sorted({item.eid for item in items})


def store_metadata(ent: dict[str, Any], keys: Iterable[str]) -> None:
    store = gw._entry_store[ent["_id"]]
    for key in keys:
        store[key] = ent[key]


def describe_group(fid: str, before: frozenset[tuple[int, int]], consumed: set[tuple[int, int]]) -> dict[str, Any]:
    items = []
    doors = []
    monsters = []
    for x, y, t, eid in gw.maps[fid]["bl"]:
        pos = (x, y)
        if pos not in consumed or pos in before:
            continue
        rec = {"pos": f"x{x}y{y}", "eid": eid, "name": auto.ITEM_CN.get(eid, eid)}
        if t == 3 and eid in RESOURCE_IDS:
            items.append(rec)
        elif t == 2:
            doors.append(rec)
        elif t == 1:
            monsters.append(rec)
    return {"items": items, "doors": doors, "monsters": monsters}


def make_compressed_edge(
    base: dict[str, Any],
    full_edge: dict[str, Any],
    max_iter: int,
) -> dict[str, Any] | None:
    fid, targets, flyback = full_edge.get("_step_info", (None, [], True))
    if not fid:
        return None
    if full_edge.get("_edge_kind") in {"boss", "progress"}:
        full_edge["_edge_fid"] = fid
        if full_edge.get("_edge_kind") == "progress":
            full_edge.setdefault("_via_targets", ["upFloor"])
        elif full_edge.get("_edge_kind") == "boss":
            full_edge.setdefault("_via_targets", ["redDoor"])
        annotate_dynamic(base, full_edge)
        annotate_major_order(base, full_edge)
        store_metadata(
            full_edge,
            (
                "_edge_fid",
                "_via_targets",
                "_delta_hp",
                "_delta_dmg",
                "_delta_yd",
                "_delta_bd",
                "_delta_rd",
                "_delta_yk",
                "_delta_bk",
                "_delta_rk",
                "_delta_atk",
                "_delta_def",
                "_dynamic_value",
                "_dynamic_cost",
                "_dynamic_net",
                "_dynamic_efficiency",
                "_dynamic_total",
                "_major_order",
            ),
        )
        return full_edge

    steps, _final, mismatch = graph.reconstruct_steps(base, full_edge, fid, targets, flyback, max_iter=max_iter)
    if not steps or mismatch:
        return None

    first_idx = topo.find_first_resource(fid, steps)
    if first_idx is None:
        return None
    first = steps[first_idx]
    first_pos = (first["x"], first["y"])
    first_t, first_eid = topo.step_kind(fid, first)
    if first_t != 3 or first_eid not in RESOURCE_IDS:
        return None

    prefix = topo.prefix_records(fid, steps, first_idx)
    group_items = topo.zero_cost_group(base, fid, first_pos, prefix["consumed"])
    if not group_items:
        return None

    before = auto.collected_for(base, fid)
    group_positions = {item.pos for item in group_items}
    consumed = set(prefix["consumed"]) | group_positions
    free_items = [item for item in group_items if item.pos not in prefix["consumed"] and item.pos not in before]

    hp = first["hp_after"]
    yk = first["yk"]
    bk = first["bk"]
    rk = first["rk"]
    atk = first["atk"]
    def_ = first["def"]
    for item in free_items:
        hp, yk, bk, rk, atk, def_ = add_item_to_state(hp, yk, bk, rk, atk, def_, item.eid)

    nc = dict(base.get("collected", {}))
    nc[fid] = before | frozenset(consumed)
    edge = gw._make_result(
        hp,
        yk,
        bk,
        rk,
        atk,
        def_,
        nc,
        base["_id"],
        (fid, [first_eid], flyback),
        dmg_cost=prefix["dmg"],
    )
    desc = describe_group(fid, before, consumed)
    edge["_last_action"] = f"{group_label(fid, group_items)} flyback={flyback}"
    edge["_edge_fid"] = fid
    edge["_resource_group"] = desc
    edge["_via_targets"] = group_via_targets(group_items)
    if rk > base["rk"] or any(item.eid == "redKey" for item in group_items):
        edge["_edge_kind"] = "redkey"
    elif atk > base["atk"] or def_ > base["def"]:
        edge["_edge_kind"] = "stat"
    elif yk > base["yk"] or bk > base["bk"]:
        edge["_edge_kind"] = "key"
    elif hp > base["hp"]:
        edge["_edge_kind"] = "potion"
    else:
        edge["_edge_kind"] = "other"

    edge["_delta_hp"] = hp - base["hp"]
    edge["_delta_dmg"] = edge.get("_dmg", 0) - base.get("_dmg", 0)
    edge["_delta_yd"] = edge.get("_yd", 0) - base.get("_yd", 0)
    edge["_delta_bd"] = edge.get("_bd", 0) - base.get("_bd", 0)
    edge["_delta_rd"] = edge.get("_rd", 0) - base.get("_rd", 0)
    edge["_delta_yk"] = yk - base["yk"]
    edge["_delta_bk"] = bk - base["bk"]
    edge["_delta_rk"] = rk - base["rk"]
    edge["_delta_atk"] = atk - base["atk"]
    edge["_delta_def"] = def_ - base["def"]
    annotate_dynamic(base, edge)
    annotate_major_order(base, edge)
    store_metadata(
        edge,
        (
            "_last_action",
            "_edge_fid",
            "_resource_group",
            "_via_targets",
            "_edge_kind",
            "_delta_hp",
            "_delta_dmg",
            "_delta_yd",
            "_delta_bd",
            "_delta_rd",
            "_delta_yk",
            "_delta_bk",
            "_delta_rk",
            "_delta_atk",
            "_delta_def",
            "_dynamic_value",
            "_dynamic_cost",
            "_dynamic_net",
            "_dynamic_efficiency",
            "_dynamic_total",
            "_major_order",
        ),
    )
    return edge


def route_edges(ent: dict[str, Any], max_targets: int, max_iter: int) -> list[dict[str, Any]]:
    by_floor_eid: dict[tuple[str, str], set[tuple[int, int]]] = defaultdict(set)
    for target in atomic.stage_candidate_targets(ent, max_targets):
        by_floor_eid[(target.fid, target.eid)].add(target.pos)

    edges: list[dict[str, Any]] = []
    for (fid, eid), positions in sorted(by_floor_eid.items(), key=lambda item: (int(item[0][0][2:]), item[0][1])):
        edges.extend(auto.exact_item_edges(ent, fid, eid, positions, max_iter=max_iter))
    if atomic.mt10_progress_allowed(ent):
        edges.extend(auto.progress_edges(ent, max_iter=max_iter))
    edges.extend(auto.boss_edges(ent))
    return edges


def edge_sort_key(ent: dict[str, Any], mode: str = "stage") -> tuple[int, ...]:
    if mode != "dynamic":
        return atomic.edge_sort_key(ent)
    kind_order = {
        "boss": 0,
        "redkey": 1,
        "progress": 2,
        "stat": 3,
        "key": 4,
        "potion": 5,
        "other": 6,
    }.get(ent.get("_edge_kind"), 6)
    return (
        0 if p9.goal(ent) else 1,
        kind_order,
        -ent.get("_dynamic_net", 0),
        -ent.get("_dynamic_efficiency", 0),
        ent.get("_dynamic_cost", 0),
        p9.stat_deficit(ent),
        rg.resource_group_score(ent),
        ent.get("_dmg", 0),
        ent.get("_yd", 0),
        ent.get("_bd", 0),
        -ent["hp"],
        -ent["yk"],
        -ent["bk"],
    )


def generate_compressed_edges(
    ent: dict[str, Any],
    max_targets: int,
    max_iter: int,
    edge_limit: int,
    priority_mode: str,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for full in route_edges(ent, max_targets=max_targets, max_iter=max_iter):
        edge = make_compressed_edge(ent, full, max_iter=max_iter)
        if edge:
            out.append(edge)

    dedup: dict[tuple[Any, ...], dict[str, Any]] = {}
    via_merge: dict[tuple[Any, ...], set[str]] = defaultdict(set)
    for edge in out:
        sig = auto.result_signature(edge)
        via_merge[sig].update(edge.get("_via_targets", []))
        old = dedup.get(sig)
        if old is None or edge_sort_key(edge, priority_mode) < edge_sort_key(old, priority_mode):
            dedup[sig] = edge

    for sig, edge in dedup.items():
        via = sorted(via_merge.get(sig, set(edge.get("_via_targets", []))))
        edge["_via_targets"] = via
        gw._entry_store[edge["_id"]]["_via_targets"] = via

    ranked = sorted(dedup.values(), key=lambda edge: edge_sort_key(edge, priority_mode))
    if edge_limit <= 0 or len(ranked) <= edge_limit:
        return ranked

    chosen: list[dict[str, Any]] = []
    seen: set[int] = set()

    def add(items: Iterable[dict[str, Any]], quota: int) -> None:
        added = 0
        for edge in items:
            if edge["_id"] in seen:
                continue
            seen.add(edge["_id"])
            chosen.append(edge)
            added += 1
            if added >= quota or len(chosen) >= edge_limit:
                return

    add([e for e in ranked if e.get("_edge_kind") == "boss"], 4)
    add([e for e in ranked if e.get("_edge_kind") == "redkey"], 8)
    add([e for e in ranked if e.get("_edge_kind") == "progress"], 6)
    add([e for e in ranked if e.get("_edge_kind") == "stat"], max(10, edge_limit // 2))
    add([e for e in ranked if e.get("_edge_kind") == "key"], max(8, edge_limit // 3))
    add([e for e in ranked if e.get("_edge_kind") == "potion"], max(6, edge_limit // 4))
    add(ranked, edge_limit)
    return chosen[:edge_limit]


def accept_factory():
    labels: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    active: dict[int, dict[str, Any]] = {}

    def accept(ent: dict[str, Any]) -> bool:
        sig = gw._collected_signature(ent)
        bucket = labels[sig]
        if any(auto.dominates(old, ent) for old in bucket):
            return False
        removed = [old for old in bucket if auto.dominates(ent, old)]
        if removed:
            remove_ids = {old["_id"] for old in removed}
            bucket[:] = [old for old in bucket if old["_id"] not in remove_ids]
            for rid in remove_ids:
                active.pop(rid, None)
        bucket.append(ent)
        active[ent["_id"]] = ent
        return True

    def rebuild(entries: list[dict[str, Any]]) -> None:
        labels.clear()
        active.clear()
        for ent in entries:
            labels[gw._collected_signature(ent)].append(ent)
            active[ent["_id"]] = ent

    return accept, rebuild, active


def make_priority(mode: str):
    if mode == "stage":
        return atomic.priority
    if mode == "stock":
        return lambda ent: (
            0 if p9.goal(ent) else 1,
            -rg.final_resource_stock(ent),
            rg.resource_group_score(ent),
            ent.get("_dmg", 0),
            ent.get("_yd", 0),
            ent.get("_bd", 0),
            p9.stat_deficit(ent),
            auto.redkey_survival_deficit(ent) if ent["atk"] >= 27 and ent["def"] >= 27 and ent["rk"] < 1 else 0,
            p9.boss_survival_deficit(ent) if ent["rk"] >= 1 else 0,
            -ent["hp"],
        )
    if mode == "cost":
        return lambda ent: (
            0 if p9.goal(ent) else 1,
            rg.resource_group_score(ent),
            rg.old_score(ent),
            ent.get("_dmg", 0),
            ent.get("_yd", 0),
            ent.get("_bd", 0),
            p9.stat_deficit(ent),
            auto.redkey_survival_deficit(ent) if ent["atk"] >= 27 and ent["def"] >= 27 and ent["rk"] < 1 else 0,
            p9.boss_survival_deficit(ent) if ent["rk"] >= 1 else 0,
            -ent["hp"],
        )
    if mode == "dynamic":
        def dynamic_priority(ent: dict[str, Any]) -> tuple[int, ...]:
            stat_deficit = p9.stat_deficit(ent)
            stat_gain = max(0, ent.get("_delta_atk", 0)) + max(0, ent.get("_delta_def", 0))
            stat_cost = ent.get("_dynamic_cost", 0)
            before_def = ent["def"] - max(0, ent.get("_delta_def", 0))
            if stat_deficit > 0 and stat_gain:
                if before_def <= 21 and stat_cost <= 120:
                    stat_order = 0
                elif before_def <= 21 and stat_cost <= 180:
                    stat_order = 1
                else:
                    stat_order = 2
            else:
                stat_order = 3
            free_positive = (
                ent.get("_dynamic_cost", 0) == 0
                and ent.get("_dynamic_net", 0) >= 1200
                and ent.get("_dynamic_total", 0) <= 3300
            )
            resource_score = (
                rg.resource_group_score(ent)
                + stat_deficit * 45
                - min(600, ent.get("_dynamic_total", 0)) // 6
            )
            return (
                auto.label_stage(ent),
                stat_deficit // 4,
                0 if free_positive else 1,
                stat_order,
                resource_score,
                -ent.get("_dynamic_net", 0),
                -ent.get("_dynamic_efficiency", 0),
                stat_deficit,
                auto.redkey_survival_deficit(ent) if ent["atk"] >= 27 and ent["def"] >= 27 and ent["rk"] < 1 else 0,
                p9.boss_survival_deficit(ent) if ent["rk"] >= 1 else 0,
                ent.get("_dmg", 0),
                ent.get("_yd", 0),
                ent.get("_bd", 0),
                -ent["hp"],
                -ent["yk"],
                -ent["bk"],
            )

        return dynamic_priority
    raise ValueError(f"unknown priority mode: {mode}")


def compact(ent: dict[str, Any]) -> dict[str, Any]:
    row = auto.compact(ent)
    row["stock"] = rg.final_resource_stock(ent)
    row["via_targets"] = ent.get("_via_targets", [])
    row["dynamic_value"] = ent.get("_dynamic_value", 0)
    row["dynamic_net"] = ent.get("_dynamic_net", 0)
    row["dynamic_efficiency"] = ent.get("_dynamic_efficiency", 0)
    row["dynamic_total"] = ent.get("_dynamic_total", 0)
    row["major_order"] = list(ent.get("_major_order", ()))
    row["lane_key"] = list(lane_key(ent))
    return row


def trim(entries: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    return atomic.trim(entries, limit)


def prune_obviously_weak(
    entries: list[dict[str, Any]],
    stage: str,
    dmg_slack: int,
    yd_slack: int,
    bd_slack: int,
) -> tuple[list[dict[str, Any]], int]:
    """Drop only candidates that are already worse on every monotone cost.

    This is an optional beam-search accelerator, not part of Pareto dominance.
    The slack keeps unusual resource routes alive unless their incurred damage
    and both door costs are all clearly behind an existing stage goal.
    """
    if dmg_slack < 0:
        return entries, 0
    goals = [ent for ent in entries if atomic.stage_goal(stage, ent)]
    if not goals:
        return entries, 0
    best = min(goals, key=lambda ent: atomic.stage_priority(stage, ent))

    def weak(ent: dict[str, Any]) -> bool:
        if atomic.stage_goal(stage, ent):
            return False
        return (
            ent.get("_dmg", 0) > best.get("_dmg", 0) + dmg_slack
            and ent.get("_yd", 0) > best.get("_yd", 0) + yd_slack
            and ent.get("_bd", 0) > best.get("_bd", 0) + bd_slack
            and ent["atk"] <= best["atk"]
            and ent["def"] <= best["def"]
            and ent["yk"] <= best["yk"] + 1
            and ent["bk"] <= best["bk"]
        )

    kept = [ent for ent in entries if not weak(ent)]
    return kept, len(entries) - len(kept)


def select_phased_sources(
    entries: list[dict[str, Any]],
    stage: str,
    limit: int,
) -> list[dict[str, Any]]:
    """Choose stage sources while preserving distinct compressed-order lanes."""
    if limit <= 0 or len(entries) <= limit:
        return sorted(entries, key=lambda ent: atomic.stage_priority(stage, ent))

    chosen: list[dict[str, Any]] = []
    seen: set[int] = set()

    def add(items: Iterable[dict[str, Any]], quota: int) -> None:
        added = 0
        for ent in items:
            if ent["_id"] in seen:
                continue
            seen.add(ent["_id"])
            chosen.append(ent)
            added += 1
            if len(chosen) >= limit or added >= quota:
                return

    priority = lambda ent: atomic.stage_priority(stage, ent)

    if stage == "stat27":
        # Keep several independent ways of approaching 27/27 alive.  A route
        # that collects stats more slowly can still win after its earlier DEF,
        # lower door cost, or larger key pocket makes later fights cheaper.
        lane_orders = [
            priority,
            lambda ent: (
                ent.get("_dmg", 0),
                ent.get("_yd", 0),
                ent.get("_bd", 0),
                p9.stat_deficit(ent),
                -min(ent["def"], 27),
                -ent["yk"],
                -ent["bk"],
                -ent["hp"],
            ),
            lambda ent: (
                ent.get("_bd", 0),
                ent.get("_yd", 0),
                ent.get("_dmg", 0),
                p9.stat_deficit(ent),
                -ent["bk"],
                -ent["yk"],
                -ent["hp"],
            ),
            lambda ent: (
                -min(ent["def"], 27),
                p9.stat_deficit(ent),
                ent.get("_dmg", 0),
                ent.get("_yd", 0),
                ent.get("_bd", 0),
                -ent["yk"],
                -ent["bk"],
                -ent["hp"],
            ),
            lambda ent: (
                -ent["bk"],
                -ent["yk"],
                ent.get("_bd", 0),
                ent.get("_yd", 0),
                ent.get("_dmg", 0),
                p9.stat_deficit(ent),
                -ent["hp"],
            ),
            lambda ent: (
                0 if "MT10" in ent.get("collected", {}) else 1,
                p9.stat_deficit(ent),
                ent.get("_bd", 0),
                ent.get("_yd", 0),
                ent.get("_dmg", 0),
                -ent["yk"],
                -ent["bk"],
                -ent["hp"],
            ),
        ]
        lane_quota = max(1, limit // len(lane_orders))
        for lane_order in lane_orders:
            add(sorted(entries, key=lane_order), lane_quota)

        buckets: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
        for ent in entries:
            buckets[(
                p9.stat_deficit(ent),
                tuple(ent.get("_major_order", ())[:4]),
                min(ent["yk"], 4),
                min(ent["bk"], 1),
                "MT10" in ent.get("collected", {}),
            )].append(ent)
        lane_heads = [min(bucket, key=priority) for bucket in buckets.values()]
        add(
            sorted(
                lane_heads,
                key=lambda ent: (
                    p9.stat_deficit(ent),
                    -min(ent["def"], 27),
                    -min(ent["atk"], 27),
                    ent.get("_dmg", 0),
                    ent.get("_yd", 0),
                    ent.get("_bd", 0),
                    -ent["yk"],
                    -ent["bk"],
                    -ent["hp"],
                ),
            ),
            max(4, limit // 2),
        )
    else:
        add(sorted(entries, key=priority), max(2, limit // 3))

    add(atomic.select_stage_sources(entries, stage, limit), limit)
    return chosen[:limit]


def run_phased_stage(
    name: str,
    starts: list[dict[str, Any]],
    rounds: int,
    args: argparse.Namespace,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    entries = atomic.trim_stage(starts, args.entry_limit, name)
    rows: list[dict[str, Any]] = []
    expanded_ids: set[int] = set()
    round_no = 0
    stop_after = rounds
    first_goal_round: int | None = None
    while round_no < stop_after:
        round_no += 1
        expandable = [
            ent for ent in entries
            if ent["_id"] not in expanded_ids and not atomic.stage_goal(name, ent)
        ]
        sources = select_phased_sources(expandable, name, args.source_limit)
        new_results: list[dict[str, Any]] = []
        for ent in sources:
            expanded_ids.add(ent["_id"])
            new_results.extend(
                generate_compressed_edges(
                    ent,
                    args.max_targets,
                    args.max_iter,
                    args.edge_limit,
                    args.priority,
                )
            )
        if not new_results:
            break
        entries = atomic.trim_stage(entries + new_results, args.entry_limit, name)
        entries, weak_pruned = prune_obviously_weak(
            entries,
            name,
            args.weak_dmg_slack,
            args.weak_yd_slack,
            args.weak_bd_slack,
        )
        goals = [ent for ent in entries if atomic.stage_goal(name, ent)]
        if goals and first_goal_round is None:
            first_goal_round = round_no
            if name == "stat27":
                stop_after = max(stop_after, round_no + args.stat_goal_grace_rounds)
        best_goal = min(goals, key=lambda ent: atomic.stage_priority(name, ent)) if goals else None
        max_stats = max((ent["atk"], ent["def"]) for ent in entries)
        rows.append({
            "stage": name,
            "round": round_no,
            "sources": len(sources),
            "new": len(new_results),
            "entries": len(entries),
            "expanded": len(expanded_ids),
            "goals": len(goals),
            "weak_pruned": weak_pruned,
            "max_atk": max_stats[0],
            "max_def": max_stats[1],
            "best": compact(best_goal) if best_goal else None,
        })
        print(
            f"{name} round {round_no}: sources={len(sources)} new={len(new_results)} "
            f"entries={len(entries)} expanded={len(expanded_ids)} goals={len(goals)} weakPruned={weak_pruned} "
            f"max={max_stats[0]}/{max_stats[1]}",
            flush=True,
        )
        if best_goal:
            print(f"  best {state_text(best_goal)} stock={rg.final_resource_stock(best_goal)}", flush=True)
    return entries, rows


def run_phased(args: argparse.Namespace) -> dict[str, Any]:
    t0 = time.time()
    start, phase1_result = delayed.find_candidate(args.phase1_expansions)
    phase1_id = start["_id"]
    rows: list[dict[str, Any]] = []

    stat_entries, stage_rows = run_phased_stage("stat27", [start], args.stat_rounds, args)
    rows.extend(stage_rows)
    stat_goals = sorted(
        [ent for ent in stat_entries if atomic.stage_goal("stat27", ent)],
        key=lambda ent: atomic.stage_priority("stat27", ent),
    )

    redkey_entries: list[dict[str, Any]] = []
    redkey_goals: list[dict[str, Any]] = []
    if stat_goals:
        redkey_entries, stage_rows = run_phased_stage(
            "redkey",
            stat_goals[: args.carry_limit],
            args.redkey_rounds,
            args,
        )
        rows.extend(stage_rows)
        redkey_goals = sorted(
            [ent for ent in redkey_entries if atomic.stage_goal("redkey", ent)],
            key=lambda ent: atomic.stage_priority("redkey", ent),
        )

    boss_entries: list[dict[str, Any]] = []
    if redkey_goals:
        boss_entries, stage_rows = run_phased_stage(
            "boss",
            redkey_goals[: args.carry_limit],
            args.boss_rounds,
            args,
        )
        rows.extend(stage_rows)

    goals = rg.best_goals(boss_entries)
    best = goals[0] if goals else None
    if best:
        write_walk(best, phase1_id)
    frontier = boss_entries or redkey_entries or stat_entries
    top_entries = sorted(frontier, key=make_priority(args.priority))[:20]
    return {
        "elapsed": time.time() - t0,
        "mode": "phased",
        "priority": args.priority,
        "phase1_elapsed": phase1_result.get("elapsed"),
        "start": compact(start),
        "expanded": sum(row["sources"] for row in rows),
        "generated_total": sum(row["new"] for row in rows),
        "accepted_total": 0,
        "entry_count": len(frontier),
        "goal_count": len(goals),
        "best": compact(best) if best else None,
        "top_goals": [compact(ent) for ent in goals[:10]],
        "top_entries": [compact(ent) for ent in top_entries],
        "rows": rows,
        "stage_counts": {
            "stat_goals": len(stat_goals),
            "redkey_goals": len(redkey_goals),
            "boss_goals": len(goals),
        },
        "weak_prune": {
            "dmg_slack": args.weak_dmg_slack,
            "yd_slack": args.weak_yd_slack,
            "bd_slack": args.weak_bd_slack,
        },
    }


def run_dijkstra_stage(
    name: str,
    starts: list[dict[str, Any]],
    max_expansions: int,
    args: argparse.Namespace,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    accept, rebuild, active = accept_factory()
    heap: list[tuple[tuple[int, ...], int, int]] = []
    seq = 0

    def stage_queue_priority(ent: dict[str, Any]) -> tuple[int, ...]:
        if name != "stat27":
            return atomic.stage_priority(name, ent)
        deficit = p9.stat_deficit(ent)
        incurred = (
            ent.get("_dmg", 0)
            + ent.get("_yd", 0) * rg.YK_VALUE
            + ent.get("_bd", 0) * rg.BK_VALUE
            + ent.get("_rd", 0) * rg.RED_KEY_VALUE
            - ent["yk"] * rg.YK_VALUE
            - ent["bk"] * rg.BK_VALUE
        )
        return (
            incurred + deficit * args.stat_heuristic_unit,
            deficit,
            -min(ent["def"], 27),
            -min(ent["atk"], 27),
            ent.get("_bd", 0),
            ent.get("_yd", 0),
            ent.get("_dmg", 0),
            -ent["yk"],
            -ent["bk"],
            -ent["hp"],
        )

    def push(ent: dict[str, Any]) -> None:
        nonlocal seq
        seq += 1
        heapq.heappush(heap, (stage_queue_priority(ent), seq, ent["_id"]))

    for ent in starts:
        if accept(ent):
            push(ent)

    rows: list[dict[str, Any]] = []
    expanded_ids: set[int] = set()
    expanded = 0
    generated = 0
    while heap and expanded < max_expansions:
        _priority, _seq, ent_id = heapq.heappop(heap)
        ent = active.get(ent_id)
        if ent is None or ent_id in expanded_ids:
            continue
        expanded_ids.add(ent_id)
        expanded += 1
        if atomic.stage_goal(name, ent):
            continue

        edges = generate_compressed_edges(
            ent,
            args.max_targets,
            args.max_iter,
            args.edge_limit,
            args.priority,
        )
        generated += len(edges)
        for edge in edges:
            if accept(edge):
                push(edge)

        weak_pruned = 0
        if args.entry_limit > 0 and len(active) > args.entry_limit:
            kept = atomic.trim_stage(list(active.values()), args.entry_limit, name)
            kept, weak_pruned = prune_obviously_weak(
                kept,
                name,
                args.weak_dmg_slack,
                args.weak_yd_slack,
                args.weak_bd_slack,
            )
            rebuild(kept)
            kept_ids = {kept_ent["_id"] for kept_ent in kept}
            expanded_ids.intersection_update(kept_ids)
            heap = []
            for kept_ent in kept:
                if kept_ent["_id"] not in expanded_ids:
                    push(kept_ent)

        if expanded % args.report_every == 0 or atomic.stage_goal(name, ent):
            entries = list(active.values())
            goals = [entry for entry in entries if atomic.stage_goal(name, entry)]
            best_goal = min(goals, key=lambda entry: atomic.stage_priority(name, entry)) if goals else None
            max_stats = max((entry["atk"], entry["def"]) for entry in entries)
            rows.append({
                "stage": name,
                "round": expanded,
                "sources": expanded,
                "new": generated,
                "entries": len(entries),
                "goals": len(goals),
                "weak_pruned": weak_pruned,
                "max_atk": max_stats[0],
                "max_def": max_stats[1],
                "best": compact(best_goal) if best_goal else None,
            })
            print(
                f"{name} expand {expanded}: generated={generated} entries={len(entries)} "
                f"goals={len(goals)} weakPruned={weak_pruned} max={max_stats[0]}/{max_stats[1]}",
                flush=True,
            )
            if best_goal:
                print(f"  best {state_text(best_goal)} stock={rg.final_resource_stock(best_goal)}", flush=True)

    entries = atomic.trim_stage(list(active.values()), args.entry_limit, name)
    entries, _weak_pruned = prune_obviously_weak(
        entries,
        name,
        args.weak_dmg_slack,
        args.weak_yd_slack,
        args.weak_bd_slack,
    )
    return entries, rows


def run_phased_dijkstra(args: argparse.Namespace) -> dict[str, Any]:
    t0 = time.time()
    start, phase1_result = delayed.find_candidate(args.phase1_expansions)
    phase1_id = start["_id"]
    rows: list[dict[str, Any]] = []

    stat_entries, stage_rows = run_dijkstra_stage("stat27", [start], args.stat_expansions, args)
    rows.extend(stage_rows)
    stat_goals = sorted(
        [ent for ent in stat_entries if atomic.stage_goal("stat27", ent)],
        key=lambda ent: atomic.stage_priority("stat27", ent),
    )

    redkey_entries: list[dict[str, Any]] = []
    redkey_goals: list[dict[str, Any]] = []
    if stat_goals:
        redkey_entries, stage_rows = run_dijkstra_stage(
            "redkey",
            stat_goals[: args.carry_limit],
            args.redkey_expansions,
            args,
        )
        rows.extend(stage_rows)
        redkey_goals = sorted(
            [ent for ent in redkey_entries if atomic.stage_goal("redkey", ent)],
            key=lambda ent: atomic.stage_priority("redkey", ent),
        )

    boss_entries: list[dict[str, Any]] = []
    if redkey_goals:
        boss_entries, stage_rows = run_dijkstra_stage(
            "boss",
            redkey_goals[: args.carry_limit],
            args.boss_expansions,
            args,
        )
        rows.extend(stage_rows)

    goals = rg.best_goals(boss_entries)
    best = goals[0] if goals else None
    if best:
        write_walk(best, phase1_id)
    frontier = boss_entries or redkey_entries or stat_entries
    top_entries = sorted(frontier, key=make_priority(args.priority))[:20]
    return {
        "elapsed": time.time() - t0,
        "mode": "phased-dijkstra",
        "priority": args.priority,
        "phase1_elapsed": phase1_result.get("elapsed"),
        "start": compact(start),
        "expanded": sum(
            max((row["sources"] for row in rows if row["stage"] == stage), default=0)
            for stage in {"stat27", "redkey", "boss"}
        ),
        "generated_total": sum(
            max((row["new"] for row in rows if row["stage"] == stage), default=0)
            for stage in {"stat27", "redkey", "boss"}
        ),
        "accepted_total": 0,
        "entry_count": len(frontier),
        "goal_count": len(goals),
        "best": compact(best) if best else None,
        "top_goals": [compact(ent) for ent in goals[:10]],
        "top_entries": [compact(ent) for ent in top_entries],
        "rows": rows,
        "stage_counts": {
            "stat_goals": len(stat_goals),
            "redkey_goals": len(redkey_goals),
            "boss_goals": len(goals),
        },
        "weak_prune": {
            "dmg_slack": args.weak_dmg_slack,
            "yd_slack": args.weak_yd_slack,
            "bd_slack": args.weak_bd_slack,
        },
    }


def write_walk(best: dict[str, Any], phase1_id: int) -> None:
    chain = gw.trace_chain(best)
    lines = [
        "# Post-9 Compressed Resource Dijkstra Best Walk",
        "",
        f"> final: {state_text(best)}",
        "",
    ]
    for idx, ent in enumerate(chain):
        if idx == 0:
            label = "4F search start"
        elif ent.get("_id") == phase1_id:
            label = "phase1 delayed prefix complete"
        else:
            label = ent.get("_last_action") or ent.get("_source") or p9.action_summary(ent)
        prev = chain[idx - 1] if idx else None
        lines.extend([f"## {idx}. {label}", "", f"- {state_text(ent)}"])
        if prev:
            lines.append(
                f"- segment dmg={ent.get('_dmg', 0) - prev.get('_dmg', 0)} "
                f"door delta={ent.get('_yd', 0) - prev.get('_yd', 0)}/"
                f"{ent.get('_bd', 0) - prev.get('_bd', 0)}/"
                f"{ent.get('_rd', 0) - prev.get('_rd', 0)}"
            )
            desc = ent.get("_resource_group")
            if desc:
                lines.append(f"- compressed group: {auto.summarize_group(desc)}")
        lines.append("")
    os.makedirs(os.path.dirname(OUT_WALK), exist_ok=True)
    with open(OUT_WALK, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")


def run(args: argparse.Namespace) -> dict[str, Any]:
    t0 = time.time()
    start, phase1_result = delayed.find_candidate(args.phase1_expansions)
    phase1_id = start["_id"]
    priority = make_priority(args.priority)
    accept, rebuild, active = accept_factory()
    heap: list[tuple[tuple[int, ...], int, int]] = []
    lane_heaps: dict[tuple[Any, ...], list[tuple[tuple[int, ...], int, int]]] = defaultdict(list)
    lane_order: list[tuple[Any, ...]] = []
    lane_cursor = 0
    expanded_ids: set[int] = set()
    seq = 0

    def push(ent: dict[str, Any]) -> None:
        nonlocal seq
        seq += 1
        item = (priority(ent), seq, ent["_id"])
        heapq.heappush(heap, item)
        if args.scheduler == "lanes":
            key = lane_key(ent)
            if key not in lane_heaps:
                lane_order.append(key)
            heapq.heappush(lane_heaps[key], (lane_priority(ent), seq, ent["_id"]))

    def pop_heap(source: list[tuple[tuple[int, ...], int, int]]) -> dict[str, Any] | None:
        while source:
            _prio, _seq, ent_id = heapq.heappop(source)
            ent = active.get(ent_id)
            if ent is not None and ent_id not in expanded_ids:
                expanded_ids.add(ent_id)
                return ent
        return None

    def pop_lane() -> dict[str, Any] | None:
        nonlocal lane_cursor
        if not lane_order:
            return None
        ready: list[tuple[tuple[tuple[int, ...], int, int], list[tuple[tuple[int, ...], int, int]]]] = []
        for key in lane_order:
            lane = lane_heaps.get(key)
            if lane is None:
                continue
            while lane:
                _prio, _seq, ent_id = lane[0]
                if active.get(ent_id) is not None and ent_id not in expanded_ids:
                    break
                heapq.heappop(lane)
            if lane:
                ready.append((lane[0], lane))
        if not ready:
            return None
        ready.sort(key=lambda item: item[0])
        if args.lane_top_k > 0:
            ready = ready[:args.lane_top_k]
            lane = ready[lane_cursor % len(ready)][1]
            lane_cursor += 1
            return pop_heap(lane)
        return pop_heap(ready[0][1])

    def pop_next() -> dict[str, Any] | None:
        if args.scheduler != "lanes":
            return pop_heap(heap)
        force_lane = expanded < args.stat_warmup
        use_lane = force_lane or (args.lane_period > 0 and (expanded + 1) % args.lane_period == 0)
        if use_lane:
            ent = pop_lane()
            if ent is not None:
                return ent
        ent = pop_heap(heap)
        if ent is not None:
            return ent
        return pop_lane()

    def queue_size() -> int:
        if args.scheduler != "lanes":
            return len(heap)
        return sum(len(lane) for lane in lane_heaps.values())

    accept(start)
    push(start)

    rows = []
    expanded = 0
    generated_total = 0
    accepted_total = 1
    best_goal: dict[str, Any] | None = None
    while queue_size() and expanded < args.max_expansions:
        ent = pop_next()
        if ent is None:
            break
        expanded += 1
        if p9.goal(ent):
            continue

        edges = generate_compressed_edges(ent, args.max_targets, args.max_iter, args.edge_limit, args.priority)
        generated_total += len(edges)
        accepted_now = 0
        for edge in edges:
            if accept(edge):
                push(edge)
                accepted_now += 1
        accepted_total += accepted_now

        if args.entry_limit > 0 and len(active) > args.entry_limit:
            kept = trim(list(active.values()), args.entry_limit)
            rebuild(kept)
            kept_ids = {kept_ent["_id"] for kept_ent in kept}
            expanded_ids.intersection_update(kept_ids)
            heap = []
            lane_heaps.clear()
            lane_order.clear()
            for kept_ent in kept:
                if kept_ent["_id"] not in expanded_ids:
                    push(kept_ent)

        if expanded % args.report_every == 0 or accepted_now or any(p9.goal(e) for e in edges):
            entries = list(active.values())
            goals = rg.best_goals(entries)
            if goals:
                best_goal = goals[0]
            stat_done = [e for e in entries if e["atk"] >= 27 and e["def"] >= 27]
            redkey_ready = [
                e for e in stat_done
                if e["rk"] < 1 and e["yk"] >= 1 and auto.redkey_survival_deficit(e) == 0
            ]
            rk_entries = [e for e in entries if e["rk"] >= 1]
            rows.append({
                "expanded": expanded,
                "edges": len(edges),
                "accepted": accepted_now,
                "entries": len(entries),
                "goals": len(goals),
                "stat_done": len(stat_done),
                "redkey_ready": len(redkey_ready),
                "rk_entries": len(rk_entries),
                "lanes": len(lane_order) if args.scheduler == "lanes" else 1,
                "best_goal": compact(goals[0]) if goals else None,
                "best_entry": compact(sorted(entries, key=priority)[0]) if entries else None,
            })
            print(
                f"expand {expanded}: edges={len(edges)} accepted={accepted_now} active={len(entries)} "
                f"stat27={len(stat_done)} redkeyReady={len(redkey_ready)} rk={len(rk_entries)} "
                f"goals={len(goals)} lanes={len(lane_order) if args.scheduler == 'lanes' else 1}",
                flush=True,
            )
            if goals:
                print(f"  best {state_text(goals[0])} stock={rg.final_resource_stock(goals[0])}", flush=True)

    entries = list(active.values())
    goals = rg.best_goals(entries)
    if goals:
        best_goal = goals[0]
        write_walk(best_goal, phase1_id)

    top_entries = sorted(entries, key=priority)[:20]
    return {
        "elapsed": time.time() - t0,
        "mode": "dijkstra",
        "priority": args.priority,
        "scheduler": args.scheduler,
        "lane_period": args.lane_period,
        "lane_top_k": args.lane_top_k,
        "stat_warmup": args.stat_warmup,
        "phase1_elapsed": phase1_result.get("elapsed"),
        "start": compact(start),
        "expanded": expanded,
        "generated_total": generated_total,
        "accepted_total": accepted_total,
        "entry_count": len(entries),
        "goal_count": len(goals),
        "best": compact(best_goal) if best_goal else None,
        "top_goals": [compact(e) for e in goals[:10]],
        "top_entries": [compact(e) for e in top_entries],
        "rows": rows,
    }


def write_outputs(data: dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    lines = [
        "# Post-9 Compressed Resource Dijkstra",
        "",
        f"- elapsed: {data['elapsed']:.1f}s",
        f"- mode: {data.get('mode', 'dijkstra')}",
        f"- priority: {data['priority']}",
        f"- scheduler: {data.get('scheduler', 'heap')}",
        f"- lane period: {data.get('lane_period', '-')}",
        f"- lane top-k: {data.get('lane_top_k', '-')}",
        f"- stat warmup: {data.get('stat_warmup', '-')}",
        f"- expanded: {data['expanded']}",
        f"- generated edges: {data['generated_total']}",
        f"- accepted labels: {data['accepted_total']}",
        f"- entry count: {data['entry_count']}",
        f"- goal count: {data['goal_count']}",
        f"- start: {data['start']}",
    ]
    if data.get("best"):
        b = data["best"]
        lines.append(
            f"- best: HP={b['hp']} ATK={b['atk']} DEF={b['def']} YK={b['yk']} BK={b['bk']} RK={b['rk']} "
            f"dmg={b['dmg']} door={b['yd']}/{b['bd']}/{b['rd']} stock={b['stock']} "
            f"rgScore={b['resource_group_score']} oldScore={b['old_score']} dyn={b.get('dynamic_total', 0)}"
        )
    lines.extend([
        "",
        "## Top Goals",
        "",
        "| # | stock | rgScore | oldScore | dyn | state | last action |",
        "|---:|---:|---:|---:|---:|---|---|",
    ])
    for idx, row in enumerate(data["top_goals"], 1):
        lines.append(
            f"| {idx} | {row['stock']} | {row['resource_group_score']} | {row['old_score']} | {row.get('dynamic_total', 0)} | "
            f"HP={row['hp']} ATK={row['atk']} DEF={row['def']} YK={row['yk']} BK={row['bk']} RK={row['rk']} "
            f"dmg={row['dmg']} door={row['yd']}/{row['bd']}/{row['rd']} | {row['last_action']} via={'+'.join(row.get('via_targets', []))} |"
        )
    lines.extend(["", "## Search Progress", ""])
    if data.get("mode") in {"phased", "phased-dijkstra"}:
        lines.extend([
            f"- stage counts: `{data.get('stage_counts', {})}`",
            f"- weak prune: `{data.get('weak_prune', {})}`",
            "",
            "| stage | round | sources | new | entries | weak pruned | max ATK/DEF | goals | best |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---|",
        ])
        for row in data["rows"]:
            best = row.get("best")
            best_text = "-"
            if best:
                best_text = (
                    f"HP={best['hp']} dmg={best['dmg']} door={best['yd']}/{best['bd']}/{best['rd']} "
                    f"stock={best['stock']}"
                )
            lines.append(
                f"| {row['stage']} | {row['round']} | {row['sources']} | {row['new']} | "
                f"{row['entries']} | {row['weak_pruned']} | {row['max_atk']}/{row['max_def']} | "
                f"{row['goals']} | {best_text} |"
            )
    else:
        lines.extend([
            "| expanded | edges | accepted | entries | lanes | 27/27 | redkey ready | rk | goals | best goal |",
            "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
        ])
        for row in data["rows"]:
            best = row.get("best_goal")
            best_text = "-"
            if best:
                best_text = (
                    f"HP={best['hp']} dmg={best['dmg']} door={best['yd']}/{best['bd']}/{best['rd']} "
                    f"stock={best['stock']}"
                )
            lines.append(
                f"| {row['expanded']} | {row['edges']} | {row['accepted']} | {row['entries']} | "
                f"{row.get('lanes', 1)} | {row['stat_done']} | {row['redkey_ready']} | {row['rk_entries']} | {row['goals']} | {best_text} |"
            )
    lines.extend([
        "",
        "## Top Frontier",
        "",
        "| # | state | dyn | kind | last action |",
        "|---:|---|---:|---|---|",
    ])
    for idx, row in enumerate(data["top_entries"], 1):
        lines.append(
            f"| {idx} | HP={row['hp']} ATK={row['atk']} DEF={row['def']} YK={row['yk']} BK={row['bk']} RK={row['rk']} "
            f"dmg={row['dmg']} door={row['yd']}/{row['bd']}/{row['rd']} stock={row['stock']} | "
            f"{row.get('dynamic_net', 0)}/{row.get('dynamic_total', 0)} | "
            f"{row['edge_kind']} | {row['last_action']} via={'+'.join(row.get('via_targets', []))} order={' > '.join(row.get('major_order', []))} |"
        )
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["dijkstra", "phased", "phased-dijkstra"], default="dijkstra")
    parser.add_argument("--phase1-expansions", type=int, default=300)
    parser.add_argument("--max-expansions", type=int, default=220)
    parser.add_argument("--entry-limit", type=int, default=520)
    parser.add_argument("--max-targets", type=int, default=0)
    parser.add_argument("--max-iter", type=int, default=500000)
    parser.add_argument("--edge-limit", type=int, default=32)
    parser.add_argument("--report-every", type=int, default=25)
    parser.add_argument("--source-limit", type=int, default=14)
    parser.add_argument("--carry-limit", type=int, default=80)
    parser.add_argument("--stat-rounds", type=int, default=12)
    parser.add_argument(
        "--stat-goal-grace-rounds",
        type=int,
        default=6,
        help="Continue stat-lane expansion for this many rounds after the first 27/27 candidate.",
    )
    parser.add_argument("--redkey-rounds", type=int, default=6)
    parser.add_argument("--boss-rounds", type=int, default=6)
    parser.add_argument("--stat-expansions", type=int, default=180)
    parser.add_argument("--redkey-expansions", type=int, default=80)
    parser.add_argument("--boss-expansions", type=int, default=80)
    parser.add_argument("--weak-dmg-slack", type=int, default=180)
    parser.add_argument("--weak-yd-slack", type=int, default=2)
    parser.add_argument("--weak-bd-slack", type=int, default=1)
    parser.add_argument(
        "--stat-heuristic-unit",
        type=int,
        default=40,
        help="Optimistic queue estimate per missing ATK/DEF point in phased Dijkstra.",
    )
    parser.add_argument("--priority", choices=["stage", "cost", "stock", "dynamic"], default="stage")
    parser.add_argument("--scheduler", choices=["heap", "lanes"], default="heap")
    parser.add_argument("--lane-period", type=int, default=6, help="When using lanes, pop one lane entry every N expansions.")
    parser.add_argument(
        "--lane-top-k",
        type=int,
        default=0,
        help="When using lanes, round-robin among the best K lane heads; 0 keeps strict best-lane behavior.",
    )
    parser.add_argument(
        "--stat-warmup",
        type=int,
        default=0,
        help="When using lanes, prefer incomplete 27/27 stat lanes for the first N expansions.",
    )
    args = parser.parse_args()
    if args.mode == "phased":
        data = run_phased(args)
    elif args.mode == "phased-dijkstra":
        data = run_phased_dijkstra(args)
    else:
        data = run(args)
    write_outputs(data)
    print(f"wrote {OUT_JSON}")
    print(f"wrote {OUT_MD}")
    if data.get("best"):
        print(f"wrote {OUT_WALK}")
        if os.path.exists(OUT_WALK_DETAIL):
            print(f"wrote {OUT_WALK_DETAIL}")


if __name__ == "__main__":
    main()
