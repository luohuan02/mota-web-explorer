#!/usr/bin/env python3
"""
MT4-MT6 Pareto搜索 + Flyback 对比
与autoclaw的mt456_pareto.py完全一致的搜索逻辑
"""
# Allow scripts to import project-root modules after being moved under scripts/.
import os as _codex_os
import sys as _codex_sys
_codex_root = _codex_os.path.dirname(_codex_os.path.dirname(_codex_os.path.abspath(__file__)))
if _codex_root not in _codex_sys.path:
    _codex_sys.path.insert(0, _codex_root)

import json, math, heapq, time, os, copy
from collections import deque

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

EM = {
    'greenSlime': (35,18,1), 'redSlime': (45,20,2), 'bat': (35,38,3),
    'skeleton': (50,42,6), 'skeletonSoldier': (55,52,12),
    'skeletonCaptain': (100,65,15), 'bluePriest': (60,32,8),
    'blueGuard': (100,180,110), 'yellowGuard': (50,48,22),
    'soldier': (210,200,65),
}

def calc_dmg(eid, atk, def_):
    e = EM.get(eid, (100,100,0))
    m = atk - e[2]
    if m <= 0:
        return float('inf')  # 无法破防，游戏返回null
    n = max(0, e[1] - def_)  # 游戏公式：per_damage可为0
    r = -(-e[0] // m)
    return (r - 1) * n

def load_data():
    def data_path(name):
        return os.path.join('data', 'maps', name)

    hero = json.load(open(data_path('hero_state.json'), encoding='utf-8'))
    maps = {}
    for fid in ['mt1', 'mt3', 'mt4', 'mt5', 'mt6', 'mt7', 'mt8', 'mt9']:
        raw = json.load(open(data_path(f'{fid}_map.json'), encoding='utf-8'))
        blocks = []
        for b in raw['bl']:
            eid, cls = b['id'], b['cls']
            t = 0
            if eid in ('upFloor', 'downFloor', 'fakeWall'): t = 4
            elif cls == 'enemys' or eid in EM: t = 1
            elif eid.endswith('Door'): t = 2
            elif cls == 'items': t = 3
            elif cls == 'animates' and (eid.endswith('Key') or eid.endswith('Potion') or eid.endswith('Gem') or eid.startswith('sword') or eid.startswith('shield')): t = 3
            if t > 0:
                blocks.append((b['x'], b['y'], t, eid, False))
        maps[fid.upper()] = {'W': raw['w'], 'H': raw['h'], 'm': raw['m'], 'bl': blocks}
    return hero, maps

def search(data, sx, sy, start_hp, start_atk, start_def, start_yk, start_bk, target_ids, max_iter=500000):
    """Pareto Dijkstra搜索 (与autoclaw run_floor一致)"""
    mapd = [row[:] for row in data['m']]
    W, H, bl = data['W'], data['H'], data['bl']
    nodes = []; pm = {}; np_set = set()
    for b in bl:
        x, y, t, eid, np = b
        if np: np_set.add((x, y))
        nodes.append((x, y, t, eid)); pm[(x, y)] = len(nodes) - 1
    NN = len(nodes)

    def is_wall(x, y):
        return x <= 0 or y <= 0 or x >= W-1 or y >= H-1 or mapd[y][x] == 1

    def bfs(px, py, vm):
        v = {(px, py)}; q = deque([(px, py)]); r = []
        while q:
            cx, cy = q.popleft()
            for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                nx, ny = cx+dx, cy+dy
                if is_wall(nx, ny) or (nx, ny) in v: continue
                v.add((nx, ny))
                ni = pm.get((nx, ny))
                if ni is not None:
                    if vm & (1 << ni): q.append((nx, ny)); continue
                    r.append(ni)
                    if nodes[ni][2] in (3, 4): q.append((nx, ny))
                    continue
                if (nx, ny) in np_set: continue
                q.append((nx, ny))
        return r

    yk_max = min(start_yk + sum(1 for n in nodes if n[3] == 'yellowKey'), 12)
    bk_max = min(start_bk + sum(1 for n in nodes if n[3] == 'blueKey'), 12)

    init = (-1, start_yk, start_bk, start_atk, start_def, 0)
    best = {init: 0}
    frm = {init: None}
    hpq = [(0, -start_yk, -start_bk, -start_atk, -start_def, -1, 0)]
    exits = {}; it = 0

    while hpq and it < max_iter:
        hs, my, mb, ma, md, cn, cv = heapq.heappop(hpq)
        cy, cb, ca, cde = -my, -mb, -ma, -md
        ck = (cn, cy, cb, ca, cde, cv)
        if ck not in best or best[ck] != hs: continue
        it += 1

        if 0 <= cn < NN and nodes[cn][3] in target_ids:
            key = (cy, cb, ca, cde)
            if key not in exits or hs < exits[key][0]:
                exits[key] = (hs, ck)

        if cn == -1: px, py = sx, sy
        else: px, py = nodes[cn][0], nodes[cn][1]
        reachable = bfs(px, py, cv)

        for tn in reachable:
            if cv & (1 << tn): continue
            n = nodes[tn]; t, eid = n[2], n[3]
            ny, nb, na, nd = cy, cb, ca, cde
            hp_cost = 0; hp_eff = 0; ok = True

            if t == 1:
                dmg = calc_dmg(eid, ca, cde)
                hp_cost = dmg; hp_eff = -dmg
            elif t == 2:
                if eid == 'yellowDoor':
                    if cy <= 0: ok = False
                    else: ny = cy - 1
                elif eid == 'blueDoor':
                    if cb <= 0: ok = False
                    else: nb = cb - 1
                elif eid == 'specialDoor': ok = True
            elif t == 3:
                if eid == 'yellowKey': ny = cy + 1
                elif eid == 'blueKey': nb = cb + 1
                elif eid == 'redPotion': hp_eff = 50
                elif eid == 'bluePotion': hp_eff = 200
                elif eid == 'redGem': na = ca + 1
                elif eid == 'blueGem': nd = cde + 1
                elif eid == 'greenGem': na = ca + 1
                elif eid.startswith('sword'): na = ca + 10
                elif eid.startswith('shield'): nd = cde + 10
            elif t == 4: pass

            if not ok: continue
            if ny < 0 or nb < 0 or ny > yk_max or nb > bk_max: continue

            new_hp = start_hp - hs + hp_eff
            if new_hp <= 0: continue

            nhs = hs - hp_eff
            nv = cv | (1 << tn)
            nk = (tn, ny, nb, na, nd, nv)

            if nk not in best or nhs < best[nk]:
                best[nk] = nhs; frm[nk] = ck
                heapq.heappush(hpq, (nhs, -ny, -nb, -na, -nd, tn, nv))

    # Pareto filter
    items = []
    for key, (hs, ck) in exits.items():
        yk, bk, atk, dfn = key
        actual_hp = start_hp - hs
        items.append((actual_hp, yk, bk, atk, dfn, hs, ck))

    items.sort(key=lambda x: -x[0])
    pareto = []
    for item in items:
        hp, yk, bk, atk, dfn = item[:5]
        dom = any(p[0] >= hp and p[1] >= yk and p[2] >= bk and p[3] >= atk and p[4] >= dfn and
                  (p[0] > hp or p[1] > yk or p[2] > bk or p[3] > atk or p[4] > dfn) for p in pareto)
        if not dom:
            pareto = [p for p in pareto if not (hp >= p[0] and yk >= p[1] and bk >= p[2] and atk >= p[3] and dfn >= p[4] and
                     (hp > p[0] or yk > p[1] or bk > p[2] or atk > p[3] or dfn > p[4]))]
            pareto.append(item)  # Keep full 7-tuple for trace_ops

    return pareto, it, nodes, frm

def trace_ops(pareto_item, nodes, frm, start_hp, start_yk, start_bk, start_atk, start_def, fid):
    """Trace path and build operation list (与autoclaw一致)"""
    ck = pareto_item[6]
    path = []; k = ck; safety = 0
    while k is not None and safety < 100:
        path.append(k); k = frm.get(k); safety += 1
    path.reverse()

    chp, cyk, cbk, catk, cdfn = start_hp, start_yk, start_bk, start_atk, start_def
    ops = []
    for pp in path:
        ni2, y2, b2, a2, d2, v2 = pp
        if ni2 == -1: continue
        n2 = nodes[ni2]
        ohp, oyk, obk = chp, cyk, cbk
        if n2[2] == 1: chp -= calc_dmg(n2[3], catk, cdfn)
        elif n2[3] == 'yellowDoor': cyk -= 1
        elif n2[3] == 'blueDoor': cbk -= 1
        elif n2[3] == 'yellowKey': cyk += 1
        elif n2[3] == 'blueKey': cbk += 1
        elif n2[3] == 'redPotion': chp += 50
        elif n2[3] == 'bluePotion': chp += 200
        elif n2[3] == 'redGem': catk += 1
        elif n2[3] == 'blueGem': cdfn += 1
        elif n2[3] == 'greenGem': catk += 1
        elif n2[3] == 'sword1': catk += 10
        elif n2[3].startswith('sword'): catk += 10
        ops.append((fid, n2[0], n2[1], n2[3], ohp, oyk, obk, chp, cyk, cbk))
    return ops

def make_flyback_data(data, first_visit_ops, nodes):
    """Create modified floor data for flyback"""
    fb = copy.deepcopy(data)
    m = fb['m']

    # Collect positions of visited entities
    collected_positions = set()
    for op in first_visit_ops:
        ox, oy = op[1], op[2]
        collected_positions.add((ox, oy))

    # Remove killed/collected blocks
    fb['bl'] = [b for b in fb['bl'] if (b[0], b[1]) not in collected_positions]

    # Open consumed doors (doors that were in the ops list = keys were spent)
    for op in first_visit_ops:
        ox, oy, eid = op[1], op[2], op[3]
        if eid.endswith('Door') and 0 <= oy < len(m) and 0 <= ox < len(m[0]):
            if m[oy][ox] in (81, 82):  # yellowDoor or blueDoor
                m[oy][ox] = 0

    # Also open doors adjacent to visited path (for doors near but not in ops)
    visited_positions = {(op[1], op[2]) for op in first_visit_ops}
    visited_positions.add((11, 10))  # MT4 start position

    for y in range(len(m)):
        for x in range(len(m[0])):
            if m[y][x] not in (81, 82): continue
            for vx, vy in visited_positions:
                if abs(vx - x) + abs(vy - y) == 1:
                    m[y][x] = 0
                    break

    return fb

def score_flyback_target(item_id, current_atk, current_def, future_enemies):
    """阶跃收益评分: flyback拿这个物品能省多少HP"""
    score = 0
    if item_id == 'redGem':
        for (hp, atk, def_) in future_enemies:
            cost_old = (math.ceil(hp / max(1, current_atk - def_)) - 1) * max(1, atk - current_def)
            cost_new = (math.ceil(hp / max(1, current_atk + 1 - def_)) - 1) * max(1, atk - current_def)
            score += cost_old - cost_new
    elif item_id == 'blueGem':
        for (hp, atk, def_) in future_enemies:
            cost_old = (math.ceil(hp / max(1, current_atk - def_)) - 1) * max(1, atk - current_def)
            cost_new = (math.ceil(hp / max(1, current_atk - def_)) - 1) * max(1, atk - (current_def + 1))
            score += cost_old - cost_new
    elif item_id == 'bluePotion': score = 200
    elif item_id == 'redPotion': score = 50
    elif item_id.endswith('Key'): score = 30
    return score

def get_future_enemies(maps, floor_ids):
    enemies = []
    for fid in floor_ids:
        if fid not in maps: continue
        for b in maps[fid]['bl']:
            if b[2] == 1:
                e = EM.get(b[3])
                if e: enemies.append(e)
    return enemies

def find_flyback_targets(floor_data, current_atk, current_def, future_enemies, min_score=20):
    targets = []
    for b in floor_data['bl']:
        eid = b[3]
        if b[2] != 3: continue
        if eid in ('yellowKey', 'blueKey'): continue
        score = score_flyback_target(eid, current_atk, current_def, future_enemies)
        if score >= min_score:
            targets.append((b[0], b[1], eid, score))
    targets.sort(key=lambda x: -x[3])
    return targets

def pareto_filter(items_5d):
    items_5d.sort(key=lambda x: -x[0])
    pareto = []
    for item in items_5d:
        hp, yk, bk, atk, def_ = item
        dom = any(p[0] >= hp and p[1] >= yk and p[2] >= bk and p[3] >= atk and p[4] >= def_ and
                  (p[0] > hp or p[1] > yk or p[2] > bk or p[3] > atk or p[4] > def_) for p in pareto)
        if not dom:
            pareto = [p for p in pareto if not (hp >= p[0] and yk >= p[1] and bk >= p[2] and atk >= p[3] and def_ >= p[4] and
                     (hp > p[0] or yk > p[1] or bk > p[2] or atk > p[3] or def_ > p[4]))]
            pareto.append(item)
    return pareto

def main():
    print("=" * 70)
    print("  MT4-MT6 Pareto Search + Flyback")
    print("=" * 70)

    hero, maps = load_data()
    print(f"\n  Start: Floor={hero['f']}, Pos=({hero['x']},{hero['y']})")
    print(f"  HP={hero['h']}, ATK={hero['a']}, DEF={hero['d']}, YK={hero['yk']}, BK={hero['bk']}")

    future_enemies = get_future_enemies(maps, ['MT6', 'MT7', 'MT8'])
    t_start = time.time()

    # ========== Phase 1: MT4 ==========
    print(f"\n  [MT4] Searching...")
    mt4_pareto, mt4_it, mt4_nodes, mt4_frm = search(
        maps['MT4'], hero['x'], hero['y'],
        hero['h'], hero['a'], hero['d'], hero['yk'], hero['bk'], ['upFloor'])
    print(f"  [MT4] {len(mt4_pareto)} Pareto, {mt4_it} iters, {time.time()-t_start:.1f}s")
    for i, p in enumerate(mt4_pareto[:5]):
        print(f"    #{i+1}: HP={p[0]}, ATK={p[3]}, DEF={p[4]}, YK={p[1]}, BK={p[2]}")
    if not mt4_pareto:
        print("  No solutions!"); return

    # ========== Phase 2: MT5 ==========
    t1 = time.time()
    print(f"\n  [MT5] Searching (from top 5 MT4)...")
    mt5_results = []
    for mi, mt4p in enumerate(mt4_pareto[:5]):
        m4hp, m4yk, m4bk, m4atk, m4def = mt4p[0], mt4p[1], mt4p[2], mt4p[3], mt4p[4]
        mt4_ops = trace_ops(mt4p, mt4_nodes, mt4_frm, hero['h'], hero['yk'], hero['bk'], hero['a'], hero['d'], 'MT4')
        print(f"  MT4#{mi+1} ops: {len(mt4_ops)} steps, collected: {[op[3] for op in mt4_ops]}")
        mt5p, mt5_it, mt5_nodes, mt5_frm = search(
            maps['MT5'], 2, 11, m4hp, m4atk, m4def, m4yk, m4bk, ['upFloor'])
        print(f"  MT4#{mi+1} -> MT5: {len(mt5p)} Pareto, {mt5_it} iters")
        for mj, mp in enumerate(mt5p[:5]):
            mt5_ops = trace_ops(mp, mt5_nodes, mt5_frm, m4hp, m4yk, m4bk, m4atk, m4def, 'MT5')
            mt5_results.append({
                'mt4_idx': mi, 'mt4_ops': mt4_ops,
                'mt5_idx': mj, 'mt5_ops': mt5_ops,
                'hp': mp[0], 'yk': mp[1], 'bk': mp[2], 'atk': mp[3], 'def': mp[4]
            })
    print(f"  [MT5] {len(mt5_results)} total, {time.time()-t1:.1f}s")

    # ========== Phase 2.5: Flyback ==========
    t_fb = time.time()
    print(f"\n  [Flyback] Analyzing candidates...")
    flyback_results = []

    for ri, mr in enumerate(mt5_results):
        m5hp, m5yk, m5bk, m5atk, m5def = mr['hp'], mr['yk'], mr['bk'], mr['atk'], mr['def']
        if m5atk < 20: continue  # Need sword for flyback to be worthwhile

        # Check if redGem already collected
        redgem_collected = any(op[3] == 'redGem' for op in mr['mt4_ops'])
        if redgem_collected: continue

        # Create flyback floor data
        fb_data = make_flyback_data(maps['MT4'], mr['mt4_ops'], mt4_nodes)

        # Use stepwise scoring to find flyback targets
        targets = find_flyback_targets(fb_data, m5atk, m5def, future_enemies, min_score=20)
        if not targets: continue

        for tx, ty, tid, tscore in targets[:3]:
            fb_pareto, fb_it, fb_nodes, fb_frm = search(
                fb_data, 1, 11, m5hp, m5atk, m5def, m5yk, m5bk, [tid], max_iter=200000)
            if not fb_pareto: continue

            print(f"    MT5#{ri} -> MT4fb {tid}: score={tscore}, HP={fb_pareto[0][0]}, ATK={fb_pareto[0][3]}")

            for fj, fp in enumerate(fb_pareto[:2]):
                fb_ops = trace_ops(fp, fb_nodes, fb_frm, m5hp, m5yk, m5bk, m5atk, m5def, 'MT4fb')
                flyback_results.append({
                    'mt4_idx': mr['mt4_idx'], 'mt4_ops': mr['mt4_ops'],
                    'mt5_idx': mr['mt5_idx'], 'mt5_ops': mr['mt5_ops'],
                    'flyback_ops': fb_ops,
                    'hp': fp[0], 'yk': fp[1], 'bk': fp[2], 'atk': fp[3], 'def': fp[4]
                })

    # Deduplicate flyback results
    fb_seen = {}
    for fr in flyback_results:
        key = (fr['atk'], fr['def'], fr['yk'], fr['bk'])
        if key not in fb_seen or fr['hp'] > fb_seen[key]['hp']:
            fb_seen[key] = fr
    flyback_results = list(fb_seen.values())

    print(f"  [Flyback] {len(flyback_results)} solutions, {time.time()-t_fb:.1f}s")

    # ========== Phase 3: MT6 ==========
    t2 = time.time()
    mt6_data = maps['MT6']

    # Combine regular MT5 + flyback results
    mt5_sorted = sorted(mt5_results, key=lambda x: x['hp'], reverse=True)[:3]
    flyback_viable = [fr for fr in flyback_results if fr['hp'] >= 300]

    all_entries = []
    for ri, mr in enumerate(mt5_sorted):
        all_entries.append(('mt5', ri, mr))
    for fi, fr in enumerate(flyback_viable):
        all_entries.append(('fb', fi, fr))

    print(f"\n  [MT6] Searching (from {len(all_entries)} entries)...")

    mt6_results = []
    for ai, (atype, aidx, ar) in enumerate(all_entries):
        m5hp, m5yk, m5bk, m5atk, m5def = ar['hp'], ar['yk'], ar['bk'], ar['atk'], ar['def']
        label = f'{atype.upper()}#{aidx}'

        mt6p, mt6_it, mt6_nodes, mt6_frm = search(
            mt6_data, 1, 2, m5hp, m5atk, m5def, m5yk, m5bk, ['upFloor'], max_iter=200000)

        if not mt6p:
            print(f"  {label} -> MT6: NO PATH")
            continue

        print(f"  {label} (HP={m5hp},ATK={m5atk},YK={m5yk}) -> MT6: {len(mt6p)} Pareto, {mt6_it} iters")

        for mk, mp in enumerate(mt6p[:3]):
            mt6_ops = trace_ops(mp, mt6_nodes, mt6_frm, m5hp, m5yk, m5bk, m5atk, m5def, 'MT6')
            fb_ops = ar.get('flyback_ops', [])
            mt6_results.append({
                'mt4_ops': ar['mt4_ops'], 'mt5_ops': ar['mt5_ops'],
                'flyback_ops': fb_ops, 'mt6_ops': mt6_ops,
                'final_hp': mp[0], 'final_yk': mp[1], 'final_bk': mp[2],
                'final_atk': mp[3], 'final_def': mp[4]
            })

    # Global Pareto
    final_items = [(r['final_hp'], r['final_yk'], r['final_bk'], r['final_atk'], r['final_def']) for r in mt6_results]
    global_pareto = pareto_filter(final_items)

    total = time.time() - t_start
    print(f"\n{'='*70}")
    print(f"  RESULTS ({total:.1f}s total)")
    print(f"{'='*70}")
    for i, p in enumerate(global_pareto):
        print(f"  #{i+1}: HP={p[0]}, ATK={p[3]}, DEF={p[4]}, YK={p[1]}, BK={p[2]}")

    # Also print flyback vs non-flyback comparison
    fb_final = [r for r in mt6_results if r.get('flyback_ops')]
    nofb_final = [r for r in mt6_results if not r.get('flyback_ops')]
    if fb_final:
        best_fb = max(fb_final, key=lambda r: r['final_hp'])
        print(f"\n  Best with Flyback: HP={best_fb['final_hp']}, ATK={best_fb['final_atk']}, DEF={best_fb['final_def']}")
    if nofb_final:
        best_nf = max(nofb_final, key=lambda r: r['final_hp'])
        print(f"  Best without Flyback: HP={best_nf['final_hp']}, ATK={best_nf['final_atk']}, DEF={best_nf['final_def']}")

    # Save
    output = {
        'total_time': total,
        'solutions': [{'rank': i+1, 'hp': p[0], 'yk': p[1], 'bk': p[2], 'atk': p[3], 'def': p[4]} for i, p in enumerate(global_pareto)]
    }
    with open('comparison_result.json', 'w') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\n  Saved to comparison_result.json")

if __name__ == '__main__':
    main()
