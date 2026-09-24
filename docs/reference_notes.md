# Reference verification and attribution

Verified on 23 September 2026. These are references for the algorithms and the comparison context, not benchmark data. All experimental numbers must come from this repository's actual run outputs.

The implementations are written for this experiment from the cited algorithmic descriptions. The plain alternating MAX/MIN recursion follows AIMA's published pseudocode conceptually, with chess legality delegated to `python-chess` and with an explicit depth cutoff. The MCTS design follows the selection, expansion, simulation, and backpropagation organization described by Browne et al. and UCT selection by Kocsis and Szepesvari. These algorithmic sources should be credited in the README, source module comments, and report. No third-party engine or tutorial implementation is presented as original work. Record any later copied or adapted source separately if that changes.

## Claim-to-source map

| Bibliography key | Role in the report | Verified primary/authoritative source |
|---|---|---|
| `shannon1950` | Historical motivation: chess programming through search and position evaluation. | [Publisher metadata](https://www.tandfonline.com/doi/abs/10.1080/14786445008521796); [paper preserved by Computer History Museum](https://archive.computerhistory.org/projects/chess/related_materials/text/2-0%20and%202-1.Programming_a_computer_for_playing_chess.shannon/2-0%20and%202-1.Programming_a_computer_for_playing_chess.shannon.062303002.pdf). |
| `aima2021` | Adversarial search, minimax, alpha-beta, cutoff evaluation, and exponential growth. | [Official book website](https://aima.cs.berkeley.edu/); [publisher front matter confirming edition, authors, ISBN and 2021 bibliographic year](https://www.pearsonhighered.com/assets/preface/0/1/3/4/0134610997.pdf). |
| `aimaPseudocode` | Concrete conceptual source for the mutually recursive MAX/MIN baseline. | [Official companion pseudocode](https://github.com/aimacode/aima-pseudocode/blob/master/md/Minimax-Decision.md); [alpha-beta pseudocode](https://github.com/aimacode/aima-pseudocode/blob/master/md/Alpha-Beta-Search.md). These files explicitly identify AIMA3e. |
| `kocsis2006` | UCT applies exploration/exploitation bandit selection within search trees. | [Springer chapter and metadata](https://link.springer.com/chapter/10.1007/11871842_29); [author-hosted paper](https://sites.ualberta.ca/~szepesva/papers/ecml06.pdf), especially sections 2.2--2.4. |
| `browne2012` | Standard MCTS stages, choices of tree/default policy and final action. | [Author institutional repository record](https://repository.essex.ac.uk/4117/); [institutional full text](https://repository.essex.ac.uk/4117/1/MCTS-Survey.pdf). Published pagination is 1--43; the repository PDF has additional pages. |
| `pythonChess` | Legal moves, FEN parsing, make/unmake, validity checks and game outcomes. | [Official core API](https://python-chess.readthedocs.io/en/latest/core.html); [overview and installation](https://python-chess.readthedocs.io/en/latest/). |
| `stockfish2025` | Illustrative modern engine source: compiled C++, selective search, ordering, transposition table and NNUE. | [Release announcement](https://stockfishchess.org/blog/2025/stockfish-17-1/); [verified release commit](https://github.com/official-stockfish/Stockfish/commit/03e27488f3d21d8ff4dbf3065603afa21dbd0ef3). |

## Exact Stockfish evidence

Use version 17.1 as a pinned example, not as a claim about the latest release. Release tag `sf_17.1` resolves to `03e27488f3d21d8ff4dbf3065603afa21dbd0ef3` (30 March 2025).

- [search.cpp](https://github.com/official-stockfish/Stockfish/blob/03e27488f3d21d8ff4dbf3065603afa21dbd0ef3/src/search.cpp): iterative deepening, alpha/beta search windows, beta cutoffs, transposition-table probes, quiescence search, futility pruning, null-move search and ProbCut.
- [movepick.cpp](https://github.com/official-stockfish/Stockfish/blob/03e27488f3d21d8ff4dbf3065603afa21dbd0ef3/src/movepick.cpp): orders captures and quiet moves using capture values and history information; prioritizes the transposition-table move.
- [tt.h](https://github.com/official-stockfish/Stockfish/blob/03e27488f3d21d8ff4dbf3065603afa21dbd0ef3/src/tt.h): transposition-table interface.
- [README.md](https://github.com/official-stockfish/Stockfish/blob/03e27488f3d21d8ff4dbf3065603afa21dbd0ef3/README.md): NNUE network file and compiled builds.
- [Official release announcement](https://stockfishchess.org/blog/2025/stockfish-17-1/): explicitly identifies the engine code as C++.

These establish differences in implementation and search design. They do not establish a numerical speed ratio between Python and C++. This study does not run Stockfish and cannot isolate the effect of programming language from algorithms, data structures, compiler optimization, and evaluation choices.

## Interpretation cautions

- Shannon's article is from **1950**, not 2009 (the publisher's online posting date). The journal title includes “London, Edinburgh, and Dublin”; volume 41, issue 314, pages 256--275. DOI: `10.1080/14786445008521796`.
- AIMA's fourth US edition has a 2021 bibliographic/copyright year. Do not call the online `AIMA3e` pseudocode “fourth-edition Figure 5.x.” The old chapter PDF at `/4th-ed/pdfs/newchap06.pdf` contains older numbering and content; it should not be cited as the final fourth-edition chapter.
- The UCT paper supplies conditional theoretical results for specified finite-horizon/discounted settings. A finite-budget chess search with truncated random rollouts and material scoring does not inherit a guarantee of choosing the optimal chess move. The exploration constant depends on the reward scaling convention. Explain the actual code's convention.
- `Board.is_valid()` checks basic position validity; it does not prove a complete legal game can reach an arbitrary constructed FEN. A FEN also omits pre-FEN repetition history. Describe synthetic FENs as constructed test positions unless a legal move sequence is supplied.
- `Board.outcome(claim_draw=False)` handles automatic endings; claimable threefold and fifty-move draws require `claim_draw=True`. Preserve and state whichever draw policy the implementation actually uses. `python-chess` also documents limits of its insufficient-material detector for certain dead positions.
- Runtime feasibility and playing strength are different outcomes. Budgeted MCTS and fixed-depth minimax do different amounts of work and do not have equal-quality guarantees. Material-based rollout scores are heuristic utilities, not calibrated win probabilities.
- No source here establishes a universal piece-count threshold or language speedup. Those should not be reported as findings from this small benchmark.
