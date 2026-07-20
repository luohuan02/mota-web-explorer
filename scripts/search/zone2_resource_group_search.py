#!/usr/bin/env python3
"""P2：zone2 资源骨架搜索（GameAStar + 可达矩阵）。

目标：从 save100(zone1 end)+补给 起，搜出 2 攻线核心动作序列
(MT11/12 清路 -> MT12 blueShop 买 2 atk)，非手写 scaffold。

ground truth (best/zone2_2atk1def_branch_walk_source.md best_after 段)：
  MT11 x10y9 bat -> MT12 x8y11 bat ->
  MT12 x7y10/x5y10 redPotion(+200) -> MT12(6,9) blueShop buy atk x2 ...

关键：到 (6,9) 前必须先清挡路 bat(8,11)（path_to 不穿活怪），
故搜索需序列化 清怪 -> 拾瓶 -> 买属性。

性能：skeleton_actions 只 flood 当前楼层（_flood_floor），不 flood 全部已访问层；
heuristic O(1) 只看 times1 + 楼层距离。
"""
from __future__ import annotations

import os, sys, json, time
from pathlib import Path
from typing import Iterable

ROOT = Path("D:/claude/mota-web-explorer")
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from src.solver.game_route import Game, RouteError, go_to_decomposed, read_json, state_line, STAIRS, floor_no
from src.solver.game_astar import GameAStar, GameAction
from src.solver.reachability_matrix import compute_matrix, _flood_floor
from scripts.search.zone2_game_route import apply_mt10_supply

SAVE100 = ROOT / "best" / "checkpoints" / "zone1_end_save.json"
MT12_BLUESHOP = (6, 9)  # blueShop stat 商店（矩阵确认）

_T0 = 0.0
_N = {"n": 0}


def _floor_n(fid: str) -> int:
    return int(fid[2:]) if fid.startswith("MT") else 0


def _diag_matrix(game: Game) -> None:
    rm = compute_matrix(game)
    cur = game.state["floor"]
    print(f"[diag] floor={cur} {state_line(game.state)} x{game.state['x']}y{game.state['y']}")
    cf = rm.floors.get(cur)
    if not cf:
        print(f"[diag] {cur} not in matrix")
        return
    print(f"[diag] {cur} reached={len(cf.reachable_cells)} cells entries={len(cf.entries)}")
    for e in cf.entries:
        print(f"[diag]   entry kind={e.kind} pos={e.pos} eid={e.eid} "
              f"access_dmg={getattr(e, 'access_dmg', '?')} path_len={getattr(e, 'path_len', '?')}")
    floor = game.floors[cur]
    cur_n = _floor_n(cur)
    for (x, y), block in floor.blocks.items():
        if block.eid not in STAIRS:
            continue
        adj = any(n in cf.reachable_cells for n in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)))
        to = f"MT{cur_n+1}" if block.eid == "upFloor" else f"MT{cur_n-1}"
        print(f"[diag]   stair {block.eid} at x{x}y{y} adj_reachable={adj} -> {to}")


def skeleton_actions(game: Game) -> Iterable[GameAction]:
    _N["n"] += 1
    if _N["n"] % 100 == 0:
        el = time.perf_counter() - _T0
        print(f"  [progress] exp={_N['n']} {game.state['floor']} HP={game.state['hp']} "
              f"G={game.state['gold']} t1={game.state.get('times1',0)} {el:.1f}s", flush=True)
    acts: list[GameAction] = []
    cur = game.state["floor"]
    cf = _flood_floor(game, cur)
    entries = cf.entries
    # 1) 当前楼层骨架/商店/怪 click（怪按 access_dmg 升序前 12）
    monsters = sorted([e for e in entries if e.kind == "monster"],
                      key=lambda e: (e.access_dmg, e.path_len))[:12]
    for e in [e for e in entries if e.kind in ("skeleton", "shop")] + monsters:
        x, y, eid = e.pos[0], e.pos[1], e.eid
        def make_apply(fid=cur, x=x, y=y, eid=eid):
            def apply(game: Game) -> None:
                go_to_decomposed(game, fid, x, y, f"click {eid}")
            return apply
        acts.append(GameAction(name=f"click {cur} x{x}y{y} {eid}", apply=make_apply()))
    # 2) 楼梯换层（upFloor->MT(n+1)，downFloor->MT(n-1)）
    cur_n = _floor_n(cur)
    floor = game.floors[cur]
    for (x, y), block in floor.blocks.items():
        if block.eid not in STAIRS:
            continue
        adj = any(n in cf.reachable_cells for n in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)))
        if not adj:
            continue
        to_fid = f"MT{cur_n+1}" if block.eid == "upFloor" else f"MT{cur_n-1}"
        def make_stair(to_fid=to_fid, fid=cur, x=x, y=y):
            def apply(game: Game) -> None:
                game.change_by_stair(to_fid, x, y, f"stair {fid}->{to_fid}")
            return apply
        acts.append(GameAction(name=f"stair {cur} x{x}y{y}->{to_fid}", apply=make_stair()))
    # 3) MT12 blueShop 每次购买=独立骨架节点（atk/def/hp）。仅 MT12 且商店可达时。
    #    必须先 move_adjacent 接近商店（触发 auto_sweep：杀挡路 bat + 捡路上药瓶），
    #    再 buy_shop。buy_shop 本身位置无关（纯状态变更），跳过 approach 会让搜索
    #    从远处"凭空买"，与 live（点击商店=先走过去 auto-sweep 再买）不符。
    #    ratio2: atk+4/次, def+8/次, hp+100*(times1+1)。
    if cur == "MT12":
        shop_ok = any(e.kind == "shop" and tuple(e.pos) == MT12_BLUESHOP for e in entries)
        if shop_ok:
            for stat in ("atk", "def", "hp"):
                def make_buy(stat=stat):
                    def apply(game: Game) -> None:
                        game.move_adjacent("MT12", MT12_BLUESHOP[0], MT12_BLUESHOP[1], f"approach MT12 shop {stat}")
                        game.buy_shop(stat, 1, shop_pos=MT12_BLUESHOP)
                    return apply
                acts.append(GameAction(name=f"buy {stat} MT12", apply=make_buy()))
    return acts


