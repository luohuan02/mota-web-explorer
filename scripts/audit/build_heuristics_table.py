#!/usr/bin/env python3
"""构建离线阈值表 data/heuristics_table.json。

算每只怪的 atk 阈值(使战斗回合数突降的 atk 值)+ def 免伤阈值 + dmg 曲线,
以及每颗宝石(+ratio atk/def)对所有怪的减伤。验证搜索经验:
  #6 23 攻 = skeleton(骷髅人)+ bluePriest(法师)阈值(回合数突降)
  #7 26 攻 = skeletonSoldier(骷髅士兵)阈值
  MT10 boss 清场: skeleton/skeletonSoldier/skeletonCaptain 在 27/27 下的总伤

战斗公式同 Game.enemy_damage(标准 special=0 怪): damage = (turns-1)*per,
  turns = ceil(hp / max(1, atk-def)), per = max(0, enemy.atk - hero.def)。
带 special 的怪(先攻/魔攻/反击等)按 Game.enemy_damage 修饰算,法术场(15)/
半血(16)非战斗怪只标记不进阈值表。

输出给搜索排序(sub-goal 净 dmg 收益)+ h(剩余 dmg 估计)+ 经验验证用。
"""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path("D:/claude/mota-web-explorer")
ENEMIES = json.load(open(ROOT / "data/maps/enemy_stats.json", encoding="utf-8-sig"))["enemys"]


def floor_ratio(fid: str) -> int:
    n = int(fid[2:])
    if 11 <= n <= 20:
        return 2
    if 31 <= n <= 40:
        return 4
    if 41 <= n <= 50:
        return 5
    return 1


def calc_damage(enemy: dict, atk: int, df: int, cross: bool = False) -> float:
    """复用 Game.enemy_damage 的纯函数版(无 Game 实例/flags)。

    标准 special=0: damage = (turns-1)*per。
    不处理 redKing 封印/终态(需 flags),这些怪在阈值表标 "special_case"。
    """
    mon_def = int(enemy["def"])
    mon_hp = int(enemy["hp"])
    a = atk * (2 if cross else 1)
    hero_hit = max(0, a - mon_def)
    if hero_hit <= 0:
        return float("inf")
    turns = math.ceil(mon_hp / hero_hit)
    per = max(0, int(enemy["atk"]) - df)
    special = enemy.get("special", 0)
    specials = set(special if isinstance(special, list) else [special])
    if 2 in specials:
        per = int(enemy["atk"])  # 魔攻：无视防御
    if 4 in specials:
        per *= 2
    if 5 in specials:
        per *= 3
    if 6 in specials:
        per *= int(enemy.get("n", 4))
    init = 0
    if 1 in specials:
        init += per  # 先攻
    if 7 in specials:
        init += int(enemy.get("defValue", 0)) * df
    counter = 0
    if 8 in specials:
        counter = int(enemy.get("atkValue", 0)) * atk
    return float(init + (turns - 1) * per + turns * counter)


def is_battle_enemy(enemy: dict) -> bool:
    """是否是正常战斗怪(可走阈值分析)。法术场(15)/半血(16)非战斗。"""
    special = enemy.get("special", 0)
    specials = set(special if isinstance(special, list) else [special])
    if 15 in specials or 16 in specials:
        return False
    if int(enemy.get("hp", 0)) <= 0 or int(enemy.get("atk", 0)) <= 0:
        return False
    return True


def atk_breakpoints(enemy: dict, max_turns: int = 25) -> list[dict]:
    """使 turns <= k 的最小 atk。

    turns = ceil(hp / (atk - def))。atk = def + ceil(hp / k) 使 turns 恰好 <= k。
    每个相邻 k 之间是突降点: atk 跨过 def+ceil(hp/k) 时 turns 从 k+1 降到 k,
    dmg 减少 per(当前 per = enemy.atk - hero.def,取 enemy.atk 作 per 上限标记)。
    """
    mon_def = int(enemy["def"])
    mon_hp = int(enemy["hp"])
    out = []
    seen = set()
    for k in range(1, max_turns + 1):
        d = max(1, math.ceil(mon_hp / k))
        atk_needed = mon_def + d
        if atk_needed in seen:
            continue
        seen.add(atk_needed)
        out.append({"turns": k, "atk_needed": atk_needed, "hero_hit": d})
    return out


