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
STAGE_LABELS = {
    "prefix48": "4区起点到48F",
    "pre_earthquake": "地震卷轴前资源",
    "farm_earthquake": "凑地震卷轴金币",
    "shield": "地震卷轴与神圣盾",
    "post_shield_49": "圣盾后到49F假魔王",
    "post_49_endgame": "49F后魔龙雪花到真魔王",
    "post_shield_no49": "圣盾后TE准备(不打49F,留downFly)",
    "late49_endgame": "TE晚49:救公主→50F小偷→49F封印→50F封印真魔王",
}
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
    "sword1": "铁剑",
    "shield1": "铁盾",
    "sword2": "银剑",
    "shield2": "银盾",
    "sword3": "骑士剑",
    "shield3": "骑士盾",
    "sword4": "圣剑",
    "shield4": "圣盾",
    "sword5": "神圣剑",
    "shield5": "神圣盾",
    "bigKey": "魔法钥匙",
    "upFly": "上楼器",
    "downFly": "下楼器",
    "coin": "幸运金币",
    "earthquake": "地震卷轴",
    "bomb": "炸弹",
    "centerFly": "中心对称飞行器",
    "cross": "十字架",
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


def stock_score(s: dict[str, Any]) -> float:
    return s["hp"] + s["yk"] * 50 + s["bk"] * 200 + s["gold"] * 0.5


