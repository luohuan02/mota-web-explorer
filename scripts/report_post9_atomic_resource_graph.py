"""Build an atomic post-9 resource graph from real floor paths.

The older auto graph treats one target search result as a single resource-group
edge.  This report splits each returned route at every newly encountered
resource, producing prefix edges such as START -> x3y11 yellowKey -> ...
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from typing import Any, Iterable


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
for path in (SCRIPT_DIR, ROOT):
    if path not in sys.path:
        sys.path.insert(0, path)
os.chdir(ROOT)

from scripts import compare_post9_order_variants as variants
from scripts import continue_delayed_phase1_with_post9_resource as delayed
from scripts import post9_auto_resource_group_pareto as auto
from src.solver import gen_walkthrough as gw
from src.solver.full_search import ENTRANCES, FLYBACK_ENTRANCES, FLOOR_13_COLLECTED, calc_dmg, search_with_path


OUT_JSON = os.path.join("outputs", "results", "post9_atomic_resource_graph_from_delayed_prefix.json")
OUT_MD = os.path.join("outputs", "reports", "post9_atomic_resource_graph_from_delayed_prefix.md")

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
}


def collected_for(ent: dict[str, Any], fid: str) -> frozenset[tuple[int, int]]:
    got = set(ent.get("collected", {}).get(fid, frozenset()))
    got.update(FLOOR_13_COLLECTED.get(fid, frozenset()))
    return frozenset(got)


def state_text(ent: dict[str, Any]) -> str:
    return (
        f"HP={ent['hp']} ATK={ent['atk']} DEF={ent['def']} "
        f"YK={ent['yk']} BK={ent['bk']} RK={ent['rk']} "
        f"dmg={ent.get('_dmg', 0)} door={ent.get('_yd', 0)}/{ent.get('_bd', 0)}/{ent.get('_rd', 0)}"
    )


def pos_label(fid: str, pos: tuple[int, int], eid: str) -> str:
    x, y = pos
    return f"{fid} x{x}y{y} {NAME.get(eid, eid)}"


def step_kind(fid: str, step: dict[str, Any]) -> tuple[int, str]:
    for x, y, t, eid in gw.maps[fid]["bl"]:
        if x == step["x"] and y == step["y"]:
            return t, eid
    return -1, step.get("eid", "")


def fmt_records(records: Iterable[dict[str, Any]]) -> str:
    vals = []
    for r in records:
        x, y = r["pos"]
        vals.append(f"x{x}y{y} {NAME.get(r['eid'], r['eid'])}")
    return "，".join(vals) if vals else "-"


def clean_action(text: str) -> str:
    out = text or "-"
    out = out.replace("flyback=True", "飞回=True")
    out = out.replace("flyback=False", "飞回=False")
    out = out.replace("pure-no-redGem", "纯蓝宝石分支")
    out = out.replace("pure-no-blueGem", "纯红宝石分支")
    out = out.replace("[progress]", "[进楼]")
    for eid, name in sorted(NAME.items(), key=lambda kv: len(kv[0]), reverse=True):
        out = out.replace(eid, name)
    return out


def target_state_for_path(curr: dict[str, Any], fid: str, targets: list[str]) -> dict[str, int]:
    target_state = {
        "hp": curr["hp"],
        "atk": curr["atk"],
        "def": curr["def"],
        "yk": curr["yk"],
        "bk": curr["bk"],
        "rk": curr["rk"],
    }
    if fid == "MT10" and "redDoor" in targets:
        target_state["hp"] += gw.boss_event_damage(curr["atk"], curr["def"])
        target_state["hp"] += calc_dmg("skeletonCaptain", curr["atk"], curr["def"])
    return target_state


def reconstruct_steps(
    prev: dict[str, Any],
    curr: dict[str, Any],
    fid: str,
    targets: list[str],
    flyback: bool,
    max_iter: int,
) -> tuple[list[dict[str, Any]], dict[str, Any] | None, str]:
    entrances = FLYBACK_ENTRANCES if flyback else ENTRANCES
    sx, sy = entrances[fid]
    removed = set(collected_for(prev, fid))
    target_state = target_state_for_path(curr, fid, targets)
    steps, final, _vis = search_with_path(
        gw.maps[fid],
        sx,
        sy,
        prev["hp"],
        prev["atk"],
        prev["def"],
        prev["yk"],
        prev["bk"],
        prev["rk"],
        targets,
        max_iter=max_iter,
        removed_pos=frozenset(removed),
        target_state=target_state,
    )
    if not steps:
        return [], None, "no-path"
    mismatch = []
    if final:
        for key in ("atk", "def", "yk", "bk", "rk"):
            if final.get(key) != target_state.get(key):
                mismatch.append(key)
        if final.get("hp") != target_state.get("hp"):
            mismatch.append("hp")
    return steps, final, ",".join(mismatch)


def split_steps(
    prev: dict[str, Any],
    curr: dict[str, Any],
    fid: str,
    route_label: str,
    steps: list[dict[str, Any]],
    include_terminal: bool = True,
) -> list[dict[str, Any]]:
    segments: list[dict[str, Any]] = []
    current_from = "START"
    pending_items: list[dict[str, Any]] = []
    pending_doors: list[dict[str, Any]] = []
    pending_monsters: list[dict[str, Any]] = []
    seg_dmg = 0
    seg_doors = [0, 0, 0]
    total_dmg = prev.get("_dmg", 0)
    total_doors = [prev.get("_yd", 0), prev.get("_bd", 0), prev.get("_rd", 0)]

    def flush(step: dict[str, Any], eid: str, terminal: bool = False) -> None:
        nonlocal current_from, pending_items, pending_doors, pending_monsters
        nonlocal seg_dmg, seg_doors, total_dmg, total_doors
        pos = (step["x"], step["y"])
        to_node = pos_label(fid, pos, eid)
        total_dmg += seg_dmg
        total_doors = [a + b for a, b in zip(total_doors, seg_doors)]
        after = {
            "hp": step["hp_after"],
            "atk": step["atk"],
            "def": step["def"],
            "yk": step["yk"],
            "bk": step["bk"],
            "rk": step["rk"],
            "dmg": total_dmg,
            "yd": total_doors[0],
            "bd": total_doors[1],
            "rd": total_doors[2],
        }
        segments.append({
            "route": clean_action(route_label),
            "fid": fid,
            "from": current_from,
            "to": to_node,
            "terminal": terminal,
            "segment_dmg": seg_dmg,
            "segment_door": list(seg_doors),
            "items": list(pending_items),
            "doors": list(pending_doors),
            "monsters": list(pending_monsters),
            "after": after,
        })
        current_from = to_node
        pending_items = []
        pending_doors = []
        pending_monsters = []
        seg_dmg = 0
        seg_doors = [0, 0, 0]

    for step in steps:
        t, eid = step_kind(fid, step)
        rec = {"pos": (step["x"], step["y"]), "eid": eid}
        if t == 1:
            pending_monsters.append(rec)
            seg_dmg += max(0, step["hp_before"] - step["hp_after"])
        elif t == 2:
            pending_doors.append(rec)
            if eid == "yellowDoor":
                seg_doors[0] += 1
            elif eid == "blueDoor":
                seg_doors[1] += 1
            elif eid == "redDoor":
                seg_doors[2] += 1
        elif t == 3:
            pending_items.append(rec)
            if eid in RESOURCE_IDS:
                flush(step, eid)
        elif include_terminal and t == 4 and eid in {"upFloor", "downFloor"}:
            flush(step, eid, terminal=True)
    return segments


def all_target_edges(ent: dict[str, Any], max_iter: int) -> list[dict[str, Any]]:
    by_floor_eid: dict[tuple[str, str], set[tuple[int, int]]] = defaultdict(set)
    for target in auto.TARGETS:
        if target.pos not in auto.collected_for(ent, target.fid):
            by_floor_eid[(target.fid, target.eid)].add(target.pos)

    edges: list[dict[str, Any]] = []
    for (fid, eid), positions in sorted(by_floor_eid.items(), key=lambda item: (int(item[0][0][2:]), item[0][1])):
        for edge in auto.exact_item_edges(ent, fid, eid, positions, max_iter=max_iter):
            if "pure-no-" in edge.get("_last_action", ""):
                continue
            edges.append(edge)
    edges.extend(auto.progress_edges(ent, max_iter=max_iter))
    return edges


def build_prefix_graph(start: dict[str, Any], max_iter: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    route_edges = all_target_edges(start, max_iter=max_iter)
    segments: list[dict[str, Any]] = []
    route_rows: list[dict[str, Any]] = []
    for edge in route_edges:
        fid, targets, flyback = edge.get("_step_info", (None, [], True))
        if not fid:
            continue
        steps, final, mismatch = reconstruct_steps(start, edge, fid, targets, flyback, max_iter=max_iter)
        route_rows.append({
            "route": clean_action(edge.get("_last_action", "")),
            "kind": edge.get("_edge_kind", "-"),
            "state": state_text(edge),
            "step_count": len(steps),
            "mismatch": mismatch,
        })
        if not steps:
            continue
        segments.extend(split_steps(start, edge, fid, edge.get("_last_action", ""), steps))
    return segments, route_rows


def unique_direct_segments(segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    best: dict[tuple[str, str, tuple[str, ...], tuple[str, ...]], dict[str, Any]] = {}
    for seg in segments:
        if seg["from"] != "START":
            continue
        sig = (
            seg["from"],
            seg["to"],
            tuple(f"{r['pos']}:{r['eid']}" for r in seg["doors"]),
            tuple(f"{r['pos']}:{r['eid']}" for r in seg["monsters"]),
        )
        old = best.get(sig)
        key = (seg["segment_dmg"], seg["segment_door"], -seg["after"]["hp"])
        old_key = (old["segment_dmg"], old["segment_door"], -old["after"]["hp"]) if old else None
        if old is None or key < old_key:
            best[sig] = seg
    return sorted(best.values(), key=lambda s: (s["fid"], s["segment_dmg"], s["segment_door"], s["to"]))


def validate_best_route(start: dict[str, Any], max_iter: int) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    best_actions = dict(variants.VARIANTS)["key-red-3f-1f"]
    final, chain = variants.apply_sequence(start, best_actions)
    rows: list[dict[str, Any]] = []
    for idx in range(1, len(chain)):
        prev = chain[idx - 1]["entry"]
        curr = chain[idx]["entry"]
        label = chain[idx]["label"]
        fid, targets, flyback = curr.get("_step_info", (None, [], True))
        steps, final_state, mismatch = reconstruct_steps(prev, curr, fid, targets, flyback, max_iter=max_iter)
        segments = split_steps(prev, curr, fid, label, steps) if steps else []
        rows.append({
            "index": idx,
            "label": label,
            "fid": fid,
            "targets": targets,
            "state": state_text(curr),
            "step_count": len(steps),
            "segment_count": len(segments),
            "atomic_targets": [seg["to"] for seg in segments],
            "mismatch": mismatch,
            "ok": bool(steps) and mismatch == "",
        })
    return final, rows


def write_outputs(data: dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    lines = [
        "# Post-9 原子资源组图",
        "",
        f"> 起点：{data['start_text']}",
        f"> 一阶路径拆分段数：{len(data['segments'])}",
        f"> 直连原子资源边数：{len(data['direct_segments'])}",
        "",
        "说明：这里先对每个未拿资源坐标做真实楼层寻路，再按路径上首次遇到的资源逐段切开。"
        "因此 `8F 大包`、`7F 红宝石+钥匙` 这类混合包会拆成多个前缀边。",
        "",
        "## 直连原子资源边",
        "",
        "| # | from | to | 段伤害 | 段门耗 | 到达状态 | 本段资源 | 本段门 | 本段怪 | 来源路径 |",
        "|---:|---|---|---:|---:|---|---|---|---|---|",
    ]
    for idx, seg in enumerate(data["direct_segments"], 1):
        after = seg["after"]
        lines.append(
            f"| {idx} | {seg['from']} | {seg['to']} | {seg['segment_dmg']} | "
            f"{'/'.join(str(x) for x in seg['segment_door'])} | "
            f"HP={after['hp']} ATK={after['atk']} DEF={after['def']} YK={after['yk']} BK={after['bk']} RK={after['rk']} "
            f"dmg={after['dmg']} door={after['yd']}/{after['bd']}/{after['rd']} | "
            f"{fmt_records(seg['items'])} | {fmt_records(seg['doors'])} | {fmt_records(seg['monsters'])} | {seg['route']} |"
        )

    lines.extend([
        "",
        "## 前缀链拆分段",
        "",
        "| # | 来源路径 | from | to | 段伤害 | 段门耗 | 本段资源 | 本段门 | 本段怪 |",
        "|---:|---|---|---|---:|---:|---|---|---|",
    ])
    for idx, seg in enumerate(data["segments"], 1):
        lines.append(
            f"| {idx} | {seg['route']} | {seg['from']} | {seg['to']} | {seg['segment_dmg']} | "
            f"{'/'.join(str(x) for x in seg['segment_door'])} | "
            f"{fmt_records(seg['items'])} | {fmt_records(seg['doors'])} | {fmt_records(seg['monsters'])} |"
        )

    lines.extend([
        "",
        "## 延迟最优路线验证",
        "",
        f"> final: {data['best_final_text']}",
        "",
        "| # | 高层动作 | 拆分段数 | 原子目标 | 验证 | 状态 |",
        "|---:|---|---:|---|---|---|",
    ])
    for row in data["validation"]:
        ok = "OK" if row["ok"] else f"FAIL({row['mismatch'] or 'no-path'})"
        targets = " -> ".join(row["atomic_targets"]) or "-"
        lines.append(
            f"| {row['index']} | {row['label']} | {row['segment_count']} | {targets} | {ok} | {row['state']} |"
        )

    os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
    with open(OUT_MD, "w", encoding="utf-8-sig") as f:
        f.write("\n".join(lines).rstrip() + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase1-expansions", type=int, default=300)
    parser.add_argument("--max-iter", type=int, default=500000)
    args = parser.parse_args()

    start, _phase1 = delayed.find_candidate(args.phase1_expansions)
    segments, route_rows = build_prefix_graph(start, max_iter=args.max_iter)
    direct = unique_direct_segments(segments)
    best_final, validation = validate_best_route(start, max_iter=args.max_iter)
    data = {
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
        },
        "start_text": state_text(start),
        "route_edges": route_rows,
        "segments": segments,
        "direct_segments": direct,
        "best_final_text": state_text(best_final),
        "validation": validation,
    }
    write_outputs(data)
    print(f"wrote {OUT_JSON}")
    print(f"wrote {OUT_MD}")
    print(f"start: {state_text(start)}")
    print(f"segments: {len(segments)} direct: {len(direct)}")
    print(f"validation: {sum(1 for r in validation if r['ok'])}/{len(validation)} OK")


if __name__ == "__main__":
    main()
