#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""将已验证的 Game walk.json 拆分成 分层记录(每层=最终地图剩余状态) + 汇总记录(金币/钥匙对账)，
写出两个 sheet 的 .xlsx。

数据源=已验证 `41228_walk.json`(每步 before/after)。金币/钥匙/dmg/魔法/商店等汇总用 walk 增量；
**每层最终剩余资源(怪/门/裸钥/血瓶/商人/事件)用共享 Game 重放 walk 后的最终 g.floors**(权威，
因为 walk.json 的 auto_sweep note 会被截断，仅靠 map−walk 算剩余怪会严重高估：41228 实例
walk-diff 剩 8277、权威 Game 只剩 385)。重放需该 walk 的 `--seed-save / --capture / --start-stat`
(用录制数据重跑 converter 里的同款 Game；start-stat 不传则自动匹配 seed 的楼层+HP)。

用法:
    python scripts/audit/gen_recording_floor_breakdown.py \
        --walk outputs/results/41228_walk.json \
        --seed-save best/checkpoints/save1_mt4_snapshot.json \
        --capture outputs/results/41228_capture.json --stage mt4-mt31 \
        --out best/41228_floor_breakdown.xlsx
不带 seed/capture 时回退到 walk 自算(门/裸钥可对账，但**剩余怪会高估**，会打印警告)。

检查点记录(2026-09-13 新增; 2026-10-03 改为并入汇总记录 sheet 末尾):
`--checkpoints <N>层,MTxx,before:<eid>,魔龙前,TE最终boss前,end`
追加区界楼层/魔龙前/TE最终boss前的累计快照(dmg/恢复血量/
消耗yk·bk·rk/剩余yk·bk 自己+地图+合计/获得金币/持有金币/地图剩余金币/商店购买情况)。
地图侧数据=权威重放每 record 一步命中检查点步数时对 g.floors 现场聚合(与最终剩余同源)。
例: --checkpoints 11层,31层,41层,魔龙前,TE最终boss前

口径(与用户对齐):
- 截点:最终 50F 真魔王 redKing 击杀步的 before(won50=False，不含 +500 击杀奖励)。
  检测=steps[-1]==(击杀 redKing, floor MT50)。
- 魔法伤害=Σ action=='地图伤害' 步 dmg(5区半血陷阱+靠近初级/高级巫师，与防御无关)。41228=1523。
- 金币对账: 总获金=打怪+卖yk+其它。打怪=击杀/auto_sweep 步 gold 增量(含 49F 封印怪等事件生成怪)。
- 钥匙对账(每色): 初始+裸拾取+商人买=开门+出售+最终。
- 分层记录(每层=最终地图状态): 剩余X门=未开门；剩余rk/bk/yk=未拾裸钥(不含事件生成)；
  剩余血量=该层未拾血瓶HP折算(红50×ratio、蓝200×ratio，分区值不同)；剩余怪金=该层未杀怪money；
  剩余商人/事件=未消费。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from collections import defaultdict
from pathlib import Path
from xml.sax.saxutils import escape as xesc


# --------------------------------------------------------------------------- #
# 最小 xlsx 写入器(纯 stdlib)
# --------------------------------------------------------------------------- #
def _sheet_xml(rows):
    body = []
    for r in rows:
        cells = []
        for v in r:
            if v is None:
                cells.append('<c/>')
            elif isinstance(v, bool):
                cells.append(f'<c t="b"><v>{1 if v else 0}</v></c>')
            elif isinstance(v, (int, float)):
                cells.append(f'<c><v>{v}</v></c>')
            else:
                cells.append(f'<c t="inlineStr"><is><t>{xesc(str(v))}</t></is></c>')
        body.append('<row>' + ''.join(cells) + '</row>')
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            f'<sheetData>{"".join(body)}</sheetData></worksheet>')


def write_xlsx(path, sheets):
    wb = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
          '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
          'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
          '<sheets>'
          + ''.join(f'<sheet name="{xesc(n)}" sheetId="{i+1}" r:id="rId{i+1}"/>'
                    for i, (n, _) in enumerate(sheets))
          + '</sheets></workbook>')
    ct = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
          '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.'
          'relationships+xml"/>'
          '<Default Extension="xml" ContentType="application/xml"/>'
          '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-'
          'officedocument.spreadsheetml.sheet.main+xml"/>'
          + ''.join(f'<Override PartName="/xl/worksheets/sheet{i+1}.xml" '
                    'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.'
                    'worksheet+xml"/>' for i in range(len(sheets)))
          + '</Types>')
    rr = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
          '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
          '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
          'relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
    wr = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
          '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
          + ''.join(f'<Relationship Id="rId{i+1}" Type="http://schemas.openxmlformats.org/'
                    'officeDocument/2006/relationships/worksheet" '
                    f'Target="worksheets/sheet{i+1}.xml"/>' for i in range(len(sheets)))
          + '</Relationships>')
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', ct)
        z.writestr('_rels/.rels', rr)
        z.writestr('xl/workbook.xml', wb)
        z.writestr('xl/_rels/workbook.xml.rels', wr)
        for i, (_, rows) in enumerate(sheets):
            z.writestr(f'xl/worksheets/sheet{i+1}.xml', _sheet_xml(rows))


# --------------------------------------------------------------------------- #
# 商人 / 事件 描述
# --------------------------------------------------------------------------- #
# 商人机制功能(位置为键 'fid:x,y' -> 机械作用：属性提升/道具获得)。用于"剩余商人"标注。
MERCHANT_FUNC = {
    # 交易商人(gold→keys / 道具 / HP)
    'MT6:8,4': '50G→1蓝钥', 'MT7:6,1': '50G→5黄钥', 'MT12:1,1': '800G→1红钥',
    'MT15:11,11': '200G→1蓝钥', 'MT31:11,1': '1000G→4黄+1蓝钥(钥匙包)',
    'MT38:5,2': '200G→3黄钥', 'MT39:9,2': '2000G→3蓝钥',
    'MT45:9,3': '1000G→+2000HP', 'MT47:5,2': '4000G→地震卷轴',
    'MT2:10,7': '卖黄钥→金', 'MT28:8,4': '卖黄钥→金',
    # 防具/商店
    'MT4:6,1': '商店(攻/防/蓝钥)', 'MT12:6,9': '商店(攻)', 'MT32:10,10': '商店(防)',
    'MT46:6,1': '商店(防/血)',
    # 老头(有实际机制奖励才列; 纯剧情老头忽略)
    'MT2:11,4': '老头+1000G', 'MT16:11,11': '圣水老人(+复活)',
}
# 事件机制功能(位置为键 -> 机械作用)。
EVENT_HINT = {
    'MT2:11,4': '老头+1000G', 'MT2:10,7': '卖钥匙商人', 'MT2:9,11': '小偷',
    'MT15:9,1': '小偷', 'MT16:11,11': '圣水(复活)',
    'MT20:6,8': '吸血鬼', 'MT26:6,6': '公主', 'MT29:6,2': '小偷',
    'MT33:10,5': '骑士剑机关', 'MT34:5,2': '开8黄门杀8怪→4YK+1RK',
    'MT35:6,7': '魔龙', 'MT40:6,7': '骑士队长boss', 'MT41:10,2': '右上撞墙红巫师',
    'MT42:5,10': '骑士队长逃跑', 'MT49:6,6': '假魔王封印', 'MT50:6,5': '真魔王揭示',
}


