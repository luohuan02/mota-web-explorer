#!/usr/bin/env python3
"""Replay and validate the fixed 4F-9F shield route.

This file intentionally does not replace the current search strategy.  It is a
small executable record for the hand-written first-stage route so it can be
used later as a seed or as a comparison target for the Pareto search.
"""

from __future__ import annotations

# Allow scripts to import project-root modules after being moved under scripts/.
import os as _codex_os
import sys as _codex_sys
_codex_root = _codex_os.path.dirname(_codex_os.path.dirname(_codex_os.path.abspath(__file__)))
if _codex_root not in _codex_sys.path:
    _codex_sys.path.insert(0, _codex_root)

import json
import os
from collections import deque
from copy import deepcopy

from src.solver.full_search import FLOOR_13_COLLECTED, calc_dmg, load_data


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

STATE_KEYS = ("hp", "atk", "def", "yk", "bk", "rk")

ITEM_NAMES = {
    "yellowDoor": "黄门",
    "blueDoor": "蓝门",
    "redDoor": "红门",
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
    "greenSlime": "绿史莱姆",
    "redSlime": "红史莱姆",
    "bat": "小蝙蝠",
    "bluePriest": "初级法师",
    "skeleton": "骷髅人",
    "skeletonSoldier": "骷髅士兵",
    "skeletonCaptain": "骷髅队长",
    "upFloor": "上楼",
    "downFloor": "下楼",
    "fakeWall": "暗墙",
}

TYPE_NAMES = {
    1: "monster",
    2: "door",
    3: "item",
    4: "terrain",
}


