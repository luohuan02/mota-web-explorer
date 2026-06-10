#!/usr/bin/env python3
"""Continue the search from the verified 4F-9F fixed shield prefix."""

from __future__ import annotations

# Allow scripts to import project-root modules after being moved under scripts/.
import os as _codex_os
import sys as _codex_sys
_codex_root = _codex_os.path.dirname(_codex_os.path.dirname(_codex_os.path.abspath(__file__)))
if _codex_root not in _codex_sys.path:
    _codex_sys.path.insert(0, _codex_root)

import json
import os
import time

import fixed_shield_strategy as prefix
from src.solver import gen_walkthrough as gw


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
WALK_DIR = os.path.join("outputs", "walkthroughs")
RESULT_DIR = os.path.join("outputs", "results")


def make_initial_entry(prefix_result):
    final = prefix_result["final_state"]
    collected = {}
    for fid, positions in prefix_result["collected"].items():
        collected[fid] = frozenset((p["x"], p["y"]) for p in positions)
    yd = bd = rd = 0
    for step in prefix_result["steps"]:
        if step.get("eid") == "yellowDoor":
            yd += 1
        elif step.get("eid") == "blueDoor":
            bd += 1
        elif step.get("eid") == "redDoor":
            rd += 1
    return {
        "hp": final["hp"],
        "atk": final["atk"],
        "def": final["def"],
        "yk": final["yk"],
        "bk": final["bk"],
        "rk": final["rk"],
        "collected": collected,
        "_dmg": prefix_total_dmg(prefix_result),
        "_yd": yd,
        "_bd": bd,
        "_rd": rd,
    }


def fixed_state_str(state):
    return (
        f"HP={state['hp']} ATK={state['atk']} DEF={state['def']} "
        f"YK={state['yk']} BK={state['bk']} RK={state['rk']}"
    )


def fixed_delta(before, after):
    return prefix.delta_str(before, after).replace("->", "→")


def fixed_step_dmg(step):
    if step.get("type") != "monster":
        return 0
    before = step["state_before"]["hp"]
    after = step["state_after"]["hp"]
    return max(0, before - after)


def prefix_total_dmg(prefix_result):
    return sum(fixed_step_dmg(step) for step in prefix_result["steps"])


def prefix_segment_dmg(steps):
    return sum(fixed_step_dmg(step) for step in steps)


def append_prefix_lines(lines, prefix_result):
    lines.append("## 固定前缀：4-9 拿盾并取 9F 红蓝宝石")
    lines.append("")
    by_segment = {}
    for step in prefix_result["steps"]:
        by_segment.setdefault(step["segment"], []).append(step)

    cumulative_dmg = 0
    for segment in prefix_result["segments"]:
        seg_steps = by_segment.get(segment["name"], [])
        seg_dmg = prefix_segment_dmg(seg_steps)
        cumulative_dmg += seg_dmg
        lines.append(f"### {segment['name']}")
        for step in seg_steps:
            delta = fixed_delta(step["state_before"], step["state_after"])
            delta_part = f" {delta}" if delta else ""
            lines.append(f"  ({step['x']},{step['y']}) {step['action']}{delta_part}")
        lines.append(
            f"  → {fixed_state_str(segment['actual'])} 本段dmg={seg_dmg} 累计dmg={cumulative_dmg}"
        )
        lines.append("")


