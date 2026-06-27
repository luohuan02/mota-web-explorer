#!/usr/bin/env python3
"""Focused slot26 macro probe around 33F sword.

This is a scratch probe for the red-key-after-20F save. It tries the stronger
attack-shop direction and forces money/potion experiments around the 33F sword
checkpoint.
"""

from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "scripts" / "search_zone3_slot26_explore.py"
QUICK = ROOT / "scripts" / "find_zone3_quick_pass_walk.py"


def load_base() -> Any:
    spec = importlib.util.spec_from_file_location("slot26_sword_base", BASE)
    if spec is None or spec.loader is None:
        raise RuntimeError(BASE)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


b = load_base()
quick_spec = importlib.util.spec_from_file_location("slot26_sword_quick", QUICK)
if quick_spec is None or quick_spec.loader is None:
    raise RuntimeError(QUICK)
quick = importlib.util.module_from_spec(quick_spec)
sys.modules[quick_spec.name] = quick
quick_spec.loader.exec_module(quick)


def line(g: Any) -> str:
    return b.state_line(g)


def buy(g: Any, order: str) -> None:
    if g.state["floor"] != "MT32":
        if b.floor_no(g.state["floor"]) > 32 and b.can_fly_to(g, "MT31"):
            g.fly("MT31")
        g.fly("MT32")
    g.go_to("MT32", 10, 10, "shop")
    for ch in order:
        if g.state["gold"] < b.p.shop_cost(g.state["times1"]):
            return
        g.buy_shop("atk" if ch == "A" else "def", 1)


def sell(g: Any, n: int) -> None:
    if n <= 0:
        return
    if g.state["floor"] != "MT28":
        g.fly("MT28")
    g.go_to("MT28", 8, 4, "sell")
    for _ in range(n):
        if g.state["yk"] <= 0:
            g.errors.append("sell no yk")
            return
        before = g.snapshot()
        g.state["yk"] -= 1
        g.state["gold"] += 100
        g.record("merchant", (8, 4), "sellYK", before, "sell 1 YK")


def start_to_right_resources(open_order: str) -> Any:
    g = b.init_replay(b.DEFAULT_SNAPSHOT)
    # Early blue gem path keeps the 32F event survivable without consuming the
    # 15F blue potion before the event.
    b.move_to(g, "MT14", 5, 1, "14F blue gem path")
    b.move_to(g, "MT31", 6, 11, "31F up")
    g.transition("MT32", 6, 11, "31F to 32F")
    b.mark_visited(g, "MT32")
    b.move_to(g, "MT32", 6, 10, "32F event tile")
    g.event_mt32_yellow_knight()
    buy(g, open_order)

    # Core resources that were repeatedly useful in the broad search.
    for fid, x, y in [
        ("MT15", 11, 8),
        ("MT18", 10, 11),
        ("MT19", 8, 1),
        ("MT14", 1, 11),
        ("MT17", 9, 8),
        ("MT17", 11, 8),
        ("MT17", 9, 5),
        ("MT17", 11, 5),
        ("MT17", 9, 1),
        ("MT17", 11, 1),
        ("MT17", 11, 3),
    ]:
        b.move_to(g, fid, x, y, f"{fid} x{x}y{y}")
    return g


def try_sword(g: Any) -> Any:
    out = copy.deepcopy(g)
    b.move_to(out, "MT32", 11, 1, "to 33")
    out.transition("MT33", 10, 1, "32 to 33")
    b.mark_visited(out, "MT33")
    for pos in [(7, 1), (6, 1), (5, 2), (6, 3), (8, 2), (11, 3), (10, 5)]:
        b.move_to(out, "MT33", *pos, "33 pre")
    out.event_mt33_sword_trap()
    # Optional potion/side resources reachable before the four guards.
    for pos in [(2, 4), (5, 10), (1, 11)]:
        before = len(out.errors)
        b.move_to(out, "MT33", *pos, f"optional {pos}")
        if len(out.errors) > before:
            out.errors.pop()
    for pos in [(9, 5), (11, 5), (9, 7), (11, 7), (10, 10)]:
        b.move_to(out, "MT33", *pos, "33 sword")
    return out


