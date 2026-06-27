#!/usr/bin/env python3
"""Compare all remaining resources after the guide and slot26 40F routes."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
GUIDE_PATH = ROOT / "scripts" / "find_zone3_quick_pass_walk.py"
CLEAN_PATH = ROOT / "scripts" / "report_zone3_slot26_clean_walk.py"
OUT_JSON = ROOT / "outputs" / "results" / "zone3_remaining_diff.json"
OUT_MD = ROOT / "outputs" / "reports" / "zone3_remaining_diff.md"

RESOURCE_ITEMS = {
    "yellowKey",
    "blueKey",
    "redKey",
    "redPotion",
    "bluePotion",
    "redGem",
    "blueGem",
    "sword3",
    "shield3",
    "pickaxe",
    "centerFly3",
}


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


def stock_score(g: Any) -> float:
    s = g.state
    return s["hp"] + s["yk"] * 50 + s["bk"] * 200 + s["gold"] * 0.5


def item_value_hp(eid: str, ratio: int) -> float:
    if eid == "yellowKey":
        return 50
    if eid == "blueKey":
        return 200
    if eid == "redPotion":
        return 50 * ratio
    if eid == "bluePotion":
        return 200 * ratio
    # Keep gems/red keys/tools visible in the resource list, but do not assign
    # leftover value in the user's 1YK=50HP=100G comparison mode.
    return 0


def record_resource(g: Any, fid: str, pos: tuple[int, int], block: Any) -> dict[str, Any] | None:
    ratio = int(g.floors[fid].ratio)
    x, y = pos
    if block.kind == "item" and block.eid in RESOURCE_ITEMS:
        return {
            "floor": fid,
            "x": x,
            "y": y,
            "kind": "item",
            "eid": block.eid,
            "ratio": ratio,
            "value_hp": item_value_hp(block.eid, ratio),
        }
    if block.kind == "enemy":
        dmg = g.damage_for(block.eid)
        money = int(g.enemies[block.eid]["money"])
        zero = dmg == 0
        return {
            "floor": fid,
            "x": x,
            "y": y,
            "kind": "enemy",
            "eid": block.eid,
            "money": money,
            "damage": "inf" if dmg == float("inf") else int(dmg),
            "zero_damage": zero,
            # Future double-gold makes each remaining monster's money worth
            # 2G, while current gold is scored as G*0.5.
            "value_hp": money * 1.0,
        }
    return None


def collect_resources(g: Any) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for fid in sorted(g.floors, key=floor_no):
        if floor_no(fid) > 40:
            continue
        floor = g.floors[fid]
        for pos, block in floor.blocks.items():
            rec = record_resource(g, fid, pos, block)
            if rec is None:
                continue
            key = f"{floor_no(fid):02d}:{pos[0]:02d}:{pos[1]:02d}"
            rows[key] = rec
    return rows


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
        value = rec["value_hp"]
        return f"item:{rec['eid']} v={value:g}"
    dmg = rec["damage"]
    zero = "0伤" if rec["zero_damage"] else f"伤{dmg}"
    return f"enemy:{rec['eid']} G={rec['money']} {zero} v={rec['value_hp']:g}"


def totals(resources: dict[str, dict[str, Any]]) -> dict[str, Any]:
    item_counts: Counter[str] = Counter()
    enemy_counts: Counter[str] = Counter()
    zero_enemy_counts: Counter[str] = Counter()
    value = 0.0
    item_value = 0.0
    zero_enemy_value = 0.0
    for rec in resources.values():
        value += float(rec["value_hp"])
        if rec["kind"] == "item":
            item_counts[rec["eid"]] += 1
            item_value += float(rec["value_hp"])
        elif rec["kind"] == "enemy":
            enemy_counts[rec["eid"]] += 1
            if rec["zero_damage"]:
                zero_enemy_counts[rec["eid"]] += 1
                zero_enemy_value += float(rec["value_hp"])
    return {
        "item_counts": dict(sorted(item_counts.items())),
        "enemy_counts": dict(sorted(enemy_counts.items())),
        "zero_enemy_counts": dict(sorted(zero_enemy_counts.items())),
        "item_value_hp": item_value,
        "zero_enemy_value_hp": zero_enemy_value,
        "total_value_hp": value,
        "resource_count": len(resources),
    }


def build_report() -> dict[str, Any]:
    runs = build_runs()
    resources = {name: collect_resources(g) for name, g in runs.items()}
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
    state_rows = {}
    for name, g in runs.items():
        state_rows[name] = {
            "ok": not g.errors and g.state["hp"] > 0,
            "state_text": state_line(g),
            "stock_score": stock_score(g),
            "errors": list(g.errors),
            "warnings": list(g.warnings),
        }
    total_rows = {name: totals(resources[name]) for name in names}
    return {
        "note": "guide uses outputs/results/zone3_quick_pass_walk.json route logic from slot36; boss_* routes use slot26 clean replay.",
        "value_model": "1YK=50HP, 1BK=200HP, current 100G=50HP; remaining monster gold is counted after double-gold as money*1.0 HP-score; redKey/gems/tools are listed but value_hp=0.",
        "states": state_rows,
        "totals": total_rows,
        "diff_rows": diff_rows,
    }


def delta(a: float, b: float) -> str:
    d = b - a
    return f"{d:+g}"


def counts_delta(base: dict[str, int], other: dict[str, int]) -> str:
    keys = sorted(set(base) | set(other))
    parts = []
    for key in keys:
        d = other.get(key, 0) - base.get(key, 0)
        if d:
            parts.append(f"{key}:{d:+d}")
    return ", ".join(parts) if parts else "无"


def write_outputs(data: dict[str, Any]) -> None:
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    names = ["guide", "boss_7buy_def", "boss_8buy_def", "boss_8buy_atk"]
    titles = {
        "guide": "攻略通40",
        "boss_7buy_def": "7买DEF",
        "boss_8buy_def": "8买DEF",
        "boss_8buy_atk": "8买ATK",
    }
    lines = [
        "# 三区通40剩余资源完整差异",
        "",
        f"- 说明：{data['note']}",
        f"- 价值模型：{data['value_model']}",
        f"- 差异行数：`{len(data['diff_rows'])}`",
        "",
        "## 状态汇总",
        "| 路线 | 状态 | stock | errors | 剩余价值 | final_score | 资源数 |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name in names:
        st = data["states"][name]
        total = data["totals"][name]
        final_score = st["stock_score"] + total["total_value_hp"]
        lines.append(
            f"| {titles[name]} | `{st['state_text']}` | {st['stock_score']:g} | "
            f"{len(st['errors'])} | {total['total_value_hp']:g} | {final_score:g} | {total['resource_count']} |"
        )
    lines.extend(["", "## 相对攻略汇总", "| 路线 | stock差 | 剩余价值差 | item数量差 | enemy数量差 | 0伤enemy数量差 |", "| --- | ---: | ---: | --- | --- | --- |"])
    guide_st = data["states"]["guide"]
    guide_total = data["totals"]["guide"]
    for name in names[1:]:
        st = data["states"][name]
        total = data["totals"][name]
        lines.append(
            f"| {titles[name]} | {delta(guide_st['stock_score'], st['stock_score'])} | "
            f"{delta(guide_total['total_value_hp'], total['total_value_hp'])} | "
            f"{counts_delta(guide_total['item_counts'], total['item_counts'])} | "
            f"{counts_delta(guide_total['enemy_counts'], total['enemy_counts'])} | "
            f"{counts_delta(guide_total['zero_enemy_counts'], total['zero_enemy_counts'])} |"
        )
    lines.extend(["", "## 全部剩余资源差异", "| 坐标 | 攻略通40 | 7买DEF | 8买DEF | 8买ATK |", "| --- | --- | --- | --- | --- |"])
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
        print(name, state["state_text"], "errors", len(state["errors"]))
    print(f"wrote {OUT_JSON}")
    print(f"wrote {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
