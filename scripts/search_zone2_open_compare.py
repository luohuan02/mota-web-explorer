#!/usr/bin/env python3
"""Open-ish local strategy comparison for zone 2.

This is still not a full tile-by-tile global solver.  It expands the macro
replay into a wider local search by enumerating important order swaps and
delayed-resource decisions, then scores every valid candidate under multiple
yellow-key values.
"""

from __future__ import annotations

import argparse
import itertools
import json
import os
import sys
import time
from copy import deepcopy
from typing import Any


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.chdir(ROOT)

from scripts import replay_zone2_guide_route as zone2  # noqa: E402
from scripts import search_zone2_macro_routes as macro  # noqa: E402
from scripts import zone2_resource_groups as rg2  # noqa: E402


PROFILES = {
    "3攻": [("atk", "atk", "atk")],
    "2攻1防": sorted(set(itertools.permutations(("atk", "atk", "def"), 3))),
}

CORE_KEYS = [
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
    "take_pre_cross_mt18_before_mt12_key",
    "take_pre_cross_mt18_red_gem",
    "take_pre_cross_mt11_blue_potion",
    "take_mt16_right_blue_key",
]

EXTRA_KEYS = [
    "take_pre_cross_mt17_red_gem",
    "take_pre_cross_mt17_blue_gem",
    "take_pre_cross_mt17_blue_potion",
    "take_final_mt18_right_blue_gem",
    "take_final_mt20_right_potions",
    "take_final_mt14_top_blue_gem",
    "delay_mt11_shield",
]


def parse_yk_values(raw: str) -> list[int]:
    out = []
    for part in raw.split(","):
        part = part.strip()
        if part:
            out.append(int(part))
    return out or [50, 100]


def base_stock_score(final: dict[str, Any], yk_value: int) -> float:
    return final["hp"] + final["yk"] * yk_value + final["bk"] * yk_value * 4 + final["gold"] * 0.5


def score_with_yk(
    rep: zone2.Replay,
    enemies: dict[str, dict[str, Any]],
    final: dict[str, Any],
    yk_value: int,
) -> tuple[float, float, float]:
    rg2.YK_VALUE = yk_value
    rg2.BK_VALUE = yk_value * 4
    base = base_stock_score(final, yk_value)
    remaining = rg2.remaining_resource_value(rep, enemies, final)
    return base + remaining, base, remaining


def better(a: dict[str, Any] | None, b: dict[str, Any]) -> bool:
    if a is None:
        return True
    af = a["final"]
    bf = b["final"]
    return (b["composite_score"], bf["hp"], bf["gold"], bf["yk"], bf["bk"]) > (
        a["composite_score"],
        af["hp"],
        af["gold"],
        af["yk"],
        af["bk"],
    )


def replay_once(
    label: str,
    state: dict[str, Any],
    cleared: dict[str, set[tuple[int, int]]],
    floors: dict[str, zone2.Floor],
    enemies: dict[str, dict[str, Any]],
    options: dict[str, Any],
) -> tuple[zone2.Replay, dict[str, Any]]:
    rep = zone2.Replay(label, deepcopy(state), macro.clone_floors(floors), enemies, deepcopy(cleared))
    result = zone2.run_route_direct(rep, options)
    return rep, result


def compact(result: dict[str, Any], options: dict[str, Any], score: float, base: float, remaining: float) -> dict[str, Any]:
    final = result["final"]
    return {
        "label": result["label"],
        "final": final,
        "base_stock_score": base,
        "remaining_group_value": remaining,
        "composite_score": score,
        "shop_buy_count": len(options.get("shop12", [])),
        "stat_buy_count": sum(1 for c in options.get("shop12", []) if c in {"atk", "def"}),
        "options": options,
        "errors": len(result["errors"]),
        "warnings": len(result["warnings"]),
    }


