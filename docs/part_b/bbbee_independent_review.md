# Independent B-BBEE data review

**Readiness: the retrospective series is suitable for qualified descriptive research**, subject to the filters and limitations below. This is a review of transcription and internal structure, not an audit of the underlying certificate data or evidence of representativeness or causality. No demonstrated numerical extraction errors were found, so no published observation was changed. The supplementary 2022 series is excluded from primary analysis until its local source is authenticated; that limitation does not block the retrospective series.

## Independent verification and coverage

A new checker uses MuPDF structured-text characters and positions, a different PDF engine from the original Poppler extraction. It independently locates each table, its year headers or year rows, level labels and printed cells, then compares the output to the published strings in the final datasets. Each table is recorded separately in `bbbee_independent_cells.csv` and in the verification log. The 28 retrospective source pages were also rendered and inspected for table titles, year and column ordering, sector and measure labels, and layout, including the Property blank. The numerical comparisons are automated; the rendered-page inspection was of layout and issue cells, not a claim that every numerical cell was visually proofread. Table 60 has 43 printed values and one genuinely blank cell. The separate engine and original parser still depend on the same local PDF and cannot verify the publisher's underlying data.

| Source tables | Independent coverage |
|---|---|
| Ownership 16, 23, 28, 35, 42, 60, 67, 74, 81, 88 | 44 numerical cells each, except Table 60: 43, plus its blank checked in the rendered page |
| Ownership 50 | 28 numerical cells; 2017–2023 |
| Sample 1, 2 | 55 and 154 annual category cells respectively, including printed dashes and annual totals |
| National compliance 4, 5 | 110 count cells and 99 percentage cells |
| Sector pairs 20–21, 26–27, 32–33, 39–40, 57–58, 64–65, 71–72, 78–79, 85–86 | Each pair: 110 count and 99 percentage cells, including dashes and count totals |
| Sector pair 47–48 | 70 count and 63 percentage cells; 2017–2023 |
| 2022 Figures 7, 8, 10 | 60, 18, 60 chart-table values respectively, independently transcribed from rendered pages and compared with final records |

Total retrospective comparison: **2,899 printed cells** (467 ownership values, 1,170 compliance count cells, 1,053 compliance percentage cells and 209 sample cells), plus the Property blank. Grand Total percentage cells are not published in the compliance percentage tables. Sample table all-years totals are outside the annual dataset; annual category cells and annual totals were compared. The 138 supplementary values include four printed zeros treated as analytical missing values. Figure transcriptions are recorded in `analysis/part_b/scripts/bbbee/independent_figures_check.py`. Source page references, sector-to-table assignments and four distinct ownership definitions were checked; financial and other code categories are not an industry crosswalk.

## Source issues

**SOURCE LIMITATION — National 2018.** Tables 4–5 print Level 5 as 14 and 6%, and total 2,605; counts sum to 2,473. Figure 1 reports 2,041 compliant and 564 non-compliant, totalling 2,605; no defensible replacement Level 5 count follows. Preserve the values and exclude the entire distribution from derived comparisons.

**SOURCE LIMITATION — Financial Services 2016.** Table 78 prints total 10, while numerical counts sum to 9; Table 79 percentages are approximately counts divided by 9, and sample Table 2 also prints 9. These do not establish a correction to the published status total. Preserve the source values and exclude this entire distribution from derived comparisons. Both distributions' calculated level percentages and Levels 1–4 summary values are suppressed.

**SOURCE LIMITATION — ownership anomalies.** All ten flagged female-overall pairs were checked in their source tables. Values below are overall/female percentage points; V is voting rights and E is economic interest. The source does not establish indicator-specific valid samples, denominator treatment or weights. Different samples are possible, not proven; retain the numbers and flags and report sensitivity to excluding affected pairs.

| Table | Sector and year | Measure | Overall / female |
|---|---|---|---|
| 42 | Generic 2016 | E | 19.85 / 21.62 |
| 67 | Tourism 2020 | E | 6.55 / 23.56 |
| 67 | Tourism 2021 | E | 11.25 / 14.38 |
| 74 | Agri-BEE 2019 | E | 4.87 / 5.78 |
| 74 | Agri-BEE 2020 | E | 9.39 / 14.66 |
| 81 | Financial Services 2015 | V | 5.44 / 26.07 |
| 81 | Financial Services 2015 | E | 5.26 / 29.00 |
| 81 | Financial Services 2016 | V | 3.15 / 3.44 |
| 81 | Financial Services 2020 | E | 13.32 / 22.89 |
| 88 | Construction 2017 | E | 11.36 / 16.13 |

