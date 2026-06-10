#!/usr/bin/env python3
"""Search post-9 continuation with atomic resource edges.

The auto resource-group search treats a target route as one compressed edge.
This experiment keeps the same real floor path finder, but cuts every returned
route at the first newly collected resource.  The next expansion re-runs path
finding from the new state, so resource order is discovered by the label search
instead of being bundled into one large edge.
"""

from __future__ import annotations

import argparse
import heapq
import json
import os
import re
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
from scripts import post9_auto_resource_group_pareto as auto
from scripts import post9_resource_group_search as rg
from scripts import report_post9_atomic_resource_graph as graph
from src.solver import gen_walkthrough as gw


OUT_JSON = os.path.join("outputs", "results", "post9_atomic_resource_dijkstra.json")
OUT_MD = os.path.join("outputs", "reports", "post9_atomic_resource_dijkstra.md")
OUT_WALK = os.path.join("outputs", "walkthroughs", "walkthrough_post9_atomic_resource_dijkstra_best.md")
OUT_WALK_DETAIL = os.path.join("outputs", "walkthroughs", "walkthrough_post9_atomic_resource_dijkstra_best_detailed.md")

RESOURCE_IDS = {
    "redGem",
    "blueGem",
    "yellowKey",
    "blueKey",
    "redKey",
    "redPotion",
    "bluePotion",
}

ITEM_NAME = {
    "redGem": "红宝石",
    "blueGem": "蓝宝石",
    "yellowKey": "黄钥匙",
    "blueKey": "蓝钥匙",
    "redKey": "红钥匙",
    "redPotion": "红血瓶",
    "bluePotion": "蓝血瓶",
    "yellowDoor": "黄门",
    "blueDoor": "蓝门",
    "redDoor": "红门",
    "greenSlime": "绿史莱姆",
    "redSlime": "红史莱姆",
    "bat": "小蝙蝠",
    "skeleton": "骷髅",
    "skeletonSoldier": "骷髅士兵",
    "bluePriest": "蓝法师",
    "yellowGuard": "初级卫兵",
    "skeletonCaptain": "骷髅队长",
    "upFloor": "上楼",
}

NODE_RE = re.compile(r"^(?P<fid>MT\d+) x(?P<x>\d+)y(?P<y>\d+) (?P<name>.+)$")


def state_text(ent: dict[str, Any]) -> str:
    return (
        f"HP={ent['hp']} ATK={ent['atk']} DEF={ent['def']} "
        f"YK={ent['yk']} BK={ent['bk']} RK={ent['rk']} "
        f"dmg={ent.get('_dmg', 0)} door={ent.get('_yd', 0)}/{ent.get('_bd', 0)}/{ent.get('_rd', 0)}"
    )


def records_to_positions(records: Iterable[dict[str, Any]]) -> set[tuple[int, int]]:
    return {tuple(r["pos"]) for r in records}


def segment_positions(seg: dict[str, Any]) -> set[tuple[int, int]]:
    return (
        records_to_positions(seg.get("items", []))
        | records_to_positions(seg.get("doors", []))
        | records_to_positions(seg.get("monsters", []))
    )


def node_target(seg: dict[str, Any]) -> tuple[tuple[int, int] | None, str]:
    items = seg.get("items", [])
    if items:
        rec = items[-1]
        return tuple(rec["pos"]), rec["eid"]
    match = NODE_RE.match(seg.get("to", ""))
    if match:
        return (int(match.group("x")), int(match.group("y"))), "upFloor" if seg.get("terminal") else "unknown"
    return None, "unknown"


def fmt_records(records: Iterable[dict[str, Any]]) -> str:
    vals = []
    for rec in records:
        pos = rec["pos"]
        if isinstance(pos, str):
            vals.append(f"{pos}{ITEM_NAME.get(rec['eid'], rec['eid'])}")
            continue
        x, y = pos
        vals.append(f"x{x}y{y}{ITEM_NAME.get(rec['eid'], rec['eid'])}")
    return ", ".join(vals) if vals else "-"


def group_text(seg: dict[str, Any]) -> str:
    return (
        f"资源:{fmt_records(seg.get('items', []))}; "
        f"门:{fmt_records(seg.get('doors', []))}; "
        f"怪:{fmt_records(seg.get('monsters', []))}"
    )


def edge_kind(base: dict[str, Any], ent: dict[str, Any], eid: str) -> str:
    if eid == "redDoor":
        return "boss"
    if eid == "upFloor":
        return "progress"
    if ent["rk"] > base["rk"] or eid == "redKey":
        return "redkey"
    if ent["atk"] > base["atk"] or ent["def"] > base["def"]:
        return "stat"
    if ent["yk"] > base["yk"] or ent["bk"] > base["bk"]:
        return "key"
    if ent["hp"] > base["hp"]:
        return "potion"
    return "other"