ROUTE = [
    {
        "name": "4F 起点到 5F",
        "floor": "MT4",
        "start": (11, 10),
        "actions": [
            (11, 8, "yellowDoor"),
            (3, 7, "greenSlime"),
            (1, 7, "redSlime"),
            (1, 8, "yellowDoor"),
            (1, 11, "upFloor"),
        ],
        "exit_to": ("MT5", (1, 11)),
        "expected_user": {"hp": 852, "atk": 10, "def": 10, "yk": 2, "bk": 1, "rk": 0},
    },
    {
        "name": "5F 拿铁剑并回 4F",
        "floor": "MT5",
        "start": (1, 11),
        "actions": [
            (6, 8, "greenSlime"),
            (7, 6, "greenSlime"),
            (11, 7, "redSlime"),
            (8, 9, "yellowDoor"),
            (9, 11, "fakeWall"),
            (11, 11, "sword1"),
            (11, 2, "redSlime"),
            (10, 1, "yellowDoor"),
            (8, 2, "greenSlime"),
            (8, 3, "yellowKey"),
            (8, 4, "yellowKey"),
            (9, 3, "yellowKey"),
            (9, 4, "yellowKey"),
            (1, 11, "downFloor"),
        ],
        "exit_to": ("MT4", (1, 11)),
        "expected_user": {"hp": 726, "atk": 20, "def": 10, "yk": 2, "bk": 1, "rk": 0},
    },
    {
        "name": "回 4F 拿红宝石和 3 黄钥匙",
        "floor": "MT4",
        "start": (1, 11),
        "actions": [
            (8, 8, "yellowDoor"),
            (8, 9, "bluePriest"),
            (9, 10, "redPotion"),
            (7, 10, "redGem"),
            (4, 8, "yellowDoor"),
            (4, 9, "bat"),
            (3, 10, "greenSlime"),
            (3, 11, "yellowKey"),
            (5, 10, "yellowKey"),
            (5, 11, "yellowKey"),
            (1, 11, "upFloor"),
        ],
        "exit_to": ("MT5", (1, 11)),
        "expected_user": {"hp": 652, "atk": 21, "def": 10, "yk": 5, "bk": 1, "rk": 0},
    },
    {
        "name": "5F 继续上 6F",
        "floor": "MT5",
        "start": (1, 11),
        "actions": [
            (6, 4, "bat"),
            (6, 2, "yellowKey"),
            (5, 1, "yellowDoor"),
            (4, 1, "redSlime"),
            (4, 4, "yellowDoor"),
            (4, 6, "bat"),
            (1, 5, "yellowKey"),
            (1, 6, "yellowKey"),
            (3, 3, "bat"),
            (2, 3, "yellowDoor"),
            (1, 1, "upFloor"),
        ],
        "exit_to": ("MT6", (1, 1)),
        "expected_user": {"hp": 548, "atk": 21, "def": 10, "yk": 5, "bk": 1, "rk": 0},
    },
    {
        "name": "6F 换钥匙并上 7F",
        "floor": "MT6",
        "start": (1, 1),
        "actions": [
            (3, 6, "redSlime"),
            (4, 6, "bluePriest"),
            (6, 6, "yellowKey"),
            (5, 4, "yellowDoor"),
            (4, 3, "redSlime"),
            (4, 2, "yellowKey"),
            (4, 1, "yellowKey"),
            (3, 2, "yellowKey"),
            (3, 1, "yellowKey"),
            (7, 8, "yellowDoor"),
            (8, 8, "yellowDoor"),
            (10, 8, "yellowDoor"),
            (11, 9, "redSlime"),
            (11, 11, "upFloor"),
        ],
        "exit_to": ("MT7", (11, 11)),
        "expected_user": {"hp": 400, "atk": 21, "def": 10, "yk": 6, "bk": 1, "rk": 0},
    },
    {
        "name": "7F 拿红宝石并上 8F",
        "floor": "MT7",
        "start": (11, 11),
        "actions": [
            (11, 7, "yellowDoor"),
            (4, 6, "bluePriest"),
            (3, 5, "yellowDoor"),
            (3, 3, "bat"),
            (3, 2, "redPotion"),
            (3, 1, "redGem"),
            (2, 6, "skeletonSoldier"),
            (1, 5, "yellowDoor"),
            (1, 1, "upFloor"),
        ],
        "exit_to": ("MT8", (1, 1)),
        "expected_user": {"hp": 124, "atk": 22, "def": 10, "yk": 3, "bk": 1, "rk": 0},
    },
    {
        "name": "8F 直上 9F",
        "floor": "MT8",
        "start": (1, 1),
        "actions": [
            (3, 1, "yellowDoor"),
            (4, 1, "yellowDoor"),
            (6, 3, "yellowDoor"),
            (5, 4, "yellowKey"),
            (4, 4, "yellowKey"),
            (3, 4, "yellowKey"),
            (6, 1, "upFloor"),
        ],
        "exit_to": ("MT9", (6, 1)),
        "expected_user": {"hp": 124, "atk": 22, "def": 10, "yk": 3, "bk": 1, "rk": 0},
    },
    {
        "name": "9F 拿铁盾",
        "floor": "MT9",
        "start": (6, 1),
        "actions": [
            (8, 1, "yellowDoor"),
            (9, 1, "greenSlime"),
            (11, 1, "redPotion"),
            (10, 5, "fakeWall"),
            (9, 7, "shield1"),
        ],
        "expected_user": {"hp": 166, "atk": 22, "def": 10, "yk": 2, "bk": 1, "rk": 0},
        "expected_note": "User note kept as-is; shield1 changes DEF by +10, so the mechanical result should be DEF=20.",
    },
    {
        "name": "9F 拿红蓝宝石开头",
        "floor": "MT9",
        "start": (9, 7),
        "actions": [
            (9, 4, "yellowDoor"),
            (8, 4, "yellowDoor"),
            (7, 4, "yellowKey"),
            (6, 5, "redGem"),
            (5, 4, "yellowKey"),
            (4, 5, "yellowDoor"),
            (3, 5, "bat"),
            (2, 4, "yellowKey"),
            (1, 5, "blueGem"),
        ],
        "expected_mechanical": {"hp": 148, "atk": 23, "def": 21, "yk": 2, "bk": 1, "rk": 0},
    },
]


def block_map(maps):
    return {
        fid: {(x, y): (t, eid) for x, y, t, eid in data["bl"]}
        for fid, data in maps.items()
    }


def initial_state(hero):
    return {
        "floor": hero["f"],
        "x": hero["x"],
        "y": hero["y"],
        "hp": hero["h"],
        "atk": hero["a"],
        "def": hero["d"],
        "yk": hero.get("yk", 0),
        "bk": hero.get("bk", 0),
        "rk": hero.get("rk", 0),
    }


def empty_collected():
    return {fid: set(pos_set) for fid, pos_set in FLOOR_13_COLLECTED.items()}


def is_wall(maps, blocks, cleared, fid, x, y, target=None, relaxed=False):
    data = maps[fid]
    width = data["W"]
    height = data["H"]
    if x <= 0 or y <= 0 or x >= width - 1 or y >= height - 1:
        return True

    pos = (x, y)
    if pos == target:
        return False
    if pos in cleared.get(fid, set()):
        return False

    block = blocks[fid].get(pos)
    if block is not None:
        if relaxed:
            return False
        t, eid = block
        return not (t == 4 and eid in ("upFloor", "downFloor"))

    return data["m"][y][x] == 1


