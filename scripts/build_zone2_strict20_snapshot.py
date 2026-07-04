#!/usr/bin/env python3
"""Build a synthetic 20F snapshot from the strict 4F-20F live walk.

This snapshot is a local bridge input, not a web proof. It removes every map
cell that the strict walk explicitly consumed, plus coordinates mentioned in
auto-pickup notes and a few known event side effects. Coordinates that are only
implied by a gold drift remain auditable instead of being guessed.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.solver.full_search import FLOOR_13_COLLECTED  # noqa: E402

STRICT_WALK = ROOT / "outputs" / "results" / "zone2_2atk1def_4to20_live_strict_walk.json"
STRICT_WEB_RECORD = ROOT / "outputs" / "results" / "strict20_preserve_pickaxe_4to50_web_strict_record_step001_402_nopot_switch.json"
AUTOOFF_MT4_TO20_WALK = ROOT / "outputs" / "results" / "strict20_autooff_mt4_to20_walk.json"
ZONE1_REPLAY = ROOT / "outputs" / "results" / "zone1_current_best_live_auto_item_true_replay.json"
ZONE1_SAVE_SNAPSHOT = ROOT / "outputs" / "results" / "zone1_save100_snapshot.json"
START_SNAPSHOT = ROOT / "outputs" / "results" / "save1_current_snapshot.json"
TEMPLATE_SNAPSHOT = ROOT / "outputs" / "results" / "slot26_snapshot.json"
OUT_JSON = ROOT / "outputs" / "results" / "zone2_2atk1def_strict20_synthetic_snapshot.json"
OUT_MD = ROOT / "outputs" / "reports" / "zone2_2atk1def_strict20_synthetic_snapshot.md"
PLAN = ROOT / "scripts" / "plan_zone3_guide_slot36.py"
SCORE = ROOT / "scripts" / "floor_final_score.py"

COORD_RE = re.compile(r"MT(?P<floor>\d+)\s*x(?P<x>\d+)y(?P<y>\d+)")

MAP_CLEAR_ACTIONS = {
    "击杀",
    "开门",
    "拾取",
    "事件",
    "事件奖励",
    "老人",
    "商人",
    "对话",
    "使用",
}


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


plan = load_module("strict20_plan", PLAN)
score_mod = load_module("strict20_score", SCORE)
BASE_FLOORS: dict[str, Any] | None = None


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def normalize_strict_walk(raw: dict[str, Any]) -> dict[str, Any]:
    """Accept either the older strict walk or the newer strict web record."""

    if "strictWalk" not in raw:
        return raw
    walk = deepcopy(raw["strictWalk"])
    final = raw.get("finalState")
    if final:
        walk["expected_final"] = {
            "floor": final["floor"],
            "x": final["x"],
            "y": final["y"],
            "hp": final["hp"],
            "atk": final["atk"],
            "def": final["def"],
            "gold": final["gold"],
            "yk": final["yk"],
            "bk": final["bk"],
            "rk": final["rk"],
        }
    return walk


def floor_no(fid: str) -> int:
    return int(fid[2:])


def pos_key(fid: str, x: int, y: int) -> tuple[str, int, int]:
    return (fid, int(x), int(y))


def base_floors() -> dict[str, Any]:
    global BASE_FLOORS
    if BASE_FLOORS is None:
        enemies = plan.load_enemy_stats()
        BASE_FLOORS = plan.load_floors({"maps": {}}, enemies)
    return BASE_FLOORS


def is_clearable_position(fid: str, x: int, y: int) -> bool:
    """True when a coordinate should disappear from a saved map.

    Route/search code often marks stairs as "collected" because the hero walked
    over them. Real stairs do not disappear, so snapshot generation must filter
    them out. Fake walls and event walls do disappear after use.
    """

    block = base_floors().get(fid).blocks.get((int(x), int(y))) if fid in base_floors() else None
    if not block:
        return True
    if block.kind == "terrain" and block.eid not in {"fakeWall", "fakeWall2"}:
        return False
    return True


def add_consumed(
    consumed: set[tuple[str, int, int]],
    fid: str | None,
    x: int | None,
    y: int | None,
) -> bool:
    if not fid or x is None or y is None:
        return False
    if not is_clearable_position(fid, int(x), int(y)):
        return False
    consumed.add(pos_key(fid, int(x), int(y)))
    return True


def fixed_prefix_consumed_positions() -> set[tuple[str, int, int]]:
    consumed: set[tuple[str, int, int]] = set()
    for fid, positions in FLOOR_13_COLLECTED.items():
        for x, y in positions:
            add_consumed(consumed, fid, x, y)
    return consumed


def zone1_live_consumed_positions(replay: dict[str, Any]) -> tuple[set[tuple[str, int, int]], list[dict[str, Any]]]:
    consumed: set[tuple[str, int, int]] = set()
    unresolved_auto_gold: list[dict[str, Any]] = []
    enemies = plan.load_enemy_stats()
    clear_actions = {"open", "kill", "take", "event", "trigger"}

    for row in replay.get("logs", []):
        step = row.get("step") or {}
        fid = step.get("fid")
        x = step.get("x")
        y = step.get("y")
        action = step.get("action")
        eid = step.get("eid")
        skipped = bool(row.get("skipped"))
        if skipped or action in clear_actions or (action == "pass" and eid in {"fakeWall", "fakeWall2"}):
            add_consumed(consumed, fid, x, y)

        note = step.get("autoGroupNote") or ""
        note_positions = []
        for match in COORD_RE.finditer(note):
            nf = f"MT{match.group('floor')}"
            nx, ny = int(match.group("x")), int(match.group("y"))
            note_positions.append(pos_key(nf, nx, ny))
            add_consumed(consumed, nf, nx, ny)

        for target in step.get("autoGroupTargets") or []:
            add_consumed(consumed, target.get("fid"), target.get("x"), target.get("y"))

        before = row.get("before") or {}
        after = row.get("after") or {}
        gold_delta = int(after.get("money", before.get("money", 0))) - int(before.get("money", 0))
        expected_gold = 0
        if action == "kill" and eid in enemies:
            expected_gold = int(enemies[eid].get("money", 0))
        drift = gold_delta - expected_gold
        if drift > 0 and not note_positions:
            unresolved_auto_gold.append(
                {
                    "index": row.get("index"),
                    "floor": fid,
                    "pos": [x, y],
                    "action": action,
                    "eid": eid,
                    "gold_delta": gold_delta,
                    "expected_gold": expected_gold,
                    "extra_gold": drift,
                    "text": step.get("text") or "",
                }
            )

    return consumed, unresolved_auto_gold


def explicit_consumed_positions(steps: list[dict[str, Any]]) -> tuple[set[tuple[str, int, int]], list[dict[str, Any]]]:
    """Return map cells definitely consumed by the strict walk.

    Auto-cleared monsters only get removed when their coordinates are present in
    the walk note. If the log only shows extra gold, the unknown source stays in
    the map and is reported as unresolved so it cannot silently affect scoring.
    """

    consumed: set[tuple[str, int, int]] = set()
    note_positions: set[tuple[str, int, int]] = set()
    unresolved_auto_gold: list[dict[str, Any]] = []

    for idx, step in enumerate(steps, 1):
        fid = step.get("floor")
        pos = step.get("pos") or []
        action = step.get("action")
        eid = step.get("eid")
        note = step.get("note") or ""
        if fid and len(pos) == 2:
            if action in MAP_CLEAR_ACTIONS or (action == "通过" and eid in {"fakeWall", "fakeWall2", "postBossSupply"}):
                add_consumed(consumed, fid, pos[0], pos[1])
            if action == "校验" and eid in {"specialDoor", "steelDoor"}:
                add_consumed(consumed, fid, pos[0], pos[1])

        for match in COORD_RE.finditer(note):
            nf = f"MT{match.group('floor')}"
            key = pos_key(nf, int(match.group("x")), int(match.group("y")))
            if add_consumed(consumed, nf, int(match.group("x")), int(match.group("y"))):
                note_positions.add(key)

        before = step.get("before") or {}
        after = step.get("after") or {}
        gold_delta = int(after.get("gold", before.get("gold", 0))) - int(before.get("gold", 0))
        if "自动" in note and gold_delta > 0 and not any(COORD_RE.finditer(note)):
            unresolved_auto_gold.append(
                {
                    "step": idx,
                    "floor": fid,
                    "pos": pos,
                    "action": action,
                    "eid": eid,
                    "gold_delta": gold_delta,
                    "note": note,
                }
            )

    # Event side effects that are required for later movement.
    for fid, x, y in [
        ("MT10", 1, 3),
        ("MT10", 2, 3),
        ("MT10", 3, 3),
        ("MT10", 9, 3),
        ("MT10", 10, 3),
        ("MT10", 11, 3),
        ("MT10", 1, 4),
        ("MT10", 2, 4),
        ("MT10", 3, 4),
        ("MT10", 9, 4),
        ("MT10", 10, 4),
        ("MT10", 11, 4),
        ("MT17", 2, 7),
        ("MT17", 2, 4),
        ("MT20", 6, 3),
        ("MT20", 6, 5),
        ("MT20", 6, 6),
        ("MT20", 6, 8),
        ("MT20", 6, 9),
    ]:
        add_consumed(consumed, fid, x, y)
    return consumed, unresolved_auto_gold


def base_grid(fid: str) -> list[list[int]]:
    raw = plan.load_base_floor(fid)
    grid = raw.get("map") or raw.get("m")
    if not grid:
        raise ValueError(f"{fid} missing map")
    return deepcopy(grid)


def snapshot_floor_limit(snapshot: dict[str, Any] | None) -> int | None:
    if not snapshot:
        return None
    floor_id = snapshot.get("floorId")
    if isinstance(floor_id, str) and floor_id.startswith("MT"):
        return floor_no(floor_id)
    return None


def snapshot_covers_floor(snapshot: dict[str, Any] | None, fid: str) -> bool:
    limit = snapshot_floor_limit(snapshot)
    if limit is None:
        return False
    return floor_no(fid) <= limit


def initial_grid(
    fid: str,
    start_snapshot: dict[str, Any] | None,
    zone1_save_snapshot: dict[str, Any] | None,
) -> list[list[int]]:
    base = base_grid(fid)
    if snapshot_covers_floor(zone1_save_snapshot, fid):
        return plan.decode_snapshot_grid(fid, base, zone1_save_snapshot)
    if not start_snapshot:
        return base
    return plan.decode_snapshot_grid(fid, base, start_snapshot)


def changed_grid(
    fid: str,
    consumed: set[tuple[str, int, int]],
    start_snapshot: dict[str, Any] | None,
    zone1_save_snapshot: dict[str, Any] | None,
) -> list[list[int]] | None:
    base = base_grid(fid)
    grid = initial_grid(fid, start_snapshot, zone1_save_snapshot)
    for cfid, x, y in sorted(consumed):
        if cfid != fid:
            continue
        if y < 0 or y >= len(grid) or x < 0 or x >= len(grid[y]):
            continue
        if grid[y][x] != 0:
            grid[y][x] = 0
    if grid == base:
        return None
    return grid


def compact_snapshot_map(fid: str, grid: list[list[int]]) -> dict[str, Any]:
    base = base_grid(fid)
    compact: list[Any] = []
    for y, row in enumerate(grid):
        out_row: list[int] = []
        row_changed = False
        for x, value in enumerate(row):
            if value == base[y][x]:
                out_row.append(-1)
            else:
                out_row.append(value)
                row_changed = True
        compact.append(out_row if row_changed else -1)
    return {"map": compact}


def build_snapshot(
    strict_walk: dict[str, Any],
    template: dict[str, Any],
    times1: int,
    *,
    strict_walk_path: Path = STRICT_WALK,
    zone1_replay: dict[str, Any] | None = None,
    zone1_save_snapshot: dict[str, Any] | None = None,
    start_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    final = strict_walk["expected_final"]
    fixed_consumed = fixed_prefix_consumed_positions()
    zone1_consumed: set[tuple[str, int, int]] = set()
    zone1_unresolved: list[dict[str, Any]] = []
    if zone1_replay:
        zone1_consumed, zone1_unresolved = zone1_live_consumed_positions(zone1_replay)
    zone2_consumed, zone2_unresolved = explicit_consumed_positions(strict_walk["steps"])
    consumed = fixed_consumed | zone1_consumed | zone2_consumed
    applied_consumed: set[tuple[str, int, int]] = set()
    zone1_save_floors: list[str] = []

    maps: dict[str, Any] = {}
    for n in range(1, 21):
        fid = f"MT{n}"
        if snapshot_covers_floor(zone1_save_snapshot, fid):
            zone1_save_floors.append(fid)
            # The save100 map is already the exact live result of the 1F-10F
            # route, including 0-damage auto-clears and generated 10F rewards.
            # Only apply actions from the strict post-save walk on top of it.
            consumed_for_floor = {pos for pos in zone2_consumed if pos[0] == fid}
        else:
            consumed_for_floor = {pos for pos in consumed if pos[0] == fid}
        applied_consumed.update(consumed_for_floor)
        grid = changed_grid(fid, consumed_for_floor, start_snapshot, zone1_save_snapshot)
        if grid is not None:
            maps[fid] = compact_snapshot_map(fid, grid)

    flags = deepcopy(template.get("hero", {}).get("flags", {}))
    flags["times1"] = times1
    flags["money1"] = plan.shop_cost(times1)
    visited = {f"MT{i}": True for i in range(1, 21)}
    flags["__visited__"] = visited

    constants = deepcopy(template.get("hero", {}).get("constants", {}))
    constants.update({"fly": 1, "book": 1, "wand": 1, "cross": 1})

    hero = {
        "x": final["x"],
        "y": final["y"],
        "hp": final["hp"],
        "atk": final["atk"],
        "def": final["def"],
        "money": final["gold"],
        "yk": final["yk"],
        "bk": final["bk"],
        "rk": final["rk"],
        "tools": deepcopy(template.get("hero", {}).get("tools", {})),
        "constants": constants,
        "flags": flags,
    }
    hero["tools"]["yellowKey"] = final["yk"]
    if final["bk"]:
        hero["tools"]["blueKey"] = final["bk"]
    else:
        hero["tools"].pop("blueKey", None)
    if final["rk"]:
        hero["tools"]["redKey"] = final["rk"]
    else:
        hero["tools"].pop("redKey", None)

    return {
        "slot": "synthetic-zone2-strict20",
        "exportedAt": "local-synthetic",
        "floorId": final["floor"],
        "hero": hero,
        "maps": maps,
        "values": deepcopy(template.get("values", {})),
        "hard": template.get("hard", 0),
        "route": [],
        "version": template.get("version"),
        "guid": template.get("guid"),
        "time": template.get("time", 0),
        "_meta": {
            "source_walk": str(strict_walk_path.relative_to(ROOT)),
            "source_zone1_live_replay": str(ZONE1_REPLAY.relative_to(ROOT)) if zone1_replay else None,
            "source_zone1_save_snapshot": str(ZONE1_SAVE_SNAPSHOT.relative_to(ROOT)) if zone1_save_snapshot else None,
            "source_start_snapshot": str(START_SNAPSHOT.relative_to(ROOT)) if start_snapshot else None,
            "consumed_position_count": len(applied_consumed),
            "raw_consumed_position_count": len(consumed),
            "consumed_by_source": {
                "fixed_1_3_prefix": len(fixed_consumed),
                "zone1_live_replay": len(zone1_consumed),
                "zone2_strict_walk": len(zone2_consumed),
            },
            "zone1_save_overlay_floors": zone1_save_floors,
            "map_override_floors": sorted(maps, key=floor_no),
            "unresolved_auto_gold_steps": zone2_unresolved if zone1_save_snapshot else zone1_unresolved + zone2_unresolved,
            "times1_inferred_from_shop12_buys": times1,
        },
    }


def init_replay(snapshot: dict[str, Any]) -> Any:
    enemies = plan.load_enemy_stats()
    floors = plan.load_floors(snapshot, enemies)
    g = plan.GuideReplay(snapshot, floors, enemies)
    g.state["visited"] = {f"MT{i}" for i in range(1, floor_no(snapshot["floorId"]) + 1)}
    return g


def write_report(snapshot: dict[str, Any], score: dict[str, Any], out_json: Path, out_md: Path) -> None:
    meta = snapshot["_meta"]
    hero = snapshot["hero"]
    unresolved = meta["unresolved_auto_gold_steps"]
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 严格 4-20 后 20F 合成快照",
        "",
        "## 结论",
        f"- 快照：`{out_json.relative_to(ROOT)}`",
        f"- 1-3F/4F 起点底图：`{meta.get('source_start_snapshot') or 'FLOOR_13_COLLECTED fallback'}`",
        f"- 1区 live replay：`{meta.get('source_zone1_live_replay') or '-'}`",
        f"- 起点状态：`MT20 x{hero['x']}y{hero['y']} HP={hero['hp']} ATK={hero['atk']} DEF={hero['def']} YK={hero['yk']} BK={hero['bk']} RK={hero['rk']} G={hero['money']}`",
        f"- 商店 flags：`times1={hero['flags']['times1']}`，下一次价格 `money1={hero['flags']['money1']}`",
        f"- 地图覆盖楼层：`{', '.join(meta['map_override_floors'])}`，显式清理格 `{meta['consumed_position_count']}` 个",
        f"- 清理来源计数：`{meta.get('consumed_by_source')}`",
        "",
        "## final-score 规则",
        "- 函数：`scripts/floor_final_score.py::current_floor_and_below_final_score`。",
        "- 已经被路线击杀或网页自动清掉的 0 伤怪如果有坐标，会从 `floor.blocks` 移除，它的金币只存在于当前 G。",
        "- 尚未击杀的 0 伤怪仍留在 `floor.blocks`，只在剩余资源里按金币价值计入。",
        "- 只有金币漂移但没有坐标的自动清怪不做猜测，列为待实机地图确认；正式 walk 需要用实机地图状态消除这些不确定项。",
        f"- 当前层及以下估算：stock={score['stock_score']:g}，items={score['item_value_hp']:g}，zeroG={score['zero_damage_monster_value_hp']:g}，final-score<={score['floor_limit']}={score['final_score']:g}",
        "",
        "## 待实机确认的自动金币",
    ]
    if unresolved:
        lines.append("| step | floor | pos | action | eid | gold | note |")
        lines.append("| ---: | --- | --- | --- | --- | ---: | --- |")
        for row in unresolved:
            pos = row.get("pos") or []
            pos_text = f"x{pos[0]}y{pos[1]}" if len(pos) == 2 else "-"
            note = (row.get("note") or "").replace("|", "/")
            step_id = row.get("step", row.get("index", "-"))
            gold = row.get("gold_delta", row.get("extra_gold", ""))
            lines.append(
                f"| {step_id} | {row.get('floor')} | {pos_text} | {row.get('action')} | "
                f"{row.get('eid') or ''} | {gold} | {note or row.get('text', '')} |"
            )
    else:
        lines.append("- 无。")
    lines.append("")
    out_md.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    # Default to the autooff MT4-20 walk so the snapshot's final state matches the
    # walk actually used by the stitched 4-50 walk (yk=1). The STRICT_WEB_RECORD
    # is a stale web recording (yk=0) that predates the autooff walk fix and
    # caused a 1-YK mismatch at the MT20 postBossSupply step.
    default_strict_walk = AUTOOFF_MT4_TO20_WALK if AUTOOFF_MT4_TO20_WALK.exists() else (STRICT_WEB_RECORD if STRICT_WEB_RECORD.exists() else STRICT_WALK)
    parser.add_argument("--strict-walk", type=Path, default=default_strict_walk)
    parser.add_argument("--zone1-replay", type=Path, default=ZONE1_REPLAY)
    parser.add_argument("--zone1-save-snapshot", type=Path, default=ZONE1_SAVE_SNAPSHOT)
    parser.add_argument("--start-snapshot", type=Path, default=START_SNAPSHOT)
    parser.add_argument("--template", type=Path, default=TEMPLATE_SNAPSHOT)
    parser.add_argument("--times1", type=int, default=3, help="Inferred shop count after the 12F 2ATK1DEF buys.")
    parser.add_argument("--out-json", type=Path, default=OUT_JSON)
    parser.add_argument("--out-md", type=Path, default=OUT_MD)
    args = parser.parse_args()

    strict_walk = normalize_strict_walk(read_json(args.strict_walk))
    zone1_replay = read_json(args.zone1_replay) if args.zone1_replay and args.zone1_replay.exists() else None
    zone1_save_snapshot = read_json(args.zone1_save_snapshot) if args.zone1_save_snapshot and args.zone1_save_snapshot.exists() else None
    start_snapshot = read_json(args.start_snapshot) if args.start_snapshot and args.start_snapshot.exists() else None
    template = read_json(args.template)
    snapshot = build_snapshot(
        strict_walk,
        template,
        args.times1,
        strict_walk_path=args.strict_walk,
        zone1_replay=zone1_replay,
        zone1_save_snapshot=zone1_save_snapshot,
        start_snapshot=start_snapshot,
    )
    g = init_replay(snapshot)
    final_score = score_mod.current_floor_and_below_final_score(g, 20)
    write_report(snapshot, final_score, args.out_json, args.out_md)
    print(f"wrote {args.out_json}")
    print(f"wrote {args.out_md}")
    print(
        "state",
        f"MT20 x{snapshot['hero']['x']}y{snapshot['hero']['y']}",
        f"HP={snapshot['hero']['hp']}",
        f"ATK={snapshot['hero']['atk']}",
        f"DEF={snapshot['hero']['def']}",
        f"YK={snapshot['hero']['yk']}",
        f"G={snapshot['hero']['money']}",
        f"times1={snapshot['hero']['flags']['times1']}",
        f"score20={final_score['final_score']:g}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
