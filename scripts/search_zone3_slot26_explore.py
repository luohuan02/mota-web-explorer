#!/usr/bin/env python3
"""Time-bounded macro/beam exploration from the slot-26 31F start.

This is a zone-3 experiment, not a replacement for the older 1F-20F searches.
It reuses the local GuideReplay mechanics so generated candidates are replayed
through map/path legality, shops, keys, floor events, and damage accounting.
"""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import math
import sys
import time
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "scripts" / "plan_zone3_guide_slot36.py"
QUICK = ROOT / "scripts" / "find_zone3_quick_pass_walk.py"
DEFAULT_SNAPSHOT = ROOT / "outputs" / "results" / "slot26_snapshot.json"
OUT_JSON = ROOT / "outputs" / "results" / "zone3_slot26_explore.json"
OUT_MD = ROOT / "outputs" / "reports" / "zone3_slot26_explore.md"

RESOURCE_IDS = {
    "yellowKey",
    "blueKey",
    "redKey",
    "redPotion",
    "bluePotion",
    "redGem",
    "blueGem",
    "sword3",
    "shield3",
    "centerFly3",
}
KEY_RESOURCE_IDS = {"yellowKey", "blueKey", "redKey", "redGem", "blueGem", "sword3", "shield3", "centerFly3"}
POTION_IDS = {"redPotion", "bluePotion"}
SHOP_POS = ("MT32", 10, 10)
MT40_REWARD = [(2, 2), (3, 2), (4, 2), (8, 2), (9, 2), (10, 2), (7, 4), (8, 4), (9, 4)]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


p = load_module("zone3_plan_slot26", PLAN)
quick = load_module("zone3_quick_helpers", QUICK)


def state_line(g: Any) -> str:
    s = g.state
    return (
        f"HP={s['hp']} ATK={s['atk']} DEF={s['def']} "
        f"YK={s['yk']} BK={s['bk']} RK={s['rk']} G={s['gold']} "
        f"{s['floor']} x{s['x']}y{s['y']} dmg={s['dmg']} door={s['yd']}/{s['bd']}/{s['rd']} shop={s['times1']}"
    )


def clone(g: Any) -> Any:
    return copy.deepcopy(g)


def floor_no(fid: str) -> int:
    return int(fid[2:])


def target_floor_key(fid: str, x: int, y: int) -> str:
    return f"{fid}:x{x}y{y}"


def init_replay(snapshot_path: Path) -> Any:
    p.SNAPSHOT = snapshot_path
    snapshot = p.read_json(snapshot_path)
    enemies = p.load_enemy_stats()
    floors = p.load_floors(snapshot, enemies)
    g = p.GuideReplay(snapshot, floors, enemies)
    flags = snapshot.get("hero", {}).get("flags", {})
    visited = {fid for fid, ok in flags.get("__visited__", {}).items() if ok}
    if not visited:
        visited = {f"MT{i}" for i in range(1, floor_no(snapshot["floorId"]) + 1)}
    visited.add(snapshot["floorId"])
    g.state["visited"] = visited
    g.state["centerFly3"] = False
    g.state["boss40"] = False
    g.state["special_done"] = set()
    return g


def mark_visited(g: Any, fid: str) -> None:
    g.state.setdefault("visited", set()).add(fid)


def can_fly_to(g: Any, fid: str) -> bool:
    return fid in g.state.get("visited", set())


def no_new_error(before_errors: int, g: Any) -> bool:
    return len(g.errors) == before_errors


def changed(before: dict[str, Any], g: Any) -> bool:
    after = g.snapshot()
    keys = ("floor", "x", "y", "hp", "atk", "def", "yk", "bk", "rk", "gold", "yd", "bd", "rd")
    return any(before.get(k) != after.get(k) for k in keys)


def move_to(g: Any, fid: str, x: int, y: int, note: str) -> bool:
    if not can_fly_to(g, fid):
        return False
    before_errors = len(g.errors)
    if g.state["floor"] != fid:
        g.fly(fid)
    g.go_to(fid, x, y, note)
    return no_new_error(before_errors, g)


