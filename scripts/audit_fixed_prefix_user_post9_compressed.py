#!/usr/bin/env python3
"""Audit the verified user post-9 route through the compressed resource graph."""

from __future__ import annotations

import os
import sys
from typing import Any, Callable


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.chdir(ROOT)

from scripts import post9_compressed_resource_dijkstra as compressed
from scripts import post9_gem_supply_search as gem
from scripts import post9_resource_group_search as resource


Selector = Callable[[dict[str, Any]], bool]


def starts(text: str) -> Selector:
    return lambda edge: edge.get("_last_action", "").startswith(text)


def kind(name: str) -> Selector:
    return lambda edge: edge.get("_edge_kind") == name


STEPS: list[tuple[str, str, Selector]] = [
    ("backbone", "6F blue gem", starts("MT6 x4y9 ")),
    ("backbone", "3F blue gem", starts("MT3 x1y1 ")),
    ("backbone", "8F red/blue gems", starts("MT8 x4y10 ")),
    ("backbone", "1F red/blue gems", starts("MT1 x7y3 ")),
    ("backbone", "3F red gem", starts("MT3 x1y9 ")),
    ("backbone", "5F blue gem", starts("MT5 x1y9 ")),
    ("recovery", "4F blue key", starts("MT4 x1y2 ")),
    ("backbone", "9F to 10F progress", kind("progress")),
    ("backbone", "10F blue gem", starts("MT10 x2y6 ")),
    ("recovery", "7F upper yellow keys", starts("MT7 x9y1 ")),
    ("recovery", "7F right potion/keys", starts("MT7 x9y9 ")),
    ("recovery", "7F lower yellow keys", starts("MT7 x5y10 ")),
    ("backbone", "10F red gem", starts("MT10 x10y6 ")),
    ("recovery", "10F blue potion", starts("MT10 x11y11 ")),
    ("recovery", "7F blue potion", starts("MT7 x7y11 ")),
    ("redkey", "8F red key", kind("redkey")),
    ("recovery", "1F blue potion", starts("MT1 x10y11 ")),
    ("recovery", "1F red potion", starts("MT1 x1y3 ")),
    ("boss", "10F boss", kind("boss")),
]


def pick(edges: list[dict[str, Any]], selector: Selector, label: str) -> dict[str, Any]:
    matches = [edge for edge in edges if selector(edge)]
    if not matches:
        print(f"FAILED: {label}")
        for edge in edges:
            print(f"  candidate: {edge.get('_last_action')} | {compressed.state_text(edge)}")
        raise SystemExit(1)
    return min(matches, key=compressed.make_priority("dynamic"))


def edges_for(ent: dict[str, Any], role: str) -> list[dict[str, Any]]:
    if role == "backbone":
        return gem.backbone_edges(
            ent,
            target_limit=0,
            edge_limit=0,
            bridge_depth=3,
            bridge_width=10,
            max_iter=500000,
        )
    if role == "recovery":
        return gem.role_edges(ent, role, target_limit=0, edge_limit=0, max_iter=500000)
    return gem.final_transition_edges(
        ent,
        role,
        bridge_depth=3,
        bridge_width=10,
        max_iter=500000,
    )


def main() -> None:
    ent, _phase1 = gem.replay_fixed_prefix_candidate()
    ent = gem.saturate_initial_free_resources(ent, 500000)
    states = [ent]
    print(f"start: {compressed.state_text(ent)}")
    for index, (role, label, selector) in enumerate(STEPS, 1):
        ent = pick(edges_for(ent, role), selector, label)
        states.append(ent)
        print(
            f"{index:02d}. {label}: {compressed.state_text(ent)} "
            f"| {ent.get('_last_action')}"
        )
    final_dmg = ent.get("_dmg", 0)
    for index, state in enumerate(states):
        optimistic_total = state.get("_dmg", 0) + gem.optimistic_remaining_damage_lower_bound(state)
        if optimistic_total > final_dmg:
            raise RuntimeError(
                f"unsafe optimistic lower bound at step {index}: "
                f"{optimistic_total} > known final {final_dmg}"
            )
    print("lower-bound audit: OK")
    print(
        f"final: {compressed.state_text(ent)} "
        f"stock={resource.final_resource_stock(ent)}"
    )


if __name__ == "__main__":
    main()
