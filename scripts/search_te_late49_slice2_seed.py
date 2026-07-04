#!/usr/bin/env python3
"""Continue the te_late49 slice2 RK=1 intermediate as a single search seed."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import rebuild_te_late49_slice2_candidate as rkseed
import search_zone3_slot26_te_late49_seeded as late49


ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "outputs" / "results" / "te_late49_slice2_seed_continue.json"
OUT_MD = ROOT / "outputs" / "reports" / "te_late49_slice2_seed_continue.md"
OUT_LOG = ROOT / "outputs" / "logs" / "te_late49_slice2_seed_continue_progress.log"


def main() -> int:
    late49.install_late49_guidance()
    parser = argparse.ArgumentParser()
    parser.add_argument("--time-limit-seconds", type=float, default=1800)
    parser.add_argument("--beam", type=int, default=420)
    parser.add_argument("--targets-per-state", type=int, default=72)
    parser.add_argument("--actions-per-state", type=int, default=120)
    parser.add_argument("--max-depth", type=int, default=260)
    parser.add_argument("--max-seeds", type=int, default=1)
    parser.add_argument("--focused-seeds", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--report-interval", type=float, default=120)
    parser.add_argument("--progress-log", type=Path, default=OUT_LOG)
    parser.add_argument("--out-json", type=Path, default=OUT_JSON)
    parser.add_argument("--out-md", type=Path, default=OUT_MD)
    args = parser.parse_args()
    seed = rkseed.rebuild()
    data = late49.seeded.explore_from_seeds(args, [seed])
    late49.write_report(data, args.out_json, args.out_md)
    args.out_json.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {args.out_json}")
    print(f"wrote {args.out_md}")
    if data.get("best_goal"):
        print("best_goal", data["best_goal"]["state_text"])
    else:
        print("best_goal not found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
