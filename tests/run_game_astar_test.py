#!/usr/bin/env python3
"""Regression checks for the generic shared-Game A* adapter."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.solver.game_astar import GameAStar, GameAction, click_action, exact_game_key
from src.solver.game_route import (
    Block,
    Floor,
    Game,
    RouteError,
    fund_shop_with_yellow_key_sale,
)
from src.solver.game_route import read_json
from scripts.search.zone4_game_route import Zone4Game


def make_game() -> Game:
    snapshot = {
        "floorId": "MT1",
        "hero": {
            "x": 1, "y": 2, "hp": 100, "atk": 10, "def": 0, "money": 0,
            "yk": 0, "bk": 0, "rk": 0, "tools": {}, "constants": {},
            "flags": {"__visited__": {"MT1": True}},
        },
        "maps": {},
    }
    game = Game(snapshot)
    game.strict_live_model = True
    game.auto_flags = {"battle": False, "item": False, "wall": False}
    game.enemies["astarEnemy"] = {"hp": 20, "atk": 30, "def": 0, "money": 0, "special": 0}

    width, height = 7, 5
    grid = [[1 for _ in range(width)] for _ in range(height)]
    blocks = {
        (x, y): Block("terrain", "yellowWall", 1)
        for y in range(height)
        for x in range(width)
    }
    open_cells = {(1, 2), (2, 2), (3, 2), (4, 2), (5, 2), (1, 1), (2, 1), (3, 1), (4, 1), (5, 1)}
    for x, y in open_cells:
        grid[y][x] = 0
        blocks.pop((x, y), None)
    # Direct route costs 30 HP.  The upper route spends a found key and reaches
    # the same goal with zero damage.
    blocks[(3, 2)] = Block("enemy", "astarEnemy", 0)
    blocks[(2, 1)] = Block("item", "yellowKey", 0)
    blocks[(3, 1)] = Block("door", "yellowDoor", 0)
    blocks[(5, 2)] = Block("item", "redGem", 0)
    game.floors = {"MT1": Floor("MT1", 1, grid, blocks, {}, {}, set(), set())}
    return game


def successors(game: Game):
    # These are candidate real map clicks. Illegal clicks are rejected by Game,
    # not approximated by the search engine.
    if game.block_at("MT1", (2, 1)) is not None:
        yield click_action("MT1", 2, 1, "A* safe-route key")
    if game.block_at("MT1", (3, 1)) is not None:
        yield click_action("MT1", 3, 1, "A* safe-route door")
    if game.block_at("MT1", (3, 2)) is not None:
        yield click_action("MT1", 3, 2, "A* direct enemy")
    if game.block_at("MT1", (5, 2)) is not None:
        yield click_action("MT1", 5, 2, "A* goal gem")
    # Deliberate no-op duplicate exercises action/no-op suppression.
    yield GameAction("noop", lambda child: child.go_to("MT1", child.state["x"], child.state["y"]))


def main() -> int:
    start = make_game()
    untouched_key = exact_game_key(start)
    result = GameAStar(
        actions=successors,
        goal=lambda game: game.state["atk"] == 11,
        heuristic=lambda _game: 0,
        max_expansions=100,
    ).search(start)

    assert result.found, result.reason
    assert result.cost == 0, result.cost
    assert result.game is not None
    assert result.game.state["hp"] == 100
    assert result.game.state["atk"] == 11
    assert result.game.state["yk"] == 0
    assert any(step["eid"] == "yellowDoor" for step in result.steps)
    assert all(step.get("eid") != "astarEnemy" for step in result.steps)
    assert exact_game_key(start) == untouched_key, "search must not mutate its caller's Game"
    assert all(action.metadata.get("kind") == "click" for action in result.actions)

    tied = GameAStar(
        actions=successors,
        goal=lambda game: game.state["atk"] == 11,
        heuristic=lambda _game: 0,
        # Deliberately prefer high damage in the secondary ordering.  Primary
        # A* cost must still return the zero-damage route.
        tie_breaker=lambda game: -float(100 - game.state["hp"]),
        max_expansions=100,
    ).search(start)
    assert tied.found and tied.cost == 0 and tied.game is not None
    assert tied.game.state["hp"] == 100

    funding = make_game()
    funding.enemies["astarEnemy"]["money"] = 100
    funding.set_ground("MT1", (2, 1))
    funding.set_ground("MT1", (3, 1))
    funding.no_auto_farm.add(("MT1", 3, 2))
    try:
        fund_shop_with_yellow_key_sale(funding, 100, preserve_yk=0)
    except RouteError:
        pass
    else:
        raise AssertionError("generic funding must not consume no_auto_farm enemies")
    assert funding.state["gold"] == 0
    funding.no_auto_farm.clear()
    fund_shop_with_yellow_key_sale(funding, 100, preserve_yk=0)
    assert funding.state["gold"] == 100 and funding.state["hp"] == 70

    pruned = GameAStar(
        actions=successors,
        goal=lambda game: game.state["atk"] == 11,
        upper_bound=0.5,
        max_expansions=100,
    ).search(start)
    # The safe route has zero HP cost, so it remains below the positive bound.
    assert pruned.found and pruned.cost == 0

    checkpoint = ROOT / "best" / "checkpoints" / "zone3_2atk1def_preserve_pickaxe_end_save.json"
    live_start = Zone4Game(read_json(checkpoint))
    live_start.strict_live_model = True
    live_start.auto_flags = {"battle": True, "item": "nopotion", "wall": True}
    live_result = GameAStar(
        actions=lambda _game: [click_action("MT41", 6, 7, "41F first keyed door")],
        goal=lambda game: game.state["yd"] == 1,
        max_expansions=4,
    ).search(live_start)
    assert live_result.found, live_result.reason
    assert live_result.cost == 22
    assert live_result.game is not None
    assert live_result.game.state["hp"] == 23
    assert live_result.game.state["yk"] == 6
    assert [step["eid"] for step in live_result.steps] == ["checkBlock", "yellowDoor"]
    assert live_start.state["hp"] == 45 and live_start.state["yk"] == 7

    print(
        "game A* shared-model test passed: "
        f"mini_cost={result.cost:g}, live_cost={live_result.cost:g}, "
        f"live_steps={len(live_result.steps)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
