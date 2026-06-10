#!/usr/bin/env python3
"""Compare walk files by damage and remaining map resources."""

from __future__ import annotations

# Allow scripts to import project-root modules after being moved under scripts/.
import os as _codex_os
import sys as _codex_sys
_codex_root = _codex_os.path.dirname(_codex_os.path.dirname(_codex_os.path.abspath(__file__)))
if _codex_root not in _codex_sys.path:
    _codex_sys.path.insert(0, _codex_root)

import os
import re
from collections import Counter, defaultdict

from src.solver.full_search import FLOOR_13_COLLECTED, load_data


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

WALKS = [
    ("fixed_prefix_best", os.path.join("outputs", "walkthroughs", "walkthrough_fixed_prefix.md")),
    ("guided_candidate1", os.path.join("outputs", "walkthroughs", "walkthrough_guided_candidate1.md")),
]

POTION_HP = {
    "redPotion": 50,
    "bluePotion": 200,
}

RESOURCE_IDS = {
    "yellowKey",
    "blueKey",
    "redKey",
    "redPotion",
    "bluePotion",
    "redGem",
    "blueGem",
    "greenGem",
    "sword1",
    "shield1",
}

CHINESE_MONSTER = {
    "绿slime": "greenSlime",
    "红slime": "redSlime",
    "蝙蝠": "bat",
    "骷髅士兵": "skeletonSoldier",
    "骷髅队长": "skeletonCaptain",
    "骷髅": "skeleton",
    "蓝法师": "bluePriest",
    "黄卫士": "yellowGuard",
    "兵士": "soldier",
}


def build_blocks(maps):
    return {
        fid: {(x, y): (t, eid) for x, y, t, eid in data["bl"]}
        for fid, data in maps.items()
    }


def all_resources(maps):
    resources = {}
    for fid, data in maps.items():
        for x, y, t, eid in data["bl"]:
            if t != 3 or eid not in RESOURCE_IDS:
                continue
            if (x, y) in FLOOR_13_COLLECTED.get(fid, frozenset()):
                continue
            resources[(fid, x, y)] = eid
    return resources


def floor_from_heading(line):
    match = re.search(r"###\s+.*?(\d+)(?:楼|F)", line)
    if not match:
        return None
    return f"MT{match.group(1)}"


def parse_hp_delta(line):
    match = re.search(r"HP=(\d+)→(\d+)", line)
    if not match:
        return None
    before = int(match.group(1))
    after = int(match.group(2))
    return before, after


def parse_key_deltas(line):
    deltas = {}
    for key in ("YK", "BK", "RK"):
        match = re.search(rf"{key}=(\d+)→(\d+)", line)
        if match:
            before = int(match.group(1))
            after = int(match.group(2))
            deltas[key] = after - before
    return deltas


def fallback_monster(line):
    if "击杀" not in line:
        return None
    for name, eid in CHINESE_MONSTER.items():
        if name in line:
            return eid
    return "unknownMonster"


def parse_walk(path, maps, blocks, resources):
    metrics = {
        "path": path,
        "steps": 0,
        "battle_damage": 0,
        "potion_hp_taken": 0,
        "final_state_line": "",
        "items_taken": Counter(),
        "doors_opened": Counter(),
        "monsters_killed": Counter(),
        "monster_damage": Counter(),
        "key_delta_positive": Counter(),
        "key_delta_negative": Counter(),
        "consumed_positions": set(),
    }

    current_floor = None
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n")
            floor = floor_from_heading(line)
            if floor:
                current_floor = floor
                continue

            if line.startswith("> 最终:"):
                metrics["final_state_line"] = line.replace("> 最终: ", "")

            step_match = re.search(r"\((\d+),(\d+)\)", line)
            if not step_match or current_floor is None:
                continue
            x, y = int(step_match.group(1)), int(step_match.group(2))
            metrics["steps"] += 1

            hp_delta = parse_hp_delta(line)
            hp_loss = 0
            hp_gain = 0
            if hp_delta:
                before, after = hp_delta
                if after < before:
                    hp_loss = before - after
                    metrics["battle_damage"] += hp_loss
                elif after > before:
                    hp_gain = after - before
                    metrics["potion_hp_taken"] += hp_gain

            for key, delta in parse_key_deltas(line).items():
                if delta > 0:
                    metrics["key_delta_positive"][key] += delta
                elif delta < 0:
                    metrics["key_delta_negative"][key] += -delta

            block = blocks.get(current_floor, {}).get((x, y))
            if block is not None:
                t, eid = block
                if t == 1 and "击杀" in line:
                    metrics["monsters_killed"][eid] += 1
                    metrics["monster_damage"][eid] += hp_loss
                elif t == 2 and "开" in line:
                    metrics["doors_opened"][eid] += 1
                elif t == 3 and "拾取" in line:
                    metrics["items_taken"][eid] += 1
                    metrics["consumed_positions"].add((current_floor, x, y))
                continue

            eid = fallback_monster(line)
            if eid:
                metrics["monsters_killed"][eid] += 1
                metrics["monster_damage"][eid] += hp_loss

    remaining = {
        pos: eid
        for pos, eid in resources.items()
        if pos not in metrics["consumed_positions"]
    }
    metrics["remaining_items"] = Counter(remaining.values())
    metrics["remaining_potion_hp"] = sum(POTION_HP.get(eid, 0) for eid in remaining.values())
    metrics["remaining_positions"] = remaining
    return metrics