def _event_snippet(ev):
    try:
        if isinstance(ev, str):
            s = ev.strip()
            return s[:28] if s and not s.startswith('{') and not s.startswith('[') else ''
        if isinstance(ev, dict):
            for key in ('text', 'dialog', 'title', 'condition'):
                v = ev.get(key)
                if isinstance(v, str):
                    v = v.strip().lstrip('\\t')
                    if v and not v.startswith('{') and not v.startswith('['):
                        return v[:28]
                elif isinstance(v, list) and v and isinstance(v[0], str):
                    first = v[0].strip().lstrip('\\t')
                    if first and not first.startswith('{') and not first.startswith('['):
                        return first[:28]
    except Exception:
        pass
    return ''


def _merchant_text(fid, x, y, eid):
    # 优先机械作用；其次按 eid 通用标注(不作具体+1000G 等猜测, 只有确认过的才写)
    func = MERCHANT_FUNC.get(f'{fid}:{x},{y}')
    if not func:
        if eid.endswith('Shop'):
            func = '商店(攻/防/血)'
        elif eid in ('trader', 'specialTrader'):
            func = '交易商人'
        elif eid == 'oldman':
            func = '老头'
        elif eid == 'king':
            func = '国王'
        elif eid == 'thief':
            func = '小偷'
        else:
            func = f'NPC({eid})'
    return f'({x},{y}){func}'


_EVENT_MECH = ('choices', 'setValue', 'openDoor', 'closeDoor', 'setBlock',
               'battle', 'changeFloor', 'hide', 'while', 'if', 'tip')
# 老头/国王等通用 NPC 的"机械奖励"关键字——给属性/金币/钥匙/道具才算可决策商人
_REWARD_KW = ('status:atk', 'status:def', 'status:hp', 'status:money', 'giveItem',
              'superPotion', 'pickaxe', 'bomb', 'earthquake', 'snow', 'cross', 'knife',
              'yellowKey', 'blueKey', 'redKey', 'redPotion', 'bluePotion',
              'sword', 'shield', 'upFly', 'downFly', 'centerFly')
# 这些 eid 属于"可能只有剧情"的通用 NPC；商店/交易商人永远有机制作用
_FLAVOR_NPC = ('oldman', 'king', 'child', 'magician', 'npc', 'npc0', 'npc1', 'npc2',
               'npc48')


def _event_mechanical(v):
    """是否真·机械事件(商人/机关/陷阱/boss)，剔除 noPass 墙体装饰、空 data。"""
    if isinstance(v, dict):
        if v.get('noPass') is True:
            return False
        s = json.dumps(v, ensure_ascii=False)
        return any(k in s for k in _EVENT_MECH)
    if isinstance(v, (str, list)):
        return any(k in json.dumps(v, ensure_ascii=False) for k in _EVENT_MECH)
    return False


def _event_text(fid, key, snippet):
    pos_hint = EVENT_HINT.get(f'{fid}:{key}')
    if pos_hint:
        return f'@{key}({pos_hint})'
    if snippet:
        return f'@{key}:{snippet}'
    return f'@{key}'


# --------------------------------------------------------------------------- #
# 加载
# --------------------------------------------------------------------------- #
def _load_json(path, binary=False):
    p = Path(path)
    if binary:
        data = p.read_bytes()
        return json.loads(data.decode('utf-8-sig') if data[:3] == b'\xef\xbb\xbf'
                          else data.decode('utf-8'))
    return json.loads(p.read_text(encoding='utf-8-sig'))


def floor_no(fid):
    try:
        return int(fid[2:]) if isinstance(fid, str) and fid[:2] == 'MT' and fid[2:].isdigit() else 0
    except (ValueError, TypeError):
        return 0


def zone_of(fid):
    n = floor_no(fid)
    return 1 + (n - 1) // 10 if 1 <= n <= 50 else 0


# --------------------------------------------------------------------------- #
# walk 解析(金币/钥匙/dmg/魔法/商店 汇总)
# --------------------------------------------------------------------------- #
def _auto_sweep_entries(note):
    """步内自动条目: auto_sweep: (门步/到达步 BFS) + auto: (击杀步折叠)。

    2026-08-31 门步自动BFS模型定稿后, 击杀步的顺路清理写 `auto:`、开门步写
    `auto_sweep:`, 两者条目格式相同 (xNyN eid, ...)——钥匙/血瓶/金币分类必须
    两种前缀都认, 否则同一开门步「拾N把+开1扇」净抵消时拾取漏计
    (41200 实证: 纯 delta 计数黄钥裸拾 134, 对账差 -44)。
    """
    if not note:
        return []
    out = []
    for m in re.finditer(r'(?:auto_sweep|auto):\s*(.*)', note):
        out += [(int(x), int(y), eid.rstrip(',')) for x, y, eid in
                re.findall(r'x(\d+)y(\d+)\s+(\S+)', m.group(1))]
    return out


def _killed_list(note):
    if not note:
        return []
    return [(int(x), int(y), eid) for x, y, eid in
            re.findall(r'\(\((\d+),\s*(\d+)\)\s*,\s*[\'"](\w+)[\'"]\)', note)]


KEY_EID_COLOR = {'yellowKey': 'yk', 'blueKey': 'bk', 'redKey': 'rk'}


def _cut_index(steps):
    """返回截点: MT50 redKing 击杀步下标(截到 before, 不含 +500 奖励), 无则 None。

    容忍击杀后的零 delta 尾步(如 converter 输出的到达(6,5)): 只要击杀之后的步
    全部无状态变化, 仍视为可截。40943 walk 末尾多一个 [到达] 曾使旧「steps[-1]
    必须是击杀」检测失效, 导致截点落到击杀后(金币多算 +500)。
    """
    kill_idx = None
    for i in range(len(steps) - 1, -1, -1):
        s = steps[i]
        if s['action'] == '击杀' and s.get('eid') == 'redKing' and s.get('floor') == 'MT50':
            kill_idx = i
            break
    if kill_idx is None:
        return None
    for s in steps[kill_idx + 1:]:
        b, a = s['before'], s['after']
        if any((a.get(k) or 0) != (b.get(k) or 0) for k in
               ('hp', 'atk', 'def', 'yk', 'bk', 'rk', 'gold', 'dmg', 'yd', 'bd', 'rd')):
            return None   # 击杀后还有真实状态变化 -> 不截, 保持旧行为
    return kill_idx