def stage_resource_text(s: dict[str, Any]) -> str:
    parts = []
    for key, label in [
        ("earthquake", "地震卷轴"),
        ("coin", "双倍金币"),
        ("magicImmune", "魔免"),
        ("snow", "雪花"),
        ("knife", "屠龙匕首"),
        ("superPotion", "圣水"),
        ("won49", "49F封印"),
        ("won50", "50F真魔王"),
    ]:
        value = s.get(key)
        if isinstance(value, bool):
            if value:
                parts.append(label)
        elif value:
            parts.append(f"{label}={value}")
    return "，".join(parts) or "-"


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
        self.stage_summaries: list[dict[str, Any]] = []
        self.errors: list[str] = []
        self.segment = "start"
        self.flags: dict[str, Any] = dict(flags)
        auto = flags.get("__auto__", {}) if isinstance(flags.get("__auto__", {}), dict) else {}
        self.auto_flags: dict[str, Any] = {
            "battle": auto.get("battle", False) is True,
            "item": auto.get("item", False),
            "wall": auto.get("wall", False) is True,
        }
        self.strict_live_model = False
        self._pending_auto_before: dict[str, Any] | None = None
        self._pending_auto_trigger = ""
        self._next_record_before: dict[str, Any] | None = None
        self._next_record_note = ""
        # Mechanism-door timing: in live, killing a guard opens its mechanism
        # door AFTER the post-battle auto-BFS runs, and "opening a door does not
        # trigger BFS" -- so items behind the door are NOT auto-picked by the
        # post-battle sweep. To match this, when go_to kills an enemy we defer
        # after_action's block mutations (set_ground/set_block: door opens, item
        # spawns) until AFTER the post-battle auto_sweep, then apply them with no
        # second sweep. Flag updates stay immediate so guard counters still work.
        self._defer_after_action = False
        self._capturing = False
        self._captured: list[tuple] = []
        self._deferred_after_effects: list[tuple] = []
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

    def delta_text(self, before: dict[str, Any], after: dict[str, Any] | None = None) -> str:
        after = after or self.snapshot()
        delta = []
        for key, label in [("hp", "HP"), ("atk", "ATK"), ("def", "DEF"), ("yk", "YK"), ("bk", "BK"), ("rk", "RK"), ("gold", "G")]:
            if before[key] != after[key]:
                delta.append(f"{label} {before[key]}->{after[key]}")
        return ", ".join(delta)

    def record(self, action: str, pos: tuple[int, int] | None, eid: str | None, before: dict[str, Any], note: str = "") -> None:
        if self._next_record_before is not None:
            before = self._next_record_before
            if self._next_record_note:
                note = f"{self._next_record_note}; {note}" if note else self._next_record_note
            self._next_record_before = None
            self._next_record_note = ""
        after = self.snapshot()
        delta = self.delta_text(before, after)
        self.steps.append(
            {
                "segment": self.segment,
                "floor": after["floor"],
                "pos": list(pos or (after["x"], after["y"])),
                "action": action,
                "eid": eid,
                "before": before,
                "after": after,
                "delta": delta,
                "note": note,
            }
        )

    def refresh_last_step(self, before: dict[str, Any], note_suffix: str = "") -> None:
        if not self.steps:
            return
        after = self.snapshot()
        step = self.steps[-1]
        step["after"] = after
        step["delta"] = self.delta_text(before, after)
        if note_suffix:
            step["note"] = f"{step.get('note')}; {note_suffix}" if step.get("note") else note_suffix

    def floor(self, fid: str | None = None) -> Floor:
        return self.floors[fid or self.state["floor"]]

    def block_at(self, fid: str, pos: tuple[int, int]) -> Block | None:
        return self.floors[fid].blocks.get(pos)

    def set_ground(self, fid: str, pos: tuple[int, int]) -> None:
        if self._capturing:
            self._captured.append(("set_ground", fid, pos))
            return
        f = self.floors[fid]
        x, y = pos
        if 0 <= y < f.height and 0 <= x < f.width:
            f.grid[y][x] = 0
        f.blocks.pop(pos, None)

    def set_block(self, fid: str, pos: tuple[int, int], kind: str, eid: str, tile: int = 0) -> None:
        if self._capturing:
            self._captured.append(("set_block", fid, pos, kind, eid, tile))
            return
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
            # breaks the seal.  In the TE late-49 flow the 50F thief was talked
            # to first, so the fake redKing was boosted to 5000/1580/190 and the
            # seal drops it to 500/158/19 (1/10).  In NE (no 50F thief) the
            # unboosted fake redKing seals to 800/500/100.
            if self.flags.get("50thief"):
                enemy = {**enemy, "hp": 500, "atk": 158, "def": 19}
            else:
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
            # fakeWall/fakeWall2 are noPass in live (core.noPass=true): the
            # auto-route BFS skips them as intermediate tiles. They are only
            # reachable as the click target (hero stops adjacent, the wall
            # breaks). Stairs are target-only by design (avoid routing through
            # floor-change triggers). flower stays passable (one-way logic in
            # go_to via can_enter_flower).
            if block.eid in {"fakeWall", "fakeWall2"} or block.eid in STAIRS:
                return pos == target
            if block.eid == "flower":
                return True
            return False
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

    def can_enter_click_path(self, fid: str, pos: tuple[int, int], target: tuple[int, int]) -> bool:
        """Passability for one real map click in strict live mode.

        A live click may end on an actionable target, but it does not route
        through unopened doors or live enemies to reach something behind them.
        Intermediate pickups are allowed because walking over an item is normal
        movement.
        """

        if pos == target:
            return self.can_enter(fid, pos, target)
        if self.is_wall(fid, pos):
            return False
        block = self.block_at(fid, pos)
        if not block:
            return True
        if block.kind == "item":
            return (fid, pos[0], pos[1]) not in self.blocked_items
        return False

    @staticmethod
    def _auto_item_allowed(eid: str, item_mode: Any) -> bool:
        if item_mode is True:
            return True
        if item_mode == "nopotion":
            return eid not in {"redPotion", "bluePotion"}
        return False

    def _auto_cell_passable(
        self,
        fid: str,
        pos: tuple[int, int],
        *,
        battle: bool,
        item_mode: Any,
        wall: bool,
    ) -> bool:
        f = self.floors[fid]
        x, y = pos
        if x < 0 or y < 0 or x >= f.width or y >= f.height:
            return False
        block = self.block_at(fid, pos)
        if not block:
            return True
        if block.kind == "terrain":
            return block.eid in {"fakeWall", "fakeWall2", "flower"} and wall
        if block.kind == "item":
            if (fid, pos[0], pos[1]) in self.blocked_items:
                return False
            return self._auto_item_allowed(block.eid, item_mode)
        if block.kind == "enemy" and battle:
            if (fid, pos[0], pos[1]) in self.retreat_wizards:
                return False
            if (fid, pos[0], pos[1]) in self.no_auto_farm:
                return False
            return self.enemy_damage(block.eid) == 0
        return False

    def _auto_reachable(
        self,
        fid: str,
        *,
        battle: bool,
        item_mode: Any,
        wall: bool,
    ) -> dict[tuple[int, int], int]:
        start = (self.state["x"], self.state["y"])
        f = self.floors[fid]
        if start[0] < 0 or start[1] < 0 or start[0] >= f.width or start[1] >= f.height:
            return {}
        seen = {start: 0}
        queue = [start]
        for cur in queue:
            cx, cy = cur
            for nxt in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                if nxt in seen:
                    continue
                if not self._auto_cell_passable(fid, nxt, battle=battle, item_mode=item_mode, wall=wall):
                    continue
                seen[nxt] = seen[cur] + 1
                queue.append(nxt)
        return seen

    def _auto_item_candidates(
        self,
        fid: str,
        *,
        battle: bool,
        item_mode: Any,
        wall: bool,
    ) -> list[tuple[int, int, tuple[int, int], Block]]:
        reach = self._auto_reachable(fid, battle=battle, item_mode=item_mode, wall=wall)
        out: list[tuple[int, int, tuple[int, int], Block]] = []
        for pos, block in self.floors[fid].blocks.items():
            if block.kind != "item":
                continue
            if pos not in reach:
                continue
            if not self._auto_item_allowed(block.eid, item_mode):
                continue
            if (fid, pos[0], pos[1]) in self.blocked_items:
                continue
            out.append((reach[pos], pos[1], pos, block))
        out.sort()
        return out

    def _auto_enemy_candidates(
        self,
        fid: str,
        *,
        battle: bool,
        item_mode: Any,
        wall: bool,
    ) -> list[tuple[int, int, tuple[int, int], Block]]:
        reach = self._auto_reachable(fid, battle=battle, item_mode=item_mode, wall=wall)
        out: list[tuple[int, int, tuple[int, int], Block]] = []
        for pos, block in self.floors[fid].blocks.items():
            if block.kind != "enemy":
                continue
            if (fid, pos[0], pos[1]) in self.retreat_wizards:
                continue
            if (fid, pos[0], pos[1]) in self.no_auto_farm:
                continue
            dmg = self.enemy_damage(block.eid)
            if dmg != 0:
                continue
            x, y = pos
            adjacent = [
                reach[(x + dx, y + dy)]
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                if (x + dx, y + dy) in reach
            ]
            if not adjacent:
                continue
            out.append((min(adjacent) + 1, pos[1], pos, block))
        out.sort()
        return out

    def _auto_wall_candidates(
        self,
        fid: str,
        *,
        battle: bool,
        item_mode: Any,
        wall: bool,
    ) -> list[tuple[int, int, tuple[int, int], Block]]:
        # Reachable fakeWall/fakeWall2 (live core.plugin.auto with wall=true
        # BFSes through them and breaks them). _auto_cell_passable treats
        # fakeWall as passable when wall=true, so they appear in reach.
        if not wall:
            return []
        reach = self._auto_reachable(fid, battle=battle, item_mode=item_mode, wall=wall)
        out: list[tuple[int, int, tuple[int, int], Block]] = []
        for pos, block in self.floors[fid].blocks.items():
            if block.kind != "terrain" or block.eid not in {"fakeWall", "fakeWall2"}:
                continue
            if pos not in reach:
                continue
            out.append((reach[pos], pos[1], pos, block))
        out.sort()
        return out

    def auto_sweep(
        self,
        fid: str | None = None,
        *,
        battle: bool | None = None,
        item: Any = None,
        wall: bool | None = None,
        max_rounds: int = 200,
    ) -> list[str]:
        """Apply h5mota-style automatic pickup / zero-damage cleanup on one floor.

        This has no final-position side effect: live automatic BFS may animate
        through resources, but the observable route checkpoint remains the tile
        that triggered the automatic handling. Doors are deliberately not opened
        here; opening a door and stepping into the opened cell are separate
        player actions.
        """

        fid = fid or self.state["floor"]
        if fid != self.state["floor"] or fid not in self.floors:
            return []
        if battle is None:
            battle = bool(self.auto_flags.get("battle"))
        if item is None:
            item = self.auto_flags.get("item")
        if wall is None:
            wall = bool(self.auto_flags.get("wall"))
        if not battle and not item and not wall:
            return []

        handled: list[str] = []
        for _ in range(max_rounds):
            changed = False
            if wall:
                # Break reachable fakeWalls first so the area behind them opens
                # up for item pickup / zero-damage battle in the same sweep.
                wall_candidates = self._auto_wall_candidates(fid, battle=battle, item_mode=item, wall=wall)
                if wall_candidates:
                    for _dist, _y, pos, block in wall_candidates:
                        live = self.block_at(fid, pos)
                        if not live or live.kind != "terrain" or live.eid not in {"fakeWall", "fakeWall2"}:
                            continue
                        self.set_ground(fid, pos)
                        self.after_action(fid, pos, live)
                        handled.append(f"x{pos[0]}y{pos[1]} {live.eid}")
                        changed = True
                    if changed:
                        continue
            if item:
                item_candidates = self._auto_item_candidates(fid, battle=battle, item_mode=item, wall=wall)
                if item_candidates:
                    for _dist, _y, pos, block in item_candidates:
                        live = self.block_at(fid, pos)
                        if not live or live.kind != "item" or live.eid != block.eid:
                            continue
                        self.apply_item(fid, live.eid)
                        self.set_ground(fid, pos)
                        self.after_action(fid, pos, live)
                        handled.append(f"x{pos[0]}y{pos[1]} {live.eid}")
                        changed = True
                    if changed:
                        continue
            if battle:
                enemy_candidates = self._auto_enemy_candidates(fid, battle=battle, item_mode=item, wall=wall)
                if enemy_candidates:
                    for _dist, _y, pos, block in enemy_candidates:
                        live = self.block_at(fid, pos)
                        if not live or live.kind != "enemy" or live.eid != block.eid:
                            continue
                        dmg = self.enemy_damage(live.eid)
                        if dmg != 0:
                            continue
                        gain = int(self.enemies[live.eid].get("money", 0))
                        if self.state.get("coin"):
                            gain *= 2
                        self.state["gold"] += gain
                        self.set_ground(fid, pos)
                        self.after_action(fid, pos, live)
                        handled.append(f"x{pos[0]}y{pos[1]} {live.eid}")
                        changed = True
                    if changed:
                        continue
            if not changed:
                break
        return handled

    def refresh_last_step_with_auto(self, before: dict[str, Any], handled: list[str], trigger: str = "live auto") -> None:
        if not handled:
            return
        self.refresh_last_step(before, f"{trigger}: " + ", ".join(handled))

    def _arm_auto_after_opened_door(self, after_door: dict[str, Any], door_pos: tuple[int, int]) -> None:
        self._pending_auto_before = after_door
        self._pending_auto_trigger = f"经过已开门格 x{door_pos[0]}y{door_pos[1]}触发自动处理"

    def _consume_pending_auto_for_next_record(self, fid: str) -> None:
        if self._pending_auto_before is None:
            return
        before = self._pending_auto_before
        trigger = self._pending_auto_trigger or "自动处理"
        self._pending_auto_before = None
        self._pending_auto_trigger = ""
        handled = self.auto_sweep(fid)
        self._next_record_before = before
        self._next_record_note = f"{trigger}: " + ", ".join(handled) if handled else trigger

    def _apply_door_live(self, fid: str, pos: tuple[int, int], block: Block, note: str = "") -> None:
        before = self.snapshot()
        if block.eid == "yellowDoor":
            self.state["yk"] -= 1
            self.state["yd"] += 1
        elif block.eid == "blueDoor":
            self.state["bk"] -= 1
            self.state["bd"] += 1
        elif block.eid == "redDoor":
            self.state["rk"] -= 1
            self.state["rd"] += 1
        else:
            self.fail(f"unmodeled live door {block.eid} at {fid} x{pos[0]}y{pos[1]}")
        if self.state["yk"] < 0 or self.state["bk"] < 0 or self.state["rk"] < 0:
            self.fail(f"negative key after door {block.eid} at {fid} {pos}")
        self.set_ground(fid, pos)
        self.after_action(fid, pos, block)
        door_note = "到门前开门，不触发自动BFS"
        full_note = f"{note}; {door_note}" if note else door_note
        self.record("开门", pos, block.eid, before, full_note)

    def path_cost(self, fid: str, pos: tuple[int, int]) -> int:
        # Align with h5mota `_automaticRoute_deepAdd`: empty/item/fakeWall all
        # cost 1 (items are NOT avoided -- the route may pass through and pick
        # them up as side effects); magic-damage cells add damage*100.
        block = self.block_at(fid, pos)
        base = 1
        if block:
            if block.kind == "item":
                base = 1
            elif block.kind == "door":
                base = {"yellowDoor": 90, "blueDoor": 140, "redDoor": 180}.get(block.eid, 9999)
            elif block.kind == "enemy":
                dmg = self.enemy_damage(block.eid)
                base = 3 if dmg == 0 else 1000 + (99999 if dmg == float("inf") else int(dmg))
        return base + self.check_damage_at(fid, pos) * 100

    def path_to(self, fid: str, target: tuple[int, int], *, strict_click: bool = False) -> list[tuple[int, int]] | None:
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
                can_enter = self.can_enter_click_path if strict_click else self.can_enter
                if not can_enter(fid, nxt, target):
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
        target = (x, y)
        path_target = target
        target_block = self.block_at(fid, target)
        strict_auto_enemy_target = False
        if (
            self.strict_live_model
            and target_block
            and target_block.kind == "enemy"
            and self.auto_flags.get("battle") is True
            and self.enemy_damage(target_block.eid) == 0
        ):
            strict_auto_enemy_target = True
            adjacent_paths: list[tuple[int, list[tuple[int, int]]]] = []
            for adj in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                adj_path = self.path_to(fid, adj, strict_click=True)
                if adj_path:
                    adjacent_paths.append((len(adj_path), adj_path))
            if adjacent_paths:
                adjacent_paths.sort(key=lambda row: row[0])
                path = adjacent_paths[0][1]
                path_target = path[-1]
            else:
                path = None
        else:
            path = self.path_to(fid, target, strict_click=self.strict_live_model)
        if not path:
            self.fail(f"no path to {fid} x{x}y{y}: {note}")
        strict_start_steps = len(self.steps)
        strict_click_before = self.snapshot()
        strict_opened_door = False
        for pos in path[1:]:
            prev = (self.state["x"], self.state["y"])
            block = self.block_at(fid, pos)
            if block and block.kind == "terrain" and block.eid == "flower" and not self.can_enter_flower(fid, prev, pos):
                self.fail(f"wrong-way flower at {fid} x{pos[0]}y{pos[1]} from x{prev[0]}y{prev[1]}")
            if self.strict_live_model and block and block.kind == "door":
                self.apply_block(fid, pos, block, note if pos == (x, y) else "")
                # Live (auto ON) + replayer repeatTargetClick move the hero onto
                # the opened door tile; model that so the offline hero position
                # matches live and the next target stays reachable.
                self.state["x"], self.state["y"] = pos
                strict_opened_door = True
                continue
            if (
                self.strict_live_model
                and block
                and block.kind == "terrain"
                and block.eid in {"fakeWall", "fakeWall2"}
            ):
                # noPass target: hero stops on the adjacent tile (prev), the
                # fakeWall breaks. Do not move the hero onto the wall tile.
                self.apply_block(fid, pos, block, note if pos == (x, y) else "")
                continue
            self.state["x"], self.state["y"] = pos
            if block:
                # Defer after_action's block mutations (mechanism door opens /
                # item spawns) for enemy kills: in live the post-battle auto-BFS
                # runs before the door opens, and opening a door does not
                # re-trigger BFS. The deferred effects are flushed after the
                # post-battle auto_sweep below.
                is_enemy_kill = block.kind == "enemy" and self.strict_live_model
                if is_enemy_kill:
                    self._defer_after_action = True
                try:
                    self.apply_block(fid, pos, block, note if pos == (x, y) else "")
                finally:
                    if is_enemy_kill:
                        self._defer_after_action = False
            else:
                # A click targeting an auto-clearable zero-damage enemy first
                # routes to its adjacent trigger tile, then live auto-BFS clears
                # the target. The trigger tile should not take that enemy's
                # spell-field damage before the automatic battle.
                if not (self.strict_live_model and strict_auto_enemy_target and pos == path_target):
                    self.apply_check_damage(fid, pos, note if pos == (x, y) else "")
                self.trigger_tile_event(fid, pos)
                if pos == path_target and note:
                    before = self.snapshot()
                    self.record("到达", pos, None, before, note)
        if self.strict_live_model:
            # core.plugin.auto fires after every action settles, including after
            # opening a door (the hero stops on the adjacent tile, then auto-BFS
            # picks up newly-accessible items / breaks fakeWalls / battles 0-dmg
            # enemies). Previously this was skipped when a door was opened, which
            # caused the offline model to miss auto-pickups behind opened doors
            # (e.g. MT33 bluePotion after opening x8y2). Always run auto_sweep.
            handled = self.auto_sweep(fid)
            if handled:
                note_suffix = "auto_sweep: " + ", ".join(handled)
                if len(self.steps) > strict_start_steps:
                    self.refresh_last_step(self.steps[-1]["before"], note_suffix)
                else:
                    self.record("auto_sweep", None, None, strict_click_before, note_suffix)
            # Now apply mechanism-door openings / spawns deferred during enemy
            # kills. No second auto_sweep: opening a door does not re-trigger BFS,
            # so items behind the door remain for a later explicit click.
            self._flush_deferred_after_effects()

    def can_enter_flower(self, fid: str, prev: tuple[int, int], pos: tuple[int, int]) -> bool:
        if fid == "MT33" and pos == (8, 10):
            return prev == (7, 10)
        if fid == "MT38" and pos == (2, 5):
            return prev == (2, 4)
        return True

    def apply_block(self, fid: str, pos: tuple[int, int], block: Block, note: str = "") -> None:
        if self.strict_live_model and block.kind == "door":
            self._apply_door_live(fid, pos, block, note)
            return
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
            # fakeWall/fakeWall2 break (disappear) when triggered; the hero
            # stops on the adjacent tile (go_to handles the no-stop-on-wall
            # logic). flower/stairs are passed through / triggered in place.
            action = "破墙" if block.eid in {"fakeWall", "fakeWall2"} else "通过"
        self.record(action, pos, block.eid, before, note)
        if block.kind != "terrain" or block.eid in {"fakeWall", "fakeWall2"}:
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
        elif eid == "sword1":
            self.state["atk"] += 10
        elif eid == "sword2":
            self.state["atk"] += 20
        elif eid == "sword3":
            self.state["atk"] += 40
        elif eid == "sword4":
            self.state["atk"] += 50
        elif eid == "sword5":
            self.state["atk"] += 100
        elif eid == "shield1":
            self.state["def"] += 10
        elif eid == "shield2":
            self.state["def"] += 20
        elif eid == "shield3":
            self.state["def"] += 40
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
        elif eid == "cross":
            self.state["cross"] = True

    def after_action(self, fid: str, pos: tuple[int, int], block: Block) -> None:
        """Dispatches block-consequence mutations (mechanism doors opening, item
        spawns) triggered by an action. When `_defer_after_action` is True (set
        during an explicit enemy kill in go_to), block mutations are CAPTURED to
        `_deferred_after_effects` instead of applied, so the post-battle
        auto_sweep runs against the pre-door-open state (matching live, where the
        post-battle BFS runs before the mechanism door opens and opening a door
        does not re-trigger BFS). Flag/state mutations still apply immediately so
        guard counters and won-flags stay correct. Flushed by go_to after
        auto_sweep with no second sweep."""
        if not self._defer_after_action:
            self._after_action_impl(fid, pos, block)
            return
        self._capturing = True
        self._captured = []
        try:
            self._after_action_impl(fid, pos, block)
        finally:
            self._deferred_after_effects.extend(self._captured)
            self._capturing = False
            self._captured = []

    def _after_action_impl(self, fid: str, pos: tuple[int, int], block: Block) -> None:
        if fid == "MT8" and block.kind == "enemy" and pos in {(9, 5), (11, 5)}:
            self.flags["8redKeyGuards"] = self.flags.get("8redKeyGuards", 0) + 1
            if self.flags["8redKeyGuards"] >= 2:
                self.set_ground(fid, (10, 4))
        if fid == "MT11" and block.kind == "enemy" and block.eid == "redPriest" and pos in {(1, 5), (3, 5)}:
            self.flags["11shieldPriests"] = self.flags.get("11shieldPriests", 0) + 1
            if self.flags["11shieldPriests"] >= 2:
                self.set_ground(fid, (2, 4))
        if fid == "MT14" and block.kind == "enemy" and block.eid == "zombieKnight" and pos in {(2, 2), (1, 1), (3, 1)}:
            self.flags["14zombieKnightGuards"] = self.flags.get("14zombieKnightGuards", 0) + 1
            if self.flags["14zombieKnightGuards"] >= 3:
                self.set_block(fid, (1, 3), "item", "redKey", 23)
        if fid == "MT17" and block.kind == "enemy" and block.eid == "yellowGuard":
            if pos in {(1, 8), (3, 8)}:
                self.flags["17lowerYellowGuards"] = self.flags.get("17lowerYellowGuards", 0) + 1
                if self.flags["17lowerYellowGuards"] >= 2:
                    self.set_ground(fid, (2, 7))
            if pos in {(1, 5), (3, 5)}:
                self.flags["17upperYellowGuards"] = self.flags.get("17upperYellowGuards", 0) + 1
                if self.flags["17upperYellowGuards"] >= 2:
                    self.set_ground(fid, (2, 4))
        if fid == "MT19" and pos == (6, 3) and block.eid in {"fakeWall2", "cross"}:
            if not self.state.get("cross"):
                self.set_block(fid, (6, 3), "item", "cross", 55)
        if fid == "MT20" and block.kind == "enemy" and block.eid == "vampire":
            for p in [(6, 3), (6, 9)]:
                self.set_ground(fid, p)
            for p in [(5, 4), (6, 4), (7, 4)]:
                self.set_block(fid, p, "item", "yellowKey", 21)
            for p in [(4, 5), (4, 6), (4, 7)]:
                self.set_block(fid, p, "item", "redGem", 27)
            for p in [(8, 5), (8, 6), (8, 7)]:
                self.set_block(fid, p, "item", "blueGem", 28)
            for p in [(5, 8), (6, 8), (7, 8)]:
                self.set_block(fid, p, "item", "bluePotion", 32)
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

    def _flush_deferred_after_effects(self) -> None:
        """Apply block mutations captured during a deferred enemy-kill after_action.
        Called by go_to AFTER the post-battle auto_sweep. Does NOT run a second
        auto_sweep -- in live, opening a mechanism door does not re-trigger BFS,
        so items behind the door stay for a later explicit click."""
        effects = self._deferred_after_effects
        self._deferred_after_effects = []
        for eff in effects:
            if eff[0] == "set_ground":
                self.set_ground(eff[1], eff[2])
            elif eff[0] == "set_block":
                self.set_block(eff[1], eff[2], eff[3], eff[4], eff[5])

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


