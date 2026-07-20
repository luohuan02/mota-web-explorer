#!/usr/bin/env python3
"""Strict Game probe for the 12F red-key leaderboard strategy.

The probe is deliberately continuous: it rebuilds the verified 1-20F scaffold,
replaces the mutually-exclusive 14F red-key fight with the real 12F merchant,
crosses 20-31F through real stairs/events, then replays both documented 31-40F
shop allocations.  No state splice or coordinate teleport is used.
"""

from __future__ import annotations

import argparse
import copy
import json
import pickle
import sys
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.solver.game_route import go_to_decomposed, read_json, shop_cost, state_line
from scripts.search.zone2_game_route import SAVE1, apply_mt10_supply, run_zone1, run_zone2
from scripts.search.zone2_2atk1def_game_route import (
    WALK_MD,
    optimize_zone2_steps,
    parse_walk_md,
    replace_mt14_red_key_fight_with_mt12_merchant,
)
from scripts.search.zone3_game_route import GUIDE_WALK, Zone3Game, run_zone3

PRESERVE_WALK = ROOT / "best" / "zone3_2atk1def_preserve_pickaxe_walk.json"


BRIDGE_STAIRS = [
    ("MT20", (6, 1), "MT21"),
    ("MT21", (6, 11), "MT22"),
    ("MT22", (6, 6), "MT23"),
    ("MT23", (11, 1), "MT24"),
    ("MT24", (2, 10), "MT25"),
    ("MT25", (1, 11), "MT26"),
    ("MT26", (2, 10), "MT27"),
    ("MT27", (11, 11), "MT28"),
    ("MT28", (1, 11), "MT29"),
]


def click_stair(g: Zone3Game, fid: str, pos: tuple[int, int], to_fid: str) -> None:
    if g.state["floor"] != fid:
        g.fail(f"bridge floor mismatch: need={fid} have={g.state['floor']}")
    g.go_to(fid, pos[0], pos[1], f"通过楼梯到 {to_fid}")
    g.transition(to_fid, f"{fid}->{to_fid}")


def run_bridge(g: Zone3Game) -> None:
    g.set_segment("20-31F 连续桥")
    for fid, pos, to_fid in BRIDGE_STAIRS:
        click_stair(g, fid, pos, to_fid)
    g.thief_mt29_open_passage()
    click_stair(g, "MT29", (6, 11), "MT30")
    for pos in [(5, 5), (7, 5), (4, 5), (8, 5), (3, 5), (9, 5)]:
        block = g.block_at("MT30", pos)
        if block is not None:
            g.go_to("MT30", pos[0], pos[1], "30F 清六只史莱姆")
    click_stair(g, "MT30", (6, 1), "MT31")
    g.set_auto(note="31F起保留血瓶，自动拾取切换为 nopotion", item="nopotion")


def allocation_walk(path: Path, kinds: list[str]) -> dict:
    data = copy.deepcopy(read_json(path))
    shop_steps = [s for s in data["steps"] if s.get("action") == "商店"]
    if len(shop_steps) != len(kinds):
        raise RuntimeError(f"expected {len(kinds)} shop steps, found {len(shop_steps)}")
    for step, kind in zip(shop_steps, kinds):
        step["eid"] = kind
        step["note"] = f"策略分支：31-40F购买 {kind}"
    return data


def shop_clusters(steps: list[dict]) -> list[tuple[int, int]]:
    clusters = []
    i = 0
    while i < len(steps):
        if steps[i].get("action") != "商店":
            i += 1
            continue
        j = i + 1
        while j < len(steps) and steps[j].get("action") == "商店":
            j += 1
        clusters.append((i, j))
        i = j
    return clusters


