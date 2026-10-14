# UNSENT EMAIL DRAFT

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
https://github.com/ak23bar/murl-chess/tree/october14-corrected-positions

This package was prepared with Codex assistance for transcription, implementation, execution and drafting. I would appreciate your guidance on the intended depth convention and the next MCTS budget to test. Neural-network work is reserved for the next stage.

Best regards,
Akbar Aman
