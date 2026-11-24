# Methodological corrections and statistical remediation

Prepared for independent re-review. The immutable source package and event register are unchanged. The pre-remediation code, tables, diagnostics, figures and local derived data are archived in outputs/baselines/pre_remediation_2026-11-24/.

## Overall status

All five events have supported revised baseline results.
Deterministic defects M2/S1/N1 are corrected. M1 is corrected for the verified Reinet conversion but remains partial for distributions, rights and provider conventions. Timing, news, exposure and selection audits are implemented; causal identification and complete historical mappings remain unresolved. Conditional bootstrap inference is retained; no volatility-robust guarantee is claimed.

## Primary choices and updated results

Preferred return: security-unit-consistent price return. Verified unit conversions are applied from research/corporate_actions_v1.csv; raw closes and raw returns are retained. Cash distributions are not selectively added to an otherwise price-only series. This is not total shareholder return.
Primary inference retains the original absolute-tail bootstrap p-value. The reported symmetric interval now inverts that same finite-draw p<0.05 rule. The five-session synchronous bootstrap includes OLS fitting error and the actual fit/event gap. Full baseline inference uses 4,999 draws; see each inference row for actual replication counts.
The five registered [0,+1] hypotheses are fixed in config/headline_hypotheses.csv, independently of selected events. Intervals are pointwise; Holm conclusions address the five-test family.

| event_id | n_mining | n_control | n_all | estimate_pct | ci_lower_pct | ci_upper_pct | p_value | holm_primary_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| mining_charter_2017 | 15 | 120 | 168 | -3.49432 | -8.44075 | 1.45212 | 0.1620 | 0.648 |
| mining_charter_2018 | 16 | 130 | 176 | -2.21674 | -5.69151 | 1.25804 | 0.1814 | 0.648 |
| ee_draft_2023 | 0 | 0 | 169 | -0.19669 | -1.32893 | 0.93556 | 0.7056 | 1.000 |
| ee_final_2025 | 0 | 0 | 160 | -0.11641 | -1.03427 | 0.80145 | 0.7842 | 1.000 |
| bbbee_draft_2026 | 0 | 0 | 160 | 1.57757 | 0.50322 | 2.65192 | 0.0134 | 0.067 |

Mining estimates are percentage-point mining-minus-control differences; other rows are aggregate CAAR in percent. Security counts are not verified issuer counts.

## Before and after

| event_id | estimate_before_pp | estimate_after_pp | change_pp | raw_p_before | raw_p_after | holm_before | holm_after |
| --- | --- | --- | --- | --- | --- | --- | --- |
| bbbee_draft_2026 | 1.577571 | 1.577571 | 0.000000 | 0.0134 | 0.0134 | 0.067 | 0.067 |
| ee_draft_2023 | -0.196685 | -0.196685 | 0.000000 | 0.7056 | 0.7056 | 1.000 | 1.000 |
| ee_final_2025 | -0.116407 | -0.116407 | 0.000000 | 0.7842 | 0.7842 | 1.000 | 1.000 |
| mining_charter_2017 | -3.494316 | -3.494316 | 0.000000 | 0.1620 | 0.1620 | 0.648 | 0.648 |
| mining_charter_2018 | -2.185924 | -2.216735 | -0.030812 | 0.1894 | 0.1814 | 0.648 | 0.648 |

Before intervals used equal-tailed basic quantiles while p-values used absolute tails. After intervals use absolute-tail inversion. Thus interval changes are not all consequences of the Reinet correction. Isolated convention and donor-mask comparisons are recorded separately under diagnostics/remediation/.

## M1 — Return measurement

The original RNI 29 November 2017 ratio was +886.1667%. The official FTSE/JSE notice confirms ten depositary receipts became one ordinary share. Only that date is adjusted: gross raw return divided by 10 gives −1.3833%. No source price changes and no guessed corporate-action factors are used.
The ledger records version, effective date, type, factor/cash amount, units, evidence, verification status, application status and unresolved cases. corporate_action_application.csv is the executed audit. Reinet corrections propagate through model fitting, residual donors, AR/CAR/CAAR and inference.
MTNZF R20 capital distribution and Aveng rights ex-date are verified actions, but a provider-consistent return adjustment is unresolved. They remain explicit price-series limitations with a targeted security-exclusion sensitivity. Lonmin’s influential jump has no verified factor and is retained. The documented Steinhoff news collapse is not automatically corrected away.

