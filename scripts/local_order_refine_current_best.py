#!/usr/bin/env python3
"""Local order refinement for the current best post-9 boss action sequence."""

from __future__ import annotations

import argparse
import ast
import json
import os
import sys
import time
from pathlib import Path
from typing import Any


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.chdir(ROOT)

from scripts import compare_merchant_resource_paths as cm
from scripts import merchant_finalscore_audit as audit
from scripts import probe_mt7_red_first_swap_sequence as probe
from scripts import run_corrected_phase1_best_boss_until_deadline as runner
from scripts import post9_resource_group_search as rg


DEFAULT_INPUT = os.path.join("best", "current_best_boss_summary.json")
OUT_JSON = os.path.join("outputs", "results", "local_order_refine_current_best.json")
OUT_MD = os.path.join("outputs", "reports", "local_order_refine_current_best.md")

Action = tuple[str, str]


def fmt_score(value: float | int | None) -> str:
    if value is None:
        return "-"
    value = float(value)
    return str(int(value)) if abs(value - int(value)) < 1e-9 else f"{value:.1f}"


def state_text(ent: dict[str, Any] | None) -> str:
    if ent is None:
        return "-"
    return (
        f"HP={ent['hp']} ATK={ent['atk']} DEF={ent['def']} "
        f"YK={ent['yk']} BK={ent['bk']} RK={ent['rk']} "
        f"G={cm.inferred_gold(ent)} dmg={ent.get('_dmg', 0)} "
        f"door={ent.get('_yd', 0)}/{ent.get('_bd', 0)}/{ent.get('_rd', 0)}"
    )


def parse_action(text: str) -> Action:
    fid, targets, _flyback = ast.literal_eval(text)
    return (fid, targets[0])


def load_sequence(path: str) -> list[Action]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    actions = (
        data.get("actions")
        or data.get("summary", {}).get("actions")
        or data.get("best", {}).get("actions")
        or data.get("best_boss", {}).get("actions")
        or []
    )
    if not actions and data.get("sequence"):
        return parse_sequence_labels(data["sequence"])
    parsed = [parse_action(item) for item in actions]
    return [action for action in parsed if action != ("MT10", "redDoor")]


def parse_sequence_labels(items: list[str]) -> list[Action]:
    out: list[Action] = []
    for item in items:
        fid, target = item.split(":", 1)
        action = (fid, target)
        if action != ("MT10", "redDoor"):
            out.append(action)
    return out


def action_aliases(action: Action) -> list[Action]:
    fid, target = action
    aliases = {
        ("MT7", "yellowKey"): [
            ("MT7_SKEL_KEY", "yellowKey"),
            ("MT7_RIGHT_KEY", "yellowKey"),
            ("MT7", "yellowKey"),
        ],
        ("MT5", "blueGem"): [("MT5_DIRECT", "blueGem"), ("MT5", "blueGem")],
        ("MT4", "blueKey"): [("MT4_DIRECT", "blueKey"), ("MT4", "blueKey")],
        ("MT9", "upFloor"): [("MT9_BLUE_UP", "upFloor"), ("MT9", "upFloor")],
        ("MT10", "blueGem"): [("MT10_DIRECT", "blueGem"), ("MT10", "blueGem")],
    }.get((fid, target), [action])
    out: list[Action] = []
    seen: set[Action] = set()
    for item in aliases:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def score_key(ent: dict[str, Any]) -> tuple[float, int, int]:
    return (cm.final_stock_with_gold(ent), -ent.get("_dmg", 0), ent["hp"])


def compact(label: str, ent: dict[str, Any] | None, source: str) -> dict[str, Any] | None:
    if ent is None:
        return None
    return audit.compact_record(audit.score_record(label, ent, source=source))


def apply_alias_step(entries: list[dict[str, Any]], action: Action, beam: int) -> list[dict[str, Any]]:
    generated: list[dict[str, Any]] = []
    for alias_fid, alias_target in action_aliases(action):
        generated.extend(probe.apply_step(entries, alias_fid, alias_target, beam))
    return probe.unique_trim(generated, beam)


def replay_sequence(seed: dict[str, Any], sequence: list[Action], beam: int) -> dict[str, Any]:
    entries = [audit.seed_for_post9(seed)]
    rows: list[dict[str, Any]] = []
    for idx, action in enumerate(sequence, 1):
        entries = apply_alias_step(entries, action, beam)
        rows.append({
            "step": idx,
            "action": f"{action[0]}:{action[1]}",
            "kept": len(entries),
            "best": state_text(entries[0]) if entries else None,
        })
        if not entries:
            return {"ok": False, "rows": rows, "best_ent": None, "best": None}

    boss_entries: list[dict[str, Any]] = []
    for ent in entries:
        boss_entries.extend(audit.annotate_money(item) for item in rg.base.boss_action(ent))
    boss_entries = [ent for ent in probe.unique_trim(boss_entries, beam) if rg.base.goal(ent)]
    boss_entries.sort(key=lambda ent: (-cm.final_stock_with_gold(ent), ent.get("_dmg", 0), -ent["hp"]))
    best_ent = boss_entries[0] if boss_entries else None
    return {
        "ok": best_ent is not None,
        "rows": rows,
        "best_ent": best_ent,
        "best": compact("local_refine", best_ent, "local order refinement") if best_ent else None,
    }


