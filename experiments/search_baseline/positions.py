"""Deliberate position fixtures; these are controls, not a random chess sample.

The first six positions were constructed for this experiment. They satisfy
python-chess's board-validity checks, which do not prove historical reachability.
The last two are the standard initial position and a legal opening sequence.
No position was selected after inspecting its benchmark performance.
"""

from dataclasses import dataclass

import chess


@dataclass(frozen=True)
class Position:
    position_id: str
    label: str
    fen: str
    expected_piece_count: int
    rationale: str
    provenance: str = "Constructed control for this experiment"

    def board(self) -> chess.Board:
        board = chess.Board(self.fen)
        if not board.is_valid():
            raise ValueError(f"Invalid position {self.position_id}: status={board.status()}")
        if len(board.piece_map()) != self.expected_piece_count:
            raise ValueError(f"Incorrect piece count in {self.position_id}")
        if board.is_game_over(claim_draw=False):
            raise ValueError(f"Benchmark position {self.position_id} is terminal")
        return board


POSITIONS = (
    Position(
        "rook_04", "Four-piece rook ending",
        "8/5k2/6r1/8/8/1R6/2K5/8 w - - 0 1", 4,
        "Very low material with long-range rook moves; sparse need not mean immobile.",
    ),
    Position(
        "rook_pawns_07", "Seven-piece rook ending",
        "8/5pk1/6p1/8/2P5/2K5/1R6/6r1 w - - 0 1", 7,
        "Adds asymmetric pawn material to two kings and two rooks.",
    ),
    Position(
        "rook_pawns_11", "Eleven-piece rook ending",
        "8/4rpk1/5pp1/8/2P1P3/P1K2P2/1R6/8 w - - 0 1", 11,
        "Larger pawn population changes mobility and captures without adding minor pieces.",
    ),
    Position(
        "pawns_16", "Sixteen-piece pawn blockade",
        "6k1/8/8/pppppp1p/PPPPPP1P/8/8/6K1 w - - 0 1", 16,
        "Paired material count with mixed_16; blocked pawn advances but captures remain legal.",
    ),
    Position(
        "mixed_16", "Sixteen-piece mixed position",
        "r3k3/1p2bpp1/2n5/3q4/3Q4/2N5/1P2BPP1/R3K3 w - - 0 1", 16,
        "Same piece count as pawns_16, with queens, rooks and minor pieces increasing mobility.",
    ),
    Position(
        "middlegame_24", "Reduced middlegame",
        "r2q1rk1/ppp2ppp/2nb4/8/3P4/2NB4/PP3PPP/R2Q1RK1 w - - 0 1", 24,
        "Developed pieces and castled kings with some central material removed.",
    ),
    Position(
        "initial_32", "Initial position", chess.STARTING_FEN, 32,
        "Full material with initially restricted mobility; paired with italian_32.",
        "Standard chess starting position",
    ),
    Position(
        "italian_32", "Italian development",
        "r1bqk1nr/pppp1ppp/2n5/2b1p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4", 32,
        "Full material after development; isolates mobility changes without captures.",
        "Legal sequence: 1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5",
    ),
)


def validated_positions() -> tuple[Position, ...]:
    """Validate every fixture before returning the immutable experiment design."""
    for position in POSITIONS:
        position.board()
    return POSITIONS


def main() -> None:
    import csv
    import sys

    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(("position_id", "piece_count", "legal_moves_at_root", "side_to_move", "fen"))
    for position in validated_positions():
        board = position.board()
        writer.writerow((position.position_id, len(board.piece_map()), board.legal_moves.count(),
                         "white" if board.turn else "black", board.fen()))


if __name__ == "__main__":
    main()
