#!/usr/bin/env python3
"""Auto-discover post-9 resource groups and search them with Pareto trimming.

This is an experiment alongside post9_resource_group_search.py.  The older
resource-group script ranks states with a hand-written group table.  This file
does not trust hand-written door/monster costs: for each candidate resource
coordinate it runs the existing floor search, and treats the returned route
visited set as a dynamic resource-group edge.
"""

from __future__ import annotations

import argparse
import heapq
import json
import os
import sys
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Iterable


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.chdir(ROOT)

from scripts import continue_delayed_phase1_with_post9_resource as delayed
from scripts import post9_action_search as p9
from scripts import post9_resource_group_search as rg
from scripts import gen_delayed_phase1_detailed_walk as detail_walk
from src.solver import gen_walkthrough as gw
from src.solver.full_search import FLOOR_13_COLLECTED, calc_dmg


OUT_JSON = os.path.join("outputs", "results", "post9_auto_resource_group_pareto.json")
OUT_MD = os.path.join("outputs", "reports", "post9_auto_resource_group_pareto.md")
OUT_WALK = os.path.join("outputs", "walkthroughs", "walkthrough_post9_auto_resource_group_best.md")
OUT_WALK_DETAIL = os.path.join("outputs", "walkthroughs", "walkthrough_post9_auto_resource_group_best_detailed.md")

RESOURCE_IDS = {
    "redGem",
    "blueGem",
    "yellowKey",
    "blueKey",
    "redKey",
    "redPotion",
    "bluePotion",
}
REDKEY_REQUIRED_MONSTERS = (
    ((6, 8), "skeleton"),
    ((8, 8), "bluePriest"),
    ((9, 5), "yellowGuard"),
    ((11, 5), "yellowGuard"),
)

ITEM_CN = {
    "redGem": "红宝石",
    "blueGem": "蓝宝石",
    "yellowKey": "黄钥匙",
    "blueKey": "蓝钥匙",
    "redKey": "红钥匙",
    "redPotion": "红血瓶",
    "bluePotion": "蓝血瓶",
    "yellowDoor": "黄门",
    "blueDoor": "蓝门",
    "redDoor": "红门",
    "greenSlime": "绿史莱姆",
    "redSlime": "红史莱姆",
    "bat": "小蝙蝠",
    "skeleton": "骷髅",
    "skeletonSoldier": "骷髅士兵",
    "bluePriest": "蓝法师",
    "yellowGuard": "初级卫兵",
    "skeletonCaptain": "骷髅队长",
    "upFloor": "上楼",
}


@dataclass(frozen=True)
class AutoTarget:
    fid: str
    pos: tuple[int, int]
    eid: str

    @property
    def label(self) -> str:
        x, y = self.pos
        return f"{self.fid} x{x}y{y} {self.eid}"


def all_targets() -> list[AutoTarget]:
    targets: list[AutoTarget] = []
    for fid, data in sorted(gw.maps.items(), key=lambda kv: int(kv[0][2:])):
        precollected = FLOOR_13_COLLECTED.get(fid, frozenset())
        for x, y, t, eid in data["bl"]:
            if t == 3 and eid in RESOURCE_IDS and (x, y) not in precollected:
                targets.append(AutoTarget(fid, (x, y), eid))
    return targets


TARGETS = all_targets()


def collected_for(ent: dict[str, Any], fid: str) -> frozenset[tuple[int, int]]:
    got = set(ent.get("collected", {}).get(fid, frozenset()))
    got.update(FLOOR_13_COLLECTED.get(fid, frozenset()))
    return frozenset(got)


def item_positions(fid: str, eid: str) -> frozenset[tuple[int, int]]:
    return frozenset((x, y) for x, y, _t, item in gw.maps[fid]["bl"] if item == eid)


def pos_eid(fid: str, pos: tuple[int, int]) -> str | None:
    for x, y, _t, eid in gw.maps[fid]["bl"]:
        if (x, y) == pos:
            return eid
    return None


def target_value(ent: dict[str, Any], eid: str) -> int:
    if eid == "redGem":
        return rg.ATK_GEM_VALUE if ent["atk"] < 27 else 0
    if eid == "blueGem":
        return rg.DEF_GEM_VALUE if ent["def"] < 27 else 0
    if eid == "yellowKey":
        return rg.YK_VALUE
    if eid == "blueKey":
        return rg.BK_VALUE
    if eid == "redKey":
        return rg.RED_KEY_VALUE if ent["rk"] < 1 else 0
    if eid == "redPotion":
        return 50
    if eid == "bluePotion":
        return 200
    return 0


def redkey_survival_deficit(ent: dict[str, Any]) -> int:
    if ent["atk"] < 27 or ent["def"] < 27 or ent["rk"] >= 1:
        return 10**9
    collected = collected_for(ent, "MT8")
    required = 1
    for pos, enemy in REDKEY_REQUIRED_MONSTERS:
        if pos not in collected:
            required += calc_dmg(enemy, ent["atk"], ent["def"])
    return max(0, required - ent["hp"])


def phase_survival_deficit(ent: dict[str, Any]) -> int:
    if ent["rk"] >= 1:
        return p9.boss_survival_deficit(ent)
    if ent["atk"] >= 27 and ent["def"] >= 27:
        return redkey_survival_deficit(ent)
    return 0


def useful_target(ent: dict[str, Any], target: AutoTarget) -> bool:
    if target.pos in collected_for(ent, target.fid):
        return False
    if target.eid == "redGem":
        return ent["atk"] < 27
    if target.eid == "blueGem":
        return ent["def"] < 27
    if target.eid == "redKey":
        return ent["atk"] >= 27 and ent["def"] >= 27 and ent["rk"] < 1 and redkey_survival_deficit(ent) == 0
    if target.eid == "blueKey":
        return ent["bk"] < 1 or ("MT10" not in ent.get("collected", {}) and p9.needs_mt10_for_stats(ent))
    if target.eid == "yellowKey":
        # Keep cheap future-key options alive before MT10/red-key.  The edge
        # cost is still computed by real search; this only limits target count.
        return ent["yk"] < max(4, p9.desired_yk(ent) + 2)
    if target.eid in {"redPotion", "bluePotion"}:
        return (
            p9.hp_deficit_for_resources(ent) > 0
            or phase_survival_deficit(ent) > 0
            or ent["atk"] >= 27
            or ent["def"] >= 27
            or target.eid == "bluePotion"
        )
    return target_value(ent, target.eid) > 0


