#!/usr/bin/env python3
"""Generate a detailed 4F-9F walkthrough for the current merchant-score best."""

from __future__ import annotations

import json
import os
import sys
from types import SimpleNamespace
from typing import Any


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.chdir(ROOT)

from scripts import compare_merchant_resource_paths as cm
from scripts import merchant_finalscore_audit as audit
from src.solver import gen_walkthrough as gw
from src.solver.full_search import search_with_path


OUT_MD = os.path.join("outputs", "walkthroughs", "walkthrough_merchant_finalscore_best.md")
OUT_JSON = os.path.join("outputs", "results", "merchant_finalscore_best_walk.json")


def state_text(ent: dict[str, Any]) -> str:
    return (
        f"HP={ent['hp']} ATK={ent['atk']} DEF={ent['def']} "
        f"YK={ent['yk']} BK={ent['bk']} RK={ent['rk']} "
        f"G={cm.inferred_gold(ent, include_boss_spawn=False)} "
        f"dmg={ent.get('_dmg', 0)} "
        f"door={ent.get('_yd', 0)}/{ent.get('_bd', 0)}/{ent.get('_rd', 0)}"
    )


def core_state(ent: dict[str, Any]) -> dict[str, int]:
    return {
        "hp": ent["hp"],
        "atk": ent["atk"],
        "def": ent["def"],
        "yk": ent["yk"],
        "bk": ent["bk"],
        "rk": ent["rk"],
    }


def step_action(eid: str) -> str:
    if eid in cm.ENEMY_GOLD:
        return "kill"
    if eid in {"yellowDoor", "blueDoor", "redDoor"}:
        return "open"
    if eid in {"upFloor", "downFloor"}:
        return "pass"
    if eid.startswith("merchant:"):
        return "reach"
    if eid == "fakeWall":
        return "pass"
    return "take"


def delta_text(before: dict[str, int], after: dict[str, int], before_gold: int, after_gold: int) -> str:
    labels = {
        "hp": "HP",
        "atk": "ATK",
        "def": "DEF",
        "yk": "YK",
        "bk": "BK",
        "rk": "RK",
    }
    parts = []
    for key, label in labels.items():
        if before[key] != after[key]:
            parts.append(f"{label} {before[key]}->{after[key]}")
    if before_gold != after_gold:
        parts.append(f"G {before_gold}->{after_gold}")
    return ", ".join(parts)


def map_eid(fid: str, x: int, y: int) -> str:
    for bx, by, _kind, eid in gw.maps[fid]["bl"]:
        if bx == x and by == y:
            return eid
    raise KeyError(f"{fid} x{x}y{y}")


def reconstruct_segment(prev: dict[str, Any], curr: dict[str, Any]) -> tuple[list[str], set[tuple[int, int]]]:
    fid, targets, flyback = curr["_step_info"]
    targets = list(targets)
    is_merchant = len(targets) == 1 and targets[0].startswith("merchant:")
    target_state = core_state(curr)
    merchant = None
    if is_merchant:
        merchant = cm.MERCHANT_BY_EID[targets[0]]
        target_state = dict(target_state)
        target_state["yk"] -= merchant.yk_gain
        target_state["bk"] -= merchant.bk_gain

    entrances = gw.FLYBACK_ENTRANCES if flyback else gw.ENTRANCES
    sx, sy = entrances[fid]
    removed = set(prev.get("collected", {}).get(fid, frozenset()))
    removed |= set(gw.FLOOR_13_COLLECTED.get(fid, frozenset()))
    steps, _final, vis_pos = search_with_path(
        gw.maps[fid],
        sx,
        sy,
        prev["hp"],
        prev["atk"],
        prev["def"],
        prev["yk"],
        prev["bk"],
        prev["rk"],
        targets,
        max_iter=500000,
        removed_pos=removed,
        target_state=target_state,
    )
    if not steps:
        raise RuntimeError(f"cannot reconstruct {curr.get('_last_action') or curr['_step_info']}")

    gold = cm.inferred_gold(prev, include_boss_spawn=False)
    lines: list[str] = []
    for step in steps:
        x, y = step["x"], step["y"]
        eid = step["eid"]
        if eid.startswith("__target_"):
            eid = map_eid(fid, x, y)
        before = {
            "hp": step["hp_before"],
            "atk": step.get("atk_before", step["atk"]),
            "def": step.get("def_before", step["def"]),
            "yk": step.get("yk_before", step["yk"]),
            "bk": step.get("bk_before", step["bk"]),
            "rk": step.get("rk_before", step.get("rk", 0)),
        }
        after = {
            "hp": step["hp_after"],
            "atk": step["atk"],
            "def": step["def"],
            "yk": step["yk"],
            "bk": step["bk"],
            "rk": step.get("rk", before["rk"]),
        }
        before_gold = gold
        gained = cm.ENEMY_GOLD.get(eid, 0)
        gold += gained
        note = f" (+{gained}G)" if gained else ""
        delta = delta_text(before, after, before_gold, gold)
        suffix = f" [{delta}]" if delta else ""
        lines.append(f"- {fid} x{x}y{y} {step_action(eid)} {eid}{suffix}{note}")

    if merchant is not None:
        before = target_state
        before_gold = gold
        after = {
            "hp": target_state["hp"],
            "atk": target_state["atk"],
            "def": target_state["def"],
            "yk": target_state["yk"] + merchant.yk_gain,
            "bk": target_state["bk"] + merchant.bk_gain,
            "rk": target_state["rk"],
        }
        gold -= merchant.spend_gold
        delta = delta_text(before, after, before_gold, gold)
        lines.append(
            f"- {fid} x{merchant.pos[0]}y{merchant.pos[1]} buy {merchant.label} "
            f"[{delta}] (-{merchant.spend_gold}G)"
        )

    expected_gold = cm.inferred_gold(curr, include_boss_spawn=False)
    if gold != expected_gold:
        lines.append(f"- warning: reconstructed gold={gold}, expected={expected_gold}")
    return lines, set(vis_pos)


