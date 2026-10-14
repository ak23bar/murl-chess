# Speaking notes: October 14, 8:30 PM America/Chicago

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