def next_floor_action(g: Any, fid: str) -> Any | None:
    n = floor_no(fid)
    if n >= 40 or fid not in g.state.get("visited", set()) or f"MT{n + 1}" in g.state.get("visited", set()):
        return None
    floors = g.floors.get(fid)
    if not floors:
        return None
    up_positions = [pos for pos, block in floors.blocks.items() if block.kind == "terrain" and block.eid == "upFloor"]
    if not up_positions:
        return None
    target = sorted(up_positions)[0]

    def apply(candidate: Any) -> bool:
        if not can_fly_to(candidate, fid):
            return False
        before_errors = len(candidate.errors)
        if candidate.state["floor"] != fid:
            candidate.fly(fid)
        candidate.go_to(fid, target[0], target[1], f"{fid} 上楼到 MT{n + 1}")
        if not no_new_error(before_errors, candidate):
            return False
        candidate.transition(f"MT{n + 1}", target[0], target[1], f"{fid} 上楼到 MT{n + 1}")
        mark_visited(candidate, f"MT{n + 1}")
        return no_new_error(before_errors, candidate)

    return {
        "label": f"{fid}:upFloor->MT{n + 1}",
        "kind": "progress",
        "priority": 9000 + n * 80,
        "apply": apply,
    }


def item_value(eid: str, g: Any) -> int:
    ratio = g.floors[g.state["floor"]].ratio if g.state["floor"] in g.floors else 1
    if eid == "sword3":
        return 4500
    if eid == "shield3":
        return 4800
    if eid == "centerFly3":
        return 5000
    if eid == "redGem":
        return 720
    if eid == "blueGem":
        return 780
    if eid == "yellowKey":
        return 260
    if eid == "blueKey":
        return 700
    if eid == "redKey":
        return 1200
    if eid == "bluePotion":
        return 80 if g.state["hp"] > 900 else 420 * ratio
    if eid == "redPotion":
        return 30 if g.state["hp"] > 900 else 110 * ratio
    return 0


def enemy_value(fid: str, eid: str, dmg: int | float, g: Any) -> int:
    enemy = g.enemies[eid]
    money = int(enemy["money"])
    if dmg == float("inf") or g.state["hp"] - int(dmg) <= 0:
        return -10**9
    # Do not over-reward random zero-damage gold because later double-gold exists.
    zero_penalty = 70 if dmg == 0 and money < 60 else 0
    blocker_bonus = 120 if floor_no(fid) >= 31 else 40
    return money * 8 + blocker_bonus - int(dmg) * 3 - zero_penalty


def block_priority(g: Any, fid: str, pos: tuple[int, int], block: Any) -> int:
    if block.kind == "item":
        old_floor = g.state["floor"]
        g.state["floor"] = fid
        try:
            val = item_value(block.eid, g)
        finally:
            g.state["floor"] = old_floor
        if block.eid in POTION_IDS:
            val -= 80
        return val
    if block.kind == "enemy":
        dmg = g.damage_for(block.eid)
        return enemy_value(fid, block.eid, dmg, g)
    return -10**9


def candidate_target_actions(g: Any, max_targets: int) -> list[dict[str, Any]]:
    rows: list[tuple[int, str, str, int, int]] = []
    for fid in sorted(g.state.get("visited", set()), key=floor_no):
        if floor_no(fid) > 40 or fid not in g.floors:
            continue
        for pos, block in g.floors[fid].blocks.items():
            if block.kind not in {"item", "enemy"}:
                continue
            if block.kind == "item" and block.eid not in RESOURCE_IDS:
                continue
            pri = block_priority(g, fid, pos, block)
            if pri <= -100000:
                continue
            # Keep low-value random enemies only if they may connect progress.
            if block.kind == "enemy" and pri < 150:
                continue
            rows.append((pri, block.eid, fid, pos[0], pos[1]))
    rows.sort(reverse=True)
    actions = []
    for pri, eid, fid, x, y in rows[:max_targets]:
        label = f"{fid}:x{x}y{y}:{eid}"

        def make_apply(tfid: str, tx: int, ty: int, teid: str) -> Callable[[Any], bool]:
            def apply(candidate: Any) -> bool:
                before_errors = len(candidate.errors)
                before = candidate.snapshot()
                ok = move_to(candidate, tfid, tx, ty, f"search {teid}")
                return ok and no_new_error(before_errors, candidate) and changed(before, candidate)

            return apply

        actions.append({"label": label, "kind": "target", "priority": pri, "apply": make_apply(fid, x, y, eid)})
    return actions


