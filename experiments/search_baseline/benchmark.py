"""Measure separately implemented MinMax and MCTS using wall-clock time.

Run from the repository root with:
    python -m experiments.search_baseline.benchmark
    python -m experiments.search_baseline.benchmark --quick

Raw records are written and flushed immediately. Incomplete searches are retained
and flagged, never passed off as completed-budget results. Summary timing columns
use only completed runs; an additional all-run median preserves censored timings.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import random
import statistics
import sys
import time
from datetime import datetime, timezone

import chess

from experiments.search_baseline.positions import Position, validated_positions
from src.mcts import mcts
from src.minimax import minimax


REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_FIELDS = (
    "run_id", "scheduled_order", "position_id", "position_label", "fen",
    "side_to_move", "piece_count", "legal_moves_at_root", "algorithm",
    "search_depth", "mcts_iterations_requested", "mcts_iterations", "repetition",
    "seed", "nodes_visited", "simulations", "execution_time_seconds", "selected_move",
    "selected_move_san", "evaluation", "score_scale", "completed", "status",
    "cutoff_rollouts", "terminal_rollouts", "rollout_plies_total", "rollout_horizon",
    "time_limit_seconds", "root_visit_information", "error",
)
SUMMARY_FIELDS = (
    "position_id", "position_label", "piece_count", "legal_moves_at_root", "algorithm",
    "search_depth", "mcts_iterations_requested", "n_runs", "n_completed", "n_timeouts",
    "n_errors", "all_completed", "execution_time_seconds_median", "execution_time_seconds_min",
    "execution_time_seconds_max", "execution_time_seconds_all_runs_median",
    "nodes_visited_median", "mcts_iterations_median", "cutoff_rollouts_median",
    "terminal_rollouts_median", "rollout_plies_total_median", "selected_moves", "evaluations",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def code_hashes() -> dict[str, str]:
    paths = sorted((REPO_ROOT / "src").glob("*.py")) + sorted(Path(__file__).parent.glob("*.py"))
    return {path.relative_to(REPO_ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in paths}


def cpu_model() -> str:
    """Best-effort human-readable model; timing logic is platform-independent."""
    if sys.platform == "win32":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as key:
                return winreg.QueryValueEx(key, "ProcessorNameString")[0].strip()
        except OSError:
            pass
    return platform.processor() or "unavailable"


def environment(args: argparse.Namespace, positions: tuple[Position, ...]) -> dict:
    packages = {}
    for package in ("python-chess", "chess", "matplotlib", "numpy"):
        try:
            packages[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            packages[package] = "not installed"
    return {
        "started_utc": utc_now(), "python": sys.version, "python_executable": sys.executable,
        "operating_system": platform.platform(), "machine": platform.machine(),
        "processor": platform.processor(), "cpu_model": cpu_model(),
        "processor_identifier": os.environ.get("PROCESSOR_IDENTIFIER", "unavailable"),
        "logical_cpu_count": os.cpu_count(), "packages": packages,
        "timer": "time.perf_counter; external elapsed wall-clock seconds around each search call",
        "timer_resolution_seconds": time.get_clock_info("perf_counter").resolution,
        "timing_includes": "Search, algorithm input-validity guard, board copies made inside algorithm, move generation, terminal detection, evaluation",
        "timing_excludes": "Imports, fixture construction and pre-search fixture validation, output formatting, CSV/JSON writes, warm-up",
        "claim_draw": False,
        "command": [sys.executable, "-m", "experiments.search_baseline.benchmark", *sys.argv[1:]],
        "parameters": {key: str(value) if isinstance(value, Path) else value
                       for key, value in vars(args).items()},
        "warmup": "One unrecorded MinMax depth-1 call and one unrecorded MCTS 2-iteration call on first position",
        "schedule": "All conditions and repetitions shuffled with independent schedule_seed",
        "summary_policy": "Median/min/max among completed searches only; incomplete rows retained and counted",
        "node_count_semantics": {"minimax": "Root plus all entered recursive nodes",
                                 "mcts": "Allocated tree nodes including root; excludes rollout positions"},
        "seed_policy": "MCTS repetition r uses seed r-1; timing spread includes random rollout-path variation",
        "rollout_plies_semantics": "Sum of rollout plies in completed MCTS simulations only",
        "code_sha256": code_hashes(),
        "positions": [{"position_id": p.position_id, "label": p.label, "fen": p.fen,
                       "piece_count": p.expected_piece_count, "legal_moves_at_root": p.board().legal_moves.count(),
                       "rationale": p.rationale, "provenance": p.provenance} for p in positions],
    }


def run_one(position: Position, algorithm: str, budget: int, repetition: int,
            order: int, args: argparse.Namespace) -> dict:
    board = position.board()
    original_fen, original_stack = board.fen(), list(board.move_stack)
    row = {field: "" for field in RAW_FIELDS}
    row.update({
        "run_id": f"{position.position_id}_{algorithm}_{budget}_r{repetition}",
        "scheduled_order": order, "position_id": position.position_id,
        "position_label": position.label, "fen": board.fen(),
        "side_to_move": "white" if board.turn else "black",
        "piece_count": len(board.piece_map()), "legal_moves_at_root": board.legal_moves.count(),
        "algorithm": algorithm, "repetition": repetition, "time_limit_seconds": args.time_limit,
        "search_depth": budget if algorithm == "minimax" else "",
        "mcts_iterations_requested": budget if algorithm == "mcts" else "",
        "seed": repetition - 1 if algorithm == "mcts" else "",
        "rollout_horizon": args.rollout_plies if algorithm == "mcts" else "",
    })
    start = time.perf_counter()
    try:
        if algorithm == "minimax":
            result = minimax(board, depth=budget, max_seconds=args.time_limit)
        else:
            result = mcts(board, iterations=budget, seed=repetition - 1,
                          rollout_plies=args.rollout_plies, max_seconds=args.time_limit)
        elapsed = time.perf_counter() - start
        row["execution_time_seconds"] = elapsed
        if board.fen() != original_fen or list(board.move_stack) != original_stack:
            raise AssertionError("Search modified its input board")
        if result.move is None or result.move not in board.legal_moves:
            raise AssertionError("Nonterminal benchmark search failed to return a legal move")
        row.update({"nodes_visited": result.nodes, "selected_move": result.move.uci(),
                    "selected_move_san": board.san(result.move), "evaluation": result.score,
                    "completed": result.completed, "status": "complete" if result.completed else "timeout",
                    "score_scale": "White pawn units" if algorithm == "minimax" else "White reward [0,1]"})
        if algorithm == "mcts":
            visits = [{"move": visit.move.uci(), "visits": visit.visits,
                       "mean_white_reward": visit.mean_white_reward} for visit in result.root_visits]
            if sum(visit["visits"] for visit in visits) != result.iterations:
                raise AssertionError("Root child visits do not equal completed simulations")
            if result.cutoff_rollouts + result.terminal_rollouts != result.iterations:
                raise AssertionError("Rollout outcome counts do not equal completed simulations")
            row.update({"mcts_iterations": result.iterations, "simulations": result.iterations,
                        "cutoff_rollouts": result.cutoff_rollouts, "terminal_rollouts": result.terminal_rollouts,
                        "rollout_plies_total": result.rollout_plies,
                        "root_visit_information": json.dumps(visits, separators=(",", ":"))})
    except Exception as exc:
        if row["execution_time_seconds"] == "":
            row["execution_time_seconds"] = time.perf_counter() - start
        row.update({"completed": False, "status": "error", "error": f"{type(exc).__name__}: {exc}"})
    return row


def summarize(rows: list[dict]) -> list[dict]:
    groups: dict[tuple, list[dict]] = {}
    for row in rows:
        key = (row["position_id"], row["algorithm"], row["search_depth"], row["mcts_iterations_requested"])
        groups.setdefault(key, []).append(row)
    summaries = []
    for key in sorted(groups, key=lambda item: (item[0], item[1], str(item[2]), str(item[3]))):
        group = groups[key]
        finished = [row for row in group if row["status"] == "complete"]
        first = group[0]
        summary = {field: "" for field in SUMMARY_FIELDS}
        for field in ("position_id", "position_label", "piece_count", "legal_moves_at_root", "algorithm",
                      "search_depth", "mcts_iterations_requested"):
            summary[field] = first[field]
        times = [row["execution_time_seconds"] for row in finished]
        summary.update({
            "n_runs": len(group), "n_completed": len(finished),
            "n_timeouts": sum(row["status"] == "timeout" for row in group),
            "n_errors": sum(row["status"] == "error" for row in group),
            "all_completed": len(finished) == len(group),
            "execution_time_seconds_median": statistics.median(times) if times else "",
            "execution_time_seconds_min": min(times) if times else "",
            "execution_time_seconds_max": max(times) if times else "",
            "execution_time_seconds_all_runs_median": statistics.median(row["execution_time_seconds"] for row in group),
            "selected_moves": json.dumps([row["selected_move"] for row in sorted(finished, key=lambda r: r["repetition"])]),
            "evaluations": json.dumps([row["evaluation"] for row in sorted(finished, key=lambda r: r["repetition"])]),
        })
        for field in ("nodes_visited", "mcts_iterations", "cutoff_rollouts", "terminal_rollouts", "rollout_plies_total"):
            values = [row[field] for row in finished if row[field] != ""]
            summary[f"{field}_median"] = statistics.median(values) if values else ""
        summaries.append(summary)
    return summaries


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--quick", action="store_true", help="All 8 fixtures, depths 1/2, MCTS 10, one repeat; writes results/smoke")
    parser.add_argument("--depths", nargs="+", type=int, default=[1, 2, 3, 4])
    parser.add_argument("--mcts-budgets", nargs="+", type=int, default=[100, 400])
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--rollout-plies", type=int, default=40)
    parser.add_argument("--time-limit", type=float, default=15.0, help="Cooperative wall-clock deadline per search (seconds)")
    parser.add_argument("--schedule-seed", type=int, default=20260923)
    parser.add_argument("--positions", nargs="+", help="Optional fixture IDs; all positions by default")
    parser.add_argument("--output-dir", type=Path, help="Alternate output directory; avoids overwriting canonical experiment results")
    args = parser.parse_args(argv)
    if args.quick:
        args.depths, args.mcts_budgets, args.repetitions = [1, 2], [10], 1
    if any(value < 1 for value in args.depths + args.mcts_budgets):
        parser.error("Depths and MCTS budgets must be positive")
    if args.repetitions < 1 or args.rollout_plies < 1 or args.time_limit <= 0:
        parser.error("Repetitions, rollout plies and time limit must be positive")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    positions = validated_positions()
    if args.positions:
        unknown = set(args.positions) - {p.position_id for p in positions}
        if unknown:
            raise SystemExit(f"Unknown positions: {sorted(unknown)}")
        positions = tuple(p for p in positions if p.position_id in args.positions)
    if args.output_dir is not None:
        output_dir = args.output_dir.resolve()
        raw_path = output_dir / "results.csv"
    elif args.quick:
        output_dir = REPO_ROOT / "results" / "smoke"
        raw_path = output_dir / "results.csv"
    else:
        output_dir = REPO_ROOT / "results"
        raw_path = REPO_ROOT / "experiments" / "search_baseline" / "results.csv"
    summary_path = output_dir / "summary.csv"
    log_path = output_dir / "logs" / "benchmark.jsonl"
    environment_path = output_dir / "logs" / "environment.json"
    for path in (raw_path, summary_path, log_path, environment_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    metadata = environment(args, positions)
    write_json(environment_path, metadata)
    warm_board = positions[0].board()
    minimax(warm_board, depth=1, max_seconds=args.time_limit)
    mcts(warm_board, iterations=2, seed=999, rollout_plies=args.rollout_plies, max_seconds=args.time_limit)
    schedule = [(p, algorithm, budget, repetition)
                for p in positions
                for algorithm, budgets in (("minimax", args.depths), ("mcts", args.mcts_budgets))
                for budget in budgets for repetition in range(1, args.repetitions + 1)]
    random.Random(args.schedule_seed).shuffle(schedule)
    rows = []
    started = time.perf_counter()
    with raw_path.open("w", newline="", encoding="utf-8") as raw_file, log_path.open("w", encoding="utf-8") as log_file:
        writer = csv.DictWriter(raw_file, fieldnames=RAW_FIELDS)
        writer.writeheader()
        for order, (position, algorithm, budget, repetition) in enumerate(schedule, start=1):
            row = run_one(position, algorithm, budget, repetition, order, args)
            rows.append(row)
            writer.writerow(row)
            raw_file.flush()
            log_file.write(json.dumps({"recorded_utc": utc_now(), **row}) + "\n")
            log_file.flush()
            print(f"[{order:3d}/{len(schedule)}] {row['run_id']}: {row['execution_time_seconds']:.6f}s "
                  f"{row['status']} move={row['selected_move']} nodes={row['nodes_visited']}", flush=True)
    with summary_path.open("w", newline="", encoding="utf-8") as summary_file:
        writer = csv.DictWriter(summary_file, fieldnames=SUMMARY_FIELDS)
        writer.writeheader()
        writer.writerows(summarize(rows))
    metadata.update({"ended_utc": utc_now(), "benchmark_elapsed_seconds": time.perf_counter() - started,
                     "raw_rows": len(rows), "completed_rows": sum(row["status"] == "complete" for row in rows),
                     "timeout_rows": sum(row["status"] == "timeout" for row in rows),
                     "error_rows": sum(row["status"] == "error" for row in rows)})
    write_json(environment_path, metadata)
    print(f"Raw results: {raw_path}\nSummary: {summary_path}\nEnvironment: {environment_path}", flush=True)
    return 1 if any(row["status"] == "error" for row in rows) else 0


if __name__ == "__main__":
    raise SystemExit(main())
