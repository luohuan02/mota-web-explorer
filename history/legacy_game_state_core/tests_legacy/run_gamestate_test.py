#!/usr/bin/env python3
"""Simple test script for Game State"""

import sys
sys.path.insert(0, '')

from src.legacy.game_state import GameState, Node, NodeType

print("Testing Game State...")

# Test 1: Creation
state = GameState(
    floor="MT4",
    x=11, y=10,
    hp=926, yk=4, bk=1, rk=0,
    atk=10, def_=10
)
assert state.floor == "MT4"
assert state.x == 11
assert state.y == 10
assert state.hp == 926
assert state.yk == 4
assert state.bk == 1
assert state.atk == 10
assert state.def_ == 10

print("✓ Creation test passed")

# Test 2: Damage calculation
# Green Slime: hp=35, atk=18, def=1
# My damage: max(1,10-1)=9 per hit
# Hits to kill: ceil(35/9)=4 hits
# Enemy damage: max(1,18-10)=8 per hit
# I take (4-1)*8=24 damage
damage = state.calculate_damage(enemy_hp=35, enemy_atk=18, enemy_def=1)
assert damage == 24

print("✓ Damage calculation test passed")

# Test 3: HP modification
state2 = state.with_hp(-10)
assert state2.hp == 916
state3 = state2.with_hp(50)
assert state3.hp == 966
state4 = state3.with_hp(100)
assert state4.hp == 1066

# Test HP clamping
state_low = state.with_hp(-1000)
assert state_low.hp == 0

print("✓ HP modification test passed")

# Test 4: Key modification
state5 = state.with_keys(yk_delta=1)
assert state5.yk == 5
state6 = state5.with_keys(bk_delta=-1)
assert state6.bk == 0

print("✓ Key modification test passed")

# Test 5: Stat modification
state7 = state.with_stats(atk_delta=1)
assert state7.atk == 11
state8 = state7.with_stats(def_delta=5)
assert state8.def_ == 15

print("✓ Stat modification test passed")

# Test 6: Visited
state9 = state.with_visited(0)
assert state9.is_visited(0) is True
assert state9.is_visited(1) is False

state10 = state9.with_visited(1)
assert state10.is_visited(0) is True
assert state10.is_visited(1) is True

print("✓ Visited test passed")

print("\n✅ All tests passed!")
