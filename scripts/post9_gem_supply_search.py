#!/usr/bin/env python3
"""Search post-9 stats as a gem backbone with bounded supply closures.

The compressed resource graph is still authoritative: every edge is replayed
through the real floor search.  This experiment changes only scheduling.  The
outer search advances gems / MT10 progress, while a small inner closure keeps
representative key and potion detours that can make the next backbone action
feasible or cheaper.
"""

from __future__ import annotations

import argparse
import heapq
import json
import os
import sys
import time
from collections import defaultdict
from typing import Any, Iterable


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.chdir(ROOT)

from scripts import continue_delayed_phase1_with_post9_resource as delayed
from scripts import fixed_shield_strategy as fixed
from scripts import phase1_action_search as p1
from scripts import post9_action_search as p9
from scripts import post9_atomic_resource_dijkstra as atomic
from scripts import post9_auto_resource_group_pareto as auto
from scripts import post9_compressed_resource_dijkstra as compressed
from scripts import post9_resource_group_search as rg
from scripts import report_post9_compressed_resource_topology as topo
from src.solver import gen_walkthrough as gw
from src.solver.full_search import calc_dmg


OUT_JSON = os.path.join("outputs", "results", "post9_gem_supply_search.json")
OUT_MD = os.path.join("outputs", "reports", "post9_gem_supply_search.md")
OUT_WALK = os.path.join("outputs", "walkthroughs", "walkthrough_post9_gem_supply_best_stat27.md")
PHASE1_REPLAY_JSON = os.path.join("outputs", "results", "delayed_phase1_post9_resource.json")
PHASE1_RESOURCE_JSON = os.path.join("outputs", "results", "phase1_resource_group_search.json")

BACKBONE_EIDS = frozenset({"redGem", "blueGem"})
SUPPLY_EIDS = frozenset({"yellowKey", "blueKey", "redPotion", "bluePotion"})
RAW_RESOURCE_VALUE = {
    "yellowKey": rg.YK_VALUE,
    "blueKey": rg.BK_VALUE,
    "redKey": 0,
    "redPotion": 50,
    "bluePotion": 200,
    "redGem": 0,
    "blueGem": 0,
}
RAW_STOCK_FUTURE_DOOR_BOUND_ENABLED = False
RAW_STOCK_FUTURE_DOOR_BOUND_VERSION = 2
NET_POCKET_RAW_STOCK_ENABLED = False
NET_POCKET_RAW_STOCK_VERSION = 1
FUTURE_DOOR_COST = {
    "yellowDoor": rg.YK_VALUE,
    "blueDoor": rg.BK_VALUE,
    "redDoor": rg.RED_KEY_VALUE,
}
MT10_ENTRY_REQUIRED_DOORS = (
    ("MT9", (6, 11), "yellowDoor"),
    ("MT9", (3, 11), "blueDoor"),
)
MT8_REDKEY_REQUIRED_DOORS = (
    ("MT8", (10, 7), "yellowDoor"),
)
MT10_BOSS_REQUIRED_DOORS = (
    ("MT10", (1, 9), "yellowDoor"),
    ("MT10", (3, 9), "yellowDoor"),
)
AUDITED_NET_RESOURCE_POCKETS = (
    {
        "name": "MT7 x5y10/x5y11 two yellow keys",
        "fid": "MT7",
        "items": (((5, 10), "yellowKey"), ((5, 11), "yellowKey")),
        "doors": (((5, 7), "yellowDoor"),),
    },
)
STAT_GEM_TARGETS = tuple(
    sorted(
        (target.fid, target.pos, target.eid)
        for target in auto.TARGETS
        if target.eid in BACKBONE_EIDS
    )
)
STAT_GEM_INDEX = {
    (fid, pos, eid): idx
    for idx, (fid, pos, eid) in enumerate(STAT_GEM_TARGETS)
}
_UNCACHED_SEARCH_FLOOR = gw.search_floor
FLOOR_SEARCH_CACHE_ENABLED = False
FLOOR_SEARCH_CACHE_LIMIT = 0
FLOOR_SEARCH_CACHE_PATH = ""
FLOOR_SEARCH_CACHE: dict[str, tuple[Any, int, Any]] = {}
FLOOR_SEARCH_CACHE_STATS: dict[str, int] = defaultdict(int)
SUPPLY_DOMINANCE_STATS: dict[str, int] = defaultdict(int)
DEFERRED_CACHE_VERSION = 1
FLOOR_SEARCH_CACHE_VERSION = 1
DEFERRED_METADATA_KEYS = (
    "_edge_kind",
    "_edge_fid",
    "_via_targets",
    "_resource_group",
    "_dynamic_value",
    "_dynamic_cost",
    "_dynamic_net",
    "_dynamic_efficiency",
    "_dynamic_total",
    "_major_order",
    "_outer_parent_order",
    "_backbone_target",
)


def search_state_key(ent: dict[str, Any]) -> str:
    """Stable exact-state key for cross-pass expansion memoization."""
    payload = [
        ent["hp"],
        ent["atk"],
        ent["def"],
        ent["yk"],
        ent["bk"],
        ent["rk"],
        ent.get("_dmg", 0),
        ent.get("_yd", 0),
        ent.get("_bd", 0),
        ent.get("_rd", 0),
        gw._collected_signature(ent),
    ]
    return json.dumps(payload, ensure_ascii=True, separators=(",", ":"))


def floor_search_cache_key(
    fid: str,
    ent: dict[str, Any],
    targets: Iterable[str],
    max_iter: int,
    flyback: bool,
    extra_removed: Iterable[tuple[int, int]] | None,
) -> str:
    """Exact inputs that affect a single-floor search result."""
    local_collected = tuple(sorted(ent.get("collected", {}).get(fid, frozenset())))
    extra = tuple(sorted(extra_removed or ()))
    payload = (
        fid,
        tuple(targets),
        max_iter,
        flyback,
        ent["hp"],
        ent["atk"],
        ent["def"],
        ent["yk"],
        ent["bk"],
        ent["rk"],
        local_collected,
        extra,
    )
    return json.dumps(payload, ensure_ascii=True, separators=(",", ":"))


def serialize_floor_search_result(result: tuple[Any, int, Any]) -> dict[str, Any]:
    pareto, iters, _nodes = result
    rows = []
    for row in pareto or []:
        hp, yk, bk, rk, atk, def_, hs, vis, dc = row
        rows.append({
            "hp": hp,
            "yk": yk,
            "bk": bk,
            "rk": rk,
            "atk": atk,
            "def": def_,
            "hs": hs,
            "vis": [list(pos) for pos in sorted(vis)],
            "dc": dc,
        })
    return {"iters": iters, "pareto": rows}


def deserialize_floor_search_result(row: dict[str, Any]) -> tuple[Any, int, Any]:
    pareto = [
        (
            item["hp"],
            item["yk"],
            item["bk"],
            item["rk"],
            item["atk"],
            item["def"],
            item["hs"],
            frozenset(tuple(pos) for pos in item["vis"]),
            item["dc"],
        )
        for item in row.get("pareto", [])
    ]
    # Callers in this script ignore the node table.  Returning an empty list on
    # disk-cache hits keeps the public shape without storing repeated map data.
    return pareto, row.get("iters", 0), []


def cached_search_floor(
    maps: dict[str, Any],
    fid: str,
    ent: dict[str, Any],
    targets: Iterable[str],
    max_iter: int = 500000,
    flyback: bool = False,
    extra_removed: Iterable[tuple[int, int]] | None = None,
) -> tuple[Any, int, Any]:
    """In-memory exact cache around the authoritative floor search."""
    target_tuple = tuple(targets)
    key = floor_search_cache_key(fid, ent, target_tuple, max_iter, flyback, extra_removed)
    cached = FLOOR_SEARCH_CACHE.get(key)
    if cached is not None:
        FLOOR_SEARCH_CACHE_STATS["hits"] += 1
        FLOOR_SEARCH_CACHE_STATS["iters_reused"] += cached[1] if cached else 0
        return cached
    FLOOR_SEARCH_CACHE_STATS["misses"] += 1
    result = _UNCACHED_SEARCH_FLOOR(
        maps,
        fid,
        ent,
        list(target_tuple),
        max_iter=max_iter,
        flyback=flyback,
        extra_removed=extra_removed,
    )
    FLOOR_SEARCH_CACHE_STATS["iters_searched"] += result[1] if result else 0
    if FLOOR_SEARCH_CACHE_LIMIT <= 0 or len(FLOOR_SEARCH_CACHE) < FLOOR_SEARCH_CACHE_LIMIT:
        FLOOR_SEARCH_CACHE[key] = result
        FLOOR_SEARCH_CACHE_STATS["stores"] += 1
    else:
        FLOOR_SEARCH_CACHE_STATS["skipped_limit"] += 1
    return result


def load_floor_search_cache(path: str) -> None:
    if not path or not os.path.exists(path):
        return
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        FLOOR_SEARCH_CACHE_STATS["disk_load_failed"] += 1
        return
    if data.get("version") != FLOOR_SEARCH_CACHE_VERSION:
        FLOOR_SEARCH_CACHE_STATS["disk_version_ignored"] += 1
        return
    loaded = 0
    for key, row in data.get("entries", {}).items():
        if FLOOR_SEARCH_CACHE_LIMIT > 0 and len(FLOOR_SEARCH_CACHE) >= FLOOR_SEARCH_CACHE_LIMIT:
            FLOOR_SEARCH_CACHE_STATS["disk_load_skipped_limit"] += 1
            break
        FLOOR_SEARCH_CACHE[key] = deserialize_floor_search_result(row)
        loaded += 1
    FLOOR_SEARCH_CACHE_STATS["disk_loaded"] += loaded


def save_floor_search_cache(path: str) -> None:
    if not FLOOR_SEARCH_CACHE_ENABLED or not path:
        return
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    entries = {
        key: serialize_floor_search_result(result)
        for key, result in FLOOR_SEARCH_CACHE.items()
    }
    write_json_with_retry(
        path,
        {
            "version": FLOOR_SEARCH_CACHE_VERSION,
            "entries": entries,
        },
        indent=None,
        separators=(",", ":"),
    )
    FLOOR_SEARCH_CACHE_STATS["disk_saved"] = len(entries)


def write_json_with_retry(
    path: str,
    data: Any,
    *,
    indent: int | None = 2,
    separators: tuple[str, str] | None = None,
    attempts: int = 3,
) -> None:
    """Write JSON with a short retry for transient Windows file-handle errors."""
    last_error: OSError | None = None
    for attempt in range(attempts):
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(
                    data,
                    f,
                    ensure_ascii=False,
                    indent=indent,
                    separators=separators,
                )
            return
        except OSError as exc:
            last_error = exc
            if attempt + 1 >= attempts:
                break
            time.sleep(1.0)
    assert last_error is not None
    raise last_error


def configure_floor_search_cache(enabled: bool, limit: int, path: str = "") -> None:
    """Install or remove the exact floor-search cache for this run."""
    global FLOOR_SEARCH_CACHE_ENABLED, FLOOR_SEARCH_CACHE_LIMIT, FLOOR_SEARCH_CACHE_PATH
    FLOOR_SEARCH_CACHE_ENABLED = enabled
    FLOOR_SEARCH_CACHE_LIMIT = limit
    FLOOR_SEARCH_CACHE_PATH = path
    FLOOR_SEARCH_CACHE.clear()
    FLOOR_SEARCH_CACHE_STATS.clear()
    if enabled:
        load_floor_search_cache(path)
    gw.search_floor = cached_search_floor if enabled else _UNCACHED_SEARCH_FLOOR
    # auto.gw is the same module object, but assign explicitly for readability.
    auto.gw.search_floor = gw.search_floor


def floor_search_cache_compact() -> dict[str, Any]:
    return {
        "enabled": FLOOR_SEARCH_CACHE_ENABLED,
        "limit": FLOOR_SEARCH_CACHE_LIMIT,
        "path": FLOOR_SEARCH_CACHE_PATH or None,
        "entries": len(FLOOR_SEARCH_CACHE),
        **dict(sorted(FLOOR_SEARCH_CACHE_STATS.items())),
    }


def remaining_gem_count(ent: dict[str, Any], eid: str) -> int:
    return sum(
        target.eid == eid and target.pos not in auto.collected_for(ent, target.fid)
        for target in auto.TARGETS
    )


def stat_gem_mask(ent: dict[str, Any]) -> int:
    mask = 0
    for idx, (fid, pos, _eid) in enumerate(STAT_GEM_TARGETS):
        if pos in auto.collected_for(ent, fid):
            mask |= 1 << idx
    return mask


def stat_gem_count(ent: dict[str, Any]) -> int:
    return stat_gem_mask(ent).bit_count()


def gem_mask_summary(entries: Iterable[dict[str, Any]], limit: int = 8) -> dict[str, Any]:
    buckets: dict[tuple[int, bool], int] = defaultdict(int)
    for ent in entries:
        buckets[(stat_gem_mask(ent), "MT10" in ent.get("collected", {}))] += 1
    top = sorted(
        buckets.items(),
        key=lambda item: (-item[1], item[0][0], item[0][1]),
    )[:limit]
    return {
        "gem_targets": len(STAT_GEM_TARGETS),
        "buckets": len(buckets),
        "largest_bucket": max(buckets.values(), default=0),
        "top": [
            {"mask": hex(mask), "mt10": mt10, "count": count}
            for (mask, mt10), count in top
        ],
    }


def raw_remaining_direct_resource_value(ent: dict[str, Any]) -> int:
    """Direct value of all remaining map resources, ignoring access cost."""
    return sum(
        RAW_RESOURCE_VALUE.get(target.eid, 0)
        for target in auto.TARGETS
        if target.pos not in auto.collected_for(ent, target.fid)
    )


def audited_net_pocket_access_adjustment(ent: dict[str, Any]) -> tuple[int, list[str]]:
    """Access costs for small audited pockets left on the map.

    The value is subtracted from direct raw stock.  Keep the table small: each
    pocket must have a known mandatory access door, otherwise the result would
    stop being a safe optimistic stock bound.
    """
    total = 0
    notes: list[str] = []
    for pocket in AUDITED_NET_RESOURCE_POCKETS:
        fid = pocket["fid"]
        collected = auto.collected_for(ent, fid)
        item_value = sum(
            RAW_RESOURCE_VALUE.get(eid, 0)
            for pos, eid in pocket["items"]
            if pos not in collected
        )
        if item_value <= 0:
            continue
        door_cost = sum(
            FUTURE_DOOR_COST.get(eid, 0)
            for pos, eid in pocket["doors"]
            if pos not in collected
        )
        adjustment = min(item_value, door_cost)
        if adjustment <= 0:
            continue
        total += adjustment
        notes.append(f"{pocket['name']} -{adjustment}")
    return total, notes


def net_pocket_adjustment_value(ent: dict[str, Any]) -> int:
    return audited_net_pocket_access_adjustment(ent)[0] if NET_POCKET_RAW_STOCK_ENABLED else 0


def raw_remaining_resource_value(ent: dict[str, Any]) -> int:
    """Remaining map-resource value under the active raw-stock model."""
    direct = raw_remaining_direct_resource_value(ent)
    return direct - net_pocket_adjustment_value(ent)


def raw_final_stock(ent: dict[str, Any]) -> int:
    """HP + current key stock + remaining resource value under active model."""
    return (
        ent["hp"]
        + ent["yk"] * rg.YK_VALUE
        + ent["bk"] * rg.BK_VALUE
        + raw_remaining_resource_value(ent)
    )


def net_remaining_resource_value(ent: dict[str, Any]) -> int:
    """Recoverable remaining resource value after paying doors and monster HP."""
    value, _notes = rg.residual_resource_value(ent, ignore_monster_damage=False)
    return value


def net_final_stock(ent: dict[str, Any]) -> int:
    """HP + current key stock + recoverable remaining resource net value."""
    return (
        ent["hp"]
        + ent["yk"] * rg.YK_VALUE
        + ent["bk"] * rg.BK_VALUE
        + net_remaining_resource_value(ent)
    )


def collected_pos(ent: dict[str, Any], fid: str, pos: tuple[int, int]) -> bool:
    return pos in auto.collected_for(ent, fid)


def future_door_cost_for(
    ent: dict[str, Any],
    doors: Iterable[tuple[str, tuple[int, int], str]],
) -> int:
    """Raw value of listed future doors that have not already been opened."""
    total = 0
    for fid, pos, eid in doors:
        if collected_pos(ent, fid, pos):
            continue
        total += FUTURE_DOOR_COST[eid]
    return total


def optimistic_future_door_stock_lower_bound(ent: dict[str, Any]) -> int:
    """Door stock every successful continuation must still pay.

    Keep this deliberately conservative.  A direct MT10 floor audit shows that
    the left two yellow doors are mandatory from the MT10 entrance to the boss
    red door; right-side MT10 doors remain excluded from this lower bound.
    """
    if not RAW_STOCK_FUTURE_DOOR_BOUND_ENABLED or p9.goal(ent):
        return 0
    total = 0
    if "MT10" not in ent.get("collected", {}):
        total += future_door_cost_for(ent, MT10_ENTRY_REQUIRED_DOORS)
    if ent["rk"] < 1:
        total += future_door_cost_for(ent, MT8_REDKEY_REQUIRED_DOORS)
    total += future_door_cost_for(ent, MT10_BOSS_REQUIRED_DOORS)
    return total


def optimistic_raw_final_stock_upper_bound(ent: dict[str, Any]) -> int:
    """Optimistic final stock after paying unavoidable damage and door stock."""
    return (
        raw_final_stock(ent)
        - optimistic_remaining_damage_lower_bound(ent)
        - optimistic_future_door_stock_lower_bound(ent)
    )


def optimistic_net_final_stock_upper_bound(ent: dict[str, Any]) -> int:
    """Safe optimistic upper bound for recoverable net-stock searches."""
    return optimistic_raw_final_stock_upper_bound(ent)


def optimistic_final_resource_stock_upper_bound(ent: dict[str, Any]) -> int:
    """Safe optimistic upper bound for door-net final-resource-stock searches."""
    return optimistic_raw_final_stock_upper_bound(ent)


def optimistic_max_stats(ent: dict[str, Any]) -> tuple[int, int]:
    """Stats after hypothetically collecting every remaining gem for free."""
    return (
        ent["atk"] + remaining_gem_count(ent, "redGem"),
        ent["def"] + remaining_gem_count(ent, "blueGem"),
    )


def optimistic_redkey_damage_lower_bound(ent: dict[str, Any]) -> int:
    """Optimistic unavoidable damage still remaining on the MT8 red-key path."""
    if ent["rk"] >= 1 or p9.goal(ent):
        return 0
    atk, def_ = optimistic_max_stats(ent)
    collected = auto.collected_for(ent, "MT8")
    total = 0
    for pos, enemy in auto.REDKEY_REQUIRED_MONSTERS:
        if pos in collected:
            continue
        dmg = calc_dmg(enemy, atk, def_)
        if dmg == float("inf"):
            return 10**9
        total += int(dmg)
    return total


def optimistic_boss_damage_lower_bound(ent: dict[str, Any]) -> int:
    """Optimistic unavoidable boss damage after collecting every remaining gem."""
    if p9.goal(ent):
        return 0
    atk, def_ = optimistic_max_stats(ent)
    dmg = p9.boss_required_damage(atk, def_)
    return 10**9 if dmg == float("inf") else int(dmg)


def optimistic_remaining_damage_lower_bound(ent: dict[str, Any]) -> int:
    """Optimistic damage that every successful continuation still has to pay."""
    return optimistic_redkey_damage_lower_bound(ent) + optimistic_boss_damage_lower_bound(ent)


def collected_landmarks(ent: dict[str, Any]) -> frozenset[tuple[str, tuple[int, int] | None]]:
    """Blocks already removed from the future map, including floor reachability."""
    out: set[tuple[str, tuple[int, int] | None]] = set()
    for fid, positions in ent.get("collected", {}).items():
        out.add((fid, None))
        out.update((fid, pos) for pos in positions)
    return frozenset(out)


