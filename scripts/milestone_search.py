#!/usr/bin/env python3
"""
里程碑倒推搜索
正推到里程碑 -> 倒推检查门槛 -> 不达标则回退拿更多宝石
"""
# Allow scripts to import project-root modules after being moved under scripts/.
import os as _codex_os
import sys as _codex_sys
_codex_root = _codex_os.path.dirname(_codex_os.path.dirname(_codex_os.path.abspath(__file__)))
if _codex_root not in _codex_sys.path:
    _codex_sys.path.insert(0, _codex_root)

import json, heapq, time, os, copy
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
        return float('inf')
    n = max(0, e[1] - def_)
    r = -(-e[0] // m)
    return (r - 1) * n

def load_data():
    def data_path(name):
        return os.path.join('data', 'maps', name)

    hero = json.load(open(data_path('hero_state.json'), encoding='utf-8'))
    maps = {}
    for fid in ['mt1', 'mt3', 'mt4', 'mt5', 'mt6', 'mt7', 'mt8', 'mt9']:
        try:
            raw = json.load(open(data_path(f'{fid}_map.json'), encoding='utf-8'))
        except:
            continue
        blocks = []
        for b in raw['bl']:
            if isinstance(b, dict):
                x, y, t, eid = b['x'], b['y'], 0, b['id']
                cls = b.get('cls', '')
            else:
                x, y, t, eid, np = b
                cls = ''
            np = False
            if eid in ('upFloor', 'downFloor', 'fakeWall'):
                t = 4
            elif cls == 'monsters' or cls == 'enemys' or eid in EM:
                t = 1
            elif eid.endswith('Door'):
                t = 2
            elif cls == 'items' or eid.endswith('Key') or eid.endswith('Potion') or eid.endswith('Gem') or eid.startswith('sword') or eid.startswith('shield'):
                t = 3
            elif cls == 'animates' and (eid.endswith('Key') or eid.endswith('Potion') or eid.endswith('Gem') or eid.startswith('sword') or eid.startswith('shield')):
                t = 3
            if t > 0:
                blocks.append((x, y, t, eid, np))
        W = raw.get('W', raw.get('w', 13))
        H = raw.get('H', raw.get('h', 13))
        maps[fid.upper()] = {'W': W, 'H': H, 'm': raw['m'], 'bl': blocks}
    return hero, maps

def search(data, sx, sy, start_hp, start_atk, start_def, start_yk, start_bk, target_ids, max_iter=300000):
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

ENTRANCES = {
    'MT4': (11, 10), 'MT5': (2, 11), 'MT6': (1, 2),
    'MT7': (1, 11), 'MT8': (1, 1), 'MT9': (6, 1),
}

def search_floor(maps, fid, entries, target, max_iter=200000):
    """搜索一层，返回所有入口的Pareto结果"""
    all_results = []
    ex, ey = ENTRANCES[fid]
    for ei, ent in enumerate(entries):
        pareto, iters, nodes, frm = search(
            maps[fid], ex, ey,
            ent['hp'], ent['atk'], ent['def'], ent['yk'], ent['bk'],
            [target], max_iter=max_iter
        )
        if pareto:
            for p in pareto:
                all_results.append({
                    'hp': p[0], 'yk': p[1], 'bk': p[2], 'atk': p[3], 'def': p[4],
                    'entry': ent, 'iters': iters
                })
    return all_results

def global_pareto(results, keep=5):
    """全局Pareto过滤，保留前keep个"""
    items = [(r['hp'], r['yk'], r['bk'], r['atk'], r['def'], r) for r in results]
    items.sort(key=lambda x: -x[0])
    pareto = []
    for item in items:
        hp, yk, bk, atk, def_, r = item
        dom = any(p[0] >= hp and p[1] >= yk and p[2] >= bk and p[3] >= atk and p[4] >= def_ and
                  (p[0] > hp or p[1] > yk or p[2] > bk or p[3] > atk or p[4] > def_) for p in pareto)
        if not dom:
            pareto = [p for p in pareto if not (hp >= p[0] and yk >= p[1] and bk >= p[2] and atk >= p[3] and def_ >= p[4] and
                     (hp > p[0] or yk > p[1] or bk > p[2] or atk > p[3] or def_ > p[4]))]
            pareto.append((hp, yk, bk, atk, def_, r))

    # 保留top3 + 最高ATK
    entries = []
    seen = set()
    for pr in pareto[:3]:
        hp, yk, bk, atk, def_, r = pr
        key = (atk, def_, yk, bk)
        if key not in seen:
            seen.add(key)
            entries.append({'hp': hp, 'atk': atk, 'def': def_, 'yk': yk, 'bk': bk})
    if pareto:
        max_atk = max(pareto, key=lambda p: (p[3], p[0]))
        hp, yk, bk, atk, def_, r = max_atk
        key = (atk, def_, yk, bk)
        if key not in seen:
            seen.add(key)
            entries.append({'hp': hp, 'atk': atk, 'def': def_, 'yk': yk, 'bk': bk})
    return entries

def check_milestone(state, next_milestone):
    """倒推检查是否满足下一里程碑门槛"""
    if next_milestone == 'sword1':
        return state['atk'] >= 20, "ATK>=20"
    elif next_milestone == 'shield1':
        return state['def'] >= 20, "DEF>=20"
    elif next_milestone == 'guard':
        ok = state['atk'] > 22
        return ok, f"ATK>22 (current={state['atk']})"
    elif next_milestone == 'boss':
        guard_cost = calc_dmg('yellowGuard', state['atk'], state['def'])
        if guard_cost == float('inf'):
            return False, "Cannot fight guard"
        hp_after = state['hp'] - guard_cost
        boss_cost = calc_dmg('skeletonCaptain', state['atk'], state['def']) + \
                   6 * calc_dmg('skeleton', state['atk'], state['def']) + \
                   2 * calc_dmg('skeletonSoldier', state['atk'], state['def'])
        ok = hp_after > boss_cost
        return ok, f"HP after guard={hp_after}, Boss={boss_cost}, surplus={hp_after-boss_cost}"
    return False, "Unknown milestone"

def main():
    print("=" * 80)
    print("  里程碑倒推搜索")
    print("=" * 80)

    hero, maps = load_data()
    print(f"\n  起点: HP={hero['h']} ATK={hero['a']} DEF={hero['d']} YK={hero['yk']} BK={hero['bk']}")

    t_start = time.time()

    # ===== Phase 1: 正推到铁剑 =====
    print("\n" + "-" * 40)
    print("Phase 1: 4F -> 铁剑")
    print("-" * 40)

    entries = [{'hp': hero['h'], 'atk': hero['a'], 'def': hero['d'], 'yk': hero['yk'], 'bk': hero['bk']}]

    # 4F -> upFloor
    mt4_results = search_floor(maps, 'MT4', entries, 'upFloor')
    mt4_entries = global_pareto(mt4_results)
    print(f"  MT4 -> upFloor: {len(mt4_results)} results, {len(mt4_entries)} Pareto entries")

    # 5F -> sword1
    mt5_results = search_floor(maps, 'MT5', mt4_entries, 'sword1')
    mt5_entries = global_pareto(mt5_results)
    print(f"  MT5 -> sword1: {len(mt5_results)} results, {len(mt5_entries)} Pareto entries")
    for i, ent in enumerate(mt5_entries):
        print(f"    #{i+1}: HP={ent['hp']} ATK={ent['atk']} DEF={ent['def']} YK={ent['yk']}")

    # 检查铁剑后是否满足下一门槛
    ok, reason = check_milestone(mt5_entries[0], 'shield1')
    print(f"\n  铁剑后门槛检查: {'PASS' if ok else 'FAIL'} ({reason})")

    # ===== Phase 2: 正推到铁盾 =====
    print("\n" + "-" * 40)
    print("Phase 2: 铁剑 -> 铁盾")
    print("-" * 40)

    # 5F -> upFloor
    mt5_up = search_floor(maps, 'MT5', mt5_entries, 'upFloor')
    mt5_up_entries = global_pareto(mt5_up)
    print(f"  MT5 -> upFloor: {len(mt5_up)} results, {len(mt5_up_entries)} entries")

    # 6F -> upFloor
    mt6_results = search_floor(maps, 'MT6', mt5_up_entries, 'upFloor')
    mt6_entries = global_pareto(mt6_results)
    print(f"  MT6 -> upFloor: {len(mt6_results)} results, {len(mt6_entries)} entries")

    # 7F -> upFloor
    mt7_results = search_floor(maps, 'MT7', mt6_entries, 'upFloor')
    mt7_entries = global_pareto(mt7_results)
    print(f"  MT7 -> upFloor: {len(mt7_results)} results, {len(mt7_entries)} entries")

    # 8F -> upFloor
    mt8_results = search_floor(maps, 'MT8', mt7_entries, 'upFloor')
    if mt8_results:
        mt8_entries = global_pareto(mt8_results)
        print(f"  MT8 -> upFloor: {len(mt8_results)} results, {len(mt8_entries)} entries")
    else:
        print(f"  MT8 -> upFloor: NO PATH!")
        mt8_entries = []

    # 9F -> shield1
    mt9_results = search_floor(maps, 'MT9', mt8_entries if mt8_entries else mt7_entries, 'shield1')
    if mt9_results:
        mt9_entries = global_pareto(mt9_results)
        print(f"  MT9 -> shield1: {len(mt9_results)} results, {len(mt9_entries)} entries")
        for i, ent in enumerate(mt9_entries):
            print(f"    #{i+1}: HP={ent['hp']} ATK={ent['atk']} DEF={ent['def']} YK={ent['yk']}")
    else:
        print(f"  MT9 -> shield1: NO PATH!")
        mt9_entries = []

    # 检查铁盾后是否满足守卫门槛
    if mt9_entries:
        ok, reason = check_milestone(mt9_entries[0], 'guard')
        print(f"\n  铁盾后守卫门槛: {'PASS' if ok else 'FAIL'} ({reason})")

    # ===== Phase 3: 倒推修复 =====
    if mt9_entries and not ok:
        print("\n" + "-" * 40)
        print("Phase 3: 倒推修复 - 回退拿更多宝石")
        print("-" * 40)

        # 铁盾后ATK不足，需要回退
        needed_atk = 23
        current_atk = mt9_entries[0]['atk']
        needed_gems = needed_atk - current_atk
        print(f"  当前ATK={current_atk}, 需要ATK={needed_atk}, 差{needed_gems}个红宝石")

        # 回退到7F，尝试拿7F红宝石
        print(f"\n  回退到7F，尝试拿redGem...")
        mt7_red = search_floor(maps, 'MT7', mt6_entries, 'redGem')
        if mt7_red:
            mt7_red_entries = global_pareto(mt7_red)
            print(f"  MT7 -> redGem: {len(mt7_red)} results, {len(mt7_red_entries)} entries")
            for i, ent in enumerate(mt7_red_entries[:3]):
                print(f"    #{i+1}: HP={ent['hp']} ATK={ent['atk']} DEF={ent['def']} YK={ent['yk']}")

            # 从拿红宝石的状态继续搜8F
            mt8_red = search_floor(maps, 'MT8', mt7_red_entries, 'upFloor')
            if mt8_red:
                mt8_red_entries = global_pareto(mt8_red)
                print(f"  MT8 -> upFloor (from redGem): {len(mt8_red)} results")

                mt9_red = search_floor(maps, 'MT9', mt8_red_entries, 'shield1')
                if mt9_red:
                    mt9_red_entries = global_pareto(mt9_red)
                    print(f"  MT9 -> shield1 (from redGem): {len(mt9_red)} results")
                    for i, ent in enumerate(mt9_red_entries[:3]):
                        print(f"    #{i+1}: HP={ent['hp']} ATK={ent['atk']} DEF={ent['def']} YK={ent['yk']}")

                    ok2, reason2 = check_milestone(mt9_red_entries[0], 'guard')
                    print(f"\n  回退后守卫门槛: {'PASS' if ok2 else 'FAIL'} ({reason2})")

    # ===== Phase 4: Flyback补宝石 =====
    if mt9_entries and not ok:
        print("\n" + "-" * 40)
        print("Phase 4: Flyback 补宝石")
        print("-" * 40)

        # 从铁盾状态flyback到1F/3F拿宝石
        shield_state = mt9_entries[0]
        print(f"  铁盾状态: HP={shield_state['hp']} ATK={shield_state['atk']} DEF={shield_state['def']}")

        # 1F有redGem(7,3), blueGem(7,4)
        # 3F有redGem(2,9), blueGem(2,1)
        # 假设flyback后史莱姆无损（22攻打史莱姆=0伤）

        flyback_states = []
        for take_1f_red in [True, False]:
            for take_1f_blue in [True, False]:
                for take_3f_red in [True, False]:
                    for take_3f_blue in [True, False]:
                        atk = shield_state['atk']
                        def_ = shield_state['def']
                        hp = shield_state['hp']
                        if take_1f_red: atk += 1
                        if take_1f_blue: def_ += 1
                        if take_3f_red: atk += 1
                        if take_3f_blue: def_ += 1

                        guard_cost = calc_dmg('yellowGuard', atk, def_)
                        if guard_cost == float('inf'):
                            continue
                        hp_after = hp - guard_cost
                        boss_cost = calc_dmg('skeletonCaptain', atk, def_) + \
                                   6 * calc_dmg('skeleton', atk, def_) + \
                                   2 * calc_dmg('skeletonSoldier', atk, def_)
                        if hp_after > boss_cost:
                            flyback_states.append({
                                'gems': [],
                                'atk': atk, 'def': def_, 'hp_after_guard': hp_after,
                                'guard_cost': guard_cost, 'boss_cost': boss_cost,
                                'surplus': hp_after - boss_cost
                            })
                            if take_1f_red: flyback_states[-1]['gems'].append('1F红')
                            if take_1f_blue: flyback_states[-1]['gems'].append('1F蓝')
                            if take_3f_red: flyback_states[-1]['gems'].append('3F红')
                            if take_3f_blue: flyback_states[-1]['gems'].append('3F蓝')

        if flyback_states:
            best = max(flyback_states, key=lambda x: x['surplus'])
            print(f"\n  可行Flyback方案: {len(flyback_states)} 个")
            print(f"  最佳: 拿{', '.join(best['gems'])}")
            print(f"    ATK={best['atk']} DEF={best['def']}")
            print(f"    守卫消耗={best['guard_cost']}, 守卫后HP={best['hp_after_guard']}")
            print(f"    Boss消耗={best['boss_cost']}, 余量={best['surplus']}")
        else:
            print(f"\n  无可行Flyback方案！")

    total = time.time() - t_start
    print(f"\n{'='*80}")
    print(f"  总计耗时: {total:.1f}s")
    print(f"{'='*80}")

if __name__ == '__main__':
    main()
