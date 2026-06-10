"""Report compressed post-9 resource groups for high-level search.

This is different from the atomic split report.  A compressed resource group is
the first reachable resource plus every other uncollected resource connected to
it without crossing a new monster or door.  Entering the group pays the path
cost up to the first resource; collecting the rest of the group is free.

The report is intentionally shallow: START -> group, then same-floor group ->
next group.  It is meant to audit the map compression before wiring it into a
high-level Dijkstra/Pareto search.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any, Iterable


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
for path in (SCRIPT_DIR, ROOT):
    if path not in sys.path:
        sys.path.insert(0, path)
os.chdir(ROOT)

from scripts import continue_delayed_phase1_with_post9_resource as delayed
from scripts import post9_auto_resource_group_pareto as auto
from scripts import report_post9_atomic_resource_graph as atomic_graph
from src.solver import gen_walkthrough as gw


OUT_MD = os.path.join("outputs", "reports", "post9_compressed_resource_topology_from_delayed_prefix.md")
ATOMIC_JSON = os.path.join("outputs", "results", "post9_atomic_resource_graph_from_delayed_prefix.json")
DETAILED_WALK = os.path.join("outputs", "walkthroughs", "walkthrough_delayed_phase1_post9_resource_detailed.md")

RESOURCE_IDS = {
    "redGem",
    "blueGem",
    "yellowKey",
    "blueKey",
    "redKey",
    "redPotion",
    "bluePotion",
    "sword1",
    "shield1",
}

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


@dataclass(frozen=True)
class ResourceItem:
    pos: tuple[int, int]
    eid: str


def floor_num(fid: str) -> int:
    return int(fid[2:])


def floor_label(fid: str) -> str:
    return f"{floor_num(fid)}楼"


def item_label(item: ResourceItem) -> str:
    x, y = item.pos
    return f"x{x}y{y} {NAME.get(item.eid, item.eid)}"


def list_text(items: Iterable[str]) -> str:
    vals = list(items)
    return "，".join(vals) if vals else "-"


def state_text(ent: dict[str, Any]) -> str:
    return (
        f"HP={ent['hp']} ATK={ent['atk']} DEF={ent['def']} "
        f"YK={ent['yk']} BK={ent['bk']} RK={ent['rk']} "
        f"dmg={ent.get('_dmg', 0)} door={ent.get('_yd', 0)}/{ent.get('_bd', 0)}/{ent.get('_rd', 0)}"
    )


def block_map(fid: str) -> dict[tuple[int, int], tuple[int, str]]:
    return {(x, y): (t, eid) for x, y, t, eid in gw.maps[fid]["bl"]}


def is_wall(fid: str, pos: tuple[int, int]) -> bool:
    x, y = pos
    data = gw.maps[fid]
    if x < 0 or y < 0 or x >= data["W"] or y >= data["H"]:
        return True
    return data["m"][y][x] == 1


def collected_for(ent: dict[str, Any], fid: str) -> frozenset[tuple[int, int]]:
    return auto.collected_for(ent, fid)


def step_kind(fid: str, step: dict[str, Any]) -> tuple[int, str]:
    for x, y, t, eid in gw.maps[fid]["bl"]:
        if x == step["x"] and y == step["y"]:
            return t, eid
    return -1, step.get("eid", "")


def find_first_resource(fid: str, steps: list[dict[str, Any]]) -> int | None:
    for idx, step in enumerate(steps):
        t, eid = step_kind(fid, step)
        if t == 3 and eid in RESOURCE_IDS:
            return idx
    return None


def prefix_records(fid: str, steps: list[dict[str, Any]], first_idx: int) -> dict[str, Any]:
    monsters: list[str] = []
    doors: list[str] = []
    consumed: set[tuple[int, int]] = set()
    dmg = 0
    door_counts = [0, 0, 0]
    for step in steps[: first_idx + 1]:
        pos = (step["x"], step["y"])
        t, eid = step_kind(fid, step)
        if t in {1, 2, 3}:
            consumed.add(pos)
        if t == 1:
            hit = max(0, step["hp_before"] - step["hp_after"])
            dmg += hit
            monsters.append(f"x{pos[0]}y{pos[1]} {NAME.get(eid, eid)}({hit})")
        elif t == 2:
            if eid == "yellowDoor":
                door_counts[0] += 1
            elif eid == "blueDoor":
                door_counts[1] += 1
            elif eid == "redDoor":
                door_counts[2] += 1
            doors.append(f"x{pos[0]}y{pos[1]} {NAME.get(eid, eid)}")
    return {
        "dmg": dmg,
        "doors": door_counts,
        "monster_text": monsters,
        "door_text": doors,
        "consumed": consumed,
    }


def zero_cost_group(
    ent: dict[str, Any],
    fid: str,
    first_pos: tuple[int, int],
    prefix_consumed: set[tuple[int, int]],
) -> list[ResourceItem]:
    """Collect all resources connected without crossing a fresh monster/door."""
    blocks = block_map(fid)
    already = set(collected_for(ent, fid))
    removed = already | set(prefix_consumed)
    q: deque[tuple[int, int]] = deque([first_pos])
    seen = {first_pos}
    found: list[ResourceItem] = []

    while q:
        pos = q.popleft()
        t, eid = blocks.get(pos, (0, ""))
        if t == 3 and eid in RESOURCE_IDS and pos not in already:
            found.append(ResourceItem(pos, eid))
        x, y = pos
        for nxt in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if nxt in seen or is_wall(fid, nxt):
                continue
            nt, _neid = blocks.get(nxt, (0, ""))
            if nt in {1, 2} and nxt not in removed:
                continue
            seen.add(nxt)
            q.append(nxt)
    return found


def group_gain(items: list[ResourceItem]) -> dict[str, int]:
    gain = {"hp": 0, "atk": 0, "def": 0, "yk": 0, "bk": 0, "rk": 0}
    for item in items:
        if item.eid == "redPotion":
            gain["hp"] += 50
        elif item.eid == "bluePotion":
            gain["hp"] += 200
        elif item.eid == "redGem":
            gain["atk"] += 1
        elif item.eid == "blueGem":
            gain["def"] += 1
        elif item.eid == "yellowKey":
            gain["yk"] += 1
        elif item.eid == "blueKey":
            gain["bk"] += 1
        elif item.eid == "redKey":
            gain["rk"] += 1
        elif item.eid.startswith("sword"):
            gain["atk"] += 10
        elif item.eid.startswith("shield"):
            gain["def"] += 10
    return gain


def gain_text(gain: dict[str, int]) -> str:
    parts = []
    for key, label in (("hp", "HP"), ("atk", "ATK"), ("def", "DEF"), ("yk", "YK"), ("bk", "BK"), ("rk", "RK")):
        if gain[key]:
            parts.append(f"{label}+{gain[key]}")
    return " ".join(parts) if parts else "-"


def make_probe(
    base: dict[str, Any],
    collected: dict[str, frozenset[tuple[int, int]]] | None = None,
    atk: int | None = None,
    def_: int | None = None,
) -> dict[str, Any]:
    """Create a high-budget probe state that still uses real ATK/DEF."""
    probe_collected = collected if collected is not None else base.get("collected", {})
    return gw._make_result(
        99999,
        50,
        20,
        0,
        atk if atk is not None else base["atk"],
        def_ if def_ is not None else base["def"],
        {fid: frozenset(pos) for fid, pos in probe_collected.items()},
        base["_id"],
        None,
        dmg_cost=0,
    )


def edge_child(probe: dict[str, Any], edge: dict[str, Any]) -> dict[str, Any]:
    gain = edge["gain"]
    new_collected = {fid: frozenset(pos) for fid, pos in probe.get("collected", {}).items()}
    fid = edge["fid"]
    before = set(new_collected.get(fid, frozenset()))
    before.update(edge["prefix_consumed"])
    before.update(item.pos for item in edge["items"])
    new_collected[fid] = frozenset(before)
    return make_probe(
        probe,
        collected=new_collected,
        atk=probe["atk"] + gain["atk"],
        def_=probe["def"] + gain["def"],
    )


def candidate_route_edges(ent: dict[str, Any], fid: str, max_iter: int) -> list[dict[str, Any]]:
    pending_by_eid: dict[str, set[tuple[int, int]]] = defaultdict(set)
    already = collected_for(ent, fid)
    for target in auto.TARGETS:
        if target.fid == fid and target.eid in RESOURCE_IDS and target.pos not in already:
            pending_by_eid[target.eid].add(target.pos)

    out: list[dict[str, Any]] = []
    for eid, positions in sorted(pending_by_eid.items()):
        out.extend(auto.exact_item_edges(ent, fid, eid, set(positions), max_iter=max_iter))
    return out


def compressed_edges_for_floor(ent: dict[str, Any], fid: str, max_iter: int) -> list[dict[str, Any]]:
    edges: list[dict[str, Any]] = []
    for route in candidate_route_edges(ent, fid, max_iter=max_iter):
        step_fid, targets, flyback = route.get("_step_info", (None, [], True))
        if step_fid != fid:
            continue
        steps, _final, mismatch = atomic_graph.reconstruct_steps(
            ent,
            route,
            fid,
            targets,
            flyback,
            max_iter=max_iter,
        )
        if not steps or mismatch:
            continue
        first_idx = find_first_resource(fid, steps)
        if first_idx is None:
            continue
        first = steps[first_idx]
        first_pos = (first["x"], first["y"])
        prefix = prefix_records(fid, steps, first_idx)
        group_items = zero_cost_group(ent, fid, first_pos, prefix["consumed"])
        if not group_items:
            continue
        gain = group_gain(group_items)
        group_sig = tuple(sorted((item.pos, item.eid) for item in group_items))
        edges.append({
            "fid": fid,
            "group_sig": group_sig,
            "first": ResourceItem(first_pos, step_kind(fid, first)[1]),
            "items": group_items,
            "gain": gain,
            "entry_dmg": prefix["dmg"],
            "entry_doors": prefix["doors"],
            "entry_monsters": prefix["monster_text"],
            "entry_door_text": prefix["door_text"],
            "prefix_consumed": prefix["consumed"],
            "route": route.get("_last_action", "-"),
        })
    return pareto_edges(edges)


def dominates(a: dict[str, Any], b: dict[str, Any]) -> bool:
    ad = a["entry_doors"]
    bd = b["entry_doors"]
    weak = a["entry_dmg"] <= b["entry_dmg"] and all(x <= y for x, y in zip(ad, bd))
    strict = a["entry_dmg"] < b["entry_dmg"] or any(x < y for x, y in zip(ad, bd))
    return weak and strict


def pareto_edges(edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_group: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for edge in edges:
        by_group[edge["group_sig"]].append(edge)

    kept: list[dict[str, Any]] = []
    for variants in by_group.values():
        local: list[dict[str, Any]] = []
        for edge in sorted(variants, key=edge_sort_key):
            if any(dominates(old, edge) for old in local):
                continue
            local = [old for old in local if not dominates(edge, old)]
            if not any(edge_key(edge) == edge_key(old) for old in local):
                local.append(edge)
        kept.extend(local)
    return sorted(kept, key=edge_sort_key)


def edge_key(edge: dict[str, Any]) -> tuple[Any, ...]:
    return (
        edge["group_sig"],
        edge["entry_dmg"],
        tuple(edge["entry_doors"]),
        tuple(sorted(edge["prefix_consumed"])),
    )


def edge_sort_key(edge: dict[str, Any]) -> tuple[Any, ...]:
    return (
        floor_num(edge["fid"]),
        edge["entry_dmg"],
        tuple(edge["entry_doors"]),
        len(edge["items"]),
        str(edge["group_sig"]),
    )


def group_name(edge: dict[str, Any]) -> str:
    return " + ".join(item_label(item) for item in edge["items"])


def door_cost_text(edge: dict[str, Any]) -> str:
    return "/".join(str(x) for x in edge["entry_doors"])


def write_report(start: dict[str, Any], direct: dict[str, list[dict[str, Any]]], second: list[dict[str, Any]]) -> None:
    second_by_floor_from: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in second:
        second_by_floor_from[(row["fid"], row["from_group"])].append(row)

    lines = [
        "# Post-9 压缩资源组拓扑图（两段）",
        "",
        f"> 起点：{state_text(start)}",
        "> 口径：同一区域内不再过新门、不打新怪即可连续取得的资源合并为一个资源组。",
        "> 本报告使用高 HP/钥匙探测状态发现拓扑；`进入伤害/门耗` 才是后续高层搜索要扣的成本。",
        "",
        "## 第一段：START -> 资源组",
        "",
        "| # | 楼层 | 资源组 | 进入伤害 | 进入门耗 Y/B/R | 进入门/怪 | 组内收益 | 来源路径 |",
        "|---:|---|---|---:|---:|---|---|---|",
    ]
    idx = 1
    for fid in sorted(direct, key=floor_num):
        for edge in direct[fid]:
            req = list_text(edge["entry_door_text"] + edge["entry_monsters"])
            lines.append(
                f"| {idx} | {floor_label(fid)} | {group_name(edge)} | {edge['entry_dmg']} | "
                f"{door_cost_text(edge)} | {req} | {gain_text(edge['gain'])} | {edge['route']} |"
            )
            idx += 1

    lines.extend([
        "",
        "## 第二段：第一段资源组 -> 同层下一资源组",
        "",
        "| # | 楼层 | from | to | 进入伤害 | 进入门耗 Y/B/R | 进入门/怪 | 组内收益 | 来源路径 |",
        "|---:|---|---|---|---:|---:|---|---|---|",
    ])
    idx = 1
    for fid in sorted(direct, key=floor_num):
        for first in direct[fid]:
            from_name = group_name(first)
            rows = second_by_floor_from.get((fid, first["group_id"]), [])
            for edge in rows:
                req = list_text(edge["entry_door_text"] + edge["entry_monsters"])
                lines.append(
                    f"| {idx} | {floor_label(fid)} | {from_name} | {group_name(edge)} | "
                    f"{edge['entry_dmg']} | {door_cost_text(edge)} | {req} | "
                    f"{gain_text(edge['gain'])} | {edge['route']} |"
                )
                idx += 1

    os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")
    print(f"wrote {OUT_MD}")
    print(f"direct={sum(len(v) for v in direct.values())} second={len(second)}")


def load_cached_atomic(path: str) -> dict[str, Any]:
    import json

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def floor_from_node(node: str) -> str:
    return node.split()[0]


def cached_item(item: dict[str, Any]) -> ResourceItem:
    return ResourceItem(tuple(item["pos"]), item["eid"])


def cached_gain(items: list[dict[str, Any]]) -> dict[str, int]:
    return group_gain([cached_item(item) for item in items])


def cached_group_name(edge: dict[str, Any]) -> str:
    return " + ".join(item_label(cached_item(item)) for item in edge["items"]) or "-"


def cached_group_sig(fid: str, items: list[dict[str, Any]]) -> tuple[Any, ...]:
    return (
        fid,
        tuple(sorted((tuple(item["pos"]), item["eid"]) for item in items)),
    )


def is_zero_follow_segment(seg: dict[str, Any]) -> bool:
    return (
        seg["segment_dmg"] == 0
        and seg["segment_door"] == [0, 0, 0]
        and not seg["doors"]
        and not seg["monsters"]
        and bool(seg["items"])
    )


def route_chains(segments: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    chains: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    for seg in segments:
        if seg["from"] == "START":
            if current:
                chains.append(current)
            current = [seg]
        elif current:
            current.append(seg)
    if current:
        chains.append(current)
    return chains


def compress_chain(chain: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None

    def flush() -> None:
        nonlocal current
        if current is not None and current["items"]:
            current["gain"] = cached_gain(current["items"])
            current["group_sig"] = cached_group_sig(current["fid"], current["items"])
            groups.append(current)
        current = None

    for seg in chain:
        if not seg["items"]:
            continue
        if current is None:
            current = {
                "fid": seg["fid"],
                "items": list(seg["items"]),
                "entry_dmg": seg["segment_dmg"],
                "entry_doors": list(seg["segment_door"]),
                "entry_monsters": [f"x{x}y{y} {NAME.get(r['eid'], r['eid'])}" for r in seg["monsters"] for x, y in [r["pos"]]],
                "entry_door_text": [f"x{x}y{y} {NAME.get(r['eid'], r['eid'])}" for r in seg["doors"] for x, y in [r["pos"]]],
                "route": seg["route"],
            }
            continue
        if is_zero_follow_segment(seg):
            current["items"].extend(seg["items"])
        else:
            flush()
            current = {
                "fid": seg["fid"],
                "items": list(seg["items"]),
                "entry_dmg": seg["segment_dmg"],
                "entry_doors": list(seg["segment_door"]),
                "entry_monsters": [f"x{x}y{y} {NAME.get(r['eid'], r['eid'])}" for r in seg["monsters"] for x, y in [r["pos"]]],
                "entry_door_text": [f"x{x}y{y} {NAME.get(r['eid'], r['eid'])}" for r in seg["doors"] for x, y in [r["pos"]]],
                "route": seg["route"],
            }
    flush()
    return groups


def cached_dominates(a: dict[str, Any], b: dict[str, Any]) -> bool:
    ad = a["entry_doors"]
    bd = b["entry_doors"]
    weak = a["entry_dmg"] <= b["entry_dmg"] and all(x <= y for x, y in zip(ad, bd))
    strict = a["entry_dmg"] < b["entry_dmg"] or any(x < y for x, y in zip(ad, bd))
    return weak and strict


def dedupe_cached(edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_sig: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for edge in edges:
        by_sig[edge["group_sig"]].append(edge)

    out: list[dict[str, Any]] = []
    for variants in by_sig.values():
        merged: dict[tuple[Any, ...], dict[str, Any]] = {}
        for edge in variants:
            key = (
                edge["group_sig"],
                edge["entry_dmg"],
                tuple(edge["entry_doors"]),
                tuple(edge["entry_door_text"]),
                tuple(edge["entry_monsters"]),
                edge.get("from_group"),
                edge.get("from_name"),
            )
            existing = merged.get(key)
            if existing is None:
                existing = dict(edge)
                existing["_routes"] = {edge["route"]}
                merged[key] = existing
            else:
                existing["_routes"].add(edge["route"])

        kept: list[dict[str, Any]] = []
        for edge in sorted(merged.values(), key=lambda e: (e["entry_dmg"], e["entry_doors"], cached_group_name(e))):
            if any(cached_dominates(old, edge) for old in kept):
                continue
            kept = [old for old in kept if not cached_dominates(edge, old)]
            edge = dict(edge)
            routes = sorted(edge.pop("_routes", {edge["route"]}))
            edge["route_count"] = len(routes)
            edge["route"] = routes[0]
            kept.append(edge)
        out.extend(kept)
    return sorted(out, key=lambda e: (floor_num(e["fid"]), e["entry_dmg"], e["entry_doors"], cached_group_name(e)))


def write_cached_report(data: dict[str, Any], out_path: str) -> None:
    chains = route_chains(data["segments"])
    compressed = [compress_chain(chain) for chain in chains]

    direct_edges: list[dict[str, Any]] = []
    second_edges: list[dict[str, Any]] = []
    for groups in compressed:
        if not groups:
            continue
        first = dict(groups[0])
        first["from_group"] = "START"
        direct_edges.append(first)
        if len(groups) >= 2:
            second = dict(groups[1])
            second["from_group"] = groups[0]["group_sig"]
            second["from_name"] = cached_group_name(groups[0])
            second_edges.append(second)

    direct = dedupe_cached([e for e in direct_edges if 1 <= floor_num(e["fid"]) <= 10])
    second = dedupe_cached([e for e in second_edges if 1 <= floor_num(e["fid"]) <= 10])
    direct_by_floor: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for edge in direct:
        edge["group_id"] = str(edge["group_sig"])
        direct_by_floor[edge["fid"]].append(edge)

    lines = [
        "# Post-9 压缩资源组拓扑图（两段）",
        "",
        f"> 起点：{data['start_text']}",
        "> 口径：同一路径上遇到第一个资源后，后续连续 0伤害、0门耗、无新门/怪的资源段合并为同一个资源组。",
        "> 本版从已有 atomic graph JSON 压缩生成，不重新跑慢搜索。",
        "",
        "## 静态资源组节点（地图压缩校验）",
        "",
        "| 楼层 | 资源组 | 组内收益 |",
        "|---|---|---|",
    ]
    for fid, groups in static_resource_groups().items():
        for group in groups:
            items = [ResourceItem(pos, eid) for pos, eid in group]
            lines.append(f"| {floor_label(fid)} | {' + '.join(item_label(item) for item in items)} | {gain_text(group_gain(items))} |")

    lines.extend([
        "",
        "## 第一段：START -> 压缩资源组",
        "",
        "| # | 楼层 | 资源组 | 进入伤害 | 进入门耗 Y/B/R | 进入门/怪 | 组内收益 | 来源路径数/示例 |",
        "|---:|---|---|---:|---:|---|---|---|",
    ])
    idx = 1
    for fid in sorted(direct_by_floor, key=floor_num):
        for edge in direct_by_floor[fid]:
            req = list_text(edge["entry_door_text"] + edge["entry_monsters"])
            lines.append(
                f"| {idx} | {floor_label(fid)} | {cached_group_name(edge)} | {edge['entry_dmg']} | "
                f"{'/'.join(str(x) for x in edge['entry_doors'])} | {req} | "
                f"{gain_text(edge['gain'])} | {edge.get('route_count', 1)} 条；{edge['route']} |"
            )
            idx += 1

    lines.extend([
        "",
        "## 第二段：第一段资源组 -> 同路径下一压缩资源组",
        "",
        "| # | 楼层 | from | to | 进入伤害 | 进入门耗 Y/B/R | 进入门/怪 | 组内收益 | 来源路径数/示例 |",
        "|---:|---|---|---|---:|---:|---|---|---|",
    ])
    idx = 1
    for edge in second:
        req = list_text(edge["entry_door_text"] + edge["entry_monsters"])
        lines.append(
            f"| {idx} | {floor_label(edge['fid'])} | {edge.get('from_name', '-')} | {cached_group_name(edge)} | "
            f"{edge['entry_dmg']} | {'/'.join(str(x) for x in edge['entry_doors'])} | {req} | "
            f"{gain_text(edge['gain'])} | {edge.get('route_count', 1)} 条；{edge['route']} |"
        )
        idx += 1

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")
    print(f"wrote {out_path}")
    print(f"direct={len(direct)} second={len(second)}")


def prefix_collected_from_walk(path: str = DETAILED_WALK) -> dict[str, set[tuple[int, int]]]:
    collected: dict[str, set[tuple[int, int]]] = defaultdict(set)
    for fid, positions in atomic_graph.FLOOR_13_COLLECTED.items():
        collected[fid].update(positions)
    if not os.path.exists(path):
        return collected

    current_fid: str | None = None
    section_no = 0
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("## "):
                m_no = re.match(r"##\s+(\d+)\.", line)
                section_no = int(m_no.group(1)) if m_no else section_no
                if section_no >= 9:
                    break
                m_fid = re.search(r"(MT\d+)", line)
                current_fid = m_fid.group(1) if m_fid else None
                continue
            if current_fid is None or section_no <= 0:
                continue
            for x, y in re.findall(r"x(\d+)y(\d+)", line):
                collected[current_fid].add((int(x), int(y)))
    return collected


def static_resource_groups() -> dict[str, list[list[tuple[tuple[int, int], str]]]]:
    collected = prefix_collected_from_walk()
    out: dict[str, list[list[tuple[tuple[int, int], str]]]] = {}
    for fid in sorted((fid for fid in gw.maps if 1 <= floor_num(fid) <= 10), key=floor_num):
        blocks = block_map(fid)
        already = collected.get(fid, set())
        resource_positions = {
            (x, y): eid
            for x, y, t, eid in gw.maps[fid]["bl"]
            if t == 3 and eid in RESOURCE_IDS and (x, y) not in already
        }
        blockers = {
            (x, y)
            for x, y, t, _eid in gw.maps[fid]["bl"]
            if t in {1, 2} and (x, y) not in already
        }
        seen: set[tuple[int, int]] = set()
        groups: list[list[tuple[tuple[int, int], str]]] = []
        for start_pos, start_eid in sorted(resource_positions.items()):
            if start_pos in seen:
                continue
            q = deque([start_pos])
            seen.add(start_pos)
            found: list[tuple[tuple[int, int], str]] = []
            while q:
                pos = q.popleft()
                if pos in resource_positions:
                    found.append((pos, resource_positions[pos]))
                x, y = pos
                for nxt in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if nxt in seen or is_wall(fid, nxt) or nxt in blockers:
                        continue
                    seen.add(nxt)
                    q.append(nxt)
            if found:
                groups.append(sorted(found))
        if groups:
            out[fid] = groups
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=ATOMIC_JSON)
    parser.add_argument("--output", default=OUT_MD)
    args = parser.parse_args()

    data = load_cached_atomic(args.input)
    write_cached_report(data, args.output)


if __name__ == "__main__":
    main()
