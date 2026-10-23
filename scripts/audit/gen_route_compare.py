#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""多条已验证 walk 的 整体 + 逐层 差异对比报告 (xlsx)。

对每条 walk:
- walk 统计: 每层 dmg / 开门数(黄蓝红) / 金币收入(正 delta) / checkpoint 快照
- 权威重放(converter 共享 Game): 静态图 − 重放剩余 = 每层已开门坐标、已杀怪坐标
  (与 gen_recording_floor_breakdown 同源, 比对 walk final 防漂移)
输出:
- sheet1 整体对比: 终态/总伤/法伤/血瓶/收入/钥匙账/剩余 + checkpoint 表 + 备注
- sheet2 逐层差异: 只列有差异的层; N==2 布局(用户 2026-09-17 定稿 + 2026-10-02 增补):
  楼层 | dmg×2+diff | 剩余血瓶HP×2+diff | 黄门×2+diff | 蓝门×2+diff | 红门×2 | 金币×2+diff
  | 门坐标差异 | 击杀差异,
  diff 列写具体值(前一线−后一线; 不用公式, 脚本 data_only 可直读); 门坐标差异只列各线独有坐标
  (真 diff, 一侧 0 也列出)。剩余血瓶HP = 权威重放末态未拾血瓶按层 ratio 折算
  (红50×ratio / 蓝200×ratio, 与 gen_recording_floor_breakdown 剩余血量同源)。

用法:
    python scripts/audit/gen_route_compare.py \
        --walk 41200=outputs/results/41200_walk.json \
        --walk 41228=outputs/results/41228_walk.json \
        --walk 41218=outputs/results/41218_walk.json \
        --anchors MT11,MT21,MT41 \
        --out best/xxx_compare.xlsx \
        --note "结论行1" --note "结论行2"

口径(与 floor_breakdown_experience.md 一致):
- checkpoint = 该层「首次到达(before)」与「首次攻略完(首个连续段的最后一步 after)」,
  不取最后一次离层(会被后期飞行回访污染)。
- 门/怪坐标差异 = 静态图块 − 权威重放剩余; 事件生成怪不在静态表, 只出现在
  剩余侧(MT50 redKing 类), 在击杀差异中单列说明。
- dmg 对比直接用 walk 逐层 delta(两线同种子同属性购买计划时可比)。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from gen_recording_floor_breakdown import _load_json, write_xlsx  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent.parent
DOOR_CN = {'yellowDoor': '黄', 'blueDoor': '蓝', 'redDoor': '红'}
VALUE_KEYS = ('hp', 'atk', 'def', 'dmg', 'yk', 'bk', 'rk', 'gold')


def static_map_blocks():
    tiles = json.load(open(ROOT / 'data/maps/tile_mapping.json', encoding='utf-8-sig'))
    eid_by_tile = {int(t): info.get('id') for t, info in
                   tiles.get('tiles', tiles).items() if isinstance(info, dict)}
    enemies = json.load(open(ROOT / 'data/maps/enemy_stats.json', encoding='utf-8-sig'))['enemys']
    doors = defaultdict(dict)   # fid -> {(x,y): eid}
    mons = defaultdict(dict)    # fid -> {(x,y): eid}
    for p in sorted((ROOT / 'data/maps').glob('mt*_map.json')):
        fid = p.stem.replace('_map', '').upper()
        raw = json.loads(p.read_text(encoding='utf-8-sig'))
        grid = raw.get('map') or raw.get('m') or []
        for y, row in enumerate(grid):
            for x, t in enumerate(row):
                eid = eid_by_tile.get(t)
                if eid in DOOR_CN:
                    doors[fid][(x, y)] = eid
                elif eid in enemies:
                    mons[fid][(x, y)] = eid
    return doors, mons


