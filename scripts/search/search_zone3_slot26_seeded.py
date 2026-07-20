#!/usr/bin/env python3
"""Seeded zone-3 search from slot26.

The broad slot26 search tends to spend most of its time rediscovering the
fragile 32F/33F setup. This runner first builds legal sword + 2F reward seeds
with the focused macro probe, then lets the guided beam search optimize the
remaining 34F/38F/39F/40F route.
"""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import os
import sys
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
GUIDED_PATH = ROOT / "scripts" / "search" / "search_zone3_slot26_guided.py"
MACRO_PATH = ROOT / "scripts" / "search" / "probe_zone3_slot26_sword_macro.py"

OUT_JSON = ROOT / "outputs" / "results" / "zone3_slot26_seeded_2h.json"
OUT_MD = ROOT / "outputs" / "reports" / "zone3_slot26_seeded_2h.md"
OUT_LOG = ROOT / "outputs" / "logs" / "zone3_slot26_seeded_2h_progress.log"


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


guided = load_module("zone3_seeded_guided", GUIDED_PATH)
macro = load_module("zone3_seeded_macro", MACRO_PATH)
base = guided.base

MT17_RIGHT_RESOURCE_TARGETS = [
    ("MT17", 9, 8, "17F right lower zombie opens lower special door 1/2"),
    ("MT17", 11, 8, "17F right lower zombie opens lower special door 2/2"),
    ("MT17", 9, 5, "17F right upper zombieKnight opens upper special door 1/2"),
    ("MT17", 11, 5, "17F right upper zombieKnight opens upper special door 2/2"),
    ("MT17", 9, 3, "17F right yellowKey after special doors"),
    ("MT17", 9, 1, "17F right redGem"),
    ("MT17", 11, 3, "17F right yellowKey"),
    ("MT17", 11, 1, "17F right blueGem"),
    ("MT17", 10, 2, "17F right bluePotion"),
]


def shop_buys(g: Any) -> int:
    return max(0, int(g.state.get("times1", 2)) - 2)


def missing(g: Any, fid: str, pos: tuple[int, int], eid: str | None = None) -> bool:
    block = g.block_at(fid, pos)
    if block is None:
        return True
    return eid is not None and block.eid != eid


def mt34_center_done(g: Any) -> bool:
    return missing(g, "MT34", (2, 6), "redKey")


def seeded_score(g: Any) -> int:
    s = g.state
    score = guided.guided_score(g)
    score += min(shop_buys(g), 8) * 35_000
    score -= max(0, shop_buys(g) - 8) * 500_000
    if mt34_center_done(g) or s["rk"] > 0:
        score += 240_000
    if guided.has_shield3(g):
        score += 260_000
    if s.get("centerFly3"):
        score += 260_000
    if s.get("boss40") or missing(g, "MT40", (6, 1), "upFloor"):
        score += 600_000
    # Before 41F, excess HP is worth less because the next floor halves it,
    # but very low HP candidates often cannot survive the remaining forced
    # fights, so do not let pure progress dominate survival.
    score -= max(0, s["hp"] - 1400) // 3
    score -= max(0, 500 - s["hp"]) * 220
    return int(score)


def seeded_goal_score(g: Any) -> int:
    s = g.state
    stock = s["hp"] + s["yk"] * 50 + s["bk"] * 200 + s["gold"] * 0.5
    return int(
        stock
        + s["atk"] * 320
        + s["def"] * 340
        - s["dmg"]
        - s["yd"] * 50
        - s["bd"] * 200
        - s["rd"] * 350
        + base.remaining_simple_value(g)
    )


def seeded_bucket(g: Any) -> tuple[Any, ...]:
    s = g.state
    visited_max = max((base.floor_no(fid) for fid in s.get("visited", {"MT31"})), default=31)
    return (
        visited_max,
        mt34_center_done(g),
        guided.has_sword3(g),
        guided.has_shield3(g),
        bool(s.get("centerFly3")),
        bool(s.get("boss40")),
        s["floor"],
        s["atk"] // 4,
        s["def"] // 4,
        min(s["hp"], 2600) // 80,
        s["yk"],
        s["bk"],
        s["rk"],
        min(shop_buys(g), 9),
        min(6000, max(-1000, s["gold"])) // 80,
    )


def install_seeded_guidance() -> None:
    guided.install_guidance()
    base.score = seeded_score
    base.goal_score = seeded_goal_score
    base.state_bucket = seeded_bucket


def valid(g: Any) -> bool:
    return not g.errors and g.state["hp"] > 0


def clone(g: Any) -> Any:
    return copy.deepcopy(g)


def add_seed(rows: list[Any], seen: set[tuple[Any, ...]], g: Any, label: str) -> None:
    if not valid(g):
        return
    state = g.state
    key = (
        state["floor"],
        state["x"],
        state["y"],
        state["hp"],
        state["atk"],
        state["def"],
        state["yk"],
        state["bk"],
        state["rk"],
        state["gold"],
        state["times1"],
        len(g.steps),
    )
    if key in seen:
        return
    seen.add(key)
    state["trace"] = [label]
    rows.append(g)


