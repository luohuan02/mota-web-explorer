#!/usr/bin/env python3
"""Continue representative retained Phase1 Pareto candidates."""

from __future__ import annotations

# Allow scripts to import project-root modules after being moved under scripts/.
import os as _codex_os
import sys as _codex_sys
_codex_root = _codex_os.path.dirname(_codex_os.path.dirname(_codex_os.path.abspath(__file__)))
if _codex_root not in _codex_sys.path:
    _codex_sys.path.insert(0, _codex_root)

import json
import multiprocessing as mp
import os
import time

from src.solver import gen_walkthrough as gw
import run_guided_strategy_compare as guided


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

PER_CANDIDATE_TIMEOUT_SECONDS = 300


def state_str(e):
    return gw.state_str(e["hp"], e["atk"], e["def"], e["yk"], e["bk"], e["rk"])


def state_record(e):
    return {
        "hp": e["hp"],
        "atk": e["atk"],
        "def": e["def"],
        "yk": e["yk"],
        "bk": e["bk"],
        "rk": e["rk"],
        "dmg": e.get("_dmg", 0),
    }


def has_pos(entry, fid, pos):
    return pos in entry.get("collected", {}).get(fid, frozenset())


def collected_signature(entry):
    return tuple(
        (fid, tuple(sorted(pos)))
        for fid, pos in sorted(entry.get("collected", {}).items())
        if pos
    )


def clone_entry(entry):
    out = dict(entry)
    out["collected"] = {
        fid: frozenset(pos)
        for fid, pos in entry.get("collected", {}).items()
    }
    return out


def candidate_flags(entry):
    return {
        "mt7_redgem_3_1": has_pos(entry, "MT7", (3, 1)),
        "mt7_door_3_5": has_pos(entry, "MT7", (3, 5)),
        "mt6_bluepriest_7_1": has_pos(entry, "MT6", (7, 1)),
        "mt6_ykey_9_1": has_pos(entry, "MT6", (9, 1)),
        "mt9_redgem_6_5": has_pos(entry, "MT9", (6, 5)),
        "mt9_bluegem_1_5": has_pos(entry, "MT9", (1, 5)),
    }


def add_candidate(selected, seen, label, entry):
    if entry is None:
        return
    sig = collected_signature(entry)
    key = (label, sig)
    if key in seen:
        return
    seen.add(key)
    selected.append(
        {
            "label": label,
            "entry": clone_entry(entry),
            "start": state_record(entry),
            "flags": candidate_flags(entry),
        }
    )


def best(entries, pred, key):
    matches = [e for e in entries if pred(e)]
    if not matches:
        return None
    return sorted(matches, key=key)[0]


def select_candidates(entries):
    selected = []
    seen = set()

    add_candidate(
        selected,
        seen,
        "delayed_7f_redgem_exact",
        best(
            entries,
            lambda e: e["atk"] == 22 and e["def"] == 21 and e["yk"] == 2 and
            e["bk"] == 1 and not has_pos(e, "MT7", (3, 1)),
            lambda e: (e.get("_dmg", 0), -e["hp"]),
        ),
    )
    add_candidate(
        selected,
        seen,
        "current_atk23_yk2_bk1",
        best(
            entries,
            lambda e: e["atk"] == 23 and e["def"] == 21 and e["yk"] == 2 and
            e["bk"] == 1 and has_pos(e, "MT7", (3, 1)),
            lambda e: (e.get("_dmg", 0), -e["hp"]),
        ),
    )
    add_candidate(
        selected,
        seen,
        "current_atk23_yk3",
        best(
            entries,
            lambda e: e["atk"] == 23 and e["def"] == 21 and e["yk"] == 3 and
            e["bk"] >= 1,
            lambda e: (e.get("_dmg", 0), -e["hp"]),
        ),
    )
    add_candidate(
        selected,
        seen,
        "current_high_key_yk7",
        best(
            entries,
            lambda e: e["atk"] == 23 and e["def"] == 21 and e["yk"] >= 7 and
            e["bk"] >= 1,
            lambda e: (e.get("_dmg", 0), -e["hp"]),
        ),
    )
    add_candidate(
        selected,
        seen,
        "high_stat_24_22_yk2_bk1",
        best(
            entries,
            lambda e: e["atk"] >= 24 and e["def"] >= 22 and e["yk"] >= 2 and
            e["bk"] >= 1,
            lambda e: (e.get("_dmg", 0), -e["hp"]),
        ),
    )
    add_candidate(
        selected,
        seen,
        "low_dmg_no_bk_yk3",
        best(
            entries,
            lambda e: e["atk"] == 22 and e["def"] == 21 and e["yk"] >= 3 and
            e["bk"] == 0,
            lambda e: (e.get("_dmg", 0), -e["hp"]),
        ),
    )
    return selected


