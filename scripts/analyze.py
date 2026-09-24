"""Regenerate report tables and three figures from measured canonical results."""

from __future__ import annotations

import csv
from pathlib import Path
import runpy
import statistics
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.search_baseline.positions import validated_positions

FIGURES = ROOT / "results" / "figures"
GENERATED = ROOT / "report" / "generated"
SHORT = {
    "rook_04": "R4", "rook_pawns_07": "R7", "rook_pawns_11": "R11",
    "pawns_16": "P16", "mixed_16": "M16", "middlegame_24": "M24",
    "initial_32": "S32", "italian_32": "I32",
}
COLORS = ["#237f8c", "#5a9d8f", "#759f49", "#d9952f", "#af3c4c", "#8f63a8", "#356ab3", "#263f60"]


def escape(value: str) -> str:
    return value.replace("\\", r"\textbackslash{}").replace("_", r"\_").replace("&", r"\&").replace("%", r"\%")


def load_rows() -> list[dict]:
    with (ROOT / "experiments" / "search_baseline" / "results.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError("No measured benchmark rows")
    if any(row["status"] == "error" for row in rows):
        raise ValueError("Benchmark has errors; inspect logs before generating report")
    return rows


def condition(rows: list[dict], position_id: str, algorithm: str, budget: int) -> list[dict]:
    field = "search_depth" if algorithm == "minimax" else "mcts_iterations_requested"
    return [row for row in rows if row["position_id"] == position_id and row["algorithm"] == algorithm
            and row[field] == str(budget)]


def complete(group: list[dict]) -> bool:
    return bool(group) and all(row["status"] == "complete" for row in group)


def measure(group: list[dict], field: str = "execution_time_seconds") -> tuple[float, float, float]:
    if not complete(group):
        raise ValueError("Incomplete group cannot provide a completed-budget statistic")
    values = [float(row[field]) for row in group]
    return statistics.median(values), min(values), max(values)


def save_figure(fig, name: str) -> None:
    for extension in ("pdf", "png"):
        path = FIGURES / f"{name}.{extension}"
        fig.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
        print(f"Created {path}")
    plt.close(fig)


def figures(rows: list[dict], positions) -> None:
    plt.rcParams.update({"font.size": 9, "axes.labelsize": 9, "legend.fontsize": 8,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "axes.grid": True, "grid.alpha": 0.18, "pdf.fonttype": 42})
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.6), sharey=True)
    offsets = {"R4": (-16, -13), "R7": (3, 7), "R11": (4, -14), "P16": (4, 7),
               "M16": (4, 5), "M24": (4, 4), "S32": (-25, 4), "I32": (-20, 5)}
    for position, color in zip(positions, COLORS):
        group = condition(rows, position.position_id, "minimax", 3)
        if not complete(group):
            continue
        median, low, high = measure(group)
        for axis, field in zip(axes, ("piece_count", "legal_moves_at_root")):
            x = int(group[0][field])
            axis.errorbar([x], [median], yerr=[[median-low], [high-median]], fmt="o", color=color,
                          capsize=3, markersize=5, elinewidth=1)
            label = SHORT[position.position_id]
            offset = offsets[label]
            if field == "legal_moves_at_root" and label == "R4":
                offset = (0, -16)
            if field == "legal_moves_at_root" and label == "P16":
                offset = (-6, -13)
            axis.annotate(label, (x, median), xytext=offset, textcoords="offset points", fontsize=7)
    axes[0].set_xlabel("Pieces on board")
    axes[1].set_xlabel("Legal moves at root")
    axes[0].set_ylabel("Elapsed seconds (log scale)")
    axes[0].set_yscale("log")
    for axis in axes:
        axis.margins(x=0.13, y=0.2)
    fig.tight_layout(w_pad=1.4)
    save_figure(fig, "runtime_mobility")

    fig, axis = plt.subplots(figsize=(6.5, 2.5))
    for position, color in zip(positions, COLORS):
        depths, nodes = [], []
        for depth in (1, 2, 3, 4):
            group = condition(rows, position.position_id, "minimax", depth)
            if complete(group):
                depths.append(depth)
                nodes.append(measure(group, "nodes_visited")[0])
        axis.plot(depths, nodes, marker="o", markersize=4, color=color, linewidth=1.4,
                  label=SHORT[position.position_id])
    axis.set_yscale("log")
    axis.set_xticks([1, 2, 3, 4])
    axis.set_xlabel("Search depth (plies)")
    axis.set_ylabel("Visited nodes (log scale)")
    axis.legend(ncol=4, loc="upper left", fontsize=7, framealpha=0.9)
    omitted = [SHORT[p.position_id] for p in positions
               if not complete(condition(rows, p.position_id, "minimax", 4))]
    if omitted:
        axis.text(0.99, 0.03, "Depth 4 omitted for incomplete " + ", ".join(omitted), transform=axis.transAxes,
                  ha="right", va="bottom", fontsize=7, color="#555555")
    fig.tight_layout()
    save_figure(fig, "node_growth")

    fig, axis = plt.subplots(figsize=(6.5, 2.5))
    for position, color in zip(positions, COLORS):
        budgets, medians, lows, highs = [], [], [], []
        for budget in (100, 400):
            group = condition(rows, position.position_id, "mcts", budget)
            if complete(group):
                median, low, high = measure(group)
                budgets.append(budget)
                medians.append(median)
                lows.append(median-low)
                highs.append(high-median)
        axis.errorbar(budgets, medians, yerr=[lows, highs], fmt="o-", color=color,
                      linewidth=1.2, markersize=4, capsize=2, label=SHORT[position.position_id])
    axis.set_xticks([100, 400])
    axis.set_xlim(75, 425)
    axis.set_xlabel("MCTS iteration budget")
    axis.set_ylabel("Elapsed seconds")
    axis.set_ylim(bottom=0)
    axis.legend(ncol=4, loc="upper left", fontsize=7, framealpha=0.9)
    fig.tight_layout()
    save_figure(fig, "mcts_budget")