**RESOLVED — Generic 2017–2018 supplementary zeros.** Figures 7 and 10 each print two zeros while their narratives state those years were not analysed. All four original strings remain in `published_value_original`; `ownership_pct` is missing and flagged.

**NON-BLOCKING LIMITATION — authentication.** The retrospective acquisition was recorded as certificate verified. The 2022 local file was acquired without successful certificate verification; a subsequent certificate-verified attempt failed at DNS resolution and a web-reader attempt timed out. Its matching local hash establishes identity, not authenticity. Exclude `status_2022` from primary analysis pending authentication. Its portal population, ownership definitions, historical figure disagreement and unknown weighting also prevent splicing it with the retrospective series even if authenticated.

**NON-BLOCKING LIMITATION — selection and comparability.** These are certificate/report entries from a changing, voluntary and selective sample, not the economy's ownership wealth, a census or a balanced firm panel. The source describes cleaning and exclusions but does not disclose indicator-specific denominators or weighting. Contextual Table 1/2 counts are not ownership denominators. Applicable generic and sector Codes and their thresholds changed over time; the 2015 amended generic Codes and sector-specific timing matter, and 2013 is especially selected and affected by earlier rules. Small or changing sector samples make movements fragile. The 2013–2023 extension is suitable only as explicitly qualified historical context; it is less comparable than 2016–2023. The source's selection and regime changes preclude causal inference or economy-wide estimates.

## Exact analytical selection

Use `read.csv(..., na.strings = c("", "NA"))`; retain the original values and flags in the source data. The following base R examples specify primary selections, with no averaging across sectors, years or indicators:

```r
own <- read.csv("data/part_b/processed/bbbee_ownership.csv", na.strings = c("", "NA"))
levels <- read.csv("data/part_b/processed/bbbee_compliance_levels.csv", na.strings = c("", "NA"))
summary <- read.csv("data/part_b/processed/bbbee_compliance_summary.csv", na.strings = c("", "NA"))

primary_ownership <- subset(own, series_id == "retro_2026" &
  reporting_year >= 2016 & reporting_year <= 2023 & !is.na(ownership_pct) &
  ownership_measure %in% c("black_voting_rights", "black_female_voting_rights",
                           "black_economic_interest", "black_female_economic_interest"))
# National: sector_original == "National"; sectors: sector_original != "National".
# Select one ownership_measure at a time. For the historical extension, use 2013–2023.

primary_levels <- subset(levels, series_id == "retro_2026" &
  reporting_year >= 2016 & reporting_year <= 2023 & entity_size == "All" &
  compliance_level != "Grand Total" &
  !(sector_original == "National" & reporting_year == 2018) &
  !(sector_original == "Financial Services" & reporting_year == 2016))
primary_summary <- subset(summary, series_id == "retro_2026" &
  reporting_year >= 2016 & reporting_year <= 2023 & entity_size == "All" &
  !is.na(analytical_value))
```

For full 2013–2023 compliance descriptions change the year bounds, retaining both distribution exclusions and regime caveats. In `primary_levels`, use nonmissing `calculated_pct` for count-derived shares and retain `published_pct` as a separately labelled published series; do not include Grand Total in category sums. Printed dashes remain missing counts, even when the published percentage is zero. A Levels 1–4 summary may infer a dash as zero only under the documented reconciliation and published-zero conditions; inspect `inferred_zero_for_dash` and `small_status_denominator_lt30`. For anomalies, identify flagged female rows and their matched overall rows by series, year, sector and measure, then report results both retaining and excluding each affected pair; never simply remove all female data. For sector ownership, inspect `small_context_sample_lt30` and sample coverage, noting 30 is a screening convention, not an indicator denominator or adequacy threshold. Missing and ambiguous observations must be checked explicitly: `sum(x, na.rm = TRUE)` on all-missing or partially missing counts can yield a misleading zero or partial total. Do not fill dashes or missing ownership values with zero.

## Reproduction and final checks

`sh analysis/part_b/scripts/bbbee/reproduce_bbbee.sh` completed successfully and regenerated 606 ownership, 1,170 compliance level, 117 summary, 209 coverage, 22 reference and 170 validation rows. The subsequent separate MuPDF, figure-transcription and structure checks passed. They verify unique analytical keys, value bounds, integer nonnegative counts, published value preservation, the two reconciliation failures, nonmissing calculated shares and summary formulas, suppression, source references, source separation and the ten anomaly flags. The pipeline's existing Poppler coordinate comparison also passed, but is not counted as the independent comparison. Original PDFs were not modified. Optional independent check scripts require `mutool`; ordinary reproduction remains Python 3 plus Poppler and does not require MuPDF.
