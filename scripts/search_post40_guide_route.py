#!/usr/bin/env python3
"""Replay and probe the guide-style route after the 40F boss.

The script starts from a live-browser snapshot exported by export_current_cdp.js
and uses local floor JSON plus a small set of real high-floor event rules.
It is intentionally conservative: when a guide step is not currently legal it
stops with the exact checkpoint rather than inventing a shortcut.
"""

from __future__ import annotations

import copy
import argparse
import heapq
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "outputs" / "results" / "guide40_current_snapshot.json"
OUT_JSON = ROOT / "outputs" / "results" / "post40_guide_probe.json"
OUT_MD = ROOT / "outputs" / "reports" / "post40_guide_probe.md"

STATE_KEYS = ("hp", "atk", "def", "yk", "bk", "rk", "gold")
STAGE_NAMES = (
    "prefix48",
    "pre_earthquake",
    "farm_earthquake",
    "shield",
    "post_shield_49",
    "post_49_endgame",
)
TRACE_ENABLED = False
CROSS_TARGETS = {"zombie", "zombieKnight", "vampire"}
DRAGON_TARGETS = {"magicDragon"}
WALL_IDS = {
    "yellowWall",
    "whiteWall",
    "whiteWall2",
    "blueWall",
    "unbreakableWall",
    "blockWall",
    "autotile",
    "star",
    "lava",
    "water",
    "blueWater",
}
DOORS = {"yellowDoor", "blueDoor", "redDoor", "specialDoor", "steelDoor"}
STAIRS = {"upFloor", "downFloor"}

ITEM_CN = {
    "yellowDoor": "黄门",
    "blueDoor": "蓝门",
    "redDoor": "红门",
    "specialDoor": "机关门",
    "yellowKey": "黄钥匙",
    "blueKey": "蓝钥匙",
    "redKey": "红钥匙",
    "redPotion": "红血瓶",
    "bluePotion": "蓝血瓶",
    "redGem": "红宝石",
    "blueGem": "蓝宝石",
    "sword4": "圣剑",
    "shield4": "圣盾",
    "shield5": "神圣盾",
    "bigKey": "魔法钥匙",
    "upFly": "上楼器",
    "downFly": "下楼器",
    "coin": "幸运金币",
    "earthquake": "地震卷轴",
    "bomb": "炸弹",
    "centerFly": "中心对称飞行器",
    "snow": "冰魔法",
    "knife": "屠龙匕首",
}


@dataclass(frozen=True)
class Block:
    kind: str
    eid: str
    tile: int


@dataclass
class Floor:
    fid: str
    ratio: int
    grid: list[list[int]]
    blocks: dict[tuple[int, int], Block]
    change_floor: dict[str, Any]

    @property
    def width(self) -> int:
        return len(self.grid[0])

    @property
    def height(self) -> int:
        return len(self.grid)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def floor_no(fid: str) -> int:
    return int(fid[2:])


def state_line(s: dict[str, Any]) -> str:
    return (
        f"HP={s['hp']} ATK={s['atk']} DEF={s['def']} "
        f"YK={s['yk']} BK={s['bk']} RK={s['rk']} G={s['gold']}"
    )


def trace_point(label: str, g: "Game") -> None:
    if not TRACE_ENABLED:
        return
    print(
        f"[trace] {label}: {state_line(g.state)} "
        f"{g.state['floor']} x{g.state['x']}y{g.state['y']} "
        f"dmg={g.state['dmg']} door={g.state['yd']}/{g.state['bd']}/{g.state['rd']} "
        f"steps={len(g.steps)}",
        flush=True,
    )


def shop_cost(times1: int) -> int:
    return 20 + 10 * (times1 + 1) * times1


def default_floor_ratio(fid: str) -> int:
    n = floor_no(fid)
    if 11 <= n <= 20:
        return 2
    if 31 <= n <= 40:
        return 4
    if 41 <= n <= 50:
        return 5
    return 1


def load_tiles() -> dict[int, dict[str, Any]]:
    raw = read_json(ROOT / "data" / "maps" / "tile_mapping.json")
    return {int(k): v for k, v in raw["tiles"].items()}


def load_enemies() -> dict[str, dict[str, Any]]:
    return read_json(ROOT / "data" / "maps" / "enemy_stats.json")["enemys"]


def load_fly_points() -> dict[str, dict[str, Any]]:
    return read_json(ROOT / "data" / "maps" / "fly_points.json")


def decode_snapshot_grid(fid: str, base_grid: list[list[int]], snapshot: dict[str, Any]) -> list[list[int]]:
    saved = snapshot.get("maps", {}).get(fid)
    if not saved:
        return copy.deepcopy(base_grid)
    saved_grid = saved.get("map")
    if not saved_grid:
        return copy.deepcopy(base_grid)
    out: list[list[int]] = []
    for y, row in enumerate(saved_grid):
        if isinstance(row, int):
            out.append(list(base_grid[y]))
            continue
        out.append([base_grid[y][x] if value == -1 else value for x, value in enumerate(row)])
    return out


def classify(eid: str, cls: str, enemies: dict[str, dict[str, Any]]) -> str | None:
    if eid in WALL_IDS:
        return "wall"
    if eid in enemies or cls == "enemy48":
        return "enemy"
    if eid in DOORS:
        return "door"
    if cls == "items" or eid in ITEM_CN:
        return "item"
    if eid in STAIRS or eid in {"fakeWall", "fakeWall2", "flower"}:
        return "terrain"
    if cls == "npcs" or eid in {"blueShop", "oldman", "trader", "thief"}:
        return "npc"
    return None


def load_floor(fid: str, snapshot: dict[str, Any], tiles: dict[int, dict[str, Any]], enemies: dict[str, Any]) -> Floor:
    raw = read_json(ROOT / "data" / "maps" / f"mt{floor_no(fid)}_map.json")
    base_grid = raw.get("map") or raw.get("m")
    if not base_grid:
        raise KeyError(f"{fid} has no map grid")
    grid = decode_snapshot_grid(fid, base_grid, snapshot)
    ratio = int(raw.get("ratio") or default_floor_ratio(fid))
    blocks: dict[tuple[int, int], Block] = {}
    for y, row in enumerate(grid):
        for x, tile in enumerate(row):
            if tile == 0:
                continue
            info = tiles.get(tile)
            if not info:
                continue
            eid = info["id"]
            cls = info.get("cls", "")
            kind = classify(eid, cls, enemies)
            if kind:
                blocks[(x, y)] = Block(kind, eid, tile)
    return Floor(fid=fid, ratio=ratio, grid=grid, blocks=blocks, change_floor=raw.get("changeFloor", {}))


def load_floors(snapshot: dict[str, Any], enemies: dict[str, Any]) -> dict[str, Floor]:
    tiles = load_tiles()
    floors: dict[str, Floor] = {}
    for n in range(1, 51):
        path = ROOT / "data" / "maps" / f"mt{n}_map.json"
        if path.exists():
            floors[f"MT{n}"] = load_floor(f"MT{n}", snapshot, tiles, enemies)
    return floors


class RouteError(Exception):
    pass