| event_id | instrument_id | alpha_before | alpha_after | beta_before | beta_after | sigma_before | sigma_after |
| --- | --- | --- | --- | --- | --- | --- | --- |
| mining_charter_2018 | RNI:XJSE:EQU | 0.0395963 | -0.0003617 | 2.84719 | 0.2390842 | 0.597084 | 0.0147788 |

JSE distinguishes J203 All Share from J203T Total Return, supporting price-index-compatible intent. The exact IRESS exported variant and equity distribution conventions still require provider verification; benchmark_convention_audit.csv states this limitation.

## M2 — Complete extreme-deletion mask

Fit/event usability and donor validity are now separate fields. Full extreme deletion sets both false; the bootstrap constructs its complete-date donor matrix only from eligible donor residuals. Baseline volume policy remains separate. New regression tests prove a flagged observation cannot re-enter the null.
The reviewer’s numerical mask diagnostic is reproduced on preserved ORIGINAL prices, isolating the defect from conversion changes. New production sensitivities additionally use the revised analytical returns, so their values need not match those old-price diagnostics.

| event_id | legacy_se | full_exclusion_se | legacy_p | full_exclusion_p | null_dates_before | null_dates_after | reference_se_error | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| mining_charter_2017 | 0.0251956 | 0.0240515 | 0.1654 | 0.1392 | 221 | 217 | 0 | reviewer diagnostic reproduced on preserved raw-price input |
| mining_charter_2018 | 0.0199195 | 0.0169594 | 0.2284 | 0.2160 | 217 | 203 | 0 | reviewer diagnostic reproduced on preserved raw-price input |
| ee_draft_2023 | 0.0055600 | 0.0052018 | 0.7028 | 0.6898 | 221 | 211 | 0 | reviewer diagnostic reproduced on preserved raw-price input |
| ee_final_2025 | 0.0046598 | 0.0047128 | 0.8018 | 0.7944 | 221 | 214 | 0 | reviewer diagnostic reproduced on preserved raw-price input |
| bbbee_draft_2026 | 0.0053860 | 0.0050436 | 0.0120 | 0.0106 | 221 | 211 | 0 | reviewer diagnostic reproduced on preserved raw-price input |

## M3/M4 — Information timing and economic interpretation

Official publication dates remain the baseline. A sourced chronology distinguishes the 2018 Cabinet reference, public 21 September stimulus/approval statement, 26 September advisory and 27 September gazetting. Earlier windows are exploratory information-event comparisons, never selected by significance.
timing_comparisons.csv provides re-estimated comparisons; fixed_sample_2018_timing.csv freezes baseline coefficients and common constituents to isolate timing. The negative gazette window is not a stable negative reaction to the entire 2018 information sequence.
The 2017 two sessions are 15 and 19 June. News records identify 2023 diplomatic overlap, 2025 tariff-related outlook information with intraday caveats, and 2026 domestic/global monetary and market developments. Date overlap is not proof of a causal price effect.
Day +1 contributes 87.1% of the 2026 CAAR. The sum of daily equal-security raw returns is -0.9976%; positive abnormal performance is relative to the fitted benchmark, not a positive wealth change.

| event_id | date | tau | market_return | n | raw_quote_return | analytical_price_return | predicted_return | abnormal_return | portfolio |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bbbee_draft_2026 | 2026-01-29 | 0 | 0.001438 | 160 | 0.002828 | 0.002828 | 0.000797 | 0.002031 | all |
| bbbee_draft_2026 | 2026-01-30 | 1 | -0.041544 | 160 | -0.012804 | -0.012804 | -0.026549 | 0.013745 | all |

primary_security_contributions.csv and primary_industry_contributions.csv show concentration on fixed complete samples. No additional external return dataset was imported. The market-adjusted alternative uses existing J203 data; it imposes different normal-return restrictions and does not isolate policy news.
The 2026 group and largest industry contributions below are in percent/percentage points; they show heterogeneous relative performance, not measured legal policy exposure. Banks and REITs are important contributors, while the source-classified mining group has a negative average CAR.