def candidate_targets(ent: dict[str, Any], max_targets: int) -> list[AutoTarget]:
    items = [t for t in TARGETS if useful_target(ent, t)]
    forced = [
        t for t in items
        if (
            t.eid == "redKey"
            or (t.fid == "MT10" and t.eid in {"redGem", "blueGem"} and target_value(ent, t.eid) > 0)
        )
    ]
    forced_keys = {(t.fid, t.pos, t.eid) for t in forced}
    items = [t for t in items if (t.fid, t.pos, t.eid) not in forced_keys]

    def rank(t: AutoTarget) -> tuple[int, int, int, int, int]:
        value = target_value(ent, t.eid)
        if t.eid == "blueGem":
            phase = 0 if ent["def"] < 27 else 4
        elif t.eid == "redGem":
            phase = 1 if ent["atk"] < 27 else 4
        elif t.eid in {"yellowKey", "blueKey"}:
            phase = 2
        elif t.eid == "redKey":
            phase = 3
        else:
            phase = 4
        return (phase, -value, int(t.fid[2:]), t.pos[0], t.pos[1])

    if max_targets <= 0:
        return sorted(forced, key=rank) + sorted(items, key=rank)
    remaining = max(0, max_targets - len(forced))
    return sorted(forced, key=rank) + sorted(items, key=rank)[:remaining]


def describe_new_blocks(fid: str, before: frozenset[tuple[int, int]], vis: frozenset[tuple[int, int]]) -> dict[str, Any]:
    items = []
    doors = []
    monsters = []
    for x, y, t, eid in gw.maps[fid]["bl"]:
        pos = (x, y)
        if pos not in vis or pos in before:
            continue
        rec = {"pos": f"x{x}y{y}", "eid": eid, "name": ITEM_CN.get(eid, eid)}
        if t == 3 and eid in RESOURCE_IDS:
            items.append(rec)
        elif t == 2:
            doors.append(rec)
        elif t == 1:
            monsters.append(rec)
    return {"items": items, "doors": doors, "monsters": monsters}


def summarize_group(desc: dict[str, Any]) -> str:
    parts = []
    for key in ("items", "doors", "monsters"):
        if not desc[key]:
            continue
        label = {"items": "取", "doors": "门", "monsters": "怪"}[key]
        vals = ",".join(f"{r['pos']}{r['name']}" for r in desc[key][:6])
        if len(desc[key]) > 6:
            vals += "..."
        parts.append(f"{label}:{vals}")
    return "; ".join(parts) if parts else "-"


def state_text(ent: dict[str, Any]) -> str:
    return (
        f"HP={ent['hp']} ATK={ent['atk']} DEF={ent['def']} "
        f"YK={ent['yk']} BK={ent['bk']} RK={ent['rk']} "
        f"dmg={ent.get('_dmg', 0)} door={ent.get('_yd', 0)}/{ent.get('_bd', 0)}/{ent.get('_rd', 0)}"
    )


def result_signature(ent: dict[str, Any]) -> tuple[Any, ...]:
    return (
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
    )


def make_edge_result(
    base_ent: dict[str, Any],
    fid: str,
    eid: str,
    flyback: bool,
    hp: int,
    yk: int,
    bk: int,
    rk: int,
    atk: int,
    def_: int,
    vis: frozenset[tuple[int, int]],
    dc: int,
    label: str,
) -> dict[str, Any]:
    before = collected_for(base_ent, fid)
    nc = dict(base_ent.get("collected", {}))
    nc[fid] = before | vis
    r = gw._make_result(
        hp,
        yk,
        bk,
        rk,
        atk,
        def_,
        nc,
        base_ent["_id"],
        (fid, [eid], flyback),
        dmg_cost=dc,
    )
    desc = describe_new_blocks(fid, before, vis)
    r["_last_action"] = label
    r["_resource_group"] = desc
    if eid == "redDoor":
        r["_edge_kind"] = "boss"
    elif eid == "upFloor":
        r["_edge_kind"] = "progress"
    elif eid == "redKey":
        r["_edge_kind"] = "redkey"
    elif atk > base_ent["atk"] or def_ > base_ent["def"]:
        r["_edge_kind"] = "stat"
    elif yk > base_ent["yk"] or bk > base_ent["bk"] or rk > base_ent["rk"]:
        r["_edge_kind"] = "key"
    elif hp > base_ent["hp"]:
        r["_edge_kind"] = "potion"
    else:
        r["_edge_kind"] = "other"
    r["_delta_hp"] = hp - base_ent["hp"]
    r["_delta_dmg"] = r.get("_dmg", 0) - base_ent.get("_dmg", 0)
    r["_delta_yd"] = r.get("_yd", 0) - base_ent.get("_yd", 0)
    r["_delta_bd"] = r.get("_bd", 0) - base_ent.get("_bd", 0)
    r["_delta_rd"] = r.get("_rd", 0) - base_ent.get("_rd", 0)
    r["_delta_yk"] = yk - base_ent["yk"]
    r["_delta_bk"] = bk - base_ent["bk"]
    r["_delta_rk"] = rk - base_ent["rk"]
    r["_delta_atk"] = atk - base_ent["atk"]
    r["_delta_def"] = def_ - base_ent["def"]
    gw._entry_store[r["_id"]]["_last_action"] = label
    gw._entry_store[r["_id"]]["_resource_group"] = desc
    gw._entry_store[r["_id"]]["_edge_kind"] = r["_edge_kind"]
    gw._entry_store[r["_id"]]["_delta_hp"] = r["_delta_hp"]
    gw._entry_store[r["_id"]]["_delta_dmg"] = r["_delta_dmg"]
    gw._entry_store[r["_id"]]["_delta_yd"] = r["_delta_yd"]
    gw._entry_store[r["_id"]]["_delta_bd"] = r["_delta_bd"]
    gw._entry_store[r["_id"]]["_delta_rd"] = r["_delta_rd"]
    gw._entry_store[r["_id"]]["_delta_yk"] = r["_delta_yk"]
    gw._entry_store[r["_id"]]["_delta_bk"] = r["_delta_bk"]
    gw._entry_store[r["_id"]]["_delta_rk"] = r["_delta_rk"]
    gw._entry_store[r["_id"]]["_delta_atk"] = r["_delta_atk"]
    gw._entry_store[r["_id"]]["_delta_def"] = r["_delta_def"]
    return r


def mark_mt10_reached(ent: dict[str, Any]) -> dict[str, Any]:
    """Mark MT10 as reachable after a successful MT9 upFloor transition."""
    nc = dict(ent.get("collected", {}))
    nc.setdefault("MT10", frozenset())
    ent["collected"] = nc
    gw._entry_store[ent["_id"]]["collected"] = nc
    return ent


