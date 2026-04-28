# State Space Tree (Upside Down: Tactical Escape)

This document describes the **search/state space** for the game in a way that matches the code in `game.py`, `maze.py`, and `entities.py`.

## 1) State definition

The AI-facing game state is represented by `Snapshot` (see `entities.py`), plus the maze layout (walls, tunnels, exits).

A snapshot $S$ contains:

- **Eleven**: `(x, y, direction, hp)`
- **Demogorgons**: list of `(x, y, direction, hp)`
- **Coins**: set of remaining coin coordinates
- **Key**: `key_pos` + `has_key`
- **Unlocked exits**: `unlocked_exits` (set of exit coordinates that are open)
- **Other counters**: `turns_left`, `points`, `last_shoot_time`

The maze (static for an episode) contains:

- `walls` and `is_walkable(pos)`
- `tunnels` and `move_with_tunnel(pos, direction)`
- `exit_positions` and `is_exit(x, y)`

## 2) Action sets (branching)

### Eleven actions $A_E(S)$

In code (`Game.valid_eleven_actions`), Eleven can do:

- `wait`
- `move(d)` where $d \in \{N,S,E,W\}$, if the destination is walkable (and not occupied by a live demogorgon)
- `shoot(i)` for each adjacent **alive** demogorgon index `i`

### Demogorgon actions $A_D(S)$

For each alive demogorgon, available moves are:

- `NONE` (stay)
- `N`, `S`, `E`, `W` if the target cell is walkable

In the *actual* game loop, each demogorgon’s move is chosen by minimax (`best_demo_move`), but the **state space** includes all legal moves.

## 3) Transition function (one round)

A full round is (simplified):

1. **Eleven chooses** an action $a_E \in A_E(S_t)$.
2. Apply $a_E$:
   - If `move`: update position using tunnel logic.
   - If `shoot`: reduce HP of the targeted adjacent demogorgon.
   - Auto-interactions:
     - If standing on a coin → coin removed.
     - If standing on the key and not already holding it → `has_key=True`.
     - If standing on an exit while holding the key → mark that exit as unlocked and consume the key.
3. **Demogorgons act** (one by one). Each demogorgon selects a legal move $a_{D_j}$ and moves.
4. If any demogorgon ends adjacent to Eleven, combat damage may apply.
5. **Terminal checks** (win/lose/time).

## 4) Terminal conditions (game over)

A state becomes terminal if:

- **Demogorgon win**: Eleven’s HP reaches 0, or the time limit expires.
- **Eleven win**:
  - Eleven is on an exit tile and the exit is **open** (already unlocked) *or* she can unlock it with a key **and** she has collected at least one coin, **or**
  - all Demogorgons are defeated.

> Note: The win condition in code uses “at least one coin” (not necessarily all coins).

## 5) State-space tree (2-ply: Eleven → Demogorgons)

The real tree is enormous, so the diagram below shows the **shape** of the game tree for one round.

```mermaid
flowchart TD
    S0["S_t (Snapshot at start of round)\nEleven: (x,y,dir,hp)\nDemos: positions/hp\nCoins set, Key, Unlocked exits"]

    S0 -->|a_E = wait| E1["S_t^E (after Eleven action)"]
    S0 -->|a_E = move(N/S/E/W)| E1
    S0 -->|a_E = shoot(i)| E1

    E1 --> D0{"Demogorgon joint response\n(a_D1, a_D2, ..., a_Dk)"}

    D0 -->|legal moves| S1["S_t^{ED} (after demos + combat)"]

    S1 -->|terminal: Eleven wins| W["WIN: Eleven"]
    S1 -->|terminal: Demogorgon wins| L["LOSE: Demogorgon"]
    S1 -->|non-terminal| S2["S_{t+1} (next round)"]
```

## 6) Useful branching-factor intuition

Let:

- $b_E$ = number of legal Eleven actions (typically `1..(1+4+adjacent_demos)`)
- $b_D$ = number of legal moves per demogorgon (typically `1..5`)
- $k$ = number of alive demogorgons

A rough upper bound on one-round expansion is:

$$b_E \times (b_D)^k$$

This is why the implementation uses **MCTS** (sampling the tree) for Eleven and **depth-limited minimax** for Demogorgons.
