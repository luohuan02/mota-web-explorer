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

from src.solver.game_route import (
    Block, Floor, Game, RouteError, _visited_floor_ids, kill_fixed_zero_damage_targets,
    safe_try, sync_mt47_retreat_wizards,
)


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

    game.floors["MT48"] = Floor("MT48", ratio=5, grid=grid, blocks=blocks,
                                 events={}, change_floor={}, after_battle=set(),
                                 after_battle_auto=set())
    return game


def assert_state(game: Game, **expected: int | str) -> None:
    snap = game.snapshot()
    for key, value in expected.items():
        assert snap[key] == value, f"{key}: expected {value}, got {snap[key]}"


def main() -> int:
    game = make_mt48_game()
    assert Game._auto_item_allowed("shield5", "nopotion")
    assert Game._auto_item_allowed("bomb", "nopotion")
    assert not Game._auto_item_allowed("redPotion", "nopotion")

    auto_probe = game.clone()
    auto_probe.set_auto(item=True)
    assert auto_probe.auto_flags["item"] is True
    assert auto_probe.flags["__auto__"]["item"] is True
    assert auto_probe.steps[-1]["action"] == "设置自动"
    assert auto_probe.steps[-1]["auto"] == {
        "battle": True, "item": True, "wall": True,
    }
    assert game.floors["MT32"].after_battle_auto == set(), (
        "conditional MT32 afterBattle openDoor must not restart auto"
    )
    assert "2,2" not in game.floors["MT41"].after_battle_auto, (
        "MT41 setValue resources come from approach movement auto, not afterBattle"
    )

    game.go_to("MT48", 4, 6, "first door click")
    assert_state(game, **{"floor": "MT48", "x": 4, "y": 5, "hp": 1099, "atk": 269, "def": 446, "yk": 12, "bk": 4, "rk": 1, "gold": 3286})
    assert game.block_at("MT48", (4, 6)) is None
    assert game.block_at("MT48", (4, 7)) is not None
    assert game.block_at("MT48", (3, 8)) is not None

    event_probe = make_mt48_game()
    event_probe.floors["MT48"].after_battle.add("4,7")
    event_probe.go_to("MT48", 4, 6, "event guard door")
    event_probe.auto_sweep("MT48")
    assert event_probe.block_at("MT48", (4, 7)) is not None, (
        "zero-damage enemies with afterBattle must require an explicit click"
    )

    paired = make_mt48_game()
    paired.state.update({"floor": "MT32", "x": 2, "y": 10})
    size = 13
    grid = [[1 for _ in range(size)] for _ in range(size)]
    wall = Block("terrain", "yellowWall", 1)
    blocks = {(x, y): wall for y in range(size) for x in range(size)}
    for pos in [(1, 10), (2, 10), (3, 10), (2, 9), (2, 8)]:
        blocks.pop(pos, None)
        grid[pos[1]][pos[0]] = 0
    blocks[(1, 10)] = Block("enemy", "blueGuard", 0)
    blocks[(3, 10)] = Block("enemy", "blueGuard", 0)
    blocks[(2, 9)] = Block("door", "specialDoor", 0)
    blocks[(2, 8)] = Block("item", "yellowKey", 0)
    paired.floors["MT32"] = Floor(
        "MT32", ratio=5, grid=grid, blocks=blocks, events={}, change_floor={},
        after_battle={"1,10", "3,10"}, after_battle_auto=set(),
    )
    paired.go_to("MT32", 1, 10, "first paired guard")
    assert paired.block_at("MT32", (2, 9)) is not None
    assert paired.block_at("MT32", (3, 10)) is not None
    paired.go_to("MT32", 3, 10, "second paired guard")
    assert paired.block_at("MT32", (2, 9)) is None
    assert paired.block_at("MT32", (2, 8)) is not None
    assert paired.state["yk"] == 13

    item_boundary = make_mt48_game()
    item_boundary.floors["MT48"].blocks[(11, 9)] = Block("item", "redPotion", 0)
    item_boundary.floors["MT48"].blocks[(11, 8)] = Block("item", "blueGem", 0)
    item_boundary.go_to("MT48", 11, 7, "target beyond pickup")
    assert item_boundary.block_at("MT48", (11, 9)) is None
    assert item_boundary.block_at("MT48", (11, 8)) is None
    assert item_boundary.state["def"] == 451
    pickup_steps = [s for s in item_boundary.steps if s.get("eid") == "redPotion"]
    assert len(pickup_steps) == 1 and "auto_sweep:" in pickup_steps[0]["note"]

    earthquake = make_mt48_game()
    earthquake.state["earthquake"] = 1
    earthquake.floors["MT48"].blocks[(11, 9)] = Block("terrain", "yellowWall", 1)
    earthquake.floors["MT48"].blocks[(11, 8)] = Block("item", "yellowKey", 0)
    earthquake.floors["MT48"].blocks[(11, 7)] = Block("item", "blueGem", 0)
    earthquake.floors["MT48"].blocks[(11, 6)] = Block("item", "redPotion", 0)
    earthquake.use_earthquake("earthquake opens the auto route")
    assert earthquake.state["earthquake"] == 0
    assert earthquake.state["yk"] == 13
    assert earthquake.state["def"] == 446
    assert earthquake.block_at("MT48", (11, 9)) is None
    assert earthquake.block_at("MT48", (11, 8)) is not None
    assert earthquake.block_at("MT48", (11, 7)) is not None
    assert earthquake.block_at("MT48", (11, 6)) is not None
    assert len(earthquake.steps) == 1
    assert earthquake.steps[0]["eid"] == "earthquake"
    assert "auto_sweep:" not in earthquake.steps[0]["note"]

    fake_wall = make_mt48_game()
    fake_wall.auto_flags["wall"] = False
    fake_wall.floors["MT48"].blocks[(11, 8)] = Block("terrain", "fakeWall2", 0)
    fake_wall.go_to("MT48", 11, 8, "single click breaks distant fake wall")
    assert len(fake_wall.steps) == 1
    assert fake_wall.steps[0]["action"] == "破墙"
    assert fake_wall.steps[0]["before"]["x"] == 11
    assert fake_wall.steps[0]["before"]["y"] == 10
    assert fake_wall.steps[0]["after"]["x"] == 11
    assert fake_wall.steps[0]["after"]["y"] == 9
    assert fake_wall.block_at("MT48", (11, 8)) is None

    snow_auto = make_mt48_game()
    snow_auto.state["snow"] = 1
    snow_auto.floors["MT48"].blocks[(11, 9)] = Block("wall", "lava", 5)
    snow_auto.floors["MT48"].blocks[(11, 8)] = Block("item", "sword5", 43)
    snow_auto.auto_sweep("MT48")
    assert snow_auto.block_at("MT48", (11, 9)) is None
    assert snow_auto.block_at("MT48", (11, 8)) is None
    assert snow_auto.state["atk"] == 369

    optional_gold = make_mt48_game()
    optional_gold.floors["MT48"].blocks[(11, 8)] = Block("enemy", "whiteKing", 0)
    optional_gold.floors["MT48"].blocks[(11, 9)] = Block("door", "blueDoor", 82)
    optional_gold.state["bk"] = 0
    before_optional = optional_gold.snapshot()
    kill_fixed_zero_damage_targets(
        optional_gold,
        [("MT48", 11, 8)],
        "optional unreachable gold",
        required=False,
    )
    assert optional_gold.snapshot() == before_optional
    assert optional_gold.block_at("MT48", (11, 8)) is not None

    game.go_to("MT48", 4, 7, "brownWizard click")
    assert_state(game, **{"floor": "MT48", "x": 4, "y": 7, "hp": 1099, "atk": 274, "def": 446, "yk": 12, "bk": 4, "rk": 1, "gold": 3446})
    assert game.block_at("MT48", (4, 7)) is None
    assert game.block_at("MT48", (3, 8)) is None

    game.go_to("MT48", 4, 9, "door click")

    assert_state(game, **{"floor": "MT48", "x": 4, "y": 8, "hp": 1099, "atk": 274, "def": 446, "yk": 11, "bk": 4, "rk": 1, "gold": 3446})
    assert game.block_at("MT48", (4, 9)) is None
    assert game.block_at("MT48", (4, 10)) is not None
    assert game.block_at("MT48", (3, 11)) is not None

    game.go_to("MT48", 4, 10, "post-door action")
    assert_state(game, **{"floor": "MT48", "x": 4, "y": 9, "hp": 1099, "atk": 274, "def": 451, "yk": 11, "bk": 4, "rk": 1, "gold": 4486})
    assert game.block_at("MT48", (3, 11)) is None
    assert game.block_at("MT48", (4, 10)) is None
    for pos in [(7, 3), (9, 3), (7, 5), (9, 5)]:
        assert game.block_at("MT48", pos) is None

    routed_probe = make_mt48_game()
    routed_probe.go_to("MT48", 4, 6, "first door click")
    routed_probe.go_to("MT48", 4, 7, "brownWizard click")
    try:
        routed_probe.go_to("MT48", 3, 11, "gem behind darkKnight")
    except RouteError:
        pass
    else:
        raise AssertionError("一次目标点击不得把路径上的存活敌人隐式变成逐格战斗")

    # The following explicit battle action, not the door click, settled auto.
    assert_state(game, **{"floor": "MT48", "x": 4, "y": 9, "hp": 1099, "atk": 274, "def": 451, "yk": 11, "bk": 4, "rk": 1, "gold": 4486})
    for pos in [(3, 11), (4, 10), (7, 3), (9, 3), (7, 5), (9, 5)]:
        assert game.block_at("MT48", pos) is None, f"expected MT48 {pos} to be cleared"

    # checkBlock is itself a live movement action. Its auto side effects must
    # settle into the same recorded atom, not wait for a later explicit click.
    check_game = make_mt48_game()
    check_game.state.update({"floor": "MT47", "x": 7, "y": 1})
    size = 13
    grid = [[1 for _ in range(size)] for _ in range(size)]
    wall = Block("terrain", "yellowWall", 1)
    blocks = {(x, y): wall for y in range(size) for x in range(size)}
    for pos in [(7, 1), (8, 1), (9, 1), (10, 1), (11, 1), (11, 2), (11, 3), (8, 3)]:
        blocks.pop(pos, None)
        grid[pos[1]][pos[0]] = 0
    blocks[(8, 2)] = Block("enemy", "redWizard", 0)
    blocks[(11, 1)] = Block("item", "yellowKey", 0)
    blocks[(11, 2)] = Block("item", "blueGem", 0)
    blocks[(11, 3)] = Block("item", "yellowKey", 0)
    check_game.floors["MT47"] = Floor("MT47", ratio=5, grid=grid, blocks=blocks,
                                       events={}, change_floor={}, after_battle=set(),
                                       after_battle_auto=set())
    damage = check_game.check_damage_at("MT47", (8, 1))
    assert damage > 0
    check_game.go_to("MT47", 11, 1, "wizard field auto settle")
    assert_state(check_game, **{"hp": 1099 - damage, "def": 451, "yk": 15})
    for pos in [(11, 1), (11, 2), (11, 3)]:
        assert check_game.block_at("MT47", pos) is None
    damage_steps = [s for s in check_game.steps if s.get("eid") == "checkBlock"]
    assert len(damage_steps) == 1
    assert "auto_sweep:" in damage_steps[0]["note"]

    check_game.retreat_wizards.discard(("MT47", 8, 3))
    sync_mt47_retreat_wizards(check_game)
    assert ("MT47", 8, 3) in check_game.retreat_wizards
    check_game._move_retreat_wizard("MT47", (8, 3), (9, 3))
    assert ("MT47", 8, 3) not in check_game.retreat_wizards
    assert ("MT47", 9, 3) in check_game.retreat_wizards

    # A failed optional multi-click route must not leak its partial movement,
    # dynamic-enemy relocation, map edits, or recorded steps into the caller.
    rollback_game = check_game.clone()
    rollback_game._move_retreat_wizard("MT47", (9, 3), (8, 3))
    rollback_steps = len(rollback_game.steps)
    rollback_pos = (rollback_game.state["floor"], rollback_game.state["x"], rollback_game.state["y"])

    def fail_after_retreat_move(game: Game) -> None:
        game._move_retreat_wizard("MT47", (8, 3), (9, 3))
        game.state["x"] = 9
        game.record("到达", (9, 3), None, game.snapshot(), "failed optional probe")
        game.fail("force rollback")

    assert not safe_try(rollback_game, fail_after_retreat_move, rollback_game)
    assert (rollback_game.state["floor"], rollback_game.state["x"], rollback_game.state["y"]) == rollback_pos
    assert len(rollback_game.steps) == rollback_steps
    assert ("MT47", 8, 3) in rollback_game.retreat_wizards
    assert ("MT47", 9, 3) not in rollback_game.retreat_wizards
    assert rollback_game.block_at("MT47", (8, 3)) is not None
    assert rollback_game.block_at("MT47", (9, 3)) is None

    # Auto must skip a retreating wizard while it has an escape tile, but may
    # kill it once a closed door traps it at the corridor endpoint.
    trapped_game = make_mt48_game()
    trapped_game.state.update({"floor": "MT47", "x": 8, "y": 2, "atk": 999, "def": 999})
    grid = [[1 for _ in range(size)] for _ in range(size)]
    blocks = {(x, y): wall for y in range(size) for x in range(size)}
    for pos in [(8, 2), (8, 3), (8, 4)]:
        blocks.pop(pos, None)
        grid[pos[1]][pos[0]] = 0
    blocks[(8, 3)] = Block("enemy", "redWizard", 0)
    blocks[(8, 4)] = Block("door", "yellowDoor", 0)
    trapped_game.floors["MT47"] = Floor(
        "MT47", ratio=5, grid=grid, blocks=blocks, events={}, change_floor={},
        after_battle=set(), after_battle_auto=set(),
    )
    trapped_game.enemies["redWizard"] = {"hp": 1, "atk": 0, "def": 0, "money": 90, "special": []}
    trapped_game.retreat_wizards.add(("MT47", 8, 3))
    fleeing_game = trapped_game.clone()
    fleeing_game.set_ground("MT47", (8, 4))
    fleeing_game.auto_sweep("MT47")
    assert fleeing_game.block_at("MT47", (8, 3)) is not None
    trapped_game.auto_sweep("MT47")
    assert trapped_game.block_at("MT47", (8, 3)) is None

    # Auto BFS must obey the same directional flower rule as an explicit
    # route. MT33 x8y10 only permits travel from the inner x7y10 pocket to
    # x8y10; it cannot be used to enter that pocket from x9y10.
    flower_game = make_mt48_game()
    flower_game.state.update({"floor": "MT33", "x": 9, "y": 10})
    grid = [[1 for _ in range(size)] for _ in range(size)]
    blocks = {(x, y): wall for y in range(size) for x in range(size)}
    for pos in [(9, 10), (8, 10), (7, 10)]:
        blocks.pop(pos, None)
        grid[pos[1]][pos[0]] = 0
    blocks[(8, 10)] = Block("terrain", "flower", 0)
    blocks[(7, 10)] = Block("enemy", "slimeMan", 0)
    flower_game.floors["MT33"] = Floor(
        "MT33", ratio=4, grid=grid, blocks=blocks, events={}, change_floor={},
        after_battle=set(), after_battle_auto=set(),
    )
    flower_game.enemies["slimeMan"] = {"hp": 1, "atk": 0, "def": 0, "money": 1, "special": []}
    flower_game.auto_sweep("MT33")
    assert flower_game.block_at("MT33", (7, 10)) is not None

    # Reaching a stair changes floor immediately in live. It must not run one
    # last broad auto sweep on the source floor before the transition step.
    stair_game = make_mt48_game()
    stair_game.state.update({"floor": "MT48", "x": 1, "y": 1})
    grid = [[1 for _ in range(size)] for _ in range(size)]
    blocks = {(x, y): wall for y in range(size) for x in range(size)}
    for pos in [(1, 1), (1, 2), (2, 2)]:
        blocks.pop(pos, None)
        grid[pos[1]][pos[0]] = 0
    blocks[(1, 2)] = Block("terrain", "downFloor", 0)
    blocks[(2, 2)] = Block("enemy", "greenSlime", 0)
    stair_game.floors["MT48"] = Floor(
        "MT48", ratio=5, grid=grid, blocks=blocks, events={}, change_floor={},
        after_battle=set(), after_battle_auto=set(),
    )
    stair_game.enemies["greenSlime"] = {"hp": 1, "atk": 0, "def": 0, "money": 40, "special": []}
    stair_gold = stair_game.state["gold"]
    stair_game.go_to("MT48", 1, 2, "downFloor click")
    assert stair_game.state["gold"] == stair_gold
    assert stair_game.block_at("MT48", (2, 2)) is not None

    # Floor tools do not grant ordinary fly access to a floor. Only a real
    # stair transition updates the engine's __visited__ map.
    tool_game = make_mt48_game()
    tool_game.state.update({"floor": "MT47", "x": 7, "y": 1, "upFly": 1})
    tool_game.visited.discard("MT48")
    tool_game.up_fly("tool visit must not unlock fly")
    assert tool_game.state["floor"] == "MT48"
    assert "MT48" not in tool_game.visited
    searchable_floors = _visited_floor_ids(tool_game)
    assert searchable_floors[0] == "MT48"
    special_floor_game = make_mt48_game()
    special_floor_game.visited.discard("MT49")
    special_floor_game.transition("MT49", landing=(2, 11), note="special floor entry")
    assert "MT49" not in special_floor_game.visited

    print("strict live click model test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
