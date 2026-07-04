#!/usr/bin/env python3
"""Probe 41F-50F continuations from local Zone-3 candidate states.

The existing post-40 route was written for the guide/save37 snapshot.  This
bridge keeps that route logic but supplies a synthetic snapshot built from a
local Zone-3 replay, so 1F-40F remaining resources are preserved.
"""

from __future__ import annotations

import copy
import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "outputs" / "results" / "post40_slot26_probe.json"
OUT_MD = ROOT / "outputs" / "reports" / "post40_slot26_probe.md"
STRICT20_WALK = ROOT / "outputs" / "results" / "strict20_preserve_pickaxe_31to50_local_walk.json"
STRICT20_AUDIT = ROOT / "outputs" / "results" / "strict20_preserve_pickaxe_4to50_local_audit.json"


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


post = load_module("post40_probe_base", ROOT / "scripts" / "search_post40_guide_route.py")
clean = load_module("zone3_clean_probe_base", ROOT / "scripts" / "report_zone3_slot26_clean_walk.py")
deadline = load_module("zone3_deadline_probe_base", ROOT / "scripts" / "report_zone3_deadline_candidate.py")
strict20_seeded = load_module("zone3_strict20_seeded_probe_base", ROOT / "scripts" / "search_zone3_slot26_seeded.py")
score_mod = load_module("post40_probe_score", ROOT / "scripts" / "floor_final_score.py")


def state_line(s: dict[str, Any]) -> str:
    return (
        f"HP={s['hp']} ATK={s['atk']} DEF={s['def']} "
        f"YK={s['yk']} BK={s['bk']} RK={s['rk']} G={s['gold']} "
        f"{s['floor']} x{s['x']}y{s['y']}"
    )


def infer_center_fly_count(zg: Any) -> tuple[int, str]:
    """Infer live centerFly uses from the Zone-3 walk.

    The local Zone-3 helper tracks the 39F centerFly3 item as a boolean, but the
    live item is a three-use tool.  One pickup grants +3; each explicit use costs
    1.  Repeating the 39F puzzle remains a live-verification risk.
    """

    pickups = 0
    uses = 0
    for step in getattr(zg, "steps", []):
        if step.get("eid") != "centerFly3":
            continue
        action = step.get("action") or ""
        note = step.get("note") or ""
        if action == "拾取":
            pickups += 1
        if "使用中心对称飞行器" in note or action in {"事件", "中心飞行"}:
            uses += 1
    count = max(0, pickups * 3 - uses)
    return count, f"centerFly3 pickups={pickups}, modeled uses={uses}"


def synthetic_snapshot_from_zone3(zg: Any, label: str) -> dict[str, Any]:
    guide_snapshot = post.read_json(post.SNAPSHOT)
    snapshot = copy.deepcopy(guide_snapshot)
    zstate = zg.state

    # Start the post-40 continuation from the normal 41F landing after stepping
    # onto the 40F upFloor.  The 40F map itself still comes from the Zone-3 replay.
    snapshot["floorId"] = "MT41"
    hero = snapshot["hero"]
    hero.update(
        {
            "x": 6,
            "y": 2,
            "hp": zstate["hp"],
            "atk": zstate["atk"],
            "def": zstate["def"],
            "money": zstate["gold"],
            "yk": zstate["yk"],
            "bk": zstate["bk"],
            "rk": zstate["rk"],
        }
    )

    state_center_fly = int(zstate.get("centerFly", 0) or 0)
    if state_center_fly:
        center_fly = state_center_fly
        center_note = f"centerFly from Zone-3 replay state={state_center_fly}"
    else:
        center_fly, center_note = infer_center_fly_count(zg)
    tools = dict(hero.get("tools", {}))
    for key in ("yellowKey", "blueKey", "redKey"):
        tools.pop(key, None)
    if center_fly:
        tools["centerFly"] = center_fly
    else:
        tools.pop("centerFly", None)
    for key in ("upFly", "downFly", "earthquake", "bomb", "bigKey", "pickaxe", "superPotion"):
        value = zstate.get(key, 0)
        if value:
            tools[key] = int(value)
        else:
            tools.pop(key, None)
    hero["tools"] = tools

    constants = dict(hero.get("constants", {}))
    if zstate.get("cross", True):
        constants["cross"] = 1
    hero["constants"] = constants

    flags = dict(hero.get("flags", {}))
    flags["times1"] = int(zstate.get("times1", 0))
    flags["synthetic_source"] = label
    flags["synthetic_center_note"] = center_note
    visited = {f"MT{i}": True for i in range(1, 42)}
    visited.update({fid: True for fid in zstate.get("visited", set())})
    visited["MT41"] = True
    flags["__visited__"] = dict(sorted(visited.items(), key=lambda kv: post.floor_no(kv[0])))
    hero["flags"] = flags

    maps = {}
    for fid, floor in zg.floors.items():
        if post.floor_no(fid) <= 40:
            maps[fid] = {"map": copy.deepcopy(floor.grid)}
    snapshot["maps"] = maps
    snapshot["synthetic"] = {
        "label": label,
        "zone3_state": copy.deepcopy(zg.snapshot()),
        "center_fly_count": center_fly,
        "center_fly_note": center_note,
    }
    return snapshot


