# Exhaustive data dictionary

Schemas below are taken from the final Parquet inventory. The two company price files have identical schemas. A nullable field can contain null; this differs from a numeric zero. Non-nullable fields are enforced during verification. All original numeric values are retained, including zeros and flagged values. Unknown metadata is represented by null, not guessed from names.

## prices_daily.parquet and prices_observed.parquet

Complete canonical source panel, including financial placeholders. Primary key: `instrument_id, date`.

| Column | Arrow type | Nullable | Units | Definition and caveat |
| --- | --- | --- | --- | --- |
| `date` | `date32[day]` | no | Native date (no time-of-day) | Observed source session date; no generated dates. |
| `instrument_id` | `string` | no | Not applicable | Original IRESS Mnemonic; not a permanent issuer identifier. |
| `ticker` | `string` | yes | Not applicable | Mnemonic prefix only when the full identifier matches ticker:XJSE:EQU. |
| `company_name` | `string` | yes | Not applicable | Original source label; not independently verified historical name. |
| `close_raw` | `double` | yes | Unverified source quote/level units; no conversion | Reported numeric close; units and adjustment basis unverified. |
| `volume` | `int64` | yes | Reported source volume; provider unit definition unverified | Reported volume; integer conversion validated without rounding; null differs from zero. |
| `number_of_trades` | `int64` | yes | Count / row position as defined | Reported trade count; integer conversion validated without rounding. |
| `source_batch` | `int16` | no | Not applicable | Canonical source company workbook number. |
| `source_file` | `string` | no | Not applicable | Canonical original workbook filename. |
| `source_sheet` | `string` | no | Not applicable | Canonical original worksheet name. |
| `source_row` | `int32` | no | Count / row position as defined | Canonical original Excel row; header is row 1. |
| `source_sha256` | `string` | no | Not applicable | SHA-256 of the canonical original workbook. |
| `duplicate_copy_count` | `int32` | no | Count / row position as defined | Number of source copies, including the canonical copy. |
| `has_valid_price` | `bool` | no | Not applicable | Close is finite and strictly positive; not proof of active trading. |
| `is_missing_price` | `bool` | no | Not applicable | Parsed close is null. |
| `is_zero_price` | `bool` | no | Not applicable | Reported close is explicitly numeric zero. |
| `is_negative_price` | `bool` | no | Not applicable | Reported close is finite and negative. |
| `is_nonfinite_price` | `bool` | no | Not applicable | Reported close is NaN or infinity. |
| `invalid_price` | `bool` | no | Not applicable | Non-null close is nonpositive/nonfinite, or close has a parse issue; missing alone is separate. |
| `has_positive_volume` | `bool` | no | Not applicable | Reported volume is strictly positive. |
| `is_zero_volume` | `bool` | no | Not applicable | Reported volume is explicitly zero. |
| `is_missing_volume` | `bool` | no | Not applicable | Reported volume is null. |
| `is_negative_volume` | `bool` | no | Not applicable | Reported volume is negative; retained unchanged. |
| `is_missing_trade_count` | `bool` | no | Not applicable | Reported number_of_trades is null. |
| `is_negative_trade_count` | `bool` | no | Not applicable | Reported number_of_trades is negative; retained unchanged. |
| `is_empty_placeholder` | `bool` | no | Not applicable | All three financial fields null and no numeric parse issue. |
| `numeric_parse_issue` | `bool` | no | Not applicable | At least one source financial field has a parsing/nonfinite issue. |
| `parse_issues` | `string` | no | Not applicable | Semicolon-separated source parsing issue codes; empty string means none. |
| `unparsed_values` | `string` | no | Not applicable | Original problematic tokens encoded as JSON, or empty string. |
| `previous_observed_date` | `date32[day]` | yes | Native date (no time-of-day) | Previous canonical row date for the same instrument; may have blank financial fields. |
| `previous_price_date` | `date32[day]` | yes | Native date (no time-of-day) | Nearest earlier finite positive close date, even across gaps; never a listing date. |
| `price_gap_sessions` | `int32` | yes | Observed company-calendar sessions | Current session position minus nearest earlier valid-price position; null if none. |
| `is_adjacent_to_previous_session` | `bool` | no | Not applicable | Previous canonical row is the immediately preceding full-calendar session. |
| `has_valid_adjacent_price` | `bool` | no | Not applicable | Current and immediately preceding session both have finite positive closes. |
| `missing_or_invalid_adjacent_observation` | `bool` | no | Not applicable | Complement of has_valid_adjacent_price, including each series' first row. |
| `unchanged_adjacent_price` | `bool` | yes | Not applicable | Equality of adjacent valid positive closes; null if the pair is unusable; not a verified zero economic return. |
| `trailing_constant_price_sessions` | `int32` | no | Observed company-calendar sessions | Consecutive equal positive closes through this date only; 1 on first valid price, 0 on missing/invalid price. |
| `potential_stale_price` | `bool` | no | Not applicable | Valid close with no positive current volume and either unchanged adjacent close or trailing run >= configured threshold; diagnostic only. |
| `extreme_price_change` | `bool` | yes | Not applicable | Absolute diagnostic raw price change strictly exceeds configured threshold (0.30); null without a usable adjacent pair. |
| `diagnostic_price_return` | `double` | yes | Fractional raw price change; 0.30 means 30% | close_raw / immediately previous session close - 1; only finite positive adjacent pairs; unverified economic interpretation. |
| `quality_rule_version` | `string` | no | Not applicable | Version binding all derived flags to the processing rules. |

