# Part A event-study methodology

## Design and estimands

The research describes JSE security-price movements around five verified transformation-policy publication dates. The register, not provisional README labels, supplies official dates. Primary analysis concerns the 2017 Mining Charter; the same machinery supports 2018 and aggregate EE/B-BBEE results. Market valuation is distinct from realised firm efficiency and equity outcomes. All results are conditional associations.

Official dates map to the identical session of the supplied observed company calendar. Unscheduled non-session dates fail explicitly, requiring a documented mapping rather than silent rolling. Weekends and observed holidays do not increment event time. t=0 is the publication-date session; daily close-to-close return at t needs the close at t−1. First disclosure time remains unverified. Previous/next-session alternatives are sensitivity analyses; 19 September 2018 is a distinct potential information event. That date is not claimed to establish first public disclosure merely because Cabinet met then.

## Return and normal-return equations

For finite positive adjacent closes, R_it = P_it/P_i,t−1 − 1; otherwise missing. R_mt is the analogous J203 return, never filled or bridged over 2 January 2024. Simple returns are fractions internally. Source Close adjustment and J203 return variant are unverified, so these are raw-price-based rather than verified total shareholder returns. Volume does not enter arithmetic, but determines analytical usability under the baseline screen.

For each event and eligible security fit R_it = alpha_i + beta_i R_mt + epsilon_it by OLS on configured sessions [−250,−30] (221 possible return dates). Minimum fitting sample is 180 valid positive-volume benchmark-paired returns. Constant/near-degenerate market or stock variation and singular fits are rejected. Coefficients, fitting N, residual standard deviation (n−2 divisor) and R² are saved. Implausibly large coefficients are diagnostic flags rather than automatic exclusions.

AR_it = R_it − alpha_hat_i − beta_hat_i R_mt. Market-adjusted AR_it = R_it − R_mt is an alternative. CAR_i[a,b] is the sum of AR_it only when every session is usable. AAR_t is the equal-security mean AR on a fixed complete-window sample; CAAR[a,b] is its sum and equals mean CAR. No compounding is intended: CAR is an additive abnormal-return measure.

## Samples and aggregation

Screens use only each event's estimation period, historical source flags and the relevant window's completeness. The baseline maximum unchanged-return fraction is 20%, computed on valid raw adjacent returns before the volume filter. It is a liquidity diagnostic, not a declaration that all zero returns are invalid. Known likely non-company instruments are excluded; unknown classification is retained in the all-security portfolio. See sample_selection.md for exact ordering and denominators.

[0,+1] is the headline window; [−1,+3] and [0,+5] are short-horizon alternatives, [−10,−1] anticipatory, [−10,+10] for visualisation. Each CAR window has its own complete sample. Plot samples are separately balanced across all 21 sessions. Their CAAR starts at −10 (not reset to zero on announcement day); pre-event movements therefore enter the displayed level. Tables report N per window and group.

Mining and non-mining groups come from the event-specific historical bulletin snapshot, joined only after filtering event_id. High label concordance supports provisional industry membership, not verified legal Mining Charter treatment. Unknowns are omitted from spread portfolios. Equal security weights sum to +1 in mining and −1 in controls. There is no market-cap weighting without historical capitalisation data. Multiple economic issuer classes may receive extra total weight because no verified historical issuer map exists; no name-similarity merger is made.

## Inference and validation

Primary inference uses centred, date-synchronous pre-event residual vectors and moving blocks. Each constituent's actual fit-date design propagates OLS parameter estimation error. No independent-firm t-test is used as primary evidence. See statistical_inference.md for the exact null statistic, finite-sample scaling, missing-date policy, intervals and assumptions. The headline five-event family receives Holm adjustment, including when a subset is run. Other windows, groups and sensitivities remain exploratory.

Automated tests cover returns, calendar windows, join multiplicity, synthetic shocks, OLS against independent lm, CAR/CAAR identities, synchronous cancellation, bootstrap error against explicit refitting, null simulations and real-input 2017 integration. Full source fingerprints must remain identical. Test execution status, code/config/event hashes, environment and source contracts accompany outputs.

## Sensitivity and interpretation

Re-estimate under 200 minimum observations, relaxed volume/unchanged screens, alternative normal returns, flagged extreme exclusion, timing shifts, a narrower mining proxy, balanced plot sampling and block lengths 1/10. Preserving extreme baseline moves avoids declaring actual news responses erroneous; severe exclusion is a diagnostic requiring corporate-action review. Real pseudo-events use seeded dates, spacing and registered-event buffers, their own pre-event samples and models. Classification snapshots are frozen and can be retrospective at pseudo-dates; known-news screening is incomplete.

No controlled firm-characteristic or EE-exposure model is supported without dated controls/target gaps. Benchmark contamination, anticipation, corporate actions, common news and incomplete identity histories limit causal interpretation. Technical pipeline completion is not thesis-final research validation.

The broader mineral-value-chain check additionally treats the historical `Iron & Steel`/`Iron & Steel Prod` labels as a broad exposure group. It is deliberately distinct from direct mining applicability. A labelled control (KIO) makes the need for this check concrete. Diagnostics list these instruments, influential firm CARs, the largest null portfolio shocks, repeated source labels and repeated valid contemporary ISINs as review queues; none is automatically merged or repaired.
