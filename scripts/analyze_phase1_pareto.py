#!/usr/bin/env python3
"""Inspect retained Phase1 Pareto candidates after the 4F-9F shield stage."""

from __future__ import annotations

# Allow scripts to import project-root modules after being moved under scripts/.
import os as _codex_os
import sys as _codex_sys
_codex_root = _codex_os.path.dirname(_codex_os.path.dirname(_codex_os.path.abspath(__file__)))
if _codex_root not in _codex_sys.path:
    _codex_sys.path.insert(0, _codex_root)

import json
import os
from collections import defaultdict

from src.solver import gen_walkthrough as gw
import run_guided_strategy_compare as guided


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)


KEY_POS = {
    "mt7_redgem_3_1": ("MT7", (3, 1)),
    "mt7_door_3_5": ("MT7", (3, 5)),
    "mt7_redpotion_3_2": ("MT7", (3, 2)),
    "mt6_bluepriest_7_1": ("MT6", (7, 1)),
    "mt6_ykey_9_1": ("MT6", (9, 1)),
    "mt9_shield_9_7": ("MT9", (9, 7)),
    "mt9_redgem_6_5": ("MT9", (6, 5)),
    "mt9_bluegem_1_5": ("MT9", (1, 5)),
    "mt9_door_4_5": ("MT9", (4, 5)),
}


def state_key(e):
    return (e["atk"], e["def"], e["yk"], e["bk"], e["rk"])


def state_str(e):
    return gw.state_str(e["hp"], e["atk"], e["def"], e["yk"], e["bk"], e["rk"])


def has_pos(entry, fid, pos):
    return pos in entry.get("collected", {}).get(fid, frozenset())


def flags(entry):
    return {name: has_pos(entry, fid, pos) for name, (fid, pos) in KEY_POS.items()}


def sig(entry):
    return tuple(
        (fid, tuple(sorted(pos)))
        for fid, pos in sorted(entry.get("collected", {}).items())
        if pos
    )


def candidate_record(idx, entry):
    rec = {
        "idx": idx,
        "hp": entry["hp"],
        "atk": entry["atk"],
        "def": entry["def"],
        "yk": entry["yk"],
        "bk": entry["bk"],
        "rk": entry["rk"],
        "dmg": entry.get("_dmg", 0),
        "flags": flags(entry),
        "id": entry.get("_id"),
    }
    return rec


def table_line(idx, entry):
    f = flags(entry)
    return (
        f"| {idx} | {state_str(entry)} | {entry.get('_dmg', 0)} | "
        f"{'Y' if f['mt7_redgem_3_1'] else 'N'} | "
        f"{'Y' if f['mt7_door_3_5'] else 'N'} | "
        f"{'Y' if f['mt6_bluepriest_7_1'] else 'N'} | "
        f"{'Y' if f['mt6_ykey_9_1'] else 'N'} | "
        f"{'Y' if f['mt9_redgem_6_5'] else 'N'} | "
        f"{'Y' if f['mt9_bluegem_1_5'] else 'N'} |"
    )


def main():
    entries = guided.run_guided_phase1(retry_level=0)
    indexed = list(enumerate(entries, start=1))

    groups = defaultdict(list)
    for idx, entry in indexed:
        groups[state_key(entry)].append((idx, entry))

    exact_user_shape = [
        (idx, e) for idx, e in indexed
        if e["atk"] == 22 and e["def"] == 21 and e["yk"] == 2 and e["bk"] == 1 and e["rk"] == 0
    ]
    delayed_shape = [
        (idx, e) for idx, e in exact_user_shape
        if not flags(e)["mt7_redgem_3_1"]
    ]
    delayed_after_pick_shape = [
        (idx, e) for idx, e in indexed
        if e["atk"] == 23 and e["def"] == 21 and e["yk"] == 2 and e["bk"] == 1 and
        e["rk"] == 0 and flags(e)["mt7_redgem_3_1"]
    ]

    lines = []
    lines.append("# Phase1 Pareto Retention Report")
    lines.append("")
    lines.append(f"- retained entries: {len(entries)}")
    lines.append(f"- unique state buckets `(ATK,DEF,YK,BK,RK)`: {len(groups)}")
    lines.append(
        f"- exact delayed shape `ATK22 DEF21 YK2 BK1`: {len(exact_user_shape)}"
    )
    lines.append(
        f"- exact delayed shape without `7F(3,1)` red gem: {len(delayed_shape)}"
    )
    lines.append(
        f"- after-pick shape `ATK23 DEF21 YK2 BK1` with `7F(3,1)` red gem: {len(delayed_after_pick_shape)}"
    )
    lines.append("")

    def add_table(title, rows, limit=20):
        lines.append(f"## {title}")
        lines.append("")
        lines.append(
            "| # | state | dmg | 7F(3,1)红 | 7F(3,5)门 | 6F(7,1)法师 | 6F(9,1)钥匙 | 9F红 | 9F蓝 |"
        )
        lines.append("|---:|---|---:|---|---|---|---|---|---|")
        for idx, entry in rows[:limit]:
            lines.append(table_line(idx, entry))
        if len(rows) > limit:
            lines.append(f"| ... | omitted {len(rows) - limit} rows | | | | | | | |")
        lines.append("")

    add_table(
        "Lowest dmg retained candidates",
        sorted(indexed, key=lambda p: (p[1].get("_dmg", 0), -p[1]["hp"]))[:30],
        limit=30,
    )
    add_table(
        "Exact `ATK22 DEF21 YK2 BK1` candidates",
        sorted(exact_user_shape, key=lambda p: (p[1].get("_dmg", 0), -p[1]["hp"])),
        limit=30,
    )
    add_table(
        "Best candidate per state bucket",
        sorted(
            [min(rows, key=lambda p: (p[1].get("_dmg", 0), -p[1]["hp"])) for rows in groups.values()],
            key=lambda p: (p[1]["atk"], p[1]["def"], p[1]["yk"], p[1].get("_dmg", 0)),
            reverse=True,
        ),
        limit=80,
    )

    records = [candidate_record(idx, entry) for idx, entry in indexed]
    result_path = os.path.join("outputs", "results", "phase1_pareto_candidates.json")
    report_path = os.path.join("outputs", "reports", "phase1_pareto_report.md")
    os.makedirs(os.path.dirname(result_path), exist_ok=True)
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    text = "\n".join(lines).rstrip() + "\n"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(text)


if __name__ == "__main__":
    main()