def special_actions(g: Any) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []

    if can_fly_to(g, "MT32") and g.block_at("MT32", (6, 10)):
        def apply32(candidate: Any) -> bool:
            before_errors = len(candidate.errors)
            if not move_to(candidate, "MT32", 6, 10, "32F 初见骑士队长"):
                return False
            candidate.event_mt32_yellow_knight()
            return no_new_error(before_errors, candidate)

        actions.append({"label": "MT32:event:yellowKnight", "kind": "event", "priority": 12000, "apply": apply32})

    if can_fly_to(g, "MT33") and "mt33_sword_trap" not in g.state.get("special_done", set()):
        def apply33(candidate: Any) -> bool:
            before_errors = len(candidate.errors)
            if not move_to(candidate, "MT33", 10, 5, "33F 骑士剑机关"):
                return False
            candidate.event_mt33_sword_trap()
            candidate.state.setdefault("special_done", set()).add("mt33_sword_trap")
            return no_new_error(before_errors, candidate)

        actions.append({"label": "MT33:event:swordTrap", "kind": "event", "priority": 9800, "apply": apply33})

    if can_fly_to(g, "MT2") and g.block_at("MT2", (11, 4)):
        def oldman(candidate: Any) -> bool:
            before_errors = len(candidate.errors)
            if not move_to(candidate, "MT2", 11, 4, "2F 老人 1000G"):
                return False
            candidate.oldman_mt2_1000g()
            return no_new_error(before_errors, candidate)

        actions.append({"label": "MT2:event:oldman1000G", "kind": "event", "priority": 10500, "apply": oldman})

    if can_fly_to(g, "MT2") and g.block_at("MT2", (10, 11)):
        def thief2(candidate: Any) -> bool:
            before_errors = len(candidate.errors)
            if not move_to(candidate, "MT2", 10, 11, "2F 小偷开35F"):
                return False
            candidate.thief_mt2_open_35()
            return no_new_error(before_errors, candidate)

        actions.append({"label": "MT2:event:thiefOpen35", "kind": "event", "priority": 8400, "apply": thief2})

    if can_fly_to(g, "MT35") and g.block_at("MT35", (5, 10)):
        def thief35(candidate: Any) -> bool:
            before_errors = len(candidate.errors)
            if not move_to(candidate, "MT35", 5, 10, "35F 小偷离开"):
                return False
            candidate.thief_mt35_depart()
            return no_new_error(before_errors, candidate)

        actions.append({"label": "MT35:event:thiefDepart", "kind": "event", "priority": 8400, "apply": thief35})

    if can_fly_to(g, "MT39") and not g.state.get("centerFly3"):
        def puzzle39(candidate: Any) -> bool:
            before_errors = len(candidate.errors)
            if candidate.state["floor"] != "MT39":
                candidate.fly("MT39")
            quick.open_mt39_puzzle(candidate)
            return no_new_error(before_errors, candidate) and bool(candidate.state.get("centerFly3"))

        actions.append({"label": "MT39:event:centerFlyPuzzle", "kind": "event", "priority": 11000, "apply": puzzle39})

    if can_fly_to(g, "MT40") and g.state.get("centerFly3"):
        def center40(candidate: Any) -> bool:
            before_errors = len(candidate.errors)
            if candidate.state["floor"] != "MT40":
                candidate.fly("MT40")
            quick.use_center_fly_to_mt40_boss_area(candidate)
            return no_new_error(before_errors, candidate)

        actions.append({"label": "MT40:use:centerFly", "kind": "event", "priority": 12000, "apply": center40})

    if can_fly_to(g, "MT40") and not g.state.get("boss40"):
        def boss40(candidate: Any) -> bool:
            before_errors = len(candidate.errors)
            if candidate.state["floor"] != "MT40":
                candidate.fly("MT40")
            # If the boss-area guards still exist, this will fail to path to x6y7.
            if not move_to(candidate, "MT40", 6, 7, "40F 触发Boss事件"):
                return False
            quick.event_mt40_boss(candidate)
            candidate.state["boss40"] = True
            return no_new_error(before_errors, candidate)

        actions.append({"label": "MT40:event:bossReward", "kind": "event", "priority": 15000, "apply": boss40})

    if can_fly_to(g, "MT38") and g.block_at("MT38", (5, 2)) and g.state["gold"] >= 200:
        def merchant38(candidate: Any) -> bool:
            before_errors = len(candidate.errors)
            if not move_to(candidate, "MT38", 5, 2, "38F 买3黄钥匙"):
                return False
            candidate.buy_mt38_yellow_keys()
            return no_new_error(before_errors, candidate)

        actions.append({"label": "MT38:merchant:3YK", "kind": "merchant", "priority": 7800, "apply": merchant38})

    if can_fly_to(g, "MT28") and g.state["yk"] > 0:
        def sell28(candidate: Any) -> bool:
            before_errors = len(candidate.errors)
            if not move_to(candidate, "MT28", 8, 4, "28F 卖1黄钥匙"):
                return False
            before = candidate.snapshot()
            candidate.state["yk"] -= 1
            candidate.state["gold"] += 100
            candidate.record("商人", (8, 4), "sellYellowKey", before, "28F 卖1黄钥匙得100G")
            return no_new_error(before_errors, candidate)

        actions.append({"label": "MT28:merchant:sell1YK", "kind": "merchant", "priority": 3200, "apply": sell28})

    if can_fly_to(g, "MT32"):
        for kind, weight in (("def", 7600), ("atk", 7200)):
            cost = p.shop_cost(g.state["times1"])
            if g.state["gold"] < cost:
                continue

            def make_shop(k: str) -> Callable[[Any], bool]:
                def shop(candidate: Any) -> bool:
                    before_errors = len(candidate.errors)
                    if not move_to(candidate, SHOP_POS[0], SHOP_POS[1], f"32F 商店 {k}"):
                        return False
                    if candidate.state["gold"] < p.shop_cost(candidate.state["times1"]):
                        return False
                    candidate.buy_shop(k, 1)
                    return no_new_error(before_errors, candidate)

                return shop

            actions.append({
                "label": f"MT32:shop:{kind}:cost{cost}",
                "kind": "shop",
                "priority": weight - cost // 2,
                "apply": make_shop(kind),
            })

    for fid in list(g.state.get("visited", set())):
        act = next_floor_action(g, fid)
        if act:
            actions.append(act)

    return actions


