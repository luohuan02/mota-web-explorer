#!/usr/bin/env python3
"""Optimize a real Zone-4 macro stage with the canonical Game A* engine.

The first target is the pre-earthquake 4000G farm.  The historical route uses
a damage-sorted greedy scan; this search considers alternate legal monster
orders while preserving the same conservative contract: one clicked monster
per edge, no door spend, no potion consumption, and no hidden multi-kill.

This is an experimental producer.  It writes only to outputs/ and never updates
best/; a candidate must still finish the complete TE replay and web verification.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.search.zone4_game_route import (  # noqa: E402
    DEFAULT_CHECKPOINT,
    Zone4Game,
    initial_climb_2atk1def,
)
from src.solver.game_astar import GameAction, GameAStar, exact_game_key  # noqa: E402
from src.solver.game_route import (  # noqa: E402
    Game,
    RouteError,
    cleanup_reachable_items,
    eat_minimal_potions_until,
    farm_gold_for_earthquake,
    collect_guide_pre_earthquake,
    read_json,
    state_line,
)


TARGET_GOLD = 4000


def effective_gold(game: Game, preserve_yk: int = 8) -> int:
    return int(game.state["gold"] + max(0, game.state["yk"] - preserve_yk) * 100)


def hp_potential(game: Game) -> int:
    total = int(game.state["hp"])
    for floor in game.floors.values():
        for block in floor.blocks.values():
            if block.kind != "item":
                continue
            if block.eid == "redPotion":
                total += 50 * floor.ratio
            elif block.eid == "bluePotion":
                total += 200 * floor.ratio
    return total


def enemy_positions(game: Game) -> set[tuple[str, int, int, str]]:
    return {
        (fid, x, y, block.eid)
        for fid, floor in game.floors.items()
        for (x, y), block in floor.blocks.items()
        if block.kind == "enemy"
    }


def farm_action(fid: str, x: int, y: int, eid: str) -> GameAction:
    def apply(game: Game) -> None:
        block = game.block_at(fid, (x, y))
        if not block or block.kind != "enemy" or block.eid != eid:
            game.fail(f"A* stale enemy target {fid} x{x}y{y} {eid}")
        if game.state["floor"] != fid:
            game.fly(fid)
        before = game.snapshot()
        before_enemies = enemy_positions(game)
        game.go_to(fid, x, y, f"GameAStar 凑4000G {eid}")
        removed = before_enemies - enemy_positions(game)
        if removed != {(fid, x, y, eid)}:
            game.fail(f"A* edge must remove exactly its target, removed={sorted(removed)}")
        if (game.state["yd"], game.state["bd"], game.state["rd"]) != (
            before["yd"], before["bd"], before["rd"]
        ):
            game.fail("A* pre-earthquake farm edge spent a key")
        if game.state["hp"] > before["hp"]:
            game.fail("A* pre-earthquake farm edge consumed a potion")
        if game.state["gold"] <= before["gold"]:
            game.fail("A* pre-earthquake farm edge gained no gold")
        if f"{x},{y}" in game.floors[fid].after_battle:
            cleanup_reachable_items(
                game, {"yellowKey", "blueKey"}, min_floor=1, max_steps=24
            )
        if (game.state["yd"], game.state["bd"], game.state["rd"]) != (
            before["yd"], before["bd"], before["rd"]
        ):
            game.fail("A* event-key cleanup spent a key")

    return GameAction(
        name=f"farm {fid} x{x}y{y} {eid}",
        apply=apply,
        metadata={"kind": "farm_enemy", "floor": fid, "x": x, "y": y, "eid": eid},
    )


def sell_yellow_key_action() -> GameAction:
    def apply(game: Game) -> None:
        if game.state["yk"] <= 0:
            game.fail("A* has no yellow key to sell")
        if game.state["floor"] != "MT28":
            game.fly("MT28")
        game.move_adjacent("MT28", 8, 4, "GameAStar 28F yellow-key seller")
        before = game.snapshot()
        game.state["yk"] -= 1
        game.state["gold"] += 100
        game.record("商人", (8, 4), "sellYellowKey", before, "GameAStar sell 1 yellow key for 100G")

    return GameAction(
        name="sell MT28 one yellowKey",
        apply=apply,
        metadata={"kind": "sell_yellow_key", "floor": "MT28", "gold": 100},
    )


def baseline_seed_positions() -> set[tuple[str, int, int, str]]:
    route_path = ROOT / "best" / "zone4_2atk1def_te_hp17659_walk.json"
    route = json.loads(route_path.read_text(encoding="utf-8"))
    start = 0
    count = 0
    for stage in route["stage_summaries"]:
        if stage["name"] == "farm_earthquake":
            count = int(stage["delta_steps"])
            break
        start += int(stage["delta_steps"])
    farm_steps = route["steps"][start:start + count]
    return {
        (step["floor"], int(step["pos"][0]), int(step["pos"][1]), str(step.get("eid")))
        for step in farm_steps
        if step.get("action") in {"击杀", "事件战斗"}
        and step.get("eid")
    }


def candidate_pool(game: Game, limit: int) -> list[tuple[str, int, int, str]]:
    seed = baseline_seed_positions()
    ranked: list[tuple[float, int, int, str, int, int, str]] = []
    for fid in sorted(game.visited):
        floor = game.floors.get(fid)
        if floor is None:
            continue
        for (x, y), block in floor.blocks.items():
            if block.kind != "enemy" or (fid == "MT33" and (x, y) == (7, 10)):
                continue
            if f"{x},{y}" in floor.after_battle:
                continue
            if (fid, x, y) in game.retreat_wizards or (fid, x, y) in game.no_auto_farm:
                continue
            damage = game.enemy_damage(block.eid)
            money = int(game.enemies[block.eid].get("money", 0))
            if damage == float("inf") or money <= 0:
                continue
            ranked.append((float(damage) / money, int(damage), -money, fid, x, y, block.eid))
    ranked.sort()
    selected = set(seed)
    target_size = max(limit, len(seed))
    for _ratio, _damage, _neg_money, fid, x, y, eid in ranked:
        if len(selected) >= target_size:
            break
        selected.add((fid, x, y, eid))
    return sorted(selected)


def action_factory(pool: list[tuple[str, int, int, str]]):
    def generate(game: Game) -> Iterable[GameAction]:
        for fid, x, y, eid in pool:
            block = game.block_at(fid, (x, y))
            if block and block.kind == "enemy" and block.eid == eid:
                yield farm_action(fid, x, y, eid)
    return generate


def floor_batch_action(
    fid: str,
    targets: list[tuple[str, int, int, str]],
) -> GameAction:
    def apply(game: Game) -> None:
        committed = 0
        while effective_gold(game) < TARGET_GOLD:
            best: tuple[int, int, Game] | None = None
            for tfid, x, y, eid in targets:
                block = game.block_at(tfid, (x, y))
                if not block or block.kind != "enemy" or block.eid != eid:
                    continue
                probe = game.clone()
                before = probe.snapshot()
                try:
                    farm_action(tfid, x, y, eid).apply(probe)
                except RouteError:
                    continue
                hp_loss = before["hp"] - probe.state["hp"]
                gold_gain = effective_gold(probe) - effective_gold(game)
                if gold_gain <= 0:
                    continue
                rank = (hp_loss, -gold_gain)
                if best is None or rank < best[:2]:
                    best = (hp_loss, -gold_gain, probe)
            if best is None:
                break
            game.__dict__.update(best[2].__dict__)
            committed += 1
        if committed == 0:
            game.fail(f"A* floor batch {fid} made no progress")

    return GameAction(
        name=f"farm floor batch {fid}",
        apply=apply,
        metadata={"kind": "farm_floor_batch", "floor": fid},
    )


def floor_action_factory(
    pool: list[tuple[str, int, int, str]],
    branch_limit: int,
    baseline_start: dict[str, Any],
):
    grouped: dict[str, list[tuple[str, int, int, str]]] = {}
    for target in pool:
        grouped.setdefault(target[0], []).append(target)

    def generate(game: Game) -> Iterable[GameAction]:
        if all(game.state[key] == value for key, value in baseline_start.items()):
            yield GameAction(
                name="verified greedy farm fallback",
                apply=farm_gold_for_earthquake,
                metadata={"kind": "verified_greedy_fallback"},
            )
        if game.state["hp"] < 1500:
            yield GameAction(
                name="support potion to 1500HP",
                apply=lambda child: eat_minimal_potions_until(
                    child, 1500, "GameAStar pre-earthquake survival", min_floor=1
                ),
                metadata={"kind": "support_potion", "target_hp": 1500},
            )
        ranked_floors: list[tuple[float, int, str, list[tuple[str, int, int, str]]]] = []
        for fid, targets in grouped.items():
            live: list[tuple[str, int, int, str]] = []
            total_money = 0
            best_ratio = math.inf
            for tfid, x, y, eid in targets:
                block = game.block_at(tfid, (x, y))
                if not block or block.kind != "enemy" or block.eid != eid:
                    continue
                money = int(game.enemies[eid].get("money", 0))
                damage = game.enemy_damage(eid)
                if money <= 0 or damage == float("inf"):
                    continue
                live.append((tfid, x, y, eid))
                total_money += money
                best_ratio = min(best_ratio, float(damage) / money)
            if live:
                ranked_floors.append((best_ratio, -total_money, fid, live))
        ranked_floors.sort()
        for _ratio, _neg_money, fid, targets in ranked_floors[:branch_limit]:
            yield floor_batch_action(fid, targets)

    return generate


def edge_cost(before: Game, after: Game, _action: GameAction) -> float:
    # HP plus all remaining potion value is conserved when a potion is merely
    # transferred into current HP. Combat/field damage reduces this potential.
    # This keeps every edge non-negative while matching the final-HP objective.
    potential_loss = max(0, hp_potential(before) - hp_potential(after))
    return float(potential_loss * 1_000_000 + 1)


def heuristic_factory(pool: list[tuple[str, int, int, str]]):
    def estimate(game: Game) -> float:
        deficit = max(0, TARGET_GOLD - game.state["gold"])
        if deficit == 0:
            return 0.0
        remaining = []
        for fid, x, y, eid in pool:
            block = game.block_at(fid, (x, y))
            if not block or block.kind != "enemy" or block.eid != eid:
                continue
            money = int(game.enemies[eid].get("money", 0))
            damage = game.enemy_damage(eid)
            if money > 0 and damage != float("inf"):
                remaining.append((int(damage) / money, int(damage), money))
        # Key sales are a zero-HP conversion but the goal preserves the baseline
        # YK stock, so only keys above that floor may contribute to the estimate.
        free_gold = max(0, game.state["yk"] - 8) * 100
        left = max(0, deficit - free_gold)
        hp_lower = 0.0
        actions_lower = math.ceil(deficit / max([100, *[money for _, _, money in remaining]]))
        for _ratio, damage, money in sorted(remaining):
            if left <= 0:
                break
            take = min(left, money)
            hp_lower += damage * (take / money)
            left -= take
        # This estimate is used only for queue ordering. Actual edge costs and the
        # baseline upper bound remain authoritative.
        return hp_lower * 1_000_000 + float(actions_lower)

    return estimate


def build_start(checkpoint: Path) -> Zone4Game:
    game = Zone4Game(read_json(checkpoint))
    game.strict_live_model = True
    game.auto_flags = {"battle": True, "item": "nopotion", "wall": True}
    initial_climb_2atk1def(game)
    collect_guide_pre_earthquake(game)
    return game


def bootstrap_event_keys(game: Game) -> list[GameAction]:
    """Resolve the mandatory MT32 paired-guard key event before gold ordering.

    Treating this deterministic event as an A* permutation multiplies every
    gold state by equivalent pre-key variants and makes each probe rerun the
    full resource cleanup. The two clicks are shared-Game actions and remain in
    the emitted candidate prefix.
    """
    prefix: list[GameAction] = []
    for x in (1, 3):
        block = game.block_at("MT32", (x, 10))
        if not block or block.kind != "enemy":
            continue
        action = farm_action("MT32", x, 10, block.eid)
        action.apply(game)
        prefix.append(action)
    if game.state["bk"] < 1:
        game.fail("MT32 paired-guard bootstrap did not produce the required blue key")
    return prefix


def bootstrap_key_sales(game: Game, preserve_yk: int) -> list[GameAction]:
    """Canonicalize zero-HP key sales that commute with no-door farm edges."""
    prefix: list[GameAction] = []
    while game.state["yk"] > preserve_yk:
        action = sell_yellow_key_action()
        action.apply(game)
        prefix.append(action)
    return prefix


def compact(game: Game) -> dict[str, Any]:
    snap = game.snapshot()
    return {key: snap[key] for key in (
        "floor", "x", "y", "hp", "atk", "def", "yk", "bk", "rk", "gold",
        "dmg", "yd", "bd", "rd",
    )}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--max-expansions", type=int, default=1200)
    parser.add_argument("--candidate-limit", type=int, default=28)
    parser.add_argument("--mode", choices=("floor-batch", "enemy"), default="floor-batch")
    parser.add_argument("--weight", type=float, default=1.0)
    parser.add_argument("--branch-limit", type=int, default=5)
    parser.add_argument(
        "--out-json",
        type=Path,
        default=ROOT / "outputs" / "results" / "zone4_game_astar_farm4000.json",
    )
    args = parser.parse_args()

    route_start = build_start(args.checkpoint)
    start = route_start.clone()
    bootstrap_actions = bootstrap_event_keys(start)
    baseline_route = json.loads(
        (ROOT / "best" / "zone4_2atk1def_te_hp17659_walk.json").read_text(encoding="utf-8")
    )
    baseline_stage = next(
        stage for stage in baseline_route["stage_summaries"] if stage["name"] == "farm_earthquake"
    )
    baseline_state = baseline_stage["after"]
    baseline = route_start.clone()
    farm_gold_for_earthquake(baseline)
    baseline_hp_loss = route_start.state["hp"] - int(baseline_state["hp"])
    baseline_potential_loss = hp_potential(route_start) - hp_potential(baseline)
    pool = candidate_pool(start, args.candidate_limit)
    print(f"route-start: {state_line(route_start.state)} {route_start.state['floor']} x{route_start.state['x']}y{route_start.state['y']}")
    print(f"search-start:{state_line(start.state)} {start.state['floor']} x{start.state['x']}y{start.state['y']}")
    print(f"baseline: {state_line(baseline_state)} {baseline_state['floor']} x{baseline_state['x']}y{baseline_state['y']}")
    print(
        f"candidate_pool={len(pool)} baseline_hp_loss={baseline_hp_loss} "
        f"baseline_potential_loss={baseline_potential_loss}"
    )

    result = GameAStar(
        actions=(
            floor_action_factory(
                pool,
                args.branch_limit,
                {
                    key: start.state[key]
                    for key in ("floor", "x", "y", "hp", "atk", "def", "yk", "bk", "rk", "gold", "dmg")
                },
            )
            if args.mode == "floor-batch"
            else action_factory(pool)
        ),
        goal=lambda game: (
            game.state["gold"]
            + max(0, game.state["yk"] - int(baseline_state["yk"])) * 100
            >= TARGET_GOLD
            and game.state["bk"] >= int(baseline_state["bk"])
        ),
        heuristic=heuristic_factory(pool),
        edge_cost=edge_cost,
        state_key=exact_game_key,
        weight=args.weight,
        max_expansions=args.max_expansions,
        upper_bound=float(baseline_potential_loss * 1_000_000 + 100_000),
    ).search(start)

    if result.game is not None:
        while (
            result.game.state["gold"] < TARGET_GOLD
            and result.game.state["yk"] > int(baseline_state["yk"])
        ):
            action = sell_yellow_key_action()
            action.apply(result.game)
            result.actions.append(action)

    payload: dict[str, Any] = {
        "ok": result.found,
        "checkpoint": str(args.checkpoint),
        "target_gold": TARGET_GOLD,
        "max_expansions": args.max_expansions,
        "candidate_limit": args.candidate_limit,
        "mode": args.mode,
        "weight": args.weight,
        "branch_limit": args.branch_limit,
        "candidate_pool": [
            {"floor": fid, "x": x, "y": y, "eid": eid} for fid, x, y, eid in pool
        ],
        "expansions": result.expansions,
        "generated": result.generated,
        "reason": result.reason,
        "route_start": compact(route_start),
        "start": compact(start),
        "baseline": {key: baseline_state[key] for key in compact(start)},
        "baseline_potential": hp_potential(baseline),
        "candidate": compact(result.game) if result.game else None,
        "candidate_cost": result.cost if result.found else None,
        "candidate_potential": hp_potential(result.game) if result.game else None,
        "hp_delta_vs_baseline": (
            result.game.state["hp"] - int(baseline_state["hp"]) if result.game else None
        ),
        "actions": [dict(action.metadata) for action in [*bootstrap_actions, *result.actions]],
        "action_names": [action.name for action in [*bootstrap_actions, *result.actions]],
    }
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"candidate: {state_line(result.game.state)} {result.game.state['floor']} "
        f"x{result.game.state['x']}y{result.game.state['y']}"
        if result.game
        else f"candidate: not found ({result.reason})"
    )
    print(f"expansions={result.expansions} generated={result.generated} out={args.out_json}")
    return 0 if result.found else 2


if __name__ == "__main__":
    raise SystemExit(main())
