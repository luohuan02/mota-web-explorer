from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import json
from collections import deque
from src.legacy.game_state import Node, NodeType

# Tile ID mapping (from raw2pf.py)
TILE_MAPPING = {
    1: (NodeType.WALL, "wall", True),
    81: (NodeType.YELLOW_DOOR, "yellowDoor", True),
    82: (NodeType.BLUE_DOOR, "blueDoor", True),
    83: (NodeType.RED_DOOR, "redDoor", True),
    85: (NodeType.SPECIAL_DOOR, "specialDoor", True),
    201: (NodeType.YELLOW_KEY, "yellowKey", False),
    202: (NodeType.BLUE_KEY, "blueKey", False),
    209: (NodeType.RED_KEY, "redKey", False),
    210: (NodeType.RED_POTION, "redPotion", False),
    211: (NodeType.BLUE_POTION, "bluePotion", False),
    217: (NodeType.RED_GEM, "redGem", False),
    218: (NodeType.BLUE_GEM, "blueGem", False),
    35: (NodeType.SWORD, "sword1", False),
    36: (NodeType.SHIELD, "shield1", False),
    2: (NodeType.FAKE_WALL, "fakeWall", False),
}

# Enemy tile IDs (need to map from actual game data)
ENEMY_TILES = {7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23}

@dataclass
class FloorMap:
    floor_id: str
    width: int
    height: int
    map_grid: List[List[int]]
    nodes: List[Node]
    node_at_pos: Dict[Tuple[int, int], int]  # (x,y) -> node index
    up_stairs_pos: Optional[Tuple[int, int]]
    down_stairs_pos: Optional[Tuple[int, int]]

    @classmethod
    def from_raw_data(cls, floor_id: str, raw_data: Dict) -> 'FloorMap':
        """Create FloorMap from raw game data (like zone1_maps.json)."""
        map_grid = raw_data["map"]
        height = len(map_grid)
        width = len(map_grid[0]) if height > 0 else 0

        nodes = []
        node_at_pos = {}

        # Collect nodes (enemies, doors, items, stairs, fake walls)
        for y in range(height):
            for x in range(width):
                tile_id = map_grid[y][x]
                node_type, node_id, no_pass = cls._classify_tile(tile_id, x, y, raw_data)

                if node_type is not None:
                    node = Node(x=x, y=y, type=node_type, id=node_id, no_pass=no_pass)
                    node_idx = len(nodes)
                    nodes.append(node)
                    node_at_pos[(x, y)] = node_idx

        up_stairs = tuple(raw_data.get("upFloor", [0, 0])) if "upFloor" in raw_data else None
        down_stairs = tuple(raw_data.get("downFloor", [0, 0])) if "downFloor" in raw_data else None

        return cls(
            floor_id=floor_id,
            width=width, height=height,
            map_grid=map_grid,
            nodes=nodes, node_at_pos=node_at_pos,
            up_stairs_pos=up_stairs,
            down_stairs_pos=down_stairs
        )

    @classmethod
    def _classify_tile(cls, tile_id: int, x: int, y: int, raw_data: Dict) -> Tuple[Optional[NodeType], str, bool]:
        """Classify a tile ID into a node type."""
        # Skip walls - they are obstacles, not interactable nodes
        if tile_id == 1:
            return (None, "", False)

        if tile_id in TILE_MAPPING:
            return TILE_MAPPING[tile_id]

        if tile_id in ENEMY_TILES:
            # Need actual enemy data from game
            return (NodeType.ENEMY, f"enemy_{tile_id}", True)

        # Stairs (we handle specially)
        return (None, "", False)

    def is_wall(self, x: int, y: int) -> bool:
        """Check if position is a wall."""
        if x < 0 or y < 0 or x >= self.width or y >= self.height:
            return True
        return self.map_grid[y][x] == 1

    def get_node_at(self, x: int, y: int) -> Optional[Tuple[int, Node]]:
        """Get node at position, if any."""
        if (x, y) in self.node_at_pos:
            idx = self.node_at_pos[(x, y)]
            return (idx, self.nodes[idx])
        return None

    def get_reachable_nodes(self, start_x: int, start_y: int, visited: int) -> List[int]:
        """BFS to find all reachable unvisited nodes from start position."""
        visited_pos = set()
        queue = deque([(start_x, start_y)])
        visited_pos.add((start_x, start_y))

        reachable_node_indices = []

        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]

        while queue:
            x, y = queue.popleft()

            # Check if this position has a node
            node_data = self.get_node_at(x, y)
            if node_data is not None:
                node_idx, node = node_data
                if not (visited & (1 << node_idx)):
                    # Found an unvisited node
                    reachable_node_indices.append(node_idx)

                # Even if visited, we can pass through (treat as empty)
                for dx, dy in directions:
                    nx, ny = x + dx, y + dy
                    if (nx, ny) not in visited_pos and not self.is_wall(nx, ny):
                        visited_pos.add((nx, ny))
                        queue.append((nx, ny))
                continue

            # Empty space, explore neighbors
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if (nx, ny) not in visited_pos and not self.is_wall(nx, ny):
                    # Check if neighbor has a no_pass node that's unvisited
                    neighbor_node = self.get_node_at(nx, ny)
                    if neighbor_node is not None:
                        _, node = neighbor_node
                        if node.no_pass and not (visited & (1 << neighbor_node[0])):
                            # Can't pass through unvisited no_pass node
                            continue
                    visited_pos.add((nx, ny))
                    queue.append((nx, ny))

        return reachable_node_indices