class Game:
    def __init__(self, snapshot: dict[str, Any]) -> None:
        self.snapshot_raw = snapshot
        self.enemies = load_enemies()
        self.floors = load_floors(snapshot, self.enemies)
        self.fly_points = load_fly_points()
        hero = snapshot["hero"]
        flags = hero.get("flags", {})
        constants = hero.get("constants", {})
        tools = hero.get("tools", {})
        self.state: dict[str, Any] = {
            "floor": snapshot["floorId"],
            "x": hero["x"],
            "y": hero["y"],
            "hp": hero["hp"],
            "atk": hero["atk"],
            "def": hero["def"],
            "gold": hero["money"],
            "yk": hero["yk"],
            "bk": hero["bk"],
            "rk": hero["rk"],
            "dmg": 0,
            "yd": 0,
            "bd": 0,
            "rd": 0,
            "times1": int(flags.get("times1", 0)),
            "centerFly": int(tools.get("centerFly", 0)),
            "upFly": int(tools.get("upFly", 0)),
            "downFly": int(tools.get("downFly", 0)),
            "earthquake": int(tools.get("earthquake", 0)),
            "bomb": int(tools.get("bomb", 0)),
            "bigKey": int(tools.get("bigKey", 0)),
            "pickaxe": int(tools.get("pickaxe", 0)),
            "superPotion": int(tools.get("superPotion", 0)),
            "snow": int(constants.get("snow", 0) or tools.get("snow", 0)),
            "knife": bool(constants.get("knife", 0)),
            "earthquakeBought": int(flags.get("earthquakeBought", 0)),
            "coin": bool(constants.get("coin", 0)),
            "cross": bool(constants.get("cross", 0)),
            "magicImmune": bool(flags.get("魔法免疫", False)),
            "won49": False,
            "won50": False,
        }
        visited = flags.get("__visited__", {})
        self.visited = {fid for fid, ok in visited.items() if ok}
        self.visited.add(self.state["floor"])
        self.steps: list[dict[str, Any]] = []
        self.errors: list[str] = []
        self.segment = "start"
        self.flags: dict[str, Any] = dict(flags)
        self.blocked_items: set[tuple[str, int, int]] = set()
        # RedWizards that retreat one tile away from the hero when approached
        # (until blocked by wall/door). They need a corner-trap route, not a
        # direct go_to, so auto-farming/sweeping must skip them.
        self.retreat_wizards: set[tuple[str, int, int]] = {("MT47", 1, 9)}
        # Bosses that the guide kills at specific stages (with higher stats after
        # shop/bless) must NOT be auto-farmed earlier when their damage is high.
        # Only the hand-written sections deal with them.
        self.no_auto_farm: set[tuple[str, int, int]] = {
            ("MT35", 6, 7),   # magicDragon (after 49F knife, guide step 11a)
            ("MT25", 6, 6),   # blackMagician (after bless, guide step 11f)
            ("MT49", 6, 3),   # redKing 49F (seal sequence, guide step 10)
            ("MT50", 6, 5),   # redKing 50F (final boss)
        }
    def clone(self) -> "Game":
        return copy.deepcopy(self)

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
            times1=self.state["times1"],
            centerFly=self.state["centerFly"],
            upFly=self.state["upFly"],
            downFly=self.state["downFly"],
            earthquake=self.state["earthquake"],
            bomb=self.state["bomb"],
            bigKey=self.state["bigKey"],
            pickaxe=self.state["pickaxe"],
            superPotion=self.state["superPotion"],
            snow=self.state["snow"],
            knife=self.state["knife"],
            earthquakeBought=self.state["earthquakeBought"],
            coin=self.state["coin"],
            magicImmune=self.state["magicImmune"],
            won49=self.state["won49"],
            won50=self.state["won50"],
        )
        return out

    def set_segment(self, name: str) -> None:
        self.segment = name

    def fail(self, message: str) -> None:
        self.errors.append(f"{self.segment}: {message}; {state_line(self.state)} {self.state['floor']} x{self.state['x']}y{self.state['y']}")
        raise RouteError(self.errors[-1])

    def record(self, action: str, pos: tuple[int, int] | None, eid: str | None, before: dict[str, Any], note: str = "") -> None:
        after = self.snapshot()
        delta = []
        for key, label in [("hp", "HP"), ("atk", "ATK"), ("def", "DEF"), ("yk", "YK"), ("bk", "BK"), ("rk", "RK"), ("gold", "G")]:
            if before[key] != after[key]:
                delta.append(f"{label} {before[key]}->{after[key]}")
        self.steps.append(
            {
                "segment": self.segment,
                "floor": after["floor"],
                "pos": list(pos or (after["x"], after["y"])),
                "action": action,
                "eid": eid,
                "before": before,
                "after": after,
                "delta": ", ".join(delta),
                "note": note,
            }
        )

    def floor(self, fid: str | None = None) -> Floor:
        return self.floors[fid or self.state["floor"]]

    def block_at(self, fid: str, pos: tuple[int, int]) -> Block | None:
        return self.floors[fid].blocks.get(pos)

    def set_ground(self, fid: str, pos: tuple[int, int]) -> None:
        f = self.floors[fid]
        x, y = pos
        if 0 <= y < f.height and 0 <= x < f.width:
            f.grid[y][x] = 0
        f.blocks.pop(pos, None)

    def set_block(self, fid: str, pos: tuple[int, int], kind: str, eid: str, tile: int = 0) -> None:
        f = self.floors[fid]
        x, y = pos
        if 0 <= y < f.height and 0 <= x < f.width:
            f.grid[y][x] = tile
        f.blocks[pos] = Block(kind, eid, tile)

    def is_wall(self, fid: str, pos: tuple[int, int]) -> bool:
        f = self.floors[fid]
        x, y = pos
        if x < 0 or y < 0 or x >= f.width or y >= f.height:
            return True
        block = f.blocks.get(pos)
        if block and block.kind == "door" and block.eid in {"specialDoor", "steelDoor"}:
            return True
        if block and block.kind == "npc":
            return True
        if block and block.eid in WALL_IDS:
            return True
        return False

    def enemy_damage(self, eid: str) -> int | float:
        enemy = self.enemies[eid]
        if eid == "redKing" and self.flags.get("50final"):
            enemy = {**enemy, "hp": 5000, "atk": 1580, "def": 190}
        elif eid == "redKing" and self.flags.get("49sealed"):
            # Killing the 4 cardinal whiteKing guards (x6y2,x6y4,x5y3,x7y3)
            # breaks the seal: redKing drops 8000hp/5000atk/1000def -> 800/500/100.
            enemy = {**enemy, "hp": 800, "atk": 500, "def": 100}
        atk = self.state["atk"] * (2 if self.state.get("cross") and eid in CROSS_TARGETS else 1)
        if self.state.get("knife") and eid in DRAGON_TARGETS:
            atk *= 2
        mon_def = int(enemy["def"])
        mon_hp = int(enemy["hp"])
        hero_hit = max(0, atk - mon_def)
        if hero_hit <= 0:
            return float("inf")
        turns = math.ceil(mon_hp / hero_hit)
        per = max(0, int(enemy["atk"]) - self.state["def"])
        special = enemy.get("special", 0)
        if special == 2 or (isinstance(special, list) and 2 in special):
            per = int(enemy["atk"])
        if special == 4 or (isinstance(special, list) and 4 in special):
            per *= 2
        if special == 5 or (isinstance(special, list) and 5 in special):
            per *= 3
        return (turns - 1) * per

    def check_damage_at(self, fid: str, pos: tuple[int, int]) -> int:
        """Pure query: damage the hero WOULD take standing at pos right now.
        Must have NO side effects -- path_to/path_cost call this during routing
        to compare candidate cells, so it cannot mutate spell_cells_hit."""
        if self.state.get("magicImmune"):
            return 0
        x, y = pos
        total = 0
        f = self.floors[fid]
        for (ex, ey), block in f.blocks.items():
            if block.kind != "enemy":
                continue
            enemy = self.enemies.get(block.eid)
            if not enemy:
                continue
            special = enemy.get("special", 0)
            specials = set(special if isinstance(special, list) else [special])
            if 15 in specials:
                # Wizard spell-field: damages the hero every time it enters the
                # field cell (verified on 42F: x10y4 takes 300 on both the first
                # pass and the return pass through the same cell).
                rng = int(enemy.get("range", 1) or 1)
                if enemy.get("zoneSquare"):
                    in_range = max(abs(ex - x), abs(ey - y)) <= rng and (ex, ey) != (x, y)
                else:
                    in_range = abs(ex - x) + abs(ey - y) <= rng and (ex, ey) != (x, y)
                if in_range:
                    total += int(enemy.get("value", 0) or 0)
        # Special 16: being between two identical magic guards halves current HP.
        for dx, dy in [(1, 0), (0, 1)]:
            a = f.blocks.get((x - dx, y - dy))
            b = f.blocks.get((x + dx, y + dy))
            if not a or not b or a.kind != "enemy" or b.kind != "enemy" or a.eid != b.eid:
                continue
            enemy = self.enemies.get(a.eid, {})
            special = enemy.get("special", 0)
            specials = set(special if isinstance(special, list) else [special])
            if 16 in specials:
                total += self.state["hp"] // 2
        return total

    def apply_check_damage(self, fid: str, pos: tuple[int, int], note: str = "") -> None:
        damage = self.check_damage_at(fid, pos)
        if damage <= 0:
            return
        before = self.snapshot()
        self.state["hp"] -= damage
        self.state["dmg"] += damage
        self.record("地图伤害", pos, "checkBlock", before, note)
        if self.state["hp"] <= 0:
            self.fail(f"地图伤害致死 {fid} x{pos[0]}y{pos[1]} damage={damage}")

    def can_enter(self, fid: str, pos: tuple[int, int], target: tuple[int, int]) -> bool:
        if self.is_wall(fid, pos):
            return False
        block = self.block_at(fid, pos)
        if not block:
            return True
        if block.kind == "terrain":
            return block.eid in {"fakeWall", "fakeWall2", "flower"} or (block.eid in STAIRS and pos == target)
        if block.kind == "item":
            if (fid, pos[0], pos[1]) in self.blocked_items:
                return False
            return True
        if block.kind == "enemy":
            # Retreating wizards cannot be killed by walking onto them (they flee
            # in the live game). Treat them as impassable so path_to routes
            # around instead of path-killing them en route to another target.
            # Exception: when the wizard IS the target (corner-trapped, no escape),
            # the hero kills it directly.
            if (fid, pos[0], pos[1]) in self.retreat_wizards and pos != target:
                return False
            dmg = self.enemy_damage(block.eid)
            return dmg != float("inf") and self.state["hp"] - int(dmg) > 0
        if block.kind == "door":
            if block.eid == "yellowDoor":
                return self.state["yk"] > 0
            if block.eid == "blueDoor":
                return self.state["bk"] > 0
            if block.eid == "redDoor":
                return self.state["rk"] > 0
        return False

    def path_cost(self, fid: str, pos: tuple[int, int]) -> int:
        block = self.block_at(fid, pos)
        base = 1
        if block:
            if block.kind == "item":
                base = 2
            elif block.kind == "door":
                base = {"yellowDoor": 90, "blueDoor": 140, "redDoor": 180}.get(block.eid, 9999)
            elif block.kind == "enemy":
                dmg = self.enemy_damage(block.eid)
                base = 3 if dmg == 0 else 1000 + (99999 if dmg == float("inf") else int(dmg))
        return base + self.check_damage_at(fid, pos) * 20

    def path_to(self, fid: str, target: tuple[int, int]) -> list[tuple[int, int]] | None:
        if self.state["floor"] != fid:
            self.fail(f"current floor {self.state['floor']} cannot path to {fid}")
        start = (self.state["x"], self.state["y"])
        if start == target:
            return [start]
        best = {start: 0}
        parent: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
        queue: list[tuple[int, int, tuple[int, int]]] = [(0, 0, start)]
        seq = 0
        while queue:
            cost, _, cur = heapq.heappop(queue)
            if cost != best.get(cur):
                continue
            if cur == target:
                break
            cx, cy = cur
            for nxt in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                if not self.can_enter(fid, nxt, target):
                    continue
                new_cost = cost + self.path_cost(fid, nxt)
                if new_cost >= best.get(nxt, 10**12):
                    continue
                best[nxt] = new_cost
                parent[nxt] = cur
                seq += 1
                heapq.heappush(queue, (new_cost, seq, nxt))
        if target not in parent:
            return None
        out = []
        cur: tuple[int, int] | None = target
        while cur is not None:
            out.append(cur)
            cur = parent[cur]
        return list(reversed(out))

    def go_to(self, fid: str, x: int, y: int, note: str = "") -> None:
        path = self.path_to(fid, (x, y))
        if not path:
            self.fail(f"no path to {fid} x{x}y{y}: {note}")
        for pos in path[1:]:
            prev = (self.state["x"], self.state["y"])
            block = self.block_at(fid, pos)
            if block and block.kind == "terrain" and block.eid == "flower" and not self.can_enter_flower(fid, prev, pos):
                self.fail(f"wrong-way flower at {fid} x{pos[0]}y{pos[1]} from x{prev[0]}y{prev[1]}")
            self.state["x"], self.state["y"] = pos
            if block:
                self.apply_block(fid, pos, block, note if pos == (x, y) else "")
            else:
                self.apply_check_damage(fid, pos, note if pos == (x, y) else "")
                self.trigger_tile_event(fid, pos)
                if pos == (x, y) and note:
                    before = self.snapshot()
                    self.record("到达", pos, None, before, note)

    def can_enter_flower(self, fid: str, prev: tuple[int, int], pos: tuple[int, int]) -> bool:
        if fid == "MT33" and pos == (8, 10):
            return prev == (7, 10)
        if fid == "MT38" and pos == (2, 5):
            return prev == (2, 4)
        return True

    def apply_block(self, fid: str, pos: tuple[int, int], block: Block, note: str = "") -> None:
        before = self.snapshot()
        action = "通过"
        if block.kind == "door":
            action = "开门"
            if block.eid == "yellowDoor":
                self.state["yk"] -= 1
                self.state["yd"] += 1
            elif block.eid == "blueDoor":
                self.state["bk"] -= 1
                self.state["bd"] += 1
            elif block.eid == "redDoor":
                self.state["rk"] -= 1
                self.state["rd"] += 1
            if self.state["yk"] < 0 or self.state["bk"] < 0 or self.state["rk"] < 0:
                self.fail(f"negative key after door {block.eid} at {fid} {pos}")
        elif block.kind == "enemy":
            action = "击杀"
            dmg = self.enemy_damage(block.eid)
            if dmg == float("inf"):
                self.fail(f"cannot break enemy {block.eid} at {fid} x{pos[0]}y{pos[1]}")
            self.state["hp"] -= int(dmg)
            self.state["dmg"] += int(dmg)
            gain = int(self.enemies[block.eid].get("money", 0))
            if self.state.get("coin"):
                gain *= 2
            self.state["gold"] += gain
            if self.state["hp"] <= 0:
                self.fail(f"battle death {block.eid} at {fid} x{pos[0]}y{pos[1]} damage={dmg}")
        elif block.kind == "item":
            action = "拾取"
            self.apply_item(fid, block.eid)
        elif block.kind == "terrain":
            action = "通过"
        self.record(action, pos, block.eid, before, note)
        if block.kind != "terrain":
            self.set_ground(fid, pos)
        self.after_action(fid, pos, block)
        self.apply_check_damage(fid, pos, note)
        self.trigger_tile_event(fid, pos)

    def apply_item(self, fid: str, eid: str) -> None:
        ratio = self.floors[fid].ratio
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
            self.state["atk"] += ratio
        elif eid == "blueGem":
            self.state["def"] += ratio
        elif eid == "sword4":
            self.state["atk"] += 50
        elif eid == "sword5":
            self.state["atk"] += 100
        elif eid == "shield4":
            self.state["def"] += 50
        elif eid == "shield5":
            self.state["def"] += 100
            self.state["magicImmune"] = True
        elif eid == "upFly":
            self.state["upFly"] += 1
        elif eid == "downFly":
            self.state["downFly"] += 1
        elif eid == "centerFly":
            self.state["centerFly"] += 1
        elif eid == "centerFly3":
            self.state["centerFly"] += 3
        elif eid == "bigKey":
            self.state["bigKey"] += 1
        elif eid == "bomb":
            self.state["bomb"] += 1
        elif eid == "pickaxe":
            self.state["pickaxe"] += 1
        elif eid == "earthquake":
            self.state["earthquake"] += 1
        elif eid == "coin":
            self.state["coin"] = True
        elif eid == "superPotion":
            self.state["superPotion"] += 1
        elif eid == "snow":
            self.state["snow"] += 1
        elif eid == "knife":
            self.state["knife"] = True

    def after_action(self, fid: str, pos: tuple[int, int], block: Block) -> None:
        if fid == "MT41" and block.kind == "enemy" and pos == (2, 2):
            self.flags["41"] = 1
        if fid == "MT41" and block.kind == "enemy" and pos == (10, 2):
            for p in [(5, 7), (7, 7)]:
                self.set_ground(fid, p)
            for p in [(5, 6), (6, 6), (7, 6), (7, 1)]:
                self.set_block(fid, p, "wall", "yellowWall", 1)
            self.set_block(fid, (6, 5), "item", "downFly", 52)
        if fid == "MT43" and block.kind == "enemy" and pos == (9, 1):
            for p in [(8, 2), (10, 2)]:
                self.set_block(fid, p, "wall", "yellowWall", 1)
        if fid == "MT15" and block.kind == "enemy" and pos == (6, 6):
            for p in [(5, 4), (5, 5), (5, 6), (7, 4), (7, 5), (7, 6), (6, 4)]:
                self.set_ground(fid, p)
            self.set_ground(fid, (6, 3))
        if fid == "MT25" and block.kind == "enemy" and pos == (6, 6):
            for p in [(4, 8), (5, 8), (7, 8), (8, 8)]:
                self.set_block(fid, p, "item", "redKey", 23)
            self.set_ground(fid, (6, 9))
        if fid == "MT35" and block.kind == "enemy" and pos == (6, 7):
            for p in [(6, 3), (5, 7), (7, 7)]:
                self.set_ground(fid, p)
            if not self.flags.get("开启特性"):
                for p in [(5, 5), (6, 5), (7, 5)]:
                    self.set_block(fid, p, "item", "bluePotion", 32)
            self.set_block(fid, (6, 6), "item", "snow", 54)
        if fid == "MT44" and block.kind == "enemy" and pos in {(5, 9), (7, 9)}:
            self.flags["441"] = self.flags.get("441", 0) + 1
            if self.flags["441"] >= 2:
                self.set_ground(fid, (6, 8))
        if fid == "MT45" and block.kind == "enemy":
            if pos in {(8, 9), (8, 11)}:
                self.flags["451"] = self.flags.get("451", 0) + 1
                if self.flags["451"] >= 2:
                    self.set_ground(fid, (7, 10))
            if pos in {(5, 9), (5, 11)}:
                self.flags["452"] = self.flags.get("452", 0) + 1
                if self.flags["452"] >= 2:
                    self.set_ground(fid, (4, 10))
        if fid == "MT49" and block.kind == "enemy":
            if pos in {(6, 2), (5, 3), (7, 3), (6, 4)}:
                self.flags["49cardinal"] = self.flags.get("49cardinal", 0) + 1
                if self.flags["49cardinal"] >= 4:
                    self.flags["49sealed"] = True
            if pos in {(5, 10), (7, 10)}:
                self.flags["491"] = self.flags.get("491", 0) + 1
                if self.flags["491"] >= 2:
                    self.set_ground(fid, (6, 9))
            if pos in {(5, 8), (7, 8)}:
                self.flags["492"] = self.flags.get("492", 0) + 1
                if self.flags["492"] >= 2:
                    self.set_ground(fid, (6, 7))
            if pos == (6, 3):
                self.state["won49"] = True
                for p in [(5, 2), (6, 2), (7, 2), (5, 3), (6, 3), (7, 3), (5, 4), (6, 4), (7, 4)]:
                    self.set_ground(fid, p)
                self.set_block(fid, (5, 2), "item", "redKey", 23)
                self.set_block(fid, (7, 2), "item", "knife", 62)
                for p in [(2, 4), (3, 4), (4, 4)]:
                    self.set_block(fid, p, "item", "redGem", 27)
                for p in [(8, 4), (9, 4), (10, 4)]:
                    self.set_block(fid, p, "item", "blueGem", 28)
                for p in [(5, 5), (6, 5), (7, 5)]:
                    self.set_block(fid, p, "item", "bluePotion", 32)
        if fid == "MT50" and block.kind == "enemy" and pos == (6, 5):
            self.state["won50"] = True

    def trigger_tile_event(self, fid: str, pos: tuple[int, int]) -> None:
        # 47F: walking onto x8y1 (adjacent to the x8y2 redWizard) triggers the
        # redWizard to move down to x8y3. The spell-field damage for x8y1 is
        # applied BEFORE this move (redWizard still at x8y2, range 1 -> 200 dmg),
        # so on the return pass x8y1 is out of range (redWizard now at x8y3,
        # distance 2) and takes no damage. Verified against the live game.
        if fid == "MT47" and pos == (8, 1) and not self.flags.get("47wizardMoved"):
            block = self.block_at(fid, (8, 2))
            if block and block.eid == "redWizard":
                before = self.snapshot()
                self.set_ground(fid, (8, 2))
                self.set_block(fid, (8, 3), "enemy", "redWizard", block.tile)
                self.flags["47wizardMoved"] = True
                # The retreated wizard (now x8y3) also retreats when approached,
                # so it must be corner-trapped (from x8y2, with x8y4 door closed
                # blocking its retreat) -- not path-killed by auto-farming.
                self.retreat_wizards.add(("MT47", 8, 3))
                self.record("事件", (8, 3), "redWizard", before, "47F 右上红巫师下移")
        if fid == "MT42" and pos == (5, 10) and self.block_at(fid, (6, 10)):
            before = self.snapshot()
            self.set_ground(fid, (6, 10))
            self.record("事件", pos, "yellowKnightEscape", before, "42F 骑士队长剧情逃跑")
        if fid == "MT41" and pos == (9, 2) and self.flags.get("41") == 1 and (
            not self.block_at(fid, (10, 2)) or self.block_at(fid, (10, 2)).eid != "redWizard"
        ):
            before = self.snapshot()
            self.set_block(fid, (10, 2), "enemy", "redWizard", 220)
            self.flags["41"] = 2
            self.record("事件", (10, 2), "redWizard", before, "41F 右上撞墙出现红巫师")

    def _move_retreat_wizard(self, fid: str, old_pos: tuple[int, int], new_pos: tuple[int, int]) -> None:
        """Record a retreating redWizard moving from old_pos to new_pos (the hero
        stepped adjacent and the wizard fled one tile away from the hero, toward
        new_pos). No hero stat/position change."""
        block = self.block_at(fid, old_pos)
        if not block or block.eid != "redWizard":
            return
        before = self.snapshot()
        self.set_ground(fid, old_pos)
        self.set_block(fid, new_pos, "enemy", "redWizard", block.tile)
        self.record("事件", new_pos, "redWizard", before, f"47F 法师后退 {old_pos}->{new_pos}")

    def transition(self, to_fid: str, note: str = "") -> None:
        before = self.snapshot()
        from_fid = self.state["floor"]
        point_key = "downFloor" if floor_no(to_fid) > floor_no(from_fid) else "upFloor"
        landing = self.fly_points[to_fid][point_key]
        if landing is None and to_fid == "MT44":
            landing = [1, 1]
        if not landing:
            self.fail(f"no landing {from_fid}->{to_fid}")
        self.state["floor"] = to_fid
        self.state["x"], self.state["y"] = landing
        self.visited.add(to_fid)
        self.record("换层", tuple(landing), None, before, note or f"{from_fid}->{to_fid}")
        self.apply_check_damage(to_fid, tuple(landing), "换层落点")

    def fly(self, fid: str) -> None:
        if fid == self.state["floor"]:
            return
        if fid not in self.visited:
            self.fail(f"cannot fly to unvisited floor {fid}")
        before = self.snapshot()
        from_fid = self.state["floor"]
        point_key = "downFloor" if floor_no(fid) > floor_no(from_fid) else "upFloor"
        landing = self.fly_points[fid][point_key]
        if not landing:
            self.fail(f"no fly landing {from_fid}->{fid}")
        self.state["floor"] = fid
        self.state["x"], self.state["y"] = landing
        self.record("飞行", tuple(landing), None, before, f"飞到 {fid}")
        self.apply_check_damage(fid, tuple(landing), "飞行落点")

    def center_fly(self, note: str = "") -> None:
        if self.state["centerFly"] <= 0:
            self.fail("no centerFly left")
        before = self.snapshot()
        f = self.floor()
        x = f.width - 1 - self.state["x"]
        y = f.height - 1 - self.state["y"]
        if self.is_wall(self.state["floor"], (x, y)) or self.block_at(self.state["floor"], (x, y)):
            self.fail(f"centerFly target blocked x{x}y{y}")
        self.state["centerFly"] -= 1
        self.state["x"], self.state["y"] = x, y
        self.record("中心飞行", (x, y), "centerFly", before, note)
        self.apply_check_damage(self.state["floor"], (x, y), note)

    def up_fly(self, note: str = "") -> None:
        if self.state["upFly"] <= 0:
            self.fail("no upFly")
        to = f"MT{floor_no(self.state['floor']) + 1}"
        x, y = self.state["x"], self.state["y"]
        if self.block_at(to, (x, y)) or self.is_wall(to, (x, y)):
            self.fail(f"upFly blocked at {to} x{x}y{y}")
        before = self.snapshot()
        self.state["upFly"] -= 1
        self.state["floor"] = to
        self.visited.add(to)
        self.record("上楼器", (x, y), "upFly", before, note)
        self.apply_check_damage(to, (x, y), note)

    def down_fly(self, note: str = "") -> None:
        if self.state["downFly"] <= 0:
            self.fail("no downFly")
        to = f"MT{floor_no(self.state['floor']) - 1}"
        x, y = self.state["x"], self.state["y"]
        if to in self.floors and (self.block_at(to, (x, y)) or self.is_wall(to, (x, y))):
            self.fail(f"downFly blocked at {to} x{x}y{y}")
        before = self.snapshot()
        self.state["downFly"] -= 1
        self.state["floor"] = to
        self.visited.add(to)
        self.record("下楼器", (x, y), "downFly", before, note)
        if to in self.floors:
            self.apply_check_damage(to, (x, y), note)

    def use_big_key(self, note: str = "") -> None:
        if self.state["bigKey"] <= 0:
            self.fail("no bigKey")
        before = self.snapshot()
        self.state["bigKey"] -= 1
        fid = self.state["floor"]
        opened = 0
        for pos, block in list(self.floors[fid].blocks.items()):
            if block.kind == "door" and block.eid == "yellowDoor":
                self.set_ground(fid, pos)
                opened += 1
        self.record("魔法钥匙", (self.state["x"], self.state["y"]), "bigKey", before, f"{note}; opened={opened}")

    def use_earthquake(self, note: str = "") -> None:
        if self.state["earthquake"] <= 0:
            self.fail("no earthquake")
        before = self.snapshot()
        self.state["earthquake"] -= 1
        fid = self.state["floor"]
        opened = 0
        for pos, block in list(self.floors[fid].blocks.items()):
            if block.eid in WALL_IDS and block.eid not in {"unbreakableWall", "blockWall"}:
                self.set_ground(fid, pos)
                opened += 1
        self.record("地震卷轴", (self.state["x"], self.state["y"]), "earthquake", before, f"{note}; opened={opened}")

    def use_bomb(self, note: str = "") -> None:
        if self.state["bomb"] <= 0:
            self.fail("no bomb")
        before = self.snapshot()
        self.state["bomb"] -= 1
        fid = self.state["floor"]
        killed = []
        for pos in [(self.state["x"] + 1, self.state["y"]), (self.state["x"] - 1, self.state["y"]), (self.state["x"], self.state["y"] + 1), (self.state["x"], self.state["y"] - 1)]:
            block = self.block_at(fid, pos)
            if block and block.kind == "enemy" and int(self.enemies[block.eid]["hp"]) < 500:
                killed.append((pos, block))
        money = 0
        for pos, block in killed:
            money += int(self.enemies[block.eid].get("money", 0))
            self.set_ground(fid, pos)
            self.after_action(fid, pos, block)
        self.state["gold"] += money
        self.record("炸弹", (self.state["x"], self.state["y"]), "bomb", before, f"{note}; killed={[(p,b.eid) for p,b in killed]}")

    def use_pickaxe(self, fid: str, x: int, y: int, note: str = "") -> None:
        if self.state["pickaxe"] <= 0:
            self.fail("no pickaxe")
        if self.state["floor"] != fid:
            self.fail(f"cannot use pickaxe on {fid} while at {self.state['floor']}")
        if abs(self.state["x"] - x) + abs(self.state["y"] - y) != 1:
            self.fail(f"pickaxe target not adjacent {fid} x{x}y{y}")
        block = self.block_at(fid, (x, y))
        if not block or block.eid not in WALL_IDS:
            self.fail(f"pickaxe target is not breakable wall {fid} x{x}y{y}")
        before = self.snapshot()
        self.state["pickaxe"] -= 1
        self.set_ground(fid, (x, y))
        self.record("使用镐", (x, y), "pickaxe", before, note)

    def use_snow(self, note: str = "") -> None:
        if self.state["snow"] <= 0:
            self.fail("no snow")
        fid = self.state["floor"]
        before = self.snapshot()
        opened = 0
        x, y = self.state["x"], self.state["y"]
        for pos in [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]:
            block = self.block_at(fid, pos)
            if block and block.eid == "lava":
                self.set_ground(fid, pos)
                opened += 1
        if opened <= 0:
            self.fail(f"snow has no adjacent lava at {fid} x{x}y{y}")
        self.record("使用", (x, y), "snow", before, f"{note}; opened={opened}")

    def use_super_potion(self, note: str = "") -> None:
        if self.state["superPotion"] <= 0:
            self.fail("no superPotion")
        before = self.snapshot()
        self.state["superPotion"] -= 1
        self.state["hp"] += int(math.floor((self.state["atk"] + self.state["def"]) * 0.74 + 0.5)) * 10
        self.record("使用", (self.state["x"], self.state["y"]), "superPotion", before, note)

    def talk_mt2_bless(self) -> None:
        self.move_adjacent("MT2", 11, 7, "2F 祝福商人")
        before = self.snapshot()
        self.state["atk"] += int(math.floor(self.state["atk"] * 0.03 + 0.5))
        self.state["def"] += int(math.floor(self.state["def"] * 0.03 + 0.5))
        self.set_ground("MT2", (11, 7))
        self.record("商人", (11, 7), "specialTrader", before, "2F +3%攻防")

    def talk_mt16_oldman(self) -> None:
        self.go_to("MT16", 11, 11, "16F 暗墙老人")
        before = self.snapshot()
        self.state["superPotion"] += 1
        self.set_ground("MT16", (11, 11))
        self.record("老人", (11, 11), "superPotion", before, "16F 圣水")

    def talk_mt26_princess(self) -> None:
        self.move_adjacent("MT26", 6, 6, "26F 公主")
        before = self.snapshot()
        self.flags["营救公主"] = True
        self.set_ground("MT26", (6, 6))
        self.set_block("MT24", (6, 1), "wall", "whiteWall2", 1)
        for p in [(5, 1), (7, 1), (6, 2), (6, 3), (6, 4)]:
            self.set_ground("MT24", p)
        self.record("事件", (6, 6), "princess", before, "26F 营救公主")

    def trigger_mt24_to_mt50(self) -> None:
        self.go_to("MT24", 6, 2, "24F 公主通路")
        before = self.snapshot()
        self.state["floor"] = "MT50"
        self.state["x"], self.state["y"] = 6, 7
        self.visited.add("MT50")
        self.record("换层", (6, 7), None, before, "24F 剧情到50F")

    def trigger_mt50_final(self) -> None:
        self.move_adjacent("MT50", 6, 5, "50F 小偷剧情")
        before = self.snapshot()
        self.flags["50final"] = True
        self.flags["与50层小偷对话"] = True
        self.record("事件", (6, 5), "redKing", before, "50F 最终剧情结束")
        self.set_block("MT50", (6, 5), "enemy", "redKing", 245)
        self.go_to("MT50", 6, 5, "50F 最终魔王")

    @staticmethod
    def trader_flag(fid: str, x: int, y: int) -> str:
        return f"{fid}@{x}@{y}@A"

    def talk_trader(self, fid: str, x: int, y: int, note: str = "") -> None:
        # Move to any adjacent reachable tile first.
        self.move_adjacent(fid, x, y, note)
        before = self.snapshot()
        n = floor_no(fid)
        if n == 47:
            cost = 4000
            if self.state["earthquakeBought"] >= 1:
                self.fail("47F earthquake trader already used")
            if self.state["gold"] < cost:
                self.fail(f"not enough gold for 47F earthquake: have={self.state['gold']}")
            self.state["gold"] -= cost
            self.state["earthquake"] += 1
            self.state["earthquakeBought"] += 1
            eid = "earthquake"
        elif n == 45:
            cost = 1000
            flag = self.trader_flag(fid, x, y)
            if self.flags.get(flag):
                self.fail("45F HP merchant already used")
            if self.state["gold"] < cost:
                self.fail(f"not enough gold for 45F HP merchant: have={self.state['gold']}")
            self.state["gold"] -= cost
            self.state["hp"] += 2000
            self.flags[flag] = 1
            eid = "hp2000"
        elif n == 31:
            cost = 1000
            flag = self.trader_flag(fid, x, y)
            if self.flags.get(flag):
                self.fail("31F key merchant already used")
            if self.state["gold"] < cost:
                self.fail(f"not enough gold for 31F key merchant: have={self.state['gold']}")
            self.state["gold"] -= cost
            self.state["yk"] += 4
            self.state["bk"] += 1
            self.flags[flag] = 1
            eid = "keyBundle31"
        else:
            self.fail(f"unmodeled trader {fid} x{x}y{y}")
        self.record("商人", (x, y), eid, before, note)

    def buy_shop(self, kind: str, count: int = 1, shop_pos: tuple[int, int] | None = None) -> None:
        for _ in range(count):
            before = self.snapshot()
            cost = shop_cost(self.state["times1"])
            if self.state["gold"] < cost:
                self.fail(f"not enough gold for shop {kind}: need={cost} have={self.state['gold']}")
            self.state["gold"] -= cost
            ratio = self.floors[self.state["floor"]].ratio
            if kind == "atk":
                self.state["atk"] += 2 * ratio
            elif kind == "def":
                self.state["def"] += 4 * ratio
            elif kind == "hp":
                self.state["hp"] += 100 * (self.state["times1"] + 1)
            else:
                self.fail(f"unknown shop kind {kind}")
            self.state["times1"] += 1
            # Record the shop's action tile (where the hero clicks to open the
            # shop dialog), not the hero's adjacent standing tile, so the replayer
            # clicks the shop directly.
            pos = shop_pos or (self.state["x"], self.state["y"])
            self.record("商店", pos, kind, before, f"cost={cost}")

    def move_adjacent(self, fid: str, x: int, y: int, note: str = "") -> None:
        candidates = []
        for pos in [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]:
            try:
                path = self.path_to(fid, pos)
            except RouteError:
                raise
            if path:
                candidates.append((len(path), pos))
        if not candidates:
            self.fail(f"no adjacent path to {fid} x{x}y{y}: {note}")
        _, pos = min(candidates)
        self.go_to(fid, pos[0], pos[1], note)

    def change_by_stair(self, to_fid: str, stair_x: int, stair_y: int, note: str = "") -> None:
        self.go_to(self.state["floor"], stair_x, stair_y, note)
        self.transition(to_fid, note)


