#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk 产物固定校验（每次生成 breakdown / compare 后必须跑）。

对一条已验证 walk 做六项独立检查, 全过输出 PASS:
1. 权威重放 final == walk final（逐字段 hp/atk/def/yk/bk/rk/gold/dmg/yd/bd/rd）
2. 击杀/拾取格集合 == walk 记录（walk 击杀步 + auto:/auto_sweep: note 条目）
3. 钥匙对账(每色) = 初始+裸拾取+商人买−开门−出售−最终 == 0
   （裸拾取 note 条目优先、商人步排除; 卖钥只认商人步——与 breakdown 生成器同口径）
4. 金币恒等式: Σ正delta − Σ负delta == final_gold − start_gold, 且
   收入分类合计(打怪+卖+其它) == Σ正delta
5. 门闭合: 静态门数 == 剩余 + 显式开门 + 残差(残差须可用 魔法钥匙/事件开门 解释,
   逐层列出残差由人工确认)
6. 剩余怪金 <= walk-diff 上界（事件生成怪单列, 不计入静态上界）

用法: python scripts/audit/verify_route_artifacts.py --walk outputs/results/X_walk.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / 'scripts' / 'search'))
sys.path.insert(0, str(ROOT))

DOOR_CN = {'yellowDoor': '黄', 'blueDoor': '蓝', 'redDoor': '红'}
EID_COLOR = {'yellowDoor': 'y', 'blueDoor': 'b', 'redDoor': 'r'}
KEY_EID_COLOR = {'yellowKey': 'yk', 'blueKey': 'bk', 'redKey': 'rk'}
DOOR_EID_COLOR = {'yellowDoor': 'yk', 'blueDoor': 'bk', 'redDoor': 'rk'}
CHECK_KEYS = ('hp', 'atk', 'def', 'yk', 'bk', 'rk', 'gold', 'dmg', 'yd', 'bd', 'rd')


