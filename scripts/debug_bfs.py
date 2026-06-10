# Allow scripts to import project-root modules after being moved under scripts/.
import os as _codex_os
import sys as _codex_sys
_codex_root = _codex_os.path.dirname(_codex_os.path.dirname(_codex_os.path.abspath(__file__)))
if _codex_root not in _codex_sys.path:
    _codex_sys.path.insert(0, _codex_root)

import json
from tmp import load_map, search, make_modified_map

m1 = load_map('mt1')
print("MT1 map grid around (1,1):")
for y in range(0, 6):
    row = ""
    for x in range(0, 8):
        v = m1['m'][y][x]
        # check if there's a block here
        block = [b for b in m1['bl'] if b[0]==x and b[1]==y]
        if block:
            row += f" {block[0][3][:3]:3s}"
        elif v == 1:
            row += " WALL"
        else:
            row += "  .  "
    print(f"y={y}: {row}")

# Check what blocks are at (1,1) and neighbors
print("\nBlocks near (1,1):")
for b in m1['bl']:
    if b[0] <= 3 and b[1] <= 3:
        print(f"  ({b[0]},{b[1]}) t={b[2]} eid={b[3]}")

# Test BFS manually
from collections import deque
W, H = m1['W'], m1['H']
mapd = m1['m']
nodes = []; pm = {}
for b in m1['bl']:
    x, y, t, eid = b
    nodes.append((x, y, t, eid)); pm[(x, y)] = len(nodes) - 1

def is_wall(x, y):
    return x <= 0 or y <= 0 or x >= W-1 or y >= H-1 or mapd[y][x] == 1

px, py = 1, 1
vm = 0
v = {(px, py)}; q = deque([(px, py)]); r = []
while q:
    cx, cy = q.popleft()
    for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
        nx, ny = cx+dx, cy+dy
        if is_wall(nx, ny):
            print(f"  wall at ({nx},{ny})")
            continue
        if (nx, ny) in v:
            continue
        v.add((nx, ny))
        ni = pm.get((nx, ny))
        if ni is not None:
            if vm & (1 << ni):
                q.append((nx, ny))
                continue
            r.append(ni)
            print(f"  found node {ni}: {nodes[ni]}")
            if nodes[ni][2] in (3, 4):
                q.append((nx, ny))
            continue
        q.append((nx, ny))

print(f"\nReachable from (1,1): {len(r)} nodes")

# Also test with the ATK=20 state
print("\n=== Test search from ATK=20 state ===")
modified = make_modified_map(m1, set())
pareto, iters, nodes, frm = search(modified, 1, 1, 678, 20, 10, 0, 0, ['redGem'])
print(f"Results: {len(pareto)}, iters={iters}")
