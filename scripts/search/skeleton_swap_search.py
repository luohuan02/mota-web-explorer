#!/usr/bin/env python3
"""Skeleton swap search on the web-verified 39944 baseline (纯净版-TE hp).

Method (CLAUDE.md 唯一管线 / 根因优先): the 39944 recording's semantic action
list is the baseline route. Reorder/insert skeleton "visit units" (fly + the
same-floor run that follows) and evaluate each candidate by a full offline
``convert()`` replay through the generic Game class -- legality (survival,
keys, funding, fly-visited) is checked by the replay itself, 0.5 s each.

Guards against silently-degraded variants:
  * ok=True and final floor MT50 and won50 (the route still wins);
  * the multiset of statlog-derived shop purchases is unchanged (a reordered
    purchase whose ``times1`` no longer matches the recording's gold delta is
    silently skipped as an approach waypoint -- diagnostics expose that).

Phase A: baseline assertion + visit-unit segmentation report (--report-only).
Phase B: candidate generation (adjacent swap / defer K / advance K; later:
         reachability-matrix inserts and shop splits).
Phase C: hill-climb on strict final-HP improvement.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

from search.recording_seed_to_game import (  # noqa: E402
    SemanticAction,
    _cancel_stair_bounce_arrows,
    _stage_slice,
    convert,
    load_capture,
)
from solver.game_route import Game  # noqa: E402

SEED_PATH = ROOT / "best/checkpoints/save1_mt4_snapshot.json"
CAPTURE_PATH = ROOT / "outputs/results/2atk_alldef_39944_capture.json"
STAGE = "mt4-mt31"
START_STAT = 55
AUTO_SPEC = "battle=false,item=false,wall=false"
BASELINE_HP = 39944
FINAL_FLOOR = "MT50"

# Tool-using units are excluded from moves: pickaxe/bomb/cross targets are
# inferred from the following action's direction, which a reorder breaks.
TOOL_KINDS = {"tool"}
TOOL_EIDS = {"pickaxe", "bomb", "cross", "centerFly", "upFly", "downFly"}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


# ---------------------------------------------------------------- replay core

_SEED: dict[str, Any] | None = None
_CAPTURE: dict[str, Any] | None = None
_ACTIONS: list[SemanticAction] | None = None


def load_context() -> tuple[dict[str, Any], dict[str, Any], list[SemanticAction]]:
    global _SEED, _CAPTURE, _ACTIONS
    if _ACTIONS is None:
        _SEED = read_json(SEED_PATH)
        _CAPTURE, _ACTIONS = load_capture(CAPTURE_PATH)
    assert _SEED is not None and _CAPTURE is not None
    return _SEED, _CAPTURE, _ACTIONS


def baseline_actions() -> list[SemanticAction]:
    """The stage-sliced, bounce-cancelled baseline action list (1462 actions)."""
    seed, capture, actions = load_context()
    g0 = Game(seed)
    sliced = _stage_slice(actions, capture, STAGE, START_STAT)
    return _cancel_stair_bounce_arrows(sliced, capture.get("statlog") or [],
                                       set(g0.visited))


def replay(actions: list[SemanticAction]) -> dict[str, Any]:
    seed, capture, _ = load_context()
    return convert(seed, capture, list(actions), STAGE, SEED_PATH, CAPTURE_PATH,
                   START_STAT, auto_spec=AUTO_SPEC)


def purchases_of(result: dict[str, Any]) -> list[tuple[Any, ...]]:
    """Executed statlog-derived shop purchases, as a sortable multiset."""
    out = []
    for d in result.get("diagnostics") or []:
        if d.get("classification") == "shop_purchase_from_delta":
            pos = d.get("pos") or [None, None]
            out.append((pos[0], pos[1], d.get("shop_kind"), d.get("count")))
    return sorted(out)


def evaluate(actions: list[SemanticAction], baseline_purchases,
             label: str) -> dict[str, Any]:
    """Replay + guards. Returns a compact verdict record."""
    t0 = time.time()
    try:
        result = replay(actions)
    except Exception as exc:  # converter crash = illegal candidate
        return {"label": label, "legal": False, "reason": f"crash: {exc}",
                "hp": None, "elapsed": round(time.time() - t0, 3)}
    final = result.get("final") or {}
    hp = final.get("hp")
    reasons = []
    if not result.get("ok"):
        reasons.append("ok=False: " + "; ".join(result.get("errors") or [])[:200])
    if final.get("floor") != FINAL_FLOOR:
        reasons.append(f"final floor {final.get('floor')} != {FINAL_FLOOR}")
    if not final.get("won50"):
        reasons.append("won50 missing")
    if purchases_of(result) != baseline_purchases:
        reasons.append("shop purchases changed (silent no-buy guard)")
    return {
        "label": label,
        "legal": not reasons,
        "reason": "; ".join(reasons),
        "hp": hp,
        "final": {k: final.get(k) for k in
                  ("floor", "hp", "atk", "def", "yk", "bk", "rk", "gold")},
        "errors": (result.get("errors") or [])[:5],
        "elapsed": round(time.time() - t0, 3),
    }


# ------------------------------------------------------------ segmentation

@dataclass
class Unit:
    idx: int
    actions: list[SemanticAction]
    floors: list[str] = field(default_factory=list)   # in visit order
    primary_floor: str | None = None                  # fly destination
    eids: list[str] = field(default_factory=list)     # target/arrow block eids
    purchase_indexes: list[int] = field(default_factory=list)
    has_tool: bool = False
    has_set_auto: bool = False
    revisit: bool = False
    movable: bool = True

    @property
    def start_index(self) -> int:
        return self.actions[0].index

    @property
    def n(self) -> int:
        return len(self.actions)

    def describe(self) -> str:
        bits = [f"u{self.idx}", "→".join(self.floors[:4]) +
                ("…" if len(self.floors) > 4 else ""), f"n={self.n}"]
        if self.revisit:
            bits.append("revisit")
        if self.purchase_indexes:
            bits.append(f"shop@{self.purchase_indexes}")
        if self.has_tool:
            bits.append("TOOL")
        if self.has_set_auto:
            bits.append("auto")
        if self.eids:
            bits.append(",".join(dict.fromkeys(self.eids))[:60])
        return " ".join(bits)


def segment(actions: list[SemanticAction],
            baseline_result: dict[str, Any]) -> list[Unit]:
    """Split at fly boundaries: unit = fly(F) + run until the next fly."""
    units: list[Unit] = []
    cur: list[SemanticAction] = []
    for a in actions:
        if a.kind == "fly" and cur:
            units.append(Unit(len(units), cur))
            cur = [a]
        else:
            cur.append(a)
    if cur:
        units.append(Unit(len(units), cur))

    # purchases from the baseline diagnostics, keyed by recording action index
    purchase_at: dict[int, dict[str, Any]] = {}
    for d in baseline_result.get("diagnostics") or []:
        if d.get("classification") == "shop_purchase_from_delta":
            purchase_at[d.get("recording_index")] = d

    seen: set[str] = set()
    for u in units:
        for a in u.actions:
            if a.kind in ("fly", "transition") and a.floor:
                if not u.floors or u.floors[-1] != a.floor:
                    u.floors.append(a.floor)
            if a.kind in ("target", "arrow"):
                if a.eid and a.eid not in ("", "empty"):
                    u.eids.append(a.eid)
            if a.kind in TOOL_KINDS or a.eid in TOOL_EIDS:
                u.has_tool = True
            if a.kind == "set_auto":
                u.has_set_auto = True
            if a.index in purchase_at:
                u.purchase_indexes.append(a.index)
        u.primary_floor = u.floors[0] if u.floors else None
        # revisit/detour: the unit's first floor was already visited by an
        # earlier unit -> the route came back for it, prime swap material.
        u.revisit = bool(u.primary_floor and u.primary_floor in seen)
        seen.update(u.floors)
        # head unit is the fixed anchor (initial climb from the MT4 seed);
        # tool units are excluded (inference depends on neighbour actions).
        u.movable = u.idx != 0 and not u.has_tool
    return units


def flatten(units: list[Unit]) -> list[SemanticAction]:
    out: list[SemanticAction] = []
    for u in units:
        out.extend(u.actions)
    return out


# ------------------------------------------------------- candidate generation

def gen_moves(units: list[Unit], ks=(1, 2, 3, 5)) -> list[tuple[str, str, list[int]]]:
    """(family, label, unit-order permutation) candidates.

    swap:    adjacent units i, i+1 exchange places
    defer:   unit i moves K positions later  (do X after Y)
    advance: unit i moves K positions earlier (do X before Y)
    """
    n = len(units)
    # revisit/detour units first: coming back for a floor is prime swap
    # material, so they lead the candidate list if the budget cuts off.
    movable = sorted((u.idx for u in units if u.movable),
                     key=lambda i: (not units[i].revisit, i))
    out: list[tuple[str, str, list[int]]] = []

    def order(perm: list[int]) -> list[int]:
        return perm

    for i in movable:
        if i + 1 < n and units[i + 1].movable:
            perm = list(range(n))
            perm[i], perm[i + 1] = perm[i + 1], perm[i]
            out.append(("swap", f"swap u{i}<->u{i+1}", order(perm)))
        for k in ks:
            if k == 1:
                continue
            j = i + k  # defer: unit i executes AFTER unit j=i+k
            if j < n:
                perm = [x for x in range(n) if x != i]
                perm.insert(perm.index(j) + 1, i)
                out.append(("defer", f"defer u{i} past u{i + 1}..u{j}", perm))
            j = i - k  # advance: before unit i-k
            if j >= 1:
                perm = [x for x in range(n) if x != i]
                perm.insert(perm.index(j), i)
                out.append(("advance", f"advance u{i} before u{j}", perm))
    return out


# ------------------------------------------------------------------ main

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-only", action="store_true",
                        help="Phase A only: assert baseline + write unit report")
    parser.add_argument("--units-json", type=Path,
                        default=ROOT / "outputs/reports/skeleton_swap_units.json")
    parser.add_argument("--round-out", type=Path,
                        default=ROOT / "outputs/results/skeleton_swap_search_round1.json")
    parser.add_argument("--max-candidates", type=int, default=1600)
    parser.add_argument("--time-budget", type=float, default=1800.0,
                        help="seconds; hill-climb stops after this budget")
    args = parser.parse_args()

    t_start = time.time()

    # Phase A: baseline assertion
    base_actions = baseline_actions()
    print(f"[A] baseline actions: {len(base_actions)}")
    base_result = replay(base_actions)
    base_final = base_result.get("final") or {}
    base_purchases = purchases_of(base_result)
    assert base_result.get("ok"), f"baseline replay failed: {base_result.get('errors')}"
    assert base_final.get("hp") == BASELINE_HP, f"baseline hp {base_final.get('hp')}"
    assert base_final.get("won50"), "baseline did not win MT50"
    print(f"[A] baseline ok hp={base_final.get('hp')} "
          f"atk={base_final.get('atk')} def={base_final.get('def')} "
          f"gold={base_final.get('gold')} purchases={len(base_purchases)}")

    units = segment(base_actions, base_result)
    movable_n = sum(1 for u in units if u.movable)
    revisit_n = sum(1 for u in units if u.revisit)
    print(f"[A] units={len(units)} movable={movable_n} revisit={revisit_n} "
          f"tool-locked={len(units) - movable_n - 1}")

    args.units_json.parent.mkdir(parents=True, exist_ok=True)
    args.units_json.write_text(json.dumps({
        "baseline": {"hp": base_final.get("hp"), "actions": len(base_actions),
                     "purchases": [list(p) for p in base_purchases]},
        "units": [{
            "idx": u.idx, "start_index": u.start_index, "n_actions": u.n,
            "floors": u.floors, "primary_floor": u.primary_floor,
            "eids": list(dict.fromkeys(u.eids)),
            "purchase_indexes": u.purchase_indexes,
            "has_tool": u.has_tool, "has_set_auto": u.has_set_auto,
            "revisit": u.revisit, "movable": u.movable,
            "describe": u.describe(),
        } for u in units],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[A] unit report -> {args.units_json}")

    if args.report_only:
        for u in units:
            print("   ", u.describe())
        return 0

    # Phase B+C: candidate moves + hill-climb
    incumbent_order = list(range(len(units)))
    incumbent_hp = base_final["hp"]
    history: list[dict[str, Any]] = []
    round_no = 0

    while time.time() - t_start < args.time_budget:
        round_no += 1
        cur_units = [units[i] for i in incumbent_order]
        moves = gen_moves(cur_units)
        moves = moves[: args.max_candidates]
        print(f"[B] round {round_no}: {len(moves)} candidates "
              f"(incumbent hp={incumbent_hp})")
        best = None
        t_round = time.time()
        for ci, (family, label, perm) in enumerate(moves):
            if time.time() - t_start > args.time_budget:
                print(f"[B] round {round_no}: time budget hit at candidate {ci}",
                      flush=True)
                moves = moves[:ci]
                break
            # perm indexes into cur_units (the CURRENT order); log the label
            # before evaluating so a pathological candidate is identifiable
            print(f"    cand {ci}/{len(moves)} {label}", flush=True)
            new_units = [cur_units[i] for i in perm]
            verdict = evaluate(flatten(new_units), base_purchases, label)
            verdict["family"] = family
            history.append(verdict)
            if verdict["legal"] and verdict["hp"] is not None \
                    and verdict["hp"] > incumbent_hp:
                if best is None or verdict["hp"] > best["hp"]:
                    best = verdict
                    best["perm"] = perm
        elapsed = time.time() - t_round
        legal_n = sum(1 for v in history if v["legal"])
        print(f"[C] round {round_no}: {len(moves)} evaluated in {elapsed:.0f}s, "
              f"legal so far={legal_n}, best="
              f"{(best['hp'], best['label']) if best else 'none'}")
        if best is None:
            print("[C] no improving move -> hill-climb converged")
            break
        incumbent_order = [incumbent_order[i] for i in best["perm"]]
        incumbent_hp = best["hp"]
        print(f"[C] accept {best['label']} -> hp={incumbent_hp}")
        if round_no >= 12:
            print("[C] round cap reached")
            break

    args.round_out.parent.mkdir(parents=True, exist_ok=True)
    args.round_out.write_text(json.dumps({
        "baseline_hp": BASELINE_HP,
        "incumbent_hp": incumbent_hp,
        "incumbent_order": incumbent_order,
        "rounds": round_no,
        "elapsed": round(time.time() - t_start, 1),
        "history": history,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[out] {args.round_out} (incumbent hp={incumbent_hp}, "
          f"{len(history)} candidates logged)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