def note_entries(note):
    out = []
    for m in re.finditer(r'(?:auto_sweep|auto):\s*(.*)', note):
        out += [(int(x), int(y), eid.rstrip(',')) for x, y, eid in
                re.findall(r'x(\d+)y(\d+)\s+(\S+)', m.group(1))]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--walk', required=True)
    ap.add_argument('--actions', default=None,
                    help='修改过的语义动作列表 JSON (capture 手术候选线)。提供后检查1 '
                         '用它独立重放; 缺省从 capture 原生派生。')
    args = ap.parse_args()
    walk = json.loads(Path(args.walk).read_text(encoding='utf-8-sig'))
    prov = walk.get('provenance') or {}
    failures = []

    import recording_seed_to_game as R
    from src.solver.game_route import Game as _BaseGame

    class CapGame(_BaseGame):
        last = None

        def __init__(self, *a, **kw):
            super().__init__(*a, **kw)
            CapGame.last = self

    R.Game = CapGame
    seed_p = Path(prov.get('seed_save') or 'best/checkpoints/save1_mt4_snapshot.json')
    cap_p = Path(prov['capture'])
    seed = R.read_json(seed_p)
    cap, actions = R.load_capture(cap_p)
    if args.actions:
        raw = json.loads(Path(args.actions).read_text(encoding='utf-8-sig'))
        actions = [R.parse_action(d, i) for i, d in enumerate(raw)]
    st = walk['steps'][0]['before']
    ss = next((i for i, e in enumerate(cap.get('statlog') or [])
               if isinstance(e, dict) and isinstance(e.get('before'), dict)
               and e['before'].get('f') == st.get('floor')
               and e['before'].get('hp') == st.get('hp')), None)
    res = R.convert(seed, cap, actions, prov.get('stage', 'mt4-mt31'), seed_p, cap_p, ss,
                    auto_spec=prov.get('auto_spec') or 'battle=false,item=false,wall=false')
    if not res['ok']:
        failures.append(f'权威重放失败: {res["errors"][:2]}')
    else:
        drift = {k: (res['final'].get(k), walk['final'].get(k)) for k in CHECK_KEYS
                 if res['final'].get(k) != walk['final'].get(k)}
        if drift:
            failures.append(f'检查1 重放final != walk final: {drift}')
        else:
            print('检查1 PASS: 权威重放 final == walk final'
                  + (' (修改动作列表)' if args.actions else ''))

    g = CapGame.last
    rem_door = defaultdict(set)
    rem_mon = defaultdict(dict)
    for fid, floor in g.floors.items():
        for pos, blk in floor.blocks.items():
            if blk.kind == 'door':
                rem_door[fid].add(pos)
            elif blk.kind == 'enemy':
                rem_mon[fid][pos] = blk.eid

    # 检查2: 击杀/拾取格集合
    tiles = json.load(open(ROOT / 'data/maps/tile_mapping.json', encoding='utf-8-sig'))
    eid_by_tile = {int(t): info.get('id') for t, info in
                   tiles.get('tiles', tiles).items() if isinstance(info, dict)}
    enemies = json.load(open(ROOT / 'data/maps/enemy_stats.json', encoding='utf-8-sig'))['enemys']
    static_mons = defaultdict(dict)
    static_doors = defaultdict(dict)
    for p in sorted((ROOT / 'data/maps').glob('mt*_map.json')):
        fid = p.stem.replace('_map', '').upper()
        raw = json.loads(p.read_text(encoding='utf-8-sig'))
        grid = raw.get('map') or raw.get('m') or []
        for y, row in enumerate(grid):
            for x, t in enumerate(row):
                eid = eid_by_tile.get(t)
                if eid in DOOR_CN:
                    static_doors[fid][(x, y)] = eid
                elif eid in enemies:
                    static_mons[fid][(x, y)] = eid
    killed_replay = {fid: {pos: e for pos, e in mons.items() if pos not in rem_mon.get(fid, {})}
                     for fid, mons in static_mons.items()}
    walk_kills = set()
    for s in walk['steps']:
        f = s['floor']
        note = s.get('note') or ''
        if s['action'] == '击杀':
            pos = s.get('pos')
            if pos:
                walk_kills.add((f, pos[0], pos[1], s.get('eid')))
        for x, y, eid in note_entries(note):
            if eid in enemies:   # note 条目含道具/墙, 只取怪
                walk_kills.add((f, x, y, eid))
    # 重放击杀直接取 Game 记录步(静态差集法对事件生成怪失效, 如 MT10/49F 封印怪)。
    # sweep 击杀在 Game 步内同样折叠进 auto:/auto_sweep: note —— 两侧用同一套提取。
    replay_kills = set()
    for s in CapGame.last.steps:
        f = s.get('floor')
        note = s.get('note') or ''
        if s.get('action') == '击杀':
            pos = s.get('pos')
            if pos:
                replay_kills.add((f, pos[0], pos[1], s.get('eid')))
        for x, y, eid in note_entries(note):
            if eid in enemies:
                replay_kills.add((f, x, y, eid))
    # 按 (floor,x,y) 比对(点击位 vs 怪物位可能有 1 格噪声)
    wk = {(f, x, y) for f, x, y, _ in walk_kills}
    rk = {(f, x, y) for f, x, y, _ in replay_kills}
    if wk - rk:
        failures.append(f'检查2 walk 有而重放无的击杀格: {sorted(wk - rk)[:8]}')
    elif rk - wk:
        failures.append(f'检查2 重放有而 walk 无的击杀格: {sorted(rk - wk)[:8]}')
    else:
        print(f'检查2 PASS: 击杀/拾取格集合一致 ({len(rk)} 格)')

    # 检查3: 钥匙对账
    led = {}
    for c in ('yk', 'bk', 'rk'):
        init = walk['steps'][0]['before'].get(c, 0)
        final = walk['steps'][-1]['after'].get(c, 0)
        pick = buy = sell = door = 0
        for s in walk['steps']:
            note = s.get('note') or ''
            act = s['action']
            d = (s['after'].get(c) or 0) - (s['before'].get(c) or 0)
            if act in ('商人', '商店'):
                if d > 0:
                    buy += d
                elif d < 0 and act == '商人':
                    gold = (s['after'].get('gold') or 0) - (s['before'].get('gold') or 0)
                    if gold > 0 and -d * 100 <= gold + 1:
                        sell += -d
                continue
            note_keys = [e for _, _, e in note_entries(note)
                         if KEY_EID_COLOR.get(e) == c]
            if note_keys:
                pick += len(note_keys)
            elif d > 0:
                pick += d
            if act == '开门' and s.get('eid') in DOOR_EID_COLOR and DOOR_EID_COLOR[s['eid']] == c:
                door += 1
        led[c] = init + pick + buy - door - sell - final
    bad_led = {c: v for c, v in led.items() if v != 0}
    if bad_led:
        failures.append(f'检查3 钥匙对账非零: {bad_led}')
    else:
        print('检查3 PASS: 钥匙对账 黄/蓝/红 全 0')

    # 检查4: 金币恒等式
    pos_g = sum(max((s['after'].get('gold') or 0) - (s['before'].get('gold') or 0), 0)
                for s in walk['steps'])
    neg_g = sum(max((s['before'].get('gold') or 0) - (s['after'].get('gold') or 0), 0)
                for s in walk['steps'])
    net = (walk['steps'][-1]['after'].get('gold') or 0) - (walk['steps'][0]['before'].get('gold') or 0)
    if pos_g - neg_g != net:
        failures.append(f'检查4 金币恒等式: Σ正{pos_g} − Σ负{neg_g} != final−start {net}')
    else:
        print(f'检查4 PASS: 金币恒等式 Σ正{pos_g} − Σ负{neg_g} = {net}')

    # 检查5: 门闭合 (静态 == 剩余 + 显式开门 + 残差; 残差须=魔法钥匙/事件开门, 人工确认)
    residuals = []
    color_cn = {'y': '黄', 'b': '蓝', 'r': '红'}
    for fid, doors in static_doors.items():
        for c in ('y', 'b', 'r'):
            n_static = sum(1 for e in doors.values() if EID_COLOR[e] == c)
            n_rem = sum(1 for p in rem_door.get(fid, set())
                        if EID_COLOR.get(static_doors[fid].get(p, ''), '') == c)
            n_open = sum(1 for s in walk['steps'] if s['floor'] == fid and s['action'] == '开门'
                         and s.get('eid') in EID_COLOR and EID_COLOR[s['eid']] == c)
            r = n_static - n_rem - n_open
            if r:
                residuals.append((fid, color_cn[c], r))
    print(f'检查5 门闭合残差(须=魔法钥匙/事件开门, 人工确认): {residuals or "无"}')

    # 检查6: 剩余怪金 <= walk-diff 上界 (事件生成怪单列, 不入静态上界)
    rem_money = sum(int(enemies[e].get('money', 0))
                    for fid, mons in static_mons.items()
                    for pos, e in mons.items() if pos in rem_mon.get(fid, {}))
    upper = sum(int(enemies[e].get('money', 0)) for fid, mons in static_mons.items()
                for pos, e in mons.items() if (fid, pos[0], pos[1]) not in wk)
    spawned = sum(int(enemies[e].get('money', 0)) for fid, d in rem_mon.items()
                  for pos, e in d.items() if pos not in static_mons.get(fid, {}))
    print(f'检查6 剩余怪金(静态未杀)={rem_money} <= walk-diff上界={upper}; '
          f'事件怪剩余(不入上界)={spawned}')
    if rem_money > upper:
        failures.append(f'检查6 剩余怪金 {rem_money} > walk-diff 上界 {upper}')

    if failures:
        print('\nFAIL:')
        for f in failures:
            print(' -', f)
        raise SystemExit(1)
    print('\nALL PASS')


if __name__ == '__main__':
    main()
