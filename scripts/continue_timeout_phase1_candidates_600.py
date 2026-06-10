#!/usr/bin/env python3
"""Retry previously timed-out Phase1 candidates with a longer timeout."""

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

import continue_selected_phase1_candidates as base
from src.solver import gen_walkthrough as gw
import run_guided_strategy_compare as guided


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

PER_CANDIDATE_TIMEOUT_SECONDS = 600
TARGET_LABELS = {
    "delayed_7f_redgem_exact",
    "current_high_key_yk7",
    "high_stat_24_22_yk2_bk1",
    "low_dmg_no_bk_yk3",
}
OUT_MD = os.path.join("outputs", "reports", "phase1_continuation_results_600.md")
OUT_JSON = os.path.join("outputs", "results", "phase1_continuation_results_600.json")


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
                    "final": base.state_record(result),
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
        return {"status": "timeout", "elapsed": PER_CANDIDATE_TIMEOUT_SECONDS}
    if not queue.empty():
        return queue.get()
    return {"status": "no_result", "elapsed": 0}


def write_report(results):
    lines = []
    lines.append("# Phase1 Continuation Results 600s")
    lines.append("")
    lines.append(f"- per-candidate timeout: {PER_CANDIDATE_TIMEOUT_SECONDS}s")
    lines.append("- candidates: previously timed-out representatives only")
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
            final_text = base.state_str(final)
            final_dmg = str(final.get("dmg", 0))
        lines.append(
            f"| {item['label']} | {base.state_str(start)} | {start.get('dmg', 0)} | "
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
            f"{base.state_str(best_by_dmg['result']['final'])} dmg={best_by_dmg['result']['final']['dmg']}"
        )
        lines.append(
            f"- best by HP: {best_by_hp['label']} "
            f"{base.state_str(best_by_hp['result']['final'])} dmg={best_by_hp['result']['final']['dmg']}"
        )
    else:
        lines.append("- no retried candidate completed within 600s")
    lines.append("")

    serializable = [
        {
            "label": item["label"],
            "start": item["start"],
            "flags": item["flags"],
            "result": item["result"],
        }
        for item in results
    ]
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(serializable, f, ensure_ascii=False, indent=2)
    text = "\n".join(lines).rstrip() + "\n"
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write(text)
    print(text)


def main():
    mp.freeze_support()
    t0 = time.time()
    print("Run guided Phase1...")
    entries = guided.run_guided_phase1(retry_level=0)
    candidates = [
        item for item in base.select_candidates(entries)
        if item["label"] in TARGET_LABELS
    ]
    results = []
    for item in candidates:
        print(
            f"retry {item['label']}: {base.state_str(item['start'])} dmg={item['start']['dmg']}",
            flush=True,
        )
        result = continue_one(item)
        item["result"] = result
        results.append(item)
        print(f"  -> {result['status']} elapsed={result.get('elapsed', 0):.1f}s", flush=True)
        write_report(results)
    print(f"total elapsed={time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
