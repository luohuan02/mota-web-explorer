#!/usr/bin/env python3
"""Compare <=40F remaining resources after guide and slot26 40F routes."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from scripts.audit import floor_final_score as fs


ROOT = Path(__file__).resolve().parents[2]
GUIDE_PATH = ROOT / "scripts" / "search" / "find_zone3_quick_pass_walk.py"
CLEAN_PATH = ROOT / "scripts" / "report_zone3_slot26_clean_walk.py"
OUT_JSON = ROOT / "outputs" / "results" / "zone3_remaining_diff.json"
OUT_MD = ROOT / "outputs" / "reports" / "zone3_remaining_diff.md"
FLOOR_LIMIT = 40
# By the project Zone-3 convention, <=40F zero-damage monsters are normally
# left for the later double-gold sweep, so each remaining G is worth 1 HP-score.
MONSTER_GOLD_FACTOR = 1.0


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def floor_no(fid: str) -> int:
    return int(fid[2:])


def state_line(g: Any) -> str:
    s = g.state
    return (
        f"HP={s['hp']} ATK={s['atk']} DEF={s['def']} "
        f"YK={s['yk']} BK={s['bk']} RK={s['rk']} G={s['gold']} "
        f"{s['floor']} x{s['x']}y{s['y']} dmg={s['dmg']} "
        f"door={s['yd']}/{s['bd']}/{s['rd']} shop={s['times1']}"
    )


def build_runs() -> dict[str, Any]:
    guide_mod = load_module("zone3_guide_quick_diff", GUIDE_PATH)
    guide = guide_mod.generate()

    clean_mod = load_module("zone3_slot26_clean_diff", CLEAN_PATH)
    r37_center = clean_mod.build_r37_center()
    return {
        "guide": guide,
        "boss_7buy_def": clean_mod.finish_variant(r37_center, first_shop="D", mid_shop=None),
        "boss_8buy_def": clean_mod.finish_variant(r37_center, first_shop="D", mid_shop="D"),
        "boss_8buy_atk": clean_mod.finish_variant(r37_center, first_shop="D", mid_shop="A"),
    }


def collect_resources(g: Any) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for rec in fs.resource_rows(g, FLOOR_LIMIT, monster_gold_factor=MONSTER_GOLD_FACTOR):
        key = f"{floor_no(rec['floor']):02d}:{rec['x']:02d}:{rec['y']:02d}"
        rows[key] = rec
    return rows


def signature(rec: dict[str, Any] | None) -> tuple[Any, ...] | None:
    if rec is None:
        return None
    if rec["kind"] == "enemy":
        return (rec["kind"], rec["eid"], rec["damage"], rec["zero_damage"], rec["value_hp"])
    return (rec["kind"], rec["eid"], rec["value_hp"])


def display(rec: dict[str, Any] | None) -> str:
    if rec is None:
        return "-"
    if rec["kind"] == "item":
        return f"item:{rec['eid']} v={float(rec['value_hp']):g}"
    damage = rec["damage"]
    damage_text = "0伤" if rec["zero_damage"] else f"伤{damage}"
    return f"enemy:{rec['eid']} G={rec['money']} {damage_text} v={float(rec['value_hp']):g}"


def delta(a: float, b: float) -> str:
    return f"{b - a:+g}"


def counts_delta(base: dict[str, int], other: dict[str, int]) -> str:
    parts: list[str] = []
    for key in sorted(set(base) | set(other)):
        diff = other.get(key, 0) - base.get(key, 0)
        if diff:
            parts.append(f"{key}:{diff:+d}")
    return ", ".join(parts) if parts else "无"


def tool_text(score: dict[str, Any]) -> str:
    bits = []
    held = score.get("held_tool_counts") or {}
    on_map = score.get("map_tool_counts") or {}
    if held:
        bits.append(f"held={held}")
    if on_map:
        bits.append(f"map={on_map}")
    return "<br>".join(bits) if bits else "-"


def build_report() -> dict[str, Any]:
    runs = build_runs()
    resources = {name: collect_resources(g) for name, g in runs.items()}
    scores = {
        name: fs.current_floor_and_below_final_score(
            g,
            FLOOR_LIMIT,
            monster_gold_factor=MONSTER_GOLD_FACTOR,
        )
        for name, g in runs.items()
    }
    names = ["guide", "boss_7buy_def", "boss_8buy_def", "boss_8buy_atk"]
    all_keys = sorted(set().union(*(set(r.keys()) for r in resources.values())))
    diff_rows = []
    for key in all_keys:
        sigs = [signature(resources[name].get(key)) for name in names]
        if len(set(sigs)) <= 1:
            continue
        floor_no_s, x_s, y_s = key.split(":")
        diff_rows.append(
            {
                "key": key,
                "floor": f"MT{int(floor_no_s)}",
                "x": int(x_s),
                "y": int(y_s),
                **{name: resources[name].get(key) for name in names},
            }
        )

    states = {}
    for name, g in runs.items():
        states[name] = {
            "ok": not g.errors and g.state["hp"] > 0,
            "state_text": state_line(g),
            "dmg": g.state["dmg"],
            "errors": list(g.errors),
            "warnings": list(g.warnings),
        }

    return {
        "note": "guide uses find_zone3_quick_pass_walk.py from slot36; boss_* routes use slot26 clean replay.",
        "value_model": (
            "final-score<=40 = current stock + remaining item value + remaining zero-damage monster value. "
            "Current stock uses 1YK=50HP, 1BK=200HP, current 100G=50HP. "
            "For this 40F audit, remaining zero-damage monster gold uses factor 1.0 HP-score for the later double-gold sweep. "
            "Nonzero-damage monsters are listed but excluded; redKey/gems/tools are listed with value_hp=0."
        ),
        "floor_limit": FLOOR_LIMIT,
        "monster_gold_factor": MONSTER_GOLD_FACTOR,
        "states": states,
        "current_floor_scores": scores,
        "diff_rows": diff_rows,
    }


def write_outputs(data: dict[str, Any]) -> None:
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    names = ["guide", "boss_7buy_def", "boss_8buy_def", "boss_8buy_atk"]
    titles = {
        "guide": "攻略通40",
        "boss_7buy_def": "slot26 7买DEF",
        "boss_8buy_def": "slot26 8买DEF",
        "boss_8buy_atk": "slot26 8买ATK",
    }
    lines = [
        "# 三区40F剩余资源与 final-score 对比",
        "",
        f"- 说明：{data['note']}",
        f"- 价值模型：{data['value_model']}",
        f"- 差异行数：`{len(data['diff_rows'])}`",
        "",
        "## 状态汇总",
        "| 路线 | 状态 | dmg | stock | 剩余物品 | 0伤怪金币 | final-score<=40 | 重要道具剩余 |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for name in names:
        state = data["states"][name]
        score = data["current_floor_scores"][name]
        lines.append(
            f"| {titles[name]} | `{state['state_text']}` | {state['dmg']} | "
            f"{score['stock_score']:g} | {score['item_value_hp']:g} | "
            f"{score['zero_damage_monster_value_hp']:g} | {score['final_score']:g} | {tool_text(score)} |"
        )

    guide_score = data["current_floor_scores"]["guide"]
    guide_stock = guide_score["stock_score"]
    lines.extend(
        [
            "",
            "## 相对攻略通40",
            "| 路线 | stock差 | 剩余价值差 | final-score差 | item数量差 | enemy数量差 | 0伤enemy数量差 |",
            "| --- | ---: | ---: | ---: | --- | --- | --- |",
        ]
    )
    for name in names[1:]:
        score = data["current_floor_scores"][name]
        lines.append(
            f"| {titles[name]} | {delta(guide_stock, score['stock_score'])} | "
            f"{delta(guide_score['remaining_value_hp'], score['remaining_value_hp'])} | "
            f"{delta(guide_score['final_score'], score['final_score'])} | "
            f"{counts_delta(guide_score['item_counts'], score['item_counts'])} | "
            f"{counts_delta(guide_score['enemy_counts'], score['enemy_counts'])} | "
            f"{counts_delta(guide_score['zero_enemy_counts'], score['zero_enemy_counts'])} |"
        )

    lines.extend(
        [
            "",
            "## 全部剩余资源差异",
            "| 坐标 | 攻略通40 | slot26 7买DEF | slot26 8买DEF | slot26 8买ATK |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for row in data["diff_rows"]:
        coord = f"{row['floor']} x{row['x']}y{row['y']}"
        lines.append(
            f"| `{coord}` | {display(row.get('guide'))} | {display(row.get('boss_7buy_def'))} | "
            f"{display(row.get('boss_8buy_def'))} | {display(row.get('boss_8buy_atk'))} |"
        )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    data = build_report()
    write_outputs(data)
    print(f"diff_rows={len(data['diff_rows'])}")
    for name, state in data["states"].items():
        score = data["current_floor_scores"][name]
        print(
            name,
            state["state_text"],
            f"final_score<=40={score['final_score']:g}",
            "errors",
            len(state["errors"]),
        )
    print(f"wrote {OUT_JSON}")
    print(f"wrote {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
