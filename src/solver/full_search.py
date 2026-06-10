#!/usr/bin/env python3
"""
完整1-10层 Pareto搜索
核心: per-entry collected 跟踪 + 每轮flyback尝试所有可收集目标
"""
import json, math, heapq, time, os
from collections import deque

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(ROOT_DIR, 'data', 'maps')
os.chdir(ROOT_DIR)

# Keep the visited mask in the Dijkstra state.  Without this, two routes that
# reach the same node with the same current keys/stats collapse even if one has
# opened extra doors or consumed a different collected set.  Phase-level Pareto
# can only be correct if these variants survive the floor-level search.
PRESERVE_VISITED_IN_STATE = False

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
    if m <= 0: return float('inf')
    n = max(0, e[1] - def_)
    r = -(-e[0] // m)
    return (r - 1) * n

def load_data():
    def data_path(name):
        path = os.path.join(DATA_DIR, name)
        if os.path.exists(path):
            return path
        return os.path.join(ROOT_DIR, name)

    hero = json.load(open(data_path('hero_state.json'), encoding='utf-8'))
    maps = {}
    for fid in ['mt1', 'mt3', 'mt4', 'mt5', 'mt6', 'mt7', 'mt8', 'mt9', 'mt10']:
        try:
            raw = json.load(open(data_path(f'{fid}_map.json'), encoding='utf-8'))
        except:
            continue
        blocks = []
        special_door_pos = set()
        for b in raw['bl']:
            if isinstance(b, dict):
                x, y, eid = b['x'], b['y'], b['id']
                cls = b.get('cls', '')
            else:
                x, y, t, eid, np = b
                cls = ''
            if not eid or eid == '':
                continue
            # specialDoor: 记录位置后设为可通行(击杀周围怪后自动开)
            if eid == 'specialDoor':
                special_door_pos.add((x, y))
                raw['m'][y-1][x-1] = 0  # 设为可通行
                continue
            if isinstance(b, dict):
                x, y, eid = b['x'], b['y'], b['id']
                cls = b.get('cls', '')
            else:
                x, y, t, eid, np = b
                cls = ''
            if not eid or eid == '':
                continue
            t = 0
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
                blocks.append((x, y, t, eid))
        W = raw.get('W', raw.get('w', 13))
        H = raw.get('H', raw.get('h', 13))
        maps[fid.upper()] = {'W': W, 'H': H, 'm': raw['m'], 'bl': blocks,
                             'special_doors': special_door_pos}
    return hero, maps

def search(data, sx, sy, start_hp, start_atk, start_def, start_yk, start_bk, start_rk,
           target_ids, max_iter=500000, removed_pos=None):
    if removed_pos is None:
        removed_pos = set()
    mapd = [row[:] for row in data['m']]
    W, H, bl = data['W'], data['H'], data['bl']
    special_doors = data.get('special_doors', set())
    bl = [b for b in bl if (b[0], b[1]) not in removed_pos]

    nodes = []; pm = {}
    guard_indices = set()
    for b in bl:
        x, y, t, eid = b
        idx = len(nodes)
        nodes.append((x, y, t, eid)); pm[(x, y)] = idx
        if eid == 'yellowGuard':
            guard_indices.add(idx)
    NN = len(nodes)
    num_guards = len(guard_indices)
    guard_list = sorted(guard_indices)
    guard_mask_max = 1 << num_guards if num_guards > 0 else 1
    guard_bit = {}
    for bit_pos, gi in enumerate(guard_list):
        guard_bit[gi] = bit_pos

    def is_wall(x, y, gm):
        if x <= 0 or y <= 0 or x >= W-1 or y >= H-1: return True
        # special door: guard check BEFORE pm check
        if (x, y) in special_doors:
            if num_guards == 0: return False
            if gm == guard_mask_max - 1: return False
            return True
        # block位置(怪物/门/物品/楼梯)总是可到达的, 即使map值为墙
        if (x, y) in pm: return False
        if mapd[y][x] == 1: return True
        return False

    def bfs(px, py, vm, gm):
        v = {(px, py)}; q = deque([(px, py)]); r = []
        while q:
            cx, cy = q.popleft()
            for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                nx, ny = cx+dx, cy+dy
                if is_wall(nx, ny, gm) or (nx, ny) in v: continue
                v.add((nx, ny))
                ni = pm.get((nx, ny))
                if ni is not None:
                    if vm & (1 << ni): q.append((nx, ny)); continue
                    r.append(ni)
                    if nodes[ni][2] in (3, 4): q.append((nx, ny))
                    continue
                q.append((nx, ny))
        return r

    yk_max = min(start_yk + sum(1 for n in nodes if n[3] == 'yellowKey'), 15)
    bk_max = min(start_bk + sum(1 for n in nodes if n[3] == 'blueKey'), 15)

    # 预计算哪些node是target
    target_bits = frozenset(i for i in range(NN) if nodes[i][3] in target_ids)
    # Preserve coverage for explicit phase targets that may not be reflected
    # fully by stats. Otherwise a route that touches only one target can
    # collapse a route that reached all targets in the same floor action.
    coverage_eids = {
        'upFloor', 'downFloor', 'fakeWall',
        'redGem', 'blueGem', 'greenGem', 'sword1', 'shield1',
    }
    target_coverage_bits = frozenset(
        i for i in target_bits if nodes[i][2] == 4 or nodes[i][3] in coverage_eids
    )
    target_coverage_mask = 0
    for i in target_coverage_bits:
        target_coverage_mask |= (1 << i)

    door_idx = {
        'yellowDoor': frozenset(i for i, n in enumerate(nodes) if n[2] == 2 and n[3] == 'yellowDoor'),
        'blueDoor': frozenset(i for i, n in enumerate(nodes) if n[2] == 2 and n[3] == 'blueDoor'),
        'redDoor': frozenset(i for i, n in enumerate(nodes) if n[2] == 2 and n[3] == 'redDoor'),
    }

    def count_bits(vm, indices):
        return sum(1 for i in indices if vm & (1 << i))

    def door_counts(vm):
        return (
            count_bits(vm, door_idx['yellowDoor']),
            count_bits(vm, door_idx['blueDoor']),
            count_bits(vm, door_idx['redDoor']),
        )

    def make_state_key(cn, yk, bk, rk, atk, def_, gm, vm):
        yd, bd, rd = door_counts(vm)
        base = (cn, yk, bk, rk, atk, def_, gm, yd, bd, rd)
        if PRESERVE_VISITED_IN_STATE:
            return base + (vm,)
        return base

    init_state = make_state_key(-1, start_yk, start_bk, start_rk, start_atk, start_def, 0, 0)
    # best: state_key -> (dmg_cost, actual_hs, vm, parent_state_key)
    best = {init_state: (0, 0, 0, None)}
    hpq = [(0, 0, 0, 0, 0, -start_yk, -start_bk, -start_rk, -start_atk, -start_def, 0, -1, 0)]
    exits = {}; it = 0

    while hpq and it < max_iter:
        dc, _, _, _, _, my, mb, mr, ma, md, mg, cn, cv = heapq.heappop(hpq)
        cy, cb, cr, ca, cde, cgm = -my, -mb, -mr, -ma, -md, mg
        state_key = make_state_key(cn, cy, cb, cr, ca, cde, cgm, cv)
        if state_key not in best or best[state_key][0] != dc: continue
        _, ahs, cv, _ = best[state_key]; it += 1

        # Exit: 当前节点是target, 或vm中已访问过target后继续探索
        has_target = (0 <= cn < NN and cn in target_bits) or \
                     any((cv & (1 << tb)) for tb in target_bits)
        if has_target:
            yd, bd, rd = door_counts(cv)
            key = (cy, cb, cr, ca, cde, cgm, yd, bd, rd, cv)
            if key not in exits or dc < exits[key][0] or (dc == exits[key][0] and ahs < exits[key][1]):
                exits[key] = (dc, ahs, state_key, cv)

        if cn == -1: px, py = sx, sy
        else: px, py = nodes[cn][0], nodes[cn][1]
        reachable = bfs(px, py, cv, cgm)

        for tn in reachable:
            if cv & (1 << tn): continue
            n = nodes[tn]; t, eid = n[2], n[3]
            ny, nb, nr, na, nd, ngm = cy, cb, cr, ca, cde, cgm
            hp_loss = 0; potion_hp = 0; ok = True
            if t == 1:
                dmg = calc_dmg(eid, ca, cde)
                if dmg == float('inf'):
                    ok = False
                else:
                    hp_loss = dmg
                    if tn in guard_bit:
                        ngm = cgm | (1 << guard_bit[tn])
            elif t == 2:
                if eid == 'yellowDoor':
                    if cy <= 0: ok = False
                    else: ny = cy - 1
                elif eid == 'blueDoor':
                    if cb <= 0: ok = False
                    else: nb = cb - 1
                elif eid == 'redDoor':
                    if cr <= 0: ok = False
                    else: nr = cr - 1
            elif t == 3:
                if eid == 'yellowKey': ny = cy + 1
                elif eid == 'blueKey': nb = cb + 1
                elif eid == 'redKey': nr = cr + 1
                elif eid == 'redPotion': potion_hp = 50
                elif eid == 'bluePotion': potion_hp = 200
                elif eid == 'redGem': na = ca + 1
                elif eid == 'blueGem': nd = cde + 1
                elif eid == 'greenGem': na = ca + 5
                elif eid.startswith('sword'): na = ca + 10
                elif eid.startswith('shield'): nd = cde + 10
            elif t == 4: pass
            if not ok: continue
            if ny < 0 or nb < 0 or nr < 0 or ny > yk_max or nb > bk_max: continue
            new_hp = start_hp - ahs - hp_loss + potion_hp
            if new_hp <= 0: continue
            new_dc = dc + hp_loss
            new_ahs = ahs + hp_loss - potion_hp
            nv = cv | (1 << tn)
            nk = make_state_key(tn, ny, nb, nr, na, nd, ngm, nv)
            if nk not in best or new_dc < best[nk][0] or (new_dc == best[nk][0] and new_ahs < best[nk][1]):
                best[nk] = (new_dc, new_ahs, nv, state_key)
                nyd, nbd, nrd = door_counts(nv)
                heapq.heappush(hpq, (new_dc, nyd, nbd, nrd, new_ahs, -ny, -nb, -nr, -na, -nd, ngm, tn, nv))

    items = []
    for key, (dc, ahs, state_key, vm) in exits.items():
        yk, bk, rk, atk, dfn, gm = key[:6]
        actual_hp = start_hp - ahs
        visited_pos = frozenset(
            (nodes[i][0], nodes[i][1])
            for i in range(NN)
            if (vm & (1 << i)) and (
                nodes[i][2] in (1, 2, 3) or
                (nodes[i][2] == 4 and i in target_coverage_bits)
            )
        )
        yd, bd, rd = door_counts(vm)
        covered_targets_seen = vm & target_coverage_mask
        items.append((actual_hp, yk, bk, rk, atk, dfn, ahs, visited_pos, dc, yd, bd, rd, covered_targets_seen))

    items.sort(key=lambda x: (x[8], x[9], x[10], x[11], -x[0]))
    pareto = []
    for item in items:
        hp, yk, bk, rk, atk, def_, ahs, vis, dc, yd, bd, rd, _t4 = item

        def dominates(a, b):
            ahp, ayk, abk, ark, aatk, adef, _aahs, _avis, adc, ayd, abd, ard, at4 = a
            bhp, byk, bbk, brk, batk, bdef, _bahs, _bvis, bdc, byd, bbd, brd, bt4 = b
            if (at4 | bt4) != at4:
                return False
            if not (
                adc <= bdc and ayd <= byd and abd <= bbd and ard <= brd and
                ayk >= byk and abk >= bbk and ark >= brk and
                aatk >= batk and adef >= bdef
            ):
                return False
            core_strict = (
                adc < bdc or ayd < byd or abd < bbd or ard < brd or
                ayk > byk or abk > bbk or ark > brk or
                aatk > batk or adef > bdef
            )
            same_core = (
                adc == bdc and ayd == byd and abd == bbd and ard == brd and
                ayk == byk and abk == bbk and ark == brk and
                aatk == batk and adef == bdef
            )
            return core_strict or (same_core and ahp >= bhp)

        dom = any(dominates(p, item) for p in pareto)
        if not dom:
            pareto = [p for p in pareto if not dominates(item, p)]
            pareto.append(item)
    return [item[:9] for item in pareto], it, nodes, best

# 1-3楼初始已收集资源(hero到达4楼前的路线消耗)
FLOOR_13_COLLECTED = {
    'MT1': frozenset([(3, 1), (4, 1), (5, 1), (5, 10), (6, 9)]),
    'MT3': frozenset([(4, 1), (4, 2), (4, 3), (5, 1), (5, 2), (5, 3),
                      (6, 1), (6, 2), (6, 3), (7, 5), (8, 10), (9, 11)]),
}

ENTRANCES = {
    'MT1': (2, 11), 'MT3': (1, 11), 'MT4': (11, 10),
    'MT5': (1, 11), 'MT6': (1, 1), 'MT7': (11, 11),
    'MT8': (1, 1), 'MT9': (6, 1), 'MT10': (1, 10),}
# flyback入口: 出现在upFloor旁边的空格
FLYBACK_ENTRANCES = {
    'MT1': (2, 1),   'MT3': (10, 11), 'MT4': (11, 11),
    'MT5': (1, 11),  'MT6': (1, 1),   'MT7': (11, 11),
    'MT8': (1, 1),   'MT9': (6, 1),   'MT10': (1, 10),
}

def search_with_path(data, sx, sy, start_hp, start_atk, start_def, start_yk, start_bk, start_rk,
                    target_ids, max_iter=500000, removed_pos=None, prefer_yk=None,
                    prefer_atk=None, prefer_def=None, target_state=None, select_mode='max_hp'):
    """搜索并回溯步骤序列, 使用min-damage Dijkstra.
    prefer_yk: 如果指定, 优先选择YK>=prefer_yk的exit
    prefer_atk/def: 如果指定, 优先选择ATK/DEF匹配的exit
    target_state: 如果指定, 优先选择最接近目标状态的exit(覆盖prefer参数)
    select_mode: 'max_hp'按最大HP选exit, 'min_damage'按最小战斗成本选exit(宝石搜索用)"""
    pareto, it, nodes, best = search(data, sx, sy, start_hp, start_atk, start_def,
                                      start_yk, start_bk, start_rk, target_ids,
                                      max_iter, removed_pos)
    if not pareto:
        return None, None, None

    NN = len(nodes)
    target_bits = set(i for i in range(NN) if nodes[i][3] in target_ids)

    # 找最优exit: vm中已访问过target的节点都算valid exit
    best_exit_sk = None
    best_ahs = float('inf')
    candidates = []
    for sk, (dc, ahs, vm, parent) in best.items():
        cn = sk[0]
        if cn < 0: continue
        # 当前节点是target, 或vm中已包含target(拿到target后继续探索)
        has_target = (cn in target_bits) or any((vm & (1 << tb)) for tb in target_bits)
        if not has_target: continue
        # 计算vm中包含多少个target
        n_targets = sum(1 for tb in target_bits if (vm & (1 << tb)))
        candidates.append((sk, dc, ahs, sk[1], n_targets))  # sk[1] = yk

    # 选exit: min ahs(=max HP)优先, n_targets次优先
    # 可选: prefer_yk/atk/def缩小范围
    filtered = candidates
    if prefer_yk is not None and prefer_yk > 0:
        preferred = [c for c in filtered if c[3] >= prefer_yk]
        if preferred: filtered = preferred
    if prefer_atk is not None:
        preferred = [c for c in filtered if c[0][4] >= prefer_atk]
        if preferred: filtered = preferred
    if prefer_def is not None:
        preferred = [c for c in filtered if c[0][5] >= prefer_def]
        if preferred: filtered = preferred

    if target_state is not None:
        # 精确匹配: 选择与目标状态最接近的exit
        def state_dist(c):
            sk = c[0]
            yk, bk, rk, atk, def_ = sk[1], sk[2], sk[3], sk[4], sk[5]
            hp_est = start_hp - c[2]  # ahs -> HP
            d = 0
            d += abs(hp_est - target_state['hp'])
            d += abs(yk - target_state['yk']) * 50
            d += abs(bk - target_state.get('bk', 0)) * 100
            d += abs(rk - target_state.get('rk', 0)) * 100
            d += abs(atk - target_state['atk']) * 50
            d += abs(def_ - target_state['def']) * 50
            return d
        filtered.sort(key=state_dist)
    elif select_mode == 'min_damage':
        # 宝石搜索: 按战斗成本(dc)升序, 同dc按ahs升序, 同ahs按n_targets降序
        filtered.sort(key=lambda c: (c[1], c[2], -c[4]))
    else:
        # 先按ahs升序(max HP), 同ahs按n_targets降序
        filtered.sort(key=lambda c: (c[2], -c[4]))
    best_exit_sk = filtered[0][0] if filtered else None

    if best_exit_sk is None:
        return None, None, None

    # 回溯parent链, 补全中间步骤
    # parent链只记录Dijkstra显式处理的节点(type 1怪物),
    # 但中间穿过的type 2/3节点(门/拾取)也需要补上
    raw_path = []
    current = best_exit_sk
    while current is not None:
        cn = current[0]
        if cn >= 0:
            raw_path.append(cn)
        _, _, _, parent = best[current]
        current = parent
    raw_path.reverse()

    # 对每对相邻节点, 检查vm差异补全中间节点
    path = []
    prev_vm = 0
    for i, ni in enumerate(raw_path):
        # 获取当前节点的vm
        sk = None
        # 找到包含ni的state_key (从best中)
        # ni是raw_path[i], 需要找到它的state_key对应的vm
        # 简单方式: 从exits或best中获取
        # 更好的方式: 在回溯时就记录vm
        pass

    # 改用: 回溯时同时记录vm
    chain = []
    current = best_exit_sk
    while current is not None:
        cn = current[0]
        _, _, vm, parent = best[current]
        chain.append((cn, vm))
        current = parent
    chain.reverse()

    # 从chain构建完整路径: 每步之间补上vm新增的type 2/3节点
    path = []
    prev_cn = -1
    prev_vm = 0
    for cn, vm in chain:
        if cn >= 0:
            # 找出从上一步到这一步vm新增的节点(排除cn本身)
            new_bits = vm & ~prev_vm
            # 清除cn自身的bit
            new_bits = new_bits & ~(1 << cn) if cn >= 0 else new_bits
            # 新增节点中type 2/3的补入path
            intermediate = []
            for bi in range(NN):
                if new_bits & (1 << bi):
                    if nodes[bi][2] in (2, 3):
                        intermediate.append(bi)
            # 中间节点排序: 需要按BFS可达顺序
            # 简单启发式: 按曼哈顿距离从prev位置排序
            if intermediate:
                if prev_cn >= 0:
                    ref_x, ref_y = nodes[prev_cn][0], nodes[prev_cn][1]
                else:
                    ref_x, ref_y = sx, sy
                intermediate.sort(key=lambda bi: abs(nodes[bi][0]-ref_x) + abs(nodes[bi][1]-ref_y))
                path.extend(intermediate)
            path.append(cn)
        prev_cn = cn
        prev_vm = vm

    # 前向模拟步骤
    steps = []
    hp = start_hp
    cy, cb, cr, ca, cd = start_yk, start_bk, start_rk, start_atk, start_def

    for ni in path:
        n = nodes[ni]
        x, y, t, eid = n
        hp_before = hp
        atk_before = ca
        def_before = cd
        yk_before = cy
        bk_before = cb
        rk_before = cr

        if t == 1:
            dmg = calc_dmg(eid, ca, cd)
            hp -= dmg
            action = '击杀'
        elif t == 2:
            if eid == 'yellowDoor': cy -= 1
            elif eid == 'blueDoor': cb -= 1
            elif eid == 'redDoor': cr -= 1
            action = '开门'
        elif t == 3:
            if eid == 'yellowKey': cy += 1
            elif eid == 'blueKey': cb += 1
            elif eid == 'redKey': cr += 1
            elif eid == 'redPotion': hp += 50
            elif eid == 'bluePotion': hp += 200
            elif eid == 'redGem': ca += 1
            elif eid == 'blueGem': cd += 1
            elif eid == 'greenGem': ca += 5
            elif eid.startswith('sword'): ca += 10
            elif eid.startswith('shield'): cd += 10
            action = '拾取'
        elif t == 4:
            action = '通行'
        else:
            action = '???'

        steps.append({
            'x': x, 'y': y, 'action': action,
            'eid': eid, 'hp_before': hp_before, 'hp_after': hp,
            'atk_before': atk_before, 'def_before': def_before,
            'yk_before': yk_before, 'bk_before': bk_before, 'rk_before': rk_before,
            'atk': ca, 'def': cd, 'yk': cy, 'bk': cb, 'rk': cr,
        })

    final_state = {'hp': hp, 'atk': ca, 'def': cd, 'yk': cy, 'bk': cb, 'rk': cr}
    vis_pos = frozenset((nodes[ni][0], nodes[ni][1]) for ni in path if nodes[ni][2] in (1,2,3))
    return steps, final_state, vis_pos


# 所有可收集资源（每层内按宝石→钥匙→药水排序，宝石减伤收益最高）
COLLECTIBLES = {
    'MT1': ['redGem', 'blueGem', 'yellowKey', 'bluePotion', 'redPotion'],
    'MT3': ['redGem', 'blueGem', 'yellowKey', 'blueKey', 'bluePotion', 'redPotion'],
    'MT4': ['redGem', 'yellowKey', 'blueKey', 'bluePotion', 'redPotion'],
    'MT5': ['blueGem', 'yellowKey', 'redPotion'],
    'MT6': ['blueGem', 'yellowKey', 'redPotion'],
    'MT7': ['redGem', 'yellowKey', 'bluePotion', 'redPotion'],
    'MT8': ['redGem', 'blueGem', 'yellowKey', 'bluePotion', 'redPotion', 'redKey'],
    'MT9': ['redGem', 'blueGem', 'yellowKey', 'redPotion'],
    'MT10': ['redGem', 'blueGem', 'bluePotion'],
}

# 只含宝石(用于Phase2, 钥匙/药水按需取)
GEM_ONLY = {fid: [t for t in ts if t in {'redGem', 'blueGem', 'greenGem'}]
            for fid, ts in COLLECTIBLES.items()}

# 钥匙+药水(用于按需补充)
KEY_POTION = {fid: [t for t in ts if t not in {'redGem', 'blueGem', 'greenGem'}]
              for fid, ts in COLLECTIBLES.items()}

def search_floor(maps, fid, ent, targets, max_iter=500000, flyback=False, extra_removed=None):
    entrances = FLYBACK_ENTRANCES if flyback else ENTRANCES
    sx, sy = entrances[fid]
    removed = ent.get('collected', {}).get(fid, frozenset())
    if fid in FLOOR_13_COLLECTED:
        removed = removed | FLOOR_13_COLLECTED[fid]
    if extra_removed:
        removed = removed | frozenset(extra_removed)
    pareto, it, nodes, best = search(maps[fid], sx, sy,
                  ent['hp'], ent['atk'], ent['def'],
                  ent['yk'], ent['bk'], ent['rk'],
                  targets, max_iter=max_iter, removed_pos=removed)
    return pareto, it, nodes

def search_floor_with_best(maps, fid, ent, targets, max_iter=500000, flyback=False):
    entrances = FLYBACK_ENTRANCES if flyback else ENTRANCES
    sx, sy = entrances[fid]
    removed = ent.get('collected', {}).get(fid, frozenset())
    if fid in FLOOR_13_COLLECTED:
        removed = removed | FLOOR_13_COLLECTED[fid]
    pareto, it, nodes, best = search(maps[fid], sx, sy,
                  ent['hp'], ent['atk'], ent['def'],
                  ent['yk'], ent['bk'], ent['rk'],
                  targets, max_iter=max_iter, removed_pos=removed)
    return pareto, it, nodes, best

def do_flyback(maps, entries, fid, targets):
    """对某层做flyback搜索，返回合并后的结果
    宝石一次性多目标搜(算法自动找最优顺序)，钥匙和药水按需搜(不够才取)
    内部不做filter, 由外部统一filter"""
    GEM_IDS = {'redGem', 'blueGem', 'greenGem'}
    gem_targets = [t for t in targets if t in GEM_IDS]
    key_potion_targets = [t for t in targets if t not in GEM_IDS]

    all_results = []
    # 第一轮: 宝石(多目标搜索, 算法自动对比先拿哪个更优)
    available_gems = []
    for tgt in gem_targets:
        for ent in entries:
            already = ent.get('collected', {}).get(fid, frozenset())
            if fid in FLOOR_13_COLLECTED:
                already = already | FLOOR_13_COLLECTED[fid]
            if any((b[0], b[1]) not in already and b[3] == tgt for b in maps[fid]['bl']):
                available_gems.append(tgt)
                break
    available_gems = list(dict.fromkeys(available_gems))  # dedupe

    if available_gems:
        for ent in entries:
            already = ent.get('collected', {}).get(fid, frozenset())
            if fid in FLOOR_13_COLLECTED:
                already = already | FLOOR_13_COLLECTED[fid]
            # 一次搜所有可用宝石, 算法自动找最优顺序
            pareto, iters, _ = search_floor(maps, fid, ent, available_gems, flyback=True)
            if pareto:
                for p in pareto:
                    hp, yk, bk, rk, atk, def_, hs, vis_pos, dmg_cost = p
                    new_collected = dict(ent.get('collected', {}))
                    new_collected[fid] = already | vis_pos
                    all_results.append({
                        'hp': hp, 'yk': yk, 'bk': bk, 'rk': rk,
                        'atk': atk, 'def': def_,
                        'collected': new_collected
                    })

    # 第二轮: 钥匙+药水 (按需搜, 不够才取)
    # 用第一轮结果+原始entries
    key_potion_entries = list(all_results) + list(entries)
    for tgt in key_potion_targets:
        for ent in key_potion_entries:
            already = ent.get('collected', {}).get(fid, frozenset())
            if fid in FLOOR_13_COLLECTED:
                already = already | FLOOR_13_COLLECTED[fid]
            target_available = any(
                (b[0], b[1]) not in already and b[3] == tgt
                for b in maps[fid]['bl']
            )
            if not target_available:
                continue
            pareto, iters, _ = search_floor(maps, fid, ent, [tgt], flyback=True)
            if pareto:
                for p in pareto:
                    hp, yk, bk, rk, atk, def_, hs, vis_pos, dmg_cost = p
                    new_collected = dict(ent.get('collected', {}))
                    new_collected[fid] = already | vis_pos
                    all_results.append({
                        'hp': hp, 'yk': yk, 'bk': bk, 'rk': rk,
                        'atk': atk, 'def': def_,
                        'collected': new_collected
                    })
    return all_results

def main():
    print("=" * 80)
    print("  1-10层策略搜索 (Phase1+gem flyback + 全量flyback + redKey)")
    print("=" * 80)

    hero, maps = load_data()
    start = {'hp': hero['h'], 'atk': hero['a'], 'def': hero['d'],
             'yk': hero['yk'], 'bk': hero['bk'], 'rk': 0,
             'collected': {}}
    print(f"\n  起点: HP={start['hp']} ATK={start['atk']} DEF={start['def']} "
          f"YK={start['yk']} BK={start['bk']}")

    t_start = time.time()

    # === Phase 1: 核心装备 + ATK宝石 ===
    # 先拿剑盾, 再flyback拿1-3楼redGem提高ATK(减伤打yellowGuard)
    print("\n=== Phase 1: 核心装备路线 ===")
    entries = [start.copy()]
    phase1 = [
        ('MT4', ['upFloor', 'redGem'], False),
        ('MT5', ['sword1'], False),
        ('MT4', ['redGem'], True),         # flyback拿redGem, ATK=20→21
        ('MT5', ['upFloor'], True),
        ('MT6', ['upFloor'], False),
        ('MT7', ['upFloor'], False),
        ('MT8', ['upFloor'], False),
        ('MT9', ['shield1'], False),
        # flyback拿1-3楼redGem (提高ATK到25)
        ('MT1', ['redGem'], True),
        ('MT3', ['redGem'], True),
    ]
    for fid, targets, force_flyback in phase1:
        print(f"\n  [{fid}] {len(entries)} entries...")
        all_results = []
        for tgt in targets:
            for ent in entries:
                already = ent.get('collected', {}).get(fid, frozenset())
                if fid in FLOOR_13_COLLECTED:
                    already = already | FLOOR_13_COLLECTED[fid]
                target_available = any(
                    (b[0], b[1]) not in already and b[3] == tgt
                    for b in maps[fid]['bl']
                )
                if not target_available and tgt != 'upFloor':
                    continue
                is_flyback = force_flyback or fid in ent.get('collected', {})
                pareto, iters, _ = search_floor(maps, fid, ent, [tgt], flyback=is_flyback)
                if pareto:
                    for p in pareto:
                        hp, yk, bk, rk, atk, def_, hs, vis_pos, dmg_cost = p
                        new_collected = dict(ent.get('collected', {}))
                        new_collected[fid] = ent.get('collected', {}).get(fid, frozenset()) | vis_pos
                        all_results.append({
                            'hp': hp, 'yk': yk, 'bk': bk, 'rk': rk,
                            'atk': atk, 'def': def_,
                            'collected': new_collected
                        })
                    print(f"    tgt={tgt} -> {len(pareto)} pareto, best HP={pareto[0][0]} ATK={pareto[0][4]}")
                else:
                    print(f"    tgt={tgt} -> NO PATH")
        if not all_results:
            print(f"  [{fid}] FAILED!"); return
        entries = _filter_entries(all_results)

    # 保存Phase1 entries
    phase1_entries = []
    for e in entries:
        pe = dict(e)
        pe['collected'] = {k: v for k, v in e.get('collected', {}).items()}
        phase1_entries.append(pe)

    # === Phase 2: Flyback只收宝石(减伤优先，钥匙药水按需后取) ===
    print("\n=== Phase 2: Flyback宝石 ===")
    flyback_order = ['MT4', 'MT5', 'MT6', 'MT7', 'MT9', 'MT8', 'MT1', 'MT3']
    for fid in flyback_order:
        gem_targets = GEM_ONLY.get(fid, [])
        # 过滤掉Phase1已拿的
        available = []
        for tgt in gem_targets:
            for ent in entries:
                already = ent.get('collected', {}).get(fid, frozenset())
                if fid in FLOOR_13_COLLECTED:
                    already = already | FLOOR_13_COLLECTED[fid]
                if any((b[0], b[1]) not in already and b[3] == tgt for b in maps[fid]['bl']):
                    available.append(tgt)
                    break
        if not available:
            continue
        print(f"\n  [Flyback {fid}] gems={available} {len(entries)} entries...")
        results = do_flyback(maps, entries, fid, available)
        if not results:
            print(f"  [{fid}] no gem results"); continue
        merged = list(results)
        for e in entries:
            dominated = any(
                r['hp'] >= e['hp'] and r['atk'] >= e['atk'] and r['def'] >= e['def'] and
                r['yk'] >= e['yk'] and r['bk'] >= e['bk'] and r['rk'] >= e['rk']
                for r in results
            )
            if not dominated:
                merged.append(e)
        entries = _filter_entries(merged)

    def backfill_key_potion(entries, required_yk=0, required_hp=0):
        """按需补充钥匙和药水: 遍历所有楼层, 搜key+portion直到满足需求
        required_yk: 最低黄钥匙需求, required_hp: 最低HP需求
        返回更新后的entries"""
        print(f"\n  [Backfill] YK>={required_yk} HP>={required_hp}...")
        flyback_order = ['MT4', 'MT5', 'MT6', 'MT7', 'MT9', 'MT8', 'MT1', 'MT3']
        for fid in flyback_order:
            kp_targets = KEY_POTION.get(fid, [])
            # 过滤已拿的
            available = []
            for tgt in kp_targets:
                for ent in entries:
                    already = ent.get('collected', {}).get(fid, frozenset())
                    if fid in FLOOR_13_COLLECTED:
                        already = already | FLOOR_13_COLLECTED[fid]
                    if any((b[0], b[1]) not in already and b[3] == tgt for b in maps[fid]['bl']):
                        available.append(tgt)
                        break
            available = list(dict.fromkeys(available))
            if not available:
                continue
            # 检查是否有entry还需要补充
            needs_supplement = False
            for ent in entries:
                if ent['yk'] < required_yk or ent['hp'] < required_hp:
                    needs_supplement = True; break
            if not needs_supplement:
                break
            print(f"    [Backfill {fid}] targets={available}...")
            results = do_flyback(maps, entries, fid, available)
            if not results:
                continue
            merged = list(results)
            for e in entries:
                dominated = any(
                    r['hp'] >= e['hp'] and r['atk'] >= e['atk'] and r['def'] >= e['def'] and
                    r['yk'] >= e['yk'] and r['bk'] >= e['bk'] and r['rk'] >= e['rk']
                    for r in results
                )
                if not dominated:
                    merged.append(e)
            entries = _filter_entries(merged)
        return entries

    # === Phase 3: MT8 redKey (按需补充钥匙+药水) ===
    print("\n=== Phase 3: MT8 redKey ===")

    def try_redkey(entries):
        all_results = []
        for ent in entries:
            already = ent.get('collected', {}).get('MT8', frozenset())
            has_rk = any((b[0], b[1]) not in already and b[3] == 'redKey'
                         for b in maps['MT8']['bl'])
            if not has_rk: continue
            pareto, iters, _ = search_floor(maps, 'MT8', ent,
                ['yellowKey', 'bluePotion', 'redKey'], max_iter=500000, flyback=True)
            if pareto:
                for p in pareto:
                    hp, yk, bk, rk, atk, def_, hs, vis_pos, dmg_cost = p
                    if rk <= ent['rk'] and not any(
                        (b[0], b[1]) in vis_pos and b[3] == 'redKey'
                        for b in maps['MT8']['bl']
                    ):
                        continue
                    new_collected = dict(ent.get('collected', {}))
                    new_collected['MT8'] = ent.get('collected', {}).get('MT8', frozenset()) | vis_pos
                    all_results.append({
                        'hp': hp, 'yk': yk, 'bk': bk, 'rk': rk,
                        'atk': atk, 'def': def_,
                        'collected': new_collected
                    })
                print(f"    HP={ent['hp']} ATK={ent['atk']} DEF={ent['def']} YK={ent['yk']}"
                      f" -> {len([p for p in pareto if p[3] > ent['rk']])} with redKey")
        return all_results

    rk_results = try_redkey(entries)
    if not rk_results:
        # 按需补充: 需要YK>=2开黄门, 需要足够HP杀yellowGuard
        print("  redKey直接搜失败, 按需补充钥匙+药水...")
        entries = backfill_key_potion(entries, required_yk=2)
        rk_results = try_redkey(entries)
    if rk_results:
        entries = _filter_entries(rk_results)
    else:
        print("  redKey FAILED!"); return

    # === Phase 4: MT10 Boss (按需补充药水) ===
    print("\n=== Phase 4: MT10 ===")

    def try_boss(entries):
        all_results = []
        for ent in entries:
            pareto, iters, _ = search_floor(maps, 'MT10', ent,
                ['skeletonCaptain', 'redGem', 'blueGem', 'bluePotion'])
            if pareto:
                for p in pareto:
                    hp, yk, bk, rk, atk, def_, hs, vis_pos, dmg_cost = p
                    new_collected = dict(ent.get('collected', {}))
                    new_collected['MT10'] = ent.get('collected', {}).get('MT10', frozenset()) | vis_pos
                    all_results.append({
                        'hp': hp, 'yk': yk, 'bk': bk, 'rk': rk,
                        'atk': atk, 'def': def_,
                        'collected': new_collected
                    })
                print(f"    -> {len(pareto)} pareto, best HP={pareto[0][0]} ATK={pareto[0][4]} DEF={pareto[0][5]} RK={pareto[0][3]}")
        return all_results

    boss_results = try_boss(entries)
    if not boss_results:
        # 按需补充药水: Boss战需要足够HP
        print("  Boss直接搜失败, 按需补充药水...")
        entries = backfill_key_potion(entries, required_hp=200)
        boss_results = try_boss(entries)
    if boss_results:
        entries = _filter_entries(boss_results)

    # 最终结果
    print("\n  [Final Results]")
    for i, e in enumerate(entries):
        print(f"  #{i+1}: HP={e['hp']} ATK={e['atk']} DEF={e['def']} "
              f"YK={e['yk']} BK={e['bk']} RK={e['rk']}")

    best = max(entries, key=lambda r: r['hp'])
    print(f"\n  *** 最优: HP={best['hp']} ATK={best['atk']} DEF={best['def']} RK={best['rk']} ***")
    print(f"\n  总耗时: {time.time() - t_start:.1f}s")

def _filter_entries(all_results, min_yk=0):
    items = [(r['hp'], r['yk'], r['bk'], r['rk'], r['atk'], r['def'], r) for r in all_results]
    items.sort(key=lambda x: -x[0])
    pareto_results = []
    for item in items:
        hp, yk, bk, rk, atk, def_, r = item
        # Filter by minimum YK if specified
        if yk < min_yk: continue
        dom = any(p[0] >= hp and p[1] >= yk and p[2] >= bk and p[3] >= rk and
                  p[4] >= atk and p[5] >= def_ and
                  (p[0] > hp or p[1] > yk or p[2] > bk or p[3] > rk or
                   p[4] > atk or p[5] > def_) for p in pareto_results)
        if not dom:
            pareto_results = [p for p in pareto_results if not (
                hp >= p[0] and yk >= p[1] and bk >= p[2] and rk >= p[3] and
                atk >= p[4] and def_ >= p[5] and
                (hp > p[0] or yk > p[1] or bk > p[2] or rk > p[3] or
                 atk > p[4] or def_ > p[5]))]
            pareto_results.append((hp, yk, bk, rk, atk, def_, r))

    entries = []; seen = set()
    def add_entry(pr):
        hp, yk, bk, rk, atk, def_, r = pr
        key = (atk, def_, yk, bk, rk)
        if key not in seen:
            seen.add(key)
            entries.append({'hp': hp, 'atk': atk, 'def': def_,
                            'yk': yk, 'bk': bk, 'rk': rk,
                            'collected': r.get('collected', {})})

    for pr in pareto_results[:16]:
        add_entry(pr)
    if pareto_results:
        add_entry(max(pareto_results, key=lambda p: (p[4], p[0])))
        add_entry(max(pareto_results, key=lambda p: (p[3], p[0])))
        add_entry(max(pareto_results, key=lambda p: (p[1], p[0])))
        add_entry(max(pareto_results, key=lambda p: (p[5], p[0])))
        # 保留YK>=2变体(MT8 redKey需要开3黄门, 需YK>=2)
        yk2_plus = [p for p in pareto_results if p[1] >= 2]
        if yk2_plus:
            add_entry(max(yk2_plus, key=lambda p: (p[0], p[1])))
            add_entry(max(yk2_plus, key=lambda p: (p[4], p[0])))
        # 保留高HP+YK>=1变体
        yk1_plus = [p for p in pareto_results if p[1] >= 1]
        if yk1_plus:
            add_entry(max(yk1_plus, key=lambda p: (p[0], p[1])))

    print(f"  Pareto: {len(pareto_results)}, keeping {len(entries)}")
    for i, e in enumerate(entries):
        ncol = sum(len(v) for v in e.get('collected', {}).values())
        print(f"    #{i+1}: HP={e['hp']} ATK={e['atk']} DEF={e['def']} "
              f"YK={e['yk']} BK={e['bk']} RK={e['rk']} collected={ncol}")
    return entries

if __name__ == '__main__':
    main()
