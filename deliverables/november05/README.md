# My poster contribution for Min and the group

I have organized my findings around the three questions we discussed on October 31 and Min circulated in his follow-up email. I used the same 20 corrected mate-in-three problems for the puzzle results. My September study provides additional runtime context. I am sharing these materials for our November 5 handoff so we can compare our findings and decide what belongs on our poster.

I suggest **“Why did the search take the rook?”** as a panel title for puzzle 6. In all three October MCTS trials, I recorded **Qxe6**, although White has a forced mate in three. I verified that Black's **...Rd8** prevents mate within the remaining three plies. The correct key is **Qc8+**. Against the same **...Rd8**, White has **Qxd8+ Re8 Qxe8#**. At seed 0, I recorded 88 visits to the capture and 56 to the key, which explains my implementation's final visit-based choice.

| Material I am sharing | Location |
|---|---|
| Concise group findings | [Google Doc](https://docs.google.com/document/d/10VYO_vFpFaVLsv9ceS01ASPTvwlAWUAKpZGiy-NSOWQ) · [PDF snapshot](../../Reports/MURL_Chess_Group_Findings.pdf) · [Markdown](../../Reports/MURL_Chess_Group_Findings.md) |
| Comprehensive research narrative | [Five-page report](../../Reports/MURL_Chess_Research.pdf) |
| Time by puzzle | [Vector chart](figures/runtime.svg) · [PNG](figures/runtime.png) |
| Three annotated boards | [Vector panel](figures/decisions.svg) · [PNG](figures/decisions.png) |
| Individual vector boards | [6 · queen capture](figures/position-06.svg) · [13 · knight capture](figures/position-13.svg) · [16 · promotion threat](figures/position-16.svg) |
| Every puzzle, move, seed, and completion flag | [My October comparison](../october14/RESULTS_SUMMARY.md) · [CSV with FENs and runtimes](../october14/results/summary.csv) |
| Shared time ceilings | [My summary](data/budget_summary.csv) · [160 measured decisions](data/budget.csv) · [environment](data/environment.json) |
| Verification | [Defensive witnesses](data/defenses.json) · [20 printed and sample lines](data/solutions.json) · [source register](sources/README.md) |

## Captions I suggest for the figures

**Runtime.** I marked five-ply Minimax calls stopped at 20 seconds with triangles. Their full-depth times are unknown. The MCTS squares summarize three seeds per board, and I used a logarithmic vertical axis.

**Boards.** I marked verified keys with teal arrows and recorded mistakes with orange arrows. The orange moves came from my MCTS runs in puzzle 6 and my three-ply Minimax runs in puzzles 13 and 16. In puzzle 13, all three MCTS seeds also chose the orange move. I verified a defensive reply in each case that prevents mate within the remaining horizon.

## Findings I suggest highlighting

In October, I recorded 6/20 correct keys for three-ply Minimax and 9/60 for MCTS at 1,000 simulations on the same 20 boards. My five-ply Minimax calls finished on 2/20 puzzles and matched both keys. In November, increasing my shared ceiling from 0.25 s to 1.00 s increased returned keys from 4 to 5 for Minimax and from 3 to 6 for MCTS. I report partial decisions separately from completed-search accuracy.

For puzzle 18, I verified that rook and queen promotion both mate on the printed line. The booklet's queen-stalemate explanation is incorrect on that board. My verified first move remains Rxg7.

## How we can combine our work

I suggest puzzle 6 for the wrong-move comparison and puzzle 16 for a completed deeper search that changed the decision. We can select these alongside everyone's results. I have retained the contributor, machine, settings, seeds, and success definitions for my measurements so we can make fair comparisons across our experiments.

Akbar Aman · UIC MATH 496 · Fall 2026
