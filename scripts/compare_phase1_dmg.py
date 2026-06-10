#!/usr/bin/env python3
"""Compare valid 4F-9F shield-prefix damage between fixed and guided Phase1."""

from __future__ import annotations

# Allow scripts to import project-root modules after being moved under scripts/.
import os as _codex_os
import sys as _codex_sys
_codex_root = _codex_os.path.dirname(_codex_os.path.dirname(_codex_os.path.abspath(__file__)))
if _codex_root not in _codex_sys.path:
    _codex_sys.path.insert(0, _codex_root)

import os
from collections import Counter

import fixed_shield_strategy as fixed
from src.solver import gen_walkthrough as gw
import run_guided_strategy_compare as guided


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)


def state_str(state):
    return (
        f"HP={state['hp']} ATK={state['atk']} DEF={state['def']} "
        f"YK={state['yk']} BK={state['bk']} RK={state['rk']}"
    )


def item_value(eid):
    if eid == "redPotion":
        return 50
    if eid == "bluePotion":
        return 200
    return 0


def metric_empty():
    return {
        "battle_damage": 0,
        "potion_hp": 0,
        "doors": Counter(),
        "items": Counter(),
        "monsters": Counter(),
        "monster_damage": Counter(),
        "steps": 0,
    }


def add_step(metric, step):
    if isinstance(step, str):
        return
    metric["steps"] += 1
    eid = step["eid"]
    action = step["action"]
    hp_before = step.get("hp_before", step.get("state_before", {}).get("hp"))
    hp_after = step.get("hp_after", step.get("state_after", {}).get("hp"))
    delta = 0 if hp_before is None or hp_after is None else hp_after - hp_before
    if action in ("击杀", "monster"):
        dmg = max(0, -delta)
        metric["battle_damage"] += dmg
        metric["monsters"][eid] += 1
        metric["monster_damage"][eid] += dmg
    elif action in ("开门", "door"):
        metric["doors"][eid] += 1
    elif action in ("拾取", "item"):
        metric["items"][eid] += 1
        metric["potion_hp"] += item_value(eid)


def fixed_metrics():
    result = fixed.replay_route()
    to_shield = metric_empty()
    to_gems = metric_empty()
    shield_state = None
    gems_state = None
    before_or_at_shield = True
    for step in result["steps"]:
        add_step(to_gems, {
            "eid": step["eid"],
            "action": step["action"].split()[0] if " " in step["action"] else step["type"],
            "hp_before": step["state_before"]["hp"],
            "hp_after": step["state_after"]["hp"],
        })
        if before_or_at_shield:
            add_step(to_shield, {
                "eid": step["eid"],
                "action": step["action"].split()[0] if " " in step["action"] else step["type"],
                "hp_before": step["state_before"]["hp"],
                "hp_after": step["state_after"]["hp"],
            })
        if step["segment"] == "9F 拿铁盾" and step["eid"] == "shield1":
            shield_state = step["state_after"]
            before_or_at_shield = False
        if step["segment"] == "9F 拿红蓝宝石开头":
            gems_state = step["state_after"]
    return {
        "to_shield": to_shield,
        "to_gems": to_gems,
        "shield_state": shield_state,
        "gems_state": gems_state,
    }


def normalize_step(step):
    action = step["action"]
    if action == "击杀":
        kind = "击杀"
    elif action == "开门":
        kind = "开门"
    elif action == "拾取":
        kind = "拾取"
    else:
        kind = action
    return {
        "eid": step["eid"],
        "action": kind,
        "hp_before": step["hp_before"],
        "hp_after": step["hp_after"],
    }


def reconstruct_guided_phase1(candidate):
    chain = gw.trace_chain(candidate)
    segments = []
    for i in range(1, len(chain)):
        prev, curr = chain[i - 1], chain[i]
        si = curr.get("_step_info")
        if not si:
            continue
        fid, target_ids, flyback = si
        entrances = gw.FLYBACK_ENTRANCES if flyback else gw.ENTRANCES
        sx, sy = entrances[fid]
        removed = prev.get("collected", {}).get(fid, frozenset())
        if fid in gw.FLOOR_13_COLLECTED:
            removed |= gw.FLOOR_13_COLLECTED[fid]
        target_state = {
            "hp": curr["hp"],
            "atk": curr["atk"],
            "def": curr["def"],
            "yk": curr["yk"],
            "bk": curr["bk"],
            "rk": curr["rk"],
        }
        steps, final, vis = gw.search_with_path(
            gw.maps[fid],
            sx,
            sy,
            prev["hp"],
            prev["atk"],
            prev["def"],
            prev["yk"],
            prev["bk"],
            prev["rk"],
            target_ids,
            max_iter=500000,
            removed_pos=removed,
            target_state=target_state,
        )
        segments.append((fid, target_ids, flyback, curr, steps or []))
    return segments


