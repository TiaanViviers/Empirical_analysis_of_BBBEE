# Robustness findings

Estimation threshold, volume screen, unchanged-price threshold, normal-return model, extreme-return exclusion, timing, mining definition, balanced event sample and block length are varied one at a time.
Full extreme-return exclusion removes flagged analytical returns from fitting, event windows AND bootstrap donors. It is deliberately severe and diagnostic, not evidence that every >30% move is erroneous.
Strict mining drops Aluminium/Aluminum from the mining group and leaves those securities unknown, rather than moving them into controls.
Primary-window sensitivities below use full re-estimation and their own complete-window samples.
Placebos refit market models using their own past; they are not resampled in-sample CARs. Dates are seeded, spaced >=22 sessions and exclude ±30 sessions around registered events.
Only the five registered policy events are excluded; unrelated news is not exhaustively screened.
Pseudo-events use the original event classification snapshot, potentially retrospective. They assess portfolio behaviour, not valid historical regulatory assignment.
Pseudo-event fitting windows exclude the real event being studied. Shortfalls are reported rather than filling the sample with contaminated dates. Other news and frozen exposures still limit inference.
Partial issuer weighting combines only the verified Fortress A/B link; every unlinked security stays separate. It is not full issuer-universe verification.
Event SD multipliers and early/late donor windows are uncertainty scenarios, not estimated event-volatility corrections. Legacy raw-price results are a measurement comparison, not preferred economic returns.

