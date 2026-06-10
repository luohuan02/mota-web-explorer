
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
        [agent, "--auto-connect", "eval", js],
        capture_output=True, text=True,
        shell=True, encoding='utf-8', errors='ignore',
        timeout=20
    )
    try:
        return json.loads(result.stdout.strip())
    except:
        return result.stdout.strip()


print("="*60)
print("读取你的 MT4 完整状态")
print("="*60)

# Read hero state
print("\n--- 勇者状态 ---")
hero = run("""
(function(){
    var h = core.status.hero;
    var tools = h.items?.tools || {};
    return {
        loc: h.loc, hp: h.hp, hpmax: h.hpmax,
        atk: h.atk, def: h.def,
        yk: tools.yellowKey || 0,
        bk: tools.blueKey || 0,
        rk: tools.redKey || 0,
        money: h.money || 0,
        lv: h.lv || 0
    };
})()""")
print(json.dumps(hero, ensure_ascii=False, indent=2))

# Read current map
print("\n--- MT4 地图 ---")
map_data = run("""
(function(){
    var md = core.status.maps.MT4;
    return {
        width: md.map[0].length,
        height: md.map.length,
        blocks: md.blocks.map(function(b){
            return {
                x: b.x, y: b.y,
                id: b.event?.id || '',
                cls: b.event?.cls || ''
            };
        })
    };
})()""")
print(f"尺寸: {map_data['width']}x{map_data['height']}")
print(f"节点数: {len(map_data['blocks'])}")

# Save
out_dir = os.path.join("data", "state")
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, "mt4_state.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump({"hero": hero, "map": map_data}, f, ensure_ascii=False, indent=2)
print(f"\n已保存到 {out_path}")

# Print blocks
print("\n--- 地图节点列表 ---")
for i, b in enumerate(map_data['blocks'][:30]):  # 前30个
    print(f"[{i:2d}] ({b['x']:2d},{b['y']:2d}) {b['cls']:10s} {b['id']}")
if len(map_data['blocks']) > 30:
    print(f"  ... 还有 {len(map_data['blocks'])-30} 个")