| event_id | group | n | mean_car | contribution_to_all_caar |
| --- | --- | --- | --- | --- |
| bbbee_draft_2026 | non_mining | 137 | 1.95171 | 1.67115 |
| bbbee_draft_2026 | mining | 22 | -0.79886 | -0.10984 |
| bbbee_draft_2026 | unknown | 1 | 2.60236 | 0.01626 |

| nature_of_business_raw | n | mean_car_pct | contribution_pp |
| --- | --- | --- | --- |
| Diversified REITs | 11 | 2.84138 | 0.19534 |
| Banks | 6 | 4.73364 | 0.17751 |
| Gen Mining | 8 | 2.25831 | 0.11292 |
| Life Ins | 4 | 4.25188 | 0.10630 |
| Food Prod | 6 | 2.74196 | 0.10282 |
| Asset Managers and Custodians | 7 | 2.09824 | 0.09180 |
| Appar Retail | 3 | 4.85044 | 0.09095 |
| Open End and Misc Inv Veh | 1 | 11.99748 | 0.07498 |


## M5 — Uncertainty and alternative inference

Conditional synchronous inference remains primary. Added scenarios vary block length, early/late donor periods, all-active donor dates and EVENT-INNOVATION SD multipliers 1.5/2; the multiplier does not scale OLS estimation error. These are scenarios, not estimated event-volatility adjustments.
A restricted BMP/KP-style standardized-CAR diagnostic is supplied for aggregate portfolios only. It concerns mean standardized CAR, not the signed mining/control contrast or raw equal-security CAAR. It assumes temporally independent innovations and representative cross-sectional correlation. It is not silently substituted as primary, and its unadjusted exploratory p-values do not create headline discoveries.
Synchronous multi-security calibration uses common and mining-sector shocks, different firm fit masks, heavy tails, serial dependence, and both proportional event-volatility and factor-only correlation changes. All simulations have zero true mean effect. Rejection and coverage Monte Carlo intervals are reported; these do not estimate real-data false-positive rates.
Executed calibration: 400 trials/scenario and 12 securities. Conditional-bootstrap rejection is 4.25% for the stable aggregate and 6.00% for the stable spread; under doubled event residual SD the rates are 31.75% / 34.50%. The KP-style aggregate rate is 3.75% under proportional event scaling, 11.25% under skewness and 21.25% under factor-only event shocks. Its different estimand and these vulnerabilities prevent promotion to headline inference.

