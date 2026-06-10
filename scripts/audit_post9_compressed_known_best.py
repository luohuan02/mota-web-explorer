#!/usr/bin/env python3
"""Audit whether the verified post-9 route exists in the compressed graph."""

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

import continue_delayed_phase1_with_post9_resource as delayed
import post9_compressed_resource_dijkstra as compressed
import post9_gem_supply_search as gem


Selector = Callable[[dict[str, Any]], bool]


def starts(text: str) -> Selector:
    return lambda edge: edge.get("_last_action", "").startswith(text)


def kind(name: str) -> Selector:
    return lambda edge: edge.get("_edge_kind") == name


STEPS: list[tuple[str, Selector]] = [
    ("4F x3y11 yellow key", starts("MT4 x3y11 ")),
    ("6F free potions", starts("MT6 x8y11 ")),
    ("7F red gem", starts("MT7 x3y1 ")),
    ("6F blue gem", starts("MT6 x4y9 ")),
    ("3F blue gem", starts("MT3 x1y1 ")),
    ("8F red/blue group", starts("MT8 x4y10 ")),
    ("1F red/blue group", starts("MT1 x7y3 ")),
    ("3F red gem", starts("MT3 x1y9 ")),
    ("5F blue gem", starts("MT5 x1y9 ")),
    ("4F blue key", starts("MT4 x1y2 ")),
    ("9F to 10F progress", kind("progress")),
    ("10F blue gem", starts("MT10 x2y6 ")),
    ("6F yellow key", starts("MT6 x9y1 ")),
    ("7F left yellow keys", starts("MT7 x5y10 ")),
    ("10F red gem", starts("MT10 x10y6 ")),
    ("7F right potion/keys", starts("MT7 x9y9 ")),
    ("10F blue potion", starts("MT10 x11y11 ")),
    ("8F red key", starts("MT8 x9y1 ")),
    ("1F blue potion", starts("MT1 x10y11 ")),
    ("7F blue potion", starts("MT7 x7y11 ")),
    ("10F boss", kind("boss")),
]


def main() -> None:
    ent, _phase1 = delayed.find_candidate(300)
    accept, _rebuild, _active = compressed.accept_factory()
    accept(ent)
    states = [ent]
    print(f"start: {compressed.state_text(ent)}")
    for index, (name, selector) in enumerate(STEPS, 1):
        edges = compressed.generate_compressed_edges(
            ent,
            max_targets=0,
            max_iter=500000,
            edge_limit=0,
            priority_mode="dynamic",
        )
        matches = [edge for edge in edges if selector(edge)]
        if not matches:
            print(f"FAILED {index}. {name}")
            for edge in edges:
                print(f"  candidate: {edge.get('_last_action')} | {compressed.state_text(edge)}")
            raise SystemExit(1)
        edge = min(matches, key=compressed.make_priority("dynamic"))
        accepted = accept(edge)
        print(
            f"{index:02d}. {name}: accepted={accepted} "
            f"{compressed.state_text(edge)} | {edge.get('_last_action')}"
        )
        ent = edge
        states.append(ent)
    final_dmg = ent.get("_dmg", 0)
    for index, state in enumerate(states):
        optimistic_total = state.get("_dmg", 0) + gem.optimistic_remaining_damage_lower_bound(state)
        if optimistic_total > final_dmg:
            raise RuntimeError(
                f"unsafe optimistic lower bound at step {index}: "
                f"{optimistic_total} > known final {final_dmg}"
            )
    print("lower-bound audit: OK")
    print(f"final: {compressed.state_text(ent)}")


if __name__ == "__main__":
    main()
