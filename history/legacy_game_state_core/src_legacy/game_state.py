from dataclasses import dataclass
from enum import Enum
import math

class NodeType(Enum):
    EMPTY = 0
    WALL = 1
    ENEMY = 2
    YELLOW_DOOR = 3
    BLUE_DOOR = 4
    RED_DOOR = 5
    SPECIAL_DOOR = 6
    YELLOW_KEY = 7
    BLUE_KEY = 8
    RED_KEY = 9
    RED_POTION = 10
    BLUE_POTION = 11
    RED_GEM = 12
    BLUE_GEM = 13
    SWORD = 14
    SHIELD = 15
    UP_STAIRS = 16
    DOWN_STAIRS = 17
    FAKE_WALL = 18

@dataclass(frozen=True)
class Node:
    x: int
    y: int
    type: NodeType
    id: str
    no_pass: bool

@dataclass
class GameState:
    floor: str
    x: int
    y: int
    hp: int
    yk: int
    bk: int
    rk: int
    atk: int
    def_: int
    visited: int = 0  # bitmask

    HP_MAX = 9999

    def calculate_damage(self, enemy_hp: int, enemy_atk: int, enemy_def: int) -> int:
        """Calculate damage taken when fighting an enemy (hero attacks first)."""
        my_damage = max(1, self.atk - enemy_def)
        enemy_damage = max(1, enemy_atk - self.def_)
        rounds = math.ceil(enemy_hp / my_damage)
        return (rounds - 1) * enemy_damage

    def with_hp(self, delta: int) -> 'GameState':
        """Return new state with HP modified (capped at 0 and HP_MAX)."""
        new_hp = max(0, min(self.HP_MAX, self.hp + delta))
        return GameState(
            floor=self.floor, x=self.x, y=self.y,
            hp=new_hp, yk=self.yk, bk=self.bk, rk=self.rk,
            atk=self.atk, def_=self.def_, visited=self.visited
        )

    def with_keys(self, yk_delta: int = 0, bk_delta: int = 0, rk_delta: int = 0) -> 'GameState':
        """Return new state with keys modified."""
        return GameState(
            floor=self.floor, x=self.x, y=self.y,
            hp=self.hp,
            yk=self.yk + yk_delta, bk=self.bk + bk_delta, rk=self.rk + rk_delta,
            atk=self.atk, def_=self.def_, visited=self.visited
        )

    def with_stats(self, atk_delta: int = 0, def_delta: int = 0) -> 'GameState':
        """Return new state with stats modified."""
        return GameState(
            floor=self.floor, x=self.x, y=self.y,
            hp=self.hp, yk=self.yk, bk=self.bk, rk=self.rk,
            atk=self.atk + atk_delta, def_=self.def_ + def_delta,
            visited=self.visited
        )

    def with_visited(self, node_idx: int) -> 'GameState':
        """Return new state with node marked as visited."""
        new_visited = self.visited | (1 << node_idx)
        return GameState(
            floor=self.floor, x=self.x, y=self.y,
            hp=self.hp, yk=self.yk, bk=self.bk, rk=self.rk,
            atk=self.atk, def_=self.def_, visited=new_visited
        )

    def is_visited(self, node_idx: int) -> bool:
        """Check if node has been visited."""
        return (self.visited & (1 << node_idx)) != 0
