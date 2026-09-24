"""Regenerate numerical report prose and the meeting guide from canonical data."""
from pathlib import Path
import csv
import json
import statistics

ROOT = Path(__file__).resolve().parents[1]
G = ROOT / 'report' / 'generated'
G.mkdir(parents=True, exist_ok=True)
rows = list(csv.DictReader((ROOT/'results/summary.csv').open(encoding='utf-8')))
raw = [json.loads(line) for line in (ROOT/'results/logs/benchmark.jsonl').read_text().splitlines()]
env = json.loads((ROOT/'results/logs/environment.json').read_text())
def row(p,a,b):
    return next(r for r in rows if r['position_id']==p and r['algorithm']==a and int(r['search_depth'] or r['mcts_iterations_requested'])==b)
def t(p,a,b): return float(row(p,a,b)['execution_time_seconds_median'])
def n(p,d): return int(float(row(p,'minimax',d)['nodes_visited_median']))
def put(name, text): (G/name).write_text(text+'\n',encoding='utf-8')
put('metrics.tex',r'\newcommand{\RunCount}{'+str(len(raw))+'}')
put('environment.tex',f"Measurements were made on September 23, 2026 (America/Chicago), using {env['cpu_model']}, {env['logical_cpu_count']} logical CPUs available, Windows 11, CPython {env['python'].split()[0]}, \\code{{python-chess}} {env['packages']['python-chess']} (\\code{{chess}} {env['packages']['chess']}). No CPU affinity or frequency control was applied; available logical CPUs do not mean the search was parallelized.")
ratio=t('mixed_16','minimax',3)/t('pawns_16','minimax',3)
node_ratio=n('mixed_16',3)/n('pawns_16',3)
put('findings.tex',f"Of {len(raw)} calls, {env['completed_rows']} completed and {env['timeout_rows']} reached the deadline; {env['error_rows']} execution errors were recorded. All nine timeouts occurred at depth four: all repetitions of the mixed sixteen-piece position, the twenty-four-piece middlegame, and the Italian position. Their full-depth runtimes are unknown.\n\n"
f"The sixteen-piece pair is especially informative. The pawn position has 15 root moves and took {t('pawns_16','minimax',3):.3f} seconds at depth three; the mixed position has 53 and took {t('mixed_16','minimax',3):.3f} seconds, a {ratio:.1f}-fold median difference. Their exact node counts are {n('pawns_16',3):,} and {n('mixed_16',3):,}, a {node_ratio:.1f}-fold workload difference.\n\n"
f"The initial and Italian positions both have 32 pieces, but depth-three medians were {t('initial_32','minimax',3):.3f} and {t('italian_32','minimax',3):.3f} seconds. Initial-position depth four completed in {t('initial_32','minimax',4):.3f} seconds; every Italian depth-four attempt timed out.")
mctsraw=[r for r in raw if r['algorithm']=='mcts']
cut=sum(r['cutoff_rollouts'] for r in mctsraw)
its=sum(r['mcts_iterations'] for r in mctsraw)
ratios=[t(p['position_id'],'mcts',400)/t(p['position_id'],'mcts',100) for p in env['positions']]
mixed=row('mixed_16','minimax',3)
put('growth.tex',f"For the initial position, MinMax visited {n('initial_32',1):,}, {n('initial_32',2):,}, {n('initial_32',3):,}, and {n('initial_32',4):,} nodes at depths one through four. The last step multiplied nodes by {n('initial_32',4)/n('initial_32',3):.2f} and median runtime by {t('initial_32','minimax',4)/t('initial_32','minimax',3):.2f}. This is the practical consequence of an expanding reply tree.\n\n"
f"Increasing MCTS from 100 to 400 iterations multiplied median time by between {min(ratios):.2f} and {max(ratios):.2f} across these positions. Approximately linear budget scaling is a useful expectation, not an exact law from two points. Across all MCTS calls, {cut:,} of {its:,} simulations ({100*cut/its:.1f}\\%) stopped at the rollout cap, showing how strongly this experiment depends on heuristic evaluation.\n\n"
f"Timing variation was substantial in some conditions: mixed-position depth three ranged from {float(mixed['execution_time_seconds_min']):.3f} to {float(mixed['execution_time_seconds_max']):.3f} seconds despite identical node counts. System load or frequency variation is a plausible explanation, not a measured diagnosis. Medians reduce sensitivity to a single slow run; the ranges remain part of the evidence.")
completed=[r for r in rows if r['all_completed']=='True']
inter=sum(float(r['execution_time_seconds_median'])<=1 for r in completed)
toler=sum(1<float(r['execution_time_seconds_median'])<=5 for r in completed)
slow=sum(float(r['execution_time_seconds_median'])>5 for r in completed)
put('practical.tex',f"Across the {len(rows)} position--budget conditions, {inter} had completed-run medians at most one second, {toler} were between one and five seconds, and {slow} exceeded five seconds with all repetitions complete. Three additional conditions timed out on all repetitions. All tested depth-three conditions completed, but that does not make all of them interactive. At depth four, only five of eight positions completed within the deadline in all three trials. All MCTS budgets completed; four hundred simulations remain a small sample of chess continuations.")
notes=f'''# Meeting speaking guide

Akbar Aman | UIC MATH 496 MURL | September 23, 2026, 8:30 PM

## 45-second opening

“I treated this as a baseline experiment rather than two isolated scripts. The study implements plain MinMax and UCT Monte Carlo Tree Search in Python using python-chess. I used eight positions, including equal-piece-count pairs with different mobility, and measured depths one through four and two simulation budgets. The main finding is that piece count alone does not predict cost: branching and depth are much more informative. MCTS lets me budget simulations, but those quick answers are not evidence of strong play. The report and code were prepared with Codex assistance, with the algorithmic references and measured logs included.”

## Five measured observations

1. **{len(raw)} calls: {env['completed_rows']} complete, {env['timeout_rows']} timeouts, {env['error_rows']} errors.** All timeouts were depth four in the mixed16, middlegame24 and Italian32 positions.
2. **Same sixteen pieces, {ratio:.1f}x median time difference:** pawn blockade {t('pawns_16','minimax',3):.3f}s versus mixed pieces {t('mixed_16','minimax',3):.3f}s at depth three; 15 versus 53 root moves, {n('pawns_16',3):,} versus {n('mixed_16',3):,} nodes.
3. **Same thirty-two pieces:** initial depth three {t('initial_32','minimax',3):.3f}s versus Italian {t('italian_32','minimax',3):.3f}s. Initial depth four {t('initial_32','minimax',4):.3f}s; Italian exceeded the fifteen-second deadline each time.
4. **One extra initial-position ply:** {n('initial_32',3):,} to {n('initial_32',4):,} nodes, a {n('initial_32',4)/n('initial_32',3):.2f}x increase.
5. **MCTS depends heavily on its cutoff evaluator:** {100*cut/its:.1f}% of {its:,} completed simulations reached the forty-ply cap. Moving from 100 to 400 simulations cost {min(ratios):.2f}-{max(ratios):.2f}x median time across fixtures.

## What the code does

- MinMax enumerates all legal continuations to a fixed depth, maximizing for White and minimizing for Black. No pruning is hidden in this baseline.
- MCTS selects using UCT, expands one untried move, runs a bounded random rollout, and propagates White reward. Black selection reverses the reward preference. The most-visited root move is returned.
- Terminal outcomes override material. Legal moves and standard rule handling come from python-chess. Optional draw claims are omitted explicitly.

## Mathematical takeaway

N(d) is roughly 1+b+...+b^d. Looking one ply farther multiplies work by roughly the branching factor b. The root's legal moves only approximate branching deeper in the tree. For MCTS, UCT combines the observed mover reward with sqrt(2)*sqrt(log(parent visits)/child visits), rewarding both good evidence and underexplored alternatives.

## One limitation to say aloud

“This measures runtime, not chess strength. Material-only evaluation and random rollouts can miss tactics. Three timings on one computer do not establish universal cutoffs.” Mixed16 depth-three runs ranged {float(mixed['execution_time_seconds_min']):.3f}-{float(mixed['execution_time_seconds_max']):.3f}s; acknowledge that system variation is visible.

## Likely questions

**Why these positions?** They span4-32 pieces and include16/32-piece pairs to expose mobility differences. Six are transparent synthetic controls; two are an actual starting board/opening sequence. They are valid under the library, not a representative sample of games.

**Why these depths and budgets?** Depths1-4 reveal rapid growth within a same-day experiment.100/400 iterations reveal MCTS budget scaling. Three repeats, a40-ply rollout cap and15-second deadline prevent one case from blocking the study. These settings are baseline choices, not tuned optima.

**Why not simply more pieces = slower?** Piece type, blocked squares, checks and captures alter legal replies. The same amount of material can produce very different search trees.

**Why is Stockfish faster?** Compiled C++ is part of it, but Stockfish also has pruning, ordering, transposition reuse, quiescence and NNUE. This experiment does not isolate a language factor or measure a Stockfish speedup.

**What exactly is the evaluation?** White weighted material minus Black: pawn1, knight/bishop3, rook5, queen9; kings0. Detected mate overrides this with +/-10000, draws0. MCTS maps material to0.5*(1+tanh(E/10)) at its cap; that is not a win probability.

**How does MCTS differ from MinMax?** MinMax backs up adversarial choices throughout a complete truncated tree. MCTS grows a sampled tree under a simulation budget. It has no guarantee of finding a tactical best move at these budgets.

**What would you improve next?** Add alpha-beta with the same evaluator and verify identical completed-depth values. Then compare evaluations under equal wall-clock budgets; eventually investigate Stockfish-labeled training data and learned evaluation plus search. Those ML stages have not been completed.

**What do timeouts mean?** A legal fallback move is returned and the result is flagged incomplete. It is not called a completed depth-four result. Full-depth runtime and value are unknown for those attempts.

**Why not claim all draws?** This baseline models automatic endings; optional threefold/fifty-move claims would need explicit action handling. FEN omits earlier repetition history. The limitation is documented.

## Screen-share route

Open report/report.pdf first. Use the paired positions and result table, then explain either the MinMax recurrence or UCT equation. Keep src/minimax.py and src/mcts.py available for implementation questions. README has run commands; the full CSV includes every selected move and root visit count.
'''
for before, after in {
    'span4-32': 'span 4-32', 'include16/32-piece': 'include 16/32-piece',
    'Depths1-4': 'Depths 1-4', 'experiment.100/400': 'experiment. 100/400',
    'a40-ply': 'a 40-ply', 'and15-second': 'and 15-second',
    'pawn1': 'pawn 1', 'knight/bishop3': 'knight/bishop 3', 'rook5': 'rook 5',
    'queen9': 'queen 9', 'kings0': 'kings 0', 'with +/-10000, draws0': 'with +/-10000, draws 0',
    'to0.5': 'to 0.5',
}.items():
    notes = notes.replace(before, after)
(ROOT/'docs/meeting_notes.md').write_text(notes,encoding='utf-8')
print('Generated numerical report narrative and meeting notes from canonical logs.')