def append_search_chain_lines(lines, best):
    chain = gw.trace_chain(best)
    print(f"路径链: {len(chain)} 步")
    for i, c in enumerate(chain):
        si = c.get("_step_info")
        if si:
            fid, tgts, fb = si
            print(
                f"  #{i}: {gw.FLOOR_NAMES.get(fid, fid)} {tgts} flyback={fb} "
                f"{gw.entry_summary(c, chain[i - 1])}"
            )
        else:
            print(
                f"  #{i}: 固定前缀终点 {gw.entry_summary(c)}"
            )

    lines.append("## 搜索续段：27攻27防、红钥匙、10楼Boss")
    lines.append("")
    for i in range(1, len(chain)):
        prev, curr = chain[i - 1], chain[i]
        si = curr.get("_step_info")
        if si is None:
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
        path_target_state = dict(target_state)
        is_mt10_boss = fid == "MT10" and (
            "skeletonCaptain" in target_ids or "redDoor" in target_ids
        )
        if is_mt10_boss:
            path_target_state["hp"] = curr["hp"] + gw.boss_event_damage(
                curr["atk"], curr["def"]
            )
            if "redDoor" in target_ids:
                path_target_state["hp"] += gw.calc_dmg(
                    "skeletonCaptain", curr["atk"], curr["def"]
                )

        steps, final, vis_pos = gw.search_with_path(
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
            target_state=path_target_state,
        )

        if not steps:
            pareto, _, _ = gw.search_floor(
                gw.maps[fid],
                fid,
                {
                    "hp": prev["hp"],
                    "atk": prev["atk"],
                    "def": prev["def"],
                    "yk": prev["yk"],
                    "bk": prev["bk"],
                    "rk": prev["rk"],
                    "collected": prev.get("collected", {}),
                },
                target_ids,
                flyback=flyback,
            )
            if pareto:
                best_p = min(
                    pareto,
                    key=lambda p: abs(p[0] - curr["hp"])
                    + abs(p[4] - curr["atk"]) * 10
                    + abs(p[5] - curr["def"]) * 10
                    + abs(p[1] - curr["yk"]) * 5,
                )
                fallback_state = {
                    "hp": best_p[0],
                    "atk": best_p[4],
                    "def": best_p[5],
                    "yk": best_p[1],
                    "bk": best_p[2],
                    "rk": best_p[3],
                }
                if is_mt10_boss:
                    fallback_state["hp"] = curr["hp"] + gw.boss_event_damage(
                        curr["atk"], curr["def"]
                    )
                    if "redDoor" in target_ids:
                        fallback_state["hp"] += gw.calc_dmg(
                            "skeletonCaptain", curr["atk"], curr["def"]
                        )
                steps, final, vis_pos = gw.search_with_path(
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
                    target_state=fallback_state,
                )

        desc = gw.FLOOR_NAMES.get(fid, fid)
        if flyback:
            desc += "(flyback)"
        target_names = [gw.EID_NAMES.get(t, t) for t in target_ids]
        lines.append(f"### {desc}: {'+'.join(target_names)}")

        if steps:
            if is_mt10_boss:
                steps = gw.expand_mt10_boss_event_steps(steps)
            prev_step = None
            for s in steps:
                if isinstance(s, str):
                    lines.append(s)
                    prev_step = None
                else:
                    lines.append(gw.format_step(s, prev_step))
                    prev_step = s
            lines.append(
                f"  → {gw.entry_summary(curr, prev)}"
            )
        else:
            lines.append("  **无路径!**")
        lines.append("")


def walk_summary(prefix_result, best):
    prefix_dmg = prefix_total_dmg(prefix_result)
    chain = gw.trace_chain(best)
    search_segments = []
    for i in range(1, len(chain)):
        prev = chain[i - 1]
        curr = chain[i]
        si = curr.get("_step_info")
        if not si:
            continue
        fid, target_ids, flyback = si
        search_segments.append(
            {
                "floor": fid,
                "targets": target_ids,
                "flyback": flyback,
                "segment_dmg": curr.get("_dmg", 0) - prev.get("_dmg", 0),
                "total_dmg": curr.get("_dmg", 0),
                "state": {
                    "hp": curr["hp"],
                    "atk": curr["atk"],
                    "def": curr["def"],
                    "yk": curr["yk"],
                    "bk": curr["bk"],
                    "rk": curr["rk"],
                },
            }
        )
    return {
        "prefix": {
            "state": {
                "hp": prefix_result["final_state"]["hp"],
                "atk": prefix_result["final_state"]["atk"],
                "def": prefix_result["final_state"]["def"],
                "yk": prefix_result["final_state"]["yk"],
                "bk": prefix_result["final_state"]["bk"],
                "rk": prefix_result["final_state"]["rk"],
            },
            "dmg": prefix_dmg,
        },
        "final": {
            "state": {
                "hp": best["hp"],
                "atk": best["atk"],
                "def": best["def"],
                "yk": best["yk"],
                "bk": best["bk"],
                "rk": best["rk"],
            },
            "dmg": best.get("_dmg", 0),
        },
        "search_segments": search_segments,
    }


