# Audit checklist

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
