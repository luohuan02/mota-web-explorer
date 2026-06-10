#!/usr/bin/env python3
"""Debug script for Floor Map"""

import sys
sys.path.insert(0, '')

from src.legacy.floor_map import FloorMap, TILE_MAPPING

print("Tile mapping keys:", list(TILE_MAPPING.keys()))
print("201 in mapping?", 201 in TILE_MAPPING)
if 201 in TILE_MAPPING:
    print("201 maps to:", TILE_MAPPING[201])

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
print("\nNodes found:", len(floor_map.nodes))
for i, node in enumerate(floor_map.nodes):
    print(f"  Node {i}: ({node.x}, {node.y}), type={node.type}, id={node.id}")