def exact_item_edges(
    ent: dict[str, Any],
    fid: str,
    eid: str,
    desired_positions: set[tuple[int, int]],
    max_iter: int,
) -> list[dict[str, Any]]:
    if not desired_positions:
        return []
    bases = [ent]
    if fid == "MT10" and "MT10" not in ent.get("collected", {}):
        # The auto resource graph models MT9 -> MT10 as a separate progress
        # edge.  Do not hide key-pocket refills inside a MT10 item edge.
        return []
    out: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    for base in bases:
        if eid == "redKey" and base["rk"] >= 1:
            continue
        before = collected_for(base, fid)
        pending = desired_positions - before
        if not pending:
            continue
        flyback = fid in base.get("collected", {})
        search_max_iter = max_iter
        if eid == "redKey":
            # MT8 red-key route includes a special guard-opened passage and is
            # consistently deeper than normal item pockets.  The legacy boss
            # pipeline uses 500k here; using the global 140k/160k cap makes
            # valid red-key-ready states look unreachable.
            search_max_iter = max(max_iter, 500000)
        search_variants: list[tuple[frozenset[tuple[int, int]], str]] = [(frozenset(), "")]
        if eid == "blueGem":
            sibling = item_positions(fid, "redGem") - before
            if sibling:
                search_variants.append((sibling, " pure-no-redGem"))
        elif eid == "redGem":
            sibling = item_positions(fid, "blueGem") - before
            if sibling:
                search_variants.append((sibling, " pure-no-blueGem"))

        for extra_removed, variant_label in search_variants:
            pareto, _it, _nodes = gw.search_floor(
                gw.maps,
                fid,
                base,
                [eid],
                flyback=flyback,
                max_iter=search_max_iter,
                extra_removed=extra_removed,
            )
            for hp, yk, bk, rk, atk, def_, _hs, vis, dc in pareto or []:
                hit = pending & vis
                if not hit:
                    continue
                hit_text = "+".join(f"x{x}y{y}" for x, y in sorted(hit))
                label = f"{fid} {eid} flyback={flyback} [{hit_text}]{variant_label}"
                r = make_edge_result(base, fid, eid, flyback, hp, yk, bk, rk, atk, def_, vis, dc, label)
                sig = result_signature(r)
                if sig in seen:
                    continue
                seen.add(sig)
                out.append(r)
    return out


def boss_edges(ent: dict[str, Any]) -> list[dict[str, Any]]:
    if ent["atk"] < 27 or ent["def"] < 27 or ent["rk"] < 1:
        return []
    out: list[dict[str, Any]] = []
    red_doors = item_positions("MT10", "redDoor")
    if "MT10" not in ent.get("collected", {}):
        return []
    for base in [ent]:
        before = collected_for(base, "MT10")
        flyback = "MT10" in base.get("collected", {})
        pareto, _it, _nodes = gw.search_floor(gw.maps, "MT10", base, ["redDoor"], flyback=flyback, max_iter=250000)
        for hp, yk, bk, rk, atk, def_, _hs, vis, dc in pareto or []:
            if not (vis & red_doors):
                continue
            extra = gw.boss_event_damage(atk, def_) + calc_dmg("skeletonCaptain", atk, def_)
            if hp - extra <= 0:
                continue
            label = f"MT10 redDoor flyback={flyback} [boss]"
            out.append(
                make_edge_result(
                    base,
                    "MT10",
                    "redDoor",
                    flyback,
                    hp - extra,
                    yk,
                    bk,
                    rk,
                    atk,
                    def_,
                    vis,
                    dc + extra,
                    label,
                )
            )
    return out


def progress_edges(ent: dict[str, Any], max_iter: int) -> list[dict[str, Any]]:
    """Expose MT9 -> MT10 as an explicit compressed edge.

    Targeting MT10 resources can trigger this transition implicitly through
    rg.ensure_mt10().  Keeping it as its own edge preserves clean "arrive on
    10F" labels for later refill/red-key planning.
    """
    if "MT10" in ent.get("collected", {}):
        return []
    if ent["yk"] < 1 or ent["bk"] < 1:
        return []
    if not (
        p9.needs_mt10_for_stats(ent)
        or ent["atk"] >= 26
        or ent["def"] >= 26
        or (ent["atk"] >= 27 and ent["def"] >= 27)
    ):
        return []

    desired = item_positions("MT9", "upFloor")
    before = collected_for(ent, "MT9")
    pending = desired - before
    if not pending:
        return []

    out: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    pareto, _it, _nodes = gw.search_floor(
        gw.maps,
        "MT9",
        ent,
        ["upFloor"],
        flyback=True,
        max_iter=max_iter,
    )
    for hp, yk, bk, rk, atk, def_, _hs, vis, dc in pareto or []:
        if not (pending & vis):
            continue
        label = "MT9 upFloor flyback=True [progress]"
        r = make_edge_result(ent, "MT9", "upFloor", True, hp, yk, bk, rk, atk, def_, vis, dc, label)
        mark_mt10_reached(r)
        sig = result_signature(r)
        if sig in seen:
            continue
        seen.add(sig)
        out.append(r)
    return out


def edge_rank(ent: dict[str, Any]) -> tuple[int, ...]:
    kind_order = {
        "boss": 0,
        "redkey": 1,
        "progress": 2,
        "stat": 3,
        "key": 4,
        "potion": 5,
        "other": 6,
    }.get(ent.get("_edge_kind"), 6)
    return (
        0 if p9.goal(ent) else 1,
        kind_order,
        rg.resource_group_score(ent),
        p9.stat_deficit(ent),
        redkey_survival_deficit(ent),
        p9.boss_survival_deficit(ent),
        ent.get("_dmg", 0),
    )


def kind_edge_rank(ent: dict[str, Any]) -> tuple[int, ...]:
    kind = ent.get("_edge_kind")
    if kind == "boss":
        return (0 if p9.goal(ent) else 1, ent.get("_dmg", 0), -ent["hp"])
    if kind == "redkey":
        return (0 if ent["rk"] >= 1 else 1, ent.get("_dmg", 0), -ent["hp"], -ent["yk"])
    if kind == "progress":
        return (
            p9.stat_deficit(ent),
            max(0, 1 - ent["yk"]),
            max(0, 1 - ent["bk"]),
            rg.resource_group_score(ent),
            ent.get("_dmg", 0),
            -ent["hp"],
        )
    if kind == "stat":
        stat_gain = max(1, ent.get("_delta_atk", 0) + ent.get("_delta_def", 0))
        stat_eff_cost = (
            ent.get("_delta_dmg", 0)
            + ent.get("_delta_yd", 0) * rg.YK_VALUE
            + ent.get("_delta_bd", 0) * rg.BK_VALUE
        ) // stat_gain
        return (
            p9.stat_deficit(ent),
            stat_eff_cost,
            -ent.get("_delta_def", 0),
            -ent.get("_delta_atk", 0),
            rg.resource_group_score(ent),
            ent.get("_dmg", 0),
            -ent["hp"],
        )
    if kind == "key":
        return (
            -(ent.get("_delta_yk", 0) * 10 + ent.get("_delta_bk", 0) * 40),
            max(0, p9.desired_yk(ent) - ent["yk"]),
            rg.resource_group_score(ent),
            ent.get("_dmg", 0),
            -ent["hp"],
        )
    if kind == "potion":
        return (
            phase_survival_deficit(ent),
            -max(0, ent.get("_delta_hp", 0)),
            rg.resource_group_score(ent),
            ent.get("_dmg", 0),
            -ent["hp"],
        )
    return edge_rank(ent)


