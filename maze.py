"""Maze generation and navigation."""

import heapq
import random
from typing import Dict, List, Optional, Set, Tuple

import pygame

from entities import CARDINALS, add_pos, direction_between, manhattan, Direction


# Constants
GRID_SIZE = 12
CELL_SIZE = 50

COLOR_FLOOR = (52, 46, 60)
COLOR_WALL = (82, 75, 92)
COLOR_EXIT = (240, 175, 45)
COLOR_EXIT_LOCKED = (140, 95, 40)
COLOR_TUNNEL = (70, 150, 200)
COLOR_TUNNEL_GLOW = (95, 210, 255)


def generate_floor_tile(size: int = CELL_SIZE) -> pygame.Surface:
    s = pygame.Surface((size, size))
    s.fill(COLOR_FLOOR)
    for _ in range(10):
        x = random.randint(0, size - 8)
        y = random.randint(0, size - 8)
        w = random.randint(6, 18)
        h = random.randint(6, 18)
        shift = random.randint(-9, 9)
        c = (
            max(0, min(255, COLOR_FLOOR[0] + shift)),
            max(0, min(255, COLOR_FLOOR[1] + shift)),
            max(0, min(255, COLOR_FLOOR[2] + shift)),
        )
        pygame.draw.rect(s, c, (x, y, w, h))
    return s


