#!/usr/bin/env python3
"""Probe guide-shaped zone-3 macro variants from slot26.

The broad slot26 beam can spend too much time around reachable low-floor
resources. This script keeps the strategic spine toward 33F sword, 38F shield,
39F center fly, and 40F boss, then enumerates the early 32F shop / key-sale
timing around that spine.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "scripts" / "plan_zone3_guide_slot36.py"
QUICK = ROOT / "scripts" / "find_zone3_quick_pass_walk.py"
SNAPSHOT = ROOT / "outputs" / "results" / "slot26_snapshot.json"
OUT_JSON = ROOT / "outputs" / "results" / "zone3_slot26_macro_variants.json"
OUT_MD = ROOT / "outputs" / "reports" / "zone3_slot26_macro_variants.md"


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


p = load_module("zone3_plan_macro26", PLAN)
quick = load_module("zone3_quick_macro26", QUICK)


def init() -> Any:
    snapshot = p.read_json(SNAPSHOT)
    enemies = p.load_enemy_stats()
    floors = p.load_floors(snapshot, enemies)
    g = p.GuideReplay(snapshot, floors, enemies)
    g.state["centerFly3"] = False
    return g


def state_line(g: Any) -> str:
    s = g.state
    return (
        f"HP={s['hp']} ATK={s['atk']} DEF={s['def']} "
        f"YK={s['yk']} BK={s['bk']} RK={s['rk']} G={s['gold']} "
        f"{s['floor']} x{s['x']}y{s['y']} dmg={s['dmg']} "
        f"door={s['yd']}/{s['bd']}/{s['rd']} shop={s['times1']}"
    )


def simple_score(g: Any) -> float:
    s = g.state
    return s["hp"] + s["yk"] * 50 + s["bk"] * 200 + s["gold"] * 0.5


def sell_count(g: Any, count: int) -> None:
    if count <= 0:
        return
    g.go_to("MT28", 8, 4, f"28F sell {count} yellow keys")
    for _ in range(count):
        before = g.snapshot()
        if g.state["yk"] <= 0:
            g.error("sell_count yellow keys not enough")
            return
        g.state["yk"] -= 1
        g.state["gold"] += 100
        g.record("merchant", (8, 4), "sellYellowKey", before, "28F sell YK for 100G")


def buy_affordable(g: Any, kind: str, max_count: int) -> int:
    bought = 0
    for _ in range(max_count):
        cost = p.shop_cost(g.state["times1"])
        if g.state["gold"] < cost:
            break
        g.buy_shop(kind, 1)
        bought += 1
    return bought


def prefix(params: dict[str, int]) -> Any:
    g = init()

    g.set_segment("slot26 31F/32F opening")
    g.go_to("MT31", 6, 11, "31F upstairs")
    g.transition("MT32", 6, 11, "31F to 32F")
    g.go_to("MT32", 6, 10, "32F yellowKnight event")
    g.event_mt32_yellow_knight()
    g.go_to("MT32", 8, 11, "32F ghostSoldier before shop")
    g.go_to("MT32", 10, 10, "32F shop")
    buy_affordable(g, "def", params["open_def"])

    g.set_segment("early resources")
    g.fly("MT14")
    for pos in [(4, 5), (6, 5), (8, 5), (1, 11)]:
        g.go_to("MT14", *pos, f"14F early {pos}")
    g.fly("MT16")
    g.go_to("MT16", 11, 7, "16F BK")
    g.fly("MT17")
    for pos in [(9, 8), (11, 8)]:
        g.go_to("MT17", *pos, f"17F lower {pos}")
    g.fly("MT18")
    for pos in [(2, 11), (10, 11)]:
        g.go_to("MT18", *pos, f"18F gem {pos}")

    g.fly("MT28")
    sell_count(g, params["sell_a"])
    g.fly("MT32")
    g.go_to("MT32", 10, 10, "32F mid shop")
    buy_affordable(g, "def", params["mid_def"])

    g.set_segment("right gems and 32F left")
    g.fly("MT14")
    for pos in [(7, 2), (5, 1), (10, 1), (9, 1), (11, 1), (11, 2)]:
        g.go_to("MT14", *pos, f"14F right {pos}")
    g.fly("MT17")
    for pos in [(9, 5), (11, 5), (9, 1), (11, 1), (11, 3)]:
        g.go_to("MT17", *pos, f"17F right {pos}")
    g.fly("MT19")
    g.go_to("MT19", 8, 1, "19F BK")
    g.fly("MT28")
    sell_count(g, params["sell_b"])
    g.fly("MT32")
    g.go_to("MT32", 10, 10, "32F late def shop")
    buy_affordable(g, "def", params["late_def"])
    for pos in [(1, 1), (2, 2)]:
        g.go_to("MT32", *pos, f"32F left gem {pos}")
    g.go_to("MT32", 10, 10, "32F pre-sword atk shop")
    buy_affordable(g, "atk", params["pre_atk"])

    g.set_segment("33F sword")
    g.go_to("MT32", 11, 1, "32F stairs")
    g.transition("MT33", 10, 1, "32F to 33F")
    for pos in [(7, 1), (6, 1), (5, 2), (6, 3), (8, 2), (11, 3), (10, 5)]:
        g.go_to("MT33", *pos, f"33F pre-sword {pos}")
    g.event_mt33_sword_trap()
    for pos in [(9, 5), (11, 5), (9, 7), (11, 7), (10, 10)]:
        g.go_to("MT33", *pos, f"33F sword {pos}")

    g.set_segment("2F reward and attack shops")
    g.fly("MT15")
    g.go_to("MT15", 11, 8, "15F blue potion")
    g.fly("MT2")
    for pos in [(3, 1), (6, 2), (8, 2), (3, 5), (3, 4), (4, 4), (11, 4)]:
        g.go_to("MT2", *pos, f"2F reward {pos}")
    g.oldman_mt2_1000g()
    g.go_to("MT2", 10, 11, "2F thief")
    g.thief_mt2_open_35()
    g.fly("MT28")
    sell_count(g, params["sell_c"])
    g.fly("MT32")
    g.go_to("MT32", 10, 10, "32F atk shop 1")
    buy_affordable(g, "atk", params["atk_a"])
    g.go_to("MT32", 3, 10, "32F blueGuard gold")
    g.go_to("MT32", 10, 10, "32F atk shop 2")
    buy_affordable(g, "atk", params["atk_b"])

    g.set_segment("31F/34F to 37F")
    g.fly("MT31")
    for pos in [(8, 4), (10, 1), (9, 10), (8, 10), (9, 11), (8, 11)]:
        g.go_to("MT31", *pos, f"31F right {pos}")
    g.fly("MT33")
    g.go_to("MT33", 1, 1, "33F to 34F")
    g.transition("MT34", 2, 1, "33F to 34F")
    for pos in [(3, 1), (11, 10), (11, 11), (10, 11), (6, 11)]:
        g.go_to("MT34", *pos, f"34F lower {pos}")
    g.transition("MT35", 6, 11, "34F to 35F")
    g.go_to("MT35", 5, 10, "35F thief")
    g.thief_mt35_depart()
    g.go_to("MT35", 11, 1, "35F to 36F")
    g.transition("MT36", 11, 2, "35F to 36F")
    g.go_to("MT36", 11, 11, "36F to 37F")
    g.transition("MT37", 11, 10, "36F to 37F")
    return g


def run_variant(params: dict[str, int]) -> Any:
    g = prefix(params)
    if g.errors:
        return g
    return quick.extend_after_current_checkpoint_v2(g)


def add_row(rows: list[dict[str, Any]], g: Any, params: dict[str, int]) -> None:
    rows.append(
        {
            "ok": not g.errors,
            "score": simple_score(g),
            "state": g.snapshot(),
            "state_text": state_line(g),
            "params": dict(params),
            "errors": g.errors[:5],
            "steps": g.steps,
        }
    )


def write_outputs(rows: list[dict[str, Any]], tried: int, elapsed: float) -> None:
    rows.sort(key=lambda r: (r["ok"], r["score"], r["state"]["atk"], r["state"]["def"]), reverse=True)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(
        json.dumps({"tried": tried, "elapsed_seconds": elapsed, "rows": rows[:200]}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    lines = ["# slot26 macro variants", "", f"- tried: `{tried}`", f"- elapsed_seconds: `{elapsed:.1f}`", ""]
    for i, row in enumerate(rows[:30], 1):
        lines.append(f"## #{i} {'OK' if row['ok'] else 'FAIL'} score={row['score']}")
        lines.append(f"- params: `{row['params']}`")
        lines.append(f"- state: `{row['state_text']}`")
        if row["errors"]:
            lines.append("- errors: " + " | ".join(row["errors"]))
        lines.append("")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def prune_rows(rows: list[dict[str, Any]], keep: int = 250) -> None:
    if len(rows) <= keep * 2:
        return
    rows.sort(key=lambda r: (r["ok"], r["score"], r["state"]["atk"], r["state"]["def"]), reverse=True)
    del rows[keep:]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-variants", type=int, default=0, help="Stop after this many variants; 0 means no limit.")
    ap.add_argument("--progress-interval", type=int, default=500, help="Print progress every N variants.")
    ns = ap.parse_args()

    rows: list[dict[str, Any]] = []
    tried = 0
    ok_count = 0
    start = time.time()

    for open_def in range(1, 4):
        for mid_def in range(0, 3):
            for late_def in range(0, 3):
                for sell_a in range(0, 3):
                    for sell_b in range(0, 5):
                        for sell_c in range(0, 6):
                            for pre_atk in range(0, 3):
                                for atk_a in range(0, 3):
                                    for atk_b in range(0, 3):
                                        params = {
                                            "open_def": open_def,
                                            "mid_def": mid_def,
                                            "late_def": late_def,
                                            "sell_a": sell_a,
                                            "sell_b": sell_b,
                                            "sell_c": sell_c,
                                            "pre_atk": pre_atk,
                                            "atk_a": atk_a,
                                            "atk_b": atk_b,
                                        }
                                        tried += 1
                                        g = run_variant(params)
                                        if not g.errors:
                                            ok_count += 1
                                        add_row(rows, g, params)
                                        prune_rows(rows)
                                        if ns.progress_interval > 0 and tried % ns.progress_interval == 0:
                                            best = max(
                                                rows,
                                                key=lambda r: (
                                                    r["ok"],
                                                    r["score"],
                                                    r["state"]["atk"],
                                                    r["state"]["def"],
                                                ),
                                            )
                                            print(
                                                f"progress tried={tried} ok={ok_count} "
                                                f"best_ok={best['ok']} score={best['score']} state={best['state_text']} "
                                                f"params={best['params']}",
                                                flush=True,
                                            )
                                        if ns.max_variants and tried >= ns.max_variants:
                                            elapsed = time.time() - start
                                            write_outputs(rows, tried, elapsed)
                                            break
                                    if ns.max_variants and tried >= ns.max_variants:
                                        break
                                if ns.max_variants and tried >= ns.max_variants:
                                    break
                            if ns.max_variants and tried >= ns.max_variants:
                                break
                        if ns.max_variants and tried >= ns.max_variants:
                            break
                    if ns.max_variants and tried >= ns.max_variants:
                        break
                if ns.max_variants and tried >= ns.max_variants:
                    break
            if ns.max_variants and tried >= ns.max_variants:
                break
        if ns.max_variants and tried >= ns.max_variants:
            break

    elapsed = time.time() - start
    write_outputs(rows, tried, elapsed)
    best = max(rows, key=lambda r: (r["ok"], r["score"], r["state"]["atk"], r["state"]["def"]))
    print(f"tried={tried} ok={ok_count}", flush=True)
    print(
        f"best={best['state_text']} params={best['params']} ok={best['ok']} score={best['score']}",
        flush=True,
    )
    print(f"json={OUT_JSON}", flush=True)
    print(f"md={OUT_MD}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