def safe_try(g: Game, fn, *args, **kwargs) -> bool:
    old_errors = len(g.errors)
    try:
        fn(*args, **kwargs)
        return True
    except RouteError:
        del g.errors[old_errors:]
        return False


def collect_existing_items(g: Game, fid: str, positions: list[tuple[int, int]], note: str) -> None:
    for x, y in positions:
        block = g.block_at(fid, (x, y))
        if not block or block.kind != "item":
            continue
        if g.state["floor"] != fid:
            g.fly(fid)
        safe_try(g, g.go_to, fid, x, y, f"{note} {(x, y)}")


def guide_prefix_to_48_visit(g: Game) -> None:
    g.set_segment("41-48 initial climb")
    # Go to 42F first so the 41F half-HP trap is applied before taking 40F potions.
    g.change_by_stair("MT42", 6, 11, "41F 先上42F触发低血半伤")
    g.fly("MT40")
    g.go_to("MT40", 5, 4, "40F 先吃1个蓝血瓶过42F固定伤")
    g.fly("MT42")
    # 42F knight event, right-side keys, center fly to the upper-left stairs.
    g.go_to("MT42", 5, 10, "42F 骑士队长剧情")
    g.go_to("MT42", 8, 5, "42F 右侧黄门")
    for pos in [
        (10, 5),
        (10, 4),
        (10, 3),
        (10, 2),
        (9, 2),
        (9, 1),
        (10, 1),
        (11, 1),
        (11, 2),
        (10, 2),
        (10, 3),
        (10, 4),
        (10, 5),
        (10, 6),
        (10, 7),
        (10, 8),
        (10, 9),
        (10, 10),
        (9, 10),
        (9, 11),
        (10, 11),
        (11, 11),
        (11, 10),
    ]:
        g.go_to("MT42", *pos, f"42F 右侧钥匙 {pos}")
    g.go_to("MT42", 11, 10, "42F 回右下中心飞点")
    g.center_fly("42F 右下到左上")
    g.change_by_stair("MT43", 1, 1, "42F 上楼")
    # 43F direct route to 45F.
    g.go_to("MT43", 3, 1, "43F 黄门")
    g.go_to("MT43", 1, 4, "43F 蓝门")
    # 43F x1y11 upFloor jumps straight to 45F in the live game (44F is a
    # pass-through on this column), so model it as a single stair to MT45.
    g.change_by_stair("MT45", 1, 11, "43F 上楼直跳45F")
    g.change_by_stair("MT46", 11, 1, "45F 上楼")
    # With only one 40F blue potion before the 42F half-HP trap, heal before
    # walking through the 46F/47F wizard fields.
    g.fly("MT14")
    g.go_to("MT14", 9, 6, "补 46F/47F 领域用红血瓶")
    g.fly("MT18")
    g.go_to("MT18", 1, 11, "补 46F/47F 领域用红血瓶")
    g.go_to("MT18", 11, 11, "补 46F/47F 回程领域用红血瓶")
    g.fly("MT17")
    g.go_to("MT17", 10, 2, "补 46F/47F 右上往返领域用蓝血瓶")
    g.fly("MT46")
    for pos in [(11, 3), (11, 5), (11, 8)]:
        g.go_to("MT46", *pos, "46F 下侧三黄门")
    g.change_by_stair("MT47", 11, 11, "46F 上楼")
    # 47F guide resources and center fly.
    g.go_to("MT47", 7, 11, "47F 左下黄门")
    g.go_to("MT47", 6, 10, "47F 左侧红宝石")
    g.go_to("MT47", 6, 10, "47F 回中心飞点")
    g.center_fly("47F 左下到右上")
    g.go_to("MT47", 7, 1, "47F 右侧黄门")
    for pos in [(11, 1), (11, 2), (11, 3)]:
        g.go_to("MT47", *pos, f"47F 右侧资源 {pos}")
    g.go_to("MT47", 3, 1, "47F 蓝门")
    g.change_by_stair("MT48", 1, 1, "47F 上楼到48")
    g.fly("MT15")
    g.go_to("MT15", 6, 6, "15F 打章鱼取稿")
    g.go_to("MT15", 6, 5, "15F 拾取稿")
    g.fly("MT48")
    g.use_pickaxe("MT48", 10, 10, "48F 用稿破墙拿圣剑")
    g.go_to("MT48", 8, 10, "48F 圣剑")


