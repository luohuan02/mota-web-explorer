#!/usr/bin/env python3
"""Incumbent-guided A* audit over completed Zone-4 macro candidates.

This search intentionally operates on *completed strict Game replays*.  A node
contains the early resource-group set, post-shield ATK target, final shop kind,
actual shop sequence and final HP.  Edges change one macro variable.  Completed
nodes have an exact terminal cost ``MAX_HP - final_hp``; therefore any node not
beating the incumbent is an exact leaf prune.  Missing neighbors are reported
as frontier work and are never silently treated as dominated.

It is a bounded/cached A* layer, not a proof over every possible route.  New
nodes are produced by ``probe_zone4_shop_resource_variants.py`` and become
eligible here only after their full TE replay succeeds.
"""
from __future__ import annotations

import argparse
import heapq
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = ROOT / "outputs/results/zone4_incumbent_macro_astar.json"
DEFAULT_INCUMBENT = ROOT / "outputs/results/zone4_all_farmfix_target241_hp_candidate.json"
MAX_HP_COST = 100_000
TARGETS = (211, 221, 231, 241, 251, 261, 271, 281, 291)
FINAL_KINDS = ("hp", "def", "atk", "skip")
GROUPS = ("mt31_red", "mt31_blue", "mt32_pair")


@dataclass(frozen=True)
class Config:
    groups: tuple[str, ...]
    target: int
    final_kind: str


def config_from(payload: dict[str, Any]) -> Config | None:
    variant = payload.get("variant") or {}
    if "postShieldAtkTarget" not in variant:
        return None
    return Config(
        tuple(sorted(str(value) for value in variant.get("earlyGroups", []))),
        int(variant["postShieldAtkTarget"]),
        str(variant.get("lateFinalShopKind", "def")),
    )


def shop_sequence(payload: dict[str, Any]) -> tuple[str, ...]:
    return tuple(
        str(step.get("eid")) for step in payload.get("steps", [])
        if step.get("action") == "商店"
    )


def validate_candidate(payload: dict[str, Any]) -> list[str]:
    """Reject successful-looking replays that violate mandatory TE timing."""
    errors: list[str] = []
    if not payload.get("ok"):
        errors.extend(str(value) for value in payload.get("errors", []))
        if not errors:
            errors.append("payload ok=false")
        return errors
    final = payload.get("final", {})
    if not final.get("won49") or not final.get("won50"):
        errors.append("route did not complete both 49F and 50F flags")
    dragons = [
        step for step in payload.get("steps", [])
        if step.get("action") == "击杀" and step.get("eid") == "magicDragon"
    ]
    if len(dragons) != 1:
        errors.append(f"expected exactly one magicDragon kill, got {len(dragons)}")
    elif "35F magic dragon before knife" not in str(dragons[0].get("note", "")):
        errors.append(f"magicDragon timing is not mandatory pre-knife: {dragons[0].get('note')!r}")
    if any(
        step.get("eid") == "magicDragon" and "key investment" in str(step.get("note", "")).lower()
        for step in payload.get("steps", [])
    ):
        errors.append("magicDragon was illegally consumed by generic key-investment farming")
    return errors


def route_signature(payload: dict[str, Any]) -> dict[str, Any]:
    final = payload["final"]
    return {
        "shops": shop_sequence(payload),
        "steps": len(payload.get("steps", [])),
        "final": {key: final.get(key) for key in (
            "hp", "atk", "def", "yk", "bk", "rk", "gold", "dmg",
            "yd", "bd", "rd", "times1", "won49", "won50",
        )},
    }


