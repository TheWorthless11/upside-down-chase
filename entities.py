"""Game entities: Direction, AgentState, Snapshot, and utility functions."""

from dataclasses import dataclass
from enum import Enum
from typing import List, Set, Tuple


class Direction(Enum):
    """Cardinal directions for movement."""
    NORTH = (0, -1)
    SOUTH = (0, 1)
    EAST = (1, 0)
    WEST = (-1, 0)
    NONE = (0, 0)


CARDINALS = [Direction.NORTH, Direction.SOUTH, Direction.EAST, Direction.WEST]
OPPOSITE = {
    Direction.NORTH: Direction.SOUTH,
    Direction.SOUTH: Direction.NORTH,
    Direction.EAST: Direction.WEST,
    Direction.WEST: Direction.EAST,
    Direction.NONE: Direction.NONE,
}


def add_pos(a: Tuple[int, int], b: Tuple[int, int]) -> Tuple[int, int]:
    """Add two positions together."""
    return (a[0] + b[0], a[1] + b[1])


def manhattan(a: Tuple[int, int], b: Tuple[int, int]) -> int:
    """Calculate Manhattan distance between two positions."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def direction_between(src: Tuple[int, int], dst: Tuple[int, int]) -> Direction:
    """Get the cardinal direction from src to dst."""
    dx = dst[0] - src[0]
    dy = dst[1] - src[1]
    if dx == 1 and dy == 0:
        return Direction.EAST
    if dx == -1 and dy == 0:
        return Direction.WEST
    if dx == 0 and dy == 1:
        return Direction.SOUTH
    if dx == 0 and dy == -1:
        return Direction.NORTH
    return Direction.NONE


@dataclass
class AgentState:
    """Represents an agent's current state."""
    x: int
    y: int
    direction: Direction
    hp: int

    def pos(self) -> Tuple[int, int]:
        return (self.x, self.y)


@dataclass
class Snapshot:
    """Game state snapshot for MCTS/Minimax search."""
    eleven: AgentState
    demogorgons: List[AgentState]
    coins: Set[Tuple[int, int]]
    key_pos: Tuple[int, int]
    has_key: bool
    turns_left: int
    points: int = 0
    last_shoot_time: int = 0

    def clone(self) -> "Snapshot":
        return Snapshot(
            eleven=AgentState(self.eleven.x, self.eleven.y, self.eleven.direction, self.eleven.hp),
            demogorgons=[AgentState(d.x, d.y, d.direction, d.hp) for d in self.demogorgons],
            coins=set(self.coins),
            key_pos=self.key_pos,
            has_key=self.has_key,
            turns_left=self.turns_left,
            points=self.points,
            last_shoot_time=self.last_shoot_time,
        )
