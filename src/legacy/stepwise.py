import math
from typing import List, Tuple, Dict

class StepwiseCalculator:
    def calculate_attack_steps(self, enemy_hp: int, enemy_atk: int, enemy_def: int,
                              current_atk: int, target_atk: int) -> List[Tuple[int, int]]:
        """Calculate ATK step points where damage drops (fewer rounds)."""
        steps = []

        for atk in range(current_atk, target_atk + 1):
            my_damage = max(1, atk - enemy_def)
            rounds = math.ceil(enemy_hp / my_damage)

            # Check if next ATK would reduce rounds
            if atk < target_atk:
                next_damage = max(1, (atk + 1) - enemy_def)
                next_rounds = math.ceil(enemy_hp / next_damage)
                if next_rounds < rounds:
                    enemy_damage = max(1, enemy_atk - 10)  # placeholder DEF
                    hp_saved = (rounds - next_rounds) * enemy_damage
                    steps.append((atk + 1, hp_saved))

        return steps

    def find_zero_damage_def(self, enemy_atk: int) -> int:
        """Find DEF needed to take zero damage from enemy."""
        # DEF >= enemy_ATK means enemy_damage = max(1, enemy_atk - DEF) = 1
        # Actually zero damage isn't possible without special items
        # Return enemy_atk as the point where formula changes
        return enemy_atk

    def score_candidate(self, item_type: str, current_atk: int, current_def: int,
                      enemies: List[Dict]) -> int:
        """Score an item candidate (gem/key/potion) based on future gains."""
        score = 0

        if item_type == "redGem":
            # Score = HP saved on future enemies
            for enemy in enemies:
                steps = self.calculate_attack_steps(
                    enemy["hp"], enemy["atk"], enemy["def"],
                    current_atk + 1, current_atk + 1
                )
                if steps:
                    score += steps[0][1]

        elif item_type == "blueGem":
            # DEF gains are less dramatic
            score = 10  # placeholder

        return score
