"""Build final prose/tables only from the completed and audited experiment."""
import csv
import json
from pathlib import Path

ROOT=Path('deliverables/october14')
BRANCH='https://github.com/ak23bar/murl-chess/tree/october14-corrected-positions'

def tex(s):
    return str(s).replace('&',r'\&').replace('_',r'\_').replace('#',r'\#').replace('%',r'\%')

def main():
    data=json.loads((ROOT/'results/validation.json').read_text())
    assert data['exact_three_unique']==20 and data['raw_records']==160
    extra=json.loads((ROOT/'results/extra_validation.json').read_text())
    assert len(extra['mcts_replays'])==3 and len(extra['castling_sensitivity'])==6
    assert 'OK' in (ROOT/'results/tests.txt').read_text(encoding='utf-8-sig')
    rows=list(csv.DictReader((ROOT/'results/summary.csv').open()))
    raw=[json.loads(l) for l in (ROOT/'results/run1/raw.jsonl').read_text().splitlines()]
    certs=json.loads((ROOT/'results/mate_certificates.json').read_text())
    stats=data['statistics']; m3=stats['minimax_3']; m5=stats['minimax_5']; mc=stats['mcts']
    cutoff=sum(x.get('cutoff_rollouts',0) for x in raw)/60000
    table=[]; mdtable=[]
    for r in rows:
        cells=[r['id'],tex(r['expected_san'])]
        plain=[r['id'],r['expected_san']]
        for key in ['minimax_3','minimax_5','mcts_seed0','mcts_seed1','mcts_seed2']:
            move=tex(r[key+'_move']); star='*' if r[key+'_completed']!='True' else ''
            if r[key+'_hit']=='True': move=r'\textbf{'+move+'}'
            cells.append(move+star)
            plain.append(r[key+'_move']+star)
        table.append(' & '.join(cells)+r' \\')
        mdtable.append('| '+' | '.join(plain)+' |')
    agg=[]
    for label,key in [('Minimax, 3 plies','minimax_3'),('Minimax, 5 plies','minimax_5'),('MCTS, 1,000 simulations','mcts')]:
        s=stats[key]
        agg.append(f"{label} & {s['completed']}/{s['total']} & {s['completed_success']}/{s['completed']} & {s['timeouts']} & {s['median_completed_seconds']:.3f}"+r' \\')
    report=r'''\documentclass[10pt,letterpaper]{article}
\usepackage[margin=0.72in]{geometry}
\usepackage[T1]{fontenc}
\usepackage{lmodern,amsmath,booktabs,xcolor,hyperref,fancyhdr}
\definecolor{navy}{HTML}{19384B}
\hypersetup{colorlinks=true,urlcolor=navy,pdftitle={MURL Chess Results - October 14, 2026},pdfauthor={Akbar Aman}}
\pagestyle{fancy}\fancyhf{}\fancyhead[L]{\small MURL Chess | October 14, 2026}\fancyhead[R]{\small Minimax and MCTS results}\fancyfoot[C]{\thepage}
\setlength{\headheight}{14pt}\setlength{\parindent}{0pt}\setlength{\parskip}{4pt}
\makeatletter
\renewcommand\section{\@startsection{section}{1}{0pt}{10pt}{5pt}{\normalfont\large\bfseries}}
\makeatother
\begin{document}
{\color{navy}\LARGE\bfseries MURL Chess Results: October 14, 2026\par}
{\large Minimax and MCTS on the 20 corrected positions}\par
\textbf{Akbar Aman}\\
For Professors Evangelos Kobotis and Drew Shulman | Meeting: 8:30 PM, America/Chicago

\section*{What I tested and found}
I tested my existing Python implementations of Minimax and Monte Carlo Tree Search (MCTS) on the 20 corrected positions, comparing their first moves with independently verified solutions. Minimax at depth 3 chose the correct first move in \textbf{6/20 positions}; MCTS did so in \textbf{9/60 runs} across three random seeds. My depth-5 Minimax attempts completed only \textbf{2/20 searches}; the other 18 reached the 20-second limit.

\textbf{In everyday terms:} I asked each program to choose the first move of a forced checkmate, then checked its answer. A correct first move does not by itself show that the program can finish the combination. A timeout means I stopped the search before it finished; I report its partial answer separately.

\section*{Why three moves can require five plies}
A \emph{ply} is one player's move. In my Minimax code, depth 3 means \emph{my move, their reply, my next move}. A mate in three attacking moves can require \emph{my move, their reply, my move, their reply, my mating move}: \textbf{five plies}. I therefore retained the requested three-ply runs and also attempted five-ply searches. These measure different amounts of look-ahead.

\section*{How I checked the positions and solutions}
I used only the corrected \texttt{Positions2.pdf}, checking all 1,280 board squares, colors and side markers. Each board is stored as a \emph{FEN}, a compact text description. All 20 passed \texttt{python-chess} validity checks; only case 3 is Black to move. Structural legality does not establish that a position occurred in the named historical game.

For the reference solutions, I used a separate exact AND/OR search to test every legal first move at 1, 3 and 5 plies. It found \textbf{one winning first move per position at five plies, and none at one or three}. The attacker needs \emph{one} move that works, but that move must withstand \emph{every} defensive reply. Formally, for legal moves $L(s)$ and successor $s_m$,
\[
W(s,d)=\bigvee_{m\in L(s)}W(s_m,d-1)\quad\text{(attacker)},\qquad
W(s,d)=\bigwedge_{m\in L(s)}W(s_m,d-1)\quad\text{(defender)}.
\]
Here $W$ means a forced mate within the remaining $d$ plies: defender checkmate is success; other endings or an exhausted horizon are failure. Saved mating strategies were also checked against every defensive reply. The verifier includes quiet moves and all promotions. Its search logic is separate, but it shares the programs' chess-rules library.

\section*{Search settings and measured results}
\textbf{Minimax} looks ahead and assumes the opponent chooses the best reply. At its stopping point, my existing version mainly counts material (P=1, N=B=3, R=5, Q=9; mate=$\pm10000$). \textbf{MCTS} explores sampled continuations and uses their results to guide further exploration. I used 1,000 simulations per run, seeds 0/1/2, UCT exploration constant $\sqrt2$, and random rollouts capped at 40 plies. A seed makes a random run repeatable. MCTS uses a simulation budget, \emph{not a fixed search depth}; its rollout cap is separate from the tree path already explored.

I kept the September implementations unchanged (commit \texttt{046a8d3}). Calls ran serially on Windows with Python 3.12.14 and chess 1.11.2. Each measured search had a 20-second limit; each verifier call had 120 seconds. Times include search overhead, excluding imports and output writing.
\begin{center}\small
\begin{tabular}{lrrrr}\toprule
Method & Completed & Correct/completed & Timeouts & Median seconds$^\dagger$\\\midrule
AGGREGATE
\bottomrule\end{tabular}
\end{center}
{\footnotesize $^\dagger$Completed searches only. The five-ply median represents just cases 16 and 18. These are not equal-time budgets or a general measure of playing strength.}

\newpage
\section*{Results for all 20 positions}
Notation: K=king, Q=queen, R=rook, B=bishop, N=knight; $x$=capture, $+$=check, $=$=promotion. For example, Nxg7+ means a knight captures on g7 with check. \textbf{Bold} marks a correct selection; an asterisk marks a timeout's partial answer. MCTS columns identify the seed.
\begin{center}\small\renewcommand{\arraystretch}{1.08}
\begin{tabular}{rllllll}\toprule
Case & Verified move & Minimax 3 & Minimax 5 & MCTS 0 & MCTS 1 & MCTS 2\\\midrule
RESULT_TABLE
\bottomrule\end{tabular}
\end{center}

\section*{What I conclude from these results}
\textbf{Limited look-ahead matters.} Three-ply Minimax cannot see the full five-ply mating sequence. I interpret its six correct choices as first-move matches, not proof of the entire mate. MCTS's nine matches also do not prove a forced continuation. All 60 MCTS runs finished, but CUTOFF\% of their 60,000 rollouts hit the cap and used a material estimate. Most simulated games therefore ended before a real outcome was available; their scores are not calibrated winning probabilities.

\textbf{Deeper search was costly.} Only cases 16 and 18 finished at five plies; both chose correctly. Eight timeout answers also matched, but I exclude them from completed-search success: 10 matching returned moves do not mean 10 completed solutions. I ran one timing trial per Minimax condition and three MCTS seeds. This small sample, desktop load and fixed run order limit broader comparisons.

\textbf{My next step} is to discuss the intended depth convention, then consider alpha-beta pruning and move ordering to reduce unnecessary Minimax search, and larger MCTS budgets. I have not run neural-network training; that remains the next stage.

\section*{Validation, assumptions, and reproducibility}
Validation includes 16 passing tests, audits of all 160 raw records, and three exact fixed-seed MCTS replays. The reference search ruled out faster mates and other winning first moves; saved strategies check every defensive reply.

I assumed no castling or en-passant rights, clock zero and no earlier repetition history. All six relevant Black castling-right alternatives for cases 1 and 4 preserved the verified moves. Other diagrams permit neither castling nor immediate en-passant. Historical clocks and optional draw claims are outside this experiment.

I preserved the September baseline. The separate branch includes code, FENs, individual runtimes, search counts, raw logs, proof trees and reproduction commands.

{\small\textbf{Repository:} \href{BRANCH_URL}{ak23bar/murl-chess: october14-corrected-positions}.\\
\textbf{References:} Corrected \texttt{Positions2.pdf}, four pages; September baseline and \texttt{references.bib} (AIMA Minimax, Kocsis--Szepesv\'ari UCT, Browne et al. MCTS); \href{https://python-chess.readthedocs.io/en/latest/core.html}{python-chess core documentation}, accessed October 14, 2026.}
\end{document}
'''
    report=report.replace('AGGREGATE','\n'.join(agg)).replace('RESULT_TABLE','\n'.join(table)).replace('CUTOFF',f'{100*cutoff:.1f}').replace('BRANCH_URL',BRANCH)
    (ROOT/'report.tex').write_text(report,encoding='utf-8')
    summary=f'''# October 14 results summary

All 20 corrected diagrams pass structural legality and exact unique mate-in-three verification. All 100 scheduled baseline searches were attempted; 82 completed and 18 returned explicit timeout fallbacks. There were no oracle timeouts.

| Method | Completed | Key hits among completed | Timeouts | Median completed seconds |
|---|---:|---:|---:|---:|
| Minimax 3 plies | 20/20 | 6/20 | 0 | {m3['median_completed_seconds']:.3f} |
| Minimax 5 plies | 2/20 | 2/2 | 18 | {m5['median_completed_seconds']:.3f} |
| MCTS 1,000 simulations, seeds 0/1/2 | 60/60 | 9/60 | 0 | {mc['median_completed_seconds']:.3f} |

Five-ply completion cases: 16 and 18. Eight additional timeout moves matched the key but are NOT completed-search successes. Three-ply key matches do not prove mate. MCTS matches do not prove forced continuations. MCTS cutoff fraction: {100*cutoff:.2f}% of 60,000 rollouts.

| Case | Verified key | Minimax 3 | Minimax 5 | MCTS seed 0 | MCTS seed 1 | MCTS seed 2 |
|---:|---|---|---|---|---|---|
'''+ '\n'.join(mdtable)+'''

An asterisk denotes a timeout. Consult results/results.csv for every individual runtime and completion/success flag. results/summary.csv is the per-position comparison; results/oracle_results.csv contains the exhaustive verification calls. Per-run success is first-move agreement only.

## One representative mating line per position

These examples are not the entire proof. The machine-checked mate_certificates.json covers every defensive reply; the exact root oracle establishes uniqueness and absence of a faster mate.

'''+ '\n'.join(f"- {c['id']}: "+' / '.join(c['longest_example_san']) for c in certs)+'\n'
    (ROOT/'RESULTS_SUMMARY.md').write_text(summary,encoding='utf-8')
    (ROOT/'meeting_notes.md').write_text('''# Speaking notes: October 14, 8:30 PM America/Chicago

## One-minute opening

I used the corrected 20-position file and kept the September algorithms unchanged. With Codex assistance, I transcribed the boards, ran the experiments, and checked each problem using a separate exact mate solver. All 20 have a unique first move that forces mate in three attacking moves.

The depth convention matters: our Minimax depth of three means three individual moves, while these problems can need five plies. At three plies, Minimax chose the correct first move in 6 of 20 cases. MCTS used 1,000 simulations with three seeds per position and chose the key in 9 of 60 runs. Five-ply Minimax completed two positions and timed out on 18 under a 20-second limit. The timeouts are explicitly labeled.

## Points to explain

- A correct first move is different from proving the entire mate. The independent verifier and strategy certificates provide the proof; the measured algorithms provide the comparison.
- MCTS is controlled by simulations, not a fixed depth. Its rollout limit was 40 plies, and about 89.6% of rollouts ended at that limit with a material-based heuristic.
- No positions were silently replaced or repaired. The side to move is White except case 3. All piece squares were checked against the source PDF.
- The five-ply median is based on only cases 16 and 18; it is not representative of all 20. Eight timeout moves happened to match the key but are excluded from completed-search successes.
- The exact oracle uses OR over attacker choices and AND over all defensive replies. It shares python-chess with the baseline, but not the baseline's search code.
- Optional draw claims and historical repetition are not modeled. All potentially relevant Black castling-right alternatives for cases 1 and 4 preserved the expected first move. FEN validity is not a proof that the position occurred historically.

## Demonstration

Case 4: Qd8+ Kxd8 Bg5+ Ke8 Rd8# is one verified line. Explain that the certificate also checks alternative defensive replies. Three-ply Minimax selected Qe3; its five-ply run returned Qd8+ but timed out before finishing the entire root search.

## Questions for the professors

1. Should the next comparison use five plies for Minimax to match the mate-in-three target, or retain the requested three-ply convention?
2. May we add alpha-beta pruning and move ordering as a separately labeled variant?
3. What MCTS simulation budget or wall-time budget should we use for the next comparison?

## Subsequent scope

The supplied Chess_AI_Python.txt was read for context and preserved unchanged; no neural-network training or performance claims are included. Review its representation, turn perspective and learning targets before treating it as a working RL baseline.

## Before the meeting

Review the report and audit checklist, attach the PDF and CSV summary to the draft email, and send before October 14 at 8:30 PM America/Chicago. Authenticate Zoom through SSO > UIC before joining using the invitation. No email has been sent by Codex.
''',encoding='utf-8')
    (ROOT/'email_draft.md').write_text(f'''# UNSENT EMAIL DRAFT

Intended recipients: Professors Evangelos Kobotis and Drew Shulman. Use their verified addresses from the course email thread; addresses have not been guessed. Attach report.pdf and results/summary.csv (optionally results/results.csv or the review ZIP).

Subject: MURL chess results for October 14: corrected 20-position benchmark

Dear Professors Kobotis and Shulman,

Please find attached the results for Minimax and MCTS on all 20 positions in the corrected Positions2.pdf.

The main results are:

- Three-ply Minimax completed all 20 searches and selected the verified winning first move in 6 cases.
- MCTS completed 1,000 simulations for each of three seeds per position and selected the winning first move in 9 of 60 runs.
- Five-ply Minimax completed 2 of 20 searches within the 20-second per-position limit; the remaining 18 are explicitly reported as timeouts.

I distinguished three individual plies from mate in three attacking moves, which can require five plies. A separate exact verifier confirmed a unique mate-in-three first move for each corrected position. The report includes all selected moves, and the accompanying data provide settings, runtimes and completion flags. A correct selected first move is not counted as proof that the measured algorithm found the full mating strategy.

Code, raw results and verification materials are on a separate branch, preserving the September baseline:
{BRANCH}

This package was prepared with Codex assistance for transcription, implementation, execution and drafting. I would appreciate your guidance on the intended depth convention and the next MCTS budget to test. Neural-network work is reserved for the next stage.

Best regards,
Akbar Aman
''',encoding='utf-8')
    (ROOT/'AUDIT_CHECKLIST.md').write_text('''# Audit checklist

## Completed automated and visual checks

- [x] Corrected Positions2.pdf recovered from the referenced user-uploaded conversation; four pages and 20 diagrams. Earlier erroneous set excluded.
- [x] Source PDF and Chess_AI_Python.txt copied without modification; SHA-256 provenance in run1/environment.json.
- [x] All rendered diagrams inspected: colors, squares, board orientation, caption and side marker. All 1,280 squares independently match extracted font glyphs.
- [x] All FENs structurally valid. Case 3 Black to move; other 19 White.
- [x] Exact oracle completed all 60 calls: no wins at 1 or 3 plies, one winning root move at 5 plies in every case. All legal root moves tested.
- [x] Twenty explicit winning-strategy certificates checked against every defensive reply; longest required line five plies.
- [x] Six castling-right alternatives checked for cases 1 and 4; unique keys unchanged. Other positions cannot castle; no legal immediate en-passant capture is possible from the diagrams.
- [x] All 100 baseline runs recorded: 20 Minimax-3, 20 Minimax-5, 60 MCTS. Timeouts separated from completion; no missing/ fabricated rows.
- [x] Raw-to-CSV consistency, legal returned moves, source hashes, rollout and visit accounting checked.
- [x] Fixed-seed replays for cases 1, 3 and 18 matched every root statistic.
- [x] Sixteen tests passed, including sign handling, both colors, deadlines, board preservation, exact-search comparisons and rejection of invalid proof certificates.

## Human review before sending

- [ ] Review report.pdf and RESULTS_SUMMARY.md, especially the 18 five-ply timeouts. Do not describe the 10 returned key matches as 10 completed solutions.
- [ ] Spot-check FENs against the attached corrected PDF, including Black-to-move case 3 and promotion cases 16-20. Machine and Codex checks are complete; this is the user's independent review.
- [ ] Confirm the professors' intended depth convention. The report explicitly includes requested depth=3 plies and bounded five-ply attempts.
- [ ] Decide whether to investigate original game histories. Structural legality and the mate property are verified; historical reachability and captions' game attributions were not independently established.
- [ ] Review assistance attribution and personalize the email. Do not imply that Akbar independently authored or executed the work.
- [ ] Use verified recipient addresses, attach report.pdf and results/summary.csv, and approve/send before October 14, 2026, 8:30 PM America/Chicago. No message was sent automatically.

Publication, PDF visual inspection and archive integrity are recorded separately in final_qa.json, generated after those actions. No unresolved diagram ambiguity was found under the documented FEN conventions. Historical clocks/repetition are unavailable; optional draw claims are outside this study.
''',encoding='utf-8')
    (ROOT/'README.md').write_text(f'''# October 14 review package

Read **report.pdf**, then **RESULTS_SUMMARY.md** and **AUDIT_CHECKLIST.md**. The email draft is **email_draft.md**; it has NOT been sent. Speaking notes are **meeting_notes.md**.

Repository branch: {BRANCH}

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
''',encoding='utf-8')
    Path('START_HERE_OCTOBER14.md').write_text('''# October 14 MURL deliverable

This is the new corrected 20-position experiment. The root README.md and report/ still describe the preserved September 23 baseline.

- [October report](deliverables/october14/report.pdf)
- [Results summary](deliverables/october14/RESULTS_SUMMARY.md)
- [Reproduction and evidence](deliverables/october14/README.md)
- [Human audit checklist](deliverables/october14/AUDIT_CHECKLIST.md)
- [Unsent email draft](deliverables/october14/email_draft.md)
- [Speaking notes](deliverables/october14/meeting_notes.md)

All 20 positions verified; Minimax-3 key matches 6/20; MCTS key matches 9/60; Minimax-5 completed 2/20 with 18 timeouts. Prepared with Codex assistance for Akbar's review. No email sent.
''',encoding='utf-8')
    print('Final report source, results summary, notes, email draft and audit/reproduction guides generated.')

if __name__=='__main__':main()
