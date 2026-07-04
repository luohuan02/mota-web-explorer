#!/usr/bin/env python3
"""Probe strict20 post-49 shop allocation variants.

The strict20 4F-50F candidate reaches 49F with strong HP but loses too much in
the last segment because the current tail over-buys DEF and under-buys ATK.
This script keeps the event/order skeleton fixed and varies only late 46F shop
targets plus the final HP-shop count.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "outputs" / "results" / "strict20_post49_shop_variants.json"
OUT_MD = ROOT / "outputs" / "reports" / "strict20_post49_shop_variants.md"

sys.path.insert(0, str(ROOT / "scripts"))
import run_post40_from_zone3_candidate as runner  # noqa: E402


post = runner.post
score_mod = runner.score_mod


PLANS: list[dict[str, Any]] = [
    {"name": "no_late_stat_hp4", "shops": [], "hp_shops": 4},
    {"name": "def442_hp4", "shops": [("def", 442)], "hp_shops": 4},
    {"name": "def452_hp4", "shops": [("def", 452)], "hp_shops": 4},
    {"name": "def462_hp4", "shops": [("def", 462)], "hp_shops": 4},
    {"name": "def472_hp4", "shops": [("def", 472)], "hp_shops": 4},
    {"name": "baseline_def502_hp4", "shops": [("def", 502)], "hp_shops": 4},
    {"name": "def482_hp4", "shops": [("def", 482)], "hp_shops": 4},
    {"name": "def492_hp4", "shops": [("def", 492)], "hp_shops": 4},
    {"name": "def512_hp4", "shops": [("def", 512)], "hp_shops": 4},
    {"name": "atk426_hp4", "shops": [("atk", 426)], "hp_shops": 4},
    {"name": "atk431_hp4", "shops": [("atk", 431)], "hp_shops": 4},
    {"name": "atk426_def482_hp4", "shops": [("atk", 426), ("def", 482)], "hp_shops": 4},
    {"name": "def482_atk426_hp4", "shops": [("def", 482), ("atk", 426)], "hp_shops": 4},
    {"name": "atk431_def482_hp4", "shops": [("atk", 431), ("def", 482)], "hp_shops": 4},
    {"name": "def492_atk426_hp4", "shops": [("def", 492), ("atk", 426)], "hp_shops": 4},
    {"name": "def502_atk426_hp4", "shops": [("def", 502), ("atk", 426)], "hp_shops": 4},
    {"name": "def482_hp5", "shops": [("def", 482)], "hp_shops": 5},
    {"name": "atk426_def482_hp5", "shops": [("atk", 426), ("def", 482)], "hp_shops": 5},
]


def state_line(s: dict[str, Any]) -> str:
    return (
        f"HP={s['hp']} ATK={s['atk']} DEF={s['def']} "
        f"YK={s['yk']} BK={s['bk']} RK={s['rk']} G={s['gold']} "
        f"{s['floor']} x{s['x']}y{s['y']} dmg={s['dmg']} "
        f"door={s['yd']}/{s['bd']}/{s['rd']}"
    )


def build_base_after_49() -> Any:
    selected = {"strict20_preserve_pickaxe_40"}
    zg = runner.build_zone3_variants(selected)["strict20_preserve_pickaxe_40"]
    g = runner.make_post_game_from_zone3("strict20_preserve_pickaxe_40", zg)
    runner.run_stages(g, stop_after="post_shield_49")
    if g.errors:
        raise RuntimeError(g.errors[0])
    return g


def run_shop_plan(g: Any, shops: list[tuple[str, int]]) -> None:
    for kind, target in shops:
        post.buy_shops_to_stat(g, kind, target, f"46F post49 variant {kind}{target}", preserve_yk=1)


def post49_variant(g: Any, plan: dict[str, Any]) -> None:
    g.set_segment(f"post-49 variant {plan['name']}")
    post.cleanup_reachable_items(g, {"redGem", "blueGem", "yellowKey", "blueKey"}, min_floor=1, preserve_rk=1)
    post.eat_all_reachable_potions(g, min_floor=1)
    post.cleanup_reachable_items(g, {"redGem", "blueGem", "yellowKey", "blueKey"}, min_floor=1, preserve_rk=1)
    if g.state["yk"] <= 0:
        post.cleanup_reachable_items(g, {"yellowKey"}, min_floor=1, preserve_rk=1)

    post.ensure_hp_for_enemy(g, "magicDragon", 20)
    g.fly("MT35")
    g.go_to("MT35", 6, 7, "35F dragon")
    g.go_to("MT35", 6, 6, "35F snow")
    for pos in [(5, 5), (6, 5), (7, 5)]:
        post.safe_try(g, g.go_to, "MT35", *pos, f"35F dragon reward potion {pos}")

    if g.state["yk"] <= 0 and g.state["gold"] >= 1000 and not g.flags.get(g.trader_flag("MT31", 1, 11)):
        if g.state["floor"] != "MT31":
            g.fly("MT31")
        post.optional_talk_trader(g, "MT31", 1, 11, "31F late key merchant before 13F sword")
    g.fly("MT13")
    g.go_to("MT13", 6, 10, "13F sword yellow door")
    g.state["x"], g.state["y"] = 6, 11
    g.go_to("MT13", 6, 10, "13F step onto lava entry")
    for y in [9, 8, 7, 6]:
        g.use_snow("13F freeze lava for sword")
        g.go_to("MT13", 6, y, f"13F lava path y{y}")
    g.go_to("MT13", 6, 5, "13F sacred sword")
    post.cleanup_reachable_items(g, {"redGem", "blueGem"}, min_floor=1, preserve_rk=1)

    run_shop_plan(g, plan["shops"])

    g.fly("MT2")
    g.talk_mt2_bless()
    g.fly("MT16")
    g.talk_mt16_oldman()

    post.ensure_hp_for_enemy(g, "blackMagician", 20)
    g.fly("MT25")
    g.go_to("MT25", 6, 10, "25F red door")
    g.go_to("MT25", 6, 9, "25F switch trigger")
    g.go_to("MT25", 6, 6, "25F blackMagician")
    for pos in [(4, 8), (5, 8), (7, 8), (8, 8)]:
        g.go_to("MT25", *pos, f"25F red key {pos}")

    g.fly("MT26")
    for y in [10, 9, 8]:
        g.go_to("MT26", 6, y, f"26F princess red door y{y}")
    g.use_snow("26F freeze princess lava")
    g.go_to("MT26", 6, 7, "26F princess front")
    g.talk_mt26_princess()

    if g.state["gold"] < 1000:
        post.safe_try(g, post.farm_gold_after_coin, g, 1000, 0, 1)
    if g.state["floor"] != "MT45":
        g.fly("MT45")
    if g.state["gold"] >= 1000 and not g.flags.get(g.trader_flag("MT45", 9, 3)):
        post.optional_talk_trader(g, "MT45", 9, 3, "45F 1000G buy 2000HP")

    post.buy_hp_with_remaining_gold(g, int(plan["hp_shops"]))
    post.final_key_bundle_and_mt20_potions(g)
    post.eat_all_reachable_potions(g, min_floor=1)
    post.eat_final_yellow_door_potions(g, min_floor=1, preserve_rk=1)
    if g.state["superPotion"] > 0:
        g.use_super_potion("final superPotion")

    g.fly("MT24")
    g.go_to("MT24", 6, 8, "24F red door")
    g.trigger_mt24_to_mt50()
    g.trigger_mt50_final()


def run_one(base: Any, plan: dict[str, Any]) -> dict[str, Any]:
    g = copy.deepcopy(base)
    before = g.snapshot()
    before["step_count"] = len(g.steps)
    try:
        post49_variant(g, plan)
    except post.RouteError:
        pass
    after = g.snapshot()
    after["step_count"] = len(g.steps)
    score = score_mod.current_floor_and_below_final_score(g, 50, monster_gold_factor=0.5)
    return {
        "name": plan["name"],
        "shops": plan["shops"],
        "hp_shops": plan["hp_shops"],
        "ok": not g.errors,
        "before": before,
        "final": after,
        "state_text": state_line(after),
        "delta_dmg": after["dmg"] - before["dmg"],
        "delta_steps": after["step_count"] - before["step_count"],
        "final_score": score,
        "errors": list(g.errors),
        "steps": g.steps[len(base.steps):],
    }


def write_outputs(rows: list[dict[str, Any]]) -> None:
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps({"rows": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# strict20 post-49 shop variants",
        "",
        "| variant | ok | final | delta_dmg | final-score<=50 | errors |",
        "|---|---|---|---:|---:|---|",
    ]
    for row in rows:
        err = "; ".join(row["errors"][:1]) if row["errors"] else ""
        lines.append(
            f"| {row['name']} | {row['ok']} | `{row['state_text']}` | "
            f"{row['delta_dmg']} | {row['final_score']['final_score']:g} | {err} |"
        )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    base = build_base_after_49()
    print(f"base={state_line(base.snapshot())}", flush=True)
    rows = []
    for plan in PLANS:
        print(f"[variant] {plan['name']}", flush=True)
        row = run_one(base, plan)
        rows.append(row)
        print(
            f"  ok={row['ok']} {row['state_text']} "
            f"score={row['final_score']['final_score']:g} errors={len(row['errors'])}",
            flush=True,
        )
    rows.sort(
        key=lambda r: (
            bool(r["ok"]),
            int(r["final"].get("hp", -10**9)),
            float(r["final_score"]["final_score"]),
        ),
        reverse=True,
    )
    write_outputs(rows)
    print(f"json={OUT_JSON}")
    print(f"md={OUT_MD}")
    return 0 if any(row["ok"] for row in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
