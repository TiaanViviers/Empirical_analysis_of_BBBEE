# Research progress

Completed event runs: mining_charter_2017, mining_charter_2018, ee_draft_2023, ee_final_2025, bbbee_draft_2026
Package verifier passed; schemas, keys, event dates, benchmark coverage and independent return formulas checked.
Return comparisons: 980380 valid returns; zero discrepancies.
Model rows: 844 ; failed/degenerate: 0
Inference rows: 55 ; unavailable: 0
Sensitivity rows: 60 ; placebo rows: 50

| event_id | window | n | n_mining | n_control | estimate | ci_lower | ci_upper | p_value | holm_primary_p | null_dates | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| mining_charter_2017 | primary | 135 | 15 | 120 | -0.03494 | -0.09252 | 0.00654 | 0.1620 | 0.648 | 221 | ok |
| mining_charter_2018 | primary | 146 | 16 | 130 | -0.02186 | -0.05545 | 0.02399 | 0.1894 | 0.648 | 217 | ok |
| ee_draft_2023 | primary | 169 | 0 | 0 | -0.00197 | -0.01259 | 0.00957 | 0.7056 | 1.000 | 221 | ok |
| ee_final_2025 | primary | 160 | 0 | 0 | -0.00116 | -0.01324 | 0.00772 | 0.7842 | 1.000 | 221 | ok |
| bbbee_draft_2026 | primary | 160 | 0 | 0 | 0.01578 | 0.00500 | 0.02632 | 0.0134 | 0.067 | 221 | ok |

Readiness: preliminary results produced, requiring methodological review. See the result report and test summary for evidence and remaining limitations.

Automated tests: see outputs/diagnostics/test_summary.md; rerun after analysis output regeneration. All unit, numerical and integration outcomes are recorded there.
Next: inspect corporate actions and influential returns, validate timing and issuer identities, review exposure definitions and bootstrap assumptions with the supervisor.
No Parts B/C, IRESS extraction, source rewrites, external data uploads or remote publication performed.

## Inference correction review — 2026-11-24

Fixed all three review issues: bootstrap paths now include/discard the true estimation-to-event gap; admissible block starts are sampled by position, including singleton sets; headline_results_percent.csv is generated from current inference and aggregate CAR results in the output module.
Regenerated all five events with 4,999 draws. Automated tests: 18 cases, 331 passed expectations, zero failed/errors/skips.
Regression tests cover five-session explicit OLS refits across 29-/19-session gaps, a changed estimation endpoint, a lone admissible block start, and fresh/overwrite headline exports. The old percentage CSV was removed before --all; the pipeline recreated it.
2026 headline raw p=0.0134 and Holm p=0.067. All 55 baseline point estimates and security counts are unchanged; uncertainty estimates and dependent figures/reports were regenerated. See outputs/diagnostics/inference_correction_comparison.csv for all before/after inference values.
Source fingerprints remain identical. The 49/50 supported-placebo limitation and substantive research limitations remain. Nothing was committed or published. 
