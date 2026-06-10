#!/usr/bin/env python3
"""Long-running 4F-9F merchant search with delayed merchant policies."""

from __future__ import annotations

import argparse
import heapq
import json
import os
import pickle
import sys
import time
from collections import defaultdict
from datetime import datetime
from typing import Any, Iterable


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.chdir(ROOT)

from scripts import compare_merchant_resource_paths as cm
from scripts import merchant_finalscore_audit as audit
from scripts import phase1_action_search as p1
from src.solver import gen_walkthrough as gw


OUT_JSON = os.path.join("outputs", "results", "merchant_phase1_long_search.json")
OUT_MD = os.path.join("outputs", "reports", "merchant_phase1_long_search.md")
CACHE_VERSION = 2


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


def merchant_labels(ent: dict[str, Any]) -> tuple[str, ...]:
    return tuple(sorted(m.key for m in cm.MERCHANTS if cm.merchant_used_by_collected(ent, m)))


def search_priority(ent: dict[str, Any]) -> tuple[Any, ...]:
    gold = cm.inferred_gold(ent, include_boss_spawn=False)
    merchants = merchant_labels(ent)
    return (
        cm.rg.resource_group_score(ent) + p1.heuristic(ent) - int(cm.gold_value(gold)),
        -ent.get("_max_floor", 4),
        ent.get("_dmg", 0),
        ent.get("_yd", 0),
        ent.get("_bd", 0),
        len(merchants),
        -ent["yk"],
        -ent["bk"],
        -gold,
        -ent["hp"],
    )


def merchant_allowed(ent: dict[str, Any], merchant: cm.Merchant, args: argparse.Namespace) -> bool:
    if merchant.key == "MT6_BK" and args.delay_bk_merchant:
        # The blue-key merchant is a stock conversion.  Buying it before the
        # shield/gem boundary usually means fighting the access monsters with
        # poor stats.  Keep it only when the branch is actually blue-key-starved
        # or when the 4-9 goal has already been reached.
        if not cm.phase1_done(ent) and ent["bk"] >= args.bk_need_threshold:
            return False
    if merchant.key == "MT7_YK" and args.delay_yk_merchant:
        # The yellow-key merchant can be useful for reachability, but the old
        # schedule bought it with a comfortable key stock.  Delay it unless the
        # branch is close to a yellow-key deficit or is already at the boundary.
        if not cm.phase1_done(ent) and ent["yk"] > args.yk_need_threshold:
            return False
    return True


def action_sort(ent: dict[str, Any], action: tuple[Any, ...]) -> tuple[Any, ...]:
    if action and action[0] == "merchant":
        merchant = cm.MERCHANT_BY_KEY[action[1]]
        if cm.phase1_done(ent):
            bucket = 88
        elif merchant.key == "MT7_YK":
            bucket = 46
        else:
            bucket = 72
        return (bucket, merchant.fid, merchant.key)
    return p1.action_rank(ent, action)


def possible_actions(ent: dict[str, Any], args: argparse.Namespace) -> list[tuple[Any, ...]]:
    actions = list(p1.possible_actions(ent))
    max_floor = ent.get("_max_floor", 4)
    used = set(ent.get("merchant_used", frozenset()))
    for merchant in cm.MERCHANTS:
        if merchant.key in used:
            continue
        if p1.FLOOR_NO[merchant.fid] > max_floor:
            continue
        if not p1.has_item(ent, "MT5", "sword1"):
            continue
        if not merchant_allowed(ent, merchant, args):
            continue
        actions.append(("merchant", merchant.key))
    actions.sort(key=lambda action: action_sort(ent, action))
    return actions[: args.action_limit]


def goal_record(ent: dict[str, Any], label: str) -> dict[str, Any]:
    row = audit.score_record(label, ent, source="long merchant phase1 search")
    out = audit.compact_record(row)
    out["actions"] = cm.trace_actions(ent)
    out["state"] = state_line(ent)
    return out


def top_records(entries: Iterable[dict[str, Any]], label: str, limit: int) -> list[dict[str, Any]]:
    rows = [goal_record(ent, label) for ent in entries]
    rows.sort(key=lambda row: (-row["final_score"], row["dmg"], -row["jhp"]))
    return rows[:limit]


