#!/usr/bin/env python3
"""Build an auto-OFF explicit MT4->MT10 post-boss-supply walk."""

from __future__ import annotations

import json
import copy
import re
from pathlib import Path
from typing import Any

from build_autooff_mt4_to_mt7_prefix_walk import (
    AUTO_ON,
    build_game_to_mt7,
    normalize_step,
    set_auto_step,
)
from search_post40_guide_route import Block, classify, load_enemies, load_tiles


ROOT = Path(__file__).resolve().parents[1]
SOURCE_WALK = ROOT / "outputs" / "results" / "strict20_preserve_pickaxe_4to50_web_strict_record_step001_402_nopot_switch.json"
MT10_POST_BOSS_MAP = ROOT / "data" / "maps" / "mt10_post_boss_map.json"
OUT_JSON = ROOT / "outputs" / "results" / "strict20_autooff_mt4_to_mt10_supply_walk.json"

AUTO_COORD_RE = re.compile(r"MT(\d+) x(\d+)y(\d+) ([A-Za-z0-9_]+)")
POST_BOSS_SUPPLY = [
    ("MT10", 1, 3, "redGem"),
    ("MT10", 2, 3, "redGem"),
    ("MT10", 3, 3, "redGem"),
    ("MT10", 9, 3, "blueGem"),
    ("MT10", 10, 3, "blueGem"),
    ("MT10", 11, 3, "blueGem"),
    ("MT10", 1, 4, "bluePotion"),
    ("MT10", 2, 4, "bluePotion"),
    ("MT10", 3, 4, "bluePotion"),
    ("MT10", 9, 4, "yellowKey"),
    ("MT10", 10, 4, "yellowKey"),
    ("MT10", 11, 4, "yellowKey"),
]
MT10_BOSS_SPAWN = [
    ((6, 4), "skeletonSoldier"),
    ((5, 5), "skeleton"),
    ((5, 4), "skeleton"),
    ((7, 4), "skeleton"),
    ((7, 5), "skeleton"),
    ((5, 6), "skeleton"),
    ((6, 6), "skeletonSoldier"),
    ((7, 6), "skeleton"),
    ((6, 1), "skeletonCaptain"),
]


def read_source_steps() -> list[dict[str, Any]]:
    raw = json.loads(SOURCE_WALK.read_text(encoding="utf-8-sig"))
    return raw.get("strictWalk", {}).get("steps") or raw.get("steps") or []


def relabel_last(g: Any, action: str, eid: str | None) -> None:
    if not g.steps:
        return
    g.steps[-1]["action"] = action
    g.steps[-1]["eid"] = eid


def source_state_text(state: dict[str, Any]) -> str:
    return (
        f"{state.get('floor')} x{state.get('x')}y{state.get('y')} "
        f"HP={state.get('hp')} ATK={state.get('atk')} DEF={state.get('def')} "
        f"YK={state.get('yk')} BK={state.get('bk')} RK={state.get('rk')} G={state.get('gold')}"
    )


def comparable_state(state: dict[str, Any]) -> dict[str, Any]:
    return {key: state.get(key) for key in ("hp", "atk", "def", "yk", "bk", "rk", "gold")}


def explicit_old_auto_resources(g: Any, step: dict[str, Any], pending: list[tuple[str, int, int, str]]) -> None:
    seen: set[tuple[str, int, int, str]] = set()
    for chunk in (step.get("note") or "").split("自动处理：")[1:]:
        for floor_no, x_text, y_text, eid in AUTO_COORD_RE.findall(chunk):
            fid = f"MT{floor_no}"
            x = int(x_text)
            y = int(y_text)
            key = (fid, x, y, eid)
            if key in seen:
                continue
            seen.add(key)
            if g.block_at(fid, (x, y)):
                pending.append(key)
        pending[:] = collect_targets_any_order(g, pending)


def add_pending_if_block(g: Any, pending: list[tuple[str, int, int, str]], fid: str, x: int, y: int, eid: str) -> None:
    if g.block_at(fid, (x, y)):
        target = (fid, x, y, eid)
        if target not in pending:
            pending.append(target)


