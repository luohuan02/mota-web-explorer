
# Allow scripts to import project-root modules after being moved under scripts/.
import os as _codex_os
import sys as _codex_sys
_codex_root = _codex_os.path.dirname(_codex_os.path.dirname(_codex_os.path.abspath(__file__)))
if _codex_root not in _codex_sys.path:
    _codex_sys.path.insert(0, _codex_root)

#!/usr/bin/env python3
"""Extract MT4, MT5, MT6 maps from browser and convert to autoclaw format"""
import json
import subprocess

agent = r"D:\nvm4w\nodejs\agent-browser.cmd"


def run(js):
    result = subprocess.run(
        [agent, "--auto-connect", "eval", js],
        capture_output=True, text=True,
        shell=True, encoding='utf-8', errors='ignore',
        timeout=30
    )
    out = result.stdout.strip()
    try:
        return json.loads(out)
    except:
        return out


print("="*60)
print("提取MT4/MT5/MT6地图")
print("="*60)

# Monster HP/ATK/DEF map (from autoclaw)
EM = {
    'greenSlime': (35,18,1), 'redSlime': (45,20,2), 'bat': (35,38,3),
    'skeleton': (50,42,6), 'skeletonSoldier': (55,52,12),
    'skeletonCaptain': (100,65,15), 'bluePriest': (60,32,8),
    'blueGuard': (100,180,110), 'yellowGuard': (50,48,22),
    'soldier': (210,200,65),
}


def extract_floor(fid):
    print(f"\n--- 提取 {fid} ---")

    # Read basic info
    width = run(f"core.status.maps.{fid}.width")
    height = run(f"core.status.maps.{fid}.height")
    print(f"  尺寸: {width}x{height}")

    # Read raw map (tile ids)
    raw_map = run(f"JSON.stringify(core.status.maps.{fid}.map)")
    map_data = json.loads(raw_map)
    print(f"  地图读取: {len(map_data)} 行")

    # Read blocks
    blocks_js = f"""JSON.stringify(core.status.maps.{fid}.blocks.map(b => ({{
        x: b.x, y: b.y,
        id: b.event?.id || '',
        cls: b.event?.cls || '',
        noPass: b.event?.noPass || false
    }})))"""
    blocks_raw = run(blocks_js)
    blocks = json.loads(blocks_raw)
    print(f"  区块数: {len(blocks)}")

    # Convert to autoclaw format: (x,y,t,eid,np)
    # t: 1=enemy, 2=door, 3=item, 4=stairs
    pf_blocks = []

    for b in blocks:
        x, y = b['x'], b['y']
        eid = b['id']
        cls = b['cls']
        np = False  # no-pass (wall)

        t = 0
        if cls == 'monsters' or eid in EM:
            t = 1
        elif cls == 'doors' or eid.endswith('Door'):
            t = 2
        elif cls == 'items' or eid.endswith('Key') or eid.endswith('Potion') or eid.endswith('Gem') or eid.startswith('sword') or eid.startswith('shield'):
            t = 3
        elif cls == 'stairs':
            t = 4

        if t > 0:
            pf_blocks.append((x, y, t, eid, np))

    # Build final structure
    result = {
        'fid': fid,
        'W': int(width),
        'H': int(height),
        'm': map_data,
        'bl': pf_blocks
    }

    filename = f"_pf_{fid.lower()}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"  保存到: {filename}")

    return result


# Extract all three floors
mt4 = extract_floor("MT4")
mt5 = extract_floor("MT5")
mt6 = extract_floor("MT6")

print("\n完成！")
