# Event-specific sample selection

The source universe consists of 1,869 instruments, not 1,869 firms with usable history. Approximately 79.5% of source rows are blank placeholders. None are converted to zero prices or zero returns. No 2026 listing status or full-period coverage statistic determines eligibility.

For each event, construct the following sequential exclusion ledger over the entire master:

1. No finite positive price during [−250,−30]: no historical usable price evidence.
2. Fewer than the configured 180 valid positive-volume J203-paired estimation returns: insufficient estimation observations. Prior closes must lie on the immediately previous supplied-calendar session.
3. More than 20% exactly unchanged valid adjacent raw returns in the estimation period, or an undefined fraction: low-information/illiquidity screen. The denominator is all valid analytical returns, not only positive-volume returns. Raw unchanged-price/source flags are preserved separately. Genuine zero price changes are mathematically valid and remain available for sensitivity analyses.
4. Historical `likely_non_company_security` flag true: known likely investment/preference/other product. These are provisional security screens, not legal security-class verification. Unknown flags do not trigger exclusion. Unmatched source-name-based reclassification is not invented.
5. Degenerate/singular market-model fit: excluded from AR calculation and separately reported in model diagnostics. The sample file's eligible flag describes pre-fit screening, not a guarantee of model success.
6. Every return in a particular CAR window must have positive volume (baseline), finite adjacent stock return and finite market return. Incomplete CARs are NA, never partial sums. Each window may therefore have a different final N.

The sample file contains every master security for every executed event, source industry/identity evidence, estimation counts, screening status and individual window-completeness flags. Source counts, sequential reasons, group counts and balanced-plot sample sizes are reported separately. The plotting sample is complete for [−10,+10]; ordinary CAR tables use their own window sample. Post-announcement completeness imposes selection and can exclude suspended/delisted firms or event-induced non-trading; results are conditional on observability.

Industry data is filtered by event_id before instrument joins; unknowns stay unknown. Confident historical non-mining members supply controls, and historical mining candidates supply exposed portfolios. Reporting month precedes publication date, but bulletin publication availability has not been established. A strict availability-verified exposure subset is empty. Non-mining firms can be indirectly exposed, and broad-policy aggregate samples have no verified unaffected group.

For bootstrap null residual vectors, use only dates with finite analytical residuals and donor_valid=TRUE for EVERY fixed event-window constituent. Do not fill missing residuals or renormalise changing groups. Contiguous moving blocks cannot span missing sessions. At least 60 synchronous complete dates are required; otherwise inference is explicitly unavailable. The baseline null includes zero-volume dates with valid analytical returns, while OLS/event returns use their volume restrictions. Full extreme exclusion also excludes donor residuals; event-only and donor-only volume sensitivities keep these policies separate. This asymmetry and potential volatility understatement require review, alongside the no-volume sensitivity.

Observed positive price starts/ends are not listing/delisting dates. Historical identifiers, ordinary/preference classifications, permanent issuers and effective ISINs are incomplete. Multiple securities are not merged by similar names or contemporary ISIN. Equal-security portfolios can overweight an issuer, and controls are heterogeneous. Historical extraction selection may retain survivorship bias. Full source universe reconstruction and verified issuer concentration are outstanding, rather than silently assumed resolved.

## Revised configuration and scope

`positive_volume` controls fitting liquidity; `event_positive_volume` controls event/anticipation usability; `null_positive_volume` controls donors independently. The source-industry baseline, reviewed-industry alternative and partial verified-issuer weighting are explicit choices; see historical_exposure.md. No current-name filling of unknown histories occurs.

Pseudo-event fitting windows now exclude their own real announcement. With fixed horizons and spacing, the 2017 seed supplies six rather than ten dates; shortfalls are disclosed. Other events retain ten attempts, including the legitimate unavailable EE-final window. Frozen source classifications remain potentially retrospective and there is no randomised treatment assignment.
