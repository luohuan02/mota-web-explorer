from dataclasses import dataclass
from typing import List, Tuple, Iterator

@dataclass(frozen=True)
class Solution:
    hp: int
    yk: int
    bk: int
    atk: int
    def_: int

    def dominates(self, other: 'Solution') -> bool:
        """Return True if this solution dominates the other (better or equal in all dimensions, strictly better in at least one)."""
        return (self.hp >= other.hp and
                self.yk >= other.yk and
                self.bk >= other.bk and
                self.atk >= other.atk and
                self.def_ >= other.def_ and
                (self.hp > other.hp or
                 self.yk > other.yk or
                 self.bk > other.bk or
                 self.atk > other.atk or
                 self.def_ > other.def_))

class ParetoFrontier:
    def __init__(self):
        self._solutions: List[Solution] = []

    def add(self, solution: Tuple[int, int, int, int, int]) -> None:
        """Add a solution to the frontier if it's not dominated."""
        sol = Solution(*solution)

        # Check if this solution is dominated by any existing
        for existing in self._solutions:
            if existing.dominates(sol):
                return

        # Remove any existing solutions dominated by this one
        self._solutions = [s for s in self._solutions if not sol.dominates(s)]

        # Add the new solution
        self._solutions.append(sol)

    def __len__(self) -> int:
        return len(self._solutions)

    def __iter__(self) -> Iterator[Solution]:
        return iter(self._solutions)

    def __contains__(self, solution: Tuple[int, int, int, int, int]) -> bool:
        sol = Solution(*solution)
        return any(s == sol for s in self._solutions)
