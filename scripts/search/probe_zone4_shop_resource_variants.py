#!/usr/bin/env python3
"""Replay complete late-49 TE tails for shop/resource strategy variants.

The input pickle is a shared ``Zone4Game`` checkpoint after
``post_shield_no49_te`` and already contains the canonical 41F prefix steps.
Each variant clones that state, sets only strategy flags, and executes the
normal ``late49_endgame`` Game pipeline.  Outputs are complete Game walk JSONs
that can go directly to the Markdown generator and unified live verifier.
"""
from __future__ import annotations

import argparse
import json
import pickle
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.search.zone4_game_route import Zone4Game  # noqa: E402
from src.solver.game_route import RouteError, go_to_decomposed, late49_endgame, state_line  # noqa: E402
from scripts.search.zone4_game_route import post_shield_no49  # noqa: E402

DEFAULT_CHECKPOINT = ROOT / "outputs/results/zone4_pre_late49_checkpoint.pkl"


def load_game(path: Path) -> Zone4Game:
    sys.modules["__main__"].Zone4Game = Zone4Game
    game = pickle.loads(path.read_bytes())
    if not isinstance(game, Zone4Game):
        raise TypeError(f"unexpected checkpoint type: {type(game)!r}")
    return game


def compact(game: Zone4Game) -> dict[str, Any]:
    return {key: game.state[key] for key in (
        "floor", "x", "y", "hp", "atk", "def", "yk", "bk", "rk", "gold",
        "dmg", "yd", "bd", "rd", "times1", "magicImmune", "won49", "won50",
    )}


EARLY_GROUPS = {
    "mt31_red": ("MT31", "redGem", "atk"),
    "mt31_blue": ("MT31", "blueGem", "def"),
    "mt32_pair": ("MT32", "blueGem", "both"),
}