def build_zone3_variants(selected: set[str] | None = None) -> dict[str, Any]:
    def want(label: str) -> bool:
        return not selected or label in selected

    rows: dict[str, Any] = {}
    strict20_args = argparse.Namespace(
        snapshot=ROOT / "outputs" / "results" / "zone2_2atk1def_strict20_to31_bridge_snapshot.json",
    )
    if want("strict20_preserve_pickaxe_40"):
        rows["strict20_preserve_pickaxe_40"] = strict20_seeded.build_continuous_40_preserve_pickaxe_seed(strict20_args)
    if want("strict20_pickaxe_40"):
        rows["strict20_pickaxe_40"] = strict20_seeded.build_continuous_40_pickaxe_seed(strict20_args)

    clean_labels = {"slot26_clean_7def", "slot26_clean_8def", "slot26_clean_8atk"}
    if not selected or selected & clean_labels:
        r37_center = clean.build_r37_center()
        if want("slot26_clean_7def"):
            rows["slot26_clean_7def"] = clean.finish_variant(r37_center, first_shop="D", mid_shop=None)
        if want("slot26_clean_8def"):
            rows["slot26_clean_8def"] = clean.finish_variant(r37_center, first_shop="D", mid_shop="D")
        if want("slot26_clean_8atk"):
            rows["slot26_clean_8atk"] = clean.finish_variant(r37_center, first_shop="D", mid_shop="A")

    if want("deadline_candidate"):
        rows["deadline_candidate"] = deadline.rebuild_candidate()
    if want("post40_focused_slice2"):
        rows["post40_focused_slice2"] = rebuild_post40_focused_slice2()
    if want("post40_focused_slice3"):
        rows["post40_focused_slice3"] = rebuild_post40_focused_slice3()
    if want("post40_focused_slice4_goal"):
        rows["post40_focused_slice4_goal"] = rebuild_post40_focused_slice4_goal()
    if want("post40_focused_slice4_mid_center"):
        rows["post40_focused_slice4_mid_center"] = rebuild_post40_focused_slice4_mid_center()
    if want("post40_focused_slice5_goal"):
        rows["post40_focused_slice5_goal"] = rebuild_post40_focused_slice5_goal()
    if want("post40_focused_slice5_mid_center"):
        rows["post40_focused_slice5_mid_center"] = rebuild_post40_focused_slice5_mid_center()
    return rows


def rebuild_post40_focused_slice2() -> Any:
    """Rebuild outputs/results/zone3_slot26_post40_seeded_focused_slice2 best_goal."""

    seeded = deadline.seeded
    macro = deadline.macro
    base = deadline.base
    seeded.install_seeded_guidance()

    base0 = macro.start_to_right_resources("AA")
    farmed = macro.farm_targets(base0, [])
    g = copy.deepcopy(farmed)
    macro.sell(g, 2)
    macro.buy(g, "AA")
    sword = macro.try_sword(g)
    after2 = macro.after_sword_to_2f(sword)
    extra = macro.collect_extra_keys(after2)
    postg = copy.deepcopy(extra)
    macro.sell(postg, 0)
    macro.buy(postg, "DD")
    healed = macro.eat_potions_until(postg, 2200, preserve_yk=1)
    pre34 = macro.collect_pre34_keys(healed)
    r37 = macro.to_37_with_34_center(pre34)
    done = copy.deepcopy(r37)
    done = macro.try_take(done, "MT34", 1, 11, "34 left blue potion before 38")
    macro.buy(done, "D")
    done = macro.finish_from_37_center(done, mid_shop=None)

    base.move_to(done, "MT37", 11, 1, "search bluePotion")
    base.move_to(done, "MT38", 9, 4, "search yellowKey")
    puzzle = next(a for a in base.special_actions(done) if a["label"] == "MT39:event:centerFlyPuzzle")
    puzzle["apply"](done)
    base.move_to(done, "MT36", 3, 11, "search soldier")
    center = next(a for a in base.special_actions(done) if a["label"] == "MT40:use:centerFly")
    center["apply"](done)
    return base.finish_goal_candidate(done)


