"""Bounded serial measurements, flushed after each call; never overwrites a run."""
import argparse
import csv
import hashlib
import json
import platform
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime, timezone
import chess
from src.minimax import minimax
from src.mcts import mcts
from .positions import positions
from .oracle import solve

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--oracle-seconds', type=float, default=120)
    ap.add_argument('--search-seconds', type=float, default=20)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    if (args.output/'raw.jsonl').exists():
        raise SystemExit('Existing run preserved. Choose a new output directory.')
    fixtures = positions()
    (args.output/'positions.json').write_text(json.dumps(fixtures, indent=2))
    paths = list(Path('src').glob('*.py')) + list(Path('experiments/october14').glob('*.py')) + list(Path('deliverables/october14/source').glob('*'))
    env = dict(utc_start=datetime.now(timezone.utc).isoformat(), python=sys.version,
               platform=platform.platform(), processor=platform.processor(), chess=chess.__version__,
               baseline='046a8d3c5ad54f7e71f9edbd66083a3fafa04e34',
               source_sha256={p.as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
               settings=dict(oracle_seconds=args.oracle_seconds, search_seconds=args.search_seconds,
                             mcts_iterations=1000, seeds=[0,1,2], rollout_cap=40,
                             order='position ascending; oracle 1,3,5; minimax 3,5; MCTS seeds 0,1,2',
                             timings='serial wall seconds; imports and file writing excluded'))
    (args.output/'environment.json').write_text(json.dumps(env, indent=2))
    with (args.output/'raw.jsonl').open('w') as stream:
        def emit(row):
            stream.write(json.dumps(row)+'\n'); stream.flush()
            print(json.dumps({k:v for k,v in row.items() if k not in ('tested_root_moves','root_visits')}), flush=True)
        for p in fixtures:
            b = chess.Board(p['fen'])
            if not b.is_valid():
                emit(dict(id=p['id'], algorithm='invalid', status=p['validity_status']))
                continue
            for depth in (1,3,5):
                emit(dict(id=p['id'], algorithm='oracle', **solve(b, depth, args.oracle_seconds)))
            for depth in (3,5):
                t = time.perf_counter()
                r = minimax(b, depth, args.search_seconds)
                emit(dict(id=p['id'], algorithm='minimax', plies=depth, move=r.move.uci() if r.move else None,
                          san=b.san(r.move) if r.move else None, score=r.score, nodes=r.nodes,
                          completed=r.completed, seconds=time.perf_counter()-t))
            for seed in (0,1,2):
                t = time.perf_counter()
                r = mcts(b, 1000, seed=seed, rollout_plies=40, max_seconds=args.search_seconds)
                emit(dict(id=p['id'], algorithm='mcts', seed=seed, requested_iterations=1000,
                          iterations=r.iterations, move=r.move.uci() if r.move else None,
                          san=b.san(r.move) if r.move else None, score=r.score, nodes=r.nodes,
                          completed=r.completed, seconds=time.perf_counter()-t,
                          cutoff_rollouts=r.cutoff_rollouts, terminal_rollouts=r.terminal_rollouts,
                          rollout_plies=r.rollout_plies,
                          root_visits=[dict(move=v.move.uci(),visits=v.visits,mean=v.mean_white_reward) for v in r.root_visits]))

if __name__ == '__main__':
    main()
