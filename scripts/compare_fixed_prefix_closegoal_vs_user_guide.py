#!/usr/bin/env python3
"""Compare the fixed-prefix close-goal improvement against the user guide."""

from __future__ import annotations

import json
import os
import sys
from collections import Counter, defaultdict
from typing import Any


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.chdir(ROOT)

from scripts import compare_delayed_phase1_vs_user_guide as base
from scripts import post9_resource_group_search as rg
from src.solver.full_search import FLOOR_13_COLLECTED, load_data


NEW_FINAL_CACHE = os.path.join("outputs", "results", "fixed_prefix_strict_improve_closegoal_final_cache.json")
OUT_JSON = os.path.join("outputs", "results", "fixed_prefix_closegoal_vs_user_guide_resource_diff.json")
OUT_MD = os.path.join("outputs", "reports", "fixed_prefix_closegoal_vs_user_guide_resource_diff.md")

RESOURCE_IDS = {
    "yellowKey",
    "blueKey",
    "redKey",
    "redPotion",
    "bluePotion",
    "redGem",
    "blueGem",
    "greenGem",
    "sword1",
    "shield1",
}

ITEM_CN = {
    "yellowKey": "黄钥匙",
    "blueKey": "蓝钥匙",
    "redKey": "红钥匙",
    "redPotion": "红血瓶",
    "bluePotion": "蓝血瓶",
    "redGem": "红宝石",
    "blueGem": "蓝宝石",
    "greenGem": "绿宝石",
    "sword1": "铁剑",
    "shield1": "铁盾",
}

RAW_ITEM_VALUE = {
    "yellowKey": 50,
    "blueKey": 200,
    "redKey": 0,
    "redPotion": 50,
    "bluePotion": 200,
    "redGem": 0,
    "blueGem": 0,
    "greenGem": 0,
    "sword1": 0,
    "shield1": 0,
}


def all_resources(maps: dict[str, Any]) -> dict[tuple[str, int, int], str]:
    out: dict[tuple[str, int, int], str] = {}
    for fid, data in maps.items():
        precollected = FLOOR_13_COLLECTED.get(fid, frozenset())
        for x, y, t, eid in data["bl"]:
            if t == 3 and eid in RESOURCE_IDS and (x, y) not in precollected:
                out[(fid, x, y)] = eid
    return out


def floor_key(fid: str) -> int:
    return int(fid[2:])


def state_row(row: dict[str, Any]) -> dict[str, int]:
    return {key: int(row[key]) for key in ("hp", "atk", "def", "yk", "bk", "rk", "dmg", "yd", "bd", "rd")}


def state_text(row: dict[str, int]) -> str:
    return (
        f"HP={row['hp']} ATK={row['atk']} DEF={row['def']} "
        f"YK={row['yk']} BK={row['bk']} RK={row['rk']} "
        f"dmg={row['dmg']} door={row['yd']}/{row['bd']}/{row['rd']}"
    )


def collected_from_row(row: dict[str, Any]) -> dict[str, set[tuple[int, int]]]:
    return {
        fid: {tuple(pos) for pos in positions}
        for fid, positions in row.get("collected", {}).items()
    }


def score_ent(row: dict[str, int], collected: dict[str, set[tuple[int, int]]]) -> dict[str, Any]:
    return {
        "hp": row["hp"],
        "atk": row["atk"],
        "def": row["def"],
        "yk": row["yk"],
        "bk": row["bk"],
        "rk": row["rk"],
        "_dmg": row["dmg"],
        "_yd": row["yd"],
        "_bd": row["bd"],
        "_rd": row["rd"],
        "collected": {fid: frozenset(pos) for fid, pos in collected.items()},
    }


def best_closegoal_row() -> dict[str, Any]:
    with open(NEW_FINAL_CACHE, encoding="utf-8") as f:
        data = json.load(f)
    goals = [
        row
        for row in data["stages"]["boss"]["entries"]
        if row.get("rk") == 0 and row.get("rd") == 1 and row.get("dmg", 10**9) < 2601
    ]
    if not goals:
        raise RuntimeError(f"No strict-improve boss goal in {NEW_FINAL_CACHE}")
    return min(goals, key=lambda row: (row["dmg"], -row["hp"], row["yd"], row["bd"]))


