#!/usr/bin/env python3
"""
生成攻略: 带父节点追踪的Pareto搜索, 反向追踪最优路径再重放每步
dmg=纯战斗伤害 + 7D Pareto + 回溯 + 四阶段
"""
import os, json, time
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT_DIR)

from src.solver.full_search import (
    load_data, search_with_path, search_floor, calc_dmg,
    ENTRANCES, FLYBACK_ENTRANCES, FLOOR_13_COLLECTED, COLLECTIBLES,
    GEM_ONLY, KEY_POTION,
)

hero, maps = load_data()

EID_NAMES = {
    'greenSlime': '绿slime', 'redSlime': '红slime', 'bat': '蝙蝠',
    'skeleton': '骷髅', 'skeletonSoldier': '骷髅士兵',
    'skeletonCaptain': '骷髅队长(Boss)', 'bluePriest': '蓝法师',
    'yellowGuard': '黄卫士', 'soldier': '兵士',
    'yellowDoor': '黄门', 'blueDoor': '蓝门', 'redDoor': '红门',
    'yellowKey': '黄钥匙', 'blueKey': '蓝钥匙', 'redKey': '红钥匙',
    'redGem': '红宝石(ATK+1)', 'blueGem': '蓝宝石(DEF+1)',
    'redPotion': '红药水(+50HP)', 'bluePotion': '蓝药水(+200HP)',
    'sword1': '铁剑(ATK+10)', 'shield1': '铁盾(DEF+10)',
    'upFloor': '上楼', 'downFloor': '下楼', 'fakeWall': '暗墙',
}
FLOOR_NAMES = {
    'MT1': '1楼', 'MT3': '3楼', 'MT4': '4楼', 'MT5': '5楼',
    'MT6': '6楼', 'MT7': '7楼', 'MT8': '8楼', 'MT9': '9楼', 'MT10': '10楼',
}


def state_str(hp, atk, def_, yk, bk, rk):
    return f"HP={hp} ATK={atk} DEF={def_} YK={yk} BK={bk} RK={rk}"


def entry_summary(curr, prev=None):
    total_dmg = curr.get('_dmg', 0)
    prev_dmg = prev.get('_dmg', 0) if prev else 0
    seg_dmg = total_dmg - prev_dmg
    return (
        f"{state_str(curr['hp'], curr['atk'], curr['def'], curr['yk'], curr['bk'], curr['rk'])} "
        f"本段dmg={seg_dmg} 累计dmg={total_dmg}"
    )


def format_step(s, prev=None):
    eid = s['eid']; name = EID_NAMES.get(eid, eid); action = s['action']
    pos = f"({s['x']},{s['y']})"; changes = []
    hp_before = prev['hp_after'] if prev else s['hp_before']
    if hp_before != s['hp_after']: changes.append(f"HP={hp_before}→{s['hp_after']}")
    atk_before = s.get('atk_before', prev['atk'] if prev else s['atk'])
    if atk_before != s['atk']: changes.append(f"ATK={atk_before}→{s['atk']}")
    def_before = s.get('def_before', prev['def'] if prev else s['def'])
    if def_before != s['def']: changes.append(f"DEF={def_before}→{s['def']}")
    yk_before = s.get('yk_before', prev['yk'] if prev else s['yk'])
    if yk_before != s['yk']: changes.append(f"YK={yk_before}→{s['yk']}")
    bk_before = s.get('bk_before', prev['bk'] if prev else s['bk'])
    if bk_before != s['bk']: changes.append(f"BK={bk_before}→{s['bk']}")
    rk_before = s.get('rk_before', prev['rk'] if prev else s.get('rk', 0))
    if rk_before != s.get('rk', 0): changes.append(f"RK={rk_before}→{s['rk']}")
    change_str = (' ' + ' '.join(changes)) if changes else ''
    if action == '通行':
        if eid == 'upFloor': return f"  {pos} 上楼{change_str}"
        elif eid == 'downFloor': return f"  {pos} 下楼{change_str}"
        elif eid == 'fakeWall': return f"  {pos} 穿暗墙{change_str}"
        return f"  {pos} 通过{change_str}"
    elif action == '击杀': return f"  {pos} 击杀{name}{change_str}"
    elif action == '开门': return f"  {pos} 开{name}{change_str}"
    elif action == '拾取': return f"  {pos} 拾取{name}{change_str}"
    return f"  {pos} {action} {name}{change_str}"


def boss_event_damage(atk, def_):
    return 2 * calc_dmg('skeletonSoldier', atk, def_) + 6 * calc_dmg('skeleton', atk, def_)


def expand_mt10_boss_event_steps(steps):
    """MT10 boss event:
    reach (6,5) after red door -> boss moves to (6,1), wall appears at (6,3),
    kill 2 skeleton soldiers + 6 skeletons, then the wall opens and boss can be hit.
    """
    out = []
    for s in steps:
        if s['eid'] == 'redDoor':
            out.append(s)
            hp = s['hp_after']
            atk = s['atk']
            def_ = s['def']
            yk = s['yk']
            bk = s['bk']
            rk = s.get('rk', 0)

            out.append("  (6,5) 触发Boss战: 骷髅队长退到(6,1), (6,3)变为墙")
            event_monsters = [
                (5, 4, 'skeletonSoldier'),
                (7, 4, 'skeletonSoldier'),
                (6, 4, 'skeleton'),
                (5, 5, 'skeleton'),
                (7, 5, 'skeleton'),
                (5, 6, 'skeleton'),
                (6, 6, 'skeleton'),
                (7, 6, 'skeleton'),
            ]
            for x, y, eid in event_monsters:
                dmg = calc_dmg(eid, atk, def_)
                hp_after = hp - dmg
                out.append({
                    'x': x, 'y': y, 'action': '击杀', 'eid': eid,
                    'hp_before': hp, 'hp_after': hp_after,
                    'atk_before': atk, 'def_before': def_,
                    'yk_before': yk, 'bk_before': bk, 'rk_before': rk,
                    'atk': atk, 'def': def_, 'yk': yk, 'bk': bk, 'rk': rk,
                })
                hp = hp_after
            out.append("  (6,3) 事件门开启")
            boss_dmg = calc_dmg('skeletonCaptain', atk, def_)
            out.append({
                'x': 6, 'y': 1, 'action': '击杀', 'eid': 'skeletonCaptain',
                'hp_before': hp, 'hp_after': hp - boss_dmg,
                'atk_before': atk, 'def_before': def_,
                'yk_before': yk, 'bk_before': bk, 'rk_before': rk,
                'atk': atk, 'def': def_, 'yk': yk, 'bk': bk, 'rk': rk,
            })
            continue

        if s['eid'] != 'skeletonCaptain':
            out.append(s)
            continue

        hp = s['hp_before']
        atk = s.get('atk_before', s['atk'])
        def_ = s.get('def_before', s['def'])
        yk = s.get('yk_before', s['yk'])
        bk = s.get('bk_before', s['bk'])
        rk = s.get('rk_before', s.get('rk', 0))

        out.append("  (6,5) 触发Boss战: 骷髅队长退到(6,1), (6,3)变为墙")
        event_monsters = [
            (5, 4, 'skeletonSoldier'),
            (7, 4, 'skeletonSoldier'),
            (6, 4, 'skeleton'),
            (5, 5, 'skeleton'),
            (7, 5, 'skeleton'),
            (5, 6, 'skeleton'),
            (6, 6, 'skeleton'),
            (7, 6, 'skeleton'),
        ]
        prev = None
        for x, y, eid in event_monsters:
            dmg = calc_dmg(eid, atk, def_)
            hp_after = hp - dmg
            ev = {
                'x': x, 'y': y, 'action': '击杀', 'eid': eid,
                'hp_before': hp, 'hp_after': hp_after,
                'atk_before': atk, 'def_before': def_,
                'yk_before': yk, 'bk_before': bk, 'rk_before': rk,
                'atk': atk, 'def': def_, 'yk': yk, 'bk': bk, 'rk': rk,
            }
            out.append(ev)
            hp = hp_after
            prev = ev
        out.append("  (6,3) 事件门开启")

        boss_dmg = calc_dmg('skeletonCaptain', atk, def_)
        out.append({
            'x': 6, 'y': 1, 'action': '击杀', 'eid': 'skeletonCaptain',
            'hp_before': hp, 'hp_after': hp - boss_dmg,
            'atk_before': atk, 'def_before': def_,
            'yk_before': yk, 'bk_before': bk, 'rk_before': rk,
            'atk': atk, 'def': def_, 'yk': yk, 'bk': bk, 'rk': rk,
        })
    return out


_entry_store = {}
_next_id = [0]
PHASE1_BUCKETS_ENABLED = True
USE_DOOR_COST_PARETO = True

DOOR_COST_FIELDS = (
    ('_yd', 'yellowDoor'),
    ('_bd', 'blueDoor'),
    ('_rd', 'redDoor'),
)


def door_cost_from_positions(fid, positions):
    if not positions:
        return 0, 0, 0
    door_by_pos = {
        (b[0], b[1]): b[3]
        for b in maps.get(fid, {}).get('bl', [])
        if b[3] in {'yellowDoor', 'blueDoor', 'redDoor'}
    }
    yd = bd = rd = 0
    for pos in positions:
        eid = door_by_pos.get(pos)
        if eid == 'yellowDoor':
            yd += 1
        elif eid == 'blueDoor':
            bd += 1
        elif eid == 'redDoor':
            rd += 1
    return yd, bd, rd


