#!/usr/bin/env python3
"""Search HP-shop timing for the preserve-pickaxe zone-3 route.

The number and cost order of shop purchases stay fixed.  A stat purchase and
an HP purchase may exchange their kinds; every candidate is then replayed by
the strict shared Game.  For successful candidates, the existing potion DP
removes every potion that can be omitted while keeping HP positive at every
canonical step, followed by a second strict replay as proof.
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build.minimize_strict_walk_hp import apply_removals, optimize
from scripts.search.zone3_game_route import Zone3Game, run_zone3
from src.solver.game_route import read_json


def replay(checkpoint: Path, payload: dict) -> Zone3Game | None:
    game = Zone3Game(read_json(checkpoint))
    game.strict_live_model = True
    game.auto_flags = {"battle": True, "item": "nopotion", "wall": True}
    for row in payload.get("removed_potions", []):
        pos = row.get("pos") or []
        if len(pos) == 2 and row.get("floor"):
            game.blocked_items.add((row["floor"], int(pos[0]), int(pos[1])))
    try:
        run_zone3(game, walk_data=payload)
    except Exception:
        return None
    return game if not game.errors and game.state["floor"] == "MT41" else None


def canonical_payload(game: Zone3Game, source: str) -> dict:
    return {
        "ok": True,
        "source": source,
        "final": game.snapshot(),
        "steps": copy.deepcopy(game.steps),
        "errors": [],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", type=Path, required=True)
    ap.add_argument("--walk", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    base = json.loads(args.walk.read_text(encoding="utf-8"))
    shops = [(i, row.get("eid")) for i, row in enumerate(base["steps"])
             if row.get("action") == "商店"]
    stat_shops = [(ordinal, idx, kind) for ordinal, (idx, kind) in enumerate(shops)
                  if kind in {"atk", "def"}]
    hp_shops = [(ordinal, idx) for ordinal, (idx, kind) in enumerate(shops) if kind == "hp"]

    candidates: list[tuple[int, str, dict]] = []
    variants: list[tuple[str, dict]] = [("baseline", copy.deepcopy(base))]
    for stat_ord, stat_idx, stat_kind in stat_shops:
        for hp_ord, hp_idx in hp_shops:
            trial = copy.deepcopy(base)
            trial["steps"][stat_idx]["eid"] = "hp"
            trial["steps"][stat_idx]["note"] = f"HP压缩搜索：与shop#{hp_ord}交换购买类型"
            trial["steps"][hp_idx]["eid"] = stat_kind
            trial["steps"][hp_idx]["note"] = f"HP压缩搜索：恢复shop#{stat_ord}的{stat_kind}"
            variants.append((f"swap-stat{stat_ord}-{stat_kind}-hp{hp_ord}", trial))

    for label, trial in variants:
        first = replay(args.checkpoint, trial)
        if first is None:
            print(label, "route-fail")
            continue
        canonical = canonical_payload(first, label)
        try:
            removed_steps, _removed_hp = optimize(canonical["steps"])
        except RuntimeError:
            print(label, "potion-dp-fail")
            continue
        minimized = apply_removals(canonical, removed_steps)
        proof = replay(args.checkpoint, minimized)
        if proof is None:
            print(label, "minimized-replay-fail")
            continue
        minimized["final"] = proof.snapshot()
        minimized["steps"] = copy.deepcopy(proof.steps)
        minimized["errors"] = []
        hp = int(proof.state["hp"])
        print(label, "HP", hp, "ATK", proof.state["atk"], "DEF", proof.state["def"],
              "YK", proof.state["yk"], "removed", len(removed_steps))
        candidates.append((hp, label, minimized))

    feasible = [row for row in candidates if 0 < row[0] < 50]
    pool = feasible or candidates
    if not pool:
        raise SystemExit("no successful shop-order candidate")
    best = max(pool, key=lambda row: row[0]) if feasible else min(pool, key=lambda row: row[0])
    best[2]["search_label"] = best[1]
    best[2]["search_goal"] = "largest positive HP below 50; otherwise lowest positive HP"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(best[2], ensure_ascii=False, indent=2), encoding="utf-8")
    print("best", best[1], "HP", best[0], "out", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