def neighbors(config: Config) -> set[Config]:
    out: set[Config] = set()
    group_set = set(config.groups)
    for group in GROUPS:
        changed = group_set ^ {group}
        out.add(Config(tuple(sorted(changed)), config.target, config.final_kind))
    index = TARGETS.index(config.target) if config.target in TARGETS else -1
    if index >= 0:
        if index:
            out.add(Config(config.groups, TARGETS[index - 1], config.final_kind))
        if index + 1 < len(TARGETS):
            out.add(Config(config.groups, TARGETS[index + 1], config.final_kind))
    for kind in FINAL_KINDS:
        if kind != config.final_kind:
            out.add(Config(config.groups, config.target, kind))
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--incumbent", type=int, default=None)
    parser.add_argument("--incumbent-json", type=Path, default=DEFAULT_INCUMBENT)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    patterns = (
        "zone4_31red_atktarget*_candidate.json",
        "zone4_atk261_*_candidate.json",
        "zone4_*farmfix*_candidate.json",
        "zone4_incumbent_neighbor_*.json",
        "zone4_31red_prep_*_final_hp_candidate.json",
    )
    nodes: dict[Config, dict[str, Any]] = {}
    invalid_candidates: list[dict[str, Any]] = []
    invalid_by_config: dict[Config, list[dict[str, Any]]] = {}
    seen_paths: set[Path] = set()
    for pattern in patterns:
        for path in (ROOT / "outputs/results").glob(pattern):
            if path in seen_paths:
                continue
            seen_paths.add(path)
            payload = json.loads(path.read_text(encoding="utf-8"))
            config = config_from(payload)
            if config is None:
                continue
            validation_errors = validate_candidate(payload)
            if validation_errors:
                invalid_row = {
                    "path": str(path.relative_to(ROOT)),
                    "config": config.__dict__,
                    "errors": validation_errors,
                }
                invalid_candidates.append(invalid_row)
                invalid_by_config.setdefault(config, []).append(invalid_row)
                continue
            row = {
                "path": str(path.relative_to(ROOT)),
                "final_hp": int(payload["final"]["hp"]),
                "final": payload["final"],
                "shop_sequence": shop_sequence(payload),
                "route_signature": route_signature(payload),
            }
            old = nodes.get(config)
            if old is None or row["final_hp"] > old["final_hp"]:
                nodes[config] = row

    if not nodes:
        raise RuntimeError("no completed macro candidates found")
    incumbent_payload = json.loads(args.incumbent_json.read_text(encoding="utf-8"))
    incumbent_errors = validate_candidate(incumbent_payload)
    if incumbent_errors:
        raise RuntimeError(f"invalid incumbent {args.incumbent_json}: {incumbent_errors}")
    best_config = config_from(incumbent_payload)
    if best_config is None:
        raise RuntimeError(f"incumbent lacks macro config: {args.incumbent_json}")
    best_row = nodes.get(best_config)
    if best_row is None:
        raise RuntimeError(f"incumbent config is absent from candidate catalog: {best_config}")
    incumbent = int(incumbent_payload["final"]["hp"])
    if args.incumbent is not None:
        incumbent = max(incumbent, args.incumbent)
    catalog_best_config, catalog_best_row = max(
        nodes.items(), key=lambda item: item[1]["final_hp"]
    )

    # A* with h=0 over exact completed costs.  This orders the finite audited
    # catalog by best final HP first.  We only expand the incumbent node; exact
    # non-winning completed neighbors are leaf-pruned, while missing neighbors
    # remain explicit frontier tasks.
    queue: list[tuple[int, str, Config]] = []
    for config, row in nodes.items():
        heapq.heappush(
            queue,
            (MAX_HP_COST - int(row["final_hp"]), repr(config), config),
        )
    popped: list[dict[str, Any]] = []
    better: list[dict[str, Any]] = []
    while queue:
        cost, _tie_breaker, config = heapq.heappop(queue)
        row = nodes[config]
        record = {
            "config": config.__dict__,
            "cost": cost,
            "final_hp": row["final_hp"],
            "shop_sequence": row["shop_sequence"],
            "path": row["path"],
        }
        popped.append(record)
        if row["final_hp"] > incumbent:
            better.append(record)

    incumbent_neighbors = neighbors(best_config)
    exact_neighbors = []
    invalid_neighbors = []
    missing_neighbors = []
    for config in sorted(incumbent_neighbors, key=repr):
        row = nodes.get(config)
        if row is None:
            invalid_rows = invalid_by_config.get(config, [])
            if invalid_rows:
                invalid_neighbors.append({
                    "config": config.__dict__,
                    "candidates": invalid_rows,
                })
            else:
                missing_neighbors.append(config.__dict__)
        else:
            exact_neighbors.append({
                "config": config.__dict__,
                "final_hp": row["final_hp"],
                "delta_vs_incumbent": row["final_hp"] - incumbent,
                "exact_pruned": row["final_hp"] <= incumbent,
                "same_route_as_incumbent": row["route_signature"] == best_row["route_signature"],
                "shop_sequence": row["shop_sequence"],
                "path": row["path"],
            })

    result = {
        "ok": True,
        "bounded": True,
        "method": "A* h=0 over completed strict-Game macro nodes with exact incumbent leaf pruning",
        "incumbent_hp": incumbent,
        "incumbent_path": str(args.incumbent_json.relative_to(ROOT)),
        "best_config": best_config.__dict__,
        "best": best_row,
        "catalog_best_config": catalog_best_config.__dict__,
        "catalog_best": catalog_best_row,
        "evaluated_nodes": len(nodes),
        "invalid_candidates": invalid_candidates,
        "popped": popped,
        "better_than_incumbent": better,
        "incumbent_exact_neighbors": exact_neighbors,
        "incumbent_invalid_neighbors": invalid_neighbors,
        "missing_incumbent_neighbors": missing_neighbors,
        "claim": "completed catalog / one-edit neighborhood only; not global optimum proof",
    }
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"incumbent={incumbent} evaluated={len(nodes)} "
        f"exact_neighbors={len(exact_neighbors)} invalid_neighbors={len(invalid_neighbors)} "
        f"missing_neighbors={len(missing_neighbors)} "
        f"better={len(better)}"
    )
    print(f"incumbent_config={best_config} hp={best_row['final_hp']} shops={best_row['shop_sequence']}")
    print(f"catalog_best={catalog_best_config} hp={catalog_best_row['final_hp']}")
    print(f"out={args.out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
