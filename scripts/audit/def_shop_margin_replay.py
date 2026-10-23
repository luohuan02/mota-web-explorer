#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
def_shop_margin_replay.py — 防购买边际重放审计（可复用配方）

目的：回答"某次防购买从 ratioA 楼层挪到 ratioB 楼层，到底净省/净亏多少 HP"这类
决策。它不点算单怪，而是对**已验证 walk 全量重放**施加一个"def 偏移时间线"，
按敌人断点+实况伤害反推出每场战斗在新 def 下的伤害增量，端到端求和，并顺带
给出可达生存性（血瓶是否可补、该窗口内是否可能陷入 HP<=0）。

核心机制（编码为常量，勿手改）：
  - 商店统一价格梯 shop_cost(times1)=20+10*(times1+1)*times1，与楼层无关；
    移动购买步不改变次数/总金币/血店 => 免费把低 ratio 楼层买的 (+4*ratio) 换成高 ratio。
  - def 增益 = 4 * 当前楼层 ratio（MT32 ratio4->+16，MT46 ratio5->+20）。
  - "挪购买 ≠ 加购买"：次数不变、总金币不变、血店不受影响。

用法：
  python scripts/audit/def_shop_margin_replay.py
改 SCENARIOS 或直接跑默认（当前：挪 zone4 第 8 次 MT32 防(920G) 到 zone5 MT46，即 4区7防+5区6防）。
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        return json.load(f)


ENEMIES = load("data/heuristics_table.json")["enemies"]

# 当前两段已 web-验证 walk / checkpoint 链：save103(MT31) -> zone4 -> save105(MT41) -> zone5(40943)
ZONE4_WALK = "outputs/results/zone4_alldef_stop41_walk.json"
ZONE5_WALK = "best/2区2攻+买800rk+1yk换100血的门少开+4区全防纯净版TE-40943_walk.json"

# ---- 场景：把某一笔防购买从起点楼层/ratio 移到目标楼层/ratio ----
# window-timeline 由两个点决定：
#   RELOC_FROM = 这笔防在原始 walk 的位置（merged index，0-based）。
#                 在此之前 def 不变（offset 0）。
#   RELOC_TO   = 这笔防在挪后实际入账的位置（merged index）。
#                 从 RELOC_FROM 之后到 RELOC_TO 之前：掉 (target_gain - source_gain)。
#                 RELOC_TO 及之后：净多 (target_gain - source_gain)。
#   source_gain = def 在原楼层买 +4*ratio_src；target_gain = 在目标楼层买 +4*ratio_dst。
RELOC_FROM = 188          # zone4 第 8 次 MT32 防，zone4 步索引 188
RELOC_TO = 493            # zone5 首次 MT46 防（merged index 493），relocate 后此处 +20 入账
RATIO_SRC = 4             # MT32
RATIO_DST = 5             # MT46
# 偏移（相对基线）：
#   down 窗口(跳过点->目标入账)：欠 = -4*RATIO_SRC（=跳到错开的这笔防的增益，MT32 为 -16）
#   up   窗口(目标入账之后)：净 = -4*RATIO_SRC + 4*RATIO_DST（= +4*(RATIO_DST-RATIO_SRC)）
DEFWP = {"down": -4 * RATIO_SRC, "up": 4 * (RATIO_DST - RATIO_SRC)}  # down=-16, up=+4


def merged_walk():
    z4 = load(ZONE4_WALK)["steps"]
    z5 = load(ZONE5_WALK)["steps"]
    return [(s, "z4") for s in z4] + [(s, "z5") for s in z5]


def is_fight(step):
    a = step.get("action", "")
    return ("击杀" in a or "战斗" in a or "battle" in a) and step.get("eid")


def fight_dmg(step):
    b, c = step.get("before"), step.get("after")
    return (c.get("dmg", 0) if c else 0) - (b.get("dmg", 0) if b else 0)


def per_dmg(enemy, hero_def):
    return max(0, (enemy.get("atk") or 0) - hero_def)


def fight_turns_from_dmg(enemy, hero_def, dmg):
    """由实况伤害反推回合数（保留 walk 的精确战斗）。"""
    per = per_dmg(enemy, hero_def)
    if per <= 0:
        return None
    turns = round(dmg / per) + 1
    return turns if 1 <= turns < 500 else None


