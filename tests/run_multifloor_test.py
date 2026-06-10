#!/usr/bin/env python3
"""Simple test script for Multi-Floor Search"""

import sys
sys.path.insert(0, '')

from src.legacy.multi_floor import MultiFloorSearch, CheckpointResult
from src.legacy.game_state import GameState
from src.legacy.pareto import ParetoFrontier
from src.legacy.floor_map import FloorMap

print("Testing Multi-Floor Search...")

# Create mock floor maps
# Just two simple floors for testing
floor1_map_data = {
    "map": [
        [1, 1, 1, 1, 1, 1, 1],
        [1, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 201, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 1],
        [1, 1, 1, 1, 1, 1, 1]
    ],
    "upFloor": [5, 2]
}

floor2_map_data = {
    "map": [
        [1, 1, 1, 1, 1, 1, 1],
        [1, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 1],
        [1, 1, 1, 1, 1, 1, 1]
    ]
}

maps_data = {
    "MT1": floor1_map_data,
    "MT2": floor2_map_data
}

search = MultiFloorSearch(floor_config_path="config/floors_zone1.json", maps_data=maps_data)

print("✓ MultiFloorSearch initialized")

# Start state
start_state = GameState(
    floor="MT1", x=1, y=1,
    hp=400, yk=5, bk=1, rk=0,
    atk=10, def_=10
)

# Just test that the API works - we won't do actual search yet
# since we need to implement more functionality
result = search.search_to_checkpoint(start_state, target_checkpoint="MT2")

assert isinstance(result, CheckpointResult)
print(f"✓ Search to checkpoint returned result with {len(result.frontier)} solutions")

print("\n✅ All tests passed!")
