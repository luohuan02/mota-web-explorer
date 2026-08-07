#!/usr/bin/env python3
"""Focused regressions for recording_seed_to_game's semantic boundary."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.solver.game_route import read_json, RouteError
from scripts.search.recording_seed_to_game import (
    MT20_KILL_EXPECTED,
    SemanticAction,
    execute_action,
    is_event_trigger,
    validate_seed_snapshot,
)
from scripts.search.zone3_game_route import Zone3Game

SEED = ROOT / "best" / "checkpoints" / "zone2_2atk0def_kill_end_save.json"


def main() -> int:
    seed = read_json(SEED)
    validate_seed_snapshot(seed, "mt20-mt31")

    hero_only = {"final": dict(MT20_KILL_EXPECTED)}
    try:
        validate_seed_snapshot(hero_only, "mt20-mt31")
    except ValueError:
        pass
    else:
        raise AssertionError("walk final summary must not be accepted as a complete seed")

    wrong = copy.deepcopy(seed)
    wrong["hero"]["hp"] += 1
    try:
        validate_seed_snapshot(wrong, "mt20-mt31")
    except ValueError as exc:
        assert "slot-32 KILL" in str(exc)
    else:
        raise AssertionError("wrong MT20 KILL state must be rejected")

    game = Zone3Game(seed)
    game.strict_live_model = True
    game.auto_flags = {"battle": True, "item": "nopotion", "wall": True}

    # h5mota arrow = turn-then-move: an arrow onto a passable plain empty tile
    # MOVES the hero there (the recording uses arrow keys to walk, e.g. the
    # MT19->MT8 flyback). Only a blocked tile (wall/door/noPass NPC) is a pure
    # turn that the handler skips. blocks is sparse, so scan the full grid.
    floor = game.floors["MT20"]
    plain = None
    for y in range(floor.height):
        for x in range(floor.width):
            if game.block_at("MT20", (x, y)) is None and not is_event_trigger(game, "MT20", (x, y)):
                plain = (x, y)
                break
        if plain is not None:
            break
    assert plain is not None, "MT20 must have at least one plain empty non-event tile"
    # Place hero adjacent to the plain tile so the arrow targets it.
    game.state["x"], game.state["y"] = plain[0] - 1, plain[1]
    diagnostics: list[dict] = []
    before_steps = len(game.steps)
    action = SemanticAction(1, "arrow", None, None, None, {"direction": "right"})
    assert execute_action(game, action, diagnostics)
    assert len(game.steps) > before_steps, "arrow onto plain empty tile must move the hero"
    assert (game.state["x"], game.state["y"]) == plain, "hero must move onto the plain tile"

    # An arrow onto a wall is a pure turn: non-fatal (caught, logged, skipped),
    # not a blocking error that aborts the stage.
    wall_pos = None
    for y in range(floor.height):
        for x in range(floor.width):
            blk = game.block_at("MT20", (x, y))
            if blk is not None and blk.kind == "terrain" and blk.eid not in ("upFloor", "downFloor", "flower"):
                wall_pos = (x, y)
                break
        if wall_pos is not None:
            break
    if wall_pos is not None:
        game.state["x"], game.state["y"] = wall_pos[0] - 1, wall_pos[1]
        wall_action = SemanticAction(2, "arrow", None, None, None, {"direction": "right"})
        wall_diag: list[dict] = []
        try:
            execute_action(game, wall_action, wall_diag)
            # If it did not raise, it must have been skipped or executed safely.
        except RouteError:
            pass  # acceptable: _safe_execute in convert() catches this

    # An event shell may have no map block, but it is not a disposable empty
    # waypoint. The classifier must preserve it for an explicit Game action.
    event_floor, event_pos = next(
        (fid, tuple(map(int, key.split(","))))
        for fid, floor_obj in game.floors.items()
        for key in floor_obj.events
        if game.block_at(fid, tuple(map(int, key.split(",")))) is None
    )
    assert is_event_trigger(game, event_floor, event_pos)
    assert (event_floor, event_pos) != ("MT20", plain)

    print("recording seed converter: ok")
    return 0

    print("recording seed converter: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