def counter_line(counter, keys):
    parts = []
    for key in keys:
        value = counter.get(key, 0)
        if value:
            parts.append(f"{key}={value}")
    return ", ".join(parts) if parts else "none"


def sum_gems(counter):
    return counter.get("redGem", 0), counter.get("blueGem", 0), counter.get("greenGem", 0)


def write_report(results):
    fixed, guided = results
    lines = []
    lines.append("# Walk Metrics Comparison")
    lines.append("")
    lines.append("| metric | fixed_prefix_best | guided_candidate1 | guided - fixed |")
    lines.append("|---|---:|---:|---:|")

    numeric_metrics = [
        ("battle_damage", "battle_damage"),
        ("potion_hp_taken", "potion_hp_taken"),
        ("remaining_potion_hp", "remaining_potion_hp"),
        ("steps", "steps"),
    ]
    for label, key in numeric_metrics:
        a = fixed[key]
        b = guided[key]
        lines.append(f"| {label} | {a} | {b} | {b - a:+d} |")

    # Effective raw stock ignores reachability/cost, but is useful to see
    # whether lower ending HP is just uneaten potion value.
    fixed_effective = fixed["remaining_potion_hp"]
    guided_effective = guided["remaining_potion_hp"]
    lines.append(
        f"| final_hp_plus_remaining_potions | {extract_final_hp(fixed) + fixed_effective} | "
        f"{extract_final_hp(guided) + guided_effective} | "
        f"{(extract_final_hp(guided) + guided_effective) - (extract_final_hp(fixed) + fixed_effective):+d} |"
    )
    lines.append("")

    for result in results:
        lines.append(f"## {result['name']}")
        lines.append("")
        lines.append(f"- final: {result['final_state_line']}")
        lines.append(f"- battle dmg: {result['battle_damage']}")
        lines.append(f"- potion HP taken: {result['potion_hp_taken']}")
        lines.append(f"- remaining potion HP on map: {result['remaining_potion_hp']}")
        lines.append(
            "- items taken: "
            + counter_line(
                result["items_taken"],
                ["redGem", "blueGem", "yellowKey", "blueKey", "redKey", "redPotion", "bluePotion"],
            )
        )
        lines.append(
            "- remaining items: "
            + counter_line(
                result["remaining_items"],
                ["redGem", "blueGem", "yellowKey", "blueKey", "redKey", "redPotion", "bluePotion"],
            )
        )
        lines.append(
            "- doors opened: "
            + counter_line(result["doors_opened"], ["yellowDoor", "blueDoor", "redDoor"])
        )
        lines.append(
            "- key gains: "
            + counter_line(result["key_delta_positive"], ["YK", "BK", "RK"])
        )
        lines.append(
            "- key spends: "
            + counter_line(result["key_delta_negative"], ["YK", "BK", "RK"])
        )
        lines.append("- top monster damage:")
        for eid, dmg in result["monster_damage"].most_common(8):
            kills = result["monsters_killed"][eid]
            lines.append(f"  - {eid}: damage={dmg}, kills={kills}")
        lines.append("")

    lines.append("## Delta Notes")
    lines.append("")
    lines.append(
        f"- guided battle dmg is {guided['battle_damage'] - fixed['battle_damage']:+d} vs fixed."
    )
    lines.append(
        f"- guided potion HP taken is {guided['potion_hp_taken'] - fixed['potion_hp_taken']:+d} vs fixed."
    )
    lines.append(
        f"- guided remaining potion HP is {guided['remaining_potion_hp'] - fixed['remaining_potion_hp']:+d} vs fixed."
    )
    lines.append(
        "- `final_hp_plus_remaining_potions` is a raw stock metric only; it does not include the cost to reach those remaining potions."
    )
    lines.append("")

    text = "\n".join(lines)
    out_path = os.path.join("outputs", "reports", "walk_metrics_comparison.md")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(text)


def extract_final_hp(result):
    match = re.search(r"HP=(\d+)", result["final_state_line"])
    return int(match.group(1)) if match else 0


def main():
    _, maps = load_data()
    blocks = build_blocks(maps)
    resources = all_resources(maps)
    results = []
    for name, path in WALKS:
        metrics = parse_walk(path, maps, blocks, resources)
        metrics["name"] = name
        results.append(metrics)
    write_report(results)


if __name__ == "__main__":
    main()