def distributed_allocation_walk(
    path: Path,
    kinds: list[str],
    counts: tuple[int, ...],
    *,
    sell_before_purchase: int | None = None,
    sell_count_before_purchase: int = 1,
    late_resources_before_purchase: list[dict] | None = None,
    collect_early_gems_before_purchase: int | None = None,
    early_resources: list[dict] | None = None,
    collect_mid_resources_before_purchase: int | None = None,
    mid_resources: list[dict] | None = None,
    collect_post_resources_after_purchase: int | None = None,
    post_resources: list[dict] | None = None,
) -> dict:
    """Place the same seven purchases at existing, human-clickable shop visits."""
    data = copy.deepcopy(read_json(path))
    clusters = shop_clusters(data["steps"])
    if len(clusters) != len(counts) or sum(counts) != len(kinds):
        raise RuntimeError(f"bad distribution clusters={clusters} counts={counts} kinds={kinds}")
    out = []
    cursor = 0
    cluster_by_start = {start: (end, counts[n]) for n, (start, end) in enumerate(clusters)}
    i = 0
    while i < len(data["steps"]):
        if i not in cluster_by_start:
            out.append(data["steps"][i])
            i += 1
            continue
        end, count = cluster_by_start[i]
        template = data["steps"][i]
        for _ in range(count):
            if collect_early_gems_before_purchase is not None and cursor == collect_early_gems_before_purchase:
                out.extend(copy.deepcopy(early_resources or []))
            if collect_mid_resources_before_purchase is not None and cursor == collect_mid_resources_before_purchase:
                out.extend(copy.deepcopy(mid_resources or []))
            if sell_before_purchase is not None and cursor == sell_before_purchase:
                out.extend(copy.deepcopy(late_resources_before_purchase or []))
                for _sale in range(sell_count_before_purchase):
                    out.append({
                        "floor": "MT28",
                        "pos": [8, 4],
                        "action": "商人",
                        "eid": "specialTrader",
                        "note": "策略搜索：晚售黄钥匙补足下一档商店资金",
                    })
            step = copy.deepcopy(template)
            step["eid"] = kinds[cursor]
            step["note"] = f"策略搜索：延迟购买 {kinds[cursor]}"
            out.append(step)
            cursor += 1
            if collect_post_resources_after_purchase is not None and cursor - 1 == collect_post_resources_after_purchase:
                out.extend(copy.deepcopy(post_resources or []))
        i = end
    data["steps"] = out
    return data


def compositions(total: int, parts: int, prefix: tuple[int, ...] = ()):
    if parts == 1:
        yield prefix + (total,)
        return
    for value in range(total + 1):
        yield from compositions(total - value, parts - 1, prefix + (value,))


def insert_late_mt31_key_bundle(data: dict) -> dict:
    """Buy the 31F 4YK+1BK bundle at the last responsible moment.

    The purchase is deliberately placed immediately before MT39's blue door:
    buying it earlier removes the liquidity needed by the 920G stat tier,
    while buying it here converts already-earned monster gold into the exact
    blue key required by the centre-fly puzzle.
    """
    out = []
    inserted = False
    for step in data["steps"]:
        if (
            not inserted
            and step.get("floor") == "MT39"
            and step.get("pos") == [8, 10]
            and step.get("action") == "开门"
        ):
            out.extend([
                {"floor": "MT31", "pos": [6, 2], "action": "飞行", "eid": None,
                 "note": "39F蓝门前回31F购买钥匙组"},
                {"floor": "MT31", "pos": [1, 11], "action": "商人", "eid": "keyBundle31",
                 "note": "31F 1000G买4黄1蓝（属性档完成后）"},
                {"floor": "MT39", "pos": [11, 2], "action": "飞行", "eid": None,
                 "note": "返回39F继续中心飞行器谜题"},
            ])
            inserted = True
        out.append(step)
    if not inserted:
        raise RuntimeError("MT39 blue-door insertion point missing")
    data["steps"] = out
    return data


def insert_mt20_right_pocket(data: dict) -> dict:
    """Spend a genuinely surplus blue key on MT20's +500HP pocket."""
    out = []
    inserted = False
    for step in data["steps"]:
        out.append(step)
        if (
            not inserted
            and step.get("floor") == "MT39"
            and step.get("pos") == [4, 4]
            and step.get("action") == "拾取"
            and step.get("eid") == "centerFly3"
        ):
            out.extend([
                {"floor": "MT20", "pos": [6, 1], "action": "飞行", "eid": None,
                 "note": "中心飞行器到手后回20F取右侧药瓶袋"},
                {"floor": "MT20", "pos": [11, 5], "action": "拾取", "eid": "yellowKey",
                 "note": "20F蓝门袋：黄钥匙"},
                {"floor": "MT20", "pos": [10, 4], "action": "拾取", "eid": "redPotion",
                 "note": "20F蓝门袋：红药"},
                {"floor": "MT20", "pos": [11, 4], "action": "拾取", "eid": "bluePotion",
                 "note": "20F蓝门袋：蓝药"},
                {"floor": "MT39", "pos": [11, 2], "action": "飞行", "eid": None,
                 "note": "返回39F继续40F路线"},
            ])
            inserted = True
    if not inserted:
        raise RuntimeError("MT39 centerFly3 insertion point missing")
    data["steps"] = out
    return data


