#!/usr/bin/env python3
"""Simple test script for Browser Controller"""

import sys
sys.path.insert(0, '')

from src.legacy.browser import BrowserController
from src.legacy.game_state import GameState

print("Testing Browser Controller...")

controller = BrowserController(profile="openclaw")

# Test 1: Check that API exists
assert hasattr(controller, "read_game_state")
assert hasattr(controller, "export_floor_map")
assert hasattr(controller, "move_to_position")
assert hasattr(controller, "press_key")
assert hasattr(controller, "save_game")
assert hasattr(controller, "load_game")
assert hasattr(controller, "verify_state")

print("✓ API methods exist")

# Test 2: Read state (placeholder)
state = controller.read_game_state()
assert isinstance(state, GameState)
print(f"✓ Read game state: HP={state.hp}, ATK={state.atk}, DEF={state.def_}")

# Test 3: Verify state (placeholder)
is_ok = controller.verify_state(state)
assert is_ok is True
print("✓ State verification works")

print("\n✅ All tests passed!")
