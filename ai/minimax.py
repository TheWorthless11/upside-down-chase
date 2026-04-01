"""Minimax algorithm with alpha-beta pruning for Demogorgons."""

from entities import Direction, Snapshot


def minimax_demo(
    game,
    snap: Snapshot,
    idx: int,
    depth: int,
    alpha: float,
    beta: float,
    maximizing: bool,
) -> float:
    """Minimax with alpha-beta pruning."""
    if depth == 0 or game.is_terminal(snap):
        return game.demo_eval(snap, idx)

    if maximizing:
        best = -10**9
        for action in game.valid_demo_actions(snap, idx):
            nxt = snap.clone()
            game.apply_demo_action(nxt, idx, action)
            val = minimax_demo(game, nxt, idx, depth - 1, alpha, beta, False)
            best = max(best, val)
            alpha = max(alpha, best)
            if beta <= alpha:
                break
        return best

    nxt = snap.clone()
    game.predicted_eleven_step(nxt)
    return minimax_demo(game, nxt, idx, depth - 1, alpha, beta, True)


def best_demo_move(game, snap: Snapshot, idx: int, depth: int = 3) -> Direction:
    """Find the best move for a Demogorgon using minimax."""
    best_action = Direction.NONE
    best_val = -10**9
    alpha = -10**9
    beta = 10**9

    for action in game.valid_demo_actions(snap, idx):
        nxt = snap.clone()
        game.apply_demo_action(nxt, idx, action)
        val = minimax_demo(game, nxt, idx, depth - 1, alpha, beta, False)
        if val > best_val:
            best_val = val
            best_action = action
        alpha = max(alpha, best_val)

    return best_action