def walk_stats(steps):
    if not steps:
        raise SystemExit('walk 无 steps')
    cut_i = _cut_index(steps)
    if cut_i is not None:
        effective = steps[:cut_i]
        final_state = steps[cut_i]['before']
        cut_step = steps[cut_i]
    else:
        effective = steps
        final_state = steps[-1]['after']
        cut_step = None
    start_state = steps[0]['before']

    # 需要每层 ratio 算血瓶 -> 这里用 walk 数据的 floor 无 ratio；改由调用方经 Game/map 提供。
    # 血瓶 ratio 需要在 compile_remaining 里按 floor 映射。这里只累加「步内出现的血瓶数」，
    # 每层 ratio 由调用方填入 ratio_of 后一起折算。
    dmg_total = magic_dmg = floor_dmg_sum = 0
    floor_dmg = {}
    monster_loot = sell_yk_gold = other_gold = 0
    key_acquired = defaultdict(int); key_buy = defaultdict(int); key_sell = defaultdict(int)
    key_pick = defaultdict(int)
    door_open = {'yk': 0, 'bk': 0, 'rk': 0}
    color_of = {'yellowDoor': 'yk', 'blueDoor': 'bk', 'redDoor': 'rk'}
    shop = defaultdict(lambda: defaultdict(int))
    shop_gain = {'攻': 0, '防': 0, '血': 0}   # 商店属性增益合计
    floor_bad = defaultdict(int)   # 本层 红/蓝血瓶 计数(后按 ratio 折)
    super_potion_hp = 0            # 圣水(superPotion) 使用恢复 HP
    floor_spend = defaultdict(lambda: {'yk': 0, 'bk': 0, 'rk': 0})   # 本层 开门花费(=耗钥)
    consumed_npc = set()           # (floor,x,y) 已消费的商人/商店/NPC
    consumed_ev = set()            # (floor,x,y) 已触发的事件(事件 action 步)
    walked_tiles = set()           # (floor,x,y) 英雄实际踩过的格(踩上即触发 step-on 事件/陷阱)
    visited = set()                # 走到过的楼层
    for s in effective:
        visited.add(s['floor'])
        if s.get('pos'):
            walked_tiles.add((s['floor'],) + tuple(s['pos']))
        f = s['floor']; b = s['before']; a = s['after']
        note = s.get('note') or ''
        pos = tuple(s['pos']) if s.get('pos') else None
        dd = (a.get('dmg') or 0) - (b.get('dmg') or 0)
        floor_dmg[f] = floor_dmg.get(f, 0) + dd
        if dd > 0:
            dmg_total += dd
        if s['action'] == '地图伤害':
            magic_dmg += dd
        if s['action'] == '开门' and s.get('eid') in color_of:
            door_open[color_of[s['eid']]] += 1
            floor_spend[f][color_of[s['eid']]] += 1
        # 血瓶拾取：单位×50×ratio。红=1 单位(50)，蓝=4 单位(200)。
        for _, _, eid in _auto_sweep_entries(note) + _killed_list(note):
            if eid == 'redPotion':
                floor_bad[f] += 1
            elif eid == 'bluePotion':
                floor_bad[f] += 4
        if s['action'] == '拾取':
            if s.get('eid') == 'redPotion':
                floor_bad[f] += 1
            elif s.get('eid') == 'bluePotion':
                floor_bad[f] += 4
        # 圣水(superPotion)使用：HP 恢复发生在使用步(拾取不回血)
        if s.get('eid') == 'superPotion':
            super_potion_hp += (a.get('hp') or 0) - (b.get('hp') or 0)
        gold = (a.get('gold') or 0) - (b.get('gold') or 0)
        if gold > 0:
            yk_l = (b.get('yk') or 0) - (a.get('yk') or 0)
            # 2026-09-05 41200 修复：卖 yk 只认商人步。开门步的 auto_sweep 常
            # 带来金币（顺路清怪），gold>0 且 yk 减 1 会被误判成卖钥匙
            # （41200 实证：卖 21 实为 15，其余 6 步是开门+顺路拾金）。
            if yk_l > 0 and gold >= 100 * yk_l and s['action'] == '商人':
                sell_yk_gold += 100 * yk_l
                key_sell['yk'] += yk_l
                gold -= 100 * yk_l
            if s['action'] == '击杀' or 'auto_sweep' in note or _killed_list(note):
                monster_loot += gold
            else:
                other_gold += gold
        # 钥匙拾取（2026-09-05 41200 修复）：note 条目优先——同一开门步可能
        # 「拾 N 把 + 开 1 扇」净 delta 抵消（甚至为 0），纯 delta 计数漏计
        # 同步抵消的拾取；无 note 条目时回退正 delta（纯拾取步/击杀奖励）。
        # 商人/商店步的 note 也列钥匙条目（购买展示），那些是 key_buy 不能
        # 重复计为拾取（41200 实证：MT7 5yk+MT38 3yk / MT6,15 2bk / MT12 1rk）。
        note_keys = [] if s['action'] in ('商人', '商店') else [
            eid for _, _, eid in _auto_sweep_entries(note) + _killed_list(note)
            if eid in KEY_EID_COLOR]
        for eid in note_keys:
            key_pick[KEY_EID_COLOR[eid]] += 1
        for c in ('yk', 'bk', 'rk'):
            d = (a.get(c) or 0) - (b.get(c) or 0)
            if d > 0:
                key_acquired[c] += d
                if not note_keys and s['action'] not in ('商人', '商店'):
                    key_pick[c] += d
        if s['action'] == '商人':
            for c in ('yk', 'bk', 'rk'):
                d = (a.get(c) or 0) - (b.get(c) or 0)
                if d > 0:
                    key_buy[c] += d
        if s['action'] == '商店':
            kind = {'atk': '攻', 'def': '防', 'hp': '血'}.get(s.get('eid'), s.get('eid'))
            shop[zone_of(f)][kind] += 1
            if kind == '攻':
                shop_gain['攻'] += (a.get('atk') or 0) - (b.get('atk') or 0)
            elif kind == '防':
                shop_gain['防'] += (a.get('def') or 0) - (b.get('def') or 0)
            elif kind == '血':
                shop_gain['血'] += (a.get('hp') or 0) - (b.get('hp') or 0)
        # 已消费商人/商店/NPC 与已触发事件
        if s['action'] in ('事件', '商人', '商店') and pos is not None:
            consumed_npc.add((f,) + pos)
        if s['action'] == '事件' and pos is not None:
            consumed_ev.add((f,) + pos)
    if cut_step is not None:
        # 截掉的击杀步本身已执行: 楼层 visited / step-on 格 walked_tiles 仍要计入
        visited.add(cut_step['floor'])
        if cut_step.get('pos'):
            walked_tiles.add((cut_step['floor'],) + tuple(cut_step['pos']))
    return {
        'effective_count': len(effective),
        'final_state': final_state, 'start_state': start_state,
        'dmg_total': dmg_total, 'magic_dmg': magic_dmg, 'phys_dmg': dmg_total - magic_dmg,
        'monster_loot': monster_loot, 'sell_yk_gold': sell_yk_gold, 'other_gold': other_gold,
        'total_income': monster_loot + sell_yk_gold + other_gold,
        'keys': dict(key_acquired), 'key_pick': dict(key_pick),
        'key_buy': dict(key_buy), 'key_sell': dict(key_sell),
        'door_open': door_open,
        'init_keys': {c: start_state.get(c, 0) for c in ('yk', 'bk', 'rk')},
        'final_keys': {c: final_state.get(c, 0) for c in ('yk', 'bk', 'rk')},
        'yd': final_state.get('yd', 0), 'bd': final_state.get('bd', 0),
        'rd': final_state.get('rd', 0),
        'zone_shop': {k: dict(v) for k, v in shop.items()},
        'shop_gain': shop_gain,
        'floor_dmg': {f: int(v) for f, v in floor_dmg.items()},
        'floor_bad': dict(floor_bad),
        'floor_spend': {f: dict(v) for f, v in floor_spend.items()},
        'super_potion_hp': super_potion_hp,
        'consumed_npc': consumed_npc,
        'consumed_ev': consumed_ev,
        'walked_tiles': walked_tiles,
        'visited': visited,
    }


