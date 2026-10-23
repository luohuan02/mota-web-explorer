#!/usr/bin/env python3
"""录像 -> Game 类可复现转换器（token 驱动 + content-classification，auto ON）。

输入：解码后的录像 route（list[str]，如 "move:5:11"/"up"/"choices:1"/"fly:MT12"）
      + ground-truth statlog（web core.startGame 回放捕获，PRE-state：每个
        _doReplayAction 执行**前**记 {i,a,f,x,y,hp,atk,def,yk,bk,rk,g} + 末尾 FINAL）。
      + SAVE1（MT4 到达态完整存档；= statlog[start_stat]）。
      + paths（automaticRoute 每个 move:x:y 的寻路路径，消除 path_to 分歧）。

关键机制（实机 step-by-step 确认）：
- 录像是 auto ON（battle/item/wall 全开）。web core.plugin.auto 只 battle/item/wall，
  **不开门**（门只能手动开）。
- 箭头步 = 按目标格内容行动（NOT turn-then-move；全程仅 1 个 turn）：
  door -> 开门 + hero 停原位（door_stay，消费钥匙不移动）；
  enemy -> 战斗 + hero 移上去；item/empty -> hero 移上去；stair -> transition；
  wall/越界 -> no-op。
- move:x:y = automaticRoute 寻路，逐格 step_path（非严格门=开门+移上门上），
  moveDirectly 先走一步（captured path 不含首步，需 prepend）。
- choices 不产生 stat 条目；delta = stat[next_non_choices] - 当前 g.state。

statlog 是 PRE-state：stat[si] = 第 si 个 non-choices action 执行前状态 = 上个 action
(含其后的 choices) 结算后状态。所以 verify = 处理每个 non-choices action **前**
drift-check g.state == stat[si]；循环末尾 g.state == stat[FINAL]。

Usage:
  python scripts/search/recording_to_game.py \
    --route <decoded_route.json> --statlog <statlog_pre.json> \
    --save1 <save1.json> --paths <paths.json> \
    --out <out.json> [--report <txt>] [--stop-floor MT21] [--start-stat 55]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from src.solver.game_route import Game, read_json, state_line, RouteError, floor_no, go_to_decomposed


def load_route(p: Path) -> list:
    data = json.loads(p.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else data.get("route", data)


def load_statlog(p: Path) -> list:
    data = json.loads(p.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else data.get("statlog", data)


def scan_residual(g: Game, lo: int = 1, hi: int = 20):
    """扫 zone(lo-hi) 楼层剩余资源（final-score 0伤害口径）。
    返回 (total, rows, cats)。cats 按类别分组剩余资源明细。
    item: YK=50/BK=200/redPotion=50/bluePotion=200, redKey/gem 默认 0;
    door: yellowDoor -50 / blueDoor -200; enemy: 0伤(atk>=def) 金币 money/2。"""
    s = g.state
    cross_targets = {"zombie", "zombieKnight", "vampire"}
    item_val = {"yellowKey": 100, "blueKey": 500, "redPotion": 50, "bluePotion": 200}
    door_cost_map = {"yellowDoor": 100, "blueDoor": 500}
    total = 0
    rows = []
    cats = {"yellowKey": [], "blueKey": [], "redPotion": [], "bluePotion": [],
            "redKey": [], "redGem": [], "blueGem": [],
            "yellowDoor": [], "blueDoor": [], "redDoor": [], "monster_gold": []}
    for fid in sorted(g.floors, key=lambda f: floor_no(f)):
        n = floor_no(fid)
        if n < lo or n > hi:
            continue
        fl = g.floors[fid]
        for pos, blk in fl.blocks.items():
            if blk is None:
                continue
            loc = f"{fid} x{pos[0]}y{pos[1]}"
            if blk.kind == "item":
                v = item_val.get(blk.eid, 0)
                if blk.eid == "redGem":
                    v = 260 if s["atk"] < 27 else 0
                elif blk.eid == "blueGem":
                    v = 280 if s["def"] < 27 else 0
                if blk.eid in cats:
                    cats[blk.eid].append(loc)
                if v:
                    total += v
                    rows.append(f"{loc} {blk.eid} +{v}")
            elif blk.kind == "door":
                c = door_cost_map.get(blk.eid, 0)
                if blk.eid in cats:
                    cats[blk.eid].append(loc)
                if c:
                    total -= c
                    rows.append(f"{loc} {blk.eid} -{c}")
            elif blk.kind == "enemy":
                e = g.enemies.get(blk.eid)
                if not e:
                    continue
                atk = s["atk"] * (2 if s.get("cross") and blk.eid in cross_targets else 1)
                if atk >= int(e["def"]):  # 0伤
                    money = int(e.get("money", 0))
                    if money:
                        total += money // 2
                        rows.append(f"{loc} {blk.eid} 0伤金+{money//2}")
                        cats["monster_gold"].append(f"{loc} {blk.eid} +{money}")
    return total, rows, cats


def find_stair(g: Game, from_fid: str, to_fid: str):
    going_up = floor_no(to_fid) > floor_no(from_fid)
    want = "upFloor" if going_up else "downFloor"
    cands = [pos for pos, blk in g.floors[from_fid].blocks.items() if blk.eid == want]
    if not cands:
        return None
    if len(cands) == 1:
        return cands[0]
    hx, hy = g.state["x"], g.state["y"]
    return min(cands, key=lambda p: abs(p[0] - hx) + abs(p[1] - hy))


def adjacent_block(g: Game, fid: str, eid: str | None = None, kind: str | None = None):
    hx, hy = g.state["x"], g.state["y"]
    for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
        blk = g.block_at(fid, (hx + dx, hy + dy))
        if not blk:
            continue
        if eid and blk.eid == eid:
            return (hx + dx, hy + dy)
        if kind and blk.kind == kind:
            return (hx + dx, hy + dy)
    return None


def stats_of(g: Game) -> dict:
    s = g.state
    return {"f": s["floor"], "hp": s["hp"], "atk": s["atk"], "def": s["def"],
            "yk": s["yk"], "bk": s["bk"], "rk": s["rk"], "g": s["gold"],
            "x": s["x"], "y": s["y"]}


def _statlog_noop(pre: dict, post: dict) -> bool:
    """statlog 前后两条(pre-state of si / pre-state of si+1)在 pos+stat 上全同
    = 该 action 是录像里的 no-op(turn 转身/面墙误触),可安全跳过。"""
    return all(pre[k] == post[k]
               for k in ("x", "y", "hp", "atk", "def", "yk", "bk", "rk", "g"))


def step_path(g: Game, fid: str, tx: int, ty: int, note: str, run_auto: bool = True, is_arrow: bool = False) -> None:
    """Move hero ONE tile onto (tx,ty). Non-strict door: OPENS + hero moves ONTO
    (matches move:x:y automaticRoute 过门). apply_block handles door/enemy/item;
    empty tiles just move + trigger events.

    For ENEMY kills, use go_to's deferred-after_action pattern: web's post-battle
    auto_sweep runs BEFORE mechanism doors open (after_action deferred), and
    opening a door does NOT re-trigger BFS. So: capture door opens during
    apply_block, auto_sweep with door still closed, then flush (no second sweep).
    Without this, e.g. MT8 killing (11,5) opens (10,4) specialDoor and auto_sweep
    immediately BFS-picks the +250hp/+2yk/+1rk beyond it, diverging from live
    (which picks them on the later move:10:3 through the open door).

    run_auto: 是否在本格触发 auto_sweep。move:x:y 的中间普通格 run_auto=False
    (auto 延后到末格/走门格),匹配 web automaticRoute 只在末格/走门格触发 auto,
    不在中间普通格触发(否则 walk 会把中间格 emit 成独立 auto step,但 live 在该
    格不拾取,如 MT10 move:6:8 的 6,2:hero 1-tile 点击到普通格,web auto 不触发,
    12 个奖励延后到末格 6,8 才拾取)。击杀格总 run_auto(战后 auto 不可延后)。"""
    blk = g.block_at(fid, (tx, ty))
    before = g.snapshot()
    g.state["x"], g.state["y"] = tx, ty
    if blk is not None:
        if (blk.kind == "item" and not is_arrow
                and not g._auto_item_allowed(blk.eid, g.auto_flags.get("item"))):
            # h5mota move:x:y 经路径无门/怪时 moveDirectly 传送(hero 不逐格踩),item(trigger=
            # getItem)不触发;item 只在 arrow 踩格 trigger 拾取 + core.auto sweep(auto item ON)
            # 拾取。故 move:x:y(非 arrow)经 item 格且 auto item 关时不拾(item 留格,hero 通过),
            # 匹配 3atk auto OFF 录像(move:9:2 经 (10,2) redKey rk 不变)。arrow(is_arrow)踩格
            # trigger 总拾取(不管 auto)。auto item 开时 _auto_item_allowed=True 不进此分支(等价
            # sweep),不破 2攻0def(auto ON)。
            g.record("通过", (tx, ty), blk.eid, before, note)
            g.apply_check_damage(fid, (tx, ty), note)
            if run_auto:
                handled = g.auto_sweep(fid)
                if handled:
                    g.refresh_last_step_with_auto(before, handled)
            return
        is_enemy = blk.kind == "enemy"
        old = g.strict_live_model
        g.strict_live_model = False
        triggered = False
        try:
            if is_enemy:
                g._defer_after_action = True
            try:
                triggered = g.apply_block(fid, (tx, ty), blk, note)
            finally:
                if is_enemy:
                    g._defer_after_action = False
        finally:
            g.strict_live_model = old
        if is_enemy:
            has_after_battle_event = f"{tx},{ty}" in g.floors[fid].after_battle
            handled: list[str] = []
            if not has_after_battle_event:
                handled += g.auto_sweep(fid)
            g._flush_deferred_after_effects()
            if f"{tx},{ty}" in g.floors[fid].after_battle_auto:
                handled += g.auto_sweep(fid)
            if handled:
                g.refresh_last_step_with_auto(before, handled)
        else:
            if run_auto:
                handled = g.auto_sweep(fid)
                if handled:
                    g.refresh_last_step_with_auto(before, handled)
        if triggered:
            # block 分支(门/敌/物/NPC)apply_block 末尾调 trigger_tile_event;若触发
            # (如 MT15 (9,1) thief NPC 触发开 (8,1)),标 trigger-event 让 move merge
            # 在此拆分:web automaticRoute 中途踩 NPC trigger 格会中断寻路。
            g.steps[-1]["note"] = (g.steps[-1].get("note") or "") + "; trigger-event"
    else:
        g.record("通过", (tx, ty), None, before, note)
        g.apply_check_damage(fid, (tx, ty), note)
        triggered = g.trigger_tile_event(fid, (tx, ty))
        # 踩上被清开的门格(former-door)时 run_auto 会触发 auto_sweep 拾门后资源,
        # 但 hero 不在此停顿:录像 statlog 证明 hero 一次性到达 move 目标(drift_check
        # 0 mismatch),web auto 不中断 automaticRoute。故不再标 walkonto-door/不再
        # 切断 captured path -- 走门格是 converter 切断 through-path 凭空造的冗余步。
        if run_auto:
            handled = g.auto_sweep(fid)
            if handled:
                g.refresh_last_step_with_auto(before, handled)
        if triggered:
            # 事件 trigger 格:web automaticRoute 中途踩事件格会中断寻路
            # (如 MT10 (6,5) spawn 后 6,6 变怪挡路,hero 卡 6,5)。v2 须单独
            # 保留该 pass(不合并进下个目标),让 replayer 分步踩 trigger。
            g.steps[-1]["note"] = (g.steps[-1].get("note") or "") + "; trigger-event"


def open_door_stay(g: Game, fid: str, dx: int, dy: int, note: str) -> bool:
    """Arrow step into an adjacent door: OPEN it (consume key) but hero STAYS
    (door_stay, confirmed live: down at (1,7) -> (1,8) yellowDoor opens, yk-1,
    hero stays (1,7)). NO auto_sweep: web core.plugin.auto only triggers after
    the hero MOVES; a door_stay (no pos change) does not trigger auto, so an
    item revealed by the opened door (e.g. MT5 sword1 past (8,9)+(9,11) fakeWall)
    is NOT swept until the hero actually moves onto a BFS-reachable tile.
    Returns False if (dx,dy) isn't a door or open fails."""
    blk = g.block_at(fid, (dx, dy))
    if blk is None or blk.kind != "door":
        return False
    old_errors = len(g.errors)
    old = g.strict_live_model
    g.strict_live_model = False
    try:
        g.apply_block(fid, (dx, dy), blk, note)
        return True
    except Exception:
        del g.errors[old_errors:]
        return False
    finally:
        g.strict_live_model = old


