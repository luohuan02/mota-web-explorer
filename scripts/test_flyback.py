# Allow scripts to import project-root modules after being moved under scripts/.
import os as _codex_os
import sys as _codex_sys
_codex_root = _codex_os.path.dirname(_codex_os.path.dirname(_codex_os.path.abspath(__file__)))
if _codex_root not in _codex_sys.path:
    _codex_sys.path.insert(0, _codex_root)

import json
from tmp import load_map, search, trace_path

m1 = load_map('mt1')
m3 = load_map('mt3')

print("=== MT1 from (1,1) target redGem ===")
pareto, iters, nodes, frm = search(m1, 1, 1, 926, 10, 10, 4, 1, ['redGem'])
print(f"Results: {len(pareto)}, iters={iters}")
for p in pareto:
    print(f"  HP={p[0]} ATK={p[3]} DEF={p[4]}")
    ops, collected = trace_path(p, nodes, frm, 926, 4, 1, 10, 10)
    print(f"  Ops: {[op[2] for op in ops]}")

print("\n=== MT1 from (1,1) target redGem+blueGem ===")
pareto, iters, nodes, frm = search(m1, 1, 1, 926, 10, 10, 4, 1, ['redGem', 'blueGem'])
print(f"Results: {len(pareto)}, iters={iters}")
for p in pareto:
    print(f"  HP={p[0]} ATK={p[3]} DEF={p[4]}")

print("\n=== MT3 from (11,11) target redGem ===")
pareto, iters, nodes, frm = search(m3, 11, 11, 926, 10, 10, 4, 1, ['redGem'])
print(f"Results: {len(pareto)}, iters={iters}")
for p in pareto:
    print(f"  HP={p[0]} ATK={p[3]} DEF={p[4]}")
    ops, collected = trace_path(p, nodes, frm, 926, 4, 1, 10, 10)
    print(f"  Ops: {[op[2] for op in ops]}")
