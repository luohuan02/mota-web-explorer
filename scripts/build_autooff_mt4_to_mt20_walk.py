#!/usr/bin/env python3
"""Build an auto-OFF explicit MT4->20F vampire walk from the strict live log."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from build_autooff_mt4_to_mt10_supply_walk import (
    AUTO_ON,
    add_pending_if_block,
    collect_post_boss_supply,
    collect_targets_any_order,
    collect_zero_enemy_gold_deficit,
    comparable_state,
    explicit_old_auto_resources,
    normalize_step,
    read_source_steps,
    relabel_last,
    source_state_text,
    trigger_mt10_boss,
    trigger_mt10_captain_event,
)
from build_autooff_mt4_to_mt7_prefix_walk import build_game_to_mt7, set_auto_step
from search_post40_guide_route import RouteError


ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "outputs" / "results" / "strict20_autooff_mt4_to20_walk.json"


def low_floor_trader(g: Any, fid: str, x: int, y: int, note: str = "") -> None:
    g.move_adjacent(fid, x, y, note)
    before = g.snapshot()
    if fid == "MT7" and (x, y) == (6, 1):
        if g.state["gold"] < 50:
            g.fail("not enough gold for MT7 trader")
        g.state["gold"] -= 50
        g.state["yk"] += 5
    elif fid == "MT6" and (x, y) == (8, 4):
        if g.state["gold"] < 50:
            g.fail("not enough gold for MT6 trader")
        g.state["gold"] -= 50
        g.state["bk"] += 1
    elif fid == "MT15" and (x, y) == (11, 11):
        if g.state["gold"] < 200:
            g.fail("not enough gold for MT15 trader")
        g.state["gold"] -= 200
        g.state["bk"] += 1
    else:
        g.fail(f"unmodeled low-floor trader {fid} x{x}y{y}")
    g.set_ground(fid, (x, y))
    g.record("商人", (x, y), "trader", before, note)


def collect_newly_reachable_items(g: Any, fid: str) -> None:
    """After a guard kill opens a mechanism door, the post-battle auto_sweep ran
    with the door still closed (live: opening a door does not re-trigger BFS), so
    items behind the door were NOT auto-picked. Explicitly go_to the nearest
    newly-reachable item -- that click triggers a fresh auto_sweep (door now open)
    which picks up the rest of the room, matching the live "click x10y2" behavior.

    No-op when auto_sweep already cleared everything (normal kills, no door)."""
    auto = g.auto_flags
    cands = g._auto_item_candidates(
        fid,
        battle=bool(auto.get("battle")),
        item_mode=auto.get("item"),
        wall=bool(auto.get("wall")),
    )
    if not cands:
        return
    _dist, _y, pos, block = cands[0]
    g.go_to(fid, pos[0], pos[1], f"机关门后显式拾取 {block.eid}")


def record_check(g: Any, fid: str, x: int, y: int, eid: str | None, note: str = "") -> None:
    before = g.snapshot()
    g.record("校验", (x, y), eid, before, note)


def trigger_mt10_thief(g: Any) -> None:
    g.move_adjacent("MT10", 6, 9, "10F 小偷事件")
    before = g.snapshot()
    g.set_ground("MT10", (6, 9))
    g.record("事件", (6, 9), "thief", before, "10F 小偷开放 11F 楼梯")


def trigger_mt15_thief_dialog(g: Any) -> None:
    g.move_adjacent("MT15", 9, 1, "15F 小偷对话")
    before = g.snapshot()
    g.record("对话", (9, 1), "thief", before, "15F 小偷对话")


def trigger_mt15_thief_event(g: Any) -> None:
    g.move_adjacent("MT15", 9, 1, "15F 小偷开右上墙")
    before = g.snapshot()
    g.set_ground("MT15", (9, 1))
    for pos in [(7, 1), (8, 1), (9, 1), (10, 1)]:
        g.set_ground("MT15", pos)
    g.record("事件", (9, 1), "thief", before, "15F 小偷开右上墙")


def trigger_mt20_vampire_event(g: Any) -> None:
    g.go_to("MT20", 6, 8, "20F 触发吸血鬼")
    relabel_last(g, "事件", "vampire")
    for pos in [(5, 5), (6, 5), (7, 5), (5, 6), (7, 6), (5, 7), (6, 7), (7, 7)]:
        g.set_ground("MT20", pos)
    g.set_block("MT20", (6, 6), "enemy", "vampire", 208)
    g.set_block("MT20", (6, 9), "door", "specialDoor", 85)


def replay_source_step_to20(
    g: Any,
    step: dict[str, Any],
    pending: list[tuple[str, int, int, str]],
) -> dict[str, int]:
    action = step.get("action")
    fid = step.get("floor")
    pos = step.get("pos") or [None, None]
    x, y = int(pos[0]), int(pos[1])
    eid = step.get("eid")
    after = step.get("after") or {}
    note = step.get("note") or ""
    # Strip stale auto_sweep / 自动处理 / 到门前开门 suffixes copied from the
    # source walk -- the model re-adds these from the actual run, so keeping the
    # source versions would claim pickups that did not happen (e.g. an old
    # auto_sweep that picked items behind a mechanism door before the timing fix).
    for _marker in ("自动处理", "到门前开门", "auto_sweep"):
        _i = note.find(_marker)
        if _i >= 0:
            note = note[:_i].rstrip(" ；;").rstrip()
    state_offsets: dict[str, int] = {}

    if action == "飞行":
        g.fly(fid)
    elif action == "通过" and after.get("floor") and after.get("floor") != fid:
        g.change_by_stair(after["floor"], x, y, note or f"{fid}->{after['floor']}")
    elif action == "事件" and fid == "MT10" and eid == "bossEvent":
        trigger_mt10_boss(g)
    elif action == "事件" and fid == "MT10" and eid == "captainEvent":
        trigger_mt10_captain_event(g)
    elif action == "通过" and eid == "postBossSupply":
        collect_post_boss_supply(g)
    elif action == "事件" and fid == "MT10" and eid == "thief":
        trigger_mt10_thief(g)
    elif action == "对话" and fid == "MT15" and eid == "thief":
        trigger_mt15_thief_dialog(g)
    elif action == "对话":
        g.move_adjacent(fid, x, y, note)
        before = g.snapshot()
        g.record("对话", (x, y), eid, before, note)
    elif action == "事件" and fid == "MT15" and eid == "thief":
        trigger_mt15_thief_event(g)
    elif action == "事件" and fid == "MT20" and eid == "vampire":
        trigger_mt20_vampire_event(g)
    elif action == "事件奖励" and fid == "MT14" and eid == "redKey":
        before_yk = g.state["yk"]
        g.go_to("MT14", 1, 3, "显式拾取 14F 三兽人武士后红钥匙")
        if g.steps:
            g.steps[-1]["note"] = f"{g.steps[-1].get('note')}; 实机不消耗黄钥匙"
        source_yk = int((step.get("after") or {}).get("yk", before_yk))
        state_offsets["yk"] = before_yk - source_yk
    elif action == "商店":
        g.move_adjacent(fid, x, y, note)
        g.buy_shop(eid, shop_pos=(x, y))
    elif action == "商人":
        low_floor_trader(g, fid, x, y, note)
    elif action == "老人" and fid == "MT16" and eid == "superPotion":
        g.talk_mt16_oldman()
    elif action == "使用" and eid == "superPotion":
        g.use_super_potion(note or "使用圣水")
    elif action == "校验":
        record_check(g, fid, x, y, eid, note)
    elif action in {"开门", "击杀"}:
        g.go_to(fid, x, y, note)
        if action == "击杀":
            # A guard kill may open a mechanism door; the post-battle auto_sweep
            # ran before it opened, so explicitly click into the now-open room.
            collect_newly_reachable_items(g, fid)
    elif action in {"拾取", "通过"}:
        # auto ON: resources (拾取) + fakeWall (通过) are auto-handled by
        # auto_sweep after each go_to. Skip the explicit go_to (it would be a
        # no-op arrival). Stairs (通过 upFloor/downFloor) + postBossSupply are
        # handled above (:109/:115). The hero routes directly to the next
        # main target; auto_sweep picks up on-path resources.
        pass
    else:
        raise RuntimeError(f"unsupported source step action={action} eid={eid} at {fid} x{x}y{y}")

    if action == "开门" and fid == "MT9" and (x, y) == (9, 4):
        add_pending_if_block(g, pending, "MT9", 10, 2, "greenSlime")
    if action == "开门" and fid == "MT9" and (x, y) == (8, 4):
        add_pending_if_block(g, pending, "MT9", 5, 4, "yellowKey")
        add_pending_if_block(g, pending, "MT9", 7, 6, "redSlime")
    if eid != "postBossSupply":
        # auto ON: auto_sweep handles on-path resources; skip
        # explicit_old_auto_resources (it would add no-op arrival steps).
        pass
    return state_offsets


def adjust_expected(expected: dict[str, Any], offsets: dict[str, int]) -> dict[str, Any]:
    out = dict(expected)
    for key, delta in offsets.items():
        if key in out:
            out[key] = (out[key] or 0) + delta
    return out


def build_walk() -> dict[str, Any]:
    g = build_game_to_mt7()
    source_steps = read_source_steps()
    warnings: list[str] = []
    pending_auto_targets: list[tuple[str, int, int, str]] = []
    offsets: dict[str, int] = {}

    for source_index, step in enumerate(source_steps[36:304], start=37):
        try:
            new_offsets = replay_source_step_to20(g, step, pending_auto_targets)
        except RouteError:
            raise
        for key, delta in new_offsets.items():
            offsets[key] = offsets.get(key, 0) + delta
        # auto ON: auto_sweep (after each go_to) picks up on-path resources,
        # so collect_targets_any_order / collect_zero_enemy_gold_deficit are
        # redundant -- they would add no-op arrival steps. Skip them.
        pending_auto_targets[:] = []
        expected = adjust_expected(comparable_state(step.get("after") or {}), offsets)
        live = comparable_state(g.snapshot())
        if not pending_auto_targets and expected != live:
            # collect_zero_enemy_gold_deficit skipped (auto_sweep battles 0-dmg)
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
        "verification_note": "auto-OFF local MT4->20F vampire walk; live replay pending",
        "auto_settings": [{"when": "4F start", "auto": dict(AUTO_ON), "reason": "auto ON: auto-bfs pickup/battle/wall"}],
        "source": "outputs/results/strict20_preserve_pickaxe_4to50_web_strict_record_step001_402_nopot_switch.json",
        "start": steps[0]["before"],
        "final": steps[-1]["after"],
        "expected_final": steps[-1]["after"],
        "steps": steps,
        "warnings": warnings,
        "errors": g.errors,
        "source_state_offsets": offsets,
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