def remaining_resources(
    resources: dict[tuple[str, int, int], str],
    collected: dict[str, set[tuple[int, int]]],
) -> dict[tuple[str, int, int], str]:
    return {
        key: eid
        for key, eid in resources.items()
        if (key[1], key[2]) not in collected.get(key[0], set())
    }


def count_remaining(
    resources: dict[tuple[str, int, int], str],
    collected: dict[str, set[tuple[int, int]]],
) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for (_fid, x, y), eid in resources.items():
        if (x, y) not in collected.get(_fid, set()):
            counter[eid] += 1
    return dict(counter)


def raw_remaining_value(
    resources: dict[tuple[str, int, int], str],
    collected: dict[str, set[tuple[int, int]]],
) -> int:
    total = 0
    for (_fid, x, y), eid in resources.items():
        if (x, y) not in collected.get(_fid, set()):
            total += RAW_ITEM_VALUE.get(eid, 0)
    return total


def resource_diff(
    resources: dict[tuple[str, int, int], str],
    new_collected: dict[str, set[tuple[int, int]]],
    guide_collected: dict[str, set[tuple[int, int]]],
) -> dict[str, dict[str, list[dict[str, str]]]]:
    diff: dict[str, dict[str, list[dict[str, str]]]] = defaultdict(
        lambda: {"new_more_left": [], "guide_more_left": []}
    )
    new_left = remaining_resources(resources, new_collected)
    guide_left = remaining_resources(resources, guide_collected)
    for key, eid in sorted(resources.items(), key=lambda item: (floor_key(item[0][0]), item[0][1], item[0][2])):
        n_left = key in new_left
        g_left = key in guide_left
        if n_left == g_left:
            continue
        fid, x, y = key
        rec = {"pos": f"x{x}y{y}", "eid": eid, "name": ITEM_CN.get(eid, eid)}
        if n_left and not g_left:
            diff[fid]["new_more_left"].append(rec)
        elif g_left and not n_left:
            diff[fid]["guide_more_left"].append(rec)
    return {fid: diff[fid] for fid in sorted(diff, key=floor_key)}


def item_text(items: list[dict[str, str]]) -> str:
    if not items:
        return "-"
    return "；".join(f"{item['pos']} {item['name']} (`{item['eid']}`)" for item in items)


def enrich(row: dict[str, int], collected: dict[str, set[tuple[int, int]]], resources: dict[tuple[str, int, int], str]) -> dict[str, Any]:
    ent = score_ent(row, collected)
    final_residual, _notes = rg.residual_resource_value(ent, ignore_monster_damage=True)
    out: dict[str, Any] = dict(row)
    out.update(
        old_score=rg.old_score(ent),
        resource_group_score=rg.resource_group_score(ent),
        final_residual_value=final_residual,
        final_resource_stock=row["hp"] + row["yk"] * rg.YK_VALUE + row["bk"] * rg.BK_VALUE + final_residual,
        raw_remaining_value=raw_remaining_value(resources, collected),
        raw_final_stock=(
            row["hp"]
            + row["yk"] * rg.YK_VALUE
            + row["bk"] * rg.BK_VALUE
            + raw_remaining_value(resources, collected)
        ),
        remaining_counts=count_remaining(resources, collected),
    )
    return out


