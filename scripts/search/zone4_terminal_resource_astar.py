#!/usr/bin/env python3
"""Search the complete pre-boss residual map for one more 46F HP shop.

Unlike the terminal fixed-point helper, this is a real combination search.
Every edge targets a remaining item or enemy through ``go_to_decomposed`` and
therefore includes doors, blockers, auto side effects, key recovery, combat and
map mutations from the shared strict ``Game``.  The goal is effective funding
(``gold + sellable YK * 100``) for the next HP shop.  Search cost is actual HP
lost before that shop; an incumbent bound of one shop's HP gain safely prunes
routes that cannot improve final HP.
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

from scripts.audit.audit_zone4_endgame_resources import (  # noqa: E402
    optimistic_funding_ledger,
    pre_boss_clone,
)
from scripts.search.zone4_game_route import Zone4Game  # noqa: E402
from src.solver.game_astar import GameAction, GameAStar  # noqa: E402
from src.solver.game_route import (  # noqa: E402
    Game,
    go_to_decomposed,
    optional_talk_trader,
    sell_yellow_keys_for_gold,
    shop_cost,
)

DEFAULT_PICKLE = ROOT / "outputs/results/zone4_31red_atktarget261_finalhp_candidate.pkl"
DEFAULT_OUT = ROOT / "outputs/results/zone4_terminal_resource_astar.json"


def load_pre_boss(path: Path, *, raw_game: bool = False) -> Game:
    sys.modules["__main__"].Zone4Game = Zone4Game
    final = pickle.loads(path.read_bytes())
    # Continuous producers may use Zone3Game as the concrete class and invoke
    # the shared Zone-4 stages.  This optimizer needs only strict Game APIs;
    # rejecting that checkpoint would force an unsafe state splice.
    if not isinstance(final, Game):
        raise TypeError(f"unexpected checkpoint type: {type(final)!r}")
    game = final.clone() if raw_game else pre_boss_clone(final)
    if raw_game:
        game.flags.pop("stopBeforeTerminalClosure", None)
    else:
        game.blocked_items.clear()
    return game


def compact(game: Game) -> dict[str, Any]:
    return {key: game.state[key] for key in (
        "floor", "x", "y", "hp", "atk", "def", "yk", "bk", "rk",
        "gold", "dmg", "yd", "bd", "rd", "times1",
    )}


def effective_funding(game: Game) -> int:
    return int(game.state["gold"] + max(0, game.state["yk"]) * 100)


def relevant_blocks(game: Game) -> tuple[tuple[Any, ...], ...]:
    return tuple(
        (fid, x, y, block.kind, block.eid, block.tile)
        for fid in sorted(game.visited, key=lambda value: int(value[2:]))
        if fid in game.floors
        for (x, y), block in sorted(game.floors[fid].blocks.items())
        if block.kind in {"item", "enemy", "door", "wall", "npc"}
    )


def state_key(game: Game) -> Hashable:
    # Position is retained: a target click can end inside a pocket whose exit is
    # not equivalent to the normal fly landing.  Omitting it would be an unsafe
    # transposition merge.
    return (
        tuple((key, game.state.get(key)) for key in (
            "hp", "atk", "def", "yk", "bk", "rk",
            "gold", "times1", "snow", "knife", "magicImmune",
        )),
        relevant_blocks(game),
        tuple(sorted(game.blocked_items)),
        tuple(sorted(game.retreat_wizards)),
        tuple(sorted(game.no_auto_farm)),
        # Merchant availability, seal/event completion and money multiplier
        # live in flags rather than map blocks.  Include them to avoid merging
        # states with different legal conversion edges.
        tuple(sorted(
            (str(key), repr(value))
            for key, value in game.flags.items()
            if key not in {"stopBeforeTerminalClosure", "routeDecisions"}
        )),
    )


def optimistic_funding(game: Game) -> int:
    """Safe upper bound: collect every remaining key and every monster coin."""
    return int(optimistic_funding_ledger(game)["optimistic_total"])


def target_action(fid: str, x: int, y: int, kind: str, eid: str) -> GameAction:
    def apply(game: Game) -> None:
        block = game.block_at(fid, (x, y))
        if not block or block.kind != kind or block.eid != eid:
            game.fail(f"stale terminal target {fid} x{x}y{y} {kind}:{eid}")
        if game.state["floor"] != fid:
            game.fly(fid)
        go_to_decomposed(game, fid, x, y, f"terminal resource A* {kind}:{eid}")
        if game.state["hp"] <= 0:
            game.fail("terminal resource edge is fatal")
        # Preserve the real endpoint.  Flying to the same floor from above or
        # below selects different stair landings, which matters for one-way
        # flowers (notably MT33).  The state key already retains floor/position,
        # so forcing a common fly floor here was both unsafe and unnecessary.

    return GameAction(
        name=f"terminal {fid} x{x}y{y} {kind}:{eid}",
        apply=apply,
        metadata={"floor": fid, "x": x, "y": y, "kind": kind, "eid": eid},
    )


def merchant_action(fid: str, x: int, y: int, label: str) -> GameAction:
    def apply(game: Game) -> None:
        if game.state["floor"] != fid:
            game.fly(fid)
        if not optional_talk_trader(game, fid, x, y, f"terminal resource A* {label}"):
            game.fail(f"terminal merchant unavailable: {label}")
        # Keep the merchant's real endpoint for the same directional-fly reason
        # as ordinary resource targets.

    return GameAction(
        name=f"terminal merchant {fid} x{x}y{y} {label}",
        apply=apply,
        metadata={"floor": fid, "x": x, "y": y, "kind": "merchant", "eid": label},
    )


def actions(
    game: Game,
    *,
    funding_only: bool = False,
    min_enemy_money: int = 0,
) -> Iterable[GameAction]:
    # If even the impossible collect-everything bound misses the shop, this
    # state has no useful children.
    target = shop_cost(game.state["times1"])
    if optimistic_funding(game) < target:
        return ()
    rows: list[tuple[int, int, str, int, int, str, str]] = []
    for fid in sorted(game.visited, key=lambda value: int(value[2:])):
        floor = game.floors.get(fid)
        if floor is None:
            continue
        for (x, y), block in floor.blocks.items():
            if block.kind not in {"item", "enemy"}:
                continue
            if (fid, x, y) in game.retreat_wizards or (fid, x, y) in game.no_auto_farm:
                continue
            # Do not exclude afterBattle enemies.  MT45's two white kings and
            # two dark knights are real zero-damage resources whose mechanism
            # events open the other half of the pocket; shared Game owns those
            # mutations and the search must execute them.
            if block.kind == "item":
                if funding_only and block.eid not in {"yellowKey", "blueKey"}:
                    continue
                priority = 0 if block.eid in {"yellowKey", "blueKey", "redKey", "redGem", "blueGem"} else 1
                money = 0
            else:
                priority = 2
                money = int(game.enemies.get(block.eid, {}).get("money", 0))
                if money <= 0 or game.enemy_damage(block.eid) == math.inf:
                    continue
                # Large mechanism/monster groups drive the funding search.
                # Tiny enemies are deferred while the gap is large, then
                # reintroduced near the threshold so exact last-coins remain
                # discoverable.  This is action ordering/reduction only; all
                # accepted edges still replay through strict Game.
                if money < min_enemy_money and target - effective_funding(game) > 100:
                    continue
            rows.append((priority, -money, fid, x, y, block.kind, block.eid))
    out = [target_action(fid, x, y, kind, eid) for _p, _m, fid, x, y, kind, eid in sorted(rows)]
    # Explicit modeled conversion nodes.  Used/unfunded/unreachable merchants
    # simply fail their strict edge and are ignored by GameAStar.
    if (
        not game.flags.get("skipFinalKeyBundle")
        and not game.flags.get(game.trader_flag("MT31", 1, 11))
    ):
        out.append(merchant_action("MT31", 1, 11, "1000G_to_4YK_1BK"))
    if not game.flags.get(game.trader_flag("MT45", 9, 3)):
        out.append(merchant_action("MT45", 9, 3, "1000G_to_2000HP"))
    return tuple(out)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--game-pickle", type=Path, default=DEFAULT_PICKLE)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--max-expansions", type=int, default=5000)
    parser.add_argument(
        "--raw-game", action="store_true",
        help="search directly from the supplied strict Game checkpoint instead of reconstructing pre-boss state",
    )
    parser.add_argument(
        "--buy-first-shop", action="store_true",
        help="buy exactly one immediately affordable HP shop before searching the next threshold",
    )
    parser.add_argument(
        "--release-blocked-items", action="store_true",
        help="release terminal route reservations before combination search",
    )
    parser.add_argument(
        "--funding-only", action="store_true",
        help="limit item targets to yellow/blue keys while retaining every money enemy",
    )
    parser.add_argument(
        "--min-enemy-money", type=int, default=0,
        help="defer smaller base-money enemies until effective funding is within 100G",
    )
    args = parser.parse_args()

    start = load_pre_boss(args.game_pickle, raw_game=args.raw_game)
    if args.release_blocked_items:
        start.blocked_items.clear()
    if args.buy_first_shop:
        from src.solver.game_route import buy_hp_with_remaining_gold
        before_times = int(start.state["times1"])
        buy_hp_with_remaining_gold(start, max_count=1)
        if int(start.state["times1"]) != before_times + 1:
            start.fail("requested first HP shop was not purchased")
    target = shop_cost(start.state["times1"])
    hp_gain = 100 * (int(start.state["times1"]) + 1)
    optimistic = optimistic_funding(start)
    funding_ledger = optimistic_funding_ledger(start)
    start_steps = len(start.steps)

    result = GameAStar(
        actions=lambda game: actions(
            game,
            funding_only=args.funding_only,
            min_enemy_money=args.min_enemy_money,
        ),
        goal=lambda game: effective_funding(game) >= target,
        heuristic=lambda _game: 0.0,
        edge_cost=lambda before, after, _action: float(max(0, before.state["hp"] - after.state["hp"])),
        state_key=state_key,
        # Preserve Dijkstra/A* cost correctness: funding is a secondary queue
        # key only, never an HP-cost heuristic.
        tie_breaker=lambda game: float(max(0, target - effective_funding(game))),
        weight=1.0,
        max_expansions=args.max_expansions,
        # Any pre-shop loss >= its HP gain cannot improve the incumbent.
        upper_bound=float(hp_gain),
    ).search(start)

    candidate = result.game
    post_shop = None
    errors: list[str] = []
    if candidate is not None:
        try:
            sell_yellow_keys_for_gold(candidate, target, preserve_yk=0)
            if candidate.state["gold"] < target:
                candidate.fail(f"effective funding did not convert to {target} actual gold")
            if candidate.state["floor"] != "MT46":
                candidate.fly("MT46")
            go_to_decomposed(candidate, "MT46", 6, 2, "terminal resource A* HP shop")
            candidate.buy_shop("hp", 1, shop_pos=(6, 1))
            post_shop = compact(candidate)
        except Exception as exc:  # RouteError plus malformed experimental state
            errors.append(f"{type(exc).__name__}: {exc}")

    payload = {
        "ok": result.found and candidate is not None and not errors,
        "scope": "complete remaining pre-boss item/enemy map; shared strict Game resource groups",
        "bounded": True,
        "start": compact(start),
        "target_shop_cost": target,
        "shop_hp_gain": hp_gain,
        "start_effective_funding": effective_funding(start),
        "optimistic_collect_all_funding": optimistic,
        "optimistic_funding_ledger": funding_ledger,
        "max_expansions": args.max_expansions,
        "funding_only": args.funding_only,
        "min_enemy_money": args.min_enemy_money,
        "raw_game": args.raw_game,
        "buy_first_shop": args.buy_first_shop,
        "release_blocked_items": args.release_blocked_items,
        "found": result.found,
        "reason": result.reason,
        "expansions": result.expansions,
        "generated": result.generated,
        "pre_shop_hp_loss": None if result.game is None else start.state["hp"] - result.game.state["hp"],
        "post_shop": post_shop,
        "net_hp_improvement": None if post_shop is None else post_shop["hp"] - start.state["hp"],
        "actions": [dict(action.metadata) for action in result.actions],
        "added_steps": [] if candidate is None else candidate.steps[start_steps:],
        "errors": errors,
        "claim": "exact for explored strict-Game states under the HP-improvement bound; max-expansions is not exhaustion",
    }
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: payload[key] for key in (
        "ok", "start", "target_shop_cost", "shop_hp_gain",
        "start_effective_funding", "optimistic_collect_all_funding",
        "found", "reason", "expansions", "generated", "pre_shop_hp_loss",
        "post_shop", "net_hp_improvement", "actions", "errors",
    )}, ensure_ascii=False, indent=2))
    print(f"out={args.out_json}")
    return 0 if payload["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