def replay_remaining(walk):
    """converter 权威重放, 返回每层剩余门/怪坐标; 并校验 replay final == walk final。"""
    prov = walk.get('provenance') or {}
    sys.path.insert(0, str(ROOT / 'scripts' / 'search'))
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
    stage = prov.get('stage', 'mt4-mt31')
    auto = prov.get('auto_spec') or 'battle=false,item=false,wall=false'
    seed = R.read_json(seed_p)
    cap, actions = R.load_capture(cap_p)
    st = walk['steps'][0]['before']
    ss = next((i for i, e in enumerate(cap.get('statlog') or [])
               if isinstance(e, dict) and isinstance(e.get('before'), dict)
               and e['before'].get('f') == st.get('floor')
               and e['before'].get('hp') == st.get('hp')), None)
    res = R.convert(seed, cap, actions, stage, seed_p, cap_p, ss, auto_spec=auto)
    if not res['ok']:
        raise SystemExit(f'{cap_p} 重放失败: {res["errors"][:2]}')
    drift = {k: (res['final'].get(k), walk['final'].get(k)) for k in VALUE_KEYS
             if res['final'].get(k) != walk['final'].get(k)}
    if drift:
        print(f"[warn] {cap_p.name} 权威重放 final 与 walk final 漂移: {drift}")
    rem_door = defaultdict(set)
    rem_mon = defaultdict(dict)
    rem_potion = {}
    for fid, floor in CapGame.last.floors.items():
        ratio = int(getattr(floor, 'ratio') or 1)
        pot = 0
        for pos, blk in floor.blocks.items():
            if blk.kind == 'door':
                rem_door[fid].add(pos)
            elif blk.kind == 'enemy':
                rem_mon[fid][pos] = blk.eid
            elif blk.kind == 'item':
                if blk.eid == 'redPotion':
                    pot += 50 * ratio
                elif blk.eid == 'bluePotion':
                    pot += 200 * ratio
        rem_potion[fid] = pot
    return rem_door, rem_mon, rem_potion


def walk_stats(walk):
    dmg = defaultdict(int)
    doors = defaultdict(lambda: defaultdict(int))   # color -> fid -> n
    gold_in = defaultdict(int)
    super_potion_hp = 0   # 圣水(superPotion) 使用恢复 HP（拾取不回血）
    shop_hp = 0           # 商店血购买增益（商店步的 hp 增量）
    for s in walk['steps']:
        f = s['floor']
        d = (s['after'].get('dmg') or 0) - (s['before'].get('dmg') or 0)
        if d:
            dmg[f] += d
        if s['action'] == '开门' and s.get('eid') in DOOR_CN:
            doors[DOOR_CN[s['eid']]][f] += 1
        g = (s['after'].get('gold') or 0) - (s['before'].get('gold') or 0)
        if g > 0:
            gold_in[f] += g
        if s.get('eid') == 'superPotion':
            super_potion_hp += (s['after'].get('hp') or 0) - (s['before'].get('hp') or 0)
        if s['action'] == '商店':
            shop_hp += (s['after'].get('hp') or 0) - (s['before'].get('hp') or 0)
    return dmg, doors, gold_in, super_potion_hp, shop_hp


def first_block(walk, fid):
    idxs = [i for i, s in enumerate(walk['steps']) if s['floor'] == fid]
    if not idxs:
        return None
    j = idxs[0]
    while j + 1 < len(walk['steps']) and walk['steps'][j + 1]['floor'] == fid:
        j += 1
    return walk['steps'][idxs[0]]['before'], walk['steps'][j]['after']


def fmt_pts(pts):
    return '、'.join(f'({x},{y})' for x, y in sorted(pts)) or '-'


