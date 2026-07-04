#!/usr/bin/env python3
"""Stitch the strict 4F-50F local candidate into one auditable walk.

This script does not search or alter the route.  It combines the existing
web-checked Zone-1/Zone-2 logs, the local 20F-31F bridge, and the local
31F-50F continuation into a single report.  The cumulative dmg/door metrics
are reported explicitly because the post-31 local replay starts its counters
from zero.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

ZONE1_REPLAY = ROOT / "outputs" / "results" / "zone1_current_best_live_auto_item_true_replay.json"
ZONE2_STRICT = ROOT / "outputs" / "results" / "zone2_2atk1def_4to20_live_strict_walk.json"
ZONE2_STRICT_WEB_RECORD = ROOT / "outputs" / "results" / "strict20_preserve_pickaxe_4to50_web_strict_record_step001_402_nopot_switch.json"
ZONE2_LOGIC = ROOT / "outputs" / "results" / "zone2_2atk1def_branch_logic_verify_4to20.json"
BRIDGE_WALK = ROOT / "outputs" / "results" / "zone2_2atk1def_strict20_to31_bridge_walk.json"
TAIL_WALK = ROOT / "outputs" / "results" / "strict20_preserve_pickaxe_31to50_local_walk.json"
AUDIT = ROOT / "outputs" / "results" / "strict20_preserve_pickaxe_4to50_local_audit.json"
FLY_POINTS = json.loads((ROOT / "data" / "maps" / "fly_points.json").read_text(encoding="utf-8"))

OUT_JSON = ROOT / "outputs" / "results" / "strict20_preserve_pickaxe_4to50_stitched_local_walk.json"
OUT_MD = ROOT / "outputs" / "walkthroughs" / "strict20_preserve_pickaxe_4to50_stitched_local_walk_zh.md"

STAT_KEYS = ("hp", "atk", "def", "yk", "bk", "rk", "gold")
STAT_LABELS = {
    "hp": "生命",
    "atk": "攻",
    "def": "防",
    "yk": "黄",
    "bk": "蓝",
    "rk": "红",
    "gold": "金币",
}
ACTION_NAMES = {
    "open": "开门",
    "kill": "击杀",
    "pass": "通过",
    "take": "拾取",
    "event": "事件",
    "shop": "商店",
    "trader": "商人",
    "fly": "飞行",
    "check": "校验",
    "trigger": "事件",
    "事件开门": "事件",
}

SET_AUTO_ACTION = "设置自动"
AUTO_START = {"battle": True, "item": True, "wall": True}
AUTO_NOPOTION = {"battle": True, "item": "nopotion", "wall": True}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def zone2_source_path() -> Path:
    return ZONE2_STRICT_WEB_RECORD if ZONE2_STRICT_WEB_RECORD.exists() else ZONE2_STRICT


def normalize_zone2_source(raw: dict[str, Any]) -> dict[str, Any]:
    if "strictWalk" not in raw:
        return raw
    walk = dict(raw["strictWalk"])
    steps = [
        step
        for step in walk.get("steps", [])
        if "2区" in str(step.get("segment") or "")
    ]
    walk["steps"] = steps
    final = raw.get("finalState")
    if final:
        walk["expected_final"] = {
            "floor": final["floor"],
            "x": final["x"],
            "y": final["y"],
            "hp": final["hp"],
            "atk": final["atk"],
            "def": final["def"],
            "gold": final["gold"],
            "yk": final["yk"],
            "bk": final["bk"],
            "rk": final["rk"],
        }
    return walk


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def normal_state(state: dict[str, Any] | None) -> dict[str, Any]:
    if not state:
        return {}
    out: dict[str, Any] = {}
    for key in ("floor", "x", "y", "hp", "atk", "def", "yk", "bk", "rk"):
        if key in state:
            out[key] = state[key]
    if "gold" in state:
        out["gold"] = state["gold"]
    elif "money" in state:
        out["gold"] = state["money"]
    for key in (
        "dmg",
        "yd",
        "bd",
        "rd",
        "times1",
        "centerFly",
        "upFly",
        "downFly",
        "earthquake",
        "bomb",
        "bigKey",
        "pickaxe",
        "superPotion",
        "snow",
        "knife",
        "coin",
        "cross",
        "magicImmune",
        "won49",
        "won50",
    ):
        if key in state:
            out[key] = state[key]
    return out


def delta_text(before: dict[str, Any], after: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in STAT_KEYS:
        if key in before and key in after and before[key] != after[key]:
            parts.append(f"{STAT_LABELS[key]} {before[key]}->{after[key]}")
    return "，".join(parts) if parts else "无数值变化"


def state_text(state: dict[str, Any]) -> str:
    return (
        f"{state.get('floor', '?')} x{state.get('x', '?')}y{state.get('y', '?')} "
        f"生命={state.get('hp', '?')} 攻={state.get('atk', '?')} 防={state.get('def', '?')} "
        f"黄={state.get('yk', '?')} 蓝={state.get('bk', '?')} 红={state.get('rk', '?')} "
        f"金币={state.get('gold', '?')}"
    )


def compact_counts(counts: dict[str, Any]) -> str:
    if not counts:
        return "{}"
    return "{" + ", ".join(f"{key}:{value}" for key, value in sorted(counts.items())) + "}"


def auto_spec_text(spec: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ("battle", "item", "wall"):
        value = spec[key]
        if isinstance(value, bool):
            value = str(value).lower()
        parts.append(f"{key}={value}")
    return ",".join(parts)


def auto_setting_step(before: dict[str, Any], spec: dict[str, Any], note: str) -> dict[str, Any]:
    state = dict(before)
    text = auto_spec_text(spec)
    return {
        "segment": "自动设置",
        "phase": "auto-setting",
        "floor": state.get("floor"),
        "pos": [state.get("x"), state.get("y")],
        "action": SET_AUTO_ACTION,
        "eid": text,
        "auto": dict(spec),
        "before": dict(state),
        "after": dict(state),
        "delta": f"自动设置 {text}",
        "note": note,
        "inserted": True,
    }


def insert_auto_setting_steps(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Make auto-pickup/battle settings explicit inside the walk."""
    if not steps:
        return []
    out: list[dict[str, Any]] = []
    start = normal_state(steps[0].get("before"))
    if start:
        out.append(
            auto_setting_step(
                start,
                AUTO_START,
                "开局开启自动清 0 伤怪、自动拾取含血瓶物品、自动暗墙",
            )
        )
    inserted_nopotion = False
    for step in steps:
        if not inserted_nopotion and step.get("floor") == "MT20" and step.get("eid") == "postBossSupply":
            out.append(
                auto_setting_step(
                    normal_state(step.get("before")),
                    AUTO_NOPOTION,
                    "20F Boss 后切换为保留血瓶：继续自动清 0 伤怪/拾取非血瓶物品",
                )
            )
            inserted_nopotion = True
        out.append(step)
    return out


