#!/usr/bin/env python3
"""Focused regressions for the shared Game zone-3 adapter."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.solver.game_route import read_json
from scripts.search.zone3_game_route import Zone3Game


def main() -> int:
    snapshot = read_json(ROOT / "best" / "checkpoints" / "zone3_2atk3atk5def_seed_mt31_save.json")
    game = Zone3Game(snapshot)
    game.strict_live_model = True
    game.auto_flags = {"battle": True, "item": "nopotion", "wall": True}

    assert "events" in vars(game.floors["MT33"]), "通用 Floor 必须保留事件格"
    game.event_mt33_sword_trap()
    assert game.block_at("MT33", (10, 8)).eid == "specialDoor"
    assert game.block_at("MT33", (10, 10)).eid == "sword3"

    guards = [(9, 5), (11, 5), (9, 7), (11, 7)]
    for pos in guards[:-1]:
        block = game.block_at("MT33", pos)
        assert block and block.kind == "enemy"
        game.set_ground("MT33", pos)
        game.after_action("MT33", pos, block)
        assert game.block_at("MT33", (10, 8)).eid == "specialDoor"
        assert game.block_at("MT33", (10, 10)).eid == "sword3"

    pos = guards[-1]
    block = game.block_at("MT33", pos)
    assert block and block.kind == "enemy"
    game.set_ground("MT33", pos)
    game.after_action("MT33", pos, block)
    assert game.block_at("MT33", (10, 8)) is None, "四守卫全灭后才开 sword3 机关门"
    assert game.block_at("MT33", (10, 10)).eid == "sword3"

    center = [(5, 4), (7, 4), (9, 4), (11, 4), (5, 8), (7, 8), (9, 8), (11, 8)]
    assert game.block_at("MT34", (2, 6)).eid == "unbreakableWall"
    for pos in center:
        block = game.block_at("MT34", pos)
        assert block and block.kind == "enemy"
        game.set_ground("MT34", pos)
        game.after_action("MT34", pos, block)
    # MT34 中心事件是 autoEvent（auto_sweep 末尾触发），不是 afterBattle。
    game._check_auto_events("MT34")
    assert game.block_at("MT34", (2, 6)).eid == "redKey", "中心八怪事件必须用红钥匙替换原不可破墙"
    game.state["floor"] = "MT34"
    game.state["x"], game.state["y"] = (2, 5)
    before_center_yk = game.state["yk"]
    game.go_to("MT34", 2, 6, "中心红钥匙及auto四黄回归")
    assert game.state["rk"] == 1 and game.state["yk"] == before_center_yk + 4, (
        "显式拾取中心红钥匙后，实机auto必须在同一动作收取周围4黄钥匙; "
        f"state={game.snapshot()} events={game.floors['MT34'].events} "
        f"blocks={[(p, game.block_at('MT34', p)) for p in [(1,5),(3,5),(1,7),(3,7)]]}"
    )

    # 实机 auto_sweep 杀中心最后一怪也触发 autoEvent（verifier MT34 x11y8 auto
    # 杀 bat 后下一步 move 拾取 +4YK+1RK）。旧 `not auto` 约束已撤回。
    auto_last = Zone3Game(snapshot)
    for pos in center:
        block = auto_last.block_at("MT34", pos)
        assert block and block.kind == "enemy"
        auto_last.set_ground("MT34", pos)
        auto_last.after_action("MT34", pos, block, auto=(pos == center[-1]))
    auto_last._check_auto_events("MT34")
    assert auto_last.block_at("MT34", (2, 6)).eid == "redKey", (
        "auto 清理最后一怪后 autoEvent 触发4黄1红（与实机 verifier 一致）"
    )
    print("zone3 shared Game model: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