def optional_talk_trader(g: Game, fid: str, x: int, y: int, note: str = "") -> bool:
    cand = g.clone()
    try:
        cand.talk_trader(fid, x, y, note)
    except RouteError:
        return False
    g.__dict__.update(cand.__dict__)
    return True


def collect_existing_items(g: Game, fid: str, positions: list[tuple[int, int]], note: str) -> None:
    for x, y in positions:
        block = g.block_at(fid, (x, y))
        if not block or block.kind != "item":
            continue
        if g.state["floor"] != fid:
            g.fly(fid)
        safe_try(g, g.go_to, fid, x, y, f"{note} {(x, y)}")


def collect_net_yellow_keys_until(g: Game, needed: int, note: str, min_floor: int = 1) -> None:
    """Collect only routes that net-increase yellow keys and do not eat potions."""

    while g.state["yk"] < needed:
        best: tuple[int, Game, str] | None = None
        for fid in _visited_floor_ids(g, min_floor):
            for (x, y), block in list(g.floors[fid].blocks.items()):
                if block.kind != "item" or block.eid != "yellowKey":
                    continue
                cand = g.clone()
                try:
                    if cand.state["floor"] != fid:
                        cand.fly(fid)
                    before = cand.snapshot()
                    cand.go_to(fid, x, y, f"{note}: net yellow key {fid} x{x}y{y}")
                except RouteError:
                    continue
                if cand.state["yk"] <= g.state["yk"]:
                    continue
                # Keep the post-40 low-HP/potion policy honest.  If the path
                # touches a potion, the local model's HP rises; skip that key.
                if cand.state["hp"] > g.state["hp"]:
                    continue
                door_cost = (
                    (cand.state["yd"] - before["yd"]) * 50
                    + (cand.state["bd"] - before["bd"]) * 200
                    + (cand.state["rd"] - before["rd"]) * 800
                )
                hp_loss = before["hp"] - cand.state["hp"]
                net_key = cand.state["yk"] - g.state["yk"]
                score = net_key * 1000 - door_cost - hp_loss
                if best is None or score > best[0]:
                    best = (score, cand, f"{fid} x{x}y{y}")
        if best is None:
            g.fail(f"cannot collect yellow key to {needed}, have={g.state['yk']}: {note}")
        _score, chosen, desc = best
        g.__dict__.update(chosen.__dict__)
        trace_point(f"collected net yellow key {desc}", g)


