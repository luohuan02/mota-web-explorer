#!/usr/bin/env python3
"""Explicit zone-3 game events used by shared-Game searches."""

from __future__ import annotations

from typing import Any


def add_mt39_center_fly_if_solved(game: Any) -> None:
    if game.block_at("MT39", (4, 2)) or game.block_at("MT39", (6, 4)):
        return
    before = game.snapshot()
    game.set_block("MT39", (4, 4), "item", "centerFly3", 331)
    game.record("事件奖励", (4, 4), "centerFly3", before, "39F 谜题生成中心对称飞行器")


def open_mt39_puzzle(game: Any) -> None:
    game.set_segment("39F 谜题与中心飞行器")
    game.go_to("MT39", 2, 8, "39F 开蓝门进谜题")
    game.go_to("MT39", 4, 2, "39F 谜题：第一行中间")
    game.go_to("MT39", 6, 4, "39F 谜题：第二行右边")
    add_mt39_center_fly_if_solved(game)
    game.go_to("MT39", 4, 4, "39F 拾取中心对称飞行器")
    game.state["centerFly"] = max(int(game.state.get("centerFly", 0)), 3)
    game.state["centerFly3"] = True


def use_center_fly_to_mt40_boss_area(game: Any) -> None:
    count = int(game.state.get("centerFly", 0))
    if count <= 0 and not game.state.get("centerFly3"):
        game.fail("没有中心对称飞行器，不能飞入40F Boss区域")
    if game.state["floor"] != "MT40":
        game.fail(f"当前楼层 {game.state['floor']}，不能在40F使用中心对称飞行器")
    before = game.snapshot()
    game.state["x"], game.state["y"] = 12 - game.state["x"], 12 - game.state["y"]
    if count > 0:
        game.state["centerFly"] = count - 1
    game.state["centerFly3"] = int(game.state.get("centerFly", 0)) > 0
    game.state["usedCenterFly40"] = True
    game.record("事件", (game.state["x"], game.state["y"]), "centerFly3", before, "40F 中心对称飞行")


def event_mt40_boss(game: Any) -> None:
    """Apply the verified post-guard 40F captain reward/map mutation."""
    before = game.snapshot()
    gain = int(game.enemies["yellowKnight"].get("money", 0))
    game.state["gold"] += gain * (2 if game.state.get("coin") else 1)
    for pos in [(5, 4), (4, 4), (3, 4), (7, 4), (8, 4), (9, 4),
                (4, 2), (3, 2), (2, 2), (8, 2), (9, 2), (10, 2), (6, 1)]:
        game.set_ground("MT40", pos)
    for pos in [(2, 2), (3, 2), (4, 2)]:
        game.set_block("MT40", pos, "item", "yellowKey", 21)
    for pos in [(8, 2), (9, 2), (10, 2)]:
        game.set_block("MT40", pos, "item", "redGem", 27)
    for pos in [(3, 4), (4, 4), (5, 4)]:
        game.set_block("MT40", pos, "item", "bluePotion", 32)
    for pos in [(7, 4), (8, 4), (9, 4)]:
        game.set_block("MT40", pos, "item", "blueGem", 28)
    game.set_block("MT40", (6, 1), "terrain", "upFloor", 87)
    game.set_ground("MT40", (6, 7))
    game.state["x"], game.state["y"] = 6, 7
    game.record("事件奖励", (6, 7), "yellowKnight", before, "40F Boss事件生成楼梯与奖励")
