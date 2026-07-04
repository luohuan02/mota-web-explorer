#!/usr/bin/env python3
"""Rebuild and score the 2026-06-29 deadline Zone-3 candidate.

This is intentionally local-only. The candidate reuses the 39F center-fly
event after an existing 40F boss clear, so it must be strict-web verified
before promotion.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import floor_final_score as fs


ROOT = Path(__file__).resolve().parents[1]
SEEDED_PATH = ROOT / "scripts" / "search_zone3_slot26_seeded.py"
CLEAN_JSON = ROOT / "outputs" / "results" / "zone3_slot26_clean_walk.json"
DIFF_JSON = ROOT / "outputs" / "results" / "zone3_remaining_diff.json"
OUT_JSON = ROOT / "outputs" / "results" / "zone3_deadline_candidate_rebuild.json"
OUT_MD = ROOT / "outputs" / "reports" / "zone3_deadline_candidate_rebuild.md"
FLOOR_LIMIT = 40
MONSTER_GOLD_FACTOR = 1.0


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


seeded = load_module("deadline_seeded", SEEDED_PATH)
macro = seeded.macro
base = seeded.base


def valid(g: Any) -> bool:
    return not g.errors and g.state["hp"] > 0


def rebuild_candidate() -> Any:
    """Rebuild trace from zone3_slot26_seeded_deadline_slice1 best_goal."""

    seeded.install_seeded_guidance()

    # Trace 1:
    # seed after2 open=AA sell=2 late=AA farms=[] postSell=0 postOrder=DD
    # hp=2200 finish:potionD_midD
    base0 = macro.start_to_right_resources("AA")
    farmed = macro.farm_targets(base0, [])
    g = copy.deepcopy(farmed)
    macro.sell(g, 2)
    macro.buy(g, "AA")
    sword = macro.try_sword(g)
    after2 = macro.after_sword_to_2f(sword)
    extra = macro.collect_extra_keys(after2)
    post = copy.deepcopy(extra)
    macro.sell(post, 0)
    macro.buy(post, "DD")
    healed = macro.eat_potions_until(post, 2200, preserve_yk=1)
    pre34 = macro.collect_pre34_keys(healed)
    r37 = macro.to_37_with_34_center(pre34 if valid(pre34) else healed)
    done = copy.deepcopy(r37)
    done = macro.try_take(done, "MT34", 1, 11, "34 left blue potion before 38")
    macro.buy(done, "D")
    done = macro.finish_from_37_center(done, mid_shop="D")

    # Trace 2-5 from the search slice.
    puzzle = next(a for a in base.special_actions(done) if a["label"] == "MT39:event:centerFlyPuzzle")
    puzzle["apply"](done)
    base.move_to(done, "MT32", 2, 2, "search redGem")
    base.move_to(done, "MT32", 1, 1, "search blueGem")
    center = next(a for a in base.special_actions(done) if a["label"] == "MT40:use:centerFly")
    center["apply"](done)
    return base.finish_goal_candidate(done)


def summarize_game(g: Any) -> dict[str, Any]:
    score = fs.current_floor_and_below_final_score(
        g,
        FLOOR_LIMIT,
        monster_gold_factor=MONSTER_GOLD_FACTOR,
    )
    return {
        "ok": valid(g),
        "state_text": base.state_line(g),
        "state": g.snapshot(),
        "errors": list(g.errors),
        "warnings": list(g.warnings),
        "trace": [
            "seed after2 open=AA sell=2 late=AA farms=[] postSell=0 postOrder=DD hp=2200 finish:potionD_midD",
            "MT39:event:centerFlyPuzzle",
            "MT32:x2y2:redGem",
            "MT32:x1y1:blueGem",
            "MT40:use:centerFly",
        ],
        "current_floor_final_score": score,
        "steps": g.steps,
    }


def load_clean_rows() -> dict[str, Any]:
    if not CLEAN_JSON.exists():
        return {}
    data = json.loads(CLEAN_JSON.read_text(encoding="utf-8"))
    out: dict[str, Any] = {}
    for key in ("boss_7buy_def", "boss_8buy_def", "boss_8buy_atk"):
        if key in data:
            row = data[key]
            out[key] = {
                "state_text": row["state_text"],
                "state": row["state"],
                "current_floor_final_score": row["current_floor_final_score"],
                "errors": row["errors"],
            }
    return out


def load_guide_row() -> dict[str, Any] | None:
    if not DIFF_JSON.exists():
        return None
    data = json.loads(DIFF_JSON.read_text(encoding="utf-8"))
    score = data.get("current_floor_scores", {}).get("guide")
    state = data.get("states", {}).get("guide")
    if not score or not state:
        return None
    return {
        "state_text": state["state_text"],
        "state": {"dmg": state["dmg"]},
        "current_floor_final_score": score,
        "errors": state.get("errors", []),
    }


def tool_text(score: dict[str, Any]) -> str:
    return f"held={score.get('held_tool_counts') or {}}; map={score.get('map_tool_counts') or {}}"


def row_line(name: str, row: dict[str, Any]) -> str:
    score = row["current_floor_final_score"]
    state = row.get("state", {})
    return (
        f"| {name} | `{row['state_text']}` | {state.get('dmg', '')} | "
        f"{score['stock_score']:g} | {score['remaining_value_hp']:g} | "
        f"{score['final_score']:g} | {tool_text(score)} | {len(row.get('errors') or [])} |"
    )


def write_outputs(candidate: dict[str, Any], comparisons: dict[str, Any]) -> None:
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "note": "local-only candidate; strict web verification pending",
        "risk": "relies on repeating the 39F centerFly event after the 40F boss route",
        "floor_limit": FLOOR_LIMIT,
        "monster_gold_factor": MONSTER_GOLD_FACTOR,
        "candidate": candidate,
        "comparisons": comparisons,
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Zone3 Deadline Candidate Rebuild",
        "",
        "- 状态：本地重建通过；web strict 未验证。",
        "- 风险：该候选在 40F boss 后回 39F 再触发/取得中心对称飞行器，必须实机验证是否可重复。",
        "- 自动设置要求：strict web proof 前必须通过 UI/存档保证 `battle=true,item=nopotion,wall=true`，不得用 API 改 flag。",
        "",
        "## 对比",
        "| 路线 | 状态 | dmg | stock | 剩余价值 | final-score<=40 | 重要道具 | errors |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- | ---: |",
        row_line("deadline local candidate", candidate),
    ]
    for key, title in [
        ("boss_7buy_def", "slot26 clean 7买DEF"),
        ("boss_8buy_def", "slot26 clean 8买DEF"),
        ("boss_8buy_atk", "slot26 clean 8买ATK"),
        ("guide", "guide/save36 40F"),
    ]:
        row = comparisons.get(key)
        if row:
            lines.append(row_line(title, row))
    lines.extend(
        [
            "",
            "## 计分口径",
            "- `final-score<=40 = current stock + remaining item value + remaining zero-damage monster value`。",
            "- 已清 0 伤怪只在当前金币中；未清 0 伤怪仍在地图剩余块中，因此不会双算。",
            "- 本 40F 审计按未来双倍金币清扫计，剩余 0 伤怪金币使用 `money*1.0`。",
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    candidate_game = rebuild_candidate()
    candidate = summarize_game(candidate_game)
    comparisons = load_clean_rows()
    guide = load_guide_row()
    if guide:
        comparisons["guide"] = guide
    write_outputs(candidate, comparisons)
    print(candidate["state_text"])
    score = candidate["current_floor_final_score"]
    print(f"final_score<=40={score['final_score']:g}")
    print(f"wrote {OUT_JSON}")
    print(f"wrote {OUT_MD}")
    return 0 if candidate["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
