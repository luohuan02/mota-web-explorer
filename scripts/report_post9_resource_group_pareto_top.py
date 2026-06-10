#!/usr/bin/env python3
"""Report Pareto-front top rows for the post-9F resource-group experiment."""

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

from scripts import post9_resource_group_search as rg


OUT_JSON = os.path.join("outputs", "results", "post9_resource_group_pareto_top.json")
OUT_MD = os.path.join("outputs", "reports", "post9_resource_group_pareto_top.md")


def compact_key(e: dict[str, Any]) -> tuple[int, ...]:
    return (
        e["hp"],
        e["atk"],
        e["def"],
        e["yk"],
        e["bk"],
        e["rk"],
        e.get("_dmg", 0),
        e.get("_yd", 0),
        e.get("_bd", 0),
        e.get("_rd", 0),
    )


def row_key(row: dict[str, Any]) -> tuple[int, ...]:
    return (
        row["hp"],
        row["atk"],
        row["def"],
        row["yk"],
        row["bk"],
        row["rk"],
        row["dmg"],
        row["yd"],
        row["bd"],
        row["rd"],
    )


def compact(e: dict[str, Any]) -> dict[str, Any]:
    residual, notes = rg.residual_resource_value(e)
    return {
        "hp": e["hp"],
        "atk": e["atk"],
        "def": e["def"],
        "yk": e["yk"],
        "bk": e["bk"],
        "rk": e["rk"],
        "dmg": e.get("_dmg", 0),
        "yd": e.get("_yd", 0),
        "bd": e.get("_bd", 0),
        "rd": e.get("_rd", 0),
        "old_score": rg.old_score(e),
        "resource_group_score": rg.resource_group_score(e),
        "residual_value": residual,
        "residual_notes": notes[:4],
    }


def unique_goals(goals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    best: dict[tuple[int, ...], dict[str, Any]] = {}
    for e in goals:
        key = compact_key(e)
        prev = best.get(key)
        if prev is None or rg.score_key(e) < rg.score_key(prev):
            best[key] = e
    return list(best.values())


def dominates(a: dict[str, Any], b: dict[str, Any]) -> bool:
    better_or_equal = (
        a["hp"] >= b["hp"]
        and a["atk"] >= b["atk"]
        and a["def"] >= b["def"]
        and a["yk"] >= b["yk"]
        and a["bk"] >= b["bk"]
        and a["rk"] >= b["rk"]
        and a["dmg"] <= b["dmg"]
        and a["yd"] <= b["yd"]
        and a["bd"] <= b["bd"]
        and a["rd"] <= b["rd"]
    )
    if not better_or_equal:
        return False
    return row_key(a) != row_key(b)


def pareto_front(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    front = []
    for row in rows:
        if any(dominates(other, row) for other in rows):
            continue
        front.append(row)
    return front


def rank_rows(rows: list[dict[str, Any]], key_name: str) -> dict[tuple[int, ...], int]:
    if key_name == "old":
        ranked = sorted(rows, key=lambda r: (r["old_score"], r["resource_group_score"], r["dmg"], r["yd"], -r["hp"]))
    elif key_name == "new":
        ranked = sorted(rows, key=lambda r: (r["resource_group_score"], r["old_score"], r["dmg"], r["yd"], -r["hp"]))
    else:
        raise ValueError(key_name)
    return {row_key(row): idx for idx, row in enumerate(ranked, 1)}


def state_text(row: dict[str, Any]) -> str:
    return (
        f"HP={row['hp']} ATK={row['atk']} DEF={row['def']} "
        f"YK={row['yk']} BK={row['bk']} RK={row['rk']} "
        f"dmg={row['dmg']} door={row['yd']}/{row['bd']}/{row['rd']}"
    )


def write_report(data: dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    lines = [
        "# Post-9 Resource Group Pareto Top",
        "",
        "Source: `scripts/post9_resource_group_search.py`",
        "",
        "- old_score = `dmg + yd*50 + bd*200 - hp - yk*50 - bk*200`",
        "- resource_group_score = `dmg - hp - yk*50 - bk*200 + stage_penalty - residual_group_value`",
        f"- raw goals: {data['raw_goal_count']}",
        f"- unique goals: {data['unique_goal_count']}",
        f"- pareto front: {data['pareto_count']}",
        "",
        "## Top 10 By Resource Group Score After Pareto Filter",
        "",
        "| # | newRank | oldRank | rgScore | oldScore | residual | state |",
        "|---:|---:|---:|---:|---:|---:|---|",
    ]
    for idx, row in enumerate(data["top_by_resource_group"], 1):
        lines.append(
            f"| {idx} | {row['new_rank']} | {row['old_rank']} | "
            f"{row['resource_group_score']} | {row['old_score']} | {row['residual_value']} | "
            f"{state_text(row)} |"
        )
    lines.extend([
        "",
        "## Top 10 By Old Score After Pareto Filter",
        "",
        "| # | oldRank | newRank | oldScore | rgScore | residual | state |",
        "|---:|---:|---:|---:|---:|---:|---|",
    ])
    for idx, row in enumerate(data["top_by_old"], 1):
        lines.append(
            f"| {idx} | {row['old_rank']} | {row['new_rank']} | "
            f"{row['old_score']} | {row['resource_group_score']} | {row['residual_value']} | "
            f"{state_text(row)} |"
        )
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")


def build_report(rounds: int, entry_limit: int, source_limit: int) -> dict[str, Any]:
    captured: dict[str, list[dict[str, Any]]] = {}
    original_write_report = rg.write_report

    def capture_and_write(data: dict[str, Any]) -> None:
        captured["goals"] = list(data.get("_goal_entries_obj", []))
        original_write_report(data)

    rg.write_report = capture_and_write
    try:
        rg.run(rounds, entry_limit, source_limit)
    finally:
        rg.write_report = original_write_report

    goals = captured.get("goals", [])
    unique = unique_goals(goals)
    rows = [compact(e) for e in unique]
    front = pareto_front(rows)
    old_ranks = rank_rows(front, "old")
    new_ranks = rank_rows(front, "new")
    for row in front:
        key = row_key(row)
        row["old_rank"] = old_ranks[key]
        row["new_rank"] = new_ranks[key]

    top_new = sorted(front, key=lambda r: (r["resource_group_score"], r["old_score"], r["dmg"], r["yd"], -r["hp"]))[:10]
    top_old = sorted(front, key=lambda r: (r["old_score"], r["resource_group_score"], r["dmg"], r["yd"], -r["hp"]))[:10]
    data = {
        "rounds": rounds,
        "entry_limit": entry_limit,
        "source_limit": source_limit,
        "raw_goal_count": len(goals),
        "unique_goal_count": len(unique),
        "pareto_count": len(front),
        "top_by_resource_group": top_new,
        "top_by_old": top_old,
    }
    write_report(data)
    return data


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds", type=int, default=12)
    parser.add_argument("--entry-limit", type=int, default=360)
    parser.add_argument("--source-limit", type=int, default=28)
    args = parser.parse_args()
    data = build_report(args.rounds, args.entry_limit, args.source_limit)
    print(
        f"raw={data['raw_goal_count']} unique={data['unique_goal_count']} "
        f"pareto={data['pareto_count']}"
    )
    print(f"wrote {OUT_JSON}")
    print(f"wrote {OUT_MD}")


if __name__ == "__main__":
    main()
