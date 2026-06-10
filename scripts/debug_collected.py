# Allow scripts to import project-root modules after being moved under scripts/.
import os as _codex_os
import sys as _codex_sys
_codex_root = _codex_os.path.dirname(_codex_os.path.dirname(_codex_os.path.abspath(__file__)))
if _codex_root not in _codex_sys.path:
    _codex_sys.path.insert(0, _codex_root)

import json
import os
from tmp import load_map, search, trace_path, make_modified_map

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
hero = json.load(open(os.path.join('data', 'maps', 'hero_state.json')))
maps = {}
for fid in ['mt1', 'mt3', 'mt4', 'mt5', 'mt6', 'mt7']:
    maps[fid.upper()] = load_map(fid)

# Simulate the ATK=20 state after MT7
collected = set()
# We need to figure out what collected looks like for the ATK=20 state
# Let's reconstruct by running the search step by step

state = {'hp': hero['h'], 'atk': hero['a'], 'def': hero['d'], 'yk': hero['yk'], 'bk': hero['bk'], 'collected': collected}

# MT4
modified = make_modified_map(maps['MT4'], state['collected'])
pareto, _, nodes, frm = search(modified, 11, 10, state['hp'], state['atk'], state['def'], state['yk'], state['bk'], ['upFloor', 'redGem'])
# Take the HP=852 ATK=10 state (no redGem)
for p in pareto:
    if p[3] == 10:
        ops, newly = trace_path(p, nodes, frm, state['hp'], state['yk'], state['bk'], state['atk'], state['def'])
        state = {'hp': p[0], 'yk': p[1], 'bk': p[2], 'atk': p[3], 'def': p[4], 'collected': state['collected'] | newly}
        break

print(f"After MT4: ATK={state['atk']} collected={len(state['collected'])}")
print(f"  items: {sorted(state['collected'])}")

# MT5
modified = make_modified_map(maps['MT5'], state['collected'])
pareto, _, nodes, frm = search(modified, 2, 11, state['hp'], state['atk'], state['def'], state['yk'], state['bk'], ['sword1', 'upFloor'])
for p in pareto:
    ops, newly = trace_path(p, nodes, frm, state['hp'], state['yk'], state['bk'], state['atk'], state['def'])
    if any(op[2] == 'sword1' for op in ops):
        state = {'hp': p[0], 'yk': p[1], 'bk': p[2], 'atk': p[3], 'def': p[4], 'collected': state['collected'] | newly}
        break

print(f"After MT5: ATK={state['atk']} collected={len(state['collected'])}")
print(f"  items: {sorted(state['collected'])}")

# MT6
modified = make_modified_map(maps['MT6'], state['collected'])
pareto, _, nodes, frm = search(modified, 1, 2, state['hp'], state['atk'], state['def'], state['yk'], state['bk'], ['upFloor'])
if pareto:
    p = pareto[0]
    ops, newly = trace_path(p, nodes, frm, state['hp'], state['yk'], state['bk'], state['atk'], state['def'])
    state = {'hp': p[0], 'yk': p[1], 'bk': p[2], 'atk': p[3], 'def': p[4], 'collected': state['collected'] | newly}

print(f"After MT6: ATK={state['atk']} collected={len(state['collected'])}")
print(f"  items: {sorted(state['collected'])}")

# MT7
modified = make_modified_map(maps['MT7'], state['collected'])
pareto, _, nodes, frm = search(modified, 1, 11, state['hp'], state['atk'], state['def'], state['yk'], state['bk'], ['upFloor', 'redGem'])
for p in pareto:
    if p[3] == 20:  # ATK=20 state (no redGem)
        ops, newly = trace_path(p, nodes, frm, state['hp'], state['yk'], state['bk'], state['atk'], state['def'])
        state = {'hp': p[0], 'yk': p[1], 'bk': p[2], 'atk': p[3], 'def': p[4], 'collected': state['collected'] | newly}
        break

print(f"After MT7: ATK={state['atk']} collected={len(state['collected'])}")
print(f"  items: {sorted(state['collected'])}")

# Now check MT1 with this collected
print("\n=== MT1 modified map ===")
mt1_mod = make_modified_map(maps['MT1'], state['collected'])
redgems = [b for b in mt1_mod['bl'] if b[3] == 'redGem']
bluegems = [b for b in mt1_mod['bl'] if b[3] == 'blueGem']
print(f"redGems remaining: {redgems}")
print(f"blueGems remaining: {bluegems}")

# Search MT1
pareto, iters, nodes, frm = search(mt1_mod, 1, 1, state['hp'], state['atk'], state['def'], state['yk'], state['bk'], ['redGem', 'blueGem'])
print(f"MT1 search results: {len(pareto)}, iters={iters}")
for p in pareto:
    print(f"  HP={p[0]} ATK={p[3]} DEF={p[4]}")
