#!/usr/bin/env python3
"""Audit merchant-aware 4F-9F resource paths and gold-adjusted stock scores.

This is intentionally an isolated experiment.  The main floor search does not
model money, so this script layers money accounting around existing replayed
floor actions and treats merchant purchases as explicit opt-in actions.
"""

from __future__ import annotations

import argparse
import heapq
import json
import os
import sys
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any, Callable, Iterable


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.chdir(ROOT)

try:
    from scripts import replay_user_post9_route as guide
except ImportError:  # Running as a script from scripts/ keeps that directory on sys.path.
    import replay_user_post9_route as guide
from scripts import fixed_shield_strategy as fixed
from scripts import phase1_action_search as p1
from scripts import post9_resource_group_search as rg
from src.solver import gen_walkthrough as gw
from src.solver.full_search import calc_dmg


OUT_JSON = os.path.join("outputs", "results", "merchant_resource_path_compare.json")
OUT_MD = os.path.join("outputs", "reports", "merchant_resource_path_compare.md")

GOLD_VALUE_PER_100 = 50
DEFAULT_START_GOLD = 7

# Values verified from h5mota `core.material.enemys[*].money` on the loaded
# 4F save.  The local map JSON only carries block ids/classes, so keep this
# visible and auditable in the output rather than hiding it in search.
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

SPAWNED_BOSS_MONSTERS = (
    "skeletonSoldier",
    "skeletonSoldier",
    "skeleton",
    "skeleton",
    "skeleton",
    "skeleton",
    "skeleton",
    "skeleton",
    "skeletonCaptain",
)

MONSTER_EIDS = set(ENEMY_GOLD)
BOSS_EVENT_MAP_MONSTER = ("MT10", (6, 4), "skeletonCaptain")
_FUTURE_BREAKDOWN_CACHE: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
_FUTURE_FLOOR_CACHE: dict[tuple[Any, ...], dict[str, Any] | None] = {}


@dataclass(frozen=True)
class Merchant:
    key: str
    fid: str
    pos: tuple[int, int]
    spend_gold: int
    yk_gain: int = 0
    bk_gain: int = 0

    @property
    def action_eid(self) -> str:
        return f"merchant:{self.key}"

    @property
    def label(self) -> str:
        gain = []
        if self.yk_gain:
            gain.append(f"+{self.yk_gain}YK")
        if self.bk_gain:
            gain.append(f"+{self.bk_gain}BK")
        return f"{self.fid} x{self.pos[0]}y{self.pos[1]} trader {self.spend_gold}G->{'+'.join(gain)}"


MERCHANTS = (
    Merchant("MT6_BK", "MT6", (8, 4), spend_gold=50, bk_gain=1),
    Merchant("MT7_YK", "MT7", (6, 1), spend_gold=50, yk_gain=5),
)
MERCHANT_BY_EID = {m.action_eid: m for m in MERCHANTS}
MERCHANT_BY_KEY = {m.key: m for m in MERCHANTS}
MERCHANT_ACCESS = {
    "MT6_BK": {
        "doors": ((11, 2),),
        "monsters": ((10, 1), (11, 4)),
    },
    "MT7_YK": {
        "doors": ((11, 7), (7, 5)),
        "monsters": ((7, 3),),
    },
}


def pos_eid(fid: str, pos: tuple[int, int]) -> str | None:
    for x, y, _t, eid in gw.maps[fid]["bl"]:
        if (x, y) == pos:
            return eid
    return None


def collected_for(ent: dict[str, Any], fid: str) -> set[tuple[int, int]]:
    out = set(ent.get("collected", {}).get(fid, frozenset()))
    out.update(gw.FLOOR_13_COLLECTED.get(fid, frozenset()))
    return out


def all_collected(ent: dict[str, Any]) -> dict[str, set[tuple[int, int]]]:
    out: dict[str, set[tuple[int, int]]] = {
        fid: set(pos) for fid, pos in gw.FLOOR_13_COLLECTED.items()
    }
    for fid, pos in ent.get("collected", {}).items():
        out.setdefault(fid, set()).update(pos)
    return out


def gold_value(gold: int) -> float:
    return gold * GOLD_VALUE_PER_100 / 100.0


def explicit_collected_for(ent: dict[str, Any], fid: str) -> set[tuple[int, int]]:
    return set(ent.get("collected", {}).get(fid, frozenset()))


def merchant_used_by_collected(ent: dict[str, Any], merchant: Merchant) -> bool:
    return (
        merchant.key in set(ent.get("merchant_used", frozenset()))
        or merchant.pos in explicit_collected_for(ent, merchant.fid)
    )


def merchant_spent_from_collected(ent: dict[str, Any]) -> int:
    return sum(m.spend_gold for m in MERCHANTS if merchant_used_by_collected(ent, m))


def monster_gold_after_4f_start(ent: dict[str, Any]) -> int:
    total = 0
    for fid, positions in (ent.get("collected") or {}).items():
        initial = set(gw.FLOOR_13_COLLECTED.get(fid, frozenset()))
        for pos in set(positions) - initial:
            eid = pos_eid(fid, pos)
            if boss_event_completed(ent) and (fid, pos, eid) == BOSS_EVENT_MAP_MONSTER:
                continue
            if eid in ENEMY_GOLD:
                total += ENEMY_GOLD[eid]
    return total


