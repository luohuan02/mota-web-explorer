#!/usr/bin/env python3
"""Debug the slot26 34F center reward timing."""

from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MACRO = ROOT / "scripts" / "probe_zone3_slot26_sword_macro.py"


spec = importlib.util.spec_from_file_location("debug_slot26_macro", MACRO)
if spec is None or spec.loader is None:
    raise RuntimeError(MACRO)
macro = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = macro
spec.loader.exec_module(macro)


def show(label: str, g) -> None:
    print(label, macro.line(g), "errors", g.errors[:10])


def scan_direct_keys(g, title: str, eid: str = "yellowKey") -> None:
    print("SCAN", title)
    rows = []
    for fid, floor in g.floors.items():
        if macro.b.floor_no(fid) > 33:
            continue
        if not macro.b.can_fly_to(g, fid):
            continue
        for (x, y), block in list(floor.blocks.items()):
            if block.kind != "item" or block.eid != eid:
                continue
            cand = macro.try_take(g, fid, x, y, f"scan key {fid} x{x}y{y}")
            if cand is g:
                continue
            rows.append((cand.state["yk"] - g.state["yk"], cand.state["hp"] - g.state["hp"], cand.state["gold"] - g.state["gold"], fid, x, y, macro.line(cand)))
    rows.sort(reverse=True)
    for row in rows[:30]:
        print(" key", row)


def build_after2():
    g = macro.start_to_right_resources("AA")
    macro.sell(g, 2)
    macro.buy(g, "AA")
    s = macro.try_sword(g)
    show("sword", s)
    e = macro.after_sword_to_2f(s)
    show("after2", e)
    return e


def main() -> int:
    base = build_after2()
    extra = macro.collect_extra_keys(base)
    show("extra", extra)
    for sell_n in [0, 1, 2]:
        for order in ["", "A", "D", "AA", "AD", "DA", "DD"]:
            g = copy.deepcopy(extra)
            macro.sell(g, sell_n)
            macro.buy(g, order)
            for hp_target in ([1050, 1800, 2200] if order == "DD" and sell_n == 0 else [1050]):
                h = macro.eat_potions_until(g, hp_target, preserve_yk=1)
                if sell_n == 0 and order == "" and hp_target == 1050:
                    scan_direct_keys(h, "after heal no shop")
                    scan_direct_keys(h, "after heal no shop blue", "blueKey")
                pre34 = macro.collect_pre34_keys(h)
                show(f"pre34 sell={sell_n} order={order} hp={hp_target}", pre34)
                c = macro.to_37_with_34_center(pre34)
                show(f"center sell={sell_n} order={order} hp={hp_target}", c)
                if sell_n == 0 and order == "DD" and hp_target == 2200 and not c.errors:
                    for prep in ["none", "potion", "potionD", "potionA"]:
                        v = copy.deepcopy(c)
                        if "potion" in prep:
                            v = macro.try_take(v, "MT34", 1, 11, "34 left blue potion before 38")
                        if prep.endswith("D"):
                            macro.buy(v, "D")
                        if prep.endswith("A"):
                            macro.buy(v, "A")
                        done = macro.finish_from_37_center(v)
                        show(f"finish center DD hp2200 {prep}", done)
                        if prep == "potionD":
                            for i, step in enumerate(done.steps, 1):
                                if step.get("eid") == "blueDoor":
                                    pos = step.get("pos", ["?", "?"])
                                    delta = f" [{step.get('delta')}]" if step.get("delta") else ""
                                    print(f" blue-step {i}: {step.get('floor')} x{pos[0]}y{pos[1]} {step.get('action')} {step.get('eid')}{delta}")
                            for i, step in enumerate(done.steps[-80:], max(1, len(done.steps) - 79)):
                                if step.get("floor") in {"MT38", "MT39", "MT40"}:
                                    pos = step.get("pos", ["?", "?"])
                                    delta = f" [{step.get('delta')}]" if step.get("delta") else ""
                                    print(f" step {i}: {step.get('floor')} x{pos[0]}y{pos[1]} {step.get('action')} {step.get('eid') or ''}{delta}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
