#!/usr/bin/env python3
"""Generate a 4F-9F single-merchant walk with gold accounting.

This is a deliberately small audit walk, not a replacement for the search.  It
follows the fixed 4F-6F prefix, buys the MT7 x6y1 merchant offer, then completes
the fixed 8F/9F shield+gem prefix.  Every segment summary includes remaining
gold so the money accounting can be checked by hand.
"""

from __future__ import annotations

import json
import os
import sys
from copy import deepcopy
from typing import Any


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.chdir(ROOT)

import fixed_shield_strategy as fixed
from src.solver.full_search import load_data, search_with_path


OUT_JSON = os.path.join("outputs", "results", "merchant_phase1_gold_walk.json")
OUT_MD = os.path.join("outputs", "walkthroughs", "walkthrough_merchant_phase1_gold.md")

MERCHANT_FID = "MT7"
MERCHANT_EID = "merchant_MT7_5YK"
MERCHANT_POS = (6, 1)
MERCHANT_COST = 50
MERCHANT_YK_GAIN = 5
MERCHANT_BK_GAIN = 0
INITIAL_GOLD = 7

ENEMY_GOLD = {
    "greenSlime": 1,
    "redSlime": 2,
    "bat": 3,
    "skeleton": 6,
    "skeletonSoldier": 8,
    "bluePriest": 5,
    "yellowGuard": 12,
    "skeletonCaptain": 30,
    "blueGuard": 50,
    "soldier": 45,
}


STATE_KEYS = ("hp", "atk", "def", "yk", "bk", "rk", "gold")

FIXED_SEGMENT_NAMES = {
    0: "4F start to 5F",
    1: "5F sword and return 4F",
    2: "4F redGem and yellow keys",
    3: "5F to 6F",
    4: "6F key route to 7F",
    6: "8F to 9F",
    7: "9F shield",
    8: "9F red/blue gem opener",
}


def patch_merchant(maps: dict[str, Any]) -> None:
    blocks = maps[MERCHANT_FID]["bl"]
    if not any((x, y, eid) == (*MERCHANT_POS, MERCHANT_EID) for x, y, _t, eid in blocks):
        blocks.append((MERCHANT_POS[0], MERCHANT_POS[1], 3, MERCHANT_EID))


def state_view(state: dict[str, Any]) -> dict[str, Any]:
    return {key: state[key] for key in STATE_KEYS}


def state_text(state: dict[str, Any]) -> str:
    return (
        f"HP={state['hp']} ATK={state['atk']} DEF={state['def']} "
        f"YK={state['yk']} BK={state['bk']} RK={state['rk']} G={state['gold']}"
    )


def merchant_offer_text() -> str:
    parts = []
    if MERCHANT_YK_GAIN:
        parts.append(f"{MERCHANT_YK_GAIN}YK")
    if MERCHANT_BK_GAIN:
        parts.append(f"{MERCHANT_BK_GAIN}BK")
    return "+".join(parts) if parts else "no resource"


def describe_action(t: int, eid: str) -> str:
    if eid.startswith("merchant_"):
        return "reach"
    if t == 1:
        return "kill"
    if t == 2:
        return "open"
    if t == 3:
        return "take"
    if eid == "upFloor":
        return "up"
    if eid == "downFloor":
        return "down"
    return "pass"


def fixed_segment(index: int) -> dict[str, Any]:
    segment = deepcopy(fixed.ROUTE[index])
    segment["name"] = FIXED_SEGMENT_NAMES.get(index, segment["name"])
    return segment


def step_delta(before: dict[str, Any], after: dict[str, Any]) -> str:
    labels = {"hp": "HP", "atk": "ATK", "def": "DEF", "yk": "YK", "bk": "BK", "rk": "RK", "gold": "G"}
    parts = []
    for key in STATE_KEYS:
        if before[key] != after[key]:
            parts.append(f"{labels[key]} {before[key]}->{after[key]}")
    return ", ".join(parts)


def block_at(blocks: dict[str, dict[tuple[int, int], tuple[int, str]]], fid: str, pos: tuple[int, int]) -> tuple[int, str]:
    return blocks[fid][pos]


def apply_gold_for_eid(state: dict[str, Any], eid: str) -> int:
    gained = ENEMY_GOLD.get(eid, 0)
    if gained:
        state["gold"] += gained
        state["_gold_gained"] += gained
    return gained


