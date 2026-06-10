#!/usr/bin/env python3
"""Generate stable tracked walkthrough files for the current best boss result."""

from __future__ import annotations

import argparse
import json
import os
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
from scripts import merchant_finalscore_audit as audit
from scripts import post9_merchant_seed_search as seed_search
from scripts import run_corrected_phase1_best_boss_until_deadline as runner
from src.solver import gen_walkthrough as gw
from src.solver.full_search import search_with_path


DEFAULT_OUT_WALK = os.path.join("outputs", "walkthroughs", "walkthrough_current_best_boss.md")
DEFAULT_BEST_WALK = os.path.join("best", "current_best_boss_walk.md")
DEFAULT_BEST_JSON = os.path.join("best", "current_best_boss_summary.json")
DEFAULT_GUIDE_WALK = os.path.join("best", "guide_boss_walk.md")
DEFAULT_README = os.path.join("best", "README.md")
PHASE1_WALK = os.path.join("outputs", "walkthroughs", "walkthrough_corrected_phase1_best_no_merchant.md")


def fmt_score(value: float) -> str:
    return str(int(value)) if abs(value - int(value)) < 1e-9 else f"{value:.1f}"


def state_text(ent: dict[str, Any]) -> str:
    return (
        f"HP={ent['hp']} ATK={ent['atk']} DEF={ent['def']} "
        f"YK={ent['yk']} BK={ent['bk']} RK={ent['rk']} "
        f"G={cm.inferred_gold(ent)} dmg={ent.get('_dmg', 0)} "
        f"door={ent.get('_yd', 0)}/{ent.get('_bd', 0)}/{ent.get('_rd', 0)}"
    )


def compact_action(ent: dict[str, Any]) -> str:
    return ent.get("_last_action") or str(ent.get("_step_info"))


def step_kind(eid: str) -> str:
    if eid in cm.ENEMY_GOLD:
        return "kill"
    if eid in {"yellowDoor", "blueDoor", "redDoor"}:
        return "open"
    if eid in {"upFloor", "downFloor"}:
        return "pass"
    if eid == "fakeWall":
        return "pass"
    return "take"


def delta_text(step: dict[str, Any], before_gold: int, after_gold: int) -> str:
    pairs = [
        ("HP", step["hp_before"], step["hp_after"]),
        ("ATK", step.get("atk_before", step["atk"]), step["atk"]),
        ("DEF", step.get("def_before", step["def"]), step["def"]),
        ("YK", step.get("yk_before", step["yk"]), step["yk"]),
        ("BK", step.get("bk_before", step["bk"]), step["bk"]),
        ("RK", step.get("rk_before", step.get("rk", 0)), step.get("rk", 0)),
        ("G", before_gold, after_gold),
    ]
    parts = [f"{name} {before}->{after}" for name, before, after in pairs if before != after]
    return ", ".join(parts)


def reconstruct_segment(prev: dict[str, Any], curr: dict[str, Any]) -> list[str]:
    step_info = curr.get("_step_info")
    if not step_info:
        return ["- no floor step metadata"]
    fid, targets, flyback = step_info
    entrances = gw.FLYBACK_ENTRANCES if flyback else gw.ENTRANCES
    sx, sy = entrances[fid]
    removed = set(prev.get("collected", {}).get(fid, frozenset()))
    removed |= set(gw.FLOOR_13_COLLECTED.get(fid, frozenset()))
    target_state = {
        "hp": curr["hp"],
        "atk": curr["atk"],
        "def": curr["def"],
        "yk": curr["yk"],
        "bk": curr["bk"],
        "rk": curr["rk"],
    }
    path_target_state = dict(target_state)
    is_boss = fid == "MT10" and ("redDoor" in targets or "skeletonCaptain" in targets)
    if is_boss:
        path_target_state["hp"] = curr["hp"] + gw.boss_event_damage(curr["atk"], curr["def"])
        if "redDoor" in targets:
            path_target_state["hp"] += gw.calc_dmg("skeletonCaptain", curr["atk"], curr["def"])
    steps, _final, _vis_pos = search_with_path(
        gw.maps[fid],
        sx,
        sy,
        prev["hp"],
        prev["atk"],
        prev["def"],
        prev["yk"],
        prev["bk"],
        prev["rk"],
        list(targets),
        max_iter=500000,
        removed_pos=removed,
        target_state=path_target_state,
    )
    if not steps:
        return [f"- reconstruction failed for {fid} targets={targets} flyback={flyback}"]
    if is_boss:
        steps = gw.expand_mt10_boss_event_steps(steps)

    lines: list[str] = []
    gold = cm.inferred_gold(prev)
    for item in steps:
        if isinstance(item, str):
            text = item.strip()
            if "(6,5)" in text:
                text = (
                    "MT10 x6y5 trigger boss event: skeletonCaptain moves to x6y1; "
                    "x6y3 becomes an event wall; 2 skeletonSoldiers and 6 skeletons spawn"
                )
            elif "(6,3)" in text:
                text = "MT10 x6y3 event wall opens after spawned monsters are killed"
            lines.append(f"- {text}")
            continue
        before_gold = gold
        gain = cm.ENEMY_GOLD.get(item["eid"], 0)
        gold += gain
        delta = delta_text(item, before_gold, gold)
        suffix = f" [{delta}]" if delta else ""
        gain_text = f" (+{gain}G)" if gain else ""
        lines.append(
            f"- {fid} x{item['x']}y{item['y']} {step_kind(item['eid'])} "
            f"{item['eid']}{suffix}{gain_text}"
        )
    expected_gold = cm.inferred_gold(curr)
    if gold != expected_gold:
        lines.append(f"- warning: reconstructed gold={gold}, expected={expected_gold}")
    return lines


