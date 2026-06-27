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
import sys
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
GUIDED_PATH = ROOT / "scripts" / "search_zone3_slot26_guided.py"
MACRO_PATH = ROOT / "scripts" / "probe_zone3_slot26_sword_macro.py"

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
    seeds.sort(key=base.score, reverse=True)
    return seeds[: args.max_seeds]


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
    parser.add_argument("--report-interval", type=float, default=60)
    parser.add_argument("--progress-log", type=Path, default=OUT_LOG)
    parser.add_argument("--out-json", type=Path, default=OUT_JSON)
    parser.add_argument("--out-md", type=Path, default=OUT_MD)
    parser.add_argument("--daemon-stdout", type=Path, default=None)
    parser.add_argument("--daemon-stderr", type=Path, default=None)
    args = parser.parse_args()
    if args.daemon_stdout:
        args.daemon_stdout.parent.mkdir(parents=True, exist_ok=True)
        sys.stdout = args.daemon_stdout.open("a", encoding="utf-8", buffering=1)
    if args.daemon_stderr:
        args.daemon_stderr.parent.mkdir(parents=True, exist_ok=True)
        sys.stderr = args.daemon_stderr.open("a", encoding="utf-8", buffering=1)
    seeds = build_seeds(args)
    if not seeds:
        print("no legal seeds")
        return 1
    data = explore_from_seeds(args, seeds)
    write_report(data, args.out_json, args.out_md)
    print(f"wrote {args.out_json}")
    print(f"wrote {args.out_md}")
    if data.get("best_goal"):
        print("best_goal", data["best_goal"]["state_text"])
    else:
        print("best_goal not found")
    if data.get("best_any"):
        print("best_any", data["best_any"]["state_text"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