| scenario | trials | rejection_rate | interval_coverage | method | bootstrap_draws | securities | rejection_mc_lower | rejection_mc_upper | coverage_mc_lower | coverage_mc_upper |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| stable_gaussian | 400 | 0.0425 | 0.9575 | all | 999 | 12 | 0.02670 | 0.06700 | 0.93300 | 0.97330 |
| serial_AR06 | 400 | 0.0550 | 0.9450 | all | 999 | 12 | 0.03660 | 0.08187 | 0.91813 | 0.96340 |
| heavy_tails_t5 | 400 | 0.0675 | 0.9325 | all | 999 | 12 | 0.04680 | 0.09643 | 0.90357 | 0.95320 |
| centered_lognormal | 400 | 0.0325 | 0.9675 | all | 999 | 12 | 0.01909 | 0.05480 | 0.94520 | 0.98091 |
| event_all_residual_sd2 | 400 | 0.3175 | 0.6825 | all | 999 | 12 | 0.27380 | 0.36467 | 0.63533 | 0.72620 |
| event_factor_sd2 | 400 | 0.2825 | 0.7175 | all | 999 | 12 | 0.24061 | 0.32853 | 0.67147 | 0.75939 |
| stable_gaussian | 400 | 0.0600 | 0.9400 | mining_minus_control | 999 | 12 | 0.04065 | 0.08772 | 0.91228 | 0.95935 |
| serial_AR06 | 400 | 0.0650 | 0.9350 | mining_minus_control | 999 | 12 | 0.04474 | 0.09354 | 0.90646 | 0.95526 |
| heavy_tails_t5 | 400 | 0.0450 | 0.9550 | mining_minus_control | 999 | 12 | 0.02865 | 0.07001 | 0.92999 | 0.97135 |
| centered_lognormal | 400 | 0.0575 | 0.9425 | mining_minus_control | 999 | 12 | 0.03862 | 0.08480 | 0.91520 | 0.96138 |
| event_all_residual_sd2 | 400 | 0.3450 | 0.6550 | mining_minus_control | 999 | 12 | 0.30009 | 0.39286 | 0.60714 | 0.69991 |
| event_factor_sd2 | 400 | 0.2675 | 0.7325 | mining_minus_control | 999 | 12 | 0.22648 | 0.31294 | 0.68706 | 0.77352 |
| stable_gaussian | 400 | 0.3075 | NA | bmp_all | 999 | 12 | 0.26429 | 0.35438 | NA | NA |
| serial_AR06 | 400 | 0.3325 | NA | bmp_all | 999 | 12 | 0.28812 | 0.38007 | NA | NA |
| heavy_tails_t5 | 400 | 0.3300 | NA | bmp_all | 999 | 12 | 0.28573 | 0.37751 | NA | NA |
| centered_lognormal | 400 | 0.3525 | NA | bmp_all | 999 | 12 | 0.30729 | 0.40052 | NA | NA |
| event_all_residual_sd2 | 400 | 0.3025 | NA | bmp_all | 999 | 12 | 0.25954 | 0.34922 | NA | NA |
| event_factor_sd2 | 400 | 0.5175 | NA | bmp_all | 999 | 12 | 0.46860 | 0.56607 | NA | NA |
| stable_gaussian | 400 | 0.0400 | 0.9600 | kp_style_all | 999 | 12 | 0.02477 | 0.06398 | 0.93602 | 0.97523 |
| serial_AR06 | 400 | 0.0375 | 0.9625 | kp_style_all | 999 | 12 | 0.02285 | 0.06094 | 0.93906 | 0.97715 |
| heavy_tails_t5 | 400 | 0.0525 | 0.9475 | kp_style_all | 999 | 12 | 0.03459 | 0.07892 | 0.92108 | 0.96541 |
| centered_lognormal | 400 | 0.1125 | 0.8875 | kp_style_all | 999 | 12 | 0.08515 | 0.14722 | 0.85278 | 0.91485 |
| event_all_residual_sd2 | 400 | 0.0375 | 0.9625 | kp_style_all | 999 | 12 | 0.02285 | 0.06094 | 0.93906 | 0.97715 |
| event_factor_sd2 | 400 | 0.2125 | 0.7875 | kp_style_all | 999 | 12 | 0.17524 | 0.25523 | 0.74477 | 0.82476 |

## S1/S2/S3/S4/N1 — Additional corrections

S1: asymmetric/tied-distribution tests verify agreement of primary p-values and confidence intervals. Legacy basic intervals and equal-tail probabilities remain auxiliary columns for comparison, not alternative primary evidence.
S2: a versioned event-dated security/issuer/exposure ledger records verified and unresolved evidence. Baseline source-industry groups and equal-security weights remain explicit. The reviewed industry alternative moves verified KIO mining operations into mining and excludes manufacturing Hulamin from the direct-mining proxy; neither establishes uniform legal treatment. Partial issuer weighting combines only verified Fortress A/B classes. Unknown historic identifiers are not assigned using current names.
S3: pseudo-event fitting windows now exclude their own real policy event. Fixed candidate horizons and spacing can produce fewer than ten dates for 2017; shortfalls are reported, not filled with contaminated windows. Frozen classifications and other news remain limitations. The unavailable 29 December 2023 EE-final placebo remains N=0/NA because J203 is missing on 2 January 2024.

| event_id | target | selected | shortfall | own_event_excluded_from_fit | classification_status |
| --- | --- | --- | --- | --- | --- |
| mining_charter_2017 | 10 | 6 | 4 | TRUE | frozen event snapshot; historical pseudo-date availability not verified |
| mining_charter_2018 | 10 | 10 | 0 | TRUE | frozen event snapshot; historical pseudo-date availability not verified |
| ee_draft_2023 | 10 | 10 | 0 | TRUE | frozen event snapshot; historical pseudo-date availability not verified |
| ee_final_2025 | 10 | 10 | 0 | TRUE | frozen event snapshot; historical pseudo-date availability not verified |
| bbbee_draft_2026 | 10 | 10 | 0 | TRUE | frozen event snapshot; historical pseudo-date availability not verified |

