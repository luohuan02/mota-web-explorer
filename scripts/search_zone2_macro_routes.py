#!/usr/bin/env python3
"""Bounded macro search for MT10-post-boss to MT20 vampire routes.

This search deliberately keeps the user's guide macro order as the legality
scaffold, then enumerates important choices that change the route's economy:
12F shop buys and optional late resource detours.  It is not a replacement for
full per-tile search, but it is fast, reproducible, and catches the meaningful
branch points that showed up during guide replay auditing.
"""

from __future__ import annotations

import itertools
import json
import os
import sys
import argparse
import time
from copy import deepcopy
from typing import Any

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.chdir(ROOT)

from scripts import replay_zone2_guide_route as zone2  # noqa: E402
from scripts import zone2_resource_groups as rg2  # noqa: E402


OPTION_KEYS = [
    "take_15_upper_blue_gem",
    "take_12_lower_left_keys",
    "take_final_mt3",
    "take_final_mt9",
    "take_final_mt11_blue_potion",
    "take_final_mt15_right_blue_potion",
    "take_4f_blue_potion",
    "take_final_mt11_red_potion",
    "take_16_lower_left",
    "take_16_upper_left",
    "take_mt17_right_red_potion_early",
    "take_final_mt17_right_red_potion",
    "take_pre_cross_mt17_red_gem",
    "take_pre_cross_mt17_blue_gem",
    "take_pre_cross_mt17_blue_potion",
    "take_pre_cross_mt18_before_mt12_key",
    "take_pre_cross_mt18_red_gem",
    "take_final_mt18_right_blue_gem",
    "take_final_mt20_right_potions",
    "take_final_mt14_top_blue_gem",
    "take_pre_cross_mt11_blue_potion",
    "take_mt16_right_blue_key",
    "take_super_potion16",
    "use_super_potion",
    "delay_mt11_shield",
]

DEFAULT_OPTIONS = {
    "take_15_upper_blue_gem": True,
    "take_12_lower_left_keys": True,
    "take_final_mt3": True,
    "talk_mt6_oldman": False,
    "take_final_mt9": True,
    "take_final_mt11_blue_potion": True,
    "take_final_mt15_right_blue_potion": False,
    "take_4f_blue_potion": True,
    "take_final_mt11_red_potion": True,
    "take_16_lower_left": True,
    "take_16_upper_left": True,
    "take_mt17_right_red_potion_early": True,
    "take_final_mt17_right_red_potion": False,
    "take_pre_cross_mt17_red_gem": False,
    "take_pre_cross_mt17_blue_gem": False,
    "take_pre_cross_mt17_blue_potion": False,
    "take_pre_cross_mt18_before_mt12_key": False,
    "take_pre_cross_mt18_red_gem": False,
    "take_final_mt18_right_blue_gem": False,
    "take_final_mt20_right_potions": False,
    "take_final_mt14_top_blue_gem": False,
    "take_pre_cross_mt11_blue_potion": False,
    "take_mt16_right_blue_key": False,
    "take_super_potion16": False,
    "use_super_potion": True,
    "delay_mt11_shield": False,
}


def base_stock_score(final: dict[str, Any]) -> float:
    return final["hp"] + final["yk"] * rg2.YK_VALUE + final["bk"] * rg2.BK_VALUE + final["gold"] * 0.5


def shop_buy_count(options: dict[str, Any]) -> int:
    return len(options.get("shop12", []))


def stat_buy_count(options: dict[str, Any]) -> int:
    return sum(1 for choice in options.get("shop12", []) if choice in {"atk", "def"})


def route_valid(result: dict[str, Any]) -> bool:
    final = result["final"]
    return (
        not result["errors"]
        and final["hp"] > 0
        and final["floor"] == "MT20"
        and final["x"] == 6
        and final["y"] == 6
        and final["rk"] == 0
        and final["cross"]
    )


def option_space(full: bool = False) -> list[dict[str, Any]]:
    by_key: dict[str, dict[str, Any]] = {}
    default_bits = dict(DEFAULT_OPTIONS)
    shop_choices: list[tuple[str, ...]] = []
    for count in (2, 3, 4):
        shop_choices.extend(itertools.product(["atk", "def", "hp"], repeat=count))

    if full:
        for shop12 in shop_choices:
            for bits in itertools.product([False, True], repeat=len(OPTION_KEYS)):
                opts = dict(default_bits)
                opts["shop12"] = list(shop12)
                opts.update(dict(zip(OPTION_KEYS, bits)))
                by_key[json.dumps(opts, sort_keys=True)] = opts
        return list(by_key.values())

    # Probe every shop combination once using the guide's resource plan.
    for shop12 in shop_choices:
        opts = {"shop12": list(shop12)}
        opts.update(default_bits)
        by_key[json.dumps(opts, sort_keys=True)] = opts

    # Expand late-resource choices only for shop plans that preserve the guide's
    # key tactical feature: at least three attack buys by the time the route
    # starts fighting big bats and red priests.
    expanded_shops = [
        shop12
        for shop12 in shop_choices
        if len(shop12) >= 3 and sum(1 for choice in shop12 if choice == "atk") >= 3
    ]
    expanded_shops.append(("atk", "atk", "atk"))
    for shop12 in expanded_shops:
        for bits in itertools.product([False, True], repeat=len(OPTION_KEYS)):
            opts = dict(default_bits)
            opts["shop12"] = list(shop12)
            opts.update(dict(zip(OPTION_KEYS, bits)))
            by_key[json.dumps(opts, sort_keys=True)] = opts
    return list(by_key.values())