def action_signature(g: Any, label: str) -> tuple[Any, ...]:
    visited = tuple(sorted(g.state.get("visited", ()), key=floor_no))
    return (
        label,
        g.state["floor"],
        g.state["x"],
        g.state["y"],
        g.state["hp"],
        g.state["atk"],
        g.state["def"],
        g.state["yk"],
        g.state["bk"],
        g.state["rk"],
        g.state["gold"],
        g.state["times1"],
        visited,
    )


def stage(g: Any) -> int:
    visited_max = max((floor_no(fid) for fid in g.state.get("visited", {"MT31"})), default=31)
    value = visited_max * 10000
    if g.state.get("boss40"):
        value += 30000
    if g.state.get("centerFly3"):
        value += 8000
    if g.block_at("MT40", (6, 1)) and g.block_at("MT40", (6, 1)).eid == "upFloor":
        value += 20000
    if g.state["atk"] >= 126:
        value += 5000
    if g.state["def"] >= 154:
        value += 4000
    if g.state["def"] >= 202:
        value += 4000
    return value


def remaining_simple_value(g: Any) -> int:
    value = 0
    for fid, floor in g.floors.items():
        if floor_no(fid) > 40:
            continue
        for _pos, block in floor.blocks.items():
            if block.kind == "item":
                if block.eid == "yellowKey":
                    value += 50
                elif block.eid == "blueKey":
                    value += 200
                elif block.eid == "redPotion":
                    value += 50 * floor.ratio
                elif block.eid == "bluePotion":
                    value += 200 * floor.ratio
                elif block.eid in {"redGem", "blueGem"}:
                    value += 250
            elif block.kind == "enemy" and g.damage_for(block.eid) == 0:
                value += min(40, int(g.enemies[block.eid]["money"]))
    return value