S4: separate event-only and donor-only volume sensitivities isolate observability choices from fit-period liquidity. Existing minimum-observation and unchanged-price screens remain configurable. The target is eligible observable/liquid JSE securities, not a survivorship-free universe of South African firms.
N1: an explicit five-row hypothesis registry determines headline membership and Holm family size. Custom event lists and single-event runs cannot reduce the family; tests cover narrow configurations.

## Selected sensitivities

| event_id | specification | n | estimate | se | p_value | status |
| --- | --- | --- | --- | --- | --- | --- |
| mining_charter_2017 | event_no_volume_screen | 135 | -0.034943 | 0.025195 | 0.1620 | ok |
| mining_charter_2017 | null_active_dates | 135 | -0.034943 | 0.028569 | 0.2446 | ok |
| mining_charter_2017 | event_sd_1p5 | 135 | -0.034943 | 0.037686 | 0.3366 | ok |
| mining_charter_2017 | event_sd_2 | 135 | -0.034943 | 0.050201 | 0.4480 | ok |
| mining_charter_2017 | donor_early | 135 | -0.034943 | 0.025198 | 0.1852 | ok |
| mining_charter_2017 | donor_late | 135 | -0.034943 | 0.024686 | 0.1338 | ok |
| mining_charter_2017 | exclude_unresolved_action_securities | 134 | -0.037843 | 0.023937 | 0.1216 | ok |
| mining_charter_2017 | reviewed_industry_proxy | 134 | -0.036704 | 0.026822 | 0.1662 | ok |
| mining_charter_2017 | partial_verified_issuer | 135 | -0.034943 | 0.025195 | 0.1620 | ok |
| mining_charter_2018 | event_no_volume_screen | 146 | -0.022167 | 0.017912 | 0.1814 | ok |
| mining_charter_2018 | null_active_dates | 146 | -0.022167 | 0.020182 | 0.2372 | ok |
| mining_charter_2018 | event_sd_1p5 | 146 | -0.022167 | 0.026761 | 0.3226 | ok |
| mining_charter_2018 | event_sd_2 | 146 | -0.022167 | 0.035632 | 0.4988 | ok |
| mining_charter_2018 | donor_early | 146 | -0.022167 | 0.019838 | 0.2134 | ok |
| mining_charter_2018 | donor_late | 146 | -0.022167 | 0.014728 | 0.1376 | ok |
| mining_charter_2018 | exclude_unresolved_action_securities | 145 | -0.019353 | 0.017954 | 0.2214 | ok |
| mining_charter_2018 | reviewed_industry_proxy | 145 | -0.019498 | 0.018694 | 0.2378 | ok |
| mining_charter_2018 | partial_verified_issuer | 146 | -0.022167 | 0.017912 | 0.1814 | ok |
| ee_draft_2023 | event_no_volume_screen | 170 | -0.002102 | 0.005531 | 0.6774 | ok |
| ee_draft_2023 | null_active_dates | 169 | -0.001967 | 0.006048 | 0.8892 | ok |
| ee_draft_2023 | event_sd_1p5 | 169 | -0.001967 | 0.008313 | 0.8026 | ok |
| ee_draft_2023 | event_sd_2 | 169 | -0.001967 | 0.011070 | 0.8468 | ok |
| ee_draft_2023 | donor_early | 169 | -0.001967 | 0.005570 | 0.7304 | ok |
| ee_draft_2023 | donor_late | 169 | -0.001967 | 0.005599 | 0.6812 | ok |
| ee_draft_2023 | exclude_unresolved_action_securities | 169 | -0.001967 | 0.005561 | 0.7056 | ok |
| ee_draft_2023 | partial_verified_issuer | 169 | -0.001926 | 0.005557 | 0.7080 | ok |
| ee_final_2025 | event_no_volume_screen | 161 | -0.001126 | 0.004671 | 0.7912 | ok |
| ee_final_2025 | null_active_dates | 160 | -0.001164 | 0.005099 | 0.8058 | ok |
| ee_final_2025 | event_sd_1p5 | 160 | -0.001164 | 0.006969 | 0.8664 | ok |
| ee_final_2025 | event_sd_2 | 160 | -0.001164 | 0.009282 | 0.9110 | ok |
| ee_final_2025 | donor_early | 160 | -0.001164 | 0.004911 | 0.7842 | ok |
| ee_final_2025 | donor_late | 160 | -0.001164 | 0.004026 | 0.7402 | ok |
| ee_final_2025 | exclude_unresolved_action_securities | 160 | -0.001164 | 0.004662 | 0.7842 | ok |
| ee_final_2025 | partial_verified_issuer | 160 | -0.001164 | 0.004662 | 0.7842 | ok |
| bbbee_draft_2026 | event_no_volume_screen | 160 | 0.015776 | 0.005406 | 0.0134 | ok |
| bbbee_draft_2026 | null_active_dates | 160 | 0.015776 | 0.007049 | 0.0502 | ok |
| bbbee_draft_2026 | event_sd_1p5 | 160 | 0.015776 | 0.007988 | 0.0502 | ok |
| bbbee_draft_2026 | event_sd_2 | 160 | 0.015776 | 0.010594 | 0.1212 | ok |
| bbbee_draft_2026 | donor_early | 160 | 0.015776 | 0.005497 | 0.0188 | ok |
| bbbee_draft_2026 | donor_late | 160 | 0.015776 | 0.005150 | 0.0048 | ok |
| bbbee_draft_2026 | exclude_unresolved_action_securities | 159 | 0.015120 | 0.005041 | 0.0112 | ok |
| bbbee_draft_2026 | partial_verified_issuer | 160 | 0.015776 | 0.005406 | 0.0134 | ok |

