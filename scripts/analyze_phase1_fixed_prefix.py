#!/usr/bin/env python3
"""Small diagnostics for why the fixed shield prefix is hard to find naturally."""

from __future__ import annotations

# Allow scripts to import project-root modules after being moved under scripts/.
import os as _codex_os
import sys as _codex_sys
_codex_root = _codex_os.path.dirname(_codex_os.path.dirname(_codex_os.path.abspath(__file__)))
if _codex_root not in _codex_sys.path:
    _codex_sys.path.insert(0, _codex_root)

import os

import fixed_shield_strategy as fixed
from src.solver.full_search import ENTRANCES, FLYBACK_ENTRANCES, FLOOR_13_COLLECTED, calc_dmg, load_data, search_with_path


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)


def state_str(state):
    return (
        f"HP={state['hp']} ATK={state['atk']} DEF={state['def']} "
        f"YK={state['yk']} BK={state['bk']} RK={state['rk']}"
    )


def checkpoints(result):
    collected = {fid: set(pos) for fid, pos in FLOOR_13_COLLECTED.items()}
    out = {}
    for segment in result["segments"]:
        for step in result["steps"]:
            if step["segment"] != segment["name"]:
                continue
            if step["type"] in ("monster", "door", "item"):
                collected.setdefault(step["floor"], set()).add((step["x"], step["y"]))
        out[segment["name"]] = {
            "state": dict(segment["actual"]),
            "collected": {fid: frozenset(pos) for fid, pos in collected.items()},
        }
    return out


def try_mt4_redgem(label, sx, sy, cp):
    _, maps = load_data()
    state = cp["state"]
    removed = cp["collected"].get("MT4", frozenset()) | FLOOR_13_COLLECTED.get("MT4", frozenset())
    target_state = {"hp": 652, "atk": 21, "def": 10, "yk": 5, "bk": 1, "rk": 0}
    steps, final, vis = search_with_path(
        maps["MT4"],
        sx,
        sy,
        state["hp"],
        state["atk"],
        state["def"],
        state["yk"],
        state["bk"],
        state["rk"],
        ["redGem", "yellowKey", "upFloor"],
        removed_pos=removed,
        target_state=target_state,
    )
    print(f"{label}: start=({sx},{sy})")
    if not steps:
        print("  no path")
        return
    print(
        "  final: "
        f"HP={final['hp']} ATK={final['atk']} DEF={final['def']} "
        f"YK={final['yk']} BK={final['bk']} RK={final['rk']}"
    )
    for s in steps:
        print(f"  ({s['x']},{s['y']}) {s['action']} {s['eid']} -> HP={s['hp_after']} ATK={s['atk']} DEF={s['def']} YK={s['yk']}")


def try_mt5_up(label, cp, target_state):
    _, maps = load_data()
    state = cp["state"]
    removed = cp["collected"].get("MT5", frozenset())
    steps, final, vis = search_with_path(
        maps["MT5"],
        *ENTRANCES["MT5"],
        state["hp"],
        state["atk"],
        state["def"],
        state["yk"],
        state["bk"],
        state["rk"],
        ["upFloor"],
        removed_pos=removed,
        target_state=target_state,
    )
    print(f"{label}:")
    if not steps:
        print("  no path")
        return
    print(
        "  final: "
        f"HP={final['hp']} ATK={final['atk']} DEF={final['def']} "
        f"YK={final['yk']} BK={final['bk']} RK={final['rk']}"
    )
    for s in steps:
        print(f"  ({s['x']},{s['y']}) {s['action']} {s['eid']} -> HP={s['hp_after']} ATK={s['atk']} DEF={s['def']} YK={s['yk']}")


def print_breakpoints():
    for atk in range(20, 23):
        dmg = calc_dmg("bat", atk, 10)
        print(f"bat damage at ATK={atk}, DEF=10: {dmg}")


def main():
    result = fixed.replay_route()
    cps = checkpoints(result)
    after_sword = cps["5F 拿铁剑并回 4F"]
    after_mt4_gems = cps["回 4F 拿红宝石和 3 黄钥匙"]
    print("After fixed sword/return checkpoint:")
    print(f"  {state_str(after_sword['state'])}")
    print("")
    print_breakpoints()
    print("")
    try_mt4_redgem("current MT4 flyback entrance", *FLYBACK_ENTRANCES["MT4"], after_sword)
    print("")
    try_mt4_redgem("manual route MT4 return entrance", 1, 11, after_sword)
    print("")
    try_mt5_up(
        "current order: MT5 up immediately after sword/return, before MT4 redGem",
        after_sword,
        {"hp": 548, "atk": 21, "def": 10, "yk": 5, "bk": 1, "rk": 0},
    )
    print("")
    try_mt5_up(
        "fixed order: MT5 up after MT4 redGem/key detour",
        after_mt4_gems,
        {"hp": 548, "atk": 21, "def": 10, "yk": 5, "bk": 1, "rk": 0},
    )


if __name__ == "__main__":
    main()
