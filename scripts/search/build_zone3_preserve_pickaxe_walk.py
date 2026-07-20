#!/usr/bin/env python3
"""Build the zone-3 preserve-pickaxe walk by transforming the verified minhp25 walk.

The minhp25 3区 route uses the 15F pickaxe at MT37 x10y5 to reach the inner-area
redKey (x7y5) for the MT38 x3y1 red door. That consumes the pickaxe, leaving none
for 4区's 48F 圣剑. This script produces a preserve variant: keep the 15F pickaxe
acquisition (step 141) but DO NOT use it; instead get the 38F red key from the
MT34 center 8-enemy event (redKey at x2y6), and skip the inner-area yellow keys
(x8y5/x9y5) + redPotions (x7y4/x7y3) behind the pickaxe wall. The 34F center
gives 4 yellow keys (compensating the 2 lost) + 1 red key.

The transformed walk is replayed through the canonical Game (zone3_game_route.py
--walk) and web-verified; it is not a coordinate patch.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "best" / "zone3_2atk1def_minhp_walk.json"
OUT = ROOT / "outputs" / "results" / "zone3_preserve_pickaxe_walk.json"

# MT34 center 8 enemies (pos -> eid), from the MT34 layout.
MT34_CENTER_ENEMIES = {
    (5, 4): "greenSlime", (5, 8): "ghostSkeleton",
    (7, 4): "swordsman", (7, 8): "redSlime",
    (9, 4): "blackSlime", (9, 8): "redKnight",
    (11, 4): "soldier", (11, 8): "bat",
}
# center corridor doors (already opened by minhp25 MT34 left path: x2y4, x2y8).
# inner doors to open per column x in (5,7,9,11): (x,5) and (x,7).
# reward positions after the 8-enemy event.
MT34_REWARD = [(2, 6, "redKey"), (1, 5, "yellowKey"), (3, 5, "yellowKey"),
               (1, 7, "yellowKey"), (3, 7, "yellowKey")]


def step(action: str, floor: str, x: int, y: int, eid: str | None = None, note: str = "") -> dict:
    return {"action": action, "floor": floor, "pos": [x, y], "eid": eid, "note": note}


def mt31_yellow_key_group_steps() -> list[dict]:
    """Positive-net key group found by the shared-Game resource probe.

    From the verified MT31 checkpoint these are three ordinary target clicks:
    two battles around one yellow door.  The final battle makes the four-key
    pocket auto-reachable, so the group costs one key and returns four (net
    +3YK).  Keeping the macro here makes the transform reproducible without an
    ignored ``outputs/`` probe file.
    """
    return [
        step("飞行", "MT31", 6, 2, None, "攻防成型后飞到31F取右下四钥匙组"),
        step("击杀", "MT31", 10, 6, "ghostSkeleton", "31F右下四钥匙组前置怪"),
        step("开门", "MT31", 11, 7, "yellowDoor", "31F右下四钥匙组黄门"),
        step("击杀", "MT31", 10, 9, "slimeMan", "击杀后auto拾取右下4黄钥匙，净+3YK"),
    ]


def mt31_late_yellow_key_group_steps() -> list[dict]:
    """Collect the still-intact MT31 upper-left four-key pocket.

    This is deliberately delayed until after the 40F boss: at the final zone-3
    stats its only damage is 14 HP.  One door and four keys make the group net
    +3YK, leaving enough keys for the mandatory 41F/42F climb in zone 4.
    """
    return [
        step("飞行", "MT31", 6, 10, None, "40F Boss后飞到31F取左上四钥匙组"),
        step("击杀", "MT31", 2, 6, "ghostSkeleton", "31F左上四钥匙组前置怪（14伤）"),
        step("开门", "MT31", 1, 5, "yellowDoor", "开门后auto清怪并拾取左上4黄钥匙，净+3YK"),
        step("飞行", "MT41", 6, 2, None, "飞回41F，作为4区起点"),
    ]


def yk_farm_steps() -> list[dict]:
    """Farm reachable yellow keys before the 34F center (which costs 8 YK for
    its 8 inner doors). The preserve route lost the 37F pickaxe-wall yellow
    keys (x8y5/x9y5), so it must replenish from MT31/MT32/MT33 lower-area keys
    that are reachable without spending YK. Duplicates already picked up by the
    minhp25 prefix are skipped by run_zone3 (block_at None)."""
    out: list[dict] = []
    out.append(step("飞行", "MT32", 10, 4, None, "飞到 MT32 补黄钥匙"))
    out.append(step("拾取", "MT32", 10, 4, "yellowKey", "32F 补黄钥匙 x10y4"))
    out.append(step("飞行", "MT33", 6, 3, None, "飞到 MT33 补黄钥匙"))
    out.append(step("拾取", "MT33", 6, 3, "yellowKey", "33F 补黄钥匙 x6y3"))
    return out


def mt34_center_steps() -> list[dict]:
    """34F center 8-enemy event -> redKey + 4 yellowKeys. Inserted right after
    the 2F yellowKey pickup (minhp25 step 78, YK=9 peak) so there is enough YK
    for the 8 inner doors. Hero flies to MT34 (lands at x3y1, the last 34F
    position), enters the center corridor at x3y6 (no need to open x2y4/x2y8
    corridor doors), kills the 8 enemies behind the 8 inner doors, and the
    event spawns redKey at (2,6) + 4 yellowKeys. The red key is carried to the
    38F red door (step 160)."""
    out: list[dict] = [
        step("拾取", "MT2", 3, 11, "bluePotion", "前移原路线第三瓶2F蓝血，覆盖31F钥匙组损耗"),
    ]
    out.extend(mt31_yellow_key_group_steps())
    out.append(step("飞行", "MT32", 6, 11, None, "飞到 MT32 买一次HP，补34F中心生存"))
    out.append(step("商店", "MT32", 10, 10, "hp", "32F HP购买一次（times1=8，+900HP）"))
    out.append(step("飞行", "MT34", 3, 1, None, "飞到 MT34 做中心八怪取红钥匙（YK=9 峰值处）"))
    # Kill the x2y3 slimeMan (blocks the corridor path) -- minhp25 does this at
    # step 84; doing it here first makes step 84 a no-op.
    out.append(step("击杀", "MT34", 2, 3, "slimeMan", "34F 清走廊 slimeMan x2y3"))
    # Open the corridor door x2y4 to access the center (x3y6). minhp25 opens
    # x2y4 later (step 85) for its left path; opening it here first is a no-op
    # there. x3 column is wall-blocked at y4, so the corridor door is required.
    out.append(step("开门", "MT34", 2, 4, "yellowDoor", "34F 中心走廊黄门 x2y4"))
    out.append(step("到达", "MT34", 3, 6, None, "进入中心八怪走廊 x3y6"))
    for x in (5, 7, 9, 11):
        # upper enemy (x,4) behind door (x,5)
        out.append(step("开门", "MT34", x, 5, "yellowDoor", f"34F 中心上黄门 x{x}y5"))
        out.append(step("击杀", "MT34", x, 4, MT34_CENTER_ENEMIES[(x, 4)], f"34F 中心八怪 x{x}y4"))
        out.append(step("到达", "MT34", x, 6, None, f"34F 中心回走廊 x{x}y6"))
        # lower enemy (x,8) behind door (x,7)
        out.append(step("开门", "MT34", x, 7, "yellowDoor", f"34F 中心下黄门 x{x}y7"))
        if x == 9:
            # Keep this non-zero-damage enemy for the final explicit battle.
            # Live auto may kill the zero-damage bat at x11y8, but an auto kill
            # does not fire the center reward event.
            continue
        out.append(step("击杀", "MT34", x, 8, MT34_CENTER_ENEMIES[(x, 8)], f"34F 中心八怪 x{x}y8"))
        out.append(step("到达", "MT34", x, 6, None, f"34F 中心回走廊 x{x}y6"))
    out.append(step("击杀", "MT34", 9, 8, "redKnight", "34F 中心最后显式战斗，触发4黄1红事件"))
    out.append(step("拾取", "MT34", 3, 5, "yellowKey", "立即点击中心奖励入口，auto收取4黄1红"))
    # The explicit final battle spawns the rewards after that click completes;
    # a subsequent real item click is therefore required to start auto pickup.
    out.append(step("飞行", "MT2", 3, 5, None, "飞回 MT2 继续原路径"))
    return out


def main() -> int:
    data = json.loads(SRC.read_text(encoding="utf-8"))
    steps = data["steps"]
    # Identify the pickaxe-use + inner-area steps to remove by content.
    # Remove: use_pickaxe (MT37 x10y5), wall keys (MT37 x9y5 pickup + its auto),
    #         fly MT37 x2y1 + x7y4/x7y3 redPotions.
    remove_keys = set()  # indices to drop
    for i, s in enumerate(steps):
        fid = s.get("floor")
        act = s.get("action")
        eid = s.get("eid") or ""
        x, y = s.get("pos", [0, 0])
        # The new MT31 four-key group already clears x10y6 and x11y7.  Do not
        # continue through the extra x9y8 yellow door solely for the x8y8 blue
        # potion: preserving that one key is exactly what the 39F suffix needs.
        if 114 <= i <= 118:
            remove_keys.add(i)
        if fid == "MT37" and act == "使用镐" and (x, y) == (10, 5):
            remove_keys.add(i)  # step 145 use pickaxe
        if fid == "MT37" and act == "拾取" and (x, y) == (9, 5) and eid == "yellowKey":
            remove_keys.add(i)  # step 146 wall yellowKey (+ auto x8y5/x7y5)
        if fid == "MT37" and act == "飞行" and (x, y) == (2, 1):
            remove_keys.add(i)  # step 153 fly MT37 (only for x7 redPotions)
        if fid == "MT37" and act == "拾取" and (x, y) in ((7, 4), (7, 3)):
            remove_keys.add(i)  # step 154-155 x7 redPotions (behind wall)
        # The inserted HP shop consumes the same purchase slot and raises later
        # costs. Keep the first original late ATK buy (source step131) and drop
        # the second (step132); otherwise it needs 1120G with only ~407G left.
        if i == 132 and act == "商店" and eid == "atk":
            remove_keys.add(i)
    # Build new step list: keep up to MT38 entry, insert 34F center before the
    # MT38 redDoor (x3y1), keep the rest.
    new_steps: list[dict] = []
    inserted = False
    for i, s in enumerate(steps):
        if i in remove_keys:
            continue
        if i == 122:
            new_steps.append(step("飞行", "MT2", 1, 10, None, "36F redKnight 前补生存血量"))
            new_steps.append(step("拾取", "MT2", 4, 10, "bluePotion", "前移第一瓶2F蓝血 +200"))
            new_steps.append(step("拾取", "MT2", 3, 10, "bluePotion", "前移第二瓶2F蓝血 +200"))
            new_steps.append(step("飞行", "MT36", 11, 2, None, "飞回36F继续 redKnight"))
        if i == 136:
            new_steps.append(step("飞行", "MT19", 1, 2, None, "36F soldier 前补最小生存血量"))
            new_steps.append(step("拾取", "MT19", 4, 1, "redPotion", "前移原留镐分支红血 +100"))
            new_steps.append(step("飞行", "MT36", 11, 2, None, "飞回36F继续左侧路线"))
        if i == 142:
            new_steps.append(step("拾取", "MT15", 11, 8, "bluePotion", "留镐分支37F前生存垫 +400"))
            new_steps.append(step("飞行", "MT14", 6, 10, None, "37F第二只 redKnight 前补最小血量"))
            new_steps.append(step("拾取", "MT14", 9, 6, "redPotion", "恢复 prior-minhp 删除红血 +100"))
        if i == 174:
            new_steps.append(step("拾取", "MT38", 11, 11, "bluePotion", "38F 可选蓝血 +800，补盾房及39F生存"))
        if i == 194:
            # HP compression: replace the oversized late +1100 shop and +200
            # potion with a key-funded exact survival bundle.  MT38 x10y7
            # yields three auto keys; two doors then buy +800/+100 HP.  The
            # strict full replay finishes 40F at 45 HP and the late key pocket
            # at 31 HP, while retaining enough keys for zone 4.
            new_steps.append(step("飞行", "MT38", 10, 1, None, "39F解谜后取38F三黄钥匙组"))
            new_steps.append(step("击杀", "MT38", 10, 7, "redKnight", "击杀后auto收取3黄钥匙"))
            new_steps.append(step("飞行", "MT31", 6, 10, None, "用1黄钥匙取31F蓝血"))
            new_steps.append(step("开门", "MT31", 9, 8, "yellowDoor", "31F蓝血前黄门"))
            new_steps.append(step("拾取", "MT31", 8, 8, "bluePotion", "31F蓝血 +800"))
            new_steps.append(step("飞行", "MT16", 6, 10, None, "用1黄钥匙取16F红血"))
            new_steps.append(step("击杀", "MT16", 10, 5, "zombie", "16F红血前置怪"))
            new_steps.append(step("开门", "MT16", 10, 4, "yellowDoor", "16F红血前黄门"))
            new_steps.append(step("拾取", "MT16", 11, 3, "redPotion", "16F红血 +100"))
            new_steps.append(step("飞行", "MT39", 11, 2, None, "飞回39F按原路上40F"))
        new_steps.append(s)
        if s.get("floor") == "MT41" and s.get("action") == "换层":
            new_steps.extend(mt31_late_yellow_key_group_steps())
        # Insert after MT2 oldman reward: YK=9 is the only point that can pay
        # x2y4 corridor + eight center doors. HP is supplied explicitly above.
        if (not inserted and s.get("floor") == "MT2" and s.get("action") == "事件奖励"
                and s.get("eid") == "oldman"):
            new_steps.extend(mt34_center_steps())
            inserted = True
    print(f"removed {len(remove_keys)} steps: {sorted(remove_keys)}")
    print("inserted MT31 key groups + exact pre-boss potion bundle + early HP shop + 34F center")
    print(f"new step count: {len(new_steps)} (was {len(steps)})")
    out = dict(data)
    out["steps"] = new_steps
    out["note"] = ("preserve-pickaxe transform of minhp25: drop 37F pickaxe use + "
                   "inner-area keys/redPotions; add 34F center 8-enemy event for the "
                   "38F red key. 15F pickaxe kept (unused) for 4区 48F 圣剑.")
    out["source_walk"] = str(SRC)
    out.pop("removed_potions", None)  # reset; replay will re-derive if needed
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