def build_seeds(args: argparse.Namespace) -> list[Any]:
    if args.preserve_pickaxe_only:
        candidate = build_continuous_40_preserve_pickaxe_seed(args)
        if candidate is None:
            return []
        candidate.state["trace"] = ["continuous 40 preserve pickaxe seed"]
        return [candidate]
    seeds: list[Any] = []
    seen: set[tuple[Any, ...]] = set()
    farm_sets = [
        [],
    ]
    if not args.focused_seeds:
        farm_sets.extend([
            [("MT32", 3, 10)],
            [("MT31", 8, 4), ("MT31", 10, 1)],
            [("MT32", 3, 10), ("MT31", 8, 4), ("MT31", 10, 1)],
            [("MT14", 4, 5), ("MT14", 6, 5), ("MT14", 8, 5)],
        ])
    open_orders = ["AA"] if args.focused_seeds else ["AA", "AD", "DA", "AAA", "AAD", "ADA", "DAA", "AAAD", "AADA", "ADAA"]
    late_orders = ["AA"] if args.focused_seeds else ["", "A", "D", "AA", "AD", "DA", "DD", "AAA", "AAD", "ADA", "DAA", "AAAA", "AAAD", "AADA", "ADAA", "AADD", "ADAD", "DDAA"]
    sword_sells = [2] if args.focused_seeds else list(range(0, 6))
    post_orders = ["", "A", "D", "AA", "AD", "DA", "DD", "AADD", "ADAD", "DDAA", "DDDD"] if args.focused_seeds else ["", "A", "D", "AA", "AD", "DA", "DD", "AAA", "AAD", "ADA", "DAA", "ADD", "DAD", "DDA", "AAAA", "AAAD", "AADA", "ADAA", "AADD", "ADAD", "DDAA", "DDDD"]
    post_sells = [0, 1, 2] if args.focused_seeds else list(range(0, 4))
    hp_targets = (500, 800, 1050, 1350, 1800, 2200) if not args.focused_seeds else (500, 800, 1050, 1800, 2200)
    for open_order in open_orders:
        if len(seeds) >= args.max_seeds:
            break
        base0 = macro.start_to_right_resources(open_order)
        if not valid(base0):
            continue
        for farms in farm_sets:
            if len(seeds) >= args.max_seeds:
                break
            farmed = macro.farm_targets(base0, farms)
            if not valid(farmed):
                continue
            for sell_n in sword_sells:
                if len(seeds) >= args.max_seeds:
                    break
                for late_order in late_orders:
                    g = clone(farmed)
                    macro.sell(g, sell_n)
                    if not valid(g):
                        continue
                    macro.buy(g, late_order)
                    if not valid(g):
                        continue
                    if args.focused_seeds and g.state["atk"] < 100:
                        continue
                    sword = macro.try_sword(g)
                    if not valid(sword):
                        continue
                    after2 = macro.after_sword_to_2f(sword)
                    if not valid(after2):
                        continue
                    label0 = f"seed after2 open={open_order} sell={sell_n} late={late_order} farms={farms}"
                    add_seed(seeds, seen, clone(after2), label0)
                    extra = macro.collect_extra_keys(after2)
                    if valid(extra):
                        add_seed(seeds, seen, clone(extra), label0 + " extraKeys")
                    for post_sell in post_sells:
                        for order in post_orders:
                            post = clone(extra if valid(extra) else after2)
                            macro.sell(post, post_sell)
                            if not valid(post):
                                continue
                            macro.buy(post, order)
                            if not valid(post):
                                continue
                            if shop_buys(post) > 8:
                                continue
                            for hp_target in hp_targets:
                                healed = macro.eat_potions_until(post, hp_target, preserve_yk=1)
                                if not valid(healed):
                                    continue
                                label = f"{label0} postSell={post_sell} postOrder={order} hp={hp_target}"
                                add_seed(seeds, seen, clone(healed), label)
                                r37 = macro.to_37_minimal(healed)
                                if valid(r37):
                                    add_seed(seeds, seen, r37, label + " to37")
                                pre34 = macro.collect_pre34_keys(healed)
                                if valid(pre34):
                                    add_seed(seeds, seen, clone(pre34), label + " pre34keys")
                                r37_center = macro.to_37_with_34_center(pre34 if valid(pre34) else healed)
                                if valid(r37_center):
                                    add_seed(seeds, seen, r37_center, label + " 34centerTo37")
                                    prep_options = [
                                        ("potionD", "D", None),
                                        ("potionA", "A", None),
                                        ("potion", "", None),
                                        ("potionD_midD", "D", "D"),
                                        ("potionD_midA", "D", "A"),
                                        ("potionA_midD", "A", "D"),
                                        ("potionA_midA", "A", "A"),
                                    ]
                                    for prep, first_shop, mid_shop in prep_options:
                                        done = clone(r37_center)
                                        if "potion" in prep:
                                            done = macro.try_take(done, "MT34", 1, 11, "34 left blue potion before 38")
                                        if first_shop:
                                            macro.buy(done, first_shop)
                                        done = macro.finish_from_37_center(done, mid_shop=mid_shop)
                                        if valid(done) and done.state.get("boss40"):
                                            add_seed(seeds, seen, done, label + f" finish:{prep}")
                    if len(seeds) >= args.max_seeds:
                        break
    if len(seeds) < args.max_seeds:
        build_bridge_entry_seeds(args, seeds, seen)
    seeds.sort(key=base.score, reverse=True)
    return seeds[: args.max_seeds]


def apply_targets(g: Any, targets: list[tuple[str, int, int, str]]) -> bool:
    for fid, x, y, note in targets:
        before_errors = len(g.errors)
        ok = base.move_to(g, fid, x, y, note)
        if not ok or len(g.errors) != before_errors:
            return False
    return valid(g)


def trigger_mt32_event(g: Any) -> bool:
    before_errors = len(g.errors)
    if not base.move_to(g, "MT31", 6, 11, "bridge seed 31F up"):
        return False
    g.transition("MT32", "31F to 32F", landing=(6, 11))
    base.mark_visited(g, "MT32")
    if not base.move_to(g, "MT32", 6, 10, "bridge seed 32F event"):
        return False
    g.event_mt32_yellow_knight()
    return valid(g) and len(g.errors) == before_errors


def buy_order(g: Any, order: str) -> bool:
    if not order:
        return valid(g)
    if g.state["floor"] != "MT32":
        if base.floor_no(g.state["floor"]) > 32 and base.can_fly_to(g, "MT31"):
            g.fly("MT31")
        g.fly("MT32")
    if not prepare_mt32_shop_access(g):
        return False
    before_errors = len(g.errors)
    try:
        g.move_adjacent("MT32", 10, 10, "continuous seed 32F shop adjacent")
    except Exception:
        return False
    if len(g.errors) != before_errors:
        return False
    for ch in order:
        cost = base.p.shop_cost(g.state["times1"])
        if g.state["gold"] < cost:
            return False
        g.buy_shop("atk" if ch == "A" else "def", 1)
    return valid(g)