def collect_guide_pre_earthquake(g: Game) -> None:
    g.set_segment("pre-earthquake resource loop")
    collect_existing_items(g, "MT40", [(4, 4), (3, 4)], "40F 夹击后延迟蓝血瓶")
    collect_existing_items(g, "MT38", [(11, 11)], "38F guide key")
    collect_existing_items(g, "MT34", [(6, 1), (9, 1), (10, 1), (10, 2), (11, 1)], "34F upper resource")
    collect_existing_items(g, "MT31", [(10, 1), (8, 10), (8, 11)], "31F guide gem")
    collect_existing_items(g, "MT32", [(11, 4), (10, 4)], "32F right key")
    collect_existing_items(g, "MT39", [(11, 6)], "39F red gem")
    collect_existing_items(g, "MT40", [(2, 2)], "40F left reward")


def farm_gold_for_earthquake(g: Game) -> None:
    g.set_segment("gold for earthquake")

    def current_enemy_positions(game: Game) -> set[tuple[str, int, int, str]]:
        return {
            (cfid, cx, cy, cblock.eid)
            for cfid, cfloor in game.floors.items()
            for (cx, cy), cblock in cfloor.blocks.items()
            if cblock.kind == "enemy"
        }

    candidates: list[tuple[int, int, str, int, int, str]] = []
    for fid, floor in g.floors.items():
        if fid not in g.visited:
            continue
        for (x, y), block in floor.blocks.items():
            if block.kind != "enemy":
                continue
            if fid == "MT33" and (x, y) == (7, 10):
                continue
            dmg = g.enemy_damage(block.eid)
            if dmg == float("inf"):
                continue
            money = int(g.enemies[block.eid].get("money", 0))
            if money <= 0:
                continue
            candidates.append((int(dmg), -money, fid, x, y, block.eid))
    candidates.sort()
    # Prefer reachable monsters that do not consume keys, potions, or HP.
    for allow_hp_loss in (False, True):
        for _dmg, _neg_money, fid, x, y, eid in candidates:
            if g.state["gold"] >= 4000:
                return
            block = g.block_at(fid, (x, y))
            if not block or block.kind != "enemy" or block.eid != eid:
                continue
            cand = g.clone()
            try:
                if cand.state["floor"] != fid:
                    cand.fly(fid)
                before = cand.snapshot()
                before_enemies = current_enemy_positions(cand)
                cand.go_to(fid, x, y, f"凑4000G {eid}")
            except RouteError:
                continue
            removed_enemies = before_enemies - current_enemy_positions(cand)
            if removed_enemies != {(fid, x, y, eid)}:
                continue
            if cand.state["yd"] != before["yd"] or cand.state["bd"] != before["bd"] or cand.state["rd"] != before["rd"]:
                continue
            hp_delta = cand.state["hp"] - before["hp"]
            if hp_delta > 0:
                continue
            if not allow_hp_loss and hp_delta < 0:
                continue
            if cand.state["gold"] <= before["gold"]:
                continue
            g.__dict__.update(cand.__dict__)
        if g.state["gold"] >= 4000:
            return
    if g.state["gold"] < 4000:
        g.fail(f"cannot farm enough gold for earthquake, have={g.state['gold']}")