def guide_prefix_to_48_visit(g: Game) -> None:
    g.set_segment("41-48 initial climb")
    if g.state["bk"] <= 0 and g.block_at("MT32", (11, 7)):
        if g.state["floor"] != "MT32":
            g.fly("MT32")
        g.go_to("MT32", 11, 7, "47F 蓝门前补32F蓝钥匙")
    # Go to 42F first so the 41F half-HP trap is applied before taking 40F potions.
    collect_net_yellow_keys_until(g, 2, "41F 上楼前补钥匙")
    if g.state["floor"] != "MT41":
        g.fly("MT41")
    g.change_by_stair("MT42", 6, 11, "41F 先上42F触发低血半伤")
    g.fly("MT40")
    g.go_to("MT40", 5, 4, "40F 先吃1个蓝血瓶过42F固定伤")
    g.fly("MT42")
    # 42F knight event, right-side keys, center fly to the upper-left stairs.
    g.go_to("MT42", 5, 10, "42F 骑士队长剧情")
    collect_net_yellow_keys_until(g, 1, "42F 右侧黄门前补钥匙")
    if g.state["floor"] != "MT42":
        g.fly("MT42")
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
    if g.state["def"] < 220:
        eat_minimal_potions_until(g, 1800, "slot26低防线补46F/47F领域血量")
        if g.state["floor"] != "MT46":
            g.fly("MT46")
    g.fly("MT46")
    for pos in [(11, 3), (11, 5), (11, 8)]:
        g.go_to("MT46", *pos, "46F 下侧三黄门")
    g.change_by_stair("MT47", 11, 11, "46F 上楼")
    # 47F guide resources and center fly.
    g.go_to("MT47", 7, 11, "47F 左下黄门")
    g.go_to("MT47", 6, 10, "47F 左侧红宝石")
    g.go_to("MT47", 6, 10, "47F 回中心飞点")
    g.center_fly("47F 左下到右上")
    collect_net_yellow_keys_until(g, 1, "47F 右侧黄门前补钥匙")
    if g.state["floor"] != "MT47":
        g.fly("MT47")
    g.go_to("MT47", 7, 1, "47F 右侧黄门")
    for pos in [(11, 1), (11, 2), (11, 3)]:
        g.go_to("MT47", *pos, f"47F 右侧资源 {pos}")
    g.go_to("MT47", 3, 1, "47F 蓝门")
    g.change_by_stair("MT48", 1, 1, "47F 上楼到48")
    g.fly("MT14")
    g.change_by_stair("MT15", 6, 11, "14F lower stair to 15F pickaxe area")
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
                break
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
            break
    if g.state["gold"] < 4000:
        old_errors = len(g.errors)
        try:
            farm_gold_after_coin(g, 4000, preserve_yk=0, min_floor=1)
        except RouteError:
            del g.errors[old_errors:]
    if g.state["gold"] < 4000 and g.state["hp"] < 1500:
        old_errors = len(g.errors)
        try:
            eat_minimal_potions_until(g, 1500, "pre-earthquake shield HP", min_floor=1)
        except RouteError:
            del g.errors[old_errors:]
    if g.state["gold"] < 4000:
        sell_yellow_keys_for_gold(g, 4000)
    if g.state["gold"] < 4000:
        g.fail(f"cannot farm enough gold for earthquake, have={g.state['gold']}")
    if g.state["hp"] < 1500:
        eat_known_pre_earthquake_potions_until(g, 1500, "pre-earthquake shield HP after gold farm")


