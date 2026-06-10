"""Print the first-step auto resource-group graph from the delayed post-9 prefix."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.chdir(ROOT)

from scripts import continue_delayed_phase1_with_post9_resource as delayed
from scripts import post9_auto_resource_group_pareto as auto
from scripts import post9_resource_group_search as rg


OUT_JSON = os.path.join("outputs", "results", "post9_auto_resource_graph_from_delayed_prefix.json")
OUT_MD = os.path.join("outputs", "reports", "post9_auto_resource_graph_from_delayed_prefix.md")


NAME = {
    "redGem": "红宝石",
    "blueGem": "蓝宝石",
    "yellowKey": "黄钥匙",
    "blueKey": "蓝钥匙",
    "redKey": "红钥匙",
    "redPotion": "红血瓶",
    "bluePotion": "蓝血瓶",
    "yellowDoor": "黄门",
    "blueDoor": "蓝门",
    "redDoor": "红门",
    "greenSlime": "绿史莱姆",
    "redSlime": "红史莱姆",
    "bat": "小蝙蝠",
    "skeleton": "骷髅",
    "skeletonSoldier": "骷髅士兵",
    "bluePriest": "蓝法师",
    "yellowGuard": "初级卫兵",
    "skeletonCaptain": "骷髅队长",
    "upFloor": "上楼",
}


def state_text(ent: dict[str, Any]) -> str:
    return (
        f"HP={ent['hp']} ATK={ent['atk']} DEF={ent['def']} "
        f"YK={ent['yk']} BK={ent['bk']} RK={ent['rk']} "
        f"dmg={ent.get('_dmg', 0)} door={ent.get('_yd', 0)}/{ent.get('_bd', 0)}/{ent.get('_rd', 0)}"
    )


def clean_action(action: str) -> str:
    out = action
    out = out.replace("flyback=True", "飞回=True")
    out = out.replace("flyback=False", "飞回=False")
    out = out.replace("pure-no-redGem", "纯蓝宝石分支")
    out = out.replace("pure-no-blueGem", "纯红宝石分支")
    out = out.replace("[progress]", "[进楼]")
    for eid, name in sorted(NAME.items(), key=lambda kv: len(kv[0]), reverse=True):
        out = out.replace(eid, name)
    return out


def fmt_group(items: list[dict[str, Any]]) -> str:
    if not items:
        return "-"
    return "，".join(f"{r['pos']} {NAME.get(r['eid'], r['eid'])}" for r in items)


def compact_edge(edge: dict[str, Any]) -> dict[str, Any]:
    group = edge.get("_resource_group", {})
    return {
        "action": clean_action(edge.get("_last_action", "")),
        "kind": edge.get("_edge_kind", "-"),
        "segment_dmg": edge.get("_delta_dmg", 0),
        "segment_door": [edge.get("_delta_yd", 0), edge.get("_delta_bd", 0), edge.get("_delta_rd", 0)],
        "delta": {
            "hp": edge.get("_delta_hp", 0),
            "atk": edge.get("_delta_atk", 0),
            "def": edge.get("_delta_def", 0),
            "yk": edge.get("_delta_yk", 0),
            "bk": edge.get("_delta_bk", 0),
            "rk": edge.get("_delta_rk", 0),
        },
        "after": {
            "hp": edge["hp"],
            "atk": edge["atk"],
            "def": edge["def"],
            "yk": edge["yk"],
            "bk": edge["bk"],
            "rk": edge["rk"],
            "dmg": edge.get("_dmg", 0),
            "yd": edge.get("_yd", 0),
            "bd": edge.get("_bd", 0),
            "rd": edge.get("_rd", 0),
            "old_score": rg.old_score(edge),
            "resource_group_score": rg.resource_group_score(edge),
            "final_resource_stock": rg.final_resource_stock(edge),
        },
        "items": group.get("items", []),
        "doors": group.get("doors", []),
        "monsters": group.get("monsters", []),
    }


def sort_key(edge: dict[str, Any]) -> tuple[Any, ...]:
    kind_order = {"progress": 0, "stat": 1, "key": 2, "potion": 3, "redkey": 4, "boss": 5, "other": 6}
    return (
        kind_order.get(edge.get("_edge_kind", "other"), 6),
        edge.get("_delta_dmg", 0),
        edge.get("_delta_yd", 0),
        edge.get("_delta_bd", 0),
        -edge.get("_delta_def", 0),
        -edge.get("_delta_atk", 0),
        edge.get("_last_action", ""),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase1-expansions", type=int, default=300)
    parser.add_argument("--max-iter", type=int, default=160000)
    args = parser.parse_args()

    start, phase1 = delayed.find_candidate(args.phase1_expansions)
    edges = auto.generate_edges(start, max_targets=0, max_iter=args.max_iter, edge_limit=0)
    edges = sorted(edges, key=sort_key)
    rows = [compact_edge(e) for e in edges]

    data = {
        "phase1_elapsed": phase1.get("elapsed"),
        "start": {
            "hp": start["hp"],
            "atk": start["atk"],
            "def": start["def"],
            "yk": start["yk"],
            "bk": start["bk"],
            "rk": start["rk"],
            "dmg": start.get("_dmg", 0),
            "yd": start.get("_yd", 0),
            "bd": start.get("_bd", 0),
            "rd": start.get("_rd", 0),
            "last_action": start.get("_last_action") or start.get("_source"),
        },
        "edge_count": len(rows),
        "edges": rows,
    }
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    lines = [
        "# 9F 红蓝宝石后自动资源组图",
        "",
        f"> 起点：{state_text(start)}",
        f"> 起点动作：{start.get('_last_action') or start.get('_source')}",
        f"> 一阶资源组边数：{len(rows)}",
        "",
        "说明：每一行是一条由真实楼层寻路生成的资源组边，不是手写资源组。`段门耗` 为黄/蓝/红门。",
        "",
        "| # | 类型 | 资源组动作 | 段伤害 | 段门耗 | 属性变化 | 到达状态 | 获得资源 | 经过门 | 经过怪 |",
        "|---:|---|---|---:|---:|---|---|---|---|---|",
    ]
    for idx, row in enumerate(rows, 1):
        d = row["delta"]
        a = row["after"]
        door = "/".join(str(x) for x in row["segment_door"])
        delta = (
            f"HP{d['hp']:+} ATK{d['atk']:+} DEF{d['def']:+} "
            f"YK{d['yk']:+} BK{d['bk']:+} RK{d['rk']:+}"
        )
        after = (
            f"HP={a['hp']} ATK={a['atk']} DEF={a['def']} "
            f"YK={a['yk']} BK={a['bk']} RK={a['rk']} "
            f"dmg={a['dmg']} door={a['yd']}/{a['bd']}/{a['rd']}"
        )
        lines.append(
            f"| {idx} | {row['kind']} | {row['action']} | {row['segment_dmg']} | {door} | "
            f"{delta} | {after} | {fmt_group(row['items'])} | {fmt_group(row['doors'])} | {fmt_group(row['monsters'])} |"
        )
    os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
    with open(OUT_MD, "w", encoding="utf-8-sig") as f:
        f.write("\n".join(lines).rstrip() + "\n")

    print(f"wrote {OUT_JSON}")
    print(f"wrote {OUT_MD}")
    print(f"start: {state_text(start)}")
    print(f"edges: {len(rows)}")


if __name__ == "__main__":
    main()