def write_report(data: dict[str, Any]) -> None:
    new = data["closegoal"]
    guide = data["guide"]
    delta = data["delta"]
    lines = [
        "# Fixed-prefix Close-goal vs User Guide",
        "",
        "## 状态对比",
        "",
        "| 路线 | 最终状态 | old_score | resource_group_score | final_residual_0dmg | final_stock |",
        "|---|---|---:|---:|---:|---:|",
        (
            f"| close-goal 新线 | {state_text(new)} | {new['old_score']} | "
            f"{new['resource_group_score']} | {new['final_residual_value']} | {new['final_resource_stock']} |"
        ),
        (
            f"| 攻略线 | {state_text(guide)} | {guide['old_score']} | "
            f"{guide['resource_group_score']} | {guide['final_residual_value']} | {guide['final_resource_stock']} |"
        ),
        "",
        "## 原始剩余资源口径",
        "",
        "`final_stock` 是资源组保守残余估值，不等于地图上全部剩余物资的直接价值。按黄钥匙 `50`、蓝钥匙 `200`、红/蓝血瓶 `50/200` 直接统计剩余物资：",
        "",
        "| 路线 | HP + 当前钥匙 | 地图剩余资源原始价值 | raw_final_stock |",
        "|---|---:|---:|---:|",
        f"| close-goal 新线 | {new['hp'] + new['yk'] * rg.YK_VALUE + new['bk'] * rg.BK_VALUE} | {new['raw_remaining_value']} | {new['raw_final_stock']} |",
        f"| 攻略线 | {guide['hp'] + guide['yk'] * rg.YK_VALUE + guide['bk'] * rg.BK_VALUE} | {guide['raw_remaining_value']} | {guide['raw_final_stock']} |",
        "",
        "## 状态差异",
        "",
        f"- HP：新线 `{new['hp']}`，攻略 `{guide['hp']}`，新线 `{delta['hp']:+d}`。",
        f"- dmg：新线 `{new['dmg']}`，攻略 `{guide['dmg']}`，新线 `{delta['dmg']:+d}`。",
        f"- 门耗：新线 `{new['yd']}/{new['bd']}/{new['rd']}`，攻略 `{guide['yd']}/{guide['bd']}/{guide['rd']}`，黄门 `{delta['yd']:+d}`，蓝门 `{delta['bd']:+d}`，红门 `{delta['rd']:+d}`。",
        f"- final_stock：新线 `{new['final_resource_stock']}`，攻略 `{guide['final_resource_stock']}`，新线 `{delta['final_resource_stock']:+d}`。",
        f"- raw_final_stock：新线 `{new['raw_final_stock']}`，攻略 `{guide['raw_final_stock']}`，新线 `{delta['raw_final_stock']:+d}`。",
        "",
        "## 剩余资源差异",
        "",
        "只列最终地图上剩余资源集合不同的楼层；两边都剩或两边都取的资源不列。",
        "",
        "| 楼层 | 新线多剩（攻略已取） | 攻略多剩（新线已取） |",
        "|---|---|---|",
    ]
    for fid, row in data["resource_diff"].items():
        lines.append(
            f"| {fid} | {item_text(row['new_more_left'])} | {item_text(row['guide_more_left'])} |"
        )
    lines.extend([
        "",
        "## 结论",
        "",
        "- 新线比攻略少 `4 dmg`，最终 HP 多 `4`，但多消耗 `1` 把黄钥匙。",
        "- 按地图剩余资源原始价值口径，新线保留 `MT1 x1y3 红血瓶`，攻略保留 `MT6 x9y1 黄钥匙` 和 `MT8 x1y5 红血瓶`；两个红血瓶相互抵消后，攻略多 `1` 把黄钥匙，即资源面多 `50`。",
        "- 因此若评价函数把剩余黄钥匙按 `50` 计入，攻略线 `raw_final_stock=1425`，新线 `raw_final_stock=1379`，攻略更优 `46`。`2597` 新线只是在纯 Boss 终点伤害 / HP 口径下严格优于攻略，不是资源调整口径下的最优。",
    ])
    os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")


def main() -> None:
    _hero, maps = load_data()
    resources = all_resources(maps)
    guide_collected = base.guide_collected(base.block_map(maps))
    guide_row = base.guide_final()
    new_snapshot = best_closegoal_row()
    new_row = state_row(new_snapshot)
    new_collected = collected_from_row(new_snapshot)

    new = enrich(new_row, new_collected, resources)
    guide = enrich(guide_row, guide_collected, resources)
    delta = {
        key: new[key] - guide[key]
        for key in (
            "hp",
            "atk",
            "def",
            "yk",
            "bk",
            "rk",
            "dmg",
            "yd",
            "bd",
            "rd",
            "final_resource_stock",
            "raw_remaining_value",
            "raw_final_stock",
        )
    }
    data = {
        "closegoal": new,
        "guide": guide,
        "delta": delta,
        "resource_diff": resource_diff(resources, new_collected, guide_collected),
    }
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    write_report(data)
    print(f"close-goal: {state_text(new)} final_stock={new['final_resource_stock']}")
    print(f"guide:      {state_text(guide)} final_stock={guide['final_resource_stock']}")
    print(f"wrote {OUT_JSON}")
    print(f"wrote {OUT_MD}")


if __name__ == "__main__":
    main()