## instruments.parquet

All extracted instruments and descriptive coverage/provenance. Primary key: `instrument_id`.

| Column | Arrow type | Nullable | Units | Definition and caveat |
| --- | --- | --- | --- | --- |
| `instrument_id` | `string` | no | Not applicable | Original IRESS Mnemonic; includes empty histories and distinct share classes. |
| `ticker` | `string` | yes | Not applicable | Syntactically parsed mnemonic prefix, not a permanent identifier. |
| `company_name` | `string` | yes | Not applicable | First source label ordered by source file, sheet and row; not issuer identity. |
| `company_names` | `list<element: string>` | no | Not applicable | Sorted distinct observed source labels. |
| `observed_price_start` | `date32[day]` | yes | Native date (no time-of-day) | First finite positive source close; not listing date. |
| `observed_price_end` | `date32[day]` | yes | Native date (no time-of-day) | Last finite positive source close; not delisting date. |
| `observed_positive_volume_start` | `date32[day]` | yes | Native date (no time-of-day) | First positive reported volume date; not listing date. |
| `observed_positive_volume_end` | `date32[day]` | yes | Native date (no time-of-day) | Last positive reported volume date; not delisting date. |
| `total_observations` | `int64` | no | Count / row position as defined | Canonical rows including placeholders. |
| `reported_financial_observations` | `int64` | no | Count / row position as defined | Canonical rows with at least one non-null numeric financial field. |
| `valid_price_observations` | `int64` | no | Count / row position as defined | Finite positive closing-price rows. |
| `positive_volume_observations` | `int64` | no | Count / row position as defined | Strictly positive reported-volume rows. |
| `missing_price_observations` | `int64` | no | Count / row position as defined | Rows whose parsed close is null; zero/negative prices are separate. |
| `calendar_sessions` | `int64` | no | Observed company-calendar sessions | Size of the complete observed company-calendar union; coverage denominator. |
| `valid_price_coverage_pct` | `double` | no | Percent of observed calendar sessions | 100 * valid_price_observations / calendar_sessions; full-period description, not eligibility. |
| `raw_source_rows` | `int64` | no | Count / row position as defined | Original row count across all source copies. |
| `duplicate_extra_rows` | `int64` | no | Count / row position as defined | raw_source_rows minus total_observations. |
| `source_batches` | `list<element: int16>` | no | Not applicable | All original source batch numbers, sorted, including duplicates. |
| `source_files` | `list<element: string>` | no | Not applicable | All original workbook filenames, sorted. |
| `isin` | `string` | yes | Not applicable | Unknown: no verified ISIN mapping supplied. |
| `issuer_id` | `string` | yes | Not applicable | Unknown: no verified instrument-to-issuer mapping supplied. |
| `security_type` | `string` | yes | Not applicable | Unknown: no classification inferred from name or EQU suffix. |
| `sector_code` | `string` | yes | Not applicable | Unknown: historical sector membership requires effective-dated enrichment. |
| `listing_date` | `date32[day]` | yes | Native date (no time-of-day) | Unknown: actual listing date requires independent source. |
| `delisting_date` | `date32[day]` | yes | Native date (no time-of-day) | Unknown: actual delisting date requires independent source. |

