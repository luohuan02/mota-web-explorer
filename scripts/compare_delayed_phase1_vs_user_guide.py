#!/usr/bin/env python3
"""Compare the delayed phase1 route against the verified guide route."""

from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter, defaultdict
from typing import Any


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.chdir(ROOT)

import fixed_shield_strategy as fixed
import replay_user_post9_route as guide
from scripts import post9_resource_group_search as rg
from src.solver.full_search import FLOOR_13_COLLECTED, load_data


DELAYED_WALK = os.path.join(
    "outputs", "walkthroughs", "walkthrough_delayed_phase1_post9_resource_detailed.md"
)
OUT_JSON = os.path.join("outputs", "results", "delayed_phase1_vs_user_guide_resource_diff.json")
OUT_MD = os.path.join("outputs", "reports", "delayed_phase1_vs_user_guide_resource_cn.md")

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

STATE_RE = re.compile(
    r"HP=(?P<hp>-?\d+) ATK=(?P<atk>-?\d+) DEF=(?P<def>-?\d+) "
    r"YK=(?P<yk>-?\d+) BK=(?P<bk>-?\d+) RK=(?P<rk>-?\d+) "
    r"dmg=(?P<dmg>-?\d+) door=(?P<yd>-?\d+)/(?P<bd>-?\d+)/(?P<rd>-?\d+)"
)


def block_map(maps: dict[str, Any]) -> dict[str, dict[tuple[int, int], tuple[int, str]]]:
    return {
        fid: {(x, y): (t, eid) for x, y, t, eid in data["bl"]}
        for fid, data in maps.items()
    }


def state_text(row: dict[str, int]) -> str:
    return (
        f"HP={row['hp']} ATK={row['atk']} DEF={row['def']} "
        f"YK={row['yk']} BK={row['bk']} RK={row['rk']} "
        f"dmg={row['dmg']} door={row['yd']}/{row['bd']}/{row['rd']}"
    )


def score_ent(row: dict[str, Any], collected: dict[str, set[tuple[int, int]]]) -> dict[str, Any]:
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


def all_resources(maps: dict[str, Any]) -> dict[tuple[str, int, int], str]:
    out = {}
    for fid, data in maps.items():
        precollected = FLOOR_13_COLLECTED.get(fid, frozenset())
        for x, y, t, eid in data["bl"]:
            if t == 3 and eid in RESOURCE_IDS and (x, y) not in precollected:
                out[(fid, x, y)] = eid
    return out


def initial_collected() -> dict[str, set[tuple[int, int]]]:
    return {fid: set(pos) for fid, pos in FLOOR_13_COLLECTED.items()}


def guide_collected(blocks: dict[str, dict[tuple[int, int], tuple[int, str]]]) -> dict[str, set[tuple[int, int]]]:
    fixed_result = fixed.replay_route()
    collected = initial_collected()
    for fid, positions in fixed_result["collected"].items():
        collected.setdefault(fid, set()).update((p["x"], p["y"]) for p in positions)

    replay = guide.replay()
    for step in replay["steps"]:
        fid = step["floor"]
        pos = tuple(step["pos"])
        if pos in blocks.get(fid, {}):
            t, _eid = blocks[fid][pos]
            if t in (1, 2, 3):
                collected.setdefault(fid, set()).add(pos)
    return collected


def delayed_collected(
    blocks: dict[str, dict[tuple[int, int], tuple[int, str]]]
) -> tuple[dict[str, set[tuple[int, int]]], dict[str, int]]:
    collected = initial_collected()
    current_floor = None
    final = None
    with open(DELAYED_WALK, encoding="utf-8") as f:
        for line in f:
            heading = re.search(r"## .*?MT(\d+)", line)
            if heading:
                current_floor = f"MT{heading.group(1)}"
                continue
            if current_floor is None:
                continue
            for x, y in re.findall(r"x(\d+)y(\d+)", line):
                pos = (int(x), int(y))
                block = blocks.get(current_floor, {}).get(pos)
                if block is None:
                    continue
                t, _eid = block
                if t in (1, 2, 3):
                    collected.setdefault(current_floor, set()).add(pos)
            if "小结" in line:
                match = STATE_RE.search(line)
                if match:
                    final = {k: int(v) for k, v in match.groupdict().items()}
    if final is None:
        raise RuntimeError(f"Cannot parse final state from {DELAYED_WALK}")
    return collected, final