def chain_records(ent: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for item in gw.trace_chain(ent):
        if not item.get("_parent_id"):
            continue
        out.append({
            "action": item.get("_last_action") or str(item.get("_step_info")),
            "hp": item["hp"],
            "atk": item["atk"],
            "def": item["def"],
            "yk": item["yk"],
            "bk": item["bk"],
            "rk": item["rk"],
            "gold": cm.inferred_gold(item, include_boss_spawn=False),
            "dmg": item.get("_dmg", 0),
            "yd": item.get("_yd", 0),
            "bd": item.get("_bd", 0),
            "rd": item.get("_rd", 0),
            "merchants": list(merchant_labels(item)),
        })
    return out


def write_outputs(data: dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    lines = [
        "# Long Merchant Phase1 Search",
        "",
        f"- status: `{data['status']}`",
        f"- elapsed: `{data['elapsed']:.1f}s`",
        f"- expanded/generated/frontier/archive: `{data['expanded']}` / `{data['generated']}` / `{data['frontier']}` / `{data['archive_entries']}`",
        f"- goals merchant/no-merchant: `{data['merchant_goal_count']}` / `{data['plain_goal_count']}`",
        f"- policy: delay_bk=`{data['config']['delay_bk_merchant']}`, delay_yk=`{data['config']['delay_yk_merchant']}`",
        f"- state-cache: `{data['config'].get('state_cache') or '-'}`",
        "",
        "## Baselines",
        "",
        "| route | state | futureG | remaining | final-score |",
        "|---|---|---:|---:|---:|",
    ]
    for row in data["baselines"]:
        lines.append(
            f"| {row['label']} | {row['state']} | {row['future_monster_gold']} | "
            f"{fmt_score(row['remaining_group_value'])} | {fmt_score(row['final_score'])} |"
        )
    lines.extend(["", "## Best Merchant Goals", "", "| # | state | merchants | futureG | remaining | final-score | actions |", "|---:|---|---|---:|---:|---:|---|"])
    for idx, row in enumerate(data["top_merchant"], 1):
        lines.append(
            f"| {idx} | {row['state']} | {','.join(row['merchants']) or '-'} | "
            f"{row['future_monster_gold']} | {fmt_score(row['remaining_group_value'])} | "
            f"{fmt_score(row['final_score'])} | {'; '.join(row['actions'])} |"
        )
    lines.extend(["", "## Best Plain Goals", "", "| # | state | futureG | remaining | final-score | actions |", "|---:|---|---:|---:|---:|---|"])
    for idx, row in enumerate(data["top_plain"], 1):
        lines.append(
            f"| {idx} | {row['state']} | {row['future_monster_gold']} | "
            f"{fmt_score(row['remaining_group_value'])} | {fmt_score(row['final_score'])} | "
            f"{'; '.join(row['actions'])} |"
        )
    if data.get("best_chain"):
        lines.extend(["", "## Best Merchant Chain", ""])
        for idx, row in enumerate(data["best_chain"], 1):
            lines.append(
                f"{idx}. {row['action']} -> HP={row['hp']} ATK={row['atk']} DEF={row['def']} "
                f"YK={row['yk']} BK={row['bk']} RK={row['rk']} G={row['gold']} "
                f"dmg={row['dmg']} door={row['yd']}/{row['bd']}/{row['rd']} "
                f"merchants={','.join(row['merchants']) or '-'}"
            )
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")


def save_state_cache(
    *,
    args: argparse.Namespace,
    t0: float,
    expanded: int,
    generated: int,
    seq: int,
    heap: list[tuple[Any, int, dict[str, Any]]],
    merchant_heap: list[tuple[Any, int, dict[str, Any]]],
    archive: dict[tuple[Any, ...], list[dict[str, Any]]],
    expanded_ids: set[int],
    seen_goal_ids: set[int],
    merchant_goals: list[dict[str, Any]],
    plain_goals: list[dict[str, Any]],
) -> None:
    if not args.state_cache:
        return
    os.makedirs(os.path.dirname(args.state_cache), exist_ok=True)
    payload = {
        "version": CACHE_VERSION,
        "saved_at": datetime.now().isoformat(timespec="seconds"),
        "elapsed": time.time() - t0,
        "expanded": expanded,
        "generated": generated,
        "seq": seq,
        "heap": heap,
        "merchant_heap": merchant_heap,
        "archive": dict(archive),
        "expanded_ids": expanded_ids,
        "seen_goal_ids": seen_goal_ids,
        "merchant_goals": merchant_goals,
        "plain_goals": plain_goals,
        "entry_store": gw._entry_store,
        "next_id": gw._next_id[0],
    }
    tmp_path = args.state_cache + ".tmp"
    with open(tmp_path, "wb") as f:
        pickle.dump(payload, f, protocol=pickle.HIGHEST_PROTOCOL)
    os.replace(tmp_path, args.state_cache)


def load_state_cache(args: argparse.Namespace) -> dict[str, Any] | None:
    if args.fresh or not args.state_cache or not os.path.exists(args.state_cache):
        return None
    with open(args.state_cache, "rb") as f:
        payload = pickle.load(f)
    if payload.get("version") != CACHE_VERSION:
        raise ValueError(f"unsupported state cache version: {payload.get('version')}")
    gw._entry_store.clear()
    gw._entry_store.update(payload.get("entry_store", {}))
    gw._next_id[0] = payload.get("next_id", gw._next_id[0])
    heapq.heapify(payload["heap"])
    heapq.heapify(payload["merchant_heap"])
    payload["archive"] = defaultdict(list, payload["archive"])
    return payload


def checkpoint(
    *,
    args: argparse.Namespace,
    status: str,
    t0: float,
    expanded: int,
    generated: int,
    heap: list[tuple[Any, int, dict[str, Any]]],
    archive: dict[tuple[Any, ...], list[dict[str, Any]]],
    merchant_goals: list[dict[str, Any]],
    plain_goals: list[dict[str, Any]],
    baselines: list[dict[str, Any]],
) -> None:
    if args.report_limit <= 0:
        top_merchant = []
        top_plain = []
        best_ent = None
    else:
        top_merchant = top_records(merchant_goals, "merchant", args.report_limit)
        top_plain = top_records(plain_goals, "plain", min(6, args.report_limit))
        best_ent = None
        if merchant_goals:
            best_ent = max(
                merchant_goals,
                key=lambda ent: (cm.final_stock_with_gold(ent), -ent.get("_dmg", 0), ent["hp"]),
            )
    data = {
        "status": status,
        "config": vars(args),
        "elapsed": time.time() - t0,
        "expanded": expanded,
        "generated": generated,
        "frontier": len(heap),
        "archive_entries": sum(len(v) for v in archive.values()),
        "merchant_goal_count": len(merchant_goals),
        "plain_goal_count": len(plain_goals),
        "baselines": baselines,
        "top_merchant": top_merchant,
        "top_plain": top_plain,
        "best_chain": chain_records(best_ent) if best_ent else [],
    }
    write_outputs(data)
    if top_merchant:
        print(
            f"[{datetime.now().strftime('%H:%M:%S')}] expanded={expanded} "
            f"merchant_goals={len(merchant_goals)} best={fmt_score(top_merchant[0]['final_score'])} "
            f"{top_merchant[0]['state']}",
            flush=True,
        )
    else:
        print(
            f"[{datetime.now().strftime('%H:%M:%S')}] expanded={expanded} "
            f"merchant_goals=0 frontier={len(heap)}",
            flush=True,
        )


def build_baselines() -> list[dict[str, Any]]:
    fixed = audit.ent_from_fixed_prefix()
    rows = [
        audit.score_record("guide", fixed, source="fixed guide 4-9"),
    ]
    try:
        delayed, _boss = audit.replay_delayed_walk()
    except FileNotFoundError as exc:
        print(f"warning: delayed baseline skipped: {exc}", flush=True)
    else:
        rows.append(audit.score_record("delayed", delayed, source="known delayed 4-9"))
    out = []
    for row in rows:
        compact = audit.compact_record(row)
        compact["state"] = state_line(row["ent"])
        out.append(compact)
    return out


def run(args: argparse.Namespace) -> None:
    cm.ensure_merchant_maps()
    deadline_ts = parse_deadline(args.deadline)
    loaded = load_state_cache(args)
    if loaded:
        archive = loaded["archive"]
        heap = loaded["heap"]
        merchant_heap = loaded["merchant_heap"]
        expanded_ids = loaded["expanded_ids"]
        seq = loaded["seq"]
        merchant_goals = loaded["merchant_goals"]
        plain_goals = loaded["plain_goals"]
        seen_goal_ids = loaded["seen_goal_ids"]
        generated = loaded["generated"]
        expanded = loaded["expanded"]
        t0 = time.time() - loaded.get("elapsed", 0.0)
    else:
        start = cm.initial_phase1_state(args.start_gold)
        archive: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
        heap: list[tuple[Any, int, dict[str, Any]]] = []
        merchant_heap: list[tuple[Any, int, dict[str, Any]]] = []
        expanded_ids: set[int] = set()
        seq = 0
        heapq.heappush(heap, (search_priority(start), seq, start))
        cm.add_to_archive(archive, start)
        merchant_goals: list[dict[str, Any]] = []
        plain_goals: list[dict[str, Any]] = []
        seen_goal_ids: set[int] = set()
        generated = 0
        expanded = 0
        t0 = time.time()
    last_checkpoint = time.time()
    run_until_ts = time.time() + args.run_seconds if args.run_seconds else None
    baselines = build_baselines()

    def push_frontier(ent: dict[str, Any]) -> None:
        key = search_priority(ent)
        heapq.heappush(heap, (key, seq, ent))
        if merchant_labels(ent):
            heapq.heappush(merchant_heap, (key, seq, ent))

    def pop_frontier() -> dict[str, Any] | None:
        use_merchant_lane = (
            args.merchant_lane_period
            and expanded > 0
            and expanded % args.merchant_lane_period == 0
        )
        heaps = (merchant_heap, heap) if use_merchant_lane else (heap, merchant_heap)
        for selected_heap in heaps:
            while selected_heap:
                _key, _seq, candidate = heapq.heappop(selected_heap)
                cid = candidate.get("_id", id(candidate))
                if cid not in expanded_ids:
                    return candidate
        return None

    while heap or merchant_heap:
        now = time.time()
        if args.max_expansions and expanded >= args.max_expansions:
            break
        if deadline_ts is not None and now >= deadline_ts:
            break
        if run_until_ts is not None and now >= run_until_ts:
            break
        ent = pop_frontier()
        if ent is None:
            break
        expanded_ids.add(ent.get("_id", id(ent)))
        expanded += 1
        if cm.phase1_done(ent):
            gid = ent.get("_id")
            if gid not in seen_goal_ids:
                seen_goal_ids.add(gid)
                if merchant_labels(ent):
                    merchant_goals.append(ent)
                elif args.keep_plain_goals:
                    plain_goals.append(ent)
        for action in possible_actions(ent, args):
            for nxt in cm.expand_action(ent, action):
                generated += 1
                if not cm.add_to_archive(archive, nxt):
                    continue
                seq += 1
                push_frontier(nxt)

        if expanded % args.checkpoint_expansions == 0 or (time.time() - last_checkpoint) >= args.checkpoint_seconds:
            save_state_cache(
                args=args,
                t0=t0,
                expanded=expanded,
                generated=generated,
                seq=seq,
                heap=heap,
                merchant_heap=merchant_heap,
                archive=archive,
                expanded_ids=expanded_ids,
                seen_goal_ids=seen_goal_ids,
                merchant_goals=merchant_goals,
                plain_goals=plain_goals,
            )
            checkpoint(
                args=args,
                status="running",
                t0=t0,
                expanded=expanded,
                generated=generated,
                heap=heap,
                archive=archive,
                merchant_goals=merchant_goals,
                plain_goals=plain_goals,
                baselines=baselines,
            )
            last_checkpoint = time.time()

    now = time.time()
    if not heap and not merchant_heap:
        status = "complete"
    elif deadline_ts is not None and now >= deadline_ts:
        status = "deadline"
    elif args.max_expansions and expanded >= args.max_expansions:
        status = "max-expansions"
    else:
        status = "paused"
    save_state_cache(
        args=args,
        t0=t0,
        expanded=expanded,
        generated=generated,
        seq=seq,
        heap=heap,
        merchant_heap=merchant_heap,
        archive=archive,
        expanded_ids=expanded_ids,
        seen_goal_ids=seen_goal_ids,
        merchant_goals=merchant_goals,
        plain_goals=plain_goals,
    )
    checkpoint(
        args=args,
        status=status,
        t0=t0,
        expanded=expanded,
        generated=generated,
        heap=heap,
        archive=archive,
        merchant_goals=merchant_goals,
        plain_goals=plain_goals,
        baselines=baselines,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--deadline", default=None, help="Local ISO timestamp, e.g. 2026-06-08T06:55:00")
    parser.add_argument("--max-expansions", type=int, default=0)
    parser.add_argument("--run-seconds", type=int, default=0)
    parser.add_argument("--start-gold", type=int, default=cm.DEFAULT_START_GOLD)
    parser.add_argument("--report-limit", type=int, default=16)
    parser.add_argument("--action-limit", type=int, default=16)
    parser.add_argument("--checkpoint-expansions", type=int, default=25)
    parser.add_argument("--checkpoint-seconds", type=int, default=900)
    parser.add_argument("--delay-bk-merchant", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--delay-yk-merchant", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--bk-need-threshold", type=int, default=1)
    parser.add_argument("--yk-need-threshold", type=int, default=2)
    parser.add_argument("--merchant-lane-period", type=int, default=6)
    parser.add_argument("--state-cache", default=os.path.join("outputs", "results", "merchant_phase1_long_search_state.pkl"))
    parser.add_argument("--fresh", action="store_true")
    parser.add_argument("--keep-plain-goals", action=argparse.BooleanOptionalAction, default=True)
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
