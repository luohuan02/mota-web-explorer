#!/usr/bin/env python3
"""Bounded compressed-resource A* for the late Zone-4 attack-shop funding stage.

Every search edge targets one real item/enemy entry through ``go_to_decomposed``.
The edge therefore includes its strict Game path, doors, battles, auto sweep and
event side effects.  Equivalent entry coordinates that produce the same map
state are collapsed before search.  The objective is the first late-49 attack
shop: reach its funding threshold while preserving the incumbent's routing-key
stock, minimizing loss of ``current HP + all remaining potion value``.

This is an experimental producer.  It writes only to ``outputs/``.  A winning
funding prefix must still complete the full TE tail, regenerate the canonical
walk and pass the unified web verifier before promotion to ``best/``.
"""
from __future__ import annotations

import argparse
import json
import math
import pickle
import sys
from pathlib import Path
from typing import Any, Hashable, Iterable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.search.zone4_game_route import Zone4Game  # noqa: E402
from src.solver.game_astar import GameAction, GameAStar  # noqa: E402
from src.solver.game_route import (  # noqa: E402
    Game,
    RouteError,
    buy_shops_to_stat,
    cleanup_reachable_items,
    collect_positive_hp_resource_groups,
    eat_all_reachable_potions,
    go_to_decomposed,
    sell_yellow_keys_for_gold,
    shop_cost,
)

DEFAULT_CHECKPOINT = ROOT / "outputs/results/zone4_pre_late49_checkpoint.pkl"
DEFAULT_OUT = ROOT / "outputs/results/zone4_resource_group_astar.json"
ITEM_VALUE = {
    "redPotion": 50,
    "bluePotion": 200,
    "redGem": 500,
    "blueGem": 550,
    "yellowKey": 100,
    "blueKey": 400,
    "redKey": 800,
}


def load_game(path: Path) -> Zone4Game:
    # Checkpoints produced by running zone4_game_route.py as a script record the
    # subclass under __main__.  Bind the canonical class before unpickling.
    sys.modules["__main__"].Zone4Game = Zone4Game
    game = pickle.loads(path.read_bytes())
    if not isinstance(game, Zone4Game):
        raise TypeError(f"unexpected checkpoint type: {type(game)!r}")
    return game


def prepare_search_start(game: Zone4Game) -> None:
    cleanup_reachable_items(
        game,
        {"redGem", "blueGem", "yellowKey", "blueKey", "redKey"},
        min_floor=1,
        preserve_rk=1,
    )
    collect_positive_hp_resource_groups(
        game,
        min_floor=1,
        preserve_yk=1,
        preserve_rk=1,
        require_stat_and_nonnegative_key_value=True,
    )
    eat_all_reachable_potions(game, min_floor=1)


def hp_potential(game: Game) -> int:
    total = int(game.state["hp"])
    for floor in game.floors.values():
        for block in floor.blocks.values():
            if block.kind == "item" and block.eid in {"redPotion", "bluePotion"}:
                total += ITEM_VALUE[block.eid] * floor.ratio
    return total


def resource_signature(game: Game) -> Hashable:
    """Compressed transposition key: ignore fly/arrival coordinate and history."""
    blocks = tuple(
        (fid, x, y, block.kind, block.eid, block.tile)
        for fid, floor in sorted(game.floors.items())
        for (x, y), block in sorted(floor.blocks.items())
        if block.kind in {"item", "enemy", "door", "wall", "npc"}
    )
    state_keys = (
        "hp", "atk", "def", "yk", "bk", "rk", "gold", "times1",
        "centerFly", "upFly", "downFly", "earthquake", "bomb", "bigKey",
        "pickaxe", "superPotion", "snow", "knife", "magicImmune",
    )
    return (
        tuple((key, game.state.get(key)) for key in state_keys),
        tuple(sorted(game.blocked_items)),
        tuple(sorted(game.retreat_wizards)),
        blocks,
    )


def compact(game: Game) -> dict[str, Any]:
    return {key: game.state[key] for key in (
        "floor", "x", "y", "hp", "atk", "def", "yk", "bk", "rk",
        "gold", "dmg", "yd", "bd", "rd", "times1",
    )}


