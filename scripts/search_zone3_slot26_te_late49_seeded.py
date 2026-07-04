#!/usr/bin/env python3
"""Seeded Zone-3 search biased for pure-TE late-49 continuation.

Late-49 TE needs a spare red key before 25F/26F, because the 49F red key is not
available until after the 50F thief event.  This wrapper reuses the seeded
Zone-3 beam search with a scoring function that strongly prefers RK>=1 at 40F.
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
OUT_JSON = ROOT / "outputs" / "results" / "zone3_slot26_te_late49_seeded.json"
OUT_MD = ROOT / "outputs" / "reports" / "zone3_slot26_te_late49_seeded.md"
OUT_LOG = ROOT / "outputs" / "logs" / "zone3_slot26_te_late49_seeded_progress.log"


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


seeded = load_module("zone3_te_late49_seeded_base", SEEDED_PATH)
base = seeded.base


def _s(g: Any) -> dict[str, Any]:
    return g.state


def late49_ready_bonus(g: Any) -> int:
    s = _s(g)
    bonus = 0
    if s.get("boss40") or seeded.missing(g, "MT40", (6, 1), "upFloor"):
        bonus += 1_000_000

    # Hard strategic need: one spare red key before 25F/26F, because 49F is late.
    bonus += min(max(s["rk"], 0), 1) * 2_500_000
    bonus -= max(0, 1 - s["rk"]) * 2_200_000
    bonus -= s["rd"] * 180_000

    # Keep enough yellow-key/gold economy for the 41F-48F bridge.
    bonus += min(max(s["gold"], 0), 2600) * 560
    bonus -= max(0, 1700 - s["gold"]) * 1100
    bonus += min(max(s["yk"], 0), 5) * 150_000
    bonus -= max(0, 3 - s["yk"]) * 240_000
    bonus += min(max(s["bk"], 0), 2) * 80_000

    # Late 49F means 35F dragon is fought before the knife; ATK is important.
    bonus += s["atk"] * 2200 + s["def"] * 1200
    bonus -= max(0, 170 - s["atk"]) * 60_000
    bonus -= max(0, 182 - s["def"]) * 35_000

    # Still prefer low HP before the 41F half trap; avoid pre-trap potions.
    bonus += min(s["hp"], 260) * 620
    if s.get("boss40") or seeded.missing(g, "MT40", (6, 1), "upFloor"):
        bonus -= max(0, s["hp"] - 260) * 4200
    bonus -= max(0, 200 - s["hp"]) * 3000
    return int(bonus)


def late49_score(g: Any) -> int:
    return int(seeded.seeded_score(g) + late49_ready_bonus(g))


def late49_goal_score(g: Any) -> int:
    s = _s(g)
    stock = s["hp"] + s["yk"] * 50 + s["bk"] * 200 + s["rk"] * 800 + s["gold"] * 0.5
    return int(
        late49_ready_bonus(g)
        + stock * 12
        + s["gold"] * 45
        + s["yk"] * 20_000
        + s["bk"] * 25_000
        + s["rk"] * 1_000_000
        + s["atk"] * 2000
        + s["def"] * 1200
        - s["dmg"] * 3
        - s["yd"] * 300
        - s["bd"] * 800
        - s["rd"] * 160_000
        + base.remaining_simple_value(g) * 2
    )


def late49_bucket(g: Any) -> tuple[Any, ...]:
    s = _s(g)
    parent = seeded.seeded_bucket(g)
    return parent + (
        min(max(s["gold"], 0), 3000) // 120,
        min(max(s["yk"], 0), 6),
        min(max(s["rk"], 0), 2),
        min(s["hp"], 1400) // 100,
    )


def install_late49_guidance() -> None:
    seeded.install_seeded_guidance()
    base.score = late49_score
    base.goal_score = late49_goal_score
    base.state_bucket = late49_bucket


def write_report(data: dict[str, Any], out_json: Path, out_md: Path) -> None:
    seeded.write_report(data, out_json, out_md)
    text = out_md.read_text(encoding="utf-8")
    text = text.replace(
        "# Zone3 slot26 seeded 搜索报告",
        "# Zone3 slot26 pure-TE late-49 红钥匙优先搜索报告",
        1,
    )
    text = text.replace(
        "- seeds:",
        "- 目标：寻找 40F 后 RK>=1 的状态，用于 50F 小偷后再下楼封印 49F 的纯净版 TE；金币不允许容忍。\n- seeds:",
        1,
    )
    out_md.write_text(text, encoding="utf-8")
    out_json.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    install_late49_guidance()
    parser = argparse.ArgumentParser()
    parser.add_argument("--time-limit-seconds", type=float, default=7200)
    parser.add_argument("--beam", type=int, default=300)
    parser.add_argument("--targets-per-state", type=int, default=48)
    parser.add_argument("--actions-per-state", type=int, default=76)
    parser.add_argument("--max-depth", type=int, default=340)
    parser.add_argument("--max-seeds", type=int, default=260)
    parser.add_argument("--focused-seeds", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--report-interval", type=float, default=120)
    parser.add_argument("--progress-log", type=Path, default=OUT_LOG)
    parser.add_argument("--out-json", type=Path, default=OUT_JSON)
    parser.add_argument("--out-md", type=Path, default=OUT_MD)
    args = parser.parse_args()
    seeds = seeded.build_seeds(args)
    if not seeds:
        print("no legal seeds")
        return 1
    data = seeded.explore_from_seeds(args, seeds)
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