def insert_late_red_cushion(data: dict) -> dict:
    """Use two surplus yellow keys for the measured +100HP boss cushion."""
    out = []
    inserted = False
    for step in data["steps"]:
        out.append(step)
        if (
            not inserted
            and step.get("floor") == "MT39"
            and step.get("pos") == [4, 4]
            and step.get("action") == "拾取"
            and step.get("eid") == "centerFly3"
        ):
            out.extend([
                {"floor": "MT16", "pos": [6, 1], "action": "飞行", "eid": None,
                 "note": "40F Boss前补第一组净收益红药"},
                {"floor": "MT16", "pos": [11, 3], "action": "拾取", "eid": "redPotion",
                 "note": "16F红药生存垫"},
                {"floor": "MT39", "pos": [11, 2], "action": "飞行", "eid": None,
                 "note": "返回39F继续40F路线"},
            ])
            inserted = True
    if not inserted:
        raise RuntimeError("MT39 centerFly3 red-cushion insertion point missing")
    data["steps"] = out
    return data


def ensure_explicit_mt40_guard_cleanup(data: dict) -> dict:
    """Make the documented pre-Boss cleanup independent of auto BFS order."""
    out = []
    inserted = False
    for step in data["steps"]:
        out.append(step)
        if (
            not inserted
            and step.get("floor") == "MT40"
            and step.get("pos") == [2, 2]
            and step.get("action") == "击杀"
        ):
            for pos in ((3, 2), (4, 2)):
                out.append({
                    "floor": "MT40", "pos": [pos[0], pos[1]],
                    "action": "击杀", "eid": "swordsman",
                    "note": "40F左上剑士在离开单向区前显式清理（auto已清则跳过）",
                })
            inserted = True
    if not inserted:
        raise RuntimeError("MT40 left swordsman insertion point missing")
    data["steps"] = out
    return data


def insert_mt40_outer_resource_group(data: dict) -> dict:
    """Collect the profitable outer-ring gems/potion before centreFly3."""
    out = []
    inserted = False
    for step in data["steps"]:
        if (
            not inserted
            and step.get("floor") == "MT40"
            and step.get("eid") == "centerFly3"
            and step.get("action") == "事件"
        ):
            out.append({
                "floor": "MT40", "pos": [1, 10], "action": "拾取", "eid": "bluePotion",
                "note": "中心飞行器前收40F外圈蓝药与沿途攻防宝石资源组",
            })
            inserted = True
        out.append(step)
    if not inserted:
        raise RuntimeError("MT40 centerFly3 insertion point missing")
    data["steps"] = out
    return data


