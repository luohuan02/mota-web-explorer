#!/usr/bin/env python3
"""通用 Game 模型（1-4 区 / 4-50 层唯一管线的共享基类）+ post-40 主流程脚本。

本文件双重身份（历史债务，未拆分）：
- ``Game`` 类：离线通用状态机，被 recording_seed_to_game / zoneN_game_route /
  各搜索与审计脚本共享。live 对齐语义（auto_sweep BFS、开门步 sweep、
  automaticRoute go_to、checkBlock.damage 阻挡、火格撤退等）都收敛在这里；
  楼层事件建模集中在 ``TRIGGER_EVENT_DESC`` / ``_after_action_impl`` /
  ``trigger_tile_event``——这是「1-50F 唯一管线共用一个 Game」架构下的
  适配层位置（CLAUDE.md 根因优先约束：楼层事件不得打补丁到 walk）。
- 文件尾 ``main()``：save37/post-40 生命榜单路线的主流程（STAGE_NAMES/
  STAGE_LABELS 是它的专用概念），与 ``scripts/build/prepend_40f_prefix_walk.js``
  配套，命令见 CLAUDE.md「常用命令」。

行为口径：以 web 实机为准（web 0 mismatch 含金币是唯一验收标准）；
guide/post40 主流程的步序约定保守、不合法即停在确切 checkpoint。
"""

from __future__ import annotations

import copy
import argparse
import heapq
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
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
    "blueWall",
    "unbreakableWall",
    "blockWall",
    "autotile",
    "star",
    "lava",
    "water",
    "blueWater",
}

# Subset of WALL_IDS whose tile event has canBreak=true (project.min.js maps_90f36752
# tile defs: only yellowWall and fakeWall set canBreak=true; fakeWall2 is false).
# The pickaxe (破墙镐) useItemEffect iterates core.utils.scan (4 dirs) and openDoor's
# every adjacent wall with block.event.canBreak, so it breaks ALL of these around
# the hero, not a single facing wall.
BREAKABLE_WALL_IDS = {"yellowWall", "fakeWall"}
DOORS = {"yellowDoor", "blueDoor", "redDoor", "specialDoor", "steelDoor"}
STAIRS = {"upFloor", "downFloor"}

# === walk 输出协议常量（gen_zone_walk_md 等人读生成器导入，勿在生成器重复定义）===
# record() 的 action 中文名 -> 人读 .md 英文动词。新增 action 必须在此登记，
# 否则 .md action 行 fallback 中文、与人读格式分叉（replayer 只按 pos 点击，
# 不解析 action，此表仅服务人读 .md）。
ACTION_VERB_EN = {
    "开门": "open",
    "击杀": "kill",
    "拾取": "take",
    "通过": "pass",
    # fakeWall/fakeWall2 破墙：实机点墙格游戏自破，人读统一 pass
    "破墙": "pass",
    "到达": "move",
    "飞行": "fly",
    # zone2+ 适配层 action（replay_zone2_guide_route / zoneN_game_route record）
    "商店": "shop",
    "商人": "trader",
    "对话": "talk",
    "事件": "event",
    "事件奖励": "reward",
    "事件战斗": "eventbattle",
}
# 不 emit .md action 行的 action（replayer 自动处理 / 非 hero 点击；事件开门 是
# zone2 适配层 action，通用 Game 不产生）。
SKIP_ACTIONS = {"换层", "已清理", "事件开门"}
# 楼层切换 action：deferred-auto 归因不可穿透的硬边界（换层 同时是 SKIP）。
FLOOR_TRANSITIONS = {"换层", "飞行"}
# 门 eid -> (消耗钥匙 state key, 累计开门数 state key)。specialDoor/steelDoor
# 不耗钥匙，不在表内。
DOOR_KEY = {
    "yellowDoor": ("yk", "yd"),
    "blueDoor": ("bk", "bd"),
    "redDoor": ("rk", "rd"),
}
# 合法 auto 配置 key（set_auto 校验 + gen fmt_auto_config 共用）。
AUTO_KEYS = ("battle", "item", "wall")

# MT10 (10F) boss trigger (6,5) 后 boss 区域终态。web events["6,5"]: captain
# (6,4 初始静态) move 到 (6,1)；skeletonSoldier (from 2,4/10,4) 到 (6,4)/(6,6)；
# skeleton (from 1,3/2,3/3,3/9,3/10,3/11,3) 到 (5,4)/(7,4)/(5,5)/(7,5)/(5,6)/(7,6)。
# 录像逐打 dmg 确认: (6,4)(6,6)=skeletonSoldier(75), 其余 6 格=skeleton(30), (6,1)=captain(304)。
MT10_BOSS_SPAWN = {
    (5, 4): "skeleton",
    (7, 4): "skeleton",
    (6, 4): "skeletonSoldier",
    (5, 5): "skeleton",
    (7, 5): "skeleton",
    (5, 6): "skeleton",
    (6, 6): "skeletonSoldier",
    (7, 6): "skeleton",
    (6, 1): "skeletonCaptain",
}

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
    events: dict[str, Any]
    after_battle: set[str]
    after_battle_auto: set[str]
    # Foreground map (fgmap): decorative/animated overlays (e.g. fire=103). The
    # web's bfs judge treats getFgNumber(tx,ty)===103 as canGoThrough=false, so
    # auto_sweep must skip fire tiles. The hero can still moveOneStep onto fire
    # (the recording does), so go_to does NOT block fire -- only auto_sweep bfs.
    # Default empty (no fgmap); only MT47 uses fire currently.
    fgmap: list[list[int]] = field(default_factory=list)

    @property
    def width(self) -> int:
        return len(self.grid[0])

    @property
    def height(self) -> int:
        return len(self.grid)

    def fg_at(self, x: int, y: int) -> int:
        """Foreground value at (x,y), 0 if out of bounds or no fgmap (web getFgNumber)."""
        fg = self.fgmap
        if not fg or y < 0 or y >= len(fg):
            return 0
        row = fg[y]
        if x < 0 or x >= len(row):
            return 0
        return int(row[x] or 0)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def floor_no(fid: str) -> int:
    return int(fid[2:])


# Floors with isHide=true in the game (core.floors[fid].isHide). The game's
# _changeFloor_getInfo resolves ":next"/":before" via findValidFloor which SKIPS
# hidden floors, so a stair with floorId=":next" from MT43 lands on MT45 (not
# MT44). MT44 is only reachable via the upFly item (floor_no+1, no skip).
# upFly/downFly do NOT skip hidden floors (item-based, floor_no±1).
HIDDEN_FLOORS = {"MT44"}


# NPC eids that are passable step-on event triggers (hero routes through them
# and trigger_tile_event fires). In practice NO NPC is passable in live: all
# npc blocks default to noPass=true (cls!=items rule in maps.initBlock), so the
# hero always stops adjacent and the event fires on FACING (turn-then-move
# toward the NPC = a pure turn; trigger="action"). This includes the thief
# (MT2 (10,11)/MT15 (9,1)/MT29 (6,2)/MT35 (5,10)) and the princess (MT26 6,6):
# the recording never steps on them -- e.g. MT29 (6,2) thief: hero at (5,2)
# turns right toward (6,2), stays at (5,2), the "action" event fires (opens
# (6,3) 暗道). MT10 (6,9) "thief event" is an empty step-on floor-event tile
# (post-boss (6,9) is ground 0), NOT a thief block, so unaffected. The
# converter's arrow handler fires noPass NPCs via _reach_event_trigger
# (move_adjacent + trigger_tile_event). Kept as an empty set (not removed) so
# the can_enter/is_intermediate/_reachable_event_triggers branches stay
# explicit if a truly passable NPC is ever added.
PASSABLE_NPC_EIDS: set[str] = set()
# Story-only NPCs live treats as passable ground (enable:false, noPass unset),
# NOT step-on trigger events (those stay noPass). The recording walks straight
# through them -- e.g. MT35 (5,10) thief says goodbye and leaves; the route then
# passes through to reach MT35 (5,11), with no event fired. Respecting the
# noPass in is_wall/can_enter lets the hero route through these decor NPCs.
PASSABLE_NPC_TILES: set[tuple[str, tuple[int, int]]] = {
    ("MT35", (5, 10)),
}


def next_floor(fid: str) -> str:
    """Resolve ":next" from fid, skipping hidden floors (matches findValidFloor)."""
    n = floor_no(fid) + 1
    while f"MT{n}" in HIDDEN_FLOORS:
        n += 1
    return f"MT{n}"


def prev_floor(fid: str) -> str:
    """Resolve ":before" from fid, skipping hidden floors."""
    n = floor_no(fid) - 1
    while f"MT{n}" in HIDDEN_FLOORS:
        n -= 1
    return f"MT{n}"


def state_line(s: dict[str, Any]) -> str:
    return (
        f"HP={s['hp']} ATK={s['atk']} DEF={s['def']} "
        f"YK={s['yk']} BK={s['bk']} RK={s['rk']} G={s['gold']}"
    )


def stock_score(s: dict[str, Any]) -> float:
    return s["hp"] + s["yk"] * 100 + s["bk"] * 500 + s["gold"] * 1.0


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


# Reverse lookup eid -> tile id. Used to scan a floor's grid for decor blocks
# that classify() returns None for (e.g. whiteWall2 is passable decor, not in
# .blocks), so trigger_tile_event can count them for conditional events like
# MT29 thief (whiteWall2@MT23 gates whether the 暗道 opens).
_EID_TO_TILE: dict[str, int] = {
    info.get("id", ""): tid for tid, info in load_tiles().items()
}


def load_enemies() -> dict[str, dict[str, Any]]:
    return read_json(ROOT / "data" / "maps" / "enemy_stats.json")["enemys"]


def load_fly_points() -> dict[str, dict[str, Any]]:
    return read_json(ROOT / "data" / "maps" / "fly_points.json")


def decode_snapshot_grid(fid: str, base_grid: list[list[int]], snapshot: dict[str, Any]) -> list[list[int]]:
    """Merge the save's runtime map over the refreshed base grid.

    2026-08-31 41218 修复：快照覆盖只对 **save 已访问楼层** 生效。未访问楼层的
    save.map 是导出存档当时的运行时提取——游戏数据此后更新时（如 MT40 (6,1)
    从 yellowKnight 改为 upFloor 楼梯）旧提取就成了陈旧数据，模型与录像所玩的
    当前游戏分歧。已访问楼层的快照状态（门/拾取/击杀进度）仍必须保留。
    """
    saved = snapshot.get("maps", {}).get(fid)
    visited = ((snapshot.get("hero") or {}).get("flags") or {}).get("__visited__") or {}
    if not saved or not visited.get(fid):
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
    # whiteWall2 is a decorative PASSABLE wall (tile_mapping noPass=false): live
    # treats it as floor, so treat as empty here -- path_to may route through it.
    # Do NOT add whiteWall/yellowWall: those are event-opened, not freely
    # passable. Fixes MT20 x5y5 unreachable (vampire-area decoration).
    if eid == "whiteWall2":
        return None
    if eid in enemies or cls == "enemy48":
        return "enemy"
    if eid in DOORS:
        return "door"
    if cls == "items" or eid in ITEM_CN:
        return "item"
    if eid in STAIRS or eid in {"fakeWall", "fakeWall2", "flower"}:
        return "terrain"
    if cls == "npcs" or cls == "npc48" or eid in {"blueShop", "oldman", "trader", "thief"}:
        return "npc"
    # Web noPass rule (maps.initBlock): when blocksInfo doesn't set noPass
    # explicitly, noPass = (cls != "items"). So all terrains/animates/autotile
    # are non-passable intermediate tiles (shop counters like blueShop-left,
    # crystalUp, fire, switch, portals, etc.). Previously these fell through to
    # None -> block_at returned None -> can_enter treated them as passable
    # empty, which let path_to route the hero onto shop counters (e.g. MT32
    # x9y10 blueShop-left) that the live game refuses to step on.
    if cls in {"terrains", "animates", "autotile"}:
        return "terrain"
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
                # Unknown non-zero tiles are never safe to treat as empty.
                # MT15 tile=17 surrounds the octopus/pickaxe and is removed by
                # the boss event; treating it as floor lets offline auto enter a
                # sealed room that live cannot reach. Keep unknowns blocking
                # until an explicit map event replaces/removes them.
                blocks[(x, y)] = Block("terrain", f"unknownTile{tile}", tile)
                continue
            eid = info["id"]
            cls = info.get("cls", "")
            kind = classify(eid, cls, enemies)
            if kind:
                blocks[(x, y)] = Block(kind, eid, tile)
    events = copy.deepcopy(raw.get("events", {}))
    # Save-map overrides use an explicit 0 (as opposed to -1 = unchanged) when
    # a one-shot NPC/event block has been removed. Keeping the raw static event
    # would turn the now-empty tile into a permanent auto/path barrier (MT15
    # thief x9y1), even though live can traverse it. Prune only when the saved
    # override explicitly clears a base non-zero event tile.
    saved_grid = (snapshot.get("maps", {}).get(fid) or {}).get("map") or []
    for loc in list(events):
        try:
            x, y = (int(v) for v in loc.split(",", 1))
            row = saved_grid[y] if y < len(saved_grid) else None
            if isinstance(row, list) and x < len(row) and row[x] == 0 and base_grid[y][x] != 0:
                events.pop(loc, None)
        except (TypeError, ValueError, IndexError):
            continue
    # One-shot floor events (e.g. MT20 (6,8) vampire spawn) are tracked in the
    # save by the `R{fid},{x},{y}` flag (set true after the event fires). The
    # save stores no `events` field and the spawn tile is empty in the base grid,
    # so the grid-prune above cannot detect it. Without this, a post-vampire seed
    # would still look pre-vampire to the model and re-spawn/kill the vampire on
    # a flyback. Prune any event whose R flag is set (already fired in the save).
    hero_flags = ((snapshot.get("hero") or {}).get("flags") or {})
    for loc in list(events):
        if hero_flags.get(f"R{fid},{loc}"):
            events.pop(loc, None)
    # Foreground map (fgmap): decorative overlays like fire (103) that the web's
    # bfs judge blocks (getFgNumber(tx,ty)===103 -> canGoThrough false). Default to
    # all-zeros when the floor has no fgmap; only MT47 uses fire currently.
    fgmap_raw = raw.get("fgmap") or []
    fgmap: list[list[int]] = []
    for gy in range(len(grid)):
        src_row = fgmap_raw[gy] if gy < len(fgmap_raw) else []
        fgmap.append([int(src_row[gx]) if gx < len(src_row) else 0 for gx in range(len(grid[0]))])
    floor = Floor(fid=fid, ratio=ratio, grid=grid, blocks=blocks,
                 change_floor=raw.get("changeFloor", {}), events=events,
                 fgmap=fgmap,
                 after_battle=set((raw.get("afterBattle") or {}).keys()),
                 after_battle_auto={
                     key for key, actions in (raw.get("afterBattle") or {}).items()
                     # A conditional branch that merely contains openDoor may
                     # instead take its flag-only branch (MT32/MT17 paired
                     # guards). Only direct unconditional openDoor actions
                     # restart live auto after the battle event settles.
                     if isinstance(actions, list)
                     and any(isinstance(action, dict) and action.get("type") == "openDoor"
                             for action in actions)
                     and '\"waitAsync\"' not in json.dumps(actions, ensure_ascii=False)
                     and '\"async\": true' not in json.dumps(actions, ensure_ascii=False)
                     and '\"setBlock\"' not in json.dumps(actions, ensure_ascii=False)
                     and '\"hide\"' not in json.dumps(actions, ensure_ascii=False)
                 })
    # 预计算 special 15 (魔法场) 敌人位置; check_damage_at 遍历它而非全 blocks(52% 热点)。
    # block_at 检查活(杀后 blocks.pop), _spell_enemies 含死位但遍历少(special 15 敌人稀有)。
    floor._spell_enemies = []
    for _pos, _blk in blocks.items():
        if _blk.kind != "enemy":
            continue
        _sp = (enemies.get(_blk.eid, {}) or {}).get("special", 0)
        _sps = set(_sp) if isinstance(_sp, list) else {_sp}
        if 15 in _sps:
            floor._spell_enemies.append(_pos)
    return floor


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


# 攻略线（guide/post40 主流程）搜索时代的语义：这些 boss 在 guide 关键阶段
# （49F 屠龙匕首/祝福/封印）拿到属性后变 0 伤，若不禁止 auto，搜索/sweep 顺路
# 会把它们提前农掉、破坏脚本化的 boss 事件边界。**不是 live 语义**——live 的
# auto 只碰 0 伤怪，boss 变 0 伤后 live 也会 auto 杀；录像转换管线不需要它，
# 只有 guide 基线搜索/骨架交换类脚本依赖。需要不同集合时用 Game(..., no_auto_farm=...)
# 注入（传空 set 即关闭该保护）。
GUIDE_NO_AUTO_FARM: set[tuple[str, int, int]] = {
    ("MT35", 6, 7),   # magicDragon (after 49F knife, guide step 11a)
    ("MT25", 6, 6),   # blackMagician (after bless, guide step 11f)
    ("MT49", 6, 3),   # redKing 49F (seal sequence, guide step 10)
    ("MT50", 6, 5),   # redKing 50F (final boss)
}
# MT47 撤退红巫师初始位（(1,9) 走廊入口；base 图静态红巫师，与 (8,2) 同机制）。
# (8,2) 不在种子里：41218/40145 实证它的标记由 _check_fire_retreat 在 hero 踩
# 相邻火格时迁移补上（初始种子只有 (1,9) 即与 live 一致）；动态恢复用
# sync_mt47_retreat_wizards。需要覆盖时用 Game(..., retreat_wizards=...) 注入。
MT47_RETREAT_WIZARD_SEED: set[tuple[str, int, int]] = {("MT47", 1, 9)}


