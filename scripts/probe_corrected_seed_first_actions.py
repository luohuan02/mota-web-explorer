#!/usr/bin/env python3
"""Probe first-action variants from the corrected 4F-9F best seed."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import Any


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.chdir(ROOT)

from scripts import compare_merchant_resource_paths as cm
from scripts import merchant_finalscore_audit as audit
from scripts import post9_merchant_seed_search as seed_search
from scripts import post9_resource_group_search as rg
from scripts import run_corrected_phase1_best_boss_until_deadline as runner
from src.solver import gen_walkthrough as gw


DEFAULT_JSON = os.path.join("outputs", "results", "corrected_seed_first_action_probe.json")
DEFAULT_MD = os.path.join("outputs", "reports", "corrected_seed_first_action_probe.md")


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


def record_text(row: dict[str, Any] | None) -> str:
    if row is None:
        return "-"
    return (
        f"HP={row['hp']} ATK={row['atk']} DEF={row['def']} "
        f"YK={row['yk']} BK={row['bk']} RK={row['rk']} "
        f"G={row['gold']} dmg={row['dmg']} "
        f"door={row['yd']}/{row['bd']}/{row['rd']}"
    )


def compact(label: str, ent: dict[str, Any] | None, source: str) -> dict[str, Any] | None:
    if ent is None:
        return None
    return audit.compact_record(audit.score_record(label, ent, source=source))


def load_seed(args: argparse.Namespace) -> dict[str, Any]:
    ns = argparse.Namespace(state_cache=args.state_cache, rescore_json=args.rescore_json)
    return runner.load_corrected_best_seed(ns)


def apply_first_action(seed: dict[str, Any], fid: str, target: str) -> list[dict[str, Any]]:
    audit.install_post9_resource_group_hooks()
    start = audit.seed_for_post9(seed)
    out = audit.merchant_aware_apply_action(start, fid, target)
    out.sort(
        key=lambda ent: (
            ent.get("_dmg", 0),
            ent.get("_yd", 0),
            ent.get("_bd", 0),
            ent.get("_rd", 0),
            -ent["atk"],
            -ent["def"],
            -ent["yk"],
            -ent["bk"],
            -ent["hp"],
        )
    )
    return out


def continue_from_forced_entries(
    seed: dict[str, Any],
    fid: str,
    target: str,
    *,
    first_limit: int,
    stat_rounds: int,
    redkey_rounds: int,
    boss_rounds: int,
    entry_limit: int,
    source_limit: int,
) -> dict[str, Any]:
    t0 = time.time()
    first_entries = apply_first_action(seed, fid, target)[:first_limit]
    merchant_actions = [("merchant", merchant.key) for merchant in cm.MERCHANTS]
    if not first_entries:
        return {
            "label": f"{fid}:{target}",
            "elapsed": time.time() - t0,
            "first_count": 0,
            "goal_count": 0,
            "best": None,
        }
    stat_entries, stat_rows = rg.base.run_stage(
        "stat27",
        first_entries,
        list(rg.STAT_ACTIONS) + merchant_actions,
        rg.base.stat_goal,
        stat_rounds,
        entry_limit,
        source_limit,
    )
    redkey_entries, redkey_rows = rg.base.run_stage(
        "redkey",
        stat_entries,
        list(rg.base.REDKEY_ACTIONS) + merchant_actions,
        rg.base.redkey_goal,
        redkey_rounds,
        entry_limit,
        source_limit,
    )
    final_entries, boss_rows = rg.base.run_stage(
        "boss",
        redkey_entries,
        list(rg.base.BOSS_PREP_ACTIONS) + merchant_actions,
        rg.base.goal,
        boss_rounds,
        entry_limit,
        source_limit,
        include_boss=True,
    )
    goals = [ent for ent in final_entries if rg.base.goal(ent)]
    goals.sort(key=lambda ent: (-cm.final_stock_with_gold(ent), ent.get("_dmg", 0), -ent["hp"]))
    return {
        "label": f"{fid}:{target}",
        "elapsed": time.time() - t0,
        "first_count": len(first_entries),
        "first_samples": [compact(f"{fid}:{target}:first", ent, "forced first action") for ent in first_entries[:5]],
        "goal_count": len(goals),
        "best": compact(f"{fid}:{target}:boss", goals[0], "forced first action continuation") if goals else None,
        "rounds": stat_rows + redkey_rows + boss_rows,
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    cm.ensure_merchant_maps()
    seed = load_seed(args)
    candidates = [
        ("MT1", "blueGem"),
        ("MT1", "redGem"),
        ("MT3", "blueGem"),
        ("MT3", "redGem"),
        ("MT7", "redGem"),
        ("MT8", "redGem"),
        ("MT8", "blueGem"),
    ]
    first_rows = []
    for fid, target in candidates:
        samples = [compact(f"{fid}:{target}", ent, "first action probe") for ent in apply_first_action(seed, fid, target)[:5]]
        first_rows.append({"action": f"{fid}:{target}", "count": len(samples), "samples": samples})

    forced = []
    for label in args.force:
        fid, target = label.split(":", 1)
        forced.append(
            continue_from_forced_entries(
                seed,
                fid,
                target,
                first_limit=args.first_limit,
                stat_rounds=args.stat_rounds,
                redkey_rounds=args.redkey_rounds,
                boss_rounds=args.boss_rounds,
                entry_limit=args.entry_limit,
                source_limit=args.source_limit,
            )
        )

    baseline = None
    if args.include_baseline:
        result = seed_search.run_post9_from_seed(
            seed,
            stat_rounds=args.stat_rounds,
            redkey_rounds=args.redkey_rounds,
            boss_rounds=args.boss_rounds,
            entry_limit=args.entry_limit,
            source_limit=args.source_limit,
        )
        baseline = compact("baseline", result["best_ent"], "unforced corrected seed continuation")

    return {
        "config": vars(args),
        "seed": compact("seed", seed, "corrected 4F-9F best seed"),
        "first_actions": first_rows,
        "forced_continuations": forced,
        "baseline": baseline,
    }


def write_outputs(data: dict[str, Any], out_json: str, out_md: str) -> None:
    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    os.makedirs(os.path.dirname(out_md), exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    lines = [
        "# Corrected Seed First Action Probe",
        "",
        f"- seed: `{record_text(data.get('seed'))}`",
        f"- forced budget stat/red/boss entry/source: `{data['config']['stat_rounds']}` / `{data['config']['redkey_rounds']}` / `{data['config']['boss_rounds']}` / `{data['config']['entry_limit']}` / `{data['config']['source_limit']}`",
        "",
        "## First Action Samples",
        "",
        "| action | samples | best immediate state | immediate final-score |",
        "|---|---:|---|---:|",
    ]
    for row in data["first_actions"]:
        best = row["samples"][0] if row["samples"] else None
        lines.append(
            f"| {row['action']} | {row['count']} | "
            f"{record_text(best)} | "
            f"{fmt_score(best['final_score']) if best else '-'} |"
        )
    lines.extend([
        "",
        "## Forced Continuations",
        "",
        "| forced first action | first variants | goals | best boss state | final-score | elapsed |",
        "|---|---:|---:|---|---:|---:|",
    ])
    for row in data["forced_continuations"]:
        best = row.get("best")
        lines.append(
            f"| {row['label']} | {row['first_count']} | {row['goal_count']} | "
            f"{record_text(best)} | "
            f"{fmt_score(best['final_score']) if best else '-'} | {row['elapsed']:.1f}s |"
        )
    if data.get("baseline"):
        base = data["baseline"]
        lines.extend([
            "",
            f"- baseline best: `{record_text(base)}`, final-score `{fmt_score(base['final_score'])}`",
        ])
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-cache", default=runner.DEFAULT_STATE_CACHE)
    parser.add_argument("--rescore-json", default=runner.DEFAULT_RESCORE_JSON)
    parser.add_argument("--stat-rounds", type=int, default=8)
    parser.add_argument("--redkey-rounds", type=int, default=4)
    parser.add_argument("--boss-rounds", type=int, default=4)
    parser.add_argument("--entry-limit", type=int, default=360)
    parser.add_argument("--source-limit", type=int, default=24)
    parser.add_argument("--first-limit", type=int, default=6)
    parser.add_argument("--force", action="append", default=["MT7:redGem"])
    parser.add_argument("--include-baseline", action="store_true")
    parser.add_argument("--out-json", default=DEFAULT_JSON)
    parser.add_argument("--out-md", default=DEFAULT_MD)
    args = parser.parse_args()
    data = run(args)
    write_outputs(data, args.out_json, args.out_md)
    for row in data["forced_continuations"]:
        best = row.get("best")
        print(
            f"{row['label']} goals={row['goal_count']} "
            f"best={fmt_score(best['final_score']) if best else '-'} "
            f"{record_text(best)} "
            f"elapsed={row['elapsed']:.1f}s"
        )


if __name__ == "__main__":
    main()
