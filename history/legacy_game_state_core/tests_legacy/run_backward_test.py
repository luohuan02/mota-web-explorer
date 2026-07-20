#!/usr/bin/env python3
"""Simple test script for Backward Pruning"""

import sys
sys.path.insert(0, '')

from src.legacy.backward import BackwardPruner, Constraints

print("Testing Backward Pruning...")

pruner = BackwardPruner()

# Test 1: Boss constraint generation
constraints = pruner.generate_boss_constraints(
    target_atk=27, target_def=27,
    boss_damage=300, guards_damage=300
)

assert constraints.min_hp == 600 + 100  # 300 + 300 + 100 margin
assert constraints.min_rk == 1
assert constraints.min_atk == 27
assert constraints.min_def == 27
assert constraints.max_atk == 27 + 10
assert constraints.max_def == 27 + 10

print("✓ Boss constraint generation works")

# Test 2: Pruning decision
# Case 1: Not enough keys
state1 = {"yk": 0}
constraints1 = Constraints(
    min_hp=600, min_yk=3, min_bk=0, min_rk=1,
    min_atk=27, min_def=27, max_atk=37, max_def=37,
    estimated_yk_gain=0, estimated_hp_gain=0
)
should_prune1 = pruner.should_prune(state1, constraints1)
assert should_prune1 is True

# Case 2: Not enough HP
state2 = {"yk": 5, "hp": 300}
should_prune2 = pruner.should_prune(state2, constraints1)
assert should_prune2 is True

# Case 3: Should be okay
state3 = {"yk": 5, "hp": 700}
should_prune3 = pruner.should_prune(state3, constraints1)
assert should_prune3 is False

print("✓ Pruning decision works")

# Test 3: Baseline
baseline_state = {"hp": 800}
pruner.set_baseline(baseline_state, hp_margin=200)

state_ok = {"hp": 650}  # above 800-200 = 600
assert pruner.worse_than_baseline(state_ok) is False

state_bad = {"hp": 500}  # below 600
assert pruner.worse_than_baseline(state_bad) is True

print("✓ Baseline check works")

print("\n✅ All tests passed!")