def move_required(g: Any, fid: str, x: int, y: int, note: str) -> bool:
    before_errors = len(g.errors)
    return base.move_to(g, fid, x, y, note) and len(g.errors) == before_errors and valid(g)


def move_optional(g: Any, fid: str, x: int, y: int, note: str) -> bool:
    before_errors = len(g.errors)
    before = g.snapshot()
    ok = base.move_to(g, fid, x, y, note)
    if len(g.errors) > before_errors:
        del g.errors[before_errors:]
        return False
    return bool(ok and g.snapshot() != before)


MT32_SHOP_ACCESS_GHOST = ("MT32", 8, 11)
MT32_SHOP_EMERGENCY_POTIONS = [
    ("MT20", 6, 8),
    ("MT20", 5, 8),
    ("MT20", 7, 8),
]


def can_survive_enemy(g: Any, eid: str) -> bool:
    dmg = g.enemy_damage(eid)
    return dmg != float("inf") and g.state["hp"] - int(dmg) > 0


def prepare_mt32_shop_access(g: Any) -> bool:
    """Open the real live path to the 32F shop.

    The web shop is three no-pass tiles wide. From the central corridor the
    hero must first clear MT32 x8y11 to stand below the shop; the local map
    used to treat the shop wings as passable and could buy too early.
    """

    block = g.block_at("MT32", (8, 11))
    if not block:
        return True
    if block.kind != "enemy":
        return False
    while not can_survive_enemy(g, block.eid):
        picked = False
        for fid, x, y in MT32_SHOP_EMERGENCY_POTIONS:
            potion = g.block_at(fid, (x, y))
            if not potion or potion.kind != "item" or potion.eid != "bluePotion":
                continue
            if not move_required(g, fid, x, y, f"continuous seed 32F shop emergency potion {fid} x{x}y{y}"):
                return False
            picked = True
            break
        if not picked:
            return False
    return move_required(g, "MT32", 8, 11, "continuous seed 32F shop access ghostSkeleton")


def build_continuous_36_seed(
    args: argparse.Namespace,
    shop1: str = "A",
    shop2: str = "A",
    hp_target: int = 2500,
    preserve_yk: int = 1,
    preserve_bk: int = 0,
    cleanup_steps: int = 1,
) -> Any | None:
    """A legal continuous 31F->37F seed for the strict 4F route.

    This avoids the old slot26 macro assumptions: it farms enough yellow keys
    for 34F, takes the 34F/32F potions before the 2F thief event, then opens
    the 35F passage, then takes the remaining 34F/31F blue potions needed to
    cross 36F and stops at the 37F entry for the generic beam search.

    ``shop1``/``shop2``/``hp_target``/``preserve_yk``/``preserve_bk``/``cleanup_steps``
    parameterize the sword3 decision point (the 33F guard survival buffer +
    post-sword blue-key reachability). Defaults reproduce the original fixed
    route; :func:`build_continuous_36_pareto` sweeps these to find a variant
    that leaves a reachable blue key (and the 15F pickaxe untouched) for the
    preserve-pickaxe 4区 continuation.
    """

    g = base.init_replay(args.snapshot)
    for fid, x, y, note in MT17_RIGHT_RESOURCE_TARGETS:
        if not move_required(g, fid, x, y, f"continuous seed {note}"):
            return None
    if not move_required(g, "MT31", 6, 11, "continuous seed 31F up"):
        return None
    g.transition("MT32", "31F to 32F", landing=(6, 11))
    base.mark_visited(g, "MT32")
    if not move_required(g, "MT32", 6, 10, "continuous seed 32F event"):
        return None
    g.event_mt32_yellow_knight()
    # 先买一攻走 33F 右路；左路 x6y1 高防怪不是骑士剑必经点。
    # 拿到 sword3 的 +40 ATK 后再回 2F 打卫兵领取 1000G。
    if not buy_order(g, shop1):
        return None
    if not move_required(g, "MT32", 11, 1, "continuous seed 32F up"):
        return None
    g.transition("MT33", "32F to 33F", landing=(10, 1))
    base.mark_visited(g, "MT33")
    for x, y in [(8, 2), (11, 3)]:
        if not move_required(g, "MT33", x, y, f"continuous seed 33F pre x{x}y{y}"):
            return None
    for fid, x, y in [
        ("MT14", 9, 1),
        ("MT14", 10, 1),
        ("MT14", 11, 1),
        ("MT14", 11, 2),
        ("MT14", 6, 1),
        ("MT14", 5, 1),
        ("MT15", 11, 8),
        ("MT20", 11, 11),
        ("MT18", 11, 11),
        ("MT19", 4, 1),
        # Kill the MT19 x4y3 zombieKnight so auto_sweep picks up the x8y1
        # blueKey behind it (the 2F oldman blue-door key). The direct x8y1
        # go_to below is unreachable until this zombie dies. Mirrors the
        # verified slot26/minhp25 route (step 45).
        ("MT19", 4, 3),
        ("MT14", 9, 6),
        ("MT18", 10, 10),
        ("MT18", 10, 11),
        ("MT19", 8, 1),
        ("MT20", 10, 10),
        ("MT20", 2, 10),
        ("MT18", 3, 5),
        ("MT18", 1, 5),
    ]:
        move_optional(g, fid, x, y, f"continuous seed resource {fid} x{x}y{y}")
    if not buy_order(g, shop2):
        return None
    try:
        base.p.eat_minimal_potions_until(
            g, hp_target, "33F 骑士剑守卫生存缓冲", min_floor=1,
            preserve_yk=preserve_yk, preserve_bk=preserve_bk,
        )
    except Exception:
        return None
    if not valid(g):
        return None
    if not move_required(g, "MT33", 10, 5, "continuous seed 33F sword trap"):
        return None
    g.event_mt33_sword_trap()
    g.state.setdefault("special_done", set()).add("mt33_sword_trap")
    for x, y in [(9, 5), (11, 5), (9, 7), (11, 7), (10, 10)]:
        if not move_required(g, "MT33", x, y, f"continuous seed sword x{x}y{y}"):
            return None
    # Re-land at the 33F upper entry before going to 34F.
    g.fly("MT31")
    g.fly("MT33")
    if not move_required(g, "MT33", 1, 1, "continuous seed 33F to 34F"):
        return None
    g.transition("MT34", "33F to 34F", landing=(2, 1))
    base.mark_visited(g, "MT34")
    for fid, x, y in [
        ("MT34", 3, 1),
        ("MT32", 11, 4),
    ]:
        if not move_required(g, fid, x, y, f"continuous seed potion {fid} x{x}y{y}"):
            return None
    if __debug__ and os.environ.get("Z3_PARETO_DEBUG"):
        print(f"  [dbg] pre-bluekey: {base.state_line(g)}")
        for fid in sorted(g.visited, key=lambda f: base.floor_no(f)):
            for (bx, by), blk in list(g.floors[fid].blocks.items()):
                if blk.kind == "item" and blk.eid in ("blueKey", "yellowKey"):
                    cand = g.clone()
                    reach = False
                    try:
                        if cand.state["floor"] != fid:
                            cand.fly(fid)
                        cand.go_to(fid, bx, by, "dbg key")
                        reach = True
                    except Exception:
                        reach = False
                    print(f"  [dbg] {blk.eid} {fid} x{bx}y{by}: reachable={reach} (yk={g.state['yk']} bk={g.state['bk']})")
    base.p.cleanup_reachable_items(g, {"blueKey"}, min_floor=1, max_steps=cleanup_steps)
    if g.state["bk"] < 1:
        return None
    for fid, x, y in [
        ("MT2", 3, 1), ("MT2", 6, 2), ("MT2", 8, 2),
        ("MT2", 3, 5), ("MT2", 3, 4), ("MT2", 4, 4), ("MT2", 11, 4),
    ]:
        if not move_required(g, fid, x, y, f"continuous seed 2F x{x}y{y}"):
            return None
    g.oldman_mt2_1000g()
    if not buy_order(g, "ADD"):
        return None
    if not move_required(g, "MT2", 10, 11, "continuous seed 2F thief"):
        return None
    g.thief_mt2_open_35()
    if not move_required(g, "MT34", 6, 11, "continuous seed 34F lower"):
        return None
    g.transition("MT35", "34F to 35F", landing=(6, 11))
    base.mark_visited(g, "MT35")
    if not move_required(g, "MT35", 5, 10, "continuous seed 35F thief"):
        return None
    g.thief_mt35_depart()
    if not move_required(g, "MT35", 11, 1, "continuous seed 35F to 36F"):
        return None
    g.transition("MT36", "35F to 36F", landing=(11, 2))
    base.mark_visited(g, "MT36")
    for fid, x, y in [
        ("MT34", 1, 11),
        ("MT31", 8, 8),
    ]:
        if not move_required(g, fid, x, y, f"continuous seed late potion {fid} x{x}y{y}"):
            return None
    if not move_required(g, "MT36", 11, 11, "continuous seed 36F to 37F"):
        return None
    g.transition("MT37", "36F to 37F", landing=(11, 10))
    base.mark_visited(g, "MT37")
    return g if valid(g) else None


