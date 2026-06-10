#!/usr/bin/env python3
"""追踪具体路径看ATK增长"""
# Allow scripts to import project-root modules after being moved under scripts/.
import os as _codex_os
import sys as _codex_sys
_codex_root = _codex_os.path.dirname(_codex_os.path.dirname(_codex_os.path.abspath(__file__)))
if _codex_root not in _codex_sys.path:
    _codex_sys.path.insert(0, _codex_root)

import json, heapq, os
from collections import deque

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MAP_DIR = os.path.join('data', 'maps')

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
        return float('inf')
    n = max(0, e[1] - def_)
    r = -(-e[0] // m)
    return (r - 1) * n

def load_map(fid):
    raw = json.load(open(os.path.join(MAP_DIR, f'{fid}_map.json'), encoding='utf-8'))
    blocks = []
    for b in raw['bl']:
        if isinstance(b, dict):
            x, y, eid = b['x'], b['y'], b['id']
            cls = b.get('cls', '')
        else:
            x, y, _, eid, _ = b
            cls = ''
        t = 0
        if eid in ('upFloor', 'downFloor', 'fakeWall'): t = 4
        elif cls == 'monsters' or cls == 'enemys' or eid in EM: t = 1
        elif eid.endswith('Door'): t = 2
        elif cls == 'items' or eid.endswith('Key') or eid.endswith('Potion') or eid.endswith('Gem') or eid.startswith('sword') or eid.startswith('shield'): t = 3
        elif cls == 'animates' and (eid.endswith('Key') or eid.endswith('Potion') or eid.endswith('Gem') or eid.startswith('sword') or eid.startswith('shield')): t = 3
        if t > 0:
            blocks.append((x, y, t, eid))
    W = raw.get('W', raw.get('w', 13))
    H = raw.get('H', raw.get('h', 13))
    return {'W': W, 'H': H, 'm': raw['m'], 'bl': blocks}

def search(data, sx, sy, start_hp, start_atk, start_def, start_yk, start_bk, target_ids, max_iter=200000):
    mapd = [row[:] for row in data['m']]
    W, H, bl = data['W'], data['H'], data['bl']
    nodes = []; pm = {}
    for b in bl:
        x, y, t, eid = b
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
            hp_eff = 0; ok = True

            if t == 1:
                dmg = calc_dmg(eid, ca, cde)
                hp_eff = -dmg
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

    items = []
    for key, (hs, ck) in exits.items():
        yk, bk, atk, dfn = key
        actual_hp = start_hp - hs
        items.append((actual_hp, yk, bk, atk, dfn, hs, ck))

    items.sort(key=lambda x: -x[0])
    pareto = []
    for item in items:
        hp, yk, bk, atk, def_ = item[:5]
        dom = any(p[0] >= hp and p[1] >= yk and p[2] >= bk and p[3] >= atk and p[4] >= def_ and
                  (p[0] > hp or p[1] > yk or p[2] > bk or p[3] > atk or p[4] > def_) for p in pareto)
        if not dom:
            pareto = [p for p in pareto if not (hp >= p[0] and yk >= p[1] and bk >= p[2] and atk >= p[3] and def_ >= p[4] and
                     (hp > p[0] or yk > p[1] or bk > p[2] or atk > p[3] or def_ > p[4]))]
            pareto.append(item)

    return pareto, it, nodes, frm

def trace_path(pareto_item, nodes, frm, start_hp, start_yk, start_bk, start_atk, start_def):
    ck = pareto_item[6]
    path = []; k = ck; safety = 0
    while k is not None and safety < 200:
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
        elif n2[3].startswith('sword'): catk += 10
        elif n2[3].startswith('shield'): cdfn += 10
        ops.append((n2[0], n2[1], n2[3], ohp, oyk, obk, chp, cyk, cbk, catk, cdfn))
    return ops

# 追踪从起点到铁盾的路径
hero = json.load(open(os.path.join(MAP_DIR, 'hero_state.json')))
maps = {}
for fid in ['mt4', 'mt5', 'mt6', 'mt7', 'mt8', 'mt9']:
    maps[fid.upper()] = load_map(fid)

ENTRANCES = {
    'MT4': (11, 10), 'MT5': (2, 11), 'MT6': (1, 2),
    'MT7': (1, 11), 'MT8': (1, 1), 'MT9': (6, 1),
}

state = {'hp': hero['h'], 'atk': hero['a'], 'def': hero['d'], 'yk': hero['yk'], 'bk': hero['bk']}
all_ops = []

for fid in ['MT4', 'MT5', 'MT6', 'MT7', 'MT8', 'MT9']:
    target = 'shield1' if fid == 'MT9' else 'upFloor'
    pareto, iters, nodes, frm = search(
        maps[fid], ENTRANCES[fid][0], ENTRANCES[fid][1],
        state['hp'], state['atk'], state['def'], state['yk'], state['bk'],
        [target], max_iter=200000
    )
    if not pareto:
        print(f"{fid}: NO PATH")
        break
    best = pareto[0]
    ops = trace_path(best, nodes, frm, state['hp'], state['yk'], state['bk'], state['atk'], state['def'])
    all_ops.extend([(fid,) + op for op in ops])
    state = {'hp': best[0], 'atk': best[3], 'def': best[4], 'yk': best[1], 'bk': best[2]}
    print(f"{fid} -> {target}: HP={state['hp']} ATK={state['atk']} DEF={state['def']} YK={state['yk']}")

print(f"\nFull path ({len(all_ops)} steps):")
for op in all_ops:
    fid, x, y, eid, ohp, oyk, obk, chp, cyk, cbk, catk, cdfn = op
    print(f"  {fid} ({x:2d},{y:2d}) {eid:15s}: HP={ohp:4d}->{chp:4d} ATK={catk} DEF={cdfn} YK={oyk}->{cyk}")
