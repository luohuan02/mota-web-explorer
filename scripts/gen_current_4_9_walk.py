#!/usr/bin/env python3
"""Write the current natural 4F-9F strategy walk used in comparison."""

from __future__ import annotations

# Allow scripts to import project-root modules after being moved under scripts/.
import os as _codex_os
import sys as _codex_sys
_codex_root = _codex_os.path.dirname(_codex_os.path.dirname(_codex_os.path.abspath(__file__)))
if _codex_root not in _codex_sys.path:
    _codex_sys.path.insert(0, _codex_root)

import os

import compare_strategy_results as compare
from src.solver import gen_walkthrough as gw
import run_guided_strategy_compare as guided


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)


def write_phase1_walk(candidate, path=None):
    if path is None:
        path = os.path.join("outputs", "walkthroughs", "walkthrough_current_4_9.md")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    chain = gw.trace_chain(candidate)
    lines = []
    lines.append("# Current Strategy 4-9 Walk")
    lines.append("")
    lines.append(
        f"> 终点: {gw.entry_summary(candidate)}"
    )
    lines.append("")

    for i in range(1, len(chain)):
        prev, curr = chain[i - 1], chain[i]
        si = curr.get("_step_info")
        if si is None:
            continue
        fid, target_ids, flyback = si
        entrances = gw.FLYBACK_ENTRANCES if flyback else gw.ENTRANCES
        sx, sy = entrances[fid]
        removed = prev.get("collected", {}).get(fid, frozenset())
        if fid in gw.FLOOR_13_COLLECTED:
            removed |= gw.FLOOR_13_COLLECTED[fid]
        target_state = {
            "hp": curr["hp"],
            "atk": curr["atk"],
            "def": curr["def"],
            "yk": curr["yk"],
            "bk": curr["bk"],
            "rk": curr["rk"],
        }
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

        desc = gw.FLOOR_NAMES.get(fid, fid)
        if flyback:
            desc += "(flyback)"
        target_names = [gw.EID_NAMES.get(t, t) for t in target_ids]
        lines.append(f"### {desc}: {'+'.join(target_names)}")
        if not steps:
            lines.append("  **无路径!**")
            lines.append("")
            continue

        prev_step = None
        for step in steps:
            lines.append(gw.format_step(step, prev_step))
            prev_step = step
        lines.append(f"  → {gw.entry_summary(curr, prev)}")
        lines.append("")

    lines.append("## 最终结果")
    lines.append("")
    lines.append(f"**{gw.entry_summary(candidate)}**")
    lines.append("")

    text = "\n".join(lines).rstrip() + "\n"
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return path


def main():
    entries = guided.run_guided_phase1(retry_level=0)
    candidates = compare.select_phase1_candidates(entries, limit=4)
    if not candidates:
        raise SystemExit("No current 4-9 candidates")
    candidate = candidates[0]
    path = write_phase1_walk(candidate)
    print(
        f"Wrote {path}: {gw.entry_summary(candidate)}"
    )


if __name__ == "__main__":
    main()