def atk_drop_points(enemy: dict) -> list[dict]:
    """atk 突降点: 相邻 turns 间的 atk 阈值,跨过即少打 1 回合。

    返回 [{atk, turns_before, turns_after, dmg_saved_per_def}],
    dmg_saved = per(打怪时 per = enemy.atk - hero.def)。
    用 enemy.atk 作 per 上限标记(per_max),实际 per 取决于 hero.def。
    """
    bps = atk_breakpoints(enemy)
    out = []
    for i in range(len(bps) - 1):
        hi = bps[i]  # turns 小(少回合)
        lo = bps[i + 1]  # turns 大(多回合)
        out.append({
            "atk": hi["atk_needed"],  # 跨过此 atk,turns 降到 hi["turns"]
            "turns_after": hi["turns"],
            "turns_before": lo["turns"],
            "saves_turns": lo["turns"] - hi["turns"],
        })
    return out


def gem_reduction(enemy: dict, atk: int, df: int, gem: str, ratio: int = 1) -> float:
    """单颗宝石对该怪的 dmg 减少(在给定 hero atk/def 下)。

    redGem(+ratio atk): dmg(atk,df) - dmg(atk+ratio,df)。跨阈值突降或线性减 turns。
    blueGem(+ratio def): dmg(atk,df) - dmg(atk,df+ratio)。线性减 per*turns。
    """
    before = calc_damage(enemy, atk, df)
    if gem == "redGem":
        after = calc_damage(enemy, atk + ratio, df)
    elif gem == "blueGem":
        after = calc_damage(enemy, atk, df + ratio)
    else:
        return 0.0
    if math.isinf(before) and math.isinf(after):
        return 0.0
    if math.isinf(before):
        return float("inf")  # 从打不死到打得死,价值极大
    if math.isinf(after):
        return 0.0
    return before - after


def find_atk_drop_at(enemy: dict, atk: int) -> bool:
    """atk 处是否是该怪的突降点(turns 比 atk-1 少)。"""
    if not is_battle_enemy(enemy):
        return False
    d1 = calc_damage(enemy, atk, 0)
    d0 = calc_damage(enemy, atk - 1, 0)
    if math.isinf(d0) and not math.isinf(d1):
        return True
    if math.isinf(d0) or math.isinf(d1):
        return False
    # turns 突降: dmg 降幅 >= per_max(enemy.atk) 的整数倍(少打整回合)
    if d0 <= d1:
        return False
    return (d0 - d1) >= int(enemy["atk"]) - 1  # 少 1 回合至少省 per>=atk-1


