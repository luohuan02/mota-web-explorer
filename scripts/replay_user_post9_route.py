#!/usr/bin/env python3
"""Replay the user supplied route after fixed 9F red+blue gems."""

from __future__ import annotations

import json
import os
import sys
from copy import deepcopy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.chdir(ROOT)

import fixed_shield_strategy as fixed
from src.solver.full_search import FLYBACK_ENTRANCES, calc_dmg, load_data
from src.solver import gen_walkthrough as gw


STATE_KEYS = ("hp", "atk", "def", "yk", "bk", "rk")


ROUTE = [
    {
        "name": "6F blue gem",
        "floor": "MT6",
        "points": [(9, 9), (8, 11), (9, 11), (9, 10), (5, 11), (2, 11), (1, 10), (2, 9), (4, 9)],
        "expected": {"hp": 189, "atk": 23, "def": 22, "yk": 1, "bk": 1, "rk": 0},
    },
    {
        "name": "3F blue gem",
        "floor": "MT3",
        "points": [(3, 5), (1, 4), (1, 3), (1, 1), (2, 2), (2, 1)],
        "expected": {"hp": 193, "atk": 23, "def": 23, "yk": 1, "bk": 1, "rk": 0},
    },
    {
        "name": "8F red+blue gems",
        "floor": "MT8",
        "points": [(7, 5), (7, 7), (6, 8), (4, 8), (1, 9), (1, 10), (2, 11), (3, 11), (4, 11), (4, 10), (5, 10), (5, 11)],
        "expected": {"hp": 83, "atk": 24, "def": 24, "yk": 2, "bk": 0, "rk": 0},
    },
    {
        "name": "1F red+blue gems",
        "floor": "MT1",
        "points": [(6, 6), (7, 6), (8, 6), (9, 6), (9, 5), (8, 4), (8, 3), (7, 3), (7, 4)],
        "expected": {"hp": 81, "atk": 25, "def": 25, "yk": 1, "bk": 0, "rk": 0},
    },
    {
        "name": "3F red gem",
        "floor": "MT3",
        "points": [(1, 6), (1, 7), (1, 9), (2, 8), (2, 9)],
        "expected": {"hp": 97, "atk": 26, "def": 25, "yk": 1, "bk": 0, "rk": 0},
    },
    {
        "name": "5F blue gem",
        "floor": "MT5",
        "points": [(2, 7), (2, 9), (3, 9), (1, 9)],
        "expected": {"hp": 66, "atk": 26, "def": 26, "yk": 2, "bk": 0, "rk": 0},
    },
    {
        "name": "4F blue key",
        "floor": "MT4",
        "points": [(2, 5), (2, 4), (1, 2), (3, 2), (2, 1)],
        "expected": {"hp": 98, "atk": 26, "def": 26, "yk": 2, "bk": 1, "rk": 0},
    },
    {
        "name": "9F up to 10F",
        "floor": "MT9",
        "points": [(7, 6), (7, 10), (6, 11), (3, 11), (2, 10), (1, 11)],
        "exit_to": ("MT10", (1, 10)),
        "expected": {"hp": 136, "atk": 26, "def": 26, "yk": 1, "bk": 0, "rk": 0},
    },
    {
        "name": "10F blue gem",
        "floor": "MT10",
        "points": [(1, 9), (1, 6), (2, 6)],
        "expected": {"hp": 104, "atk": 26, "def": 27, "yk": 0, "bk": 0, "rk": 0},
    },
    {
        "name": "7F six yellow keys and HP",
        "floor": "MT7",
        "points": [(9, 5), (9, 3), (9, 2), (9, 1), (9, 7), (9, 9), (9, 10), (9, 11), (5, 7), (5, 9), (5, 10), (5, 11)],
        "expected": {"hp": 238, "atk": 26, "def": 27, "yk": 5, "bk": 0, "rk": 0},
    },
    {
        "name": "10F red gem",
        "floor": "MT10",
        "points": [(3, 9), (4, 11), (8, 11), (9, 9), (9, 6), (10, 6)],
        "expected": {"hp": 178, "atk": 27, "def": 27, "yk": 3, "bk": 0, "rk": 0},
    },
    {
        "name": "10F blue potion",
        "floor": "MT10",
        "points": [(11, 9), (11, 11)],
        "expected": {"hp": 378, "atk": 27, "def": 27, "yk": 2, "bk": 0, "rk": 0},
    },
    {
        "name": "7F blue potion",
        "floor": "MT7",
        "points": [(7, 7), (7, 9), (7, 10), (7, 11)],
        "expected": {"hp": 563, "atk": 27, "def": 27, "yk": 1, "bk": 0, "rk": 0},
    },
    {
        "name": "8F red key",
        "floor": "MT8",
        "points": [(8, 8), (10, 7), (9, 5), (11, 5), (10, 4), (9, 3), (9, 1), (11, 3), (11, 1), (10, 2)],
        "expected": {"hp": 420, "atk": 27, "def": 27, "yk": 2, "bk": 0, "rk": 1},
    },
    {
        "name": "1F final HP refill",
        "floor": "MT1",
        "points": [(10, 9), (10, 10), (10, 11), (4, 3), (1, 3)],
        "expected": {"hp": 659, "atk": 27, "def": 27, "yk": 0, "bk": 0, "rk": 1},
    },
    {
        "name": "10F boss",
        "floor": "MT10",
        "points": [(6, 9), (6, 5), (5, 4), (7, 4), (6, 4), (5, 5), (7, 5), (5, 6), (6, 6), (7, 6), (6, 1)],
        "expected": {"hp": 25, "atk": 27, "def": 27, "yk": 0, "bk": 0, "rk": 0},
    },
]

