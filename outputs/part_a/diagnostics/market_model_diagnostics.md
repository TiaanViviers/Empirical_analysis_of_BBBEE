# Market-model diagnostics

| event_id | n | failed | alpha_median | beta_median | beta_min | beta_max | median_r_squared | median_sigma |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| mining_charter_2017 | 169 | 0 | 0.00018 | 0.53942 | -0.38715 | 1.87944 | 0.08912 | 0.01660 |
| mining_charter_2018 | 177 | 0 | -0.00013 | 0.45877 | -0.34972 | 1.83895 | 0.04146 | 0.01938 |
| ee_draft_2023 | 172 | 0 | -0.00033 | 0.48263 | -0.16265 | 1.70549 | 0.08992 | 0.02136 |
| ee_final_2025 | 161 | 0 | 0.00034 | 0.65417 | -0.23194 | 2.43695 | 0.08555 | 0.01746 |
| bbbee_draft_2026 | 165 | 0 | 0.00005 | 0.58070 | -2.26124 | 2.39343 | 0.09693 | 0.01824 |

OLS fits are instrument/event-specific and use usable dates in the configured pre-event interval.
Degenerate market or stock variance and singular fits are rejected. Large alpha/beta values are flagged, not silently removed.
Full model estimates, flagged models, and beta distribution are supplied. No event observations enter estimation.
