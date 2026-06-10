
# Allow scripts to import project-root modules after being moved under scripts/.
import os as _codex_os
import sys as _codex_sys
_codex_root = _codex_os.path.dirname(_codex_os.path.dirname(_codex_os.path.abspath(__file__)))
if _codex_root not in _codex_sys.path:
    _codex_sys.path.insert(0, _codex_root)

#!/usr/bin/env python3
"""
魔塔策略探索 - 连接你当前已打开的浏览器
从第4层开始探索最优策略！
"""

import sys
import os
import json
sys.path.insert(0, '')

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.legacy.game_state import GameState
from src.legacy.browser import BrowserController


def main():
    print("="*70)
    print("魔塔策略探索 - 连接你的第4层进度")
    print("="*70)
    print()
    print("说明:")
    print("- 确保你已经在Chrome中打开了 https://h5mota.com/games/51/")
    print("- 并且已经玩到第4层！")
    print()
    input("按回车键连接...")

    browser = BrowserController()

    print("\n正在连接你的浏览器...")
    # Use auto-connect to your existing Chrome
    success = browser.connect_existing()
    if not success:
        print("连接失败！")
        print("\n尝试用我们的profile打开...")
        success = browser.open_game()
        if not success:
            print("也失败了，请确认Chrome已打开！")
            return

    print("\n--- 读取当前状态 ---")
    state = browser.read_game_state()
    print(f"楼层: {state.floor}")
    print(f"位置: ({state.x}, {state.y})")
    print(f"HP: {state.hp}")
    print(f"攻击: {state.atk}")
    print(f"防御: {state.def_}")
    print(f"黄钥匙: {state.yk}")
    print(f"蓝钥匙: {state.bk}")
    print(f"红钥匙: {state.rk}")

    print("\n--- 读取地图数据 ---")
    map_data = browser.export_floor_map()
    if map_data:
        print(f"楼层ID: {map_data.get('floorId')}")
        print(f"尺寸: {map_data.get('width')}x{map_data.get('height')}")
        blocks = map_data.get('blocks', [])
        print(f"节点数: {len(blocks)}")
        print()
        print("前10个节点:")
        for i, b in enumerate(blocks[:10]):
            print(f"  [{i}] {b}")

        out_dir = os.path.join("data", "state")
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "current_map.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(map_data, f, ensure_ascii=False, indent=2)
        print(f"\n已保存地图到 {out_path}")

    print()
    print("="*70)
    print("状态读取完成！")
    print("="*70)
    print()
    print("下一步可以:")
    print("1. 分析当前地图的节点")
    print("2. 运行单楼层搜索")
    print("3. 手动操作并记录")

    print()
    print("现在你可以在浏览器中继续玩，或按回车关闭连接...")
    input()
    browser.close()


if __name__ == "__main__":
    main()