def sell_yellow_keys_for_gold(g: Game, target_gold: int) -> None:
    if g.state["gold"] >= target_gold:
        return
    if g.state["floor"] != "MT28":
        g.fly("MT28")
    g.move_adjacent("MT28", 8, 4, "28F yellow-key seller")
    while g.state["gold"] < target_gold and g.state["yk"] > 0:
        before = g.snapshot()
        g.state["yk"] -= 1
        g.state["gold"] += 100
        g.record("商人", (8, 4), "sellYellowKey", before, "28F sell 1 yellow key for 100G")


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


def eat_minimal_potions_until(g: Game, target_hp: int, note: str, min_floor: int = 1) -> None:
    """Reach a small HP threshold while minimizing potion over-eating."""

    while g.state["hp"] < target_hp:
        best: tuple[tuple[int, int, int], Game, str] | None = None
        fallback: tuple[tuple[int, int, int], Game, str] | None = None
        for fid in _potion_floor_ids(g, min_floor):
            for (x, y), block in list(g.floors[fid].blocks.items()):
                if block.kind != "item" or block.eid not in {"redPotion", "bluePotion"}:
                    continue
                cand = g.clone()
                try:
                    if cand.state["floor"] != fid:
                        cand.fly(fid)
                    before = cand.snapshot()
                    cand.go_to(fid, x, y, f"{note}: minimal potion {fid} x{x}y{y}")
                except RouteError:
                    continue
                gain = cand.state["hp"] - before["hp"]
                if gain <= 0:
                    continue
                door_cost = (
                    (cand.state["yd"] - before["yd"]) * 50
                    + (cand.state["bd"] - before["bd"]) * 200
                    + (cand.state["rd"] - before["rd"]) * 800
                )
                key = (max(0, cand.state["hp"] - target_hp), door_cost, gain)
                row = (key, cand, f"{fid} x{x}y{y}")
                if cand.state["hp"] >= target_hp:
                    if best is None or key < best[0]:
                        best = row
                elif fallback is None or key < fallback[0]:
                    fallback = row
        chosen_row = best or fallback
        if chosen_row is None:
            g.fail(f"cannot minimally eat potions to {target_hp}, have={g.state['hp']}: {note}")
        _key, chosen, desc = chosen_row
        g.__dict__.update(chosen.__dict__)
        trace_point(f"minimal potion {desc} for {target_hp}", g)


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