def farm_gold_after_coin(g: Game, target_gold: int, preserve_yk: int = 0, min_floor: int = 1) -> None:
    g.set_segment("post-coin gold cleanup")
    while g.state["gold"] < target_gold:
        trace_point(f"farm_gold_after_coin scan target={target_gold}", g)
        changed = False
        for fid in _visited_floor_ids(g, min_floor):
            result = _simulate_gold_floor_batch(g, fid, target_gold, preserve_yk)
            if result is None:
                continue
            score, chosen = result
            g.__dict__.update(chosen.__dict__)
            changed = True
            trace_point(f"farm_gold_after_coin floor batch {fid} score={score:.1f}", g)
            if g.state["gold"] >= target_gold:
                return
        if not changed:
            g.fail(f"cannot farm post-coin gold to {target_gold}, have={g.state['gold']}")


def _visited_floor_ids(g: Game, min_floor: int = 1) -> list[str]:
    return sorted(
        (fid for fid in g.visited if fid in g.floors and floor_no(fid) >= min_floor),
        key=floor_no,
    )


def _potion_floor_ids(g: Game, min_floor: int = 1) -> list[str]:
    return sorted(
        (fid for fid in g.visited if fid in g.floors and floor_no(fid) >= min_floor),
        key=lambda fid: (-g.floors[fid].ratio, -floor_no(fid)),
    )


def _hp_door_cost(before: dict[str, Any], after: dict[str, Any]) -> int:
    return (
        (after["yd"] - before["yd"]) * 100
        + (after["bd"] - before["bd"]) * 500
        + (after["rd"] - before["rd"]) * 800
    )


def _simulate_gold_floor_batch(g: Game, fid: str, target_gold: int, preserve_yk: int) -> tuple[float, Game] | None:
    cand = g.clone()
    try:
        if cand.state["floor"] != fid:
            cand.fly(fid)
    except RouteError:
        return None

    total_score = 0.0
    while cand.state["gold"] < target_gold:
        best: tuple[float, int, Game] | None = None
        for (x, y), block in list(cand.floors[fid].blocks.items()):
            if block.kind != "enemy":
                continue
            if (fid, x, y) in cand.retreat_wizards:
                continue
            if (fid, x, y) in cand.no_auto_farm:
                continue
            probe = cand.clone()
            try:
                before = probe.snapshot()
                probe.go_to(fid, x, y, f"幸运金币后清怪 {block.eid}")
            except RouteError:
                continue
            gain = probe.state["gold"] - before["gold"]
            if gain <= 0:
                continue
            if probe.state["yk"] < preserve_yk:
                continue
            key_cost = _hp_door_cost(before, probe.snapshot())
            if gain < key_cost:
                continue
            hp_loss = before["hp"] - probe.state["hp"]
            score = gain - key_cost - hp_loss * 0.05
            if score <= 0:
                continue
            if best is None or (score, gain) > (best[0], best[1]):
                best = (float(score), gain, probe)
        if best is None:
            break
        score, _gain, cand = best
        total_score += score

    if cand.state["gold"] <= g.state["gold"]:
        return None
    return total_score, cand


def _simulate_zero_damage_floor_batch(g: Game, fid: str, preserve_yk: int) -> tuple[float, Game] | None:
    cand = g.clone()
    try:
        if cand.state["floor"] != fid:
            cand.fly(fid)
    except RouteError:
        return None

    total_score = 0.0
    while True:
        best: tuple[float, Game] | None = None
        for (x, y), block in list(cand.floors[fid].blocks.items()):
            if block.kind != "enemy":
                continue
            if (fid, x, y) in cand.retreat_wizards:
                continue
            if (fid, x, y) in cand.no_auto_farm:
                continue
            probe = cand.clone()
            try:
                before = probe.snapshot()
                probe.go_to(fid, x, y, f"0伤清怪 {block.eid}")
            except RouteError:
                continue
            gain = probe.state["gold"] - before["gold"]
            if gain <= 0:
                continue
            if before["hp"] - probe.state["hp"] != 0:
                continue
            if probe.state["yk"] < preserve_yk:
                continue
            if probe.state["yd"] != before["yd"] or probe.state["bd"] != before["bd"] or probe.state["rd"] != before["rd"]:
                continue
            score = float(gain)
            if best is None or score > best[0]:
                best = (score, probe)
        if best is None:
            break
        score, cand = best
        total_score += score

    if total_score <= 0:
        return None
    return total_score, cand


def clear_zero_damage_monsters(g: Game, preserve_yk: int = 1, min_floor: int = 1) -> None:
    """Clear EVERY 0-damage, 0-HP-loss, key-neutral monster across the map (lucky
    coin doubles gold). Unlike farm_gold_after_coin this has no money floor, so it
    also sweeps the small skeletons/bats/slimes the guide calls "0血0消耗的怪".
    Stops when no such monster remains. Never raises."""
    g.set_segment("zero-damage monster sweep")
    while True:
        changed = False
        for fid in _visited_floor_ids(g, min_floor):
            result = _simulate_zero_damage_floor_batch(g, fid, preserve_yk)
            if result is None:
                continue
            score, cand = result
            g.__dict__.update(cand.__dict__)
            changed = True
            trace_point(f"zero-damage floor batch {fid} score={score:.1f}", g)
        if not changed:
            return


def eat_accessible_potions(g: Game, target_hp: int, min_floor: int = 1) -> None:
    g.set_segment("post-shield potion cleanup")
    while g.state["hp"] < target_hp:
        best: tuple[int, Game, str] | None = None
        for fid, floor in g.floors.items():
            if fid not in g.visited or floor_no(fid) < min_floor:
                continue
            for (x, y), block in list(floor.blocks.items()):
                if block.kind != "item" or block.eid not in {"redPotion", "bluePotion"}:
                    continue
                cand = g.clone()
                try:
                    if cand.state["floor"] != fid:
                        cand.fly(fid)
                    before = cand.snapshot()
                    cand.go_to(fid, x, y, f"盾后补血 {fid} x{x}y{y}")
                except RouteError:
                    continue
                gain = cand.state["hp"] - before["hp"]
                if gain <= 0:
                    continue
                door_cost = (cand.state["yd"] - before["yd"]) * 100 + (cand.state["bd"] - before["bd"]) * 500 + (cand.state["rd"] - before["rd"]) * 800
                score = gain - door_cost
                if best is None or score > best[0]:
                    best = (score, cand, f"{fid} x{x}y{y}")
        if best is None:
            g.fail(f"cannot eat potions to {target_hp}, have={g.state['hp']}")
        _score, chosen, _desc = best
        g.__dict__.update(chosen.__dict__)


