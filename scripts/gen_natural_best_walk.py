#!/usr/bin/env python3
"""Generate a full walk for the best completed natural Phase1 candidate."""

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

import continue_selected_phase1_candidates as selected
from src.solver import gen_walkthrough as gw
import run_guided_strategy_compare as guided
from gen_guided_candidate_walk import append_chain_walk, clone_chain, clone_entry, entry_state


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

TARGET_LABEL = "current_atk23_yk2_bk1"
OUT_MD = os.path.join("outputs", "walkthroughs", "walkthrough_natural_atk23_dmg2600.md")
OUT_JSON = os.path.join("outputs", "results", "walkthrough_natural_atk23_dmg2600_summary.json")


def main():
    t0 = time.time()
    print("Run guided Phase1...")
    entries = guided.run_guided_phase1(retry_level=0)
    candidates = selected.select_candidates(entries)
    item = next((c for c in candidates if c["label"] == TARGET_LABEL), None)
    if item is None:
        raise SystemExit(f"candidate {TARGET_LABEL} not found")

    candidate = item["entry"]
    phase1_chain = clone_chain(gw.trace_chain(candidate))
    print(f"Selected {TARGET_LABEL}: {entry_state(candidate)} dmg={candidate.get('_dmg', 0)}")

    print("Continue selected candidate...")
    result = gw.run_search(
        retry_level=0,
        initial_entry=clone_entry(candidate),
        skip_phase1=True,
    )
    if result is None:
        raise SystemExit("continuation failed")

    continuation_chain = clone_chain(gw.trace_chain(result))
    print(f"Final: {entry_state(result)} dmg={result.get('_dmg', 0)}")

    lines = []
    lines.append("# Natural Candidate ATK23 DMG2600 Walk")
    lines.append("")
    lines.append(f"> Phase1: {gw.entry_summary(candidate)}")
    lines.append(f"> Final: {gw.entry_summary(result)}")
    lines.append("")
    lines.append("## Comparison")
    lines.append("")
    lines.append("- fixed final: HP=55 ATK=27 DEF=27 YK=0 BK=0 RK=0 dmg=2621 doorY/B/R=42/2/1")
    lines.append(
        f"- natural final: {entry_state(result)} dmg={result.get('_dmg', 0)} "
        f"doorY/B/R={result.get('_yd', 0)}/{result.get('_bd', 0)}/{result.get('_rd', 0)}"
    )
    lines.append("- natural saves dmg with the same final stats, keys, and door costs; HP is only a tie-break under the current score.")
    lines.append("")
    append_chain_walk(lines, phase1_chain, "Natural Phase1")
    append_chain_walk(lines, continuation_chain, "Continuation To Boss")
    lines.append("## Final")
    lines.append("")
    lines.append(f"**{gw.entry_summary(result)}**")
    lines.append("")

    os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(
            {
                "label": TARGET_LABEL,
                "phase1": {
                    "hp": candidate["hp"],
                    "atk": candidate["atk"],
                    "def": candidate["def"],
                    "yk": candidate["yk"],
                    "bk": candidate["bk"],
                    "rk": candidate["rk"],
                    "dmg": candidate.get("_dmg", 0),
                    "yd": candidate.get("_yd", 0),
                    "bd": candidate.get("_bd", 0),
                    "rd": candidate.get("_rd", 0),
                },
                "final": {
                    "hp": result["hp"],
                    "atk": result["atk"],
                    "def": result["def"],
                    "yk": result["yk"],
                    "bk": result["bk"],
                    "rk": result["rk"],
                    "dmg": result.get("_dmg", 0),
                    "yd": result.get("_yd", 0),
                    "bd": result.get("_bd", 0),
                    "rd": result.get("_rd", 0),
                },
                "elapsed": time.time() - t0,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    print(f"Wrote {OUT_MD}")
    print(f"Wrote {OUT_JSON}")
    print(f"elapsed={time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
