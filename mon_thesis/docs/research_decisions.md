# Research decision register — methodological correction pass

These are documented decisions made after the independent review, not a claim
of prospective preregistration. Choices were made for measurement, consistency
and interpretability, not to obtain a significant estimate. The earlier code,
results and evidence remain in `outputs/baselines/pre_remediation_2026-11-24/`.

## D1 — Use unit-consistent price returns; apply only verified conversions

**Decision.** Preserve raw quotes and raw ratios. Apply the ledger-approved
Reinet ten-to-one conversion on its effective date. Do not selectively add cash
to some firms and label the panel total return.

**Rationale/evidence.** The FTSE/JSE conversion notice establishes changed quote
units. A mathematically correct raw ratio is not an economic return across that
conversion. See [return measurement](return_measurement.md) and the executed
ledger. MTNZF and Aveng actions are documented but their provider-consistent
adjustment remains unresolved.

**Alternatives/impact.** Legacy raw-price and unresolved-action-security
exclusions are reported. Baseline point estimates change only through affected
fitting/event records; the Reinet model changes substantially. Full total return
would require a complete distribution/rights history and compatible benchmark.

**Supervisor/provider input.** Required for final return convention and complete
economic-return history. The deterministic security-unit error itself is fixed.

## D2 — Retain absolute-tail testing; invert the same rule for intervals

**Decision.** Keep the existing two-sided absolute-tail plus-one p-value and
strict rejection rule `p < alpha`. Use the corresponding finite-draw symmetric
interval. Preserve legacy basic intervals and equal-tail probabilities only as
auxiliary comparisons.

**Rationale.** The previous test/interval pair could disagree under skewness.
Changing the p-value ordering after observing results could create a favourable
2026 discovery. Inverting the retained rule fixes consistency while preserving
the original ordering. [Statistical inference](statistical_inference.md)
specifies the exact order statistic and assumptions.

**Alternatives/impact.** Equal-tailed testing with basic intervals is a different
defensible convention under its approximation; the independent review shows its
different 2026 conclusion. It is not silently promoted. Interval shapes change;
primary p-values change only if inputs/donor policy change.

**Supervisor input.** Review the inferential approximation and final designated
ordering. Software coherence is resolved; scientific assumptions are not.

## D3 — Keep the five headline hypotheses fixed

**Decision.** `config/headline_hypotheses.csv` registers the two mining spreads
and three aggregate [0,+1] tests. Execution lists and CLI overrides do not shrink
this family. Exploratory windows/specifications are separate.

**Rationale/alternatives.** The default Holm procedure was correct but a narrow
custom config could reduce its size. Explicit registration prevents accidental
redefinition. A genuinely different research family would require a separately
documented design change, not a shorter execution list.

**Supervisor input.** Confirm the economic headline estimands; no routine
permission is required to fix execution-dependent adjustment.

## D4 — Retain publication dates; distinguish earlier information events

**Decision.** Keep 27 September 2018 as the incremental gazette-date baseline.
The 19 September meeting reference, public 21 September stimulus/approval and
26 September advisory are distinct exploratory windows. Also report a common
sample with baseline coefficients frozen, using point estimates only.

**Rationale/evidence.** The source-linked [information chronology](../research/event_information_chronology.csv)
separates public information from a meeting date and formal publication. The
21 September statement bundles other economic measures. No date is selected by
coefficient or p-value. The 2017 window spans 15 and 19 June; first disclosure
hours and prior uploads for the other events remain unresolved.

**Alternatives/impact.** Earlier windows change sign, including with a fixed
sample. A different primary date would change the question, not simply improve
the same estimator.

**Supervisor input.** Required to settle announcement novelty and the thesis's
event-specific interpretation. First public availability needs historical work.

## D5 — Keep conditional synchronous inference; do not promise volatility robustness

**Decision.** Retain synchronous residual moving blocks for primary raw-CAR
inference. Add event-only innovation scaling, early/late donor windows, active
donor dates and synchronous multi-security calibration. Do not replace it with
independent-security t-tests.

