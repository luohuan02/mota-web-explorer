#!/usr/bin/env python3
"""Check whether the MT6-key/no-MT9-key branch survives the stat27 stage."""

from __future__ import annotations

import os
import sys


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.chdir(ROOT)

from scripts import continue_delayed_phase1_with_post9_resource as delayed
from scripts import post9_action_search as p9
from scripts import post9_resource_group_search as rg


def state(e):
    return (
        f"HP={e['hp']} ATK={e['atk']} DEF={e['def']} YK={e['yk']} BK={e['bk']} RK={e['rk']} "
        f"dmg={e.get('_dmg', 0)} door={e.get('_yd', 0)}/{e.get('_bd', 0)}/{e.get('_rd', 0)} "
        f"rg={rg.resource_group_score(e)} old={rg.old_score(e)}"
    )


def has(e, fid, pos):
    return pos in e.get("collected", {}).get(fid, frozenset())


def main() -> None:
    p9.select_sources = rg.select_sources
    p9.trim_entries = rg.trim_entries
    p9.best_goals = rg.best_goals
    p9.ensure_mt10 = rg.ensure_mt10
    p9.apply_action = rg.apply_action
    p9.redkey_survival_deficit = rg.redkey_survival_deficit

    candidate, _phase1 = delayed.find_candidate(300)
    entries, rows = p9.run_stage(
        "stat27",
        [candidate],
        rg.STAT_ACTIONS,
        p9.stat_goal,
        12,
        360,
        28,
    )
    pocket = [e for e in entries if has(e, "MT6", (9, 1)) and not has(e, "MT9", (2, 2))]
    stat_pocket = [e for e in pocket if p9.stat_goal(e)]
    print(f"entries={len(entries)} pocket={len(pocket)} stat_pocket={len(stat_pocket)}")
    for idx, e in enumerate(sorted(stat_pocket, key=rg.score_key)[:20], 1):
        print(f"{idx}: {state(e)} mt10={p9.mt10_stage(e)}")

    redkey_entries, _rows = p9.run_stage(
        "redkey",
        entries,
        p9.REDKEY_ACTIONS,
        p9.redkey_goal,
        6,
        360,
        28,
    )
    redkey_pocket = [
        e for e in redkey_entries
        if has(e, "MT6", (9, 1)) and not has(e, "MT9", (2, 2)) and p9.redkey_goal(e)
    ]
    print(f"redkey_entries={len(redkey_entries)} redkey_pocket={len(redkey_pocket)}")
    for idx, e in enumerate(sorted(redkey_pocket, key=rg.score_key)[:20], 1):
        print(f"R{idx}: {state(e)} mt10={p9.mt10_stage(e)}")

    final_entries, _rows = p9.run_stage(
        "boss",
        redkey_entries,
        p9.BOSS_PREP_ACTIONS,
        p9.goal,
        6,
        360,
        28,
        include_boss=True,
    )
    final_pocket = [
        e for e in final_entries
        if has(e, "MT6", (9, 1)) and not has(e, "MT9", (2, 2)) and p9.goal(e)
    ]
    print(f"final_entries={len(final_entries)} final_pocket={len(final_pocket)}")
    for idx, e in enumerate(sorted(final_pocket, key=rg.score_key)[:20], 1):
        print(f"F{idx}: {state(e)} mt10={p9.mt10_stage(e)}")


if __name__ == "__main__":
    main()
