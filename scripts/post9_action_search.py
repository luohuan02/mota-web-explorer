#!/usr/bin/env python3
"""Action-level search after the fixed 9F red+blue-gem prefix.

This is an experiment for the post-9F stage.  The existing solver still owns
the authoritative map mechanics and per-floor Dijkstra/Pareto search; this
script changes only the outer scheduler.  Instead of forcing a fixed
gem/key/potion order, it expands one useful action at a time and keeps
representative states for damage, door cost, key budget, HP, and MT10 partial
progress.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.chdir(ROOT)

import fixed_shield_strategy as fixed
from src.solver import gen_walkthrough as gw
from src.solver.full_search import FLYBACK_ENTRANCES, calc_dmg, search_with_path


OUT_JSON = os.path.join("outputs", "results", "post9_action_search.json")
OUT_MD = os.path.join("outputs", "reports", "post9_action_search.md")
OUT_WALK = os.path.join("outputs", "walkthroughs", "walkthrough_post9_action_best.md")

STATE_KEYS = ("hp", "atk", "def", "yk", "bk", "rk")
LEFT_MT10_DOORS = frozenset([(1, 9), (3, 9)])
RIGHT_MT10_DOORS = frozenset([(9, 9), (11, 9)])

GEM_ACTIONS = [
    ("MT6", "blueGem"),
    ("MT3", "blueGem"),
    ("MT8", "blueGem"),
    ("MT8", "redGem"),
    ("MT1", "blueGem"),
    ("MT1", "redGem"),
    ("MT3", "redGem"),
    ("MT5", "blueGem"),
    ("MT10", "blueGem"),
    ("MT10", "redGem"),
    ("MT7", "redGem"),
    ("MT4", "redGem"),
    ("MT9", "blueGem"),
    ("MT9", "redGem"),
]

RESOURCE_ACTIONS = [
    ("MT4", "blueKey"),
    ("MT7", "yellowKey"),
    ("MT10", "bluePotion"),
    ("MT7", "bluePotion"),
    ("MT8", "redKey"),
    ("MT1", "bluePotion"),
    ("MT1", "redPotion"),
    ("MT1", "yellowKey"),
    ("MT3", "blueKey"),
    ("MT3", "yellowKey"),
    ("MT3", "bluePotion"),
    ("MT3", "redPotion"),
    ("MT4", "yellowKey"),
    ("MT4", "bluePotion"),
    ("MT4", "redPotion"),
    ("MT5", "yellowKey"),
    ("MT5", "redPotion"),
    ("MT6", "yellowKey"),
    ("MT6", "redPotion"),
    ("MT7", "redPotion"),
    ("MT8", "yellowKey"),
    ("MT8", "bluePotion"),
    ("MT8", "redPotion"),
    ("MT9", "yellowKey"),
    ("MT9", "redPotion"),
]

STAT_ACTIONS = [
    ("MT6", "blueGem"),
    ("MT3", "blueGem"),
    ("MT8", "blueGem"),
    ("MT8", "redGem"),
    ("MT1", "blueGem"),
    ("MT1", "redGem"),
    ("MT3", "redGem"),
    ("MT5", "blueGem"),
    ("MT4", "blueKey"),
    ("MT7", "yellowKey"),
    ("MT10", "blueGem"),
    ("MT10", "redGem"),
    ("MT7", "redGem"),
    ("MT4", "redGem"),
    ("MT9", "blueGem"),
    ("MT9", "redGem"),
]

REDKEY_ACTIONS = [
    ("MT10", "bluePotion"),
    ("MT7", "bluePotion"),
    ("MT7", "yellowKey"),
    ("MT8", "yellowKey"),
    ("MT8", "redPotion"),
    ("MT8", "bluePotion"),
    ("MT8", "redKey"),
]

BOSS_PREP_ACTIONS = [
    ("MT1", "bluePotion"),
    ("MT1", "redPotion"),
    ("MT7", "bluePotion"),
    ("MT10", "bluePotion"),
    ("MT3", "bluePotion"),
    ("MT4", "bluePotion"),
    ("MT8", "bluePotion"),
]


def state_record(e):
    return {key: e[key] for key in STATE_KEYS}


def state_text(e):
    st = state_record(e)
    return (
        f"HP={st['hp']} ATK={st['atk']} DEF={st['def']} "
        f"YK={st['yk']} BK={st['bk']} RK={st['rk']} "
        f"dmg={e.get('_dmg', 0)} "
        f"door={e.get('_yd', 0)}/{e.get('_bd', 0)}/{e.get('_rd', 0)}"
    )


def prefix_metrics(prefix_result):
    dmg = yd = bd = rd = 0
    for step in prefix_result["steps"]:
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


def convert_collected(prefix_result):
    return {
        fid: frozenset((item["x"], item["y"]) for item in positions)
        for fid, positions in prefix_result["collected"].items()
    }


def seed_fixed_prefix():
    prefix = fixed.replay_route()
    if not prefix["ok"]:
        raise RuntimeError("fixed 4-9 prefix replay failed")
    dmg, yd, bd, rd = prefix_metrics(prefix)
    st = prefix["final_state"]
    ent = {
        "hp": st["hp"],
        "atk": st["atk"],
        "def": st["def"],
        "yk": st["yk"],
        "bk": st["bk"],
        "rk": st["rk"],
        "collected": convert_collected(prefix),
        "_id": 1,
        "_parent_id": None,
        "_step_info": None,
        "_dmg": dmg,
        "_yd": yd,
        "_bd": bd,
        "_rd": rd,
    }
    gw._entry_store.clear()
    gw._next_id[0] = 1
    gw._entry_store[1] = dict(ent)
    return ent


def item_positions(fid, target):
    return frozenset(
        (b[0], b[1])
        for b in gw.maps[fid]["bl"]
        if b[3] == target
    )


def collected_for(ent, fid):
    got = set(ent.get("collected", {}).get(fid, frozenset()))
    if fid in gw.FLOOR_13_COLLECTED:
        got.update(gw.FLOOR_13_COLLECTED[fid])
    return frozenset(got)


def target_available(ent, fid, target):
    if target == "upFloor":
        return True
    already = collected_for(ent, fid)
    return bool(item_positions(fid, target) - already)


def has_target(ent, fid, target):
    return bool(item_positions(fid, target) & collected_for(ent, fid))


def boss_event_damage(atk, def_):
    return (
        2 * calc_dmg("skeletonSoldier", atk, def_) +
        6 * calc_dmg("skeleton", atk, def_)
    )


def boss_required_damage(atk, def_):
    return boss_event_damage(atk, def_) + calc_dmg("skeletonCaptain", atk, def_)


def boss_survival_deficit(ent):
    if ent["atk"] < 27 or ent["def"] < 27 or ent["rk"] < 1:
        return 10**9
    return max(0, boss_required_damage(ent["atk"], ent["def"]) + 1 - ent["hp"])


def boss_feasible_rough(ent):
    return boss_survival_deficit(ent) == 0


def redkey_survival_deficit(ent):
    if ent["atk"] < 27 or ent["def"] < 27 or ent["rk"] >= 1:
        return 10**9
    # Rough lower bound for the MT8 red-key route.  The exact floor search still
    # decides reachability; this is only a source/trim checkpoint so low-HP
    # 27/27 states do not crowd out red-key-capable ones.
    return max(0, 260 - ent["hp"])


def redkey_feasible_rough(ent):
    return redkey_survival_deficit(ent) == 0


def phase_survival_deficit(ent):
    if ent["rk"] >= 1:
        return boss_survival_deficit(ent)
    if ent["atk"] >= 27 and ent["def"] >= 27:
        return redkey_survival_deficit(ent)
    return 0


def cost_key(ent):
    return (
        ent.get("_dmg", 0),
        ent.get("_yd", 0),
        ent.get("_bd", 0),
        ent.get("_rd", 0),
        -ent["yk"],
        -ent["bk"],
        -ent["rk"],
    )


def floor_action(ent, fid, target, flyback=None, max_iter=250000):
    if target != "upFloor" and not target_available(ent, fid, target):
        return []
    is_fb = (fid in ent.get("collected", {})) if flyback is None else flyback
    extra_removed = None
    if fid in {"MT3", "MT10"} and target == "blueGem":
        extra_removed = item_positions(fid, "redGem") - collected_for(ent, fid)
    elif fid in {"MT3", "MT10"} and target == "redGem":
        extra_removed = item_positions(fid, "blueGem") - collected_for(ent, fid)
    pareto, _, _ = gw.search_floor(
        gw.maps, fid, ent, [target],
        max_iter=max_iter, flyback=is_fb, extra_removed=extra_removed,
    )
    if not pareto:
        return []

    already = collected_for(ent, fid)
    needed = item_positions(fid, target) - already
    results = []
    for hp, yk, bk, rk, atk, def_, _hs, vis, dc in pareto:
        if target != "upFloor" and needed and not (vis & needed):
            continue
        if fid in {"MT3", "MT10"} and target == "blueGem" and atk > ent["atk"]:
            continue
        if fid in {"MT3", "MT10"} and target == "redGem" and def_ > ent["def"]:
            continue
        nc = dict(ent.get("collected", {}))
        nc[fid] = already | vis
        r = gw._make_result(
            hp, yk, bk, rk, atk, def_, nc, ent["_id"],
            (fid, [target], is_fb), dmg_cost=dc,
        )
        r["_source"] = f"{fid}:{target}"
        gw._entry_store[r["_id"]]["_source"] = r["_source"]
        results.append(r)
    return results


def ensure_mt10(ent):
    if "MT10" in ent.get("collected", {}):
        return [ent]
    # The only legal first entry to MT10 is the real 9F up stair.
    return floor_action(ent, "MT9", "upFloor", flyback=True, max_iter=80000)


def mt10_action(ent, target):
    results = []
    for base in ensure_mt10(ent):
        results.extend(floor_action(base, "MT10", target, flyback=("MT10" in base.get("collected", {}))))
    return results


def boss_action(ent):
    if ent["atk"] < 27 or ent["def"] < 27 or ent["rk"] < 1:
        return []
    results = []
    red_doors = item_positions("MT10", "redDoor")
    for base in ensure_mt10(ent):
        is_fb = "MT10" in base.get("collected", {})
        pareto, _, _ = gw.search_floor(gw.maps, "MT10", base, ["redDoor"], flyback=is_fb)
        if not pareto:
            continue
        already = collected_for(base, "MT10")
        for hp, yk, bk, rk, atk, def_, _hs, vis, dc in pareto:
            if not (vis & red_doors):
                continue
            extra = boss_event_damage(atk, def_) + calc_dmg("skeletonCaptain", atk, def_)
            hp_after = hp - extra
            if hp_after <= 0:
                continue
            nc = dict(base.get("collected", {}))
            nc["MT10"] = already | vis
            r = gw._make_result(
                hp_after, yk, bk, rk, atk, def_, nc, base["_id"],
                ("MT10", ["redDoor"], is_fb), dmg_cost=dc + extra,
            )
            r["_source"] = "MT10:boss"
            gw._entry_store[r["_id"]]["_source"] = r["_source"]
            results.append(r)
    return results


def boss_probe(ent):
    if not ent:
        return None
    out = {
        "source": compact_state(ent),
        "base_count": 0,
        "redDoor_pareto": 0,
        "samples": [],
    }
    red_doors = item_positions("MT10", "redDoor")
    bases = ensure_mt10(ent)
    out["base_count"] = len(bases)
    for base in bases[:4]:
        is_fb = "MT10" in base.get("collected", {})
        pareto, _, _ = gw.search_floor(gw.maps, "MT10", base, ["redDoor"], flyback=is_fb)
        out["redDoor_pareto"] += len(pareto or [])
        for hp, yk, bk, rk, atk, def_, _hs, vis, dc in (pareto or [])[:5]:
            extra = boss_event_damage(atk, def_) + calc_dmg("skeletonCaptain", atk, def_)
            out["samples"].append({
                "hp_after_redDoor": hp,
                "yk": yk,
                "bk": bk,
                "rk": rk,
                "atk": atk,
                "def": def_,
                "dc": dc,
                "has_redDoor": bool(vis & red_doors),
                "boss_extra": extra,
                "hp_after_boss": hp - extra,
            })
    return out


def mt10_stage(ent):
    mt10 = collected_for(ent, "MT10")
    return (
        int(bool(item_positions("MT10", "blueGem") & mt10)),
        int(bool(item_positions("MT10", "redGem") & mt10)),
        int(bool(item_positions("MT10", "bluePotion") & mt10)),
        int(bool(item_positions("MT10", "redDoor") & mt10)),
    )


def goal(ent):
    return (
        ent["hp"] > 0 and ent["atk"] >= 27 and ent["def"] >= 27 and
        bool(item_positions("MT10", "redDoor") & collected_for(ent, "MT10"))
    )


def stat_deficit(ent):
    return max(0, 27 - ent["atk"]) + max(0, 27 - ent["def"])


def needs_mt10_for_stats(ent):
    if stat_deficit(ent) <= 0:
        return False
    if ent["def"] < 27 and target_available(ent, "MT10", "blueGem"):
        return True
    if ent["atk"] < 27 and target_available(ent, "MT10", "redGem"):
        return True
    return False


def desired_yk(ent):
    """Small demand estimate for direct key actions.

    This is not a floor-specific strategy.  It asks how many yellow keys the
    current stage can plausibly consume soon: MT10 stat gems before 27/27,
    red-key access after 27/27, or final refills after the red key.
    """
    if ent["rk"] >= 1:
        return 1 if boss_survival_deficit(ent) > 0 else 0
    if ent["atk"] >= 27 and ent["def"] >= 27:
        return 2
    if needs_mt10_for_stats(ent):
        need = 1 if "MT10" not in ent.get("collected", {}) else 0
        opened = collected_for(ent, "MT10")
        if ent["def"] < 27 and target_available(ent, "MT10", "blueGem"):
            need += 0 if (1, 9) in opened else 1
        if ent["atk"] < 27 and target_available(ent, "MT10", "redGem"):
            need += sum(1 for pos in RIGHT_MT10_DOORS if pos not in opened)
        return min(6, need)
    return 0


def hp_deficit_for_resources(ent):
    if ent["rk"] >= 1:
        return boss_survival_deficit(ent)
    if ent["atk"] >= 27 and ent["def"] >= 27:
        return redkey_survival_deficit(ent)
    return 0


def action_allowed(ent, fid, target):
    if target == "blueGem" and ent["def"] >= 27:
        return False
    if target == "redGem" and ent["atk"] >= 27:
        return False
    if fid == "MT5" and target == "blueGem" and ent["atk"] < 26:
        return False
    if fid == "MT10" and target in {"blueGem", "redGem", "bluePotion"}:
        if "MT10" not in ent.get("collected", {}):
            if ent["bk"] < 1 or ent["yk"] < 1:
                return False
        if target == "blueGem" and not has_target(ent, "MT10", "blueGem"):
            # Entering plus the blue-gem route only needs MT9's entry door and
            # MT10 x1y9.  The x3y9 left door belongs to the later red-gem route.
            enter_yk = 0 if "MT10" in ent.get("collected", {}) else 1
            opened = collected_for(ent, "MT10")
            need_left = 0 if (1, 9) in opened else 1
            if ent["yk"] < enter_yk + need_left:
                return False
        if target in {"redGem", "bluePotion"}:
            opened = collected_for(ent, "MT10")
            need_right = sum(1 for pos in RIGHT_MT10_DOORS if pos not in opened)
            if ent["yk"] < need_right:
                return False
    if target in {"yellowKey", "blueKey", "redPotion", "bluePotion"}:
        # Resource actions are useful when they unlock MT10/red-key/boss or when
        # HP is still below the event damage budget.  Free incidental pickups are
        # still collected by other searches when they are on the route.
        if ent["atk"] < 25 or ent["def"] < 24:
            return False
        if target == "yellowKey":
            if ent["atk"] < 27 or ent["def"] < 27:
                mt10_is_next_bottleneck = (
                    needs_mt10_for_stats(ent) and
                    ("MT10" in ent.get("collected", {}) or (ent["bk"] > 0 and stat_deficit(ent) <= 2))
                )
                if not mt10_is_next_bottleneck:
                    return False
            return ent["yk"] < desired_yk(ent)
        if target == "blueKey":
            return (
                ent["bk"] < 1 and "MT10" not in ent.get("collected", {}) and
                needs_mt10_for_stats(ent) and stat_deficit(ent) <= 2
            )
        if target in {"redPotion", "bluePotion"}:
            if ent["atk"] < 27 or ent["def"] < 27:
                return False
            if fid == "MT1" and ent["rk"] < 1:
                return False
            return hp_deficit_for_resources(ent) > 0
    if target == "redKey":
        return ent["atk"] >= 27 and ent["def"] >= 27 and ent["rk"] < 1
    return True


def apply_action(ent, fid, target):
    if not action_allowed(ent, fid, target):
        return []
    if fid == "MT10":
        return mt10_action(ent, target)
    return floor_action(ent, fid, target, flyback=(fid in ent.get("collected", {})))


def source_limit_for(fid, target, base_limit):
    critical = {
        ("MT7", "yellowKey"),
        ("MT10", "redGem"),
        ("MT10", "bluePotion"),
        ("MT7", "bluePotion"),
        ("MT8", "redKey"),
        ("MT1", "bluePotion"),
        ("MT1", "redPotion"),
    }
    if (fid, target) in critical:
        return base_limit * 3
    if target in {"redGem", "blueGem"}:
        return base_limit * 2
    return base_limit


def action_score_key(ent, fid, target):
    dmg = ent.get("_dmg", 0)
    doors = (ent.get("_yd", 0), ent.get("_bd", 0), ent.get("_rd", 0))
    if target in {"redGem", "blueGem"}:
        return (dmg, *doors, -(ent["atk"] + ent["def"]), -ent["yk"], -ent["bk"], -ent["hp"])
    if target in {"yellowKey", "blueKey"}:
        return (dmg, *doors, -ent["yk"], -ent["bk"], -ent["hp"])
    if target in {"redPotion", "bluePotion"}:
        return (
            0 if (ent["rk"] >= 1 or (ent["atk"] >= 27 and ent["def"] >= 27)) else 1,
            phase_survival_deficit(ent),
            dmg,
            *doors,
            -ent["yk"],
            -ent["bk"],
        )
    if target == "redKey":
        return (redkey_survival_deficit(ent), dmg, *doors, -ent["yk"], -ent["bk"])
    return (dmg, *doors, -ent["hp"])


def select_sources(entries, fid, target, limit):
    src = [
        e for e in entries
        if action_allowed(e, fid, target) and target_available(e, fid, target)
    ]
    if not src:
        return []
    selected = []
    seen = set()
    selectors = [
        lambda e: action_score_key(e, fid, target),
        lambda e: (0 if (e["rk"] >= 1 or e["atk"] >= 27 and e["def"] >= 27) else 1, phase_survival_deficit(e), *cost_key(e)),
        lambda e: (redkey_survival_deficit(e), *cost_key(e), -e["hp"]),
        lambda e: (boss_survival_deficit(e), *cost_key(e), -e["hp"]),
        lambda e: (e.get("_yd", 0), e.get("_bd", 0), e.get("_rd", 0), e.get("_dmg", 0), -e["hp"]),
        lambda e: (-e["yk"], -e["bk"], e.get("_dmg", 0), e.get("_yd", 0), -e["hp"]),
    ]
    if target in {"redPotion", "bluePotion"}:
        selectors.extend([
            lambda e: (
                0 if (e["atk"] >= 27 and e["def"] >= 27) else 1,
                hp_deficit_for_resources(e), e.get("_dmg", 0), e.get("_yd", 0), -e["yk"], -e["bk"], -e["hp"],
            ),
            lambda e: (
                phase_survival_deficit(e), e.get("_dmg", 0), e.get("_yd", 0), -e["yk"], -e["hp"],
            ),
        ])
    if target in {"yellowKey", "blueKey"}:
        selectors.extend([
            lambda e: (stat_deficit(e), e.get("_dmg", 0), e.get("_yd", 0), e.get("_bd", 0), -e["hp"]),
            lambda e: (-(e["atk"] + e["def"]), e.get("_dmg", 0), e.get("_yd", 0), -e["yk"], -e["bk"], -e["hp"]),
            lambda e: (max(0, desired_yk(e) - e["yk"]), e.get("_dmg", 0), e.get("_yd", 0), -e["hp"]),
        ])
    if target == "redGem":
        selectors.extend([
            lambda e: (-e["def"], e.get("_dmg", 0), e.get("_yd", 0), -e["yk"], -e["hp"]),
            lambda e: (0 if e["def"] >= 27 else 1, e.get("_dmg", 0), e.get("_yd", 0), -e["yk"], -e["hp"]),
        ])
    if target == "blueGem":
        selectors.extend([
            lambda e: (-e["atk"], e.get("_dmg", 0), e.get("_yd", 0), -e["yk"], -e["hp"]),
            lambda e: (0 if e["atk"] >= 26 else 1, e.get("_dmg", 0), e.get("_yd", 0), -e["yk"], -e["hp"]),
        ])
    if target == "redKey":
        selectors.extend([
            lambda e: (0 if e["yk"] >= 1 else 1, redkey_survival_deficit(e), *cost_key(e), -e["hp"]),
            lambda e: (0 if e["yk"] >= 2 else 1, redkey_survival_deficit(e), *cost_key(e), -e["hp"]),
            lambda e: (redkey_survival_deficit(e), *cost_key(e), -e["hp"]),
            lambda e: (redkey_survival_deficit(e), -e["yk"], -e["bk"], e.get("_dmg", 0), -e["hp"]),
        ])
    per_selector = max(2, limit // len(selectors))
    for selector in selectors:
        for e in sorted(src, key=selector)[:per_selector]:
            if e["_id"] in seen:
                continue
            seen.add(e["_id"])
            selected.append(e)
            if len(selected) >= limit:
                return selected
    return selected[:limit]


def filter_entries(entries):
    """Keep the full post-9F Pareto set before stage trimming.

    gen_walkthrough._filter_entries_tracked intentionally samples a small
    number of representatives from the Pareto frontier.  That is fast for the
    coarse staged solver, but in this action scheduler it can drop a route that
    has slightly worse current HP/dmg while preserving a key that later converts
    into the boss refill.  Here we keep every non-dominated state per collected
    signature, then trim_entries applies stage-aware quotas.
    """
    groups = {}
    for e in entries:
        groups.setdefault(gw._collected_signature(e), []).append(e)

    def tuple_for(e):
        return (
            e.get("_dmg", 0),
            e.get("_yd", 0),
            e.get("_bd", 0),
            e.get("_rd", 0),
            e["hp"], e["atk"], e["def"], e["yk"], e["bk"], e["rk"],
            e,
        )

    def dominates(a, b):
        ad, ayd, abd, ard, ahp, aatk, adef, ayk, abk, ark = a[:10]
        bdmg, byd, bbd, brd, bhp, batk, bdef, byk, bbk, brk = b[:10]
        if not (
            ad <= bdmg and ayd <= byd and abd <= bbd and ard <= brd and
            aatk >= batk and adef >= bdef and
            ayk >= byk and abk >= bbk and ark >= brk
        ):
            return False
        core_strict = (
            ad < bdmg or ayd < byd or abd < bbd or ard < brd or
            aatk > batk or adef > bdef or
            ayk > byk or abk > bbk or ark > brk
        )
        same_core = (
            ad == bdmg and ayd == byd and abd == bbd and ard == brd and
            aatk == batk and adef == bdef and
            ayk == byk and abk == bbk and ark == brk
        )
        return core_strict or (same_core and ahp >= bhp)

    filtered = []
    for group in groups.values():
        local = []
        for item in sorted((tuple_for(e) for e in group), key=lambda p: (p[0], p[1], p[2], p[3], -p[4])):
            if any(dominates(p, item) for p in local):
                continue
            local = [p for p in local if not dominates(item, p)]
            local.append(item)
        filtered.extend(item[-1] for item in local)

    existing = {e.get("_id") for e in filtered}
    for e in entries:
        if goal(e) and e.get("_id") not in existing:
            filtered.append(e)
            existing.add(e.get("_id"))
    return filtered


def trim_entries(entries, limit):
    filtered = filter_entries(entries)
    if len(filtered) <= limit:
        return filtered

    chosen = []
    seen = set()

    def add(items, quota):
        added = 0
        for e in items:
            if e["_id"] in seen:
                continue
            seen.add(e["_id"])
            chosen.append(e)
            added += 1
            if len(chosen) >= limit or added >= quota:
                return

    def add_bucketed(items, key_fn, selectors, quota, per_selector=1):
        groups = {}
        for e in items:
            groups.setdefault(key_fn(e), []).append(e)
        added = 0
        for bucket in groups.values():
            for selector in selectors:
                picked = 0
                for e in sorted(bucket, key=selector):
                    if e["_id"] in seen:
                        continue
                    seen.add(e["_id"])
                    chosen.append(e)
                    added += 1
                    picked += 1
                    if len(chosen) >= limit or added >= quota or picked >= per_selector:
                        break
                if len(chosen) >= limit or added >= quota:
                    return

    add([e for e in filtered if goal(e)], limit)

    pre_stat = [
        e for e in filtered
        if e["rk"] < 1 and not (e["atk"] >= 27 and e["def"] >= 27)
    ]
    add_bucketed(
        pre_stat,
        lambda e: (
            e["atk"], e["def"], e["yk"], e["bk"],
            e.get("_yd", 0), e.get("_bd", 0), mt10_stage(e),
        ),
        [
            lambda e: (*cost_key(e), -e["hp"]),
            lambda e: (phase_survival_deficit(e), *cost_key(e), -e["hp"]),
            lambda e: (-e["yk"], -e["bk"], e.get("_dmg", 0), e.get("_yd", 0), -e["hp"]),
        ],
        220,
    )

    stat_pre_rk = [
        e for e in filtered
        if e["rk"] < 1 and e["atk"] >= 27 and e["def"] >= 27
    ]
    add_bucketed(
        stat_pre_rk,
        lambda e: (
            e["yk"], e["bk"], e.get("_yd", 0), e.get("_bd", 0), mt10_stage(e),
        ),
        [
            lambda e: (*cost_key(e), -e["hp"]),
            lambda e: (redkey_survival_deficit(e), *cost_key(e), -e["hp"]),
            lambda e: (redkey_survival_deficit(e), -e["yk"], e.get("_dmg", 0), -e["hp"]),
        ],
        260,
    )

    post_rk = [
        e for e in filtered
        if e["rk"] >= 1 and e["atk"] >= 27 and e["def"] >= 27
    ]
    add_bucketed(
        post_rk,
        lambda e: (
            e["yk"], e["bk"], e.get("_yd", 0), e.get("_bd", 0), mt10_stage(e),
        ),
        [
            lambda e: (*cost_key(e), -e["hp"]),
            lambda e: (boss_survival_deficit(e), *cost_key(e), -e["hp"]),
            lambda e: (-e["yk"], e.get("_dmg", 0), e.get("_yd", 0), -e["hp"]),
        ],
        260,
    )

    add(sorted(
        [e for e in filtered if redkey_feasible_rough(e)],
        key=lambda e: (*cost_key(e), -e["hp"]),
    ), 70)
    add(sorted(
        [e for e in filtered if e["atk"] >= 27 and e["def"] >= 27 and e["rk"] < 1],
        key=lambda e: (redkey_survival_deficit(e), *cost_key(e), -e["hp"]),
    ), 55)
    add(sorted(
        [e for e in filtered if e["atk"] >= 27 and e["def"] >= 27 and e["rk"] < 1],
        key=lambda e: (redkey_survival_deficit(e), -e["yk"], e.get("_dmg", 0), e.get("_yd", 0), -e["hp"]),
    ), 45)
    add(sorted(
        [e for e in filtered if e["atk"] >= 27 and e["def"] >= 27 and e["rk"] < 1],
        key=lambda e: (redkey_survival_deficit(e), *cost_key(e), -e["hp"]),
    ), 45)
    add(sorted(
        [e for e in filtered if e["atk"] >= 27 and e["def"] >= 27 and e["rk"] < 1 and e["yk"] >= 1],
        key=lambda e: (redkey_survival_deficit(e), *cost_key(e), -e["hp"]),
    ), 45)
    add(sorted(
        [e for e in filtered if e["atk"] >= 27 and e["def"] >= 27 and e["rk"] < 1 and e["yk"] >= 2],
        key=lambda e: (redkey_survival_deficit(e), *cost_key(e), -e["hp"]),
    ), 45)
    add(sorted(
        [e for e in filtered if boss_feasible_rough(e)],
        key=lambda e: (*cost_key(e), -e["hp"]),
    ), 70)
    add(sorted(
        [e for e in filtered if e["rk"] >= 1 and e["atk"] >= 27 and e["def"] >= 27],
        key=lambda e: (boss_survival_deficit(e), *cost_key(e), -e["hp"]),
    ), 55)
    add(sorted(
        [e for e in filtered if e["rk"] >= 1 and e["atk"] >= 27 and e["def"] >= 27],
        key=lambda e: (boss_survival_deficit(e), -e["yk"], e.get("_dmg", 0), e.get("_yd", 0), -e["hp"]),
    ), 45)
    add(sorted(
        [e for e in filtered if e["rk"] >= 1 and e["atk"] >= 27 and e["def"] >= 27],
        key=lambda e: (boss_survival_deficit(e), *cost_key(e), -e["hp"]),
    ), 45)
    add(sorted(
        [e for e in filtered if e["rk"] >= 1 and e["atk"] >= 27 and e["def"] >= 27 and e["yk"] >= 1],
        key=lambda e: (boss_survival_deficit(e), *cost_key(e), -e["hp"]),
    ), 45)
    add(sorted(
        [e for e in filtered if e["rk"] >= 1 and e["atk"] >= 27 and e["def"] >= 27 and e["yk"] >= 2],
        key=lambda e: (boss_survival_deficit(e), *cost_key(e), -e["hp"]),
    ), 45)
    add(sorted(filtered, key=lambda e: (e.get("_dmg", 0), e.get("_yd", 0), e.get("_bd", 0), e.get("_rd", 0), -e["hp"])), 70)
    add(sorted(filtered, key=lambda e: (e.get("_yd", 0), e.get("_bd", 0), e.get("_rd", 0), e.get("_dmg", 0), -e["yk"], -e["bk"])), 55)
    add(sorted(filtered, key=lambda e: (-e["yk"], -e["bk"], e.get("_dmg", 0), e.get("_yd", 0), -e["hp"])), 55)
    add(sorted(filtered, key=lambda e: (-(e["atk"] + e["def"]), e.get("_dmg", 0), e.get("_yd", 0), -e["yk"])), 45)
    add(sorted([e for e in filtered if "MT10" in e.get("collected", {})], key=lambda e: (mt10_stage(e), e.get("_dmg", 0), e.get("_yd", 0), -e["yk"], -e["hp"])), 55)
    add(sorted([e for e in filtered if e["rk"] >= 1], key=lambda e: (e.get("_dmg", 0), e.get("_yd", 0), -e["hp"])), 40)

    # Keep exact resource/stat/door buckets.  This is the key guard against
    # dropping a low-door route just because another branch has more current HP.
    bucketed = {}
    for e in filtered:
        key = (
            e["atk"], e["def"], e["yk"], e["bk"], e["rk"],
            e.get("_yd", 0), e.get("_bd", 0), e.get("_rd", 0),
            mt10_stage(e),
        )
        bucketed.setdefault(key, []).append(e)
    for bucket in bucketed.values():
        add(sorted(bucket, key=lambda e: (e.get("_dmg", 0), -e["hp"])), 1)
        if len(chosen) >= limit:
            break
    return chosen[:limit]


def best_goals(entries):
    goals = [e for e in entries if goal(e)]
    return sorted(goals, key=lambda e: (e.get("_dmg", 0), e.get("_yd", 0), e.get("_bd", 0), e.get("_rd", 0), -e["hp"]))


def compact_state(e):
    if not e:
        return None
    return state_record(e) | {
        "dmg": e.get("_dmg", 0),
        "yd": e.get("_yd", 0),
        "bd": e.get("_bd", 0),
        "rd": e.get("_rd", 0),
        "mt10_stage": mt10_stage(e),
    }


def diagnostics(entries):
    stat27 = [e for e in entries if e["atk"] >= 27 and e["def"] >= 27]
    redkey = [e for e in entries if e["rk"] >= 1]
    mt10_any = [e for e in entries if "MT10" in e.get("collected", {})]
    mt10_left = [
        e for e in entries
        if LEFT_MT10_DOORS <= collected_for(e, "MT10")
    ]
    mt10_right = [
        e for e in entries
        if RIGHT_MT10_DOORS <= collected_for(e, "MT10")
    ]
    high = sorted(
        entries,
        key=lambda e: (-(e["atk"] + e["def"]), e.get("_dmg", 0), e.get("_yd", 0), -e["hp"]),
    )
    return {
        "stat27": len(stat27),
        "redkey": len(redkey),
        "mt10_any": len(mt10_any),
        "mt10_left": len(mt10_left),
        "mt10_right": len(mt10_right),
        "best_high_stat": compact_state(high[0] if high else None),
        "best_stat27": compact_state(sorted(
            stat27,
            key=lambda e: (e.get("_dmg", 0), e.get("_yd", 0), e.get("_bd", 0), -e["yk"], -e["hp"]),
        )[0] if stat27 else None),
        "best_redkey_ready": compact_state(sorted(
            [e for e in entries if redkey_feasible_rough(e)],
            key=lambda e: (*cost_key(e), -e["hp"]),
        )[0] if any(redkey_feasible_rough(e) for e in entries) else None),
        "best_redkey_ready_hp": compact_state(sorted(
            [e for e in entries if redkey_feasible_rough(e)],
            key=lambda e: (-e["hp"], *cost_key(e)),
        )[0] if any(redkey_feasible_rough(e) for e in entries) else None),
        "best_redkey": compact_state(sorted(
            redkey,
            key=lambda e: (e.get("_dmg", 0), e.get("_yd", 0), e.get("_bd", 0), -e["hp"]),
        )[0] if redkey else None),
        "best_redkey_hp": compact_state(sorted(
            redkey,
            key=lambda e: (-e["hp"], e.get("_dmg", 0), e.get("_yd", 0), e.get("_bd", 0)),
        )[0] if redkey else None),
        "best_redkey_feasible": compact_state(sorted(
            [e for e in redkey if boss_feasible_rough(e)],
            key=lambda e: (*cost_key(e), -e["hp"]),
        )[0] if any(boss_feasible_rough(e) for e in redkey) else None),
        "best_redkey_deficit": compact_state(sorted(
            redkey,
            key=lambda e: (boss_survival_deficit(e), *cost_key(e), -e["hp"]),
        )[0] if redkey else None),
    }


def action_summary(ent):
    si = ent.get("_step_info")
    if not si:
        return "start"
    fid, targets, flyback = si
    return f"{fid} {'+'.join(targets)} flyback={flyback}"


def trace_chain(best):
    return gw.trace_chain(best)


def write_walk(best):
    chain = trace_chain(best)
    lines = [
        "# Post-9F Action Search Best Walk",
        "",
        f"> final: {state_text(best)}",
        "",
    ]
    for idx, ent in enumerate(chain):
        if idx == 0:
            lines.append(f"## 0. fixed prefix")
            lines.append("")
            lines.append(f"- {state_text(ent)}")
            lines.append("")
            continue
        prev = chain[idx - 1]
        lines.append(f"## {idx}. {action_summary(ent)}")
        lines.append("")
        lines.append(f"- {state_text(ent)}")
        lines.append(
            f"- segment dmg={ent.get('_dmg', 0) - prev.get('_dmg', 0)} "
            f"door delta={ent.get('_yd', 0) - prev.get('_yd', 0)}/"
            f"{ent.get('_bd', 0) - prev.get('_bd', 0)}/"
            f"{ent.get('_rd', 0) - prev.get('_rd', 0)}"
        )
        lines.append("")
    os.makedirs(os.path.dirname(OUT_WALK), exist_ok=True)
    with open(OUT_WALK, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")


def stat_goal(ent):
    return ent["atk"] >= 27 and ent["def"] >= 27


def redkey_goal(ent):
    return stat_goal(ent) and ent["rk"] >= 1


def keep_phase_goals(entries, pred, limit):
    goals = [e for e in entries if pred(e)]
    if not goals:
        return trim_entries(entries, limit)
    return trim_entries(goals, limit)


def stage_round(
    entries,
    action_specs,
    entry_limit,
    source_limit,
    include_boss=False,
):
    new_results = []
    action_counts = []
    for fid, target in action_specs:
        sources = select_sources(entries, fid, target, source_limit_for(fid, target, source_limit))
        if not sources:
            continue
        before = len(new_results)
        for ent in sources:
            new_results.extend(apply_action(ent, fid, target))
        gained = len(new_results) - before
        if gained:
            action_counts.append((f"{fid}:{target}", len(sources), gained))

    if include_boss:
        boss_pool = [
            e for e in entries
            if e["rk"] >= 1 and e["atk"] >= 27 and e["def"] >= 27
        ]
        boss_sources = []
        seen = set()
        selectors = [
            lambda e: (0 if boss_feasible_rough(e) else 1, *cost_key(e), -e["hp"]),
            lambda e: (boss_survival_deficit(e), *cost_key(e), -e["hp"]),
            lambda e: (boss_survival_deficit(e), *cost_key(e), -e["hp"]),
            lambda e: (-e["yk"], e.get("_dmg", 0), e.get("_yd", 0), -e["hp"]),
        ]
        for selector in selectors:
            for e in sorted(boss_pool, key=selector)[:max(4, source_limit // 2)]:
                if e["_id"] in seen:
                    continue
                seen.add(e["_id"])
                boss_sources.append(e)
        before = len(new_results)
        for ent in boss_sources:
            new_results.extend(boss_action(ent))
        gained = len(new_results) - before
        if gained:
            action_counts.append(("MT10:boss", len(boss_sources), gained))

    if not new_results:
        return entries, action_counts, 0
    merged = trim_entries(entries + new_results, entry_limit)
    return merged, action_counts, len(new_results)


def run_stage(name, entries, action_specs, pred, rounds, entry_limit, source_limit, include_boss=False):
    rows = []
    for round_no in range(1, rounds + 1):
        entries, action_counts, new_count = stage_round(
            entries, action_specs, entry_limit, source_limit, include_boss=include_boss
        )
        goals = [e for e in entries if pred(e)]
        row = {
            "stage": name,
            "round": round_no,
            "entries": len(entries),
            "new": new_count,
            "goals": len(goals),
            "diagnostics": diagnostics(entries),
            "best_goal": state_record(best_goals(entries)[0]) | {
                "dmg": best_goals(entries)[0].get("_dmg", 0),
                "yd": best_goals(entries)[0].get("_yd", 0),
                "bd": best_goals(entries)[0].get("_bd", 0),
                "rd": best_goals(entries)[0].get("_rd", 0),
            } if best_goals(entries) else None,
            "actions": action_counts[:12],
        }
        rows.append(row)
        print(
            f"{name} round {round_no}: entries={len(entries)} new={new_count} "
            f"stage_goals={len(goals)} final_goals={len(best_goals(entries))} "
            f"stat27={row['diagnostics']['stat27']} rk={row['diagnostics']['redkey']}",
            flush=True,
        )
    return keep_phase_goals(entries, pred, entry_limit), rows


def run_staged(rounds=20, entry_limit=360, source_limit=28):
    start = seed_fixed_prefix()
    t0 = time.time()
    rows = []

    stat_rounds = max(6, rounds)
    redkey_rounds = max(4, rounds // 2)
    boss_rounds = max(4, rounds // 2)

    stat_entries, r = run_stage(
        "stat27", [start], STAT_ACTIONS, stat_goal,
        stat_rounds, entry_limit, source_limit,
    )
    rows.extend(r)
    redkey_entries, r = run_stage(
        "redkey", stat_entries, REDKEY_ACTIONS, redkey_goal,
        redkey_rounds, entry_limit, source_limit,
    )
    rows.extend(r)
    final_entries, r = run_stage(
        "boss", redkey_entries, BOSS_PREP_ACTIONS, goal,
        boss_rounds, entry_limit, source_limit, include_boss=True,
    )
    rows.extend(r)

    goals = best_goals(final_entries)
    elapsed = time.time() - t0
    data = {
        "elapsed": elapsed,
        "rounds": rows,
        "entry_count": len(final_entries),
        "goal_count": len(goals),
        "best": None,
        "top_goals": [],
        "boss_probe": None,
    }
    if not goals:
        redkey = [e for e in final_entries if e["rk"] >= 1 and e["atk"] >= 27 and e["def"] >= 27]
        probe_source = sorted(
            redkey,
            key=lambda e: (boss_survival_deficit(e), *cost_key(e), -e["hp"]),
        )[0] if redkey else None
        data["boss_probe"] = boss_probe(probe_source) if probe_source else None
    if goals:
        best = goals[0]
        data["best"] = state_record(best) | {
            "dmg": best.get("_dmg", 0),
            "yd": best.get("_yd", 0),
            "bd": best.get("_bd", 0),
            "rd": best.get("_rd", 0),
        }
        data["top_goals"] = [
            state_record(e) | {
                "dmg": e.get("_dmg", 0),
                "yd": e.get("_yd", 0),
                "bd": e.get("_bd", 0),
                "rd": e.get("_rd", 0),
                "mt10_stage": mt10_stage(e),
            }
            for e in goals[:10]
        ]
        write_walk(best)
    write_outputs(data)
    return data


def run(rounds=20, entry_limit=360, source_limit=28):
    start = seed_fixed_prefix()
    entries = [start]
    rows = []
    t0 = time.time()
    action_specs = GEM_ACTIONS + RESOURCE_ACTIONS

    for round_no in range(1, rounds + 1):
        new_results = []
        action_counts = []

        for fid, target in action_specs:
            sources = select_sources(entries, fid, target, source_limit_for(fid, target, source_limit))
            if not sources:
                continue
            before = len(new_results)
            for ent in sources:
                new_results.extend(apply_action(ent, fid, target))
            gained = len(new_results) - before
            if gained:
                action_counts.append((f"{fid}:{target}", len(sources), gained))

        boss_pool = [
            e for e in entries
            if e["rk"] >= 1 and e["atk"] >= 27 and e["def"] >= 27
        ]
        boss_sources = []
        seen_boss = set()

        def add_boss_sources(items):
            for e in items:
                if e["_id"] in seen_boss:
                    continue
                seen_boss.add(e["_id"])
                boss_sources.append(e)
                if len(boss_sources) >= source_limit:
                    return

        per_boss_selector = max(2, source_limit // 4)
        add_boss_sources(sorted(
            boss_pool,
            key=lambda e: (e.get("_dmg", 0), e.get("_yd", 0), e.get("_bd", 0), -e["hp"]),
        )[:per_boss_selector])
        add_boss_sources(sorted(
            [e for e in boss_pool if boss_feasible_rough(e)],
            key=lambda e: (*cost_key(e), -e["hp"]),
        )[:per_boss_selector])
        add_boss_sources(sorted(
            boss_pool,
            key=lambda e: (boss_survival_deficit(e), *cost_key(e), -e["hp"]),
        )[:per_boss_selector])
        add_boss_sources(sorted(
            boss_pool,
            key=lambda e: (e.get("_yd", 0), e.get("_bd", 0), e.get("_dmg", 0), -e["hp"]),
        )[:per_boss_selector])
        add_boss_sources(sorted(
            boss_pool,
            key=lambda e: (-e["yk"], e.get("_dmg", 0), e.get("_yd", 0), -e["hp"]),
        )[:per_boss_selector])
        boss_new = []
        for ent in boss_sources:
            boss_new.extend(boss_action(ent))
        if boss_new:
            new_results.extend(boss_new)
            action_counts.append(("MT10:boss", len(boss_sources), len(boss_new)))

        if not new_results:
            rows.append({
                "round": round_no,
                "entries": len(entries),
                "new": 0,
                "goals": len(best_goals(entries)),
                "actions": [],
            })
            break

        entries = trim_entries(entries + new_results, entry_limit)
        late_boss_pool = [
            e for e in entries
            if e["rk"] >= 1 and e["atk"] >= 27 and e["def"] >= 27
        ]
        late_boss_sources = []
        seen_late = set()
        for selector in [
            lambda e: (0 if boss_feasible_rough(e) else 1, *cost_key(e), -e["hp"]),
            lambda e: (boss_survival_deficit(e), *cost_key(e), -e["hp"]),
            lambda e: (e.get("_dmg", 0), e.get("_yd", 0), e.get("_bd", 0), -e["hp"]),
        ]:
            for e in sorted(late_boss_pool, key=selector)[:max(2, source_limit // 4)]:
                if e["_id"] in seen_late:
                    continue
                seen_late.add(e["_id"])
                late_boss_sources.append(e)
        late_boss_new = []
        for ent in late_boss_sources:
            late_boss_new.extend(boss_action(ent))
        if late_boss_new:
            entries = trim_entries(entries + late_boss_new, entry_limit)
            action_counts.append(("MT10:boss_late", len(late_boss_sources), len(late_boss_new)))
        goals = best_goals(entries)
        rows.append({
            "round": round_no,
            "entries": len(entries),
            "new": len(new_results),
            "goals": len(goals),
            "diagnostics": diagnostics(entries),
            "best_goal": state_record(goals[0]) | {
                "dmg": goals[0].get("_dmg", 0),
                "yd": goals[0].get("_yd", 0),
                "bd": goals[0].get("_bd", 0),
                "rd": goals[0].get("_rd", 0),
            } if goals else None,
            "actions": action_counts[:12],
        })
        print(
            f"round {round_no}: entries={len(entries)} new={len(new_results)} goals={len(goals)} "
            f"stat27={rows[-1]['diagnostics']['stat27']} rk={rows[-1]['diagnostics']['redkey']}",
            flush=True,
        )
        if goals:
            print(f"  best {state_text(goals[0])}", flush=True)

    goals = best_goals(entries)
    elapsed = time.time() - t0
    data = {
        "elapsed": elapsed,
        "rounds": rows,
        "entry_count": len(entries),
        "goal_count": len(goals),
        "best": None,
        "top_goals": [],
        "boss_probe": None,
    }
    if not goals:
        redkey = [e for e in entries if e["rk"] >= 1 and e["atk"] >= 27 and e["def"] >= 27]
        probe_source = sorted(
            redkey,
            key=lambda e: (boss_survival_deficit(e), *cost_key(e), -e["hp"]),
        )[0] if redkey else None
        data["boss_probe"] = boss_probe(probe_source) if probe_source else None
    if goals:
        best = goals[0]
        data["best"] = state_record(best) | {
            "dmg": best.get("_dmg", 0),
            "yd": best.get("_yd", 0),
            "bd": best.get("_bd", 0),
            "rd": best.get("_rd", 0),
        }
        data["top_goals"] = [
            state_record(e) | {
                "dmg": e.get("_dmg", 0),
                "yd": e.get("_yd", 0),
                "bd": e.get("_bd", 0),
                "rd": e.get("_rd", 0),
                "mt10_stage": mt10_stage(e),
            }
            for e in goals[:10]
        ]
        write_walk(best)
    write_outputs(data)
    return data


def write_outputs(data):
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    lines = [
        "# Post-9F Action Search",
        "",
        f"- elapsed: {data['elapsed']:.1f}s",
        f"- final entry count: {data['entry_count']}",
        f"- goal count: {data['goal_count']}",
    ]
    if data["best"]:
        b = data["best"]
        lines.append(
            f"- best: HP={b['hp']} ATK={b['atk']} DEF={b['def']} "
            f"YK={b['yk']} BK={b['bk']} RK={b['rk']} "
            f"dmg={b['dmg']} door={b['yd']}/{b['bd']}/{b['rd']}"
        )
    lines.extend([
        "",
        "## Rounds",
        "",
        "| stage | round | entries | new | goals | best goal |",
        "|---|---:|---:|---:|---:|---|",
    ])
    for row in data["rounds"]:
        best = "-"
        if row.get("best_goal"):
            b = row["best_goal"]
            best = (
                f"HP={b['hp']} dmg={b['dmg']} "
                f"door={b['yd']}/{b['bd']}/{b['rd']}"
            )
        lines.append(
            f"| {row.get('stage', 'all')} | {row['round']} | {row['entries']} | {row['new']} | "
            f"{row['goals']} | {best} |"
        )
    lines.extend([
        "",
        "## Diagnostics",
        "",
        "| stage | round | stat27 | redkey | MT10 any/left/right | high-stat best | stat27 best | redkey-ready | redkey best | redkey feasible | redkey deficit |",
        "|---|---:|---:|---:|---:|---|---|---|---|---|---|",
    ])
    for row in data["rounds"]:
        d = row.get("diagnostics") or {}

        def fmt(st):
            if not st:
                return "-"
            return (
                f"HP={st['hp']} A/D={st['atk']}/{st['def']} "
                f"Y/B/R={st['yk']}/{st['bk']}/{st['rk']} "
                f"dmg={st['dmg']} door={st['yd']}/{st['bd']}/{st['rd']} "
                f"mt10={st['mt10_stage']}"
            )

        lines.append(
            f"| {row.get('stage', 'all')} | {row['round']} | {d.get('stat27', 0)} | {d.get('redkey', 0)} | "
            f"{d.get('mt10_any', 0)}/{d.get('mt10_left', 0)}/{d.get('mt10_right', 0)} | "
            f"{fmt(d.get('best_high_stat'))} | {fmt(d.get('best_stat27'))} | "
            f"{fmt(d.get('best_redkey_ready'))}<br>hp:{fmt(d.get('best_redkey_ready_hp'))} | "
            f"{fmt(d.get('best_redkey'))}<br>hp:{fmt(d.get('best_redkey_hp'))} | {fmt(d.get('best_redkey_feasible'))} | "
            f"{fmt(d.get('best_redkey_deficit'))} |"
        )
    if data["top_goals"]:
        lines.extend([
            "",
            "## Top Goals",
            "",
            "| # | state | dmg | door Y/B/R | MT10 stage |",
            "|---:|---|---:|---:|---|",
        ])
        for idx, e in enumerate(data["top_goals"], 1):
            lines.append(
                f"| {idx} | HP={e['hp']} ATK={e['atk']} DEF={e['def']} "
                f"YK={e['yk']} BK={e['bk']} RK={e['rk']} | "
                f"{e['dmg']} | {e['yd']}/{e['bd']}/{e['rd']} | {e['mt10_stage']} |"
            )
    if data.get("boss_probe"):
        lines.extend(["", "## Boss Probe", ""])
        lines.append(f"- source: {data['boss_probe']['source']}")
        lines.append(f"- base_count: {data['boss_probe']['base_count']}")
        lines.append(f"- redDoor_pareto: {data['boss_probe']['redDoor_pareto']}")
        for sample in data["boss_probe"]["samples"][:8]:
            lines.append(f"- sample: {sample}")
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds", type=int, default=20)
    parser.add_argument("--entry-limit", type=int, default=360)
    parser.add_argument("--source-limit", type=int, default=28)
    parser.add_argument("--out-suffix", default="")
    parser.add_argument("--staged", action="store_true")
    args = parser.parse_args()

    global OUT_JSON, OUT_MD, OUT_WALK
    if args.out_suffix:
        OUT_JSON = os.path.join("outputs", "results", f"post9_action_search_{args.out_suffix}.json")
        OUT_MD = os.path.join("outputs", "reports", f"post9_action_search_{args.out_suffix}.md")
        OUT_WALK = os.path.join("outputs", "walkthroughs", f"walkthrough_post9_action_best_{args.out_suffix}.md")

    data = (
        run_staged(args.rounds, args.entry_limit, args.source_limit)
        if args.staged else
        run(args.rounds, args.entry_limit, args.source_limit)
    )
    print(f"wrote {OUT_JSON}")
    print(f"wrote {OUT_MD}")
    if data["best"]:
        print(f"wrote {OUT_WALK}")


if __name__ == "__main__":
    main()
