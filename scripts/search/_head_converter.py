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
    STAIRS, RouteError, floor_no, go_to_decomposed, read_json, shop_cost,
)
from src.solver.game_route import Game

MT20_KILL_EXPECTED = {
    "floor": "MT20", "x": 6, "y": 5,
    "hp": 1215, "atk": 76, "def": 66,
    "yk": 5, "bk": 0, "rk": 0, "gold": 1298,
}
VALUE_FIELDS = ("hp", "atk", "def", "yk", "bk", "rk", "gold")


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
    directions = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}
    derived: list[dict[str, Any]] = []
    for index, item in enumerate(log):
        if not isinstance(item, dict):
            continue
        wrapped = isinstance(item.get("before"), dict)
        before = item["before"] if wrapped else item
        after = item.get("after") if wrapped else (log[index + 1] if index + 1 < len(log) else {})
        action = item.get("action") or before.get("action")
        if not isinstance(action, str):
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
        elif action.startswith("choices") or action in {"help", "turn"}:
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
                 stage: str, start_stat: int | None) -> list[SemanticAction]:
    """Bound the stage by the recording's own floor progression.

    The statlog's floor field is reliable evidence of where each action ran,
    even when its HP/gold drift. Stage 1 starts at the verified MT20 seed
    state and stops at the first action on MT31; stage 2 starts at MT31 and
    stops at MT41. ``start_stat`` is the statlog index matching the seed state.
    """
    stop_floor = STAGE_STOP_FLOOR[stage]
    if start_stat is not None:
        actions = [a for a in actions if a.data.get("stat_index", a.index) >= start_stat]
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
        if after.get("f") == stop_floor:
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
    # transition[i] = (from_floor, to_floor) for stair-step arrows, else None.
    transition: list[tuple[str, str] | None] = []
    for a in actions:
        if a.kind != "arrow":
            transition.append(None)
            continue
        si = a.data.get("stat_index")
        f_b = _statlog_floor(statlog, si, "before")
        f_a = _statlog_floor(statlog, si, "after")
        transition.append((f_b, f_a) if f_b and f_a and f_b != f_a else None)

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
        _from, to = t
        is_new_visit = to not in visited
        visited.add(to)
        if is_new_visit:
            # Load-bearing first visit: keep it, break the cancellation chain.
            stack = []
            continue
        if stack:
            top = stack[-1]
            top_t = transition[top]
            if top_t is not None and top_t[0] == to and top_t[1] == _from:
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
    """A trader NPC tile (eid 'trader'); e.g. MT38 (5,2) 200G -> 3 yk."""
    if block is None or getattr(block, "kind", None) != "npc":
        return False
    return (block.eid or "") == "trader"


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


STAGE_STOP_FLOOR = {"mt20-mt31": "MT31", "mt31-mt40": "MT41"}


def _transition_if_stair(g: Game, fid: str, pos: tuple[int, int],
                         block: Any, action: SemanticAction) -> None:
    """Transition to the adjacent floor when the hero stepped onto a stair.

    ``go_to`` records "通过" on the stair tile but does not change floor; the
    real game transitions when the hero steps on the stair. The block is the
    pre-movement tile (stairs are not consumed), so it is still valid here.
    """
    if block is not None and block.kind == "terrain" and block.eid in STAIRS:
        to_no = floor_no(fid) + (1 if block.eid == "upFloor" else -1)
        to_fid = f"MT{to_no}"
        if g.state["floor"] == fid:
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
    # trader transaction delta, talk_trader applies cost/gain; otherwise treat
    # as an approach waypoint and stop adjacent (do not step onto the noPass NPC).
    if _is_trader_npc(block):
        statlog = statlog if statlog is not None else []
        if _trader_purchase_from_delta(g, statlog, action.data.get("stat_index")):
            g.talk_trader(fid, pos[0], pos[1], f"录像商人#{action.index}")
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
        g.record("事件", pos, eid, before,
                 f"录像事件#{action.index} {action.eid or eid}".strip())
    return bool(triggered)


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
    if not isinstance(stat_index, int) or not (0 <= stat_index < len(statlog) - 1):
        return None
    pre = statlog[stat_index]
    post = statlog[stat_index + 1]
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
                               stat_index: Any) -> bool:
    """Detect a trader transaction from the recording's pre/post state delta.

    The recording triggers a trader (e.g. MT38 (5,2) 200G -> 3 yk) with an
    arrow toward the noPass trader NPC; the menu ``choices`` that confirms the
    purchase is not a hooked ``_doReplayAction`` token, so the -cost/+gain
    delta lands on that arrow's statlog entry (its ``after`` is the next hooked
    action's pre-state, i.e. post-choices). Return True when gold drops by
    exactly the current floor's trader cost and every stat-trackable gain
    (yk/bk/rk/hp) matches. Earthquake (MT47, not in the statlog) is verified
    by gold cost alone.
    """
    if not isinstance(stat_index, int) or not (0 <= stat_index < len(statlog) - 1):
        return False
    pre = statlog[stat_index]
    post = statlog[stat_index + 1]
    if not isinstance(pre, dict) or not isinstance(post, dict):
        return False
    entry = g.TRADER_TABLE.get(floor_no(g.state["floor"]))
    if entry is None:
        return False
    cost, gain, _eid = entry
    d_g = (post.get("g", 0) or 0) - (pre.get("g", 0) or 0)
    if d_g != -cost:
        return False
    for key, val in gain.items():
        if key == "earthquake":
            continue
        if (post.get(key, 0) or 0) - (pre.get(key, 0) or 0) != val:
            return False
    return True


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
            if _trader_purchase_from_delta(g, statlog, action.data.get("stat_index")):
                g.talk_trader(fid, pos[0], pos[1], f"录像商人#{action.index}")
                return True
            diagnostics.append({
                "recording_index": action.index, "kind": "arrow",
                "classification": "skipped_trader_npc_no_purchase",
                "direction": direction, "pos": list(pos),
            })
            return False
        # h5mota arrow = turn-then-move: if the adjacent tile is passable (empty
        # ground / stair / item), the hero MOVES there; only a blocked tile (wall
        # / closed door / noPass NPC) is a pure turn. Do NOT skip empty tiles --
        # the recording uses arrow keys for walking (e.g. the MT19->MT8 flyback),
        # and skipping those moves desyncs the hero's position. go_to_decomposed
        # moves onto passable tiles, opens doors, and battles monsters on the
        # path; a wall/noPass NPC raises RouteError, caught by _safe_execute as a
        # non-fatal noop (a recorder turn that produced no game effect).
        go_to_decomposed(g, fid, pos[0], pos[1], f"录像方向#{action.index} {direction}")
        _transition_if_stair(g, fid, pos, block, action)
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
        elif tool == "pickaxe":
            if not action.floor or action.pos is None:
                raise ValueError(f"pickaxe #{action.index} needs floor and target pos")
            g.use_pickaxe(action.floor, *action.pos, f"录像工具#{action.index}")
        else:
            raise ValueError(f"unknown/underspecified tool #{action.index}: {tool!r}")
        return True
    raise ValueError(f"unknown semantic action #{action.index}: {kind!r}")


