#!/usr/bin/env python3
"""Stage-by-stage Pareto/beam comparison pipeline.

Stages:
1. 4F-9F shield prefix candidates
2. 27 ATK / 27 DEF candidates
3. red-key candidates
4. MT10 boss candidates

The script keeps a small representative frontier between stages so the run is
fast enough to inspect while still preserving fixed-prefix and key-heavy lines.
"""

from __future__ import annotations

# Allow scripts to import project-root modules after being moved under scripts/.
import os as _codex_os
import sys as _codex_sys
_codex_root = _codex_os.path.dirname(_codex_os.path.dirname(_codex_os.path.abspath(__file__)))
if _codex_root not in _codex_sys.path:
    _codex_sys.path.insert(0, _codex_root)

import json
import os
import time
from collections import defaultdict

import fixed_shield_strategy as fixed_prefix
from src.solver import gen_walkthrough as gw
import gen_walkthrough_fixed_prefix as fixed_walk
import run_guided_strategy_compare as guided


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

REPORT_PATH = os.path.join("outputs", "reports", "staged_pareto_report.md")
SUMMARY_PATH = os.path.join("outputs", "results", "staged_pareto_summary.json")
BEST_WALK_PATH = os.path.join("outputs", "walkthroughs", "walkthrough_staged_pareto_best.md")


def state_dict(e):
    return {
        "hp": e["hp"],
        "atk": e["atk"],
        "def": e["def"],
        "yk": e["yk"],
        "bk": e["bk"],
        "rk": e["rk"],
        "dmg": e.get("_dmg", 0),
        "yd": e.get("_yd", 0),
        "bd": e.get("_bd", 0),
        "rd": e.get("_rd", 0),
    }


def state_str(e):
    return (
        f"HP={e['hp']} ATK={e['atk']} DEF={e['def']} "
        f"YK={e['yk']} BK={e['bk']} RK={e['rk']} "
        f"doorY/B/R={e.get('_yd', 0)}/{e.get('_bd', 0)}/{e.get('_rd', 0)}"
    )


def collected_sig(e):
    return tuple(
        (fid, tuple(sorted(pos)))
        for fid, pos in sorted(e.get("collected", {}).items())
        if pos
    )


def entry_key(e):
    return (
        e["hp"],
        e["atk"],
        e["def"],
        e["yk"],
        e["bk"],
        e["rk"],
        e.get("_dmg", 0),
        e.get("_yd", 0),
        e.get("_bd", 0),
        e.get("_rd", 0),
        collected_sig(e),
    )


def root_entry(e):
    cur = e
    seen = set()
    while cur is not None:
        eid = cur.get("_id")
        if eid in seen:
            break
        seen.add(eid)
        parent = cur.get("_parent_id")
        if parent is None:
            stored = gw._entry_store.get(eid)
            if stored and stored.get("_source"):
                return stored
            return cur
        cur = gw._entry_store.get(parent)
    return e


def entry_source(e):
    return root_entry(e).get("_source", "guided")


def future_keys(e):
    return gw.phase1_future_key_score(e)


def describe_entry(e, stage):
    notes = []
    src = entry_source(e)
    if src == "fixed_prefix":
        notes.append("fixed-prefix seed")
    if stage == "shield":
        mt7 = e.get("collected", {}).get("MT7", frozenset())
        mt6 = e.get("collected", {}).get("MT6", frozenset())
        if (3, 1) in mt7:
            notes.append("7F red gem taken")
        else:
            notes.append("7F red gem delayed")
        if (9, 1) in mt6:
            notes.append("6F mage/key consumed")
        else:
            notes.append("6F mage/key reserved")
        notes.append(f"futureKeys={future_keys(e)}")
        notes.append(f"doors={e.get('_yd', 0)}/{e.get('_bd', 0)}/{e.get('_rd', 0)}")
    elif stage == "stats27":
        notes.append("reached 27/27")
        if "MT10" in e.get("collected", {}):
            notes.append("MT10 gems used")
        notes.append(f"keys Y/B={e['yk']}/{e['bk']}")
    elif stage == "redkey":
        notes.append("red key ready" if e["rk"] else "no red key")
        notes.append(f"HP before boss prep={e['hp']}")
    elif stage == "boss":
        notes.append("boss cleared")
        notes.append(f"final HP={e['hp']}")
    return "; ".join(notes)


def add_fixed_seed(entries):
    result = fixed_prefix.replay_route()
    if not result["ok"] or not result["strict_reachable"]:
        return None
    entry = fixed_walk.make_initial_entry(result)
    gw._next_id[0] += 1
    eid = gw._next_id[0]
    entry["_id"] = eid
    entry["_parent_id"] = None
    entry["_step_info"] = None
    entry["_source"] = "fixed_prefix"
    gw._entry_store[eid] = dict(entry)
    entries.append(entry)
    return result


