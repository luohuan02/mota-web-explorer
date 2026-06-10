from __future__ import annotations

# Allow scripts to import project-root modules after being moved under scripts/.
import os as _codex_os
import sys as _codex_sys
_codex_root = _codex_os.path.dirname(_codex_os.path.dirname(_codex_os.path.abspath(__file__)))
if _codex_root not in _codex_sys.path:
    _codex_sys.path.insert(0, _codex_root)

import os

from src.solver import gen_walkthrough as gw
import run_guided_strategy_compare as guided
from continue_delayed_redgem_candidate import future_key_left, select_delayed
from try_forced_fixed_continuation_from_delayed import consume, make_entry


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)


def item_at(fid, pos):
    for b in gw.maps[fid]["bl"]:
        if (b[0], b[1]) == pos:
            return b[3]
    return "?"


def show(entry, label):
    print(
        label,
        gw.state_str(entry["hp"], entry["atk"], entry["def"], entry["yk"], entry["bk"], entry["rk"]),
        "dmg",
        entry.get("_dmg", 0),
        "futureKeys",
        future_key_left(entry),
    )
    for fid in ["MT7", "MT9", "MT8", "MT6", "MT5", "MT4"]:
        pos = sorted(entry.get("collected", {}).get(fid, frozenset()))
        named = [f"{p}:{item_at(fid, p)}" for p in pos]
        print(fid, ", ".join(named))


def main():
    entries = guided.run_guided_phase1(retry_level=0)
    delayed = make_entry(select_delayed(entries))
    after_redgem, err = consume(delayed, "MT7", ["redGem"], True)
    if after_redgem is None:
        raise SystemExit(err)
    show(delayed, "delayed")
    show(after_redgem, "after_redgem")


if __name__ == "__main__":
    main()