def _potion_sweep(g: Game, min_floor: int, segment: str) -> bool:
    """One greedy pass: pick the best positive-score potion reachable now. Returns
    True if one was eaten. Each pass may spend keys to reach a door-guarded potion."""
    g.set_segment(segment)
    best: tuple[int, Game, str] | None = None
    for fid, floor in g.floors.items():
        if fid not in g.visited or floor_no(fid) < min_floor:
            continue
        for (x, y), block in list(floor.blocks.items()):
            if block.kind != "item" or block.eid not in {"redPotion", "bluePotion"}:
                continue
            cand = g.clone()
            try:
                if cand.state["floor"] != fid:
                    cand.fly(fid)
                before = cand.snapshot()
                cand.go_to(fid, x, y, f"potion {fid} x{x}y{y}")
            except RouteError:
                continue
            gain = cand.state["hp"] - before["hp"]
            if gain <= 0:
                continue
            door_cost = (cand.state["yd"] - before["yd"]) * 100 + (cand.state["bd"] - before["bd"]) * 500 + (cand.state["rd"] - before["rd"]) * 800
            score = gain - door_cost
            if best is None or score > best[0]:
                best = (score, cand, f"{fid} x{x}y{y}")
    if best is None:
        return False
    _score, chosen, _desc = best
    g.__dict__.update(chosen.__dict__)
    return True


def _simulate_potion_floor_batch(g: Game, fid: str, segment: str) -> tuple[float, Game] | None:
    cand = g.clone()
    cand.set_segment(segment)
    try:
        if cand.state["floor"] != fid:
            cand.fly(fid)
    except RouteError:
        return None

    total_score = 0.0
    while True:
        best: tuple[float, int, Game] | None = None
        for (x, y), block in list(cand.floors[fid].blocks.items()):
            if block.kind != "item" or block.eid not in {"redPotion", "bluePotion"}:
                continue
            probe = cand.clone()
            try:
                before = probe.snapshot()
                probe.go_to(fid, x, y, f"potion {fid} x{x}y{y}")
            except RouteError:
                continue
            gain = probe.state["hp"] - before["hp"]
            if gain <= 0:
                continue
            score = gain - _hp_door_cost(before, probe.snapshot())
            if score <= 0:
                continue
            if best is None or (score, gain) > (best[0], best[1]):
                best = (float(score), gain, probe)
        if best is None:
            break
        score, _gain, cand = best
        total_score += score

    if total_score <= 0:
        return None
    return total_score, cand


def _potion_floor_sweep(g: Game, min_floor: int, segment: str) -> bool:
    g.set_segment(segment)
    changed = False
    for fid in _potion_floor_ids(g, min_floor):
        result = _simulate_potion_floor_batch(g, fid, segment)
        if result is None:
            continue
        score, cand = result
        g.__dict__.update(cand.__dict__)
        changed = True
        trace_point(f"potion floor batch {fid} score={score:.1f}", g)
    return changed


def eat_all_reachable_potions(g: Game, min_floor: int = 1) -> None:
    """Repeatedly collect keys then potions until stable. Keys unlock door-guarded
    potions, so the two must be interleaved (guide: 需要钥匙开门的宝石/药水也要拿)."""
    for _ in range(60):
        # Eat every currently-reachable potion (may consume keys).
        while _potion_floor_sweep(g, min_floor, "final potion cleanup"):
            pass
        # Collect any newly-relevant keys so the next potion pass can spend them.
        before_keys = (g.state["yk"], g.state["bk"], g.state["rk"])
        cleanup_reachable_items(g, {"yellowKey", "blueKey", "redKey"}, min_floor=min_floor, preserve_rk=1)
        if (g.state["yk"], g.state["bk"], g.state["rk"]) == before_keys:
            # No new keys gained -> another potion pass that fails means done.
            if not _potion_floor_sweep(g, min_floor, "final potion cleanup"):
                return


def eat_final_yellow_door_potions(g: Game, min_floor: int = 1, preserve_rk: int = 1) -> None:
    """Final HP-leaderboard cleanup: spend leftover yellow keys on potions, but
    keep blue/red doors closed. This is only safe after all yellow-key routing is
    complete."""
    g.set_segment("final yellow-key potion cleanup")
    while True:
        best: tuple[int, Game] | None = None
        for fid in _potion_floor_ids(g, min_floor):
            for (x, y), block in list(g.floors[fid].blocks.items()):
                if block.kind != "item" or block.eid not in {"redPotion", "bluePotion"}:
                    continue
                cand = g.clone()
                try:
                    if cand.state["floor"] != fid:
                        cand.fly(fid)
                    before = cand.snapshot()
                    cand.go_to(fid, x, y, f"final yellow potion {fid} x{x}y{y}")
                except RouteError:
                    continue
                gain = cand.state["hp"] - before["hp"]
                if gain <= 0:
                    continue
                if cand.state["bd"] != before["bd"] or cand.state["rd"] != before["rd"]:
                    continue
                if cand.state["rk"] < preserve_rk:
                    continue
                if best is None or gain > best[0]:
                    best = (gain, cand)
        if best is None:
            return
        gain, chosen = best
        g.__dict__.update(chosen.__dict__)
        trace_point(f"final yellow-key potion gain={gain}", g)


def cleanup_reachable_items(g: Game, item_ids: set[str], min_floor: int = 1, preserve_rk: int = 0) -> None:
    g.set_segment("final resource cleanup")
    while True:
        best: tuple[int, Game, str] | None = None
        for fid, floor in g.floors.items():
            if fid not in g.visited or floor_no(fid) < min_floor:
                continue
            for (x, y), block in list(floor.blocks.items()):
                if block.kind != "item" or block.eid not in item_ids:
                    continue
                cand = g.clone()
                try:
                    if cand.state["floor"] != fid:
                        cand.fly(fid)
                    before = cand.snapshot()
                    cand.go_to(fid, x, y, f"final resource {fid} x{x}y{y}")
                except RouteError:
                    continue
                delta_atk = cand.state["atk"] - before["atk"]
                delta_def = cand.state["def"] - before["def"]
                if cand.state["rk"] < preserve_rk:
                    continue
                delta_keys = (cand.state["yk"] - before["yk"]) * 2 + (cand.state["bk"] - before["bk"]) * 8 + (cand.state["rk"] - before["rk"]) * 20
                door_cost = (cand.state["yd"] - before["yd"]) * 2 + (cand.state["bd"] - before["bd"]) * 8 + (cand.state["rd"] - before["rd"]) * 20
                score = (delta_atk + delta_def) * 1000 + delta_keys * 20 - door_cost
                if best is None or score > best[0]:
                    best = (score, cand, f"{fid} x{x}y{y}")
        if best is None:
            return
        _score, chosen, _desc = best
        g.__dict__.update(chosen.__dict__)


def buy_attack_with_farming(g: Game, count: int) -> None:
    for _ in range(count):
        cost = shop_cost(g.state["times1"])
        if g.state["gold"] < cost:
            if not safe_try(g, farm_gold_after_coin, g, cost, 0, 1):
                eat_accessible_potions(g, max(g.state["hp"], 7000), min_floor=1)
                safe_try(g, farm_gold_after_coin, g, cost, 0, 1)
        if g.state["gold"] < cost:
            break
        if g.state["floor"] != "MT46":
            g.fly("MT46")
        g.go_to("MT46", 6, 2, "46F attack shop")
        g.buy_shop("atk", 1, shop_pos=(6, 1))
        trace_point("buy_attack_with_farming bought atk", g)


def kill_47_retreat_wizards(g: Game) -> None:
    """Corner-trap the 47F retreating redWizards (x8y3 and x1y9). Both retreat
    one tile away from the hero when approached until blocked by wall/door, so a
    direct go_to fails (they flee). Approach from 48F (downFloor lands at x2y1):

      x8y3 wizard: stand at x8y2 (above it). x8y4 yellowDoor (closed) blocks its
        down-retreat, so it stays at x8y3 and is killed directly. Do NOT open
        x8y4 or it flees further and wastes a yellow key.

      x1y9 wizard: walk to x1y8 (above it); it retreats down x1y10 -> x1y11,
        then x1y12 wall blocks it; kill at x1y11.
    """
    g.set_segment("47F retreat-wizard corner trap")
    need_x8 = ("MT47", 8, 3) in g.retreat_wizards and g.block_at("MT47", (8, 3))
    need_x1 = ("MT47", 1, 9) in g.retreat_wizards and g.block_at("MT47", (1, 9))
    if not (need_x8 or need_x1):
        return
    g.fly("MT48")
    g.change_by_stair("MT47", 11, 11, "48F 下楼到47F取后退法师")

    if need_x8:
        # Stand at x8y2 (above the x8y3 wizard). x8y4 door stays closed so the
        # wizard cannot retreat further; kill at x8y3.
        g.go_to("MT47", 8, 2, "47F x8y3法师包围-到x8y2")
        g.go_to("MT47", 8, 3, "47F x8y3法师包围-击杀x8y3")
        g.retreat_wizards.discard(("MT47", 8, 3))

    if need_x1:
        # Walk to x1y8 (above the wizard) via the x1 column top.
        g.go_to("MT47", 1, 8, "47F x1y9法师包围-到x1y8上方")
        # Hero at x1y8 adjacent to wizard x1y9 (below): wizard retreats to x1y10.
        g._move_retreat_wizard("MT47", (1, 9), (1, 10))
        g.go_to("MT47", 1, 9, "47F x1y9法师包围-到x1y9")
        g._move_retreat_wizard("MT47", (1, 10), (1, 11))
        g.go_to("MT47", 1, 10, "47F x1y9法师包围-到x1y10")
        # Wizard now at x1y11, x1y12 wall blocks further retreat -> stays.
        g.go_to("MT47", 1, 11, "47F x1y9法师包围-击杀x1y11")
        g.retreat_wizards.discard(("MT47", 1, 9))


def buy_hp_with_remaining_gold(g: Game, max_count: int = 3) -> None:
    for _ in range(max_count):
        cost = shop_cost(g.state["times1"])
        if g.state["gold"] < cost:
            if not safe_try(g, farm_gold_after_coin, g, cost, 0, 1):
                break
        if g.state["gold"] < cost:
            break
        if g.state["floor"] != "MT46":
            g.fly("MT46")
        g.go_to("MT46", 6, 2, "46F HP shop")
        g.buy_shop("hp", 1, shop_pos=(6, 1))
        trace_point("buy_hp_with_remaining_gold bought hp", g)


def kill_fixed_zero_damage_targets(g: Game, targets: list[tuple[str, int, int]], note: str) -> None:
    g.set_segment(note)
    for fid, x, y in targets:
        block = g.block_at(fid, (x, y))
        if not block or block.kind != "enemy":
            continue
        if g.state["floor"] != fid:
            g.fly(fid)
        before = g.snapshot()
        g.go_to(fid, x, y, f"{note} {fid} x{x}y{y}")
        after = g.snapshot()
        if after["hp"] != before["hp"] or after["dmg"] != before["dmg"]:
            g.fail(f"fixed zero-damage target caused damage at {fid} x{x}y{y}")
        if (after["yd"], after["bd"], after["rd"]) != (before["yd"], before["bd"], before["rd"]):
            g.fail(f"fixed zero-damage target opened a door at {fid} x{x}y{y}")


