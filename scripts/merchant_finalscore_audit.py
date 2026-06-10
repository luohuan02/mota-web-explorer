#!/usr/bin/env python3
"""Compare merchant-aware 4F-9F and boss final-score candidates."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from copy import deepcopy
from types import SimpleNamespace
from typing import Any


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.chdir(ROOT)

from scripts import compare_merchant_resource_paths as cm
from scripts import fixed_shield_strategy as fixed
from scripts import gen_delayed_phase1_detailed_walk as delayed_walk
from scripts import post9_action_search as p9base
from scripts import post9_gem_supply_search as p9gem
from scripts import post9_resource_group_search as rg
from src.solver import gen_walkthrough as gw


OUT_JSON = os.path.join("outputs", "results", "merchant_finalscore_audit.json")
OUT_MD = os.path.join("outputs", "reports", "merchant_finalscore_audit.md")
DELAYED_WALK = os.path.join(
    "outputs", "walkthroughs", "walkthrough_post9_gem_supply_best_stat27_topk_dp_full.md"
)
MERCHANT_WALK_JSON = os.path.join("outputs", "results", "merchant_phase1_gold_walk.json")


def prefix_metrics(prefix_result: dict[str, Any]) -> tuple[int, int, int, int]:
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


def ent_from_fixed_prefix() -> dict[str, Any]:
    prefix = fixed.replay_route()
    if not prefix["ok"] or not prefix["strict_reachable"]:
        raise RuntimeError(f"fixed prefix replay failed: {prefix['errors']}")
    dmg, yd, bd, rd = prefix_metrics(prefix)
    st = prefix["final_state"]
    collected = {
        fid: frozenset((item["x"], item["y"]) for item in positions)
        for fid, positions in prefix["collected"].items()
    }
    return {
        "hp": st["hp"],
        "atk": st["atk"],
        "def": st["def"],
        "yk": st["yk"],
        "bk": st["bk"],
        "rk": st["rk"],
        "collected": collected,
        "_dmg": dmg,
        "_yd": yd,
        "_bd": bd,
        "_rd": rd,
    }


def state_to_ent(state: dict[str, int], collected: dict[str, frozenset]) -> dict[str, Any]:
    return {
        "hp": state["hp"],
        "atk": state["atk"],
        "def": state["def"],
        "yk": state["yk"],
        "bk": state["bk"],
        "rk": state["rk"],
        "collected": {fid: frozenset(pos) for fid, pos in collected.items()},
        "_dmg": state["dmg"],
        "_yd": state["yd"],
        "_bd": state["bd"],
        "_rd": state["rd"],
    }


def replay_delayed_walk(path: str = DELAYED_WALK) -> tuple[dict[str, Any], dict[str, Any]]:
    start_state, segments = delayed_walk.parse_compact_walk(path)
    collected = gw.initial_collected_state()
    prev = start_state
    phase1_ent: dict[str, Any] | None = None
    final_ent: dict[str, Any] | None = None
    for seg in segments:
        before = dict(prev)
        if seg["fid"] == "MULTI":
            for fid, x, y, _eid in seg["free_items"]:
                collected[fid] = collected.get(fid, frozenset()) | frozenset({(x, y)})
        else:
            steps, _vis = delayed_walk.reconstruct_segment(before, collected, seg)
            if steps is None:
                raise RuntimeError(f"cannot reconstruct delayed segment: {seg['label']}")
        ent = state_to_ent(seg["state"], collected)
        if "phase1 delayed prefix complete" in seg["label"]:
            phase1_ent = ent
        final_ent = ent
        prev = seg["state"]
    if phase1_ent is None or final_ent is None:
        raise RuntimeError("delayed phase1/final ent missing")
    return phase1_ent, final_ent


def merchant_walk_ent(path: str = MERCHANT_WALK_JSON) -> dict[str, Any] | None:
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    st = data["final_state"]
    collected = {
        fid: frozenset(tuple(pos) for pos in positions)
        for fid, positions in data.get("collected", {}).items()
    }
    ent = {
        "hp": st["hp"],
        "atk": st["atk"],
        "def": st["def"],
        "yk": st["yk"],
        "bk": st["bk"],
        "rk": st["rk"],
        "collected": collected,
        "_dmg": st["_dmg"],
        "_yd": st["_yd"],
        "_bd": st["_bd"],
        "_rd": st["_rd"],
        "_gold_initial": st.get("_gold_initial"),
        "_gold_gained": st.get("_gold_gained"),
        "_gold_spent": st.get("_gold_spent"),
        "_seed_source": "verified MT7 merchant walk",
    }
    return ent


def state_signature(ent: dict[str, Any]) -> tuple[Any, ...]:
    collected = tuple(
        sorted((fid, tuple(sorted(pos))) for fid, pos in ent.get("collected", {}).items())
    )
    merchants = tuple(sorted(m.key for m in cm.MERCHANTS if cm.merchant_used_by_collected(ent, m)))
    return (
        ent["hp"], ent["atk"], ent["def"], ent["yk"], ent["bk"], ent["rk"],
        ent.get("_dmg", 0), ent.get("_yd", 0), ent.get("_bd", 0), ent.get("_rd", 0),
        merchants,
        collected,
    )


def selected_merchant_labels(ent: dict[str, Any]) -> tuple[str, ...]:
    return tuple(sorted(m.key for m in cm.MERCHANTS if cm.merchant_used_by_collected(ent, m)))


def select_merchant_seeds(
    goals: list[dict[str, Any]],
    explicit: dict[str, Any] | None,
    limit: int,
) -> list[dict[str, Any]]:
    pools: list[list[dict[str, Any]]] = []
    if explicit is not None:
        pools.append([explicit])
    pools.extend([
        sorted(goals, key=lambda ent: (-cm.final_stock_with_gold(ent), ent.get("_dmg", 0), -ent["hp"])),
        sorted(goals, key=lambda ent: (-ent["hp"], ent.get("_dmg", 0), -cm.final_stock_with_gold(ent))),
        sorted(goals, key=lambda ent: (-(ent["yk"] * 5 + ent["bk"] * 20), ent.get("_dmg", 0), -ent["hp"])),
        sorted(goals, key=lambda ent: (-len(selected_merchant_labels(ent)), ent.get("_dmg", 0), -ent["hp"])),
    ])
    for merchant in cm.MERCHANTS:
        subset = [ent for ent in goals if merchant.key in selected_merchant_labels(ent)]
        pools.append(sorted(subset, key=lambda ent: (-cm.final_stock_with_gold(ent), ent.get("_dmg", 0), -ent["hp"])))

    out: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    for pool in pools:
        for ent in pool:
            sig = state_signature(ent)
            if sig in seen:
                continue
            seen.add(sig)
            out.append(ent)
            if len(out) >= limit:
                return out
            break
    for ent in sorted(goals, key=lambda ent: (-cm.final_stock_with_gold(ent), ent.get("_dmg", 0), -ent["hp"])):
        sig = state_signature(ent)
        if sig in seen:
            continue
        seen.add(sig)
        out.append(ent)
        if len(out) >= limit:
            break
    return out


def install_post9_resource_group_hooks() -> None:
    rg.base.select_sources = merchant_aware_select_sources
    rg.base.trim_entries = rg.trim_entries
    rg.base.best_goals = rg.best_goals
    rg.base.ensure_mt10 = rg.ensure_mt10
    rg.base.apply_action = merchant_aware_apply_action
    rg.base.redkey_survival_deficit = rg.redkey_survival_deficit


def annotate_money(ent: dict[str, Any]) -> dict[str, Any]:
    ent["merchant_used"] = frozenset(
        m.key for m in cm.MERCHANTS if cm.merchant_used_by_collected(ent, m)
    )
    ent["gold"] = cm.inferred_gold(ent, include_boss_spawn=False)
    ent["_gold_spent"] = cm.merchant_spent_from_collected(ent)
    ent["_gold_gained"] = ent["gold"] + ent["_gold_spent"] - cm.DEFAULT_START_GOLD
    ent.setdefault("_max_floor", 10 if "MT10" in ent.get("collected", {}) else 9)
    cm.sync_store(ent)
    return ent


def merchant_aware_select_sources(entries: list[dict[str, Any]], fid: str, target: str, limit: int) -> list[dict[str, Any]]:
    if fid != "merchant":
        return rg.select_sources(entries, fid, target, limit)
    merchant = cm.MERCHANT_BY_KEY[target]
    src = [
        annotate_money(e)
        for e in entries
        if not cm.merchant_used_by_collected(e, merchant)
    ]
    if not src:
        return []
    if merchant.bk_gain:
        selectors = [
            lambda e: (-e["bk"], e.get("_dmg", 0), -e["hp"]),
            lambda e: (max(0, merchant.spend_gold - e.get("gold", 0)), e.get("_dmg", 0), -e["hp"]),
            lambda e: (rg.redkey_survival_deficit(e), e.get("_dmg", 0), -e["yk"], -e["hp"]),
        ]
    else:
        selectors = [
            lambda e: (-e["yk"], e.get("_dmg", 0), -e["hp"]),
            lambda e: (max(0, merchant.spend_gold - e.get("gold", 0)), e.get("_dmg", 0), -e["hp"]),
            lambda e: (p9base.boss_survival_deficit(e), e.get("_dmg", 0), -e["yk"], -e["hp"]),
        ]
    selected: list[dict[str, Any]] = []
    seen: set[int] = set()
    per_selector = max(2, limit // len(selectors))
    for selector in selectors:
        picked = 0
        for ent in sorted(src, key=selector):
            eid = ent.get("_id")
            if eid in seen:
                continue
            seen.add(eid)
            selected.append(ent)
            picked += 1
            if len(selected) >= limit or picked >= per_selector:
                break
    return selected[:limit]


def merchant_aware_apply_action(ent: dict[str, Any], fid: str, target: str) -> list[dict[str, Any]]:
    ent = annotate_money(ent)
    if fid == "merchant":
        out = cm.expand_merchant_action(ent, ("merchant", target))
    else:
        out = rg.apply_action(ent, fid, target)
    return [annotate_money(item) for item in out]


def seed_for_post9(ent: dict[str, Any]) -> dict[str, Any]:
    seed = deepcopy(ent)
    seed["_id"] = 1
    seed["_parent_id"] = None
    seed["_step_info"] = None
    seed.setdefault("_max_floor", 9)
    annotate_money(seed)
    gw._entry_store.clear()
    gw._next_id[0] = 1
    gw._entry_store[1] = dict(seed)
    return seed


def run_post9_from_seed(
    seed_ent: dict[str, Any],
    *,
    rounds: int,
    entry_limit: int,
    source_limit: int,
) -> dict[str, Any]:
    install_post9_resource_group_hooks()
    seed = seed_for_post9(seed_ent)
    t0 = time.time()
    merchant_actions = [("merchant", merchant.key) for merchant in cm.MERCHANTS]
    stat_entries, stat_rows = rg.base.run_stage(
        "stat27", [seed], list(rg.STAT_ACTIONS) + merchant_actions, rg.base.stat_goal,
        max(6, rounds), entry_limit, source_limit,
    )
    redkey_entries, redkey_rows = rg.base.run_stage(
        "redkey", stat_entries, list(rg.base.REDKEY_ACTIONS) + merchant_actions, rg.base.redkey_goal,
        max(4, rounds // 2), entry_limit, source_limit,
    )
    final_entries, boss_rows = rg.base.run_stage(
        "boss", redkey_entries, list(rg.base.BOSS_PREP_ACTIONS) + merchant_actions, rg.base.goal,
        max(4, rounds // 2), entry_limit, source_limit, include_boss=True,
    )
    goals = [ent for ent in final_entries if rg.base.goal(ent)]
    goals.sort(key=lambda ent: (-cm.final_stock_with_gold(ent), ent.get("_dmg", 0), -ent["hp"]))
    merchant_goals = [ent for ent in goals if selected_merchant_labels(ent)]
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
    }


def remaining_groups(ent: dict[str, Any]) -> list[dict[str, Any]]:
    rows = cm.resource_group_breakdown_with_future_gold(ent)
    rows.sort(key=lambda row: (-row["value"], row["floor"], row["group"]))
    return rows


def score_record(label: str, ent: dict[str, Any], *, source: str) -> dict[str, Any]:
    groups = remaining_groups(ent)
    residual_value = sum(row["value"] for row in groups)
    base_stock = cm.final_resource_stock_with_future_gold(ent)
    merchant_residual = sum(row.get("future_merchant_value", 0) for row in groups)
    future_monster_gold = sum(row.get("future_monster_gold", 0) for row in groups)
    gold = cm.inferred_gold(ent)
    final_score = base_stock + cm.gold_value(gold)
    return {
        "label": label,
        "source": source,
        "jhp": ent["hp"],
        "hp": ent["hp"],
        "atk": ent["atk"],
        "def": ent["def"],
        "yk": ent["yk"],
        "bk": ent["bk"],
        "rk": ent["rk"],
        "dmg": ent.get("_dmg", 0),
        "yd": ent.get("_yd", 0),
        "bd": ent.get("_bd", 0),
        "rd": ent.get("_rd", 0),
        "gold": gold,
        "gold_score": cm.gold_value(gold),
        "future_monster_gold": future_monster_gold,
        "future_monster_gold_score": cm.gold_value(future_monster_gold),
        "base_final_stock": base_stock,
        "merchant_residual": merchant_residual,
        "remaining_group_value": residual_value,
        "final_score": final_score,
        "merchants": sorted(m.key for m in cm.MERCHANTS if cm.merchant_used_by_collected(ent, m)),
        "actions": cm.trace_actions(ent),
        "remaining_groups": groups,
        "ent": ent,
    }


def group_diff(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    labels = [row["label"] for row in records]
    by_label = {
        row["label"]: {group["group"]: group for group in row["remaining_groups"]}
        for row in records
    }
    names = sorted({name for groups in by_label.values() for name in groups})
    out = []
    for name in names:
        values = {
            label: by_label[label].get(name, {}).get("value")
            for label in labels
        }
        if len(set(values.values())) <= 1:
            continue
        out.append({
            "group": name,
            "values": values,
        })
    return out


def compact_record(row: dict[str, Any]) -> dict[str, Any]:
    out = {k: v for k, v in row.items() if k not in {"ent", "remaining_groups"}}
    out["remaining_groups"] = row["remaining_groups"]
    return out


def fmt_score(value: float) -> str:
    return str(int(value)) if abs(value - int(value)) < 1e-9 else f"{value:.1f}"


def group_summary(groups: list[dict[str, Any]], limit: int = 8) -> str:
    if not groups:
        return "-"
    return "; ".join(f"{row['group']}={fmt_score(row['value'])}" for row in groups[:limit])


def write_outputs(data: dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    lines = [
        "# Merchant Final-Score Audit",
        "",
        "## Score Model",
        "",
        f"- final-score = HP/key stock + full-map remaining resources + current gold * 0.5. Key values: YK={rg.YK_VALUE}, BK={rg.BK_VALUE}.",
        "- Full-map remaining resources count uncollected monster gold and unused merchant net value as future zero-damage resources, while still subtracting unopened yellow/blue door key value.",
        "- 4F start money is 7. Enemy money is read from `core.material.enemys[*].money`.",
        "- Boss event gold is counted once; the original MT10 x6y4 captain block is excluded after the boss event.",
        "",
    ]
    for stage_key, title in [("phase1", "4-9 after shield/red-blue gems"), ("boss", "After 10F boss")]:
        lines.extend([
            f"## {title}",
            "",
            "| route | jhp | dmg | keys | doors | gold | future monster gold | remaining groups | final-score | source |",
            "|---|---:|---:|---|---|---:|---:|---:|---:|---|",
        ])
        for row in data[stage_key]["records"]:
            lines.append(
                f"| {row['label']} | {row['jhp']} | {row['dmg']} | "
                f"{row['yk']}/{row['bk']}/{row['rk']} | {row['yd']}/{row['bd']}/{row['rd']} | "
                f"{row['gold']} | {row['future_monster_gold']} | "
                f"{fmt_score(row['remaining_group_value'])} | "
                f"{fmt_score(row['final_score'])} | {row['source']} |"
            )
        lines.extend(["", "### Remaining Groups", ""])
        for row in data[stage_key]["records"]:
            lines.append(f"- {row['label']}: {group_summary(row['remaining_groups'])}")
        action_rows = [row for row in data[stage_key]["records"] if row.get("actions")]
        if action_rows:
            lines.extend(["", "### Compact Actions", ""])
            for row in action_rows:
                lines.append(f"- {row['label']}: " + "; ".join(row["actions"]))
        lines.extend(["", "### Diff Groups", ""])
        diff = data[stage_key]["diff_groups"]
        if not diff:
            lines.append("- none")
        else:
            labels = [row["label"] for row in data[stage_key]["records"]]
            lines.append("| group | " + " | ".join(labels) + " |")
            lines.append("|---|" + "|".join("---:" for _ in labels) + "|")
            for row in diff:
                vals = [
                    "-" if row["values"][label] is None else fmt_score(row["values"][label])
                    for label in labels
                ]
                lines.append(f"| {row['group']} | " + " | ".join(vals) + " |")
        lines.append("")
    lines.extend([
        "## Merchant Search",
        "",
        f"- phase1 elapsed/expanded/generated/goals: `{data['merchant_search']['elapsed']:.1f}s` / "
        f"`{data['merchant_search']['expanded']}` / `{data['merchant_search']['generated']}` / "
        f"`{data['merchant_search']['raw_goal_count']}`",
        f"- explicit verified MT7 walk loaded: `{data['merchant_phase1_explicit_walk_loaded']}`",
        f"- phase1 merchant candidates scored: `{data['merchant_phase1_candidate_count']}`",
        f"- post9 seeds tried: `{len(data['merchant_boss_runs'])}`",
        f"- merchant boss goal found: `{data['merchant_boss_found']}`",
    ])
    for run in data["merchant_boss_runs"]:
        lines.append(
            f"- seed {run['seed_rank']}: goals={run['goal_count']} elapsed={run['elapsed']:.1f}s "
            f"seedScore={fmt_score(run['seed_final_score'])} source={run['seed_source']}"
        )
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase1-expansions", type=int, default=500)
    parser.add_argument("--phase1-min-expansions", type=int, default=180)
    parser.add_argument("--phase1-goal-limit", type=int, default=80)
    parser.add_argument("--phase1-report-limit", type=int, default=32)
    parser.add_argument("--boss-seeds", type=int, default=6)
    parser.add_argument("--post9-rounds", type=int, default=8)
    parser.add_argument("--post9-entry-limit", type=int, default=320)
    parser.add_argument("--post9-source-limit", type=int, default=24)
    args = parser.parse_args()

    cm.ensure_merchant_maps()
    search_args = SimpleNamespace(
        max_expansions=args.phase1_expansions,
        min_expansions=args.phase1_min_expansions,
        goal_limit=args.phase1_goal_limit,
        report_limit=args.phase1_report_limit,
        start_gold=cm.DEFAULT_START_GOLD,
    )
    merchant_goals, merchant_meta = cm.run_search(search_args)
    merchant_goals.sort(key=lambda ent: (-cm.final_stock_with_gold(ent), ent.get("_dmg", 0), -ent["hp"]))
    for ent in merchant_goals:
        ent.setdefault("_seed_source", "phase1 merchant search")
    explicit_walk = merchant_walk_ent()
    combined_phase1_goals: list[dict[str, Any]] = []
    seen_phase1: set[tuple[Any, ...]] = set()
    for ent in ([explicit_walk] if explicit_walk is not None else []) + merchant_goals:
        sig = state_signature(ent)
        if sig in seen_phase1:
            continue
        seen_phase1.add(sig)
        combined_phase1_goals.append(ent)
    combined_phase1_goals.sort(
        key=lambda ent: (-cm.final_stock_with_gold(ent), ent.get("_dmg", 0), -ent["hp"])
    )
    if not combined_phase1_goals:
        raise RuntimeError("no merchant phase1 goals found")

    merchant_phase1_best = combined_phase1_goals[0]
    merchant_seeds = select_merchant_seeds(merchant_goals, explicit_walk, args.boss_seeds)
    merchant_boss_runs = []
    best_boss_ent = None
    best_boss_seed = None
    for rank, seed in enumerate(merchant_seeds, 1):
        run = run_post9_from_seed(
            seed,
            rounds=args.post9_rounds,
            entry_limit=args.post9_entry_limit,
            source_limit=args.post9_source_limit,
        )
        row = {
            "seed_rank": rank,
            "seed_source": seed.get("_seed_source", "phase1 merchant search"),
            "seed_state": {
                "hp": seed["hp"],
                "atk": seed["atk"],
                "def": seed["def"],
                "yk": seed["yk"],
                "bk": seed["bk"],
                "rk": seed["rk"],
                "dmg": seed.get("_dmg", 0),
                "doors": [seed.get("_yd", 0), seed.get("_bd", 0), seed.get("_rd", 0)],
                "gold": cm.inferred_gold(seed),
                "merchants": list(selected_merchant_labels(seed)),
            },
            "seed_final_score": cm.final_stock_with_gold(seed),
            "elapsed": run["elapsed"],
            "goal_count": run["goal_count"],
            "entry_count": run["entry_count"],
        }
        merchant_boss_runs.append(row)
        if run["best_ent"] is None:
            continue
        if best_boss_ent is None or cm.final_stock_with_gold(run["best_ent"]) > cm.final_stock_with_gold(best_boss_ent):
            best_boss_ent = run["best_ent"]
            best_boss_seed = rank

    fixed_phase1 = ent_from_fixed_prefix()
    fixed_boss = cm.guide_full_ent()
    delayed_phase1, delayed_boss = replay_delayed_walk(DELAYED_WALK)

    phase1_records = [
        score_record("merchant", merchant_phase1_best, source="search at least 1 merchant"),
        score_record("guide", fixed_phase1, source="fixed guide 4-9"),
        score_record("delayed", delayed_phase1, source="known delayed best prefix"),
    ]
    boss_records = []
    if best_boss_ent is not None:
        boss_records.append(score_record("merchant", best_boss_ent, source=f"post9 search seed #{best_boss_seed}"))
    boss_records.extend([
        score_record("guide", fixed_boss, source="fixed guide boss replay"),
        score_record("delayed", delayed_boss, source="known delayed best walk"),
    ])

    data = {
        "config": vars(args),
        "score_model": {
            "gold_value_per_100": cm.GOLD_VALUE_PER_100,
            "yellow_key_value": rg.YK_VALUE,
            "blue_key_value": rg.BK_VALUE,
            "start_gold": cm.DEFAULT_START_GOLD,
            "enemy_gold": cm.ENEMY_GOLD,
            "merchant_access": cm.MERCHANT_ACCESS,
        },
        "merchant_search": merchant_meta,
        "merchant_phase1_candidate_count": len(combined_phase1_goals),
        "merchant_phase1_explicit_walk_loaded": explicit_walk is not None,
        "merchant_boss_runs": merchant_boss_runs,
        "merchant_boss_found": best_boss_ent is not None,
        "phase1": {
            "records": [compact_record(row) for row in phase1_records],
            "diff_groups": group_diff(phase1_records),
        },
        "boss": {
            "records": [compact_record(row) for row in boss_records],
            "diff_groups": group_diff(boss_records),
        },
    }
    write_outputs(data)
    print(f"wrote {OUT_JSON}")
    print(f"wrote {OUT_MD}")
    print(
        "phase1 best merchant",
        f"score={fmt_score(phase1_records[0]['final_score'])}",
        f"state=HP{phase1_records[0]['hp']} {phase1_records[0]['atk']}/{phase1_records[0]['def']} "
        f"keys={phase1_records[0]['yk']}/{phase1_records[0]['bk']}/{phase1_records[0]['rk']}",
    )
    print(
        "boss best merchant",
        "not found" if best_boss_ent is None else f"score={fmt_score(boss_records[0]['final_score'])}",
        "" if best_boss_ent is None else (
            f"state=HP{boss_records[0]['hp']} {boss_records[0]['atk']}/{boss_records[0]['def']} "
            f"keys={boss_records[0]['yk']}/{boss_records[0]['bk']}/{boss_records[0]['rk']}"
        ),
    )


if __name__ == "__main__":
    main()
