#!/usr/bin/env python3
"""Inspect Phase1 entries in the fixed resource bucket after 9F gems."""

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


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)


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


def key(e):
    return (
        e.get("_dmg", 0),
        e.get("_yd", 0),
        e.get("_bd", 0),
        e.get("_rd", 0),
        -e["hp"],
        str(sorted((fid, sorted(pos)) for fid, pos in e.get("collected", {}).items())),
    )


def main():
    gw.USE_DOOR_COST_PARETO = True
    entries = guided.run_guided_phase1(retry_level=0)
    bucket = [
        e for e in entries
        if e["atk"] == 23 and e["def"] == 21 and e["yk"] == 2 and
        e["bk"] == 1 and e["rk"] == 0
    ]
    print(f"bucket count={len(bucket)}")
    seen = set()
    rows = []
    for e in sorted(bucket, key=key):
        row_key = (
            e["hp"], e.get("_dmg", 0), e.get("_yd", 0), e.get("_bd", 0),
            e.get("_rd", 0), flags(e)
        )
        if row_key in seen:
            continue
        seen.add(row_key)
        rows.append(e)
    for i, e in enumerate(rows[:20], 1):
        print(
            f"{i:02d} HP={e['hp']} ATK={e['atk']} DEF={e['def']} "
            f"YK={e['yk']} BK={e['bk']} RK={e['rk']} "
            f"dmg={e.get('_dmg', 0)} door={e.get('_yd', 0)}/{e.get('_bd', 0)}/{e.get('_rd', 0)} "
            f"{flags(e)}"
        )


if __name__ == "__main__":
    main()
