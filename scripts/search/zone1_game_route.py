#!/usr/bin/env python3
"""1区通用 Game 类重放（auto ON，strict live model）。

用 src/solver/game_route.py 的通用 Game 类（含 auto_sweep）
替代 fixed_shield_strategy + replay_user_post9_route 的手写 Replay，从 save1
快照（MT4）跑到 10F Boss，auto 全开，生成 walk 供 web 验证。

坐标种子来自 fixed_shield_strategy.ROUTE（4F-9F）与 replay_user_post9_route.ROUTE
（9F-10F Boss）。go_to 内部 auto_sweep 会自动处理可达零伤怪/道具/暗墙，因此离线
推导与实机 auto ON 行为一致。
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from src.solver.game_route import Game, read_json, state_line
from scripts.baseline import fixed_shield_strategy as fixed
from scripts.baseline import replay_user_post9_route as guide10
from src.solver.full_search import FLYBACK_ENTRANCES

SAVE1 = ROOT / "outputs" / "results" / "save1_current_snapshot.json"
OUT_JSON = ROOT / "outputs" / "results" / "zone1_game_route.json"
OUT_MD = ROOT / "outputs" / "reports" / "zone1_game_route.md"


def flyback(g: Game, fid: str, name: str) -> None:
    """飞到 fid（用 fly_points landing，与实机 fly 一致）。fly 不触发 auto_sweep
    （core.plugin.auto 只在 go_to/开 门 等行动后触发，不含 fly）。"""
    if g.state["floor"] == fid:
        return
    g.fly(fid)


import re

WALK_MD = ROOT / "best" / "current_best_boss_walk.md"


def parse_current_best_walk() -> list[tuple[str, int, int, str, str]]:
    """解析 best/current_best_boss_walk.md 的 Phase1 + Post9 Detailed Steps。

    每行 `- MTx xNyN (open|kill|take|pass) eid` 或 `- MTx xNyN trigger boss event`。
    这是 live_zone3_mouse_replayer_cdp.js web 复验用的同一份 walk；auto ON 下 auto_sweep 会
    自动拾取/清理可达资源，take/pass step 在实机会被 canSkipMissingTarget 跳过。
    """
    text = WALK_MD.read_text(encoding="utf-8")
    steps: list[tuple[str, int, int, str, str]] = []
    for line in text.splitlines():
        m = re.match(r"- (MT\d+) x(\d+)y(\d+) (open|kill|take|pass) ([A-Za-z0-9_]+)", line)
        if m:
            steps.append((m.group(1), int(m.group(2)), int(m.group(3)), m.group(4), m.group(5)))
            continue
        m = re.match(r"- (MT\d+) x(\d+)y(\d+) trigger boss event", line)
        if m:
            steps.append((m.group(1), int(m.group(2)), int(m.group(3)), "trigger", "bossEvent"))
    return steps


def run_zone1(g: Game) -> None:
    g.set_segment("1区 current_best detailed (auto ON)")
    boss_pos = set(guide10.SPAWNED_BOSS.keys()) | {(6, 1)}
    for fid, x, y, action, eid in parse_current_best_walk():
        if g.state["floor"] != fid:
            flyback(g, fid, f"{action} {eid}")
        if action == "trigger" and eid == "bossEvent":
            # 10F boss: go_to 触发点，生成 SPAWNED_BOSS（不击杀，由后续 kill step 逐个 apply_block）。
            g.go_to(fid, x, y, "10F boss 触发")
            # 改 record action 为 "事件"（boss 触发），避免被 convert 当 "到达" 过滤
            if g.steps and g.steps[-1].get("action") == "到达":
                g.steps[-1]["action"] = "事件"
                g.steps[-1]["eid"] = "bossEvent"
            for sp_pos, sp_eid in guide10.SPAWNED_BOSS.items():
                g.set_block("MT10", sp_pos, "enemy", sp_eid)
            # web 点击 trigger 后 auto-battle 一步清完所有 spawned + captain
            # （replayer clearMt10BossDyn）。静默清完，刷新 trigger step 的 after + note，
            # 不再生成逐个 kill step（否则 web 一次清完，Game 多步失配）。
            cleared = g.clear_mt10_boss_dyn()
            if cleared and g.steps:
                g.refresh_last_step(
                    g.steps[-1]["before"],
                    "clearMt10BossDyn 动态清: " + ", ".join(cleared),
                )
            continue
        if fid == "MT10" and action == "kill" and (x, y) in boss_pos:
            # boss 区域 spawned/captain 有伤，go_to strict_click 寻路不通，直接 apply_block。
            block = g.block_at("MT10", (x, y))
            if block and block.kind == "enemy":
                before = g.snapshot()
                g.state["x"], g.state["y"] = x, y
                g.apply_block("MT10", (x, y), block, f"10F 打 {block.eid}")
            continue
        if action == "pass" and eid in ("upFloor", "downFloor"):
            # 走到楼梯自动上/下楼（detailed steps 的 pass upFloor/downFloor 含换层）。
            g.go_to(fid, x, y, f"{action} {eid}")
            delta = 1 if eid == "upFloor" else -1
            next_fid = f"MT{int(fid[2:]) + delta}"
            g.transition(next_fid, f"{fid} -> {next_fid}")
            continue
        # auto ON 下 auto_sweep 可能已拾取道具/清零伤怪，目标格消失则 skip（不移动 hero），
        # 与 live_zone1 canSkipMissingTarget 一致，避免 hero 位置偏移。
        if action in ("take", "kill") and g.block_at(fid, (x, y)) is None:
            continue
        g.go_to(fid, x, y, f"{action} {eid}")


def replay_mt10_boss(g: Game, entry: dict) -> None:
    """10F boss: 走到 (6,5) 触发生成 SPAWNED_BOSS，再逐个击杀 spawned + captain。

    boss 区域 spawned 怪有伤，go_to strict_click 寻路会避开，因此触发后直接
    apply_block 逐个击杀（hero 站到目标格），与 post9 replay() 的顺序一致。
    """
    for x, y in entry["points"]:
        pos = (x, y)
        if pos == (6, 5):
            g.go_to("MT10", 6, 5, "10F boss 触发点")
            for sp_pos, sp_eid in guide10.SPAWNED_BOSS.items():
                g.set_block("MT10", sp_pos, "enemy", sp_eid)
            continue
        block = g.block_at("MT10", pos)
        if block and block.kind == "enemy":
            before = g.snapshot()
            g.state["x"], g.state["y"] = pos
            g.apply_block("MT10", pos, block, f"10F 打 {block.eid}")
        else:
            g.go_to("MT10", x, y, entry["name"])


def main() -> int:
    g = Game(read_json(SAVE1))
    g.strict_live_model = True
    g.auto_flags = {"battle": True, "item": True, "wall": True}
    try:
        run_zone1(g)
    except Exception as e:
        print(f"EXCEPTION: {type(e).__name__}: {e}")
    print(f"ok={not g.errors}")
    print(
        f"final={state_line(g.state)} {g.state['floor']} "
        f"x{g.state['x']}y{g.state['y']} dmg={g.state['dmg']} "
        f"door={g.state['yd']}/{g.state['bd']}/{g.state['rd']}"
    )
    if g.errors:
        for e in g.errors[:15]:
            print("ERR", e)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(
        json.dumps(
            {
                "ok": not g.errors,
                "final": g.snapshot(),
                "steps": g.steps,
                "errors": g.errors,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"json={OUT_JSON}")
    return 0 if not g.errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
