#!/usr/bin/env python3
"""Audit zone-2 route path ordering and rejected timing probes."""

from __future__ import annotations

import json
import os
import sys
from copy import deepcopy
from typing import Any


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
SCRIPT_DIR = os.path.join(ROOT, "scripts")
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)
os.chdir(ROOT)

import replay_zone2_guide_route as zone2  # noqa: E402


def route_summary(result: dict[str, Any]) -> dict[str, Any]:
    final = result["final"]
    strict_errors = [msg for msg in result["errors"] if "strict path blocked" in msg]
    return {
        "label": result["label"],
        "final": final,
        "errors": result["errors"],
        "warnings": result["warnings"],
        "strict_errors": strict_errors,
        "state": zone2.state_text(final),
        "dmg": final["dmg"],
        "door": f"{final['yd']}/{final['bd']}/{final['rd']}",
    }


def replay(
    label: str,
    state: dict[str, Any],
    cleared: dict[str, set[tuple[int, int]]],
    floors: dict[str, zone2.Floor],
    enemies: dict[str, dict[str, Any]],
    options: dict[str, Any] | None = None,
    validate_paths: bool = False,
) -> dict[str, Any]:
    rep = zone2.Replay(
        label,
        deepcopy(state),
        deepcopy(floors),
        enemies,
        deepcopy(cleared),
        validate_paths=validate_paths,
    )
    return zone2.run_route_direct(rep, options or {})


def main() -> None:
    floors, enemies = zone2.load_floors()
    rows: list[dict[str, Any]] = []
    delay_rows: list[dict[str, Any]] = []
    for label, state, cleared in zone2.scenario_states():
        rows.append(route_summary(replay(label, state, cleared, floors, enemies, validate_paths=True)))
        delay_rows.append(
            route_summary(
                replay(
                    f"{label}:delay_mt11_shield",
                    state,
                    cleared,
                    floors,
                    enemies,
                    options={"delay_mt11_shield": True},
                    validate_paths=True,
                )
            )
        )

    os.makedirs(os.path.join("outputs", "results"), exist_ok=True)
    os.makedirs(os.path.join("outputs", "reports"), exist_ok=True)
    out_json = os.path.join("outputs", "results", "zone2_path_audit.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump({"strict_path_audit": rows, "delay_mt11_shield_probe": delay_rows}, f, ensure_ascii=False, indent=2)

    lines = ["# 二区路径合法性审计", ""]
    lines.append("严格路径审计会检查同层步骤不能穿过尚未清理的怪物、门、物品或暗墙。")
    lines.append("")
    lines.append("## 严格路径审计")
    lines.append("")
    lines.append("| 路线 | 最终状态 | 错误 | 严格路径错误 |")
    lines.append("|---|---|---:|---:|")
    for row in rows:
        final = row["final"]
        lines.append(
            f"| {row['label']} | {row['state']} dmg={final['dmg']} door={row['door']} | "
            f"{len(row['errors'])} | {len(row['strict_errors'])} |"
        )
    lines.append("")
    lines.append("## 延后 11F 盾探针")
    lines.append("")
    lines.append("探针含义：买 15F 蓝钥匙前先跳过 MT11 x2y9，等攻击到 68 后再回盾房。")
    lines.append("")
    lines.append("| 路线 | 最终状态 | 错误 | 前几个错误 |")
    lines.append("|---|---|---:|---|")
    for row in delay_rows:
        first = "; ".join(row["errors"][:2])
        lines.append(f"| {row['label']} | {row['state']} dmg={row['dmg']} door={row['door']} | {len(row['errors'])} | {first} |")

    out_md = os.path.join("outputs", "reports", "zone2_path_audit.md")
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")

    print(f"已写入 {out_json}")
    print(f"已写入 {out_md}")
    for row in rows:
        print(f"{row['label']}: 错误={len(row['errors'])} 严格路径错误={len(row['strict_errors'])}")
    for row in delay_rows:
        print(f"{row['label']}: hp={row['final']['hp']} 错误={len(row['errors'])}")


if __name__ == "__main__":
    main()