def guided_metrics():
    entries = guided.run_guided_phase1(retry_level=0)
    candidate = guided.select_candidates(entries, limit=1)[0]
    segments = reconstruct_guided_phase1(candidate)
    to_shield = metric_empty()
    to_gems = metric_empty()
    shield_state = None
    gems_state = {
        "hp": candidate["hp"],
        "atk": candidate["atk"],
        "def": candidate["def"],
        "yk": candidate["yk"],
        "bk": candidate["bk"],
        "rk": candidate["rk"],
    }
    before_or_at_shield = True
    for fid, target_ids, flyback, curr, steps in segments:
        for raw_step in steps:
            step = normalize_step(raw_step)
            add_step(to_gems, step)
            if before_or_at_shield:
                add_step(to_shield, step)
        if fid == "MT9" and "shield1" in target_ids and before_or_at_shield:
            shield_state = {
                "hp": curr["hp"],
                "atk": curr["atk"],
                "def": curr["def"],
                "yk": curr["yk"],
                "bk": curr["bk"],
                "rk": curr["rk"],
            }
            before_or_at_shield = False
    return {
        "to_shield": to_shield,
        "to_gems": to_gems,
        "shield_state": shield_state,
        "gems_state": gems_state,
        "candidate": candidate,
    }


def counter_desc(counter):
    if not counter:
        return "none"
    return ", ".join(f"{key}={value}" for key, value in sorted(counter.items()))


def section(lines, title, fixed_data, guided_data, fixed_state, guided_state):
    lines.append(f"## {title}")
    lines.append("")
    lines.append("| metric | fixed | guided | guided - fixed |")
    lines.append("|---|---:|---:|---:|")
    for key, label in [
        ("battle_damage", "battle dmg"),
        ("potion_hp", "potion HP taken"),
        ("steps", "steps"),
    ]:
        f = fixed_data[key]
        g = guided_data[key]
        lines.append(f"| {label} | {f} | {g} | {g - f:+d} |")
    lines.append("")
    lines.append(f"- fixed state: {state_str(fixed_state)}")
    lines.append(f"- guided state: {state_str(guided_state)}")
    lines.append(f"- fixed doors: {counter_desc(fixed_data['doors'])}")
    lines.append(f"- guided doors: {counter_desc(guided_data['doors'])}")
    lines.append(f"- fixed items: {counter_desc(fixed_data['items'])}")
    lines.append(f"- guided items: {counter_desc(guided_data['items'])}")
    lines.append("- top fixed monster dmg:")
    for eid, dmg in fixed_data["monster_damage"].most_common(6):
        lines.append(f"  - {eid}: dmg={dmg}, kills={fixed_data['monsters'][eid]}")
    lines.append("- top guided monster dmg:")
    for eid, dmg in guided_data["monster_damage"].most_common(6):
        lines.append(f"  - {eid}: dmg={dmg}, kills={guided_data['monsters'][eid]}")
    lines.append("")


def main():
    f = fixed_metrics()
    g = guided_metrics()
    lines = []
    lines.append("# 4-9 Phase1 Damage Comparison")
    lines.append("")
    lines.append("修正 1/3 楼 flyback 入口后，本报告只比较合法的 4-9 剑盾/拿盾阶段。")
    lines.append("")
    section(
        lines,
        "到拿铁盾为止",
        f["to_shield"],
        g["to_shield"],
        f["shield_state"],
        g["shield_state"],
    )
    section(
        lines,
        "到9楼红蓝宝石开头为止",
        f["to_gems"],
        g["to_gems"],
        f["gems_state"],
        g["gems_state"],
    )
    text = "\n".join(lines).rstrip() + "\n"
    out_path = os.path.join("outputs", "reports", "phase1_dmg_comparison.md")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as out:
        out.write(text)
    print(text)


if __name__ == "__main__":
    main()
