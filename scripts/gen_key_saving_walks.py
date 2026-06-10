#!/usr/bin/env python3
"""Generate walks for key-saving representative Phase1 candidates."""

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

import continue_selected_phase1_candidates as selected
from gen_guided_candidate_walk import append_chain_walk, clone_chain, clone_entry, entry_state
import run_guided_strategy_compare as guided
from src.solver import gen_walkthrough as gw


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

WALK_DIR = os.path.join("outputs", "walkthroughs")
RESULT_DIR = os.path.join("outputs", "results")


def state_record(entry):
    return {
        "hp": entry["hp"],
        "atk": entry["atk"],
        "def": entry["def"],
        "yk": entry["yk"],
        "bk": entry["bk"],
        "rk": entry["rk"],
        "dmg": entry.get("_dmg", 0),
        "yd": entry.get("_yd", 0),
        "bd": entry.get("_bd", 0),
        "rd": entry.get("_rd", 0),
    }


def state_line(record):
    return (
        f"HP={record['hp']} ATK={record['atk']} DEF={record['def']} "
        f"YK={record['yk']} BK={record['bk']} RK={record['rk']} "
        f"dmg={record['dmg']} doorY/B/R={record['yd']}/{record['bd']}/{record['rd']}"
    )


def write_yk3_full(item, phase1_chain):
    t0 = time.time()
    candidate = item["entry"]
    print(f"Continue {item['label']}: {gw.entry_summary(candidate)}")
    result = gw.run_search(
        retry_level=0,
        initial_entry=clone_entry(candidate),
        skip_phase1=True,
    )
    if result is None:
        raise SystemExit("current_atk23_yk3 continuation failed")

    continuation_chain = clone_chain(gw.trace_chain(result))
    phase1 = state_record(candidate)
    final = state_record(result)

    lines = []
    lines.append("# Natural Candidate ATK23 YK3 Walk")
    lines.append("")
    lines.append(f"> Phase1: {gw.entry_summary(candidate)}")
    lines.append(f"> Final: {gw.entry_summary(result)}")
    lines.append("")
    lines.append("## Key Notes")
    lines.append("")
    lines.append("- Compared with `current_atk23_yk2_bk1`, this candidate keeps one extra yellow key at Phase1.")
    lines.append("- It still spends all keys by the final Boss state, so the saving is temporary unless later routing uses it better.")
    lines.append("")
    append_chain_walk(lines, phase1_chain, "Natural Phase1")
    append_chain_walk(lines, continuation_chain, "Continuation To Boss")
    lines.append("## Final")
    lines.append("")
    lines.append(f"**{gw.entry_summary(result)}**")
    lines.append("")

    os.makedirs(WALK_DIR, exist_ok=True)
    os.makedirs(RESULT_DIR, exist_ok=True)
    md_path = os.path.join(WALK_DIR, "walkthrough_natural_atk23_yk3.md")
    json_path = os.path.join(RESULT_DIR, "walkthrough_natural_atk23_yk3_summary.json")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "label": item["label"],
                "phase1": phase1,
                "final": final,
                "elapsed": time.time() - t0,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    print(f"Wrote {md_path}")
    print(f"Wrote {json_path}")
    return {"label": item["label"], "phase1": phase1, "final": final, "walk": md_path}


def write_bk_retained_phase1(items, phase1_chains):
    bk_items = [item for item in items if item["start"]["bk"] >= 1]
    lines = []
    lines.append("# BK-Retained Phase1 Representative Walks")
    lines.append("")
    lines.append("| label | Phase1 state | flags |")
    lines.append("|---|---|---|")
    for item in bk_items:
        record = state_record(item["entry"])
        flags = item["flags"]
        flag_text = (
            f"7Fgem={'Y' if flags['mt7_redgem_3_1'] else 'N'}, "
            f"7Fdoor={'Y' if flags['mt7_door_3_5'] else 'N'}, "
            f"6Fmage={'Y' if flags['mt6_bluepriest_7_1'] else 'N'}, "
            f"6Fkey={'Y' if flags['mt6_ykey_9_1'] else 'N'}"
        )
        lines.append(f"| {item['label']} | {state_line(record)} | {flag_text} |")
    lines.append("")
    lines.append("> These are Phase1 walks only. Some representatives previously timed out or failed in continuation.")
    lines.append("")

    for item in bk_items:
        chain = phase1_chains[item["label"]]
        append_chain_walk(lines, chain, f"{item['label']} Phase1")

    os.makedirs(WALK_DIR, exist_ok=True)
    path = os.path.join(WALK_DIR, "walkthrough_bk_retained_phase1_candidates.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")
    print(f"Wrote {path}")
    return path


def main():
    t0 = time.time()
    print("Run guided Phase1...")
    entries = guided.run_guided_phase1(retry_level=0)
    items = selected.select_candidates(entries)
    phase1_chains = {
        item["label"]: clone_chain(gw.trace_chain(item["entry"]))
        for item in items
    }
    by_label = {item["label"]: item for item in items}
    if "current_atk23_yk3" not in by_label:
        raise SystemExit("current_atk23_yk3 not found")

    yk3 = write_yk3_full(by_label["current_atk23_yk3"], phase1_chains["current_atk23_yk3"])
    bk_path = write_bk_retained_phase1(items, phase1_chains)

    summary_path = os.path.join(RESULT_DIR, "key_saving_walks_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "yk3": yk3,
                "bk_retained_phase1_walk": bk_path,
                "bk_retained_labels": [item["label"] for item in items if item["start"]["bk"] >= 1],
                "elapsed": time.time() - t0,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    print(f"Wrote {summary_path}")
    print(f"elapsed={time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