def build_continuous_38_pickaxe_seed(args: argparse.Namespace) -> Any | None:
    """Extend the strict 37F seed through the 15F pickaxe and 37F red key."""

    g = build_continuous_36_seed(args)
    if g is None:
        return None
    for fid, x, y in [
        ("MT2", 4, 10),
        ("MT2", 3, 11),
        ("MT2", 3, 10),
        ("MT32", 10, 4),
    ]:
        if not move_required(g, fid, x, y, f"continuous pickaxe seed resource {fid} x{x}y{y}"):
            return None
    if not buy_order(g, "AA"):
        return None
    if not move_required(g, "MT36", 1, 11, "continuous pickaxe seed 36F bluePotion"):
        return None
    g.fly("MT14")
    g.fly("MT15")
    for fid, x, y in [
        ("MT15", 6, 6),
        ("MT15", 6, 5),
        ("MT37", 11, 5),
    ]:
        if not move_required(g, fid, x, y, f"continuous pickaxe seed {fid} x{x}y{y}"):
            return None
    before_errors = len(g.errors)
    g.use_pickaxe("MT37", 10, 5, "continuous pickaxe seed 37F break wall")
    if len(g.errors) != before_errors:
        return None
    for fid, x, y in [
        ("MT37", 7, 5),
        ("MT37", 11, 1),
        ("MT37", 1, 1),
    ]:
        if not move_required(g, fid, x, y, f"continuous pickaxe seed {fid} x{x}y{y}"):
            return None
    g.transition("MT38", "37F to 38F", landing=(2, 1))
    base.mark_visited(g, "MT38")
    return g if valid(g) else None


