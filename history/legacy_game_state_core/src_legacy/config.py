from dataclasses import dataclass
from typing import List, Optional, Dict
import json

@dataclass
class FloorConfig:
    floor_id: str
    next_floor: Optional[str]  # Which floor to go to next
    prev_floor: Optional[str]
    is_checkpoint: bool = False

@dataclass
class FloorSequence:
    floors: List[FloorConfig]
    checkpoints: List[str]  # List of floor IDs that are checkpoints
    floor_index: Dict[str, int]

    @classmethod
    def from_dict(cls, data: Dict) -> 'FloorSequence':
        floors = []
        for floor_data in data["floors"]:
            floors.append(FloorConfig(
                floor_id=floor_data["id"],
                next_floor=floor_data.get("next"),
                prev_floor=floor_data.get("prev"),
                is_checkpoint=floor_data.get("checkpoint", False)
            ))

        floor_index = {f.floor_id: i for i, f in enumerate(floors)}
        checkpoints = [f.floor_id for f in floors if f.is_checkpoint]

        return cls(floors=floors, checkpoints=checkpoints, floor_index=floor_index)

def load_floor_config(path: str) -> FloorSequence:
    """Load floor configuration from JSON file."""
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return FloorSequence.from_dict(data)
