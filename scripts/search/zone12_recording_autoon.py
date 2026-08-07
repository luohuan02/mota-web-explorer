#!/usr/bin/env python3
"""Recording-driven Game reproduction (auto ON + skip-if-cleared).

Per user direction: the recording is auto OFF (explicit steps), but we replay
with auto ON (1/2区全开 per CLAUDE.md). Mechanism:

- Follow the recording's hero positions (statlog) in order.
- For each next position: if that tile is already cleared (block_at is None --
  item picked / enemy killed / door opened / fakeWall broken by auto), SKIP it
  (auto already did it) and move to the next recording step.
- Otherwise go_to(target) with auto ON; auto_sweep sweeps adjacent pockets.
  This is what makes "kill (8,2) slime -> auto picks (8,3)(8,4)(9,3)(9,4)" work,
  and "go to (10,11) -> auto picks (11,11) sword" (then the (11,11) step skips).

Floor changes: adjacent (±1) -> stair; non-adjacent -> fly.
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
from scripts.baseline import replay_user_post9_route as guide10
from scripts.search.zone2_game_route import apply_mt10_supply

STATLOG_PATH = Path(r"C:/Users/peiyan.liang/.claude/jobs/79814e6b/tmp/replay_statlog.json")
SAVE1 = ROOT / "outputs" / "results" / "save1_current_snapshot.json"
OUT_JSON = ROOT / "outputs" / "results" / "zone12_recording_autoon.json"
OUT_TXT = Path(r"C:/Users/peiyan.liang/.claude/jobs/79814e6b/tmp/zone12_autoon_report.txt")

MT10_BOSS_TRIGGER = (6, 5)


def load_statlog():
    with open(STATLOG_PATH, encoding="utf-8") as f:
        s = json.load(f)
    return s if isinstance(s, list) else s.get("statlog", s)


def fire_floor_event(g, fid, hero_pos, log):
    """Fire one-shot floor events when the hero reaches a trigger position.

    The recording is auto OFF and triggers these via choices (not visible as
    position changes); modeled on zone2/zone3 event handling. Each fires once.
    """
    hx, hy = hero_pos
    # MT15 thief (9,1): event openDoor (8,1) + thief moves away (9,1 cleared),
    # connecting the (11,2) region (whose only exit is the thief) to (6,1) upFloor.
    # Fire only when the hero is inside the (11,2) region ({(11,2),(11,1),(10,1),
    # (10,2),(9,2)} -- tiles from which the replayer can route to (9,1)-adjacent
    # (10,1)/(9,2) and trigger the dialog). A wider radius fires too early: at
    # (9,4) the (11,3) yellowDoor is still closed, so the (11,2) region is sealed
    # and the replayer cannot reach (9,1). Floor-entry fire is too early too (the
    # hero enters at (6,10), sealed from (9,1) by specialDoor (6,3)).
    if fid == "MT15" and not g.flags.get("mt15_thief") and (hx, hy) in {(11, 2), (11, 1), (10, 1), (10, 2), (9, 2)}:
        before = g.snapshot()
        # The thief event clears the (9,1) one-shot event tile (block.disable in
        # web). set_ground removes the block, but f.events still lists "9,1", so
        # auto_sweep's `if loc_key in f.events: continue` (game_route.py) would
        # keep treating (9,1) as a barrier forever -- sealing the top passage
        # that connects (6,10) to the (3,3)/(1,10)/(3,10) pocket. Pop the event
        # so later auto_sweep crosses (9,1) like live (matches MT29 thief below
        # and MT20 vampire in Game.trigger_tile_event).
        g.floors["MT15"].events.pop("9,1", None)
        if g.block_at("MT15", (8, 1)) is not None:
            g.set_ground("MT15", (8, 1))
        if g.block_at("MT15", (9, 1)) is not None:
            g.set_ground("MT15", (9, 1))  # thief leaves
        g.record("事件", (9, 1), "thief", before, "15F 小偷事件开 (8,1) 门 + 移除 thief，打通 upFloor (6,1) 路径")
        g.flags["mt15_thief"] = 1
        log(f"  [event] MT15 thief: opened (8,1), removed thief (9,1)")
    # MT20 vampire (6,8 trigger -> spawn at 6,6): NOT fired here. The live game
    # requires the hero to step onto (6,8) to trigger the boss entrance (8
    # bigBats merge into vampire at 6,6 + specialDoor at 6,9). The recording's
    # statlog walks through (6,8) (statlog idx 969), and Game.trigger_tile_event
    # spawns the vampire when go_to reaches (6,8). Firing on floor-entry spawned
    # the vampire early and the replayer never clicked (6,8), so the live boss
    # never appeared and step 393 (kill 6,6) failed. The skip-if-cleared guard
    # below must not skip (6,8) because it is an event trigger tile, not an
    # auto-cleared empty tile.
    # MT29 thief (6,2): "ask to pass" -- the hero must step adjacent to (6,2)
    # and talk to trigger the dialogue, which opens (6,3) and removes the thief,
    # connecting (5,2) through (6,2)/(6,3) to the (6,11) upFloor. Skip-empty
    # mode routes the hero to upFloor (6,11) without standing next to (6,2), so
    # walk adjacent + fire the trigger explicitly. Live: click (6,2) -> hero
    # stops at (5,2) -> multi-segment dialogue -> openDoor (6,3) + thief leaves.
    if fid == "MT29" and not g.flags.get("mt29_thief"):
        g.move_adjacent("MT29", 6, 2, "29F 小偷 trigger")
        before = g.snapshot()
        g.floors["MT29"].events.pop("6,2", None)
        if g.block_at("MT29", (6, 3)) is not None:
            g.set_ground("MT29", (6, 3))
        if g.block_at("MT29", (6, 2)) is not None:
            g.set_ground("MT29", (6, 2))  # thief leaves
        g.record("事件", (6, 2), "thief", before, "29F 小偷对话开 (6,3) + 移除 thief，打通 upFloor (6,11) 路径")
        g.flags["mt29_thief"] = 1
        log(f"  [event] MT29 thief: walked to (5,2), opened (6,3), removed thief (6,2)")


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


def main(stop_floor="MT32", write=True, stop_before_redkey_buy=False, skip_ranges=None, stop_after_mt10_supply=False, stop_before_idx=None):
    statlog = load_statlog()
    mt4 = next(i for i, s in enumerate(statlog) if s["f"] == "MT4")

    # skip_ranges: list of (lo, hi) statlog index ranges to skip entirely (e.g. pure
    # gold-farming detours the KILL line does not need). Each removable visit is a
    # fly-based detour, so skipping the whole range leaves the hero pre-detour; the
    # next non-skipped entry flies to the next visit (fly is position-agnostic).
    skip_ranges = skip_ranges or []

    g = Game(read_json(SAVE1))
    g.strict_live_model = True
    g.auto_flags = {"battle": True, "item": True, "wall": True}  # auto ON

    buf = []
    def log(*a):
        buf.append(" ".join(str(x) for x in a))

    log(f"start: {state_line(g.state)} {g.state['floor']} x{g.state['x']}y{g.state['y']}")

    # recording floor-transition reference (BEFORE-state of first action on each floor)
    rec_transitions = []
    prev = None
    for s in statlog:
        if s["f"] != prev:
            rec_transitions.append(s)
            prev = s["f"]

    skipped = 0
    errors = 0
    boss_triggered = False
    skip_mt10_supply = False
    i = mt4
    g.state["x"], g.state["y"] = statlog[mt4]["x"], statlog[mt4]["y"]
    while i + 1 < len(statlog):
        cur = statlog[i]
        nxt = statlog[i + 1]
        if any(lo <= i < hi for lo, hi in skip_ranges):
            i += 1
            continue
        # stop before processing a given statlog index (e.g. stop before the
        # redKey-merchant approach segment, which the KILL line does not need).
        if stop_before_idx is not None and i >= stop_before_idx:
            log(f"[stop] before statlog idx {stop_before_idx}: {state_line(g.state)} {g.state['floor']} x{g.state['x']}y{g.state['y']}")
            break
        if g.state["floor"] == stop_floor and nxt["f"] != stop_floor:
            break
        # After MT10 boss+supply (auto-eaten), skip the recording's manual supply
        # picks (same-floor MT10 steps) until the MT10->MT11 floor transition, which
        # the normal stair/fly branch below handles. Clear the flag once off MT10.
        if skip_mt10_supply and cur["f"] == "MT10" and nxt["f"] == "MT10":
            i += 1
            continue
        if skip_mt10_supply and cur["f"] != "MT10":
            skip_mt10_supply = False
        # Floor event triggers: when the hero reaches a trigger position, fire the
        # one-shot event (the recording is auto OFF so it triggers these via choices,
        # which aren't visible as position changes). Modeled on zone2/zone3 events.
        fire_floor_event(g, cur["f"], (g.state["x"], g.state["y"]), log)
        # Shop/trader purchase: same floor + same position + gold changed (excludes
        # plain door-opens, which are yk-1 only with no gold change). The recording
        # is auto OFF so it buys explicitly; apply via buy_shop / talk_trader.
        if (cur["f"] == nxt["f"] and cur["x"] == nxt["x"] and cur["y"] == nxt["y"]
                and nxt.get("g", cur.get("g", 0)) != cur.get("g", 0)):
            da = nxt.get("atk", 0) - cur.get("atk", 0)
            dd = nxt.get("def", 0) - cur.get("def", 0)
            # kill-branch 钩子：停在 MT12 redKey trader 买之前（cross 已持、ATK70、RK=0），
            # 让调用方 clone 后真杀 zKnight 验证机制。
            if stop_before_redkey_buy and cur["f"] == "MT12" and da == 0 and dd == 0:
                log(f"[stop] before MT12 redKey buy at i={i}: {state_line(g.state)} cross={g.state.get('cross')} rk={g.state['rk']}")
                break
            ratio = g.floors[cur["f"]].ratio
            try:
                # Find the adjacent shop NPC so buy_shop records its tile (the
                # replayer clicks the NPC to open the choices dialog; recording
                # the hero's tile leaves the replayer clicking empty floor).
                shop_pos = None
                for sdx, sdy in ((0, -1), (-1, 0), (0, 1), (1, 0)):
                    sb = g.block_at(cur["f"], (cur["x"] + sdx, cur["y"] + sdy))
                    if sb and sb.eid in {"shop", "blueShop", "redShop", "yellowShop"}:
                        shop_pos = (cur["x"] + sdx, cur["y"] + sdy)
                        break
                if da > 0:
                    g.buy_shop("atk", da // (2 * ratio), shop_pos=shop_pos)
                elif dd > 0:
                    g.buy_shop("def", dd // (4 * ratio), shop_pos=shop_pos)
                else:
                    # trader: hero is adjacent to an npc trader block; find it
                    hx, hy = cur["x"], cur["y"]
                    trader = None
                    for dx, dy in ((0, -1), (-1, 0), (0, 1), (1, 0)):
                        b = g.block_at(cur["f"], (hx + dx, hy + dy))
                        if b and b.kind == "npc" and b.eid == "trader":
                            trader = (hx + dx, hy + dy)
                            break
                    if trader:
                        g.talk_trader(cur["f"], trader[0], trader[1], f"purchase {cur['a']!r}")
                    else:
                        log(f"i={i} purchase at {cur['f']} x{hx}y{hy} but no adjacent trader")
                        errors += 1
            except RouteError as ex:
                log(f"i={i} purchase {cur['f']} x{cur['x']}y{cur['y']} RouteError: {ex}")
                errors += 1
            i += 1
            continue
        # Use the hero's ACTUAL floor (not the statlog's cur["f"]) for transition
        # detection, so skip_ranges fly-detours work: after a skip the hero stays
        # on its real floor, and the next statlog target on a different floor
        # triggers a position-agnostic fly. In the non-skip case
        # g.state["floor"] == cur["f"], so this is a no-op (no regression).
        hf = g.state["floor"]
        if nxt["f"] != hf:
            if abs(floor_no(nxt["f"]) - floor_no(hf)) == 1:
                stair = find_stair(g, hf, nxt["f"])
                if stair:
                    try:
                        go_to_decomposed(g, hf, stair[0], stair[1], f"stair {hf}->{nxt['f']}")
                        g.transition(nxt["f"], f"stair {hf}->{nxt['f']}")
                    except RouteError as ex:
                        log(f"i={i} stair {hf}->{nxt['f']} RouteError: {ex}")
                        errors += 1
                else:
                    log(f"i={i} no stair {hf}->{nxt['f']}")
                    errors += 1
            else:
                try:
                    g.fly(nxt["f"])
                except RouteError as ex:
                    log(f"i={i} fly {nxt['f']} RouteError: {ex}")
                    errors += 1
        elif cur["f"] == "MT10" and (nxt["x"], nxt["y"]) == MT10_BOSS_TRIGGER and not boss_triggered:
            # MT10 boss: reach (6,5) trigger, spawn SPAWNED_BOSS, then model the live
            # auto-battle (clearMt10BossDyn) that one-shots all spawned + captain.
            # The recording (auto OFF) kills them step-by-step; the net damage is the
            # same. After this, the recording's individual spawn-kill positions are
            # cleared tiles -- the walk-to-empty step below handles them harmlessly.
            try:
                go_to_decomposed(g, "MT10", 6, 5, "MT10 boss 触发")
            except RouteError as ex:
                log(f"i={i} MT10 boss trigger RouteError: {ex}")
                errors += 1
            if g.steps and g.steps[-1].get("action") == "到达":
                g.steps[-1]["action"] = "事件"
                g.steps[-1]["eid"] = "bossEvent"
            for sp_pos, sp_eid in guide10.SPAWNED_BOSS.items():
                g.set_block("MT10", sp_pos, "enemy", sp_eid)
            cleared = g.clear_mt10_boss_dyn()
            if cleared and g.steps:
                g.refresh_last_step(
                    g.steps[-1]["before"],
                    "clearMt10BossDyn 动态清: " + ", ".join(cleared),
                )
            # MT10 boss trigger also fires the (6,9) thief event: it opens the
            # captain-path yellowWall (6,3), auto-eats the 12 supply resources
            # (6gem+3bluePotion+3yellowKey -- the recording picks these manually
            # step-by-step since it is auto OFF; net stats are identical), and
            # opens the 11F stair. Use zone2's web-verified apply_mt10_supply.
            apply_mt10_supply(g)
            boss_triggered = True
            skip_mt10_supply = True  # skip recording's manual supply picks (auto-eaten)
            log(f"i={i} MT10 boss+supply done: hp={g.state['hp']} atk={g.state['atk']} hero=({g.state['x']},{g.state['y']})")
            if stop_after_mt10_supply:
                log(f"[stop] after MT10 boss+supply: {state_line(g.state)}")
                break
        else:
            tx, ty = nxt["x"], nxt["y"]
            tile_empty = g.block_at(hf, (tx, ty)) is None
            is_event_trigger = f"{tx},{ty}" in g.floors[hf].events
            # skip-if-cleared: tile already empty (auto picked/broke it) -> skip.
            # But an event-trigger tile (e.g. MT20 (6,8) vampire entrance) is
            # empty (id 0) yet must be walked onto to fire its event -- never
            # skip those, or the live boss never spawns.
            if tile_empty and not is_event_trigger and (g.state["x"], g.state["y"]) == (tx, ty):
                skipped += 1
            elif tile_empty and not is_event_trigger and (g.state["x"], g.state["y"]) != (tx, ty):
                # auto ON: 该格已被 auto_sweep 清空 (block_at is None) -- 不再让 hero
                # 走到空格去对齐录像 statlog 位置。Game auto 语义：清了就是清了，hero
                # 原地不动，下一个真实目标 re-plan 路线时 auto 会顺带清路上的资源。
                # auto OFF 录像的位置不是 auto ON 回放的硬约束。
                skipped += 1
            else:
                try:
                    go_to_decomposed(g, hf, tx, ty, f"step {cur['a']!r}")
                except RouteError as ex:
                    log(f"i={i} {cur['a']!r} -> ({tx},{ty}) RouteError: {ex}")
                    errors += 1
                    if errors > 40:
                        log("too many errors")
                        break
        i += 1

    log(f"final: {state_line(g.state)} {g.state['floor']} x{g.state['x']}y{g.state['y']} errors={errors} skipped={skipped}")

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
    if write:
        OUT_JSON.write_text(json.dumps({"final": g.snapshot(), "steps": g.steps, "errors": g.errors, "ok": not g.errors}, ensure_ascii=False, indent=2), encoding="utf-8")
        OUT_TXT.write_text("\n".join(buf), encoding="utf-8")
    print(f"matched {match}/{n}; errors={errors}; skipped={skipped}; json={OUT_JSON}")
    return g


if __name__ == "__main__":
    g = main()
    raise SystemExit(0 if g else 1)
