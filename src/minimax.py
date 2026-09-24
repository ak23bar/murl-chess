"""Plain depth-limited MinMax, with no pruning or move ordering.

White maximizes and Black minimizes a score expressed in White pawn units.
The root counts as one visited node. A depth of one examines each legal move
and evaluates its resulting board. Ties keep python-chess's first legal move.

Conceptual references: Russell and Norvig, Artificial Intelligence: A Modern
Approach, 4th ed., chapter 5 (background); the official AIMA 3rd-edition
companion's Minimax-Decision/Max-Value/Min-Value pseudocode (algorithm structure).
The Python implementation is original to this study; it is not copied code.
"""

import argparse
from dataclasses import dataclass
import json
from math import isfinite
from time import perf_counter

import chess

from .evaluation import evaluate, material_score, outcome_score


@dataclass(frozen=True)
class MinimaxResult:
    move: chess.Move | None
    score: float
    nodes: int
    completed: bool


class _SearchTimeout(Exception):
    pass


def minimax(
    board: chess.Board, depth: int, max_seconds: float | None = None
) -> MinimaxResult:
    """Return a legal move, White score, visited nodes, and completion status.

    ``completed`` means the requested depth was fully searched, or the root
    was already terminal. On timeout, the best fully searched root branch
    is retained. If none finished, return the first legal move and the root's
    static score. Such a fallback is explicitly NOT a completed depth result.
    Input board and its repetition history are preserved through a copy.
    """
    if not isinstance(depth, int) or isinstance(depth, bool) or depth < 1:
        raise ValueError("depth must be a positive integer")
    if max_seconds is not None and (not isfinite(max_seconds) or max_seconds < 0):
        raise ValueError("max_seconds must be finite and nonnegative")
    if not board.is_valid():
        raise ValueError("board must be a valid standard chess position")

    deadline = None if max_seconds is None else perf_counter() + max_seconds
    work = board.copy(stack=True)
    nodes = 1
    outcome = work.outcome(claim_draw=False)
    if outcome is not None:
        return MinimaxResult(None, outcome_score(outcome), nodes, True)

    def check_time() -> None:
        if deadline is not None and perf_counter() >= deadline:
            raise _SearchTimeout

    def search(remaining: int) -> float:
        nonlocal nodes
        check_time()
        nodes += 1
        result = work.outcome(claim_draw=False)
        if result is not None:
            return outcome_score(result)
        if remaining == 0:
            return material_score(work)

        maximizing = work.turn == chess.WHITE
        best = float("-inf") if maximizing else float("inf")
        for move in work.legal_moves:
            work.push(move)
            try:
                value = search(remaining - 1)
            finally:
                work.pop()
            best = max(best, value) if maximizing else min(best, value)
        return best

    maximizing = work.turn == chess.WHITE
    best_move = next(iter(work.legal_moves))
    fallback_score = evaluate(work)
    best_score = float("-inf") if maximizing else float("inf")
    finished_branches = 0
    try:
        for move in work.legal_moves:
            check_time()
            work.push(move)
            try:
                score = search(depth - 1)
            finally:
                work.pop()
            if finished_branches == 0 or (score > best_score if maximizing else score < best_score):
                best_score, best_move = score, move
            finished_branches += 1
        return MinimaxResult(best_move, best_score, nodes, True)
    except _SearchTimeout:
        score = best_score if finished_branches else fallback_score
        return MinimaxResult(best_move, score, nodes, False)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fen", default=chess.STARTING_FEN)
    parser.add_argument("--depth", type=int, default=3)
    parser.add_argument("--max-seconds", type=float, default=None)
    args = parser.parse_args()
    board = chess.Board(args.fen)
    start = perf_counter()
    result = minimax(board, args.depth, args.max_seconds)
    elapsed = perf_counter() - start
    print(json.dumps({
        "algorithm": "minimax", "fen": board.fen(), "depth": args.depth,
        "move": result.move.uci() if result.move is not None else None,
        "score_white_pawns": result.score, "nodes": result.nodes,
        "completed": result.completed, "execution_time_seconds": elapsed,
    }, indent=2))


if __name__ == "__main__":
    main()