def build_continuous_40_pickaxe_seed(args: argparse.Namespace) -> Any | None:
    """Extend the strict pickaxe route to the 40F boss reward endpoint."""

    g = build_continuous_38_pickaxe_seed(args)
    if g is None:
        return None
    for fid, x, y in [
        ("MT37", 7, 3),
        ("MT37", 8, 3),
        ("MT14", 1, 11),
        ("MT31", 8, 10),
        ("MT31", 9, 10),
        ("MT31", 8, 11),
        ("MT31", 9, 11),
        ("MT38", 3, 1),
        ("MT38", 5, 2),
    ]:
        if not move_required(g, fid, x, y, f"continuous 40 seed {fid} x{x}y{y}"):
            return None
    g.buy_mt38_yellow_keys()
    for fid, x, y in [
        # x5y8 blueGem is sealed behind x6y8 redPotion. Skip the whole
        # support-resource branch before the zone-4 half-HP trap; deleting the
        # potion alone would make the gem unreachable.
        ("MT38", 1, 10),
        ("MT38", 3, 10),
        ("MT38", 2, 7),
        ("MT38", 11, 1),
    ]:
        if not move_required(g, fid, x, y, f"continuous 40 seed {fid} x{x}y{y}"):
            return None
    g.transition("MT39", "38F to 39F", landing=(11, 1))
    base.mark_visited(g, "MT39")
    for fid, x, y in [
        ("MT39", 11, 3),
        ("MT39", 11, 6),
        ("MT38", 11, 11),
        ("MT38", 11, 1),
    ]:
        if not move_required(g, fid, x, y, f"continuous 40 seed {fid} x{x}y{y}"):
            return None
    g.transition("MT39", "38F to 39F puzzle", landing=(11, 1))
    base.mark_visited(g, "MT39")
    before_errors = len(g.errors)
    base.quick.open_mt39_puzzle(g)
    if len(g.errors) != before_errors:
        return None
    for fid, x, y in [
        ("MT39", 3, 11),
        ("MT39", 5, 9),
        ("MT39", 6, 9),
        ("MT39", 11, 11),
    ]:
        if not move_required(g, fid, x, y, f"continuous 40 seed {fid} x{x}y{y}"):
            return None
    g.transition("MT40", "39F to 40F", landing=(11, 11))
    base.mark_visited(g, "MT40")
    before_errors = len(g.errors)
    base.quick.use_center_fly_to_mt40_boss_area(g)
    if len(g.errors) != before_errors:
        return None
    for x, y in [(2, 2), (3, 2), (4, 2), (3, 4), (4, 4), (5, 4), (7, 4), (8, 4), (9, 4), (8, 2), (9, 2), (10, 2)]:
        if not move_required(g, "MT40", x, y, f"continuous 40 seed MT40 x{x}y{y}"):
            return None
    if not move_required(g, "MT40", 6, 7, "continuous 40 seed boss trigger"):
        return None
    before_errors = len(g.errors)
    base.quick.event_mt40_boss(g)
    g.state["boss40"] = True
    if len(g.errors) != before_errors:
        return None
    for x, y in [(2, 2), (3, 2), (4, 2), (8, 2), (9, 2), (10, 2), (7, 4), (8, 4), (9, 4)]:
        if not move_required(g, "MT40", x, y, f"continuous 40 seed reward MT40 x{x}y{y}"):
            return None
    if not move_required(g, "MT40", 6, 1, "continuous 40 seed 40F stairs"):
        return None
    return g if valid(g) else None


def build_continuous_36_pareto(args: argparse.Namespace) -> list[Any]:
    """Sweep the 33F sword3 decision point and keep variants that reach the
    37F entry with a reachable post-sword blue key while leaving the 15F
    pickaxe untouched (``MT15 x6y5`` still on the map).

    The original fixed route (shop1=shop2="A", hp=2500, preserve_yk=1) exhausts
    yellow keys on the survival-buffer potion path, making the MT14 x1y11 blue
    key unreachable after sword3 -> ``no legal seeds``. Sweeping shop order /
    HP target / preserve_yk / preserve_bk / cleanup_steps finds a variant whose
    buffer path preserves enough keys. Returns the Pareto frontier
    (non-dominated on hp/yk/bk/atk/def/gold), best-first.
    """
    winners: list[Any] = []
    seen: set[tuple[Any, ...]] = set()
    grid_shop1 = ["A", "D"]
    grid_shop2 = ["A", "D"]
    grid_hp = [2600, 2800]
    grid_pyk = [1, 2, 3]
    grid_pbk = [0, 1]
    grid_clean = [1]
    total = len(grid_shop1) * len(grid_shop2) * len(grid_hp) * len(grid_pyk) * len(grid_pbk) * len(grid_clean)
    tried = 0
    import time as _time
    for shop1 in grid_shop1:
        for shop2 in grid_shop2:
            for hp_target in grid_hp:
                for preserve_yk in grid_pyk:
                    for preserve_bk in grid_pbk:
                        for cleanup_steps in grid_clean:
                            tried += 1
                            _t0 = _time.time()
                            try:
                                g = build_continuous_36_seed(
                                    args, shop1=shop1, shop2=shop2, hp_target=hp_target,
                                    preserve_yk=preserve_yk, preserve_bk=preserve_bk,
                                    cleanup_steps=cleanup_steps,
                                )
                            except Exception as e:  # RouteError / no-path / non-survival
                                print(f"[pareto36 {tried}/{total}] shop1={shop1} shop2={shop2} hp={hp_target} pyk={preserve_yk} pbk={preserve_bk} clean={cleanup_steps} EXC {type(e).__name__} ({_time.time()-_t0:.1f}s)")
                                continue
                            ok = g is not None and valid(g)
                            extra = ""
                            if ok:
                                if g.block_at("MT15", (6, 5)) is None:
                                    extra = " PICKAXE_USED"
                                    ok = False
                                elif g.state["bk"] < 1:
                                    extra = " bk<1"
                                    ok = False
                            print(f"[pareto36 {tried}/{total}] shop1={shop1} shop2={shop2} hp={hp_target} pyk={preserve_yk} pbk={preserve_bk} clean={cleanup_steps} -> {'WIN' if ok else 'fail'}{extra} ({_time.time()-_t0:.1f}s)")
                            if not ok:
                                continue
                            # 15F pickaxe must remain on the map (untouched by 3区).
                            if g.block_at("MT15", (6, 5)) is None:
                                continue
                            if g.state["bk"] < 1:
                                continue
                            key = (
                                g.state["floor"], g.state["hp"], g.state["yk"],
                                g.state["bk"], g.state["atk"], g.state["def"],
                                g.state["gold"], shop1, shop2, hp_target,
                                preserve_yk, preserve_bk, cleanup_steps,
                            )
                            if key in seen:
                                continue
                            seen.add(key)
                            g.state.setdefault("trace", []).append(
                                f"pareto36 shop1={shop1} shop2={shop2} hp={hp_target} "
                                f"pyk={preserve_yk} pbk={preserve_bk} clean={cleanup_steps}"
                            )
                            winners.append(g)
    print(f"[pareto36] tried={tried} winners={len(winners)}")
    if not winners:
        return []

    def dims(gg: Any) -> list[int]:
        s = gg.state
        return [s["hp"], s["yk"], s["bk"], s["atk"], s["def"], s["gold"]]

    def dominates(a: Any, b: Any) -> bool:
        da, db = dims(a), dims(b)
        return all(x >= y for x, y in zip(da, db)) and any(x > y for x, y in zip(da, db))

    frontier = [c for c in winners if not any(dominates(o, c) for o in winners if o is not c)]
    if not frontier:
        frontier = list(winners)
    frontier.sort(
        key=lambda gg: (
            gg.state["hp"] + gg.state["yk"] * 50 + gg.state["bk"] * 200
            + gg.state["gold"] * 0.5 + gg.state["atk"] * 320 + gg.state["def"] * 340
        ),
        reverse=True,
    )
    for gg in frontier:
        print(f"[pareto36] winner: {base.state_line(gg)} trace={gg.state.get('trace', [])[-1]}")
    return frontier


