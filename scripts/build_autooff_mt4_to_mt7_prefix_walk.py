#!/usr/bin/env python3
"""Build an auto-OFF explicit MT4->MT7 prefix walk for strict live replay.

This is a small bridge artifact while the full 4F->50F generator is being
converted away from live auto-BFS assumptions.  It uses the shared Game model
from search_post40_guide_route.py so state transitions stay in the same code
path as the later post-40 route work.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from search_post40_guide_route import Game


ROOT = Path(__file__).resolve().parents[1]
SAVE1_SNAPSHOT = ROOT / "outputs" / "results" / "save1_current_snapshot.json"
OUT_JSON = ROOT / "outputs" / "results" / "strict20_autooff_mt4_to_mt7_prefix_walk.json"

AUTO_ON = {"battle": True, "item": True, "wall": True}


def start_snapshot() -> dict[str, Any]:
    data = json.loads(SAVE1_SNAPSHOT.read_text(encoding="utf-8-sig"))
    hero = data.setdefault("hero", {})
    flags = hero.setdefault("flags", {})
    flags["__auto__"] = dict(AUTO_ON)
    return data


def set_auto_step(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "segment": "自动设置",
        "phase": "auto-on",
        "floor": state["floor"],
        "pos": [state["x"], state["y"]],
        "action": "设置自动",
        "eid": "battle=true,item=true,wall=true",
        "auto": dict(AUTO_ON),
        "before": dict(state),
        "after": dict(state),
        "delta": "自动设置 battle=true,item=true,wall=true",
        "note": "auto ON：auto-bfs 自动拾取/战斗(0伤)/破墙",
        "inserted": True,
    }


def normalize_step(step: dict[str, Any]) -> dict[str, Any]:
    out = dict(step)
    if out.get("action") == "破墙":
        # The live replayer uses PASS handling for fakeWall side effects.
        out["action"] = "通过"
    return out


def build_game_to_mt7() -> Game:
    g = Game(start_snapshot())
    g.strict_live_model = True
    g.auto_flags = dict(AUTO_ON)
    g.set_segment("1区 auto-ON 前缀")

    # MT4 -> MT5, route to the sword room.
    g.go_to("MT4", 11, 8, "开 MT4 上方黄门")
    g.go_to("MT4", 3, 7, "击杀 MT4 绿头怪")
    g.go_to("MT4", 1, 7, "击杀 MT4 红头怪")
    g.go_to("MT4", 1, 8, "开 MT4 左下黄门")
    g.change_by_stair("MT5", 1, 11, "上 5F")

    # MT5 sword case: with auto ON, auto_sweep breaks the fakeWall + picks the
    # sword after opening the door, BUT the hero still routes through x9y11 /
    # x11y11 to reach x11y2 (the y9 wall blocks the x11 column). Keep the
    # explicit go_to (they are path waypoints, recorded as 到达 no-ops with
    # auto ON -- the resource is gone but the hero must pass through).
    g.go_to("MT5", 6, 8, "击杀 MT5 绿头怪")
    g.go_to("MT5", 7, 6, "击杀 MT5 绿头怪")
    g.go_to("MT5", 11, 7, "击杀 MT5 红头怪")
    g.go_to("MT5", 8, 9, "开 MT5 铁剑房黄门")
    g.go_to("MT5", 9, 11, "经 MT5 铁剑前暗墙（路径点）")
    g.go_to("MT5", 11, 11, "经 MT5 铁剑格（路径点）")
    g.go_to("MT5", 11, 2, "击杀 MT5 红头怪")

    # Climb to MT6. Resource go_to kept as path waypoints (reachability).
    g.go_to("MT5", 10, 1, "开 MT5 右上黄门")
    g.go_to("MT5", 8, 2, "击杀 MT5 右上绿头怪")
    for pos in [(8, 3), (9, 3), (8, 4), (9, 4)]:
        g.go_to("MT5", *pos, "经 MT5 右上黄钥匙（路径点）")
    g.fly("MT4")
    g.go_to("MT4", 8, 8, "开 MT4 红宝石房黄门")
    g.go_to("MT4", 8, 9, "击杀 MT4 初级法师")
    for pos, note in [((9, 10), "经 MT4 红血瓶（路径点）"), ((7, 10), "经 MT4 红宝石（路径点）")]:
        g.go_to("MT4", *pos, note)
    g.go_to("MT4", 4, 8, "开 MT4 左侧黄门")
    g.go_to("MT4", 4, 9, "击杀 MT4 小蝙蝠")
    for pos in [(5, 10), (5, 11)]:
        g.go_to("MT4", *pos, "经 MT4 左下黄钥匙（路径点）")
    g.go_to("MT4", 3, 10, "击杀 MT4 左下绿头怪")
    g.go_to("MT4", 3, 11, "经 MT4 左下黄钥匙（路径点）")
    g.fly("MT5")
    g.go_to("MT5", 6, 4, "击杀 MT5 小蝙蝠")
    g.go_to("MT5", 6, 2, "经 MT5 黄钥匙（路径点）")
    g.go_to("MT5", 5, 1, "开 MT5 左上黄门")
    g.go_to("MT5", 4, 1, "击杀 MT5 红头怪")
    g.go_to("MT5", 4, 4, "开 MT5 左侧黄门")
    g.go_to("MT5", 4, 6, "击杀 MT5 小蝙蝠")
    for pos in [(1, 5), (1, 6)]:
        g.go_to("MT5", *pos, "经 MT5 左侧黄钥匙（路径点）")
    g.go_to("MT5", 3, 3, "击杀 MT5 小蝙蝠")
    g.go_to("MT5", 2, 3, "开 MT5 左上黄门")
    g.change_by_stair("MT6", 1, 1, "上 6F")

    # MT6 path waypoints + doors + kills, then stop at MT7 entry.
    g.go_to("MT6", 3, 6, "击杀 MT6 红头怪")
    g.go_to("MT6", 4, 6, "击杀 MT6 初级法师")
    g.go_to("MT6", 6, 6, "经 MT6 中部黄钥匙（路径点）")
    g.go_to("MT6", 5, 4, "开 MT6 黄门")
    g.go_to("MT6", 4, 3, "击杀 MT6 红头怪")
    for pos in [(3, 1), (4, 1), (3, 2), (4, 2)]:
        g.go_to("MT6", *pos, "经 MT6 左上黄钥匙（路径点）")
    g.go_to("MT6", 7, 8, "开 MT6 右路黄门")
    g.go_to("MT6", 8, 8, "开 MT6 右路黄门")
    g.go_to("MT6", 10, 8, "开 MT6 右路黄门")
    g.go_to("MT6", 11, 9, "击杀 MT6 红头怪")
    g.change_by_stair("MT7", 11, 11, "上 7F，前 6 层 auto ON 验证终点")
    return g


def build_walk() -> dict[str, Any]:
    g = build_game_to_mt7()
    steps = [set_auto_step(g.steps[0]["before"])] + [normalize_step(step) for step in g.steps]
    for idx, step in enumerate(steps, 1):
        step["index"] = idx

    return {
        "ok": not g.errors,
        "web_verified": False,
        "verification_note": "auto-ON local prefix; live replay pending",
        "auto_settings": [{"when": "4F start", "auto": dict(AUTO_ON), "reason": "auto ON: auto-bfs pickup/battle/wall"}],
        "start": steps[0]["before"],
        "final": steps[-1]["after"],
        "steps": steps,
        "errors": g.errors,
    }


def main() -> int:
    data = build_walk()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    final = data["final"]
    print(f"ok={data['ok']}")
    print(f"json={OUT_JSON}")
    print(
        "final="
        f"{final['floor']} x{final['x']}y{final['y']} "
        f"HP={final['hp']} ATK={final['atk']} DEF={final['def']} "
        f"YK={final['yk']} BK={final['bk']} RK={final['rk']} G={final['gold']}"
    )
    print(f"steps={len(data['steps'])}")
    return 0 if data["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
