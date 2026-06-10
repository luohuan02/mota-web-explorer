#!/usr/bin/env python3
"""Check whether the hand-written fixed 4F-9F prefix is retained by Phase1 Pareto."""

from __future__ import annotations

# Allow scripts to import project-root modules after being moved under scripts/.
import os as _codex_os
import sys as _codex_sys
_codex_root = _codex_os.path.dirname(_codex_os.path.dirname(_codex_os.path.abspath(__file__)))
if _codex_root not in _codex_sys.path:
    _codex_sys.path.insert(0, _codex_root)

import json
import os

import fixed_shield_strategy as fixed
from src.solver import gen_walkthrough as gw
import run_guided_strategy_compare as guided


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)


def state_str(e):
    return gw.state_str(e["hp"], e["atk"], e["def"], e["yk"], e["bk"], e["rk"])


def sig_from_collected(collected):
    return tuple(
        (fid, tuple(sorted(pos)))
        for fid, pos in sorted(collected.items())
        if pos
    )


def fixed_collected(prefix_result):
    return {
        fid: frozenset((p["x"], p["y"]) for p in positions)
        for fid, positions in prefix_result["collected"].items()
    }


def key_flags(entry):
    c = entry.get("collected", {})
    return {
        "7F(3,1)redGem": (3, 1) in c.get("MT7", frozenset()),
        "7F(3,5)door": (3, 5) in c.get("MT7", frozenset()),
        "6F(7,1)mage": (7, 1) in c.get("MT6", frozenset()),
        "6F(9,1)yellowKey": (9, 1) in c.get("MT6", frozenset()),
        "9F(6,5)redGem": (6, 5) in c.get("MT9", frozenset()),
        "9F(1,5)blueGem": (1, 5) in c.get("MT9", frozenset()),
    }


def flags_text(entry):
    f = key_flags(entry)
    return ", ".join(f"{k}={'Y' if v else 'N'}" for k, v in f.items())


def main():
    prefix_result = fixed.replay_route()
    fixed_state = prefix_result["final_state"]
    fixed_sig = sig_from_collected(fixed_collected(prefix_result))
    entries = guided.run_guided_phase1(retry_level=0)

    exact = [
        e for e in entries
        if sig_from_collected(e.get("collected", {})) == fixed_sig
    ]
    same_state = [
        e for e in entries
        if e["hp"] == fixed_state["hp"] and e["atk"] == fixed_state["atk"] and
        e["def"] == fixed_state["def"] and e["yk"] == fixed_state["yk"] and
        e["bk"] == fixed_state["bk"] and e["rk"] == fixed_state["rk"]
    ]
    same_resource_bucket = [
        e for e in entries
        if e["atk"] == fixed_state["atk"] and e["def"] == fixed_state["def"] and
        e["yk"] == fixed_state["yk"] and e["bk"] == fixed_state["bk"] and
        e["rk"] == fixed_state["rk"]
    ]
    delayed_bucket = [
        e for e in entries
        if e["atk"] == 22 and e["def"] == 21 and e["yk"] == 2 and
        e["bk"] == 1 and e["rk"] == 0 and
        (3, 1) not in e.get("collected", {}).get("MT7", frozenset())
    ]

    lines = []
    lines.append("# Fixed Prefix In Phase1 Pareto")
    lines.append("")
    lines.append(f"- fixed final state: {state_str(fixed_state)}")
    lines.append("- fixed dmg: 928")
    lines.append(f"- retained Phase1 entries: {len(entries)}")
    lines.append(f"- exact collected signature retained: {'YES' if exact else 'NO'}")
    lines.append(f"- exact full state retained: {'YES' if same_state else 'NO'}")
    lines.append(f"- same resource bucket retained: {len(same_resource_bucket)}")
    lines.append(f"- delayed `ATK22 DEF21 YK2 BK1` bucket retained: {len(delayed_bucket)}")
    lines.append("")
    lines.append("## Exact collected signature")
    lines.append("")
    if exact:
        for e in sorted(exact, key=lambda x: (x.get("_dmg", 0), -x["hp"])):
            lines.append(f"- {state_str(e)} dmg={e.get('_dmg', 0)} {flags_text(e)}")
    else:
        lines.append("- not retained")
    lines.append("")
    lines.append("## Same resource bucket `(ATK23 DEF21 YK2 BK1 RK0)`")
    lines.append("")
    for e in sorted(same_resource_bucket, key=lambda x: (x.get("_dmg", 0), -x["hp"]))[:30]:
        lines.append(f"- {state_str(e)} dmg={e.get('_dmg', 0)} {flags_text(e)}")
    lines.append("")
    lines.append("## Delayed red-gem bucket `(ATK22 DEF21 YK2 BK1 RK0)`")
    lines.append("")
    for e in sorted(delayed_bucket, key=lambda x: (x.get("_dmg", 0), -x["hp"]))[:30]:
        lines.append(f"- {state_str(e)} dmg={e.get('_dmg', 0)} {flags_text(e)}")
    lines.append("")

    text = "\n".join(lines).rstrip() + "\n"
    out_path = os.path.join("outputs", "reports", "fixed_prefix_in_phase1_pareto.md")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(text)


if __name__ == "__main__":
    main()
