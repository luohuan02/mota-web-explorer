#!/usr/bin/env python3
"""Audit recoverable resources around the Zone-4 TE ending.

The default mode retains the historical pre-boss view for comparison.  Passing
``--post-boss-final`` audits the actual final Game state, including the sealed
true-redKing's spendable 500G and any subsequent strict cleanup/shop actions.
All reachability probes and cleanup strategies use the shared strict ``Game``
implementation; this script does not edit coordinates or replay browser APIs.
"""
from __future__ import annotations

import json
import pickle
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.search.zone4_game_route import DEFAULT_CHECKPOINT, Zone4Game, run_zone4
from src.solver.game_route import (
    RouteError,
    buy_hp_with_remaining_gold,
    cleanup_reachable_items,
    clear_zero_damage_monsters,
    eat_all_reachable_potions,
    go_to_decomposed,
    read_json,
    shop_cost,
    terminal_hp_resource_closure,
)

OUT_JSON = ROOT / "outputs" / "results" / "zone4_endgame_resource_audit.json"
OUT_MD = ROOT / "outputs" / "reports" / "zone4_endgame_resource_audit.md"
CACHE = ROOT / "outputs" / "results" / "zone4_endgame_resource_audit_game.pkl"
ITEMS = {"redGem", "blueGem", "yellowKey", "blueKey", "redKey"}


def compact_state(g: Zone4Game) -> dict[str, Any]:
    return {k: g.state[k] for k in (
        "floor", "x", "y", "hp", "atk", "def", "yk", "bk", "rk",
        "gold", "dmg", "yd", "bd", "rd", "times1",
    )}


def delta(before: dict[str, Any], after: dict[str, Any]) -> dict[str, int]:
    keys = ("hp", "atk", "def", "yk", "bk", "rk", "gold", "dmg", "yd", "bd", "rd")
    return {key: int(after[key]) - int(before[key]) for key in keys}


def pre_boss_clone(final: Zone4Game) -> Zone4Game:
    g = final.clone()
    # The canonical final action is the sealed redKing: 0 HP damage and 500G.
    # Rewind only its economic/map effect; remaining-resource probes never need
    # to fight that boss and are compared against the genuine 20G pre-boss base.
    last = final.steps[-1]
    before = last.get("before", {})
    after = last.get("after", {})
    if not (
        last.get("floor") == "MT50"
        and after.get("gold", 0) - before.get("gold", 0) == 500
        and after.get("hp") == before.get("hp")
    ):
        raise RuntimeError("canonical route no longer ends with the expected 500G zero-damage boss")
    # Use the last MT24 state before the final one-way ascent.  MT50 itself is
    # intentionally not flyable, so probing from the boss tile would falsely
    # classify every lower-floor resource as unreachable.
    mt24 = next(
        step["after"] for step in reversed(final.steps)
        if step.get("after", {}).get("floor") == "MT24"
    )
    for key in ("floor", "x", "y", "hp", "atk", "def", "yk", "bk", "rk", "gold", "dmg", "yd", "bd", "rd", "times1"):
        g.state[key] = mt24[key]
    return g


def cache_signature() -> tuple[tuple[str, int], ...]:
    paths = [
        DEFAULT_CHECKPOINT,
        ROOT / "src" / "solver" / "game_route.py",
        ROOT / "scripts" / "search" / "zone4_game_route.py",
    ]
    return tuple((str(path.relative_to(ROOT)), path.stat().st_mtime_ns) for path in paths)


