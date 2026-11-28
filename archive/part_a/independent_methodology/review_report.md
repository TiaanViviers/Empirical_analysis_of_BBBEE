# Independent econometric and statistical methodology review — Part A

> Historical review of the pre-remediation implementation. Current working outputs have changed; original code/results and this report are archived under `outputs/baselines/pre_remediation_2026-11-24/`. Read [the corrections report](methodological_corrections_report.md) for current status.

**Audit date:** 24 November 2026, Africa/Johannesburg.  
**Scope:** the current working-tree implementation and all five events, after the three corrections identified in the earlier software review. Repository HEAD remains `8a9c45e`; the new analysis is uncommitted. This review evaluates the submitted files and results, rather than treating the passing tests as methodological validation.

## 1. Overall verdict

**Part A is a reproducible and useful preliminary descriptive event study, suitable for supervisor discussion with this review attached. It is not ready for thesis-final statistical or policy-effect claims.**

The return arithmetic, event-specific OLS estimates, CAR/CAAR identities, fixed portfolio weights, baseline bootstrap algebra and default five-test Holm calculations reproduce. The earlier estimation-to-event-gap, singleton-block-start and headline-export defects have been corrected. There is no evidence of an accidental join multiplication or use of event observations in baseline OLS fitting.

However, there is a demonstrated corporate-action discontinuity in a baseline control, an incomplete implementation of the extreme-deletion sensitivity, substantial announcement-timing and overlapping-news problems, and no established protection against event-induced volatility. The strongest positive result, January 2026, is a relative-to-benchmark outcome concentrated on a day of pronounced market stress. It cannot presently be interpreted as an isolated B-BBEE policy response.

No additional **Critical** implementation failure that invalidates every calculation was established. The **Major** findings below prevent a thesis-final interpretation. Some require code or data corrections; others require a narrower estimand and substantive research decisions. These are different kinds of problem.

Original source data, the event register, analysis modules, configuration, derived datasets and existing headline outputs were preserved. Full reproduction and the existing test suite ran in an isolated copy. Additional scripts are in [review/independent_methodology](../../../archive/part_a/independent_methodology/README.md); their evidence is in [diagnostics/independent_review](../diagnostics/independent_review).

## 2. Current headline results and status of the previous fixes

All estimates below use [0,+1]. Mining estimates are mining-minus-control differences in percentage points; the remaining estimates are aggregate CAAR in percent. Intervals are the submitted **pointwise**, unadjusted 95% intervals.

| Event | Complete securities | Estimate | 95% interval | Raw p | Holm p |
| --- | --- | ---: | --- | ---: | ---: |
| Mining Charter 2017 | 15 mining / 120 controls | −3.4943 pp | [−9.2525, +0.6537] pp | 0.1620 | 0.6480 |
| Mining Charter 2018 | 16 mining / 130 controls | −2.1859 pp | [−5.5453, +2.3988] pp | 0.1894 | 0.6480 |
| EE draft 2023 | 169 | −0.1967% | [−1.2587, +0.9566]% | 0.7056 | 1.0000 |
| EE final 2025 | 160 | −0.1164% | [−1.3244, +0.7715]% | 0.7842 | 1.0000 |
| B-BBEE draft 2026 | 160 | +1.5776% | [+0.4997, +2.6323]% | 0.0134 | 0.0670 |

Source: [headline_results_percent.csv](../tables/headline_results_percent.csv), reconciled to individual CARs and the inference table. The 2017 and 2018 all-security samples are 168 and 176; these differ from the classified spread samples of 135 and 146.

**None of the five designated baseline tests rejects at 5% after the current Holm adjustment.** The old 2026 values, 0.0108 and 0.054, have been superseded. None of the 55 baseline point estimates or security counts changed with the three corrections; uncertainty estimates changed.

Verified corrections:

- `R/05_inference.R::bootstrap_portfolio()` now samples `T + gap + L` positions and discards the actual gap. With estimation −250:−30 and [0,+1], fit positions are 1:221, gap positions 222:250, and event positions 251:252.
- `block_indices()` now samples positions using `starts[sample.int(length(starts), ...)]`. The lone-admissible-start regression test passes.
- `R/08_generate_outputs.R::write_headline_results()` now creates and refreshes the percentage table. A fresh full run generated it identically to the submitted table.

## 3. Findings ranked by severity

### Major M1 — A documented security-unit conversion is being treated as an investment return

**Evidence and location.** `R/01_construct_returns.R::compute_returns()` faithfully calculates unadjusted quote ratios. That arithmetic is not sufficient to establish economic return correctness. The 2018 non-mining control sample includes `RNI:XJSE:EQU`. Its source closes change from **3,000 on 28 November 2017 to 29,585 on 29 November**, producing a recorded return of **+886.1667%** inside the 2018 estimation period.

