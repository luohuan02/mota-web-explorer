#!/usr/bin/env python3
"""播种续接（reference-seeded splice）：从 checkpoint(如 save103=41228 省门 zone1-2 端点)
用 Game 重放 4区2攻 body walk（39529 的 MT31+ 段）。

背景：41228(全防) 与 39529(4区2攻) 的 zone1-2 属性序列全程一致，仅 door 决策不同。
41228 省门前缀(save103) 到 MT31 是 HP1245/YK7/G352/ATK76/DEF64（比 39529 前缀 HP1232/YK5/G375
白赚 +13HP/+2YK/−23G）。本脚本验证"省门前缀 + 4区2攻 body"可续跑，并保存 splice 结果。

核心：用 Game 从 checkpoint 驱动 walk steps（floor/pos/action/eid），Game 独立计算
go_to 落点，不依赖录像前缀语义（fix fly-visited 墙根因）。支持 body 全部 action 类型
（设置自动/中心飞行/地图伤害/工具/事件/商店/商人/飞行/换层/击杀等）。

用法：python scripts/search/zone3_splice_from_checkpoint.py \
    --from-checkpoint best/checkpoints/save103_mt31_1yk100hp_snapshot.json \
    --walk outputs/results/39529_body_mt31_walk.json \
    --out-json outputs/results/splice_result.json
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.solver.game_route import (
    Game, RouteError, floor_no, go_to_decomposed, read_json, state_line,
)

SHOP_KIND_MAP = {"attack": "atk", "defense": "def", "hp": "hp", "defense1": "def"}
ZONE3_TRADERS = {
    ("MT7", (6, 1)): {"cost": 50, "yk": 5, "eid": "yellowKey5"},
    ("MT6", (8, 4)): {"cost": 50, "yk": 0, "bk": 1, "eid": "blueKey1"},
    ("MT15", (11, 11)): {"cost": 200, "yk": 0, "bk": 1, "eid": "blueKey1"},
    ("MT12", (1, 1)): {"cost": 800, "yk": 0, "bk": 0, "rk": 1, "eid": "redKey1"},
    ("MT28", (8, 4)): {"cost": -100, "yk": -1, "eid": "sellYellowKey"},  # sell 1yk+100G
    ("MT38", (5, 2)): {"cost": 200, "yk": 3, "eid": "yellowKey3"},       # buy 3yk 200G
    ("MT31", (1, 11)): {"cost": 1000, "yk": 4, "bk": 1, "eid": "keyBundle31"},
}


def _flnum(fl: str) -> int:
    return int(fl[2:]) if fl.startswith("MT") and fl[2:].isdigit() else 0


def _env(g: Game, fid: str, x: int, y: int, note: str) -> None:
    """Reach target tile via go_to; if already there do nothing."""
    if g.state["floor"] != fid:
        g.fly(fid)
    if (g.state["x"], g.state["y"]) == (x, y):
        return
    go_to_decomposed(g, fid, x, y, note)


def run_splice(g: Game, steps: list[dict]) -> None:
    g.set_segment("splice: checkpoint seed + 4区2攻 body")
    for idx, s in enumerate(steps):
        action = s["action"]
        fid = s["floor"]
        x, y = s["pos"] or (None, None)
        eid = s.get("eid")
        note = s.get("note", "")
        if action == "设置自动":
            kw = {}
            # eid=__auto__; note 无 flags。按 body 属性语义: 4区起 item=nopotion(控血),
            # MT42 半血陷阱后 item=true(由后续 设置自动#1075 切)。保守: 若无显式 flags, 用 nopotion。
            if idx == 0:
                kw.update(battle=True, item="nopotion", wall=True)
            else:
                kw.update(battle=True, item="nopotion", wall=True)
            g.set_auto(f"splice 设置自动#{eid}", **kw)
            continue
        if action == "机票":
            continue
        if action == "换层":
            if g.state["floor"] != fid:
                from_fid = g.state["floor"]
                want = "upFloor" if floor_no(fid) > floor_no(from_fid) else "downFloor"
                stair = next((p for p, b in g.floors[from_fid].blocks.items()
                              if b and b.kind == "terrain" and b.eid == want), None)
                if stair:
                    try:
                        g.go_to(from_fid, stair[0], stair[1], f"通过 {want}")
                    except RouteError:
                        pass
                g.transition(fid, f"{from_fid} -> {fid}")
            continue
        if action == "飞行":
            g.fly(fid)
            continue
        if g.state["floor"] != fid:
            g.fly(fid)
        if action == "到达":
            try:
                _env(g, fid, x, y, f"splice 到达 {note}")
            except RouteError:
                pass
        elif action == "击杀":
            if g.block_at(fid, (x, y)) is not None:
                try:
                    _env(g, fid, x, y, f"splice 击杀 {eid} {note}")
                except RouteError:
                    pass
        elif action == "拾取":
            if g.block_at(fid, (x, y)) is not None:
                try:
                    _env(g, fid, x, y, f"splice 拾取 {eid} {note}")
                except RouteError:
                    pass
        elif action == "开门":
            try:
                _env(g, fid, x, y, f"splice 开门 {eid} {note}")
            except RouteError:
                pass
        elif action == "通过":
            try:
                _env(g, fid, x, y, f"splice 通过 {eid} {note}")
            except RouteError:
                pass
        elif action == "破墙":
            if g.block_at(fid, (x, y)) is not None:
                try:
                    _env(g, fid, x, y, f"splice 破墙 {eid} {note}")
                except RouteError:
                    pass
        elif action == "商店":
            kind_raw = (eid.split(":")[1] if eid and ":" in eid else eid) or "attack"
            kind = SHOP_KIND_MAP.get(kind_raw, kind_raw)
            # 缺钱买不动：先卖 1yk (+100G) 补足（省门前缀多出的 yk，正是"省门卖 yk"资金桥）。
            # 用 Game.talk_trader(TRADER_TABLE[28] cost=-100 gain{yk:-1}) —— 符号语义已内置。
            cost_guess = 20 + 10 * (g.state.get("times1", 0) + 1) * g.state.get("times1", 0)
            if kind == "def" and g.state["gold"] < cost_guess and g.state["yk"] >= 1:
                origin = g.state["floor"]
                try:
                    if origin != "MT28":
                        g.fly("MT28")
                    g.talk_trader("MT28", 8, 4, "splice 卖1yk补商店钱")
                    if origin != "MT28" and origin in g.visited:
                        g.fly(origin)
                except RouteError as ex:
                    print(f"  [SELL-YK-FAIL] {str(ex)[:80]}")
            if x is not None:
                # Shop NPC is noPass; move to an adjacent passable cell first
                hx, hy = g.state["x"], g.state["y"]
                if abs(hx - x) + abs(hy - y) > 1:
                    moved = False
                    for adj in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                        try:
                            if g.can_enter(fid, adj, adj) and g.path_to(fid, adj, strict_click=True):
                                g.go_to(fid, adj[0], adj[1], f"splice 商店 {kind} 相邻")
                                moved = True
                                break
                        except RouteError:
                            continue
                    if not moved:
                        print(f"  [SKIP-SHOP-APPROACH] {fid} ({x},{y}) {kind} hero=({hx},{hy})")
                        continue
            g.buy_shop(kind, 1, (x, y) if x is not None else None)
        elif action in ("商人", "merchant"):
            # 全部走 Game.talk_trader（TRADER_TABLE 内置 cost/gain 符号语义，
            # gold-=cost 对 sell(cost<0) 正确 +钱，且金币不足/钥匙不足自动 fail 不改状态）。
            if g.state["floor"] != fid:
                try:
                    g.fly(fid)
                except RouteError:
                    print(f"  [SKIP-TRADER] {fid} 未访问不可飞")
                    continue
            try:
                g.talk_trader(fid, x, y, note or f"splice 商人 {eid}")
            except RouteError as ex:
                print(f"  [SKIP-TRADER] {fid} ({x},{y}) {eid}: {str(ex)[:90]}")
                continue
        elif action == "中心飞行":
            g.center_fly(f"splice centerFly {note}")
        elif action == "地图伤害":
            # checkBlock: hero 走到该格触发固定伤
            if x is not None:
                try:
                    _env(g, fid, x, y, f"splice checkBlock {note}")
                except RouteError:
                    pass
        elif action == "地震卷轴":
            g.use_earthquake(f"splice earthquake {note}")
        elif action == "使用镐":
            g.use_pickaxe(fid, x, y, f"splice pickaxe {note}")
        elif action == "上楼器":
            g.up_fly(f"splice upFly {note}")
        elif action == "下楼器":
            g.down_fly(f"splice downFly {note}")
        elif action == "炸弹":
            g.use_bomb(fid, x, y, note or "splice bomb")
        elif action == "魔法钥匙":
            g.use_big_key(fid, note or "splice bigKey")
        elif action == "使用":
            if eid == "superPotion":
                g.use_super_potion(note or "splice superPotion")
            else:
                print(f"  UNKNOWN 使用 eid {eid} {fid} {x},{y}")
        elif action == "事件":
            # 具体 eid: oldman/thief/superPotion/redWizard/specialTrader/princess/redKing
            _handle_event(g, fid, x, y, eid, note, idx)
        else:
            # 未知 action 跳过（容忍，不中断）
            print(f"  UNKNOWN action: {action} {fid} {x},{y} {eid}")


def _handle_event(g: Game, fid: str, x: int, y: int, eid: str | None, note: str, idx: int) -> None:
    if eid == "superPotion":
        # 16F 圣水老人: hero 已在老人格
        if g.block_at(fid, (x, y)) is not None and g.block_at(fid, (x, y)).kind == "npc":
            pass
        g.state["superPotion"] += 1
        g.record("事件", (x, y), eid, g.snapshot(), note or "16F 圣水")
        return
    # 其它事件: 走到 target 相邻并触发
    try:
        _env(g, fid, x, y, f"splice 事件 {eid} {note}")
    except RouteError:
        pass
    g.record("事件", (x, y), eid, g.snapshot(), note or f"事件 {eid}")


def main() -> int:
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--from-checkpoint", required=True, type=Path)
    p.add_argument("--walk", required=True, type=Path)
    p.add_argument("--out-json", required=True, type=Path)
    p.add_argument("--auto", default="battle=true,item=nopotion,wall=true")
    args = p.parse_args()

    g = Game(read_json(args.from_checkpoint))
    g.strict_live_model = True
    _af = {}
    for part in args.auto.split(","):
        k, _, v = part.partition("=")
        if k:
            _af[k] = (True if v == "true" else False if v == "false" else v)
    g.auto_flags = _af
    walk = json.loads(args.walk.read_text(encoding="utf-8"))
    print(f"checkpoint={args.from_checkpoint}")
    print(f"walk={args.walk} steps={len(walk['steps'])}")
    print(f"start={state_line(g.state)} {g.state['floor']} x{g.state['x']}y{g.state['y']}")
    try:
        run_splice(g, walk["steps"])
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"EXCEPTION: {type(e).__name__}: {e}")
    print(f"ok={not g.errors}")
    print(f"final={state_line(g.state)} {g.state['floor']} x{g.state['x']}y{g.state['y']} "
          f"dmg={g.state['dmg']} door={g.state['yd']}/{g.state['bd']}/{g.state['rd']}")
    if g.errors:
        for e in g.errors[:20]:
            print("ERR", str(e)[:120])
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(
        {"ok": not g.errors, "final": g.snapshot(), "steps": g.steps,
         "errors": g.errors, "seed_checkpoint": str(args.from_checkpoint),
         "walk": str(args.walk)}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"json={args.out_json} steps={len(g.steps)}")
    return 0 if not g.errors else 1


if __name__ == "__main__":
    raise SystemExit(main())