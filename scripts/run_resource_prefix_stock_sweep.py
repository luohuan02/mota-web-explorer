#!/usr/bin/env python3
"""Run overnight resource-prefix post-9 stock searches.

This script intentionally orchestrates existing search scripts instead of
changing their internals.  It alternates final-stock and net-stock post-9 runs
from the current phase1_resource_group_search best_delayed_shape, and
occasionally refreshes that 4F-9F prefix search.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "outputs" / "results" / "resource_prefix_stock_sweep_summary.json"
OUT_MD = ROOT / "outputs" / "reports" / "resource_prefix_stock_sweep_summary.md"
BASE_FINAL_STOCK = 737
BASE_NET_STOCK = 582


def parse_deadline(value: str) -> datetime:
    if value:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    now = datetime.now()
    tomorrow = now.date() + timedelta(days=1)
    return datetime.combine(tomorrow, datetime.strptime("07:45:00", "%H:%M:%S").time())


def state_text(row: dict[str, Any] | None) -> str:
    if not row:
        return "-"
    return (
        f"HP={row.get('hp')} ATK={row.get('atk')} DEF={row.get('def')} "
        f"YK={row.get('yk')} BK={row.get('bk')} RK={row.get('rk')} "
        f"dmg={row.get('dmg')} door={row.get('yd')}/{row.get('bd')}/{row.get('rd')}"
    )


def run_command(args: list[str], timeout_s: float, label: str) -> dict[str, Any]:
    started = time.time()
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] start {label}", flush=True)
    timed_out = False
    rc: int | None = None
    stdout = ""
    stderr = ""
    try:
        proc = subprocess.run(
            args,
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=max(1, int(timeout_s)),
        )
        rc = proc.returncode
        stdout = proc.stdout
        stderr = proc.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        rc = None
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
    elapsed = time.time() - started
    print(
        f"[{datetime.now():%Y-%m-%d %H:%M:%S}] end {label} "
        f"elapsed={elapsed:.1f}s rc={rc} timeout={timed_out}",
        flush=True,
    )
    if stdout:
        print(stdout[-4000:], flush=True)
    if stderr:
        print(stderr[-4000:], file=sys.stderr, flush=True)
    return {
        "label": label,
        "args": args,
        "elapsed": elapsed,
        "returncode": rc,
        "timed_out": timed_out,
        "stdout_tail": stdout[-4000:],
        "stderr_tail": stderr[-4000:],
        "finished_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def post9_args(tag: str, objective: str) -> list[str]:
    strict_args: list[str]
    if objective == "final-stock":
        strict_args = ["--strict-final-stock-bound", str(BASE_FINAL_STOCK)]
    elif objective == "net-stock":
        strict_args = ["--strict-net-stock-bound", str(BASE_NET_STOCK)]
    else:
        strict_args = []
    return [
        sys.executable,
        "scripts\\post9_gem_supply_search.py",
        "--phase1-source",
        "resource",
        "--output-tag",
        tag,
        "--outer-scheduler",
        "dijkstra",
        "--goal-objective",
        objective,
        *strict_args,
        "--raw-stock-future-door-bound",
        "--net-pocket-raw-stock",
        "--intermediate-dominance-prune",
        "--stat-retry-rounds",
        "4",
        "--stat-deferred-limit",
        "1800",
        "--stat-deferred-resume-limit",
        "72",
        "--stat-deferred-cache",
        f"outputs\\results\\{tag}_stat_live.json",
        "--stat-expansions",
        "48",
        "--stat-goal-grace-expansions",
        "8",
        "--stat-heuristic-unit",
        "160",
        "--stat-cost-lane-period",
        "3",
        "--stat-progress-lane-period",
        "3",
        "--stat-def-lane-period",
        "4",
        "--stat-close-lane-period",
        "4",
        "--stat-close-resume-limit",
        "12",
        "--stat-gem-mask-frontier",
        "--stat-gem-mask-per-bucket",
        "2",
        "--stat-local-refine-passes",
        "2",
        "--stat-local-refine-seeds",
        "1",
        "--stat-local-refine-width",
        "3",
        "--stat-local-refine-window",
        "3",
        "--stat-local-refine-beam",
        "4",
        "--stat-local-refine-trials",
        "10",
        "--stat-local-refine-order-depth",
        "2",
        "--stat-local-refine-jit-supply",
        "--report-every",
        "8",
        "--entry-limit",
        "900",
        "--supply-depth",
        "2",
        "--stat-extra-key-supply-depth",
        "1",
        "--supply-width",
        "8",
        "--supply-targets",
        "14",
        "--supply-edges",
        "6",
        "--backbone-targets",
        "10",
        "--backbone-edges",
        "10",
        "--continue-final",
        "--carry-limit",
        "24",
        "--redkey-rounds",
        "3",
        "--boss-rounds",
        "3",
        "--final-entry-limit",
        "900",
        "--final-source-limit",
        "24",
        "--final-checkpoint-cache",
        f"outputs\\results\\{tag}_final_live.json",
        "--final-checkpoint-cache-limit",
        "1500",
        "--final-edges",
        "22",
        "--final-supply-depth",
        "2",
        "--final-supply-width",
        "12",
        "--final-bridge-depth",
        "3",
        "--final-bridge-width",
        "8",
    ]


def phase1_args(expansions: int) -> list[str]:
    return [
        sys.executable,
        "scripts\\phase1_resource_group_search.py",
        "--max-expansions",
        str(expansions),
        "--scheduler",
        "lanes",
        "--queue-modes",
        "resource,dmg",
    ]


def summarize_post9(tag: str, objective: str, command_row: dict[str, Any]) -> dict[str, Any]:
    path = ROOT / "outputs" / "results" / f"post9_gem_supply_search_{tag}.json"
    data = load_json(path)
    best = data.get("best") if data else None
    strict = data.get("strict_improve") if data else {}
    row = {
        **command_row,
        "kind": "post9",
        "objective": objective,
        "tag": tag,
        "result_path": str(path.relative_to(ROOT)),
        "search_elapsed": data.get("elapsed") if data else None,
        "best": best,
        "best_final_stock": best.get("final_resource_stock") if best else None,
        "best_net_stock": best.get("net_final_stock") if best else None,
        "best_raw_stock": best.get("raw_final_stock") if best else None,
        "best_dmg": best.get("dmg") if best else None,
        "best_hp": best.get("hp") if best else None,
        "final_stock_improvements": strict.get("final_stock_improvements", []),
        "net_stock_improvements": strict.get("net_stock_improvements", []),
    }
    return row


def summarize_phase1(expansions: int, command_row: dict[str, Any]) -> dict[str, Any]:
    path = ROOT / "outputs" / "results" / "phase1_resource_group_search.json"
    data = load_json(path)
    best = data.get("best_delayed_shape") if data else None
    return {
        **command_row,
        "kind": "phase1",
        "expansions": expansions,
        "result_path": str(path.relative_to(ROOT)),
        "best_delayed_shape": best,
        "best_state": state_text(best),
        "best_rg": best.get("resource_group_score") if best else None,
        "best_old": best.get("old_score") if best else None,
        "search_elapsed": data.get("elapsed") if data else None,
        "delayed_shape_count": data.get("delayed_shape_count") if data else None,
        "pareto_count": data.get("pareto_count") if data else None,
    }


def write_summary(summary: dict[str, Any]) -> None:
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    with OUT_JSON.open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    lines = [
        "# Resource Prefix Stock Sweep Summary",
        "",
        f"- started: `{summary['started_at']}`",
        f"- updated: `{summary['updated_at']}`",
        f"- deadline: `{summary['deadline']}`",
        f"- baseline finalStock/netStock: `{BASE_FINAL_STOCK}/{BASE_NET_STOCK}`",
        f"- best finalStock: `{summary.get('best_final_stock')}`",
        f"- best netStock: `{summary.get('best_net_stock')}`",
        f"- first finalStock improvement elapsed: `{summary.get('first_final_improvement_elapsed')}`",
        f"- first netStock improvement elapsed: `{summary.get('first_net_improvement_elapsed')}`",
        "",
        "## Post-9 Runs",
        "",
        "| # | objective | elapsed | search | best | final | net | raw | result |",
        "|---:|---|---:|---:|---|---:|---:|---:|---|",
    ]
    post_rows = [row for row in summary["runs"] if row["kind"] == "post9"]
    for idx, row in enumerate(post_rows, 1):
        lines.append(
            f"| {idx} | {row['objective']} | {row['elapsed']:.1f}s | "
            f"{(row.get('search_elapsed') or 0):.1f}s | "
            f"HP={row.get('best_hp')} dmg={row.get('best_dmg')} | "
            f"{row.get('best_final_stock')} | {row.get('best_net_stock')} | "
            f"{row.get('best_raw_stock')} | `{row['result_path']}` |"
        )
    lines.extend([
        "",
        "## Phase1 Runs",
        "",
        "| # | expansions | elapsed | delayed | pareto | best | rg | old |",
        "|---:|---:|---:|---:|---:|---|---:|---:|",
    ])
    phase_rows = [row for row in summary["runs"] if row["kind"] == "phase1"]
    for idx, row in enumerate(phase_rows, 1):
        lines.append(
            f"| {idx} | {row['expansions']} | {row['elapsed']:.1f}s | "
            f"{row.get('delayed_shape_count')} | {row.get('pareto_count')} | "
            f"{row.get('best_state')} | {row.get('best_rg')} | {row.get('best_old')} |"
        )
    with OUT_MD.open("w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")


def update_bests(summary: dict[str, Any]) -> None:
    best_final = summary.get("best_final_stock")
    best_net = summary.get("best_net_stock")
    start_time = summary["_started_time"]
    for row in summary["runs"]:
        if row["kind"] != "post9":
            continue
        final_stock = row.get("best_final_stock")
        net_stock = row.get("best_net_stock")
        if final_stock is not None and (best_final is None or final_stock > best_final):
            best_final = final_stock
        if net_stock is not None and (best_net is None or net_stock > best_net):
            best_net = net_stock
        if (
            final_stock is not None
            and final_stock > BASE_FINAL_STOCK
            and summary.get("first_final_improvement_elapsed") is None
        ):
            summary["first_final_improvement_elapsed"] = row["_finished_elapsed"]
        if (
            net_stock is not None
            and net_stock > BASE_NET_STOCK
            and summary.get("first_net_improvement_elapsed") is None
        ):
            summary["first_net_improvement_elapsed"] = row["_finished_elapsed"]
    summary["best_final_stock"] = best_final
    summary["best_net_stock"] = best_net
    summary["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    summary["total_elapsed"] = time.time() - start_time


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--deadline", default="")
    parser.add_argument("--reserve-minutes", type=float, default=15.0)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()

    deadline = parse_deadline(args.deadline)
    stop_at = deadline - timedelta(minutes=args.reserve_minutes)
    started = time.time()
    summary: dict[str, Any] = {
        "started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "deadline": deadline.strftime("%Y-%m-%d %H:%M:%S"),
        "stop_at": stop_at.strftime("%Y-%m-%d %H:%M:%S"),
        "runs": [],
        "best_final_stock": None,
        "best_net_stock": None,
        "first_final_improvement_elapsed": None,
        "first_net_improvement_elapsed": None,
        "_started_time": started,
    }

    cycle = 1
    phase1_runs = 0
    while datetime.now() < stop_at:
        remaining = (stop_at - datetime.now()).total_seconds()
        if remaining < 900:
            break

        for objective in ("final-stock", "net-stock"):
            remaining = (stop_at - datetime.now()).total_seconds()
            if remaining < 900:
                break
            tag = f"resource_{objective.replace('-', '')}_overnight_r{cycle}"
            timeout_s = min(remaining - 120, 3600)
            command_row = run_command(post9_args(tag, objective), timeout_s, f"{tag}:{objective}")
            row = summarize_post9(tag, objective, command_row)
            row["_finished_elapsed"] = time.time() - started
            summary["runs"].append(row)
            update_bests(summary)
            write_summary(summary)
            if args.once:
                break
        if args.once:
            break

        remaining = (stop_at - datetime.now()).total_seconds()
        if remaining > 7200:
            phase1_runs += 1
            expansions = 1800 + phase1_runs * 300
            timeout_s = min(remaining - 120, 5400)
            command_row = run_command(
                phase1_args(expansions),
                timeout_s,
                f"phase1_resource:{expansions}",
            )
            row = summarize_phase1(expansions, command_row)
            row["_finished_elapsed"] = time.time() - started
            summary["runs"].append(row)
            update_bests(summary)
            write_summary(summary)
        cycle += 1

    update_bests(summary)
    summary.pop("_started_time", None)
    write_summary(summary)
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(f"wrote {OUT_MD.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