def final_key_bundle_and_mt20_potions(g: Game) -> None:
    """HP-leaderboard tail cleanup after all stat/HP shops are done.

    The remaining free monsters after the current 21764 route are worth more
    than 1000G with the lucky coin. Spend exactly that on the 31F merchant
    (1000G -> 4YK + 1BK), then open the MT20 right-side blue-door pocket for
    its red+blue potion (+500HP at 11-20F ratio 2).
    """
    g.set_segment("final 31F key bundle + MT20 potions")
    before_gold = g.state["gold"]
    kill_fixed_zero_damage_targets(g, [
        ("MT47", 6, 5),
        ("MT47", 9, 5),
        ("MT47", 9, 3),
        ("MT48", 7, 3),
        ("MT48", 9, 3),
        ("MT48", 7, 5),
        ("MT48", 9, 5),
    ], "final fixed zero-damage gold")
    if g.state["gold"] < 1000:
        clear_zero_damage_monsters(g, preserve_yk=0, min_floor=1)
    trace_point(f"final free-gold sweep gain={g.state['gold'] - before_gold}", g)

    if g.state["gold"] < 1000:
        g.fail(f"not enough gold for 31F key bundle after final sweep: have={g.state['gold']}")
    if not g.flags.get(g.trader_flag("MT31", 1, 11)):
        if g.state["floor"] != "MT31":
            g.fly("MT31")
        g.talk_trader("MT31", 1, 11, "31F 1000G 买4黄1蓝")
    trace_point("final after 31F key bundle", g)

    # Earlier HP routing deliberately blocked the MT20 key/potion pocket so the
    # single blue key could be used for MT48. The bought blue key re-enables it.
    g.blocked_items.discard(("MT20", 11, 5))
    before_hp = g.state["hp"]
    if g.state["floor"] != "MT20":
        g.fly("MT20")
    for pos in [(11, 5), (10, 4), (11, 4)]:
        block = g.block_at("MT20", pos)
        if block and block.kind == "item":
            g.go_to("MT20", *pos, f"20F 蓝门后补血/钥匙 {pos}")
    gained = g.state["hp"] - before_hp
    if gained < 500:
        g.fail(f"MT20 potion cleanup gained only {gained}HP, expected 500HP")
    kill_fixed_zero_damage_targets(g, [("MT20", 11, 7)], "final MT20 zero-damage gold")
    trace_point("final after MT20 potion cleanup", g)


def buy_shops_to_stat(g: Game, kind: str, target_stat: int, note: str, preserve_yk: int = 1) -> None:
    """Buy `kind` (atk/def) shops at MT46 until the stat reaches `target_stat`,
    farming 0-damage-ish monsters (with lucky coin) between purchases. Stops when
    no more gold can be farmed. Mirrors the guide's "def-first then dump atk" plan.
    Farms the WHOLE map (min_floor=1) because the guide collects all positive monsters."""
    stat_key = kind
    while g.state[stat_key] < target_stat:
        cost = shop_cost(g.state["times1"])
        if g.state["gold"] < cost:
            if not safe_try(g, farm_gold_after_coin, g, cost, preserve_yk, 1):
                break
        if g.state["gold"] < cost:
            break
        if g.state["floor"] != "MT46":
            g.fly("MT46")
        g.go_to("MT46", 6, 2, note)
        g.buy_shop(kind, 1, shop_pos=(6, 1))
        trace_point(f"shop {kind} buy toward {target_stat}", g)


def ensure_hp_for_enemy(g: Game, eid: str, margin: int = 1) -> None:
    dmg = g.enemy_damage(eid)
    if dmg == float("inf"):
        g.fail(f"cannot damage required enemy {eid}")
    need = int(dmg) + margin
    if g.state["hp"] <= need:
        eat_accessible_potions(g, need + 1, min_floor=1)


def earthquake_and_shield(g: Game) -> None:
    g.set_segment("earthquake and sacred shield")
    g.fly("MT48")
    g.change_by_stair("MT47", 11, 11, "48F 下楼到47")
    g.talk_trader("MT47", 5, 2, "47F 4000G 买地震卷轴")
    g.fly("MT37")
    g.use_earthquake("37F 炸墙拿关键资源")
    for pos, block in list(g.floors["MT37"].blocks.items()):
        if block.kind == "item" and block.eid in {"redPotion", "bluePotion"}:
            g.blocked_items.add(("MT37", pos[0], pos[1]))
    collect_existing_items(g, "MT37", [
        (5, 4),
        (3, 5),
        (4, 5),
        (5, 5),
        (7, 5),
        (8, 5),
        (9, 5),
        (3, 7),
        (4, 7),
        (7, 7),
        (8, 7),
        (9, 7),
        (3, 8),
        (4, 8),
        (5, 8),
        (7, 8),
        (8, 8),
        (9, 8),
        (4, 9),
        (5, 9),
        (8, 9),
    ], "37F non-potion resource")
    g.fly("MT45")
    # Lower-left upFly route: red door and paired dark knights open the special door.
    for pos in [(6, 2), (6, 6), (4, 7), (2, 8), (2, 10)]:
        g.go_to("MT45", *pos, f"45F 上楼器路线 {pos}")
    # Fly use must be connected to a stair side; walking back through the middle
    # corridor applies the remaining wizard-field damage that the web game shows.
    g.go_to("MT45", 2, 1, "45F 回到楼梯边再飞")
    g.fly("MT43")
    g.up_fly("43F 使用上楼器到44")
    g.go_to("MT44", 6, 9, "44F 卫兵中间")
    g.use_bomb("44F 炸双卫兵")
    for pos in [(6, 8), (6, 7), (6, 6), (5, 6), (7, 6), (6, 5)]:
        safe_try(g, g.go_to, "MT44", *pos, f"44F shield/potions {pos}")
    g.go_to("MT44", 1, 2, "44F 回到楼梯边再飞")
    g.blocked_items.clear()


def post_shield_49(g: Game) -> None:
    g.set_segment("post-shield to 49 boss")
    g.fly("MT43")
    g.go_to("MT43", 3, 1, "43F 左上黄门")
    for pos in [(3, 6), (8, 6), (11, 5)]:
        g.go_to("MT43", *pos, f"43F 中路绕右上 {pos}")
    g.go_to("MT43", 9, 1, "43F 右侧打右上警卫")
    g.go_to("MT43", 9, 4, "43F 圣盾")
    g.go_to("MT43", 11, 11, "43F 右下蓝钥匙")
    g.fly("MT46")
    g.go_to("MT46", 3, 8, "46F 魔法钥匙")
    g.fly("MT41")
    g.use_big_key("41F 开全层黄门")
    g.go_to("MT41", 5, 6, "41F 左蓝门")
    g.go_to("MT41", 2, 2, "41F 左上红巫师")
    g.go_to("MT41", 4, 1, "41F 左上蓝钥匙")
    g.go_to("MT41", 7, 6, "41F 右蓝门")
    g.go_to("MT41", 9, 2, "41F 右上撞墙前")
    g.go_to("MT41", 10, 2, "41F 右上红巫师")
    g.fly("MT40")
    g.fly("MT41")
    g.go_to("MT41", 6, 5, "41F 下楼器")
    for pos in [(3, 10), (4, 10), (3, 11), (4, 11), (8, 10), (9, 10), (8, 11), (9, 11)]:
        safe_try(g, g.go_to, "MT41", *pos, f"41F magic-key opened resource {pos}")
    trace_point("post_shield_49 after 41F magic-key resources", g)
    g.fly("MT1")
    g.down_fly("1F 下楼器到0F")
    # MT0 map is not in local data. The downFly lands at x2y1 but the lucky coin
    # (coin) is at x6y6 on the live 0F map. Record the hero walking to x6y6 and
    # picking it up; the replayer clicks x6y6 and the game auto-routes there.
    before = g.snapshot()
    g.state["x"], g.state["y"] = 6, 6
    g.state["coin"] = True
    g.record("拾取", (6, 6), "coin", before, "0F 幸运金币 x6y6")
    trace_point("post_shield_49 after lucky coin", g)
    # --- Guide step 9: def-first shops so普通怪 become 0-damage, then dump atk ---
    # DEF >= 430 makes darkKnight/redBat/redWizard etc. 0-damage for free farming.
    buy_shops_to_stat(g, "def", 430, "46F def-first 商店", preserve_yk=1)
    trace_point("post_shield_49 after def-first shops", g)
    # Kill the 47F x1y9 retreating redWizard by corner-trapping it: approach from
    # above so it retreats down to x1y11 (wall), then kill at x1y11. The x8y2
    # redWizard already retreated to x8y3 (x8y4 door blocks) so a direct kill works.
    kill_47_retreat_wizards(g)
    trace_point("post_shield_49 after retreat wizards", g)
    # Sweep 0-damage monsters + collect gems/keys once before 49F boss. The money
    # filter in farm_gold_after_coin is already removed, so later gold-buying will
    # naturally pick up low-gold monsters too. Don't over-sweep: leave yk-costing
    # monsters for post-49F gold extraction.
    clear_zero_damage_monsters(g, preserve_yk=1, min_floor=1)
    trace_point("post_shield_49 after zero-damage sweep", g)
    # HP objective: keep this blue key for MT48. The MT20 blue-door group is
    # only 500HP + 1YK, while the second MT48 blue door opens 3 red potions
    # worth 750HP on ratio 5.
    g.blocked_items.add(("MT20", 11, 5))
    cleanup_reachable_items(g, {"redGem", "blueGem", "yellowKey", "blueKey", "redKey"},
                            min_floor=1, preserve_rk=1)
    trace_point("post_shield_49 after resource cleanup", g)
    # Collect 45F left gems (now safe) and any 0-damage monsters farmed along the way.
    g.fly("MT45")
    for pos in [(1, 3), (2, 3), (1, 5), (2, 5)]:
        safe_try(g, g.go_to, "MT45", *pos, f"45F left gem {pos}")
    # Dump remaining gold into ATK before 49F. For HP leaderboard, stop at 291:
    # the saved shop buys can fund late HP, while the final boss turn count
    # remains acceptable after sword5 and blessing.
    # reserved: the 45F 2000HP merchant path needs yellow doors.
    buy_shops_to_stat(g, "atk", 291, "46F atk 商店", preserve_yk=1)
    trace_point("post_shield_49 after atk shops", g)
    # 45F 1000G -> 2000HP merchant (guide step 12); farm a bit more if just short.
    if g.state["gold"] < 1000:
        safe_try(g, farm_gold_after_coin, g, 1000, 0, 1)
    if g.state["floor"] != "MT45":
        g.fly("MT45")
    if g.state["gold"] >= 1000 and not g.flags.get(g.trader_flag("MT45", 9, 3)):
        g.talk_trader("MT45", 9, 3, "45F 1000G 买2000血")
    trace_point("post_shield_49 after 45F HP merchant", g)
    # Eat ALL reachable potions before 49F (guide eats everything once traps are off).
    eat_all_reachable_potions(g, min_floor=1)
    trace_point("post_shield_49 after potion sweep", g)
    g.fly("MT41")
    g.fly("MT42")
    g.go_to("MT42", 7, 1, "42F 补49F红门用红钥匙")
    g.fly("MT48")
    g.change_by_stair("MT49", 1, 11, "48F 上楼到49")
    g.go_to("MT49", 3, 11, "49F 红门")
    for pos in [(5, 10), (7, 10), (6, 9), (5, 8), (7, 8), (6, 7)]:
        g.go_to("MT49", *pos, f"49F 开Boss前机关 {pos}")
    g.go_to("MT49", 6, 6, "49F boss事件")
    # Event creates the 8 guards and redKing.
    for p in [(5, 2), (5, 3), (5, 4), (6, 4), (7, 4), (7, 3), (7, 2), (6, 2)]:
        g.set_block("MT49", p, "enemy", "whiteKing", 246)
    g.set_block("MT49", (6, 3), "enemy", "redKing", 245)
    # Kill the 4 cardinal guards FIRST (x6y2,x5y3,x7y3,x6y4) to break the seal
    # (redKing 8000hp/5000atk/1000def -> 800/500/100). The 4 corner guards would
    # be path-killed en route and break the order, so mark them no-path-kill while
    # killing cardinals; the live game auto-routes around them just the same.
    corners = {("MT49", 5, 2), ("MT49", 7, 2), ("MT49", 5, 4), ("MT49", 7, 4)}
    g.retreat_wizards |= corners
    for pos in [(6, 2), (5, 3), (7, 3), (6, 4)]:
        g.go_to("MT49", *pos, f"49F boss 十字守卫 {pos}")
    g.flags["49sealed"] = True
    g.retreat_wizards -= corners
    # Now the 4 corner guards (for gold), then redKing.
    for pos in [(5, 2), (7, 2), (5, 4), (7, 4), (6, 3)]:
        g.go_to("MT49", *pos, f"49F boss 角守卫/魔王 {pos}")
    for pos in [(5, 2), (7, 2), (2, 4), (3, 4), (4, 4), (8, 4), (9, 4), (10, 4), (5, 5), (6, 5), (7, 5)]:
        safe_try(g, g.go_to, "MT49", *pos, f"49F reward {pos}")
    trace_point("post_shield_49 after 49F boss", g)


