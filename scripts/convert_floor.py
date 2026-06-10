#!/usr/bin/env python3
"""Convert browser-extracted floor data to autoclaw format"""
# Allow scripts to import project-root modules after being moved under scripts/.
import os as _codex_os
import sys as _codex_sys
_codex_root = _codex_os.path.dirname(_codex_os.path.dirname(_codex_os.path.abspath(__file__)))
if _codex_root not in _codex_sys.path:
    _codex_sys.path.insert(0, _codex_root)

import json
import os

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MAP_DIR = os.path.join("data", "maps")

EM = {
    'greenSlime': (35,18,1), 'redSlime': (45,20,2), 'bat': (35,38,3),
    'skeleton': (50,42,6), 'skeletonSoldier': (55,52,12),
    'skeletonCaptain': (100,65,15), 'bluePriest': (60,32,8),
    'blueGuard': (100,180,110), 'yellowGuard': (50,48,22),
    'soldier': (210,200,65),
}

def convert(raw_path, out_path, fid):
    content = open(raw_path, encoding='utf-8').read().strip()
    raw = json.loads(content)
    # Handle double-encoded JSON from browser output
    if isinstance(raw, str):
        raw = json.loads(raw)
    W, H = raw['w'], raw['h']
    m = raw['m']

    # Handle compressed map format (h5mota uses 0 + row arrays alternating)
    if len(m) < H:
        # Decompress
        decompressed = []
        i = 0
        while i < len(m) and len(decompressed) < H:
            if m[i] == 0:
                i += 1
                if i < len(m) and isinstance(m[i], list):
                    decompressed.append(m[i])
                    i += 1
                else:
                    decompressed.append([0]*W)
            else:
                decompressed.append([0]*W)
                i += 1
        while len(decompressed) < H:
            decompressed.append([0]*W)
        m = decompressed

    blocks = []
    for b in raw['bl']:
        x, y, eid, cls = b['x'], b['y'], b['id'], b['cls']
        t = 0
        np = False
        if eid in ('upFloor', 'downFloor', 'fakeWall'):
            t = 4
        elif cls == 'monsters' or eid in EM:
            t = 1
        elif eid.endswith('Door'):
            t = 2
        elif cls == 'items' or eid.endswith('Key') or eid.endswith('Potion') or eid.endswith('Gem') or eid.startswith('sword') or eid.startswith('shield'):
            t = 3
        elif cls == 'animates' and (eid.endswith('Key') or eid.endswith('Potion') or eid.endswith('Gem') or eid.startswith('sword') or eid.startswith('shield')):
            t = 3
        if t > 0:
            blocks.append((x, y, t, eid, np))

    result = {
        'fid': fid,
        'W': W,
        'H': H,
        'm': m,
        'bl': blocks
    }
    json.dump(result, open(out_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print(f"Converted {raw_path} -> {out_path}")
    print(f"  Size: {W}x{H}, Blocks: {len(blocks)}")

convert(os.path.join(MAP_DIR, 'mt1_full_raw.json'), os.path.join(MAP_DIR, 'mt1_map.json'), 'MT1')
convert(os.path.join(MAP_DIR, 'mt3_full_raw.json'), os.path.join(MAP_DIR, 'mt3_map.json'), 'MT3')
