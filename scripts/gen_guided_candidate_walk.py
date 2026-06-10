#!/usr/bin/env python3
"""Generate a walk for the best guided natural Phase1 candidate.

This does not overwrite walkthrough.md.  It writes a separate comparison walk
so the guided route can be inspected against the fixed-prefix best route.
"""

from __future__ import annotations

# Allow scripts to import project-root modules after being moved under scripts/.
import os as _codex_os
import sys as _codex_sys
_codex_root = _codex_os.path.dirname(_codex_os.path.dirname(_codex_os.path.abspath(__file__)))
if _codex_root not in _codex_sys.path:
    _codex_sys.path.insert(0, _codex_root)

import copy
import os
import time

from src.solver import gen_walkthrough as gw
import run_guided_strategy_compare as guided


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)


def clone_entry(entry):
    cloned = dict(entry)
    cloned["collected"] = {
        fid: frozenset(pos_set)
        for fid, pos_set in entry.get("collected", {}).items()
    }
    return cloned


def clone_chain(chain):
    return [clone_entry(entry) for entry in chain]


def entry_state(e):
    return gw.state_str(e["hp"], e["atk"], e["def"], e["yk"], e["bk"], e["rk"])


def append_chain_walk(lines, chain, title):
    lines.append(f"## {title}")
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
        path_target_state = dict(target_state)
        is_mt10_boss = fid == "MT10" and (
            "skeletonCaptain" in target_ids or "redDoor" in target_ids
        )
        if is_mt10_boss:
            path_target_state["hp"] = curr["hp"] + gw.boss_event_damage(
                curr["atk"], curr["def"]
            )
            if "redDoor" in target_ids:
                path_target_state["hp"] += gw.calc_dmg(
                    "skeletonCaptain", curr["atk"], curr["def"]
                )

        steps, final, vis_pos = gw.search_with_path(
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
            target_state=path_target_state,
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

        if is_mt10_boss:
            steps = gw.expand_mt10_boss_event_steps(steps)
        prev_step = None
        for step in steps:
            if isinstance(step, str):
                lines.append(step)
                prev_step = None
            else:
                lines.append(gw.format_step(step, prev_step))
                prev_step = step
        lines.append(f"  → {entry_state(curr)}")
        lines.append("")


def main():
    t0 = time.time()
    print("Run guided Phase1...")
    entries = guided.run_guided_phase1(retry_level=0)
    candidates = guided.select_candidates(entries, limit=3)
    if not candidates:
        raise SystemExit("No guided candidates")
    candidate = candidates[0]
    phase1_chain = clone_chain(gw.trace_chain(candidate))

    print(f"Selected candidate #1: {entry_state(candidate)}")
    print("Continue selected candidate...")
    continuation_start = clone_entry(candidate)
    result = gw.run_search(
        retry_level=0,
        initial_entry=continuation_start,
        skip_phase1=True,
    )
    continuation_chain = []
    if result:
        continuation_chain = clone_chain(gw.trace_chain(result))
        print(f"Final: {entry_state(result)}")
    else:
        print("Continuation failed after corrected MT1/MT3 flyback entrances")

    lines = []
    lines.append("# Guided Phase1 Candidate #1 Walk")
    lines.append("")
    lines.append(f"> Phase1候选: {entry_state(candidate)}")
    if result:
        lines.append(f"> 最终: {entry_state(result)}")
    else:
        lines.append("> 最终: 续搜失败（已修正1/3楼flyback入口后）")
    lines.append(f"> 对照当前固定前缀最优: HP=32 ATK=27 DEF=27 YK=0 BK=0 RK=0")
    lines.append("")
    append_chain_walk(lines, phase1_chain, "新Phase1自然剑盾路线")
    if continuation_chain:
        append_chain_walk(lines, continuation_chain, "续搜：27攻27防、红钥匙、10楼Boss")
    else:
        lines.append("## 续搜：27攻27防、红钥匙、10楼Boss")
        lines.append("")
        lines.append("修正 1/3 楼 flyback 入口后，这个候选没有完成后续通关。")
        lines.append("")
    lines.append("## 最终结果")
    lines.append("")
    if result:
        lines.append(f"**{entry_state(result)}**")
    else:
        lines.append("**续搜失败**")
    lines.append("")

    text = "\n".join(lines).rstrip() + "\n"
    out_dir = os.path.join("outputs", "walkthroughs")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "walkthrough_guided_candidate1.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"Wrote {out_path}")
    print(f"elapsed={time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
