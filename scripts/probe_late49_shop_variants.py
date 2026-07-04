#!/usr/bin/env python3
"""Probe no-coin late-49 TE shop variants from the slot26 40F state.

This is local-only evidence for choosing the post-40 strategy.  It preserves
the downFly for 50F -> 49F and therefore does not take the 0F lucky coin.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import probe_post40_te_late49_route as late49


ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "outputs" / "results" / "late49_shop_variants.json"
OUT_MD = ROOT / "outputs" / "reports" / "late49_shop_variants.md"

post = late49.post


VARIANTS = [
    {"name": "current_atk291_def430", "order": [("atk", 291), ("def", 430), ("atk", 291)]},
    {"name": "def430_then_atk291", "order": [("def", 430), ("atk", 291)]},
    {"name": "atk281_def430_atk291", "order": [("atk", 281), ("def", 430), ("atk", 291)]},
    {"name": "atk271_def430_atk291", "order": [("atk", 271), ("def", 430), ("atk", 291)]},
    {"name": "atk301_only", "order": [("atk", 301)]},
    {"name": "atk291_then_hp", "order": [("atk", 291), ("hp", 1)]},
]


def state_line(s: dict[str, Any]) -> str:
    return (
        f"HP={s['hp']} ATK={s['atk']} DEF={s['def']} "
        f"YK={s['yk']} BK={s['bk']} RK={s['rk']} G={s['gold']} "
        f"{s['floor']} x{s['x']}y{s['y']}"
    )


def final_redking_damage(g: Any) -> int | float:
    old = bool(g.flags.get("50final"))
    g.flags["50final"] = True
    dmg = g.enemy_damage("redKing")
    g.flags["50final"] = old
    return dmg


def run_to_after_42_red_key() -> Any:
    g = late49.make_game("slot26_clean_7def")
    for fn in [
        post.guide_prefix_to_48_visit,
        post.collect_guide_pre_earthquake,
        post.farm_gold_for_earthquake,
        post.earthquake_and_shield,
    ]:
        fn(g)

    g.fly("MT43")
    g.go_to("MT43", 3, 1, "43F upper-left yellow door")
    for pos in [(3, 6), (8, 6), (11, 5)]:
        g.go_to("MT43", *pos, f"43F middle/right resource {pos}")
    g.go_to("MT43", 9, 1, "43F upper-right guard")
    g.go_to("MT43", 9, 4, "43F sacred shield")
    g.go_to("MT43", 11, 11, "43F lower-right blue key")
    g.fly("MT46")
    g.go_to("MT46", 3, 8, "46F magic key")
    g.fly("MT41")
    g.use_big_key("41F open all yellow doors")
    g.go_to("MT41", 5, 6, "41F left blue door")
    g.go_to("MT41", 2, 2, "41F upper-left red wizard")
    g.go_to("MT41", 4, 1, "41F upper-left blue key")
    g.go_to("MT41", 7, 6, "41F right blue door")
    g.go_to("MT41", 9, 2, "41F right wall trigger")
    g.go_to("MT41", 10, 2, "41F upper-right red wizard")
    g.fly("MT40")
    g.fly("MT41")
    g.go_to("MT41", 6, 5, "41F downFly")
    for pos in [(3, 10), (4, 10), (3, 11), (4, 11), (8, 10), (9, 10), (8, 11), (9, 11)]:
        post.safe_try(g, g.go_to, "MT41", *pos, f"41F magic-key resource {pos}")

    g.fly("MT42")
    g.go_to("MT42", 7, 1, "42F red key for late-49 TE")
    return g


def apply_shop_plan(g: Any, order: list[tuple[str, int]]) -> None:
    for kind, target in order:
        if kind == "hp":
            post.buy_hp_with_remaining_gold(g, target)
        else:
            post.buy_shops_to_stat(g, kind, target, f"46F variant {kind} shop", preserve_yk=1)


def finish_post_shield(g: Any, order: list[tuple[str, int]]) -> Any:
    apply_shop_plan(g, order)
    post.kill_47_retreat_wizards(g)
    post.clear_zero_damage_monsters(g, preserve_yk=1, min_floor=1)
    g.blocked_items.add(("MT20", 11, 5))
    post.cleanup_reachable_items(g, {"redGem", "blueGem", "yellowKey", "blueKey", "redKey"},
                                 min_floor=1, preserve_rk=1)
    for pos in [(1, 3), (2, 3), (1, 5), (2, 5)]:
        post.safe_try(g, g.go_to, "MT45", *pos, f"45F left gem {pos}")
    if g.state["gold"] < 1000:
        post.safe_try(g, post.farm_gold_after_coin, g, 1000, 0, 1)
    if g.state["floor"] != "MT45":
        g.fly("MT45")
    if g.state["gold"] >= 1000 and not g.flags.get(g.trader_flag("MT45", 9, 3)):
        g.talk_trader("MT45", 9, 3, "45F 1000G to 2000HP")
    post.eat_all_reachable_potions(g, min_floor=1)
    return g


def run_variant(seed: Any, variant: dict[str, Any]) -> dict[str, Any]:
    g = copy.deepcopy(seed)
    try:
        finish_post_shield(g, variant["order"])
        post_after = g.snapshot()
        post_after["step_count"] = len(g.steps)
        late49.late49_endgame(g)
    except post.RouteError:
        pass
    dmg = final_redking_damage(g)
    return {
        "name": variant["name"],
        "order": variant["order"],
        "ok": not g.errors,
        "final": g.snapshot(),
        "state_text": state_line(g.state),
        "final_redking_damage": dmg,
        "surplus_vs_final_redking": None if dmg == float("inf") else g.state["hp"] - int(dmg),
        "errors": list(g.errors),
        "steps": len(g.steps),
    }


def write_outputs(rows: list[dict[str, Any]]) -> None:
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps({"rows": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# Late-49 TE shop variant probe",
        "",
        "- Local-only; downFly is reserved for 50F -> 49F, so lucky coin is not used.",
        "- Gold is exact local gold; no live-gold tolerance.",
        "",
        "| variant | result | final | final redKing dmg | surplus | errors |",
        "| --- | --- | --- | ---: | ---: | --- |",
    ]
    for row in rows:
        err = "; ".join(row["errors"][:2]) if row["errors"] else ""
        lines.append(
            f"| {row['name']} | {'OK' if row['ok'] else 'FAIL'} | `{row['state_text']}` | "
            f"{row['final_redking_damage']} | {row['surplus_vs_final_redking']} | {err} |"
        )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    post.TRACE_ENABLED = False
    seed = run_to_after_42_red_key()
    rows = []
    for variant in VARIANTS:
        print(f"[variant] {variant['name']}", flush=True)
        row = run_variant(seed, variant)
        rows.append(row)
        print(f"  ok={row['ok']} {row['state_text']} surplus={row['surplus_vs_final_redking']} errors={len(row['errors'])}", flush=True)
    rows.sort(key=lambda r: (r["ok"], r["surplus_vs_final_redking"] if r["surplus_vs_final_redking"] is not None else -10**9), reverse=True)
    write_outputs(rows)
    print(f"wrote {OUT_JSON}")
    print(f"wrote {OUT_MD}")
    return 0 if any(row["ok"] for row in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