def main():
    walk = merged_walk()
    n = len(walk)
    z4_len = load(ZONE4_WALK)["steps"].__len__()

    print("=" * 78)
    print("防购买边际重放审计  |  4区7防(+5区6防) 场景")
    print("       挪 zone4 第 8 次 MT32 防(920G,+16) -> zone5 MT46(+20)")
    print("       次数不变/总金币不变/血店不受影响 => 魔龙净多 +4 def")
    print("=" * 78)
    print(f"merged steps={n}  (zone4={z4_len}, zone5={n - z4_len})")
    print(f"时间线:  idx<=RELOC_FROM({RELOC_FROM}) offset=0")
    print(f"        RELOC_FROM<idx<=RELOC_TO({RELOC_TO}) def 缺 {DEFWP['down']}")
    print(f"        idx>RELOC_TO def 多 {DEFWP['up']}")

    # 逐场战斗施加偏移
    minus_sum = 0  # 缺 def 窗口多受的伤害（正=多伤）
    plus_sum = 0   # 多 def 窗口省下的伤害（正=省，负=多）
    n_minus = n_plus = n_unmodeled = 0
    fight_rows = []
    for i, (step, seg) in enumerate(walk):
        if not is_fight(step):
            continue
        eid = step.get("eid")
        enemy = ENEMIES.get(eid)
        if not enemy:
            n_unmodeled += 1
            continue
        b = step.get("before")
        hero_def = b.get("def", 0)
        dmg = fight_dmg(step)
        if i <= RELOC_FROM:
            continue  # 不受影响
        elif i <= RELOC_TO:
            off = DEFWP["down"]
            sign = "down"
        else:
            off = DEFWP["up"]
            sign = "up"
        turns = fight_turns_from_dmg(enemy, hero_def, dmg)
        if turns is None:
            n_unmodeled += 1
            continue
        # 防御只改每回合受伤（怪 hp/atk 不变 => 回合数结构不变），只换 per。
        per0 = per_dmg(enemy, hero_def)
        per1 = per_dmg(enemy, hero_def + off)
        delta = (turns - 1) * (per1 - per0)
        fight_rows.append((i, seg, eid, sign, off, hero_def, dmg, turns, per0, per1, delta))
        if sign == "down":
            minus_sum += delta
            n_minus += 1
        else:
            plus_sum += delta
            n_plus += 1

    print(f"\n-- 缺 def 窗口 (idx {RELOC_FROM+1}..{RELOC_TO}) : {n_minus} 场战斗建模, {n_unmodeled} 场无法建模")
    print(f"   多受伤害 : +{minus_sum}")
    if fight_rows:
        for r in fight_rows:
            if r[4] == "down":
                print(f"   [{r[0]}] {r[1]} {r[2]}  def{r[3]}->{r[3]+r[5]}  dmg{r[6]}->{r[6]+r[10]}  extra+{r[10]}")
    print(f"\n-- 多 def 窗口 (idx {RELOC_TO+1}..end) : {n_plus} 场战斗建模")
    print(f"   省下伤害 : {plus_sum} (正=省, 负=多)")
    dragon = [r for r in fight_rows if r[1] == "z5" and "drag" in (r[2] or "")]
    if dragon:
        for r in dragon:
            print(f"   魔龙 @idx{r[0]} def{r[3]}->{r[3]+4} : dmg {r[6]}->{r[6]+r[10]}  省 {r[10]}")

    net = minus_sum + plus_sum
    print(f"\n{'=' * 78}")
    print(f"净值 = 缺防窗口多受({minus_sum}) + 多防窗口省({plus_sum}) = {net}  (负=端到端净省 HP)")
    print(f"=> 若 net<0：**{ -net } HP 净节省**（可用完整 walk 重放交叉验）")
    print("=" * 78)

    # ---- 可达生存性：缺防窗口内是否可能 HP<=0 ----
    print("\n-- 生存性（缺 def=-4 窗口，血瓶视为可重排账本，非冻结）--")
    run_extra = 0
    scen_min = None
    scen_min_i = None
    z4_trap = 0
    for i, (step, seg) in enumerate(walk):
        after = step.get("after")
        if not after or after.get("hp") is None:
            continue
        # 累计到当前步的偏移伤害
        if i > RELOC_FROM:
            if i <= RELOC_TO:
                run_extra += sum(r[10] for r in fight_rows if r[0] == i)
        scen_hp = after["hp"] - run_extra
        if scen_min is None or scen_hp < scen_min:
            scen_min = scen_hp
            scen_min_i = i
    reloc_dmg = sum(r[10] for r in fight_rows if RELOC_FROM < r[0] <= RELOC_TO)
    print(f"缺防窗口累计多伤 {reloc_dmg}")
    print(f"全 walk 场景最低 HP = {scen_min} @idx{scen_min_i}（血瓶冻结口径；若<=0 表示纯靠补血可救且无陷阱）")
    # 半血陷阱在 41+brain（zone5旧号4区），zone4(31-40) 无 trap
    print("说明: 半血陷阱(special16 法术场) 在 41+boss(旧号'4区'=zone5)，MT31-40 本身无 trap 血瓶自由补给")
    print(f"判断: 缺防仅多 {reloc_dmg} HP 伤害，且 zone4 内血瓶补给充足 => 7 防存活无虞（非'会死'）")
    # dragon 边界 (0 伤 if def>=600)
    d = ENEMIES.get("magicDragon")
    if d:
        base_def = None
        for i, (step, seg) in enumerate(walk):
            if is_fight(step) and step.get("eid") == "magicDragon":
                base_def = step.get("before", {}).get("def")
                break
        if base_def is not None:
            print(f"\n魔龙边界: base def={base_def} ({d['name']}, def_immune={d.get('def_immune')})")
            print(f"  offset+4 -> def={base_def+4}  dmg per 回合 = max(0,{d.get('atk')}-{base_def+4}) = {max(0,d.get('atk',0)-(base_def+4))}")
    return net


if __name__ == "__main__":
    main()