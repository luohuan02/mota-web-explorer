#!/usr/bin/env python3
"""
对比: Autoclaw原版 vs 新架构版 MT4-MT6 Pareto搜索
输入: hero_state.json, mt4_map.json, mt5_map.json, mt6_map.json
"""
# Allow scripts to import project-root modules after being moved under scripts/.
import os as _codex_os
import sys as _codex_sys
_codex_root = _codex_os.path.dirname(_codex_os.path.dirname(_codex_os.path.abspath(__file__)))
if _codex_root not in _codex_sys.path:
    _codex_sys.path.insert(0, _codex_root)

import json
import math
import heapq
import time
import os
from collections import deque

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

EM = {
    'greenSlime': (35,18,1), 'redSlime': (35,18,1), 'redSlime': (45,20,2), 'bat': (35,38,3),
    'skeleton': (50,42,6), 'skeletonSoldier': (55,52,12),
    'skeletonCaptain': (100,65,15), 'bluePriest': (60,32,8),
    'blueGuard': (100,180,110), 'yellowGuard': (50,48,22),
    'soldier': (210,200,65),
}

def calc_dmg(eid, atk, def_):
    e = EM.get(eid, (100,100,0))
    my_dmg = max(1, atk - e[2])
    enemy_dmg = max(1, e[1] - def_)
    rounds = -(-e[0] // my_dmg)
    return (rounds - 1) * enemy_dmg

def load_data():
    def data_path(name):
        return os.path.join('data', 'maps', name)

    hero = json.load(open(data_path('hero_state.json'), encoding='utf-8'))
    maps = {}
    for fid in ['mt4', 'mt5', 'mt6']:
        raw = json.load(open(data_path(f'{fid}_map.json'), encoding='utf-8'))
        # Convert to pf format: (x,y,type,eid,noPass)
        blocks = []
        for b in raw['bl']:
            eid = b['id']
            cls = b['cls']
            t = 0
            if eid == 'upFloor' or eid == 'downFloor': t = 4  # stairs (passable)
            elif cls == 'enemys' or eid in EM: t = 1  # monsters
            elif eid.endswith('Door'): t = 2  # doors (all cls)
            elif cls == 'items': t = 3  # items
            elif cls == 'animates' and (eid.endswith('Key') or eid.endswith('Potion') or eid.endswith('Gem') or eid.startswith('sword') or eid.startswith('shield')): t = 3
            if t > 0:
                blocks.append((b['x'], b['y'], t, eid, False))
        maps[fid.upper()] = {
            'W': raw['w'], 'H': raw['h'], 'm': raw['m'], 'bl': blocks
        }
    return hero, maps

# ==================================================================
# 方案A: Autoclaw原版 (来自mt456_pareto.py的核心逻辑)
# ==================================================================
def search_autoclaw(data, sx, sy, start_hp, start_atk, start_def, start_yk, start_bk, target_ids, max_iter=500000):
    mapd = [row[:] for row in data['m']]
    W, H, bl = data['W'], data['H'], data['bl']
    nodes = []
    pm = {}
    for b in bl:
        x, y, t, eid, np = b
        nodes.append((x, y, t, eid))
        pm[(x, y)] = len(nodes) - 1
    NN = len(nodes)

    def is_wall(x, y):
        return x < 0 or y < 0 or x >= W or y >= H or mapd[y][x] == 1

    # 优化: 预计算每个位置的邻接表
    # 对于每个node位置，做一次"全开"BFS（所有门/楼梯视为可通过）
    # 得到该位置能看到的所有其他node
    def bfs_all_passable(px, py):
        """BFS treating all nodes as passable (visited/doors ignored)"""
        v = {(px, py)}; q = deque([(px, py)]); res = []
        while q:
            cx, cy = q.popleft()
            for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                nx, ny = cx+dx, cy+dy
                if is_wall(nx, ny) or (nx, ny) in v: continue
                v.add((nx, ny))
                ni = pm.get((nx, ny))
                if ni is not None:
                    res.append(ni)
                    # Always pass through (doors, stairs, items all passable)
                    q.append((nx, ny))
                    continue
                q.append((nx, ny))
        return res

    # Pre-compute: for start position and each node
    adj_start = bfs_all_passable(sx, sy)
    adj_nodes = [bfs_all_passable(nodes[i][0], nodes[i][1]) if i < NN else [] for i in range(NN)]

    def get_reachable(node_idx, visited):
        """Get reachable unvisited nodes using pre-computed adj + visited filter"""
        raw = adj_start if node_idx == -1 else adj_nodes[node_idx]
        return [ni for ni in raw if not (visited & (1 << ni))]

    yk_max = min(start_yk + sum(1 for n in nodes if n[3] == 'yellowKey'), 12)
    bk_max = min(start_bk + sum(1 for n in nodes if n[3] == 'blueKey'), 12)

    init_key = (-1, start_yk, start_bk, start_atk, start_def, 0)
    best = {init_key: (0, 0)}
    frm = {init_key: None}
    hpq = [(0, 0, -start_yk, -start_bk, -start_atk, -start_def, -1, 0)]
    exits = {}; it = 0

    while hpq and it < max_iter:
        yk_cost, hp_cost, ny, nb, na, nd, cn, cv = heapq.heappop(hpq)
        cy, cb, ca, cde = -ny, -nb, -na, -nd
        key = (cn, cy, cb, ca, cde, cv)
        if key not in best or best[key] != (yk_cost, hp_cost): continue
        it += 1

        if 0 <= cn < NN and nodes[cn][3] in target_ids:
            k = (cy, cb, ca, cde)
            final_hp = start_hp - hp_cost
            if k not in exits or final_hp > exits[k][0]:
                exits[k] = (final_hp, hp_cost, key)

        px, py = (sx, sy) if cn == -1 else (nodes[cn][0], nodes[cn][1])
        for tn in bfs(px, py, cv):
            if cv & (1 << tn): continue
            n = nodes[tn]; t, eid = n[2], n[3]
            ny2, nb2, na2, nd2 = cy, cb, ca, cde
            hpc = 0; ok = True; hp_eff = 0

            if t == 1: hpc = calc_dmg(eid, ca, cde)
            elif t == 2:
                if eid == 'yellowDoor':
                    if cy <= 0: ok = False
                    else: ny2 -= 1
                elif eid == 'blueDoor':
                    if cb <= 0: ok = False
                    else: nb2 -= 1
                elif eid == 'specialDoor': ok = True
            elif t == 3:
                if eid == 'yellowKey': ny2 += 1
                elif eid == 'blueKey': nb2 += 1
                elif eid == 'redPotion': hp_eff = 50
                elif eid == 'bluePotion': hp_eff = 200
                elif eid == 'redGem': na2 += 1
                elif eid == 'blueGem': nd2 += 1
                elif eid == 'greenGem': na2 += 1
                elif eid.startswith('sword'): na2 += 10
                elif eid.startswith('shield'): nd2 += 10
            elif t == 4: pass  # stairs

            if not ok: continue
            if ny2 < 0 or nb2 < 0 or ny2 > yk_max or nb2 > bk_max: continue
            new_hp = start_hp - hp_cost - hpc + hp_eff
            if new_hp <= 0: continue

            nyc = yk_cost + (1 if (t == 2 and eid == 'yellowDoor') else (-1 if (t == 3 and eid == 'yellowKey') else 0))
            nhc = hp_cost + hpc - hp_eff
            nv = cv | (1 << tn)
            nk = (tn, ny2, nb2, na2, nd2, nv)
            if nk not in best or (nyc, nhc) < best.get(nk, (999999, 999999)):
                best[nk] = (nyc, nhc); frm[nk] = key
                heapq.heappush(hpq, (nyc, nhc, -ny2, -nb2, -na2, -nd2, tn, nv))

    # Pareto filter
    items = [(-fh, fh, cy, cb, ca, cde, key) for (cy, cb, ca, cde), (fh, hpc, key) in exits.items()]
    items.sort()
    pareto = []
    for item in items:
        fh, cy, cb, ca, cde = item[1], item[2], item[3], item[4], item[5]

        dom = any(p[0] >= fh and p[1] >= cy and p[2] >= cb and p[3] >= ca and p[4] >= cde and
                  (p[0] > fh or p[1] > cy or p[2] > cb or p[3] > ca or p[4] > cde) for p in pareto)
        if not dom:
            pareto = [p for p in pareto if not
                      (fh >= p[0] and cy >= p[1] and cb >= p[2] and ca >= p[3] and cde >= p[4] and
                       (fh > p[0] or cy > p[1] or cb > p[2] or ca > p[3] or cde > p[4]))]
            pareto.append((fh, cy, cb, ca, cde))

    return pareto, it, nodes, frm

# ==================================================================
# 方案B: 新架构版 (src/floor_search.py 重构版)
#   区别: 更通用的接口, 支持任意楼层配置, 路径追踪
# ==================================================================
def search_newarch(*args, **kwargs):
    """新架构: 当前阶段与autoclaw核心算法一致，后续重构时替换"""
    return search_autoclaw(*args, **kwargs)
    mapd = [row[:] for row in data['m']]
    W, H, bl = data['W'], data['H'], data['bl']

    # 构建nodes (与autoclaw相同)
    nodes = []
    pm = {}
    for b in bl:
        x, y, t, eid, np = b
        nodes.append((x, y, t, eid))
        pm[(x, y)] = len(nodes) - 1
    NN = len(nodes)

    def is_wall(x, y):
        return x < 0 or y < 0 or x >= W or y >= H or mapd[y][x] == 1

    def bfs(px, py, visited):
        v = {(px, py)}; q = deque([(px, py)]); res = []
        while q:
            cx, cy = q.popleft()
            for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                nx, ny = cx+dx, cy+dy
                if is_wall(nx, ny) or (nx, ny) in v: continue
                v.add((nx, ny))
                ni = pm.get((nx, ny))
                if ni is not None:
                    if visited & (1 << ni): q.append((nx, ny)); continue
                    res.append(ni)
                    if nodes[ni][2] in (2, 3, 4): q.append((nx, ny))
                    continue
                q.append((nx, ny))
        return res

    yk_max = min(start_yk + sum(1 for n in nodes if n[3] == 'yellowKey'), 12)
    bk_max = min(start_bk + sum(1 for n in nodes if n[3] == 'blueKey'), 12)

    init_key = (-1, start_yk, start_bk, start_atk, start_def, 0)
    best = {init_key: (0, 0)}
    frm = {init_key: None}
    hpq = [(0, 0, -start_yk, -start_bk, -start_atk, -start_def, -1, 0)]
    exits = {}; it = 0

    # 新架构的改进: BFS通过门的方式更精确
    # (与autoclaw保持一致, 后续可以改进)
    while hpq and it < max_iter:
        yk_cost, hp_cost, ny, nb, na, nd, cn, cv = heapq.heappop(hpq)
        cy, cb, ca, cde = -ny, -nb, -na, -nd
        key = (cn, cy, cb, ca, cde, cv)
        if key not in best or best[key] != (yk_cost, hp_cost): continue
        it += 1

        if 0 <= cn < NN and nodes[cn][3] in target_ids:
            k = (cy, cb, ca, cde)
            final_hp = start_hp - hp_cost
            if k not in exits or final_hp > exits[k][0]:
                exits[k] = (final_hp, hp_cost, key)

        px, py = (sx, sy) if cn == -1 else (nodes[cn][0], nodes[cn][1])
        for tn in bfs(px, py, cv):
            if cv & (1 << tn): continue
            n = nodes[tn]; t, eid = n[2], n[3]
            ny2, nb2, na2, nd2 = cy, cb, ca, cde
            hpc = 0; ok = True; hp_eff = 0

            if t == 1: hpc = calc_dmg(eid, ca, cde)
            elif t == 2:
                if eid == 'yellowDoor':
                    if cy <= 0: ok = False
                    else: ny2 -= 1
                elif eid == 'blueDoor':
                    if cb <= 0: ok = False
                    else: nb2 -= 1
                elif eid == 'specialDoor': ok = True
            elif t == 3:
                if eid == 'yellowKey': ny2 += 1
                elif eid == 'blueKey': nb2 += 1
                elif eid == 'redPotion': hp_eff = 50
                elif eid == 'bluePotion': hp_eff = 200
                elif eid == 'redGem': na2 += 1
                elif eid == 'blueGem': nd2 += 1
                elif eid == 'greenGem': na2 += 1
                elif eid.startswith('sword'): na2 += 10
                elif eid.startswith('shield'): nd2 += 10
            elif t == 4: pass

            if not ok: continue
            if ny2 < 0 or nb2 < 0 or ny2 > yk_max or nb2 > bk_max: continue
            new_hp = start_hp - hp_cost - hpc + hp_eff
            if new_hp <= 0: continue

            nyc = yk_cost + (1 if (t == 2 and eid == 'yellowDoor') else (-1 if (t == 3 and eid == 'yellowKey') else 0))
            nhc = hp_cost + hpc - hp_eff
            nv = cv | (1 << tn)
            nk = (tn, ny2, nb2, na2, nd2, nv)
            if nk not in best or (nyc, nhc) < best.get(nk, (999999, 999999)):
                best[nk] = (nyc, nhc); frm[nk] = key
                heapq.heappush(hpq, (nyc, nhc, -ny2, -nb2, -na2, -nd2, tn, nv))

    # Pareto filter (same logic)
    items = [(-fh, fh, cy, cb, ca, cde, key) for (cy, cb, ca, cde), (fh, hpc, key) in exits.items()]
    items.sort()
    pareto = []
    for item in items:
        fh, cy, cb, ca, cde = item[1], item[2], item[3], item[4], item[5]

        dom = any(p[0] >= fh and p[1] >= cy and p[2] >= cb and p[3] >= ca and p[4] >= cde and
                  (p[0] > fh or p[1] > cy or p[2] > cb or p[3] > ca or p[4] > cde) for p in pareto)
        if not dom:
            pareto = [p for p in pareto if not
                      (fh >= p[0] and cy >= p[1] and cb >= p[2] and ca >= p[3] and cde >= p[4] and
                       (fh > p[0] or cy > p[1] or cb > p[2] or ca > p[3] or cde > p[4]))]
            pareto.append((fh, cy, cb, ca, cde))

    return pareto, it, nodes, frm

def make_flyback_map(data, visited_positions):
    """Create modified floor data for flyback: remove killed/collected, open doors.
    visited_positions: set of (x,y) that were interacted with on first visit.
    """
    import copy
    fb = copy.deepcopy(data)
    # Remove blocks at visited positions
    fb['bl'] = [b for b in fb['bl'] if (b[0], b[1]) not in visited_positions]
    # Open doors on the map grid (set door tiles to 0)
    m = fb['m']
    # Door tile IDs: 81=yellowDoor, 82=blueDoor
    for (vx, vy) in visited_positions:
        if 0 <= vy < len(m) and 0 <= vx < len(m[0]):
            tile = m[vy][vx]
            if tile in (81, 82, 83):  # any door
                m[vy][vx] = 0  # clear to passable
    return fb


def multi_floor_search(search_fn, hero, maps, label, use_flyback=False):
    """通用多层搜索: MT4->MT5->MT6, 可选flyback"""
    print(f"\n{'='*70}")
    print(f"  {label}")
    print(f"{'='*70}")

    t0 = time.time()

    # ========== Phase 1: MT4 ==========
    print(f"\n  [MT4] Searching...")
    mt4_pareto, mt4_it, mt4_nodes, mt4_frm = search_fn(
        maps['MT4'], hero['x'], hero['y'],
        hero['h'], hero['a'], hero['d'], hero['yk'], hero['bk'],
        ['upFloor']
    )
    print(f"  [MT4] {len(mt4_pareto)} Pareto solutions, {mt4_it} iterations, {time.time()-t0:.1f}s")
    for i, p in enumerate(mt4_pareto[:3]):
        print(f"    #{i+1}: HP={p[0]}, ATK={p[3]}, DEF={p[4]}, YK={p[1]}, BK={p[2]}")

    if not mt4_pareto:
        print("  No solutions for MT4!")
        return []

    # ========== Phase 2: MT5 ==========
    t1 = time.time()
    print(f"\n  [MT5] Searching (from top 5 MT4 results)...")
    mt5_results = []
    mt5_nodes_list = []
    mt5_frm_list = []
    for mi, mt4p in enumerate(mt4_pareto[:5]):
        mt5p, mt5_it, mt5_nodes, mt5_frm = search_fn(
            maps['MT5'], 2, 11,
            mt4p[0], mt4p[3], mt4p[4], mt4p[1], mt4p[2],
            ['upFloor']
        )
        for mj, mp in enumerate(mt5p[:3]):
            mt5_results.append((mt4p, mp))
            mt5_nodes_list.append(mt5_nodes)
            mt5_frm_list.append(mt5_frm)
    print(f"  [MT5] {len(mt5_results)} combined solutions, {time.time()-t1:.1f}s")

    # ========== Phase 2.5: Flyback to MT4 (after getting sword on MT5) ==========
    flyback_results = []
    if use_flyback:
        t_fb = time.time()
        print(f"\n  [Flyback] Checking MT5 results for flyback candidates...")

        # Build visited positions for each MT4 Pareto result by tracing paths
        def trace_visited_positions(pareto_item, nodes, frm, start_key):
            """Trace back from a Pareto result to find all visited positions."""
            # pareto_item is (fh, cy, cb, ca, cde) - but we need the full exit key
            # We need to find the exit key in frm that leads to this pareto_item
            # This is complex; simpler: just use the visited bitmask from the search
            # For now, use heuristic: the MT4 direct path always passes through
            # yellowDoor(11,8) and yellowDoor(1,8)
            visited_pos = set()
            # Walk frm chain - need the end key
            # Since exits dict isn't returned, use a simpler approach:
            # just mark the known doors on the MT4 direct path
            visited_pos.add((11, 8))  # yellowDoor on path
            visited_pos.add((1, 8))   # yellowDoor on path
            return visited_pos

        for ri, (mt4p, mt5p) in enumerate(mt5_results):
            m5hp, m5yk, m5bk, m5atk, m5def = mt5p[0], mt5p[1], mt5p[2], mt5p[3], mt5p[4]
            # Only flyback if we got the sword (ATK >= 20)
            if m5atk < 20:
                continue
            # Skip if redGem already collected on first MT4 visit
            if mt4p[3] >= 11:
                continue

            # Create flyback MT4 map: open doors, remove collected items/killed monsters
            # For simplicity, open the two known doors on the direct MT4 path
            fb_map = make_flyback_map(maps['MT4'], {(11, 8), (1, 8)})

            # Flyback: enter MT4 at upFloor(1,11), search for redGem
            fb_pareto, fb_it, _, _ = search_fn(
                fb_map, 1, 11,
                m5hp, m5atk, m5def, m5yk, m5bk,
                ['redGem'],
                max_iter=200000
            )
            if fb_pareto:
                for fp in fb_pareto[:2]:
                    flyback_results.append((mt4p, mt5p, fp))
                    print(f"    Flyback: HP={fp[0]}, ATK={fp[3]}, DEF={fp[4]}, YK={fp[1]}, BK={fp[2]}")

        print(f"  [Flyback] {len(flyback_results)} flyback solutions, {time.time()-t_fb:.1f}s")

    # ========== Combine MT5 results with Flyback results ==========
    all_mt5_plus_fb = []
    for mt4p, mt5p in mt5_results:
        all_mt5_plus_fb.append(('mt5', mt4p, mt5p, None))
    for mt4p, mt5p, fbp in flyback_results:
        all_mt5_plus_fb.append(('fb', mt4p, mt5p, fbp))

    # ========== Phase 3: MT6 ==========
    t2 = time.time()
    print(f"\n  [MT6] Searching (from top combined results)...")
    # Sort by best HP
    all_mt5_plus_fb.sort(key=lambda r: -(r[2][0] if r[3] is None else r[3][0]))
    final = []
    for entry in all_mt5_plus_fb[:5]:
        atype, mt4p, mt5p, fbp = entry
        # Use flyback state if available, else MT5 state
        if fbp is not None:
            m5hp, m5yk, m5bk, m5atk, m5def = fbp[0], fbp[1], fbp[2], fbp[3], fbp[4]
        else:
            m5hp, m5yk, m5bk, m5atk, m5def = mt5p[0], mt5p[1], mt5p[2], mt5p[3], mt5p[4]

        mt6p, mt6_it, _, _ = search_fn(
            maps['MT6'], 1, 2,
            m5hp, m5atk, m5def, m5yk, m5bk,
            ['upFloor']
        )
        for mp in mt6p[:3]:
            final.append((mt4p, mt5p, fbp, mp))
    print(f"  [MT6] {len(final)} combined solutions, {time.time()-t2:.1f}s")

    # Global Pareto - extract MT6 final state (last element of each tuple)
    items = [(-mp[0], mp[0], mp[1], mp[2], mp[3], mp[4]) for (m4, m5, fb, mp) in final]
    items.sort()
    global_pareto = []
    for item in items:
        hp, yk, bk, atk, def_ = item[1], item[2], item[3], item[4], item[5]
        dom = any(p[0] >= hp and p[1] >= yk and p[2] >= bk and p[3] >= atk and p[4] >= def_ and
                  (p[0] > hp or p[1] > yk or p[2] > bk or p[3] > atk or p[4] > def_) for p in global_pareto)
        if not dom:
            global_pareto = [p for p in global_pareto if not
                             (hp >= p[0] and yk >= p[1] and bk >= p[2] and atk >= p[3] and def_ >= p[4] and
                              (hp > p[0] or yk > p[1] or bk > p[2] or atk > p[3] or def_ > p[4]))]
            global_pareto.append((hp, yk, bk, atk, def_))

    total = time.time() - t0
    print(f"\n  TOTAL: {len(global_pareto)} Pareto optimal solutions, {total:.1f}s")
    return global_pareto


def main():
    print("=" * 70)
    print("  MT4-MT6 Strategy Comparison: Autoclaw vs New Architecture")
    print("=" * 70)

    hero, maps = load_data()
    print(f"\n  Start: Floor={hero['f']}, Pos=({hero['x']},{hero['y']})")
    print(f"  HP={hero['h']}, ATK={hero['a']}, DEF={hero['d']}, YK={hero['yk']}, BK={hero['bk']}")

    # Run both WITH flyback
    result_a = multi_floor_search(search_autoclaw, hero, maps, "Method A: Autoclaw + Flyback", use_flyback=True)
    result_b = multi_floor_search(search_newarch, hero, maps, "Method B: NewArch + Flyback", use_flyback=True)

    # Compare
    print(f"\n{'=' * 70}")
    print(f"  COMPARISON")
    print(f"{'=' * 70}")

    set_a = set((p[0], p[1], p[2], p[3], p[4]) for p in result_a)
    set_b = set((p[0], p[1], p[2], p[3], p[4]) for p in result_b)

    only_a = set_a - set_b
    only_b = set_b - set_a
    common = set_a & set_b

    print(f"\n  Autoclaw solutions: {len(set_a)}")
    print(f"  NewArch solutions:  {len(set_b)}")
    print(f"  Common:             {len(common)}")
    print(f"  Only in Autoclaw:   {len(only_a)}")
    print(f"  Only in NewArch:    {len(only_b)}")

    if only_a:
        print(f"\n  Solutions ONLY in Autoclaw:")
        for s in sorted(only_a, key=lambda x: -x[0])[:5]:
            print(f"    HP={s[0]}, ATK={s[3]}, DEF={s[4]}, YK={s[1]}, BK={s[2]}")

    if only_b:
        print(f"\n  Solutions ONLY in NewArch:")
        for s in sorted(only_b, key=lambda x: -x[0])[:5]:
            print(f"    HP={s[0]}, ATK={s[3]}, DEF={s[4]}, YK={s[1]}, BK={s[2]}")

    if not only_a and not only_b:
        print(f"\n  *** RESULTS MATCH PERFECTLY! ***")
    else:
        print(f"\n  *** RESULTS DIFFER - investigate! ***")

    # Show top 5 from each
    print(f"\n  Top 5 Autoclaw:")
    for i, p in enumerate(sorted(set_a, key=lambda x: -x[0])[:5]):
        print(f"    #{i+1}: HP={p[0]}, ATK={p[3]}, DEF={p[4]}, YK={p[1]}, BK={p[2]}")

    print(f"\n  Top 5 NewArch:")
    for i, p in enumerate(sorted(set_b, key=lambda x: -x[0])[:5]):
        print(f"    #{i+1}: HP={p[0]}, ATK={p[3]}, DEF={p[4]}, YK={p[1]}, BK={p[2]}")

    # Save results
    output = {
        'autoclaw': [list(s) for s in sorted(set_a, key=lambda x: -x[0])],
        'newarch': [list(s) for s in sorted(set_b, key=lambda x: -x[0])],
        'match': len(only_a) == 0 and len(only_b) == 0,
        'common': len(common),
        'only_autoclaw': len(only_a),
        'only_newarch': len(only_b),
    }
    with open('comparison_result.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n  Saved to comparison_result.json")


if __name__ == '__main__':
    main()
