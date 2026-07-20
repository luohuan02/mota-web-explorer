from dataclasses import dataclass
from typing import List, Optional
from src.legacy.game_state import GameState
from src.legacy.stepwise import StepwiseCalculator

@dataclass
class FlybackCandidate:
    floor_id: str
    item_type: str
    position: tuple
    score: int
    estimated_cost: int

class FlybackFinder:
    def __init__(self):
        self.stepwise = StepwiseCalculator()

    def find_candidates(self, state: GameState, visited_floors: List[str],
                     min_score: int = 0) -> List[FlybackCandidate]:
        """Find valuable flyback candidates."""
        candidates = []

        # Only trigger on significant stat gains
        if state.atk < 20 and state.def_ < 20:
            return candidates

        # TODO: For each visited floor, look for valuable items
        # that would now be cheaper to get with higher stats

        # Placeholder logic
        if state.atk >= 20 and "MT4" in visited_floors:
            candidates.append(FlybackCandidate(
                floor_id="MT4",
                item_type="redGem",
                position=(0, 0),
                score=100,
                estimated_cost=50
            ))

        # Filter by minimum score
        return [c for c in candidates if c.score > min_score]

    def should_trigger_flyback(self, old_atk: int, new_atk: int,
                          old_def: int, new_def: int) -> bool:
        """Check if we should consider flyback after stat change."""
        if new_atk >= 20 and old_atk < 20:
            return True  # Got sword!
        if new_def >= 20 and old_def < 20:
            return True  # Got shield!
        return False
