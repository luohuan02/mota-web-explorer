#!/usr/bin/env python3
"""Audit taking the 7F red gem before the 1F blue gem.

This targeted check starts from the current delayed phase1 prefix, forces
`MT7 redGem`, refills with the MT4 x3y10 yellow-key action, then follows the
same broad suffix used by the current delayed continuation.  It exists to make
the "7F red first" hypothesis reproducible without changing the main search.
"""

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
from src.solver.full_search import load_data


OUT_JSON = os.path.join("outputs", "results", "mt7_red_first_variant.json")
OUT_MD = os.path.join("outputs", "reports", "mt7_red_first_variant.md")


def row_text(row: dict[str, Any]) -> str:
    return (
        f"HP={row['hp']} ATK={row['atk']} DEF={row['def']} "
        f"YK={row['yk']} BK={row['bk']} RK={row['rk']} "
        f"dmg={row['dmg']} door={row['yd']}/{row['bd']}/{row['rd']}"
    )


def build_mt7_first() -> tuple[dict[str, Any], list[tuple[str, dict[str, Any]]]]:
    ent, _phase1 = delayed.find_candidate(300)
    chain = [("phase1 delayed prefix", ent)]
    actions = [
        ("MT7 redGem first", "MT7", ["redGem"], True, None, None),
        ("MT4 x3y10 yellowKey refill", "MT4", ["yellowKey"], True, {(3, 10)}, None),
        ("MT1 blueGem after MT7 red", "MT1", ["blueGem"], True, None, None),
        ("MT3 blueGem", "MT3", ["blueGem"], True, None, None),
        ("MT8 blueGem", "MT8", ["blueGem"], True, None, None),
        ("MT6 blueGem", "MT6", ["blueGem"], True, None, None),
        ("MT3 redGem", "MT3", ["redGem"], True, None, None),
        ("MT5 blueGem", "MT5", ["blueGem"], True, None, None),
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
        chain.append((label, ent))
    return ent, chain


def main() -> None:
    _hero, maps = load_data()
    blocks = cmp.block_map(maps)
    resources = base.all_resources(maps)

    variant_ent, chain = build_mt7_first()
    variant_seen = base.collected_as_sets(variant_ent)
    delayed_row, delayed_seen = base.delayed_current(blocks)
    guide_row, guide_seen = base.guide_current(blocks)

    rows = [
        base.enrich("mt7-red-first audit", base.row_from_ent(variant_ent), variant_seen, resources),
        base.enrich("current delayed", delayed_row, delayed_seen, resources),
        base.enrich("user guide", guide_row, guide_seen, resources),
    ]
    data = {
        "rows": rows,
        "chain": [{"label": label, "state": base.row_from_ent(ent)} for label, ent in chain],
        "notes": [
            "This is a forced audit branch, not a broad-search replacement.",
            "The MT4 x3y10 yellow-key action may collect adjacent MT4 key-pocket resources under the current floor-search action abstraction.",
        ],
    }
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    lines = [
        "# MT7 Red First Variant Audit",
        "",
        "这个审计从 delayed phase1 前缀出发，强制先拿 `7F redGem`，再用 `4F x3y10 yellowKey` 补钥匙，然后走当前后缀。",
        "",
        "## Result",
        "",
        "| 路线 | 最终状态 | old_score | resource_group_score | final_residual_0dmg | final_stock |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['name']} | {row_text(row)} | {row['old_score']} | "
            f"{row['resource_group_score']} | {row['final_residual_value']} | "
            f"{row['final_resource_stock']} |"
        )
    lines.extend([
        "",
        "## Step Audit",
        "",
        "| step | state |",
        "|---|---|",
    ])
    for label, ent in chain:
        lines.append(f"| {label} | {base.state_text(ent)} |")
    lines.extend([
        "",
        "## Note",
        "",
        "- 这条强制分支验证的是当前 action 抽象下的实际结果；其中 `MT4 x3y10 yellowKey` 可能顺手收走 4F 左侧钥匙口袋。",
        "- 若要测试只拿 `x3y10` 且不收走相邻口袋，需要把 floor action 进一步细分成坐标级资源包。",
    ])
    os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")

    print(f"wrote {OUT_JSON}")
    print(f"wrote {OUT_MD}")
    for row in rows:
        print(
            f"{row['name']}: {row_text(row)} old={row['old_score']} "
            f"rg={row['resource_group_score']} finalStock={row['final_resource_stock']}"
        )


if __name__ == "__main__":
    main()