def phase1_walk_body() -> list[str]:
    if not os.path.exists(PHASE1_WALK):
        return ["_Phase1 detailed walk not found._"]
    lines = open(PHASE1_WALK, encoding="utf-8").read().splitlines()
    start = 0
    for idx, line in enumerate(lines):
        if line.startswith("## Detailed Steps"):
            start = idx
            break
    return lines[start:]


def run_best(args: argparse.Namespace) -> dict[str, Any]:
    cm.ensure_merchant_maps()
    seed = runner.load_corrected_best_seed(args)
    result = seed_search.run_post9_from_seed(
        seed,
        stat_rounds=args.stat_rounds,
        redkey_rounds=args.redkey_rounds,
        boss_rounds=args.boss_rounds,
        entry_limit=args.entry_limit,
        source_limit=args.source_limit,
    )
    best = result["best_ent"]
    if best is None:
        raise RuntimeError("no boss goal found")
    record = audit.score_record("current_best", best, source="corrected phase1 best continuation")
    if args.expect_final_score and abs(record["final_score"] - args.expect_final_score) > 1e-9:
        raise RuntimeError(
            f"unexpected final-score: expected={args.expect_final_score} actual={record['final_score']}"
        )
    return {"seed": seed, "best": best, "record": record, "search": result}


