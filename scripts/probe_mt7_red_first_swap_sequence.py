#!/usr/bin/env python3
"""Replay a current-best-like sequence with MT7 redGem moved to the front."""

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

from scripts import compare_merchant_resource_paths as cm
from scripts import merchant_finalscore_audit as audit
from scripts import post9_resource_group_search as rg
from scripts import run_corrected_phase1_best_boss_until_deadline as runner
from src.solver import gen_walkthrough as gw


OUT_JSON = os.path.join("outputs", "results", "mt7_red_first_swap_sequence.json")
OUT_MD = os.path.join("outputs", "reports", "mt7_red_first_swap_sequence.md")

SEQUENCES = {
    "blue-up": [
    ("MT7", "redGem"),
    ("MT1", "blueGem"),
    ("MT3", "blueGem"),
    ("MT8", "blueGem"),
    ("MT6", "blueGem"),
    ("MT3", "redGem"),
    ("MT5", "blueGem"),
    ("MT4", "blueKey"),
    ("MT7", "yellowKey"),
    ("MT9_BLUE_UP", "upFloor"),
    ("MT10_DIRECT", "blueGem"),
    ("MT6", "yellowKey"),
    ("MT10", "redGem"),
    ("MT7", "bluePotion"),
    ("MT8", "redKey"),
    ("MT10", "bluePotion"),
    ("MT1", "bluePotion"),
    ],
    "user-mt7": [
        ("MT7", "redGem"),
        ("MT7_SKEL_KEY", "yellowKey"),
        ("MT6", "blueGem"),
        ("MT3", "blueGem"),
        ("MT1", "blueGem"),
        ("MT3", "redGem"),
        ("MT8", "blueGem"),
        ("MT5_DIRECT", "blueGem"),
        ("MT4_DIRECT", "blueKey"),
        ("MT9_BLUE_UP", "upFloor"),
        ("MT10_DIRECT", "blueGem"),
        ("MT7_RIGHT_KEY", "yellowKey"),
        ("MT10", "redGem"),
        ("MT10", "bluePotion"),
        ("MT6", "yellowKey"),
        ("MT8", "redKey"),
        ("MT1", "bluePotion"),
        ("MT7", "bluePotion"),
    ],
    "user-def-before-key": [
        ("MT7", "redGem"),
        ("MT3", "blueGem"),
        ("MT6", "blueGem"),
        ("MT7_SKEL_KEY", "yellowKey"),
        ("MT1", "blueGem"),
        ("MT8", "blueGem"),
        ("MT3", "redGem"),
        ("MT5_DIRECT", "blueGem"),
        ("MT4_DIRECT", "blueKey"),
        ("MT9_BLUE_UP", "upFloor"),
        ("MT10_DIRECT", "blueGem"),
        ("MT7_RIGHT_KEY", "yellowKey"),
        ("MT10", "redGem"),
        ("MT10", "bluePotion"),
        ("MT6", "yellowKey"),
        ("MT8", "redKey"),
        ("MT1", "bluePotion"),
        ("MT7", "bluePotion"),
    ],
}


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


def compact(label: str, ent: dict[str, Any] | None, source: str) -> dict[str, Any] | None:
    if ent is None:
        return None
    return audit.compact_record(audit.score_record(label, ent, source=source))


def load_seed(args: argparse.Namespace) -> dict[str, Any]:
    ns = argparse.Namespace(state_cache=args.state_cache, rescore_json=args.rescore_json)
    return runner.load_corrected_best_seed(ns)


