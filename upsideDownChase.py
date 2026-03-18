"""
Upside Down: Tactical Escape
A real-time tactical game featuring Eleven vs Demogorgons
Uses Minimax AI for Demogorgons and MCTS for Eleven
"""

import pygame
import random
import math
import os
from enum import Enum
from typing import List, Tuple, Optional
import copy

# Initialize Pygame
pygame.init()

# Constants
CELL_SIZE = 64
GRID_SIZE = 14
SCREEN_WIDTH = GRID_SIZE * CELL_SIZE
SCREEN_HEIGHT = GRID_SIZE * CELL_SIZE + 60  # Extra space for HUD
FPS = 60

# Colors
COLOR_DARK_BG = (20, 15, 25)
COLOR_DARK_PURPLE = (45, 20, 60)
COLOR_AMBER = (255, 191, 0)
COLOR_AMBER_DIM = (180, 130, 0)
COLOR_BLUE = (70, 130, 200)
COLOR_RED = (180, 50, 50)
COLOR_GREY = (80, 80, 90)
COLOR_PINK = (255, 150, 180)
COLOR_WHITE = (255, 255, 255)
COLOR_SCENT = (150, 50, 50, 40)
COLOR_VINE = (60, 30, 80)
COLOR_STONE = (50, 45, 55)

# Directions
class Direction(Enum):
    NORTH = (0, -1)
    SOUTH = (0, 1)
    EAST = (1, 0)
    WEST = (-1, 0)
    NONE = (0, 0)

DIRECTION_OPPOSITES = {
    Direction.NORTH: Direction.SOUTH,
    Direction.SOUTH: Direction.NORTH,
    Direction.EAST: Direction.WEST,
    Direction.WEST: Direction.EAST,
    Direction.NONE: Direction.NONE
}


