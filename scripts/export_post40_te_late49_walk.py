#!/usr/bin/env python3
"""Export the current pure-TE late-49 local candidate as a strict walk draft."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC_JSON = ROOT / "outputs" / "results" / "post40_te_late49_probe.json"
OUT_JSON = ROOT / "outputs" / "walkthroughs" / "post40_te_late49_slice5_mid_center_strict_walk.json"
OUT_MD = ROOT / "outputs" / "walkthroughs" / "post40_te_late49_slice5_mid_center_strict_walk_zh.md"


def state_text(s: dict[str, Any]) -> str:
    return (
        f"HP={s['hp']} ATK={s['atk']} DEF={s['def']} "
        f"YK={s['yk']} BK={s['bk']} RK={s['rk']} G={s['gold']} "
        f"{s['floor']} x{s['x']}y{s['y']}"
    )


def delta_text(step: dict[str, Any]) -> str:
    return step.get("delta") or ""


def tools_text(s: dict[str, Any]) -> str:
    keys = [
        "centerFly",
        "upFly",
        "downFly",
        "earthquake",
        "bomb",
        "bigKey",
        "pickaxe",
        "superPotion",
        "snow",
        "cross",
        "knife",
        "coin",
    ]
    parts = []
    for key in keys:
        value = s.get(key)
        if isinstance(value, bool):
            if value:
                parts.append(f"{key}=true")
        elif isinstance(value, int) and value:
            parts.append(f"{key}={value}")
    return ", ".join(parts) if parts else "-"


def load_row(label: str) -> dict[str, Any]:
    data = json.loads(SRC_JSON.read_text(encoding="utf-8"))
    for row in data["rows"]:
        if row["label"] == label:
            return row
    raise SystemExit(f"label not found: {label}")


def build_payload(row: dict[str, Any]) -> dict[str, Any]:
    steps = row["steps"]
    return {
        "ok": bool(row["ok"]),
        "name": "post40_te_late49_slice5_mid_center_strict_walk",
        "status": "local-only; pending strict human-input web verification",
        "source": str(SRC_JSON.relative_to(ROOT)),
        "label": row["label"],
        "objective": "纯净版-TE HP；50F 小偷后使用下楼器到 49F 封印假魔王，再回 50F 通关",
        "strict_web_requirements": {
            "allow_extra_gold": False,
            "auto": {"battle": True, "item": "nopotion", "wall": True},
            "forbidden_operation_api": [
                "core.doAction",
                "core.moveHero",
                "core.setHeroLoc",
                "core.changeFloor",
                "core.flyTo",
                "core.useItem",
                "core.loadData",
            ],
            "allowed_setting_api": "only explicit auto-setting read/write before proof replay",
        },
        "start": steps[0]["before"] if steps else None,
        "final": row["final"],
        "current_floor_final_score": row["current_floor_final_score"],
        "stage_summaries": row["stage_summaries"],
        "errors": row["errors"],
        "steps": steps,
    }


def write_markdown(payload: dict[str, Any], out_md: Path) -> None:
    final = payload["final"]
    score = payload["current_floor_final_score"]
    start = payload["start"]
    lines: list[str] = [
        "# 纯净版-TE post40/slot26 seed tail 本地草案",
        "",
        "## 核心结论",
        "",
        f"- 状态：{payload['status']}",
        "- 注意：本文件不是 4F 起点到 50F 的连续 walk；它只是从本地 slot26/post40 搜索状态继续的尾段草案。",
        "- 正式 4-50 结果必须从 4F 起点连续串接 1区、2区、20F->31F 桥、3区和 4区尾段，并重新 web 复现。",
        "- 约束：金币必须精确匹配；不使用 `--allow-extra-gold`。",
        "- Web 复现限制：只允许真实点击、方向键/左右键、空格确认；禁止直接调用玩法推进 API。",
        "- 自动设置：`battle=true,item=nopotion,wall=true`，用于保留血瓶并记录自动清怪/拾取结果。",
        f"- 起点：`{state_text(start)}`",
        f"- 终点：`{state_text(final)}`",
        f"- 纯伤害 dmg：`{final['dmg']}`；开门 黄/蓝/红=`{final['yd']}/{final['bd']}/{final['rd']}`",
        f"- final-score<=50：`{score['final_score']:g}` "
        f"(stock={score['stock_score']:g}, remaining={score['remaining_value_hp']:g})",
        f"- 重要道具保留：`{tools_text(final)}`",
        "",
        "## final-score 计算",
        "",
        "- 函数：`scripts/floor_final_score.py::current_floor_and_below_final_score`。",
        "- 范围：当前层及其以下，本 walk 为 `floor_limit=50`。",
        "- 库存分：`HP + 50*黄钥匙 + 200*蓝钥匙 + 0.5*金币`。",
        "- 剩余资源：地图中仍存在的黄钥匙、蓝钥匙、血瓶计入；红钥匙、宝石和工具只列数量，不给剩余分。",
        "- 0伤怪金币：只统计仍留在地图上的 0 伤怪。已经自动清掉的怪已从地图删除并进入当前金币，所以不会双算。",
        f"- 剩余物品：`{score['item_counts']}`",
        f"- 剩余 0 伤怪：`{score['zero_enemy_counts']}`，折算 `{score['zero_damage_monster_value_hp']:g}`",
        f"- 重要道具地图剩余：`{score.get('map_tool_counts') or {}}`；持有：`{score.get('held_tool_counts') or {}}`",
        "",
        "## 阶段节点",
        "",
        "| 阶段 | 节点状态 | 本段 dmg | 累计 dmg | stock |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for stage in payload["stage_summaries"]:
        after = stage["after"]
        lines.append(
            f"| {stage['name']} | `{state_text(after)}` | {stage['delta_dmg']} | "
            f"{after['dmg']} | {stage['stock_score']:.1f} |"
        )
    lines.extend(
        [
            "",
            "## 与旧结果对比",
            "",
            "| 结果 | 约束 | 终点 | dmg | final-score | 重要道具/备注 |",
            "| --- | --- | --- | ---: | ---: | --- |",
            "| 当前 late-49 草案 | 不拿 0F 金币；50F 小偷后下楼封 49F；金币精确 | "
            f"`{state_text(final)}` | {final['dmg']} | {score['final_score']:g} | `{tools_text(final)}` |",
            "| 旧 save37 web-verified | save37 续跑；拿幸运金币；非同一 late-49 约束 | "
            "`HP=22264 ATK=418 DEF=517 YK=4 BK=0 RK=0 G=1235 MT50 x6y5` | 27134 | - | "
            "`coin=true, snow=1`; 已 web 验证但不能接到 slot26/late-49 约束 |",
            "| 旧 slot26 post40 mid_center | 本地桥接；拿幸运金币；49F 顺序不同 | "
            "`HP=14564 ATK=431 DEF=525 YK=2 BK=0 RK=0 G=3228 MT50 x6y5` | 34705 | - | "
            "`coin=true, centerFly=2, snow=1`; 仅作非同约束参考 |",
            "",
            "## Web 复现状态",
            "",
            "- 当前浏览器不在本 walk 起点；尚未完成 strict human-input web 复现。",
            "- strict verifier 已要求金币精确匹配，并修正为校验第 1 步之前的起点状态。",
            "- `bigKey`、`snow` 走状态栏真实点击；`centerFly` 走键盘 `3` 后点击目标格。",
            "",
            "## 详细步骤",
            "",
            "| # | 楼层坐标 | 动作 | 数值变化 | 备注 |",
            "| ---: | --- | --- | --- | --- |",
        ]
    )
    for i, step in enumerate(payload["steps"], 1):
        pos = step.get("pos") or [step["after"]["x"], step["after"]["y"]]
        eid = step.get("eid") or ""
        note = (step.get("note") or "").replace("|", "/")
        lines.append(
            f"| {i} | {step['floor']} x{pos[0]}y{pos[1]} | {step['action']} {eid} | "
            f"{delta_text(step)} | {note} |"
        )
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", default="post40_focused_slice5_mid_center")
    parser.add_argument("--out-json", type=Path, default=OUT_JSON)
    parser.add_argument("--out-md", type=Path, default=OUT_MD)
    args = parser.parse_args()
    row = load_row(args.label)
    payload = build_payload(row)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(payload, args.out_md)
    print(f"json={args.out_json}")
    print(f"md={args.out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