def label_stage(ent: dict[str, Any]) -> int:
    if p9.goal(ent):
        return 0
    elif ent["rk"] >= 1:
        return 1
    elif ent["atk"] >= 27 and ent["def"] >= 27 and ent["yk"] >= 1 and redkey_survival_deficit(ent) == 0:
        return 2
    elif ent["atk"] >= 27 and ent["def"] >= 27:
        return 3
    elif "MT10" in ent.get("collected", {}):
        return 4
    return 5


def label_priority_stage(ent: dict[str, Any]) -> tuple[int, ...]:
    stage = label_stage(ent)
    return (
        stage,
        p9.stat_deficit(ent),
        redkey_survival_deficit(ent) if ent["atk"] >= 27 and ent["def"] >= 27 and ent["rk"] < 1 else 0,
        p9.boss_survival_deficit(ent) if ent["rk"] >= 1 else 0,
        ent.get("_dmg", 0),
        ent.get("_yd", 0),
        ent.get("_bd", 0),
        -ent["hp"],
        rg.resource_group_score(ent),
    )


def label_priority_score(ent: dict[str, Any]) -> tuple[int, ...]:
    stage = label_stage(ent)
    return (
        rg.resource_group_score(ent),
        ent.get("_dmg", 0),
        ent.get("_yd", 0),
        ent.get("_bd", 0),
        -ent["hp"],
        stage,
        p9.stat_deficit(ent),
        redkey_survival_deficit(ent) if ent["atk"] >= 27 and ent["def"] >= 27 and ent["rk"] < 1 else 0,
        p9.boss_survival_deficit(ent) if ent["rk"] >= 1 else 0,
    )


def label_priority_balanced(ent: dict[str, Any]) -> tuple[int, ...]:
    stage = label_stage(ent)
    return (
        rg.resource_group_score(ent) + stage * 350,
        stage,
        p9.stat_deficit(ent),
        redkey_survival_deficit(ent) if ent["atk"] >= 27 and ent["def"] >= 27 and ent["rk"] < 1 else 0,
        p9.boss_survival_deficit(ent) if ent["rk"] >= 1 else 0,
        ent.get("_dmg", 0),
        ent.get("_yd", 0),
        ent.get("_bd", 0),
        -ent["hp"],
    )


def make_label_priority(mode: str) -> Any:
    if mode == "score":
        return label_priority_score
    if mode == "balanced":
        return label_priority_balanced
    return label_priority_stage


