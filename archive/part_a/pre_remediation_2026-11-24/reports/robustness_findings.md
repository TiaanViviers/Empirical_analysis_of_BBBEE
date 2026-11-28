# Robustness findings

Estimation threshold, volume screen, unchanged-price threshold, normal-return model, extreme-return exclusion, timing, mining definition, balanced event sample and block length are varied one at a time.
Extreme-return exclusion is deliberately severe and diagnostic. It is not an assertion that every >30% move is a data error.
Strict mining drops Aluminium/Aluminum from the mining group and leaves those securities unknown, rather than moving them into controls.
Primary-window sensitivities below use full re-estimation and their own complete-window samples.
Placebos refit market models using their own past; they are not resampled in-sample CARs. Dates are seeded, spaced >=22 sessions and exclude ±30 sessions around registered events.
Only the five registered policy events are excluded; unrelated news is not exhaustively screened.
Pseudo-events use the original event classification snapshot, potentially retrospective. They assess portfolio behaviour, not valid historical regulatory assignment.
Some later pseudo-event estimation periods may contain the real event; their null calibration is exploratory.
Verified issuer links are unavailable. No name-based consolidation or 2026-ISIN historical de-duplication was attempted.

| event_id | specification | estimate | ci_lower | ci_upper | p_value | n | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| mining_charter_2017 | baseline | -0.03494 | -0.09252 | 0.00654 | 0.1620 | 135 | ok |
| mining_charter_2017 | min_200 | -0.03494 | -0.09252 | 0.00654 | 0.1620 | 135 | ok |
| mining_charter_2017 | no_volume_screen | -0.03494 | -0.09250 | 0.00656 | 0.1620 | 135 | ok |
| mining_charter_2017 | no_zero_restriction | -0.03883 | -0.08243 | -0.00382 | 0.0480 | 184 | ok |
| mining_charter_2017 | market_adjusted | -0.03445 | -0.09100 | 0.00704 | 0.1788 | 135 | ok |
| mining_charter_2017 | drop_flagged_extremes | -0.03472 | -0.09234 | 0.00677 | 0.1654 | 135 | ok |
| mining_charter_2017 | next_session | -0.01906 | -0.07836 | 0.02447 | 0.4194 | 135 | ok |
| mining_charter_2017 | previous_session | -0.02994 | -0.08792 | 0.01126 | 0.2382 | 134 | ok |
| mining_charter_2017 | strict_mining | -0.03421 | -0.09359 | 0.00864 | 0.1870 | 134 | ok |
| mining_charter_2017 | balanced_plot_sample | -0.03438 | -0.09191 | 0.00704 | 0.1702 | 132 | ok |
| mining_charter_2017 | block_1 | -0.03494 | -0.08704 | 0.00871 | 0.1498 | 135 | ok |
| mining_charter_2017 | block_10 | -0.03494 | -0.09038 | 0.00551 | 0.1590 | 135 | ok |
| mining_charter_2017 | mineral_value_chain | -0.03657 | -0.09320 | 0.00457 | 0.1422 | 135 | ok |
| mining_charter_2018 | baseline | -0.02186 | -0.05545 | 0.02399 | 0.1894 | 146 | ok |
| mining_charter_2018 | min_200 | -0.02186 | -0.05545 | 0.02399 | 0.1894 | 146 | ok |
| mining_charter_2018 | no_volume_screen | -0.02186 | -0.05544 | 0.02400 | 0.1894 | 146 | ok |
| mining_charter_2018 | no_zero_restriction | -0.01939 | -0.05918 | 0.03097 | 0.2946 | 200 | ok |
| mining_charter_2018 | market_adjusted | -0.02678 | -0.05995 | 0.01870 | 0.1308 | 146 | ok |
| mining_charter_2018 | drop_flagged_extremes | -0.01924 | -0.05261 | 0.02683 | 0.2284 | 145 | ok |
| mining_charter_2018 | next_session | 0.01335 | -0.02048 | 0.05979 | 0.3766 | 147 | ok |
| mining_charter_2018 | previous_session | -0.03625 | -0.07000 | 0.00832 | 0.0488 | 145 | ok |
| mining_charter_2018 | strict_mining | -0.02731 | -0.06242 | 0.01840 | 0.1558 | 145 | ok |
| mining_charter_2018 | balanced_plot_sample | -0.02244 | -0.05623 | 0.02374 | 0.1852 | 144 | ok |
| mining_charter_2018 | block_1 | -0.02186 | -0.05588 | 0.01558 | 0.2110 | 146 | ok |
| mining_charter_2018 | block_10 | -0.02186 | -0.05496 | 0.02432 | 0.1754 | 146 | ok |
| mining_charter_2018 | mineral_value_chain | -0.01412 | -0.04756 | 0.03141 | 0.3646 | 146 | ok |
| mining_charter_2018 | cabinet_2018_09_19 | 0.01058 | -0.02312 | 0.05678 | 0.5128 | 146 | ok |
| ee_draft_2023 | baseline | -0.00197 | -0.01259 | 0.00957 | 0.7056 | 169 | ok |
| ee_draft_2023 | min_200 | -0.00197 | -0.01259 | 0.00957 | 0.7056 | 169 | ok |
| ee_draft_2023 | no_volume_screen | -0.00208 | -0.01282 | 0.00949 | 0.6796 | 170 | ok |
| ee_draft_2023 | no_zero_restriction | -0.00306 | -0.01253 | 0.00785 | 0.5566 | 193 | ok |
| ee_draft_2023 | market_adjusted | -0.01012 | -0.02603 | 0.01257 | 0.2122 | 169 | ok |
| ee_draft_2023 | drop_flagged_extremes | -0.00198 | -0.01262 | 0.00954 | 0.7028 | 169 | ok |
| ee_draft_2023 | next_session | -0.00018 | -0.01132 | 0.01169 | 0.9718 | 170 | ok |
| ee_draft_2023 | previous_session | -0.00544 | -0.01634 | 0.00668 | 0.2912 | 168 | ok |
| ee_draft_2023 | balanced_plot_sample | -0.00203 | -0.01277 | 0.00871 | 0.6890 | 157 | ok |
| ee_draft_2023 | block_1 | -0.00197 | -0.01266 | 0.00973 | 0.7128 | 169 | ok |
| ee_draft_2023 | block_10 | -0.00197 | -0.01280 | 0.00984 | 0.7080 | 169 | ok |
| ee_final_2025 | baseline | -0.00116 | -0.01324 | 0.00772 | 0.7842 | 160 | ok |
| ee_final_2025 | min_200 | -0.00116 | -0.01324 | 0.00772 | 0.7842 | 160 | ok |
| ee_final_2025 | no_volume_screen | -0.00111 | -0.01327 | 0.00779 | 0.7936 | 161 | ok |
| ee_final_2025 | no_zero_restriction | 0.00123 | -0.01108 | 0.00968 | 0.7964 | 186 | ok |
| ee_final_2025 | market_adjusted | -0.00407 | -0.01516 | 0.00644 | 0.4444 | 160 | ok |
| ee_final_2025 | drop_flagged_extremes | -0.00107 | -0.01316 | 0.00780 | 0.8018 | 160 | ok |
| ee_final_2025 | next_session | 0.00311 | -0.00624 | 0.01207 | 0.4646 | 158 | ok |
| ee_final_2025 | previous_session | 0.00224 | -0.00750 | 0.01129 | 0.6074 | 161 | ok |
| ee_final_2025 | balanced_plot_sample | -0.00064 | -0.01209 | 0.00773 | 0.8902 | 155 | ok |
| ee_final_2025 | block_1 | -0.00116 | -0.01072 | 0.00691 | 0.7862 | 160 | ok |
| ee_final_2025 | block_10 | -0.00116 | -0.01062 | 0.00770 | 0.7824 | 160 | ok |
| bbbee_draft_2026 | baseline | 0.01578 | 0.00500 | 0.02632 | 0.0134 | 160 | ok |
| bbbee_draft_2026 | min_200 | 0.01598 | 0.00514 | 0.02643 | 0.0134 | 159 | ok |
| bbbee_draft_2026 | no_volume_screen | 0.01578 | 0.00501 | 0.02633 | 0.0134 | 160 | ok |
| bbbee_draft_2026 | no_zero_restriction | 0.01381 | 0.00362 | 0.02440 | 0.0142 | 184 | ok |
| bbbee_draft_2026 | market_adjusted | 0.03013 | 0.01477 | 0.04160 | 0.0002 | 160 | ok |
| bbbee_draft_2026 | drop_flagged_extremes | 0.01630 | 0.00545 | 0.02683 | 0.0120 | 160 | ok |
| bbbee_draft_2026 | next_session | 0.02077 | 0.01008 | 0.03122 | 0.0050 | 159 | ok |
| bbbee_draft_2026 | previous_session | -0.00326 | -0.01345 | 0.00690 | 0.4728 | 159 | ok |
| bbbee_draft_2026 | balanced_plot_sample | 0.01577 | 0.00617 | 0.02656 | 0.0100 | 155 | ok |
| bbbee_draft_2026 | block_1 | 0.01578 | 0.00457 | 0.02610 | 0.0100 | 160 | ok |
| bbbee_draft_2026 | block_10 | 0.01578 | 0.00545 | 0.02548 | 0.0078 | 160 | ok |
