"""Render a two-level post-9 atomic resource topology report.

This is a readable audit view over
outputs/results/post9_atomic_resource_graph_from_delayed_prefix.json.
The source JSON contains full path splits; this report intentionally shows:

1. START -> first resource segment, grouped by MT1..MT9.
2. first resource -> second resource segment, grouped by MT1..MT9.

For each START edge we also show a short same-route continuation preview so a
first segment such as MT1 x8y4 redPotion does not look like the entire group.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from collections import defaultdict
from typing import Any


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_IN = os.path.join(
    ROOT,
    "outputs",
    "results",
    "post9_atomic_resource_graph_from_delayed_prefix.json",
)
DEFAULT_OUT = os.path.join(
    ROOT,
    "outputs",
    "reports",
    "post9_atomic_two_level_topology_from_delayed_prefix.md",
)

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
    "downFloor": "下楼",
}


def floor_num(fid: str) -> int:
    m = re.search(r"(\d+)$", fid)
    return int(m.group(1)) if m else 999


def in_floor_range(fid: str) -> bool:
    n = floor_num(fid)
    return 1 <= n <= 9


def rec_text(records: list[dict[str, Any]]) -> str:
    if not records:
        return "-"
    vals = []
    for record in records:
        x, y = record["pos"]
        vals.append(f"x{x}y{y} {NAME.get(record['eid'], record['eid'])}")
    return "，".join(vals)


def door_text(doors: list[int]) -> str:
    return f"{doors[0]}/{doors[1]}/{doors[2]}"


def after_text(seg: dict[str, Any]) -> str:
    after = seg["after"]
    return (
        f"HP={after['hp']} ATK={after['atk']} DEF={after['def']} "
        f"YK={after['yk']} BK={after['bk']} RK={after['rk']} "
        f"dmg={after['dmg']} door={after['yd']}/{after['bd']}/{after['rd']}"
    )


def edge_sort_key(seg: dict[str, Any]) -> tuple[Any, ...]:
    return (
        floor_num(seg["fid"]),
        seg["segment_dmg"],
        tuple(seg["segment_door"]),
        seg["from"],
        seg["to"],
        seg.get("route", ""),
    )


def rec_key(records: list[dict[str, Any]]) -> tuple[tuple[tuple[int, int], str], ...]:
    return tuple(((tuple(r["pos"]), r["eid"]) for r in records))


def edge_key(seg: dict[str, Any]) -> tuple[Any, ...]:
    return (
        seg["fid"],
        seg["from"],
        seg["to"],
        seg["segment_dmg"],
        tuple(seg["segment_door"]),
        rec_key(seg["items"]),
        rec_key(seg["doors"]),
        rec_key(seg["monsters"]),
    )


def unique_edges(edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    best: dict[tuple[Any, ...], dict[str, Any]] = {}
    routes: dict[tuple[Any, ...], set[str]] = defaultdict(set)
    for seg in edges:
        key = edge_key(seg)
        routes[key].add(seg.get("route", "-"))
        old = best.get(key)
        old_key = (
            old["segment_dmg"],
            tuple(old["segment_door"]),
            -old["after"]["hp"],
        ) if old else None
        new_key = (seg["segment_dmg"], tuple(seg["segment_door"]), -seg["after"]["hp"])
        if old is None or new_key < old_key:
            best[key] = dict(seg)
    out = []
    for key, seg in best.items():
        seg["_routes"] = sorted(routes[key])
        out.append(seg)
    return sorted(out, key=edge_sort_key)


def chain_preview(segments: list[dict[str, Any]], seg: dict[str, Any], max_next: int = 4) -> str:
    """Show same-route continuation after this segment."""
    route = seg.get("route")
    current = seg["to"]
    found = False
    preview: list[str] = []
    for candidate in segments:
        if candidate.get("route") != route:
            continue
        if not found:
            if (
                candidate["from"] == seg["from"]
                and candidate["to"] == seg["to"]
                and candidate["segment_dmg"] == seg["segment_dmg"]
                and candidate["segment_door"] == seg["segment_door"]
            ):
                found = True
            continue
        if candidate["from"] != current:
            break
        preview.append(candidate["to"])
        current = candidate["to"]
        if len(preview) >= max_next:
            break
    return " -> ".join(preview) if preview else "-"


def group_by_floor(edges: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for edge in edges:
        if in_floor_range(edge["fid"]):
            grouped[edge["fid"]].append(edge)
    return dict(sorted(grouped.items(), key=lambda item: floor_num(item[0])))


def route_count_text(seg: dict[str, Any]) -> str:
    routes = seg.get("_routes", [])
    if not routes:
        return seg.get("route", "-")
    if len(routes) == 1:
        return routes[0]
    return f"{len(routes)} 条：{routes[0]}"


def edge_row(idx: int, seg: dict[str, Any], include_preview: bool, segments: list[dict[str, Any]]) -> str:
    preview = chain_preview(segments, seg) if include_preview else "-"
    return (
        f"| {idx} | {seg['from']} | {seg['to']} | {seg['segment_dmg']} | "
        f"{door_text(seg['segment_door'])} | {rec_text(seg['items'])} | "
        f"{rec_text(seg['doors'])} | {rec_text(seg['monsters'])} | "
        f"{after_text(seg)} | {preview} | {route_count_text(seg)} |"
    )


def write_report(data: dict[str, Any], out_path: str) -> None:
    segments = [seg for seg in data["segments"] if in_floor_range(seg["fid"])]
    direct = unique_edges([seg for seg in segments if seg["from"] == "START"])
    direct_nodes = {seg["to"] for seg in direct}
    second = unique_edges([seg for seg in segments if seg["from"] in direct_nodes])

    direct_by_floor = group_by_floor(direct)
    second_by_floor = group_by_floor(second)

    lines = [
        "# Post-9 原子资源拓扑图（直连 + 二段）",
        "",
        f"> 起点：{data['start_text']}",
        f"> 输入：`outputs/results/post9_atomic_resource_graph_from_delayed_prefix.json`",
        f"> START 直连边：{len(direct)}",
        f"> 二段边：{len(second)}",
        "",
        "说明：直连边只表示 `START -> 第一份资源`，不是完整资源组；`同路径后续预览` 用来提示这条路径后面还会继续吃到哪些资源。",
        "",
    ]

    lines.extend([
        "## START 直连边（MT1-MT9）",
        "",
        "| # | from | to | 段伤害 | 段门耗 | 本段资源 | 本段门 | 本段怪 | 到达状态 | 同路径后续预览 | 来源路径 |",
        "|---:|---|---|---:|---:|---|---|---|---|---|---|",
    ])
    idx = 1
    for fid in sorted(direct_by_floor, key=floor_num):
        lines.append(f"|  | **{fid}** |  |  |  |  |  |  |  |  |  |")
        for seg in direct_by_floor[fid]:
            lines.append(edge_row(idx, seg, include_preview=True, segments=segments))
            idx += 1

    lines.extend([
        "",
        "## 二段边（第一份资源 -> 下一份资源，MT1-MT9）",
        "",
        "| # | from | to | 段伤害 | 段门耗 | 本段资源 | 本段门 | 本段怪 | 到达状态 | 同路径后续预览 | 来源路径 |",
        "|---:|---|---|---:|---:|---|---|---|---|---|---|",
    ])
    idx = 1
    for fid in sorted(second_by_floor, key=floor_num):
        lines.append(f"|  | **{fid}** |  |  |  |  |  |  |  |  |  |")
        for seg in second_by_floor[fid]:
            lines.append(edge_row(idx, seg, include_preview=True, segments=segments))
            idx += 1

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")

    print(f"wrote {out_path}")
    print(f"direct={len(direct)} second={len(second)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=DEFAULT_IN)
    parser.add_argument("--output", default=DEFAULT_OUT)
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)
    write_report(data, args.output)


if __name__ == "__main__":
    main()