def write_walk(result: dict[str, Any], output: str) -> None:
    seed = result["seed"]
    best = result["best"]
    record = result["record"]
    chain = gw.trace_chain(best)
    os.makedirs(os.path.dirname(output), exist_ok=True)
    lines = [
        "# Current Best Boss Walk",
        "",
        "## Summary",
        "",
        f"- phase1 seed: {state_text(seed)}",
        f"- final: {state_text(best)}",
        f"- final-score: {fmt_score(record['final_score'])}",
        f"- remaining groups: {fmt_score(record['remaining_group_value'])}",
        f"- future monster gold: {record['future_monster_gold']}G",
        f"- merchants used: {', '.join(record['merchants']) or '-'}",
        "",
        "## Phase1 4F-9F Detailed Walk",
        "",
    ]
    lines.extend(phase1_walk_body())
    lines.extend(["", "## Post9 Compact Actions", ""])
    for idx, ent in enumerate(chain):
        if idx == 0:
            lines.append(f"0. seed -> {state_text(ent)}")
        else:
            lines.append(f"{idx}. {compact_action(ent)} -> {state_text(ent)}")
    lines.extend(["", "## Post9 Detailed Steps", ""])
    for idx in range(1, len(chain)):
        prev = chain[idx - 1]
        curr = chain[idx]
        lines.append(f"### {idx}. {compact_action(curr)}")
        lines.append("")
        lines.append(f"- before: {state_text(prev)}")
        lines.extend(reconstruct_segment(prev, curr))
        lines.append(f"- after: {state_text(curr)}")
        lines.append("")
    with open(output, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")


def write_summary(result: dict[str, Any], output: str) -> None:
    record = audit.compact_record(result["record"])
    payload = {
        "summary": record,
        "state": state_text(result["best"]),
        "actions": cm.trace_actions(result["best"]),
        "search": {
            "goal_count": result["search"]["goal_count"],
            "merchant_goal_count": result["search"]["merchant_goal_count"],
            "entry_count": result["search"]["entry_count"],
            "elapsed": result["search"]["elapsed"],
        },
    }
    os.makedirs(os.path.dirname(output), exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def write_best_readme(output: str, record: dict[str, Any]) -> None:
    state = (
        f"HP={record['hp']} ATK={record['atk']} DEF={record['def']} "
        f"YK={record['yk']} BK={record['bk']} RK={record['rk']} "
        f"G={record['gold']} dmg={record['dmg']} "
        f"door={record['yd']}/{record['bd']}/{record['rd']} "
        f"final-score={fmt_score(record['final_score'])}"
    )
    lines = [
        "# Best Walk Artifacts",
        "",
        "Tracked stable walkthroughs:",
        "",
        "- `current_best_boss_walk.md`: current best final-score boss route.",
        "- `guide_boss_walk.md`: guide baseline boss route.",
        "- `current_best_boss_summary.json`: machine-readable summary for current best.",
        "",
        "Scoring model:",
        "",
        "- `1YK = 50HP`, `1BK = 4YK = 200HP`, `100G = 1YK = 50HP`.",
        "- `final-score` includes current HP/key/gold stock plus full-map remaining resource groups.",
        "- Future monster gold is counted as zero-damage future income; unopened doors still cost key value.",
        "- Unused merchants are future net resources and merchant purchases consume actual gold.",
        "- Guide source: https://www.taptap.cn/moment/15225056477054087",
        "",
        "Current best:",
        "",
        "```text",
        state,
        "```",
        "",
        "Important source/resource paths to keep:",
        "",
        "- `AGENTS.md`, `CLAUDE.md`, `README.md`, `.gitignore`",
        "- `config/`, `data/`, `src/`, `scripts/`, `tests/`",
        "- `browser-profile/` locally, because it stores the h5mota browser save/profile.",
        "- Current strategy scripts: `scripts/post9_gem_supply_search.py`, `scripts/post9_action_search.py`, `scripts/post9_resource_group_search.py`, `scripts/post9_merchant_seed_search.py`, `scripts/run_corrected_phase1_best_boss_until_deadline.py`.",
        "- Current corrected scoring/search scripts: `scripts/compare_merchant_resource_paths.py`, `scripts/long_merchant_phase1_search.py`, `scripts/rescore_merchant_phase1_cache.py`, `scripts/gen_corrected_merchant_phase1_best_walk.py`, `scripts/gen_best_current_boss_walk.py`.",
        "- Guide/delayed scripts: `scripts/fixed_shield_strategy.py`, `scripts/replay_user_post9_route.py`, `scripts/continue_delayed_phase1_with_post9_resource.py`, `scripts/gen_delayed_phase1_detailed_walk.py`, `scripts/compare_delayed_phase1_vs_user_guide.py`.",
        "- Tests: `tests/run_merchant_fullmap_score_test.py`, plus existing solver/search regression tests.",
        "",
        "Note: older `1482.5` artifacts in ignored `outputs/` are stale. They were invalidated by the MT10 special-action guard because MT10 resources must not be reachable before the MT9 upFloor route is actually opened.",
        "",
        "`outputs/` remains ignored by git and can hold temporary search runs/checkpoints.",
        "",
    ]
    os.makedirs(os.path.dirname(output), exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def copy_guide_walk(output: str) -> None:
    cm.ensure_merchant_maps()
    audit.install_post9_resource_group_hooks()
    guide_ent = cm.guide_full_ent()
    record = audit.score_record("guide", guide_ent, source="fixed guide boss replay")
    state = (
        f"HP={record['hp']} ATK={record['atk']} DEF={record['def']} "
        f"YK={record['yk']} BK={record['bk']} RK={record['rk']} "
        f"G={record['gold']} dmg={record['dmg']} "
        f"door={record['yd']}/{record['bd']}/{record['rd']} "
        f"final-score={fmt_score(record['final_score'])}"
    )
    actions = cm.trace_actions(guide_ent)
    lines = [
        "# Guide Baseline Boss Walk",
        "",
        "Manual guide source:",
        "https://www.taptap.cn/moment/15225056477054087",
        "",
        "Scoring model:",
        "",
        "- `1YK = 50HP`, `1BK = 4YK = 200HP`, `100G = 1YK = 50HP`.",
        "- This file records the fixed guide baseline under the current full-map final-score model.",
        "",
        "Guide baseline:",
        "",
        "```text",
        state,
        "```",
    ]
    if actions:
        lines.extend(["", "Compact replay actions:", ""])
        for idx, action in enumerate(actions, 1):
            lines.append(f"{idx}. {action}")
    else:
        lines.extend([
            "",
            "The fixed guide baseline is stored here as a clean scored replay state. For the original step-by-step manual route, use the TapTap guide link above.",
        ])
    os.makedirs(os.path.dirname(output), exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-cache", default=runner.DEFAULT_STATE_CACHE)
    parser.add_argument("--rescore-json", default=runner.DEFAULT_RESCORE_JSON)
    parser.add_argument("--stat-rounds", type=int, default=12)
    parser.add_argument("--redkey-rounds", type=int, default=6)
    parser.add_argument("--boss-rounds", type=int, default=6)
    parser.add_argument("--entry-limit", type=int, default=620)
    parser.add_argument("--source-limit", type=int, default=36)
    parser.add_argument("--expect-final-score", type=float, default=0)
    parser.add_argument("--output-walk", default=DEFAULT_OUT_WALK)
    parser.add_argument("--best-walk", default=DEFAULT_BEST_WALK)
    parser.add_argument("--best-json", default=DEFAULT_BEST_JSON)
    parser.add_argument("--guide-walk", default=DEFAULT_GUIDE_WALK)
    parser.add_argument("--best-readme", default=DEFAULT_README)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = run_best(args)
    write_walk(result, args.output_walk)
    write_walk(result, args.best_walk)
    write_summary(result, args.best_json)
    copy_guide_walk(args.guide_walk)
    write_best_readme(args.best_readme, result["record"])
    print(f"wrote {args.output_walk}")
    print(f"wrote {args.best_walk}")
    print(f"wrote {args.best_json}")
    print(f"wrote {args.guide_walk}")
    print(f"wrote {args.best_readme}")


if __name__ == "__main__":
    main()
