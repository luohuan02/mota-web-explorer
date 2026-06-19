#!/usr/bin/env python3
"""Probe the TapTap 244 zone-1 key-saving route.

This is a focused replay/search probe, not a replacement for the canonical
best artifacts.  It starts from the phase-1 seed recorded in
best/current_best_boss_walk.md, adds an explicit MT9 no-blue-door up-floor
action, and tries TapTap-like merchant/key orders before the MT10 boss.
"""

from __future__ import annotations

import json
import os
import re
import sys
from typing import Any


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
SCRIPTS = os.path.join(ROOT, "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)
os.chdir(ROOT)

from scripts import compare_merchant_resource_paths as cm  # noqa: E402
from scripts import merchant_finalscore_audit as audit  # noqa: E402
from scripts import post9_resource_group_search as rg  # noqa: E402
from scripts import probe_mt7_red_first_swap_sequence as probe  # noqa: E402
from src.solver.full_search import FLOOR_13_COLLECTED  # noqa: E402
from src.solver import gen_walkthrough as gw  # noqa: E402


Action = tuple[str, str]

PHASE1_RE = re.compile(
    r"^- (?P<fid>MT\d+) x(?P<x>\d+)y(?P<y>\d+) "
    r"(?P<action>open|kill|take|pass) (?P<eid>[A-Za-z0-9_]+)"
)

SEQUENCES: dict[str, list[Action]] = {
    # Current best order, but replace the 9F blue-door entry with the
    # TapTap-style no-blue-door entry and buy both key merchants first.
    "merchant_before_no_blue": [
        ("MT7", "redGem"),
        ("MT3", "blueGem"),
        ("MT6", "blueGem"),
        ("MT7_SKEL_KEY", "yellowKey"),
        ("MT1", "blueGem"),
        ("MT8", "blueGem"),
        ("MT3", "redGem"),
        ("MT5_DIRECT", "blueGem"),
        ("MT4_DIRECT", "blueKey"),
        ("merchant", "MT6_BK"),
        ("merchant", "MT7_YK"),
        ("MT9_NO_BLUE_UP", "upFloor"),
        ("MT10_DIRECT", "blueGem"),
        ("MT7_RIGHT_KEY", "yellowKey"),
        ("MT10", "redGem"),
        ("MT10", "bluePotion"),
        ("MT8_REDKEY_NO_BLUEKEY", "redKey"),
        ("MT1", "bluePotion"),
        ("MT7_YELLOW_BLUEPOTION", "bluePotion"),
    ],
    # User-corrected MT7 merchant route: reach x6y1 by opening the right-side
    # yellow door and killing the skeleton soldier, not by spending the center
    # blue door.  This can also collect the right-side blue potion and two
    # yellow keys, so the later MT7_RIGHT_KEY macro is intentionally skipped.
    "mt7_yellow_merchant_right_pocket": [
        ("MT7", "redGem"),
        ("MT3", "blueGem"),
        ("MT6", "blueGem"),
        ("MT7_SKEL_KEY", "yellowKey"),
        ("MT1", "blueGem"),
        ("MT8", "blueGem"),
        ("MT3", "redGem"),
        ("MT5_DIRECT", "blueGem"),
        ("MT4_DIRECT", "blueKey"),
        ("merchant", "MT6_BK"),
        ("MT7_MERCHANT_YELLOW_RIGHT", "MT7_YK"),
        ("MT9_NO_BLUE_UP", "upFloor"),
        ("MT10_DIRECT", "blueGem"),
        ("MT10", "redGem"),
        ("MT10", "bluePotion"),
        ("MT7_YELLOW_BLUEPOTION", "bluePotion"),
        ("MT8_REDKEY_NO_BLUEKEY", "redKey"),
        ("MT1", "bluePotion"),
    ],
    "mt7_yellow_merchant_right_pocket_hp_fix": [
        ("MT7", "redGem"),
        ("MT3", "blueGem"),
        ("MT6", "blueGem"),
        ("MT7_SKEL_KEY", "yellowKey"),
        ("MT1", "blueGem"),
        ("MT8", "blueGem"),
        ("MT3", "redGem"),
        ("MT5_DIRECT", "blueGem"),
        ("MT4_DIRECT", "blueKey"),
        ("merchant", "MT6_BK"),
        ("MT7_MERCHANT_YELLOW_RIGHT", "MT7_YK"),
        ("MT9_NO_BLUE_UP", "upFloor"),
        ("MT10_DIRECT", "blueGem"),
        ("MT10", "redGem"),
        ("MT10", "bluePotion"),
        ("MT7_YELLOW_BLUEPOTION", "bluePotion"),
        ("MT8_REDKEY_NO_BLUEKEY", "redKey"),
        ("MT1", "bluePotion"),
        ("MT4", "bluePotion"),
        ("MT9", "redPotion"),
    ],
    # Buy the blue key early, but delay the 7F yellow-key merchant until after
    # the 10F blue gem path has proved affordable.
    "mt7_merchant_after_mt10_blue": [
        ("MT7", "redGem"),
        ("MT3", "blueGem"),
        ("MT6", "blueGem"),
        ("MT7_SKEL_KEY", "yellowKey"),
        ("MT1", "blueGem"),
        ("MT8", "blueGem"),
        ("MT3", "redGem"),
        ("MT5_DIRECT", "blueGem"),
        ("MT4_DIRECT", "blueKey"),
        ("merchant", "MT6_BK"),
        ("MT9_NO_BLUE_UP", "upFloor"),
        ("MT10_DIRECT", "blueGem"),
        ("merchant", "MT7_YK"),
        ("MT7_RIGHT_KEY", "yellowKey"),
        ("MT10", "redGem"),
        ("MT10", "bluePotion"),
        ("MT8_REDKEY_NO_BLUEKEY", "redKey"),
        ("MT1", "bluePotion"),
        ("MT7_YELLOW_BLUEPOTION", "bluePotion"),
    ],
    # A more literal key-saving lane: enter 10F without the 7F merchant, then
    # use the merchant only if the route still needs key refill before red key.
    "mt7_merchant_before_redkey": [
        ("MT7", "redGem"),
        ("MT3", "blueGem"),
        ("MT6", "blueGem"),
        ("MT7_SKEL_KEY", "yellowKey"),
        ("MT1", "blueGem"),
        ("MT8", "blueGem"),
        ("MT3", "redGem"),
        ("MT5_DIRECT", "blueGem"),
        ("MT4_DIRECT", "blueKey"),
        ("merchant", "MT6_BK"),
        ("MT9_NO_BLUE_UP", "upFloor"),
        ("MT10_DIRECT", "blueGem"),
        ("MT7_RIGHT_KEY", "yellowKey"),
        ("MT10", "redGem"),
        ("MT10", "bluePotion"),
        ("merchant", "MT7_YK"),
        ("MT8_REDKEY_NO_BLUEKEY", "redKey"),
        ("MT1", "bluePotion"),
        ("MT7_YELLOW_BLUEPOTION", "bluePotion"),
    ],
}


def inferred_state_text(ent: dict[str, Any] | None) -> str:
    if ent is None:
        return "-"
    return (
        f"HP={ent['hp']} ATK={ent['atk']} DEF={ent['def']} "
        f"YK={ent['yk']} BK={ent['bk']} RK={ent['rk']} "
        f"G={cm.inferred_gold(ent, include_boss_spawn=rg.base.goal(ent))} "
        f"dmg={ent.get('_dmg', 0)} "
        f"door={ent.get('_yd', 0)}/{ent.get('_bd', 0)}/{ent.get('_rd', 0)}"
    )


def parse_current_phase1_seed(path: str = os.path.join("best", "current_best_boss_walk.md")) -> dict[str, Any]:
    text = open(path, encoding="utf-8").read().splitlines()
    summary = next(line for line in text if line.startswith("- phase1 seed:"))
    m = re.search(
        r"HP=(?P<hp>-?\d+) ATK=(?P<atk>\d+) DEF=(?P<def>\d+) "
        r"YK=(?P<yk>-?\d+) BK=(?P<bk>-?\d+) RK=(?P<rk>-?\d+) "
        r"G=(?P<gold>-?\d+) dmg=(?P<dmg>\d+) door=(?P<yd>\d+)/(?P<bd>\d+)/(?P<rd>\d+)",
        summary,
    )
    if not m:
        raise RuntimeError(f"cannot parse phase1 summary: {summary}")

    collected: dict[str, set[tuple[int, int]]] = {
        fid: set(pos) for fid, pos in FLOOR_13_COLLECTED.items()
    }
    in_phase1 = False
    for line in text:
        if line.startswith("## Phase1 4F-9F Detailed Walk"):
            in_phase1 = True
            continue
        if in_phase1 and line.startswith("## Score Model"):
            break
        if not in_phase1:
            continue
        sm = PHASE1_RE.match(line)
        if not sm:
            continue
        if sm.group("action") in {"open", "kill", "take"}:
            fid = sm.group("fid")
            collected.setdefault(fid, set()).add((int(sm.group("x")), int(sm.group("y"))))

    ent = {
        "hp": int(m.group("hp")),
        "atk": int(m.group("atk")),
        "def": int(m.group("def")),
        "yk": int(m.group("yk")),
        "bk": int(m.group("bk")),
        "rk": int(m.group("rk")),
        "collected": {fid: frozenset(pos) for fid, pos in collected.items()},
        "_dmg": int(m.group("dmg")),
        "_yd": int(m.group("yd")),
        "_bd": int(m.group("bd")),
        "_rd": int(m.group("rd")),
        "_seed_source": "best/current_best_boss_walk phase1 seed",
    }
    expected_gold = int(m.group("gold"))
    actual_gold = cm.inferred_gold(ent, include_boss_spawn=False)
    if actual_gold != expected_gold:
        ent["_gold_parse_warning"] = {"expected": expected_gold, "actual": actual_gold}
    return ent


def trim_keep_keys(entries: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    if not entries:
        return []
    trimmed = rg.trim_entries(entries, max(limit, 1))
    pools = [
        sorted(trimmed, key=lambda e: (-e["bk"], -e["yk"], e.get("_dmg", 0), -e["hp"])),
        sorted(trimmed, key=lambda e: (-cm.final_stock_with_gold(e), e.get("_dmg", 0), -e["hp"])),
        sorted(trimmed, key=lambda e: (e.get("_dmg", 0), e.get("_yd", 0), e.get("_bd", 0), -e["hp"])),
        sorted(trimmed, key=lambda e: (-e["hp"], e.get("_dmg", 0), -e["bk"], -e["yk"])),
    ]
    out: list[dict[str, Any]] = []
    seen: set[int] = set()
    for pool in pools:
        for ent in pool:
            eid = ent.get("_id")
            if eid in seen:
                continue
            seen.add(eid)
            out.append(ent)
            if len(out) >= limit:
                return out
    return out


def apply_no_blue_up(ent: dict[str, Any]) -> list[dict[str, Any]]:
    if "MT10" in ent.get("collected", {}):
        return []
    if ent["atk"] < 25 or ent["def"] < 25:
        return []
    out = rg.floor_action_variant(
        ent,
        "MT9",
        "upFloor",
        flyback=True,
        forbid={(3, 11), (6, 3)},
        max_iter=250000,
        source_label="MT9:no-blue-door-up",
    )
    return [audit.annotate_money(item) for item in out]


def apply_mt7_yellow_merchant(ent: dict[str, Any], *, take_right_pocket: bool) -> list[dict[str, Any]]:
    before = cm.collected_for(ent, "MT7")
    require = {(7, 5), (7, 3)}
    if take_right_pocket:
        require |= {(9, 7), (9, 9), (9, 10), (9, 11)}
    forbid = {(5, 5)}
    out = []
    for item in cm.expand_merchant_action(audit.annotate_money(ent), ("merchant", "MT7_YK")):
        delta = cm.collected_for(item, "MT7") - before
        if require <= delta and not (forbid & delta):
            out.append(audit.annotate_money(item))
    return out


def apply_step(entries: list[dict[str, Any]], action: Action, beam: int) -> list[dict[str, Any]]:
    fid, target = action
    generated: list[dict[str, Any]] = []
    for ent in entries:
        if fid == "MT9_NO_BLUE_UP":
            generated.extend(apply_no_blue_up(ent))
        elif fid == "MT7_MERCHANT_YELLOW":
            generated.extend(apply_mt7_yellow_merchant(ent, take_right_pocket=False))
        elif fid == "MT7_MERCHANT_YELLOW_RIGHT":
            generated.extend(apply_mt7_yellow_merchant(ent, take_right_pocket=True))
        elif fid == "MT8_REDKEY_NO_BLUEKEY":
            generated.extend(
                rg.floor_action_variant(
                    ent,
                    "MT8",
                    "redKey",
                    flyback=True,
                    forbid={(7, 10)},
                    max_iter=250000,
                    source_label="MT8:redKey-without-right-blue-key",
                )
            )
        elif fid == "MT7_YELLOW_BLUEPOTION":
            generated.extend(
                rg.floor_action_variant(
                    ent,
                    "MT7",
                    "bluePotion",
                    flyback=True,
                    require={(7, 11)},
                    forbid={(5, 5)},
                    max_iter=250000,
                    source_label="MT7:x7y11-bluePotion-yellow-door",
                )
            )
        else:
            generated.extend(audit.merchant_aware_apply_action(ent, fid, target))
    return trim_keep_keys(generated, beam)


def replay_sequence(seed: dict[str, Any], name: str, sequence: list[Action], beam: int) -> dict[str, Any]:
    entries = [audit.seed_for_post9(seed)]
    rows: list[dict[str, Any]] = [
        {
            "step": 0,
            "action": "seed",
            "kept": 1,
            "best": audit.compact_record(audit.score_record("seed", entries[0], source="seed")),
        }
    ]
    for idx, action in enumerate(sequence, 1):
        entries = apply_step(entries, action, beam)
        rows.append({
            "step": idx,
            "action": f"{action[0]}:{action[1]}",
            "kept": len(entries),
            "best": audit.compact_record(
                audit.score_record(f"{action[0]}:{action[1]}", entries[0], source=name)
            ) if entries else None,
        })
        if not entries:
            return {"name": name, "ok": False, "rows": rows, "boss": None, "post_boss_supply": None}

    boss_entries: list[dict[str, Any]] = []
    for ent in entries:
        boss_entries.extend(audit.annotate_money(item) for item in rg.base.boss_action(ent))
    boss_entries = [ent for ent in trim_keep_keys(boss_entries, beam) if rg.base.goal(ent)]
    boss_entries.sort(key=lambda e: (-e["bk"], -e["yk"], -cm.final_stock_with_gold(e), e.get("_dmg", 0), -e["hp"]))
    boss = boss_entries[0] if boss_entries else None
    if boss is None:
        return {"name": name, "ok": False, "rows": rows, "boss": None, "post_boss_supply": None}
    post = dict(boss)
    post["hp"] += 600
    post["atk"] += 3
    post["def"] += 3
    post["yk"] += 3
    return {
        "name": name,
        "ok": True,
        "rows": rows,
        "boss": audit.compact_record(audit.score_record(f"{name}:boss", boss, source="taptap244 probe")),
        "post_boss_supply": {
            "hp": post["hp"],
            "atk": post["atk"],
            "def": post["def"],
            "yk": post["yk"],
            "bk": post["bk"],
            "rk": post["rk"],
            "gold": cm.inferred_gold(post, include_boss_spawn=True),
            "dmg": post.get("_dmg", 0),
            "yd": post.get("_yd", 0),
            "bd": post.get("_bd", 0),
            "rd": post.get("_rd", 0),
        },
    }


def write_outputs(data: dict[str, Any], suffix: str) -> None:
    os.makedirs(os.path.join("outputs", "results"), exist_ok=True)
    os.makedirs(os.path.join("outputs", "reports"), exist_ok=True)
    json_path = os.path.join("outputs", "results", f"taptap244_zone1_probe{suffix}.json")
    md_path = os.path.join("outputs", "reports", f"taptap244_zone1_probe{suffix}.md")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    lines = [
        "# TapTap 244 1区省蓝钥匙探针",
        "",
        f"- beam: `{data['beam']}`",
        f"- seed: `{data['seed_text']}`",
        "",
        "| 路线 | 是否到10F Boss后 | Boss后状态 | 10F补给后状态 |",
        "|---|---|---|---|",
    ]
    for result in data["results"]:
        boss = result.get("boss") or {}
        post = result.get("post_boss_supply") or {}
        boss_text = (
            f"HP={boss['hp']} ATK={boss['atk']} DEF={boss['def']} YK={boss['yk']} BK={boss['bk']} "
            f"G={boss['gold']} dmg={boss['dmg']} door={boss['yd']}/{boss['bd']}/{boss['rd']}"
            if boss else "-"
        )
        post_text = (
            f"HP={post['hp']} ATK={post['atk']} DEF={post['def']} YK={post['yk']} BK={post['bk']} "
            f"G={post['gold']}"
            if post else "-"
        )
        lines.append(f"| {result['name']} | {'是' if result['ok'] else '否'} | {boss_text} | {post_text} |")
    lines.append("")
    lines.append("## 逐步保留")
    for result in data["results"]:
        lines.append("")
        lines.append(f"### {result['name']}")
        lines.append("")
        lines.append("| step | action | kept | best |")
        lines.append("|---:|---|---:|---|")
        for row in result["rows"]:
            best = row.get("best") or {}
            text = (
                f"HP={best['hp']} ATK={best['atk']} DEF={best['def']} YK={best['yk']} BK={best['bk']} "
                f"RK={best['rk']} G={best['gold']} dmg={best['dmg']} door={best['yd']}/{best['bd']}/{best['rd']}"
                if best else "-"
            )
            lines.append(f"| {row['step']} | `{row['action']}` | {row['kept']} | {text} |")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")
    data["_json_path"] = json_path
    data["_md_path"] = md_path


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--beam", type=int, default=180)
    parser.add_argument("--suffix", default="")
    args = parser.parse_args()

    cm.ensure_merchant_maps()
    audit.install_post9_resource_group_hooks()
    seed = parse_current_phase1_seed()
    results = [
        replay_sequence(seed, name, sequence, args.beam)
        for name, sequence in SEQUENCES.items()
    ]
    data = {
        "beam": args.beam,
        "seed": audit.compact_record(
            audit.score_record("seed", seed, source="best/current_best_boss_walk phase1")
        ),
        "seed_text": inferred_state_text(seed),
        "results": results,
    }
    suffix = f"_{args.suffix}" if args.suffix and not args.suffix.startswith("_") else args.suffix
    write_outputs(data, suffix)
    for result in results:
        post = result.get("post_boss_supply")
        print(result["name"], "ok" if result["ok"] else "failed", post or "")
    print(f"wrote {data['_json_path']}")
    print(f"wrote {data['_md_path']}")


if __name__ == "__main__":
    main()
