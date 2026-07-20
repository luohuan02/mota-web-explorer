from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class Constraints:
    min_hp: int
    min_yk: int
    min_bk: int
    min_rk: int
    min_atk: int
    min_def: int
    max_atk: int
    max_def: int
    estimated_yk_gain: int
    estimated_hp_gain: int

class BackwardPruner:
    def generate_boss_constraints(self, target_atk: int, target_def: int,
                                 boss_damage: int, guards_damage: int) -> Constraints:
        """Generate constraints for Boss fight victory."""
        total_damage = boss_damage + guards_damage
        hp_margin = 100

        return Constraints(
            min_hp=total_damage + hp_margin,
            min_yk=0, min_bk=0, min_rk=1,
            min_atk=target_atk, min_def=target_def,
            max_atk=target_atk + 10, max_def=target_def + 10,
            estimated_yk_gain=0, estimated_hp_gain=0
        )

    def should_prune(self, state: Dict[str, int], constraints: Constraints) -> bool:
        """Check if state should be pruned (impossible to reach goal)."""
        yk_needed = constraints.min_yk - constraints.estimated_yk_gain
        if state.get("yk", 0) < yk_needed:
            return True

        if state.get("hp", 0) < constraints.min_hp:
            return True

        # Property has diminishing returns above certain point
        if constraints.max_atk and state.get("atk", 0) > constraints.max_atk:
            # Still keep, but prioritize other solutions
            pass

        return False

    def set_baseline(self, baseline_state: Dict[str, int], hp_margin: int = 200):
        """Set baseline from greedy run for pruning."""
        self.baseline_hp = baseline_state.get("hp", 0)
        self.hp_margin = hp_margin

    def worse_than_baseline(self, state: Dict[str, int]) -> bool:
        """Check if state is significantly worse than baseline."""
        hp = state.get("hp", 0)
        return hp < (self.baseline_hp - self.hp_margin)
