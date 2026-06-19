#!/usr/bin/env python3
"""Replay the supplied zone-2 guide route from post-MT10-boss states.

This is intentionally a hand-route replay, not a search.  The 11F-20F maps
contain several event-only mechanics, so this script records those rules in one
place and emits a stable walk artifact that later searches can compare against.
"""

from __future__ import annotations

import ast
import heapq
import json
import os
import re
import sys
from collections import deque
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Iterable


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.chdir(ROOT)

from src.solver.full_search import FLOOR_13_COLLECTED  # noqa: E402
from scripts import fixed_shield_strategy as fixed  # noqa: E402
from scripts import replay_user_post9_route as guide10  # noqa: E402


STATE_KEYS = ("hp", "atk", "def", "yk", "bk", "rk", "gold")
POST_BOSS_SUPPLY = [
    ("MT10", 1, 3, "redGem"),
    ("MT10", 2, 3, "redGem"),
    ("MT10", 3, 3, "redGem"),
    ("MT10", 9, 3, "blueGem"),
    ("MT10", 10, 3, "blueGem"),
    ("MT10", 11, 3, "blueGem"),
    ("MT10", 1, 4, "bluePotion"),
    ("MT10", 2, 4, "bluePotion"),
    ("MT10", 3, 4, "bluePotion"),
    ("MT10", 9, 4, "yellowKey"),
    ("MT10", 10, 4, "yellowKey"),
    ("MT10", 11, 4, "yellowKey"),
]

CROSS_TARGETS = {"zombie", "zombieKnight", "vampire"}
MT15_BARRIER = {(5, 4), (5, 5), (5, 6), (6, 4), (7, 4), (7, 5), (7, 6)}
MT14_RED_KEY_GUARDS = {(1, 1), (3, 1), (2, 2)}
MT8_RED_KEY_GUARDS = {(9, 5), (11, 5)}
MT20_VAMPIRE_MERGE_BATS = {(5, 5), (6, 5), (7, 5), (5, 6), (7, 6), (5, 7), (6, 7), (7, 7)}
MT17_SPECIAL_PAIRS = {
    frozenset({(1, 8), (3, 8)}): (2, 7),
    frozenset({(1, 5), (3, 5)}): (2, 4),
    frozenset({(9, 8), (11, 8)}): (10, 7),
    frozenset({(9, 5), (11, 5)}): (10, 4),
}
MT11_RED_PRIESTS = {(1, 5), (3, 5)}


ITEM_CN = {
    "yellowDoor": "黄门",
    "blueDoor": "蓝门",
    "redDoor": "红门",
    "specialDoor": "机关门",
    "fakeWall": "暗墙",
    "fakeWall2": "暗墙",
    "yellowKey": "黄钥匙",
    "blueKey": "蓝钥匙",
    "redKey": "红钥匙",
    "redPotion": "红血瓶",
    "bluePotion": "蓝血瓶",
    "redGem": "红宝石",
    "blueGem": "蓝宝石",
    "sword2": "银剑",
    "shield2": "银盾",
    "sword5": "神圣剑",
    "pickaxe": "镐",
    "cross": "十字架",
    "superPotion": "圣水",
    "fly": "楼层传送器",
    "greenSlime": "绿头怪",
    "redSlime": "红头怪",
    "bat": "小蝙蝠",
    "bigBat": "大蝙蝠",
    "skeleton": "骷髅人",
    "skeletonSoldier": "骷髅士兵",
    "blackSlime": "小黑",
    "redPriest": "高级法师",
    "bluePriest": "初级法师",
    "zombie": "兽人",
    "zombieKnight": "兽人武士",
    "rock": "石头人",
    "slimeMan": "幽灵",
    "yellowGuard": "黄卫兵",
    "octopus": "大章鱼",
    "vampire": "吸血鬼",
    "oldman": "老人",
    "thief": "小偷",
    "trader": "商人",
    "blueShop": "蓝商店",
}


@dataclass(frozen=True)
class Block:
    kind: str
    eid: str


@dataclass
class Floor:
    fid: str
    width: int
    height: int
    ratio: int
    grid: list[list[int]]
    blocks: dict[tuple[int, int], Block]


def extract_json_array(text: str, key: str) -> Any:
    marker = f'"{key}"'
    start = text.index(marker)
    start = text.index("[", start)
    depth = 0
    in_string = False
    escape = False
    for idx in range(start, len(text)):
        ch = text[idx]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                return ast.literal_eval(text[start : idx + 1])
    raise ValueError(f"cannot extract array {key}")


def load_raw_map(path: str) -> dict[str, Any]:
    text = open(path, encoding="utf-8").read()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        grid = extract_json_array(text, "map")
        return {
            "width": len(grid[0]),
            "height": len(grid),
            "map": grid,
            "_partial": True,
        }


def load_tile_mapping() -> dict[int, dict[str, Any]]:
    raw = json.load(open(os.path.join("data", "maps", "tile_mapping.json"), encoding="utf-8"))
    return {int(k): v for k, v in raw["tiles"].items()}


def load_enemy_stats() -> dict[str, dict[str, Any]]:
    raw = json.load(open(os.path.join("data", "maps", "enemy_stats.json"), encoding="utf-8"))
    return raw["enemys"]


def classify_from_id(eid: str, cls: str, enemies: dict[str, Any]) -> str | None:
    if eid in {"yellowWall", "unbreakableWall", "lava", "whiteWall2", "none"}:
        return None
    if eid in enemies:
        return "enemy"
    if eid in {"yellowDoor", "blueDoor", "redDoor", "specialDoor"}:
        return "door"
    if cls == "items" or eid in {
        "yellowKey",
        "blueKey",
        "redKey",
        "redPotion",
        "bluePotion",
        "redGem",
        "blueGem",
        "greenGem",
        "sword1",
        "shield1",
        "sword2",
        "shield2",
        "sword5",
        "pickaxe",
        "cross",
        "fly",
    }:
        return "item"
    if eid in {"upFloor", "downFloor", "fakeWall", "fakeWall2"}:
        return "terrain"
    if eid in {"trader", "oldman", "thief", "blueShop", "specialTrader", "king"} or cls == "npcs":
        return "npc"
    if cls in {"terrains", "animates"}:
        return "terrain"
    return None


def build_floor(fid: str, raw: dict[str, Any], tiles: dict[int, dict[str, Any]], enemies: dict[str, Any]) -> Floor:
    grid = raw.get("map") or raw.get("m")
    width = raw.get("width") or raw.get("W") or len(grid[0])
    height = raw.get("height") or raw.get("H") or len(grid)
    floor_no = int(fid[2:]) if fid.startswith("MT") and fid[2:].isdigit() else 0
    ratio = int(raw.get("ratio") or (2 if 11 <= floor_no <= 20 else 1))
    blocks: dict[tuple[int, int], Block] = {}

    if raw.get("bl"):
        for item in raw["bl"]:
            if not isinstance(item, dict):
                x, y, _t, eid, _np = item
                cls = ""
            else:
                x, y, eid = item["x"], item["y"], item["id"]
                cls = item.get("cls", "")
            kind = classify_from_id(eid, cls, enemies)
            if kind:
                blocks[(x, y)] = Block(kind, eid)
    else:
        for y, row in enumerate(grid):
            for x, tile in enumerate(row):
                if tile in {0, 1, 5, 17, 321, 330}:
                    continue
                info = tiles.get(tile)
                if not info:
                    continue
                eid = info["id"]
                kind = classify_from_id(eid, info.get("cls", ""), enemies)
                if kind:
                    blocks[(x, y)] = Block(kind, eid)

    return Floor(fid=fid, width=width, height=height, ratio=ratio, grid=grid, blocks=blocks)