def _coalesce_redundant_arrivals(steps: list[dict[str, Any]],
                                 event_positions: set[tuple[str, int, int]] | None = None
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
    """
    value_fields = ("hp", "atk", "def", "yk", "bk", "rk", "gold")
    positioning = {"到达", "通过"}
    # Fly tools whose destination is a function of the hero's current tile:
    # the pre-positioning 到达/通过 before them is load-bearing.
    position_dependent_fly = {"中心飞行", "上楼器", "下楼器"}
    out: list[dict[str, Any]] = []
    for i, s in enumerate(steps):
        before = s.get("before", {}) or {}
        after = s.get("after", {}) or {}
        action = s.get("action", "")
        note = s.get("note", "") or ""
        next_action = steps[i + 1].get("action", "") if i + 1 < len(steps) else ""
        stat_same = all(before.get(k) == after.get(k) for k in value_fields)
        same_floor = before.get("floor") == after.get("floor")
        is_positioning = action in positioning
        has_auto = "auto_sweep" in note
        is_stair = s.get("eid") in STAIRS
        before_transition = next_action == "换层"
        before_position_fly = next_action in position_dependent_fly
        pos = s.get("pos") or []
        is_event_tile = (event_positions is not None and len(pos) == 2
                         and (before.get("floor"), pos[0], pos[1]) in event_positions)
        if (is_positioning and stat_same and same_floor and not has_auto
                and not is_stair and not before_transition
                and not is_event_tile
                and not before_position_fly):
            continue
        out.append(s)
    return out


def convert(seed: dict[str, Any], capture: dict[str, Any], actions: list[SemanticAction],
            stage: str, seed_path: Path, capture_path: Path,
            start_stat: int | None) -> dict[str, Any]:
    validate_seed_snapshot(seed, stage)
    g = Game(seed)
    g.strict_live_model = True
    g.set_segment(f"录像语义 seed {stage}")
    g.set_auto("三区录像 seed：保留血瓶", battle=True, item="nopotion", wall=True)
    actions = _stage_slice(actions, capture, stage, start_stat)
    statlog = capture.get("statlog") if isinstance(capture.get("statlog"), list) else []
    actions = _cancel_stair_bounce_arrows(actions, statlog, set(g.visited))
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
    diagnostics: list[dict[str, Any]] = []
    errors: list[str] = []
    executed = 0
    skipped = 0

    for ordinal, action in enumerate(actions):
        before_steps = len(g.steps)
        try:
            did_execute = _safe_execute(g, action, diagnostics, statlog)
        except ValueError as exc:
            errors.append(f"recording action #{action.index}: {exc}")
            break
        if did_execute:
            executed += 1
        else:
            skipped += 1
        stat_index = action.data.get("stat_index")
        observed = _post_state(statlog, stat_index)
        diag = stat_diagnostic(g, observed, action)
        if diag:
            diag["steps_emitted"] = len(g.steps) - before_steps
            diagnostics.append(diag)
        if g.errors:
            errors.extend(g.errors)
            break

    seed_start = {key: MT20_KILL_EXPECTED[key] for key in MT20_KILL_EXPECTED} if stage == "mt20-mt31" else g.snapshot()
    provenance = {
        "seed_save": str(seed_path), "seed_sha256": sha256_file(seed_path),
        "capture": str(capture_path), "capture_sha256": sha256_file(capture_path),
        "recording": capture.get("recording", {}), "stage": stage,
        "auto": dict(g.auto_flags),
        "seed_state": seed_start,
    }
    raw_step_count = len(g.steps)
    coalesced_steps = _coalesce_redundant_arrivals(g.steps, event_positions)
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
    parser.add_argument("--stage", required=True, choices=("mt20-mt31", "mt31-mt40"))
    parser.add_argument("--start-stat", type=int, default=None,
                        help="statlog index matching the seed state (stage 1 default: MT20 KILL)")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    capture, actions = load_capture(args.capture)
    start_stat = args.start_stat
    if start_stat is None and args.stage == "mt20-mt31":
        start_stat = _find_mt20_seed_stat(capture)
    result = convert(read_json(args.seed_save), capture, actions, args.stage,
                     args.seed_save, args.capture, start_stat)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": result["ok"], "final": result["final"],
                      "errors": result["errors"], "stats": result["stats"],
                      "diagnostics": len(result["diagnostics"])} , ensure_ascii=False))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
