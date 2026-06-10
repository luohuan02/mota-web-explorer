#!/usr/bin/env python3
"""Report old score vs conservative remaining-resource score.

This script keeps the existing score untouched and adds a second ranking that
does not treat an unopened door as a win when the door guards an equal net key
resource.  The residual resource model is intentionally conservative: it only
credits simple key pockets that caused known ranking confusion.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.chdir(ROOT)

from src.solver import gen_walkthrough as gw
from scripts import phase1_action_search as p1
from scripts import post9_action_search as p9


OUT_JSON = os.path.join("outputs", "results", "resource_score_top.json")
OUT_MD = os.path.join("outputs", "reports", "resource_score_top.md")

YK_VALUE = 50
BK_VALUE = 200

# Conservative, hand-audited key pockets.  Door entries are counted only if
# the pocket item is still uncollected and the door itself is still unopened.
YELLOW_KEY_POCKETS = [
    {
        "name": "6F x9y1 黄钥匙",
        "fid": "MT6",
        "keys": {(9, 1)},
        "doors": set(),
    },
    {
        "name": "7F x5y10/x5y11 两黄钥匙",
        "fid": "MT7",
        "keys": {(5, 10), (5, 11)},
        "doors": {(5, 7)},
    },
]


def collected_for(e: dict[str, Any], fid: str) -> set[tuple[int, int]]:
    positions = set((e.get("collected") or {}).get(fid, frozenset()))
    positions.update(gw.FLOOR_13_COLLECTED.get(fid, frozenset()))
    return positions


def state_record(e: dict[str, Any], source: str) -> dict[str, Any]:
    return {
        "source": source,
        "id": e.get("_id") or e.get("id"),
        "hp": int(e["hp"]),
        "atk": int(e["atk"]),
        "def": int(e["def"]),
        "yk": int(e["yk"]),
        "bk": int(e["bk"]),
        "rk": int(e["rk"]),
        "dmg": int(e.get("_dmg", e.get("dmg", 0))),
        "yd": int(e.get("_yd", e.get("yd", 0))),
        "bd": int(e.get("_bd", e.get("bd", 0))),
        "rd": int(e.get("_rd", e.get("rd", 0))),
    }


def old_score(e: dict[str, Any]) -> int:
    r = state_record(e, e.get("source", ""))
    return (
        r["dmg"]
        + r["yd"] * YK_VALUE
        + r["bd"] * BK_VALUE
        - r["hp"]
        - r["yk"] * YK_VALUE
        - r["bk"] * BK_VALUE
    )


def residual_yellow_key_net(e: dict[str, Any]) -> tuple[int, list[str]]:
    """Return conservative recoverable net yellow keys and notes."""
    total = 0
    notes: list[str] = []
    override = e.get("_residual_yk_net_override")
    if override is not None:
        total = int(override)
        notes.append(f"manual residual YK net={total}")
        return total, notes

    for pocket in YELLOW_KEY_POCKETS:
        fid = pocket["fid"]
        used = collected_for(e, fid)
        keys_left = sum(1 for pos in pocket["keys"] if pos not in used)
        if keys_left <= 0:
            continue
        unopened_doors = sum(1 for pos in pocket["doors"] if pos not in used)
        net = max(0, keys_left - unopened_doors)
        if net:
            total += net
            notes.append(
                f"{pocket['name']} +{net}yk"
                + (f" ({keys_left} key - {unopened_doors} door)" if unopened_doors else "")
            )
    return total, notes


def remaining_raw_key_counts(e: dict[str, Any]) -> tuple[int, int]:
    y = b = 0
    for fid, data in gw.maps.items():
        used = collected_for(e, fid)
        for x, y_pos, t, eid in data["bl"]:
            if t != 3 or (x, y_pos) in used:
                continue
            if eid == "yellowKey":
                y += 1
            elif eid == "blueKey":
                b += 1
    return y, b


def resource_score(e: dict[str, Any]) -> int:
    r = state_record(e, e.get("source", ""))
    residual_yk, _notes = residual_yellow_key_net(e)
    return (
        r["dmg"]
        - r["hp"]
        - r["yk"] * YK_VALUE
        - r["bk"] * BK_VALUE
        - residual_yk * YK_VALUE
    )


def enrich(e: dict[str, Any], source: str) -> dict[str, Any]:
    rec = state_record(e, source)
    rec["old_score"] = old_score(e)
    rec["resource_score"] = resource_score(e)
    rec["score_delta"] = rec["resource_score"] - rec["old_score"]
    residual_yk, notes = residual_yellow_key_net(e)
    raw_yk, raw_bk = remaining_raw_key_counts(e) if "collected" in e else (None, None)
    rec["residual_yk_net"] = residual_yk
    rec["residual_notes"] = notes
    rec["remaining_raw_yk"] = raw_yk
    rec["remaining_raw_bk"] = raw_bk
    rec["actions"] = e.get("actions", [])
    rec["fixed_exact"] = e.get("fixed_exact", False)
    return rec


def unique_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    out = []
    for row in rows:
        key = (
            row["hp"], row["atk"], row["def"], row["yk"], row["bk"], row["rk"],
            row["dmg"], row["yd"], row["bd"], row["rd"], row["source"],
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out


def top_by(rows: list[dict[str, Any]], key: str, limit: int) -> list[dict[str, Any]]:
    return unique_rows(sorted(rows, key=lambda r: (r[key], r["old_score"], -r["hp"])))[:limit]


def rank_map(rows: list[dict[str, Any]], key: str) -> dict[tuple[Any, ...], int]:
    ranked = unique_rows(sorted(rows, key=lambda r: (r[key], r["old_score"], -r["hp"])))
    return {
        (
            r["hp"], r["atk"], r["def"], r["yk"], r["bk"], r["rk"],
            r["dmg"], r["yd"], r["bd"], r["rd"], r["source"],
        ): i + 1
        for i, r in enumerate(ranked)
    }


def attach_rank_delta(rows: list[dict[str, Any]]) -> None:
    old_ranks = rank_map(rows, "old_score")
    res_ranks = rank_map(rows, "resource_score")
    for row in rows:
        key = (
            row["hp"], row["atk"], row["def"], row["yk"], row["bk"], row["rk"],
            row["dmg"], row["yd"], row["bd"], row["rd"], row["source"],
        )
        row["old_rank"] = old_ranks.get(key)
        row["resource_rank"] = res_ranks.get(key)
        if row["old_rank"] is not None and row["resource_rank"] is not None:
            row["rank_delta"] = row["old_rank"] - row["resource_rank"]


def external_final_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    guide_path = os.path.join("outputs", "results", "user_post9_route_replay.json")
    if os.path.exists(guide_path):
        with open(guide_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        final = data["final"]
        state = final["state"]
        rows.append(enrich({
            **state,
            "_dmg": final["dmg"],
            "_yd": final["doors"]["yellow"],
            "_bd": final["doors"]["blue"],
            "_rd": final["doors"]["red"],
            "_residual_yk_net_override": 1,
        }, "guide verified"))

    # The verified wide walk has a compact action walk, so its residual is
    # recorded manually from the audited diff report: 7F two keys behind one
    # yellow door => net +1 YK.
    rows.append(enrich({
        "hp": 8,
        "atk": 27,
        "def": 27,
        "yk": 0,
        "bk": 0,
        "rk": 0,
        "_dmg": 2618,
        "_yd": 39,
        "_bd": 2,
        "_rd": 1,
        "_residual_yk_net_override": 1,
    }, "verified wide walk"))
    return rows


def run_phase1(max_expansions: int, queue_mode: str) -> list[dict[str, Any]]:
    print(f"running phase1 action search: expansions={max_expansions} mode={queue_mode}", flush=True)
    result = p1.run(max_expansions=max_expansions, queue_mode=queue_mode, include_entries=True)
    goals = result.get("_goal_entries", [])
    rows = [enrich(e, f"phase1:{queue_mode}") for e in goals]
    attach_rank_delta(rows)
    return rows


def run_boss(rounds: int, entry_limit: int, source_limit: int) -> list[dict[str, Any]]:
    print(
        f"running post9 staged search: rounds={rounds} entry_limit={entry_limit} source_limit={source_limit}",
        flush=True,
    )
    start = p9.seed_fixed_prefix()
    stat_entries, _stat_rows = p9.run_stage(
        "stat27", [start], p9.STAT_ACTIONS, p9.stat_goal,
        max(6, rounds), entry_limit, source_limit,
    )
    redkey_entries, _red_rows = p9.run_stage(
        "redkey", stat_entries, p9.REDKEY_ACTIONS, p9.redkey_goal,
        max(4, rounds // 2), entry_limit, source_limit,
    )
    final_entries, _boss_rows = p9.run_stage(
        "boss", redkey_entries, p9.BOSS_PREP_ACTIONS, p9.goal,
        max(4, rounds // 2), entry_limit, source_limit, include_boss=True,
    )
    goals = p9.best_goals(final_entries)
    rows = [enrich(e, "post9 staged") for e in goals]
    rows.extend(external_final_rows())
    attach_rank_delta(rows)
    return rows


def state_text(row: dict[str, Any]) -> str:
    return (
        f"HP={row['hp']} ATK={row['atk']} DEF={row['def']} "
        f"YK={row['yk']} BK={row['bk']} RK={row['rk']} "
        f"dmg={row['dmg']} door={row['yd']}/{row['bd']}/{row['rd']}"
    )


def table(rows: list[dict[str, Any]], title: str) -> list[str]:
    lines = [
        f"## {title}",
        "",
        "| # | oldRank | resRank | oldScore | resScore | delta | state | resYK | source | notes |",
        "|---:|---:|---:|---:|---:|---:|---|---:|---|---|",
    ]
    for i, row in enumerate(rows, 1):
        notes = "; ".join(row.get("residual_notes") or [])
        lines.append(
            f"| {i} | {row.get('old_rank', '-')} | {row.get('resource_rank', '-')} | "
            f"{row['old_score']} | {row['resource_score']} | {row['score_delta']} | "
            f"{state_text(row)} | {row['residual_yk_net']} | {row['source']} | {notes or '-'} |"
        )
    lines.append("")
    return lines


def write_report(phase_rows: list[dict[str, Any]], boss_rows: list[dict[str, Any]], limit: int) -> None:
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)

    data = {
        "score_definitions": {
            "old_score": "dmg + yd*50 + bd*200 - hp - yk*50 - bk*200",
            "resource_score": "dmg - hp - yk*50 - bk*200 - conservative_residual_yk_net*50",
            "note": "resource_score preserves old score separately and uses only audited residual YK pockets.",
        },
        "phase_count": len(phase_rows),
        "boss_count": len(boss_rows),
        "phase_old_top": top_by(phase_rows, "old_score", limit),
        "phase_resource_top": top_by(phase_rows, "resource_score", limit),
        "boss_old_top": top_by(boss_rows, "old_score", limit),
        "boss_resource_top": top_by(boss_rows, "resource_score", limit),
    }
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    lines = [
        "# Resource Score Top",
        "",
        "旧 score 保留：`dmg + yd*50 + bd*200 - hp - yk*50 - bk*200`。",
        "",
        "新增 resource score：`dmg - hp - yk*50 - bk*200 - conservative_residual_yk_net*50`。",
        "",
        "这个新 score 不再把“少开门”直接算成胜利，而是看当前剩余钥匙和保守可回收黄钥匙净值。",
        "目前 residual 只计入已审过的关键口袋：6F `x9y1` 黄钥匙、7F `x5y10/x5y11` 两黄钥匙扣 `x5y7` 黄门成本。",
        "",
        f"- 4-9 候选数：{len(phase_rows)}",
        f"- boss 候选数：{len(boss_rows)}",
        "",
    ]
    lines.extend(table(data["phase_old_top"], "4-9 Old Score Top"))
    lines.extend(table(data["phase_resource_top"], "4-9 Resource Score Top"))
    lines.extend(table(data["boss_old_top"], "Boss Old Score Top"))
    lines.extend(table(data["boss_resource_top"], "Boss Resource Score Top"))

    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase-expansions", type=int, default=300)
    parser.add_argument("--phase-queue", choices=["resource", "dmg", "dual"], default="resource")
    parser.add_argument("--post9-rounds", type=int, default=12)
    parser.add_argument("--post9-entry-limit", type=int, default=360)
    parser.add_argument("--post9-source-limit", type=int, default=28)
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()

    phase_rows = run_phase1(args.phase_expansions, args.phase_queue)
    boss_rows = run_boss(args.post9_rounds, args.post9_entry_limit, args.post9_source_limit)
    write_report(phase_rows, boss_rows, args.limit)
    print(f"wrote {OUT_JSON}")
    print(f"wrote {OUT_MD}")


if __name__ == "__main__":
    main()
