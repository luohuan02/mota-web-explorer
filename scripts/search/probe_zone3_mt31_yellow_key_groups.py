#!/usr/bin/env python3
"""Probe legal positive-net yellow-key groups from the verified MT31 checkpoint.

This is deliberately a small shared-Game search, not a hand-authored route.  A
transition consists only of the floor transporter plus repeated real target
clicks on a remaining yellow key.  ``strict_live_model`` therefore splits any
door, battle, or pickup encountered en route into the same atomic clicks used
by the web replayer.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.solver.game_route import read_json, state_line
from scripts.search.zone3_game_route import Zone3Game


DEFAULT_CHECKPOINT = ROOT / "outputs" / "results" / "zone3_current_2atk1def_mt31_checkpoint.json"
DEFAULT_OUT = ROOT / "outputs" / "results" / "zone3_mt31_yellow_key_group_probe.json"


def init_game(path: Path) -> Zone3Game:
    snapshot = read_json(path)
    g = Zone3Game(snapshot)
    flags = snapshot.get("hero", {}).get("flags", {})
    visited = {fid for fid, value in flags.get("__visited__", {}).items() if value}
    if not visited:
        visited = {f"MT{i}" for i in range(1, int(snapshot["floorId"][2:]) + 1)}
    visited.add(snapshot["floorId"])
    g.visited = visited
    g.state["visited"] = g.visited
    g.strict_live_model = True
    g.auto_flags = {"battle": True, "item": "nopotion", "wall": True}
    return g


def yellow_targets(g: Zone3Game) -> list[tuple[str, int, int]]:
    return sorted(
        (fid, pos[0], pos[1])
        for fid in g.visited
        for pos, block in g.floors[fid].blocks.items()
        if block.kind == "item" and block.eid == "yellowKey"
    )


def remaining_signature(g: Zone3Game) -> tuple[tuple[str, int, int], ...]:
    return tuple(yellow_targets(g))


def click_until_collected(g: Zone3Game, target: tuple[str, int, int], limit: int = 16) -> bool:
    fid, x, y = target
    if fid not in g.visited:
        return False
    try:
        if g.state["floor"] != fid:
            g.fly(fid)
        for _ in range(limit):
            block = g.block_at(fid, (x, y))
            if block is None or block.eid != "yellowKey":
                return True
            before_steps = len(g.steps)
            before_errors = len(g.errors)
            try:
                g.go_to(fid, x, y, f"黄钥匙资源组目标 {fid} x{x}y{y}")
            except Exception:
                # A browser target click cannot route through a closed door or
                # enemy.  Use the loose route only to discover its first
                # blocker, then emit a separate strict click on that blocker.
                del g.errors[before_errors:]
                path = g.path_to(fid, (x, y), strict_click=False)
                if not path:
                    return False
                blocker = next(
                    (pos for pos in path[1:] if g.block_at(fid, pos) is not None),
                    None,
                )
                if blocker is None:
                    return False
                g.go_to(fid, blocker[0], blocker[1],
                        f"资源组前置真实点击，目标 {fid} x{x}y{y}")
            if len(g.steps) == before_steps or len(g.errors) > before_errors:
                return False
    except Exception:
        return False
    block = g.block_at(fid, (x, y))
    return block is None or block.eid != "yellowKey"


def dominates(a: Zone3Game, b: Zone3Game) -> bool:
    sa, sb = a.state, b.state
    fields = ("hp", "atk", "def", "yk", "bk", "rk", "gold")
    return all(sa[k] >= sb[k] for k in fields) and any(sa[k] > sb[k] for k in fields)


def pareto(states: list[Zone3Game], width: int) -> list[Zone3Game]:
    groups: dict[tuple[tuple[str, int, int], ...], list[Zone3Game]] = {}
    for candidate in states:
        bucket = groups.setdefault(remaining_signature(candidate), [])
        if any(dominates(old, candidate) for old in bucket):
            continue
        bucket[:] = [old for old in bucket if not dominates(candidate, old)]
        bucket.append(candidate)
    kept = [g for bucket in groups.values() for g in bucket]
    kept.sort(
        key=lambda g: (
            g.state["yk"], g.state["bk"], g.state["rk"], g.state["hp"],
            g.state["atk"], g.state["def"], g.state["gold"], -len(g.steps),
        ),
        reverse=True,
    )
    return kept[:width]


def compact(g: Zone3Game, start_steps: int) -> dict[str, Any]:
    return {
        "final": g.snapshot(),
        "state": state_line(g.state),
        "remaining_yellow_keys": [list(v) for v in yellow_targets(g)],
        "steps": g.steps[start_steps:],
        "errors": g.errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--depth", type=int, default=5)
    parser.add_argument("--beam", type=int, default=160)
    args = parser.parse_args()

    start = init_game(args.checkpoint)
    start_steps = len(start.steps)
    frontier = [start]
    all_states = [start]
    for depth in range(1, args.depth + 1):
        expanded: list[Zone3Game] = []
        failure_samples: list[str] = []
        for state in frontier:
            for target in yellow_targets(state):
                candidate = copy.deepcopy(state)
                if click_until_collected(candidate, target) and not candidate.errors and candidate.state["hp"] > 0:
                    expanded.append(candidate)
                elif len(failure_samples) < 8:
                    failure_samples.append(f"{target}: {candidate.errors[-1] if candidate.errors else 'no path/progress'}")
        frontier = pareto(expanded, args.beam)
        all_states.extend(frontier)
        best = max((g.state["yk"] for g in frontier), default=start.state["yk"])
        print(f"depth={depth} expanded={len(expanded)} kept={len(frontier)} bestYK={best}")
        if depth == 1 and failure_samples:
            print("failure samples:")
            for sample in failure_samples:
                print(f"  {sample}")
        if not frontier:
            break

    winners = pareto(all_states, args.beam)
    payload = {
        "ok": True,
        "checkpoint": str(args.checkpoint),
        "start": start.snapshot(),
        "initial_yellow_targets": [list(v) for v in yellow_targets(start)],
        "candidate_count": len(winners),
        "candidates": [compact(g, start_steps) for g in winners],
    }
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"best={payload['candidates'][0]['state'] if payload['candidates'] else '-'}")
    print(f"json={args.out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
