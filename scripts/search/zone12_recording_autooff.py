#!/usr/bin/env python3
"""Recording-driven Game reproduction (auto OFF, exact statlog positions).

The recording is auto OFF (explicit step-by-step). auto ON diverges because
auto_sweep never enters side pockets the recording steps into explicitly
(e.g. MT5 yellow keys at (8,3),(9,3),(8,4),(9,4)). So we reproduce with
auto OFF, replaying the hero's exact footprints: for each statlog entry i,
go_to the hero's next position (statlog[i+1] pos). Arrow steps become
one-tile go_to (no facing model needed); move:x:y become multi-tile
go_to_decomposed (opens doors en route, matching live automaticRoute).

Floor changes: adjacent (±1) -> change_by_stair via the floor's stair block;
non-adjacent -> fly.
"""
from __future__ import annotations

import json
import os
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from src.solver.game_route import Game, read_json, state_line, RouteError, floor_no, go_to_decomposed

STATLOG_PATH = Path(r"C:/Users/peiyan.liang/.claude/jobs/79814e6b/tmp/replay_statlog.json")
SAVE1 = ROOT / "outputs" / "results" / "save1_current_snapshot.json"
OUT_JSON = ROOT / "outputs" / "results" / "zone12_recording_autooff.json"
OUT_TXT = Path(r"C:/Users/peiyan.liang/.claude/jobs/79814e6b/tmp/zone12_autooff_report.txt")


def load_statlog():
    with open(STATLOG_PATH, encoding="utf-8") as f:
        s = json.load(f)
    return s if isinstance(s, list) else s.get("statlog", s)


def find_stair(g, from_fid, to_fid):
    going_up = floor_no(to_fid) > floor_no(from_fid)
    want = "upFloor" if going_up else "downFloor"
    f = g.floors[from_fid]
    cands = [pos for pos, blk in f.blocks.items() if blk.eid == want]
    if not cands:
        return None
    if len(cands) == 1:
        return cands[0]
    hx, hy = g.state["x"], g.state["y"]
    return min(cands, key=lambda p: abs(p[0]-hx) + abs(p[1]-hy))


def main(stop_floor="MT11"):
    statlog = load_statlog()
    mt4 = next(i for i, s in enumerate(statlog) if s["f"] == "MT4")

    g = Game(read_json(SAVE1))
    g.strict_live_model = True
    g.auto_flags = {"battle": False, "item": False, "wall": False}  # auto OFF

    buf = []
    def log(*a):
        buf.append(" ".join(str(x) for x in a))

    log(f"start: {state_line(g.state)} {g.state['floor']} x{g.state['x']}y{g.state['y']}")

    # recording floor-transition reference
    rec_transitions = []
    prev = None
    for s in statlog:
        if s["f"] != prev:
            rec_transitions.append(s)
            prev = s["f"]

    errors = 0
    # iterate statlog positions from mt4; go_to next position
    i = mt4
    # snap Game hero to recording start pos (in case SAVE1 differs)
    g.state["x"], g.state["y"] = statlog[mt4]["x"], statlog[mt4]["y"]
    while i + 1 < len(statlog):
        cur = statlog[i]
        nxt = statlog[i + 1]
        if g.state["floor"] == stop_floor and nxt["f"] != stop_floor:
            break
        if nxt["f"] != cur["f"]:
            # floor transition
            if abs(floor_no(nxt["f"]) - floor_no(cur["f"])) == 1:
                stair = find_stair(g, cur["f"], nxt["f"])
                if stair:
                    try:
                        go_to_decomposed(g, cur["f"], stair[0], stair[1], f"stair {cur['f']}->{nxt['f']}")
                        g.transition(nxt["f"], f"stair {cur['f']}->{nxt['f']}")
                    except RouteError as ex:
                        log(f"i={i} stair {cur['f']}->{nxt['f']} RouteError: {ex}")
                        errors += 1
                else:
                    log(f"i={i} no stair {cur['f']}->{nxt['f']}")
                    errors += 1
            else:
                try:
                    g.fly(nxt["f"])
                except RouteError as ex:
                    log(f"i={i} fly {nxt['f']} RouteError: {ex}")
                    errors += 1
        else:
            # same floor: go_to next position
            try:
                go_to_decomposed(g, cur["f"], nxt["x"], nxt["y"], f"step {cur['a']!r}")
            except RouteError as ex:
                log(f"i={i} {cur['a']!r} -> ({nxt['x']},{nxt['y']}) RouteError: {ex}")
                errors += 1
                if errors > 40:
                    log("too many errors")
                    break
        i += 1

    log(f"final: {state_line(g.state)} {g.state['floor']} x{g.state['x']}y{g.state['y']} errors={errors}")

    # compare floor transitions
    log("\n=== floor transition comparison (game vs recording) ===")
    game_t = []
    prev = None
    for st in g.steps:
        aft = st.get("after") or {}
        if aft.get("floor") and aft["floor"] != prev:
            game_t.append(aft)
            prev = aft["floor"]
    n = min(len(game_t), len(rec_transitions))
    match = 0
    for k in range(n):
        gm = game_t[k]
        rc = rec_transitions[k]
        gs = f"hp={gm.get('hp')} atk={gm.get('atk')} def={gm.get('def')} yk={gm.get('yk')} bk={gm.get('bk')} rk={gm.get('rk')} g={gm.get('gold', gm.get('g'))}"
        rs = f"hp={rc['hp']} atk={rc['atk']} def={rc['def']} yk={rc['yk']} bk={rc['bk']} rk={rc['rk']} g={rc['g']}"
        ok = (gs == rs)
        if ok:
            match += 1
        log(f"  {k} {gm.get('floor')} vs {rc['f']} {'OK' if ok else 'DIFF'}")
        if not ok:
            log(f"    game: {gs}")
            log(f"    rec : {rs}")
    log(f"matched {match}/{n}")

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps({"final": g.snapshot(), "steps": g.steps, "errors": g.errors}, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_TXT.write_text("\n".join(buf), encoding="utf-8")
    print(f"matched {match}/{n}; errors={errors}; json={OUT_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
