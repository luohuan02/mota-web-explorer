#!/usr/bin/env python3
"""Generate a quick passable zone-3 walk from the clean slot-36 31F start.

This is deliberately a route finder / replay calculator, not a live browser
executor.  It keeps the zone-3 32F attack/defense shop purchases at seven.
"""

from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "scripts" / "plan_zone3_guide_slot36.py"
OUT_JSON = ROOT / "outputs" / "results" / "zone3_quick_pass_walk.json"
OUT_MD = ROOT / "outputs" / "reports" / "zone3_quick_pass_walk_zh.md"


def load_plan_module():
    spec = importlib.util.spec_from_file_location("zone3_plan", PLAN)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {PLAN}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["zone3_plan"] = mod
    spec.loader.exec_module(mod)
    return mod


p = load_plan_module()

SKIP_PRE41_POTIONS = {
    ("MT14", 9, 6),   # red potion; save HP value for post-half-trap timing.
    ("MT34", 1, 11),  # blue potion
    ("MT34", 11, 10), # red potion
    ("MT34", 11, 2),  # red potion
    ("MT38", 11, 11), # blue potion
}


ACTION_CN = {
    "鍑绘潃": "击杀",
    "寮€闂?": "开门",
    "鎷惧彇": "拾取",
    "閫氳繃": "通过",
    "瀵硅瘽": "对话",
    "椋炶": "飞行",
    "鎹㈠眰": "换层",
    "鍟嗗簵": "商店",
    "鍟嗕汉": "商人",
    "浜嬩欢": "事件",
    "浜嬩欢鎴樻枟": "事件战斗",
    "浜嬩欢濂栧姳": "事件奖励",
    "鏍￠獙": "校验",
    "鍒拌揪": "到达",
    "鎾炴殫澧?": "撞暗墙",
    "鐢ㄩ晲": "用镐",
}

ITEM_CN = {
    "yellowDoor": "黄门",
    "blueDoor": "蓝门",
    "redDoor": "红门",
    "specialDoor": "机关门",
    "steelDoor": "铁门",
    "yellowKey": "黄钥匙",
    "blueKey": "蓝钥匙",
    "redKey": "红钥匙",
    "redPotion": "红血瓶",
    "bluePotion": "蓝血瓶",
    "redGem": "红宝石",
    "blueGem": "蓝宝石",
    "sword3": "骑士剑",
    "shield3": "骑士盾",
    "pickaxe": "镐",
    "centerFly3": "中心对称飞行器",
    "yellowKnight": "骑士队长",
    "ghostSkeleton": "鬼战士",
    "soldier": "战士",
    "swordsman": "双手剑士",
    "redKnight": "骑士",
    "slimeMan": "幽灵",
    "zombie": "兽人",
    "zombieKnight": "兽人武士",
    "blueGuard": "中级卫兵",
    "oldman": "老人",
    "thief": "小偷",
    "sellYellowKey": "卖黄钥匙",
    "atk": "攻击",
    "def": "防御",
}


def state_text(state: dict[str, Any]) -> str:
    return (
        f"HP={state['hp']} ATK={state['atk']} DEF={state['def']} "
        f"YK={state['yk']} BK={state['bk']} RK={state['rk']} G={state['gold']}"
    )


def first_strike_damage(g: Any, eid: str) -> int:
    enemy = g.enemies[eid]
    atk = g.state["atk"] * (2 if g.state.get("cross") and eid in p.CROSS_TARGETS else 1)
    hit = atk - int(enemy["def"])
    if hit <= 0:
        raise RuntimeError(f"{eid} cannot be damaged at ATK={g.state['atk']}")
    rounds = math.ceil(int(enemy["hp"]) / hit)
    return rounds * max(0, int(enemy["atk"]) - g.state["def"])


