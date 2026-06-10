#!/usr/bin/env python3
"""Generate a coordinate-level walk for the delayed Phase1 continuation."""

from __future__ import annotations

import argparse
import os
import re
import sys
from typing import Any


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.chdir(ROOT)

from src.solver import gen_walkthrough as gw
from scripts import fixed_shield_strategy as fixed


IN_WALK = os.path.join("outputs", "walkthroughs", "walkthrough_delayed_phase1_post9_resource.md")
OUT_WALK = os.path.join("outputs", "walkthroughs", "walkthrough_delayed_phase1_post9_resource_detailed.md")

PHASE1_PREFIX_ACTIONS = {
    "phase1 delayed prefix complete": "MT9:shield1+redGem+blueGem:new",
}
FIXED_PREFIX_LABEL = "fixed 4-9 shield prefix + MT9 red/blue gems complete"

NAMES = {
    "greenSlime": "绿史莱姆",
    "redSlime": "红史莱姆",
    "bat": "小蝙蝠",
    "skeleton": "骷髅人",
    "skeletonSoldier": "骷髅士兵",
    "skeletonCaptain": "骷髅队长",
    "bluePriest": "初级法师",
    "yellowGuard": "初级卫兵",
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
    "upFloor": "上楼",
    "downFloor": "下楼",
    "fakeWall": "暗墙",
}

FLOOR = {
    "MT1": "1楼",
    "MT2": "2楼",
    "MT3": "3楼",
    "MT4": "4楼",
    "MT5": "5楼",
    "MT6": "6楼",
    "MT7": "7楼",
    "MT8": "8楼",
    "MT9": "9楼",
    "MT10": "10楼",
}

STATE_RE = re.compile(
    r"HP=(?P<hp>-?\d+) ATK=(?P<atk>-?\d+) DEF=(?P<def>-?\d+) "
    r"YK=(?P<yk>-?\d+) BK=(?P<bk>-?\d+) RK=(?P<rk>-?\d+) "
    r"dmg=(?P<dmg>-?\d+) door=(?P<yd>-?\d+)/(?P<bd>-?\d+)/(?P<rd>-?\d+)"
)


def parse_state(text: str) -> dict[str, int]:
    m = STATE_RE.search(text)
    if not m:
        raise ValueError(f"state not found: {text}")
    return {k: int(v) for k, v in m.groupdict().items()}


def parse_action(label: str) -> tuple[str, list[str], bool]:
    label = label.split("[", 1)[0].strip()
    if label == FIXED_PREFIX_LABEL:
        return "FIXED_PREFIX", [], False
    label = PHASE1_PREFIX_ACTIONS.get(label, label)
    if ":" in label:
        parts = label.split(":")
        fid = parts[0]
        targets = parts[1].split("+")
        flyback = parts[2] == "fb" if len(parts) > 2 else False
        return fid, targets, flyback
    parts = label.split()
    fid = parts[0]
    coordinates = [(int(x), int(y)) for x, y in re.findall(r"x(\d+)y(\d+)", label)]
    if coordinates:
        targets = []
        for x, y in coordinates:
            matches = [eid for bx, by, _kind, eid in gw.maps[fid]["bl"] if bx == x and by == y]
            if not matches:
                raise ValueError(f"map item not found for {fid} x{x}y{y}: {label}")
            targets.append(matches[0])
    else:
        targets = parts[1].split("+")
    flyback = "flyback=True" in label
    return fid, targets, flyback


def parse_free_saturation(label: str) -> list[tuple[str, int, int, str]]:
    return [
        (fid, int(x), int(y), eid)
        for fid, x, y, eid in re.findall(r"(MT\d+) x(\d+)y(\d+) (\w+)", label)
    ]


def parse_compact_walk(path: str = IN_WALK) -> tuple[dict[str, int], list[dict[str, Any]]]:
    lines = open(path, encoding="utf-8").read().splitlines()
    start_state = None
    segments = []
    current_label = None
    for line in lines:
        if line.startswith("## "):
            m = re.match(r"## \d+\. (.+)$", line)
            current_label = m.group(1).strip() if m else None
        elif line.startswith("- HP="):
            state = parse_state(line)
            if current_label and current_label.startswith("4F search start"):
                start_state = state
            elif current_label:
                if current_label.startswith("post9 free supply saturation:"):
                    segments.append({
                        "label": current_label,
                        "fid": "MULTI",
                        "targets": [],
                        "flyback": True,
                        "free_items": parse_free_saturation(current_label),
                        "state": state,
                    })
                    continue
                fid, targets, flyback = parse_action(current_label)
                segments.append({
                    "label": current_label,
                    "fid": fid,
                    "targets": targets,
                    "flyback": flyback,
                    "state": state,
                })
    if start_state is None:
        raise RuntimeError("start state not found")
    return start_state, segments


