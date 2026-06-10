#!/usr/bin/env python3
"""Compare fixed 4F-9F prefix, current natural strategy, and full walkthrough."""

from __future__ import annotations

# Allow scripts to import project-root modules after being moved under scripts/.
import os as _codex_os
import sys as _codex_sys
_codex_root = _codex_os.path.dirname(_codex_os.path.dirname(_codex_os.path.abspath(__file__)))
if _codex_root not in _codex_sys.path:
    _codex_sys.path.insert(0, _codex_root)

import json
import os
from collections import Counter

import fixed_shield_strategy as fixed
from src.solver import gen_walkthrough as gw
import run_guided_strategy_compare as guided


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

POTION_HP = {
    "redPotion": 50,
    "bluePotion": 200,
}

RUN_FULL_CONTINUATION = False
FULL_CONTINUATION_NOTE = (
    "A separate full-continuation attempt timed out at 15 minutes: sampled "
    "candidate #1 and #2 did not produce a complete route, and candidate #3 was "
    "still running when the command timed out."
)


def state_dict(entry):
    return {
        "hp": entry["hp"],
        "atk": entry["atk"],
        "def": entry["def"],
        "yk": entry["yk"],
        "bk": entry["bk"],
        "rk": entry["rk"],
    }


def state_str(state):
    return (
        f"HP={state['hp']} ATK={state['atk']} DEF={state['def']} "
        f"YK={state['yk']} BK={state['bk']} RK={state['rk']}"
    )


def empty_metric():
    return {
        "battle_damage": 0,
        "potion_hp": 0,
        "steps": 0,
        "doors": Counter(),
        "items": Counter(),
        "monsters": Counter(),
        "monster_damage": Counter(),
    }


def add_damage(metric, eid, before_hp, after_hp):
    dmg = max(0, before_hp - after_hp)
    metric["battle_damage"] += dmg
    metric["monsters"][eid] += 1
    metric["monster_damage"][eid] += dmg


def add_fixed_step(metric, step):
    metric["steps"] += 1
    eid = step["eid"]
    if step["type"] == "monster":
        add_damage(metric, eid, step["state_before"]["hp"], step["state_after"]["hp"])
    elif step["type"] == "door":
        metric["doors"][eid] += 1
    elif step["type"] == "item":
        metric["items"][eid] += 1
        metric["potion_hp"] += POTION_HP.get(eid, 0)


def add_search_step(metric, step):
    if isinstance(step, str):
        return
    metric["steps"] += 1
    eid = step["eid"]
    action = step["action"]
    if action == "击杀":
        add_damage(metric, eid, step["hp_before"], step["hp_after"])
    elif action == "开门":
        metric["doors"][eid] += 1
    elif action == "拾取":
        metric["items"][eid] += 1
        metric["potion_hp"] += POTION_HP.get(eid, 0)


def fixed_4_9_metric():
    result = fixed.replay_route()
    metric = empty_metric()
    for step in result["steps"]:
        add_fixed_step(metric, step)
    return {
        "state": state_dict(result["final_state"]),
        "metric": metric,
        "dmg": metric["battle_damage"],
    }


def reconstruct_guided_phase1(candidate):
    chain = gw.trace_chain(candidate)
    segments = []
    for i in range(1, len(chain)):
        prev, curr = chain[i - 1], chain[i]
        si = curr.get("_step_info")
        if not si:
            continue
        fid, target_ids, flyback = si
        entrances = gw.FLYBACK_ENTRANCES if flyback else gw.ENTRANCES
        sx, sy = entrances[fid]
        removed = prev.get("collected", {}).get(fid, frozenset())
        if fid in gw.FLOOR_13_COLLECTED:
            removed |= gw.FLOOR_13_COLLECTED[fid]
        target_state = state_dict(curr)
        steps, final, vis = gw.search_with_path(
            gw.maps[fid],
            sx,
            sy,
            prev["hp"],
            prev["atk"],
            prev["def"],
            prev["yk"],
            prev["bk"],
            prev["rk"],
            target_ids,
            max_iter=500000,
            removed_pos=removed,
            target_state=target_state,
        )
        segments.append((fid, target_ids, flyback, curr, steps or []))
    return segments