def bfs_path(maps, blocks, cleared, fid, start, target, relaxed=False):
    if start == target:
        return [start]
    queue = deque([start])
    parent = {start: None}
    while queue:
        cx, cy = queue.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = cx + dx, cy + dy
            nxt = (nx, ny)
            if nxt in parent:
                continue
            if is_wall(maps, blocks, cleared, fid, nx, ny, target=target, relaxed=relaxed):
                continue
            parent[nxt] = (cx, cy)
            if nxt == target:
                path = [nxt]
                cur = (cx, cy)
                while cur is not None:
                    path.append(cur)
                    cur = parent[cur]
                path.reverse()
                return path
            queue.append(nxt)
    return None


def blockers_on_path(blocks, cleared, fid, path, target):
    blockers = []
    if not path:
        return blockers
    for pos in path[1:-1]:
        if pos in cleared.get(fid, set()):
            continue
        if pos in blocks[fid]:
            t, eid = blocks[fid][pos]
            if not (t == 4 and eid in ("upFloor", "downFloor")):
                blockers.append({"x": pos[0], "y": pos[1], "type": TYPE_NAMES[t], "eid": eid})
    if target in blocks[fid]:
        # The target itself is expected to be consumed by the current action, so
        # it is not a missing intermediate blocker.
        pass
    return blockers


def apply_action(state, t, eid):
    before = {key: state[key] for key in STATE_KEYS}
    error = None

    if t == 1:
        damage = calc_dmg(eid, state["atk"], state["def"])
        if damage == float("inf"):
            error = f"Cannot damage {eid} with ATK={state['atk']} DEF={state['def']}"
        elif state["hp"] - damage <= 0:
            error = f"Death on {eid}: damage={damage}, HP={state['hp']}"
        else:
            state["hp"] -= damage
    elif t == 2:
        if eid == "yellowDoor":
            if state["yk"] <= 0:
                error = "No yellow key"
            else:
                state["yk"] -= 1
        elif eid == "blueDoor":
            if state["bk"] <= 0:
                error = "No blue key"
            else:
                state["bk"] -= 1
        elif eid == "redDoor":
            if state["rk"] <= 0:
                error = "No red key"
            else:
                state["rk"] -= 1
    elif t == 3:
        if eid == "yellowKey":
            state["yk"] += 1
        elif eid == "blueKey":
            state["bk"] += 1
        elif eid == "redKey":
            state["rk"] += 1
        elif eid == "redPotion":
            state["hp"] += 50
        elif eid == "bluePotion":
            state["hp"] += 200
        elif eid == "redGem":
            state["atk"] += 1
        elif eid == "blueGem":
            state["def"] += 1
        elif eid == "greenGem":
            state["atk"] += 5
        elif eid.startswith("sword"):
            state["atk"] += 10
        elif eid.startswith("shield"):
            state["def"] += 10
        else:
            error = f"Unknown item {eid}"
    elif t == 4:
        pass
    else:
        error = f"Unknown block type {t}"

    after = {key: state[key] for key in STATE_KEYS}
    return before, after, error


def action_text(t, eid):
    name = ITEM_NAMES.get(eid, eid)
    if t == 1:
        return f"击杀{name}"
    if t == 2:
        return f"开{name}"
    if t == 3:
        return f"拾取{name}"
    if eid == "upFloor":
        return "上楼"
    if eid == "downFloor":
        return "下楼"
    if eid == "fakeWall":
        return "穿暗墙"
    return f"通过{name}"


def state_only(state):
    return {key: state[key] for key in STATE_KEYS}


def state_str(state):
    return (
        f"HP={state['hp']} ATK={state['atk']} DEF={state['def']} "
        f"YK={state['yk']} BK={state['bk']} RK={state['rk']}"
    )


def delta_str(before, after):
    parts = []
    labels = {"hp": "HP", "atk": "ATK", "def": "DEF", "yk": "YK", "bk": "BK", "rk": "RK"}
    for key in STATE_KEYS:
        if before[key] != after[key]:
            parts.append(f"{labels[key]}={before[key]}->{after[key]}")
    return " ".join(parts)


def compare_expected(actual, expected):
    return {key: (actual.get(key), expected.get(key)) for key in STATE_KEYS if actual.get(key) != expected.get(key)}


