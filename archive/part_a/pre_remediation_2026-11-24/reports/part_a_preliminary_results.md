# Part A preliminary results

Execution mode: full configured analysis.

## Research objective

Measure short-horizon JSE price reactions associated with transformation-policy announcements. Outcomes concern market valuations, not realised productivity, profitability or equity gains. Parts B and C are outside scope.

## Data and sample

| event_id | source_instruments | historical_prices | enough_estimation | eligible | eligible_classified | eligible_unknown | complete_primary | complete_plot | primary_mining | primary_control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| mining_charter_2017 | 1869 | 475 | 255 | 169 | 135 | 34 | 168 | 164 | 15 | 120 |
| mining_charter_2018 | 1869 | 465 | 261 | 177 | 146 | 31 | 176 | 173 | 16 | 130 |
| ee_draft_2023 | 1869 | 354 | 212 | 172 | 159 | 13 | 169 | 157 | 25 | 133 |
| ee_final_2025 | 1869 | 329 | 195 | 161 | 157 | 4 | 160 | 155 | 22 | 134 |
| bbbee_draft_2026 | 1869 | 320 | 196 | 165 | 162 | 3 | 160 | 155 | 22 | 137 |

Immutable source package 1.2.0. Estimation window: -250:-30 ; minimum usable dates: 180 ; positive volume: TRUE ; maximum fraction of unchanged returns: 0.2 .
Known likely non-company securities are screened using historical bulletin flags. Unclassified securities remain in aggregate results as unknown; they do not enter mining/control comparisons.
## Event dates and timing

Official register dates anchor session zero. All five first-public-disclosure timestamps remain unverified. Scheduled 10:00 briefings do not prove first disclosure. Previous/next-session timing and 19 September 2018 are separate sensitivities.

## Returns and normal returns

Simple raw closing-price returns require positive finite closes on immediately adjacent observed sessions. J203 is the benchmark; its return variant is unverified. No return bridges the January 2024 gap.
Instrument-specific OLS: R_it = alpha_i + beta_i R_mt + epsilon_it. AR is actual minus predicted price return. Complete-window CAR sums daily AR. Equal-security-weight CAAR is the mean of complete-window CARs.

## Primary [0,1] results and inference

Fractional returns (0.01 = 1%). Mining events report the mining-minus-control spread; broad-policy events report aggregate market-model CAAR. N is the combined portfolio security count.

| event_id | window | n | n_mining | n_control | estimate | ci_lower | ci_upper | p_value | holm_primary_p | null_dates | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| mining_charter_2017 | primary | 135 | 15 | 120 | -0.03494 | -0.09252 | 0.00654 | 0.1620 | 0.648 | 221 | ok |
| mining_charter_2018 | primary | 146 | 16 | 130 | -0.02186 | -0.05545 | 0.02399 | 0.1894 | 0.648 | 217 | ok |
| ee_draft_2023 | primary | 169 | 0 | 0 | -0.00197 | -0.01259 | 0.00957 | 0.7056 | 1.000 | 221 | ok |
| ee_final_2025 | primary | 160 | 0 | 0 | -0.00116 | -0.01324 | 0.00772 | 0.7842 | 1.000 | 221 | ok |
| bbbee_draft_2026 | primary | 160 | 0 | 0 | 0.01578 | 0.00500 | 0.02632 | 0.0134 | 0.067 | 221 | ok |

Intervals and two-sided Monte Carlo p-values use date-synchronous moving blocks of centred pre-event firm residual vectors. Firm-specific regression parameter error is propagated using each original OLS design. Simulated paths preserve the trading-session gap between estimation and each event window (29 intervening sessions for [0,+1]), discarding gap draws. Common shocks are retained. Complete pre-event null dates and block lengths are reported.
The null uses all valid raw returns for fixed constituents, including zero-volume days. Positive-volume screens apply to OLS fitting and event returns. This asymmetry can understate active-day volatility; no-volume sensitivity is supplied. The method assumes a stable residual process and cannot establish robustness to event-induced volatility.
0 of 5 headline tests have Holm-adjusted p<0.05. Other windows/specifications are exploratory and multiply comparisons.

## All CAR windows and group estimates