def select_representatives(entries, limit=32):
    if not entries:
        return []
    filtered = gw._filter_entries_tracked(entries, 0)
    selected = []
    seen = set()

    def add(items):
        for e in items:
            key = entry_key(e)
            if key in seen:
                continue
            seen.add(key)
            selected.append(e)
            if len(selected) >= limit:
                return

    fixed = [e for e in filtered if entry_source(e) == "fixed_prefix"]
    add(sorted(fixed, key=lambda e: (e.get("_dmg", 0), e.get("_yd", 0), e.get("_bd", 0), e.get("_rd", 0), -e["hp"]))[:2])
    add(sorted(filtered, key=lambda e: (e.get("_dmg", 0), e.get("_yd", 0), e.get("_bd", 0), e.get("_rd", 0), -e["hp"], -e["yk"], -e["bk"])))
    add(sorted(filtered, key=lambda e: (-future_keys(e), e.get("_dmg", 0), -e["hp"])))
    add(sorted(filtered, key=lambda e: (-future_keys(e), e.get("_yd", 0), e.get("_bd", 0), e.get("_rd", 0), e.get("_dmg", 0), -e["hp"])))
    add(sorted(filtered, key=lambda e: (-e["yk"], -e["bk"], e.get("_dmg", 0), e.get("_yd", 0), e.get("_bd", 0), e.get("_rd", 0), -e["hp"])))
    add(sorted(filtered, key=lambda e: (-e["hp"], e.get("_dmg", 0), e.get("_yd", 0), e.get("_bd", 0), e.get("_rd", 0), -e["yk"], -e["bk"])))
    add(sorted(filtered, key=lambda e: (-(e["atk"] + e["def"]), e.get("_dmg", 0), e.get("_yd", 0), e.get("_bd", 0), e.get("_rd", 0), -e["hp"])))
    return selected[:limit]


def target_positions(fid, targets, entry):
    collected = entry.get("collected", {}).get(fid, frozenset())
    return frozenset(
        (b[0], b[1])
        for b in gw.maps[fid]["bl"]
        if b[3] in targets and (b[0], b[1]) not in collected
    )


def expand_entries(entries, fid, targets, flyback, require_all=False, require_redkey=False, max_iter=300000):
    out = []
    for ent in entries:
        already = ent.get("collected", {}).get(fid, frozenset())
        if fid in gw.FLOOR_13_COLLECTED:
            already |= gw.FLOOR_13_COLLECTED[fid]
        need = target_positions(fid, targets, ent)
        pareto, _, _ = gw.search_floor(
            gw.maps,
            fid,
            ent,
            targets,
            max_iter=max_iter,
            flyback=flyback,
        )
        if not pareto:
            continue
        for hp, yk, bk, rk, atk, def_, hs, vis, dc in pareto:
            if require_all and not need <= vis:
                continue
            if require_redkey and rk <= ent["rk"] and not any(
                (b[0], b[1]) in vis and b[3] == "redKey"
                for b in gw.maps[fid]["bl"]
            ):
                continue
            if not require_all and not require_redkey and targets and "upFloor" not in targets:
                if need and not (need & vis):
                    continue
            nc = dict(ent.get("collected", {}))
            nc[fid] = already | vis
            out.append(
                gw._make_result(
                    hp,
                    yk,
                    bk,
                    rk,
                    atk,
                    def_,
                    nc,
                    ent["_id"],
                    (fid, targets, flyback),
                    dmg_cost=dc,
                )
            )
    return out


def expand_boss(entries):
    out = []
    red_door_pos = frozenset(
        (b[0], b[1]) for b in gw.maps["MT10"]["bl"] if b[3] == "redDoor"
    )
    for ent in entries:
        already = ent.get("collected", {}).get("MT10", frozenset())
        is_fb = "MT10" in ent.get("collected", {})
        pareto, _, _ = gw.search_floor(gw.maps, "MT10", ent, ["redDoor"], flyback=is_fb)
        if not pareto:
            continue
        for hp, yk, bk, rk, atk, def_, hs, vis, dc in pareto:
            if not (red_door_pos & vis):
                continue
            extra = gw.boss_event_damage(atk, def_) + gw.calc_dmg("skeletonCaptain", atk, def_)
            if hp - extra <= 0:
                continue
            nc = dict(ent.get("collected", {}))
            nc["MT10"] = already | vis
            out.append(
                gw._make_result(
                    hp - extra,
                    yk,
                    bk,
                    rk,
                    atk,
                    def_,
                    nc,
                    ent["_id"],
                    ("MT10", ["redDoor"], is_fb),
                    dmg_cost=dc + extra,
                )
            )
    return out