SPAWNED_BOSS = {
    (5, 4): "skeletonSoldier",
    (7, 4): "skeletonSoldier",
    (6, 4): "skeleton",
    (5, 5): "skeleton",
    (7, 5): "skeleton",
    (5, 6): "skeleton",
    (6, 6): "skeleton",
    (7, 6): "skeleton",
    (6, 1): "skeletonCaptain",
}


def as_state_text(state):
    return (
        f"HP={state['hp']} ATK={state['atk']} DEF={state['def']} "
        f"YK={state['yk']} BK={state['bk']} RK={state['rk']}"
    )


def state_record(state):
    return {key: state[key] for key in STATE_KEYS}


def diff_state(actual, expected):
    return {
        key: {"actual": actual.get(key), "expected": expected.get(key)}
        for key in STATE_KEYS
        if actual.get(key) != expected.get(key)
    }


def convert_collected(prefix_result):
    return {
        fid: set((item["x"], item["y"]) for item in positions)
        for fid, positions in prefix_result["collected"].items()
    }


def prefix_metrics(prefix_result):
    dmg = yd = bd = rd = 0
    for step in prefix_result["steps"]:
        before = step["state_before"]["hp"]
        after = step["state_after"]["hp"]
        dmg += max(0, before - after)
        eid = step["eid"]
        if eid == "yellowDoor":
            yd += 1
        elif eid == "blueDoor":
            bd += 1
        elif eid == "redDoor":
            rd += 1
    return dmg, yd, bd, rd


def apply_block(state, t, eid):
    before = state_record(state)
    err = None
    dmg = 0
    door = None
    if t == 1:
        dmg = calc_dmg(eid, state["atk"], state["def"])
        if dmg == float("inf"):
            err = f"cannot damage {eid}"
        elif state["hp"] - dmg <= 0:
            err = f"death on {eid}, damage={dmg}"
        else:
            state["hp"] -= dmg
    elif t == 2:
        if eid == "yellowDoor":
            if state["yk"] <= 0:
                err = "no yellow key"
            else:
                state["yk"] -= 1
                door = "yellow"
        elif eid == "blueDoor":
            if state["bk"] <= 0:
                err = "no blue key"
            else:
                state["bk"] -= 1
                door = "blue"
        elif eid == "redDoor":
            if state["rk"] <= 0:
                err = "no red key"
            else:
                state["rk"] -= 1
                door = "red"
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
    return before, state_record(state), err, dmg, door


