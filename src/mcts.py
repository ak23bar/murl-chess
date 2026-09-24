"""Pedagogical UCT Monte Carlo Tree Search with bounded random rollouts.

Four stages: select a tree path, expand one move, simulate a capped random
rollout, backpropagate its White reward. All stored rewards are White values;
at a Black parent, UCT exploits (1 - mean_white_reward). This is essential:
Black must choose moves that benefit Black, rather than cooperate with White.

Conceptual sources: Kocsis and Szepesvari (2006), Bandit Based Monte-Carlo
Planning; Browne et al. (2012), A Survey of Monte Carlo Tree Search Methods.
These describe the algorithm; no external implementation was copied.
"""

import argparse
from dataclasses import dataclass, field
import json
from math import isfinite, log, sqrt
import random
from time import perf_counter

import chess

from .evaluation import material_reward, outcome_reward, white_reward


EXPLORATION_CONSTANT = sqrt(2.0)


@dataclass(frozen=True)
class RootVisit:
    move: chess.Move
    visits: int
    mean_white_reward: float | None


@dataclass(frozen=True)
class MCTSResult:
    move: chess.Move | None
    score: float
    iterations: int
    nodes: int
    root_visits: tuple[RootVisit, ...]
    completed: bool
    cutoff_rollouts: int
    terminal_rollouts: int
    rollout_plies: int


@dataclass
class _Node:
    board: chess.Board
    parent: "_Node | None" = None
    move: chess.Move | None = None
    children: list["_Node"] = field(default_factory=list)
    visits: int = 0
    reward_sum: float = 0.0
    untried_moves: list[chess.Move] = field(init=False)
    outcome: chess.Outcome | None = field(init=False)

    def __post_init__(self) -> None:
        self.outcome = self.board.outcome(claim_draw=False)
        self.untried_moves = [] if self.outcome is not None else list(self.board.legal_moves)


class _SearchTimeout(Exception):
    pass


def _uct_value(parent: _Node, child: _Node) -> float:
    if child.visits == 0:
        return float("inf")
    mean_white = child.reward_sum / child.visits
    exploitation = mean_white if parent.board.turn == chess.WHITE else 1.0 - mean_white
    exploration = EXPLORATION_CONSTANT * sqrt(log(max(1, parent.visits)) / child.visits)
    return exploitation + exploration


