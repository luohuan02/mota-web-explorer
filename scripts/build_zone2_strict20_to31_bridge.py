#!/usr/bin/env python3
"""Replay the strict 20F snapshot through the 20F-31F bridge.

The bridge uses normal map movement plus the explicit 29F thief and 30F
six-slime door events. It writes a 31F snapshot that can be passed to the zone-3
search/report scripts with ``--snapshot``.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
IN_SNAPSHOT = ROOT / "outputs" / "results" / "zone2_2atk1def_strict20_synthetic_snapshot.json"
OUT_JSON = ROOT / "outputs" / "results" / "zone2_2atk1def_strict20_to31_bridge_snapshot.json"
OUT_WALK = ROOT / "outputs" / "results" / "zone2_2atk1def_strict20_to31_bridge_walk.json"
OUT_MD = ROOT / "outputs" / "reports" / "zone2_2atk1def_strict20_to31_bridge.md"
PLAN = ROOT / "scripts" / "plan_zone3_guide_slot36.py"
SCORE = ROOT / "scripts" / "floor_final_score.py"


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


plan = load_module("strict20_bridge_plan", PLAN)
score_mod = load_module("strict20_bridge_score", SCORE)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def floor_no(fid: str) -> int:
    return int(fid[2:])


def base_grid(fid: str) -> list[list[int]]:
    raw = plan.load_base_floor(fid)
    grid = raw.get("map") or raw.get("m")
    if not grid:
        raise ValueError(f"{fid} missing map")
    return deepcopy(grid)


def decoded_source_grid(fid: str, snapshot: dict[str, Any]) -> list[list[int]]:
    return plan.decode_snapshot_grid(fid, base_grid(fid), snapshot)


def compact_map(fid: str, grid: list[list[int]]) -> dict[str, Any] | None:
    base = base_grid(fid)
    compact: list[Any] = []
    changed = False
    for y, row in enumerate(grid):
        row_out: list[int] = []
        row_changed = False
        for x, value in enumerate(row):
            if value == base[y][x]:
                row_out.append(-1)
            else:
                row_out.append(value)
                row_changed = True
                changed = True
        compact.append(row_out if row_changed else -1)
    if not changed:
        return None
    return {"map": compact}


def state_text(g: Any) -> str:
    s = g.state
    return (
        f"HP={s['hp']} ATK={s['atk']} DEF={s['def']} "
        f"YK={s['yk']} BK={s['bk']} RK={s['rk']} G={s['gold']} "
        f"{s['floor']} x{s['x']}y{s['y']} dmg={s['dmg']} door={s['yd']}/{s['bd']}/{s['rd']} "
        f"times1={s['times1']}"
    )


def init_replay(snapshot: dict[str, Any]) -> Any:
    enemies = plan.load_enemy_stats()
    floors = plan.load_floors(snapshot, enemies)
    g = plan.GuideReplay(snapshot, floors, enemies)
    flags = snapshot.get("hero", {}).get("flags", {})
    visited = {fid for fid, ok in flags.get("__visited__", {}).items() if ok}
    if not visited:
        visited = {f"MT{i}" for i in range(1, floor_no(snapshot["floorId"]) + 1)}
    visited.add(snapshot["floorId"])
    g.state["visited"] = visited
    return g


def mark_visited(g: Any, fid: str) -> None:
    g.state.setdefault("visited", set()).add(fid)


def up_floor_pos(g: Any, fid: str) -> tuple[int, int]:
    rows = [pos for pos, block in g.floors[fid].blocks.items() if block.kind == "terrain" and block.eid == "upFloor"]
    if not rows:
        raise RuntimeError(f"{fid} has no upFloor")
    return sorted(rows)[0]


def climb_one(g: Any, fid: str, note: str) -> None:
    target = up_floor_pos(g, fid)
    g.go_to(fid, target[0], target[1], note)
    if g.errors:
        return
    next_fid = f"MT{floor_no(fid) + 1}"
    g.transition(next_fid, target[0], target[1], f"{fid} -> {next_fid}")
    mark_visited(g, next_fid)


def event_mt29_thief(g: Any) -> None:
    g.go_to("MT29", 6, 2, "29F thief opens the tunnel")
    if g.errors:
        return
    before = g.snapshot()
    g.set_ground("MT29", (6, 2))
    g.set_ground("MT29", (6, 3))
    g.set_block("MT2", (10, 11), "npc", "thief", 123)
    g.record("事件", (6, 2), "thief", before, "29F 小偷开暗道，并转到 MT2 x10y11")


def event_mt30_six_slimes(g: Any) -> None:
    for pos in [(3, 5), (4, 5), (5, 5), (7, 5), (8, 5), (9, 5)]:
        g.go_to("MT30", pos[0], pos[1], "30F six-slime door")
        if g.errors:
            return
    before = g.snapshot()
    g.set_ground("MT30", (6, 4))
    g.record("事件开门", (6, 4), "specialDoor", before, "30F 六个史莱姆清完，机关门打开")


def collect_mt20_post_boss_supply(g: Any, auto_item: str = "nopotion", transition_to: str | None = None) -> None:
    """Model the live auto-pickup burst while walking from vampire to stairs.

    If transition_to is set, also perform the up-floor transition (live reaches
    the stair at x6y1 and triggers the floor change in the same click that
    collects the post-boss supply).
    """
    if g.state["floor"] != "MT20":
        return
    before = g.snapshot()
    g.state["atk"] += 6
    g.state["def"] += 6
    g.state["yk"] += 3
    consumed_positions = [
        (5, 4), (6, 4), (7, 4),
        (4, 5), (4, 6), (4, 7),
        (8, 5), (8, 6), (8, 7),
    ]
    if auto_item == "true":
        g.state["hp"] += 1200
        consumed_positions += [(5, 8), (6, 8), (7, 8)]
    for pos in consumed_positions:
        g.set_ground("MT20", pos)
    if auto_item != "true":
        for pos in [(5, 8), (6, 8), (7, 8)]:
            if not g.block_at("MT20", pos):
                g.set_block("MT20", pos, "item", "bluePotion", 32)
    note = "MT20 post-boss auto collects 3 yellow keys and 3 red/blue gems; item=nopotion keeps 3 blue potions on map"
    if auto_item == "true":
        note = "MT20 post-boss auto collects 3 yellow keys, 3 red/blue gems, and 3 blue potions"
    g.state["x"], g.state["y"] = 6, 1
    if transition_to:
        # Transition to the next floor WITHOUT keeping the passive "换层" step:
        # live triggers the floor change via the single postBossSupply click at
        # x6y1 (the stair), so the walk should have ONE click step (拾取) whose
        # after-state is on MT21. g.transition records a "换层" step; pop it so
        # only the 拾取 step below remains.
        g.transition(transition_to, 6, 1, f"MT20 -> {transition_to}")
        if g.steps and g.steps[-1].get("action") == "换层":
            g.steps.pop()
        note += f"; 上楼到 {transition_to}"
    g.record(
        "拾取",
        (6, 1),
        "postBossSupply",
        before,
        note,
    )


def run_bridge(snapshot: dict[str, Any], auto_item: str = "nopotion") -> Any:
    g = init_replay(snapshot)
    g.set_segment("20F-31F bridge")
    # postBossSupply bulk step models the live post-vampire auto-pickup burst
    # (3 yellow keys + 3 gems + 3 blue potions) AND the floor change to MT21
    # (live triggers the up-floor when reaching the stair at x6y1). The bulk
    # records the final state on MT21 so the replayer matches live (which is
    # already on MT21 after the pickup click).
    collect_mt20_post_boss_supply(g, auto_item=auto_item, transition_to="MT21")
    for n in range(21, 29):
        climb_one(g, f"MT{n}", f"MT{n} 上楼")
        if g.errors:
            return g
    if g.state["floor"] != "MT29":
        return g
    # First attempt documents the true blocker, then the legal thief event opens it.
    probe = deepcopy(g)
    probe.go_to("MT29", *up_floor_pos(probe, "MT29"), "probe direct 29F up")
    if probe.errors:
        g.warnings.append(probe.errors[-1])
    event_mt29_thief(g)
    if g.errors:
        return g
    climb_one(g, "MT29", "MT29 小偷开路后上楼")
    if g.errors:
        return g
    event_mt30_six_slimes(g)
    if g.errors:
        return g
    climb_one(g, "MT30", "MT30 机关门后上楼")
    return g


def snapshot_from_replay(source: dict[str, Any], g: Any) -> dict[str, Any]:
    state = g.snapshot()
    maps: dict[str, Any] = {}
    for n in range(1, 32):
        fid = f"MT{n}"
        if fid not in g.floors:
            continue
        source_grid = decoded_source_grid(fid, source)
        grid = deepcopy(g.floors[fid].grid)
        base = base_grid(fid)
        # Terrain stairs are pass-through in the local model but not consumed in
        # the real game, so restore them before serializing the snapshot.
        for y, row in enumerate(base):
            for x, tile in enumerate(row):
                info = plan.load_tile_mapping().get(tile)
                if info and info.get("id") in {"upFloor", "downFloor"}:
                    grid[y][x] = source_grid[y][x]
        encoded = compact_map(fid, grid)
        if encoded is not None:
            maps[fid] = encoded

    flags = deepcopy(source.get("hero", {}).get("flags", {}))
    # item="nopotion": the tail route (MT31-50) was planned preserving potions
    # for 3F/4F. item=true would auto-pick potions early and break the tail route
    # (it stops at MT28). Keep nopotion so the tail auto_sweep matches the route
    # planning; potions are picked via explicit walk steps instead.
    flags["__auto__"] = {"battle": True, "item": "nopotion", "wall": True}
    visited = {f"MT{i}": True for i in range(1, 32)}
    flags["__visited__"] = visited
    flags["times1"] = int(state["times1"])
    flags["money1"] = plan.shop_cost(int(state["times1"]))

    hero = deepcopy(source["hero"])
    hero.update(
        {
            "x": state["x"],
            "y": state["y"],
            "hp": state["hp"],
            "atk": state["atk"],
            "def": state["def"],
            "money": state["gold"],
            "yk": state["yk"],
            "bk": state["bk"],
            "rk": state["rk"],
            "flags": flags,
        }
    )
    hero.setdefault("tools", {})["yellowKey"] = state["yk"]
    if state["bk"]:
        hero["tools"]["blueKey"] = state["bk"]
    else:
        hero["tools"].pop("blueKey", None)
    if state["rk"]:
        hero["tools"]["redKey"] = state["rk"]
    else:
        hero["tools"].pop("redKey", None)

    return {
        **{k: deepcopy(v) for k, v in source.items() if k not in {"floorId", "hero", "maps", "_meta"}},
        "slot": "synthetic-zone2-strict20-to31",
        "floorId": state["floor"],
        "hero": hero,
        "maps": maps,
        "_meta": {
            "source_snapshot": str(IN_SNAPSHOT.relative_to(ROOT)),
            "bridge_state": state,
            "bridge_steps": len(g.steps),
            "bridge_warnings": list(g.warnings),
            "auto_item": flags["__auto__"]["item"],
        },
    }


def write_outputs(source: dict[str, Any], g: Any, snapshot: dict[str, Any], args: argparse.Namespace) -> None:
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_walk.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.parent.mkdir(parents=True, exist_ok=True)

    args.out_json.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    score31 = score_mod.current_floor_and_below_final_score(g, 31)
    walk = {
        "ok": not g.errors,
        "source_snapshot": str(args.snapshot),
        "out_snapshot": str(args.out_json),
        "final": g.snapshot(),
        "state_text": state_text(g),
        "current_floor_final_score": score31,
        "errors": list(g.errors),
        "warnings": list(g.warnings),
        "steps": g.steps,
    }
    args.out_walk.write_text(json.dumps(walk, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 严格 20F 到 31F 桥接",
        "",
        "## 结论",
        f"- 结果：`{'通过' if not g.errors else '未通过'}`",
        f"- 终点：`{state_text(g)}`",
        f"- 输出快照：`{args.out_json.relative_to(ROOT)}`",
        f"- 当前层及以下 final-score：`{score31['final_score']:g}` (stock={score31['stock_score']:g}, remaining={score31['remaining_value_hp']:g})",
        f"- 重要道具：held={score31['held_tool_counts'] or {}}, map={score31['map_tool_counts'] or {}}",
        "",
        "## 桥接事件",
        "- 29F：先直接走上楼口会失败；正常点击小偷后，MT29 x6y3 暗道打开，小偷转到 MT2 x10y11。",
        "- 30F：清 6 个史莱姆后，MT30 x6y4 机关门打开，再上 31F。",
        "",
    ]
    if g.warnings:
        lines.append("## Warnings")
        lines.extend(f"- {w}" for w in g.warnings)
        lines.append("")
    if g.errors:
        lines.append("## Errors")
        lines.extend(f"- {e}" for e in g.errors)
        lines.append("")
    lines.append("## Walk")
    for i, step in enumerate(g.steps, 1):
        pos = step.get("pos") or ["?", "?"]
        delta = f" [{step['delta']}]" if step.get("delta") else ""
        note = f" ({step.get('note')})" if step.get("note") else ""
        lines.append(
            f"{i:03d}. {step.get('floor')} x{pos[0]}y{pos[1]} {step.get('action')} "
            f"{step.get('eid') or ''}{delta}{note}".rstrip()
        )
    args.out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", type=Path, default=IN_SNAPSHOT)
    parser.add_argument("--out-json", type=Path, default=OUT_JSON)
    parser.add_argument("--out-walk", type=Path, default=OUT_WALK)
    parser.add_argument("--out-md", type=Path, default=OUT_MD)
    parser.add_argument("--auto-item", choices=["nopotion", "true"], default="nopotion")
    args = parser.parse_args()

    source = read_json(args.snapshot)
    g = run_bridge(source, auto_item=args.auto_item)
    snapshot = snapshot_from_replay(source, g)
    write_outputs(source, g, snapshot, args)
    print(f"ok={not g.errors}")
    print(state_text(g))
    print(f"snapshot={args.out_json}")
    print(f"walk={args.out_walk}")
    print(f"md={args.out_md}")
    if g.errors:
        for error in g.errors:
            print(f"error: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