def door_cost_from_collected(collected):
    yd = bd = rd = 0
    for fid, positions in (collected or {}).items():
        dy, db, dr = door_cost_from_positions(fid, positions)
        yd += dy
        bd += db
        rd += dr
    return yd, bd, rd


def door_cost_str(e):
    return f"doorY/B/R={e.get('_yd', 0)}/{e.get('_bd', 0)}/{e.get('_rd', 0)}"


def entry_summary(curr, prev=None):
    total_dmg = curr.get('_dmg', 0)
    prev_dmg = prev.get('_dmg', 0) if prev else 0
    seg_dmg = total_dmg - prev_dmg
    return (
        f"{state_str(curr['hp'], curr['atk'], curr['def'], curr['yk'], curr['bk'], curr['rk'])} "
        f"seg_dmg={seg_dmg} total_dmg={total_dmg} {door_cost_str(curr)}"
    )

PHASE1_FUTURE_KEY_POS = {
    'MT7': frozenset([(9, 10), (9, 11), (9, 1), (9, 2), (5, 10), (5, 11)]),
    'MT6': frozenset([(9, 1)]),
    'MT9': frozenset([(9, 9), (1, 7), (5, 7)]),
}


def phase1_future_key_score(r):
    collected = r.get('collected', {}) or {}
    score = 0
    for fid, positions in PHASE1_FUTURE_KEY_POS.items():
        used = collected.get(fid, frozenset())
        score += sum(1 for pos in positions if pos not in used)
    return score


def initial_collected_state():
    """Resources consumed on fixed 1-3F before the 4F search starts."""
    return {fid: frozenset(pos_set) for fid, pos_set in FLOOR_13_COLLECTED.items()}

def _make_result(hp, yk, bk, rk, atk, def_, collected, parent_id, step_info, dmg_cost=0):
    parent = _entry_store.get(parent_id)
    total_dmg = (parent.get('_dmg', 0) if parent else 0) + dmg_cost
    parent_yd = parent.get('_yd', 0) if parent else 0
    parent_bd = parent.get('_bd', 0) if parent else 0
    parent_rd = parent.get('_rd', 0) if parent else 0
    yd_cost = bd_cost = rd_cost = 0
    if parent and step_info:
        fid = step_info[0]
        before = parent.get('collected', {}).get(fid, frozenset())
        after = collected.get(fid, frozenset())
        yd_cost, bd_cost, rd_cost = door_cost_from_positions(fid, after - before)
    total_yd = parent_yd + yd_cost
    total_bd = parent_bd + bd_cost
    total_rd = parent_rd + rd_cost
    _next_id[0] += 1; eid = _next_id[0]
    r = {'hp': hp, 'yk': yk, 'bk': bk, 'rk': rk, 'atk': atk, 'def': def_,
         'collected': collected, '_id': eid, '_parent_id': parent_id,
         '_step_info': step_info, '_dmg': total_dmg,
         '_yd': total_yd, '_bd': total_bd, '_rd': total_rd}
    _entry_store[eid] = {'hp': hp, 'atk': atk, 'def': def_, 'yk': yk, 'bk': bk, 'rk': rk,
                          'collected': {k: v for k, v in collected.items()},
                          '_id': eid, '_parent_id': parent_id, '_step_info': step_info,
                          '_dmg': total_dmg, '_yd': total_yd, '_bd': total_bd, '_rd': total_rd}
    return r

def _collected_signature(r):
    collected = r.get('collected', {}) or {}
    return tuple(
        (fid, tuple(sorted(pos)))
        for fid, pos in sorted(collected.items())
        if pos
    )


def _filter_entries_tracked_legacy(all_results, retry_level=0):
    """Legacy Pareto by cumulative dmg + 5 resources, scoped by collected signature.

    HP is not a long-term optimization dimension.  It is used by floor search
    for survival, and here only as a tie-break when cumulative dmg and all
    resource dimensions are identical within the same collected signature.
    """
    items = []
    for r in all_results:
        dmg = r.get('_dmg', 0)
        sig = _collected_signature(r)
        items.append((dmg, r['hp'], r['atk'], r['def'], r['yk'], r['bk'], r['rk'], sig, r))

    groups = {}
    for item in items:
        groups.setdefault(item[7], []).append(item)

    pareto_results = []
    for group in groups.values():
        group.sort(key=lambda x: (x[0], -x[1], -x[4]))
        local = []
        for item in group:
            dmg, hp, atk, def_, yk, bk, rk, sig, r = item
            def dominates(a, b):
                ad, ahp, aatk, adef, ayk, abk, ark = a[:7]
                bd, bhp, batk, bdef, byk, bbk, brk = b[:7]
                if not (ad <= bd and aatk >= batk and adef >= bdef and
                        ayk >= byk and abk >= bbk and ark >= brk):
                    return False
                core_strict = (
                    ad < bd or aatk > batk or adef > bdef or
                    ayk > byk or abk > bbk or ark > brk
                )
                same_core = (
                    ad == bd and aatk == batk and adef == bdef and
                    ayk == byk and abk == bbk and ark == brk
                )
                return core_strict or (same_core and ahp >= bhp)

            dom = any(dominates(p, item) for p in local)
            if not dom:
                local = [p for p in local if not dominates(item, p)]
                local.append(item)
        pareto_results.extend(local)

    entries = []
    seen = set()

    def add_entry(pr, tag=''):
        dmg, hp, atk, def_, yk, bk, rk, sig, r = pr
        key = (atk, def_, yk, bk, rk, sig, tag)
        if key in seen:
            return
        seen.add(key)
        e = {'hp': hp, 'atk': atk, 'def': def_, 'yk': yk, 'bk': bk, 'rk': rk,
             'collected': r.get('collected', {}), '_dmg': dmg}
        if '_id' in r:
            e['_id'] = r['_id']
        if '_parent_id' in r:
            e['_parent_id'] = r['_parent_id']
        if '_step_info' in r:
            e['_step_info'] = r['_step_info']
        entries.append(e)

    N = 12 + retry_level * 2
    if pareto_results:
        for key_fn in [
            lambda p: (-p[0], p[1]),
            lambda p: (p[2], -p[0], p[1]),
            lambda p: (p[3], -p[0], p[1]),
            lambda p: (p[4], -p[0], p[1]),
            lambda p: (p[5], -p[0], p[1]),
            lambda p: (p[6], -p[0], p[1]),
        ]:
            for pr in sorted(pareto_results, key=key_fn, reverse=True)[:N]:
                add_entry(pr)

    strategic_specs = [
        ('mt10_any', lambda r: 'MT10' in r.get('collected', {})),
        ('mt10_left', lambda r: frozenset([(1, 9), (3, 9)]) <= r.get('collected', {}).get('MT10', frozenset())),
        ('mt10_right', lambda r: frozenset([(9, 9), (11, 9)]) <= r.get('collected', {}).get('MT10', frozenset())),
        ('mt10_res', lambda r: frozenset([(2, 6), (10, 6), (11, 11)]) <= r.get('collected', {}).get('MT10', frozenset())),
        ('phase1_bat_threshold', lambda r: r['atk'] >= 21 and r['yk'] >= 5 and (7, 10) in r.get('collected', {}).get('MT4', frozenset())),
        ('phase1_lowdef_keyline', lambda r: 21 <= r['atk'] <= 22 and r['def'] <= 10 and r['yk'] >= 3),
        ('phase1_mt7_redgem', lambda r: (3, 1) in r.get('collected', {}).get('MT7', frozenset())),
        ('phase1_shield_keyline', lambda r: 22 <= r['atk'] <= 23 and 20 <= r['def'] <= 21 and r['yk'] >= 2 and (9, 7) in r.get('collected', {}).get('MT9', frozenset())),
        ('phase1_mt9_shield_gems', lambda r: frozenset([(9, 7), (6, 5), (1, 5)]) <= r.get('collected', {}).get('MT9', frozenset())),
        ('stat27', lambda r: r['atk'] >= 27 and r['def'] >= 27),
        ('stat27_ready', lambda r: r['atk'] >= 27 and r['def'] >= 27 and r['yk'] >= 3),
        ('mt10_gem_budget', lambda r: r['atk'] >= 26 and r['def'] >= 26 and r['yk'] >= 5 and r['bk'] >= 1 and 'MT10' not in r.get('collected', {})),
        ('mt10_inside_budget', lambda r: r['atk'] >= 26 and r['def'] >= 26 and r['yk'] >= 4 and 'MT10' in r.get('collected', {})),
    ]
    for tag, pred in strategic_specs:
        tagged = [pr for pr in pareto_results if pred(pr[8])]
        if not tagged:
            continue
        for key_fn in [
            lambda p: (-p[0], p[4], p[2], p[3], p[1]),
            lambda p: (p[4], -p[0], p[2], p[3], p[1]),
            lambda p: (p[2], p[3], -p[0], p[4], p[1]),
        ]:
            for pr in sorted(tagged, key=key_fn, reverse=True)[:N]:
                add_entry(pr, tag)

    for yk_value in range(8):
        stat_yk = [pr for pr in pareto_results
                   if pr[2] >= 27 and pr[3] >= 27 and pr[4] == yk_value]
        for pr in sorted(stat_yk, key=lambda p: (-p[0], p[1]), reverse=True)[:4]:
            add_entry(pr, f'stat27_yk{yk_value}')

    # Keep key-balance variants while climbing from 24/24 to 27/27. These
    # states are often numerically worse than low-key/high-HP states, but they
    # are the only branches that can still pay for MT8 red key and MT10 boss
    # doors after the final gems.
    for atk_min, def_min in [(24, 24), (25, 24), (24, 25), (25, 25), (26, 25), (25, 26), (26, 26)]:
        for yk_value in range(10):
            near = [pr for pr in pareto_results
                    if pr[2] >= atk_min and pr[3] >= def_min and pr[4] == yk_value]
            if not near:
                continue
            for pr in sorted(near, key=lambda p: (p[2] + p[3], -p[0], p[1]), reverse=True)[:3]:
                add_entry(pr, f'near{atk_min}_{def_min}_yk{yk_value}')
            for pr in sorted(near, key=lambda p: (-p[0], p[2] + p[3], p[1]), reverse=True)[:2]:
                add_entry(pr, f'nearhp{atk_min}_{def_min}_yk{yk_value}')

    for yk_value in range(10):
        boss_ready = [pr for pr in pareto_results
                      if pr[6] >= 1 and pr[2] >= 26 and pr[3] >= 25 and pr[4] == yk_value]
        if not boss_ready:
            continue
        for pr in sorted(boss_ready, key=lambda p: (-p[0], p[2] + p[3], p[1]), reverse=True)[:5]:
            add_entry(pr, f'boss_hp_yk{yk_value}')
        for pr in sorted(boss_ready, key=lambda p: (p[4], -p[0], p[2] + p[3], p[1]), reverse=True)[:5]:
            add_entry(pr, f'boss_key_yk{yk_value}')

    budget_ready = [
        pr for pr in pareto_results
        if pr[2] >= 26 and pr[3] >= 26 and pr[4] >= 5 and pr[5] >= 1 and
        'MT10' not in pr[8].get('collected', {})
    ]
    for pr in sorted(budget_ready, key=lambda p: (p[4], p[5], -p[0], p[1]), reverse=True)[:16]:
        add_entry(pr, 'mt10_budget_pre')
    inside_budget = [
        pr for pr in pareto_results
        if pr[2] >= 26 and pr[3] >= 26 and pr[4] >= 4 and
        'MT10' in pr[8].get('collected', {})
    ]
    for pr in sorted(inside_budget, key=lambda p: (p[4], -p[0], p[1]), reverse=True)[:16]:
        add_entry(pr, 'mt10_budget_inside')

    if PHASE1_BUCKETS_ENABLED:
        # Phase1 has several low-stat but key-critical branches.  Keep the best
        # HP representative for small ATK/DEF/YK/BK buckets so a route that
        # preserves the blue key is not crowded out by higher-stat branches that
        # spent it.  This is intentionally disabled after Phase1.
        phase1_defs = [10, 11, 12, 20, 21, 22, 23]
        for atk_value in range(21, 25):
            for def_value in phase1_defs:
                for yk_value in range(8):
                    for bk_value in range(3):
                        bucket = [
                            pr for pr in pareto_results
                            if pr[2] == atk_value and pr[3] == def_value and
                            pr[4] == yk_value and pr[5] == bk_value and pr[6] == 0 and
                            'MT10' not in pr[8].get('collected', {})
                        ]
                        for pr in sorted(bucket, key=lambda p: (-p[0], p[1]), reverse=True)[:2]:
                            add_entry(pr, f'phase1_{atk_value}_{def_value}_{yk_value}_{bk_value}')
                        for pr in sorted(
                            bucket,
                            key=lambda p: (
                                phase1_future_key_score(p[8]),
                                -p[0],
                                p[1],
                            ),
                            reverse=True,
                        )[:2]:
                            add_entry(pr, f'phase1_future_{atk_value}_{def_value}_{yk_value}_{bk_value}')

    return entries