_GOAL = "2atk"  # 2atk | 2atk1def | mt14（main 里由 --goal 覆盖）


def goal(game: Game) -> bool:
    s = game.state
    if s["hp"] <= 0:
        return False
    if _GOAL == "2atk":
        return s["floor"] == "MT12" and s.get("times1", 0) >= 2
    if _GOAL == "2atk1def":
        return s["floor"] == "MT12" and s["atk"] >= 38 and s["def"] >= 38
    if _GOAL == "mt14":
        return s["floor"] == "MT14"
    return False


def heuristic(game: Game) -> float:
    """O(1) 引导式。2atk/2atk1def 推向 MT12+购买；mt14 推向 MT14。"""
    s = game.state
    cur = s["floor"]
    if _GOAL in ("2atk", "2atk1def"):
        atk_need = max(0.0, (38 - s["atk"]) / 4.0)
        def_need = max(0.0, (38 - s["def"]) / 8.0) if _GOAL == "2atk1def" else 0.0
        if atk_need == 0.0 and def_need == 0.0 and cur == "MT12":
            return 0.0
        base = atk_need + def_need
        if cur == "MT12":
            return base
        return base + 1.0 + float(abs(_floor_n(cur) - 12))
    # mt14
    fn = _floor_n(cur)
    if fn >= 14:
        return 0.0
    h = float(14 - fn)
    if s["atk"] < 34:
        h += 1.0
    return h


def main() -> int:
    global _T0, _GOAL
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--diag", action="store_true")
    p.add_argument("--goal", default="2atk", choices=["2atk", "2atk1def", "mt14"])
    p.add_argument("--max-expansions", type=int, default=8000)
    p.add_argument("--weight", type=float, default=3.0)
    p.add_argument("--top-k", type=int, default=1, help="收集 top-K goal 状态（按 dmg 排序）")
    p.add_argument("--out-json", type=Path,
                  default=ROOT / "outputs" / "results" / "zone2_search_walk.json")
    args = p.parse_args()
    _GOAL = args.goal

    g = Game(read_json(SAVE100))
    g.strict_live_model = True
    g.auto_flags = {"battle": True, "item": True, "wall": True}
    apply_mt10_supply(g)
    print(f"start: {state_line(g.state)} {g.state['floor']} x{g.state['x']}y{g.state['y']}", flush=True)

    if args.diag:
        _diag_matrix(g)
        return 0

    print(f"  target: {args.goal} | weight={args.weight} max_exp={args.max_expansions}", flush=True)
    _T0 = time.perf_counter()

    astar = GameAStar(
        actions=skeleton_actions,
        goal=goal,
        heuristic=heuristic,
        edge_cost=lambda b, a, _act: float(max(0, a.state["dmg"] - b.state["dmg"])),
        state_key=lambda game: (game.state["floor"], game.state["x"], game.state["y"],
                                game.state["atk"], game.state["def"], game.state["hp"] // 20,
                                game.state["times1"], game.state["gold"],
                                game.state["yk"], game.state["bk"], game.state["rk"]),
        weight=args.weight,
        max_expansions=args.max_expansions,
        top_k=args.top_k,
    )
    res = astar.search(g)
    el = time.perf_counter() - _T0
    print(f"\nfound={res.found} cost={res.cost} expansions={res.expansions} "
          f"generated={res.generated} reason={res.reason} {el:.1f}s", flush=True)
    if res.found and res.game:
        print(f"final: {state_line(res.game.state)} {res.game.state['floor']} "
              f"x{res.game.state['x']}y{res.game.state['y']}", flush=True)
        print(f"actions ({len(res.actions)}):", flush=True)
        for a in res.actions:
            print(f"  {a.name}", flush=True)
        if res.top_goals:
            print(f"\ntop-{len(res.top_goals)} goals (by dmg asc):", flush=True)
            for i, (c, gm, _rt) in enumerate(res.top_goals):
                s = gm.state
                print(f"  #{i+1} dmg={c:.0f} HP={s['hp']} ATK={s['atk']} DEF={s['def']} "
                      f"YK={s['yk']} BK={s['bk']} RK={s['rk']} G={s['gold']} "
                      f"{s['floor']} x{s['x']}y{s['y']}", flush=True)
        # Game-steps JSON（= replayer walk.json；gen_zone_walk_md.py 同源产 walk.md）
        steps = res.game.steps if hasattr(res.game, "steps") else []
        print(f"steps={len(steps)} (含补给+路线)", flush=True)
        args.out_json.parent.mkdir(parents=True, exist_ok=True)
        args.out_json.write_text(json.dumps({
            "ok": not res.game.errors,
            "variant": f"zone2_search_{args.goal}",
            "source_checkpoint": "save100(=live slot 100, MT10 boss后补给前)",
            "goal": args.goal,
            "final": res.game.snapshot(),
            "steps": steps,
            "errors": res.game.errors,
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"walk.json={args.out_json}", flush=True)
    return 0 if res.found else 1


if __name__ == "__main__":
    raise SystemExit(main())