| window | group | n | mean_car | median_car | sd_car | event_id |
| --- | --- | --- | --- | --- | --- | --- |
| primary | all | 168 | -0.01318 | -0.01015 | 0.02971 | mining_charter_2017 |
| primary | mining | 15 | -0.04438 | -0.05287 | 0.04442 | mining_charter_2017 |
| primary | non_mining | 120 | -0.00944 | -0.00904 | 0.02544 | mining_charter_2017 |
| primary | unknown | 33 | -0.01262 | -0.00677 | 0.02880 | mining_charter_2017 |
| short | all | 167 | -0.01291 | -0.01063 | 0.03694 | mining_charter_2017 |
| short | mining | 15 | -0.05151 | -0.04981 | 0.04317 | mining_charter_2017 |
| short | non_mining | 119 | -0.00680 | -0.00740 | 0.03346 | mining_charter_2017 |
| short | unknown | 33 | -0.01743 | -0.01394 | 0.03572 | mining_charter_2017 |
| week | all | 166 | -0.01959 | -0.01499 | 0.04055 | mining_charter_2017 |
| week | mining | 15 | -0.04391 | -0.04853 | 0.06159 | mining_charter_2017 |
| week | non_mining | 119 | -0.01647 | -0.01059 | 0.03701 | mining_charter_2017 |
| week | unknown | 32 | -0.01980 | -0.01279 | 0.03875 | mining_charter_2017 |
| anticipation | all | 166 | 0.00655 | 0.00483 | 0.05526 | mining_charter_2017 |
| anticipation | mining | 15 | 0.01491 | 0.02525 | 0.05629 | mining_charter_2017 |
| anticipation | non_mining | 118 | 0.00684 | 0.00262 | 0.05533 | mining_charter_2017 |
| anticipation | unknown | 33 | 0.00171 | 0.01422 | 0.05574 | mining_charter_2017 |
| plot | all | 164 | -0.00522 | -0.00914 | 0.07218 | mining_charter_2017 |
| plot | mining | 15 | 0.01285 | 0.01813 | 0.09373 | mining_charter_2017 |
| plot | non_mining | 117 | -0.00668 | -0.01386 | 0.07153 | mining_charter_2017 |
| plot | unknown | 32 | -0.00835 | -0.00914 | 0.06404 | mining_charter_2017 |
| primary | all | 176 | 0.00493 | 0.00253 | 0.04304 | mining_charter_2018 |
| primary | mining | 16 | -0.01496 | -0.00317 | 0.04263 | mining_charter_2018 |
| primary | non_mining | 130 | 0.00690 | 0.00441 | 0.04574 | mining_charter_2018 |
| primary | unknown | 30 | 0.00699 | 0.00139 | 0.02631 | mining_charter_2018 |
| short | all | 175 | 0.00995 | 0.00107 | 0.05566 | mining_charter_2018 |
| short | mining | 16 | 0.01558 | 0.00098 | 0.05781 | mining_charter_2018 |
| short | non_mining | 129 | 0.00894 | 0.00107 | 0.05943 | mining_charter_2018 |
| short | unknown | 30 | 0.01131 | 0.00122 | 0.03525 | mining_charter_2018 |
| week | all | 176 | 0.00243 | -0.00243 | 0.07429 | mining_charter_2018 |
| week | mining | 16 | 0.03635 | 0.03396 | 0.07033 | mining_charter_2018 |
| week | non_mining | 130 | 0.00064 | -0.00529 | 0.07722 | mining_charter_2018 |
| week | unknown | 30 | -0.00789 | 0.00412 | 0.05880 | mining_charter_2018 |
| anticipation | all | 174 | -0.00114 | -0.00421 | 0.09461 | mining_charter_2018 |
| anticipation | mining | 16 | 0.08943 | 0.04401 | 0.14837 | mining_charter_2018 |
| anticipation | non_mining | 128 | -0.01444 | -0.01396 | 0.08652 | mining_charter_2018 |
| anticipation | unknown | 30 | 0.00735 | 0.00711 | 0.06201 | mining_charter_2018 |
| plot | all | 173 | 0.01241 | 0.00589 | 0.15333 | mining_charter_2018 |
| plot | mining | 16 | 0.17522 | 0.14785 | 0.16009 | mining_charter_2018 |
| plot | non_mining | 128 | -0.00965 | -0.01346 | 0.15007 | mining_charter_2018 |
| plot | unknown | 29 | 0.01998 | 0.04033 | 0.10534 | mining_charter_2018 |
| primary | all | 169 | -0.00197 | -0.00283 | 0.02722 | ee_draft_2023 |
| primary | mining | 25 | -0.00098 | -0.00508 | 0.02039 | ee_draft_2023 |
| primary | non_mining | 133 | -0.00214 | -0.00272 | 0.02820 | ee_draft_2023 |
| primary | unknown | 11 | -0.00206 | -0.00152 | 0.03080 | ee_draft_2023 |
| short | all | 166 | -0.01363 | -0.01890 | 0.04774 | ee_draft_2023 |
| short | mining | 24 | -0.02704 | -0.03359 | 0.03220 | ee_draft_2023 |
| short | non_mining | 131 | -0.01086 | -0.01368 | 0.04888 | ee_draft_2023 |
| short | unknown | 11 | -0.01739 | -0.03138 | 0.06012 | ee_draft_2023 |
| week | all | 164 | -0.01328 | -0.01093 | 0.05007 | ee_draft_2023 |
| week | mining | 22 | -0.02100 | -0.01749 | 0.03655 | ee_draft_2023 |
| week | non_mining | 131 | -0.01159 | -0.00939 | 0.05091 | ee_draft_2023 |
| week | unknown | 11 | -0.01798 | -0.01514 | 0.06460 | ee_draft_2023 |
| anticipation | all | 161 | -0.01826 | -0.02025 | 0.06693 | ee_draft_2023 |
| anticipation | mining | 22 | 0.01453 | 0.00409 | 0.08014 | ee_draft_2023 |
| anticipation | non_mining | 129 | -0.02131 | -0.02122 | 0.06009 | ee_draft_2023 |
| anticipation | unknown | 10 | -0.05109 | -0.05182 | 0.09665 | ee_draft_2023 |
| plot | all | 157 | -0.01931 | -0.02914 | 0.09476 | ee_draft_2023 |
| plot | mining | 21 | -0.01966 | -0.02312 | 0.08232 | ee_draft_2023 |
| plot | non_mining | 126 | -0.01564 | -0.03029 | 0.09505 | ee_draft_2023 |
| plot | unknown | 10 | -0.06487 | -0.06784 | 0.11230 | ee_draft_2023 |
| primary | all | 160 | -0.00116 | -0.00566 | 0.03021 | ee_final_2025 |
| primary | mining | 22 | 0.02350 | 0.03520 | 0.03396 | ee_final_2025 |
| primary | non_mining | 134 | -0.00528 | -0.00716 | 0.02759 | ee_final_2025 |
| primary | unknown | 4 | 0.00091 | -0.01135 | 0.03652 | ee_final_2025 |
| short | all | 158 | 0.00141 | 0.00072 | 0.04175 | ee_final_2025 |
| short | mining | 22 | -0.01202 | -0.02837 | 0.05017 | ee_final_2025 |
| short | non_mining | 132 | 0.00408 | 0.00364 | 0.03890 | ee_final_2025 |
| short | unknown | 4 | -0.01268 | -0.00399 | 0.07502 | ee_final_2025 |
| week | all | 157 | 0.00388 | 0.00842 | 0.04954 | ee_final_2025 |
| week | mining | 21 | -0.01315 | -0.00620 | 0.06065 | ee_final_2025 |
| week | non_mining | 132 | 0.00699 | 0.00847 | 0.04509 | ee_final_2025 |
| week | unknown | 4 | -0.00932 | -0.00208 | 0.10772 | ee_final_2025 |
| anticipation | all | 159 | -0.01482 | -0.01704 | 0.06001 | ee_final_2025 |
| anticipation | mining | 22 | 0.01658 | 0.01348 | 0.09764 | ee_final_2025 |
| anticipation | non_mining | 133 | -0.01916 | -0.01775 | 0.05004 | ee_final_2025 |
| anticipation | unknown | 4 | -0.04314 | -0.02218 | 0.06011 | ee_final_2025 |
| plot | all | 155 | -0.00048 | 0.00170 | 0.06759 | ee_final_2025 |
| plot | mining | 21 | -0.02597 | -0.01587 | 0.08135 | ee_final_2025 |
| plot | non_mining | 130 | 0.00435 | 0.00246 | 0.06408 | ee_final_2025 |
| plot | unknown | 4 | -0.02379 | -0.00161 | 0.08692 | ee_final_2025 |
| primary | all | 160 | 0.01578 | 0.01918 | 0.03275 | bbbee_draft_2026 |
| primary | mining | 22 | -0.00799 | -0.00536 | 0.04573 | bbbee_draft_2026 |
| primary | non_mining | 137 | 0.01952 | 0.02012 | 0.02872 | bbbee_draft_2026 |
| primary | unknown | 1 | 0.02602 | 0.02602 | NA | bbbee_draft_2026 |
| short | all | 159 | 0.01460 | 0.01989 | 0.04672 | bbbee_draft_2026 |
| short | mining | 22 | -0.01131 | -0.01066 | 0.06909 | bbbee_draft_2026 |
| short | non_mining | 136 | 0.01867 | 0.02085 | 0.04104 | bbbee_draft_2026 |
| short | unknown | 1 | 0.03128 | 0.03128 | NA | bbbee_draft_2026 |
| week | all | 158 | 0.02034 | 0.02721 | 0.05746 | bbbee_draft_2026 |
| week | mining | 22 | -0.02373 | -0.01669 | 0.07215 | bbbee_draft_2026 |
| week | non_mining | 135 | 0.02728 | 0.03040 | 0.05174 | bbbee_draft_2026 |
| week | unknown | 1 | 0.05236 | 0.05236 | NA | bbbee_draft_2026 |
| anticipation | all | 157 | -0.00439 | -0.00528 | 0.06160 | bbbee_draft_2026 |
| anticipation | mining | 22 | 0.03491 | 0.03284 | 0.06734 | bbbee_draft_2026 |
| anticipation | non_mining | 134 | -0.01098 | -0.00929 | 0.05858 | bbbee_draft_2026 |
| anticipation | unknown | 1 | 0.01445 | 0.01445 | NA | bbbee_draft_2026 |
| plot | all | 155 | 0.01402 | 0.02409 | 0.08829 | bbbee_draft_2026 |
| plot | mining | 22 | 0.00606 | 0.02308 | 0.09278 | bbbee_draft_2026 |
| plot | non_mining | 132 | 0.01475 | 0.02496 | 0.08789 | bbbee_draft_2026 |
| plot | unknown | 1 | 0.09342 | 0.09342 | NA | bbbee_draft_2026 |