def describe_step(step):
    action = step["action"]
    eid = step.get("eid")
    pos = step["pos"]
    if action == "walk":
        return f"x{pos[0]}y{pos[1]} 路过"
    if action == "bossTrigger":
        return f"x{pos[0]}y{pos[1]} 触发Boss事件"
    if action == "spawnedMonster":
        return f"x{pos[0]}y{pos[1]} 击杀{eid}"
    if action == "alreadyCleared":
        return f"x{pos[0]}y{pos[1]} 已清理({eid})"
    if eid in {"yellowDoor", "blueDoor", "redDoor"}:
        return f"x{pos[0]}y{pos[1]} 开{eid}"
    if eid in {"upFloor", "downFloor", "fakeWall"}:
        return f"x{pos[0]}y{pos[1]} 通过{eid}"
    if eid in {"yellowKey", "blueKey", "redKey", "redPotion", "bluePotion", "redGem", "blueGem", "greenGem", "sword1", "shield1"}:
        return f"x{pos[0]}y{pos[1]} 拾取{eid}"
    return f"x{pos[0]}y{pos[1]} 击杀{eid}"


def delta_text(before, after):
    parts = []
    labels = {"hp": "HP", "atk": "ATK", "def": "DEF", "yk": "YK", "bk": "BK", "rk": "RK"}
    for key in STATE_KEYS:
        if before[key] != after[key]:
            parts.append(f"{labels[key]}={before[key]}->{after[key]}")
    return " ".join(parts)


def replay():
    hero, maps = load_data()
    blocks = fixed.block_map(maps)
    prefix = fixed.replay_route()
    state = deepcopy(prefix["final_state"])
    collected = convert_collected(prefix)
    cleared = {fid: set(pos) for fid, pos in collected.items()}
    total_dmg, yd, bd, rd = prefix_metrics(prefix)
    current_floor = state["floor"]
    boss_triggered = False
    steps = []
    segments = []
    errors = []
    warnings = []

    for segment in ROUTE:
        fid = segment["floor"]
        if segment.get("start") == "flyback":
            start = FLYBACK_ENTRANCES[fid]
            state["floor"] = fid
            state["x"], state["y"] = start
            current_floor = fid
        elif fid != current_floor:
            start = FLYBACK_ENTRANCES[fid]
            state["floor"] = fid
            state["x"], state["y"] = start
            current_floor = fid

        seg_start = state_record(state)
        seg_dmg_start = total_dmg
        seg_yd_start, seg_bd_start, seg_rd_start = yd, bd, rd
        seg_notes = []

        for x, y in segment["points"]:
            pos = (x, y)
            start_pos = (state["x"], state["y"])
            is_boss_event_step = fid == "MT10" and (pos == (6, 5) or (boss_triggered and pos in SPAWNED_BOSS))
            if not is_boss_event_step:
                path = fixed.bfs_path(maps, blocks, cleared, fid, start_pos, pos, relaxed=False)
                if path is None:
                    relaxed = fixed.bfs_path(maps, blocks, cleared, fid, start_pos, pos, relaxed=True)
                    missing = fixed.blockers_on_path(blocks, cleared, fid, relaxed, pos) if relaxed else []
                    note = {
                        "segment": segment["name"],
                        "pos": pos,
                        "warning": "not strictly reachable",
                        "missing": missing,
                    }
                    warnings.append(note)
                    seg_notes.append(note)

            action = "walk"
            eid = None
            before = state_record(state)
            after = before.copy()
            err = None
            step_dmg = 0

            if fid == "MT10" and pos == (6, 5):
                boss_triggered = True
                action = "bossTrigger"
            elif boss_triggered and pos in SPAWNED_BOSS:
                eid = SPAWNED_BOSS[pos]
                action = "spawnedMonster"
                before, after, err, step_dmg, _door = apply_block(state, 1, eid)
                total_dmg += step_dmg
                cleared.setdefault(fid, set()).add(pos)
            elif pos in cleared.get(fid, set()):
                block = blocks[fid].get(pos)
                eid = block[1] if block else None
                action = "alreadyCleared"
                note = {"segment": segment["name"], "pos": pos, "warning": "already cleared", "eid": eid}
                warnings.append(note)
                seg_notes.append(note)
            else:
                block = blocks[fid].get(pos)
                if block is None:
                    action = "walk"
                else:
                    t, eid = block
                    action = eid
                    before, after, err, step_dmg, door = apply_block(state, t, eid)
                    total_dmg += step_dmg
                    if door == "yellow":
                        yd += 1
                    elif door == "blue":
                        bd += 1
                    elif door == "red":
                        rd += 1
                    if t in (1, 2, 3):
                        collected.setdefault(fid, set()).add(pos)
                    cleared.setdefault(fid, set()).add(pos)

            if err:
                item = {"segment": segment["name"], "pos": pos, "error": err, "eid": eid}
                errors.append(item)
                seg_notes.append(item)

            state["x"], state["y"] = x, y
            steps.append({
                "segment": segment["name"],
                "floor": fid,
                "pos": pos,
                "action": action,
                "eid": eid,
                "before": before,
                "after": state_record(state),
                "dmg": step_dmg,
                "total_dmg": total_dmg,
                "doors": {"yellow": yd, "blue": bd, "red": rd},
            })

        if "exit_to" in segment:
            next_floor, next_pos = segment["exit_to"]
            state["floor"] = next_floor
            state["x"], state["y"] = next_pos
            current_floor = next_floor

        actual = state_record(state)
        expected = segment.get("expected", {})
        segments.append({
            "name": segment["name"],
            "actual": actual,
            "expected": expected,
            "diff": diff_state(actual, expected),
            "segment_dmg": total_dmg - seg_dmg_start,
            "total_dmg": total_dmg,
            "segment_doors": {"yellow": yd - seg_yd_start, "blue": bd - seg_bd_start, "red": rd - seg_rd_start},
            "total_doors": {"yellow": yd, "blue": bd, "red": rd},
            "notes": seg_notes,
        })

    return {
        "ok": not errors,
        "prefix": {
            "state": state_record(prefix["final_state"]),
            "dmg": prefix_metrics(prefix)[0],
            "doors": {"yellow": prefix_metrics(prefix)[1], "blue": prefix_metrics(prefix)[2], "red": prefix_metrics(prefix)[3]},
        },
        "final": {
            "state": state_record(state),
            "dmg": total_dmg,
            "doors": {"yellow": yd, "blue": bd, "red": rd},
        },
        "segments": segments,
        "steps": steps,
        "warnings": warnings,
        "errors": errors,
    }


