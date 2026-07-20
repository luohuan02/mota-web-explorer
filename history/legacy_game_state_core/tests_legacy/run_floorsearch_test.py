#!/usr/bin/env python3
"""Simple test script for Floor Search"""

import sys
sys.path.insert(0, '')

from src.legacy.floor_search import FloorSearch
from src.legacy.floor_map import FloorMap
from src.legacy.game_state import GameState
from src.legacy.pareto import ParetoFrontier

print("Testing Floor Search...")

# Simple test map - has a yellow door and yellow key
map_data = {
    "map": [
        [1, 1, 1, 1, 1, 1, 1],
        [1, 0, 0, 81, 0, 0, 1],
        [1, 0, 0, 0, 0, 201, 1],
        [1, 0, 0, 0, 0, 0, 1],
        [1, 1, 1, 1, 1, 1, 1]
    ]
}

floor_map = FloorMap.from_raw_data("MT1", map_data)
print(f"Floor map has {len(floor_map.nodes)} nodes")

search = FloorSearch(floor_map)

# Start at (1, 1) with 1 yellow key
start_state = GameState(
    floor="MT1", x=1, y=1,
    hp=100, yk=1, bk=0, rk=0,
    atk=10, def_=10
)

# Search - just explore everything
results = search.search(start_state, target_types=None)

print(f"Found {len(results)} Pareto optimal solutions")
assert isinstance(results, ParetoFrontier)
assert len(results) > 0

# Print the solutions
for i, sol in enumerate(results):
    print(f"  Solution {i}: HP={sol.hp}, YK={sol.yk}, BK={sol.bk}, ATK={sol.atk}, DEF={sol.def_}")

print("\n✅ All tests passed!")
