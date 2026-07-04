#!/usr/bin/env python3
"""Probe a pure-TE post-40 route with late 49F sealing.

This is deliberately kept out of best/ until it is replayed in the live page.
It follows the user-required endgame shape:

    24F -> 50F thief event, downFly to 49F, seal/clear fake redKing,
    return through 24F -> 50F, then fight the final redKing.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import floor_final_score as fs


ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "outputs" / "results" / "post40_te_late49_probe.json"
OUT_MD = ROOT / "outputs" / "reports" / "post40_te_late49_probe.md"


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


post = load_module("post40_te_late49_base", ROOT / "scripts" / "search_post40_guide_route.py")
bridge = load_module("post40_te_late49_bridge", ROOT / "scripts" / "run_post40_from_zone3_candidate.py")


def state_line(s: dict[str, Any]) -> str:
    return (
        f"HP={s['hp']} ATK={s['atk']} DEF={s['def']} "
        f"YK={s['yk']} BK={s['bk']} RK={s['rk']} G={s['gold']} "
        f"{s['floor']} x{s['x']}y{s['y']}"
    )


def make_game(label: str) -> Any:
    if label == "guide_save37_baseline":
        return post.Game(post.read_json(post.SNAPSHOT))
    if label in {"slot26_clean_7def", "slot26_clean_8def", "slot26_clean_8atk"}:
        r37_center = bridge.clean.build_r37_center()
        mid_shop = {
            "slot26_clean_7def": None,
            "slot26_clean_8def": "D",
            "slot26_clean_8atk": "A",
        }[label]
        zg = bridge.clean.finish_variant(r37_center, first_shop="D", mid_shop=mid_shop)
        snapshot = bridge.synthetic_snapshot_from_zone3(zg, label)
        g = post.Game(snapshot)
        zsnap = zg.snapshot()
        g.state["dmg"] = int(zsnap.get("dmg", 0))
        g.state["yd"] = int(zsnap.get("yd", 0))
        g.state["bd"] = int(zsnap.get("bd", 0))
        g.state["rd"] = int(zsnap.get("rd", 0))
        g.flags["TE"] = True
        g.flags["addhp"] = True
        return g
    focused_builders = {
        "post40_focused_slice2": bridge.rebuild_post40_focused_slice2,
        "post40_focused_slice3": bridge.rebuild_post40_focused_slice3,
        "post40_focused_slice5_goal": bridge.rebuild_post40_focused_slice5_goal,
        "post40_focused_slice5_mid_center": bridge.rebuild_post40_focused_slice5_mid_center,
        "post40_focused_slice4_goal": bridge.rebuild_post40_focused_slice4_goal,
        "post40_focused_slice4_mid_center": bridge.rebuild_post40_focused_slice4_mid_center,
    }
    if label in focused_builders:
        zg = focused_builders[label]()
        snapshot = bridge.synthetic_snapshot_from_zone3(zg, label)
        g = post.Game(snapshot)
        zsnap = zg.snapshot()
        g.state["dmg"] = int(zsnap.get("dmg", 0))
        g.state["yd"] = int(zsnap.get("yd", 0))
        g.state["bd"] = int(zsnap.get("bd", 0))
        g.state["rd"] = int(zsnap.get("rd", 0))
        g.flags["TE"] = True
        g.flags["addhp"] = True
        return g
    raise ValueError(label)


def post_shield_no49(g: Any) -> None:
    g.set_segment("post-shield prep without 49F")
    g.fly("MT43")
    g.go_to("MT43", 3, 1, "43F upper-left yellow door")
    for pos in [(3, 6), (8, 6), (11, 5)]:
        g.go_to("MT43", *pos, f"43F middle/right resource {pos}")
    g.go_to("MT43", 9, 1, "43F upper-right guard")
    g.go_to("MT43", 9, 4, "43F sacred shield")
    g.go_to("MT43", 11, 11, "43F lower-right blue key")
    g.fly("MT46")
    g.go_to("MT46", 3, 8, "46F magic key")
    g.fly("MT41")
    g.use_big_key("41F open all yellow doors")
    g.go_to("MT41", 5, 6, "41F left blue door")
    g.go_to("MT41", 2, 2, "41F upper-left red wizard")
    g.go_to("MT41", 4, 1, "41F upper-left blue key")
    g.go_to("MT41", 7, 6, "41F right blue door")
    g.go_to("MT41", 9, 2, "41F right wall trigger")
    g.go_to("MT41", 10, 2, "41F upper-right red wizard")
    g.fly("MT40")
    g.fly("MT41")
    g.go_to("MT41", 6, 5, "41F downFly")
    for pos in [(3, 10), (4, 10), (3, 11), (4, 11), (8, 10), (9, 10), (8, 11), (9, 11)]:
        post.safe_try(g, g.go_to, "MT41", *pos, f"41F magic-key resource {pos}")
    post.trace_point("late49 after 41F magic-key resources", g)

    # Keep the downFly for the required TE sequence:
    # 24F -> 50F thief, then downFly from 50F to 49F for sealing.
    post.trace_point("late49 reserve downFly for 50F->49F", g)

    # Take the 42F red key before the attack-first shop/farming loop spends the
    # remaining yellow-key routing budget.  It is the pre-princess red key for
    # the user-required late-49 TE order.
    g.fly("MT42")
    g.go_to("MT42", 7, 1, "42F red key for late-49 TE")
    post.trace_point("late49 after 42F red key", g)

    # Late-49 cannot use the 49F knife before 35F dragon.  Buy attack first so
    # magicDragon is not a 100+ turn fight.
    post.buy_shops_to_stat(g, "atk", 291, "46F pre-dragon atk shop", preserve_yk=1)
    post.buy_shops_to_stat(g, "def", 430, "46F pre-dragon def shop", preserve_yk=1)
    post.kill_47_retreat_wizards(g)
    post.clear_zero_damage_monsters(g, preserve_yk=1, min_floor=1)
    g.blocked_items.add(("MT20", 11, 5))
    post.cleanup_reachable_items(g, {"redGem", "blueGem", "yellowKey", "blueKey", "redKey"},
                                 min_floor=1, preserve_rk=1)
    for pos in [(1, 3), (2, 3), (1, 5), (2, 5)]:
        post.safe_try(g, g.go_to, "MT45", *pos, f"45F left gem {pos}")
    post.buy_shops_to_stat(g, "atk", 291, "46F atk shop", preserve_yk=1)
    if g.state["gold"] < 1000:
        post.safe_try(g, post.farm_gold_after_coin, g, 1000, 0, 1)
    if g.state["floor"] != "MT45":
        g.fly("MT45")
    if g.state["gold"] >= 1000 and not g.flags.get(g.trader_flag("MT45", 9, 3)):
        g.talk_trader("MT45", 9, 3, "45F 1000G to 2000HP")
    post.eat_all_reachable_potions(g, min_floor=1)
    post.trace_point("late49 after no-49 prep", g)


def trigger_mt50_thief(g: Any) -> None:
    g.move_adjacent("MT50", 6, 5, "50F thief event")
    before = g.snapshot()
    g.flags["50final"] = True
    g.flags["50thief"] = True
    g.record("event", (6, 5), "redKing", before, "50F thief reveals final redKing")
    g.set_block("MT50", (6, 5), "enemy", "redKing", 245)


def downfly_to_mt49_event(g: Any) -> None:
    if g.state["downFly"] <= 0:
        g.fail("no downFly for late 49F seal")
    if g.state["floor"] != "MT50":
        g.fail(f"late 49F downFly must start on MT50, got {g.state['floor']}")
    before = g.snapshot()
    g.state["downFly"] -= 1
    g.state["floor"] = "MT49"
    g.visited.add("MT49")
    g.record("downFly", (g.state["x"], g.state["y"]), "downFly", before, "50F downFly to 49F seal event")


def trigger_mt49_event(g: Any) -> None:
    if g.state["floor"] != "MT49":
        g.fail(f"not on MT49 for seal event: {g.state['floor']}")
    before = g.snapshot()
    g.state["x"], g.state["y"] = 6, 6
    g.set_block("MT49", (6, 7), "door", "specialDoor", 85)
    g.set_block("MT49", (6, 3), "enemy", "redKing", 245)
    for p in [(5, 2), (5, 3), (5, 4), (6, 4), (7, 4), (7, 3), (7, 2), (6, 2)]:
        g.set_block("MT49", p, "enemy", "whiteKing", 246)
    g.record("event", (6, 6), "redKing", before, "49F seal event after 50F thief")


def clear_mt49_from_center(g: Any) -> None:
    g.retreat_wizards |= {("MT49", 5, 2), ("MT49", 7, 2), ("MT49", 5, 4), ("MT49", 7, 4)}
    for pos in [(6, 4), (5, 3), (7, 3), (6, 2)]:
        g.go_to("MT49", *pos, f"49F seal cardinal guard {pos}")
    g.flags["49sealed"] = True
    had_50final = bool(g.flags.get("50final"))
    # The 50F thief flag is already set, but the redKing on MT49 is the sealed
    # fake redKing and must use the 49sealed stats until it is defeated.
    g.flags["50final"] = False
    g.retreat_wizards.clear()
    for pos in [(5, 2), (7, 2), (5, 4), (7, 4), (6, 3)]:
        g.go_to("MT49", *pos, f"49F seal corner/fake redKing {pos}")
    if had_50final:
        g.flags["50final"] = True
    for pos in [(5, 2), (7, 2), (2, 4), (3, 4), (4, 4), (8, 4), (9, 4), (10, 4), (5, 5), (6, 5), (7, 5)]:
        post.safe_try(g, g.go_to, "MT49", *pos, f"49F late reward {pos}")


def late49_endgame(g: Any) -> None:
    g.set_segment("late-49 TE endgame")
    # Late-49 TE still needs one red key for the 25F/26F princess path before
    # the 49F rewards exist.  The reachable 42F red key must be modeled here;
    # otherwise an RK=0 40F state is incorrectly rejected at the 25F red door.
    post.cleanup_reachable_items(g, {"redGem", "blueGem", "yellowKey", "blueKey", "redKey"}, min_floor=1, preserve_rk=1)
    if g.state["rk"] < 1:
        g.fly("MT42")
        g.go_to("MT42", 7, 1, "42F red key for late-49 TE")
    post.eat_all_reachable_potions(g, min_floor=1)

    post.ensure_hp_for_enemy(g, "magicDragon", 20)
    g.fly("MT35")
    g.go_to("MT35", 6, 7, "35F magic dragon before knife")
    g.go_to("MT35", 6, 6, "35F snow")
    for pos in [(5, 5), (6, 5), (7, 5)]:
        post.safe_try(g, g.go_to, "MT35", *pos, f"35F dragon potion {pos}")

    post.collect_net_yellow_keys_until(g, 1, "13F sacred sword yellow door", min_floor=1)
    g.fly("MT13")
    g.go_to("MT13", 6, 10, "13F sacred sword yellow door")
    g.state["x"], g.state["y"] = 6, 11
    g.go_to("MT13", 6, 10, "13F stand on lava edge")
    for y in [9, 8, 7, 6]:
        g.use_snow("13F freeze lava for sacred sword")
        g.go_to("MT13", 6, y, f"13F lava path y{y}")
    g.go_to("MT13", 6, 5, "13F sacred sword")
    post.cleanup_reachable_items(g, {"redGem", "blueGem"}, min_floor=1, preserve_rk=1)

    post.buy_shops_to_stat(g, "def", 502, "46F endgame def shop", preserve_yk=1)
    g.fly("MT2")
    g.talk_mt2_bless()
    post.collect_net_yellow_keys_until(g, 1, "16F superPotion oldman path", min_floor=1)
    g.fly("MT16")
    g.talk_mt16_oldman()

    post.buy_hp_with_remaining_gold(g, 2)
    post.ensure_hp_for_enemy(g, "blackMagician", 20)
    g.fly("MT25")
    g.go_to("MT25", 6, 10, "25F red door")
    g.go_to("MT25", 6, 9, "25F trigger")
    g.go_to("MT25", 6, 6, "25F black magician")
    for pos in [(4, 8), (5, 8), (7, 8), (8, 8)]:
        g.go_to("MT25", *pos, f"25F red key {pos}")

    g.fly("MT26")
    for y in [10, 9, 8]:
        g.go_to("MT26", 6, y, f"26F princess red door y{y}")
    g.use_snow("26F freeze lava before princess")
    g.go_to("MT26", 6, 7, "26F before princess")
    g.talk_mt26_princess()

    if g.state["gold"] < 1000:
        post.safe_try(g, post.farm_gold_after_coin, g, 1000, 0, 1)
    if g.state["floor"] != "MT45":
        g.fly("MT45")
    if g.state["gold"] >= 1000 and not g.flags.get(g.trader_flag("MT45", 9, 3)):
        g.talk_trader("MT45", 9, 3, "45F 1000G to 2000HP")

    post.buy_hp_with_remaining_gold(g, 4)
    post.final_key_bundle_and_mt20_potions(g)
    post.eat_all_reachable_potions(g, min_floor=1)
    post.eat_final_yellow_door_potions(g, min_floor=1, preserve_rk=1)

    g.fly("MT24")
    g.go_to("MT24", 6, 8, "24F red door before 50F thief")
    g.trigger_mt24_to_mt50()
    trigger_mt50_thief(g)
    downfly_to_mt49_event(g)
    trigger_mt49_event(g)
    clear_mt49_from_center(g)

    post.buy_hp_with_remaining_gold(g, 4)
    post.cleanup_reachable_items(g, {"redGem", "blueGem", "yellowKey", "blueKey"}, min_floor=1, preserve_rk=0)
    post.eat_all_reachable_potions(g, min_floor=1)
    if g.state["superPotion"] > 0:
        g.use_super_potion("final superPotion after late 49F rewards")

    g.fly("MT24")
    g.trigger_mt24_to_mt50()
    g.go_to("MT50", 6, 5, "50F final redKing after 49F seal")


def run_stages(g: Any, trace: bool = False) -> Any:
    stages = [
        ("prefix48", post.guide_prefix_to_48_visit),
        ("pre_earthquake", post.collect_guide_pre_earthquake),
        ("farm_earthquake", post.farm_gold_for_earthquake),
        ("shield", post.earthquake_and_shield),
        ("post_shield_no49", post_shield_no49),
        ("late49_endgame", late49_endgame),
    ]
    post.TRACE_ENABLED = trace
    for name, fn in stages:
        before = g.snapshot()
        before["step_count"] = len(g.steps)
        try:
            fn(g)
        except post.RouteError:
            break
        after = g.snapshot()
        after["step_count"] = len(g.steps)
        g.stage_summaries.append(
            {
                "name": name,
                "before": before,
                "after": after,
                "delta_dmg": after["dmg"] - before["dmg"],
                "delta_steps": after["step_count"] - before["step_count"],
                "stock_score": post.stock_score(after),
            }
        )
    return g


def row_for(label: str, g: Any) -> dict[str, Any]:
    final_score = fs.current_floor_and_below_final_score(g, 50, monster_gold_factor=0.5)
    return {
        "label": label,
        "ok": not g.errors,
        "final": g.snapshot(),
        "state_text": state_line(g.state),
        "current_floor_final_score": final_score,
        "stage_summaries": g.stage_summaries,
        "errors": g.errors,
        "steps": g.steps,
    }


def write_outputs(rows: list[dict[str, Any]]) -> None:
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps({"rows": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# Post-40 pure-TE late-49 probe",
        "",
        "- Flow: 24F -> 50F thief, downFly to 49F seal, return 24F -> 50F final.",
        "- Local only. Web strict-human-input verification is still required.",
        "- Gold must match exactly; no live-gold tolerance is used.",
        "- Score scope: current floor and below, no lucky coin; remaining zero-damage monster gold uses normal `100G=50HP`.",
        "",
        "| route | result | final | dmg | final-score<=50 | key tools | errors |",
        "| --- | --- | --- | ---: | ---: | --- | --- |",
    ]
    for row in rows:
        f = row["final"]
        err = "; ".join(row["errors"][:2]) if row["errors"] else ""
        score = row["current_floor_final_score"]
        tools = {**(score.get("held_tool_counts") or {}), **{f"map:{k}": v for k, v in (score.get("map_tool_counts") or {}).items()}}
        lines.append(
            f"| {row['label']} | {'OK' if row['ok'] else 'FAIL'} | `{row['state_text']}` | "
            f"{f['dmg']} | {score['final_score']:g} | `{tools}` | {err} |"
        )
    lines.append("")
    for row in rows:
        lines.append(f"## {row['label']}")
        lines.append("")
        lines.append(f"- ok: `{row['ok']}`")
        lines.append(f"- final: `{row['state_text']}` dmg={row['final']['dmg']} door={row['final']['yd']}/{row['final']['bd']}/{row['final']['rd']}")
        score = row["current_floor_final_score"]
        lines.append(
            f"- final-score<=50: `{score['final_score']:g}` "
            f"(stock={score['stock_score']:g}, remaining={score['remaining_value_hp']:g})"
        )
        lines.append(f"- important tools: held `{score.get('held_tool_counts') or {}}`; map `{score.get('map_tool_counts') or {}}`")
        if row["errors"]:
            lines.append("- errors:")
            lines.extend(f"  - {e}" for e in row["errors"][:8])
        lines.append("")
        lines.append("| stage | after | delta dmg | total dmg | stock |")
        lines.append("| --- | --- | ---: | ---: | ---: |")
        for stage in row["stage_summaries"]:
            after = stage["after"]
            lines.append(
                f"| {stage['name']} | `{state_line(after)}` | {stage['delta_dmg']} | "
                f"{after['dmg']} | {stage['stock_score']:.1f} |"
            )
        lines.append("")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--only",
        action="append",
        choices=[
            "guide_save37_baseline",
            "slot26_clean_7def",
            "slot26_clean_8def",
            "slot26_clean_8atk",
            "post40_focused_slice2",
            "post40_focused_slice3",
            "post40_focused_slice5_goal",
            "post40_focused_slice5_mid_center",
            "post40_focused_slice4_goal",
            "post40_focused_slice4_mid_center",
        ],
    )
    parser.add_argument("--trace", action="store_true")
    args = parser.parse_args()
    labels = args.only or ["guide_save37_baseline", "slot26_clean_7def"]
    rows = []
    for label in labels:
        print(f"[late49] running {label}", flush=True)
        g = run_stages(make_game(label), trace=args.trace)
        row = row_for(label, g)
        rows.append(row)
        print(f"[late49] done {label} ok={row['ok']} {row['state_text']} errors={len(row['errors'])}", flush=True)
        if row["errors"]:
            print("  first_error:", row["errors"][0], flush=True)
    write_outputs(rows)
    print(f"json={OUT_JSON}")
    print(f"md={OUT_MD}")
    return 0 if any(row["ok"] for row in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
