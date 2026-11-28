# Research progress

Completed event runs: mining_charter_2017, mining_charter_2018, ee_draft_2023, ee_final_2025, bbbee_draft_2026
Package verifier passed; schemas, keys, event dates, benchmark coverage and independent return formulas checked.
Return comparisons: 980380 valid returns; zero discrepancies.
Model rows: 844 ; failed/degenerate: 0
Inference rows: 55 ; unavailable: 0
Sensitivity rows: 109 ; placebo rows: 46

| event_id | window | n | n_mining | n_control | estimate | ci_lower | ci_upper | p_value | holm_primary_p | null_dates | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| mining_charter_2017 | primary | 135 | 15 | 120 | -0.03494 | -0.08441 | 0.01452 | 0.1620 | 0.648 | 221 | ok |
| mining_charter_2018 | primary | 146 | 16 | 130 | -0.02217 | -0.05692 | 0.01258 | 0.1814 | 0.648 | 217 | ok |
| ee_draft_2023 | primary | 169 | 0 | 0 | -0.00197 | -0.01329 | 0.00936 | 0.7056 | 1.000 | 221 | ok |
| ee_final_2025 | primary | 160 | 0 | 0 | -0.00116 | -0.01034 | 0.00801 | 0.7842 | 1.000 | 221 | ok |
| bbbee_draft_2026 | primary | 160 | 0 | 0 | 0.01578 | 0.00503 | 0.02652 | 0.0134 | 0.067 | 221 | ok |

Readiness: preliminary results produced, requiring methodological review. See the result report and test summary for evidence and remaining limitations.

Automated tests: see ../../outputs/part_a/diagnostics/test_summary.md; rerun after analysis output regeneration. All unit, numerical and integration outcomes are recorded there.
Next: inspect corporate actions and influential returns, validate timing and issuer identities, review exposure definitions and bootstrap assumptions with the supervisor.
No Parts B/C, IRESS extraction, source rewrites, external data uploads or remote publication performed.
