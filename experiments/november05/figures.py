"""I build my poster figures from the recorded calls and verified defenses."""
import csv
import json
from pathlib import Path
from statistics import median

import chess
import chess.svg
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

NOV = Path("deliverables/november05")
OUT = NOV / "figures"
TEAL, RUST, INK = "#116c67", "#b74824", "#1a3447"


def save(fig, name):
    for ext in ("png", "svg"):
        fig.savefig(OUT / f"{name}.{ext}", dpi=240, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def boards(examples):
    fig, axes = plt.subplots(1, 3, figsize=(11, 4), layout="constrained")
    for ax, e in zip(axes, examples, strict=True):
        board = chess.Board(e["fen"])
        for sq in chess.SQUARES:
            x, y = chess.square_file(sq), chess.square_rank(sq)
            ax.add_patch(Rectangle((x, y), 1, 1, color=("#dce5df", "#f8f3e6")[(x+y)%2]))
            piece = board.piece_at(sq)
            if piece:
                ax.text(x+.5, y+.49, piece.unicode_symbol(), ha="center", va="center",
                        fontsize=27, color="#17242d")
        arrows = []
        for san, color in [(e["key"], TEAL), (e["returned"], RUST)]:
            move = board.parse_san(san)
            arrows.append(chess.svg.Arrow(move.from_square, move.to_square, color=color))
            start, end = [(chess.square_file(s)+.5, chess.square_rank(s)+.5)
                          for s in (move.from_square, move.to_square)]
            ax.annotate("", xy=end, xytext=start, arrowprops=dict(arrowstyle="-|>", color=color,
                        lw=3, alpha=.87, shrinkA=7, shrinkB=4))
        (OUT / f"position-{e['id']:02d}.svg").write_text(chess.svg.board(board, arrows=arrows), encoding="utf8")
        ax.set(xlim=(0,8), ylim=(0,8), aspect="equal", xticks=[i+.5 for i in range(8)],
               yticks=[i+.5 for i in range(8)], xticklabels=list("abcdefgh"), yticklabels=list("12345678"))
        ax.tick_params(length=0, labelsize=9)
        ax.set_title(f"Position {e['id']}   |   White to play", loc="left", color=INK, fontsize=13)
        ax.set_xlabel(f"Key  {e['key']}     /     Played  {e['returned']}", fontsize=12, color=INK)
    save(fig, "decisions")


def timings():
    rows = list(csv.DictReader(Path("deliverables/october14/results/summary.csv").open()))
    xs = [int(row["id"]) for row in rows]
    fig, ax = plt.subplots(figsize=(9, 3.5), layout="constrained")
    ax.scatter(xs, [float(r["minimax_3_seconds"]) for r in rows], color=TEAL, label="Minimax, 3 plies")
    ax.scatter(xs, [median(float(r[f"mcts_seed{s}_seconds"]) for s in range(3)) for r in rows],
               marker="s", color=INK, label="MCTS, median of 3 seeds")
    for done, marker, label in [(True, "D", "Minimax, 5 plies"), (False, "^", "5-ply timeout")]:
        group = [r for r in rows if (r["minimax_5_completed"]=="True")==done]
        ax.scatter([int(r["id"]) for r in group], [float(r["minimax_5_seconds"]) for r in group],
                   marker=marker, color=RUST, label=label)
    ax.axhline(20, color=RUST, lw=.7, alpha=.55)
    ax.set(yscale="log", xticks=xs, xlabel="Corrected puzzle number", ylabel="Wall time (seconds, log scale)")
    ax.legend(loc="upper center", bbox_to_anchor=(.5,1.22), ncol=4, frameon=False, fontsize=9)
    ax.grid(axis="y", alpha=.18)
    save(fig, "runtime")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    boards(json.loads((NOV / "data/defenses.json").read_text()))
    timings()
