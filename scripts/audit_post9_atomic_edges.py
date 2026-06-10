#!/usr/bin/env python3
"""Audit atomic post-9 edge generation from known good continuation states."""

from __future__ import annotations

import argparse
import os
import sys


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.chdir(ROOT)

from scripts import gen_delayed_phase1_detailed_walk as detail_walk
from scripts import post9_atomic_resource_dijkstra as atomic
from scripts import post9_action_search as p9
from src.solver import gen_walkthrough as gw


def state_text(ent: dict) -> str:
    return (
        f"HP={ent['hp']} ATK={ent['atk']} DEF={ent['def']} "
        f"YK={ent['yk']} BK={ent['bk']} RK={ent['rk']} "
        f"dmg={ent.get('_dmg', 0)} door={ent.get('_yd', 0)}/{ent.get('_bd', 0)}/{ent.get('_rd', 0)} "
        f"deficit={p9.stat_deficit(ent)}"
    )


def load_chain_from_walk(path: str) -> list[dict]:
    old_in = detail_walk.IN_WALK
    try:
        detail_walk.IN_WALK = path
        start_state, segments = detail_walk.parse_compact_walk()
    finally:
        detail_walk.IN_WALK = old_in

    gw._entry_store.clear()
    gw._next_id[0] = 1
    collected = gw.initial_collected_state()
    root = gw._make_result(
        start_state["hp"],
        start_state["yk"],
        start_state["bk"],
        start_state["rk"],
        start_state["atk"],
        start_state["def"],
        collected,
        None,
        None,
        dmg_cost=0,
    )
    root["_dmg"] = start_state["dmg"]
    root["_yd"] = start_state["yd"]
    root["_bd"] = start_state["bd"]
    root["_rd"] = start_state["rd"]
    gw._entry_store[root["_id"]].update({
        "_dmg": root["_dmg"],
        "_yd": root["_yd"],
        "_bd": root["_bd"],
        "_rd": root["_rd"],
        "_last_action": "walk start",
    })

    chain = [root]
    prev = start_state
    parent = root
    for seg in segments:
        steps, vis = detail_walk.reconstruct_segment(dict(prev), collected, seg)
        if steps is None or vis is None:
            raise RuntimeError(f"failed to reconstruct segment: {seg['label']}")
        if seg["fid"] == "MT9" and "upFloor" in seg["targets"]:
            collected.setdefault("MT10", frozenset())
        st = seg["state"]
        ent = gw._make_result(
            st["hp"],
            st["yk"],
            st["bk"],
            st["rk"],
            st["atk"],
            st["def"],
            dict(collected),
            parent["_id"],
            (seg["fid"], seg["targets"], seg["flyback"]),
            dmg_cost=st["dmg"] - prev["dmg"],
        )
        ent["_dmg"] = st["dmg"]
        ent["_yd"] = st["yd"]
        ent["_bd"] = st["bd"]
        ent["_rd"] = st["rd"]
        ent["_last_action"] = seg["label"]
        gw._entry_store[ent["_id"]].update({
            "_dmg": ent["_dmg"],
            "_yd": ent["_yd"],
            "_bd": ent["_bd"],
            "_rd": ent["_rd"],
            "_last_action": ent["_last_action"],
        })
        chain.append(ent)
        parent = ent
        prev = st
    return chain


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--atk", type=int)
    parser.add_argument("--defense", type=int)
    parser.add_argument("--limit", type=int, default=60)
    parser.add_argument(
        "--walk",
        default=os.path.join("outputs", "walkthroughs", "walkthrough_post9_order_key_red_3f_1f.md"),
    )
    parser.add_argument("--max-targets", type=int, default=0)
    parser.add_argument("--edge-limit", type=int, default=80)
    parser.add_argument("--max-iter", type=int, default=500000)
    parser.add_argument("--probe-redkey", action="store_true")
    args = parser.parse_args()

    chain = load_chain_from_walk(args.walk)

    targets = []
    for ent in chain:
        if args.atk is not None and ent["atk"] != args.atk:
            continue
        if args.defense is not None and ent["def"] != args.defense:
            continue
        targets.append(ent)
    if not targets:
        print("no matching chain states")
        return

    for ent in targets:
        print()
        print(state_text(ent))
        print(ent.get("_last_action") or ent.get("_source") or ent.get("_step_info"))
        if args.probe_redkey:
            red_targets = atomic.auto.item_positions("MT8", "redKey") - atomic.auto.collected_for(ent, "MT8")
            red_edges = atomic.auto.exact_item_edges(ent, "MT8", "redKey", set(red_targets), max_iter=args.max_iter)
            print(f"redKey targets={sorted(red_targets)} edges={len(red_edges)}")
            for red in sorted(red_edges, key=atomic.edge_sort_key)[:10]:
                print(f"  red {state_text(red)} action={red.get('_last_action')}")
        edges = atomic.generate_atomic_edges(ent, args.max_targets, args.max_iter, args.edge_limit)
        ranked = sorted(edges, key=atomic.edge_sort_key)[: args.limit]
        for idx, edge in enumerate(ranked, 1):
            via = "+".join(edge.get("_via_targets", []))
            print(
                f"{idx:02d}. {state_text(edge)} kind={edge.get('_edge_kind')} "
                f"via={via} action={edge.get('_last_action')}"
            )


if __name__ == "__main__":
    main()
