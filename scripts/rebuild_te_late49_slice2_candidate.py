#!/usr/bin/env python3
"""Rebuild the best RK=1 intermediate from te_late49 slice2 and try finishing 40F."""

from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


deadline = load_module("te_late49_slice2_deadline", ROOT / "scripts" / "report_zone3_deadline_candidate.py")
base = deadline.base
macro = deadline.macro
seeded = deadline.seeded


def rebuild():
    seeded.install_seeded_guidance()
    base0 = macro.start_to_right_resources("AA")
    farmed = macro.farm_targets(base0, [])
    g = copy.deepcopy(farmed)
    macro.sell(g, 2)
    macro.buy(g, "AA")
    sword = macro.try_sword(g)
    after2 = macro.after_sword_to_2f(sword)
    extra = macro.collect_extra_keys(after2)
    postg = copy.deepcopy(extra)
    macro.sell(postg, 1)
    macro.buy(postg, "DD")
    healed = macro.eat_potions_until(postg, 2200, preserve_yk=1)
    pre34 = macro.collect_pre34_keys(healed)
    done = macro.to_37_with_34_center(pre34)
    done = macro.try_take(done, "MT34", 1, 11, "slice2 bluePotion")
    base.move_to(done, "MT36", 1, 5, "slice2 redKnight")
    base.move_to(done, "MT32", 2, 2, "slice2 redGem")
    return done


def main() -> int:
    g = rebuild()
    print("intermediate", base.state_line(g), "dmg", g.state["dmg"], "door", g.state["yd"], g.state["bd"], g.state["rd"])
    try:
        out = base.finish_goal_candidate(copy.deepcopy(g))
        print("finish_goal", base.state_line(out), "dmg", out.state["dmg"], "door", out.state["yd"], out.state["bd"], out.state["rd"])
        print("errors", out.errors[:5])
    except Exception as exc:
        print("finish_goal_error", type(exc).__name__, exc)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
