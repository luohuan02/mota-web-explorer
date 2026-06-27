#!/usr/bin/env python3
"""Write a clean slot26 zone-3 walk from replayed macro checkpoints."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MACRO_PATH = ROOT / "scripts" / "probe_zone3_slot26_sword_macro.py"
OUT_JSON = ROOT / "outputs" / "results" / "zone3_slot26_clean_walk.json"
OUT_MD = ROOT / "outputs" / "reports" / "zone3_slot26_clean_walk.md"


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


def simple_stock(g: Any) -> float:
    s = g.state
    return s["hp"] + s["yk"] * 50 + s["bk"] * 200 + s["gold"] * 0.5


def summary(g: Any) -> dict[str, Any]:
    return {
        "ok": valid(g),
        "state_text": base.state_line(g),
        "state": g.snapshot(),
        "simple_stock_score": simple_stock(g),
        "remaining_simple_value": base.remaining_simple_value(g),
        "errors": list(g.errors),
        "warnings": list(g.warnings),
        "steps": g.steps,
    }


def step_text(step: dict[str, Any]) -> str:
    x, y = step.get("pos", ["?", "?"])
    eid = step.get("eid") or ""
    delta = f" [{step['delta']}]" if step.get("delta") else ""
    return f"{step.get('floor')} x{x}y{y} {step.get('action')} {eid}{delta}".rstrip()


def write_report(rows: dict[str, Any]) -> None:
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    primary = rows["boss_8buy_def"]
    lines = [
        "# 三区 slot26 clean walk（8次攻防，39F中途买DEF）",
        "",
        "## 结论",
        f"- 主线状态：`{primary['state_text']}`",
        f"- simple_stock_score(1YK=50HP=100G)：`{primary['simple_stock_score']}`",
        f"- remaining_simple_value(31-40F)：`{primary['remaining_simple_value']}`",
        f"- errors/warnings：`{len(primary['errors'])}` / `{len(primary['warnings'])}`",
        "",
        "## 对照状态",
    ]
    for key, title in [
        ("boss_7buy_def", "7买，boss后停40F上楼口"),
        ("boss_8buy_def", "8买DEF，39F红宝石后回商店"),
        ("boss_8buy_atk", "8买ATK，39F红宝石后回商店"),
    ]:
        row = rows[key]
        lines.append(f"- {title}：`{row['state_text']}`，simple=`{row['simple_stock_score']}`，errors=`{len(row['errors'])}`")
    lines.extend(
        [
            "",
            "## 关键顺序",
            "- 34F中间8怪和奖励必须在第一次从33F进入34F上侧时处理，不能等飞回34F后再做。",
            "- 第2把蓝钥匙取MT32 x11y7，否则37F蓝门和39F谜题蓝门不够。",
            "- 第8次属性购买放在39F x11y6红宝石后；此时G=961，够花920买DEF，并且中心对称飞行器还没使用，可以回39F继续进40F。",
            "- 40F先主动清12怪，再触发x6y7事件，boss后只取钥匙和宝石，不取血瓶，停MT40 x6y1。",
            "",
            "## 详细Walk",
        ]
    )
    for i, step in enumerate(primary["steps"], 1):
        lines.append(f"{i:03d}. {step_text(step)}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    r37_center = build_r37_center()
    rows = {
        "r37_center": summary(r37_center),
        "boss_7buy_def": summary(finish_variant(r37_center, first_shop="D", mid_shop=None)),
        "boss_8buy_def": summary(finish_variant(r37_center, first_shop="D", mid_shop="D")),
        "boss_8buy_atk": summary(finish_variant(r37_center, first_shop="D", mid_shop="A")),
    }
    write_report(rows)
    for key, row in rows.items():
        print(key, row["state_text"], "errors", len(row["errors"]))
    print(f"wrote {OUT_JSON}")
    print(f"wrote {OUT_MD}")
    return 0 if all(row["ok"] for row in rows.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
