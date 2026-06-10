#!/usr/bin/env python3
"""Compare a post-9 route variant that refills at 6F x9y1 instead of 9F x2y2.

This is a targeted audit script, not a replacement for the broad search.  It
starts from the current delayed phase1 candidate, inserts an explicit 6F
yellow-key pickup, and filters the later MT9 up-floor action so paths that
collect 9F x2y2 are rejected.
"""

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

from scripts import compare_delayed_phase1_vs_user_guide as cmp
from scripts import continue_delayed_phase1_with_post9_resource as delayed
from scripts import post9_action_search as p9
from scripts import post9_resource_group_search as rg
from src.solver import gen_walkthrough as gw
from src.solver.full_search import FLOOR_13_COLLECTED, load_data


OUT_JSON = os.path.join("outputs", "results", "mt6_key_variant_comparison.json")
OUT_MD = os.path.join("outputs", "reports", "mt6_key_variant_comparison.md")
OUT_WALK = os.path.join("outputs", "walkthroughs", "walkthrough_mt6_key_variant.md")

STATE_RE = re.compile(
    r"HP=(?P<hp>-?\d+) ATK=(?P<atk>-?\d+) DEF=(?P<def>-?\d+) "
    r"YK=(?P<yk>-?\d+) BK=(?P<bk>-?\d+) RK=(?P<rk>-?\d+) "
    r"dmg=(?P<dmg>-?\d+) door=(?P<yd>-?\d+)/(?P<bd>-?\d+)/(?P<rd>-?\d+)"
)

RESOURCE_IDS = cmp.RESOURCE_IDS
ITEM_CN = cmp.ITEM_CN


def target_positions(fid: str, targets: list[str]) -> frozenset[tuple[int, int]]:
    return frozenset((x, y) for x, y, _t, eid in gw.maps[fid]["bl"] if eid in targets)


def state_text(ent: dict[str, Any]) -> str:
    return (
        f"HP={ent['hp']} ATK={ent['atk']} DEF={ent['def']} "
        f"YK={ent['yk']} BK={ent['bk']} RK={ent['rk']} "
        f"dmg={ent.get('_dmg', ent.get('dmg', 0))} "
        f"door={ent.get('_yd', ent.get('yd', 0))}/"
        f"{ent.get('_bd', ent.get('bd', 0))}/{ent.get('_rd', ent.get('rd', 0))}"
    )


def row_from_ent(ent: dict[str, Any]) -> dict[str, int]:
    return {
        "hp": ent["hp"],
        "atk": ent["atk"],
        "def": ent["def"],
        "yk": ent["yk"],
        "bk": ent["bk"],
        "rk": ent["rk"],
        "dmg": ent.get("_dmg", 0),
        "yd": ent.get("_yd", 0),
        "bd": ent.get("_bd", 0),
        "rd": ent.get("_rd", 0),
    }


def all_resources(maps: dict[str, Any]) -> dict[tuple[str, int, int], str]:
    out = {}
    for fid, data in maps.items():
        precollected = FLOOR_13_COLLECTED.get(fid, frozenset())
        for x, y, t, eid in data["bl"]:
            if t == 3 and eid in RESOURCE_IDS and (x, y) not in precollected:
                out[(fid, x, y)] = eid
    return out


