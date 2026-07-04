#!/usr/bin/env python3
"""Summarize the first 4F-10F boss probes under auto-setting assumptions."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

USER_DEF_JSON = ROOT / "outputs" / "results" / "zone1_first_probe_user_def_before_key_auto.json"
BLUE_UP_JSON = ROOT / "outputs" / "results" / "zone1_first_probe_blue_up_auto.json"
NO_BLUE_JSON = ROOT / "outputs" / "results" / "taptap244_zone1_probe_first_auto.json"
CURRENT_BEST_JSON = ROOT / "best" / "current_best_boss_summary.json"
GUIDE_WALK = ROOT / "best" / "guide_boss_walk.md"
CURRENT_BEST_WALK = ROOT / "best" / "current_best_boss_walk.md"

OUT_REPORT = ROOT / "outputs" / "reports" / "zone1_first_auto_exploration_summary.md"
OUT_WALK = ROOT / "outputs" / "walkthroughs" / "zone1_first_auto_current_best_walk.md"


STATE_RE = re.compile(
    r"HP=(?P<hp>-?\d+) ATK=(?P<atk>\d+) DEF=(?P<def>\d+) "
    r"YK=(?P<yk>-?\d+) BK=(?P<bk>-?\d+) RK=(?P<rk>-?\d+) "
    r"G=(?P<gold>-?\d+) dmg=(?P<dmg>\d+) "
    r"door=(?P<yd>\d+)/(?P<bd>\d+)/(?P<rd>\d+) "
    r"final-score=(?P<final_score>\d+(?:\.\d+)?)"
)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def fmt_score(value: Any) -> str:
    if value is None:
        return "-"
    value = float(value)
    return str(int(value)) if abs(value - int(value)) < 1e-9 else f"{value:.1f}"


def state_text(row: dict[str, Any] | None) -> str:
    if not row:
        return "-"
    return (
        f"HP={row['hp']} ATK={row['atk']} DEF={row['def']} "
        f"YK={row['yk']} BK={row['bk']} RK={row.get('rk', 0)} "
        f"G={row['gold']} dmg={row['dmg']} "
        f"door={row['yd']}/{row['bd']}/{row['rd']}"
    )


def guide_record() -> dict[str, Any]:
    text = GUIDE_WALK.read_text(encoding="utf-8")
    m = STATE_RE.search(text)
    if not m:
        raise RuntimeError(f"cannot parse guide baseline from {GUIDE_WALK}")
    row = {k: int(v) for k, v in m.groupdict().items() if k != "final_score"}
    row["final_score"] = float(m.group("final_score"))
    return row


def candidate_rows() -> list[dict[str, str]]:
    current_best = load_json(CURRENT_BEST_JSON)["summary"]
    user_def = load_json(USER_DEF_JSON)["best_boss"]
    blue_up = load_json(BLUE_UP_JSON)["best_boss"]
    no_blue = load_json(NO_BLUE_JSON)

    rows: list[dict[str, str]] = [
        {
            "name": "攻略线 baseline",
            "branch": "guide",
            "mt9": "攻略固定上楼",
            "boss": state_text(guide_record()),
            "score": fmt_score(guide_record()["final_score"]),
            "source": "best/guide_boss_walk.md",
        },
        {
            "name": "当前 best 记录",
            "branch": "tracked current best",
            "mt9": "MT9_BLUE_UP",
            "boss": state_text(current_best),
            "score": fmt_score(current_best["final_score"]),
            "source": "best/current_best_boss_summary.json",
        },
        {
            "name": "延后最优复跑",
            "branch": "user-def-before-key",
            "mt9": "MT9_BLUE_UP",
            "boss": state_text(user_def),
            "score": fmt_score(user_def["final_score"]),
            "source": "outputs/results/zone1_first_probe_user_def_before_key_auto.json",
        },
        {
            "name": "蓝门固定顺序",
            "branch": "blue-up",
            "mt9": "MT9_BLUE_UP",
            "boss": state_text(blue_up),
            "score": fmt_score(blue_up["final_score"]),
            "source": "outputs/results/zone1_first_probe_blue_up_auto.json",
        },
    ]
    for result in no_blue["results"]:
        boss = result.get("boss")
        rows.append(
            {
                "name": result["name"],
                "branch": "TapTap244 / 省蓝钥匙",
                "mt9": "MT9_NO_BLUE_UP" if boss else "MT9_NO_BLUE_UP 失败",
                "boss": state_text(boss),
                "score": fmt_score(boss.get("final_score") if boss else None),
                "source": "outputs/results/taptap244_zone1_probe_first_auto.json",
            }
        )
    return rows


def write_report() -> None:
    rows = candidate_rows()
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# 1区 4F-10F Boss 首轮自动设置探索",
        "",
        "## 自动设置口径",
        "",
        "- `__auto__.battle=true`：实机可自动清 0 伤怪；本地 replay 仍保留杀怪和金币计数。",
        "- `__auto__.item=\"nopotion\"`：自动拾取非血瓶物品；血瓶不视为自动收益。",
        "- `__auto__.wall=true`：自动开暗墙/岩浆；本轮 4F-10F boss 候选没有依赖岩浆清理。",
        "- walk 中的 `redPotion` / `bluePotion` 是显式路线动作或补血动作，不是自动拾取血瓶。",
        "",
        "## 候选对比",
        "",
        "| 候选 | 分支 | 9F 处理 | Boss 后状态 | final-score | 保存位置 |",
        "|---|---|---|---|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['name']} | {row['branch']} | {row['mt9']} | "
            f"{row['boss']} | {row['score']} | `{row['source']}` |"
        )

    lines.extend(
        [
            "",
            "## 初步结论",
            "",
            "- 本轮复跑中，`user-def-before-key` 延后最优线复现当前最高 `1376.5`，与 tracked current best 一致。",
            "- `blue-up` 固定顺序可到 Boss，但低 `15 HP / 15 score`。",
            "- `MT9_NO_BLUE_UP` 省蓝钥匙候选已保存；能到 Boss 的最好分支为 `1173.5`，目前明显低于 current best，但保留作为后续 1区/2区接续对照。",
            "- `mt7_yellow_merchant_right_pocket` 和 `mt7_merchant_before_redkey` 在当前脚本约束下不能完成到 Boss；`hp_fix` 可完成但分数较低。",
            "",
            "## Walk 输出",
            "",
            f"- 自动设置口径版 current best walk：`{OUT_WALK.relative_to(ROOT)}`",
            "- 9F 省蓝钥匙候选暂为 compact replay 表，详见 `outputs/reports/taptap244_zone1_probe_first_auto.md`。",
            "",
            "## 本轮校验",
            "",
            "```powershell",
            "python -m py_compile scripts\\probe_mt7_red_first_swap_sequence.py scripts\\probe_taptap244_zone1.py scripts\\report_zone1_first_auto_exploration.py",
            "python scripts\\probe_mt7_red_first_swap_sequence.py --variant user-def-before-key --beam 160 --out-json outputs\\results\\zone1_first_probe_user_def_before_key_auto.json --out-md outputs\\reports\\zone1_first_probe_user_def_before_key_auto.md",
            "python scripts\\probe_mt7_red_first_swap_sequence.py --variant blue-up --beam 160 --out-json outputs\\results\\zone1_first_probe_blue_up_auto.json --out-md outputs\\reports\\zone1_first_probe_blue_up_auto.md",
            "python scripts\\probe_taptap244_zone1.py --beam 180 --suffix first_auto",
            "python scripts\\report_zone1_first_auto_exploration.py",
            "```",
        ]
    )
    OUT_REPORT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def write_auto_walk() -> None:
    source = CURRENT_BEST_WALK.read_text(encoding="utf-8")
    OUT_WALK.parent.mkdir(parents=True, exist_ok=True)
    header = [
        "# 1区 Current Best Boss Walk（自动设置口径）",
        "",
        "## 自动设置",
        "",
        "- `__auto__.battle=true`：允许实机自动清 0 伤怪；walk 仍保留金币/怪物结果。",
        "- `__auto__.item=\"nopotion\"`：自动拾取非血瓶物品；血瓶必须按路线显式拾取或继续保留。",
        "- `__auto__.wall=true`：自动开暗墙/岩浆；4F-10F boss 段没有使用雪花清岩浆。",
        "",
        "## 打印口径",
        "",
        "- 下方内容基于 `best/current_best_boss_walk.md`，不提升为新的 best。",
        "- `take redPotion` / `take bluePotion` 表示路线显式踩取血瓶，不是自动拾取血瓶。",
        "- 0 伤怪和非血瓶物品在实机自动设置下可能被自动清/拾；本地 walk 为可审计 replay，仍列出资源变化。",
        "",
        "---",
        "",
    ]
    OUT_WALK.write_text("\n".join(header) + source, encoding="utf-8")


def main() -> None:
    write_auto_walk()
    write_report()
    print(f"wrote {OUT_WALK.relative_to(ROOT)}")
    print(f"wrote {OUT_REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
