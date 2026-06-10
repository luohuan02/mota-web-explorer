#!/usr/bin/env python3
"""Try the fixed-prefix successful continuation order from delayed Phase1."""

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
from continue_delayed_redgem_candidate import future_key_left


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)


def state_str(e):
    return gw.state_str(e["hp"], e["atk"], e["def"], e["yk"], e["bk"], e["rk"])


def has_pos(entry, fid, pos):
    return pos in entry.get("collected", {}).get(fid, frozenset())


def select_delayed(entries):
    matches = [
        e for e in entries
        if e["atk"] == 22 and e["def"] == 21 and e["yk"] == 2 and e["bk"] == 1 and
        e["rk"] == 0 and not has_pos(e, "MT7", (3, 1))
    ]
    return sorted(matches, key=lambda e: (-future_key_left(e), e.get("_dmg", 0), -e["hp"]))[0]


def make_entry(entry):
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


def update_entry(entry, fid, hp, yk, bk, rk, atk, def_, vis, dc, extra_dmg=0):
    al = entry.get("collected", {}).get(fid, frozenset())
    nc = dict(entry.get("collected", {}))
    nc[fid] = al | vis
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


def target_positions(fid, targets):
    return frozenset(
        (b[0], b[1]) for b in gw.maps[fid]["bl"] if b[3] in targets
    )


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
            options.append(update_entry(entry, fid, hp, yk, bk, rk, atk, def_, vis, dc, extra_dmg=extra))
            continue
        if targets and "upFloor" not in targets:
            if all(t in {"redGem", "blueGem"} for t in targets):
                missing = need_pos - entry.get("collected", {}).get(fid, frozenset())
                if not missing <= vis:
                    continue
            elif not (need_pos & vis):
                continue
        options.append(update_entry(entry, fid, hp, yk, bk, rk, atk, def_, vis, dc))

    if not options:
        return None, "filtered empty"
    if any(t in {"yellowKey", "blueKey", "redPotion", "bluePotion"} for t in targets):
        return sorted(
            options,
            key=lambda e: (-e["yk"], -e["bk"], -e["rk"], e.get("_dmg", 0), -e["hp"]),
        )[0], None
    return sorted(options, key=lambda e: (e.get("_dmg", 0), -e["hp"], -e["atk"], -e["def"], -e["yk"]))[0], None


def main():
    entries = guided.run_guided_phase1(retry_level=0)
    delayed = make_entry(select_delayed(entries))
    chain = []
    chain.append(("phase1 delayed", delayed))

    after_redgem, err = consume(delayed, "MT7", ["redGem"], True)
    if after_redgem is None:
        raise SystemExit(f"failed MT7 redGem: {err}")
    chain.append(("take delayed MT7 redGem", after_redgem))

    summary_path = os.path.join("outputs", "results", "walkthrough_fixed_prefix_summary.json")
    with open(summary_path, "r", encoding="utf-8") as f:
        summary = json.load(f)
    entry = after_redgem
    for seg in summary["search_segments"]:
        entry, err = consume(entry, seg["floor"], seg["targets"], seg["flyback"])
        label = f"{seg['floor']} {seg['targets']} flyback={seg['flyback']}"
        if entry is None:
            chain.append((f"FAILED {label}: {err}", chain[-1][1]))
            break
        chain.append((label, entry))

    lines = []
    lines.append("# Forced Fixed Continuation From Delayed Phase1")
    lines.append("")
    lines.append("| step | state | dmg |")
    lines.append("|---|---|---:|")
    for label, item in chain:
        lines.append(f"| {label} | {state_str(item)} | {item.get('_dmg', 0)} |")
    lines.append("")
    final_label, final_entry = chain[-1]
    if not final_label.startswith("FAILED"):
        lines.append(f"- final: {state_str(final_entry)} dmg={final_entry.get('_dmg', 0)}")
    text = "\n".join(lines).rstrip() + "\n"
    out_path = os.path.join("outputs", "reports", "forced_delayed_continuation.md")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(text)


if __name__ == "__main__":
    main()