def score_row(row: dict[str, int], collected: dict[str, set[tuple[int, int]]]) -> dict[str, Any]:
    ent = {
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
    residual, notes = rg.residual_resource_value(ent)
    final_residual, final_notes = rg.residual_resource_value(ent, ignore_monster_damage=True)
    return {
        "old_score": rg.old_score(ent),
        "resource_group_score": rg.resource_group_score(ent),
        "residual_value": residual,
        "residual_notes": notes,
        "final_residual_value": final_residual,
        "final_resource_stock": row["hp"] + row["yk"] * rg.YK_VALUE + row["bk"] * rg.BK_VALUE + final_residual,
        "final_residual_notes": final_notes,
        "final_residual_breakdown": rg.residual_resource_breakdown(ent, ignore_monster_damage=True, include_zero=True),
    }


def count_remaining(resources: dict[tuple[str, int, int], str], seen: dict[str, set[tuple[int, int]]]) -> Counter:
    c = Counter()
    for (fid, x, y), eid in resources.items():
        if (x, y) not in seen.get(fid, set()):
            c[eid] += 1
    return c


def count_taken(resources: dict[tuple[str, int, int], str], seen: dict[str, set[tuple[int, int]]]) -> Counter:
    c = Counter()
    for (fid, x, y), eid in resources.items():
        if (x, y) in seen.get(fid, set()):
            c[eid] += 1
    return c


def counter_cn(counter: Counter) -> str:
    order = ["yellowKey", "blueKey", "redKey", "redPotion", "bluePotion", "redGem", "blueGem", "sword1", "shield1"]
    parts = [f"{ITEM_CN.get(k, k)} {counter[k]}" for k in order if counter.get(k)]
    return "，".join(parts) if parts else "-"


def collected_as_sets(ent: dict[str, Any]) -> dict[str, set[tuple[int, int]]]:
    out = {fid: set(pos) for fid, pos in FLOOR_13_COLLECTED.items()}
    for fid, pos in ent.get("collected", {}).items():
        out.setdefault(fid, set()).update(pos)
    return out


def collected_for(ent: dict[str, Any], fid: str) -> frozenset[tuple[int, int]]:
    got = set(ent.get("collected", {}).get(fid, frozenset()))
    got.update(FLOOR_13_COLLECTED.get(fid, frozenset()))
    return frozenset(got)


def action_extra_removed(ent: dict[str, Any], fid: str, target: str) -> frozenset[tuple[int, int]]:
    if fid in {"MT3", "MT10"} and target == "blueGem":
        return target_positions(fid, ["redGem"]) - collected_for(ent, fid)
    if fid in {"MT3", "MT10"} and target == "redGem":
        return target_positions(fid, ["blueGem"]) - collected_for(ent, fid)
    return frozenset()


def apply_action(
    ent: dict[str, Any],
    fid: str,
    targets: list[str],
    flyback: bool,
    label: str,
    require: set[tuple[int, int]] | None = None,
    forbid: set[tuple[int, int]] | None = None,
) -> dict[str, Any]:
    require = require or set()
    forbid = forbid or set()
    extra_removed = frozenset()
    if len(targets) == 1:
        extra_removed = action_extra_removed(ent, fid, targets[0])
    pareto, _it, _nodes = gw.search_floor(
        gw.maps,
        fid,
        ent,
        targets,
        flyback=flyback,
        extra_removed=extra_removed,
        max_iter=500000,
    )
    if not pareto:
        raise RuntimeError(f"{label}: no pareto")

    already = collected_for(ent, fid)
    need = target_positions(fid, targets) - already
    red_doors = target_positions("MT10", ["redDoor"])
    options = []
    for hp, yk, bk, rk, atk, def_, _hs, vis, dc in pareto:
        if require and not require <= vis:
            continue
        if forbid and (forbid & vis):
            continue
        if "upFloor" not in targets and targets:
            if fid == "MT10" and "redDoor" in targets:
                if not (red_doors & vis):
                    continue
            elif all(t in {"redGem", "blueGem"} for t in targets):
                if need and not need <= vis:
                    continue
            elif need and not (need & vis):
                continue

        nc = dict(ent.get("collected", {}))
        nc[fid] = already | vis
        extra = 0
        if fid == "MT10" and "redDoor" in targets:
            extra = gw.boss_event_damage(atk, def_) + gw.calc_dmg("skeletonCaptain", atk, def_)
            if hp - extra <= 0:
                continue
        r = gw._make_result(
            hp - extra,
            yk,
            bk,
            rk,
            atk,
            def_,
            nc,
            ent["_id"],
            (fid, targets, flyback),
            dmg_cost=dc + extra,
        )
        r["_source"] = label
        gw._entry_store[r["_id"]]["_source"] = label
        options.append(r)
    if not options:
        raise RuntimeError(f"{label}: filtered empty")

    if targets == ["yellowKey"] or targets == ["blueKey"]:
        key = lambda e: (-e["yk"], -e["bk"], e.get("_dmg", 0), -e["hp"])
    elif targets == ["redDoor"]:
        key = lambda e: (e.get("_dmg", 0), e.get("_yd", 0), -e["hp"])
    else:
        key = lambda e: (e.get("_dmg", 0), e.get("_yd", 0), e.get("_bd", 0), -e["hp"], -e["atk"], -e["def"], -e["yk"])
    return sorted(options, key=key)[0]


def build_variant() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    start, _phase1 = delayed.find_candidate(300)
    chain = [{"label": "phase1 delayed prefix", "entry": start}]
    ent = start
    actions = [
        ("MT7 redGem", "MT7", ["redGem"], True, None, None),
        ("MT3 blueGem", "MT3", ["blueGem"], True, None, None),
        ("MT8 blueGem", "MT8", ["blueGem"], True, None, None),
        ("MT1 blueGem", "MT1", ["blueGem"], True, None, None),
        ("MT3 redGem", "MT3", ["redGem"], True, None, None),
        ("MT5 blueGem", "MT5", ["blueGem"], True, None, None),
        ("MT6 blueGem", "MT6", ["blueGem"], True, None, None),
        ("MT4 blueKey", "MT4", ["blueKey"], True, None, None),
        ("MT6 x9y1 yellowKey", "MT6", ["yellowKey"], True, {(9, 1)}, None),
        ("MT7 yellowKey", "MT7", ["yellowKey"], True, None, None),
        ("MT9 upFloor without x2y2", "MT9", ["upFloor"], True, None, {(2, 2)}),
        ("MT10 blueGem", "MT10", ["blueGem"], False, None, None),
        ("MT10 redGem", "MT10", ["redGem"], True, None, None),
        ("MT7 bluePotion", "MT7", ["bluePotion"], True, None, None),
        ("MT8 yellowKey/redKey", "MT8", ["yellowKey"], True, None, None),
        ("MT10 bluePotion", "MT10", ["bluePotion"], True, None, None),
        ("MT1 bluePotion", "MT1", ["bluePotion"], True, None, None),
        ("MT10 boss", "MT10", ["redDoor"], True, None, None),
    ]
    for label, fid, targets, flyback, require, forbid in actions:
        ent = apply_action(
            ent,
            fid,
            targets,
            flyback,
            label,
            require=set(require or ()),
            forbid=set(forbid or ()),
        )
        chain.append({"label": label, "entry": ent})
    return ent, chain


def delayed_current(blocks: dict[str, dict[tuple[int, int], tuple[int, str]]]) -> tuple[dict[str, int], dict[str, set[tuple[int, int]]]]:
    collected, final = cmp.delayed_collected(blocks)
    return final, collected


def guide_current(blocks: dict[str, dict[tuple[int, int], tuple[int, str]]]) -> tuple[dict[str, int], dict[str, set[tuple[int, int]]]]:
    return cmp.guide_final(), cmp.guide_collected(blocks)


def pair_resource_diff(
    resources: dict[tuple[str, int, int], str],
    a_seen: dict[str, set[tuple[int, int]]],
    b_seen: dict[str, set[tuple[int, int]]],
) -> dict[str, dict[str, list[dict[str, str]]]]:
    diff = defaultdict(lambda: {"a_taken_b_left": [], "a_left_b_taken": []})
    for (fid, x, y), eid in sorted(resources.items()):
        a = (x, y) in a_seen.get(fid, set())
        b = (x, y) in b_seen.get(fid, set())
        if a == b:
            continue
        rec = {"pos": f"x{x}y{y}", "eid": eid, "name": ITEM_CN.get(eid, eid)}
        if a and not b:
            diff[fid]["a_taken_b_left"].append(rec)
        elif b and not a:
            diff[fid]["a_left_b_taken"].append(rec)
    return dict(diff)


def diff_lines(title: str, diff: dict[str, dict[str, list[dict[str, str]]]], a_name: str, b_name: str) -> list[str]:
    lines = [
        f"## {title}",
        "",
        f"| 楼层 | {a_name} 已拿、{b_name} 剩余 | {a_name} 剩余、{b_name} 已拿 |",
        "|---:|---|---|",
    ]
    if not diff:
        lines.append("| - | - | - |")
        return lines
    for fid in sorted(diff, key=lambda x: int(x[2:])):
        a = "，".join(f"{r['pos']} {r['name']}" for r in diff[fid]["a_taken_b_left"]) or "-"
        b = "，".join(f"{r['pos']} {r['name']}" for r in diff[fid]["a_left_b_taken"]) or "-"
        lines.append(f"| {int(fid[2:])}F | {a} | {b} |")
    return lines


def enrich(name: str, row: dict[str, int], collected: dict[str, set[tuple[int, int]]], resources: dict[tuple[str, int, int], str]) -> dict[str, Any]:
    scored = score_row(row, collected)
    out = dict(row)
    out.update(scored)
    out["name"] = name
    out["taken_counts"] = dict(count_taken(resources, collected))
    out["remaining_counts"] = dict(count_remaining(resources, collected))
    return out


def write_walk(chain: list[dict[str, Any]]) -> None:
    lines = ["# MT6 x9y1 Key Variant Walk", ""]
    for idx, item in enumerate(chain):
        ent = item["entry"]
        if idx == 0:
            seg = 0
            door = "0/0/0"
        else:
            prev = chain[idx - 1]["entry"]
            seg = ent.get("_dmg", 0) - prev.get("_dmg", 0)
            door = (
                f"{ent.get('_yd', 0) - prev.get('_yd', 0)}/"
                f"{ent.get('_bd', 0) - prev.get('_bd', 0)}/"
                f"{ent.get('_rd', 0) - prev.get('_rd', 0)}"
            )
        lines.extend([
            f"## {idx}. {item['label']}",
            "",
            f"- {state_text(ent)}",
            f"- segment dmg={seg} door delta={door}",
            "",
        ])
    os.makedirs(os.path.dirname(OUT_WALK), exist_ok=True)
    with open(OUT_WALK, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")


def write_report(data: dict[str, Any]) -> None:
    rows = data["rows"]
    lines = [
        "# 6F x9y1 替代 9F x2y2 策略对比",
        "",
        "这个脚本从当前 delayed phase1 前缀出发，显式拿 `6F x9y1` 黄钥匙，并在 `MT9 upFloor` 阶段过滤掉会拿 `9F x2y2` 的路径。",
        "",
        "## 基础属性与分数",
        "",
        "| 路线 | 最终状态 | old_score | resource_group_score | residual | final_residual_0dmg | final_stock | 剩余关键资源 |",
        "|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['name']} | HP={row['hp']} ATK={row['atk']} DEF={row['def']} "
            f"YK={row['yk']} BK={row['bk']} RK={row['rk']} dmg={row['dmg']} "
            f"door={row['yd']}/{row['bd']}/{row['rd']} | {row['old_score']} | "
            f"{row['resource_group_score']} | {row['residual_value']} | "
            f"{row['final_residual_value']} | {row['final_resource_stock']} | "
            f"{counter_cn(Counter(row['remaining_counts']))} |"
        )
    lines.extend([
        "",
        "说明：old_score = `dmg + yd*50 + bd*200 - hp - yk*50 - bk*200`；resource_group_score 会额外扣掉可回收资源组净值。",
        "`residual` 是当前攻防下回收剩余资源仍需付出的门/怪成本；`final_residual_0dmg` 用于最终横向比较，忽略剩余怪物伤害，只保留门成本；`final_stock = HP + 持有钥匙价值 + final_residual_0dmg`。",
        "",
        "## final_residual_0dmg 计算明细",
        "",
        "计算公式：`资源组净值 = 剩余物品价值 - 未开门成本 - 怪物伤害`。这里是最终横向比较口径，所以怪物伤害固定按 `0` 计算；门成本仍按 `黄门=50`、`蓝门=200` 扣除。只计入净值为正的资源组。",
        "",
        "### 楼层小计",
        "",
    ])
    lines.extend(cmp.floor_summary_lines([
        (row["name"], row["final_residual_breakdown"]) for row in rows
    ]))
    for row in rows:
        lines.append("")
        lines.extend(cmp.breakdown_lines(row["name"], row["final_residual_breakdown"]))
    lines.append("")
    lines.extend(diff_lines("新策略 vs 当前 delayed 最优线：最终剩余资源差异", data["diff_variant_delayed"], "新策略", "delayed"))
    lines.append("")
    lines.extend(diff_lines("新策略 vs 攻略线：最终剩余资源差异", data["diff_variant_guide"], "新策略", "攻略"))
    lines.extend([
        "",
        "## 关键结论",
        "",
        "- `mt6-key variant` 是审计脚本强制版本；`current delayed` 是当前主搜索自然输出。",
        "- 如果二者最终剩余资源差异为空，说明主搜索已经自然进入同一类 key-pocket 路线。",
        "- 当前自然搜索版本已经优于强制审计版本；关键的 `6F x9y1` 替代 `9F x2y2` 已经被自然搜索覆盖。",
    ])
    os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")


def main() -> None:
    _hero, maps = load_data()
    blocks = cmp.block_map(maps)
    resources = all_resources(maps)

    variant_ent, chain = build_variant()
    variant_collected = collected_as_sets(variant_ent)
    delayed_row, delayed_seen = delayed_current(blocks)
    guide_row, guide_seen = guide_current(blocks)

    rows = [
        enrich("mt6-key variant", row_from_ent(variant_ent), variant_collected, resources),
        enrich("current delayed", delayed_row, delayed_seen, resources),
        enrich("user guide", guide_row, guide_seen, resources),
    ]
    data = {
        "rows": rows,
        "diff_variant_delayed": pair_resource_diff(resources, variant_collected, delayed_seen),
        "diff_variant_guide": pair_resource_diff(resources, variant_collected, guide_seen),
    }
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    write_walk(chain)
    write_report(data)
    print(f"wrote {OUT_JSON}")
    print(f"wrote {OUT_MD}")
    print(f"wrote {OUT_WALK}")
    for row in rows:
        print(
            f"{row['name']}: HP={row['hp']} ATK={row['atk']} DEF={row['def']} "
            f"YK={row['yk']} BK={row['bk']} RK={row['rk']} dmg={row['dmg']} "
            f"door={row['yd']}/{row['bd']}/{row['rd']} old={row['old_score']} "
            f"rg={row['resource_group_score']} residual={row['residual_value']}"
        )


if __name__ == "__main__":
    main()
