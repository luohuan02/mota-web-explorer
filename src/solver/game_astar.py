#!/usr/bin/env python3
"""Generic A*/Dijkstra search over the canonical :class:`Game` model.

The old floor search in ``full_search.py`` has its own combat, door, item and
map mutations.  This module deliberately owns none of those rules: an edge is
accepted only after its action succeeds on a cloned ``Game``.  Consequently a
found route is already a normal Game walk and can go through the existing JSON
-> Markdown -> live-verifier pipeline.
"""

from __future__ import annotations

import heapq
import math
from dataclasses import dataclass, field
from itertools import count
from typing import Any, Callable, Hashable, Iterable, Mapping

from src.solver.game_route import Game, RouteError


GamePredicate = Callable[[Game], bool]
GameMetric = Callable[[Game], float]
GameKey = Callable[[Game], Hashable]


def _freeze(value: Any) -> Hashable:
    """Convert nested JSON-like Game state into a deterministic hash key."""
    if isinstance(value, Mapping):
        return tuple(sorted((str(key), _freeze(item)) for key, item in value.items()))
    if isinstance(value, (set, frozenset)):
        return tuple(sorted((_freeze(item) for item in value), key=repr))
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, float) and math.isinf(value):
        return ("inf", 1 if value > 0 else -1)
    try:
        hash(value)
    except TypeError:
        return repr(value)
    return value


def exact_game_key(game: Game) -> Hashable:
    """Exact transposition key for every route-relevant mutable Game field.

    Floor grids are represented by their mutable block dictionaries.  All
    modeled wall/door/item/enemy changes go through ``set_ground``/``set_block``
    and therefore alter this signature.  Static floor data and append-only walk
    records are intentionally excluded.
    """
    blocks = tuple(
        (fid, x, y, block.kind, block.eid, block.tile)
        for fid, floor in sorted(game.floors.items())
        for (x, y), block in sorted(floor.blocks.items())
    )
    return (
        _freeze(game.state),
        tuple(sorted(game.visited)),
        _freeze(game.flags),
        blocks,
        tuple(sorted(game.blocked_items)),
        tuple(sorted(game.retreat_wizards)),
        tuple(sorted(game.no_auto_farm)),
        _freeze(game.auto_flags),
        bool(game.strict_live_model),
    )


@dataclass(frozen=True)
class GameAction:
    """One search edge whose implementation uses public Game route methods."""

    name: str
    apply: Callable[[Game], None] = field(compare=False, repr=False)
    metadata: Mapping[str, Any] = field(default_factory=dict, compare=False)


def click_action(fid: str, x: int, y: int, note: str = "") -> GameAction:
    """Build a reproducible map-click action backed by ``Game.go_to``."""
    return GameAction(
        name=f"click {fid} x{x}y{y}",
        apply=lambda game: game.go_to(fid, x, y, note),
        metadata={"kind": "click", "floor": fid, "x": x, "y": y, "note": note},
    )


@dataclass
class GameAStarResult:
    found: bool
    game: Game | None
    actions: list[GameAction]
    cost: float
    expansions: int
    generated: int
    reason: str
    # top-K goal states found, sorted by cost asc: [(cost, game, route), ...].
    # Empty when top_k=1 (use .game/.actions/.cost for the single best).
    top_goals: list[tuple[float, Game, list[GameAction]]] = field(default_factory=list)

    @property
    def steps(self) -> list[dict[str, Any]]:
        return [] if self.game is None else self.game.steps