def annotate_edge(
    base: dict[str, Any],
    ent: dict[str, Any],
    label: str,
    seg: dict[str, Any],
    eid: str,
    via_targets: Iterable[str] = (),
) -> dict[str, Any]:
    desc = {
        "items": list(seg.get("items", [])),
        "doors": list(seg.get("doors", [])),
        "monsters": list(seg.get("monsters", [])),
    }
    ent["_last_action"] = label
    ent["_via_targets"] = list(via_targets)
    ent["_resource_group"] = desc
    ent["_edge_kind"] = edge_kind(base, ent, eid)
    ent["_delta_hp"] = ent["hp"] - base["hp"]
    ent["_delta_dmg"] = ent.get("_dmg", 0) - base.get("_dmg", 0)
    ent["_delta_yd"] = ent.get("_yd", 0) - base.get("_yd", 0)
    ent["_delta_bd"] = ent.get("_bd", 0) - base.get("_bd", 0)
    ent["_delta_rd"] = ent.get("_rd", 0) - base.get("_rd", 0)
    ent["_delta_yk"] = ent["yk"] - base["yk"]
    ent["_delta_bk"] = ent["bk"] - base["bk"]
    ent["_delta_rk"] = ent["rk"] - base["rk"]
    ent["_delta_atk"] = ent["atk"] - base["atk"]
    ent["_delta_def"] = ent["def"] - base["def"]
    store = gw._entry_store[ent["_id"]]
    for key in (
        "_last_action",
        "_via_targets",
        "_resource_group",
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
    ):
        store[key] = ent[key]
    return ent


def apply_segment(base: dict[str, Any], full_edge: dict[str, Any], seg: dict[str, Any]) -> dict[str, Any] | None:
    fid, targets, flyback = full_edge.get("_step_info", (None, [], True))
    if not fid:
        return None
    pos, eid = node_target(seg)
    if pos is None:
        return None

    add_pos = segment_positions(seg)
    if seg.get("terminal"):
        add_pos.add(pos)

    before = auto.collected_for(base, fid)
    nc = dict(base.get("collected", {}))
    nc[fid] = before | frozenset(add_pos)

    after = seg["after"]
    ent = gw._make_result(
        after["hp"],
        after["yk"],
        after["bk"],
        after["rk"],
        after["atk"],
        after["def"],
        nc,
        base["_id"],
        (fid, [eid], flyback),
        dmg_cost=seg["segment_dmg"],
    )
    label = f"{fid} atomic {eid} x{pos[0]}y{pos[1]} via {full_edge.get('_last_action', '')}"
    if seg.get("terminal") and fid == "MT9" and eid == "upFloor":
        auto.mark_mt10_reached(ent)
    return annotate_edge(base, ent, label, seg, eid, targets)


def route_edges(ent: dict[str, Any], max_targets: int, max_iter: int) -> list[dict[str, Any]]:
    by_floor_eid: dict[tuple[str, str], set[tuple[int, int]]] = defaultdict(set)
    for target in stage_candidate_targets(ent, max_targets):
        by_floor_eid[(target.fid, target.eid)].add(target.pos)

    edges: list[dict[str, Any]] = []
    for (fid, eid), positions in sorted(by_floor_eid.items(), key=lambda item: (int(item[0][0][2:]), item[0][1])):
        edges.extend(auto.exact_item_edges(ent, fid, eid, positions, max_iter=max_iter))
    if mt10_progress_allowed(ent):
        edges.extend(auto.progress_edges(ent, max_iter=max_iter))
    edges.extend(auto.boss_edges(ent))
    return edges


def mt10_progress_allowed(ent: dict[str, Any]) -> bool:
    if "MT10" in ent.get("collected", {}):
        return False
    if ent["atk"] >= 27 and ent["def"] >= 27:
        return True
    if ent["atk"] >= 26 and ent["def"] >= 26:
        return True
    return p9.stat_deficit(ent) <= 2 and ent["bk"] >= 1 and ent["yk"] >= 1


def stage_candidate_targets(ent: dict[str, Any], max_targets: int) -> list[auto.AutoTarget]:
    """Return resource targets that match the current macro stage.

    Atomic edges still collect incidental prerequisites, so the target set can
    stay narrow.  During the stat stage, for example, aiming at gems will expose
    the red potions / keys on the path as first-class atomic edges.
    """
    items = [t for t in auto.TARGETS if t.pos not in auto.collected_for(ent, t.fid)]
    stat_pending = ent["atk"] < 27 or ent["def"] < 27
    mt10_needed = p9.needs_mt10_for_stats(ent)

    def keep(t: auto.AutoTarget) -> bool:
        if stat_pending:
            if t.eid == "redGem":
                return ent["atk"] < 27
            if t.eid == "blueGem":
                return ent["def"] < 27
            if t.eid == "yellowKey":
                return ent["yk"] < max(3, p9.desired_yk(ent) + 1)
            if t.eid == "blueKey":
                return ent["bk"] < 1 and mt10_needed
            return False
        if ent["rk"] < 1:
            if t.eid == "redKey":
                return auto.redkey_survival_deficit(ent) == 0
            if t.eid == "yellowKey":
                return ent["yk"] < max(3, p9.desired_yk(ent) + 1)
            if t.eid in {"redPotion", "bluePotion"}:
                return auto.redkey_survival_deficit(ent) > 0
            return False
        if t.eid in {"redPotion", "bluePotion"}:
            return p9.boss_survival_deficit(ent) > 0
        if t.eid == "yellowKey":
            return ent["yk"] < p9.desired_yk(ent)
        return False

    def rank(t: auto.AutoTarget) -> tuple[int, int, int, int, int]:
        value = auto.target_value(ent, t.eid)
        if t.eid == "blueGem":
            phase = 0
        elif t.eid == "redGem":
            phase = 1
        elif t.eid == "blueKey":
            phase = 2
        elif t.eid == "yellowKey":
            phase = 3
        elif t.eid == "redKey":
            phase = 4
        elif t.eid == "bluePotion":
            phase = 5
        else:
            phase = 6
        return (phase, -value, int(t.fid[2:]), t.pos[0], t.pos[1])

    kept = sorted([t for t in items if keep(t)], key=rank)
    forced: list[auto.AutoTarget] = []
    if stat_pending:
        if ent["bk"] < 1 and mt10_needed:
            forced.extend([t for t in kept if t.eid == "blueKey"][:3])
        if ent["yk"] < max(2, p9.desired_yk(ent)):
            forced.extend([t for t in kept if t.eid == "yellowKey"][:5])
    elif ent["rk"] < 1:
        if ent["yk"] < max(2, p9.desired_yk(ent)):
            forced.extend([t for t in kept if t.eid == "yellowKey"][:5])
        forced.extend([t for t in kept if t.eid == "redKey"][:2])
    forced_keys = {(t.fid, t.pos, t.eid) for t in forced}
    rest = [t for t in kept if (t.fid, t.pos, t.eid) not in forced_keys]
    if max_targets > 0:
        selected = forced + rest[: max(0, max_targets - len(forced))]
    else:
        selected = forced + rest
    return selected


