#!/usr/bin/env python3
"""Simple test script for Pareto Frontier"""

import sys
sys.path.insert(0, '')

from src.legacy.pareto import ParetoFrontier

print("Testing Pareto Frontier...")

# Test 1: Dominance
frontier = ParetoFrontier()

sol1 = (500, 3, 1, 20, 10)
frontier.add(sol1)
assert len(frontier) == 1, "First solution should be added"

sol2 = (400, 2, 0, 19, 9)
frontier.add(sol2)
assert len(frontier) == 1, "Dominated solution should not be added"

sol3 = (550, 2, 1, 20, 10)
frontier.add(sol3)
assert len(frontier) == 2, "Non-dominated solution should be added"

print("✓ Dominance test passed")

# Test 2: Iteration and contains
solutions = list(frontier)
assert len(solutions) == 2
assert sol1 in frontier
assert sol3 in frontier

print("✓ Iteration test passed")
print("\n✅ All tests passed!")
