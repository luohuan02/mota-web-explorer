#!/usr/bin/env python3
"""Incrementally rescore merchant phase1 cache with corrected full-map stock."""

from __future__ import annotations

import argparse
import json
import os
import pickle
import sys
import time
from datetime import datetime
from typing import Any


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
SCRIPTS = os.path.join(ROOT, "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)
os.chdir(ROOT)

from scripts import compare_merchant_resource_paths as cm
from scripts import merchant_finalscore_audit as audit
from src.solver import gen_walkthrough as gw


DEFAULT_STATE_CACHE = os.path.join("outputs", "results", "merchant_phase1_long_search_state.pkl")
DEFAULT_SCORE_CACHE = os.path.join("outputs", "results", "merchant_phase1_corrected_score_cache.pkl")
OUT_JSON = os.path.join("outputs", "results", "merchant_phase1_corrected_rescore.json")
OUT_MD = os.path.join("outputs", "reports", "merchant_phase1_corrected_rescore.md")
SCORE_VERSION = 3


def parse_deadline(text: str | None) -> float | None:
    if not text:
        return None
    return datetime.fromisoformat(text).timestamp()


def fmt_score(value: float) -> str:
    return str(int(value)) if abs(value - int(value)) < 1e-9 else f"{value:.1f}"


def state_line(ent: dict[str, Any]) -> str:
    return (
        f"HP={ent['hp']} ATK={ent['atk']} DEF={ent['def']} "
        f"YK={ent['yk']} BK={ent['bk']} RK={ent['rk']} "
        f"G={cm.inferred_gold(ent, include_boss_spawn=False)} "
        f"dmg={ent.get('_dmg', 0)} door={ent.get('_yd', 0)}/{ent.get('_bd', 0)}/{ent.get('_rd', 0)}"
    )


def load_state_cache(path: str) -> dict[str, Any]:
    with open(path, "rb") as f:
        payload = pickle.load(f)
    gw._entry_store.clear()
    gw._entry_store.update(payload.get("entry_store", {}))
    gw._next_id[0] = payload.get("next_id", gw._next_id[0])
    return payload


def load_score_cache(path: str) -> dict[int, dict[str, Any]]:
    if not os.path.exists(path):
        return {}
    with open(path, "rb") as f:
        payload = pickle.load(f)
    if payload.get("version") != SCORE_VERSION:
        return {}
    return payload.get("scores", {})


def save_score_cache(path: str, scores: dict[int, dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp_path = path + ".tmp"
    with open(tmp_path, "wb") as f:
        pickle.dump(
            {
                "version": SCORE_VERSION,
                "saved_at": datetime.now().isoformat(timespec="seconds"),
                "scores": scores,
            },
            f,
            protocol=pickle.HIGHEST_PROTOCOL,
        )
    os.replace(tmp_path, path)


def score_entry(ent: dict[str, Any], label: str) -> dict[str, Any]:
    row = audit.compact_record(audit.score_record(label, ent, source="corrected phase1 cache rescore"))
    row.pop("remaining_groups", None)
    row["state"] = state_line(ent)
    row["actions"] = cm.trace_actions(ent)
    return row


def write_outputs(data: dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    lines = [
        "# Corrected Merchant Phase1 Rescore",
        "",
        f"- status: `{data['status']}`",
        f"- scored/total: `{data['scored_count']}` / `{data['total_count']}`",
        f"- merchant/plain scored: `{data['merchant_scored']}` / `{data['plain_scored']}`",
        f"- elapsed this run: `{data['elapsed']:.1f}s`",
        f"- state cache expanded/generated/frontier: `{data['state_expanded']}` / `{data['state_generated']}` / `{data['state_frontier']}`",
        "",
        "## Best Scored Goals",
        "",
        "| # | label | state | merchants | futureG | remaining | final-score | actions |",
        "|---:|---|---|---|---:|---:|---:|---|",
    ]
    for idx, row in enumerate(data["top"], 1):
        lines.append(
            f"| {idx} | {row['label']} | {row['state']} | {','.join(row['merchants']) or '-'} | "
            f"{row['future_monster_gold']} | {fmt_score(row['remaining_group_value'])} | "
            f"{fmt_score(row['final_score'])} | {'; '.join(row['actions'])} |"
        )
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")


def run(args: argparse.Namespace) -> dict[str, Any]:
    cm.ensure_merchant_maps()
    cm._FUTURE_BREAKDOWN_CACHE.clear()
    cm._FUTURE_FLOOR_CACHE.clear()
    state_payload = load_state_cache(args.state_cache)
    scores = load_score_cache(args.score_cache)
    merchant_goals = list(state_payload.get("merchant_goals", []))
    plain_goals = list(state_payload.get("plain_goals", []))
    work: list[tuple[str, dict[str, Any]]] = [("merchant", ent) for ent in merchant_goals]
    work.extend(("plain", ent) for ent in plain_goals)
    deadline_ts = parse_deadline(args.deadline)
    run_until_ts = time.time() + args.run_seconds if args.run_seconds else None
    t0 = time.time()
    newly_scored = 0
    status = "complete"

    for label, ent in work:
        now = time.time()
        if deadline_ts is not None and now >= deadline_ts:
            status = "deadline"
            break
        if run_until_ts is not None and now >= run_until_ts:
            status = "paused"
            break
        ent_id = ent.get("_id")
        if ent_id in scores:
            continue
        scores[ent_id] = score_entry(ent, label)
        newly_scored += 1
        if args.save_every and newly_scored % args.save_every == 0:
            save_score_cache(args.score_cache, scores)

    save_score_cache(args.score_cache, scores)
    rows = list(scores.values())
    rows.sort(key=lambda row: (-row["final_score"], row["dmg"], -row["jhp"]))
    merchant_scored = sum(1 for row in rows if row["label"] == "merchant")
    plain_scored = sum(1 for row in rows if row["label"] == "plain")
    data = {
        "status": status,
        "config": vars(args),
        "elapsed": time.time() - t0,
        "newly_scored": newly_scored,
        "scored_count": len(scores),
        "total_count": len(work),
        "merchant_scored": merchant_scored,
        "plain_scored": plain_scored,
        "state_expanded": state_payload.get("expanded"),
        "state_generated": state_payload.get("generated"),
        "state_frontier": len(state_payload.get("heap", [])),
        "top": rows[: args.report_limit],
    }
    write_outputs(data)
    return data


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-cache", default=DEFAULT_STATE_CACHE)
    parser.add_argument("--score-cache", default=DEFAULT_SCORE_CACHE)
    parser.add_argument("--deadline", default=None)
    parser.add_argument("--run-seconds", type=int, default=0)
    parser.add_argument("--report-limit", type=int, default=20)
    parser.add_argument("--save-every", type=int, default=25)
    args = parser.parse_args()
    data = run(args)
    print(
        f"scored={data['scored_count']}/{data['total_count']} "
        f"new={data['newly_scored']} status={data['status']}"
    )
    if data["top"]:
        print(
            f"best={fmt_score(data['top'][0]['final_score'])} "
            f"{data['top'][0]['label']} {data['top'][0]['state']}"
        )


if __name__ == "__main__":
    main()