def unique_trim(entries: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    if not entries:
        return []
    trimmed = rg.trim_entries(entries, max(limit, 1))
    pools = [
        sorted(trimmed, key=lambda e: (-cm.final_stock_with_gold(e), e.get("_dmg", 0), -e["hp"])),
        sorted(trimmed, key=lambda e: (e.get("_dmg", 0), e.get("_yd", 0), e.get("_bd", 0), -e["hp"])),
        sorted(trimmed, key=lambda e: (-e["yk"], -e["bk"], e.get("_dmg", 0), -e["hp"])),
    ]
    out: list[dict[str, Any]] = []
    seen: set[int] = set()
    for pool in pools:
        for ent in pool:
            eid = ent.get("_id")
            if eid in seen:
                continue
            seen.add(eid)
            out.append(ent)
            if len(out) >= limit:
                return out
    return out


def apply_step(entries: list[dict[str, Any]], fid: str, target: str, limit: int) -> list[dict[str, Any]]:
    generated: list[dict[str, Any]] = []
    for ent in entries:
        generated.extend(audit.merchant_aware_apply_action(ent, fid, target))
    return unique_trim(generated, limit)


def run(args: argparse.Namespace) -> dict[str, Any]:
    cm.ensure_merchant_maps()
    audit.install_post9_resource_group_hooks()
    seed = audit.seed_for_post9(load_seed(args))
    entries = [seed]
    rows = [{"step": "seed", "count": 1, "best": compact("seed", seed, "corrected seed")}]

    sequence = SEQUENCES[args.variant]
    for fid, target in sequence:
        entries = apply_step(entries, fid, target, args.beam)
        rows.append({
            "step": f"{fid}:{target}",
            "count": len(entries),
            "best": compact(f"{fid}:{target}", entries[0], "mt7 red first swap") if entries else None,
        })
        if not entries:
            break

    boss_entries: list[dict[str, Any]] = []
    if entries:
        for ent in entries:
            boss_entries.extend(rg.base.boss_action(ent))
    boss_entries = unique_trim(boss_entries, args.beam)
    best_boss = boss_entries[0] if boss_entries else None
    return {
        "config": vars(args),
        "sequence": [f"{fid}:{target}" for fid, target in sequence],
        "rows": rows,
        "boss_count": len(boss_entries),
        "best_boss": compact("mt7_red_first_swap_boss", best_boss, "mt7 red first swap") if best_boss else None,
    }


def write_outputs(data: dict[str, Any], out_json: str, out_md: str) -> None:
    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    os.makedirs(os.path.dirname(out_md), exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    lines = [
        "# MT7 Red First Swap Sequence",
        "",
        f"- beam: `{data['config']['beam']}`",
        f"- boss candidates: `{data['boss_count']}`",
        "",
        "| step | kept | best state | final-score |",
        "|---|---:|---|---:|",
    ]
    for row in data["rows"]:
        best = row.get("best")
        lines.append(
            f"| {row['step']} | {row['count']} | "
            f"{state_text_from_record(best)} | {fmt_score(best['final_score']) if best else '-'} |"
        )
    best = data.get("best_boss")
    lines.extend([
        "",
        "## Boss",
        "",
        f"- best: `{state_text_from_record(best)}`",
        f"- final-score: `{fmt_score(best['final_score']) if best else '-'}`",
    ])
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")


def state_text_from_record(row: dict[str, Any] | None) -> str:
    if row is None:
        return "-"
    return (
        f"HP={row['hp']} ATK={row['atk']} DEF={row['def']} "
        f"YK={row['yk']} BK={row['bk']} RK={row['rk']} "
        f"G={row['gold']} dmg={row['dmg']} door={row['yd']}/{row['bd']}/{row['rd']}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-cache", default=runner.DEFAULT_STATE_CACHE)
    parser.add_argument("--rescore-json", default=runner.DEFAULT_RESCORE_JSON)
    parser.add_argument("--variant", choices=sorted(SEQUENCES), default="blue-up")
    parser.add_argument("--beam", type=int, default=16)
    parser.add_argument("--out-json", default=OUT_JSON)
    parser.add_argument("--out-md", default=OUT_MD)
    args = parser.parse_args()
    data = run(args)
    write_outputs(data, args.out_json, args.out_md)
    best = data.get("best_boss")
    print(f"boss_count={data['boss_count']} best={fmt_score(best['final_score']) if best else '-'} {state_text_from_record(best)}")


if __name__ == "__main__":
    main()