def find_best_phase1() -> dict[str, Any]:
    cm.ensure_merchant_maps()
    args = SimpleNamespace(
        max_expansions=80,
        min_expansions=20,
        goal_limit=8,
        report_limit=8,
        start_gold=cm.DEFAULT_START_GOLD,
    )
    goals, _meta = cm.run_search(args)
    goals.sort(key=lambda ent: (-cm.final_stock_with_gold(ent), ent.get("_dmg", 0), -ent["hp"]))
    if not goals:
        raise RuntimeError("no merchant phase1 goals")
    return goals[0]


def write_walk(best: dict[str, Any]) -> None:
    chain = gw.trace_chain(best)
    record = audit.score_record("merchant", best, source="phase1 merchant search")
    os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump({
            "summary": audit.compact_record(record),
            "actions": cm.trace_actions(best),
        }, f, ensure_ascii=False, indent=2)

    lines = [
        "# Merchant Final-Score Best Walk",
        "",
        "## Summary",
        "",
        f"- final: {state_text(best)}",
        f"- merchants used: {', '.join(record['merchants']) or '-'}",
        f"- current full-map final-score: {audit.fmt_score(record['final_score'])}",
        f"- future monster gold: {record['future_monster_gold']}G",
        f"- full-map remaining resources: {audit.fmt_score(record['remaining_group_value'])}",
        "",
        "## Compact Actions",
        "",
    ]
    for idx, action in enumerate(cm.trace_actions(best), 1):
        lines.append(f"{idx}. {action}")
    lines.extend(["", "## Detailed Steps", ""])

    for idx in range(1, len(chain)):
        prev = chain[idx - 1]
        curr = chain[idx]
        action = curr.get("_last_action") or str(curr.get("_step_info"))
        lines.append(f"### {idx}. {action}")
        lines.append("")
        lines.append(f"- before: {state_text(prev)}")
        try:
            step_lines, _vis = reconstruct_segment(prev, curr)
            lines.extend(step_lines)
        except Exception as exc:  # Keep the walk file useful even if one replay variant drifts.
            lines.append(f"- reconstruction failed: {exc}")
        lines.append(f"- after: {state_text(curr)}")
        lines.append("")

    lines.extend([
        "## Score Note",
        "",
        "This route is selected by the current full-map final-score model: remaining monsters are future zero-damage gold, unopened yellow/blue doors still cost key value, and unused merchants are future net resources.",
        "",
    ])
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")


def main() -> None:
    best = find_best_phase1()
    write_walk(best)
    print(f"wrote {OUT_MD}")
    print(f"wrote {OUT_JSON}")


if __name__ == "__main__":
    main()
