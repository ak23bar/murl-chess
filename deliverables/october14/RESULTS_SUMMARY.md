# October 14 results summary

All 20 corrected diagrams pass structural legality and exact unique mate-in-three verification. All 100 scheduled baseline searches were attempted; 82 completed and 18 returned explicit timeout fallbacks. There were no oracle timeouts.

| Method | Completed | Key hits among completed | Timeouts | Median completed seconds |
|---|---:|---:|---:|---:|
| Minimax 3 plies | 20/20 | 6/20 | 0 | 0.535 |
| Minimax 5 plies | 2/20 | 2/2 | 18 | 8.195 |
| MCTS 1,000 simulations, seeds 0/1/2 | 60/60 | 9/60 | 0 | 2.724 |

Five-ply completion cases: 16 and 18. Eight additional timeout moves matched the key but are NOT completed-search successes. Three-ply key matches do not prove mate. MCTS matches do not prove forced continuations. MCTS cutoff fraction: 89.56% of 60,000 rollouts.

| Case | Verified key | Minimax 3 | Minimax 5 | MCTS seed 0 | MCTS seed 1 | MCTS seed 2 |
|---:|---|---|---|---|---|---|
| 1 | Nxg7+ | Nf4 | Bf8* | Bb4 | Nxg7+ | g5 |
| 2 | Bf5+ | Be2+ | Bxh7+* | fxe7 | fxe7 | Bf1+ |
| 3 | Ne2+ | Bc3 | Kh7* | Rxg2 | Nh1 | Bc5 |
| 4 | Qd8+ | Qe3 | Qd8+* | Qxe4 | Qxe4 | a3 |
| 5 | Rxg3 | Nf3 | Re7* | Rxg3 | hxg3 | Rxg3 |
| 6 | Qc8+ | Qc8+ | Qc8+* | Qxe6 | Qxe6 | Qxe6 |
| 7 | Ng5 | Ng5 | Ng5* | Kg2 | Qe3 | Qf3 |
| 8 | Qxg8+ | Qf8 | Ne7* | Ne7 | Qb7 | Qf4 |
| 9 | Rxg8+ | Qd6 | Rxg8+* | Qf4 | Qa6 | Rb2 |
| 10 | Rh8+ | Qxh2+ | Rh8+* | Qc5 | Qa6 | Qf8 |
| 11 | Rd8+ | Qe8+ | Ne7+* | Qxb8 | Rxb4 | Qe1 |
| 12 | Rxg7+ | Ne7 | Rxg7+* | Qb6 | Qg1 | Rd7 |
| 13 | Nf6 | Kxd1 | Nf6* | Kxd1 | Kxd1 | Kxd1 |
| 14 | Nd6 | hxg7+ | Qxg7+* | Qe3 | Kh2 | Kf1 |
| 15 | Rxa8 | Rxa8 | Be7* | Rxa8 | Rxa8 | Rxa8 |
| 16 | Rf7 | Kg4 | Rf7 | Rg1 | Kf4 | Ra1 |
| 17 | d8=Q+ | d8=Q+ | Rh6* | Ra6 | a8=Q+ | Rf2 |
| 18 | Rxg7 | Rxg7 | Rxg7 | Rxg7 | Kb1 | Rxg7 |
| 19 | Qg8+ | Qg8+ | Qg8+* | d7 | Qg8+ | Qe2 |
| 20 | c8=Q+ | Rxa7 | Re6* | Rxa7 | Rxa7 | Rxa7 |

An asterisk denotes a timeout. Consult results/results.csv for every individual runtime and completion/success flag. results/summary.csv is the per-position comparison; results/oracle_results.csv contains the exhaustive verification calls. Per-run success is first-move agreement only.

## One representative mating line per position

These examples are not the entire proof. The machine-checked mate_certificates.json covers every defensive reply; the exact root oracle establishes uniqueness and absence of a faster mate.

- 1: Nxg7+ / Kd8 / Qf6+ / Ne7 / Qxe7#
- 2: Bf5+ / Ke8 / Bd7+ / Kf8 / Bxe7#
- 3: Ne2+ / Kb1 / Nc3+ / Kc1 / Ba3#
- 4: Qd8+ / Kxd8 / Bg5+ / Ke8 / Rd8#
- 5: Rxg3 / Bxg3 / Nf3 / Bb8 / g4#
- 6: Qc8+ / Rd8 / Qxd8+ / Re8 / Qxe8#
- 7: Ng5 / g6 / Qd4+ / Rg7 / Re8#
- 8: Qxg8+ / Kxg8 / Ne7+ / Kh8 / Rf8#
- 9: Rxg8+ / Kxg8 / Qe6+ / Kh8 / Qe8#
- 10: Rh8+ / Kxh8 / Qf8+ / Kh7 / Qxg7#
- 11: Rd8+ / Qf8 / Ne7+ / Kh8 / Qh5#
- 12: Rxg7+ / Kh8 / Nh6 / Nh5 / Rg8#
- 13: Nf6 / Ne7 / Rxe7 / Ne3 / Rh7#
- 14: Nd6 / Re8 / Nf7+ / Kg8 / Qxe8#
- 15: Rxa8 / f6 / Bxf6+ / Kf7 / Bg5#
- 16: Rf7 / Kg8 / Rd7 / Kh8 / b8=Q#
- 17: d8=Q+ / Kh7 / Qe7+ / Kh8 / Rf8#
- 18: Rxg7 / Kf8 / Ne6+ / Ke8 / c8=Q#
- 19: Qg8+ / Kh6 / Kg4 / Nc8 / h8=Q#
- 20: c8=Q+ / Kh7 / Qxd7+ / Kh8 / Qg7#
