"""Audit saved benchmark evidence without rerunning searches.

From the repository root:
    python scripts/verify_results.py
    python scripts/verify_results.py --output-dir results/smoke

The canonical audit is written to results/logs/validation.json. Alternate
benchmark directories receive their own logs/validation.json. Minimax
determinism here means agreement across completed recorded repetitions;
algorithm correctness is checked separately by tests/test_search.py.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys

import chess


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
from experiments.search_baseline.benchmark import RAW_FIELDS, SUMMARY_FIELDS, summarize
from experiments.search_baseline.positions import validated_positions


class Audit:
    def __init__(self) -> None:
        self.counts: Counter[str] = Counter()
        self.failures: list[str] = []

    def check(self, category: str, condition: bool, description: str) -> bool:
        self.counts[category] += 1
        if not condition:
            self.failures.append(f"{category}: {description}")
        return condition


def read_csv(path: Path, fields: tuple[str, ...]) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != fields:
            raise ValueError(f"Unexpected CSV header: {path}")
        return list(reader)


def csv_value(value: object) -> str:
    """Match csv.DictWriter's representation of the benchmark's scalar values."""
    return "" if value is None else str(value)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit_results(raw_path: Path, output_dir: Path, audit: Audit) -> dict:
    log_path = output_dir / "logs" / "benchmark.jsonl"
    environment_path = output_dir / "logs" / "environment.json"
    summary_path = output_dir / "summary.csv"
    raw = read_csv(raw_path, RAW_FIELDS)
    summary = read_csv(summary_path, SUMMARY_FIELDS)
    records = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    environment = json.loads(environment_path.read_text(encoding="utf-8"))
    audit.check("file_agreement", len(raw) == len(records), "Raw CSV and JSONL row counts differ")
    audit.check("run_complete", bool(environment.get("ended_utc")), "Environment has no completed-run timestamp")
    audit.check("row_uniqueness", len({r["run_id"] for r in records}) == len(records), "Duplicate run IDs")
    audit.check("schedule", [r["scheduled_order"] for r in records] == list(range(1, len(records) + 1)), "Schedule order is not consecutive")
    for index, (csv_row, record) in enumerate(zip(raw, records), start=1):
        if not all(field in record for field in RAW_FIELDS):
            raise ValueError(f"JSONL row {index} is missing required fields")
        for field in RAW_FIELDS:
            audit.check("csv_jsonl_field_agreement", csv_row[field] == csv_value(record[field]), f"Row {index}, field {field}")

    params = environment["parameters"]
    fixtures = {p.position_id: p for p in validated_positions()}
    selected_ids = [p["position_id"] for p in environment["positions"]]
    expected = {(position_id, algorithm, budget, repetition)
                for position_id in selected_ids
                for algorithm, budgets in (("minimax", params["depths"]), ("mcts", params["mcts_budgets"]))
                for budget in budgets for repetition in range(1, params["repetitions"] + 1)}
    actual = {(r["position_id"], r["algorithm"],
               r["search_depth"] if r["algorithm"] == "minimax" else r["mcts_iterations_requested"], r["repetition"])
              for r in records}
    audit.check("schedule", actual == expected and len(records) == len(expected), "Recorded conditions differ from declared complete schedule")
    for position in environment["positions"]:
        fixture = fixtures[position["position_id"]]
        board = fixture.board()
        audit.check("environment_positions", chess.Board(position["fen"]).fen() == board.fen(), f"Environment FEN differs: {fixture.position_id}")
        audit.check("environment_positions", position["piece_count"] == len(board.piece_map()), f"Environment piece count differs: {fixture.position_id}")
        audit.check("environment_positions", position["legal_moves_at_root"] == board.legal_moves.count(), f"Environment mobility differs: {fixture.position_id}")

    minimax_groups: dict[tuple[str, int], list[dict]] = defaultdict(list)
    for record in records:
        run_id = record["run_id"]
        board = chess.Board(record["fen"])
        legal = set(board.legal_moves)
        audit.check("fen_validity", board.is_valid() and not board.is_game_over(claim_draw=False), run_id)
        fixture = fixtures[record["position_id"]]
        audit.check("fixture_agreement", board.fen() == fixture.board().fen(), run_id)
        audit.check("fixture_agreement", record["position_label"] == fixture.label, run_id)
        audit.check("fen_metrics", record["piece_count"] == len(board.piece_map()), f"Piece count: {run_id}")
        audit.check("fen_metrics", record["legal_moves_at_root"] == len(legal), f"Mobility: {run_id}")
        audit.check("fen_metrics", record["side_to_move"] == ("white" if board.turn else "black"), f"Side to move: {run_id}")
        audit.check("status", record["status"] in ("complete", "timeout") and record["error"] == "", f"Error or unknown status: {run_id}")
        audit.check("status", record["completed"] is (record["status"] == "complete"), f"Completion flag: {run_id}")
        audit.check("timing", math.isfinite(record["execution_time_seconds"]) and record["execution_time_seconds"] > 0, run_id)
        audit.check("timing", record["time_limit_seconds"] == params["time_limit"], f"Time limit: {run_id}")
        move = chess.Move.from_uci(record["selected_move"])
        if not audit.check("selected_move_legality", move in legal, run_id):
            continue
        audit.check("san_agreement", record["selected_move_san"] == board.san(move), run_id)
        audit.check("nodes", isinstance(record["nodes_visited"], int) and record["nodes_visited"] >= 1, run_id)
        audit.check("evaluation", math.isfinite(record["evaluation"]), run_id)

        if record["algorithm"] == "minimax":
            audit.check("score_scale", record["score_scale"] == "White pawn units", run_id)
            if record["completed"]:
                minimax_groups[(record["position_id"], record["search_depth"])].append(record)
            continue
        if record["algorithm"] != "mcts":
            audit.check("algorithm", False, run_id)
            continue

        iterations = record["mcts_iterations"]
        visits = json.loads(record["root_visit_information"])
        visit_moves = [chess.Move.from_uci(item["move"]) for item in visits]
        audit.check("mcts_root_moves", set(visit_moves) == legal and len(visit_moves) == len(legal), run_id)
        audit.check("mcts_iterations", 0 <= iterations <= record["mcts_iterations_requested"], run_id)
        audit.check("mcts_iterations", record["completed"] == (iterations == record["mcts_iterations_requested"]), run_id)
        audit.check("mcts_iterations", record["simulations"] == iterations, run_id)
        audit.check("mcts_visits", sum(item["visits"] for item in visits) == iterations, run_id)
        audit.check("mcts_rollouts", record["cutoff_rollouts"] + record["terminal_rollouts"] == iterations, run_id)
        audit.check("mcts_rollouts", min(record["cutoff_rollouts"], record["terminal_rollouts"]) >= 0, run_id)
        audit.check("mcts_rollouts", record["rollout_horizon"] == params["rollout_plies"], run_id)
        audit.check("mcts_rollouts", 0 <= record["rollout_plies_total"] <= iterations * record["rollout_horizon"], run_id)
        audit.check("mcts_nodes", record["nodes_visited"] <= iterations + (1 if record["completed"] else 2), run_id)
        audit.check("mcts_seed", record["seed"] == record["repetition"] - 1, run_id)
        audit.check("score_scale", record["score_scale"] == "White reward [0,1]" and 0 <= record["evaluation"] <= 1, run_id)
        for item in visits:
            count, mean = item["visits"], item["mean_white_reward"]
            audit.check("mcts_visit_values", isinstance(count, int) and count >= 0, f"{run_id}: {item['move']}")
            audit.check("mcts_visit_values", (mean is None if count == 0 else mean is not None and math.isfinite(mean) and 0 <= mean <= 1), f"{run_id}: {item['move']}")
        if iterations:
            selected = next(item for item in visits if item["move"] == record["selected_move"])
            rank = lambda item: (item["visits"], item["mean_white_reward"] if board.turn else 1 - item["mean_white_reward"])
            visited = [item for item in visits if item["visits"]]
            audit.check("mcts_selected_child", rank(selected) == max(map(rank, visited)), run_id)
            audit.check("mcts_selected_child", record["evaluation"] == selected["mean_white_reward"], run_id)

    for key, group in minimax_groups.items():
        reference = group[0]
        for record in group[1:]:
            for field in ("nodes_visited", "evaluation", "selected_move"):
                audit.check("minimax_repeat_determinism", record[field] == reference[field], f"{key}: {field}")

    recalculated = summarize(records)
    audit.check("summary", len(summary) == len(recalculated), "Summary row count")
    for index, (csv_row, calculated) in enumerate(zip(summary, recalculated), start=1):
        for field in SUMMARY_FIELDS:
            audit.check("summary_field_recalculation", csv_row[field] == csv_value(calculated[field]), f"Row {index}: {field}")
    for key, value in (("raw_rows", len(records)),
                       ("completed_rows", sum(r["status"] == "complete" for r in records)),
                       ("timeout_rows", sum(r["status"] == "timeout" for r in records)),
                       ("error_rows", sum(r["status"] == "error" for r in records))):
        audit.check("environment_counts", environment.get(key) == value, key)
    audit.check("no_errors", environment.get("error_rows") == 0, "Benchmark recorded errors")
    for relative_path, digest in environment["code_sha256"].items():
        audit.check("source_hashes", sha256(REPO_ROOT / relative_path) == digest, relative_path)
    return {
        "raw_rows": len(raw), "jsonl_rows": len(records), "summary_rows": len(summary),
        "position_count": len(selected_ids), "minimax_completed_groups": len(minimax_groups),
        "minimax_groups_with_repeated_completed_runs": sum(len(group) > 1 for group in minimax_groups.values()),
        "mcts_rows": sum(r["algorithm"] == "mcts" for r in records),
        "completed_rows": sum(r["status"] == "complete" for r in records),
        "timeout_rows": sum(r["status"] == "timeout" for r in records),
        "input_sha256": {str(path.relative_to(REPO_ROOT)) if path.is_relative_to(REPO_ROOT) else str(path): sha256(path)
                         for path in (raw_path, log_path, summary_path, environment_path)},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output-dir", type=Path, help="Alternative benchmark directory, e.g. results/smoke")
    args = parser.parse_args()
    output_dir = args.output_dir.resolve() if args.output_dir is not None else REPO_ROOT / "results"
    raw_path = output_dir / "results.csv" if args.output_dir is not None else REPO_ROOT / "experiments" / "search_baseline" / "results.csv"
    audit = Audit()
    details = {}
    try:
        details = audit_results(raw_path, output_dir, audit)
    except Exception as exc:
        audit.failures.append(f"Audit stopped: {type(exc).__name__}: {exc}")
    result = {
        "verified_utc": datetime.now(timezone.utc).isoformat(),
        "passed": not audit.failures, "checks_performed": sum(audit.counts.values()),
        "check_counts": dict(sorted(audit.counts.items())), "failures": audit.failures,
        "scope": "Saved-output consistency, legality, recorded-repetition determinism, and summary recomputation; no search reruns",
        **details,
    }
    validation_path = output_dir / "logs" / "validation.json"
    validation_path.parent.mkdir(parents=True, exist_ok=True)
    validation_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"{'PASS' if result['passed'] else 'FAIL'}: {result['checks_performed']} checks; {len(audit.failures)} failures")
    print(f"Validation record: {validation_path}")
    for failure in audit.failures[:10]:
        print(f"  {failure}")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