def load_floors() -> tuple[dict[str, Floor], dict[str, dict[str, Any]]]:
    tiles = load_tile_mapping()
    enemies = load_enemy_stats()
    floors: dict[str, Floor] = {}
    for floor in range(1, 21):
        fid = f"MT{floor}"
        name = f"mt{floor}_map.json"
        if fid == "MT10":
            name = "mt10_post_boss_map.json"
        path = os.path.join("data", "maps", name)
        if not os.path.exists(path):
            continue
        raw = load_raw_map(path)
        floors[fid] = build_floor(fid, raw, tiles, enemies)
    return floors, enemies


def state_text(state: dict[str, Any], include_pos: bool = False) -> str:
    base = (
        f"HP={state['hp']} ATK={state['atk']} DEF={state['def']} "
        f"YK={state['yk']} BK={state['bk']} RK={state['rk']} G={state['gold']}"
    )
    if include_pos:
        base += f" {state['floor']} x{state['x']}y{state['y']}"
    return base


def state_delta(before: dict[str, Any], after: dict[str, Any]) -> str:
    labels = {"hp": "HP", "atk": "ATK", "def": "DEF", "yk": "YK", "bk": "BK", "rk": "RK", "gold": "G"}
    out = []
    for key in STATE_KEYS:
        if before.get(key) != after.get(key):
            out.append(f"{labels[key]} {before.get(key)}->{after.get(key)}")
    return ", ".join(out)


