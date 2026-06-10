#!/usr/bin/env python3
"""Download MT4/MT5/MT6 map data from browser to local JSON files."""
# Allow scripts to import project-root modules after being moved under scripts/.
import os as _codex_os
import sys as _codex_sys
_codex_root = _codex_os.path.dirname(_codex_os.path.dirname(_codex_os.path.abspath(__file__)))
if _codex_root not in _codex_sys.path:
    _codex_sys.path.insert(0, _codex_root)

import json
import subprocess
import sys
import os

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AGENT = r"D:\nvm4w\nodejs\agent-browser.cmd"
MAP_DIR = os.path.join("data", "maps")
os.makedirs(MAP_DIR, exist_ok=True)

def run_js(js):
    """Run JS via agent-browser."""
    result = subprocess.run(
        [AGENT, "--auto-connect", "eval", js],
        capture_output=True, text=True,
        shell=False, encoding='utf-8', errors='ignore',
        timeout=60
    )
    out = result.stdout.strip()
    if not out:
        print(f"  DBG: rc={result.returncode}, stderr={result.stderr[:300]}")
        return None
    # agent-browser wraps output in double quotes, and escapes internal quotes
    # e.g. output is: "{\\"f\\":\\"MT4\\",...}"
    if out.startswith('"') and out.endswith('"'):
        out = out[1:-1]
        out = out.replace('\\"', '"')
    try:
        return json.loads(out)
    except Exception as e:
        # Try finding JSON directly
        idx = out.find('{')
        if idx < 0:
            idx = out.find('[')
        if idx >= 0:
            try:
                return json.loads(out[idx:])
            except:
                pass
        print(f"  DBG: parse error {e}, raw={out[:200]}")
        return None

# 1. Hero state
print("[1/4] Reading hero state...")
hero = run_js('JSON.stringify({f:core.status.floorId,x:core.status.hero.loc.x,y:core.status.hero.loc.y,h:core.status.hero.hp,a:core.status.hero.atk,d:core.status.hero.def,yk:core.status.hero.items.tools.yellowKey,bk:core.status.hero.items.tools.blueKey})')
if hero:
    print(f"  OK: Floor={hero['f']}, Pos=({hero['x']},{hero['y']}), HP={hero['h']}, ATK={hero['a']}, DEF={hero['d']}, YK={hero.get('yk',0)}, BK={hero.get('bk',0)}")
    with open(os.path.join(MAP_DIR, 'hero_state.json'), 'w', encoding='utf-8') as f:
        json.dump(hero, f, ensure_ascii=False, indent=2)
else:
    print("  FAILED, using defaults")
    hero = {"f":"MT4","x":11,"y":10,"h":926,"a":10,"d":10,"yk":4,"bk":1}
    with open(os.path.join(MAP_DIR, 'hero_state.json'), 'w', encoding='utf-8') as f:
        json.dump(hero, f, ensure_ascii=False, indent=2)

# 2-4. Map data - use different approach for blocks to avoid undefined errors
for fid in ['MT4', 'MT5', 'MT6']:
    print(f"\n[{['MT4','MT5','MT6'].index(fid)+2}/4] Reading {fid} map...")

    # Read basic map structure first
    js1 = 'JSON.stringify({w:core.status.maps["' + fid + '"].width,h:core.status.maps["' + fid + '"].height,m:core.status.maps["' + fid + '"].map})'
    basic = run_js(js1)
    if not basic:
        print(f"  FAILED to read {fid} basic info")
        continue

    # Read blocks count
    js2 = 'core.status.maps["' + fid + '"].blocks.length'
    result = subprocess.run(
        [AGENT, "--auto-connect", "eval", js2],
        capture_output=True, text=True, shell=False,
        encoding='utf-8', errors='ignore', timeout=30
    )
    bl_count = result.stdout.strip()
    print(f"  Size: {basic['w']}x{basic['h']}, Blocks count: {bl_count}")

    # Read blocks in chunks to avoid too-long output
    try:
        bl_count = int(bl_count)
    except:
        bl_count = 0

    all_blocks = []
    chunk_size = 30
    for offset in range(0, max(bl_count, 1), chunk_size):
        js3 = 'JSON.stringify(core.status.maps["' + fid + '"].blocks.slice(' + str(offset) + ',' + str(min(offset+chunk_size, bl_count)) + ').map(function(b){return{x:b.x,y:b.y,id:b.event?b.event.id:"",cls:b.event?b.event.cls:""}}))'
        chunk = run_js(js3)
        if chunk and isinstance(chunk, list):
            all_blocks.extend(chunk)
        else:
            print(f"    Chunk {offset}-{offset+chunk_size} failed")

    print(f"  Got {len(all_blocks)} blocks")

    # Combine
    data = {
        'w': basic['w'],
        'h': basic['h'],
        'm': basic['m'],
        'bl': all_blocks
    }
    with open(os.path.join(MAP_DIR, f'{fid.lower()}_map.json'), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  Saved {os.path.join(MAP_DIR, f'{fid.lower()}_map.json')}")

print("\nDone! Files saved under data/maps/")