def run_plan(entries, plan, limit=32):
    current = entries
    step_counts = []
    for label, fid, targets, flyback, require_all, require_redkey in plan:
        raw = expand_entries(
            current,
            fid,
            targets,
            flyback,
            require_all=require_all,
            require_redkey=require_redkey,
        )
        current = select_representatives(raw, limit=limit)
        step_counts.append({"step": label, "raw": len(raw), "kept": len(current)})
        if not current:
            break
    return current, step_counts


def top10(entries, stage):
    reps = select_representatives(entries, limit=80)
    chosen = []
    seen = set()

    def add(items):
        for e in items:
            key = entry_key(e)
            if key in seen:
                continue
            seen.add(key)
            chosen.append(e)
            if len(chosen) >= 10:
                return

    add(sorted(reps, key=lambda e: (e.get("_dmg", 0), e.get("_yd", 0), e.get("_bd", 0), e.get("_rd", 0), -e["hp"])))
    add(sorted(reps, key=lambda e: (-e["hp"], e.get("_dmg", 0), e.get("_yd", 0), e.get("_bd", 0), e.get("_rd", 0))))
    add(sorted(reps, key=lambda e: (-e["yk"], -e["bk"], e.get("_dmg", 0), e.get("_yd", 0), e.get("_bd", 0), e.get("_rd", 0))))
    add(sorted(reps, key=lambda e: (-future_keys(e), e.get("_dmg", 0), e.get("_yd", 0), e.get("_bd", 0), e.get("_rd", 0))))
    add(sorted(reps, key=lambda e: (-(e["atk"] + e["def"]), e.get("_dmg", 0), e.get("_yd", 0), e.get("_bd", 0), e.get("_rd", 0))))
    return [
        {
            "rank": idx,
            "state": state_dict(e),
            "source": entry_source(e),
            "futureKeys": future_keys(e),
            "description": describe_entry(e, stage),
            "_id": e.get("_id"),
        }
        for idx, e in enumerate(chosen[:10], 1)
    ]


def write_report(stage_data, best, elapsed):
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    lines = []
    lines.append("# Staged Pareto Report")
    lines.append("")
    lines.append(
        "This report uses stage-level representative Pareto/beam pruning: "
        "4-9 shield -> 27/27 -> red key -> MT10 boss."
    )
    lines.append("")
    if best:
        lines.append(f"- best complete: {state_str(best)} dmg={best.get('_dmg', 0)} source={entry_source(best)}")
    else:
        lines.append("- best complete: none")
    lines.append(f"- elapsed: {elapsed:.1f}s")
    lines.append("")

    for name, data in stage_data.items():
        lines.append(f"## {data['title']}")
        lines.append("")
        lines.append(f"- raw entries: {data['raw_count']}")
        lines.append(f"- kept representatives: {data['kept_count']}")
        if data.get("steps"):
            lines.append("- step counts: " + "; ".join(
                f"{s['step']} raw={s['raw']} kept={s['kept']}" for s in data["steps"]
            ))
        lines.append("")
        lines.append("| # | source | state | dmg | doors Y/B/R | futureKeys | description |")
        lines.append("|---:|---|---|---:|---:|---:|---|")
        for row in data["top10"]:
            st = row["state"]
            lines.append(
                f"| {row['rank']} | {row['source']} | "
                f"HP={st['hp']} ATK={st['atk']} DEF={st['def']} YK={st['yk']} BK={st['bk']} RK={st['rk']} | "
                f"{st['dmg']} | {st['yd']}/{st['bd']}/{st['rd']} | {row['futureKeys']} | {row['description']} |"
            )
        lines.append("")

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")


