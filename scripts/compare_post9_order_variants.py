#!/usr/bin/env python3
"""Audit post-9 gem order variants from the delayed phase1 prefix."""

from __future__ import annotations

import json
import os
import sys
from typing import Any


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.chdir(ROOT)

from scripts import compare_delayed_phase1_vs_user_guide as cmp
from scripts import compare_mt6_key_variant as base
from scripts import continue_delayed_phase1_with_post9_resource as delayed
from scripts import gen_delayed_phase1_detailed_walk as detail_walk
from src.solver.full_search import load_data


OUT_JSON = os.path.join("outputs", "results", "post9_order_variants.json")
OUT_MD = os.path.join("outputs", "reports", "post9_order_variants.md")
MAIN_COMPACT_WALK = os.path.join("outputs", "walkthroughs", "walkthrough_delayed_phase1_post9_resource.md")
MAIN_DETAIL_WALK = os.path.join("outputs", "walkthroughs", "walkthrough_delayed_phase1_post9_resource_detailed.md")
BEST_COMPACT_WALK = os.path.join("outputs", "walkthroughs", "walkthrough_post9_order_key_red_3f_1f.md")
BEST_DETAIL_WALK = os.path.join("outputs", "walkthroughs", "walkthrough_post9_order_key_red_3f_1f_detailed.md")

MT4_X3Y11_KEY_FORBID = {
    (1, 2), (2, 1), (3, 2),
    (5, 10), (5, 11),
    (9, 2), (11, 2),
}

COMMON_SUFFIX = [
    ("MT8 blueGem", "MT8", ["blueGem"], True, None, None),
    ("MT6 blueGem", "MT6", ["blueGem"], True, None, None),
    ("MT3 redGem", "MT3", ["redGem"], True, None, None),
    ("MT5 blueGem", "MT5", ["blueGem"], True, None, None),
    ("MT4 blueKey", "MT4", ["blueKey"], True, None, None),
    ("MT9 upFloor", "MT9", ["upFloor"], True, None, None),
    ("MT10 blueGem", "MT10", ["blueGem"], False, None, None),
    ("MT7 yellowKey", "MT7", ["yellowKey"], True, None, None),
    ("MT10 redGem", "MT10", ["redGem"], True, None, None),
    ("MT6 yellowKey", "MT6", ["yellowKey"], True, None, None),
    ("MT7 bluePotion", "MT7", ["bluePotion"], True, None, None),
    ("MT8 redKey", "MT8", ["redKey"], True, None, None),
    ("MT10 bluePotion", "MT10", ["bluePotion"], True, None, None),
    ("MT1 bluePotion", "MT1", ["bluePotion"], True, None, None),
    ("MT10 boss", "MT10", ["redDoor"], True, None, None),
]

VARIANTS = [
    (
        "key-red-1f",
        [
            ("MT4 x3y11 yellowKey exact", "MT4", ["yellowKey"], True, {(3, 11)}, MT4_X3Y11_KEY_FORBID),
            ("MT7 redGem", "MT7", ["redGem"], True, None, None),
            ("MT1 blueGem", "MT1", ["blueGem"], True, None, None),
            ("MT3 blueGem", "MT3", ["blueGem"], True, None, None),
        ] + COMMON_SUFFIX,
    ),
    (
        "key-red-3f-1f",
        [
            ("MT4 x3y11 yellowKey exact", "MT4", ["yellowKey"], True, {(3, 11)}, MT4_X3Y11_KEY_FORBID),
            ("MT7 redGem", "MT7", ["redGem"], True, None, None),
            ("MT3 blueGem", "MT3", ["blueGem"], True, None, None),
            ("MT1 blueGem", "MT1", ["blueGem"], True, None, None),
        ] + COMMON_SUFFIX,
    ),
    (
        "key-3f-red-1f",
        [
            ("MT4 x3y11 yellowKey exact", "MT4", ["yellowKey"], True, {(3, 11)}, MT4_X3Y11_KEY_FORBID),
            ("MT3 blueGem", "MT3", ["blueGem"], True, None, None),
            ("MT7 redGem", "MT7", ["redGem"], True, None, None),
            ("MT1 blueGem", "MT1", ["blueGem"], True, None, None),
        ] + COMMON_SUFFIX,
    ),
]


def row_text(row: dict[str, Any]) -> str:
    return (
        f"HP={row['hp']} ATK={row['atk']} DEF={row['def']} "
        f"YK={row['yk']} BK={row['bk']} RK={row['rk']} "
        f"dmg={row['dmg']} door={row['yd']}/{row['bd']}/{row['rd']}"
    )


def compact_label(label: str, fid: str, targets: list[str], flyback: bool) -> str:
    out = f"{fid} {'+'.join(targets)} flyback={flyback}"
    if "x3y11" in label:
        out += " [x3y11 exact]"
    return out


