"""Main game class and logic."""

import math
import os  # We need 'os' to build file paths for loading images and fonts
import random  # Used for placing characters and items at random spots
from array import array
from typing import List, Optional, Set, Tuple

import pygame

from entities import CARDINALS, Direction, OPPOSITE, Snapshot, add_pos, direction_between, manhattan, AgentState
from maze import CELL_SIZE, GRID_SIZE, Maze, astar_distance
from ai.mcts import mcts_action
from ai.minimax import best_demo_move


# Constants
HUD_HEIGHT = 90
SCREEN_WIDTH = GRID_SIZE * CELL_SIZE
SCREEN_HEIGHT = GRID_SIZE * CELL_SIZE + HUD_HEIGHT
FPS = 60
TURN_DELAY_MS = 150

TOTAL_COINS = 3
NUM_DEMOGORGONS = 3
TIME_LIMIT_MS = 5 * 60 * 1000
DETECTION_RADIUS = 4
SHOOT_COOLDOWN_MS = 2 * 60 * 1000
MAX_SHOOTS = 2

# Colors
COLOR_BG = (18, 14, 22)
COLOR_HUD = (28, 24, 35)
COLOR_TEXT = (235, 225, 235)
COLOR_EXIT = (240, 175, 45)
COLOR_COIN = (255, 220, 85)
COLOR_KEY = (255, 245, 140)
COLOR_ELEVEN = (235, 150, 185)
COLOR_DEMOGORGON = (170, 70, 85)
COLOR_DETECTION = (155, 60, 70, 45)
COLOR_DETECTION_INNER = (190, 70, 80, 25)


def build_encounter_sound() -> Optional[pygame.mixer.Sound]:
    """Generate procedural creepy encounter sound."""
    if pygame.mixer.get_init() is None:
        return None

    sample_rate = 22050
    duration = 0.35
    total = int(sample_rate * duration)
    tone = array("h")

    for i in range(total):
        t = i / sample_rate
        carrier = math.sin(2 * math.pi * 180 * t)
        low = math.sin(2 * math.pi * 55 * t)
        wobble = math.sin(2 * math.pi * 2.5 * t)
        val = (carrier * 0.45 + low * 0.35 + wobble * 0.2)
        fade = 1.0 - (i / total)
        tone.append(int(max(-1.0, min(1.0, val)) * 12000 * fade))

    try:
        return pygame.mixer.Sound(buffer=tone.tobytes())
    except pygame.error:
        return None


# ---------------------------------------------------------
# NEW DRAWN CHARACTERS (FUNKO POP STYLE!)
# ---------------------------------------------------------