def farm_targets(g: Any, targets: list[tuple[str, int, int]]) -> Any:
    out = copy.deepcopy(g)
    for fid, x, y in targets:
        b.move_to(out, fid, x, y, f"farm {fid} x{x}y{y}")
        if out.errors:
            return out
    return out


def try_take(g: Any, fid: str, x: int, y: int, note: str) -> Any:
    out = copy.deepcopy(g)
    before_errors = len(out.errors)
    before = out.snapshot()
    b.move_to(out, fid, x, y, note)
    if len(out.errors) != before_errors:
        return g
    if out.snapshot() == before:
        return g
    return out


def after_sword_to_2f(g: Any) -> Any:
    out = copy.deepcopy(g)
    # Try old potions / cheap resources before the 2F guards.
    for fid, x, y in [
        ("MT33", 2, 4),
        ("MT14", 9, 6),
        ("MT20", 11, 11),
        ("MT20", 11, 4),
        ("MT33", 1, 11),
        ("MT33", 5, 10),
    ]:
        out = try_take(out, fid, x, y, f"post-sword {fid} x{x}y{y}")
    b.move_to(out, "MT2", 3, 1, "2F blue door")
    for pos in [(6, 2), (8, 2), (3, 5), (3, 4), (4, 4), (11, 4)]:
        b.move_to(out, "MT2", *pos, "2F reward")
    if not out.errors:
        out.oldman_mt2_1000g()
        b.move_to(out, "MT2", 10, 11, "2F thief")
        out.thief_mt2_open_35()
    return out


def eat_potions_until(g: Any, target_hp: int, preserve_yk: int = 0) -> Any:
    out = copy.deepcopy(g)
    while out.state["hp"] < target_hp:
        best: tuple[int, Any] | None = None
        for fid, floor in out.floors.items():
            if b.floor_no(fid) > 33:
                continue
            if not b.can_fly_to(out, fid):
                continue
            for (x, y), block in list(floor.blocks.items()):
                if block.kind != "item" or block.eid not in {"redPotion", "bluePotion"}:
                    continue
                cand = try_take(out, fid, x, y, f"eat {fid} x{x}y{y}")
                if cand is out:
                    continue
                if cand.state["yk"] < preserve_yk:
                    continue
                gain = cand.state["hp"] - out.state["hp"]
                if gain <= 0:
                    continue
                # Prefer fewer incidental door/key costs for similar HP gain.
                value = gain * 10 - (cand.state["yd"] - out.state["yd"]) * 80 - (cand.state["bd"] - out.state["bd"]) * 240
                if best is None or value > best[0]:
                    best = (value, cand)
        if best is None:
            break
        out = best[1]
    return out


def collect_extra_keys(g: Any) -> Any:
    out = copy.deepcopy(g)
    for fid, x, y in [
        ("MT14", 9, 1),
        ("MT14", 11, 1),
        ("MT14", 11, 2),
        ("MT32", 1, 10),
        ("MT32", 1, 7),
        ("MT32", 2, 7),
        ("MT32", 3, 7),
        ("MT32", 4, 7),
        ("MT32", 4, 8),
    ]:
        out = try_take(out, fid, x, y, f"extra key {fid} x{x}y{y}")
    return out


def collect_pre34_keys(g: Any) -> Any:
    out = copy.deepcopy(g)
    for fid, x, y in [
        ("MT32", 11, 4),
        ("MT32", 10, 4),
        ("MT32", 11, 7),
        ("MT31", 8, 10),
        ("MT31", 8, 11),
        ("MT31", 9, 10),
        ("MT31", 9, 11),
        ("MT31", 3, 1),
        ("MT31", 4, 1),
        ("MT31", 3, 2),
        ("MT31", 4, 2),
        ("MT31", 4, 4),
    ]:
        out = try_take(out, fid, x, y, f"pre34 key {fid} x{x}y{y}")
    return out


