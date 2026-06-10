#!/usr/bin/env python3
"""Simple test script for Floor Config"""

import sys
sys.path.insert(0, '')

from src.legacy.config import load_floor_config, FloorSequence

print("Testing Floor Config...")

# Load the config
config = load_floor_config("config/floors_zone1.json")

assert isinstance(config, FloorSequence)
assert len(config.floors) == 10

print("✓ Config loaded successfully")

# Check floors
assert config.floors[0].floor_id == "MT1"
assert config.floors[0].next_floor == "MT2"
assert config.floors[0].prev_floor is None

assert config.floors[4].floor_id == "MT5"
assert config.floors[4].is_checkpoint is True

assert config.floors[-1].floor_id == "MT10"
assert config.floors[-1].next_floor is None

print("✓ Floor configs are correct")

# Check checkpoints
assert len(config.checkpoints) == 3
assert "MT5" in config.checkpoints
assert "MT9" in config.checkpoints
assert "MT10" in config.checkpoints

print("✓ Checkpoints are correct")

# Check floor index
assert config.floor_index["MT1"] == 0
assert config.floor_index["MT5"] == 4
assert config.floor_index["MT10"] == 9

print("✓ Floor index works")

print("\n✅ All tests passed!")