All rows in this section are exploratory. Their individual p-values do not correct for searching across specifications. Larger or smaller p-values were not a criterion for selecting the correction method.
The 2026 positive point estimate persists across many same-date screens, but its raw p is sensitive to donor selection and volatility assumptions: inspect the all-active donor and event-SD scenarios rather than treating baseline significance as universal. No scenario is selected to obtain or remove significance.

## Validation and reproduction

Matched post-run tests: 31 cases; 395 passed expectations; 0 failed; 0 errors; 0 skipped.
The pre-correction all-event run and 331-expectation tests reproduced before analytical edits. All nine original CSV tables were byte-identical; the archive includes code/config/source fingerprints and reproduction logs.
Current independent NumPy OLS/return/CAR checks, component regressions, p/interval checks, CLI selection checks and source/archival preservation evidence are under outputs/diagnostics/remediation/. Run-specific code/config/ledger hashes are in diagnostics/run_metadata.json. Tests carry an inference-table and code fingerprint to prevent stale pass claims.

From the repository root:

```sh
Rscript mon_thesis/run_analysis.R --all
Rscript mon_thesis/tests/testthat.R
Rscript mon_thesis/review/remediation/validate_components.R
iress-export/.venv/bin/python mon_thesis/review/remediation/verify_corrected.py
Rscript mon_thesis/review/remediation/calibrate_inference.R
Rscript mon_thesis/review/remediation/finalize_handover.R
```

Single-event interface remains Rscript mon_thesis/run_analysis.R --event mining_charter_2017. It overwrites latest-run aggregates; use an isolated copy for comparisons. See review/remediation/README.md for portable Python selection and archive restoration.

## Remaining limitations and next review priorities

1. Highest priority: provider-adjustment conventions, complete capital/rights/distribution histories and economically consistent equity/benchmark returns. Only the sourced security-unit correction is approved here.
2. First disclosures and concurrent news, especially 2018 approval/stimulus versus gazetting and the 2026 stress-day contribution. Two daily observations do not isolate a causal policy effect or identify event volatility.
3. Historical security/issuer identities, legal/geographic exposure and selection into observable/liquid event samples. Dated workforce/compliance/financial controls remain absent.
4. Independent assessment of the conditional residual process, block choice, standardized diagnostic assumptions, finite-draw inversion and simulation design. A passing implementation does not settle these research assumptions.

## Research readiness

Suitable for independent methodological re-review and preliminary supervisor discussion, accompanied by the explicit partial/unresolved items. Not thesis-final causal or efficiency-cost evidence. Failure to reject is not proof of no economic effect. No full reader-facing R Markdown report was written in this pass.

Research choices, alternatives and required supervisor decisions are recorded in docs/research_decisions.md. No remote push, licensed-data distribution or supervisor contact was performed.