def _extend_preserve_36_to_40(g: Any) -> Any | None:
    """Extend a 36F/37F-entry winner to the 40F boss endpoint via the 34F
    center red key (no 15F pickaxe use). Mirrors the original fixed extension
    but operates on any pareto winner. Returns the extended game or None."""
    for fid, x, y in [
        ("MT2", 4, 10),
        ("MT2", 3, 11),
        ("MT2", 3, 10),
        ("MT32", 10, 4),
    ]:
        if not move_required(g, fid, x, y, f"continuous preserve prep {fid} x{x}y{y}"):
            return None
    if not buy_order(g, "AA"):
        return None
    if not move_required(g, "MT36", 1, 11, "continuous preserve 36F bluePotion"):
        return None
    for fid, x, y in [
        ("MT31", 8, 10),
        ("MT31", 9, 10),
        ("MT31", 8, 11),
        ("MT31", 9, 11),
        ("MT31", 3, 1),
        ("MT31", 4, 1),
        ("MT31", 3, 2),
        ("MT31", 4, 2),
        ("MT32", 2, 5),
        ("MT34", 6, 1),
        ("MT9", 1, 7),
        ("MT9", 5, 7),
        ("MT18", 5, 11),
        ("MT18", 7, 11),
    ]:
        if not move_required(g, fid, x, y, f"continuous preserve key {fid} x{x}y{y}"):
            return None
    for x, y in [(5, 4), (7, 4), (9, 4), (11, 4), (5, 8), (7, 8), (9, 8), (11, 8)]:
        if not move_required(g, "MT34", x, y, f"continuous preserve 34F center x{x}y{y}"):
            return None
    for x, y in [(2, 6), (1, 5), (3, 5), (1, 7), (3, 7)]:
        if not move_required(g, "MT34", x, y, f"continuous preserve 34F reward x{x}y{y}"):
            return None
    act37 = base.next_floor_action(g, "MT37")
    if not act37 or not act37["apply"](g) or not valid(g):
        return None
    for fid, x, y in [
        ("MT38", 3, 1),
        ("MT38", 5, 2),
    ]:
        if not move_required(g, fid, x, y, f"continuous preserve 38F merchant path {fid} x{x}y{y}"):
            return None
    g.buy_mt38_yellow_keys()
    if not valid(g):
        return None
    for fid, x, y in [
        ("MT37", 11, 1),
        ("MT38", 6, 2),
        ("MT34", 10, 1),
        ("MT34", 9, 1),
        ("MT38", 11, 11),
        ("MT31", 4, 4),
        ("MT38", 9, 4),
        ("MT38", 5, 8),
        ("MT38", 1, 10),
        ("MT38", 3, 10),
        ("MT38", 2, 7),
    ]:
        if not move_required(g, fid, x, y, f"continuous preserve 38F prep {fid} x{x}y{y}"):
            return None
    if not buy_order(g, "D"):
        return None
    if not move_required(g, "MT38", 11, 1, "continuous preserve 38F up"):
        return None
    g.transition("MT39", "38F to 39F preserve", landing=(11, 1))
    base.mark_visited(g, "MT39")
    if not move_required(g, "MT39", 11, 3, "continuous preserve 39F yellowKey"):
        return None
    before_errors = len(g.errors)
    base.quick.open_mt39_puzzle(g)
    if len(g.errors) != before_errors or not valid(g):
        return None
    for fid, x, y in [
        ("MT39", 3, 11),
        ("MT39", 5, 9),
        ("MT39", 6, 9),
        ("MT39", 9, 11),
        ("MT39", 11, 11),
    ]:
        if not move_required(g, fid, x, y, f"continuous preserve 39F after puzzle {fid} x{x}y{y}"):
            return None
    g.transition("MT40", "39F to 40F preserve", landing=(11, 11))
    base.mark_visited(g, "MT40")
    if not move_required(g, "MT40", 9, 9, "continuous preserve 40F redPotion before centerFly"):
        return None
    before_errors = len(g.errors)
    base.quick.use_center_fly_to_mt40_boss_area(g)
    if len(g.errors) != before_errors or not valid(g):
        return None
    for x, y in [(2, 2), (3, 2), (4, 2), (3, 4), (4, 4), (5, 4), (7, 4), (8, 4), (9, 4), (8, 2), (9, 2), (10, 2)]:
        if not move_required(g, "MT40", x, y, f"continuous preserve 40F guard x{x}y{y}"):
            return None
    if not move_required(g, "MT40", 6, 7, "continuous preserve 40F boss trigger"):
        return None
    before_errors = len(g.errors)
    base.quick.event_mt40_boss(g)
    g.state["boss40"] = True
    if len(g.errors) != before_errors or not valid(g):
        return None
    g = base.finish_goal_candidate(g)
    return g if valid(g) and g.block_at("MT15", (6, 5)) else None


def build_continuous_40_preserve_pickaxe_seed(args: argparse.Namespace) -> Any | None:
    """Strict 4F-chain 40F endpoint that leaves the 15F pickaxe available.

    The route gets the 34F center red key instead of spending the 15F pickaxe on
    the 37F red-key wall. It then takes the 38F shield/core, buys one 32F DEF
    shop, and uses 39F/40F potions to pass the 40F guards with low HP.

    The 33F sword3 decision point is swept by :func:`build_continuous_36_pareto`;
    each Pareto winner is extended to 40F and the best boss40 endpoint (with the
    15F pickaxe still untouched) is returned.
    """
    winners = build_continuous_36_pareto(args)
    if not winners:
        return None
    best: Any | None = None
    for seed in winners:
        try:
            g = _extend_preserve_36_to_40(clone(seed))
        except Exception:
            continue
        if g is None or not valid(g) or not g.state.get("boss40"):
            continue
        if g.block_at("MT15", (6, 5)) is None:
            continue
        if best is None or base.goal_score(g) > base.goal_score(best):
            best = g
            print(f"[preserve40] new best: {base.state_line(g)}")
    return best


