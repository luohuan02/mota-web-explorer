#!/usr/bin/env python3
"""Continue the delayed 7F red-gem Phase1 candidate explicitly."""

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

from src.solver import gen_walkthrough as gw
import run_guided_strategy_compare as guided


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)


def state_str(e):
    return gw.state_str(e["hp"], e["atk"], e["def"], e["yk"], e["bk"], e["rk"])


def has_pos(entry, fid, pos):
    return pos in entry.get("collected", {}).get(fid, frozenset())


FUTURE_KEY_POS = {
    "MT7": {(9, 10), (9, 11), (9, 1), (9, 2), (5, 10), (5, 11)},
    "MT6": {(9, 1)},
    "MT9": {(9, 9), (1, 7), (5, 7)},
}


def future_key_left(entry):
    total = 0
    for fid, positions in FUTURE_KEY_POS.items():
        consumed = entry.get("collected", {}).get(fid, frozenset())
        total += sum(1 for pos in positions if pos not in consumed)
    return total


def select_delayed(entries):
    matches = [
        e for e in entries
        if e["atk"] == 22 and e["def"] == 21 and e["yk"] == 2 and e["bk"] == 1 and
        e["rk"] == 0 and not has_pos(e, "MT7", (3, 1))
    ]
    if not matches:
        return None
    return sorted(matches, key=lambda e: (-future_key_left(e), e.get("_dmg", 0), -e["hp"]))[0]


def take_mt7_redgem(entry):
    al = entry.get("collected", {}).get("MT7", frozenset())
    pareto, _, _ = gw.search_floor(gw.maps, "MT7", entry, ["redGem"], flyback=True)
    results = []
    for hp, yk, bk, rk, atk, def_, hs, vis, dc in pareto:
        if (3, 1) not in vis:
            continue
        nc = dict(entry.get("collected", {}))
        nc["MT7"] = al | vis
        results.append(
            {
                "hp": hp,
                "atk": atk,
                "def": def_,
                "yk": yk,
                "bk": bk,
                "rk": rk,
                "collected": nc,
                "_dmg": entry.get("_dmg", 0) + dc,
            }
        )
    if not results:
        return None
    return sorted(results, key=lambda e: (e.get("_dmg", 0), -e["hp"], -e["yk"]))[0]


def main():
    t0 = time.time()
    entries = guided.run_guided_phase1(retry_level=0)
    delayed = select_delayed(entries)
    if delayed is None:
        raise SystemExit("no delayed candidate")
    print(
        f"delayed start: {state_str(delayed)} dmg={delayed.get('_dmg', 0)} "
        f"futureKeys={future_key_left(delayed)}"
    )
    after_redgem = take_mt7_redgem(delayed)
    if after_redgem is None:
        raise SystemExit("cannot take MT7 redGem")
    print(f"after MT7 redGem: {state_str(after_redgem)} dmg={after_redgem.get('_dmg', 0)}")

    result = gw.run_search(retry_level=0, initial_entry=after_redgem, skip_phase1=True)
    record = {
        "delayed_start": {
            "hp": delayed["hp"],
            "atk": delayed["atk"],
            "def": delayed["def"],
            "yk": delayed["yk"],
            "bk": delayed["bk"],
            "rk": delayed["rk"],
            "dmg": delayed.get("_dmg", 0),
        },
        "after_redgem": {
            "hp": after_redgem["hp"],
            "atk": after_redgem["atk"],
            "def": after_redgem["def"],
            "yk": after_redgem["yk"],
            "bk": after_redgem["bk"],
            "rk": after_redgem["rk"],
            "dmg": after_redgem.get("_dmg", 0),
        },
        "elapsed": time.time() - t0,
    }
    if result:
        record["result"] = {
            "hp": result["hp"],
            "atk": result["atk"],
            "def": result["def"],
            "yk": result["yk"],
            "bk": result["bk"],
            "rk": result["rk"],
            "dmg": result.get("_dmg", 0),
        }
        print(f"final: {state_str(result)} dmg={result.get('_dmg', 0)}")
    else:
        record["result"] = None
        print("final: failed")
    out_path = os.path.join("outputs", "results", "delayed_redgem_continuation.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)
    print(f"elapsed={record['elapsed']:.1f}s")


if __name__ == "__main__":
    main()
