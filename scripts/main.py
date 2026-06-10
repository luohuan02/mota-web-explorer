
# Allow scripts to import project-root modules after being moved under scripts/.
import os as _codex_os
import sys as _codex_sys
_codex_root = _codex_os.path.dirname(_codex_os.path.dirname(_codex_os.path.abspath(__file__)))
if _codex_root not in _codex_sys.path:
    _codex_sys.path.insert(0, _codex_root)

#!/usr/bin/env python3
"""
魔塔自动探索主程序
整合 Pareto 优化、楼层搜索、回溯剪枝、Flyback 和浏览器控制
"""

import sys
import os
sys.path.insert(0, '')

from src.legacy.game_state import GameState
from src.legacy.floor_map import FloorMap
from src.legacy.floor_search import FloorSearch
from src.legacy.pareto import ParetoFrontier
from src.legacy.browser import BrowserController


def main():
    print("="*70)
    print("魔塔 51 层 自动探索优化系统")
    print("="*70)
    print()

    mode = input("选择模式: [1] 纯算法模拟  [2] 浏览器实际操作: ").strip()

    if mode == "2":
        run_browser_mode()
    else:
        run_simulation_mode()


def run_simulation_mode():
    """纯算法模拟模式 - 测试优化策略"""
    print("\n--- 模拟模式 ---")
    print()
    print("当前可用模块:")
    print("- Pareto 前沿优化 (src/pareto.py)")
    print("- 游戏状态管理 (src/game_state.py)")
    print("- 楼层地图解析 (src/floor_map.py)")
    print("- 单楼层 Dijkstra 搜索 (src/floor_search.py)")
    print("- 多楼层协调 (src/multi_floor.py)")
    print("- 逐步优化 (src/stepwise.py)")
    print("- Flyback 候选发现 (src/flyback.py)")
    print("- 回溯剪枝 (src/backward.py)")
    print()
    print("请选择一个测试:")
    print("1. Pareto 测试")
    print("2. 运行所有单元测试")
    choice = input("选择 (1/2): ").strip()

    if choice == "1":
        test_pareto()
    else:
        run_all_tests()


def test_pareto():
    """测试 Pareto 优化"""
    from src.legacy.pareto import ParetoFrontier
    frontier = ParetoFrontier()
    print()
    print("添加候选解...")
    candidates = [
        (500, 5, 2, 15, 15),
        (450, 6, 3, 16, 14),
        (520, 4, 1, 14, 14),
        (480, 5, 2, 16, 16),
    ]
    for cand in candidates:
        frontier.add(cand)
        print(f"  加了 {cand}，当前前沿共 {len(frontier)} 个解")

    print()
    print("最终 Pareto 前沿:")
    for sol in frontier:
        print(f"  HP={sol.hp}, YK={sol.yk}, BK={sol.bk}, ATK={sol.atk}, DEF={sol.def_}")


def run_all_tests():
    """运行所有单元测试"""
    import subprocess
    test_dir = os.path.join(os.path.dirname(__file__), "tests")
    test_scripts = [
        "run_pareto_test.py",
        "run_gamestate_test.py",
        "run_floormap_test.py",
        "run_floorsearch_test.py",
        "run_config_test.py",
        "run_multifloor_test.py",
        "run_stepwise_test.py",
        "run_flyback_test.py",
        "run_backward_test.py",
        "run_browser_test.py",
    ]

    for script in test_scripts:
        path = os.path.join(test_dir, script)
        if os.path.exists(path):
            print()
            print("="*50)
            print(f"运行 {script}...")
            print("="*50)
            try:
                result = subprocess.run(
                    [sys.executable, path],
                    cwd=os.path.dirname(__file__),
                    capture_output=False,
                    text=True
                )
            except Exception as e:
                print(f"执行失败: {e}")


def run_browser_mode():
    """浏览器实际操作模式"""
    print("\n--- 浏览器模式 ---")
    print()

    browser = BrowserController()
    print(f"Profile 目录: {browser.profile_path}")
    print()
    print("正在打开浏览器...")
    success = browser.open_game()
    if not success:
        print("打开浏览器失败！")
        return

    print()
    print("浏览器已打开！请在页面中手动操作:")
    print("1. 点击 '开始游戏'")
    print("2. 选择难度并开始")
    print()
    input("准备好后，按回车键继续...")

    print()
    print("读取当前状态...")
    state = browser.read_game_state()
    print(f"  楼层: {state.floor}")
    print(f"  HP: {state.hp}")
    print(f"  ATK/DEF: {state.atk}/{state.def_}")

    print()
    print("读取地图...")
    map_data = browser.export_floor_map()
    if map_data:
        print(f"  楼层: {map_data.get('floorId')}")
        print(f"  地图尺寸: {map_data.get('width')}x{map_data.get('height')}")

    print()
    print("浏览器模式框架已搭建！")
    print("接下来可以:")
    print("- 解析地图数据")
    print("- 运行搜索算法")
    print("- 执行移动")

    print()
    input("按回车键关闭浏览器...")
    browser.close()


if __name__ == "__main__":
    main()