def build_bridge_entry_seeds(args: argparse.Namespace, seeds: list[Any], seen: set[tuple[Any, ...]]) -> None:
    """Fallback seeds for a continuous 20F->31F bridge snapshot."""

    base_start = base.init_replay(args.snapshot)
    prelude_variants = [
        [
            *MT17_RIGHT_RESOURCE_TARGETS,
        ],
        [
            *MT17_RIGHT_RESOURCE_TARGETS,
            ("MT31", 8, 10, "bridge seed 31F yellowKey"),
            ("MT31", 9, 10, "bridge seed 31F yellowKey"),
            ("MT31", 8, 11, "bridge seed 31F yellowKey"),
            ("MT31", 9, 11, "bridge seed 31F yellowKey"),
        ],
        [
            *MT17_RIGHT_RESOURCE_TARGETS,
            ("MT31", 8, 10, "bridge seed 31F yellowKey"),
            ("MT31", 9, 10, "bridge seed 31F yellowKey"),
            ("MT31", 8, 11, "bridge seed 31F yellowKey"),
            ("MT31", 9, 11, "bridge seed 31F yellowKey"),
            ("MT31", 8, 8, "bridge seed 31F bluePotion"),
        ],
        [
            *MT17_RIGHT_RESOURCE_TARGETS,
            ("MT31", 8, 10, "bridge seed 31F yellowKey"),
            ("MT31", 9, 10, "bridge seed 31F yellowKey"),
            ("MT31", 8, 11, "bridge seed 31F yellowKey"),
            ("MT31", 9, 11, "bridge seed 31F yellowKey"),
            ("MT14", 5, 1, "bridge seed 14F blueGem"),
        ],
    ]
    shop_orders = ["", "A", "D", "AA", "AD", "DA", "DD", "AAD", "ADA", "DAA", "ADD", "DAD", "DDA", "AADD", "ADAD", "DDAA"]
    for idx, targets in enumerate(prelude_variants, 1):
        if len(seeds) >= args.max_seeds:
            return
        pre = clone(base_start)
        if not apply_targets(pre, targets):
            continue
        event_state = clone(pre)
        if not trigger_mt32_event(event_state):
            continue
        add_seed(seeds, seen, clone(event_state), f"bridgePrelude{idx}:event")
        for order in shop_orders:
            if len(seeds) >= args.max_seeds:
                return
            cand = clone(event_state)
            macro.buy(cand, order)
            if not valid(cand):
                continue
            add_seed(seeds, seen, cand, f"bridgePrelude{idx}:event shop={order}")
    continuous = build_continuous_36_seed(args)
    if continuous is not None:
        add_seed(seeds, seen, continuous, "continuousStrict20:to36")
    continuous38 = build_continuous_38_pickaxe_seed(args)
    if continuous38 is not None:
        add_seed(seeds, seen, continuous38, "continuousStrict20:to38Pickaxe")
    continuous40 = build_continuous_40_pickaxe_seed(args)
    if continuous40 is not None:
        add_seed(seeds, seen, continuous40, "continuousStrict20:to40Pickaxe")


def finish_goal_candidate(g: Any) -> Any:
    return base.finish_goal_candidate(g)


def maybe_update_best_goal(best_goal: Any | None, candidate: Any) -> Any | None:
    if not candidate.state.get("boss40"):
        return best_goal
    finished = finish_goal_candidate(candidate)
    if not valid(finished):
        return best_goal
    if best_goal is None or base.goal_score(finished) > base.goal_score(best_goal):
        return finished
    return best_goal


def explore_from_seeds(args: argparse.Namespace, seeds: list[Any]) -> dict[str, Any]:
    frontier = base.select_beam(seeds, args.beam)
    best_any = frontier[0] if frontier else None
    best_goal = None
    for seed in seeds:
        best_goal = maybe_update_best_goal(best_goal, seed)
    expanded = 0
    generated = 0
    started = time.time()
    deadline = started + args.time_limit_seconds
    last_report = started

    def progress(message: str) -> None:
        if args.progress_log:
            args.progress_log.parent.mkdir(parents=True, exist_ok=True)
            with args.progress_log.open("a", encoding="utf-8") as f:
                f.write(message + "\n")
        try:
            print(message, flush=True)
        except OSError:
            pass

    progress(f"[seeded] seeds={len(seeds)} top={base.state_line(frontier[0]) if frontier else '-'}")
    for depth in range(args.max_depth):
        if time.time() >= deadline or not frontier:
            break
        next_rows: list[Any] = []
        for source in frontier:
            if time.time() >= deadline:
                break
            actions = base.special_actions(source) + base.candidate_target_actions(source, args.targets_per_state)
            actions.sort(key=lambda a: a["priority"], reverse=True)
            seen_labels = set()
            for action in actions[: args.actions_per_state]:
                if time.time() >= deadline:
                    break
                label = action["label"]
                if label in seen_labels:
                    continue
                seen_labels.add(label)
                candidate = clone(source)
                before_errors = len(candidate.errors)
                before_steps = len(candidate.steps)
                try:
                    ok = action["apply"](candidate)
                except Exception as exc:
                    candidate.errors.append(f"{label}: exception {exc}")
                    ok = False
                expanded += 1
                if not ok or len(candidate.errors) != before_errors or len(candidate.steps) == before_steps:
                    continue
                candidate.state.setdefault("trace", list(source.state.get("trace", []))).append(label)
                generated += 1
                next_rows.append(candidate)
                if best_any is None or base.score(candidate) > base.score(best_any):
                    best_any = candidate
                best_goal = maybe_update_best_goal(best_goal, candidate)
        frontier = base.select_beam(frontier + next_rows, args.beam)
        now = time.time()
        if now - last_report >= args.report_interval:
            top = frontier[0] if frontier else best_any
            goal_text = base.state_line(best_goal) if best_goal else "-"
            progress(
                f"[{now - started:7.1f}s] depth={depth + 1} frontier={len(frontier)} "
                f"expanded={expanded} generated={generated} top={base.state_line(top) if top else '-'} goal={goal_text}",
            )
            last_report = now

    return {
        "elapsed": time.time() - started,
        "expanded": expanded,
        "generated": generated,
        "beam": args.beam,
        "seed_count": len(seeds),
        "best_any": base.serialize_run(best_any) if best_any else None,
        "best_goal": base.serialize_run(best_goal) if best_goal else None,
    }


