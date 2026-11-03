"""I validate my paired design and summarize keys returned at each time ceiling."""
import argparse
import csv
from pathlib import Path
from statistics import median
import chess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    directory = parser.parse_args().directory
    rows = list(csv.DictReader((directory / "budget.csv").open()))
    puzzles = {r["id"]: r for r in csv.DictReader(Path("deliverables/october14/results/summary.csv").open())}
    expected = {(i, c, a, s) for i in puzzles for c in ("0.25", "1.0")
                for a, s in [("minimax", ""), ("mcts", "0"), ("mcts", "1"), ("mcts", "2")]}
    assert len(rows) == len(expected) == 160
    assert {(r["id"], r["cap"], r["method"], r["seed"]) for r in rows} == expected
    for r in rows:
        p = puzzles[r["id"]]
        b = chess.Board(p["fen"])
        assert r["fen"] == p["fen"] and r["key"] == p["expected_uci"]
        assert r["hit"] == str(r["move"] == r["key"])
        assert b.san(b.parse_uci(r["move"])) == r["san"]
        assert float(r["seconds"]) > 0 and int(r["nodes"]) >= 1
        if r["method"] == "mcts":
            assert 0 < int(r["iterations"]) <= 100000
            assert r["completed"] == str(int(r["iterations"]) == 100000)
    with (directory / "budget_summary.csv").open("w", newline="") as f:
        writer = None
        for cap in ("0.25", "1.0"):
            for method in ("minimax", "mcts"):
                grp = [r for r in rows if r["cap"]==cap and r["method"]==method]
                done = [r for r in grp if r["completed"]=="True"]
                out = dict(cap=cap, method=method, n=len(grp), returned_hits=sum(r["hit"]=="True" for r in grp),
                           completed=len(done), completed_hits=sum(r["hit"]=="True" for r in done),
                           median_seconds=round(median(float(r["seconds"]) for r in grp), 4),
                           median_iterations=median(int(r["iterations"]) for r in grp) if method=="mcts" else "")
                if writer is None:
                    writer = csv.DictWriter(f, fieldnames=list(out))
                    writer.writeheader()
                writer.writerow(out)


if __name__ == "__main__":
    main()