def collect_named_group(game: Zone4Game, name: str) -> None:
    """Resolve a named strategy group by item identity, then replay it strictly.

    Coordinates are deliberately not part of the strategy contract.  Every
    matching item is probed on a clone, auto/doors/battles are included, and the
    best real group delta for the requested stat role is committed.
    """
    fid, eid, role = EARLY_GROUPS[name]
    before = game.snapshot()
    best: tuple[tuple[int, ...], Zone4Game] | None = None
    for (x, y), block in list(game.floors[fid].blocks.items()):
        if block.kind != "item" or block.eid != eid:
            continue
        cand = game.clone()
        try:
            if cand.state["floor"] != fid:
                cand.fly(fid)
            go_to_decomposed(cand, fid, x, y, f"early resource search {name}")
        except RouteError:
            continue
        atk_gain = cand.state["atk"] - before["atk"]
        def_gain = cand.state["def"] - before["def"]
        if role == "atk" and atk_gain <= 0:
            continue
        if role == "def" and def_gain <= 0:
            continue
        if role == "both" and (atk_gain <= 0 or def_gain <= 0):
            continue
        if cand.state["hp"] <= 0:
            continue
        rank = (
            atk_gain + def_gain,
            cand.state["hp"] - before["hp"],
            cand.state["gold"] - before["gold"],
            cand.state["yk"] - before["yk"],
            cand.state["bk"] - before["bk"],
        )
        if best is None or rank > best[0]:
            best = (rank, cand)
    if best is None:
        game.fail(f"no legal early resource group for {name}")
    game.__dict__.update(best[1].__dict__)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--final-shop", choices=("def", "atk", "hp", "skip"), required=True)
    parser.add_argument(
        "--prep-last-shop", choices=("atk", "def", "hp", "skip"), default="atk",
        help="shop kind for the last post_shield_no49 purchase",
    )
    parser.add_argument("--post-shield-atk-target", type=int, default=291)
    parser.add_argument(
        "--key-investment-yellow-value", type=int, default=20,
        help="gold opportunity cost assigned to each net yellow key spent while farming",
    )
    parser.add_argument(
        "--early-groups", default="",
        help="comma-separated dynamic groups: mt31_red,mt31_blue,mt32_pair",
    )
    parser.add_argument(
        "--run-post-shield-prep", action="store_true",
        help="checkpoint is immediately after shield; collect groups then run post_shield_no49",
    )
    parser.add_argument(
        "--skip-final-key-bundle", action="store_true",
        help="skip the optional MT31 1000G -> 4YK+1BK conversion and defer MT20 pocket",
    )
    parser.add_argument(
        "--defer-blocked-terminal-resources", action="store_true",
        help="keep route-deferred pockets closed during terminal funding so their keys can fund alternatives",
    )
    parser.add_argument(
        "--terminal-shops-first", action="store_true",
        help="at each terminal fixed-point round, attempt HP shops before spending keys on potion groups",
    )
    parser.add_argument(
        "--stop-before-terminal-closure", action="store_true",
        help="emit the strict pre-boss terminal-resource checkpoint without consuming optional groups",
    )
    parser.add_argument("--out-json", type=Path, required=True)
    parser.add_argument("--out-pickle", type=Path)
    args = parser.parse_args()

    game = load_game(args.checkpoint)
    game.flags["lateFinalShopKind"] = args.final_shop
    game.flags["postShieldLastShopKind"] = args.prep_last_shop
    game.flags["postShieldAtkTarget"] = args.post_shield_atk_target
    game.flags["keyInvestmentYellowValue"] = args.key_investment_yellow_value
    game.flags["skipFinalKeyBundle"] = args.skip_final_key_bundle
    game.flags["deferBlockedTerminalResources"] = args.defer_blocked_terminal_resources
    game.flags["terminalShopsFirst"] = args.terminal_shops_first
    game.flags["stopBeforeTerminalClosure"] = args.stop_before_terminal_closure
    early_groups = [value for value in args.early_groups.split(",") if value]
    unknown = [value for value in early_groups if value not in EARLY_GROUPS]
    if unknown:
        parser.error(f"unknown early groups: {unknown}")
    if early_groups and not args.run_post_shield_prep:
        parser.error("--early-groups requires --run-post-shield-prep")
    if args.run_post_shield_prep:
        prep_before = game.snapshot()
        prep_steps = len(game.steps)
        for group in early_groups:
            collect_named_group(game, group)
        post_shield_no49(game)
        prep_after = game.snapshot()
        game.stage_summaries.append({
            "name": "post_shield_no49_te_resource_variant",
            "label": f"圣盾后TE准备（提前资源组={','.join(early_groups) or 'none'}）",
            "before": prep_before,
            "after": prep_after,
            "delta_dmg": prep_after["dmg"] - prep_before["dmg"],
            "delta_steps": len(game.steps) - prep_steps,
            "stock_score": prep_after["hp"] + prep_after["yk"] * 50 + prep_after["bk"] * 200 + prep_after["gold"] * 0.5,
        })
    before = game.snapshot()
    before_steps = len(game.steps)
    t0 = time.time()
    try:
        late49_endgame(game)
    except Exception as exc:
        if not game.errors:
            game.errors.append(f"{type(exc).__name__}: {exc}")
    elapsed = time.time() - t0
    after = game.snapshot()
    game.stage_summaries.append({
        "name": f"late49_endgame_te_shop_{args.final_shop}",
        "label": f"TE晚49完整尾段（第5商店={args.final_shop}）",
        "before": before,
        "after": after,
        "delta_dmg": after["dmg"] - before["dmg"],
        "delta_steps": len(game.steps) - before_steps,
        "stock_score": after["hp"] + after["yk"] * 50 + after["bk"] * 200 + after["gold"] * 0.5,
    })
    payload = {
        "ok": not game.errors,
        "variant": {
            "lateFinalShopKind": args.final_shop,
            "postShieldLastShopKind": args.prep_last_shop,
            "postShieldAtkTarget": args.post_shield_atk_target,
            "keyInvestmentYellowValue": args.key_investment_yellow_value,
            "earlyGroups": early_groups,
            "skipFinalKeyBundle": args.skip_final_key_bundle,
            "deferBlockedTerminalResources": args.defer_blocked_terminal_resources,
            "terminalShopsFirst": args.terminal_shops_first,
            "stopBeforeTerminalClosure": args.stop_before_terminal_closure,
        },
        "source_checkpoint": str(args.checkpoint),
        "elapsed": elapsed,
        "auto": {"battle": True, "item": "nopotion", "wall": True},
        "auto_final": game.auto_flags,
        "strict_live_model": game.strict_live_model,
        "final": after,
        "steps": game.steps,
        "stage_summaries": game.stage_summaries,
        "errors": game.errors,
    }
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.out_pickle:
        args.out_pickle.parent.mkdir(parents=True, exist_ok=True)
        args.out_pickle.write_bytes(pickle.dumps(game, protocol=pickle.HIGHEST_PROTOCOL))
    print(f"variant={args.final_shop} ok={payload['ok']} elapsed={elapsed:.1f}s")
    print(f"final={state_line(game.state)} dmg={game.state['dmg']} door={game.state['yd']}/{game.state['bd']}/{game.state['rd']} steps={len(game.steps)}")
    print(f"json={args.out_json}")
    if game.errors:
        for error in game.errors[:10]:
            print("ERR", error)
    return 0 if payload["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
