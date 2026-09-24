"""Shared evaluation conventions: positive values always favor White.

Material values are deliberately simple pawn units, not a fitted chess model.
Terminal outcomes take precedence over material. python-chess detects automatic
draws, but we do not model optional threefold/50-move draw claims as actions.
That policy is explicit in every call to ``outcome(claim_draw=False)``.

Conceptual references: AIMA, 4th ed., chapter 5 (cutoff evaluation); python-chess
core documentation (Board.outcome). This implementation was written for this
experiment; no external source code was copied.
"""

from math import tanh

import chess


PIECE_VALUES = {
    chess.PAWN: 1.0,
    chess.KNIGHT: 3.0,
    chess.BISHOP: 3.0,
    chess.ROOK: 5.0,
    chess.QUEEN: 9.0,
    chess.KING: 0.0,
}
MATE_SCORE = 10_000.0
ROLLOUT_MATERIAL_SCALE = 10.0


def material_score(board: chess.Board) -> float:
    """White material minus Black material, measured in pawn units."""
    return sum(
        value * (len(board.pieces(piece, chess.WHITE))
                 - len(board.pieces(piece, chess.BLACK)))
        for piece, value in PIECE_VALUES.items()
    )


def outcome_score(outcome: chess.Outcome) -> float:
    """Map a terminal result to +mate, -mate, or zero from White's view."""
    if outcome.winner is None:
        return 0.0
    return MATE_SCORE if outcome.winner == chess.WHITE else -MATE_SCORE


def outcome_reward(outcome: chess.Outcome) -> float:
    """White win = 1, draw = 1/2, Black win = 0."""
    if outcome.winner is None:
        return 0.5
    return 1.0 if outcome.winner == chess.WHITE else 0.0


def evaluate(board: chess.Board) -> float:
    """Terminal-aware material evaluation used by MinMax."""
    outcome = board.outcome(claim_draw=False)
    return outcome_score(outcome) if outcome is not None else material_score(board)


def material_reward(board: chess.Board) -> float:
    """Bounded White reward at a rollout cutoff; NOT a win probability.

    A ten-pawn scale prevents large material differences from dominating the
    UCT reward range. It is a declared heuristic, not a calibrated parameter.
    """
    return 0.5 * (1.0 + tanh(material_score(board) / ROLLOUT_MATERIAL_SCALE))


def white_reward(board: chess.Board) -> float:
    """Terminal-aware reward used for MCTS fallbacks and tests."""
    outcome = board.outcome(claim_draw=False)
    return outcome_reward(outcome) if outcome is not None else material_reward(board)
