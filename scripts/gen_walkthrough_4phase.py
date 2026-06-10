#!/usr/bin/env python3
"""
生成攻略: 带父节点追踪的Pareto搜索, 反向追踪最优路径再重放每步
dmg=纯战斗伤害 + 7D Pareto + 回溯 + 四阶段
"""
# Allow scripts to import project-root modules after being moved under scripts/.
import os as _codex_os
import sys as _codex_sys
_codex_root = _codex_os.path.dirname(_codex_os.path.dirname(_codex_os.path.abspath(__file__)))
if _codex_root not in _codex_sys.path:
    _codex_sys.path.insert(0, _codex_root)

import os, json, time
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.solver.full_search import (load_data, search_with_path, search_floor, calc_dmg,
                         ENTRANCES, FLYBACK_ENTRANCES, FLOOR_13_COLLECTED, COLLECTIBLES,
                         GEM_ONLY, KEY_POTION)

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


def format_step(s, prev=None):
    eid = s['eid']; name = EID_NAMES.get(eid, eid); action = s['action']
    pos = f"({s['x']},{s['y']})"; changes = []
    hp_before = prev['hp_after'] if prev else s['hp_before']
    if hp_before != s['hp_after']: changes.append(f"HP={hp_before}→{s['hp_after']}")
    atk_before = prev['atk'] if prev else s['atk']
    if atk_before != s['atk']: changes.append(f"ATK={atk_before}→{s['atk']}")
    def_before = prev['def'] if prev else s['def']
    if def_before != s['def']: changes.append(f"DEF={def_before}→{s['def']}")
    yk_before = prev['yk'] if prev else s['yk']
    if yk_before != s['yk']: changes.append(f"YK={yk_before}→{s['yk']}")
    bk_before = prev['bk'] if prev else s['bk']
    if bk_before != s['bk']: changes.append(f"BK={bk_before}→{s['bk']}")
    rk_before = prev['rk'] if prev else s.get('rk', 0)
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


_entry_store = {}
_next_id = [0]

def _make_result(hp, yk, bk, rk, atk, def_, collected, parent_id, step_info, dmg_cost=0):
    _next_id[0] += 1; eid = _next_id[0]
    r = {'hp': hp, 'yk': yk, 'bk': bk, 'rk': rk, 'atk': atk, 'def': def_,
         'collected': collected, '_id': eid, '_parent_id': parent_id,
         '_step_info': step_info, '_dmg': dmg_cost}
    _entry_store[eid] = {'hp': hp, 'atk': atk, 'def': def_, 'yk': yk, 'bk': bk, 'rk': rk,
                          'collected': {k: v for k, v in collected.items()},
                          '_id': eid, '_parent_id': parent_id, '_step_info': step_info}
    return r