def target_action(fid: str, x: int, y: int, kind: str, eid: str) -> GameAction:
    def apply(game: Game) -> None:
        block = game.block_at(fid, (x, y))
        if not block or block.kind != kind or block.eid != eid:
            game.fail(f"stale compressed resource target {fid} x{x}y{y} {kind}:{eid}")
        before = resource_signature(game)
        if game.state["floor"] != fid:
            game.fly(fid)
        go_to_decomposed(game, fid, x, y, f"resource-group A* {kind}:{eid}")
        if resource_signature(game) == before:
            game.fail(f"compressed resource edge made no progress: {fid} x{x}y{y}")
        if game.state["hp"] <= 0 or game.state["rk"] < 1:
            game.fail("compressed resource edge violates survival/red-key reserve")

    return GameAction(
        name=f"resource {fid} x{x}y{y} {kind}:{eid}",
        apply=apply,
        metadata={"kind": "resource_group", "floor": fid, "x": x, "y": y,
                  "block_kind": kind, "eid": eid},
    )


def raw_targets(game: Game) -> list[tuple[str, int, int, str, str]]:
    rows: list[tuple[int, int, int, str, int, int, str, str]] = []
    excluded_floors = {"MT24", "MT25", "MT26", "MT35", "MT49", "MT50"}
    for fid in sorted(game.visited):
        if fid in excluded_floors or fid not in game.floors:
            continue
        floor = game.floors[fid]
        for (x, y), block in floor.blocks.items():
            if block.kind not in {"item", "enemy"}:
                continue
            if f"{x},{y}" in floor.after_battle:
                continue
            if (fid, x, y) in game.retreat_wizards or (fid, x, y) in game.no_auto_farm:
                continue
            if block.kind == "item":
                value = ITEM_VALUE.get(block.eid, 0)
                rows.append((0, -value, 0, fid, x, y, block.kind, block.eid))
            else:
                damage = game.enemy_damage(block.eid)
                money = int(game.enemies.get(block.eid, {}).get("money", 0))
                if damage == math.inf or money <= 0:
                    continue
                rows.append((1, int(damage), -money, fid, x, y, block.kind, block.eid))
    rows.sort()
    return [(fid, x, y, kind, eid) for _a, _b, _c, fid, x, y, kind, eid in rows]