def monotone_intermediate_dominates(a: dict[str, Any], b: dict[str, Any]) -> bool:
    """Whether a can safely replace b for every remaining post-9 continuation."""
    a_landmarks = collected_landmarks(a)
    b_landmarks = collected_landmarks(b)
    if not b_landmarks <= a_landmarks:
        return False
    weakly_better = (
        a.get("_dmg", 0) <= b.get("_dmg", 0)
        and a.get("_yd", 0) <= b.get("_yd", 0)
        and a.get("_bd", 0) <= b.get("_bd", 0)
        and a.get("_rd", 0) <= b.get("_rd", 0)
        and a["hp"] >= b["hp"]
        and a["atk"] >= b["atk"]
        and a["def"] >= b["def"]
        and a["yk"] >= b["yk"]
        and a["bk"] >= b["bk"]
        and a["rk"] >= b["rk"]
    )
    if not weakly_better:
        return False
    return (
        a_landmarks != b_landmarks
        or a.get("_dmg", 0) < b.get("_dmg", 0)
        or a.get("_yd", 0) < b.get("_yd", 0)
        or a.get("_bd", 0) < b.get("_bd", 0)
        or a.get("_rd", 0) < b.get("_rd", 0)
        or a["hp"] > b["hp"]
        or a["atk"] > b["atk"]
        or a["def"] > b["def"]
        or a["yk"] > b["yk"]
        or a["bk"] > b["bk"]
        or a["rk"] > b["rk"]
    )


class IntermediateDominance:
    """Optional cross-signature pruning for monotone post-9 map progress."""

    def __init__(self, enabled: bool) -> None:
        self.enabled = enabled
        self.pruned: dict[str, int] = defaultdict(int)

    def filter(self, entries: Iterable[dict[str, Any]], reason: str) -> list[dict[str, Any]]:
        filtered = auto.pareto_filter(entries)
        if not self.enabled or len(filtered) <= 1:
            return filtered
        ordered = sorted(
            filtered,
            key=lambda ent: (
                ent.get("_dmg", 0),
                ent.get("_yd", 0),
                ent.get("_bd", 0),
                ent.get("_rd", 0),
                -ent["hp"],
                -ent["atk"],
                -ent["def"],
                -ent["yk"],
                -ent["bk"],
                -ent["rk"],
                -len(collected_landmarks(ent)),
            ),
        )
        kept: list[dict[str, Any]] = []
        for ent in ordered:
            if any(monotone_intermediate_dominates(old, ent) for old in kept):
                self.pruned[reason] += 1
                continue
            removed = [old for old in kept if monotone_intermediate_dominates(ent, old)]
            if removed:
                self.pruned[reason] += len(removed)
                remove_ids = {old["_id"] for old in removed}
                kept = [old for old in kept if old["_id"] not in remove_ids]
            kept.append(ent)
        return kept

    def compact(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "pruned": dict(sorted(self.pruned.items())),
        }


class StrictImproveBound:
    """Optional branch-and-bound guard for finding a strictly better boss walk."""

    def __init__(
        self,
        dmg_limit: int,
        raw_stock_limit: int = 0,
        net_stock_limit: int = 0,
        final_stock_limit: int = 0,
    ) -> None:
        self.initial_limit = dmg_limit if dmg_limit > 0 else None
        self.limit = self.initial_limit
        self.initial_raw_stock_limit = raw_stock_limit if raw_stock_limit > 0 else None
        self.raw_stock_limit = self.initial_raw_stock_limit
        self.initial_net_stock_limit = net_stock_limit if net_stock_limit > 0 else None
        self.net_stock_limit = self.initial_net_stock_limit
        self.initial_final_stock_limit = final_stock_limit if final_stock_limit > 0 else None
        self.final_stock_limit = self.initial_final_stock_limit
        self.pruned: dict[str, int] = defaultdict(int)
        self.improvements: list[int] = []
        self.raw_stock_improvements: list[int] = []
        self.net_stock_improvements: list[int] = []
        self.final_stock_improvements: list[int] = []

    def allows(self, ent: dict[str, Any], reason: str) -> bool:
        if self.limit is not None:
            optimistic_total = ent.get("_dmg", 0) + optimistic_remaining_damage_lower_bound(ent)
            if not (
                optimistic_total < self.limit
                or (p9.goal(ent) and optimistic_total <= self.limit)
            ):
                self.pruned[reason] += 1
                return False
        if self.raw_stock_limit is not None:
            optimistic_stock = optimistic_raw_final_stock_upper_bound(ent)
            if not (
                optimistic_stock > self.raw_stock_limit
                or (p9.goal(ent) and optimistic_stock >= self.raw_stock_limit)
            ):
                self.pruned[reason] += 1
                return False
        if self.net_stock_limit is not None:
            optimistic_stock = optimistic_net_final_stock_upper_bound(ent)
            if not (
                optimistic_stock > self.net_stock_limit
                or (p9.goal(ent) and optimistic_stock >= self.net_stock_limit)
            ):
                self.pruned[reason] += 1
                return False
        if self.final_stock_limit is not None:
            optimistic_stock = optimistic_final_resource_stock_upper_bound(ent)
            if not (
                optimistic_stock > self.final_stock_limit
                or (p9.goal(ent) and optimistic_stock >= self.final_stock_limit)
            ):
                self.pruned[reason] += 1
                return False
        return True

    def consider_goal(self, ent: dict[str, Any]) -> None:
        if not p9.goal(ent):
            return
        dmg = ent.get("_dmg", 0)
        if self.limit is not None and dmg < self.limit:
            self.limit = dmg
            self.improvements.append(dmg)
        stock = raw_final_stock(ent)
        if self.raw_stock_limit is not None and stock > self.raw_stock_limit:
            self.raw_stock_limit = stock
            self.raw_stock_improvements.append(stock)
        stock = net_final_stock(ent)
        if self.net_stock_limit is not None and stock > self.net_stock_limit:
            self.net_stock_limit = stock
            self.net_stock_improvements.append(stock)
        stock = rg.final_resource_stock(ent)
        if self.final_stock_limit is not None and stock > self.final_stock_limit:
            self.final_stock_limit = stock
            self.final_stock_improvements.append(stock)

    def compact(self) -> dict[str, Any]:
        raw_stock_terms = ["raw_final_stock", "redkey", "boss"]
        if RAW_STOCK_FUTURE_DOOR_BOUND_ENABLED:
            raw_stock_terms.append("future-mandatory-doors")
        if NET_POCKET_RAW_STOCK_ENABLED:
            raw_stock_terms.insert(1, "audited-net-pockets")
        return {
            "initial_limit": self.initial_limit,
            "current_limit": self.limit,
            "lower_bound": "redkey+boss",
            "initial_raw_stock_limit": self.initial_raw_stock_limit,
            "current_raw_stock_limit": self.raw_stock_limit,
            "raw_stock_future_door_bound": RAW_STOCK_FUTURE_DOOR_BOUND_ENABLED,
            "net_pocket_raw_stock": NET_POCKET_RAW_STOCK_ENABLED,
            "raw_stock_upper_bound": "-".join(raw_stock_terms),
            "improvements": self.improvements,
            "raw_stock_improvements": self.raw_stock_improvements,
            "initial_net_stock_limit": self.initial_net_stock_limit,
            "current_net_stock_limit": self.net_stock_limit,
            "net_stock_upper_bound": "raw-stock-upper-bound",
            "net_stock_improvements": self.net_stock_improvements,
            "initial_final_stock_limit": self.initial_final_stock_limit,
            "current_final_stock_limit": self.final_stock_limit,
            "final_stock_upper_bound": "raw-stock-upper-bound",
            "final_stock_improvements": self.final_stock_improvements,
            "pruned": dict(sorted(self.pruned.items())),
        }


def set_output_tag(tag: str) -> None:
    global OUT_JSON, OUT_MD, OUT_WALK
    suffix = f"_{tag}" if tag else ""
    OUT_JSON = os.path.join("outputs", "results", f"post9_gem_supply_search{suffix}.json")
    OUT_MD = os.path.join("outputs", "reports", f"post9_gem_supply_search{suffix}.md")
    OUT_WALK = os.path.join("outputs", "walkthroughs", f"walkthrough_post9_gem_supply_best_stat27{suffix}.md")


def state_text(ent: dict[str, Any]) -> str:
    return compressed.state_text(ent)


def compact_state(ent: dict[str, Any]) -> dict[str, Any]:
    row = compressed.compact(ent)
    row["stat_gem_mask"] = hex(stat_gem_mask(ent))
    row["stat_gem_count"] = stat_gem_count(ent)
    row["net_remaining_value"] = net_remaining_resource_value(ent)
    row["net_final_stock"] = net_final_stock(ent)
    direct_remaining = raw_remaining_direct_resource_value(ent)
    net_adjustment, net_notes = audited_net_pocket_access_adjustment(ent)
    row["raw_remaining_direct_value"] = direct_remaining
    row["raw_net_pocket_adjustment"] = net_adjustment if NET_POCKET_RAW_STOCK_ENABLED else 0
    if NET_POCKET_RAW_STOCK_ENABLED and net_notes:
        row["raw_net_pocket_notes"] = net_notes
    row["raw_remaining_value"] = raw_remaining_resource_value(ent)
    row["raw_final_stock"] = raw_final_stock(ent)
    row["raw_stock_upper_bound"] = optimistic_raw_final_stock_upper_bound(ent)
    return row


def phase1_state_match(ent: dict[str, Any], row: dict[str, Any]) -> bool:
    return all(ent[key] == row[key] for key in ("hp", "atk", "def", "yk", "bk", "rk")) and all(
        ent.get(f"_{key}", 0) == row[key] for key in ("dmg", "yd", "bd", "rd")
    )


def initial_phase1_state() -> dict[str, Any]:
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


def replay_phase1_candidate() -> tuple[dict[str, Any], dict[str, Any]]:
    with open(PHASE1_REPLAY_JSON, encoding="utf-8") as f:
        saved = json.load(f)
    chain = saved["phase1_candidate"]["chain"]
    return replay_phase1_chain(chain, "replay", require_old_target=True)


def replay_phase1_chain(
    chain: list[dict[str, Any]],
    source: str,
    require_old_target: bool = False,
) -> tuple[dict[str, Any], dict[str, Any]]:
    ent = initial_phase1_state()
    max_floor = 4
    for row in chain:
        fid, targets_text, travel = row["action"].split(":")
        targets = targets_text.split("+")
        flyback = travel == "fb"
        floor_no = int(fid[2:])
        new_max_floor = max_floor + 1 if "upFloor" in targets and floor_no == max_floor else max_floor
        action = (fid, targets, flyback, new_max_floor, targets)
        matches = [candidate for candidate in p1.expand_action(ent, action) if phase1_state_match(candidate, row)]
        if not matches:
            raise RuntimeError(f"phase1 replay mismatch at {row['action']}: expected {row}")
        ent = matches[0]
        max_floor = new_max_floor
    if require_old_target and not delayed.target_match(ent):
        raise RuntimeError(f"phase1 replay final mismatch: {state_text(ent)}")
    return ent, {
        "elapsed": 0.0,
        "source": source,
        "steps": len(chain),
        "label": f"phase1 {source} prefix complete",
    }


def replay_resource_phase1_candidate() -> tuple[dict[str, Any], dict[str, Any]]:
    """Replay the best 4F-9F prefix found by phase1_resource_group_search."""
    with open(PHASE1_RESOURCE_JSON, encoding="utf-8") as f:
        saved = json.load(f)
    row = saved.get("best_delayed_shape")
    if not row or not row.get("chain"):
        raise RuntimeError(f"best_delayed_shape missing from {PHASE1_RESOURCE_JSON}")
    ent, meta = replay_phase1_chain(row["chain"], "resource", require_old_target=False)
    expected = {key: row[key] for key in ("hp", "atk", "def", "yk", "bk", "rk")}
    expected.update({"dmg": row["dmg"], "yd": row["yd"], "bd": row["bd"], "rd": row["rd"]})
    actual = {
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
    }
    if actual != expected:
        raise RuntimeError(f"resource phase1 replay mismatch: expected={expected} actual={actual}")
    meta["label"] = "phase1 resource best_delayed_shape complete"
    return ent, meta


def fixed_prefix_metrics(prefix: dict[str, Any]) -> tuple[int, int, int, int]:
    dmg = yd = bd = rd = 0
    for step in prefix["steps"]:
        before = step["state_before"]["hp"]
        after = step["state_after"]["hp"]
        dmg += max(0, before - after)
        eid = step["eid"]
        if eid == "yellowDoor":
            yd += 1
        elif eid == "blueDoor":
            bd += 1
        elif eid == "redDoor":
            rd += 1
    return dmg, yd, bd, rd


def replay_fixed_prefix_candidate() -> tuple[dict[str, Any], dict[str, Any]]:
    """Replay the verified hand-written 4F-9F prefix as a post-9 search seed."""
    prefix = fixed.replay_route()
    if not prefix["ok"] or not prefix["strict_reachable"]:
        raise RuntimeError(
            "fixed shield prefix replay failed: "
            f"errors={prefix['errors']} warnings={prefix['warnings']}"
        )
    final = prefix["final_state"]
    expected = {
        "hp": 148,
        "atk": 23,
        "def": 21,
        "yk": 2,
        "bk": 1,
        "rk": 0,
    }
    actual = {key: final[key] for key in expected}
    if actual != expected:
        raise RuntimeError(f"fixed shield prefix final mismatch: expected={expected} actual={actual}")

    root = initial_phase1_state()
    collected = {
        fid: frozenset((item["x"], item["y"]) for item in positions)
        for fid, positions in prefix["collected"].items()
    }
    dmg, yd, bd, rd = fixed_prefix_metrics(prefix)
    ent = gw._make_result(
        final["hp"],
        final["yk"],
        final["bk"],
        final["rk"],
        final["atk"],
        final["def"],
        collected,
        root["_id"],
        None,
        dmg_cost=dmg,
    )
    ent["_yd"], ent["_bd"], ent["_rd"] = yd, bd, rd
    ent["_max_floor"] = 9
    ent["_action_depth"] = len(prefix["steps"])
    ent["_last_action"] = "fixed 4-9 shield prefix + MT9 red/blue gems"
    gw._entry_store[ent["_id"]].update({
        "_yd": yd,
        "_bd": bd,
        "_rd": rd,
        "_max_floor": 9,
        "_action_depth": len(prefix["steps"]),
        "_last_action": ent["_last_action"],
    })
    return ent, {
        "elapsed": 0.0,
        "source": "fixed",
        "steps": len(prefix["steps"]),
        "label": "fixed 4-9 shield prefix + MT9 red/blue gems complete",
    }


def find_phase1_candidate(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any]]:
    if args.phase1_source == "replay":
        return replay_phase1_candidate()
    if args.phase1_source == "resource":
        return replay_resource_phase1_candidate()
    if args.phase1_source == "fixed":
        return replay_fixed_prefix_candidate()
    return delayed.find_candidate(args.phase1_expansions)


def target_rank(ent: dict[str, Any], target: auto.AutoTarget, role: str) -> tuple[int, ...]:
    if role == "backbone":
        phase = 0 if target.eid == "blueGem" else 1
    else:
        phase = {
            "yellowKey": 0,
            "blueKey": 1,
            "bluePotion": 2,
            "redPotion": 3,
        }.get(target.eid, 4)
    return (
        phase,
        -auto.target_value(ent, target.eid),
        int(target.fid[2:]),
        target.pos[0],
        target.pos[1],
    )


def role_targets(
    ent: dict[str, Any],
    role: str,
    limit: int,
) -> list[auto.AutoTarget]:
    allowed = BACKBONE_EIDS if role == "backbone" else SUPPLY_EIDS
    targets: list[auto.AutoTarget] = []
    for target in auto.TARGETS:
        if target.eid not in allowed or target.pos in auto.collected_for(ent, target.fid):
            continue
        if target.eid == "redGem" and ent["atk"] >= 27:
            continue
        if target.eid == "blueGem" and ent["def"] >= 27:
            continue
        if target.eid == "yellowKey" and ent["yk"] >= 5:
            continue
        if target.eid == "blueKey" and ent["bk"] >= 2:
            continue
        targets.append(target)
    groups: dict[tuple[str, str], list[auto.AutoTarget]] = defaultdict(list)
    for target in targets:
        groups[(target.fid, target.eid)].append(target)
    for items in groups.values():
        items.sort(key=lambda target: target_rank(ent, target, role))

    group_keys = sorted(groups, key=lambda key: target_rank(ent, groups[key][0], role))
    if role in {"supply", "recovery"}:
        # A coordinate limit accidentally favors floors with many yellow keys.
        # Group selection keeps one route probe per floor / resource type and
        # reserves room for the blue-key bridge and potion alternatives.
        ordered: list[tuple[str, str]] = []
        lane_order = (
            ("bluePotion", "redPotion", "yellowKey", "blueKey")
            if role == "recovery"
            else ("yellowKey", "blueKey", "bluePotion", "redPotion")
        )
        lanes = [
            [key for key in group_keys if key[1] == eid]
            for eid in lane_order
        ]
        for lane_idx in range(max((len(lane) for lane in lanes), default=0)):
            ordered.extend(lane[lane_idx] for lane in lanes if lane_idx < len(lane))
        group_keys = ordered
    elif role == "backbone":
        ordered = []
        lanes = [
            [key for key in group_keys if key[1] == eid]
            for eid in ("blueGem", "redGem")
        ]
        for lane_idx in range(max((len(lane) for lane in lanes), default=0)):
            ordered.extend(lane[lane_idx] for lane in lanes if lane_idx < len(lane))
        group_keys = ordered
    if limit > 0:
        group_keys = group_keys[:limit]
    return [target for key in group_keys for target in groups[key]]


def free_group_edge(
    base: dict[str, Any],
    fid: str,
    items: list[topo.ResourceItem],
) -> dict[str, Any]:
    hp, yk, bk, rk, atk, def_ = (
        base["hp"],
        base["yk"],
        base["bk"],
        base["rk"],
        base["atk"],
        base["def"],
    )
    for item in items:
        hp, yk, bk, rk, atk, def_ = compressed.add_item_to_state(
            hp, yk, bk, rk, atk, def_, item.eid
        )
    before = auto.collected_for(base, fid)
    consumed = {item.pos for item in items}
    nc = dict(base.get("collected", {}))
    nc[fid] = before | frozenset(consumed)
    edge = gw._make_result(
        hp,
        yk,
        bk,
        rk,
        atk,
        def_,
        nc,
        base["_id"],
        (fid, [item.eid for item in items], True),
        dmg_cost=0,
    )
    edge["_last_action"] = f"{compressed.group_label(fid, items)} flyback=True [free]"
    edge["_edge_fid"] = fid
    edge["_resource_group"] = compressed.describe_group(fid, before, consumed)
    edge["_via_targets"] = compressed.group_via_targets(items)
    if rk > base["rk"]:
        edge["_edge_kind"] = "redkey"
    elif atk > base["atk"] or def_ > base["def"]:
        edge["_edge_kind"] = "stat"
    elif yk > base["yk"] or bk > base["bk"]:
        edge["_edge_kind"] = "key"
    elif hp > base["hp"]:
        edge["_edge_kind"] = "potion"
    else:
        edge["_edge_kind"] = "other"
    compressed.annotate_dynamic(base, edge)
    compressed.annotate_major_order(base, edge)
    compressed.store_metadata(
        edge,
        (
            "_last_action",
            "_edge_fid",
            "_resource_group",
            "_via_targets",
            "_edge_kind",
            "_delta_hp",
            "_delta_dmg",
            "_delta_yd",
            "_delta_bd",
            "_delta_rd",
            "_delta_yk",
            "_delta_bk",
            "_delta_rk",
            "_delta_atk",
            "_delta_def",
            "_dynamic_value",
            "_dynamic_cost",
            "_dynamic_net",
            "_dynamic_efficiency",
            "_dynamic_total",
            "_major_order",
        ),
    )
    return edge


