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


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

FUTURE_KEY_POS = {
    "MT7": {(9, 10), (9, 11), (9, 1), (9, 2), (5, 10), (5, 11)},
    "MT6": {(9, 1)},
    "MT9": {(9, 9), (1, 7), (5, 7)},
}


def has_pos(entry, fid, pos):
    return pos in entry.get("collected", {}).get(fid, frozenset())


def future_keys_left(entry):
    left = 0
    parts = []
    for fid, positions in FUTURE_KEY_POS.items():
        consumed = entry.get("collected", {}).get(fid, frozenset())
        remain = sorted(pos for pos in positions if pos not in consumed)
        left += len(remain)
        parts.append(f"{fid}:{remain}")
    return left, " ".join(parts)


def main():
    entries = guided.run_guided_phase1(retry_level=0)
    rows = []
    for e in entries:
        if e["def"] == 21 and e["yk"] == 2 and e["bk"] == 1 and e["rk"] == 0 and e["atk"] in {22, 23}:
            left, detail = future_keys_left(e)
            rows.append((left, e.get("_dmg", 0), e["hp"], e, detail))
    rows.sort(key=lambda x: (-x[0], x[1], -x[2]))
    print(f"ATK22/23 DEF21 YK2 BK1 candidates: {len(rows)}")
    for i, (left, dmg, hp, e, detail) in enumerate(rows[:20], 1):
        flags = [
            f"MT7red={(3, 1) in e.get('collected', {}).get('MT7', frozenset())}",
            f"MT7door35={(3, 5) in e.get('collected', {}).get('MT7', frozenset())}",
            f"MT6_9_1={(9, 1) in e.get('collected', {}).get('MT6', frozenset())}",
        ]
        print(
            f"{i:02d} left={left} dmg={dmg} hp={hp} "
            f"{gw.state_str(e['hp'], e['atk'], e['def'], e['yk'], e['bk'], e['rk'])} "
            f"{' '.join(flags)} {detail}"
        )


if __name__ == "__main__":
    main()
