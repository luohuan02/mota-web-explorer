#!/usr/bin/env python3
"""Continue the corrected best 4F-9F seed to the 10F boss until a deadline."""

from __future__ import annotations

import argparse
import json
import os
import pickle
import sys
import time
from datetime import datetime, timedelta
from typing import Any


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
SCRIPTS = os.path.join(ROOT, "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)
os.chdir(ROOT)

from scripts import compare_merchant_resource_paths as cm
from scripts import merchant_finalscore_audit as audit
from scripts import post9_merchant_seed_search as seed_search
from src.solver import gen_walkthrough as gw


DEFAULT_STATE_CACHE = os.path.join("outputs", "results", "merchant_phase1_long_search_state.pkl")
DEFAULT_RESCORE_JSON = os.path.join("outputs", "results", "merchant_phase1_corrected_rescore.json")


def fmt_score(value: float | int | None) -> str:
    if value is None:
        return "-"
    return str(int(value)) if abs(value - int(value)) < 1e-9 else f"{value:.1f}"


def parse_deadline(text: str) -> datetime:
    return datetime.fromisoformat(text)


def state_text(ent: dict[str, Any] | None) -> str:
    if ent is None:
        return "-"
    return (
        f"HP={ent['hp']} ATK={ent['atk']} DEF={ent['def']} "
        f"YK={ent['yk']} BK={ent['bk']} RK={ent['rk']} "
        f"G={cm.inferred_gold(ent, include_boss_spawn=False)} "
        f"dmg={ent.get('_dmg', 0)} "
        f"door={ent.get('_yd', 0)}/{ent.get('_bd', 0)}/{ent.get('_rd', 0)}"
    )


def load_state_cache(path: str) -> dict[str, Any]:
    with open(path, "rb") as f:
        payload = pickle.load(f)
    gw._entry_store.clear()
    gw._entry_store.update(payload.get("entry_store", {}))
    gw._next_id[0] = payload.get("next_id", gw._next_id[0])
    return payload


def load_target_row(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    top = data.get("top") or [data.get("target_row")]
    if not top or top[0] is None:
        raise RuntimeError(f"no target row found in {path}")
    return top[0]


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


def load_corrected_best_seed(args: argparse.Namespace) -> dict[str, Any]:
    payload = load_state_cache(args.state_cache)
    row = load_target_row(args.rescore_json)
    pools = []
    if row.get("label") == "merchant":
        pools.extend(payload.get("merchant_goals", []))
    else:
        pools.extend(payload.get("plain_goals", []))
    pools.extend(payload.get("merchant_goals", []))
    pools.extend(payload.get("plain_goals", []))
    matches = [ent for ent in pools if entry_matches_row(ent, row)]
    if not matches:
        raise RuntimeError(f"corrected best seed not found: {row.get('state')}")
    seed = matches[0]
    seed["_seed_source"] = "corrected 4-9 best no merchant"
    return seed


def compact_score(label: str, ent: dict[str, Any] | None, source: str) -> dict[str, Any] | None:
    if ent is None:
        return None
    return audit.compact_record(audit.score_record(label, ent, source=source))


def goal_key(row: dict[str, Any] | None) -> tuple[float, int, int]:
    if not row:
        return (-10**18, 10**9, -10**9)
    return (float(row["final_score"]), -int(row["dmg"]), int(row["jhp"]))


def budget_for_run(index: int, args: argparse.Namespace) -> dict[str, int]:
    if args.stat_rounds:
        return {
            "stat_rounds": args.stat_rounds,
            "redkey_rounds": args.redkey_rounds,
            "boss_rounds": args.boss_rounds,
            "entry_limit": args.entry_limit,
            "source_limit": args.source_limit,
        }
    ladder = [
        (6, 3, 3, 360, 24),
        (8, 4, 4, 440, 28),
        (10, 5, 5, 520, 32),
        (12, 6, 6, 620, 36),
        (14, 7, 7, 720, 42),
        (16, 8, 8, 820, 48),
    ]
    stat, red, boss, entry, source = ladder[min(index, len(ladder) - 1)]
    return {
        "stat_rounds": stat,
        "redkey_rounds": red,
        "boss_rounds": boss,
        "entry_limit": entry,
        "source_limit": source,
    }


def write_outputs(data: dict[str, Any], args: argparse.Namespace) -> None:
    os.makedirs(os.path.dirname(args.output_json), exist_ok=True)
    os.makedirs(os.path.dirname(args.output_md), exist_ok=True)
    tmp_json = args.output_json + ".tmp"
    with open(tmp_json, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp_json, args.output_json)

    lines = [
        "# Corrected Phase1 Best To Boss Deadline Search",
        "",
        f"- status: `{data['status']}`",
        f"- deadline: `{data['deadline']}`",
        f"- stop-at: `{data['stop_at']}`",
        f"- elapsed: `{data['elapsed']:.1f}s`",
        f"- completed runs: `{len(data['runs'])}`",
        f"- seed: `{data['seed_state']}`",
        f"- seed final-score: `{fmt_score(data['seed_score']['final_score'])}`",
        "",
        "## Best So Far",
        "",
        "| label | source | state | merchants | futureG | remaining | final-score |",
        "|---|---|---|---|---:|---:|---:|",
    ]
    for row in data["best_compare"]:
        lines.append(
            f"| {row['label']} | {row['source']} | "
            f"HP={row['hp']} ATK={row['atk']} DEF={row['def']} "
            f"YK={row['yk']} BK={row['bk']} RK={row['rk']} "
            f"G={row['gold']} dmg={row['dmg']} door={row['yd']}/{row['bd']}/{row['rd']} | "
            f"{','.join(row['merchants']) or '-'} | {row['future_monster_gold']} | "
            f"{fmt_score(row['remaining_group_value'])} | {fmt_score(row['final_score'])} |"
        )
    lines.extend(
        [
            "",
            "## Runs",
            "",
            "| # | elapsed | budget stat/red/boss entry/source | goals | merchant goals | best-any | merchants | best-merchant | merchants |",
            "|---:|---:|---|---:|---:|---:|---|---:|---|",
        ]
    )
    for row in data["runs"]:
        any_row = row.get("best_any")
        merchant_row = row.get("best_merchant")
        budget = row["budget"]
        lines.append(
            f"| {row['run']} | {row['elapsed']:.1f}s | "
            f"{budget['stat_rounds']}/{budget['redkey_rounds']}/{budget['boss_rounds']} "
            f"{budget['entry_limit']}/{budget['source_limit']} | "
            f"{row['goal_count']} | {row['merchant_goal_count']} | "
            f"{fmt_score(any_row['final_score']) if any_row else '-'} | "
            f"{','.join(any_row.get('merchants', [])) if any_row else '-'} | "
            f"{fmt_score(merchant_row['final_score']) if merchant_row else '-'} | "
            f"{','.join(merchant_row.get('merchants', [])) if merchant_row else '-'} |"
        )
    lines.extend(
        [
            "",
            "## Current Best Actions",
            "",
        ]
    )
    actions = data.get("best_actions") or []
    if actions:
        for idx, action in enumerate(actions, 1):
            lines.append(f"{idx}. {action}")
    else:
        lines.append("-")
    with open(args.output_md, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")


def run(args: argparse.Namespace) -> dict[str, Any]:
    cm.ensure_merchant_maps()
    seed = load_corrected_best_seed(args)
    seed_score = compact_score("seed", seed, "corrected 4-9 best no merchant")
    deadline = parse_deadline(args.deadline)
    stop_at = deadline - timedelta(minutes=args.reserve_minutes)
    t0 = time.time()
    audit.install_post9_resource_group_hooks()

    guide_boss = cm.guide_full_ent()
    baseline_rows = [
        audit.compact_record(audit.score_record("guide", guide_boss, source="guide boss baseline")),
    ]
    try:
        _delayed_phase1, delayed_boss = audit.replay_delayed_walk()
    except FileNotFoundError as exc:
        print(f"warning: delayed baseline skipped: {exc}", flush=True)
    else:
        baseline_rows.append(
            audit.compact_record(audit.score_record("delayed", delayed_boss, source="delayed boss baseline"))
        )
    runs: list[dict[str, Any]] = []
    best_any: dict[str, Any] | None = None
    best_merchant: dict[str, Any] | None = None
    best_any_ent: dict[str, Any] | None = None
    best_merchant_ent: dict[str, Any] | None = None
    status = "deadline"

    run_index = 0
    while datetime.now() < stop_at:
        if args.max_runs and run_index >= args.max_runs:
            status = "max-runs"
            break
        budget = budget_for_run(run_index, args)
        started = time.time()
        result = seed_search.run_post9_from_seed(seed, **budget)
        run_elapsed = time.time() - started
        any_row = compact_score(
            "best_any",
            result["best_ent"],
            f"corrected seed deadline run #{run_index + 1}",
        )
        merchant_row = compact_score(
            "best_merchant",
            result["best_merchant_ent"],
            f"corrected seed deadline run #{run_index + 1}",
        )
        if goal_key(any_row) > goal_key(best_any):
            best_any = any_row
            best_any_ent = result["best_ent"]
        if goal_key(merchant_row) > goal_key(best_merchant):
            best_merchant = merchant_row
            best_merchant_ent = result["best_merchant_ent"]
        runs.append(
            {
                "run": run_index + 1,
                "elapsed": run_elapsed,
                "budget": budget,
                "goal_count": result["goal_count"],
                "merchant_goal_count": result["merchant_goal_count"],
                "entry_count": result["entry_count"],
                "best_any": any_row,
                "best_merchant": merchant_row,
            }
        )
        compare_rows: list[dict[str, Any]] = []
        if best_any:
            compare_rows.append(best_any)
        if best_merchant:
            compare_rows.append(best_merchant)
        compare_rows.extend(baseline_rows)
        data = {
            "status": "running" if datetime.now() < stop_at else "deadline",
            "deadline": deadline.isoformat(timespec="seconds"),
            "stop_at": stop_at.isoformat(timespec="seconds"),
            "elapsed": time.time() - t0,
            "seed_state": state_text(seed),
            "seed_score": seed_score,
            "runs": runs,
            "best_compare": compare_rows,
            "best_actions": list(best_any.get("actions", [])) if best_any else [],
        }
        write_outputs(data, args)
        print(
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
            f"run={run_index + 1} elapsed={run_elapsed:.1f}s goals={result['goal_count']} "
            f"best={fmt_score(any_row['final_score']) if any_row else '-'} "
            f"overall={fmt_score(best_any['final_score']) if best_any else '-'}",
            flush=True,
        )
        run_index += 1

    compare_rows = []
    if best_any:
        compare_rows.append(best_any)
    if best_merchant:
        compare_rows.append(best_merchant)
    compare_rows.extend(baseline_rows)
    data = {
        "status": status,
        "deadline": deadline.isoformat(timespec="seconds"),
        "stop_at": stop_at.isoformat(timespec="seconds"),
        "elapsed": time.time() - t0,
        "seed_state": state_text(seed),
        "seed_score": seed_score,
        "runs": runs,
        "best_compare": compare_rows,
        "best_actions": list(best_any.get("actions", [])) if best_any else [],
    }
    write_outputs(data, args)
    return data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--deadline", default="2026-06-09T07:00:00")
    parser.add_argument("--reserve-minutes", type=int, default=10)
    parser.add_argument("--state-cache", default=DEFAULT_STATE_CACHE)
    parser.add_argument("--rescore-json", default=DEFAULT_RESCORE_JSON)
    parser.add_argument(
        "--output-json",
        default=os.path.join("outputs", "results", "corrected_phase1_best_to_boss_deadline.json"),
    )
    parser.add_argument(
        "--output-md",
        default=os.path.join("outputs", "reports", "corrected_phase1_best_to_boss_deadline.md"),
    )
    parser.add_argument("--max-runs", type=int, default=0)
    parser.add_argument("--stat-rounds", type=int, default=0)
    parser.add_argument("--redkey-rounds", type=int, default=4)
    parser.add_argument("--boss-rounds", type=int, default=4)
    parser.add_argument("--entry-limit", type=int, default=520)
    parser.add_argument("--source-limit", type=int, default=32)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data = run(args)
    print(f"wrote {args.output_json}")
    print(f"wrote {args.output_md}")
    print(f"status={data['status']} runs={len(data['runs'])}")


if __name__ == "__main__":
    main()
