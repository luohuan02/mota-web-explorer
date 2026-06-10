#!/usr/bin/env python3
"""Run only the guided Phase1 milestones and show fixed-prefix checkpoints."""

from __future__ import annotations

# Allow scripts to import project-root modules after being moved under scripts/.
import os as _codex_os
import sys as _codex_sys
_codex_root = _codex_os.path.dirname(_codex_os.path.dirname(_codex_os.path.abspath(__file__)))
if _codex_root not in _codex_sys.path:
    _codex_sys.path.insert(0, _codex_root)

import os

from src.solver import gen_walkthrough as gw


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)


def state_tuple(e):
    return e["hp"], e["atk"], e["def"], e["yk"], e["bk"], e["rk"]


def fmt(e):
    return f"HP={e['hp']} ATK={e['atk']} DEF={e['def']} YK={e['yk']} BK={e['bk']} RK={e['rk']}"


def run():
    gw._entry_store.clear()
    gw._next_id[0] = 1
    start = {
        "hp": gw.hero["h"],
        "atk": gw.hero["a"],
        "def": gw.hero["d"],
        "yk": gw.hero["yk"],
        "bk": gw.hero["bk"],
        "rk": 0,
        "collected": {},
        "_id": 1,
        "_parent_id": None,
        "_step_info": None,
        "_dmg": 0,
    }
    gw._entry_store[1] = dict(start)
    entries = [start.copy()]

    milestones = [
        ("MT4", ["upFloor"], False),
        ("MT5", ["sword1"], False),
        ("MT4", ["redGem", "yellowKey", "redPotion"], True),
        ("MT5", ["upFloor"], True),
        ("MT6", ["upFloor"], False),
        ("MT7", ["redGem", "redPotion"], False),
        ("MT7", ["upFloor"], False),
        ("MT8", ["upFloor"], False),
        ("MT9", ["shield1"], False),
        ("MT9", ["redGem", "blueGem", "yellowKey"], True),
    ]
    checkpoints = {
        "after_mt4_threshold": (652, 21, 10, 5, 1, 0),
        "after_mt5_up": (548, 21, 10, 5, 1, 0),
        "after_mt6_up": (400, 21, 10, 6, 1, 0),
        "after_mt7_up": (124, 22, 10, 3, 1, 0),
        "after_mt8_up": (124, 22, 10, 3, 1, 0),
        "after_mt9_shield": (166, 22, 20, 2, 1, 0),
        "after_mt9_gems": (148, 23, 21, 2, 1, 0),
    }

    for idx, (fid, targets, force_flyback) in enumerate(milestones, start=1):
        all_results = []
        if len(targets) > 1:
            for ent in entries:
                already = ent.get("collected", {}).get(fid, frozenset())
                if fid in gw.FLOOR_13_COLLECTED:
                    already |= gw.FLOOR_13_COLLECTED[fid]
                is_fb = force_flyback or fid in ent.get("collected", {})
                pareto, _, _ = gw.search_floor(gw.maps, fid, ent, targets, flyback=is_fb)
                if pareto:
                    for hp, yk, bk, rk, atk, def_, hs, vis, dc in pareto:
                        nc = dict(ent.get("collected", {}))
                        nc[fid] = already | vis
                        all_results.append(
                            gw._make_result(
                                hp, yk, bk, rk, atk, def_, nc, ent["_id"],
                                (fid, targets, is_fb), dmg_cost=dc
                            )
                        )
        else:
            for tgt in targets:
                for ent in entries:
                    already = ent.get("collected", {}).get(fid, frozenset())
                    if fid in gw.FLOOR_13_COLLECTED:
                        already |= gw.FLOOR_13_COLLECTED[fid]
                    if tgt != "upFloor" and not any(
                        (b[0], b[1]) not in already and b[3] == tgt
                        for b in gw.maps[fid]["bl"]
                    ):
                        continue
                    is_fb = force_flyback or fid in ent.get("collected", {})
                    pareto, _, _ = gw.search_floor(gw.maps, fid, ent, [tgt], flyback=is_fb)
                    if pareto:
                        for hp, yk, bk, rk, atk, def_, hs, vis, dc in pareto:
                            nc = dict(ent.get("collected", {}))
                            nc[fid] = already | vis
                            all_results.append(
                                gw._make_result(
                                    hp, yk, bk, rk, atk, def_, nc, ent["_id"],
                                    (fid, [tgt], is_fb), dmg_cost=dc
                                )
                            )
        entries = gw._filter_entries_tracked(all_results, retry_level=0)
        print(f"#{idx} {fid} {targets} -> {len(entries)} entries")
        for e in sorted(entries, key=lambda r: (r["atk"], r["def"], r["yk"], r["hp"]), reverse=True)[:5]:
            print(f"  {fmt(e)}")
        for name, target in checkpoints.items():
            matches = [e for e in entries if state_tuple(e) == target]
            if matches:
                print(f"  MATCH {name}: {fmt(matches[0])}")


if __name__ == "__main__":
    run()
