#!/usr/bin/env python3
"""Intelligent auto-ON MT4->10 walk: go_to only main targets (stairs/weapons/
bosses/doors) extracted from the web record; auto_sweep picks up on-path
resources (keys/gems/potions/0-dmg enemies). Replaces the verbose auto-OFF
explicit-pickup walk."""
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from build_autooff_mt4_to_mt7_prefix_walk import AUTO_ON, set_auto_step, normalize_step
from search_post40_guide_route import RouteError

WEAPONS = {"sword1","shield1","sword2","shield2","sword3","shield3","sword4","shield4","sword5","shield5"}
BOSSES = {"skeletonCaptain","vampire","magicDragon","redKing","bigBoss","yellowKnight"}
STAIRS = {"upFloor","downFloor"}

WEB_RECORD = ROOT / "outputs" / "results" / "zone1_current_best_live_auto_item_true_replay.json"
OUT_JSON = ROOT / "outputs" / "results" / "autoon_mt4_to_mt10_main_targets_walk.json"


def load_main_targets():
    d = json.loads(WEB_RECORD.read_text(encoding="utf-8"))
    logs = d.get("logs") or d.get("steps") or []
    out = []
    for l in logs:
        s = l.get("step") or {}
        fid = s.get("fid"); act = s.get("action"); eid = s.get("eid")
        x, y = s.get("x"), s.get("y")
        if fid is None or x is None:
            continue
        if eid in STAIRS or eid in WEAPONS or eid in BOSSES:
            out.append((fid, x, y, act, eid))
        elif act == "open":
            out.append((fid, x, y, act, eid))
    return out


def build():
    from build_autooff_mt4_to_mt7_prefix_walk import build_game_to_mt7  # reuse Game init
    # We need a fresh Game from save1 with auto ON; build_game_to_mt7 already sets auto ON.
    g = build_game_to_mt7()
    g.set_segment("1区 auto-ON 主目标")
    targets = load_main_targets()
    for fid, x, y, act, eid in targets:
        if g.errors:
            break
        cur = g.state["floor"]
        if cur != fid:
            # need to fly / change floor to fid (flyback targets)
            try:
                g.fly(fid)
            except Exception as e:
                g.fail(f"fly to {fid} failed: {e}")
                break
        if eid in STAIRS:
            g.go_to(fid, x, y, f"上楼 {fid} x{x}y{y}")
            if not g.errors:
                nxt = f"MT{int(fid[2:])+1}"
                g.transition(nxt, f"{fid} -> {nxt}")
        else:
            g.go_to(fid, x, y, f"{act} {eid} {fid} x{x}y{y}")
    steps = [set_auto_step(g.steps[0]["before"])] + [normalize_step(s) for s in g.steps]
    return {
        "ok": not g.errors,
        "name": "autoon_mt4_to_mt10_main_targets",
        "auto_settings": [{"when": "4F start", "auto": dict(AUTO_ON), "reason": "auto ON intelligent: main targets + auto-bfs"}],
        "start": steps[0]["before"],
        "final": steps[-1]["after"],
        "steps": steps,
        "errors": list(g.errors),
        "main_targets": len(targets),
    }


def main():
    data = build()
    OUT_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"ok={data['ok']} steps={len(data['steps'])} main_targets={data['main_targets']} errors={data['errors'][:3]}")
    print(f"final={data['final'].get('floor')} HP={data['final'].get('hp')} ATK={data['final'].get('atk')}")
    print(f"json={OUT_JSON}")

if __name__ == "__main__":
    main()
