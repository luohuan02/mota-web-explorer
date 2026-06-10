# Allow scripts to import project-root modules after being moved under scripts/.
import os as _codex_os
import sys as _codex_sys
_codex_root = _codex_os.path.dirname(_codex_os.path.dirname(_codex_os.path.abspath(__file__)))
if _codex_root not in _codex_sys.path:
    _codex_sys.path.insert(0, _codex_root)

from tmp import load_map, search, trace_path

m3 = load_map('mt3')
for yk in [0, 1, 2, 3, 4]:
    print(f"=== MT3 start_yk={yk} ===")
    pareto, iters, nodes, frm = search(m3, 11, 11, 500, 20, 10, yk, 0, ['redGem'])
    print(f"  Results: {len(pareto)}, iters={iters}")
    for p in pareto:
        print(f"    HP={p[0]} ATK={p[3]} DEF={p[4]} YK={p[1]}")
        ops, _ = trace_path(p, nodes, frm, 500, yk, 0, 20, 10)
        print(f"    Ops: {[op[2] for op in ops]}")

m1 = load_map('mt1')
for yk in [0, 1, 2, 3, 4]:
    print(f"=== MT1 start_yk={yk} ===")
    pareto, iters, nodes, frm = search(m1, 1, 1, 500, 20, 10, yk, 0, ['redGem'])
    print(f"  Results: {len(pareto)}, iters={iters}")
    for p in pareto:
        print(f"    HP={p[0]} ATK={p[3]} DEF={p[4]} YK={p[1]}")