def state_line(state: dict[str, int]) -> str:
    return (
        f"HP={state['hp']} ATK={state['atk']} DEF={state['def']} "
        f"YK={state['yk']} BK={state['bk']} RK={state['rk']}"
    )


def full_state_line(state: dict[str, int]) -> str:
    return (
        f"{state_line(state)} dmg={state['dmg']} "
        f"door={state['yd']}/{state['bd']}/{state['rd']}"
    )


def step_delta(step: dict[str, Any]) -> str:
    parts = []
    pairs = [
        ("HP", step["hp_before"], step["hp_after"]),
        ("ATK", step["atk_before"], step["atk"]),
        ("DEF", step["def_before"], step["def"]),
        ("YK", step["yk_before"], step["yk"]),
        ("BK", step["bk_before"], step["bk"]),
        ("RK", step["rk_before"], step["rk"]),
    ]
    for name, before, after in pairs:
        if before != after:
            parts.append(f"{name} {before}->{after}")
    return ", ".join(parts)


def classify_step(step: dict[str, Any]) -> str:
    eid = step["eid"]
    name = NAMES.get(eid, eid)
    if eid in {"yellowDoor", "blueDoor", "redDoor"}:
        return f"开{name}"
    if eid in {
        "yellowKey", "blueKey", "redKey", "redPotion", "bluePotion",
        "redGem", "blueGem", "greenGem", "sword1", "shield1",
    }:
        return f"拿{name}"
    if eid in {"upFloor", "downFloor"}:
        return name
    if eid == "fakeWall":
        return "穿暗墙"
    return f"打{name}"


def format_step(step: dict[str, Any]) -> str:
    delta = step_delta(step)
    suffix = f" ({delta})" if delta else ""
    return f"x{step['x']}y{step['y']} {classify_step(step)}{suffix}"


def boss_event_steps(hp: int, atk: int, def_: int, yk: int, bk: int, rk: int) -> list[Any]:
    out: list[Any] = ["x6y5 触发 Boss 战：Boss 退到 x6y1，x6y3 出现墙，周围刷怪"]
    monsters = [
        (5, 4, "skeletonSoldier"),
        (7, 4, "skeletonSoldier"),
        (6, 4, "skeleton"),
        (5, 5, "skeleton"),
        (7, 5, "skeleton"),
        (5, 6, "skeleton"),
        (6, 6, "skeleton"),
        (7, 6, "skeleton"),
    ]
    for x, y, eid in monsters:
        dmg = gw.calc_dmg(eid, atk, def_)
        step = {
            "x": x,
            "y": y,
            "eid": eid,
            "hp_before": hp,
            "hp_after": hp - dmg,
            "atk_before": atk,
            "def_before": def_,
            "yk_before": yk,
            "bk_before": bk,
            "rk_before": rk,
            "atk": atk,
            "def": def_,
            "yk": yk,
            "bk": bk,
            "rk": rk,
        }
        out.append(step)
        hp -= dmg
    out.append("x6y3 墙打开")
    dmg = gw.calc_dmg("skeletonCaptain", atk, def_)
    out.append({
        "x": 6,
        "y": 1,
        "eid": "skeletonCaptain",
        "hp_before": hp,
        "hp_after": hp - dmg,
        "atk_before": atk,
        "def_before": def_,
        "yk_before": yk,
        "bk_before": bk,
        "rk_before": rk,
        "atk": atk,
        "def": def_,
        "yk": yk,
        "bk": bk,
        "rk": rk,
    })
    return out