def spawned_boss_gold() -> int:
    return sum(ENEMY_GOLD[eid] for eid in SPAWNED_BOSS_MONSTERS)


def boss_event_completed(ent: dict[str, Any]) -> bool:
    try:
        return is_boss_goal(ent)
    except KeyError:
        return (6, 9) in set(ent.get("collected", {}).get("MT10", frozenset()))


def is_boss_goal(ent: dict[str, Any]) -> bool:
    return rg.base.goal(ent)


def inferred_gold(ent: dict[str, Any], *, include_boss_spawn: bool | None = None) -> int:
    if include_boss_spawn is None:
        include_boss_spawn = is_boss_goal(ent)
    total = DEFAULT_START_GOLD + monster_gold_after_4f_start(ent) - merchant_spent_from_collected(ent)
    if include_boss_spawn:
        total += spawned_boss_gold()
    return total


def merchant_residual_breakdown(ent: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for merchant in MERCHANTS:
        if merchant_used_by_collected(ent, merchant):
            continue
        used = collected_for(ent, merchant.fid)
        reward = merchant.yk_gain * rg.YK_VALUE + merchant.bk_gain * rg.BK_VALUE
        gold_cost = gold_value(merchant.spend_gold)
        doors = []
        door = 0
        for pos in MERCHANT_ACCESS.get(merchant.key, {}).get("doors", ()):
            if pos in used:
                continue
            eid = pos_eid(merchant.fid, pos)
            cost = rg.door_cost(eid)
            if cost:
                door += cost
                doors.append({"pos": f"x{pos[0]}y{pos[1]}", "eid": eid, "cost": cost})
        monsters = []
        future_gold = 0
        for pos in MERCHANT_ACCESS.get(merchant.key, {}).get("monsters", ()):
            if pos not in used:
                eid = pos_eid(merchant.fid, pos)
                if eid:
                    monster_gold = ENEMY_GOLD.get(eid, 0)
                    future_gold += monster_gold
                    monsters.append({
                        "pos": f"x{pos[0]}y{pos[1]}",
                        "eid": eid,
                        "damage": 0,
                        "gold": monster_gold,
                        "gold_score": gold_value(monster_gold),
                    })
        future_gold_score = gold_value(future_gold)
        value = reward + future_gold_score - gold_cost - door
        if value <= 0:
            continue
        rows.append({
            "fid": merchant.fid,
            "floor": int(merchant.fid[2:]),
            "group": merchant.label,
            "items": [{
                "pos": f"x{merchant.pos[0]}y{merchant.pos[1]}",
                "eid": merchant.action_eid,
                "value": reward,
            }],
            "reward": reward,
            "doors": doors,
            "door_cost": door,
            "monsters": monsters,
            "monster_damage": 0,
            "future_monster_gold": future_gold,
            "future_monster_gold_score": future_gold_score,
            "gold_cost": gold_cost,
            "value": value,
        })
    return rows


def block_by_pos(fid: str) -> dict[tuple[int, int], tuple[int, str]]:
    out: dict[tuple[int, int], tuple[int, str]] = {}
    for x, y, kind, eid in gw.maps[fid]["bl"]:
        out.setdefault((x, y), (kind, eid))
    return out


def future_breakdown_cache_key(ent: dict[str, Any]) -> tuple[Any, ...]:
    collected = tuple(
        sorted((fid, tuple(sorted(pos))) for fid, pos in ent.get("collected", {}).items())
    )
    merchants = tuple(sorted(m.key for m in MERCHANTS if merchant_used_by_collected(ent, m)))
    return (ent["atk"], ent["def"], ent["rk"], boss_event_completed(ent), merchants, collected)


def future_floor_cache_key(ent: dict[str, Any], fid: str) -> tuple[Any, ...]:
    merchants = tuple(sorted(m.key for m in MERCHANTS if merchant_used_by_collected(ent, m)))
    return (
        fid,
        ent["atk"],
        ent["def"],
        ent["rk"],
        boss_event_completed(ent),
        merchants,
        tuple(sorted(collected_for(ent, fid))),
    )


def future_pos_value(fid: str, pos: tuple[int, int], eid: str, ent: dict[str, Any]) -> tuple[str, float, dict[str, Any]] | None:
    if boss_event_completed(ent) and (fid, pos, eid) == BOSS_EVENT_MAP_MONSTER:
        return None
    if eid in ENEMY_GOLD:
        monster_gold = ENEMY_GOLD[eid]
        return "monster", gold_value(monster_gold), {
            "pos": f"x{pos[0]}y{pos[1]}",
            "eid": eid,
            "damage": 0,
            "gold": monster_gold,
            "gold_score": gold_value(monster_gold),
        }
    merchant = MERCHANT_BY_EID.get(eid)
    if merchant is not None and not merchant_used_by_collected(ent, merchant):
        reward = merchant.yk_gain * rg.YK_VALUE + merchant.bk_gain * rg.BK_VALUE
        gold_cost = gold_value(merchant.spend_gold)
        return "merchant", reward - gold_cost, {
            "pos": f"x{pos[0]}y{pos[1]}",
            "eid": eid,
            "value": reward - gold_cost,
            "reward": reward,
            "gold_cost": gold_cost,
        }
    item_value = rg.item_value(eid, ent)
    if item_value > 0:
        return "item", item_value, {
            "pos": f"x{pos[0]}y{pos[1]}",
            "eid": eid,
            "value": item_value,
        }
    return None


def future_floor_breakdown(ent: dict[str, Any], fid: str) -> dict[str, Any] | None:
    cache_key = future_floor_cache_key(ent, fid)
    cached = _FUTURE_FLOOR_CACHE.get(cache_key)
    if cache_key in _FUTURE_FLOOR_CACHE:
        return dict(cached) if cached is not None else None

    used = collected_for(ent, fid)
    blocks = block_by_pos(fid)
    block_positions = set(blocks)
    closed_doors: list[tuple[tuple[int, int], str, int]] = []
    reward_by_pos: dict[tuple[int, int], tuple[str, float, dict[str, Any]]] = {}

    for pos, (_kind, eid) in blocks.items():
        if pos in used:
            continue
        if eid in {"yellowDoor", "blueDoor"}:
            cost = rg.door_cost(eid)
            if cost > 0:
                closed_doors.append((pos, eid, cost))
            continue
        value = future_pos_value(fid, pos, eid, ent)
        if value is not None:
            reward_by_pos[pos] = value

    data = gw.maps[fid]
    width = data["W"]
    height = data["H"]
    map_data = data["m"]
    sx, sy = gw.FLYBACK_ENTRANCES[fid]
    best: dict[str, Any] | None = None
    door_count = len(closed_doors)

    def is_passable(x: int, y: int, opened: set[tuple[int, int]]) -> bool:
        if x <= 0 or y <= 0 or x >= width - 1 or y >= height - 1:
            return False
        pos = (x, y)
        block = blocks.get(pos)
        if block is not None:
            _kind, eid = block
            if pos not in used and eid in {"yellowDoor", "blueDoor"}:
                return pos in opened
            if pos not in used and eid.endswith("Door"):
                return False
            return True
        return map_data[y][x] != 1

    for mask in range(1 << door_count):
        opened = {
            closed_doors[idx][0]
            for idx in range(door_count)
            if mask & (1 << idx)
        }
        seen = {(sx, sy)}
        queue = deque([(sx, sy)])
        while queue:
            x, y = queue.popleft()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                npos = (nx, ny)
                if npos in seen or not is_passable(nx, ny, opened):
                    continue
                seen.add(npos)
                queue.append(npos)

        opened_cost = 0
        doors = []
        for pos, eid, cost in closed_doors:
            if pos not in opened or pos not in seen:
                continue
            opened_cost += cost
            doors.append({"pos": f"x{pos[0]}y{pos[1]}", "eid": eid, "cost": cost})

        items = []
        monsters = []
        merchants = []
        reward = 0.0
        future_gold = 0
        future_gold_score = 0.0
        future_merchant_value = 0.0
        for pos, (kind, value, info) in reward_by_pos.items():
            if pos not in seen:
                continue
            reward += value
            if kind == "monster":
                monsters.append(info)
                future_gold += info["gold"]
                future_gold_score += info["gold_score"]
            elif kind == "merchant":
                merchants.append(info)
                future_merchant_value += value
            else:
                items.append(info)

        net = reward - opened_cost
        if best is None or net > best["value"]:
            best = {
                "fid": fid,
                "floor": int(fid[2:]),
                "group": f"{fid} full-map future resources",
                "items": items,
                "merchants": merchants,
                "reward": reward,
                "doors": doors,
                "door_cost": opened_cost,
                "monsters": monsters,
                "monster_damage": 0,
                "future_monster_gold": future_gold,
                "future_monster_gold_score": future_gold_score,
                "future_merchant_value": future_merchant_value,
                "value": net,
            }

    if best is None or best["value"] <= 0:
        _FUTURE_FLOOR_CACHE[cache_key] = None
        return None
    _FUTURE_FLOOR_CACHE[cache_key] = best
    return best


def resource_group_breakdown_with_future_gold(ent: dict[str, Any]) -> list[dict[str, Any]]:
    key = future_breakdown_cache_key(ent)
    cached = _FUTURE_BREAKDOWN_CACHE.get(key)
    if cached is not None:
        return [dict(row) for row in cached]
    rows = []
    for fid in sorted(gw.maps):
        row = future_floor_breakdown(ent, fid)
        if row is not None:
            rows.append(row)
    _FUTURE_BREAKDOWN_CACHE[key] = rows
    return [dict(row) for row in rows]


def final_resource_stock_with_future_gold(ent: dict[str, Any]) -> float:
    return (
        ent["hp"]
        + ent["yk"] * rg.YK_VALUE
        + ent["bk"] * rg.BK_VALUE
        + sum(row["value"] for row in resource_group_breakdown_with_future_gold(ent))
    )


def final_stock_with_gold(ent: dict[str, Any]) -> float:
    return final_resource_stock_with_future_gold(ent) + gold_value(inferred_gold(ent))


def monster_gold_for_positions(fid: str, positions: Iterable[tuple[int, int]]) -> int:
    total = 0
    for pos in positions:
        eid = pos_eid(fid, pos)
        if eid in ENEMY_GOLD:
            total += ENEMY_GOLD[eid]
    return total


def collected_monster_gold(ent: dict[str, Any]) -> int:
    total = 0
    for fid, positions in all_collected(ent).items():
        total += monster_gold_for_positions(fid, positions)
    return total


def initial_phase1_state(start_gold: int = 0) -> dict[str, Any]:
    gw.PHASE1_BUCKETS_ENABLED = True
    gw._entry_store.clear()
    gw._next_id[0] = 1
    start = {
        "hp": gw.hero["h"],
        "atk": gw.hero["a"],
        "def": gw.hero["d"],
        "yk": gw.hero["yk"],
        "bk": gw.hero["bk"],
        "rk": 0,
        "gold": start_gold,
        "_gold_gained": 0,
        "_gold_spent": 0,
        "merchant_used": frozenset(),
        "collected": gw.initial_collected_state(),
        "_id": 1,
        "_parent_id": None,
        "_step_info": None,
        "_dmg": 0,
        "_yd": 0,
        "_bd": 0,
        "_rd": 0,
        "_max_floor": 4,
        "_action_depth": 0,
    }
    gw._entry_store[1] = dict(start)
    return start


def sync_store(ent: dict[str, Any]) -> None:
    if "_id" in ent and ent["_id"] in gw._entry_store:
        gw._entry_store[ent["_id"]].update({
            "gold": ent.get("gold", 0),
            "_gold_gained": ent.get("_gold_gained", 0),
            "_gold_spent": ent.get("_gold_spent", 0),
            "merchant_used": ent.get("merchant_used", frozenset()),
            "_last_action": ent.get("_last_action"),
            "_max_floor": ent.get("_max_floor", 4),
            "_action_depth": ent.get("_action_depth", 0),
        })


def ensure_merchant_maps() -> None:
    for merchant in MERCHANTS:
        blocks = gw.maps[merchant.fid]["bl"]
        if not any((x, y, eid) == (*merchant.pos, merchant.action_eid) for x, y, _t, eid in blocks):
            blocks.append((merchant.pos[0], merchant.pos[1], 3, merchant.action_eid))


def collected_signature(ent: dict[str, Any]) -> tuple[Any, ...]:
    return tuple(
        (fid, tuple(sorted(pos)))
        for fid, pos in sorted((ent.get("collected") or {}).items())
        if pos
    )


def merchant_signature(ent: dict[str, Any]) -> tuple[str, ...]:
    return tuple(sorted(ent.get("merchant_used", frozenset())))


def dominates(a: dict[str, Any], b: dict[str, Any]) -> bool:
    if collected_signature(a) != collected_signature(b):
        return False
    if merchant_signature(a) != merchant_signature(b):
        return False
    if not (
        a.get("_dmg", 0) <= b.get("_dmg", 0)
        and a.get("_yd", 0) <= b.get("_yd", 0)
        and a.get("_bd", 0) <= b.get("_bd", 0)
        and a.get("_rd", 0) <= b.get("_rd", 0)
        and a["atk"] >= b["atk"]
        and a["def"] >= b["def"]
        and a["yk"] >= b["yk"]
        and a["bk"] >= b["bk"]
        and a["rk"] >= b["rk"]
        and a.get("gold", 0) >= b.get("gold", 0)
    ):
        return False
    strict = (
        a.get("_dmg", 0) < b.get("_dmg", 0)
        or a.get("_yd", 0) < b.get("_yd", 0)
        or a.get("_bd", 0) < b.get("_bd", 0)
        or a.get("_rd", 0) < b.get("_rd", 0)
        or a["atk"] > b["atk"]
        or a["def"] > b["def"]
        or a["yk"] > b["yk"]
        or a["bk"] > b["bk"]
        or a["rk"] > b["rk"]
        or a.get("gold", 0) > b.get("gold", 0)
    )
    same_core = (
        a.get("_dmg", 0) == b.get("_dmg", 0)
        and a.get("_yd", 0) == b.get("_yd", 0)
        and a.get("_bd", 0) == b.get("_bd", 0)
        and a.get("_rd", 0) == b.get("_rd", 0)
        and a["atk"] == b["atk"]
        and a["def"] == b["def"]
        and a["yk"] == b["yk"]
        and a["bk"] == b["bk"]
        and a["rk"] == b["rk"]
        and a.get("gold", 0) == b.get("gold", 0)
    )
    return strict or (same_core and a["hp"] >= b["hp"])


def add_to_archive(archive: dict[tuple[Any, ...], list[dict[str, Any]]], ent: dict[str, Any]) -> bool:
    bucket = (ent.get("_max_floor", 4), collected_signature(ent), merchant_signature(ent))
    items = archive[bucket]
    if any(dominates(old, ent) for old in items):
        return False
    archive[bucket] = [old for old in items if not dominates(ent, old)]
    archive[bucket].append(ent)
    return True


def phase1_done(ent: dict[str, Any]) -> bool:
    return p1.is_goal(ent)


def state_text(ent: dict[str, Any]) -> str:
    return (
        f"HP={ent['hp']} ATK={ent['atk']} DEF={ent['def']} "
        f"YK={ent['yk']} BK={ent['bk']} RK={ent['rk']} "
        f"dmg={ent.get('_dmg', 0)} door={ent.get('_yd', 0)}/{ent.get('_bd', 0)}/{ent.get('_rd', 0)} "
        f"G={ent.get('gold', 0)} spent={ent.get('_gold_spent', 0)}"
    )


def score_key(ent: dict[str, Any]) -> tuple[Any, ...]:
    return (
        -final_stock_with_gold(ent),
        rg.resource_group_score(ent),
        ent.get("_dmg", 0),
        ent.get("_yd", 0),
        ent.get("_bd", 0),
        -ent.get("gold", 0),
        -ent["hp"],
    )


def priority(ent: dict[str, Any]) -> tuple[Any, ...]:
    return (
        rg.resource_group_score(ent)
        + p1.heuristic(ent)
        - int(gold_value(ent.get("gold", 0)))
        - (80 if ent.get("merchant_used") else 0),
        -ent.get("_max_floor", 4),
        len(ent.get("merchant_used", frozenset())),
        ent.get("_dmg", 0),
        ent.get("_yd", 0),
        ent.get("_bd", 0),
        -ent["yk"],
        -ent["bk"],
        -ent.get("gold", 0),
        -ent["hp"],
    )


def action_sort(ent: dict[str, Any], action: tuple[Any, ...]) -> tuple[Any, ...]:
    if action and action[0] == "merchant":
        merchant = MERCHANT_BY_KEY[action[1]]
        return (35 if merchant.fid == "MT7" else 48, merchant.fid, merchant.key)
    return p1.action_rank(ent, action)


def possible_actions(ent: dict[str, Any]) -> list[tuple[Any, ...]]:
    actions = list(p1.possible_actions(ent))
    max_floor = ent.get("_max_floor", 4)
    used = set(ent.get("merchant_used", frozenset()))
    for merchant in MERCHANTS:
        if merchant.key in used:
            continue
        if p1.FLOOR_NO[merchant.fid] > max_floor:
            continue
        if not p1.has_item(ent, "MT5", "sword1"):
            continue
        actions.append(("merchant", merchant.key))
    actions.sort(key=lambda action: action_sort(ent, action))
    return actions[:16]


def action_parts(action: tuple[Any, ...]) -> tuple[str, list[str], bool, int, list[str]]:
    return p1.action_parts(action)


def expand_normal_action(ent: dict[str, Any], action: tuple[Any, ...]) -> list[dict[str, Any]]:
    fid, targets, flyback, new_max_floor, must_targets = action_parts(action)
    already = collected_for(ent, fid)
    pareto, _iters, _nodes = gw.search_floor(
        gw.maps,
        fid,
        ent,
        targets,
        max_iter=120000,
        flyback=flyback,
    )
    if not pareto:
        return []
    need = frozenset()
    for target in must_targets:
        need |= frozenset(
            (x, y)
            for x, y, _t, eid in gw.maps[fid]["bl"]
            if eid == target and (x, y) not in already
        )
    out = []
    for hp, yk, bk, rk_, atk, def_, _hs, vis, dc in pareto:
        if need and not need <= vis:
            continue
        if p1.unintended_major_positions(fid, targets, vis):
            continue
        nc = dict(ent.get("collected", {}))
        nc[fid] = already | vis
        gained = monster_gold_for_positions(fid, set(vis) - already)
        res = gw._make_result(
            hp,
            yk,
            bk,
            rk_,
            atk,
            def_,
            nc,
            ent["_id"],
            (fid, targets, flyback),
            dmg_cost=dc,
        )
        res["_max_floor"] = new_max_floor
        res["_action_depth"] = ent.get("_action_depth", 0) + 1
        res["gold"] = ent.get("gold", 0) + gained
        res["_gold_gained"] = ent.get("_gold_gained", 0) + gained
        res["_gold_spent"] = ent.get("_gold_spent", 0)
        res["merchant_used"] = ent.get("merchant_used", frozenset())
        res["_last_action"] = f"{fid}:{'+'.join(targets)}:{'fb' if flyback else 'new'}"
        sync_store(res)
        out.append(res)
    return cap_results(out)


def expand_merchant_action(ent: dict[str, Any], action: tuple[Any, ...]) -> list[dict[str, Any]]:
    merchant = MERCHANT_BY_KEY[action[1]]
    if merchant.key in set(ent.get("merchant_used", frozenset())):
        return []
    already = collected_for(ent, merchant.fid)
    pareto, _iters, _nodes = gw.search_floor(
        gw.maps,
        merchant.fid,
        ent,
        [merchant.action_eid],
        max_iter=120000,
        flyback=merchant.fid in ent.get("collected", {}) or p1.FLOOR_NO[merchant.fid] < ent.get("_max_floor", 4),
    )
    if not pareto:
        return []
    out = []
    for hp, yk, bk, rk_, atk, def_, _hs, vis, dc in pareto:
        if merchant.pos not in vis:
            continue
        nc = dict(ent.get("collected", {}))
        nc[merchant.fid] = already | vis
        gained = monster_gold_for_positions(merchant.fid, set(vis) - already)
        if ent.get("gold", 0) + gained < merchant.spend_gold:
            continue
        res = gw._make_result(
            hp,
            yk + merchant.yk_gain,
            bk + merchant.bk_gain,
            rk_,
            atk,
            def_,
            nc,
            ent["_id"],
            (merchant.fid, [merchant.action_eid], True),
            dmg_cost=dc,
        )
        used = set(ent.get("merchant_used", frozenset()))
        used.add(merchant.key)
        res["_max_floor"] = ent.get("_max_floor", 4)
        res["_action_depth"] = ent.get("_action_depth", 0) + 1
        res["gold"] = ent.get("gold", 0) + gained - merchant.spend_gold
        res["_gold_gained"] = ent.get("_gold_gained", 0) + gained
        res["_gold_spent"] = ent.get("_gold_spent", 0) + merchant.spend_gold
        res["merchant_used"] = frozenset(used)
        res["_last_action"] = merchant.label
        sync_store(res)
        out.append(res)
    return cap_results(out, limit=24)


def expand_action(ent: dict[str, Any], action: tuple[Any, ...]) -> list[dict[str, Any]]:
    if action and action[0] == "merchant":
        return expand_merchant_action(ent, action)
    return expand_normal_action(ent, action)


def cap_results(results: list[dict[str, Any]], limit: int = 96) -> list[dict[str, Any]]:
    if len(results) <= limit:
        return results
    chosen: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()

    def key_for(ent: dict[str, Any]) -> tuple[Any, ...]:
        return (
            ent["atk"],
            ent["def"],
            ent["yk"],
            ent["bk"],
            ent["rk"],
            ent.get("_yd", 0),
            ent.get("_bd", 0),
            ent.get("_rd", 0),
            ent.get("gold", 0),
            merchant_signature(ent),
            collected_signature(ent),
        )

    def add(items: Iterable[dict[str, Any]], quota: int) -> None:
        added = 0
        for ent in items:
            key = key_for(ent)
            if key in seen:
                continue
            seen.add(key)
            chosen.append(ent)
            added += 1
            if len(chosen) >= limit or added >= quota:
                return

    add(sorted(results, key=lambda e: (e.get("_dmg", 0), e.get("_yd", 0), e.get("_bd", 0), -e["hp"])), 18)
    add(sorted(results, key=lambda e: (-e["yk"], -e["bk"], e.get("_dmg", 0), -e.get("gold", 0), -e["hp"])), 18)
    add(sorted(results, key=lambda e: (-e.get("gold", 0), e.get("_dmg", 0), -e["hp"])), 12)
    add(sorted(results, key=lambda e: score_key(e)), limit)
    return chosen[:limit]


def select_representatives(entries: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    if len(entries) <= limit:
        return sorted(entries, key=score_key)
    chosen: list[dict[str, Any]] = []
    seen: set[int] = set()

    def add(items: Iterable[dict[str, Any]], quota: int) -> None:
        added = 0
        for ent in items:
            eid = ent["_id"]
            if eid in seen:
                continue
            seen.add(eid)
            chosen.append(ent)
            added += 1
            if len(chosen) >= limit or added >= quota:
                return

    add(sorted(entries, key=score_key), max(4, limit // 3))
    add(sorted(entries, key=lambda e: (-len(e.get("merchant_used", frozenset())), score_key(e))), max(4, limit // 4))
    add(sorted(entries, key=lambda e: (-e["yk"], -e["bk"], e.get("_dmg", 0), -e["hp"])), max(4, limit // 4))
    add(sorted(entries, key=lambda e: (e.get("_dmg", 0), e.get("_yd", 0), e.get("_bd", 0), -e["hp"])), limit)
    return chosen[:limit]


def trace_actions(ent: dict[str, Any]) -> list[str]:
    chain = gw.trace_chain(ent)
    return [item.get("_last_action") or str(item.get("_step_info")) for item in chain if item.get("_parent_id")]


def result_record(ent: dict[str, Any]) -> dict[str, Any]:
    final_stock = final_resource_stock_with_future_gold(ent)
    gold = inferred_gold(ent)
    groups = resource_group_breakdown_with_future_gold(ent)
    merchant_residual = sum(row.get("future_merchant_value", 0) for row in groups)
    future_monster_gold = sum(
        row.get("future_monster_gold", 0)
        for row in groups
    )
    final_score = final_stock + gold_value(gold)
    return {
        "id": ent.get("_id"),
        "hp": ent["hp"],
        "atk": ent["atk"],
        "def": ent["def"],
        "yk": ent["yk"],
        "bk": ent["bk"],
        "rk": ent["rk"],
        "dmg": ent.get("_dmg", 0),
        "yd": ent.get("_yd", 0),
        "bd": ent.get("_bd", 0),
        "rd": ent.get("_rd", 0),
        "gold": gold,
        "gold_gained": monster_gold_after_4f_start(ent),
        "gold_spent": merchant_spent_from_collected(ent),
        "merchant_used": sorted(
            m.key for m in MERCHANTS if merchant_used_by_collected(ent, m)
        ),
        "final_stock": final_stock,
        "gold_value": gold_value(gold),
        "future_monster_gold": future_monster_gold,
        "future_monster_gold_value": gold_value(future_monster_gold),
        "merchant_residual": merchant_residual,
        "final_stock_with_gold": final_score,
        "final_score": final_score,
        "jhp": ent["hp"],
        "resource_group_score": rg.resource_group_score(ent),
        "actions": trace_actions(ent),
    }


def run_search(args: argparse.Namespace) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    ensure_merchant_maps()
    start = initial_phase1_state(args.start_gold)
    archive: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    heap: list[tuple[Any, int, dict[str, Any]]] = []
    seq = 0
    heapq.heappush(heap, (priority(start), seq, start))
    add_to_archive(archive, start)
    goals: list[dict[str, Any]] = []
    generated = 0
    expanded = 0
    t0 = time.time()

    while heap and expanded < args.max_expansions:
        _key, _seq, ent = heapq.heappop(heap)
        expanded += 1
        if phase1_done(ent) and any(merchant_used_by_collected(ent, m) for m in MERCHANTS):
            goals.append(ent)
            if len(goals) >= args.goal_limit and expanded >= args.min_expansions:
                break
        for action in possible_actions(ent):
            for nxt in expand_action(ent, action):
                generated += 1
                if not add_to_archive(archive, nxt):
                    continue
                seq += 1
                heapq.heappush(heap, (priority(nxt), seq, nxt))

    meta = {
        "elapsed": time.time() - t0,
        "expanded": expanded,
        "generated": generated,
        "archive_entries": sum(len(v) for v in archive.values()),
        "raw_goal_count": len(goals),
        "frontier": len(heap),
    }
    return select_representatives(goals, args.report_limit), meta


def load_result(path: str) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def ent_from_result_row(row: dict[str, Any]) -> dict[str, Any]:
    collected = {
        fid: frozenset((item["x"], item["y"]) if isinstance(item, dict) else tuple(item) for item in positions)
        for fid, positions in row.get("collected", {}).items()
    }
    return {
        "hp": row["hp"],
        "atk": row["atk"],
        "def": row["def"],
        "yk": row["yk"],
        "bk": row["bk"],
        "rk": row.get("rk", 0),
        "collected": collected,
        "_dmg": row.get("dmg", row.get("_dmg", 0)),
        "_yd": row.get("yd", row.get("_yd", 0)),
        "_bd": row.get("bd", row.get("_bd", 0)),
        "_rd": row.get("rd", row.get("_rd", 0)),
    }


def guide_full_ent() -> dict[str, Any]:
    fixed_result = fixed.replay_route()
    collected: dict[str, set[tuple[int, int]]] = {
        fid: set(pos) for fid, pos in gw.FLOOR_13_COLLECTED.items()
    }
    for fid, positions in fixed_result["collected"].items():
        collected.setdefault(fid, set()).update((item["x"], item["y"]) for item in positions)
    replay = guide.replay()
    for step in replay["steps"]:
        fid = step["floor"]
        pos = tuple(step["pos"])
        eid = step.get("eid")
        if eid and (
            eid in {"yellowDoor", "blueDoor", "redDoor"}
            or eid in MONSTER_EIDS
            or eid.endswith("Key")
            or eid.endswith("Potion")
            or eid.endswith("Gem")
        ):
            collected.setdefault(fid, set()).add(pos)
    state = replay["final"]["state"]
    doors = replay["final"]["doors"]
    return {
        "hp": state["hp"],
        "atk": state["atk"],
        "def": state["def"],
        "yk": state["yk"],
        "bk": state["bk"],
        "rk": state["rk"],
        "collected": {fid: frozenset(pos) for fid, pos in collected.items()},
        "_dmg": replay["final"]["dmg"],
        "_yd": doors["yellow"],
        "_bd": doors["blue"],
        "_rd": doors["red"],
        "gold": inferred_gold({"collected": {fid: frozenset(pos) for fid, pos in collected.items()}}, include_boss_spawn=True),
        "_gold_spent": 0,
        "_gold_gained": 0,
        "merchant_used": frozenset(),
    }


def existing_best_record(label: str, path: str) -> dict[str, Any]:
    data = load_result(path)
    row = data["best"]
    ent = ent_from_result_row(row)
    ent["gold"] = collected_monster_gold(ent)
    ent["_gold_spent"] = 0
    ent["_gold_gained"] = ent["gold"]
    ent["merchant_used"] = frozenset()
    rec = result_record(ent)
    rec["label"] = label
    rec["path"] = path
    return rec


def guide_record() -> dict[str, Any]:
    ent = guide_full_ent()
    rec = result_record(ent)
    rec["label"] = "fixed guide post-9"
    rec["path"] = "outputs/results/user_post9_route_replay.json"
    return rec


def summarize_phase1_to_boss_upper(phase1: dict[str, Any]) -> dict[str, Any]:
    """Simple same-boss-resource projection from a 4-9 result.

    The full post-9 search is not rerun here.  This row answers whether the
    merchant prefix carries more scored stock into the later boss-resource
    problem, using the current residual groups and gold valuation at 9F.
    """
    return {
        "state": state_text(phase1),
        "phase1_final_stock": rg.final_resource_stock(phase1),
        "phase1_gold": phase1.get("gold", 0),
        "phase1_gold_value": gold_value(phase1.get("gold", 0)),
        "phase1_final_stock_with_gold": final_stock_with_gold(phase1),
        "merchant_used": sorted(phase1.get("merchant_used", frozenset())),
        "remaining_resource_groups": rg.residual_resource_breakdown(phase1, ignore_monster_damage=True)[:20],
    }


def write_outputs(data: dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    lines = [
        "# Merchant Resource Path Compare",
        "",
        "## Assumptions",
        "",
        f"- Gold score: `100G = 50 stock`, so remaining gold contributes `G * 0.5`.",
        f"- Key score: `1YK = {rg.YK_VALUE}`, `1BK = 4YK = {rg.BK_VALUE}`.",
        f"- Enemy gold table: `{ENEMY_GOLD}`.",
        "- Merchant actions are explicit and consume gold before adding keys.",
        "- MT6 red potion and MT6 trader are kept as separate resources; the trader is not merged into the red-potion group.",
        "",
        "## 4F-9F Merchant Search",
        "",
        f"- elapsed: `{data['phase1_search']['elapsed']:.1f}s`",
        f"- expanded/generated: `{data['phase1_search']['expanded']}/{data['phase1_search']['generated']}`",
        f"- raw goals: `{data['phase1_search']['raw_goal_count']}`",
        "",
        "| # | state | merchants | final | gold | final+gold | actions |",
        "|---:|---|---|---:|---:|---:|---|",
    ]
    for idx, row in enumerate(data["merchant_phase1_top"], 1):
        lines.append(
            f"| {idx} | HP={row['hp']} ATK={row['atk']} DEF={row['def']} "
            f"YK={row['yk']} BK={row['bk']} dmg={row['dmg']} door={row['yd']}/{row['bd']}/{row['rd']} | "
            f"{','.join(row['merchant_used']) or '-'} | {row['final_stock']} | {row['gold']} | "
            f"{row['final_stock_with_gold']:.1f} | {'; '.join(row['actions'])} |"
        )
    lines.extend([
        "",
        "## Existing Boss Goals With Gold",
        "",
        "| route | state | final | gold | final+gold | source |",
        "|---|---|---:|---:|---:|---|",
    ])
    for row in data["existing_boss_goals"]:
        lines.append(
            f"| {row['label']} | HP={row['hp']} ATK={row['atk']} DEF={row['def']} "
            f"YK={row['yk']} BK={row['bk']} dmg={row['dmg']} door={row['yd']}/{row['bd']}/{row['rd']} | "
            f"{row['final_stock']} | {row['gold']} | {row['final_stock_with_gold']:.1f} | `{row['path']}` |"
        )
    lines.extend([
        "",
        "## Merchant Prefix Boss-Resource Projection",
        "",
    ])
    proj = data.get("merchant_prefix_projection")
    if proj:
        lines.extend([
            f"- state: `{proj['state']}`",
            f"- phase1 finalStock/gold/final+gold: `{proj['phase1_final_stock']}` / `{proj['phase1_gold']}` / `{proj['phase1_final_stock_with_gold']:.1f}`",
            f"- merchants: `{','.join(proj['merchant_used']) or '-'}`",
            "",
            "Top remaining final-resource groups at the 9F boundary:",
            "",
            "| group | value | reward | door | items |",
            "|---|---:|---:|---:|---|",
        ])
        for row in proj["remaining_resource_groups"][:10]:
            items = ", ".join(f"{item['pos']} {item['eid']}={item['value']}" for item in row["items"])
            lines.append(
                f"| {row['group']} | {row['value']} | {row['reward']} | {row['door_cost']} | {items} |"
            )
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-expansions", type=int, default=1200)
    parser.add_argument("--min-expansions", type=int, default=250)
    parser.add_argument("--goal-limit", type=int, default=160)
    parser.add_argument("--report-limit", type=int, default=12)
    parser.add_argument("--start-gold", type=int, default=DEFAULT_START_GOLD)
    parser.add_argument(
        "--delayed-result",
        default="outputs/results/post9_gem_supply_search_topk_dp_full.json",
    )
    parser.add_argument(
        "--fixed-result",
        default="outputs/results/user_post9_route_replay.json",
    )
    args = parser.parse_args()

    goals, meta = run_search(args)
    top = [result_record(ent) for ent in goals]
    top.sort(key=lambda row: (-row["final_stock_with_gold"], row["dmg"], -row["hp"]))

    existing = [
        guide_record(),
        existing_best_record("delayed post-9 known best", args.delayed_result),
    ]

    data = {
        "assumptions": {
            "gold_value_per_100": GOLD_VALUE_PER_100,
            "yellow_key_value": rg.YK_VALUE,
            "blue_key_value": rg.BK_VALUE,
            "enemy_gold": ENEMY_GOLD,
            "start_gold": args.start_gold,
            "merchant_groups": [
                {
                    "key": m.key,
                    "fid": m.fid,
                    "pos": list(m.pos),
                    "spend_gold": m.spend_gold,
                    "yk_gain": m.yk_gain,
                    "bk_gain": m.bk_gain,
                }
                for m in MERCHANTS
            ],
        },
        "phase1_search": meta,
        "merchant_phase1_top": top,
        "existing_boss_goals": existing,
        "merchant_prefix_projection": summarize_phase1_to_boss_upper(top[0]) if top else None,
    }
    write_outputs(data)
    print(f"wrote {OUT_JSON}")
    print(f"wrote {OUT_MD}")
    if top:
        print(
            "best merchant phase1:",
            state_text(top[0]),
            f"final+gold={top[0]['final_stock_with_gold']:.1f}",
        )


if __name__ == "__main__":
    main()