def write_report(data: dict[str, Any], out_json: Path, out_md: Path) -> None:
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# Zone3 slot26 seeded 搜索报告",
        "",
        f"- elapsed: `{data['elapsed']:.1f}s`",
        f"- expanded/generated: `{data['expanded']}` / `{data['generated']}`",
        f"- beam: `{data['beam']}`",
        f"- seeds: `{data['seed_count']}`",
        f"- snapshot: `{data.get('snapshot', '-')}`",
        "",
    ]
    for key, title in (("best_goal", "最好 40F Boss 候选"), ("best_any", "最好中间候选")):
        row = data.get(key)
        lines.append(f"## {title}")
        if not row:
            lines.append("- 未找到")
            lines.append("")
            continue
        lines.append(f"- score: `{row['score']}`; goal_score: `{row['goal_score']}`")
        lines.append(f"- simple_stock_score(1YK=50HP=100G): `{row['simple_stock_score']}`")
        lines.append(f"- state: `{row['state_text']}`")
        lines.append(f"- remaining_simple_value: `{row['remaining_simple_value']}`")
        lines.append(f"- errors/warnings: `{len(row['errors'])}` / `{len(row['warnings'])}`")
        lines.append(f"- trace length: `{len(row['trace'])}`; steps: `{len(row['steps'])}`")
        if row["trace"]:
            lines.append("")
            lines.append("### Trace")
            for i, label in enumerate(row["trace"], 1):
                lines.append(f"{i}. `{label}`")
        lines.append("")
        lines.append("### 最后 120 步")
        start = max(1, len(row["steps"]) - 119)
        for i, step in enumerate(row["steps"][-120:], start):
            pos = step.get("pos", ["?", "?"])
            delta = f" [{step.get('delta')}]" if step.get("delta") else ""
            lines.append(f"{i}. {step.get('floor')} x{pos[0]}y{pos[1]} {step.get('action')} {step.get('eid') or ''}{delta}".rstrip())
        lines.append("")
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_walk(data: dict[str, Any], source: Path, out_walk: Path) -> None:
    """Export the offline-replayed best goal as the machine replay walk."""
    goal = data.get("best_goal")
    if not goal:
        raise RuntimeError("cannot write walk without best_goal")
    steps = goal["steps"]
    start = steps[0]["before"] if steps else goal["state"]
    payload = {
        "ok": not goal["errors"],
        "source": str(source),
        "auto": {"battle": True, "item": "nopotion", "wall": True},
        "start": start,
        "final": goal["state"],
        "state_text": goal["state_text"],
        "score": goal["score"],
        "goal_score": goal["goal_score"],
        "simple_stock_score": goal["simple_stock_score"],
        "steps": steps,
        "errors": goal["errors"],
        "warnings": goal["warnings"],
    }
    out_walk.parent.mkdir(parents=True, exist_ok=True)
    out_walk.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    install_seeded_guidance()
    parser = argparse.ArgumentParser()
    parser.add_argument("--time-limit-seconds", type=float, default=7200)
    parser.add_argument("--beam", type=int, default=360)
    parser.add_argument("--targets-per-state", type=int, default=46)
    parser.add_argument("--actions-per-state", type=int, default=74)
    parser.add_argument("--max-depth", type=int, default=320)
    parser.add_argument("--max-seeds", type=int, default=260)
    parser.add_argument("--focused-seeds", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--preserve-pickaxe-only", action="store_true",
                        help="只从严格连续的40F留镐 seed 继续搜索")
    parser.add_argument("--snapshot", type=Path, default=base.DEFAULT_SNAPSHOT)
    parser.add_argument("--report-interval", type=float, default=60)
    parser.add_argument("--progress-log", type=Path, default=OUT_LOG)
    parser.add_argument("--out-json", type=Path, default=OUT_JSON)
    parser.add_argument("--out-md", type=Path, default=OUT_MD)
    parser.add_argument("--out-walk", type=Path, default=None)
    parser.add_argument("--daemon-stdout", type=Path, default=None)
    parser.add_argument("--daemon-stderr", type=Path, default=None)
    args = parser.parse_args()
    if args.daemon_stdout:
        args.daemon_stdout.parent.mkdir(parents=True, exist_ok=True)
        sys.stdout = args.daemon_stdout.open("a", encoding="utf-8", buffering=1)
    if args.daemon_stderr:
        args.daemon_stderr.parent.mkdir(parents=True, exist_ok=True)
        sys.stderr = args.daemon_stderr.open("a", encoding="utf-8", buffering=1)
    macro.set_snapshot(args.snapshot)
    seeds = build_seeds(args)
    if not seeds:
        print("no legal seeds")
        return 1
    data = explore_from_seeds(args, seeds)
    data["snapshot"] = str(args.snapshot)
    write_report(data, args.out_json, args.out_md)
    if args.out_walk:
        write_walk(data, args.out_json, args.out_walk)
    print(f"wrote {args.out_json}")
    print(f"wrote {args.out_md}")
    if args.out_walk:
        print(f"wrote {args.out_walk}")
    if data.get("best_goal"):
        print("best_goal", data["best_goal"]["state_text"])
    else:
        print("best_goal not found")
    if data.get("best_any"):
        print("best_any", data["best_any"]["state_text"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
