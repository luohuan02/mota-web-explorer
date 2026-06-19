#!/usr/bin/env python3
"""Zone-2 remaining resource groups for scoring and diff reports."""

from __future__ import annotations

from collections import deque
from typing import Any

from scripts import replay_zone2_guide_route as zone2

YK_VALUE = 50
BK_VALUE = 200


def super_potion_value(final: dict[str, Any]) -> int:
    return int(0.74 * (final["atk"] + final["def"]) + 0.5) * 10


def item_value(fid: str, eid: str, floor: zone2.Floor, final: dict[str, Any]) -> float:
    if eid == "yellowKey":
        return YK_VALUE
    if eid == "blueKey":
        return BK_VALUE
    if eid == "redPotion":
        return 50 * floor.ratio
    if eid == "bluePotion":
        return 200 * floor.ratio
    if eid == "redKey":
        return 0
    if eid in {"redGem", "blueGem", "greenGem"}:
        return 0
    if eid in {"sword2", "shield2", "sword5", "pickaxe", "cross", "fly"}:
        return 0
    return 0


def door_cost(eid: str) -> int:
    if eid == "yellowDoor":
        return YK_VALUE
    if eid == "blueDoor":
        return BK_VALUE
    return 0


def is_wall_for_group(rep: zone2.Replay, fid: str, pos: tuple[int, int]) -> bool:
    x, y = pos
    floor = rep.floors[fid]
    if x < 0 or y < 0 or x >= floor.width or y >= floor.height:
        return True
    if x == 0 or y == 0 or x == floor.width - 1 or y == floor.height - 1:
        return True
    if pos in rep.cleared.get(fid, set()):
        return False
    tile = floor.grid[y][x]
    if tile in {1, 5, 330}:
        return True
    if fid == "MT15" and tile == 17:
        return True
    block = floor.blocks.get(pos)
    if block and block.eid == "specialDoor":
        return True
    return False


def component_cells(rep: zone2.Replay, fid: str) -> list[set[tuple[int, int]]]:
    floor = rep.floors[fid]
    seen: set[tuple[int, int]] = set()
    groups: list[set[tuple[int, int]]] = []
    for y in range(floor.height):
        for x in range(floor.width):
            start = (x, y)
            if start in seen or is_wall_for_group(rep, fid, start):
                continue
            queue = deque([start])
            seen.add(start)
            cells = {start}
            while queue:
                cx, cy = queue.popleft()
                for nxt in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                    if nxt in seen or is_wall_for_group(rep, fid, nxt):
                        continue
                    seen.add(nxt)
                    cells.add(nxt)
                    queue.append(nxt)
            groups.append(cells)
    return groups


def remaining_resource_groups(
    rep: zone2.Replay,
    enemies: dict[str, dict[str, Any]],
    final: dict[str, Any],
    include_zero: bool = False,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for fid in sorted(rep.floors, key=lambda f: int(f[2:]) if f.startswith("MT") and f[2:].isdigit() else 0):
        floor = rep.floors[fid]
        for cells in component_cells(rep, fid):
            items: list[dict[str, Any]] = []
            monsters: list[dict[str, Any]] = []
            doors: list[dict[str, Any]] = []
            reward = 0.0
            cost = 0
            for pos in sorted(cells):
                if pos in rep.cleared.get(fid, set()):
                    continue
                block = floor.blocks.get(pos)
                if not block:
                    continue
                if block.kind == "item":
                    value = item_value(fid, block.eid, floor, final)
                    if value > 0:
                        reward += value
                        items.append({"pos": f"x{pos[0]}y{pos[1]}", "eid": block.eid, "value": value})
                elif block.kind == "enemy":
                    value = float(enemies.get(block.eid, {}).get("money", 0)) * 0.5
                    if value > 0:
                        reward += value
                        monsters.append({"pos": f"x{pos[0]}y{pos[1]}", "eid": block.eid, "gold_value": value})
                elif block.kind == "door":
                    value = door_cost(block.eid)
                    if value > 0:
                        cost += value
                        doors.append({"pos": f"x{pos[0]}y{pos[1]}", "eid": block.eid, "cost": value})
            value = reward - cost
            if value < 0 or (value == 0 and not include_zero):
                continue
            if not items and not monsters:
                continue
            label_bits = []
            if items:
                label_bits.extend(f"{item['pos']} {zone2.ITEM_CN.get(item['eid'], item['eid'])}" for item in items[:3])
            if monsters:
                label_bits.extend(f"{mon['pos']} {zone2.ITEM_CN.get(mon['eid'], mon['eid'])}" for mon in monsters[:3])
            group_name = f"{fid} " + "、".join(label_bits)
            rows.append(
                {
                    "key": group_name,
                    "fid": fid,
                    "group": group_name,
                    "items": items,
                    "monsters": monsters,
                    "doors": doors,
                    "reward": reward,
                    "door_cost": cost,
                    "value": value,
                }
            )

    if (11, 11) not in rep.cleared.get("MT16", set()):
        value = super_potion_value(final)
        rows.append(
            {
                "key": "MT16 圣水事件",
                "fid": "MT16",
                "group": "MT16 圣水事件",
                "items": [{"pos": "x11y11", "eid": "superPotion", "value": value}],
                "monsters": [],
                "doors": [],
                "reward": value,
                "door_cost": 0,
                "value": value,
            }
        )
    rows.sort(key=lambda row: (row["fid"], row["group"]))
    return rows


def remaining_resource_value(rep: zone2.Replay, enemies: dict[str, dict[str, Any]], final: dict[str, Any]) -> float:
    return sum(row["value"] for row in remaining_resource_groups(rep, enemies, final))
