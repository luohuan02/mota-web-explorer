# Allow scripts to import project-root modules after being moved under scripts/.
import os as _codex_os
import sys as _codex_sys
_codex_root = _codex_os.path.dirname(_codex_os.path.dirname(_codex_os.path.abspath(__file__)))
if _codex_root not in _codex_sys.path:
    _codex_sys.path.insert(0, _codex_root)

from tmp import load_map, search, trace_path

m4 = load_map('mt4')
for max_iter in [200000, 500000, 1000000]:
    print(f"\n=== MT4 max_iter={max_iter} ===")
    pareto, iters, nodes, frm = search(m4, 11, 10, 926, 10, 10, 4, 1, ['upFloor', 'redGem'], max_iter=max_iter)
    print(f"Results: {len(pareto)}, iters={iters}")
    for p in pareto[:15]:
        print(f"  HP={p[0]:4d} ATK={p[3]} DEF={p[4]} YK={p[1]} BK={p[2]}")
