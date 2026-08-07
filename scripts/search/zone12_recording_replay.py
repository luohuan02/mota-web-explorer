#!/usr/bin/env python3
"""2攻线录像复现：用通用 Game 类按录像 route 逐 action 重放 MT4-20（1/2区），
对齐 ground-truth stat log，输出 walk JSON 供 web 验证。

起点 SAVE1 = 录像 stat i=55 状态（MT4，含 MT1-3 固定前缀 + 纯净版 reset）。
录像 choices（商店/商人）按 hero 相邻 NPC 识别并映射到通用 buy_shop/talk_trader。
楼梯换层（move:x:y 目标在楼梯后面，hero 寻路中途踩楼梯换层）用 change_by_stair
显式处理（Game 类楼梯是 target-only，不会路由穿过）。

stat log 的 stats/floor 是 action 之后的状态（可靠），position 时序不稳（不验证）。
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

from src.solver.game_route import Game, read_json, state_line, floor_no, go_to_decomposed

TMP = Path(os.environ.get("CLAUDE_JOB_DIR", "C:/Users/peiyan.liang/.claude/jobs/79814e6b")) / "tmp"
ROUTE_JSON = TMP / "decoded_route_1134.json"
STATLOG_JSON = TMP / "replay_statlog.json"
SAVE1 = ROOT / "outputs" / "results" / "save1_current_snapshot.json"
OUT_JSON = ROOT / "outputs" / "results" / "zone12_recording_replay.json"
OUT_REPORT = TMP / "zone12_replay_report.txt"

STOP_FLOOR = "MT21"  # zone3 start: stop at end of zone2 (MT20 last exit)


def main() -> int:
    route = json.loads(ROUTE_JSON.read_text(encoding="utf-8"))
    statlog = json.loads(STATLOG_JSON.read_text(encoding="utf-8"))

    # route -> stat index (choices don't advance stat)
    route_stat: list[int | None] = [None] * len(route)
    si = 0
    for ri, a in enumerate(route):
        if not (isinstance(a, str) and a.startswith("choices")):
            route_stat[ri] = si
            si += 1
    assert si == len(statlog), f"stat count mismatch {si} vs {len(statlog)}"

    # SAVE1 == stat i=55 (MT4 arrival). Start applying from the route action
    # that produces stat 56 (the first action after the MT1-3 prefix).
    start_ri = next(ri for ri, s in enumerate(route_stat) if s == 55) + 1

    g = Game(read_json(SAVE1))
    g.strict_live_model = True
    # 录像回放 auto OFF：道具仅在 hero 踩到时拾取（path/step），不做 BFS auto_sweep。
    # 录像 sword1@MT5(11,11) 在 ri=79 move:11:3 路径踩到时才拾取（非 ri=77 相邻时
    # auto 预拾），证明回放 auto OFF。Game 类 auto_flags 全关以匹配。
    g.auto_flags = {"battle": False, "item": False, "wall": False}
    g.set_segment("2攻线录像复现 zone1/2 (auto OFF)")

    mismatches: list[str] = []
    trace: list[str] = []
    trace_fh = (TMP / "zone12_trace.txt").open("w", encoding="utf-8")

    def trace_step(ri: int, a: str) -> None:
        s = g.state
        line = f"ri={ri} {a} -> {s['floor']} ({s['x']},{s['y']}) hp={s['hp']} atk={s['atk']} yk={s['yk']} bk={s['bk']} g={s['gold']} facing={facing}"
        trace.append(line)
        trace_fh.write(line + "\n")
        trace_fh.flush()

    def stats(g: Game) -> dict:
        s = g.state
        return {"hp": s["hp"], "atk": s["atk"], "def": s["def"],
                "yk": s["yk"], "bk": s["bk"], "rk": s["rk"], "g": s["gold"]}

    def verify(ri: int, stat_idx: int | None, label: str) -> None:
        if stat_idx is None or stat_idx >= len(statlog):
            return
        if g.state["floor"] == STOP_FLOOR:
            return
        exp = statlog[stat_idx]
        got = stats(g)
        fields = ["hp", "atk", "def", "yk", "bk", "rk", "g"]
        diffs = {f: (got[f], exp[f]) for f in fields if got[f] != exp[f]}
        if diffs or (g.state["floor"] != exp["f"] and g.state["floor"] != STOP_FLOOR):
            mismatches.append(
                f"ri={ri} stat={stat_idx} [{label}] floor got={g.state['floor']} exp={exp['f']} "
                f"diffs={diffs} pos=({g.state['x']},{g.state['y']})"
            )

    def try_move(g: Game, fid: str, tx: int, ty: int, note: str) -> bool:
        """go_to_decomposed; return False (no-op) if blocked (wall/unfightable).

        录像的 step(up/down/left/right) 可能撞墙/撞不可杀怪 = 游戏 no-op（hero 转身
        不移动，stat 无变化）。move:x:y 一般是有效目的地。go_to_decomposed 对不可达
        目标会 fail，此时当 no-op 跳过，由 stat 验证把关。
        """
        old_errors = len(g.errors)
        try:
            go_to_decomposed(g, fid, tx, ty, note)
            return True
        except Exception:
            del g.errors[old_errors:]
            return False

    def find_stair(g: Game, going_up: bool) -> tuple[int, int] | None:
        eid = "upFloor" if going_up else "downFloor"
        src = g.state["floor"]
        for pos, blk in g.floors[src].blocks.items():
            if blk.eid == eid:
                return pos
        return None

    def adjacent_block(g: Game, eid: str | None = None, kind: str | None = None):
        src = g.state["floor"]
        hx, hy = g.state["x"], g.state["y"]
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            pos = (hx + dx, hy + dy)
            blk = g.block_at(src, pos)
            if not blk:
                continue
            if eid and blk.eid == eid:
                return pos
            if kind and blk.kind == kind:
                return pos
        return None

    DX = {"up": 0, "down": 0, "left": -1, "right": 1}
    DY = {"up": -1, "down": 1, "left": 0, "right": 0}

    def dir_of(a: tuple[int, int], b: tuple[int, int]) -> str | None:
        if b[0] > a[0]:
            return "right"
        if b[0] < a[0]:
            return "left"
        if b[1] > a[1]:
            return "down"
        if b[1] < a[1]:
            return "up"
        return None

    def last_move_dir(g: Game) -> str | None:
        """facing = direction of the hero's last actual position change."""
        for s in reversed(g.steps):
            b = s.get("before"); af = s.get("after")
            if b and af and (b.get("x") != af.get("x") or b.get("y") != af.get("y")):
                return dir_of((b["x"], b["y"]), (af["x"], af["y"]))
        return None

    # facing tracks the hero's last move direction (arrow-key steps are
    # turn-then-move: a step moves only if the hero already faces that way).
    # ri=59 "up" moved => facing was "up" after the MT3->MT4 stair landing.
    facing = "up"

    ri = start_ri
    last_floor = g.state["floor"]
    while ri < len(route):
        a = route[ri]
        if not isinstance(a, str):
            ri += 1
            continue
        this_stat = route_stat[ri]

        # ---- choices: shop or trader ----
        if a.startswith("choices"):
            n = int(a.split(":")[1]) if ":" in a else 0
            shop_pos = adjacent_block(g, eid="blueShop")
            if shop_pos is not None:
                # shop menu: 0=hp, 1=atk, 2=def, 3=leave
                if n == 1:
                    g.buy_shop("atk", 1, shop_pos=shop_pos)
                elif n == 2:
                    g.buy_shop("def", 1, shop_pos=shop_pos)
                elif n == 0:
                    g.buy_shop("hp", 1, shop_pos=shop_pos)
                # n == 3 leave: no-op
            else:
                tpos = adjacent_block(g, kind="npc")
                if tpos is not None:
                    g.talk_trader(g.state["floor"], tpos[0], tpos[1], "录像 trader")
                else:
                    mismatches.append(f"ri={ri} unhandled choices {a} at {g.state['floor']} ({g.state['x']},{g.state['y']})")
            ri += 1
            continue

        if a.startswith("turn") or a.startswith("help"):
            ri += 1
            continue

        # ---- fly ----
        if a.startswith("fly"):
            target_floor = a.split(":")[1]
            try:
                g.fly(target_floor)
            except Exception:
                mismatches.append(f"ri={ri} fly {target_floor} failed at {g.state['floor']}({g.state['x']},{g.state['y']}) hp={g.state['hp']} yk={g.state['yk']} g={g.state['gold']}")
            verify(ri, this_stat, f"fly {target_floor}")
            trace_step(ri, a)
            ri += 1
            continue

        # ---- move / step ----
        # Stair transition check first (applies to both move:x:y and steps):
        # the recording's floor change means the hero reached a stair.
        exp_stat = statlog[this_stat] if this_stat is not None else None
        is_stair = exp_stat and exp_stat["f"] != g.state["floor"] and exp_stat["f"] != STOP_FLOOR
        if is_stair:
            going_up = floor_no(exp_stat["f"]) > floor_no(g.state["floor"])
            stair = find_stair(g, going_up)
            if stair:
                moved = try_move(g, g.state["floor"], stair[0], stair[1],
                                 f"stair {g.state['floor']}->{exp_stat['f']}")
                if moved:
                    facing = last_move_dir(g) or facing
                    g.transition(exp_stat["f"], f"{g.state['floor']}->{exp_stat['f']}")
                else:
                    mismatches.append(f"ri={ri} no path to stair {g.state['floor']}({g.state['x']},{g.state['y']})->{stair}->{exp_stat['f']}")
            else:
                mismatches.append(f"ri={ri} no stair {g.state['floor']}->{exp_stat['f']}")
            verify(ri, this_stat, f"stair->{exp_stat['f']}")
            trace_step(ri, a)
        elif a.startswith("move:"):
            parts = a.split(":")
            tx, ty = int(parts[1]), int(parts[2])
            try_move(g, g.state["floor"], tx, ty, f"move {a}")
            facing = last_move_dir(g) or facing
            verify(ri, this_stat, f"move {a}")
            trace_step(ri, a)
        elif a in ("up", "down", "left", "right"):
            # arrow-key step: turn-then-move. Moves only if already facing `a`;
            # otherwise it's a turn (no-op). Either way, facing becomes `a`.
            if facing == a:
                hx, hy = g.state["x"], g.state["y"]
                try_move(g, g.state["floor"], hx + DX[a], hy + DY[a], f"step {a}")
            # else: turn (no-op)
            facing = a
            verify(ri, this_stat, f"step {a}")
            trace_step(ri, a)

        # stop at zone3 start
        if g.state["floor"] == STOP_FLOOR:
            break
        ri += 1

    # final summary
    exp_final = statlog[989]  # MT20 last exit (zone2 end)
    print(f"ok={not g.errors}  mismatches={len(mismatches)}  errors={len(g.errors)}")
    print(f"final={state_line(g.state)} {g.state['floor']} "
          f"x{g.state['x']}y{g.state['y']} dmg={g.state['dmg']} "
          f"door={g.state['yd']}/{g.state['bd']}/{g.state['rd']} times1={g.state['times1']}")
    print(f"exp  HP={exp_final['hp']} ATK={exp_final['atk']} DEF={exp_final['def']} "
          f"YK={exp_final['yk']} BK={exp_final['bk']} RK={exp_final['rk']} G={exp_final['g']} "
          f"@{exp_final['f']}")
    if mismatches:
        print(f"\n--- first 40 mismatches ---")
        for m in mismatches[:40]:
            print(m)
    if g.errors:
        print(f"\n--- first 20 errors ---")
        for e in g.errors[:20]:
            print("ERR", e)

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(
        json.dumps({"ok": not g.errors and not mismatches, "final": g.snapshot(),
                    "steps": g.steps, "errors": g.errors},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    report = [f"ok={not g.errors} mismatches={len(mismatches)} errors={len(g.errors)}",
              f"final={state_line(g.state)} {g.state['floor']}"]
    report += mismatches
    report += ["--- errors ---"] + [str(e) for e in g.errors]
    OUT_REPORT.write_text("\n".join(report), encoding="utf-8")
    (TMP / "zone12_trace.txt").write_text("\n".join(trace), encoding="utf-8")
    print(f"\njson={OUT_JSON}  report={OUT_REPORT}  steps={len(g.steps)}")
    return 0 if not g.errors and not mismatches else 1


if __name__ == "__main__":
    raise SystemExit(main())
