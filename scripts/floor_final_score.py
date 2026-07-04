#!/usr/bin/env python3
"""Current-floor-and-below final-score helpers.

The scorer works on a replay object after the route has mutated its floor maps.
That matters for live/auto side effects: a killed 0-damage monster has already
increased current gold and has been removed from ``floor.blocks``; an un-killed
0-damage monster is still present in ``floor.blocks`` and is counted as a
remaining resource. This is what prevents double counting.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

YK_VALUE = 50
BK_VALUE = 200
GOLD_HP_RATE = 0.5

RESOURCE_ITEMS = {
    "yellowKey",
    "blueKey",
    "redKey",
    "redPotion",
    "bluePotion",
    "redGem",
    "blueGem",
    "sword3",
    "shield3",
    "pickaxe",
    "bomb",
    "cross",
    "upFly",
    "downFly",
    "centerFly",
    "centerFly3",
    "earthquake",
    "snow",
    "coin",
    "superPotion",
}

IMPORTANT_TOOLS = (
    "centerFly",
    "centerFly3",
    "pickaxe",
    "earthquake",
    "upFly",
    "downFly",
    "snow",
    "cross",
    "bomb",
)


def enemy_damage(g: Any, eid: str) -> int | float:
    if hasattr(g, "damage_for"):
        return g.damage_for(eid)
    if hasattr(g, "enemy_damage"):
        return g.enemy_damage(eid)
    raise AttributeError("replay object has neither damage_for nor enemy_damage")


def floor_no(fid: str) -> int:
    return int(fid[2:]) if fid.startswith("MT") and fid[2:].isdigit() else 0


def item_value_hp(eid: str, ratio: int) -> float:
    if eid == "yellowKey":
        return float(YK_VALUE)
    if eid == "blueKey":
        return float(BK_VALUE)
    if eid == "redPotion":
        return float(50 * ratio)
    if eid == "bluePotion":
        return float(200 * ratio)
    # Red keys, gems, swords/shields, and tools are strategically important but
    # have 0 leftover score in the project scoring convention.
    return 0.0


def stock_score(state: dict[str, Any]) -> float:
    return (
        float(state.get("hp", 0))
        + float(state.get("yk", 0)) * YK_VALUE
        + float(state.get("bk", 0)) * BK_VALUE
        + float(state.get("gold", 0)) * GOLD_HP_RATE
    )


def held_tool_counts(state: dict[str, Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    if state.get("centerFly") or state.get("centerFly3"):
        counts["centerFly"] = int(state.get("centerFly", 1) or 1)
    for key in IMPORTANT_TOOLS:
        if key in {"centerFly", "centerFly3"}:
            continue
        value = state.get(key)
        if isinstance(value, bool):
            counts[key] = int(value)
        elif isinstance(value, int) and value > 0:
            counts[key] = value
    return {key: value for key, value in counts.items() if value}


def resource_rows(
    g: Any,
    floor_limit: int | None = None,
    *,
    monster_gold_factor: float = GOLD_HP_RATE,
) -> list[dict[str, Any]]:
    """Return remaining resource rows on floors <= ``floor_limit``.

    Monster money is scored only when the monster is already 0 damage at the
    current stats. Non-zero-damage monsters are listed for audit, but their
    ``value_hp`` is 0 so they do not inflate final-score.
    """

    limit = floor_limit if floor_limit is not None else floor_no(g.state["floor"])
    rows: list[dict[str, Any]] = []
    for fid in sorted(g.floors, key=floor_no):
        if floor_no(fid) > limit:
            continue
        floor = g.floors[fid]
        ratio = int(getattr(floor, "ratio", 1) or 1)
        for pos, block in sorted(floor.blocks.items()):
            x, y = pos
            if block.kind == "item" and block.eid in RESOURCE_ITEMS:
                value = item_value_hp(block.eid, ratio)
                rows.append(
                    {
                        "floor": fid,
                        "x": x,
                        "y": y,
                        "kind": "item",
                        "eid": block.eid,
                        "ratio": ratio,
                        "value_hp": value,
                    }
                )
            elif block.kind == "enemy":
                dmg = enemy_damage(g, block.eid)
                money = int(g.enemies[block.eid]["money"])
                zero = dmg == 0
                value = float(money) * monster_gold_factor if zero else 0.0
                rows.append(
                    {
                        "floor": fid,
                        "x": x,
                        "y": y,
                        "kind": "enemy",
                        "eid": block.eid,
                        "money": money,
                        "damage": "inf" if dmg == float("inf") else int(dmg),
                        "zero_damage": zero,
                        "value_hp": value,
                    }
                )
    return rows


def current_floor_and_below_final_score(
    g: Any,
    floor_limit: int | None = None,
    *,
    monster_gold_factor: float = GOLD_HP_RATE,
) -> dict[str, Any]:
    """Compute the current-floor-and-below final-score breakdown."""

    limit = floor_limit if floor_limit is not None else floor_no(g.state["floor"])
    rows = resource_rows(g, limit, monster_gold_factor=monster_gold_factor)
    item_counts: Counter[str] = Counter()
    enemy_counts: Counter[str] = Counter()
    zero_enemy_counts: Counter[str] = Counter()
    nonzero_enemy_counts: Counter[str] = Counter()
    map_tool_counts: Counter[str] = Counter()
    item_value = 0.0
    zero_enemy_value = 0.0
    nonzero_enemy_gold = 0
    for row in rows:
        value = float(row["value_hp"])
        if row["kind"] == "item":
            eid = row["eid"]
            item_counts[eid] += 1
            item_value += value
            if eid in IMPORTANT_TOOLS:
                map_tool_counts[eid] += 1
        elif row["kind"] == "enemy":
            eid = row["eid"]
            enemy_counts[eid] += 1
            if row["zero_damage"]:
                zero_enemy_counts[eid] += 1
                zero_enemy_value += value
            else:
                nonzero_enemy_counts[eid] += 1
                nonzero_enemy_gold += int(row["money"])
    stock = stock_score(g.state)
    remaining_value = item_value + zero_enemy_value
    return {
        "floor_limit": limit,
        "monster_gold_factor": monster_gold_factor,
        "stock_score": stock,
        "item_value_hp": item_value,
        "zero_damage_monster_value_hp": zero_enemy_value,
        "remaining_value_hp": remaining_value,
        "final_score": stock + remaining_value,
        "item_counts": dict(sorted(item_counts.items())),
        "enemy_counts": dict(sorted(enemy_counts.items())),
        "zero_enemy_counts": dict(sorted(zero_enemy_counts.items())),
        "nonzero_enemy_counts": dict(sorted(nonzero_enemy_counts.items())),
        "nonzero_enemy_gold_excluded": nonzero_enemy_gold,
        "map_tool_counts": dict(sorted(map_tool_counts.items())),
        "held_tool_counts": held_tool_counts(g.state),
        "resource_count": len(rows),
    }