| event_id | specification | estimate | ci_lower | ci_upper | p_value | n | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| mining_charter_2017 | baseline | -0.03494 | -0.08441 | 0.01452 | 0.1620 | 135 | ok |
| mining_charter_2017 | min_200 | -0.03494 | -0.08441 | 0.01452 | 0.1620 | 135 | ok |
| mining_charter_2017 | no_volume_screen | -0.03494 | -0.08439 | 0.01451 | 0.1620 | 135 | ok |
| mining_charter_2017 | no_zero_restriction | -0.03883 | -0.07731 | -0.00035 | 0.0480 | 184 | ok |
| mining_charter_2017 | market_adjusted | -0.03445 | -0.08086 | 0.01195 | 0.1788 | 135 | ok |
| mining_charter_2017 | drop_flagged_extremes | -0.03472 | -0.08110 | 0.01166 | 0.1392 | 135 | ok |
| mining_charter_2017 | next_session | -0.01906 | -0.06981 | 0.03169 | 0.4194 | 135 | ok |
| mining_charter_2017 | previous_session | -0.02994 | -0.07875 | 0.01886 | 0.2382 | 134 | ok |
| mining_charter_2017 | strict_mining | -0.03421 | -0.08530 | 0.01688 | 0.1870 | 134 | ok |
| mining_charter_2017 | balanced_plot_sample | -0.03438 | -0.08368 | 0.01492 | 0.1702 | 132 | ok |
| mining_charter_2017 | block_1 | -0.03494 | -0.08388 | 0.01400 | 0.1498 | 135 | ok |
| mining_charter_2017 | block_10 | -0.03494 | -0.08279 | 0.01290 | 0.1590 | 135 | ok |
| mining_charter_2017 | mineral_value_chain | -0.03657 | -0.08564 | 0.01251 | 0.1422 | 135 | ok |
| mining_charter_2017 | event_no_volume_screen | -0.03494 | -0.08441 | 0.01452 | 0.1620 | 135 | ok |
| mining_charter_2017 | null_active_dates | -0.03494 | -0.08910 | 0.01921 | 0.2446 | 135 | ok |
| mining_charter_2017 | event_sd_1p5 | -0.03494 | -0.10860 | 0.03871 | 0.3366 | 135 | ok |
| mining_charter_2017 | event_sd_2 | -0.03494 | -0.13300 | 0.06312 | 0.4480 | 135 | ok |
| mining_charter_2017 | donor_early | -0.03494 | -0.08524 | 0.01535 | 0.1852 | 135 | ok |
| mining_charter_2017 | donor_late | -0.03494 | -0.08204 | 0.01215 | 0.1338 | 135 | ok |
| mining_charter_2017 | exclude_unresolved_action_securities | -0.03784 | -0.08474 | 0.00906 | 0.1216 | 134 | ok |
| mining_charter_2017 | reviewed_industry_proxy | -0.03670 | -0.08902 | 0.01561 | 0.1662 | 134 | ok |
| mining_charter_2017 | partial_verified_issuer | -0.03494 | -0.08441 | 0.01452 | 0.1620 | 135 | ok |
| mining_charter_2017 | legacy_raw_price | -0.03494 | -0.08441 | 0.01452 | 0.1620 | 135 | ok |
| mining_charter_2018 | baseline | -0.02217 | -0.05692 | 0.01258 | 0.1814 | 146 | ok |
| mining_charter_2018 | min_200 | -0.02217 | -0.05692 | 0.01258 | 0.1814 | 146 | ok |
| mining_charter_2018 | no_volume_screen | -0.02217 | -0.05695 | 0.01261 | 0.1814 | 146 | ok |
| mining_charter_2018 | no_zero_restriction | -0.01962 | -0.06511 | 0.02587 | 0.2940 | 200 | ok |
| mining_charter_2018 | market_adjusted | -0.02678 | -0.06093 | 0.00738 | 0.1228 | 146 | ok |
| mining_charter_2018 | drop_flagged_extremes | -0.01924 | -0.05348 | 0.01501 | 0.2174 | 145 | ok |
| mining_charter_2018 | next_session | 0.01281 | -0.02246 | 0.04808 | 0.3998 | 147 | ok |
| mining_charter_2018 | previous_session | -0.03654 | -0.07114 | -0.00193 | 0.0398 | 145 | ok |
| mining_charter_2018 | strict_mining | -0.02761 | -0.06383 | 0.00860 | 0.1480 | 145 | ok |
| mining_charter_2018 | balanced_plot_sample | -0.02275 | -0.05778 | 0.01228 | 0.1770 | 144 | ok |
| mining_charter_2018 | block_1 | -0.02217 | -0.05667 | 0.01233 | 0.1956 | 146 | ok |
| mining_charter_2018 | block_10 | -0.02217 | -0.05669 | 0.01235 | 0.1626 | 146 | ok |
| mining_charter_2018 | mineral_value_chain | -0.01444 | -0.04973 | 0.02085 | 0.3500 | 146 | ok |
| mining_charter_2018 | event_no_volume_screen | -0.02217 | -0.05692 | 0.01258 | 0.1814 | 146 | ok |
| mining_charter_2018 | null_active_dates | -0.02217 | -0.06010 | 0.01576 | 0.2372 | 146 | ok |
| mining_charter_2018 | event_sd_1p5 | -0.02217 | -0.07382 | 0.02948 | 0.3226 | 146 | ok |
| mining_charter_2018 | event_sd_2 | -0.02217 | -0.09082 | 0.04649 | 0.4988 | 146 | ok |
| mining_charter_2018 | donor_early | -0.02217 | -0.06127 | 0.01694 | 0.2134 | 146 | ok |
| mining_charter_2018 | donor_late | -0.02217 | -0.05209 | 0.00775 | 0.1376 | 146 | ok |
| mining_charter_2018 | exclude_unresolved_action_securities | -0.01935 | -0.05422 | 0.01551 | 0.2214 | 145 | ok |
| mining_charter_2018 | reviewed_industry_proxy | -0.01950 | -0.05728 | 0.01829 | 0.2378 | 145 | ok |
| mining_charter_2018 | partial_verified_issuer | -0.02217 | -0.05692 | 0.01258 | 0.1814 | 146 | ok |
| mining_charter_2018 | legacy_raw_price | -0.02186 | -0.05801 | 0.01429 | 0.1894 | 146 | ok |
| mining_charter_2018 | cabinet_2018_09_19 | 0.00991 | -0.02474 | 0.04455 | 0.5568 | 146 | ok |
| mining_charter_2018 | public_stimulus_2018_09_21 | 0.04686 | 0.01280 | 0.08091 | 0.0214 | 148 | ok |
| mining_charter_2018 | advisory_2018_09_26 | -0.03654 | -0.07114 | -0.00193 | 0.0398 | 145 | ok |
| ee_draft_2023 | baseline | -0.00197 | -0.01329 | 0.00936 | 0.7056 | 169 | ok |
| ee_draft_2023 | min_200 | -0.00197 | -0.01329 | 0.00936 | 0.7056 | 169 | ok |
| ee_draft_2023 | no_volume_screen | -0.00208 | -0.01352 | 0.00935 | 0.6796 | 170 | ok |
| ee_draft_2023 | no_zero_restriction | -0.00306 | -0.01304 | 0.00692 | 0.5566 | 193 | ok |
| ee_draft_2023 | market_adjusted | -0.01012 | -0.02825 | 0.00800 | 0.2122 | 169 | ok |
| ee_draft_2023 | drop_flagged_extremes | -0.00198 | -0.01289 | 0.00893 | 0.6898 | 169 | ok |
| ee_draft_2023 | next_session | -0.00018 | -0.01183 | 0.01146 | 0.9718 | 170 | ok |
| ee_draft_2023 | previous_session | -0.00544 | -0.01721 | 0.00633 | 0.2912 | 168 | ok |
| ee_draft_2023 | balanced_plot_sample | -0.00203 | -0.01277 | 0.00872 | 0.6890 | 157 | ok |
| ee_draft_2023 | block_1 | -0.00197 | -0.01322 | 0.00929 | 0.7128 | 169 | ok |
| ee_draft_2023 | block_10 | -0.00197 | -0.01335 | 0.00942 | 0.7080 | 169 | ok |
| ee_draft_2023 | event_no_volume_screen | -0.00210 | -0.01349 | 0.00929 | 0.6774 | 170 | ok |
| ee_draft_2023 | null_active_dates | -0.00197 | -0.01203 | 0.00810 | 0.8892 | 169 | ok |
| ee_draft_2023 | event_sd_1p5 | -0.00197 | -0.01889 | 0.01495 | 0.8026 | 169 | ok |
| ee_draft_2023 | event_sd_2 | -0.00197 | -0.02462 | 0.02068 | 0.8468 | 169 | ok |
| ee_draft_2023 | donor_early | -0.00197 | -0.01227 | 0.00833 | 0.7304 | 169 | ok |
| ee_draft_2023 | donor_late | -0.00197 | -0.01347 | 0.00954 | 0.6812 | 169 | ok |
| ee_draft_2023 | exclude_unresolved_action_securities | -0.00197 | -0.01329 | 0.00936 | 0.7056 | 169 | ok |
| ee_draft_2023 | partial_verified_issuer | -0.00193 | -0.01329 | 0.00944 | 0.7080 | 169 | ok |
| ee_draft_2023 | legacy_raw_price | -0.00197 | -0.01329 | 0.00936 | 0.7056 | 169 | ok |
| ee_final_2025 | baseline | -0.00116 | -0.01034 | 0.00801 | 0.7842 | 160 | ok |
| ee_final_2025 | min_200 | -0.00116 | -0.01034 | 0.00801 | 0.7842 | 160 | ok |
| ee_final_2025 | no_volume_screen | -0.00111 | -0.01036 | 0.00813 | 0.7936 | 161 | ok |
| ee_final_2025 | no_zero_restriction | 0.00123 | -0.00841 | 0.01086 | 0.7964 | 186 | ok |
| ee_final_2025 | market_adjusted | -0.00407 | -0.01507 | 0.00692 | 0.4444 | 160 | ok |
| ee_final_2025 | drop_flagged_extremes | -0.00107 | -0.01041 | 0.00827 | 0.7944 | 160 | ok |
| ee_final_2025 | next_session | 0.00311 | -0.00601 | 0.01223 | 0.4646 | 158 | ok |
| ee_final_2025 | previous_session | 0.00224 | -0.00699 | 0.01147 | 0.6074 | 161 | ok |
| ee_final_2025 | balanced_plot_sample | -0.00064 | -0.00954 | 0.00826 | 0.8902 | 155 | ok |
| ee_final_2025 | block_1 | -0.00116 | -0.00990 | 0.00757 | 0.7862 | 160 | ok |
| ee_final_2025 | block_10 | -0.00116 | -0.01030 | 0.00798 | 0.7824 | 160 | ok |
| ee_final_2025 | event_no_volume_screen | -0.00113 | -0.01039 | 0.00813 | 0.7912 | 161 | ok |
| ee_final_2025 | null_active_dates | -0.00116 | -0.01230 | 0.00997 | 0.8058 | 160 | ok |
| ee_final_2025 | event_sd_1p5 | -0.00116 | -0.01475 | 0.01242 | 0.8664 | 160 | ok |
| ee_final_2025 | event_sd_2 | -0.00116 | -0.01917 | 0.01684 | 0.9110 | 160 | ok |
| ee_final_2025 | donor_early | -0.00116 | -0.01318 | 0.01085 | 0.7842 | 160 | ok |
| ee_final_2025 | donor_late | -0.00116 | -0.00866 | 0.00634 | 0.7402 | 160 | ok |
| ee_final_2025 | exclude_unresolved_action_securities | -0.00116 | -0.01034 | 0.00801 | 0.7842 | 160 | ok |
| ee_final_2025 | partial_verified_issuer | -0.00116 | -0.01034 | 0.00801 | 0.7842 | 160 | ok |
| ee_final_2025 | legacy_raw_price | -0.00116 | -0.01034 | 0.00801 | 0.7842 | 160 | ok |
| bbbee_draft_2026 | baseline | 0.01578 | 0.00503 | 0.02652 | 0.0134 | 160 | ok |
| bbbee_draft_2026 | min_200 | 0.01598 | 0.00529 | 0.02666 | 0.0134 | 159 | ok |
| bbbee_draft_2026 | no_volume_screen | 0.01578 | 0.00508 | 0.02649 | 0.0134 | 160 | ok |
| bbbee_draft_2026 | no_zero_restriction | 0.01381 | 0.00350 | 0.02412 | 0.0142 | 184 | ok |
| bbbee_draft_2026 | market_adjusted | 0.03013 | 0.01798 | 0.04228 | 0.0002 | 160 | ok |
| bbbee_draft_2026 | drop_flagged_extremes | 0.01630 | 0.00670 | 0.02590 | 0.0106 | 160 | ok |
| bbbee_draft_2026 | next_session | 0.02077 | 0.01018 | 0.03136 | 0.0050 | 159 | ok |
| bbbee_draft_2026 | previous_session | -0.00326 | -0.01344 | 0.00692 | 0.4728 | 159 | ok |
| bbbee_draft_2026 | balanced_plot_sample | 0.01577 | 0.00577 | 0.02577 | 0.0100 | 155 | ok |
| bbbee_draft_2026 | block_1 | 0.01578 | 0.00492 | 0.02663 | 0.0100 | 160 | ok |
| bbbee_draft_2026 | block_10 | 0.01578 | 0.00573 | 0.02582 | 0.0078 | 160 | ok |
| bbbee_draft_2026 | event_no_volume_screen | 0.01578 | 0.00503 | 0.02652 | 0.0134 | 160 | ok |
| bbbee_draft_2026 | null_active_dates | 0.01578 | -0.00177 | 0.03332 | 0.0502 | 160 | ok |
| bbbee_draft_2026 | event_sd_1p5 | 0.01578 | -0.00002 | 0.03157 | 0.0502 | 160 | ok |
| bbbee_draft_2026 | event_sd_2 | 0.01578 | -0.00531 | 0.03686 | 0.1212 | 160 | ok |
| bbbee_draft_2026 | donor_early | 0.01578 | 0.00566 | 0.02590 | 0.0188 | 160 | ok |
| bbbee_draft_2026 | donor_late | 0.01578 | 0.00506 | 0.02649 | 0.0048 | 160 | ok |
| bbbee_draft_2026 | exclude_unresolved_action_securities | 0.01512 | 0.00509 | 0.02515 | 0.0112 | 159 | ok |
| bbbee_draft_2026 | partial_verified_issuer | 0.01578 | 0.00503 | 0.02652 | 0.0134 | 160 | ok |
| bbbee_draft_2026 | legacy_raw_price | 0.01578 | 0.00503 | 0.02652 | 0.0134 | 160 | ok |
