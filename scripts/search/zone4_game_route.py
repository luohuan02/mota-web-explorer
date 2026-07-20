#!/usr/bin/env python3
"""4区通用 Game 类重放（2ATK1DEF, TE late-49, auto ON, item=nopotion）。

从 zone3 2ATK1DEF 留镐压血终点 (MT41 x6y2 HP=45, YK=7, pickaxe=1,
best/checkpoints/zone3_2atk1def_preserve_pickaxe_end_save.json) 起，回放 4 区 (MT41-50)
TE late-49 路线。

复用 src/solver/game_route.py 的 guide 阶段函数（initial climb / pre-earthquake /
farm-earthquake / shield）+ TE 阶段（post_shield_no49 + late49_endgame，原为死代码，
本脚本接线启用）。按 2ATK1DEF 起点（已在 MT41 x6y2，跳过 MT40->MT41 楼梯）与
DEF=166（vs guide 218）迭代适配；适配只改通用逻辑/商店 stat 目标/资源顺序，不在
单坐标打补丁。

auto 起点为 {battle, wall} + item="nopotion"，取得神圣盾后由 Game step 动态切为
item=true。strict_live_model=True 匹配 web verifier
（target-click-only）；48F 使用3区保留的镐取得圣剑。

唯一管线：本脚本 -> outputs/results/zone4_game_route.json ->
scripts/build/gen_zone_walk_md.py -> best/zone4_2atk1def_*_walk.md ->
node scripts/live/live_zone3_mouse_replayer_cdp.js --walk <json> --load-slot 150
  --set-auto battle=true,item=nopotion,wall=true --target-click-only
"""
from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.solver.game_route import (
    Game,
    go_to_decomposed,
    read_json,
    state_line,
    collect_guide_pre_earthquake,
    farm_gold_for_earthquake,
    earthquake_and_shield,
    post_shield_no49,
    late49_endgame,
    collect_existing_items,
    cleanup_reachable_items,
    eat_minimal_potions_until,
)

DEFAULT_CHECKPOINT = ROOT / "best" / "checkpoints" / "zone3_2atk1def_preserve_pickaxe_end_save.json"
OUT_JSON = ROOT / "outputs" / "results" / "zone4_game_route.json"

# TE stage order: pre-shield (climb + earthquake + 神圣盾) -> TE prep (不打 49F, 留下楼器)
# -> TE endgame (救公主 -> 50F 小偷 -> 下楼器 49F 封印 -> 50F 封印真魔王)。
# (TE_STAGES defined after initial_climb_2atk1def below.)


class Zone4Game(Game):
    """4 区 TE 适配层。zone4 楼层事件（MT41-50 after_action / seal / thief /
    centerFly / pickaxe / snow 等）已在通用 Game 类建模；此 subclass 预留 zone4
    专用 hook，搜索代码不得依赖旧 GuideReplay 或为单条 walk 加坐标跳过补丁。"""
    pass