def guided_4_9_metric(candidate):
    metric = empty_metric()
    for fid, target_ids, flyback, curr, steps in reconstruct_guided_phase1(candidate):
        for step in steps:
            add_search_step(metric, step)
    return {
        "state": state_dict(candidate),
        "metric": metric,
        "dmg": candidate.get("_dmg", metric["battle_damage"]),
    }


def candidate_signature(entry):
    collected_sig = tuple(
        (fid, tuple(sorted(pos)))
        for fid, pos in sorted(entry.get("collected", {}).items())
        if pos
    )
    return (
        entry["hp"],
        entry["atk"],
        entry["def"],
        entry["yk"],
        entry["bk"],
        entry["rk"],
        collected_sig,
    )


def select_phase1_candidates(entries, limit=4):
    delayed = [
        e for e in entries
        if e["atk"] == 22 and e["def"] == 21 and e["yk"] >= 2 and e["bk"] >= 1 and
        (3, 1) not in e.get("collected", {}).get("MT7", frozenset())
    ]
    valid = [
        e for e in entries
        if e["atk"] >= 23 and e["def"] >= 21 and e["yk"] >= 2 and e["bk"] >= 1
    ]
    if not valid:
        valid = list(entries)
    selectors = [
        lambda e: (e.get("_dmg", 0), -e["hp"], -e["yk"], -(e["atk"] + e["def"])),
        lambda e: (-e["hp"], e.get("_dmg", 0), -e["yk"], -(e["atk"] + e["def"])),
        lambda e: (-e["yk"], -e["bk"], e.get("_dmg", 0), -e["hp"]),
        lambda e: (-(e["atk"] + e["def"]), e.get("_dmg", 0), -e["hp"], -e["yk"]),
    ]
    selected = []
    seen = set()
    if delayed:
        entry = sorted(delayed, key=lambda e: (e.get("_dmg", 0), -e["hp"]))[0]
        sig = candidate_signature(entry)
        seen.add(sig)
        selected.append(entry)
    for selector in selectors:
        for entry in sorted(valid, key=selector):
            sig = candidate_signature(entry)
            if sig in seen:
                continue
            seen.add(sig)
            selected.append(entry)
            break
        if len(selected) >= limit:
            break
    return selected


def run_current_strategy():
    entries = guided.run_guided_phase1(retry_level=0)
    candidates = select_phase1_candidates(entries)
    candidate_metrics = []
    for idx, candidate in enumerate(candidates, start=1):
        candidate_metrics.append(
            {
                "index": idx,
                "candidate": candidate,
                "phase1": guided_4_9_metric(candidate),
            }
        )

    full_results = []
    if RUN_FULL_CONTINUATION:
        for item in candidate_metrics:
            candidate = item["candidate"]
            print(
                f"continue current candidate #{item['index']}: "
                f"{state_str(state_dict(candidate))} dmg={candidate.get('_dmg', 0)}",
                flush=True,
            )
            result = gw.run_search(retry_level=0, initial_entry=candidate, skip_phase1=True)
            item["full"] = result
            if result:
                full_results.append(item)
    else:
        for item in candidate_metrics:
            item["full"] = None

    if full_results:
        best = min(
            full_results,
            key=lambda item: (item["full"].get("_dmg", 0), -item["full"]["hp"]),
        )
    else:
        best = min(
            candidate_metrics,
            key=lambda item: (item["phase1"]["dmg"], -item["phase1"]["state"]["hp"]),
        )
    return best, candidate_metrics