This is not merely an unexplained statistical outlier. The [FTSE/JSE notice of 22 November 2017](https://clientportal.jse.co.za/Content/ICANoticeItems/FTSE-JSE-Africa/20171129%20Reinet%20Conversion%20of%20Depositary%20Receipts%20Informative%20Notice.pdf) specifies that ten Reinet depositary receipts were replaced by one ordinary share on 29 November, with a tenfold price increase and corresponding share-count reduction. The raw ratio compares different security units. Applying the documented ratio to that one observation gives `29585 / (3000 × 10) − 1 = −1.3833%`.

An in-memory diagnostic using only that source-backed conversion changes Reinet's fitted parameters substantially:

| Reinet 2018 model | Submitted | One conversion corrected diagnostically |
| --- | ---: | ---: |
| Daily alpha | +3.9596% | −0.0362% |
| Beta | 2.8472 | 0.2391 |
| Daily residual SD | 59.7084% | 1.4779% |

Its contribution to the date-level pre-event spread residual variance is approximately **13.6%**, using `cov(w_i e_i, Σ_j w_j e_j) / var(Σ_j w_j e_j)` on common dates. This is a covariance decomposition of pre-event residual variance, not an exact allocation of the final bootstrap SE.

The headline effect is smaller than the firm-level distortion: correcting this one return changes the 2018 spread from **−2.1859 to −2.2167 pp**, its SE from **1.9857 to 1.7912 pp**, and raw p from **0.1894 to 0.1814**. Omitting Reinet gives −2.2295 pp and p=0.1804. Thus this example does **not** reverse the baseline inference; it establishes that an important donor observation and model are economically mismeasured.

A second example concerns `MTNZF:XJSE:EQU` in the 2026 portfolio. The recorded close falls 2,110→105 on **23 July 2025**, giving −95.0237%. The issuer's [special-distribution communication](https://mtnzakhelefuthi.nedsecure.co.za/Home/DownloadForms?iFilename=UnwindSMSEmailers.pdf) confirms a R20 capital payout, and its [15 July finalisation announcement](https://www.i-ex.co.za/Library/FileDownloader.ashx?DocumentID=4187779) identifies 23 July as the ex-distribution date. **Conditional on Close being in cents**, including the R20 payment gives `(105 + 2000) / 2110 − 1 = −0.2370%`. Provider units have not been certified, so this is an explicit diagnostic assumption, not an approved adjustment. Other MTNZF jumps remain, including +237.14% on 25 July. One payout correction is not a complete treatment of the unwinding scheme.

**Required correction.** Obtain provider adjustment definitions and build a separate, sourced corporate-action/return ledger. Adjust security-unit conversions before interpreting quote changes as returns. Decide and document how dividends, capital distributions and rights enter the chosen return estimand, and make equity and benchmark conventions compatible. Refit models and regenerate inference from the approved derived series. Preserve the immutable source package. Do not delete all large changes indiscriminately: genuine news shocks must remain distinguishable from mechanical conversions.

Evidence: [corporate_action_model_changes.csv](../diagnostics/independent_review/corporate_action_model_changes.csv), [corporate_action_sensitivities.csv](../diagnostics/independent_review/corporate_action_sensitivities.csv), [headline_pre_event_extremes.csv](../diagnostics/independent_review/headline_pre_event_extremes.csv).

### Major M2 — The extreme-deletion sensitivity does not delete extremes from its bootstrap donor panel

**Evidence and location.** `R/02_select_samples.R::select_sample(remove_extreme=TRUE)` changes `usable` to false on flagged dates. `R/04_abnormal_returns.R::abnormal_returns()` nevertheless retains the finite `ar_raw` on those dates. `R/05_inference.R::bootstrap_portfolio()` constructs its donor matrix from **all finite `ar_raw`**, without applying the extreme-deletion mask.

Consequently, `drop_flagged_extremes` excludes flagged observations from OLS fitting and event-window usability while still resampling their pre-event shocks. A flat sensitivity result cannot establish robustness to contaminated extreme donor returns. This issue is distinct from the documented choice to retain zero-volume residuals in the baseline null.

I repeated the supplied deletion analysis, then made flagged `ar_raw` unavailable **in a diagnostic copy only**, requiring the same fixed constituents and contiguous complete donor dates:

| Event | Submitted deletion SE, pp | Fit-and-null deletion SE, pp | Submitted p | Fit-and-null p | Donor dates before→after |
| --- | ---: | ---: | ---: | ---: | --- |
| Mining 2017 | 2.5196 | 2.4052 | 0.1654 | 0.1392 | 221→217 |
| Mining 2018 | 1.9920 | 1.6959 | 0.2284 | 0.2160 | 217→203 |
| EE draft 2023 | 0.5560 | 0.5202 | 0.7028 | 0.6898 | 221→211 |
| EE final 2025 | 0.4660 | 0.4713 | 0.8018 | 0.7944 | 221→214 |
| B-BBEE 2026 | 0.5386 | 0.5044 | 0.0120 | 0.0106 | 221→211 |

The 2018 SE falls about **14.9%** relative to the supplied deletion sensitivity. Point estimates and constituents are unchanged between these two deletion versions; the difference is donor treatment. The comparison is a sensitivity to deletion, not a claim that the deleted economic shocks were all errors.

**Required correction.** Give the sensitivity an explicit donor-validity mask separate from the baseline volume policy. Propagate extreme exclusions into the null residual panel, retaining complete fixed portfolios and calendar-gap checks. Add a test that an observation excluded under the extreme-deletion specification cannot appear in its donor matrix. Rename the current check as fit/event-only deletion if retaining its present behaviour intentionally; it cannot support a broader outlier-robustness claim.

Evidence: [extremes_retained_in_deletion_null.csv](../diagnostics/independent_review/extremes_retained_in_deletion_null.csv), [targeted_sensitivities.csv](../diagnostics/independent_review/targeted_sensitivities.csv).

### Major M3 — The 2018 analysis needs a public-information chronology, not just an official date and a Cabinet-meeting alternative

The 27 September baseline is a defensible **gazette-publication-date** estimand. It is not established as the first public information event. The configured alternative, **19 September**, is a Cabinet meeting date; a meeting is not proof of public disclosure that day. The [26 September ministerial advisory](https://www.gov.za/news/media-advisories/media-briefings/minister-gwede-mantashe-briefs-media-gazetting-mining-charter) reports that earlier approval and schedules the 27 September briefing.

There is also direct evidence of earlier public information that the current sensitivity list omits: the President's [21 September 2018 stimulus-and-recovery statement](https://www.thepresidency.gov.za/statement-president-cyril-ramaphosa-economic-stimulus-and-recovery-plan) explicitly announces Cabinet approval of the revised Charter and discusses withdrawal of the MPRDA Amendment Bill within a broad economic package. Therefore the chronology cannot be reduced to 19 September approval versus 27 September gazetting. This source establishes public information **by 21 September**, not a verified first-disclosure hour.

Re-estimated [0,+1] diagnostic comparisons are:

| Anchor | Spread, pp | Raw p | Interpretation |
| --- | ---: | ---: | --- |
| 19 September | +1.0577 | 0.5128 | Configured Cabinet-date sensitivity; public availability unverified |
| 20 September | +2.7832 | 0.1166 | Review diagnostic; not a verified first release |
| 21 September | +4.7583 | 0.0282 | Public stimulus/approval announcement; multiple simultaneous policies |
| 26 September | −3.6255 | 0.0488 | Advisory/previous-session window; includes 27 September |
| 27 September | −2.1859 | 0.1894 | Registered gazette-publication baseline |

These p-values are exploratory and unadjusted for the searched timing alternatives. The 21 September window ends on **25 September**, because the intervening weekend and Heritage Day do not increment event time.

The sign change is not merely a consequence of changing constituents or re-estimated models. Freezing the original 2018 OLS coefficients and using the same **16 mining and 128 controls** complete across every reviewed window gives **+1.1211 pp on 19 September, +4.6215 pp on 21 September and −2.2437 pp on 27 September**. This fixed-sample exercise reports point estimates only; it does not reuse an incorrectly aligned inference design.

**Required correction.** Build a dated, sourced chronology of approval, public announcement, text availability and gazetting. Separate the incremental gazette response from earlier approval/stimulus information. Preserve the designated baseline while explaining what it measures; do not select a replacement date because its coefficient or p-value is favourable. The current evidence does not support a stable negative reaction to the overall 2018 policy-information sequence.

Evidence: `config/analysis.yml::robustness$earlier_2018_date`, `R/07_robustness.R::run_robustness()`, [fixed_sample_2018_timing.csv](../diagnostics/independent_review/fixed_sample_2018_timing.csv), [targeted_sensitivities.csv](../diagnostics/independent_review/targeted_sensitivities.csv).

### Major M4 — The 2026 positive CAAR is exposed to benchmark composition and concurrent macroeconomic news

Independent calculations on the **same 160 primary-window constituents** give:

| Date | J203 daily return | Equal-security raw stock return | Market-model AAR |
| --- | ---: | ---: | ---: |
| 29 January 2026 | +0.1438% | +0.2828% | +0.2031% |
| 30 January 2026 | −4.1544% | −1.2804% | +1.3745% |

Approximately **87.1%** of the +1.5776% CAAR comes on 30 January. The sum of the two daily equal-security raw portfolio returns is approximately **−0.9976%**, despite the positive abnormal return. This is not an arithmetic contradiction: the portfolio falls less than its fitted normal-return prediction during the market decline. That relative performance does not establish an increase in shareholder wealth attributable to the draft codes.

There are concrete overlapping events. The SARB lists its [January 2026 MPC statement as published on 29 January](https://resbank.co.za/en/home/publications/statements/mpc-statements); the [statement](https://www.reservebank.co.za/en/home/publications/publication-detail-pages/statements/monetary-policy-statements/2026/january) reports a hold at 6.75% and a divided vote. The White House [announced Kevin Warsh as its Fed-chair nominee on 30 January](https://www.whitehouse.gov/releases/2026/01/wide-acclaim-for-president-trumps-nomination-of-kevin-warsh-as-fed-chair/). Contemporary [White House pool reporting](https://www.presidency.ucsb.edu/documents/pool-reports-january-30-2026) records the nomination as already announced by 09:13 US Eastern time, before the end of the South African trading day. The [World Gold Council's January review](https://www.gold.org/goldhub/research/gold-market-commentary-january-2026) independently identifies large intraday gold swings on the month's final two days.

These sources establish overlapping information and market conditions. They do **not** prove which item caused the observed returns. Nevertheless, the combination is a serious identification problem for attributing an equal-weight-minus-market-model result to the B-BBEE bundle. A contemporaneous J203 regressor removes only the historically fitted linear exposure; it does not guarantee removal of heterogeneous domestic, commodity, currency or interest-rate shocks. Conversely, it can absorb a genuinely broad policy effect because affected firms are inside the benchmark.

**Required correction.** Add a sourced news/market-condition audit and report day-0/day-1 decomposition. Obtain independently verified disclosure timing and, if feasible, sector/commodity/global-market controls selected for economic reasons. Keep raw portfolio and benchmark movements visible. Until then, describe the finding as unusual conditional relative performance around the dates, not evidence that the proposals raised firm value or lowered efficiency costs.

Evidence: [event_daily_returns.csv](../diagnostics/independent_review/event_daily_returns.csv), `R/03_market_models.R`, `R/04_abnormal_returns.R`, [robustness_summary.csv](../tables/robustness_summary.csv). The market-adjusted alternative is +3.0130%, substantially different in magnitude from the fitted market-model result; it is a different normal-return restriction, not independent causal corroboration.

### Major M5 — Event-induced volatility remains an unaddressed inferential risk

The bootstrap preserves synchronous innovations and short-run dependence **within its pre-event donor process**. It does not estimate a changed event-day residual variance or correlation structure. Resampling more often from the same historical process cannot supply that protection. The documentation correctly acknowledges this; the issue is a limit on the scientific interpretation of the intervals, not an undisclosed claim that the code implements a volatility-robust named test. Event-induced variance and cross-sectional dependence are established, separate concerns in the original [Boehmer, Musumeci and Poulsen paper](https://ink.library.smu.edu.sg/lkcsb_research/4666/) and [Kolari and Pynnönen paper](https://doi.org/10.1093/rfs/hhq072).

I ran **500 zero-mean-effect trials per scenario**, with 999 bootstrap draws per trial, using a separately specified scalar-portfolio regression DGP, the actual 221-session fit and the 29-session gap. This checks temporal calibration; the multivariate algebra is checked separately.

| Controlled null DGP | Block length | Rejection rate, absolute-tail p<0.05 | Basic-interval coverage |
| --- | ---: | ---: | ---: |
| IID Gaussian | 5 | 6.4% | 92.6% |
| Stationary AR(0.6) | 5 | 4.8% | 95.2% |
| Stationary AR(0.6) | 10 | 4.8% | 94.8% |
| Standardised Student t, 5 df | 5 | 5.6% | 94.0% |
| Centred lognormal innovations | 5 | 5.2% | 95.6% |
| Gaussian; event-day residual SD doubled, mean effect still zero | 5 | **34.2%** | **65.0%** |

The stationary absolute-tail rejection rates have Monte Carlo intervals containing 5%; these experiments do not establish exact 95% interval coverage or general validity for the actual financial data. For the doubled-SD scenario, the Wilson interval for the rejection rate is approximately **30.2–38.5%**. This demonstrates failure of a stronger zero-mean-effect interpretation when the historical-volatility assumption fails; it is **not** an estimate of the actual event variance or actual empirical false-positive rate.

A separate transparent stress test multiplies the entire 2026 prediction-error distribution by 1.5. Its raw p becomes **0.0536**, and its pointwise interval crosses zero. That multiplier also scales estimation error, so it is a scenario calculation, not an event-only variance estimator or an approved replacement p-value.

**Required correction.** Decide with the supervisor whether inference is explicitly conditional on a stable residual process, or whether a specified event-volatility-robust procedure is required. After repairing return measurement, examine variance regimes, leverage, tail behaviour and block-length choice. Evaluate a suitable alternative using a realistic synchronous DGP and explain its assumptions; an ordinary independent-firm t-test is not a substitute. Avoid describing the existing intervals as covering arbitrary announcement-induced risk changes.

Evidence: [synthetic_null_summary.csv](../diagnostics/independent_review/synthetic_null_summary.csv), [synthetic_null_trials.csv](../diagnostics/independent_review/synthetic_null_trials.csv), [prediction_error_scale_sensitivity.csv](../diagnostics/independent_review/prediction_error_scale_sensitivity.csv), `review/independent_methodology/stress_bootstrap.R`.

### Moderate S1 — The reported p-values and intervals use different two-sided orderings

`R/05_inference.R::infer_event()` reports the basic equal-tailed interval

`[estimate − q97.5%(D*), estimate − q2.5%(D*)]`

but tests using the absolute-tail probability

`(1 + count(|D*| ≥ |estimate|)) / (B + 1)`.

Both constructions have a coherent meaning under the stated bootstrap approximation. They are **not generally inversions of the same test when D* is asymmetric**. Simulation-mean centring does not make a distribution symmetric. This is not evidence that either formula was accidentally transcribed incorrectly.

There is an actual same-level disagreement in the submitted 2018 `previous_session` sensitivity: estimate **−3.6255 pp**, absolute-tail **p=0.0488**, but basic 95% interval **[−7.0000,+0.8320] pp** includes zero. The corresponding doubled-smaller-tail diagnostic is **0.0692**. All 55 baseline rows happen to agree on the raw 5% decision; that does not remove the underlying distinction.

The difference also matters for the 2026 headline: absolute-tail p is **0.0134**, whereas the doubled-smaller-tail calculation on exactly the same draws is **0.0052**. Applying the same five-event Holm procedure to all five equal-tail diagnostics gives **0.026 for 2026**, compared with the designated absolute-tail value 0.067. This is a demonstration of test-definition sensitivity, **not permission to substitute the significant version after observing the result**.

**Required correction.** State one primary rejection rule before interpreting further results. Either pair the absolute-tail test with an interval obtained by inverting that rule, or pair the current basic interval with a matching equal-tail rule, accounting for finite Monte Carlo conventions. If retaining both, label them as different constructions and explain possible disagreement. Assess calibration and scientific justification before changing the designation.

A separate issue must not be confused with this: a pointwise 95% interval excluding zero while a **Holm-adjusted** p exceeds 0.05 is expected, because the interval is not a simultaneous five-event interval. The baseline 2026 positive interval versus Holm p=0.067 is therefore **not**, by itself, an inconsistency.

Evidence: [null_distribution_diagnostics.csv](../diagnostics/independent_review/null_distribution_diagnostics.csv), [previous_session_tail_comparison.csv](../diagnostics/independent_review/previous_session_tail_comparison.csv), [asymmetric_null_example.csv](../diagnostics/independent_review/asymmetric_null_example.csv).

### Moderate S2 — The historical industry proxy is not verified legal exposure, and economic issuers are not the observation unit

The source-specific classifications are applied as coded, with no accidental cross-event join. The limitation is their substantive content.

- The primary mining samples are exactly **15/120** and **16/130**. The list includes Hulamin under `Aluminium`; the strict proxy removes it. KIO is in controls under `Iron & Steel`. Moving KIO alone to mining changes the 2018 spread from **−2.1859 to −1.4496 pp**; moving the broader configured mineral-value-chain labels gives −1.4124 pp. Neither reassignment proves legal applicability, but the material change rules out a claim that classification is immaterial.
- The 2017 primary all-security sample includes **33 unknowns**, and the 2018 sample includes **30**. These differ from the pre-fit eligible unknown counts of 34 and 31. The 2017 unknowns include ANG, BHP, NPH and VAL, whose current labels suggest identity/history questions relevant to mining. Current names alone cannot establish their historical exposure.
- There is concrete external support for investigating VAL: the [JSE name-change notice](https://clientportal.jse.co.za/Content/JSENoticesandCircularsItems/JSE%20Clear%20Market%20Notice%2016225%20EDM%20-%20Treatment%20of%20Anglo%20American%20Platinum%20Ltd%20%28AMS%29%20-%20Corporate%20Action%20-%20Name%20Change%20-%2028%20May%202025%20%28Ex-Date%29.pdf) records AMS→VAL in May 2025 with the same ISIN. The supplied VAL series has usable 2017 prices but is unknown in the historical classification join. A hypothetical VAL-to-mining reassignment changes the 2017 spread to **−3.5602 pp**, p=0.1612. This is a review candidate, not verification of the vendor's complete historical splice or regulatory treatment.
- `issuer_id` and `security_type` are missing in **all 833 complete primary security-event records**. No repeated current ISIN or exact company-label group cannot certify absence of multiple securities per issuer: share classes normally have different ISINs and names. FFA and FFB both enter the 2017, 2018 and 2023 all-security portfolios; the [2017 JSE Fortress notice](https://clientportal.jse.co.za/Content/JSENoticesandCircularsItems/JSE%20Market%20Notice%2049117%20EDM%20-%20Treatment%20of%20Fortress%20Inc%20Fund%20Ltd%20A%20%28FFA%29%20and%20Fortress%20Inc%20Fund%20Ltd%20B%20%28FFB%29%20Corporate%20Action.pdf) identifies the A/B securities and their distinct identifiers. Equal-security weighting is valid as a stated estimand, but is not equal-issuer weighting.
- Investment vehicles, REITs and BEE schemes need a clearly stated population rule. MTNZF's historical investment-vehicle label is not excluded by the supplied likely-non-company flag. Its issuer announcement describes an unwind and prospective cash-shell status. This does not make its ordinary equity mathematically invalid, but it is different from an operating-company exposure. Excluding the flagged investment-label candidates leaves the 2026 estimate **+1.5120%**, raw p=0.0112; it does not remove the positive relative-return pattern.

**Required correction.** Produce a manually reviewed event-dated security/issuer/exposure ledger, preserving unresolved cases. Validate direct South African mining-right exposure, geography and relevant security class rather than equating every mining label with identical treatment. Report sensitivity to verified issuer weighting and candidate classifications. Keep broad-policy results as aggregate security portfolios until actual EE/B-BBEE exposure measures exist. Do not automatically assign unknowns by contemporary names or merge similar names.

Evidence: [primary_constituents.csv](../diagnostics/independent_review/primary_constituents.csv), [unclassified_primary.csv](../diagnostics/independent_review/unclassified_primary.csv), [fortress_share_classes.csv](../diagnostics/independent_review/fortress_share_classes.csv), [targeted_sensitivities.csv](../diagnostics/independent_review/targeted_sensitivities.csv), `R/02_select_samples.R::classify_event()`.

### Moderate S3 — Placebos are useful descriptive checks, not a strong calibration or randomisation design

The code reselects samples and refits models using each pseudo-event's past. Selection is seeded before examining outcomes. I verified calendar spacing of at least 22 sessions and distances exceeding 30 sessions from every registered event. There is no evidence of outcome-based date selection in the implementation.

| Event | Attempts | Valid | Raw p<0.05 | Future pseudo-dates | Fits containing that event's real announcement |
| --- | ---: | ---: | ---: | ---: | ---: |
| Mining 2017 | 10 | 10 | 1 | 6 | 5 |
| Mining 2018 | 10 | 10 | 0 | 0 | 0 |
| EE draft 2023 | 10 | 10 | 2 | 0 | 0 |
| EE final 2025 | 10 | 9 | 0 | 0 | 0 |
| B-BBEE 2026 | 10 | 10 | 0 | 0 | 0 |

The 2017 forward extension is outcome-independent, but five pseudo-event estimation windows contain the actual 2017 announcement. Frozen classifications can also be retrospective. The registered-policy buffer does not screen other policy announcements, macroeconomic news or firm-specific events. Overlapping estimation histories and some shared dates mean the pooled 49 results are not 49 independent Bernoulli calibration trials.

There are **3/49 raw rejections**, approximately 6.1%, but this count cannot certify nominal 5% size. Ten pseudo-events per event have little resolution, and economically meaningful non-policy news is not evidence of a software false positive.

The unavailable 2025 placebo is handled correctly: the 29 December 2023 [0,+1] window includes missing J203 session 2 January 2024. It is explicitly N=0 with unavailable inference. Removing or filling the gap merely to obtain 50 valid results would be inappropriate.

**Required correction.** Keep these as exploratory diagnostics. If formal calibration is wanted, define the eligible-date and information-availability rules in advance, increase coverage, record policy/news overlaps and separate contaminated fitting windows. Do not describe this design as exact random assignment or use the absence of placebo rejections as causal validation.

Evidence: `R/07_robustness.R::run_robustness()`, [placebo_selection_audit.csv](../diagnostics/independent_review/placebo_selection_audit.csv), [placebo_results.csv](../tables/placebo_results.csv).

### Moderate S4 — Liquidity and observability screens define a selected estimand; they do not certify representativeness

Independent reconstruction matches all **9,345 event-by-master eligibility decisions**. The relevant fit sample is the configured −250:−30 period, not a full-history or current-listing screen. The sequential exclusion ledger also reconciles. For 2017, exclusions are 1,394 without historical positive closes, 220 with insufficient fitting observations, 81 with excessive unchanged returns and 5 likely non-company securities, leaving 169 eligible. Corresponding 2018 counts are 1,404, 204, 75 and 9, leaving 177.

Requiring 180 usable fitting dates and at most 20% zero returns selects comparatively liquid securities. The requirement that every event-window return have positive volume then conditions inclusion on post-announcement trading/observability. Suspension, delisting or an event-driven failure to trade can remove precisely the securities of interest. This is a selection limitation, not an inadvertent future observation in the pre-event OLS fit.

Volume asymmetry in the null deserves a proportionate assessment. The share of zero-volume rows among headline pre-event constituents is only about **0.11–0.39%** in these samples, and the supplied no-volume sensitivity changes estimates little. Nevertheless, insisting that every constituent trade on the same day would reduce donor dates, e.g. 2026 from 221 raw-complete dates to **131 all-positive-volume dates**. These are different conditional samples. A no-volume specification simultaneously changes fitting and event usability; it is not a clean test of donor-volatility comparability.

**Required correction.** State the population as securities meeting these observability/liquidity conditions. Report exclusions and plausible unavailable-event outcomes, reconcile the historical universe where possible, and avoid generalising to all JSE firms or the economy. The current data cannot establish a survivorship-free historical universe.

Evidence: [sample_screening.csv](../diagnostics/independent_review/sample_screening.csv), [null_process_diagnostics.csv](../diagnostics/independent_review/null_process_diagnostics.csv), [sample_exclusions.csv](../diagnostics/sample_exclusions.csv), `docs/sample_selection.md`.

### Minor N1 — The fixed five-test family is implemented correctly by default but is not independently locked in configuration

The default family is exactly the two mining spreads plus the three aggregate [0,+1] tests. Independent Holm calculations reproduce **0.648, 0.648, 1, 1, 0.067**. The ordinary `--event` path retains the default five-event configuration and therefore reserves five tests correctly.

However, `R/08_generate_outputs.R::generate_outputs()` takes the family size from `length(cfg$analysis$events)`. A custom config containing only the 2026 event would use `n=1`, despite output text stating that five hypotheses are reserved. The corresponding adjusted value would be 0.0134 rather than 0.067. This is a configuration-contract risk, not an error in the submitted default run.

**Recommended correction.** Encode an explicit primary testing-family registry independently of execution selection, or clearly label a deliberately redefined family. Add a narrow-config test. Continue labelling all other windows, subgroups, timings and 60 sensitivity rows exploratory; primary-family Holm does not protect discoveries selected from those alternatives.

## 4. Independent verification: what passed, and its limits

### Arithmetic, samples, joins and market models

The separate [Python verifier](../../../archive/part_a/independent_methodology/verify_data.py) uses NumPy least squares and direct source-price ratios, not the project's OLS/CAR functions.

| Verification | Observed result |
| --- | --- |
| Source-adjacent stock returns | 980,380 valid returns; zero disagreement |
| Compact source/derived row reconciliation | 982,129 rows; one-to-one keys |
| Event-specific eligibility | All 9,345 decisions and fitting counts reproduced |
| Event-specific classification join | All 9,345 group assignments reconciled to that event's source record |
| Independently refitted OLS models | 844; maximum coefficient/residual-SD difference 7.8×10⁻¹⁵ |
| Firm CAR records | 4,179 completeness/value records checked; complete-CAR maximum difference 1.0×10⁻¹⁵ |
| All 55 inference point estimates | Maximum difference 5.0×10⁻¹⁶ |
| Balanced cumulative portfolio series | Maximum cumulative difference 5.3×10⁻¹⁶ |
| Source verifier in isolated full run | Passed; 26 payload files and eight source Parquet datasets |
| Current test suite in isolated copy | 18 cases; 331 passed expectations; no failures, errors or skips |
| Full `--all` reproduction | Successful; all nine submitted statistical CSV tables byte-identical |

Removing blank source placeholders during the independent calculation did not bridge gaps: the independent verifier explicitly checks consecutive supplied-calendar session IDs. The full isolated R run also recalculated the original full-panel returns. J203's missing 2 January 2024 observation leaves both 2 and 3 January returns unavailable; no multi-session ratio is relabelled as a daily return.

The baseline market model uses an intercept and benchmark return, fitted on usable sessions −250:−30, with 221 possible dates and at least 180 observations. No event-window observations enter fitting. CAR is the **sum** of AR, not compounded wealth; CAAR equals mean complete-window CAR under the corresponding fixed equal-security weights. This is internally correct for the stated additive estimand. Non-mining controls and mining portfolios separately sum to weights −1 and +1 for the spread. Unknowns remain in all-security outcomes but outside spreads.

An independent one-security-at-a-time omission check finds:

| Event | Range of primary point estimates after one omission |
| --- | --- |
| Mining 2017 | −4.2573 to −2.8561 pp |
| Mining 2018 | −2.7306 to −1.6304 pp |
| EE draft 2023 | −0.2584 to −0.1227% |
| EE final 2025 | −0.2149 to −0.0667% |
| B-BBEE 2026 | +1.5120 to +1.6589% |

These are point-estimate influence checks, not jackknife standard errors or simultaneous confidence statements. No single omission reverses the baseline sign; this does not remove common-news or measurement problems.

### Bootstrap algebra and assumptions

For constituent i, let `X_i` be its actual usable estimation-date design and `q = (L, sum of event market returns)'`. The implemented prediction error can be written as

`D* = Σ_i w_i [Σ_event e*_it − q' (X_i'X_i)^−1 X_i' e*_{i,fit}]`.

The first term is the pseudo-event innovation; the second propagates alpha/beta estimation error. In code, the stored influence column is `w_i X_i (X_i'X_i)^−1 q`, which yields the displayed scalar after multiplication by the synchronous residual vectors. The signs and dimensions are correct. Firm-specific fitting masks are preserved; a common date index is used across securities. For market-adjusted returns the regression-error term is correctly omitted.

I independently sampled admissible starts and performed **199 explicit three-security regression refits**, with different usable fitting dates, common AR(0.5) innovations, signed portfolio weights and a 29-session gap. Maximum discrepancy from the production algebra was **3.47×10⁻¹⁷**. The existing exact-common-shock cancellation and corrected singleton/gap tests also passed. This verifies the algebra and dependence synchronisation, not the appropriateness of the donor process.

Residual columns are centred on common complete dates and scaled by `sqrt(n_i/(n_i−2))`. That is a degrees-of-freedom adjustment under the regression framework; it is not a general correction for serial heteroskedasticity, leverage-dependent residual variance or selection into common dates. Source blocks cannot cross missing sessions. Dependencies beyond the chosen block length and dependence across concatenated block boundaries are not preserved. Baseline headline donor counts are 221, 217, 221, 221 and 221. **4,999 draws are not 4,999 independent historical observations.**

The implementation uses overlapping, non-circular blocks, fixed market regressors and observed constituent sets. Mean-centring the simulated statistic removes its Monte Carlo mean but does not repair skewness, distribution changes or source errors. These are conditions to assess, not bugs merely because the bootstrap is custom. Standard event-study background and estimation-error concerns are discussed in [MacKinlay's original survey](https://www.bu.edu/econ/files/2011/01/MacKinlay-1996-Event-Studies-in-Economics-and-Finance.pdf); this audit's algebraic checks are independent of a claim to implement a named published test.

### Tables and figures

The CSV tables, percentage conversion and plotted numerical series reconcile. Visual inspection of the current 2026 CAAR and robustness figures found no contradictory labels or obvious rendering defect. The CAAR plot uses 155 securities balanced over −10:+10, whereas its primary table uses 160 over [0,+1]. Its cumulative level begins at −10. The fact that its level at +1 differs from the headline [0,+1] result is therefore expected. Pointwise bands are labelled as such; neither the plot bands nor the five primary pointwise intervals are simultaneous family bands.

Evidence files: [independent_numeric_checks.json](../diagnostics/independent_review/independent_numeric_checks.json), [full_rerun_table_comparison.json](../diagnostics/independent_review/full_rerun_table_comparison.json), [explicit_multivariate_refit.csv](../diagnostics/independent_review/explicit_multivariate_refit.csv), [figure_reconciliation.csv](../diagnostics/independent_review/figure_reconciliation.csv), [test_summary.md](../diagnostics/independent_review/test_summary.md).

## 5. Which findings are robust, fragile or unsupported?

| Finding | Assessment supported by this audit |
| --- | --- |
| 2017 negative mining-minus-control point estimate | **Fairly stable as a descriptive sign** across the supplied timing/specification variations and individual omissions. Size and uncertainty remain conditional on exposure and return measurement. The relaxed zero-return screen gives raw p=0.0480 on a different sample; this is exploratory, not a replacement headline. |
| 2018 negative policy response | **Fragile as a statement about the policy-information sequence.** The negative gazette-window spread reproduces, but earlier public-information windows are positive, including on a fixed sample. KIO/exposure choices affect magnitude, and Reinet contaminates the original donor process. |
| 2023 and 2025 broad-policy effects absent | **Unsupported.** The designated tests do not reject, but this is not equivalence testing and does not establish economically negligible effects. Wide conditional intervals, common benchmark exposure and unmeasured treatment intensity prevent that conclusion. The 2025 sign also changes under relaxed zero-return or timing choices. |
| 2026 positive market-model abnormal return | **Reproducible conditional relative performance, but fragile as a significance or policy-attribution claim.** Positive under most same-date modelling screens and omissions; heavily concentrated on day +1, sensitive to timing, tail ordering, block length and volatility assumptions. |
| No designated baseline headline survives current Holm adjustment | **Numerically correct for the declared absolute-tail baseline family.** It is not a statement that every reasonable specification would produce no rejection. |
| Realised efficiency costs, productivity, profitability, compliance burdens or equity gains | **Not identified by Part A.** The measured outcomes are short-run security-price residuals. |

The 2026 block-length example is particularly relevant. With all five events evaluated under the same alternative, raw p=0.0078 for block length 10 yields a diagnostic five-event Holm value of **0.039**, versus 0.067 under the declared five-session baseline. Market-adjusted and next-session alternatives also change significance. These are exploratory alternatives with their own multiplicity; they must not be used to select the result to present. They show that the binary discovery statement is less robust than the positive same-date point estimate.

For 2023 there is a concrete additional confound beyond generic market news: a [ministerial parliamentary reply](https://www.parliament.gov.za/storage/app/media/Docs/exe_rq_na/6df0fbe6-ba5b-471a-be11-cccb387ed193.pdf) records the US ambassador's 11 May arms-related allegations and the government's 12 May response. This overlaps the EE draft window. No causal market effect of that episode is estimated here; its existence strengthens the need for a contemporaneous-news chronology.

Official date evidence is consistent with the registered publication dates: the [2017 release speech](https://www.gov.za/speeches/minister-mosebenzi-zwane-occasion-release-mining-charter-15-jun-2017-0000), [2018 ministerial release](https://www.gov.za/news/media-statements/minister-gwede-mantashe-release-mining-charter-2018-27-sep-2018), [2023 government notice listing](https://www.gov.za/xh/documents/notices?order=field_gcisdoc_document_date&page=235&sort=desc), [2025 gazette](https://www.gov.za/sites/default/files/gcis_document/202504/52514gon6124.pdf) and [2026 draft-code notice](https://www.gov.za/sites/default/files/gcis_document/202601/54032gon3743_0.pdf) support those dates. They do not certify the first public upload or disclosure hour. The 2026 source is one notice in a bundle, not an established common treatment intensity for every listed security.

For 2017, [0,+1] is **15 and 19 June**, not two consecutive calendar days: Youth Day and the weekend intervene. Session alignment is correct, but the second return includes that intervening news interval. Earlier consultation/approval and the distinction between anticipation and a full-text surprise need a documented chronology. Merely observing pre-event abnormal movements does not establish their cause.

## 6. Corrections and research decisions in priority order

1. **Resolve economic return measurement before final inference.** Source and reconcile Reinet and other conversions, distributions, rights and influential events in both fitting and event periods. Define the approved equity/benchmark return convention and create a versioned derived adjustment ledger. Recompute all samples, models, outcomes, bootstrap donors, sensitivities and placebos; leave source data unchanged.
2. **Repair or accurately relabel the extreme-deletion sensitivity.** Ensure its donor mask follows its intended exclusion rule. Test the distinction between a baseline zero-volume policy and a sensitivity excluding flagged returns. Retain the complete-portfolio and missing-session safeguards.
3. **Settle the estimand and information chronology.** In particular, distinguish 2018 approval/stimulus information from gazetting, and investigate 2026 macro/commodity overlap and disclosure timing. Keep dated alternatives separate and predesignated. A day-0-only or differently timed window is a different question, not an automatic improvement.
4. **Specify the inference rule and its scope.** Choose compatible p-value/interval conventions on methodological grounds, freeze the five-test family independently of execution selection, justify block length, and quantify Monte Carlo error where relevant. Do not change these choices to cross a significance threshold.
5. **Assess volatility and model stability after return corrections.** Use more informative synchronous simulations than the original 60 Gaussian smoke trials. Retain the clear warning if uncertainty remains conditional on a stationary pre-event residual process. A volatility-robust alternative needs its own justification and calibration.
6. **Review the actual constituents and exposure map.** Prioritise KIO, Hulamin, unresolved historical mining identifiers, cash-shell/investment vehicles, share classes and issuer links. Establish dated evidence of source publication availability where obtainable. Report issuer-aware sensitivity only when the mapping is verified.
7. **Improve the research narrative and archive.** Present current results as descriptive valuation movements, show day-level contributions and raw/benchmark returns, distinguish failure to reject from absence of an effect, and state that broader efficiency/equity outcomes are outside this design. Archive a complete new run with code/config/data-version hashes and review dispositions once decisions are implemented.

The existing cautionary narrative already avoids most explicit causal overclaims. It should now incorporate the **specific** demonstrated corporate actions and overlapping announcements, rather than relying solely on general limitations paragraphs.

## 7. What remains unconfirmed, and what can be fixed locally

| Issue | Classification | What this audit establishes or cannot establish |
| --- | --- | --- |
| Extreme-deletion donor mismatch | Fixable implementation error | Demonstrated directly; quantified without changing headline files. |
| Reinet security-unit conversion | Fixable derived-return/identity error | Documented ratio and date; one-return diagnostic quantified. A full approved adjustment history remains outstanding. |
| Other corporate actions/dividends and J203 variant | External data verification plus return-definition decision | Arithmetic and internal alignment pass; provider economic conventions are not certified. |
| Inference/interval ordering and configurable family | Fixable methodological/reporting contract | Both current formulas reproduced; their different decisions and family-size edge are demonstrated. |
| Event-induced volatility/stationarity | Research assumption and inference-design limitation | Stress-test vulnerability demonstrated; actual event variance is not identified from two event days. |
| First disclosure, announcement novelty and simultaneous news | Historical research and identification limitation | Several primary dates/overlaps verified; exact first disclosures and isolated causal effects remain unconfirmed. |
| Legal exposure, security classes and issuer maps | Historical data limitation | Current classification logic reproduces; legal treatment and all historical issuer links do not. |
| Complete historical exchange universe/calendar | External reconciliation | Supplied-session arithmetic passes; no complete independent JSE universe/calendar certification was performed. |
| Survivorship and event observability | Selection/design limitation | Screens are transparent; rejected/unobserved counterfactual outcomes are unavailable. |
| Controlled EE/B-BBEE exposure regressions | Missing research data | Historical workforce gaps, compliance, financial controls and credible unaffected groups remain absent. |
| Fresh dependency restore | Environment limitation | Installed environment and isolated runs work; a clean network restore was not tested. |

No test result resolves these inherently historical or counterfactual questions. A scientifically defensible thesis can report a limited descriptive analysis with these boundaries; it cannot turn the present estimates into causal efficiency costs through stronger wording.

## 8. Reproduction and preservation record

Read [the diagnostic README](../../../archive/part_a/independent_methodology/README.md) for the five standalone audit commands and script purposes. The independent numerical audit uses Python/PyArrow/Pandas/NumPy; production financial calculations remain in the existing R project. The controlled simulations use 999 draws for practicality, while real-data baseline and targeted inference use the configured **4,999** draws.

The full pipeline and test suite were executed from a copy of the project in the temporary workspace recorded in [audit_workspace.txt](../diagnostics/independent_review/audit_workspace.txt), with an absolute `PART_A_PYTHON` path. Only the immutable source package was symlinked into that copy. Tests and pipeline reporting therefore did not overwrite the submitted diagnostics or research handover.

Relevant records:

- [Full isolated pipeline log](../diagnostics/independent_review/full_pipeline_log.txt) and [test log](../diagnostics/independent_review/test_log.txt).
- [Nine-table byte comparison](../diagnostics/independent_review/full_rerun_table_comparison.json).
- [Protected-file pre-review fingerprints](../diagnostics/independent_review/protected_files_before.json) and [post-review preservation check](../diagnostics/independent_review/protected_file_check.json).
- [Independent OLS coefficients](../diagnostics/independent_review/independent_models.csv), [CARs](../diagnostics/independent_review/independent_cars.csv), [all 55 outcome reconciliations](../diagnostics/independent_review/headline_and_window_reconciliation.csv), and [independent Holm calculation](../diagnostics/independent_review/independent_holm.csv).

This report and its separate diagnostics are review artifacts. No diagnostic return correction, date reassignment, exposure relabelling, alternative test or volatility multiplier has silently replaced a production result. No commit, push or external communication was performed during this audit.
