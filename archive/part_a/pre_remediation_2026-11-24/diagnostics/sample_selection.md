# Executed sample selection

| event_id | source_instruments | historical_prices | enough_estimation | eligible | eligible_classified | eligible_unknown | complete_primary | complete_plot | primary_mining | primary_control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| mining_charter_2017 | 1869 | 475 | 255 | 169 | 135 | 34 | 168 | 164 | 15 | 120 |
| mining_charter_2018 | 1869 | 465 | 261 | 177 | 146 | 31 | 176 | 173 | 16 | 130 |
| ee_draft_2023 | 1869 | 354 | 212 | 172 | 159 | 13 | 169 | 157 | 25 | 133 |
| ee_final_2025 | 1869 | 329 | 195 | 161 | 157 | 4 | 160 | 155 | 22 | 134 |
| bbbee_draft_2026 | 1869 | 320 | 196 | 165 | 162 | 3 | 160 | 155 | 22 | 137 |

| event_id | exclusion | n |
| --- | --- | --- |
| mining_charter_2017 | insufficient_estimation_returns | 220 |
| mining_charter_2017 | no_historical_positive_close | 1394 |
| mining_charter_2017 | included | 169 |
| mining_charter_2017 | known_likely_noncompany | 5 |
| mining_charter_2017 | excess_unchanged_closes | 81 |
| mining_charter_2018 | no_historical_positive_close | 1404 |
| mining_charter_2018 | known_likely_noncompany | 9 |
| mining_charter_2018 | included | 177 |
| mining_charter_2018 | insufficient_estimation_returns | 204 |
| mining_charter_2018 | excess_unchanged_closes | 75 |
| ee_draft_2023 | no_historical_positive_close | 1515 |
| ee_draft_2023 | excess_unchanged_closes | 38 |
| ee_draft_2023 | included | 172 |
| ee_draft_2023 | known_likely_noncompany | 2 |
| ee_draft_2023 | insufficient_estimation_returns | 142 |
| ee_final_2025 | no_historical_positive_close | 1540 |
| ee_final_2025 | excess_unchanged_closes | 31 |
| ee_final_2025 | included | 161 |
| ee_final_2025 | known_likely_noncompany | 3 |
| ee_final_2025 | insufficient_estimation_returns | 134 |
| bbbee_draft_2026 | no_historical_positive_close | 1549 |
| bbbee_draft_2026 | excess_unchanged_closes | 29 |
| bbbee_draft_2026 | included | 165 |
| bbbee_draft_2026 | insufficient_estimation_returns | 124 |
| bbbee_draft_2026 | known_likely_noncompany | 2 |

Complete CAR samples differ by window; plotting uses a separate balanced 21-session sample. Counts are securities, not verified companies.