def initial_climb_2atk1def(g: Game) -> None:
    """2ATK1DEF 4区初始攀登 MT41->MT48（显式步骤，strict_live_model 兼容）。

    镜像 guide 22264 walk steps 001-083，适配 2ATK1DEF 起点（已在 MT41 x6y2，
    跳过 MT40->MT41 楼梯）。strict 模式不能穿关闭门寻路，故 MT41 三黄门显式开。
    药水用 collect_existing_items：2ATK1DEF 3区已拾的（MT18 x11y11、MT17 x10y2、
    MT14 x7y1）自动跳过，不重复拾取。
    """
    g.set_segment("41-48 initial climb (2ATK1DEF)")
    # MT41: 显式开 x6y7/8/9 三黄门（strict 不能穿门寻路）；途中 x6y4 半血陷阱 25->12。
    for y in (7, 8, 9):
        g.go_to("MT41", 6, y, f"41F x6y{y} 黄门")
    g.change_by_stair("MT42", 6, 11, "41F x6y11 上楼到42F")
    # 41F 半血陷阱已经结算；此后到 44F 神圣盾前只有固定魔法领域伤害。
    # guide 可从 17/18F 取缓冲，但该分支已在 3 区消耗，必须从当前存档仍在的
    # 40F 血瓶中补足，而不能假设旧资源仍存在。
    eat_minimal_potions_until(
        g,
        701,
        "41F半血后覆盖42/46/47F累计固定伤的最小可达药瓶集合",
        min_floor=1,
    )
    g.fly("MT34")
    go_to_decomposed(g, "MT34", 11, 1, "41F半血后补取34F右上蓝宝石")
    if g.state["floor"] != "MT42":
        g.fly("MT42")
    # 42F 骑士队长剧情 + 右侧钥匙（固定伤 checkBlock 由 apply_check_damage 自动记）。
    g.go_to("MT42", 5, 10, "42F 骑士队长剧情")
    cleanup_reachable_items(g, {"yellowKey"}, min_floor=41, max_steps=20)
    if g.state["floor"] != "MT42":
        g.fly("MT42")
    go_to_decomposed(g, "MT42", 1, 10, "42F 预清中心飞行左下落点守怪")
    g.go_to("MT42", 8, 5, "42F 右侧黄门")
    for pos in [(10,5),(10,4),(10,3),(10,2),(9,2),(9,1),(10,1),(11,1),(11,2)]:
        g.go_to("MT42", pos[0], pos[1], f"42F 右侧钥匙 {pos}")
    g.center_fly("42F x11y2到左下空格x1y10，避免重复穿越x10y4魔法领域")
    g.go_to("MT42", 1, 9, "42F 左下蓝药（半血后显式拾取）")
    go_to_decomposed(g, "MT42", 1, 1, "42F 左列清障到上楼口")
    g.transition("MT43", "42F 上楼")
    # 43F 直跳 45F。
    go_to_decomposed(g, "MT43", 11, 11, "43F 先取右下蓝钥匙供43F与47F两扇蓝门")
    g.fly("MT43")
    g.go_to("MT43", 3, 1, "43F 黄门")
    g.go_to("MT43", 1, 4, "43F 蓝门")
    g.go_to("MT43", 1, 8, "43F x1y8 黄门")
    g.change_by_stair("MT45", 1, 11, "43F 上楼直跳45F")
    g.change_by_stair("MT46", 11, 1, "45F 上楼")
    # 补 46F/47F 领域用血瓶（collect_existing_items 跳过 2ATK1DEF 3区已拾的）。
    g.fly("MT14")
    collect_existing_items(g, "MT14", [(9, 6)], "补 46F/47F 领域用红血瓶")
    g.fly("MT18")
    collect_existing_items(g, "MT18", [(1, 11), (11, 11)], "补 46F/47F 领域用红血瓶")
    g.fly("MT17")
    collect_existing_items(g, "MT17", [(10, 2)], "补 46F/47F 右上往返领域用蓝血瓶")
    g.fly("MT46")
    for pos in [(11, 3), (11, 5), (11, 8)]:
        g.go_to("MT46", *pos, "46F 下侧三黄门")
    g.change_by_stair("MT47", 11, 11, "46F 上楼")
    # 47F guide 资源 + 中心飞。
    g.go_to("MT47", 7, 11, "47F 左下黄门")
    g.go_to("MT47", 6, 10, "47F 左侧红宝石")
    g.go_to("MT47", 6, 10, "47F 回中心飞点")
    g.center_fly("47F 左下到右上")
    g.go_to("MT47", 7, 1, "47F 右侧黄门")
    for pos in [(11, 1), (11, 2), (11, 3)]:
        g.go_to("MT47", *pos, f"47F 右侧资源 {pos}")
    go_to_decomposed(g, "MT47", 3, 1, "47F 蓝门")
    g.change_by_stair("MT48", 1, 1, "47F 上楼到48")
    # 3区已保留15F镐；首次到48F落点为x11y10，正好相邻破x10y10墙取圣剑。
    g.use_pickaxe("MT48", 10, 10, "48F 使用3区保留镐破墙拿圣剑")
    g.go_to("MT48", 8, 10, "48F 圣剑")


def earthquake_and_shield_2atk1def(g: Game) -> None:
    """走通用地震卷轴与神圣盾阶段。

    起点 RK=0 是正确状态：通用阶段先在 47F 买地震卷轴，再震开 37F
    镐墙并取得其中的红钥匙，之后才开 45F 红门。42F 地面红钥匙继续
    保留给 TE 公主路线；34F 中心事件已在 3 区使用，不得重复触发。
    """
    earthquake_and_shield(g)