def break_wall_stay(g: Game, fid: str, wx: int, wy: int, note: str) -> bool:
    """Arrow step into adjacent fakeWall2 (暗墙): BREAK it (trigger openDoor) but
    hero STAYS on the adjacent tile -- same semantics as open_door_stay. Web: hero
    steps toward 暗墙, trigger openDoor 破墙, afterOpenDoor may spawn an item on the
    wall tile (e.g. MT19 (6,3) cross); the spawned block locks the tile so hero
    cannot move onto it in the same step and remains adjacent. 暗墙和门统一：接近
    触发 + stay，不一步踩上去。NO auto_sweep (like door_stay)."""
    blk = g.block_at(fid, (wx, wy))
    if blk is None or blk.kind != "terrain" or blk.eid != "fakeWall2":
        return False
    old_errors = len(g.errors)
    old = g.strict_live_model
    g.strict_live_model = False
    try:
        g.apply_block(fid, (wx, wy), blk, note)  # 破墙 + set_ground + after_action (spawn) + trigger
        return True
    except Exception:
        del g.errors[old_errors:]
        return False
    finally:
        g.strict_live_model = old


def try_step_path(g: Game, fid: str, tx: int, ty: int, note: str, run_auto: bool = True, is_arrow: bool = False) -> bool:
    old_errors = len(g.errors)
    try:
        step_path(g, fid, tx, ty, note, run_auto=run_auto, is_arrow=is_arrow)
        return True
    except Exception:
        del g.errors[old_errors:]
        return False


_AUTO_MARKERS = ("auto_sweep:", "auto:", "live auto:")


def _note_has_auto(note: str) -> bool:
    return any(m in note for m in _AUTO_MARKERS)


def _is_pass(s) -> bool:
    return s.get("action") == "通过" and s.get("eid") is None


def _is_target(s) -> bool:
    """可直达的目标 step:击杀/开门/拾取/破墙/踩楼梯(通过+楼梯 eid)。"""
    a = s.get("action")
    if a in ("击杀", "开门", "拾取", "破墙"):
        return True
    if a == "通过" and s.get("eid") in ("upFloor", "downFloor"):
        return True
    return False


def _is_walkonto_door(s, prev) -> bool:
    """走门格 pass:开门 stay before 后走一步到门格(用户要求保留,解决 auto 时序)。"""
    if not _is_pass(s) or prev is None:
        return False
    if prev.get("action") != "开门":
        return False
    sp = s.get("pos")
    pp = prev.get("pos")
    return sp is not None and pp is not None and tuple(sp) == tuple(pp)


def _has_trigger(note: str) -> bool:
    """事件 trigger pass:hero 踩格触发楼层事件(spawn/移动)。须单独保留(v2 不合并):
    web automaticRoute 中途踩事件格会中断寻路(如 MT10 (6,5) boss spawn)。"""
    return "trigger-event" in note


def _has_walkonto_door(note: str) -> bool:
    """踩上被清开的门格(走门格,former door):live auto 在此触发并中断
    automaticRoute(hero 停该格)。须单独保留,否则合并进后续目标会让 replayer
    一次点到目标,但 live 中断在此 -> 位置 mismatch(如 MT10 captain 清 6,9
    redDoor 后,6,8->6,11 路过 6,9 中断,hero 停 6,9)。"""
    return "walkonto-door" in note


def _is_door_walkonto_merged(s) -> bool:
    """开门+走门格 pass(pass 1 合并产物):开门(消费钥匙)+走门格 两步合一。
    须独立点击(replayer 点门:door_stay 开门 + retry 走门格),不能合并进后续目标--
    否则 replayer 点后续目标时门未开,hero 寻路被关闭的门挡住(如 MT4 11,8 黄门是
    11,9 区到 4,7 的必经路,fold move:waypoint 后该 door-pass 紧接 kill,若被
    pass 3 当普通 pass 收集合并进 kill,门永远不开 -> 卡死/YK mismatch)。"""
    return (s.get("action") == "通过" and s.get("eid") is None
            and "开门+走门格" in (s.get("note") or ""))