def rebuild_post40_focused_slice3() -> Any:
    """Rebuild outputs/results/zone3_slot26_post40_seeded_focused_slice3 best_goal."""

    seeded = deadline.seeded
    macro = deadline.macro
    base = deadline.base
    seeded.install_seeded_guidance()

    base0 = macro.start_to_right_resources("AA")
    farmed = macro.farm_targets(base0, [])
    g = copy.deepcopy(farmed)
    macro.sell(g, 2)
    macro.buy(g, "AA")
    sword = macro.try_sword(g)
    after2 = macro.after_sword_to_2f(sword)
    extra = macro.collect_extra_keys(after2)
    postg = copy.deepcopy(extra)
    macro.sell(postg, 0)
    macro.buy(postg, "DD")
    healed = macro.eat_potions_until(postg, 2200, preserve_yk=1)
    pre34 = macro.collect_pre34_keys(healed)
    r37 = macro.to_37_with_34_center(pre34)
    done = copy.deepcopy(r37)
    done = macro.try_take(done, "MT34", 1, 11, "34 left blue potion before 38")
    macro.buy(done, "D")
    done = macro.finish_from_37_center(done, mid_shop=None)

    base.move_to(done, "MT31", 8, 2, "search soldier")
    base.move_to(done, "MT38", 9, 4, "search yellowKey")
    base.move_to(done, "MT2", 4, 10, "search bluePotion")
    puzzle = next(a for a in base.special_actions(done) if a["label"] == "MT39:event:centerFlyPuzzle")
    puzzle["apply"](done)
    center = next(a for a in base.special_actions(done) if a["label"] == "MT40:use:centerFly")
    center["apply"](done)
    return base.finish_goal_candidate(done)


def rebuild_post40_focused_slice4_goal() -> Any:
    """Rebuild outputs/results/zone3_slot26_post40_seeded_focused_slice4 best_goal."""

    seeded = deadline.seeded
    macro = deadline.macro
    base = deadline.base
    seeded.install_seeded_guidance()

    base0 = macro.start_to_right_resources("AA")
    farmed = macro.farm_targets(base0, [])
    g = copy.deepcopy(farmed)
    macro.sell(g, 2)
    macro.buy(g, "AA")
    sword = macro.try_sword(g)
    after2 = macro.after_sword_to_2f(sword)
    extra = macro.collect_extra_keys(after2)
    postg = copy.deepcopy(extra)
    macro.sell(postg, 0)
    macro.buy(postg, "DD")
    healed = macro.eat_potions_until(postg, 2200, preserve_yk=1)
    pre34 = macro.collect_pre34_keys(healed)
    r37 = macro.to_37_with_34_center(pre34)
    done = copy.deepcopy(r37)
    done = macro.try_take(done, "MT34", 1, 11, "34 left blue potion before 38")
    macro.buy(done, "D")
    done = macro.finish_from_37_center(done, mid_shop=None)

    puzzle = next(a for a in base.special_actions(done) if a["label"] == "MT39:event:centerFlyPuzzle")
    puzzle["apply"](done)
    base.move_to(done, "MT2", 4, 10, "search bluePotion")
    base.move_to(done, "MT38", 9, 4, "search yellowKey")
    center = next(a for a in base.special_actions(done) if a["label"] == "MT40:use:centerFly")
    center["apply"](done)
    return base.finish_goal_candidate(done)


