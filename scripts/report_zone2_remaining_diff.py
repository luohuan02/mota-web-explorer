#!/usr/bin/env python3
"""Compare remaining resource groups for selected zone-2 routes."""

from __future__ import annotations

import json
import os
import sys
from copy import deepcopy
from typing import Any

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.chdir(ROOT)

from scripts import replay_zone2_guide_route as zone2  # noqa: E402
from scripts import zone2_resource_groups as rg2  # noqa: E402


DEFAULT_GUIDE_OPTIONS = {
    "shop12": ["atk", "atk", "atk"],
    "take_15_upper_blue_gem": True,
    "take_12_lower_left_keys": True,
    "take_final_mt3": True,
    "talk_mt6_oldman": False,
    "take_final_mt9": True,
    "take_final_mt11_blue_potion": True,
    "take_mt19_x3y8": True,
    "take_4f_blue_potion": True,
    "take_final_mt11_red_potion": True,
    "take_16_lower_left": True,
    "take_super_potion16": False,
    "use_super_potion": True,
}

LABEL_CN = {
    "guide_correct": "攻略复现",
    "guide_score_best": "攻略起点综合评分最优",
    "guide_min_shop_best": "攻略起点最少商店购买最优",
    "best_score_best": "当前最优起点综合评分最优",
    "best_min_shop_best": "当前最优起点最少商店购买最优",
}


def load_macro_options() -> dict[str, dict[str, Any]]:
    path = os.path.join("outputs", "results", "zone2_macro_search.json")
    data = json.load(open(path, encoding="utf-8"))
    return {
        "guide_score_best": data["scenarios"]["guide_after_mt10_boss_supply"]["score_best"]["options"],
        "guide_min_shop_best": data["scenarios"]["guide_after_mt10_boss_supply"]["min_shop_best"]["options"],
        "best_score_best": data["scenarios"]["best_after_mt10_boss_supply"]["score_best"]["options"],
        "best_min_shop_best": data["scenarios"]["best_after_mt10_boss_supply"]["min_shop_best"]["options"],
    }


def clone_floors(floors: dict[str, zone2.Floor]) -> dict[str, zone2.Floor]:
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