def clear_mt34_center_reward(g: Any) -> Any:
    out = copy.deepcopy(g)
    # Must be done from the upper 34F entry. If we postpone until after 37F and
    # fly back, the fly landing is on the lower side and the center is sealed.
    for pos in [(5, 4), (7, 4), (9, 4), (11, 4), (11, 8), (9, 8), (7, 8), (5, 8)]:
        b.move_to(out, "MT34", *pos, f"34 center enemy {pos}")
        if out.errors:
            return out
    for pos in [(2, 6), (1, 5), (3, 5), (1, 7), (3, 7)]:
        b.move_to(out, "MT34", *pos, f"34 center reward {pos}")
        if out.errors:
            return out
    return out


def take_mt34_non_potion_resources(g: Any) -> Any:
    out = copy.deepcopy(g)
    for pos in [(6, 1), (9, 1), (10, 1), (10, 2), (11, 1), (11, 11), (10, 11)]:
        out = try_take(out, "MT34", *pos, f"34 non-potion {pos}")
    return out


def to_37(g: Any) -> Any:
    out = copy.deepcopy(g)
    b.move_to(out, "MT31", 8, 4, "31F right")
    for pos in [(10, 1), (9, 10), (8, 10), (9, 11), (8, 11)]:
        b.move_to(out, "MT31", *pos, "31F right")
    b.move_to(out, "MT33", 1, 1, "33 to 34")
    out.transition("MT34", 2, 1, "33 to 34")
    b.mark_visited(out, "MT34")
    for pos in [(3, 1), (11, 10), (11, 11), (10, 11), (6, 11)]:
        b.move_to(out, "MT34", *pos, "34 lower")
    out.transition("MT35", 6, 11, "34 to 35")
    b.mark_visited(out, "MT35")
    b.move_to(out, "MT35", 5, 10, "35 thief")
    if not out.errors:
        out.thief_mt35_depart()
    b.move_to(out, "MT35", 11, 1, "35 to 36")
    out.transition("MT36", 11, 2, "35 to 36")
    b.mark_visited(out, "MT36")
    b.move_to(out, "MT36", 11, 11, "36 to 37")
    out.transition("MT37", 11, 10, "36 to 37")
    b.mark_visited(out, "MT37")
    return out


def to_37_minimal(g: Any) -> Any:
    out = copy.deepcopy(g)
    b.move_to(out, "MT33", 1, 1, "33 to 34")
    out.transition("MT34", 2, 1, "33 to 34")
    b.mark_visited(out, "MT34")
    for pos in [(3, 1), (11, 10), (11, 11), (10, 11), (6, 11)]:
        b.move_to(out, "MT34", *pos, "34 lower")
    out.transition("MT35", 6, 11, "34 to 35")
    b.mark_visited(out, "MT35")
    b.move_to(out, "MT35", 5, 10, "35 thief")
    if not out.errors:
        out.thief_mt35_depart()
    b.move_to(out, "MT35", 11, 1, "35 to 36")
    out.transition("MT36", 11, 2, "35 to 36")
    b.mark_visited(out, "MT36")
    b.move_to(out, "MT36", 11, 11, "36 to 37")
    out.transition("MT37", 11, 10, "36 to 37")
    b.mark_visited(out, "MT37")
    return out


def to_37_with_34_center(g: Any) -> Any:
    out = copy.deepcopy(g)
    b.move_to(out, "MT33", 1, 1, "33 to 34")
    out.transition("MT34", 2, 1, "33 to 34")
    b.mark_visited(out, "MT34")
    out = clear_mt34_center_reward(out)
    if out.errors:
        return out
    out = take_mt34_non_potion_resources(out)
    if out.errors:
        return out
    b.move_to(out, "MT34", 6, 11, "34 to 35")
    out.transition("MT35", 6, 11, "34 to 35")
    b.mark_visited(out, "MT35")
    b.move_to(out, "MT35", 5, 10, "35 thief")
    if not out.errors:
        out.thief_mt35_depart()
    b.move_to(out, "MT35", 11, 1, "35 to 36")
    out.transition("MT36", 11, 2, "35 to 36")
    b.mark_visited(out, "MT36")
    b.move_to(out, "MT36", 11, 11, "36 to 37")
    out.transition("MT37", 11, 10, "36 to 37")
    b.mark_visited(out, "MT37")
    return out


