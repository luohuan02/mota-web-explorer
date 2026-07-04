#!/usr/bin/env python3
"""Build a strict tail walk from the current live MT42 checkpoint to 50F.

This is a narrow bridge for the current web-verified run.  The browser has
already reached MT42 after the right-side key cluster, but the old local walk
diverged because automatic zero-damage cleanup changed gold/resources.  This
script treats the exported live saveData snapshot as authoritative for HP,
stats, keys, gold, tools, and map blocks, then continues the existing pure-TE
post-40 route from that exact state.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SNAPSHOT = ROOT / "outputs" / "results" / "strict20_live_current_mt42_step806_snapshot.json"
DEFAULT_OUT_JSON = ROOT / "outputs" / "results" / "strict20_live_current_mt42_to50_tail_walk.json"
DEFAULT_OUT_MD = ROOT / "outputs" / "reports" / "strict20_live_current_mt42_to50_tail_walk.md"


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


post = load_module("mt42_tail_post40", ROOT / "scripts" / "search_post40_guide_route.py")
score_mod = load_module("mt42_tail_score", ROOT / "scripts" / "floor_final_score.py")


def state_text(s: dict[str, Any]) -> str:
    return (
        f"{s['floor']} x{s['x']}y{s['y']} "
        f"HP={s['hp']} ATK={s['atk']} DEF={s['def']} "
        f"YK={s['yk']} BK={s['bk']} RK={s['rk']} G={s['gold']} "
        f"dmg={s['dmg']} door={s['yd']}/{s['bd']}/{s['rd']}"
    )


def current_mt42_to_48_suffix(g: Any) -> None:
    """Continue guide_prefix_to_48_visit from live MT42 x10y9/x11y10."""

    g.set_segment("MT42 current checkpoint to 48F sword")
    if g.state["floor"] != "MT42":
        g.fail(f"tail must start on MT42, got {g.state['floor']}")
    if (g.state["x"], g.state["y"]) != (11, 10):
        before_move = g.snapshot()
        before_steps = len(g.steps)
        g.go_to("MT42", 11, 10, "42F move to center-fly origin after live auto key pickup")
        if len(g.steps) > before_steps and g.steps[-1]["action"] == "到达":
            g.steps[-1]["before"] = before_move
            g.steps[-1]["delta"] = ""
    g.center_fly("42F right-lower to left-upper")
    g.change_by_stair("MT43", 1, 1, "42F up to 43F")

    # 43F direct route to 45F/46F.
    g.go_to("MT43", 3, 1, "43F yellow door")
    g.go_to("MT43", 1, 4, "43F blue door")
    g.change_by_stair("MT45", 1, 11, "43F up stair jumps to 45F")
    g.change_by_stair("MT46", 11, 1, "45F up to 46F")

    # Heal before walking the 46F/47F wizard fields if those potions remain.
    g.fly("MT14")
    g.go_to("MT14", 9, 6, "pre 46F/47F field red potion")
    g.fly("MT18")
    record_mt18_live_auto_zombie(g)
    g.go_to("MT18", 1, 11, "pre 46F/47F field red potion")
    g.go_to("MT18", 11, 11, "pre 46F/47F return-field red potion")
    g.fly("MT17")
    if not record_mt17_live_auto_group(g):
        g.go_to("MT17", 10, 2, "pre 46F/47F right-top blue potion")
    if g.state["def"] < 220:
        post.eat_minimal_potions_until(g, 1800, "low-def route HP for 46F/47F field")
        if g.state["floor"] != "MT46":
            g.fly("MT46")

    g.fly("MT46")
    for pos in [(11, 3), (11, 5), (11, 8)]:
        g.go_to("MT46", *pos, "46F lower three-door route")
    g.change_by_stair("MT47", 11, 11, "46F up to 47F")

    # 47F guide resources and center fly.
    g.go_to("MT47", 7, 11, "47F lower-left yellow door")
    g.go_to("MT47", 6, 10, "47F left red gem")
    g.go_to("MT47", 6, 10, "47F return to center-fly origin")
    g.center_fly("47F lower-left to upper-right")
    post.collect_net_yellow_keys_until(g, 1, "before 47F right yellow door")
    if g.state["floor"] != "MT47":
        g.fly("MT47")
    g.go_to("MT47", 7, 1, "47F right yellow door")
    if not record_mt47_live_auto_right_resources(g):
        for pos in [(11, 1), (11, 2), (11, 3)]:
            g.go_to("MT47", *pos, f"47F right resource {pos}")
    g.go_to("MT47", 3, 1, "47F blue door")
    g.change_by_stair("MT48", 1, 1, "47F up to 48F")

    # Preserve-pickaxe branch now spends the 15F pickaxe for 48F holy sword.
    g.fly("MT14")
    g.change_by_stair("MT15", 6, 11, "14F lower stair to 15F pickaxe area")
    if not record_mt15_live_auto_octopus(g):
        g.go_to("MT15", 6, 6, "15F octopus for pickaxe")
    g.go_to("MT15", 6, 5, "15F pickaxe")
    g.fly("MT48")
    g.use_pickaxe("MT48", 10, 10, "48F break wall for holy sword")
    g.go_to("MT48", 8, 10, "48F holy sword")


def record_mt18_live_auto_zombie(g: Any) -> None:
    """Mirror the live auto-battle side effect before MT18 x1y11.

    With battle auto on, clicking the far MT18 x1y11 target first clears the
    remaining zero-damage zombieKnight at x7y4 and leaves the hero at x5y2.
    This must be modeled exactly because the +30G affects later shop choices.
    """

    block = g.block_at("MT18", (7, 4))
    if not block or block.kind != "enemy" or block.eid != "zombieKnight":
        return
    before = g.snapshot()
    dmg = g.enemy_damage(block.eid)
    if dmg == float("inf"):
        g.fail("MT18 live auto zombieKnight is not killable")
    gain = int(g.enemies[block.eid].get("money", 0))
    if g.state.get("coin"):
        gain *= 2
    g.state["hp"] -= int(dmg)
    g.state["dmg"] += int(dmg)
    g.state["gold"] += gain
    g.set_ground("MT18", (7, 4))
    g.state["x"], g.state["y"] = 5, 2
    g.record("到达", (1, 11), None, before, "click MT18 x1y11; auto clears MT18 x7y4 zombieKnight and stops at x5y2")


def record_mt17_live_auto_group(g: Any) -> bool:
    """Mirror live auto-battle before the nominal MT17 x10y2 click.

    The target potion is already gone/not useful in this live branch.  A real
    click toward x10y2 instead clears the remaining zero-damage monsters at
    x5y3 and x5y7, grants 48G, and leaves the hero at x7y2.
    """

    targets = [((5, 3), "zombieKnight"), ((5, 7), "zombie")]
    present: list[tuple[tuple[int, int], Any]] = []
    for pos, eid in targets:
        block = g.block_at("MT17", pos)
        if block and block.kind == "enemy" and block.eid == eid:
            present.append((pos, block))
    if not present:
        return False
    before = g.snapshot()
    for pos, block in present:
        dmg = g.enemy_damage(block.eid)
        if dmg == float("inf"):
            g.fail(f"MT17 live auto {block.eid} is not killable")
        gain = int(g.enemies[block.eid].get("money", 0))
        if g.state.get("coin"):
            gain *= 2
        g.state["hp"] -= int(dmg)
        g.state["dmg"] += int(dmg)
        g.state["gold"] += gain
        g.set_ground("MT17", pos)
    g.state["x"], g.state["y"] = 7, 2
    cleared = ", ".join(f"x{x}y{y} {block.eid}" for (x, y), block in present)
    g.record("到达", (10, 2), None, before, f"click MT17 x10y2; auto clears {cleared} and stops at x7y2")
    return True


def record_mt47_live_auto_right_resources(g: Any) -> bool:
    """Mirror live x8y1 side effects on MT47.

    After opening x7y1, a real move to x8y1 takes wizard-field damage, moves the
    redWizard from x8y2 to x8y3, and auto-picks the right-side yellowKey,
    blueGem, yellowKey group at x11y1/x11y2/x11y3.
    """

    if g.state["floor"] != "MT47" or (g.state["x"], g.state["y"]) != (7, 1):
        return False
    resources = [((11, 1), "yellowKey"), ((11, 2), "blueGem"), ((11, 3), "yellowKey")]
    if not all((g.block_at("MT47", pos) and g.block_at("MT47", pos).eid == eid) for pos, eid in resources):
        return False
    before = g.snapshot()
    damage = g.check_damage_at("MT47", (8, 1))
    g.state["x"], g.state["y"] = 8, 1
    if damage > 0:
        g.state["hp"] -= int(damage)
        g.state["dmg"] += int(damage)
    wiz = g.block_at("MT47", (8, 2))
    if wiz and wiz.eid == "redWizard":
        g.set_ground("MT47", (8, 2))
        g.set_block("MT47", (8, 3), "enemy", "redWizard", wiz.tile)
        g.flags["47wizardMoved"] = True
        g.retreat_wizards.add(("MT47", 8, 3))
    for pos, eid in resources:
        block = g.block_at("MT47", pos)
        if block and block.kind == "item" and block.eid == eid:
            g.apply_item("MT47", eid)
            g.set_ground("MT47", pos)
    g.record(
        "地图伤害",
        (8, 1),
        "checkBlock",
        before,
        "47F x8y1 damage; redWizard moves to x8y3; auto-picks x11y1/x11y2/x11y3",
    )
    return True


def record_mt15_live_auto_octopus(g: Any) -> bool:
    """Mirror live auto-clear of MT15 x2y1 while clicking the octopus."""

    if g.state["floor"] != "MT15":
        return False
    side = g.block_at("MT15", (2, 1))
    boss = g.block_at("MT15", (6, 6))
    if not side or side.kind != "enemy" or side.eid != "zombieKnight":
        return False
    if not boss or boss.kind != "enemy" or boss.eid != "octopus":
        return False
    before = g.snapshot()
    for pos, block in [((2, 1), side), ((6, 6), boss)]:
        dmg = g.enemy_damage(block.eid)
        if dmg == float("inf"):
            g.fail(f"MT15 live auto {block.eid} is not killable")
        gain = int(g.enemies[block.eid].get("money", 0))
        if g.state.get("coin"):
            gain *= 2
        g.state["hp"] -= int(dmg)
        g.state["dmg"] += int(dmg)
        g.state["gold"] += gain
        g.set_ground("MT15", pos)
        g.after_action("MT15", pos, block)
    g.state["x"], g.state["y"] = 6, 6
    g.apply_check_damage("MT15", (6, 6), "15F octopus for pickaxe")
    g.record("击杀", (6, 6), "octopus", before, "15F octopus; auto clears MT15 x2y1 zombieKnight")
    return True


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


def build_tail(args: argparse.Namespace) -> Any:
    install_live_tail_hooks()
    snapshot = post.read_json(args.snapshot)
    g = post.Game(snapshot)
    apply_current_live_snapshot_fixes(g)
    g.state["dmg"] = args.base_dmg
    g.state["yd"], g.state["bd"], g.state["rd"] = args.base_doors
    g.flags["TE"] = True
    g.flags["addhp"] = True
    post.TRACE_ENABLED = args.trace

    stages: list[tuple[str, str, Callable[[Any], None]]] = [
        ("mt42_to_48", "MT42 current checkpoint to 48F sword", current_mt42_to_48_suffix),
        ("pre_earthquake", post.STAGE_LABELS["pre_earthquake"], collect_tail_pre_earthquake),
        ("farm_earthquake", post.STAGE_LABELS["farm_earthquake"], farm_tail_gold_for_earthquake),
        ("shield", post.STAGE_LABELS["shield"], post.earthquake_and_shield),
        ("post_shield_49", post.STAGE_LABELS["post_shield_49"], post.post_shield_49),
        ("post_49_endgame", post.STAGE_LABELS["post_49_endgame"], post.post_49_endgame),
    ]
    try:
        for name, label, fn in stages:
            run_stage(g, name, label, fn)
            if args.stop_after == name:
                break
    except post.RouteError:
        pass
    return g


def collect_tail_pre_earthquake(g: Any) -> None:
    g.set_segment("pre-earthquake resource loop")
    post.collect_existing_items(g, "MT40", [(4, 4), (3, 4)], "40F delayed blue potion after 40F boss")
    post.collect_existing_items(g, "MT38", [(11, 11)], "38F guide key")
    post.collect_existing_items(g, "MT34", [(6, 1), (9, 1), (10, 1), (10, 2), (11, 1)], "34F upper resource")
    post.collect_existing_items(g, "MT31", [(10, 1), (8, 10), (8, 11)], "31F guide gem")
    post.collect_existing_items(g, "MT32", [(11, 4), (10, 4)], "32F right key")
    if not record_mt39_live_auto_ghost_red_gem(g):
        post.collect_existing_items(g, "MT39", [(11, 6)], "39F red gem")
    post.collect_existing_items(g, "MT40", [(2, 2)], "40F left reward")


def farm_tail_gold_for_earthquake(g: Any) -> None:
    # These MT43 lower-left potions trap the live hero away from any stair/fly
    # use point, so they are not legal pre-earthquake healing resources.
    g.blocked_items.add(("MT43", 4, 10))
    g.blocked_items.add(("MT43", 4, 11))
    # MT46 x7y6 sits behind a field-damage pocket. Taking it before the
    # earthquake requires an extra exit movement that the model did not record.
    g.blocked_items.add(("MT46", 7, 6))
    post.farm_gold_for_earthquake(g)
    if g.state["hp"] < 1500:
        post.eat_minimal_potions_until(g, 1500, "pre-earthquake shield HP after live guard gold")


def record_mt39_live_auto_ghost_red_gem(g: Any) -> bool:
    """Mirror live auto-pickup of MT39 x11y6 after killing x11y7."""

    ghost = g.block_at("MT39", (11, 7))
    gem = g.block_at("MT39", (11, 6))
    if not ghost or ghost.kind != "enemy" or ghost.eid != "ghostSkeleton":
        return False
    if not gem or gem.kind != "item" or gem.eid != "redGem":
        return False
    if g.state["floor"] != "MT39":
        g.fly("MT39")
    before = g.snapshot()
    dmg = g.enemy_damage(ghost.eid)
    if dmg == float("inf"):
        g.fail("MT39 live auto ghostSkeleton is not killable")
    # Live afterBattle includes an extra guard-linked ghostSkeleton payout at
    # this point, so the observed battle gain is 70G before the lucky coin.
    gain = 70
    g.state["hp"] -= int(dmg)
    g.state["dmg"] += int(dmg)
    g.state["gold"] += gain
    g.set_ground("MT39", (11, 7))
    g.after_action("MT39", (11, 7), ghost)
    g.apply_item("MT39", gem.eid)
    g.set_ground("MT39", (11, 6))
    g.state["x"], g.state["y"] = 11, 7
    g.apply_check_damage("MT39", (11, 7), "MT39 x11y7 ghostSkeleton")
    g.record("击杀", (11, 7), ghost.eid, before, "MT39 x11y7 ghostSkeleton grants 70G via live guard payout; auto-picks x11y6 redGem")
    return True


def apply_current_live_snapshot_fixes(g: Any) -> None:
    """Apply narrow map fixes observed in the current live MT42 tail save.

    The h5mota live map has a few already-empty ghostSkeleton cells in this
    branch, but the static-map fallback can reintroduce them while rebuilding
    the local Game.  Do not award gold here: live verification shows these
    cells are empty without an accompanying gold gain at the current checkpoint.
    """

    stale_enemies = [
        ("MT31", (10, 3), "ghostSkeleton"),
        ("MT31", (11, 3), "ghostSkeleton"),
        ("MT39", (3, 9), "ghostSkeleton"),
        ("MT19", (8, 3), "zombieKnight"),
        ("MT19", (8, 8), "zombieKnight"),
        ("MT16", (3, 6), "rock"),
        ("MT12", (10, 3), "zombie"),
        ("MT16", (2, 2), "redPriest"),
        ("MT16", (5, 3), "zombie"),
        ("MT16", (10, 5), "zombie"),
        ("MT10", (10, 7), "skeletonSoldier"),
        ("MT10", (3, 6), "skeleton"),
        ("MT10", (11, 6), "skeleton"),
        ("MT6", (8, 6), "skeleton"),
        ("MT6", (10, 3), "skeleton"),
        ("MT36", (1, 3), "slimeMan"),
        ("MT36", (7, 1), "zombieKnight"),
        ("MT37", (11, 6), "swordsman"),
    ]
    for fid, pos, eid in stale_enemies:
        block = g.block_at(fid, pos)
        if block and block.kind == "enemy" and block.eid == eid:
            g.set_ground(fid, pos)

    stale_items = [
        ("MT43", (10, 8), "yellowKey"),
    ]
    for fid, pos, eid in stale_items:
        block = g.block_at(fid, pos)
        if block and block.kind == "item" and block.eid == eid:
            g.set_ground(fid, pos)


def install_live_tail_hooks() -> None:
    """Install narrow live-only modeling hooks for this mid-run checkpoint."""

    if getattr(post.Game, "_mt42_tail_hooks_installed", False):
        return
    original_apply_block = post.Game.apply_block
    original_use_earthquake = post.Game.use_earthquake
    original_go_to = post.Game.go_to

    def apply_block(self: Any, fid: str, pos: tuple[int, int], block: Any, note: str = "") -> None:
        if (
            fid == "MT48"
            and pos in {(4, 6), (4, 9)}
            and block.kind == "door"
            and block.eid == "yellowDoor"
        ):
            original_apply_block(self, fid, pos, block, note)
            return
        if fid == "MT16" and pos == (6, 6) and block.kind == "enemy" and block.eid == "zombieKnight":
            before = self.snapshot()
            dmg = self.enemy_damage(block.eid)
            if dmg == float("inf"):
                self.fail("MT16 x6y6 live guard zombieKnight is not killable")
            self.state["hp"] -= int(dmg)
            self.state["dmg"] += int(dmg)
            # Live afterBattle includes guard-linked enemies at this point,
            # yielding exactly 116G while removing only the center block.
            self.state["gold"] += 116
            self.set_ground(fid, pos)
            self.record("击杀", pos, block.eid, before, "MT16 x6y6 zombieKnight grants 116G via live guard payout")
            self.after_action(fid, pos, block)
            self.apply_check_damage(fid, pos, note)
            self.trigger_tile_event(fid, pos)
            return
        if fid == "MT19" and pos == (6, 9) and block.kind == "enemy" and block.eid == "zombieKnight":
            before = self.snapshot()
            dmg = self.enemy_damage(block.eid)
            if dmg == float("inf"):
                self.fail("MT19 live guard zombieKnight group is not killable")
            self.state["hp"] -= int(dmg)
            self.state["dmg"] += int(dmg)
            self.state["gold"] += 90
            for guard_pos in [(6, 9), (8, 3), (8, 8)]:
                guard = self.block_at(fid, guard_pos)
                if guard and guard.kind == "enemy" and guard.eid == "zombieKnight":
                    self.set_ground(fid, guard_pos)
                    self.after_action(fid, guard_pos, guard)
            self.record("击杀", pos, block.eid, before, "MT19 x6y9 zombieKnight clears live guard group x6y9/x8y3/x8y8 for 90G")
            self.apply_check_damage(fid, pos, note)
            self.trigger_tile_event(fid, pos)
            return
        if fid == "MT12" and pos == (5, 3) and block.kind == "enemy" and block.eid == "redPriest":
            before = self.snapshot()
            dmg = self.enemy_damage(block.eid)
            if dmg == float("inf"):
                self.fail("MT12 live guard redPriest is not killable")
            self.state["hp"] -= int(dmg)
            self.state["dmg"] += int(dmg)
            self.state["gold"] += 40
            for guard_pos in [(5, 3), (10, 3)]:
                guard = self.block_at(fid, guard_pos)
                if guard and guard.kind == "enemy":
                    self.set_ground(fid, guard_pos)
                    self.after_action(fid, guard_pos, guard)
            self.record("击杀", pos, block.eid, before, "MT12 x5y3 redPriest clears live guard group x5y3/x10y3 for 40G")
            self.apply_check_damage(fid, pos, note)
            self.trigger_tile_event(fid, pos)
            return
        if fid == "MT10" and pos == (2, 7) and block.kind == "enemy" and block.eid == "skeletonSoldier":
            before = self.snapshot()
            dmg = self.enemy_damage(block.eid)
            if dmg == float("inf"):
                self.fail("MT10 live guard skeleton group is not killable")
            self.state["hp"] -= int(dmg)
            self.state["dmg"] += int(dmg)
            self.state["gold"] += 28
            for guard_pos in [(2, 7), (10, 7), (3, 6), (11, 6)]:
                guard = self.block_at(fid, guard_pos)
                if guard and guard.kind == "enemy":
                    self.set_ground(fid, guard_pos)
                    self.after_action(fid, guard_pos, guard)
            self.record("击杀", pos, block.eid, before, "MT10 x2y7 clears live skeleton guard group for 28G")
            self.apply_check_damage(fid, pos, note)
            self.trigger_tile_event(fid, pos)
            return
        if fid == "MT32" and pos == (1, 4) and block.kind == "enemy" and block.eid == "soldier":
            before = self.snapshot()
            dmg = self.enemy_damage(block.eid)
            if dmg == float("inf"):
                self.fail("MT32 x1y4 soldier is not killable")
            gain = int(self.enemies[block.eid].get("money", 0))
            if self.state.get("coin"):
                gain *= 2
            self.state["hp"] -= int(dmg)
            self.state["dmg"] += int(dmg)
            self.state["gold"] += gain
            self.state["yk"] += 4
            self.state["bk"] += 1
            self.flags["32"] = 1
            self.set_ground(fid, pos)
            self.record("击杀", pos, block.eid, before, "MT32 x1y4 soldier triggers live 32F key reward +4YK +1BK")
            self.after_action(fid, pos, block)
            self.apply_check_damage(fid, pos, note)
            self.trigger_tile_event(fid, pos)
            return
        if fid == "MT6" and pos == (9, 6) and block.kind == "enemy" and block.eid == "skeletonSoldier":
            before = self.snapshot()
            dmg = self.enemy_damage(block.eid)
            if dmg == float("inf"):
                self.fail("MT6 live guard skeleton group is not killable")
            self.state["hp"] -= int(dmg)
            self.state["dmg"] += int(dmg)
            self.state["gold"] += 20
            for guard_pos in [(9, 6), (8, 6), (10, 3)]:
                guard = self.block_at(fid, guard_pos)
                if guard and guard.kind == "enemy":
                    self.set_ground(fid, guard_pos)
                    self.after_action(fid, guard_pos, guard)
            self.record("击杀", pos, block.eid, before, "MT6 x9y6 clears live skeleton guard group for 20G")
            self.apply_check_damage(fid, pos, note)
            self.trigger_tile_event(fid, pos)
            return
        if fid == "MT36" and pos == (1, 5) and block.kind == "enemy" and block.eid == "redKnight":
            before = self.snapshot()
            dmg = self.enemy_damage(block.eid)
            if dmg == float("inf"):
                self.fail("MT36 live guard redKnight group is not killable")
            self.state["hp"] -= int(dmg)
            self.state["dmg"] += int(dmg)
            self.state["gold"] += 95
            for guard_pos in [(1, 5), (1, 3)]:
                guard = self.block_at(fid, guard_pos)
                if guard and guard.kind == "enemy":
                    self.set_ground(fid, guard_pos)
                    self.after_action(fid, guard_pos, guard)
            self.record("击杀", pos, block.eid, before, "MT36 x1y5 redKnight clears live guard group x1y5/x1y3 for 95G")
            self.apply_check_damage(fid, pos, note)
            self.trigger_tile_event(fid, pos)
            return
        if fid == "MT36" and pos == (9, 1) and block.kind == "enemy" and block.eid == "redKnight":
            before = self.snapshot()
            dmg = self.enemy_damage(block.eid)
            if dmg == float("inf"):
                self.fail("MT36 x9y1 live guard redKnight group is not killable")
            self.state["hp"] -= int(dmg)
            self.state["dmg"] += int(dmg)
            self.state["gold"] += 95
            for guard_pos in [(9, 1), (7, 1)]:
                guard = self.block_at(fid, guard_pos)
                if guard and guard.kind == "enemy":
                    self.set_ground(fid, guard_pos)
                    self.after_action(fid, guard_pos, guard)
            self.record("击杀", pos, block.eid, before, "MT36 x9y1 redKnight clears live guard group x9y1/x7y1 for 95G")
            self.apply_check_damage(fid, pos, note)
            self.trigger_tile_event(fid, pos)
            return
        if fid == "MT37" and pos == (11, 3) and block.kind == "enemy" and block.eid == "redKnight":
            before = self.snapshot()
            dmg = self.enemy_damage(block.eid)
            if dmg == float("inf"):
                self.fail("MT37 live guard redKnight group is not killable")
            self.state["hp"] -= int(dmg)
            self.state["dmg"] += int(dmg)
            self.state["gold"] += 120
            for guard_pos in [(11, 3), (11, 6)]:
                guard = self.block_at(fid, guard_pos)
                if guard and guard.kind == "enemy":
                    self.set_ground(fid, guard_pos)
                    self.after_action(fid, guard_pos, guard)
            self.record("击杀", pos, block.eid, before, "MT37 x11y3 redKnight clears live guard group x11y3/x11y6 for 120G")
            self.apply_check_damage(fid, pos, note)
            self.trigger_tile_event(fid, pos)
            return
        if fid == "MT8" and pos == (1, 5) and block.kind == "item" and block.eid == "redPotion":
            before = self.snapshot()
            self.apply_item(fid, block.eid)
            self.set_ground(fid, pos)
            gain = 0
            for slime_pos in [(2, 6), (3, 6), (4, 6)]:
                slime = self.block_at(fid, slime_pos)
                if slime and slime.kind == "enemy":
                    gain += int(self.enemies[slime.eid].get("money", 0))
                    self.set_ground(fid, slime_pos)
                    self.after_action(fid, slime_pos, slime)
            self.state["gold"] += gain
            self.record("\u62fe\u53d6", pos, block.eid, before, "MT8 x1y5 redPotion; live auto clears x2y6/x3y6/x4y6 slimes for +5G")
            self.after_action(fid, pos, block)
            self.apply_check_damage(fid, pos, note)
            self.trigger_tile_event(fid, pos)
            return
        if fid == "MT3" and pos == (9, 2) and block.kind == "door" and block.eid == "yellowDoor":
            before = self.snapshot()
            self.state["yk"] -= 1
            self.state["yd"] += 1
            if self.state["yk"] < 0:
                self.fail("negative key after MT3 x9y2 live door")
            self.set_ground(fid, pos)
            bat = self.block_at(fid, (10, 2))
            if bat and bat.kind == "enemy" and bat.eid == "bat":
                self.state["gold"] += int(self.enemies[bat.eid].get("money", 0))
                self.set_ground(fid, (10, 2))
                self.after_action(fid, (10, 2), bat)
            self.record("\u5f00\u95e8", pos, block.eid, before, "MT3 x9y2 yellowDoor; live auto clears x10y2 bat for +3G")
            self.after_action(fid, pos, block)
            self.apply_check_damage(fid, pos, note)
            self.trigger_tile_event(fid, pos)
            return
        if fid == "MT16" and pos == (8, 2) and block.kind == "door" and block.eid == "yellowDoor":
            before = self.snapshot()
            self.state["yk"] -= 1
            self.state["yd"] += 1
            if self.state["yk"] < 0:
                self.fail("negative key after MT16 x8y2 live door")
            self.set_ground(fid, pos)
            gain = 0
            for enemy_pos in [(9, 2), (11, 1)]:
                enemy = self.block_at(fid, enemy_pos)
                if enemy and enemy.kind == "enemy":
                    gain += int(self.enemies[enemy.eid].get("money", 0))
                    self.set_ground(fid, enemy_pos)
                    self.after_action(fid, enemy_pos, enemy)
            self.state["gold"] += gain
            self.record("\u5f00\u95e8", pos, block.eid, before, "MT16 x8y2 yellowDoor; live auto clears x9y2 blackSlime and x11y1 bigBat for +20G")
            self.after_action(fid, pos, block)
            self.apply_check_damage(fid, pos, note)
            self.trigger_tile_event(fid, pos)
            return
        if fid == "MT34" and pos == (9, 10) and block.kind == "enemy" and block.eid == "soldier":
            before = self.snapshot()
            dmg = self.enemy_damage(block.eid)
            if dmg == float("inf"):
                self.fail("MT34 x9y10 soldier is not killable")
            self.state["hp"] -= int(dmg)
            self.state["dmg"] += int(dmg)
            self.state["gold"] += int(self.enemies[block.eid].get("money", 0))
            self.set_ground(fid, pos)
            for item_pos in [(10, 11), (11, 11)]:
                item = self.block_at(fid, item_pos)
                if item and item.kind == "item":
                    self.apply_item(fid, item.eid)
                    self.set_ground(fid, item_pos)
                    self.after_action(fid, item_pos, item)
            self.record("\u51fb\u6740", pos, block.eid, before, "MT34 x9y10 soldier; live auto-picks x10y11 yellowKey and x11y11 redGem")
            self.after_action(fid, pos, block)
            self.apply_check_damage(fid, pos, note)
            self.trigger_tile_event(fid, pos)
            return
        if fid == "MT42" and pos == (3, 8) and block.kind == "enemy" and block.eid == "redBat":
            before = self.snapshot()
            dmg = self.enemy_damage(block.eid)
            if dmg == float("inf"):
                self.fail("MT42 x3y8 redBat is not killable")
            gain = int(self.enemies[block.eid].get("money", 0))
            if self.state.get("coin"):
                gain *= 2
            self.state["hp"] -= int(dmg)
            self.state["dmg"] += int(dmg)
            self.state["gold"] += gain
            self.set_ground(fid, pos)
            for item_pos in [(3, 9), (2, 9)]:
                item = self.block_at(fid, item_pos)
                if item and item.kind == "item" and item.eid == "yellowKey":
                    self.apply_item(fid, item.eid)
                    self.set_ground(fid, item_pos)
                    self.after_action(fid, item_pos, item)
            self.record("\u51fb\u6740", pos, block.eid, before, "MT42 x3y8 redBat; live auto-picks x3y9/x2y9 yellowKeys")
            self.after_action(fid, pos, block)
            self.apply_check_damage(fid, pos, note)
            self.trigger_tile_event(fid, pos)
            return
        if fid == "MT42" and pos == (9, 8) and block.kind == "enemy" and block.eid == "whiteKing":
            before = self.snapshot()
            picked: list[str] = []
            # Live auto-pick runs before this target battle and takes the
            # reachable lower-left non-potion group, so the whiteKing damage is
            # computed after the blue gem's DEF +5.
            for item_pos, expected in [
                ((1, 11), "yellowKey"),
                ((2, 11), "yellowKey"),
                ((3, 11), "blueGem"),
            ]:
                item = self.block_at(fid, item_pos)
                if not item or item.kind != "item" or item.eid != expected:
                    continue
                self.apply_item(fid, item.eid)
                self.set_ground(fid, item_pos)
                self.after_action(fid, item_pos, item)
                picked.append(f"x{item_pos[0]}y{item_pos[1]} {item.eid}")
            bat_pos = (1, 10)
            bat = self.block_at(fid, bat_pos)
            if bat and bat.kind == "enemy" and bat.eid == "redBat":
                bat_dmg = self.enemy_damage(bat.eid)
                if bat_dmg == float("inf"):
                    self.fail("MT42 live auto redBat is not killable")
                bat_gain = int(self.enemies[bat.eid].get("money", 0))
                if self.state.get("coin"):
                    bat_gain *= 2
                self.state["hp"] -= int(bat_dmg)
                self.state["dmg"] += int(bat_dmg)
                self.state["gold"] += bat_gain
                self.set_ground(fid, bat_pos)
                self.after_action(fid, bat_pos, bat)
                picked.append("x1y10 redBat")
            dmg = self.enemy_damage(block.eid)
            if dmg == float("inf"):
                self.fail("MT42 x9y8 whiteKing is not killable")
            gain = int(self.enemies[block.eid].get("money", 0))
            if self.state.get("coin"):
                gain *= 2
            self.state["hp"] -= int(dmg)
            self.state["dmg"] += int(dmg)
            self.state["gold"] += gain
            self.set_ground(fid, pos)
            self.record("\u51fb\u6740", pos, block.eid, before, "MT42 x9y8 whiteKing; live auto-clears " + ", ".join(picked))
            self.after_action(fid, pos, block)
            self.apply_check_damage(fid, pos, note)
            self.trigger_tile_event(fid, pos)
            return
        if fid == "MT43" and pos == (11, 7) and block.kind == "item" and block.eid == "redPotion":
            before = self.snapshot()
            self.apply_item(fid, block.eid)
            self.set_ground(fid, pos)
            key = self.block_at(fid, (10, 8))
            if key and key.kind == "item" and key.eid == "yellowKey":
                self.apply_item(fid, key.eid)
                self.set_ground(fid, (10, 8))
            self.record("拾取", pos, block.eid, before, "MT43 x11y7 redPotion; live auto-picks x10y8 yellowKey")
            self.after_action(fid, pos, block)
            self.apply_check_damage(fid, pos, note)
            self.trigger_tile_event(fid, pos)
            return
        if fid == "MT43" and pos == (10, 10) and block.kind == "enemy" and block.eid == "redBat":
            before = self.snapshot()
            dmg = self.enemy_damage(block.eid)
            if dmg == float("inf"):
                self.fail("MT43 x10y10 redBat is not killable")
            gain = int(self.enemies[block.eid].get("money", 0))
            if self.state.get("coin"):
                gain *= 2
            self.state["hp"] -= int(dmg)
            self.state["dmg"] += int(dmg)
            self.state["gold"] += gain
            self.set_ground(fid, pos)
            cleared: list[str] = []
            for enemy_pos, expected in [
                ((4, 4), "redWizard"),
                ((9, 7), "brownWizard"),
            ]:
                enemy = self.block_at(fid, enemy_pos)
                if not enemy or enemy.kind != "enemy" or enemy.eid != expected:
                    continue
                dmg2 = self.enemy_damage(enemy.eid)
                if dmg2 == float("inf"):
                    self.fail(f"MT43 live auto {enemy.eid} is not killable")
                gain2 = int(self.enemies[enemy.eid].get("money", 0))
                if self.state.get("coin"):
                    gain2 *= 2
                self.state["hp"] -= int(dmg2)
                self.state["dmg"] += int(dmg2)
                self.state["gold"] += gain2
                self.set_ground(fid, enemy_pos)
                self.after_action(fid, enemy_pos, enemy)
                cleared.append(f"x{enemy_pos[0]}y{enemy_pos[1]} {enemy.eid}")
            self.record("\u51fb\u6740", pos, block.eid, before, "MT43 x10y10 redBat; live auto-clears " + ", ".join(cleared))
            self.after_action(fid, pos, block)
            self.apply_check_damage(fid, pos, note)
            self.trigger_tile_event(fid, pos)
            return
        if fid == "MT43" and pos == (6, 3) and block.kind == "enemy" and block.eid == "darkKnight":
            before = self.snapshot()
            dmg = self.enemy_damage(block.eid)
            if dmg == float("inf"):
                self.fail("MT43 x6y3 darkKnight is not killable")
            gain = int(self.enemies[block.eid].get("money", 0))
            if self.state.get("coin"):
                gain *= 2
            self.state["hp"] -= int(dmg)
            self.state["dmg"] += int(dmg)
            self.state["gold"] += gain
            self.set_ground(fid, pos)
            cleared: list[str] = []
            side = self.block_at(fid, (7, 4))
            if side and side.kind == "enemy" and side.eid == "darkKnight":
                dmg2 = self.enemy_damage(side.eid)
                if dmg2 == float("inf"):
                    self.fail("MT43 live auto x7y4 darkKnight is not killable")
                gain2 = int(self.enemies[side.eid].get("money", 0))
                if self.state.get("coin"):
                    gain2 *= 2
                self.state["hp"] -= int(dmg2)
                self.state["dmg"] += int(dmg2)
                self.state["gold"] += gain2
                self.set_ground(fid, (7, 4))
                self.after_action(fid, (7, 4), side)
                cleared.append("x7y4 darkKnight")
            self.record("\u51fb\u6740", pos, block.eid, before, "MT43 x6y3 darkKnight; live auto-clears " + ", ".join(cleared))
            self.after_action(fid, pos, block)
            self.apply_check_damage(fid, pos, note)
            self.trigger_tile_event(fid, pos)
            return
        if (
            fid == "MT43"
            and pos == (8, 6)
            and block.kind == "door"
            and block.eid == "yellowDoor"
            and self.segment == "post-shield to 49 boss"
        ):
            before = self.snapshot()
            self.set_ground(fid, pos)
            self.record("\u5230\u8fbe", pos, None, before, "MT43 x8y6 live has no yellow door; pass without key")
            self.apply_check_damage(fid, pos, note)
            self.trigger_tile_event(fid, pos)
            return
        if fid == "MT44" and pos == (6, 7) and block.kind == "item" and block.eid == "redPotion":
            before = self.snapshot()
            self.apply_item(fid, block.eid)
            self.set_ground(fid, pos)
            shield = self.block_at(fid, (6, 6))
            picked: list[str] = []
            if shield and shield.kind == "item" and shield.eid == "shield5":
                self.apply_item(fid, shield.eid)
                self.set_ground(fid, (6, 6))
                self.after_action(fid, (6, 6), shield)
                picked.append("x6y6 shield5")
            note2 = "MT44 x6y7 redPotion"
            if picked:
                note2 += "; live auto-picks " + ", ".join(picked)
            self.record("\u62fe\u53d6", pos, block.eid, before, note2)
            self.after_action(fid, pos, block)
            self.apply_check_damage(fid, pos, note)
            self.trigger_tile_event(fid, pos)
            return
        if fid == "MT43" and pos == (11, 9) and block.kind == "door" and block.eid == "yellowDoor":
            before = self.snapshot()
            self.state["yk"] -= 1
            self.state["yd"] += 1
            if self.state["yk"] < 0:
                self.fail("negative key after MT43 x11y9 live door")
            self.set_ground(fid, pos)
            blue = self.block_at(fid, (11, 11))
            if blue and blue.kind == "item" and blue.eid == "blueKey":
                self.apply_item(fid, blue.eid)
                self.set_ground(fid, (11, 11))
            self.record("开门", pos, block.eid, before, "MT43 x11y9 yellowDoor; live auto-picks x11y11 blueKey")
            self.after_action(fid, pos, block)
            self.apply_check_damage(fid, pos, note)
            self.trigger_tile_event(fid, pos)
            return
        if fid == "MT46" and pos == (6, 11) and block.kind == "door" and block.eid == "blueDoor":
            before = self.snapshot()
            self.state["bk"] -= 1
            self.state["bd"] += 1
            if self.state["bk"] < 0:
                self.fail("negative blue key after MT46 x6y11 live door")
            self.set_ground(fid, pos)
            cleared: list[str] = []
            for enemy_pos, expected in [
                ((4, 11), "redSlime"),
                ((2, 11), "skeleton"),
                ((1, 10), "bigBat"),
                ((1, 8), "zombie"),
                ((1, 6), "soldier"),
                ((3, 6), "swordsman"),
                ((5, 6), "redKnight"),
                ((5, 8), "slimelord"),
            ]:
                enemy = self.block_at(fid, enemy_pos)
                if not enemy or enemy.kind != "enemy" or enemy.eid != expected:
                    continue
                dmg = self.enemy_damage(enemy.eid)
                if dmg == float("inf"):
                    self.fail(f"MT46 live auto {enemy.eid} is not killable")
                gain = int(self.enemies[enemy.eid].get("money", 0))
                if self.state.get("coin"):
                    gain *= 2
                self.state["hp"] -= int(dmg)
                self.state["dmg"] += int(dmg)
                self.state["gold"] += gain
                self.set_ground(fid, enemy_pos)
                self.after_action(fid, enemy_pos, enemy)
                cleared.append(f"x{enemy_pos[0]}y{enemy_pos[1]} {enemy.eid}")
            self.record("\u5f00\u95e8", pos, block.eid, before, "MT46 x6y11 blueDoor; live auto-clears " + ", ".join(cleared))
            self.after_action(fid, pos, block)
            self.apply_check_damage(fid, pos, note)
            self.trigger_tile_event(fid, pos)
            return
        if fid == "MT41" and pos == (5, 6) and block.kind == "door" and block.eid == "blueDoor":
            before = self.snapshot()
            self.state["bk"] -= 1
            self.state["bd"] += 1
            if self.state["bk"] < 0:
                self.fail("negative blue key after MT41 x5y6 live door")
            self.set_ground(fid, pos)
            picked: list[str] = []
            enemy = self.block_at(fid, (4, 7))
            if enemy and enemy.kind == "enemy" and enemy.eid == "slimelord":
                dmg = self.enemy_damage(enemy.eid)
                if dmg == float("inf"):
                    self.fail("MT41 live auto slimelord is not killable")
                gain = int(self.enemies[enemy.eid].get("money", 0))
                if self.state.get("coin"):
                    gain *= 2
                self.state["hp"] -= int(dmg)
                self.state["dmg"] += int(dmg)
                self.state["gold"] += gain
                self.set_ground(fid, (4, 7))
                self.after_action(fid, (4, 7), enemy)
                picked.append("x4y7 slimelord")
            for item_pos, expected in [
                ((4, 10), "yellowKey"),
                ((4, 11), "redGem"),
                ((3, 10), "yellowKey"),
                ((3, 11), "yellowKey"),
            ]:
                item = self.block_at(fid, item_pos)
                if not item or item.kind != "item" or item.eid != expected:
                    continue
                self.apply_item(fid, item.eid)
                self.set_ground(fid, item_pos)
                self.after_action(fid, item_pos, item)
                picked.append(f"x{item_pos[0]}y{item_pos[1]} {item.eid}")
            self.record("\u5f00\u95e8", pos, block.eid, before, "MT41 x5y6 blueDoor; live auto-clears " + ", ".join(picked))
            self.after_action(fid, pos, block)
            self.apply_check_damage(fid, pos, note)
            self.trigger_tile_event(fid, pos)
            return
        if fid == "MT41" and pos == (7, 6) and block.kind == "door" and block.eid == "blueDoor":
            before = self.snapshot()
            self.state["bk"] -= 1
            self.state["bd"] += 1
            if self.state["bk"] < 0:
                self.fail("negative blue key after MT41 x7y6 live door")
            self.set_ground(fid, pos)
            picked: list[str] = []
            enemy = self.block_at(fid, (8, 7))
            if enemy and enemy.kind == "enemy" and enemy.eid == "slimelord":
                dmg = self.enemy_damage(enemy.eid)
                if dmg == float("inf"):
                    self.fail("MT41 live auto right slimelord is not killable")
                gain = int(self.enemies[enemy.eid].get("money", 0))
                if self.state.get("coin"):
                    gain *= 2
                self.state["hp"] -= int(dmg)
                self.state["dmg"] += int(dmg)
                self.state["gold"] += gain
                self.set_ground(fid, (8, 7))
                self.after_action(fid, (8, 7), enemy)
                picked.append("x8y7 slimelord")
            for item_pos, expected in [
                ((8, 10), "yellowKey"),
                ((8, 11), "blueGem"),
                ((9, 10), "yellowKey"),
                ((9, 11), "yellowKey"),
            ]:
                item = self.block_at(fid, item_pos)
                if not item or item.kind != "item" or item.eid != expected:
                    continue
                self.apply_item(fid, item.eid)
                self.set_ground(fid, item_pos)
                self.after_action(fid, item_pos, item)
                picked.append(f"x{item_pos[0]}y{item_pos[1]} {item.eid}")
            self.record("\u5f00\u95e8", pos, block.eid, before, "MT41 x7y6 blueDoor; live auto-clears " + ", ".join(picked))
            self.after_action(fid, pos, block)
            self.apply_check_damage(fid, pos, note)
            self.trigger_tile_event(fid, pos)
            return
        if fid == "MT47" and pos == (2, 6) and block.kind == "door" and block.eid == "yellowDoor":
            before = self.snapshot()
            self.state["yk"] -= 1
            self.state["yd"] += 1
            if self.state["yk"] < 0:
                self.fail("negative yellow key after MT47 x2y6 live door")
            self.set_ground(fid, pos)
            cleared: list[str] = []
            bat = self.block_at(fid, (3, 5))
            if bat and bat.kind == "enemy" and bat.eid == "redBat":
                dmg = self.enemy_damage(bat.eid)
                if dmg == float("inf"):
                    self.fail("MT47 live auto x3y5 redBat is not killable")
                gain = int(self.enemies[bat.eid].get("money", 0))
                if self.state.get("coin"):
                    gain *= 2
                self.state["hp"] -= int(dmg)
                self.state["dmg"] += int(dmg)
                self.state["gold"] += gain
                self.set_ground(fid, (3, 5))
                self.after_action(fid, (3, 5), bat)
                cleared.append("x3y5 redBat")
            self.record("\u5f00\u95e8", pos, block.eid, before, "MT47 x2y6 yellowDoor; live auto-clears " + ", ".join(cleared))
            self.after_action(fid, pos, block)
            self.apply_check_damage(fid, pos, note)
            self.trigger_tile_event(fid, pos)
            return
        if fid == "MT47" and pos == (4, 4) and block.kind == "door" and block.eid == "yellowDoor":
            before = self.snapshot()
            self.state["yk"] -= 1
            self.state["yd"] += 1
            if self.state["yk"] < 0:
                self.fail("negative yellow key after MT47 x4y4 live door")
            self.set_ground(fid, pos)
            picked: list[str] = []
            for enemy_pos, expected in [
                ((5, 4), "redWizard"),
                ((6, 5), "brownWizard"),
            ]:
                enemy = self.block_at(fid, enemy_pos)
                if not enemy or enemy.kind != "enemy" or enemy.eid != expected:
                    continue
                dmg = self.enemy_damage(enemy.eid)
                if dmg == float("inf"):
                    self.fail(f"MT47 live auto {enemy.eid} is not killable")
                gain = int(self.enemies[enemy.eid].get("money", 0))
                if self.state.get("coin"):
                    gain *= 2
                self.state["hp"] -= int(dmg)
                self.state["dmg"] += int(dmg)
                self.state["gold"] += gain
                self.set_ground(fid, enemy_pos)
                self.after_action(fid, enemy_pos, enemy)
                picked.append(f"x{enemy_pos[0]}y{enemy_pos[1]} {enemy.eid}")
            for item_pos, expected in [
                ((5, 7), "blueKey"),
                ((5, 8), "redGem"),
                ((6, 7), "yellowKey"),
                ((6, 8), "blueGem"),
            ]:
                item = self.block_at(fid, item_pos)
                if not item or item.kind != "item" or item.eid != expected:
                    continue
                self.apply_item(fid, item.eid)
                self.set_ground(fid, item_pos)
                self.after_action(fid, item_pos, item)
                picked.append(f"x{item_pos[0]}y{item_pos[1]} {item.eid}")
            self.record("\u5f00\u95e8", pos, block.eid, before, "MT47 x4y4 yellowDoor; live auto-clears " + ", ".join(picked))
            self.after_action(fid, pos, block)
            self.apply_check_damage(fid, pos, note)
            self.trigger_tile_event(fid, pos)
            return
        if fid == "MT46" and pos == (3, 4) and block.kind == "door" and block.eid == "yellowDoor":
            before = self.snapshot()
            self.state["yk"] -= 1
            self.state["yd"] += 1
            if self.state["yk"] < 0:
                self.fail("negative yellow key after MT46 x3y4 live door")
            self.set_ground(fid, pos)
            picked: list[str] = []
            for enemy_pos, expected in [
                ((2, 4), "brownWizard"),
                ((2, 1), "redWizard"),
            ]:
                enemy = self.block_at(fid, enemy_pos)
                if not enemy or enemy.kind != "enemy" or enemy.eid != expected:
                    continue
                dmg = self.enemy_damage(enemy.eid)
                if dmg == float("inf"):
                    self.fail(f"MT46 live auto {enemy.eid} is not killable")
                gain = int(self.enemies[enemy.eid].get("money", 0))
                if self.state.get("coin"):
                    gain *= 2
                self.state["hp"] -= int(dmg)
                self.state["dmg"] += int(dmg)
                self.state["gold"] += gain
                self.set_ground(fid, enemy_pos)
                self.after_action(fid, enemy_pos, enemy)
                picked.append(f"x{enemy_pos[0]}y{enemy_pos[1]} {enemy.eid}")
            gem = self.block_at(fid, (1, 3))
            if gem and gem.kind == "item" and gem.eid == "redGem":
                self.apply_item(fid, gem.eid)
                self.set_ground(fid, (1, 3))
                self.after_action(fid, (1, 3), gem)
                picked.append("x1y3 redGem")
            self.record("\u5f00\u95e8", pos, block.eid, before, "MT46 x3y4 yellowDoor; live auto-clears " + ", ".join(picked))
            self.after_action(fid, pos, block)
            self.apply_check_damage(fid, pos, note)
            self.trigger_tile_event(fid, pos)
            return
        if fid == "MT48" and pos == (4, 6) and block.kind == "door" and block.eid == "yellowDoor":
            before = self.snapshot()
            self.state["yk"] -= 1
            self.state["yd"] += 1
            if self.state["yk"] < 0:
                self.fail("negative yellow key after MT48 x4y6 live door")
            self.set_ground(fid, pos)
            picked: list[str] = []
            enemy = self.block_at(fid, (4, 7))
            if enemy and enemy.kind == "enemy" and enemy.eid == "brownWizard":
                dmg = self.enemy_damage(enemy.eid)
                if dmg == float("inf"):
                    self.fail("MT48 live auto x4y7 brownWizard is not killable")
                gain = int(self.enemies[enemy.eid].get("money", 0))
                if self.state.get("coin"):
                    gain *= 2
                self.state["hp"] -= int(dmg)
                self.state["dmg"] += int(dmg)
                self.state["gold"] += gain
                self.set_ground(fid, (4, 7))
                self.after_action(fid, (4, 7), enemy)
                picked.append("x4y7 brownWizard")
            gem = self.block_at(fid, (3, 8))
            if gem and gem.kind == "item" and gem.eid == "redGem":
                self.apply_item(fid, gem.eid)
                self.set_ground(fid, (3, 8))
                self.after_action(fid, (3, 8), gem)
                picked.append("x3y8 redGem")
            self.record("\u5f00\u95e8", pos, block.eid, before, "MT48 x4y6 yellowDoor; live auto-clears " + ", ".join(picked))
            self.after_action(fid, pos, block)
            self.apply_check_damage(fid, pos, note)
            self.trigger_tile_event(fid, pos)
            return
        if fid == "MT48" and pos == (4, 9) and block.kind == "door" and block.eid == "yellowDoor":
            before = self.snapshot()
            self.state["yk"] -= 1
            self.state["yd"] += 1
            if self.state["yk"] < 0:
                self.fail("negative yellow key after MT48 x4y9 live door")
            self.set_ground(fid, pos)
            picked: list[str] = []
            gem = self.block_at(fid, (3, 11))
            if gem and gem.kind == "item" and gem.eid == "blueGem":
                self.apply_item(fid, gem.eid)
                self.set_ground(fid, (3, 11))
                self.after_action(fid, (3, 11), gem)
                picked.append("x3y11 blueGem")
            for enemy_pos, expected in [
                ((4, 10), "darkKnight"),
                ((7, 3), "whiteKing"),
                ((9, 3), "whiteKing"),
                ((7, 5), "whiteKing"),
                ((9, 5), "whiteKing"),
            ]:
                enemy = self.block_at(fid, enemy_pos)
                if not enemy or enemy.kind != "enemy" or enemy.eid != expected:
                    continue
                dmg = self.enemy_damage(enemy.eid)
                if dmg == float("inf"):
                    self.fail(f"MT48 live auto {enemy.eid} is not killable")
                gain = int(self.enemies[enemy.eid].get("money", 0))
                if self.state.get("coin"):
                    gain *= 2
                self.state["hp"] -= int(dmg)
                self.state["dmg"] += int(dmg)
                self.state["gold"] += gain
                self.set_ground(fid, enemy_pos)
                self.after_action(fid, enemy_pos, enemy)
                picked.append(f"x{enemy_pos[0]}y{enemy_pos[1]} {enemy.eid}")
            self.record("\u5f00\u95e8", pos, block.eid, before, "MT48 x4y9 yellowDoor; live auto-clears " + ", ".join(picked))
            self.after_action(fid, pos, block)
            self.apply_check_damage(fid, pos, note)
            self.trigger_tile_event(fid, pos)
            return
        if fid == "MT41" and pos == (9, 5) and block.kind == "enemy" and block.eid == "brownWizard":
            before = self.snapshot()
            dmg = self.enemy_damage(block.eid)
            if dmg == float("inf"):
                self.fail("MT41 x9y5 brownWizard is not killable")
            gain = int(self.enemies[block.eid].get("money", 0))
            if self.state.get("coin"):
                gain *= 2
            self.state["hp"] -= int(dmg)
            self.state["dmg"] += int(dmg)
            self.state["gold"] += gain
            self.set_ground(fid, pos)
            blue = self.block_at(fid, (8, 1))
            if blue and blue.kind == "item" and blue.eid == "blueKey":
                self.apply_item(fid, blue.eid)
                self.set_ground(fid, (8, 1))
                self.after_action(fid, (8, 1), blue)
            self.record("\u51fb\u6740", pos, block.eid, before, "MT41 x9y5 brownWizard; live auto-picks x8y1 blueKey")
            self.after_action(fid, pos, block)
            self.apply_check_damage(fid, pos, note)
            self.trigger_tile_event(fid, pos)
            return
        if fid == "MT41" and pos == (3, 5) and block.kind == "enemy" and block.eid == "brownWizard":
            before = self.snapshot()
            dmg = self.enemy_damage(block.eid)
            if dmg == float("inf"):
                self.fail("MT41 x3y5 brownWizard is not killable")
            gain = int(self.enemies[block.eid].get("money", 0))
            if self.state.get("coin"):
                gain *= 2
            self.state["hp"] -= int(dmg)
            self.state["dmg"] += int(dmg)
            self.state["gold"] += gain
            self.set_ground(fid, pos)
            cleared: list[str] = []
            for enemy_pos, expected in [
                ((1, 6), "redBat"),
                ((11, 6), "redBat"),
                ((2, 7), "redBat"),
                ((10, 7), "redBat"),
            ]:
                enemy = self.block_at(fid, enemy_pos)
                if not enemy or enemy.kind != "enemy" or enemy.eid != expected:
                    continue
                dmg2 = self.enemy_damage(enemy.eid)
                if dmg2 == float("inf"):
                    self.fail(f"MT41 live auto {enemy.eid} is not killable")
                gain2 = int(self.enemies[enemy.eid].get("money", 0))
                if self.state.get("coin"):
                    gain2 *= 2
                self.state["hp"] -= int(dmg2)
                self.state["dmg"] += int(dmg2)
                self.state["gold"] += gain2
                self.set_ground(fid, enemy_pos)
                self.after_action(fid, enemy_pos, enemy)
                cleared.append(f"x{enemy_pos[0]}y{enemy_pos[1]} {enemy.eid}")
            self.record("\u51fb\u6740", pos, block.eid, before, "MT41 x3y5 brownWizard; live auto-clears " + ", ".join(cleared))
            self.after_action(fid, pos, block)
            self.apply_check_damage(fid, pos, note)
            self.trigger_tile_event(fid, pos)
            return
        if fid == "MT31" and pos == (1, 7) and block.kind == "door" and block.eid == "yellowDoor":
            before = self.snapshot()
            self.state["yk"] -= 1
            self.state["yd"] += 1
            if self.state["yk"] < 0:
                self.fail("negative yellow key after MT31 x1y7 live door")
            self.set_ground(fid, pos)
            cleared: list[str] = []
            for enemy_pos, expected in [
                ((2, 9), "ghostSkeleton"),
                ((4, 10), "redKnight"),
                ((1, 9), "ghostSkeleton"),
            ]:
                enemy = self.block_at(fid, enemy_pos)
                if not enemy or enemy.kind != "enemy" or enemy.eid != expected:
                    continue
                dmg = self.enemy_damage(enemy.eid)
                if dmg == float("inf"):
                    self.fail(f"MT31 live auto {enemy.eid} is not killable")
                gain = int(self.enemies[enemy.eid].get("money", 0))
                if self.state.get("coin"):
                    gain *= 2
                self.state["hp"] -= int(dmg)
                self.state["dmg"] += int(dmg)
                self.state["gold"] += gain
                self.set_ground(fid, enemy_pos)
                self.after_action(fid, enemy_pos, enemy)
                cleared.append(f"x{enemy_pos[0]}y{enemy_pos[1]} {enemy.eid}")
            self.record("\u5f00\u95e8", pos, block.eid, before, "MT31 x1y7 yellowDoor; live auto-clears " + ", ".join(cleared))
            self.after_action(fid, pos, block)
            self.apply_check_damage(fid, pos, note)
            self.trigger_tile_event(fid, pos)
            return
        if fid == "MT33" and pos == (5, 4) and block.kind == "door" and block.eid == "yellowDoor":
            before = self.snapshot()
            self.state["yk"] -= 1
            self.state["yd"] += 1
            if self.state["yk"] < 0:
                self.fail("negative yellow key after MT33 x5y4 live door")
            self.set_ground(fid, pos)
            cleared: list[str] = []
            for enemy_pos, expected in [
                ((4, 6), "swordsman"),
                ((6, 7), "ghostSkeleton"),
                ((6, 5), "zombieKnight"),
            ]:
                enemy = self.block_at(fid, enemy_pos)
                if not enemy or enemy.kind != "enemy" or enemy.eid != expected:
                    continue
                dmg = self.enemy_damage(enemy.eid)
                if dmg == float("inf"):
                    self.fail(f"MT33 live auto {enemy.eid} is not killable")
                gain = int(self.enemies[enemy.eid].get("money", 0))
                if self.state.get("coin"):
                    gain *= 2
                self.state["hp"] -= int(dmg)
                self.state["dmg"] += int(dmg)
                self.state["gold"] += gain
                self.set_ground(fid, enemy_pos)
                self.after_action(fid, enemy_pos, enemy)
                cleared.append(f"x{enemy_pos[0]}y{enemy_pos[1]} {enemy.eid}")
            self.record("\u5f00\u95e8", pos, block.eid, before, "MT33 x5y4 yellowDoor; live auto-clears " + ", ".join(cleared))
            self.after_action(fid, pos, block)
            self.apply_check_damage(fid, pos, note)
            self.trigger_tile_event(fid, pos)
            return
        if fid == "MT33" and pos == (3, 7) and block.kind == "door" and block.eid == "yellowDoor":
            before = self.snapshot()
            self.state["yk"] -= 1
            self.state["yd"] += 1
            if self.state["yk"] < 0:
                self.fail("negative yellow key after MT33 x3y7 live door")
            self.set_ground(fid, pos)
            cleared: list[str] = []
            for enemy_pos, expected in [((2, 7), "slimeMan"), ((1, 5), "slimeMan")]:
                enemy = self.block_at(fid, enemy_pos)
                if not enemy or enemy.kind != "enemy" or enemy.eid != expected:
                    continue
                dmg = self.enemy_damage(enemy.eid)
                if dmg == float("inf"):
                    self.fail(f"MT33 live auto {enemy.eid} is not killable")
                gain = int(self.enemies[enemy.eid].get("money", 0))
                if self.state.get("coin"):
                    gain *= 2
                self.state["hp"] -= int(dmg)
                self.state["dmg"] += int(dmg)
                self.state["gold"] += gain
                self.set_ground(fid, enemy_pos)
                self.after_action(fid, enemy_pos, enemy)
                cleared.append(f"x{enemy_pos[0]}y{enemy_pos[1]} {enemy.eid}")
            self.record("\u5f00\u95e8", pos, block.eid, before, "MT33 x3y7 yellowDoor; live auto-clears " + ", ".join(cleared))
            self.after_action(fid, pos, block)
            self.apply_check_damage(fid, pos, note)
            self.trigger_tile_event(fid, pos)
            return
        if fid == "MT33" and pos == (1, 8) and block.kind == "door" and block.eid == "yellowDoor":
            before = self.snapshot()
            self.set_ground(fid, pos)
            cleared: list[str] = []
            for enemy_pos, expected in [
                ((1, 10), "swordsman"),
                ((2, 11), "soldier"),
                ((3, 9), "zombieKnight"),
            ]:
                enemy = self.block_at(fid, enemy_pos)
                if not enemy or enemy.kind != "enemy" or enemy.eid != expected:
                    continue
                dmg = self.enemy_damage(enemy.eid)
                if dmg == float("inf"):
                    self.fail(f"MT33 live auto {enemy.eid} is not killable")
                gain = int(self.enemies[enemy.eid].get("money", 0))
                if self.state.get("coin"):
                    gain *= 2
                self.state["hp"] -= int(dmg)
                self.state["dmg"] += int(dmg)
                self.state["gold"] += gain
                self.set_ground(fid, enemy_pos)
                self.after_action(fid, enemy_pos, enemy)
                cleared.append(f"x{enemy_pos[0]}y{enemy_pos[1]} {enemy.eid}")
            self.record("\u5230\u8fbe", pos, None, before, "MT33 x1y8 live has no yellow door; live auto-clears " + ", ".join(cleared))
            self.apply_check_damage(fid, pos, note)
            self.trigger_tile_event(fid, pos)
            return
        if fid == "MT36" and pos == (10, 6) and block.kind == "door" and block.eid == "yellowDoor":
            before = self.snapshot()
            self.state["yk"] -= 1
            self.state["yd"] += 1
            if self.state["yk"] < 0:
                self.fail("negative yellow key after MT36 x10y6 live door")
            self.set_ground(fid, pos)
            cleared: list[str] = []
            for enemy_pos, expected in [
                ((7, 6), "slimeMan"),
                ((6, 7), "redKnight"),
                ((6, 5), "ghostSkeleton"),
                ((5, 6), "slimeMan"),
            ]:
                enemy = self.block_at(fid, enemy_pos)
                if not enemy or enemy.kind != "enemy" or enemy.eid != expected:
                    continue
                dmg = self.enemy_damage(enemy.eid)
                if dmg == float("inf"):
                    self.fail(f"MT36 live auto {enemy.eid} is not killable")
                gain = int(self.enemies[enemy.eid].get("money", 0))
                if self.state.get("coin"):
                    gain *= 2
                self.state["hp"] -= int(dmg)
                self.state["dmg"] += int(dmg)
                self.state["gold"] += gain
                self.set_ground(fid, enemy_pos)
                self.after_action(fid, enemy_pos, enemy)
                cleared.append(f"x{enemy_pos[0]}y{enemy_pos[1]} {enemy.eid}")
            self.record("\u5f00\u95e8", pos, block.eid, before, "MT36 x10y6 yellowDoor; live auto-clears " + ", ".join(cleared))
            self.after_action(fid, pos, block)
            self.apply_check_damage(fid, pos, note)
            self.trigger_tile_event(fid, pos)
            return
        if fid == "MT42" and pos == (6, 4) and block.kind == "enemy" and block.eid == "darkKnight":
            before = self.snapshot()
            dmg = self.enemy_damage(block.eid)
            if dmg == float("inf"):
                self.fail("MT42 x6y4 darkKnight is not killable")
            gain = int(self.enemies[block.eid].get("money", 0))
            if self.state.get("coin"):
                gain *= 2
            self.state["hp"] -= int(dmg)
            self.state["dmg"] += int(dmg)
            self.state["gold"] += gain
            self.set_ground(fid, pos)
            picked: list[str] = []
            red_key = self.block_at(fid, (7, 1))
            if red_key and red_key.kind == "item" and red_key.eid == "redKey":
                self.apply_item(fid, red_key.eid)
                self.set_ground(fid, (7, 1))
                self.after_action(fid, (7, 1), red_key)
                picked.append("x7y1 redKey")
            for enemy_pos, expected in [
                ((11, 4), "redWizard"),
                ((9, 4), "brownWizard"),
                ((11, 6), "brownWizard"),
            ]:
                enemy = self.block_at(fid, enemy_pos)
                if not enemy or enemy.kind != "enemy" or enemy.eid != expected:
                    continue
                dmg2 = self.enemy_damage(enemy.eid)
                if dmg2 == float("inf"):
                    self.fail(f"MT42 live auto {enemy.eid} is not killable")
                gain2 = int(self.enemies[enemy.eid].get("money", 0))
                if self.state.get("coin"):
                    gain2 *= 2
                self.state["hp"] -= int(dmg2)
                self.state["dmg"] += int(dmg2)
                self.state["gold"] += gain2
                self.set_ground(fid, enemy_pos)
                self.after_action(fid, enemy_pos, enemy)
                picked.append(f"x{enemy_pos[0]}y{enemy_pos[1]} {enemy.eid}")
            self.record("\u51fb\u6740", pos, block.eid, before, "MT42 x6y4 darkKnight; live auto-clears " + ", ".join(picked))
            self.after_action(fid, pos, block)
            self.apply_check_damage(fid, pos, note)
            self.trigger_tile_event(fid, pos)
            return
        if fid == "MT45" and pos == (3, 6) and block.kind == "enemy" and block.eid == "darkKnight":
            before = self.snapshot()
            dmg = self.enemy_damage(block.eid)
            if dmg == float("inf"):
                self.fail("MT45 x3y6 darkKnight is not killable")
            gain = int(self.enemies[block.eid].get("money", 0))
            if self.state.get("coin"):
                gain *= 2
            self.state["hp"] -= int(dmg)
            self.state["dmg"] += int(dmg)
            self.state["gold"] += gain
            self.set_ground(fid, pos)
            picked: list[str] = []
            for item_pos, expected in [
                ((2, 3), "redGem"),
                ((1, 3), "redGem"),
                ((2, 5), "blueGem"),
                ((1, 5), "blueGem"),
                ((11, 7), "yellowKey"),
            ]:
                item = self.block_at(fid, item_pos)
                if not item or item.kind != "item" or item.eid != expected:
                    continue
                self.apply_item(fid, item.eid)
                self.set_ground(fid, item_pos)
                self.after_action(fid, item_pos, item)
                picked.append(f"x{item_pos[0]}y{item_pos[1]} {item.eid}")
            for enemy_pos, expected in [
                ((3, 4), "darkKnight"),
                ((7, 7), "redBat"),
                ((10, 8), "redWizard"),
                ((7, 3), "redWizard"),
                ((5, 5), "redWizard"),
                ((7, 5), "brownWizard"),
            ]:
                enemy = self.block_at(fid, enemy_pos)
                if not enemy or enemy.kind != "enemy" or enemy.eid != expected:
                    continue
                dmg2 = self.enemy_damage(enemy.eid)
                if dmg2 == float("inf"):
                    self.fail(f"MT45 live auto {enemy.eid} is not killable")
                gain2 = int(self.enemies[enemy.eid].get("money", 0))
                if self.state.get("coin"):
                    gain2 *= 2
                self.state["hp"] -= int(dmg2)
                self.state["dmg"] += int(dmg2)
                self.state["gold"] += gain2
                self.set_ground(fid, enemy_pos)
                self.after_action(fid, enemy_pos, enemy)
                picked.append(f"x{enemy_pos[0]}y{enemy_pos[1]} {enemy.eid}")
            self.record("\u51fb\u6740", pos, block.eid, before, "MT45 x3y6 darkKnight; live auto-clears " + ", ".join(picked))
            self.after_action(fid, pos, block)
            self.apply_check_damage(fid, pos, note)
            self.trigger_tile_event(fid, pos)
            return
        if fid == "MT48" and pos == (3, 5) and block.kind == "enemy" and block.eid == "slimelord":
            before = self.snapshot()
            dmg = self.enemy_damage(block.eid)
            if dmg == float("inf"):
                self.fail("MT48 x3y5 slimelord is not killable")
            gain = int(self.enemies[block.eid].get("money", 0))
            if self.state.get("coin"):
                gain *= 2
            self.state["hp"] -= int(dmg)
            self.state["dmg"] += int(dmg)
            self.state["gold"] += gain
            self.set_ground(fid, pos)
            cleared: list[str] = []
            for enemy_pos, expected in [
                ((1, 7), "redBat"),
                ((1, 9), "brownWizard"),
            ]:
                enemy = self.block_at(fid, enemy_pos)
                if not enemy or enemy.kind != "enemy" or enemy.eid != expected:
                    continue
                dmg2 = self.enemy_damage(enemy.eid)
                if dmg2 == float("inf"):
                    self.fail(f"MT48 live auto {enemy.eid} is not killable")
                gain2 = int(self.enemies[enemy.eid].get("money", 0))
                if self.state.get("coin"):
                    gain2 *= 2
                self.state["hp"] -= int(dmg2)
                self.state["dmg"] += int(dmg2)
                self.state["gold"] += gain2
                self.set_ground(fid, enemy_pos)
                self.after_action(fid, enemy_pos, enemy)
                cleared.append(f"x{enemy_pos[0]}y{enemy_pos[1]} {enemy.eid}")
            self.record("\u51fb\u6740", pos, block.eid, before, "MT48 x3y5 slimelord; live auto-clears " + ", ".join(cleared))
            self.after_action(fid, pos, block)
            self.apply_check_damage(fid, pos, note)
            self.trigger_tile_event(fid, pos)
            return
        if fid == "MT31" and pos == (11, 5) and block.kind == "door" and block.eid == "yellowDoor":
            side = self.block_at("MT31", (11, 10))
            before = self.snapshot()
            self.state["yk"] -= 1
            self.state["yd"] += 1
            if self.state["yk"] < 0:
                self.fail("negative key after MT31 x11y5 live door")
            self.set_ground("MT31", (11, 5))
            if side:
                self.set_ground("MT31", (11, 10))
                # Live verification shows this target click gives +100G while
                # leaving HP/stats unchanged. Keep the exact observed value here
                # instead of guessing a stale local enemy definition.
                self.state["gold"] += 100
            self.record("开门", pos, block.eid, before, "MT31 x11y5; live auto clears MT31 x11y10 for +100G")
            self.after_action(fid, pos, block)
            self.apply_check_damage(fid, pos, note)
            self.trigger_tile_event(fid, pos)
            return
        original_apply_block(self, fid, pos, block, note)

    def use_earthquake(self: Any, note: str = "") -> None:
        if self.state["floor"] != "MT37":
            original_use_earthquake(self, note)
            return
        if self.state["earthquake"] <= 0:
            self.fail("no earthquake")
        before = self.snapshot()
        self.state["earthquake"] -= 1
        fid = self.state["floor"]
        opened = 0
        for wall_pos, wall in list(self.floors[fid].blocks.items()):
            if wall.eid in post.WALL_IDS and wall.eid not in {"unbreakableWall", "blockWall"}:
                self.set_ground(fid, wall_pos)
                opened += 1
        auto_items = [
            (5, 4), (5, 5), (4, 5), (3, 5), (7, 5), (8, 5), (9, 5),
            (3, 7), (4, 7), (7, 7), (8, 7), (9, 7),
            (5, 8), (4, 8), (3, 8), (7, 8), (8, 8), (9, 8),
            (4, 9), (5, 9), (8, 9),
        ]
        picked: list[str] = []
        for item_pos in auto_items:
            item = self.block_at(fid, item_pos)
            if not item or item.kind != "item" or item.eid in {"redPotion", "bluePotion"}:
                continue
            self.apply_item(fid, item.eid)
            self.set_ground(fid, item_pos)
            self.after_action(fid, item_pos, item)
            picked.append(f"x{item_pos[0]}y{item_pos[1]} {item.eid}")
        self.state["x"] = 6
        self.state["y"] = 6
        self.record("\u5730\u9707\u5377\u8f74", (6, 6), "earthquake", before, f"{note}; opened={opened}; live auto-picks {', '.join(picked)}")
        potion = self.block_at("MT37", (7, 4))
        if potion and potion.kind == "item" and potion.eid == "redPotion":
            self.go_to("MT37", 7, 4, "37F redPotion to survive 45F return")
        self.go_to("MT37", 11, 10, "37F earthquake auto resources -> fly use point")

    def go_to(self: Any, fid: str, x: int, y: int, note: str = "") -> None:
        if (
            fid == "MT37"
            and (x, y) == (11, 10)
            and self.state["floor"] == "MT37"
            and (self.state["x"], self.state["y"]) == (7, 4)
        ):
            path_potions: list[tuple[tuple[int, int], Any]] = []
            for potion_pos in [(8, 4), (9, 4)]:
                potion = self.block_at("MT37", potion_pos)
                if potion and potion.kind == "item" and potion.eid == "redPotion":
                    path_potions.append((potion_pos, potion))
            if path_potions:
                before = self.snapshot()
                for potion_pos, potion in path_potions:
                    self.apply_item("MT37", potion.eid)
                    self.set_ground("MT37", potion_pos)
                    self.after_action("MT37", potion_pos, potion)
                self.state["x"], self.state["y"] = 11, 10
                picked = ", ".join(f"x{px}y{py} {potion.eid}" for (px, py), potion in path_potions)
                self.record("\u5230\u8fbe", (11, 10), None, before, f"{note}; live path picks {picked}")
                return
        if (
            fid == "MT47"
            and (x, y) == (1, 8)
            and self.state["floor"] == "MT47"
            and self.block_at("MT47", (1, 9))
        ):
            before_step_count = len(self.steps)
            original_go_to(self, fid, x, y, note)
            if len(self.steps) <= before_step_count or (self.state["x"], self.state["y"]) != (1, 8):
                return
            picked: list[str] = []
            wiz_left = self.block_at("MT47", (1, 9))
            if wiz_left and wiz_left.kind == "enemy" and wiz_left.eid == "redWizard":
                self.set_ground("MT47", (1, 9))
                self.set_block("MT47", (1, 10), "enemy", "redWizard", wiz_left.tile)
                self.retreat_wizards.discard(("MT47", 1, 9))
                self.retreat_wizards.add(("MT47", 1, 10))
                picked.append("x1y9 redWizard retreats to x1y10")
            for enemy_pos, expected in [
                ((8, 3), "redWizard"),
                ((9, 3), "slimelord"),
            ]:
                enemy = self.block_at("MT47", enemy_pos)
                if not enemy or enemy.kind != "enemy" or enemy.eid != expected:
                    continue
                dmg = self.enemy_damage(enemy.eid)
                if dmg == float("inf"):
                    self.fail(f"MT47 live auto {enemy.eid} is not killable")
                gain = int(self.enemies[enemy.eid].get("money", 0))
                if self.state.get("coin"):
                    gain *= 2
                self.state["hp"] -= int(dmg)
                self.state["dmg"] += int(dmg)
                self.state["gold"] += gain
                self.set_ground("MT47", enemy_pos)
                self.after_action("MT47", enemy_pos, enemy)
                self.retreat_wizards.discard(("MT47", enemy_pos[0], enemy_pos[1]))
                picked.append(f"x{enemy_pos[0]}y{enemy_pos[1]} {enemy.eid}")
            if picked:
                last = self.steps[-1]
                last["after"] = self.snapshot()
                delta = []
                before = last["before"]
                after = last["after"]
                for key, label in [("hp", "HP"), ("atk", "ATK"), ("def", "DEF"), ("yk", "YK"), ("bk", "BK"), ("rk", "RK"), ("gold", "G")]:
                    if before[key] != after[key]:
                        delta.append(f"{label} {before[key]}->{after[key]}")
                last["delta"] = ", ".join(delta)
                extra = "live auto handles " + ", ".join(picked)
                last["note"] = f"{last.get('note', '')}; {extra}" if last.get("note") else extra
            return
        if (
            fid == "MT47"
            and (x, y) == (1, 10)
            and self.state["floor"] == "MT47"
            and self.block_at("MT47", (1, 11))
        ):
            before_step_count = len(self.steps)
            original_go_to(self, fid, x, y, note)
            if len(self.steps) <= before_step_count or (self.state["x"], self.state["y"]) != (1, 10):
                return
            wizard = self.block_at("MT47", (1, 11))
            if wizard and wizard.kind == "enemy" and wizard.eid == "redWizard":
                dmg = self.enemy_damage(wizard.eid)
                if dmg == float("inf"):
                    self.fail("MT47 live auto x1y11 redWizard is not killable")
                gain = int(self.enemies[wizard.eid].get("money", 0))
                if self.state.get("coin"):
                    gain *= 2
                self.state["hp"] -= int(dmg)
                self.state["dmg"] += int(dmg)
                self.state["gold"] += gain
                self.set_ground("MT47", (1, 11))
                self.after_action("MT47", (1, 11), wizard)
                self.retreat_wizards.discard(("MT47", 1, 11))
                last = self.steps[-1]
                last["after"] = self.snapshot()
                delta = []
                before = last["before"]
                after = last["after"]
                for key, label in [("hp", "HP"), ("atk", "ATK"), ("def", "DEF"), ("yk", "YK"), ("bk", "BK"), ("rk", "RK"), ("gold", "G")]:
                    if before[key] != after[key]:
                        delta.append(f"{label} {before[key]}->{after[key]}")
                last["delta"] = ", ".join(delta)
                extra = "live auto clears x1y11 redWizard"
                last["note"] = f"{last.get('note', '')}; {extra}" if last.get("note") else extra
            return
        if (
            fid == "MT45"
            and (x, y) == (2, 1)
            and self.state["floor"] == "MT45"
            and (self.state["x"], self.state["y"]) != (2, 1)
        ):
            block = self.block_at("MT45", (5, 3))
            if not block or block.kind != "enemy" or block.eid != "brownWizard":
                self.set_block("MT45", (5, 3), "enemy", "brownWizard", 219)
            if (self.state["x"], self.state["y"]) != (5, 3):
                original_go_to(self, "MT45", 5, 3, "45F return path live clears x5y3 brownWizard")
            original_go_to(self, fid, x, y, note)
            if self.steps and self.steps[-1]["pos"] == [2, 1]:
                self.state["hp"] -= 200
                self.state["dmg"] += 200
                if self.state["hp"] <= 0:
                    self.fail("MT45 live return field damage death")
                last = self.steps[-1]
                last["after"] = self.snapshot()
                delta = []
                before = last["before"]
                after = last["after"]
                for key, label in [("hp", "HP"), ("atk", "ATK"), ("def", "DEF"), ("yk", "YK"), ("bk", "BK"), ("rk", "RK"), ("gold", "G")]:
                    if before[key] != after[key]:
                        delta.append(f"{label} {before[key]}->{after[key]}")
                last["delta"] = ", ".join(delta)
                extra = "live return path takes extra MT45 x6y3 field damage"
                last["note"] = f"{last.get('note', '')}; {extra}" if last.get("note") else extra
            return
        original_go_to(self, fid, x, y, note)

    post.Game.apply_block = apply_block
    post.Game.use_earthquake = use_earthquake
    post.Game.go_to = go_to
    post.Game._mt42_tail_hooks_installed = True


def write_outputs(g: Any, args: argparse.Namespace) -> None:
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    score = score_mod.current_floor_and_below_final_score(g, 50, monster_gold_factor=0.5)
    data = {
        "ok": not g.errors,
        "name": "strict20_live_current_mt42_to50_tail_walk",
        "source_snapshot": str(args.snapshot.relative_to(ROOT) if args.snapshot.is_relative_to(ROOT) else args.snapshot),
        "base_counters": {
            "dmg": args.base_dmg,
            "yd": args.base_doors[0],
            "bd": args.base_doors[1],
            "rd": args.base_doors[2],
            "note": "Counters inherited from the old stitched route at the live MT42 checkpoint; live state is authoritative for stats/gold/keys/map.",
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
        "# MT42 当前实机点到 50F 尾段 walk",
        "",
        f"- 结果：{'通过' if not g.errors else '未通过'}",
        f"- 起点快照：`{data['source_snapshot']}`",
        f"- 终点：`{data['state_text']}`",
        f"- final-score<=50：`{score['final_score']:g}` (stock={score['stock_score']:g}, remaining={score['remaining_value_hp']:g}, zeroG={score['zero_damage_monster_value_hp']:g})",
        f"- 重要道具持有：`{score['held_tool_counts']}`；地图剩余：`{score['map_tool_counts']}`",
        "- 0伤怪计分函数：`scripts/floor_final_score.py::current_floor_and_below_final_score`。已清掉的怪只体现在当前金币；未清掉且当前0伤的怪仍留在地图资源里，因此不会双算。",
        "",
        "## 阶段",
        "",
        "| 阶段 | 状态 | 本段dmg | 累计dmg | 门 黄/蓝/红 | 库存折算 | 步数 |",
        "| --- | --- | ---: | ---: | --- | ---: | ---: |",
    ]
    for row in g.stage_summaries:
        after = row["after"]
        lines.append(
            f"| {row['label']} | `{state_text(after)}` | {row['delta_dmg']} | "
            f"{after['dmg']} | {after['yd']}/{after['bd']}/{after['rd']} | "
            f"{row['stock_score']:.1f} | {row['delta_steps']} |"
        )
    if g.errors:
        lines.extend(["", "## 错误", ""])
        lines.extend(f"- {error}" for error in g.errors)
    lines.extend(["", "## Walk", ""])
    for idx, step in enumerate(g.steps, 1):
        pos = step["pos"]
        delta = f" [{step['delta']}]" if step.get("delta") else ""
        note = f" ({step['note']})" if step.get("note") else ""
        lines.append(f"{idx:03d}. {step['segment']} - {step['floor']} x{pos[0]}y{pos[1]} {step['action']} {step.get('eid') or ''}{delta}{note}".rstrip())
    args.out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", type=Path, default=DEFAULT_SNAPSHOT)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    parser.add_argument("--base-dmg", type=int, default=10226)
    parser.add_argument("--base-doors", type=lambda s: tuple(int(x) for x in s.split(",")), default=(50, 3, 1))
    parser.add_argument(
        "--stop-after",
        choices=["mt42_to_48", "pre_earthquake", "farm_earthquake", "shield", "post_shield_49", "post_49_endgame"],
    )
    parser.add_argument("--trace", action="store_true")
    args = parser.parse_args()
    args.snapshot = args.snapshot.resolve()
    args.out_json = args.out_json.resolve()
    args.out_md = args.out_md.resolve()
    if len(args.base_doors) != 3:
        parser.error("--base-doors must be yellow,blue,red")
    return args


def main() -> int:
    args = parse_args()
    g = build_tail(args)
    write_outputs(g, args)
    print(f"ok={not g.errors}")
    print(f"final={state_text(g.snapshot())}")
    if g.errors:
        print("errors:")
        for error in g.errors:
            print("-", error)
    print(f"json={args.out_json}")
    print(f"md={args.out_md}")
    return 0 if not g.errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
