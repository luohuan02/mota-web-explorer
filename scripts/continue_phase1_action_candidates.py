#!/usr/bin/env python3
"""Continue representative action-search Phase1 candidates to Boss clear."""

from __future__ import annotations

import json
import os
import sys
import time
import argparse


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.chdir(ROOT)

from src.solver import gen_walkthrough as gw
import phase1_action_search as phase1


OUT_JSON = os.path.join("outputs", "results", "phase1_action_continuation.json")
OUT_MD = os.path.join("outputs", "reports", "phase1_action_continuation.md")


def state_dict(e):
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
    }


def state_text(e):
    st = state_dict(e) if "_dmg" in e or "_yd" in e else e
    return (
        f"HP={st['hp']} ATK={st['atk']} DEF={st['def']} "
        f"YK={st['yk']} BK={st['bk']} RK={st['rk']} "
        f"dmg={st['dmg']} door={st['yd']}/{st['bd']}/{st['rd']}"
    )


def sig(e):
    return (
        e["hp"], e["atk"], e["def"], e["yk"], e["bk"], e["rk"],
        e.get("_dmg", 0), e.get("_yd", 0), e.get("_bd", 0), e.get("_rd", 0),
        tuple(
            (fid, tuple(sorted(pos)))
            for fid, pos in sorted((e.get("collected") or {}).items())
            if pos
        ),
    )


def best(entries, pred, key):
    matches = [e for e in entries if pred(e)]
    if not matches:
        return None
    return sorted(matches, key=key)[0]


def select_candidates(goal_entries):
    specs = [
        (
            "fixed_exact",
            lambda e: phase1.fixed_exact_match(e),
            lambda e: (e.get("_dmg", 0), -e["hp"]),
        ),
        (
            "best_dmg",
            lambda e: True,
            lambda e: (e.get("_dmg", 0), e.get("_yd", 0), e.get("_bd", 0), -e["hp"]),
        ),
        (
            "best_bk1_bd0",
            lambda e: e["bk"] >= 1 and e.get("_bd", 0) == 0,
            lambda e: (e.get("_dmg", 0), e.get("_yd", 0), -e["hp"]),
        ),
        (
            "delayed_7f_red_bd0",
            lambda e: (
                e["atk"] == 22 and e["def"] == 21 and e["yk"] >= 2 and
                e["bk"] >= 1 and e.get("_bd", 0) == 0 and
                not phase1.has_item(e, "MT7", "redGem")
            ),
            lambda e: (e.get("_dmg", 0), e.get("_yd", 0), -e["yk"], -e["hp"]),
        ),
        (
            "atk23_yk2_bk1_bd0_7f_red_left",
            lambda e: (
                e["atk"] == 23 and e["def"] == 21 and e["yk"] == 2 and
                e["bk"] == 1 and e.get("_bd", 0) == 0 and
                not phase1.has_item(e, "MT7", "redGem")
            ),
            lambda e: (e.get("_dmg", 0), e.get("_yd", 0), -e["hp"]),
        ),
        (
            "atk23_yk2_bk1_bd0",
            lambda e: (
                e["atk"] == 23 and e["def"] == 21 and e["yk"] == 2 and
                e["bk"] == 1 and e.get("_bd", 0) == 0
            ),
            lambda e: (e.get("_dmg", 0), e.get("_yd", 0), -e["hp"]),
        ),
        (
            "low_ydoor_bk1",
            lambda e: e["bk"] >= 1 and e["atk"] >= 23 and e["def"] >= 21,
            lambda e: (e.get("_yd", 0), e.get("_bd", 0), e.get("_dmg", 0), -e["hp"]),
        ),
        (
            "high_hp_bk1",
            lambda e: e["bk"] >= 1,
            lambda e: (-e["hp"], e.get("_dmg", 0), e.get("_yd", 0), e.get("_bd", 0)),
        ),
    ]
    selected = []
    seen = set()
    for label, pred, key in specs:
        e = best(goal_entries, pred, key)
        if not e:
            continue
        s = sig(e)
        if s in seen:
            continue
        seen.add(s)
        selected.append((label, e))
    return selected


