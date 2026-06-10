#!/usr/bin/env python3
"""Generate the corrected full-map best 4F-9F phase1 walkthrough.

The route is selected from the long merchant phase1 state cache using the top
row of the corrected rescore report.  Despite the file family name, the current
best route is the no-merchant candidate.
"""

from __future__ import annotations

import argparse
import json
import os
import pickle
import sys
from typing import Any


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
SCRIPTS = os.path.join(ROOT, "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)
os.chdir(ROOT)

from scripts import compare_merchant_resource_paths as cm
from scripts import gen_merchant_finalscore_walk as walk
from scripts import merchant_finalscore_audit as audit
from src.solver import gen_walkthrough as gw


DEFAULT_STATE_CACHE = os.path.join("outputs", "results", "merchant_phase1_long_search_state.pkl")
DEFAULT_RESCORE_JSON = os.path.join("outputs", "results", "merchant_phase1_corrected_rescore.json")
DEFAULT_OUT_MD = os.path.join("outputs", "walkthroughs", "walkthrough_corrected_phase1_best_no_merchant.md")
DEFAULT_OUT_JSON = os.path.join("outputs", "results", "corrected_phase1_best_no_merchant_walk.json")


def fmt_score(value: float) -> str:
    return str(int(value)) if abs(value - int(value)) < 1e-9 else f"{value:.1f}"


def load_state_cache(path: str) -> dict[str, Any]:
    with open(path, "rb") as f:
        payload = pickle.load(f)
    gw._entry_store.clear()
    gw._entry_store.update(payload.get("entry_store", {}))
    gw._next_id[0] = payload.get("next_id", gw._next_id[0])
    return payload


def load_target(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not data.get("top"):
        raise RuntimeError(f"no top rows in {path}")
    return data["top"][0]


def entry_matches_row(ent: dict[str, Any], row: dict[str, Any]) -> bool:
    return (
        ent["hp"] == row["hp"]
        and ent["atk"] == row["atk"]
        and ent["def"] == row["def"]
        and ent["yk"] == row["yk"]
        and ent["bk"] == row["bk"]
        and ent["rk"] == row["rk"]
        and ent.get("_dmg", 0) == row["dmg"]
        and ent.get("_yd", 0) == row["yd"]
        and ent.get("_bd", 0) == row["bd"]
        and ent.get("_rd", 0) == row["rd"]
        and cm.inferred_gold(ent, include_boss_spawn=False) == row["gold"]
    )


def find_entry(payload: dict[str, Any], row: dict[str, Any]) -> dict[str, Any]:
    label = row.get("label")
    pools: list[dict[str, Any]] = []
    if label == "merchant":
        pools.extend(payload.get("merchant_goals", []))
    elif label == "plain":
        pools.extend(payload.get("plain_goals", []))
    else:
        pools.extend(payload.get("plain_goals", []))
        pools.extend(payload.get("merchant_goals", []))
    matches = [ent for ent in pools if entry_matches_row(ent, row)]
    if not matches:
        raise RuntimeError(f"target row not found in state cache: {row.get('state')}")
    if len(matches) > 1:
        matches.sort(key=lambda ent: (ent.get("_id", 0),))
    return matches[0]


def write_outputs(best: dict[str, Any], target_row: dict[str, Any], args: argparse.Namespace) -> None:
    cm.ensure_merchant_maps()
    record = audit.score_record(target_row.get("label", "plain"), best, source="corrected phase1 cache rescore")
    compact = audit.compact_record(record)
    actions = cm.trace_actions(best)
    chain = gw.trace_chain(best)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    os.makedirs(os.path.dirname(args.json_output), exist_ok=True)
    with open(args.json_output, "w", encoding="utf-8") as f:
        json.dump(
            {
                "target_row": target_row,
                "summary": compact,
                "entry_id": best.get("_id"),
                "parent_id": best.get("_parent_id"),
                "actions": actions,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    title = "Corrected Phase1 Best Walk"
    if not compact.get("merchants"):
        title += " (No Merchant)"
    lines = [
        f"# {title}",
        "",
        "## Summary",
        "",
        f"- entry id: `{best.get('_id')}`",
        f"- final: {walk.state_text(best)}",
        f"- merchants used: {', '.join(compact['merchants']) or '-'}",
        f"- corrected full-map final-score: {fmt_score(compact['final_score'])}",
        f"- full-map remaining resources: {fmt_score(compact['remaining_group_value'])}",
        f"- future monster gold: {compact['future_monster_gold']}G",
        f"- note: this is a 4F-9F phase1 walk, not a corrected post-9/Boss continuation.",
        "",
        "## Compact Actions",
        "",
    ]
    for idx, action in enumerate(actions, 1):
        lines.append(f"{idx}. {action}")
    lines.extend(["", "## Detailed Steps", ""])

    for idx in range(1, len(chain)):
        prev = chain[idx - 1]
        curr = chain[idx]
        action = curr.get("_last_action") or str(curr.get("_step_info"))
        lines.append(f"### {idx}. {action}")
        lines.append("")
        lines.append(f"- before: {walk.state_text(prev)}")
        try:
            step_lines, _visited = walk.reconstruct_segment(prev, curr)
            lines.extend(step_lines)
        except Exception as exc:
            lines.append(f"- reconstruction failed: {exc}")
        lines.append(f"- after: {walk.state_text(curr)}")
        lines.append("")

    lines.extend(
        [
            "## Score Model",
            "",
            "- Gold is valued as `100G = 1YK = 50HP`, so `1G = 0.5 score`.",
            "- Future reachable monsters are counted as zero-damage future gold.",
            "- Future map resources and unused merchant net resources are included in the remaining-resource score.",
            "- Door/key costs remain part of the state through `door=Y/B/R` and remaining key stock.",
            "",
        ]
    )
    with open(args.output, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-cache", default=DEFAULT_STATE_CACHE)
    parser.add_argument("--rescore-json", default=DEFAULT_RESCORE_JSON)
    parser.add_argument("--output", default=DEFAULT_OUT_MD)
    parser.add_argument("--json-output", default=DEFAULT_OUT_JSON)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = load_state_cache(args.state_cache)
    target_row = load_target(args.rescore_json)
    best = find_entry(payload, target_row)
    write_outputs(best, target_row, args)
    print(f"wrote {args.output}")
    print(f"wrote {args.json_output}")
    print(f"entry {best.get('_id')}: {walk.state_text(best)}")


if __name__ == "__main__":
    main()