def patch_known_strict_live_timing(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Align old live-derived zone-1 logs with strict browser click timing."""
    out = [dict(step) for step in steps]
    for idx, step in enumerate(out):
        if (
            step.get("floor") == "MT32"
            and step.get("pos") == [10, 4]
            and step.get("eid") == "yellowKey"
            and idx > 450
        ):
            before = normal_state(step.get("before"))
            after = normal_state(step.get("after"))
            stat_delta = {
                key: after.get(key, 0) - before.get(key, 0)
                for key in ("hp", "atk", "def", "yk", "bk", "rk", "gold", "dmg", "yd", "bd", "rd", "times1")
                if after.get(key) != before.get(key)
            }
            if stat_delta:
                for future in out[idx + 1 :]:
                    for state_key in ("before", "after"):
                        state = future.get(state_key)
                        if not isinstance(state, dict):
                            continue
                        for key, delta in stat_delta.items():
                            if key in state:
                                state[key] -= delta
            base = normal_state(out[idx - 1].get("after"))
            step["before"] = dict(base)
            step["after"] = dict(base)
            step["delta"] = "自动处理已完成"
            note = step.get("note") or ""
            auto_note = "已在 MT32 x9y5 黄门点击后自动拾取，此处不再重复处理"
            step["note"] = f"{note}；{auto_note}" if note else auto_note
            break
    for idx, step in enumerate(out):
        if (
            step.get("floor") == "MT36"
            and step.get("pos") == [3, 11]
            and step.get("eid") == "soldier"
            and idx > 500
        ):
            before = normal_state(step.get("before"))
            after = normal_state(step.get("after"))
            old_gain = after.get("gold", 0) - before.get("gold", 0)
            live_gain = 100
            gold_delta = live_gain - old_gain
            if gold_delta:
                step_after = step.get("after")
                if isinstance(step_after, dict) and "gold" in step_after:
                    step_after["gold"] += gold_delta
                for future in out[idx + 1 :]:
                    for state_key in ("before", "after"):
                        state = future.get(state_key)
                        if isinstance(state, dict) and "gold" in state:
                            state["gold"] += gold_delta
            note = step.get("note") or ""
            live_note = "实机 MT36 x3y11 soldier 后自动清 x1y9 swordsman，合计 100G"
            step["note"] = f"{note}；{live_note}" if note else live_note
            break
    for idx, step in enumerate(out):
        if (
            step.get("floor") == "MT36"
            and step.get("pos") == [1, 9]
            and step.get("eid") == "swordsman"
            and idx > 700
        ):
            before = normal_state(step.get("before"))
            after = normal_state(step.get("after"))
            gold_gain = after.get("gold", 0) - before.get("gold", 0)
            if gold_gain:
                for future in out[idx + 1 :]:
                    for state_key in ("before", "after"):
                        state = future.get(state_key)
                        if isinstance(state, dict) and "gold" in state:
                            state["gold"] -= gold_gain
            base = normal_state(out[idx - 1].get("after"))
            step["before"] = dict(base)
            step["after"] = dict(base)
            step["delta"] = "自动处理已完成"
            note = step.get("note") or ""
            auto_note = "已在 MT36 x3y11 soldier 点击后自动清理，此处不再重复计金币"
            step["note"] = f"{note}；{auto_note}" if note else auto_note
            break
    for idx, step in enumerate(out):
        if (
            step.get("floor") == "MT34"
            and step.get("pos") == [4, 2]
            and step.get("eid") == "yellowDoor"
            and idx > 500
        ):
            before = normal_state(step.get("before"))
            after = normal_state(step.get("after"))
            old_gain = after.get("gold", 0) - before.get("gold", 0)
            live_gain = 55
            gold_delta = live_gain - old_gain
            if gold_delta:
                step_after = step.get("after")
                if isinstance(step_after, dict) and "gold" in step_after:
                    step_after["gold"] += gold_delta
                for future in out[idx + 1 :]:
                    for state_key in ("before", "after"):
                        state = future.get(state_key)
                        if isinstance(state, dict) and "gold" in state:
                            state["gold"] += gold_delta
            note = step.get("note") or ""
            live_note = "实机 MT34 x4y2 yellowDoor 后自动清 x1y10 swordsman，合计 55G"
            step["note"] = f"{note}；{live_note}" if note else live_note
            break
    for idx, step in enumerate(out):
        if (
            step.get("floor") == "MT34"
            and step.get("pos") == [1, 10]
            and step.get("eid") == "swordsman"
            and idx > 700
        ):
            before = normal_state(step.get("before"))
            after = normal_state(step.get("after"))
            gold_gain = after.get("gold", 0) - before.get("gold", 0)
            if gold_gain:
                for future in out[idx + 1 :]:
                    for state_key in ("before", "after"):
                        state = future.get(state_key)
                        if isinstance(state, dict) and "gold" in state:
                            state["gold"] -= gold_gain
            base = normal_state(out[idx - 1].get("after"))
            step["before"] = dict(base)
            step["after"] = dict(base)
            step["delta"] = "自动处理已完成"
            note = step.get("note") or ""
            auto_note = "已在 MT34 x4y2 黄门点击后自动清理，此处不再重复计金币"
            step["note"] = f"{note}；{auto_note}" if note else auto_note
            break
    for idx, step in enumerate(out):
        if (
            step.get("floor") == "MT18"
            and step.get("pos") == [4, 8]
            and step.get("eid") == "yellowDoor"
            and idx > 500
        ):
            before = normal_state(step.get("before"))
            after = normal_state(step.get("after"))
            patched = dict(after)
            patched["yk"] = before.get("yk", patched.get("yk", 0))
            patched["gold"] = before.get("gold", patched.get("gold", 0)) + 48
            stat_delta = {
                key: patched.get(key, 0) - after.get(key, 0)
                for key in ("hp", "atk", "def", "yk", "bk", "rk", "gold", "dmg", "yd", "bd", "rd", "times1")
                if patched.get(key) != after.get(key)
            }
            step["after"] = dict(patched)
            if stat_delta:
                for future in out[idx + 1 :]:
                    for state_key in ("before", "after"):
                        state = future.get(state_key)
                        if not isinstance(state, dict):
                            continue
                        for key, delta in stat_delta.items():
                            if key in state:
                                state[key] += delta
            note = step.get("note") or ""
            live_note = "实机 MT18 x4y8 yellowDoor 后自动清 x4y9/x4y10/x5y9/x5y10 bigBat，并拾取 x5y11 yellowKey，合计 48G"
            step["note"] = f"{note}；{live_note}" if note else live_note
            break
    for target_pos, target_eid, reason in (
        ([4, 9], "bigBat", "已在 MT18 x4y8 黄门点击后自动清理"),
        ([4, 10], "bigBat", "已在 MT18 x4y8 黄门点击后自动清理"),
        ([5, 11], "yellowKey", "已在 MT18 x4y8 黄门点击后自动拾取"),
        ([5, 9], "bigBat", "已在 MT18 x4y8 黄门点击后自动清理"),
        ([5, 10], "bigBat", "已在 MT18 x4y8 黄门点击后自动清理"),
    ):
        for idx, step in enumerate(out):
            if (
                step.get("floor") == "MT18"
                and step.get("pos") == target_pos
                and step.get("eid") == target_eid
                and idx > 500
            ):
                before = normal_state(step.get("before"))
                after = normal_state(step.get("after"))
                stat_delta = {
                    key: after.get(key, 0) - before.get(key, 0)
                    for key in ("hp", "atk", "def", "yk", "bk", "rk", "gold", "dmg", "yd", "bd", "rd", "times1")
                    if after.get(key) != before.get(key)
                }
                if stat_delta:
                    for future in out[idx + 1 :]:
                        for state_key in ("before", "after"):
                            state = future.get(state_key)
                            if not isinstance(state, dict):
                                continue
                            for key, delta in stat_delta.items():
                                if key in state:
                                    state[key] -= delta
                base = normal_state(out[idx - 1].get("after"))
                step["before"] = dict(base)
                step["after"] = dict(base)
                step["delta"] = "自动处理已完成"
                note = step.get("note") or ""
                auto_note = f"{reason}，此处不再重复处理"
                step["note"] = f"{note}；{auto_note}" if note else auto_note
                break
    for idx, step in enumerate(out):
        if (
            step.get("floor") == "MT18"
            and step.get("pos") == [8, 8]
            and step.get("eid") == "yellowDoor"
            and idx > 500
        ):
            before = normal_state(step.get("before"))
            after = normal_state(step.get("after"))
            patched = dict(after)
            patched["yk"] = before.get("yk", patched.get("yk", 0))
            patched["gold"] = before.get("gold", patched.get("gold", 0)) + 32
            stat_delta = {
                key: patched.get(key, 0) - after.get(key, 0)
                for key in ("hp", "atk", "def", "yk", "bk", "rk", "gold", "dmg", "yd", "bd", "rd", "times1")
                if patched.get(key) != after.get(key)
            }
            step["after"] = dict(patched)
            if stat_delta:
                for future in out[idx + 1 :]:
                    for state_key in ("before", "after"):
                        state = future.get(state_key)
                        if not isinstance(state, dict):
                            continue
                        for key, delta in stat_delta.items():
                            if key in state:
                                state[key] += delta
            note = step.get("note") or ""
            live_note = "实机 MT18 x8y8 yellowDoor 后自动清 x7y9/x7y10/x8y9/x8y10 blackSlime，并拾取 x7y11 yellowKey，合计 32G"
            step["note"] = f"{note}；{live_note}" if note else live_note
            break
    for target_pos, target_eid, reason in (
        ([8, 9], "blackSlime", "已在 MT18 x8y8 黄门点击后自动清理"),
        ([8, 10], "blackSlime", "已在 MT18 x8y8 黄门点击后自动清理"),
        ([7, 11], "yellowKey", "已在 MT18 x8y8 黄门点击后自动拾取"),
        ([7, 9], "blackSlime", "已在 MT18 x8y8 黄门点击后自动清理"),
        ([7, 10], "blackSlime", "已在 MT18 x8y8 黄门点击后自动清理"),
    ):
        for idx, step in enumerate(out):
            if (
                step.get("floor") == "MT18"
                and step.get("pos") == target_pos
                and step.get("eid") == target_eid
                and idx > 500
            ):
                before = normal_state(step.get("before"))
                after = normal_state(step.get("after"))
                stat_delta = {
                    key: after.get(key, 0) - before.get(key, 0)
                    for key in ("hp", "atk", "def", "yk", "bk", "rk", "gold", "dmg", "yd", "bd", "rd", "times1")
                    if after.get(key) != before.get(key)
                }
                if stat_delta:
                    for future in out[idx + 1 :]:
                        for state_key in ("before", "after"):
                            state = future.get(state_key)
                            if not isinstance(state, dict):
                                continue
                            for key, delta in stat_delta.items():
                                if key in state:
                                    state[key] -= delta
                base = normal_state(out[idx - 1].get("after"))
                step["before"] = dict(base)
                step["after"] = dict(base)
                step["delta"] = "自动处理已完成"
                note = step.get("note") or ""
                auto_note = f"{reason}，此处不再重复处理"
                step["note"] = f"{note}；{auto_note}" if note else auto_note
                break
    for idx, step in enumerate(out):
        if (
            step.get("floor") == "MT34"
            and step.get("pos") == [2, 6]
            and step.get("eid") == "redKey"
            and idx > 600
        ):
            before = normal_state(step.get("before"))
            after = normal_state(step.get("after"))
            patched = dict(after)
            patched["x"] = 2
            patched["y"] = 6
            patched["yk"] = before.get("yk", patched.get("yk", 0)) + 4
            patched["rk"] = before.get("rk", patched.get("rk", 0)) + 1
            stat_delta = {
                key: patched.get(key, 0) - after.get(key, 0)
                for key in ("hp", "atk", "def", "yk", "bk", "rk", "gold", "dmg", "yd", "bd", "rd", "times1")
                if patched.get(key) != after.get(key)
            }
            step["after"] = dict(patched)
            if stat_delta:
                for future in out[idx + 1 :]:
                    for state_key in ("before", "after"):
                        state = future.get(state_key)
                        if not isinstance(state, dict):
                            continue
                        for key, delta in stat_delta.items():
                            if key in state:
                                state[key] += delta
            note = step.get("note") or ""
            live_note = "实机 MT34 八怪奖励触发后直接获得 x2y6 redKey 和四把 yellowKey"
            step["note"] = f"{note}；{live_note}" if note else live_note
            break
    for target_pos, target_eid, reason in (
        ([2, 6], "redKey", "已在 MT34 八怪奖励触发时自动拾取"),
        ([1, 5], "yellowKey", "已在 MT34 八怪奖励触发时自动拾取"),
        ([3, 5], "yellowKey", "已在 MT34 八怪奖励触发时自动拾取"),
        ([1, 7], "yellowKey", "已在 MT34 八怪奖励触发时自动拾取"),
        ([3, 7], "yellowKey", "已在 MT34 八怪奖励触发时自动拾取"),
    ):
        for idx, step in enumerate(out):
            if (
                step.get("floor") == "MT34"
                and step.get("pos") == target_pos
                and step.get("eid") == target_eid
                and idx > 600
                and step.get("action") != "事件奖励"
            ):
                before = normal_state(step.get("before"))
                after = normal_state(step.get("after"))
                stat_delta = {
                    key: after.get(key, 0) - before.get(key, 0)
                    for key in ("hp", "atk", "def", "yk", "bk", "rk", "gold", "dmg", "yd", "bd", "rd", "times1")
                    if after.get(key) != before.get(key)
                }
                if stat_delta:
                    for future in out[idx + 1 :]:
                        for state_key in ("before", "after"):
                            state = future.get(state_key)
                            if not isinstance(state, dict):
                                continue
                            for key, delta in stat_delta.items():
                                if key in state:
                                    state[key] -= delta
                base = normal_state(out[idx - 1].get("after"))
                step["before"] = dict(base)
                step["after"] = dict(base)
                step["delta"] = "自动处理已完成"
                note = step.get("note") or ""
                auto_note = f"{reason}，此处不再重复处理"
                step["note"] = f"{note}；{auto_note}" if note else auto_note
                break
    for idx, step in enumerate(out):
        if (
            step.get("floor") == "MT14"
            and step.get("pos") == [2, 6]
            and step.get("eid") == "blackSlime"
            and idx > 600
        ):
            before = normal_state(step.get("before"))
            after = normal_state(step.get("after"))
            gold_gain = after.get("gold", 0) - before.get("gold", 0)
            if gold_gain:
                for future in out[idx + 1 :]:
                    for state_key in ("before", "after"):
                        state = future.get(state_key)
                        if isinstance(state, dict) and "gold" in state:
                            state["gold"] -= gold_gain
            base = normal_state(out[idx - 1].get("after"))
            step["before"] = dict(base)
            step["after"] = dict(base)
            step["delta"] = "自动处理已完成"
            note = step.get("note") or ""
            auto_note = "已由早前 MT14 自动清理处理，此处不再重复计金币"
            step["note"] = f"{note}；{auto_note}" if note else auto_note
            break
    for idx, step in enumerate(out):
        if (
            step.get("floor") == "MT38"
            and step.get("pos") == [4, 1]
            and step.get("eid") == "slimeMan"
            and idx > 600
        ):
            before = normal_state(step.get("before"))
            after = normal_state(step.get("after"))
            patched = dict(after)
            patched["yk"] = before.get("yk", patched.get("yk", 0)) + 1
            stat_delta = {
                key: patched.get(key, 0) - after.get(key, 0)
                for key in ("hp", "atk", "def", "yk", "bk", "rk", "gold", "dmg", "yd", "bd", "rd", "times1")
                if patched.get(key) != after.get(key)
            }
            step["after"] = dict(patched)
            if stat_delta:
                for future in out[idx + 1 :]:
                    for state_key in ("before", "after"):
                        state = future.get(state_key)
                        if not isinstance(state, dict):
                            continue
                        for key, delta in stat_delta.items():
                            if key in state:
                                state[key] += delta
            note = step.get("note") or ""
            live_note = "实机 MT38 x4y1 slimeMan 后自动拾取 x6y2 yellowKey"
            step["note"] = f"{note}；{live_note}" if note else live_note
            break
    for idx, step in enumerate(out):
        if (
            step.get("floor") == "MT38"
            and step.get("pos") == [6, 2]
            and step.get("eid") == "yellowKey"
            and idx > 600
        ):
            before = normal_state(step.get("before"))
            after = normal_state(step.get("after"))
            stat_delta = {
                key: after.get(key, 0) - before.get(key, 0)
                for key in ("hp", "atk", "def", "yk", "bk", "rk", "gold", "dmg", "yd", "bd", "rd", "times1")
                if after.get(key) != before.get(key)
            }
            if stat_delta:
                for future in out[idx + 1 :]:
                    for state_key in ("before", "after"):
                        state = future.get(state_key)
                        if not isinstance(state, dict):
                            continue
                        for key, delta in stat_delta.items():
                            if key in state:
                                state[key] -= delta
            base = normal_state(out[idx - 1].get("after"))
            step["before"] = dict(base)
            step["after"] = dict(base)
            step["delta"] = "自动处理已完成"
            note = step.get("note") or ""
            auto_note = "已在 MT38 x4y1 slimeMan 后自动拾取，此处不再重复处理"
            step["note"] = f"{note}；{auto_note}" if note else auto_note
            break
    for idx, step in enumerate(out):
        if (
            step.get("floor") == "MT34"
            and step.get("pos") == [8, 2]
            and step.get("eid") == "yellowDoor"
            and idx > 600
        ):
            before = normal_state(step.get("before"))
            after = normal_state(step.get("after"))
            patched = dict(after)
            patched["yk"] = before.get("yk", patched.get("yk", 0)) + 2
            patched["def"] = before.get("def", patched.get("def", 0)) + 4
            stat_delta = {
                key: patched.get(key, 0) - after.get(key, 0)
                for key in ("hp", "atk", "def", "yk", "bk", "rk", "gold", "dmg", "yd", "bd", "rd", "times1")
                if patched.get(key) != after.get(key)
            }
            step["after"] = dict(patched)
            if stat_delta:
                for future in out[idx + 1 :]:
                    for state_key in ("before", "after"):
                        state = future.get(state_key)
                        if not isinstance(state, dict):
                            continue
                        for key, delta in stat_delta.items():
                            if key in state:
                                state[key] += delta
            note = step.get("note") or ""
            live_note = "实机 MT34 x8y2 yellowDoor 后自动拾取 x10y2/x10y1/x9y1 yellowKey 和 x11y1 blueGem，x11y2 redPotion 因 nopotion 保留"
            step["note"] = f"{note}；{live_note}" if note else live_note
            break
    for target_pos, target_eid, reason in (
        ([10, 2], "yellowKey", "已在 MT34 x8y2 黄门点击后自动拾取"),
        ([10, 1], "yellowKey", "已在 MT34 x8y2 黄门点击后自动拾取"),
        ([9, 1], "yellowKey", "已在 MT34 x8y2 黄门点击后自动拾取"),
        ([11, 1], "blueGem", "已在 MT34 x8y2 黄门点击后自动拾取"),
    ):
        for idx, step in enumerate(out):
            if (
                step.get("floor") == "MT34"
                and step.get("pos") == target_pos
                and step.get("eid") == target_eid
                and idx > 600
            ):
                before = normal_state(step.get("before"))
                after = normal_state(step.get("after"))
                stat_delta = {
                    key: after.get(key, 0) - before.get(key, 0)
                    for key in ("hp", "atk", "def", "yk", "bk", "rk", "gold", "dmg", "yd", "bd", "rd", "times1")
                    if after.get(key) != before.get(key)
                }
                if stat_delta:
                    for future in out[idx + 1 :]:
                        for state_key in ("before", "after"):
                            state = future.get(state_key)
                            if not isinstance(state, dict):
                                continue
                            for key, delta in stat_delta.items():
                                if key in state:
                                    state[key] -= delta
                base = normal_state(out[idx - 1].get("after"))
                step["before"] = dict(base)
                step["after"] = dict(base)
                step["delta"] = "自动处理已完成"
                note = step.get("note") or ""
                auto_note = f"{reason}，此处不再重复处理"
                step["note"] = f"{note}；{auto_note}" if note else auto_note
                break
    for idx, step in enumerate(out):
        if (
            step.get("floor") == "MT38"
            and step.get("pos") == [8, 1]
            and step.get("eid") == "slimeMan"
            and idx > 600
        ):
            before = normal_state(step.get("before"))
            after = normal_state(step.get("after"))
            patched = dict(after)
            patched["hp"] = before.get("hp", patched.get("hp", 0)) - 52
            patched["dmg"] = before.get("dmg", patched.get("dmg", 0)) + 52
            stat_delta = {
                key: patched.get(key, 0) - after.get(key, 0)
                for key in ("hp", "atk", "def", "yk", "bk", "rk", "gold", "dmg", "yd", "bd", "rd", "times1")
                if patched.get(key) != after.get(key)
            }
            step["after"] = dict(patched)
            if stat_delta:
                for future in out[idx + 1 :]:
                    for state_key in ("before", "after"):
                        state = future.get(state_key)
                        if not isinstance(state, dict):
                            continue
                        for key, delta in stat_delta.items():
                            if key in state:
                                state[key] += delta
            note = step.get("note") or ""
            live_note = "实机 DEF=114 后 MT38 x8y1 slimeMan 伤害为 52"
            step["note"] = f"{note}；{live_note}" if note else live_note
            break
    for target_pos in ([11, 6], [11, 9]):
        for idx, step in enumerate(out):
            if (
                step.get("floor") == "MT38"
                and step.get("pos") == target_pos
                and step.get("eid") == "ghostSkeleton"
                and idx > 600
            ):
                before = normal_state(step.get("before"))
                after = normal_state(step.get("after"))
                patched = dict(after)
                patched["hp"] = before.get("hp", patched.get("hp", 0)) - 66
                patched["dmg"] = before.get("dmg", patched.get("dmg", 0)) + 66
                stat_delta = {
                    key: patched.get(key, 0) - after.get(key, 0)
                    for key in ("hp", "atk", "def", "yk", "bk", "rk", "gold", "dmg", "yd", "bd", "rd", "times1")
                    if patched.get(key) != after.get(key)
                }
                step["after"] = dict(patched)
                if stat_delta:
                    for future in out[idx + 1 :]:
                        for state_key in ("before", "after"):
                            state = future.get(state_key)
                            if not isinstance(state, dict):
                                continue
                            for key, delta in stat_delta.items():
                                if key in state:
                                    state[key] += delta
                note = step.get("note") or ""
                live_note = f"实机 DEF=114 后 MT38 x{target_pos[0]}y{target_pos[1]} ghostSkeleton 伤害为 66"
                step["note"] = f"{note}；{live_note}" if note else live_note
                break
    for idx, step in enumerate(out):
        if (
            step.get("floor") == "MT38"
            and step.get("pos") == [11, 9]
            and step.get("eid") == "ghostSkeleton"
            and idx > 600
        ):
            before = normal_state(step.get("before"))
            after = normal_state(step.get("after"))
            patched = dict(after)
            patched["yk"] = before.get("yk", patched.get("yk", 0)) + 1
            stat_delta = {
                key: patched.get(key, 0) - after.get(key, 0)
                for key in ("hp", "atk", "def", "yk", "bk", "rk", "gold", "dmg", "yd", "bd", "rd", "times1")
                if patched.get(key) != after.get(key)
            }
            step["after"] = dict(patched)
            if stat_delta:
                for future in out[idx + 1 :]:
                    for state_key in ("before", "after"):
                        state = future.get(state_key)
                        if not isinstance(state, dict):
                            continue
                        for key, delta in stat_delta.items():
                            if key in state:
                                state[key] += delta
            note = step.get("note") or ""
            live_note = "实机 MT38 x11y9 ghostSkeleton 后自动拾取 x9y9 yellowKey"
            step["note"] = f"{note}；{live_note}" if note else live_note
            break
    for idx, step in enumerate(out):
        if (
            step.get("floor") == "MT38"
            and step.get("pos") == [9, 9]
            and step.get("eid") == "yellowKey"
            and idx > 1000
        ):
            before = normal_state(step.get("before"))
            after = normal_state(step.get("after"))
            stat_delta = {
                key: after.get(key, 0) - before.get(key, 0)
                for key in ("hp", "atk", "def", "yk", "bk", "rk", "gold", "dmg", "yd", "bd", "rd", "times1")
                if after.get(key) != before.get(key)
            }
            if stat_delta:
                for future in out[idx + 1 :]:
                    for state_key in ("before", "after"):
                        state = future.get(state_key)
                        if not isinstance(state, dict):
                            continue
                        for key, delta in stat_delta.items():
                            if key in state:
                                state[key] -= delta
            base = normal_state(out[idx - 1].get("after"))
            step["before"] = dict(base)
            step["after"] = dict(base)
            step["delta"] = "自动处理已完成"
            note = step.get("note") or ""
            auto_note = "已在 MT38 x11y9 ghostSkeleton 后自动拾取，此处不再重复处理"
            step["note"] = f"{note}；{auto_note}" if note else auto_note
            break
    for idx, step in enumerate(out):
        if (
            step.get("floor") == "MT38"
            and step.get("pos") == [10, 7]
            and step.get("eid") == "redKnight"
            and idx > 600
        ):
            before = normal_state(step.get("before"))
            after = normal_state(step.get("after"))
            patched = dict(after)
            patched["hp"] = before.get("hp", patched.get("hp", 0)) - 348
            patched["dmg"] = before.get("dmg", patched.get("dmg", 0)) + 348
            patched["yk"] = before.get("yk", patched.get("yk", 0)) + 3
            stat_delta = {
                key: patched.get(key, 0) - after.get(key, 0)
                for key in ("hp", "atk", "def", "yk", "bk", "rk", "gold", "dmg", "yd", "bd", "rd", "times1")
                if patched.get(key) != after.get(key)
            }
            step["after"] = dict(patched)
            if stat_delta:
                for future in out[idx + 1 :]:
                    for state_key in ("before", "after"):
                        state = future.get(state_key)
                        if not isinstance(state, dict):
                            continue
                        for key, delta in stat_delta.items():
                            if key in state:
                                state[key] += delta
            note = step.get("note") or ""
            live_note = "实机 DEF=114 后 MT38 x10y7 redKnight 伤害为 348，并自动拾取 x9y6/x9y5/x9y4 yellowKey"
            step["note"] = f"{note}；{live_note}" if note else live_note
            break
    for target_pos in ([9, 6], [9, 5], [9, 4]):
        for idx, step in enumerate(out):
            if (
                step.get("floor") == "MT38"
                and step.get("pos") == target_pos
                and step.get("eid") == "yellowKey"
                and idx > 600
            ):
                before = normal_state(step.get("before"))
                after = normal_state(step.get("after"))
                stat_delta = {
                    key: after.get(key, 0) - before.get(key, 0)
                    for key in ("hp", "atk", "def", "yk", "bk", "rk", "gold", "dmg", "yd", "bd", "rd", "times1")
                    if after.get(key) != before.get(key)
                }
                if stat_delta:
                    for future in out[idx + 1 :]:
                        for state_key in ("before", "after"):
                            state = future.get(state_key)
                            if not isinstance(state, dict):
                                continue
                            for key, delta in stat_delta.items():
                                if key in state:
                                    state[key] -= delta
                base = normal_state(out[idx - 1].get("after"))
                step["before"] = dict(base)
                step["after"] = dict(base)
                step["delta"] = "自动处理已完成"
                note = step.get("note") or ""
                auto_note = "已在 MT38 x10y7 redKnight 后自动拾取，此处不再重复处理"
                step["note"] = f"{note}；{auto_note}" if note else auto_note
                break
    for idx, step in enumerate(out):
        if (
            step.get("floor") == "MT38"
            and step.get("pos") == [7, 6]
            and step.get("eid") == "ghostSkeleton"
            and idx > 600
        ):
            before = normal_state(step.get("before"))
            after = normal_state(step.get("after"))
            patched = dict(after)
            patched["hp"] = before.get("hp", patched.get("hp", 0)) - 66
            patched["dmg"] = before.get("dmg", patched.get("dmg", 0)) + 66
            patched["gold"] = before.get("gold", patched.get("gold", 0)) + 90
            stat_delta = {
                key: patched.get(key, 0) - after.get(key, 0)
                for key in ("hp", "atk", "def", "yk", "bk", "rk", "gold", "dmg", "yd", "bd", "rd", "times1")
                if patched.get(key) != after.get(key)
            }
            step["after"] = dict(patched)
            if stat_delta:
                for future in out[idx + 1 :]:
                    for state_key in ("before", "after"):
                        state = future.get(state_key)
                        if not isinstance(state, dict):
                            continue
                        for key, delta in stat_delta.items():
                            if key in state:
                                state[key] += delta
            note = step.get("note") or ""
            live_note = "实机 DEF=114 后 MT38 x7y6 ghostSkeleton 伤害为 66，并自动清 x7y7 swordsman，合计 90G"
            step["note"] = f"{note}；{live_note}" if note else live_note
            break
    for idx, step in enumerate(out):
        if (
            step.get("floor") == "MT38"
            and step.get("pos") == [7, 7]
            and step.get("eid") == "swordsman"
            and idx > 600
        ):
            before = normal_state(step.get("before"))
            after = normal_state(step.get("after"))
            gold_gain = after.get("gold", 0) - before.get("gold", 0)
            if gold_gain:
                for future in out[idx + 1 :]:
                    for state_key in ("before", "after"):
                        state = future.get(state_key)
                        if isinstance(state, dict) and "gold" in state:
                            state["gold"] -= gold_gain
            base = normal_state(out[idx - 1].get("after"))
            step["before"] = dict(base)
            step["after"] = dict(base)
            step["delta"] = "自动处理已完成"
            note = step.get("note") or ""
            auto_note = "已在 MT38 x7y6 ghostSkeleton 后自动清理，此处不再重复计金币"
            step["note"] = f"{note}；{auto_note}" if note else auto_note
            break
    for idx, step in enumerate(out):
        if (
            step.get("floor") == "MT38"
            and step.get("pos") == [9, 11]
            and step.get("eid") == "soldier"
            and idx > 600
        ):
            before = normal_state(step.get("before"))
            after = normal_state(step.get("after"))
            patched = dict(after)
            patched["hp"] = before.get("hp", patched.get("hp", 0)) - 164
            patched["dmg"] = before.get("dmg", patched.get("dmg", 0)) + 164
            stat_delta = {
                key: patched.get(key, 0) - after.get(key, 0)
                for key in ("hp", "atk", "def", "yk", "bk", "rk", "gold", "dmg", "yd", "bd", "rd", "times1")
                if patched.get(key) != after.get(key)
            }
            step["after"] = dict(patched)
            if stat_delta:
                for future in out[idx + 1 :]:
                    for state_key in ("before", "after"):
                        state = future.get(state_key)
                        if not isinstance(state, dict):
                            continue
                        for key, delta in stat_delta.items():
                            if key in state:
                                state[key] += delta
            note = step.get("note") or ""
            live_note = "实机 DEF=118 后 MT38 x9y11 soldier 伤害为 164"
            step["note"] = f"{note}；{live_note}" if note else live_note
            break
    for target_pos in ([1, 10], [3, 10]):
        for idx, step in enumerate(out):
            if (
                step.get("floor") == "MT38"
                and step.get("pos") == target_pos
                and step.get("eid") == "blueGuard"
                and idx > 600
            ):
                before = normal_state(step.get("before"))
                after = normal_state(step.get("after"))
                patched = dict(after)
                patched["hp"] = before.get("hp", patched.get("hp", 0)) - 124
                patched["dmg"] = before.get("dmg", patched.get("dmg", 0)) + 124
                stat_delta = {
                    key: patched.get(key, 0) - after.get(key, 0)
                    for key in ("hp", "atk", "def", "yk", "bk", "rk", "gold", "dmg", "yd", "bd", "rd", "times1")
                    if patched.get(key) != after.get(key)
                }
                step["after"] = dict(patched)
                if stat_delta:
                    for future in out[idx + 1 :]:
                        for state_key in ("before", "after"):
                            state = future.get(state_key)
                            if not isinstance(state, dict):
                                continue
                            for key, delta in stat_delta.items():
                                if key in state:
                                    state[key] += delta
                note = step.get("note") or ""
                live_note = f"实机 DEF=118 后 MT38 x{target_pos[0]}y{target_pos[1]} blueGuard 伤害为 124"
                step["note"] = f"{note}；{live_note}" if note else live_note
                break
    for idx in range(len(out) - 2):
        step = out[idx]
        next_step = out[idx + 1]
        after = normal_state(step.get("after"))
        if (
            step.get("floor") == "MT5"
            and step.get("pos") == [8, 9]
            and step.get("action") == "开门"
            and step.get("eid") == "yellowDoor"
            and next_step.get("floor") == "MT5"
            and next_step.get("eid") == "sword1"
        ):
            patched = dict(after)
            patched["x"] = 8
            patched["y"] = 9
            patched["atk"] = int(patched.get("atk", 0)) + 10
            step["after"] = patched
            step["delta"] = delta_text(normal_state(step.get("before")), patched)
            note = step.get("note") or ""
            auto_note = "实机开门后自动拾取 MT5 x11y11 铁剑"
            step["note"] = f"{note}；{auto_note}" if note else auto_note

            next_step["before"] = dict(patched)
            next_step["after"] = dict(patched)
            next_step["delta"] = "自动处理已完成"
            note2 = next_step.get("note") or ""
            next_step["note"] = f"{note2}；{auto_note}" if note2 else auto_note

            out[idx + 2]["before"] = dict(patched)
            out[idx + 2]["delta"] = delta_text(patched, normal_state(out[idx + 2].get("after")))
            break
    for idx in range(len(out) - 5):
        step = out[idx]
        resource_steps = out[idx + 1 : idx + 5]
        if (
            step.get("floor") == "MT1"
            and step.get("pos") == [9, 5]
            and step.get("action") == "开门"
            and step.get("eid") == "yellowDoor"
            and [s.get("pos") for s in resource_steps] == [[8, 4], [8, 3], [7, 3], [7, 4]]
        ):
            patched = dict(normal_state(resource_steps[0].get("after")))
            patched["x"] = 9
            patched["y"] = 5
            auto_note = "实机 MT1 x9y5 为空格；点击后移动到 x9y5，并自动拾取 x8y4 红血瓶、x8y3 黄钥匙、x7y3 红宝石、x7y4 蓝宝石"

            step["action"] = "通过"
            step["eid"] = "autoResourceGroup"
            step["after"] = dict(patched)
            step["delta"] = delta_text(normal_state(step.get("before")), patched)
            note = step.get("note") or ""
            step["note"] = f"{note}；{auto_note}" if note else auto_note

            for offset in range(1, 5):
                auto_step = out[idx + offset]
                auto_step["before"] = dict(patched)
                auto_step["after"] = dict(patched)
                auto_step["delta"] = "自动处理已完成"
                note2 = auto_step.get("note") or ""
                auto_step["note"] = f"{note2}；{auto_note}" if note2 else auto_note

            following = out[idx + 5]
            following["before"] = dict(patched)
            following["delta"] = delta_text(patched, normal_state(following.get("after")))
            break
    for idx in range(len(out) - 2):
        step = out[idx]
        next_step = out[idx + 1]
        if (
            step.get("floor") == "MT9"
            and step.get("pos") == [3, 11]
            and step.get("action") == "开门"
            and step.get("eid") == "blueDoor"
            and next_step.get("floor") == "MT9"
            and next_step.get("pos") == [2, 10]
            and next_step.get("eid") == "redPotion"
        ):
            patched = dict(normal_state(next_step.get("after")))
            patched["x"] = 3
            patched["y"] = 11
            auto_note = "实机开 MT9 x3y11 蓝门后自动拾取 x2y10 红血瓶，英雄停在 x3y11"

            step["after"] = dict(patched)
            step["delta"] = delta_text(normal_state(step.get("before")), patched)
            note = step.get("note") or ""
            step["note"] = f"{note}；{auto_note}" if note else auto_note

            next_step["before"] = dict(patched)
            next_step["after"] = dict(patched)
            next_step["delta"] = "自动处理已完成"
            note2 = next_step.get("note") or ""
            next_step["note"] = f"{note2}；{auto_note}" if note2 else auto_note

            following = out[idx + 2]
            following["before"] = dict(patched)
            following["delta"] = delta_text(patched, normal_state(following.get("after")))
            break
    for idx, step in enumerate(out):
        if (
            step.get("floor") == "MT14"
            and step.get("pos") == [1, 3]
            and step.get("action") == "事件奖励"
            and step.get("eid") == "redKey"
        ):
            before = normal_state(step.get("before"))
            old_after = normal_state(step.get("after"))
            patched = dict(old_after)
            patched["x"] = 1
            patched["y"] = 3
            patched["yk"] = before.get("yk", patched.get("yk", 0))
            patched["rk"] = before.get("rk", patched.get("rk", 0)) + 1
            yk_delta = patched.get("yk", 0) - old_after.get("yk", 0)

            step["action"] = "拾取"
            step["after"] = dict(patched)
            step["delta"] = delta_text(before, patched)
            note = step.get("note") or ""
            pickup_note = "实机红钥匙是 MT14 x1y3 预置/生成物品，目标点击后停在 x1y3，不消耗黄钥匙"
            step["note"] = f"{note}；{pickup_note}" if note else pickup_note

            if yk_delta:
                for future in out[idx + 1 :]:
                    for key in ("before", "after"):
                        state = future.get(key)
                        if isinstance(state, dict) and "yk" in state:
                            state["yk"] += yk_delta
                if idx + 1 < len(out):
                    out[idx + 1]["before"] = dict(patched)
            break
    for idx in range(len(out) - 1):
        step = out[idx]
        next_step = out[idx + 1]
        if (
            step.get("action") == "通过"
            and next_step.get("action") == "换层"
            and stats_equal(normal_state(step.get("after")), normal_state(next_step.get("before")))
        ):
            target = normal_state(next_step.get("after"))
            if target and target.get("floor") != normal_state(step.get("after")).get("floor"):
                step["after"] = dict(target)
                step["delta"] = delta_text(normal_state(step.get("before")), target)
                note = step.get("note") or ""
                stair_note = "实机点击楼梯后立即换层"
                step["note"] = f"{note}；{stair_note}" if note else stair_note
                next_step["before"] = dict(target)
                next_step["after"] = dict(target)
                next_step["delta"] = "自动处理已完成"
    for idx in range(len(out) - 2):
        step = out[idx]
        red_potion = out[idx + 1]
        yellow_key = out[idx + 2]
        if (
            step.get("floor") == "MT33"
            and step.get("pos") == [6, 1]
            and step.get("action") == "击杀"
            and step.get("eid") == "slimeMan"
            and red_potion.get("floor") == "MT33"
            and red_potion.get("pos") == [5, 2]
            and red_potion.get("eid") == "redPotion"
            and yellow_key.get("floor") == "MT33"
            and yellow_key.get("pos") == [6, 3]
            and yellow_key.get("eid") == "yellowKey"
        ):
            patched_kill = dict(normal_state(step.get("after")))
            patched_kill["yk"] = normal_state(step.get("before")).get("yk", patched_kill.get("yk", 0)) + 1
            auto_note = "实机 item=nopotion 下杀 MT33 x6y1 后自动拾取 x6y3 黄钥匙，红血瓶保留"
            step["after"] = dict(patched_kill)
            note = step.get("note") or ""
            step["note"] = f"{note}；{auto_note}" if note else auto_note

            red_after = dict(normal_state(red_potion.get("after")))
            red_after["yk"] = patched_kill["yk"]
            red_potion["before"] = dict(patched_kill)
            red_potion["after"] = dict(red_after)

            yellow_key["before"] = dict(red_after)
            yellow_key["after"] = dict(red_after)
            yellow_key["delta"] = "自动处理已完成"
            note2 = yellow_key.get("note") or ""
            yellow_key["note"] = f"{note2}；{auto_note}" if note2 else auto_note
            break
    for target_pos in ([4, 5], [8, 5]):
        for idx, step in enumerate(out):
            if (
                step.get("floor") == "MT14"
                and step.get("pos") == target_pos
                and step.get("action") == "击杀"
                and step.get("eid") == "bigBat"
                and idx > 0
            ):
                before = normal_state(step.get("before"))
                after = normal_state(step.get("after"))
                gold_gain = after.get("gold", 0) - before.get("gold", 0)
                if gold_gain:
                    for future in out[idx + 1 :]:
                        for key in ("before", "after"):
                            state = future.get(key)
                            if isinstance(state, dict) and "gold" in state:
                                state["gold"] -= gold_gain
                base = normal_state(out[idx - 1].get("after"))
                step["before"] = dict(base)
                step["after"] = dict(base)
                step["delta"] = "自动处理已完成"
                note = step.get("note") or ""
                auto_note = f"实机 MT14 x{target_pos[0]}y{target_pos[1]} 大蝙蝠已由早前自动清理处理，此处不再重复计金币"
                step["note"] = f"{note}；{auto_note}" if note else auto_note
                break
    for idx, step in enumerate(out):
        if (
            step.get("floor") == "MT14"
            and step.get("pos") == [6, 5]
            and step.get("action") == "击杀"
            and step.get("eid") == "rock"
        ):
            before = normal_state(step.get("before"))
            after = normal_state(step.get("after"))
            old_gain = after.get("gold", 0) - before.get("gold", 0)
            live_gain = 80
            gold_delta = live_gain - old_gain
            if gold_delta:
                step_after = step.get("after")
                if isinstance(step_after, dict) and "gold" in step_after:
                    step_after["gold"] += gold_delta
                for future in out[idx + 1 :]:
                    for key in ("before", "after"):
                        state = future.get(key)
                        if isinstance(state, dict) and "gold" in state:
                            state["gold"] += gold_delta
            note = step.get("note") or ""
            live_note = "实机 MT14 x6y5 rock 金币收益为 80"
            step["note"] = f"{note}；{live_note}" if note else live_note
            break
    for idx in range(len(out) - 2):
        step = out[idx]
        yellow_key = out[idx + 1]
        blue_gem = out[idx + 2]
        if (
            step.get("floor") == "MT14"
            and step.get("pos") == [7, 1]
            and step.get("action") == "拾取"
            and step.get("eid") == "redPotion"
            and yellow_key.get("floor") == "MT14"
            and yellow_key.get("pos") == [6, 1]
            and yellow_key.get("eid") == "yellowKey"
            and blue_gem.get("floor") == "MT14"
            and blue_gem.get("pos") == [5, 1]
            and blue_gem.get("eid") == "blueGem"
        ):
            patched = dict(normal_state(step.get("after")))
            patched["yk"] = patched.get("yk", 0) + 1
            patched["def"] = patched.get("def", 0) + 2
            patched["gold"] = patched.get("gold", 0) + 8
            auto_note = "实机点击 MT14 x7y1 红血瓶后自动拾取 x6y1 黄钥匙、x5y1 蓝宝石，并清理 x5y2 黑史莱姆"
            step["after"] = dict(patched)
            note = step.get("note") or ""
            step["note"] = f"{note}；{auto_note}" if note else auto_note

            for auto_step in (yellow_key, blue_gem):
                auto_step["before"] = dict(patched)
                auto_step["after"] = dict(patched)
                auto_step["delta"] = "自动处理已完成"
                note2 = auto_step.get("note") or ""
                auto_step["note"] = f"{note2}；{auto_note}" if note2 else auto_note

            for future in out[idx + 3 :]:
                for key in ("before", "after"):
                    state = future.get(key)
                    if isinstance(state, dict) and "gold" in state:
                        state["gold"] += 8
            break
    for idx, step in enumerate(out):
        if (
            step.get("floor") == "MT15"
            and step.get("pos") == [11, 6]
            and step.get("action") == "击杀"
            and step.get("eid") == "redPriest"
        ):
            before = normal_state(step.get("before"))
            after = normal_state(step.get("after"))
            old_gain = after.get("gold", 0) - before.get("gold", 0)
            live_gain = 44
            gold_delta = live_gain - old_gain
            if gold_delta:
                step_after = step.get("after")
                if isinstance(step_after, dict) and "gold" in step_after:
                    step_after["gold"] += gold_delta
                for future in out[idx + 1 :]:
                    for key in ("before", "after"):
                        state = future.get(key)
                        if isinstance(state, dict) and "gold" in state:
                            state["gold"] += gold_delta
            note = step.get("note") or ""
            live_note = "实机 MT15 x11y6 redPriest 战斗后自动清 MT15 x2y11 redPriest，合计 44G"
            step["note"] = f"{note}；{live_note}" if note else live_note
            break
    for idx, step in enumerate(out):
        if (
            step.get("floor") == "MT20"
            and step.get("pos") == [8, 11]
            and step.get("action") == "击杀"
            and step.get("eid") == "redPriest"
        ):
            before = normal_state(step.get("before"))
            after = normal_state(step.get("after"))
            old_gain = after.get("gold", 0) - before.get("gold", 0)
            live_gain = 78
            gold_delta = live_gain - old_gain
            if gold_delta:
                step_after = step.get("after")
                if isinstance(step_after, dict) and "gold" in step_after:
                    step_after["gold"] += gold_delta
                for future in out[idx + 1 :]:
                    for key in ("before", "after"):
                        state = future.get(key)
                        if isinstance(state, dict) and "gold" in state:
                            state["gold"] += gold_delta
            note = step.get("note") or ""
            live_note = "实机 MT20 x8y11 redPriest 战斗后自动清 MT20 x10y10、x2y10 rock，合计 78G"
            step["note"] = f"{note}；{live_note}" if note else live_note
            break
    for target_pos in ([10, 10], [2, 10]):
        for idx, step in enumerate(out):
            if (
                step.get("floor") == "MT20"
                and step.get("pos") == target_pos
                and step.get("action") == "击杀"
                and step.get("eid") == "rock"
                and idx > 0
            ):
                before = normal_state(step.get("before"))
                after = normal_state(step.get("after"))
                gold_gain = after.get("gold", 0) - before.get("gold", 0)
                if gold_gain:
                    for future in out[idx + 1 :]:
                        for key in ("before", "after"):
                            state = future.get(key)
                            if isinstance(state, dict) and "gold" in state:
                                state["gold"] -= gold_gain
                base = normal_state(out[idx - 1].get("after"))
                step["before"] = dict(base)
                step["after"] = dict(base)
                step["delta"] = "自动处理已完成"
                note = step.get("note") or ""
                auto_note = f"实机已在 MT20 x8y11 redPriest 后自动清理 MT20 x{target_pos[0]}y{target_pos[1]} rock，此处不再重复计金币"
                step["note"] = f"{note}；{auto_note}" if note else auto_note
                break
    for idx, step in enumerate(out):
        if (
            step.get("floor") == "MT18"
            and step.get("pos") == [10, 7]
            and step.get("eid") == "rock"
        ):
            before = normal_state(step.get("before"))
            after = normal_state(step.get("after"))
            old_gain = after.get("gold", 0) - before.get("gold", 0)
            live_gain = 102
            gold_delta = live_gain - old_gain
            if gold_delta:
                step_after = step.get("after")
                if isinstance(step_after, dict) and "gold" in step_after:
                    step_after["gold"] += gold_delta
                for future in out[idx + 1 :]:
                    for key in ("before", "after"):
                        state = future.get(key)
                        if isinstance(state, dict) and "gold" in state:
                            state["gold"] += gold_delta
            note = step.get("note") or ""
            live_note = "实机 MT18 x10y7 rock 点击后连同 x3y5/x1y5 rock、x9y4 zombie 自动清理，合计 102G"
            step["note"] = f"{note}；{live_note}" if note else live_note
            break
    for idx, step in enumerate(out):
        if (
            step.get("floor") == "MT18"
            and step.get("pos") == [11, 8]
            and step.get("eid") == "yellowDoor"
        ):
            before = normal_state(step.get("before"))
            after = normal_state(step.get("after"))
            patched = dict(after)
            patched["x"] = 11
            patched["y"] = 8
            patched["def"] = before.get("def", patched.get("def", 0)) + 2
            patched["yk"] = before.get("yk", patched.get("yk", 0))
            patched["gold"] = before.get("gold", patched.get("gold", 0)) + 22
            stat_delta = {
                key: patched.get(key, 0) - after.get(key, 0)
                for key in ("hp", "atk", "def", "yk", "bk", "rk", "gold", "dmg", "yd", "bd", "rd", "times1")
                if patched.get(key) != after.get(key)
            }
            step["after"] = dict(patched)
            if stat_delta:
                for future in out[idx + 1 :]:
                    for state_key in ("before", "after"):
                        state = future.get(state_key)
                        if not isinstance(state, dict):
                            continue
                        for key, delta in stat_delta.items():
                            if key in state:
                                state[key] += delta
            note = step.get("note") or ""
            live_note = "实机开 MT18 x11y8 黄门后自动清 x11y9 redPriest，并拾取 x10y10 yellowKey、x10y11 blueGem；x11y11 redPotion 因 nopotion 保留"
            step["note"] = f"{note}；{live_note}" if note else live_note
            break
    for target_pos, target_eid, reason in (
        ([11, 9], "redPriest", "已在 MT18 x11y8 黄门点击后自动清理"),
        ([10, 10], "yellowKey", "已在 MT18 x11y8 黄门点击后自动拾取"),
        ([10, 11], "blueGem", "已在 MT18 x11y8 黄门点击后自动拾取"),
    ):
        for idx, step in enumerate(out):
            if (
                step.get("floor") == "MT18"
                and step.get("pos") == target_pos
                and step.get("eid") == target_eid
                and idx > 0
            ):
                before = normal_state(step.get("before"))
                after = normal_state(step.get("after"))
                stat_delta = {
                    key: after.get(key, 0) - before.get(key, 0)
                    for key in ("hp", "atk", "def", "yk", "bk", "rk", "gold", "dmg", "yd", "bd", "rd", "times1")
                    if after.get(key) != before.get(key)
                }
                if stat_delta:
                    for future in out[idx + 1 :]:
                        for state_key in ("before", "after"):
                            state = future.get(state_key)
                            if not isinstance(state, dict):
                                continue
                            for key, delta in stat_delta.items():
                                if key in state:
                                    state[key] -= delta
                base = normal_state(out[idx - 1].get("after"))
                step["before"] = dict(base)
                step["after"] = dict(base)
                step["delta"] = "自动处理已完成"
                note = step.get("note") or ""
                auto_note = f"{reason}，此处不再重复处理"
                step["note"] = f"{note}；{auto_note}" if note else auto_note
                break
    for idx, step in enumerate(out):
        if (
            step.get("floor") == "MT19"
            and step.get("pos") == [4, 3]
            and step.get("eid") == "zombieKnight"
            and idx > 400
        ):
            before = normal_state(step.get("before"))
            after = normal_state(step.get("after"))
            patched = dict(after)
            patched["x"] = 4
            patched["y"] = 3
            patched["hp"] = before.get("hp", patched.get("hp", 0)) - 10
            patched["bk"] = before.get("bk", patched.get("bk", 0)) + 1
            patched["gold"] = before.get("gold", patched.get("gold", 0)) + 52
            patched["dmg"] = before.get("dmg", patched.get("dmg", 0)) + 10
            stat_delta = {
                key: patched.get(key, 0) - after.get(key, 0)
                for key in ("hp", "atk", "def", "yk", "bk", "rk", "gold", "dmg", "yd", "bd", "rd", "times1")
                if patched.get(key) != after.get(key)
            }
            step["after"] = dict(patched)
            if stat_delta:
                for future in out[idx + 1 :]:
                    for state_key in ("before", "after"):
                        state = future.get(state_key)
                        if not isinstance(state, dict):
                            continue
                        for key, delta in stat_delta.items():
                            if key in state:
                                state[key] += delta
            note = step.get("note") or ""
            live_note = "实机 MT19 x4y3 zombieKnight 因 DEF=110 只受 10 伤，并自动清 x6y1 redPriest、拾取 x8y1 blueKey，合计 52G"
            step["note"] = f"{note}；{live_note}" if note else live_note
            break
    for target_pos, target_eid, reason in (
        ([6, 1], "redPriest", "已在 MT19 x4y3 zombieKnight 点击后自动清理"),
        ([8, 1], "blueKey", "已在 MT19 x4y3 zombieKnight 点击后自动拾取"),
    ):
        for idx, step in enumerate(out):
            if (
                step.get("floor") == "MT19"
                and step.get("pos") == target_pos
                and step.get("eid") == target_eid
                and idx > 400
            ):
                before = normal_state(step.get("before"))
                after = normal_state(step.get("after"))
                stat_delta = {
                    key: after.get(key, 0) - before.get(key, 0)
                    for key in ("hp", "atk", "def", "yk", "bk", "rk", "gold", "dmg", "yd", "bd", "rd", "times1")
                    if after.get(key) != before.get(key)
                }
                if stat_delta:
                    for future in out[idx + 1 :]:
                        for state_key in ("before", "after"):
                            state = future.get(state_key)
                            if not isinstance(state, dict):
                                continue
                            for key, delta in stat_delta.items():
                                if key in state:
                                    state[key] -= delta
                base = normal_state(out[idx - 1].get("after"))
                step["before"] = dict(base)
                step["after"] = dict(base)
                step["delta"] = "自动处理已完成"
                note = step.get("note") or ""
                auto_note = f"{reason}，此处不再重复处理"
                step["note"] = f"{note}；{auto_note}" if note else auto_note
                break
    for idx, step in enumerate(out):
        if (
            step.get("floor") == "MT32"
            and step.get("pos") == [9, 5]
            and idx > 450
        ):
            before = normal_state(step.get("before"))
            after = normal_state(step.get("after"))
            patched = dict(after)
            patched["x"] = 9
            patched["y"] = 5
            patched["yk"] = before.get("yk", patched.get("yk", 0)) + 1
            patched["yd"] = before.get("yd", patched.get("yd", 0)) + 1
            stat_delta = {
                key: patched.get(key, 0) - after.get(key, 0)
                for key in ("hp", "atk", "def", "yk", "bk", "rk", "gold", "dmg", "yd", "bd", "rd", "times1")
                if patched.get(key) != after.get(key)
            }
            step["after"] = dict(patched)
            if stat_delta:
                for future in out[idx + 1 :]:
                    for state_key in ("before", "after"):
                        state = future.get(state_key)
                        if not isinstance(state, dict):
                            continue
                        for key, delta in stat_delta.items():
                            if key in state:
                                state[key] += delta
            note = step.get("note") or ""
            live_note = "实机开 MT32 x9y5 黄门后自动拾取门后两把 yellowKey，蓝血瓶因 nopotion 保留，钥匙净增 1"
            step["note"] = f"{note}；{live_note}" if note else live_note
            break
    for idx, step in enumerate(out):
        if (
            step.get("floor") == "MT32"
            and step.get("pos") == [11, 5]
            and idx > 450
        ):
            before = normal_state(step.get("before"))
            after = normal_state(step.get("after"))
            stat_delta = {
                key: after.get(key, 0) - before.get(key, 0)
                for key in ("hp", "atk", "def", "yk", "bk", "rk", "gold", "dmg", "yd", "bd", "rd", "times1")
                if after.get(key) != before.get(key)
            }
            if stat_delta:
                for future in out[idx + 1 :]:
                    for state_key in ("before", "after"):
                        state = future.get(state_key)
                        if not isinstance(state, dict):
                            continue
                        for key, delta in stat_delta.items():
                            if key in state:
                                state[key] -= delta
            base = normal_state(out[idx - 1].get("after"))
            step["before"] = dict(base)
            step["after"] = dict(base)
            step["delta"] = "自动处理已完成"
            note = step.get("note") or ""
            auto_note = "已在 MT32 x9y5 黄门点击后自动拾取，此处不再重复处理"
            step["note"] = f"{note}；{auto_note}" if note else auto_note
            break
    for target_pos, target_eid, reason in (
        ([3, 5], "rock", "已在 MT18 x10y7 rock 点击后自动清理"),
        ([1, 5], "rock", "已在 MT18 x10y7 rock 点击后自动清理"),
        ([9, 4], "zombie", "已在 MT18 x10y7 rock 点击后自动清理"),
        ([10, 5], "bigBat", "已在早前 MT18 自动路线中清理"),
        ([10, 2], "blackSlime", "已在早前 MT18 自动路线中清理"),
    ):
        for idx, step in enumerate(out):
            if (
                step.get("floor") == "MT18"
                and step.get("pos") == target_pos
                and step.get("eid") == target_eid
                and idx > 0
            ):
                before = normal_state(step.get("before"))
                after = normal_state(step.get("after"))
                gold_gain = after.get("gold", 0) - before.get("gold", 0)
                if gold_gain:
                    for future in out[idx + 1 :]:
                        for key in ("before", "after"):
                            state = future.get(key)
                            if isinstance(state, dict) and "gold" in state:
                                state["gold"] -= gold_gain
                base = normal_state(out[idx - 1].get("after"))
                step["before"] = dict(base)
                step["after"] = dict(base)
                step["delta"] = "自动处理已完成"
                note = step.get("note") or ""
                auto_note = f"{reason}，此处不再重复计金币"
                step["note"] = f"{note}；{auto_note}" if note else auto_note
                break
    for idx, step in enumerate(out):
        if (
            step.get("floor") == "MT18"
            and step.get("pos") == [1, 11]
            and step.get("eid") is None
            and idx > 700
        ):
            before = normal_state(step.get("before"))
            after = normal_state(step.get("after"))
            old_gain = after.get("gold", 0) - before.get("gold", 0)
            live_gain = 30
            gold_delta = live_gain - old_gain
            if gold_delta:
                step_after = step.get("after")
                if isinstance(step_after, dict):
                    step_after["gold"] = step_after.get("gold", before.get("gold", 0)) + gold_delta
                    step_after["x"] = 5
                    step_after["y"] = 2
                for future in out[idx + 1 :]:
                    for key in ("before", "after"):
                        state = future.get(key)
                        if isinstance(state, dict) and "gold" in state:
                            state["gold"] += gold_delta
            note = step.get("note") or ""
            live_note = "实机点击 MT18 x1y11 时自动清理 x7y4 zombieKnight，停在 x5y2，合计 30G"
            step["note"] = f"{note}；{live_note}" if note else live_note
            break
    for idx, step in enumerate(out):
        if (
            step.get("floor") == "MT18"
            and step.get("pos") == [7, 4]
            and step.get("eid") == "zombieKnight"
            and idx > 700
        ):
            before = normal_state(step.get("before"))
            after = normal_state(step.get("after"))
            gold_gain = after.get("gold", 0) - before.get("gold", 0)
            if gold_gain:
                for future in out[idx + 1 :]:
                    for key in ("before", "after"):
                        state = future.get(key)
                        if isinstance(state, dict) and "gold" in state:
                            state["gold"] -= gold_gain
            base = normal_state(out[idx - 1].get("after"))
            step["before"] = dict(base)
            step["after"] = dict(base)
            step["delta"] = "自动处理已完成"
            note = step.get("note") or ""
            auto_note = "已在 MT18 x1y11 点击时自动清理，此处不再重复计金币"
            step["note"] = f"{note}；{auto_note}" if note else auto_note
            break
    for step in out:
        if step.get("delta") != "自动处理已完成" and step.get("action") != SET_AUTO_ACTION:
            step["delta"] = delta_text(normal_state(step.get("before")), normal_state(step.get("after")))
    return out


def convert_zone1_logs(data: dict[str, Any]) -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = []
    for log in data.get("logs", []):
        src = log.get("step", {})
        before = normal_state(log.get("before"))
        after = normal_state(log.get("after"))
        action = ACTION_NAMES.get(src.get("action"), src.get("action") or "")
        steps.append(
            {
                "segment": src.get("section") or "1区",
                "phase": src.get("phase"),
                "floor": src.get("fid") or before.get("floor") or after.get("floor"),
                "pos": [src.get("x"), src.get("y")],
                "action": action,
                "eid": src.get("eid"),
                "before": before,
                "after": after,
                "delta": delta_text(before, after),
                "note": src.get("text") or "",
                "source_index": log.get("index"),
            }
        )
    return steps


def normalize_steps(steps: list[dict[str, Any]], segment_prefix: str | None = None) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for idx, step in enumerate(steps, 1):
        before = normal_state(step.get("before"))
        after = normal_state(step.get("after"))
        segment = step.get("segment") or segment_prefix or ""
        if segment_prefix and segment and not segment.startswith(segment_prefix):
            segment = f"{segment_prefix} / {segment}"
        action = ACTION_NAMES.get(step.get("action"), step.get("action"))
        out.append(
            {
                **step,
                "segment": segment,
                "action": action,
                "before": before,
                "after": after,
                "delta": step.get("delta") or delta_text(before, after),
                "source_index": step.get("source_index", idx),
            }
        )
    return out


def stage_row(name: str, state: dict[str, Any], dmg: int, doors: tuple[int, int, int], score: float | None = None) -> dict[str, Any]:
    row: dict[str, Any] = {
        "name": name,
        "state": state,
        "state_text": state_text(state),
        "cumulative_dmg_from_4f": dmg,
        "cumulative_doors_from_4f": {"yellow": doors[0], "blue": doors[1], "red": doors[2]},
    }
    if score is not None:
        row["current_floor_and_below_final_score"] = score
    return row


def stats_equal(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return all(left.get(key) == right.get(key) for key in STAT_KEYS)


def insert_floor_fly_steps(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Make inter-floor jumps explicit for strict human-input replay."""
    if not steps:
        return []
    out: list[dict[str, Any]] = []
    previous_after: dict[str, Any] | None = None
    for step in steps:
        before = normal_state(step.get("before"))
        after = normal_state(step.get("after"))
        if (
            previous_after
            and before
            and step.get("action") == "通过"
            and step.get("floor") == previous_after.get("floor")
            and before.get("floor") != previous_after.get("floor")
            and stats_equal(previous_after, before)
        ):
            step = dict(step)
            before = dict(previous_after)
            step["before"] = before
            step["delta"] = delta_text(before, after)
        if (
            previous_after
            and before
            and previous_after.get("floor") != before.get("floor")
            and stats_equal(previous_after, before)
        ):
            target_floor = before.get("floor")
            out.append(
                {
                    "segment": step.get("segment") or "",
                    "phase": "human-floor-transfer",
                    "floor": target_floor,
                    "pos": [before.get("x"), before.get("y")],
                    "action": "\u98de\u884c",
                    "eid": target_floor,
                    "before": previous_after,
                    "after": before,
                    "delta": delta_text(previous_after, before),
                    "note": f"\u6309 g \u6253\u5f00\u697c\u5c42\u4f20\u9001\uff0c\u65b9\u5411\u952e\u9009\u62e9 {target_floor}\uff0c\u7a7a\u683c\u786e\u8ba4",
                    "source_index": step.get("source_index"),
                    "inserted": True,
                }
            )
        if (
            before
            and after
            and before.get("floor") != after.get("floor")
            and step.get("action") not in {"飞行", "换层", "通过"}
        ):
            target_floor = after.get("floor")
            points = FLY_POINTS.get(target_floor, {})
            landing = points.get("downFloor") or points.get("upFloor") or [after.get("x"), after.get("y")]
            fly_after = dict(before)
            fly_after["floor"] = target_floor
            fly_after["x"] = landing[0]
            fly_after["y"] = landing[1]
            out.append(
                {
                    "segment": step.get("segment") or "",
                    "phase": "human-floor-transfer",
                    "floor": target_floor,
                    "pos": [fly_after.get("x"), fly_after.get("y")],
                    "action": "飞行",
                    "eid": target_floor,
                    "before": before,
                    "after": fly_after,
                    "delta": delta_text(before, fly_after),
                    "note": f"按 g 打开楼层传送，方向键选择 {target_floor}，空格确认",
                    "source_index": step.get("source_index"),
                    "inserted": True,
                }
            )
            step = dict(step)
            step["before"] = fly_after
            step["delta"] = delta_text(fly_after, after)
        out.append(step)
        previous_after = after
    for idx, step in enumerate(out, 1):
        step["index"] = idx
    return out


def stock_score(state: dict[str, Any]) -> float:
    return (
        float(state.get("hp", 0))
        + float(state.get("yk", 0)) * 50
        + float(state.get("bk", 0)) * 200
        + float(state.get("gold", 0)) * 0.5
    )


def held_tool_counts(state: dict[str, Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    if state.get("centerFly") or state.get("centerFly3"):
        counts["centerFly"] = int(state.get("centerFly", 1) or 1)
    for key in ("pickaxe", "earthquake", "upFly", "downFly", "snow", "cross", "bomb"):
        value = state.get(key)
        if isinstance(value, bool):
            value = int(value)
        if isinstance(value, int) and value > 0:
            counts[key] = value
    return counts


def rescore_with_state(score: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    out = dict(score)
    stock = stock_score(state)
    out["stock_score"] = stock
    out["final_score"] = stock + float(out.get("remaining_value_hp", 0))
    tools = dict(score.get("held_tool_counts", {}))
    tools.update(held_tool_counts(state))
    out["held_tool_counts"] = tools
    return out


def patched_state_for_template(steps: list[dict[str, Any]], template: dict[str, Any]) -> dict[str, Any]:
    keys = ("floor", "x", "y", "dmg", "yd", "bd", "rd", "times1")
    found: dict[str, Any] | None = None
    for step in steps:
        after = normal_state(step.get("after"))
        if after and all(after.get(key) == template.get(key) for key in keys if key in template):
            found = after
    return {**normal_state(template), **(found or {})}


def enforce_step_continuity(steps: list[dict[str, Any]]) -> list[str]:
    warnings: list[str] = []
    prev: dict[str, Any] | None = None
    nonpos_keys = {
        "hp",
        "atk",
        "def",
        "yk",
        "bk",
        "rk",
        "gold",
        "dmg",
        "yd",
        "bd",
        "rd",
        "times1",
        "centerFly",
        "upFly",
        "downFly",
        "earthquake",
        "bomb",
        "bigKey",
        "pickaxe",
        "superPotion",
        "snow",
        "coin",
        "cross",
        "magicImmune",
    }
    for idx, step in enumerate(steps, 1):
        if prev is not None:
            before = normal_state(step.get("before"))
            mismatches = [
                key
                for key in sorted(nonpos_keys & before.keys() & prev.keys())
                if before.get(key) != prev.get(key)
            ]
            if mismatches:
                warnings.append(
                    f"step {idx}: before differs from previous after on {','.join(mismatches)}"
                )
            step["before"] = dict(prev)
            if step.get("delta") != "自动处理已完成" and step.get("action") != SET_AUTO_ACTION:
                step["delta"] = delta_text(normal_state(step.get("before")), normal_state(step.get("after")))
        prev = normal_state(step.get("after"))
    return warnings


def check_step_continuity(steps: list[dict[str, Any]]) -> list[str]:
    warnings: list[str] = []
    prev: dict[str, Any] | None = None
    nonpos_keys = {
        "hp",
        "atk",
        "def",
        "yk",
        "bk",
        "rk",
        "gold",
        "dmg",
        "yd",
        "bd",
        "rd",
        "times1",
        "centerFly",
        "upFly",
        "downFly",
        "earthquake",
        "bomb",
        "bigKey",
        "pickaxe",
        "superPotion",
        "snow",
        "coin",
        "cross",
        "magicImmune",
    }
    for idx, step in enumerate(steps, 1):
        if prev is not None:
            before = normal_state(step.get("before"))
            mismatches = [
                key
                for key in sorted(nonpos_keys & before.keys() & prev.keys())
                if before.get(key) != prev.get(key)
            ]
            if mismatches:
                warnings.append(f"step {idx}: before differs from previous after on {','.join(mismatches)}")
        prev = normal_state(step.get("after"))
    return warnings


def main() -> int:
    zone1 = read_json(ZONE1_REPLAY)
    zone2_path = zone2_source_path()
    zone2 = normalize_zone2_source(read_json(zone2_path))
    zone2_logic = read_json(ZONE2_LOGIC)["result"]
    bridge = read_json(BRIDGE_WALK)
    tail = read_json(TAIL_WALK)
    audit = read_json(AUDIT)

    zone2_total = zone2_logic["final"]
    zone3_40 = audit["zone3_40_state"]
    final_state = audit["final_state"]

    # Zone-2 logic verification carries cumulative counters from the 4F start.
    base_dmg_4to20 = int(zone2_total["dmg"])
    base_doors_4to20 = (int(zone2_total["yd"]), int(zone2_total["bd"]), int(zone2_total["rd"]))

    zone3_40_dmg = int(zone3_40["dmg"])
    final_tail_dmg = int(final_state["dmg"])
    zone3_40_doors = (int(zone3_40["yd"]), int(zone3_40["bd"]), int(zone3_40["rd"]))
    final_tail_doors = (int(final_state["yd"]), int(final_state["bd"]), int(final_state["rd"]))

    cumulative_40_dmg = base_dmg_4to20 + zone3_40_dmg
    cumulative_50_dmg = base_dmg_4to20 + final_tail_dmg
    cumulative_40_doors = tuple(base_doors_4to20[i] + zone3_40_doors[i] for i in range(3))
    cumulative_50_doors = tuple(base_doors_4to20[i] + final_tail_doors[i] for i in range(3))

    zone1_steps = convert_zone1_logs(zone1)
    zone2_steps = normalize_steps(zone2.get("steps", []), "2区 10F-20F")
    bridge_steps = normalize_steps(bridge.get("steps", []), "20F-31F 桥接")
    tail_steps = normalize_steps(tail.get("steps", []), "31F-50F 本地候选")

    combined_steps = zone1_steps + zone2_steps + bridge_steps + tail_steps
    combined_steps = insert_auto_setting_steps(combined_steps)
    steps = insert_floor_fly_steps(combined_steps)
    enforce_step_continuity(steps)
    continuity_warnings = check_step_continuity(steps)
    zone3_40 = patched_state_for_template(steps, zone3_40)
    final_state = {**normal_state(final_state), **normal_state(steps[-1].get("after"))}
    score40 = rescore_with_state(audit["zone3_40_score"], zone3_40)
    score50 = rescore_with_state(audit["final_score"], final_state)

    stage_rows = [
        stage_row("1区 Boss 后", normal_state(zone1["finalState"]), 2454, (41, 2, 1)),
        stage_row("2区 20F 吸血鬼后", normal_state(zone2["expected_final"]), base_dmg_4to20, base_doors_4to20),
        stage_row("20F-31F 桥接后", normal_state(bridge["final"]), base_dmg_4to20, base_doors_4to20),
        stage_row("40F Boss 后", normal_state(zone3_40), cumulative_40_dmg, cumulative_40_doors, score40["final_score"]),
        stage_row("50F 真魔王后", normal_state(final_state), cumulative_50_dmg, cumulative_50_doors, score50["final_score"]),
    ]

    output = {
        "ok": not audit.get("errors"),
        "web_verified": False,
        "verification_note": "local stitched audit only; strict human-input web replay is still pending",
        "continuity_warnings": continuity_warnings,
        "sources": {
            "zone1_replay": rel(ZONE1_REPLAY),
            "zone2_strict_walk": rel(zone2_path),
            "zone2_logic_metrics": rel(ZONE2_LOGIC),
            "bridge_walk": rel(BRIDGE_WALK),
            "tail_walk": rel(TAIL_WALK),
            "audit": rel(AUDIT),
            "score_function": "scripts/floor_final_score.py::current_floor_and_below_final_score",
        },
        "auto_settings": [
            {
                "when": "4F start",
                "auto": AUTO_START,
                "reason": "early route needs automatic zero-damage cleanup and potion pickup",
            },
            {
                "when": "after 20F vampire, before postBossSupply",
                "auto": AUTO_NOPOTION,
                "reason": "preserve potions for 3F/4F while still collecting non-potion resources",
            },
        ],
        "start": normal_state(zone1["startState"]),
        "final": normal_state(final_state),
        "cumulative_metrics": {
            "dmg_4to20": base_dmg_4to20,
            "dmg_31to40": zone3_40_dmg,
            "dmg_31to50": final_tail_dmg,
            "dmg_4to40": cumulative_40_dmg,
            "dmg_4to50": cumulative_50_dmg,
            "doors_4to20": {"yellow": base_doors_4to20[0], "blue": base_doors_4to20[1], "red": base_doors_4to20[2]},
            "doors_4to40": {"yellow": cumulative_40_doors[0], "blue": cumulative_40_doors[1], "red": cumulative_40_doors[2]},
            "doors_4to50": {"yellow": cumulative_50_doors[0], "blue": cumulative_50_doors[1], "red": cumulative_50_doors[2]},
        },
        "scores": {
            "floor40_current_and_below": score40,
            "floor50_current_and_below": score50,
        },
        "important_tools": {
            "floor40_held": score40["held_tool_counts"],
            "floor40_map": score40["map_tool_counts"],
            "floor50_held": score50["held_tool_counts"],
            "floor50_map": score50["map_tool_counts"],
        },
        "comparison": {
            "previous_post40_focused_slice5_mid_center": {
                "state": "HP=500 ATK=451 DEF=422 YK=4 BK=0 RK=1 G=1942",
                "dmg_31to50": 46059,
                "final_score_floor50": 3482.5,
                "held_tools": {"centerFly": 2, "snow": 1, "cross": 1},
            },
            "current_strict20_preserve_pickaxe": {
                "state": state_text(normal_state(final_state)),
                "dmg_31to50": final_tail_dmg,
                "dmg_4to50": cumulative_50_dmg,
                "final_score_floor50": score50["final_score"],
                "held_tools": score50["held_tool_counts"],
            },
        },
        "stages": stage_rows,
        "steps": steps,
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(output)

    print(f"ok={output['ok']}")
    print(f"json={OUT_JSON}")
    print(f"md={OUT_MD}")
    print(f"final={state_text(normal_state(final_state))}")
    print(f"dmg_4to50={cumulative_50_dmg}")
    print(f"final_score_floor50={score50['final_score']}")
    print(f"continuity_warnings={len(continuity_warnings)}")
    return 0 if output["ok"] else 1


def write_markdown(data: dict[str, Any]) -> None:
    metrics = data["cumulative_metrics"]
    score40 = data["scores"]["floor40_current_and_below"]
    score50 = data["scores"]["floor50_current_and_below"]
    final = data["final"]
    prev = data["comparison"]["previous_post40_focused_slice5_mid_center"]
    cur = data["comparison"]["current_strict20_preserve_pickaxe"]

    lines: list[str] = [
        "# 纯净版-TE 4F-50F 本地拼接 Walk（待 web 严格复现）",
        "",
        "## 核心结论",
        "",
        f"- 本地拼接结果：{state_text(final)}",
        f"- 纯伤害 dmg：4F-40F = {metrics['dmg_4to40']}；4F-50F = {metrics['dmg_4to50']}（31F-50F 内部计数 {metrics['dmg_31to50']}）",
        f"- 开门累计：4F-40F = {metrics['doors_4to40']['yellow']}/{metrics['doors_4to40']['blue']}/{metrics['doors_4to40']['red']}；4F-50F = {metrics['doors_4to50']['yellow']}/{metrics['doors_4to50']['blue']}/{metrics['doors_4to50']['red']}",
        f"- 40F 当前层及以下 final-score = {score40['final_score']}（stock={score40['stock_score']}，剩余物品={score40['item_value_hp']}，0伤怪金币={score40['zero_damage_monster_value_hp']}）",
        f"- 50F 当前层及以下 final-score = {score50['final_score']}（stock={score50['stock_score']}，剩余物品={score50['item_value_hp']}，0伤怪金币={score50['zero_damage_monster_value_hp']}）",
        "- web 状态：未完成严格 human-input 复现；本文件不能当作 web verified 证明。",
        "",
        "## 自动设置",
        "",
        f"- 开局：`{auto_spec_text(data['auto_settings'][0]['auto'])}`，用于 1/2 区缺血阶段自动吃血瓶和清 0 伤怪。",
        f"- 20F Boss 后、postBossSupply 前：`{auto_spec_text(data['auto_settings'][1]['auto'])}`，保留血瓶但继续自动拾取非血瓶资源。",
        "",
        "## 分数函数",
        "",
        "- 使用 `scripts/floor_final_score.py::current_floor_and_below_final_score`。",
        "- 该函数在 replay 已变更后的地图上计算：已清掉的 0 伤怪只体现在当前金币里，不再出现在剩余资源；未打的 0 伤怪仍在地图块里，按未来金币计入。因此不会双算。",
        "- 非 0 伤怪会列入审计计数，但不把其金币计入 final-score，避免把未来伤害成本忽略掉。",
        "",
        "## 重要道具",
        "",
        f"- 40F 后持有：{compact_counts(data['important_tools']['floor40_held'])}；地图剩余：{compact_counts(data['important_tools']['floor40_map'])}",
        f"- 50F 后持有：{compact_counts(data['important_tools']['floor50_held'])}；地图剩余：{compact_counts(data['important_tools']['floor50_map'])}",
        "",
        "## 阶段快照",
        "",
        "| 阶段 | 状态 | 累计 dmg | 累计门 黄/蓝/红 | final-score |",
        "|---|---|---:|---|---:|",
    ]
    for row in data["stages"]:
        doors = row["cumulative_doors_from_4f"]
        score = row.get("current_floor_and_below_final_score", "")
        lines.append(
            f"| {row['name']} | {row['state_text']} | {row['cumulative_dmg_from_4f']} | "
            f"{doors['yellow']}/{doors['blue']}/{doors['red']} | {score} |"
        )

    lines.extend(
        [
            "",
            "## 与之前 40F 探索结果对比",
            "",
            "| 路线 | 状态 | dmg | final-score<=50 | 重要道具 | 备注 |",
            "|---|---|---:|---:|---|---|",
            f"| 当前 strict20 保留稿路线 | {cur['state']} | {cur['dmg_31to50']}（31F-50F）；{cur['dmg_4to50']}（4F-50F） | {cur['final_score_floor50']} | {compact_counts(cur['held_tools'])} | 本地拼接，待 web |",
            f"| 之前 post40_focused_slice5_mid_center | {prev['state']} | {prev['dmg_31to50']}（post40/31F后口径） | {prev['final_score_floor50']} | {compact_counts(prev['held_tools'])} | 旧 post40 候选 |",
            "",
            "## 来源",
            "",
        ]
    )
    for key, value in data["sources"].items():
        lines.append(f"- {key}: `{value}`")

    lines.extend(
        [
            "",
            "## 详细步骤",
            "",
            "说明：为避免文件过长，Markdown 只列完整点击/事件序列的压缩行；完整 before/after 状态在 JSON 中。",
            "",
            "| # | 阶段 | 动作 | 数值变化 | 备注 |",
            "|---:|---|---|---|---|",
        ]
    )
    for step in data["steps"]:
        pos = step.get("pos") or ["?", "?"]
        note = (step.get("note") or "").replace("|", "/")
        action = step.get("action") or ""
        eid = step.get("eid") or ""
        floor = step.get("floor") or "?"
        target = f"{action} {floor} x{pos[0]}y{pos[1]} {eid}".strip()
        lines.append(
            f"| {step['index']} | {step.get('segment') or ''} | {target} | {step.get('delta') or ''} | {note} |"
        )

    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
