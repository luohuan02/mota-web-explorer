#!/usr/bin/env python3
"""Run post-9 merchant-aware searches from selected 4F-9F seeds."""

from __future__ import annotations

import argparse
import json
import os
import pickle
import sys
import time
from typing import Any


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.chdir(ROOT)

from scripts import compare_merchant_resource_paths as cm
from scripts import merchant_finalscore_audit as audit
from scripts import post9_resource_group_search as rg
from src.solver import gen_walkthrough as gw


OUT_JSON = os.path.join("outputs", "results", "post9_merchant_seed_search.json")
OUT_MD = os.path.join("outputs", "reports", "post9_merchant_seed_search.md")
DEFAULT_LONG_CACHE = os.path.join("outputs", "results", "merchant_phase1_long_search_state.pkl")


def fmt_score(value: float) -> str:
    return str(int(value)) if abs(value - int(value)) < 1e-9 else f"{value:.1f}"


def state_text(ent: dict[str, Any] | None) -> str:
    if ent is None:
        return "-"
    return (
        f"HP={ent['hp']} ATK={ent['atk']} DEF={ent['def']} "
        f"YK={ent['yk']} BK={ent['bk']} RK={ent['rk']} "
        f"G={cm.inferred_gold(ent)} dmg={ent.get('_dmg', 0)} "
        f"door={ent.get('_yd', 0)}/{ent.get('_bd', 0)}/{ent.get('_rd', 0)}"
    )


def merchant_labels(ent: dict[str, Any] | None) -> list[str]:
    if ent is None:
        return []
    return list(audit.selected_merchant_labels(ent))


def score_compact(label: str, ent: dict[str, Any] | None, source: str) -> dict[str, Any] | None:
    if ent is None:
        return None
    return audit.compact_record(audit.score_record(label, ent, source=source))


def load_long_merchant_seeds(path: str, limit: int) -> list[dict[str, Any]]:
    if limit <= 0 or not os.path.exists(path):
        return []
    with open(path, "rb") as f:
        payload = pickle.load(f)
    if "entry_store" in payload:
        gw._entry_store.clear()
        gw._entry_store.update(payload["entry_store"])
        gw._next_id[0] = payload.get("next_id", gw._next_id[0])
    goals = list(payload.get("merchant_goals", []))
    goals.sort(key=lambda ent: (-cm.final_stock_with_gold(ent), ent.get("_dmg", 0), -ent["hp"]))
    seeds: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    for ent in goals:
        sig = audit.state_signature(ent)
        if sig in seen:
            continue
        seen.add(sig)
        ent = dict(ent)
        ent["_seed_source"] = "4-9 merchant long-search best"
        seeds.append(ent)
        if len(seeds) >= limit:
            break
    return seeds


def build_seeds(args: argparse.Namespace) -> list[dict[str, Any]]:
    fixed = audit.ent_from_fixed_prefix()
    fixed["_seed_source"] = "guide 4-9 no merchant"
    delayed, _delayed_boss = audit.replay_delayed_walk()
    delayed["_seed_source"] = "delayed 4-9 no merchant"
    seeds = [fixed, delayed]
    seeds.extend(load_long_merchant_seeds(args.long_cache, args.merchant_phase1_seeds))
    if args.seed_filter != "all":
        seeds = [seed for seed in seeds if seed.get("_seed_source", "").startswith(args.seed_filter)]
    return seeds