class Replay:
    def __init__(
        self,
        label: str,
        state: dict[str, Any],
        floors: dict[str, Floor],
        enemies: dict[str, dict[str, Any]],
        cleared: dict[str, set[tuple[int, int]]],
        validate_paths: bool = False,
    ) -> None:
        self.label = label
        self.state = deepcopy(state)
        self.floors = floors
        self.enemies = enemies
        self.cleared = {fid: set(pos) for fid, pos in cleared.items()}
        self.validate_paths = validate_paths
        self.steps: list[dict[str, Any]] = []
        self.segments: list[dict[str, Any]] = []
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self._segment_start: dict[str, Any] | None = None
        self._segment_name = ""

    def snapshot(self) -> dict[str, Any]:
        out = {key: self.state[key] for key in STATE_KEYS}
        out.update(
            floor=self.state["floor"],
            x=self.state["x"],
            y=self.state["y"],
            dmg=self.state["dmg"],
            yd=self.state["yd"],
            bd=self.state["bd"],
            rd=self.state["rd"],
            cross=bool(self.state.get("cross")),
            pickaxe=bool(self.state.get("pickaxe")),
            superPotion=bool(self.state.get("superPotion")),
        )
        return out

    def begin_segment(self, name: str) -> None:
        if self._segment_start is not None:
            self.end_segment()
        self._segment_name = name
        self._segment_start = self.snapshot()

    def end_segment(self) -> None:
        if self._segment_start is None:
            return
        start = self._segment_start
        end = self.snapshot()
        self.segments.append(
            {
                "name": self._segment_name,
                "start": start,
                "end": end,
                "dmg": end["dmg"] - start["dmg"],
                "doors": {
                    "yellow": end["yd"] - start["yd"],
                    "blue": end["bd"] - start["bd"],
                    "red": end["rd"] - start["rd"],
                },
            }
        )
        self._segment_start = None

    def warn(self, msg: str) -> None:
        self.warnings.append(f"{self._segment_name}: {msg}")

    def error(self, msg: str) -> None:
        self.errors.append(f"{self._segment_name}: {msg}")

    def record(self, action: str, pos: tuple[int, int] | None = None, eid: str | None = None, before: dict[str, Any] | None = None, note: str = "") -> None:
        after = self.snapshot()
        self.steps.append(
            {
                "segment": self._segment_name,
                "floor": self.state["floor"],
                "pos": list(pos or (self.state["x"], self.state["y"])),
                "action": action,
                "eid": eid,
                "before": before,
                "after": after,
                "note": note,
            }
        )

    def is_wall(self, fid: str, pos: tuple[int, int]) -> bool:
        x, y = pos
        floor = self.floors[fid]
        if x < 0 or y < 0 or x >= floor.width or y >= floor.height:
            return True
        if x == 0 or y == 0 or x == floor.width - 1 or y == floor.height - 1:
            return True
        if pos in self.cleared.get(fid, set()):
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

    def path(self, fid: str, target: tuple[int, int]) -> list[tuple[int, int]] | None:
        start = (self.state["x"], self.state["y"])
        if self.state["floor"] != fid:
            self.error(f"current floor {self.state['floor']} != target floor {fid}")
            return None
        heap: list[tuple[int, int, tuple[int, int]]] = [(0, 0, start)]
        parent: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
        best = {start: 0}
        seq = 0

        def step_cost(pos: tuple[int, int]) -> int:
            if pos in self.cleared.get(fid, set()):
                return 1
            block = self.floors[fid].blocks.get(pos)
            if not block:
                return 1
            if block.kind == "item":
                return 3
            if block.kind == "terrain":
                return 5
            if block.kind == "npc":
                return 50
            if block.kind == "door":
                return 80
            if block.kind == "enemy":
                dmg = self.damage_for(block.eid)
                if dmg == float("inf"):
                    return 10000
                return 100 + int(dmg)
            return 10

        while heap:
            cost, _seq, cur = heapq.heappop(heap)
            if cost != best.get(cur):
                continue
            if cur == target:
                break
            cx, cy = cur
            for nxt in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                if nxt != target and self.is_wall(fid, nxt):
                    continue
                # Do not route through uncleared special doors, even as target,
                # unless an event has already removed it from blocks.
                block = self.floors[fid].blocks.get(nxt)
                if nxt != target and block and block.eid == "specialDoor" and nxt not in self.cleared.get(fid, set()):
                    continue
                new_cost = cost + step_cost(nxt)
                if new_cost >= best.get(nxt, 10**9):
                    continue
                best[nxt] = new_cost
                parent[nxt] = cur
                seq += 1
                heapq.heappush(heap, (new_cost, seq, nxt))
        if target not in parent:
            return None
        out = []
        cur: tuple[int, int] | None = target
        while cur is not None:
            out.append(cur)
            cur = parent[cur]
        out.reverse()
        return out

    def go_to(self, fid: str, x: int, y: int, note: str = "") -> None:
        target = (x, y)
        path = self.path(fid, target)
        if not path:
            self.error(f"no path to {fid} x{x}y{y}")
            return
        for pos in path[1:]:
            self.state["x"], self.state["y"] = pos
            block = self.floors[fid].blocks.get(pos)
            if block and pos not in self.cleared.get(fid, set()):
                self.apply_block(fid, pos, block, note=note if pos == target else "")
            elif pos == target and note:
                before = self.snapshot()
                self.record("到达", pos, None, before, note)

    def strict_path_exists(self, fid: str, target: tuple[int, int]) -> bool:
        if self.state["floor"] != fid:
            return True
        start = (self.state["x"], self.state["y"])
        if start == target:
            return True
        floor = self.floors[fid]

        def passable(pos: tuple[int, int]) -> bool:
            if pos == target:
                return not self.is_wall(fid, pos) or pos in self.cleared.get(fid, set())
            if self.is_wall(fid, pos):
                return False
            if pos in self.cleared.get(fid, set()):
                return True
            block = floor.blocks.get(pos)
            if not block:
                return True
            return block.kind == "terrain" and block.eid in {"upFloor", "downFloor"}

        queue = deque([start])
        seen = {start}
        while queue:
            cx, cy = queue.popleft()
            for nxt in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                if nxt in seen or not passable(nxt):
                    continue
                if nxt == target:
                    return True
                seen.add(nxt)
                queue.append(nxt)
        return False

    def act(self, fid: str, x: int, y: int, note: str = "") -> None:
        """Apply exactly one route action at a known coordinate.

        The guide route is hand-authored and often uses the floor transporter,
        so this avoids letting shortest-path routing consume unintended doors or
        resources while still applying the real block effect.
        """
        pos = (x, y)
        before = self.snapshot()
        if self.validate_paths and self.state["floor"] == fid and not self.strict_path_exists(fid, pos):
            self.error(
                f"strict path blocked from x{self.state['x']}y{self.state['y']} "
                f"to {fid} x{x}y{y}"
            )
        self.state["floor"] = fid
        self.state["x"] = x
        self.state["y"] = y
        if pos in self.cleared.get(fid, set()):
            self.record("已清理", pos, None, before, note)
            return
        block = self.floors[fid].blocks.get(pos)
        if not block:
            self.record("经过", pos, None, before, note)
            return
        self.apply_block(fid, pos, block, note=note)

    def teleport(self, fid: str, x: int, y: int, note: str = "楼层传送") -> None:
        before = self.snapshot()
        self.state["floor"] = fid
        self.state["x"] = x
        self.state["y"] = y
        self.record("传送", (x, y), None, before, note)

    def transition(self, fid: str, x: int, y: int, note: str = "上下楼") -> None:
        before = self.snapshot()
        self.state["floor"] = fid
        self.state["x"] = x
        self.state["y"] = y
        self.record("换层", (x, y), None, before, note)

    def damage_for(self, eid: str) -> int | float:
        enemy = self.enemies[eid]
        atk = self.state["atk"] * (2 if self.state.get("cross") and eid in CROSS_TARGETS else 1)
        damage_per_hit = atk - enemy["def"]
        if damage_per_hit <= 0:
            return float("inf")
        rounds = -(-enemy["hp"] // damage_per_hit)
        return (rounds - 1) * max(0, enemy["atk"] - self.state["def"])

    def apply_block(self, fid: str, pos: tuple[int, int], block: Block, note: str = "") -> None:
        before = self.snapshot()
        eid = block.eid
        action = "通过"
        if block.kind == "enemy":
            dmg = self.damage_for(eid)
            if dmg == float("inf"):
                self.error(f"cannot damage {eid} at {fid} x{pos[0]}y{pos[1]}")
                dmg = 0
            if self.state["hp"] - dmg <= 0:
                self.error(f"death on {eid} at {fid} x{pos[0]}y{pos[1]} damage={dmg}")
            self.state["hp"] -= int(dmg)
            self.state["dmg"] += int(dmg)
            self.state["gold"] += int(self.enemies[eid].get("money", 0))
            action = "击杀"
        elif block.kind == "door":
            action = "开门"
            if eid == "yellowDoor":
                if self.state["yk"] <= 0:
                    self.error(f"no yellow key at {fid} x{pos[0]}y{pos[1]}")
                self.state["yk"] -= 1
                self.state["yd"] += 1
            elif eid == "blueDoor":
                if self.state["bk"] <= 0:
                    self.error(f"no blue key at {fid} x{pos[0]}y{pos[1]}")
                self.state["bk"] -= 1
                self.state["bd"] += 1
            elif eid == "redDoor":
                if self.state["rk"] <= 0:
                    self.error(f"no red key at {fid} x{pos[0]}y{pos[1]}")
                self.state["rk"] -= 1
                self.state["rd"] += 1
            elif eid == "specialDoor":
                self.error(f"closed special door at {fid} x{pos[0]}y{pos[1]}")
        elif block.kind == "item":
            action = "拾取"
            self.apply_item(eid)
        elif block.kind == "terrain":
            action = "通过"
        elif block.kind == "npc":
            action = "对话"
        self.record(action, pos, eid, before, note)
        self.cleared.setdefault(fid, set()).add(pos)
        self.after_action(fid, pos, block)

    def apply_item(self, eid: str) -> None:
        ratio = self.floors[self.state["floor"]].ratio
        if eid == "yellowKey":
            self.state["yk"] += 1
        elif eid == "blueKey":
            self.state["bk"] += 1
        elif eid == "redKey":
            self.state["rk"] += 1
        elif eid == "redPotion":
            self.state["hp"] += 50 * ratio
        elif eid == "bluePotion":
            self.state["hp"] += 200 * ratio
        elif eid == "redGem":
            self.state["atk"] += 1 * ratio
        elif eid == "blueGem":
            self.state["def"] += 1 * ratio
        elif eid == "sword2":
            self.state["atk"] += 20
        elif eid == "shield2":
            self.state["def"] += 20
        elif eid == "sword5":
            self.state["atk"] += 100
        elif eid == "pickaxe":
            self.state["pickaxe"] = True
        elif eid == "cross":
            self.state["cross"] = True
        elif eid == "fly":
            self.state["fly"] = True

    def after_action(self, fid: str, pos: tuple[int, int], block: Block) -> None:
        if fid == "MT11" and block.eid == "redPriest":
            if MT11_RED_PRIESTS <= self.cleared.get(fid, set()):
                self.clear_special(fid, (2, 4), "两高级法师开盾门")
        if fid == "MT17" and block.kind == "enemy" and any(pos in pair for pair in MT17_SPECIAL_PAIRS):
            seen = self.cleared.get(fid, set())
            for pair, door in MT17_SPECIAL_PAIRS.items():
                if pair <= seen:
                    self.clear_special(fid, door, "两黄卫兵开机关门")
        if fid == "MT8" and block.eid == "yellowGuard":
            if MT8_RED_KEY_GUARDS <= self.cleared.get(fid, set()):
                self.clear_special(fid, (10, 4), "8F 两黄卫兵开红钥匙区机关门")
        if fid == "MT15" and block.eid == "octopus":
            for p in MT15_BARRIER:
                self.cleared.setdefault(fid, set()).add(p)
            self.clear_special(fid, (6, 3), "大章鱼后开门")
        if fid == "MT14" and block.eid == "zombieKnight":
            if MT14_RED_KEY_GUARDS <= self.cleared.get(fid, set()) and not self.state.get("mt14_red_key_reward"):
                before = self.snapshot()
                self.state["rk"] += 1
                self.state["mt14_red_key_reward"] = True
                self.record("事件奖励", pos, "redKey", before, "14F 三兽人武士掉红钥匙")
        if fid == "MT19" and pos == (6, 3) and block.eid in {"fakeWall2", "cross"}:
            # The real event replaces the opened center wall/door with cross.
            if not self.state.get("cross"):
                self.floors[fid].blocks[(6, 3)] = Block("item", "cross")
                self.cleared[fid].discard((6, 3))

    def clear_special(self, fid: str, pos: tuple[int, int], note: str) -> None:
        if pos not in self.cleared.get(fid, set()):
            before = self.snapshot()
            self.cleared.setdefault(fid, set()).add(pos)
            self.record("事件开门", pos, "specialDoor", before, note)

    def event_thief10(self) -> None:
        before = self.snapshot()
        self.record("事件", (6, 9), "thief", before, "10F 小偷事件，开放 11F 楼梯")

    def event_thief15(self) -> None:
        before = self.snapshot()
        self.cleared.setdefault("MT15", set()).add((8, 1))
        self.record("事件", (9, 1), "thief", before, "15F 小偷开右上墙")

    def event_vampire_trigger(self) -> None:
        self.state["floor"] = "MT20"
        self.state["x"] = 6
        self.state["y"] = 8
        before = self.snapshot()
        for pos in MT20_VAMPIRE_MERGE_BATS:
            self.cleared.setdefault("MT20", set()).add(pos)
            self.floors["MT20"].blocks.pop(pos, None)
        self.floors["MT20"].blocks[(6, 6)] = Block("enemy", "vampire")
        self.record("事件", (6, 8), "vampire", before, "20F 触发吸血鬼")

    def event_super_potion16(self) -> None:
        before = self.snapshot()
        self.state["superPotion"] = True
        self.cleared.setdefault("MT16", set()).add((11, 11))
        self.record("事件", (11, 11), "superPotion", before, "16F 老人给圣水")

    def shop12_attack_three(self) -> None:
        self.shop12_buys(["atk", "atk", "atk"])

    def shop12_buys(self, choices: list[str]) -> None:
        costs = [20, 40, 80, 140, 220, 320, 440, 580, 740]
        for idx, choice in enumerate(choices, 1):
            cost = costs[idx - 1]
            before = self.snapshot()
            if self.state["gold"] < cost:
                self.error(f"not enough gold for 12F shop #{idx}: need {cost}, have {self.state['gold']}")
            self.state["gold"] -= cost
            if choice == "atk":
                self.state["atk"] += 4
                eid = "blueShop:attack"
                note = f"12F 第 {idx} 次买攻击，花费 {cost}G"
            elif choice == "def":
                self.state["def"] += 8
                eid = "blueShop:defense"
                note = f"12F 第 {idx} 次买防御，花费 {cost}G"
            elif choice == "hp":
                self.state["hp"] += idx * 100
                eid = "blueShop:hp"
                note = f"12F 第 {idx} 次买生命，花费 {cost}G"
            else:
                self.error(f"unknown 12F shop choice: {choice}")
                eid = f"blueShop:{choice}"
                note = f"12F 第 {idx} 次未知购买 {choice}，花费 {cost}G"
            self.record("商店", (6, 9), eid, before, note)

    def merchant(self, fid: str, pos: tuple[int, int], spend: int, gain: dict[str, int], note: str) -> None:
        if self.validate_paths and self.state["floor"] == fid and not self.strict_path_exists(fid, pos):
            self.error(
                f"strict path blocked from x{self.state['x']}y{self.state['y']} "
                f"to merchant {fid} x{pos[0]}y{pos[1]}"
            )
        self.state["floor"] = fid
        self.state["x"], self.state["y"] = pos
        before = self.snapshot()
        if pos in self.cleared.get(fid, set()):
            self.record("商人", pos, "trader", before, f"{note}（已使用，跳过）")
            return
        if self.state["gold"] < spend:
            self.error(f"not enough gold for merchant {fid} x{pos[0]}y{pos[1]}: need {spend}, have {self.state['gold']}")
        self.state["gold"] -= spend
        for key, value in gain.items():
            self.state[key] += value
        self.cleared.setdefault(fid, set()).add(pos)
        self.record("商人", pos, "trader", before, note)

    def use_super_potion(self) -> None:
        before = self.snapshot()
        if not self.state.get("superPotion"):
            self.warn("superPotion not in inventory")
        hp_gain = int(0.74 * (self.state["atk"] + self.state["def"]) + 0.5) * 10
        self.state["hp"] += hp_gain
        self.state["superPotion"] = False
        self.record("使用道具", (self.state["x"], self.state["y"]), "superPotion", before, f"圣水 +{hp_gain}HP")


def add_positions(dst: dict[str, set[tuple[int, int]]], fid: str, positions: Iterable[tuple[int, int]]) -> None:
    dst.setdefault(fid, set()).update(positions)


def normalize_event_clears(collected: dict[str, set[tuple[int, int]]]) -> None:
    if MT8_RED_KEY_GUARDS <= collected.get("MT8", set()):
        collected.setdefault("MT8", set()).add((10, 4))
    if MT14_RED_KEY_GUARDS <= collected.get("MT14", set()):
        collected.setdefault("MT14", set()).add((3, 1))
    seen17 = collected.get("MT17", set())
    for pair, door in MT17_SPECIAL_PAIRS.items():
        if pair <= seen17:
            collected.setdefault("MT17", set()).add(door)
    if MT11_RED_PRIESTS <= collected.get("MT11", set()):
        collected.setdefault("MT11", set()).add((2, 4))


def guide_start_collected() -> dict[str, set[tuple[int, int]]]:
    collected = {fid: set(pos) for fid, pos in FLOOR_13_COLLECTED.items()}
    prefix = fixed.replay_route()
    for fid, positions in prefix["collected"].items():
        add_positions(collected, fid, ((p["x"], p["y"]) for p in positions))
    replay = guide10.replay()
    floors, _enemies = load_floors()
    for step in replay["steps"]:
        fid = step["floor"]
        pos = tuple(step["pos"])
        block = floors.get(fid).blocks.get(pos) if fid in floors else None
        if block and block.kind in {"enemy", "door", "item", "terrain"}:
            collected.setdefault(fid, set()).add(pos)
    for fid, x, y, _eid in POST_BOSS_SUPPLY:
        collected.setdefault(fid, set()).add((x, y))
    normalize_event_clears(collected)
    return collected


def best_start_collected() -> dict[str, set[tuple[int, int]]]:
    collected = {fid: set(pos) for fid, pos in FLOOR_13_COLLECTED.items()}
    floors, _enemies = load_floors()
    text = open(os.path.join("best", "current_best_boss_walk.md"), encoding="utf-8").read()
    for fid_num, x, y, action in re.findall(r"- MT(\d+) x(\d+)y(\d+) (kill|take|open|pass)", text):
        fid = f"MT{int(fid_num)}"
        pos = (int(x), int(y))
        block = floors.get(fid).blocks.get(pos) if fid in floors else None
        if block and (action != "pass" or block.kind == "terrain"):
            collected.setdefault(fid, set()).add(pos)
    for fid, x, y, _eid in POST_BOSS_SUPPLY:
        collected.setdefault(fid, set()).add((x, y))
    normalize_event_clears(collected)
    return collected


def apply_post_boss_supply_to_state(state: dict[str, Any]) -> None:
    for _fid, _x, _y, eid in POST_BOSS_SUPPLY:
        if eid == "redGem":
            state["atk"] += 1
        elif eid == "blueGem":
            state["def"] += 1
        elif eid == "bluePotion":
            state["hp"] += 200
        elif eid == "yellowKey":
            state["yk"] += 1


def scenario_states() -> list[tuple[str, dict[str, Any], dict[str, set[tuple[int, int]]]]]:
    guide_state = {
        "floor": "MT10",
        "x": 6,
        "y": 2,
        "hp": 25,
        "atk": 27,
        "def": 27,
        "yk": 0,
        "bk": 0,
        "rk": 0,
        "gold": 304,
        "dmg": 2601,
        "yd": 40,
        "bd": 2,
        "rd": 1,
        "cross": False,
        "pickaxe": False,
        "superPotion": False,
    }
    best_state = {
        "floor": "MT10",
        "x": 6,
        "y": 2,
        "hp": 122,
        "atk": 27,
        "def": 27,
        "yk": 0,
        "bk": 0,
        "rk": 0,
        "gold": 305,
        "dmg": 2454,
        "yd": 41,
        "bd": 2,
        "rd": 1,
        "cross": False,
        "pickaxe": False,
        "superPotion": False,
    }
    apply_post_boss_supply_to_state(guide_state)
    apply_post_boss_supply_to_state(best_state)
    return [
        ("guide_after_mt10_boss_supply", guide_state, guide_start_collected()),
        ("best_after_mt10_boss_supply", best_state, best_start_collected()),
    ]


def run_route(rep: Replay) -> dict[str, Any]:
    rep.begin_segment("10F 小偷开 11F")
    rep.go_to("MT10", 6, 9)
    rep.event_thief10()
    rep.go_to("MT10", 6, 11)
    rep.transition("MT11", 6, 11)

    rep.begin_segment("11F 打小蝙蝠上 12F")
    rep.go_to("MT11", 11, 11)
    rep.transition("MT12", 11, 11)

    rep.begin_segment("12F 三次买攻击后上 13F")
    rep.go_to("MT12", 6, 9)
    rep.shop12_attack_three()
    rep.go_to("MT12", 1, 11)
    rep.transition("MT13", 1, 11)

    rep.begin_segment("13F 直接过")
    rep.go_to("MT13", 11, 11)
    rep.transition("MT14", 11, 11)

    rep.begin_segment("14F 开楼梯上方黄门并撞暗墙")
    rep.go_to("MT14", 6, 11)
    rep.go_to("MT14", 6, 9)
    rep.go_to("MT14", 6, 8)
    rep.teleport("MT7", 11, 11, "返回 7F")

    rep.begin_segment("7F/6F 买商人钥匙")
    rep.teleport("MT7", 6, 1, "飞到 7F 上方商人")
    rep.merchant("MT7", (6, 1), 50, {"yk": 5}, "7F 上方商人 50G -> 5黄钥匙")
    rep.teleport("MT6", 8, 4, "飞到 6F 右上商人")
    rep.merchant("MT6", (8, 4), 50, {"bk": 1}, "6F 右上商人 50G -> 1蓝钥匙")
    rep.teleport("MT15", 6, 11, "回到 15F")

    rep.begin_segment("15F 右路小偷上 16F")
    rep.go_to("MT15", 9, 1)
    rep.event_thief15()
    rep.go_to("MT15", 6, 1)
    rep.transition("MT16", 6, 1)

    rep.begin_segment("16F 中路向下上 17F")
    rep.go_to("MT16", 6, 11)
    rep.transition("MT17", 6, 11)

    rep.begin_segment("17F 左侧四卫兵取银剑")
    for pos in [(1, 8), (3, 8), (1, 5), (3, 5)]:
        rep.go_to("MT17", *pos)
    rep.go_to("MT17", 2, 2)
    rep.go_to("MT17", 6, 11)
    rep.transition("MT16", 6, 11)

    rep.begin_segment("16F 左下暗墙取宝石钥匙血瓶")
    rep.go_to("MT16", 2, 9)
    rep.go_to("MT16", 2, 8)
    rep.go_to("MT16", 1, 7)
    rep.go_to("MT16", 1, 5)
    rep.go_to("MT16", 2, 5)

    rep.begin_segment("11F 左下补钥匙金币")
    rep.teleport("MT11", 6, 11, "飞到 11F")
    rep.go_to("MT11", 4, 11)
    rep.go_to("MT11", 2, 9)

    rep.begin_segment("15F 右下买蓝钥匙")
    rep.teleport("MT15", 6, 11, "去 15F 右下商人")
    rep.go_to("MT15", 11, 11)
    rep.merchant("MT15", (11, 11), 200, {"bk": 1}, "15F 右下商人 200G -> 1蓝钥匙")

    rep.begin_segment("11F 开蓝门杀法师取银盾")
    rep.teleport("MT11", 6, 11, "回 11F 取盾")
    rep.go_to("MT11", 8, 11)
    rep.go_to("MT11", 1, 7)
    rep.go_to("MT11", 2, 8)
    rep.go_to("MT11", 1, 5)
    rep.go_to("MT11", 3, 5)
    rep.go_to("MT11", 2, 2)

    rep.begin_segment("回 1区补钥匙飞行器")
    rep.teleport("MT1", 2, 1, "回 1F")
    rep.go_to("MT1", 1, 6)
    rep.go_to("MT1", 2, 11)
    rep.go_to("MT1", 3, 11)
    rep.teleport("MT8", 1, 1, "回 8F 右下")
    rep.go_to("MT8", 7, 10)
    rep.go_to("MT8", 7, 11)
    rep.teleport("MT9", 6, 1, "回 9F 左上")
    rep.go_to("MT9", 2, 2)

    rep.begin_segment("12F 取红蓝宝石")
    rep.teleport("MT12", 11, 11, "回 12F")
    rep.go_to("MT12", 6, 1)
    rep.go_to("MT12", 10, 6)

    rep.begin_segment("11F 右侧取红宝石")
    rep.teleport("MT11", 6, 11, "回 11F")
    rep.go_to("MT11", 5, 1)

    rep.begin_segment("16F 左上打大蝙蝠拿三黄钥匙")
    rep.teleport("MT16", 6, 1, "回 16F")
    rep.go_to("MT16", 1, 1)
    rep.go_to("MT16", 1, 2)
    rep.go_to("MT16", 1, 3)

    rep.begin_segment("17F 走蓝门上 18F")
    rep.teleport("MT17", 6, 11, "回 17F")
    rep.go_to("MT17", 6, 1)
    rep.transition("MT18", 6, 1)

    rep.begin_segment("18F 暗墙右路拿钥匙后上 19F")
    rep.go_to("MT18", 6, 3)
    rep.go_to("MT18", 11, 3)
    rep.go_to("MT18", 5, 4)
    rep.go_to("MT18", 1, 1)
    rep.transition("MT19", 1, 1)

    rep.begin_segment("19F 左下上 20F")
    rep.go_to("MT19", 6, 11)
    rep.transition("MT20", 6, 11)

    rep.begin_segment("20F 左边红蓝宝石")
    rep.go_to("MT20", 1, 4)
    rep.go_to("MT20", 2, 4)
    rep.go_to("MT20", 6, 11)
    rep.transition("MT19", 6, 11)

    rep.begin_segment("19F 右上红宝石")
    rep.go_to("MT19", 11, 1)
    rep.go_to("MT19", 6, 11)

    rep.begin_segment("15F 左侧三黄门取蓝钥匙")
    rep.teleport("MT15", 6, 11, "回 15F 左侧")
    rep.go_to("MT15", 3, 6)

    rep.begin_segment("19F 中路取十字架")
    rep.teleport("MT19", 6, 11, "回 19F 中路")
    rep.go_to("MT19", 6, 7)
    rep.go_to("MT19", 5, 6)
    rep.go_to("MT19", 6, 4)
    rep.go_to("MT19", 6, 3)

    rep.begin_segment("15F 左上蓝宝石")
    rep.teleport("MT15", 6, 11, "回 15F 左上")
    rep.go_to("MT15", 1, 1)

    rep.begin_segment("12F 左下钥匙")
    rep.teleport("MT12", 11, 11, "回 12F 左下")
    rep.go_to("MT12", 2, 8)

    rep.begin_segment("14F 左上三兽人武士红钥匙")
    rep.teleport("MT14", 6, 11, "回 14F 左上")
    rep.go_to("MT14", 5, 1)
    for pos in [(1, 1), (3, 1), (2, 2)]:
        rep.go_to("MT14", *pos)

    rep.begin_segment("20F 吸血鬼决战")
    rep.teleport("MT20", 6, 11, "回 20F")
    rep.go_to("MT20", 6, 9)
    rep.go_to("MT20", 6, 8)
    rep.event_vampire_trigger()
    rep.go_to("MT20", 6, 6)
    rep.end_segment()
    return {
        "label": rep.label,
        "final": rep.snapshot(),
        "segments": rep.segments,
        "steps": rep.steps,
        "errors": rep.errors,
        "warnings": rep.warnings,
    }


def run_route_direct(rep: Replay, options: dict[str, Any] | None = None) -> dict[str, Any]:
    """Replay the supplied guide as explicit coordinate actions."""
    options = options or {}

    def a(fid: str, x: int, y: int, note: str = "") -> None:
        rep.act(fid, x, y, note)

    def many(fid: str, coords: Iterable[tuple[int, int]]) -> None:
        for x, y in coords:
            a(fid, x, y)

    rep.begin_segment("10F 小偷开 11F")
    rep.event_thief10()
    rep.transition("MT11", 6, 11)

    rep.begin_segment("11F 打小蝙蝠上 12F")
    a("MT11", 10, 9)
    rep.transition("MT12", 11, 11)

    rep.begin_segment("12F 三次买攻击后上 13F")
    a("MT12", 8, 11)
    a("MT12", 7, 10)
    a("MT12", 5, 10)
    rep.shop12_buys(list(options.get("shop12", ["atk", "atk", "atk"])))
    a("MT12", 4, 11)
    rep.transition("MT13", 1, 11)

    rep.begin_segment("13F 通过并处理 14F 暗墙")
    rep.transition("MT14", 11, 11)
    many("MT14", [(9, 9), (8, 8), (6, 8), (6, 9), (5, 10)])
    rep.teleport("MT7", 11, 11, "返回 7F")

    rep.begin_segment("7F/6F 买钥匙商人")
    if (7, 5) not in rep.cleared.get("MT7", set()):
        many("MT7", [(7, 5), (7, 3)])
    rep.merchant("MT7", (6, 1), 50, {"yk": 5}, "7F 商人：50G -> 5 黄钥匙")
    many("MT6", [(7, 1), (9, 1), (10, 1), (11, 2), (11, 4), (8, 3)])
    rep.merchant("MT6", (8, 4), 50, {"bk": 1}, "6F 商人：50G -> 1 蓝钥匙")
    rep.teleport("MT15", 6, 11, "去 15F")

    rep.begin_segment("15F 右路小偷")
    many("MT15", [(8, 11), (9, 11), (10, 10), (9, 9), (9, 6), (10, 5), (11, 3), (11, 2)])
    a("MT15", 9, 1)
    rep.event_thief15()
    rep.transition("MT16", 6, 1)

    rep.begin_segment("16F 中路上 17F")
    many("MT16", [(7, 3), (6, 4), (5, 5), (7, 7), (6, 8)])
    rep.transition("MT17", 6, 11)

    rep.begin_segment("17F 四卫兵取银剑")
    many("MT17", [(4, 11), (1, 11), (2, 10), (1, 8), (3, 8), (1, 5), (3, 5), (2, 2)])
    rep.transition("MT16", 6, 11)

    rep.begin_segment("9F 提前补钥匙")
    if (
        options.get("take_16_lower_left", True)
        and rep.state["yk"] <= 0
        and (2, 2) not in rep.cleared.get("MT9", set())
    ):
        many("MT9", [(1, 3), (2, 2)])

    rep.begin_segment("16F 左下宝石钥匙")
    if options.get("take_16_lower_left", True):
        many("MT16", [(4, 10), (2, 9), (2, 8), (2, 7), (1, 7), (1, 6), (1, 5), (2, 5)])

    rep.begin_segment("11F 左下钥匙与 200G 准备")
    rep.teleport("MT11", 6, 11, "去 11F 左下")
    many("MT11", [(5, 9), (4, 9), (4, 11), (3, 11), (2, 11), (1, 11), (1, 10)])
    if not options.get("delay_mt11_shield", False):
        a("MT11", 2, 9)

    rep.begin_segment("15F 买蓝钥匙")
    rep.merchant("MT15", (11, 11), 200, {"bk": 1}, "15F 商人：200G -> 1 蓝钥匙")

    rep.begin_segment("11F 取银盾")
    if not options.get("delay_mt11_shield", False):
        rep.teleport("MT11", 6, 11, "回 11F 盾房")
        many("MT11", [(2, 8), (1, 7), (1, 5), (3, 5), (2, 2)])

    rep.begin_segment("1区补钥匙和楼层传送器")
    if (4, 3) not in rep.cleared.get("MT1", set()):
        a("MT1", 4, 3, "真实飞到 1F 后进入左下区域需要先开此门")
    if (1, 3) not in rep.cleared.get("MT1", set()):
        a("MT1", 1, 3, "开 MT1 x4y3 后顺路补红血瓶")
    many("MT1", [(2, 4), (2, 5), (1, 6), (2, 7), (2, 8)])
    many("MT1", [(3, 10), (3, 11), (2, 11), (1, 11), (1, 10)])
    many("MT8", [(11, 9), (11, 10), (10, 11), (9, 11), (8, 10), (7, 10), (7, 11)])
    if (2, 2) not in rep.cleared.get("MT9", set()):
        many("MT9", [(1, 3), (2, 2)])

    rep.begin_segment("12F 右侧和上方宝石")
    many(
        "MT12",
        [
            (11, 9),
            (11, 8),
            (11, 7),
            (10, 6),
            (9, 7),
            (9, 5),
            (8, 6),
            (7, 6),
            (6, 7),
            (6, 5),
            (6, 4),
            (7, 3),
            (7, 1),
            (6, 1),
            (5, 1),
        ],
    )

    rep.begin_segment("11F 右侧红宝石")
    many("MT11", [(11, 8), (11, 4), (10, 1), (11, 1), (9, 3), (8, 2), (7, 1), (6, 2), (5, 1)])

    rep.begin_segment("11F 延后取银盾")
    if options.get("delay_mt11_shield", False):
        rep.teleport("MT11", 6, 11, "攻击到 68 后回 11F 盾房")
        many("MT11", [(2, 9), (2, 8), (1, 7), (1, 5), (3, 5), (2, 2)])

    rep.begin_segment("16F 左上三黄钥匙")
    if options.get("take_16_upper_left", True):
        many("MT16", [(4, 2), (2, 1), (1, 1), (1, 2), (1, 3)])

    rep.begin_segment("pre-cross MT17 right red gem")
    if (
        options.get("take_pre_cross_mt17_red_gem", False)
        or options.get("take_pre_cross_mt17_blue_gem", False)
        or options.get("take_pre_cross_mt17_blue_potion", False)
    ):
        rep.teleport("MT17", 6, 11, "pre-cross attack support")
        if (8, 11) not in rep.cleared.get("MT17", set()):
            many("MT17", [(8, 11), (11, 11)])
        many("MT17", [(10, 10), (9, 8), (11, 8), (10, 7), (9, 5), (11, 5), (10, 4), (9, 3), (9, 1)])
        if options.get("take_pre_cross_mt17_blue_gem", False):
            a("MT17", 11, 1)
        if options.get("take_pre_cross_mt17_blue_potion", False):
            a("MT17", 10, 2)
        a("MT17", 6, 11)

    rep.begin_segment("17F 蓝门路线上 18F")
    rep.teleport("MT17", 6, 11, "go to 18F")
    if options.get("take_mt17_right_red_potion_early", True) and (8, 11) not in rep.cleared.get("MT17", set()):
        many("MT17", [(8, 11), (11, 11)])
    many("MT17", [(6, 9), (7, 7), (7, 5), (7, 3)])
    rep.transition("MT18", 6, 1)

    rep.begin_segment("18F 暗墙和兽人武士")
    many("MT18", [(6, 3), (8, 1), (9, 1), (11, 1), (11, 2), (11, 3), (11, 4), (11, 5), (5, 4), (4, 4), (2, 4), (1, 3), (3, 2)])
    rep.transition("MT19", 1, 1)

    rep.begin_segment("19F 左下上 20F")
    many("MT19", [(1, 3), (1, 4), (1, 6), (1, 7), (1, 9), (1, 11), (3, 11), (4, 10), (5, 10), (7, 10)])
    rep.transition("MT20", 6, 11)

    rep.begin_segment("20F 左侧宝石")
    many("MT20", [(4, 11), (1, 11), (1, 9), (1, 7), (2, 6), (2, 4), (1, 4), (1, 5)])
    rep.transition("MT19", 6, 11)

    rep.begin_segment("19F 右上红宝石")
    many("MT19", [(8, 11), (10, 11), (11, 10), (10, 9), (9, 9), (11, 8), (11, 7), (11, 5), (10, 3), (10, 2), (10, 1), (11, 1)])

    rep.begin_segment("15F 左侧蓝钥匙")
    many("MT15", [(4, 1), (1, 4), (1, 7), (2, 9), (3, 7), (3, 6), (3, 5)])

    def pre_cross_mt12_blue_key() -> None:
        rep.begin_segment("pre-cross MT12 lower-left blue key")
        if (
            options.get("take_pre_cross_mt18_red_gem", False)
            and options.get("take_12_lower_left_keys", True)
            and (2, 8) not in rep.cleared.get("MT12", set())
        ):
            rep.teleport("MT12", 11, 11, "pre-cross blue key support")
            many("MT12", [(3, 10), (3, 9), (2, 7), (1, 7), (1, 8), (2, 8)])

    def pre_cross_mt18_red_gem() -> None:
        rep.begin_segment("pre-cross MT18 red gem")
        if options.get("take_pre_cross_mt18_red_gem", False):
            rep.teleport("MT18", 6, 1, "pre-cross attack support")
            many("MT18", [(6, 6), (2, 7), (1, 8), (1, 9), (2, 10), (2, 11), (1, 11)])

    def pre_cross_mt11_blue_potion() -> None:
        rep.begin_segment("pre-cross MT11 blue potion")
        if (
            options.get("take_pre_cross_mt11_blue_potion", False)
            and options.get("take_final_mt11_blue_potion", True)
            and (8, 11) not in rep.cleared.get("MT11", set())
        ):
            rep.teleport("MT11", 6, 11, "pre-cross hp support")
            many("MT11", [(9, 10), (9, 11), (8, 11)])

    if options.get("take_pre_cross_mt18_before_mt12_key", False):
        pre_cross_mt18_red_gem()
        pre_cross_mt11_blue_potion()
        pre_cross_mt12_blue_key()
    else:
        pre_cross_mt12_blue_key()
        pre_cross_mt18_red_gem()
        pre_cross_mt11_blue_potion()

    rep.begin_segment("19F 中路十字架")
    rep.teleport("MT19", 6, 11, "去 19F 中路")
    many("MT19", [(3, 8), (6, 7), (7, 6), (8, 5), (6, 4), (4, 5), (6, 3), (6, 3)])

    rep.begin_segment("15F 左上蓝宝石")
    if options.get("take_15_upper_blue_gem", True):
        many("MT15", [(1, 2), (1, 1)])

    rep.begin_segment("12F 左下钥匙")
    if options.get("take_12_lower_left_keys", True) and (2, 8) not in rep.cleared.get("MT12", set()):
        many("MT12", [(3, 10), (3, 9), (2, 7), (1, 7), (1, 8), (2, 8)])

    rep.begin_segment("决战前低成本资源")
    if options.get("take_final_mt3", True):
        many("MT3", [(9, 8), (10, 8), (11, 8), (11, 7)])
    if options.get("talk_mt6_oldman", False):
        a("MT6", 4, 8)
    if options.get("take_final_mt9", True):
        many("MT9", [(8, 11), (9, 11), (9, 9), (11, 11)])
    if options.get("take_final_mt11_blue_potion", True) and (8, 11) not in rep.cleared.get("MT11", set()):
        many("MT11", [(9, 10), (9, 11), (8, 11)])

    rep.begin_segment("16F right blue key")
    if options.get("take_mt16_right_blue_key", False) and (11, 7) not in rep.cleared.get("MT16", set()):
        rep.teleport("MT16", 6, 11, "extra blue key for 14F")
        many("MT16", [(8, 10), (10, 9), (10, 8), (11, 7)])

    rep.begin_segment("12F 800G 买红钥匙")
    if options.get("buy_red_key_12", False):
        rep.teleport("MT12", 11, 11, "去 12F 红钥匙商人")
        rep.merchant("MT12", (1, 1), 800, {"rk": 1}, "12F 商人：800G -> 1 红钥匙")

    rep.begin_segment("14F 三兽人武士红钥匙")
    if not options.get("buy_red_key_12", False):
        rep.teleport("MT14", 6, 11, "去 14F 红钥匙")
        many("MT14", [(4, 8), (3, 7), (1, 5), (2, 4), (2, 2), (1, 1), (3, 1)])

    rep.begin_segment("4F 蓝血瓶")
    if options.get("take_4f_blue_potion", True):
        many("MT4", [(4, 5), (6, 5), (9, 5), (10, 4), (10, 3), (9, 2), (11, 2)])

    rep.begin_segment("最终 11F 红血瓶")
    if options.get("take_final_mt11_red_potion", True):
        rep.teleport("MT11", 6, 11, "去 11F 红血瓶")
        many("MT11", [(4, 7), (7, 7), (8, 7), (9, 6)])

    rep.begin_segment("final MT15 right blue potion")
    if options.get("take_final_mt15_right_blue_potion", False) and (11, 8) not in rep.cleared.get("MT15", set()):
        rep.teleport("MT15", 6, 11, "final HP support")
        many("MT15", [(11, 6), (11, 8)])

    rep.begin_segment("final MT17 right red potion")
    if options.get("take_final_mt17_right_red_potion", False) and (8, 11) not in rep.cleared.get("MT17", set()):
        rep.teleport("MT17", 6, 11, "delayed right red potion")
        many("MT17", [(8, 11), (11, 11)])

    rep.begin_segment("final MT18 right blue gem")
    if options.get("take_final_mt18_right_blue_gem", False) and (10, 11) not in rep.cleared.get("MT18", set()):
        rep.teleport("MT18", 6, 1, "final defense support")
        many("MT18", [(8, 1), (9, 1), (11, 1), (11, 2), (11, 3), (11, 4), (11, 5), (11, 8), (11, 9), (11, 10), (10, 11)])

    rep.begin_segment("final MT20 right potions")
    if options.get("take_final_mt20_right_potions", False) and (11, 4) not in rep.cleared.get("MT20", set()):
        rep.teleport("MT20", 6, 11, "final HP support")
        many("MT20", [(8, 11), (11, 11), (11, 9), (10, 8), (10, 6), (11, 5), (11, 4), (10, 4)])

    rep.begin_segment("final MT14 top blue gem")
    if options.get("take_final_mt14_top_blue_gem", False) and (5, 1) not in rep.cleared.get("MT14", set()):
        rep.teleport("MT14", 6, 11, "final defense support")
        many("MT14", [(4, 8), (3, 7), (1, 5), (2, 4), (4, 5), (5, 4), (5, 2), (5, 1)])

    rep.begin_segment("16F 圣水")
    if options.get("take_super_potion16", False):
        many("MT16", [(9, 11), (10, 11), (11, 11)])
        rep.event_super_potion16()
        if options.get("use_super_potion", True):
            rep.use_super_potion()

    rep.begin_segment("20F 吸血鬼")
    rep.teleport("MT20", 6, 11, "去 20F Boss")
    a("MT20", 6, 9)
    rep.event_vampire_trigger()
    a("MT20", 6, 6)
    rep.end_segment()

    return {
        "label": rep.label,
        "final": rep.snapshot(),
        "segments": rep.segments,
        "steps": rep.steps,
        "errors": rep.errors,
        "warnings": rep.warnings,
    }


def step_line(step: dict[str, Any]) -> str:
    pos = step["pos"]
    eid = step.get("eid")
    name = ITEM_CN.get(eid, eid or "")
    before = step.get("before") or {}
    after = step["after"]
    delta = state_delta(before, after) if before else ""
    suffix = f" [{delta}]" if delta else ""
    note = f" ({step['note']})" if step.get("note") else ""
    return f"- {step['floor']} x{pos[0]}y{pos[1]} {step['action']} {name}{suffix}{note}"


def write_outputs(results: list[dict[str, Any]]) -> None:
    os.makedirs(os.path.join("outputs", "results"), exist_ok=True)
    os.makedirs(os.path.join("outputs", "walkthroughs"), exist_ok=True)
    out_json = os.path.join("outputs", "results", "zone2_guide_route_replay.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump({"results": results}, f, ensure_ascii=False, indent=2)

    lines = ["# 二区攻略路线重放", ""]
    lines.append("用户攻略目标：20F 吸血鬼后、Boss 奖励前，`HP=76 ATK=72 DEF=58 YK=5 BK=0`。")
    lines.append("")
    lines.append("| 路线 | 最终状态 | 总伤害 | 开门 黄/蓝/红 | 警告 | 错误 |")
    lines.append("|---|---|---:|---:|---:|---:|")
    for result in results:
        final = result["final"]
        lines.append(
            f"| {result['label']} | {state_text(final)} | {final['dmg']} | "
            f"{final['yd']}/{final['bd']}/{final['rd']} | {len(result['warnings'])} | {len(result['errors'])} |"
        )
    for result in results:
        lines.append("")
        lines.append(f"## {result['label']}")
        lines.append("")
        final = result["final"]
        lines.append(f"- 最终状态：{state_text(final)} dmg={final['dmg']} door={final['yd']}/{final['bd']}/{final['rd']}")
        lines.append(f"- 十字架：`{final.get('cross')}`")
        if result["warnings"]:
            lines.append(f"- 警告：`{len(result['warnings'])}`")
        if result["errors"]:
            lines.append(f"- 错误：`{len(result['errors'])}`")
        lines.append("")
        lines.append("| 阶段 | 阶段结束状态 | 阶段伤害 | 总伤害 | 总开门 黄/蓝/红 |")
        lines.append("|---|---|---:|---:|---:|")
        for seg in result["segments"]:
            end = seg["end"]
            lines.append(
                f"| {seg['name']} | {state_text(end)} | {seg['dmg']} | {end['dmg']} | "
                f"{end['yd']}/{end['bd']}/{end['rd']} |"
            )
        lines.append("")
        lines.append("### 详细 Walk")
        grouped: dict[str, list[dict[str, Any]]] = {}
        for step in result["steps"]:
            grouped.setdefault(step["segment"], []).append(step)
        for seg in result["segments"]:
            lines.append("")
            lines.append(f"#### {seg['name']}")
            lines.append("")
            for step in grouped.get(seg["name"], []):
                lines.append(step_line(step))
        if result["warnings"]:
            lines.append("")
            lines.append("### 警告")
            lines.extend(f"- {msg}" for msg in result["warnings"])
        if result["errors"]:
            lines.append("")
            lines.append("### 错误")
            lines.extend(f"- {msg}" for msg in result["errors"])
    out_md = os.path.join("outputs", "walkthroughs", "walkthrough_zone2_guide_route.md")
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")
    print(f"已写入 {out_json}")
    print(f"已写入 {out_md}")


def main() -> None:
    floors, enemies = load_floors()
    results = []
    for label, state, cleared in scenario_states():
        rep = Replay(label, state, deepcopy(floors), enemies, cleared)
        results.append(run_route_direct(rep))
    write_outputs(results)
    for result in results:
        final = result["final"]
        print(
            f"{result['label']}: {state_text(final)} "
            f"dmg={final['dmg']} door={final['yd']}/{final['bd']}/{final['rd']} "
            f"warnings={len(result['warnings'])} errors={len(result['errors'])}"
        )
        if result["errors"]:
            for msg in result["errors"][:8]:
                print(f"  ERROR {msg}")
        if result["warnings"]:
            for msg in result["warnings"][:8]:
                print(f"  WARN {msg}")


if __name__ == "__main__":
    main()
