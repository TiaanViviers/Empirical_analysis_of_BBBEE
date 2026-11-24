# Validation — work in progress

Machine-readable checks are in `data/part_b/processed/cee_validation_results.csv` and Parquet. All extracted demographic count rows reconcile with their source totals, and there are no duplicate raw analytical keys. Sector totals match national totals for count-based years 2017 and 2020–2025. In 2019 sector sums are 31 top managers and 256 senior managers below national counts. This is unresolved; do not force agreement or assume all sector classifications partition national coverage. The 2018 percentage-only sectors and 2016 percentage-only records cannot be checked for count reconciliation.

For 2024, 37 of 380 component percentages differ from their count-derived values by more than 0.051 percentage points; the largest difference is approximately 0.4904 percentage points. Published values remain unchanged. Later and earlier count-adapter results pass the same numerical check, but this is not a substitute for visual source verification. The 2024 coverage transcription was visually compared with PDF page 30 and its sector totals reconcile with the national totals. PDF pages 68, 81, 82 and 83 of the 25th report have been rendered and inspected; the other sector appendix pages and other reports' extracted tables remain to be checked visually. The original PoC separately checked 2024 Table 7. Summary-table cross-checks, complete source-table visual checks, and per-year missingness review remain outstanding.

## Subsequent update

2018 sector counts have been recovered using the PDF digit encoding; the two construction totals were transcribed from rendered page 89. All 24 2018 count rows reconcile, sector totals equal national totals, and the largest count-versus-published percentage difference is below 0.05 percentage points. The construction page was inspected; other 2018 pages still require visual checks. Four sector labels previously included the table header word FOREIGN and have been corrected. See `cee_issue_register.md` and `cee_visual_verification_log.csv` for unresolved work. Sector reporting coverage has been extracted for all years; 2023 sector employee counts exceed national coverage by 300, and some labels are incomplete. Coverage labels and the discrepancy need source review.

## Independent review update

The 2016 retrospective national counts on rendered PDF page 106 of the 19th report were transcribed and reconcile; the 2023 coverage sector mismatch was confirmed on the rendered source table. Ten wrapped labels were reconstructed from PDF text. This does not complete source checking of other observations; see `cee_independent_review.md` and the visual log.

## Final review update

The independent review has now covered all ten reporting years using an independent PDF text extractor and rendered-page sampling, including management values and headings, coverage observations and EAP benchmarks. The 2020 wrapped coverage labels are corrected in the generating script. Source discrepancies remain as documented in `cee_issue_register.md`; exact year-by-year verification methods, counts and reproducibility checks are in `cee_independent_review.md`. Earlier statements that the collection has not been independently checked are superseded by this update.