def _filter_entries_tracked(all_results, retry_level=0):
    """Pareto七维: (dmg=纯战斗伤害↓, HP↑, ATK↑, DEF↑, YK↑, BK↑, RK↑)
    retry_level越大保留越多entry, 不做HP阈值过滤"""
    items = []
    for r in all_results:
        dmg = r.get('_dmg', 0)
        if dmg == 0:
            parent = _entry_store.get(r.get('_parent_id'))
            parent_hp = parent['hp'] if parent else r['hp']
            dmg = max(0, parent_hp - r['hp'])
        items.append((dmg, r['hp'], r['atk'], r['def'], r['yk'], r['bk'], r['rk'], r))
    items.sort(key=lambda x: x[0])
    pareto_results = []
    for item in items:
        dmg, hp, atk, def_, yk, bk, rk, r = item
        dom = any(p[0] <= dmg and p[1] >= hp and p[2] >= atk and p[3] >= def_ and
                  p[4] >= yk and p[5] >= bk and p[6] >= rk and
                  (p[0] < dmg or p[1] > hp or p[2] > atk or p[3] > def_ or
                   p[4] > yk or p[5] > bk or p[6] > rk) for p in pareto_results)
        if not dom:
            pareto_results = [p for p in pareto_results if not (
                dmg <= p[0] and hp >= p[1] and atk >= p[2] and def_ >= p[3] and
                yk >= p[4] and bk >= p[5] and rk >= p[6] and
                (dmg < p[0] or hp > p[1] or atk > p[2] or def_ > p[3] or
                 yk > p[4] or bk > p[5] or rk > p[6]))]
            pareto_results.append((dmg, hp, atk, def_, yk, bk, rk, r))

    entries = []; seen = set()
    def add_entry(pr, tag=''):
        dmg, hp, atk, def_, yk, bk, rk, r = pr
        key = (atk, def_, yk, bk, rk, tag)
        if key not in seen:
            seen.add(key)
            e = {'hp': hp, 'atk': atk, 'def': def_, 'yk': yk, 'bk': bk, 'rk': rk,
                 'collected': r.get('collected', {})}
            if '_id' in r: e['_id'] = r['_id']
            if '_parent_id' in r: e['_parent_id'] = r['_parent_id']
            if '_step_info' in r: e['_step_info'] = r['_step_info']
            entries.append(e)

    keep_n = min(len(pareto_results), 16 + retry_level * 5)
    for pr in pareto_results[:keep_n]: add_entry(pr)
    if pareto_results:
        add_entry(max(pareto_results, key=lambda p: (p[2], p[1])), tag='atk')
        add_entry(max(pareto_results, key=lambda p: (p[3], p[1])), tag='def')
        add_entry(max(pareto_results, key=lambda p: (p[4], p[1])), tag='yk')
        add_entry(max(pareto_results, key=lambda p: (p[5], p[1])), tag='bk')
        add_entry(max(pareto_results, key=lambda p: (p[6], p[1])), tag='rk')
        add_entry(max(pareto_results, key=lambda p: (p[1], -p[0])), tag='hp')
        add_entry(min(pareto_results, key=lambda p: p[0]), tag='dmg')
        pareto_by_hp = sorted(pareto_results, key=lambda p: p[1], reverse=True)
        for j, hp_pr in enumerate(pareto_by_hp[:retry_level + 1]):
            add_entry(hp_pr, tag=f'ext_hp{j}')
        yk2_plus = [p for p in pareto_results if p[4] >= 2]
        if yk2_plus:
            add_entry(max(yk2_plus, key=lambda p: (p[4], p[1])), tag='yk2')
        yk1_plus = [p for p in pareto_results if p[4] >= 1]
        if yk1_plus: add_entry(max(yk1_plus, key=lambda p: (p[4], p[1])), tag='yk1')
    return entries