## instrument_metadata_2026-11-23.parquet

IRESS Expert Screener snapshot captured 2026-11-23. One row per instrument ID; join to `instruments.parquet` on `instrument_id`. Snapshot labels are not historical attributes. Primary key: `instrument_id`.

| Column | Arrow type | Nullable | Units | Definition and caveat |
| --- | --- | --- | --- | --- |
| `instrument_id` | `string` | no | Not applicable | Full decoded IRESS mnemonic; primary key. |
| `ticker` | `string` | no | Not applicable | Original Screener ticker; not a permanent issuer identifier. |
| `company_name` | `string` | no | Not applicable | Original Screener company name at capture. |
| `isin_raw` | `string` | yes | Not applicable | Original Screener ISIN field, unchanged, including placeholders. |
| `isin_valid` | `bool` | no | Not applicable | Strict ISO 6166 format and Luhn check digit both pass. |
| `isin_format_valid_source` | `bool` | no | Not applicable | Format-only flag in the extraction CSV. |
| `instrument_type` | `string` | no | Not applicable | Original IRESS instrument-type label. |
| `exchange` | `string` | no | Not applicable | Original IRESS exchange label. |
| `country` | `string` | no | Not applicable | Original IRESS country label. |
| `listing_status_snapshot` | `string` | no | Not applicable | Listed/Delisted on snapshot date only. |
| `snapshot_date` | `date32[day]` | no | Not applicable | Local date of this Screener snapshot. |
| `captured_at` | `timestamp[us, tz=Africa/Johannesburg]` | no | Not applicable | Actual extraction timestamp from the validated summary. |
| `has_historical_prices_record` | `bool` | no | Not applicable | Instrument ID occurs in the 1,869-row historical instrument master. |
| `screener_position` | `int32` | no | Not applicable | 1-based row position in the 1,872-result snapshot. |
| `landing_href` | `string` | no | Not applicable | Original IRESS InstrumentLanding href; provenance only. |

## market_index.parquet

Observed daily FTSE/JSE All Share levels with an explicit gap flag. Primary key: `index_id, date`.

| Column | Arrow type | Nullable | Units | Definition and caveat |
| --- | --- | --- | --- | --- |
| `date` | `date32[day]` | yes | Native date (no time-of-day) | Observed source index session date; the missing session is not synthesized. |
| `index_id` | `string` | yes | Not applicable | Original IRESS index mnemonic, J203:XJSE:IND. |
| `index_name` | `string` | yes | Not applicable | Original source index name. |
| `close_raw` | `double` | yes | Unverified source quote/level units; no conversion | Reported numeric index level; source return methodology remains unverified. |
| `source_file` | `string` | yes | Not applicable | Original index workbook filename. |
| `source_sheet` | `string` | yes | Not applicable | Original index worksheet name. |
| `source_row` | `int32` | yes | Count / row position as defined | Original Excel row, including header row 1. |
| `source_sha256` | `string` | yes | Not applicable | SHA-256 of the original index workbook. |
| `frequency` | `string` | yes | Not applicable | daily, after identity, frequency, uniqueness and level checks. |
| `return_variant` | `string` | yes | Not applicable | Unknown/null until price-versus-total-return methodology is verified. |
| `units` | `string` | yes | Not applicable | Unknown/null pending provider definition. |
| `has_valid_price` | `bool` | yes | Not applicable | Finite strictly positive reported level. |
| `previous_observed_date` | `date32[day]` | yes | Native date (no time-of-day) | Previous index source observation, which may precede a missing session. |
| `is_adjacent_to_previous_session` | `bool` | yes | Not applicable | True only when the previous index observation is the immediately preceding full company-calendar session; false after a gap and on the first row. |
| `calendar_complete` | `bool` | yes | Not applicable | Whether the full-period observed company calendar is covered. Descriptive global metadata, not historical eligibility. |