def cleanup_reachable_items(
    g: Game,
    item_ids: set[str],
    min_floor: int = 1,
    preserve_rk: int = 0,
    max_steps: int | None = None,
) -> None:
    g.set_segment("final resource cleanup")
    picked = 0
    while True:
        if max_steps is not None and picked >= max_steps:
            return
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
        picked += 1


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
        g.flags.setdefault("routeWarnings", [])
        g.flags["routeWarnings"].append(f"MT20 potion cleanup gained {gained}HP; pocket may have been collected earlier")
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


def eat_known_pre_earthquake_potions_until(g: Game, target_hp: int, note: str) -> None:
    """Fast, bounded heal for the pre-earthquake route.

    Full-map potion search is expensive here because the map is wide open after
    40F. These are high-value potions on floors already visited by the
    earthquake route; each candidate is still cloned and path-checked before it
    is committed.
    """

    candidates = [
        ("MT41", 1, 11),
        ("MT41", 11, 11),
        ("MT42", 1, 9),
        ("MT43", 4, 9),
        ("MT43", 4, 10),
        ("MT43", 4, 11),
        ("MT43", 6, 6),
        ("MT45", 11, 11),
        ("MT48", 2, 1),
        ("MT40", 1, 10),
        ("MT37", 5, 7),
        ("MT37", 7, 9),
    ]
    while g.state["hp"] < target_hp:
        best: tuple[int, Game] | None = None
        for fid, x, y in candidates:
            block = g.block_at(fid, (x, y)) if fid in g.floors else None
            if not block or block.kind != "item" or block.eid not in {"redPotion", "bluePotion"}:
                continue
            cand = g.clone()
            try:
                before = cand.snapshot()
                if cand.state["floor"] != fid:
                    cand.fly(fid)
                cand.go_to(fid, x, y, f"{note}: known potion {fid} x{x}y{y}")
            except RouteError:
                continue
            gain = cand.state["hp"] - before["hp"]
            if gain <= 0 or cand.state["hp"] <= 0:
                continue
            if best is None or gain > best[0]:
                best = (gain, cand)
        if best is None:
            return
        _gain, chosen = best
        g.__dict__.update(chosen.__dict__)


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
                            min_floor=1, preserve_rk=1, max_steps=0)
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
        optional_talk_trader(g, "MT45", 9, 3, "45F 1000G 买2000血")
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
    if g.state["yk"] <= 0 and g.state["gold"] >= 1000 and not g.flags.get(g.trader_flag("MT31", 1, 11)):
        if g.state["floor"] != "MT31":
            g.fly("MT31")
        optional_talk_trader(g, "MT31", 1, 11, "31F late key merchant before 13F sword")
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

    # --- Step 11c: skip late 46F stat shops. The strict20 post-49 probe shows
    # DEF is already above the winning threshold after the 2F blessing; the
    # extra DEF buy reduces final HP.
    trace_point("post_49 after skipping endgame stat shops", g)

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
        optional_talk_trader(g, "MT45", 9, 3, "45F 1000G 买2000血")
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