def _filter_entries_tracked(all_results, retry_level=0):
    """Pareto by cumulative dmg, cumulative door use, current keys, and stats.

    Current keys stay as positive reachability resources.  Door counters are
    cumulative irreversible costs; they prevent a key-heavy route that spent
    more doors from crowding out a lower-consumption route.
    """
    items = []
    for r in all_results:
        yd = r.get('_yd', 0)
        bd = r.get('_bd', 0)
        rd = r.get('_rd', 0)
        cmp_yd, cmp_bd, cmp_rd = (yd, bd, rd) if USE_DOOR_COST_PARETO else (0, 0, 0)
        sig = _collected_signature(r)
        items.append((
            r.get('_dmg', 0), cmp_yd, cmp_bd, cmp_rd,
            r['hp'], r['atk'], r['def'], r['yk'], r['bk'], r['rk'],
            sig, r,
        ))

    groups = {}
    for item in items:
        groups.setdefault(item[10], []).append(item)

    def cost_hp_key(p):
        return (p[0], p[1], p[2], p[3], -p[4])

    pareto_results = []
    for group in groups.values():
        group.sort(key=cost_hp_key)
        local = []

        def dominates(a, b):
            ad, ayd, abd, ard, ahp, aatk, adef, ayk, abk, ark = a[:10]
            bdmg, byd, bbd, brd, bhp, batk, bdef, byk, bbk, brk = b[:10]
            if not (
                ad <= bdmg and ayd <= byd and abd <= bbd and ard <= brd and
                aatk >= batk and adef >= bdef and
                ayk >= byk and abk >= bbk and ark >= brk
            ):
                return False
            core_strict = (
                ad < bdmg or ayd < byd or abd < bbd or ard < brd or
                aatk > batk or adef > bdef or
                ayk > byk or abk > bbk or ark > brk
            )
            same_core = (
                ad == bdmg and ayd == byd and abd == bbd and ard == brd and
                aatk == batk and adef == bdef and
                ayk == byk and abk == bbk and ark == brk
            )
            return core_strict or (same_core and ahp >= bhp)

        for item in group:
            if any(dominates(p, item) for p in local):
                continue
            local = [p for p in local if not dominates(item, p)]
            local.append(item)
        pareto_results.extend(local)

    entries = []
    seen = set()

    def add_entry(pr, tag=''):
        dmg, _cmp_yd, _cmp_bd, _cmp_rd, hp, atk, def_, yk, bk, rk, sig, r = pr
        actual_yd = r.get('_yd', 0)
        actual_bd = r.get('_bd', 0)
        actual_rd = r.get('_rd', 0)
        key = (atk, def_, yk, bk, rk, actual_yd, actual_bd, actual_rd, sig, tag)
        if key in seen:
            return
        seen.add(key)
        e = {
            'hp': hp, 'atk': atk, 'def': def_, 'yk': yk, 'bk': bk, 'rk': rk,
            'collected': r.get('collected', {}), '_dmg': dmg,
            '_yd': actual_yd, '_bd': actual_bd, '_rd': actual_rd,
        }
        for k in ('_id', '_parent_id', '_step_info', '_source'):
            if k in r:
                e[k] = r[k]
        entries.append(e)

    N = 12 + retry_level * 2
    if pareto_results:
        selectors = [
            cost_hp_key,
            lambda p: (-p[5], p[0], p[1], p[2], p[3], -p[4]),
            lambda p: (-p[6], p[0], p[1], p[2], p[3], -p[4]),
            lambda p: (-p[7], p[0], p[1], p[2], p[3], -p[4]),
            lambda p: (-p[8], p[0], p[1], p[2], p[3], -p[4]),
            lambda p: (-p[9], p[0], p[1], p[2], p[3], -p[4]),
        ]
        for key_fn in selectors:
            for pr in sorted(pareto_results, key=key_fn)[:N]:
                add_entry(pr)

    strategic_specs = [
        ('mt10_any', lambda r: 'MT10' in r.get('collected', {})),
        ('mt10_left', lambda r: frozenset([(1, 9), (3, 9)]) <= r.get('collected', {}).get('MT10', frozenset())),
        ('mt10_right', lambda r: frozenset([(9, 9), (11, 9)]) <= r.get('collected', {}).get('MT10', frozenset())),
        ('mt10_res', lambda r: frozenset([(2, 6), (10, 6), (11, 11)]) <= r.get('collected', {}).get('MT10', frozenset())),
        ('phase1_bat_threshold', lambda r: r['atk'] >= 21 and r['yk'] >= 5 and (7, 10) in r.get('collected', {}).get('MT4', frozenset())),
        ('phase1_lowdef_keyline', lambda r: 21 <= r['atk'] <= 22 and r['def'] <= 10 and r['yk'] >= 3),
        ('phase1_mt7_redgem', lambda r: (3, 1) in r.get('collected', {}).get('MT7', frozenset())),
        ('phase1_shield_keyline', lambda r: 22 <= r['atk'] <= 23 and 20 <= r['def'] <= 21 and r['yk'] >= 2 and (9, 7) in r.get('collected', {}).get('MT9', frozenset())),
        ('phase1_mt9_shield_gems', lambda r: frozenset([(9, 7), (6, 5), (1, 5)]) <= r.get('collected', {}).get('MT9', frozenset())),
        ('stat27', lambda r: r['atk'] >= 27 and r['def'] >= 27),
        ('stat27_ready', lambda r: r['atk'] >= 27 and r['def'] >= 27 and r['yk'] >= 3),
        ('mt10_gem_budget', lambda r: r['atk'] >= 26 and r['def'] >= 26 and r['yk'] >= 5 and r['bk'] >= 1 and 'MT10' not in r.get('collected', {})),
        ('mt10_inside_budget', lambda r: r['atk'] >= 26 and r['def'] >= 26 and r['yk'] >= 4 and 'MT10' in r.get('collected', {})),
    ]
    strategic_selectors = [
        lambda p: (p[0], p[1], p[2], p[3], -p[7], -p[5], -p[6], -p[4]),
        lambda p: (-p[7], -p[8], p[0], p[1], p[2], p[3], -p[4]),
        lambda p: (-(p[5] + p[6]), p[0], p[1], p[2], p[3], -p[7], -p[4]),
    ]
    for tag, pred in strategic_specs:
        tagged = [pr for pr in pareto_results if pred(pr[11])]
        if not tagged:
            continue
        for key_fn in strategic_selectors:
            for pr in sorted(tagged, key=key_fn)[:N]:
                add_entry(pr, tag)

    for yk_value in range(8):
        stat_yk = [pr for pr in pareto_results
                   if pr[5] >= 27 and pr[6] >= 27 and pr[7] == yk_value]
        for pr in sorted(stat_yk, key=cost_hp_key)[:4]:
            add_entry(pr, f'stat27_yk{yk_value}')

    for atk_min, def_min in [(24, 24), (25, 24), (24, 25), (25, 25), (26, 25), (25, 26), (26, 26)]:
        for yk_value in range(10):
            near = [pr for pr in pareto_results
                    if pr[5] >= atk_min and pr[6] >= def_min and pr[7] == yk_value]
            if not near:
                continue
            for pr in sorted(near, key=lambda p: (-(p[5] + p[6]), p[0], p[1], p[2], p[3], -p[4]))[:3]:
                add_entry(pr, f'near{atk_min}_{def_min}_yk{yk_value}')
            for pr in sorted(near, key=cost_hp_key)[:2]:
                add_entry(pr, f'nearhp{atk_min}_{def_min}_yk{yk_value}')

    for yk_value in range(10):
        boss_ready = [pr for pr in pareto_results
                      if pr[9] >= 1 and pr[5] >= 26 and pr[6] >= 25 and pr[7] == yk_value]
        if not boss_ready:
            continue
        for pr in sorted(boss_ready, key=lambda p: (-(p[5] + p[6]), p[0], p[1], p[2], p[3], -p[4]))[:5]:
            add_entry(pr, f'boss_hp_yk{yk_value}')
        for pr in sorted(boss_ready, key=lambda p: (-p[7], p[0], p[1], p[2], p[3], -p[4]))[:5]:
            add_entry(pr, f'boss_key_yk{yk_value}')

    budget_ready = [
        pr for pr in pareto_results
        if pr[5] >= 26 and pr[6] >= 26 and pr[7] >= 5 and pr[8] >= 1 and
        'MT10' not in pr[11].get('collected', {})
    ]
    for pr in sorted(budget_ready, key=lambda p: (-p[7], -p[8], p[0], p[1], p[2], p[3], -p[4]))[:16]:
        add_entry(pr, 'mt10_budget_pre')
    inside_budget = [
        pr for pr in pareto_results
        if pr[5] >= 26 and pr[6] >= 26 and pr[7] >= 4 and
        'MT10' in pr[11].get('collected', {})
    ]
    for pr in sorted(inside_budget, key=lambda p: (-p[7], p[0], p[1], p[2], p[3], -p[4]))[:16]:
        add_entry(pr, 'mt10_budget_inside')

    if PHASE1_BUCKETS_ENABLED:
        phase1_defs = [10, 11, 12, 20, 21, 22, 23]
        for atk_value in range(21, 25):
            for def_value in phase1_defs:
                for yk_value in range(8):
                    for bk_value in range(3):
                        bucket = [
                            pr for pr in pareto_results
                            if pr[5] == atk_value and pr[6] == def_value and
                            pr[7] == yk_value and pr[8] == bk_value and pr[9] == 0 and
                            'MT10' not in pr[11].get('collected', {})
                        ]
                        for pr in sorted(bucket, key=cost_hp_key)[:2]:
                            add_entry(pr, f'phase1_{atk_value}_{def_value}_{yk_value}_{bk_value}')
                        for pr in sorted(
                            bucket,
                            key=lambda p: (
                                -phase1_future_key_score(p[11]),
                                p[0], p[1], p[2], p[3], -p[4],
                            ),
                        )[:2]:
                            add_entry(pr, f'phase1_future_{atk_value}_{def_value}_{yk_value}_{bk_value}')

    return entries