def reconstruct_segment(prev_state: dict[str, int], collected: dict[str, frozenset], seg: dict[str, Any]):
    fid = seg["fid"]
    targets = seg["targets"]
    flyback = seg["flyback"]
    entrances = gw.FLYBACK_ENTRANCES if flyback else gw.ENTRANCES
    sx, sy = entrances[fid]
    removed = collected.get(fid, frozenset())
    if fid in gw.FLOOR_13_COLLECTED:
        removed = removed | gw.FLOOR_13_COLLECTED[fid]
    target_state = {
        "hp": seg["state"]["hp"],
        "atk": seg["state"]["atk"],
        "def": seg["state"]["def"],
        "yk": seg["state"]["yk"],
        "bk": seg["state"]["bk"],
        "rk": seg["state"]["rk"],
    }
    is_boss = fid == "MT10" and "redDoor" in targets
    path_target_state = dict(target_state)
    if is_boss:
        path_target_state["hp"] = (
            target_state["hp"]
            + gw.boss_event_damage(target_state["atk"], target_state["def"])
            + gw.calc_dmg("skeletonCaptain", target_state["atk"], target_state["def"])
        )
    steps, final, vis_pos = gw.search_with_path(
        gw.maps[fid],
        sx,
        sy,
        prev_state["hp"],
        prev_state["atk"],
        prev_state["def"],
        prev_state["yk"],
        prev_state["bk"],
        prev_state["rk"],
        targets,
        max_iter=500000,
        removed_pos=removed,
        target_state=path_target_state,
    )
    if not steps:
        return None, None
    collected[fid] = removed | vis_pos
    if is_boss:
        reddoor_state = steps[-1]
        steps = list(steps) + boss_event_steps(
            reddoor_state["hp_after"],
            reddoor_state["atk"],
            reddoor_state["def"],
            reddoor_state["yk"],
            reddoor_state["bk"],
            reddoor_state["rk"],
        )
    return steps, collected[fid]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=IN_WALK)
    parser.add_argument("--output", default=OUT_WALK)
    args = parser.parse_args()

    start_state, segments = parse_compact_walk(args.input)
    collected = gw.initial_collected_state()
    lines = [
        "# Delayed Phase1 + Post-9 Resource Group Detailed Walk",
        "",
        f"> start: {full_state_line(start_state)}",
        f"> final: {full_state_line(segments[-1]['state'])}",
        "",
        "说明：这是按 compact walk 逐段重放出的坐标级路线；每段末尾的 dmg/door 与搜索结果对齐。",
        "",
    ]
    prev = start_state
    for idx, seg in enumerate(segments, 1):
        before = dict(prev)
        if seg["fid"] == "FIXED_PREFIX":
            prefix = fixed.replay_route()
            if not prefix["ok"] or not prefix["strict_reachable"]:
                raise RuntimeError(f"fixed prefix replay failed: {prefix['errors']}")
            collected = {
                fid: frozenset((item["x"], item["y"]) for item in positions)
                for fid, positions in prefix["collected"].items()
            }
            lines.append(f"## {idx}. fixed 4-9 shield prefix + MT9 red/blue gems")
            lines.append("")
            by_segment: dict[str, list[dict[str, Any]]] = {}
            for step in prefix["steps"]:
                by_segment.setdefault(step["segment"], []).append(step)
            for part in prefix["segments"]:
                lines.append(f"### {part['name']}")
                formatted = [
                    f"x{step['x']}y{step['y']} {step['action']}"
                    for step in by_segment.get(part["name"], [])
                ]
                lines.append("- " + "，".join(formatted))
            lines.append(f"- 小结：{full_state_line(seg['state'])}")
            lines.append("")
            prev = seg["state"]
            continue
        if seg["fid"] == "MULTI":
            lines.append(f"## {idx}. post-9 free supply saturation")
            lines.append("")
            formatted = []
            for fid, x, y, eid in seg["free_items"]:
                collected[fid] = collected.get(fid, frozenset()) | frozenset({(x, y)})
                formatted.append(f"{FLOOR.get(fid, fid)} x{x}y{y} {NAMES.get(eid, eid)}")
            lines.append("- " + ", ".join(formatted))
            seg_dmg = seg["state"]["dmg"] - prev["dmg"]
            dy = seg["state"]["yd"] - prev["yd"]
            db = seg["state"]["bd"] - prev["bd"]
            dr = seg["state"]["rd"] - prev["rd"]
            lines.append(
                f"- summary: {full_state_line(seg['state'])}, segment dmg={seg_dmg}, door +{dy}/{db}/{dr}"
            )
            lines.append("")
            prev = seg["state"]
            continue
        if seg["fid"] == "resumed":
            lines.append(f"## {idx}. resumed deferred checkpoint")
            lines.append("")
            lines.append(f"- source: {seg['label']}")
            seg_dmg = seg["state"]["dmg"] - prev["dmg"]
            dy = seg["state"]["yd"] - prev["yd"]
            db = seg["state"]["bd"] - prev["bd"]
            dr = seg["state"]["rd"] - prev["rd"]
            lines.append(
                f"- summary: {full_state_line(seg['state'])}, segment dmg={seg_dmg}, door +{dy}/{db}/{dr}"
            )
            lines.append("")
            prev = seg["state"]
            continue
        steps, _vis = reconstruct_segment(before, collected, seg)
        lines.append(f"## {idx}. {FLOOR.get(seg['fid'], seg['fid'])} {seg['label']}")
        lines.append("")
        if steps is None:
            lines.append("- 重放失败，保留摘要动作。")
        else:
            formatted = []
            for step in steps:
                if isinstance(step, str):
                    formatted.append(step)
                else:
                    formatted.append(format_step(step))
            lines.append("- " + "，".join(formatted))
        seg_dmg = seg["state"]["dmg"] - prev["dmg"]
        dy = seg["state"]["yd"] - prev["yd"]
        db = seg["state"]["bd"] - prev["bd"]
        dr = seg["state"]["rd"] - prev["rd"]
        lines.append(
            f"- 小结：{full_state_line(seg['state'])}，本段 dmg={seg_dmg}，门耗 +{dy}/{db}/{dr}"
        )
        lines.append("")
        prev = seg["state"]

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
