import heapq
from dataclasses import dataclass
from typing import List, Optional, Set, Dict, Tuple
from src.legacy.floor_map import FloorMap
from src.legacy.game_state import GameState, NodeType
from src.legacy.pareto import ParetoFrontier

@dataclass(frozen=True)
class SearchState:
    yk_cost: int
    hp_cost: int
    neg_yk: int
    neg_bk: int
    neg_atk: int
    neg_def: int
    node_idx: int
    visited: int

    # For heap ordering, we want to compare (yk_cost, hp_cost) first
    def __lt__(self, other):
        if self.yk_cost != other.yk_cost:
            return self.yk_cost < other.yk_cost
        if self.hp_cost != other.hp_cost:
            return self.hp_cost < other.hp_cost
        if self.neg_yk != other.neg_yk:
            return self.neg_yk > other.neg_yk  # Prefer more keys
        if self.neg_bk != other.neg_bk:
            return self.neg_bk > other.neg_bk
        if self.neg_atk != other.neg_atk:
            return self.neg_atk > other.neg_atk
        if self.neg_def != other.neg_def:
            return self.neg_def > other.neg_def
        return self.node_idx < other.node_idx

class FloorSearch:
    def __init__(self, floor_map: FloorMap):
        self.map = floor_map
        # Need enemy definitions - placeholder for now
        self.enemies = {}

    def search(self, start_state: GameState, target_types: Optional[Set[NodeType]] = None, max_iter: int = 500000) -> ParetoFrontier:
        """Search floor using Dijkstra, return Pareto frontier of solutions."""
        frontier = ParetoFrontier()

        # For each (node_idx, yk, bk, atk, def_, visited), track best (yk_cost, hp_cost)
        best: Dict[Tuple[int, int, int, int, int, int], Tuple[int, int]] = {}

        # Heap: (yk_cost, hp_cost, -yk, -bk, -atk, -def, node_idx, visited)
        # Start at -1 for "initial position, no node"
        heap = [SearchState(
            yk_cost=0, hp_cost=0,
            neg_yk=-start_state.yk, neg_bk=-start_state.bk,
            neg_atk=-start_state.atk, neg_def=-start_state.def_,
            node_idx=-1, visited=start_state.visited
        )]

        current_hp = {-1: start_state.hp}
        current_keys = {-1: (start_state.yk, start_state.bk)}
        current_stats = {-1: (start_state.atk, start_state.def_)}

        start_key = (-1, start_state.yk, start_state.bk, start_state.atk, start_state.def_, start_state.visited)
        best[start_key] = (0, 0)

        iter_count = 0

        while heap and iter_count < max_iter:
            state = heapq.heappop(heap)
            iter_count += 1

            current_yk = -state.neg_yk
            current_bk = -state.neg_bk
            current_atk = -state.neg_atk
            current_def = -state.neg_def

            key = (state.node_idx, current_yk, current_bk, current_atk, current_def, state.visited)

            # Check if this state is still the best
            if key not in best or best[key] != (state.yk_cost, state.hp_cost):
                continue

            # Check if we've reached a target
            if state.node_idx >= 0:
                node = self.map.nodes[state.node_idx]
                if target_types is None or node.type in target_types:
                    # Found a solution - add to frontier
                    final_hp = current_hp.get(state.node_idx, start_state.hp)
                    frontier.add((final_hp, current_yk, current_bk, current_atk, current_def))
                    continue

            # Get current position
            if state.node_idx == -1:
                curr_x, curr_y = start_state.x, start_state.y
            else:
                node = self.map.nodes[state.node_idx]
                curr_x, curr_y = node.x, node.y

            # Find reachable nodes
            reachable = self.map.get_reachable_nodes(curr_x, curr_y, state.visited)

            for next_node_idx in reachable:
                next_node = self.map.nodes[next_node_idx]

                # Try to apply this node
                new_state = self._apply_node(
                    start_state, state.visited,
                    state.node_idx, current_yk, current_bk, current_atk, current_def,
                    next_node_idx, current_hp.get(state.node_idx, start_state.hp)
                )

                if new_state is None:
                    continue

                new_yk, new_bk, new_yk_cost, new_hp_cost, new_hp, new_atk, new_def, new_visited = new_state

                new_key = (next_node_idx, new_yk, new_bk, new_atk, new_def, new_visited)
                total_yk_cost = state.yk_cost + new_yk_cost
                total_hp_cost = state.hp_cost + new_hp_cost

                # Check if this is better than existing
                if new_key not in best or (total_yk_cost, total_hp_cost) < best.get(new_key, (9999, 9999)):
                    best[new_key] = (total_yk_cost, total_hp_cost)
                    current_hp[next_node_idx] = new_hp
                    current_keys[next_node_idx] = (new_yk, new_bk)
                    current_stats[next_node_idx] = (new_atk, new_def)

                    heap_state = SearchState(
                        yk_cost=total_yk_cost, hp_cost=total_hp_cost,
                        neg_yk=-new_yk, neg_bk=-new_bk,
                        neg_atk=-new_atk, neg_def=-new_def,
                        node_idx=next_node_idx, visited=new_visited
                    )
                    heapq.heappush(heap, heap_state)

        return frontier

    def _apply_node(self, start_state: GameState, visited: int,
                  from_node_idx: int, yk: int, bk: int, atk: int, def_: int,
                  to_node_idx: int, current_hp: int) -> Optional[Tuple]:
        """Apply a node, return new state or None if impossible."""
        node = self.map.nodes[to_node_idx]
        new_yk, new_bk = yk, bk
        yk_cost = 0
        hp_cost = 0
        new_hp = current_hp
        new_atk, new_def = atk, def_

        if node.type == NodeType.ENEMY:
            # Need enemy data - placeholder
            hp_cost = 10  # TODO: real damage calc
            new_hp -= hp_cost
            if new_hp <= 0:
                return None

        elif node.type == NodeType.YELLOW_DOOR:
            if yk <= 0:
                return None
            new_yk -= 1
            yk_cost += 1

        elif node.type == NodeType.BLUE_DOOR:
            if bk <= 0:
                return None
            new_bk -= 1

        elif node.type == NodeType.YELLOW_KEY:
            new_yk += 1
            yk_cost -= 1  # Net gain reduces cost

        elif node.type == NodeType.BLUE_KEY:
            new_bk += 1

        elif node.type == NodeType.RED_POTION:
            new_hp = min(start_state.HP_MAX, new_hp + 50)

        elif node.type == NodeType.BLUE_POTION:
            new_hp = min(start_state.HP_MAX, new_hp + 200)

        elif node.type == NodeType.RED_GEM:
            new_atk += 1

        elif node.type == NodeType.BLUE_GEM:
            new_def += 1

        elif node.type == NodeType.SWORD:
            new_atk += 10

        elif node.type == NodeType.SHIELD:
            new_def += 10

        new_visited = visited | (1 << to_node_idx)

        return (new_yk, new_bk, yk_cost, hp_cost, new_hp, new_atk, new_def, new_visited)
