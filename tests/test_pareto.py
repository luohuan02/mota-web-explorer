from src.legacy.pareto import ParetoFrontier

def test_pareto_dominance():
    """Test that dominated solutions are pruned."""
    frontier = ParetoFrontier()

    # Add initial solution
    sol1 = (500, 3, 1, 20, 10)
    frontier.add(sol1)
    assert len(frontier) == 1

    # Add a dominated solution (worse in all dimensions)
    sol2 = (400, 2, 0, 19, 9)
    frontier.add(sol2)
    assert len(frontier) == 1  # sol2 is dominated, not added

    # Add a non-dominated solution (better HP, worse YK)
    sol3 = (550, 2, 1, 20, 10)
    frontier.add(sol3)
    assert len(frontier) == 2  # both sol1 and sol3 kept

def test_pareto_iteration():
    """Test that we can iterate over frontier solutions."""
    frontier = ParetoFrontier()
    sol1 = (500, 3, 1, 20, 10)
    sol2 = (550, 2, 1, 20, 10)
    frontier.add(sol1)
    frontier.add(sol2)

    solutions = list(frontier)
    assert len(solutions) == 2
    assert sol1 in solutions
    assert sol2 in solutions
