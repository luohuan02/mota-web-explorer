#!/usr/bin/env python3
"""MT44 双卫兵机关门 + clone COW 事件泄漏回归 (2026-09-17 夜间线模型修复)。

1. MT44 specialDoor(6,8): 双 redGuard(5,9)/(7,9) 全灭后开门 (afterBattle flag:44,
   web mt44_map.json); 炸弹击杀走 use_bomb -> after_action 同样触发。
2. clone COW: clone 共享 Floor 对象, trigger_tile_event 的事件消费 (events.pop)
   不得泄漏到 clone —— 否则 clone 上同事件永不再触发 (41301 walk [1198] 实锤)。
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.solver.game_route import read_json
from scripts.search.zone3_game_route import Zone3Game


def build_game() -> Zone3Game:
    snapshot = read_json(ROOT / "best" / "checkpoints" / "zone3_2atk3atk5def_seed_mt31_save.json")
    game = Zone3Game(snapshot)
    game.strict_live_model = True
    game.auto_flags = {"battle": True, "item": "nopotion", "wall": True}
    return game


def test_mt44_door_after_battle() -> None:
    game = build_game()
    assert game.block_at("MT44", (6, 8)) is not None, "MT44 (6,8) 初始为 specialDoor"
    assert game.block_at("MT44", (6, 8)).eid == "specialDoor"

    guards = [(5, 9), (7, 9)]
    for pos in guards[:-1]:
        block = game.block_at("MT44", pos)
        assert block and block.kind == "enemy" and block.eid == "redGuard"
        game.set_ground("MT44", pos)
        game.after_action("MT44", pos, block)
        assert game.block_at("MT44", (6, 8)) is not None, "第一只卫兵死后门不开 (flag:44 未满)"

    pos = guards[-1]
    block = game.block_at("MT44", pos)
    game.set_ground("MT44", pos)
    game.after_action("MT44", pos, block)
    assert game.block_at("MT44", (6, 8)) is None, "双卫兵全灭后 specialDoor(6,8) 必须打开"
    assert game.block_at("MT44", (6, 6)).eid == "shield5", "门后 shield5 可达"


def test_mt44_door_via_bomb() -> None:
    game = build_game()
    # 41301 walk [969-970]: hero 到 (6,9) 用炸弹同时炸死双卫兵 -> [971] 过门。
    game.state["floor"] = "MT44"
    game.state["x"], game.state["y"] = (6, 9)
    game.state["bomb"] = max(game.state.get("bomb", 0), 1)
    game.use_bomb("回归: 44F 炸双卫兵")
    assert game.block_at("MT44", (5, 9)) is None
    assert game.block_at("MT44", (7, 9)) is None
    assert game.block_at("MT44", (6, 8)) is None, "炸弹击杀触发 afterBattle, 双杀后开门"


def test_trigger_event_cow_no_leak() -> None:
    game = build_game()
    clone = game.clone()
    # clone 共享 Floor 对象 (COW _owned=False)
    assert game.floors["MT50"] is clone.floors["MT50"], "clone 应共享 Floor (写时复制前提)"
    assert "6,5" in game.floors["MT50"].events
    assert "6,5" in clone.floors["MT50"].events

    # 原体触发 50F 小偷事件 (一次性, events.pop)
    assert game.trigger_tile_event("MT50", (6, 5)) is True
    assert game.block_at("MT50", (6, 5)).eid == "redKing"
    assert "6,5" not in game.floors["MT50"].events

    # 修复点: 事件消费不得泄漏到 clone
    assert "6,5" in clone.floors["MT50"].events, (
        "clone 的一次性事件必须独立保留; 若此处失败说明 events.pop 绕过了 COW"
    )
    assert clone.block_at("MT50", (6, 5)).eid == "thief", "clone 的地图不受原体事件影响"

    # clone 上同一事件仍可独立触发
    assert clone.trigger_tile_event("MT50", (6, 5)) is True
    assert clone.block_at("MT50", (6, 5)).eid == "redKing"


def main() -> int:
    test_mt44_door_after_battle()
    test_mt44_door_via_bomb()
    test_trigger_event_cow_no_leak()
    print("MT44 door + COW event leak regressions passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
