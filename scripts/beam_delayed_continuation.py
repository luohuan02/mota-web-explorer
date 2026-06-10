#!/usr/bin/env python3
"""Beam-search continuation from the key-preserving delayed 4-9 candidate."""

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
from try_forced_fixed_continuation_from_delayed import make_entry, state_str


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)


def target_positions(fid, targets, entry=None):
    collected = frozenset()
    if entry is not None:
        collected = entry.get("collected", {}).get(fid, frozenset())
    return frozenset(
        (b[0], b[1])
        for b in gw.maps[fid]["bl"]
        if b[3] in targets and (b[0], b[1]) not in collected
    )


def select_beam(entries, limit=28):
    if not entries:
        return []
    entries = gw._filter_entries_tracked(entries, 0)
    selected = []
    seen = set()

    def add_some(items):
        for e in items:
            key = e.get("_id", id(e))
            if key in seen:
                continue
            seen.add(key)
            selected.append(e)
            if len(selected) >= limit:
                return

    add_some(sorted(entries, key=lambda e: (e.get("_dmg", 0), -e["yk"], -e["bk"], -e["hp"])))
    add_some(sorted(entries, key=lambda e: (-e["yk"], -e["bk"], e.get("_dmg", 0), -e["hp"])))
    add_some(sorted(entries, key=lambda e: (-e["hp"], e.get("_dmg", 0), -e["yk"], -e["bk"])))
    add_some(sorted(entries, key=lambda e: (-(e["atk"] + e["def"]), e.get("_dmg", 0), -e["yk"], -e["hp"])))
    return selected[:limit]


def expand(entries, fid, targets, flyback, label, require_all=False, max_iter=500000):
    out = []
    for ent in entries:
        al = ent.get("collected", {}).get(fid, frozenset())
        need = target_positions(fid, targets, ent)
        pareto, _, _ = gw.search_floor(gw.maps, fid, ent, targets, max_iter=max_iter, flyback=flyback)
        if not pareto:
            continue
        for hp, yk, bk, rk, atk, def_, hs, vis, dc in pareto:
            if require_all and not need <= vis:
                continue
            if not require_all and targets and "upFloor" not in targets and not (need & vis):
                continue
            nc = dict(ent.get("collected", {}))
            nc[fid] = al | vis
            out.append(gw._make_result(hp, yk, bk, rk, atk, def_, nc, ent["_id"], (fid, targets, flyback), dmg_cost=dc))
    beam = select_beam(out)
    print_step(label, beam)
    return beam


def expand_boss(entries):
    out = []
    red_door_pos = target_positions("MT10", ["redDoor"])
    for ent in entries:
        al = ent.get("collected", {}).get("MT10", frozenset())
        pareto, _, _ = gw.search_floor(gw.maps, "MT10", ent, ["redDoor"], flyback=True)
        if not pareto:
            continue
        for hp, yk, bk, rk, atk, def_, hs, vis, dc in pareto:
            if not (red_door_pos & vis):
                continue
            extra = gw.boss_event_damage(atk, def_) + gw.calc_dmg("skeletonCaptain", atk, def_)
            if hp - extra <= 0:
                continue
            nc = dict(ent.get("collected", {}))
            nc["MT10"] = al | vis
            out.append(gw._make_result(hp - extra, yk, bk, rk, atk, def_, nc, ent["_id"], ("MT10", ["redDoor"], True), dmg_cost=dc + extra))
    beam = select_beam(out)
    print_step("MT10 boss", beam)
    return beam


def print_step(label, entries):
    if not entries:
        print(f"{label}: no entries", flush=True)
        return
    best = sorted(entries, key=lambda e: (e.get("_dmg", 0), -e["hp"], -e["yk"]))[0]
    key_best = sorted(entries, key=lambda e: (-e["yk"], -e["bk"], e.get("_dmg", 0), -e["hp"]))[0]
    print(
        f"{label}: {len(entries)} entries; best {state_str(best)} dmg={best.get('_dmg',0)}; "
        f"key {state_str(key_best)} dmg={key_best.get('_dmg',0)}",
        flush=True,
    )