def finish_from_37_center(g: Any, take_38_potion: bool = True, mid_shop: str | None = None) -> Any:
    out = copy.deepcopy(g)
    b.move_to(out, "MT37", 1, 1, "37 to 38")
    out.transition("MT38", 1, 1, "37 to 38")
    b.mark_visited(out, "MT38")
    b.move_to(out, "MT38", 3, 1, "38 red door")
    b.move_to(out, "MT38", 5, 2, "38 buy yellow keys")
    if not out.errors:
        out.buy_mt38_yellow_keys()
    b.move_to(out, "MT38", 5, 8, "38 blue gem")
    b.move_to(out, "MT38", 1, 10, "38 left blueGuard")
    b.move_to(out, "MT38", 3, 10, "38 right blueGuard")
    b.move_to(out, "MT38", 2, 7, "38 shield")
    if take_38_potion:
        out = try_take(out, "MT38", 11, 11, "38 blue potion")
    b.move_to(out, "MT38", 11, 1, "38 to 39")
    out.transition("MT39", 11, 1, "38 to 39")
    b.mark_visited(out, "MT39")
    b.move_to(out, "MT39", 11, 3, "39 entrance key")
    b.move_to(out, "MT39", 11, 6, "39 red gem")
    if mid_shop:
        cost = b.p.shop_cost(out.state["times1"])
        if out.state["gold"] < cost:
            out.errors.append(f"39F mid-shop no gold: need={cost} have={out.state['gold']}")
            return out
        buy(out, mid_shop)
    if out.state["floor"] != "MT38":
        out.fly("MT38")
    b.move_to(out, "MT38", 11, 1, "38 re-enter 39 for puzzle")
    out.transition("MT39", 11, 1, "38 to 39 puzzle side")
    b.move_to(out, "MT39", 3, 11, "39 lower-left yellow key before puzzle")
    quick.open_mt39_puzzle(out)
    b.move_to(out, "MT39", 5, 9, "39 ghostSkeleton")
    b.move_to(out, "MT39", 6, 9, "39 blue gem")
    b.move_to(out, "MT39", 11, 11, "39 to 40")
    out.transition("MT40", 11, 11, "39 to 40")
    b.mark_visited(out, "MT40")
    quick.use_center_fly_to_mt40_boss_area(out)
    for pos in [(2, 2), (3, 2), (4, 2), (3, 4), (4, 4), (5, 4), (7, 4), (8, 4), (9, 4), (8, 2), (9, 2), (10, 2)]:
        b.move_to(out, "MT40", *pos, f"40 pre-boss {pos}")
    b.move_to(out, "MT40", 6, 7, "40 boss event")
    quick.event_mt40_boss(out)
    out.state["boss40"] = True
    for pos in [(2, 2), (3, 2), (4, 2), (8, 2), (9, 2), (10, 2), (7, 4), (8, 4), (9, 4)]:
        b.move_to(out, "MT40", *pos, f"40 reward {pos}")
    b.move_to(out, "MT40", 6, 1, "40 stairs")
    return out


def finish_after_2f(g: Any) -> Any | None:
    best: tuple[tuple[Any, ...], str, int, Any] | None = None
    orders = [
        "",
        "A",
        "D",
        "AA",
        "AD",
        "DA",
        "DD",
        "AAA",
        "AAD",
        "ADA",
        "DAA",
        "ADD",
        "DAD",
        "DDA",
        "DDDD",
        "AADD",
        "ADAD",
        "DDAA",
    ]
    for sell_n in range(0, 5):
        for order1 in orders:
            for take_gold_guard in [False, True]:
                for order2 in orders:
                    out = copy.deepcopy(g)
                    sell(out, sell_n)
                    if out.errors:
                        continue
                    buy(out, order1)
                    if take_gold_guard:
                        b.move_to(out, "MT32", 3, 10, "32F blueGuard gold")
                    buy(out, order2)
                    out = eat_potions_until(out, 1400)
                    if out.errors:
                        continue
                    r37 = to_37(out)
                    if r37.errors:
                        key = (False, r37.state["floor"], r37.state["atk"], r37.state["def"], r37.state["hp"])
                        cand = r37
                    else:
                        cand = quick.extend_after_current_checkpoint_v2(copy.deepcopy(r37))
                        key = (
                            not cand.errors,
                            cand.state.get("boss40", False) or cand.state.get("floor") == "MT40",
                            cand.state["atk"],
                            cand.state["def"],
                            cand.state["hp"] + cand.state["gold"] * 0.5 + cand.state["yk"] * 50 + cand.state["bk"] * 200,
                        )
                    if best is None or key > best[0]:
                        best = (key, f"sell={sell_n} order1={order1} guard={take_gold_guard} order2={order2}", len(cand.errors), cand)
                    if not cand.errors:
                        print("FINISH_OK", f"sell={sell_n} order1={order1} guard={take_gold_guard} order2={order2}", line(cand))
                        return cand
    if best:
        print("FINISH_BEST", best[1], "err_count", best[2], line(best[3]), "errors", best[3].errors[:8])
        return best[3]
    return None


