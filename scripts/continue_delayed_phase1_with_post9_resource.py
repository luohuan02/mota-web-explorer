#!/usr/bin/env python3
"""Continue the best delayed Phase1 candidate with post-9 resource-group search."""

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

from src.solver import gen_walkthrough as gw
from scripts import phase1_action_search as p1
from scripts import post9_action_search as p9
from scripts import post9_resource_group_search as rg


OUT_JSON = os.path.join("outputs", "results", "delayed_phase1_post9_resource.json")
OUT_MD = os.path.join("outputs", "reports", "delayed_phase1_post9_resource.md")
OUT_WALK = os.path.join("outputs", "walkthroughs", "walkthrough_delayed_phase1_post9_resource.md")


TARGET = {
    "hp": 262,
    "atk": 22,
    "def": 21,
    "yk": 2,
    "bk": 1,
    "rk": 0,
    "dmg": 814,
    "yd": 24,
    "bd": 0,
    "rd": 0,
}


def state_text(ent: dict[str, Any]) -> str:
    return (
        f"HP={ent['hp']} ATK={ent['atk']} DEF={ent['def']} "
        f"YK={ent['yk']} BK={ent['bk']} RK={ent['rk']} "
        f"dmg={ent.get('_dmg', ent.get('dmg', 0))} "
        f"door={ent.get('_yd', ent.get('yd', 0))}/{ent.get('_bd', ent.get('bd', 0))}/{ent.get('_rd', ent.get('rd', 0))}"
    )


def target_match(ent: dict[str, Any]) -> bool:
    return (
        ent["hp"] == TARGET["hp"]
        and ent["atk"] == TARGET["atk"]
        and ent["def"] == TARGET["def"]
        and ent["yk"] == TARGET["yk"]
        and ent["bk"] == TARGET["bk"]
        and ent["rk"] == TARGET["rk"]
        and ent.get("_dmg", 0) == TARGET["dmg"]
        and ent.get("_yd", 0) == TARGET["yd"]
        and ent.get("_bd", 0) == TARGET["bd"]
        and ent.get("_rd", 0) == TARGET["rd"]
    )


def find_candidate(max_expansions: int) -> tuple[dict[str, Any], dict[str, Any]]:
    result = p1.run(max_expansions=max_expansions, include_entries=True, queue_mode="dmg")
    goals = result.get("_goal_entries", [])
    matches = [e for e in goals if target_match(e)]
    if not matches:
        matches = [
            e for e in goals
            if p1.delayed_shape_match(e) and e.get("_bd", 0) == 0
        ]
    if not matches:
        raise RuntimeError("delayed Phase1 candidate not found")
    candidate = sorted(matches, key=lambda e: (e.get("_dmg", 0), e.get("_yd", 0), -e["hp"]))[0]
    return candidate, result


def action_summary(ent: dict[str, Any]) -> str:
    if ent.get("_last_action"):
        return ent["_last_action"]
    return p9.action_summary(ent)


