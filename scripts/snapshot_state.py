
# Allow scripts to import project-root modules after being moved under scripts/.
import os as _codex_os
import sys as _codex_sys
_codex_root = _codex_os.path.dirname(_codex_os.path.dirname(_codex_os.path.abspath(__file__)))
if _codex_root not in _codex_sys.path:
    _codex_sys.path.insert(0, _codex_root)

#!/usr/bin/env python3
"""
快速读取当前浏览器状态！
"""

import sys
import os
import json
import subprocess
sys.path.insert(0, '')

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_agent(cmd, args):
    agent_path = r"D:\nvm4w\nodejs\agent-browser.cmd"
    full_cmd = [agent_path, "--auto-connect"] + [cmd] + args
    try:
        result = subprocess.run(
            full_cmd,
            capture_output=True,
            text=True,
            timeout=30,
            shell=True,
            encoding='utf-8',
            errors='ignore'
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except Exception as e:
        print(f"Error: {e}")
        return None


def eval_js(js):
    out = run_agent("eval", [js])
    if not out:
        return None
    try:
        return json.loads(out)
    except:
        return out


def main():
    print("="*60)
    print("快速读取浏览器状态")
    print("="*60)

    # Test connection
    print("\n[1/3] 测试连接...")
    test = eval_js("1+1")
    if test is None:
        print("连接失败！请确保Chrome已打开并访问了游戏")
        return
    print(f"✓ 连接成功！1+1={test}")

    # Read state
    print("\n[2/3] 读取游戏状态...")
    state_js = """(function(){
        if(!window.core || !core.status) return {error:'no core'};
        var h = core.status.hero || {};
        var loc = h.loc || {x:1,y:1};
        var tools = h.items?.tools || {};
        return {
            floor: core.status.floorId || '?',
            x: loc.x, y: loc.y,
            hp: h.hp || 0, atk: h.atk || 0, def: h.def || 0,
            yk: tools.yellowKey || 0, bk: tools.blueKey || 0, rk: tools.redKey || 0
        };
    })()"""
    state = eval_js(state_js)
    if state:
        print(f"  楼层: {state.get('floor','?')}")
        print(f"  位置: ({state.get('x','?')}, {state.get('y','?')})")
        print(f"  HP: {state.get('hp','?')}")
        print(f"  ATK/DEF: {state.get('atk','?')}/{state.get('def','?')}")
        print(f"  钥匙: Y={state.get('yk','?')} B={state.get('bk','?')} R={state.get('rk','?')}")
        out_dir = os.path.join("data", "state")
        os.makedirs(out_dir, exist_ok=True)
        state_path = os.path.join(out_dir, "current_state.json")
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        print(f"  ✓ 保存到 {state_path}")

    # Read map
    print("\n[3/3] 读取地图...")
    map_js = """(function(){
        var fid = core.status.floorId;
        var md = core.status.maps?.[fid];
        if(!md) return {error:'no map'};
        return {
            floorId: fid,
            width: md.map?.[0]?.length || 0,
            height: md.map?.length || 0,
            map: md.map || [],
            blocks: md.blocks || []
        };
    })()"""
    map_data = eval_js(map_js)
    if map_data and "error" not in map_data:
        print(f"  楼层: {map_data.get('floorId')}")
        print(f"  尺寸: {map_data.get('width')}x{map_data.get('height')}")
        print(f"  节点数: {len(map_data.get('blocks', []))}")
        out_dir = os.path.join("data", "state")
        os.makedirs(out_dir, exist_ok=True)
        map_path = os.path.join(out_dir, "current_map.json")
        with open(map_path, "w", encoding="utf-8") as f:
            json.dump(map_data, f, ensure_ascii=False, indent=2)
        print(f"  ✓ 保存到 {map_path}")
    else:
        print("  读取地图失败")

    print("\n完成！")


if __name__ == "__main__":
    main()