def saturate_initial_free_resources(ent: dict[str, Any], max_iter: int) -> dict[str, Any]:
    """Collect zero-cost cross-floor supply groups once at the post-9 boundary.

    A static flood fill misses fake-wall and entrance details on a few floors.
    The authoritative floor search is cheap enough to run once for the delayed
    prefix.  Later paid edges already collect their same-floor zero-cost pocket.
    """
    edges = role_edges(ent, "supply", target_limit=0, edge_limit=0, max_iter=max_iter)
    free_edges = [
        edge for edge in edges
        if edge.get("_delta_dmg", 0) == 0
        and edge.get("_delta_yd", 0) == 0
        and edge.get("_delta_bd", 0) == 0
        and edge.get("_delta_rd", 0) == 0
        and (
            edge.get("_delta_hp", 0) > 0
            or edge.get("_delta_yk", 0) > 0
            or edge.get("_delta_bk", 0) > 0
        )
    ]
    if not free_edges:
        return ent

    nc = {fid: frozenset(pos) for fid, pos in ent.get("collected", {}).items()}
    for edge in free_edges:
        for fid, positions in edge.get("collected", {}).items():
            nc[fid] = frozenset(set(nc.get(fid, frozenset())) | set(positions))

    items: list[tuple[str, topo.ResourceItem]] = []
    for fid, positions in nc.items():
        before = auto.collected_for(ent, fid)
        for x, y, t, eid in gw.maps[fid]["bl"]:
            if t == 3 and eid in compressed.RESOURCE_IDS and (x, y) in positions and (x, y) not in before:
                items.append((fid, topo.ResourceItem((x, y), eid)))
    if not items:
        return ent

    hp, yk, bk, rk, atk, def_ = ent["hp"], ent["yk"], ent["bk"], ent["rk"], ent["atk"], ent["def"]
    for _fid, item in items:
        hp, yk, bk, rk, atk, def_ = compressed.add_item_to_state(
            hp, yk, bk, rk, atk, def_, item.eid
        )
    edge = gw._make_result(
        hp,
        yk,
        bk,
        rk,
        atk,
        def_,
        nc,
        ent["_id"],
        None,
        dmg_cost=0,
    )
    edge["_last_action"] = "post9 free supply saturation: " + "+".join(
        f"{fid} x{item.pos[0]}y{item.pos[1]} {item.eid}"
        for fid, item in items
    )
    edge["_edge_fid"] = "MULTI"
    edge["_resource_group"] = {
        "items": [
            {"pos": f"{fid} x{item.pos[0]}y{item.pos[1]}", "eid": item.eid, "name": item.eid}
            for fid, item in items
        ],
        "doors": [],
        "monsters": [],
    }
    edge["_via_targets"] = sorted({item.eid for _fid, item in items})
    edge["_edge_kind"] = "key" if yk > ent["yk"] or bk > ent["bk"] else "potion"
    compressed.annotate_dynamic(ent, edge)
    compressed.annotate_major_order(ent, edge)
    compressed.store_metadata(
        edge,
        (
            "_last_action",
            "_edge_fid",
            "_resource_group",
            "_via_targets",
            "_edge_kind",
            "_delta_hp",
            "_delta_dmg",
            "_delta_yd",
            "_delta_bd",
            "_delta_rd",
            "_delta_yk",
            "_delta_bk",
            "_delta_rk",
            "_delta_atk",
            "_delta_def",
            "_dynamic_value",
            "_dynamic_cost",
            "_dynamic_net",
            "_dynamic_efficiency",
            "_dynamic_total",
            "_major_order",
        ),
    )
    return edge


