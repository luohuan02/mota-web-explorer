#!/usr/bin/env python3
"""Recording-driven Game reproduction (auto ON) for zones 1-2.

Drives the Game class with the recording's move:x:y + fly + choices targets
(auto all-on for zones 1-2), skipping arrow steps/turn/help (auto_sweep
subsumes single-tile pickups). Compares floor-transition stats vs the
recording statlog. Stair transitions (non-fly floor changes) are routed via
the floor's upFloor/downFloor block.

This replaces the broken raw-action replay (zone12_recording_replay.py),
which tried to replay every arrow step and got stuck on stairs.
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

from src.solver.game_route import Game, read_json, state_line, RouteError, floor_no, go_to_decomposed

ROUTE = Path(r"C:/Users/peiyan.liang/.claude/jobs/79814e6b/tmp/decoded_route_1134.json")
STATLOG_PATH = Path(r"C:/Users/peiyan.liang/.claude/jobs/79814e6b/tmp/replay_statlog.json")
SAVE1 = ROOT / "outputs" / "results" / "save1_current_snapshot.json"
OUT_JSON = ROOT / "outputs" / "results" / "zone12_recording_driven.json"
OUT_TXT = Path(r"C:/Users/peiyan.liang/.claude/jobs/79814e6b/tmp/zone12_driven_report.txt")

# choice route-idx -> (kind, ...) mapping derived from align_context.txt
# zone 1 (MT4-10) has NO choices. zone 2 choices:
CHOICE_MAP = {
    459: ("shop_atk", "MT12", 2),   # 2 atk purchases (+8 atk, -60G)
    460: ("shop_atk", "MT12", 0),   # already counted (same session) - skip
    461: ("shop_atk", "MT12", 0),   # same session - skip
    471: ("trader", "MT7", 6, 1),   # 5YK for 50G (MT7 trader x6y1)
    498: ("trader", "MT15", 10, 11),  # 1BK for 200G (MT15 trader)
    574: ("trader", "MT6", 8, 4),   # 1BK for 50G (MT6 trader x8y4)
    965: ("trader", "MT12", 1, 1),  # 1RK for 800G (MT12 trader)
}


def load_route():
    with open(ROUTE, encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else data.get("route", data)


def load_statlog():
    with open(STATLOG_PATH, encoding="utf-8") as f:
        s = json.load(f)
    return s if isinstance(s, list) else s.get("statlog", s)


def find_stair(g: Game, from_fid: str, to_fid: str):
    """Find the upFloor/downFloor block on from_fid leading toward to_fid."""
    going_up = floor_no(to_fid) > floor_no(from_fid)
    want = "upFloor" if going_up else "downFloor"
    f = g.floors[from_fid]
    cands = [pos for pos, blk in f.blocks.items() if blk.eid == want]
    if not cands:
        return None
    if len(cands) == 1:
        return cands[0]
    # multiple: pick closest to current hero
    hx, hy = g.state["x"], g.state["y"]
    return min(cands, key=lambda p: abs(p[0]-hx) + abs(p[1]-hy))


def stats_of(g: Game):
    s = g.state
    return {"f": s["floor"], "x": s["x"], "y": s["y"], "hp": s["hp"], "atk": s["atk"],
            "def": s["def"], "yk": s["yk"], "bk": s["bk"], "rk": s["rk"], "g": s["gold"]}


def main(stop_floor: str = "MT11") -> int:
    route = load_route()
    statlog = load_statlog()

    # Find MT4 entry route idx (first statlog MT4, route idx where that move is)
    mt4_sl = next(i for i, s in enumerate(statlog) if s["f"] == "MT4")
    # align: find route idx whose action == statlog[mt4_sl]['a'] at the right position
    # simple: scan route for the action, counting
    sl_ptr = 0
    route_start = None
    target_a = statlog[mt4_sl]["a"]
    count_seen = 0
    # we want the mt4_sl-th statlog entry; align by walking
    sl_idx_to_ri = {}
    from collections import defaultdict
    sl_by_a = defaultdict(list)
    for i, s in enumerate(statlog):
        sl_by_a[s["a"]].append(i)
    ptr = defaultdict(int)
    for ri, e in enumerate(route):
        if isinstance(e, str) and (e.startswith("move:") or e in ("up","down","left","right") or e.startswith("fly:")):
            lst = sl_by_a.get(e, [])
            p = ptr[e]
            if p < len(lst):
                sl_idx_to_ri[lst[p]] = ri
                ptr[e] = p + 1
    route_start = sl_idx_to_ri.get(mt4_sl)
    print(f"MT4 entry statlog idx {mt4_sl} -> route idx {route_start} action {statlog[mt4_sl]['a']!r}")

    g = Game(read_json(SAVE1))
    g.strict_live_model = True
    g.auto_flags = {"battle": True, "item": True, "wall": True}

    buf = []
    def log(*a):
        buf.append(" ".join(str(x) for x in a))
        print(*a)

    log(f"start: {state_line(g.state)} {g.state['floor']} x{g.state['x']}y{g.state['y']}")

    # Build statlog floor-transition reference (first state per floor visit)
    rec_floor_states = []  # list of (floor, state) in visit order
    prev = None
    for s in statlog:
        if s["f"] != prev:
            rec_floor_states.append(s)
            prev = s["f"]

    # Walk route from route_start, feed to Game
    rec_ptr = mt4_sl  # current statlog pointer (for floor-change detection)
    mismatches = []
    last_rec_floor = statlog[mt4_sl]["f"]

    def check_floor_transition(ri):
        """If recording floor changed since last check, record expected vs game."""
        nonlocal last_rec_floor
        # find current recording floor at this route idx via alignment
        # use sl_idx_to_ri reverse: largest sl idx with ri <= current
        # simpler: track via statlog pointer
        pass

    # Simpler: after each Game action, find the recording state at the corresponding
    # statlog entry and compare. We align route->statlog on the fly.
    sl_ri = sl_idx_to_ri  # statlog idx -> route idx
    ri_to_sl = {v: k for k, v in sl_ri.items()}

    errors = 0
    for ri in range(route_start, len(route)):
        e = route[ri]
        if g.state["floor"] == stop_floor and isinstance(e, str) and e.startswith("fly:"):
            # arrived at stop floor boundary roughly; break after processing stop floor entry
            pass
        if not isinstance(e, str):
            continue
        try:
            if e.startswith("move:"):
                parts = e.split(":")
                x, y = int(parts[1]), int(parts[2])
                go_to_decomposed(g, g.state["floor"], x, y, e)
            elif e.startswith("fly:"):
                fid = e.split(":", 1)[1]
                g.fly(fid)
            elif e.startswith("choices:"):
                cm = CHOICE_MAP.get(ri)
                if cm is None:
                    pass  # MT1-3 prefix choices or end-game; skip
                elif cm[0] == "shop_atk":
                    _, fid, count = cm
                    if count > 0:
                        # ensure on fid
                        if g.state["floor"] != fid:
                            g.fly(fid)
                        # find shop position on fid (blueShop block)
                        f = g.floors[fid]
                        shop = next((pos for pos, blk in f.blocks.items() if blk.eid == "blueShop"), None)
                        g.move_adjacent(fid, shop[0], shop[1], "approach shop") if shop else None
                        g.buy_shop("atk", count, shop)
                elif cm[0] == "trader":
                    _, fid, tx, ty = cm
                    if g.state["floor"] != fid:
                        g.fly(fid)
                    g.talk_trader(fid, tx, ty, f"trader {fid}")
            elif e in ("up", "down", "left", "right", "turn", "help"):
                # skip; auto_sweep / next go_to handles. BUT detect floor change via statlog.
                pass
            else:
                pass
        except RouteError as ex:
            log(f"ri={ri} {e!r} RouteError: {ex}")
            errors += 1
            if errors > 20:
                log("too many errors, stopping")
                break
            continue

        # Floor-change detection: if recording transitions floor here (non-fly), do stair.
        sl_idx = ri_to_sl.get(ri)
        if sl_idx is not None and sl_idx + 1 < len(statlog):
            nxt = statlog[sl_idx + 1]
            cur = statlog[sl_idx]
            if nxt["f"] != cur["f"] and not route[ri].startswith("fly:"):
                # stair transition cur.f -> nxt.f
                stair = find_stair(g, cur["f"], nxt["f"])
                if stair:
                    try:
                        go_to_decomposed(g, cur["f"], stair[0], stair[1], f"stair {cur['f']}->{nxt['f']}")
                        g.transition(nxt["f"], f"stair {cur['f']}->{nxt['f']}")
                    except RouteError as ex:
                        log(f"ri={ri} stair {cur['f']}->{nxt['f']} RouteError: {ex}")
                        errors += 1
                else:
                    log(f"ri={ri} no stair {cur['f']}->{nxt['f']}")
        if g.state["floor"] == stop_floor:
            log(f"reached {stop_floor} at ri={ri}")
            break

    log(f"final: {state_line(g.state)} {g.state['floor']} x{g.state['x']}y{g.state['y']} errors={errors}")

    # Compare floor transitions
    log("\n=== floor transition comparison ===")
    game_transitions = []
    prev = None
    for st in g.steps:
        aft = st.get("after") or {}
        if aft.get("floor") and aft["floor"] != prev:
            game_transitions.append(aft)
            prev = aft["floor"]
    n = min(len(game_transitions), len(rec_floor_states))
    match = 0
    for i in range(n):
        gm = game_transitions[i]
        rc = rec_floor_states[i]
        gs = f"hp={gm.get('hp')} atk={gm.get('atk')} def={gm.get('def')} yk={gm.get('yk')} bk={gm.get('bk')} rk={gm.get('rk')} g={gm.get('gold', gm.get('g'))}"
        rs = f"hp={rc['hp']} atk={rc['atk']} def={rc['def']} yk={rc['yk']} bk={rc['bk']} rk={rc['rk']} g={rc['g']}"
        ok = (gs == rs)
        if ok:
            match += 1
        else:
            log(f"  {i} {gm.get('floor')} vs {rc['f']} {'OK' if ok else 'DIFF'}")
            log(f"    game: {gs}")
            log(f"    rec : {rs}")
    log(f"matched {match}/{n} floor transitions")

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps({"final": g.snapshot(), "steps": g.steps, "errors": g.errors}, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_TXT.write_text("\n".join(buf), encoding="utf-8")
    print(f"json={OUT_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