## observation_lineage.parquet

Every original company Excel row, including identical copies. Primary key: `source_file, source_sheet, source_row`.

| Column | Arrow type | Nullable | Units | Definition and caveat |
| --- | --- | --- | --- | --- |
| `instrument_id` | `string` | no | Not applicable | Canonical observation instrument key. |
| `date` | `date32[day]` | no | Native date (no time-of-day) | Canonical observation date key. |
| `source_batch` | `int16` | no | Not applicable | Original workbook batch, including secondary duplicate copies. |
| `source_file` | `string` | no | Not applicable | Original workbook filename. |
| `source_sheet` | `string` | no | Not applicable | Original worksheet name. |
| `source_row` | `int32` | no | Count / row position as defined | Original Excel row, counting the header as row 1. |
| `source_sha256` | `string` | no | Not applicable | SHA-256 of this source workbook. |
| `copy_rank` | `int32` | no | Count / row position as defined | 1-based order by filename, sheet, source row within the instrument-date. |
| `duplicate_copy_count` | `int32` | no | Count / row position as defined | Total original copies of the instrument-date, including the canonical one. |
| `is_canonical` | `bool` | no | Not applicable | True exactly for copy_rank=1. |
| `canonical_source_file` | `string` | no | Not applicable | Selected canonical workbook filename. |
| `canonical_source_sheet` | `string` | no | Not applicable | Selected canonical worksheet name. |
| `canonical_source_row` | `int32` | no | Count / row position as defined | Selected canonical Excel source row. |

## Missing values and derivations

Parsed blank financial cells remain null. Explicit numeric zero is preserved and counts as an observed financial value. A missing close alone sets is_missing_price; invalid_price separately identifies zero, negative, nonfinite or unparsed closes. has_valid_price is numerical validity only. Boolean unchanged/extreme flags are null when their adjacent comparison cannot be made; they are not silently set to false. Unparseable source numeric tokens, if any, remain in unparsed_values/parse_issues alongside the parsed numeric null. The supplied audited inputs contain no numeric parsing issues.

Quality rule version: `trailing-1.0.0`. Trailing constant-price threshold: 20 sessions. Extreme raw-change threshold: strict absolute change >0.3. Diagnostics use the full observed company-session calendar and immediately adjacent valid positive prices. No forward fill, unit conversion, dividend/split adjustment, clipping or extrapolation is performed.

## Relationships and cardinality

prices_daily → instruments is many-to-one on instrument_id. instruments → instrument_metadata_2026-11-23 is one-to-one on instrument_id for all 1,869 master IDs; three metadata IDs have no master row. Snapshot status must not be backdated. prices_observed is an exact row subset of prices_daily. prices_daily → observation_lineage is one-to-many on instrument_id,date; is_canonical selects exactly one original copy. Company prices → market_index is many-to-one on date for the single J203 ID, with unmatched dates retained explicitly. Instrument IDs are not issuer IDs. Source files may have source labels repeated across historical dates; these do not establish name validity at each date.
## Historical Bulletin datasets

### jse_bulletin_securities.parquet

Key: source_file, worksheet, source_row. Dates are Arrow date32; flags are Boolean. All identity and industry labels preserve source text.

