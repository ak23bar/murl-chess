# Meeting speaking guide

Akbar Aman | UIC MATH 496 MURL | September 23, 2026, 8:30 PM

## 45-second opening

“I treated this as a baseline experiment rather than two isolated scripts. The study implements plain MinMax and UCT Monte Carlo Tree Search in Python using python-chess. I used eight positions, including equal-piece-count pairs with different mobility, and measured depths one through four and two simulation budgets. The main finding is that piece count alone does not predict cost: branching and depth are much more informative. MCTS lets me budget simulations, but those quick answers are not evidence of strong play. The report and code were prepared with Codex assistance, with the algorithmic references and measured logs included.”

## Five measured observations

1. **144 calls: 135 complete, 9 timeouts, 0 errors.** All timeouts were depth four in the mixed16, middlegame24 and Italian32 positions.
2. **Same sixteen pieces, 41.3x median time difference:** pawn blockade 0.087s versus mixed pieces 3.586s at depth three; 15 versus 53 root moves, 2,978 versus 123,342 nodes.
3. **Same thirty-two pieces:** initial depth three 0.268s versus Italian 1.141s. Initial depth four 6.194s; Italian exceeded the fifteen-second deadline each time.
4. **One extra initial-position ply:** 9,323 to 206,604 nodes, a 22.16x increase.
5. **MCTS depends heavily on its cutoff evaluator:** 97.1% of 12,000 completed simulations reached the forty-ply cap. Moving from 100 to 400 simulations cost 3.03-5.99x median time across fixtures.

## What the code does

- MinMax enumerates all legal continuations to a fixed depth, maximizing for White and minimizing for Black. No pruning is hidden in this baseline.
- MCTS selects using UCT, expands one untried move, runs a bounded random rollout, and propagates White reward. Black selection reverses the reward preference. The most-visited root move is returned.
- Terminal outcomes override material. Legal moves and standard rule handling come from python-chess. Optional draw claims are omitted explicitly.

## Mathematical takeaway

N(d) is roughly 1+b+...+b^d. Looking one ply farther multiplies work by roughly the branching factor b. The root's legal moves only approximate branching deeper in the tree. For MCTS, UCT combines the observed mover reward with sqrt(2)*sqrt(log(parent visits)/child visits), rewarding both good evidence and underexplored alternatives.

## One limitation to say aloud

“This measures runtime, not chess strength. Material-only evaluation and random rollouts can miss tactics. Three timings on one computer do not establish universal cutoffs.” Mixed16 depth-three runs ranged 3.528-9.261s; acknowledge that system variation is visible.

## Likely questions

**Why these positions?** They span 4-32 pieces and include 16/32-piece pairs to expose mobility differences. Six are transparent synthetic controls; two are an actual starting board/opening sequence. They are valid under the library, not a representative sample of games.

**Why these depths and budgets?** Depths 1-4 reveal rapid growth within a same-day experiment. 100/400 iterations reveal MCTS budget scaling. Three repeats, a 40-ply rollout cap and 15-second deadline prevent one case from blocking the study. These settings are baseline choices, not tuned optima.

**Why not simply more pieces = slower?** Piece type, blocked squares, checks and captures alter legal replies. The same amount of material can produce very different search trees.

**Why is Stockfish faster?** Compiled C++ is part of it, but Stockfish also has pruning, ordering, transposition reuse, quiescence and NNUE. This experiment does not isolate a language factor or measure a Stockfish speedup.

**What exactly is the evaluation?** White weighted material minus Black: pawn 1, knight/bishop 3, rook 5, queen 9; kings 0. Detected mate overrides this with +/-10000, draws 0. MCTS maps material to 0.5*(1+tanh(E/10)) at its cap; that is not a win probability.

**How does MCTS differ from MinMax?** MinMax backs up adversarial choices throughout a complete truncated tree. MCTS grows a sampled tree under a simulation budget. It has no guarantee of finding a tactical best move at these budgets.

**What would you improve next?** Add alpha-beta with the same evaluator and verify identical completed-depth values. Then compare evaluations under equal wall-clock budgets; eventually investigate Stockfish-labeled training data and learned evaluation plus search. Those ML stages have not been completed.

**What do timeouts mean?** A legal fallback move is returned and the result is flagged incomplete. It is not called a completed depth-four result. Full-depth runtime and value are unknown for those attempts.

**Why not claim all draws?** This baseline models automatic endings; optional threefold/fifty-move claims would need explicit action handling. FEN omits earlier repetition history. The limitation is documented.

## Screen-share route

Open report/report.pdf first. Use the paired positions and result table, then explain either the MinMax recurrence or UCT equation. Keep src/minimax.py and src/mcts.py available for implementation questions. README has run commands; the full CSV includes every selected move and root visit count.