def post_shield_no49(g: Game) -> None:
    """TE late-49 prep: same as post_shield_49 but WITHOUT the 0F lucky-coin
    trip and WITHOUT the 49F fight.  The downFly picked up at 41F x6y5 is
    reserved for the required TE sequence (24F -> 50F thief -> downFly to 49F
    seal).  No double-gold is taken, so monster gold stays at 1x."""
    g.set_segment("post-shield prep without 49F")
    g.fly("MT43")
    g.go_to("MT43", 3, 1, "43F upper-left yellow door")
    for pos in [(3, 6), (8, 6), (11, 5)]:
        g.go_to("MT43", *pos, f"43F middle/right resource {pos}")
    g.go_to("MT43", 9, 1, "43F upper-right guard")
    g.go_to("MT43", 9, 4, "43F sacred shield")
    g.go_to("MT43", 11, 11, "43F lower-right blue key")
    g.fly("MT46")
    g.go_to("MT46", 3, 8, "46F magic key")
    g.fly("MT41")
    g.use_big_key("41F open all yellow doors")
    g.go_to("MT41", 5, 6, "41F left blue door")
    g.go_to("MT41", 2, 2, "41F upper-left red wizard")
    g.go_to("MT41", 4, 1, "41F upper-left blue key")
    g.go_to("MT41", 7, 6, "41F right blue door")
    g.go_to("MT41", 9, 2, "41F right wall trigger")
    g.go_to("MT41", 10, 2, "41F upper-right red wizard")
    g.fly("MT40")
    g.fly("MT41")
    g.go_to("MT41", 6, 5, "41F downFly")
    for pos in [(3, 10), (4, 10), (3, 11), (4, 11), (8, 10), (9, 10), (8, 11), (9, 11)]:
        safe_try(g, g.go_to, "MT41", *pos, f"41F magic-key resource {pos}")
    trace_point("late49 after 41F magic-key resources", g)

    # Keep the downFly for the required TE sequence:
    # 24F -> 50F thief, then downFly from 50F to 49F for sealing.
    trace_point("late49 reserve downFly for 50F->49F", g)

    # Take the 42F red key before the attack-first shop/farming loop spends the
    # remaining yellow-key routing budget.  It is the pre-princess red key for
    # the user-required late-49 TE order.
    g.fly("MT42")
    g.go_to("MT42", 7, 1, "42F red key for late-49 TE")
    trace_point("late49 after 42F red key", g)

    # Late-49 cannot use the 49F knife before 35F dragon.  Buy attack first so
    # magicDragon is not a 100+ turn fight.
    buy_shops_to_stat(g, "atk", 291, "46F pre-dragon atk shop", preserve_yk=1)
    # TE has no lucky coin (monster gold stays 1x), so gold is roughly half of
    # NE.  Farm 0-damage monster gold BEFORE the def buy so the 47F retreat-
    # wizards (redWizard atk 380 -> need def >= 380) become affordable.  In NE
    # this gold comes from the 0F lucky-coin trip + 2x monster gold.
    safe_try(g, farm_gold_after_coin, g, 1500, 0, 1)
    buy_shops_to_stat(g, "def", 430, "46F pre-dragon def shop", preserve_yk=1)
    safe_try(g, kill_47_retreat_wizards, g)
    clear_zero_damage_monsters(g, preserve_yk=1, min_floor=1)
    g.blocked_items.add(("MT20", 11, 5))
    cleanup_reachable_items(g, {"redGem", "blueGem", "yellowKey", "blueKey", "redKey"},
                            min_floor=1, preserve_rk=1)
    for pos in [(1, 3), (2, 3), (1, 5), (2, 5)]:
        safe_try(g, g.go_to, "MT45", *pos, f"45F left gem {pos}")
    buy_shops_to_stat(g, "atk", 291, "46F atk shop", preserve_yk=1)
    if g.state["gold"] < 1000:
        safe_try(g, farm_gold_after_coin, g, 1000, 0, 1)
    if g.state["floor"] != "MT45":
        g.fly("MT45")
    if g.state["gold"] >= 1000 and not g.flags.get(g.trader_flag("MT45", 9, 3)):
        g.talk_trader("MT45", 9, 3, "45F 1000G to 2000HP")
    eat_all_reachable_potions(g, min_floor=1)
    trace_point("late49 after no-49 prep", g)


def trigger_mt50_thief(g: Game) -> None:
    """Talk to the 50F thief: reveals the true redKing and (per game quirk)
    boosts the 49F fake redKing to 5000/1580/190.  Sets 50final + 50thief.
    Does NOT kill the 50F redKing -- downFly to 49F immediately."""
    g.move_adjacent("MT50", 6, 5, "50F thief event")
    before = g.snapshot()
    g.flags["50final"] = True
    g.flags["50thief"] = True
    g.record("事件", (6, 5), "redKing", before, "50F 小偷现身真魔王")
    g.set_block("MT50", (6, 5), "enemy", "redKing", 245)


def downfly_to_mt49_event(g: Game) -> None:
    if g.state["downFly"] <= 0:
        g.fail("no downFly for late 49F seal")
    if g.state["floor"] != "MT50":
        g.fail(f"late 49F downFly must start on MT50, got {g.state['floor']}")
    before = g.snapshot()
    g.state["downFly"] -= 1
    g.state["floor"] = "MT49"
    g.visited.add("MT49")
    g.record("下楼器", (g.state["x"], g.state["y"]), "downFly", before, "50F downFly to 49F seal event")


def trigger_mt49_event(g: Game) -> None:
    if g.state["floor"] != "MT49":
        g.fail(f"not on MT49 for seal event: {g.state['floor']}")
    before = g.snapshot()
    g.state["x"], g.state["y"] = 6, 6
    g.set_block("MT49", (6, 7), "door", "specialDoor", 85)
    g.set_block("MT49", (6, 3), "enemy", "redKing", 245)
    for p in [(5, 2), (5, 3), (5, 4), (6, 4), (7, 4), (7, 3), (7, 2), (6, 2)]:
        g.set_block("MT49", p, "enemy", "whiteKing", 246)
    g.record("事件", (6, 6), "redKing", before, "49F seal event after 50F thief")


def clear_mt49_from_center(g: Game) -> None:
    """Kill the 4 cardinal guards to seal the fake redKing (49sealed=True), then
    kill the 4 corner guards + the sealed fake redKing and collect rewards.

    The 50F thief flag (50final) is cleared here and NOT restored: in TE the 49F
    seal also seals the 50F true redKing, so the final 50F fight must use the
    49sealed stats (500/158/19 via the 50thief branch) rather than 50final
    (5000/1580/190)."""
    g.retreat_wizards |= {("MT49", 5, 2), ("MT49", 7, 2), ("MT49", 5, 4), ("MT49", 7, 4)}
    for pos in [(6, 4), (5, 3), (7, 3), (6, 2)]:
        g.go_to("MT49", *pos, f"49F seal cardinal guard {pos}")
    g.flags["49sealed"] = True
    # 50final is cleared so the 49F fake redKing uses 49sealed stats.  It is NOT
    # restored: the 50F true redKing must also be sealed (500/158/19).
    g.flags["50final"] = False
    g.retreat_wizards.clear()
    for pos in [(5, 2), (7, 2), (5, 4), (7, 4), (6, 3)]:
        g.go_to("MT49", *pos, f"49F seal corner/fake redKing {pos}")
    for pos in [(5, 2), (7, 2), (2, 4), (3, 4), (4, 4), (8, 4), (9, 4), (10, 4), (5, 5), (6, 5), (7, 5)]:
        safe_try(g, g.go_to, "MT49", *pos, f"49F late reward {pos}")