def write_walk(best: dict[str, Any], phase1_candidate_id: int) -> None:
    chain = gw.trace_chain(best)
    lines = [
        "# Delayed Phase1 + Post-9 Resource Group Walk",
        "",
        f"> final: {state_text(best)}",
        "",
    ]
    for idx, ent in enumerate(chain):
        if idx == 0:
            lines.append("## 0. 4F search start")
            lines.append("")
            lines.append(f"- {state_text(ent)}")
            lines.append("")
            continue
        prev = chain[idx - 1]
        label = action_summary(ent)
        if ent.get("_id") == phase1_candidate_id:
            label += "  [phase1 delayed prefix complete]"
        lines.append(f"## {idx}. {label}")
        lines.append("")
        lines.append(f"- {state_text(ent)}")
        lines.append(
            f"- segment dmg={ent.get('_dmg', 0) - prev.get('_dmg', 0)} "
            f"door delta={ent.get('_yd', 0) - prev.get('_yd', 0)}/"
            f"{ent.get('_bd', 0) - prev.get('_bd', 0)}/"
            f"{ent.get('_rd', 0) - prev.get('_rd', 0)}"
        )
        lines.append("")
    os.makedirs(os.path.dirname(OUT_WALK), exist_ok=True)
    with open(OUT_WALK, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")


def run_post9_from(start: dict[str, Any], rounds: int, entry_limit: int, source_limit: int) -> dict[str, Any]:
    p9.select_sources = rg.select_sources
    p9.trim_entries = rg.trim_entries
    p9.best_goals = rg.best_goals
    p9.ensure_mt10 = rg.ensure_mt10
    p9.apply_action = rg.apply_action
    p9.redkey_survival_deficit = rg.redkey_survival_deficit
    p9.OUT_WALK = OUT_WALK

    t0 = time.time()
    stat_entries, stat_rows = p9.run_stage(
        "stat27", [start], rg.STAT_ACTIONS, p9.stat_goal,
        max(6, rounds), entry_limit, source_limit,
    )
    redkey_entries, redkey_rows = p9.run_stage(
        "redkey", stat_entries, p9.REDKEY_ACTIONS, p9.redkey_goal,
        max(4, rounds // 2), entry_limit, source_limit,
    )
    final_entries, boss_rows = p9.run_stage(
        "boss", redkey_entries, p9.BOSS_PREP_ACTIONS, p9.goal,
        max(4, rounds // 2), entry_limit, source_limit, include_boss=True,
    )
    goals = rg.best_goals(final_entries)
    best = goals[0] if goals else None
    if best:
        write_walk(best, start["_id"])
    return {
        "elapsed": time.time() - t0,
        "rounds": stat_rows + redkey_rows + boss_rows,
        "entry_count": len(final_entries),
        "goal_count": len(goals),
        "best": rg.compact(best) if best else None,
        "top_goals": [rg.compact(e) for e in goals[:10]],
        "_best_obj": best,
    }


def write_report(data: dict[str, Any]) -> None:
    best_obj = data.pop("_best_obj", None)
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    lines = [
        "# Delayed Phase1 Candidate Continued With Post-9 Resource Group Search",
        "",
        f"- phase1 search elapsed: {data['phase1_elapsed']:.1f}s",
        f"- post9 continuation elapsed: {data['post9']['elapsed']:.1f}s",
        f"- post9 entry count: {data['post9']['entry_count']}",
        f"- post9 goal count: {data['post9']['goal_count']}",
        f"- phase1 candidate: {data['phase1_candidate_text']}",
    ]
    if data["post9"].get("best"):
        b = data["post9"]["best"]
        lines.append(
            f"- best final: HP={b['hp']} ATK={b['atk']} DEF={b['def']} "
            f"YK={b['yk']} BK={b['bk']} RK={b['rk']} dmg={b['dmg']} "
            f"door={b['yd']}/{b['bd']}/{b['rd']} finalStock={b.get('final_resource_stock')} "
            f"finalResidual0dmg={b.get('final_residual_value')} rgScore={b['resource_group_score']} oldScore={b['old_score']}"
        )
    else:
        lines.append("- best final: NOT FOUND")
    lines.extend([
        "",
        "## Top Goals",
        "",
        "| # | finalStock | finalResidual0dmg | rgScore | oldScore | residual | state |",
        "|---:|---:|---:|---:|---:|---:|---|",
    ])
    for idx, row in enumerate(data["post9"].get("top_goals", []), 1):
        lines.append(
            f"| {idx} | {row.get('final_resource_stock')} | {row.get('final_residual_value')} | "
            f"{row['resource_group_score']} | {row['old_score']} | {row['residual_value']} | "
            f"HP={row['hp']} ATK={row['atk']} DEF={row['def']} YK={row['yk']} BK={row['bk']} RK={row['rk']} "
            f"dmg={row['dmg']} door={row['yd']}/{row['bd']}/{row['rd']} |"
        )
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")
    if best_obj:
        data["_best_obj"] = best_obj


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase1-expansions", type=int, default=300)
    parser.add_argument("--rounds", type=int, default=12)
    parser.add_argument("--entry-limit", type=int, default=360)
    parser.add_argument("--source-limit", type=int, default=28)
    args = parser.parse_args()

    t0 = time.time()
    candidate, phase1_result = find_candidate(args.phase1_expansions)
    phase1_elapsed = time.time() - t0
    print(f"candidate {state_text(candidate)}", flush=True)
    post9 = run_post9_from(candidate, args.rounds, args.entry_limit, args.source_limit)
    data = {
        "phase1_elapsed": phase1_elapsed,
        "phase1_summary": {
            "elapsed": phase1_result.get("elapsed", 0),
            "generated": phase1_result.get("generated", 0),
            "goal_entries": phase1_result.get("goal_entries", 0),
            "delayed_shape_count": phase1_result.get("delayed_shape_count", 0),
        },
        "phase1_candidate": p1.result_record(candidate),
        "phase1_candidate_text": state_text(candidate),
        "post9": {k: v for k, v in post9.items() if k != "_best_obj"},
        "_best_obj": post9.get("_best_obj"),
    }
    write_report(data)
    best = data["post9"].get("best")
    if best:
        print(
            f"best HP={best['hp']} ATK={best['atk']} DEF={best['def']} YK={best['yk']} BK={best['bk']} "
            f"dmg={best['dmg']} door={best['yd']}/{best['bd']}/{best['rd']} "
            f"finalStock={best.get('final_resource_stock')} rg={best['resource_group_score']}"
        )
    else:
        print("best NOT FOUND")
    print(f"wrote {OUT_JSON}")
    print(f"wrote {OUT_MD}")
    print(f"wrote {OUT_WALK}")


if __name__ == "__main__":
    main()