def _is_move_merge(note: str) -> bool:
    """move:x:y 的 merge step(note 以 "move " 开头,如 "move move:9:2 直达 9,2"):
    多格 automaticRoute,可能含绕路(detour,如 MT15 11,2->9,2->5,1 绕 8,2 墙到
    6,1)。coalesce 不能合并它进后续目标,否则 replayer 一次点目标,hero 走直线
    automaticRoute 被墙/障碍挡住找不到路(录像实际绕了路)-> "stopped before stair"。
    保留独立步让 replayer 逐个点 move 目标,hero 走录像的 exact 路径。"""
    return note.startswith("move ")


def _extract_auto(note: str, seen: set, parts: list) -> None:
    for m in _AUTO_MARKERS:
        k = note.find(m)
        if k < 0:
            continue
        rest = note[k + len(m):].strip()
        for sep in (";", "；"):
            p = rest.find(sep)
            if p >= 0:
                rest = rest[:p]
        for it in rest.split(","):
            it = it.strip().rstrip(",")
            if it and it not in seen:
                seen.add(it)
                parts.append(it)


def _merge_move_segment(seg: list, a: str) -> dict:
    """合并一段 move 逐格 step 成 ONE step at 段末格(replayer 点段末格一次到位)。
    段内不含中断点(trigger-event/walkonto-door),合并安全:web automaticRoute
    末格点击,hero 走完整段,auto 在走门格/末格触发,终态一致。"""
    merged = dict(seg[-1])
    merged["before"] = seg[0].get("before")
    auto_parts: list[str] = []
    seen_auto: set[str] = set()
    for p in seg:
        _extract_auto(p.get("note") or "", seen_auto, auto_parts)
    lp = seg[-1]["pos"]
    note_parts = [f"move {a} 直达 {lp[0]},{lp[1]} (合并 {len(seg)} step)"]
    if auto_parts:
        note_parts.append("live auto: " + ", ".join(auto_parts))
    # 保留段末中断点标记(trigger-event / walkonto-door),否则被 "move ... 直达 ..."
    # note 覆盖,coalesce 误把中断段当普通 move_merge 合并/折叠,丢失 web 中断点
    # (如 move:11:3 段1 末 (8,9) former-door 的 walkonto-door 标记,MT10 (6,2)
    # 骷髅队长剧情 trigger-event 标记)。
    seg_note = seg[-1].get("note") or ""
    if "trigger-event" in seg_note:
        note_parts.append("trigger-event")
    if "walkonto-door" in seg_note:
        note_parts.append("walkonto-door")
    merged["note"] = "; ".join(note_parts)
    return merged


def _merge_door_walkonto(steps: list) -> list:
    """Pass 1:不再合并 "开门 X + 走门格 pass X"(用户要求去掉走门格)。

    走门格(走到门格上)不是游戏机制(door_stay 开门 hero 停邻格才是),是冗余动作。
    开门(arrow door_stay)独立成 step(hero 邻格),走门格(move merge)留给 Pass 2
    _fold_move_waypoint case 1 折进紧接目标:replayer 点开门(门开 hero 邻格)+ 点目标,
    hero 寻路经门格(former-door)auto 拿门后资源,到达目标。开门已开门,后续寻路不被挡。
    录像 statlog 证明 hero 一次性可达目标(web auto 不中断),故折进目标安全。"""
    return list(steps)


def _merge_waypoint_into_target(wp: dict, tgt: dict) -> dict:
    """把 move waypoint step wp 折进紧接的目标 step tgt:用 wp 的 before(更早 pre-state),
    合并两者的 auto items 成一个 auto_sweep 段。replayer assertAutoSweepSideEffects
    只查首个 auto_sweep 段,故须合并;gen_zone_walk_md extract_clear_note 遍历所有
    marker 也能正确显示。tgt 的描述性 note(开门+走门格/step ... battle 等)保留,
    wp 的 "move ... 直达 ..." 噪声丢弃。"""
    merged = dict(tgt)
    merged["before"] = wp.get("before")
    tgt_note = tgt.get("note") or ""
    wp_note = wp.get("note") or ""
    all_auto: list[str] = []
    seen: set[str] = set()
    _extract_auto(tgt_note, seen, all_auto)
    _extract_auto(wp_note, seen, all_auto)
    rest_parts: list[str] = []
    for part in tgt_note.replace("；", ";").split(";"):
        p = part.strip()
        if not p or any(m in p for m in _AUTO_MARKERS):
            continue
        rest_parts.append(p)
    note_parts = list(rest_parts)
    if all_auto:
        note_parts.append("auto_sweep: " + ", ".join(all_auto))
    merged["note"] = "; ".join(note_parts) if note_parts else tgt_note
    return merged


def _is_shop_npc_target(s) -> bool:
    """Shop/NPC interaction target: hero must reach the adjacent tile first and
    face-on trigger the commonEvent (shop/trader dialog). Folding the preceding
    move waypoint into the target makes the replayer click the NPC from wherever
    the hero is (possibly far), so automaticRoute routes the hero to adjacent and
    repeatTargetClick can mis-select a buy option (MT12 blueShop: hero at (8,11)
    after bat, folded 事件 blueShop click bought HP instead of atk). Keep the
    move-to-adjacent step separate so the hero stands adjacent before the click."""
    a = s.get("action")
    if a in ("商店", "商人"):
        return True
    if a == "事件" and s.get("eid") in {"blueShop", "trader", "shop", "oldman"}:
        return True
    return False


def _fold_move_waypoint(steps: list) -> list:
    """Pass 2:fold move waypoint + 紧接目标步。

    两类 fold:
    1. adjacent fold(安全):move:x:y waypoint W + 紧接 adjacent(Manhattan=1)目标 T
       (T 非 door-pass)。auto_sweep at T ⊇ at W(BFS 覆盖相邻格),W 的 before+auto
       累计进 T 不丢。replayer repeatTargetClick(3 retry)处理中途 former-door 停顿。
    2. former-door 中断段 fold(去掉"move 到空地"/"门后再次点击门位置"冗余,用户要求):
       walkonto-door 中断段 W(move_merge 段末 former-door,如 move:11:3 段1 末 (8,9);
       或 walkonto-door step,如 hero 走回 former-door)+ 紧接目标 T(无论 adjacent,
       含 door-pass)。W 是 former-door walkonto(web 踩 former-door auto_sweep 中断寻路)。
       fold 后 replayer 点 T,hero 寻路经 former-door;若 web 不中断(资源已清)则 OK,
       若中断则 mismatch,需回退保留独立步。

    in-place 折叠后重处理 folded step,支持链式 fold。"""
    steps = list(steps)
    i = 0
    while i < len(steps):
        s = steps[i]
        snote = s.get("note") or ""
        sp = s.get("pos")
        if i + 1 >= len(steps) or sp is None:
            i += 1
            continue
        nxt = steps[i + 1]
        np_ = nxt.get("pos")
        if (nxt.get("floor") != s.get("floor") or nxt.get("action") == "换层"
                or np_ is None):
            i += 1
            continue
        adjacent = abs(sp[0] - np_[0]) + abs(sp[1] - np_[1]) == 1
        is_walkonto = "walkonto-door" in snote
        mm = _is_move_merge(snote)
        # adjacent 安全 fold(move_merge + adjacent + nxt 非 door-pass);
        # 或 former-door 中断段 fold(walkonto-door + pass,任意 nxt)
        # door_stay(开门)不 fold 进 move:replayer 点 door_stay,hero automaticRoute
        # 寻路到门邻格,若路径有怪/门挡(automaticRoute 不杀不开)则卡。move 独立
        # (hero 到邻格 auto_sweep 清挡)+ door_stay 独立(点门开门)。3攻5防 MT9
        # step 237 move(杀(1,8)骷髅)+door_stay(3,7)fold 致 hero (1,10) 卡。
        if ((mm and adjacent and not _is_door_walkonto_merged(nxt)
                and nxt.get("action") != "开门"
                and not _is_shop_npc_target(nxt))
                or (is_walkonto and _is_pass(s))):
            steps[i] = _merge_waypoint_into_target(s, nxt)
            del steps[i + 1]
            continue  # 重处理 folded step(可能继续折进 next-next)
        i += 1
    return steps