def generate():
    print("固定前缀校验中...")
    prefix_result = prefix.replay_route()
    if not prefix_result["ok"] or not prefix_result["strict_reachable"]:
        raise SystemExit("fixed prefix is not valid")

    initial_entry = make_initial_entry(prefix_result)
    prefix_dmg = prefix_total_dmg(prefix_result)
    print(f"固定前缀终点: {fixed_state_str(prefix_result['final_state'])} dmg={prefix_dmg}")
    print("从固定前缀继续搜索...")

    t0 = time.time()
    best = None
    best_retry = 0
    for retry in range(1):
        result = gw.run_search(
            retry_level=retry,
            initial_entry=initial_entry,
            skip_phase1=True,
            result_objective="dmg",
        )
        if result:
            print(
                f"  retry {retry}: "
                f"{gw.state_str(result['hp'], result['atk'], result['def'], result['yk'], result['bk'], result['rk'])}"
            )
            if best is None or (
                result.get("_dmg", 0),
                result.get("_yd", 0),
                result.get("_bd", 0),
                result.get("_rd", 0),
                -result["hp"],
            ) < (
                best.get("_dmg", 0),
                best.get("_yd", 0),
                best.get("_bd", 0),
                best.get("_rd", 0),
                -best["hp"],
            ):
                best = result
                best_retry = retry

    if best is None:
        raise SystemExit("续搜失败")

    print(
        f"最优: {gw.state_str(best['hp'], best['atk'], best['def'], best['yk'], best['bk'], best['rk'])} "
        f"({time.time() - t0:.1f}s)"
    )

    lines = []
    lines.append("# 魔塔固定前缀续搜攻略（dmg-first）")
    lines.append("")
    lines.append(
        f"> 固定前缀终点: {fixed_state_str(prefix_result['final_state'])} "
        f"本段dmg={prefix_dmg} 累计dmg={prefix_dmg}"
    )
    lines.append(f"> 最终: {gw.entry_summary(best)}")
    lines.append("")
    append_prefix_lines(lines, prefix_result)
    append_search_chain_lines(lines, best)
    lines.append("## 最终结果")
    lines.append("")
    lines.append(f"**{gw.entry_summary(best)}**")
    lines.append("")

    text = "\n".join(lines).rstrip() + "\n"
    os.makedirs(WALK_DIR, exist_ok=True)
    os.makedirs(RESULT_DIR, exist_ok=True)
    with open(os.path.join(WALK_DIR, "walkthrough.md"), "w", encoding="utf-8") as f:
        f.write(text)
    with open(os.path.join(WALK_DIR, "walkthrough_fixed_prefix.md"), "w", encoding="utf-8") as f:
        f.write(text)
    with open(os.path.join(WALK_DIR, "walkthrough_fixed_prefix_dmgfirst.md"), "w", encoding="utf-8") as f:
        f.write(text)
    with open(os.path.join(RESULT_DIR, "walkthrough_fixed_prefix_summary.json"), "w", encoding="utf-8") as f:
        json.dump(walk_summary(prefix_result, best), f, ensure_ascii=False, indent=2)
    with open(os.path.join(RESULT_DIR, "walkthrough_fixed_prefix_dmgfirst_summary.json"), "w", encoding="utf-8") as f:
        json.dump(walk_summary(prefix_result, best), f, ensure_ascii=False, indent=2)
    print("已写入 outputs/walkthroughs/walkthrough.md 和 outputs/walkthroughs/walkthrough_fixed_prefix_dmgfirst.md")
    return best


if __name__ == "__main__":
    generate()
