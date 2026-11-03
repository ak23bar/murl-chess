# Validation record · November 3, 2026

I used the following checks to verify my data and prepare the material for our group.

| Check | Observed result |
|---|---|
| Baseline regression suite | All 16 tests passed. |
| September saved measurements | 11,172 consistency checks passed on copies of the archived inputs. |
| October saved measurements | Rebuilt the 20-row summary from 160 raw records. Its SHA-256 matched the archived summary. The source hashes and all 1,280 board squares passed. |
| Exact search replay | All 60 new verifier calls completed. No position had a winning key at one or three plies. Each had its archived unique key at five. |
| Algorithm replay | All 20 completed three-ply Minimax choices matched. For puzzles 6, 13 and 16, all nine seeded MCTS moves and every root visit count and mean reward matched. |
| Reference solutions | Replayed 100 printed plies with canonical move notation. All 20 printed keys agreed and all 20 lines reached mate. All 20 strategy certificates passed the defender-coverage and mate-leaf checks. |
| Refutations | For each of the three published incorrect moves, one legal defense was found for which an exhaustive three-ply search returned no forced mate. |
| November design | All 160 scheduled position/ceiling/method/seed combinations occurred exactly once. Verified move legality, key flags, effort, MCTS iteration completion, and the four-condition summary. |
| Publication | Both Mermaid blocks parsed and rendered to SVG. Relative links in the project, reports, poster, and source guides resolved. Vector figures parsed, the supplied template ZIP passed integrity checks, and all eight original source hashes matched. The final five-page report was rendered and inspected. |

I have included the [reproduction commands](../../README.md#reproduce-the-checks) for the group to audit or repeat my checks. A repeat of my timing experiment can change the work completed before timeout. After reviewing our email chain and transcript, I revised the current narrative into first person, added my Google Doc and PDF summary, and checked both final PDF layouts. I retained my original submitted PDFs and measured data.