def replay_candidate(
    label: str,
    state: dict[str, Any],
    cleared: dict[str, set[tuple[int, int]]],
    floors: dict[str, zone2.Floor],
    enemies: dict[str, dict[str, Any]],
    options: dict[str, Any],
) -> dict[str, Any]:
    rep = zone2.Replay(label, deepcopy(state), clone_floors(floors), enemies, deepcopy(cleared))
    result = zone2.run_route_direct(rep, options)
    result["options"] = options
    final = result["final"]
    result["base_stock_score"] = base_stock_score(final)
    result["remaining_group_value"] = rg2.remaining_resource_value(rep, enemies, final)
    result["composite_score"] = result["base_stock_score"] + result["remaining_group_value"]
    result["stock_score"] = result["composite_score"]
    result["shop_buy_count"] = shop_buy_count(options)
    result["stat_buy_count"] = stat_buy_count(options)
    return result


def clone_floors(floors: dict[str, zone2.Floor]) -> dict[str, zone2.Floor]:
    """Clone mutable floor blocks while sharing static grids for fast replay."""
    return {
        fid: zone2.Floor(
            fid=floor.fid,
            width=floor.width,
            height=floor.height,
            ratio=floor.ratio,
            grid=floor.grid,
            blocks=dict(floor.blocks),
        )
        for fid, floor in floors.items()
    }


def compact_result(result: dict[str, Any]) -> dict[str, Any]:
    final = result["final"]
    return {
        "label": result["label"],
        "final": final,
        "base_stock_score": result["base_stock_score"],
        "remaining_group_value": result["remaining_group_value"],
        "composite_score": result["composite_score"],
        "stock_score": result["stock_score"],
        "shop_buy_count": result["shop_buy_count"],
        "stat_buy_count": result["stat_buy_count"],
        "errors": len(result["errors"]),
        "warnings": len(result["warnings"]),
        "options": result["options"],
    }


def best_by(rows: list[dict[str, Any]], key: str) -> dict[str, Any] | None:
    if not rows:
        return None
    if key == "score":
        return max(rows, key=lambda r: (r["composite_score"], r["final"]["hp"], r["final"]["gold"]))
    if key == "min_shop":
        return min(rows, key=lambda r: (r["shop_buy_count"], r["stat_buy_count"], -r["composite_score"], -r["final"]["hp"], -r["final"]["gold"]))
    raise ValueError(key)


