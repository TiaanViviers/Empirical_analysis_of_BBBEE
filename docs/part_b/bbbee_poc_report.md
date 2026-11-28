# Pilot extraction and validation

Run from repository root: `python3 analysis/part_b/scripts/bbbee/pilot.py`. Requires Python 3 and Poppler `pdftotext`. CSV uses standard library; Parquet was not produced because pandas/pyarrow are not installed. Original PDFs are untouched. Decimal commas are preserved in ownership original strings and normalised to percentage points; status figures retain printed percentage and count separately.

- `data/part_b/pilot/bbbee/retrospective_ownership.csv`: 88 rows (tables 16 and 81, 11 years × 4 measures × 2 sectors).
- `retrospective_compliance.csv`: 110 rows (tables 4–5, 11 years × 9 levels plus total); total rows have no published percentage.
- `retrospective_sector_coverage.csv`: 154 rows (table 2, 13 sector/unknown categories plus total × 11 years); dashes retained and treated as unspecified, not assumed zero.
- `status_2022_ownership.csv`: 138 rows (Figures 7 and 10: 60 each; Figure 8: 18). Four Generic 2017–18 entries have original zero and null analytic values, marked not analysed.

Poppler text with layout was used for retrospective tables; the embedded chart data tables are image content and were manually transcribed into the reproducible script from rendered physical pages 19–21. Rendered retrospective PDF pages 48, 55, 66, 125 were examined to check headings, year alignment, original values and structure; the page 55 table was visually checked across the published rows. Figure 7, 8 and 10 rendered numerical tables were read visually. This is not an independent second-person cell-by-cell audit; further independent proofreading is required before publication. The PDF year headers in table 4 were confirmed left-to-right 2013–2023 from the rendering.

Script checks unique ownership keys, complete row counts, status sums versus totals, percentage counts and female-versus-overall ownership. The 2018 status cells sum to 2,473 versus published 2,605; Level 5 says 14 (14/2,605 = 0.5374%) but table 5 says 6%. All other years’ status counts sum to their totals and all other percentages match to within 0.51 percentage point (whole-percentage rounding). Preserve both printed values; do not fill the gap. Four table 81 female averages exceed the overall averages: 2015 both, 2016 voting, 2020 economic interest. None of the national retrospective rows or 2022 sector female rows exceed their paired overall values. Figure 8 values match all six supplied national ownership anchors, and male plus female equals total in each year. Fig 5 differs in historical values; source inconsistency is unresolved.

The pilot demonstrates feasible direct extraction, subject to manual proofreading, source limitations and the unresolved inconsistencies. Source table values are not empirical conclusions.
