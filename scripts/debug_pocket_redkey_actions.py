#!/usr/bin/env python3
"""Try red-key actions from the best stat27 key-pocket entry."""

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
        f"rg={rg.resource_group_score(e)} old={rg.old_score(e)} mt10={p9.mt10_stage(e)}"
    )


def has(e, fid, pos):
    return pos in e.get("collected", {}).get(fid, frozenset())


def best_pocket_stat():
    p9.select_sources = rg.select_sources
    p9.trim_entries = rg.trim_entries
    p9.best_goals = rg.best_goals
    p9.ensure_mt10 = rg.ensure_mt10
    p9.apply_action = rg.apply_action
    p9.redkey_survival_deficit = rg.redkey_survival_deficit
    candidate, _phase1 = delayed.find_candidate(300)
    entries, _rows = p9.run_stage("stat27", [candidate], rg.STAT_ACTIONS, p9.stat_goal, 12, 360, 28)
    pocket = [
        e for e in entries
        if has(e, "MT6", (9, 1)) and not has(e, "MT9", (2, 2)) and p9.stat_goal(e)
    ]
    return sorted(pocket, key=rg.score_key)[0]


def show(label, entries):
    print(label, len(entries))
    for idx, e in enumerate(sorted(entries, key=rg.score_key)[:10], 1):
        print(f"  {idx}: {state(e)} pocket={has(e, 'MT6', (9, 1)) and not has(e, 'MT9', (2, 2))}")


def main() -> None:
    ent = best_pocket_stat()
    print("start", state(ent))
    current = [ent]
    for fid, target in p9.REDKEY_ACTIONS:
        out = []
        for e in current:
            out.extend(rg.apply_action(e, fid, target))
        show(f"{fid}:{target}", out)
        if out:
            current = p9.trim_entries(current + out, 80)
            show("  after trim", current)


if __name__ == "__main__":
    main()