def main() -> int:
    farm_sets = [
        [],
        [("MT32", 3, 10)],
        [("MT31", 8, 4), ("MT31", 10, 1)],
        [("MT32", 3, 10), ("MT31", 8, 4), ("MT31", 10, 1)],
        [("MT14", 4, 5), ("MT14", 6, 5), ("MT14", 8, 5)],
        [("MT17", 9, 5), ("MT17", 11, 5)],
    ]
    best: tuple[tuple[Any, ...], str, int, str, int, Any] | None = None
    tried = 0
    for open_order in ["AA", "AD", "DA", "AAA", "AAD", "ADA", "DAA", "AAAD", "AADA", "ADAA"]:
        base = start_to_right_resources(open_order)
        for farms in farm_sets:
            farmed = farm_targets(base, farms)
            if farmed.errors:
                continue
            for sell_n in range(0, 8):
                for late_order in ["", "A", "D", "AA", "AD", "DA", "AAA", "AAD", "ADA", "DAA", "AAAA", "AAAD", "AADA"]:
                    g = copy.deepcopy(farmed)
                    sell(g, sell_n)
                    if g.errors:
                        continue
                    buy(g, late_order)
                    tried += 1
                    s = try_sword(g)
                    ok = not s.errors
                    key = (
                        ok,
                        s.state["atk"],
                        s.state["def"],
                        s.state["hp"],
                        s.state["gold"],
                        -s.state["yd"],
                    )
                    if best is None or key > best[0]:
                        best = (key, open_order, sell_n, late_order, len(farms), s)
                    if ok:
                        print("OK", open_order, "sell", sell_n, "late", late_order, "farms", farms, line(s))
                        e = after_sword_to_2f(s)
                        print("AFTER_2F", "ok", not e.errors, line(e), "errors", e.errors[:8])
                        if not e.errors:
                            for sell_n, order in [
                                (0, "AA"),
                                (0, "AD"),
                                (0, "DA"),
                                (0, "DD"),
                                (1, "AA"),
                                (1, "AD"),
                                (1, "DA"),
                                (1, "DD"),
                                (3, "AA"),
                                (3, "AD"),
                                (3, "DA"),
                                (3, "DD"),
                                (2, "AA"),
                                (2, "AD"),
                                (2, "DA"),
                                (2, "DD"),
                            ]:
                                fast = copy.deepcopy(e)
                                fast = collect_extra_keys(fast)
                                sell(fast, sell_n)
                                buy(fast, order)
                                fast = eat_potions_until(fast, 1050, preserve_yk=1)
                                r37 = to_37_minimal(fast)
                                print("FAST_R37", f"sell={sell_n} order={order}", "ok", not r37.errors, line(r37), "errors", r37.errors[:8])
                                if not r37.errors:
                                    done = quick.extend_after_current_checkpoint_v2(copy.deepcopy(r37))
                                    print("FAST_DONE", f"sell={sell_n} order={order}", "ok", not done.errors, line(done), "errors", done.errors[:8])
                                    if not done.errors:
                                        return 0
                            return 0
                            finish_after_2f(e)
                            return 0
    if best:
        _key, open_order, sell_n, late_order, farm_count, s = best
        print("NO_OK tried", tried)
        print("BEST", open_order, "sell", sell_n, "late", late_order, "farm_count", farm_count, line(s))
        print("errors", s.errors[:8])
    else:
        print("NO_CANDIDATE")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