def role_edges(
    ent: dict[str, Any],
    role: str,
    target_limit: int,
    edge_limit: int,
    max_iter: int,
) -> list[dict[str, Any]]:
    by_floor_eid: dict[tuple[str, str], set[tuple[int, int]]] = defaultdict(set)
    for target in role_targets(ent, role, target_limit):
        by_floor_eid[(target.fid, target.eid)].add(target.pos)

    full_edges: list[dict[str, Any]] = []
    for (fid, eid), positions in sorted(
        by_floor_eid.items(),
        key=lambda item: (int(item[0][0][2:]), item[0][1]),
    ):
        full_edges.extend(auto.exact_item_edges(ent, fid, eid, positions, max_iter=max_iter))
    if role == "backbone" and atomic.mt10_progress_allowed(ent):
        full_edges.extend(auto.progress_edges(ent, max_iter=max_iter))

    dedup: dict[tuple[Any, ...], dict[str, Any]] = {}
    for full_edge in full_edges:
        edge = compressed.make_compressed_edge(ent, full_edge, max_iter=max_iter)
        if not edge:
            continue
        sig = auto.result_signature(edge)
        old = dedup.get(sig)
        if old is None or compressed.edge_sort_key(edge, "dynamic") < compressed.edge_sort_key(old, "dynamic"):
            dedup[sig] = edge

    ranked = sorted(dedup.values(), key=lambda edge: compressed.edge_sort_key(edge, "dynamic"))
    if edge_limit <= 0 or len(ranked) <= edge_limit:
        return ranked

    chosen: list[dict[str, Any]] = []
    seen: set[int] = set()

    def add(items: Iterable[dict[str, Any]], quota: int) -> None:
        added = 0
        for edge in items:
            if edge["_id"] in seen:
                continue
            seen.add(edge["_id"])
            chosen.append(edge)
            added += 1
            if added >= quota or len(chosen) >= edge_limit:
                return

    add(
        sorted(
            ranked,
            key=lambda edge: (
                edge.get("_delta_dmg", 0),
                edge.get("_delta_yd", 0),
                edge.get("_delta_bd", 0),
                -edge.get("_delta_yk", 0),
                -edge.get("_delta_bk", 0),
                -edge.get("_delta_hp", 0),
            ),
        ),
        max(2, edge_limit // 3),
    )
    add([edge for edge in ranked if edge.get("_edge_kind") == "progress"], 2)
    add([edge for edge in ranked if edge.get("_edge_kind") == "stat"], max(3, edge_limit // 2))
    add([edge for edge in ranked if edge.get("_edge_kind") == "key"], max(2, edge_limit // 3))
    add([edge for edge in ranked if edge.get("_edge_kind") == "potion"], max(2, edge_limit // 3))
    add(ranked, edge_limit)
    return chosen[:edge_limit]


def backbone_target_edges(
    ent: dict[str, Any],
    target: auto.AutoTarget,
    max_iter: int,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    full_edges = auto.exact_item_edges(ent, target.fid, target.eid, {target.pos}, max_iter=max_iter)
    for full_edge in full_edges:
        edge = compressed.make_compressed_edge(ent, full_edge, max_iter=max_iter)
        if not edge:
            continue
        edge["_backbone_target"] = f"{target.fid}:x{target.pos[0]}y{target.pos[1]}:{target.eid}"
        gw._entry_store[edge["_id"]]["_backbone_target"] = edge["_backbone_target"]
        out.append(edge)
    return out


def advance_backbone_target(
    base: dict[str, Any],
    target: auto.AutoTarget,
    bridge_depth: int,
    bridge_width: int,
    max_iter: int,
) -> list[dict[str, Any]]:
    """Follow one gem target through incidental compressed resource pockets."""
    frontier = [base]
    reached: list[dict[str, Any]] = []
    for _depth in range(bridge_depth + 1):
        next_frontier: list[dict[str, Any]] = []
        for ent in frontier:
            for edge in backbone_target_edges(ent, target, max_iter=max_iter):
                if edge["atk"] > base["atk"] or edge["def"] > base["def"]:
                    reached.append(edge)
                else:
                    next_frontier.append(edge)
        if not next_frontier:
            break
        frontier = select_supply_representatives(base, next_frontier, bridge_width)
    return reached


def backbone_edges(
    ent: dict[str, Any],
    target_limit: int,
    edge_limit: int,
    bridge_depth: int,
    bridge_width: int,
    max_iter: int,
    efficiency_prune: bool = False,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for target in role_targets(ent, "backbone", target_limit):
        out.extend(
            advance_backbone_target(
                ent,
                target,
                bridge_depth=bridge_depth,
                bridge_width=bridge_width,
                max_iter=max_iter,
            )
        )
    if atomic.mt10_progress_allowed(ent):
        for full_edge in auto.progress_edges(ent, max_iter=max_iter):
            edge = compressed.make_compressed_edge(ent, full_edge, max_iter=max_iter)
            if edge:
                out.append(edge)

    dedup: dict[tuple[Any, ...], dict[str, Any]] = {}
    for edge in out:
        # Keep the outer source order so frontier trimming can preserve
        # multiple useful continuations from the same careful prefix.
        edge["_outer_parent_order"] = tuple(ent.get("_major_order", ()))
        sig = auto.result_signature(edge)
        old = dedup.get(sig)
        if old is None or compressed.edge_sort_key(edge, "dynamic") < compressed.edge_sort_key(old, "dynamic"):
            dedup[sig] = edge
    ranked = sorted(dedup.values(), key=lambda edge: compressed.edge_sort_key(edge, "dynamic"))
    if edge_limit <= 0 or len(ranked) <= edge_limit:
        return ranked

    chosen: list[dict[str, Any]] = []
    seen: set[int] = set()

    def add(items: Iterable[dict[str, Any]], quota: int) -> None:
        added = 0
        for edge in items:
            if edge["_id"] in seen:
                continue
            seen.add(edge["_id"])
            chosen.append(edge)
            added += 1
            if added >= quota or len(chosen) >= edge_limit:
                return

    add(
        sorted(
            ranked,
            key=lambda edge: (
                edge.get("_delta_dmg", 0),
                edge.get("_delta_yd", 0),
                edge.get("_delta_bd", 0),
                p9.stat_deficit(edge),
                -edge["def"],
                -edge["atk"],
            ),
        ),
        max(3, edge_limit // 2),
    )
    if efficiency_prune:
        add(
            sorted(
                [edge for edge in ranked if edge.get("_edge_kind") == "stat"],
                key=stat_edge_efficiency_priority,
            ),
            max(3, edge_limit // 2),
        )
    add([edge for edge in ranked if edge.get("_edge_kind") == "progress"], 2)
    add([edge for edge in ranked if edge.get("_edge_kind") == "stat"], edge_limit)
    add(ranked, edge_limit)
    return chosen[:edge_limit]


def select_supply_representatives(
    base: dict[str, Any],
    entries: list[dict[str, Any]],
    limit: int,
    package_dp: bool = False,
    package_per_bucket: int = 1,
    dominance_prune: bool = False,
    net_stock_dominance: bool = False,
) -> list[dict[str, Any]]:
    """Keep no-detour, minimum-cost, reserve-key, and reserve-HP variants."""
    filtered = auto.pareto_filter(entries)
    if dominance_prune:
        filtered = prune_supply_dominated_packages(
            base,
            filtered,
            net_stock_dominance=net_stock_dominance,
        )
    if limit <= 0 or len(filtered) <= limit:
        return filtered
    if package_dp:
        filtered = select_supply_package_representatives(
            base,
            filtered,
            limit,
            package_per_bucket,
        )
        if len(filtered) <= limit:
            return filtered

    chosen: list[dict[str, Any]] = []
    seen: set[int] = set()

    def add(items: Iterable[dict[str, Any]], quota: int) -> None:
        added = 0
        for ent in items:
            if ent["_id"] in seen:
                continue
            seen.add(ent["_id"])
            chosen.append(ent)
            added += 1
            if added >= quota or len(chosen) >= limit:
                return

    add([base], 1)
    orders = [
        lambda ent: (
            ent.get("_dmg", 0) - base.get("_dmg", 0),
            ent.get("_yd", 0) - base.get("_yd", 0),
            ent.get("_bd", 0) - base.get("_bd", 0),
            -ent["yk"],
            -ent["bk"],
            -ent["hp"],
        ),
        lambda ent: (
            -ent["yk"],
            ent.get("_yd", 0) - base.get("_yd", 0),
            ent.get("_dmg", 0) - base.get("_dmg", 0),
            -ent["bk"],
            -ent["hp"],
        ),
        lambda ent: (
            -ent["bk"],
            ent.get("_bd", 0) - base.get("_bd", 0),
            ent.get("_yd", 0) - base.get("_yd", 0),
            ent.get("_dmg", 0) - base.get("_dmg", 0),
            -ent["yk"],
            -ent["hp"],
        ),
        lambda ent: (
            -ent["hp"],
            ent.get("_yd", 0) - base.get("_yd", 0),
            ent.get("_bd", 0) - base.get("_bd", 0),
            ent.get("_dmg", 0) - base.get("_dmg", 0),
            -ent["yk"],
            -ent["bk"],
        ),
        lambda ent: (
            rg.resource_group_score(ent),
            ent.get("_dmg", 0),
            ent.get("_yd", 0),
            ent.get("_bd", 0),
            -ent["yk"],
            -ent["bk"],
            -ent["hp"],
        ),
    ]
    quota = max(1, limit // len(orders))
    for order in orders:
        add(sorted(filtered, key=order), quota)
    add(sorted(filtered, key=orders[0]), limit)
    return chosen[:limit]


def supply_hp_bucket(delta_hp: int) -> int:
    if delta_hp <= 0:
        return 0
    if delta_hp <= 50:
        return 1
    if delta_hp <= 200:
        return 2
    if delta_hp <= 400:
        return 3
    return 4


def supply_package_key(base: dict[str, Any], ent: dict[str, Any]) -> tuple[int, int, int]:
    return (
        min(6, max(0, ent["yk"] - base["yk"])),
        min(3, max(0, ent["bk"] - base["bk"])),
        supply_hp_bucket(ent["hp"] - base["hp"]),
    )


def supply_package_priority(base: dict[str, Any], ent: dict[str, Any]) -> tuple[int, ...]:
    return (
        ent.get("_dmg", 0) - base.get("_dmg", 0),
        ent.get("_yd", 0) - base.get("_yd", 0),
        ent.get("_bd", 0) - base.get("_bd", 0),
        -ent["yk"],
        -ent["bk"],
        -ent["hp"],
        rg.resource_group_score(ent),
    )


def _stat_threshold_bucket(atk: int) -> int:
    if atk < 26:
        return 0
    if atk == 26:
        return 1
    return 2


def _progress_flags(ent: dict[str, Any]) -> tuple[int, int, int, int]:
    return (
        1 if "MT10" in ent.get("collected", {}) else 0,
        1 if ent["rk"] >= 1 else 0,
        1 if ent.get("_rd", 0) >= 1 else 0,
        1 if p9.goal(ent) else 0,
    )


def _supply_bucket(base: dict[str, Any], ent: dict[str, Any]) -> tuple[Any, ...]:
    """State bucket where package dominance is allowed to compare entries.

    Resource gains stay out of this key on purpose: a +2 YK low-cost package
    should be allowed to dominate a +1 YK high-cost package.  The actual
    dominance check below still requires ATK/DEF/keys/HP to be no worse.
    """
    return (
        _stat_threshold_bucket(min(base["atk"], 27)),
        min(base["def"], 27),
        _progress_flags(ent),
    )


def _delta_costs(base: dict[str, Any], ent: dict[str, Any]) -> tuple[int, int, int, int]:
    return (
        ent.get("_dmg", 0) - base.get("_dmg", 0),
        ent.get("_yd", 0) - base.get("_yd", 0),
        ent.get("_bd", 0) - base.get("_bd", 0),
        ent.get("_rd", 0) - base.get("_rd", 0),
    )


def supply_package_dominates(
    base: dict[str, Any],
    a: dict[str, Any],
    b: dict[str, Any],
    *,
    net_stock_dominance: bool = False,
) -> bool:
    """Return True when supply package A safely replaces B in the same bucket."""
    if _supply_bucket(base, a) != _supply_bucket(base, b):
        return False
    if any(x < y for x, y in zip(_progress_flags(a), _progress_flags(b))):
        return False
    cost_a = _delta_costs(base, a)
    cost_b = _delta_costs(base, b)
    if net_stock_dominance:
        if cost_a[0] > cost_b[0] or cost_a[3] > cost_b[3]:
            return False
    elif any(x > y for x, y in zip(cost_a, cost_b)):
        return False
    if not (
        a["hp"] >= b["hp"]
        and a["atk"] >= b["atk"]
        and a["def"] >= b["def"]
        and a["yk"] >= b["yk"]
        and a["bk"] >= b["bk"]
        and a["rk"] >= b["rk"]
    ):
        return False
    if net_stock_dominance and raw_final_stock(a) < raw_final_stock(b):
        return False
    return (
        (cost_a[0] < cost_b[0])
        or (not net_stock_dominance and any(x < y for x, y in zip(cost_a[1:], cost_b[1:])))
        or (net_stock_dominance and raw_final_stock(a) > raw_final_stock(b))
        or a["hp"] > b["hp"]
        or a["atk"] > b["atk"]
        or a["def"] > b["def"]
        or a["yk"] > b["yk"]
        or a["bk"] > b["bk"]
        or a["rk"] > b["rk"]
    )


def prune_supply_dominated_packages(
    base: dict[str, Any],
    entries: Iterable[dict[str, Any]],
    *,
    net_stock_dominance: bool = False,
) -> list[dict[str, Any]]:
    """Cross-signature supply dominance within narrow stat/resource buckets."""
    ordered = sorted(entries, key=lambda ent: (_supply_bucket(base, ent), supply_package_priority(base, ent)))
    kept: list[dict[str, Any]] = []
    for ent in ordered:
        if any(
            supply_package_dominates(
                base,
                old,
                ent,
                net_stock_dominance=net_stock_dominance,
            )
            for old in kept
        ):
            SUPPLY_DOMINANCE_STATS["pruned"] += 1
            if net_stock_dominance:
                SUPPLY_DOMINANCE_STATS["net_stock_pruned"] += 1
            continue
        before = len(kept)
        kept = [
            old
            for old in kept
            if not supply_package_dominates(
                base,
                ent,
                old,
                net_stock_dominance=net_stock_dominance,
            )
        ]
        SUPPLY_DOMINANCE_STATS["pruned"] += before - len(kept)
        if net_stock_dominance:
            SUPPLY_DOMINANCE_STATS["net_stock_pruned"] += before - len(kept)
        kept.append(ent)
    SUPPLY_DOMINANCE_STATS["input"] += len(ordered)
    SUPPLY_DOMINANCE_STATS["output"] += len(kept)
    return kept


def select_supply_package_representatives(
    base: dict[str, Any],
    entries: list[dict[str, Any]],
    limit: int,
    package_per_bucket: int,
) -> list[dict[str, Any]]:
    """Keep Pareto representatives for each net key/HP supply package.

    This approximates the human "try +1/+2/+3/+4 keys" comparison without
    claiming that different collected signatures are interchangeable.  The
    authoritative Pareto filter still runs first; this selector only decides
    which package buckets survive a bounded beam.
    """
    buckets: dict[tuple[int, int, int], list[dict[str, Any]]] = defaultdict(list)
    for ent in entries:
        buckets[supply_package_key(base, ent)].append(ent)

    out: list[dict[str, Any]] = []
    per_bucket = max(1, package_per_bucket)
    for key, bucket in sorted(buckets.items()):
        bucket_entries = sorted(auto.pareto_filter(bucket), key=lambda ent: supply_package_priority(base, ent))
        out.extend(bucket_entries[:per_bucket])
    if len(out) <= limit:
        return out

    chosen: list[dict[str, Any]] = []
    seen: set[int] = set()

    def add(items: Iterable[dict[str, Any]], quota: int) -> None:
        added = 0
        for ent in items:
            if ent["_id"] in seen:
                continue
            seen.add(ent["_id"])
            chosen.append(ent)
            added += 1
            if added >= quota or len(chosen) >= limit:
                return

    # First give each distinct package a chance, then fill by cost.
    package_heads = []
    seen_packages: set[tuple[int, int, int]] = set()
    for ent in sorted(out, key=lambda item: (supply_package_key(base, item), supply_package_priority(base, item))):
        key = supply_package_key(base, ent)
        if key in seen_packages:
            continue
        seen_packages.add(key)
        package_heads.append(ent)
    add(package_heads, limit)
    add(sorted(out, key=lambda ent: supply_package_priority(base, ent)), limit)
    return chosen[:limit]


def supply_closure(
    base: dict[str, Any],
    depth: int,
    width: int,
    target_limit: int,
    edge_limit: int,
    max_iter: int,
    role: str = "supply",
    package_dp: bool = False,
    package_per_bucket: int = 1,
    dominance_prune: bool = False,
    net_stock_dominance: bool = False,
) -> tuple[list[dict[str, Any]], int]:
    entries = [base]
    frontier = [base]
    expanded: set[int] = set()
    generated = 0
    for _depth in range(depth):
        new_entries: list[dict[str, Any]] = []
        for ent in frontier:
            if ent["_id"] in expanded:
                continue
            expanded.add(ent["_id"])
            edges = role_edges(
                ent,
                role,
                target_limit=target_limit,
                edge_limit=edge_limit,
                max_iter=max_iter,
            )
            generated += len(edges)
            new_entries.extend(edges)
        if not new_entries:
            break
        entries = select_supply_representatives(
            base,
            entries + new_entries,
            width,
            package_dp=package_dp,
            package_per_bucket=package_per_bucket,
            dominance_prune=dominance_prune,
            net_stock_dominance=net_stock_dominance,
        )
        kept = {ent["_id"] for ent in entries}
        frontier = [ent for ent in new_entries if ent["_id"] in kept and ent["_id"] not in expanded]
    return (
        select_supply_representatives(
            base,
            entries,
            width,
            package_dp=package_dp,
            package_per_bucket=package_per_bucket,
            dominance_prune=dominance_prune,
            net_stock_dominance=net_stock_dominance,
        ),
        generated,
    )


def final_transition_edges(
    ent: dict[str, Any],
    stage: str,
    bridge_depth: int,
    bridge_width: int,
    max_iter: int,
) -> list[dict[str, Any]]:
    """Try the stage transition while exposing incidental resource pockets."""
    if stage == "boss":
        out: list[dict[str, Any]] = []
        for full_edge in auto.boss_edges(ent):
            edge = compressed.make_compressed_edge(ent, full_edge, max_iter=max_iter)
            if edge:
                out.append(edge)
        return out

    if stage != "redkey":
        raise ValueError(stage)
    target = auto.AutoTarget("MT8", next(iter(auto.item_positions("MT8", "redKey"))), "redKey")
    frontier = [ent]
    reached: list[dict[str, Any]] = []
    for _depth in range(bridge_depth + 1):
        next_frontier: list[dict[str, Any]] = []
        for base in frontier:
            full_edges = auto.exact_item_edges(
                base,
                target.fid,
                target.eid,
                {target.pos},
                max_iter=max_iter,
            )
            for full_edge in full_edges:
                edge = compressed.make_compressed_edge(base, full_edge, max_iter=max_iter)
                if not edge:
                    continue
                if edge["rk"] > ent["rk"]:
                    reached.append(edge)
                else:
                    next_frontier.append(edge)
        if not next_frontier:
            break
        frontier = select_supply_representatives(ent, next_frontier, bridge_width)
    return reached


def final_stage_goal(stage: str, ent: dict[str, Any]) -> bool:
    if stage == "redkey":
        return ent["rk"] >= 1
    if stage == "boss":
        return p9.goal(ent)
    raise ValueError(stage)


def final_stage_priority(stage: str, ent: dict[str, Any]) -> tuple[int, ...]:
    if stage == "redkey":
        return (
            0 if ent["rk"] >= 1 else 1,
            auto.redkey_survival_deficit(ent) if ent["rk"] < 1 else 0,
            ent.get("_dmg", 0),
            ent.get("_yd", 0),
            ent.get("_bd", 0),
            -ent["yk"],
            -ent["bk"],
            -ent["hp"],
        )
    if stage == "boss":
        return (
            0 if p9.goal(ent) else 1,
            p9.boss_survival_deficit(ent),
            ent.get("_dmg", 0),
            ent.get("_yd", 0),
            ent.get("_bd", 0),
            -ent["yk"],
            -ent["bk"],
            -ent["hp"],
        )
    raise ValueError(stage)


def select_final_frontier(
    stage: str,
    entries: list[dict[str, Any]],
    limit: int,
) -> list[dict[str, Any]]:
    filtered = auto.pareto_filter(entries)
    if limit <= 0 or len(filtered) <= limit:
        return sorted(filtered, key=lambda ent: final_stage_priority(stage, ent))

    chosen: list[dict[str, Any]] = []
    seen: set[int] = set()

    def add(items: Iterable[dict[str, Any]], quota: int) -> None:
        added = 0
        for ent in items:
            if ent["_id"] in seen:
                continue
            seen.add(ent["_id"])
            chosen.append(ent)
            added += 1
            if added >= quota or len(chosen) >= limit:
                return

    add(sorted(filtered, key=lambda ent: final_stage_priority(stage, ent)), max(3, limit // 3))
    add(
        sorted(
            filtered,
            key=lambda ent: (
                ent.get("_yd", 0),
                ent.get("_bd", 0),
                ent.get("_dmg", 0),
                -ent["yk"],
                -ent["bk"],
                -ent["hp"],
            ),
        ),
        max(2, limit // 4),
    )
    add(
        sorted(
            filtered,
            key=lambda ent: (
                ent.get("_dmg", 0),
                ent.get("_yd", 0),
                ent.get("_bd", 0),
                -rg.final_resource_stock(ent),
                -ent["yk"],
                -ent["bk"],
                -ent["hp"],
            ),
        ),
        max(2, limit // 4),
    )
    add(
        sorted(
            filtered,
            key=lambda ent: (
                -optimistic_raw_final_stock_upper_bound(ent),
                ent.get("_dmg", 0),
                ent.get("_yd", 0),
                ent.get("_bd", 0),
                -ent["yk"],
                -ent["bk"],
                -ent["hp"],
            ),
        ),
        max(2, limit // 4),
    )
    add(
        sorted(
            filtered,
            key=lambda ent: (
                -ent["hp"],
                ent.get("_yd", 0),
                ent.get("_bd", 0),
                ent.get("_dmg", 0),
                -ent["yk"],
                -ent["bk"],
            ),
        ),
        max(2, limit // 4),
    )
    add(sorted(filtered, key=lambda ent: (-ent["yk"], -ent["hp"], ent.get("_dmg", 0))), limit)
    return chosen[:limit]


def run_recovery_stage(
    stage: str,
    starts: list[dict[str, Any]],
    rounds: int,
    args: argparse.Namespace,
    bound: StrictImproveBound,
    middle: IntermediateDominance,
    expanded_state_keys: set[str] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Advance red-key / boss transitions with potion-first recovery closure."""
    expanded_state_keys = expanded_state_keys if expanded_state_keys is not None else set()
    entries = middle.filter(
        (ent for ent in starts if bound.allows(ent, f"{stage}-seed")),
        f"{stage}-seed",
    )
    frontier = select_final_frontier(
        stage,
        [
            ent for ent in entries
            if search_state_key(ent) not in expanded_state_keys
        ],
        args.final_source_limit,
    )
    rows: list[dict[str, Any]] = []
    expanded_total = 0
    for round_no in range(1, rounds + 1):
        sources = [ent for ent in frontier if not final_stage_goal(stage, ent)]
        if not sources:
            break
        new_entries: list[dict[str, Any]] = []
        closure_count = 0
        for source in sources:
            expanded_state_keys.add(search_state_key(source))
            expanded_total += 1
            transitions = final_transition_edges(
                source,
                stage,
                bridge_depth=args.final_bridge_depth,
                bridge_width=args.final_bridge_width,
                max_iter=args.max_iter,
            )
            transitions = [
                ent for ent in transitions
                if bound.allows(ent, f"{stage}-transition")
            ]
            for ent in transitions:
                bound.consider_goal(ent)
            new_entries.extend(transitions)
            needs_recovery = (
                auto.redkey_survival_deficit(source) > 0
                if stage == "redkey"
                else p9.boss_survival_deficit(source) > 0
            )
            if transitions and not needs_recovery:
                continue
            supplied, _generated = supply_closure(
                source,
                depth=args.final_supply_depth,
                width=args.final_supply_width,
                target_limit=args.final_targets,
                edge_limit=args.final_edges,
                max_iter=args.max_iter,
                role="recovery",
            )
            closure_count += max(0, len(supplied) - 1)
            for recovered in supplied:
                if recovered["_id"] == source["_id"]:
                    continue
                if not bound.allows(recovered, f"{stage}-supply"):
                    continue
                new_entries.append(recovered)
                recovered_transitions = final_transition_edges(
                    recovered,
                    stage,
                    bridge_depth=args.final_bridge_depth,
                    bridge_width=args.final_bridge_width,
                    max_iter=args.max_iter,
                )
                recovered_transitions = [
                    ent for ent in recovered_transitions
                    if bound.allows(ent, f"{stage}-transition")
                ]
                for ent in recovered_transitions:
                    bound.consider_goal(ent)
                new_entries.extend(recovered_transitions)

        entries = middle.filter(
            (
                ent for ent in entries + new_entries
                if bound.allows(ent, f"{stage}-entry")
            ),
            f"{stage}-entry",
        )
        if args.final_entry_limit > 0:
            entries = select_final_frontier(stage, entries, args.final_entry_limit)
        active_ids = {ent["_id"] for ent in entries}
        frontier = select_final_frontier(
            stage,
            [
                ent
                for ent in new_entries
                if (
                    ent["_id"] in active_ids
                    and not final_stage_goal(stage, ent)
                    and search_state_key(ent) not in expanded_state_keys
                )
            ],
            args.final_source_limit,
        )
        goals = [ent for ent in entries if final_stage_goal(stage, ent)]
        best_goal = min(goals, key=lambda ent: final_stage_priority(stage, ent)) if goals else None
        best_entry = min(entries, key=lambda ent: final_stage_priority(stage, ent)) if entries else None
        rows.append({
            "stage": stage,
            "round": round_no,
            "sources": len(sources),
            "closure": closure_count,
            "new": len(new_entries),
            "entries": len(entries),
            "goals": len(goals),
            "max_atk": max(ent["atk"] for ent in entries),
            "max_def": max(ent["def"] for ent in entries),
            "best": compressed.compact(best_goal) if best_goal else None,
            "best_entry": compressed.compact(best_entry) if best_entry else None,
        })
        print(
            f"{stage} recovery round {round_no}: sources={len(sources)} closure={closure_count} "
            f"new={len(new_entries)} entries={len(entries)} goals={len(goals)}",
            flush=True,
        )
        if best_goal:
            print(f"  best {state_text(best_goal)} stock={rg.final_resource_stock(best_goal)}", flush=True)
    return entries, rows


def goal_priority(ent: dict[str, Any]) -> tuple[int, ...]:
    return (
        ent.get("_dmg", 0),
        ent.get("_yd", 0),
        ent.get("_bd", 0),
        -ent["yk"],
        -ent["bk"],
        -ent["hp"],
    )


def raw_stock_goal_priority(ent: dict[str, Any]) -> tuple[int, ...]:
    return (
        -raw_final_stock(ent),
        ent.get("_dmg", 0),
        ent.get("_yd", 0),
        ent.get("_bd", 0),
        -ent["yk"],
        -ent["bk"],
        -ent["hp"],
    )


def net_stock_goal_priority(ent: dict[str, Any]) -> tuple[int, ...]:
    return (
        -net_final_stock(ent),
        ent.get("_dmg", 0),
        ent.get("_yd", 0),
        ent.get("_bd", 0),
        -ent["yk"],
        -ent["bk"],
        -ent["hp"],
    )


def final_stock_goal_priority(ent: dict[str, Any]) -> tuple[int, ...]:
    return (
        -rg.final_resource_stock(ent),
        rg.resource_group_score(ent),
        rg.old_score(ent),
        ent.get("_dmg", 0),
        ent.get("_yd", 0),
        ent.get("_bd", 0),
        -ent["yk"],
        -ent["bk"],
        -ent["hp"],
    )


def select_goal_carry(entries: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    """Carry representative 27/27 states into red-key and boss continuation."""
    filtered = auto.pareto_filter(entries)
    if limit <= 0 or len(filtered) <= limit:
        return sorted(filtered, key=goal_priority)

    chosen: list[dict[str, Any]] = []
    seen: set[int] = set()

    def add(items: Iterable[dict[str, Any]], quota: int) -> None:
        added = 0
        for ent in items:
            if ent["_id"] in seen:
                continue
            seen.add(ent["_id"])
            chosen.append(ent)
            added += 1
            if added >= quota or len(chosen) >= limit:
                return

    add(sorted(filtered, key=goal_priority), max(2, limit // 4))
    add(
        sorted(
            filtered,
            key=lambda ent: (
                ent.get("_yd", 0),
                ent.get("_bd", 0),
                ent.get("_dmg", 0),
                -ent["yk"],
                -ent["bk"],
                -ent["hp"],
            ),
        ),
        max(2, limit // 4),
    )
    add(
        sorted(
            filtered,
            key=lambda ent: (
                -ent["yk"],
                -ent["bk"],
                ent.get("_dmg", 0),
                ent.get("_yd", 0),
                ent.get("_bd", 0),
                -ent["hp"],
            ),
        ),
        max(2, limit // 4),
    )
    add(
        sorted(
            filtered,
            key=lambda ent: (
                -rg.final_resource_stock(ent),
                ent.get("_dmg", 0),
                ent.get("_yd", 0),
                ent.get("_bd", 0),
                -ent["hp"],
            ),
        ),
        max(2, limit // 4),
    )
    add(
        sorted(
            filtered,
            key=lambda ent: (
                -optimistic_raw_final_stock_upper_bound(ent),
                ent.get("_dmg", 0),
                ent.get("_yd", 0),
                ent.get("_bd", 0),
                -ent["yk"],
                -ent["bk"],
                -ent["hp"],
            ),
        ),
        max(2, limit // 4),
    )
    add(sorted(filtered, key=lambda ent: (-ent["hp"],) + goal_priority(ent)), limit)
    return chosen[:limit]


def supply_needed(ent: dict[str, Any]) -> bool:
    if ent["hp"] <= 120:
        return True
    if ent["yk"] <= 1:
        return True
    if p9.needs_mt10_for_stats(ent) and ent["bk"] < 1 and p9.stat_deficit(ent) <= 2:
        return True
    return p9.stat_deficit(ent) <= 2


def stat_supply_depth(ent: dict[str, Any], args: argparse.Namespace) -> int:
    """Look one bounded layer deeper when near-goal stat routes are key-starved."""
    depth = args.supply_depth
    if (
        args.stat_extra_key_supply_depth > 0
        and p9.stat_deficit(ent) <= 2
        and ent["yk"] <= 1
    ):
        depth += args.stat_extra_key_supply_depth
    return depth


def trim_backbone_frontier(
    entries: list[dict[str, Any]],
    limit: int,
    per_prefix: int,
) -> list[dict[str, Any]]:
    """Keep low-cost backbone paths plus diverse continuations.

    The stat-stage selector intentionally favors quick progress toward 27/27.
    That is useful late in the search, but it can evict a slower low-damage
    prefix before its early DEF gains pay back.  Reserve half of the beam for
    cumulative-cost leaders, then fill the remainder with parent-prefix,
    low-door, and high-DEF lanes.
    """
    filtered = auto.pareto_filter(entries)
    if limit <= 0 or len(filtered) <= limit:
        return filtered

    def cost_key(ent: dict[str, Any]) -> tuple[int, ...]:
        return (
            ent.get("_dmg", 0),
            ent.get("_yd", 0),
            ent.get("_bd", 0),
            p9.stat_deficit(ent),
            -ent["yk"],
            -ent["bk"],
            -ent["hp"],
        )

    buckets: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for ent in filtered:
        buckets[(
            tuple(ent.get("_major_order", ())),
            min(ent["yk"], 4),
            min(ent["bk"], 2),
            "MT10" in ent.get("collected", {}),
        )].append(ent)

    representatives: list[dict[str, Any]] = []
    for bucket in buckets.values():
        representatives.extend(
            sorted(
                bucket,
                key=lambda ent: (
                    ent.get("_dmg", 0),
                    ent.get("_yd", 0),
                    ent.get("_bd", 0),
                    -ent["yk"],
                    -ent["bk"],
                    -ent["hp"],
                    p9.stat_deficit(ent),
                ),
            )[:per_prefix]
        )

    parent_buckets: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for ent in representatives:
        parent_buckets[(
            tuple(ent.get("_outer_parent_order", ())),
            min(ent["yk"], 4),
            min(ent["bk"], 2),
            "MT10" in ent.get("collected", {}),
        )].append(ent)
    parent_heads: list[dict[str, Any]] = []
    for bucket in parent_buckets.values():
        parent_heads.extend(
            sorted(
                bucket,
                key=lambda ent: (
                    p9.stat_deficit(ent),
                    ent.get("_dmg", 0),
                    ent.get("_yd", 0),
                    ent.get("_bd", 0),
                    -ent["def"],
                    -ent["atk"],
                    -ent["yk"],
                    -ent["bk"],
                    -ent["hp"],
                ),
            )[:per_prefix]
        )

    stat_buckets: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for ent in representatives:
        stat_buckets[(
            min(ent["atk"], 27),
            min(ent["def"], 27),
            min(ent["yk"], 4),
            min(ent["bk"], 2),
            ent.get("_bd", 0),
            "MT10" in ent.get("collected", {}),
        )].append(ent)
    stat_heads = [min(bucket, key=cost_key) for bucket in stat_buckets.values()]

    chosen: list[dict[str, Any]] = []
    seen: set[int] = set()

    def add(items: Iterable[dict[str, Any]], quota: int) -> None:
        added = 0
        for ent in items:
            if ent["_id"] in seen:
                continue
            seen.add(ent["_id"])
            chosen.append(ent)
            added += 1
            if added >= quota or len(chosen) >= limit:
                return

    # Reserve explicit room for each lane before the stage-progress fallback.
    # With a small beam, letting the first lane consume half the frontier
    # repeatedly evicts BK-preserving / low-door routes before their delayed
    # DEF savings appear.
    lane_quota = max(2, limit // 4)
    add(sorted(representatives, key=cost_key), lane_quota)
    add(
        sorted(
            representatives,
            key=lambda ent: (
                ent.get("_bd", 0),
                ent.get("_yd", 0),
                ent.get("_dmg", 0),
                p9.stat_deficit(ent),
                -ent["bk"],
                -ent["yk"],
                -ent["hp"],
            ),
        ),
        lane_quota,
    )
    add(sorted(parent_heads, key=cost_key), lane_quota)
    add(sorted(stat_heads, key=cost_key), lane_quota)
    add(
        sorted(
            representatives,
            key=lambda ent: (
                -min(ent["def"], 27),
                p9.stat_deficit(ent),
                ent.get("_dmg", 0),
                ent.get("_yd", 0),
                ent.get("_bd", 0),
                -ent["yk"],
                -ent["bk"],
                -ent["hp"],
            ),
        ),
        lane_quota,
    )
    add(compressed.select_phased_sources(representatives, "stat27", limit), limit)
    return chosen[:limit]


def stat_paid_cost(ent: dict[str, Any]) -> int:
    return (
        ent.get("_dmg", 0)
        + ent.get("_yd", 0) * rg.YK_VALUE
        + ent.get("_bd", 0) * rg.BK_VALUE
        + ent.get("_rd", 0) * rg.RED_KEY_VALUE
    )


def _ratio(numerator: int, denominator: int, scale: int = 100) -> int:
    return (numerator * scale) // max(1, denominator)


def stat_edge_efficiency_priority(edge: dict[str, Any]) -> tuple[int, ...]:
    """Prefer stat edges whose DEF gain is bought with less immediate cost.

    This is a bounded scheduling key, not a dominance proof.  Two different
    gem pockets can leave different resources behind, so lower damage per DEF
    is only safe as a representative-selection lane.
    """
    def_gain = max(0, edge.get("_delta_def", 0))
    atk_gain = max(0, edge.get("_delta_atk", 0))
    paid_cost = (
        max(0, edge.get("_delta_dmg", 0))
        + max(0, edge.get("_delta_yd", 0)) * rg.YK_VALUE
        + max(0, edge.get("_delta_bd", 0)) * rg.BK_VALUE
        + max(0, edge.get("_delta_rd", 0)) * rg.RED_KEY_VALUE
    )
    return (
        0 if def_gain > 0 else 1,
        _ratio(paid_cost, def_gain),
        _ratio(max(0, edge.get("_delta_dmg", 0)), def_gain),
        max(0, edge.get("_delta_yd", 0)),
        max(0, edge.get("_delta_bd", 0)),
        -def_gain,
        -atk_gain,
        p9.stat_deficit(edge),
        -min(edge["def"], 27),
        -min(edge["atk"], 27),
        -edge["yk"],
        -edge["bk"],
        -edge["hp"],
    )


def stat_queue_priority(ent: dict[str, Any], heuristic_unit: int) -> tuple[int, ...]:
    """A* ordering for the compressed stat backbone.

    Opened doors are irreversible paid cost.  Key stock is used as an access
    deficit and a tie-break only: optional key pockets should not outrank the
    gem backbone before they are needed.  Pareto acceptance remains
    authoritative.
    """
    paid_cost = stat_paid_cost(ent)
    deficit = p9.stat_deficit(ent)
    near_mt10 = p9.needs_mt10_for_stats(ent) and deficit <= 2
    mt10_gap = 1 if near_mt10 and "MT10" not in ent.get("collected", {}) else 0
    access_gap = 0
    if mt10_gap:
        access_gap = max(0, 1 - ent["bk"]) + max(0, p9.desired_yk(ent) - ent["yk"])
    reached_mt10_rank = 0 if near_mt10 and "MT10" in ent.get("collected", {}) else 1
    return (
        reached_mt10_rank,
        paid_cost + deficit * heuristic_unit + mt10_gap * heuristic_unit * 6 + access_gap * heuristic_unit,
        mt10_gap,
        access_gap,
        paid_cost,
        ent.get("_bd", 0),
        ent.get("_yd", 0),
        deficit,
        -min(ent["def"], 27),
        -min(ent["atk"], 27),
        -ent["yk"],
        -ent["bk"],
        -ent["hp"],
    )


def stat_cost_lane_priority(ent: dict[str, Any]) -> tuple[int, ...]:
    """Low-paid-cost lane for delayed threshold-payoff routes."""
    return (
        stat_paid_cost(ent),
        ent.get("_bd", 0),
        ent.get("_yd", 0),
        p9.stat_deficit(ent),
        -min(ent["def"], 27),
        -min(ent["atk"], 27),
        -ent["yk"],
        -ent["bk"],
        -ent["hp"],
    )


def stat_progress_lane_priority(ent: dict[str, Any]) -> tuple[int, ...]:
    """Fast stat-growth lane for early investments with delayed payoff."""
    near_mt10 = p9.needs_mt10_for_stats(ent) and p9.stat_deficit(ent) <= 2
    return (
        0 if near_mt10 and "MT10" in ent.get("collected", {}) else 1,
        p9.stat_deficit(ent),
        -min(ent["def"], 27),
        -min(ent["atk"], 27),
        stat_paid_cost(ent),
        ent.get("_bd", 0),
        ent.get("_yd", 0),
        -ent["yk"],
        -ent["bk"],
        -ent["hp"],
    )


def stat_def_lane_priority(ent: dict[str, Any]) -> tuple[int, ...]:
    """DEF-first lane: early defense can reduce damage across many fights."""
    near_mt10 = p9.needs_mt10_for_stats(ent) and p9.stat_deficit(ent) <= 2
    return (
        0 if near_mt10 and "MT10" in ent.get("collected", {}) else 1,
        -min(ent["def"], 27),
        p9.stat_deficit(ent),
        stat_paid_cost(ent),
        -min(ent["atk"], 27),
        ent.get("_bd", 0),
        ent.get("_yd", 0),
        -ent["yk"],
        -ent["bk"],
        -ent["hp"],
    )


def stat_efficiency_lane_priority(ent: dict[str, Any]) -> tuple[int, ...]:
    """Cumulative cheap-DEF lane for the 23/21 post-9 stat phase."""
    def_gain = max(0, min(ent["def"], 27) - 21)
    atk_gain = max(0, min(ent["atk"], 27) - 23)
    paid_cost = stat_paid_cost(ent)
    return (
        0 if def_gain > 0 else 1,
        _ratio(paid_cost, def_gain),
        _ratio(ent.get("_dmg", 0), def_gain),
        ent.get("_bd", 0),
        ent.get("_yd", 0),
        p9.stat_deficit(ent),
        -def_gain,
        -atk_gain,
        -min(ent["def"], 27),
        -min(ent["atk"], 27),
        -ent["yk"],
        -ent["bk"],
        -ent["hp"],
    )


def stat_close_goal_lane_priority(ent: dict[str, Any]) -> tuple[int, ...]:
    """Near-27/27 lane for cheap states hidden behind broad paid-cost ordering."""
    return (
        p9.stat_deficit(ent),
        ent.get("_dmg", 0) + optimistic_remaining_damage_lower_bound(ent),
        ent.get("_dmg", 0),
        ent.get("_bd", 0),
        ent.get("_yd", 0),
        -ent["yk"],
        -ent["bk"],
        -ent["hp"],
    )


def stat_mask_bucket_key(ent: dict[str, Any]) -> tuple[Any, ...]:
    """Gem-set layer used for bounded frontier representation."""
    return (
        stat_gem_mask(ent),
        "MT10" in ent.get("collected", {}),
    )


def select_stat_entries(
    entries: Iterable[dict[str, Any]],
    limit: int,
    args: argparse.Namespace,
    stage: str = "stat27",
) -> list[dict[str, Any]]:
    """Trim stat entries, optionally reserving representatives per gem mask.

    This is a bounded scheduling aid, not a cross-signature dominance proof.
    Different collected signatures remain distinct; the mask is only used when
    a finite frontier has to choose which states to keep.
    """
    if not args.stat_gem_mask_frontier:
        return atomic.trim_stage(list(entries), limit, stage)
    filtered = auto.pareto_filter(entries)
    if limit <= 0 or len(filtered) <= limit:
        return sorted(filtered, key=lambda ent: stat_queue_priority(ent, args.stat_heuristic_unit))

    chosen: list[dict[str, Any]] = []
    seen: set[int] = set()

    def add(items: Iterable[dict[str, Any]], quota: int) -> None:
        added = 0
        for ent in items:
            if ent["_id"] in seen:
                continue
            seen.add(ent["_id"])
            chosen.append(ent)
            added += 1
            if added >= quota or len(chosen) >= limit:
                return

    goals = [ent for ent in filtered if atomic.stage_goal(stage, ent)]
    add(sorted(goals, key=goal_priority), max(20, limit // 5))

    buckets: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for ent in filtered:
        if atomic.stage_goal(stage, ent):
            continue
        buckets[stat_mask_bucket_key(ent)].append(ent)
    mask_heads: list[dict[str, Any]] = []
    per_bucket = max(1, args.stat_gem_mask_per_bucket)
    for bucket in buckets.values():
        ordered: list[dict[str, Any]] = []
        local_seen: set[int] = set()
        for lane in (
            sorted(bucket, key=lambda ent: stat_queue_priority(ent, args.stat_heuristic_unit)),
            sorted(bucket, key=stat_cost_lane_priority),
            sorted(bucket, key=stat_def_lane_priority),
            sorted(bucket, key=stat_efficiency_lane_priority) if args.stat_efficiency_prune else [],
            sorted(bucket, key=stat_progress_lane_priority),
        ):
            for ent in lane:
                if ent["_id"] in local_seen:
                    continue
                local_seen.add(ent["_id"])
                ordered.append(ent)
                if len(ordered) >= per_bucket:
                    break
            if len(ordered) >= per_bucket:
                break
        mask_heads.extend(ordered)

    add(
        sorted(mask_heads, key=lambda ent: stat_queue_priority(ent, args.stat_heuristic_unit)),
        max(40, limit // 2),
    )
    add(sorted(filtered, key=lambda ent: stat_queue_priority(ent, args.stat_heuristic_unit)), max(20, limit // 4))
    add(sorted(filtered, key=stat_cost_lane_priority), max(20, limit // 4))
    add(sorted(filtered, key=stat_def_lane_priority), max(20, limit // 4))
    if args.stat_efficiency_prune:
        add(sorted(filtered, key=stat_efficiency_lane_priority), max(20, limit // 4))
    add(atomic.trim_stage(filtered, limit, stage), limit)
    return chosen[:limit]


def select_deferred_stat_frontier(
    entries: Iterable[dict[str, Any]],
    limit: int,
    heuristic_unit: int,
    middle: IntermediateDominance,
    reason: str,
    args: argparse.Namespace,
    close_lane_enabled: bool = False,
) -> list[dict[str, Any]]:
    """Keep diverse unexpanded stat checkpoints for a later narrow pass."""
    dedup: dict[str, dict[str, Any]] = {}
    for ent in middle.filter(entries, reason):
        if atomic.stage_goal("stat27", ent):
            continue
        key = search_state_key(ent)
        old = dedup.get(key)
        if old is None or stat_queue_priority(ent, heuristic_unit) < stat_queue_priority(old, heuristic_unit):
            dedup[key] = ent
    filtered = list(dedup.values())
    if limit <= 0 or len(filtered) <= limit:
        return sorted(filtered, key=lambda ent: stat_queue_priority(ent, heuristic_unit))

    chosen: list[dict[str, Any]] = []
    seen: set[int] = set()

    def add(items: Iterable[dict[str, Any]], quota: int) -> None:
        added = 0
        for ent in items:
            if ent["_id"] in seen:
                continue
            seen.add(ent["_id"])
            chosen.append(ent)
            added += 1
            if added >= quota or len(chosen) >= limit:
                return

    quota = max(2, limit // (5 if close_lane_enabled else 4))
    add(sorted(filtered, key=lambda ent: stat_queue_priority(ent, heuristic_unit)), quota)
    if args.stat_gem_mask_frontier:
        mask_buckets: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
        for ent in filtered:
            mask_buckets[stat_mask_bucket_key(ent)].append(ent)
        mask_heads = [
            ent
            for bucket in mask_buckets.values()
            for ent in sorted(bucket, key=lambda item: stat_queue_priority(item, heuristic_unit))[
                : max(1, args.stat_gem_mask_per_bucket)
            ]
        ]
        add(sorted(mask_heads, key=lambda ent: stat_queue_priority(ent, heuristic_unit)), quota)
    add(sorted(filtered, key=stat_cost_lane_priority), quota)
    add(sorted(filtered, key=stat_progress_lane_priority), quota)
    add(sorted(filtered, key=stat_def_lane_priority), quota)
    if args.stat_efficiency_prune:
        add(sorted(filtered, key=stat_efficiency_lane_priority), quota)
    if close_lane_enabled:
        add(sorted(filtered, key=stat_close_goal_lane_priority), quota)
    add(sorted(filtered, key=lambda ent: stat_queue_priority(ent, heuristic_unit)), limit)
    return chosen[:limit]


def select_deferred_stat_resume(
    entries: list[dict[str, Any]],
    limit: int,
    heuristic_unit: int,
    close_goal_limit: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Mix late near-goal representatives into the next retry pass."""
    if limit <= 0 or not entries:
        return [], entries
    chosen: list[dict[str, Any]] = []
    seen: set[int] = set()

    close_quota = min(limit, max(0, close_goal_limit))
    if close_quota:
        for ent in sorted(entries, key=stat_close_goal_lane_priority):
            if ent["_id"] in seen:
                continue
            seen.add(ent["_id"])
            chosen.append(ent)
            if len(chosen) >= close_quota:
                break
    for ent in sorted(entries, key=lambda item: stat_queue_priority(item, heuristic_unit)):
        if ent["_id"] in seen:
            continue
        seen.add(ent["_id"])
        chosen.append(ent)
        if len(chosen) >= limit:
            break
    return chosen, [ent for ent in entries if ent["_id"] not in seen]


def stat_deferred_config(args: argparse.Namespace) -> dict[str, Any]:
    """Generation settings that must match before reusing expanded-state memo."""
    return {
        "phase1_source": args.phase1_source,
        "supply_policy": args.supply_policy,
        "supply_depth": args.supply_depth,
        "stat_extra_key_supply_depth": args.stat_extra_key_supply_depth,
        "stat_supply_package_dp": args.stat_supply_package_dp,
        "stat_supply_package_per_bucket": args.stat_supply_package_per_bucket,
        "supply_dominance_prune": args.supply_dominance_prune,
        "supply_net_stock_dominance": args.supply_net_stock_dominance,
        "net_pocket_raw_stock": args.net_pocket_raw_stock,
        "net_pocket_raw_stock_version": (
            NET_POCKET_RAW_STOCK_VERSION
            if args.net_pocket_raw_stock
            else 0
        ),
        "stat_gem_mask_frontier": args.stat_gem_mask_frontier,
        "stat_gem_mask_per_bucket": args.stat_gem_mask_per_bucket,
        "stat_efficiency_prune": args.stat_efficiency_prune,
        "stat_efficiency_lane_period": args.stat_efficiency_lane_period,
        "raw_stock_future_door_bound": args.raw_stock_future_door_bound,
        "raw_stock_future_door_bound_version": (
            RAW_STOCK_FUTURE_DOOR_BOUND_VERSION
            if args.raw_stock_future_door_bound
            else 0
        ),
        "supply_width": args.supply_width,
        "supply_targets": args.supply_targets,
        "supply_edges": args.supply_edges,
        "backbone_targets": args.backbone_targets,
        "backbone_edges": args.backbone_edges,
        "backbone_bridge_depth": args.backbone_bridge_depth,
        "backbone_bridge_width": args.backbone_bridge_width,
        "max_iter": args.max_iter,
    }


def deferred_snapshot(ent: dict[str, Any]) -> dict[str, Any]:
    row = {
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
        "collected": {
            fid: [list(pos) for pos in sorted(positions)]
            for fid, positions in sorted(ent.get("collected", {}).items())
        },
        "last_action": ent.get("_last_action"),
    }
    for key in DEFERRED_METADATA_KEYS:
        if key in ent:
            row[key] = ent[key]
    return row


def restore_deferred_snapshot(
    start: dict[str, Any],
    row: dict[str, Any],
) -> dict[str, Any]:
    """Restore a verified checkpoint as a compact child of the current seed."""
    collected = {
        fid: frozenset(tuple(pos) for pos in positions)
        for fid, positions in row["collected"].items()
    }
    edge = gw._make_result(
        row["hp"],
        row["yk"],
        row["bk"],
        row["rk"],
        row["atk"],
        row["def"],
        collected,
        start["_id"],
        None,
        dmg_cost=max(0, row["dmg"] - start.get("_dmg", 0)),
    )
    edge["_dmg"] = row["dmg"]
    edge["_yd"] = row["yd"]
    edge["_bd"] = row["bd"]
    edge["_rd"] = row["rd"]
    original_action = row.get("last_action") or "unknown"
    edge["_last_action"] = f"resumed deferred checkpoint after {original_action}"
    for key in DEFERRED_METADATA_KEYS:
        if key in row:
            edge[key] = tuple(row[key]) if key in {"_major_order", "_outer_parent_order"} else row[key]
    gw._entry_store[edge["_id"]].update(edge)
    return edge


def compatible_saved_bound(
    saved_limit: int | None,
    saved_raw_stock_limit: int | None,
    saved_net_stock_limit: int | None,
    saved_final_stock_limit: int | None,
    bound: StrictImproveBound,
) -> bool:
    if bound.limit is None:
        dmg_ok = saved_limit is None
    else:
        dmg_ok = saved_limit is not None and bound.limit <= saved_limit
    if bound.raw_stock_limit is None:
        raw_ok = saved_raw_stock_limit is None
    else:
        raw_ok = (
            saved_raw_stock_limit is not None
            and bound.raw_stock_limit >= saved_raw_stock_limit
        )
    if bound.net_stock_limit is None:
        net_ok = saved_net_stock_limit is None
    else:
        net_ok = (
            saved_net_stock_limit is not None
            and bound.net_stock_limit >= saved_net_stock_limit
        )
    if bound.final_stock_limit is None:
        final_ok = saved_final_stock_limit is None
    else:
        final_ok = (
            saved_final_stock_limit is not None
            and bound.final_stock_limit >= saved_final_stock_limit
        )
    return dmg_ok and raw_ok and net_ok and final_ok


def load_stat_deferred_cache(
    start: dict[str, Any],
    args: argparse.Namespace,
    bound: StrictImproveBound,
    middle: IntermediateDominance,
) -> tuple[list[dict[str, Any]], set[str], dict[str, Any]]:
    path = args.stat_deferred_cache
    status = {
        "path": path or None,
        "loaded": 0,
        "expanded_memo_loaded": 0,
        "saved": 0,
    }
    if not path or not os.path.exists(path):
        return [], set(), status
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if data.get("version") != DEFERRED_CACHE_VERSION:
        status["ignored"] = "version mismatch"
        return [], set(), status
    if data.get("root_key") != search_state_key(start):
        status["ignored"] = "root state mismatch"
        return [], set(), status

    deferred = [
        restore_deferred_snapshot(start, row)
        for row in data.get("deferred", [])
    ]
    deferred = middle.filter(
        (ent for ent in deferred if bound.allows(ent, "cache-load")),
        "stat-cache-load",
    )
    status["loaded"] = len(deferred)

    expanded_keys: set[str] = set()
    if (
        data.get("config") == stat_deferred_config(args)
        and compatible_saved_bound(
            data.get("bound_limit"),
            data.get("raw_stock_bound"),
            data.get("net_stock_bound"),
            data.get("final_stock_bound"),
            bound,
        )
    ):
        expanded_keys.update(data.get("expanded_state_keys", []))
    status["expanded_memo_loaded"] = len(expanded_keys)
    return deferred, expanded_keys, status


def save_stat_deferred_cache(
    start: dict[str, Any],
    deferred: list[dict[str, Any]],
    expanded_state_keys: set[str],
    args: argparse.Namespace,
    bound: StrictImproveBound,
    status: dict[str, Any],
) -> None:
    path = args.stat_deferred_cache
    if not path:
        return
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    rows = [deferred_snapshot(ent) for ent in deferred]
    write_json_with_retry(
        path,
        {
            "version": DEFERRED_CACHE_VERSION,
            "root_key": search_state_key(start),
            "config": stat_deferred_config(args),
            "bound_limit": bound.limit,
            "raw_stock_bound": bound.raw_stock_limit,
            "net_stock_bound": bound.net_stock_limit,
            "final_stock_bound": bound.final_stock_limit,
            "expanded_state_keys": sorted(expanded_state_keys),
            "deferred": rows,
        },
    )
    status["saved"] = len(rows)


def final_checkpoint_config(args: argparse.Namespace) -> dict[str, Any]:
    """Generation settings that must match before reusing recovery expansion memo."""
    return {
        "phase1_source": args.phase1_source,
        "final_targets": args.final_targets,
        "final_edges": args.final_edges,
        "final_supply_depth": args.final_supply_depth,
        "final_supply_width": args.final_supply_width,
        "final_bridge_depth": args.final_bridge_depth,
        "final_bridge_width": args.final_bridge_width,
        "raw_stock_future_door_bound": args.raw_stock_future_door_bound,
        "raw_stock_future_door_bound_version": (
            RAW_STOCK_FUTURE_DOOR_BOUND_VERSION
            if args.raw_stock_future_door_bound
            else 0
        ),
        "net_pocket_raw_stock": args.net_pocket_raw_stock,
        "net_pocket_raw_stock_version": (
            NET_POCKET_RAW_STOCK_VERSION
            if args.net_pocket_raw_stock
            else 0
        ),
        "max_iter": args.max_iter,
    }


def load_final_checkpoint_cache(
    start: dict[str, Any],
    args: argparse.Namespace,
    bound: StrictImproveBound,
    middle: IntermediateDominance,
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, set[str]], dict[str, Any]]:
    path = args.final_checkpoint_cache
    entries = {"redkey": [], "boss": []}
    expanded = {"redkey": set(), "boss": set()}
    status: dict[str, Any] = {
        "path": path or None,
        "loaded": {"redkey": 0, "boss": 0},
        "expanded_memo_loaded": {"redkey": 0, "boss": 0},
        "saved": {"redkey": 0, "boss": 0},
    }
    if not path or not os.path.exists(path):
        return entries, expanded, status
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if data.get("version") != DEFERRED_CACHE_VERSION:
        status["ignored"] = "version mismatch"
        return entries, expanded, status
    if data.get("root_key") != search_state_key(start):
        status["ignored"] = "root state mismatch"
        return entries, expanded, status

    reuse_expanded = (
        data.get("config") == final_checkpoint_config(args)
        and compatible_saved_bound(
            data.get("bound_limit"),
            data.get("raw_stock_bound"),
            data.get("net_stock_bound"),
            data.get("final_stock_bound"),
            bound,
        )
    )
    for stage in entries:
        saved = data.get("stages", {}).get(stage, {})
        restored = [
            restore_deferred_snapshot(start, row)
            for row in saved.get("entries", [])
        ]
        entries[stage] = middle.filter(
            (
                ent for ent in restored
                if bound.allows(ent, f"{stage}-cache-load")
            ),
            f"{stage}-cache-load",
        )
        status["loaded"][stage] = len(entries[stage])
        if reuse_expanded:
            expanded[stage].update(saved.get("expanded_state_keys", []))
        status["expanded_memo_loaded"][stage] = len(expanded[stage])
    return entries, expanded, status


def save_final_checkpoint_cache(
    start: dict[str, Any],
    entries: dict[str, list[dict[str, Any]]],
    expanded: dict[str, set[str]],
    args: argparse.Namespace,
    bound: StrictImproveBound,
    middle: IntermediateDominance,
    status: dict[str, Any],
) -> None:
    path = args.final_checkpoint_cache
    if not path:
        return
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    stages: dict[str, Any] = {}
    for stage, stage_entries in entries.items():
        kept = select_final_frontier(
            stage,
            middle.filter(stage_entries, f"{stage}-cache-save"),
            args.final_checkpoint_cache_limit,
        )
        stages[stage] = {
            "expanded_state_keys": sorted(expanded[stage]),
            "entries": [deferred_snapshot(ent) for ent in kept],
        }
        status["saved"][stage] = len(kept)
    write_json_with_retry(
        path,
        {
            "version": DEFERRED_CACHE_VERSION,
            "root_key": search_state_key(start),
            "config": final_checkpoint_config(args),
            "bound_limit": bound.limit,
            "raw_stock_bound": bound.raw_stock_limit,
            "net_stock_bound": bound.net_stock_limit,
            "final_stock_bound": bound.final_stock_limit,
            "stages": stages,
        },
    )


def run_stat_dijkstra_pass(
    starts: list[dict[str, Any]],
    args: argparse.Namespace,
    bound: StrictImproveBound,
    middle: IntermediateDominance,
    expanded_state_keys: set[str],
    pass_no: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int, int, list[dict[str, Any]]]:
    """Best-first stat search over compressed gem edges and supply closures."""
    accept, rebuild, active = compressed.accept_factory()
    heap: list[tuple[tuple[int, ...], int, int]] = []
    cost_heap: list[tuple[tuple[int, ...], int, int]] = []
    progress_heap: list[tuple[tuple[int, ...], int, int]] = []
    def_heap: list[tuple[tuple[int, ...], int, int]] = []
    efficiency_heap: list[tuple[tuple[int, ...], int, int]] = []
    close_heap: list[tuple[tuple[int, ...], int, int]] = []
    seq = 0
    expanded_ids: set[int] = set()
    rows: list[dict[str, Any]] = []
    expanded = 0
    generated = 0
    progress_generated = 0
    first_goal_expanded: int | None = None
    deferred: list[dict[str, Any]] = []

    def push(ent: dict[str, Any]) -> None:
        nonlocal seq
        seq += 1
        heapq.heappush(
            heap,
            (stat_queue_priority(ent, args.stat_heuristic_unit), seq, ent["_id"]),
        )
        heapq.heappush(cost_heap, (stat_cost_lane_priority(ent), seq, ent["_id"]))
        heapq.heappush(progress_heap, (stat_progress_lane_priority(ent), seq, ent["_id"]))
        heapq.heappush(def_heap, (stat_def_lane_priority(ent), seq, ent["_id"]))
        heapq.heappush(efficiency_heap, (stat_efficiency_lane_priority(ent), seq, ent["_id"]))
        heapq.heappush(close_heap, (stat_close_goal_lane_priority(ent), seq, ent["_id"]))

    def pop_source(lane: str) -> dict[str, Any] | None:
        selected = {
            "weighted": heap,
            "cost": cost_heap,
            "progress": progress_heap,
            "def": def_heap,
            "efficiency": efficiency_heap,
            "close": close_heap,
        }[lane]
        fallbacks = [heap, cost_heap, progress_heap, def_heap, efficiency_heap, close_heap]
        for queue in (selected, *fallbacks):
            while queue:
                _priority, _seq, ent_id = heapq.heappop(queue)
                ent = active.get(ent_id)
                if (
                    ent is None
                    or ent_id in expanded_ids
                    or search_state_key(ent) in expanded_state_keys
                    or atomic.stage_goal("stat27", ent)
                ):
                    continue
                return ent
        return None

    for start in starts:
        if bound.allows(start, "stat-seed") and accept(start):
            push(start)
    while heap and expanded < args.stat_expansions:
        if (
            first_goal_expanded is not None
            and expanded >= first_goal_expanded + args.stat_goal_grace_expansions
        ):
            break
        lane = "weighted"
        if (
            args.stat_close_lane_period > 0
            and expanded > 0
            and expanded % args.stat_close_lane_period == 0
        ):
            lane = "close"
        elif (
            args.stat_cost_lane_period > 0
            and expanded > 0
            and expanded % args.stat_cost_lane_period == 0
        ):
            lane = "cost"
        elif (
            args.stat_def_lane_period > 0
            and expanded > 0
            and expanded % args.stat_def_lane_period == 0
        ):
            lane = "def"
        elif (
            args.stat_efficiency_lane_period > 0
            and expanded > 0
            and expanded % args.stat_efficiency_lane_period == 0
        ):
            lane = "efficiency"
        elif (
            args.stat_progress_lane_period > 0
            and expanded > 0
            and expanded % args.stat_progress_lane_period == 0
        ):
            lane = "progress"
        source = pop_source(lane)
        if source is None:
            break
        ent_id = source["_id"]
        expanded_ids.add(ent_id)
        expanded_state_keys.add(search_state_key(source))
        expanded += 1

        new_entries: list[dict[str, Any]] = []
        direct_edges = backbone_edges(
            source,
            target_limit=args.backbone_targets,
            edge_limit=args.backbone_edges,
            bridge_depth=args.backbone_bridge_depth,
            bridge_width=args.backbone_bridge_width,
            max_iter=args.max_iter,
            efficiency_prune=args.stat_efficiency_prune,
        )
        generated += len(direct_edges)
        progress_generated += sum(edge.get("_edge_kind") == "progress" for edge in direct_edges)
        new_entries.extend(direct_edges)
        if args.supply_policy == "always" or supply_needed(source) or not direct_edges:
            supplied, supply_generated = supply_closure(
                source,
                depth=stat_supply_depth(source, args),
                width=args.supply_width,
                target_limit=args.supply_targets,
                edge_limit=args.supply_edges,
                max_iter=args.max_iter,
                package_dp=args.stat_supply_package_dp,
                package_per_bucket=args.stat_supply_package_per_bucket,
                dominance_prune=args.supply_dominance_prune,
                net_stock_dominance=args.supply_net_stock_dominance,
            )
            generated += supply_generated
            for recovered in supplied:
                if recovered["_id"] == source["_id"]:
                    continue
                if not bound.allows(recovered, "stat-supply"):
                    continue
                edges = backbone_edges(
                    recovered,
                    target_limit=args.backbone_targets,
                    edge_limit=args.backbone_edges,
                    bridge_depth=args.backbone_bridge_depth,
                    bridge_width=args.backbone_bridge_width,
                    max_iter=args.max_iter,
                    efficiency_prune=args.stat_efficiency_prune,
                )
                generated += len(edges)
                progress_generated += sum(edge.get("_edge_kind") == "progress" for edge in edges)
                new_entries.extend(edges)

        for edge in new_entries:
            if not bound.allows(edge, "stat-edge"):
                continue
            if accept(edge):
                push(edge)
                if atomic.stage_goal("stat27", edge) and first_goal_expanded is None:
                    first_goal_expanded = expanded

        if args.entry_limit > 0 and len(active) > args.entry_limit:
            filtered = middle.filter(active.values(), "stat-active-trim")
            kept = select_stat_entries(filtered, args.entry_limit, args, "stat27")
            kept_ids = {ent["_id"] for ent in kept}
            deferred.extend(
                ent
                for ent in filtered
                if ent["_id"] not in kept_ids
                and ent["_id"] not in expanded_ids
                and search_state_key(ent) not in expanded_state_keys
                and bound.allows(ent, "stat-deferred-trim")
            )
            rebuild(kept)
            expanded_ids.intersection_update(kept_ids)
            heap = []
            cost_heap = []
            progress_heap = []
            def_heap = []
            efficiency_heap = []
            close_heap = []
            for ent in kept:
                if ent["_id"] not in expanded_ids and not atomic.stage_goal("stat27", ent):
                    push(ent)

        if expanded % args.report_every == 0 or first_goal_expanded == expanded:
            current = list(active.values())
            goals = [ent for ent in current if atomic.stage_goal("stat27", ent)]
            best = min(goals, key=goal_priority) if goals else None
            max_stats = max((ent["atk"], ent["def"]) for ent in current)
            mt10_entries = sum("MT10" in ent.get("collected", {}) for ent in current)
            rows.append({
                "pass": pass_no,
                "round": expanded,
                "sources": expanded,
                "closure": 0,
                "new": generated,
                "entries": len(current),
                "frontier": len(heap),
                "expanded": expanded,
                "goals": len(goals),
                "max_atk": max_stats[0],
                "max_def": max_stats[1],
                "mt10_entries": mt10_entries,
                "progress_generated": progress_generated,
                "best": compressed.compact(best) if best else None,
            })
            print(
                f"stat dijkstra pass {pass_no} expand {expanded}: generated={generated} entries={len(current)} "
                f"heap={len(heap)} goals={len(goals)} max={max_stats[0]}/{max_stats[1]} "
                f"mt10={mt10_entries} progressEdges={progress_generated}",
                flush=True,
            )
            if best:
                print(f"  best {state_text(best)} stock={rg.final_resource_stock(best)}", flush=True)

    filtered = middle.filter(active.values(), "stat-active-tail")
    entries = select_stat_entries(filtered, args.entry_limit, args, "stat27")
    kept_ids = {ent["_id"] for ent in entries}
    deferred.extend(
        ent
        for ent in filtered
        if ent["_id"] not in expanded_ids
        and search_state_key(ent) not in expanded_state_keys
        and not atomic.stage_goal("stat27", ent)
        and bound.allows(ent, "stat-deferred-tail")
    )
    return entries, rows, expanded, generated, deferred


def run_stat_dijkstra(
    start: dict[str, Any],
    args: argparse.Namespace,
    bound: StrictImproveBound,
    middle: IntermediateDominance,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int, int, dict[str, Any]]:
    """Run narrow resumable Dijkstra passes and persist the remaining frontier."""
    pending, expanded_state_keys, cache_status = load_stat_deferred_cache(start, args, bound, middle)
    pending = select_deferred_stat_frontier(
        pending,
        args.stat_deferred_limit,
        args.stat_heuristic_unit,
        middle,
        "stat-pending-load",
        args,
        args.stat_close_lane_period > 0 or args.stat_close_resume_limit > 0,
    )
    all_entries: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    expanded_total = 0
    generated_total = 0
    retry_rows: list[dict[str, Any]] = []
    starts = [start]
    if pending and args.stat_deferred_resume_limit > 0:
        resumed, pending = select_deferred_stat_resume(
            pending,
            args.stat_deferred_resume_limit,
            args.stat_heuristic_unit,
            args.stat_close_resume_limit,
        )
        starts.extend(resumed)

    for pass_no in range(1, args.stat_retry_rounds + 1):
        entries, pass_rows, expanded, generated, deferred = run_stat_dijkstra_pass(
            starts,
            args,
            bound,
            middle,
            expanded_state_keys,
            pass_no,
        )
        rows.extend(pass_rows)
        expanded_total += expanded
        generated_total += generated
        all_entries = select_stat_entries(
            middle.filter(all_entries + entries, "stat-retry-merge"),
            args.entry_limit,
            args,
            "stat27",
        )
        pending = select_deferred_stat_frontier(
            pending + deferred,
            args.stat_deferred_limit,
            args.stat_heuristic_unit,
            middle,
            "stat-pending-merge",
            args,
            args.stat_close_lane_period > 0 or args.stat_close_resume_limit > 0,
        )
        retry_rows.append({
            "pass": pass_no,
            "starts": len(starts),
            "expanded": expanded,
            "generated": generated,
            "entries": len(entries),
            "pending": len(pending),
        })
        print(
            f"stat dijkstra pass {pass_no} complete: starts={len(starts)} expanded={expanded} "
            f"generated={generated} entries={len(entries)} deferred={len(pending)}",
            flush=True,
        )
        if not pending or pass_no >= args.stat_retry_rounds:
            break
        starts, pending = select_deferred_stat_resume(
            pending,
            args.stat_deferred_resume_limit,
            args.stat_heuristic_unit,
            args.stat_close_resume_limit,
        )
        if not starts:
            break

    save_stat_deferred_cache(
        start,
        pending,
        expanded_state_keys,
        args,
        bound,
        cache_status,
    )
    return all_entries, rows, expanded_total, generated_total, {
        "passes": retry_rows,
        "pending": len(pending),
        "expanded_state_keys": len(expanded_state_keys),
        "cache": cache_status,
    }


def stat_replay_priority(ent: dict[str, Any]) -> tuple[int, ...]:
    """Choose a cheap valid representative while replaying one resource order."""
    return (
        stat_paid_cost(ent),
        ent.get("_dmg", 0),
        ent.get("_yd", 0),
        ent.get("_bd", 0),
        -ent["yk"],
        -ent["bk"],
        -ent["hp"],
    )


def resource_items_added(
    before: dict[str, Any],
    after: dict[str, Any],
) -> tuple[tuple[str, tuple[int, int], str], ...]:
    """Return newly collected resource landmarks for one compressed edge."""
    items: list[tuple[str, tuple[int, int], str]] = []
    for fid, positions in after.get("collected", {}).items():
        new_positions = set(positions) - set(before.get("collected", {}).get(fid, frozenset()))
        if not new_positions or fid not in gw.maps:
            continue
        for x, y, t, eid in gw.maps[fid]["bl"]:
            if t == 3 and eid in compressed.RESOURCE_IDS and (x, y) in new_positions:
                items.append((fid, (x, y), eid))
    return tuple(sorted(items))


def stat_replay_steps(
    start: dict[str, Any],
    goal: dict[str, Any],
) -> list[dict[str, Any]]:
    """Describe the compressed actions after start without tying them to IDs."""
    chain = gw.trace_chain(goal)
    start_idx = next((idx for idx, ent in enumerate(chain) if ent["_id"] == start["_id"]), None)
    if start_idx is None:
        return []
    steps: list[dict[str, Any]] = []
    for before, after in zip(chain[start_idx:], chain[start_idx + 1:]):
        steps.append({
            "kind": after.get("_edge_kind", "other"),
            "fid": after.get("_edge_fid"),
            "items": resource_items_added(before, after),
            "label": after.get("_last_action") or p9.action_summary(after),
            "atk_gain": max(0, after["atk"] - before["atk"]),
            "def_gain": max(0, after["def"] - before["def"]),
            "yk_gain": after["yk"] - before["yk"],
            "bk_gain": after["bk"] - before["bk"],
            "yd_gain": after.get("_yd", 0) - before.get("_yd", 0),
            "bd_gain": after.get("_bd", 0) - before.get("_bd", 0),
            "fallback_dmg": max(0, after.get("_dmg", 0) - before.get("_dmg", 0)),
            "monster_eids": tuple(
                monster["eid"]
                for monster in after.get("_resource_group", {}).get("monsters", [])
            ),
        })
    return steps


def stat_backbone_replay_steps(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Drop incidental supplies so replay can refill them only when useful."""
    return [step for step in steps if step["kind"] in {"stat", "progress"}]


def select_stat_replay_representatives(
    entries: list[dict[str, Any]],
    limit: int,
) -> list[dict[str, Any]]:
    """Keep cheap replay prefixes alongside reserve-key and reserve-HP lanes."""
    filtered = auto.pareto_filter(entries)
    if limit <= 0 or len(filtered) <= limit:
        return sorted(filtered, key=stat_replay_priority)

    chosen: list[dict[str, Any]] = []
    seen: set[int] = set()

    def add(items: Iterable[dict[str, Any]], quota: int) -> None:
        added = 0
        for ent in items:
            if ent["_id"] in seen:
                continue
            seen.add(ent["_id"])
            chosen.append(ent)
            added += 1
            if added >= quota or len(chosen) >= limit:
                return

    orders = [
        stat_replay_priority,
        lambda ent: (
            -ent["yk"],
            -ent["bk"],
            stat_paid_cost(ent),
            ent.get("_dmg", 0),
            -ent["hp"],
        ),
        lambda ent: (
            -ent["hp"],
            stat_paid_cost(ent),
            ent.get("_dmg", 0),
            -ent["yk"],
            -ent["bk"],
        ),
    ]
    quota = max(1, limit // len(orders))
    for order in orders:
        add(sorted(filtered, key=order), quota)
    add(sorted(filtered, key=stat_replay_priority), limit)
    return chosen[:limit]


def replay_step_edges(
    base: dict[str, Any],
    step: dict[str, Any],
    args: argparse.Namespace,
) -> list[dict[str, Any]]:
    """Replay a semantic resource-group step from a possibly reordered state."""
    if step["kind"] == "progress":
        out: list[dict[str, Any]] = []
        for full_edge in auto.progress_edges(base, max_iter=args.max_iter):
            edge = compressed.make_compressed_edge(base, full_edge, max_iter=args.max_iter)
            if edge:
                out.append(edge)
        return sorted(auto.pareto_filter(out), key=stat_replay_priority)

    items = step["items"]
    pending = [
        item
        for item in items
        if item[1] not in auto.collected_for(base, item[0])
    ]
    if not pending:
        return [base]

    anchors = pending
    if step["kind"] == "stat":
        anchors = [item for item in pending if item[2] in BACKBONE_EIDS]
    out: list[dict[str, Any]] = []
    for fid, pos, eid in anchors:
        if step["kind"] == "stat":
            out.extend(
                advance_backbone_target(
                    base,
                    auto.AutoTarget(fid, pos, eid),
                    bridge_depth=args.backbone_bridge_depth,
                    bridge_width=args.backbone_bridge_width,
                    max_iter=args.max_iter,
                )
            )
        else:
            for full_edge in auto.exact_item_edges(base, fid, eid, {pos}, max_iter=args.max_iter):
                edge = compressed.make_compressed_edge(base, full_edge, max_iter=args.max_iter)
                if edge:
                    out.append(edge)

    matched = [
        edge
        for edge in out
        if all(pos in auto.collected_for(edge, fid) for fid, pos, _eid in pending)
    ]
    dedup: dict[tuple[Any, ...], dict[str, Any]] = {}
    for edge in matched:
        sig = auto.result_signature(edge)
        old = dedup.get(sig)
        if old is None or stat_replay_priority(edge) < stat_replay_priority(old):
            dedup[sig] = edge
    return sorted(auto.pareto_filter(dedup.values()), key=stat_replay_priority)


def replay_stat_order(
    start: dict[str, Any],
    steps: list[dict[str, Any]],
    args: argparse.Namespace,
    cache: dict[tuple[Any, ...], list[dict[str, Any]]] | None = None,
) -> dict[str, Any] | None:
    """Replay one high-level order with a small Pareto beam of path variants."""
    frontier = [start]
    prefix: list[dict[str, Any]] = []
    for step in steps:
        prefix.append(step)
        cache_key = stat_order_signature(prefix)
        if cache is not None and cache_key in cache:
            frontier = cache[cache_key]
            continue
        expanded: list[dict[str, Any]] = []
        for ent in frontier:
            direct = replay_step_edges(ent, step, args)
            expanded.extend(direct)
            if direct or not getattr(args, "stat_local_refine_jit_supply", False):
                continue
            supplied, _generated = supply_closure(
                ent,
                depth=stat_supply_depth(ent, args),
                width=args.supply_width,
                target_limit=args.supply_targets,
                edge_limit=args.supply_edges,
                max_iter=args.max_iter,
                package_dp=args.stat_supply_package_dp,
                package_per_bucket=args.stat_supply_package_per_bucket,
                dominance_prune=args.supply_dominance_prune,
                net_stock_dominance=args.supply_net_stock_dominance,
            )
            for recovered in supplied:
                if recovered["_id"] == ent["_id"]:
                    continue
                expanded.extend(replay_step_edges(recovered, step, args))
        if not expanded:
            return None
        frontier = select_stat_replay_representatives(
            expanded,
            args.stat_local_refine_width,
        )
        if cache is not None:
            cache[cache_key] = frontier
    goals = [ent for ent in frontier if atomic.stage_goal("stat27", ent)]
    return min(goals, key=goal_priority) if goals else None


def stat_order_signature(steps: list[dict[str, Any]]) -> tuple[Any, ...]:
    """Stable semantic key for one replayable compressed-resource order."""
    return tuple(
        (
            step["kind"],
            step["fid"],
            step["items"],
        )
        for step in steps
    )


def stat_order_hint(start: dict[str, Any], steps: list[dict[str, Any]]) -> tuple[int, int, int, int]:
    """Cheap optimistic rank before expensive real-floor replay.

    Revalue each resource group's monsters under the candidate stat order and
    add a coarse penalty when the order spends more keys up front than the
    current pocket can cover.  This is the runtime equivalent of the old
    gem-only DP hint: it cheaply ranks promising backbones, then real replay
    decides whether an order is reachable and actually lowers cost.
    """
    atk, def_ = start["atk"], start["def"]
    yk, bk = start["yk"], start["bk"]
    key_debt = 0
    optimistic_dmg = 0
    weighted_position = 0
    stat_position = 0
    for idx, step in enumerate(steps):
        # Net key deltas hide packages that need doors before their own key
        # reward is reached.  Penalize that up-front debt so key-positive stat
        # pockets are tried before key-hungry pockets that need JIT supply.
        yd_need = max(0, step.get("yd_gain", 0))
        bd_need = max(0, step.get("bd_gain", 0))
        if yd_need > yk:
            key_debt += (yd_need - yk) * 1000
        if bd_need > bk:
            key_debt += (bd_need - bk) * 5000
        yk = max(0, yk - yd_need) + max(0, step.get("yk_gain", 0) + yd_need)
        bk = max(0, bk - bd_need) + max(0, step.get("bk_gain", 0) + bd_need)

        monster_eids = step.get("monster_eids", ())
        if monster_eids:
            for eid in monster_eids:
                dmg = calc_dmg(eid, atk, def_)
                optimistic_dmg += 10000 if dmg == float("inf") else int(dmg)
        else:
            optimistic_dmg += step.get("fallback_dmg", 0)
        atk_gain = step.get("atk_gain", 0)
        def_gain = step.get("def_gain", 0)
        if atk_gain or def_gain:
            weighted_position += idx * (def_gain * 120 + atk_gain * 80)
            stat_position += idx
        atk = min(27, atk + atk_gain)
        def_ = min(27, def_ + def_gain)
    return key_debt, optimistic_dmg, weighted_position, stat_position


def stat_order_key_feasible(start: dict[str, Any], steps: list[dict[str, Any]]) -> bool:
    """Reject semantic reorders that visibly spend keys before collecting them."""
    yk, bk = start["yk"], start["bk"]
    for step in steps:
        yk += step.get("yk_gain", 0)
        bk += step.get("bk_gain", 0)
        if yk < 0 or bk < 0:
            return False
    return True


def crosses_progress_boundary(
    steps: list[dict[str, Any]],
    src_idx: int,
    dst_idx: int,
) -> bool:
    """Do not spend replay budget moving a gem across the MT10 unlock edge."""
    lo, hi = sorted((src_idx, dst_idx))
    return any(step["kind"] == "progress" for step in steps[lo : hi + 1])


def semantic_order_variants(
    steps: list[dict[str, Any]],
    window: int,
    depth: int,
) -> list[tuple[list[dict[str, Any]], list[list[int]]]]:
    """Generate bounded order lookahead without requiring intermediate reachability."""
    frontier = [(steps, [])]
    seen = {stat_order_signature(steps)}
    out: list[tuple[list[dict[str, Any]], list[list[int]]]] = []
    for _depth in range(depth):
        next_frontier: list[tuple[list[dict[str, Any]], list[list[int]]]] = []
        for lane_steps, lane_moves in frontier:
            for src_idx, step in enumerate(lane_steps):
                if step["kind"] != "stat":
                    continue
                lo = max(0, src_idx - window)
                hi = min(len(lane_steps) - 1, src_idx + window)
                for dst_idx in range(lo, hi + 1):
                    if dst_idx == src_idx or crosses_progress_boundary(lane_steps, src_idx, dst_idx):
                        continue
                    moved = list(lane_steps)
                    moved_step = moved.pop(src_idx)
                    moved.insert(dst_idx, moved_step)
                    signature = stat_order_signature(moved)
                    if signature in seen:
                        continue
                    seen.add(signature)
                    row = (moved, lane_moves + [[src_idx, dst_idx]])
                    out.append(row)
                    next_frontier.append(row)
        frontier = next_frontier
    return out


def has_adjacent_order_move(moves: list[list[int]]) -> bool:
    return any(abs(src_idx - dst_idx) == 1 for src_idx, dst_idx in moves)


def add_certified_prune_stats(
    stats: dict[str, int],
    winner: dict[str, Any],
    loser: dict[str, Any],
    loser_moves: list[list[int]],
) -> None:
    stats["pruned"] += 1
    if auto.result_signature(winner) == auto.result_signature(loser):
        stats["exact_duplicate"] += 1
    if gw._collected_signature(winner) == gw._collected_signature(loser):
        stats["same_collected_signature"] += 1
    elif collected_landmarks(loser) <= collected_landmarks(winner):
        stats["superset_collected_landmarks"] += 1
    if has_adjacent_order_move(loser_moves):
        stats["adjacent_swap"] += 1


def certified_order_candidate_filter(
    candidates: list[tuple[dict[str, Any], list[dict[str, Any]], list[list[int]]]],
) -> tuple[
    list[tuple[dict[str, Any], list[dict[str, Any]], list[list[int]]]],
    dict[str, int],
]:
    """Drop only semantic order candidates already proven no better.

    Every candidate has been replayed through the real floor search before this
    filter runs.  A removed order is either an exact duplicate final state, or
    is dominated by another replayed state that has collected at least the same
    future map landmarks with no worse monotone resources/costs.
    """
    stats: dict[str, int] = defaultdict(int)
    exact: dict[tuple[Any, ...], tuple[dict[str, Any], list[dict[str, Any]], list[list[int]]]] = {}
    for candidate in candidates:
        trial, _steps, moves = candidate
        signature = auto.result_signature(trial)
        old = exact.get(signature)
        if old is None:
            exact[signature] = candidate
            continue
        add_certified_prune_stats(stats, old[0], trial, moves)

    kept: list[tuple[dict[str, Any], list[dict[str, Any]], list[list[int]]]] = []
    for candidate in sorted(exact.values(), key=lambda row: goal_priority(row[0])):
        trial, _steps, moves = candidate
        dominator = next(
            (old for old in kept if monotone_intermediate_dominates(old[0], trial)),
            None,
        )
        if dominator is not None:
            add_certified_prune_stats(stats, dominator[0], trial, moves)
            continue
        survivors = []
        for old in kept:
            if monotone_intermediate_dominates(trial, old[0]):
                add_certified_prune_stats(stats, trial, old[0], old[2])
                continue
            survivors.append(old)
        survivors.append(candidate)
        kept = survivors
    return kept, dict(sorted(stats.items()))


def refine_stat_goals(
    start: dict[str, Any],
    goals: list[dict[str, Any]],
    args: argparse.Namespace,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    """Improve found stat routes with a bounded top-K gem-order beam.

    A compressed best-first search can reach 27/27 before a tiny ordering gain
    has had time to surface globally.  A greedy single-move pass also misses
    coordinated reorders when the first move is neutral or temporarily worse.
    This neighborhood pass keeps several replayable intermediate orders alive,
    moves one stat group within a small window, and validates every candidate
    through the real floor search.  It changes scheduling only; Pareto
    acceptance and route legality stay authoritative.
    """
    if args.stat_local_refine_passes <= 0 or not goals:
        return goals, [], {}

    improved: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    certified_prune_total: dict[str, int] = defaultdict(int)
    replay_cache: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for seed in goals[: args.stat_local_refine_seeds]:
        seed_steps = stat_replay_steps(start, seed)
        if args.stat_local_refine_jit_supply:
            seed_steps = stat_backbone_replay_steps(seed_steps)
        if not seed_steps:
            continue
        best = seed
        frontier = [(seed, seed_steps, [])]
        visited = {stat_order_signature(seed_steps)}
        for pass_no in range(1, args.stat_local_refine_passes + 1):
            ordered_trials: list[tuple[tuple[int, int, int], int, list[dict[str, Any]], list[list[int]]]] = []
            candidates: list[tuple[dict[str, Any], list[dict[str, Any]], list[list[int]]]] = []
            for lane_idx, (_lane_goal, lane_steps, lane_moves) in enumerate(frontier):
                lane_trials: list[
                    tuple[tuple[int, int, int], int, list[dict[str, Any]], list[list[int]]]
                ] = []
                for moved, moves in semantic_order_variants(
                    lane_steps,
                    window=args.stat_local_refine_window,
                    depth=args.stat_local_refine_order_depth,
                ):
                    signature = stat_order_signature(moved)
                    if signature in visited:
                        continue
                    visited.add(signature)
                    lane_trials.append((
                        stat_order_hint(start, moved),
                        moves[-1][0],
                        moved,
                        lane_moves + moves,
                    ))
                lane_trials.sort(key=lambda row: row[0])
                per_lane = max(2, args.stat_local_refine_trials // max(1, len(frontier)))
                if lane_idx == 0:
                    per_lane = max(per_lane, (args.stat_local_refine_trials * 2) // 3)
                lane_chosen: list[
                    tuple[tuple[int, int, int], int, list[dict[str, Any]], list[list[int]]]
                ] = []
                chosen_signatures: set[tuple[Any, ...]] = set()

                def add_trials(
                    trials: Iterable[
                        tuple[tuple[int, int, int], int, list[dict[str, Any]], list[list[int]]]
                    ],
                    quota: int,
                ) -> None:
                    for trial in trials:
                        signature = stat_order_signature(trial[2])
                        if signature in chosen_signatures:
                            continue
                        chosen_signatures.add(signature)
                        lane_chosen.append(trial)
                        if len(lane_chosen) >= quota:
                            return

                seen_sources: set[int] = set()
                source_heads = []
                for trial in lane_trials:
                    if trial[1] not in seen_sources:
                        seen_sources.add(trial[1])
                        source_heads.append(trial)
                add_trials(source_heads, per_lane)
                adjacent_first = sorted(
                    lane_trials,
                    key=lambda row: (
                        abs(row[3][-1][0] - row[3][-1][1]) != 1,
                        row[3][-1][1] > row[3][-1][0],
                        row[0],
                    ),
                )
                add_trials(adjacent_first, per_lane)
                if len(lane_chosen) < per_lane:
                    add_trials(lane_trials, per_lane)
                ordered_trials.extend(lane_chosen[:per_lane])
            for _hint, _src_idx, moved, moves in ordered_trials[: args.stat_local_refine_trials]:
                trial = replay_stat_order(start, moved, args, cache=replay_cache)
                if trial:
                    candidates.append((trial, moved, moves))
            if not candidates:
                break
            if args.stat_certified_order_prune:
                candidates, prune_stats = certified_order_candidate_filter(candidates)
                if prune_stats:
                    for key, value in prune_stats.items():
                        certified_prune_total[key] += value
                    row_best = min((row[0] for row in candidates), key=goal_priority) if candidates else best
                    rows.append({
                        "pass": pass_no,
                        "moves": "certified-order-prune",
                        "beam": len(candidates),
                        "best": compressed.compact(row_best),
                        "certified_pruned": prune_stats,
                    })
                    print(
                        f"stat certified order prune pass {pass_no}: "
                        f"pruned={prune_stats} remaining={len(candidates)}",
                        flush=True,
                    )
            candidates.sort(key=lambda row: goal_priority(row[0]))
            frontier = candidates[: args.stat_local_refine_beam]
            lane_best, lane_steps, lane_moves = frontier[0]
            if goal_priority(lane_best) < goal_priority(best):
                best = lane_best
                rows.append({
                    "pass": pass_no,
                    "moves": lane_moves,
                    "beam": len(frontier),
                    "best": compressed.compact(best),
                })
                print(
                    f"stat local refine pass {pass_no}: moves={lane_moves} "
                    f"beam={len(frontier)} {state_text(best)}",
                    flush=True,
                )
            else:
                print(
                    f"stat local refine pass {pass_no}: no immediate gain; "
                    f"keeping {len(frontier)} replayable order lanes",
                    flush=True,
                )
        if goal_priority(best) < goal_priority(seed):
            print(
                f"stat local refine selected: moves="
                f"{next((row['moves'] for row in reversed(rows) if row['best']['dmg'] == best.get('_dmg', 0)), [])} "
                f"{state_text(best)}",
                flush=True,
            )
        improved.append(best)
    return (
        sorted(auto.pareto_filter(goals + improved), key=goal_priority),
        rows,
        dict(sorted(certified_prune_total.items())),
    )


def write_walk(best: dict[str, Any], phase1_id: int, phase1_label: str) -> None:
    title = (
        "# Post-9 Gem Backbone + Supply Closure Best Boss Walk"
        if p9.goal(best)
        else "# Post-9 Gem Backbone + Supply Closure Best 27/27 Walk"
    )
    lines = [
        title,
        "",
        f"> final: {state_text(best)}",
        "",
    ]
    chain = gw.trace_chain(best)
    for idx, ent in enumerate(chain):
        if idx == 0:
            label = "4F search start"
        elif ent["_id"] == phase1_id:
            replay_action = ent.get("_last_action")
            label = (
                f"{replay_action} [{phase1_label}]"
                if replay_action and ":" in replay_action
                else phase1_label
            )
        else:
            label = ent.get("_last_action") or ent.get("_source") or p9.action_summary(ent)
        lines.extend([f"## {idx}. {label}", "", f"- {state_text(ent)}", ""])
    os.makedirs(os.path.dirname(OUT_WALK), exist_ok=True)
    with open(OUT_WALK, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")


def run(args: argparse.Namespace) -> dict[str, Any]:
    global RAW_STOCK_FUTURE_DOOR_BOUND_ENABLED, NET_POCKET_RAW_STOCK_ENABLED
    RAW_STOCK_FUTURE_DOOR_BOUND_ENABLED = args.raw_stock_future_door_bound
    NET_POCKET_RAW_STOCK_ENABLED = args.net_pocket_raw_stock
    if args.supply_net_stock_dominance and not args.net_pocket_raw_stock:
        raise ValueError("--supply-net-stock-dominance requires --net-pocket-raw-stock")
    floor_cache_enabled = args.floor_search_cache or bool(args.floor_search_cache_path)
    configure_floor_search_cache(
        floor_cache_enabled,
        args.floor_search_cache_limit,
        args.floor_search_cache_path,
    )
    t0 = time.time()
    bound = StrictImproveBound(
        args.strict_improve_dmg_bound,
        args.strict_raw_stock_bound,
        args.strict_net_stock_bound,
        args.strict_final_stock_bound,
    )
    middle = IntermediateDominance(args.intermediate_dominance_prune)
    phase1_t0 = time.time()
    start, phase1 = find_phase1_candidate(args)
    phase1_elapsed = time.time() - phase1_t0
    phase1_id = start["_id"]
    phase1_label = phase1.get("label", "phase1 prefix complete")
    start = saturate_initial_free_resources(start, args.max_iter)
    first_goal_round: int | None = None
    stat_retry: dict[str, Any] = {}
    if args.outer_scheduler == "dijkstra":
        entries, rows, expanded_total, generated_total, stat_retry = run_stat_dijkstra(
            start,
            args,
            bound,
            middle,
        )
        frontier: list[dict[str, Any]] = []
        stop_after = 0
    else:
        entries = [start]
        frontier = [start]
        expanded_total = 0
        rows = []
        generated_total = 0
        stop_after = args.rounds

    round_no = 0
    while round_no < stop_after:
        round_no += 1
        sources = [ent for ent in frontier if not atomic.stage_goal("stat27", ent)]
        if not sources:
            break

        new_entries: list[dict[str, Any]] = []
        closure_count = 0
        for source in sources:
            expanded_total += 1
            direct_edges = backbone_edges(
                source,
                target_limit=args.backbone_targets,
                edge_limit=args.backbone_edges,
                bridge_depth=args.backbone_bridge_depth,
                bridge_width=args.backbone_bridge_width,
                max_iter=args.max_iter,
                efficiency_prune=args.stat_efficiency_prune,
            )
            generated_total += len(direct_edges)
            new_entries.extend(direct_edges)
            supplies = [source]
            if args.supply_policy == "always" or supply_needed(source) or not direct_edges:
                supplies, supply_generated = supply_closure(
                    source,
                    depth=stat_supply_depth(source, args),
                    width=args.supply_width,
                    target_limit=args.supply_targets,
                    edge_limit=args.supply_edges,
                    max_iter=args.max_iter,
                    package_dp=args.stat_supply_package_dp,
                    package_per_bucket=args.stat_supply_package_per_bucket,
                    dominance_prune=args.supply_dominance_prune,
                    net_stock_dominance=args.supply_net_stock_dominance,
                )
                generated_total += supply_generated
            closure_count += max(0, len(supplies) - 1)
            for supplied in supplies:
                if supplied["_id"] == source["_id"]:
                    continue
                edges = backbone_edges(
                    supplied,
                    target_limit=args.backbone_targets,
                    edge_limit=args.backbone_edges,
                    bridge_depth=args.backbone_bridge_depth,
                    bridge_width=args.backbone_bridge_width,
                    max_iter=args.max_iter,
                    efficiency_prune=args.stat_efficiency_prune,
                )
                generated_total += len(edges)
                new_entries.extend(edges)

        entries = select_stat_entries(
            middle.filter(
                (
                    ent for ent in entries + new_entries
                    if bound.allows(ent, "stat-layer-entry")
                ),
                "stat-layer-entry",
            ),
            args.entry_limit,
            args,
            "stat27",
        )
        active_ids = {ent["_id"] for ent in entries}
        next_frontier = [ent for ent in new_entries if ent["_id"] in active_ids]
        frontier = trim_backbone_frontier(
            next_frontier,
            min(args.frontier_limit, args.source_limit),
            args.per_prefix,
        )
        goals = [ent for ent in entries if atomic.stage_goal("stat27", ent)]
        if goals and first_goal_round is None:
            first_goal_round = round_no
            stop_after = max(stop_after, round_no + args.goal_grace_rounds)
        best = min(goals, key=goal_priority) if goals else None
        max_stats = max((ent["atk"], ent["def"]) for ent in entries)
        row = {
            "round": round_no,
            "sources": len(sources),
            "closure": closure_count,
            "new": len(new_entries),
            "entries": len(entries),
            "frontier": len(frontier),
            "expanded": expanded_total,
            "goals": len(goals),
            "max_atk": max_stats[0],
            "max_def": max_stats[1],
            "best": compressed.compact(best) if best else None,
        }
        rows.append(row)
        print(
            f"round {round_no}: sources={len(sources)} closure={closure_count} "
            f"new={len(new_entries)} entries={len(entries)} frontier={len(frontier)} expanded={expanded_total} "
            f"goals={len(goals)} max={max_stats[0]}/{max_stats[1]}",
            flush=True,
        )
        if args.trace_frontier:
            for ent in sorted(frontier, key=lambda item: (item.get("_dmg", 0), p9.stat_deficit(item)))[: args.trace_frontier]:
                print(
                    f"    frontier {state_text(ent)} order={' > '.join(ent.get('_major_order', ()))}",
                    flush=True,
                )
        if best:
            print(f"  best {state_text(best)} stock={rg.final_resource_stock(best)}", flush=True)

    stat_goals = sorted(
        [
            ent for ent in entries
            if atomic.stage_goal("stat27", ent) and bound.allows(ent, "stat-goal")
        ],
        key=goal_priority,
    )
    stat_goals, refinement_rows, certified_order_prune = refine_stat_goals(start, stat_goals, args)
    stat_goals = [
        ent for ent in stat_goals
        if bound.allows(ent, "stat-refined-goal")
    ]
    stat_best = stat_goals[0] if stat_goals else None
    final_rows: list[dict[str, Any]] = []
    redkey_goals: list[dict[str, Any]] = []
    final_goals: list[dict[str, Any]] = []
    final_cache_entries = {"redkey": [], "boss": []}
    final_cache_expanded = {"redkey": set(), "boss": set()}
    final_cache_status: dict[str, Any] = {}
    best = stat_best
    best_stage = "stat27" if stat_best else None
    if args.continue_final:
        final_cache_entries, final_cache_expanded, final_cache_status = load_final_checkpoint_cache(
            start,
            args,
            bound,
            middle,
        )
    if args.continue_final and (stat_goals or final_cache_entries["redkey"]):
        carry = select_goal_carry(stat_goals, args.carry_limit) if stat_goals else []
        redkey_entries, stage_rows = run_recovery_stage(
            "redkey",
            carry + final_cache_entries["redkey"],
            args.redkey_rounds,
            args,
            bound,
            middle,
            final_cache_expanded["redkey"],
        )
        final_cache_entries["redkey"] = redkey_entries
        final_rows.extend(stage_rows)
        redkey_goals = sorted(
            [ent for ent in redkey_entries if atomic.stage_goal("redkey", ent)],
            key=lambda ent: atomic.stage_priority("redkey", ent),
        )
        boss_starts = []
        if redkey_goals:
            boss_starts.extend(select_goal_carry(redkey_goals, args.carry_limit))
        boss_starts.extend(final_cache_entries["boss"])
        if boss_starts:
            boss_entries, stage_rows = run_recovery_stage(
                "boss",
                boss_starts,
                args.boss_rounds,
                args,
                bound,
                middle,
                final_cache_expanded["boss"],
            )
            final_cache_entries["boss"] = boss_entries
            final_rows.extend(stage_rows)
            boss_goal_entries = [
                ent for ent in boss_entries
                if p9.goal(ent) and bound.allows(ent, "final-goal")
            ]
            if args.goal_objective == "raw-stock":
                final_goals = sorted(boss_goal_entries, key=raw_stock_goal_priority)
            elif args.goal_objective == "net-stock":
                final_goals = sorted(boss_goal_entries, key=net_stock_goal_priority)
            elif args.goal_objective == "final-stock":
                final_goals = sorted(boss_goal_entries, key=final_stock_goal_priority)
            else:
                final_goals = [
                    ent for ent in rg.best_goals(boss_goal_entries)
                    if bound.allows(ent, "final-goal-best")
                ]
            if final_goals:
                best = final_goals[0]
                best_stage = "boss"
    if args.continue_final:
        save_final_checkpoint_cache(
            start,
            final_cache_entries,
            final_cache_expanded,
            args,
            bound,
            middle,
            final_cache_status,
        )
    if best:
        print(
            f"selected {best_stage} best {state_text(best)} "
            f"stock={rg.final_resource_stock(best)} netStock={net_final_stock(best)}",
            flush=True,
        )
        write_walk(best, phase1_id, phase1_label)
    save_floor_search_cache(args.floor_search_cache_path)
    return {
        "elapsed": time.time() - t0,
        "mode": "gem-supply",
        "phase1_elapsed": phase1_elapsed,
        "phase1_source": args.phase1_source,
        "start": compressed.compact(start),
        "entry_count": len(entries),
        "expanded": expanded_total,
        "generated_total": generated_total,
        "goal_count": len(final_goals) if args.continue_final else len(stat_goals),
        "best_stage": best_stage,
        "best": compact_state(best) if best else None,
        "top_goals": [
            compact_state(ent)
            for ent in (final_goals if args.continue_final else stat_goals)[:10]
        ],
        "stat27_goal_count": len(stat_goals),
        "stat27_best": compact_state(stat_best) if stat_best else None,
        "stat27_top": [compact_state(ent) for ent in stat_goals[:10]],
        "stat_gem_mask_summary": gem_mask_summary(entries),
        "stat_refinement": refinement_rows,
        "stat_certified_order_prune": certified_order_prune,
        "stat_retry": stat_retry,
        "supply_dominance": dict(SUPPLY_DOMINANCE_STATS),
        "redkey_goal_count": len(redkey_goals),
        "final_checkpoint_cache": final_cache_status,
        "final_rows": final_rows,
        "rows": rows,
        "strict_improve": bound.compact(),
        "floor_search_cache": floor_search_cache_compact(),
        "intermediate_dominance": middle.compact(),
        "config": {
            "rounds": args.rounds,
            "goal_grace_rounds": args.goal_grace_rounds,
            "outer_scheduler": args.outer_scheduler,
            "stat_expansions": args.stat_expansions,
            "stat_goal_grace_expansions": args.stat_goal_grace_expansions,
            "stat_heuristic_unit": args.stat_heuristic_unit,
            "stat_cost_lane_period": args.stat_cost_lane_period,
            "stat_progress_lane_period": args.stat_progress_lane_period,
            "stat_def_lane_period": args.stat_def_lane_period,
            "stat_efficiency_prune": args.stat_efficiency_prune,
            "stat_efficiency_lane_period": args.stat_efficiency_lane_period,
            "stat_close_lane_period": args.stat_close_lane_period,
            "stat_close_resume_limit": args.stat_close_resume_limit,
            "strict_improve_dmg_bound": args.strict_improve_dmg_bound,
            "strict_raw_stock_bound": args.strict_raw_stock_bound,
            "strict_net_stock_bound": args.strict_net_stock_bound,
            "strict_final_stock_bound": args.strict_final_stock_bound,
            "raw_stock_future_door_bound": args.raw_stock_future_door_bound,
            "net_pocket_raw_stock": args.net_pocket_raw_stock,
            "floor_search_cache": args.floor_search_cache,
            "floor_search_cache_limit": args.floor_search_cache_limit,
            "floor_search_cache_path": args.floor_search_cache_path,
            "goal_objective": args.goal_objective,
            "intermediate_dominance_prune": args.intermediate_dominance_prune,
            "stat_retry_rounds": args.stat_retry_rounds,
            "stat_deferred_limit": args.stat_deferred_limit,
            "stat_deferred_resume_limit": args.stat_deferred_resume_limit,
            "stat_deferred_cache": args.stat_deferred_cache,
            "stat_local_refine_passes": args.stat_local_refine_passes,
            "stat_local_refine_seeds": args.stat_local_refine_seeds,
            "stat_local_refine_width": args.stat_local_refine_width,
            "stat_local_refine_window": args.stat_local_refine_window,
            "stat_local_refine_beam": args.stat_local_refine_beam,
            "stat_local_refine_trials": args.stat_local_refine_trials,
            "stat_local_refine_order_depth": args.stat_local_refine_order_depth,
            "stat_local_refine_jit_supply": args.stat_local_refine_jit_supply,
            "stat_certified_order_prune": args.stat_certified_order_prune,
            "report_every": args.report_every,
            "source_limit": args.source_limit,
            "frontier_limit": args.frontier_limit,
            "per_prefix": args.per_prefix,
            "entry_limit": args.entry_limit,
            "supply_policy": args.supply_policy,
            "supply_depth": args.supply_depth,
            "stat_extra_key_supply_depth": args.stat_extra_key_supply_depth,
            "stat_supply_package_dp": args.stat_supply_package_dp,
            "stat_supply_package_per_bucket": args.stat_supply_package_per_bucket,
            "supply_dominance_prune": args.supply_dominance_prune,
            "supply_net_stock_dominance": args.supply_net_stock_dominance,
            "stat_gem_mask_frontier": args.stat_gem_mask_frontier,
            "stat_gem_mask_per_bucket": args.stat_gem_mask_per_bucket,
            "supply_width": args.supply_width,
            "supply_targets": args.supply_targets,
            "supply_edges": args.supply_edges,
            "backbone_targets": args.backbone_targets,
            "backbone_edges": args.backbone_edges,
            "backbone_bridge_depth": args.backbone_bridge_depth,
            "backbone_bridge_width": args.backbone_bridge_width,
            "continue_final": args.continue_final,
            "carry_limit": args.carry_limit,
            "redkey_rounds": args.redkey_rounds,
            "boss_rounds": args.boss_rounds,
            "final_source_limit": args.final_source_limit,
            "final_entry_limit": args.final_entry_limit,
            "final_checkpoint_cache": args.final_checkpoint_cache,
            "final_checkpoint_cache_limit": args.final_checkpoint_cache_limit,
            "final_targets": args.final_targets,
            "final_edges": args.final_edges,
            "final_supply_depth": args.final_supply_depth,
            "final_supply_width": args.final_supply_width,
            "final_bridge_depth": args.final_bridge_depth,
            "final_bridge_width": args.final_bridge_width,
        },
    }


def write_outputs(data: dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
    write_json_with_retry(OUT_JSON, data)

    lines = [
        "# Post-9 Gem Backbone + Supply Closure Search",
        "",
        f"- elapsed: `{data['elapsed']:.3f}s`",
        f"- goals: `{data['goal_count']}`",
        f"- expanded: `{data['expanded']}`",
        f"- generated: `{data['generated_total']}`",
        f"- best stage: `{data.get('best_stage')}`",
        f"- strict improve: `{data['strict_improve']}`",
        f"- floor search cache: `{data.get('floor_search_cache', {})}`",
        f"- intermediate dominance: `{data['intermediate_dominance']}`",
        f"- stat certified order prune: `{data.get('stat_certified_order_prune', {})}`",
        f"- stat gem mask summary: `{data.get('stat_gem_mask_summary', {})}`",
        f"- stat retry: `{data['stat_retry']}`",
        f"- supply dominance: `{data.get('supply_dominance', {})}`",
        f"- raw stock model: `net_pocket={data['config'].get('net_pocket_raw_stock', False)}`",
        f"- final checkpoint cache: `{data['final_checkpoint_cache']}`",
        f"- config: `{data['config']}`",
        "",
    ]
    if data["best"]:
        best = data["best"]
        raw_text = (
            f" rawStock={best['raw_final_stock']}"
            if "raw_final_stock" in best
            else ""
        )
        net_text = (
            f" netStock={best['net_final_stock']}"
            if "net_final_stock" in best
            else ""
        )
        lines.append(
            f"- best: HP={best['hp']} ATK={best['atk']} DEF={best['def']} "
            f"YK={best['yk']} BK={best['bk']} dmg={best['dmg']} "
            f"door={best['yd']}/{best['bd']}/{best['rd']}{raw_text}{net_text}"
        )
    lines.extend([
        "",
        "## Progress",
        "",
        "| pass | round | sources | closure | new | entries | frontier | expanded | goals | max ATK/DEF | best |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ])
    for row in data["rows"]:
        best = row["best"]
        best_text = "-"
        if best:
            best_text = f"HP={best['hp']} dmg={best['dmg']} door={best['yd']}/{best['bd']}/{best['rd']}"
        lines.append(
            f"| {row.get('pass', 1)} | {row['round']} | {row['sources']} | {row['closure']} | {row['new']} | "
            f"{row['entries']} | {row['frontier']} | {row['expanded']} | {row['goals']} | "
            f"{row['max_atk']}/{row['max_def']} | {best_text} |"
        )
    lines.extend([
        "",
        "## Top Goals",
        "",
        "| # | state | net stock | raw stock | raw upper |",
        "|---:|---|---:|---:|---:|",
    ])
    for idx, goal in enumerate(data["top_goals"], 1):
        lines.append(
            f"| {idx} | HP={goal['hp']} ATK={goal['atk']} DEF={goal['def']} "
            f"YK={goal['yk']} BK={goal['bk']} dmg={goal['dmg']} "
            f"door={goal['yd']}/{goal['bd']}/{goal['rd']} | "
            f"{goal.get('net_final_stock', '-')} | "
            f"{goal.get('raw_final_stock', '-')} | {goal.get('raw_stock_upper_bound', '-')} |"
        )
    if data.get("stat_refinement"):
        lines.extend([
            "",
            "## Stat Local Refinement",
            "",
            "| pass | moves | state | certified pruned |",
            "|---:|---|---|---|",
        ])
        for row in data["stat_refinement"]:
            best = row["best"]
            lines.append(
                f"| {row['pass']} | {row['moves']} | "
                f"HP={best['hp']} dmg={best['dmg']} door={best['yd']}/{best['bd']}/{best['rd']} | "
                f"{row.get('certified_pruned', '-')} |"
            )
    if data.get("final_rows"):
        lines.extend([
            "",
            "## Final Continuation",
            "",
            "| stage | round | sources | closure | new | entries | goals | max ATK/DEF | best | best frontier |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---|---|",
        ])
        for row in data["final_rows"]:
            best = row["best"]
            best_text = "-"
            if best:
                best_text = f"HP={best['hp']} dmg={best['dmg']} door={best['yd']}/{best['bd']}/{best['rd']}"
            best_entry = row.get("best_entry")
            best_entry_text = "-"
            if best_entry:
                best_entry_text = (
                    f"HP={best_entry['hp']} dmg={best_entry['dmg']} "
                    f"door={best_entry['yd']}/{best_entry['bd']}/{best_entry['rd']}"
                )
            lines.append(
                f"| {row['stage']} | {row['round']} | {row['sources']} | {row.get('closure', 0)} | {row['new']} | "
                f"{row['entries']} | {row['goals']} | {row['max_atk']}/{row['max_def']} | {best_text} | {best_entry_text} |"
            )
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase1-expansions", type=int, default=300)
    parser.add_argument("--phase1-source", choices=["replay", "resource", "fixed", "search"], default="replay")
    parser.add_argument("--output-tag", default="")
    parser.add_argument("--rounds", type=int, default=18)
    parser.add_argument("--goal-grace-rounds", type=int, default=5)
    parser.add_argument("--outer-scheduler", choices=["layers", "dijkstra"], default="layers")
    parser.add_argument("--stat-expansions", type=int, default=180)
    parser.add_argument("--stat-goal-grace-expansions", type=int, default=40)
    parser.add_argument("--stat-heuristic-unit", type=int, default=40)
    parser.add_argument(
        "--strict-improve-dmg-bound",
        type=int,
        default=0,
        help="Only keep states whose optimistic remaining red-key and boss damage stays strictly below this incumbent; 0 disables.",
    )
    parser.add_argument(
        "--strict-raw-stock-bound",
        type=int,
        default=0,
        help="Only keep states whose optimistic final raw resource stock can strictly exceed this incumbent; 0 disables.",
    )
    parser.add_argument(
        "--strict-net-stock-bound",
        type=int,
        default=0,
        help=(
            "Only keep states whose optimistic final stock can strictly exceed this recoverable net-stock incumbent; "
            "0 disables. Uses raw-stock as a safe upper bound."
        ),
    )
    parser.add_argument(
        "--strict-final-stock-bound",
        type=int,
        default=0,
        help=(
            "Only keep states whose optimistic final stock can strictly exceed this door-net final-stock incumbent; "
            "0 disables. Remaining monsters are ignored in the incumbent stock model."
        ),
    )
    parser.add_argument(
        "--raw-stock-future-door-bound",
        action="store_true",
        help="Strengthen raw-stock upper bounds by subtracting conservative future mandatory MT10-entry, MT8-red-key, and MT10-boss yellow door costs.",
    )
    parser.add_argument(
        "--net-pocket-raw-stock",
        action="store_true",
        help=(
            "Use audited net value for small remaining key pockets when computing raw-stock objective "
            "(for example MT7 x5y10/x5y11 counts as two yellow keys minus its unopened yellow door)."
        ),
    )
    parser.add_argument(
        "--floor-search-cache",
        action="store_true",
        help="Cache exact single-floor search results by local state, targets, flyback mode, max_iter, and extra_removed.",
    )
    parser.add_argument(
        "--floor-search-cache-limit",
        type=int,
        default=0,
        help="Maximum in-memory floor-search cache entries; 0 means unlimited for the current process.",
    )
    parser.add_argument(
        "--floor-search-cache-path",
        default="",
        help="Optional JSON path for persisting exact floor-search cache entries across runs; also enables the cache.",
    )
    parser.add_argument(
        "--goal-objective",
        choices=["dmg", "raw-stock", "net-stock", "final-stock"],
        default="dmg",
        help="Rank final boss goals by damage, raw leftover stock, recoverable net stock, or door-net final stock.",
    )
    parser.add_argument(
        "--intermediate-dominance-prune",
        action="store_true",
        help="Prune a middle state only when a farther-progressed state is no worse on damage, doors, HP, stats, and keys.",
    )
    parser.add_argument(
        "--stat-retry-rounds",
        type=int,
        default=1,
        help="Run this many narrow stat Dijkstra passes, resuming candidates deferred by width or grace limits.",
    )
    parser.add_argument(
        "--stat-deferred-limit",
        type=int,
        default=600,
        help="Keep at most this many diverse unexpanded stat checkpoints between retry passes.",
    )
    parser.add_argument(
        "--stat-deferred-resume-limit",
        type=int,
        default=24,
        help="Resume at most this many deferred stat checkpoints in each retry pass.",
    )
    parser.add_argument(
        "--stat-deferred-cache",
        default="",
        help="Optional JSON path for persisting unexpanded stat checkpoints and exact expanded-state memo.",
    )
    parser.add_argument(
        "--stat-cost-lane-period",
        type=int,
        default=4,
        help="Expand one pure paid-cost lane state every N weighted-A* expansions; 0 disables.",
    )
    parser.add_argument(
        "--stat-progress-lane-period",
        type=int,
        default=3,
        help="Expand one fast stat-growth lane state every N weighted-A* expansions; 0 disables.",
    )
    parser.add_argument(
        "--stat-def-lane-period",
        type=int,
        default=5,
        help="Expand one DEF-first lane state every N weighted-A* expansions; 0 disables.",
    )
    parser.add_argument(
        "--stat-efficiency-prune",
        action="store_true",
        help=(
            "Use cheap-DEF representative lanes in bounded stat edge/frontier selection. "
            "This is a scheduling trim, not a cross-resource proof."
        ),
    )
    parser.add_argument(
        "--stat-efficiency-lane-period",
        type=int,
        default=0,
        help="Expand one low-cost-per-DEF lane state every N weighted-A* expansions; 0 disables.",
    )
    parser.add_argument(
        "--stat-close-lane-period",
        type=int,
        default=0,
        help="Expand one low optimistic-total state near 27/27 every N expansions; 0 disables.",
    )
    parser.add_argument(
        "--stat-close-resume-limit",
        type=int,
        default=0,
        help="Resume this many late near-27/27 deferred checkpoints in each retry pass; 0 preserves weighted-only resume.",
    )
    parser.add_argument(
        "--stat-local-refine-passes",
        type=int,
        default=4,
        help="Replay adjacent stat-group swaps after reaching 27/27; 0 disables.",
    )
    parser.add_argument("--stat-local-refine-seeds", type=int, default=2)
    parser.add_argument("--stat-local-refine-width", type=int, default=3)
    parser.add_argument("--stat-local-refine-window", type=int, default=3)
    parser.add_argument(
        "--stat-local-refine-beam",
        type=int,
        default=6,
        help="Keep this many replayable intermediate gem orders during local refinement.",
    )
    parser.add_argument(
        "--stat-local-refine-trials",
        type=int,
        default=18,
        help="Replay at most this many cheap-ranked gem-order variants per refinement pass.",
    )
    parser.add_argument(
        "--stat-local-refine-order-depth",
        type=int,
        default=2,
        help="Generate this many semantic reorder moves before requiring real-floor replay.",
    )
    parser.add_argument(
        "--stat-local-refine-jit-supply",
        action="store_true",
        help="Replay only stat/progress order and refill supply groups when the next backbone action is blocked.",
    )
    parser.add_argument(
        "--stat-certified-order-prune",
        action="store_true",
        help="After replaying local gem-order variants, drop only exact duplicate or monotone-dominated orders.",
    )
    parser.add_argument("--report-every", type=int, default=20)
    parser.add_argument("--source-limit", type=int, default=8)
    parser.add_argument("--frontier-limit", type=int, default=16)
    parser.add_argument("--per-prefix", type=int, default=2)
    parser.add_argument("--trace-frontier", type=int, default=0)
    parser.add_argument("--entry-limit", type=int, default=520)
    parser.add_argument("--supply-policy", choices=["needed", "always"], default="needed")
    parser.add_argument("--supply-depth", type=int, default=2)
    parser.add_argument(
        "--stat-extra-key-supply-depth",
        type=int,
        default=1,
        help="Add bounded supply-closure depth near 27/27 when YK is nearly exhausted.",
    )
    parser.add_argument(
        "--stat-supply-package-dp",
        action="store_true",
        help="During stat supply closure, preserve representatives for each net YK/BK/HP supply package bucket.",
    )
    parser.add_argument(
        "--stat-supply-package-per-bucket",
        type=int,
        default=1,
        help="Keep this many Pareto representatives per stat supply package bucket before the usual width trim.",
    )
    parser.add_argument(
        "--supply-dominance-prune",
        action="store_true",
        help=(
            "Prune same-progress supply packages dominated on damage, doors, HP, stats, and keys. "
            "Intended for key/potion package comparisons such as low-damage +2 YK vs high-damage +1 YK."
        ),
    )
    parser.add_argument(
        "--supply-net-stock-dominance",
        action="store_true",
        help=(
            "When --supply-dominance-prune and --net-pocket-raw-stock are enabled, allow a supply package "
            "with extra yellow/blue door count to dominate if its audited raw stock, damage, HP, stats, and keys are no worse."
        ),
    )
    parser.add_argument(
        "--stat-gem-mask-frontier",
        action="store_true",
        help="Reserve bounded stat-frontier representatives per collected-gem mask and MT10 reachability bucket.",
    )
    parser.add_argument(
        "--stat-gem-mask-per-bucket",
        type=int,
        default=2,
        help="Keep this many representatives per gem-mask frontier bucket when --stat-gem-mask-frontier is enabled.",
    )
    parser.add_argument("--supply-width", type=int, default=7)
    parser.add_argument("--supply-targets", type=int, default=7)
    parser.add_argument("--supply-edges", type=int, default=5)
    parser.add_argument("--backbone-targets", type=int, default=8)
    parser.add_argument("--backbone-edges", type=int, default=8)
    parser.add_argument("--backbone-bridge-depth", type=int, default=3)
    parser.add_argument("--backbone-bridge-width", type=int, default=6)
    parser.add_argument("--continue-final", action="store_true")
    parser.add_argument("--carry-limit", type=int, default=12)
    parser.add_argument("--redkey-rounds", type=int, default=6)
    parser.add_argument("--boss-rounds", type=int, default=6)
    parser.add_argument("--final-entry-limit", type=int, default=520)
    parser.add_argument("--final-source-limit", type=int, default=14)
    parser.add_argument(
        "--final-checkpoint-cache",
        default="",
        help="Optional JSON path for persisting red-key and boss recovery checkpoints with exact expanded-state memo.",
    )
    parser.add_argument(
        "--final-checkpoint-cache-limit",
        type=int,
        default=1000,
        help="Keep at most this many representative checkpoints per final recovery stage.",
    )
    parser.add_argument("--final-targets", type=int, default=0)
    parser.add_argument("--final-edges", type=int, default=24)
    parser.add_argument("--final-supply-depth", type=int, default=2)
    parser.add_argument("--final-supply-width", type=int, default=10)
    parser.add_argument("--final-bridge-depth", type=int, default=3)
    parser.add_argument("--final-bridge-width", type=int, default=8)
    parser.add_argument("--max-iter", type=int, default=500000)
    args = parser.parse_args()
    set_output_tag(args.output_tag)
    data = run(args)
    write_outputs(data)
    print(f"wrote {OUT_JSON}")
    print(f"wrote {OUT_MD}")
    if data["best"]:
        print(f"wrote {OUT_WALK}")


if __name__ == "__main__":
    main()