def write_walk(lines: list[str], result: dict[str, Any]) -> None:
    final = result["final"]
    lines.append(f"## {result['label']}")
    lines.append("")
    lines.append(
        f"- 最终状态：{zone2.state_text(final)} dmg={final['dmg']} "
        f"door={final['yd']}/{final['bd']}/{final['rd']} 综合评分={result['composite_score']:.1f} "
        f"商店购买={result['shop_buy_count']} 攻防购买={result['stat_buy_count']}"
    )
    lines.append(f"- 选项：`{json.dumps(result['options'], ensure_ascii=False, sort_keys=True)}`")
    lines.append("")
    grouped: dict[str, list[dict[str, Any]]] = {}
    for step in result["steps"]:
        grouped.setdefault(step["segment"], []).append(step)
    for seg in result["segments"]:
        lines.append(f"### {seg['name']}")
        lines.append("")
        for step in grouped.get(seg["name"], []):
            lines.append(zone2.step_line(step))
        lines.append("")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true", help="Enumerate all shop and late-resource combinations.")
    parser.add_argument("--suffix", default="", help="Suffix for output filenames.")
    parser.add_argument("--progress-every", type=int, default=0, help="Print progress every N candidates per scenario.")
    parser.add_argument("--yk-value", type=int, default=50, help="Score value of one yellow key in HP units.")
    args = parser.parse_args()
    rg2.YK_VALUE = args.yk_value
    rg2.BK_VALUE = args.yk_value * 4

    floors, enemies = zone2.load_floors()
    options = option_space(full=args.full)
    os.makedirs(os.path.join("outputs", "results"), exist_ok=True)
    os.makedirs(os.path.join("outputs", "reports"), exist_ok=True)
    os.makedirs(os.path.join("outputs", "walkthroughs"), exist_ok=True)

    all_outputs: dict[str, Any] = {"config": {"candidate_count": len(options)}, "scenarios": {}}
    report = [
        "# 二区宏策略搜索",
        "",
        f"`综合评分` = 当前 HP/钥匙/金币库存 + 剩余资源组净值。本次 `1黄钥匙={rg2.YK_VALUE}HP`。剩余怪物按未来金币收入计入，"
        "未开黄/蓝门按钥匙价值扣除，16F 圣水按当前攻防下界计入。",
        "",
    ]
    walk_lines = ["# 二区宏策略搜索最佳 Walk", ""]

    for label, state, cleared in zone2.scenario_states():
        valid: list[dict[str, Any]] = []
        invalid = 0
        started = time.time()
        for idx, opts in enumerate(options, 1):
            result = replay_candidate(label, state, cleared, floors, enemies, opts)
            if route_valid(result):
                valid.append(result)
            else:
                invalid += 1
            if args.progress_every and idx % args.progress_every == 0:
                elapsed = time.time() - started
                rate = idx / elapsed if elapsed > 0 else 0
                print(
                    f"{label}: {idx}/{len(options)} 有效={len(valid)} 无效={invalid} "
                    f"速度={rate:.1f}/s",
                    flush=True,
                )

        score_best = best_by(valid, "score")
        min_shop_best = best_by(valid, "min_shop")
        top_score = sorted(valid, key=lambda r: (r["composite_score"], r["final"]["hp"]), reverse=True)[:20]
        top_min_shop = sorted(valid, key=lambda r: (r["shop_buy_count"], r["stat_buy_count"], -r["composite_score"], -r["final"]["hp"]))[:20]

        all_outputs["scenarios"][label] = {
            "valid_count": len(valid),
            "invalid_count": invalid,
            "score_best": compact_result(score_best) if score_best else None,
            "min_shop_best": compact_result(min_shop_best) if min_shop_best else None,
            "stock_best": compact_result(score_best) if score_best else None,
            "top_score": [compact_result(r) for r in top_score],
            "top_min_shop": [compact_result(r) for r in top_min_shop],
        }

        report.append(f"## {label}")
        report.append("")
        report.append(f"- 有效候选：`{len(valid)}` / `{len(options)}`")
        report.append(f"- 无效候选：`{invalid}`")
        if score_best:
            f = score_best["final"]
            report.append(
                f"- 综合评分最优：`{zone2.state_text(f)}` 综合评分=`{score_best['composite_score']:.1f}` "
                f"剩余资源组=`{score_best['remaining_group_value']:.1f}` "
                f"商店购买=`{score_best['shop_buy_count']}` 攻防购买=`{score_best['stat_buy_count']}` "
                f"选项=`{json.dumps(score_best['options'], ensure_ascii=False, sort_keys=True)}`"
            )
            score_best["label"] = f"{label}:score_best"
            write_walk(walk_lines, score_best)
        if min_shop_best and min_shop_best is not score_best:
            f = min_shop_best["final"]
            report.append(
                f"- 最少商店购买最优：`{zone2.state_text(f)}` 综合评分=`{min_shop_best['composite_score']:.1f}` "
                f"剩余资源组=`{min_shop_best['remaining_group_value']:.1f}` "
                f"商店购买=`{min_shop_best['shop_buy_count']}` 攻防购买=`{min_shop_best['stat_buy_count']}` "
                f"选项=`{json.dumps(min_shop_best['options'], ensure_ascii=False, sort_keys=True)}`"
            )
            min_shop_best["label"] = f"{label}:min_shop_best"
            write_walk(walk_lines, min_shop_best)
        elif min_shop_best:
            f = min_shop_best["final"]
            report.append(f"- 最少商店购买最优：同综合评分最优，`{zone2.state_text(f)}`")
        report.append("")

    suffix = f"_{args.suffix}" if args.suffix else ""
    out_json = os.path.join("outputs", "results", f"zone2_macro_search{suffix}.json")
    out_md = os.path.join("outputs", "reports", f"zone2_macro_search{suffix}.md")
    out_walk = os.path.join("outputs", "walkthroughs", f"walkthrough_zone2_macro_search_best{suffix}.md")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(all_outputs, f, ensure_ascii=False, indent=2)
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(report).rstrip() + "\n")
    with open(out_walk, "w", encoding="utf-8") as f:
        f.write("\n".join(walk_lines).rstrip() + "\n")

    print(f"已写入 {out_json}")
    print(f"已写入 {out_md}")
    print(f"已写入 {out_walk}")
    for label, data in all_outputs["scenarios"].items():
        score = data["score_best"]
        min_shop = data["min_shop_best"]
        print(f"{label}: 有效={data['valid_count']} 无效={data['invalid_count']}")
        if score:
            f = score["final"]
            print(f"  综合评分最优 {zone2.state_text(f)} score={score['composite_score']:.1f}")
        if min_shop and min_shop != score:
            f = min_shop["final"]
            print(f"  最少商店购买最优 {zone2.state_text(f)} score={min_shop['composite_score']:.1f} shop={min_shop['shop_buy_count']}")


if __name__ == "__main__":
    main()