class Game:
    def __init__(self, snapshot: dict[str, Any],
                 *, no_auto_farm: set[tuple[str, int, int]] | None = None,
                 retreat_wizards: set[tuple[str, int, int]] | None = None) -> None:
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
        # Auto-load autoEvent "already triggered" flags from the save state.
        # The save does not store these custom flags, so a floor whose autoEvent
        # condition is ALREADY met at load time (center cleared / puzzle doors
        # open) would otherwise re-fire the autoEvent and re-spawn its reward on
        # the next visit (e.g. slot34 MT34 center cleared in zone1-3 -> zone4
        # re-visit must not re-spawn the 4YK+1RK that was already picked up).
        if "MT34" in self.floors:
            center = {(5, 4), (7, 4), (9, 4), (11, 4), (5, 8), (7, 8), (9, 8), (11, 8)}
            if all(not (self.floors["MT34"].blocks.get(p)
                        and self.floors["MT34"].blocks[p].kind == "enemy")
                   for p in center):
                self.flags["mt34_center_reward"] = 1
        if "MT39" in self.floors:
            puzzle_open = {(4, 2), (6, 4)}
            if all(self.floors["MT39"].blocks.get(p) is None for p in puzzle_open):
                self.flags["mt39_centerfly3"] = 1
        # MT32 (6,10) yellowKnight one-time event: the web sets flag "32" and
        # removes events["6,10"] when it fires. The save stores "32" (not our
        # internal mt32_yellowknight name) and does not persist the popped
        # event, so a zone4 re-visit would otherwise re-fire the +100G event.
        if self.flags.get("32"):
            self.flags["mt32_yellowknight"] = 1
            if "MT32" in self.floors:
                self.floors["MT32"].events.pop("6,10", None)
        # MT10 (6,11) upFloor is SHOWN only by the skeletonCaptain afterBattle
        # ("show [6,11]" in web mt10_map.json afterBattle["6,1"]; the base map's
        # events["6,11"] has enable:false so live has NO block there until the
        # captain dies). Before the captain kill the stair must not exist --
        # otherwise pre-boss climbs MT10->MT11 pass offline but are impossible
        # in live (2026-09-18 41898 detour false positive, web verifier caught
        # it: core.getBlock(6,11) == null on live).
        if "MT10" in self.floors and not self.flags.get("10f战胜骷髅队长"):
            cap_stair = self.floors["MT10"].blocks.get((6, 11))
            if cap_stair is not None and cap_stair.kind == "terrain" and cap_stair.eid == "upFloor":
                self.floors["MT10"].blocks[(6, 11)] = None
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
        # go_to 递归深度计数：最外层 go_to 结束时检查 autoEvent（_check_auto_events）。
        self._go_to_depth = 0
        # Tiles that were doors (yellowDoor/redDoor/blueDoor/specialDoor/...)
        # and have been cleared (opened by hero 开门 or by an afterBattle event
        # like MT10 captain clearing (6,9)). Stepping onto such a tile later is
        # a 走门格 in live: core.plugin.auto fires and INTERRUPTS the hero's
        # automaticRoute there (hero stops on the former-door tile). The
        # converter marks these pass steps so coalesce keeps them as separate
        # nodes (else replayer coalesces 6,9 into 6,11, clicks 6,11, but live
        # interrupts at 6,9 -> position mismatch).
        self._former_doors: dict[str, set[tuple[int, int]]] = {}
        # RedWizards that retreat one tile away from the hero when approached
        # (until blocked by wall/door). They need a corner-trap route, not a
        # direct go_to, so auto-farming/sweeping must skip them. Seed + 注入
        # 语义见 MT47_RETREAT_WIZARD_SEED。
        self.retreat_wizards: set[tuple[str, int, int]] = set(
            MT47_RETREAT_WIZARD_SEED if retreat_wizards is None else retreat_wizards)
        # guide 基线搜索的 boss 保护（guide/post40 主流程需要，录像转换不需要），
        # 见 GUIDE_NO_AUTO_FARM。
        self.no_auto_farm: set[tuple[str, int, int]] = set(
            GUIDE_NO_AUTO_FARM if no_auto_farm is None else no_auto_farm)

    def clone(self) -> "Game":
        # Search probes clone thousands of times; copy.deepcopy of the full game
        # (incl. 10 floors' blocks dicts) was 74% of runtime (acquire_resource
        # 试探 clone). copy-on-write: share Floor objects (read-mostly map data),
        # deepcopy only the one floor a set_block/set_ground mutates. Immutable
        # prefix steps shared; only the mutable last step deep-copied.
        cloned = Game.__new__(type(self))  # 保留子类 (Zone3Game/Zone4Game 事件方法)
        cloned.__dict__.update(self.__dict__)  # 浅拷基准(只读 snapshot_raw/enemies/fly_points 共享)
        cloned.floors = dict(self.floors)  # 浅拷 dict; Floor 对象共享
        for f in cloned.floors.values():
            f._owned = False  # 标共享: 写时 deepcopy 单 floor
        cloned.state = copy.deepcopy(self.state)
        cloned.visited = set(self.visited)
        cloned.steps = list(self.steps[:-1])
        if self.steps:
            cloned.steps.append(copy.deepcopy(self.steps[-1]))
        cloned.stage_summaries = list(self.stage_summaries)
        cloned.errors = list(self.errors)
        cloned.flags = copy.deepcopy(self.flags)
        cloned.auto_flags = dict(self.auto_flags)
        cloned._pending_auto_before = (copy.deepcopy(self._pending_auto_before)
                                        if self._pending_auto_before is not None else None)
        cloned._next_record_before = (copy.deepcopy(self._next_record_before)
                                      if self._next_record_before is not None else None)
        cloned._captured = list(self._captured)
        cloned._deferred_after_effects = list(self._deferred_after_effects)
        cloned.blocked_items = set(self.blocked_items)
        cloned._go_to_depth = self._go_to_depth
        cloned.retreat_wizards = set(self.retreat_wizards)
        cloned.no_auto_farm = set(self.no_auto_farm)
        cloned._former_doors = {k: set(v) for k, v in self._former_doors.items()}
        return cloned

    def _cow(self, fid: str) -> None:
        """floors copy-on-write: clone 共享 Floor 对象, 写前 deepcopy 独占。
        原始未 clone 的 floor _owned 未设(getattr True=独占, 跳过); clone 标
        _owned=False 触发首次写 deepcopy。"""
        f = self.floors.get(fid)
        if f is None or getattr(f, "_owned", True):
            return
        f = copy.deepcopy(f)
        f._owned = True
        self.floors[fid] = f

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

    def set_auto(self, note: str | None = None, **changes: Any) -> None:
        """Record a real, verifier-visible automatic-operation transition.

        Automatic settings are part of the route state, not a launch-time
        constant.  In particular Zone 4 starts with ``item=nopotion`` for the
        half-HP fields and must switch to ``item=true`` immediately after the
        sacred shield grants magic immunity.  The unified live verifier already
        executes ``设置自动`` steps; recording the transition here keeps offline
        Game, machine JSON, human walk, and browser replay on one timeline.
        """
        unknown = set(changes) - set(AUTO_KEYS)
        if unknown:
            self.fail(f"unknown auto settings: {sorted(unknown)}")
        for key, value in changes.items():
            if value not in {True, False, "nopotion"}:
                self.fail(f"invalid auto setting {key}={value!r}")
        before = self.snapshot()
        self.auto_flags.update(changes)
        self.flags["__auto__"] = dict(self.auto_flags)
        self.record(
            "设置自动",
            (self.state["x"], self.state["y"]),
            "__auto__",
            before,
            note or "神圣盾后魔法免疫，自动拾取血瓶开启",
        )
        self.steps[-1]["auto"] = dict(self.auto_flags)

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
        step["before"] = before
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
        self._cow(fid)
        f = self.floors[fid]
        x, y = pos
        blk = f.blocks.get(pos)
        if blk is not None and blk.kind == "door":
            self._former_doors.setdefault(fid, set()).add((x, y))
        if 0 <= y < f.height and 0 <= x < f.width:
            f.grid[y][x] = 0
        f.blocks.pop(pos, None)

    def set_block(self, fid: str, pos: tuple[int, int], kind: str, eid: str, tile: int = 0) -> None:
        if self._capturing:
            self._captured.append(("set_block", fid, pos, kind, eid, tile))
            return
        self._cow(fid)
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
        if block and block.kind == "npc" and block.eid not in PASSABLE_NPC_EIDS and (fid, pos) not in PASSABLE_NPC_TILES:
            return True
        if block and block.eid in WALL_IDS:
            return True
        return False

    def enemy_damage(self, eid: str, special_override: int | list | None = None) -> int | float:
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
        # web getDamageInfo: `if(core.hasItem("cross")&&["zombie","zombieKnight",
        # "vampire"].indexOf(enemy.id)>=0){hero_atk*=2}`. cross 拾取后存 items.constants
        # (core.getItem('cross') 后 hasItem('cross')=true 实证)。cross 在 items 期间双倍生效。
        # 注意：cross 可能在某事件后从 items 消耗——需 replayer 验证各 step hasItem 状态。
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
        # special_override 用于事件战斗：事件脚本可能在战前 setEnemy special
        # （如 MT32 (6,10) yellowKnight 事件设 special=1 先攻），战后再复位。
        # 静态 enemy 数据此时仍是 special=0，故需 override 才能匹配实机伤害。
        special = special_override if special_override is not None else enemy.get("special", 0)
        specials = set(special if isinstance(special, list) else [special])
        # web getDamageInfo: per_damage 修饰
        if 2 in specials:
            per = int(enemy["atk"])  # 魔攻：无视防御
        if 4 in specials:
            per *= 2
        if 5 in specials:
            per *= 3
        if 6 in specials:
            per *= int(enemy.get("n", 4))
        # web getDamageInfo: init_damage = 先攻(per) + 破甲(defValue*def) + 净化(purify*mdef) + 吸血(hp*value)
        # damage = init_damage + (turn-1)*per + turn*counterDamage - mdef
        init_damage = 0
        if 1 in specials:
            init_damage += per  # 先攻：怪物先打一次
        if 7 in specials:
            init_damage += int(enemy.get("defValue", 0)) * self.state["def"]
        if 9 in specials:
            init_damage += int(enemy.get("n", 0)) * self.state.get("mdef", 0)
        counter = 0
        if 8 in specials:
            counter = int(enemy.get("atkValue", 0)) * atk  # 反击：每回合 counterDamage
        damage = init_damage + (turns - 1) * per + turns * counter
        return damage


    def check_damage_at(self, fid: str, pos: tuple[int, int]) -> int:
        """Pure query: damage the hero WOULD take standing at pos right now.
        Must have NO side effects -- path_to/path_cost call this during routing
        to compare candidate cells, so it cannot mutate spell_cells_hit."""
        if self.state.get("magicImmune"):
            return 0
        x, y = pos
        total = 0
        f = self.floors[fid]
        spell = getattr(f, "_spell_enemies", None)
        if spell is None:
            # 合成 Floor（测试/探针直接构造，绕过 load 阶段）没有 _spell_enemies
            # 预计算；按同规则惰性算一次。加载器路径总会 set，不影响运行时性能。
            spell = f._spell_enemies = []
            for _pos, _blk in f.blocks.items():
                if _blk.kind != "enemy":
                    continue
                _sp = (self.enemies.get(_blk.eid, {}) or {}).get("special", 0)
                if 15 in (_sp if isinstance(_sp, list) else {_sp}):
                    spell.append(_pos)
        for (ex, ey) in spell:
            block = f.blocks.get((ex, ey))
            if not block or block.kind != "enemy":
                continue
            enemy = self.enemies.get(block.eid)
            if not enemy:
                continue
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
        # A dead hero (hp <= 0, only possible after a swallowed battle-death
        # RouteError) must not produce a NEGATIVE tile cost: path_cost feeds
        # Dijkstra, and a negative special-16 halving edge makes path_to
        # re-push nodes forever (2026-08-18 skeleton-swap candidate hang).
        # For a live hero hp > 0 this clamp is a no-op; for a dead one any
        # value is fiction, so clamp at 0 rather than poison the search.
        return max(total, 0)

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
            # fakeWall/fakeWall2 are noPass in live (core.noPass=true): a strict
            # click never routes through them (hero stops adjacent, the wall
            # breaks as the click target). Stairs are target-only by design
            # (avoid routing through floor-change triggers). flower stays
            # passable (one-way logic in go_to via can_enter_flower).
            #
            # Loose path (go_to_decomposed finding the first blocker) must be
            # allowed through a fakeWall when auto wall is ON, because auto_sweep
            # will break it -- otherwise a target sealed behind a fakeWall (e.g.
            # MT5 sword1 behind (9,11)) has no loose path and go_to_decomposed
            # gives up. can_enter_click_path still refuses it as an intermediate
            # tile, so strict single-click routing is unchanged.
            if block.eid in STAIRS:
                return pos == target
            if block.eid in {"fakeWall", "fakeWall2"}:
                if pos == target:
                    return True
                return bool(self.auto_flags.get("wall"))
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
            kk = DOOR_KEY.get(block.eid)
            return kk is not None and self.state[kk[0]] > 0
        if block.kind == "npc":
            # Passable NPCs (princess, thief) are step-on event triggers: the
            # hero routes through them and trigger_tile_event fires (e.g. MT26
            # (6,6) princess rescue). Other NPCs (shop/trader/oldman) are noPass
            # in live (face-on commonEvent): the hero stops adjacent, so they
            # block pathing. tile_mapping marks all NPCs noPass=false, but live
            # maps.initBlock defaults non-item cls to noPass=true unless the NPC
            # is a step-on trigger.
            return block.eid in PASSABLE_NPC_EIDS or (fid, pos) in PASSABLE_NPC_TILES
        return False

    def can_enter_click_path(self, fid: str, pos: tuple[int, int], target: tuple[int, int]) -> bool:
        """Passability for one real map click in strict live mode.

        A live click may end on an actionable target, but it does not route
        through unopened doors or live enemies to reach something behind them.
        Intermediate pickups are allowed because walking over an item is normal
        movement.

        A strict click path cannot cross a live enemy or unopened door. The web
        verifier must issue one real map click and let the game's own click
        router choose the path; keyboard/forced-movement fallbacks are forbidden.
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
        if block.kind == "npc":
            # Passable NPCs (princess, thief) can be routed through as an
            # intermediate tile (step-on event fires via trigger_tile_event).
            return block.eid in PASSABLE_NPC_EIDS or (fid, pos) in PASSABLE_NPC_TILES
        return False

    @staticmethod
    def _auto_item_allowed(eid: str, item_mode: Any) -> bool:
        if item_mode is True:
            return True
        if item_mode == "nopotion":
            # web potionIds (project.min.js 自动操作): redPotion/bluePotion/
            # greenPotion/yellowPotion/superPotion。本塔 50 层只有红/蓝血瓶
            # 落地（扫描核实），但排除集按 web 全集对齐防未来分歧。装备和
            # 工具仍自动收（MT37 bomb / MT44 shield5 实证）；用工具是显式动作。
            return eid not in {
                "redPotion", "bluePotion", "greenPotion", "yellowPotion", "superPotion",
            }
        return False

    def _retreat_wizard_trapped_for_auto(self, fid: str, pos: tuple[int, int]) -> bool:
        """Whether a known retreating wizard has no remaining escape tile.

        Direct target routing still treats these special enemies as retreating.
        The live auto plugin, however, battles one once its corridor endpoint is
        blocked (MT47 x8y3 by the closed x8y4 door, or either outer wall).

        格位来源（MT47 两条撤退走廊，2026-08-31 41218 实证）：右走廊 x8y1-y3
        （web 撤退链 8,2→8,1 / 8,2→8,3，(8,3) 可被 x8y4 门封死），左走廊
        x1y9-y11（撤退链 1,9→1,10→1,11，(1,11) 下缘是边界墙）。向任意方向
        撤退一步的通用实现需要 web moveOneStep 的方向参数化，当前按两条
        已知走廊的端点判定——超出 MT47 的撤退怪本塔不存在（special 15 怪
        仅 41-49 层，撤退机制仅 MT47 实测）。
        """
        if (fid, pos[0], pos[1]) not in self.retreat_wizards or fid != "MT47":
            return False
        x, y = pos
        if (x, y) == (8, 3):
            return self.block_at(fid, (8, 4)) is not None
        if (x, y) == (8, 1):
            return self.is_wall(fid, (8, 0))
        if (x, y) == (1, 11):
            return self.is_wall(fid, (1, 12))
        return False

    def auto_sweep(
        self,
        fid: str | None = None,
        *,
        battle: bool | None = None,
        item: Any = None,
        wall: bool | None = None,
        exclude: set[tuple[int, int]] | None = None,
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
        # web core.plugin.auto + bfs 精确模拟（源码 project.min.js core.plugin.auto / bfs）：
        # 单次 BFS（FIFO），从英雄位置出发，mapped 一次性（每格只 visit 一次）。
        # 方向顺序匹配 core.utils.scan: up(0,-1), left(-1,0), down(0,1), right(1,0)。
        # 每次 battle/item/wall 后 damage 实时重算（enemy_damage 用当前 atk/def），后续 visit
        # 的格子用新 damage 判定 → cascade：道具在敌人前 visit 时，拾取后敌人变 0-dmg 被清。
        # mapped 一次性保证反方向不 cascade：敌人在道具前 visit（当时非 0-dmg）不清且不再
        # visit，道具后即使变 0-dmg 也不补清（匹配 web MT9 x10y2 greenSlime 拾 shield1 后不清）。
        # 旧版 range(1) 全图 wall→battle→item 分批扫描既非 BFS 顺序也无 mapped 语义，已弃用。
        f = self.floors[fid]
        start = (self.state["x"], self.state["y"])
        # web core.plugin.auto: has(floor.events[heroLoc]) → 直接返回不跑 bfs。
        # 英雄站在事件格（如拾取后停在事件格）不触发自动清扫。
        if f"{start[0]},{start[1]}" in f.events:
            return []
        # web: deep=Infinity 除非英雄当前格 hasBlockDamage（checkBlock 的
        # damage/ambush/repulse/chase 四图，enableGentleClick false → deep=0）。
        # 2026-09-05 40145 修复（推翻 2026-08-30 41200 的"本塔四图恒空"结论）：
        # updateCheckBlock（project/functions.js）对 special 15 领域/16 夹击
        # **会**写入 damage 图，仅受 '!core.hasFlag("魔法免疫")' 限制——MT47
        # damage=[] 是因为该线已拿神圣盾（magicImmune），不是法术场不入图。
        # MT42（未拿盾）实测 damage 有 11 格。check_damage_at 与 updateCheckBlock
        # 同源（special 15/16 + magicImmune 全免 + 怪死场消），故可直接用它的
        # 起点值判 deep：hero 站在法术场/夹击格时 live sweep 完全不跑。
        deep = 0 if self.check_damage_at(fid, start) > 0 else 10 ** 9
        DIRS = ((0, -1), (-1, 0), (0, 1), (1, 0))  # up, left, down, right (core.utils.scan)
        mapped: dict[tuple[int, int], bool] = {start: True}
        queue: list[tuple[int, int]] = [start]
        rounds = 0
        while queue and rounds < deep:
            cur = queue.pop(0)
            # live 实证（2026-09-07 combo16 web 复验 + 9222 手动 core.auto()）：
            # auto BFS 不可从花丛格向外扩展——站 MT38 (2,5) 花丛手动触发 core.auto()
            # 也不拾取相邻可达的 (2,7) shield3。花丛对 auto BFS 是吸收格：可走入
            # （go_to 寻路按 can_enter_flower 单向合法），但 BFS 到达即止。
            cur_block = self.block_at(fid, cur)
            if cur_block and cur_block.kind == "terrain" and cur_block.eid == "flower":
                continue
            for dx, dy in DIRS:
                nxt = (cur[0] + dx, cur[1] + dy)
                if nxt in mapped:
                    continue
                nx, ny = nxt
                if nx < 0 or ny < 0 or nx >= f.width or ny >= f.height:
                    continue
                directional_block = self.block_at(fid, nxt)
                if (
                    directional_block
                    and directional_block.kind == "terrain"
                    and directional_block.eid == "flower"
                    and not self.can_enter_flower(fid, cur, nxt)
                ):
                    continue
                mapped[nxt] = True
                # web judge (project.min.js) 可达性前置检查（在 empty/enemy/item 之前）：
                # 事件格/changeFloor/fire 在 web 中带 block（extractBlocks），非 empty，直接阻断。
                loc_key = f"{nx},{ny}"
                if f.grid[ny][nx] == 103 or f.fg_at(nx, ny) == 103:
                    # fire (animates): canGoThrough false. web's getFgNumber
                    # checks the fgmap; the main grid may also carry 103. The hero can
                    # still moveOneStep onto fire (recording does), so this only blocks
                    # auto_sweep bfs, not go_to.
                    # 2026-08-30 实证保持阻挡：41200 一访 (7,1) 门步 walk-through 时
                    # live 未穿 (8,1)/(8,3) 火收集 x11 资源（曾经二访 (1,6) 窗口的
                    # +50 疑似穿火，后被商人/事件源排查否定，见 walk [888] MT47 (5,2)
                    # -4000G 兑换商人）。
                    continue
                if loc_key in f.change_floor:
                    cf = f.change_floor[loc_key] or {}
                    ignore_cf = cf.get("ignoreChangeFloor", self.flags.get("ignoreChangeFloor", False))
                    if not (ignore_cf and f.grid[ny][nx] == 0):
                        continue  # 楼梯 changeFloor: 默认 ignoreChangeFloor=false → 阻断
                if loc_key in f.events:
                    continue  # 事件格 event.data: canGoThrough false（如 MT20 [6,8] vampire 触发前）。
                    # event 触发后由 trigger_tile_event pop（MT20 (6,8) L1951 / MT15 (9,1) thief 走后），
                    # pop 后不再阻断，匹配 web canGoThrough。
                block = self.block_at(fid, nxt)
                if not block:
                    pass  # 空地，canGoThrough true
                elif block.kind == "terrain" or block.eid == "lava":
                    if block.eid == "fakeWall2":
                        # 暗墙 noPass=false 可穿 (canGoThrough true)：auto BFS 穿过不触发
                        # openDoor。破墙 + afterOpenDoor (如 MT19 (6,3) cross) 需 hero 显式
                        # step (arrow 破+stay / move:x:y 破+move)，和门统一 (门也不 auto 开)。
                        pass  # 可穿，不破不 after_action
                    else:
                        # web judge (project.min.js): only isWall(block.id===2),
                        # isLava(snow), isEnemy, isItem are auto-passable. flower is
                        # a terrain tile that is NOT canGoThrough in the auto bfs, so
                        # it must NOT be crossed -- crossing it over-reaches (e.g. MT38
                        # (3,1) reaching (2,7) shield3 through the (2,5) flower that web
                        # never reaches). 2026-08-16 fixed (39944 全防 line).
                        auto_terrain = wall and (
                            block.eid == "fakeWall"
                            or (block.eid == "lava" and bool(self.state.get("snow")))
                        )
                        if not auto_terrain:
                            continue  # 非自动墙：不通过
                        self.set_ground(fid, nxt)
                        self.after_action(fid, nxt, block)
                        handled.append(f"x{nx}y{ny} {block.eid}")
                elif block.kind == "item":
                    if (fid, nx, ny) in self.blocked_items:
                        continue
                    if not self._auto_item_allowed(block.eid, item):
                        continue  # nopotion 血瓶：performGetItem false → 不拾不通过
                    # web canGetItem = !hasBlockDamage(loc)（enableGentleClick=false）：
                    # damage 格（法术场/夹击）上的道具**不能远程拾取**（英雄必须
                    # 真走过去）。2026-09-05 40145 修复（推翻 2026-08-30 41200
                    # "四图不含法术场"结论——MT47 damage=[] 是 magicImmune 所致，
                    # 未拿盾的 MT42 damage 图非空）。magicImmune 下
                    # check_damage_at 恒 0，41200 (11,6) redBat 行为不变。
                    if self.check_damage_at(fid, nxt) > 0:
                        continue
                    self.apply_item(fid, block.eid)
                    self.set_ground(fid, nxt)
                    self.after_action(fid, nxt, block)
                    handled.append(f"x{nx}y{ny} {block.eid}")
                elif block.kind == "enemy" and battle:
                    if exclude and nxt in exclude:
                        continue  # 路径上待显式击杀的敌人：保留给独立战斗原子，不 auto 清
                    # core.plugin.auto refuses monsters with battle events.
                    # They must be clicked explicitly even at zero damage so
                    # the event can own the action boundary (MT32 paired blue
                    # guards are the critical example).
                    if loc_key in f.after_battle:
                        continue
                    if (
                        (fid, nx, ny) in self.retreat_wizards
                        and not self._retreat_wizard_trapped_for_auto(fid, nxt)
                    ):
                        continue
                    if (fid, nx, ny) in self.no_auto_farm:
                        continue
                    if not self._auto_can_battle(block):
                        continue  # 非 0-dmg/特殊/事件：canBattle false → 不清不通过
                    gain = int(self.enemies[block.eid].get("money", 0))
                    if self.state.get("coin"):
                        gain *= 2
                    self.state["gold"] += gain
                    self.set_ground(fid, nxt)
                    self.after_action(fid, nxt, block, auto=True)
                    handled.append(f"x{nx}y{ny} {block.eid}")
                else:
                    continue  # 墙/门/非 auto 敌人/未知：canGoThrough false
                # web bfs 每个 tile visit 后：if (hasBlockDamage(loc)) return
                # —— checkBlock 格（法术场/夹击等）可被访问（战斗/拾取/破墙照常
                # 结算）但**绝不扩展**（damage 格挡 BFS 前进）。
                # 2026-09-05 40145 修复（推翻 2026-08-30 41200"四图不含法术场"
                # 结论）：MT42 未拿盾时 damage 图非空（special 15/16 都入图，
                # project/functions.js updateCheckBlock），(8,5) 门步 BFS 被
                # (9,5) 法术场格挡住收不到顶部钥匙房；MT47 damage=[] 仅因
                # 已拿神圣盾（magicImmune → check_damage_at 恒 0，两侧行为
                # 一致）。41200 的 (11,6) redBat 场景在 magicImmune 下不受影响。
                # web 每次战斗/拾取/破墙后 updateCheckBlock 重算 → 怪死场消，
                # check_damage_at 从当前 blocks 实时计算，语义等价。
                if self.check_damage_at(fid, nxt) > 0:
                    continue
                queue.append(nxt)
            rounds += 1
        return handled

    def _auto_can_battle(self, block: Block) -> bool:
        """web canBattle (project.min.js): 0-dmg + 非特殊怪 + 无 guards + 无战斗事件。
        special 排除集 {12,13,14,19,21,26,27,28,29}（魔法/穿透/命中伪等不可auto）。
        hasEvent (afterBattle/beforeBattle/events/willLvUp) 与 guards 暂不检查：
        zone1/2 无战斗事件 auto 清怪；zone3+ 需要时再补 guard_mask/事件标记。"""
        eid = block.eid
        if self.enemy_damage(eid) != 0:
            return False
        enemy = self.enemies.get(eid, {})
        special = enemy.get("special", 0)
        specials = set(special if isinstance(special, list) else [special])
        if specials & {12, 13, 14, 19, 21, 26, 27, 28, 29}:
            return False
        return True

    def _check_auto_events(self, fid: str) -> None:
        """h5mota autoEvent (core.floors[fid].autoEvent): hero 每次行动后检查
        condition，满足则执行 data。在 auto_sweep 末尾调用，使生成的 item 不被
        当次 BFS 拾取（匹配 web 时序：autoEvent 在 auto BFS 之后触发，道具下次
        auto_sweep 才拾取）。
        MT34 (2,6) autoEvent: 中心 8 怪 (5,4)(7,4)(9,4)(11,4)(5,8)(7,8)(9,8)
        (11,8) 全清 -> hide (2,6) + setBlock 4 yellowKey (1,5)(3,5)(1,7)(3,7)
        + redKey (2,6)。实机 verifier：auto 杀最后 (11,8) bat 后当 step yk=0，
        下一步 move 触发 auto_sweep 拾取 +4YK+1RK。旧的 _after_action_impl
        afterBattle 建模（杀怪即生成 + 同次 BFS 拾取）与实机时序不符，已移除。"""
        if fid == "MT34" and not self.flags.get("mt34_center_reward"):
            center = {(5, 4), (7, 4), (9, 4), (11, 4), (5, 8), (7, 8), (9, 8), (11, 8)}
            if all(not (self.block_at(fid, p) and self.block_at(fid, p).kind == "enemy")
                   for p in center):
                self.set_block(fid, (2, 6), "item", "redKey", 23)
                for _p in [(1, 5), (3, 5), (1, 7), (3, 7)]:
                    self.set_block(fid, _p, "item", "yellowKey", 21)
                self.flags["mt34_center_reward"] = 1
        # MT39 中心对称飞行器谜题 (autoEvent["8,4"])：3x3 黄门 (2,2)-(6,6)，
        # 开 (4,2)+(6,4) 两扇（其余 7 扇关）后 openDoor (4,4) + setBlock
        # centerFly3 at (4,4)。hero 踩 (4,4) 拾取 centerFly3 -> centerFly+3。
        # 实机 statlog 1069 开 (4,2)，1071 开 (6,4)，1072 到 (4,4) 拾取。
        # converter 漏此 autoEvent 会导致 centerFly=0，后续 item:centerFly 失败。
        if fid == "MT39" and not self.flags.get("mt39_centerfly3"):
            puzzle_open = {(4, 2), (6, 4)}
            puzzle_closed = {(2, 2), (6, 2), (2, 4), (4, 4), (2, 6), (4, 6), (6, 6)}
            if (all(self.block_at(fid, p) is None for p in puzzle_open)
                    and all(self.block_at(fid, p) is not None for p in puzzle_closed)):
                self.set_block(fid, (4, 4), "item", "centerFly3", 331)
                self.flags["mt39_centerfly3"] = 1

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
        action = "开门"
        kk = DOOR_KEY.get(block.eid)
        if kk is None:
            self.fail(f"unmodeled live door {block.eid} at {fid} x{pos[0]}y{pos[1]}")
        self.state[kk[0]] -= 1
        self.state[kk[1]] += 1
        if self.state["yk"] < 0 or self.state["bk"] < 0 or self.state["rk"] < 0:
            self.fail(f"negative key after door {block.eid} at {fid} {pos}")
        self.set_ground(fid, pos)
        self.after_action(fid, pos, block)
        # 2026-08-30 41200 修复：开门时 hero 会经 walk-through/箭头踩上门格
        # （live #3671 箭头踩上带火的 (8,4) 门格），moveOneStep 火处理会清掉
        # 门格的火（(8,4) 的三步传播火由此消失，二访 (1,6) 到达 sweep 才能穿
        # (8,4) 进右下口袋）。旧的门分支跳过了火处理，模型火格持久残留 →
        # auto BFS 可达性与 live 分歧。同时按 _check_fire_retreat 语义处理
        # 门格相邻的撤退法师（一般无）。
        self._check_fire_retreat(fid, pos)
        # 2026-08-30 41200 录像修复：web 开门后 control.moveOneStep 补丁在 hero
        # 续走（continueAutomaticRoute）踏上**门格**的那一刻插入 core.auto()，
        # auto BFS 从门格起跑——门格通常无相邻伤害（hasBlockDamage=false → deep=∞），
        # 能穿过刚开的门远程收集 0 伤怪 + 道具（41200 MT47 (8,4) 实证）。旧约定
        # 「开门不触发自动BFS」的验证线（23076 等）只是竞态恰好把这次 sweep 计入
        # 下一步。verifier 对开门步确定性补一次「走进门格」点击触发同一 sweep。
        # hero 状态位置保持录像语义（箭头开门 hero 停邻格）——后续 arrow 序列的
        # 落点依赖它；sweep 临时以门格为起点跑（deep 判定与 live 一致），跑完还原。
        door_note = "到门前开门，开门后以门格为起点自动BFS"
        hx, hy = self.state["x"], self.state["y"]
        self.state["x"], self.state["y"] = pos
        handled = self.auto_sweep(fid)
        self.state["x"], self.state["y"] = hx, hy
        if handled:
            door_note += "; auto_sweep: " + ", ".join(handled)
        full_note = f"{note}; {door_note}" if note else door_note
        self.record("开门", pos, block.eid, before, full_note)

    def path_cost(self, fid: str, pos: tuple[int, int]) -> float:
        # Align with h5mota `_automaticRoute_deepAdd`: empty/fakeWall cost 1,
        # magic-damage cells add damage*100. Items cost 1 + small epsilon: 实机
        # automaticRoute 在等长路径里偏好不穿道具(如 MT40 (6,7)->(5,1) 走 column6
        # 避开 (5,4) bluePotion, 而非等长 column5 穿它); 但道具在直接最短路上仍会被
        # 穿过拾取(无等长空替代时, 如 strict test "target beyond pickup" 穿 redPotion)。
        # epsilon=0.1 仅在等长路径 tiebreak 时偏向空地, 不改变最短路结构。
        block = self.block_at(fid, pos)
        base: float = 1.0
        if block:
            if block.kind == "item":
                base = 1.1
            elif block.kind == "door":
                base = {"yellowDoor": 90, "blueDoor": 140, "redDoor": 180}.get(block.eid, 9999)
            elif block.kind == "enemy":
                dmg = self.enemy_damage(block.eid)
                base = 3 if dmg == 0 else 1000 + (99999 if dmg == float("inf") else int(dmg))
        # Removed (2026-08-11): a strict_live_model discount that used to give
        # event tiles cost 0.9 to "prefer routing through event triggers" (the
        # MT26 (6,6) princess case). That is not what live's automaticRoute
        # does: it does NOT discount event tiles, and a disruptive event tile
        # (e.g. the 40F boss (6,7)) interrupts the route, so automaticRoute can
        # never pass straight through it. The discount made go_to(MT40,5,7)
        # from (6,1) route through (6,7) and fire the 40F boss early, diverging
        # from the recording (see tmp/trace_mt40.py). Passable step-on NPCs
        # (princess/thief) are already walkable ground (cost 1.0) and their
        # events fire via trigger_tile_event / move_adjacent, so no discount is
        # needed to route through them.
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

    def _reachable_event_triggers(self, fid: str, target: tuple[int, int]) -> list[tuple[int, int]]:
        """Passable step-on event-trigger tiles reachable from the hero (loose
        path). Used by go_to_decomposed when the static BFS finds no path to the
        target because an event-opened door/wall blocks it: the recording's
        automaticRoute fires such triggers mid-move (e.g. MT15 (9,1) thief opens
        (8,1) unbreakableWall), and stepping on the trigger here fires its event
        (opening the door) so a re-plan can complete.

        Only passable step-on triggers: empty tiles or passable NPCs (thief).
        Doors/walls/enemies/shops are not step-on triggers (blockers handled by
        the normal decompose path, or noPass face-on NPCs). Excludes the hero's
        own tile and the target.
        """
        hx, hy = self.state["x"], self.state["y"]
        out: list[tuple[int, int]] = []
        for pos_str in list(self.floors[fid].events.keys()):
            parts = pos_str.split(",")
            if len(parts) != 2:
                continue
            tx, ty = int(parts[0]), int(parts[1])
            if (tx, ty) == (hx, hy) or (tx, ty) == target:
                continue
            blk = self.block_at(fid, (tx, ty))
            if blk is not None:
                # only passable NPCs (thief) are step-on triggers among blocks
                if not (blk.kind == "npc" and blk.eid in PASSABLE_NPC_EIDS):
                    continue
            if self.path_to(fid, (tx, ty), strict_click=False):
                out.append((tx, ty))
        return out

    def go_to(self, fid: str, x: int, y: int, note: str = "") -> None:
        # go_to 包装：最外层结束（= 一次 hero 行动结束）检查 h5mota autoEvent。
        # 实机 autoEvent 在 auto BFS 之后触发，生成的道具下次行动才拾取，
        # 所以 _check_auto_events 放在 go_to 末尾而非 auto_sweep 末尾——同 go_to
        # 内 auto_sweep 不会拾取刚生成的 item（还没生成），下次 go_to 拾取。
        # 递归 go_to 共享深度计数，仅最外层触发。
        self._go_to_depth = self._go_to_depth + 1
        try:
            return self._go_to_body(fid, x, y, note)
        finally:
            self._go_to_depth -= 1
            if self._go_to_depth <= 0:
                self._go_to_depth = 0
                self._check_auto_events(self.state["floor"])

    def _go_to_body(self, fid: str, x: int, y: int, note: str = "") -> None:
        target = (x, y)
        if target == (self.state["x"], self.state["y"]) and self.block_at(fid, target) is None:
            # A click on the hero's current empty tile is a live no-op: it does
            # not start auto BFS.  In particular, already standing beside an
            # NPC must not manufacture an auto_sweep before the NPC click.
            return
        # Live: when the hero is idle at the move's start, core.plugin.auto
        # fires once from the CURRENT position before automaticRoute moves. This
        # is normally a no-op (the previous action's destination sweep already
        # cleared everything reachable from here) -- EXCEPT when that previous
        # action's auto was blocked (target_after_battle_blocks_auto): e.g. MT25
        # blackMagician dies at (6,6), afterBattle spawns 4 redKeys at (4,8)(5,8)
        # (7,8)(8,8) but auto is skipped at the kill; the next move (e.g.
        # move:1:10) fires auto from (6,6), which CAN reach the redKeys, while
        # its destination (1,10) cannot. _pending_after_battle_sweep is set only
        # by that blocked-afterBattle kill, so we sweep the current position just
        # for the move that immediately follows it (and not for every go_to).
        if self.strict_live_model and getattr(self, "_pending_after_battle_sweep", False):
            self._pending_after_battle_sweep = False
            # The afterBattle-spawned/revealed reward AT this move's destination
            # (e.g. MT15 octopus -> pickaxe at x6y5) is picked up by STEP-ON in
            # live (apply_block -> PICKUP step), NOT by the move-start auto: the
            # afterBattle event is still processing so core.plugin.auto returns
            # early, and the hero simply walks onto the item tile. If this sweep
            # picked it up here, the pickup would have no step (kill after.pickaxe
            # =0 because auto was skipped; destination step before.pickaxe=1
            # because the sweep already took it -> stat_same -> coalesce drops the
            # step -> web never clicks the tile -> MT48 pickaxe use fails). Exclude
            # the destination tile from this sweep so step-on owns the pickup and
            # the walk emits a PICKUP step with the tool 0->1 transition. Distant
            # afterBattle rewards (e.g. MT25 blackMagician 4 redKeys) are still
            # swept here. blocked_items is restored after the sweep.
            dest_key = (fid, x, y)
            # This move-start auto is a side effect of the SAME click that routes
            # to the destination (live fires auto from the current position, then
            # automaticRoute moves). Its pickup (e.g. MT32 (1,10) sweeps +4yk+1bk
            # that its destination (3,8) cannot reach) must land on the arrival
            # step's before (pre-sweep) + note, else the arrival step is stat_same
            # with no auto_sweep note and coalesce drops it, losing the key gain
            # from the walk. Capture the pre-sweep state and the handled items here
            # and fold them into the arrival step below.
            pending_click_before = self.snapshot()
            self.blocked_items.add(dest_key)
            try:
                pending_sweep_handled = self.auto_sweep(fid)
            finally:
                self.blocked_items.discard(dest_key)
        else:
            pending_click_before = None
            pending_sweep_handled = []
        path_target = target
        target_block = self.block_at(fid, target)
        target_is_stair = bool(target_block and target_block.eid in STAIRS)
        strict_auto_enemy_target = bool(
            self.strict_live_model
            and target_block
            and target_block.kind == "enemy"
            and self.auto_flags.get("battle") is True
            and self.enemy_damage(target_block.eid) == 0
        )
        if strict_auto_enemy_target:
            adjacent_paths = []
            for adj in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                # The click router needs a tile the hero can actually stand on
                # beside the auto-battle target. An unopened door is actionable
                # as its own click target but is not a legal trigger tile for a
                # neighbouring enemy (MT14 rock x6y5 must not choose yellowDoor
                # x6y6 and spend an extra key).
                adj_block = self.block_at(fid, adj)
                if adj_block and adj_block.kind not in {"item"}:
                    if not (adj_block.kind == "terrain" and adj_block.eid == "flower"):
                        continue
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
        # 路径中每步移动的 auto_sweep（battle only）清的零伤怪 -- 收集起来，末尾
        # 一起记到最终 step 的 note，否则金币计入但 auto 标注漏（如 MT4 路过清
        # x4y11/x8y11 greenSlime +2G，只显示 (+7G) 不分 bluePriest+5 / auto+2）。
        path_auto_handled: list[str] = []
        # 路径上（非目标）的敌人保留给 is_enemy_kill 分支记录独立「击杀」原子，
        # 不让移动每步的 auto_sweep 提前 auto 清掉（否则战斗被压进拾取/到达 note，
        # 违反 strict 单原子原则）。目标敌人（strict_auto_enemy_target）不排除：
        # 它需 auto 清触发级联（如 darkKnight 死后清 whiteKing + 拾 blueGem）。
        path_kill_reserved: set[tuple[int, int]] = set()
        auto_target_eid = target_block.eid if strict_auto_enemy_target else None
        for p in path:
            if p == target:
                continue
            b = self.block_at(fid, p)
            if b is not None and b.kind == "enemy":
                path_kill_reserved.add(p)
        for pos in path[1:]:
            prev = (self.state["x"], self.state["y"])
            block = self.block_at(fid, pos)
            if block and block.kind == "terrain" and block.eid == "flower" and not self.can_enter_flower(fid, prev, pos):
                self.fail(f"wrong-way flower at {fid} x{pos[0]}y{pos[1]} from x{prev[0]}y{prev[1]}")
            if self.strict_live_model and block and block.kind == "door":
                door_before = self.snapshot()
                moved_to_door = (
                    self.state["x"] != strict_click_before["x"]
                    or self.state["y"] != strict_click_before["y"]
                )
                # A far target click first walks the hero to the tile beside
                # the noPass door. That ordinary movement runs full auto while
                # the door is still closed; the subsequent door interaction
                # itself does not restart auto. Fold both effects into the one
                # real click atom (MT43 x11y5 picks x10y8 yellowKey on approach).
                handled = (
                    self.auto_sweep(fid, exclude=path_kill_reserved)
                    if moved_to_door
                    else []
                )
                self.apply_block(fid, pos, block, note if pos == (x, y) else "")
                # Opening a door is its own action and does not restart the
                # auto plugin. The hero remains on the adjacent approach tile.
                all_handled = path_auto_handled + handled
                self.refresh_last_step_with_auto(
                    strict_click_before if all_handled else door_before,
                    all_handled,
                    "auto_sweep",
                )
                strict_opened_door = True
                # A door interaction ends the current real action. Re-plan the
                # remaining target from the new map instead of letting one
                # synthetic click cross the door and later action tiles.
                if pos != target:
                    self.go_to(fid, x, y, note)
                return
            if (
                self.strict_live_model
                and block
                and block.kind == "terrain"
                and block.eid in {"fakeWall", "fakeWall2"}
            ):
                # noPass target: hero stops on the adjacent tile (prev), the
                # fakeWall breaks. This is one real target click from the
                # original route origin, so fold the silent approach movement
                # and its auto effects into this atom. Do not move the hero
                # onto the wall tile.
                self.apply_block(fid, pos, block, note if pos == (x, y) else "")
                self.refresh_last_step(
                    strict_click_before,
                    "auto_sweep: " + ", ".join(path_auto_handled)
                    if path_auto_handled
                    else "",
                )
                if pos != target:
                    self.go_to(fid, x, y, note)
                return
            # A door click opens from the adjacent tile, but a completed battle
            # moves the hero onto the defeated enemy tile. This position is also
            # the origin of the post-battle auto BFS (for example MT14 x1y9
            # redPriest then auto-pick MT14 x1y11 blueKey).
            self.state["x"], self.state["y"] = pos
            # Empty event-trigger tile (no block): step-on events on cleared
            # tiles (e.g. MT24 (6,2) princess pathway, whose wall was cleared
            # by the MT26 rescue) aren't handled by apply_block (it only runs
            # for blocks). Fire the event explicitly; if it transitions floor
            # (e.g. 24F->50F), the remaining path is on the old floor, so stop.
            if not block and f"{pos[0]},{pos[1]}" in self.floors[fid].events:
                # Record arrival at the event tile before the transition/event
                # fires, so the verifier can click it (paired with the 换层 step
                # for changeFloor events like MT24 (6,2) -> MT50).
                if pos == path_target and note:
                    before_arrive = self.snapshot()
                    self.record("通过", pos, None, before_arrive, note)
                if self.trigger_tile_event(fid, pos):
                    if pos != target:
                        self.go_to(fid, x, y, note)
                    return
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
                # Web core.plugin.auto fires after every action, including an
                # en-route enemy kill during a multi-tile click: the post-battle
                # auto-BFS immediately clears newly-reachable 0-dmg enemies (e.g.
                # MT14 killing x6y5 rock opens x7y5 -> x8y5 bigBat is auto-cleared
                # right away). Without this the bigBat gold lands in the next
                # step's `before` instead of the kill step's `after`, diverging
                # from live. Refresh the kill step's after to capture it.
                if is_enemy_kill and self.strict_live_model:
                    has_after_battle_event = f"{pos[0]},{pos[1]}" in self.floors[fid].after_battle
                    handled = (
                        [] if has_after_battle_event
                        else self.auto_sweep(fid, exclude=path_kill_reserved)
                    )
                    all_handled = path_auto_handled + handled
                    if all_handled and self.steps:
                        self.refresh_last_step(strict_click_before, "auto: " + ", ".join(all_handled))
                    self._flush_deferred_after_effects()
                    if f"{pos[0]},{pos[1]}" in self.floors[fid].after_battle_auto:
                        after_event_handled = self.auto_sweep(fid, exclude=path_kill_reserved)
                        if after_event_handled and self.steps:
                            self.refresh_last_step(
                                strict_click_before,
                                "auto_sweep: " + ", ".join(after_event_handled),
                            )
                    # Battle/pickup/event tiles are strict action boundaries.
                    # Re-plan after the settled action so one offline route can
                    # never cross several live actions atomically.
                    if pos != target:
                        self.go_to(fid, x, y, note)
                    return
                if block.kind == "item" and self.strict_live_model:
                    # Walking toward a farther target may cross an item. Live
                    # stops that real action on the pickup, settles auto from
                    # the pickup tile, then requires a fresh click for the
                    # remainder (MT37 earthquake pocket: the first explicit
                    # potion pickup immediately auto-collects all non-potions).
                    handled = self.auto_sweep(fid, exclude=path_kill_reserved)
                    all_handled = path_auto_handled + handled
                    if all_handled and self.steps:
                        self.refresh_last_step(
                            strict_click_before,
                            "auto_sweep: " + ", ".join(all_handled),
                        )
                    if pos != target:
                        self.go_to(fid, x, y, note)
                    return
            else:
                if not (strict_auto_enemy_target and pos == path_target):
                    damage_step = len(self.steps)
                    self.apply_check_damage(fid, pos, note if pos == (x, y) else "")
                    damage_recorded = len(self.steps) > damage_step
                else:
                    damage_step = len(self.steps)
                    damage_recorded = False
                self.trigger_tile_event(fid, pos)
                # Web moveOneStep fire-retreat (project.min.js): stepping on a
                # fire tile (fgmap 103) makes adjacent redWizards retreat to the
                # 2-step tile (if empty), propagating fire. MT47 only. Must fire
                # before auto_sweep so the retreated wizard is at its new pos.
                is_fire_step = self.floors[fid].fg_at(pos[0], pos[1]) == 103
                self._check_fire_retreat(fid, pos)
                if damage_recorded and self.strict_live_model:
                    # checkBlock, its tile event, and auto settle are one live
                    # movement action. Fold event records into the damage atom
                    # and run auto from the post-event map (MT47 x8y1 moves the
                    # wizard before its resource pocket becomes reachable).
                    event_steps = self.steps[damage_step + 1:]
                    del self.steps[damage_step + 1:]
                    handled = self.auto_sweep(fid)
                    extras = [s.get("note", "") for s in event_steps if s.get("note")]
                    if handled:
                        extras.append("auto_sweep: " + ", ".join(handled))
                    step = self.steps[damage_step]
                    step["after"] = self.snapshot()
                    if extras:
                        step["note"] = "; ".join(filter(None, [step.get("note", ""), *extras]))
                if pos == path_target and note:
                    # If this click's move-start auto (pending_after_battle_sweep)
                    # picked rewards that the destination itself cannot reach, the
                    # arrival step must show the PRE-sweep state as before and fold
                    # the pickup into its note. Otherwise before==after (stat_same,
                    # no auto_sweep note) and coalesce drops the step, losing the
                    # pickup (e.g. MT32 keys) from the walk.
                    if pending_sweep_handled:
                        before = pending_click_before
                        auto_note = "; auto_sweep: " + ", ".join(pending_sweep_handled)
                    else:
                        before = self.snapshot()
                        auto_note = ""
                    # Mark fire-tile steps so the converter coalesce keeps them
                    # (automaticRoute can't route through fire; the verifier
                    # steps onto fire via arrow key).
                    rec_note = note + ("; 火格" if is_fire_step else "") + auto_note
                    self.record("到达", pos, None, before, rec_note)
                # Live automaticRoute (move:x:y) does NOT run core.plugin.auto at
                # intermediate path tiles -- the auto BFS fires once, AFTER the
                # hero settles at the destination (core.plugin.autoNextStep is
                # gated on the hero being idle, which it is not mid-route). Running
                # auto_sweep at each intermediate tile over-predicts: e.g. MT14
                # move:2:3 paths (2,5)->(2,4)->(2,3); an intermediate sweep at
                # (2,4) kills the 3 zombieKnight guards and spawns the (1,3)
                # redKey, then the destination sweep at (2,3) picks that just-
                # spawned redKey (rk 0->1). Live's single destination sweep kills
                # the guards + spawns the redKey in one single-pass BFS, so (1,3)
                # -- a wall when the BFS first reached it -- is NOT picked (rk=0);
                # the redKey needs the next explicit move (rec#997 up to (2,2)) to
                # be collected. Action blockers (door/enemy/item) on the path
                # still settle auto_sweep at their own branches above before
                # re-planning, so only the empty-tile intermediate sweep is
                # suppressed here. The destination sweep runs below (line ~1802).
        target_auto_handled = bool(
            strict_auto_enemy_target
            and self.block_at(fid, target) is None
            and any(entry.startswith(f"x{x}y{y} ") for entry in path_auto_handled)
        )
        if strict_auto_enemy_target:
            live_target = self.block_at(fid, target)
            if (
                live_target
                and live_target.kind == "enemy"
                and abs(self.state["x"] - x) + abs(self.state["y"] - y) == 1
            ):
                self.state["x"], self.state["y"] = target
                self._defer_after_action = True
                try:
                    self.apply_block(fid, target, live_target, note)
                finally:
                    self._defer_after_action = False
        if self.strict_live_model:
            # core.plugin.auto fires after every action settles, including after
            # opening a door (the hero stops on the adjacent tile, then auto-BFS
            # picks up newly-accessible items / breaks fakeWalls / battles 0-dmg
            # enemies). Previously this was skipped when a door was opened, which
            # caused the offline model to miss auto-pickups behind opened doors
            # (e.g. MT33 bluePotion after opening x8y2). Always run auto_sweep.
            # A stair click changes floor immediately when the hero reaches the
            # target. The live auto plugin does not get a final source-floor
            # sweep between stepping on the stair and changeFloor (MT48
            # downFloor must not farm a distant source-floor slimelord).
            # A 0-dmg target enemy with an afterBattle event: live auto fires
            # from the post-battle moveOneStep, but the afterBattle event is
            # already processing (event.id=="action"), so core.plugin.auto
            # returns early and never runs its BFS. The event's rewards (e.g.
            # MT15 octopus -> reveal pickaxe at x6y5) must be picked up by the
            # next EXPLICIT move (step-on getItem), not by auto. Skipping
            # auto_sweep here matches that timing; the after_battle_auto
            # restart below still handles events that genuinely re-enable auto.
            target_after_battle_blocks_auto = (
                strict_auto_enemy_target
                and f"{x},{y}" in self.floors[fid].after_battle
                and f"{x},{y}" not in self.floors[fid].after_battle_auto
            )
            if target_after_battle_blocks_auto:
                # The kill's auto was skipped, so the afterBattle-spawned
                # rewards (e.g. MT25 blackMagician 4 redKeys) stay reachable
                # from the current position. The next move must sweep from here
                # (its destination may not reach them) -- see _go_to_body start.
                self._pending_after_battle_sweep = True
            handled = (
                []
                if target_is_stair or target_after_battle_blocks_auto
                else self.auto_sweep(fid, exclude=path_kill_reserved)
            )
            # 合并路径中每步 battle-only auto 清的零伤怪（之前被丢弃，金币计入但 note 漏）。
            all_handled = path_auto_handled + handled
            if all_handled:
                note_suffix = "auto_sweep: " + ", ".join(all_handled)
                if len(self.steps) > strict_start_steps:
                    self.refresh_last_step(self.steps[-1]["before"], note_suffix)
                else:
                    self.record("auto_sweep", None, None, strict_click_before, note_suffix)
            if target_auto_handled and self.steps:
                # One real click on the enemy routes toward it; battle=true may
                # kill the target while the hero is still on the adjacent path
                # tile.  Keep this as one logical kill click, not an artificial
                # move followed by an already-missing kill.
                step = self.steps[-1]
                step["floor"] = fid
                step["pos"] = [x, y]
                step["action"] = "击杀"
                step["eid"] = auto_target_eid
                step["note"] = note_suffix
            # A zero-damage target is resolved in this separate strict-auto
            # branch rather than the en-route kill branch above. Preserve the
            # same conditional afterBattle semantics here: a flag-only branch
            # stops, while the branch that actually removes a mechanism door
            # restarts auto on the newly connected map.
            target_event_restarts_auto = f"{x},{y}" in self.floors[fid].after_battle_auto
            self._flush_deferred_after_effects()
            if target_event_restarts_auto:
                after_event_handled = self.auto_sweep(fid, exclude=path_kill_reserved)
                if after_event_handled and self.steps:
                    self.refresh_last_step(
                        self.steps[-1]["before"],
                        "auto_sweep: " + ", ".join(after_event_handled),
                    )

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
            kk = DOOR_KEY.get(block.eid)
            if kk is not None:
                self.state[kk[0]] -= 1
                self.state[kk[1]] += 1
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
        # A fakeWall/fakeWall2 break may spawn an item at the broken tile via
        # after_action (e.g. MT19 (6,3) fakeWall2 -> cross). go_to for a
        # fakeWall2 target stops the hero ADJACENT (it breaks the wall from the
        # neighbouring tile, matching live automaticRoute), so the hero is NOT on
        # pos -- but the recording's net effect is "break wall + pick up the
        # spawned item" (it breaks in one action, then steps onto the item in the
        # next; the converter coalesces both into one target click when the
        # break action is a before==after no-op). auto_sweep does not process the
        # hero's own tile and never reaches the item under an adjacent break, so
        # pick up the spawned item here. This only fires when after_action
        # actually spawned an item at pos (otherwise block_at is None), so plain
        # fakeWall2 breaks that reveal nothing are unaffected. The live verifier
        # re-clicks the tile (maybeRetryAdjacentTarget) to step onto the spawned
        # item, so the walk's after (item picked up) matches live after retry.
        if block.kind == "terrain" and block.eid in {"fakeWall", "fakeWall2"}:
            spawned = self.block_at(fid, pos)
            if (spawned and spawned.kind == "item" and spawned.eid != block.eid
                    and (fid, pos[0], pos[1]) not in self.blocked_items
                    and self._auto_item_allowed(spawned.eid, self.auto_flags.get("item"))):
                self.apply_item(fid, spawned.eid)
                self.set_ground(fid, pos)
                self.after_action(fid, pos, spawned)
                self.refresh_last_step(before, f"拾取 {spawned.eid} (破墙后生成)")
        self.apply_check_damage(fid, pos, note)
        return self.trigger_tile_event(fid, pos)

    def clear_mt10_boss_dyn(self) -> list[str]:
        """10F boss 动态清怪：boss trigger 后一步清完 8 spawned + captain。

        匹配 replayer clearMt10BossDyn + web 行为：web 点击 trigger (x6y5) 后，
        8 spawned(x4-8/y4-7) 包围 hero，auto-battle 一次清完，captain(x6y1) 经
        x6y2 剧情后击杀，hero 终点 x6y1。静默击杀（不记录单独 step），由调用方
        refresh_last_step 刷新 trigger step 的 after + note。顺序匹配 OLD walk：
        x5y4,x7y4,x6y4,x5y5,x7y5,x5y6,x6y6,x7y6,x6y1。"""
        order = [(5, 4), (7, 4), (6, 4), (5, 5), (7, 5), (5, 6), (6, 6), (7, 6), (6, 1)]
        cleared: list[str] = []
        for pos in order:
            block = self.block_at("MT10", pos)
            if not block or block.kind != "enemy":
                continue
            dmg = self.enemy_damage(block.eid)
            if dmg == float("inf"):
                self.fail(f"clear_mt10_boss_dyn cannot break {block.eid} at {pos}")
                continue
            self.state["hp"] -= int(dmg)
            self.state["dmg"] += int(dmg)
            gain = int(self.enemies[block.eid].get("money", 0))
            if self.state.get("coin"):
                gain *= 2
            self.state["gold"] += gain
            if self.state["hp"] <= 0:
                self.fail(f"clear_mt10_boss_dyn death at {pos} {block.eid} dmg={dmg}")
            cleared.append(f"x{pos[0]}y{pos[1]} {block.eid}")
            self.set_ground("MT10", pos)
            self.after_action("MT10", pos, block)
        # captain 击杀后 hero 站到 x6y1
        self.state["x"], self.state["y"] = 6, 1
        return cleared

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

    def after_action(self, fid: str, pos: tuple[int, int], block: Block, *, auto: bool = False) -> None:
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
            self._after_action_impl(fid, pos, block, auto=auto)
            return
        self._capturing = True
        self._captured = []
        try:
            self._after_action_impl(fid, pos, block, auto=auto)
        finally:
            self._deferred_after_effects.extend(self._captured)
            self._capturing = False
            self._captured = []

    def _after_action_impl(self, fid: str, pos: tuple[int, int], block: Block, *, auto: bool = False) -> None:
        # MT40 (6,1) 骑士队长踩在 upFloor 楼梯块上（live 实证 2026-08-31：骑士死后
        # 该格变为 upFloor（tile 87），hero 踩上即换层到 MT41——41218 录像四连 up）。
        # 旧模型数据里 knight 块覆盖了楼梯块，换层判定失效。
        if fid == "MT40" and block.kind == "enemy" and block.eid == "yellowKnight" and pos == (6, 1):
            self.set_block(fid, pos, "terrain", "upFloor", 87)
            self.floors[fid].change_floor["6,1"] = {"floorId": ":next", "stair": "downFloor", "time": 0}
        if fid == "MT8" and block.kind == "enemy" and pos in {(9, 5), (11, 5)}:
            self.flags["8redKeyGuards"] = self.flags.get("8redKeyGuards", 0) + 1
            if self.flags["8redKeyGuards"] >= 2:
                self.set_ground(fid, (10, 4))
        # MT10 captain (6,1) afterBattle (web MT10.afterBattle["6,1"]): captain 死后在外围放
        # 3 redGem(1-3,3) + 3 blueGem(9-11,3) + 3 bluePotion(1-3,4) + 3 yellowKey(9-11,4)，
        # 开门 (4,4)(6,7)(8,4)，清 (6,9)。hero 到 (6,8) 后 auto_sweep 经开门的 (4,4)(8,4)
        # 与已清空的 boss 区域可达外围，拾取 12 道具 = +3atk +3def +600hp +3yk (录像 ri=314)。
        if fid == "MT10" and block.kind == "enemy" and block.eid == "skeletonCaptain" and pos == (6, 1):
            if not self.flags.get("10f战胜骷髅队长"):
                for p in [(1, 3), (2, 3), (3, 3)]:
                    self.set_block(fid, p, "item", "redGem", 27)
                for p in [(9, 3), (10, 3), (11, 3)]:
                    self.set_block(fid, p, "item", "blueGem", 28)
                for p in [(1, 4), (2, 4), (3, 4)]:
                    self.set_block(fid, p, "item", "bluePotion", 32)
                for p in [(9, 4), (10, 4), (11, 4)]:
                    self.set_block(fid, p, "item", "yellowKey", 21)
                self.set_ground(fid, (4, 4))
                self.set_ground(fid, (6, 7))
                self.set_ground(fid, (8, 4))
                self.set_ground(fid, (6, 9))
                # web afterBattle["6,1"]: "show [6,11]" — 上 MT11 的楼梯在 captain
                # 死后才出现（base map events["6,11"] enable:false, 加载时已按此
                # 移除该块）。
                self.set_block(fid, (6, 11), "terrain", "upFloor", 87)
                self.flags["10f战胜骷髅队长"] = True
        # MT10 (6,3) autoEvent（web MT10.events["6,3"]）：
        # flag:10f机关 && 8 个竞技场格 (5,4)(6,4)(7,4)(5,5)(7,5)(5,6)(6,6)(7,6) 全空
        # -> openDoor (6,3)。captain 可达的硬门槛：竞技场必须全清。镜像 web 时序：
        # (6,5) spawn 事件重新 specialDoor 封 (6,3)，每只竞技场怪死后检查一次。
        if (
            fid == "MT10"
            and self.flags.get("mt10_boss_spawned")
            and not self.flags.get("mt10_arena_open")
        ):
            door63 = self.block_at("MT10", (6, 3))
            if door63 is not None and door63.kind == "door" and door63.eid == "specialDoor":
                if all(
                    (b := self.block_at("MT10", p)) is None or b.kind != "enemy"
                    for p in [(5, 4), (6, 4), (7, 4), (5, 5), (7, 5), (5, 6), (6, 6), (7, 6)]
                ):
                    self.set_ground("MT10", (6, 3))
                    self.flags["mt10_arena_open"] = True
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
        # MT17 right-section specialDoors (afterBattle flag:173/174):
        # kill (9,8)+(11,8) zombie -> open (10,7); kill (9,5)+(11,5) zombieKnight -> open (10,4).
        # Order matters: (10,7) must open before hero can reach (9,5)/(11,5) to open (10,4).
        if fid == "MT17" and block.kind == "enemy":
            if block.eid == "zombie" and pos in {(9, 8), (11, 8)}:
                self.flags["17rightLowerGuards"] = self.flags.get("17rightLowerGuards", 0) + 1
                if self.flags["17rightLowerGuards"] >= 2:
                    self.set_ground(fid, (10, 7))
            if block.eid == "zombieKnight" and pos in {(9, 5), (11, 5)}:
                self.flags["17rightUpperGuards"] = self.flags.get("17rightUpperGuards", 0) + 1
                if self.flags["17rightUpperGuards"] >= 2:
                    self.set_ground(fid, (10, 4))
        # MT32 specialDoor (2,9) (afterBattle flag:32):
        # kill (1,10)+(3,10) blueGuard -> open (2,9). (2,9) is the ONLY bottom->top path on MT32.
        if fid == "MT32" and block.kind == "enemy" and block.eid == "blueGuard" and pos in {(1, 10), (3, 10)}:
            self.flags["32blueGuards"] = self.flags.get("32blueGuards", 0) + 1
            if self.flags["32blueGuards"] >= 2:
                self.set_ground(fid, (2, 9))
        # MT33 swordTrap 机关门 (10,4)/(10,8) (afterBattle: 4 sword guards):
        # swordTrap 事件在 (10,5) 触发时 spawn specialDoor at (10,4)+(10,8)（见
        # zone3_game_route.py "事件" 分支）。杀完 4 守卫 (9,5)(11,5)(9,7)(11,7) 后开门。
        # (10,8) 是 sword3 房间 (x9-11,y9-11) 的唯一入口；未 spawn/未开则离线
        # auto_sweep 会在杀第 1 个守卫后就拿到 sword3，与实机不符（实机要 4 个全死
        # 开门后才显式拾取）。开门走 deferred 路径（go_to 杀怪时 _defer_after_action=True），
        # 故 post-battle auto_sweep 看到门仍关，flush 后才开，匹配 web 时序。
        # 旧 GuideReplay 的同类补丁已归档；这里是通用事件模型的唯一实现。
        if fid == "MT33" and block.kind == "enemy" and pos in {(9, 5), (11, 5), (9, 7), (11, 7)}:
            _mt33_sword_guards = {(9, 5), (11, 5), (9, 7), (11, 7)}
            remaining = {p for p in _mt33_sword_guards if self.block_at(fid, p)}
            if not remaining:
                self.set_ground(fid, (10, 4))
                self.set_ground(fid, (10, 8))
        # MT2 steelDoors (afterBattle flag:2):
        # kill (6,2)+(8,2) blueGuard -> open ALL 6 steelDoors (5,5)/(5,8)/(5,11)/(9,5)/(9,8)/(9,11).
        # These gate the oldman (11,4), thief (10,11), and yellowKey pockets.
        if fid == "MT2" and block.kind == "enemy" and block.eid == "blueGuard" and pos in {(6, 2), (8, 2)}:
            self.flags["2blueGuards"] = self.flags.get("2blueGuards", 0) + 1
            if self.flags["2blueGuards"] >= 2:
                for p in [(5, 5), (5, 8), (5, 11), (9, 5), (9, 8), (9, 11)]:
                    self.set_ground(fid, p)
        # MT34 中心 8 怪事件已移到 _check_auto_events（h5mota autoEvent 在
        # auto_sweep 末尾触发，非 afterBattle；杀怪即生成会被同次 BFS 拾取，
        # 与实机"下次行动才拾取"时序不符）。见 _check_auto_events 注释。
        # MT38 骑士盾房机关：左右两个 blueGuard (1,10)/(3,10) 共用
        # flag:38；第二只死亡后打开 (2,9) specialDoor。该门是通往
        # MT38 x2y7 shield3 的唯一入口。事件来自 data/maps/mt38_map.json
        # afterBattle，属于通用地图变化，不是单条 walk 坐标跳过。
        if fid == "MT38" and block.kind == "enemy" and pos in {(1, 10), (3, 10)}:
            guards = {(1, 10), (3, 10)}
            if not any(self.block_at(fid, p) for p in guards):
                self.set_ground(fid, (2, 9))
        # MT44 specialDoor (6,8) (afterBattle flag:44，web mt44_map.json):
        # kill (5,9)+(7,9) redGuard -> open (6,8)（通往 shield5 口袋的唯一入口）。
        # 炸弹击杀同样触发 afterBattle（41301 walk [970] 炸弹双杀 -> [971] 过门
        # web-verified），use_bomb 走同一 after_action 钩子，无需单独处理。
        if fid == "MT44" and block.kind == "enemy" and block.eid == "redGuard" and pos in {(5, 9), (7, 9)}:
            guards = {(5, 9), (7, 9)}
            if not any(self.block_at(fid, p) for p in guards):
                self.set_ground(fid, (6, 8))
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
        # MT30 六只史莱姆共同控制中心机关门。真实楼层事件在第六只
        # afterBattle 时打开 (6,4)；这是地图级事件，所有路线共享，不能由
        # 某条 walk 假定机关门已经消失。
        if fid == "MT30" and block.kind == "enemy" and pos in {
            (3, 5), (4, 5), (5, 5), (7, 5), (8, 5), (9, 5),
        }:
            guards = {(3, 5), (4, 5), (5, 5), (7, 5), (8, 5), (9, 5)}
            if not any(self.block_at(fid, p) for p in guards):
                self.set_ground(fid, (6, 4))
                self.flags["30"] = 5
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
            # These redKeys spawn after the kill's destination auto_sweep ran, so
            # they are not picked at the kill. They ARE reachable from the hero's
            # current position (6,6); the next move must sweep from here (its
            # destination (1,10) cannot reach them). See _go_to_body start.
            self._pending_after_battle_sweep = True
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
                    # TE late-49: 50F thief set 50final (boost redKing to
                    # 5000/1580/190); the 49F seal drops it back to 49sealed
                    # stats (500/158/19 via 50thief). Clear 50final here so
                    # both the 49F fake and the 50F true redKing use sealed
                    # stats -- matches guide clear_mt49_from_center (50final=False)
                    # and the game quirk that the seal also seals the 50F boss.
                    self.flags["50final"] = False
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
                # 真实 afterBattle["6,3"]（杀 49F redKing）最后 openDoor (6,7)+(6,9)：
                # 录像在杀 redKing 后立即下到 (6,8) 杀 (5,8)/(7,8) darkKnight 与
                # (5,10)/(7,10) redWizard。若不开这两扇门，conv 到不了 (6,8)，
                # 拿不到 +420 金 -> 买不起 MT45 (9,3) hp2000 商人(缺 420 G)。
                # 下方 491/492 flag 分支(杀两组怪后开门)仍是真实地图语义，但录像
                # 顺序是 redKing 先开(两门)，故两处都须成立。
                self.set_ground(fid, (6, 7))
                self.set_ground(fid, (6, 9))
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

    # 事件 trigger 点的人读描述（hero 踩该格触发楼层事件 spawn/移动/开门）。与下方
    # trigger_tile_event 的事件分支一一对应（新增事件点须同步两处）。gen_zone_walk_md
    # 导入此映射，在 walk .md 的 trigger-event pass 步加 (触发: ...) 备注，避免 gen
    # 手写映射分叉。gen 无 runtime flags 不能自动推断完整原因，此处简短事件名即可。
    # 架构定位：这张表就是「1-50F 唯一管线」的楼层事件适配层——不拆到各 zone
    # 脚本的原因：一条 4-50 层录像跨全部楼层，适配层跟随共享 Game 才能让
    # converter/verifier/审计读到同一套事件边界（拆散会重现"为单线打补丁"）。
    TRIGGER_EVENT_DESC = {
        ("MT10", (6, 5)): "10F boss spawn",
        ("MT10", (6, 2)): "队长剧情对话",
        ("MT10", (6, 9)): "小偷事件开路",
        ("MT15", (9, 1)): "小偷对话开门",
        ("MT20", (6, 8)): "吸血鬼入场",
        ("MT42", (5, 10)): "骑士队长逃跑",
        ("MT47", (8, 1)): "红巫师下移",
        ("MT41", (9, 2)): "撞墙出红巫师",
        ("MT40", (6, 7)): "40F 骑士队长 boss 事件",
        ("MT49", (6, 6)): "49F 假魔王封印事件",
        ("MT50", (6, 5)): "50F 小偷现身真魔王",
        ("MT26", (6, 6)): "26F 营救公主",
        ("MT24", (6, 2)): "24F 公主通路到50F",
        ("MT16", (11, 11)): "16F 圣水老人",
    }

    def trigger_tile_event(self, fid: str, pos: tuple[int, int]) -> bool:
        """hero 踩 pos 触发楼层事件(spawn/移动/开门)。返回是否触发任何事件。

        walk emit 时触发事件的 pass step 须单独保留(v2 不合并):web automaticRoute
        中途踩事件格会中断寻路(如 MT10 (6,5) boss spawn 后 6,6 变怪挡路,hero 卡 6,5)。"""
        triggered = False
        # COW 必须先于任何 events 突变: clone 共享 Floor 对象(_owned=False),
        # 下面的 events.pop 直接改共享字典会泄漏到 clone(实锤: MT50(6,5) 小偷
        # 事件在原体先触发后, clone 里 "6,5" 已被 pop, 事件永不再触发,
        # [1198] 红魔王不 spawn)。set_block/set_ground 内部自带 _cow,
        # 但裸 events.pop 没有, 统一在入口补齐。
        self._cow(fid)
        # 3F (5,9) 魔王布阵剧情（1F 新游戏线专用，41206 转换实证）。门控 =
        # 塔旗标 flag:03（事件 [0] 置位）：4F 种子线 flag:03 已置 → 永不触发
        # （agentH 回归教训：用自造 flag 门控会让 41231 基线转换踩格即削弱）。
        # 事件尾部
        # setValue 绝对赋值 hp=400/atk=10/def=10（非 delta）、清 nowWeapon/
        # nowShield/魔法免疫，hide remove:true 移除召唤怪 (5,7)/(5,8)/(4,9)/
        # (6,9)/(5,10) + 事件格 (5,9) 自身（一次性），changeFloor MT2 (3,8)。
        # statlog 双帧：[16] after=MT3 (5,9) 削弱态（事件中），[17] before=
        # MT2 (3,8)（传送后）——walk 单 事件 step 记传送后净态（同 MT24 公主
        # changeFloor 模式）。4F 种子线 flag:03 已置、事件已被 live 移除再武装
        # 的语义由 memory「加载存档重新武装」覆盖：4F 线踩上仍会触发（旧建模
        # 语义=召唤无收益，搜索绕开），本分支用 mt3_demon_arrange flag 保证
        # 一次会话只触发一次剧情削弱。
        if fid == "MT3" and pos == (5, 9) and not self.flags.get("03"):
            before = self.steps[-1]["before"] if self.steps else self.snapshot()
            self.state["hp"] = 400
            self.state["atk"] = 10
            self.state["def"] = 10
            self.state["magicImmune"] = False
            for p in [(5, 7), (5, 8), (4, 9), (6, 9), (5, 10), (5, 9)]:
                self.set_ground(fid, p)
            self.floors[fid].events.pop("5,9", None)
            self.flags["03"] = 1
            self.flags["mt3_demon_arrange_story"] = 1
            # 监狱跳跃：传 MT2 (3,8) 后 hero 的出狱移动 (3,8)->(1,8)->(1,10)
            # 是点击瞬移（(2,8) 墙/(1,9) unbreakableWall 之间，statlog 19-22
            # 位移实证；live automaticRoute 对这两段无逐格动画）。静态网格
            # 保持原状（墙不开），跳跃由 converter 的 jail-jump 特例执行。
            self.state["floor"] = "MT2"
            self.state["x"], self.state["y"] = 3, 8
            self.visited.add("MT2")
            # 净态并入踩格步（MT32 (6,10) 模式）：live 踩上 (5,9) 事件立即
            # 削弱+传送，walk 的踩格步 after 必须是事件后态（MT2 (3,8)），
            # 否则 verifier 在踩格步就 mismatch。**保持踩格步身份**（pos=(5,9)、
            # action=通过/到达）：verifier 对 换层 步不点击，改标换层会让 hero
            # 永远踩不上事件格（2026-09-13 41206 复验实证）。
            self.refresh_last_step(before, "3F 魔王布阵剧情：削弱 hp=400/atk=10/def=10，传 MT2 (3,8)")
            triggered = True
        # 47F x8y1 (adjacent to the x8y2 redWizard): the wizard's (8,2)->(8,3)
        # retreat is NOT a floor event -- it is the generic moveOneStep
        # fire-retreat (the hero steps the x8y1 fire tile), fully modeled by
        # _check_fire_retreat including the fgmap updates (fire set at the old
        # pos (8,2) + 3-step (8,4), cleared at the new pos (8,3)). The
        # spell-field damage for x8y1 is applied before the retreat either way
        # (apply_check_damage runs before _check_fire_retreat in _go_to_body).
        # Verified live: web auto later kills the corner-trapped wizard at
        # (8,3) remotely via the eastern row1 path once it is 0-damage.
        if fid == "MT42" and pos == (5, 10) and self.block_at(fid, (6, 10)):
            before = self.snapshot()
            self.set_ground(fid, (6, 10))
            # 2026-09-10 39547/40520 修复：逃跑事件触发后必须消费 events——
            # live 事件脚本跑完即从 events 表移除；模型残留 "5,10"/"6,10" 会让
            # 后续 auto BFS 把这两格当事件格阻断（auto_sweep L1193），MT42
            # (5,11)/(6,11) 方向的 sweep 够不到 (7,1) redKey → MT25 (6,10)
            # 红门开不出 → 公主救援/24F 通路全断（39547 转换死于 MT24）。
            self.floors[fid].events.pop("5,10", None)
            self.floors[fid].events.pop("6,10", None)
            self.record("事件", pos, "yellowKnightEscape", before, "42F 骑士队长剧情逃跑")
            triggered = True
        if fid == "MT32" and pos == (6, 10) and not self.flags.get("mt32_yellowknight"):
            # 32F (6,10) yellowKnight 先攻事件战:hero 踩 (6,10) 触发 yellowKnight
            # spawn(10,1)->move 到 (6,10) 处 battle(setEnemy special=1 先攻),战后 yellowKnight
            # 逃跑(hide)。hero 掉 enemy_damage(special_override=1) + 拿 money;yellowKnight 不留 block。
            # 同步 hide (6,2)/(6,9) 开路;event 一次性 pop 解除 auto/path 阻断。
            # 静默(不 record 事件 step):web 踩 (6,10) 在 step-onto 即触发,效果须并入通过 step 的
            # after -- refresh_last_step 把当前态(含 -420HP/+100G)写回通过 step。这是首个变 HP/gold
            # 的 trigger(MT10/MT20 spawn、MT42/MT47 逃均不变 stat,pre-event after 即事件后态),
            # 不能留 pre-event after,否则 reloader 点通过 step 后 web 实机已掉血 -> mismatch。
            # 例外:若上一 step 是换层(hero 刚从楼梯落到 MT32,下一步才踩 (6,10)),事件不能并入
            # 换层 step--那会让换层 after 变成 (6,10) 的事件后态,而实机换层只落到 (6,11)。此时事件
            # 必须独立 record,verifier 把换层(落点 (6,11))与事件((6,10))分别校验。
            prev_is_transition = bool(self.steps and self.steps[-1].get("action") == "换层")
            before = self.snapshot() if prev_is_transition else (self.steps[-1]["before"] if self.steps else self.snapshot())
            dmg = self.enemy_damage("yellowKnight", special_override=1)
            gain = int(self.enemies["yellowKnight"].get("money", 0))
            gain *= (2 if self.state.get("coin") else 1)  # coin 双倍金币(对齐 zone3_game_route.event_mt32_yellow_knight)
            self.state["hp"] -= int(dmg)
            self.state["dmg"] += int(dmg)
            self.state["gold"] += gain
            for p in [(6, 10), (6, 2), (6, 9)]:
                if self.block_at(fid, p) is not None:
                    self.set_ground(fid, p)
            self.floors[fid].events.pop("6,10", None)
            self.flags["mt32_yellowknight"] = 1
            note = f"32F (6,10) 骑士队长先攻事件战 -{int(dmg)}HP +{gain}G"
            if prev_is_transition:
                self.record("事件", pos, "yellowKnight", before, note)
            else:
                self.refresh_last_step(before, note)
            triggered = True
        if fid == "MT41" and pos == (9, 2) and self.flags.get("41") == 1 and (
            not self.block_at(fid, (10, 2)) or self.block_at(fid, (10, 2)).eid != "redWizard"
        ):
            before = self.snapshot()
            self.set_block(fid, (10, 2), "enemy", "redWizard", 220)
            self.flags["41"] = 2
            self.record("事件", (10, 2), "redWizard", before, "41F 右上撞墙出现红巫师")
            triggered = True
        if fid == "MT15" and pos == (9, 1) and not self.flags.get("mt15_thief"):
            # 15F thief x9y1: noPass NPC (trigger="action"). hero 停相邻格 (9,2)
            # 面朝 (9,1) 触发 thief 对话 -> openDoor (8,1) + thief 离开 (move left:3
            # 走到 (6,1)）(events["9,1"] move loc (9,1) steps left:3)。录像 [370]
            # `up` (9,2)->(9,2) 纯转身 face-on。converter _reach_event_trigger
            # move_adjacent(9,2) + 本方法（pos=(9,1)）+ record 事件 at (9,1)。
            # event 触发后 (9,1) 变普通格（web 可穿），auto_sweep 才能穿
            # 过 (9,1) 打到 (1,10)/(3,10) bigBat 与 (3,3) blackSlime。
            # (8,1)=330=unbreakableWall 在 WALL_IDS 内 -> classify "wall"，Game 创建墙 block
            # （非 None，旧注释"已 None"错误）。live openDoor(8,1) 把它开成空地，Game 必须
            # set_ground 移除墙，否则到 (5,1) 的唯一干净路径（无怪/门）被 (8,1) 墙封死，
            # move:5:1 unreachable（thief 在移动中途踩 (9,1) 才开 (8,1)，静态 BFS 规划时
            # (8,1) 仍是墙 -> go_to_decomposed 需先踩 (9,1) 触发再重规划，见 go_to_decomposed）。
            # thief move 到 (6,1) 楼梯无 block（thief 已被下方 set_ground(9,1) 移除）。
            self.set_ground(fid, (8, 1))
            # thief 离开 (9,1)（events["9,1"] move loc (9,1) steps left:3 走到 (6,1)）。
            # 必须移除 (9,1) thief block，否则 hero 在 (9,2) 被 noPass thief 挡住，
            # 无法穿 (9,1)->(8,1) 到 (5,1)（旧 passable-thief 模型踩上 (9,1) 掩盖此 bug）。
            self.set_ground(fid, (9, 1))
            self.floors["MT15"].events.pop("9,1", None)
            self.flags["mt15_thief"] = 1
            triggered = True
        if fid == "MT2" and pos == (3, 7) and not self.flags.get("mt2_jail_thief"):
            # 2F 监狱小偷（41206 1F 新游戏线实证）：布阵剧情把 hero 传进监狱
            # (3,8) 后，向上面向 (3,7) 小偷触发越狱对话——openDoor (2,7) 打开
            # 监狱暗道、小偷 left:2/down:2 离开并 hide。之后出狱步行
            # (3,8)->(3,7)->(2,7)->(1,7)->(1,8)->(1,9)->(1,10)->(1,11) 楼梯
            # 全部按静态网格可达（(1,9)=0 不是墙；第一次读格错列误判 330）。
            # 4F 种子线 thief 事件已被消费且 hero 不再进监狱，flag 门控兜底。
            self.set_ground(fid, (2, 7))   # openDoor (2,7) 越狱暗道
            self.set_ground(fid, (3, 7))   # 小偷离开 (3,7)
            # 小偷 left:2/down:2 走到 (1,9) 驻留（live 实证 2026-09-13：越狱事件
            # 后 (1,9) thief noPass=true 阻挡 col-1 出狱路；录像 statlog 21 的
            # move:1:10 是小偷 walk 未完成时的时序运气点击）。walk 侧出狱 =
            # 到达 (1,8) 后显式触发 (1,9) 告别事件（见 mt2_jail_farewell 分支），
            # hero 停留 (1,8)、小偷 hide，之后 (1,9) 永久通行（NPC 运行时移动
            # 不跨楼层持久化，后续 fly:MT2 回访 (1,9) 为空）。
            self.set_block(fid, (1, 9), "npc", "thief", 0)
            # 注意 (2,8) 是静态 yellowWall（live runtime 实证 noPass=true），
            # 越狱事件不开它——出狱路走 (3,7)->(2,7)->(1,7)->(1,8)。
            self.floors[fid].events.pop("3,7", None)
            self.flags["mt2_jail_thief"] = 1
            triggered = True
        if (fid == "MT2" and pos == (1, 9) and self.flags.get("mt2_jail_thief")
                and not self.flags.get("mt2_jail_farewell")):
            # 越狱小偷告别（41206）：hero 站 (1,8) 相邻面向驻留小偷（点击会
            # 被 noPass 挡住只触发交互），触发 farewell 对话后小偷 move down:2
            # + hide——hero 不移动，(1,9) 变空地永久通行。由 converter 的
            # 监狱出狱特例在 hero (1,8) 时显式调用。
            self.set_ground(fid, (1, 9))
            self.flags["mt2_jail_farewell"] = 1
            triggered = True
        if fid == "MT33" and pos == (10, 5) and not self.flags.get("mt33_sword_trap"):
            # 33F 骑士剑机关（2026-09-26 40935 录像修正，实机 mt33_map.json 事件全解码）：
            # 踩 x10y5 后【无条件】x11y4 = yellowWall（黄墙不可开——旧模型建成
            # yellowDoor 导致 go_to 穿门顺路误拾 (11,3) 蓝瓶，+800 假增益）；
            # 再按实机 if 条件分叉：四守卫 (9,5)(11,5)(9,7)(11,7) 仍有存活 →
            # 两端 spawn specialDoor x10y4/x10y8（四守卫全灭由 after_action 开
            # 两门）；已全灭（如 40935 录像先 auto 清 0 伤守卫再踩机关）→ 不
            # spawn，机关只封 x11y4 即隐没。在此之前 sword3 房必须不可达，避免
            # auto_sweep 在第一只守卫后提前拿剑。
            self.set_block(fid, (11, 4), "wall", "yellowWall")
            _mt33_trap_guards = {(9, 5), (11, 5), (9, 7), (11, 7)}
            if any(self.block_at(fid, p) for p in _mt33_trap_guards):
                self.set_block(fid, (10, 4), "door", "specialDoor")
                self.set_block(fid, (10, 8), "door", "specialDoor")
            self.floors[fid].events.pop("10,5", None)
            self.flags["mt33_sword_trap"] = 1
            triggered = True
        if fid == "MT2" and pos == (11, 4) and not self.flags.get("mt2_oldman_gold"):
            # 2F (11,4) 老人：hero 相邻按方向触发 systemEvents.oldman ->
            # commonEvent "对话" arg1=楼层号(2) -> choices[谢谢] -> 谢谢分支
            # case 2: status:money += 1000 + tip "获得1000金币"；尾部 set flag
            # "对话2" + hide (11,4) remove=true 移除 oldman block。一次性。
            # oldman 是 noPass NPC(can_enter 对 kind=npc 返回 False)，hero 不踩
            # 上去；由 converter _reach_event_trigger(move_adjacent + 本方法) 触发，
            # 后者负责 record 事件 step（本方法只改状态，不 record，同 MT29 thief）。
            self.state["gold"] += 1000
            self.set_ground(fid, pos)
            self.flags["mt2_oldman_gold"] = 1
            triggered = True
        if fid == "MT2" and pos == (10, 11) and not self.flags.get("mt2_thief_mt35"):
            # 2F 小偷后续对话：hero 踩 x10y11 后，小偷前往 35F，移除 MT35
            # x4y9 黄墙并在 x5y10 显示小偷。该事件不改变当前库存，却是
            # 35F->36F 楼梯通路的前置；不能被录像的零效果 move/arrow 剪掉。
            self.set_ground("MT35", (4, 9))
            self.floors[fid].events.pop("10,11", None)
            self.flags["mt2_thief_mt35"] = 1
            triggered = True
        if fid == "MT2" and pos == (11, 7) and not self.flags.get("mt2_bless"):
            # 2F (11,7) specialTrader 祝福：免费 +3% 攻击力和 +3% 防御力
            # (Math.round)，一次性。录像在终局 stats 高时用(atk267->275,
            # def543->559)。specialTrader 可通行(noPass=false)，hero 踩上触发。
            self.state["atk"] += int(self.state["atk"] * 0.03 + 0.5)
            self.state["def"] += int(self.state["def"] * 0.03 + 0.5)
            self.flags["mt2_bless"] = 1
            triggered = True
        if fid == "MT20" and pos == (6, 8) and not self.flags.get("mt20_vampire") and "6,8" in self.floors[fid].events:
            # 20F vampire: stepping onto (6,8) triggers the boss entrance -- 8
            # bigBats spawn around (6,6), merge into the vampire, and a
            # specialDoor seals the south exit (6,9) until the vampire dies
            # (afterBattle opens 6,3 + 6,9). Live: hero steps onto (6,8) ->
            # event -> vampire at (6,6), hero stays at (6,8). The 8 spawn tiles
            # (incl. the original (6,5) bigBat and (5,5) whiteWall2 decor) are
            # cleared by the merge -- the bigBats never battle individually, so
            # no gold is gained for them (only the vampire's afterBattle money).
            # go_to records the ARRIVE; this trigger only spawns the boss.
            self.floors["MT20"].events.pop("6,8", None)
            for p in [(5, 5), (6, 5), (7, 5), (5, 6), (7, 6), (5, 7), (6, 7), (7, 7)]:
                if self.block_at("MT20", p) is not None:
                    self.set_ground("MT20", p)
            self.set_block("MT20", (6, 6), "enemy", "vampire")
            if self.block_at("MT20", (6, 9)) is None:
                self.set_block("MT20", (6, 9), "terrain", "specialDoor")
            self.flags["mt20_vampire"] = 1
            triggered = True
        if fid == "MT10" and pos == (6, 5) and not self.flags.get("mt10_boss_spawned"):
            # 10F boss trigger (web events["6,5"]): captain (6,4 初始静态) move 到 (6,1)，
            # 外围 skeleton/skeletonSoldier move 进 boss 区域包围 hero，开门 (4,4)(8,4)(5,6)(7,6)
            # 放怪、关门 (6,7)(6,3) 封路。终态见 MT10_BOSS_SPAWN。静默 set_block（不 record）：
            # clear_mt10_boss_dyn 模式由调用方 set_block 覆盖 + clear record；逐打模式由 step_path
            # 逐怪 record。幂等 (flag mt10_boss_spawned)。
            # setBlock 0 清空 [[5,4],[6,3],[7,4],[5,5],[7,5]]：其中 (5,4)(7,4)(5,5)(7,5) 由
            # MT10_BOSS_SPAWN set_block 覆盖(含清墙)；(6,3) 非 spawn 位置，需显式清空
            # (move:6:3 / move:6:8 路径经过)。
            self.set_ground("MT10", (6, 3))
            for (sx, sy), eid in MT10_BOSS_SPAWN.items():
                self.set_block("MT10", (sx, sy), "enemy", eid)
            # web (6,5) event: setBlock 0 clears (6,3) mid-event (captain 的 up:3
            # 通道)，但 closeDoor specialDoor (6,3) 在怪物入场后**重新封门**；
            # (6,3) 只能由 MT10 autoEvent["6,3"] 在 8 只竞技场怪全死后 openDoor
            # （条件 flag:10f机关 && (5,4)(6,4)(7,4)(5,5)(7,5)(5,6)(6,6)(7,6)
            # 全空）。只建"清 (6,3)"不建"重封门"会让 go_to 在竞技场未清空时
            # 非法穿 (6,3) 直达 (6,2)/(6,1) captain（2026-08-20 骨架延后变体
            # web 卡死实测，见 _after_action_impl 的 autoEvent 镜像）。
            self.set_block("MT10", (6, 3), "door", "specialDoor")
            self.flags["mt10_boss_spawned"] = True
            triggered = True
        if fid == "MT10" and pos == (6, 2) and self.flags.get("mt10_boss_spawned") and not self.flags.get("mt10_captain_text"):
            # 10F 骷髅队长剧情事件格 (6,2):spawned 清完 + (6,3) 墙开后 hero 途经/踩
            # (6,2) 触发 captain 剧情文本(纯文本,无状态变化)。标 trigger-event 让
            # coalesce 不合并进 (6,1) 击杀,replayer 先点 (6,2) 触发剧情 + Space 推进,
            # 再点 (6,1) 打 captain(否则 replayer 点 (6,1) hero 寻路经 (6,2) 触发剧情
            # 卡 lock=text)。见 skills/mota-live-verify/SKILL.md「1区/10F Boss 实机注意点」。
            self.flags["mt10_captain_text"] = True
            triggered = True
        if fid == "MT10" and pos == (6, 9) and self.flags.get("mt10_boss_spawned") and not self.flags.get("mt10_thief"):
            # 10F 小偷事件格 (6,9): boss spawned 后 hero 踩 (6,9) 触发 thief 事件
            # (thief 走动开路到 upFloor;纯中断无 block 变化,(6,3) 墙已由 (6,5) boss
            # spawn 开,12 补给资源由 auto_sweep 拾)。web automaticRoute 经 (6,9) 中断,
            # hero 停 (6,9);converter 标 trigger-event 拆分 captured path,replayer 先
            # 点 (6,9) 触发再点 (6,11) upFloor(否则 replayer 合并点击 (6,11),web hero
            # 寻路经 (6,9) 中断 -> 位置 mismatch,见 game_route.py:466 注释)。
            # zone2 apply_mt10_supply 已建模此事件(auto-eat 12 + hero 停 6,9)。
            self.flags["mt10_thief"] = True
            triggered = True
        if fid == "MT29" and pos == (6, 2) and not self.flags.get("mt29_thief"):
            # 29F thief (6,2): noPass NPC (trigger="action"). hero 停相邻格 (5,2)
            # 面朝 (6,2) 触发 thief 对话（录像 [705] `right` (5,2)->(5,2) 纯转身
            # face-on）。converter _reach_event_trigger move_adjacent(5,2) + 本方法
            # （pos=(6,2)）+ record 事件 at (6,2)；verifier 点 (6,2)，live hero
            # noPass 停 (5,2)，对话触发。
            #
            # 事件条件分支（events["6,2"] 双层 if）：
            #   whiteWall2@MT23 == 0  -> 开 (6,3) + thief 离开 (6,2)（move down:9）-> MT2 (10,11)
            #   whiteWall2@MT23 > 0 且 额外功能开关 -> 同上（thief 开玩笑说"还在挖"然后开暗道）
            #   whiteWall2@MT23 > 0 且 非 额外功能开关（纯净版-TE）-> thief 说"还在挖"，
            #       **什么都不做**（thief 留 (6,2)，(6,3) 仍 unbreakableWall 330）。
            # 实机本路线确认（hero 在 MT50 后查）：(6,2) thief id=123 仍在，(6,3) 仍是 330。
            # whiteWall2 (tile 321) 是可穿装饰（classify None），不在 .blocks，须数 MT23 grid。
            # 本路线不还原 MT23 墙（live count=43 恒定），所以走"什么都不做"分支。
            ww2_tile = _EID_TO_TILE.get("whiteWall2")
            ww2_count = (sum(1 for row in self.floors["MT23"].grid for c in row if c == ww2_tile)
                         if ww2_tile is not None else 0)
            extra_features = self.flags.get("额外功能开关", False)  # 纯净版-TE: false
            if not (ww2_count > 0 and not extra_features):
                # 暗道完成分支：开 (6,3) + thief 离开 (6,2)（move down:9 走到 (6,11)）。
                # thief 走到 (6,11) 楼梯无 block（thief 已被 set_ground(6,2) 移除）。
                # show MT2 (10,11) 由后续 MT2 (10,11) 事件建模（thief 出现）。
                self.set_ground("MT29", (6, 3))
                self.set_ground("MT29", (6, 2))  # thief leaves
            # else (ww2_count > 0 且 非额外功能): thief 留 (6,2)，(6,3) 仍墙，什么都不做。
            self.flags["mt29_thief"] = 1
            triggered = True
        if fid == "MT40" and pos == (6, 7) and not self.flags.get("402") and "6,7" in self.floors[fid].events:
            # 40F (6,7) 骑士队长 boss 事件 (events["6,7"]): setEnemy special=1 (先攻) 后,
            # 12 守卫 (row4 ghostSkeleton/soldier + row2 swordsman/redKnight) + (6,1) yellowKnight
            # 逐个 move 到 (6,7) battle; 全战后 spawn 奖励 3 yellowKey(2,2)(3,2)(4,2) +
            # 3 redGem(8,2)(9,2)(10,2) + 3 bluePotion(3,4)(4,4)(5,4) + 3 blueGem(7,4)(8,4)(9,4),
            # (6,1) 变 upFloor(87), flag:402=true, hide (6,7)。多数路线 auto_sweep 已在到达
            # (6,7) 前直接清完 12 守卫 + (6,1) yellowKnight (零伤), 事件此时只剩 spawn 奖励;
            # 未清的怪在此以 special=1 先攻补打 (匹配 setEnemy special=1)。
            # 不 pop events["6,7"]: 实机 events["6,7"] 触发后不自动移除, auto plugin 检测
            # has(events[heroLoc]) 直接 return 不跑 BFS (auto_sweep 起 in-events 判定),
            # 故奖励在 *下次* 行动(离开 (6,7))才被 auto 拾取, 匹配录像 (踩 (6,7) atk 不变,
            # move:5:1 时 +12atk +12def +3yk)。flag:402 幂等。
            order = [
                (5, 4), (4, 4), (3, 4), (7, 4), (8, 4), (9, 4),
                (4, 2), (3, 2), (2, 2), (8, 2), (9, 2), (10, 2), (6, 1),
            ]
            for epos in order:
                b = self.block_at(fid, epos)
                if not b or b.kind != "enemy":
                    continue
                dmg = self.enemy_damage(b.eid, special_override=1)
                if dmg == float("inf"):
                    self.fail(f"40F Boss事件无法击杀 {b.eid} at {epos}")
                self.state["hp"] -= int(dmg)
                self.state["dmg"] += int(dmg)
                gain = int(self.enemies[b.eid].get("money", 0))
                if self.state.get("coin"):
                    gain *= 2
                self.state["gold"] += gain
                if self.state["hp"] <= 0:
                    self.fail(f"40F Boss事件死亡 {b.eid} at {epos}")
                self.set_ground(fid, epos)
            for p in [(2, 2), (3, 2), (4, 2)]:
                self.set_block(fid, p, "item", "yellowKey", 21)
            for p in [(8, 2), (9, 2), (10, 2)]:
                self.set_block(fid, p, "item", "redGem", 27)
            for p in [(3, 4), (4, 4), (5, 4)]:
                self.set_block(fid, p, "item", "bluePotion", 32)
            for p in [(7, 4), (8, 4), (9, 4)]:
                self.set_block(fid, p, "item", "blueGem", 28)
            self.set_block(fid, (6, 1), "terrain", "upFloor", 87)
            self.set_ground(fid, (6, 7))
            self.flags["402"] = True
            triggered = True
        if fid == "MT49" and pos == (6, 6) and "6,6" in self.floors[fid].events:
            # 49F (6,6) 假魔王封印事件 (events["6,6"], step-on list): setBlock
            # specialDoor (6,7) + redKing (6,3) + 8 whiteKing 守卫 ((5,2)(5,3)(5,4)
            # (6,4)(7,4)(7,3)(7,2)(6,2)), 清 4 cardinal ((5,3)(6,2)(7,3)(6,4)) 后
            # setBlock whiteKing 覆盖。web 踩 (6,6) 触发;hero 停 (6,6)。后续点击杀
            # 4 cardinal -> 49cardinal 计数 -> 49sealed + 清 50final (见 after_action)。
            # 然后杀 4 corner + 假魔王 (6,3, 49sealed stats)。事件只 spawn,不杀。
            before = self.snapshot()
            self.floors[fid].events.pop("6,6", None)
            self.set_block(fid, (6, 7), "door", "specialDoor", 85)
            self.set_block(fid, (6, 3), "enemy", "redKing", 245)
            for p in [(5, 2), (5, 3), (5, 4), (6, 4), (7, 4), (7, 3), (7, 2), (6, 2)]:
                self.set_block(fid, p, "enemy", "whiteKing", 246)
            self.record("事件", (6, 6), "redKing", before, "49F 假魔王封印事件")
            triggered = True
        if fid == "MT50" and pos == (6, 5) and "6,5" in self.floors[fid].events:
            # 50F (6,5) 小偷=真魔王揭示事件 (events["6,5"], step-on list): 小偷对话
            # -> hide 小偷 -> setEnemy redKing (5000/1580/190) + setBlock redKing (6,5)
            # -> 对话"我就是魔王" -> set flag:与50层小偷对话 (49F 封印前置)。
            # 设 50final + 50thief: enemy_damage 用 50final stats (5000/1580/190)。
            # TE 后续 downFly 到 49F 封印 -> 49sealed 清 50final -> redKing 降为
            # 500/158/19 (50thief 分支)。事件只 spawn redKing,不杀;hero 踩 (6,5)
            # (thief tile 123 passable) 触发后 (6,5) 变 redKing (noPass)。
            before = self.snapshot()
            self.flags["50final"] = True
            self.flags["50thief"] = True
            self.flags["与50层小偷对话"] = True
            self.floors[fid].events.pop("6,5", None)
            self.set_block(fid, (6, 5), "enemy", "redKing", 245)
            self.record("事件", (6, 5), "redKing", before, "50F 小偷现身真魔王")
            triggered = True
        if fid == "MT26" and pos == (6, 6) and "6,6" in self.floors[fid].events:
            # 26F (6,6) 公主 (princess tile 132, passable step-on event): rescue
            # sets flag:营救公主, clears MT26 (6,6), and on MT24 sets (6,1)=
            # whiteWall2, (5,1)/(7,1)=yellowWall, clears (6,2)/(6,3)/(6,4) --
            # the walls blocking the 24F->50F path. The recording's move:5:6
            # from (6,8) routes through (6,6), triggering this. MT24 (6,2)
            # event then changeFloor to MT50 (6,7) when flag:营救公主 is set.
            before = self.snapshot()
            self.flags["营救公主"] = True
            self.set_ground(fid, (6, 6))
            self.set_block("MT24", (6, 1), "wall", "whiteWall2", 1)
            self.set_block("MT24", (5, 1), "wall", "yellowWall")
            self.set_block("MT24", (7, 1), "wall", "yellowWall")
            for p in [(6, 2), (6, 3), (6, 4)]:
                self.set_ground("MT24", p)
            self.floors[fid].events.pop("6,6", None)
            self.record("事件", (6, 6), "princess", before, "26F 营救公主")
            triggered = True
        if fid == "MT24" and pos == (6, 2) and "6,2" in self.floors[fid].events:
            # 24F (6,2) 公主通路事件: if flag:营救公主, changeFloor to MT50 (6,7).
            # The tile is cleared by the MT26 princess rescue, so the hero steps
            # on it (e.g. recording #4892 'up' from (6,3) -> (6,2) -> MT50).
            # This is the TE 24F->50F transition (after rescuing the princess).
            if self.flags.get("营救公主"):
                before = self.snapshot()
                # Do NOT pop "6,2": this is a persistent changeFloor event
                # (if flag:营救公主 -> MT50), triggered each time the hero steps
                # on (6,2). The recording triggers it twice (#4892 first MT50
                # entry for the thief reveal + downFly to 49F, then #5060 after
                # the 49F boss for the final fight).
                self.state["floor"] = "MT50"
                self.state["x"], self.state["y"] = 6, 7
                self.visited.add("MT50")
                self.record("换层", (6, 7), None, before, "24F 公主通路到50F")
                triggered = True
        if fid == "MT16" and pos == (11, 11) and "11,11" in self.floors[fid].events:
            # 16F (11,11) 圣水老人 (fakeWall2 trigger="action"): facing it opens
            # the wall and the oldman gives superPotion (item:superPotion += 1).
            # The recording faces (11,11) from (10,11) (6x 'right', no stat
            # change). Net effect: superPotion += 1, wall cleared. Simplify to
            # give superPotion on the trigger (the recording's net result).
            before = self.snapshot()
            self.state["superPotion"] += 1
            self.set_ground(fid, (11, 11))
            self.floors[fid].events.pop("11,11", None)
            self.record("事件", (11, 11), "superPotion", before, "16F 圣水老人")
            triggered = True
        return triggered

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
        old_marker = (fid, old_pos[0], old_pos[1])
        if old_marker in self.retreat_wizards:
            self.retreat_wizards.discard(old_marker)
            self.retreat_wizards.add((fid, new_pos[0], new_pos[1]))
        self.record("事件", new_pos, "redWizard", before, f"47F 法师后退 {old_pos}->{new_pos}")

    def _check_fire_retreat(self, fid: str, pos: tuple[int, int]) -> None:
        """Web moveOneStep fire-retreat (project.min.js): when the hero steps on
        a fire tile (fgmap 103), clear fire at the hero pos, and for each
        direction, if the adjacent tile has a redWizard and the 2-step tile is
        empty (no block), retreat the wizard to the 2-step tile, set fire at
        the old pos (and 3-step if the 2-step was fire), and clear fire at the
        new pos. MT47 only (only floor with fire). Folded into the hero's
        movement step -- no separate step record; auto_sweep battles the
        corner-trapped wizard at its new pos (e.g. (1,9)->(1,10)->(1,11),
        killed at (1,11); (8,2)->(8,1) killed at (8,1))."""
        f = self.floors.get(fid)
        if f is None or f.fg_at(pos[0], pos[1]) != 103:
            return
        f.fgmap[pos[1]][pos[0]] = 0  # clear fire at hero pos
        DIRS = ((0, -1), (-1, 0), (0, 1), (1, 0))  # up, left, down, right (core.utils.scan)
        for dx, dy in DIRS:
            adj = (pos[0] + dx, pos[1] + dy)
            two = (pos[0] + 2 * dx, pos[1] + 2 * dy)
            if not (0 <= two[0] < f.width and 0 <= two[1] < f.height):
                continue
            block = self.block_at(fid, adj)
            if not block or block.eid != "redWizard":
                continue
            if self.block_at(fid, two) is not None:
                continue  # 2-step not empty -> wizard stays
            two_was_fire = f.fg_at(two[0], two[1]) == 103
            # Retreat wizard adj -> two.
            self.set_ground(fid, adj)
            self.set_block(fid, two, "enemy", "redWizard", block.tile)
            # A fire-retreated wizard keeps live flee-on-approach semantics:
            # mark it retreating (migrate the marker if already marked) so it
            # is not path-killed / auto-farmed unless corner-trapped.
            self.retreat_wizards.discard((fid, adj[0], adj[1]))
            self.retreat_wizards.add((fid, two[0], two[1]))
            # adj 铺火条件与 web 源码逐字一致（project.min.js moveOneStep）：
            # 「if (core.getFgNumber(nnx,nny)===103) { setBgFgBlock fg103 三步格;
            #    setBgFgBlock fg103 让出格 }」——只在 two 原本是火（连锁撤退）时，
            # 让出格与三步格才同时铺火。2026-08-30 曾误改为无条件铺 adj 火，
            # 与 web 源码相悖，已回退。
            if two_was_fire:
                three = (pos[0] + 3 * dx, pos[1] + 3 * dy)
                # Web isValidPosition bounds the whole scan to the inner
                # 11x11 playfield (1..11), so the propagated fire never lands
                # on the border ring (e.g. hero (1,9): 3-step (1,12) gets NO
                # fire in live).
                if 1 <= three[0] <= f.width - 2 and 1 <= three[1] <= f.height - 2:
                    # Web sets the propagated fire unless the 3-step block
                    # carries event data (project.min.js: nnnb.event.data).
                    # Doors/terrain/items carry none -- verified live: the
                    # (8,4) yellowDoor tile DOES receive fire on MT47.
                    three_block = self.block_at(fid, three)
                    if three_block is None or three_block.kind != "npc":
                        f.fgmap[three[1]][three[0]] = 103
                f.fgmap[adj[1]][adj[0]] = 103
            f.fgmap[two[1]][two[0]] = 0

    def transition(self, to_fid: str, note: str = "", *, landing: tuple[int, int] | None = None) -> None:
        before = self.snapshot()
        from_fid = self.state["floor"]
        # Live changeFloor 语义对齐 (2026-09-12 agentV b2r1 web 复验打回): 相邻层的
        # transition 在实机只能由「踩楼梯格」触发 —— hero 必须站在 from 层对应方向
        # 的楼梯格上, 否则是不可点击的传送 (verifier 对换层步零动作, 真实转层完全
        # 依赖前一步楼梯点击)。事件转层 (landing 显式给出, 如 24F->MT50) 与非相邻
        # 层跳转不受此约束。
        if (
            landing is None
            and self.strict_live_model
            and abs(floor_no(to_fid) - floor_no(from_fid)) == 1
        ):
            stair_eid = "upFloor" if floor_no(to_fid) > floor_no(from_fid) else "downFloor"
            stairs = [
                pos
                for pos, b in self.floors[from_fid].blocks.items()
                if b is not None and b.kind == "terrain" and b.eid == stair_eid
            ]
            if (self.state["x"], self.state["y"]) not in stairs:
                self.fail(
                    f"transition {from_fid}->{to_fid} without hero on {stair_eid} stair "
                    f"(hero at x{self.state['x']}y{self.state['y']}; live changeFloor "
                    f"requires the stair click)"
                )
        point_key = "downFloor" if floor_no(to_fid) > floor_no(from_fid) else "upFloor"
        resolved_landing = list(landing) if landing is not None else self.fly_points[to_fid][point_key]
        if resolved_landing is None and to_fid == "MT44":
            resolved_landing = [1, 1]
        if not resolved_landing:
            self.fail(f"no landing {from_fid}->{to_fid}")
        self.state["floor"] = to_fid
        self.state["x"], self.state["y"] = resolved_landing
        # The hero has entered this floor (stair/event/fly); add it to visited
        # so the ordinary floor teleporter can fly back to it. The recording
        # flies back to MT49 (e.g. #5045 fly:MT49 MT8->MT49 after the 49F boss),
        # so MT49/MT50 must be in visited after a real entry.
        self.visited.add(to_fid)
        self.record("换层", tuple(resolved_landing), None, before, note or f"{from_fid}->{to_fid}")
        self.apply_check_damage(to_fid, tuple(resolved_landing), "换层落点")

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
        # upFly/downFly relocate the hero but do not set the engine's
        # __visited__ flag used by the ordinary floor teleporter.
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
        """Break ALL 4 adjacent canBreak walls (web useItemEffect loops 4 dirs).

        The web pickaxe (破墙镐) useItemEffect iterates core.utils.scan
        (up/left/down/right) and openDoor's every adjacent wall with
        block.event.canBreak. Only yellowWall/fakeWall have canBreak=true, so
        the pickaxe breaks ALL of them around the hero (e.g. MT48 x11y10 breaks
        both x10y10 and x12y10 yellowWall). The (x,y) target is kept only for
        the record (the wall the hero will move through); it is NOT the sole
        wall broken."""
        if self.state["pickaxe"] <= 0:
            self.fail("no pickaxe")
        if self.state["floor"] != fid:
            self.fail(f"cannot use pickaxe on {fid} while at {self.state['floor']}")
        hx, hy = self.state["x"], self.state["y"]
        before = self.snapshot()
        self.state["pickaxe"] -= 1
        broken: list[str] = []
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            pos = (hx + dx, hy + dy)
            b = self.block_at(fid, pos)
            if b and b.eid in BREAKABLE_WALL_IDS:
                self.set_ground(fid, pos)
                broken.append(f"x{pos[0]}y{pos[1]} {b.eid}")
        if not broken:
            self.fail(f"pickaxe broke no canBreak wall at {fid} x{hx}y{hy}")
        self.record("使用镐", (x, y), "pickaxe", before, f"{note}; broke={broken}")

    def use_pickaxe_adjacent(self, note: str = "") -> tuple[int, int]:
        """Use pickaxe when the recording has no target tile.

        Recordings emit ``item:pickaxe`` without a target tile. The web pickaxe
        breaks ALL adjacent canBreak walls (not facing-based), so pick any
        adjacent breakable wall as the record target; all are broken."""
        if self.state["pickaxe"] <= 0:
            self.fail("no pickaxe")
        fid = self.state["floor"]
        hx, hy = self.state["x"], self.state["y"]
        target: tuple[int, int] | None = None
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            b = self.block_at(fid, (hx + dx, hy + dy))
            if b and b.eid in BREAKABLE_WALL_IDS:
                target = (hx + dx, hy + dy)
                break
        if target is None:
            self.fail(f"no adjacent breakable wall for pickaxe at {fid} x{hx}y{hy}")
        self.use_pickaxe(fid, *target, note)
        return target

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
        # Princess is noPass and stays after the rescue (the commonEvent fires
        # on facing her each time; the false-branch only modifies MT24). Do NOT
        # clear (6,6) -- the hero never steps onto it.
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

    # 商人 common event (core.events.commonEvent['商人']) is switch(arg1) where
    # arg1 = floor number (set by the trader trigger). Each entry is
    # (cost_gold, {state_key: gain}, eid). Verified against the live game.
    TRADER_TABLE = {
        2:  (-1000, {},                        "oldmanGold1000"),
        6:  (50,   {"bk": 1},                 "blueKey1"),
        7:  (50,   {"yk": 5},                 "yellowKey5"),
        12: (800,  {"rk": 1},                 "redKey1"),
        15: (200,  {"bk": 1},                 "blueKey1_15"),
        28: (-100, {"yk": -1},                "specialTrader"),
        31: (1000, {"yk": 4, "bk": 1},        "keyBundle31"),
        38: (200,  {"yk": 3},                 "yellowKey3"),
        39: (2000, {"bk": 3},                 "blueKey3"),
        45: (1000, {"hp": 2000},              "hp2000"),
        47: (4000, {"earthquake": 1},         "earthquake"),
    }

    def talk_trader(self, fid: str, x: int, y: int, note: str = "") -> None:
        # Move to any adjacent reachable tile first.
        self.move_adjacent(fid, x, y, note)
        before = self.snapshot()
        n = floor_no(fid)
        entry = self.TRADER_TABLE.get(n)
        if entry is None:
            self.fail(f"unmodeled trader {fid} x{x}y{y}")
            return
        cost, gain, eid = entry
        flag = self.trader_flag(fid, x, y)
        # specialTrader (e.g. MT28 sells yellowKeys for gold, one per dialog)
        # is repeatable -- each dialog sells one key, so it must not be gated
        # by the one-shot flag the way one-shot traders are.
        repeatable = eid == "specialTrader"
        if not repeatable and self.flags.get(flag):
            self.fail(f"{fid} trader already used")
        # 47F earthquake trader additionally guards on a dedicated counter.
        if n == 47 and self.state.get("earthquakeBought", 0) >= 1:
            self.fail("47F earthquake trader already used")
        if self.state["gold"] < cost:
            self.fail(f"not enough gold for {fid} trader: need={cost} have={self.state['gold']}")
        # Reverse traders (gain value < 0) consume items; verify the hero has
        # enough of the sold item before applying.
        for key, val in gain.items():
            if val < 0 and self.state.get(key, 0) < -val:
                self.fail(f"not enough {key} for {fid} trader: need={-val} have={self.state.get(key, 0)}")
        self.state["gold"] -= cost
        for key, val in gain.items():
            if key == "earthquake":
                self.state["earthquake"] += val
                self.state["earthquakeBought"] = self.state.get("earthquakeBought", 0) + val
            else:
                self.state[key] += val
        if not repeatable:
            self.flags[flag] = 1
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
                # strict path(只走可踩格,门/怪不穿),匹配下方 strict go_to。
                # 否则默认 loose path 含门/怪时,go_to strict fail(no path);
                # 用 strict 让 candidates 空时进 loose fallback(go_to_decomposed 开/打)。
                path = self.path_to(fid, pos, strict_click=True)
            except RouteError:
                raise
            if path:
                candidates.append((len(path), pos))
        if not candidates:
            # A lower-stat branch may have a door or non-zero-damage enemy on
            # every strict path to the NPC.  Pick the shortest loose adjacent
            # route, then let the shared decomposer emit each blocker as its
            # own real click.  This preserves talk/trader click semantics.
            loose_candidates = []
            for pos in [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]:
                path = self.path_to(fid, pos, strict_click=False)
                if path:
                    loose_candidates.append((len(path), pos))
            if not loose_candidates:
                self.fail(f"no adjacent path to {fid} x{x}y{y}: {note}")
            _, pos = min(loose_candidates)
            go_to_decomposed(self, fid, pos[0], pos[1], note)
            return
        _, pos = min(candidates)
        self.go_to(fid, pos[0], pos[1], note)

    def change_by_stair(self, to_fid: str, stair_x: int, stair_y: int, note: str = "") -> None:
        self.go_to(self.state["floor"], stair_x, stair_y, note)
        self.transition(to_fid, note)


def safe_try(g: Game, fn, *args, **kwargs) -> bool:
    # Optional route probes must be transactional.  Several route helpers make
    # more than one legal click before discovering that their final target is
    # unsafe or unreachable.  Keeping that partial map/hero state after the
    # RouteError creates a walk which no longer matches a fresh live replay
    # (most visibly for the retreating MT47 redWizards).
    before = g.clone()
    try:
        fn(*args, **kwargs)
        return True
    except RouteError:
        g.__dict__.clear()
        g.__dict__.update(before.__dict__)
        return False


def go_to_decomposed(g: Game, fid: str, x: int, y: int, note: str = "", limit: int = 32) -> None:
    """Reach a target through action blockers using reproducible real clicks.

    Strict target-click routing correctly refuses to cross a closed door or a
    non-zero-damage enemy.  A high-stat route may have relied on auto clearing
    those enemies, while a lower-stat branch must click them explicitly.  Use
    the loose path only to identify its *first* blocker, click that blocker via
    normal strict ``Game.go_to``, then re-plan.  No hero coordinates or blocks
    are edited here.
    """
    initial_target = g.block_at(fid, (x, y))
    for _ in range(limit):
        if initial_target is None and g.state["floor"] == fid and (g.state["x"], g.state["y"]) == (x, y):
            return
        if initial_target is not None and g.block_at(fid, (x, y)) is None:
            return
        old_errors = len(g.errors)
        try:
            g.go_to(fid, x, y, note)
            return
        except RouteError:
            del g.errors[old_errors:]
        path = g.path_to(fid, (x, y), strict_click=False)
        if not path:
            # No loose path. The target may be reachable only through a door/
            # wall that an event opens mid-move (the recording's automaticRoute
            # fires the trigger when the hero steps on it, e.g. MT15 (9,1) thief
            # opens (8,1) unbreakableWall). The static BFS plans before the hero
            # steps, so it sees (8,1) as a wall and finds no path. Step onto
            # reachable passable event-trigger tiles (clone-test: only commit
            # triggers that actually open a path to the target) and re-plan.
            opened = False
            for tpos in g._reachable_event_triggers(fid, (x, y)):
                cand = g.clone()
                try:
                    cand.go_to(fid, tpos[0], tpos[1], f"test trigger {tpos}")
                except RouteError:
                    continue
                if cand.path_to(fid, (x, y), strict_click=False):
                    g.go_to(fid, tpos[0], tpos[1], f"{note}: 触发事件开路 {tpos}")
                    opened = True
                    break
            if opened:
                continue
            g.fail(f"cannot decompose route to {fid} x{x}y{y}: {note}")
        blocker = next((pos for pos in path[1:] if g.block_at(fid, pos) is not None), None)
        if blocker is None:
            g.fail(f"decomposed route made no progress to {fid} x{x}y{y}: {note}")
        g.go_to(fid, blocker[0], blocker[1], f"{note}: 前置真实点击")
    g.fail(f"decomposed route exceeded {limit} clicks to {fid} x{x}y{y}: {note}")


def optional_talk_trader(g: Game, fid: str, x: int, y: int, note: str = "") -> bool:
    cand = g.clone()
    try:
        cand.talk_trader(fid, x, y, note)
    except RouteError:
        return False
    g.__dict__.update(cand.__dict__)
    return True


def buy_mt45_hp_merchant(g: Game, note: str, *, required: bool = True) -> bool:
    """Reach and buy the MT45 1000G -> 2000HP merchant via real clicks.

    Some strategy branches open the center/right corridor early while others
    first become rich enough near the endgame.  Never assume that earlier side
    effect: decompose the route through its live doors/enemies at purchase time.
    Work on a clone so an optional failed purchase is transactional too.
    """
    flag = g.trader_flag("MT45", 9, 3)
    if g.flags.get(flag):
        return True
    if g.state["gold"] < 1000:
        if required:
            g.fail(f"not enough gold for 45F HP merchant: have={g.state['gold']}")
        return False
    cand = g.clone()
    try:
        if cand.state["floor"] != "MT45":
            cand.fly("MT45")
        go_to_decomposed(cand, "MT45", 9, 4, f"{note}: 商人通道")
        cand.talk_trader("MT45", 9, 3, note)
    except RouteError:
        if required:
            raise
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
                    (cand.state["yd"] - before["yd"]) * 100
                    + (cand.state["bd"] - before["bd"]) * 500
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
    # NOTE: an earlier revision added an early MT32 (11,7) blue-key detour here
    # ("47F 蓝门前补32F蓝钥匙"). It diverged from the web-verified 22264 walk,
    # which collects that blue key LATE (step ~506, after the lucky coin makes
    # MT32 monsters zero-damage) and gets early blue keys from MT43/MT41 instead.
    # The early detour also flew to MT40 landing at (10,11) (not save37 x9y4),
    # breaking the path to the x6y1 stair, and took 24 damage. Removed to match
    # the verified strategy; MT41 is reached by stair climb below.
    # Go to 42F first so the 41F half-HP trap is applied before taking 40F potions.
    collect_net_yellow_keys_until(g, 2, "41F 上楼前补钥匙")
    # MT41 is unvisited at save37 (hero reached MT40 from below); fly() correctly
    # refuses unvisited floors (matches real flyTo + flyto_visited_hack_disabled).
    # Climb MT40->MT41 via the x6y1 stair, exactly as the verified 22264 walk does
    # (prepend steps 0-1: MT40 x6y1 upFloor -> MT41 x6y2). MT40 is visited.
    if g.state["floor"] != "MT41":
        if g.state["floor"] != "MT40":
            g.fly("MT40")
        g.change_by_stair("MT41", 6, 1, "40F x6y1 上楼到41F")
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
            # Battle events may open a resource pocket without restarting the
            # live auto plugin. Trigger the normal generic item search right
            # after such a committed kill, so the next recorded action is a
            # reproducible item click rather than an accidental pickup during
            # some unrelated later battle.
            if f"{x},{y}" in g.floors[fid].after_battle:
                cleanup_reachable_items(
                    g, {"yellowKey", "blueKey"}, min_floor=1, max_steps=24
                )
        if g.state["gold"] >= 4000:
            break
    # Event-bearing zero-damage guards require explicit clicks and their
    # afterBattle door does not restart auto. Collect newly reachable keys via
    # the normal item-search pipeline before deciding whether keys must be sold
    # for the earthquake scroll; do not rely on a modeled auto side effect.
    cleanup_reachable_items(
        g, {"yellowKey", "blueKey"}, min_floor=1, max_steps=24
    )
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


def sell_yellow_keys_for_gold(g: Game, target_gold: int, preserve_yk: int = 0) -> None:
    if g.state["gold"] >= target_gold:
        return
    if g.state["floor"] != "MT28":
        g.fly("MT28")
    g.move_adjacent("MT28", 8, 4, "28F yellow-key seller")
    while g.state["gold"] < target_gold and g.state["yk"] > preserve_yk:
        before = g.snapshot()
        g.state["yk"] -= 1
        g.state["gold"] += 100
        g.record("商人", (8, 4), "sellYellowKey", before, "28F sell 1 yellow key for 100G")


def farm_gold_after_coin(g: Game, target_gold: int, preserve_yk: int = 0, min_floor: int = 1) -> None:
    sync_mt47_retreat_wizards(g)
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
    # A floor reached only by upFly/downFly is not unlocked for ordinary fly,
    # but while the hero is physically standing there its local actions are
    # still searchable. Keep travel permission and current-floor reachability
    # as distinct concepts.
    reachable = set(g.visited)
    reachable.add(g.state["floor"])
    return sorted(
        (fid for fid in reachable if fid in g.floors and floor_no(fid) >= min_floor),
        # If the current floor came only from a floor tool, leaving it is
        # irreversible until a real stair visit. Consume equal-value local
        # candidates before teleporting away.
        key=lambda fid: (
            0 if fid == g.state["floor"] and fid not in g.visited else 1,
            floor_no(fid),
        ),
    )


def _potion_floor_ids(g: Game, min_floor: int = 1) -> list[str]:
    reachable = set(g.visited)
    reachable.add(g.state["floor"])
    return sorted(
        (fid for fid in reachable if fid in g.floors and floor_no(fid) >= min_floor),
        key=lambda fid: (
            0 if fid == g.state["floor"] and fid not in g.visited else 1,
            -g.floors[fid].ratio,
            -floor_no(fid),
        ),
    )


def _hp_door_cost(before: dict[str, Any], after: dict[str, Any]) -> int:
    return (
        (after["yd"] - before["yd"]) * 100
        + (after["bd"] - before["bd"]) * 500
        + (after["rd"] - before["rd"]) * 800
    )


def sync_mt47_retreat_wizards(g: Game) -> None:
    """Restore retreat markers from the current dynamic MT47 map state."""
    for x, ys in ((8, (1, 2, 3)), (1, (9, 10, 11))):
        for y in ys:
            block = g.block_at("MT47", (x, y))
            if block and block.kind == "enemy" and block.eid == "redWizard":
                g.retreat_wizards.add(("MT47", x, y))


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
    sync_mt47_retreat_wizards(g)
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


def eat_minimal_potions_until(
    g: Game,
    target_hp: int,
    note: str,
    min_floor: int = 1,
    preserve_yk: int = 0,
    preserve_bk: int = 0,
    preserve_rk: int = 0,
) -> None:
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
                if (cand.state["yk"] < preserve_yk or cand.state["bk"] < preserve_bk
                        or cand.state["rk"] < preserve_rk):
                    continue
                door_cost = (
                    (cand.state["yd"] - before["yd"]) * 100
                    + (cand.state["bd"] - before["bd"]) * 500
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


def _simulate_potion_floor_batch(
    g: Game,
    fid: str,
    segment: str,
    *,
    allow_door_investment: bool = False,
) -> tuple[float, Game] | None:
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
                if allow_door_investment:
                    go_to_decomposed(probe, fid, x, y, f"potion {fid} x{x}y{y}")
                else:
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


def _potion_floor_sweep(
    g: Game,
    min_floor: int,
    segment: str,
    *,
    allow_door_investment: bool = False,
) -> bool:
    g.set_segment(segment)
    changed = False
    for fid in _potion_floor_ids(g, min_floor):
        result = _simulate_potion_floor_batch(
            g,
            fid,
            segment,
            allow_door_investment=allow_door_investment,
        )
        if result is None:
            continue
        score, cand = result
        g.__dict__.update(cand.__dict__)
        changed = True
        trace_point(f"potion floor batch {fid} score={score:.1f}", g)
    return changed


def eat_all_reachable_potions(
    g: Game,
    min_floor: int = 1,
    *,
    allow_door_investment: bool = False,
    preserve_rk: int = 1,
) -> None:
    """Repeatedly collect keys then potions until stable. Keys unlock door-guarded
    potions, so the two must be interleaved (guide: 需要钥匙开门的宝石/药水也要拿)."""
    for _ in range(60):
        # Eat every currently-reachable potion (may consume keys).
        while _potion_floor_sweep(
            g,
            min_floor,
            "final potion cleanup",
            allow_door_investment=allow_door_investment,
        ):
            pass
        # Collect any newly-relevant keys so the next potion pass can spend them.
        before_keys = (g.state["yk"], g.state["bk"], g.state["rk"])
        cleanup_reachable_items(
            g,
            {"yellowKey", "blueKey", "redKey"},
            min_floor=min_floor,
            preserve_rk=preserve_rk,
            allow_door_investment=allow_door_investment,
        )
        if (g.state["yk"], g.state["bk"], g.state["rk"]) == before_keys:
            # No new keys gained -> another potion pass that fails means done.
            if not _potion_floor_sweep(
                g,
                min_floor,
                "final potion cleanup",
                allow_door_investment=allow_door_investment,
            ):
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
    allow_door_investment: bool = False,
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
                    if allow_door_investment:
                        go_to_decomposed(cand, fid, x, y, f"final resource {fid} x{x}y{y}")
                    else:
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
                if allow_door_investment and score <= 0:
                    continue
                if best is None or score > best[0]:
                    best = (score, cand, f"{fid} x{x}y{y}")
        if best is None:
            return
        _score, chosen, _desc = best
        g.__dict__.update(chosen.__dict__)
        picked += 1


def collect_positive_hp_resource_groups(
    g: Game,
    min_floor: int = 1,
    *,
    preserve_yk: int = 0,
    preserve_rk: int = 0,
    require_stat_and_nonnegative_key_value: bool = False,
) -> None:
    """Collect door-backed item groups whose fully replayed delta gains HP.

    The clicked tile is only a group entry: strict movement and auto may also
    consume a door and collect adjacent keys, gems, or potions.  Rank the real
    group delta and repeat from the changed map.  This avoids both coordinate
    special-cases and the old failure mode where ``go_to`` rejected a profitable
    group merely because a closed door was its first blocker.
    """
    g.set_segment("positive-HP resource-group cleanup")
    while True:
        before = g.snapshot()
        best: tuple[tuple[int, int, int, int], Game] | None = None
        for fid in _visited_floor_ids(g, min_floor):
            for (x, y), block in list(g.floors[fid].blocks.items()):
                if block.kind != "item":
                    continue
                if (fid, x, y) in g.blocked_items:
                    continue
                cand = g.clone()
                try:
                    if cand.state["floor"] != fid:
                        cand.fly(fid)
                    go_to_decomposed(cand, fid, x, y, f"positive-HP resource group {block.eid}")
                except RouteError:
                    continue
                hp_gain = cand.state["hp"] - before["hp"]
                if (
                    hp_gain <= 0
                    or cand.state["hp"] <= 0
                    or cand.state["yk"] < preserve_yk
                    or cand.state["rk"] < preserve_rk
                ):
                    continue
                key_gain = (
                    (cand.state["yk"] - before["yk"]) * 4
                    + (cand.state["bk"] - before["bk"]) * 16
                    + (cand.state["rk"] - before["rk"]) * 32
                )
                stat_gain = (
                    cand.state["atk"] - before["atk"]
                    + cand.state["def"] - before["def"]
                )
                if require_stat_and_nonnegative_key_value and (stat_gain <= 0 or key_gain < 0):
                    continue
                rank = (
                    hp_gain,
                    key_gain,
                    cand.state["def"] - before["def"],
                    cand.state["atk"] - before["atk"],
                )
                if best is None or rank > best[0]:
                    best = (rank, cand)
        if best is None:
            return
        g.__dict__.update(best[1].__dict__)


def collect_stat_resource_groups(
    g: Game,
    max_groups: int,
    min_floor: int = 1,
    *,
    preserve_yk: int = 1,
    preserve_rk: int = 1,
    max_key_value_loss: int = 4,
) -> None:
    """Take a bounded number of early stat groups through strict Game paths.

    This is a macro-search variable, not a coordinate list.  Each candidate is
    a fully replayed item-group entry, may include auto-collected adjacent gems,
    and is rejected if it loses HP or exceeds the configured key opportunity
    cost (yellow=4, blue=16, red=32 units).
    """
    g.set_segment("early stat resource-group search")
    for _ in range(max_groups):
        before = g.snapshot()
        best: tuple[tuple[int, int, int, int], Game] | None = None
        for fid in _visited_floor_ids(g, min_floor):
            for (x, y), block in list(g.floors[fid].blocks.items()):
                if block.kind != "item":
                    continue
                if (fid, x, y) in g.blocked_items:
                    continue
                cand = g.clone()
                try:
                    if cand.state["floor"] != fid:
                        cand.fly(fid)
                    go_to_decomposed(cand, fid, x, y, f"early stat resource group {block.eid}")
                except RouteError:
                    continue
                if (
                    cand.state["hp"] < before["hp"]
                    or cand.state["yk"] < preserve_yk
                    or cand.state["rk"] < preserve_rk
                ):
                    continue
                atk_gain = cand.state["atk"] - before["atk"]
                def_gain = cand.state["def"] - before["def"]
                if atk_gain + def_gain <= 0:
                    continue
                key_delta = (
                    (cand.state["yk"] - before["yk"]) * 4
                    + (cand.state["bk"] - before["bk"]) * 16
                    + (cand.state["rk"] - before["rk"]) * 32
                )
                key_loss = max(0, -key_delta)
                if key_loss > max_key_value_loss:
                    continue
                rank = (atk_gain + def_gain, def_gain, atk_gain, -key_loss)
                if best is None or rank > best[0]:
                    best = (rank, cand)
        if best is None:
            return
        g.__dict__.update(best[1].__dict__)


def terminal_hp_resource_closure(
    g: Game,
    max_rounds: int = 12,
    *,
    preserve_blocked_items: bool = False,
    shops_first: bool = False,
) -> None:
    """Close the terminal potion/key/gold loop to a strict fixed point.

    This runs only after all mandatory fights and routing keys are finished.
    Each round first spends keys on groups with a *real positive HP delta*, then
    clears free gold and tries the 46F HP shop using monster pockets plus genuine
    28F yellow-key sales.  A shop purchase or a key-backed group can expose a
    new profitable group, so a single cleanup pass is not sufficient.
    """
    g.set_segment("terminal HP resource fixed point")
    # ``blocked_items`` is a route-planning policy used to defer potions/keys
    # across half-HP traps or reserve a key for mandatory routing.  Once every
    # mandatory fight and door is complete, none of those reservations remain
    # valid.  Releasing the whole policy set is deliberately generic: otherwise
    # live auto can collect a deferred neighbour (for example a key beside a
    # potion pocket) while offline Game silently suppresses it.
    if not preserve_blocked_items:
        g.blocked_items.clear()

    def signature() -> tuple[Any, ...]:
        resources = tuple(
            sorted(
                (fid, x, y, block.kind, block.eid)
                for fid in g.visited
                if fid in g.floors
                for (x, y), block in g.floors[fid].blocks.items()
                if block.kind in {"item", "enemy", "door"}
            )
        )
        return (
            g.state["hp"], g.state["atk"], g.state["def"],
            g.state["yk"], g.state["bk"], g.state["rk"],
            g.state["gold"], g.state["times1"], resources,
        )

    for _ in range(max_rounds):
        before = signature()
        if shops_first:
            buy_hp_with_remaining_gold(
                g,
                max_count=8,
                allow_key_investment=True,
                allow_key_sale=True,
            )
        collect_positive_hp_resource_groups(
            g, min_floor=1, preserve_yk=0, preserve_rk=0,
        )
        eat_all_reachable_potions(
            g,
            min_floor=1,
            allow_door_investment=True,
            preserve_rk=0,
        )
        clear_zero_damage_monsters(g, preserve_yk=0, min_floor=1)
        if not shops_first:
            buy_hp_with_remaining_gold(
                g,
                max_count=8,
                allow_key_investment=True,
                allow_key_sale=True,
            )
        if signature() == before:
            return
    g.fail(f"terminal HP resource closure did not converge in {max_rounds} rounds")


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
        below = g.block_at("MT47", (8, 4))
        if below is not None:
            # Closed x8y4 door blocks the retreat, so one target click routes
            # to the empty x8y2 beside the wizard and live auto kills it in the
            # same action. Clicking the retreat-enemy tile itself is rejected
            # by the live route finder even while trapped.
            g.retreat_wizards.discard(("MT47", 8, 3))
            g.go_to("MT47", 8, 2, "47F x8y3法师包围-走到x8y2（安全时auto击杀）")
        else:
            # If an earlier key-investment route opened x8y4, approach from
            # below and push the wizard twice toward the top wall.
            g.go_to("MT47", 8, 4, "47F x8法师退避-走到x8y4")
            g._move_retreat_wizard("MT47", (8, 3), (8, 2))
            g.go_to("MT47", 8, 3, "47F x8法师退避-走到x8y3")
            g._move_retreat_wizard("MT47", (8, 2), (8, 1))
            g.retreat_wizards.discard(("MT47", 8, 1))
            g.go_to("MT47", 8, 2, "47F x8法师退避-走到x8y2触发auto击杀")

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
        g.retreat_wizards.discard(("MT47", 1, 11))


def buy_hp_with_remaining_gold(
    g: Game,
    max_count: int = 3,
    *,
    allow_key_investment: bool = False,
    allow_key_sale: bool = False,
) -> None:
    for _ in range(max_count):
        cost = shop_cost(g.state["times1"])
        if g.state["gold"] < cost:
            farmed = safe_try(g, farm_gold_after_coin, g, cost, 0, 1)
            if not farmed and allow_key_investment:
                farmed = safe_try(
                    g,
                    farm_gold_with_key_investment,
                    g,
                    cost,
                    0,
                    0,
                )
            if not farmed and allow_key_sale:
                farmed = safe_try(g, fund_shop_with_yellow_key_sale, g, cost, 0)
            if not farmed:
                break
        if g.state["gold"] < cost:
            break
        if g.state["floor"] != "MT46":
            g.fly("MT46")
        g.go_to("MT46", 6, 2, "46F HP shop")
        g.buy_shop("hp", 1, shop_pos=(6, 1))
        trace_point("buy_hp_with_remaining_gold bought hp", g)


def fund_shop_with_yellow_key_sale(
    g: Game,
    target_gold: int,
    preserve_yk: int = 0,
    max_steps: int = 40,
) -> None:
    """Reach a final shop cost using monster/key groups plus 28F key sales.

    A pure gold farmer may roll back when monsters alone cannot hit the target,
    while selling the current keys first can leave the route a few coins short.
    Search on ``gold + sellable_yk * 100`` and commit only strict Game actions
    that increase that effective funding; perform the actual merchant sales only
    after the combined target is attainable.
    """
    g.set_segment("final effective-funding cleanup")

    def effective(game: Game) -> int:
        return game.state["gold"] + max(0, game.state["yk"] - preserve_yk) * 100

    for _ in range(max_steps):
        if g.state["gold"] >= target_gold or effective(g) >= target_gold:
            break
        before_effective = effective(g)
        best: tuple[float, int, int, Game] | None = None
        for fid in _visited_floor_ids(g, 1):
            for (x, y), block in list(g.floors[fid].blocks.items()):
                if block.kind == "enemy":
                    if (fid, x, y) in g.retreat_wizards or (fid, x, y) in g.no_auto_farm:
                        continue
                elif block.kind == "item" and block.eid in {"yellowKey", "blueKey", "redKey"}:
                    pass
                else:
                    continue
                cand = g.clone()
                try:
                    before = cand.snapshot()
                    if cand.state["floor"] != fid:
                        cand.fly(fid)
                    go_to_decomposed(cand, fid, x, y, f"final effective funding {block.eid}")
                except RouteError:
                    continue
                if cand.state["hp"] <= 0 or cand.state["yk"] < preserve_yk:
                    continue
                funding_gain = effective(cand) - before_effective
                if funding_gain <= 0:
                    continue
                hp_loss = max(0, before["hp"] - cand.state["hp"])
                score = funding_gain - hp_loss
                row = (float(score), funding_gain, -hp_loss, cand)
                if best is None or row[:3] > best[:3]:
                    best = row
        if best is None:
            break
        g.__dict__.update(best[3].__dict__)

    if effective(g) < target_gold:
        g.fail(
            f"cannot fund shop with yellow-key sale to {target_gold}, "
            f"gold={g.state['gold']} yk={g.state['yk']}"
        )
    sell_yellow_keys_for_gold(g, target_gold, preserve_yk=preserve_yk)
    if g.state["gold"] < target_gold:
        g.fail(
            f"yellow-key sale funding short of {target_gold}, have={g.state['gold']}"
        )


def kill_fixed_zero_damage_targets(
    g: Game,
    targets: list[tuple[str, int, int]],
    note: str,
    *,
    required: bool = True,
) -> None:
    g.set_segment(note)
    for fid, x, y in targets:
        block = g.block_at(fid, (x, y))
        if not block or block.kind != "enemy":
            continue
        cand = g.clone()
        try:
            if cand.state["floor"] != fid:
                cand.fly(fid)
            before = cand.snapshot()
            cand.go_to(fid, x, y, f"{note} {fid} x{x}y{y}")
        except RouteError:
            if required:
                raise
            continue
        after = cand.snapshot()
        if after["hp"] != before["hp"] or after["dmg"] != before["dmg"]:
            if required:
                g.fail(f"fixed zero-damage target caused damage at {fid} x{x}y{y}")
            continue
        if (after["yd"], after["bd"], after["rd"]) != (before["yd"], before["bd"], before["rd"]):
            if required:
                g.fail(f"fixed zero-damage target opened a door at {fid} x{x}y{y}")
            continue
        g.__dict__.update(cand.__dict__)


def final_key_bundle_and_mt20_potions(g: Game, *, required: bool = True) -> None:
    """HP-leaderboard tail cleanup after all stat/HP shops are done.

    The remaining free monsters after the current 21764 route are worth more
    than 1000G with the lucky coin. Spend exactly that on the 31F merchant
    (1000G -> 4YK + 1BK), then open the MT20 right-side blue-door pocket for
    its red+blue potion (+500HP at 11-20F ratio 2).
    """
    g.set_segment("final 31F key bundle + MT20 potions")
    if g.flags.get("skipFinalKeyBundle"):
        # This is a strategy decision, not an availability failure.  Retain the
        # merchant and MT20 pocket in the map so the later resource search can
        # compare saving 1000G against spending the eventual blue key here.
        g.blocked_items.update({
            ("MT20", 11, 5),
            ("MT20", 10, 4),
            ("MT20", 11, 4),
        })
        g.flags.setdefault("routeDecisions", []).append(
            "skip optional 31F 1000G key bundle and defer MT20 potion pocket"
        )
        return
    before_gold = g.state["gold"]
    kill_fixed_zero_damage_targets(g, [
        ("MT47", 6, 5),
        ("MT47", 9, 5),
        ("MT47", 9, 3),
        ("MT48", 7, 3),
        ("MT48", 9, 3),
        ("MT48", 7, 5),
        ("MT48", 9, 5),
    ], "final fixed zero-damage gold", required=required)
    if g.state["gold"] < 1000:
        clear_zero_damage_monsters(g, preserve_yk=0, min_floor=1)
    trace_point(f"final free-gold sweep gain={g.state['gold'] - before_gold}", g)

    if g.state["gold"] < 1000:
        if required:
            g.fail(f"not enough gold for 31F key bundle after final sweep: have={g.state['gold']}")
        g.flags.setdefault("routeWarnings", [])
        g.flags["routeWarnings"].append(
            f"skip optional 31F key bundle/MT20 potions: have={g.state['gold']}G"
        )
        return
    if not g.flags.get(g.trader_flag("MT31", 1, 11)):
        if g.state["floor"] != "MT31":
            g.fly("MT31")
        if not optional_talk_trader(g, "MT31", 1, 11, "31F 1000G 买4黄1蓝"):
            if required:
                g.fail("31F key bundle is funded but its trader is unreachable")
            g.flags.setdefault("routeWarnings", [])
            g.flags["routeWarnings"].append(
                "skip optional 31F key bundle/MT20 potions: trader unreachable"
            )
            return
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
            # A lower-ATK shop allocation may leave a formerly auto-cleared
            # monster on the pocket approach.  Decompose it into genuine
            # door/enemy clicks instead of assuming the high-stat incumbent's
            # direct strict path remains available.
            go_to_decomposed(g, "MT20", *pos, f"20F 蓝门后补血/钥匙 {pos}")
    gained = g.state["hp"] - before_hp
    if gained < 500:
        g.flags.setdefault("routeWarnings", [])
        g.flags["routeWarnings"].append(f"MT20 potion cleanup gained {gained}HP; pocket may have been collected earlier")
    kill_fixed_zero_damage_targets(g, [("MT20", 11, 7)], "final MT20 zero-damage gold")
    trace_point("final after MT20 potion cleanup", g)


def farm_gold_with_key_investment(
    g: Game,
    target_gold: int,
    preserve_yk: int = 1,
    preserve_rk: int = 0,
    max_steps: int = 24,
) -> None:
    """Fallback gold search that may invest a key before collecting a group.

    ``farm_gold_after_coin`` intentionally rejects a first action whose gold is
    below its key valuation.  Near a mandatory endgame stat threshold that can
    strand profitable groups behind a door.  Probe each remaining enemy by a
    fully replayed clone and commit the best positive-gold, surviving action;
    every intervening blocker remains a strict real click.
    """
    sync_mt47_retreat_wizards(g)
    g.set_segment("key-investment gold cleanup")
    yellow_opportunity_cost = int(g.flags.get("keyInvestmentYellowValue", 20))
    for _ in range(max_steps):
        if g.state["gold"] >= target_gold:
            return
        best: tuple[float, int, int, Game] | None = None
        for fid in _visited_floor_ids(g, 1):
            for (x, y), block in list(g.floors[fid].blocks.items()):
                if (
                    block.kind != "enemy"
                    or (fid, x, y) in g.retreat_wizards
                    or (fid, x, y) in g.no_auto_farm
                ):
                    continue
                cand = g.clone()
                try:
                    before = cand.snapshot()
                    if cand.state["floor"] != fid:
                        cand.fly(fid)
                    go_to_decomposed(cand, fid, x, y, f"终局钥匙投资金币 {block.eid}")
                except RouteError:
                    continue
                gain = cand.state["gold"] - before["gold"]
                hp_loss = before["hp"] - cand.state["hp"]
                keys_spent = before["yk"] - cand.state["yk"]
                net_funding_gain = gain - max(0, keys_spent) * yellow_opportunity_cost
                if (
                    gain <= 0
                    or net_funding_gain <= 0
                    or cand.state["hp"] <= 0
                    or cand.state["yk"] < preserve_yk
                    or cand.state["rk"] < preserve_rk
                ):
                    continue
                score = net_funding_gain - max(0, hp_loss) * 0.1
                row = (score, gain, -max(0, hp_loss), cand)
                if best is None or row[:3] > best[:3]:
                    best = row
        if best is None:
            g.fail(f"cannot farm key-investment gold to {target_gold}, have={g.state['gold']}")
        g.__dict__.update(best[3].__dict__)
    if g.state["gold"] < target_gold:
        g.fail(f"key-investment gold exceeded {max_steps} actions, have={g.state['gold']} target={target_gold}")


def buy_shops_to_stat(
    g: Game,
    kind: str,
    target_stat: int,
    note: str,
    preserve_yk: int = 1,
    allow_key_investment: bool = False,
    preserve_rk: int = 0,
) -> None:
    """Buy `kind` (atk/def) shops at MT46 until the stat reaches `target_stat`,
    farming 0-damage-ish monsters (with lucky coin) between purchases. Stops when
    no more gold can be farmed. Mirrors the guide's "def-first then dump atk" plan.
    Farms the WHOLE map (min_floor=1) because the guide collects all positive monsters."""
    stat_key = kind
    while g.state[stat_key] < target_stat:
        cost = shop_cost(g.state["times1"])
        if g.state["gold"] < cost:
            farmed = False
            if preserve_rk <= 0:
                farmed = safe_try(g, farm_gold_after_coin, g, cost, preserve_yk, 1)
            if not farmed and allow_key_investment:
                farmed = safe_try(
                    g,
                    farm_gold_with_key_investment,
                    g,
                    cost,
                    preserve_yk,
                    preserve_rk,
                )
            if not farmed:
                break
        # Funding may traverse a gem/resource group and raise the requested
        # stat to (or beyond) the target.  Re-check after every farming macro;
        # otherwise the loop buys one unnecessary shop level merely because
        # the stat was below target before the resource search began.
        if g.state[stat_key] >= target_stat:
            break
        if g.state["gold"] < cost:
            break
        if g.state["floor"] != "MT46":
            g.fly("MT46")
        go_to_decomposed(g, "MT46", 6, 2, note)
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


def earthquake_and_shield(g: Game, *, bomb_44_guards: bool = True) -> None:
    g.set_segment("earthquake and sacred shield")
    g.fly("MT48")
    g.change_by_stair("MT47", 11, 11, "48F 下楼到47")
    g.talk_trader("MT47", 5, 2, "47F 4000G 买地震卷轴")
    g.fly("MT37")
    g.use_earthquake("37F 炸墙拿关键资源")
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
    # The 45F lower-left upFly route crosses four 300-damage magic fields
    # before the sacred shield.  High-HP guide checkpoints need no potion here,
    # but low-HP branches must consume the smallest reachable combination after
    # the earthquake opens 37F.  Keep HP strictly above the 1200 fixed damage,
    # then reserve all remaining 37F potions for the post-shield cleanup.
    if g.state["hp"] <= 1200:
        eat_minimal_potions_until(g, 1201, "45F pre-shield magic fields", min_floor=1)
    for pos, block in list(g.floors["MT37"].blocks.items()):
        if block.kind == "item" and block.eid in {"redPotion", "bluePotion"}:
            g.blocked_items.add(("MT37", pos[0], pos[1]))
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
    if bomb_44_guards:
        g.use_bomb("44F 炸双卫兵")
    else:
        for pos in ((5, 9), (7, 9)):
            g.go_to("MT44", *pos, f"44F 正常击杀卫兵保留炸弹 {pos}")
    for pos in [(6, 8), (6, 7), (6, 6), (5, 6), (7, 6)]:
        safe_try(g, g.go_to, "MT44", *pos, f"44F shield/potions {pos}")
    g.go_to("MT44", 6, 5, "44F 神圣盾")
    if not g.state["magicImmune"]:
        g.fail("44F 神圣盾后仍未获得魔法免疫")
    g.set_auto(item=True)
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
    if g.state["gold"] >= 1000 and not g.flags.get(g.trader_flag("MT45", 9, 3)):
        buy_mt45_hp_merchant(g, "45F 1000G 买2000血", required=False)
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
    g.go_to("MT13", 6, 10, "13F 走到熔岩口 x6y10")
    if g.block_at("MT13", (6, 5)) is not None:
        for y in [9, 8, 7, 6]:
            block = g.block_at("MT13", (6, y))
            if block and block.eid == "lava":
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
    block = g.block_at("MT26", (6, 7))
    if block and block.eid == "lava":
        g.use_snow("26F 冻结公主前熔岩")
    g.go_to("MT26", 6, 7, "26F 公主前")
    g.talk_mt26_princess()
    trace_point("post_49 after 26F princess", g)

    # --- Step 12b: 45F 1000G -> 2000HP merchant ---
    if g.state["gold"] < 1000:
        safe_try(g, farm_gold_after_coin, g, 1000, 0, 1)
    if g.state["gold"] >= 1000 and not g.flags.get(g.trader_flag("MT45", 9, 3)):
        buy_mt45_hp_merchant(g, "45F 1000G 买2000血", required=False)
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


def post_shield_no49(g: Game, *, stop_before_45_merchant: bool = False) -> None:
    """TE late-49 prep: same as post_shield_49 but WITHOUT the 0F lucky-coin
    trip and WITHOUT the 49F fight.  The downFly picked up at 41F x6y5 is
    reserved for the required TE sequence (24F -> 50F thief -> downFly to 49F
    seal).  No double-gold is taken, so monster gold stays at 1x."""
    g.set_segment("post-shield prep without 49F")
    g.fly("MT43")
    go_to_decomposed(g, "MT43", 3, 1, "43F upper-left yellow door")
    for pos in [(3, 6), (8, 6), (11, 5)]:
        go_to_decomposed(g, "MT43", *pos, f"43F middle/right resource {pos}")
    go_to_decomposed(g, "MT43", 9, 1, "43F upper-right guard")
    go_to_decomposed(g, "MT43", 9, 4, "43F sacred shield")
    go_to_decomposed(g, "MT43", 11, 11, "43F lower-right blue key")
    g.fly("MT46")
    go_to_decomposed(g, "MT46", 3, 8, "46F magic key")
    g.fly("MT41")
    g.use_big_key("41F open all yellow doors")
    go_to_decomposed(g, "MT41", 5, 6, "41F left blue door")
    go_to_decomposed(g, "MT41", 2, 2, "41F upper-left red wizard")
    go_to_decomposed(g, "MT41", 4, 1, "41F upper-left blue key")
    go_to_decomposed(g, "MT41", 7, 6, "41F right blue door")
    go_to_decomposed(g, "MT41", 9, 2, "41F right wall trigger")
    go_to_decomposed(g, "MT41", 10, 2, "41F upper-right red wizard")
    g.fly("MT40")
    g.fly("MT41")
    go_to_decomposed(g, "MT41", 6, 5, "41F downFly")
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
    go_to_decomposed(g, "MT42", 7, 1, "42F red key for late-49 TE")
    trace_point("late49 after 42F red key", g)

    # Late-49 cannot use the 49F knife before 35F dragon.  Buy attack first so
    # magicDragon is not a 100+ turn fight.
    post_shield_atk_target = int(g.flags.get("postShieldAtkTarget", 291))
    buy_shops_to_stat(
        g,
        "atk",
        post_shield_atk_target,
        "46F pre-dragon atk shop",
        preserve_yk=1,
    )
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
    prep_last_shop_kind = str(g.flags.get("postShieldLastShopKind", "atk"))
    if prep_last_shop_kind == "atk":
        buy_shops_to_stat(
            g,
            "atk",
            post_shield_atk_target,
            "46F atk shop",
            preserve_yk=1,
        )
    elif prep_last_shop_kind in {"def", "hp"}:
        cost = shop_cost(g.state["times1"])
        if g.state["gold"] < cost:
            safe_try(g, farm_gold_after_coin, g, cost, 1, 1)
        if g.state["gold"] >= cost:
            if g.state["floor"] != "MT46":
                g.fly("MT46")
            go_to_decomposed(g, "MT46", 6, 2, f"46F prep last {prep_last_shop_kind} shop variant")
            g.buy_shop(prep_last_shop_kind, 1, shop_pos=(6, 1))
    elif prep_last_shop_kind != "skip":
        g.fail(f"unknown postShieldLastShopKind={prep_last_shop_kind}")
    if g.state["gold"] < 1000:
        safe_try(g, farm_gold_after_coin, g, 1000, 0, 1)
    if stop_before_45_merchant:
        return
    merchant_access_eids = ("redWizard", "brownWizard", "redBat")
    merchant_access_damage = sum(int(g.enemy_damage(eid)) for eid in merchant_access_eids)
    if g.state["hp"] <= merchant_access_damage:
        eat_minimal_potions_until(
            g,
            merchant_access_damage + 1,
            "45F HP merchant access battles",
            min_floor=1,
        )
    if g.state["gold"] >= 1000 and not g.flags.get(g.trader_flag("MT45", 9, 3)):
        buy_mt45_hp_merchant(g, "45F 1000G to 2000HP")
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
    # MT49 x6y6 contains the seal event, so downFly is correctly blocked from
    # the current x6y6. Move by one real map click to an empty matching landing.
    g.go_to("MT50", 5, 6, "50F move to legal downFly landing")


def downfly_to_mt49_event(g: Game) -> None:
    if g.state["downFly"] <= 0:
        g.fail("no downFly for late 49F seal")
    if g.state["floor"] != "MT50":
        g.fail(f"late 49F downFly must start on MT50, got {g.state['floor']}")
    g.down_fly("50F downFly to 49F seal event")


def trigger_mt49_event(g: Game) -> None:
    if g.state["floor"] != "MT49":
        g.fail(f"not on MT49 for seal event: {g.state['floor']}")
    g.go_to("MT49", 6, 6, "49F enter seal event")
    before = g.snapshot()
    g._cow("MT49")  # 裸 events.pop 绕过 COW, clone 共享 floor 会泄漏
    g.floors["MT49"].events.pop("6,6", None)
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
    corner_guards = {("MT49", 5, 2), ("MT49", 7, 2), ("MT49", 5, 4), ("MT49", 7, 4)}
    g.retreat_wizards |= corner_guards
    for pos in [(6, 4), (5, 3), (7, 3), (6, 2)]:
        g.go_to("MT49", *pos, f"49F seal cardinal guard {pos}")
    g.flags["49sealed"] = True
    # 50final is cleared so the 49F fake redKing uses 49sealed stats.  It is NOT
    # restored: the 50F true redKing must also be sealed (500/158/19).
    g.flags["50final"] = False
    g.retreat_wizards.difference_update(corner_guards)
    for pos in [(5, 2), (7, 2), (5, 4), (7, 4), (6, 3)]:
        g.go_to("MT49", *pos, f"49F seal corner/fake redKing {pos}")
    for pos in [(5, 2), (7, 2), (2, 4), (3, 4), (4, 4), (8, 4), (9, 4), (10, 4), (5, 5), (6, 5), (7, 5)]:
        safe_try(g, g.go_to, "MT49", *pos, f"49F late reward {pos}")


def _late49_final_stat_shop(g: Game) -> None:
    """The fifth/sixth MT46 stat shop as a strategy variable.

    The sealed TE bosses have low stats, so this shop is a strategy variable
    rather than a hard-coded DEF target.  Search candidates may buy HP or ATK
    with the same gold and must compare the complete tail (not just the next
    fight).  Canonical replay remains DEF unless a search flag says otherwise.
    Extracted so the dragon-deferred variant can run it before the magicDragon.
    """
    final_shop_kind = str(g.flags.get("lateFinalShopKind", "def"))
    if final_shop_kind in {"atk", "def"}:
        gain = 2 * g.floors["MT46"].ratio if final_shop_kind == "atk" else 4 * g.floors["MT46"].ratio
        buy_shops_to_stat(
            g,
            final_shop_kind,
            int(g.state[final_shop_kind]) + gain,
            f"46F endgame {final_shop_kind} shop variant",
            preserve_yk=1,
            allow_key_investment=True,
            preserve_rk=1,
        )
    elif final_shop_kind == "hp":
        buy_hp_with_remaining_gold(
            g,
            max_count=1,
            allow_key_investment=True,
            allow_key_sale=False,
        )
    elif final_shop_kind != "skip":
        g.fail(f"unknown lateFinalShopKind={final_shop_kind}")


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
    # Once the sacred shield makes the remaining half-HP/magic fields harmless,
    # consume profitable door-backed potion groups before the dragon and other
    # mandatory fights.  In addition to their direct HP, any adjacent blue gem
    # now reduces every later battle instead of being stranded at the endpoint.
    collect_positive_hp_resource_groups(
        g,
        min_floor=1,
        preserve_yk=1,
        preserve_rk=1,
        require_stat_and_nonnegative_key_value=True,
    )
    collect_stat_resource_groups(
        g,
        int(g.flags.get("earlyStatGroupBudget", 0)),
        min_floor=1,
        preserve_yk=1,
        preserve_rk=1,
        max_key_value_loss=4,
    )
    eat_all_reachable_potions(g, min_floor=1)

    # The no-49 preparation can end below its intended ATK target because HP
    # was still scarce while farming.  After the potion sweep we have enough HP
    # to convert additional non-zero-damage monsters into shop gold.  Complete
    # the pre-dragon ATK target now, then take the one-time blessing and sacred
    # water early: without the 49F knife this is the legal TE survival bridge to
    # the 35F magicDragon/snow event.
    # With the low-HP preserve-pickaxe checkpoint, ATK 282 before blessing
    # leaves the magicDragon at 8769 damage while all reachable pre-dragon HP
    # totals only 7944. One more +10 ATK shop buy drops the fight safely below
    # that stock. Funding it requires investing spare keys into profitable
    # door-backed monster pockets, so use the same general farm evaluator as
    # the later DEF phase instead of hard-coding a floor or monster.
    pre_dragon_atk_target = 292
    survival_probe = g.clone()
    survival_probe.state["atk"] += int(math.floor(survival_probe.state["atk"] * 0.03 + 0.5))
    survival_probe.state["def"] += int(math.floor(survival_probe.state["def"] * 0.03 + 0.5))
    survival_probe.state["hp"] += int(math.floor(
        (survival_probe.state["atk"] + survival_probe.state["def"]) * 0.74 + 0.5
    )) * 10
    projected_dragon_damage = survival_probe.enemy_damage("magicDragon")
    if (
        projected_dragon_damage != float("inf")
        and survival_probe.state["hp"] > int(projected_dragon_damage) + 20
    ):
        pre_dragon_atk_target = g.state["atk"]
        g.flags.setdefault("routeDecisions", []).append(
            "skip conservative pre-dragon ATK 292 tier: projected blessing+superPotion "
            f"HP={survival_probe.state['hp']} damage={int(projected_dragon_damage)}"
        )
    buy_shops_to_stat(
        g,
        "atk",
        pre_dragon_atk_target,
        "46F final pre-dragon atk shop",
        preserve_yk=1,
        allow_key_investment=True,
        preserve_rk=1,
    )
    while g.state["atk"] < pre_dragon_atk_target:
        cost = shop_cost(g.state["times1"])
        sell_yellow_keys_for_gold(g, cost, preserve_yk=1)
        if g.state["gold"] < cost:
            break
        if g.state["floor"] != "MT46":
            g.fly("MT46")
        go_to_decomposed(g, "MT46", 6, 2, "46F key-sale-funded pre-dragon atk shop")
        g.buy_shop("atk", 1, shop_pos=(6, 1))
        # The higher ATK can turn another group of monsters profitable; retry
        # normal full-map farming before selling more keys for the next buy.
        buy_shops_to_stat(
            g,
            "atk",
            pre_dragon_atk_target,
            "46F final pre-dragon atk shop",
            preserve_yk=1,
            allow_key_investment=True,
            preserve_rk=1,
        )
    if g.state["atk"] < pre_dragon_atk_target:
        g.fail(
            f"cannot fund pre-dragon ATK {pre_dragon_atk_target}, "
            f"have={g.state['atk']} gold={g.state['gold']}"
        )
    g.fly("MT2")
    g.talk_mt2_bless()
    collect_net_yellow_keys_until(g, 1, "16F pre-dragon superPotion oldman path", min_floor=1)
    g.fly("MT16")
    g.talk_mt16_oldman()
    g.use_super_potion("pre-dragon superPotion for late-49 TE")

    # Dragon-deferred variant: the magicDragon has very low DEF (250), so its
    # damage is dominated by hero ATK (each +10 ATK removes a combat round and
    # saves ~1380 HP).  Collect the MT46-48 red gems and run the final stat
    # shop BEFORE the dragon instead of after it, so the dragon is fought at
    # higher ATK/DEF.  The snow/sword5 dependency is untouched (dragon still
    # precedes sword5); the stat shop preserves 1 YK for the sword5 yellow door.
    if g.flags.get("late49DeferDragon"):
        cleanup_reachable_items(g, {"redGem", "blueGem"}, min_floor=1, preserve_rk=1)
        _late49_final_stat_shop(g)

    ensure_hp_for_enemy(g, "magicDragon", 20)
    g.fly("MT35")
    g.go_to("MT35", 6, 7, "35F magic dragon before knife")
    g.go_to("MT35", 6, 6, "35F snow")
    for pos in [(5, 5), (6, 5), (7, 5)]:
        safe_try(g, g.go_to, "MT35", *pos, f"35F dragon potion {pos}")

    collect_net_yellow_keys_until(g, 1, "13F sacred sword yellow door", min_floor=1)
    g.fly("MT13")
    g.go_to("MT13", 6, 10, "13F sacred sword yellow door")
    g.go_to("MT13", 6, 10, "13F stand on lava edge")
    if g.block_at("MT13", (6, 5)) is not None:
        for y in [9, 8, 7, 6]:
            block = g.block_at("MT13", (6, y))
            if block and block.eid == "lava":
                g.use_snow("13F freeze lava for sacred sword")
            g.go_to("MT13", 6, y, f"13F lava path y{y}")
        g.go_to("MT13", 6, 5, "13F sacred sword")
    if not g.flags.get("late49DeferDragon"):
        cleanup_reachable_items(g, {"redGem", "blueGem"}, min_floor=1, preserve_rk=1)
        _late49_final_stat_shop(g)

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
    # A noPass door opens while the hero remains on its adjacent tile. After
    # the final y8 red door, walk into that now-empty door cell so snow is
    # genuinely adjacent to the y7 lava in both Game and the browser.
    g.go_to("MT26", 6, 8, "26F step into opened red-door cell before snow")
    block = g.block_at("MT26", (6, 7))
    if block and block.eid == "lava":
        g.use_snow("26F freeze lava before princess")
    g.go_to("MT26", 6, 7, "26F before princess")
    g.talk_mt26_princess()

    if g.state["gold"] < 1000:
        safe_try(g, farm_gold_after_coin, g, 1000, 0, 1)
    if g.state["gold"] >= 1000 and not g.flags.get(g.trader_flag("MT45", 9, 3)):
        buy_mt45_hp_merchant(g, "45F 1000G to 2000HP")

    buy_hp_with_remaining_gold(g, 4)
    # The 2ATK1DEF late-49 branch has already spent its available monster gold
    # reaching the mandatory DEF/HP thresholds.  This leaderboard cleanup is
    # beneficial when affordable, but is not a prerequisite for TE.
    final_key_bundle_and_mt20_potions(g, required=False)
    eat_all_reachable_potions(g, min_floor=1)
    eat_final_yellow_door_potions(g, min_floor=1, preserve_rk=1)

    g.fly("MT24")
    g.go_to("MT24", 6, 8, "24F red door before 50F thief")
    g.trigger_mt24_to_mt50()
    trigger_mt50_thief(g)
    downfly_to_mt49_event(g)
    trigger_mt49_event(g)
    clear_mt49_from_center(g)

    # downFly enters the sealed center but does not unlock ordinary fly, and the
    # remaining lower-left red-door pocket is only reachable from the stair
    # side. Re-enter with a real MT48 stair click; transition() then records the
    # genuine visit and later search may legally fly to MT49.
    g.fly("MT48")
    g.change_by_stair("MT49", 1, 11, "48F 楼梯重进49F外侧做终局金币清理")
    go_to_decomposed(g, "MT49", 5, 10, "49F 外侧红门后红巫师终局金币")

    # The MT47 redWizards are genuine retreating enemies, not ordinary auto
    # targets. At final stats, use the shared corner-trap click sequence so the
    # optional 180G remains human-reproducible instead of clearing their marker
    # and pretending a direct click can kill them.
    safe_try(g, kill_47_retreat_wizards, g)

    # Search/checkpoint boundary for terminal resource-order optimization.  It
    # is a strategy-level stop (after every mandatory pre-boss fight, before
    # any optional potion/key/shop closure), so candidates can reuse this exact
    # strict-Game state instead of replaying the four-minute prefix for every
    # A* experiment.
    if g.flags.get("stopBeforeTerminalClosure"):
        return

    # Candidate terminal funding edge identified by the full-map audit: the
    # remaining MT9 skeleton pocket is inaccessible after all yellow keys have
    # been converted by the HP closure.  Probe it while the four post-49 keys
    # still exist, then let the generic closure re-optimise the remaining key
    # allocation and shop thresholds.  Each target is still a strict real-click
    # route; a missing/already-auto-cleared sibling is harmless.
    for pos in [(1, 8), (4, 7)]:
        safe_try(g, go_to_decomposed, g, "MT9", pos[0], pos[1], "终局闭包前9F免费怪金币组")

    # All mandatory routing is finished.  Close potion pockets, monster gold,
    # yellow-key sales, and repeated HP-shop thresholds to a fixed point.
    terminal_hp_resource_closure(
        g,
        preserve_blocked_items=bool(g.flags.get("deferBlockedTerminalResources")),
        shops_first=bool(g.flags.get("terminalShopsFirst")),
    )
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
    lines.append("- `库存折算分 = HP + 黄钥匙*100 + 蓝钥匙*500 + 金币*1`；本 Post-40 脚本暂未重算全图剩余资源 `final-score`。")
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