def fmt_kills(d):
    return '、'.join(f'({x},{y}){e}' for (x, y), e in sorted(d.items())) or '-'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--walk', action='append', required=True,
                    help='label=path/to/walk.json, 可重复')
    ap.add_argument('--anchors', default='MT11,MT21,MT41')
    ap.add_argument('--out', required=True)
    ap.add_argument('--note', action='append', default=[],
                    help='整体对比 sheet 末尾的结论行, 可重复')
    args = ap.parse_args()

    labels = [w.split('=', 1)[0] for w in args.walk]
    N = len(labels)
    static_doors, static_mons = static_map_blocks()

    data = {}
    for w in args.walk:
        label, path = w.split('=', 1)
        walk = _load_json(path)
        rem_door, rem_mon, rem_potion = replay_remaining(walk)
        opened = {fid: {pos for pos in static_doors.get(fid, {}) if pos not in rem_door.get(fid, set())}
                  for fid in static_doors}
        opened_eid = {fid: {pos: static_doors[fid][pos] for pos in opened[fid]} for fid in opened}
        killed = {fid: {pos: e for pos, e in static_mons.get(fid, {}).items()
                        if pos not in rem_mon.get(fid, {})} for fid in static_mons}
        spawned_rem = {fid: {pos: e for pos, e in rem_mon.get(fid, {}).items()
                             if pos not in static_mons.get(fid, {})} for fid in rem_mon}
        dmg, doors, gold_in, super_potion_hp, shop_hp = walk_stats(walk)
        snaps = {f: first_block(walk, f) for f in args.anchors.split(',')}
        data[label] = {
            'walk': walk, 'opened': opened_eid, 'killed': killed,
            'spawned_rem': spawned_rem, 'dmg': dmg, 'doors': doors,
            'gold_in': gold_in, 'snaps': snaps, 'final': walk['steps'][-1]['after'],
            'rem_potion': rem_potion,
            'super_potion_hp': super_potion_hp, 'shop_hp': shop_hp,
        }

    # ---------------- sheet1 整体对比 ----------------
    rows = [['指标'] + labels + (['diff(后者-前者)'] if N == 2 else [])]

    def add(metric, vals, diff=None):
        if diff is None and N == 2 and all(isinstance(v, (int, float)) for v in vals):
            diff = vals[1] - vals[0]
        rows.append([metric] + vals + ([diff] if N == 2 else []))

    def finale(key):
        return [data[l]['final'].get(key) for l in labels]

    add('终态HP', finale('hp'))
    add('终态ATK', finale('atk'))
    add('终态DEF', finale('def'))
    add('终态dmg', finale('dmg'))
    add('终态金币', finale('gold'))
    add('终态楼层', finale('floor'))
    dmg_tot = [sum(data[l]['dmg'].values()) for l in labels]
    add('dmg合计', dmg_tot)
    potion = [data[l]['final']['hp'] - data[l]['walk']['steps'][0]['before']['hp'] + t
              for l, t in zip(labels, dmg_tot)]
    add('拾取血量(=HP-起点+dmg)', potion)
    # 药瓶/圣水拆分：拾取血量(derived) = 药瓶(红+蓝) + 圣水(superPotion) + 商店血购买
    add('圣水恢复HP(superPotion)', [data[l]['super_potion_hp'] for l in labels])
    add('药瓶恢复HP(红+蓝)', [p - data[l]['super_potion_hp'] - data[l]['shop_hp']
                             for l, p in zip(labels, potion)])
    ginc = [sum(data[l]['gold_in'].values()) for l in labels]
    add('金币获得合计', ginc)
    for c in ('黄', '蓝', '红'):
        add(f'{c}门开门', [sum(data[l]['doors'][c].values()) for l in labels])
    enemies = json.load(open(ROOT / 'data/maps/enemy_stats.json', encoding='utf-8-sig'))['enemys']

    def rem_money(label):
        d = data[label]
        tot = 0
        for fid, mons in static_mons.items():
            killed = d['killed'].get(fid, {})
            tot += sum(int(enemies[e].get('money', 0)) for p, e in mons.items()
                       if p not in killed)
        for fid, sp in d['spawned_rem'].items():
            tot += sum(int(enemies[e].get('money', 0)) for e in sp.values())
        return tot

    add('剩余怪金(静态未杀+事件怪)', [rem_money(l) for l in labels])
    rows.append([])
    rows.append(['checkpoint（均为首次进入该层的到达快照 before；同字段各线相邻便于对比）'])
    FIELDS = ['到达HP', '到达DEF', '到达dmg', '到达yk', '到达bk', '到达金币']
    hdr1 = ['层']
    hdr2 = ['层']
    for fld in FIELDS:
        hdr1 += [fld] + [''] * (N - 1)
        hdr2 += labels
    rows.append(hdr1)
    rows.append(hdr2)
    for f in args.anchors.split(','):
        row = [f]
        for fld, key in (('到达HP', 'hp'), ('到达DEF', 'def'), ('到达dmg', 'dmg'),
                         ('到达yk', 'yk'), ('到达bk', 'bk'), ('到达金币', 'gold')):
            for l in labels:
                fb = data[l]['snaps'].get(f)
                row.append(fb[0].get(key) if fb else '-')
        rows.append(row)
    if args.note:
        rows.append([])
        for n in args.note:
            rows.append([n])

    # ---------------- sheet2 逐层差异 ----------------
    s2 = []
    allf = sorted({f for l in labels for f in
                   set(data[l]['dmg']) | set(data[l]['gold_in'])
                   | {fid for c in DOOR_CN.values() for fid in data[l]['doors'][c]}
                   | set(static_doors) | set(static_mons)},
                  key=lambda x: int(x[2:]) if x[2:].isdigit() else 0)

    def floor_has_diff(fid):
        vals = [data[l]['dmg'].get(fid, 0) for l in labels]
        if len(set(vals)) > 1:
            return True
        if len({data[l]['rem_potion'].get(fid, 0) for l in labels}) > 1:
            return True
        for c in ('黄', '蓝', '红'):
            if len({data[l]['doors'][c].get(fid, 0) for l in labels}) > 1:
                return True
        if len({data[l]['gold_in'].get(fid, 0) for l in labels}) > 1:
            return True
        ka = [data[l]['killed'].get(fid, {}) for l in labels]
        oa = [data[l]['opened'].get(fid, set()) for l in labels]
        return any(ka[i] != ka[0] for i in range(1, N)) or any(oa[i] != oa[0] for i in range(1, N))

    # 列头必须与数据行逐列对齐（用户 2026-09-17 定稿布局，N==2；2026-10-02 dmg 后增补剩余血瓶HP）：
    # 楼层 | dmg×2+diff | 剩余血瓶HP×2+diff | 黄门×2+diff | 蓝门×2+diff | 红门×2 | 金币×2+diff
    # | 门坐标差异 | 击杀差异
    # diff 列写具体值（前一线−后一线；不用 Excel 公式——脚本 data_only 读公式列为 None），
    # 红门不加 diff。
    groups = [('dmg', True), ('剩余血瓶HP', True), ('黄门', True), ('蓝门', True),
              ('红门', False), ('金币', True)]

    def gvals(name, fid):
        if name == 'dmg':
            return [data[l]['dmg'].get(fid, 0) for l in labels]
        if name == '剩余血瓶HP':
            return [data[l]['rem_potion'].get(fid, 0) for l in labels]
        if name == '金币':
            return [data[l]['gold_in'].get(fid, 0) for l in labels]
        c = name[0]
        return [data[l]['doors'][c].get(fid, 0) for l in labels]

    hdr = ['楼层']
    for name, with_diff in groups:
        hdr += [f'{l} {name}' for l in labels]
        if with_diff and N == 2:
            hdr.append(f'{name}diff')
    hdr += ['门坐标差异', '击杀差异']
    s2.append([f'逐层差异 —— 每线列序: dmg | 剩余血瓶HP | 黄门 | 蓝门 | 红门 | 金币 '
               f'—— {"/".join(labels)}'])
    s2.append(hdr)
    gsums = {name: defaultdict(int) for name, _ in groups}

    def diff_cell(vals):
        return vals[0] - vals[1]  # 前一线 − 后一线（与用户原公式 =B-C 同向）

    for fid in allf:
        if not floor_has_diff(fid):
            continue
        row = [fid]
        for name, with_diff in groups:
            vals = gvals(name, fid)
            row += vals
            for i, l in enumerate(labels):
                gsums[name][l] += vals[i]
            if with_diff and N == 2:
                row.append(diff_cell(vals))
        # 门坐标差异: 真 diff —— 只列各线独有坐标(某色只在一侧开也要列出, 如 MT33 蓝门 1vs0)
        dtxt = []
        for c in ('黄', '蓝', '红'):
            sets = [{p for p, e in data[l]['opened'].get(fid, {}).items() if e == _eid(c)}
                    for l in labels]
            if len({frozenset(s) for s in sets}) <= 1:
                continue
            parts = []
            for l, s in zip(labels, sets):
                others = set().union(*(o for ol, o in zip(labels, sets) if ol != l))
                uniq = s - others
                if uniq:
                    parts.append(f'{l}独有:{fmt_pts(uniq)}')
            if parts:
                dtxt.append(f'{c}门 ' + ' | '.join(parts))
            else:
                dtxt.append(f'{c}门[' + ' vs '.join(f'{l}:{fmt_pts(s)}'
                                                    for l, s in zip(labels, sets)) + ']')
        row.append('  '.join(dtxt) or '-')
        # 击杀差异
        ktxt = []
        for l in labels:
            others = [k for i, k in enumerate(
                [data[x]['killed'].get(fid, {}) for x in labels]) if i != labels.index(l)]
            mine = data[l]['killed'].get(fid, {})
            only = {p: e for p, e in mine.items()
                    if any(o.get(p) != e for o in others)}
            # 只在所有其它线都没有时才算独有
            only = {p: e for p, e in only.items()
                    if all(o.get(p) != e for o in others)}
            if only:
                ktxt.append(f'{l}独杀:{fmt_kills(only)}')
        spawned_txt = []
        for l in labels:
            sp = data[l]['spawned_rem'].get(fid, {})
            if sp:
                spawned_txt.append(f'{l}剩余(事件怪):{fmt_kills(sp)}')
        row.append('  '.join(ktxt + spawned_txt) or '-')
        s2.append(row)
    tot_row = ['差异层合计(非全线总伤, 全线总伤见整体对比)']
    for name, with_diff in groups:
        vals = [gsums[name][l] for l in labels]
        tot_row += vals
        if with_diff and N == 2:
            tot_row.append(diff_cell(vals))
    s2.append(tot_row)

    write_xlsx(args.out, [('整体对比', rows), ('逐层差异', s2)])
    print(json.dumps({'out': args.out, 'labels': labels}, ensure_ascii=False))


def _eid(cn):
    return {'黄': 'yellowDoor', '蓝': 'blueDoor', '红': 'redDoor'}[cn]


if __name__ == '__main__':
    main()