def continue_one(label, entry, phase1_actions=None):
    initial = dict(entry)
    initial["collected"] = {
        fid: frozenset(pos)
        for fid, pos in (entry.get("collected") or {}).items()
    }
    if phase1_actions is None:
        phase1_actions = phase1.chain_labels(entry)
    gw.PHASE1_BUCKETS_ENABLED = False
    t0 = time.time()
    result = gw.run_search(retry_level=0, initial_entry=initial, skip_phase1=True, result_objective="dmg")
    elapsed = time.time() - t0
    return {
        "label": label,
        "phase1": state_dict(entry),
        "phase1_actions": phase1_actions,
        "ok": result is not None,
        "elapsed": elapsed,
        "final": state_dict(result) if result else None,
    }


def write_outputs(data):
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    lines = [
        "# Phase1 Action Continuation",
        "",
        f"- phase1 elapsed: {data['phase1_search']['elapsed']:.1f}s",
        f"- selected candidates: {len(data['candidates'])}",
        "",
        "| # | label | phase1 | result | elapsed |",
        "|---:|---|---|---|---:|",
    ]
    for idx, row in enumerate(data["candidates"], 1):
        result = "FAILED"
        if row["ok"]:
            f = row["final"]
            result = (
                f"HP={f['hp']} ATK={f['atk']} DEF={f['def']} "
                f"YK={f['yk']} BK={f['bk']} RK={f['rk']} "
                f"dmg={f['dmg']} door={f['yd']}/{f['bd']}/{f['rd']}"
            )
        p = row["phase1"]
        phase = (
            f"HP={p['hp']} ATK={p['atk']} DEF={p['def']} "
            f"YK={p['yk']} BK={p['bk']} RK={p['rk']} "
            f"dmg={p['dmg']} door={p['yd']}/{p['bd']}/{p['rd']}"
        )
        lines.append(
            f"| {idx} | {row['label']} | {phase} | {result} | {row['elapsed']:.1f}s |"
        )
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-expansions", type=int, default=350)
    parser.add_argument("--goal-limit", type=int, default=200)
    parser.add_argument(
        "--labels",
        default="",
        help="Comma-separated candidate labels to continue; default continues all selected labels.",
    )
    parser.add_argument("--out-suffix", default="")
    args = parser.parse_args()

    global OUT_JSON, OUT_MD
    if args.out_suffix:
        OUT_JSON = os.path.join("outputs", "results", f"phase1_action_continuation_{args.out_suffix}.json")
        OUT_MD = os.path.join("outputs", "reports", f"phase1_action_continuation_{args.out_suffix}.md")

    t0 = time.time()
    phase = phase1.run(max_expansions=args.max_expansions, goal_limit=args.goal_limit, include_entries=True)
    goals = phase["_goal_entries"]
    selected = select_candidates(goals)
    wanted = {x.strip() for x in args.labels.split(",") if x.strip()}
    if wanted:
        selected = [(label, entry) for label, entry in selected if label in wanted]
    selected = [
        (label, entry, phase1.chain_labels(entry))
        for label, entry in selected
    ]
    rows = []
    data = {
        "elapsed": 0.0,
        "phase1_search": {
            "elapsed": phase["elapsed"],
            "expansions": phase["expansions"],
            "goal_entries": phase["goal_entries"],
            "fixed_exact_count": phase["fixed_exact_count"],
        },
        "candidates": rows,
    }
    for label, entry, phase1_actions in selected:
        print(f"continue {label}: {state_text(entry)}", flush=True)
        rows.append(continue_one(label, entry, phase1_actions=phase1_actions))
        if rows[-1]["ok"]:
            print(f"  ok {state_text(rows[-1]['final'])}", flush=True)
        else:
            print("  failed", flush=True)
        data["elapsed"] = time.time() - t0
        write_outputs(data)
    data["elapsed"] = time.time() - t0
    write_outputs(data)
    print(f"wrote {OUT_JSON}")
    print(f"wrote {OUT_MD}")


if __name__ == "__main__":
    main()