# --------------------------------------------------------------------------- #
# 检查点记录(第三 sheet): 区界楼层/魔龙前/TE最终boss前 的累计快照
# --------------------------------------------------------------------------- #
CHECKPOINT_ALIASES = {
    '魔龙前': 'before:magicDragon',
}


def resolve_checkpoints(steps, eff_len, final_state, specs):
    """解析检查点 spec 列表 -> [(显示名, 已执行步数, 检查点时刻 hero 状态)]。

    语法:
    - '<N>层' / 'MTxx'  = 首次到达该层(换层步 after, 已含到达时结算的 arrival auto)。
    - 'before:<eid>'    = 首个 `击杀 eid` 步之前(该步 before; walk 链自洽时
                          == 上一步 after)。
    - '魔龙前'          = before:magicDragon 别名。
    - 'TE最终boss前'    = 50F 真魔王 redKing 击杀步 before。注意 49F 假魔王封印怪
                          eid 同为 redKing, 必须限定 floor==MT50(_cut_index 同款)。
                          录像止步于最终 boss 击杀前(无 MT50 redKing 击杀步)时
                          退化为全部有效步之后(=录像末尾)。
    - 'end'             = 全部有效步之后(截点口径下即 redKing 击杀前)。
    状态一律取检查点时刻的真实 hero 状态, 不重算。
    """
    out = []
    for spec in specs:
        name = spec
        m = re.match(r'^(\d+)层$', spec) or re.match(r'(?i)^MT(\d+)$', spec)
        if m:
            fid = f'MT{int(m.group(1))}'
            idx = next((i for i, s in enumerate(steps)
                        if s['after'].get('floor') == fid), None)
            if idx is None:
                raise SystemExit(f'检查点 {name}: walk 未到达 {fid}')
            out.append((name, idx + 1, steps[idx]['after']))
            continue
        if spec in ('TE最终boss前', '最终boss前'):
            i = next((k for k, s in enumerate(steps[:eff_len])
                      if s['action'] == '击杀' and s.get('eid') == 'redKing'
                      and s.get('floor') == 'MT50'), None)
            if i is None:
                out.append((name, eff_len, final_state))
            else:
                out.append((name, i, steps[i]['before']))
            continue
        tgt = CHECKPOINT_ALIASES.get(spec, spec)
        if tgt == 'end':
            out.append((name, eff_len, final_state))
            continue
        if tgt.startswith('before:'):
            eid = tgt.split(':', 1)[1]
            i = next((k for k, s in enumerate(steps[:eff_len])
                      if s['action'] == '击杀' and s.get('eid') == eid), None)
            if i is None:
                if spec == 'TE最终boss前':
                    # 录像在最终 boss 击杀前截止: 末尾即 TE最终boss前
                    out.append((name, eff_len, final_state))
                    continue
                raise SystemExit(f'检查点 {name}: 有效步内未找到 `击杀 {eid}` 步')
            out.append((name, i, steps[i]['before']))
            continue
        raise SystemExit(f'未知检查点 spec: {spec}(支持 <N>层/MTxx/before:<eid>/'
                         '魔龙前/TE最终boss前/end)')
    return out


def checkpoint_hero_stats(steps, idx, state, start_hp, ratio_of=None):
    """检查点 hero 侧累计(含已执行的前 idx 步):
    消耗yk/bk/rk=开门消耗(出售另见汇总钥匙对账); 获得金币=金币正增量累计;
    打怪金币=游戏「数据统计」金币口径(statistics.money 只在引擎 afterBattle 累加:
    击杀步+auto清怪步+带伤害的事件战斗步计入; 卖钥/事件赠送/炸弹杀怪不计,
    41206 boss前实证 17485 与实机数据统计一致); 药瓶恢复HP=红50×ratio/蓝200×ratio
    (不含圣水/商店血); 商店购买情况=按楼层+类型聚合(如 MT32防×7)。"""
    color_of = {'yellowDoor': 'yk', 'blueDoor': 'bk', 'redDoor': 'rk'}
    consumed = {'yk': 0, 'bk': 0, 'rk': 0}
    earned = 0
    battle_gold = 0
    potion_units = defaultdict(int)
    shops = {}
    for s in steps[:idx]:
        f = s['floor']
        note = s.get('note') or ''
        if s['action'] == '开门' and s.get('eid') in color_of:
            consumed[color_of[s['eid']]] += 1
        for _, _, eid in _auto_sweep_entries(note) + _killed_list(note):
            if eid == 'redPotion':
                potion_units[f] += 1
            elif eid == 'bluePotion':
                potion_units[f] += 4
        if s['action'] == '拾取':
            if s.get('eid') == 'redPotion':
                potion_units[f] += 1
            elif s.get('eid') == 'bluePotion':
                potion_units[f] += 4
        g = (s['after'].get('gold') or 0) - (s['before'].get('gold') or 0)
        if g > 0:
            earned += g
            dd = (s['after'].get('dmg') or 0) - (s['before'].get('dmg') or 0)
            if s['action'] == '击杀' or _auto_sweep_entries(note) or dd > 0:
                battle_gold += g
        if s['action'] == '商店':
            kind = {'atk': '攻', 'def': '防', 'hp': '血'}.get(s.get('eid'), s.get('eid'))
            key = (s['floor'], kind)
            shops[key] = shops.get(key, 0) + 1
    recovered = (state.get('hp') or 0) - start_hp + (state.get('dmg') or 0)
    potion_hp = sum(u * 50 * (ratio_of or {}).get(f, 1) for f, u in potion_units.items())
    shop_str = ' '.join(f'{f}{k}×{n}' for (f, k), n in sorted(shops.items())) or '无'
    return {'dmg': state.get('dmg', 0), '恢复血量': recovered, '药瓶恢复HP': potion_hp,
            '消耗': consumed, 'yk': state.get('yk', 0), 'bk': state.get('bk', 0),
            '获得金币': earned, '打怪金币': battle_gold,
            'gold': state.get('gold', 0), '商店': shop_str}