def generate_atomic_edges(ent: dict[str, Any], max_targets: int, max_iter: int, edge_limit: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for full in route_edges(ent, max_targets=max_targets, max_iter=max_iter):
        fid, targets, flyback = full.get("_step_info", (None, [], True))
        if not fid:
            continue
        if full.get("_edge_kind") in {"boss", "progress"}:
            if full.get("_edge_kind") == "progress" and "_via_targets" not in full:
                full["_via_targets"] = ["upFloor"]
                gw._entry_store[full["_id"]]["_via_targets"] = full["_via_targets"]
            out.append(full)
            continue
        steps, _final, mismatch = graph.reconstruct_steps(ent, full, fid, targets, flyback, max_iter=max_iter)
        if not steps or mismatch:
            continue
        segments = graph.split_steps(ent, full, fid, full.get("_last_action", ""), steps)
        if not segments:
            continue
        edge = apply_segment(ent, full, segments[0])
        if edge:
            out.append(edge)

    def merge_via(dst: dict[str, Any], src: dict[str, Any]) -> dict[str, Any]:
        merged = sorted(set(dst.get("_via_targets", [])) | set(src.get("_via_targets", [])))
        if merged != dst.get("_via_targets", []):
            dst["_via_targets"] = merged
            gw._entry_store[dst["_id"]]["_via_targets"] = merged
        return dst

    dedup: dict[tuple[Any, ...], dict[str, Any]] = {}
    for edge in out:
        sig = auto.result_signature(edge)
        old = dedup.get(sig)
        key = edge_sort_key(edge)
        if old is None:
            dedup[sig] = edge
        elif key < edge_sort_key(old):
            dedup[sig] = merge_via(edge, old)
        else:
            merge_via(old, edge)
    ranked = sorted(dedup.values(), key=edge_sort_key)
    if edge_limit <= 0:
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
            if added >= quota:
                return

    add([e for e in ranked if e.get("_edge_kind") == "boss"], 4)
    add([e for e in ranked if e.get("_edge_kind") == "redkey"], 6)
    add([e for e in ranked if e.get("_edge_kind") == "progress"], 6)
    add([e for e in ranked if e.get("_edge_kind") == "stat"], max(8, edge_limit // 2))
    add([e for e in ranked if e.get("_edge_kind") == "key"], max(8, edge_limit // 2))
    add([e for e in ranked if e.get("_edge_kind") == "potion"], max(8, edge_limit // 2))
    add(ranked, edge_limit)
    return chosen[: max(edge_limit, len(chosen))]


def edge_sort_key(ent: dict[str, Any]) -> tuple[int, ...]:
    kind_order = {
        "boss": 0,
        "redkey": 1,
        "progress": 2,
        "stat": 3,
        "key": 4,
        "potion": 5,
        "other": 6,
    }.get(ent.get("_edge_kind"), 6)
    via = set(ent.get("_via_targets", []))
    if "blueGem" in via:
        via_rank = 0
    elif "redGem" in via:
        via_rank = 1
    elif "redKey" in via:
        via_rank = 2
    elif "upFloor" in via:
        via_rank = 3
    elif "blueKey" in via or "yellowKey" in via:
        via_rank = 4
    else:
        via_rank = 5
    return (
        0 if p9.goal(ent) else 1,
        kind_order,
        p9.stat_deficit(ent),
        via_rank,
        auto.redkey_survival_deficit(ent) if ent["atk"] >= 27 and ent["def"] >= 27 and ent["rk"] < 1 else 0,
        p9.boss_survival_deficit(ent) if ent["rk"] >= 1 else 0,
        rg.resource_group_score(ent),
        ent.get("_dmg", 0),
        ent.get("_yd", 0),
        ent.get("_bd", 0),
        -ent["hp"],
        -ent["yk"],
        -ent["bk"],
    )


def priority(ent: dict[str, Any]) -> tuple[int, ...]:
    stage = auto.label_stage(ent)
    return (
        stage,
        p9.stat_deficit(ent),
        auto.redkey_survival_deficit(ent) if ent["atk"] >= 27 and ent["def"] >= 27 and ent["rk"] < 1 else 0,
        p9.boss_survival_deficit(ent) if ent["rk"] >= 1 else 0,
        rg.resource_group_score(ent),
        ent.get("_dmg", 0),
        ent.get("_yd", 0),
        ent.get("_bd", 0),
        -ent["hp"],
    )


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


def trim(entries: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    if limit <= 0:
        return auto.pareto_filter(entries)
    filtered = auto.pareto_filter(entries)
    if len(filtered) <= limit:
        return filtered
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

    goals = [e for e in filtered if p9.goal(e)]
    stat_done = [e for e in filtered if e["atk"] >= 27 and e["def"] >= 27]
    stat_pending = [e for e in filtered if e["atk"] < 27 or e["def"] < 27]
    redkey_ready = [e for e in stat_done if e["rk"] < 1 and e["yk"] >= 1]
    rk_entries = [e for e in filtered if e["rk"] >= 1 and not p9.goal(e)]

    add(sorted(goals, key=lambda e: (-rg.final_resource_stock(e), rg.resource_group_score(e))), limit)
    add(sorted(redkey_ready, key=priority), max(20, limit // 8))
    add(sorted(rk_entries, key=priority), max(20, limit // 8))

    bucketed: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for ent in stat_pending:
        mt1 = auto.collected_for(ent, "MT1")
        mt3 = auto.collected_for(ent, "MT3")
        mt7 = auto.collected_for(ent, "MT7")
        mt8 = auto.collected_for(ent, "MT8")
        bucketed[(
            min(ent["atk"], 27),
            min(ent["def"], 27),
            min(ent["yk"], 4),
            min(ent["bk"], 1),
            "MT10" in ent.get("collected", {}),
            (7, 4) in mt1,
            (2, 1) in mt3,
            (3, 1) in mt7,
            (5, 11) in mt8,
        )].append(ent)
    heads = []
    for bucket in bucketed.values():
        heads.extend(sorted(bucket, key=priority)[:3])
    add(sorted(heads, key=priority), max(80, limit // 2))
    add(sorted(filtered, key=priority), limit)
    return chosen[:limit]


def compact(ent: dict[str, Any]) -> dict[str, Any]:
    row = auto.compact(ent)
    row["stock"] = rg.final_resource_stock(ent)
    row["via_targets"] = ent.get("_via_targets", [])
    return row


def write_walk(best: dict[str, Any], phase1_id: int) -> None:
    chain = gw.trace_chain(best)
    lines = [
        "# Post-9 Atomic Resource Dijkstra Best Walk",
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
                lines.append(f"- atomic group: {group_text(desc)}")
        lines.append("")
    os.makedirs(os.path.dirname(OUT_WALK), exist_ok=True)
    with open(OUT_WALK, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")

    old_in, old_out = detail_walk.IN_WALK, detail_walk.OUT_WALK
    try:
        detail_walk.IN_WALK = OUT_WALK
        detail_walk.OUT_WALK = OUT_WALK_DETAIL
        detail_walk.main()
    except Exception:
        pass
    finally:
        detail_walk.IN_WALK = old_in
        detail_walk.OUT_WALK = old_out


def run(args: argparse.Namespace) -> dict[str, Any]:
    t0 = time.time()
    start, phase1_result = delayed.find_candidate(args.phase1_expansions)
    phase1_id = start["_id"]
    accept, rebuild, active = accept_factory()
    heap: list[tuple[tuple[int, ...], int, int]] = []
    seq = 0

    def push(ent: dict[str, Any]) -> None:
        nonlocal seq
        seq += 1
        heapq.heappush(heap, (priority(ent), seq, ent["_id"]))

    accept(start)
    push(start)

    rows = []
    expanded = 0
    generated_total = 0
    accepted_total = 1
    goals: list[dict[str, Any]] = []
    best_goal: dict[str, Any] | None = None
    while heap and expanded < args.max_expansions:
        _prio, _seq, ent_id = heapq.heappop(heap)
        ent = active.get(ent_id)
        if ent is None:
            continue
        expanded += 1
        if p9.goal(ent):
            continue
        edges = generate_atomic_edges(ent, args.max_targets, args.max_iter, args.edge_limit)
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
            heap = []
            for kept_ent in kept:
                push(kept_ent)

        if expanded % args.report_every == 0 or accepted_now or any(p9.goal(e) for e in edges):
            entries = list(active.values())
            goals = rg.best_goals(entries)
            if goals:
                best_goal = goals[0]
            stat_done = [e for e in entries if e["atk"] >= 27 and e["def"] >= 27]
            redkey_ready = [e for e in stat_done if e["rk"] < 1 and e["yk"] >= 1 and auto.redkey_survival_deficit(e) == 0]
            rk_entries = [e for e in entries if e["rk"] >= 1]
            row = {
                "expanded": expanded,
                "edges": len(edges),
                "accepted": accepted_now,
                "entries": len(entries),
                "goals": len(goals),
                "stat_done": len(stat_done),
                "redkey_ready": len(redkey_ready),
                "rk_entries": len(rk_entries),
                "best_goal": compact(goals[0]) if goals else None,
                "best_entry": compact(sorted(entries, key=priority)[0]) if entries else None,
            }
            rows.append(row)
            print(
                f"expand {expanded}: edges={len(edges)} accepted={accepted_now} active={len(entries)} "
                f"stat27={len(stat_done)} redkeyReady={len(redkey_ready)} rk={len(rk_entries)} goals={len(goals)}",
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
        "# Post-9 Atomic Resource Dijkstra",
        "",
        f"- elapsed: {data['elapsed']:.1f}s",
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
            f"rgScore={b['resource_group_score']} oldScore={b['old_score']}"
        )
    lines.extend([
        "",
        "## Top Goals",
        "",
        "| # | stock | rgScore | oldScore | state | last action |",
        "|---:|---:|---:|---:|---|---|",
    ])
    for idx, row in enumerate(data["top_goals"], 1):
        lines.append(
            f"| {idx} | {row['stock']} | {row['resource_group_score']} | {row['old_score']} | "
            f"HP={row['hp']} ATK={row['atk']} DEF={row['def']} YK={row['yk']} BK={row['bk']} RK={row['rk']} "
            f"dmg={row['dmg']} door={row['yd']}/{row['bd']}/{row['rd']} | {row['last_action']} via={'+'.join(row.get('via_targets', []))} |"
        )
    lines.extend(["", "## Search Progress", ""])
    if data.get("mode") == "beam":
        lines.extend([
            "| stage | round | sources | new | entries | max ATK/DEF | goals | best |",
            "|---|---:|---:|---:|---:|---:|---:|---|",
        ])
        for row in data["rows"]:
            best = row.get("best")
            best_text = "-"
            if best:
                best_text = (
                    f"HP={best['hp']} ATK={best['atk']} DEF={best['def']} "
                    f"dmg={best['dmg']} door={best['yd']}/{best['bd']}/{best['rd']} stock={best['stock']}"
                )
            lines.append(
                f"| {row['stage']} | {row['round']} | {row['sources']} | {row['new']} | "
                f"{row['entries']} | {row.get('max_atk', '-')}/{row.get('max_def', '-')} | {row['goals']} | {best_text} |"
            )
    else:
        lines.extend([
            "| expanded | edges | accepted | entries | 27/27 | redkey ready | rk | goals | best goal |",
            "|---:|---:|---:|---:|---:|---:|---:|---:|---|",
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
                f"{row['stat_done']} | {row['redkey_ready']} | {row['rk_entries']} | {row['goals']} | {best_text} |"
            )
    lines.extend([
        "",
        "## Top Frontier",
        "",
        "| # | state | kind | last action |",
        "|---:|---|---|---|",
    ])
    for idx, row in enumerate(data["top_entries"], 1):
        lines.append(
            f"| {idx} | HP={row['hp']} ATK={row['atk']} DEF={row['def']} YK={row['yk']} BK={row['bk']} RK={row['rk']} "
            f"dmg={row['dmg']} door={row['yd']}/{row['bd']}/{row['rd']} stock={row['stock']} | "
            f"{row['edge_kind']} | {row['last_action']} via={'+'.join(row.get('via_targets', []))} |"
        )
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")


def stage_goal(name: str, ent: dict[str, Any]) -> bool:
    if name == "stat27":
        return ent["atk"] >= 27 and ent["def"] >= 27
    if name == "redkey":
        return ent["rk"] >= 1
    if name == "boss":
        return p9.goal(ent)
    raise ValueError(name)


def stage_priority(name: str, ent: dict[str, Any]) -> tuple[int, ...]:
    via = set(ent.get("_via_targets", []))
    via_stat_rank = 0 if "blueGem" in via else 1 if "redGem" in via else 2
    via_chain_rank = (
        0 if via & {"blueGem", "redGem"}
        else 1 if "upFloor" in via
        else 2 if "blueKey" in via
        else 3
    )
    chain_kind_rank = (
        0 if ent.get("_edge_kind") in {"potion", "key", "other"} and via_chain_rank == 0 else 1
    )
    if name == "stat27":
        mt10_gap = max(0, 1 - ent["bk"]) if p9.needs_mt10_for_stats(ent) or p9.stat_deficit(ent) <= 2 else 0
        return (
            p9.stat_deficit(ent),
            via_chain_rank,
            chain_kind_rank,
            ent.get("_bd", 0),
            ent.get("_yd", 0),
            ent.get("_dmg", 0),
            -min(ent["def"], 27),
            -min(ent["atk"], 27),
            mt10_gap,
            0 if "MT10" in ent.get("collected", {}) else 1 if p9.stat_deficit(ent) <= 2 else 0,
            via_stat_rank,
            rg.resource_group_score(ent),
            -ent["hp"],
        )
    if name == "redkey":
        return (
            0 if ent["rk"] >= 1 else 1,
            0 if "redKey" in via else 1,
            auto.redkey_survival_deficit(ent) if ent["rk"] < 1 else 0,
            max(0, 1 - ent["yk"]) if ent["rk"] < 1 else 0,
            rg.resource_group_score(ent),
            ent.get("_dmg", 0),
            ent.get("_yd", 0),
            ent.get("_bd", 0),
            -ent["hp"],
        )
    if name == "boss":
        return (
            0 if p9.goal(ent) else 1,
            p9.boss_survival_deficit(ent),
            rg.resource_group_score(ent),
            ent.get("_dmg", 0),
            ent.get("_yd", 0),
            ent.get("_bd", 0),
            -ent["hp"],
        )
    raise ValueError(name)


def trim_stage(entries: list[dict[str, Any]], limit: int, stage: str) -> list[dict[str, Any]]:
    filtered = auto.pareto_filter(entries)
    goals = [e for e in filtered if stage_goal(stage, e)]
    if len(filtered) <= limit:
        return sorted(filtered, key=lambda e: stage_priority(stage, e))

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

    add(sorted(goals, key=lambda e: stage_priority(stage, e)), max(20, limit // 4))

    buckets: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for ent in filtered:
        buckets[(
            min(ent["atk"], 27),
            min(ent["def"], 27),
            min(ent["yk"], 5),
            min(ent["bk"], 2),
            ent["rk"],
            "MT10" in ent.get("collected", {}),
            stage,
        )].append(ent)
    heads = []
    for bucket in buckets.values():
        heads.extend(sorted(bucket, key=lambda e: stage_priority(stage, e))[:3])
    add(sorted(heads, key=lambda e: stage_priority(stage, e)), max(80, limit // 2))
    if stage in {"stat27", "redkey"}:
        chain_buckets: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
        for ent in filtered:
            via = set(ent.get("_via_targets", []))
            if stage == "stat27" and not (via & {"redGem", "blueGem", "blueKey", "upFloor"}):
                continue
            if stage == "redkey" and "redKey" not in via:
                continue
            chain_buckets[stage_bucket_key(ent, stage)].append(ent)
        chain_heads = []
        for bucket in chain_buckets.values():
            chain_heads.extend(sorted(bucket, key=lambda e: stage_priority(stage, e))[:2])
        add(sorted(chain_heads, key=lambda e: stage_priority(stage, e)), max(80, limit // 2))
    add(sorted(filtered, key=lambda e: stage_priority(stage, e)), limit)
    return chosen[:limit]


def stage_bucket_key(ent: dict[str, Any], stage: str) -> tuple[Any, ...]:
    mt1 = auto.collected_for(ent, "MT1")
    mt3 = auto.collected_for(ent, "MT3")
    mt4 = auto.collected_for(ent, "MT4")
    mt5 = auto.collected_for(ent, "MT5")
    mt6 = auto.collected_for(ent, "MT6")
    mt7 = auto.collected_for(ent, "MT7")
    mt8 = auto.collected_for(ent, "MT8")
    mt9 = auto.collected_for(ent, "MT9")
    mt10 = auto.collected_for(ent, "MT10")
    return (
        stage,
        min(ent["atk"], 27),
        min(ent["def"], 27),
        min(ent["yk"], 5),
        min(ent["bk"], 2),
        ent["rk"],
        "MT10" in ent.get("collected", {}),
        tuple(sorted(ent.get("_via_targets", []))),
        ent.get("_edge_kind", "-"),
        (7, 3) in mt1,
        (7, 4) in mt1,
        (1, 9) in mt3,
        (2, 8) in mt3,
        (2, 9) in mt3,
        (2, 1) in mt3,
        (3, 11) in mt4,
        (1, 9) in mt5,
        (3, 9) in mt5,
        (4, 9) in mt6,
        (9, 1) in mt6,
        (3, 1) in mt7,
        (5, 10) in mt7,
        (5, 11) in mt7,
        (4, 10) in mt8,
        (5, 11) in mt8,
        (10, 2) in mt8,
        (2, 10) in mt9,
        (2, 6) in mt10,
        (10, 6) in mt10,
    )


def select_stage_sources(entries: list[dict[str, Any]], stage: str, limit: int) -> list[dict[str, Any]]:
    if limit <= 0 or len(entries) <= limit:
        return sorted(entries, key=lambda e: stage_priority(stage, e))
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

    ranked = sorted(entries, key=lambda e: stage_priority(stage, e))
    add(ranked, max(2, limit // 3))
    if stage == "stat27":
        add(
            sorted(
                [
                    e for e in entries
                    if set(e.get("_via_targets", [])) & {"redGem", "blueGem", "blueKey", "upFloor"}
                ],
                key=lambda e: (
                    p9.stat_deficit(e),
                    0 if set(e.get("_via_targets", [])) & {"redGem", "blueGem"} else 1 if "upFloor" in e.get("_via_targets", []) else 2,
                    e.get("_dmg", 0),
                    e.get("_yd", 0),
                    e.get("_bd", 0),
                    -e["yk"],
                    -e["bk"],
                    -e["hp"],
                ),
            ),
            max(4, limit // 3),
        )
        add(
            sorted(
                entries,
                key=lambda e: (
                    -(min(e["atk"], 27) + min(e["def"], 27)),
                    -min(e["def"], 27),
                    -min(e["atk"], 27),
                    -e["bk"],
                    -e["yk"],
                    0 if "MT10" in e.get("collected", {}) else 1,
                    e.get("_dmg", 0),
                    e.get("_yd", 0),
                    e.get("_bd", 0),
                    -e["hp"],
                ),
            ),
            max(2, limit // 4),
        )
        add(
            sorted(
                entries,
                key=lambda e: (
                    -min(e["atk"], 27),
                    -min(e["def"], 27),
                    -e["bk"],
                    -e["yk"],
                    0 if "MT10" in e.get("collected", {}) else 1,
                    e.get("_dmg", 0),
                    -e["hp"],
                ),
            ),
            max(1, limit // 6),
        )
        add(
            sorted(
                entries,
                key=lambda e: (
                    -min(e["def"], 27),
                    -min(e["atk"], 27),
                    -e["bk"],
                    -e["yk"],
                    0 if "MT10" in e.get("collected", {}) else 1,
                    e.get("_dmg", 0),
                    -e["hp"],
                ),
            ),
            max(1, limit // 6),
        )
    elif stage == "redkey":
        add(
            sorted(
                [e for e in entries if "redKey" in e.get("_via_targets", [])],
                key=lambda e: (
                    0 if e["rk"] >= 1 else 1,
                    auto.redkey_survival_deficit(e) if e["rk"] < 1 else 0,
                    e.get("_dmg", 0),
                    e.get("_yd", 0),
                    e.get("_bd", 0),
                    -e["yk"],
                    -e["hp"],
                ),
            ),
            max(4, limit // 3),
        )

    buckets: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for ent in entries:
        buckets[stage_bucket_key(ent, stage)].append(ent)
    heads = [sorted(bucket, key=lambda e: stage_priority(stage, e))[0] for bucket in buckets.values()]
    add(sorted(heads, key=lambda e: stage_priority(stage, e)), limit)
    add(ranked, limit)
    return chosen[:limit]


def run_beam_stage(
    name: str,
    starts: list[dict[str, Any]],
    rounds: int,
    entry_limit: int,
    source_limit: int,
    max_targets: int,
    max_iter: int,
    edge_limit: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    entries = trim_stage(starts, entry_limit, name)
    rows: list[dict[str, Any]] = []
    for round_no in range(1, rounds + 1):
        sources = select_stage_sources(entries, name, source_limit)
        new_results: list[dict[str, Any]] = []
        for ent in sources:
            if name != "boss" and stage_goal(name, ent):
                continue
            new_results.extend(generate_atomic_edges(ent, max_targets, max_iter, edge_limit))
        if not new_results:
            break
        entries = trim_stage(entries + new_results, entry_limit, name)
        goals = [e for e in entries if stage_goal(name, e)]
        best_goal = sorted(goals, key=lambda e: stage_priority(name, e))[0] if goals else None
        max_stats = max((e["atk"], e["def"], e["hp"], e.get("_dmg", 0)) for e in entries)
        rows.append({
            "stage": name,
            "round": round_no,
            "sources": len(sources),
            "new": len(new_results),
            "entries": len(entries),
            "goals": len(goals),
            "max_atk": max_stats[0],
            "max_def": max_stats[1],
            "best": compact(best_goal) if best_goal else None,
            "best_entry": compact(entries[0]) if entries else None,
        })
        print(
            f"{name} round {round_no}: sources={len(sources)} new={len(new_results)} "
            f"entries={len(entries)} goals={len(goals)} max={max_stats[0]}/{max_stats[1]}",
            flush=True,
        )
        if best_goal:
            print(f"  best {state_text(best_goal)} stock={rg.final_resource_stock(best_goal)}", flush=True)
    return entries, rows


def run_incremental_stat(
    starts: list[dict[str, Any]],
    rounds_per_step: int,
    entry_limit: int,
    source_limit: int,
    carry_limit: int,
    bridge_carry_limit: int,
    max_targets: int,
    max_iter: int,
    edge_limit: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    entries = trim_stage(starts, entry_limit, "stat27")
    rows: list[dict[str, Any]] = []
    step_no = 0
    while entries and not any(stage_goal("stat27", e) for e in entries):
        step_no += 1
        base_deficit = min(p9.stat_deficit(e) for e in entries)
        improved: list[dict[str, Any]] = []
        for round_no in range(1, rounds_per_step + 1):
            sources = select_stage_sources(entries, "stat27", source_limit)
            new_results: list[dict[str, Any]] = []
            for ent in sources:
                new_results.extend(generate_atomic_edges(ent, max_targets, max_iter, edge_limit))
            if not new_results:
                break
            entries = trim_stage(entries + new_results, entry_limit, "stat27")
            improved = [e for e in entries if p9.stat_deficit(e) < base_deficit]
            goals = [e for e in entries if stage_goal("stat27", e)]
            max_stats = max((e["atk"], e["def"], e["hp"], e.get("_dmg", 0)) for e in entries)
            best_goal = sorted(goals or improved, key=lambda e: stage_priority("stat27", e))[0] if (goals or improved) else None
            rows.append({
                "stage": f"stat+{step_no}",
                "round": round_no,
                "sources": len(sources),
                "new": len(new_results),
                "entries": len(entries),
                "goals": len(goals),
                "max_atk": max_stats[0],
                "max_def": max_stats[1],
                "best": compact(best_goal) if best_goal else None,
                "best_entry": compact(entries[0]) if entries else None,
            })
            print(
                f"stat+{step_no} round {round_no}: baseDef={base_deficit} sources={len(sources)} "
                f"new={len(new_results)} entries={len(entries)} improved={len(improved)} "
                f"goals={len(goals)} max={max_stats[0]}/{max_stats[1]}",
                flush=True,
            )
            if goals:
                return entries, rows
            if improved:
                carry = sorted(improved, key=lambda e: stage_priority("stat27", e))[:carry_limit]
                bridge: list[dict[str, Any]] = []
                if bridge_carry_limit > 0:
                    bridge = [
                        e for e in entries
                        if p9.stat_deficit(e) == base_deficit
                        and (
                            e.get("_edge_kind") in {"key", "potion"}
                            or e.get("_delta_yk", 0) > 0
                            or e.get("_delta_bk", 0) > 0
                            or set(e.get("_via_targets", [])) & {"redGem", "blueGem", "blueKey", "upFloor"}
                        )
                    ]
                    bridge = sorted(
                        bridge,
                        key=lambda e: (
                            e.get("_bd", 0),
                            e.get("_yd", 0),
                            e.get("_dmg", 0),
                            -e["yk"],
                            -e["bk"],
                            -e["hp"],
                            rg.resource_group_score(e),
                        ),
                    )[:bridge_carry_limit]
                entries = trim_stage(
                    carry + bridge,
                    entry_limit,
                    "stat27",
                )
                break
        else:
            break
        if not improved:
            break
        if step_no > 16:
            break
    return entries, rows


def run_beam(args: argparse.Namespace) -> dict[str, Any]:
    t0 = time.time()
    start, phase1_result = delayed.find_candidate(args.phase1_expansions)
    phase1_id = start["_id"]
    all_rows: list[dict[str, Any]] = []

    if args.incremental_stat:
        stat_entries, rows = run_incremental_stat(
            [start],
            args.stat_rounds,
            args.entry_limit,
            args.source_limit,
            args.carry_limit,
            args.bridge_carry_limit,
            args.max_targets,
            args.max_iter,
            args.edge_limit,
        )
    else:
        stat_entries, rows = run_beam_stage(
            "stat27",
            [start],
            args.stat_rounds,
            args.entry_limit,
            args.source_limit,
            args.max_targets,
            args.max_iter,
            args.edge_limit,
        )
    all_rows.extend(rows)
    stat_goals = sorted([e for e in stat_entries if stage_goal("stat27", e)], key=lambda e: stage_priority("stat27", e))

    redkey_entries: list[dict[str, Any]] = []
    boss_entries: list[dict[str, Any]] = []
    if stat_goals:
        redkey_entries, rows = run_beam_stage(
            "redkey",
            stat_goals[: args.carry_limit],
            args.redkey_rounds,
            args.entry_limit,
            args.source_limit,
            args.max_targets,
            args.max_iter,
            args.edge_limit,
        )
        all_rows.extend(rows)
        redkey_goals = sorted([e for e in redkey_entries if stage_goal("redkey", e)], key=lambda e: stage_priority("redkey", e))
    else:
        redkey_goals = []

    if redkey_goals:
        boss_entries, rows = run_beam_stage(
            "boss",
            redkey_goals[: args.carry_limit],
            args.boss_rounds,
            args.entry_limit,
            args.source_limit,
            args.max_targets,
            args.max_iter,
            args.edge_limit,
        )
        all_rows.extend(rows)

    goals = rg.best_goals(boss_entries)
    best = goals[0] if goals else None
    if best:
        write_walk(best, phase1_id)
    top_entries = sorted((boss_entries or redkey_entries or stat_entries), key=lambda e: priority(e))[:20]
    return {
        "elapsed": time.time() - t0,
        "mode": "beam",
        "phase1_elapsed": phase1_result.get("elapsed"),
        "start": compact(start),
        "expanded": sum(r["sources"] for r in all_rows),
        "generated_total": sum(r["new"] for r in all_rows),
        "accepted_total": 0,
        "entry_count": len(boss_entries or redkey_entries or stat_entries),
        "goal_count": len(goals),
        "best": compact(best) if best else None,
        "top_goals": [compact(e) for e in goals[:10]],
        "top_entries": [compact(e) for e in top_entries],
        "rows": all_rows,
        "stage_counts": {
            "stat_goals": len(stat_goals),
            "redkey_goals": len(redkey_goals),
            "boss_goals": len(goals),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["dijkstra", "beam"], default="dijkstra")
    parser.add_argument("--phase1-expansions", type=int, default=300)
    parser.add_argument("--max-expansions", type=int, default=260)
    parser.add_argument("--entry-limit", type=int, default=520)
    parser.add_argument("--source-limit", type=int, default=12)
    parser.add_argument("--carry-limit", type=int, default=60)
    parser.add_argument("--bridge-carry-limit", type=int, default=0)
    parser.add_argument("--max-targets", type=int, default=0)
    parser.add_argument("--max-iter", type=int, default=500000)
    parser.add_argument("--edge-limit", type=int, default=28)
    parser.add_argument("--report-every", type=int, default=25)
    parser.add_argument("--stat-rounds", type=int, default=16)
    parser.add_argument("--redkey-rounds", type=int, default=8)
    parser.add_argument("--boss-rounds", type=int, default=8)
    parser.add_argument("--incremental-stat", action=argparse.BooleanOptionalAction, default=True)
    args = parser.parse_args()
    data = run_beam(args) if args.mode == "beam" else run(args)
    write_outputs(data)
    print(f"wrote {OUT_JSON}")
    print(f"wrote {OUT_MD}")
    if data.get("best"):
        print(f"wrote {OUT_WALK}")
        if os.path.exists(OUT_WALK_DETAIL):
            print(f"wrote {OUT_WALK_DETAIL}")


if __name__ == "__main__":
    main()
