#!/usr/bin/env python3
"""Compare cumulative damage groups for two completed strict-Game routes.

The report uses the shared Game's cumulative ``dmg`` counter rather than raw
HP deltas, so potions or other auto side effects in the same logical step do
not hide combat/field damage.  Repeated semantic actions are paired by
occurrence; actions present on only one branch are reported separately instead
of being falsely attributed to an early gem.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BASELINE = ROOT / "outputs/results/zone4_atk261_none_farmfix_candidate.json"
DEFAULT_CANDIDATE = ROOT / "outputs/results/zone4_atk261_all_farmfix_candidate.json"
DEFAULT_JSON = ROOT / "outputs/results/zone4_early_gem_damage_audit.json"
DEFAULT_MD = ROOT / "outputs/reports/zone4_early_gem_damage_audit.md"


def load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not payload.get("ok"):
        raise RuntimeError(f"route is not a completed candidate: {path}")
    return payload


def damage_groups(payload: dict[str, Any]) -> dict[tuple[Any, ...], dict[str, Any]]:
    occurrences: Counter[tuple[Any, ...]] = Counter()
    groups: dict[tuple[Any, ...], dict[str, Any]] = {}
    for index, step in enumerate(payload.get("steps", []), 1):
        before = step.get("before", {})
        after = step.get("after", {})
        damage = int(after.get("dmg", 0)) - int(before.get("dmg", 0))
        if damage <= 0:
            continue
        pos = tuple(step.get("pos", ()))
        semantic = (
            str(step.get("floor", "")),
            pos,
            str(step.get("action", "")),
            str(step.get("eid", "")),
        )
        occurrence = occurrences[semantic]
        occurrences[semantic] += 1
        key = (*semantic, occurrence)
        groups[key] = {
            "step": index,
            "floor": semantic[0],
            "pos": list(pos),
            "action": semantic[2],
            "eid": semantic[3],
            "occurrence": occurrence + 1,
            "damage": damage,
            "before_stats": {
                key: before.get(key) for key in ("hp", "atk", "def", "dmg")
            },
            "after_stats": {
                key: after.get(key) for key in ("hp", "atk", "def", "dmg")
            },
            "note": step.get("note", ""),
        }
    return groups


def compact_final(payload: dict[str, Any]) -> dict[str, Any]:
    final = payload["final"]
    return {key: final.get(key) for key in (
        "hp", "atk", "def", "yk", "bk", "rk", "gold", "dmg",
        "yd", "bd", "rd", "times1", "won49", "won50",
    )}


def shop_sequence(payload: dict[str, Any]) -> list[str]:
    return [
        str(step.get("eid")) for step in payload.get("steps", [])
        if step.get("action") == "商店"
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--candidate", type=Path, default=DEFAULT_CANDIDATE)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_MD)
    args = parser.parse_args()

    baseline = load(args.baseline)
    candidate = load(args.candidate)
    base_groups = damage_groups(baseline)
    cand_groups = damage_groups(candidate)
    common_keys = set(base_groups) & set(cand_groups)
    baseline_only_keys = set(base_groups) - set(cand_groups)
    candidate_only_keys = set(cand_groups) - set(base_groups)

    common: list[dict[str, Any]] = []
    for key in common_keys:
        base = base_groups[key]
        cand = cand_groups[key]
        common.append({
            "floor": base["floor"],
            "pos": base["pos"],
            "action": base["action"],
            "eid": base["eid"],
            "occurrence": base["occurrence"],
            "baseline_step": base["step"],
            "candidate_step": cand["step"],
            "baseline_damage": base["damage"],
            "candidate_damage": cand["damage"],
            "damage_saved": base["damage"] - cand["damage"],
            "baseline_before": base["before_stats"],
            "candidate_before": cand["before_stats"],
        })
    common.sort(key=lambda row: (row["damage_saved"], row["baseline_damage"]), reverse=True)
    baseline_only = [base_groups[key] for key in baseline_only_keys]
    candidate_only = [cand_groups[key] for key in candidate_only_keys]
    baseline_only.sort(key=lambda row: row["damage"], reverse=True)
    candidate_only.sort(key=lambda row: row["damage"], reverse=True)

    common_saved = sum(row["damage_saved"] for row in common)
    baseline_only_damage = sum(row["damage"] for row in baseline_only)
    candidate_only_damage = sum(row["damage"] for row in candidate_only)
    total_saved = int(baseline["final"]["dmg"]) - int(candidate["final"]["dmg"])
    identity = common_saved + baseline_only_damage - candidate_only_damage
    baseline_shops = shop_sequence(baseline)
    candidate_shops = shop_sequence(candidate)
    result = {
        "ok": total_saved == identity and baseline_shops == candidate_shops,
        "scope": "same postShieldAtkTarget=261; no early gem groups vs MT31 red/blue plus MT32 pair",
        "baseline_path": str(args.baseline),
        "candidate_path": str(args.candidate),
        "baseline_variant": baseline.get("variant"),
        "candidate_variant": candidate.get("variant"),
        "baseline_shop_sequence": baseline_shops,
        "candidate_shop_sequence": candidate_shops,
        "same_shop_sequence": baseline_shops == candidate_shops,
        "baseline_final": compact_final(baseline),
        "candidate_final": compact_final(candidate),
        "total_damage_saved": total_saved,
        "final_hp_improvement": int(candidate["final"]["hp"]) - int(baseline["final"]["hp"]),
        "matched_damage_groups": len(common),
        "matched_group_damage_saved": common_saved,
        "baseline_only_groups": len(baseline_only),
        "baseline_only_damage": baseline_only_damage,
        "candidate_only_groups": len(candidate_only),
        "candidate_only_damage": candidate_only_damage,
        "accounting_identity": {
            "formula": "matched_saved + baseline_only_damage - candidate_only_damage",
            "value": identity,
            "equals_total_damage_saved": identity == total_saved,
        },
        "changed_common_groups": [row for row in common if row["damage_saved"] != 0],
        "baseline_only": baseline_only,
        "candidate_only": candidate_only,
    }
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 4区提前宝石逐伤害组差分",
        "",
        f"- 基线：`{args.baseline}`，终态 `{result['baseline_final']}`",
        f"- 候选：`{args.candidate}`，终态 `{result['candidate_final']}`",
        f"- 总纯伤害节省：`{total_saved}`；最终 HP 提升：`{result['final_hp_improvement']}`",
        f"- 两条路线商店序列相同：`{'/'.join(baseline_shops)}`",
        f"- 共同伤害组节省 `{common_saved}`；仅基线伤害 `{baseline_only_damage}`；仅候选伤害 `{candidate_only_damage}`",
        f"- 恒等式：`{common_saved} + {baseline_only_damage} - {candidate_only_damage} = {identity}`",
        "",
        "共同伤害组只比较语义相同且出现次数相同的动作；分支独有战斗单列，不能归因给宝石。",
        "",
        "## 共同伤害组变化",
        "",
        "| 位置 | 动作 | 基线伤害 | 候选伤害 | 节省 | 基线攻防 | 候选攻防 |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in result["changed_common_groups"]:
        x, y = row["pos"] if len(row["pos"]) == 2 else ("-", "-")
        b = row["baseline_before"]
        c = row["candidate_before"]
        lines.append(
            f"| {row['floor']} x{x}y{y} | {row['action']} {row['eid']} #{row['occurrence']} | "
            f"{row['baseline_damage']} | {row['candidate_damage']} | {row['damage_saved']:+d} | "
            f"{b['atk']}/{b['def']} | {c['atk']}/{c['def']} |"
        )
    lines += ["", "## 分支独有伤害组", "", "### 仅基线", ""]
    lines.extend(
        f"- {row['floor']} x{row['pos'][0]}y{row['pos'][1]} {row['action']} {row['eid']}: {row['damage']}"
        for row in baseline_only
    )
    lines += ["", "### 仅候选", ""]
    lines.extend(
        f"- {row['floor']} x{row['pos'][0]}y{row['pos'][1]} {row['action']} {row['eid']}: {row['damage']}"
        for row in candidate_only
    )
    args.out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        f"damage {baseline['final']['dmg']}->{candidate['final']['dmg']} "
        f"saved={total_saved} matched={len(common)} "
        f"baseline_only={len(baseline_only)} candidate_only={len(candidate_only)} ok={result['ok']}"
    )
    print(f"json={args.out_json}")
    print(f"md={args.out_md}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