def run_post9_from_seed(
    seed_ent: dict[str, Any],
    *,
    stat_rounds: int,
    redkey_rounds: int,
    boss_rounds: int,
    entry_limit: int,
    source_limit: int,
) -> dict[str, Any]:
    audit.install_post9_resource_group_hooks()
    seed = audit.seed_for_post9(seed_ent)
    t0 = time.time()
    merchant_actions = [("merchant", merchant.key) for merchant in cm.MERCHANTS]
    stat_entries, stat_rows = rg.base.run_stage(
        "stat27",
        [seed],
        list(rg.STAT_ACTIONS) + merchant_actions,
        rg.base.stat_goal,
        stat_rounds,
        entry_limit,
        source_limit,
    )
    redkey_entries, redkey_rows = rg.base.run_stage(
        "redkey",
        stat_entries,
        list(rg.base.REDKEY_ACTIONS) + merchant_actions,
        rg.base.redkey_goal,
        redkey_rounds,
        entry_limit,
        source_limit,
    )
    final_entries, boss_rows = rg.base.run_stage(
        "boss",
        redkey_entries,
        list(rg.base.BOSS_PREP_ACTIONS) + merchant_actions,
        rg.base.goal,
        boss_rounds,
        entry_limit,
        source_limit,
        include_boss=True,
    )
    jit = run_jit_supply_lanes(seed, beam=max(120, source_limit * 3))
    order_beam = run_order_beam_lanes(seed, beam=max(160, source_limit * 4))
    goals = [ent for ent in final_entries if rg.base.goal(ent)]
    goals.extend(jit["boss_goals"])
    goals.extend(order_beam["boss_goals"])
    goals.sort(key=lambda ent: (-cm.final_stock_with_gold(ent), ent.get("_dmg", 0), -ent["hp"]))
    merchant_goals = [ent for ent in goals if audit.selected_merchant_labels(ent)]
    return {
        "elapsed": time.time() - t0,
        "goal_count": len(goals),
        "merchant_goal_count": len(merchant_goals),
        "entry_count": len(final_entries),
        "rounds": stat_rows + redkey_rows + boss_rows,
        "best_ent": goals[0] if goals else None,
        "best_merchant_ent": merchant_goals[0] if merchant_goals else None,
        "top_ents": goals[:8],
        "top_merchant_ents": merchant_goals[:8],
        "jit_lanes": jit["rows"] + order_beam["rows"],
    }


STAT_TARGETS = {"redGem", "blueGem"}
SUPPLY_TARGETS = {"yellowKey", "blueKey", "upFloor"}