def generate_eleven_sprite(size: int = 64) -> pygame.Surface:
    """Generate Eleven sprite (top-view) - pink dress, blue jacket"""
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    center = size // 2
    
    # Blue jacket (outer layer)
    pygame.draw.ellipse(surface, (60, 100, 160), (size//4 - 4, size//3, size//2 + 8, size//2))
    
    # Pink dress (inner)
    pygame.draw.ellipse(surface, COLOR_PINK, (size//4, size//3 + 4, size//2, size//2 - 8))
    
    # Head (brown hair, top view)
    pygame.draw.circle(surface, (100, 60, 40), (center, size//3), size//5)
    
    # Face hint
    pygame.draw.circle(surface, (240, 200, 180), (center, size//3 + 2), size//8)
    
    # Arms (blue jacket sleeves)
    pygame.draw.ellipse(surface, (60, 100, 160), (size//6, size//2 - 5, size//5, size//3))
    pygame.draw.ellipse(surface, (60, 100, 160), (size - size//6 - size//5, size//2 - 5, size//5, size//3))
    
    return surface


def generate_demogorgon_sprite(size: int = 64) -> pygame.Surface:
    """Generate Demogorgon sprite (top-view) - grey creature with petal head"""
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    center = size // 2
    
    # Body (grey, hunched)
    pygame.draw.ellipse(surface, (70, 65, 75), (size//4, size//3, size//2, size//2))
    
    # Petal head - multiple petals opening outward
    petal_color = (90, 80, 85)
    inner_color = (140, 50, 60)
    num_petals = 5
    for i in range(num_petals):
        angle = (2 * math.pi * i / num_petals) - math.pi / 2
        px = center + int(math.cos(angle) * size//6)
        py = size//4 + int(math.sin(angle) * size//6)
        
        # Draw petal
        petal_points = [
            (center, size//4),
            (px - 8, py - 5),
            (px, py - 12),
            (px + 8, py - 5)
        ]
        pygame.draw.polygon(surface, petal_color, petal_points)
    
    # Inner mouth (red)
    pygame.draw.circle(surface, inner_color, (center, size//4), size//10)
    
    # Claws
    claw_color = (60, 55, 65)
    pygame.draw.polygon(surface, claw_color, [(size//5, size//2 + 10), (size//8, size - 10), (size//4, size//2 + 15)])
    pygame.draw.polygon(surface, claw_color, [(size - size//5, size//2 + 10), (size - size//8, size - 10), (size - size//4, size//2 + 15)])
    
    return surface


def generate_floor_tile(size: int = 64) -> pygame.Surface:
    """Generate dark stone floor tile with purple vines"""
    surface = pygame.Surface((size, size))
    surface.fill(COLOR_STONE)
    
    # Draw stone texture
    for _ in range(8):
        x = random.randint(0, size - 10)
        y = random.randint(0, size - 10)
        w = random.randint(8, 20)
        h = random.randint(8, 20)
        shade = random.randint(-10, 10)
        color = (COLOR_STONE[0] + shade, COLOR_STONE[1] + shade, COLOR_STONE[2] + shade)
        pygame.draw.rect(surface, color, (x, y, w, h))
    
    # Draw purple vines
    for _ in range(3):
        start_x = random.randint(0, size)
        start_y = random.randint(0, size)
        for _ in range(5):
            end_x = start_x + random.randint(-15, 15)
            end_y = start_y + random.randint(-15, 15)
            pygame.draw.line(surface, COLOR_VINE, (start_x, start_y), (end_x, end_y), 2)
            start_x, start_y = end_x, end_y
    
    return surface


def generate_portal_tile(size: int = 64) -> pygame.Surface:
    """Generate amber portal exit tile"""
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    center = size // 2
    
    # Outer glow
    for r in range(size//2, size//4, -3):
        alpha = int(100 * (1 - r / (size//2)))
        color = (*COLOR_AMBER_DIM, alpha)
        pygame.draw.circle(surface, color, (center, center), r)
    
    # Inner portal
    pygame.draw.circle(surface, COLOR_AMBER, (center, center), size//4)
    pygame.draw.circle(surface, (255, 220, 100), (center, center), size//6)
    
    # Swirl effect
    for i in range(4):
        angle = i * math.pi / 2 + pygame.time.get_ticks() / 500
        x = center + int(math.cos(angle) * size//5)
        y = center + int(math.sin(angle) * size//5)
        pygame.draw.circle(surface, (255, 240, 150), (x, y), 4)
    
    return surface


def generate_wall_tile(size: int = 64) -> pygame.Surface:
    """Generate wall tile"""
    surface = pygame.Surface((size, size))
    surface.fill(COLOR_GREY)
    
    # Add brick pattern
    brick_color = (90, 85, 95)
    for row in range(4):
        offset = (row % 2) * (size // 4)
        for col in range(3):
            x = col * (size // 2) + offset - size // 4
            y = row * (size // 4)
            pygame.draw.rect(surface, brick_color, (x + 2, y + 2, size // 2 - 4, size // 4 - 4))
    
    return surface


class Entity:
    """Base class for all game entities"""
    
    def __init__(self, x: int, y: int, lives: int = 3):
        self.x = x
        self.y = y
        self.lives = lives
        self.direction = Direction.SOUTH
        self.last_move_time = 0
        self.move_interval = 500  # ms between moves
        self.sprite: Optional[pygame.Surface] = None
        self.knockback_timer = 0
    
    def get_position(self) -> Tuple[int, int]:
        return (self.x, self.y)
    
    def set_position(self, x: int, y: int):
        self.x = x
        self.y = y
    
    def can_move(self, current_time: int) -> bool:
        if self.knockback_timer > current_time:
            return False
        return current_time - self.last_move_time >= self.move_interval
    
    def move(self, direction: Direction, maze: 'Maze', current_time: int) -> bool:
        if not self.can_move(current_time):
            return False
        
        dx, dy = direction.value
        new_x = self.x + dx
        new_y = self.y + dy
        
        if maze.is_valid_position(new_x, new_y):
            self.x = new_x
            self.y = new_y
            self.direction = direction
            self.last_move_time = current_time
            return True
        return False
    
    def draw(self, screen: pygame.Surface, offset_y: int = 0):
        if self.sprite:
            screen.blit(self.sprite, (self.x * CELL_SIZE, self.y * CELL_SIZE + offset_y))
        else:
            pygame.draw.rect(screen, COLOR_GREY, 
                           (self.x * CELL_SIZE + 8, self.y * CELL_SIZE + offset_y + 8, 
                            CELL_SIZE - 16, CELL_SIZE - 16))


class Eleven(Entity):
    """Player character controlled by MCTS AI"""
    
    def __init__(self, x: int, y: int, num_demogorgons: int = 3):
        # Health = (Number of Demogorgons * 3) - 1
        health = (num_demogorgons * 3) - 1
        super().__init__(x, y, health)
        self.move_interval = 400  # Moves every 0.4 seconds
        self.sprite = generate_eleven_sprite(CELL_SIZE)
        self.mcts_simulations = 100
    
    def draw(self, screen: pygame.Surface, offset_y: int = 0):
        if self.sprite:
            screen.blit(self.sprite, (self.x * CELL_SIZE, self.y * CELL_SIZE + offset_y))
        else:
            # Fallback: Blue rectangle
            pygame.draw.rect(screen, COLOR_BLUE, 
                           (self.x * CELL_SIZE + 8, self.y * CELL_SIZE + offset_y + 8, 
                            CELL_SIZE - 16, CELL_SIZE - 16))
    
    def get_move_mcts(self, maze: 'Maze', demogorgons: List['Demogorgon'], 
                      exits: List[Tuple[int, int]]) -> Direction:
        """
        MCTS-based movement decision.
        Simulates paths to find the safest route to the least guarded exit.
        """
        best_direction = Direction.NONE
        best_score = float('-inf')
        
        # Find the safest exit (least guarded)
        exit_scores = []
        for exit_pos in exits:
            min_demo_dist = float('inf')
            for demo in demogorgons:
                if demo.lives > 0:
                    dist = abs(demo.x - exit_pos[0]) + abs(demo.y - exit_pos[1])
                    min_demo_dist = min(min_demo_dist, dist)
            exit_scores.append((exit_pos, min_demo_dist))
        
        # Sort by safest (farthest from any demogorgon)
        exit_scores.sort(key=lambda x: -x[1])
        target_exit = exit_scores[0][0] if exit_scores else exits[0]
        
        # MCTS Simulation placeholder
        possible_moves = [Direction.NORTH, Direction.SOUTH, Direction.EAST, Direction.WEST]
        
        for direction in possible_moves:
            dx, dy = direction.value
            new_x = self.x + dx
            new_y = self.y + dy
            
            if not maze.is_valid_position(new_x, new_y):
                continue
            
            # Simulate multiple random rollouts
            total_score = 0
            for _ in range(self.mcts_simulations // len(possible_moves)):
                score = self._simulate_rollout(new_x, new_y, target_exit, 
                                               demogorgons, maze, depth=10)
                total_score += score
            
            avg_score = total_score / max(1, self.mcts_simulations // len(possible_moves))
            
            if avg_score > best_score:
                best_score = avg_score
                best_direction = direction
        
        return best_direction
    
    def _simulate_rollout(self, start_x: int, start_y: int, target: Tuple[int, int],
                          demogorgons: List['Demogorgon'], maze: 'Maze', 
                          depth: int) -> float:
        """Simulate a random rollout from position to estimate value"""
        x, y = start_x, start_y
        score = 0
        
        for step in range(depth):
            # Check if reached exit
            if (x, y) == target:
                score += 100 - step * 2  # Bonus for reaching quickly
                break
            
            # Penalty for being near demogorgons
            for demo in demogorgons:
                if demo.lives > 0:
                    dist = abs(demo.x - x) + abs(demo.y - y)
                    if dist <= 2:
                        score -= (3 - dist) * 10
                    if dist == 0:
                        score -= 50  # Collision penalty
            
            # Move towards target with some randomness
            dx = 1 if target[0] > x else (-1 if target[0] < x else 0)
            dy = 1 if target[1] > y else (-1 if target[1] < y else 0)
            
            # Add randomness
            if random.random() < 0.3:
                dx = random.choice([-1, 0, 1])
                dy = random.choice([-1, 0, 1])
            
            new_x, new_y = x + dx, y + dy
            if maze.is_valid_position(new_x, new_y):
                x, y = new_x, new_y
        
        # Final distance to target
        final_dist = abs(x - target[0]) + abs(y - target[1])
        score -= final_dist * 2
        
        return score


class Demogorgon(Entity):
    """Enemy controlled by Minimax AI"""
    
    def __init__(self, x: int, y: int):
        super().__init__(x, y, lives=3)
        self.move_interval = 600  # Moves every 0.6 seconds
        self.sprite = generate_demogorgon_sprite(CELL_SIZE)
        self.detection_radius = 4
        self.patrol_target: Optional[Tuple[int, int]] = None
        self.scent_pulse = 0
    
    def draw(self, screen: pygame.Surface, offset_y: int = 0):
        # Draw scent radius (detection zone)
        self._draw_scent(screen, offset_y)
        
        if self.sprite:
            screen.blit(self.sprite, (self.x * CELL_SIZE, self.y * CELL_SIZE + offset_y))
        else:
            # Fallback: Red rectangle
            pygame.draw.rect(screen, COLOR_RED, 
                           (self.x * CELL_SIZE + 8, self.y * CELL_SIZE + offset_y + 8, 
                            CELL_SIZE - 16, CELL_SIZE - 16))
    
    def _draw_scent(self, screen: pygame.Surface, offset_y: int):
        """Draw pulsing scent radius"""
        if self.lives <= 0:
            return
            
        self.scent_pulse = (self.scent_pulse + 2) % 60
        pulse_factor = 0.8 + 0.2 * math.sin(self.scent_pulse * math.pi / 30)
        
        center_x = self.x * CELL_SIZE + CELL_SIZE // 2
        center_y = self.y * CELL_SIZE + offset_y + CELL_SIZE // 2
        radius = int(self.detection_radius * CELL_SIZE * 0.35 * pulse_factor)
        
        # Create transparent surface for scent
        scent_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(scent_surface, (150, 50, 50, 30), (radius, radius), radius)
        pygame.draw.circle(scent_surface, (180, 60, 60, 20), (radius, radius), int(radius * 0.7))
        
        screen.blit(scent_surface, (center_x - radius, center_y - radius))
    
    def get_distance_to(self, x: int, y: int) -> int:
        """Manhattan distance to a position"""
        return abs(self.x - x) + abs(self.y - y)
    
    def can_detect(self, eleven: Eleven) -> bool:
        """Check if Eleven is within detection radius"""
        return self.get_distance_to(eleven.x, eleven.y) <= self.detection_radius
    
    def get_move_minimax(self, eleven: Eleven, maze: 'Maze', 
                         exits: List[Tuple[int, int]], other_demos: List['Demogorgon']) -> Direction:
        """
        Minimax-based movement decision.
        If Eleven is within range, prioritize blocking path to nearest exit.
        Otherwise, patrol exits.
        """
        if self.lives <= 0:
            return Direction.NONE
        
        # Check if Eleven is within detection range
        if self.can_detect(eleven):
            return self._minimax_chase(eleven, maze, exits, depth=3)
        else:
            return self._patrol_exits(maze, exits)
    
    def _minimax_chase(self, eleven: Eleven, maze: 'Maze', 
                       exits: List[Tuple[int, int]], depth: int) -> Direction:
        """
        Minimax algorithm to block Eleven's path to exits.
        Demogorgon is minimizing (blocking), simulating Eleven maximizing (escaping).
        """
        # Find nearest exit to Eleven
        nearest_exit = min(exits, key=lambda e: abs(e[0] - eleven.x) + abs(e[1] - eleven.y))
        
        best_direction = Direction.NONE
        best_score = float('inf')  # Minimizing
        
        possible_moves = [Direction.NORTH, Direction.SOUTH, Direction.EAST, Direction.WEST]
        
        for direction in possible_moves:
            dx, dy = direction.value
            new_x = self.x + dx
            new_y = self.y + dy
            
            if not maze.is_valid_position(new_x, new_y):
                continue
            
            # Calculate score based on blocking effectiveness
            score = self._evaluate_blocking_position(new_x, new_y, eleven, nearest_exit)
            
            # Minimax recursion (simplified)
            if depth > 0:
                # Simulate Eleven's response
                eleven_best = self._simulate_eleven_response(new_x, new_y, eleven, 
                                                            nearest_exit, maze, depth - 1)
                score += eleven_best * 0.5
            
            if score < best_score:
                best_score = score
                best_direction = direction
        
        return best_direction
    
    def _evaluate_blocking_position(self, demo_x: int, demo_y: int, 
                                    eleven: Eleven, exit_pos: Tuple[int, int]) -> float:
        """Evaluate how well a position blocks Eleven from the exit"""
        # Distance from demogorgon to the line between Eleven and exit
        eleven_to_exit_x = exit_pos[0] - eleven.x
        eleven_to_exit_y = exit_pos[1] - eleven.y
        
        # Ideal blocking position is between Eleven and exit
        midpoint_x = (eleven.x + exit_pos[0]) / 2
        midpoint_y = (eleven.y + exit_pos[1]) / 2
        
        dist_to_midpoint = abs(demo_x - midpoint_x) + abs(demo_y - midpoint_y)
        dist_to_eleven = abs(demo_x - eleven.x) + abs(demo_y - eleven.y)
        
        # Lower score is better for blocking
        score = dist_to_midpoint * 2 + dist_to_eleven
        
        return score
    
    def _simulate_eleven_response(self, demo_x: int, demo_y: int, eleven: Eleven,
                                  exit_pos: Tuple[int, int], maze: 'Maze', 
                                  depth: int) -> float:
        """Simulate Eleven's optimal response (maximizing escape potential)"""
        best_score = float('-inf')
        
        for direction in [Direction.NORTH, Direction.SOUTH, Direction.EAST, Direction.WEST]:
            dx, dy = direction.value
            new_x = eleven.x + dx
            new_y = eleven.y + dy
            
            if not maze.is_valid_position(new_x, new_y):
                continue
            
            # Score: distance to exit (lower is better for Eleven, higher for us)
            dist_to_exit = abs(new_x - exit_pos[0]) + abs(new_y - exit_pos[1])
            dist_to_demo = abs(new_x - demo_x) + abs(new_y - demo_y)
            
            score = -dist_to_exit + dist_to_demo * 0.5
            best_score = max(best_score, score)
        
        return -best_score  # Negate because we want to minimize Eleven's advantage
    
    def _patrol_exits(self, maze: 'Maze', exits: List[Tuple[int, int]]) -> Direction:
        """Patrol between exits when Eleven is not detected"""
        # Pick a patrol target if none or reached
        if self.patrol_target is None or (self.x, self.y) == self.patrol_target:
            self.patrol_target = random.choice(exits)
        
        # Move towards patrol target
        target_x, target_y = self.patrol_target
        
        best_direction = Direction.NONE
        best_dist = float('inf')
        
        for direction in [Direction.NORTH, Direction.SOUTH, Direction.EAST, Direction.WEST]:
            dx, dy = direction.value
            new_x = self.x + dx
            new_y = self.y + dy
            
            if maze.is_valid_position(new_x, new_y):
                dist = abs(new_x - target_x) + abs(new_y - target_y)
                if dist < best_dist:
                    best_dist = dist
                    best_direction = direction
        
        return best_direction


class Maze:
    """Game environment with walls and exits"""
    
    def __init__(self, width: int = GRID_SIZE, height: int = GRID_SIZE):
        self.width = width
        self.height = height
        self.walls: List[Tuple[int, int]] = []
        self.exits: List[Tuple[int, int]] = []
        self.floor_tile = generate_floor_tile(CELL_SIZE)
        self.wall_tile = generate_wall_tile(CELL_SIZE)
        self.portal_frame = 0
        
        self._generate_maze()
    
    def _generate_maze(self):
        """Generate maze with walls and exits"""
        # Create border walls
        for x in range(self.width):
            self.walls.append((x, 0))
            self.walls.append((x, self.height - 1))
        for y in range(1, self.height - 1):
            self.walls.append((0, y))
            self.walls.append((self.width - 1, y))
        
        # Add some internal walls for cover
        internal_walls = [
            # Central obstacles
            (5, 5), (5, 6), (5, 7),
            (8, 5), (8, 6), (8, 7),
            (6, 8), (7, 8),
            
            # Corner covers
            (3, 3), (3, 4),
            (10, 3), (10, 4),
            (3, 10), (4, 10),
            (10, 10), (9, 10),
            
            # Additional obstacles
            (7, 3), (6, 3),
            (7, 11), (6, 11),
        ]
        
        for wall in internal_walls:
            if wall not in self.walls:
                self.walls.append(wall)
        
        # Place 3 exits at different edges (remove wall at exit positions)
        exit_positions = [
            (self.width // 2, 0),           # Top center
            (0, self.height // 2),          # Left center
            (self.width - 1, self.height // 2)  # Right center
        ]
        
        for exit_pos in exit_positions:
            if exit_pos in self.walls:
                self.walls.remove(exit_pos)
            self.exits.append(exit_pos)
    
    def is_valid_position(self, x: int, y: int) -> bool:
        """Check if position is within bounds and not a wall"""
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return False
        return (x, y) not in self.walls
    
    def is_exit(self, x: int, y: int) -> bool:
        """Check if position is an exit"""
        return (x, y) in self.exits
    
    def draw(self, screen: pygame.Surface, offset_y: int = 0):
        """Draw the maze"""
        self.portal_frame += 1
        
        # Draw floor tiles
        for x in range(self.width):
            for y in range(self.height):
                screen.blit(self.floor_tile, (x * CELL_SIZE, y * CELL_SIZE + offset_y))
        
        # Draw walls
        for wall_x, wall_y in self.walls:
            screen.blit(self.wall_tile, (wall_x * CELL_SIZE, wall_y * CELL_SIZE + offset_y))
        
        # Draw exits (amber portals)
        for exit_x, exit_y in self.exits:
            portal = generate_portal_tile(CELL_SIZE)
            screen.blit(portal, (exit_x * CELL_SIZE, exit_y * CELL_SIZE + offset_y))


class Game:
    """Main game class managing all game logic"""
    
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Upside Down: Tactical Escape")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 32)
        self.small_font = pygame.font.Font(None, 24)
        
        self.maze = Maze()
        self.num_demogorgons = 3
        
        # Place Eleven in center
        self.eleven = Eleven(GRID_SIZE // 2, GRID_SIZE // 2, self.num_demogorgons)
        
        # Place Demogorgons
        self.demogorgons: List[Demogorgon] = []
        demo_positions = [(2, 2), (11, 2), (6, 11)]
        for pos in demo_positions:
            demo = Demogorgon(pos[0], pos[1])
            self.demogorgons.append(demo)
        
        self.running = True
        self.game_over = False
        self.victory = False
        self.hud_height = 60
        
        # Message system
        self.message = ""
        self.message_timer = 0
    
    def show_message(self, msg: str, duration: int = 2000):
        """Display a temporary message"""
        self.message = msg
        self.message_timer = pygame.time.get_ticks() + duration
    
    def handle_combat(self, current_time: int):
        """Handle combat between Eleven and Demogorgons"""
        for demo in self.demogorgons:
            if demo.lives <= 0:
                continue
            
            # Check if same tile
            if self.eleven.x == demo.x and self.eleven.y == demo.y:
                # Determine attack direction
                eleven_approach = self.eleven.direction
                demo_facing = demo.direction
                
                # Check if Eleven attacked from behind
                is_backstab = (eleven_approach == DIRECTION_OPPOSITES.get(demo_facing, Direction.NONE))
                
                if is_backstab:
                    # Eleven stabs demogorgon from behind
                    demo.lives -= 1
                    self.show_message(f"Backstab! Demogorgon hurt ({demo.lives} lives left)")
                    
                    # Push Eleven back
                    dx, dy = DIRECTION_OPPOSITES[eleven_approach].value
                    new_x = self.eleven.x + dx
                    new_y = self.eleven.y + dy
                    if self.maze.is_valid_position(new_x, new_y):
                        self.eleven.x = new_x
                        self.eleven.y = new_y
                else:
                    # Demogorgon attacks Eleven (frontal assault)
                    self.eleven.lives -= 1
                    self.show_message(f"Attacked! Eleven hurt ({self.eleven.lives} lives left)")
                    
                    # Knockback Eleven
                    dx, dy = demo.direction.value
                    new_x = self.eleven.x + dx
                    new_y = self.eleven.y + dy
                    if self.maze.is_valid_position(new_x, new_y):
                        self.eleven.x = new_x
                        self.eleven.y = new_y
                    self.eleven.knockback_timer = current_time + 500
    
    def check_win_conditions(self):
        """Check if game is won or lost"""
        # Check if Eleven reached an exit
        if self.maze.is_exit(self.eleven.x, self.eleven.y):
            self.victory = True
            self.game_over = True
            return
        
        # Check if Eleven is dead
        if self.eleven.lives <= 0:
            self.victory = False
            self.game_over = True
            return
        
        # Check if all demogorgons defeated
        alive_demos = sum(1 for d in self.demogorgons if d.lives > 0)
        if alive_demos == 0:
            self.victory = True
            self.game_over = True
    
    def update(self):
        """Update game state"""
        if self.game_over:
            return
        
        current_time = pygame.time.get_ticks()
        
        # Update Eleven (MCTS AI)
        if self.eleven.can_move(current_time):
            direction = self.eleven.get_move_mcts(self.maze, self.demogorgons, self.maze.exits)
            self.eleven.move(direction, self.maze, current_time)
        
        # Update Demogorgons (Minimax AI)
        for demo in self.demogorgons:
            if demo.lives > 0 and demo.can_move(current_time):
                other_demos = [d for d in self.demogorgons if d != demo and d.lives > 0]
                direction = demo.get_move_minimax(self.eleven, self.maze, 
                                                  self.maze.exits, other_demos)
                demo.move(direction, self.maze, current_time)
        
        # Handle combat
        self.handle_combat(current_time)
        
        # Check win conditions
        self.check_win_conditions()
    
    def draw_hud(self):
        """Draw heads-up display"""
        hud_rect = pygame.Rect(0, 0, SCREEN_WIDTH, self.hud_height)
        pygame.draw.rect(self.screen, (30, 25, 35), hud_rect)
        pygame.draw.line(self.screen, COLOR_AMBER_DIM, (0, self.hud_height - 2), 
                        (SCREEN_WIDTH, self.hud_height - 2), 2)
        
        # Eleven's health
        health_text = f"Eleven HP: {self.eleven.lives}"
        health_surface = self.font.render(health_text, True, COLOR_PINK)
        self.screen.blit(health_surface, (20, 15))
        
        # Health bar
        bar_x = 160
        bar_width = 150
        bar_height = 20
        max_health = (self.num_demogorgons * 3) - 1
        health_ratio = max(0, self.eleven.lives / max_health)
        
        pygame.draw.rect(self.screen, (60, 50, 70), (bar_x, 18, bar_width, bar_height))
        pygame.draw.rect(self.screen, COLOR_PINK, (bar_x, 18, int(bar_width * health_ratio), bar_height))
        pygame.draw.rect(self.screen, COLOR_WHITE, (bar_x, 18, bar_width, bar_height), 2)
        
        # Demogorgon count
        alive_demos = sum(1 for d in self.demogorgons if d.lives > 0)
        demo_text = f"Demogorgons: {alive_demos}/{self.num_demogorgons}"
        demo_surface = self.font.render(demo_text, True, COLOR_RED)
        self.screen.blit(demo_surface, (SCREEN_WIDTH - 220, 15))
        
        # Message display
        current_time = pygame.time.get_ticks()
        if self.message and current_time < self.message_timer:
            msg_surface = self.small_font.render(self.message, True, COLOR_AMBER)
            msg_rect = msg_surface.get_rect(center=(SCREEN_WIDTH // 2, 40))
            self.screen.blit(msg_surface, msg_rect)
    
    def draw_game_over(self):
        """Draw game over screen"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        if self.victory:
            text = "ESCAPED!"
            color = COLOR_AMBER
        else:
            text = "CAPTURED..."
            color = COLOR_RED
        
        text_surface = pygame.font.Font(None, 64).render(text, True, color)
        text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(text_surface, text_rect)
        
        restart_text = "Press R to Restart or Q to Quit"
        restart_surface = self.font.render(restart_text, True, COLOR_WHITE)
        restart_rect = restart_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
        self.screen.blit(restart_surface, restart_rect)
    
    def draw(self):
        """Render the game"""
        self.screen.fill(COLOR_DARK_BG)
        
        # Draw HUD
        self.draw_hud()
        
        # Draw maze
        self.maze.draw(self.screen, self.hud_height)
        
        # Draw demogorgons
        for demo in self.demogorgons:
            if demo.lives > 0:
                demo.draw(self.screen, self.hud_height)
        
        # Draw Eleven
        self.eleven.draw(self.screen, self.hud_height)
        
        # Draw game over screen if needed
        if self.game_over:
            self.draw_game_over()
        
        pygame.display.flip()
    
    def reset(self):
        """Reset the game"""
        self.maze = Maze()
        self.eleven = Eleven(GRID_SIZE // 2, GRID_SIZE // 2, self.num_demogorgons)
        
        self.demogorgons = []
        demo_positions = [(2, 2), (11, 2), (6, 11)]
        for pos in demo_positions:
            demo = Demogorgon(pos[0], pos[1])
            self.demogorgons.append(demo)
        
        self.game_over = False
        self.victory = False
        self.message = ""
        self.message_timer = 0
    
    def run(self):
        """Main game loop"""
        while self.running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_r and self.game_over:
                        self.reset()
                    elif event.key == pygame.K_q and self.game_over:
                        self.running = False
            
            # Update
            self.update()
            
            # Draw
            self.draw()
            
            # Control frame rate
            self.clock.tick(FPS)
        
        pygame.quit()


def main():
    """Entry point"""
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
