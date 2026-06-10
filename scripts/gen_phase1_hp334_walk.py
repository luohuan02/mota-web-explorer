#!/usr/bin/env python3
"""Generate a 4F-9F walk for the HP334/ATK22/DEF21/YK2/BK1/dmg742 candidate."""

from __future__ import annotations

# Allow scripts to import project-root modules after being moved under scripts/.
import os as _codex_os
import sys as _codex_sys
_codex_root = _codex_os.path.dirname(_codex_os.path.dirname(_codex_os.path.abspath(__file__)))
if _codex_root not in _codex_sys.path:
    _codex_sys.path.insert(0, _codex_root)

import os

from src.solver import gen_walkthrough as gw
import run_guided_strategy_compare as guided
from gen_current_4_9_walk import write_phase1_walk


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)


TARGET = {
    "hp": 334,
    "atk": 22,
    "def": 21,
    "yk": 2,
    "bk": 1,
    "rk": 0,
    "_dmg": 742,
}


def matches(entry):
    return all(entry.get(key) == value for key, value in TARGET.items())


def main():
    entries = guided.run_guided_phase1(retry_level=0)
    candidates = [entry for entry in entries if matches(entry)]
    if not candidates:
        raise SystemExit("target candidate not found")

    candidate = sorted(candidates, key=lambda e: (e.get("_dmg", 0), -e["hp"]))[0]
    path = write_phase1_walk(
        candidate,
        os.path.join("outputs", "walkthroughs", "walkthrough_phase1_hp334_dmg742.md"),
    )
    print(f"Wrote {path}: {gw.entry_summary(candidate)}")
    chain = gw.trace_chain(candidate)
    for i, entry in enumerate(chain):
        step = entry.get("_step_info")
        if not step:
            print(f"#{i}: start {gw.entry_summary(entry)}")
            continue
        fid, targets, flyback = step
        print(f"#{i}: {fid} {targets} flyback={flyback} {gw.entry_summary(entry, chain[i - 1])}")


if __name__ == "__main__":
    main()
