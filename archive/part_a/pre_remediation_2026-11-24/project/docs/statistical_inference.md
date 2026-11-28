# Date-synchronous portfolio inference

## Rationale and scope

Securities share the same announcement sessions. Cross-security residual correlation invalidates an interpretation based only on independent-firm CAR standard errors. Kolari and Pynnönen document severe over-rejection even for modest correlation under event clustering ([2010 paper](https://doi.org/10.1093/rfs/hhq072)). We do not claim to implement their named test. Our primary method is a conditional residual moving-block bootstrap over common market dates. Overlapping-block mechanics follow the standard construction illustrated by [Wicklin/SAS](https://blogs.sas.com/content/iml/2021/01/13/moving-block-bootstrap-sas.html); the multivariate residual and regression-error propagation below is the project implementation.

Mining headlines test an equal-security mining-minus-control CAR. Broad-policy headlines test aggregate market-model CAAR without asserting a legal treatment group. Each test uses its own fixed complete event-window constituent set. Bootstrap uncertainty measures time-series sampling variability conditional on constituents, historical exposure proxy and observed market regressors. It does not estimate policy-assignment uncertainty.

## Residual panel and null statistic

Let w_i be +1/N for a group, or +1/N_M in mining and −1/N_C in controls. Let X_i comprise [1,R_mt] for that security's actual usable OLS estimation dates, within [−250,−30]. Let q = [L, sum_event R_mt]' for an L-session CAR window. Original residuals e_it are calculated using fitted firm coefficients on all valid raw pre-event closes.

Retain only pre-event dates with finite e_it for ALL fixed constituents. Remove each column's mean on this common-date subset and multiply each firm's residual column by sqrt(n_i/(n_i−2)), compensating for OLS residual degrees of freedom (an approximation under serial dependence). Require at least 60 complete dates. Missing-date patterns are not imputed. Moving blocks of length 5 can start only where all five dates are consecutive in the full supplied calendar. Sample positions in the admissible-start vector with replacement using sample.int, including when only one start exists; a single start value must not be interpreted as an integer range. Use identical date indices for all firms; concatenate and truncate to T+G+L, where T=221 and G=a−estimation_end−1 is the number of intervening trading sessions. Block lengths 1/10 are sensitivities. Seeds and replication counts are recorded; the full run uses B=4,999.

For each bootstrap draw, assign the first T residual vectors to the original estimation-session positions. For each firm, refit its simulated residuals on that firm's actual X_i fit positions. This is computed algebraically via the linear OLS influence matrix and is numerically tested against explicit refitting. Discard the next G vectors without using them for either estimation or the event sum, and use positions T+G+1 through T+G+L as pseudo-event residuals. For [0,+1] following estimation end −30, G=29 and the draw has 252 sessions: fit columns 1:221, discarded columns 222:250 and event columns 251:252. Anticipation/plot windows beginning at −10 instead have G=19. The gap is preserved for market-adjusted inference as well. This prevents a five-session block from artificially connecting the end of estimation to an event 30 sessions later. The simulated CAR prediction error is

D* = sum_event sum_i w_i e_it* − sum_i w_i q' (X_i'X_i)^−1 X_i' e_i,fit*.

The second term propagates estimated alpha/beta error, with the original missing/volume fit-date masks. Entire residual vectors are sampled synchronously in both terms, preserving cross-sectional dependence. Contiguous source blocks cannot cross source missing sessions; concatenation boundaries are ordinary bootstrap block boundaries. The market-adjusted alternative has no estimated coefficients and omits the second term.

Centre the simulated D* distribution by its simulation mean, mitigating finite-sample overlapping-block endpoint imbalance. SE is its sample standard deviation. The basic pointwise 95% interval is [estimate−q_.975(D*), estimate−q_.025(D*)]. The two-sided p-value is (1 + count(|D*| >= |estimate|))/(B+1); its minimum at B=4,999 is 0.0002. This is a bootstrap tail probability, not an exact randomisation test. Complete null-date counts are reported for every estimate. Failed calculations produce a reason and NA inference rather than a placeholder p-value.

Balanced CAAR charts repeat the same procedure for each cumulative horizon beginning at −10. Bands are pointwise, not simultaneous. Their samples differ from per-window CAR samples; matching endpoint values should only be expected for matching constituents and cumulative bounds. Figures report sample sizes and starting convention.

## Multiple comparisons

Headline window is [0,+1]. The family consists of mining-minus-control for 2017/2018 and aggregate CAAR for the other three dates. Raw p-values and Holm-adjusted p-values are both reported. Subset runs reserve all five hypotheses (R p.adjust n=5), avoiding a smaller family merely because only one event was executed. Additional groups, windows and sensitivities are exploratory. No significance claim should be chosen after searching those alternatives.

## Assumptions and limits

The common-date residual panel is assumed approximately stationary and representative of event-window innovations conditional on market returns. It can exclude atypical pre-event dates when one constituent lacks prices. Bootstrapping cannot repair corporate actions, misclassified exposure, unobserved news, selection into observable event windows or uncertain event timing.

Null residuals retain valid zero-volume closes, while baseline OLS/event usability requires positive volume. This is deliberately transparent and avoids changing constituent weights or impossible all-constituent active-day intersections, but inactive-day residuals may understate active-day volatility. No-volume robustness evaluates that design. Common-date complete-case sampling, degrees-of-freedom scaling under dependence, fixed fit-date masks and homogeneity of residual distribution over time are substantive approximations. Event-induced volatility or changing residual/market relationships are not guaranteed covered. Short pre-event histories and few independent blocks limit calibration. The method is not a general causal confidence interval.

## Executed checks

Tests verify that perfectly common innovations cancel in a matched spread, date blocks respect gaps and seeds (including a lone admissible start at an index greater than one), and algebraic OLS prediction-error draws match explicit refits to 1e−12 tolerance. The explicit-refit checks include five-session blocks, 29- and 19-session gaps, alternative CAR lengths and a changed estimation-window endpoint. A deterministic 60-simulation Gaussian common-shock null experiment records its rejection rate; this is a limited smoke calibration, not proof of nominal size under heteroskedastic dependent financial data. Synthetic injected shocks test effect recovery; real-data OLS and CAR calculations are compared with independent lm/predict. Consult the executed test summary and null_calibration.csv; unexecuted tests are never labelled passed.