def worker(entry, queue):
    t0 = time.time()
    try:
        result = gw.run_search(retry_level=0, initial_entry=entry, skip_phase1=True)
        if result is None:
            queue.put({"status": "failed", "elapsed": time.time() - t0})
        else:
            queue.put(
                {
                    "status": "success",
                    "elapsed": time.time() - t0,
                    "final": state_record(result),
                }
            )
    except Exception as exc:
        queue.put({"status": "error", "elapsed": time.time() - t0, "error": repr(exc)})


def continue_one(item):
    queue = mp.Queue()
    process = mp.Process(target=worker, args=(item["entry"], queue))
    process.start()
    process.join(PER_CANDIDATE_TIMEOUT_SECONDS)
    if process.is_alive():
        process.terminate()
        process.join(10)
        return {
            "status": "timeout",
            "elapsed": PER_CANDIDATE_TIMEOUT_SECONDS,
        }
    if not queue.empty():
        return queue.get()
    return {"status": "no_result", "elapsed": 0}


def write_report(results):
    lines = []
    lines.append("# Phase1 Continuation Results")
    lines.append("")
    lines.append(
        f"- per-candidate timeout: {PER_CANDIDATE_TIMEOUT_SECONDS}s"
    )
    lines.append("")
    lines.append("| label | start | start dmg | key flags | status | final | final dmg | elapsed |")
    lines.append("|---|---|---:|---|---|---|---:|---:|")
    for item in results:
        start = item["start"]
        result = item["result"]
        flags = item["flags"]
        flag_text = (
            f"7Fgem={'Y' if flags['mt7_redgem_3_1'] else 'N'}, "
            f"7Fdoor={'Y' if flags['mt7_door_3_5'] else 'N'}, "
            f"6Fmage={'Y' if flags['mt6_bluepriest_7_1'] else 'N'}, "
            f"6Fkey={'Y' if flags['mt6_ykey_9_1'] else 'N'}"
        )
        final = result.get("final")
        final_text = "none"
        final_dmg = ""
        if final:
            final_text = state_str(final)
            final_dmg = str(final.get("dmg", 0))
        lines.append(
            f"| {item['label']} | {state_str(start)} | {start.get('dmg', 0)} | "
            f"{flag_text} | {result['status']} | {final_text} | {final_dmg} | "
            f"{result.get('elapsed', 0):.1f} |"
        )
    lines.append("")
    successful = [r for r in results if r["result"]["status"] == "success"]
    if successful:
        best_by_dmg = min(successful, key=lambda r: (r["result"]["final"]["dmg"], -r["result"]["final"]["hp"]))
        best_by_hp = max(successful, key=lambda r: r["result"]["final"]["hp"])
        lines.append(
            f"- best by dmg: {best_by_dmg['label']} "
            f"{state_str(best_by_dmg['result']['final'])} dmg={best_by_dmg['result']['final']['dmg']}"
        )
        lines.append(
            f"- best by HP: {best_by_hp['label']} "
            f"{state_str(best_by_hp['result']['final'])} dmg={best_by_hp['result']['final']['dmg']}"
        )
    else:
        lines.append("- no selected candidate completed within this run")
    lines.append("")

    serializable = []
    for item in results:
        serializable.append(
            {
                "label": item["label"],
                "start": item["start"],
                "flags": item["flags"],
                "result": item["result"],
            }
        )
    result_path = os.path.join("outputs", "results", "phase1_continuation_results.json")
    report_path = os.path.join("outputs", "reports", "phase1_continuation_results.md")
    os.makedirs(os.path.dirname(result_path), exist_ok=True)
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(serializable, f, ensure_ascii=False, indent=2)
    text = "\n".join(lines).rstrip() + "\n"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(text)


def main():
    mp.freeze_support()
    entries = guided.run_guided_phase1(retry_level=0)
    candidates = select_candidates(entries)
    results = []
    for item in candidates:
        print(
            f"continue {item['label']}: {state_str(item['start'])} dmg={item['start']['dmg']}",
            flush=True,
        )
        result = continue_one(item)
        item["result"] = result
        results.append(item)
        print(f"  -> {result['status']} elapsed={result.get('elapsed', 0):.1f}s", flush=True)
        write_report(results)


if __name__ == "__main__":
    main()
