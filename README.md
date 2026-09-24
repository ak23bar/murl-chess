# MURL Chess - Experiment 01

**Start with [the report](report/report.pdf) and [meeting notes](docs/meeting_notes.md).**

Prepared for Akbar Aman, UIC MATH 496 MURL, with Evangelos Kobotis and Drew Shulman, September 23, 2026. This study implements plain MinMax and UCT Monte Carlo Tree Search with `python-chess`, then measures runtime across eight deliberate chess positions. It is a pedagogical research baseline, not a competitive engine.

## Setup

Python 3.12 was used; Python 3.10+ is required. From this repository directory:

```sh
python -m venv .venv
```

Activate on Windows PowerShell with `.\.venv\Scripts\Activate.ps1`, or on macOS/Linux with `source .venv/bin/activate`. If PowerShell blocks activation, invoke `.\.venv\Scripts\python.exe` in place of `python`; activation is optional.

```sh
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m experiments.search_baseline.positions
python -m experiments.search_baseline.benchmark --quick
```

The quick run exercises all fixtures and writes only `results/smoke/`. It does not replace the report's measurements. The included `.venv` in this local workspace is already installed; it is excluded from Git and the portable archive.

## Run and reproduce

Individual searches from the repository root:

```sh
python -m src.minimax --depth 3
python -m src.mcts --iterations 400 --seed 0
python -m src.minimax --fen "8/5k2/6r1/8/8/1R6/2K5/8 w - - 0 1" --depth 3
```

These print the selected legal move, score, counts and real elapsed seconds. For a bounded run, add `--max-seconds 15`. The CLI `completed` flag distinguishes full search from a timeout fallback. Terminal positions return `move: null` and an outcome score.

The complete experiment (several minutes; 144 calls):

```sh
python -m experiments.search_baseline.benchmark
python scripts/verify_results.py
python scripts/analyze.py
```

This replaces canonical result files and regenerates figures and report inputs. To retain the supplied run, use:

```sh
python -m experiments.search_baseline.benchmark --output-dir results/rerun
```

The report interprets the supplied September 23 run. If changing conditions, review its prose as well as regenerating tables. Exact wall times depend on the computer and load. Non-timeout deterministic MinMax outputs and fixed-seed MCTS outputs should reproduce under the pinned library versions; wall times need not.

Compile the PDF with [Tectonic](https://tectonic-typesetting.github.io/) installed:

```sh
cd report
tectonic report.tex
```

Tectonic handles BibTeX automatically and may download TeX packages on first use. Alternatively use `latexmk -pdf report.tex` with a complete TeX Live/MiKTeX installation. The prebuilt PDF and generated inputs are included; reading them needs no Python or TeX installation.

## Algorithms and conventions

- **Plain MinMax:** recursive White MAX / Black MIN; material values P=1, N=B=3, R=5, Q=9. Positive scores favor White. Terminal wins are +/-10000, draws zero. Depth counts plies. No alpha-beta, move ordering, transposition table, quiescence, or learned evaluation.
- **MCTS:** selection, expansion, uniform random rollout, backpropagation. UCT uses mover-perspective mean reward plus `sqrt(2)*sqrt(log(parent_visits)/child_visits)`. Stored rewards always favor White; Black selection uses `1-mean_white_reward`. Final move is the most-visited child. Terminal rewards are 1/0.5/0; capped rollouts use `0.5*(1+tanh(material/10))`. These are heuristic utilities, not win probabilities.
- Both preserve the input board and handle library-recognized automatic endings before cutoffs. Optional draw claims are not modeled (`claim_draw=False`). A FEN does not include earlier repetition history. Basic board validity does not prove historical reachability.

## Experimental methodology

Eight positions contain 4, 7, 11, 16, 16, 24, 32 and 32 pieces. Paired material counts expose mobility differences. Six are constructed controls; two come from the initial board and a recorded legal opening. All are White-to-move; tests also cover Black decisions.

MinMax depths 1-4 and MCTS budgets 100/400 use three repetitions, forty-ply rollout limits, and a cooperative 15-second deadline per call. Conditions are shuffled with seed 20260923. MCTS uses seeds 0,1,2; its range includes stochastic-path variation. `perf_counter` timing includes the full search, internal checks/copies and evaluation; it excludes imports, fixture setup, warmup and output writing. No parallel benchmark calls are launched by the runner.

Raw rows are flushed immediately to CSV and JSONL. Summary medians/min/max include completed runs only and explicitly record censoring. Do not interpret a timeout's partial move or score as a full-depth result. The report's operational categories are <=1 second interactive, 1-5 seconds meeting-tolerable, >5 seconds slow for live use. These are descriptive conventions, not playing-strength measures.

MinMax counts all entered tree nodes including the root. MCTS counts stored tree nodes; rollout plies are separate. Its node counts and reward scores are not directly comparable with MinMax's.

## Repository map

```text
src/                          evaluation, MinMax and MCTS
experiments/search_baseline/   fixtures, runner, canonical raw results.csv
tests/                        behavioral correctness tests
scripts/                      result audit and figure/table generation
results/summary.csv           medians, ranges and completion counts
results/figures/               three figures as PDF and PNG
results/logs/                  JSONL, environment/source hashes, QA
report/report.tex, report.pdf  self-contained meeting report
report/generated/             inputs generated from measurements
docs/meeting_notes.md          opening, numerical takeaways, instructor Q&A
docs/reference_notes.md        verified source/claim map
docs/provenance.md             assistance and attribution disclosure
references.bib                bibliography
```

## Attribution and scope

The mutually recursive MinMax structure conceptually adapts the [official AIMA pseudocode](https://github.com/aimacode/aima-pseudocode/blob/master/md/Minimax-Decision.md), whose page is labeled AIMA3e; the fourth-edition textbook provides background. MCTS follows [Browne et al. (2012)](https://doi.org/10.1109/TCIAIG.2012.2186810), with UCT from [Kocsis and Szepesvari (2006)](https://doi.org/10.1007/11871842_29). [Shannon (1950)](https://doi.org/10.1080/14786445008521796) supplies historical context. Rules and legal moves use [python-chess](https://python-chess.readthedocs.io/en/latest/core.html).

No external engine/tutorial implementation was copied. Codex assisted implementation, actual execution, analysis and drafting; see [provenance](docs/provenance.md). The report credits these sources explicitly, and its numbers come from included logs.

[Stockfish 17.1 official source](https://github.com/official-stockfish/Stockfish/tree/03e27488f3d21d8ff4dbf3065603afa21dbd0ef3) is a pinned contextual example of C++, pruning, ordering, transposition tables and NNUE. Stockfish was not benchmarked. The study cannot infer a language speedup or compare chess strength. Engine-supervised data and learned evaluation are future research, not completed work.