def record_step(
    steps: list[dict[str, Any]],
    segment: str,
    fid: str,
    pos: tuple[int, int],
    eid: str,
    action: str,
    before: dict[str, Any],
    after: dict[str, Any],
    note: str = "",
) -> None:
    steps.append({
        "segment": segment,
        "floor": fid,
        "x": pos[0],
        "y": pos[1],
        "eid": eid,
        "action": action,
        "before": before,
        "after": after,
        "note": note,
    })


def apply_fixed_segment(
    segment: dict[str, Any],
    state: dict[str, Any],
    maps: dict[str, Any],
    blocks: dict[str, dict[tuple[int, int], tuple[int, str]]],
    cleared: dict[str, set[tuple[int, int]]],
    collected: dict[str, set[tuple[int, int]]],
    steps: list[dict[str, Any]],
) -> dict[str, Any]:
    fid = segment["floor"]
    state["floor"] = fid
    state["x"], state["y"] = tuple(segment["start"])
    start_gold = state["gold"]
    start_dmg = state.get("_dmg", 0)
    start_doors = (state.get("_yd", 0), state.get("_bd", 0), state.get("_rd", 0))

    for x, y, expected_eid in segment["actions"]:
        pos = (x, y)
        t, eid = block_at(blocks, fid, pos)
        before = state_view(state)
        hp_before = state["hp"]
        _old, _new, error = fixed.apply_action(state, t, eid)
        if error:
            raise RuntimeError(f"{segment['name']} failed at {fid} x{x}y{y}: {error}")
        if t == 1:
            state["_dmg"] += max(0, hp_before - state["hp"])
            gained = apply_gold_for_eid(state, eid)
            note = f"+{gained}G" if gained else ""
        else:
            note = ""
        if t == 2:
            if eid == "yellowDoor":
                state["_yd"] += 1
            elif eid == "blueDoor":
                state["_bd"] += 1
            elif eid == "redDoor":
                state["_rd"] += 1
        cleared.setdefault(fid, set()).add(pos)
        if t in (1, 2, 3):
            collected.setdefault(fid, set()).add(pos)
        state["x"], state["y"] = pos
        after = state_view(state)
        record_step(steps, segment["name"], fid, pos, eid, describe_action(t, eid), before, after, note)
        if eid != expected_eid:
            steps[-1]["note"] = (steps[-1]["note"] + " " if steps[-1]["note"] else "") + f"expected {expected_eid}"

    if "exit_to" in segment:
        next_floor, next_pos = segment["exit_to"]
        state["floor"] = next_floor
        state["x"], state["y"] = next_pos

    return {
        "name": segment["name"],
        "floor": fid,
        "actual": state_view(state),
        "gold_delta": state["gold"] - start_gold,
        "dmg_delta": state.get("_dmg", 0) - start_dmg,
        "door_delta": [
            state.get("_yd", 0) - start_doors[0],
            state.get("_bd", 0) - start_doors[1],
            state.get("_rd", 0) - start_doors[2],
        ],
    }


def removed_for_floor(cleared: dict[str, set[tuple[int, int]]], fid: str) -> set[tuple[int, int]]:
    return set(cleared.get(fid, set()))