def build_table() -> dict:
    # zone1 出现的怪(MT1-10),用于详细表 + 经验验证
    zone1_eids = [
        "greenSlime", "redSlime", "bat", "skeleton", "skeletonSoldier",
        "skeletonCaptain", "bluePriest",
    ]
    out_enemies = {}
    for eid, e in ENEMIES.items():
        if not is_battle_enemy(e):
            out_enemies[eid] = {
                "name": e["name"], "non_battle": True,
                "special": e.get("special", 0),
                "note": "法术场/半血/空属性,非战斗怪",
            }
            continue
        entry = {
            "name": e["name"],
            "hp": int(e["hp"]), "atk": int(e["atk"]), "def": int(e["def"]),
            "money": int(e.get("money", 0)),
            "special": e.get("special", 0),
            "def_immune": int(e["atk"]),  # hero.def >= enemy.atk -> per=0 免伤
            "atk_breakpoints": atk_breakpoints(e),
            "atk_drops": atk_drop_points(e),
        }
        out_enemies[eid] = entry

    # 宝石/装备增量(zone1 ratio=1)
    gems = {
        "redGem": {"delta_atk": 1, "delta_def": 0, "ratio_per_zone": {1: 1, 2: 2, 3: 1, 4: 4, 5: 5}},
        "blueGem": {"delta_atk": 0, "delta_def": 1, "ratio_per_zone": {1: 1, 2: 2, 3: 1, 4: 4, 5: 5}},
        "greenGem": {"delta_atk": 0, "delta_def": 0, "note": "经验值宝石(zone1 +0? 需确认)"},
    }
    equipment = {
        "sword1": {"delta_atk": 10}, "shield1": {"delta_def": 10},
        "sword2": {"delta_atk": 20}, "shield2": {"delta_def": 20},
    }

    # 经验验证: 找 23/26/27 攻处哪些 zone1 怪突降
    exp_check = {}
    for atk_val in [22, 23, 24, 25, 26, 27]:
        drops = [eid for eid in zone1_eids
                 if eid in ENEMIES and is_battle_enemy(ENEMIES[eid])
                 and find_atk_drop_at(ENEMIES[eid], atk_val)]
        exp_check[f"atk{atk_val}"] = drops

    # MT10 boss 清场总伤(在 27/27 下): 6 skeleton + 2 skeletonSoldier + 1 skeletonCaptain
    mt10_boss = {
        "composition": {"skeleton": 6, "skeletonSoldier": 2, "skeletonCaptain": 1},
        "dmg_at_27_27": {},
    }
    for eid, cnt in mt10_boss["composition"].items():
        e = ENEMIES[eid]
        per_monster = calc_damage(e, 27, 27)
        mt10_boss["dmg_at_27_27"][eid] = {
            "per": per_monster, "count": cnt, "total": per_monster * cnt,
        }
    mt10_boss["dmg_total_27_27"] = sum(
        v["total"] for v in mt10_boss["dmg_at_27_27"].values())

    # 宝石减伤样例(zone1, hero atk/def 在典型 22-27 区间)
    gem_sample = {}
    for atk_val in [22, 24, 26]:
        for def_val in [22, 24, 26]:
            key = f"atk{atk_val}_def{def_val}"
            gem_sample[key] = {}
            for gem in ["redGem", "blueGem"]:
                reductions = {}
                for eid in zone1_eids:
                    if eid in ENEMIES and is_battle_enemy(ENEMIES[eid]):
                        r = gem_reduction(ENEMIES[eid], atk_val, def_val, gem, ratio=1)
                        if r > 0:
                            reductions[eid] = r
                gem_sample[key][gem] = reductions

    return {
        "meta": {
            "source": "data/maps/enemy_stats.json",
            "formula": "damage = init + (turns-1)*per + turns*counter; "
                       "turns=ceil(hp/(atk-def)), per=max(0,enemy.atk-hero.def)",
            "note": "atk 阈值=使 turns 突降的 atk; def>=enemy.atk 免伤; "
                    "宝石减伤在给定 hero atk/def 下算",
        },
        "enemies": out_enemies,
        "gems": gems,
        "equipment": equipment,
        "experience_check": exp_check,
        "mt10_boss": mt10_boss,
        "gem_reduction_sample": gem_sample,
    }


def main() -> int:
    table = build_table()
    out = ROOT / "data" / "heuristics_table.json"
    out.write_text(json.dumps(table, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"写入 {out}")

    # 控制台摘要: 经验验证
    ec = table["experience_check"]
    print("\n=== 经验验证: atk 突降点 ===")
    for k, v in ec.items():
        print(f"  {k}: {v}")
    print(f"\n=== MT10 boss 清场总伤(27/27)=== {table['mt10_boss']['dmg_total_27_27']}")
    for eid, v in table["mt10_boss"]["dmg_at_27_27"].items():
        print(f"  {eid}: per={v['per']} ×{v['count']} = {v['total']}")

    # 关键怪的阈值表
    print("\n=== zone1 关键怪 atk 阈值 ===")
    for eid in ["greenSlime", "bat", "skeleton", "bluePriest",
                "skeletonSoldier", "skeletonCaptain"]:
        e = table["enemies"].get(eid, {})
        if "atk_drops" not in e:
            continue
        drops = [(d["atk"], d["turns_after"]) for d in e["atk_drops"][:6]]
        print(f"  {eid}({e.get('name','')} hp={e.get('hp')} atk={e.get('atk')} def={e.get('def')}): "
              f"def_immune={e['def_immune']} atk_drops={drops}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
