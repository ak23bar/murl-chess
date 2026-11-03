"""Compare returned decisions at two shared wall-clock ceilings, in serial."""
import argparse
import csv
import json
import platform
import random
import sys
import time
from pathlib import Path

import chess
from src.minimax import minimax
from src.mcts import mcts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    out = parser.parse_args().output
    out.mkdir(parents=True, exist_ok=True)
    positions = list(csv.DictReader(Path("deliverables/october14/results/summary.csv").open()))
    jobs = [(p, cap, method, seed) for p in positions for cap in (0.25, 1.0)
            for method, seed in [("minimax", None), ("mcts", 0), ("mcts", 1), ("mcts", 2)]]
    random.Random(496).shuffle(jobs)
    meta = dict(system=platform.platform(), cpu=platform.processor(), python=sys.version,
                chess=chess.__version__, order_seed=496, start_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    with (out / "budget.csv").open("x", newline="") as stream:
        writer = None
        for order, (p, cap, method, seed) in enumerate(jobs, 1):
            board = chess.Board(p["fen"])
            start = time.perf_counter()
            result = (minimax(board, 3, cap) if method == "minimax"
                      else mcts(board, 100000, seed, 40, cap))
            seconds = time.perf_counter() - start
            assert result.move in board.legal_moves
            row = dict(order=order, id=p["id"], fen=p["fen"], cap=cap, method=method, seed=seed,
                       legal_moves=board.legal_moves.count(), seconds=seconds, move=result.move.uci(),
                       san=board.san(result.move), key=p["expected_uci"], hit=result.move.uci()==p["expected_uci"],
                       completed=result.completed, nodes=result.nodes, iterations=getattr(result,"iterations",""))
            if writer is None:
                writer = csv.DictWriter(stream, fieldnames=list(row))
                writer.writeheader()
            writer.writerow(row)
    (out / "environment.json").write_text(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
