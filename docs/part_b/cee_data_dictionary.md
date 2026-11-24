# Dataset dictionary

All percentages are on a 0–100 scale. Blank CSV fields and Parquet nulls mean missing, not zero. Counts are integers; Parquet stores integer counts where complete and nullable numeric values where national and sector coverage records have differing fields. Every `source_id` links to `source_inventory.csv`. PDF page numbers are one-based.

## Management raw

Key: `reporting_year`, `geographic_scope`, `sector_original` (null for national), `reporting_population`, `occupational_level`, `population_group`, `gender`. Fields: `publication_year` is the report year, not a verified release date; `sector_standardised` is currently null; `employee_count` is the reported demographic count; `total_employees` is the published total of permanent employees in that management level including foreign nationals, repeated for convenience and must not be summed over rows; `published_representation_pct` is the printed percentage; `calculated_representation_pct` is 100 times the count divided by that total. `source_page_pdf`, `source_page_printed`, `source_table` locate the cell. `source_value_original` combines the extracted count and published percent; `quality_flag` identifies count reconciliation. Demographic records have no total row.

## Management derived

Key: year, scope, original sector, reporting population and occupational level. Common fields have the same meaning as raw. `total_managers` is the source total; `black_manager_count` sums African, Coloured and Indian men and women; `black_female_manager_count` sums African, Coloured and Indian women; the two corresponding `_pct` fields divide these counts by total managers and multiply by 100. `calculation_method` is `count_based`; the source data do not establish statutory citizenship qualifications. `comparability_flag` records unresolved sector mapping or reporting-population limits. Percentages are null when counts fail to reconcile.

## Reporting coverage

Key: year, geographic scope, sector original, reporting population. `reports_received` counts reports, not necessarily employers; `employees_covered` counts reported employees including temporary employees. `employer_eligibility_definition` is a short pointer rather than a complete legal definition. `source_page_pdf`, `source_table`, and `quality_flag` indicate provenance and transcription status. `sector_standardised` is unmapped.

## EAP benchmarks

Key: reporting year, geographic scope, population group and gender. `benchmark_year` and `benchmark_quarter` identify the cited QLFS reference period; `representation_pct` is the published EAP percentage, not a management observation. Foreign-national missing values are null. `source_page_pdf` points to the PoC Table 7 reproduction of EAP; `quality_flag` documents verification.

## Sector crosswalk

Key: year, `sector_original`. `sector_standardised` is deliberately empty; `classification_system` describes the source, `mapping_method`, `mapping_confidence`, `comparable_across_years` and `notes` record the absence of a defensible historical mapping. The original sector labels in the coverage table are as printed there, and should not be joined to Appendix C by position without further verification.

## Validation results

`page`, `sector`, `level` identify the record checked; `check` is count reconciliation, percentage difference, or sector-minus-national total; `observed` is the signed difference in counts or percentage points; `passed` reports the relevant check result. A failed percentage difference is a discrepancy for investigation, not a corrected value. The percentage threshold is 0.051 percentage points.

## Historical extension

`calculation_method` also takes `published_percentage_sum` for 2016 and 2018 sector records and the retrospective 2016 national observations. Those records have null counts, and their indicators sum rounded printed components. A national observation for 2016 has `source_id=cee_19th` and `publication_year=2019`, reflecting the retrospective report rather than the report year. The crosswalk now contains all extracted original year/sector labels; none are asserted comparable. EAP records contain eight demographic cells per year; missing foreign-national EAP cells are not included as rows. Count fields use nullable integer types in Parquet.

## Subsequent update

2018 sector observations now use `count_based`. Only 2016 remains percentage-only. The coverage dataset additionally includes `source_sector_fragment` (possibly truncated source text) and `sector_row_number` (one-based row order within the source table); a null or partial `sector_original` must not be used as an analytical join key. The 2023 coverage flag identifies its 300-employee mismatch. These statements supersede earlier statements that 2018 sectors are percentage-only or that coverage is limited to 2024.

## Independent review update

The 2016 national observations are now count-based using counts transcribed from 19th report Appendix E, PDF page 106; 2016 sector observations remain published percentage sums. Ten wrapped coverage labels for 2021, 2022 and 2025 are reconstructed from source text using the associated counts; other labels remain subject to review. The original extracted fragment remains in `source_sector_fragment`. See `cee_independent_review.md` for verification scope.

## Final independent review update

For raw management and reporting coverage, `comparability_flag` is `2025_reporting_regime_break` for 2025 and null otherwise. The derived management table also carries this flag for 2025 and flags the 2016 retrospective coverage difference and 2019 national–sector discrepancy. Coverage `source_sector_fragment` preserves the initially extracted text; seven 2020 labels and the earlier ten wrapped labels are reconstructed in the generator. EAP `benchmark_year` and `benchmark_quarter` describe the benchmark rather than the employer-reporting regime. Final source-check scope and analytical filters are in `cee_independent_review.md`.