def replay_route():
    hero, maps = load_data()
    blocks = block_map(maps)
    cleared = empty_collected()
    collected = empty_collected()
    state = initial_state(hero)
    all_steps = []
    segment_results = []
    warnings = []
    errors = []

    for segment in ROUTE:
        seg_name = segment["name"]
        seg_floor = segment["floor"]
        seg_start = tuple(segment["start"])
        seg_warnings = []
        seg_errors = []

        if state["floor"] != seg_floor or (state["x"], state["y"]) != seg_start:
            msg = (
                f"{seg_name}: start mismatch, current "
                f"{state['floor']} ({state['x']},{state['y']}) vs expected {seg_floor} {seg_start}"
            )
            seg_warnings.append(msg)
            warnings.append(msg)
            state["floor"] = seg_floor
            state["x"], state["y"] = seg_start

        for x, y, expected_eid in segment["actions"]:
            pos = (x, y)
            actual_block = blocks[seg_floor].get(pos)
            if actual_block is None:
                msg = f"{seg_name}: no block at {seg_floor} ({x},{y}), expected {expected_eid}"
                seg_errors.append(msg)
                errors.append(msg)
                continue

            t, eid = actual_block
            if eid != expected_eid:
                msg = f"{seg_name}: eid mismatch at {seg_floor} ({x},{y}), map={eid}, route={expected_eid}"
                seg_errors.append(msg)
                errors.append(msg)

            start_pos = (state["x"], state["y"])
            strict_path = bfs_path(maps, blocks, cleared, seg_floor, start_pos, pos, relaxed=False)
            relaxed_path = None
            missing = []
            if strict_path is None:
                relaxed_path = bfs_path(maps, blocks, cleared, seg_floor, start_pos, pos, relaxed=True)
                missing = blockers_on_path(blocks, cleared, seg_floor, relaxed_path, pos) if relaxed_path else []
                msg = f"{seg_name}: cannot strictly reach {seg_floor} ({x},{y}) {eid} from {start_pos}"
                if missing:
                    missing_desc = ", ".join(
                        f"({b['x']},{b['y']}) {b['eid']}" for b in missing
                    )
                    msg += f"; missing intermediate actions: {missing_desc}"
                seg_warnings.append(msg)
                warnings.append(msg)

            before, after, action_error = apply_action(state, t, eid)
            if action_error:
                msg = f"{seg_name}: {action_error} at {seg_floor} ({x},{y}) {eid}"
                seg_errors.append(msg)
                errors.append(msg)

            cleared.setdefault(seg_floor, set()).add(pos)
            if t in (1, 2, 3):
                collected.setdefault(seg_floor, set()).add(pos)
            state["x"], state["y"] = x, y

            step = {
                "segment": seg_name,
                "floor": seg_floor,
                "x": x,
                "y": y,
                "type": TYPE_NAMES.get(t, str(t)),
                "eid": eid,
                "action": action_text(t, eid),
                "state_before": before,
                "state_after": after,
                "strict_reachable": strict_path is not None,
                "path": strict_path,
                "relaxed_path": relaxed_path,
                "missing_intermediate": missing,
                "error": action_error,
            }
            all_steps.append(step)

        if "exit_to" in segment:
            next_floor, next_pos = segment["exit_to"]
            state["floor"] = next_floor
            state["x"], state["y"] = next_pos

        actual = state_only(state)
        expected_user = segment.get("expected_user")
        expected_mechanical = segment.get("expected_mechanical")
        segment_result = {
            "name": seg_name,
            "floor": seg_floor,
            "actual": deepcopy(actual),
            "expected_user": expected_user,
            "expected_mechanical": expected_mechanical,
            "expected_note": segment.get("expected_note"),
            "user_diff": compare_expected(actual, expected_user) if expected_user else {},
            "mechanical_diff": compare_expected(actual, expected_mechanical) if expected_mechanical else {},
            "warnings": seg_warnings,
            "errors": seg_errors,
        }
        segment_results.append(segment_result)

    result = {
        "ok": not errors,
        "strict_reachable": not warnings,
        "initial_state": {
            "floor": hero["f"],
            "x": hero["x"],
            "y": hero["y"],
            "hp": hero["h"],
            "atk": hero["a"],
            "def": hero["d"],
            "yk": hero.get("yk", 0),
            "bk": hero.get("bk", 0),
            "rk": hero.get("rk", 0),
        },
        "final_state": deepcopy(state),
        "segments": segment_results,
        "steps": all_steps,
        "warnings": warnings,
        "errors": errors,
        "collected": {
            fid: [{"x": x, "y": y} for x, y in sorted(positions)]
            for fid, positions in collected.items()
        },
    }
    return result


