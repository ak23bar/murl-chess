# Poster handoff for La Min Aung

**Suggested panel title: Why did the search take the rook?** Use puzzle 6 for the clearest contrast. White has a forced mate in three. Every October MCTS seed took the rook with **Qxe6**. Black's **...Rd8** then prevents a forced mate within the remaining three plies. White's key is **Qc8+**. Against the same rook block **...Rd8**, White plays **Qxd8+ Re8 Qxe8#**. At seed 0 MCTS visited the capture 88 times and the check 56 times. Its final rule chose the more visited move.

| Poster material | Where to find it |
|---|---|
| Research narrative | [Five-page report](../../Reports/MURL_Chess_Research.pdf) |
| Time by puzzle | [Vector chart](figures/runtime.svg) · [PNG](figures/runtime.png) |
| Three annotated boards | [Vector panel](figures/decisions.svg) · [PNG](figures/decisions.png) |
| Individual vector boards | [6 · queen capture](figures/position-06.svg) · [13 · knight capture](figures/position-13.svg) · [16 · promotion threat](figures/position-16.svg) |
| Every puzzle, move, seed, and completion flag | [October comparison table](../october14/RESULTS_SUMMARY.md) · [CSV with FEN and runtime](../october14/results/summary.csv) |
| Shared-time results | [Summary](data/budget_summary.csv) · [160 measured decisions](data/budget.csv) · [environment](data/environment.json) |
| Proof and source checks | [Defensive witnesses](data/defenses.json) · [20 printed and sample lines](data/solutions.json) · [source register](sources/README.md) |

**Runtime caption.** Triangles mark five-ply Minimax calls stopped at 20 seconds. Full-depth time for those puzzles is unknown. MCTS squares summarize three seeds on each board. The vertical axis uses a logarithmic scale.

**Board caption.** Teal arrows show verified keys. Orange arrows show legal moves actually played by MCTS in puzzle 6 and three-ply Minimax in puzzles 13 and 16. In puzzle 13, all three MCTS seeds also chose the orange move. A defensive reply in each case removes the forced mate within the puzzle horizon.

**Results box.** In October, three-ply Minimax matched 6/20 keys; MCTS at 1,000 simulations matched 9/60 across the same 20 boards. Five-ply Minimax finished 2/20, both correct. In November, at ceilings of 0.25 s and 1.00 s, returned-key counts rose from 4 to 5 for Minimax (20 calls each) and from 3 to 6 for MCTS (60 each). Only completed October calls count toward completed-search accuracy.

**Source note for puzzle 18.** Rook and queen promotion both mate on the printed line. The booklet's queen-stalemate explanation is contradicted by replay. The unique key remains Rxg7.

**Attribution.** Akbar Aman contributed these measurements and analyses to the Fall 2026 UIC MATH 496 MURL Chess project. La Min Aung coordinates the group poster. Keep any additional group results labeled with their author, inputs, time budget, seeds, and completion definition.