def post_49_endgame(g: Game) -> None:
    """Guide steps 10-12 in exact order:

      10. 49F boss guards + redKing, then 46F buy def.
      11. 35F dragon + snow, 13F sword via snow, 46F buy def (DEF=542),
          2F bless trader (ATK=439 DEF=558), 25F red door + blackMagician (68 dmg).
      12. 25F red keys, 26F princess, 45F 1000G->2000HP, eat 16F superPotion,
          24F -> 50F final boss.
    """
    g.set_segment("post-49 endgame setup")
    cleanup_reachable_items(g, {"redGem", "blueGem", "yellowKey", "blueKey"}, min_floor=1, preserve_rk=1)
    # Traps are off after the 44F sacred shield -> eat ALL potions early so the
    # superPotion (16F 圣水) at step 12 multiplies a larger HP base, matching the
    # guide's ~31445 HP before the final boss sequence.
    eat_all_reachable_potions(g, min_floor=1)
    trace_point("post_49 after initial cleanup/potions", g)

    # Do not buy post-49 attack here: 49F reward + 13F sword5 already reaches
    # the guide's ATK426 before blessing; the saved gold is worth more as DEF.
    trace_point("post_49 after skipping extra attack buys", g)
    cleanup_reachable_items(g, {"redGem", "blueGem", "yellowKey", "blueKey"}, min_floor=1, preserve_rk=1)
    if g.state["yk"] <= 0:
        cleanup_reachable_items(g, {"yellowKey"}, min_floor=1, preserve_rk=1)
    trace_point("post_49 after gem/key cleanup", g)

    # --- Step 11a: 35F dragon + snow (picks up snow tool) ---
    ensure_hp_for_enemy(g, "magicDragon", 20)
    g.fly("MT35")
    g.go_to("MT35", 6, 7, "35F 魔龙")
    g.go_to("MT35", 6, 6, "35F 雪花")
    for pos in [(5, 5), (6, 5), (7, 5)]:
        safe_try(g, g.go_to, "MT35", *pos, f"35F 魔龙后蓝血瓶 {pos}")
    trace_point("post_49 after 35F dragon/snow", g)

    # --- Step 11b: 13F sword5 via snow ---
    g.fly("MT13")
    g.go_to("MT13", 6, 10, "13F 神圣剑黄门")
    # Opening the door leaves the hero on the adjacent tile (x6y11) in the live
    # game; walk onto x6y10 (now open ground) so snow can freeze the x6y9 lava
    # below. Record an explicit ARRIVE so the replayer clicks x6y10 to step on.
    g.state["x"], g.state["y"] = 6, 11  # match live post-door position
    g.go_to("MT13", 6, 10, "13F 走到熔岩口 x6y10")
    for y in [9, 8, 7, 6]:
        g.use_snow("13F 冻结熔岩拿神圣剑")
        g.go_to("MT13", 6, y, f"13F 熔岩通路 y{y}")
    g.go_to("MT13", 6, 5, "13F 神圣剑")
    cleanup_reachable_items(g, {"redGem", "blueGem"}, min_floor=1, preserve_rk=1)
    trace_point("post_49 after 13F sword5", g)

    # --- Step 11c: 46F buy def. For HP leaderboard, skip the late DEF buys:
    # the saved gold can buy late HP shops, while DEF remains above the final
    # threshold after the 2F blessing.
    buy_shops_to_stat(g, "def", 502, "46F endgame def 商店", preserve_yk=1)
    trace_point("post_49 after endgame def shops", g)

    # --- Step 11d: 2F bless trader (+3% atk/def -> ATK439 DEF558) ---
    g.fly("MT2")
    g.talk_mt2_bless()
    trace_point("post_49 after 2F bless", g)

    # --- Step 11e: 16F superPotion pickup (圣水), held for use at step 12 ---
    g.fly("MT16")
    g.talk_mt16_oldman()
    trace_point("post_49 after 16F superPotion pickup", g)

    # --- Step 11f: 25F red door + blackMagician (now DEF558 -> 68 dmg) ---
    ensure_hp_for_enemy(g, "blackMagician", 20)
    g.fly("MT25")
    g.go_to("MT25", 6, 10, "25F 红门")
    # The x6y9 "none" event must be triggered first (opens the path to x6y6).
    g.go_to("MT25", 6, 9, "25F x6y9 机关触发")
    g.go_to("MT25", 6, 6, "25F 黑衣魔法师")
    for pos in [(4, 8), (5, 8), (7, 8), (8, 8)]:
        g.go_to("MT25", *pos, f"25F 红钥匙 {pos}")
    trace_point("post_49 after 25F blackMagician", g)

    # --- Step 12a: 26F princess ---
    g.fly("MT26")
    for y in [10, 9, 8]:
        g.go_to("MT26", 6, y, f"26F 公主红门 y{y}")
    g.use_snow("26F 冻结公主前熔岩")
    g.go_to("MT26", 6, 7, "26F 公主前")
    g.talk_mt26_princess()
    trace_point("post_49 after 26F princess", g)

    # --- Step 12b: 45F 1000G -> 2000HP merchant ---
    if g.state["gold"] < 1000:
        safe_try(g, farm_gold_after_coin, g, 1000, 0, 1)
    if g.state["floor"] != "MT45":
        g.fly("MT45")
    if g.state["gold"] >= 1000 and not g.flags.get(g.trader_flag("MT45", 9, 3)):
        g.talk_trader("MT45", 9, 3, "45F 1000G 买2000血")
    trace_point("post_49 after 45F HP merchant", g)

    # --- Step 12c: eat remaining potions, then use the 16F superPotion ---
    buy_hp_with_remaining_gold(g, 4)
    final_key_bundle_and_mt20_potions(g)
    eat_all_reachable_potions(g, min_floor=1)
    eat_final_yellow_door_potions(g, min_floor=1, preserve_rk=1)
    if g.state["superPotion"] > 0:
        g.use_super_potion("最终前圣水")
    trace_point("post_49 after final HP/potions/superPotion", g)

    # --- Step 12d: 24F -> 50F final boss ---
    g.fly("MT24")
    g.go_to("MT24", 6, 8, "24F 红门")
    g.trigger_mt24_to_mt50()
    g.trigger_mt50_final()
    trace_point("post_49 after 50F final boss", g)


def _trace_stage(trace: bool, name: str, when: str, g: Game) -> None:
    if not trace:
        return
    print(
        f"[{when}] {name}: {state_line(g.state)} "
        f"{g.state['floor']} x{g.state['x']}y{g.state['y']} "
        f"dmg={g.state['dmg']} door={g.state['yd']}/{g.state['bd']}/{g.state['rd']} "
        f"steps={len(g.steps)}",
        flush=True,
    )


def run_guide_probe(trace: bool = False, stop_after: str | None = None) -> Game:
    global TRACE_ENABLED
    TRACE_ENABLED = trace
    g = Game(read_json(SNAPSHOT))
    stages = [
        ("prefix48", guide_prefix_to_48_visit),
        ("pre_earthquake", collect_guide_pre_earthquake),
        ("farm_earthquake", farm_gold_for_earthquake),
        ("shield", earthquake_and_shield),
        ("post_shield_49", post_shield_49),
        ("post_49_endgame", post_49_endgame),
    ]
    try:
        for name, fn in stages:
            _trace_stage(trace, name, "start", g)
            fn(g)
            _trace_stage(trace, name, "end", g)
            if stop_after == name:
                break
    except RouteError:
        pass
    return g


def write_outputs(g: Game) -> None:
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(
        json.dumps({"ok": not g.errors, "final": g.snapshot(), "errors": g.errors, "steps": g.steps}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    lines = [
        "# 40F Boss 后攻略骨架探测",
        "",
        f"- 结果：{'通过' if not g.errors else '未通过'}",
        f"- 当前状态：{state_line(g.state)} {g.state['floor']} x{g.state['x']}y{g.state['y']}",
        f"- 累计损失：{g.state['dmg']}；开门 黄/蓝/红={g.state['yd']}/{g.state['bd']}/{g.state['rd']}",
        "",
    ]
    if g.errors:
        lines.append("## 停止原因")
        lines.extend(f"- {e}" for e in g.errors)
        lines.append("")
    lines.append("## Walk")
    for i, step in enumerate(g.steps, 1):
        pos = step["pos"]
        eid = ITEM_CN.get(step.get("eid") or "", step.get("eid") or "")
        delta = f" [{step['delta']}]" if step.get("delta") else ""
        note = f" ({step['note']})" if step.get("note") else ""
        lines.append(f"{i:03d}. {step['segment']} - {step['floor']} x{pos[0]}y{pos[1]} {step['action']} {eid}{delta}{note}".rstrip())
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", action="store_true", help="print state before and after each route stage")
    parser.add_argument("--stop-after", choices=STAGE_NAMES, help="stop after the named stage")
    parser.add_argument("--no-write", action="store_true", help="do not update output artifacts")
    args = parser.parse_args()

    g = run_guide_probe(trace=args.trace, stop_after=args.stop_after)
    if not args.no_write:
        write_outputs(g)
    print(f"ok={not g.errors}")
    print(f"final={state_line(g.state)} {g.state['floor']} x{g.state['x']}y{g.state['y']} dmg={g.state['dmg']} door={g.state['yd']}/{g.state['bd']}/{g.state['rd']}")
    if g.errors:
        print("errors:")
        for error in g.errors:
            print("-", error)
        if not args.no_write:
            print(f"json={OUT_JSON}")
            print(f"md={OUT_MD}")
        return 1
    if not args.no_write:
        print(f"json={OUT_JSON}")
        print(f"md={OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