def generate_eleven_sprite(size: int = 50) -> pygame.Surface:
    """Draws a cute Eleven with a big head, pink dress, and blue jacket."""
    # 1. We make a clear glass box to draw Eleven inside.
    # pygame.SRCALPHA makes the background invisible so she isn't in a black square!
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    
    # 2. Draw her little body first (bottom half)
    # The dress is a pink triangle shape (a polygon)
    pink = (240, 160, 180)
    pygame.draw.polygon(s, pink, [(size//3, size//2), (size*2//3, size//2), (size*3//4, size-10), (size//4, size-10)])
    
    # 3. Draw her blue jacket over the dress
    blue = (30, 80, 120)
    # Left side of jacket
    pygame.draw.rect(s, blue, (size//4, size//2, size//6, size//3))
    # Right side of jacket
    pygame.draw.rect(s, blue, (size*7//12, size//2, size//6, size//3))
    
    # 4. Draw her giant Funko Pop head!
    skin_color = (255, 220, 200)
    pygame.draw.ellipse(s, skin_color, (size//6, size//10, size*2//3, size*3//5))
    
    # 5. Draw her short dark hair on top of her head
    # We use an 'arc' which is like a rainbow shape
    hair_color = (50, 40, 40)
    pygame.draw.arc(s, hair_color, (size//6, size//10, size*2//3, size*3//5), 0, 3.14, int(size//6))
    
    # 6. Draw her big big eyes
    # First the white part...
    pygame.draw.circle(s, (255, 255, 255), (size*2//5, size*4//10), size//8)
    pygame.draw.circle(s, (255, 255, 255), (size*3//5, size*4//10), size//8)
    # Then the brown part inside!
    pygame.draw.circle(s, (60, 40, 30), (size*2//5, size*4//10), size//12)
    pygame.draw.circle(s, (60, 40, 30), (size*3//5, size*4//10), size//12)
    
    return s


def generate_demogorgon_sprite(size: int = 50) -> pygame.Surface:
    """Draws a creepy Demogorgon with 5 red petals for a face."""
    # 1. Make our clear glass box again
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    center = size // 2
    
    # 2. Draw a skinny grey body
    grey = (120, 110, 115)
    pygame.draw.ellipse(s, grey, (size*2//5, size//3, size//5, size//2))
    
    # 3. Draw skinny arms
    pygame.draw.line(s, grey, (size*2//5, size//2), (size//4, size*2//3), 3)
    pygame.draw.line(s, grey, (size*3//5, size//2), (size*3//4, size*2//3), 3)
    
    # 4. Draw the scary flower face (5 petals)
    petals = 5
    for i in range(petals):
        # This math helps us put the petals in a circle, like pieces of a pizza!
        angle = (2 * math.pi * i / petals) - math.pi / 2
        px = center + int(math.cos(angle) * size // 2.5)
        py = size // 3 + int(math.sin(angle) * size // 2.5)
        
        # Draw a red triangle for each petal
        red = (160, 50, 50)
        pygame.draw.polygon(s, red, [(center, size//3), (px - 6, py - 6), (px, py), (px + 6, py - 6)])
    
    # 5. Draw the dark black mouth right in the middle
    pygame.draw.circle(s, (20, 15, 20), (center, size//3), size//6)
    
    return s


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Upside Down: Tactical Escape")
        self.clock = pygame.time.Clock()

        # --- Custom Font Loading ---
        font_path = os.path.join(os.path.dirname(__file__), "benguiat.ttf")
        try:
            self.font = pygame.font.Font(font_path, 30)
            self.small_font = pygame.font.Font(font_path, 22)
        except FileNotFoundError:
            self.font = pygame.font.Font(None, 30)
            self.small_font = pygame.font.Font(None, 22)

        # Load character sprites
        self.eleven_sprite = generate_eleven_sprite()
        self.demo_sprite = generate_demogorgon_sprite()

        # ---------------------------------------------------------
        # BACKGROUND PICTURE LOADING
        # ---------------------------------------------------------
        board_path = os.path.join(os.path.dirname(__file__), "Board.png")
        try:
            board_image = pygame.image.load(board_path).convert()
            
            # Picture 1 for the Game: We make it a little shorter so it fits under the HUD
            self.board_bg = pygame.transform.scale(board_image, (SCREEN_WIDTH, SCREEN_HEIGHT - HUD_HEIGHT))
            
            # Picture 2 for the Menu: We stretch it to cover the entire full screen!
            self.menu_bg = pygame.transform.scale(board_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except FileNotFoundError:
            # If the picture is missing, make fake black backgrounds so it doesn't crash
            self.board_bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT - HUD_HEIGHT))
            self.board_bg.fill((0, 0, 0))
            self.menu_bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            self.menu_bg.fill((0, 0, 0))

        self.encounter_sound = build_encounter_sound()
        self.encounter_channel: Optional[pygame.mixer.Channel] = None
        self.encounter_active = False

        self.running = True
        self.last_action_tick = pygame.time.get_ticks()

        self.message = ""
        self.message_until = 0

        # This tells the game to pause on the home screen when it first opens
        self.in_menu = True 

        self.reset()

    def reset(self):
        """Reset game to initial state."""
        self.maze = Maze(GRID_SIZE)
        self.last_action_tick = pygame.time.get_ticks()

        floor = [
            (x, y)
            for x in range(1, GRID_SIZE - 1)
            for y in range(1, GRID_SIZE - 1)
            if self.maze.is_walkable((x, y)) and not self.maze.is_exit(x, y) and (x, y) not in self.maze.tunnels
        ]

        self.eleven = AgentState(*random.choice(floor), Direction.SOUTH, hp=(NUM_DEMOGORGONS * 3 - 1))
        self.maze.entry_pos = self.eleven.pos()

        self.demogorgons: List[AgentState] = []
        random.shuffle(floor)
        for cell in floor:
            if manhattan(cell, self.eleven.pos()) >= 5:
                self.demogorgons.append(AgentState(cell[0], cell[1], Direction.NORTH, hp=3))
            if len(self.demogorgons) >= NUM_DEMOGORGONS:
                break

        available = [p for p in floor if p != self.eleven.pos() and all((d.x, d.y) != p for d in self.demogorgons)]
        random.shuffle(available)

        self.coins: Set[Tuple[int, int]] = set(available[:TOTAL_COINS])
        self.key_pos = available[TOTAL_COINS] if len(available) > TOTAL_COINS else random.choice(available)
        self.has_key = False

        self.game_start_time = pygame.time.get_ticks()
        self.turns_left = 0
        self.points = 0
        self.last_shoot_time = self.game_start_time
        self.shoots_used = 0
        self.game_over = False
        self.victory = False
        self.winner = ""
        self.show_message("AI vs AI started: Eleven must collect all coins, key, then escape")
        
        # ---------------------------------------------------------
        # NEW CODE: HIDING THE KEY
        # ---------------------------------------------------------
        self.has_key = False # Eleven starts with NO key!
        while True:
            # Pick a random X and Y square on the map (use Maze.size)
            rx = random.randint(1, self.maze.size - 2)
            ry = random.randint(1, self.maze.size - 2)
            pos = (rx, ry)

            # Make sure the key is NOT inside a wall, and NOT on top of any exit door
            if self.maze.is_walkable(pos) and not self.maze.is_exit(rx, ry):
                self.key_pos = pos  # Save the safe hiding spot!
                break

    def show_message(self, text: str, ms: int = 1800):
        """Display a temporary message."""
        self.message = text
        self.message_until = pygame.time.get_ticks() + ms

    def snapshot(self) -> Snapshot:
        """Create a game state snapshot."""
        return Snapshot(
            eleven=AgentState(self.eleven.x, self.eleven.y, self.eleven.direction, self.eleven.hp),
            demogorgons=[AgentState(d.x, d.y, d.direction, d.hp) for d in self.demogorgons],
            coins=set(self.coins),
            key_pos=self.key_pos,
            has_key=self.has_key,
            unlocked_exits=set(getattr(self.maze, "unlocked_exits", set())),
            turns_left=self.turns_left,
            points=self.points,
            last_shoot_time=self.last_shoot_time,
        )

    def apply_snapshot(self, snap: Snapshot):
        """Apply a snapshot to game state."""
        self.eleven = snap.eleven
        self.demogorgons = snap.demogorgons
        self.coins = set(snap.coins)
        self.key_pos = snap.key_pos
        self.has_key = snap.has_key
        # Restore unlocked exits into the maze if present in the snapshot
        if getattr(snap, "unlocked_exits", None) is not None:
            self.maze.unlocked_exits = set(snap.unlocked_exits)
        self.turns_left = snap.turns_left
        self.points = snap.points
        self.last_shoot_time = snap.last_shoot_time

    def is_terminal(self, snap: Snapshot) -> bool:
        """Check if game state is terminal."""
        elapsed = pygame.time.get_ticks() - self.game_start_time
        if elapsed >= TIME_LIMIT_MS or snap.eleven.hp <= 0:
            return True
        if snap.has_key and len(snap.coins) == 0 and self.maze.is_exit(snap.eleven.x, snap.eleven.y):
            return True
        return False

    def reward(self, snap: Snapshot, initial_coins: int) -> float:
        """Calculate reward for a state."""
        if snap.eleven.hp <= 0:
            return -100.0
        if snap.has_key and len(snap.coins) == 0 and self.maze.is_exit(snap.eleven.x, snap.eleven.y):
            elapsed = pygame.time.get_ticks() - self.game_start_time
            time_bonus = max(0, (TIME_LIMIT_MS - elapsed) / 1000.0)
            return 100.0 + time_bonus * 0.3

        collected = initial_coins - len(snap.coins)
        score = collected * 15.0
        if snap.has_key:
            score += 25.0

        target = self.choose_goal_for_eleven(snap)
        score -= manhattan((snap.eleven.x, snap.eleven.y), target) * 0.8

        for d in snap.demogorgons:
            if d.hp <= 0:
                continue
            dist = manhattan((d.x, d.y), (snap.eleven.x, snap.eleven.y))
            if dist <= 1:
                score -= 35
            elif dist <= 3:
                score -= (4 - dist) * 6
            elif dist <= 5:
                score -= (6 - dist) * 2

        elapsed = pygame.time.get_ticks() - self.game_start_time
        score -= (elapsed / 1000.0) * 0.1
        return score

    def choose_goal_for_eleven(self, snap: Snapshot) -> Tuple[int, int]:
        """Choose the next objective for Eleven."""
        if snap.coins:
            return min(snap.coins, key=lambda c: manhattan((snap.eleven.x, snap.eleven.y), c))
        if not snap.has_key:
            return snap.key_pos
        # Choose the nearest exit door as the goal
        exits = getattr(self.maze, "exit_positions", {self.maze.exit_pos})
        return min(exits, key=lambda e: manhattan((snap.eleven.x, snap.eleven.y), e))

    def is_face_to_face(self, e: AgentState, d: AgentState) -> bool:
        """Check if Eleven and Demogorgon face each other."""
        if manhattan((e.x, e.y), (d.x, d.y)) != 1:
            return False
        e_to_d = direction_between((e.x, e.y), (d.x, d.y))
        d_to_e = direction_between((d.x, d.y), (e.x, e.y))
        return e.direction == e_to_d and d.direction == d_to_e

    def is_backstab(self, attacker: AgentState, target: AgentState) -> bool:
        """Check if attack is from behind (backstab)."""
        if manhattan((attacker.x, attacker.y), (target.x, target.y)) != 1:
            return False
        target_to_attacker = direction_between((target.x, target.y), (attacker.x, attacker.y))
        return target_to_attacker == OPPOSITE[target.direction]

    def valid_eleven_actions(self, snap: Snapshot) -> List[Tuple[str, object]]:
        """Get valid actions for Eleven."""
        acts: List[Tuple[str, object]] = [("wait", None)]

        for d in CARDINALS:
            new_pos = self.maze.move_with_tunnel((snap.eleven.x, snap.eleven.y), d)
            occupied = any(dd.hp > 0 and (dd.x, dd.y) == new_pos for dd in snap.demogorgons)
            if new_pos != (snap.eleven.x, snap.eleven.y) and not occupied:
                acts.append(("move", d))

        for i, d in enumerate(snap.demogorgons):
            if d.hp <= 0:
                continue
            if manhattan((snap.eleven.x, snap.eleven.y), (d.x, d.y)) == 1:
                acts.append(("shoot", i))

        return acts

    def apply_eleven_action(self, snap: Snapshot, action: Tuple[str, object]):
        """Apply Eleven's action to snapshot."""
        kind, value = action
        if kind == "move":
            direction: Direction = value
            new_pos = self.maze.move_with_tunnel((snap.eleven.x, snap.eleven.y), direction)
            snap.eleven.x, snap.eleven.y = new_pos
            snap.eleven.direction = direction
        elif kind == "shoot":
            idx = value
            if 0 <= idx < len(snap.demogorgons):
                d = snap.demogorgons[idx]
                if d.hp > 0 and manhattan((snap.eleven.x, snap.eleven.y), (d.x, d.y)) == 1:
                    if self.is_backstab(snap.eleven, d):
                        d.hp -= 2
                    elif self.is_face_to_face(snap.eleven, d):
                        d.hp -= 1
                    else:
                        d.hp -= 1

        if (snap.eleven.x, snap.eleven.y) in snap.coins:
            snap.coins.remove((snap.eleven.x, snap.eleven.y))

        if not snap.has_key and (snap.eleven.x, snap.eleven.y) == snap.key_pos:
            snap.has_key = True

        # If Eleven steps on an exit and has a key in the snapshot, unlock that exit (consume key)
        if getattr(self.maze, "is_exit", None) is not None:
            if self.maze.is_exit(snap.eleven.x, snap.eleven.y):
                if snap.has_key:
                    if getattr(snap, "unlocked_exits", None) is None:
                        snap.unlocked_exits = set()
                    if (snap.eleven.x, snap.eleven.y) not in snap.unlocked_exits:
                        snap.unlocked_exits.add((snap.eleven.x, snap.eleven.y))
                        snap.has_key = False

    def rollout_eleven_action(self, snap: Snapshot) -> Tuple[str, object]:
        """Select action during rollout using simple heuristics."""
        actions = self.valid_eleven_actions(snap)
        weighted = []
        target = self.choose_goal_for_eleven(snap)

        for action in actions:
            test = snap.clone()
            self.apply_eleven_action(test, action)
            pos = (test.eleven.x, test.eleven.y)

            safe = 0.0
            for d in test.demogorgons:
                if d.hp > 0:
                    dist = manhattan(pos, (d.x, d.y))
                    safe += min(dist, 5)

            goal_gain = -manhattan(pos, target)
            w = safe * 2.3 + goal_gain * 1.8
            if action[0] == "shoot":
                w += 6
            weighted.append((w, action))

        weighted.sort(key=lambda x: x[0], reverse=True)
        top = weighted[: min(3, len(weighted))]
        return random.choice([a for _, a in top])

    def predicted_eleven_step(self, snap: Snapshot):
        """Predict Eleven's next step."""
        action = self.rollout_eleven_action(snap)
        self.apply_eleven_action(snap, action)

    def valid_demo_actions(self, snap: Snapshot, idx: int) -> List[Direction]:
        """Get valid actions for a Demogorgon."""
        d = snap.demogorgons[idx]
        if d.hp <= 0:
            return [Direction.NONE]

        occupied = {(dd.x, dd.y) for j, dd in enumerate(snap.demogorgons) if j != idx and dd.hp > 0}

        actions = [Direction.NONE]
        for move in CARDINALS:
            n = add_pos((d.x, d.y), move.value)
            if self.maze.is_walkable(n):
                actions.append(move)
        return actions

    def apply_demo_action(self, snap: Snapshot, idx: int, move: Direction):
        """Apply Demogorgon action (no tunnels for Demogorgons)."""
        d = snap.demogorgons[idx]
        if d.hp <= 0:
            return
        nxt = add_pos((d.x, d.y), move.value)
        if self.maze.is_walkable(nxt):
            d.x, d.y = nxt
            d.direction = move

    def demo_eval(self, snap: Snapshot, idx: int) -> float:
        """Evaluate state for a Demogorgon."""
        d = snap.demogorgons[idx]
        if d.hp <= 0:
            return -999.0

        epos = (snap.eleven.x, snap.eleven.y)
        dpos = (d.x, d.y)
        blocked = {(other.x, other.y) for j, other in enumerate(snap.demogorgons) if j != idx and other.hp > 0}
        chase_dist = astar_distance(self.maze, dpos, epos, blocked, use_tunnels=False)
        score = -chase_dist * 3.2

        adjacent_threat = 0
        for move in CARDINALS:
            n = add_pos(epos, move.value)
            if not self.maze.is_walkable(n):
                adjacent_threat += 0.9
            elif any(dd.hp > 0 and (dd.x, dd.y) == n for dd in snap.demogorgons):
                adjacent_threat += 1.4
        score += adjacent_threat * 3.0

        if snap.has_key and len(snap.coins) == 0:
            # Compute distance to the nearest exit door
            exits = getattr(self.maze, "exit_positions", {self.maze.exit_pos})
            exit_block_dist = min(astar_distance(self.maze, dpos, ex, blocked, use_tunnels=False) for ex in exits)
            score += -exit_block_dist * 1.8

        cluster_penalty = 0.0
        for j, other in enumerate(snap.demogorgons):
            if j == idx or other.hp <= 0:
                continue
            dist = manhattan(dpos, (other.x, other.y))
            if dist <= 1:
                cluster_penalty += 3.5
            elif dist == 2:
                cluster_penalty += 1.5
        score -= cluster_penalty

        return score

    def apply_demogorgon_turn(self, snap: Snapshot):
        """Apply actions for all Demogorgons."""
        for idx, d in enumerate(snap.demogorgons):
            if d.hp <= 0:
                continue

            move = best_demo_move(self, snap, idx, depth=2)
            self.apply_demo_action(snap, idx, move)

            e = snap.eleven
            if manhattan((d.x, d.y), (e.x, e.y)) == 1:
                d_to_e = direction_between((d.x, d.y), (e.x, e.y))
                e_to_d = direction_between((e.x, e.y), (d.x, d.y))

                if d.direction == d_to_e and e.direction == e_to_d:
                    e.hp -= 2
                elif not self.is_backstab(e, d):
                    e.hp -= 1

    def run_round(self):
        """Execute one game round with both agents."""
        if self.game_over:
            return

        snap = self.snapshot()

        action = mcts_action(self, snap, iterations=80, rollout_depth=8)
        self.apply_eleven_action(snap, action)

        self.apply_demogorgon_turn(snap)
        snap.turns_left -= 1

        self.apply_snapshot(snap)
        self.resolve_encounter_skills()
        self.post_turn_updates()

    def resolve_encounter_skills(self):
        """Resolve encounters between Eleven and adjacent Demogorgons."""
        now = pygame.time.get_ticks()

        for d in self.demogorgons:
            if d.hp <= 0:
                continue

            if manhattan(self.eleven.pos(), d.pos()) != 1:
                continue

            can_shoot = False

            if self.shoots_used == 0:
                can_shoot = True
            elif self.shoots_used >= 1:
                time_since_last_shoot = now - self.last_shoot_time
                can_shoot = time_since_last_shoot >= SHOOT_COOLDOWN_MS

            if can_shoot and self.shoots_used < MAX_SHOOTS:
                d.hp = 0
                self.shoots_used += 1
                self.last_shoot_time = now
                shots_remaining = MAX_SHOOTS - self.shoots_used
                self.show_message(f"Eleven shot! Demogorgon defeated! ({shots_remaining} shots left)")
                return
            else:
                self.eleven.hp = 0
                self.show_message("Demogorgon caught and ate Eleven!")
                return

    def post_turn_updates(self):
        """Update game state after each turn."""
        
        # 1. Did the Demogorgons catch Eleven?
        if self.eleven.hp <= 0:
            self.game_over = True
            self.victory = False
            self.winner = "Demogorgon"
            self.show_message("Eleven was caught", 3000)
            return

        # 2. Did we run out of time?
        elapsed = pygame.time.get_ticks() - self.game_start_time
        if elapsed >= TIME_LIMIT_MS:
            self.game_over = True
            self.victory = False
            self.winner = "Demogorgon"
            self.points += 0
            self.show_message("Time is over", 3000)
            return

        # ---------------------------------------------------------
        # NEW UPDATED CODE: EXIT DOOR LOGIC
        # ---------------------------------------------------------
        # 3. Is Eleven standing on the exit door right now?
        if self.maze.is_exit(self.eleven.x, self.eleven.y):
            # If Eleven has a key and the door is not yet unlocked, use the key to unlock this door
            if self.has_key and (self.eleven.pos() not in getattr(self.maze, "unlocked_exits", set())):
                self.maze.unlocked_exits.add(self.eleven.pos())
                self.has_key = False
                self.show_message("You used the key to unlock this door!", 1400)
                # If all coins already collected, unlocking here wins the game
                if len(self.coins) == 0:
                    self.game_over = True
                    self.victory = True
                    self.winner = "Eleven"
                    self.points += 50
                    self.show_message("Eleven escaped the Upside Down!", 3200)
                    return
            else:
                # Door is locked (no key) or already unlocked but no coins
                if not self.has_key and (self.eleven.pos() not in getattr(self.maze, "unlocked_exits", set())):
                    self.show_message("The door is locked! Find the key!", 1000)
                elif len(self.coins) > 0 and (self.eleven.pos() not in getattr(self.maze, "unlocked_exits", set())):
                    self.show_message(f"The door is locked! Collect {len(self.coins)} more coins!", 1000)

        # 4. Did Eleven step on the Key to pick it up?
        if not self.has_key and self.eleven.pos() == self.key_pos:
            self.has_key = True
            self.points += 20
            self.show_message("Eleven picked up the key")

        # 5. Did Eleven step on a Coin to pick it up?
        if self.eleven.pos() in self.coins:
            self.coins.remove(self.eleven.pos())
            self.points += 10
            self.show_message(f"Coin collected ({TOTAL_COINS - len(self.coins)}/{TOTAL_COINS})")

        # 6. Did Eleven defeat all the monsters?
        alive = [d for d in self.demogorgons if d.hp > 0]
        if not alive:
            self.game_over = True
            self.victory = True
            self.winner = "Eleven"
            self.points += 100
            self.show_message("All Demogorgons defeated", 3200)
            
    def update_encounter_audio(self):
        """Update encounter sound effects."""
        encounter_now = False
        for d in self.demogorgons:
            if d.hp <= 0:
                continue
            if manhattan(self.eleven.pos(), d.pos()) <= 1:
                encounter_now = True
                break

        if encounter_now and not self.encounter_active:
            self.encounter_active = True
            if self.encounter_sound is not None and pygame.mixer.get_init() is not None:
                self.encounter_channel = self.encounter_sound.play(loops=-1)
        elif not encounter_now and self.encounter_active:
            self.encounter_active = False
            if self.encounter_channel is not None:
                self.encounter_channel.stop()

    def draw_detection(self):
        """Draw detection radius for Demogorgons."""
        for d in self.demogorgons:
            if d.hp <= 0:
                continue
            radius = int(DETECTION_RADIUS * CELL_SIZE * 0.38)
            cx = d.x * CELL_SIZE + CELL_SIZE // 2
            cy = d.y * CELL_SIZE + HUD_HEIGHT + CELL_SIZE // 2
            surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, COLOR_DETECTION, (radius, radius), radius)
            pygame.draw.circle(surf, COLOR_DETECTION_INNER, (radius, radius), int(radius * 0.66))
            self.screen.blit(surf, (cx - radius, cy - radius))

    def draw_entities(self):
        """Draw game entities."""
        for d in self.demogorgons:
            if d.hp <= 0:
                continue
            self.screen.blit(self.demo_sprite, (d.x * CELL_SIZE, d.y * CELL_SIZE + HUD_HEIGHT))
            hp = self.small_font.render(str(d.hp), True, COLOR_TEXT)
            self.screen.blit(hp, (d.x * CELL_SIZE + 4, d.y * CELL_SIZE + HUD_HEIGHT + 4))

        self.screen.blit(self.eleven_sprite, (self.eleven.x * CELL_SIZE, self.eleven.y * CELL_SIZE + HUD_HEIGHT))

    def draw_items(self):
        """Draw coins and key."""
        for c in self.coins:
            cx = c[0] * CELL_SIZE + CELL_SIZE // 2
            cy = c[1] * CELL_SIZE + HUD_HEIGHT + CELL_SIZE // 2
            pygame.draw.circle(self.screen, COLOR_COIN, (cx, cy), CELL_SIZE // 7)
            pygame.draw.circle(self.screen, (255, 240, 170), (cx - 2, cy - 2), CELL_SIZE // 13)

        if not self.has_key:
            kx = self.key_pos[0] * CELL_SIZE + CELL_SIZE // 2
            ky = self.key_pos[1] * CELL_SIZE + HUD_HEIGHT + CELL_SIZE // 2
            pygame.draw.circle(self.screen, COLOR_KEY, (kx, ky), CELL_SIZE // 8)
            pygame.draw.rect(self.screen, COLOR_KEY, (kx + 3, ky - 2, 12, 4), border_radius=2)

    def draw_hud(self):
        """Draw heads-up display."""
        pygame.draw.rect(self.screen, COLOR_HUD, (0, 0, SCREEN_WIDTH, HUD_HEIGHT))
        pygame.draw.line(self.screen, (120, 95, 130), (0, HUD_HEIGHT - 2), (SCREEN_WIDTH, HUD_HEIGHT - 2), 2)

        now = pygame.time.get_ticks()
        elapsed = now - self.game_start_time
        remaining_ms = max(0, TIME_LIMIT_MS - elapsed)
        minutes = remaining_ms // 60000
        seconds = (remaining_ms % 60000) // 1000
        time_str = f"{minutes}:{seconds:02d}"

        if self.shoots_used == 0:
            can_shoot_now = True
        elif self.shoots_used >= 1:
            time_since_shoot = now - self.last_shoot_time
            can_shoot_now = time_since_shoot >= SHOOT_COOLDOWN_MS
        else:
            can_shoot_now = False

        if can_shoot_now and self.shoots_used < MAX_SHOOTS:
            shoot_str = f"Shoot: READY ({self.shoots_used + 1}/{MAX_SHOOTS})"
            shoot_color = (100, 255, 100)
        elif self.shoots_used >= MAX_SHOOTS:
            shoot_str = f"Shoot: USED ({self.shoots_used}/{MAX_SHOOTS})"
            shoot_color = (150, 150, 150)
        else:
            time_since_shoot = now - self.last_shoot_time
            cooldown_remaining_ms = SHOOT_COOLDOWN_MS - time_since_shoot
            cooldown_sec = (cooldown_remaining_ms + 999) // 1000
            shoot_str = f"Shoot: {cooldown_sec}s ({self.shoots_used + 1}/{MAX_SHOOTS})"
            shoot_color = (255, 200, 70)

        lines = [
            f"HP: {self.eleven.hp}",
            f"Points: {self.points}",
            f"Coins: {TOTAL_COINS - len(self.coins)}/{TOTAL_COINS}",
            f"Key: {'✓' if self.has_key else '✗'}",
            f"Time: {time_str}",
        ]

        x = 15
        for txt in lines:
            s = self.font.render(txt, True, COLOR_TEXT)
            self.screen.blit(s, (x, 10))
            x += s.get_width() + 18

        shoot_surf = self.font.render(shoot_str, True, shoot_color)
        self.screen.blit(shoot_surf, (15, 44))

        alive = sum(1 for d in self.demogorgons if d.hp > 0)
        right = self.font.render(f"Demogorgons: {alive}/{len(self.demogorgons)}", True, (230, 170, 180))
        self.screen.blit(right, (SCREEN_WIDTH - right.get_width() - 15, 44))

        if self.message and pygame.time.get_ticks() < self.message_until:
            m = self.small_font.render(self.message, True, (255, 205, 110))
            rect = m.get_rect(center=(SCREEN_WIDTH // 2, 68))
            self.screen.blit(m, rect)

        esc_hint = pygame.font.Font(None, 24).render("ESC-Quit", True, (150, 150, 150))
        self.screen.blit(esc_hint, (15, HUD_HEIGHT - 25))
        
        # ---------------------------------------------------------
        # NEW CODE: KEY TEXT IN MENU
        # ---------------------------------------------------------
        if self.has_key:
            key_text = "Key: FOUND!"
            key_color = (255, 215, 0) # Shiny Gold Color
        else:
            key_text = "Key: MISSING"
            key_color = (150, 150, 150) # Boring Grey Color
            
        # Draw the text right in the top middle of the screen!
        key_surface = self.font.render(key_text, True, key_color)
        self.screen.blit(key_surface, (SCREEN_WIDTH // 2 - 80, 15))

    def draw_game_over(self):
        """Draw game over screen."""
        if not self.game_over:
            return
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.screen.blit(overlay, (0, 0))

        winner_text = f"WINNER: {self.winner}" if self.winner else "GAME OVER"
        color = COLOR_EXIT if self.victory else (220, 90, 90)
        s = pygame.font.Font(None, 64).render(winner_text, True, color)
        self.screen.blit(s, s.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40)))

        points_text = f"Points: {self.points}"
        ps = self.font.render(points_text, True, COLOR_TEXT)
        self.screen.blit(ps, ps.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)))

        hint = self.font.render("R - Restart | Q - Quit", True, COLOR_TEXT)
        self.screen.blit(hint, hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50)))

    def draw_menu(self):
        """Draws the beautiful Home Page with a Start button!"""
        # 1. Slap our big board picture onto the screen as the background
        self.screen.blit(self.menu_bg, (0, 0))
        
        # 2. Put a dark, see-through glass over the background so the text is easy to read
        # SRCALPHA means "allow see-through colors"
        dark_glass = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        dark_glass.fill((0, 0, 0, 150)) # Black color, 150 means "half see-through"
        self.screen.blit(dark_glass, (0, 0))
        
        # 3. Draw the giant Game Title
        # Make a giant font (size 70)
        title_font = pygame.font.Font(None, 70) 
        title_text = title_font.render("UPSIDE DOWN: ESCAPE", True, (240, 175, 45))
        # Find the exact center of the screen for the title
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))
        self.screen.blit(title_text, title_rect)
        
        # 4. Draw the "Start Game" button
        # First, draw a dark red box in the middle of the screen
        button_rect = pygame.Rect(0, 0, 350, 60)
        button_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        pygame.draw.rect(self.screen, (150, 40, 50), button_rect, border_radius=10)
        
        # Next, write "Press SPACE to Start" inside the red box
        button_text = self.font.render("Press SPACE to Start Game", True, (255, 255, 255))
        text_rect = button_text.get_rect(center=button_rect.center)
        self.screen.blit(button_text, text_rect)
        
        # 5. Show it all on the screen!
        pygame.display.flip()

    def draw(self):
        """Draw the current game state."""
        self.screen.fill(COLOR_BG)
        self.draw_hud()

        # --- Draw the Board background image ---
        # Blit (paste) the pre-loaded board image right below the HUD bar.
        # The top-left corner is at (0, HUD_HEIGHT) so it sits under the HUD.
        self.screen.blit(self.board_bg, (0, HUD_HEIGHT))

        self.maze.draw(self.screen, HUD_HEIGHT, self.has_key, HUD_HEIGHT)
        self.draw_detection()
        self.draw_items()
        self.draw_entities()

        self.draw_game_over()
        self.update_window_title()
        pygame.display.flip()

    def update_window_title(self):
        """Update window title with game stats."""
        now = pygame.time.get_ticks()
        elapsed = now - self.game_start_time
        remaining_ms = max(0, TIME_LIMIT_MS - elapsed)
        minutes = remaining_ms // 60000
        seconds = (remaining_ms % 60000) // 1000
        time_str = f"{minutes}:{seconds:02d}"

        coins_collected = TOTAL_COINS - len(self.coins)
        key_str = "✓" if self.has_key else "✗"

        title = f"Upside Down | Time: {time_str} | Score: {self.points} | Coins: {coins_collected}/{TOTAL_COINS} | Key: {key_str}"
        pygame.display.set_caption(title)

    def update(self):
        """Update game state."""
        now = pygame.time.get_ticks()
        self.update_encounter_audio()

        if not self.game_over and now - self.last_action_tick >= TURN_DELAY_MS:
            self.last_action_tick = now
            self.run_round()

    def run(self):
        """Main game loop. This keeps the game running forever until you quit!"""
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    # If we are on the Home Page and press the Spacebar...
                    if self.in_menu and event.key == pygame.K_SPACE:
                        self.in_menu = False # Turn off the menu
                        self.reset()         # Start a fresh game!
                    
                    # Normal game controls (Quit or Restart)
                    elif event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                        self.running = False
                    elif event.key == pygame.K_r:
                        self.reset()

            # If the menu is turned ON, only draw the menu
            if self.in_menu:
                self.draw_menu()
            # If the menu is turned OFF, play the game normally!
            else:
                self.update()
                self.draw()
            
            # This makes the game run at exactly 60 frames per second
            self.clock.tick(FPS)

        # Stop the creepy music when we close the game
        if self.encounter_channel is not None:
            self.encounter_channel.stop()
        pygame.quit()

