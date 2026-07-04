#!/usr/bin/env python3
"""Build a static future-resource-group cache from a live h5mota snapshot.

The cache is intentionally conservative: it overlays the current browser save
snapshot on top of the repository map JSON, then groups remaining item cells
that are connected without crossing a fresh enemy, door, hard wall, or lava.
Fake walls are treated as passable when the live auto-wall setting is enabled,
because the game can open them without spending route resources.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SNAPSHOT = ROOT / "outputs" / "results" / "save1_current_snapshot.json"
DEFAULT_OUT_JSON = ROOT / "outputs" / "results" / "save1_future_resource_group_cache.json"
DEFAULT_OUT_MD = ROOT / "outputs" / "reports" / "save1_future_resource_group_cache.md"

DOORS = {"yellowDoor", "blueDoor", "redDoor", "specialDoor", "steelDoor"}
STAIRS = {"upFloor", "downFloor"}
SHOP_SIDES = {"blueShop-left", "blueShop-right", "pinkShop-left", "pinkShop-right"}
SHOP_IDS = {"blueShop", "pinkShop"}
TRADER_IDS = {"trader", "specialTrader"}
OLDMAN_IDS = {"oldman"}
EVENT_BLOCK_TILES = {17}
HARD_WALLS = {
    "yellowWall",
    "whiteWall",
    "whiteWall2",
    "blueWall",
    "unbreakableWall",
    "blockWall",
    "autotile",
    "star",
    "blueWater",
    "water",
    "flower",
    "darkLight",
    "box",
    "boxed",
}
AUTO_WALLS = {"fakeWall", "fakeWall2"}
LAVA = {"lava"}
POTIONS = {"redPotion", "bluePotion", "greenPotion", "yellowPotion"}
CORE_TOOL_ITEMS = {
    "cross",
    "snow",
    "earthquake",
    "pickaxe",
    "upFly",
    "downFly",
    "centerFly",
    "centerFly3",
    "knife",
    "coin",
    "superPotion",
}
CORE_KEY_ITEMS = {"redKey"}
SECONDARY_STAT_ITEMS = {"redGem", "blueGem"}
SUPPORT_ITEMS = {"yellowKey", "blueKey", *POTIONS}
STRATEGY_ROLE_CN = {
    "core_target": "核心目标",
    "secondary_stat": "二等属性",
    "support_resource": "补充资源",
    "conversion_node": "转换节点",
    "story_event": "剧情/未知",
}

ITEM_CN = {
    "redGem": "红宝石",
    "blueGem": "蓝宝石",
    "yellowKey": "黄钥匙",
    "blueKey": "蓝钥匙",
    "redKey": "红钥匙",
    "redPotion": "红血瓶",
    "bluePotion": "蓝血瓶",
    "sword1": "铁剑",
    "sword2": "银剑",
    "sword3": "骑士剑",
    "sword4": "圣剑",
    "sword5": "神圣剑",
    "shield1": "铁盾",
    "shield2": "银盾",
    "shield3": "骑士盾",
    "shield4": "圣盾",
    "shield5": "神圣盾",
    "pickaxe": "稿",
    "earthquake": "地震卷轴",
    "upFly": "上楼飞行器",
    "downFly": "下楼飞行器",
    "centerFly": "中心对称飞行器",
    "centerFly3": "中心对称飞行器",
    "coin": "幸运金币",
    "snow": "冰魔法",
    "knife": "屠龙匕首",
    "cross": "十字架",
    "superPotion": "圣水",
}

NPC_CN = {
    "oldman": "老人",
    "trader": "商人",
    "specialTrader": "特殊商人",
    "blueShop": "蓝商店",
    "pinkShop": "红商店",
    "thief": "小偷",
    "king": "国王",
    "princess": "公主",
}

NPC_RESOURCE_HINTS: dict[tuple[str, int, int], dict[str, Any]] = {
    ("MT2", 11, 4): {
        "resource_model": "one_time_reward",
        "options": [{"label": "老人奖励", "gain": {"gold": 1000}}],
        "note": "2F 老人给 1000G。",
    },
    ("MT2", 11, 7): {
        "resource_model": "one_time_dynamic_reward",
        "options": [{"label": "祝福", "gain_dynamic": "ATK += round(ATK*0.03), DEF += round(DEF*0.03)"}],
        "note": "特殊商人祝福，收益随当前攻防变化。",
    },
    ("MT4", 6, 1): {
        "resource_model": "shop",
        "options": [{"label": "普通商店", "cost_dynamic": "shop_cost(times1)", "gain_dynamic": "ATK+2, DEF+4, or HP shop by times1"}],
        "note": "1区商店；两侧商店图块不可作为通路。",
    },
    ("MT6", 8, 4): {
        "resource_model": "merchant",
        "options": [{"label": "买蓝钥匙", "cost": {"gold": 50}, "gain": {"bk": 1}}],
        "note": "6F 商人，50G 买 1 蓝钥匙。",
    },
    ("MT7", 6, 1): {
        "resource_model": "merchant",
        "options": [{"label": "买黄钥匙", "cost": {"gold": 50}, "gain": {"yk": 5}}],
        "note": "7F 商人，50G 买 5 黄钥匙。",
    },
    ("MT12", 6, 9): {
        "resource_model": "shop",
        "options": [{"label": "二区商店", "cost_dynamic": "shop_cost(times1)", "gain_dynamic": "ratio=2 shop choices"}],
        "note": "12F 商店，ratio=2。",
    },
    ("MT12", 11, 1): {
        "id": "specialTrader",
        "name": "特殊商人",
        "kind": "trader",
        "resource_model": "repeatable_merchant",
        "options": [{"label": "买黄钥匙", "cost": {"gold": 1000}, "gain": {"yk": 1}}],
        "note": "12F 特殊商人，1000G 买 1 黄钥匙，可重复到金币不足。",
    },
    ("MT16", 11, 11): {
        "id": "oldman",
        "name": "圣水老人",
        "kind": "oldman",
        "resource_model": "one_time_tool",
        "options": [{"label": "拿圣水", "gain": {"tools": 1}, "gain_item": "superPotion", "use_dynamic": "HP += ATK + DEF when used"}],
        "note": "16F 老人给圣水；使用时收益随 ATK+DEF 变化。",
    },
    ("MT28", 8, 4): {
        "resource_model": "repeatable_merchant",
        "options": [{"label": "卖黄钥匙", "cost": {"yk": 1}, "gain": {"gold": 100}}],
        "note": "28F 商人，黄钥匙换金币；额外功能可批量卖。",
    },
    ("MT32", 10, 10): {
        "resource_model": "shop",
        "options": [{"label": "三区商店", "cost_dynamic": "shop_cost(times1)", "gain_dynamic": "ratio=4 shop choices"}],
        "note": "32F 商店，ratio=4。",
    },
    ("MT38", 5, 2): {
        "resource_model": "merchant",
        "options": [{"label": "买黄钥匙", "cost": {"gold": 200}, "gain": {"yk": 3}}],
        "note": "38F 商人，200G 买 3 黄钥匙。",
    },
    ("MT46", 6, 1): {
        "resource_model": "shop",
        "options": [{"label": "四区商店", "cost_dynamic": "shop_cost(times1)", "gain_dynamic": "ratio=5 shop choices"}],
        "note": "46F 商店，ratio=5。",
    },
}


def resolve_item_id(number: Any, tiles: dict[int, Any], item_ids: set[str]) -> str | None:
    if isinstance(number, str) and number in item_ids:
        return number
    try:
        tile = int(number)
    except (TypeError, ValueError):
        return None
    info = tiles.get(tile)
    if info and info.get("cls") == "items":
        return str(info["id"])
    return None


def parse_locs(raw: Any, fallback: tuple[int, int] | None = None) -> list[tuple[int, int]]:
    if raw is None:
        return [fallback] if fallback else []
    if (
        isinstance(raw, list)
        and len(raw) == 2
        and all(isinstance(v, int) for v in raw)
    ):
        return [(int(raw[0]), int(raw[1]))]
    locs: list[tuple[int, int]] = []
    if isinstance(raw, list):
        for item in raw:
            locs.extend(parse_locs(item, fallback=None))
    return locs


def eval_simple_condition(condition: Any, flags: dict[str, Any]) -> bool | None:
    if condition == "flag:开启特性":
        return bool(flags.get("开启特性", 0))
    return None


def collect_setblock_items(
    node: Any,
    *,
    tiles: dict[int, Any],
    item_ids: set[str],
    flags: dict[str, Any],
    trigger_pos: tuple[int, int] | None,
    branch_notes: list[str],
) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    if isinstance(node, list):
        for child in node:
            found.extend(
                collect_setblock_items(
                    child,
                    tiles=tiles,
                    item_ids=item_ids,
                    flags=flags,
                    trigger_pos=trigger_pos,
                    branch_notes=branch_notes,
                )
            )
        return found
    if not isinstance(node, dict):
        return found

    if node.get("type") == "if":
        cond = node.get("condition")
        value = eval_simple_condition(cond, flags)
        branches: list[tuple[str, Any]]
        if value is True:
            branches = [(f"{cond}=true", node.get("true", []))]
        elif value is False:
            branches = [(f"{cond}=false", node.get("false", []))]
        else:
            branches = [(f"{cond}=true?", node.get("true", [])), (f"{cond}=false?", node.get("false", []))]
        for note, child in branches:
            found.extend(
                collect_setblock_items(
                    child,
                    tiles=tiles,
                    item_ids=item_ids,
                    flags=flags,
                    trigger_pos=trigger_pos,
                    branch_notes=branch_notes + [note],
                )
            )
        return found

    if node.get("type") == "setBlock":
        eid = resolve_item_id(node.get("number"), tiles, item_ids)
        if eid:
            for x, y in parse_locs(node.get("loc"), fallback=trigger_pos):
                found.append({"x": x, "y": y, "id": eid, "condition_path": list(branch_notes)})

    for key, child in node.items():
        if key in {"true", "false"}:
            continue
        found.extend(
            collect_setblock_items(
                child,
                tiles=tiles,
                item_ids=item_ids,
                flags=flags,
                trigger_pos=trigger_pos,
                branch_notes=branch_notes,
            )
        )
    return found


def collect_map_changes(
    node: Any,
    *,
    tiles: dict[int, Any],
    flags: dict[str, Any],
    trigger_pos: tuple[int, int] | None,
    branch_notes: list[str],
) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    if isinstance(node, list):
        for child in node:
            found.extend(
                collect_map_changes(
                    child,
                    tiles=tiles,
                    flags=flags,
                    trigger_pos=trigger_pos,
                    branch_notes=branch_notes,
                )
            )
        return found
    if not isinstance(node, dict):
        return found

    if node.get("type") == "if":
        cond = node.get("condition")
        value = eval_simple_condition(cond, flags)
        branches: list[tuple[str, Any]]
        if value is True:
            branches = [(f"{cond}=true", node.get("true", []))]
        elif value is False:
            branches = [(f"{cond}=false", node.get("false", []))]
        else:
            branches = [(f"{cond}=true?", node.get("true", [])), (f"{cond}=false?", node.get("false", []))]
        for note, child in branches:
            found.extend(
                collect_map_changes(
                    child,
                    tiles=tiles,
                    flags=flags,
                    trigger_pos=trigger_pos,
                    branch_notes=branch_notes + [note],
                )
            )
        return found

    typ = node.get("type")
    if typ in {"hide", "openDoor", "closeDoor", "show"}:
        locs = parse_locs(node.get("loc"), fallback=trigger_pos if typ == "hide" else None)
        if locs:
            found.append(
                {
                    "action": typ,
                    "locs": [{"x": x, "y": y} for x, y in locs],
                    "id": node.get("id"),
                    "remove": node.get("remove"),
                    "conditions": list(branch_notes),
                }
            )
    elif typ == "setBlock":
        number = node.get("number")
        eid = resolve_item_id(number, tiles, {str(info["id"]) for info in tiles.values() if info.get("cls") == "items"})
        if eid is None:
            locs = parse_locs(node.get("loc"), fallback=trigger_pos)
            if locs:
                try:
                    tile = int(number)
                    info = tiles.get(tile)
                    block_id = info["id"] if info else str(number)
                except (TypeError, ValueError):
                    block_id = str(number)
                found.append(
                    {
                        "action": "setBlock",
                        "number": str(number),
                        "id": block_id,
                        "locs": [{"x": x, "y": y} for x, y in locs],
                        "conditions": list(branch_notes),
                    }
                )

    for key, child in node.items():
        if key in {"true", "false"}:
            continue
        found.extend(
            collect_map_changes(
                child,
                tiles=tiles,
                flags=flags,
                trigger_pos=trigger_pos,
                branch_notes=branch_notes,
            )
        )
    return found


def parse_pos_key(key: str) -> tuple[int, int] | None:
    try:
        x_str, y_str = key.split(",", 1)
        return int(x_str), int(y_str)
    except (ValueError, AttributeError):
        return None


def event_resource_groups(
    fid: str,
    raw: dict[str, Any],
    *,
    tiles: dict[int, Any],
    flags: dict[str, Any],
    ratio: int,
) -> list[dict[str, Any]]:
    item_ids = {str(info["id"]) for info in tiles.values() if info.get("cls") == "items"}
    groups: list[dict[str, Any]] = []
    event_index = 1
    sections = (
        ("afterBattle", raw.get("afterBattle", {}), "战斗后"),
        ("afterOpenDoor", raw.get("afterOpenDoor", {}), "开门后"),
        ("afterGetItem", raw.get("afterGetItem", {}), "拾取后"),
        ("events", raw.get("events", {}), "事件后"),
    )
    for section, entries, label in sections:
        if not isinstance(entries, dict):
            continue
        for pos_key, payload in sorted(entries.items(), key=lambda kv: kv[0]):
            trigger_pos = parse_pos_key(pos_key)
            found = collect_setblock_items(
                payload.get("data", payload) if isinstance(payload, dict) else payload,
                tiles=tiles,
                item_ids=item_ids,
                flags=flags,
                trigger_pos=trigger_pos,
                branch_notes=[],
            )
            if not found:
                continue
            all_gain = {"hp": 0, "atk": 0, "def": 0, "yk": 0, "bk": 0, "rk": 0, "tools": 0}
            no_potion_gain = {"hp": 0, "atk": 0, "def": 0, "yk": 0, "bk": 0, "rk": 0, "tools": 0}
            records = []
            for item in sorted(found, key=lambda row: (row["y"], row["x"], row["id"])):
                gain = item_gain(item["id"], ratio)
                add_gain(all_gain, gain)
                if item["id"] not in POTIONS:
                    add_gain(no_potion_gain, gain)
                records.append(
                    {
                        "x": item["x"],
                        "y": item["y"],
                        "id": item["id"],
                        "name": ITEM_CN.get(item["id"], item["id"]),
                        "is_potion": item["id"] in POTIONS,
                        "gain": gain,
                        "condition_path": item["condition_path"],
                    }
                )
            strategy = strategy_for_items(records)
            groups.append(
                {
                    "floor": fid,
                    "group_id": f"{fid}.event{event_index:02d}",
                    "trigger_type": section,
                    "trigger_label": label,
                    "trigger_pos": {"x": trigger_pos[0], "y": trigger_pos[1]} if trigger_pos else None,
                    "items": records,
                    "item_count": len(records),
                    "potion_count": sum(1 for row in records if row["is_potion"]),
                    "gain_all_items": all_gain,
                    "gain_no_potions": no_potion_gain,
                    "conditions": sorted({note for row in records for note in row.get("condition_path", [])}),
                    "strategy": strategy,
                }
            )
            event_index += 1
    return groups


def event_map_changes(
    fid: str,
    raw: dict[str, Any],
    *,
    tiles: dict[int, Any],
    flags: dict[str, Any],
) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []
    event_index = 1
    sections = (
        ("afterBattle", raw.get("afterBattle", {}), "战斗后"),
        ("afterOpenDoor", raw.get("afterOpenDoor", {}), "开门后"),
        ("afterGetItem", raw.get("afterGetItem", {}), "拾取后"),
        ("events", raw.get("events", {}), "事件后"),
    )
    for section, entries, label in sections:
        if not isinstance(entries, dict):
            continue
        for pos_key, payload in sorted(entries.items(), key=lambda kv: kv[0]):
            trigger_pos = parse_pos_key(pos_key)
            changes = collect_map_changes(
                payload.get("data", payload) if isinstance(payload, dict) else payload,
                tiles=tiles,
                flags=flags,
                trigger_pos=trigger_pos,
                branch_notes=[],
            )
            if not changes:
                continue
            groups.append(
                {
                    "floor": fid,
                    "change_id": f"{fid}.change{event_index:02d}",
                    "trigger_type": section,
                    "trigger_label": label,
                    "trigger_pos": {"x": trigger_pos[0], "y": trigger_pos[1]} if trigger_pos else None,
                    "changes": changes,
                }
            )
            event_index += 1
    return groups


def npc_kind(eid: str) -> str:
    if eid in SHOP_IDS:
        return "shop"
    if eid in TRADER_IDS:
        return "trader"
    if eid in OLDMAN_IDS:
        return "oldman"
    return "npc"


def npc_resource_groups(fid: str, floor: dict[str, Any], raw: dict[str, Any]) -> list[dict[str, Any]]:
    npc_positions: dict[tuple[int, int], dict[str, Any]] = {}
    for (x, y), cell in floor["cells"].items():
        if cell["kind"] in {"shop", "trader", "oldman", "npc"}:
            npc_positions[(x, y)] = {
                "x": x,
                "y": y,
                "id": cell["id"],
                "name": NPC_CN.get(cell["id"], cell["id"]),
                "kind": npc_kind(cell["id"]),
                "visible_now": True,
                "tile": cell["tile"],
            }

    for (hint_fid, x, y), hint in NPC_RESOURCE_HINTS.items():
        if hint_fid != fid:
            continue
        npc_positions.setdefault(
            (x, y),
            {
                "x": x,
                "y": y,
                "id": hint.get("id", hint.get("resource_model", "resource_event")),
                "name": hint.get("name", hint.get("resource_model", "resource_event")),
                "kind": hint.get("kind", "resource_event"),
                "visible_now": False,
                "tile": None,
            },
        )

    groups: list[dict[str, Any]] = []
    for index, ((x, y), npc) in enumerate(sorted(npc_positions.items(), key=lambda kv: (kv[0][1], kv[0][0])), 1):
        hint = NPC_RESOURCE_HINTS.get((fid, x, y), {})
        resource_model = hint.get("resource_model", "dialogue_or_event")
        options = hint.get("options", [])
        event_payload = None
        events = raw.get("events") or {}
        if f"{x},{y}" in events:
            event_payload = events[f"{x},{y}"]
        groups.append(
            {
                "floor": fid,
                "group_id": f"{fid}.npc{index:02d}",
                "x": x,
                "y": y,
                "id": npc["id"],
                "name": npc["name"],
                "kind": npc["kind"],
                "visible_now": npc["visible_now"],
                "resource_model": resource_model,
                "options": options,
                "note": hint.get("note", ""),
                "has_event_payload": event_payload is not None,
                "search_treatment": (
                    "explicit_state_transition"
                    if hint.get("resource_model")
                    else "inspect_before_search_if_route_depends_on_it"
                ),
                "strategy": strategy_for_npc(resource_model, options),
            }
        )
    return groups


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def floor_no(fid: str) -> int:
    return int(fid[2:])


def default_ratio(fid: str) -> int:
    n = floor_no(fid)
    if 11 <= n <= 20:
        return 2
    if 31 <= n <= 40:
        return 4
    if 41 <= n <= 50:
        return 5
    return 1


def decode_grid(fid: str, base_grid: list[list[int]], snapshot: dict[str, Any]) -> list[list[int]]:
    saved = snapshot.get("maps", {}).get(fid) or {}
    saved_grid = saved.get("map")
    if not saved_grid:
        return [list(row) for row in base_grid]

    out: list[list[int]] = []
    for y, row in enumerate(saved_grid):
        if isinstance(row, int):
            out.append(list(base_grid[y]))
            continue
        out.append([base_grid[y][x] if value == -1 else int(value) for x, value in enumerate(row)])
    return out


def load_tiles() -> dict[int, dict[str, Any]]:
    raw = read_json(ROOT / "data" / "maps" / "tile_mapping.json")
    return {int(k): v for k, v in raw["tiles"].items()}


def load_enemies() -> dict[str, dict[str, Any]]:
    return read_json(ROOT / "data" / "maps" / "enemy_stats.json")["enemys"]


def classify(eid: str, cls: str, enemies: dict[str, Any]) -> str:
    if eid in enemies or cls == "enemys":
        return "enemy"
    if eid in DOORS:
        return "door"
    if cls == "items":
        return "item"
    if eid in SHOP_SIDES:
        return "shopSide"
    if eid in SHOP_IDS:
        return "shop"
    if eid in TRADER_IDS:
        return "trader"
    if eid in OLDMAN_IDS:
        return "oldman"
    if eid in AUTO_WALLS:
        return "autoWall"
    if eid in LAVA:
        return "lava"
    if eid in HARD_WALLS or cls in {"animates", "autotile"}:
        return "wall"
    if eid in STAIRS:
        return "terrain"
    if cls == "npcs":
        return "npc"
    return "other"


def enemy_damage(enemy: dict[str, Any], atk: int, defense: int) -> int | None:
    if atk <= int(enemy.get("def", 0)):
        return None
    turns = (int(enemy["hp"]) + atk - int(enemy["def"]) - 1) // (atk - int(enemy["def"]))
    return max(0, int(enemy["atk"]) - defense) * max(0, turns - 1)


def item_gain(eid: str, ratio: int) -> dict[str, int]:
    gain = {"hp": 0, "atk": 0, "def": 0, "yk": 0, "bk": 0, "rk": 0, "tools": 0}
    if eid == "redPotion":
        gain["hp"] += 50 * ratio
    elif eid == "bluePotion":
        gain["hp"] += 200 * ratio
    elif eid == "redGem":
        gain["atk"] += 1 * ratio
    elif eid == "blueGem":
        gain["def"] += 1 * ratio
    elif eid == "yellowKey":
        gain["yk"] += 1
    elif eid == "blueKey":
        gain["bk"] += 1
    elif eid == "redKey":
        gain["rk"] += 1
    elif eid.startswith("sword"):
        gain["atk"] += 10 * ratio
    elif eid.startswith("shield"):
        gain["def"] += 10 * ratio
    else:
        gain["tools"] += 1
    return gain


def item_strategy_role(eid: str) -> tuple[str, str]:
    if eid.startswith("sword"):
        return "core_target", "剑类决定攻杀阈值和 boss 路线"
    if eid.startswith("shield"):
        return "core_target", "盾类决定防杀阈值和半血后稳定性"
    if eid in CORE_KEY_ITEMS:
        return "core_target", "红钥匙通常打开关键路线分支"
    if eid in CORE_TOOL_ITEMS:
        return "core_target", "关键道具/剧情工具会改变可达区域或终局条件"
    if eid in SECONDARY_STAT_ITEMS:
        return "secondary_stat", "攻防宝石主要改变伤害曲线和阈值"
    if eid in SUPPORT_ITEMS:
        return "support_resource", "钥匙/血瓶属于缺口补充和批处理资源"
    return "support_resource", "普通可拾取资源"


def strategy_for_items(items: list[dict[str, Any]]) -> dict[str, Any]:
    role_rank = {"core_target": 3, "secondary_stat": 2, "support_resource": 1, "story_event": 0}
    best_role = "support_resource"
    reasons: list[str] = []
    core_ids: list[str] = []
    secondary_ids: list[str] = []
    support_ids: list[str] = []
    for item in items:
        role, reason = item_strategy_role(str(item["id"]))
        if role_rank[role] > role_rank[best_role]:
            best_role = role
        if reason not in reasons:
            reasons.append(reason)
        if role == "core_target":
            core_ids.append(str(item["id"]))
        elif role == "secondary_stat":
            secondary_ids.append(str(item["id"]))
        else:
            support_ids.append(str(item["id"]))
    priority = {"core_target": 100, "secondary_stat": 60, "support_resource": 30, "story_event": 10}[best_role]
    if core_ids and any(item_id in CORE_KEY_ITEMS for item_id in core_ids):
        priority = max(priority, 95)
    if core_ids and any(item_id in {"snow", "cross", "earthquake", "downFly"} for item_id in core_ids):
        priority = max(priority, 110)
    return {
        "role": best_role,
        "role_cn": STRATEGY_ROLE_CN[best_role],
        "priority": priority,
        "core_items": sorted(set(core_ids)),
        "secondary_items": sorted(set(secondary_ids)),
        "support_items": sorted(set(support_ids)),
        "reason": "；".join(reasons[:4]) if reasons else "-",
    }


def strategy_for_npc(resource_model: str, options: list[dict[str, Any]]) -> dict[str, Any]:
    labels = {str(option.get("label", "")) for option in options}
    if resource_model in {"shop", "merchant", "repeatable_merchant", "one_time_reward", "one_time_dynamic_reward"}:
        return {
            "role": "conversion_node",
            "role_cn": STRATEGY_ROLE_CN["conversion_node"],
            "priority": 90 if resource_model == "shop" else 80,
            "reason": "金币/钥匙/攻防/购买次数相关的显式状态转换",
            "labels": sorted(label for label in labels if label),
        }
    if resource_model == "one_time_tool":
        return {
            "role": "core_target",
            "role_cn": STRATEGY_ROLE_CN["core_target"],
            "priority": 90,
            "reason": "一次性关键工具，收益取决于使用时机",
            "labels": sorted(label for label in labels if label),
        }
    return {
        "role": "story_event",
        "role_cn": STRATEGY_ROLE_CN["story_event"],
        "priority": 10,
        "reason": "暂未解析为资源转换，路线依赖时需单独核对",
        "labels": sorted(label for label in labels if label),
    }


def add_gain(total: dict[str, int], gain: dict[str, int]) -> None:
    for key, value in gain.items():
        total[key] = total.get(key, 0) + value


def gain_text(gain: dict[str, int]) -> str:
    parts = []
    for key, label in (("hp", "HP"), ("atk", "ATK"), ("def", "DEF"), ("yk", "YK"), ("bk", "BK"), ("rk", "RK"), ("tools", "工具")):
        if gain.get(key):
            parts.append(f"{label}+{gain[key]}")
    return " ".join(parts) if parts else "-"


def build_floor(fid: str, snapshot: dict[str, Any], tiles: dict[int, Any], enemies: dict[str, Any]) -> dict[str, Any]:
    raw = read_json(ROOT / "data" / "maps" / f"mt{floor_no(fid)}_map.json")
    base_grid = raw.get("map") or raw.get("m")
    if not base_grid:
        raise ValueError(f"{fid} has no map grid")
    ratio = int(raw.get("ratio") or default_ratio(fid))
    grid = decode_grid(fid, base_grid, snapshot)
    cells: dict[tuple[int, int], dict[str, Any]] = {}
    for y, row in enumerate(grid):
        for x, tile in enumerate(row):
            if tile == 0:
                continue
            info = tiles.get(tile)
            if not info:
                if tile in EVENT_BLOCK_TILES:
                    cells[(x, y)] = {"tile": tile, "id": f"eventBlock:{tile}", "cls": "events", "kind": "eventBlock"}
                    continue
                cells[(x, y)] = {"tile": tile, "id": f"unknown:{tile}", "cls": "unknown", "kind": "unknown"}
                continue
            eid = info["id"]
            cls = info.get("cls", "")
            kind = classify(eid, cls, enemies)
            cell = {"tile": tile, "id": eid, "cls": cls, "kind": kind}
            if kind == "enemy":
                dmg = enemy_damage(enemies[eid], snapshot["hero"]["atk"], snapshot["hero"]["def"]) if eid in enemies else None
                cell["money"] = int(enemies.get(eid, {}).get("money", 0))
                cell["damage_now"] = dmg
                cell["zero_damage_now"] = dmg == 0
            cells[(x, y)] = cell
    return {"fid": fid, "ratio": ratio, "grid": grid, "cells": cells, "width": len(grid[0]), "height": len(grid)}


def passable_for_group(floor: dict[str, Any], pos: tuple[int, int], auto_wall: bool, has_snow: bool) -> bool:
    x, y = pos
    if x < 0 or y < 0 or x >= floor["width"] or y >= floor["height"]:
        return False
    cell = floor["cells"].get(pos)
    if cell is None:
        return True
    kind = cell["kind"]
    if kind in {"item", "terrain"}:
        return True
    if kind == "autoWall":
        return auto_wall
    if kind == "lava":
        return auto_wall and has_snow
    return False


def group_resources(floor: dict[str, Any], auto_wall: bool, has_snow: bool) -> list[dict[str, Any]]:
    item_positions = sorted(pos for pos, cell in floor["cells"].items() if cell["kind"] == "item")
    remaining = set(item_positions)
    groups: list[dict[str, Any]] = []

    while remaining:
        start = min(remaining, key=lambda p: (p[1], p[0]))
        queue: deque[tuple[int, int]] = deque([start])
        seen = {start}
        items: list[tuple[int, int]] = []
        auto_wall_openings: set[tuple[int, int]] = set()
        lava_edges: set[tuple[int, int]] = set()
        blockers: Counter[str] = Counter()

        while queue:
            pos = queue.popleft()
            cell = floor["cells"].get(pos)
            if cell and cell["kind"] == "item":
                items.append(pos)
            if cell and cell["kind"] == "autoWall":
                auto_wall_openings.add(pos)
            if cell and cell["kind"] == "lava":
                lava_edges.add(pos)
            x, y = pos
            for nxt in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if nxt in seen:
                    continue
                if passable_for_group(floor, nxt, auto_wall, has_snow):
                    seen.add(nxt)
                    queue.append(nxt)
                else:
                    blocker = floor["cells"].get(nxt)
                    if blocker:
                        blockers[blocker["kind"] + ":" + blocker["id"]] += 1

        remaining.difference_update(items)
        all_gain = {"hp": 0, "atk": 0, "def": 0, "yk": 0, "bk": 0, "rk": 0, "tools": 0}
        no_potion_gain = {"hp": 0, "atk": 0, "def": 0, "yk": 0, "bk": 0, "rk": 0, "tools": 0}
        records = []
        for x, y in sorted(items, key=lambda p: (p[1], p[0])):
            eid = floor["cells"][(x, y)]["id"]
            gain = item_gain(eid, floor["ratio"])
            add_gain(all_gain, gain)
            if eid not in POTIONS:
                add_gain(no_potion_gain, gain)
            records.append({
                "x": x,
                "y": y,
                "id": eid,
                "name": ITEM_CN.get(eid, eid),
                "is_potion": eid in POTIONS,
                "gain": gain,
            })
        xs = [p[0] for p in items]
        ys = [p[1] for p in items]
        groups.append({
            "floor": floor["fid"],
            "group_id": f"{floor['fid']}.g{len(groups)+1:02d}",
            "items": records,
            "item_count": len(records),
            "potion_count": sum(1 for row in records if row["is_potion"]),
            "gain_all_items": all_gain,
            "gain_no_potions": no_potion_gain,
            "strategy": strategy_for_items(records),
            "bbox": {"x1": min(xs), "y1": min(ys), "x2": max(xs), "y2": max(ys)},
            "auto_wall_cells_in_component": sorted([{"x": x, "y": y} for x, y in auto_wall_openings], key=lambda r: (r["y"], r["x"])),
            "lava_cells_in_component": sorted([{"x": x, "y": y} for x, y in lava_edges], key=lambda r: (r["y"], r["x"])),
            "adjacent_blocker_counts": dict(sorted(blockers.items())),
        })
    return groups


def floor_summary(floor: dict[str, Any], groups: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(cell["kind"] for cell in floor["cells"].values())
    enemy_ids = Counter(cell["id"] for cell in floor["cells"].values() if cell["kind"] == "enemy")
    item_ids = Counter(cell["id"] for cell in floor["cells"].values() if cell["kind"] == "item")
    zero_damage = sum(1 for cell in floor["cells"].values() if cell["kind"] == "enemy" and cell.get("zero_damage_now"))
    return {
        "floor": floor["fid"],
        "ratio": floor["ratio"],
        "counts": dict(sorted(counts.items())),
        "item_ids": dict(sorted(item_ids.items())),
        "enemy_ids": dict(sorted(enemy_ids.items())),
        "zero_damage_enemies_now": zero_damage,
        "group_count": len(groups),
        "group_item_count": sum(g["item_count"] for g in groups),
    }


def strategy_counts(cache: dict[str, Any]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for floor in cache["floors"]:
        for group in floor.get("groups", []):
            counts[group.get("strategy", {}).get("role", "unknown")] += 1
        for group in floor.get("event_groups", []):
            counts[group.get("strategy", {}).get("role", "unknown")] += 1
        for group in floor.get("npc_resource_groups", []):
            counts[group.get("strategy", {}).get("role", "unknown")] += 1
    return dict(sorted(counts.items()))


def validate(cache: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    total_items = 0
    grouped_items = 0
    for floor in cache["floors"]:
        summary = floor["summary"]
        item_count = int(summary["counts"].get("item", 0))
        group_items = int(summary["group_item_count"])
        total_items += item_count
        grouped_items += group_items
        if item_count != group_items:
            errors.append(f"{summary['floor']}: item_count={item_count} grouped={group_items}")
        seen: set[tuple[int, int]] = set()
        for group in floor["groups"]:
            for item in group["items"]:
                pos = (int(item["x"]), int(item["y"]))
                if pos in seen:
                    errors.append(f"{summary['floor']}: duplicate item position x{pos[0]}y{pos[1]}")
                seen.add(pos)
        if summary["group_count"] and not summary["group_item_count"]:
            errors.append(f"{summary['floor']}: nonzero groups but no grouped items")
    if total_items == 0:
        warnings.append("no remaining items detected")
    if cache.get("unknown_tiles"):
        warnings.append(f"unknown tiles present: {len(cache['unknown_tiles'])}; see unknown_tiles")
    event_group_count = sum(len(floor.get("event_groups", [])) for floor in cache["floors"])
    event_item_count = sum(
        group["item_count"]
        for floor in cache["floors"]
        for group in floor.get("event_groups", [])
    )
    npc_group_count = sum(len(floor.get("npc_resource_groups", [])) for floor in cache["floors"])
    event_change_count = sum(len(floor.get("event_map_changes", [])) for floor in cache["floors"])
    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "total_items": total_items,
        "grouped_items": grouped_items,
        "total_groups": sum(f["summary"]["group_count"] for f in cache["floors"]),
        "event_resource_groups": event_group_count,
        "event_resource_items": event_item_count,
        "npc_resource_groups": npc_group_count,
        "event_map_changes": event_change_count,
        "strategy_counts": strategy_counts(cache),
    }


def write_md(cache: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    state = cache["source"]["state"]
    auto = cache["source"]["auto"]
    lines = [
        "# 1号存档后续地图资源组缓存",
        "",
        f"- 目标：纯净版 TE 最高血量",
        f"- 起点：`{state['floor']} x{state['x']}y{state['y']} HP={state['hp']} ATK={state['atk']} DEF={state['def']} YK={state['yk']} BK={state['bk']} RK={state['rk']} G={state['gold']}`",
        f"- 自动设置：`battle={auto.get('battle')}`，`item={auto.get('item')}`，`wall={auto.get('wall')}`",
        f"- 缓存口径：当前 live snapshot 覆盖本地完整地图；假墙在自动开墙开启时视作 0 成本连通；未拿雪花前岩浆仍阻断。",
        f"- 校验：`ok={cache['validation']['ok']}`，items `{cache['validation']['grouped_items']}/{cache['validation']['total_items']}`，groups `{cache['validation']['total_groups']}`",
        "",
        "## 战略分层汇总",
        "",
        "| 层级 | 数量 |",
        "| --- | ---: |",
    ]
    for role, count in cache["validation"].get("strategy_counts", {}).items():
        lines.append(f"| {STRATEGY_ROLE_CN.get(role, role)} | {count} |")
    lines.extend([
        "",
        "## 楼层汇总",
        "",
        "| 楼层 | 资源组 | 物品 | 怪物 | 当前0伤怪 | 门 | 假墙 | 岩浆 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ])
    for floor in cache["floors"]:
        summary = floor["summary"]
        counts = summary["counts"]
        if not any(counts.get(k, 0) for k in ("item", "enemy", "door", "autoWall", "lava")) and summary["group_count"] == 0:
            continue
        lines.append(
            f"| {summary['floor']} | {summary['group_count']} | {counts.get('item', 0)} | "
            f"{counts.get('enemy', 0)} | {summary['zero_damage_enemies_now']} | {counts.get('door', 0)} | "
            f"{counts.get('autoWall', 0)} | {counts.get('lava', 0)} |"
        )
    lines.extend(["", "## 资源组预览", ""])
    for floor in cache["floors"]:
        if not floor["groups"]:
            continue
        lines.append(f"### {floor['summary']['floor']}")
        for group in floor["groups"][:8]:
            names = "，".join(f"x{item['x']}y{item['y']} {item['name']}" for item in group["items"])
            role = group.get("strategy", {}).get("role_cn", "-")
            lines.append(
                f"- `{group['group_id']}`（{role}）：{names}；全拿 `{gain_text(group['gain_all_items'])}`；"
                f"初始自动不拿血瓶 `{gain_text(group['gain_no_potions'])}`"
            )
        if len(floor["groups"]) > 8:
            lines.append(f"- ... 另有 {len(floor['groups']) - 8} 组见 JSON")
        lines.append("")
    event_floors = [floor for floor in cache["floors"] if floor.get("event_groups")]
    if event_floors:
        lines.extend(["## 事件后资源组", ""])
        for floor in event_floors:
            lines.append(f"### {floor['summary']['floor']}")
            for group in floor["event_groups"]:
                trigger = group.get("trigger_pos")
                trigger_text = f"x{trigger['x']}y{trigger['y']}" if trigger else "未知位置"
                names = "，".join(f"x{item['x']}y{item['y']} {item['name']}" for item in group["items"])
                conditions = "；".join(group.get("conditions") or ["-"])
                role = group.get("strategy", {}).get("role_cn", "-")
                lines.append(
                    f"- `{group['group_id']}`（{role}）：{group['trigger_label']} `{trigger_text}` 后生成 {names}；"
                    f"全拿 `{gain_text(group['gain_all_items'])}`；初始自动不拿血瓶 `{gain_text(group['gain_no_potions'])}`；条件 `{conditions}`"
                )
            lines.append("")
    npc_floors = [floor for floor in cache["floors"] if floor.get("npc_resource_groups")]
    if npc_floors:
        lines.extend(["## NPC / 商店资源点", ""])
        for floor in npc_floors:
            lines.append(f"### {floor['summary']['floor']}")
            for group in floor["npc_resource_groups"]:
                options = "；".join(option.get("label", "?") for option in group.get("options", [])) or "-"
                note = group.get("note") or "-"
                role = group.get("strategy", {}).get("role_cn", "-")
                visible = "当前可见" if group.get("visible_now") else "事件/条件后"
                lines.append(
                    f"- `{group['group_id']}`（{role}）：x{group['x']}y{group['y']} {group['name']}，"
                    f"`{group['resource_model']}`，{visible}；选项 `{options}`；{note}"
                )
            lines.append("")
    change_floors = [floor for floor in cache["floors"] if floor.get("event_map_changes")]
    if change_floors:
        lines.extend(["## 事件地图变化", ""])
        for floor in change_floors:
            lines.append(f"### {floor['summary']['floor']}")
            for group in floor["event_map_changes"]:
                trigger = group.get("trigger_pos")
                trigger_text = f"x{trigger['x']}y{trigger['y']}" if trigger else "未知位置"
                pieces = []
                for change in group["changes"]:
                    locs = "，".join(f"x{loc['x']}y{loc['y']}" for loc in change.get("locs", []))
                    detail = change.get("id") or change.get("number") or ""
                    pieces.append(f"{change['action']} {detail} {locs}".strip())
                lines.append(
                    f"- `{group['change_id']}`：{group['trigger_label']} `{trigger_text}` 后 "
                    + "；".join(pieces)
                )
            lines.append("")
    if cache["validation"]["errors"]:
        lines.extend(["## 校验错误", ""])
        lines.extend(f"- {err}" for err in cache["validation"]["errors"])
    if cache["validation"]["warnings"]:
        lines.extend(["## 校验警告", ""])
        lines.extend(f"- {warn}" for warn in cache["validation"]["warnings"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_cache(snapshot_path: Path) -> dict[str, Any]:
    snapshot = read_json(snapshot_path)
    tiles = load_tiles()
    enemies = load_enemies()
    flags = snapshot["hero"].get("flags", {})
    auto = flags.get("__auto__", {}) or {}
    auto_wall = bool(auto.get("wall"))
    tools = snapshot["hero"].get("tools", {}) or {}
    constants = snapshot["hero"].get("constants", {}) or {}
    has_snow = bool(tools.get("snow") or constants.get("snow"))
    visited = sorted((flags.get("__visited__", {}) or {}).keys(), key=floor_no)

    floors = []
    aggregate = Counter()
    unknown_tiles: list[dict[str, int | str]] = []
    for n in range(1, 51):
        fid = f"MT{n}"
        raw = read_json(ROOT / "data" / "maps" / f"mt{n}_map.json")
        floor = build_floor(fid, snapshot, tiles, enemies)
        for (x, y), cell in sorted(floor["cells"].items(), key=lambda kv: (kv[0][1], kv[0][0])):
            if cell["kind"] == "unknown":
                unknown_tiles.append({"floor": fid, "x": x, "y": y, "tile": int(cell["tile"])})
        groups = group_resources(floor, auto_wall=auto_wall, has_snow=has_snow)
        events = event_resource_groups(fid, raw, tiles=tiles, flags=flags, ratio=floor["ratio"])
        changes = event_map_changes(fid, raw, tiles=tiles, flags=flags)
        npcs = npc_resource_groups(fid, floor, raw)
        summary = floor_summary(floor, groups)
        aggregate.update(summary["counts"])
        floors.append({
            "floor": fid,
            "visited": fid in visited,
            "summary": summary,
            "groups": groups,
            "event_groups": events,
            "event_map_changes": changes,
            "npc_resource_groups": npcs,
        })

    state = {
        "floor": snapshot["floorId"],
        "x": snapshot["hero"]["x"],
        "y": snapshot["hero"]["y"],
        "hp": snapshot["hero"]["hp"],
        "atk": snapshot["hero"]["atk"],
        "def": snapshot["hero"]["def"],
        "yk": snapshot["hero"]["yk"],
        "bk": snapshot["hero"]["bk"],
        "rk": snapshot["hero"]["rk"],
        "gold": snapshot["hero"]["money"],
    }
    cache = {
        "schema": "mota.live_resource_group_cache.v1",
        "source": {
            "snapshot": str(snapshot_path.relative_to(ROOT)),
            "exportedAt": snapshot.get("exportedAt"),
            "target": "pure_TE_max_hp",
            "state": state,
            "auto": auto,
            "feature_flag": flags.get("开启特性", 0),
            "extra_feature_flag": flags.get("额外功能开关", None),
            "visited_floors": visited,
            "has_snow": has_snow,
        },
        "rules": {
            "auto_wall_fake_walls_passable": auto_wall,
            "lava_passable_requires_snow": True,
            "initial_auto_item_mode": auto.get("item"),
            "potion_items_withheld_when_item_nopotion": sorted(POTIONS),
        },
        "aggregate_counts": dict(sorted(aggregate.items())),
        "unknown_tiles": unknown_tiles,
        "floors": floors,
    }
    cache["validation"] = validate(cache)
    return cache


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", default=str(DEFAULT_SNAPSHOT))
    parser.add_argument("--out-json", default=str(DEFAULT_OUT_JSON))
    parser.add_argument("--out-md", default=str(DEFAULT_OUT_MD))
    args = parser.parse_args()

    snapshot_path = Path(args.snapshot).resolve()
    cache = build_cache(snapshot_path)
    out_json = Path(args.out_json)
    out_md = Path(args.out_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    write_md(cache, out_md)

    print(f"ok={cache['validation']['ok']}")
    print(f"snapshot={snapshot_path}")
    print(f"json={out_json}")
    print(f"md={out_md}")
    print(
        "state="
        f"{cache['source']['state']['floor']} x{cache['source']['state']['x']}y{cache['source']['state']['y']} "
        f"HP={cache['source']['state']['hp']} ATK={cache['source']['state']['atk']} DEF={cache['source']['state']['def']}"
    )
    print(f"groups={cache['validation']['total_groups']} items={cache['validation']['grouped_items']}/{cache['validation']['total_items']}")
    print(
        "event_groups="
        f"{cache['validation']['event_resource_groups']} event_items={cache['validation']['event_resource_items']}"
    )
    print(f"event_map_changes={cache['validation']['event_map_changes']}")
    print(f"npc_resource_groups={cache['validation']['npc_resource_groups']}")
    if cache["validation"]["errors"]:
        print("errors:")
        for err in cache["validation"]["errors"]:
            print(f"- {err}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