def rebuild_post40_focused_slice4_mid_center() -> Any:
    """Extend slice4 best_any by returning to 40F with centerFly if legal."""

    seeded = deadline.seeded
    macro = deadline.macro
    base = deadline.base
    seeded.install_seeded_guidance()

    base0 = macro.start_to_right_resources("AA")
    farmed = macro.farm_targets(base0, [])
    g = copy.deepcopy(farmed)
    macro.sell(g, 2)
    macro.buy(g, "AA")
    sword = macro.try_sword(g)
    after2 = macro.after_sword_to_2f(sword)
    extra = macro.collect_extra_keys(after2)
    postg = copy.deepcopy(extra)
    macro.sell(postg, 0)
    macro.buy(postg, "DD")
    healed = macro.eat_potions_until(postg, 2200, preserve_yk=1)
    pre34 = macro.collect_pre34_keys(healed)
    r37 = macro.to_37_with_34_center(pre34)
    done = copy.deepcopy(r37)
    done = macro.try_take(done, "MT34", 1, 11, "34 left blue potion before 38")
    macro.buy(done, "D")
    done = macro.finish_from_37_center(done, mid_shop=None)

    puzzle = next(a for a in base.special_actions(done) if a["label"] == "MT39:event:centerFlyPuzzle")
    puzzle["apply"](done)
    base.move_to(done, "MT2", 4, 10, "search bluePotion")
    base.move_to(done, "MT38", 9, 4, "search yellowKey")
    base.move_to(done, "MT36", 3, 11, "search soldier")
    center = next(a for a in base.special_actions(done) if a["label"] == "MT40:use:centerFly")
    center["apply"](done)
    return base.finish_goal_candidate(done)


def rebuild_post40_focused_slice5_goal() -> Any:
    """Rebuild outputs/results/zone3_slot26_post40_seeded_focused_slice5 best_goal."""

    seeded = deadline.seeded
    macro = deadline.macro
    base = deadline.base
    seeded.install_seeded_guidance()

    base0 = macro.start_to_right_resources("AA")
    farmed = macro.farm_targets(base0, [])
    g = copy.deepcopy(farmed)
    macro.sell(g, 2)
    macro.buy(g, "AA")
    sword = macro.try_sword(g)
    after2 = macro.after_sword_to_2f(sword)
    extra = macro.collect_extra_keys(after2)
    postg = copy.deepcopy(extra)
    macro.sell(postg, 0)
    macro.buy(postg, "DD")
    healed = macro.eat_potions_until(postg, 2200, preserve_yk=1)
    pre34 = macro.collect_pre34_keys(healed)
    r37 = macro.to_37_with_34_center(pre34)
    done = copy.deepcopy(r37)
    done = macro.try_take(done, "MT34", 1, 11, "34 left blue potion before 38")
    macro.buy(done, "D")
    done = macro.finish_from_37_center(done, mid_shop=None)

    base.move_to(done, "MT9", 1, 7, "search yellowKey")
    puzzle = next(a for a in base.special_actions(done) if a["label"] == "MT39:event:centerFlyPuzzle")
    puzzle["apply"](done)
    base.move_to(done, "MT36", 3, 11, "search soldier")
    center = next(a for a in base.special_actions(done) if a["label"] == "MT40:use:centerFly")
    center["apply"](done)
    return base.finish_goal_candidate(done)


def rebuild_post40_focused_slice5_mid_center() -> Any:
    """Extend slice5 best_any by returning to 40F with centerFly if legal."""

    seeded = deadline.seeded
    macro = deadline.macro
    base = deadline.base
    seeded.install_seeded_guidance()

    base0 = macro.start_to_right_resources("AA")
    farmed = macro.farm_targets(base0, [])
    g = copy.deepcopy(farmed)
    macro.sell(g, 2)
    macro.buy(g, "AA")
    sword = macro.try_sword(g)
    after2 = macro.after_sword_to_2f(sword)
    extra = macro.collect_extra_keys(after2)
    postg = copy.deepcopy(extra)
    macro.sell(postg, 0)
    macro.buy(postg, "DD")
    healed = macro.eat_potions_until(postg, 2200, preserve_yk=1)
    pre34 = macro.collect_pre34_keys(healed)
    r37 = macro.to_37_with_34_center(pre34)
    done = copy.deepcopy(r37)
    done = macro.try_take(done, "MT34", 1, 11, "34 left blue potion before 38")
    macro.buy(done, "D")
    done = macro.finish_from_37_center(done, mid_shop=None)

    puzzle = next(a for a in base.special_actions(done) if a["label"] == "MT39:event:centerFlyPuzzle")
    puzzle["apply"](done)
    base.move_to(done, "MT38", 9, 4, "search yellowKey")
    base.move_to(done, "MT2", 4, 10, "search bluePotion")
    base.move_to(done, "MT31", 4, 10, "search redKnight")
    center = next(a for a in base.special_actions(done) if a["label"] == "MT40:use:centerFly")
    center["apply"](done)
    return base.finish_goal_candidate(done)


