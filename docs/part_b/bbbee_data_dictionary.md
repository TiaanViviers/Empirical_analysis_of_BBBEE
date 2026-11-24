# B-BBEE data dictionary

All datasets are UTF-8 CSV, with a header, empty fields for missing/not applicable, percentages in percentage points on 0–100, and semicolon-separated flags. Keys below identify rows; do not drop `series_id` when joining. `retro_2026` is the retrospective certificate/report sample; `status_2022` is the distinct voluntary portal series. `source_page_pdf` counts physical pages from 1; printed pages are supplied separately. Source identifiers and file hashes are in `bbbee_source_inventory.csv`.

For primary analysis exclude the unauthenticated `status_2022` series. Read blank fields as `NA`, select nonmissing analytical values explicitly, and do not use `sum(..., na.rm=TRUE)` as evidence that a distribution is complete. See `bbbee_independent_review.md` for exact filters and distribution exclusions.

## Ownership (`bbbee_ownership.csv`)

Key: `series_id`, `reporting_year`, `sector_original`, `ownership_measure` (all entity sizes combined). `ownership_pct` is analytical; `published_value_original` preserves the source string, including its decimal comma and percent sign. `black_voting_rights`, `black_female_voting_rights`, `black_economic_interest`, `black_female_economic_interest` are four separate reported retrospective averages. The three `reported_black_*ownership` fields retain 2022 portal figures' labels; they are not equated with either retrospective measure. `indicator_sample_n`, `numerator` and `denominator` are blank when not provided; `contextual_sample_n` is the table 1 or 2 sample count, not an indicator denominator. `aggregation_method` describes only the established source method. `quality_flag` includes `blank_in_source`, `not_analysed_printed_zero`, `female_average_exceeds_overall_unresolved`, and `small_context_sample_lt30`. Four printed Generic zeros are analytically missing.

## Compliance (`bbbee_compliance_levels.csv`)

Key: `series_id`, year, sector, entity size and `compliance_level` (Levels 1–8, Non-Compliant, Grand Total). `published_count_original` preserves dashes; `entity_count` and `numerator` are missing for dashes. `valid_status_denominator` is the published status total, including where that total is inconsistent; it must not be mistaken for verified reconciliation. `published_pct_original` and `published_pct` retain table 5 or sector percentage table, whereas `calculated_pct` uses count / published total × 100 only when the distribution reconciles. Published total rows are retained; their calculated percentage is 100 where reliable. Count and percentage sources and physical pages are separately recorded. `source_page_printed` refers to the count table; for a percentage table on the next page, subtract 2 from `source_pct_page_pdf`.

## Derived summary (`bbbee_compliance_summary.csv`)

Key: series, year, sector, size, indicator definition. `analytical_value` is the Levels 1–4 count divided by published status total, × 100. Numerator and denominator are recorded. It is missing when the distribution fails reconciliation or the necessary dash cells cannot be interpreted conservatively. Where numeric counts sum to the total and a Levels 1–4 dash has a published 0% share, zero is inferred only for this calculation and flagged `inferred_zero_for_dash`; the original level remains missing. Small denominators are flagged below 30. This threshold is a screening convention, not a statistical adequacy test.

## Coverage (`bbbee_reporting_coverage.csv`)

Key: series, year, coverage measure, sector and entity size. Table 1 records enterprise sizes (including `Unknown` and `Grand Total`); Table 2 records original sectors (including `Unknown` and `Grand Total`). `sample_count` and `numerator` repeat published counts; dashes remain missing. `denominator`, `eligible_population_count`, and `reporting_rate_pct` are blank because an eligible universe is not established. Counts are context for the sample, not unique firms, a balanced panel, or valid ownership-specific n. Grand totals are published totals, not categories to sum alongside components.

## Reference and checks

`bbbee_sector_reference.csv` preserves table 2 and supplementary chart sector labels and notes; it does not define a CEE bridge or assert undocumented dates. `bbbee_validation_results.csv` contains checks and issues, including one row per compliance distribution, flagged ownership anomalies and one check per table. `bbbee_verification_log.csv` records method, cells and page. `quality_flag` identifies observation-specific concerns; `comparability_flag` describes cross-year/series limits. `source_table` uses the report's printed numbering; compliance has separate count and percentage table identifiers.