**Rationale/evidence.** Common and sector shocks make cross-sectional
independence untenable. A restricted BMP/KP-style aggregate diagnostic is
implemented and formula-tested, but concerns standardized CAR and assumptions
different from raw CAAR or a signed mining/control contrast. Calibration shows
that its proportional-volatility advantage does not cover skewness or changing
factor correlation. See `diagnostics/remediation/synchronous_calibration_summary.csv`.

**Alternatives/impact.** A volatility multiplier is a scenario, not a variance
estimate from two event days. Donor choice and block length change 2026
significance. No more favourable alternative is designated primary.

**Supervisor input.** Required on acceptable conditional assumptions and final
uncertainty claims. A generally event-volatility-robust causal procedure is not
identified by the available data and is not declared solved.

## D6 — Keep source exposure as baseline; supply evidenced industry alternatives

**Decision.** Primary groups remain the original industry proxy. Use a reviewed
industry sensitivity for KIO and Hulamin, with explicit unresolved cases for
historical IDs and legal exposure. Current names never fill unknowns.

**Rationale/alternatives.** Verified operating industry does not establish
uniform incremental legal treatment or unaffected controls. [Historical
exposure](historical_exposure.md) lists evidence and retrospective-availability
limits. Strict-mining and broad mineral-value-chain checks answer different
proxy definitions.

**Supervisor input.** Required for any final legal exposure design and verified
historical mapping. Baseline differences remain descriptive industry spreads.

## D7 — Equal security weights remain primary

**Decision.** Apply partial issuer weighting only to verified Fortress A/B links
as a sensitivity. Leave every unverified security separate.

**Rationale/impact.** Different classes generally have different names/ISINs;
absence of repeated labels does not certify independent issuers. Full issuer
weighting or market-cap weighting is unsupported by current histories. The
partial sensitivity is not represented as a verified universe of companies.

**Supervisor input.** Confirm the target unit. Further issuer-history evidence
is needed before claiming equal-issuer results.

## D8 — Exclude the real event from placebo fitting windows

**Decision.** Preserve seeded, outcome-independent selection, existing horizons,
spacing and registered-event buffers, but reject a pseudo-date whose fit period
contains its own real announcement. Report feasible-count shortfalls.

**Rationale/impact.** Filling a ten-date quota with contaminated histories would
weaken calibration. The fixed 2017 horizon supplies six selected dates under the
current seed; other events retain ten. The missing-J203 EE-final pseudo-event is
still explicitly unavailable, not replaced with fabricated market data.

**Alternatives.** Extending further in time could fill a quota but adds regime
and retrospective-exposure concerns. Frozen classifications and unscreened other
news prevent exact randomisation or strong counterfactual interpretation.

**Supervisor input.** Review whether more historical research is worthwhile;
these remain exploratory diagnostics, not proof of nominal size or causality.

## D9 — Keep liquidity/observability conditions explicit and configurable

**Decision.** Baseline: 180 positive-volume fitting returns, at most 20% unchanged
analytical returns, and complete positive-volume event windows. Separate
`event_positive_volume`, `null_positive_volume` and the full extreme donor mask.

**Rationale/impact.** Event completeness selects observable securities and can
exclude suspensions/nontrading. Event-only and donor-only volume sensitivities
isolate that choice from fit-period selection. Neither solves survivorship.

**Supervisor input.** Required for target-population claims and interpretation
of unavailable event outcomes. No all-firm or economy-wide inference is made.

## D10 — Use existing benchmark alternatives; do not invent controls

**Decision.** Report raw, analytical, predicted and abnormal daily returns with
industry/security contributions and sourced news. Retain the existing
market-adjusted comparison. Do not add speculative factors or collect a new
large return dataset during this pass.

**Rationale/impact.** J203 contains potentially affected firms and has different
weights from the equal-security portfolio. The 2026 result is concentrated on
the market-stress following day and does not isolate B-BBEE. Dated global,
commodity or sector factors could be justified in future, but require compatible
data and a stated economic model.

**Supervisor input.** Needed if stronger identification is sought. The current
outputs are organised for a later accessible R Markdown report; that report is
outside this correction pass.