def build_base() -> Zone4Game:
    if "--game-pickle" in sys.argv:
        i = sys.argv.index("--game-pickle")
        if i + 1 >= len(sys.argv):
            raise RuntimeError("--game-pickle requires a path")
        final = pickle.loads(Path(sys.argv[i + 1]).read_bytes())
        print(f"game-pickle={sys.argv[i + 1]}")
        if "--post-boss-final" in sys.argv:
            return final.clone()
        return pre_boss_clone(final)
    signature = cache_signature()
    if CACHE.exists():
        try:
            payload = pickle.loads(CACHE.read_bytes())
            if payload.get("signature") == signature or "--reuse-cache" in sys.argv:
                print(f"cache={CACHE}")
                return payload["game"]
        except (OSError, pickle.PickleError, EOFError, AttributeError):
            pass
    g = Zone4Game(read_json(DEFAULT_CHECKPOINT))
    g.strict_live_model = True
    g.auto_flags = {"battle": True, "item": "nopotion", "wall": True}
    run_zone4(g)
    if g.errors:
        raise RuntimeError(f"canonical Zone4 replay failed: {g.errors[:3]}")
    base = pre_boss_clone(g)
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_bytes(pickle.dumps({"signature": signature, "game": base}, protocol=pickle.HIGHEST_PROTOCOL))
    return base


def raw_remaining(g: Zone4Game) -> tuple[Counter[str], list[dict[str, Any]]]:
    counts: Counter[str] = Counter()
    rows: list[dict[str, Any]] = []
    for fid in sorted(g.visited, key=lambda value: int(value[2:])):
        floor = g.floors.get(fid)
        if floor is None:
            continue
        for (x, y), block in sorted(floor.blocks.items()):
            if block.kind not in {"item", "enemy"}:
                continue
            counts[f"{block.kind}:{block.eid}"] += 1
            rows.append({"floor": fid, "x": x, "y": y, "kind": block.kind, "eid": block.eid})
    return counts, rows


def optimistic_funding_ledger(g: Zone4Game) -> dict[str, Any]:
    """Return a safe no-door-cost upper bound for another 46F shop.

    This is deliberately more generous than any legal route: every remaining
    yellow key is valued at its full 28F sale price and every remaining enemy's
    money is counted even when unreachable, damaging or strategically blocked.
    Door/key costs are ignored.  Therefore a total below the next shop cost is
    a proof that no cleanup order can fund that shop.
    """
    multiplier = 2 if g.state.get("coin") else 1
    remaining_yk = 0
    enemy_money = 0
    enemy_counts: Counter[str] = Counter()
    enemy_money_by_id: Counter[str] = Counter()
    for fid in g.visited:
        floor = g.floors.get(fid)
        if floor is None:
            continue
        for block in floor.blocks.values():
            if block.kind == "item" and block.eid == "yellowKey":
                remaining_yk += 1
            elif block.kind == "enemy":
                money = int(g.enemies.get(block.eid, {}).get("money", 0)) * multiplier
                enemy_money += money
                enemy_counts[block.eid] += 1
                enemy_money_by_id[block.eid] += money
    current_gold = int(g.state["gold"])
    current_yk_sale = max(0, int(g.state["yk"])) * 100
    remaining_yk_sale = remaining_yk * 100
    return {
        "lucky_coin": bool(g.state.get("coin")),
        "money_multiplier": multiplier,
        "current_gold": current_gold,
        "current_yk": int(g.state["yk"]),
        "current_yk_sale": current_yk_sale,
        "remaining_yellow_keys": remaining_yk,
        "remaining_yk_sale": remaining_yk_sale,
        "remaining_enemy_money": enemy_money,
        "remaining_enemy_counts": dict(sorted(enemy_counts.items())),
        "remaining_enemy_money_by_id": dict(sorted(enemy_money_by_id.items())),
        "optimistic_total": current_gold + current_yk_sale + remaining_yk_sale + enemy_money,
        "ignored_costs": "all doors, combat HP, reachability and strategic timing",
    }