def score(g: Any) -> int:
    s = g.state
    stock = s["hp"] + s["yk"] * 50 + s["bk"] * 200 + s["rk"] * 500 + s["gold"] // 2
    stats = s["atk"] * 95 + s["def"] * 120
    door_penalty = s["yd"] * 25 + s["bd"] * 70 + s["rd"] * 150
    potion_penalty = 0
    if floor_no(s["floor"]) < 41:
        # High pre-41 HP is less valuable because 41F halves it.
        potion_penalty = max(0, s["hp"] - 600) // 2
    return stage(g) + stock + stats - s["dmg"] - door_penalty - potion_penalty


def goal_score(g: Any) -> int:
    s = g.state
    stock = s["hp"] + s["yk"] * 50 + s["bk"] * 200 + s["rk"] * 500 + s["gold"] // 2
    return stock + s["atk"] * 140 + s["def"] * 170 - s["dmg"] - s["yd"] * 50 - s["bd"] * 200 - s["rd"] * 350 + remaining_simple_value(g)


def simple_stock_score(g: Any) -> float:
    """Comparison-only score: 1YK = 50HP = 100G, BK keeps project 4YK value."""
    s = g.state
    return s["hp"] + s["yk"] * 50 + s["bk"] * 200 + s["gold"] * 0.5


def state_bucket(g: Any) -> tuple[Any, ...]:
    s = g.state
    visited_max = max((floor_no(fid) for fid in s.get("visited", {"MT31"})), default=31)
    return (
        visited_max,
        s.get("boss40", False),
        s.get("centerFly3", False),
        s["floor"],
        s["atk"] // 2,
        s["def"] // 2,
        s["yk"],
        s["bk"],
        s["rk"],
        s["times1"],
        min(3000, max(-1000, s["gold"])) // 100,
    )


def select_beam(cands: list[Any], limit: int) -> list[Any]:
    buckets: dict[tuple[Any, ...], Any] = {}
    for g in cands:
        key = state_bucket(g)
        old = buckets.get(key)
        if old is None or score(g) > score(old):
            buckets[key] = g
    rows = sorted(buckets.values(), key=score, reverse=True)
    return rows[:limit]


def finish_goal_candidate(g: Any) -> Any:
    out = clone(g)
    if not out.state.get("boss40"):
        return out
    for x, y in MT40_REWARD:
        block = out.block_at("MT40", (x, y))
        if block and block.kind == "item" and block.eid in KEY_RESOURCE_IDS:
            move_to(out, "MT40", x, y, "40F boss后钥匙/宝石")
    move_to(out, "MT40", 6, 1, "40F boss后上楼口")
    return out


def explore(args: argparse.Namespace) -> dict[str, Any]:
    start = init_replay(args.snapshot)
    frontier = [start]
    best_any = start
    best_goal: Any | None = None
    expanded = 0
    generated = 0
    started = time.time()
    deadline = started + args.time_limit_seconds
    last_report = started

    def progress(message: str) -> None:
        if args.progress_log:
            args.progress_log.parent.mkdir(parents=True, exist_ok=True)
            with args.progress_log.open("a", encoding="utf-8") as f:
                f.write(message + "\n")
        try:
            print(message, flush=True)
        except OSError:
            pass

    for depth in range(args.max_depth):
        if time.time() >= deadline:
            break
        next_rows: list[Any] = []
        for source in frontier:
            if time.time() >= deadline:
                break
            actions = special_actions(source) + candidate_target_actions(source, args.targets_per_state)
            actions.sort(key=lambda a: a["priority"], reverse=True)
            seen_labels = set()
            for action in actions[: args.actions_per_state]:
                if time.time() >= deadline:
                    break
                label = action["label"]
                if label in seen_labels:
                    continue
                seen_labels.add(label)
                candidate = clone(source)
                before_errors = len(candidate.errors)
                before_steps = len(candidate.steps)
                try:
                    ok = action["apply"](candidate)
                except Exception as exc:  # keep the search alive and auditable
                    candidate.errors.append(f"{label}: exception {exc}")
                    ok = False
                expanded += 1
                if not ok or len(candidate.errors) != before_errors or len(candidate.steps) == before_steps:
                    continue
                candidate.state.setdefault("trace", list(source.state.get("trace", []))).append(label)
                generated += 1
                next_rows.append(candidate)
                if score(candidate) > score(best_any):
                    best_any = candidate
                if candidate.state.get("boss40"):
                    finished = finish_goal_candidate(candidate)
                    if best_goal is None or goal_score(finished) > goal_score(best_goal):
                        best_goal = finished
        frontier = select_beam(frontier + next_rows, args.beam)
        now = time.time()
        if now - last_report >= args.report_interval:
            top = frontier[0] if frontier else best_any
            goal_text = state_line(best_goal) if best_goal else "-"
            progress(
                f"[{now - started:7.1f}s] depth={depth + 1} frontier={len(frontier)} "
                f"expanded={expanded} generated={generated} top={state_line(top)} goal={goal_text}",
            )
            last_report = now
        if not frontier:
            break

    elapsed = time.time() - started
    result = {
        "snapshot": str(args.snapshot),
        "elapsed": elapsed,
        "expanded": expanded,
        "generated": generated,
        "beam": args.beam,
        "best_any": serialize_run(best_any),
        "best_goal": serialize_run(best_goal) if best_goal else None,
    }
    return result


