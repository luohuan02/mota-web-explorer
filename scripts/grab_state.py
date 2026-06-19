
# Allow scripts to import project-root modules after being moved under scripts/.
import os as _codex_os
import sys as _codex_sys
_codex_root = _codex_os.path.dirname(_codex_os.path.dirname(_codex_os.path.abspath(__file__)))
if _codex_root not in _codex_sys.path:
    _codex_sys.path.insert(0, _codex_root)

#!/usr/bin/env python3
import json
import os
import subprocess

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

agent = r"D:\nvm4w\nodejs\agent-browser.cmd"


def run(js):
    result = subprocess.run(
        [agent, "--cdp", "9222", "eval", js],
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
print("抓取完整状态")
print("="*60)

# Hero
print("\n[1] 勇者状态:")
hero = run("""JSON.stringify({
    loc: core.status.hero.loc,
    hp: core.status.hero.hp, hpmax: core.status.hero.hpmax,
    atk: core.status.hero.atk, def: core.status.hero.def,
    money: core.status.hero.money, lv: core.status.hero.lv,
    tools: core.status.hero.items?.tools || {}
})""")
print(hero)

# MT4 map structure
print("\n[2] MT4 map keys:")
map_keys = run("Object.keys(core.status.maps.MT4)")
print(map_keys)

print("\n[3] MT4 map type:")
map_type = run("typeof core.status.maps.MT4.map")
print(map_type)

print("\n[4] MT4 map[0] length (width):")
map_width = run("core.status.maps.MT4.map?.[0]?.length || 0")
print(map_width)

print("\n[5] MT4 map length (height):")
map_height = run("core.status.maps.MT4.map?.length || 0")
print(map_height)

print("\n[6] MT4 blocks type:")
blocks_type = run("typeof core.status.maps.MT4.blocks")
print(blocks_type)

print("\n[7] MT4 blocks length:")
blocks_len = run("core.status.maps.MT4.blocks?.length || 0")
print(blocks_len)

print("\n[8] First block sample:")
block1 = run("JSON.stringify(core.status.maps.MT4.blocks?.[0] || {})")
print(block1)

# Save full data
print("\n[9] Saving full state...")
full_data = run("""JSON.stringify({
    hero: {
        loc: core.status.hero.loc,
        hp: core.status.hero.hp, hpmax: core.status.hero.hpmax,
        atk: core.status.hero.atk, def: core.status.hero.def,
        money: core.status.hero.money, lv: core.status.hero.lv,
        tools: core.status.hero.items?.tools || {}
    },
    floorId: core.status.floorId,
    map: {
        width: core.status.maps.MT4.map?.[0]?.length || 0,
        height: core.status.maps.MT4.map?.length || 0,
        blocks: core.status.maps.MT4.blocks || []
    }
})""")
out_dir = os.path.join("data", "state")
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, "full_state.json")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(full_data)
print(f"Saved to {out_path}")

print("\nDone!")