def unique_actions(actions: list[tuple[str, str]]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for action in actions:
        if action in seen:
            continue
        seen.add(action)
        out.append(action)
    return out


def real_fid(fid: str) -> str:
    return rg.special_real_fid(fid) if hasattr(rg, "special_real_fid") else fid


def action_prefix(ent: dict[str, Any], depth: int = 2) -> tuple[str, ...]:
    cached = ent.get(f"_jit_action_prefix_{depth}")
    if cached is not None:
        return tuple(cached)
    actions = tuple(cm.trace_actions(ent)[:depth])
    ent[f"_jit_action_prefix_{depth}"] = actions
    return actions


def gem_signature(ent: dict[str, Any]) -> tuple[tuple[str, tuple[int, int], str], ...]:
    cached = ent.get("_jit_gem_signature")
    if cached is not None:
        return tuple(cached)
    sig: list[tuple[str, tuple[int, int], str]] = []
    for fid, positions in ent.get("collected", {}).items():
        for pos in positions:
            eid = cm.pos_eid(fid, pos)
            if eid in STAT_TARGETS:
                sig.append((fid, tuple(pos), eid))
    value = tuple(sorted(sig))
    ent["_jit_gem_signature"] = value
    return value


JIT_STAT_ACTIONS: tuple[tuple[str, str], ...] = tuple(unique_actions([
    action for action in rg.STAT_ACTIONS
    if action[1] in STAT_TARGETS and real_fid(action[0]) != "MT10"
]))

JIT_SUPPLY_ACTIONS: tuple[tuple[str, str], ...] = tuple(unique_actions([
    action for action in rg.STAT_ACTIONS
    if action[1] in SUPPLY_TARGETS
]))


def jit_trim(entries: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    if not entries:
        return []
    trimmed = rg.trim_entries(entries, max(limit, min(len(entries), limit * 2)))
    out: list[dict[str, Any]] = []
    seen: set[int] = set()

    def add(items: list[dict[str, Any]], quota: int) -> None:
        added = 0
        for ent in items:
            eid = ent.get("_id")
            if eid in seen:
                continue
            seen.add(eid)
            out.append(ent)
            added += 1
            if len(out) >= limit or added >= quota:
                return

    def add_bucketed(key_fn, quota: int, per_bucket: int = 1) -> None:
        groups: dict[Any, list[dict[str, Any]]] = {}
        for ent in trimmed:
            groups.setdefault(key_fn(ent), []).append(ent)
        added = 0
        for bucket in groups.values():
            bucket_picks: list[dict[str, Any]] = []
            for selector in (
                rg.jit_def_before_supply_rank,
                lambda ent: (-cm.final_stock_with_gold(ent), ent.get("_dmg", 0), -ent["hp"]),
                lambda ent: (ent.get("_dmg", 0), ent.get("_yd", 0), ent.get("_bd", 0), -ent["hp"]),
            ):
                for ent in sorted(bucket, key=selector):
                    if ent in bucket_picks:
                        continue
                    bucket_picks.append(ent)
                    break
                if len(bucket_picks) >= per_bucket:
                    break
            before = len(out)
            add(bucket_picks, per_bucket)
            added += len(out) - before
            if len(out) >= limit or added >= quota:
                return

    add_bucketed(lambda ent: action_prefix(ent, 1), max(16, limit // 5), per_bucket=2)
    add_bucketed(lambda ent: action_prefix(ent, 2), max(16, limit // 5), per_bucket=1)
    add_bucketed(gem_signature, max(24, limit // 4), per_bucket=1)

    pools = [
        sorted(trimmed, key=lambda ent: (-cm.final_stock_with_gold(ent), ent.get("_dmg", 0), -ent["hp"])),
        sorted(trimmed, key=rg.jit_def_before_supply_rank),
        sorted(trimmed, key=rg.stat_balance_rank),
        sorted(trimmed, key=lambda ent: (ent.get("_dmg", 0), ent.get("_yd", 0), ent.get("_bd", 0), -ent["hp"])),
        sorted(trimmed, key=lambda ent: (max(0, 27 - ent["def"]), -ent["def"], ent.get("_dmg", 0), -ent["hp"])),
        sorted(trimmed, key=lambda ent: (max(0, 27 - ent["atk"]), -ent["atk"], ent.get("_dmg", 0), -ent["hp"])),
        sorted(trimmed, key=lambda ent: (-ent["yk"], -ent["bk"], ent.get("_dmg", 0), -ent["hp"])),
    ]
    for pool in pools:
        add(pool, limit)
        if len(out) >= limit:
            return out
    return out


def expand_action_set(
    entries: list[dict[str, Any]],
    action_specs: list[tuple[str, str]] | tuple[tuple[str, str], ...],
    *,
    source_limit: int,
) -> tuple[list[dict[str, Any]], list[tuple[str, int, int]]]:
    generated: list[dict[str, Any]] = []
    counts: list[tuple[str, int, int]] = []
    for fid, target in action_specs:
        sources = audit.merchant_aware_select_sources(entries, fid, target, source_limit)
        if not sources:
            continue
        before = len(generated)
        for ent in sources:
            generated.extend(audit.merchant_aware_apply_action(ent, fid, target))
        gained = len(generated) - before
        if gained:
            counts.append((f"{fid}:{target}", len(sources), gained))
    return generated, counts


def run_jit_supply_lanes(seed: dict[str, Any], beam: int = 120) -> dict[str, Any]:
    """Run generic JIT-supply refinement alongside the broad scheduler.

    The lane is deliberately not a fixed route.  It first explores reachable
    stat actions, keeping representatives that raise DEF/ATK cheaply, then
    tries key/up-floor supply packages from those later stat states.  Normal
    stage search completes the route afterward.
    """
    entries = [seed]
    rows: list[dict[str, Any]] = []
    source_limit = max(8, beam // 8)

    for round_no in range(1, 4):
        generated, counts = expand_action_set(entries, JIT_STAT_ACTIONS, source_limit=source_limit)
        if not generated:
            break
        entries = jit_trim(entries + generated, beam)
        rows.append({
            "lane": "jit-supply",
            "step": f"stat-warmup-{round_no}",
            "kept": len(entries),
            "best": state_text(entries[0]) if entries else None,
            "actions": counts[:8],
        })
        if not entries:
            break

    for round_no in range(1, 3):
        generated, counts = expand_action_set(entries, JIT_SUPPLY_ACTIONS, source_limit=source_limit)
        if not generated:
            break
        entries = jit_trim(generated, beam)
        rows.append({
            "lane": "jit-supply",
            "step": f"supply-after-stats-{round_no}",
            "kept": len(entries),
            "best": state_text(entries[0]) if entries else None,
            "actions": counts[:8],
        })

    merchant_actions = [("merchant", merchant.key) for merchant in cm.MERCHANTS]
    completion_entry_limit = max(beam, 160)
    completion_source_limit = max(12, beam // 6)
    stat_entries, stat_rows = rg.base.run_stage(
        "jit-stat27",
        entries,
        list(rg.STAT_ACTIONS) + merchant_actions,
        rg.base.stat_goal,
        8,
        completion_entry_limit,
        completion_source_limit,
    )
    redkey_entries, redkey_rows = rg.base.run_stage(
        "jit-redkey",
        stat_entries,
        list(rg.base.REDKEY_ACTIONS) + merchant_actions,
        rg.base.redkey_goal,
        3,
        completion_entry_limit,
        completion_source_limit,
    )
    final_entries, boss_rows = rg.base.run_stage(
        "jit-boss",
        redkey_entries,
        list(rg.base.BOSS_PREP_ACTIONS) + merchant_actions,
        rg.base.goal,
        3,
        completion_entry_limit,
        completion_source_limit,
        include_boss=True,
    )
    for row in stat_rows + redkey_rows + boss_rows:
        best = row.get("best_goal")
        rows.append({
            "lane": "jit-supply",
            "step": f"{row['stage']}-{row['round']}",
            "kept": row["entries"],
            "best": None if best is None else (
                f"HP={best['hp']} ATK={best['atk']} DEF={best['def']} "
                f"YK={best['yk']} BK={best['bk']} RK={best['rk']} "
                f"dmg={best['dmg']} door={best['yd']}/{best['bd']}/{best['rd']}"
            ),
            "actions": row.get("actions", [])[:8],
        })

    boss_goals = [ent for ent in final_entries if rg.base.goal(ent)]
    boss_goals.sort(key=lambda ent: (-cm.final_stock_with_gold(ent), ent.get("_dmg", 0), -ent["hp"]))
    return {"boss_goals": boss_goals[:beam], "rows": rows}


def order_beam_actions(entries: list[dict[str, Any]]) -> list[tuple[str, str]]:
    actions: list[tuple[str, str]] = []
    if any(ent["atk"] < 27 or ent["def"] < 27 for ent in entries):
        actions.extend(rg.STAT_ACTIONS)
    if any(ent["atk"] >= 27 and ent["def"] >= 27 and ent["rk"] < 1 for ent in entries):
        actions.extend(rg.base.REDKEY_ACTIONS)
    if any(ent["atk"] >= 27 and ent["def"] >= 27 and ent["rk"] >= 1 for ent in entries):
        actions.extend(rg.base.BOSS_PREP_ACTIONS)
    actions.extend(("merchant", merchant.key) for merchant in cm.MERCHANTS)
    return unique_actions(actions)


def boss_goal_variants(entries: list[dict[str, Any]], source_limit: int, beam: int) -> list[dict[str, Any]]:
    pool = [
        ent for ent in entries
        if ent["atk"] >= 27 and ent["def"] >= 27 and ent["rk"] >= 1
    ]
    if not pool:
        return []
    sources: list[dict[str, Any]] = []
    seen: set[int] = set()
    selectors = [
        lambda ent: (rg.base.boss_survival_deficit(ent), ent.get("_dmg", 0), ent.get("_yd", 0), -ent["hp"]),
        lambda ent: (-cm.final_stock_with_gold(ent), ent.get("_dmg", 0), -ent["hp"]),
        lambda ent: (-ent["yk"], -ent["bk"], ent.get("_dmg", 0), -ent["hp"]),
    ]
    for selector in selectors:
        for ent in sorted(pool, key=selector)[:source_limit]:
            eid = ent.get("_id")
            if eid in seen:
                continue
            seen.add(eid)
            sources.append(ent)
    goals: list[dict[str, Any]] = []
    for ent in sources:
        goals.extend(audit.annotate_money(item) for item in rg.base.boss_action(ent))
    goals = [ent for ent in goals if rg.base.goal(ent)]
    goals.sort(key=lambda ent: (-cm.final_stock_with_gold(ent), ent.get("_dmg", 0), -ent["hp"]))
    return goals[:beam]


def run_order_beam_lanes(seed: dict[str, Any], beam: int = 160, max_depth: int = 20) -> dict[str, Any]:
    """Generic action-order beam for local sequence refinement.

    Unlike the old MT7-first lane, this does not prescribe a route.  It keeps a
    compact set of action-order representatives while trying every currently
    legal stat/supply/potion action, so useful swaps such as "DEF before key
    pocket" can survive to the boss check.
    """
    entries = [seed]
    rows: list[dict[str, Any]] = []
    boss_goals: list[dict[str, Any]] = []
    source_limit = max(10, beam // 10)

    for depth in range(1, max_depth + 1):
        actions = order_beam_actions(entries)
        generated, counts = expand_action_set(entries, actions, source_limit=source_limit)
        if not generated:
            break
        entries = jit_trim(entries + generated, beam)
        new_goals = boss_goal_variants(entries, source_limit=max(8, source_limit // 2), beam=beam)
        if new_goals:
            boss_goals.extend(new_goals)
            boss_goals = jit_trim(boss_goals, beam)
        best_goal = boss_goals[0] if boss_goals else None
        rows.append({
            "lane": "order-beam",
            "step": f"depth-{depth}",
            "kept": len(entries),
            "best": state_text(best_goal) if best_goal else state_text(entries[0]) if entries else None,
            "actions": counts[:8],
            "boss_goals": len(boss_goals),
        })

    boss_goals = [ent for ent in boss_goals if rg.base.goal(ent)]
    boss_goals.sort(key=lambda ent: (-cm.final_stock_with_gold(ent), ent.get("_dmg", 0), -ent["hp"]))
    return {"boss_goals": boss_goals[:beam], "rows": rows}


def run(args: argparse.Namespace) -> dict[str, Any]:
    cm.ensure_merchant_maps()
    seeds = build_seeds(args)
    rows: list[dict[str, Any]] = []
    best_any: dict[str, Any] | None = None
    best_merchant: dict[str, Any] | None = None
    t0 = time.time()

    for idx, seed in enumerate(seeds, 1):
        run_result = run_post9_from_seed(
            seed,
            stat_rounds=args.stat_rounds,
            redkey_rounds=args.redkey_rounds,
            boss_rounds=args.boss_rounds,
            entry_limit=args.entry_limit,
            source_limit=args.source_limit,
        )
        any_ent = run_result["best_ent"]
        merchant_ent = run_result["best_merchant_ent"]
        row = {
            "seed_rank": idx,
            "seed_source": seed.get("_seed_source", f"seed {idx}"),
            "seed": score_compact("seed", seed, seed.get("_seed_source", "seed")),
            "elapsed": run_result["elapsed"],
            "goal_count": run_result["goal_count"],
            "merchant_goal_count": run_result["merchant_goal_count"],
            "entry_count": run_result["entry_count"],
            "best_any": score_compact("best_any", any_ent, seed.get("_seed_source", "seed")),
            "best_merchant": score_compact("best_merchant", merchant_ent, seed.get("_seed_source", "seed")),
        }
        rows.append(row)
        if any_ent is not None and (
            best_any is None
            or cm.final_stock_with_gold(any_ent) > cm.final_stock_with_gold(best_any["ent"])
        ):
            best_any = {"seed_rank": idx, "ent": any_ent}
        if merchant_ent is not None and (
            best_merchant is None
            or cm.final_stock_with_gold(merchant_ent) > cm.final_stock_with_gold(best_merchant["ent"])
        ):
            best_merchant = {"seed_rank": idx, "ent": merchant_ent}

    _delayed_phase1, delayed_boss = audit.replay_delayed_walk()
    guide_boss = cm.guide_full_ent()
    boss_compare_rows = [
        audit.score_record("guide", guide_boss, source="guide boss baseline"),
        audit.score_record("delayed", delayed_boss, source="delayed boss baseline"),
    ]
    if best_merchant is not None:
        boss_compare_rows.insert(
            0,
            audit.score_record(
                "best_merchant",
                best_merchant["ent"],
                source=f"post9 merchant seed #{best_merchant['seed_rank']}",
            ),
        )
    if best_any is not None:
        boss_compare_rows.insert(
            0,
            audit.score_record(
                "best_any",
                best_any["ent"],
                source=f"post9 any seed #{best_any['seed_rank']}",
            ),
        )

    return {
        "config": vars(args),
        "elapsed": time.time() - t0,
        "seed_runs": rows,
        "best_any_seed_rank": None if best_any is None else best_any["seed_rank"],
        "best_merchant_seed_rank": None if best_merchant is None else best_merchant["seed_rank"],
        "boss_compare": [audit.compact_record(row) for row in boss_compare_rows],
        "boss_diff_groups": audit.group_diff(boss_compare_rows),
    }


def write_outputs(data: dict[str, Any]) -> None:
    tag = data["config"].get("output_tag")
    out_json = OUT_JSON if not tag else os.path.join("outputs", "results", f"post9_merchant_seed_search_{tag}.json")
    out_md = OUT_MD if not tag else os.path.join("outputs", "reports", f"post9_merchant_seed_search_{tag}.md")
    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    os.makedirs(os.path.dirname(out_md), exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    lines = [
        "# Post9 Merchant Seed Search",
        "",
        f"- elapsed: `{data['elapsed']:.1f}s`",
        f"- rounds stat/redkey/boss: `{data['config']['stat_rounds']}` / `{data['config']['redkey_rounds']}` / `{data['config']['boss_rounds']}`",
        f"- entry/source: `{data['config']['entry_limit']}` / `{data['config']['source_limit']}`",
        f"- best-any seed: `{data['best_any_seed_rank']}`",
        f"- best-merchant seed: `{data['best_merchant_seed_rank']}`",
        "",
        "## Seed Runs",
        "",
        "| # | seed | seed-score | goals | merchant-goals | best-any | merchants | best-merchant | merchants |",
        "|---:|---|---:|---:|---:|---:|---|---:|---|",
    ]
    for row in data["seed_runs"]:
        seed = row["seed"] or {}
        any_row = row["best_any"] or {}
        merchant_row = row["best_merchant"] or {}
        lines.append(
            f"| {row['seed_rank']} | {row['seed_source']} | "
            f"{fmt_score(seed.get('final_score', 0))} | {row['goal_count']} | "
            f"{row['merchant_goal_count']} | "
            f"{fmt_score(any_row['final_score']) if any_row else '-'} | "
            f"{','.join(any_row.get('merchants', [])) or '-'} | "
            f"{fmt_score(merchant_row['final_score']) if merchant_row else '-'} | "
            f"{','.join(merchant_row.get('merchants', [])) or '-'} |"
        )

    lines.extend([
        "",
        "## Boss Compare",
        "",
        "| label | source | state | merchants | futureG | remaining | final-score |",
        "|---|---|---|---|---:|---:|---:|",
    ])
    for row in data["boss_compare"]:
        lines.append(
            f"| {row['label']} | {row['source']} | "
            f"HP={row['hp']} ATK={row['atk']} DEF={row['def']} "
            f"YK={row['yk']} BK={row['bk']} RK={row['rk']} "
            f"G={row['gold']} dmg={row['dmg']} door={row['yd']}/{row['bd']}/{row['rd']} | "
            f"{','.join(row['merchants']) or '-'} | {row['future_monster_gold']} | "
            f"{fmt_score(row['remaining_group_value'])} | {fmt_score(row['final_score'])} |"
        )
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")
    data["_out_json"] = out_json
    data["_out_md"] = out_md


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds", type=int, default=8)
    parser.add_argument("--stat-rounds", type=int, default=None)
    parser.add_argument("--redkey-rounds", type=int, default=None)
    parser.add_argument("--boss-rounds", type=int, default=None)
    parser.add_argument("--entry-limit", type=int, default=320)
    parser.add_argument("--source-limit", type=int, default=24)
    parser.add_argument("--merchant-phase1-seeds", type=int, default=3)
    parser.add_argument("--long-cache", default=DEFAULT_LONG_CACHE)
    parser.add_argument("--seed-filter", choices=("all", "guide", "delayed", "4-9 merchant"), default="all")
    parser.add_argument("--output-tag", default="")
    args = parser.parse_args()
    if args.stat_rounds is None:
        args.stat_rounds = args.rounds
    if args.redkey_rounds is None:
        args.redkey_rounds = max(1, args.rounds // 2)
    if args.boss_rounds is None:
        args.boss_rounds = max(1, args.rounds // 2)
    data = run(args)
    write_outputs(data)
    print(f"wrote {data['_out_json']}")
    print(f"wrote {data['_out_md']}")


if __name__ == "__main__":
    main()