def apply_sequence(start: dict[str, Any], actions: list[tuple[str, str, list[str], bool, set[tuple[int, int]] | None, set[tuple[int, int]] | None]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    ent = start
    chain = [{"label": "phase1 delayed prefix", "compact_label": None, "entry": ent}]
    for label, fid, targets, flyback, require, forbid in actions:
        ent = base.apply_action(
            ent,
            fid,
            targets,
            flyback,
            label,
            require=set(require or ()),
            forbid=set(forbid or ()),
        )
        chain.append({
            "label": label,
            "compact_label": compact_label(label, fid, targets, flyback),
            "entry": ent,
        })
    return ent, chain


def compact_state(ent: dict[str, Any]) -> str:
    row = base.row_from_ent(ent)
    return (
        f"HP={row['hp']} ATK={row['atk']} DEF={row['def']} "
        f"YK={row['yk']} BK={row['bk']} RK={row['rk']} "
        f"dmg={row['dmg']} door={row['yd']}/{row['bd']}/{row['rd']}"
    )


def compact_prefix(final_state: str) -> list[str]:
    lines = open(MAIN_COMPACT_WALK, encoding="utf-8").read().splitlines()
    out = []
    for line in lines:
        if line.startswith("> final:"):
            out.append(f"> final: {final_state}")
            continue
        if line.startswith("## 9."):
            break
        out.append(line)
    while out and out[-1] == "":
        out.pop()
    out.append("")
    return out


def write_compact_walk(title: str, chain: list[dict[str, Any]], out_path: str) -> None:
    final_state = compact_state(chain[-1]["entry"])
    lines = compact_prefix(final_state)
    prev = chain[0]["entry"]
    for idx, item in enumerate(chain[1:], 9):
        ent = item["entry"]
        row = base.row_from_ent(ent)
        prev_row = base.row_from_ent(prev)
        lines.extend([
            f"## {idx}. {item['compact_label']}",
            "",
            f"- {compact_state(ent)}",
            (
                f"- segment dmg={row['dmg'] - prev_row['dmg']} "
                f"door delta={row['yd'] - prev_row['yd']}/"
                f"{row['bd'] - prev_row['bd']}/{row['rd'] - prev_row['rd']}"
            ),
            "",
        ])
        prev = ent
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")


def write_detailed_walk(compact_path: str, detail_path: str) -> None:
    old_in, old_out = detail_walk.IN_WALK, detail_walk.OUT_WALK
    try:
        detail_walk.IN_WALK = compact_path
        detail_walk.OUT_WALK = detail_path
        detail_walk.main()
    finally:
        detail_walk.IN_WALK = old_in
        detail_walk.OUT_WALK = old_out


def main() -> None:
    _hero, maps = load_data()
    blocks = cmp.block_map(maps)
    resources = base.all_resources(maps)
    start, _phase1 = delayed.find_candidate(300)

    rows: list[dict[str, Any]] = []
    chains: dict[str, list[dict[str, Any]]] = {}
    for name, actions in VARIANTS:
        try:
            ent, chain = apply_sequence(start, actions)
        except RuntimeError as exc:
            rows.append({"name": name, "error": str(exc)})
            continue
        seen = base.collected_as_sets(ent)
        row = base.enrich(name, base.row_from_ent(ent), seen, resources)
        rows.append(row)
        chains[name] = [
            {"label": item["label"], "state": base.row_from_ent(item["entry"])}
            for item in chain
        ]
        if name == "key-red-1f":
            write_compact_walk("key-red-1f", chain, MAIN_COMPACT_WALK)
            write_detailed_walk(MAIN_COMPACT_WALK, MAIN_DETAIL_WALK)
        elif name == "key-red-3f-1f":
            write_compact_walk("key-red-3f-1f", chain, BEST_COMPACT_WALK)
            write_detailed_walk(BEST_COMPACT_WALK, BEST_DETAIL_WALK)

    delayed_row, delayed_seen = base.delayed_current(blocks)
    guide_row, guide_seen = base.guide_current(blocks)
    rows.append(base.enrich("current delayed", delayed_row, delayed_seen, resources))
    rows.append(base.enrich("user guide", guide_row, guide_seen, resources))

    data = {"rows": rows, "chains": chains}
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    lines = [
        "# Post-9 Order Variants",
        "",
        "从 delayed phase1 前缀出发，审计 4F 精确补钥匙、7F 红宝石、1F/3F 宝石的顺序差异。",
        "",
        "说明：地图中 4F `x3y10` 是绿史莱姆，黄钥匙在 `x3y11`；当前攻防下打 `x3y10` 不掉血，所以这里记作 `x3y11 yellowKey exact`。",
        "",
        "## Summary",
        "",
        "| 路线 | 最终状态 | old_score | resource_group_score | final_residual_0dmg | final_stock |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in rows:
        if "error" in row:
            lines.append(f"| {row['name']} | FAILED: {row['error']} | - | - | - | - |")
            continue
        lines.append(
            f"| {row['name']} | {row_text(row)} | {row['old_score']} | "
            f"{row['resource_group_score']} | {row['final_residual_value']} | "
            f"{row['final_resource_stock']} |"
        )
    for name, chain in chains.items():
        lines.extend(["", f"## {name}", "", "| step | state |", "|---|---|"])
        for item in chain:
            st = item["state"]
            lines.append(
                f"| {item['label']} | HP={st['hp']} ATK={st['atk']} DEF={st['def']} "
                f"YK={st['yk']} BK={st['bk']} RK={st['rk']} dmg={st['dmg']} "
                f"door={st['yd']}/{st['bd']}/{st['rd']} |"
            )
    os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")

    print(f"wrote {OUT_JSON}")
    print(f"wrote {OUT_MD}")
    for row in rows:
        if "error" in row:
            print(f"{row['name']}: FAILED {row['error']}")
        else:
            print(
                f"{row['name']}: {row_text(row)} old={row['old_score']} "
                f"rg={row['resource_group_score']} finalStock={row['final_resource_stock']}"
            )


if __name__ == "__main__":
    main()