def apply_search_segment(
    name: str,
    fid: str,
    target_ids: list[str],
    state: dict[str, Any],
    maps: dict[str, Any],
    blocks: dict[str, dict[tuple[int, int], tuple[int, str]]],
    cleared: dict[str, set[tuple[int, int]]],
    collected: dict[str, set[tuple[int, int]]],
    steps: list[dict[str, Any]],
    merchant_buy: bool = False,
    target_pos: tuple[int, int] | None = None,
) -> dict[str, Any]:
    start_gold = state["gold"]
    start_dmg = state.get("_dmg", 0)
    start_doors = (state.get("_yd", 0), state.get("_bd", 0), state.get("_rd", 0))
    search_data = maps[fid]
    search_target_ids = target_ids
    if target_pos is not None:
        search_data = deepcopy(maps[fid])
        marker_eid = f"__target_x{target_pos[0]}y{target_pos[1]}"
        patched = False
        patched_blocks = []
        for x, y, t, eid in search_data["bl"]:
            if (x, y) == target_pos:
                patched_blocks.append((x, y, t, marker_eid))
                patched = True
            else:
                patched_blocks.append((x, y, t, eid))
        if not patched:
            raise RuntimeError(f"target_pos {fid} x{target_pos[0]}y{target_pos[1]} is not a block")
        search_data["bl"] = patched_blocks
        search_target_ids = [marker_eid]
    search_steps, final_state, vis_pos = search_with_path(
        search_data,
        state["x"],
        state["y"],
        state["hp"],
        state["atk"],
        state["def"],
        state["yk"],
        state["bk"],
        state["rk"],
        search_target_ids,
        max_iter=500000,
        removed_pos=removed_for_floor(cleared, fid),
        select_mode="min_damage",
    )
    if not search_steps or final_state is None:
        raise RuntimeError(f"cannot find segment {name} on {fid} targets={target_ids}")

    for raw in search_steps:
        pos = (raw["x"], raw["y"])
        t, _map_eid = block_at(blocks, fid, pos)
        before = state_view(state)
        if target_pos is None:
            eid = raw["eid"]
            state["hp"] = raw["hp_after"]
            state["atk"] = raw["atk"]
            state["def"] = raw["def"]
            state["yk"] = raw["yk"]
            state["bk"] = raw["bk"]
            state["rk"] = raw.get("rk", state["rk"])
        else:
            eid = _map_eid
            hp_before = state["hp"]
            _old, _new, error = fixed.apply_action(state, t, eid)
            if error:
                raise RuntimeError(f"{name} failed at {fid} x{pos[0]}y{pos[1]}: {error}")
            raw = dict(raw)
            raw["hp_before"] = hp_before
            raw["hp_after"] = state["hp"]
        state["x"], state["y"] = pos
        note = ""
        if t == 1:
            dmg = max(0, raw["hp_before"] - raw["hp_after"])
            state["_dmg"] += dmg
            gained = apply_gold_for_eid(state, eid)
            note = f"+{gained}G" if gained else ""
        elif t == 2:
            if eid == "yellowDoor":
                state["_yd"] += 1
            elif eid == "blueDoor":
                state["_bd"] += 1
            elif eid == "redDoor":
                state["_rd"] += 1
        cleared.setdefault(fid, set()).add(pos)
        if t in (1, 2, 3):
            collected.setdefault(fid, set()).add(pos)
        after = state_view(state)
        record_step(steps, name, fid, pos, eid, describe_action(t, eid), before, after, note)

    if merchant_buy:
        if state["gold"] < MERCHANT_COST:
            raise RuntimeError(f"merchant reached with only {state['gold']}G, need {MERCHANT_COST}G")
        before = state_view(state)
        state["gold"] -= MERCHANT_COST
        state["_gold_spent"] += MERCHANT_COST
        state["yk"] += MERCHANT_YK_GAIN
        state["bk"] += MERCHANT_BK_GAIN
        after = state_view(state)
        gain_text_parts = []
        if MERCHANT_YK_GAIN:
            gain_text_parts.append(f"{MERCHANT_YK_GAIN} yellow keys")
        if MERCHANT_BK_GAIN:
            gain_text_parts.append(f"{MERCHANT_BK_GAIN} blue keys")
        gain_text = " and ".join(gain_text_parts)
        note_parts = [f"-{MERCHANT_COST}G"]
        if MERCHANT_YK_GAIN:
            note_parts.append(f"+{MERCHANT_YK_GAIN}YK")
        if MERCHANT_BK_GAIN:
            note_parts.append(f"+{MERCHANT_BK_GAIN}BK")
        record_step(
            steps,
            name,
            fid,
            MERCHANT_POS,
            MERCHANT_EID,
            f"buy {gain_text}",
            before,
            after,
            " ".join(note_parts),
        )

    return {
        "name": name,
        "floor": fid,
        "actual": state_view(state),
        "gold_delta": state["gold"] - start_gold,
        "dmg_delta": state.get("_dmg", 0) - start_dmg,
        "door_delta": [
            state.get("_yd", 0) - start_doors[0],
            state.get("_bd", 0) - start_doors[1],
            state.get("_rd", 0) - start_doors[2],
        ],
    }


