#!/usr/bin/env python3
"""Simple test script for Floor Map"""

import sys
sys.path.insert(0, '')

from src.legacy.floor_map import FloorMap

print("Testing Floor Map...")

# Use simple test data
map_data = {
    "map": [
        [1, 1, 1, 1, 1],
        [1, 0, 0, 0, 1],
        [1, 0, 201, 0, 1],
        [1, 0, 0, 0, 1],
        [1, 1, 1, 1, 1]
    ],
    "upFloor": [1, 1],
    "downFloor": [3, 3]
}

floor_map = FloorMap.from_raw_data("MT4", map_data)

# Test 1: Basic properties
assert floor_map.floor_id == "MT4"
assert floor_map.width == 5
assert floor_map.height == 5

print("✓ Basic properties test passed")

# Test 2: Wall detection
assert floor_map.is_wall(0, 0) is True
assert floor_map.is_wall(1, 1) is False
assert floor_map.is_wall(2, 2) is False

print("✓ Wall detection test passed")

# Test 3: Nodes
# Should have one yellow key at (2, 2)
assert len(floor_map.nodes) == 1
node = floor_map.nodes[0]
assert node.x == 2
assert node.y == 2
assert node.id == "yellowKey"
assert node.no_pass is False

print("✓ Nodes test passed")

# Test 4: Node at position
node_data = floor_map.get_node_at(2, 2)
assert node_data is not None
node_idx, node_obj = node_data
assert node_idx == 0
assert node_obj == node

print("✓ Node at position test passed")

print("✓ Node at position test passed")

# Test 5: BFS Connectivity
# Create a slightly more complex map
map_data2 = {
    "map": [
        [1, 1, 1, 1, 1, 1, 1],
        [1, 0, 0, 0, 0, 0, 1],
        [1, 0, 1, 1, 1, 0, 1],
        [1, 0, 0, 201, 0, 0, 1],
        [1, 0, 1, 1, 1, 0, 1],
        [1, 0, 0, 0, 0, 0, 1],
        [1, 1, 1, 1, 1, 1, 1]
    ]
}

floor_map2 = FloorMap.from_raw_data("MT1", map_data2)
# Start at (1, 1), visited nothing
reachable = floor_map2.get_reachable_nodes(start_x=1, start_y=1, visited=0)
# Should find the yellow key at (3, 3)
assert len(reachable) >= 1
found_key = any(floor_map2.nodes[idx].id == "yellowKey" for idx in reachable)
assert found_key is True

print("✓ BFS connectivity test passed")

print("\n✅ All tests passed!")
