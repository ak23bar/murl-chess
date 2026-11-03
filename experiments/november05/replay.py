"""Repeat exact root checks and selected deterministic searches independently of timings."""
import csv
import json
from pathlib import Path

import chess
from experiments.october14.oracle import solve
from src.mcts import mcts
from src.minimax import minimax


def main():
    root = Path("deliverables/october14/results")
    raw = [json.loads(line) for line in (root / "run1/raw.jsonl").read_text().splitlines()]
    rows = list(csv.DictReader((root / "summary.csv").open()))
    for row in rows:
        board = chess.Board(row["fen"])
        for depth in (1, 3, 5):
            result = solve(board, depth)
            assert result["completed"]
            assert result["winning_moves"] == ([row["expected_uci"]] if depth == 5 else [])
            assert len(result["tested_root_moves"]) == board.legal_moves.count()
        result = minimax(board, 3)
        assert result.completed and board.san(result.move) == row["minimax_3_move"]
    for r in raw:
        if r["id"] in (6, 13, 16) and r["algorithm"]=="mcts":
            board = chess.Board(rows[r["id"]-1]["fen"])
            result = mcts(board, 1000, seed=r["seed"], rollout_plies=40)
            assert result.completed and result.move.uci() == r["move"]
            visits = [dict(move=v.move.uci(), visits=v.visits, mean=v.mean_white_reward)
                      for v in result.root_visits]
            assert visits == r["root_visits"]
    print("Reproduced 60 exact root checks, 20 depth-three moves, and all root visits for 9 seeded MCTS calls.")


if __name__ == "__main__":
    main()