def generate_wall_tile(size: int = CELL_SIZE) -> pygame.Surface:
    s = pygame.Surface((size, size))
    s.fill(COLOR_WALL)
    for row in range(4):
        offset = (row % 2) * (size // 4)
        for col in range(3):
            x = col * (size // 2) + offset - size // 4
            y = row * (size // 4)
            pygame.draw.rect(s, (95, 88, 105), (x + 2, y + 2, size // 2 - 4, size // 4 - 4))
    return s


class Maze:
    def __init__(self, size: int = GRID_SIZE):
        self.size = size
        self.walls: Set[Tuple[int, int]] = set()
        self.exit_pos: Tuple[int, int] = (size - 1, size // 2)
        self.entry_pos: Tuple[int, int] = (0, 0)
        self.tunnels: Dict[Tuple[int, int], Tuple[int, int]] = {}

        self.floor_tile = generate_floor_tile()
        self.wall_tile = generate_wall_tile()

        self._generate()

    def _generate(self):
        self.walls = {(x, y) for x in range(self.size) for y in range(self.size)}

        odd_cells = [i for i in range(1, self.size - 1, 2)]
        start = (random.choice(odd_cells), random.choice(odd_cells))

        visited = {start}
        stack = [start]
        self.walls.discard(start)

        while stack:
            x, y = stack[-1]
            neighbors = []
            for dx, dy in [(2, 0), (-2, 0), (0, 2), (0, -2)]:
                nx, ny = x + dx, y + dy
                if 1 <= nx < self.size - 1 and 1 <= ny < self.size - 1 and (nx, ny) not in visited:
                    neighbors.append((nx, ny, x + dx // 2, y + dy // 2))

            if neighbors:
                nx, ny, wx, wy = random.choice(neighbors)
                visited.add((nx, ny))
                self.walls.discard((wx, wy))
                self.walls.discard((nx, ny))
                stack.append((nx, ny))
            else:
                stack.pop()

        room_count = random.randint(2, 4)
        for _ in range(room_count):
            rw = random.randint(2, 3)
            rh = random.randint(2, 3)
            rx = random.randint(1, self.size - rw - 2)
            ry = random.randint(1, self.size - rh - 2)
            for y in range(ry, ry + rh):
                for x in range(rx, rx + rw):
                    self.walls.discard((x, y))

        loops = random.randint(5, 9)
        for _ in range(loops):
            x = random.randint(1, self.size - 2)
            y = random.randint(1, self.size - 2)
            if (x, y) not in self.walls:
                continue
            floor_neighbors = 0
            for d in CARDINALS:
                nx, ny = add_pos((x, y), d.value)
                if (nx, ny) not in self.walls and 0 <= nx < self.size and 0 <= ny < self.size:
                    floor_neighbors += 1
            if floor_neighbors >= 2:
                self.walls.discard((x, y))

        self._generate_exit()
        self._generate_tunnels()

    def _generate_exit(self):
        candidates = []
        edge_cells = []
        for i in range(1, self.size - 1):
            edge_cells.extend([(i, 0, i, 1), (i, self.size - 1, i, self.size - 2), (0, i, 1, i), (self.size - 1, i, self.size - 2, i)])

        random.shuffle(edge_cells)
        for ex, ey, ix, iy in edge_cells:
            if (ix, iy) not in self.walls:
                candidates.append((ex, ey))

        self.exit_pos = random.choice(candidates) if candidates else (self.size - 1, self.size // 2)
        self.walls.discard(self.exit_pos)

    def _generate_tunnels(self):
        """Generate 4 interconnected tunnel gates with random exit points."""
        floor_cells = [
            (x, y)
            for x in range(1, self.size - 1)
            for y in range(1, self.size - 1)
            if (x, y) not in self.walls
        ]
        if len(floor_cells) < 4:
            return

        gates = []
        for _ in range(4):
            if not gates:
                a = random.choice(floor_cells)
                gates.append(a)
            else:
                far = [cell for cell in floor_cells if manhattan(cell, gates[0]) >= self.size // 2 and cell not in gates]
                next_gate = random.choice(far) if far else random.choice([c for c in floor_cells if c not in gates])
                while next_gate in gates:
                    next_gate = random.choice(floor_cells)
                gates.append(next_gate)

        for gate in gates:
            other_gates = [g for g in gates if g != gate]
            self.tunnels[gate] = other_gates

    def is_walkable(self, pos: Tuple[int, int]) -> bool:
        x, y = pos
        if x < 0 or y < 0 or x >= self.size or y >= self.size:
            return False
        return pos not in self.walls

    def move_with_tunnel(self, pos: Tuple[int, int], direction: Direction) -> Tuple[int, int]:
        if direction == Direction.NONE:
            return pos

        nxt = add_pos(pos, direction.value)
        if not self.is_walkable(nxt):
            return pos
        if nxt in self.tunnels:
            exit_gates = self.tunnels[nxt]
            if isinstance(exit_gates, list):
                return random.choice(exit_gates)
            return exit_gates
        return nxt

    def draw(self, screen: pygame.Surface, offset_y: int, has_key: bool, hud_height: int):
        for x in range(self.size):
            for y in range(self.size):
                screen.blit(self.floor_tile, (x * CELL_SIZE, y * CELL_SIZE + offset_y))

        for x, y in self.walls:
            screen.blit(self.wall_tile, (x * CELL_SIZE, y * CELL_SIZE + offset_y))

        ex, ey = self.exit_pos
        color = (220, 50, 50) if has_key else COLOR_EXIT_LOCKED
        x_pos = ex * CELL_SIZE + 12
        y_pos = ey * CELL_SIZE + offset_y + 16
        door_w = CELL_SIZE - 24
        door_h = CELL_SIZE - 24
        pygame.draw.rect(screen, color, (x_pos, y_pos, door_w, door_h))
        pygame.draw.arc(screen, color, (x_pos, y_pos - door_h // 3, door_w, door_h), 3.14, 6.28, 3)

        for t_in, _ in self.tunnels.items():
            tx, ty = t_in
            half = CELL_SIZE // 3
            pygame.draw.rect(screen, COLOR_TUNNEL_GLOW, (tx * CELL_SIZE + CELL_SIZE // 2 - half, ty * CELL_SIZE + offset_y + CELL_SIZE // 2 - half, half * 2, half * 2))
            half_inner = CELL_SIZE // 5
            pygame.draw.rect(screen, COLOR_TUNNEL, (tx * CELL_SIZE + CELL_SIZE // 2 - half_inner, ty * CELL_SIZE + offset_y + CELL_SIZE // 2 - half_inner, half_inner * 2, half_inner * 2))

        ex_x, ex_y = self.entry_pos
        entry_radius = CELL_SIZE // 4
        pygame.draw.circle(screen, (255, 200, 50), (ex_x * CELL_SIZE + CELL_SIZE // 2, ex_y * CELL_SIZE + offset_y + CELL_SIZE // 2), entry_radius, 3)
        pygame.draw.circle(screen, (200, 160, 20), (ex_x * CELL_SIZE + CELL_SIZE // 2, ex_y * CELL_SIZE + offset_y + CELL_SIZE // 2), entry_radius // 2)


def astar_next_step(
    maze: Maze,
    start: Tuple[int, int],
    goal: Tuple[int, int],
    blocked: Optional[Set[Tuple[int, int]]] = None,
) -> Tuple[int, int]:
    if start == goal:
        return start

    if blocked is None:
        blocked = set()

    frontier = [(0, start)]
    came_from: Dict[Tuple[int, int], Optional[Tuple[int, int]]] = {start: None}
    gscore = {start: 0}

    while frontier:
        _, current = heapq.heappop(frontier)
        if current == goal:
            break

        for d in CARDINALS:
            n = add_pos(current, d.value)
            if not maze.is_walkable(n):
                continue
            if n in blocked and n != goal:
                continue

            if n in maze.tunnels:
                exit_gates = maze.tunnels[n]
                n = random.choice(exit_gates) if isinstance(exit_gates, list) else exit_gates

            tentative = gscore[current] + 1
            if tentative < gscore.get(n, 10**9):
                gscore[n] = tentative
                f = tentative + manhattan(n, goal)
                heapq.heappush(frontier, (f, n))
                came_from[n] = current

    if goal not in came_from:
        return start

    cursor = goal
    while came_from[cursor] != start and came_from[cursor] is not None:
        cursor = came_from[cursor]
    return cursor


def astar_distance(
    maze: Maze,
    start: Tuple[int, int],
    goal: Tuple[int, int],
    blocked: Optional[Set[Tuple[int, int]]] = None,
    use_tunnels: bool = True,
) -> int:
    if start == goal:
        return 0

    if blocked is None:
        blocked = set()

    frontier = [(0, start)]
    gscore = {start: 0}

    while frontier:
        _, current = heapq.heappop(frontier)
        if current == goal:
            return gscore[current]

        for d in CARDINALS:
            n = add_pos(current, d.value)
            if not maze.is_walkable(n):
                continue
            if n in blocked and n != goal:
                continue

            if use_tunnels and n in maze.tunnels:
                exit_gates = maze.tunnels[n]
                n = random.choice(exit_gates) if isinstance(exit_gates, list) else exit_gates

            tentative = gscore[current] + 1
            if tentative < gscore.get(n, 10**9):
                gscore[n] = tentative
                f = tentative + manhattan(n, goal)
                heapq.heappush(frontier, (f, n))

    return 999
