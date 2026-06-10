#!/usr/bin/env python3
"""Try a key-preserving delayed prefix with an explicit MT9 key refill."""

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
from continue_delayed_redgem_candidate import future_key_left, select_delayed
from try_forced_fixed_continuation_from_delayed import consume, make_entry, state_str


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)


def main():
    entries = guided.run_guided_phase1(retry_level=0)
    entry = make_entry(select_delayed(entries))
    chain = [("phase1 delayed", entry)]

    steps = [
        ("MT7 redGem", "MT7", ["redGem"], True),
        ("MT6 blueGem", "MT6", ["blueGem"], True),
        ("MT3 red+blue", "MT3", ["redGem", "blueGem"], True),
        ("MT8 red+blue", "MT8", ["redGem", "blueGem"], True),
        ("MT1 red+blue", "MT1", ["redGem", "blueGem"], True),
        ("MT5 key refill", "MT5", ["yellowKey", "blueKey", "redPotion", "bluePotion"], True),
        ("MT4 key refill", "MT4", ["yellowKey", "blueKey", "redPotion", "bluePotion"], True),
        ("MT7 key refill", "MT7", ["yellowKey", "blueKey", "redPotion", "bluePotion"], True),
        ("MT9 key refill", "MT9", ["yellowKey", "redPotion"], True),
        ("MT9 up", "MT9", ["upFloor"], True),
        ("MT10 gems", "MT10", ["redGem", "blueGem"], False),
        ("MT3 late refill", "MT3", ["yellowKey", "blueKey", "redPotion", "bluePotion"], True),
        ("MT1 late refill", "MT1", ["yellowKey", "bluePotion", "redPotion"], True),
        ("MT8 redKey", "MT8", ["yellowKey", "bluePotion", "redKey"], True),
        ("MT7 late potion", "MT7", ["redGem", "yellowKey", "bluePotion", "redPotion"], True),
        ("MT3 late potion", "MT3", ["redGem", "blueGem", "yellowKey", "blueKey", "bluePotion", "redPotion"], True),
        ("MT1 late potion", "MT1", ["redGem", "blueGem", "yellowKey", "bluePotion", "redPotion"], True),
        ("MT10 boss", "MT10", ["redDoor"], True),
    ]

    failed = None
    for label, fid, targets, flyback in steps:
        nxt, err = consume(entry, fid, targets, flyback)
        if nxt is None:
            failed = f"FAILED {label}: {err}"
            chain.append((failed, entry))
            break
        entry = nxt
        chain.append((label, entry))

    lines = ["# Custom Delayed Continuation", "", "| step | state | dmg | futureKeys |", "|---|---|---:|---:|"]
    for label, item in chain:
        lines.append(f"| {label} | {state_str(item)} | {item.get('_dmg', 0)} | {future_key_left(item)} |")
    if failed is None:
        lines.append("")
        lines.append(f"- final: {state_str(entry)} dmg={entry.get('_dmg', 0)}")
    text = "\n".join(lines).rstrip() + "\n"
    out_path = os.path.join("outputs", "reports", "custom_delayed_continuation.md")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(text)


if __name__ == "__main__":
    main()