def probe_targets(g: Zone4Game, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    base = compact_state(g)
    out: list[dict[str, Any]] = []
    for row in rows:
        cand = g.clone()
        try:
            if cand.state["floor"] != row["floor"]:
                cand.fly(row["floor"])
            go_to_decomposed(
                cand, row["floor"], row["x"], row["y"],
                f"endgame audit {row['kind']} {row['eid']}",
            )
        except RouteError:
            continue
        after = compact_state(cand)
        change = delta(base, after)
        if not any(change.values()):
            continue
        out.append({**row, "delta": change, "after": after})
    out.sort(
        key=lambda row: (
            row["delta"]["hp"], row["delta"]["gold"],
            row["delta"]["atk"] + row["delta"]["def"],
        ),
        reverse=True,
    )
    return out


def strategy_zero_damage(g: Zone4Game) -> None:
    clear_zero_damage_monsters(g, preserve_yk=0, min_floor=1)


def strategy_resources(g: Zone4Game) -> None:
    cleanup_reachable_items(
        g, ITEMS, min_floor=1, preserve_rk=0, allow_door_investment=True,
    )
    clear_zero_damage_monsters(g, preserve_yk=0, min_floor=1)
    eat_all_reachable_potions(
        g, min_floor=1, allow_door_investment=True, preserve_rk=0,
    )


def strategy_fixed_point(g: Zone4Game) -> None:
    terminal_hp_resource_closure(g)


def take_best_positive_hp_group(g: Zone4Game) -> bool:
    """Commit the best currently recoverable item group with real HP gain.

    A target may auto-collect adjacent keys/gems/potions, so rank the fully
    replayed group delta instead of assigning a static value to its target tile.
    """
    before = compact_state(g)
    best: tuple[tuple[int, int, int, int], Zone4Game] | None = None
    for fid in sorted(g.visited, key=lambda value: int(value[2:])):
        for (x, y), block in list(g.floors[fid].blocks.items()):
            if block.kind != "item":
                continue
            cand = g.clone()
            try:
                if cand.state["floor"] != fid:
                    cand.fly(fid)
                go_to_decomposed(cand, fid, x, y, f"HP-first resource group {block.eid}")
            except RouteError:
                continue
            after = compact_state(cand)
            d = delta(before, after)
            if d["hp"] <= 0 or after["hp"] <= 0:
                continue
            rank = (d["hp"], d["yk"] * 4 + d["bk"] * 16 + d["rk"] * 32, d["def"], d["atk"])
            if best is None or rank > best[0]:
                best = (rank, cand)
    if best is None:
        return False
    g.__dict__.update(best[1].__dict__)
    return True


def strategy_hp_first(g: Zone4Game) -> None:
    while take_best_positive_hp_group(g):
        pass
    strategy_fixed_point(g)


def run_strategy(base: Zone4Game, name: str, fn: Callable[[Zone4Game], None]) -> dict[str, Any]:
    cand = base.clone()
    before = compact_state(cand)
    start_steps = len(cand.steps)
    try:
        fn(cand)
        error = None
    except RouteError as exc:
        error = str(exc)
    after = compact_state(cand)
    return {
        "name": name,
        "ok": error is None,
        "error": error,
        "before": before,
        "after": after,
        "delta": delta(before, after),
        "added_steps": len(cand.steps) - start_steps,
        "steps": cand.steps[start_steps:],
    }


def main() -> int:
    base = build_base()
    counts, rows = raw_remaining(base)
    probes = probe_targets(base, rows)
    strategies = [
        run_strategy(base, "zero_damage", strategy_zero_damage),
        run_strategy(base, "resources", strategy_resources),
        run_strategy(base, "hp_first", strategy_hp_first),
        run_strategy(base, "fixed_point", strategy_fixed_point),
    ]
    fixed = next(row for row in strategies if row["name"] == "fixed_point")
    next_cost = shop_cost(base.state["times1"])
    effective_funding = base.state["gold"] + base.state["yk"] * 100
    funding_ledger = optimistic_funding_ledger(base)
    reward_positions = {
        (5, 2), (7, 2), (2, 4), (3, 4), (4, 4),
        (8, 4), (9, 4), (10, 4), (5, 5), (6, 5), (7, 5),
    }
    remaining_49_rewards = [
        row for row in rows
        if row["floor"] == "MT49" and (row["x"], row["y"]) in reward_positions
    ]
    positive_hp_probes = [row for row in probes if row["delta"]["hp"] > 0]
    assertions = {
        "fixed_point_hp_delta_zero": fixed["delta"]["hp"] == 0,
        "fixed_point_shop_count_unchanged": fixed["after"]["times1"] == fixed["before"]["times1"],
        "no_reachable_positive_hp_target": not positive_hp_probes,
        "optimistic_collect_all_funding_below_next_hp_shop": (
            funding_ledger["optimistic_total"] < next_cost
        ),
        "mt49_event_rewards_cleared": not remaining_49_rewards,
    }
    post_boss = "--post-boss-final" in sys.argv
    result = {
        "objective": "2026复刻版 / 纯净版-TE / 生命",
        "audit_phase": "post_boss_before_confirmation" if post_boss else "pre_boss",
        "baseline_pre_boss": compact_state(base),
        "next_hp_shop_cost": next_cost,
        "effective_funding_gold_plus_yk_sale": effective_funding,
        "optimistic_funding_ledger": funding_ledger,
        "remaining_counts": dict(sorted(counts.items())),
        "reachable_target_probes": probes,
        "reachable_positive_hp_probes": positive_hp_probes,
        "remaining_mt49_event_rewards": remaining_49_rewards,
        "strategies": strategies,
        "assertions": assertions,
        "ok": all(assertions.values()),
    }
    out_json = Path(sys.argv[sys.argv.index("--out-json") + 1]) if "--out-json" in sys.argv else OUT_JSON
    out_md = Path(sys.argv[sys.argv.index("--out-md") + 1]) if "--out-md" in sys.argv else OUT_MD
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 4区终战后确认前剩余资源审计" if post_boss else "# 4区终战前剩余资源审计",
        "",
        "- 目标：`2026复刻版 / 纯净版-TE / 生命`",
        f"- 终战前基线：`{compact_state(base)}`",
        f"- 下一次 46F 生命商店成本：`{result['next_hp_shop_cost']}G`",
        f"- 有效资金（金币 + 可售黄钥匙）：`{effective_funding}G`",
        f"- 无视全部门、伤害与可达性的收集上界：`{funding_ledger['optimistic_total']}G`",
        f"- 幸运金币：`{funding_ledger['lucky_coin']}`；怪物金币倍率：`{funding_ledger['money_multiplier']}x`",
        ("- 真魔王500G已到账，并按实机确认框前可继续消费处理。" if post_boss
         else "- 本视图不把尚未击杀的真魔王500G倒算为战前资金。"),
        "- 上界仍低于商店成本时，任何真实清场顺序只会更差。",
        "",
        "## 剩余资源计数",
        "",
    ]
    lines.extend(f"- `{key}`：{value}" for key, value in result["remaining_counts"].items())
    lines += [
        "",
        "## 可达目标探针（按单次点击链的实际变化排序）",
        "",
        "| 位置 | 类型 | HP | 攻 | 防 | 黄/蓝/红钥匙 | 金币 | 开门 |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in probes[:80]:
        d = row["delta"]
        lines.append(
            f"| {row['floor']} x{row['x']}y{row['y']} | {row['kind']}:{row['eid']} | "
            f"{d['hp']:+d} | {d['atk']:+d} | {d['def']:+d} | "
            f"{d['yk']:+d}/{d['bk']:+d}/{d['rk']:+d} | {d['gold']:+d} | "
            f"{d['yd']:+d}/{d['bd']:+d}/{d['rd']:+d} |"
        )
    lines += ["", "## 清场策略对比", "", "| 策略 | 可执行 | HP变化 | 金币变化 | 钥匙变化 | 新增步骤 |", "|---|---:|---:|---:|---:|---:|"]
    for row in strategies:
        d = row["delta"]
        lines.append(
            f"| {row['name']} | {row['ok']} | {d['hp']:+d} | {d['gold']:+d} | "
            f"{d['yk']:+d}/{d['bk']:+d}/{d['rk']:+d} | {row['added_steps']} |"
        )
    lines += ["", "## 终战闭环断言", ""]
    lines.extend(f"- `{key}`：{'通过' if value else '失败'}" for key, value in assertions.items())
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"baseline={result['baseline_pre_boss']}")
    print(f"remaining={result['remaining_counts']}")
    print(f"assertions={assertions} ok={result['ok']}")
    for row in strategies:
        print(f"strategy={row['name']} ok={row['ok']} delta={row['delta']} steps={row['added_steps']} error={row['error']}")
    print(f"json={out_json}")
    print(f"md={out_md}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