def replay_named(
    label: str,
    scenario_label: str,
    options: dict[str, Any],
    floors: dict[str, zone2.Floor],
    enemies: dict[str, dict[str, Any]],
    scenarios: dict[str, tuple[dict[str, Any], dict[str, set[tuple[int, int]]]]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    state, cleared = scenarios[scenario_label]
    rep = zone2.Replay(label, deepcopy(state), clone_floors(floors), enemies, deepcopy(cleared))
    result = zone2.run_route_direct(rep, options)
    result["label"] = label
    result["options"] = options
    groups = rg2.remaining_resource_groups(rep, enemies, result["final"])
    return result, groups


def base_stock(final: dict[str, Any]) -> float:
    return final["hp"] + final["yk"] * 50 + final["bk"] * 200 + final["gold"] * 0.5


def shop_buy_count(options: dict[str, Any]) -> int:
    return len(options.get("shop12", []))


def stat_buy_count(options: dict[str, Any]) -> int:
    return sum(1 for choice in options.get("shop12", []) if choice in {"atk", "def"})


def group_value(groups: list[dict[str, Any]]) -> float:
    return sum(row["value"] for row in groups)


def format_final(result: dict[str, Any], groups: list[dict[str, Any]]) -> str:
    f = result["final"]
    score = base_stock(f) + group_value(groups)
    return (
        f"{zone2.state_text(f)} dmg={f['dmg']} door={f['yd']}/{f['bd']}/{f['rd']} "
        f"综合评分={score:.1f} 剩余资源组={group_value(groups):.1f} "
        f"商店购买={shop_buy_count(result['options'])} 攻防购买={stat_buy_count(result['options'])}"
    )


def format_group(row: dict[str, Any]) -> str:
    parts = []
    for item in row.get("items", []):
        parts.append(f"{item['pos']} {zone2.ITEM_CN.get(item['eid'], item['eid'])}={item['value']}")
    for monster in row.get("monsters", []):
        parts.append(f"{monster['pos']} {zone2.ITEM_CN.get(monster['eid'], monster['eid'])}金币={monster['gold_value']}")
    for door in row.get("doors", []):
        parts.append(f"扣{door['pos']} {zone2.ITEM_CN.get(door['eid'], door['eid'])}={door['cost']}")
    detail = "；".join(parts)
    return f"{row['group']}，净值={row['value']:.1f}" + (f"（{detail}）" if detail else "")


def main() -> None:
    floors, enemies = zone2.load_floors()
    scenario_rows = {label: (state, cleared) for label, state, cleared in zone2.scenario_states()}
    macro_options = load_macro_options()
    selected = [
        ("guide_correct", "guide_after_mt10_boss_supply", DEFAULT_GUIDE_OPTIONS),
        ("guide_score_best", "guide_after_mt10_boss_supply", macro_options["guide_score_best"]),
        ("guide_min_shop_best", "guide_after_mt10_boss_supply", macro_options["guide_min_shop_best"]),
        ("best_score_best", "best_after_mt10_boss_supply", macro_options["best_score_best"]),
        ("best_min_shop_best", "best_after_mt10_boss_supply", macro_options["best_min_shop_best"]),
    ]

    results: dict[str, dict[str, Any]] = {}
    remaining: dict[str, dict[str, dict[str, Any]]] = {}
    for label, scenario_label, options in selected:
        result, groups = replay_named(label, scenario_label, options, floors, enemies, scenario_rows)
        results[label] = result
        remaining[label] = {row["key"]: row for row in groups}

    labels = [label for label, _scenario, _opts in selected]
    all_keys = sorted(set().union(*(set(remaining[label]) for label in labels)))
    diff_keys = [
        key
        for key in all_keys
        if len({key in remaining[label] for label in labels}) > 1
    ]

    os.makedirs(os.path.join("outputs", "reports"), exist_ok=True)
    os.makedirs(os.path.join("outputs", "results"), exist_ok=True)
    out_json = os.path.join("outputs", "results", "zone2_remaining_diff.json")
    out_md = os.path.join("outputs", "reports", "zone2_remaining_diff.md")

    payload = {
        "routes": {
            label: {
                "final": results[label]["final"],
                "options": results[label]["options"],
                "remaining_group_value": group_value(list(remaining[label].values())),
                "composite_score": base_stock(results[label]["final"]) + group_value(list(remaining[label].values())),
            }
            for label in labels
        },
        "diffs": [
            {
                "group": key,
                "remaining_in": [label for label in labels if key in remaining[label]],
                "remaining_in_cn": [LABEL_CN.get(label, label) for label in labels if key in remaining[label]],
                "sample": next(remaining[label][key] for label in labels if key in remaining[label]),
            }
            for key in diff_keys
        ],
    }
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    lines = ["# 二区剩余资源组差异", ""]
    lines.append("## 路线")
    lines.append("")
    for label in labels:
        lines.append(f"- {LABEL_CN.get(label, label)}（`{label}`）：{format_final(results[label], list(remaining[label].values()))}")
    lines.append("")
    lines.append("## 只列差异")
    lines.append("")
    lines.append("| 资源组 | 哪些线路还剩 |")
    lines.append("|---|---|")
    for key in diff_keys:
        entry = next(remaining[label][key] for label in labels if key in remaining[label])
        present = ", ".join(f"{LABEL_CN.get(label, label)}（`{label}`）" for label in labels if key in remaining[label])
        lines.append(f"| {format_group(entry)} | {present} |")
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")

    print(f"已写入 {out_json}")
    print(f"已写入 {out_md}")
    for label in labels:
        print(f"{label}: {format_final(results[label], list(remaining[label].values()))}")
    print(f"差异资源组数量: {len(diff_keys)}")


if __name__ == "__main__":
    main()