def guide_final() -> dict[str, int]:
    replay = guide.replay()
    state = replay["final"]["state"]
    doors = replay["final"]["doors"]
    return {
        "hp": state["hp"],
        "atk": state["atk"],
        "def": state["def"],
        "yk": state["yk"],
        "bk": state["bk"],
        "rk": state["rk"],
        "dmg": replay["final"]["dmg"],
        "yd": doors["yellow"],
        "bd": doors["blue"],
        "rd": doors["red"],
    }


def floor_resource_diff(
    resources: dict[tuple[str, int, int], str],
    guide_seen: dict[str, set[tuple[int, int]]],
    delayed_seen: dict[str, set[tuple[int, int]]],
) -> dict[str, dict[str, list[dict[str, Any]]]]:
    diff = defaultdict(lambda: {"guide_left_delayed_taken": [], "delayed_left_guide_taken": []})
    for (fid, x, y), eid in sorted(resources.items()):
        g = (x, y) in guide_seen.get(fid, set())
        d = (x, y) in delayed_seen.get(fid, set())
        if g == d:
            continue
        rec = {"pos": f"x{x}y{y}", "eid": eid, "name": ITEM_CN.get(eid, eid)}
        if d and not g:
            diff[fid]["guide_left_delayed_taken"].append(rec)
        elif g and not d:
            diff[fid]["delayed_left_guide_taken"].append(rec)
    return dict(diff)


def count_remaining(
    resources: dict[tuple[str, int, int], str],
    seen: dict[str, set[tuple[int, int]]],
) -> Counter:
    c = Counter()
    for (fid, x, y), eid in resources.items():
        if (x, y) not in seen.get(fid, set()):
            c[eid] += 1
    return c


def count_taken(
    resources: dict[tuple[str, int, int], str],
    seen: dict[str, set[tuple[int, int]]],
) -> Counter:
    c = Counter()
    for (fid, x, y), eid in resources.items():
        if (x, y) in seen.get(fid, set()):
            c[eid] += 1
    return c


def counter_cn(counter: Counter) -> str:
    order = ["yellowKey", "blueKey", "redKey", "redPotion", "bluePotion", "redGem", "blueGem", "sword1", "shield1"]
    parts = [f"{ITEM_CN.get(k, k)} {counter[k]}" for k in order if counter.get(k)]
    return "，".join(parts) if parts else "-"


def item_list_cn(items: list[dict[str, Any]]) -> str:
    if not items:
        return "-"
    return "，".join(
        f"{item['pos']} {ITEM_CN.get(item['eid'], item['eid'])}({item['value']})"
        for item in items
    )


def door_list_cn(doors: list[dict[str, Any]]) -> str:
    if not doors:
        return "-"
    return "，".join(f"{door['pos']} {door['cost']}" for door in doors)


def monster_list_cn(monsters: list[dict[str, Any]]) -> str:
    if not monsters:
        return "-"
    return "，".join(f"{mon['pos']} {mon['eid']}({mon['damage']})" for mon in monsters)


def floor_summary_lines(routes: list[tuple[str, list[dict[str, Any]]]]) -> list[str]:
    floors = sorted({row["floor"] for _name, rows in routes for row in rows})
    lines = [
        "| 路线 | " + " | ".join(f"{floor}F" for floor in floors) + " | 总计 |",
        "|---" + "|---:" * (len(floors) + 1) + "|",
    ]
    for name, rows in routes:
        by_floor = defaultdict(int)
        for row in rows:
            by_floor[row["floor"]] += row["value"]
        total = sum(by_floor.values())
        vals = " | ".join(str(by_floor.get(floor, 0)) for floor in floors)
        lines.append(f"| {name} | {vals} | {total} |")
    return lines


def breakdown_lines(route_name: str, rows: list[dict[str, Any]]) -> list[str]:
    lines = [
        f"### {route_name}",
        "",
        "| 楼层 | 资源组 | 剩余物品 | 物品价值 | 门成本 | 怪物伤害 | 净值 |",
        "|---:|---|---|---:|---:|---:|---:|",
    ]
    for row in sorted(rows, key=lambda r: (r["floor"], r["group"])):
        lines.append(
            f"| {row['floor']}F | {row['group']} | {item_list_cn(row['items'])} | "
            f"{row['reward']} | {row['door_cost']} | {row['monster_damage']} | {row['value']} |"
        )
    if not rows:
        lines.append("| - | - | - | 0 | 0 | 0 | 0 |")
    return lines