def late49_endgame(g: Game) -> None:
    """TE late-49 endgame: rescue princess first, then 24F -> 50F thief,
    downFly to 49F seal, return 24F -> 50F, kill the sealed true redKing."""
    g.set_segment("late-49 TE endgame")
    # Late-49 TE still needs one red key for the 25F/26F princess path before
    # the 49F rewards exist.  The reachable 42F red key must be modeled here;
    # otherwise an RK=0 40F state is incorrectly rejected at the 25F red door.
    cleanup_reachable_items(g, {"redGem", "blueGem", "yellowKey", "blueKey", "redKey"}, min_floor=1, preserve_rk=1)
    if g.state["rk"] < 1:
        g.fly("MT42")
        g.go_to("MT42", 7, 1, "42F red key for late-49 TE")
    eat_all_reachable_potions(g, min_floor=1)

    ensure_hp_for_enemy(g, "magicDragon", 20)
    g.fly("MT35")
    g.go_to("MT35", 6, 7, "35F magic dragon before knife")
    g.go_to("MT35", 6, 6, "35F snow")
    for pos in [(5, 5), (6, 5), (7, 5)]:
        safe_try(g, g.go_to, "MT35", *pos, f"35F dragon potion {pos}")

    collect_net_yellow_keys_until(g, 1, "13F sacred sword yellow door", min_floor=1)
    g.fly("MT13")
    g.go_to("MT13", 6, 10, "13F sacred sword yellow door")
    g.state["x"], g.state["y"] = 6, 11
    g.go_to("MT13", 6, 10, "13F stand on lava edge")
    for y in [9, 8, 7, 6]:
        g.use_snow("13F freeze lava for sacred sword")
        g.go_to("MT13", 6, y, f"13F lava path y{y}")
    g.go_to("MT13", 6, 5, "13F sacred sword")
    cleanup_reachable_items(g, {"redGem", "blueGem"}, min_floor=1, preserve_rk=1)

    buy_shops_to_stat(g, "def", 502, "46F endgame def shop", preserve_yk=1)
    g.fly("MT2")
    g.talk_mt2_bless()
    collect_net_yellow_keys_until(g, 1, "16F superPotion oldman path", min_floor=1)
    g.fly("MT16")
    g.talk_mt16_oldman()

    buy_hp_with_remaining_gold(g, 2)
    ensure_hp_for_enemy(g, "blackMagician", 20)
    g.fly("MT25")
    g.go_to("MT25", 6, 10, "25F red door")
    g.go_to("MT25", 6, 9, "25F trigger")
    g.go_to("MT25", 6, 6, "25F black magician")
    for pos in [(4, 8), (5, 8), (7, 8), (8, 8)]:
        g.go_to("MT25", *pos, f"25F red key {pos}")

    g.fly("MT26")
    for y in [10, 9, 8]:
        g.go_to("MT26", 6, y, f"26F princess red door y{y}")
    g.use_snow("26F freeze lava before princess")
    g.go_to("MT26", 6, 7, "26F before princess")
    g.talk_mt26_princess()

    if g.state["gold"] < 1000:
        safe_try(g, farm_gold_after_coin, g, 1000, 0, 1)
    if g.state["floor"] != "MT45":
        g.fly("MT45")
    if g.state["gold"] >= 1000 and not g.flags.get(g.trader_flag("MT45", 9, 3)):
        g.talk_trader("MT45", 9, 3, "45F 1000G to 2000HP")

    buy_hp_with_remaining_gold(g, 4)
    final_key_bundle_and_mt20_potions(g)
    eat_all_reachable_potions(g, min_floor=1)
    eat_final_yellow_door_potions(g, min_floor=1, preserve_rk=1)

    g.fly("MT24")
    g.go_to("MT24", 6, 8, "24F red door before 50F thief")
    g.trigger_mt24_to_mt50()
    trigger_mt50_thief(g)
    downfly_to_mt49_event(g)
    trigger_mt49_event(g)
    clear_mt49_from_center(g)

    buy_hp_with_remaining_gold(g, 4)
    cleanup_reachable_items(g, {"redGem", "blueGem", "yellowKey", "blueKey"}, min_floor=1, preserve_rk=0)
    eat_all_reachable_potions(g, min_floor=1)
    if g.state["superPotion"] > 0:
        g.use_super_potion("final superPotion after late 49F rewards")

    g.fly("MT24")
    g.trigger_mt24_to_mt50()
    g.go_to("MT50", 6, 5, "50F final redKing after 49F seal")
    trace_point("late49 after 50F sealed final redKing", g)


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
            before = g.snapshot()
            before["step_count"] = len(g.steps)
            fn(g)
            after = g.snapshot()
            after["step_count"] = len(g.steps)
            g.stage_summaries.append(
                {
                    "name": name,
                    "label": STAGE_LABELS.get(name, name),
                    "before": before,
                    "after": after,
                    "delta_dmg": after["dmg"] - before["dmg"],
                    "delta_steps": after["step_count"] - before["step_count"],
                    "stock_score": stock_score(after),
                }
            )
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
        json.dumps(
            {
                "ok": not g.errors,
                "final": g.snapshot(),
                "stage_summaries": g.stage_summaries,
                "errors": g.errors,
                "steps": g.steps,
            },
            ensure_ascii=False,
            indent=2,
        ),
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
    lines.append("## 阶段分数")
    lines.append("")
    lines.append("- `库存折算分 = HP + 黄钥匙*50 + 蓝钥匙*200 + 金币*0.5`；本 Post-40 脚本暂未重算全图剩余资源 `final-score`。")
    lines.append("")
    lines.append("| 大阶段 | 状态快照 | 本段dmg | 累计dmg | 门 黄/蓝/红 | 库存折算分 | 关键资源 | 步数 |")
    lines.append("|---|---|---:|---:|---|---:|---|---:|")
    for row in g.stage_summaries:
        after = row["after"]
        lines.append(
            f"| {row['label']} | {state_line(after)} {after['floor']} x{after['x']}y{after['y']} | "
            f"{row['delta_dmg']} | {after['dmg']} | {after['yd']}/{after['bd']}/{after['rd']} | "
            f"{row['stock_score']:.1f} | {stage_resource_text(after)} | {row['delta_steps']} |"
        )
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
