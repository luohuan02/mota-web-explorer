#!/usr/bin/env python3
"""Generate best walk artifacts from a local-order-refine result JSON."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.chdir(ROOT)

from scripts import gen_best_current_boss_walk as gen_best
from scripts import local_order_refine_current_best as refine
from scripts import merchant_finalscore_audit as audit
from scripts import compare_merchant_resource_paths as cm
from scripts import run_corrected_phase1_best_boss_until_deadline as runner


DEFAULT_INPUT = os.path.join("outputs", "results", "user_def_before_key_probe_after_mt10_guard.json")


def parse_sequence(items: list[str]) -> list[refine.Action]:
    out: list[refine.Action] = []
    for item in items:
        fid, target = item.split(":", 1)
        out.append((fid, target))
    return out


def replay_from_result(args: argparse.Namespace) -> dict[str, Any]:
    with open(args.input, encoding="utf-8") as f:
        data = json.load(f)
    cm.ensure_merchant_maps()
    seed = runner.load_corrected_best_seed(args)
    audit.install_post9_resource_group_hooks()
    sequence = parse_sequence(data.get("best_sequence") or data.get("sequence") or [])
    replay = refine.replay_sequence(seed, sequence, args.beam)
    best = replay["best_ent"]
    if best is None:
        raise RuntimeError("local refined sequence did not replay to a boss goal")
    record = audit.score_record("current_best", best, source="local order refinement")
    if args.expect_final_score and abs(record["final_score"] - args.expect_final_score) > 1e-9:
        raise RuntimeError(
            f"unexpected final-score: expected={args.expect_final_score} actual={record['final_score']}"
        )
    return {
        "seed": seed,
        "best": best,
        "record": record,
        "search": {
            "goal_count": 1,
            "merchant_goal_count": 1 if record["merchants"] else 0,
            "entry_count": len(replay.get("rows", [])),
            "elapsed": data.get("elapsed", 0),
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=DEFAULT_INPUT)
    parser.add_argument("--state-cache", default=runner.DEFAULT_STATE_CACHE)
    parser.add_argument("--rescore-json", default=runner.DEFAULT_RESCORE_JSON)
    parser.add_argument("--beam", type=int, default=160)
    parser.add_argument("--expect-final-score", type=float, default=1376.5)
    parser.add_argument(
        "--output-walk",
        default=os.path.join("outputs", "walkthroughs", "walkthrough_current_best_boss_bk200_valid.md"),
    )
    parser.add_argument("--best-walk", default=gen_best.DEFAULT_BEST_WALK)
    parser.add_argument("--best-json", default=gen_best.DEFAULT_BEST_JSON)
    parser.add_argument("--guide-walk", default=gen_best.DEFAULT_GUIDE_WALK)
    parser.add_argument("--best-readme", default=gen_best.DEFAULT_README)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = replay_from_result(args)
    gen_best.write_walk(result, args.output_walk)
    gen_best.write_walk(result, args.best_walk)
    gen_best.write_summary(result, args.best_json)
    gen_best.copy_guide_walk(args.guide_walk)
    gen_best.write_best_readme(args.best_readme, result["record"])
    print(f"wrote {args.output_walk}")
    print(f"wrote {args.best_walk}")
    print(f"wrote {args.best_json}")
    print(f"wrote {args.guide_walk}")
    print(f"wrote {args.best_readme}")


if __name__ == "__main__":
    main()