def run_search(retry_level=0, initial_entry=None, skip_phase1=False, result_objective='hp'):
    global PHASE1_BUCKETS_ENABLED
    _entry_store.clear(); _next_id[0] = 0
    print(f"  [run_search retry={retry_level}]", flush=True)
    PHASE1_BUCKETS_ENABLED = not skip_phase1
    if initial_entry is None:
        start = {'hp': hero['h'], 'atk': hero['a'], 'def': hero['d'],
                 'yk': hero['yk'], 'bk': hero['bk'], 'rk': 0, 'collected': initial_collected_state(),
                 '_id': 1, '_parent_id': None, '_step_info': None,
                 '_dmg': 0, '_yd': 0, '_bd': 0, '_rd': 0}
    else:
        start = dict(initial_entry)
        start['_id'] = 1
        start['_parent_id'] = None
        start['_step_info'] = None
        start.setdefault('_dmg', 0)
        start.setdefault('_yd', 0)
        start.setdefault('_bd', 0)
        start.setdefault('_rd', 0)
    _next_id[0] = 1; _entry_store[1] = dict(start)
    entries = [start.copy()]

    # Phase1: 里程碑 + 关键flyback (老结构, 已验证)
    milestones = [
        ('MT4', ['upFloor'], False),
        ('MT5', ['sword1'], False),
        # 剑后先回4楼拿红宝石，达到蝙蝠2刀阈值(ATK 21)，并补足钥匙。
        ('MT4', ['redGem', 'yellowKey', 'redPotion'], True),
        ('MT5', ['upFloor'], True),
        ('MT6', ['upFloor'], False),
        # 7楼红宝石要在8楼前拿，才能降低骷髅士兵/后续怪的损耗。
        ('MT7', ['redGem', 'redPotion'], False),
        ('MT7', ['upFloor'], False),
        ('MT8', ['upFloor'], False),
        ('MT9', ['shield1'], False),
        # 拿盾后顺手保留9楼红蓝宝石开局，作为后续27/27阶段的强前缀。
        ('MT9', ['redGem', 'blueGem', 'yellowKey'], True),
    ]
    if not skip_phase1:
        for fid, targets, force_flyback in milestones:
            all_results = []
            if len(targets) > 1:
                for ent in entries:
                    already = ent.get('collected', {}).get(fid, frozenset())
                    if fid in FLOOR_13_COLLECTED: already |= FLOOR_13_COLLECTED[fid]
                    is_fb = force_flyback or fid in ent.get('collected', {})
                    pareto, _, _ = search_floor(maps, fid, ent, targets, flyback=is_fb)
                    if pareto:
                        for hp, yk, bk, rk, atk, def_, hs, vis, dc in pareto:
                            nc = dict(ent.get('collected', {})); nc[fid] = already | vis
                            all_results.append(_make_result(hp,yk,bk,rk,atk,def_,nc,ent['_id'],(fid,targets,is_fb),dmg_cost=dc))
            else:
                for tgt in targets:
                    for ent in entries:
                        already = ent.get('collected', {}).get(fid, frozenset())
                        if fid in FLOOR_13_COLLECTED: already |= FLOOR_13_COLLECTED[fid]
                        if tgt != 'upFloor' and not any(
                            (b[0],b[1]) not in already and b[3]==tgt for b in maps[fid]['bl']): continue
                        is_fb = force_flyback or fid in ent.get('collected', {})
                        pareto, _, _ = search_floor(maps, fid, ent, [tgt], flyback=is_fb)
                        if pareto:
                            for hp, yk, bk, rk, atk, def_, hs, vis, dc in pareto:
                                nc = dict(ent.get('collected', {})); nc[fid] = already | vis
                                all_results.append(_make_result(hp,yk,bk,rk,atk,def_,nc,ent['_id'],(fid,[tgt],is_fb),dmg_cost=dc))
            if not all_results:
                e0 = entries[0] if entries else {}
                print(f"  FAIL Phase1 {fid} (HP={e0.get('hp')} ATK={e0.get('atk')})"); return None
            entries = _filter_entries_tracked(all_results, retry_level)

    PHASE1_BUCKETS_ENABLED = False

    def merge(e, r): return _filter_entries_tracked(list(r) + e, retry_level)
    # Keep MT10 out of the early wide gem sweep. It is still considered as a
    # normal gem floor in ensure_stats_27(), where the candidate set is already
    # shaped by the 27/27 target and key budget.
    flyback_order = ['MT7','MT6','MT3','MT1','MT9','MT4','MT8','MT5']

    def debug_entries(label, ents, limit=4):
        if not ents:
            print(f"  [{label}] no entries", flush=True)
            return
        ordered = sorted(
            ents,
            key=lambda e: (
                e.get('_dmg', 0),
                e.get('_yd', 0),
                e.get('_bd', 0),
                e.get('_rd', 0),
                -e['atk'],
                -e['def'],
                -e['yk'],
                -e['bk'],
                -e['rk'],
                -e['hp'],
            ),
        )[:limit]
        text = "; ".join(
            f"DMG={e.get('_dmg',0)} HP={e['hp']} ATK={e['atk']} DEF={e['def']} "
            f"YK={e['yk']} BK={e['bk']} RK={e['rk']} {door_cost_str(e)}"
            for e in ordered
        )
        print(f"  [{label}] {len(ents)} entries: {text}", flush=True)

    def do_flyback(ents, fid, targets, multi=True, max_iter=500000):
        res = []
        if multi:
            for ent in ents:
                al = ent.get('collected',{}).get(fid,frozenset())
                if fid in FLOOR_13_COLLECTED: al |= FLOOR_13_COLLECTED[fid]
                is_fb = fid in ent.get('collected',{})
                pareto, _, _ = search_floor(maps, fid, ent, targets, max_iter=max_iter, flyback=is_fb)
                if pareto:
                    for hp,yk,bk,rk,atk,def_,hs,vis,dc in pareto:
                        nc = dict(ent.get('collected',{})); nc[fid] = al | vis
                        res.append(_make_result(hp,yk,bk,rk,atk,def_,nc,ent['_id'],(fid,targets,is_fb),dmg_cost=dc))
        else:
            for tgt in targets:
                for ent in ents:
                    al = ent.get('collected',{}).get(fid,frozenset())
                    if fid in FLOOR_13_COLLECTED: al |= FLOOR_13_COLLECTED[fid]
                    if not any((b[0],b[1]) not in al and b[3]==tgt for b in maps[fid]['bl']): continue
                    is_fb = fid in ent.get('collected',{})
                    pareto, _, _ = search_floor(maps, fid, ent, [tgt], max_iter=max_iter, flyback=is_fb)
                    if pareto:
                        for hp,yk,bk,rk,atk,def_,hs,vis,dc in pareto:
                            nc = dict(ent.get('collected',{})); nc[fid] = al | vis
                            res.append(_make_result(hp,yk,bk,rk,atk,def_,nc,ent['_id'],(fid,[tgt],is_fb),dmg_cost=dc))
        return res

    def do_key_backfill(ents, fid, targets):
        """Collect key/potion targets one at a time.

        Multi-target floor search may exit after any target and later return a
        branch that looks cheap but does not preserve the key budget needed for
        MT10/red-key.  Key backfill is only called after a concrete shortage,
        so keep separate yellow-key / blue-key / potion variants here.
        """
        return do_flyback(ents, fid, targets, multi=False)

    def key_improvements(results, keep_pred=None):
        kept = []
        for r in results:
            parent = _entry_store.get(r.get('_parent_id'), {})
            key_gain = (
                r['yk'] > parent.get('yk', -1) or
                r['bk'] > parent.get('bk', -1) or
                r['rk'] > parent.get('rk', -1)
            )
            potion_without_key_loss = (
                r['hp'] > parent.get('hp', 10**9) and
                r['yk'] >= parent.get('yk', 0) and
                r['bk'] >= parent.get('bk', 0) and
                r['rk'] >= parent.get('rk', 0)
            )
            if key_gain or potion_without_key_loss or (keep_pred and keep_pred(r)):
                kept.append(r)
        return kept

    def target_available(ent, fid, target):
        al = ent.get('collected',{}).get(fid,frozenset())
        if fid in FLOOR_13_COLLECTED:
            al |= FLOOR_13_COLLECTED[fid]
        return any((b[0], b[1]) not in al and b[3] == target for b in maps[fid]['bl'])

    def target_allowed(ent, fid, target):
        # MT5 blue gem is guarded by a skeleton soldier. At ATK 26 the fight
        # crosses a useful round threshold, so do not pull this gem early.
        if fid == 'MT5' and target == 'blueGem' and ent['atk'] < 26:
            return False
        # MT10 is executed through the real MT9 up-floor wrapper. Budget the
        # requested target, not the whole floor: the verified baseline first
        # takes only the left blue gem, refills elsewhere, then returns for the
        # right red gem/potion.
        if fid == 'MT10' and 'MT10' not in ent.get('collected', {}):
            if target == 'blueGem':
                if ent['bk'] < 1 or ent['yk'] < 2:
                    return False
            elif target == 'redGem':
                if ent['bk'] < 1 or ent['yk'] < 4:
                    return False
            elif target == 'bluePotion':
                if ent['bk'] < 1 or ent['yk'] < 4:
                    return False
            else:
                if ent['bk'] < 1 or ent['yk'] < 2:
                    return False
        return True

    def collect_single_target(ents, fid, target):
        sources = [
            ent for ent in ents
            if target_allowed(ent, fid, target) and target_available(ent, fid, target)
        ]
        if not sources:
            return []
        if fid == 'MT1' and target in {'redGem', 'blueGem'}:
            bundled = [
                ent for ent in sources
                if target_available(ent, 'MT1', 'redGem') and target_available(ent, 'MT1', 'blueGem')
            ]
            if bundled:
                r = collect_required_targets(bundled, 'MT1', ['redGem', 'blueGem'])
                if r:
                    return r
        if fid == 'MT10':
            return collect_mt10_single_target(sources, target)
        return do_flyback(sources, fid, [target], multi=False)

    def collect_required_targets(ents, fid, targets):
        res = []
        required = frozenset(
            (b[0], b[1]) for b in maps[fid]['bl'] if b[3] in set(targets)
        )
        for ent in ents:
            al = ent.get('collected',{}).get(fid,frozenset())
            if fid in FLOOR_13_COLLECTED:
                al |= FLOOR_13_COLLECTED[fid]
            missing = required - al
            if not missing:
                continue
            is_fb = fid in ent.get('collected',{})
            pareto, _, _ = search_floor(maps, fid, ent, targets, flyback=is_fb)
            if not pareto:
                continue
            for hp,yk,bk,rk,atk,def_,hs,vis,dc in pareto:
                if not missing <= vis:
                    continue
                nc = dict(ent.get('collected',{})); nc[fid] = al | vis
                res.append(_make_result(hp,yk,bk,rk,atk,def_,nc,ent['_id'],
                    (fid,targets,is_fb), dmg_cost=dc))
        return res

    def collect_gems_defense_first(ents, floor_order):
        """Keep blue-gem-first variants before costly red-gem branches."""
        current = ents
        for target, order in [('blueGem', floor_order)]:
            for fid in order:
                before_count = len(current)
                r = collect_single_target(current, fid, target)
                if r:
                    current = merge(current, r)
                    print(
                        f"  [gem {fid} {target}] {before_count}->{len(current)} "
                        f"(new {len(r)})",
                        flush=True,
                    )
        return current

    # Phase2: 进入后续资源规划。钥匙/血瓶不再预补，除非后续目标失败。
    if entries:
        best = min(entries, key=lambda e: (e.get('_dmg', 0), e.get('_yd', 0), e.get('_bd', 0), e.get('_rd', 0), -e['atk'], -e['def'], -e['yk']))
        print(f"  [Phase2 start] {len(entries)}条, best DMG={best.get('_dmg',0)} HP={best['hp']} ATK={best['atk']} YK={best['yk']} {door_cost_str(best)}", flush=True)

    # Phase3: 搜宝石。MT10通过MT9上楼入口包装成普通宝石候选。
    mt10_entries = None  # 到达10楼后的entries, 每次访问MT10前重新计算
    def ensure_mt10(ents):
        """确保hero到达10楼: 搜MT9上楼, 返回包含MT9过渡的entries"""
        nonlocal mt10_entries
        mt9_up = do_flyback(ents, 'MT9', ['upFloor'], multi=False, max_iter=40000)
        if not mt9_up:
            e0 = ents[0] if ents else {}
            print(f"  FAIL MT9 upFloor (HP={e0.get('hp')} YK={e0.get('yk')})")
            return None
        # 只允许已经走过MT9上楼点的状态进入MT10；否则Boss链会绕过9楼上楼步骤。
        mt10_entries = _filter_entries_tracked(mt9_up, retry_level)
        return mt10_entries

    def collect_mt10_single_target(ents, target):
        """Collect a single MT10 target via the real MT9 up-floor entrance."""
        res = []
        already_mt10 = [e for e in ents if 'MT10' in e.get('collected', {})]
        climb_sources = [e for e in ents if 'MT10' not in e.get('collected', {})]
        climb_mt10 = ensure_mt10(climb_sources) if climb_sources else []
        climb_mt10 = climb_mt10 or []
        e10s = _filter_entries_tracked(already_mt10 + climb_mt10, retry_level)
        if not e10s:
            return res

        for ent in e10s:
            al = ent.get('collected',{}).get('MT10',frozenset())
            needed_pos = frozenset(
                (b[0], b[1]) for b in maps['MT10']['bl']
                if b[3] == target and (b[0], b[1]) not in al
            )
            if not needed_pos:
                continue
            is_fb = 'MT10' in ent.get('collected', {})
            pareto, _, _ = search_floor(maps, 'MT10', ent, [target], flyback=is_fb)
            if not pareto:
                continue
            for hp,yk,bk,rk,atk,def_,hs,vis,dc in pareto:
                if not (vis & needed_pos):
                    continue
                nc = dict(ent.get('collected',{})); nc['MT10'] = al | vis
                res.append(_make_result(hp,yk,bk,rk,atk,def_,nc,ent['_id'],
                    ('MT10',[target],is_fb), dmg_cost=dc))
        return res

    if skip_phase1:
        entries = _filter_entries_tracked(entries, retry_level)
    else:
        entries = collect_gems_defense_first(entries, flyback_order)

    def try_mt10_resources(ents):
        res = []
        e10s = ensure_mt10(ents)
        if not e10s:
            return res
        targets = ['redGem', 'blueGem', 'bluePotion']
        required_pos = frozenset(
            (b[0], b[1]) for b in maps['MT10']['bl'] if b[3] in targets
        )
        for ent in e10s:
            al = ent.get('collected',{}).get('MT10',frozenset())
            missing = required_pos - al
            if not missing:
                continue
            pareto, _, _ = search_floor(maps, 'MT10', ent, targets, flyback=False)
            if not pareto:
                continue
            for hp,yk,bk,rk,atk,def_,hs,vis,dc in pareto:
                if not missing <= vis:
                    continue
                nc = dict(ent.get('collected',{})); nc['MT10'] = al | vis
                res.append(_make_result(hp,yk,bk,rk,atk,def_,nc,ent['_id'],
                    ('MT10',targets,False), dmg_cost=dc))
        return res

    def try_mt10_gems(ents):
        """Fetch only the MT10 gem(s) still needed for 27/27.

        The old stats stage pulled redGem+blueGem+bluePotion together. That can
        dominate numerically for HP/ATK/DEF, but it spends the yellow-key budget
        before the red-key phase. Keep this stage gem-only and let later phases
        decide whether MT10 potion is worth the extra doors.
        """
        res = []
        blue_sources = [e for e in ents if e['def'] < 27]
        if blue_sources:
            res.extend(collect_single_target(blue_sources, 'MT10', 'blueGem'))
        red_sources = [e for e in ents if e['atk'] < 27]
        if red_sources:
            res.extend(collect_single_target(red_sources, 'MT10', 'redGem'))
        return res

    def try_mt10_preopen_left(ents):
        """到达10楼并只预开左侧两扇黄门，给后续红钥匙后flyback Boss线省钥匙。"""
        res = []
        e10s = ensure_mt10(ents)
        if not e10s:
            return res
        required_pos = frozenset([(1, 9), (3, 9)])
        for ent in e10s:
            al = ent.get('collected',{}).get('MT10',frozenset())
            missing = required_pos - al
            if not missing:
                continue
            pareto, _, _ = search_floor(maps, 'MT10', ent, ['yellowDoor'], flyback=False)
            if not pareto:
                continue
            for hp,yk,bk,rk,atk,def_,hs,vis,dc in pareto:
                if not missing <= vis:
                    continue
                nc = dict(ent.get('collected',{})); nc['MT10'] = al | vis
                res.append(_make_result(hp,yk,bk,rk,atk,def_,nc,ent['_id'],
                    ('MT10',['yellowDoor'],False), dmg_cost=dc))
        return res

    # MT10 resources are consumed on demand below. Pulling all of them here
    # spends the yellow-key budget before the red-key phase.

    # Phase4: 拿红钥匙 (在MT10宝石之前, 此时还有YK)
    def ensure_stats_27(ents):
        entries2 = _filter_entries_tracked(ents, retry_level)
        stat_order = ['MT6','MT9','MT8','MT5','MT4','MT7','MT3','MT1','MT10']
        target_yk = 2
        mt10_redkey_reserve_yk = 0
        mt10_gem_budget_bk = 1
        mt10_left_doors = frozenset([(1, 9), (3, 9)])
        mt10_right_doors = frozenset([(9, 9), (11, 9)])

        def needs_mt10_gems(e):
            al = e.get('collected',{}).get('MT10',frozenset())
            need_red = e['atk'] < 27 and any(
                (b[0], b[1]) not in al and b[3] == 'redGem'
                for b in maps['MT10']['bl']
            )
            need_blue = e['def'] < 27 and any(
                (b[0], b[1]) not in al and b[3] == 'blueGem'
                for b in maps['MT10']['bl']
            )
            return need_red or need_blue

        def mt10_gem_yk_cost(e):
            al = e.get('collected',{}).get('MT10',frozenset())
            cost = 0
            needs_red = e['atk'] < 27 and any(
                (b[0], b[1]) not in al and b[3] == 'redGem'
                for b in maps['MT10']['bl']
            )
            needs_blue = e['def'] < 27 and any(
                (b[0], b[1]) not in al and b[3] == 'blueGem'
                for b in maps['MT10']['bl']
            )
            if needs_red:
                cost += sum(1 for pos in mt10_right_doors if pos not in al)
            if needs_blue:
                cost += sum(1 for pos in mt10_left_doors if pos not in al)
            return cost

        def has_mt10_budget(e):
            enter_yk = 0 if 'MT10' in e.get('collected', {}) else 1
            enter_bk = 0 if 'MT10' in e.get('collected', {}) else mt10_gem_budget_bk
            return (
                e['yk'] >= mt10_redkey_reserve_yk + enter_yk + mt10_gem_yk_cost(e) and
                e['bk'] >= enter_bk
            )

        def needs_mt10_budget_backfill(ents0):
            high = [
                e for e in ents0
                if needs_mt10_gems(e) and e['atk'] >= 26 and e['def'] >= 26
            ]
            return bool(high) and not any(has_mt10_budget(e) for e in high)

        def budget_focus(ents0):
            focus = [
                e for e in ents0
                if needs_mt10_gems(e) and e['atk'] >= 26 and e['def'] >= 26 and
                not has_mt10_budget(e)
            ]
            selected = []
            seen_ids = set()

            def add_some(items):
                for e in items:
                    key = e.get('_id', id(e))
                    if key in seen_ids:
                        continue
                    seen_ids.add(key)
                    selected.append(e)

            add_some(sorted(focus, key=lambda e: (e.get('_dmg', 0), e.get('_yd', 0), e.get('_bd', 0), e.get('_rd', 0), -e['yk'], -e['bk'], -e['hp']))[:6])
            add_some(sorted(focus, key=lambda e: (-e['yk'], -e['bk'], e.get('_dmg', 0), e.get('_yd', 0), e.get('_bd', 0), e.get('_rd', 0), -e['hp']))[:6])
            add_some(sorted(focus, key=lambda e: (-e['hp'], e.get('_dmg', 0), e.get('_yd', 0), e.get('_bd', 0), e.get('_rd', 0), -e['yk'], -e['bk']))[:4])
            return selected

        def cap_budget_results(results):
            scored = sorted(
                results,
                key=lambda e: (
                    0 if has_mt10_budget(e) else 1,
                    -e['yk'],
                    -e['bk'],
                    e.get('_dmg', 0),
                    e.get('_yd', 0),
                    e.get('_bd', 0),
                    e.get('_rd', 0),
                    -(e['atk'] + e['def']),
                    -e['hp'],
                ),
            )
            return scored[:24]

        def mt10_budget_sources(ents0):
            candidates = [
                e for e in ents0
                if needs_mt10_gems(e) and has_mt10_budget(e)
            ]
            selected = []
            seen_ids = set()

            def add_some(items):
                for e in items:
                    key = e.get('_id', id(e))
                    if key in seen_ids:
                        continue
                    seen_ids.add(key)
                    selected.append(e)

            add_some(sorted(candidates, key=lambda e: (e.get('_dmg', 0), e.get('_yd', 0), e.get('_bd', 0), e.get('_rd', 0), -e['yk'], -e['bk'], -e['hp']))[:1])
            add_some(sorted(candidates, key=lambda e: (-e['yk'], -e['bk'], e.get('_dmg', 0), e.get('_yd', 0), e.get('_bd', 0), e.get('_rd', 0), -e['hp']))[:1])
            return selected

        def trim_stats(ents0, limit=220):
            ents0 = _filter_entries_tracked(ents0, retry_level)
            if len(ents0) <= limit:
                return ents0
            chosen = []
            seen = set()

            def add_some(items, quota):
                added = 0
                for e in items:
                    key = e.get('_id', id(e))
                    if key in seen:
                        continue
                    seen.add(key)
                    chosen.append(e)
                    added += 1
                    if len(chosen) >= limit or added >= quota:
                        return

            add_some(sorted(
                ents0,
                key=lambda e: (
                    e.get('_dmg', 0), e.get('_yd', 0), e.get('_bd', 0), e.get('_rd', 0),
                    -(e['atk'] + e['def']), -e['yk'], -e['bk'], -e['hp'],
                ),
            ), 70)
            add_some(sorted(
                ents0,
                key=lambda e: (
                    e.get('_yd', 0), e.get('_bd', 0), e.get('_rd', 0), e.get('_dmg', 0),
                    -e['yk'], -e['bk'], -(e['atk'] + e['def']), -e['hp'],
                ),
            ), 45)
            add_some(sorted(
                ents0,
                key=lambda e: (
                    -e['yk'], -e['bk'], e.get('_dmg', 0), e.get('_yd', 0), e.get('_bd', 0),
                    -(e['atk'] + e['def']), -e['hp'],
                ),
            ), 45)
            add_some(sorted(
                [e for e in ents0 if 'MT10' in e.get('collected', {})],
                key=lambda e: (
                    e.get('_dmg', 0), e.get('_yd', 0), e.get('_bd', 0),
                    -e['yk'], -e['bk'], -(e['atk'] + e['def']), -e['hp'],
                ),
            ), 45)
            add_some(sorted(
                [e for e in ents0 if e['atk'] >= 26 and e['def'] >= 26],
                key=lambda e: (
                    e.get('_dmg', 0), e.get('_yd', 0), e.get('_bd', 0),
                    -e['yk'], -e['bk'], -e['hp'],
                ),
            ), 45)
            add_some(sorted(
                ents0,
                key=lambda e: (-e['hp'], e.get('_dmg', 0), e.get('_yd', 0), -e['yk'], -e['bk']),
            ), 20)
            return chosen[:limit]

        def backfill_for_mt10_budget(ents0):
            ents1 = ents0
            for fid in ['MT6','MT5','MT4','MT7','MT9','MT8','MT1','MT3']:
                high = [
                    e for e in ents1
                    if needs_mt10_gems(e) and e['atk'] >= 26 and e['def'] >= 26
                ]
                if any(has_mt10_budget(e) for e in high):
                    break
                focus = budget_focus(ents1)
                if not focus:
                    break
                targets = [t for t in KEY_POTION.get(fid, [])
                           if t in {'yellowKey', 'blueKey', 'redPotion', 'bluePotion'}]
                if not targets:
                    continue
                r = key_improvements(
                    do_key_backfill(focus, fid, targets),
                    keep_pred=has_mt10_budget,
                )
                if r:
                    ents1 = trim_stats(merge(ents1, cap_budget_results(r)))
            return ents1

        for _ in range(8):
            ready = [e for e in entries2 if e['atk'] >= 27 and e['def'] >= 27]
            keyed_ready = [e for e in ready if e['yk'] >= target_yk]
            if keyed_ready:
                return _filter_entries_tracked(ready, retry_level)

            progressed = False

            stat_score_before = max((e['atk'] + e['def'] for e in entries2), default=0)
            has_ready_without_key = bool(ready) and not keyed_ready
            if not has_ready_without_key:
                for target, order in [('blueGem', stat_order), ('redGem', stat_order)]:
                    for fid in order:
                        if target == 'blueGem':
                            if not any(e['def'] < 27 for e in entries2):
                                continue
                        else:
                            if not any(e['atk'] < 27 for e in entries2):
                                continue
                        before_count = len(entries2)
                        r = collect_single_target(entries2, fid, target)
                        if r:
                            new_entries = trim_stats(merge(entries2, r))
                            if len(new_entries) != len(entries2) or {
                                e.get('_id') for e in new_entries
                            } != {e.get('_id') for e in entries2}:
                                progressed = True
                            entries2 = new_entries
                            print(
                                f"  [stat {fid} {target}] {before_count}->{len(entries2)} "
                                f"(new {len(r)})",
                                flush=True,
                            )

            if (not has_ready_without_key) and any(e['atk'] < 27 or e['def'] < 27 for e in entries2):
                if needs_mt10_budget_backfill(entries2):
                    before_count = len(entries2)
                    entries2 = backfill_for_mt10_budget(entries2)
                    entries2 = trim_stats(entries2)
                    if len(entries2) != before_count or not needs_mt10_budget_backfill(entries2):
                        progressed = True
                # MT10 gems are single-target actions. Let target_allowed()
                # filter each target's own entrance budget instead of requiring
                # enough keys for all remaining MT10 gems at once.
                r = try_mt10_gems(entries2)
                if r:
                    entries2 = trim_stats(merge(entries2, r))
                    progressed = True

            stat_score_after = max((e['atk'] + e['def'] for e in entries2), default=0)
            if stat_score_after <= stat_score_before:
                progressed = False

            ready_now = [e for e in entries2 if e['atk'] >= 27 and e['def'] >= 27]
            needs_key_after_ready = ready_now and not any(e['yk'] >= target_yk for e in ready_now)
            still_needs_gems = any(e['atk'] < 27 or e['def'] < 27 for e in entries2)
            high_stat_needs_keys = [
                e for e in entries2
                if (e['atk'] < 27 or e['def'] < 27) and e['atk'] >= 25 and e['def'] >= 25
            ]
            low_key_for_more_gems = bool(high_stat_needs_keys) and all(e['yk'] < 2 for e in high_stat_needs_keys)
            mt10_budget_blocked = needs_mt10_budget_backfill(entries2)
            needs_unlock_for_gems = still_needs_gems and ((not progressed) or low_key_for_more_gems or mt10_budget_blocked)
            if needs_key_after_ready or needs_unlock_for_gems:
                if mt10_budget_blocked:
                    before_count = len(entries2)
                    entries2 = backfill_for_mt10_budget(entries2)
                    entries2 = trim_stats(entries2)
                    if len(entries2) != before_count or not needs_mt10_budget_backfill(entries2):
                        progressed = True
                        mt10_budget_blocked = needs_mt10_budget_backfill(entries2)

                key_targets = ['yellowKey', 'blueKey', 'redPotion', 'bluePotion']
                for fid in ['MT6','MT5','MT4','MT7','MT9','MT8','MT1','MT3']:
                    if any(e['atk'] >= 27 and e['def'] >= 27 and e['yk'] >= target_yk for e in entries2) and not needs_mt10_budget_backfill(entries2):
                        break
                    source_entries = budget_focus(entries2) if mt10_budget_blocked else entries2
                    if not source_entries:
                        continue
                    r = key_improvements(
                        do_key_backfill(source_entries, fid, key_targets),
                        keep_pred=lambda e: (
                            (e['atk'] >= 27 and e['def'] >= 27 and e['yk'] >= target_yk) or
                            has_mt10_budget(e)
                        ),
                    )
                    if r:
                        if mt10_budget_blocked:
                            r = cap_budget_results(r)
                        entries2 = trim_stats(merge(entries2, r))
                        progressed = True

            if not progressed:
                break

        ready = [e for e in entries2 if e['atk'] >= 27 and e['def'] >= 27]
        if not ready:
            best = sorted(entries2, key=lambda e: (e['atk'], e['def'], e['hp']), reverse=True)[:8]
            print("  FAIL Stats27:", [(e['hp'], e['yk'], e['bk'], e['rk'], e['atk'], e['def']) for e in best], flush=True)
            return None
        loose = [e for e in entries2
                 if e['atk'] >= 26 and e['def'] >= 25]
        return _filter_entries_tracked(ready + loose, retry_level)

    stats_entries = ensure_stats_27(entries)
    if not stats_entries:
        return None
    entries = _filter_entries_tracked(
        [e for e in stats_entries if e['atk'] >= 27 and e['def'] >= 27],
        retry_level,
    )
    debug_entries('Stats27', entries)

    def try_redkey(ents):
        res = []
        for ent in ents:
            al = ent.get('collected',{}).get('MT8',frozenset())
            if not any((b[0],b[1]) not in al and b[3]=='redKey' for b in maps['MT8']['bl']): continue
            pareto, _, _ = search_floor(maps, 'MT8', ent,
                ['yellowKey','bluePotion','redKey'], max_iter=500000, flyback=True)
            if pareto:
                for hp,yk,bk,rk,atk,def_,hs,vis,dc in pareto:
                    if rk <= ent['rk'] and not any(
                        (b[0],b[1]) in vis and b[3]=='redKey' for b in maps['MT8']['bl']): continue
                    nc = dict(ent.get('collected',{})); nc['MT8'] = al | vis
                    res.append(_make_result(hp,yk,bk,rk,atk,def_,nc,ent['_id'],
                        ('MT8',['yellowKey','bluePotion','redKey'],True), dmg_cost=dc))
        return res

    rk_r = try_redkey(entries)
    if not rk_r:
        # YK不够, 补充后重试
        print(f"  [redKey] 补充YK后重试...", flush=True)
        for _ in range(4):
            progressed = False
            for fid in flyback_order:
                if all(e['yk'] >= 2 and e['hp'] >= 260 for e in entries):
                    break
                targets = [t for t in KEY_POTION.get(fid, [])
                           if t in {'yellowKey', 'blueKey', 'redPotion', 'bluePotion'}]
                if not targets:
                    continue
                r = key_improvements(
                    do_key_backfill(entries, fid, targets),
                    keep_pred=lambda e: e['yk'] >= 2 and e['hp'] >= 260,
                )
                if r:
                    entries = merge(entries, r)
                    progressed = True
            rk_r = try_redkey(entries)
            if rk_r or not progressed:
                break
    if rk_r:
        entries = _filter_entries_tracked(rk_r, retry_level)
        debug_entries('redKey ok', entries)
    else:
        print(f"  FAIL redKey (继续尝试Boss)", flush=True)
        e0 = entries[0] if entries else {}
        print(f"  FAIL redKey (HP={e0.get('hp')} YK={e0.get('yk')} RK={e0.get('rk')})")

    # Phase5: Boss搜索
    # search_floor 的多目标语义是“任一目标可退出”，所以Boss必须单独作为目标搜索。
    BOSS_TRIGGER_POS = frozenset(
        (b[0], b[1]) for b in maps['MT10']['bl'] if b[3] == 'redDoor'
    )
    def try_boss(ents):
        res = []
        for ent in ents:
            al = ent.get('collected',{}).get('MT10',frozenset())
            is_fb = 'MT10' in ent.get('collected', {})
            pareto, _, _ = search_floor(maps, 'MT10', ent, ['redDoor'], flyback=is_fb)
            if not pareto: continue
            for hp,yk,bk,rk,atk,def_,hs,vis,dc in pareto:
                if not (BOSS_TRIGGER_POS & vis):
                    continue
                if hp <= 0: continue
                boss_total_dmg = boss_event_damage(atk, def_) + calc_dmg('skeletonCaptain', atk, def_)
                hp -= boss_total_dmg
                dc += boss_total_dmg
                if hp <= 0: continue
                nc = dict(ent.get('collected',{})); nc['MT10'] = al | vis
                res.append(_make_result(hp,yk,bk,rk,atk,def_,nc,ent['_id'],
                    ('MT10',['redDoor'],is_fb), dmg_cost=dc))
        return res

    def try_mt10_current_target(ents, target):
        res = []
        for ent in ents:
            al = ent.get('collected',{}).get('MT10',frozenset())
            needed_pos = frozenset(
                (b[0], b[1]) for b in maps['MT10']['bl']
                if b[3] == target and (b[0], b[1]) not in al
            )
            if not needed_pos:
                continue
            is_fb = 'MT10' in ent.get('collected', {})
            pareto, _, _ = search_floor(maps, 'MT10', ent, [target], flyback=is_fb)
            if not pareto:
                continue
            for hp,yk,bk,rk,atk,def_,hs,vis,dc in pareto:
                if not (vis & needed_pos):
                    continue
                nc = dict(ent.get('collected',{})); nc['MT10'] = al | vis
                res.append(_make_result(hp,yk,bk,rk,atk,def_,nc,ent['_id'],
                    ('MT10',[target],is_fb), dmg_cost=dc))
        return res

    # Boss前不再预补钥匙/血瓶；先尝试现有资源，失败再按需补救。
    already_mt10 = [e for e in entries if 'MT10' in e.get('collected', {})]
    already_mt10 = [e for e in entries if 'MT10' in e.get('collected', {})]
    climb_mt10 = ensure_mt10(entries) or []
    e10 = _filter_entries_tracked(already_mt10 + climb_mt10, retry_level)
    if not e10:
        print(f"  FAIL ensure_mt10 before boss", flush=True)
        return None
    debug_entries('boss input', e10)
    if 'MT10' not in flyback_order:
        flyback_order.append('MT10')
    boss_r = try_boss(e10)
    if not boss_r:
        # 只有Boss尝试失败后，才补钥匙/血瓶/剩余宝石重试。
        for _ in range(4):
            progressed = False
            for fid in flyback_order:
                targets = [t for t in COLLECTIBLES.get(fid, [])
                           if t in {'yellowKey', 'blueKey', 'redKey', 'redPotion', 'bluePotion', 'redGem', 'blueGem'}]
                if not targets:
                    continue
                r = do_flyback(e10, fid, targets, multi=True)
                if r:
                    e10 = merge(e10, r)
                    progressed = True
            boss_r = try_boss(e10)
            if boss_r or not progressed:
                break
    if boss_r:
        entries = _filter_entries_tracked(boss_r, retry_level)
        debug_entries('boss ok', entries)
        if result_objective == 'dmg':
            return min(entries, key=lambda r: (
                r.get('_dmg', 0),
                r.get('_yd', 0),
                r.get('_bd', 0),
                r.get('_rd', 0),
                -r['hp'],
            ))
        return max(entries, key=lambda r: r['hp'])
    debug_entries('boss failed input', e10)
    return None

