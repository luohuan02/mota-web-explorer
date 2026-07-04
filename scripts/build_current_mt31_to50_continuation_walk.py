#!/usr/bin/env python3
"""Build a continuation walk from the current live MT31 checkpoint to 50F."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SNAPSHOT = ROOT / "outputs" / "results" / "strict20_live_current_mt31_step217_snapshot.json"
DEFAULT_OUT_JSON = ROOT / "outputs" / "results" / "strict20_live_current_mt31_to50_continuation_walk.json"
DEFAULT_OUT_MD = ROOT / "outputs" / "reports" / "strict20_live_current_mt31_to50_continuation_walk.md"

sys.path.insert(0, str(ROOT / "scripts"))
import build_current_mt42_to50_tail_walk as tail  # noqa: E402


post = tail.post
score_mod = tail.score_mod


def state_text(s: dict[str, Any]) -> str:
    return (
        f"{s['floor']} x{s['x']}y{s['y']} "
        f"HP={s['hp']} ATK={s['atk']} DEF={s['def']} "
        f"YK={s['yk']} BK={s['bk']} RK={s['rk']} G={s['gold']} "
        f"dmg={s['dmg']} door={s['yd']}/{s['bd']}/{s['rd']}"
    )


def run_stage(g: Any, name: str, label: str, fn: Callable[[Any], None]) -> None:
    before = g.snapshot()
    before["step_count"] = len(g.steps)
    fn(g)
    after = g.snapshot()
    after["step_count"] = len(g.steps)
    g.stage_summaries.append(
        {
            "name": name,
            "label": label,
            "before": before,
            "after": after,
            "delta_dmg": after["dmg"] - before["dmg"],
            "delta_steps": after["step_count"] - before["step_count"],
            "stock_score": post.stock_score(after),
        }
    )


def resume_post_shield_after_mt31(g: Any) -> None:
    g.set_segment("post-shield resume after MT31 auto")
    # We are already after the lucky coin and the MT31 x1y7 live auto-cleanup.
    # Continue from the same decision point as post_shield_49's def-first phase.
    post.buy_shops_to_stat(g, "def", 430, "46F def-first shop", preserve_yk=1)
    post.kill_47_retreat_wizards(g)
    post.clear_zero_damage_monsters(g, preserve_yk=1, min_floor=1)
    g.blocked_items.add(("MT20", 11, 5))
    post.cleanup_reachable_items(g, {"redGem", "blueGem", "yellowKey", "blueKey", "redKey"}, min_floor=1, preserve_rk=1)
    g.fly("MT45")
    for pos in [(1, 3), (2, 3), (1, 5), (2, 5)]:
        post.safe_try(g, g.go_to, "MT45", *pos, f"45F left gem {pos}")
    post.buy_shops_to_stat(g, "atk", 291, "46F atk shop", preserve_yk=1)
    if g.state["gold"] < 1000:
        post.safe_try(g, post.farm_gold_after_coin, g, 1000, 0, 1)
    if g.state["floor"] != "MT45":
        g.fly("MT45")
    if g.state["gold"] >= 1000 and not g.flags.get(g.trader_flag("MT45", 9, 3)):
        post.optional_talk_trader(g, "MT45", 9, 3, "45F 1000G buy 2000HP")
    post.eat_all_reachable_potions(g, min_floor=1)
    g.fly("MT41")
    g.fly("MT42")
    g.go_to("MT42", 7, 1, "42F red-door key for 49F")
    g.fly("MT48")
    g.change_by_stair("MT49", 1, 11, "48F up to 49F")
    g.go_to("MT49", 3, 11, "49F red door")
    for pos in [(5, 10), (7, 10), (6, 9), (5, 8), (7, 8), (6, 7)]:
        g.go_to("MT49", *pos, f"49F boss pre-switch {pos}")
    g.go_to("MT49", 6, 6, "49F boss event")
    for p in [(5, 2), (5, 3), (5, 4), (6, 4), (7, 4), (7, 3), (7, 2), (6, 2)]:
        g.set_block("MT49", p, "enemy", "whiteKing", 246)
    g.set_block("MT49", (6, 3), "enemy", "redKing", 245)
    corners = {("MT49", 5, 2), ("MT49", 7, 2), ("MT49", 5, 4), ("MT49", 7, 4)}
    g.retreat_wizards |= corners
    for pos in [(6, 2), (5, 3), (7, 3), (6, 4)]:
        g.go_to("MT49", *pos, f"49F boss cardinal guard {pos}")
    g.flags["49sealed"] = True
    g.retreat_wizards -= corners
    for pos in [(5, 2), (7, 2), (5, 4), (7, 4), (6, 3)]:
        g.go_to("MT49", *pos, f"49F boss corner guard/redKing {pos}")
    for pos in [(5, 2), (7, 2), (2, 4), (3, 4), (4, 4), (8, 4), (9, 4), (10, 4), (5, 5), (6, 5), (7, 5)]:
        post.safe_try(g, g.go_to, "MT49", *pos, f"49F reward {pos}")


def build(args: argparse.Namespace) -> Any:
    tail.install_live_tail_hooks()
    snapshot = post.read_json(args.snapshot)
    g = post.Game(snapshot)
    g.state["dmg"] = args.base_dmg
    g.state["yd"], g.state["bd"], g.state["rd"] = args.base_doors
    g.flags["TE"] = True
    g.flags["addhp"] = True
    post.TRACE_ENABLED = args.trace
    run_stage(g, "post_shield_resume", "post-shield resume after MT31 auto", resume_post_shield_after_mt31)
    run_stage(g, "post_49_endgame", post.STAGE_LABELS["post_49_endgame"], post.post_49_endgame)
    return g


def write_outputs(g: Any, args: argparse.Namespace) -> None:
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    score = score_mod.current_floor_and_below_final_score(g, 50, monster_gold_factor=0.5)
    data = {
        "ok": not g.errors,
        "name": "strict20_live_current_mt31_to50_continuation_walk",
        "source_snapshot": str(args.snapshot.relative_to(ROOT) if args.snapshot.is_relative_to(ROOT) else args.snapshot),
        "base_counters": {
            "dmg": args.base_dmg,
            "yd": args.base_doors[0],
            "bd": args.base_doors[1],
            "rd": args.base_doors[2],
            "note": "Continuation counters are local to the exported MT31 checkpoint unless supplied by stitched prefix.",
        },
        "final": g.snapshot(),
        "state_text": state_text(g.snapshot()),
        "final_score": score,
        "stage_summaries": g.stage_summaries,
        "errors": g.errors,
        "steps": g.steps,
    }
    args.out_json.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# MT31 当前实机 checkpoint 到 50F continuation walk",
        "",
        f"- 结果：{'通过' if not g.errors else '未通过'}",
        f"- 起点快照：`{data['source_snapshot']}`",
        f"- 终点：`{data['state_text']}`",
        f"- final-score<=50：`{score['final_score']:g}` (stock={score['stock_score']:g}, remaining={score['remaining_value_hp']:g}, zeroG={score['zero_damage_monster_value_hp']:g})",
        "",
        "## Walk",
        "",
    ]
    for i, step in enumerate(g.steps, start=1):
        pos = step["pos"]
        eid = step.get("eid") or ""
        delta = f" [{step['delta']}]" if step.get("delta") else ""
        note = f" ({step['note']})" if step.get("note") else ""
        lines.append(f"{i:03d}. {step['segment']} - {step['floor']} x{pos[0]}y{pos[1]} {step['action']} {eid}{delta}{note}".rstrip())
    args.out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", type=Path, default=DEFAULT_SNAPSHOT)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    parser.add_argument("--base-dmg", type=int, default=0)
    parser.add_argument("--base-doors", type=lambda s: tuple(map(int, s.split("/"))), default=(0, 0, 0))
    parser.add_argument("--trace", action="store_true")
    args = parser.parse_args()
    args.snapshot = args.snapshot.resolve()
    args.out_json = args.out_json.resolve()
    args.out_md = args.out_md.resolve()
    g = build(args)
    write_outputs(g, args)
    print(f"ok={not g.errors}")
    print(f"final={state_text(g.snapshot())}")
    print(f"json={args.out_json}")
    print(f"md={args.out_md}")


if __name__ == "__main__":
    main()