def add_mt39_center_fly_if_solved(g: Any) -> None:
    if g.block_at("MT39", (4, 2)) or g.block_at("MT39", (6, 4)):
        return
    before = g.snapshot()
    g.set_block("MT39", (4, 4), "item", "centerFly3", 331)
    g.record("事件奖励", (4, 4), "centerFly3", before, "39F 按第一行中间、第二行右边开门后生成飞行器")


def open_mt39_puzzle(g: Any) -> None:
    g.set_segment("39F 谜题与中心飞行器")
    g.go_to("MT39", 2, 8, "39F 开蓝门进谜题")
    g.go_to("MT39", 4, 2, "39F 谜题：第一行中间")
    g.go_to("MT39", 6, 4, "39F 谜题：第二行右边")
    add_mt39_center_fly_if_solved(g)
    g.go_to("MT39", 4, 4, "39F 拾取中心对称飞行器")
    g.state["centerFly3"] = True


def use_center_fly_to_mt40_boss_area(g: Any) -> None:
    if not g.state.get("centerFly3"):
        g.error("没有中心对称飞行器，不能飞入40F Boss区域")
        return
    if g.state["floor"] != "MT40":
        g.error(f"当前楼层 {g.state['floor']}，不能在40F使用中心对称飞行器")
        return
    before = g.snapshot()
    # In this tower the 39F item is the center-symmetry fly item.  From the
    # lower-right 40F entrance it lands at the upper-left boss area.
    g.state["x"], g.state["y"] = 12 - g.state["x"], 12 - g.state["y"]
    g.state["centerFly3"] = False
    g.record("事件", (g.state["x"], g.state["y"]), "centerFly3", before, "40F 使用中心对称飞行器进入Boss区域")


def event_mt40_boss(g: Any) -> None:
    before = g.snapshot()
    # The 40F event still battles the captain at x6y1 after the 12 guards have
    # been actively cleared. At current DEF this is 0 damage, but the live game
    # grants the captain's 100G.
    g.state["gold"] += int(g.enemies["yellowKnight"]["money"])
    for pos in [
        (5, 4),
        (4, 4),
        (3, 4),
        (7, 4),
        (8, 4),
        (9, 4),
        (4, 2),
        (3, 2),
        (2, 2),
        (8, 2),
        (9, 2),
        (10, 2),
        (6, 1),
    ]:
        g.set_ground("MT40", pos)
    for pos in [(2, 2), (3, 2), (4, 2)]:
        g.set_block("MT40", pos, "item", "yellowKey", 21)
    for pos in [(8, 2), (9, 2), (10, 2)]:
        g.set_block("MT40", pos, "item", "redGem", 27)
    for pos in [(3, 4), (4, 4), (5, 4)]:
        g.set_block("MT40", pos, "item", "bluePotion", 32)
    for pos in [(7, 4), (8, 4), (9, 4)]:
        g.set_block("MT40", pos, "item", "blueGem", 28)
    g.set_block("MT40", (6, 1), "terrain", "upFloor", 87)
    g.set_ground("MT40", (6, 7))
    g.state["x"], g.state["y"] = 6, 7
    g.record("事件奖励", (6, 7), "yellowKnight", before, "40F Boss事件：主动清怪后生成楼梯与奖励")
    return
    sequence = (
        ["ghostSkeleton"] * 3
        + ["soldier"] * 3
        + ["swordsman"] * 3
        + ["redKnight"] * 3
        + ["yellowKnight"]
    )
    damage = 0
    gold = 0
    for eid in sequence:
        damage += first_strike_damage(g, eid)
        gold += int(g.enemies[eid]["money"])
    if g.state["hp"] - damage <= 0:
        g.error(f"40F Boss事件会死亡: HP={g.state['hp']} damage={damage}")
    g.state["hp"] -= damage
    g.state["dmg"] += damage
    g.state["gold"] += gold
    for pos in [
        (5, 4),
        (4, 4),
        (3, 4),
        (7, 4),
        (8, 4),
        (9, 4),
        (4, 2),
        (3, 2),
        (2, 2),
        (8, 2),
        (9, 2),
        (10, 2),
        (6, 1),
    ]:
        g.set_ground("MT40", pos)
    for pos in [(2, 2), (3, 2), (4, 2)]:
        g.set_block("MT40", pos, "item", "yellowKey", 21)
    for pos in [(8, 2), (9, 2), (10, 2)]:
        g.set_block("MT40", pos, "item", "redGem", 27)
    for pos in [(3, 4), (4, 4), (5, 4)]:
        g.set_block("MT40", pos, "item", "bluePotion", 32)
    for pos in [(7, 4), (8, 4), (9, 4)]:
        g.set_block("MT40", pos, "item", "blueGem", 28)
    g.set_block("MT40", (6, 1), "terrain", "upFloor", 87)
    g.state["x"], g.state["y"] = 6, 7
    g.record("事件战斗", (6, 7), "yellowKnight", before, "40F Boss事件：怪物先攻，双手剑士各450伤害")


