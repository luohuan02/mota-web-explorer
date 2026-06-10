
# Allow scripts to import project-root modules after being moved under scripts/.
import os as _codex_os
import sys as _codex_sys
_codex_root = _codex_os.path.dirname(_codex_os.path.dirname(_codex_os.path.abspath(__file__)))
if _codex_root not in _codex_sys.path:
    _codex_sys.path.insert(0, _codex_root)

#!/usr/bin/env python3
"""Test browser integration with agent-browser - persistent profile!"""

import sys
sys.path.insert(0, '')

from src.legacy.browser import BrowserController


def main():
    print("="*60)
    print("魔塔浏览器集成测试 (持久化Profile)")
    print("="*60)
    print()

    browser = BrowserController()
    print(f"Profile目录: {browser.profile_path}")
    print()

    print("正在打开浏览器...")
    success = browser.open_game()
    if not success:
        print("打开失败！")
        return

    print("\n读取游戏状态...")
    state = browser.read_game_state()
    print(f"  楼层: {state.floor}")
    print(f"  位置: ({state.x}, {state.y})")
    print(f"  HP: {state.hp}")
    print(f"  攻击/防御: {state.atk}/{state.def_}")
    print(f"  钥匙: 黄={state.yk}, 蓝={state.bk}, 红={state.rk}")

    print("\n读取地图数据...")
    map_data = browser.export_floor_map()
    if map_data:
        print(f"  楼层: {map_data.get('floorId')}")
        print(f"  尺寸: {map_data.get('width')}x{map_data.get('height')}")
        print(f"  节点数: {len(map_data.get('blocks', []))}")

    print("\n测试完成！")
    print("提示: 下次运行时会复用相同Profile，你的游戏进度/登录状态都会被保存！")
    print("\n按回车关闭浏览器...")
    input()
    browser.close()


if __name__ == "__main__":
    main()
