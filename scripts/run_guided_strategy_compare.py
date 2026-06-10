#!/usr/bin/env python3
"""Compare the guided natural Phase1 against the fixed-prefix continuation.

The full natural search can get very wide after the improved Phase1.  This
script runs that Phase1, selects a few promising entry states, then continues
each one independently with the existing Phase2/Boss logic.
"""

from __future__ import annotations

# Allow scripts to import project-root modules after being moved under scripts/.
import os as _codex_os
import sys as _codex_sys
_codex_root = _codex_os.path.dirname(_codex_os.path.dirname(_codex_os.path.abspath(__file__)))
if _codex_root not in _codex_sys.path:
    _codex_sys.path.insert(0, _codex_root)

import os
import time

from src.solver import gen_walkthrough as gw


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)


def fmt(e):
    return f"HP={e['hp']} ATK={e['atk']} DEF={e['def']} YK={e['yk']} BK={e['bk']} RK={e['rk']}"


def run_one_milestone(entries, fid, targets, force_flyback, retry_level=0):
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
    if not all_results:
        return []
    return gw._filter_entries_tracked(all_results, retry_level)


def run_guided_phase1(retry_level=0):
    gw.PHASE1_BUCKETS_ENABLED = True
    gw._entry_store.clear()
    gw._next_id[0] = 1
    start = {
        "hp": gw.hero["h"],
        "atk": gw.hero["a"],
        "def": gw.hero["d"],
        "yk": gw.hero["yk"],
        "bk": gw.hero["bk"],
        "rk": 0,
        "collected": gw.initial_collected_state(),
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
    for idx, (fid, targets, force_flyback) in enumerate(milestones, start=1):
        entries = run_one_milestone(entries, fid, targets, force_flyback, retry_level)
        if not entries:
            raise RuntimeError(f"Phase1 failed at {fid} {targets}")
        best_hp = max(entries, key=lambda e: e["hp"])
        best_profile = max(entries, key=lambda e: (e["atk"] + e["def"], e["yk"], e["hp"]))
        print(
            f"phase1 #{idx} {fid} {targets}: {len(entries)} entries, "
            f"best_hp={fmt(best_hp)}, best_profile={fmt(best_profile)}",
            flush=True,
        )
    return entries


def select_candidates(entries, limit=3):
    ranked = []
    priority_groups = [
        lambda e: e["atk"] == 22 and e["def"] == 21 and e["yk"] >= 2 and
        e["bk"] >= 1 and (3, 1) not in e.get("collected", {}).get("MT7", frozenset()),
        lambda e: e["atk"] >= 23 and e["def"] >= 21 and e["yk"] >= 2 and e["bk"] >= 1,
        lambda e: e["atk"] == 23 and e["def"] == 21 and e["yk"] >= 2,
        lambda e: e["bk"] >= 1 and e["yk"] >= 2,
    ]
    selectors = [
        lambda e: (-e.get("_dmg", 0), e["hp"], e["yk"], e["atk"] + e["def"]),
        lambda e: (e["hp"], e["yk"], e["atk"] + e["def"]),
        lambda e: (e["atk"] + e["def"], e["yk"], e["hp"]),
        lambda e: (e["yk"], e["hp"], e["atk"] + e["def"]),
        lambda e: (e["hp"] + 80 * e["yk"] + 60 * (e["atk"] + e["def"]), e["hp"]),
    ]
    seen = set()
    for group in priority_groups:
        group_entries = [e for e in entries if group(e)]
        picked_group = False
        for e in sorted(group_entries, key=lambda x: (x["hp"], x["yk"], x["atk"] + x["def"]), reverse=True)[:limit]:
            key = (e["hp"], e["atk"], e["def"], e["yk"], e["bk"], e["rk"])
            sig = tuple((fid, tuple(sorted(pos))) for fid, pos in sorted(e.get("collected", {}).items()))
            full_key = (key, sig)
            if full_key in seen:
                continue
            seen.add(full_key)
            ranked.append(e)
            picked_group = True
            break
        if picked_group and len(ranked) >= limit:
            return ranked
        if picked_group:
            continue

    for selector in selectors:
        for e in sorted(entries, key=selector, reverse=True)[:limit]:
            key = (e["hp"], e["atk"], e["def"], e["yk"], e["bk"], e["rk"])
            sig = tuple((fid, tuple(sorted(pos))) for fid, pos in sorted(e.get("collected", {}).items()))
            full_key = (key, sig)
            if full_key in seen:
                continue
            seen.add(full_key)
            ranked.append(e)
            if len(ranked) >= limit:
                return ranked
    return ranked


def main():
    t0 = time.time()
    entries = run_guided_phase1(retry_level=0)
    candidates = select_candidates(entries, limit=3)
    print("")
    print("Selected candidates:")
    for i, e in enumerate(candidates, start=1):
        print(f"  #{i}: {fmt(e)}")

    best = None
    best_i = None
    for i, ent in enumerate(candidates, start=1):
        print("")
        print(f"Continue candidate #{i}: {fmt(ent)}", flush=True)
        gw.PHASE1_BUCKETS_ENABLED = False
        result = gw.run_search(retry_level=0, initial_entry=ent, skip_phase1=True)
        if result:
            print(f"  result #{i}: {fmt(result)}", flush=True)
            if best is None or result["hp"] > best["hp"]:
                best = result
                best_i = i
        else:
            print(f"  result #{i}: failed", flush=True)

    print("")
    if best:
        print(f"BEST candidate #{best_i}: {fmt(best)}")
    else:
        print("No complete result")
    print(f"elapsed={time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
