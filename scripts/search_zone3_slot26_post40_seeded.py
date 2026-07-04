#!/usr/bin/env python3
"""Seeded Zone-3 search biased for a post-40 HP continuation.

This reuses ``search_zone3_slot26_seeded`` but changes the ordering objective:
40F candidates need enough gold and yellow-key economy to connect to the
41F-50F HP route exactly, with no live-gold tolerance.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SEEDED_PATH = ROOT / "scripts" / "search_zone3_slot26_seeded.py"
OUT_JSON = ROOT / "outputs" / "results" / "zone3_slot26_post40_seeded.json"
OUT_MD = ROOT / "outputs" / "reports" / "zone3_slot26_post40_seeded.md"
OUT_LOG = ROOT / "outputs" / "logs" / "zone3_slot26_post40_seeded_progress.log"


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


seeded = load_module("zone3_post40_seeded_base", SEEDED_PATH)
base = seeded.base
guided = seeded.guided


def _s(g: Any) -> dict[str, Any]:
    return g.state


def post40_ready_bonus(g: Any) -> int:
    s = _s(g)
    bonus = 0
    if s.get("boss40") or seeded.missing(g, "MT40", (6, 1), "upFloor"):
        bonus += 1_000_000
    # The current local 4-50 clear comes from a G~1846/YK3 40F state.  Lower
    # gold states repeatedly fail before the 47F earthquake purchase.
    bonus += min(max(s["gold"], 0), 2400) * 620
    bonus -= max(0, 1700 - s["gold"]) * 1200
    bonus += min(max(s["yk"], 0), 5) * 170_000
    bonus -= max(0, 3 - s["yk"]) * 260_000
    bonus += min(max(s["bk"], 0), 2) * 90_000
    # Post-40 can repair stats, but very low DEF pays too much in the early
    # 46F/47F field route.
    bonus += s["def"] * 1500 + s["atk"] * 900
    bonus -= max(0, 182 - s["def"]) * 45_000
    # HP before 41F is halved soon.  High HP often means a potion was eaten too
    # early and loses value to the 41F trap; keep just enough to enter 4区.
    bonus += min(s["hp"], 260) * 620
    if s.get("boss40") or seeded.missing(g, "MT40", (6, 1), "upFloor"):
        bonus -= max(0, s["hp"] - 260) * 4200
    bonus -= max(0, 220 - s["hp"]) * 3500
    return int(bonus)


def post40_score(g: Any) -> int:
    return int(seeded.seeded_score(g) + post40_ready_bonus(g))


def post40_goal_score(g: Any) -> int:
    s = _s(g)
    stock = s["hp"] + s["yk"] * 50 + s["bk"] * 200 + s["gold"] * 0.5
    return int(
        post40_ready_bonus(g)
        + stock * 12
        + s["gold"] * 50
        + s["yk"] * 25_000
        + s["bk"] * 30_000
        + s["atk"] * 900
        + s["def"] * 1500
        - s["dmg"] * 3
        - s["yd"] * 350
        - s["bd"] * 900
        - s["rd"] * 2000
        + base.remaining_simple_value(g) * 2
    )


def post40_bucket(g: Any) -> tuple[Any, ...]:
    s = _s(g)
    parent = seeded.seeded_bucket(g)
    return parent + (
        min(max(s["gold"], 0), 3000) // 120,
        min(max(s["yk"], 0), 6),
        min(s["hp"], 1400) // 100,
    )


def install_post40_guidance() -> None:
    seeded.install_seeded_guidance()
    base.score = post40_score
    base.goal_score = post40_goal_score
    base.state_bucket = post40_bucket


def write_report(data: dict[str, Any], out_json: Path, out_md: Path) -> None:
    seeded.write_report(data, out_json, out_md)
    text = out_md.read_text(encoding="utf-8")
    text = text.replace(
        "# Zone3 slot26 seeded 搜索报告",
        "# Zone3 slot26 post40 接续优先搜索报告",
        1,
    )
    text = text.replace(
        "- seeds:",
        "- 目标：优先寻找可精确接 41F-50F HP 尾段的 40F 状态；金币不允许容忍。\n- seeds:",
        1,
    )
    out_md.write_text(text, encoding="utf-8")
    out_json.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    install_post40_guidance()
    parser = argparse.ArgumentParser()
    parser.add_argument("--time-limit-seconds", type=float, default=7200)
    parser.add_argument("--beam", type=int, default=300)
    parser.add_argument("--targets-per-state", type=int, default=48)
    parser.add_argument("--actions-per-state", type=int, default=76)
    parser.add_argument("--max-depth", type=int, default=320)
    parser.add_argument("--max-seeds", type=int, default=260)
    parser.add_argument("--focused-seeds", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--snapshot", type=Path, default=base.DEFAULT_SNAPSHOT)
    parser.add_argument("--report-interval", type=float, default=120)
    parser.add_argument("--progress-log", type=Path, default=OUT_LOG)
    parser.add_argument("--out-json", type=Path, default=OUT_JSON)
    parser.add_argument("--out-md", type=Path, default=OUT_MD)
    args = parser.parse_args()
    seeded.macro.set_snapshot(args.snapshot)
    seeds = seeded.build_seeds(args)
    if not seeds:
        print("no legal seeds")
        return 1
    data = seeded.explore_from_seeds(args, seeds)
    data["snapshot"] = str(args.snapshot)
    write_report(data, args.out_json, args.out_md)
    print(f"wrote {args.out_json}")
    print(f"wrote {args.out_md}")
    if data.get("best_goal"):
        print("best_goal", data["best_goal"]["state_text"])
    else:
        print("best_goal not found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