## Exposure analysis

For mining events, unadjusted CAR-on-industry-indicator coefficients equal the portfolio mean difference. Historical industry membership is a provisional exposure proxy, not verified legal treatment. Financial controls, EE target gaps and historical B-BBEE levels are missing.

## Robustness and placebos

Robustness execution: full configured checks
See robustness_summary.csv for re-estimated sensitivity results and placebo_results.csv for seeded, independently refitted pseudo-events. Frozen industry snapshots and unscreened unrelated news limit placebo interpretation.

## Interpretation and limitations

Results describe conditional abnormal price movements around public-policy dates. They do not identify causal policy effects or realised efficiency costs. Non-mining firms may be indirectly affected. The benchmark contains affected firms and may absorb broad policy responses.
Anticipation is material in 2017 and 2018. The 2025 window may overlap major tariff/trade news. The 2026 proposal bundle lacks a credible unaffected group. Insignificance is not evidence that a policy had no economic effect.
Corporate-action and dividend adjustments are unverified. Extreme movements remain in the baseline and can materially distort raw-price CARs. The complete source extreme-return audit and deletion sensitivity must be reviewed.
Issuer identities, security classes, listing histories and historical ISIN validity are incomplete. Equal security weights can overweight issuers with several securities. No issuer-level interpretation is claimed.
Historical bulletin reporting dates precede events, but publication availability is unverified. Strict availability-verified exposure analysis is unsupported. Source calendar and historical universe are not fully externally certified.

## Outstanding work and readiness

Preliminary results produced; methodological review required. Verify adjustment conventions and corporate actions for influential firms, release timing, historical identity/exposure matches, issuer concentration and null-volatility assumptions before thesis use.
Inspect recorded automated test outcomes separately in outputs/diagnostics/test_summary.md. Execution success alone does not establish research readiness.
