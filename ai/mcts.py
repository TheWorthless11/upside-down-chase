"""Monte Carlo Tree Search (MCTS) algorithm for Eleven."""

import math
import random
from typing import List, Optional, Tuple

from entities import Snapshot


class MCTSNode:
    """Node in the MCTS tree."""
    def __init__(self, state: Snapshot, parent: Optional["MCTSNode"] = None, action=None):
        self.state = state
        self.parent = parent
        self.action = action
        self.children: List[MCTSNode] = []
        self.visits = 0
        self.value = 0.0
        self.untried_actions: List = []

    def uct_score(self, exploration: float = 1.41) -> float:
        if self.visits == 0:
            return float("inf")
        exploit = self.value / self.visits
        explore = exploration * math.sqrt(math.log(max(1, self.parent.visits)) / self.visits)
        return exploit + explore


def mcts_action(
    game,
    root_state: Snapshot,
    iterations: int = 250,
    rollout_depth: int = 12,
) -> Tuple[str, object]:
    """Execute MCTS to find the best action for Eleven."""
    root = MCTSNode(root_state.clone())
    root.untried_actions = game.valid_eleven_actions(root.state)
    initial_coins = len(root_state.coins)

    for _ in range(iterations):
        node = root
        state = root_state.clone()

        # Selection & Expansion
        while not node.untried_actions and node.children:
            node = max(node.children, key=lambda c: c.uct_score())
            game.apply_eleven_action(state, node.action)
            game.apply_demogorgon_turn(state)
            state.turns_left -= 1

        if node.untried_actions:
            action = random.choice(node.untried_actions)
            node.untried_actions.remove(action)
            game.apply_eleven_action(state, action)
            game.apply_demogorgon_turn(state)
            state.turns_left -= 1

            child = MCTSNode(state.clone(), parent=node, action=action)
            child.untried_actions = game.valid_eleven_actions(child.state)
            node.children.append(child)
            node = child

        # Rollout
        rollout_state = state.clone()
        depth = rollout_depth
        while depth > 0 and not game.is_terminal(rollout_state):
            action = game.rollout_eleven_action(rollout_state)
            game.apply_eleven_action(rollout_state, action)
            game.apply_demogorgon_turn(rollout_state)
            rollout_state.turns_left -= 1
            depth -= 1

        # Backpropagation
        r = game.reward(rollout_state, initial_coins)

        while node is not None:
            node.visits += 1
            node.value += r
            node = node.parent

    if not root.children:
        acts = game.valid_eleven_actions(root_state)
        return random.choice(acts) if acts else ("wait", None)

    best = max(root.children, key=lambda c: c.visits)
    return best.action