def write_best_walk(best, fixed_prefix_result):
    if not best:
        return
    os.makedirs(os.path.dirname(BEST_WALK_PATH), exist_ok=True)
    chain = gw.trace_chain(best)
    root = chain[0] if chain else best
    lines = []
    lines.append("# Staged Pareto Best Walk")
    lines.append("")
    lines.append(f"> final: {gw.entry_summary(best)}")
    lines.append(f"> source: {entry_source(best)}")
    lines.append("")
    if root.get("_source") == "fixed_prefix":
        fixed_walk.append_prefix_lines(lines, fixed_prefix_result)
        fixed_walk.append_search_chain_lines(lines, best)
        lines.append("## Final")
        lines.append("")
        lines.append(f"**{gw.entry_summary(best)}**")
    else:
        # Generic replay for a guided-search chain.
        from gen_guided_candidate_walk import append_chain_walk

        append_chain_walk(lines, chain, "Guided full chain")
        lines.append("## Final")
        lines.append("")
        lines.append(f"**{gw.entry_summary(best)}**")
    with open(BEST_WALK_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")


def main():
    t0 = time.time()
    print("Run 4-9 guided phase1...")
    phase1_entries = guided.run_guided_phase1(retry_level=0)
    fixed_prefix_result = add_fixed_seed(phase1_entries)

    shield_entries = select_representatives(phase1_entries, limit=32)
    print(f"shield stage kept={len(shield_entries)}")

    stat_plan = [
        ("MT6 blueGem", "MT6", ["blueGem"], True, True, False),
        ("MT3 red+blue", "MT3", ["redGem", "blueGem"], True, True, False),
        ("MT8 red+blue", "MT8", ["redGem", "blueGem"], True, True, False),
        ("MT1 red+blue", "MT1", ["redGem", "blueGem"], True, True, False),
        ("MT5 refill", "MT5", ["yellowKey", "blueKey", "redPotion", "bluePotion"], True, False, False),
        ("MT4 refill", "MT4", ["yellowKey", "blueKey", "redPotion", "bluePotion"], True, False, False),
        ("MT7 refill", "MT7", ["yellowKey", "blueKey", "redPotion", "bluePotion"], True, False, False),
        ("MT9 up", "MT9", ["upFloor"], True, False, False),
        ("MT10 red+blue", "MT10", ["redGem", "blueGem"], False, True, False),
    ]
    stat_entries, stat_steps = run_plan(shield_entries, stat_plan, limit=32)
    stat_entries = select_representatives(
        [e for e in stat_entries if e["atk"] >= 27 and e["def"] >= 27],
        limit=32,
    )
    print(f"stats27 stage kept={len(stat_entries)}")

    redkey_plan = [
        ("MT8 redKey", "MT8", ["yellowKey", "bluePotion", "redKey"], True, False, True),
    ]
    redkey_entries, redkey_steps = run_plan(stat_entries, redkey_plan, limit=32)
    redkey_entries = select_representatives([e for e in redkey_entries if e["rk"] >= 1], limit=32)
    print(f"redkey stage kept={len(redkey_entries)}")

    boss_prep_plan = [
        ("MT7 boss prep", "MT7", ["redGem", "yellowKey", "bluePotion", "redPotion"], True, False, False),
        ("MT3 boss prep", "MT3", ["redGem", "blueGem", "yellowKey", "blueKey", "bluePotion", "redPotion"], True, False, False),
        ("MT1 boss prep", "MT1", ["redGem", "blueGem", "yellowKey", "bluePotion", "redPotion"], True, False, False),
    ]
    boss_inputs, boss_prep_steps = run_plan(redkey_entries, boss_prep_plan, limit=32)
    boss_entries = select_representatives(expand_boss(boss_inputs), limit=32)
    print(f"boss stage kept={len(boss_entries)}")

    best = None
    if boss_entries:
        best = sorted(boss_entries, key=lambda e: (e.get("_dmg", 0), -e["hp"]))[0]

    stage_data = {
        "shield": {
            "title": "4-9 shield stage",
            "raw_count": len(phase1_entries),
            "kept_count": len(shield_entries),
            "top10": top10(shield_entries, "shield"),
        },
        "stats27": {
            "title": "27 ATK / 27 DEF stage",
            "raw_count": len(stat_entries),
            "kept_count": len(stat_entries),
            "steps": stat_steps,
            "top10": top10(stat_entries, "stats27"),
        },
        "redkey": {
            "title": "red-key stage",
            "raw_count": len(redkey_entries),
            "kept_count": len(redkey_entries),
            "steps": redkey_steps,
            "top10": top10(redkey_entries, "redkey"),
        },
        "boss": {
            "title": "MT10 boss stage",
            "raw_count": len(boss_entries),
            "kept_count": len(boss_entries),
            "steps": boss_prep_steps + [{"step": "MT10 boss", "raw": len(boss_entries), "kept": len(boss_entries)}],
            "top10": top10(boss_entries, "boss"),
        },
    }

    summary = {
        "best": state_dict(best) if best else None,
        "best_source": entry_source(best) if best else None,
        "elapsed": time.time() - t0,
        "stages": {
            name: {
                "raw_count": data["raw_count"],
                "kept_count": data["kept_count"],
                "steps": data.get("steps", []),
                "top10": data["top10"],
            }
            for name, data in stage_data.items()
        },
    }
    os.makedirs(os.path.dirname(SUMMARY_PATH), exist_ok=True)
    with open(SUMMARY_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    elapsed = time.time() - t0
    write_report(stage_data, best, elapsed)
    write_best_walk(best, fixed_prefix_result)
    print(f"Wrote {REPORT_PATH}")
    print(f"Wrote {SUMMARY_PATH}")
    print(f"elapsed={elapsed:.1f}s")
    if best:
        print(f"Wrote {BEST_WALK_PATH}")
        print(f"best: {state_str(best)} dmg={best.get('_dmg', 0)} source={entry_source(best)}")
    else:
        print("No complete boss result")


if __name__ == "__main__":
    main()
