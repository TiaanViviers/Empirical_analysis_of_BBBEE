# Execution report — methodological correction pass

All five events have supported revised baseline results.

This report supersedes the pre-remediation execution report. The original report and results are retained in ../../archive/part_a/pre_remediation_2026-11-24/.
Read methodological_corrections_report.md for issue-by-issue changes, before/after results, calibration, unresolved limitations and reproduction commands. The historical independent_methodology_review.md remains the review of the earlier implementation.

| event_id | n_mining | n_control | n_all | estimate_pct | ci_lower_pct | ci_upper_pct | p_value | holm_primary_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| mining_charter_2017 | 15 | 120 | 168 | -3.49432 | -8.44075 | 1.45212 | 0.1620 | 0.648 |
| mining_charter_2018 | 16 | 130 | 176 | -2.21674 | -5.69151 | 1.25804 | 0.1814 | 0.648 |
| ee_draft_2023 | 0 | 0 | 169 | -0.19669 | -1.32893 | 0.93556 | 0.7056 | 1.000 |
| ee_final_2025 | 0 | 0 | 160 | -0.11641 | -1.03427 | 0.80145 | 0.7842 | 1.000 |
| bbbee_draft_2026 | 0 | 0 | 160 | 1.57757 | 0.50322 | 2.65192 | 0.0134 | 0.067 |

Matched post-run tests: 31 cases; 395 passed expectations; 0 failed; 0 errors; 0 skipped.

Baseline inference rows: 55 ; unavailable: 0
Sensitivity rows: 109 ; placebo attempts: 46 ; valid: 45
Source package fingerprints must agree before/after every run. Readiness: independent re-review and preliminary discussion; not thesis-final or causal efficiency evidence.