def extend_after_current_checkpoint(g: Any) -> Any:
    # Pick up the now-cheap 32F/31F key pockets before the 34F center reward.
    # This avoids relying on 36F fake-wall lanes and keeps the route at 7 shop buys.
    g.set_segment("32F/31F 黄钥匙与补血")
    g.fly("MT32")
    for pos in [(1, 10), (1, 7), (2, 7), (3, 7), (4, 7), (4, 8), (11, 4), (10, 4)]:
        g.go_to("MT32", *pos, f"32F 左侧与右侧补给 {pos}")
    g.fly("MT31")
    for pos in [(3, 1), (4, 1), (3, 2), (4, 2), (4, 4)]:
        g.go_to("MT31", *pos, f"31F 左上资源 {pos}")

    # 34F center reward: clear 8 enemies, collect 4 yellow + 1 red key,
    # then take the left blue potion and top/right key pocket.
    g.set_segment("34F 中间奖励与补血")
    g.fly("MT34")
    for pos in [(5, 4), (7, 4), (9, 4), (11, 4), (5, 8), (7, 8), (9, 8), (11, 8)]:
        g.go_to("MT34", *pos, f"34F 中间8怪 {pos}")
    for pos in [(2, 6), (1, 5), (3, 5), (1, 7), (3, 7)]:
        g.go_to("MT34", *pos, f"34F 中间奖励 {pos}")
    g.go_to("MT34", 1, 11, "34F 左下蓝血瓶")
    for pos in [(6, 1), (9, 1), (10, 1), (10, 2), (11, 1), (11, 2)]:
        g.go_to("MT34", *pos, f"34F 顶部补给 {pos}")

    # 37F left side to 38F, then shield route.
    g.set_segment("37F 左侧上38F与38F骑士盾")
    g.fly("MT37")
    g.go_to("MT37", 1, 1, "37F 左侧上楼")
    g.transition("MT38", 1, 1, "37F 上楼到38F")
    g.go_to("MT38", 3, 1, "38F 开红门")
    g.go_to("MT38", 5, 2, "38F 200G买3黄钥匙")
    g.buy_mt38_yellow_keys()
    g.go_to("MT38", 5, 8, "38F 蓝宝石")
    g.go_to("MT38", 1, 10, "38F 左中级卫兵")
    g.go_to("MT38", 3, 10, "38F 右中级卫兵")
    g.go_to("MT38", 2, 7, "38F 骑士盾")

    # Enter 39F, take the entrance key and the blue gem.
    g.set_segment("39F 钥匙与蓝宝石前置")
    g.fly("MT38")
    g.go_to("MT38", 11, 1, "38F 上楼到39F")
    g.transition("MT39", 11, 1, "38F 上楼到39F")
    g.go_to("MT39", 11, 3, "39F 入口黄钥匙")
    g.go_to("MT39", 6, 9, "39F 左下蓝宝石")

    # HP setup: the 38F blue potion keeps the 40F boss event safe.
    g.set_segment("40F 前补血")
    g.fly("MT38")
    g.go_to("MT38", 11, 11, "38F 右下蓝血瓶")

    # Return to 39F, solve puzzle, take center fly.
    g.fly("MT38")
    g.go_to("MT38", 11, 1, "38F 上楼回39F")
    g.transition("MT39", 11, 1, "38F 上楼到39F")
    open_mt39_puzzle(g)

    # Go to 40F, use center-fly, trigger boss, collect post-boss keys/gems only.
    g.set_segment("40F Boss")
    g.go_to("MT39", 11, 11, "39F 上楼到40F")
    g.transition("MT40", 11, 11, "39F 上楼到40F")
    use_center_fly_to_mt40_boss_area(g)
    for pos in [
        (2, 2),
        (3, 2),
        (4, 2),
        (3, 4),
        (4, 4),
        (5, 4),
        (7, 4),
        (8, 4),
        (9, 4),
        (8, 2),
        (9, 2),
        (10, 2),
    ]:
        g.go_to("MT40", *pos, f"40F pre-boss active clear {pos}")
    g.go_to("MT40", 6, 7, "40F 踩门口触发Boss事件")
    event_mt40_boss(g)
    for pos in [(2, 2), (3, 2), (4, 2), (8, 2), (9, 2), (10, 2), (7, 4), (8, 4), (9, 4)]:
        g.go_to("MT40", *pos, f"40F Boss后钥匙/宝石 {pos}")
    g.go_to("MT40", 6, 1, "40F Boss后上楼口")
    return g


