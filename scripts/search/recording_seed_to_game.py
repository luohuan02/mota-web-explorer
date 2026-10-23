#!/usr/bin/env python3
"""将录像的语义节点顺序转换为严格 Game walk。

此工具不尝试逐帧复刻 ``.h5route``。录像 capture 只提供“下一件有意义的事”
的顺序；完整 browser save 才是世界状态真相。每个节点由共享 Game / Game
按严格 target-click 模型重新规划，录像 statlog 只输出诊断，绝不回写英雄数值。

capture JSON 最小格式::

  {
    "recording": {"path": "...", "sha256": "..."},
    "semantic_actions": [
      {"index": 12, "kind": "target", "floor": "MT29", "pos": [6, 2]},
      {"index": 13, "kind": "fly", "floor": "MT31"}
    ],
    "statlog": [{"f":"MT29", "x":6, "y":2, "hp":..., ...}]
  }

``kind=target`` 可指向怪、门、物品、假墙、楼梯或空事件 trigger。普通空
waypoint 会被跳过；事件 trigger 空格不会。choices/tool/NPC 等不能从 route token
可靠推断时，capture 必须显式写成 ``shop``/``trader``/``tool``/``event``，否则
转换立即报错，而不是猜测或用 statlog 修资源。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.solver.game_route import (
    AUTO_KEYS, STAIRS, RouteError, WALL_IDS, classify, floor_no,
    go_to_decomposed, load_enemies, load_tiles, next_floor, prev_floor,
    read_json, shop_cost,
)
from src.solver.game_route import Game

MT20_KILL_EXPECTED = {
    "floor": "MT20", "x": 6, "y": 5,
    "hp": 1215, "atk": 76, "def": 66,
    "yk": 5, "bk": 0, "rk": 0, "gold": 1298,
}
VALUE_FIELDS = ("hp", "atk", "def", "yk", "bk", "rk", "gold")

# 敌人踩在楼梯块上的复合格（block=enemy 叠在 stair tile 上，敌人死后楼梯显形）。
# (fid, pos) -> 楼梯下的敌人 eid。与 game_route._after_action_impl 的机制知识一致。
_ENEMY_ON_STAIR_TILES = [("MT40", (6, 1), "yellowKnight")]


@dataclass(frozen=True)
class SemanticAction:
    index: int
    kind: str
    floor: str | None
    pos: tuple[int, int] | None
    eid: str | None
    data: dict[str, Any]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_action(raw: dict[str, Any], fallback_index: int) -> SemanticAction:
    if not isinstance(raw, dict):
        raise ValueError(f"semantic action #{fallback_index} is not an object")
    kind = raw.get("kind")
    if not isinstance(kind, str) or not kind:
        raise ValueError(f"semantic action #{fallback_index} has no kind")
    floor = raw.get("floor")
    if floor is not None and not isinstance(floor, str):
        raise ValueError(f"semantic action #{fallback_index} floor must be a string")
    pos_raw = raw.get("pos")
    pos = None
    if pos_raw is not None:
        if not (isinstance(pos_raw, list) and len(pos_raw) == 2
                and all(isinstance(v, int) for v in pos_raw)):
            raise ValueError(f"semantic action #{fallback_index} pos must be [x,y]")
        pos = (pos_raw[0], pos_raw[1])
    return SemanticAction(
        index=int(raw.get("index", fallback_index)), kind=kind, floor=floor,
        pos=pos, eid=raw.get("eid"), data=raw,
    )


def _derived_actions_from_route(route: list[Any]) -> list[dict[str, Any]]:
    """Derive semantic actions from a decoded route token list.

    The recording's statlog is optional evidence; the route token order is the
    action sequence. ``move:x:y`` is a click endpoint on the action's pre-action
    floor. Direction input targets the adjacent tile (Game's current position +
    delta) -- a plain empty or wall tile is skipped, an actionable block or
    event trigger is executed. ``choices``/``item`` are left as blocking
    semantic actions that require explicit annotation; they are not guessed.
    """
    directions = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}
    derived: list[dict[str, Any]] = []
    for index, token in enumerate(route):
        if not isinstance(token, str):
            continue
        if token.startswith("move:"):
            parts = token.split(":")
            if len(parts) >= 3:
                derived.append({"index": index, "kind": "target", "pos": [int(parts[1]), int(parts[2])],
                                "source_token": token})
        elif token.startswith("fly:"):
            derived.append({"index": index, "kind": "fly", "floor": token.split(":", 1)[1],
                            "source_token": token})
        elif token in directions:
            derived.append({"index": index, "kind": "arrow", "direction": token,
                            "source_token": token})
        elif token.startswith("choices") or token == "help" or token.startswith("turn"):
            # choices/help/turn are recorder UI actions; the semantic converter
            # does not guess shop/trader/tool meaning from them.
            continue
        elif token.startswith("item:"):
            derived.append({"index": index, "kind": "tool", "tool": token.split(":", 1)[1],
                            "source_token": token})
    return derived


def _statlog_entry_flat(item: dict[str, Any]) -> bool:
    """rec1-style statlog: flat {i, action, f, x, y, hp, ...} (pre-state)."""
    return isinstance(item, dict) and "action" in item and "f" in item


def _event_positions_cache() -> dict[str, set[tuple[int, int]]]:
    """Map fid -> set of (x,y) event-trigger tiles from data/maps/ (static).

    Used by the statlog skip filter to avoid dropping arrows that face an
    event tile (action-triggered events like MT16 (11,11) superPotion don't
    change hero stats, so before==after, but the arrow is meaningful).
    """
    cache: dict[str, set[tuple[int, int]]] = {}
    maps_dir = ROOT / "data" / "maps"
    for p in sorted(maps_dir.glob("mt*_map.json")):
        fid = p.stem.replace("_map", "").upper()  # MT16 (statlog uses uppercase)
        try:
            raw = json.loads(p.read_text(encoding="utf-8-sig"))
        except Exception:
            continue
        events = raw.get("events") if isinstance(raw, dict) else None
        if not isinstance(events, dict):
            continue
        poses: set[tuple[int, int]] = set()
        for loc in events:
            try:
                sx, sy = loc.split(",")
                poses.add((int(sx), int(sy)))
            except (ValueError, AttributeError):
                continue
        cache[fid] = poses
    return cache


_EVENT_POSITIONS_CACHE: dict[str, set[tuple[int, int]]] | None = None


def _before_targets_stair(before: dict[str, Any], direction: str) -> bool:
    """Whether an arrow press targets a stair tile, judged from a statlog
    `before` sample + the pressed direction (no Game instance needed).

    Stair = the floor's changeFloor entry at the target tile, or the
    enemy-on-stair composite (e.g. MT40 (6,1) yellowKnight hiding the upFloor).
    """
    d = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}.get(direction)
    if d is None or not isinstance(before, dict):
        return False
    fid = before.get("f")
    floor = _floor_change_floor_cache().get(fid)
    if floor is None:
        return False
    tx, ty = before.get("x", 0) + d[0], before.get("y", 0) + d[1]
    if f"{tx},{ty}" in floor:
        return True
    return (fid, tx, ty) in {(f2, x2, y2) for f2, (x2, y2), _e in _ENEMY_ON_STAIR_TILES}


_CHANGE_FLOOR_CACHE: dict[str, dict[str, Any]] | None = None


def _floor_change_floor_cache() -> dict[str, dict[str, Any]]:
    """Map fid -> changeFloor dict from data/maps (static, cached)."""
    global _CHANGE_FLOOR_CACHE
    if _CHANGE_FLOOR_CACHE is None:
        cache: dict[str, dict[str, Any]] = {}
        maps_dir = ROOT / "data" / "maps"
        for p in sorted(maps_dir.glob("mt*_map.json")):
            fid = p.stem.replace("_map", "").upper()
            try:
                raw = json.loads(p.read_text(encoding="utf-8-sig"))
            except Exception:
                continue
            cf = raw.get("changeFloor") if isinstance(raw, dict) else None
            if isinstance(cf, dict):
                cache[fid] = cf
        _CHANGE_FLOOR_CACHE = cache
    return _CHANGE_FLOOR_CACHE


def _event_positions() -> dict[str, set[tuple[int, int]]]:
    global _EVENT_POSITIONS_CACHE
    if _EVENT_POSITIONS_CACHE is None:
        _EVENT_POSITIONS_CACHE = _event_positions_cache()
    return _EVENT_POSITIONS_CACHE


_TILE_PASSABLE_CACHE: dict[str, dict[tuple[int, int], bool]] | None = None


def _tile_passable(fid: str, x: int, y: int) -> bool:
    """Whether a key press toward (fid,x,y) can MOVE the hero (static base grid).

    Passable = empty tile, item, stair, or passable decor (classify None, e.g.
    whiteWall2). Blocked = terrain wall / fakeWall / closed door / enemy / NPC
    -- pressing into these turns or faces in place, so a before==after statlog
    phase is a real facing (not an absorbed press). Doors/enemies can change at
    runtime, but for the no-op filter's purpose the base grid is the right
    prior: a press toward a base-passable tile that shows no movement was
    absorbed, and a press toward a base-blocked tile is meaningful facing.
    """
    global _TILE_PASSABLE_CACHE
    if _TILE_PASSABLE_CACHE is None:
        tiles = load_tiles()
        enemies = load_enemies()
        cache: dict[str, dict[tuple[int, int], bool]] = {}
        maps_dir = ROOT / "data" / "maps"
        for p in sorted(maps_dir.glob("mt*_map.json")):
            f2 = p.stem.replace("_map", "").upper()
            raw = read_json(p)
            grid = raw.get("map") or raw.get("m") or []
            cells: dict[tuple[int, int], bool] = {}
            for yy, row in enumerate(grid):
                for xx, tile in enumerate(row):
                    if tile == 0:
                        cells[(xx, yy)] = True
                        continue
                    info = tiles.get(tile)
                    if not info:
                        cells[(xx, yy)] = False
                        continue
                    eid = info["id"]
                    kind = classify(eid, info.get("cls", ""), enemies)
                    cells[(xx, yy)] = (eid in STAIRS or kind == "item"
                                       or kind is None)
            cache[f2] = cells
        _TILE_PASSABLE_CACHE = cache
    return _TILE_PASSABLE_CACHE.get(fid, {}).get((x, y), False)


def _statlog_to_route_map(route: list[Any], statlog_len: int) -> list[int]:
    """Map each statlog index to the route index of its token.

    The capture's statlog records every ``_doReplayAction`` call EXCEPT
    ``choices`` tokens (menu selections are consumed inside the action-chain
    dialog, not via ``_doReplayAction``). ``help`` / ``turn`` / moves / arrows
    / fly / item are all present. So the statlog is the route with every
    ``choices`` token removed. This map lets us read the ``choices`` sequence
    that follows a ``help`` token (the SET_AUTO menu interaction) from the
    route, even though those choices are absent from the statlog.
    """
    out: list[int] = []
    ri = 0
    for _ in range(statlog_len):
        while ri < len(route) and isinstance(route[ri], str) and route[ri].startswith("choices"):
            ri += 1
        out.append(ri)
        ri += 1
    return out


def _read_choices_after(route: list[Any], help_ri: int) -> list[int]:
    """Read the ``choices:N`` tokens immediately following a ``help`` token.

    ``help_ri`` is a *coarse* route position from ``_statlog_to_route_map``,
    which assumes statlog and route are 1:1. Native replay captures (the
    capture_h5route_cdp.js 3-phase turn/path/execute expansion) produce ~2-3
    statlog entries per route token, so the mapped index drifts far past the
    real ``help`` token. Snap to the nearest actual ``help`` at-or-before the
    mapped index, then read the ``choices`` that immediately follow it. Since
    ``choices`` always immediately follow their ``help``, this is exact.
    """
    help_ri = max((i for i, t in enumerate(route[:help_ri + 1]) if t == "help"),
                  default=help_ri)
    seq: list[int] = []
    j = help_ri + 1
    while j < len(route) and isinstance(route[j], str) and route[j].startswith("choices"):
        try:
            seq.append(int(route[j].split(":", 1)[1]))
        except (ValueError, IndexError):
            pass
        j += 1
    return seq


def _apply_set_auto_toggles(current: dict[str, Any], choices: list[int]) -> dict[str, Any]:
    """Apply a 游戏说明 -> 自动操作 menu selection sequence to the auto state.

    The ``help`` token opens the 游戏说明 commonEvent menu. The following
    ``choices:N`` tokens select menu entries:

    - Top-level 游戏说明 menu: ``4`` = 自动操作 (enter submenu), ``6`` = 返回游戏
      (return, ends the interaction). Other indices (游戏特性/结局/榜单/...) are
      ignored -- they don't touch ``__auto__``.
    - 自动操作 submenu: ``0`` = 清零伤怪 battle (toggle true↔false), ``1`` = 拾取
      物品 item (toggle true↔false), ``2`` = 开暗墙岩浆 wall (toggle), ``3`` =
      退出 (exit submenu), ``4`` = 拾取血瓶 item (toggle true↔nopotion).

    A bare ``help`` + ``choices:6`` (open then immediately return) is a no-op.
    Returns the new auto_flags dict (battle/item/wall only). The caller emits a
    ``设置自动`` step only when this differs from the current state.
    """
    auto = {k: current.get(k, False) for k in AUTO_KEYS}
    in_submenu = False
    for c in choices:
        if not in_submenu:
            if c == 4:          # enter 自动操作 submenu
                in_submenu = True
            # c == 6 (返回游戏) or other top-level: no auto change
        else:
            if c == 0:          # battle toggle
                auto["battle"] = not bool(auto.get("battle"))
            elif c == 1:        # item toggle true↔false
                auto["item"] = False if auto.get("item") is True else True
            elif c == 2:        # wall toggle
                auto["wall"] = not bool(auto.get("wall"))
            elif c == 4:        # item toggle true↔nopotion
                auto["item"] = "nopotion" if auto.get("item") is True else True
            elif c == 3:        # exit submenu
                in_submenu = False
            # other indices ignored
    return auto


def _derived_actions_from_statlog(capture: dict[str, Any]) -> list[dict[str, Any]]:
    """Derive only unambiguous target/fly nodes from an immutable raw capture.

    Supports two statlog shapes:
    - rec1 flat: each entry is the pre-state of its action; the next entry is
      the post-state.
    - capture-wrapped: each entry has {before, after, action, index}.

    ``move:x:y`` is a click endpoint on the action's pre-action floor. Direction
    input is mapped to its adjacent target only when it produced a visible
    position/stat/event change. Menu choices and tools deliberately stay
    unresolved: guessing their semantic meaning would violate the seed contract.
    """
    log = capture.get("statlog")
    if not isinstance(log, list):
        raise ValueError("raw capture has no statlog for semantic derivation")
    route = capture.get("route") if isinstance(capture.get("route"), list) else []
    sl_to_ri = _statlog_to_route_map(route, len(log)) if route else []
    directions = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}
    derived: list[dict[str, Any]] = []
    emitted_help_route: set[int] = set()
    # Exact statlog-help-run <-> route-help correlation. The capture's 3-phase
    # turn/path/execute expander turns ONE route "help" token into a run of 2-3
    # consecutive "help" statlog entries; those runs and the route "help" tokens
    # are in the same order, so the k-th statlog help run maps to the k-th route
    # help token. The coarse sl_to_ri linear map (~1 statlog entry per route
    # token) drifts ~3x past the real help, so `max(help <= coarse)` snaps every
    # help onto the LAST help when a recording has several toggles (e.g. zone4's
    # item->nopotion at MT20, then back ON after the shield) -- dropping the
    # earlier toggles. This run-based correlation is exact regardless of the
    # number of helps or the per-token expansion rate.
    route_help_idxs = [i for i, t in enumerate(route) if t == "help"]
    # Runs of consecutive "help" statlog entries.
    statlog_help_runs: list[list[int]] = []
    _in_help_run = False
    for _i, _item in enumerate(log):
        _seg = ((_item.get("action") if isinstance(_item, dict) else None)
                or ((_item.get("before") or {}).get("action") if isinstance(_item, dict) else None))
        _is_help = _seg == "help"
        if _is_help and not _in_help_run:
            statlog_help_runs.append([_i])
            _in_help_run = True
        elif _is_help:
            statlog_help_runs[-1].append(_i)
        elif not _is_help:
            _in_help_run = False
    # Align help runs to route help tokens by PHASE CAPACITY, not 1:1 order.
    # Each route token expands to ~scale statlog phases (native replay capture),
    # so a run of L entries serves round(L/scale) route help tokens. Adjacent
    # no-op menu opens (help+choices:6 twice in a row, e.g. 38729 route[924]/
    # [926]) merge into ONE statlog run because their phases are adjacent with
    # no action between; the old k-th-run <-> k-th-token correlation then saw
    # fewer runs than tokens and shifted every later REAL toggle (route[1106]
    # item nopotion->true) onto a no-op token, silently dropping it (MT40
    # bluePotion sweep +1600 divergence). Capacity alignment keeps the mapping
    # monotone and total: runs are consumed in order, each serving
    # max(1, round(len/scale)) tokens.
    _n_non_choice = len([t for t in route
                         if not (isinstance(t, str) and t.startswith("choices"))])
    _scale = (len(log) / _n_non_choice) if _n_non_choice else 2.0
    help_entry_to_route: dict[int, int] = {}
    _hi = 0
    for _run in statlog_help_runs:
        if _hi >= len(route_help_idxs):
            break
        _cap = max(1, round(len(_run) / _scale))
        _cap = min(_cap, len(route_help_idxs) - _hi)
        for _j in range(_cap):
            _entry = _run[min(round(_j * len(_run) / _cap), len(_run) - 1)]
            help_entry_to_route[_entry] = route_help_idxs[_hi]
            _hi += 1
    for index, item in enumerate(log):
        if not isinstance(item, dict):
            continue
        wrapped = isinstance(item.get("before"), dict)
        before = item["before"] if wrapped else item
        after = item.get("after") if wrapped else (log[index + 1] if index + 1 < len(log) else {})
        action = item.get("action") or before.get("action")
        if not isinstance(action, str):
            continue
        # SET_AUTO menu interaction (help + choices) MUST be handled before the
        # before==after no-op filter: 'help' never changes hero stats (before==
        # after), so the no-op filter's `else: continue` would drop it, but it
        # changes __auto__ (item true->nopotion etc.) -- a real state change the
        # converter must track. The choices sequence lives in the route (absent
        # from the statlog); execute_action applies the toggles and records a
        # 设置自动 step only when the auto state actually changes.
        #
        # Native replay captures emit ~2-3 statlog phases per route token, so
        # one 'help' route token can produce several consecutive "help" statlog
        # entries (all the same dialog interaction). Each would read the same
        # trailing choices and TOGGLE auto twice -> net to the wrong state. Emit
        # set_auto only for the FIRST help entry of a run (dedupe by the snapped
        # route help index, which is equal for all phases of the same token).
        if action == "help":
            # Map this statlog help entry to its aligned route "help" token
            # (phase-capacity precompute above; one entry per token, first
            # phase of each token emits).
            snapped = help_entry_to_route.get(index)
            if snapped is None:
                continue
            if snapped in emitted_help_route:
                continue
            emitted_help_route.add(snapped)
            derived.append({"index": index, "kind": "set_auto",
                            "choices": _read_choices_after(route, snapped),
                            "floor": before.get("f"), "stat_index": index,
                            "source_token": "help"})
            continue
        # Native replay captures (capture_h5route_cdp.js) expand each route
        # token into ~3 statlog phases (turn/path-compute/execute); only the
        # execute phase changes hero state. Skipping before==after no-op
        # phases keeps derived actions 1:1 with route tokens, so arrows don't
        # over-move the hero (3 "up" entries for 1 step would move 3 tiles).
        # Event triggers that only flip the event field are kept (before!=after).
        # Exception: item: tools that change the MAP but not hero stats
        # (pickaxe breaks an adjacent wall, hero stays put -> before==after for
        # all 3 phases). For these, keep only the LAST phase of the consecutive
        # run (the execute), so the pickaxe use isn't dropped. centerFly/upFly/
        # downFly move the hero (before!=after) so their execute phase is kept
        # by the general before!=after rule below.
        if wrapped and isinstance(after, dict) and before == after:
            if action.startswith("item:"):
                is_last_of_run = (index + 1 >= len(log)
                                  or not isinstance(log[index + 1], dict)
                                  or log[index + 1].get("action") != action)
                if not is_last_of_run:
                    continue
            elif action in directions:
                dx, dy = directions[action]
                tgt = (before.get("x", 0) + dx, before.get("y", 0) + dy)
                fid = before.get("f")
                is_stair_tgt = _before_targets_stair(before, action)
                if is_stair_tgt:
                    # 楼梯目标箭头（2026-09-04 40145/41218 修复）：与 item: 同理，
                    # 一个 press 的多个相位里只保留最后一个（execute 相位，可能
                    # 显示换层或位置变化）——全部保留会 1 press 派生 N 支箭头
                    # （hero 多走 N-1 格），全丢则换层丢失。
                    is_last_of_run = (index + 1 >= len(log)
                                      or not isinstance(log[index + 1], dict)
                                      or log[index + 1].get("action") != action)
                    if not is_last_of_run:
                        continue
                # 2026-09-05 41200 修复：非 event 格的 before==after 相位一律
                # 丢弃（老行为）。event 格相位：若同一 press run（连续同方向
                # token 的多个相位）中某相位把 hero 真实移到了本相位面向的目标
                # 格 T 上，则本相位只是 hero 仍在自动走路时被吞掉的重复按键——
                # 上格由那个相位执行，丢弃；否则该相位是承载性的：hero 面向
                # noPass 事件格（MT16 (11,11) fakeWall2+老人、MT29 (6,2) thief）
                # 触发事件 / 破墙不移动，before==after 是唯一证据，保留。
                # （不用静态格子可通行性判断：目标格可能是运行时已开/已破的门或
                # 墙——41200 MT10 (6,9) 基础图是红门、按键时已被 sweep 打开。）
                if not (fid in _event_positions()
                        and tgt in _event_positions().get(fid, set())):
                    continue
                run_start = index
                while (run_start - 1 >= 0 and isinstance(log[run_start - 1], dict)
                       and log[run_start - 1].get("action") == action):
                    run_start -= 1
                run_end = index
                while (run_end + 1 < len(log) and isinstance(log[run_end + 1], dict)
                       and log[run_end + 1].get("action") == action):
                    run_end += 1
                absorbed = False
                for k in range(run_start, run_end + 1):
                    e = log[k]
                    eb, ea = e.get("before"), e.get("after")
                    if (isinstance(eb, dict) and isinstance(ea, dict)
                            and eb != ea
                            and ea.get("f") == fid
                            and (ea.get("x"), ea.get("y")) == tgt):
                        absorbed = True
                        break
                if absorbed:
                    continue
            else:
                continue
        if action.startswith("move:"):
            _, sx, sy = action.split(":", 2)
            derived.append({"index": index, "kind": "target", "floor": before["f"],
                            "pos": [int(sx), int(sy)], "stat_index": index,
                            "source_token": action})
        elif action.startswith("fly:"):
            derived.append({"index": index, "kind": "fly", "floor": action.split(":", 1)[1],
                            "stat_index": index, "source_token": action})
        elif action in directions:
            dx, dy = directions[action]
            # Include every arrow, not just position/stat-changing ones: an
            # arrow onto an event trigger (e.g. MT29 (6,2) thief) may change
            # the map without moving the hero or altering stats. The arrow
            # handler skips pure turns (empty/wall targets) at runtime.
            derived.append({"index": index, "kind": "arrow", "floor": before["f"],
                            "direction": action, "stat_index": index,
                            "source_token": action})
        elif action.startswith("choices") or action == "turn":
            continue
        elif action.startswith("item:"):
            derived.append({"index": index, "kind": "tool", "tool": action.split(":", 1)[1],
                            "stat_index": index, "source_token": action})
    return derived


def _derive_semantic_actions(capture: dict[str, Any]) -> list[dict[str, Any]]:
    """Prefer explicit annotation; fall back to statlog (has floor), then route."""
    raw = capture.get("semantic_actions")
    if isinstance(raw, list) and raw:
        return raw
    statlog = capture.get("statlog")
    if isinstance(statlog, list) and statlog:
        return _derived_actions_from_statlog(capture)
    route = capture.get("route")
    if isinstance(route, list) and route:
        return _derived_actions_from_route(route)
    raise ValueError("capture must contain semantic_actions[], route[], or statlog[]")


def _stage_slice(actions: list[SemanticAction], capture: dict[str, Any],
                 stage: str, start_stat: int | None,
                 stop_floor_override: str | None = None) -> list[SemanticAction]:
    """Bound the stage by the recording's own floor progression.

    The statlog's floor field is reliable evidence of where each action ran,
    even when its HP/gold drift. Stage 1 starts at the verified MT20 seed
    state and stops at the first action on MT31; stage 2 starts at MT31 and
    stops at MT41. ``start_stat`` is the statlog index matching the seed state.
    ``stop_floor_override`` lets a full-from-save1 stage (mt4-mt31, whose
    default stop is None = process all) stop at an earlier floor (e.g. MT41 to
    reproduce only zone1-2 + zone3 from a recording that continues into zone4).
    """
    stop_floor = stop_floor_override if stop_floor_override else STAGE_STOP_FLOOR[stage]
    if start_stat is not None:
        # SET_AUTO（help+choices 的 auto 切换）不随 stage 切片丢弃：有的录像在
        # 1F-3F 固定前缀里就开 auto（41218 route#2 help），切掉后模型全程
        # auto 关闭、sweep 全死（铁剑/fakeWall/钥匙全面失同步）。
        actions = [a for a in actions
                   if a.kind == "set_auto" or a.data.get("stat_index", a.index) >= start_stat]
    statlog = capture.get("statlog") if isinstance(capture.get("statlog"), list) else []
    out: list[SemanticAction] = []
    for action in actions:
        out.append(action)
        si = action.data.get("stat_index")
        if not isinstance(si, int) or not (0 <= si < len(statlog)):
            continue
        observed = statlog[si]
        wrapped = isinstance(observed, dict) and isinstance(observed.get("after"), dict)
        after = observed["after"] if wrapped else (
            statlog[si + 1] if si + 1 < len(statlog) and isinstance(statlog[si + 1], dict) else {})
        if stop_floor is not None and after.get("f") == stop_floor:
            break
    return out


def _statlog_floor(statlog: list[Any], stat_index: Any, which: str) -> str | None:
    """Read the before/after floor id for a statlog frame, or None.

    Handles both wrapped ({before, after}) and flat ({f, ...}) statlog entries.
    """
    if not isinstance(stat_index, int) or not (0 <= stat_index < len(statlog)):
        return None
    entry = statlog[stat_index]
    if not isinstance(entry, dict):
        return None
    if which == "before":
        b = entry.get("before")
        return (b.get("f") if isinstance(b, dict) else entry.get("f"))
    a = entry.get("after")
    if isinstance(a, dict):
        return a.get("f")
    nxt = statlog[stat_index + 1] if stat_index + 1 < len(statlog) else None
    if isinstance(nxt, dict):
        b = nxt.get("before")
        return (b.get("f") if isinstance(b, dict) else nxt.get("f"))
    return None


def _cancel_stair_bounce_arrows(actions: list[SemanticAction],
                                statlog: list[Any],
                                seed_visited: set[str] | None = None) -> list[SemanticAction]:
    """Cancel adjacent opposite stair-transition arrows that are pure no-ops.

    The recording sometimes captures the player bouncing the hero across an
    upFloor/downFloor stair with no game effect -- e.g. MT32(10,1)<->MT33(10,1)
    pressed "right" 7 times, or MT20<->MT21, MT36<->MT37, MT38<->MT39. Each
    such arrow becomes a 通过+换层 pair in the walk: pure noise that the live
    replayer would replay as visible up-then-down stair bouncing.

    A "stair-step arrow" is an arrow whose before.floor != after.floor (it
    stepped onto a stair and transitioned). Two consecutive stair-step arrows
    A->B then B->A, with no non-arrow semantic action between, form a round
    trip. The round trip is a pure no-op ONLY IF floor B was already visited
    before the pair -- otherwise the first A->B is load-bearing: it visits B
    for the first time, unlocking ``fly:B`` later (e.g. MT32->MT33 at frame 777
    is the first MT33 visit, required by the later ``fly:MT33``). So we track
    the visited set (seed + floors visited earlier in the stage) and only
    cancel arrows whose destination was already visited.

    Stack-based: a cancellable arrow A->B whose predecessor on the stack is the
    opposite B->A pops and cancels both (iterative, so a bounce chain collapses
    to its single net transition). A load-bearing arrow (B newly visited) and
    any non-arrow action break the chain (clear the stack) so a real action or
    a first-time visit between two transitions means the trip was load-bearing.
    """
    if not statlog:
        return actions
    visited = set(seed_visited) if seed_visited else set()
    # transition[i] = (from_floor, from_pos, to_floor, to_pos) for stair-step
    # arrows, else None. Position is tracked because a stair round trip
    # A(p1)->B->A(p2) is only a pure no-op if p2 == p1 (hero returns to the
    # same tile). The MT24-26 princess sequence bounces MT26(1,10)->MT25(2,11)
    # ->MT24(2,11)->...->MT26(2,11): the return to MT26 lands at (2,11), not
    # (1,10), so the bounce moved the hero and is load-bearing (must not cancel).
    transition: list[tuple[str, tuple, str, tuple] | None] = []
    for a in actions:
        if a.kind != "arrow":
            transition.append(None)
            continue
        si = a.data.get("stat_index")
        pre, post = _statlog_states(statlog, si)
        f_b = pre.get("f") if isinstance(pre, dict) else None
        f_a = post.get("f") if isinstance(post, dict) else None
        if f_b and f_a and f_b != f_a:
            pos_b = (pre.get("x"), pre.get("y"))
            pos_a = (post.get("x"), post.get("y"))
            transition.append((f_b, pos_b, f_a, pos_a))
        else:
            transition.append(None)

    removed = [False] * len(actions)
    stack: list[int] = []  # indices of uncancelled cancellable stair-step arrows
    for idx, a in enumerate(actions):
        t = transition[idx]
        if t is None:
            # Non-stair action (non-arrow or same-floor arrow): commit the
            # stack (keep all pending), clear it so a later stair arrow can't
            # cancel across a real action.
            stack = []
            continue
        _from, _from_pos, to, _to_pos = t
        is_new_visit = to not in visited
        visited.add(to)
        if is_new_visit:
            # Load-bearing first visit: keep it, break the cancellation chain.
            stack = []
            continue
        if stack:
            top = stack[-1]
            top_t = transition[top]
            # top is the opposite B->A round-trip partner: top.from==A ==
            # current.to, top.to==B == current.from, AND the hero returns to
            # the same tile on A (current.to_pos == top.from_pos). Position
            # check: a bounce that lands on a different tile moved the hero
            # and is load-bearing (e.g. MT26(1,10)->MT25->MT26(2,11)).
            if (top_t is not None
                    and top_t[2] == _from       # top.to  (B) == current.from (B)
                    and top_t[0] == to          # top.from(A) == current.to   (A)
                    and t[3] == top_t[1]):      # current.to_pos == top.from_pos
                stack.pop()
                removed[top] = True
                removed[idx] = True
                continue
        stack.append(idx)
    return [a for idx, a in enumerate(actions) if not removed[idx]]


def load_capture(path: Path) -> tuple[dict[str, Any], list[SemanticAction]]:
    capture = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(capture, dict):
        raise ValueError("capture root must be an object")
    raw_actions = _derive_semantic_actions(capture)
    if not isinstance(raw_actions, list):
        raise ValueError("capture must contain semantic_actions[], route[], or statlog[]")
    return capture, [parse_action(raw, i) for i, raw in enumerate(raw_actions)]


def validate_seed_snapshot(raw: dict[str, Any], stage: str) -> None:
    """Reject report-only final snapshots before constructing Game."""
    if not isinstance(raw, dict) or "hero" not in raw or "floorId" not in raw:
        raise ValueError("seed-save must be a complete browser save, not a walk final snapshot")
    hero = raw.get("hero")
    if not isinstance(hero, dict):
        raise ValueError("seed-save hero is missing")
    for key in ("maps", "x", "y", "hp", "atk", "def", "money", "flags", "tools"):
        if key not in raw and key not in hero:
            raise ValueError(f"seed-save missing complete-world field: {key}")
    if not isinstance(raw.get("maps"), dict):
        raise ValueError("seed-save maps must be a complete map object")
    if not isinstance(hero.get("flags"), dict) or not isinstance(hero.get("tools"), dict):
        raise ValueError("seed-save hero.flags/tools are required")
    if not isinstance(hero["flags"].get("__visited__"), dict):
        raise ValueError("seed-save hero.flags.__visited__ is required")
    if stage == "mt20-mt31":
        state = {
            "floor": raw["floorId"], "x": hero["x"], "y": hero["y"],
            "hp": hero["hp"], "atk": hero["atk"], "def": hero["def"],
            "yk": hero["yk"], "bk": hero["bk"], "rk": hero["rk"],
            "gold": hero["money"],
        }
        diff = {k: (state.get(k), v) for k, v in MT20_KILL_EXPECTED.items()
                if state.get(k) != v}
        if diff:
            raise ValueError(f"mt20-mt31 seed is not verified slot-32 KILL state: {diff}")


def _post_state(statlog: list[Any], si: Any) -> dict[str, Any] | None:
    """Resolve the post-action observed state from a statlog index.

    Wrapped capture: entry has {after}. Flat rec1 statlog: entry is the
    pre-state, so the post-state is the next entry.
    """
    if not isinstance(si, int) or not (0 <= si < len(statlog)):
        return None
    entry = statlog[si]
    if not isinstance(entry, dict):
        return None
    if isinstance(entry.get("after"), dict):
        return entry["after"]
    if si + 1 < len(statlog) and isinstance(statlog[si + 1], dict):
        return statlog[si + 1]
    return entry


def stat_diagnostic(g: Game, observed: dict[str, Any] | None,
                    action: SemanticAction) -> dict[str, Any] | None:
    if not isinstance(observed, dict):
        return None
    # Raw native captures store {before, after}; legacy captures store the
    # flat state itself. Prefer after because a semantic action has just run.
    if isinstance(observed.get("after"), dict):
        observed = observed["after"]
    state = g.snapshot()
    aliases = {"floor": "f", "gold": "g"}
    value_diff = {}
    for field in VALUE_FIELDS:
        source = aliases.get(field, field)
        if source in observed and state[field] != observed[source]:
            value_diff[field] = {"game": state[field], "recorded": observed[source]}
    position_diff = {}
    for field, source in (("floor", "f"), ("x", "x"), ("y", "y")):
        if source in observed and state[field] != observed[source]:
            position_diff[field] = {"game": state[field], "recorded": observed[source]}
    if not value_diff and not position_diff:
        return None
    return {
        "recording_index": action.index,
        "kind": action.kind,
        "value_diff": value_diff,
        "position_diff": position_diff,
    }


def is_event_trigger(g: Game, fid: str, pos: tuple[int, int]) -> bool:
    return f"{pos[0]},{pos[1]}" in g.floors[fid].events


def _is_shop_npc(block: Any) -> bool:
    """A shop NPC tile (blueShop / shop). Mirrors the live replayer's
    isShopLikeEvent so the converter and verifier agree on what is a shop."""
    if block is None or getattr(block, "kind", None) != "npc":
        return False
    eid = block.eid or ""
    return eid == "shop" or eid == "blueShop" or eid.startswith("blueShop")


def _is_trader_npc(block: Any) -> bool:
    """A trader NPC tile (eid 'trader' or 'specialTrader').

    eid 'trader': one-shot gold->item traders (e.g. MT38 (5,2) 200G -> 3 yk).
    eid 'specialTrader': repeatable traders. MT28 (8,4) sells yellowKeys for
    gold (100G each); MT2 (11,7) is a +3% atk/def blessing handled elsewhere.
    The converter detects the transaction from the statlog delta, so a
    specialTrader whose delta does not match the floor's TRADER_TABLE entry
    (e.g. MT2 blessing) simply returns no purchase and is skipped.
    """
    if block is None or getattr(block, "kind", None) != "npc":
        return False
    return (block.eid or "") in ("trader", "specialTrader")


def _find_mt20_seed_stat(capture: dict[str, Any]) -> int | None:
    """Find the statlog index whose state matches the MT20 KILL seed.

    The seed save is the verified post-vampire state (HP=1215 at MT20 x6y5).
    In a flat statlog each entry is a pre-state, so the entry matching the seed
    is the stage-1 starting point (the next action runs FROM this state).
    """
    statlog = capture.get("statlog")
    if not isinstance(statlog, list):
        return None
    for idx, entry in enumerate(statlog):
        if not isinstance(entry, dict):
            continue
        if (entry.get("f") == MT20_KILL_EXPECTED["floor"]
                and entry.get("x") == MT20_KILL_EXPECTED["x"]
                and entry.get("y") == MT20_KILL_EXPECTED["y"]
                and entry.get("hp") == MT20_KILL_EXPECTED["hp"]
                and entry.get("g") == MT20_KILL_EXPECTED["gold"]):
            return idx
    return None


STAGE_STOP_FLOOR = {"mt20-mt31": "MT31", "mt31-mt40": "MT41", "mt41-mt50": None,
                    "mt4-mt31": None}  # zone1-3 full from MT4 save1 (e.g. 2攻买红钥匙线)


def _infer_pickaxe_target(g: Game, actions: list[SemanticAction],
                          ordinal: int) -> tuple[int, int] | None:
    """Infer the pickaxe target wall from the next action's direction.

    ``item:pickaxe`` doesn't encode which adjacent wall to break. The next
    action (move:X:Y target or arrow) reveals the direction the hero moves
    through the broken wall, so break the adjacent breakable wall in that
    direction. Used when a pickaxe use has 2+ adjacent breakable walls (e.g.
    MT48 (11,10) has (10,10) and (12,10) both yellowWall).
    """
    hx, hy = g.state["x"], g.state["y"]
    fid = g.state["floor"]
    directions = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}
    for nxt in actions[ordinal + 1:ordinal + 4]:
        ddx, ddy = 0, 0
        if nxt.kind == "target" and nxt.pos:
            ddx = nxt.pos[0] - hx
            ddy = nxt.pos[1] - hy
        elif nxt.kind == "arrow":
            d = nxt.data.get("direction")
            if d not in directions:
                continue
            ddx, ddy = directions[d]
        else:
            continue
        if ddx == 0 and ddy == 0:
            continue
        if abs(ddx) >= abs(ddy):
            dx, dy = (-1 if ddx < 0 else 1), 0
        else:
            dx, dy = 0, (-1 if ddy < 0 else 1)
        tx, ty = hx + dx, hy + dy
        block = g.block_at(fid, (tx, ty))
        if block and block.eid in WALL_IDS:
            return (tx, ty)
        return None
    return None


def _arrow_targets_stair(floors: dict[str, Any], action: SemanticAction, statlog: list[Any]) -> bool:
    """Whether this arrow press targets a stair tile: change_floor, or the
    enemy-on-stair composite (the knight hides the stair until killed)."""
    if action.kind != "arrow":
        return False
    d = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}.get(action.data.get("direction"))
    if d is None:
        return False
    si = action.data.get("stat_index")
    pre, _post = _statlog_states(statlog, si)
    if not isinstance(pre, dict):
        return False
    floor = floors.get(pre.get("f"))
    if floor is None:
        return False
    tx, ty = pre.get("x", 0) + d[0], pre.get("y", 0) + d[1]
    if f"{tx},{ty}" in (floor.change_floor or {}):
        return True
    return (pre.get("f"), tx, ty) in {(fid, x, y) for fid, (x, y), _eid in _ENEMY_ON_STAIR_TILES}


def _annotate_stair_turn_runs(actions: list[SemanticAction], statlog: list[Any],
                              floors: dict[str, Any]) -> None:
    """Mark the first arrow of a stair-bounce run whose parity implies a
    turn-only leading press (2026-08-31 41218).

    h5mota arrows are turn-then-move: after a fly landing the hero may face the
    wrong way, so the first press of a stair-bounce run only TURNS (no move, no
    floor transition) while the statlog's async sampling cannot distinguish it
    from an in-flight move (both show before==after). What IS reliable: the run's
    start floor (the first entry's before.f) and end floor (the last entry's
    after.f, sampled after the movement settled). The model executes one
    transition per arrow; if the arrow count's parity mismatches the recorded
    floor-change parity, the leading press was a turn -> annotate it so
    execute_action skips the whole press (no go_to, no transition).
    """
    directions = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}

    def is_stair_arrow(a: SemanticAction) -> bool:
        if a.kind != "arrow":
            return False
        si = a.data.get("stat_index")
        pre, _post = _statlog_states(statlog, si)
        if not isinstance(pre, dict):
            return False
        d = directions.get(a.data.get("direction"))
        if d is None:
            return False
        floor = floors.get(pre.get("f"))
        if floor is None:
            return False
        tx, ty = pre.get("x", 0) + d[0], pre.get("y", 0) + d[1]
        if f"{tx},{ty}" in (floor.change_floor or {}):
            return True
        # 敌人踩在楼梯块上（如 MT40 (6,1) yellowKnight on upFloor）：骑士死后
        # 楼梯显形（_after_action_impl 会补 change_floor），预扫描阶段按
        # ENEMY_ON_STAIR_TILES 识别为楼梯箭头。
        return (pre.get("f"), tx, ty) in {(fid, x, y) for fid, (x, y), _eid
                                          in _ENEMY_ON_STAIR_TILES}

    def stair_key(a: SemanticAction) -> tuple[str, str] | None:
        """Identify the stair pair this arrow bounces on: (pre-floor, stair tile).
        A run must stay on the SAME stair pair to be a bounce; a chain of
        transitions through DIFFERENT stairs (MT23->24->25->26->27, one real
        transition per arrow) is not a bounce and must not be turn-annotated."""
        si = a.data.get("stat_index")
        pre, _post = _statlog_states(statlog, si)
        if not isinstance(pre, dict):
            return None
        d = directions.get(a.data.get("direction"))
        if d is None:
            return None
        return (pre.get("f") or "", f"{pre.get('x', 0) + d[0]},{pre.get('y', 0) + d[1]}")

    i = 0
    n = len(actions)
    while i < n:
        if not is_stair_arrow(actions[i]):
            i += 1
            continue
        key0 = stair_key(actions[i])
        j = i
        while (j + 1 < n and is_stair_arrow(actions[j + 1])
               and stair_key(actions[j + 1]) == key0):
            j += 1
        run = actions[i:j + 1]
        # 2026-09-04 40145 定稿：同一楼梯对上的连按 run，statlog 异步采样无法
        # 逐 press 区分转向/移动中/换层完成（run 自身末样本也滞后）——可靠的
        # 末楼层 = run 后第一个非楼梯箭头动作的 pre.f（此时移动/换层已稳定）。
        # 净楼层变化 → 恰好一次换层：只保留最后一支箭头执行（go_to 顺路战斗/
        # 开门/踩骑士格），其余全部标 turn 跳过；未变 → 全部 turn。实证：40145
        # MT10 五连 right → MT11；41218 MT40 四连 up（骑士踩楼梯）→ MT41。
        si0 = run[0].data.get("stat_index")
        si1 = run[-1].data.get("stat_index")
        end_f = None
        # 2026-09-05 41200 修复：末楼层只采样 run 后第一个动作的 pre.f——
        # 旧扫描会跨过后续"不同楼梯对"的箭头（如 A->B 首访后紧接 B->A 回程），
        # 把回程的净变化归到本 run，导致 A->B（首访，load-bearing）被整 run
        # 标 turn 跳过、B 永不入 visited，后续 fly:B 全部失败（41200 MT47(1,1)
        # downFloor #3254 首访 MT48 -> #3629 fly:MT48 报 unvisited）。
        # run 内部同楼梯对连按的采样滞后仍由"取下一个动作 pre.f"解决（该动作
        # 已在 run 稳定后执行，floor 可靠）。
        if j + 1 < n:
            a2 = actions[j + 1]
            p2, _q2 = _statlog_states(statlog, a2.data.get("stat_index"))
            if isinstance(p2, dict) and p2.get("f"):
                end_f = p2.get("f")
        if end_f is None:
            _, post = _statlog_states(statlog, si1)
            if isinstance(post, dict):
                end_f = post.get("f")
        pre, _ = _statlog_states(statlog, si0)
        start_f = pre.get("f") if isinstance(pre, dict) else None

        def _press_moved(a: SemanticAction) -> bool:
            """该 press 相位是否观测到真实位移/换层（2026-09-05 41200 修复）。

            敌人踩楼梯复合格（MT40 (6,1) yellowKnight）：press 走上该格先战斗、
            不换层——pre/post 同楼层但位置变了。这种 press 是真实的（杀骑士+
            上格），绝不能标 turn 跳过；只有 pre==post 的相位才是转向/被吞
            候选。
            """
            p, q = _statlog_states(statlog, a.data.get("stat_index"))
            if not (isinstance(p, dict) and isinstance(q, dict)):
                return False
            if p.get("f") != q.get("f"):
                return True
            return (p.get("x"), p.get("y")) != (q.get("x"), q.get("y"))

        if start_f is not None and end_f is not None and start_f != end_f:
            for a in run[:-1]:
                if not _press_moved(a):
                    a.data["turn_first"] = True
        else:
            for a in run:
                if not _press_moved(a):
                    a.data["turn_first"] = True
        i = j + 1


def _transition_if_stair(g: Game, fid: str, pos: tuple[int, int],
                         block: Any, action: SemanticAction,
                         statlog: list[Any] | None = None) -> None:
    """Transition to the adjacent floor when the hero stepped onto a stair.

    ``go_to`` records "通过" on the stair tile but does not change floor; the
    real game transitions when the hero steps on the stair. The block is the
    pre-movement tile (stairs are not consumed), so it is still valid here.

    Destination comes from the changeFloor ``floorId`` (":next"/":before" or a
    specific "MTxx"), NOT the tile direction. ":next"/":before" skip hidden
    floors (HIDDEN_FLOORS, e.g. MT44) to match the game's findValidFloor --
    MT43 (1,11) upFloor with floorId=":next" lands on MT45, not MT44.
    """
    if block is not None and block.kind == "terrain" and block.eid in STAIRS:
        cf = g.floors[fid].change_floor.get(f"{pos[0]},{pos[1]}") or {}
        floor_id = cf.get("floorId")
        if floor_id == ":next":
            to_fid = next_floor(fid)
        elif floor_id == ":before":
            to_fid = prev_floor(fid)
        elif isinstance(floor_id, str) and floor_id.startswith("MT"):
            to_fid = floor_id
        else:
            # Fallback: tile direction, skipping hidden floors.
            to_fid = next_floor(fid) if block.eid == "upFloor" else prev_floor(fid)
        if g.state["floor"] == fid:
            # 2026-08-31 41218 修复：arrow = turn-then-move。楼梯弹跳 run 的首按键
            # 可能只是转向（fly 落地后朝向不符）——该 press 不移动不换层。run 级
            # 奇偶校验在 convert() 预扫描时给首箭头打 turn_first 标记（见
            # _annotate_stair_turn_runs），这里按标记跳过整次按键（不 go_to、
            # 不换层），使 run 的净楼层与录像一致。
            if action.data.get("turn_first"):
                return
            g.transition(to_fid, f"录像楼梯#{action.index} {fid}->{to_fid}")


def execute_target(g: Game, action: SemanticAction, diagnostics: list[dict[str, Any]],
                   statlog: list[Any] | None = None) -> bool:
    if not action.floor or action.pos is None:
        raise ValueError(f"target #{action.index} needs floor and pos")
    fid, pos = action.floor, action.pos
    if g.state["floor"] != fid:
        raise ValueError(
            f"target #{action.index} {fid} requires current floor {g.state['floor']}; "
            "capture must emit fly/transition explicitly"
        )
    block = g.block_at(fid, pos)
    # Shop NPC target (move:x:y onto a shop tile): if the statlog shows a
    # purchase delta, buy via the Game; otherwise treat as an approach waypoint
    # and stop adjacent (do not step onto the noPass NPC).
    if _is_shop_npc(block):
        statlog = statlog if statlog is not None else []
        purchase = _shop_purchase_from_delta(g, statlog, action.data.get("stat_index"))
        if purchase:
            return _execute_shop(g, fid, pos, purchase[0], purchase[1], action, diagnostics)
        g.move_adjacent(fid, pos[0], pos[1], f"录像商店目标#{action.index} 相邻")
        return True
    # Trader NPC target (move:x:y onto a trader tile): if the statlog shows the
    # trader transaction delta, talk_trader applies cost/gain (repeatable
    # specialTrader may be used `count` times under one arrow, e.g. MT28 sells
    # 2 yellowKeys for +200G); otherwise treat as an approach waypoint and stop
    # adjacent (do not step onto the noPass NPC).
    if _is_trader_npc(block):
        statlog = statlog if statlog is not None else []
        _cnt = _trader_purchase_from_delta(g, statlog, action.data.get("stat_index"))
        if _cnt:
            for _ in range(_cnt):
                g.talk_trader(fid, pos[0], pos[1], f"录像商人#{action.index}")
            return True
        # Mirror the arrow branch (L1018-1023): a specialTrader whose delta does
        # not match TRADER_TABLE (e.g. MT2 (11,7) +3% atk/def blessing) is a
        # passable event NPC, not a gold trade -- fire trigger_tile_event so a
        # target onto the tile behaves identically to the recording's arrow
        # step. Without this, a target (arrow-converted or capture target)
        # only moves adjacent and the event never fires.
        if _reach_event_trigger(g, fid, pos, action):
            return True
        g.move_adjacent(fid, pos[0], pos[1], f"录像商人目标#{action.index} 相邻")
        return True
    # Do not skip empty move:x:y waypoints: the hero must traverse them to
    # position adjacent to event triggers whose direct path is blocked (e.g.
    # MT29 (5,2) before stepping right to the (6,2) thief). go_to handles the
    # already-at-target no-op; a real click moves the hero through empty floor.
    go_to_decomposed(g, fid, *pos, f"录像语义目标#{action.index} {action.eid or ''}".strip())
    _transition_if_stair(g, fid, pos, block, action)
    return True


def _reach_event_trigger(g: Game, fid: str, pos: tuple[int, int],
                         action: SemanticAction) -> bool:
    """Reach a noPass event trigger (e.g. MT29 thief NPC) by standing adjacent
    and clicking the trigger tile.

    The real game lets the hero step onto the tile and fire the event; the
    shared Game model marks NPC blocks noPass, so go_to_decomposed cannot step
    onto them. Move adjacent, snapshot, run trigger_tile_event for the state
    mutation, then record an ``事件`` step at the trigger tile so the live
    verifier clicks it (firing the dialogue/event in the real game). The eid
    is captured before trigger_tile_event clears the block, so the verifier's
    side-effect-only special cases (e.g. MT29 thief) match by eid.
    """
    g.move_adjacent(fid, pos[0], pos[1], f"录像事件#{action.index} 相邻")
    block = g.block_at(fid, pos)
    eid = (block.eid if block else None) or action.eid or "event"
    before = g.snapshot()
    triggered = g.trigger_tile_event(fid, pos)
    # Only record an event step when the Game actually modeled the trigger.
    # A noPass NPC the Game has not modeled (e.g. an oldman/trader without a
    # trigger_tile_event branch) must not emit a side-effect-free event step --
    # the live verifier would click the NPC and fire its real dialogue, causing
    # a state mismatch. Returning False lets _safe_execute treat it as a noop.
    if triggered:
        _note = f"录像事件#{action.index} {action.eid or eid}".strip()
        # 2F 监狱小偷 (3,7)（41206）：hero 必须以「面向按键」触发（点击会
        # 产生 automaticRoute + 事件后 route-resume 乱走）。note 打
        # facing-trigger 标记，verifier 对该 事件 步改用方向键触发。
        if fid == "MT2" and pos == (3, 7):
            _note += " facing-trigger"
        g.record("事件", pos, eid, before, _note)
    return bool(triggered)


def _statlog_states(statlog: list[Any], stat_index: Any) -> tuple[Any, Any]:
    """Return (pre, post) hero states for a statlog entry.

    Handles both formats: flat rec1 (entry IS the pre-state, the next entry
    is the post-state) and wrapped (entry has {before, after}). Shop/trader
    delta detection uses this so it works on both native-replay captures
    (wrapped) and route-derived captures (flat).
    """
    if not isinstance(stat_index, int) or not (0 <= stat_index < len(statlog)):
        return None, None
    entry = statlog[stat_index]
    if not isinstance(entry, dict):
        return None, None
    if isinstance(entry.get("after"), dict):
        return entry.get("before"), entry.get("after")
    post = statlog[stat_index + 1] if stat_index + 1 < len(statlog) else {}
    return entry, post


def _shop_purchase_from_delta(g: Game, statlog: list[Any],
                              stat_index: Any) -> tuple[str, int] | None:
    """Detect a shop purchase from the recording's pre/post state delta.

    The recording encodes shop purchases (e.g. MT32 blueShop def x5 / atk x3)
    as direction arrows that step toward the shop NPC and open its dialog; the
    menu selection itself is not in the route tokens. The statlog's pre->post
    delta is the reliable signal: atk/def/hp increases while gold decreases by
    exactly the shop_cost sum. Returns (kind, count) validated against the
    Game's current times1, or None if the delta is not a clean shop purchase.
    """
    pre, post = _statlog_states(statlog, stat_index)
    if not isinstance(pre, dict) or not isinstance(post, dict):
        return None
    d_atk = (post.get("atk", 0) or 0) - (pre.get("atk", 0) or 0)
    d_def = (post.get("def", 0) or 0) - (pre.get("def", 0) or 0)
    d_hp = (post.get("hp", 0) or 0) - (pre.get("hp", 0) or 0)
    d_g = (post.get("g", 0) or 0) - (pre.get("g", 0) or 0)
    if d_g >= 0:
        return None  # a purchase must spend gold
    fid = g.state["floor"]
    ratio = g.floors[fid].ratio
    times1 = g.state["times1"]
    candidates: list[tuple[str, int]] = []
    if d_def > 0 and d_atk == 0 and d_def % (4 * ratio) == 0:
        candidates.append(("def", d_def // (4 * ratio)))
    if d_atk > 0 and d_def == 0 and d_atk % (2 * ratio) == 0:
        candidates.append(("atk", d_atk // (2 * ratio)))
    if d_hp > 0 and d_atk == 0 and d_def == 0:
        # HP shop gain = 100*(times1+1) per purchase, escalating with times1.
        cnt = 0
        remaining = d_hp
        t = times1
        while remaining > 0 and cnt < 99:
            gain = 100 * (t + 1)
            if remaining < gain:
                break
            remaining -= gain
            t += 1
            cnt += 1
        if cnt > 0 and remaining == 0:
            candidates.append(("hp", cnt))
    for kind, count in candidates:
        if count < 1:
            continue
        gold_used = sum(shop_cost(times1 + i) for i in range(count))
        if gold_used == -d_g:
            return (kind, count)
    return None


def _trader_purchase_from_delta(g: Game, statlog: list[Any],
                               stat_index: Any) -> int:
    """Detect a trader transaction; return the repeat count (0 = none).

    The recording triggers a trader (e.g. MT38 (5,2) 200G -> 3 yk) with an
    arrow toward the noPass trader NPC; the menu ``choices`` that confirms the
    purchase is not a hooked ``_doReplayAction`` token, so the -cost/+gain
    delta lands on that arrow's statlog entry (its ``after`` is the next hooked
    action's pre-state, i.e. post-choices). Return a count>0 when gold changes
    by a whole multiple of the current floor's trader cost and every
    stat-trackable gain (yk/bk/rk/hp) scales by that count.

    One-shot traders (TRADER_TABLE[floor]) have a fixed delta (count == 1).
    Repeatable reverse traders (specialTrader, e.g. MT28 sells yellowKeys for
    gold, 100G/key) can be used N times under one recording arrow, so the delta
    is N times the per-dialog exchange -- count == N and the caller repeats
    talk_trader N times. Earthquake (MT47, not in the statlog) is verified by
    gold cost alone.
    """
    pre, post = _statlog_states(statlog, stat_index)
    if not isinstance(pre, dict) or not isinstance(post, dict):
        return 0
    entry = g.TRADER_TABLE.get(floor_no(g.state["floor"]))
    if entry is None:
        return 0
    cost, gain, _eid = entry
    d_g = (post.get("g", 0) or 0) - (pre.get("g", 0) or 0)
    if cost != 0:
        if d_g % (-cost) != 0:
            return 0
        count = d_g // (-cost)
    else:
        count = 1
    if count < 1:
        return 0
    for key, val in gain.items():
        if key == "earthquake":
            continue
        if (post.get(key, 0) or 0) - (pre.get(key, 0) or 0) != val * count:
            return 0
    return count


def _execute_shop(g: Game, fid: str, shop_pos: tuple[int, int],
                  kind: str, count: int, action: SemanticAction,
                  diagnostics: list[dict[str, Any]]) -> bool:
    """Stand adjacent to the shop tile and buy `count` of `kind`.

    The hero is already at a passable tile adjacent to the shop (the recording's
    arrow stepped toward it); move_adjacent is a no-op then. buy_shop records
    one ``商店`` step per unit so the live replayer clicks the shop dialog once
    per purchase and selects the matching choice (atk/def/hp).
    """
    g.move_adjacent(fid, shop_pos[0], shop_pos[1], f"录像商店#{action.index} 相邻")
    g.buy_shop(kind, count, shop_pos=shop_pos)
    diagnostics.append({
        "recording_index": action.index, "kind": "shop",
        "classification": "shop_purchase_from_delta",
        "shop_kind": kind, "count": count, "pos": list(shop_pos),
    })
    return True


def _safe_execute(g: Game, action: SemanticAction, diagnostics: list[dict[str, Any]],
                  statlog: list[Any]) -> bool:
    """Execute one semantic action, treating pure recorder no-ops as non-fatal.

    An arrow onto a wall or an unreachable waypoint is a recorder facing input
    that produced no game effect. Route-derived arrows carry no statlog, so a
    RouteError here is logged and skipped rather than aborting the stage. A
    noPass event trigger (NPC) falls back to move_adjacent + trigger.
    """
    try:
        return execute_action(g, action, diagnostics, statlog)
    except RouteError as exc:
        if g.errors:
            g.errors.pop()
        # Fallback: if the target was an event trigger tile, the RouteError is
        # likely because the NPC is noPass. Reach it by standing adjacent.
        target_pos = action.pos
        if action.kind == "arrow":
            directions = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}
            direction = action.data.get("direction")
            if direction in directions:
                target_pos = (g.state["x"] + directions[direction][0],
                              g.state["y"] + directions[direction][1])
        if target_pos is not None and action.floor:
            fid = action.floor
        else:
            fid = g.state["floor"]
        # A noPass NPC (oldman/trader/thief) that the Game models as kind="npc"
        # (can_enter returns False) also reaches via move_adjacent + trigger.
        # Unlike shop NPCs (intercepted earlier in execute_action/execute_target
        # before go_to), these raise RouteError on go_to_decomposed and need the
        # same adjacent-trigger fallback as event-trigger tiles. is_event_trigger
        # only checks the floor events dict, which excludes NPCs whose trigger is
        # encoded in systemEvents/commonEvent (e.g. MT2 (11,4) oldman +1000G).
        is_npc_trigger = False
        if target_pos is not None and action.kind in ("target", "arrow"):
            _blk = g.block_at(fid, target_pos)
            is_npc_trigger = _blk is not None and _blk.kind == "npc"
        if (target_pos is not None and action.kind in ("target", "arrow")
                and (is_event_trigger(g, fid, target_pos) or is_npc_trigger)):
            blk = g.block_at(fid, target_pos)
            diagnostics.append({
                "recording_index": action.index, "kind": action.kind,
                "classification": "event_trigger_adjacent_fallback",
                "pos": list(target_pos),
                "block_eid": blk.eid if blk else None,
                "block_kind": blk.kind if blk else None,
                "floor_at_fallback": fid,
            })
            try:
                if _reach_event_trigger(g, fid, target_pos, action):
                    return True
            except RouteError as exc2:
                if g.errors:
                    g.errors.pop()
        diagnostics.append({
            "recording_index": action.index, "kind": action.kind,
            "classification": "noop_routeerror", "detail": str(exc),
        })
        return False


def execute_action(g: Game, action: SemanticAction,
                   diagnostics: list[dict[str, Any]],
                   statlog: list[Any] | None = None) -> bool:
    """Execute only named Game semantics; never correct state from recording."""
    statlog = statlog if statlog is not None else []
    kind = action.kind
    if kind == "arrow":
        directions = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}
        direction = action.data.get("direction")
        if direction not in directions:
            raise ValueError(f"arrow #{action.index} needs a valid direction")
        fid = g.state["floor"]
        dx, dy = directions[direction]
        pos = (g.state["x"] + dx, g.state["y"] + dy)
        block = g.block_at(fid, pos)
        # Shop NPC (e.g. MT32 blueShop): the recording's arrow steps toward the
        # shop tile and the statlog delta reveals the purchase (atk/def/hp up,
        # gold down by shop_cost). Buy via the Game instead of stepping onto the
        # noPass NPC. An arrow with no purchase delta just opens the dialog / is
        # a recorder turn -- skip it; the replayer's shop step opens the dialog
        # when the purchase step runs.
        if _is_shop_npc(block):
            purchase = _shop_purchase_from_delta(g, statlog, action.data.get("stat_index"))
            if purchase:
                return _execute_shop(g, fid, pos, purchase[0], purchase[1], action, diagnostics)
            diagnostics.append({
                "recording_index": action.index, "kind": "arrow",
                "classification": "skipped_shop_npc_no_purchase",
                "direction": direction, "pos": list(pos),
            })
            return False
        # Trader NPC (e.g. MT38 (5,2) 200G -> 3 yk): the recording's arrow steps
        # toward the trader tile and the statlog delta reveals the transaction
        # (gold down by the trader cost, yk/bk/rk up by the gain). talk_trader
        # applies it instead of stepping onto the noPass NPC. An arrow with no
        # transaction delta just opens the dialog / is a recorder turn -- skip it;
        # the replayer's 商人 step opens the dialog when the purchase step runs.
        if _is_trader_npc(block):
            _cnt = _trader_purchase_from_delta(g, statlog, action.data.get("stat_index"))
            if _cnt:
                for _ in range(_cnt):
                    g.talk_trader(fid, pos[0], pos[1], f"录像商人#{action.index}")
                return True
            # A specialTrader whose delta does not match TRADER_TABLE (e.g. MT2
            # (11,7) +3% atk/def blessing) is a passable event NPC, not a gold
            # trade. Fire it via trigger_tile_event (only records an 事件 step if
            # the Game modeled it; otherwise _safe_execute treats it as a noop).
            if _reach_event_trigger(g, fid, pos, action):
                return True
            diagnostics.append({
                "recording_index": action.index, "kind": "arrow",
                "classification": "skipped_trader_npc_no_purchase",
                "direction": direction, "pos": list(pos),
            })
            return False
        # Princess (MT26 6,6) is noPass in live: the hero stops adjacent (e.g.
        # x5y6) and the rescue commonEvent fires on facing her. The recording
        # faces the princess via an arrow (turn-then-face, no stat change) --
        # fire talk_mt26_princess instead of stepping onto the noPass tile.
        if block and block.kind == "npc" and block.eid == "princess":
            if not g.flags.get("营救公主"):
                g.talk_mt26_princess()
                return True
            diagnostics.append({
                "recording_index": action.index, "kind": "arrow",
                "classification": "skipped_princess_already_rescued",
                "direction": direction, "pos": list(pos),
            })
            return False
        # Thief NPC (MT15 (9,1)/MT29 (6,2)/MT2 (10,11)/MT35 (5,10)): noPass in
        # live (cls=npcs default, trigger="action"). The recording faces the
        # thief via a turn-then-move arrow that produces NO movement (hero
        # stays adjacent -- e.g. MT29 (5,2) turns right toward (6,2), stays at
        # (5,2); MT15 (9,2) turns up toward (9,1), stays at (9,2)), and the
        # "action" event fires on facing (opens the 暗道 / sends the thief on).
        # Fire via _reach_event_trigger (move_adjacent + trigger_tile_event +
        # record 事件 at the thief tile) instead of stepping onto the noPass
        # tile. The verifier then clicks the thief tile: the live hero stops
        # adjacent (noPass), the dialogue fires, matching the recording. (MT10
        # (6,9) is an empty step-on floor-event tile, not a thief block, so the
        # general go_to_decomposed path below handles it.)
        if block and block.kind == "npc" and block.eid == "thief":
            return _reach_event_trigger(g, fid, pos, action)
        # h5mota arrow = turn-then-move: if the adjacent tile is passable (empty
        # ground / stair / item), the hero MOVES there; only a blocked tile (wall
        # / closed door / noPass NPC) is a pure turn. Do NOT skip empty tiles --
        # the recording uses arrow keys for walking (e.g. the MT19->MT8 flyback),
        # and skipping those moves desyncs the hero's position. go_to_decomposed
        # moves onto passable tiles, opens doors, and battles monsters on the
        # path; a wall/noPass NPC raises RouteError, caught by _safe_execute as a
        # non-fatal noop (a recorder turn that produced no game effect).
        if action.data.get("turn_first"):
            # 楼梯弹跳 run 的首按键是纯转向（run 级奇偶校验标注）：不移动、
            # 不换层，hero 原地面向新方向。
            diagnostics.append({
                "recording_index": action.index, "kind": "arrow",
                "classification": "skipped_stair_turn_only",
                "direction": direction, "pos": list(pos),
            })
            return False
        go_to_decomposed(g, fid, pos[0], pos[1], f"录像方向#{action.index} {direction}")
        _transition_if_stair(g, fid, pos, block, action, statlog)
        return True
    if kind == "target":
        return execute_target(g, action, diagnostics, statlog)
    if kind == "fly":
        if not action.floor:
            raise ValueError(f"fly #{action.index} needs floor")
        g.fly(action.floor)
        return True
    if kind == "transition":
        if not action.floor or action.pos is None:
            raise ValueError(f"transition #{action.index} needs destination floor and stair pos")
        g.change_by_stair(action.floor, action.pos[0], action.pos[1], f"录像换层#{action.index}")
        return True
    if kind == "shop":
        if not action.floor or action.pos is None:
            raise ValueError(f"shop #{action.index} needs floor and shop pos")
        shop_kind = action.data.get("shop_kind")
        count = action.data.get("count", 1)
        if shop_kind not in {"atk", "def", "hp"} or not isinstance(count, int) or count < 1:
            raise ValueError(f"shop #{action.index} needs shop_kind=atk|def|hp and positive count")
        if g.state["floor"] != action.floor:
            raise ValueError(f"shop #{action.index} on wrong floor")
        g.move_adjacent(action.floor, *action.pos, f"录像商店#{action.index}")
        g.buy_shop(shop_kind, count, shop_pos=action.pos)
        return True
    if kind == "trader":
        if not action.floor or action.pos is None:
            raise ValueError(f"trader #{action.index} needs floor and npc pos")
        if g.state["floor"] != action.floor:
            raise ValueError(f"trader #{action.index} on wrong floor")
        g.talk_trader(action.floor, *action.pos, f"录像商人#{action.index}")
        return True
    if kind == "event":
        # Floor-trigger events are modeled in Game.trigger_tile_event by
        # (floor, pos) -- no zone-specific subclass methods. Explicit "event"
        # semantic actions (rare; statlog derivation does not emit them) just
        # re-trigger the tile event at the recorded position.
        if not action.floor or action.pos is None:
            raise ValueError(f"event #{action.index} needs floor and pos")
        triggered = g.trigger_tile_event(action.floor, action.pos)
        if not triggered:
            diagnostics.append({
                "recording_index": action.index, "kind": "event",
                "classification": "event_not_modeled", "pos": list(action.pos or []),
            })
        return bool(triggered)
    if kind == "tool":
        tool = action.data.get("tool")
        if tool == "centerFly":
            g.center_fly(f"录像工具#{action.index}")
        elif tool == "upFly":
            g.up_fly(f"录像工具#{action.index}")
        elif tool == "downFly":
            g.down_fly(f"录像工具#{action.index}")
        elif tool == "bigKey":
            g.use_big_key(f"录像工具#{action.index}")
        elif tool == "earthquake":
            g.use_earthquake(f"录像工具#{action.index}")
        elif tool == "bomb":
            g.use_bomb(f"录像工具#{action.index}")
        elif tool == "superPotion":
            g.use_super_potion(f"录像工具#{action.index}")
        elif tool == "pickaxe":
            if action.floor and action.pos is not None:
                g.use_pickaxe(action.floor, *action.pos, f"录像工具#{action.index}")
            else:
                # Recordings emit item:pickaxe without a target tile; auto-find
                # the unique adjacent breakable wall (the hero faces it).
                g.use_pickaxe_adjacent(f"录像工具#{action.index} 自动目标")
        else:
            raise ValueError(f"unknown/underspecified tool #{action.index}: {tool!r}")
        return True
    if kind == "set_auto":
        # 游戏说明 -> 自动操作 menu interaction recorded as help+choices. Apply
        # the toggles to the Game's current auto state; record a verifier-visible
        # 设置自动 step ONLY when the state actually changes (a redundant help
        # that re-sets the current state, or a bare help+choices:6 open/close,
        # is a no-op and emits no step -- matching the recording's net effect).
        choices = action.data.get("choices") or []
        new_auto = _apply_set_auto_toggles(g.auto_flags, choices)
        cur = {k: g.auto_flags.get(k, False) for k in AUTO_KEYS}
        if new_auto == cur:
            return False
        g.set_auto(f"录像SET_AUTO#{action.index} via 游戏说明 menu", **new_auto)
        return True
    raise ValueError(f"unknown semantic action #{action.index}: {kind!r}")


# 3F 魔王布阵监狱三格（41206）：布阵剧情传送 MT2 (3,8) 后，出狱点击
# (1,8)/(1,10) 为瞬移（statlog 19-22 位移实证），详见 convert 内 jail-jump。
_MT2_JAIL_TILES = {(3, 8), (1, 8), (1, 10)}
_ARROW_DIRS = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}


# 3F 魔王布阵监狱（41206）：小偷驻留 (1,9) 挡 col-1 出狱路，hero 的点击
# (1,8)/(1,10) 靠 live moveDirectly 瞬移过它（statlog 19-22 位移实证），
# 详见 convert 内 jail-jump 特例。
_MT2_JAIL_TILES = {(3, 8), (1, 8), (1, 10)}
_ARROW_DIRS = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}


def _coalesce_redundant_arrivals(steps: list[dict[str, Any]],
                                 event_positions: set[tuple[str, int, int]] | None = None,
                                 floors: dict[str, Any] | None = None
                                 ) -> list[dict[str, Any]]:
    """Drop ALL 到达/通过 positioning steps that had no map effect.

    The Game class is a reachability matrix: each step goes directly to a
    meaningful click target (door / kill / pickup / event / stair / fly).
    Empty-ground ``move:x:y`` tokens in the recording only walk the hero
    across floor; they are not reachability-matrix states, so their 到达/通过
    steps are redundant noise. The live replayer clicks the *target* directly
    -- a far click automaticRoutes the hero there and, via
    ``maybeRetryAdjacentTarget`` / the far-KILL branch, re-clicks once if the
    first click only routed the hero adjacent (closed door / enemy not yet
    engaged). So no pre-positioning 到达 step is needed before a meaningful
    action; the replayer routes from wherever the hero currently stands.

    Cross-floor movement is flown explicitly (飞行器中转), never walked.

    Kept (never removed):
    - stat-changing steps (kills, pickups, doors, events, shops, ...).
    - auto_sweep steps: even with unchanged stats they broke walls / opened
      paths, so the map effect is load-bearing for later reachability.
    - stair clicks (eid upFloor/downFloor) and any step immediately followed
      by 换层: the replayer pairs 通过-stair + 换层 and the stair click must
      stay so the floor transition fires.
    - 到达/通过 on a floor-event trigger tile (e.g. MT40 (6,7) boss event):
      may show before==after (spawns rewards / opens doors without a stat
      change this step) but is load-bearing -- skipping it means the event
      never fires.
    - 到达/通过 immediately before a position-dependent fly tool
      (中心飞行 centerFly / 上楼器 upFly / 下楼器 downFly): these fly the
      hero to a destination computed from the CURRENT position (centerFly =
      center-symmetric tile; upFly/downFly = same x,y on the adjacent floor).
      The fly step's pos was computed assuming the hero stands here, so the
      positioning step must stay (e.g. MT40 centerFly from (10,11)->(2,1);
      from (9,9) the symmetric (3,3) is blocked and the fly fails).
    - 到达/通过 immediately before the MT50 redKing reveal EVENT step: the
      verifier reveals redKing via a KEYBOARD trigger that requires the hero
      already adjacent to (6,5) (tiles (5,5)/(6,6)/(6,4)/(7,5)); it does NOT
      route the hero to the event tile. The recording's positioning move
      (``move:5:5`` from the 换层 landing (6,7) -> (5,5)) is a plain empty-
      ground walk that coalesce would otherwise drop, leaving the hero at
      (6,7) non-adjacent and the reveal throwing "must be adjacent". This is
      a documented game boundary (same as 38624/39003/39529/39944): keep the
      positioning 到达 so the hero physically stands adjacent before the
      keyboard reveal. (The redKing *kill* 击杀 is a meaningful action the
      replayer routes to directly, so it needs no positioning step.)
    - 到达/通过 immediately before an 开门, standing adjacent to the door
      (is_door_approach): the recording opened the door with an adjacent
      arrow (hero stays, no auto sweep). Dropping the approach makes the
      replayer click the door from farther back, and live automaticRoute
      walks the hero THROUGH the just-opened door + sweeps the freshly
      reachable pocket behind it, consuming items the walk schedules later.
    """
    # Value fields the live verifier compares every step. A positioning step is
    # redundant (droppable) only when ALL of these are unchanged -- plus the tool
    # counts below, which capture real pickups the replayer must click (e.g. MT15
    # octopus -> pickaxe at x6y5, swept silently by the pending-after-battle sweep
    # with no stat change in hp/atk/def/keys/gold). Without the tool counts, that
    # 到达 step looks stat_same and gets folded into the next fly step, so the web
    # replayer never clicks x6y5 and the pickaxe is never picked up (MT48 use
    # fails). Tool count changes are always load-bearing (a pickup), so keeping
    # such a step is always correct.
    value_fields = ("hp", "atk", "def", "yk", "bk", "rk", "gold")
    tool_fields = ("pickaxe", "centerFly", "upFly", "downFly", "bomb",
                   "earthquake", "bigKey", "superPotion", "snow")
    positioning = {"到达", "通过"}
    # Actions whose effect is a function of the hero's current tile: the
    # pre-positioning 到达/通过 before them is load-bearing. The live replayer
    # does NOT move the hero for these (it fires the tool in place), so the
    # hero must already stand at the recorded pos via an explicit step.
    #   - Fly tools (centerFly/upFly/downFly): destination computed from pos.
    #   - 炸弹 bomb / 使用镐 pickaxe: affect the 4 tiles adjacent to the hero,
    #     so the hero must be at the recorded pos or the wrong tiles break.
    # 地震卷轴 earthquake is global (opens all breakable walls on the floor)
    # and does NOT depend on the hero's tile, so it is excluded.
    position_dependent_fly = {"中心飞行", "上楼器", "下楼器", "炸弹", "使用镐"}
    out: list[dict[str, Any]] = []
    for i, s in enumerate(steps):
        before = s.get("before", {}) or {}
        after = s.get("after", {}) or {}
        action = s.get("action", "")
        note = s.get("note", "") or ""
        next_action = steps[i + 1].get("action", "") if i + 1 < len(steps) else ""
        stat_same = all(before.get(k) == after.get(k) for k in value_fields)
        stat_same = stat_same and all(before.get(k) == after.get(k) for k in tool_fields)
        same_floor = before.get("floor") == after.get("floor")
        is_positioning = action in positioning
        has_auto = "auto_sweep" in note
        # A positioning 到达/通过 immediately before a 击杀 whose pos differs
        # from the kill target is load-bearing: the recording *routed the hero to
        # a separate approach tile* (e.g. MT5 bat at (3,3) reached by clicking
        # (3,2) then stepping down). The live verifier clicks each walk step's
        # target as one click; collapsing the approach into a single far 击杀
        # click at the enemy tile makes the game's automaticRoute re-route the
        # hero from its current tile, which can differ from the recording's
        # approach (Game's go_to item-epsilon picks a different door/path) and
        # diverge (opens (2,3) door yk6->5, stalls at (1,3)). The hero must
        # physically stand at the recorded approach tile first, exactly like the
        # position-dependent fly tools / redKing reveal kept below. Only fire
        # when the preceding positioning is on the SAME floor and moves onto a
        # tile adjacent to the kill target (a real approach), not a same-tile
        # noop or a cross-floor step.
        _ns = steps[i + 1] if i + 1 < len(steps) else {}
        _npos = _ns.get("pos") or []
        pos = s.get("pos") or []
        is_kill_approach = (
            next_action == "击杀"
            and same_floor
            and len(pos) == 2 and len(_npos) == 2
            and pos != _npos
            and abs(pos[0] - _npos[0]) + abs(pos[1] - _npos[1]) == 1
        )
        # Door-open approach (2026-08-30 41200 录像修复): a positioning 到达/
        # 通过 immediately before an 开门 whose pos differs from the door tile
        # is load-bearing when it stands adjacent to the door. The recording
        # opened the door with an ADJACENT arrow (hero stays on the approach
        # tile, no auto sweep -- Game 开门 model). If coalesce drops the
        # approach, the replayer's click on the door pos happens from FARTHER
        # back (previous kept step's after pos), and live automaticRoute walks
        # the hero THROUGH the just-opened door onto the door tile, then the
        # idle move triggers auto sweep which remotely collects the freshly
        # reachable pocket behind the door -- items the walk schedules later
        # (41200 MT47: 到达 (8,3) dropped, click (8,4) from (8,1) walked hero
        # to (8,4), auto sweep grabbed x8y6 yellowKey + x9y5 brownWizard that
        # the walk emits at step 1022 -> per-step value mismatch). Keeping the
        # adjacent approach makes live an adjacent door click (hero stays, no
        # sweep -- MT4/MT47 adjacent-click evidence), matching the Game model.
        is_door_approach = (
            next_action == "开门"
            and same_floor
            and len(pos) == 2 and len(_npos) == 2
            and pos != _npos
            and abs(pos[0] - _npos[0]) + abs(pos[1] - _npos[1]) == 1
        )
        is_stair = s.get("eid") in STAIRS
        before_transition = next_action == "换层"
        before_position_fly = next_action in position_dependent_fly
        next_step = steps[i + 1] if i + 1 < len(steps) else {}
        # MT50 redKing reveal is a keyboard-trigger EVENT requiring the hero to
        # already stand adjacent to (6,5); the verifier does not route the hero
        # there, so the recording's positioning 到达 must survive coalesce.
        before_redking_reveal = (
            next_step.get("action") == "事件"
            and next_step.get("eid") == "redKing"
            and next_step.get("floor") == "MT50"
        )
        # facing-trigger 事件（MT2 越狱小偷 farewell 等）由 verifier 用方向键
        # 触发、不路由 hero，要求 hero 已相邻站立：其前的 positioning 到达 步
        # 必须保留（同 redKing reveal 保留逻辑）。
        before_facing_event = (
            next_step.get("action") == "事件"
            and "facing-trigger" in str(next_step.get("note") or "")
        )
        is_event_tile = (event_positions is not None and len(pos) == 2
                         and (before.get("floor"), pos[0], pos[1]) in event_positions)
        # MT2 (1,9) 越狱小偷 farewell 格（41206 实证 step15 timeout）：该格
        # click = NPC 相邻交互（hero 不进入，告别对话后小偷 hide），而录像只会
        # moveDirectly 越过它（statlog 21 move:1:10 实证）。positioning 步以
        # (1,9) 为点击目标时 verifier 停在 (1,8) 永不匹配——is_event_tile 的
        # 保留例外对此格不适用，强制按普通零效果步删除。
        is_jail_thief_tile = (
            before.get("floor") == "MT2" and len(pos) == 2
            and pos[0] == 1 and pos[1] == 9
        )
        if is_jail_thief_tile:
            is_event_tile = False
        # Fire tile (fgmap 103): the hero must moveOneStep onto fire (automaticRoute
        # cannot route onto/through fire), so the live verifier uses an arrow key for
        # the last step. A fire-tile ARRIVE/通过 is load-bearing even when stat_same
        # (no pickup): dropping it merges the fire step into the next click, which
        # then cannot route through the fire (e.g. MT47 (1,8) before the (1,9)
        # redWizard kill). The Game marks these steps with "火格" in the note (the
        # fgmap fire is cleared by the redWizard retreat, so checking fg_at after
        # simulation would miss them).
        is_fire_tile = "火格" in note
        # Flower tile (e.g. MT38 (2,5) / MT33 (8,10)): live auto BFS cannot expand
        # out of a flower tile (2026-09-07 9222 manual core.auto() on (2,5) picked
        # nothing), so the shield3-style pickup behind the flower must be reached
        # by an explicit click sequence. Dropping the flower arrival merges it into
        # a far click whose long automaticRoute stops early (hero stuck at (2,1)
        # on the y1 corridor, shield3 never picked -- combo16 live verify step762).
        # Keep flower-tile positioning steps so the replayer clicks the flower
        # itself, then the next target from the flower's exit side.
        is_flower_tile = s.get("eid") == "flower"
        if (is_positioning and stat_same and same_floor and not has_auto
                and not is_stair and not before_transition
                and not is_event_tile
                and not before_position_fly
                and not before_redking_reveal
                and not before_facing_event
                and not is_fire_tile
                and not is_flower_tile
                and not is_kill_approach
                and not is_door_approach):
            continue
        out.append(s)
    return out


def convert(seed: dict[str, Any], capture: dict[str, Any], actions: list[SemanticAction],
            stage: str, seed_path: Path, capture_path: Path,
            start_stat: int | None, auto_spec: str = "battle=false,item=false,wall=false",
            stop_floor: str | None = None) -> dict[str, Any]:
    validate_seed_snapshot(seed, stage)
    g = Game(seed)
    g.strict_live_model = True
    g.set_segment(f"录像语义 seed {stage}")
    # auto_spec is the SEED auto base (the recording's source-save state), NOT
    # the walk's net auto. Recordings captured from a fresh save1 slot start
    # auto-OFF: the first 游戏说明 -> 自动操作 help+choices (录像SET_AUTO#55)
    # TOGGLES battle/item/wall ON. So the default base for slot1 recordings is
    # all-false, and the recording's own help/choices toggles then drive the
    # auto state (matching the verified 38624/39003/V1 walks: seed step0
    # all-false -> step1 all-true). Hardcoding a non-false base here (e.g.
    # item=nopotion) made the first help toggle auto to all-false instead of
    # on, so auto_sweep picked nothing, MT5 keys stayed un-picked, the yellow
    # door stayed shut, and conversion blocked at MT5->MT6 (2026-08-14).
    # Zone4 (mt41-mt50) recordings start from a later save whose base is
    # item=nopotion -- pass auto_spec="battle=true,item=nopotion,wall=true"
    # explicitly for those.
    _af: dict[str, Any] = {}
    for _part in auto_spec.split(","):
        _k, _, _v = _part.strip().partition("=")
        if _k:
            _af[_k] = (True if _v == "true" else False if _v == "false" else _v)
    g.set_auto("录像 seed auto", **_af)
    # 额外功能开关（41206 实证 2026-09-13）：此类录像靠开场 choices 开启 gate，
    # seed 捕获点不可见（save210 flags 无 额外功能开关/I333）。判据 = route 中
    # 出现 help + choices:N(N>=4)：gate 关闭时 游戏说明 主菜单只有 7 项
    # （index 4=交易统计），gate 开启时 index 4=自动操作——录像走 自动操作
    # 菜单（SET_AUTO）本身就是 gate 已开启的证据。MT29 小偷暗道分支
    # （29层小偷可以直接通过）依赖此 flag：误 False 会把 (6,3) 暗道保持
    # unbreakableWall，go_to MT29 (5,11) RouteError -> 楼梯 run 静默锚定
    # 传送吞掉显式换层步（verifier 点不到 MT30）。
    _route_tokens = capture.get("route") or []
    for _ri, _rt in enumerate(_route_tokens):
        if str(_rt) == "help" and _ri + 1 < len(_route_tokens):
            _nx = str(_route_tokens[_ri + 1])
            if _nx.startswith("choices:") and int(_nx.split(":", 1)[1] or 0) >= 4:
                g.flags["额外功能开关"] = 1
                break
    actions = _stage_slice(actions, capture, stage, start_stat, stop_floor_override=stop_floor)
    statlog = capture.get("statlog") if isinstance(capture.get("statlog"), list) else []
    actions = _cancel_stair_bounce_arrows(actions, statlog, set(g.visited))
    # 2026-08-31 41218：楼梯弹跳 run 的转向首按键标注（run 级奇偶校验）。
    _annotate_stair_turn_runs(actions, statlog, g.floors)
    # Snapshot floor-event trigger tiles BEFORE execution: trigger_tile_event
    # removes the event from floor.events after firing (e.g. MT33 (10,5)
    # 骑士剑机关 close-door), so building the set after the loop would miss
    # already-consumed triggers and the coalesce would drop their 到达 step --
    # leaving the live replayer without the explicit trigger click and the
    # hero stuck routing through the event tile mid-route.
    event_positions: set[tuple[str, int, int]] = set()
    for fid, floor in g.floors.items():
        for loc in getattr(floor, "events", {}) or {}:
            try:
                sx, sy = loc.split(",")
                event_positions.add((fid, int(sx), int(sy)))
            except (ValueError, AttributeError):
                continue
    # Also keep load-bearing step-on triggers modeled in Game.trigger_tile_event
    # but NOT in floor.events (e.g. MT10 (6,5) boss spawn, MT20 (6,8) vampire
    # entrance). These have before==after (a map spawn, not a stat change), so
    # the coalesce would otherwise drop the 到达/通过 step -- the live verifier
    # then clicks past the trigger without firing it and the spawned boss/
    # monsters are absent (e.g. MT10 boss kills fail). TRIGGER_EVENT_DESC lists
    # exactly the (fid, pos) pairs that trigger_tile_event models.
    for (fid, tpos), _desc in getattr(Game, "TRIGGER_EVENT_DESC", {}).items():
        event_positions.add((fid, tpos[0], tpos[1]))
    diagnostics: list[dict[str, Any]] = []
    errors: list[str] = []
    executed = 0
    skipped = 0
    prev_stair_arrow = False

    for ordinal, action in enumerate(actions):
        # 2026-08-31 楼梯 run 净楼层锚定：连续楼梯箭头 run 结束时，模型按每箭头
        # 一次换层执行的净楼层在转向步/采样滞后下可能差奇偶（41218 MT40 四连 up、
        # 40145 MT10/11 链）。run 结束进入首个非楼梯动作时，把 hero floor/pos 锚定
        # 到录像观测值（该动作的 before 采样——此时移动已稳定）。floor/pos 是
        # verifier 容错字段；hp/atk/钥匙/金币仍全部由模型推导，绝不回写。
        is_stair_arrow = _arrow_targets_stair(g.floors, action, statlog)
        if prev_stair_arrow and not is_stair_arrow:
            si = action.data.get("stat_index")
            pre, _ = _statlog_states(statlog, si) if statlog else (None, None)
            if (isinstance(pre, dict) and pre.get("f")
                    and pre.get("f") != g.state["floor"]):
                diagnostics.append({
                    "classification": "stair_run_net_anchor",
                    "recording_index": action.index,
                    "model_floor": g.state["floor"],
                    "recorded_floor": pre.get("f"),
                })
                g.state["floor"] = pre.get("f")
                g.state["x"], g.state["y"] = pre.get("x"), pre.get("y")
                # 锚定换层 = hero 实际到过该层（2026-09-14 agentT2 发现：不更新
                # visited 会让后续合法 fly:MT39 误报 cannot fly to unvisited floor）。
                g.visited.add(pre.get("f"))
        prev_stair_arrow = is_stair_arrow
        # item:pickaxe has no target tile in the recording; infer the adjacent
        # breakable wall from the next action's direction (the hero breaks the
        # wall it then walks through). Falls back to use_pickaxe_adjacent.
        if (action.kind == "tool" and action.data.get("tool") == "pickaxe"
                and action.pos is None):
            target = _infer_pickaxe_target(g, actions, ordinal)
            if target is not None:
                action = SemanticAction(
                    index=action.index, kind=action.kind, floor=g.state["floor"],
                    pos=target, eid=action.eid, data=action.data)
        before_steps = len(g.steps)
        # 2026-09-08 41081：对话期吞键。live 原生回放中，事件对话框会吞掉路线缓冲
        # 里的方向键——statlog 样本 before==after 全状态无变化（位置+hp/atk/def/
        # yk/bk/rk/g）就是铁证。模型不能把它当真实移动执行：41081 在 MT24 公主通路
        # 对话框期录了 7 连 up，模型换层到 MT50 后把后续 up 当移动踩上刚 spawn 的
        # redKing 开打了未封印真魔王（dmg +28536）；末尾 (5,5) 的 right 连发也被当
        # 移动撞上 redKing。41231 同结构靠 hero 血量不足以存活该战、go_to
        # RouteError 巧合挡下。
        # 注意不能用「位置不变」单判据：转向开门键（如 4F (11,9) up 对 (11,8) 黄门，
        # 样本 diff=['yk']）无位移但承载开门，必须执行。
        # 例外（照常执行）：目标格是未触发的 step-on 事件（MT24 (6,2) 公主通路
        # changeFloor 这类吞键兼任换层触发），或目标格是 npc（MT29 小偷/26F 公主等
        # noPass NPC 的面向触发键）。
        if action.kind == "arrow":
            _pre, _post = _statlog_states(statlog, action.data.get("stat_index"))
            _STATE_KEYS = ("f", "x", "y", "hp", "atk", "def", "yk", "bk", "rk", "g")
            if (isinstance(_pre, dict) and isinstance(_post, dict)
                    and all(_pre.get(k) == _post.get(k) for k in _STATE_KEYS)):
                directions = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}
                _d = directions.get(action.data.get("direction"))
                _tx, _ty = g.state["x"] + (_d[0] if _d else 0), g.state["y"] + (_d[1] if _d else 0)
                _mfloor = g.floors.get(g.state["floor"])
                _blk = _mfloor.blocks.get((_tx, _ty)) if _mfloor else None
                _in_events = bool(_mfloor and f"{_tx},{_ty}" in (_mfloor.events or {}))
                _is_npc = bool(_blk and _blk.kind == "npc")
                if not _in_events and not _is_npc:
                    diagnostics.append({
                        "recording_index": action.index, "kind": "arrow",
                        "classification": "skipped_dialog_press_no_state_change",
                        "direction": action.data.get("direction"),
                        "model_floor": g.state["floor"],
                    })
                    skipped += 1
                    continue
        # 3F 魔王布阵监狱出狱（41206 实证 2026-09-13）：越狱后小偷驻留 (1,9)
        # （noPass，live runtime 实证），录像的 move:1:10 是小偷 walk 未完成时
        # 的时序运气 moveDirectly 点击，walk 不能依赖该时序。可复现结构 =
        # hero 到 (1,8) 后显式触发 (1,9) 告别事件（hero 停留、小偷 hide，
        # Game mt2_jail_farewell 分支），之后 (1,9) 永久通行，后续动作正常
        # 寻路（不再需要跳跃特例）。仅布阵剧情 flag 置位 + hero 相邻 (1,9)
        # + 小偷仍驻留时触发一次。
        if (g.flags.get("mt3_demon_arrange_story")
                and g.state.get("floor") == "MT2"
                and (g.state["x"], g.state["y"]) == (1, 8)
                and g.flags.get("mt2_jail_thief")
                and not g.flags.get("mt2_jail_farewell")
                and g.block_at("MT2", (1, 9)) is not None):
            _tb = g.block_at("MT2", (1, 9))
            _eid = (_tb.eid if _tb else None) or "thief"
            _before = g.snapshot()
            if g.trigger_tile_event("MT2", (1, 9)):
                g.record("事件", [1, 9], _eid, _before,
                         "布阵监狱小偷告别 facing-trigger")
                executed += 1
        try:
            did_execute = _safe_execute(g, action, diagnostics, statlog)
        except ValueError as exc:
            errors.append(f"recording action #{action.index}: {exc}")
            break
        if did_execute:
            executed += 1
        else:
            skipped += 1
        # Legality invariant: _safe_execute deliberately swallows RouteErrors
        # that are recorder no-ops (facing arrows), but battle death and
        # negative key counts fail AFTER mutating state -- swallowing those
        # leaves a dead/indebted hero that keeps walking (2026-08-18: a
        # skeleton-swap candidate died on MT42, hp went to -177, and the
        # special-16 hp//2 damage turned negative, hanging path_to). A route
        # whose hero is dead or holding a negative key is illegal at ANY action
        # boundary, so abort the conversion instead of continuing.
        if (g.state["hp"] <= 0 or g.state["yk"] < 0 or g.state["bk"] < 0
                or g.state["rk"] < 0):
            errors.append(
                f"recording action #{action.index}: illegal hero state after "
                f"swallowed RouteError: hp={g.state['hp']} "
                f"yk={g.state['yk']} bk={g.state['bk']} rk={g.state['rk']}")
            break
        stat_index = action.data.get("stat_index")
        observed = _post_state(statlog, stat_index)
        diag = stat_diagnostic(g, observed, action)
        if diag:
            diag["steps_emitted"] = len(g.steps) - before_steps
            diagnostics.append(diag)
        # After the MT42 (10,8) half-HP trap (hero steps between whiteKing
        # guards (9,8)/(11,8), HP halves), switch item=nopotion -> item=true:
        # there are no more half-HP traps after this point, and the recording
        # enables auto-potion around here (potions are then auto-swept, e.g.
        # the MT31 +200 redPotion pickup at #3572). Keep item=nopotion through
        # the trap itself so HP stays low (minimal halving loss, matching the
        # recording's hp 7->4). set_auto records a verifier-visible 设置自动 step.
        if (stage == "mt41-mt50" and g.auto_flags.get("item") is not True
                and isinstance(observed, dict)
                and observed.get("f") == "MT42"
                and observed.get("x") == 10 and observed.get("y") == 8):
            g.set_auto("MT42(10,8) 半血陷阱后：自动血瓶",
                       battle=True, item=True, wall=True)
        if g.errors:
            errors.extend(g.errors)
            break

    seed_start = {key: MT20_KILL_EXPECTED[key] for key in MT20_KILL_EXPECTED} if stage == "mt20-mt31" else g.snapshot()
    provenance = {
        "seed_save": str(seed_path), "seed_sha256": sha256_file(seed_path),
        "capture": str(capture_path), "capture_sha256": sha256_file(capture_path),
        "recording": capture.get("recording", {}), "stage": stage,
        # 2026-09-05 40145 教训：start_stat 决定从录像 statlog 哪里起转（40145 是
        # 1F 起点完整录像，须 --start-stat 284 匹配 MT4 seed）——不记进 provenance
        # 就无法复现/审计这条 walk 是从录像哪一段转出来的。
        "start_stat": start_stat, "stop_floor": stop_floor,
        # auto = 转换结束时的 auto flags(终态)；auto_spec = 本次转换的种子 auto base
        # (原样记录 --auto 参数)。下游(如 gen_recording_floor_breakdown)重放权威 Game
        # 必须用种子 base，不能用终态——slot1 录像终态全 true 而种子 base 全 false。
        "auto": dict(g.auto_flags), "auto_spec": auto_spec,
        "seed_state": seed_start,
    }
    raw_step_count = len(g.steps)
    coalesced_steps = _coalesce_redundant_arrivals(g.steps, event_positions, g.floors)
    return {
        "ok": not errors and not g.errors,
        "final": g.snapshot(), "steps": coalesced_steps,
        "errors": errors or g.errors,
        "diagnostics": diagnostics,
        "stats": {"semantic_actions": len(actions), "executed": executed, "skipped": skipped,
                  "steps_raw": raw_step_count, "steps_coalesced": len(coalesced_steps)},
        "provenance": provenance,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-save", required=True, type=Path)
    parser.add_argument("--capture", required=True, type=Path)
    parser.add_argument("--stage", required=True,
                        choices=("mt20-mt31", "mt31-mt40", "mt41-mt50", "mt4-mt31"))
    parser.add_argument("--start-stat", type=int, default=None,
                        help="statlog index matching the seed state (stage 1 default: MT20 KILL)")
    parser.add_argument("--auto", default="battle=false,item=false,wall=false",
                        help="seed auto base (recording's source-save state). slot1 recordings start auto-OFF "
                             "(all-false); the recording's first 游戏说明->自动操作 help+choices toggles it on. "
                             "zone4 (mt41-mt50) recordings start item=nopotion: pass "
                             "battle=true,item=nopotion,wall=true")
    parser.add_argument("--stop-floor", default=None,
                        help="override the stage's stop floor (e.g. MT41 to stop a mt4-mt31 full-route run before zone4)")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    capture, actions = load_capture(args.capture)
    start_stat = args.start_stat
    if start_stat is None and args.stage == "mt20-mt31":
        start_stat = _find_mt20_seed_stat(capture)
    result = convert(read_json(args.seed_save), capture, actions, args.stage,
                     args.seed_save, args.capture, start_stat, auto_spec=args.auto,
                     stop_floor=args.stop_floor)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": result["ok"], "final": result["final"],
                      "errors": result["errors"], "stats": result["stats"],
                      "diagnostics": len(result["diagnostics"])} , ensure_ascii=False))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
