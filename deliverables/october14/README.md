# October 14 review package

Read **report.pdf**, then **RESULTS_SUMMARY.md** and **AUDIT_CHECKLIST.md**. The email draft is **email_draft.md**; it has NOT been sent. Speaking notes are **meeting_notes.md**.

Repository branch: https://github.com/ak23bar/murl-chess/tree/october14-corrected-positions

The original September 23 baseline is preserved at commit 046a8d3c5ad54f7e71f9edbd66083a3fafa04e34. No original tracked file was changed. The new experiment imports the original src/minimax.py and src/mcts.py without edits. New code and prose were prepared by Codex for Akbar's review.

## Reproduce from the repository root

Python 3.12.14 and chess 1.11.2 were used. Install the October-specific requirements in a virtual environment:

```sh
python -m pip install -r experiments/october14/requirements.txt
python -m unittest discover -s tests -v
python -m experiments.october14.extract_glyphs
python -m experiments.october14.audit
```

The last command audits the shipped run and rewrites derived CSVs, not raw measurements. To perform a fresh timed run without replacing supplied evidence:

```sh
python -m experiments.october14.run --output deliverables/october14/results/rerun
python -m experiments.october14.audit --run-dir deliverables/october14/results/rerun --output-dir deliverables/october14/results/rerun_analysis
```

The runner refuses to overwrite an existing raw.jsonl. Calls run serially: per position, oracle horizons 1/3/5, Minimax 3/5, MCTS seeds 0/1/2. There is one Minimax trial per depth and position. Limits are 120 seconds per oracle call and 20 seconds per measured baseline call. MCTS uses 1,000 simulations and a 40-ply rollout cap. Worst-case configured compute is about 153 minutes (60 oracle calls x 120 seconds plus 100 baseline calls x 20 seconds); the supplied complete run took about ten minutes. Exact runtimes and timeout outputs depend on machine/load; non-timeout fixed-seed MCTS outputs should reproduce with pinned versions.

To recheck the supplied evidence and regenerate the report source after validation:

```sh
python -m experiments.october14.certificates
python -m experiments.october14.verify_extra
python -m experiments.october14.build_deliverables
tectonic deliverables/october14/report.tex
```

Certificates, extra validation and the report builder target the supplied run1. A new measured run requires reviewing the report narrative, not merely swapping the CSV. The report builder checks canonical counts; the prose interprets the supplied October 14 results. Re-run tests and save their output to results/tests.txt before rebuilding if needed. The prebuilt PDF is supplied so TeX installation is optional.

## Evidence map

- source/Positions2.pdf: exact corrected input; source/Chess_AI_Python.txt: unchanged subsequent-scope reference, never executed.
- source/extracted_board_glyphs.json: raw PDF chess-font extraction; independent of the hand-entered piece lists.
- results/positions.csv and run1/positions.json: all FENs, piece lists, page numbers and validity status.
- results/run1/raw.jsonl: all 160 raw calls, including full MCTS root statistics. environment.json records software, settings and execution-source SHA-256 hashes.
- results/results.csv: 100 measured searches with runtime, budget/completion, move, score, search effort and correctness flags. Blank seed/plies fields are not applicable.
- results/summary.csv: 20-position comparison; oracle_results.csv: 60 exact solver calls.
- results/mate_certificates.json: one forced winning strategy per case, every defensive reply covered, and representative longest lines.
- results/validation.json, extra_validation.json, tests.txt: data checks, castling sensitivity, replay and behavioral tests.
- final_qa.json and manifest.json: final PDF/package checks and file hashes.

All no-rights FENs use clocks 0/1. These encode a puzzle position, not reconstructed game history. python-chess provides legal moves to both the experiment and verifier. No Stockfish, tablebase or neural-network result is claimed. The local test suite covers both colors, but the source dataset contains only one Black-to-move case.