def extend_after_current_checkpoint_v2(g: Any) -> Any:
    # 32F/31F resources. MT32 x3y10 was cleared before the second attack shop.
    g.set_segment("32F/31F resources")
    g.fly("MT32")
    for pos in [(1, 10), (1, 7), (2, 7), (3, 7), (4, 7), (4, 8), (11, 4), (10, 4)]:
        g.go_to("MT32", *pos, f"32F resource {pos}")
    g.fly("MT31")
    for pos in [(3, 1), (4, 1), (3, 2), (4, 2), (4, 4)]:
        g.go_to("MT31", *pos, f"31F resource {pos}")

    # 34F center reward. Take x2y6 first to avoid a later duplicate arrival.
    g.set_segment("34F center reward")
    g.fly("MT34")
    for pos in [(5, 4), (7, 4), (9, 4), (11, 4), (5, 8), (7, 8), (9, 8), (11, 8)]:
        g.go_to("MT34", *pos, f"34F center enemy {pos}")
    for pos in [(2, 6), (1, 5), (3, 5), (1, 7), (3, 7)]:
        g.go_to("MT34", *pos, f"34F center reward {pos}")
    g.go_to("MT34", 1, 11, "34F left blue potion")
    for pos in [(6, 1), (9, 1), (10, 1), (10, 2), (11, 1), (11, 2)]:
        g.go_to("MT34", *pos, f"34F top/right resource {pos}")

    g.set_segment("37F/38F shield")
    g.fly("MT37")
    g.go_to("MT37", 1, 1, "37F left stairs")
    g.transition("MT38", 1, 1, "37F to 38F")
    g.go_to("MT38", 3, 1, "38F red door")
    g.go_to("MT38", 5, 2, "38F buy yellow keys")
    g.buy_mt38_yellow_keys()
    g.go_to("MT38", 5, 8, "38F blue gem")
    g.go_to("MT38", 1, 10, "38F left blueGuard")
    g.go_to("MT38", 3, 10, "38F right blueGuard")
    g.go_to("MT38", 2, 7, "38F shield3")

    g.set_segment("39F free red gem")
    g.go_to("MT38", 11, 1, "38F stairs to 39F")
    g.transition("MT39", 11, 1, "38F to 39F")
    g.go_to("MT39", 11, 3, "39F entrance yellow key")
    g.go_to("MT39", 11, 6, "39F free red gem")

    g.set_segment("40F pre-HP")
    g.fly("MT38")
    g.go_to("MT38", 11, 11, "38F right blue potion")

    g.set_segment("39F puzzle and lower-left resources")
    g.go_to("MT38", 11, 1, "38F stairs back to 39F")
    g.transition("MT39", 11, 1, "38F to 39F")
    open_mt39_puzzle(g)
    g.go_to("MT39", 3, 11, "39F free yellow key after x4y10 door")
    g.go_to("MT39", 5, 9, "39F zero-damage ghostSkeleton")
    g.go_to("MT39", 6, 9, "39F blue gem via zero-damage route")

    g.set_segment("40F boss active clear")
    g.go_to("MT39", 11, 11, "39F stairs to 40F")
    g.transition("MT40", 11, 11, "39F to 40F")
    use_center_fly_to_mt40_boss_area(g)
    for pos in [
        (2, 2),
        (3, 2),
        (4, 2),
        (3, 4),
        (4, 4),
        (5, 4),
        (7, 4),
        (8, 4),
        (9, 4),
        (8, 2),
        (9, 2),
        (10, 2),
    ]:
        g.go_to("MT40", *pos, f"40F pre-boss active clear {pos}")
    g.go_to("MT40", 6, 7, "40F trigger boss reward event")
    event_mt40_boss(g)
    for pos in [(2, 2), (3, 2), (4, 2), (8, 2), (9, 2), (10, 2), (7, 4), (8, 4), (9, 4)]:
        g.go_to("MT40", *pos, f"40F post-boss key/gem {pos}")
    g.go_to("MT40", 6, 1, "40F stairs to 41F")
    return g


