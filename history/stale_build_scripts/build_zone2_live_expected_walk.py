#!/usr/bin/env python3
"""Build the live-browser JSON walk for the current Zone-2 2ATK/1DEF branch."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]


def adjusted_state(state: dict[str, Any], gold_offset: int) -> dict[str, Any]:
    out = dict(state)
    out["gold"] = out.get("gold", 0) + gold_offset
    return out


def post_boss_supply_steps(start: dict[str, Any]) -> list[dict[str, Any]]:
    after = dict(start)
    after.update({"floor": "MT10", "x": 6, "y": 3})
    after["hp"] += 600
    after["atk"] += 3
    after["def"] += 3
    after["yk"] += 3
    return [
        {
            "segment": "10F Boss 后补给",
            "floor": "MT10",
            "pos": [6, 3],
            "action": "通过",
            "eid": "postBossSupply",
            "before": dict(start),
            "after": after,
            "note": "资源组入口：点击 MT10 x6y3；自动处理 3 红宝石、3 蓝宝石、3 蓝血瓶、3 黄钥匙，实测落点 MT10 x6y3",
        }
    ]


def convert_step(step: dict[str, Any], gold_offset: int) -> dict[str, Any]:
    out = dict(step)
    out["before"] = adjusted_state(step["before"], gold_offset)
    out["after"] = adjusted_state(step["after"], gold_offset)

    action = step["action"]
    if action == "传送":
        out["action"] = "飞行"
    elif action == "换层":
        out["action"] = "通过"
        out["floor"] = step["before"]["floor"]
    elif action == "使用道具":
        out["action"] = "使用"
    elif action in {"已清理", "事件开门"}:
        # A "已清理"/"事件开门" marker that also changes floor is not a real
        # action the live hero can execute -- the logic verify recorded a state
        # checkpoint where the hero is already on another floor (tiles cleared
        # in a prior visit, e.g. zone1). The live replayer cannot teleport, so
        # convert the floor change into an explicit fly to the target floor.
        # Same-floor markers stay as 校验 (state assertion, position ignored).
        if step["before"]["floor"] != step["after"]["floor"]:
            out["action"] = "飞行"
            out["floor"] = step["after"]["floor"]
        else:
            out["action"] = "校验"

    if action == "商店":
        eid = step.get("eid") or ""
        if "attack" in eid:
            out["eid"] = "atk"
        elif "defense" in eid:
            out["eid"] = "def"
        elif "hp" in eid:
            out["eid"] = "hp"
    elif action == "事件奖励" and step.get("eid") == "redKey":
        if step["before"].get("rk") == step["after"].get("rk"):
            out["action"] = "事件奖励"
            out["eid"] = "redKey"
            out["pos"] = [1, 3]
            out["note"] = f"{step.get('note') or ''}；生成物位于 MT14 x1y3，下一步按物品拾取".strip("；")
        else:
            out["action"] = "拾取"
            out["eid"] = "redKey"
            out["pos"] = [1, 3]
            out["note"] = f"{step.get('note') or ''}；旧模型奖励折算为实机 MT14 x1y3 拾取".strip("；")
    elif action == "事件" and step.get("eid") == "superPotion":
        out["action"] = "老人"
        out["eid"] = "superPotion"
        out["note"] = f"{step.get('note') or ''}；16F 老人给圣水".strip("；")
    elif action == "使用道具" and step.get("eid") == "superPotion":
        out["eid"] = "superPotion"

    return out


def _floor_num(fid: str) -> int | None:
    if fid.startswith("MT") and fid[2:].isdigit():
        return int(fid[2:])
    return None


def stair_up_to(fid: str) -> tuple[list[int], list[int], str] | None:
    """For floor `fid` (e.g. MT15), find the stair entry from its predecessor
    (MT14): the up-exit tile on MT14 (:next changeFloor) and the landing tile
    on MT15 (:before changeFloor). Returns (up_exit_pos, landing_pos, fid)."""
    n = _floor_num(fid)
    if n is None or n <= 1:
        return None
    prev = f"MT{n - 1}"
    prev_map = ROOT / "data" / "maps" / f"mt{n - 1}_map.json"
    if not prev_map.exists():
        return None
    cf = json.loads(prev_map.read_text(encoding="utf-8-sig")).get("changeFloor", {})
    up_key = next((k for k, v in cf.items() if v.get("floorId") == ":next"), None)
    if up_key is None:
        return None
    ux, uy = up_key.split(",")
    up_pos = [int(ux), int(uy)]
    landing_pos = up_pos
    this_map = ROOT / "data" / "maps" / f"mt{n}_map.json"
    if this_map.exists():
        cft = json.loads(this_map.read_text(encoding="utf-8-sig")).get("changeFloor", {})
        land_key = next((k for k, v in cft.items() if v.get("floorId") == ":before"), None)
        if land_key:
            lx, ly = land_key.split(",")
            landing_pos = [int(lx), int(ly)]
    return up_pos, landing_pos, fid


def build_walk(source: Path, gold_offset: int) -> dict[str, Any]:
    result = json.loads(source.read_text(encoding="utf-8-sig"))["result"]
    start = {
        "hp": 122,
        "atk": 27,
        "def": 27,
        "yk": 0,
        "bk": 0,
        "rk": 0,
        "gold": 305 + gold_offset,
        "floor": "MT10",
        "x": 6,
        "y": 1,
        "dmg": 2454,
        "yd": 41,
        "bd": 2,
        "rd": 1,
        "cross": False,
        "pickaxe": False,
        "superPotion": False,
    }
    steps = post_boss_supply_steps(start)
    # The logic verify does not enforce continuous hero position OR the
    # h5mota rule that a floor must be entered via stairs/event before it can
    # be flown to. Two kinds of gap therefore appear in the raw step stream:
    #   (a) floor discontinuity -- a non-transition step whose before.floor
    #       differs from the previous step's after.floor (the hero "jumps").
    #       Stats are continuous across these (verified), so a fly (which
    #       changes only floor) is the correct inserted action.
    #   (b) a fly (传送) whose target has never been visited -- must be split
    #       into fly-to-predecessor + real stair entry.
    visited: set[str] = {f"MT{i}" for i in range(1, 11)}
    split_notes: list[str] = []

    def emit_fly(target: str, before_state: dict[str, Any], segment: str) -> dict[str, Any]:
        """Append fly step(s) to reach `target` from `before_state` and return
        the resulting after-state. Splits into fly-to-predecessor + stair when
        `target` is unvisited (h5mota forbids flying to unvisited floors)."""
        if target in visited:
            after = dict(before_state)
            after["floor"] = target
            steps.append({
                "segment": segment,
                "floor": target,
                "pos": [before_state.get("x", 0), before_state.get("y", 0)],
                "action": "飞行",
                "eid": None,
                "before": dict(before_state),
                "after": after,
                "note": f"飞到 {target}",
            })
            return after
        info = stair_up_to(target)
        if info is None:
            after = dict(before_state)
            after["floor"] = target
            steps.append({
                "segment": segment,
                "floor": target,
                "pos": [before_state.get("x", 0), before_state.get("y", 0)],
                "action": "飞行",
                "eid": None,
                "before": dict(before_state),
                "after": after,
                "note": f"飞到 {target}（未找到楼梯入口数据，直飞）",
            })
            visited.add(target)
            return after
        up_pos, landing_pos, _ = info
        predecessor = f"MT{_floor_num(target) - 1}"
        fly_after = dict(before_state)
        fly_after["floor"] = predecessor
        steps.append({
            "segment": segment,
            "floor": predecessor,
            "pos": [before_state.get("x", 0), before_state.get("y", 0)],
            "action": "飞行",
            "eid": None,
            "before": dict(before_state),
            "after": fly_after,
            "note": f"首次进 {target} 前先飞回已访问的 {predecessor}（{target} 未首次访问，不能直接飞）",
        })
        stair_after = dict(before_state)
        stair_after["floor"] = target
        stair_after["x"] = landing_pos[0]
        stair_after["y"] = landing_pos[1]
        steps.append({
            "segment": segment,
            "floor": predecessor,
            "pos": up_pos,
            "action": "通过",
            "eid": None,
            "before": fly_after,
            "after": stair_after,
            "note": f"经 {predecessor} x{up_pos[0]}y{up_pos[1]} 上楼梯首次进入 {target}，落点 {target} x{landing_pos[0]}y{landing_pos[1]}",
        })
        visited.add(target)
        split_notes.append(f"{target}（原 fly 拆为 fly {predecessor} + 楼梯首次进入）")
        return stair_after

    current_floor = "MT10"
    last_after = steps[-1]["after"]
    for step in result["steps"]:
        conv = convert_step(step, gold_offset)
        action = conv["action"]
        before_floor = conv["before"]["floor"]
        after_floor = conv["after"]["floor"]
        # (a) insert a fly when the step starts on a different floor than where
        # the hero currently stands (logic-verify floor discontinuity).
        if before_floor != current_floor:
            last_after = emit_fly(before_floor, last_after, step.get("segment", ""))
            current_floor = before_floor
        # (b) a fly whose target is unvisited must be split into stair entry.
        if action == "飞行" and after_floor not in visited:
            last_after = emit_fly(after_floor, last_after, step.get("segment", ""))
            current_floor = after_floor
            continue
        steps.append(conv)
        last_after = conv["after"]
        current_floor = after_floor
        visited.add(after_floor)
    return {
        "ok": True,
        "name": "4-20 纯净版 TE 当前最佳 1区+2区分支实机期望",
        "source": str(source.relative_to(ROOT)),
        "gold_offset_from_zone1_auto": gold_offset,
        "start_after_zone1_live": start,
        "steps": steps,
        "expected_final": steps[-1]["after"],
        "visit_order_splits": split_notes,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source",
        type=Path,
        default=ROOT / "outputs/results/zone2_2atk1def_branch_logic_verify_4to20.json",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "outputs/results/zone2_2atk1def_live_expected_walk_4to20.json",
    )
    parser.add_argument("--gold-offset", type=int, default=8)
    args = parser.parse_args()

    walk = build_walk(args.source, args.gold_offset)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(walk, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"out": str(args.out), "steps": len(walk["steps"]), "expected_final": walk["expected_final"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
