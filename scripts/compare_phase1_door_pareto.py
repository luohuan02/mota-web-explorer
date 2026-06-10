#!/usr/bin/env python3
"""Compare Phase1 frontiers with and without cumulative door-cost Pareto."""

from __future__ import annotations

# Allow scripts to import project-root modules after being moved under scripts/.
import os as _codex_os
import sys as _codex_sys
_codex_root = _codex_os.path.dirname(_codex_os.path.dirname(_codex_os.path.abspath(__file__)))
if _codex_root not in _codex_sys.path:
    _codex_sys.path.insert(0, _codex_root)

import json
import os
import time

import fixed_shield_strategy as fixed
from src.solver import gen_walkthrough as gw
import run_guided_strategy_compare as guided


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

OUT_MD = os.path.join("outputs", "reports", "phase1_door_pareto_comparison.md")
OUT_JSON = os.path.join("outputs", "results", "phase1_door_pareto_comparison.json")

MILESTONES = [
    ("MT4", ["upFloor"], False),
    ("MT5", ["sword1"], False),
    ("MT4", ["redGem", "yellowKey", "redPotion"], True),
    ("MT5", ["upFloor"], True),
    ("MT6", ["upFloor"], False),
    ("MT7", ["redGem", "redPotion"], False),
    ("MT7", ["upFloor"], False),
    ("MT8", ["upFloor"], False),
    ("MT9", ["shield1"], False),
    ("MT9", ["redGem", "blueGem", "yellowKey"], True),
]


def state_str(e):
    return (
        f"HP={e['hp']} ATK={e['atk']} DEF={e['def']} "
        f"YK={e['yk']} BK={e['bk']} RK={e['rk']}"
    )


def full_str(e):
    return (
        f"{state_str(e)} dmg={e.get('_dmg', 0)} "
        f"door={e.get('_yd', 0)}/{e.get('_bd', 0)}/{e.get('_rd', 0)} "
        f"futureKeys={gw.phase1_future_key_score(e)}"
    )


def sig_from_collected(collected):
    return tuple(
        (fid, tuple(sorted(pos)))
        for fid, pos in sorted((collected or {}).items())
        if pos
    )


def fixed_until(prefix_result, segment_index):
    segment_names = {s["name"] for s in prefix_result["segments"][: segment_index + 1]}
    collected = gw.initial_collected_state()
    hp = atk = def_ = yk = bk = rk = None
    dmg = yd = bd = rd = 0
    for step in prefix_result["steps"]:
        if step["segment"] not in segment_names:
            continue
        collected.setdefault(step["floor"], frozenset())
        if step["type"] in {"monster", "door", "item"}:
            current = set(collected.get(step["floor"], frozenset()))
            current.add((step["x"], step["y"]))
            collected[step["floor"]] = frozenset(current)
        if step["type"] == "monster":
            dmg += max(0, step["state_before"]["hp"] - step["state_after"]["hp"])
        if step["eid"] == "yellowDoor":
            yd += 1
        elif step["eid"] == "blueDoor":
            bd += 1
        elif step["eid"] == "redDoor":
            rd += 1
        after = step["state_after"]
        hp, atk, def_, yk, bk, rk = (
            after["hp"],
            after["atk"],
            after["def"],
            after["yk"],
            after["bk"],
            after["rk"],
        )
    return {
        "hp": hp,
        "atk": atk,
        "def": def_,
        "yk": yk,
        "bk": bk,
        "rk": rk,
        "collected": collected,
        "_dmg": dmg,
        "_yd": yd,
        "_bd": bd,
        "_rd": rd,
    }


def entry_unique_key(e):
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
        sig_from_collected(e.get("collected", {})),
    )


def unique_entries(entries):
    out = []
    seen = set()
    for e in entries:
        key = entry_unique_key(e)
        if key in seen:
            continue
        seen.add(key)
        out.append(e)
    return out


def flags(e):
    c = e.get("collected", {})
    pairs = [
        ("7F_red", "MT7", (3, 1)),
        ("7F_door35", "MT7", (3, 5)),
        ("6F_mage", "MT6", (7, 1)),
        ("6F_yk", "MT6", (9, 1)),
        ("9F_red", "MT9", (6, 5)),
        ("9F_blue", "MT9", (1, 5)),
    ]
    return " ".join(f"{name}={'Y' if pos in c.get(fid, frozenset()) else 'N'}" for name, fid, pos in pairs)