def coalesce_node_level(steps: list) -> list:
    """emit 节点级 walk(贴合 Game go_to 直达目标)。

    内部 captured path 逐格精确复现录像路径 + auto_sweep(state 对齐 statlog 0
    mismatch);walk emit 时把"前导无 auto pass 序列 + 目标 step(击杀/开门/拾取/
    破墙/踩楼梯)"合并成 1 步直达目标 step,匹配 Game 类 go_to 节点直达 + replayer
    点击目标游戏 automaticRoute 一次到位。

    保留(不合并):
    - 有 auto_sweep 的 pass:独立节点(auto 触发点,合并会丢 auto 时序)
    - 走门格 pass:开门 stay before 后走一步到门格(用户要求,解决 auto 时序)
    - 事件 trigger pass:hero 踩格触发 spawn/移动,web 寻路中途踩会中断(须分步)
    - 换层(CHANGE_FLOOR)单独
    - 开门 stay + 走门格 两步模式(用户要求保留)"""
    # Pass 1: 合并 开门 X + 走门格 pass X -> 开门+走门格 (见 _merge_door_walkonto)。
    # Pass 2: fold move:x:y waypoint + 紧接 adjacent 目标 -> 目标 (见 _fold_move_waypoint),
    #   消除"移到非目标空格"冗余费步(replayer 点目标 hero auto-route 经 waypoint)。
    steps = _fold_move_waypoint(_merge_door_walkonto(steps))
    out: list = []
    i = 0
    n = len(steps)
    while i < n:
        s = steps[i]
        prev = steps[i - 1] if i > 0 else None
        if (not _is_pass(s) or _note_has_auto(s.get("note") or "")
                or _is_walkonto_door(s, prev) or _has_trigger(s.get("note") or "")
                or _has_walkonto_door(s.get("note") or "")
                or _is_door_walkonto_merged(s)
                or _is_move_merge(s.get("note") or "")):
            out.append(s)
            i += 1
            continue
        # 收集连续无 auto 非 走门格 非 trigger pass(同楼层)
        passes = [s]
        j = i
        while j + 1 < n:
            nxt = steps[j + 1]
            if (_is_pass(nxt) and nxt["floor"] == s["floor"]
                    and not _note_has_auto(nxt.get("note") or "")
                    and not _is_walkonto_door(nxt, steps[j])
                    and not _has_trigger(nxt.get("note") or "")
                    and not _has_walkonto_door(nxt.get("note") or "")
                    and not _is_door_walkonto_merged(nxt)
                    and not _is_move_merge(nxt.get("note") or "")):
                passes.append(nxt)
                j += 1
            else:
                break
        # j+1: 目标 step / 非 pass / 换层 / 跨层 -> 合并 passes+目标 成1步直达目标
        if j + 1 < n:
            target = steps[j + 1]
            if target["floor"] == s["floor"] and _is_target(target):
                auto_parts: list[str] = []
                seen_auto: set[str] = set()
                for p in passes:
                    _extract_auto(p.get("note") or "", seen_auto, auto_parts)
                _extract_auto(target.get("note") or "", seen_auto, auto_parts)
                tpos = target["pos"]
                note_parts = [f"直达 {tpos[0]},{tpos[1]} (合并 {len(passes)} pass + {target['action']})"]
                if auto_parts:
                    note_parts.append("auto_sweep: " + ", ".join(auto_parts))
                merged = dict(target)
                merged["before"] = passes[0].get("before")
                merged["note"] = "; ".join(note_parts)
                out.append(merged)
                i = j + 2
                continue
        # 无目标:合并 passes 成1步 pass(节点级直达末格)
        if len(passes) > 1:
            last = passes[-1]
            merged = dict(last)
            merged["before"] = passes[0].get("before")
            merged["note"] = f"节点级直达 {last['pos'][0]},{last['pos'][1]} (合并 {len(passes)} pass)"
            out.append(merged)
            i = j + 1
            continue
        out.append(s)
        i += 1
    return out


def _is_stair_pass(s) -> bool:
    return s.get("action") == "通过" and s.get("eid") in ("upFloor", "downFloor")