class GameAStar:
    """Reusable weighted A* engine for canonical ``Game`` states.

    ``weight=1`` is ordinary A*. ``weight=0`` is Dijkstra.  The caller supplies
    domain actions and objective/heuristic only; transition legality and all
    side effects remain owned by ``Game``.
    """

    def __init__(
        self,
        *,
        actions: Callable[[Game], Iterable[GameAction]],
        goal: GamePredicate,
        heuristic: GameMetric | None = None,
        edge_cost: Callable[[Game, Game, GameAction], float] | None = None,
        state_key: GameKey = exact_game_key,
        tie_breaker: GameMetric | None = None,
        weight: float = 1.0,
        max_expansions: int = 100_000,
        upper_bound: float = math.inf,
        top_k: int = 1,
        pareto_metrics: tuple[GameMetric, ...] | None = None,
    ) -> None:
        if weight < 0:
            raise ValueError("weight must be non-negative")
        if max_expansions <= 0:
            raise ValueError("max_expansions must be positive")
        if upper_bound <= 0:
            raise ValueError("upper_bound must be positive")
        if top_k < 1:
            raise ValueError("top_k must be >= 1")
        self.actions = actions
        self.goal = goal
        self.heuristic = heuristic or (lambda _game: 0.0)
        self.edge_cost = edge_cost or self.hp_loss_cost
        self.state_key = state_key
        self.tie_breaker = tie_breaker or (lambda _game: 0.0)
        self.weight = float(weight)
        self.max_expansions = int(max_expansions)
        self.upper_bound = float(upper_bound)
        self.top_k = int(top_k)
        # Multi-objective Pareto frontier per state_key.  When provided, a key
        # keeps ALL non-dominated cost vectors instead of only the lowest-cost
        # one.  This prevents damage-min branches from pruning gem-grabbing
        # branches (dmg+ but atk/def+).  The first metric must be the cumulative
        # main cost (used for priority + upper_bound); later metrics are state
        # attributes where lower is better (e.g. -atk, -def, -yk).  None falls
        # back to single-cost Dijkstra/A* (Pareto degenerates to best-cost).
        self.pareto_metrics = tuple(pareto_metrics) if pareto_metrics else None

    @staticmethod
    def hp_loss_cost(before: Game, after: Game, _action: GameAction) -> float:
        """Default non-negative route cost: modeled damage/HP loss."""
        damage_delta = int(after.state.get("dmg", 0)) - int(before.state.get("dmg", 0))
        return float(max(0, damage_delta))

    def cost_vector(self, game: Game) -> tuple[int, ...]:
        """Multi-objective cost vector.  Lower is better on every component.

        With ``pareto_metrics`` the vector is ``[m(game) for m in metrics]`` --
        the caller is responsible for negating attributes where higher is better
        (e.g. ``-atk``).  Without it the vector is the single cumulative ``dmg``,
        which makes Pareto degenerate to ordinary best-cost pruning.
        """
        if self.pareto_metrics:
            return tuple(int(m(game)) for m in self.pareto_metrics)
        return (int(game.state.get("dmg", 0)),)

    @staticmethod
    def dominates(a: tuple[int, ...], b: tuple[int, ...]) -> bool:
        """True when cost vector ``a`` dominates ``b`` (a is no worse on every
        component and strictly better on at least one).  Both must be equal
        length; lower is better on every component."""
        le = True
        lt = False
        for x, y in zip(a, b):
            if x > y:
                le = False
                break
            if x < y:
                lt = True
        return le and lt

    def search(self, start: Game) -> GameAStarResult:
        initial = start.clone()
        start_key = self.state_key(initial)
        start_vec = self.cost_vector(initial)
        # Pareto frontier per state_key: list of non-dominated cost vectors.
        # Single-objective (pareto_metrics is None) keeps exactly one vector per
        # key -- the lowest main cost -- so this reduces to ordinary best-cost
        # Dijkstra/A*.  Multi-objective keeps every non-dominated vector so that
        # a gem-grabbing branch (dmg+ but atk+) is not pruned by a damage-min
        # branch (dmg- but atk-).
        frontier_vecs: dict[Hashable, list[tuple[int, ...]]] = {start_key: [start_vec]}
        # Route reconstruction indexed by (key, vec): a key can have several
        # non-dominated vectors, each reached via a different parent path.
        parents: dict[tuple[Hashable, tuple[int, ...]],
                      tuple[Hashable, tuple[int, ...], GameAction] | None] = {
            (start_key, start_vec): None,
        }
        serial = count()
        # queue entry: (priority, cost, tie_breaker, seq, key, game, vec)
        # cost is the cumulative main-cost increment from start (used for
        # upper_bound + priority + top-K ordering); vec is the absolute
        # multi-objective vector (used for Pareto dominance).
        queue: list[tuple[float, float, float, int, Hashable, Game, tuple[int, ...]]] = [
            (
                self.weight * float(self.heuristic(initial)),
                0.0,
                float(self.tie_breaker(initial)),
                next(serial),
                start_key,
                initial,
                start_vec,
            )
        ]
        expansions = 0
        generated = 0
        top_goals: list[tuple[float, Game, list[GameAction]]] = []
        collected_goal_keys: set[tuple[Hashable, tuple[int, ...]]] = set()

        while queue and expansions < self.max_expansions:
            _priority, cost, _tie, _seq, key, game, vec = heapq.heappop(queue)
            # Stale entry: this vector was superseded on the key's frontier.
            if vec not in frontier_vecs.get(key, []):
                continue
            if self.goal(game):
                route: list[GameAction] = []
                ck, cv = key, vec
                seen_route: set[tuple[Hashable, tuple[int, ...]]] = set()
                while parents[(ck, cv)] is not None:
                    # Cycle guard (defensive): the same-vec dedup + first-wins
                    # parent rule should make the chain acyclic, but a stray
                    # cycle must not OOM route reconstruction.
                    if (ck, cv) in seen_route:
                        break
                    seen_route.add((ck, cv))
                    pk, pv, action = parents[(ck, cv)]  # type: ignore[misc]
                    route.append(action)
                    ck, cv = pk, pv
                route.reverse()
                if self.top_k <= 1:
                    return GameAStarResult(True, game, route, cost, expansions, generated, "goal", top_goals)
                # top-K: record this distinct goal (key, vec) and keep collecting.
                # Skip expanding the goal (its children are beyond-goal); other
                # goal states are reached via different pre-goal paths.
                if (key, vec) not in collected_goal_keys:
                    top_goals.append((cost, game, route))
                    collected_goal_keys.add((key, vec))
                if len(top_goals) >= self.top_k:
                    top_goals.sort(key=lambda t: t[0])
                    best = top_goals[0]
                    return GameAStarResult(True, best[1], best[2], best[0], expansions, generated, "goal", top_goals)
                continue

            expansions += 1
            seen_names: set[str] = set()
            for action in self.actions(game):
                if action.name in seen_names:
                    continue
                seen_names.add(action.name)
                child = game.clone()
                before_steps = len(child.steps)
                try:
                    action.apply(child)
                except RouteError:
                    continue
                generated += 1
                child_key = self.state_key(child)
                # Reject no-op clicks/macros. They cannot improve a non-negative
                # route and otherwise create self-loop churn.
                if child_key == key and len(child.steps) == before_steps:
                    continue
                step_cost = float(self.edge_cost(game, child, action))
                if not math.isfinite(step_cost) or step_cost < 0:
                    raise ValueError(f"edge_cost must be finite and non-negative: {action.name} -> {step_cost}")
                new_cost = cost + step_cost
                if new_cost >= self.upper_bound:
                    continue
                child_vec = self.cost_vector(child)
                cfront = frontier_vecs.get(child_key, [])
                # Pareto prune: skip if an existing vector on this key dominates
                # the new one (no better on any objective).
                if any(self.dominates(f, child_vec) for f in cfront):
                    continue
                # Same absolute vector already on the frontier: same cumulative
                # dmg + same atk/def (vec is absolute), so the first discovery is
                # already optimal.  Skipping avoids re-adding and the A->B->A
                # parent-cycle that Pareto multi-vector per key can otherwise form.
                if child_vec in cfront:
                    continue
                # Drop existing vectors that the new one dominates.
                new_front = [f for f in cfront if not self.dominates(child_vec, f)]
                new_front.append(child_vec)
                frontier_vecs[child_key] = new_front
                # First discovery wins (same vec => same cost); never overwrite,
                # otherwise later re-discoveries via a different parent can form a
                # cycle in the (key, vec) -> parent chain.
                if (child_key, child_vec) not in parents:
                    parents[(child_key, child_vec)] = (key, vec, action)
                priority = new_cost + self.weight * float(self.heuristic(child))
                heapq.heappush(
                    queue,
                    (
                        priority,
                        new_cost,
                        float(self.tie_breaker(child)),
                        next(serial),
                        child_key,
                        child,
                        child_vec,
                    ),
                )

        reason = "max_expansions" if queue else "exhausted"
        if top_goals:
            # top-K run exhausted before collecting K; return what we have.
            top_goals.sort(key=lambda t: t[0])
            best = top_goals[0]
            return GameAStarResult(True, best[1], best[2], best[0], expansions, generated, reason, top_goals)
        return GameAStarResult(False, None, [], math.inf, expansions, generated, reason)


__all__ = [
    "GameAction",
    "GameAStar",
    "GameAStarResult",
    "click_action",
    "exact_game_key",
]
