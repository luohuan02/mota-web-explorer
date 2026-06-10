#!/usr/bin/env python3
"""Debug MT8 path requirements"""
# Allow scripts to import project-root modules after being moved under scripts/.
import os as _codex_os
import sys as _codex_sys
_codex_root = _codex_os.path.dirname(_codex_os.path.dirname(_codex_os.path.abspath(__file__)))
if _codex_root not in _codex_sys.path:
    _codex_sys.path.insert(0, _codex_root)

import json
from debug_path import load_map, search

maps = {}
for fid in ['mt8']:
    maps[fid.upper()] = load_map(fid)

# Try various states entering MT8
states = [
    {'hp': 500, 'atk': 23, 'def': 10, 'yk': 1, 'bk': 1},
    {'hp': 500, 'atk': 23, 'def': 10, 'yk': 2, 'bk': 1},
    {'hp': 500, 'atk': 23, 'def': 10, 'yk': 3, 'bk': 1},
    {'hp': 500, 'atk': 23, 'def': 11, 'yk': 1, 'bk': 1},
    {'hp': 500, 'atk': 23, 'def': 11, 'yk': 2, 'bk': 1},
    {'hp': 400, 'atk': 23, 'def': 10, 'yk': 2, 'bk': 1},
    {'hp': 587, 'atk': 23, 'def': 11, 'yk': 0, 'bk': 1},
    {'hp': 600, 'atk': 22, 'def': 10, 'yk': 2, 'bk': 1},
    {'hp': 600, 'atk': 22, 'def': 11, 'yk': 2, 'bk': 1},
]

for s in states:
    print(f"\nMT8 start: HP={s['hp']} ATK={s['atk']} DEF={s['def']} YK={s['yk']}")
    pareto, iters, nodes, frm = search(
        maps['MT8'], 1, 1,
        s['hp'], s['atk'], s['def'], s['yk'], s['bk'],
        ['upFloor'], max_iter=200000
    )
    print(f"  Results: {len(pareto)}, iters={iters}")
    for p in pareto[:3]:
        hp, yk, bk, atk, def_ = p[:5]
        print(f"    HP={hp} ATK={atk} DEF={def_} YK={yk}")

# Also print MT8 map monsters
print("\n=== MT8 monsters ===")
for b in maps['MT8']['bl']:
    if b[2] == 1:
        print(f"  ({b[0]},{b[1]}) {b[3]}")
print("\n=== MT8 doors ===")
for b in maps['MT8']['bl']:
    if b[2] == 2:
        print(f"  ({b[0]},{b[1]}) {b[3]}")
print("\n=== MT8 items ===")
for b in maps['MT8']['bl']:
    if b[2] == 3:
        print(f"  ({b[0]},{b[1]}) {b[3]}")
