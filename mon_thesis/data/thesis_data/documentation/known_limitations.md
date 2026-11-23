# Known limitations and unresolved research decisions

These limits remain after successful source preservation and technical validation. They do not justify undocumented repairs or automatic sample exclusions.

1. Price units and source corporate-action adjustments have not been independently verified; no unit conversion or return adjustment was applied.
2. The exact IRESS J203 price-versus-total-return variant remains unverified.
3. A mnemonic is not a verified permanent security or issuer identifier; distinct share classes and source IDs remain separate.
4. Actual listing/delisting/suspension histories, issuer mappings, historical ISIN validity and historical sectors are unavailable. The 2026-11-23 snapshot supplies raw ISIN fields and current labels only; 380 ISIN fields are nonstandard or placeholders.
5. A complete observed date calendar contains placeholders and does not establish historical listing status.
6. Unchanged closes, zero volume, extreme changes and stale-price flags do not by themselves identify valid economic returns or errors.
7. The source universe has not been reconciled against an authoritative dated identifier list; survivorship-bias freedom is not established.
8. All policy event dates are provisional. No final event-specific eligibility, abnormal returns, CAR/CAAR, regressions or policy effects were estimated.
9. Full-period instrument coverage is descriptive and must not determine earlier historical eligibility or characteristics.
10. The calendar is the observed company-date union, corroborated by daily J203 except documented gaps; no independent official exchange-calendar reconciliation has been completed.

Documented benchmark missing sessions: 2024-01-02. The supplied thesis benchmark lacks 2024-01-02, while all five current planned estimation/event windows are fully covered. Obtain and verify missing source observations separately; do not interpolate or bridge a gap.

The 2026-11-23 Screener snapshot matches all 1,869 historical master IDs and has three additional IDs; this is a dated source comparison, not proof of historical universe completeness. PBT name differences still require identifier-level treatment, not name-based merging. Interhold/Interleisure identical overlaps were reduced deterministically with all copies in lineage. Preference-share-looking labels and the provider EQU suffix are insufficient verification of security class.

Prioritise provider quote/adjustment definitions and corporate actions, dated identifier/issuer/security-class histories, actual listing and suspension histories, historical sectors, dated financial statements/market values and B-BBEE/EE exposure. Keep effective and publication/availability dates separately. Verify policy announcement dates and times before choosing session zero. Final liquidity/completeness criteria and event-specific samples belong to the later research layer.
## Historical classification limitations

Partial historical JSE Bulletin labels are available for five reporting months; they are not asserted equivalent to ICB. Publication dates/pre-announcement availability remain unverified; a strict availability-verified sample is empty. The September 2018 and April 2025 cross-check files are missing. Identity matching uses conservative ticker/name concordance and enumerated display variants; substantive renames and ticker reuse require review. Coverage denominators are provisional event-specific instrument samples under existing price-quality diagnostics; no final issuer sample or policy applicability has been established. Classifications may change by event and must not overwrite a single timeless sector field. No absence establishes delisting. See historical_industry_classifications.md and the manual-review queue.