def load_full_walkthrough_summary():
    path = os.path.join("outputs", "results", "walkthrough_fixed_prefix_summary.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def counter_line(counter):
    if not counter:
        return "none"
    return ", ".join(f"{key}={value}" for key, value in sorted(counter.items()))


def row_metric(lines, label, fixed_value, new_value):
    if isinstance(fixed_value, int) and isinstance(new_value, int):
        delta = f"{new_value - fixed_value:+d}"
    else:
        delta = "-"
    lines.append(f"| {label} | {fixed_value} | {new_value} | {delta} |")


def write_report(fixed_phase1, current_best, candidate_metrics, full_summary):
    current_phase1 = current_best["phase1"]
    current_full = current_best.get("full")
    lines = []
    lines.append("# Strategy Result Comparison")
    lines.append("")
    lines.append("## 4-9 shield prefix")
    lines.append("")
    lines.append("| metric | fixed prefix | current strategy | delta |")
    lines.append("|---|---:|---:|---:|")
    row_metric(lines, "battle dmg", fixed_phase1["dmg"], current_phase1["dmg"])
    row_metric(lines, "potion HP taken", fixed_phase1["metric"]["potion_hp"], current_phase1["metric"]["potion_hp"])
    row_metric(lines, "steps", fixed_phase1["metric"]["steps"], current_phase1["metric"]["steps"])
    row_metric(lines, "final HP", fixed_phase1["state"]["hp"], current_phase1["state"]["hp"])
    row_metric(lines, "final ATK", fixed_phase1["state"]["atk"], current_phase1["state"]["atk"])
    row_metric(lines, "final DEF", fixed_phase1["state"]["def"], current_phase1["state"]["def"])
    row_metric(lines, "final YK", fixed_phase1["state"]["yk"], current_phase1["state"]["yk"])
    row_metric(lines, "final BK", fixed_phase1["state"]["bk"], current_phase1["state"]["bk"])
    lines.append("")
    lines.append(f"- fixed state: {state_str(fixed_phase1['state'])}")
    lines.append(f"- current state: {state_str(current_phase1['state'])}")
    lines.append(f"- fixed items: {counter_line(fixed_phase1['metric']['items'])}")
    lines.append(f"- current items: {counter_line(current_phase1['metric']['items'])}")
    lines.append(f"- fixed doors: {counter_line(fixed_phase1['metric']['doors'])}")
    lines.append(f"- current doors: {counter_line(current_phase1['metric']['doors'])}")
    lines.append("")
    lines.append("## Full walkthrough")
    lines.append("")
    lines.append("| metric | fixed-prefix walkthrough | current strategy continuation | delta |")
    lines.append("|---|---:|---:|---:|")
    fixed_full_dmg = full_summary["final"]["dmg"]
    fixed_full_state = full_summary["final"]["state"]
    if current_full:
        current_full_state = state_dict(current_full)
        current_full_dmg = current_full.get("_dmg", 0)
        row_metric(lines, "total dmg", fixed_full_dmg, current_full_dmg)
        row_metric(lines, "final HP", fixed_full_state["hp"], current_full_state["hp"])
        row_metric(lines, "final ATK", fixed_full_state["atk"], current_full_state["atk"])
        row_metric(lines, "final DEF", fixed_full_state["def"], current_full_state["def"])
        row_metric(lines, "final YK", fixed_full_state["yk"], current_full_state["yk"])
        row_metric(lines, "final BK", fixed_full_state["bk"], current_full_state["bk"])
        row_metric(lines, "final RK", fixed_full_state["rk"], current_full_state["rk"])
        lines.append("")
        lines.append(f"- fixed-prefix full: {state_str(fixed_full_state)} dmg={fixed_full_dmg}")
        lines.append(f"- current full: {state_str(current_full_state)} dmg={current_full_dmg}")
    else:
        row_metric(lines, "total dmg", fixed_full_dmg, "not run")
        lines.append("")
        lines.append(f"- fixed-prefix full: {state_str(fixed_full_state)} dmg={fixed_full_dmg}")
        lines.append("- current full: not run in the fast comparison report")
        lines.append(f"- note: {FULL_CONTINUATION_NOTE}")
    lines.append("")
    lines.append("## Current candidates")
    lines.append("")
    lines.append("| # | 4-9 state | 4-9 dmg | full result |")
    lines.append("|---:|---|---:|---|")
    for item in candidate_metrics:
        candidate = item["candidate"]
        phase1 = item["phase1"]
        full = item.get("full")
        if full:
            full_text = f"{state_str(state_dict(full))} dmg={full.get('_dmg', 0)}"
        else:
            full_text = "not run"
        lines.append(
            f"| {item['index']} | {state_str(state_dict(candidate))} | "
            f"{phase1['dmg']} | {full_text} |"
        )
    lines.append("")

    text = "\n".join(lines).rstrip() + "\n"
    out_path = os.path.join("outputs", "reports", "strategy_result_comparison.md")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(text)


def main():
    fixed_phase1 = fixed_4_9_metric()
    current_best, candidate_metrics = run_current_strategy()
    full_summary = load_full_walkthrough_summary()
    write_report(fixed_phase1, current_best, candidate_metrics, full_summary)


if __name__ == "__main__":
    main()
