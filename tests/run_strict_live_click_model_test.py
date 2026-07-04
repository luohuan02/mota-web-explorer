#!/usr/bin/env python3
"""Regression checks for strict live-click semantics.

The miniature MT48 map mirrors the verified live protocol:

1. Clicking a keyed door opens it from the adjacent tile and does not run auto BFS.
2. Clicking an item behind a still-live enemy is not a legal single click.
3. Clicking the blocking enemy is the next real action; the hero first moves to
   the adjacent opened-door tile, then auto pickup / zero-damage cleanup runs.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.search_post40_guide_route import Block, Floor, Game, RouteError


def make_mt48_game() -> Game:
    snapshot = {
        "floorId": "MT48",
        "hero": {
            "x": 11,
            "y": 10,
            "hp": 1099,
            "atk": 269,
            "def": 446,
            "money": 3286,
            "yk": 13,
            "bk": 4,
            "rk": 1,
            "tools": {},
            "constants": {"coin": 1},
            "flags": {"__visited__": {"MT48": True}},
        },
        "maps": {},
    }
    game = Game(snapshot)
    game.strict_live_model = True
    game.auto_flags = {"battle": True, "item": "nopotion", "wall": True}

    size = 13
    grid = [[1 for _ in range(size)] for _ in range(size)]
    wall = Block("terrain", "yellowWall", 1)
    blocks: dict[tuple[int, int], Block] = {(x, y): wall for y in range(size) for x in range(size)}

    open_cells = {
        (11, 10),
        (11, 9),
        (11, 8),
        (11, 7),
        (11, 6),
        (11, 5),
        (11, 4),
        (11, 3),
        (11, 2),
        (11, 1),
        (10, 1),
        (9, 1),
        (8, 1),
        (7, 1),
        (6, 1),
        (5, 1),
        (4, 1),
        (4, 2),
        (4, 3),
        (4, 4),
        (4, 5),
        (4, 6),
        (4, 7),
        (4, 8),
        (3, 8),
        (4, 9),
        (4, 10),
        (4, 11),
        (3, 11),
        (5, 10),
        (6, 10),
        (7, 10),
        (7, 9),
        (7, 8),
        (7, 7),
        (7, 6),
        (7, 5),
        (8, 5),
        (9, 5),
        (7, 4),
        (7, 3),
        (8, 3),
        (9, 3),
    }
    for pos in open_cells:
        blocks.pop(pos, None)
        grid[pos[1]][pos[0]] = 0

    blocks[(4, 6)] = Block("door", "yellowDoor", 81)
    blocks[(4, 7)] = Block("enemy", "brownWizard", 0)
    blocks[(3, 8)] = Block("item", "redGem", 0)
    blocks[(4, 9)] = Block("door", "yellowDoor", 81)
    blocks[(4, 10)] = Block("enemy", "darkKnight", 0)
    blocks[(3, 11)] = Block("item", "blueGem", 0)
    for pos in [(7, 3), (9, 3), (7, 5), (9, 5)]:
        blocks[pos] = Block("enemy", "whiteKing", 0)

    game.floors["MT48"] = Floor("MT48", ratio=5, grid=grid, blocks=blocks, change_floor={})
    return game


def assert_state(game: Game, **expected: int | str) -> None:
    snap = game.snapshot()
    for key, value in expected.items():
        assert snap[key] == value, f"{key}: expected {value}, got {snap[key]}"


def main() -> int:
    game = make_mt48_game()

    game.go_to("MT48", 4, 6, "first door click")
    assert_state(game, **{"floor": "MT48", "x": 4, "y": 5, "hp": 1099, "atk": 269, "def": 446, "yk": 12, "bk": 4, "rk": 1, "gold": 3286})
    assert game.block_at("MT48", (4, 6)) is None
    assert game.block_at("MT48", (4, 7)) is not None
    assert game.block_at("MT48", (3, 8)) is not None

    game.go_to("MT48", 4, 7, "brownWizard click")
    assert_state(game, **{"floor": "MT48", "x": 4, "y": 6, "hp": 1099, "atk": 274, "def": 446, "yk": 12, "bk": 4, "rk": 1, "gold": 3446})
    assert game.block_at("MT48", (4, 7)) is None
    assert game.block_at("MT48", (3, 8)) is None

    game.go_to("MT48", 4, 9, "door click")

    assert_state(game, **{"floor": "MT48", "x": 4, "y": 8, "hp": 1099, "atk": 274, "def": 446, "yk": 11, "bk": 4, "rk": 1, "gold": 3446})
    assert game.block_at("MT48", (4, 9)) is None
    assert game.block_at("MT48", (3, 11)) is not None
    assert game.block_at("MT48", (4, 10)) is not None
    for pos in [(7, 3), (9, 3), (7, 5), (9, 5)]:
        assert game.block_at("MT48", pos) is not None

    blocked_probe = game.clone()
    try:
        blocked_probe.go_to("MT48", 3, 11, "blocked gem click")
    except RouteError:
        pass
    else:
        raise AssertionError("strict live click incorrectly routed through darkKnight to the gem")

    game.go_to("MT48", 4, 10, "blocking darkKnight click")
    assert_state(game, **{"floor": "MT48", "x": 4, "y": 9, "hp": 1099, "atk": 274, "def": 451, "yk": 11, "bk": 4, "rk": 1, "gold": 4486})
    for pos in [(3, 11), (4, 10), (7, 3), (9, 3), (7, 5), (9, 5)]:
        assert game.block_at("MT48", pos) is None, f"expected MT48 {pos} to be cleared"

    print("strict live click model test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
