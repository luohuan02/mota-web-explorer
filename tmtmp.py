# -*- coding: utf-8 -*-
import json

w = json.load(open('outputs/results/41200_walk.json', encoding='utf-8'))
print('--- 基线 MT43->MT44 上下文')
for i, s in enumerate(w['steps']):
    if 940 <= i <= 960:
        print(f"  {i} {s['action']:3s} {s['floor']} {s.get('eid') or ''} "
              f"->({s['after']['x']},{s['after']['y']}) | {(s.get('note') or '')[:66]}")
print('MT43 changeFloor:', json.load(open('data/maps/mt43_map.json', encoding='utf-8-sig')).get('changeFloor'))

c = json.load(open('tmp/41200_l2b_fail2.json', encoding='utf-8')) if False else None