def make_post_game_from_zone3(label: str, zg: Any) -> Any:
    snapshot = synthetic_snapshot_from_zone3(zg, label)
    g = post.Game(snapshot)
    zsnap = zg.snapshot()
    g.state["dmg"] = int(zsnap.get("dmg", 0))
    g.state["yd"] = int(zsnap.get("yd", 0))
    g.state["bd"] = int(zsnap.get("bd", 0))
    g.state["rd"] = int(zsnap.get("rd", 0))
    g.flags["TE"] = True
    g.flags["addhp"] = True
    return g


def run_stages(g: Any, trace: bool = False, stop_after: str | None = None) -> Any:
    stages = [
        ("prefix48", post.guide_prefix_to_48_visit),
        ("pre_earthquake", post.collect_guide_pre_earthquake),
        ("farm_earthquake", post.farm_gold_for_earthquake),
        ("shield", post.earthquake_and_shield),
        ("post_shield_no49", post.post_shield_no49),
        ("late49_endgame", post.late49_endgame),
    ]
    post.TRACE_ENABLED = trace
    try:
        for name, fn in stages:
            before = g.snapshot()
            before["step_count"] = len(g.steps)
            fn(g)
            after = g.snapshot()
            after["step_count"] = len(g.steps)
            g.stage_summaries.append(
                {
                    "name": name,
                    "label": post.STAGE_LABELS.get(name, name),
                    "before": before,
                    "after": after,
                    "delta_dmg": after["dmg"] - before["dmg"],
                    "delta_steps": after["step_count"] - before["step_count"],
                    "stock_score": post.stock_score(after),
                }
            )
            if stop_after == name:
                break
    except post.RouteError:
        pass
    return g


def row_for(label: str, g: Any, source: str) -> dict[str, Any]:
    return {
        "label": label,
        "source": source,
        "ok": not g.errors,
        "final": g.snapshot(),
        "state_text": state_line(g.state),
        "stage_summaries": g.stage_summaries,
        "errors": g.errors,
        "steps": g.steps,
    }


def export_strict20_preserve_pickaxe(zg: Any, pg: Any, row: dict[str, Any]) -> None:
    STRICT20_WALK.parent.mkdir(parents=True, exist_ok=True)
    STRICT20_AUDIT.parent.mkdir(parents=True, exist_ok=True)
    zone3_40_state = zg.snapshot()
    final_state = row["final"]
    combined_steps = list(zg.steps) + list(row["steps"])
    walk = {
        "name": "strict20_preserve_pickaxe_31to50_local_walk",
        "source_snapshot": "outputs/results/zone2_2atk1def_strict20_to31_bridge_snapshot.json",
        "zone3_40_state": zone3_40_state,
        "final": final_state,
        "state_text": row["state_text"],
        "errors": list(row["errors"]),
        "steps": combined_steps,
        "note": "31F-40F strict20 preserve-pickaxe seed plus 41F-50F TE late-49 continuation: no 0F lucky coin, downFly reserved for 50F->49F seal, 49F seal seals both fake+true redKing, final 50F kill on sealed true redKing (500/158/19)",
    }
    audit = {
        "zone3_40_state": zone3_40_state,
        "zone3_40_state_text": state_line(zone3_40_state),
        "zone3_40_score": score_mod.current_floor_and_below_final_score(zg, 40, monster_gold_factor=0.5),
        "final_state": final_state,
        "final_state_text": row["state_text"],
        "final_score": score_mod.current_floor_and_below_final_score(pg, 50, monster_gold_factor=0.5),
        "stage_summaries": row["stage_summaries"],
        "errors": list(row["errors"]),
        "steps": combined_steps,
    }
    STRICT20_WALK.write_text(json.dumps(walk, ensure_ascii=False, indent=2), encoding="utf-8")
    STRICT20_AUDIT.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")