def run_search(retry_level=0):
    _entry_store.clear(); _next_id[0] = 0
    start = {'hp': hero['h'], 'atk': hero['a'], 'def': hero['d'],
             'yk': hero['yk'], 'bk': hero['bk'], 'rk': 0, 'collected': {},
             '_id': 1, '_parent_id': None, '_step_info': None}
    _next_id[0] = 1; _entry_store[1] = dict(start)
    entries = [start.copy()]

    def merge(e, r): return _filter_entries_tracked(list(r) + e, retry_level)

    def flyback_search(ents, fid, targets, multi=True):
        res = []
        if multi:
            for ent in ents:
                al = ent.get('collected', {}).get(fid, frozenset())
                if fid in FLOOR_13_COLLECTED: al |= FLOOR_13_COLLECTED[fid]
                is_fb = fid in ent.get('collected', {})
                pareto, _, _ = search_floor(maps, fid, ent, targets, flyback=is_fb)
                if pareto:
                    for hp, yk, bk, rk, atk, def_, hs, vis, dc in pareto:
                        nc = dict(ent.get('collected', {})); nc[fid] = al | vis
                        res.append(_make_result(hp,yk,bk,rk,atk,def_,nc,ent['_id'],(fid,targets,is_fb),dmg_cost=dc))
        else:
            for tgt in targets:
                for ent in ents:
                    al = ent.get('collected', {}).get(fid, frozenset())
                    if fid in FLOOR_13_COLLECTED: al |= FLOOR_13_COLLECTED[fid]
                    if not any((b[0],b[1]) not in al and b[3]==tgt for b in maps[fid]['bl']): continue
                    is_fb = fid in ent.get('collected', {})
                    pareto, _, _ = search_floor(maps, fid, ent, [tgt], flyback=is_fb)
                    if pareto:
                        for hp,yk,bk,rk,atk,def_,hs,vis,dc in pareto:
                            nc = dict(ent.get('collected', {})); nc[fid] = al | vis
                            res.append(_make_result(hp,yk,bk,rk,atk,def_,nc,ent['_id'],(fid,[tgt],is_fb),dmg_cost=dc))
        return res

    def run_steps(steps):
        nonlocal entries
        for fid, targets, fb in steps:
            all_r = []
            if len(targets) > 1:
                # 多target一次搜索
                for ent in entries:
                    al = ent.get('collected', {}).get(fid, frozenset())
                    if fid in FLOOR_13_COLLECTED: al |= FLOOR_13_COLLECTED[fid]
                    is_fb = fb or fid in ent.get('collected', {})
                    pareto, _, _ = search_floor(maps, fid, ent, targets, flyback=is_fb)
                    if pareto:
                        for hp,yk,bk,rk,atk,def_,hs,vis,dc in pareto:
                            nc = dict(ent.get('collected', {})); nc[fid] = al | vis
                            all_r.append(_make_result(hp,yk,bk,rk,atk,def_,nc,ent['_id'],(fid,targets,is_fb),dmg_cost=dc))
            else:
                tgt = targets[0]
                for ent in entries:
                    al = ent.get('collected', {}).get(fid, frozenset())
                    if fid in FLOOR_13_COLLECTED: al |= FLOOR_13_COLLECTED[fid]
                    if tgt != 'upFloor' and not any(
                        (b[0],b[1]) not in al and b[3]==tgt for b in maps[fid]['bl']): continue
                    is_fb = fb or fid in ent.get('collected', {})
                    pareto, _, _ = search_floor(maps, fid, ent, [tgt], flyback=is_fb)
                    if pareto:
                        for hp,yk,bk,rk,atk,def_,hs,vis,dc in pareto:
                            nc = dict(ent.get('collected', {})); nc[fid] = al | vis
                            all_r.append(_make_result(hp,yk,bk,rk,atk,def_,nc,ent['_id'],(fid,[tgt],is_fb),dmg_cost=dc))
            if not all_r:
                # 检查是否所有target已被提前收集(如flyback顺手收了)
                all_precollected = True
                for tgt in targets:
                    if tgt == 'upFloor': all_precollected = False; break
                    if not any((b[0],b[1]) in ent.get('collected',{}).get(fid,frozenset())
                               and b[3]==tgt for ent in entries for b in maps[fid]['bl']):
                        all_precollected = False; break
                if all_precollected: continue  # 已收集, 不算失败
                print(f"  FAIL {fid} (entries={len(entries)})"); return False
            entries = _filter_entries_tracked(all_r, retry_level)
        return True

    flyback_order = ['MT7','MT6','MT3','MT1','MT9','MT4','MT8','MT5','MT10']

    def dynamic_gem_flyback(skip_floors=None):
        nonlocal entries
        if skip_floors is None: skip_floors = set()
        changed = True
        while changed:
            changed = False
            for fid in flyback_order:
                if fid in skip_floors: continue
                avail = [t for t in GEM_ONLY.get(fid, [])
                         if any(not any((b[0],b[1]) in e.get('collected',{}).get(fid,frozenset())
                                        and b[3]==t for b in maps[fid]['bl']) for e in entries)]
                if not avail: continue
                before = len(entries)
                r = flyback_search(entries, fid, avail)
                if r: entries = merge(entries, r)
                if len(entries) != before: changed = True

    def backfill_yk(need):
        nonlocal entries
        for fid in flyback_order:
            if all(e['yk'] >= need for e in entries): break
            r = flyback_search(entries, fid, ['yellowKey'], multi=False)
            if r: entries = merge(entries, r)

    def try_redkey(ents):
        res = []
        for ent in ents:
            al = ent.get('collected', {}).get('MT8', frozenset())
            if not any((b[0],b[1]) not in al and b[3]=='redKey' for b in maps['MT8']['bl']): continue
            pareto, _, _ = search_floor(maps, 'MT8', ent,
                ['yellowKey','bluePotion','redKey'], max_iter=500000, flyback=True)
            if pareto:
                for hp,yk,bk,rk,atk,def_,hs,vis,dc in pareto:
                    if rk <= ent['rk'] and not any(
                        (b[0],b[1]) in vis and b[3]=='redKey' for b in maps['MT8']['bl']): continue
                    nc = dict(ent.get('collected', {})); nc['MT8'] = al | vis
                    res.append(_make_result(hp,yk,bk,rk,atk,def_,nc,ent['_id'],
                        ('MT8',['yellowKey','bluePotion','redKey'],True), dmg_cost=dc))
        return res

    def try_boss(ents):
        res = []
        evt = {'skeleton','skeletonSoldier'}
        for ent in ents:
            al = ent.get('collected', {}).get('MT10', frozenset())
            pareto, _, _ = search_floor(maps, 'MT10', ent, ['skeletonCaptain'], flyback=False)
            if pareto:
                for hp,yk,bk,rk,atk,def_,hs,vis,dc in pareto:
                    if hp <= 0: continue
                    extra = 0
                    for b in maps['MT10']['bl']:
                        if b[2]==1 and b[3] in evt:
                            if (b[0],b[1]) not in vis and (b[0],b[1]) not in al:
                                extra += calc_dmg(b[3], atk, def_)
                    hp -= extra; dc += extra
                    if hp <= 0: continue
                    fv = vis | frozenset((b[0],b[1]) for b in maps['MT10']['bl']
                        if b[2]==1 and b[3] in evt and (b[0],b[1]) not in vis and (b[0],b[1]) not in al)
                    nc = dict(ent.get('collected', {})); nc['MT10'] = al | fv
                    res.append(_make_result(hp,yk,bk,rk,atk,def_,nc,ent['_id'],
                        ('MT10',['skeletonCaptain'],False), dmg_cost=dc))
        return res

    # ===== Phase A: Sword =====
    if not run_steps([('MT4',['upFloor'],False), ('MT5',['sword1'],False)]): return None

    # ===== Phase B: Shield + 关键gem(硬编码最优顺序) =====
    if not run_steps([
        ('MT4',['redGem'],True), ('MT5',['upFloor'],True),
        ('MT6',['upFloor'],False), ('MT7',['upFloor'],False),
        ('MT8',['upFloor'],False), ('MT9',['shield1'],False),
        ('MT7',['redGem'],True),     # ATK=22→23 阈值
        ('MT3',['redGem'],True),     # ATK=23→24
        ('MT1',['redGem','blueGem'],True),  # ATK=24→25
    ]): return None

    # ===== Phase C: 动态flyback收集剩余宝石 + 补充HP/YK + RedKey =====
    dynamic_gem_flyback()
    backfill_yk(6)
    # 补充HP: 搜蓝药水
    for fid in flyback_order:
        if all(e['hp'] >= 500 for e in entries): break
        r = flyback_search(entries, fid, ['bluePotion'], multi=False)
        if r: entries = merge(entries, r)
    rk_r = try_redkey(entries)
    if not rk_r: backfill_yk(2); rk_r = try_redkey(entries)
    if rk_r: entries = _filter_entries_tracked(rk_r, retry_level)
    else:
        e0 = entries[0] if entries else {}
        print(f"  FAIL redKey (e0: HP={e0.get('hp')} YK={e0.get('yk')} BK={e0.get('bk')} ATK={e0.get('atk')} DEF={e0.get('def')})")
        return None

    # ===== Phase D: Boss =====
    boss_r = try_boss(entries)
    if not boss_r: backfill_yk(4); boss_r = try_boss(entries)
    if boss_r:
        entries = _filter_entries_tracked(boss_r, retry_level)
        return max(entries, key=lambda r: r['hp'])
    e0 = entries[0] if entries else {}
    print(f"  FAIL Boss (e0: HP={e0.get('hp')} YK={e0.get('yk')} RK={e0.get('rk')})"); return None


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
    for retry in range(10):
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
            print(f"  #{i}: {FLOOR_NAMES.get(fid,fid)} {tgts} flyback={fb} HP={c['hp']} ATK={c['atk']} DEF={c['def']}")
        else: print(f"  #{i}: 起点 HP={c['hp']} ATK={c['atk']} DEF={c['def']}")

    lines = []
    lines.append("# 魔塔1-10层最优攻略")
    lines.append(f"\n> 起点: {state_str(hero['h'],hero['a'],hero['d'],hero['yk'],hero['bk'],0)}")
    lines.append(f"> 终点: {state_str(best['hp'],best['atk'],best['def'],best['yk'],best['bk'],best['rk'])}")
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
        steps, final, vis_pos = search_with_path(
            maps[fid], sx, sy, prev['hp'],prev['atk'],prev['def'],
            prev['yk'],prev['bk'],prev['rk'],
            target_ids, max_iter=500000, removed_pos=removed, target_state=target_state)
        if not steps:
            pareto, _, _ = search_floor(maps, fid,
                {'hp':prev['hp'],'atk':prev['atk'],'def':prev['def'],
                 'yk':prev['yk'],'bk':prev['bk'],'rk':prev['rk'],
                 'collected':prev.get('collected',{})}, target_ids, flyback=flyback)
            if pareto:
                best_p = min(pareto, key=lambda p: abs(p[0]-curr['hp'])+abs(p[4]-curr['atk'])*10+
                             abs(p[5]-curr['def'])*10+abs(p[1]-curr['yk'])*5)
                fb_ts = {'hp':best_p[0],'atk':best_p[4],'def':best_p[5],'yk':best_p[1],'bk':best_p[2],'rk':best_p[3]}
                steps, final, vis_pos = search_with_path(
                    maps[fid], sx, sy, prev['hp'],prev['atk'],prev['def'],
                    prev['yk'],prev['bk'],prev['rk'],
                    target_ids, max_iter=500000, removed_pos=removed, target_state=fb_ts)
        if steps:
            desc = FLOOR_NAMES.get(fid, fid)
            if flyback: desc += "(flyback)"
            target_names = [EID_NAMES.get(t, t) for t in target_ids]
            desc += f": {'+'.join(target_names)}"
            lines.append(f"### {desc}")
            prev_step = None
            for s in steps: lines.append(format_step(s, prev_step)); prev_step = s
            lines.append(f"  → {state_str(curr['hp'],curr['atk'],curr['def'],curr['yk'],curr['bk'],curr['rk'])}")
        else: lines.append(f"### {FLOOR_NAMES.get(fid, fid)}: **无路径!**")
        lines.append("")
    lines.append("## 最终结果")
    lines.append(f"**{state_str(best['hp'],best['atk'],best['def'],best['yk'],best['bk'],best['rk'])}**")
    wt = "\n".join(lines)
    with open('walkthrough.md', 'w', encoding='utf-8') as f: f.write(wt)
    print(wt)


if __name__ == '__main__':
    generate()