def mcts(
    board: chess.Board,
    iterations: int,
    seed: int = 0,
    rollout_plies: int = 40,
    max_seconds: float | None = None,
) -> MCTSResult:
    """Search under an iteration budget and return the most-visited root move.

    Every completed iteration backpropagates exactly one reward. Random moves
    are uniform among legal moves. At the rollout cap, a bounded material
    heuristic replaces the unavailable game result; score is NOT a calibrated
    probability. Time checks occur within selection and every rollout ply.
    An interrupted simulation contributes no reward or completed iteration.
    ``nodes`` counts allocated tree nodes, including root and a possible final
    unvisited node created by an interrupted iteration. ``rollout_plies`` in
    the returned result sums plies only from completed simulations.
    """
    if not isinstance(iterations, int) or isinstance(iterations, bool) or iterations < 1:
        raise ValueError("iterations must be a positive integer")
    if not isinstance(rollout_plies, int) or isinstance(rollout_plies, bool) or rollout_plies < 0:
        raise ValueError("rollout_plies must be a nonnegative integer")
    if max_seconds is not None and (not isfinite(max_seconds) or max_seconds < 0):
        raise ValueError("max_seconds must be finite and nonnegative")
    if not board.is_valid():
        raise ValueError("board must be a valid standard chess position")

    deadline = None if max_seconds is None else perf_counter() + max_seconds
    rng = random.Random(seed)
    root = _Node(board.copy(stack=True))
    if root.outcome is not None:
        return MCTSResult(None, outcome_reward(root.outcome), 0, 1, (), True, 0, 0, 0)
    root_moves = tuple(root.untried_moves)
    created_nodes = 1
    completed_iterations = 0
    terminal_rollouts = 0
    cutoff_rollouts = 0
    total_rollout_plies = 0

    def check_time() -> None:
        if deadline is not None and perf_counter() >= deadline:
            raise _SearchTimeout

    for _ in range(iterations):
        try:
            check_time()

            # 1. Selection: fully expanded parents choose a UCT child.
            node = root
            while not node.untried_moves and node.children:
                check_time()
                node = max(node.children, key=lambda child: _uct_value(node, child))

            # 2. Expansion: add a uniformly chosen untried legal move.
            if node.untried_moves:
                move = node.untried_moves.pop(rng.randrange(len(node.untried_moves)))
                child_board = node.board.copy(stack=True)
                child_board.push(move)
                child = _Node(child_board, parent=node, move=move)
                node.children.append(child)
                node = child
                created_nodes += 1

            # 3. Simulation: play random moves until terminal or the cap.
            simulation = node.board.copy(stack=True)
            used_plies = 0
            result = node.outcome
            while result is None and used_plies < rollout_plies:
                check_time()
                simulation.push(rng.choice(list(simulation.legal_moves)))
                used_plies += 1
                result = simulation.outcome(claim_draw=False)
            check_time()
            reward = outcome_reward(result) if result is not None else material_reward(simulation)

            # 4. Backpropagation: the same White reward reaches every ancestor.
            while node is not None:
                node.visits += 1
                node.reward_sum += reward
                node = node.parent
            completed_iterations += 1
            total_rollout_plies += used_plies
            if result is None:
                cutoff_rollouts += 1
            else:
                terminal_rollouts += 1
        except _SearchTimeout:
            break

    by_move = {child.move: child for child in root.children}
    visits = tuple(
        RootVisit(
            move,
            by_move[move].visits if move in by_move else 0,
            by_move[move].reward_sum / by_move[move].visits
            if move in by_move and by_move[move].visits else None,
        )
        for move in root_moves
    )
    if completed_iterations:
        def final_rank(child: _Node) -> tuple[int, float]:
            mean = child.reward_sum / child.visits if child.visits else 0.5
            mover_mean = mean if board.turn == chess.WHITE else 1.0 - mean
            return child.visits, mover_mean
        chosen = max(root.children, key=final_rank)
        move, score = chosen.move, chosen.reward_sum / chosen.visits
    else:
        move, score = root_moves[0], white_reward(board)
    return MCTSResult(
        move, score, completed_iterations, created_nodes, visits,
        completed_iterations == iterations, cutoff_rollouts, terminal_rollouts,
        total_rollout_plies,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fen", default=chess.STARTING_FEN)
    parser.add_argument("--iterations", type=int, default=400)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--rollout-plies", type=int, default=40)
    parser.add_argument("--max-seconds", type=float, default=None)
    args = parser.parse_args()
    board = chess.Board(args.fen)
    start = perf_counter()
    result = mcts(board, args.iterations, args.seed, args.rollout_plies, args.max_seconds)
    elapsed = perf_counter() - start
    print(json.dumps({
        "algorithm": "mcts", "fen": board.fen(), "seed": args.seed,
        "requested_iterations": args.iterations, "iterations": result.iterations,
        "move": result.move.uci() if result.move is not None else None,
        "score_white_reward": result.score, "nodes": result.nodes,
        "completed": result.completed, "cutoff_rollouts": result.cutoff_rollouts,
        "terminal_rollouts": result.terminal_rollouts,
        "total_rollout_plies": result.rollout_plies,
        "execution_time_seconds": elapsed,
        "root_visits": [
            {"move": item.move.uci(), "visits": item.visits,
             "mean_white_reward": item.mean_white_reward}
            for item in result.root_visits
        ],
    }, indent=2))


if __name__ == "__main__":
    main()
