#!/usr/bin/env python3
"""Try forced continuation on all unique delayed exact Phase1 variants."""

from __future__ import annotations

# Allow scripts to import project-root modules after being moved under scripts/.
import os as _codex_os
import sys as _codex_sys
_codex_root = _codex_os.path.dirname(_codex_os.path.dirname(_codex_os.path.abspath(__file__)))
if _codex_root not in _codex_sys.path:
    _codex_sys.path.insert(0, _codex_root)

import json
import os

from src.solver import gen_walkthrough as gw
import run_guided_strategy_compare as guided


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)


def state_str(e):
    return gw.state_str(e["hp"], e["atk"], e["def"], e["yk"], e["bk"], e["rk"])


def has_pos(entry, fid, pos):
    return pos in entry.get("collected", {}).get(fid, frozenset())


def signature(entry):
    return tuple(
        (fid, tuple(sorted(pos)))
        for fid, pos in sorted(entry.get("collected", {}).items())
        if pos
    )


def clone(entry):
    return {
        "hp": entry["hp"],
        "atk": entry["atk"],
        "def": entry["def"],
        "yk": entry["yk"],
        "bk": entry["bk"],
        "rk": entry["rk"],
        "collected": {
            fid: frozenset(pos)
            for fid, pos in entry.get("collected", {}).items()
        },
        "_dmg": entry.get("_dmg", 0),
    }


def target_positions(fid, targets):
    return frozenset(
        (b[0], b[1]) for b in gw.maps[fid]["bl"] if b[3] in targets
    )


def update(entry, fid, hp, yk, bk, rk, atk, def_, vis, dc, extra_dmg=0):
    nc = dict(entry.get("collected", {}))
    nc[fid] = entry.get("collected", {}).get(fid, frozenset()) | vis
    return {
        "hp": hp - extra_dmg,
        "atk": atk,
        "def": def_,
        "yk": yk,
        "bk": bk,
        "rk": rk,
        "collected": nc,
        "_dmg": entry.get("_dmg", 0) + dc + extra_dmg,
    }


def consume(entry, fid, targets, flyback):
    pareto, _, _ = gw.search_floor(gw.maps, fid, entry, targets, flyback=flyback)
    if not pareto:
        return None, "no pareto"
    need_pos = target_positions(fid, targets)
    red_door_pos = target_positions("MT10", ["redDoor"])
    options = []
    for hp, yk, bk, rk, atk, def_, hs, vis, dc in pareto:
        if "redKey" in targets and rk <= entry["rk"]:
            continue
        if fid == "MT10" and "redDoor" in targets:
            if not (red_door_pos & vis):
                continue
            extra = gw.boss_event_damage(atk, def_) + gw.calc_dmg("skeletonCaptain", atk, def_)
            if hp - extra <= 0:
                continue
            options.append(update(entry, fid, hp, yk, bk, rk, atk, def_, vis, dc, extra))
            continue
        if targets and not (need_pos & vis) and "upFloor" not in targets:
            continue
        options.append(update(entry, fid, hp, yk, bk, rk, atk, def_, vis, dc))
    if not options:
        return None, "filtered empty"
    if any(t in {"yellowKey", "blueKey", "redPotion", "bluePotion"} for t in targets):
        return sorted(options, key=lambda e: (-e["yk"], -e["bk"], -e["rk"], e.get("_dmg", 0), -e["hp"]))[0], None
    return sorted(options, key=lambda e: (e.get("_dmg", 0), -e["hp"], -e["atk"], -e["def"], -e["yk"]))[0], None


def run_variant(start, segments):
    chain = [("phase1 delayed", start)]
    entry, err = consume(start, "MT7", ["redGem"], True)
    if entry is None:
        return chain + [(f"FAILED take MT7 redGem: {err}", start)]
    chain.append(("take delayed MT7 redGem", entry))
    for seg in segments:
        entry, err = consume(entry, seg["floor"], seg["targets"], seg["flyback"])
        label = f"{seg['floor']} {seg['targets']} flyback={seg['flyback']}"
        if entry is None:
            chain.append((f"FAILED {label}: {err}", chain[-1][1]))
            return chain
        chain.append((label, entry))
    return chain


def main():
    entries = guided.run_guided_phase1(retry_level=0)
    raw = [
        e for e in entries
        if e["atk"] == 22 and e["def"] == 21 and e["yk"] == 2 and e["bk"] == 1 and
        e["rk"] == 0 and not has_pos(e, "MT7", (3, 1))
    ]
    unique = {}
    for e in raw:
        sig = signature(e)
        if sig not in unique or (e.get("_dmg", 0), -e["hp"]) < (unique[sig].get("_dmg", 0), -unique[sig]["hp"]):
            unique[sig] = e
    starts = sorted(unique.values(), key=lambda e: (e.get("_dmg", 0), -e["hp"]))

    summary_path = os.path.join("outputs", "results", "walkthrough_fixed_prefix_summary.json")
    with open(summary_path, "r", encoding="utf-8") as f:
        segments = json.load(f)["search_segments"]

    lines = []
    lines.append("# Forced Delayed Variant Continuation")
    lines.append("")
    lines.append(f"- raw delayed candidates: {len(raw)}")
    lines.append(f"- unique collected signatures: {len(starts)}")
    lines.append("")
    lines.append("| variant | start | start dmg | final/failed step | state | dmg |")
    lines.append("|---:|---|---:|---|---|---:|")
    details = []
    for idx, start0 in enumerate(starts, start=1):
        start = clone(start0)
        chain = run_variant(start, segments)
        label, state = chain[-1]
        lines.append(
            f"| {idx} | {state_str(start)} | {start.get('_dmg', 0)} | "
            f"{label} | {state_str(state)} | {state.get('_dmg', 0)} |"
        )
        details.append((idx, chain))
    lines.append("")
    for idx, chain in details:
        lines.append(f"## Variant {idx}")
        lines.append("")
        lines.append("| step | state | dmg |")
        lines.append("|---|---|---:|")
        for label, state in chain:
            lines.append(f"| {label} | {state_str(state)} | {state.get('_dmg', 0)} |")
        lines.append("")
    text = "\n".join(lines).rstrip() + "\n"
    out_path = os.path.join("outputs", "reports", "forced_delayed_variants.md")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(text)


if __name__ == "__main__":
    main()