def candidate_options(profile: str, shop: tuple[str, ...], bits: tuple[bool, ...]) -> dict[str, Any]:
    opts = dict(macro.DEFAULT_OPTIONS)
    opts["shop12"] = list(shop)
    opts.update(dict(zip(CORE_KEYS, bits)))

    # Keep the wider but expensive branches off in the core pass.  They are
    # valuable for proving nearby boundaries, but so far only create costly
    # detours for the 2攻1防/3攻 comparison.
    for key in EXTRA_KEYS:
        opts[key] = False

    opts["take_super_potion16"] = False
    opts["use_super_potion"] = False
    opts["talk_mt6_oldman"] = False

    if profile == "2攻1防":
        # Known required tactical supports are left enumerable except the
        # attack-threshold resource itself, which otherwise wastes most of the
        # core pass on impossible candidates.
        opts["take_pre_cross_mt18_red_gem"] = True
    return opts


def write_outputs(
    summary: dict[str, Any],
    best_full: dict[tuple[str, str, int], dict[str, Any]],
    yk_values: list[int],
    suffix: str,
) -> None:
    os.makedirs(os.path.join("outputs", "results"), exist_ok=True)
    os.makedirs(os.path.join("outputs", "reports"), exist_ok=True)
    os.makedirs(os.path.join("outputs", "walkthroughs"), exist_ok=True)

    json_path = os.path.join("outputs", "results", f"zone2_open_compare{suffix}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    lines = ["# 二区开放局部策略比较", ""]
    lines.append(
        "本轮不是完整逐格全局搜索；它在攻略宏骨架上开放关键交换和延后资源："
        "`18F 红宝石/12F 蓝钥匙顺序`、`MT17 右下红血瓶早晚`、低成本血瓶/钥匙/宝石开关等。"
    )
    lines.append("")
    lines.append(
        f"- 已评估候选：`{summary['evaluated']}`，有效：`{summary['valid']}`，"
        f"耗时：`{summary['elapsed_seconds']:.1f}s`，是否耗尽搜索空间：`{summary['exhausted']}`"
    )
    lines.append(f"- YK 价值：`{', '.join(map(str, yk_values))}`")
    lines.append("")

    for scenario in summary["scenarios"]:
        lines.append(f"## {scenario}")
        lines.append("")
        lines.append("| YK价值 | 路线族 | 最佳终态 | dmg | 门 黄/蓝/红 | 综合评分 | 关键选项 |")
        lines.append("|---:|---|---|---:|---:|---:|---|")
        for yk in yk_values:
            for profile in PROFILES:
                row = summary["best"].get(scenario, {}).get(profile, {}).get(str(yk))
                if not row:
                    lines.append(f"| {yk} | {profile} | 无有效候选 |  |  |  |  |")
                    continue
                final = row["final"]
                state = (
                    f"HP={final['hp']} ATK={final['atk']} DEF={final['def']} "
                    f"YK={final['yk']} BK={final['bk']} RK={final['rk']} G={final['gold']}"
                )
                opts = row["options"]
                key_opts = {
                    "shop12": opts.get("shop12"),
                    "18F先于12F": opts.get("take_pre_cross_mt18_before_mt12_key"),
                    "MT17红瓶早拿": opts.get("take_mt17_right_red_potion_early"),
                    "MT17红瓶晚拿": opts.get("take_final_mt17_right_red_potion"),
                    "15F右蓝瓶": opts.get("take_final_mt15_right_blue_potion"),
                    "16F右蓝钥匙": opts.get("take_mt16_right_blue_key"),
                }
                lines.append(
                    f"| {yk} | {profile} | {state} | {final['dmg']} | "
                    f"{final['yd']}/{final['bd']}/{final['rd']} | {row['composite_score']:.1f} | "
                    f"`{json.dumps(key_opts, ensure_ascii=False)}` |"
                )
        lines.append("")

    report_path = os.path.join("outputs", "reports", f"zone2_open_compare{suffix}.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")

    walk_lines = ["# 二区开放局部策略最佳 Walk", ""]
    for key, full in best_full.items():
        scenario, profile, yk = key
        result = full["result"]
        result["options"] = full["options"]
        result["base_stock_score"] = full["base_stock_score"]
        result["remaining_group_value"] = full["remaining_group_value"]
        result["composite_score"] = full["composite_score"]
        result["shop_buy_count"] = len(full["options"].get("shop12", []))
        result["stat_buy_count"] = sum(1 for c in full["options"].get("shop12", []) if c in {"atk", "def"})
        result["label"] = f"{scenario}:{profile}:YK{yk}"
        macro.write_walk(walk_lines, result)
    walk_path = os.path.join("outputs", "walkthroughs", f"walkthrough_zone2_open_compare{suffix}.md")
    with open(walk_path, "w", encoding="utf-8") as f:
        f.write("\n".join(walk_lines).rstrip() + "\n")

    print(f"已写入 {json_path}")
    print(f"已写入 {report_path}")
    print(f"已写入 {walk_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seconds", type=float, default=9000.0)
    parser.add_argument("--yk-values", default="50,100")
    parser.add_argument("--suffix", default="")
    parser.add_argument("--progress-every", type=int, default=5000)
    args = parser.parse_args()

    yk_values = parse_yk_values(args.yk_values)
    suffix = f"_{args.suffix}" if args.suffix and not args.suffix.startswith("_") else args.suffix
    floors, enemies = zone2.load_floors()
    scenarios = zone2.scenario_states()

    best: dict[str, dict[str, dict[str, dict[str, Any]]]] = {}
    best_full: dict[tuple[str, str, int], dict[str, Any]] = {}
    evaluated = 0
    valid = 0
    invalid = 0
    started = time.time()
    deadline = started + args.seconds
    exhausted = True

    total_core = len(scenarios) * sum(len(shops) for shops in PROFILES.values()) * (2 ** len(CORE_KEYS))
    print(f"核心候选空间约 {total_core}，限时 {args.seconds:.0f}s", flush=True)

    for scenario_label, state, cleared in scenarios:
        best.setdefault(scenario_label, {})
        for profile, shops in PROFILES.items():
            best[scenario_label].setdefault(profile, {})
            for shop in shops:
                for bits in itertools.product([False, True], repeat=len(CORE_KEYS)):
                    if time.time() >= deadline:
                        exhausted = False
                        break
                    opts = candidate_options(profile, shop, bits)
                    rep, result = replay_once(scenario_label, state, cleared, floors, enemies, opts)
                    evaluated += 1
                    if macro.route_valid(result):
                        valid += 1
                        for yk in yk_values:
                            score, base, remaining = score_with_yk(rep, enemies, result["final"], yk)
                            row = compact(result, opts, score, base, remaining)
                            cur = best[scenario_label][profile].get(str(yk))
                            if better(cur, row):
                                best[scenario_label][profile][str(yk)] = row
                                best_full[(scenario_label, profile, yk)] = {
                                    "result": deepcopy(result),
                                    "options": deepcopy(opts),
                                    "base_stock_score": base,
                                    "remaining_group_value": remaining,
                                    "composite_score": score,
                                }
                    else:
                        invalid += 1
                    if args.progress_every and evaluated % args.progress_every == 0:
                        elapsed = time.time() - started
                        rate = evaluated / elapsed if elapsed > 0 else 0.0
                        print(
                            f"进度 evaluated={evaluated} valid={valid} invalid={invalid} "
                            f"rate={rate:.1f}/s elapsed={elapsed:.1f}s",
                            flush=True,
                        )
                if not exhausted:
                    break
            if not exhausted:
                break
        if not exhausted:
            break

    elapsed = time.time() - started
    summary = {
        "config": {
            "core_keys": CORE_KEYS,
            "extra_keys_disabled_in_core": EXTRA_KEYS,
            "profiles": {k: [list(x) for x in v] for k, v in PROFILES.items()},
            "yk_values": yk_values,
            "seconds_limit": args.seconds,
            "estimated_core_candidates": total_core,
        },
        "scenarios": [s[0] for s in scenarios],
        "evaluated": evaluated,
        "valid": valid,
        "invalid": invalid,
        "elapsed_seconds": elapsed,
        "exhausted": exhausted,
        "best": best,
    }
    write_outputs(summary, best_full, yk_values, suffix)


if __name__ == "__main__":
    main()
