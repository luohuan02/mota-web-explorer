#!/usr/bin/env python3
"""Simple test script for Stepwise Calculator"""

import sys
sys.path.insert(0, '')

from src.legacy.stepwise import StepwiseCalculator

print("Testing Stepwise Calculator...")

calc = StepwiseCalculator()

# Test 1: Attack stepwise calculation
# Bat: hp=35, atk=38, def=3
# ATK=10: damage=7, rounds=ceil(35/7)=5
# ATK=19: damage=16, rounds=3
# ATK=21: damage=18, rounds=2  <-- step!
step_gains = calc.calculate_attack_steps(
    enemy_hp=35, enemy_atk=38, enemy_def=3,
    current_atk=10, target_atk=30
)

print(f"Found {len(step_gains)} attack steps")
assert len(step_gains) > 0

# Print them out
for atk, hp_saved in step_gains:
    print(f"  ATK={atk}: HP saved={hp_saved}")

print("✓ Attack stepwise calculation test passed")

# Test 2: Defense zero damage point
# Enemy ATK=18
# DEF=18: enemy damage=1
# DEF=19: enemy damage=1 (no change)
# ...
# The formula changes at DEF=18
zero_def = calc.find_zero_damage_def(enemy_atk=18)
assert zero_def == 18

print("✓ Defense zero damage point test passed")

print("\n✅ All tests passed!")
