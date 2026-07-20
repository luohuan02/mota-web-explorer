#!/usr/bin/env python3
"""Greedily remove costly battles from a fixed Zone-3 skeleton.

Every candidate is accepted only when the complete strict Zone3Game replay
still succeeds and improves final HP.  This is a general skeleton reducer, not
a coordinate skip list; keys, doors, events and reachability are decided by
the same Game replay used to generate the canonical JSON.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.search.zone3_game_route import Zone3Game, run_zone3
from src.solver.game_route import read_json


def replay(checkpoint: Path, payload: dict) -> Zone3Game | None:
    g = Zone3Game(read_json(checkpoint))
    g.strict_live_model = True
    g.auto_flags = {"battle": True, "item": "nopotion", "wall": True}
    for row in payload.get("removed_potions", []):
        pos = row.get("pos") or []
        if len(pos) == 2 and row.get("floor"):
            g.blocked_items.add((row["floor"], int(pos[0]), int(pos[1])))
    try:
        run_zone3(g, [0], walk_data=payload)
    except Exception:
        return None
    return g if not g.errors and g.state["floor"] == "MT41" else None


def costly_battle(step: dict) -> bool:
    return (
        step.get("action") == "击杀"
        and int(step.get("after", {}).get("hp", 0)) < int(step.get("before", {}).get("hp", 0))
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", type=Path, required=True)
    ap.add_argument("--walk", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    payload = json.loads(args.walk.read_text(encoding="utf-8"))
    baseline = replay(args.checkpoint, payload)
    if baseline is None:
        raise SystemExit("baseline replay failed")
    best_hp = int(baseline.state["hp"])
    removed: list[dict] = []
    changed = True
    while changed:
        changed = False
        for idx, step in list(enumerate(payload["steps"])):
            if not costly_battle(step):
                continue
            trial = json.loads(json.dumps(payload))
            candidate = trial["steps"].pop(idx)
            result = replay(args.checkpoint, trial)
            if result is None or int(result.state["hp"]) <= best_hp:
                continue
            best_hp = int(result.state["hp"])
            payload = trial
            removed.append({
                "original_action": candidate.get("action"),
                "floor": candidate.get("floor"),
                "pos": candidate.get("pos"),
                "eid": candidate.get("eid"),
                "old_hp_cost": int(candidate["before"]["hp"]) - int(candidate["after"]["hp"]),
                "new_final_hp": best_hp,
            })
            print(f"accepted {candidate.get('floor')} {candidate.get('pos')} {candidate.get('eid')} -> HP={best_hp}")
            changed = True
            break
    payload["hp_skeleton_optimized"] = True
    payload["removed_costly_battles"] = removed
    payload["optimized_replay_final_hp"] = best_hp
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"removed={len(removed)} final_hp={best_hp} out={args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
