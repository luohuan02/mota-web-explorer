#!/usr/bin/env python3
"""Write a clean slot26 zone-3 walk from replayed macro checkpoints."""

from __future__ import annotations

import copy
import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from scripts.audit import floor_final_score as fs


ROOT = Path(__file__).resolve().parents[2]
MACRO_PATH = ROOT / "scripts" / "search" / "probe_zone3_slot26_sword_macro.py"
OUT_JSON = ROOT / "outputs" / "results" / "zone3_slot26_clean_walk.json"
OUT_MD = ROOT / "outputs" / "reports" / "zone3_slot26_clean_walk.md"
FLOOR_LIMIT = 40
MONSTER_GOLD_FACTOR = 1.0


def load_macro() -> Any:
    spec = importlib.util.spec_from_file_location("zone3_slot26_clean_macro", MACRO_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(MACRO_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


macro = load_macro()
base = macro.b
OUT_JSON_PATH = OUT_JSON
OUT_MD_PATH = OUT_MD


def valid(g: Any) -> bool:
    return not g.errors and g.state["hp"] > 0


def build_r37_center() -> Any:
    g = macro.start_to_right_resources("AA")
    macro.sell(g, 2)
    macro.buy(g, "AA")
    sword = macro.try_sword(g)
    after2 = macro.after_sword_to_2f(sword)
    extra = macro.collect_extra_keys(after2)
    post = copy.deepcopy(extra if valid(extra) else after2)
    macro.buy(post, "DD")
    healed = macro.eat_potions_until(post, 2200, preserve_yk=1)
    pre34 = macro.collect_pre34_keys(healed)
    return macro.to_37_with_34_center(pre34)


def finish_variant(r37_center: Any, first_shop: str = "D", mid_shop: str | None = None) -> Any:
    g = copy.deepcopy(r37_center)
    g = macro.try_take(g, "MT34", 1, 11, "34 left blue potion before 38")
    if first_shop:
        macro.buy(g, first_shop)
    return macro.finish_from_37_center(g, mid_shop=mid_shop)


def summary(g: Any) -> dict[str, Any]:
    score = fs.current_floor_and_below_final_score(
        g,
        FLOOR_LIMIT,
        monster_gold_factor=MONSTER_GOLD_FACTOR,
    )
    return {
        "ok": valid(g),
        "state_text": base.state_line(g),
        "state": g.snapshot(),
        "simple_stock_score": score["stock_score"],
        "remaining_simple_value": base.remaining_simple_value(g),
        "current_floor_final_score": score,
        "errors": list(g.errors),
        "warnings": list(g.warnings),
        "steps": g.steps,
    }


def step_text(step: dict[str, Any]) -> str:
    x, y = step.get("pos", ["?", "?"])
    eid = step.get("eid") or ""
    delta = f" [{step['delta']}]" if step.get("delta") else ""
    return f"{step.get('floor')} x{x}y{y} {step.get('action')} {eid}{delta}".rstrip()


def score_line(row: dict[str, Any]) -> str:
    score = row["current_floor_final_score"]
    return (
        f"stock={score['stock_score']:g}；"
        f"剩余物品={score['item_value_hp']:g}；"
        f"0伤怪金币={score['zero_damage_monster_value_hp']:g}；"
        f"final-score<=40={score['final_score']:g}"
    )


def tool_line(row: dict[str, Any]) -> str:
    score = row["current_floor_final_score"]
    return (
        f"held={score['held_tool_counts'] or {}}；"
        f"map={score['map_tool_counts'] or {}}"
    )


def write_report(rows: dict[str, Any]) -> None:
    OUT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    primary = rows["boss_8buy_def"]
    lines = [
        "# 三区 slot26 clean walk（8买DEF，39F中途回商店）",
        "",
        "## 结论",
        f"- 主线状态：`{primary['state_text']}`",
        f"- 纯伤害 dmg：`{primary['state']['dmg']}`；开门：`{primary['state']['yd']}/{primary['state']['bd']}/{primary['state']['rd']}`",
        f"- current-floor final-score：{score_line(primary)}",
        f"- 重要道具剩余：{tool_line(primary)}",
        f"- errors/warnings：`{len(primary['errors'])}` / `{len(primary['warnings'])}`",
        "",
        "## 对照状态",
        "| 路线 | 状态 | dmg | final-score<=40 | 重要道具剩余 | errors |",
        "| --- | --- | ---: | ---: | --- | ---: |",
    ]
    for key, title in [
        ("boss_7buy_def", "7买DEF，boss后停40F上楼口"),
        ("boss_8buy_def", "8买DEF，39F红宝石后回商店"),
        ("boss_8buy_atk", "8买ATK，39F红宝石后回商店"),
    ]:
        row = rows[key]
        score = row["current_floor_final_score"]
        lines.append(
            f"| {title} | `{row['state_text']}` | {row['state']['dmg']} | "
            f"{score['final_score']:g} | {tool_line(row)} | {len(row['errors'])} |"
        )
    lines.extend(
        [
            "",
            "## 计分说明",
            "- final-score<=40 由 `scripts/floor_final_score.py::current_floor_and_below_final_score` 计算。",
            "- 已清掉的 0 伤怪只体现在当前金币里；未清的 0 伤怪仍在剩余地图块里，计入剩余 0 伤怪金币，因此不会双算。",
            "- 本 40F 口径把未来双倍金币清扫作为既定收益，剩余 0 伤怪金币按 `money*1.0` 计；非 0 伤怪只列审计，不进分。",
            "",
            "## 关键顺序",
            "- 34F中间8怪和奖励必须在第一次从33F进入34F上侧时处理，不能等飞回34F后再做。",
            "- 第一把蓝钥匙取MT32 x11y7，否则37F蓝门和39F谜题蓝门不够。",
            "- 第8次属性购买放在39F红宝石后；此时G=961，够花920买DEF，并且中心对称飞行器还没使用，可以回39F继续进40F。",
            "- 40F先主动清12怪，再触发x6y7事件；boss后只取钥匙和宝石，不取血瓶，停MT40 x6y1。",
            "",
            "## 详细Walk",
        ]
    )
    for i, step in enumerate(primary["steps"], 1):
        lines.append(f"{i:03d}. {step_text(step)}")
    OUT_MD_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    global OUT_JSON_PATH, OUT_MD_PATH
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", type=Path, default=base.DEFAULT_SNAPSHOT)
    parser.add_argument("--out-json", type=Path, default=OUT_JSON)
    parser.add_argument("--out-md", type=Path, default=OUT_MD)
    args = parser.parse_args()
    macro.set_snapshot(args.snapshot)
    OUT_JSON_PATH = args.out_json
    OUT_MD_PATH = args.out_md

    r37_center = build_r37_center()
    rows = {
        "r37_center": summary(r37_center),
        "boss_7buy_def": summary(finish_variant(r37_center, first_shop="D", mid_shop=None)),
        "boss_8buy_def": summary(finish_variant(r37_center, first_shop="D", mid_shop="D")),
        "boss_8buy_atk": summary(finish_variant(r37_center, first_shop="D", mid_shop="A")),
    }
    write_report(rows)
    for key, row in rows.items():
        score = row["current_floor_final_score"]
        print(key, row["state_text"], f"final_score<=40={score['final_score']:g}", "errors", len(row["errors"]))
    print(f"snapshot {args.snapshot}")
    print(f"wrote {OUT_JSON_PATH}")
    print(f"wrote {OUT_MD_PATH}")
    return 0 if all(row["ok"] for row in rows.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