def json_default(obj):
    if isinstance(obj, set):
        return sorted(obj)
    if isinstance(obj, tuple):
        return list(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def write_json(result, path=os.path.join("outputs", "results", "fixed_shield_strategy.json")):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=json_default)


def write_markdown(result, path=os.path.join("outputs", "reports", "fixed_shield_strategy.md")):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    lines = []
    lines.append("# 4-9 固定拿盾路线校验")
    lines.append("")
    lines.append(f"- 机制执行: {'OK' if result['ok'] else 'FAILED'}")
    lines.append(f"- 严格可达: {'OK' if result['strict_reachable'] else '有警告'}")
    lines.append(f"- 初始: {state_str(result['initial_state'])}")
    lines.append(f"- 最终: {state_str(result['final_state'])}")
    lines.append("")

    by_segment = {}
    for step in result["steps"]:
        by_segment.setdefault(step["segment"], []).append(step)

    for segment in result["segments"]:
        lines.append(f"## {segment['name']}")
        lines.append("")
        for step in by_segment.get(segment["name"], []):
            before = step["state_before"]
            after = step["state_after"]
            delta = delta_str(before, after)
            reach = "" if step["strict_reachable"] else " [可达性警告]"
            delta_part = f" {delta}" if delta else ""
            lines.append(
                f"- {step['floor']} ({step['x']},{step['y']}) "
                f"{step['action']} {step['eid']}{delta_part}{reach}"
            )
            if step["missing_intermediate"]:
                missing = ", ".join(
                    f"({b['x']},{b['y']}) {b['eid']}" for b in step["missing_intermediate"]
                )
                lines.append(f"  - 缺少中间动作: {missing}")
        lines.append(f"  => {state_str(segment['actual'])}")
        if segment.get("expected_user"):
            diff = segment["user_diff"]
            status = "OK" if not diff else f"DIFF {diff}"
            lines.append(f"  - 用户记录对比: {status}")
        if segment.get("expected_mechanical"):
            diff = segment["mechanical_diff"]
            status = "OK" if not diff else f"DIFF {diff}"
            lines.append(f"  - 机制预期对比: {status}")
        if segment.get("expected_note"):
            lines.append(f"  - 备注: {segment['expected_note']}")
        if segment["warnings"]:
            lines.append("  - 警告:")
            for msg in segment["warnings"]:
                lines.append(f"    - {msg}")
        if segment["errors"]:
            lines.append("  - 错误:")
            for msg in segment["errors"]:
                lines.append(f"    - {msg}")
        lines.append("")

    if result["warnings"]:
        lines.append("## 可达性警告汇总")
        lines.append("")
        for msg in result["warnings"]:
            lines.append(f"- {msg}")
        lines.append("")

    if result["errors"]:
        lines.append("## 错误汇总")
        lines.append("")
        for msg in result["errors"]:
            lines.append(f"- {msg}")
        lines.append("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")


def print_summary(result):
    print("Fixed 4F-9F shield route validation")
    print(f"Mechanics: {'OK' if result['ok'] else 'FAILED'}")
    print(f"Strict reachability: {'OK' if result['strict_reachable'] else 'WARNINGS'}")
    print(f"Initial: {state_str(result['initial_state'])}")
    print(f"Final:   {state_str(result['final_state'])}")
    print("")
    for segment in result["segments"]:
        user_diff = segment.get("user_diff") or {}
        mech_diff = segment.get("mechanical_diff") or {}
        status = []
        if segment["errors"]:
            status.append("errors")
        if segment["warnings"]:
            status.append("reach-warnings")
        if user_diff:
            status.append("user-diff")
        if mech_diff:
            status.append("mechanical-diff")
        status_text = ", ".join(status) if status else "ok"
        print(f"- {segment['name']}: {state_str(segment['actual'])} [{status_text}]")
    if result["warnings"]:
        print("")
        print("Warnings:")
        for msg in result["warnings"]:
            print(f"- {msg}")
    if result["errors"]:
        print("")
        print("Errors:")
        for msg in result["errors"]:
            print(f"- {msg}")
    print("")
    print("Wrote outputs/reports/fixed_shield_strategy.md and outputs/results/fixed_shield_strategy.json")


def main():
    result = replay_route()
    write_json(result)
    write_markdown(result)
    print_summary(result)
    if result["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