def diff_table_rows(diff: dict[str, dict[str, list[dict[str, Any]]]]) -> list[str]:
    lines = []
    for fid in sorted(diff, key=lambda x: int(x[2:])):
        left_by_guide = diff[fid]["guide_left_delayed_taken"]
        left_by_delayed = diff[fid]["delayed_left_guide_taken"]
        a = "，".join(f"{r['pos']} {r['name']}" for r in left_by_guide) or "-"
        b = "，".join(f"{r['pos']} {r['name']}" for r in left_by_delayed) or "-"
        lines.append(f"| {int(fid[2:])}F | {a} | {b} |")
    return lines


def write_report(data: dict[str, Any]) -> None:
    delayed = data["delayed"]
    guide_row = data["guide"]
    dmg_gain = guide_row["dmg"] - delayed["dmg"]
    yellow_delta = delayed["yd"] - guide_row["yd"]
    hp_delta = delayed["hp"] - guide_row["hp"]
    old_gain = guide_row["old_score"] - delayed["old_score"]
    rg_gain = guide_row["resource_group_score"] - delayed["resource_group_score"]
    stock_delta = delayed["final_resource_stock"] - guide_row["final_resource_stock"]

    def better_text(delta: int) -> str:
        if delta > 0:
            return f"延后线路好 `{delta}`"
        if delta < 0:
            return f"攻略线路好 `{-delta}`"
        return "两者相同"

    def stock_text(delta: int) -> str:
        if delta > 0:
            return f"延后线路好 `{delta}`"
        if delta < 0:
            return f"攻略线路好 `{-delta}`"
        return "两者相同"

    lines = [
        "# 延后 4-9 线路 vs 攻略线路资源对比",
        "",
        "对比对象：",
        f"- 延后线路：`{DELAYED_WALK}`",
        "- 攻略线路：`outputs/walkthroughs/walkthrough_user_post9_route.md`",
        "",
        "## 最终状态与得分",
        "",
        "| 路线 | 最终状态 | old_score | resource_group_score | residual | final_residual_0dmg | final_stock |",
        "|---|---|---:|---:|---:|---:|---:|",
        f"| 延后线路 | {state_text(delayed)} | {delayed['old_score']} | {delayed['resource_group_score']} | {delayed['residual_value']} | {delayed['final_residual_value']} | {delayed['final_resource_stock']} |",
        f"| 攻略线路 | {state_text(guide_row)} | {guide_row['old_score']} | {guide_row['resource_group_score']} | {guide_row['residual_value']} | {guide_row['final_residual_value']} | {guide_row['final_resource_stock']} |",
        "",
        "说明：",
        "- old_score = `dmg + yd*50 + bd*200 - hp - yk*50 - bk*200`。",
        "- resource_group_score 会额外扣掉当前还能回收、且按资源组估算为正收益的剩余资源价值。",
        "- residual 是当前攻防下回收剩余资源仍需付出的门/怪成本；final_residual_0dmg 用于最终横向比较，忽略剩余怪物伤害，只保留门成本。",
        "- final_stock = HP + 持有钥匙价值 + final_residual_0dmg。",
        "",
        "## final_residual_0dmg 计算明细",
        "",
        "计算公式：`资源组净值 = 剩余物品价值 - 未开门成本 - 怪物伤害`。这里是最终横向比较口径，所以怪物伤害固定按 `0` 计算；门成本仍按 `黄门=50`、`蓝门=200` 扣除。只计入净值为正的资源组。",
        "",
        "### 楼层小计",
        "",
    ]
    lines.extend(floor_summary_lines([
        ("延后线路", delayed["final_residual_breakdown"]),
        ("攻略线路", guide_row["final_residual_breakdown"]),
    ]))
    lines.append("")
    lines.extend(breakdown_lines("延后线路", delayed["final_residual_breakdown"]))
    lines.append("")
    lines.extend(breakdown_lines("攻略线路", guide_row["final_residual_breakdown"]))
    lines.extend([
        "",
        "## 直接差异",
        "",
        f"- 延后线路 dmg 少 `{dmg_gain}`。",
        f"- 延后线路黄门差异 `{yellow_delta:+d}`；蓝门、红门相同。",
        f"- 延后线路通关 HP {'多' if hp_delta >= 0 else '少'} `{abs(hp_delta)}`。",
        f"- old_score：延后线路 `{delayed['old_score']}`，攻略线路 `{guide_row['old_score']}`，{better_text(old_gain)}。",
        f"- resource_group_score：延后线路 `{delayed['resource_group_score']}`，攻略线路 `{guide_row['resource_group_score']}`，{better_text(rg_gain)}。",
        f"- final_stock：延后线路 `{delayed['final_resource_stock']}`，攻略线路 `{guide_row['final_resource_stock']}`，{stock_text(stock_delta)}。",
        "",
        "## 剩余资源总量",
        "",
        "| 路线 | 已拿关键资源 | 剩余关键资源 |",
        "|---|---|---|",
        f"| 延后线路 | {counter_cn(Counter(delayed['taken_counts']))} | {counter_cn(Counter(delayed['remaining_counts']))} |",
        f"| 攻略线路 | {counter_cn(Counter(guide_row['taken_counts']))} | {counter_cn(Counter(guide_row['remaining_counts']))} |",
        "",
        "## 每层剩余资源差异",
        "",
        "只列两条路线最后不一样的资源。双方都拿了、双方都没拿的不列。",
        "",
        "| 楼层 | 攻略剩余、延后已拿 | 延后剩余、攻略已拿 |",
        "|---:|---|---|",
    ])
    lines.extend(diff_table_rows(data["resource_diff"]))
    lines.extend(
        [
            "",
            "## 结论",
            "",
            "当前延后线路已经自然走出 `6F x9y1 黄钥匙` 替代 `9F x2y2 黄钥匙` 的 key-pocket 分支；后续不再把 9F 骷髅士兵钥匙作为上 10F 的隐式附带资源。",
            "",
            f"与攻略相比，它少 `{dmg_gain}` 点纯伤害，多开 `{yellow_delta}` 个黄门，最终 HP {'多' if hp_delta >= 0 else '少'} `{abs(hp_delta)}`。"
            "old_score 与 resource_group_score 会受到 dmg 项影响，因此当前两个分数下延后线路更优；"
            f"但按最终横向资源口径 final_stock，{'延后线路更优' if stock_delta > 0 else '攻略线路更优' if stock_delta < 0 else '两者相同'} `{abs(stock_delta)}`。",
        ]
    )
    os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main() -> None:
    _hero, maps = load_data()
    blocks = block_map(maps)
    resources = all_resources(maps)

    g_collected = guide_collected(blocks)
    d_collected, d_final = delayed_collected(blocks)
    g_final = guide_final()

    g_ent = score_ent(g_final, g_collected)
    d_ent = score_ent(d_final, d_collected)
    g_residual, g_notes = rg.residual_resource_value(g_ent)
    d_residual, d_notes = rg.residual_resource_value(d_ent)
    g_final_residual, g_final_notes = rg.residual_resource_value(g_ent, ignore_monster_damage=True)
    d_final_residual, d_final_notes = rg.residual_resource_value(d_ent, ignore_monster_damage=True)
    g_final_breakdown = rg.residual_resource_breakdown(g_ent, ignore_monster_damage=True, include_zero=True)
    d_final_breakdown = rg.residual_resource_breakdown(d_ent, ignore_monster_damage=True, include_zero=True)

    g_final.update(
        old_score=rg.old_score(g_ent),
        resource_group_score=rg.resource_group_score(g_ent),
        residual_value=g_residual,
        residual_notes=g_notes,
        final_residual_value=g_final_residual,
        final_resource_stock=g_final["hp"] + g_final["yk"] * rg.YK_VALUE + g_final["bk"] * rg.BK_VALUE + g_final_residual,
        final_residual_notes=g_final_notes,
        final_residual_breakdown=g_final_breakdown,
        taken_counts=dict(count_taken(resources, g_collected)),
        remaining_counts=dict(count_remaining(resources, g_collected)),
    )
    d_final.update(
        old_score=rg.old_score(d_ent),
        resource_group_score=rg.resource_group_score(d_ent),
        residual_value=d_residual,
        residual_notes=d_notes,
        final_residual_value=d_final_residual,
        final_resource_stock=d_final["hp"] + d_final["yk"] * rg.YK_VALUE + d_final["bk"] * rg.BK_VALUE + d_final_residual,
        final_residual_notes=d_final_notes,
        final_residual_breakdown=d_final_breakdown,
        taken_counts=dict(count_taken(resources, d_collected)),
        remaining_counts=dict(count_remaining(resources, d_collected)),
    )

    data = {
        "delayed": d_final,
        "guide": g_final,
        "resource_diff": floor_resource_diff(resources, g_collected, d_collected),
    }
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    write_report(data)
    print(f"wrote {OUT_MD}")
    print(f"wrote {OUT_JSON}")
    print(f"delayed: {state_text(d_final)} old={d_final['old_score']} rg={d_final['resource_group_score']}")
    print(f"guide:   {state_text(g_final)} old={g_final['old_score']} rg={g_final['resource_group_score']}")


if __name__ == "__main__":
    main()