def replay() -> dict[str, Any]:
    hero, maps = load_data()
    patch_merchant(maps)
    blocks = fixed.block_map(maps)
    cleared = fixed.empty_collected()
    collected = fixed.empty_collected()
    state = fixed.initial_state(hero)
    state.update({
        "gold": INITIAL_GOLD,
        "_gold_initial": INITIAL_GOLD,
        "_gold_gained": 0,
        "_gold_spent": 0,
        "_dmg": 0,
        "_yd": 0,
        "_bd": 0,
        "_rd": 0,
    })
    steps: list[dict[str, Any]] = []
    segments: list[dict[str, Any]] = []

    # Fixed prefix through MT6, ending at the MT7 entrance.
    for segment_index in range(5):
        segments.append(apply_fixed_segment(fixed_segment(segment_index), state, maps, blocks, cleared, collected, steps))

    # The merchant is a separate resource action because it consumes gold.
    segments.append(
        apply_search_segment(
            "7F merchant x6y1 (50G -> 5YK)",
            MERCHANT_FID,
            [MERCHANT_EID],
            state,
            maps,
            blocks,
            cleared,
            collected,
            steps,
            merchant_buy=True,
        )
    )
    segments.append(
        apply_search_segment(
            "7F redGem after merchant",
            "MT7",
            ["redGem"],
            state,
            maps,
            blocks,
            cleared,
            collected,
            steps,
        )
    )
    segments.append(
        apply_search_segment(
            "7F upFloor after merchant",
            "MT7",
            ["upFloor"],
            state,
            maps,
            blocks,
            cleared,
            collected,
            steps,
        )
    )
    state["floor"] = "MT8"
    state["x"], state["y"] = (1, 1)

    # Fixed 8F and 9F prefix.
    for segment_index in range(6, len(fixed.ROUTE)):
        segments.append(apply_fixed_segment(fixed_segment(segment_index), state, maps, blocks, cleared, collected, steps))

    return {
        "assumptions": {
            "enemy_gold": ENEMY_GOLD,
            "score_conversion": {
                "100_gold": "1YK",
                "1_yellow_key": "50HP",
            },
            "merchant": {
                "floor": MERCHANT_FID,
                "pos": list(MERCHANT_POS),
                "cost_gold": MERCHANT_COST,
                "yk_gain": MERCHANT_YK_GAIN,
                "bk_gain": MERCHANT_BK_GAIN,
            },
        },
        "initial_state": state_view({
            "hp": hero["h"],
            "atk": hero["a"],
            "def": hero["d"],
            "yk": hero["yk"],
            "bk": hero["bk"],
            "rk": 0,
            "gold": INITIAL_GOLD,
        }),
        "final_state": deepcopy(state),
        "segments": segments,
        "steps": steps,
        "collected": {fid: sorted(list(pos)) for fid, pos in collected.items()},
    }


def write_outputs(result: dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    lines = [
        "# 4-9 Merchant Gold Walk",
        "",
        f"- merchant: {MERCHANT_FID} x{MERCHANT_POS[0]}y{MERCHANT_POS[1]}, {MERCHANT_COST}G -> {merchant_offer_text()}",
        f"- final: {state_text(result['final_state'])} dmg={result['final_state']['_dmg']} door={result['final_state']['_yd']}/{result['final_state']['_bd']}/{result['final_state']['_rd']}",
        f"- gold initial/gained/spent/left: {result['final_state']['_gold_initial']}/{result['final_state']['_gold_gained']}/{result['final_state']['_gold_spent']}/{result['final_state']['gold']}",
        "",
        "Gold table used:",
        "",
        "```json",
        json.dumps(ENEMY_GOLD, ensure_ascii=False, indent=2),
        "```",
        "",
    ]
    by_segment: dict[str, list[dict[str, Any]]] = {}
    for step in result["steps"]:
        by_segment.setdefault(step["segment"], []).append(step)

    for idx, segment in enumerate(result["segments"], 1):
        lines.append(f"## {idx}. {segment['name']}")
        lines.append("")
        for step in by_segment.get(segment["name"], []):
            delta = step_delta(step["before"], step["after"])
            note = f" ({step['note']})" if step.get("note") else ""
            delta_part = f" [{delta}]" if delta else ""
            lines.append(
                f"- {step['floor']} x{step['x']}y{step['y']} {step['action']} {step['eid']}"
                f"{delta_part}{note}"
            )
        door = segment["door_delta"]
        lines.append(
            f"- segment result: {state_text(segment['actual'])}; "
            f"seg_dmg={segment['dmg_delta']}; seg_door={door[0]}/{door[1]}/{door[2]}; "
            f"seg_gold={segment['gold_delta']:+d}"
        )
        lines.append("")

    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")


def main() -> None:
    result = replay()
    write_outputs(result)
    print(f"wrote {OUT_MD}")
    print(f"wrote {OUT_JSON}")
    print(
        f"final {state_text(result['final_state'])} "
        f"dmg={result['final_state']['_dmg']} "
        f"door={result['final_state']['_yd']}/{result['final_state']['_bd']}/{result['final_state']['_rd']} "
        f"gold initial/gained/spent/left={result['final_state']['_gold_initial']}/{result['final_state']['_gold_gained']}/{result['final_state']['_gold_spent']}/{result['final_state']['gold']}"
    )


if __name__ == "__main__":
    main()
