# Allow scripts to import project-root modules after being moved under scripts/.
import os as _codex_os
import sys as _codex_sys
_codex_root = _codex_os.path.dirname(_codex_os.path.dirname(_codex_os.path.abspath(__file__)))
if _codex_root not in _codex_sys.path:
    _codex_sys.path.insert(0, _codex_root)

from tmp import load_map, search, trace_path

m7 = load_map('mt7')
for targets in [['upFloor'], ['upFloor', 'redGem']]:
    print(f"\n=== MT7 targets={targets} ===")
    for yk in [0, 1, 2, 3]:
        pareto, iters, nodes, frm = search(m7, 1, 11, 600, 21, 10, yk, 0, targets)
        print(f"  start_yk={yk}: {len(pareto)} results, iters={iters}")
        for p in pareto[:5]:
            print(f"    HP={p[0]} ATK={p[3]} DEF={p[4]} YK={p[1]}")
            ops, _ = trace_path(p, nodes, frm, 600, yk, 0, 21, 10)
            print(f"      ops: {[op[2] for op in ops]}")