TE_STAGES = [
    ("prefix48", initial_climb_2atk1def, "41-48 initial climb (2ATK1DEF)"),
    ("pre_earthquake", collect_guide_pre_earthquake, "pre-earthquake resource loop"),
    ("farm_earthquake", farm_gold_for_earthquake, "gold for earthquake"),
    ("shield", earthquake_and_shield_2atk1def, "earthquake and sacred shield"),
    ("post_shield_no49_te", post_shield_no49, "圣盾后TE准备(不打49F,留downFly)"),
    ("late49_endgame_te", late49_endgame, "TE晚49:救公主->50F小偷->49F封印->50F封印真魔王"),
]


def run_zone4(g: Game, stop_after: str | None = None) -> None:
    for name, fn, label in TE_STAGES:
        g.set_segment(label)
        before = g.snapshot()
        before_steps = len(g.steps)
        try:
            fn(g)
        except Exception as e:  # RouteError or other -- record and stop
            print(f"STAGE {name} EXCEPTION: {type(e).__name__}: {e}")
            if not g.errors:
                g.fail(f"stage {name} 异常: {e}")
            break
        after = g.snapshot()
        g.stage_summaries.append(
            {
                "name": name,
                "label": label,
                "before": before,
                "after": after,
                "delta_dmg": after["dmg"] - before["dmg"],
                "delta_steps": len(g.steps) - before_steps,
                "stock_score": after["hp"] + after["yk"] * 50 + after["bk"] * 200 + after["gold"] * 0.5,
            }
        )
        print(
            f"[stage] {name}: {state_line(after)} {after['floor']} "
            f"x{after['x']}y{after['y']} dmg={after['dmg']} "
            f"door={after['yd']}/{after['bd']}/{after['rd']} steps={len(g.steps)}"
        )
        if stop_after == name:
            break


def _arg(name: str) -> str | None:
    for i, a in enumerate(sys.argv):
        if a == name and i + 1 < len(sys.argv):
            return sys.argv[i + 1]
        if a.startswith(name + "="):
            return a.split("=", 1)[1]
    return None


def main() -> int:
    checkpoint = Path(_arg("--from-checkpoint") or DEFAULT_CHECKPOINT)
    stop_after = _arg("--stop-after")
    out_json = Path(_arg("--out-json") or OUT_JSON)
    out_pickle_arg = _arg("--out-pickle")
    g = Zone4Game(read_json(checkpoint))
    g.strict_live_model = True
    g.auto_flags = {"battle": True, "item": "nopotion", "wall": True}
    g.flags["__auto__"] = dict(g.auto_flags)
    initial_auto = dict(g.auto_flags)
    g.flags["earlyStatGroupBudget"] = int(_arg("--early-stat-groups") or 0)
    print(f"from-checkpoint={checkpoint}")
    print(f"start={state_line(g.state)} {g.state['floor']} x{g.state['x']}y{g.state['y']} stop_after={stop_after}")
    run_zone4(g, stop_after)
    print(f"ok={not g.errors}")
    print(
        f"final={state_line(g.state)} {g.state['floor']} "
        f"x{g.state['x']}y{g.state['y']} dmg={g.state['dmg']} "
        f"door={g.state['yd']}/{g.state['bd']}/{g.state['rd']}"
    )
    if g.errors:
        for e in g.errors[:20]:
            print("ERR", e)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(
        json.dumps(
            {
                "ok": not g.errors,
                "auto": initial_auto,
                "auto_final": g.auto_flags,
                "strict_live_model": g.strict_live_model,
                "final": g.snapshot(),
                "steps": g.steps,
                "stage_summaries": g.stage_summaries,
                "errors": g.errors,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"json={out_json} steps={len(g.steps)}")
    if out_pickle_arg:
        out_pickle = Path(out_pickle_arg)
        out_pickle.parent.mkdir(parents=True, exist_ok=True)
        out_pickle.write_bytes(pickle.dumps(g, protocol=pickle.HIGHEST_PROTOCOL))
        print(f"pickle={out_pickle}")
    return 0 if not g.errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
