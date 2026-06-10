from dataclasses import dataclass
from typing import Dict, Optional, List
from src.legacy.config import load_floor_config, FloorSequence, FloorConfig
from src.legacy.game_state import GameState
from src.legacy.floor_map import FloorMap
from src.legacy.floor_search import FloorSearch
from src.legacy.pareto import ParetoFrontier

@dataclass
class CheckpointResult:
    floor_id: str
    frontier: ParetoFrontier
    paths: List  # For each solution, the path taken

class MultiFloorSearch:
    def __init__(self, floor_config_path: str, maps_data: Optional[Dict] = None):
        self.sequence = load_floor_config(floor_config_path)
        self.floor_maps: Dict[str, FloorMap] = {}
        self.floor_searches: Dict[str, FloorSearch] = {}

        # Load maps if provided
        if maps_data:
            for floor_id, map_data in maps_data.items():
                self._load_floor(floor_id, map_data)

    def _load_floor(self, floor_id: str, map_data: Dict) -> None:
        """Load a single floor map and searcher."""
        floor_map = FloorMap.from_raw_data(floor_id, map_data)
        self.floor_maps[floor_id] = floor_map
        self.floor_searches[floor_id] = FloorSearch(floor_map)

    def search_to_checkpoint(self, start_state: GameState, target_checkpoint: str) -> CheckpointResult:
        """Search from start state to target checkpoint."""
        current_frontier = ParetoFrontier()

        # Add start state to frontier
        current_frontier.add((start_state.hp, start_state.yk, start_state.bk, start_state.atk, start_state.def_))

        # Get start floor index
        start_idx = self.sequence.floor_index[start_state.floor]
        target_idx = self.sequence.floor_index[target_checkpoint]

        # Process each floor in sequence
        for i in range(start_idx, target_idx + 1):
            floor_config = self.sequence.floors[i]
            floor_id = floor_config.floor_id

            if floor_id not in self.floor_searches:
                raise ValueError(f"Floor {floor_id} not loaded")

            # For each solution in current frontier, search this floor
            new_frontier = ParetoFrontier()

            # TODO: For each solution in current_frontier
            #   - search floor for stairs
            #   - add resulting solutions to new_frontier

            current_frontier = new_frontier

            if floor_id == target_checkpoint:
                break

        return CheckpointResult(
            floor_id=target_checkpoint,
            frontier=current_frontier,
            paths=[]
        )