def build_pool(game: Game, probe_limit: int, pool_limit: int) -> list[GameAction]:
    """Probe real one-edge outcomes and collapse duplicate resource groups."""
    base = compact(game)
    base_potential = hp_potential(game)
    unique: dict[Hashable, tuple[tuple[float, ...], GameAction]] = {}
    for fid, x, y, kind, eid in raw_targets(game)[:probe_limit]:
        action = target_action(fid, x, y, kind, eid)
        cand = game.clone()
        try:
            action.apply(cand)
        except RouteError:
            continue
        if cand.state["yk"] < 1 or cand.state["bk"] < 1 or cand.state["rk"] < 1:
            continue
        gold_gain = cand.state["gold"] - base["gold"]
        stat_gain = cand.state["atk"] + cand.state["def"] - base["atk"] - base["def"]
        key_value = (
            (cand.state["yk"] - base["yk"]) * 100
            + (cand.state["bk"] - base["bk"]) * 400
            + (cand.state["rk"] - base["rk"]) * 800
        )
        potential_loss = max(0, base_potential - hp_potential(cand))
        progress = gold_gain + max(0, key_value) + stat_gain * 120
        if progress <= 0:
            continue
        rank = (potential_loss, -stat_gain, -(gold_gain + key_value), len(cand.steps) - len(game.steps))
        sig = resource_signature(cand)
        if sig not in unique or rank < unique[sig][0]:
            unique[sig] = (rank, action)
    return [row[1] for row in sorted(unique.values(), key=lambda row: row[0])[:pool_limit]]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--max-expansions", type=int, default=80)
    parser.add_argument("--probe-limit", type=int, default=100)
    parser.add_argument("--pool-limit", type=int, default=28)
    parser.add_argument("--preserve-yk", type=int, default=15)
    parser.add_argument("--preserve-bk", type=int, default=2)
    parser.add_argument(
        "--funding-heuristic-scale", type=float, default=1000.0,
        help="queue-ordering weight per missing gold; 1000 equals 0.001 HP-cost unit",
    )
    args = parser.parse_args()

    start = load_game(args.checkpoint)
    prepare_search_start(start)
    target_cost = shop_cost(start.state["times1"])

    incumbent = start.clone()
    buy_shops_to_stat(
        incumbent, "atk", 292, "incumbent greedy attack shop",
        preserve_yk=1, allow_key_investment=True, preserve_rk=1,
    )
    incumbent_loss = hp_potential(start) - hp_potential(incumbent)
    pool = build_pool(start, args.probe_limit, args.pool_limit)

    def effective_funding(game: Game) -> int:
        return int(game.state["gold"] + max(0, game.state["yk"] - args.preserve_yk) * 100)

    result = GameAStar(
        actions=lambda game: (
            action for action in pool
            if (block := game.block_at(action.metadata["floor"], (action.metadata["x"], action.metadata["y"])))
            and block.kind == action.metadata["block_kind"]
            and block.eid == action.metadata["eid"]
        ),
        goal=lambda game: (
            effective_funding(game) >= target_cost
            and game.state["yk"] >= args.preserve_yk
            and game.state["bk"] >= args.preserve_bk
            and game.state["rk"] >= 1
        ),
        heuristic=lambda game: float(
            max(0, target_cost - effective_funding(game)) * args.funding_heuristic_scale
        ),
        edge_cost=lambda before, after, _action: float(
            max(0, hp_potential(before) - hp_potential(after)) * 1_000_000 + 1
        ),
        state_key=resource_signature,
        weight=1.0,
        max_expansions=args.max_expansions,
        upper_bound=float(max(1, incumbent_loss) * 1_000_000 + 100_000),
    ).search(start)

    candidate = result.game
    if candidate is not None:
        sell_yellow_keys_for_gold(candidate, target_cost, preserve_yk=args.preserve_yk)
        if candidate.state["gold"] < target_cost:
            candidate.fail("A* effective funding did not convert to actual gold")
        if candidate.state["floor"] != "MT46":
            candidate.fly("MT46")
        go_to_decomposed(candidate, "MT46", 6, 2, "resource-group A* attack shop")
        candidate.buy_shop("atk", 1, shop_pos=(6, 1))

    payload = {
        "ok": result.found and candidate is not None and not candidate.errors,
        "scope": "late49 first attack-shop funding; compressed strict Game resource groups",
        "bounded": True,
        "checkpoint": str(args.checkpoint),
        "start": compact(start),
        "target_shop_cost": target_cost,
        "preserve": {"yk": args.preserve_yk, "bk": args.preserve_bk, "rk": 1},
        "incumbent_after_shop": compact(incumbent),
        "incumbent_potential_loss": incumbent_loss,
        "pool": [dict(action.metadata) for action in pool],
        "max_expansions": args.max_expansions,
        "funding_heuristic_scale": args.funding_heuristic_scale,
        "expansions": result.expansions,
        "generated": result.generated,
        "reason": result.reason,
        "candidate_after_shop": compact(candidate) if candidate else None,
        "candidate_potential_loss": hp_potential(start) - hp_potential(candidate) if candidate else None,
        "actions": [dict(action.metadata) for action in result.actions],
        "action_names": [action.name for action in result.actions],
        "steps": candidate.steps if candidate else [],
        "errors": candidate.errors if candidate else [],
    }
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: payload[key] for key in (
        "ok", "start", "target_shop_cost", "preserve", "incumbent_after_shop",
        "incumbent_potential_loss", "expansions", "generated", "reason",
        "candidate_after_shop", "candidate_potential_loss", "action_names", "errors",
    )}, ensure_ascii=False, indent=2))
    print(f"out={args.out_json} pool={len(pool)}")
    return 0 if payload["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