| Column | Arrow type | Nullable | Meaning |
| --- | --- | --- | --- |
| historical_security_name | string | True | Exact source SECURITY cell, including original case/spacing; null if absent. |
| historical_share_code | string | True | Exact source SHARE CODE cell; not a permanent identifier. |
| nature_of_business_raw | string | True | Exact historical JSE Bulletin label; no asserted ICB equivalence. |
| source_file | string | True | Original workbook filename; raw workbook excluded from portable package. |
| source_sha256 | string | True | SHA-256 of unchanged original workbook, also recorded in source inventory. |
| worksheet | string | True | Exact original worksheet title. |
| security_type_rule | string | True | Semicolon-separated explicit source-label/name rules; empty means no rule fired. |
| instrument_id | string | True | Accepted exact IRESS mnemonic; null for unresolved bulletin rows. |
| match_status | string | True | matched, ambiguous or unmatched; no inferred historical status. |
| match_method | string | True | Exact ticker plus validated normalized name or documented display variant; _DEL variant requires validation; unresolved methods and duplicate-ID/code conflicts enter review. |
| match_confidence | string | True | high_label_concordance or unresolved; not independent historical identity verification. |
| match_evidence | string | True | Human-readable accepted label evidence or unresolved reason. |
| candidate_instrument_ids | string | True | Semicolon-separated candidates, including unaccepted review suggestions. |
| bulletin_month | date32[day] | True | Reporting month encoded as first day; not publication date. |
| identity_incomplete | bool | False | Missing name or share code; preserved for review. |
| industry_missing | bool | False | No nonempty raw industry label. |
| likely_investment_product | bool | False | Exact explicit product-label rule; no row exclusion. |
| likely_non_company_security | bool | False | Product, preference, other security labels or explicit name class marker; diagnostic only. |
| mining_candidate | bool | False | Exact enumerated mining/metal source labels; not confirmed policy applicability. |
| has_historical_prices_record | bool | False | Accepted ID occurs in 1,869-row historical-price master; false if unresolved or metadata-only. |
| source_row | int64 | False | 1-based original Excel row. |
| header_row | int64 | False | 1-based applicable section header row. |
### event_industry_classifications.parquet

Key: event_id, instrument_id. Dates are Arrow date32; flags are Boolean. All identity and industry labels preserve source text.

| Column | Arrow type | Nullable | Meaning |
| --- | --- | --- | --- |
| historical_security_name | string | True | Exact source SECURITY cell, including original case/spacing; null if absent. |
| historical_share_code | string | True | Exact source SHARE CODE cell; not a permanent identifier. |
| nature_of_business_raw | string | True | Exact historical JSE Bulletin label; no asserted ICB equivalence. |
| source_file | string | True | Original workbook filename; raw workbook excluded from portable package. |
| source_sha256 | string | True | SHA-256 of unchanged original workbook, also recorded in source inventory. |
| worksheet | string | True | Exact original worksheet title. |
| security_type_rule | string | True | Semicolon-separated explicit source-label/name rules; empty means no rule fired. |
| instrument_id | string | True | Accepted exact IRESS mnemonic; null for unresolved bulletin rows. |
| match_status | string | True | matched, ambiguous or unmatched; no inferred historical status. |
| match_method | string | True | Exact ticker plus validated normalized name or documented display variant; _DEL variant requires validation; unresolved methods and duplicate-ID/code conflicts enter review. |
| match_confidence | string | True | high_label_concordance or unresolved; not independent historical identity verification. |
| match_evidence | string | True | Human-readable accepted label evidence or unresolved reason. |
| candidate_instrument_ids | string | True | Semicolon-separated candidates, including unaccepted review suggestions. |
| event_id | string | True | Provisional event key reused from existing event audit. |
| quality_flags | string | True | Semicolon-separated publication/identity limitations and non-company screening flags. |
| bulletin_month | date32[day] | True | Reporting month encoded as first day; not publication date. |
| event_date | date32[day] | True | Provisional event date; no new date research performed. |
| publication_date | date32[day] | True | Unknown (all null); no publication dates invented. |
| identity_incomplete | bool | False | Missing name or share code; preserved for review. |
| industry_missing | bool | False | No nonempty raw industry label. |
| likely_investment_product | bool | False | Exact explicit product-label rule; no row exclusion. |
| likely_non_company_security | bool | False | Product, preference, other security labels or explicit name class marker; diagnostic only. |
| mining_candidate | bool | False | Exact enumerated mining/metal source labels; not confirmed policy applicability. |
| has_historical_prices_record | bool | False | Accepted ID occurs in 1,869-row historical-price master; false if unresolved or metadata-only. |
| preannouncement_availability_verified | bool | False | False throughout; reporting month precedes event but publication availability is unverified. |
| is_retrospective | bool | False | False; no post-event classifications included or used for filling. |
| event_date_provisional | bool | False | True; existing event dates require separate confirmation. |
| source_row | int64 | False | 1-based original Excel row. |
| header_row | int64 | False | 1-based applicable section header row. |