def generate_edges(ent: dict[str, Any], max_targets: int, max_iter: int, edge_limit: int) -> list[dict[str, Any]]:
    by_floor_eid: dict[tuple[str, str], set[tuple[int, int]]] = defaultdict(set)
    for target in candidate_targets(ent, max_targets):
        by_floor_eid[(target.fid, target.eid)].add(target.pos)

    edges: list[dict[str, Any]] = []
    for (fid, eid), positions in sorted(by_floor_eid.items(), key=lambda item: (int(item[0][0][2:]), item[0][1])):
        edges.extend(exact_item_edges(ent, fid, eid, positions, max_iter=max_iter))
    edges.extend(progress_edges(ent, max_iter=max_iter))
    edges.extend(boss_edges(ent))

    dedup: dict[tuple[Any, ...], dict[str, Any]] = {}
    for edge in edges:
        sig = result_signature(edge)
        old = dedup.get(sig)
        if old is None or edge_rank(edge) < edge_rank(old):
            dedup[sig] = edge
    ranked = sorted(dedup.values(), key=edge_rank)
    if edge_limit <= 0:
        return ranked
    chosen: list[dict[str, Any]] = []
    seen_ids: set[int] = set()

    def add(items: Iterable[dict[str, Any]], quota: int) -> None:
        added = 0
        for edge in items:
            if edge["_id"] in seen_ids:
                continue
            seen_ids.add(edge["_id"])
            chosen.append(edge)
            added += 1
            if added >= quota:
                return

    # Keep stage-progress edges even when their immediate score is worse than
    # cheap refill/resource edges.  Otherwise the compressed graph keeps
    # circling around resources and never tries red key / boss transitions.
    add(sorted([e for e in ranked if e.get("_edge_kind") == "boss"], key=kind_edge_rank), 4)
    add(sorted([e for e in ranked if e.get("_edge_kind") == "redkey"], key=kind_edge_rank), 6)
    add(sorted([e for e in ranked if e.get("_edge_kind") == "progress"], key=kind_edge_rank), max(4, edge_limit // 3))
    add(sorted([e for e in ranked if e.get("_edge_kind") == "stat"], key=kind_edge_rank), max(5, edge_limit // 2))
    add(sorted([e for e in ranked if e.get("_edge_kind") == "key"], key=kind_edge_rank), max(6, edge_limit // 2))
    add(sorted([e for e in ranked if e.get("_edge_kind") == "potion"], key=kind_edge_rank), max(5, edge_limit // 2))
    add(ranked, edge_limit)
    return chosen[: max(edge_limit, len(chosen))]


def dominates(a: dict[str, Any], b: dict[str, Any]) -> bool:
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
    )
    return strict or (same_core and a["hp"] >= b["hp"])


def pareto_filter(entries: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for ent in entries:
        groups[gw._collected_signature(ent)].append(ent)

    out: list[dict[str, Any]] = []
    for group in groups.values():
        local: list[dict[str, Any]] = []
        for ent in sorted(group, key=lambda e: (e.get("_dmg", 0), e.get("_yd", 0), e.get("_bd", 0), -e["hp"])):
            if any(dominates(p, ent) for p in local):
                continue
            local = [p for p in local if not dominates(ent, p)]
            local.append(ent)
        out.extend(local)
    return out


def trim_entries(entries: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    filtered = pareto_filter(entries)
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
            if len(chosen) >= limit or added >= quota:
                return

    def add_bucket_best(
        items: Iterable[dict[str, Any]],
        key_fn: Any,
        sort_key: Any,
        quota: int,
        per_bucket: int = 1,
    ) -> None:
        buckets: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
        for ent in items:
            buckets[key_fn(ent)].append(ent)
        heads: list[dict[str, Any]] = []
        for bucket_items in buckets.values():
            heads.extend(sorted(bucket_items, key=sort_key)[:per_bucket])
        add(sorted(heads, key=sort_key), quota)

    def stat_stage_bucket(e: dict[str, Any]) -> tuple[Any, ...]:
        mt8 = collected_for(e, "MT8")
        mt1 = collected_for(e, "MT1")
        mt3 = collected_for(e, "MT3")
        mt7 = collected_for(e, "MT7")
        return (
            min(e["atk"], 27),
            min(e["def"], 27),
            min(e["yk"], 4),
            min(e["bk"], 1),
            "MT10" in e.get("collected", {}),
            (4, 10) in mt8 or (5, 11) in mt8,
            (7, 4) in mt1,
            (2, 1) in mt3,
            (3, 1) in mt7,
        )

    stat_low_cost_key = lambda e: (
        e.get("_dmg", 0),
        e.get("_yd", 0),
        e.get("_bd", 0),
        redkey_survival_deficit(e),
        -e["hp"],
        -e["yk"],
        -e["bk"],
        rg.resource_group_score(e),
    )

    goals = [e for e in filtered if p9.goal(e)]
    add(sorted(goals, key=lambda e: (-rg.final_resource_stock(e), rg.resource_group_score(e))), limit)
    redkey_ready = [
        e for e in filtered
        if e["atk"] >= 27 and e["def"] >= 27 and e["rk"] < 1 and e["yk"] >= 1
    ]
    add(
        sorted(
            redkey_ready,
            key=lambda e: (
                redkey_survival_deficit(e),
                -e["yk"],
                -e["bk"],
                rg.resource_group_score(e),
                e.get("_dmg", 0),
                -e["hp"],
            ),
        ),
        max(12, limit // 12),
    )
    stat_done_refill = [
        e for e in filtered
        if e["atk"] >= 27 and e["def"] >= 27 and e["rk"] < 1
    ]
    mt10_stat_pending = [
        e for e in filtered
        if "MT10" in e.get("collected", {}) and (e["atk"] < 27 or e["def"] < 27)
    ]
    stat_pending = [e for e in filtered if e["atk"] < 27 or e["def"] < 27]
    add_bucket_best(
        stat_pending,
        stat_stage_bucket,
        stat_low_cost_key,
        max(24, limit // 4),
        per_bucket=2,
    )
    add(
        sorted(
            mt10_stat_pending,
            key=lambda e: (
                p9.stat_deficit(e),
                max(0, 1 - e["yk"]),
                rg.resource_group_score(e),
                e.get("_dmg", 0),
                -e["hp"],
            ),
        ),
        max(12, limit // 10),
    )
    add(
        sorted(
            stat_done_refill,
            key=lambda e: (
                max(0, 1 - e["yk"]),
                redkey_survival_deficit(e),
                -e["hp"],
                rg.resource_group_score(e),
            ),
        ),
        max(12, limit // 12),
    )
    add(
        sorted(
            stat_done_refill,
            key=lambda e: (
                redkey_survival_deficit(e),
                max(0, 1 - e["yk"]),
                -e["hp"],
                -e["yk"],
                rg.resource_group_score(e),
            ),
        ),
        max(12, limit // 10),
    )
    add(
        sorted(
            stat_done_refill,
            key=lambda e: (
                max(0, 1 - e["yk"]),
                -e["hp"],
                redkey_survival_deficit(e),
                -e["yk"],
                rg.resource_group_score(e),
            ),
        ),
        max(12, limit // 10),
    )
    phases = [
        [e for e in filtered if e["atk"] < 27 or e["def"] < 27],
        [e for e in filtered if e["atk"] >= 27 and e["def"] >= 27 and e["rk"] < 1],
        [e for e in filtered if e["atk"] >= 27 and e["def"] >= 27 and e["rk"] >= 1 and not p9.goal(e)],
    ]
    selectors = [
        lambda e: (rg.resource_group_score(e), e.get("_dmg", 0), -e["hp"]),
        lambda e: (p9.stat_deficit(e), rg.resource_group_score(e), -e["def"], -e["atk"]),
        lambda e: (redkey_survival_deficit(e), rg.resource_group_score(e), -e["yk"], -e["hp"]),
        lambda e: (p9.boss_survival_deficit(e), rg.resource_group_score(e), -e["yk"], -e["hp"]),
        lambda e: (-rg.final_resource_stock(e), rg.resource_group_score(e), e.get("_dmg", 0)),
        lambda e: (-e["yk"], -e["bk"], rg.resource_group_score(e), e.get("_dmg", 0)),
    ]
    quota = max(8, limit // (len(phases) * len(selectors)))
    for phase in phases:
        for selector in selectors:
            add(sorted(phase, key=selector), quota)
            if len(chosen) >= limit:
                return chosen[:limit]
    add(sorted(filtered, key=lambda e: (rg.resource_group_score(e), e.get("_dmg", 0), -e["hp"])), limit)
    return chosen[:limit]


def compact(ent: dict[str, Any]) -> dict[str, Any]:
    return {
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
        "old_score": rg.old_score(ent),
        "resource_group_score": rg.resource_group_score(ent),
        "final_resource_stock": rg.final_resource_stock(ent),
        "final_residual_value": rg.final_residual_resource_value(ent),
        "last_action": ent.get("_last_action") or ent.get("_source") or p9.action_summary(ent),
        "edge_kind": ent.get("_edge_kind", "-"),
        "delta_hp": ent.get("_delta_hp", 0),
        "delta_dmg": ent.get("_delta_dmg", 0),
        "delta_yd": ent.get("_delta_yd", 0),
        "delta_bd": ent.get("_delta_bd", 0),
        "delta_yk": ent.get("_delta_yk", 0),
        "delta_bk": ent.get("_delta_bk", 0),
        "delta_atk": ent.get("_delta_atk", 0),
        "delta_def": ent.get("_delta_def", 0),
    }


def write_walk(best: dict[str, Any], phase1_id: int) -> None:
    chain = gw.trace_chain(best)
    lines = [
        "# Post-9 Auto Resource Group Pareto Best Walk",
        "",
        f"> final: {state_text(best)}",
        "",
    ]
    for idx, ent in enumerate(chain):
        if idx == 0:
            label = "4F search start"
        elif ent.get("_id") == phase1_id:
            label = "phase1 delayed prefix complete"
        else:
            label = ent.get("_last_action") or ent.get("_source") or p9.action_summary(ent)
        prev = chain[idx - 1] if idx else None
        lines.extend([f"## {idx}. {label}", "", f"- {state_text(ent)}"])
        if prev:
            lines.append(
                f"- segment dmg={ent.get('_dmg', 0) - prev.get('_dmg', 0)} "
                f"door delta={ent.get('_yd', 0) - prev.get('_yd', 0)}/"
                f"{ent.get('_bd', 0) - prev.get('_bd', 0)}/"
                f"{ent.get('_rd', 0) - prev.get('_rd', 0)}"
            )
            desc = ent.get("_resource_group")
            if desc:
                lines.append(f"- auto group: {summarize_group(desc)}")
        lines.append("")
    os.makedirs(os.path.dirname(OUT_WALK), exist_ok=True)
    with open(OUT_WALK, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")

    old_in, old_out = detail_walk.IN_WALK, detail_walk.OUT_WALK
    try:
        detail_walk.IN_WALK = OUT_WALK
        detail_walk.OUT_WALK = OUT_WALK_DETAIL
        detail_walk.main()
    except Exception:
        # The compact walk is still the authoritative artifact for this
        # prototype.  Detailed replay may not understand every bracket label.
        pass
    finally:
        detail_walk.IN_WALK = old_in
        detail_walk.OUT_WALK = old_out


def audit_edges(start: dict[str, Any], max_targets: int, max_iter: int) -> list[dict[str, Any]]:
    edges = generate_edges(start, max_targets=max_targets, max_iter=max_iter, edge_limit=200)
    rows = []
    for edge in edges:
        prev = gw._entry_store.get(edge["_parent_id"], start)
        desc = edge.get("_resource_group", {})
        rows.append({
            "action": edge.get("_last_action") or p9.action_summary(edge),
            "state": compact(edge),
            "segment_dmg": edge.get("_dmg", 0) - prev.get("_dmg", 0),
            "segment_door": [
                edge.get("_yd", 0) - prev.get("_yd", 0),
                edge.get("_bd", 0) - prev.get("_bd", 0),
                edge.get("_rd", 0) - prev.get("_rd", 0),
            ],
            "group": desc,
            "group_text": summarize_group(desc),
            "edge_kind": edge.get("_edge_kind", "-"),
        })
    return rows


def audit_redkey_ready(entries: list[dict[str, Any]], max_iter: int) -> list[dict[str, Any]]:
    ready = [
        e for e in entries
        if e["atk"] >= 27 and e["def"] >= 27 and e["rk"] < 1 and e["yk"] >= 1
    ]
    ready = sorted(
        ready,
        key=lambda e: (
            redkey_survival_deficit(e),
            rg.resource_group_score(e),
            e.get("_dmg", 0),
            -e["hp"],
        ),
    )[:8]
    rows = []
    redkey_pos = set(item_positions("MT8", "redKey"))
    for ent in ready:
        mt8_collected = collected_for(ent, "MT8")
        pending = redkey_pos - mt8_collected
        flyback = "MT8" in ent.get("collected", {})
        raw, iters, _nodes = gw.search_floor(
            gw.maps,
            "MT8",
            ent,
            ["redKey"],
            flyback=flyback,
            max_iter=max(max_iter, 500000),
        )
        raw_hits = [
            {
                "hp": hp,
                "yk": yk,
                "bk": bk,
                "rk": rk,
                "atk": atk,
                "def": def_,
                "dmg": dc,
                "hit": bool(pending & vis),
            }
            for hp, yk, bk, rk, atk, def_, _hs, vis, dc in (raw or [])[:6]
        ]
        edges = exact_item_edges(ent, "MT8", "redKey", redkey_pos, max_iter=max_iter)
        chain = gw.trace_chain(ent)[-8:]
        rows.append({
            "state": compact(ent),
            "flyback": flyback,
            "pending": [f"x{x}y{y}" for x, y in sorted(pending)],
            "mt8_collected": [
                f"x{x}y{y}:{pos_eid('MT8', (x, y))}"
                for x, y in sorted(mt8_collected)
            ],
            "raw_count": len(raw or []),
            "raw_iters": iters,
            "raw_hits": raw_hits,
            "chain_tail": [
                e.get("_last_action") or e.get("_source") or p9.action_summary(e)
                for e in chain
            ],
            "edge_count": len(edges),
            "edges": [compact(e) for e in sorted(edges, key=edge_rank)[:4]],
        })
    return rows


def run(
    phase1_expansions: int,
    rounds: int,
    entry_limit: int,
    source_limit: int,
    max_targets: int,
    max_iter: int,
    edge_limit: int,
) -> dict[str, Any]:
    t0 = time.time()
    start, phase1_result = delayed.find_candidate(phase1_expansions)
    phase1_id = start["_id"]
    entries = [start]
    audit = audit_edges(start, max_targets=max_targets, max_iter=max_iter)
    rows = []
    for round_no in range(1, rounds + 1):
        sources = entries if source_limit <= 0 else trim_entries(entries, source_limit)
        new_results: list[dict[str, Any]] = []
        action_counts = []
        for ent in sources:
            before = len(new_results)
            new_results.extend(generate_edges(ent, max_targets=max_targets, max_iter=max_iter, edge_limit=edge_limit))
            gained = len(new_results) - before
            if gained:
                action_counts.append((ent["_id"], gained))
        if not new_results:
            break
        entries = trim_entries(entries + new_results, entry_limit)
        goals = rg.best_goals(entries)
        stat_done = [e for e in entries if e["atk"] >= 27 and e["def"] >= 27]
        redkey_ready = [e for e in stat_done if e["rk"] < 1 and e["yk"] >= 1]
        rk_entries = [e for e in entries if e["rk"] >= 1]
        mt10_entries = [e for e in entries if "MT10" in e.get("collected", {})]

        def best_of(items: list[dict[str, Any]]) -> dict[str, Any] | None:
            if not items:
                return None
            return compact(sorted(
                items,
                key=lambda e: (
                    p9.boss_survival_deficit(e),
                    redkey_survival_deficit(e),
                    rg.resource_group_score(e),
                    e.get("_dmg", 0),
                    -e["hp"],
                ),
            )[0])

        row = {
            "round": round_no,
            "sources": len(sources),
            "new": len(new_results),
            "entries": len(entries),
            "goals": len(goals),
            "stat_done": len(stat_done),
            "redkey_ready": len(redkey_ready),
            "rk_entries": len(rk_entries),
            "mt10_entries": len(mt10_entries),
            "best_goal": compact(goals[0]) if goals else None,
            "best_redkey_ready": best_of(redkey_ready),
            "best_rk": best_of(rk_entries),
        }
        rows.append(row)
        print(
            f"round {round_no}: sources={len(sources)} new={len(new_results)} "
            f"entries={len(entries)} stat27={len(stat_done)} redkeyReady={len(redkey_ready)} "
            f"rk={len(rk_entries)} goals={len(goals)}",
            flush=True,
        )
        if goals:
            print(f"  best {state_text(goals[0])} stock={rg.final_resource_stock(goals[0])}", flush=True)

    goals = rg.best_goals(entries)
    best = goals[0] if goals else None
    if best:
        write_walk(best, phase1_id)
    top_entries = sorted(
        entries,
        key=lambda e: (
            0 if p9.goal(e) else 1,
            p9.stat_deficit(e),
            max(0, 1 - e["yk"]) if e["atk"] >= 27 and e["def"] >= 27 and e["rk"] < 1 else 0,
            redkey_survival_deficit(e) if e["atk"] >= 27 and e["def"] >= 27 and e["rk"] < 1 else 0,
            0 if e["rk"] >= 1 else 1,
            p9.boss_survival_deficit(e),
            rg.resource_group_score(e),
            e.get("_dmg", 0),
            -e["hp"],
        ),
    )[:20]
    return {
        "elapsed": time.time() - t0,
        "phase1_elapsed": phase1_result.get("elapsed"),
        "phase1_start": compact(start),
        "rounds": rows,
        "entry_count": len(entries),
        "goal_count": len(goals),
        "best": compact(best) if best else None,
        "top_goals": [compact(e) for e in goals[:10]],
        "top_entries": [compact(e) for e in top_entries],
        "audit_edges": audit[:60],
        "redkey_ready_audit": audit_redkey_ready(entries, max_iter=max_iter),
    }


def run_dijkstra(
    phase1_expansions: int,
    max_expansions: int,
    entry_limit: int,
    max_targets: int,
    max_iter: int,
    edge_limit: int,
    priority_mode: str,
) -> dict[str, Any]:
    t0 = time.time()
    start, phase1_result = delayed.find_candidate(phase1_expansions)
    phase1_id = start["_id"]
    audit = audit_edges(start, max_targets=max_targets, max_iter=max_iter)
    priority = make_label_priority(priority_mode)

    labels: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    active: dict[int, dict[str, Any]] = {}
    heap: list[tuple[tuple[int, ...], int, int]] = []
    seq = 0
    rows = []

    def rebuild(kept: list[dict[str, Any]]) -> None:
        labels.clear()
        active.clear()
        for ent in kept:
            labels[gw._collected_signature(ent)].append(ent)
            active[ent["_id"]] = ent

    def accept(ent: dict[str, Any]) -> bool:
        nonlocal seq
        sig = gw._collected_signature(ent)
        bucket = labels[sig]
        if any(dominates(old, ent) for old in bucket):
            return False
        removed = [old for old in bucket if dominates(ent, old)]
        if removed:
            remove_ids = {old["_id"] for old in removed}
            bucket[:] = [old for old in bucket if old["_id"] not in remove_ids]
            for rid in remove_ids:
                active.pop(rid, None)
        bucket.append(ent)
        active[ent["_id"]] = ent
        seq += 1
        heapq.heappush(heap, (priority(ent), seq, ent["_id"]))
        return True

    def active_entries() -> list[dict[str, Any]]:
        return list(active.values())

    accept(start)
    expanded = 0
    generated_total = 0
    accepted_total = 1
    goals: list[dict[str, Any]] = []
    while heap and expanded < max_expansions:
        _priority, _seq, ent_id = heapq.heappop(heap)
        ent = active.get(ent_id)
        if ent is None:
            continue
        expanded += 1
        if p9.goal(ent):
            continue
        edges = generate_edges(ent, max_targets=max_targets, max_iter=max_iter, edge_limit=edge_limit)
        generated_total += len(edges)
        accepted_now = 0
        for edge in edges:
            if accept(edge):
                accepted_now += 1
        accepted_total += accepted_now

        if entry_limit > 0 and len(active) > entry_limit:
            kept = trim_entries(active_entries(), entry_limit)
            rebuild(kept)
            heap = [(priority(e), i, e["_id"]) for i, e in enumerate(kept)]
            heapq.heapify(heap)
            seq += len(kept)

        if expanded % 25 == 0 or accepted_now or any(p9.goal(e) for e in edges):
            entries = active_entries()
            goals = rg.best_goals(entries)
            stat_done = [e for e in entries if e["atk"] >= 27 and e["def"] >= 27]
            redkey_ready = [e for e in stat_done if e["rk"] < 1 and e["yk"] >= 1 and redkey_survival_deficit(e) == 0]
            rk_entries = [e for e in entries if e["rk"] >= 1]
            rows.append({
                "round": expanded,
                "sources": 1,
                "new": len(edges),
                "entries": len(entries),
                "goals": len(goals),
                "stat_done": len(stat_done),
                "redkey_ready": len(redkey_ready),
                "rk_entries": len(rk_entries),
                "mt10_entries": len([e for e in entries if "MT10" in e.get("collected", {})]),
                "best_goal": compact(goals[0]) if goals else None,
                "best_redkey_ready": compact(sorted(redkey_ready, key=priority)[0]) if redkey_ready else None,
                "best_rk": compact(sorted(rk_entries, key=priority)[0]) if rk_entries else None,
            })
            print(
                f"expand {expanded}: edges={len(edges)} accepted={accepted_now} active={len(entries)} "
                f"stat27={len(stat_done)} redkeyReady={len(redkey_ready)} rk={len(rk_entries)} goals={len(goals)}",
                flush=True,
            )
            if goals:
                print(f"  best {state_text(goals[0])} stock={rg.final_resource_stock(goals[0])}", flush=True)

    entries = active_entries()
    goals = rg.best_goals(entries)
    best = goals[0] if goals else None
    if best:
        write_walk(best, phase1_id)
    top_entries = sorted(entries, key=priority)[:20]
    return {
        "elapsed": time.time() - t0,
        "mode": "dijkstra",
        "priority": priority_mode,
        "phase1_elapsed": phase1_result.get("elapsed"),
        "phase1_start": compact(start),
        "rounds": rows,
        "entry_count": len(entries),
        "generated_total": generated_total,
        "accepted_total": accepted_total,
        "goal_count": len(goals),
        "best": compact(best) if best else None,
        "top_goals": [compact(e) for e in goals[:10]],
        "top_entries": [compact(e) for e in top_entries],
        "audit_edges": audit[:60],
        "redkey_ready_audit": audit_redkey_ready(entries, max_iter=max_iter),
    }


def write_outputs(data: dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    lines = [
        "# Post-9 Auto Resource Group Pareto",
        "",
        "这个实验把“资源组”当作地图压缩边：目标是一个具体资源坐标，边成本由真实楼层寻路计算，边内容是本次路径实际经过的门、怪、顺路资源。",
        "",
        "## Heuristic Values",
        "",
        "- redGem=260、blueGem=280 不是精确收益，是后9楼排序启发值。",
        "- 粗略含义：一个宝石可能影响后续多场关键战斗，价值约等于它未来可少掉的血；蓝宝石略高，是因为盾后阶段先加防通常能影响更多低攻怪。",
        "- 这个值只用于排序/保留代表，不作为 Pareto 支配条件。",
        "",
        "## Summary",
        "",
        f"- elapsed: {data['elapsed']:.1f}s",
        f"- entry count: {data['entry_count']}",
        f"- goal count: {data['goal_count']}",
        f"- start: {data['phase1_start']}",
    ]
    if data.get("best"):
        b = data["best"]
        lines.append(
            f"- best: HP={b['hp']} ATK={b['atk']} DEF={b['def']} YK={b['yk']} BK={b['bk']} RK={b['rk']} "
            f"dmg={b['dmg']} door={b['yd']}/{b['bd']}/{b['rd']} finalStock={b['final_resource_stock']} "
            f"rgScore={b['resource_group_score']} oldScore={b['old_score']}"
        )
    lines.extend([
        "",
        "## Top Goals",
        "",
        "| # | finalStock | rgScore | oldScore | state | kind | last action |",
        "|---:|---:|---:|---:|---|---|---|",
    ])
    for idx, row in enumerate(data["top_goals"], 1):
        lines.append(
            f"| {idx} | {row['final_resource_stock']} | {row['resource_group_score']} | {row['old_score']} | "
            f"HP={row['hp']} ATK={row['atk']} DEF={row['def']} YK={row['yk']} BK={row['bk']} RK={row['rk']} "
            f"dmg={row['dmg']} door={row['yd']}/{row['bd']}/{row['rd']} | {row['edge_kind']} | {row['last_action']} |"
        )
    lines.extend([
        "",
        "## Top Non-Goal/Frontier Entries",
        "",
        "| # | stat deficit | rk | boss deficit | rgScore | state | kind | last action |",
        "|---:|---:|---:|---:|---:|---|---|",
    ])
    for idx, row in enumerate(data["top_entries"], 1):
        stat_def = max(0, 27 - row["atk"]) + max(0, 27 - row["def"])
        boss_def = 0 if row["rk"] >= 1 and row["atk"] >= 27 and row["def"] >= 27 else "-"
        lines.append(
            f"| {idx} | {stat_def} | {row['rk']} | {boss_def} | {row['resource_group_score']} | "
            f"HP={row['hp']} ATK={row['atk']} DEF={row['def']} YK={row['yk']} BK={row['bk']} RK={row['rk']} "
            f"dmg={row['dmg']} door={row['yd']}/{row['bd']}/{row['rd']} stock={row['final_resource_stock']} | {row['edge_kind']} | {row['last_action']} |"
        )
    lines.extend([
        "",
        "## Rounds",
        "",
        "| round | sources | new | entries | 27/27 | redkey ready | rk | goals | best rk/goal |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ])
    for row in data["rounds"]:
        best = row.get("best_goal") or row.get("best_rk") or row.get("best_redkey_ready")
        best_text = "-"
        if best:
            best_text = (
                f"HP={best['hp']} dmg={best['dmg']} door={best['yd']}/{best['bd']}/{best['rd']} "
                f"stock={best['final_resource_stock']}"
            )
        lines.append(
            f"| {row['round']} | {row['sources']} | {row['new']} | {row['entries']} | "
            f"{row.get('stat_done', 0)} | {row.get('redkey_ready', 0)} | {row.get('rk_entries', 0)} | "
            f"{row['goals']} | {best_text} |"
        )
    lines.extend([
        "",
        "## Redkey Ready Audit",
        "",
        "| # | ready state | redkey edges | best redkey edge |",
        "|---:|---|---:|---|",
    ])
    for idx, row in enumerate(data.get("redkey_ready_audit", []), 1):
        st = row["state"]
        ready_text = (
            f"HP={st['hp']} ATK={st['atk']} DEF={st['def']} YK={st['yk']} BK={st['bk']} "
            f"dmg={st['dmg']} door={st['yd']}/{st['bd']}/{st['rd']} action={st['last_action']}"
        )
        best_text = "-"
        if row["edges"]:
            e = row["edges"][0]
            best_text = (
                f"HP={e['hp']} YK={e['yk']} RK={e['rk']} dmg={e['dmg']} "
                f"door={e['yd']}/{e['bd']}/{e['rd']} action={e['last_action']}"
            )
        debug = (
            f"pending={','.join(row.get('pending', [])) or '-'} "
            f"raw={row.get('raw_count', 0)}/iters={row.get('raw_iters', 0)} "
            f"mt8={';'.join(row.get('mt8_collected', [])[:10])}"
        )
        if row.get("raw_hits"):
            debug += " rawHits=" + json.dumps(row["raw_hits"], ensure_ascii=False)
        lines.append(
            f"| {idx} | {ready_text}<br>{debug} | {row['edge_count']} | {best_text} |"
        )
    lines.extend([
        "",
        "## Auto Edge Audit From Start",
        "",
        "| # | action | kind | seg dmg | seg door | after | auto group |",
        "|---:|---|---|---:|---:|---|---|",
    ])
    for idx, row in enumerate(data["audit_edges"], 1):
        st = row["state"]
        door = "/".join(str(x) for x in row["segment_door"])
        lines.append(
            f"| {idx} | {row['action']} | {row['edge_kind']} | {row['segment_dmg']} | {door} | "
            f"HP={st['hp']} ATK={st['atk']} DEF={st['def']} YK={st['yk']} BK={st['bk']} RK={st['rk']} "
            f"dmg={st['dmg']} door={st['yd']}/{st['bd']}/{st['rd']} | {row['group_text']} |"
        )
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["beam", "dijkstra"], default="beam")
    parser.add_argument("--priority", choices=["stage", "balanced", "score"], default="stage")
    parser.add_argument("--phase1-expansions", type=int, default=300)
    parser.add_argument("--rounds", type=int, default=10)
    parser.add_argument("--max-expansions", type=int, default=240)
    parser.add_argument("--entry-limit", type=int, default=220)
    parser.add_argument("--source-limit", type=int, default=36)
    parser.add_argument("--max-targets", type=int, default=26)
    parser.add_argument("--max-iter", type=int, default=160000)
    parser.add_argument("--edge-limit", type=int, default=10)
    args = parser.parse_args()
    if args.mode == "dijkstra":
        data = run_dijkstra(
            phase1_expansions=args.phase1_expansions,
            max_expansions=args.max_expansions,
            entry_limit=args.entry_limit,
            max_targets=args.max_targets,
            max_iter=args.max_iter,
            edge_limit=args.edge_limit,
            priority_mode=args.priority,
        )
    else:
        data = run(
            phase1_expansions=args.phase1_expansions,
            rounds=args.rounds,
            entry_limit=args.entry_limit,
            source_limit=args.source_limit,
            max_targets=args.max_targets,
            max_iter=args.max_iter,
            edge_limit=args.edge_limit,
        )
    write_outputs(data)
    print(f"wrote {OUT_JSON}")
    print(f"wrote {OUT_MD}")
    if data.get("best"):
        print(f"wrote {OUT_WALK}")
        if os.path.exists(OUT_WALK_DETAIL):
            print(f"wrote {OUT_WALK_DETAIL}")


if __name__ == "__main__":
    main()