def collect_targets_any_order(g: Any, targets: list[tuple[str, int, int, str]]) -> list[tuple[str, int, int, str]]:
    pending = [target for target in targets if g.block_at(target[0], (target[1], target[2]))]
    if not pending:
        return []
    open_known_blockers(g, pending)

    def solve(game: Any, rest: list[tuple[str, int, int, str]]) -> Any | None:
        if not rest:
            return game
        for idx, (fid, x, y, eid) in enumerate(rest):
            cand = game.clone()
            try:
                if cand.state["floor"] != fid:
                    cand.fly(fid)
                cand.go_to(fid, x, y, f"显式处理原合并资源 {eid}")
            except Exception:
                continue
            solved = solve(cand, rest[:idx] + rest[idx + 1 :])
            if solved is not None:
                return solved
        return None

    solved = solve(g, pending)
    if solved is not None:
        g.__dict__.update(solved.__dict__)
        return []

    remaining = list(pending)
    progressed = True
    while progressed:
        progressed = False
        for idx, (fid, x, y, eid) in enumerate(list(remaining)):
            cand = g.clone()
            try:
                if cand.state["floor"] != fid:
                    cand.fly(fid)
                cand.go_to(fid, x, y, f"显式处理原合并资源 {eid}")
            except Exception:
                continue
            g.__dict__.update(cand.__dict__)
            del remaining[idx]
            progressed = True
            break
    return remaining


def collect_zero_enemy_gold_deficit(g: Any, expected: dict[str, Any]) -> bool:
    live = comparable_state(g.snapshot())
    if any(live.get(key) != expected.get(key) for key in ("hp", "atk", "def", "yk", "bk", "rk")):
        return False
    missing = int(expected.get("gold") or 0) - int(live.get("gold") or 0)
    if missing <= 0:
        return False

    candidates: list[tuple[tuple[str, int, int, str], int]] = []
    for _dist, _y, pos, block in g._auto_enemy_candidates(g.state["floor"], battle=True, item_mode=True, wall=True):
        money = int(g.enemies[block.eid].get("money", 0))
        if money <= 0:
            continue
        candidates.append(((g.state["floor"], pos[0], pos[1], block.eid), money))

    choices: list[list[tuple[str, int, int, str]]] = []

    def choose(idx: int, remaining: int, chosen: list[tuple[str, int, int, str]]) -> None:
        if remaining == 0:
            choices.append(list(chosen))
            return
        if remaining < 0 or idx >= len(candidates) or len(choices) >= 16:
            return
        target, money = candidates[idx]
        chosen.append(target)
        choose(idx + 1, remaining - money, chosen)
        chosen.pop()
        choose(idx + 1, remaining, chosen)

    choose(0, missing, [])
    for targets in choices:
        cand = g.clone()
        remaining = collect_targets_any_order(cand, targets)
        if remaining:
            continue
        after = comparable_state(cand.snapshot())
        if after == expected:
            g.__dict__.update(cand.__dict__)
            return True
    return False


def open_known_blockers(g: Any, pending: list[tuple[str, int, int, str]]) -> None:
    if ("MT9", 9, 7, "shield1") in pending:
        block = g.block_at("MT9", (10, 5))
        if block and block.eid in {"fakeWall", "fakeWall2"}:
            if g.state["floor"] != "MT9":
                g.fly("MT9")
            g.go_to("MT9", 10, 5, "显式破 MT9 铁盾通道暗墙")


def trigger_mt10_boss(g: Any) -> None:
    g.go_to("MT10", 6, 5, "触发 10F Boss 事件")
    relabel_last(g, "事件", "bossEvent")
    g.set_ground("MT10", (6, 2))
    g.set_ground("MT10", (6, 3))
    for pos, eid in MT10_BOSS_SPAWN:
        g.set_block("MT10", pos, "enemy", eid, 0)


def trigger_mt10_captain_event(g: Any) -> None:
    g.go_to("MT10", 6, 2, "触发骷髅队长剧情事件")
    relabel_last(g, "事件", "captainEvent")


def collect_post_boss_supply(g: Any) -> None:
    apply_mt10_post_boss_map(g)
    g.go_to("MT10", 6, 3, "10F Boss 后补给入口")
    relabel_last(g, "通过", "postBossSupply")
    for fid, x, y, eid in POST_BOSS_SUPPLY:
        if not g.block_at(fid, (x, y)):
            continue
        g.go_to(fid, x, y, f"显式拾取 Boss 后补给 {eid}")


def apply_mt10_post_boss_map(g: Any) -> None:
    raw = json.loads(MT10_POST_BOSS_MAP.read_text(encoding="utf-8-sig"))
    tiles = load_tiles()
    enemies = load_enemies()
    floor = g.floors["MT10"]
    floor.grid = copy.deepcopy(raw["map"])
    floor.blocks.clear()
    for y, row in enumerate(floor.grid):
        for x, tile in enumerate(row):
            if tile == 0:
                continue
            info = tiles.get(int(tile))
            if not info:
                continue
            eid = info["id"]
            kind = classify(eid, info.get("cls", ""), enemies)
            if kind:
                floor.blocks[(x, y)] = Block(kind, eid, int(tile))


