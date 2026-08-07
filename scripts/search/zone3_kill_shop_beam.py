#!/usr/bin/env python3
"""zone3 KILL 线参数化商店 beam 搜索 (在已验证 walk 骨架上优化商店决策)。

from-scratch A* 撞 zone3 长程前置墙 (MT2 thief 需 BK+blueDoor+detour) + 商店组合爆炸,
不实际。本脚本改用已验证 kill walk 作骨架 (所有前置/事件/收集固定), 只在 8 个商店点
分支 kind ∈ {atk, def, skip} (不 hp, 用户点1), Game 逐段回放验证存活, 按 final-score
选最优。直接命中用户杠杆:
  1. 不买 hp (#118 hp->atk/def/skip)
  2. 对比多买 vs 省钱 zone4 (buy/skip)
  3. 早买 atk 达 150 让 swordsman 0伤 (在更早商店槽买 atk)
  4. 3区买防 (所有商店都在 zone3 MT32)

beam: 每个商店点保留 top-K (hp + atk/def 增益 + gold×1.25 + 钥匙), 分支 3 路, 死亡剪枝。
终点用 comparison_score (HP+钥匙+剩余资源+gold×溢价) 排序选最优。
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.solver.game_route import state_line, RouteError  # noqa: E402
from src.solver.reachability_matrix import compute_matrix, comparison_score  # noqa: E402
from scripts.search.zone3_kill_astar import build_start  # noqa: E402
from scripts.search.zone3_game_route import run_zone3  # noqa: E402

KILL_WALK = ROOT / "best" / "zone3_2atk0def_kill_walk.json"
DEFAULT_OUT_JSON = ROOT / "outputs" / "results" / "zone3_kill_shop_beam_walk.json"
SHOP_POS = (10, 10)  # MT32 blueShop (所有 8 个商店都在此)
GOLD_PREMIUM = 1.25


def _rank_proxy(g) -> float:
    """beam 中间排序代理 (Pareto 后超额时用): hp + atk/def 增益 + gold×溢价 + 钥匙值。"""
    s = g.state
    return (s["hp"]
            + (s["atk"] - 76) * 6 + (s["def"] - 66) * 6
            + s["gold"] * 0.4
            + s["yk"] * 50 + s["bk"] * 200 + s["rk"] * 420)


def _pareto_metrics(g):
    """Pareto 指标 (越高越好): atk, def, hp, gold, yk, bk, rk。"""
    s = g.state
    return (s["atk"], s["def"], s["hp"], s["gold"], s["yk"], s["bk"], s["rk"])


def _pareto_keep(items, cap):
    """保留 Pareto 非支配分支 (atk/def/hp/gold/keys 多目标, 避免单一 proxy 偏向 def 或 atk)。
    超过 cap 时按 _rank_proxy 截断。items: list of (game, decs, off)。"""
    metrics = [(i, _pareto_metrics(i[0])) for i in items]
    kept = []
    for i, mi in metrics:
        dominated = False
        for j, mj in metrics:
            if j is i:
                continue
            # mj 支配 mi: mj 各维 >= mi 且至少一维 >
            if all(mj[k] >= mi[k] for k in range(len(mi))) and any(mj[k] > mi[k] for k in range(len(mi))):
                dominated = True
                break
        if not dominated:
            kept.append(i)
    if len(kept) > cap:
        kept.sort(key=lambda t: -_rank_proxy(t[0]))
        kept = kept[:cap]
    return kept


def main() -> int:
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--beam-k", type=int, default=40)
    p.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    args = p.parse_args()

    walk = json.loads(KILL_WALK.read_text(encoding="utf-8"))
    steps = walk["steps"]
    shop_idx = [i for i, s in enumerate(steps) if s.get("action") == "商店"]
    print(f"shops at idx {shop_idx}, kinds {[steps[i].get('eid') for i in shop_idx]}", flush=True)
    print(f"incumbent (existing kill walk, has hp): HP=609 ATK=166 DEF=174 G=2285 dmg=8806", flush=True)

    t0 = time.perf_counter()
    # beam: list of (game, decisions, step_replay_offset)
    g0 = build_start()
    beam = [(g0, [], 0)]
    prev = 0
    for si, sidx in enumerate(shop_idx):
        seg = steps[prev:sidx]
        # 回放非商店段到所有 beam 游戏 (RouteError = 该分支死亡)
        for (g, decs, _off) in beam:
            if seg:
                try:
                    run_zone3(g, [0], None, {"steps": seg})
                except RouteError:
                    g.errors.append("segment replay RouteError (branch dead)")
        # 剪死亡
        beam = [(g, decs, sidx) for (g, decs, _off) in beam
                if not g.errors and g.state["hp"] > 0]
        if not beam:
            print(f"  all beam died before shop #{si} (idx {sidx})", flush=True)
            break
        # 分支 atk/def/skip (不 hp)
        new_beam = []
        for (g, decs, _off) in beam:
            for kind in ("atk", "def", "skip"):
                g2 = g.clone()
                if kind != "skip":
                    try:
                        g2.move_adjacent("MT32", SHOP_POS[0], SHOP_POS[1], f"shop {kind}")
                        g2.buy_shop(kind, 1, shop_pos=SHOP_POS)
                    except Exception:
                        continue
                if g2.state["hp"] > 0 and not g2.errors:
                    new_beam.append((g2, decs + [kind], sidx))
        beam = _pareto_keep(new_beam, args.beam_k)
        prev = sidx + 1
        bs = beam[0][0].state
        print(f"  shop#{si} (idx {sidx}): {len(new_beam)} branches -> keep {len(beam)}, "
              f"sample HP={bs['hp']} ATK={bs['atk']} DEF={bs['def']} G={bs['gold']} t1={bs['times1']} "
              f"decisions={beam[0][1]}", flush=True)

    # 最终段 (last shop -> end)
    seg = steps[prev:]
    finalists = []
    for (g, decs, _off) in beam:
        if seg:
            try:
                run_zone3(g, [0], None, {"steps": seg})
            except RouteError:
                g.errors.append("final segment replay RouteError")
        if not g.errors and g.state["hp"] > 0 and g.flags.get("402"):
            rm = compute_matrix(g)
            cs = comparison_score(g, rm)
            finalists.append((g, decs, cs))

    el = time.perf_counter() - t0
    print(f"\nbeam done in {el:.1f}s. finalists (reached MT41+flags402): {len(finalists)}", flush=True)
    if not finalists:
        print("no finalist reached MT41 with flags402.", flush=True)
        # show best survivor even if not at goal
        if beam:
            for g, decs, _ in sorted(beam, key=lambda t: -_rank_proxy(t[0]))[:3]:
                s = g.state
                print(f"  survivor: HP={s['hp']} ATK={s['atk']} DEF={s['def']} {s['floor']} "
                      f"flags402={g.flags.get('402')} decs={decs}", flush=True)
        return 2

    finalists.sort(key=lambda t: -t[2]["total"])
    print(f"\n=== top finalists (by final-score) ===", flush=True)
    for i, (g, decs, cs) in enumerate(finalists[:10]):
        s = g.state
        print(f"  #{i+1} HP={s['hp']} ATK={s['atk']} DEF={s['def']} YK={s['yk']} BK={s['bk']} "
              f"RK={s['rk']} G={s['gold']} dmg={s['dmg']} t1={s['times1']} {s['floor']} | "
              f"final-score={cs['total']:.0f} (gold_val={cs['gold_value']:.0f} remain={cs['remaining']['total']:.0f}) "
              f"decisions={decs}", flush=True)

    best_g, best_decs, best_cs = finalists[0]
    s = best_g.state
    print(f"\nBEST: HP={s['hp']} ATK={s['atk']} DEF={s['def']} G={s['gold']} dmg={s['dmg']} "
          f"final-score={best_cs['total']:.0f} decisions={best_decs}", flush=True)
    print(f"  vs incumbent HP=609 dmg=8806 (has hp shop)", flush=True)

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps({
        "ok": not best_g.errors,
        "variant": "zone3_kill_shop_beam",
        "source_slot": 32,
        "source_walk": str(KILL_WALK),
        "goal": "MT41+flags402 (no hp shop, shop-kind beam)",
        "shop_decisions": best_decs,
        "final": best_g.snapshot(),
        "steps": best_g.steps,
        "errors": best_g.errors,
        "comparison_score": best_cs,
        "all_finalists": [
            {"decisions": decs, "final": g.snapshot(), "final_score": cs["total"],
             "hp": g.state["hp"], "dmg": g.state["dmg"], "gold": g.state["gold"]}
            for g, decs, cs in finalists[:10]
        ],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"walk.json={args.out_json} steps={len(best_g.steps)}", flush=True)
    return 0 if not best_g.errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
