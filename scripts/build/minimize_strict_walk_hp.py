#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


POTION_EIDS = {"redPotion", "bluePotion"}


def potion_gain(step: dict[str, Any]) -> int:
    return int(step["after"]["hp"]) - int(step["before"]["hp"])


def optimize(steps: list[dict[str, Any]]) -> tuple[list[int], int]:
    states: dict[int, list[int]] = {0: []}
    for idx, step in enumerate(steps, 1):
        next_states: dict[int, list[int]] = {}
        is_potion = step.get("action") == "拾取" and step.get("eid") in POTION_EIDS
        gain = potion_gain(step) if is_potion else 0
        for removed, removed_steps in states.items():
            keep_removed = removed
            keep_hp = int(step["after"]["hp"]) - keep_removed
            if keep_hp > 0:
                best = next_states.get(keep_removed)
                if best is None or len(best) > len(removed_steps):
                    next_states[keep_removed] = removed_steps
            if is_potion:
                drop_removed = removed + gain
                drop_hp = int(step["after"]["hp"]) - drop_removed
                if drop_hp > 0:
                    cand = removed_steps + [idx]
                    best = next_states.get(drop_removed)
                    if best is None or len(best) > len(cand):
                        next_states[drop_removed] = cand
        states = next_states
        if not states:
            raise RuntimeError(f"no feasible states remain at step {idx}")
    best_removed = max(states)
    return states[best_removed], best_removed


def apply_removals(payload: dict[str, Any], removed_steps: list[int]) -> dict[str, Any]:
    removed_set = set(removed_steps)
    out = json.loads(json.dumps(payload))
    removed_total = 0
    new_steps: list[dict[str, Any]] = []
    removed_rows: list[dict[str, Any]] = []
    for idx, step in enumerate(payload["steps"], 1):
        gain = potion_gain(step) if step.get("action") == "拾取" and step.get("eid") in POTION_EIDS else 0
        if idx in removed_set:
            removed_rows.append(
                {
                    "index": idx,
                    "floor": step["floor"],
                    "pos": step["pos"],
                    "eid": step["eid"],
                    "hp_gain": gain,
                    "note": step.get("note", ""),
                }
            )
            removed_total += gain
            continue
        row = json.loads(json.dumps(step))
        row["before"]["hp"] -= removed_total
        row["after"]["hp"] -= removed_total
        new_steps.append(row)
    out["steps"] = new_steps
    if "final" in out and out["final"]:
        out["final"]["hp"] -= removed_total
    if "expected_final" in out and out["expected_final"]:
        out["expected_final"]["hp"] -= removed_total
    out["derived_from"] = out.get("derived_from") or out.get("source_walk") or ""
    out["hp_minimized_from"] = payload.get("derived_from") or payload.get("source_walk") or payload.get("source") or ""
    out["removed_potions"] = removed_rows
    out["removed_hp_total"] = removed_total
    out["minimized_final_hp"] = out.get("expected_final", out.get("final", {})).get("hp")
    if "state_text" in out and out.get("final"):
        parts = str(out["state_text"]).split()
        if parts:
            parts[0] = f"HP={out['final']['hp']}"
            out["state_text"] = " ".join(parts)
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--walk", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    payload = json.loads(args.walk.read_text(encoding="utf-8"))
    removed_steps, removed_total = optimize(payload["steps"])
    result = apply_removals(payload, removed_steps)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    final_state = result.get("expected_final") or result.get("final") or {}
    print(f"removed_steps={removed_steps}")
    print(f"removed_hp_total={removed_total}")
    print(f"final_hp={final_state.get('hp')}")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