def build_to_mt31() -> Zone3Game:
    steps = replace_mt14_red_key_fight_with_mt12_merchant(
        optimize_zone2_steps(parse_walk_md(WALK_MD))
    )
    g = Zone3Game(read_json(SAVE1))
    g.strict_live_model = True
    g.auto_flags = {"battle": True, "item": True, "wall": True}
    run_zone1(g)
    apply_mt10_supply(g)
    run_zone2(g, steps)
    run_bridge(g)
    return g


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out-json",
        type=Path,
        default=ROOT / "outputs" / "results" / "redkey_12_zone3_allocation_probe.json",
    )
    parser.add_argument(
        "--terminal-pickle",
        type=Path,
        default=ROOT / "outputs" / "results" / "redkey_12_preterminal_game.pkl",
        help="strict Game checkpoint immediately before terminal potion/key/shop closure",
    )
    parser.add_argument(
        "--late49-defer-dragon",
        action="store_true",
        help="Experiment: collect MT46-48 red gems + final stat shop BEFORE the "
             "magicDragon so it is fought at higher ATK/DEF (dragon DEF=250 is "
             "extremely ATK-sensitive). Sets late49DeferDragon on best_game.",
    )
    parser.add_argument(
        "--out-json-suffix",
        default="",
        help="suffix appended to the continuous-TE output filename (e.g. _deferdragon)",
    )
    args = parser.parse_args()
    base = build_to_mt31()
    variants = {
        "guide_five_def_two_atk": (GUIDE_WALK, ["def"] * 5 + ["atk"] * 2),
        "guide_seven_def": (GUIDE_WALK, ["def"] * 7),
        "resource_delayed_five_def_two_atk": (PRESERVE_WALK, ["def"] * 5 + ["atk"] * 2),
        "resource_delayed_seven_def": (PRESERVE_WALK, ["def"] * 7),
    }
    rows = []
    for label, (walk_path, kinds) in variants.items():
        g = copy.deepcopy(base)
        start_step = len(g.steps)
        try:
            run_zone3(g, sell_deficit=[0], walk_data=allocation_walk(walk_path, kinds))
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
        else:
            error = None
        rows.append({
            "label": label,
            "allocation": kinds,
            "scaffold": str(walk_path.relative_to(ROOT)),
            "ok": not g.errors,
            "error": error,
            "start_mt31": base.snapshot(),
            "final": g.snapshot(),
            "errors": g.errors,
            "steps": g.steps,
            "zone3_steps": g.steps[start_step:],
        })
        print(label, "ok=", not g.errors, state_line(g.state), g.state["floor"],
              f"dmg={g.state['dmg']} door={g.state['yd']}/{g.state['bd']}/{g.state['rd']}")
        if g.errors:
            print("ERR", g.errors[-1])

    search_rows = []
    best_search = None
    best_game = None
    preboss_probe_walk = None
    cluster_count = len(shop_clusters(read_json(PRESERVE_WALK)["steps"]))
    gem_step = {
        "floor": "MT32", "pos": [1, 1], "action": "拾取", "eid": "blueGem",
        "note": "策略搜索：33F守卫前取得32F红蓝宝石组",
    }
    static = Zone3Game(read_json(SAVE1))
    funding_bundles = {"none": [gem_step]}
    funding_bundles["MT31_right_four_key_group"] = [gem_step,
        {"floor": "MT31", "pos": [10, 6], "action": "击杀", "eid": "ghostSkeleton",
         "note": "策略搜索：提前清31F右下四钥匙组前置怪"},
        {"floor": "MT31", "pos": [11, 7], "action": "开门", "eid": "yellowDoor",
         "note": "策略搜索：提前开31F右下四钥匙组"},
        {"floor": "MT31", "pos": [10, 9], "action": "击杀", "eid": "slimeMan",
         "note": "策略搜索：提前收31F右下四钥匙并补商店金币"},
    ]
    funding_bundles["MT31_right_four_key_group_blue_potion"] = [
        *funding_bundles["MT31_right_four_key_group"],
        {"floor": "MT31", "pos": [9, 8], "action": "开门", "eid": "yellowDoor",
         "note": "策略搜索：四钥匙组后开右下蓝瓶门"},
        {"floor": "MT31", "pos": [8, 8], "action": "拾取", "eid": "bluePotion",
         "note": "策略搜索：33F双战士最小生存垫"},
    ]
    for floor_num in range(1, 34):
        fid = f"MT{floor_num}"
        for pos, block in static.floors[fid].blocks.items():
            if block.kind == "enemy" and int(static.enemies[block.eid].get("money", 0)) >= 31:
                label = f"{fid}_x{pos[0]}y{pos[1]}_{block.eid}"
                funding_bundles[label] = [gem_step, {
                    "floor": fid,
                    "pos": [pos[0], pos[1]],
                    "action": "击杀",
                    "eid": block.eid,
                    "note": "策略搜索：保留黄钥匙的商店资金怪",
                }]
    funding_bundles = {
        "MT31_right_group_blue_then_left_group":
            funding_bundles["MT31_right_four_key_group_blue_potion"]
    }
    left_key_group = [
        {"floor": "MT31", "pos": [2, 6], "action": "击杀", "eid": "ghostSkeleton",
         "note": "策略搜索：第五防后清31F左上四钥匙组前置怪"},
        {"floor": "MT31", "pos": [1, 5], "action": "开门", "eid": "yellowDoor",
         "note": "策略搜索：第五防后开31F左上四钥匙组"},
        {"floor": "MT31", "pos": [1, 2], "action": "击杀", "eid": "swordsman",
         "note": "策略搜索：骑士剑后处理左上双手剑士"},
        {"floor": "MT31", "pos": [3, 1], "action": "拾取", "eid": "yellowKey",
         "note": "策略搜索：收31F左上四钥匙组"},
    ]
    post_bundles = {"left_group_only": left_key_group}
    for floor_num in range(1, 35):
        fid = f"MT{floor_num}"
        for pos, block in static.floors[fid].blocks.items():
            if block.kind == "item" and block.eid == "redPotion":
                label = f"left_group_plus_{fid}_x{pos[0]}y{pos[1]}_red"
                post_bundles[label] = [*left_key_group, {
                    "floor": fid,
                    "pos": [pos[0], pos[1]],
                    "action": "拾取",
                    "eid": "redPotion",
                    "note": "策略搜索：34F中心后半最小红药生存垫",
                }]
            if block.kind == "item" and block.eid == "bluePotion":
                label = f"left_group_plus_{fid}_x{pos[0]}y{pos[1]}_blue"
                post_bundles[label] = [*left_key_group, {
                    "floor": fid,
                    "pos": [pos[0], pos[1]],
                    "action": "拾取",
                    "eid": "bluePotion",
                    "note": "策略搜索：34F中心后半蓝药生存垫",
                }]
    mt15_blue_bundle = [*left_key_group, {
        "floor": "MT15", "pos": [11, 8], "action": "拾取", "eid": "bluePotion",
        "note": "策略搜索：34F中心全防路线蓝药生存垫",
    }]
    combined_post_bundles = {"left_group_mt15_blue": mt15_blue_bundle}
    for floor_num in range(1, 35):
        fid = f"MT{floor_num}"
        for pos, block in static.floors[fid].blocks.items():
            if block.kind == "item" and block.eid == "redPotion":
                label = f"left_group_mt15_blue_plus_{fid}_x{pos[0]}y{pos[1]}_red"
                combined_post_bundles[label] = [*mt15_blue_bundle, {
                    "floor": fid, "pos": [pos[0], pos[1]], "action": "拾取", "eid": "redPotion",
                    "note": "策略搜索：34F中心后段补一红药",
                }]
    post_bundles = combined_post_bundles
    post_bundles = {
        "left_group_mt15_blue_mt31_red": [*mt15_blue_bundle, {
            "floor": "MT31", "pos": [10, 1], "action": "拾取", "eid": "redPotion",
            "note": "策略搜索：34F中心与后段士兵生存垫",
        }]
    }
    survival_base = post_bundles["left_group_mt15_blue_mt31_red"]
    second_blue_bundles = {"survival_base_only": survival_base}
    for floor_num in range(1, 35):
        fid = f"MT{floor_num}"
        for pos, block in static.floors[fid].blocks.items():
            if block.kind == "item" and block.eid == "bluePotion":
                label = f"survival_base_plus_{fid}_x{pos[0]}y{pos[1]}_blue"
                second_blue_bundles[label] = [*survival_base, {
                    "floor": fid, "pos": [pos[0], pos[1]], "action": "拾取", "eid": "bluePotion",
                    "note": "策略搜索：36F横排前第二蓝药生存垫",
                }]
    post_bundles = second_blue_bundles
    extra_red_base = [*survival_base]
    post_bundles = {
        "survival_plus_mt31_second_red": [*extra_red_base, {
            "floor": "MT31", "pos": [2, 11], "action": "拾取", "eid": "redPotion",
            "note": "策略搜索：36F前补31F另一红药",
        }],
        "survival_plus_mt33_left_red": [*extra_red_base, {
            "floor": "MT33", "pos": [2, 4], "action": "拾取", "eid": "redPotion",
            "note": "策略搜索：36F前补33F左侧红药",
        }],
        "survival_plus_two_extra_reds": [*extra_red_base,
            {"floor": "MT31", "pos": [2, 11], "action": "拾取", "eid": "redPotion",
             "note": "策略搜索：36F前补31F另一红药"},
            {"floor": "MT33", "pos": [2, 4], "action": "拾取", "eid": "redPotion",
             "note": "策略搜索：36F前补33F左侧红药"},
        ],
    }
    post_bundles = {
        "survival_plus_mt31_second_red": [*extra_red_base, {
            "floor": "MT31", "pos": [2, 11], "action": "拾取", "eid": "redPotion",
            "note": "策略搜索：36F前补31F另一红药",
        }]
    }
    late_funding_bundles = {"none": []}
    for floor_num in range(1, 38):
        fid = f"MT{floor_num}"
        for pos, block in static.floors[fid].blocks.items():
            if block.kind == "enemy" and int(static.enemies[block.eid].get("money", 0)) >= 22:
                label = f"{fid}_x{pos[0]}y{pos[1]}_{block.eid}"
                late_funding_bundles[label] = [{
                    "floor": fid, "pos": [pos[0], pos[1]], "action": "击杀", "eid": block.eid,
                    "note": "策略搜索：第7防少卖1黄钥匙的22G资金怪",
                }]
    late_funding_bundles = {
        "MT14_x1y9_redPriest": [{
            "floor": "MT14", "pos": [1, 9], "action": "击杀", "eid": "redPriest",
            "note": "策略搜索：第7防少卖1黄钥匙的资金怪与资源组",
        }]
    }
    post_bundles = {
        "survival_plus_mt31_second_red_mt3_red": [*extra_red_base,
            {"floor": "MT31", "pos": [2, 11], "action": "拾取", "eid": "redPotion",
             "note": "策略搜索：36F前补31F另一红药"},
            {"floor": "MT3", "pos": [11, 1], "action": "拾取", "eid": "redPotion",
             "note": "策略搜索：37F红骑士前补50HP"},
        ]
    }
    threshold_base = [*extra_red_base, {
        "floor": "MT31", "pos": [2, 11], "action": "拾取", "eid": "redPotion",
        "note": "策略搜索：36F前补31F另一红药",
    }]
    threshold_post_bundles = {"threshold_base": threshold_base}
    for floor_num in range(1, 35):
        fid = f"MT{floor_num}"
        for pos, block in static.floors[fid].blocks.items():
            if block.kind == "item" and block.eid == "redPotion":
                label = f"threshold_plus_{fid}_x{pos[0]}y{pos[1]}_red"
                threshold_post_bundles[label] = [*threshold_base, {
                    "floor": fid, "pos": [pos[0], pos[1]], "action": "拾取", "eid": "redPotion",
                    "note": "策略搜索：37F红骑士阈值红药",
                }]
    post_bundles = threshold_post_bundles
    # The single-sale liquidity case is the exact remaining threshold:
    # 698G + 100G from one sold yellow key still needs 122G for the 920G
    # seventh purchase.  MT14's red-priest pocket is the best first funding
    # group found by the one-target probe; combine it with every other
    # meaningful enemy target, then spend the retained key on the MT3 potion.
    # A successful replay must still retain the final yellow key for MT37.
    mt14_funding = {
        "floor": "MT14", "pos": [1, 9], "action": "击杀", "eid": "redPriest",
        "note": "策略搜索：第7防少卖一把黄钥匙的第一资金组",
    }
    late_funding_bundles = {}
    for floor_num in range(1, 38):
        fid = f"MT{floor_num}"
        for pos, block in static.floors[fid].blocks.items():
            if block.kind != "enemy" or int(static.enemies[block.eid].get("money", 0)) < 22:
                continue
            if fid == "MT14" and pos == (1, 9):
                continue
            label = f"MT14_redPriest_plus_{fid}_x{pos[0]}y{pos[1]}_{block.eid}"
            late_funding_bundles[label] = [mt14_funding, {
                "floor": fid, "pos": [pos[0], pos[1]], "action": "击杀", "eid": block.eid,
                "note": "策略搜索：第7防少卖一把黄钥匙的第二资金组",
            }]
    # Once the exhaustive two-target pass identified the only useful funding
    # families, keep the survival-threshold probe focused and deterministic.
    late_funding_bundles = {
        k: v for k, v in late_funding_bundles.items()
        if "MT16_x2y2_redPriest" in k
    }
    for bundle in late_funding_bundles.values():
        bundle.extend([
            {"floor": "MT19", "pos": [8, 3], "action": "击杀", "eid": "zombieKnight",
             "note": "策略搜索：零卖钥匙方案补足第7次购买"},
            {"floor": "MT19", "pos": [8, 8], "action": "击杀", "eid": "zombieKnight",
             "note": "策略搜索：39F前凑足31F钥匙包1000G"},
        ])
    post_bundles = {
        "threshold_mt3_red": [*threshold_base, {
            "floor": "MT3", "pos": [11, 1], "action": "拾取", "eid": "redPotion",
            "note": "策略搜索：37F红骑士前补50HP并保留最后一把门钥匙",
        }]
    }
    allocations = {"seven_def": ["def"] * 7}
    for allocation_label, kinds in allocations.items():
      for funding_label, funding_steps in funding_bundles.items():
       for post_label, post_steps in post_bundles.items():
        for late_funding_label, late_funding_steps in late_funding_bundles.items():
         for counts in compositions(len(kinds), cluster_count):
            # The strict replay already proves that at most two buys are liquid
            # at the first visit.  Prune only this exact affordability fact.
            if counts != (2, 2, 2, 1):
                continue
            g = base.clone()
            try:
                candidate_walk = distributed_allocation_walk(
                    PRESERVE_WALK,
                    kinds,
                    counts,
                    sell_before_purchase=6,
                    sell_count_before_purchase=0,
                    late_resources_before_purchase=late_funding_steps,
                    collect_early_gems_before_purchase=3,
                    early_resources=funding_steps,
                    collect_post_resources_after_purchase=4,
                    post_resources=post_steps,
                )
                candidate_walk = insert_late_red_cushion(
                    insert_late_mt31_key_bundle(candidate_walk)
                )
                candidate_walk = ensure_explicit_mt40_guard_cleanup(candidate_walk)
                candidate_walk = insert_mt40_outer_resource_group(candidate_walk)
                if (
                    allocation_label == "seven_def"
                ):
                    preboss_probe_walk = copy.deepcopy(candidate_walk)
                run_zone3(
                    g,
                    sell_deficit=[0],
                    walk_data=candidate_walk,
                )
            except Exception as exc:
                error = f"{type(exc).__name__}: {exc}"
            else:
                error = None
            row = {
                "allocation": allocation_label,
                "early_resources": "mt32_gems",
                "funding_resource": funding_label,
                "post_resource": post_label,
                "late_funding_resource": late_funding_label,
                "counts": counts,
                "ok": not g.errors,
                "error": error,
                "final": g.snapshot(),
                "last_error": g.errors[-1] if g.errors else None,
            }
            search_rows.append(row)
            if not g.errors and (
                best_search is None or g.state["hp"] > best_search["final"]["hp"]
            ):
                best_search = {**row, "steps": g.steps}
                best_game = g.clone()
                print("NEW BEST", allocation_label, counts, state_line(g.state))
    resource_probe = []
    if preboss_probe_walk is not None:
        event_index = next(
            i for i, step in enumerate(preboss_probe_walk["steps"])
            if step.get("floor") == "MT40"
            and step.get("eid") == "centerFly3"
            and step.get("action") == "事件"
        )
        preboss = base.clone()
        run_zone3(
            preboss,
            sell_deficit=[0],
            walk_data={"steps": preboss_probe_walk["steps"][:event_index]},
        )
        tail = preboss_probe_walk["steps"][event_index:]
        for fid, floor in preboss.floors.items():
            for pos, block in list(floor.blocks.items()):
                if block.kind != "item" or block.eid not in {
                    "redPotion", "bluePotion", "redGem", "blueGem"
                }:
                    continue
                trial = preboss.clone()
                steps = []
                if trial.state["floor"] != fid:
                    steps.append({"floor": fid, "pos": [trial.state["x"], trial.state["y"]],
                                  "action": "飞行", "eid": None, "note": "Boss前资源探针"})
                steps.append({"floor": fid, "pos": [pos[0], pos[1]], "action": "拾取",
                              "eid": block.eid, "note": "Boss前资源探针"})
                if fid != "MT40":
                    steps.append({"floor": "MT40", "pos": [6, 7], "action": "飞行",
                                  "eid": None, "note": "Boss前资源探针返回40F"})
                before = trial.snapshot()
                try:
                    run_zone3(trial, sell_deficit=[0], walk_data={"steps": [*steps, *tail]})
                except Exception as exc:
                    error = f"{type(exc).__name__}: {exc}"
                else:
                    error = None
                resource_probe.append({
                    "floor": fid, "pos": pos, "eid": block.eid,
                    "ok": not trial.errors, "error": error,
                    "delta_before_boss": {
                        "hp": trial.state["hp"] - before["hp"],
                        "yk": trial.state["yk"] - before["yk"],
                        "bk": trial.state["bk"] - before["bk"],
                        "gold": trial.state["gold"] - before["gold"],
                    },
                    "final": trial.snapshot(),
                    "last_error": trial.errors[-1] if trial.errors else None,
                })
        resource_probe.sort(key=lambda row: (not row["ok"], -row["final"]["hp"]))
    search_rows.sort(key=lambda row: (not row["ok"], -row["final"]["hp"], row["counts"]))
    payload = {
        "ok": best_search is not None,
        "mt31": base.snapshot(),
        "variants": rows,
        "distribution_search": search_rows,
        "best_distribution": best_search,
        "preboss_resource_probe": resource_probe,
    }
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"json={args.out_json}")
    if best_game is not None:
        from scripts.search.zone4_game_route import run_zone4

        if args.late49_defer_dragon:
            best_game.flags["late49DeferDragon"] = True

        # Export the exact strict-Game boundary before optional terminal
        # potion/key/shop closure.  A zero-key post-boss snapshot cannot
        # represent alternatives that use a key pocket to cross a 46F shop
        # threshold, so it is not a valid A* start.
        preterminal = best_game.clone()
        preterminal.flags["stopBeforeTerminalClosure"] = True
        run_zone4(preterminal)
        args.terminal_pickle.parent.mkdir(parents=True, exist_ok=True)
        args.terminal_pickle.write_bytes(
            pickle.dumps(preterminal, protocol=pickle.HIGHEST_PROTOCOL)
        )
        print(f"preterminal_pickle={args.terminal_pickle} {state_line(preterminal.state)}")

        # Keep the ordinary closure result as a baseline, but do not let its
        # final state masquerade as the terminal search start.
        continuous = best_game.clone()
        run_zone4(continuous)
        terminal_probe = []
        if not continuous.errors:
            next_cost = shop_cost(continuous.state["times1"])
            best_terminal = None
            for fid, floor in continuous.floors.items():
                for pos, block in list(floor.blocks.items()):
                    if block.kind != "enemy" or int(continuous.enemies[block.eid].get("money", 0)) <= 0:
                        continue
                    cand = continuous.clone()
                    before = cand.snapshot()
                    try:
                        if cand.state["floor"] != fid:
                            cand.fly(fid)
                        go_to_decomposed(cand, fid, pos[0], pos[1], "终局剩余金币单组审计")
                    except Exception as exc:
                        error = f"{type(exc).__name__}: {exc}"
                    else:
                        error = None
                    row = {
                        "floor": fid, "pos": pos, "eid": block.eid,
                        "gold_gain": cand.state["gold"] - before["gold"],
                        "hp_loss": before["hp"] - cand.state["hp"],
                        "yk_delta": cand.state["yk"] - before["yk"],
                        "error": error,
                    }
                    if error is None and cand.state["hp"] > 0 and cand.state["gold"] >= next_cost:
                        try:
                            cand.fly("MT46")
                            go_to_decomposed(cand, "MT46", 6, 2, "终局补金币后购买下一档HP")
                            cand.buy_shop("hp", 1, shop_pos=(6, 1))
                        except Exception as exc:
                            row["shop_error"] = f"{type(exc).__name__}: {exc}"
                        else:
                            row["after_shop"] = cand.snapshot()
                            if best_terminal is None or cand.state["hp"] > best_terminal.state["hp"]:
                                best_terminal = cand
                    terminal_probe.append(row)
            terminal_probe.sort(key=lambda row: (-row["gold_gain"], row["hp_loss"]))
            if best_terminal is not None:
                continuous = best_terminal
        zone4_name = "redkey_12_continuous_te_probe"
        if args.out_json_suffix:
            zone4_name += args.out_json_suffix
        zone4_out = ROOT / "outputs" / "results" / f"{zone4_name}.json"
        zone4_out.write_text(json.dumps({
            "ok": not continuous.errors,
            "final": continuous.snapshot(),
            "steps": continuous.steps,
            "stage_summaries": continuous.stage_summaries,
            "errors": continuous.errors,
            "terminal_single_group_probe": terminal_probe,
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"continuous_zone4={zone4_out} ok={not continuous.errors} {state_line(continuous.state)}")
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