def write_outputs(rows: list[dict[str, Any]]) -> None:
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps({"rows": rows}, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Post-40 Slot26 Continuation Probe",
        "",
        "- 目的：从不同 40F 本地候选接 41F-50F HP 通关骨架。",
        "- 注意：`slot26_*` 与 `deadline_candidate` 都是本地桥接结果，仍需 web human-input 验证。",
        "- web 验证要求：金币必须精确匹配，不允许 `live gold >= expected` 这种容忍。",
        "- 中心飞行器计数：39F `centerFly3` 按实机三次使用建模；若同一谜题重复取得，标为高风险。",
        "",
        "| 路线 | 结果 | 最终状态 | dmg | 门 黄/蓝/红 | 阶段数 | 错误 |",
        "| --- | --- | --- | ---: | --- | ---: | --- |",
    ]
    for row in rows:
        final = row["final"]
        err = "; ".join(row["errors"][:2]) if row["errors"] else ""
        lines.append(
            f"| {row['label']} | {'OK' if row['ok'] else 'FAIL'} | `{row['state_text']}` | "
            f"{final['dmg']} | {final['yd']}/{final['bd']}/{final['rd']} | "
            f"{len(row['stage_summaries'])} | {err} |"
        )
    lines.append("")
    for row in rows:
        lines.append(f"## {row['label']}")
        lines.append("")
        lines.append(f"- source: `{row['source']}`")
        lines.append(f"- ok: `{row['ok']}`")
        lines.append(f"- final: `{row['state_text']}` dmg={row['final']['dmg']} door={row['final']['yd']}/{row['final']['bd']}/{row['final']['rd']}")
        if row["errors"]:
            lines.append("- errors:")
            lines.extend(f"  - {e}" for e in row["errors"][:5])
        lines.append("")
        lines.append("| 阶段 | 状态 | 本段dmg | 累计dmg | 库存分 |")
        lines.append("| --- | --- | ---: | ---: | ---: |")
        for stage in row["stage_summaries"]:
            after = stage["after"]
            lines.append(
                f"| {stage['label']} | `{state_line(after)}` | {stage['delta_dmg']} | "
                f"{after['dmg']} | {stage['stock_score']:.1f} |"
            )
        lines.append("")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--only",
        action="append",
        choices=[
            "guide_save37_baseline",
            "strict20_preserve_pickaxe_40",
            "strict20_pickaxe_40",
            "slot26_clean_7def",
            "slot26_clean_8def",
            "slot26_clean_8atk",
            "deadline_candidate",
            "post40_focused_slice2",
            "post40_focused_slice3",
            "post40_focused_slice4_goal",
            "post40_focused_slice4_mid_center",
            "post40_focused_slice5_goal",
            "post40_focused_slice5_mid_center",
        ],
        help="run only the named row; may be repeated",
    )
    parser.add_argument("--trace", action="store_true", help="enable post40 trace output")
    args = parser.parse_args()
    selected = set(args.only or [])

    rows: list[dict[str, Any]] = []

    if not selected or "guide_save37_baseline" in selected:
        print("[post40] running guide_save37_baseline", flush=True)
        guide = post.Game(post.read_json(post.SNAPSHOT))
        rows.append(row_for("guide_save37_baseline", run_stages(guide, trace=args.trace), "outputs/results/guide40_current_snapshot.json"))
        print(f"[post40] done guide_save37_baseline ok={rows[-1]['ok']} {rows[-1]['state_text']}", flush=True)

    for label, zg in build_zone3_variants(selected).items():
        if selected and label not in selected:
            continue
        print(f"[post40] running {label}", flush=True)
        g = make_post_game_from_zone3(label, zg)
        pg = run_stages(g, trace=args.trace)
        row = row_for(label, pg, "local Zone-3 replay synthetic snapshot")
        rows.append(row)
        if label == "strict20_preserve_pickaxe_40" and zg is not None:
            export_strict20_preserve_pickaxe(zg, pg, row)
        print(f"[post40] done {label} ok={rows[-1]['ok']} {rows[-1]['state_text']}", flush=True)

    write_outputs(rows)
    for row in rows:
        print(
            f"{row['label']} ok={row['ok']} {row['state_text']} "
            f"dmg={row['final']['dmg']} door={row['final']['yd']}/{row['final']['bd']}/{row['final']['rd']} "
            f"errors={len(row['errors'])}"
        )
        if row["errors"]:
            print("  first_error:", row["errors"][0])
    print(f"json={OUT_JSON}")
    print(f"md={OUT_MD}")
    return 0 if any(row["ok"] for row in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