def is_supply(action: Action) -> bool:
    return action[1] in {"yellowKey", "blueKey", "redKey", "redPotion", "bluePotion", "upFloor"}


def neighbors(sequence: list[Action], move_window: int) -> list[list[Action]]:
    out: list[list[Action]] = []
    n = len(sequence)
    for idx in range(n - 1):
        item = list(sequence)
        item[idx], item[idx + 1] = item[idx + 1], item[idx]
        out.append(item)
    for idx, action in enumerate(sequence):
        if not is_supply(action):
            continue
        for dst in range(idx + 2, min(n, idx + move_window + 1)):
            item = list(sequence)
            moved = item.pop(idx)
            item.insert(dst, moved)
            out.append(item)
    return out


def sequence_key(sequence: list[Action]) -> tuple[Action, ...]:
    return tuple(sequence)


def run(args: argparse.Namespace) -> dict[str, Any]:
    cm.ensure_merchant_maps()
    audit.install_post9_resource_group_hooks()
    seed = runner.load_corrected_best_seed(args)
    base_sequence = load_sequence(args.input)
    t0 = time.time()

    current = base_sequence
    current_result = replay_sequence(seed, current, args.beam)
    best_sequence = current
    best_result = current_result
    evaluated = {sequence_key(current)}
    history = [{
        "pass": 0,
        "kind": "base",
        "score": None if not current_result["best"] else current_result["best"]["final_score"],
        "state": None if not current_result["best_ent"] else state_text(current_result["best_ent"]),
        "sequence": [f"{fid}:{target}" for fid, target in current],
    }]

    for pass_no in range(1, args.passes + 1):
        improved = False
        candidates = neighbors(best_sequence, args.move_window)
        pass_best_sequence = best_sequence
        pass_best_result = best_result
        for seq in candidates:
            key = sequence_key(seq)
            if key in evaluated:
                continue
            evaluated.add(key)
            result = replay_sequence(seed, seq, args.beam)
            if not result["best_ent"]:
                continue
            if (
                pass_best_result["best_ent"] is None
                or score_key(result["best_ent"]) > score_key(pass_best_result["best_ent"])
            ):
                pass_best_sequence = seq
                pass_best_result = result
                improved = True
        best_sequence = pass_best_sequence
        best_result = pass_best_result
        history.append({
            "pass": pass_no,
            "kind": "improved" if improved else "stable",
            "score": None if not best_result["best"] else best_result["best"]["final_score"],
            "state": None if not best_result["best_ent"] else state_text(best_result["best_ent"]),
            "sequence": [f"{fid}:{target}" for fid, target in best_sequence],
            "evaluated": len(evaluated),
        })
        if not improved:
            break

    data = {
        "elapsed": time.time() - t0,
        "beam": args.beam,
        "passes": args.passes,
        "move_window": args.move_window,
        "evaluated": len(evaluated),
        "base_sequence": [f"{fid}:{target}" for fid, target in base_sequence],
        "best_sequence": [f"{fid}:{target}" for fid, target in best_sequence],
        "best": best_result["best"],
        "best_rows": best_result["rows"],
        "history": history,
    }
    return data


def write_outputs(data: dict[str, Any], out_json: str, out_md: str) -> None:
    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    os.makedirs(os.path.dirname(out_md), exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    lines = [
        "# Local Order Refine Current Best",
        "",
        f"- elapsed: `{data['elapsed']:.1f}s`",
        f"- evaluated: `{data['evaluated']}`",
        f"- beam: `{data['beam']}`",
    ]
    best = data.get("best")
    if best:
        lines.append(
            f"- best: `HP={best['hp']} ATK={best['atk']} DEF={best['def']} "
            f"YK={best['yk']} BK={best['bk']} RK={best['rk']} G={best['gold']} "
            f"dmg={best['dmg']} door={best['yd']}/{best['bd']}/{best['rd']} "
            f"final-score={fmt_score(best['final_score'])}`"
        )
    lines.extend(["", "## History", ""])
    for row in data["history"]:
        lines.append(
            f"- pass {row['pass']} {row['kind']}: "
            f"{fmt_score(row.get('score'))} {row.get('state') or '-'}"
        )
    lines.extend(["", "## Best Sequence", ""])
    for idx, action in enumerate(data["best_sequence"], 1):
        lines.append(f"{idx}. {action}")
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=DEFAULT_INPUT)
    parser.add_argument("--state-cache", default=runner.DEFAULT_STATE_CACHE)
    parser.add_argument("--rescore-json", default=runner.DEFAULT_RESCORE_JSON)
    parser.add_argument("--beam", type=int, default=120)
    parser.add_argument("--passes", type=int, default=4)
    parser.add_argument("--move-window", type=int, default=4)
    parser.add_argument("--output-json", default=OUT_JSON)
    parser.add_argument("--output-md", default=OUT_MD)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data = run(args)
    write_outputs(data, args.output_json, args.output_md)
    best = data.get("best")
    print(
        "best="
        + (fmt_score(best["final_score"]) if best else "-")
        + " "
        + (f"HP={best['hp']} dmg={best['dmg']}" if best else "")
    )
    print(f"wrote {args.output_json}")
    print(f"wrote {args.output_md}")


if __name__ == "__main__":
    main()