def map_floor_remaining_key_gold(g, fid):
    """单层地图侧聚合: 剩余裸钥 yk/bk + 未杀怪 money(事件生成怪已 spawn 未杀的
    也计入, 与 breakdown 剩余怪金同源)。返回 (map_yk, map_bk, map_gold)。"""
    floor = g.floors[fid]
    my = mb = money = 0
    enemies = g.enemies
    for blk in floor.blocks.values():
        k = getattr(blk, 'kind', None)
        eid = getattr(blk, 'eid', '')
        if k == 'item':
            if eid == 'yellowKey':
                my += 1
            elif eid == 'blueKey':
                mb += 1
        elif k == 'enemy':
            money += int(enemies.get(eid, {}).get('money', 0))
    return my, mb, money


def find_start_stat(capture, floor, hp):
    """找 statlog 里匹配 walk 起点(楼层+HP) 的帧下标, 供 converter 切片跳过前缀。"""
    statlog = capture.get('statlog') or []
    for i, st in enumerate(statlog):
        if not isinstance(st, dict):
            continue
        b = st.get('before')
        if isinstance(b, dict) and b.get('f') == floor and b.get('hp') == hp:
            return i
    return None


def authoritative_remaining(walk_path, seed_save, capture_path, stage, start_stat, auto,
                            start_floor=None, start_hp=None, consumed_npc=None,
                            consumed_ev=None, walked_tiles=None, cp_counts=None):
    """用共享 Game 重放 walk，返回最终每层剩余资源 + ratio_of。

    cp_counts: {walk coalesced 已执行步数: 检查点名}。重放每 record 一步全图聚合
    地图侧剩余(裸钥/怪金)存入 raw_aggs——convert 返回后按「coalesced 步对象即
    raw 步对象」的身份映射(id())定位检查点对应的 raw 步, 取该 raw 步执行完的
    聚合存入返回值 cp_map。检查点 sheet 的「剩余(地图)」「地图剩余金币」数据源,
    与最终剩余同一权威口径。注意: 不能按 hero 当前层做增量缓存——fly/换层步会
    顺带结算旧层的 deferred auto sweep(after.floor 已是新层而旧层地图变了,
    41206 MT48 whiteKing sweep 实证), 必须全图重算。
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'search'))
    import recording_seed_to_game as R
    from src.solver.game_route import Game

    cp_map = {}
    raw_aggs = {} if cp_counts else None

    class _Game(Game):
        last = None

        def __init__(self, *a, **kw):
            super().__init__(*a, **kw)
            _Game.last = self

        def record(self, *a, **kw):
            super().record(*a, **kw)
            if raw_aggs is None:
                return
            my = mb = money = 0
            for f in self.floors:
                c = map_floor_remaining_key_gold(self, f)
                my += c[0]
                mb += c[1]
                money += c[2]
            raw_aggs[len(self.steps)] = {'map_yk': my, 'map_bk': mb, 'map_gold': money}

    R.Game = _Game
    seed = R.read_json(Path(seed_save))
    cap, _actions = R.load_capture(Path(capture_path))
    if start_stat is None:
        start_stat = find_start_stat(cap, start_floor, start_hp)
    res = R.convert(seed, cap, _actions, stage, Path(seed_save), Path(capture_path),
                    start_stat, auto_spec=auto)
    if not res.get('ok'):
        raise SystemExit('Game 重放失败: ' + '; '.join(list(dict.fromkeys(res['errors']))[:4]))
    g = _Game.last
    if raw_aggs:
        # coalesced 步是 raw 步(同一批 dict 对象)的子集——按身份映射定位检查点
        # 在 raw 步流中的位置, 取该 raw 步执行完的现场聚合。
        id_to_raw = {id(st): i for i, st in enumerate(g.steps)}
        for cidx in cp_counts:
            if not (1 <= cidx <= len(res['steps'])):
                print(f'警告: 检查点(步{cidx})超出重放步数, 地图列置空')
                continue
            r = id_to_raw.get(id(res['steps'][cidx - 1]))
            sn = raw_aggs.get(r + 1) if r is not None else None
            if sn is None:
                print(f'警告: 检查点(步{cidx})未能映射到重放原始步, 地图列置空')
            else:
                cp_map[cidx] = sn
    enemys = g.enemies
    rem_money = {}; rem_door = {}; rem_bare = {}; rem_potion = {}
    rem_npc = {}; rem_ev = {}; ratio_of = {}
    # 已消费商人/已触发事件由 walk 提供, 从 g.floors 里对应位置剔除(否则买过/触发过的仍显示剩余)
    for fid, floor in g.floors.items():
        ratio_of[fid] = int(getattr(floor, 'ratio') or 1)
        rm = 0; ry = rb = rr = 0; kk = {'y': 0, 'b': 0, 'r': 0}; pot = 0; npc = {}
        for pos, blk in floor.blocks.items():
            k = getattr(blk, 'kind', None); eid = getattr(blk, 'eid', '')
            if k == 'enemy':
                rm += int(enemys.get(eid, {}).get('money', 0))
            elif k == 'door':
                if eid == 'yellowDoor':
                    ry += 1
                elif eid == 'blueDoor':
                    rb += 1
                elif eid == 'redDoor':
                    rr += 1
            elif k == 'item':
                if eid == 'redPotion':
                    pot += 50 * ratio_of[fid]
                elif eid == 'bluePotion':
                    pot += 200 * ratio_of[fid]
                elif eid == 'yellowKey':
                    kk['y'] += 1
                elif eid == 'blueKey':
                    kk['b'] += 1
                elif eid == 'redKey':
                    kk['r'] += 1
            elif k == 'npc':
                npc[pos] = eid
        rem_money[fid] = rm
        rem_door[fid] = {'r': rr, 'b': rb, 'y': ry}
        rem_bare[fid] = kk
        rem_potion[fid] = pot
        if npc:
            rem_npc[fid] = []
            for pos, eid_tuple in npc.items():
                px, py = pos[0], pos[1]
                if eid_tuple.endswith('Shop') or eid_tuple in ('trader', 'specialTrader'):
                    keep = True          # 商店/交易商人 -> 必有机制作用
                    _eid = eid_tuple
                elif eid_tuple in _FLAVOR_NPC:
                    if f'{fid}:{px},{py}' in MERCHANT_FUNC:
                        keep = True        # 是已知交易商人(如 MT31 钥匙包, 由 TRADER_TABLE 驱动)
                    else:
                        ev = floor.events.get(f'{px},{py}')
                        s = json.dumps(ev, ensure_ascii=False) if ev is not None else ''
                        keep = any(kw in s for kw in _REWARD_KW)   # 纯剧情无奖励 -> 忽略
                    _eid = eid_tuple
                else:
                    keep = True          # 其它未知 npc 保守保留
                    _eid = eid_tuple
                if keep and (fid, px, py) not in consumed_npc:
                    rem_npc[fid].append((px, py, _eid))
        ev = getattr(floor, 'events', None) or {}
        if ev:
            rem_ev[fid] = []
            for k, v in ev.items():
                try:
                    kx, ky = int(k.split(',')[0]), int(k.split(',')[1])
                except (ValueError, AttributeError):
                    kx = ky = -1
                if (fid, kx, ky) in consumed_ev or (fid, kx, ky) in consumed_npc:
                    continue   # 已触发 / 该位置是已消费的商店/商人 -> 不算剩余
                if walked_tiles and (fid, kx, ky) in walked_tiles:
                    continue   # 英雄实际踩过该格 => step-on 事件已触发
                if not _event_mechanical(v):
                    continue   # 渲染装饰(noPass墙/空data) 不算剩余事件
                if isinstance(v, dict) and v.get('enable') is False:
                    continue   # 2026-09-10 用户口径：enable:false=作者禁用，live 永不触发，不算剩余
                rem_ev[fid].append((k, _event_snippet(v)))
    return {
        'remaining_authoritative': True,
        'rem_money': rem_money, 'rem_door': rem_door, 'rem_bare': rem_bare,
        'rem_potion': rem_potion, 'rem_npc': rem_npc, 'rem_ev': rem_ev,
        'ratio_of': ratio_of, 'cp_map': cp_map,
    }


# --------------------------------------------------------------------------- #
# 主逻辑
# --------------------------------------------------------------------------- #
def build(walk_path, maps_dir, seed_save=None, capture=None, stage=None,
          start_stat=None, auto=None, rem_walk_path=None, checkpoints=None):
    walk = _load_json(walk_path)
    ws = walk_stats(walk['steps'])
    cps = None
    if checkpoints:
        cps = resolve_checkpoints(walk['steps'], ws['effective_count'],
                                  ws['final_state'], checkpoints)
    ratio_of, rem = {}, {
        'remaining_authoritative': False,
        'rem_money': {}, 'rem_door': {}, 'rem_bare': {}, 'rem_potion': {},
        'rem_npc': {}, 'rem_ev': {},
    }
    rem_walk = None
    if rem_walk_path:
        # 拼接 walk(多段 provenance)时: 汇总增量来自本 walk, 权威重放的 seed/capture/stage
        # 取自接续段 walk(其 Game 重放从未到楼层继承种子存档=此前区段验证后的末态)。
        rem_walk = _load_json(rem_walk_path)
    # 未显式给 seed/capture/stage 时自动读 walk 自带 provenance(转换时记录的真实参数)。
    if not (seed_save and capture and stage):
        pv = ((rem_walk or {}).get('provenance') or (walk.get('provenance') or {}))
        seed_save = seed_save or pv.get('seed_save')
        capture = capture or pv.get('capture')
        stage = stage or pv.get('stage')
        # auto 解析顺序: 显式 CLI --auto > provenance.auto_spec(转换时记录的种子 base,
        # 新版 converter 才有) > 默认全 false(slot1 录像的种子 base)。绝不能用
        # provenance['auto'](转换终态 flags)当种子 base——slot1 录像终态全 true 而
        # 种子 base 全 false, 用终态重放会发散(39529 实证 action#110 楼层错乱)。
        if auto is None:
            auto = pv.get('auto_spec') or 'battle=false,item=false,wall=false'
        if seed_save and capture and stage:
            print(f'[auto] 用 provenance: seed={seed_save} capture={capture} stage={stage} '
                  f'auto={auto}')
    if seed_save and capture and stage:
        src = rem_walk or walk
        rem = authoritative_remaining(str(rem_walk_path or walk_path), seed_save, capture, stage,
                                      start_stat, auto,
                                      start_floor=src['steps'][0]['before'].get('floor'),
                                      start_hp=src['steps'][0]['before'].get('hp'),
                                      consumed_npc=ws.get('consumed_npc') or set(),
                                      consumed_ev=ws.get('consumed_ev') or set(),
                                      walked_tiles=ws.get('walked_tiles') or set(),
                                      cp_counts=({idx: name for name, idx, _ in cps}
                                                 if cps else None))
        ratio_of = rem['ratio_of']
    else:
        print('警告: 未提供 --seed-save/--capture/--stage 且 walk 无可用 provenance，'
              '每层剩余怪将用 walk 自算(会高估)；建议提供录制数据重放共享 Game。', file=sys.stderr)

    # 拾取血量折算(需每层 ratio；floor_bad 记 1 单位=1 红(50)、蓝记 2 单位)
    bad = ws['floor_bad']
    if ratio_of:
        potion_hp = sum(int(u) * 50 * ratio_of.get(f, 1) for f, u in bad.items())
    else:
        potion_hp = sum(int(u) * 50 for u in bad.values())

    def _agg(d):
        return sum(d.values())

    if cps:
        cp_rows = []
        start_hp = ws['start_state'].get('hp') or 0
        cp_map = rem.get('cp_map') or {}
        ratio_of = rem.get('ratio_of') or {}
        for name, idx, state in cps:
            h = checkpoint_hero_stats(walk['steps'], idx, state, start_hp, ratio_of)
            sn = cp_map.get(idx)
            if sn is None:
                if rem['remaining_authoritative']:
                    print(f'警告: 检查点「{name}」(已执行 {idx} 步)未捕获地图快照——'
                          '权威重放步数与 walk 不对齐, 地图列置空')
                sn = {'map_yk': None, 'map_bk': None, 'map_gold': None}
            cp_rows.append({
                '检查点': name, '步数': idx,
                'dmg': h['dmg'], '恢复血量': h['恢复血量'],
                '药瓶恢复HP': h['药瓶恢复HP'],
                '消耗yk': h['消耗']['yk'], '消耗bk': h['消耗']['bk'],
                '消耗rk': h['消耗']['rk'],
                '剩余yk(自己)': h['yk'], '剩余bk(自己)': h['bk'],
                '剩余yk(地图)': sn['map_yk'], '剩余bk(地图)': sn['map_bk'],
                '剩余yk(合计)': None if sn['map_yk'] is None else h['yk'] + sn['map_yk'],
                '剩余bk(合计)': None if sn['map_bk'] is None else h['bk'] + sn['map_bk'],
                '获得金币(合计)': h['获得金币'], '获得金币(打怪)': h['打怪金币'],
                '持有金币': h['gold'],
                '地图剩余金币': sn['map_gold'],
                '商店购买情况': h['商店'],
            })
    else:
        cp_rows = None

    return dict(ws, **{
        'walk': str(walk_path),
        'rem_walk': str(rem_walk_path) if rem_walk_path else None,
        'potion_hp': potion_hp,
        'super_potion_hp': ws['super_potion_hp'],
        'remaining': rem,
        'checkpoint_rows': cp_rows,
        'zone_shop': ws['zone_shop'],
        'rem_total': {
            'money': _agg(rem['rem_money']),
            'door_y': sum(v['y'] for v in rem['rem_door'].values()),
            'door_b': sum(v['b'] for v in rem['rem_door'].values()),
            'door_r': sum(v['r'] for v in rem['rem_door'].values()),
            'bare_y': sum(v['y'] for v in rem['rem_bare'].values()),
            'bare_b': sum(v['b'] for v in rem['rem_bare'].values()),
            'bare_r': sum(v['r'] for v in rem['rem_bare'].values()),
            'potion': _agg(rem['rem_potion']),
        },
    })


# --------------------------------------------------------------------------- #
# sheets
# --------------------------------------------------------------------------- #
def build_sheets(ws):
    res = ws['remaining']
    fs = ws['final_state']
    C = {'yk': '黄', 'bk': '蓝', 'rk': '红'}

    rows = [['分楼层汇总记录（最终50F真魔王封印后/击杀前）']]
    rows.append(['数据源: walk=' + str(ws.get('walk', ''))])
    if ws.get('rem_walk'):
        rows.append(['权威重放种子来自接续段 walk: ' + str(ws.get('rem_walk')) +
                     '（汇总增量=本 walk 全线；未到楼层末态继承其种子存档）'])
    st = ws.get('start_state') or {}
    rows.append(['起点状态: ' + ' '.join(f'{k}={st.get(k)}' for k in
                                        ('floor', 'hp', 'atk', 'def', 'yk', 'bk', 'rk', 'gold')
                                        if st.get(k) is not None)])
    rows.append([])
    hdr = ['剩余状态(HP)', '剩余状态(ATK)', '剩余状态(DEF)', '剩余状态(金币)',
           'dmg', '魔法伤害量', '拾取血量(已拾血瓶)', '药瓶恢复HP(红+蓝)', '圣水恢复HP(superPotion)', '剩余血量',
           '总获金币', '打怪金币', '卖yk金币', '其它金币', '剩余怪金']
    row = [fs.get('hp'), fs.get('atk'), fs.get('def'), fs.get('gold'),
           ws['dmg_total'], ws['magic_dmg'], ws['potion_hp'], ws['potion_hp'],
           ws.get('super_potion_hp', 0), fs.get('hp'),
           ws['total_income'], ws['monster_loot'], ws['sell_yk_gold'],
           ws['other_gold'], ws['rem_total']['money']]
    rows.append(hdr); rows.append(row)
    rows.append(['<= 金币对账: 总获金=打怪+卖yk+其它；打怪=击杀+auto+事件生成怪收入'
                 '(其它=事件/NPC赠送, 如MT2老头+1000、MT32骑士队长先攻+100)'])

    rows.append([])
    rows.append(['钥匙对账(每色)'])
    rows.append(['颜色', '初始', '裸拾取', '商人购买', '开门消耗', '出售', '最终库存', '对账(=0?)'])
    ztot_keys = [0, 0, 0]
    for i, c in enumerate(('yk', 'bk', 'rk')):
        init = ws['init_keys'][c]
        buy = ws['key_buy'].get(c, 0)
        pick = ws['key_pick'].get(c, 0)
        opened = ws['door_open'][c]
        sold = ws['key_sell'].get(c, 0)
        final = ws['final_keys'][c]
        rows.append([f'{C[c]}钥', init, pick, buy, opened, sold, final,
                     init + pick + buy - opened - sold - final])
        ztot_keys[i] = (opened, pick, buy)
    rows.append(['说明：裸拾取=地图裸钥(不含商人买)；商人买另列；对账=初始+裸拾+买−开−售−最终'])
    rows.append(['合计(开/裸拾/买): 黄', ztot_keys[0][0], ztot_keys[0][1], ztot_keys[0][2],
                 '蓝', ztot_keys[1][0], ztot_keys[1][1], ztot_keys[1][2],
                 '红', ztot_keys[2][0], ztot_keys[2][1], ztot_keys[2][2]])

    rows.append([])
    rows.append(['各区商店购买次数', '总计', '攻', '防', '血'])
    znames = {1: '1区(1-10F)', 2: '2区(11-20F)', 3: '3区(21-30F)',
              4: '4区(31-40F)', 5: '5区(41-50F)'}
    ztot = {'攻': 0, '防': 0, '血': 0}
    for z in range(1, 6):
        d = ws['zone_shop'].get(z, {})
        for k in ztot:
            ztot[k] += d.get(k, 0)
        rows.append([znames[z], sum(d.values()), d.get('攻', 0), d.get('防', 0), d.get('血', 0)])
    rows.append(['合计', sum(ztot.values()), ztot['攻'], ztot['防'], ztot['血']])
    sg = ws['shop_gain']
    rows.append(['累计商店属性增益', '', f"攻+{sg['攻']}", f"防+{sg['防']}", f"血+{sg['血']}"])

    rows.append([])
    rows.append(['全图剩余资源（authoritative Game 末态）' if res['remaining_authoritative']
                 else '全图剩余资源（walk 自算，怪会高估）'])
    rt = ws['rem_total']
    rows.append(['剩余怪金', rt['money']])
    rows.append(['剩余门 黄/蓝/红', rt['door_y'], rt['door_b'], rt['door_r']])
    rows.append(['剩余裸钥 黄/蓝/红', rt['bare_y'], rt['bare_b'], rt['bare_r']])
    rows.append(['剩余血瓶HP(按区ratio)', rt['potion']])

    rows.append([])
    rows.append(['口径：截点=最终50F真魔王redKing击杀前；dmg含魔法；魔法伤害=地图伤害步；',
                 '拾取血量=已拾血瓶按ratio(红50×ratio蓝200×ratio)；剩余怪金=authoritative Game '
                 '末态未杀怪money；剩余裸钥/门/血瓶=Game 末态剩余；剩余血量=该层未拾血瓶HP折算。'])

    headers = ['楼层', '掉血量(当层dmg)', '花费yk', '花费bk', '花费rk',
               '剩余红门', '剩余rk', '剩余蓝门', '剩余bk',
               '剩余黄门', '剩余yk', '剩余血量(未拾血瓶HP)', '剩余怪金', '剩余商人', '剩余事件']
    freq = [headers]
    # 权威模式下列出 Game 重放的全部楼层(g.floors 覆盖 50 层): 接续段 walk 未到的楼层
    # 末态继承自种子存档(此前区段验证后的真实末态), 不能只列 walk 走到过的楼层。
    visited = ws.get('visited') or set()
    all_floors = sorted(set(visited) | set(res['rem_money']) | set(ws['floor_dmg']),
                        key=lambda f: floor_no(f))
    inherited = {f for f in all_floors if res['remaining_authoritative'] and f not in visited}
    for fid in all_floors:
        d = res['rem_door'].get(fid, {'y': 0, 'b': 0, 'r': 0})
        bare = res['rem_bare'].get(fid, {'y': 0, 'b': 0, 'r': 0})
        spend = ws['floor_spend'].get(fid, {'yk': 0, 'bk': 0, 'rk': 0})
        npc = ';'.join(_merchant_text(fid, x, y, eid)
                       for x, y, eid in res['rem_npc'].get(fid, [])) or '-'
        evs = ';'.join(_event_text(fid, k, sn)
                       for k, sn in res['rem_ev'].get(fid, [])) or '-'
        label = f'{fid}({zone_of(fid)}区)' + ('*' if fid in inherited else '')
        freq.append([
            label, ws['floor_dmg'].get(fid, 0),
            spend['yk'], spend['bk'], spend['rk'],
            d['r'], bare['r'], d['b'], bare['b'], d['y'], bare['y'],
            res['rem_potion'].get(fid, 0), res['rem_money'].get(fid, 0),
            npc, evs,
        ])
    if inherited:
        freq.append(['* = 该层本次 walk 未到，末态继承自起始存档(此前区段验证后的状态)'])

    cp_rows = ws.get('checkpoint_rows')
    cpsheet = None
    if cp_rows is not None:
        cpsheet = [
            ['检查点记录（累计口径，含已执行的全部步）'],
            ['口径: 检查点=首次到达该层(换层步 after)/魔龙前(magicDragon 击杀步 before)/'
             'TE最终boss前(50F redKing 击杀步 before, 录像止步时=末尾)。'],
            ['恢复血量=HP−起点HP+dmg(=药瓶+圣水+商店血); 药瓶恢复HP=红50×区ratio/蓝200×区ratio'
             '(不含圣水/商店血); 消耗yk/bk/rk=开门消耗(出售另见汇总钥匙对账); '
             '商店购买情况=按楼层+类型聚合。'],
            ['剩余(自己)=hero 库存; 剩余(地图)=共享 Game 权威重放至检查点步的未拾裸钥; '
             '合计=两者相加; 地图剩余金币=该时刻未杀怪 money(事件生成怪已 spawn 未杀计入)。'],
            ['获得金币(合计)=金币正增量累计(打怪+卖钥+事件赠送); 获得金币(打怪)=游戏'
             '「设置→游戏信息→数据统计」金币口径(engine statistics.money, 只计 afterBattle '
             '路径: 击杀/auto清怪/带伤害的事件战; 卖钥/事件赠送/炸弹杀怪不计; 41206 '
             'boss前=17485 与实机数据统计一致)。'],
            [],
        ]
        cols = list(cp_rows[0].keys())
        cpsheet.append(cols)
        cpsheet += [[r[c] for c in cols] for r in cp_rows]
    return rows, freq, cpsheet


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--walk', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--maps-dir', default='data/maps')
    ap.add_argument('--rem-walk',
                    help='拼接 walk 用: 汇总增量取本 walk, 权威重放 seed/capture/stage/auto '
                         '取自该接续段 walk 的 provenance')
    ap.add_argument('--seed-save')
    ap.add_argument('--capture')
    ap.add_argument('--stage', choices=('mt4-mt31', 'mt20-mt31', 'mt31-mt40', 'mt41-mt50'))
    ap.add_argument('--start-stat', type=int)
    ap.add_argument('--auto', default=None,
                    help='权威重放的种子 auto base。缺省读 provenance.auto_spec(新版 converter '
                         '记录)；旧 walk 无此字段时默认 battle=false,item=false,wall=false。'
                         'zone4/zone5 接续段 walk 通常需显式 battle=true,item=nopotion|true,wall=true')
    ap.add_argument('--no-stop-boss', action='store_true')
    ap.add_argument('--checkpoints', default=None,
                    help='追加检查点记录(逗号分隔, 直接并入汇总记录 sheet 末尾, 不单独开 sheet)。'
                         'spec: <N>层/MTxx=首次到达; before:<eid>=首个击杀该怪之前; '
                         '魔龙前; TE最终boss前; end。'
                         '例: --checkpoints 11层,31层,41层,魔龙前,TE最终boss前')
    args = ap.parse_args()

    ws = build(args.walk, Path(args.maps_dir), args.seed_save, args.capture, args.stage,
               args.start_stat, args.auto, rem_walk_path=args.rem_walk,
               checkpoints=(args.checkpoints.split(',') if args.checkpoints else None))
    summary_rows, floor_rows, cp_sheet = build_sheets(ws)
    sheets = [('汇总记录', summary_rows), ('分层记录', floor_rows)]
    if cp_sheet is not None:
        # 用户 2026-10-03: 检查点不单独开 sheet, 直接追加到汇总记录末尾
        summary_rows.append([])
        summary_rows += cp_sheet
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    write_xlsx(args.out, sheets)
    print(json.dumps({
        'final': {k: ws['final_state'].get(k) for k in
                  ('hp', 'atk', 'def', 'yk', 'bk', 'rk', 'gold', 'floor', 'dmg',
                   'yd', 'bd', 'rd', 'times1')},
        'dmg/magic/phys': [ws['dmg_total'], ws['magic_dmg'], ws['phys_dmg']],
        'potion_hp': ws['potion_hp'],
        'super_potion_hp': ws.get('super_potion_hp', 0),
        'income_总=打怪+卖yk+其它': [ws['total_income'], ws['monster_loot'],
                                   ws['sell_yk_gold'], ws['other_gold']],
        'remaining_authoritative': ws['remaining']['remaining_authoritative'],
        'rem_money_total': ws['rem_total']['money'],
        'rem_bare_keys_y/b/r': [ws['rem_total']['bare_y'], ws['rem_total']['bare_b'],
                                ws['rem_total']['bare_r']],
        'rem_doors_y/b/r': [ws['rem_total']['door_y'], ws['rem_total']['door_b'],
                            ws['rem_total']['door_r']],
        'rem_potion_hp_total': ws['rem_total']['potion'],
        'key_ledger(开/裸拾/买/卖/终)': {
            '黄': [ws['door_open']['yk'], ws['key_pick'].get('yk', 0),
                   ws['key_buy'].get('yk', 0), ws['key_sell'].get('yk', 0), ws['final_keys']['yk']],
            '蓝': [ws['door_open']['bk'], ws['key_pick'].get('bk', 0),
                   ws['key_buy'].get('bk', 0), ws['key_sell'].get('bk', 0), ws['final_keys']['bk']],
            '红': [ws['door_open']['rk'], ws['key_pick'].get('rk', 0),
                   ws['key_buy'].get('rk', 0), ws['key_sell'].get('rk', 0), ws['final_keys']['rk']]},
        'zone_shop': ws['zone_shop'],
        'n_floors_listed': len(set(ws.get('visited') or ()) | set(ws['remaining']['rem_money'])
                               | set(ws['floor_dmg'])),
        'n_floors_visited': len(ws.get('visited') or ()),
        'out': args.out,
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()