def select_start(entries):
    matches = [
        e for e in entries
        if e["atk"] == 23 and e["def"] == 21 and e["yk"] == 2 and
        e["bk"] == 1 and e["rk"] == 0
    ]
    if not matches:
        matches = [
            e for e in entries
            if e["atk"] == 22 and e["def"] == 21 and e["yk"] == 2 and
            e["bk"] == 1 and e["rk"] == 0
        ]
    return sorted(matches, key=lambda e: (-future_key_left(e), e.get("_dmg", 0), -e["hp"]))[0]


def main():
    gw._entry_store.clear()
    gw._next_id[0] = 0
    phase1 = guided.run_guided_phase1(retry_level=0)
    start = make_entry(select_start(phase1))
    start["_id"] = 1
    start["_parent_id"] = None
    start["_step_info"] = None
    gw._next_id[0] = 1
    gw._entry_store[1] = dict(start)
    entries = [start]
    print_step("phase1 delayed", entries)

    plan = []
    if start["atk"] < 23:
        plan.append(("MT7 redGem", "MT7", ["redGem"], True, True))
    plan += [
        ("MT6 blueGem", "MT6", ["blueGem"], True, True),
        ("MT3 gems", "MT3", ["redGem", "blueGem"], True, True),
        ("MT8 gems", "MT8", ["redGem", "blueGem"], True, True),
        ("MT1 gems", "MT1", ["redGem", "blueGem"], True, True),
        ("MT5 refill", "MT5", ["yellowKey", "blueKey", "redPotion", "bluePotion"], True, False),
        ("MT4 refill", "MT4", ["yellowKey", "blueKey", "redPotion", "bluePotion"], True, False),
        ("MT9 refill", "MT9", ["yellowKey", "redPotion"], True, False),
        ("MT8 pre refill", "MT8", ["yellowKey", "bluePotion", "redPotion"], True, False),
        ("MT9 up", "MT9", ["upFloor"], True, False),
        ("MT10 gems", "MT10", ["redGem", "blueGem"], False, True),
        ("late MT7 refill", "MT7", ["yellowKey", "blueKey", "bluePotion", "redPotion"], True, False),
        ("late MT9 refill", "MT9", ["yellowKey", "redPotion"], True, False),
        ("late MT3 refill", "MT3", ["yellowKey", "blueKey", "redPotion", "bluePotion"], True, False),
        ("late MT1 refill", "MT1", ["yellowKey", "bluePotion", "redPotion"], True, False),
        ("MT8 redKey", "MT8", ["yellowKey", "bluePotion", "redKey"], True, False),
        ("late MT7 potion", "MT7", ["yellowKey", "bluePotion", "redPotion"], True, False),
        ("late MT3 potion", "MT3", ["yellowKey", "blueKey", "bluePotion", "redPotion"], True, False),
        ("late MT1 potion", "MT1", ["yellowKey", "bluePotion", "redPotion"], True, False),
    ]
    for label, fid, targets, flyback, require_all in plan:
        next_entries = expand(entries, fid, targets, flyback, label, require_all=require_all, max_iter=180000)
        if label.startswith("late "):
            if not next_entries:
                print(f"{label}: skipped", flush=True)
                continue
            entries = select_beam(entries + next_entries)
            continue
        entries = next_entries
        if not entries:
            break
    if entries:
        entries = expand_boss(entries)

    lines = ["# Beam Delayed Continuation", ""]
    if entries:
        best = max(entries, key=lambda e: e["hp"])
        lines.append(f"- final: {state_str(best)} dmg={best.get('_dmg', 0)}")
        lines.append(f"- chain length: {len(gw.trace_chain(best))}")
    else:
        lines.append("- final: failed")
    text = "\n".join(lines) + "\n"
    out_path = os.path.join("outputs", "reports", "beam_delayed_continuation.md")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(text)


if __name__ == "__main__":
    main()