def tables(rows: list[dict], positions) -> None:
    lines = [r"\begin{center}\small", r"\begin{tabular}{llrr}", r"\toprule",
             r"ID & Position & Pieces & Root moves \\", r"\midrule"]
    for position in positions:
        board = position.board()
        lines.append(f"{SHORT[position.position_id]} & {escape(position.label)} & "
                     f"{len(board.piece_map())} & {board.legal_moves.count()} " + r"\\")
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{center}"])
    (GENERATED / "position_table.tex").write_text("\n".join(lines)+"\n", encoding="utf-8")

    lines = [r"\begin{center}\small", r"\setlength{\tabcolsep}{7pt}", r"\begin{tabular}{lrrrrr}",
             r"\toprule", r" & \multicolumn{3}{c}{MinMax depth} & \multicolumn{2}{c}{MCTS iterations} \\",
             r"\cmidrule(lr){2-4}\cmidrule(lr){5-6}", r"ID & 2 & 3 & 4 & 100 & 400 \\", r"\midrule"]
    for position in positions:
        cells = []
        for algorithm, budget in (("minimax", 2), ("minimax", 3), ("minimax", 4), ("mcts", 100), ("mcts", 400)):
            group = condition(rows, position.position_id, algorithm, budget)
            if complete(group):
                cells.append(f"{measure(group)[0]:.3f}")
            else:
                done = sum(row["status"] == "complete" for row in group)
                cells.append(r"\textit{TO}" if done == 0 else f"{done}/{len(group)} done")
        lines.append(SHORT[position.position_id] + " & " + " & ".join(cells) + r" \\")
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{center}",
                  r"{\small\textbf{Table 1.} Median elapsed seconds across three runs per condition. TO means all three searches reached the fifteen-second deadline before completing the requested depth. Timeout durations are censored observations, not full-depth runtimes. Depth-one results and all individual runs remain in the raw CSV.}"])
    (GENERATED / "results_table.tex").write_text("\n".join(lines)+"\n", encoding="utf-8")

    lines = [r"\begingroup\footnotesize"]
    for position in positions:
        lines.append(r"\textbf{" + SHORT[position.position_id] + ": " + escape(position.position_id) + "}\\\\")
        lines.append(r"\texttt{" + position.fen + r"}\par\smallskip")
    lines.append(r"\endgroup")
    (GENERATED / "fens.tex").write_text("\n".join(lines)+"\n", encoding="utf-8")
    for name in ("position_table.tex", "results_table.tex", "fens.tex"):
        print(f"Created {GENERATED / name}")


def main() -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    GENERATED.mkdir(parents=True, exist_ok=True)
    positions = validated_positions()
    rows = load_rows()
    figures(rows, positions)
    tables(rows, positions)
    runpy.run_path(str(ROOT / "scripts" / "report_narrative.py"), run_name="__main__")


if __name__ == "__main__":
    main()