def top_rows(entries, limit=10):
    entries = unique_entries(entries)
    chosen = []
    seen = set()

    def add(seq):
        for e in seq:
            key = entry_unique_key(e)
            if key in seen:
                continue
            seen.add(key)
            chosen.append(e)
            if len(chosen) >= limit:
                return

    add(sorted(entries, key=lambda e: (e.get("_dmg", 0), e.get("_yd", 0), e.get("_bd", 0), e.get("_rd", 0), -e["hp"])))
    add(sorted(entries, key=lambda e: (-gw.phase1_future_key_score(e), e.get("_dmg", 0), e.get("_yd", 0), -e["hp"])))
    add(sorted(entries, key=lambda e: (-e["yk"], -e["bk"], e.get("_dmg", 0), e.get("_yd", 0), -e["hp"])))
    add(sorted(entries, key=lambda e: (-e["hp"], e.get("_dmg", 0), e.get("_yd", 0), -e["yk"])))
    return chosen[:limit]


def analyze_stage(entries, fixed_entry):
    entries = unique_entries(entries)
    fixed_sig = sig_from_collected(fixed_entry["collected"])
    exact = [e for e in entries if sig_from_collected(e.get("collected", {})) == fixed_sig]
    same_state = [
        e for e in entries
        if all(e[k] == fixed_entry[k] for k in ("hp", "atk", "def", "yk", "bk", "rk"))
    ]
    same_bucket = [
        e for e in entries
        if all(e[k] == fixed_entry[k] for k in ("atk", "def", "yk", "bk", "rk"))
    ]
    delayed = [
        e for e in entries
        if e["atk"] == 22 and e["def"] == 21 and e["yk"] == 2 and
        e["bk"] == 1 and e["rk"] == 0 and
        (3, 1) not in e.get("collected", {}).get("MT7", frozenset())
    ]
    return {
        "count": len(entries),
        "fixed": {
            "state": {
                "hp": fixed_entry["hp"],
                "atk": fixed_entry["atk"],
                "def": fixed_entry["def"],
                "yk": fixed_entry["yk"],
                "bk": fixed_entry["bk"],
                "rk": fixed_entry["rk"],
                "dmg": fixed_entry.get("_dmg", 0),
                "yd": fixed_entry.get("_yd", 0),
                "bd": fixed_entry.get("_bd", 0),
                "rd": fixed_entry.get("_rd", 0),
            },
            "exact_collected": bool(exact),
            "same_full_state": len(same_state),
            "same_resource_bucket": len(same_bucket),
            "delayed_bucket": len(delayed),
        },
        "top": [
            {
                "state": {
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
                },
                "futureKeys": gw.phase1_future_key_score(e),
                "flags": flags(e),
            }
            for e in top_rows(entries)
        ],
    }


def run_phase1(use_door_pareto):
    gw.USE_DOOR_COST_PARETO = use_door_pareto
    gw.PHASE1_BUCKETS_ENABLED = True
    gw._entry_store.clear()
    gw._next_id[0] = 1
    start = {
        "hp": gw.hero["h"],
        "atk": gw.hero["a"],
        "def": gw.hero["d"],
        "yk": gw.hero["yk"],
        "bk": gw.hero["bk"],
        "rk": 0,
        "collected": gw.initial_collected_state(),
        "_id": 1,
        "_parent_id": None,
        "_step_info": None,
        "_dmg": 0,
        "_yd": 0,
        "_bd": 0,
        "_rd": 0,
    }
    gw._entry_store[1] = dict(start)
    entries = [start.copy()]
    history = []
    t0 = time.time()
    for idx, (fid, targets, force_flyback) in enumerate(MILESTONES, 1):
        s0 = time.time()
        entries = guided.run_one_milestone(entries, fid, targets, force_flyback, retry_level=0)
        history.append({
            "idx": idx,
            "fid": fid,
            "targets": targets,
            "count": len(entries),
            "elapsed": time.time() - s0,
        })
        if not entries:
            raise RuntimeError(f"Phase1 failed at {fid} {targets}")
    return {
        "elapsed": time.time() - t0,
        "history": history,
        "shield_entries": history[8]["count"],
        "gem_entries": history[9]["count"],
        "shield_stage": stage_entries_at(use_door_pareto, 9),
    }, entries


def run_until(use_door_pareto, stop_idx):
    gw.USE_DOOR_COST_PARETO = use_door_pareto
    gw.PHASE1_BUCKETS_ENABLED = True
    gw._entry_store.clear()
    gw._next_id[0] = 1
    start = {
        "hp": gw.hero["h"],
        "atk": gw.hero["a"],
        "def": gw.hero["d"],
        "yk": gw.hero["yk"],
        "bk": gw.hero["bk"],
        "rk": 0,
        "collected": gw.initial_collected_state(),
        "_id": 1,
        "_parent_id": None,
        "_step_info": None,
        "_dmg": 0,
        "_yd": 0,
        "_bd": 0,
        "_rd": 0,
    }
    gw._entry_store[1] = dict(start)
    entries = [start.copy()]
    for fid, targets, force_flyback in MILESTONES[:stop_idx]:
        entries = guided.run_one_milestone(entries, fid, targets, force_flyback, retry_level=0)
        if not entries:
            raise RuntimeError(f"Phase1 failed at {fid} {targets}")
    return entries