def trace_chain(best):
    chain = []; entry = best; visited = set()
    while entry is not None:
        eid = entry.get('_id')
        if eid in visited: break
        visited.add(eid); chain.append(entry)
        parent_id = entry.get('_parent_id')
        if parent_id is None: break
        entry = _entry_store.get(parent_id)
    chain.reverse(); return chain


def generate():
    print("搜索中...")
    t0 = time.time()
    best = None; best_retry = 0
    for retry in range(5):
        result = run_search(retry)
        if result:
            print(f"  retry {retry}: HP={result['hp']} ATK={result['atk']} DEF={result['def']}")
            if not best or result['hp'] > best['hp']: best = result; best_retry = retry
    if not best: print("失败!"); return
    best = run_search(best_retry)  # 重跑确保_entry_store匹配
    if not best: print("失败!"); return
    print(f"最优: {state_str(best['hp'],best['atk'],best['def'],best['yk'],best['bk'],best['rk'])} ({time.time()-t0:.1f}s)")

    chain = trace_chain(best)
    print(f"路径链: {len(chain)} 步")
    for i, c in enumerate(chain):
        si = c.get('_step_info')
        if si:
            fid, tgts, fb = si
            print(f"  #{i}: {FLOOR_NAMES.get(fid,fid)} {tgts} flyback={fb} {entry_summary(c, chain[i-1])}")
        else: print(f"  #{i}: 起点 {entry_summary(c)}")

    lines = []
    lines.append("# 魔塔1-10层最优攻略")
    lines.append(f"\n> 起点: {state_str(hero['h'],hero['a'],hero['d'],hero['yk'],hero['bk'],0)}")
    lines.append(f"> 终点: {entry_summary(best)}")
    lines.append("")
    for i in range(1, len(chain)):
        prev, curr = chain[i-1], chain[i]
        si = curr.get('_step_info')
        if si is None: continue
        fid, target_ids, flyback = si
        entrances = FLYBACK_ENTRANCES if flyback else ENTRANCES
        sx, sy = entrances[fid]
        removed = prev.get('collected', {}).get(fid, frozenset())
        if fid in FLOOR_13_COLLECTED: removed |= FLOOR_13_COLLECTED[fid]
        target_state = {'hp':curr['hp'],'atk':curr['atk'],'def':curr['def'],
                        'yk':curr['yk'],'bk':curr['bk'],'rk':curr['rk']}
        path_target_state = dict(target_state)
        is_mt10_boss = fid == 'MT10' and ('skeletonCaptain' in target_ids or 'redDoor' in target_ids)
        if is_mt10_boss:
            path_target_state['hp'] = curr['hp'] + boss_event_damage(curr['atk'], curr['def'])
            if 'redDoor' in target_ids:
                path_target_state['hp'] += calc_dmg('skeletonCaptain', curr['atk'], curr['def'])
        steps, final, vis_pos = search_with_path(
            maps[fid], sx, sy, prev['hp'],prev['atk'],prev['def'],
            prev['yk'],prev['bk'],prev['rk'],
            target_ids, max_iter=500000, removed_pos=removed, target_state=path_target_state)
        if not steps:
            pareto, _, _ = search_floor(maps, fid,
                {'hp':prev['hp'],'atk':prev['atk'],'def':prev['def'],
                 'yk':prev['yk'],'bk':prev['bk'],'rk':prev['rk'],
                 'collected':prev.get('collected',{})}, target_ids, flyback=flyback)
            if pareto:
                best_p = min(pareto, key=lambda p: abs(p[0]-curr['hp'])+abs(p[4]-curr['atk'])*10+
                             abs(p[5]-curr['def'])*10+abs(p[1]-curr['yk'])*5)
                fb_ts = {'hp':best_p[0],'atk':best_p[4],'def':best_p[5],'yk':best_p[1],'bk':best_p[2],'rk':best_p[3]}
                if is_mt10_boss:
                    fb_ts['hp'] = curr['hp'] + boss_event_damage(curr['atk'], curr['def'])
                    if 'redDoor' in target_ids:
                        fb_ts['hp'] += calc_dmg('skeletonCaptain', curr['atk'], curr['def'])
                steps, final, vis_pos = search_with_path(
                    maps[fid], sx, sy, prev['hp'],prev['atk'],prev['def'],
                    prev['yk'],prev['bk'],prev['rk'],
                    target_ids, max_iter=500000, removed_pos=removed, target_state=fb_ts)
        if steps:
            if is_mt10_boss:
                steps = expand_mt10_boss_event_steps(steps)
            desc = FLOOR_NAMES.get(fid, fid)
            if flyback: desc += "(flyback)"
            target_names = [EID_NAMES.get(t, t) for t in target_ids]
            desc += f": {'+'.join(target_names)}"
            lines.append(f"### {desc}")
            prev_step = None
            for s in steps:
                if isinstance(s, str):
                    lines.append(s)
                    prev_step = None
                else:
                    lines.append(format_step(s, prev_step))
                    prev_step = s
            lines.append(f"  → {entry_summary(curr, prev)}")
        else: lines.append(f"### {FLOOR_NAMES.get(fid, fid)}: **无路径!**")
        lines.append("")
    lines.append("## 最终结果")
    lines.append(f"**{entry_summary(best)}**")
    wt = "\n".join(lines)
    out_dir = os.path.join('outputs', 'walkthroughs')
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, 'walkthrough.md'), 'w', encoding='utf-8') as f:
        f.write(wt)
    print(wt)


if __name__ == '__main__':
    generate()