def replay_source_step(g: Any, step: dict[str, Any], pending: list[tuple[str, int, int, str]]) -> None:
    action = step.get("action")
    fid = step.get("floor")
    pos = step.get("pos") or [None, None]
    x, y = int(pos[0]), int(pos[1])
    eid = step.get("eid")
    after = step.get("after") or {}
    note = step.get("note") or ""

    if action == "飞行":
        g.fly(fid)
    elif action == "通过" and eid in {"upFloor", "downFloor"} and after.get("floor") and after.get("floor") != fid:
        g.change_by_stair(after["floor"], x, y, note or f"{fid}->{after['floor']}")
    elif action == "事件" and eid == "bossEvent":
        trigger_mt10_boss(g)
    elif action == "事件" and eid == "captainEvent":
        trigger_mt10_captain_event(g)
    elif action == "通过" and eid == "postBossSupply":
        collect_post_boss_supply(g)
    elif action in {"开门", "击杀", "拾取", "通过"}:
        g.go_to(fid, x, y, note)
    else:
        raise RuntimeError(f"unsupported source step action={action} eid={eid} at {fid} x{x}y{y}")

    if action == "开门" and fid == "MT9" and (x, y) == (9, 4):
        add_pending_if_block(g, pending, "MT9", 10, 2, "greenSlime")
    if action == "开门" and fid == "MT9" and (x, y) == (8, 4):
        add_pending_if_block(g, pending, "MT9", 5, 4, "yellowKey")
        add_pending_if_block(g, pending, "MT9", 7, 6, "redSlime")
    if eid != "postBossSupply":
        explicit_old_auto_resources(g, step, pending)


def build_walk() -> dict[str, Any]:
    g = build_game_to_mt7()
    source_steps = read_source_steps()
    warnings: list[str] = []
    pending_auto_targets: list[tuple[str, int, int, str]] = []

    # Source steps are 1-based in the old report. 1..36 are covered by
    # build_game_to_mt7(); 37..136 reaches MT10 post-boss supply.
    for source_index, step in enumerate(source_steps[36:136], start=37):
        replay_source_step(g, step, pending_auto_targets)
        pending_auto_targets[:] = collect_targets_any_order(g, pending_auto_targets)
        expected = comparable_state(step.get("after") or {})
        live = comparable_state(g.snapshot())
        if not pending_auto_targets and expected != live:
            collect_zero_enemy_gold_deficit(g, expected)
            live = comparable_state(g.snapshot())
        if not pending_auto_targets and expected != live:
            warnings.append(
                f"source step {source_index}: expected {expected}, got {live}; "
                f"source_after={source_state_text(step.get('after') or {})}; "
                f"model_after={source_state_text(g.snapshot())}"
            )

    if pending_auto_targets:
        formatted = ", ".join(f"{fid} x{x}y{y} {eid}" for fid, x, y, eid in pending_auto_targets)
        warnings.append(f"unresolved explicit old auto resources: {formatted}")

    steps = [set_auto_step(g.steps[0]["before"])] + [normalize_step(step) for step in g.steps]
    for idx, step in enumerate(steps, 1):
        step["index"] = idx

    return {
        "ok": not g.errors and not warnings,
        "web_verified": False,
        "verification_note": "auto-OFF local MT4->MT10 supply walk; live replay pending",
        "auto_settings": [{"when": "4F start", "auto": dict(AUTO_ON), "reason": "auto ON: auto-bfs pickup/battle/wall"}],
        "source": str(SOURCE_WALK.relative_to(ROOT)).replace("\\", "/"),
        "start": steps[0]["before"],
        "final": steps[-1]["after"],
        "steps": steps,
        "warnings": warnings,
        "errors": g.errors,
    }


def main() -> int:
    data = build_walk()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    final = data["final"]
    print(f"ok={data['ok']}")
    print(f"json={OUT_JSON}")
    print(
        "final="
        f"{final['floor']} x{final['x']}y{final['y']} "
        f"HP={final['hp']} ATK={final['atk']} DEF={final['def']} "
        f"YK={final['yk']} BK={final['bk']} RK={final['rk']} G={final['gold']} "
        f"dmg={final.get('dmg')} door={final.get('yd')}/{final.get('bd')}/{final.get('rd')}"
    )
    print(f"steps={len(data['steps'])}")
    print(f"warnings={len(data['warnings'])}")
    if data["warnings"]:
        print(data["warnings"][0])
    return 0 if data["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