def stage_entries_at(use_door_pareto, stop_idx):
    return run_until(use_door_pareto, stop_idx)


def run_phase1_snapshots(use_door_pareto):
    gw.USE_DOOR_COST_PARETO = use_door_pareto
    gw.PHASE1_BUCKETS_ENABLED = True
    gw._entry_store.clear()
    gw._next_id[0] = 1
    start = {
        "hp": gw.hero["h"],
        "atk": gw.hero["a"],
        "def": gw.hero["d"],
        "yk": gw.hero["yk"],
        "bk": gw.hero["bk"],
        "rk": 0,
        "collected": gw.initial_collected_state(),
        "_id": 1,
        "_parent_id": None,
        "_step_info": None,
        "_dmg": 0,
        "_yd": 0,
        "_bd": 0,
        "_rd": 0,
    }
    gw._entry_store[1] = dict(start)
    entries = [start.copy()]
    shield_entries = []
    redblue_entries = []
    t0 = time.time()
    for idx, (fid, targets, force_flyback) in enumerate(MILESTONES, 1):
        entries = guided.run_one_milestone(entries, fid, targets, force_flyback, retry_level=0)
        if not entries:
            raise RuntimeError(f"Phase1 failed at {fid} {targets}")
        if idx == 9:
            shield_entries = list(entries)
        elif idx == 10:
            redblue_entries = list(entries)
    return time.time() - t0, shield_entries, redblue_entries


def write_outputs(results):
    lines = []
    lines.append("# Phase1 Door Pareto Comparison")
    lines.append("")
    for mode_name, data in results.items():
        lines.append(f"## {mode_name}")
        lines.append("")
        lines.append(f"- elapsed: {data['elapsed']:.1f}s")
        lines.append(f"- unique shield states: {data['shield']['count']}")
        lines.append(f"- unique 9F red+blue states: {data['redblue']['count']}")
        lines.append("")
        for stage_key, title in [("shield", "4-9 shield"), ("redblue", "9F red+blue gems")]:
            stage = data[stage_key]
            fixed_state = stage["fixed"]["state"]
            lines.append(f"### {title}")
            lines.append("")
            lines.append(
                f"- fixed: HP={fixed_state['hp']} ATK={fixed_state['atk']} DEF={fixed_state['def']} "
                f"YK={fixed_state['yk']} BK={fixed_state['bk']} RK={fixed_state['rk']} "
                f"dmg={fixed_state['dmg']} door={fixed_state['yd']}/{fixed_state['bd']}/{fixed_state['rd']}"
            )
            lines.append(f"- exact collected retained: {'YES' if stage['fixed']['exact_collected'] else 'NO'}")
            lines.append(f"- same full state retained: {stage['fixed']['same_full_state']}")
            lines.append(f"- same resource bucket retained: {stage['fixed']['same_resource_bucket']}")
            if stage_key == "redblue":
                lines.append(f"- delayed ATK22 DEF21 YK2 BK1 bucket retained: {stage['fixed']['delayed_bucket']}")
            lines.append("")
            lines.append("| # | state | dmg | doors Y/B/R | futureKeys | flags |")
            lines.append("|---:|---|---:|---:|---:|---|")
            for idx, row in enumerate(stage["top"], 1):
                st = row["state"]
                lines.append(
                    f"| {idx} | HP={st['hp']} ATK={st['atk']} DEF={st['def']} "
                    f"YK={st['yk']} BK={st['bk']} RK={st['rk']} | "
                    f"{st['dmg']} | {st['yd']}/{st['bd']}/{st['rd']} | "
                    f"{row['futureKeys']} | {row['flags']} |"
                )
            lines.append("")

    os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


def main():
    prefix_result = fixed.replay_route()
    fixed_shield = fixed_until(prefix_result, 7)
    fixed_redblue = fixed_until(prefix_result, 8)
    results = {}
    for label, use_door in [("legacy_key_only", False), ("door_cost_pareto", True)]:
        print(f"Running {label}...")
        elapsed, shield_entries, redblue_entries = run_phase1_snapshots(use_door)
        results[label] = {
            "elapsed": elapsed,
            "shield": analyze_stage(shield_entries, fixed_shield),
            "redblue": analyze_stage(redblue_entries, fixed_redblue),
        }
        print(
            f"  {label}: elapsed={results[label]['elapsed']:.1f}s "
            f"shield={results[label]['shield']['count']} redblue={results[label]['redblue']['count']}"
        )
    gw.USE_DOOR_COST_PARETO = True
    write_outputs(results)
    print(f"Wrote {OUT_MD}")
    print(f"Wrote {OUT_JSON}")


if __name__ == "__main__":
    main()
