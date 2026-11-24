# Part B supporting data dictionary

The five UTF-8 CSVs are in `data/part_b/processed/`. Dates use ISO 8601. Percentages use the 0–100 scale and preserve the published decimal precision. Page numbers are one-based. `source_id` links to `supporting_source_inventory.csv`.

## ee_sector_targets.csv

| Field | Definition |
|---|---|
| `target_id` | Unique identifier built from policy version, sector, level and gender. |
| `policy_version`, `policy_status_at_publication` | `draft_2023` / `draft` or `final_2025` / `final`. |
| `announcement_date`, `gazette_number`, `notice_number` | Date printed on the gazette and integer identifiers of the publication and notice. |
| `target_horizon_years` | Five years in both editions. |
| `sector_original`, `sector_id` | Original table heading, with wrapping and printed sequence number removed, and canonical sector key. |
| `geographic_scope` | `national`. Draft values come from the National row group. Final values apply to nationally identified sectors. |
| `occupational_level` | `top_management` or `senior_management`. |
| `target_population` | `black` for the draft’s published BLACK column and `designated_groups` for the final notice’s published DESIGNATED GROUPS columns. |
| `gender` | `male`, `female` or source-published `total`. The gender cells are contributions to the whole level. |
| `target_pct`, `published_value_original` | Numeric percent and original percent string, including its printed decimal separator and percent sign. |
| `source_id`, `source_page_pdf`, `source_page_printed` | Source identifier, physical PDF page and outer gazette folio. |
| `quality_flag` | `ok` for this release. The pipeline distinguishes published rounding differences of up to 0.1 percentage points and larger published total discrepancies. |

## ee_gazette_workforce_baseline_2022.csv

| Field | Definition |
|---|---|
| `reporting_year`, `publication_date` | Workforce profile year 2022 and draft gazette publication date 2023-05-12. |
| `sector_original`, `sector_id`, `occupational_level`, `gender` | Same labels and keys as the draft target observations. The analytical key is sector, occupational level and gender. |
| `population_group` | `black`, the published BLACK column. |
| `observed_pct`, `published_value_original` | Observed percent and original percent string. |
| `reporting_population` | Source wording `Workforce Profile 2022 (All employers)`. The extract contains published shares. Coverage, count and citizenship details are limited as described in the handover. |
| `source_id`, `source_page_pdf`, `source_page_printed`, `quality_flag` | Same conventions as the targets. |

## ee_sector_reference.csv

| Field | Definition |
|---|---|
| `sector_id`, `sector_name` | Unique canonical key and display label taken from the final table. |
| `draft_2023_sector_original`, `final_2025_sector_original` | Draft and final labels used in the targets. |
| `cee_2023_sector_original`, `cee_2024_sector_original` | Existing CEE sector strings for workforce years 2023 and 2024, as used in the count dataset. |
| `mapping_status` | `matched_label` for equivalent headings, including spelling and punctuation variants. `matched_within_report_evidence` for the trade label supported by the CEE body-to-appendix comparison. |
| `mapping_evidence`, `notes` | Source evidence and relevant label details. |

## statssa_sector_employment.csv

| Field | Definition |
|---|---|
| `observation_year`, `observation_quarter`, `observation_period` | Observation year, quarter 3 and combined key such as `2016Q3`. |
| `industry_original`, `industry_standardised` | Published row label and standardised key. `national_total` explicitly identifies the separately published aggregate. Key is observation period × standardised industry. |
| `geographic_scope`, `survey`, `population_coverage` | National, QLFS, employed persons aged 15–64 in the household survey. |
| `published_employment_value`, `published_unit`, `employment_persons` | Original estimate in the printed `Thousand` unit and arithmetic conversion × 1,000. |
| `publication_date`, `publication_vintage` | Official release date and publication quarter of the PDF. The year-on-year comparison column has a later vintage than its observation period. |
| `source_id`, `source_table_or_sheet`, `source_page_or_cell` | Release ID, Table B, and printed page, physical PDF page and source column. |
| `quality_flag` | `ok` for the available, verified, published estimates. |
| `comparability_flag` | `mixed_publication_vintage` ordinarily. Separate mixed-vintage flags identify 2020–2021 pandemic telephone collection, 2022 return to mainly in-person collection and the 2025 questionnaire revision. |

## supporting_data_validation.csv

`dataset` and `source` identify the scope of each `check`. `expected_result` and `actual_result` preserve the compared values or counts. `status` uses `pass`, `source_note` for documented source arithmetic, and `source_limitation` for inaccessible sources. A `fail` aborts generation. `discrepancy_or_explanation` records methods, locations and reasons where applicable.

## supporting_source_inventory.csv

`original_url` gives the publisher link or attachment listing. `acquisition_url` gives the direct download, archived-copy link or confirmed attempted attachment URL. `publication_date` is blank when the exact date has not been established. `local_path`, `file_size_bytes`, `page_count` and `sha256` identify each preserved document. Reference-only and unavailable sources have blank local file fields. `acquisition_date`, `acquisition_status` and `notes` document collection and provenance.
