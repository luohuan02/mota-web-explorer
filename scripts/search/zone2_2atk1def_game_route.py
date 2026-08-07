#!/usr/bin/env python3
"""2区 2ATK1DEF 分支 Game 类重放（auto ON）。

best/zone2_2atk1def_branch_walk.md 的动作是对的（早期 logic verify 生成），但金币标注
过期（不含 auto_sweep 隐式击杀）。本脚本解析该 .md（中文 eid）-> 英文 eid steps，
跑 run_zone1 + apply_mt10_supply + run_zone2(steps)，输出 Game 类 JSON
（含 auto_sweep，金币正确）供 gen_zone_walk_md.py 重新生成 .md。

run_zone2 已重构为接收 steps 列表（默认仍读 canonical replay）。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from src.solver.game_route import Game, read_json, state_line
from scripts.search.zone2_game_route import run_zone1, apply_mt10_supply, run_zone2, SAVE1
from scripts.baseline import replay_zone2_guide_route as zone2_seed
from scripts.search.search_zone2_macro_routes import DEFAULT_OPTIONS, clone_floors

WALK_MD = ROOT / "best" / "zone2_2atk1def_branch_walk_source.md"
OUT_JSON = ROOT / "outputs" / "results" / "zone2_2atk1def_game_route.json"

# 中文 eid -> 英文 eid（.md 用中文，run_zone2 要英文）
CN_TO_EN = {
    # enemies
    "绿头怪": "greenSlime", "红头怪": "redSlime", "小黑": "blackSlime",
    "小蝙蝠": "bat", "大蝙蝠": "bigBat", "吸血鬼": "vampire",
    "初级法师": "bluePriest", "高级法师": "redPriest",
    "骷髅人": "skeleton", "骷髅士兵": "skeletonSoldier",
    "兽人": "zombie", "兽人武士": "zombieKnight",
    "石头人": "rock", "幽灵": "slimeMan", "黄卫兵": "yellowGuard",
    # doors
    "黄门": "yellowDoor", "蓝门": "blueDoor", "红门": "redDoor", "机关门": "specialDoor",
    # items
    "红宝石": "redGem", "蓝宝石": "blueGem",
    "黄钥匙": "yellowKey", "蓝钥匙": "blueKey", "红钥匙": "redKey",
    "红血瓶": "redPotion", "蓝血瓶": "bluePotion",
    "铁剑": "sword1", "铁盾": "shield1", "银剑": "sword2", "银盾": "shield2",
    "暗墙": "fakeWall", "十字架": "cross", "圣水": "superPotion",
    "楼层传送器": "fly",
    # NPCs
    "老人": "oldman", "小偷": "thief", "商人": "trader",
}

# .md 动作行 regex：- MTx xNyN <action> <eid>? [annotations]? (note)?
LINE_RE = re.compile(r"^- (MT\d+) x(\d+)y(\d+) (\S+)(.*)$")


def parse_walk_md(md_path: Path) -> list[dict]:
    """解析 .md -> steps [{floor, pos, action, eid, note}]（英文 eid）。

    .md 有两段：guide_after（G=922）和 best_after（G=930）。route_chains 跟踪
    best_after（current_best 分支，zone1 末 HP=722 G=313 + supply），只解析它。
    """
    text = md_path.read_text(encoding="utf-8")
    # 只取 best_after 段（## best_after_mt10_boss_supply 到文件末尾）
    marker = "## best_after_mt10_boss_supply"
    idx = text.find(marker)
    if idx < 0:
        raise RuntimeError(f"未找到 {marker} 段")
    text = text[idx:]
    steps = []
    unmapped = set()
    for line in text.splitlines():
        m = LINE_RE.match(line)
        if not m:
            continue
        fid, x, y, action, rest = m.groups()
        rest = rest.strip()
        eid_cn = None
        note = ""
        # eid：rest 不以 [ 或 ( 开头时，第一个 token 是 eid
        if rest and not rest.startswith("[") and not rest.startswith("("):
            eid_cn = rest.split()[0]
        # note：括号内
        note_m = re.search(r"\(([^)]*)\)\s*$", rest)
        if note_m:
            note = note_m.group(1)
        # eid 中文 -> 英文（商店 eid blueShop:attack 保留原样）
        eid = None
        if eid_cn:
            if eid_cn in CN_TO_EN:
                eid = CN_TO_EN[eid_cn]
            elif ":" in eid_cn or eid_cn in ("blueShop:attack", "blueShop:defense", "blueShop:hp"):
                eid = eid_cn  # 商店 eid 保留
            else:
                unmapped.add(eid_cn)
                eid = eid_cn  # 先用中文，跑出错再查
        steps.append({
            "floor": fid,
            "pos": [int(x), int(y)],
            "action": action,
            "eid": eid,
            "note": note,
        })
    if unmapped:
        print(f"WARN unmapped eids: {sorted(unmapped)}")
    return steps


def _is_step(s: dict, floor: str, pos: tuple[int, int], action: str | None = None, eid: str | None = None) -> bool:
    if s.get("floor") != floor or tuple(s.get("pos", ())) != pos:
        return False
    if action is not None and s.get("action") != action:
        return False
    if eid is not None and s.get("eid") != eid:
        return False
    return True


def optimize_zone2_steps(steps: list[dict]) -> list[dict]:
    """Apply small hand-audited ordering fixes to the parsed 2ATK1DEF seed.

    The source markdown is kept as a historical seed. These rewrites are local
    replay-normalization rules found during live verification:
    - do not walk down from 17F to 16F only to immediately fly away;
    - buy the 15F blue key before entering 11F's lower-left/shield room batch;
    - postpone the 16F super potion detour before the 20F vampire.
    """
    out = list(steps)

    # 17F sword -> 9F key pocket: the MT16 downstairs step only creates an
    # empty report section before an immediate floor transfer to MT9.
    out = [
        s for s in out
        if not _is_step(s, "MT16", (6, 11), "换层")
    ]

    # Reorder: after MT16 lower-left resources, buy the 15F blue key first,
    # then do the MT11 lower-left key batch and shield room in one MT11 visit.
    try:
        mt11_start = next(
            i for i, s in enumerate(out)
            if _is_step(s, "MT11", (6, 11), "传送")
            and i + 1 < len(out)
            and _is_step(out[i + 1], "MT11", (5, 9), "开门", "yellowDoor")
        )
        trader = next(
            i for i, s in enumerate(out[mt11_start + 1:], mt11_start + 1)
            if _is_step(s, "MT15", (11, 11), "商人", "trader")
        )
        mt11_return = next(
            i for i, s in enumerate(out[trader + 1:], trader + 1)
            if _is_step(s, "MT11", (6, 11), "传送")
        )
        mt11_batch = out[mt11_start:trader]
        trader_step = out[trader]
        shield_tail = out[mt11_return + 1:]
        out = out[:mt11_start] + [trader_step] + mt11_batch + shield_tail
    except StopIteration:
        print("WARN optimize: MT15/MT11 reorder pattern not found")

    # 20F vampire is barely survivable without the 16F super potion detour.
    # Keep the oldman/superPotion for later stat-scaled use.
    drop_start = drop_end = None
    for i, s in enumerate(out):
        if _is_step(s, "MT16", (9, 11), "击杀", "slimeMan"):
            drop_start = i
        if drop_start is not None and _is_step(s, "MT16", (11, 11), "使用道具", "superPotion"):
            drop_end = i + 1
            break
    if drop_start is not None and drop_end is not None:
        out = out[:drop_start] + out[drop_end:]
    else:
        print("WARN optimize: MT16 superPotion detour pattern not found")

    return out


def replace_mt14_red_key_fight_with_mt12_merchant(steps: list[dict]) -> list[dict]:
    """Replace the named red-key acquisition macro, preserving the verified scaffold.

    The leaderboard strategy buys the 12F 800G red key and therefore does not
    enter the mutually-exclusive 14F three-zombieKnight reward pocket.  This is
    a floor-event strategy substitution; every retained/inserted action is
    still replayed by the shared strict Game and later by real target clicks.
    """
    start = next(
        i for i, step in enumerate(steps)
        if _is_step(step, "MT14", (6, 11), "传送") and "红钥匙" in step.get("note", "")
    )
    end = next(
        i for i, step in enumerate(steps[start:], start)
        if _is_step(step, "MT14", (3, 1), "事件奖励", "redKey")
    )
    merchant = {
        "floor": "MT12", "pos": [1, 1], "action": "商人", "eid": "trader",
        "note": "12F 商人：800G -> 1 红钥匙",
    }
    return steps[:start] + [merchant] + steps[end + 1:]


def remove_def_shop(steps: list[dict]) -> list[dict]:
    """2攻线：去掉 12F 防御商店购买，只保留 2 攻击。

    2ATK1DEF 的 -8 DEF 在 2区多挨约 1200 HP，但 2攻 同时把 14F 三兽人武士红钥匙
    换成 12F 800G 商人（见 replace_mt14_red_key_fight_with_mt12_merchant），
    省下三兽人武士战斗约 2460 HP，净省 ~1200 HP，可存活。DEF 维持 30 进入 3/4区，
    后续靠 4区爆防补回（官方 41477 策略）。
    """
    out = [s for s in steps if not (s.get("action") == "商店" and s.get("eid") == "blueShop:defense")]
    if len(out) == len(steps):
        print("WARN remove_def_shop: no blueShop:defense step found")
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--buy-red-key-12", action="store_true")
    parser.add_argument("--two-attack", action="store_true",
                        help="2攻线: 12F 红钥匙商人 + 去掉 12F 防御商店 (2 atk only)")
    parser.add_argument("--out-json", type=Path, default=OUT_JSON)
    args = parser.parse_args()
    if args.two_attack:
        raw_steps = parse_walk_md(WALK_MD)
        steps = remove_def_shop(replace_mt14_red_key_fight_with_mt12_merchant(optimize_zone2_steps(raw_steps)))
        print(f"2攻线: transformed verified scaffold to {len(steps)} steps (redKey-12 + no def shop)")
    elif args.buy_red_key_12:
        raw_steps = parse_walk_md(WALK_MD)
        steps = replace_mt14_red_key_fight_with_mt12_merchant(optimize_zone2_steps(raw_steps))
        print(f"transformed verified scaffold to {len(steps)} steps for 12F red-key branch")
    else:
        raw_steps = parse_walk_md(WALK_MD)
        steps = optimize_zone2_steps(raw_steps)
        print(f"parsed {len(raw_steps)} steps from {WALK_MD}; optimized to {len(steps)}")
    # actions breakdown
    acts = {}
    for s in steps:
        acts[s["action"]] = acts.get(s["action"], 0) + 1
    print(f"actions: {acts}")

    g = Game(read_json(SAVE1))
    g.strict_live_model = True
    g.auto_flags = {"battle": True, "item": True, "wall": True}
    try:
        run_zone1(g)
        apply_mt10_supply(g)
        run_zone2(g, steps)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"EXCEPTION: {type(e).__name__}: {e}")
    print(f"ok={not g.errors}")
    print(
        f"final={state_line(g.state)} {g.state['floor']} "
        f"x{g.state['x']}y{g.state['y']} dmg={g.state['dmg']} "
        f"door={g.state['yd']}/{g.state['bd']}/{g.state['rd']}"
    )
    if g.errors:
        for e in g.errors[:20]:
            print("ERR", e)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(
        json.dumps(
            {"ok": not g.errors, "final": g.snapshot(), "steps": g.steps,
             "errors": g.errors},
            ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"json={args.out_json} steps={len(g.steps)}")
    return 0 if not g.errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