def _hoist_stair_uturn(steps: list) -> list:
    """楼梯 U 型折返提升(coalesce 后 pass,录像多余动作,用户反馈)。

    录像里玩家第一次上/下楼时漏拿本层资源,到邻层后立刻原楼梯折返,拿完再上去:
        [i]   踩楼梯 F->G            (第一次上楼,漏拿)
        [i+1] 换层 ->G
        [i+2] 踩楼梯 G->F            (立刻折返 = 白跑)
        [i+3] 换层 ->F               (落回 [i] 的出发格)
        [i+4..j-1] F 层动作          (拿漏掉的资源)
        [j]   踩楼梯(同格同向) F->G  (再上去)
        [j+1] 换层 ->G
    例(本录像 MT8):上 9F 时漏拿 (3,4)(4,4)(5,4) 三把黄钥匙,到 9F 立刻折返
    下来拿(step 57 yk+3)再上去,bounce 4 步白跑。

    安全性(结构性,不靠肉眼):bounce 四步全程零效果(踩楼梯立即换层不触发
    auto/拾取,换层本身无效果),且 [i+3] 落格 == [i] 出发格(断言);故
    [i+4..j-1] 提升到 [i] 前执行时入参状态与起点完全相同,终态与顺序无关。
    提升后删 [i..i+3] 四步,保留 [j][j+1] 作唯一上楼(其 before 已与 [j-1]
    衔接)。折返段含任何 换层/飞行 或 40 步内找不到同楼梯折返则不提升。"""
    out: list = []
    i = 0
    n = len(steps)
    hoisted = 0
    while i < n:
        s = steps[i]
        if (i + 3 < n and _is_stair_pass(s) and steps[i + 1].get("action") == "换层"
                and _is_stair_pass(steps[i + 2]) and steps[i + 3].get("action") == "换层"):
            f1 = s.get("floor")
            g1 = steps[i + 1].get("floor")
            b1 = s.get("before") or {}
            a3 = steps[i + 3].get("after") or {}
            uturn = (g1 != f1 and steps[i + 2].get("floor") == g1
                     and steps[i + 3].get("floor") == f1
                     and (a3.get("x"), a3.get("y")) == (b1.get("x"), b1.get("y")))
            if uturn:
                j = i + 4
                found = -1
                while j < n and j < i + 40:
                    sj = steps[j]
                    if sj.get("action") in ("换层", "飞行"):
                        break
                    if (_is_stair_pass(sj) and sj.get("floor") == f1
                            and sj.get("pos") == s.get("pos") and sj.get("eid") == s.get("eid")):
                        found = j
                        break
                    j += 1
                if (found > 0 and found + 1 < n
                        and steps[found + 1].get("action") == "换层"
                        and steps[found + 1].get("floor") == g1):
                    mid = steps[i + 4:found]
                    b_mid = (mid[0].get("before") or {}) if mid else {}
                    if (mid and (b_mid.get("x"), b_mid.get("y")) == (b1.get("x"), b1.get("y"))
                            and all((st.get("before") or {}).get("floor") == f1
                                    and (st.get("after") or {}).get("floor") == f1
                                    for st in mid)):
                        out.extend(mid)
                        out.append(steps[found])
                        out.append(steps[found + 1])
                        i = found + 2
                        hoisted += 1
                        continue
        out.append(s)
        i += 1
    if hoisted:
        print(f"hoist stair U-turn: {hoisted} 处")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--route", required=True)
    ap.add_argument("--statlog", required=True)
    ap.add_argument("--save1", required=True)
    ap.add_argument("--paths", default="")
    ap.add_argument("--out", required=True)
    ap.add_argument("--report", default="")
    ap.add_argument("--stop-floor", default="MT21")
    ap.add_argument("--start-stat", type=int, default=55)
    ap.add_argument("--auto", default="battle=true,item=true,wall=true",
                    help="录像录制时的 auto 设置（回放沿用玩家 flags.__auto__；"
                         "未开过自动操作的录像 flags.__auto__ 为 null，应传 "
                         "battle=false,item=false,wall=false）")
    ap.add_argument("--residual-out", default="",
                    help="非空则导出 zone1-20 剩余资源扫描(final-score 0伤害口径)到该 JSON")
    args = ap.parse_args()

    route = load_route(Path(args.route))
    statlog = load_statlog(Path(args.statlog))
    SAVE1 = Path(args.save1)
    STOP = args.stop_floor
    paths = []
    if args.paths:
        paths = json.loads(Path(args.paths).read_text(encoding="utf-8"))

    FINAL_IDX = len(statlog) - 1  # last entry = FINAL (post-state of last action)

    # route -> non-choices stat index (choices don't call _doReplayAction -> no stat)
    route_stat: list[int | None] = [None] * len(route)
    si = 0
    for ri, a in enumerate(route):
        if not (isinstance(a, str) and a.startswith("choices")):
            route_stat[ri] = si
            si += 1
    # PRE-state: stat[si] = pre-state of action si. There are si non-choices actions
    # (0..si-1) + 1 FINAL = len(statlog). So si == len(statlog) - 1.
    assert si == FINAL_IDX, f"non-choices count {si} != FINAL_IDX {FINAL_IDX}"

    start_ri = next(ri for ri, s in enumerate(route_stat) if s == args.start_stat)
    start_si = args.start_stat

    # paths are captured for the FULL recording; skip move:x:y before start_ri.
    path_ptr = 0
    if paths:
        for ri2 in range(start_ri):
            if isinstance(route[ri2], str) and route[ri2].startswith("move:"):
                path_ptr += 1

    def _parse_auto(spec: str) -> dict:
        flags: dict = {}
        for part in spec.split(","):
            k, _, v = part.strip().partition("=")
            if not k:
                continue
            flags[k] = (v == "true") if v in ("true", "false") else v
        return flags

    auto_flags = _parse_auto(args.auto)
    g = Game(read_json(SAVE1))
    g.strict_live_model = True
    g.auto_flags = auto_flags  # 必须匹配录像录制时的 auto（flags.__auto__）
    g.set_segment(f"录像->Game 转换 (auto={args.auto})")

    mismatches: list[str] = []
    # 被剪枝的零效果 move 后续 si 集合:该段 hero 少了被剪位移,statlog pos 期望不可达,
    # drift_check 对这些 si 跳过 pos 校验(stat 仍校验;剪枝断言了 move 零效果 stat 不变,
    # 且 hero 在下一真实动作结束时与 statlog 重新对齐,否则 pos_diff 会重新出现)。
    skip_pos_si: set[int] = set()

    def drift_check(si_idx: int, label: str) -> None:
        if si_idx >= len(statlog):
            return
        if g.state["floor"] == STOP:
            return
        exp = statlog[si_idx]
        got = stats_of(g)
        fields = ["hp", "atk", "def", "yk", "bk", "rk", "g"]
        diffs = {f: (got[f], exp[f]) for f in fields if got[f] != exp[f]}
        floor_diff = g.state["floor"] != exp["f"] and g.state["floor"] != STOP
        pos_diff = ((g.state["x"], g.state["y"]) != (exp["x"], exp["y"])
                    and si_idx not in skip_pos_si)
        if diffs or floor_diff or pos_diff:
            mismatches.append(
                f"si={si_idx} [{label}] floor got={g.state['floor']} exp={exp['f']} "
                f"diffs={diffs} pos=({g.state['x']},{g.state['y']}) exp_pos=({exp['x']},{exp['y']})")

    def try_move(g: Game, fid: str, tx: int, ty: int, note: str) -> bool:
        old_errors = len(g.errors)
        try:
            go_to_decomposed(g, fid, tx, ty, note)
            return True
        except Exception:
            del g.errors[old_errors:]
            return False

    DX = {"up": 0, "down": 0, "left": -1, "right": 1}
    DY = {"up": -1, "down": 1, "left": 0, "right": 0}

    ri = start_ri
    while ri < len(route):
        a = route[ri]
        if not isinstance(a, str):
            ri += 1
            continue
        this_si = route_stat[ri]

        # ---- choices: group consecutive, delta-driven, no drift-check here
        # (the next non-choices' drift-check, or FINAL, covers the group) ----
        if a.startswith("choices"):
            j = ri
            while j < len(route) and isinstance(route[j], str) and (route[j].startswith("choices") or route[j] == "help"):
                j += 1
            next_si = route_stat[j] if (j < len(route) and route_stat[j] is not None) else FINAL_IDX
            after = statlog[next_si]
            hf = g.state["floor"]
            da = after["atk"] - g.state["atk"]
            dd = after["def"] - g.state["def"]
            dyk = after["yk"] - g.state["yk"]
            dbk = after["bk"] - g.state["bk"]
            drk = after["rk"] - g.state["rk"]
            dhp = after["hp"] - g.state["hp"]
            dg = after["g"] - g.state["gold"]
            label = f"choices {a} (group ri={ri}..{j-1} -> si={next_si})"
            ratio = g.floors[hf].ratio
            try:
                if da > 0:
                    shop_pos = adjacent_block(g, hf, eid="blueShop") or adjacent_block(g, hf, kind="npc")
                    g.buy_shop("atk", da // (2 * ratio), shop_pos=shop_pos)
                elif dd > 0:
                    shop_pos = adjacent_block(g, hf, eid="blueShop") or adjacent_block(g, hf, kind="npc")
                    g.buy_shop("def", dd // (4 * ratio), shop_pos=shop_pos)
                elif dg > 0:
                    # 纯金币奖励需走共享 Game 的已知 NPC 转换，不能把录像 statlog 的
                    # dg 直接写入状态：MT2 oldman 的真实固定奖励为 +1000G，录像帧会
                    # 漂成 +1008G。放 key 分支前以免 yk 假阳误走普通商人。
                    tpos = adjacent_block(g, hf, kind="npc")
                    if tpos and floor_no(hf) in g.TRADER_TABLE:
                        g.talk_trader(hf, tpos[0], tpos[1], label)
                    else:
                        mismatches.append(
                            f"ri={ri} {label} unknown gold-reward npc dg={dg} "
                            f"@ {hf} ({g.state['x']},{g.state['y']})"
                        )
                elif dyk > 0 or dbk > 0 or drk > 0:
                    tpos = adjacent_block(g, hf, kind="npc")
                    if tpos:
                        g.talk_trader(hf, tpos[0], tpos[1], label)
                    else:
                        mismatches.append(f"ri={ri} {label} trader delta dyk{dyk}/dbk{dbk}/drk{drk} but no adjacent npc @ {hf} ({g.state['x']},{g.state['y']})")
                elif dhp > 0:
                    shop_pos = adjacent_block(g, hf, eid="blueShop")
                    if shop_pos:
                        g.buy_shop("hp", 1, shop_pos=shop_pos)
                # else: no-op event dialog
            except RouteError as ex:
                mismatches.append(f"ri={ri} {label} RouteError: {ex}")
            ri = j
            continue

        # ---- non-choices action: drift-check BEFORE processing (g.state == stat[si]) ----
        if this_si is not None:
            drift_check(this_si, f"before {a}")

        if g.state["floor"] == STOP:
            break

        hf = g.state["floor"]

        if a.startswith("turn") or a == "help":
            ri += 1
            continue

        # ---- fly ----
        if a.startswith("fly"):
            target = a.split(":", 1)[1]
            try:
                g.fly(target)
            except RouteError as ex:
                mismatches.append(f"si={this_si} fly {target} RouteError: {ex}")
            ri += 1
            continue

        # ---- move:x:y: 内部 captured path 逐格精确复现录像路径 + auto_sweep(state
        # 对齐 statlog 0 mismatch),walk emit 时由 coalesce_node_level 合并成节点级
        # step(目标格),匹配 Game 类 go_to + replayer 节点级设计。逐格是内部 state
        # 计算,不是 walk 输出;纯 go_to 节点级会因事件格/门可达性差异 (MT15 (9,1)
        # thief 等) 丢失录像路径,273 mismatch,不可行。----
        if a.startswith("move:"):
            if paths and path_ptr < len(paths):
                path = paths[path_ptr]
                path_ptr += 1
                pf = path["floor"]
                psx, psy = path["sx"], path["sy"]
                cross = False
                if pf != hf:
                    # 录像的 fly 可能因录制帧时序“失败”：fly action 后 statlog 仍留在
                    # 源层，下一条 move 的 post-state 才显示目标层。Game/live fly 已经
                    # 正确落到目标层；这条 move 是延迟换层标记，不是目标层内的真实
                    # click。若把它再直达执行，会误清目标层资源（MT1->MT9 的
                    # move:7:11 额外拿 +28G/+1YK），从此所有资源账漂移。
                    # 只在录像下一帧恰好与当前 Game 楼层/落点一致时静默消费；其它
                    # path-floor 异常仍保守地按原逻辑直达，避免吞掉真实移动。
                    post = statlog[this_si + 1] if this_si + 1 < len(statlog) else None
                    if (post and post["f"] == hf
                            and (post["x"], post["y"]) == (g.state["x"], g.state["y"])):
                        ri += 1
                        continue
                    parts = a.split(":")
                    _tx, _ty = int(parts[1]), int(parts[2])
                    try_move(g, hf, _tx, _ty, f"move {a} direct {hf}")
                    drift_check(this_si, f"move {a} direct {hf}")
                    ri += 1
                    continue
                # 本 move 要踩的格:moveDirectly 首步(同层且未到位时)+ captured path。
                # 逐格精确复现录像路径(auto_sweep 在走门格首格 + 末格触发,对齐 statlog 0
                # mismatch);然后合并成本 move 的 ONE step at 末格,匹配 web automaticRoute
                # 一次点击末格、hero 走完整路径、auto 在走门格+末格触发、终态一致。
                # 不合并的话中间格会成独立 step,replayer 单独点中间格让 hero 停住触发
                # auto,但 walk 该格无 auto -> mismatch(如 MT8 move:6:4 的 6,3 走门格:
                # 6,2->6,3 1-tile 点击,live auto 在 6,3 拾 3 YK,walk step 期望 YK=0)。
                # 合并后 replayer 点末格 6,4,hero 6,2->6,3->6,4 一次走完,auto 在 6,3+6,4
                # 触发,终态 YK=3 匹配。drift_check 只查 g.state 不查 g.steps,合并安全。
                pre_move_pos = (g.state["x"], g.state["y"])
                pre_move_stats = stats_of(g)
                path_tiles = [(s["x"], s["y"]) for s in path.get("path", [])]
                move_tiles: list[tuple[int, int]] = []
                if not path_tiles:
                    # path 空 = moveDirectly 直达(传送/寻路):hero 到 route 目标,不是
                    # paths sx,sy 起点(move:1:10 paths sx=9,sy=11 但目标 (1,10);step
                    # (9,11) 会少走到 (1,10),后续 step 237 (1,9) 不邻 -> replayer 卡)。
                    parts = a.split(":")
                    move_tiles = [(int(parts[1]), int(parts[2]))]
                elif not cross and pre_move_pos != (psx, psy):
                    if pre_move_pos in path_tiles:
                        # 前序零效果 move 被剪枝(见下方 prune),hero 在 captured path
                        # 中间格:从后缀继续即可。被剪掉的前缀已证明零效果,不重走。
                        path_tiles = path_tiles[path_tiles.index(pre_move_pos) + 1:]
                    else:
                        move_tiles.append((psx, psy))
                    move_tiles.extend(path_tiles)
                else:
                    move_tiles.extend(path_tiles)
                prev = g.steps[-1] if g.steps else None
                first_tile = move_tiles[0] if move_tiles else None
                first_is_door = bool(first_tile and prev and prev.get("action") == "开门"
                                     and tuple(prev.get("pos") or []) == first_tile)
                last_idx = len(move_tiles) - 1
                # move:x:y 末格 noPass 门（未开、block 仍在）不会被 moveDirectly
                # 自动开启；英雄停在门前，门后资源也不会被 auto_sweep。后续 arrow
                # open_door_stay 或路径内开门才会处理。该规则以已验证的实机 Game
                # click 模型为准，不能按有已知帧漂移的录像 statlog 改写。
                if move_tiles:
                    last_blk = g.block_at(hf, move_tiles[-1])
                    if last_blk and last_blk.kind == "door":
                        move_tiles.pop()
                        last_idx = len(move_tiles) - 1
                steps_before = len(g.steps)
                move_ok = True
                for idx, (sx, sy) in enumerate(move_tiles):
                    # 走门格(被清开的门格)中间格也触发 auto(匹配 web core.plugin.auto
                    # 在走门格触发并拾可达资源,如 MT17 (2,4) specialDoor 走门格拾 (2,2)
                    # sword2)。仅末格/首格 first_is_door 触发会漏中间走门格 -> web mismatch。
                    is_former_door = (sx, sy) in g._former_doors.get(hf, ())
                    run_auto = (idx == last_idx) or (idx == 0 and first_is_door) or is_former_door
                    if not try_step_path(g, hf, sx, sy, f"move {a} step {sx},{sy}", run_auto=run_auto):
                        mismatches.append(f"si={this_si} {a} step ({sx},{sy}) failed @ {hf} ({g.state['x']},{g.state['y']})")
                        move_ok = False
                        break
                # path 末格若触发换层(踩楼梯/fly 道具/事件),statlog 下个 non-choices
                # 楼层会变。move:x:y 的 path 逐格走不换层(apply_block terrain 只 record
                # "通过"),需补 transition 到 statlog 楼层+位置。不限于 upFloor/downFloor:
                # MT1 无楼梯,move:7:11 踩 fly 道具区触发 fly 换层到 MT9 (6,2),path 末格
                # (7,11) 是空地,靠 g.steps[-1].eid 判不出。统一用 statlog 楼层判断最可靠。
                if move_ok:
                    ns_si = None
                    for rj in range(ri + 1, len(route)):
                        ns = route_stat[rj]
                        if ns is not None:
                            ns_si = ns
                            break
                    post = statlog[ns_si] if ns_si is not None and ns_si < len(statlog) else None
                    if post and post["f"] != hf:
                        try:
                            g.transition(post["f"], f"move {a} {hf}->{post['f']}",
                                         landing=(post["x"], post["y"]))
                            hf = post["f"]
                        except RouteError as ex:
                            mismatches.append(f"si={this_si} {a} transition {hf}->{post['f']} RouteError: {ex}")
                # 按中断点(trigger-event)分段合并:web automaticRoute 中途踩事件
                # trigger 格会中断寻路(MT15 (9,1) thief 触发开 (8,1)),replayer 须
                # 分步点(先点到 trigger 格触发,再点到末格)。trigger 格作为前段末格
                # 保留;整段无 trigger 则 ONE step at 末格(auto 在走门格 former-door /
                # 末格触发,由 _merge_move_segment 收集进 note,匹配 web automaticRoute
                # 一次点击末格、hero 走完整路径、auto 在 former-door+末格触发、终态一致)。
                # 不在 former-door(走门格)切断:录像 statlog 证明 hero 一次性到达目标,
                # web auto 不中断;切断会凭空造出"走门格+走到目标"冗余(用户反馈)。
                move_steps = g.steps[steps_before:]
                if move_ok and move_steps:
                    # 换层(transition)step 独立保留:reloader CHANGE_FLOOR 不点击只等
                    # (live_zone3_mouse_replayer_cdp.js CHANGE_FLOOR return),靠前一步 PASS
                    # 末格(fly 道具/楼梯)点击触发换层。合并进 move 会丢 trigger:move:7:11
                    # 踩 fly 道具换层合并成 CHANGE_FLOOR [6,2] landing,reloader 不点击只等
                    # hero 到 MT9 -> timeout。拆出后 non_trans merge 成 PASS 末格 (7,11)
                    # (replayer 点 (7,11) fly 道具触发 fly 换层) + trans CHANGE_FLOOR (6,2)。
                    trans = [s for s in move_steps if s.get("action") == "换层"]
                    non_trans = [s for s in move_steps if s.get("action") != "换层"]
                    del g.steps[steps_before:]
                    if non_trans:
                        # breaks 含击杀(非 0 伤 battle):reloader 点合并目标,hero
                        # automaticRoute 寻路遇怪(非 0 伤)不杀,卡。击杀独立 step
                        # (reloader 点怪杀)+ pass 目标。3攻5防 MT9 move:2:7 含 (1,8)
                        # 骷髅 battle 合并致 hero (1,10) 卡 (2,7)。
                        breaks = [i for i, p in enumerate(non_trans)
                                  if _has_trigger(p.get("note") or "")
                                  or p.get("action") == "击杀"]
                        if breaks:
                            segments: list = []
                            start = 0
                            for b in breaks:
                                segments.append(non_trans[start:b + 1])
                                start = b + 1
                            if start < len(non_trans):
                                segments.append(non_trans[start:])
                            for seg in segments:
                                g.steps.append(_merge_move_segment(seg, a) if len(seg) > 1 else dict(seg[0]))
                        elif len(non_trans) > 1:
                            g.steps.append(_merge_move_segment(non_trans, a))
                        else:
                            g.steps.append(dict(non_trans[0]))
                    g.steps.extend(trans)
                # ---- 零效果 move 剪枝(录像多余动作,用户反馈) ----
                # 录像里玩家偶发点了零效果 waypoint(无 auto/trigger、stat 不变):
                # (a) 紧接 fly:fly 位置无关(任意格起飞到达相同),waypoint 纯多余;
                #     例 MT6 move:3:8 (2,9)->(3,8) 后 fly MT3。
                # (b) 紧接 move 且 hero 剪枝后停留格(pre_move_pos)在下一 move 的
                #     captured path 上:下一 move 从路径后缀重放即等价,waypoint 纯多余;
                #     例 MT4 move:9:1 (10,3)->(9,1) 死胡同,下一 move:11:10 路径过
                #     (10,3)(index 2),从后缀 22 格重放。安全性由 captured path 佐证,
                #     不靠肉眼:pre_move_pos 不在路径上则不剪。
                # move 与下一真实动作之间常有 no-op 箭头(turn 转身/面墙误触,statlog
                # 前后 pos+stat 全同,如 move:9:1 -> right -> move:11:10);剪枝时一并
                # 跳过(ri=j2-1),否则从剪枝位置重放这些箭头会错误位移。
                # 剪枝 = 恢复 hero 到 pre_move_pos + 删掉本 move 的 emitted steps。
                # 下一真实动作的 statlog pos 期望不可达(少了这段位移),其 si 记入
                # skip_pos_si,drift_check 跳过 pos 校验(stat 仍校验);hero 在下一
                # 动作结束时与 statlog 重新对齐,否则 pos_diff 会重新报出。
                if move_ok and not cross:
                    post_stats = stats_of(g)
                    zero_effect = all(post_stats[k] == pre_move_stats[k] for k in
                                      ("hp", "atk", "def", "yk", "bk", "rk", "g"))
                    emitted = g.steps[steps_before:]
                    if (zero_effect and emitted
                            and not any(_note_has_auto(s.get("note") or "")
                                        or _has_trigger(s.get("note") or "")
                                        for s in emitted)):
                        j2 = ri + 1
                        while j2 < len(route):
                            t = route[j2]
                            if not isinstance(t, str):
                                break
                            si_t = route_stat[j2]
                            if (si_t is not None and si_t + 1 < len(statlog)
                                    and (t.startswith("turn") or t == "help"
                                         or t in ("up", "down", "left", "right"))
                                    and _statlog_noop(statlog[si_t], statlog[si_t + 1])):
                                # 数值/坐标不变不代表没有地图副作用：例如 MT2 x10y11
                                # 小偷事件由 right 触发，录像帧仍停 x10y11。事件 arrow
                                # 不可跟着前序零效果 move 一并剪掉，否则 MT35 x4y9 墙不移除。
                                pre_t = statlog[si_t]
                                if t in DX:
                                    event_pos = (pre_t["x"] + DX[t], pre_t["y"] + DY[t])
                                    if f"{event_pos[0]},{event_pos[1]}" in g.floors[hf].events:
                                        break
                                j2 += 1
                                continue
                            break
                        nxt = route[j2] if j2 < len(route) else None
                        prune = False
                        if isinstance(nxt, str) and nxt.startswith("fly"):
                            prune = True
                        elif (isinstance(nxt, str) and nxt.startswith("move:")
                                and path_ptr < len(paths)):
                            npath = paths[path_ptr]  # 本 move 已消费自身 entry,这是下一 move 的
                            if npath.get("floor") == hf:
                                ntiles = [(s["x"], s["y"]) for s in npath.get("path", [])]
                                prune = pre_move_pos in ntiles
                        if prune:
                            g.state["x"], g.state["y"] = pre_move_pos
                            del g.steps[steps_before:]
                            nsi = route_stat[j2] if j2 < len(route) else None
                            if nsi is not None:
                                for si_ in range(this_si + 1, nsi + 1):
                                    skip_pos_si.add(si_)
                            print(f"prune zero-effect move si={this_si} {a} @ {hf} "
                                  f"({pre_move_pos[0]},{pre_move_pos[1]}) next={nxt}")
                            ri = j2 - 1  # 尾部 ri+=1 落在 j2:no-op 箭头一并跳过
            else:
                parts = a.split(":")
                tx, ty = int(parts[1]), int(parts[2])
                if not try_move(g, hf, tx, ty, f"move {a}"):
                    mismatches.append(f"si={this_si} {a} unreachable @ {hf} ({g.state['x']},{g.state['y']})")
            ri += 1
            continue

        # ---- arrow step: content-driven (target tile decides action) ----
        if a in ("up", "down", "left", "right"):
            tx, ty = g.state["x"] + DX[a], g.state["y"] + DY[a]
            # statlog 判断 arrow 是否纯转身(no-op):h5mota arrow=turn-then-move,目标不可走
            # 时只转身不移动。纯转身 = pos 不变 + stat(hp/yk/bk/rk/g) 全不变。若 stat 变了
            # (door_stay 开门 yk-1 / trigger spawn hp 变 / 战斗),不是转身,走下面的正常
            # block 分支处理。不需要 facing 建模:statlog 全字段即可区分转身 vs door_stay。
            # 之前只查 pos 会把 door_stay 误判转身漏开门(si=57 up door_stay yk4->3 漏,
            # 连锁 yk 多 1 到 MT32 误判 trader)。
            nxt_arr = statlog[this_si + 1] if this_si is not None and this_si + 1 < len(statlog) else None
            # break_wall_stay (arrow at fakeWall/fakeWall2: 破墙 + hero 停邻格) 改 pos
            # 也不改 stat -> 会被上面的"pos+stat 全不变"误判转身跳过,漏破墙+漏 spawn
            # 道具(如 MT19 (6,3) cross: si652 up 破 fakeWall2 spawn cross 被跳过 -> si653
            # 踩上时 cross 生成时机错 -> cross 没拿到 -> MT20 vampire 无 cross 爆伤)。
            # 故目标若是可破墙(fakeWall/fakeWall2),即使 pos+stat 不变也不当转身跳过。
            _tgt_blk = g.block_at(hf, (tx, ty))
            _tgt_breakable = bool(_tgt_blk and _tgt_blk.kind == "terrain"
                                  and _tgt_blk.eid in {"fakeWall", "fakeWall2"})
            if (nxt_arr and nxt_arr["f"] == hf
                    and (nxt_arr["x"], nxt_arr["y"]) == (g.state["x"], g.state["y"])
                    and nxt_arr["yk"] == g.state["yk"]
                    and nxt_arr["bk"] == g.state["bk"]
                    and nxt_arr["rk"] == g.state["rk"]
                    and nxt_arr["hp"] == g.state["hp"]
                    and nxt_arr["g"] == g.state["gold"]
                    and not _tgt_breakable):
                ri += 1
                continue
            f = g.floors[hf]
            if tx < 0 or ty < 0 or tx >= f.width or ty >= f.height:
                pass  # out of bounds: no-op (shouldn't happen in valid route)
            else:
                blk = g.block_at(hf, (tx, ty))
                if blk is None:
                    # empty ground: move onto
                    if not try_step_path(g, hf, tx, ty, f"step {a}->{tx},{ty}"):
                        mismatches.append(f"si={this_si} step {a} -> ({tx},{ty}) empty failed @ {hf} ({g.state['x']},{g.state['y']})")
                elif blk.kind == "door":
                    # arrow into door = open + STAY (door_stay)
                    if not open_door_stay(g, hf, tx, ty, f"step {a} 开门 {tx},{ty}"):
                        mismatches.append(f"si={this_si} step {a} door_stay -> ({tx},{ty}) not a door @ {hf} ({g.state['x']},{g.state['y']})")
                elif blk.kind == "enemy":
                    if not try_step_path(g, hf, tx, ty, f"step {a} battle {tx},{ty}"):
                        mismatches.append(f"si={this_si} step {a} battle -> ({tx},{ty}) failed @ {hf} ({g.state['x']},{g.state['y']})")
                elif blk.kind == "item":
                    if not try_step_path(g, hf, tx, ty, f"step {a} take {tx},{ty}", is_arrow=True):
                        mismatches.append(f"si={this_si} step {a} take -> ({tx},{ty}) failed @ {hf} ({g.state['x']},{g.state['y']})")
                elif blk.kind == "npc":
                    # 箭头面向 NPC 会在相邻格触发 NPC/event，而非移动到 NPC 格。
                    # 如 MT2 (10,11) 小偷对话会开 MT35 (4,9) 通道；库存可完全不变，
                    # 但不能当作 no-op 丢弃。
                    before_npc = g.snapshot()
                    g.record("事件", (tx, ty), blk.eid, before_npc, f"step {a} NPC {tx},{ty}")
                    if g.trigger_tile_event(hf, (tx, ty)):
                        g.steps[-1]["note"] += "; trigger-event"
                elif blk.kind == "terrain":
                    if blk.eid in ("upFloor", "downFloor"):
                        # stair: 踩楼梯换层。replayer 期望 PASS 楼梯格(eid=
                        # upFloor,点击触发换层) + CHANGE_FLOOR(no-op coalesce)。
                        # transition() 只生成 CHANGE_FLOOR,缺 PASS 楼梯可点击目标
                        # -> replayer CHANGE_FLOOR no-op 时 hero 没踩楼梯,卡住。
                        # 故先手动 record PASS 楼梯(移位,不 apply_block 不
                        # auto_sweep,匹配 web 踩楼梯立即换层不 BFS 拾取),再 transition。
                        post = statlog[this_si + 1] if this_si is not None and this_si + 1 < len(statlog) else None
                        if post and post["f"] != hf:
                            before_stair = g.snapshot()
                            g.state["x"], g.state["y"] = tx, ty
                            g.record("通过", (tx, ty), blk.eid, before_stair, f"step {a} 踩楼梯 {tx},{ty}")
                            try:
                                g.transition(post["f"], f"step {a} stair {hf}->{post['f']}")
                            except RouteError as ex:
                                mismatches.append(f"si={this_si} step {a} stair transition {hf}->{post['f']} RouteError: {ex}")
                        else:
                            try_step_path(g, hf, tx, ty, f"step {a} terrain {tx},{ty}")
                    elif blk.eid == "fakeWall2":
                        # arrow 到 fakeWall2:hero 踩上 vs stay 由 statlog[next] pos 决定。
                        # auto ON:破墙 spawn item(如 MT19 cross)lock tile,hero stay 相邻
                        # (break_wall_stay,2攻0def);auto OFF:破墙 hero 踩上(try_step_path,
                        # 3atk si=832 up (6,4)->(6,3) pos=(6,3))。统一踩上会破 2攻0def(838
                        # mismatch),统一 stay 会破 3atk(144 mismatch)。statlog[next] pos==
                        # 目标格 = 踩上,pos 不变 = stay。
                        nxt = statlog[this_si + 1] if this_si is not None and this_si + 1 < len(statlog) else None
                        if nxt is not None and (nxt["x"], nxt["y"]) == (tx, ty):
                            if not try_step_path(g, hf, tx, ty, f"step {a} 破暗墙 {tx},{ty}"):
                                mismatches.append(f"si={this_si} step {a} break -> ({tx},{ty}) failed @ {hf} ({g.state['x']},{g.state['y']})")
                        else:
                            if not break_wall_stay(g, hf, tx, ty, f"step {a} 破暗墙 {tx},{ty}"):
                                mismatches.append(f"si={this_si} step {a} break -> ({tx},{ty}) failed @ {hf} ({g.state['x']},{g.state['y']})")
                    elif blk.eid in ("fakeWall", "flower"):
                        if not try_step_path(g, hf, tx, ty, f"step {a} break {tx},{ty}"):
                            mismatches.append(f"si={this_si} step {a} break -> ({tx},{ty}) failed @ {hf} ({g.state['x']},{g.state['y']})")
                    else:
                        pass  # wall: no-op
                else:
                    pass  # unknown: no-op
            # 少数楼梯在离线静态 map 中被录成地面（例如 MT38 -> MT39），但录像的
            # PRE-state 明确显示本次 arrow 后已换层。已识别 terrain stair 的分支会
            # 在上面先 transition；这里只补“动作后仍在原层”的通用兜底，保留前面的
            # PASS 点击步，并以录像的真实落点建立 visited/fly 可达性。
            if nxt_arr and nxt_arr["f"] != hf and g.state["floor"] == hf:
                try:
                    g.transition(nxt_arr["f"], f"step {a} inferred stair {hf}->{nxt_arr['f']}",
                                 landing=(nxt_arr["x"], nxt_arr["y"]))
                except RouteError as ex:
                    mismatches.append(
                        f"si={this_si} step {a} inferred stair transition "
                        f"{hf}->{nxt_arr['f']} RouteError: {ex}"
                    )
            ri += 1
            continue

        # unknown token
        ri += 1

    # ---- FINAL drift-check (post-state of last action) ----
    drift_check(FINAL_IDX, "FINAL")

    exp_final = statlog[FINAL_IDX]
    print(f"ok={not g.errors and not mismatches}  mismatches={len(mismatches)}  errors={len(g.errors)}")
    print(f"final={state_line(g.state)} {g.state['floor']} x{g.state['x']}y{g.state['y']} "
          f"dmg={g.state['dmg']} door={g.state['yd']}/{g.state['bd']}/{g.state['rd']} times1={g.state['times1']}")
    print(f"exp  HP={exp_final['hp']} ATK={exp_final['atk']} DEF={exp_final['def']} "
          f"YK={exp_final['yk']} BK={exp_final['bk']} RK={exp_final['rk']} G={exp_final['g']} @{exp_final['f']}")
    if mismatches:
        print("\n--- first 40 mismatches ---")
        for m in mismatches[:40]:
            print(m)
    if g.errors:
        print("\n--- first 20 errors ---")
        for e in g.errors[:20]:
            print("ERR", e)

    final_steps = _hoist_stair_uturn(coalesce_node_level(g.steps))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"ok": not g.errors and not mismatches, "final": g.snapshot(),
                               "steps": final_steps, "errors": g.errors,
                               "mismatches": mismatches}, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.report:
        rp = Path(args.report)
        rp.parent.mkdir(parents=True, exist_ok=True)
        rep = [f"ok={not g.errors and not mismatches} mismatches={len(mismatches)} errors={len(g.errors)}",
               f"final={state_line(g.state)} {g.state['floor']}"]
        rep += mismatches
        rep += ["--- errors ---"] + [str(e) for e in g.errors]
        rp.write_text("\n".join(rep), encoding="utf-8")
    print(f"\njson={out}")
    if args.residual_out:
        rtotal, rrows, cats = scan_residual(g)
        s = g.state
        stock = s["hp"] + s["yk"] * 100 + s["bk"] * 500 + s["gold"] * 1.0
        cat_summary = {
            "剩余YK道具": len(cats["yellowKey"]),
            "剩余BK道具": len(cats["blueKey"]),
            "剩余红药": len(cats["redPotion"]),
            "剩余蓝药": len(cats["bluePotion"]),
            "剩余红钥匙": len(cats["redKey"]),
            "剩余红宝石": len(cats["redGem"]),
            "剩余蓝宝石": len(cats["blueGem"]),
            "未开黄门": len(cats["yellowDoor"]),
            "未开蓝门": len(cats["blueDoor"]),
            "未开红门": len(cats["redDoor"]),
            "0伤怪数量": len(cats["monster_gold"]),
            "0伤怪金币总money": sum(int(r.rsplit("+", 1)[-1]) for r in cats["monster_gold"]),
        }
        Path(args.residual_out).write_text(json.dumps({
            "final_state": g.snapshot(),
            "current_stock": {"hp": s["hp"], "yk": s["yk"], "bk": s["bk"], "rk": s["rk"], "gold": s["gold"]},
            "stock": stock,
            "residual_value": rtotal,
            "final_score": stock + rtotal,
            "cat_summary": cat_summary,
            "cats": cats,
            "residual_breakdown": rrows,
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"residual={rtotal} stock={stock} final-score={stock+rtotal} -> {args.residual_out}")
    return 0 if not g.errors and not mismatches else 1


if __name__ == "__main__":
    raise SystemExit(main())