def serialize_run(g: Any | None) -> dict[str, Any] | None:
    if g is None:
        return None
    return {
        "score": score(g),
        "goal_score": goal_score(g),
        "simple_stock_score": simple_stock_score(g),
        "state": g.snapshot(),
        "state_text": state_line(g),
        "errors": g.errors,
        "warnings": g.warnings,
        "trace": list(g.state.get("trace", [])),
        "steps": g.steps,
        "remaining_simple_value": remaining_simple_value(g),
    }


def write_report(data: dict[str, Any], out_json: Path, out_md: Path) -> None:
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# Zone3 slot26 探索报告",
        "",
        f"- elapsed: `{data['elapsed']:.1f}s`",
        f"- expanded/generated: `{data['expanded']}` / `{data['generated']}`",
        f"- beam: `{data['beam']}`",
        "",
    ]
    for key, title in (("best_goal", "最好通关候选"), ("best_any", "最好中间候选")):
        row = data.get(key)
        lines.append(f"## {title}")
        if not row:
            lines.append("- 未找到")
            lines.append("")
            continue
        lines.append(f"- score: `{row['score']}`；goal_score: `{row['goal_score']}`")
        lines.append(f"- simple_stock_score(1YK=50HP=100G): `{row['simple_stock_score']}`")
        lines.append(f"- state: `{row['state_text']}`")
        lines.append(f"- remaining_simple_value: `{row['remaining_simple_value']}`")
        lines.append(f"- trace length: `{len(row['trace'])}`；steps: `{len(row['steps'])}`")
        if row["trace"]:
            lines.append("")
            lines.append("### Trace")
            for i, label in enumerate(row["trace"], 1):
                lines.append(f"{i}. `{label}`")
        lines.append("")
        lines.append("### 最后 80 步")
        for i, step in enumerate(row["steps"][-80:], max(1, len(row["steps"]) - 79)):
            pos = step.get("pos", ["?", "?"])
            delta = f" [{step.get('delta')}]" if step.get("delta") else ""
            lines.append(f"{i}. {step.get('floor')} x{pos[0]}y{pos[1]} {step.get('action')} {step.get('eid') or ''}{delta}".rstrip())
        lines.append("")
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", type=Path, default=DEFAULT_SNAPSHOT)
    parser.add_argument("--time-limit-seconds", type=float, default=5400)
    parser.add_argument("--beam", type=int, default=180)
    parser.add_argument("--targets-per-state", type=int, default=24)
    parser.add_argument("--actions-per-state", type=int, default=36)
    parser.add_argument("--max-depth", type=int, default=260)
    parser.add_argument("--report-interval", type=float, default=30)
    parser.add_argument("--progress-log", type=Path, default=None)
    parser.add_argument("--out-json", type=Path, default=OUT_JSON)
    parser.add_argument("--out-md", type=Path, default=OUT_MD)
    args = parser.parse_args()
    data = explore(args)
    write_report(data, args.out_json, args.out_md)
    print(f"wrote {args.out_json}")
    print(f"wrote {args.out_md}")
    if data.get("best_goal"):
        print("best_goal", data["best_goal"]["state_text"])
    else:
        print("best_goal not found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