def write_report(result):
    os.makedirs(os.path.join("outputs", "reports"), exist_ok=True)
    os.makedirs(os.path.join("outputs", "results"), exist_ok=True)

    with open(os.path.join("outputs", "results", "user_post9_route_replay.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    natural_path = os.path.join("outputs", "results", "walkthrough_natural_atk23_dmg2596_experimental_summary.json")
    fixed_path = os.path.join("outputs", "results", "walkthrough_fixed_prefix_dmgfirst_summary.json")
    natural = json.load(open(natural_path, encoding="utf-8")) if os.path.exists(natural_path) else None
    fixed_summary = json.load(open(fixed_path, encoding="utf-8")) if os.path.exists(fixed_path) else None

    lines = ["# User Post-9F Route Replay", ""]
    lines.append(f"- mechanics: {'OK' if result['ok'] else 'FAILED'}")
    lines.append(f"- prefix: {as_state_text(result['prefix']['state'])} dmg={result['prefix']['dmg']} door={result['prefix']['doors']['yellow']}/{result['prefix']['doors']['blue']}/{result['prefix']['doors']['red']}")
    lines.append(f"- replay final: {as_state_text(result['final']['state'])} dmg={result['final']['dmg']} door={result['final']['doors']['yellow']}/{result['final']['doors']['blue']}/{result['final']['doors']['red']}")
    if natural:
        n = natural["final"]
        lines.append(f"- natural 2596 artifact: HP={n['hp']} ATK={n['atk']} DEF={n['def']} YK={n['yk']} BK={n['bk']} RK={n['rk']} dmg={n['dmg']} door={n['yd']}/{n['bd']}/{n['rd']} (rerun before final ranking)")
    if fixed_summary:
        f = fixed_summary["final"]["state"]
        lines.append(f"- current fixed-prefix output: HP={f['hp']} ATK={f['atk']} DEF={f['def']} YK={f['yk']} BK={f['bk']} RK={f['rk']} dmg={fixed_summary['final']['dmg']}")
    lines.append("")
    lines.append("| segment | actual | expected diff | seg dmg | total dmg | total door Y/B/R | notes |")
    lines.append("|---|---|---|---:|---:|---:|---|")
    for seg in result["segments"]:
        diff = "OK" if not seg["diff"] else json.dumps(seg["diff"], ensure_ascii=False)
        doors = seg["total_doors"]
        notes = "; ".join(
            n.get("warning") or n.get("error") or ""
            for n in seg["notes"]
        )
        lines.append(
            f"| {seg['name']} | {as_state_text(seg['actual'])} | {diff} | "
            f"{seg['segment_dmg']} | {seg['total_dmg']} | "
            f"{doors['yellow']}/{doors['blue']}/{doors['red']} | {notes or '-'} |"
        )
    if result["warnings"]:
        lines.append("")
        lines.append("## Warnings")
        lines.append("")
        for item in result["warnings"]:
            lines.append(f"- {item}")
    if result["errors"]:
        lines.append("")
        lines.append("## Errors")
        lines.append("")
        for item in result["errors"]:
            lines.append(f"- {item}")

    with open(os.path.join("outputs", "reports", "user_post9_route_replay.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")

    walk_lines = [
        "# User Verified Post-9F Route Walk",
        "",
        "> 前缀: fixed 4-9 拿盾并取 9F 红蓝宝石",
        f"> 前缀状态: {as_state_text(result['prefix']['state'])} dmg={result['prefix']['dmg']} door={result['prefix']['doors']['yellow']}/{result['prefix']['doors']['blue']}/{result['prefix']['doors']['red']}",
        f"> 最终状态: {as_state_text(result['final']['state'])} dmg={result['final']['dmg']} door={result['final']['doors']['yellow']}/{result['final']['doors']['blue']}/{result['final']['doors']['red']}",
        "",
        "## 修正说明",
        "",
        "- 6F 段补入 `x8y11` 红血瓶，原手写 `x9y10` 是空地。",
        "- 9F 上 10F 段补入 `x2y10` 红血瓶。",
        "- 1F `x1y3` 红血瓶未被 1-3 固定路线吃掉，可以在 Boss 前补血。",
        "",
    ]
    steps_by_segment = {}
    for step in result["steps"]:
        steps_by_segment.setdefault(step["segment"], []).append(step)
    for segment in result["segments"]:
        walk_lines.append(f"## {segment['name']}")
        walk_lines.append("")
        for step in steps_by_segment.get(segment["name"], []):
            before = step["before"]
            after = step["after"]
            delta = delta_text(before, after)
            delta_part = f" {delta}" if delta else ""
            walk_lines.append(f"- {step['floor']} {describe_step(step)}{delta_part}")
        doors = segment["total_doors"]
        walk_lines.append(
            f"=> {as_state_text(segment['actual'])} "
            f"本段dmg={segment['segment_dmg']} 累计dmg={segment['total_dmg']} "
            f"door={doors['yellow']}/{doors['blue']}/{doors['red']}"
        )
        walk_lines.append("")
    walk_lines.append("## Final")
    walk_lines.append("")
    walk_lines.append(
        f"**{as_state_text(result['final']['state'])} "
        f"dmg={result['final']['dmg']} "
        f"door={result['final']['doors']['yellow']}/{result['final']['doors']['blue']}/{result['final']['doors']['red']}**"
    )
    walk_lines.append("")
    with open(os.path.join("outputs", "walkthroughs", "walkthrough_user_post9_route.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(walk_lines).rstrip() + "\n")


def main():
    result = replay()
    write_report(result)
    print(f"mechanics={'OK' if result['ok'] else 'FAILED'}")
    print(f"final {as_state_text(result['final']['state'])} dmg={result['final']['dmg']} door={result['final']['doors']['yellow']}/{result['final']['doors']['blue']}/{result['final']['doors']['red']}")
    for seg in result["segments"]:
        diff = "OK" if not seg["diff"] else seg["diff"]
        print(f"{seg['name']}: {as_state_text(seg['actual'])} dmg={seg['total_dmg']} diff={diff}")
    print("wrote outputs/reports/user_post9_route_replay.md")
    print("wrote outputs/walkthroughs/walkthrough_user_post9_route.md")


if __name__ == "__main__":
    main()
