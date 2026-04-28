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


# ---------------------------------------------------------
# NEW PROCEDURAL BACKGROUND GENERATOR (NO IMAGES NEEDED)
# ---------------------------------------------------------


def generate_floor_tile(size: int = 50) -> pygame.Surface:
    """Draws a stone floor with creepy dark vines crawling over it."""
    # 1. Create a blank canvas for our floor tile
    surface = pygame.Surface((size, size))
    
    # 2. Fill it with a dark, greenish-grey stone color
    base_color = (65, 70, 65)
    surface.fill(base_color)
    
    # 3. Draw a grid of smaller stones inside this tile to match your picture
    stone_size = size // 3
    for x in range(0, size, stone_size):
        for y in range(0, size, stone_size):
            # Draw the square stone
            stone_rect = (x, y, stone_size, stone_size)
            pygame.draw.rect(surface, (75, 80, 75), stone_rect)
            # Draw a dark outline around the stone to make it look like cracks
            pygame.draw.rect(surface, (40, 45, 40), stone_rect, 2)
            
    # 4. Draw creepy Upside Down vines (dark curvy lines)
    # We will draw 2 to 4 random vines per tile
    num_vines = random.randint(2, 4)
    for _ in range(num_vines):
        # Pick a random starting point and ending point for the vine
        start_x, start_y = random.randint(0, size), random.randint(0, size)
        end_x, end_y = random.randint(0, size), random.randint(0, size)
        
        # Pick a random middle point so the vine curves and looks organic
        mid_x = (start_x + end_x) // 2 + random.randint(-15, 15)
        mid_y = (start_y + end_y) // 2 + random.randint(-15, 15)
        
        # Draw the dark, thick vine
        vine_color = (30, 20, 25) # Very dark purplish-black
        pygame.draw.line(surface, vine_color, (start_x, start_y), (mid_x, mid_y), 3)
        pygame.draw.line(surface, vine_color, (mid_x, mid_y), (end_x, end_y), 3)

    return surface


def generate_wall_tile(size: int = 50) -> pygame.Surface:
    """Draws a wall that looks raised and 3D using light and shadow tricks."""
    surface = pygame.Surface((size, size))
    
    # 1. Base color of the wall (Grey)
    wall_color = (90, 95, 100)
    surface.fill(wall_color)
    
    # 2. Fake 3D Effect (Beveling)
    # We draw a bright line on the top and left (where the light hits)
    # We draw a dark line on the bottom and right (where the shadow falls)
    light_color = (130, 135, 140)
    shadow_color = (40, 45, 50)
    
    # Top edge (Light)
    pygame.draw.rect(surface, light_color, (0, 0, size, 4))
    # Left edge (Light)
    pygame.draw.rect(surface, light_color, (0, 0, 4, size))
    # Bottom edge (Shadow)
    pygame.draw.rect(surface, shadow_color, (0, size - 4, size, 4))
    # Right edge (Shadow)
    pygame.draw.rect(surface, shadow_color, (size - 4, 0, 4, size))
    
    # 3. Add a glowing light to a few random walls (like in your picture!)
    # There is a 1-in-10 chance a wall will have a glowing yellow light
    if random.randint(1, 10) == 1:
        # Draw the metal light fixture
        fixture_rect = (size // 4, size // 4, size // 2, 8)
        pygame.draw.rect(surface, (50, 40, 20), fixture_rect)
        
        # Draw the bright orange/yellow glow
        glow_rect = (size // 4 + 2, size // 4 + 2, size // 2 - 4, 4)
        pygame.draw.rect(surface, (255, 180, 50), glow_rect)

    return surface

class Maze:
    def __init__(self, size: int = GRID_SIZE):
        self.size = size
        self.walls: Set[Tuple[int, int]] = set()
        # Support multiple exit doors
        self.exit_positions: Set[Tuple[int, int]] = set()
        # Backwards-compatible single exit property (first exit)
        self.exit_pos: Tuple[int, int] = (size - 1, size // 2)
        self.entry_pos: Tuple[int, int] = (0, 0)
        self.tunnels: Dict[Tuple[int, int], Tuple[int, int]] = {}
        self.unlocked_exits: Set[Tuple[int, int]] = set()

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

        # Choose multiple exits (2-4) if possible
        num_exits = min(len(candidates), random.randint(2, 4)) if candidates else 1
        chosen = random.sample(candidates, num_exits) if candidates else [(self.size - 1, self.size // 2)]
        self.exit_positions = set(chosen)
        # Keep a single convenience attribute for compatibility
        self.exit_pos = next(iter(self.exit_positions))
        for e in self.exit_positions:
            self.walls.discard(e)

    def is_exit(self, x: int, y: int) -> bool:
        """Return True if (x,y) is one of the exit doors."""
        return (x, y) in self.exit_positions

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
            # Deterministic tunnel choice (first gate) to make behavior
            # reproducible for planning and simulation.
            return exit_gates[0] if isinstance(exit_gates, list) else exit_gates
        return nxt

    def draw(self, screen: pygame.Surface, offset_y: int, has_key: bool, hud_height: int):
        for x in range(self.size):
            for y in range(self.size):
                screen.blit(self.floor_tile, (x * CELL_SIZE, y * CELL_SIZE + offset_y))

        for x, y in self.walls:
            screen.blit(self.wall_tile, (x * CELL_SIZE, y * CELL_SIZE + offset_y))

        # Draw all exit doors
        for ex, ey in self.exit_positions:
            color = COLOR_EXIT if (ex, ey) in getattr(self, "unlocked_exits", set()) else COLOR_EXIT_LOCKED
            x_pos = ex * CELL_SIZE + 12
            y_pos = ey * CELL_SIZE + offset_y + 16
            door_w = CELL_SIZE - 24
            door_h = CELL_SIZE - 24
            pygame.draw.rect(screen, color, (x_pos, y_pos, door_w, door_h))
            pygame.draw.arc(screen, color, (x_pos, y_pos - door_h // 3, door_w, door_h), 3.14, 6.28, 3)

        for t_in, _ in self.tunnels.items():
            tx, ty = t_in
            # Draw tunnel portals as small diamond shapes instead of big boxes
            cx = tx * CELL_SIZE + CELL_SIZE // 2
            cy = ty * CELL_SIZE + offset_y + CELL_SIZE // 2
            # Outer glow diamond
            r = CELL_SIZE // 4
            pygame.draw.polygon(screen, COLOR_TUNNEL_GLOW, [
                (cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)
            ])
            # Inner solid diamond
            ri = CELL_SIZE // 6
            pygame.draw.polygon(screen, COLOR_TUNNEL, [
                (cx, cy - ri), (cx + ri, cy), (cx, cy + ri), (cx - ri, cy)
            ])

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
                # Use a deterministic tunnel exit for pathfinding to make search stable
                n = exit_gates[0] if isinstance(exit_gates, list) else exit_gates

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
                # Deterministic choice for A* to keep planning reproducible
                n = exit_gates[0] if isinstance(exit_gates, list) else exit_gates

            tentative = gscore[current] + 1
            if tentative < gscore.get(n, 10**9):
                gscore[n] = tentative
                f = tentative + manhattan(n, goal)
                heapq.heappush(frontier, (f, n))

    return 999