def generate() -> Any:
    p.OPTIONAL_BLOCKED_ITEMS = set(SKIP_PRE41_POTIONS)
    g = p.run_guide()
    return extend_after_current_checkpoint_v2(g)


def translated_step(step: dict[str, Any]) -> str:
    pos = step["pos"]
    action = ACTION_CN.get(step.get("action"), step.get("action") or "")
    eid = ITEM_CN.get(step.get("eid"), step.get("eid") or "")
    delta = f" [{step['delta']}]" if step.get("delta") else ""
    return f"{step['floor']} x{pos[0]}y{pos[1]} {action} {eid}{delta}".rstrip()


def write_outputs(g: Any) -> None:
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    result = {
        "ok": not g.errors,
        "final": g.snapshot(),
        "errors": g.errors,
        "warnings": g.warnings,
        "shop_purchases_zone3": 7,
        "steps": g.steps,
    }
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 三区快速通关Walk（31F起点，商店攻防7次）",
        "",
        f"- 结果：{'通过' if not g.errors else '未通过'}",
        f"- 最终：{state_text(g.state)} {g.state['floor']} x{g.state['x']}y{g.state['y']}",
        f"- 累计伤害：{g.state['dmg']}；开门：黄{g.state['yd']} / 蓝{g.state['bd']} / 红{g.state['rd']}",
        "- 说明：不打15F章鱼、不拿镐；商店价格按网页公式 money1=20+10*(times1+1)*times1；为41F半血陷阱控血，跳过 MT14 x9y6、MT34 x1y11、MT34 x11y10、MT34 x11y2、MT38 x11y11 血瓶；40F先主动清12个怪，再触发事件生成楼梯、钥匙和宝石；Boss后只吃钥匙和宝石，不吃蓝血瓶；不提前清零伤怪，留给后续双倍金币。",
        "",
    ]
    if g.errors:
        lines.append("## 错误")
        lines.extend(f"- {e}" for e in g.errors)
        lines.append("")
    lines.append("## 详细Walk")
    for i, step in enumerate(g.steps, 1):
        lines.append(f"{i:03d}. {translated_step(step)}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    g = generate()
    write_outputs(g)
    print(f"ok={not g.errors}")
    print(f"final={state_text(g.state)} {g.state['floor']} x{g.state['x']}y{g.state['y']}")
    print(f"json={OUT_JSON}")
    print(f"md={OUT_MD}")
    if g.errors:
        print("errors:")
        for err in g.errors:
            print(f"- {err}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
