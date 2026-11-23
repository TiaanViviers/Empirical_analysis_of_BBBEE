# IRESS JSE historical data: thesis research handover

Data version **1.2.0**. This package contains validated research source data for the Stellenbosch University economics thesis on the efficiency/equity trade-off associated with B-BBEE and Employment Equity policies. It supports **Part A: the JSE stock-market event study**, to be analysed by Monique and subsequent researchers. It contains no estimated policy effects.

## A. Background and scope

IRESS Expert Comparison exports were collected daily for the requested period 1 January 2016–31 March 2026. Actual company observation dates run from **2016-01-04 to 2026-03-31**, across **2,560 observed company-calendar sessions**. The extraction included historical instruments to retain potentially relevant delisted securities, rather than restricting the source to currently trading firms. This does not establish a survivorship-bias-free universe.

The five planned events are:

| Proposed event | Working date |
| --- | --- |
| Mining Charter 2017 | 2017-06-15 |
| Final Mining Charter 2018 | 2018-09-27 |
| Draft EE sector targets | 2023-05-12 |
| Final EE sector targets | 2025-04-15 |
| Draft B-BBEE Code amendments | 2026-01-29 |

**These dates remain provisional.** Official announcement dates, times and trading-session alignment require verification before analysis. The working design uses estimation return dates -250:-30 inclusive (221 dates), event windows [0,+1], [-1,+3] and [0,+5], anticipation [-10,-1], and a visualisation window [-10,+10]. A return at the start of a window also needs the previous session's close.

## B. Dataset overview

| File | Rows | Distinct instruments/indexes | Coverage | Primary key |
| --- | --- | --- | --- | --- |
| [data/instruments.parquet](data/instruments.parquet) | 1,869 | 1,869 | 2016-01-04 to 2026-03-31 | instrument_id |
| [data/instrument_metadata_2026-11-23.parquet](data/instrument_metadata_2026-11-23.parquet) | 1,872 | 1,872 | Snapshot: 2026-11-23 | instrument_id |
| [data/market_index.parquet](data/market_index.parquet) | 2,559 | 1 | 2016-01-04 to 2026-03-31 | index_id, date |
| [data/observation_lineage.parquet](data/observation_lineage.parquet) | 4,789,760 | 1,869 | 2016-01-04 to 2026-03-31 | source_file, source_sheet, source_row |
| [data/prices_daily.parquet](data/prices_daily.parquet) | 4,784,640 | 1,869 | 2016-01-04 to 2026-03-31 | instrument_id, date |
| [data/prices_observed.parquet](data/prices_observed.parquet) | 982,129 | 598 | 2016-01-04 to 2026-03-31 | instrument_id, date |

Coverage for the instrument master describes observed positive-price coverage across the master, not a date column or listing history. All instruments, including entirely empty histories, remain in the master. Physical company/lineage order is instrument, date, and then original source order where applicable; the benchmark is ordered by date. Sorting is a storage convention, not evidence that every row is a usable return.

- **prices_daily** preserves every unique extracted instrument-date, including placeholders, zeros, inactive histories and flagged observations.
- **prices_observed** has precisely the same columns and values, retaining only rows where close, volume or trade count is numerically non-null. **Numeric zero is an observed value.** It is reproducible from the full table using that predicate.
- **instruments** supplies one descriptive record per original mnemonic, with all source batches/files and unknown identifiers represented as nulls.
- **instrument_metadata_2026-11-23** supplies dated Screener labels and raw ISINs; it is a later snapshot, not historical classification. All 1,869 master IDs match, and three additional Screener IDs have no historical price master record.
- **market_index** preserves the reported J203 levels with provenance and adjacency flags. Its missing dates are documented below.
- **observation_lineage** retains every original company source row. Each full-panel key has one canonical source and potentially several identical source copies.

**Neither price table is the final econometric sample.** 594 instruments have at least one finite positive close; 495 ever report positive volume. The compact table also retains zero-only financial histories. An instrument is not necessarily a distinct company.

Other package files:

- [documentation/data_dictionary.md](documentation/data_dictionary.md): exhaustive fields, exact Arrow types, nullability, units and flag definitions.
- [documentation/instrument_metadata.md](documentation/instrument_metadata.md): capture, ISIN checks, reconciliation, joins and point-in-time limits.
- [documentation/processing_summary.md](documentation/processing_summary.md): approved rules, measured reconciliation, validation and reproducibility.
- [documentation/known_limitations.md](documentation/known_limitations.md): methodological and source limitations.
- [documentation/source_inventory.json](documentation/source_inventory.json): original filenames, source hashes, worksheets, row counts, headers and cell types; source workbooks are retained separately.
- [documentation/trading_calendar.csv](documentation/trading_calendar.csv): observed company-calendar sessions used for adjacency, including sessions absent from J203.
- [documentation/event_coverage.csv](documentation/event_coverage.csv): exploratory company/market coverage under different liquidity/completeness definitions, when available from the source audit.
- [documentation/market_event_coverage.csv](documentation/market_event_coverage.csv): benchmark availability for the five proposed windows.
- [data/market_index.metadata.json](data/market_index.metadata.json): benchmark checksum, source reference and known gap metadata. Its path is package-relative; original_processing_path retains the original relative preprocessing location.
- [manifest.json](manifest.json): dataset versions, schemas, sizes, counts, code/configuration/source fingerprints and file checksums. `manifest.sha256` checks the manifest itself.
- [documentation/verify_package.py](documentation/verify_package.py): independent payload/Parquet verification; it needs Python and PyArrow, but no extraction repository or raw exports.
- [documentation/example_python.py](documentation/example_python.py) and [documentation/example_r.R](documentation/example_r.R): executable copies of the loading/filtering examples below; run from the package root.

## C. Important fields and interpretation

Dates are native **Arrow date32**, not locale-dependent text. `instrument_id` preserves the exact IRESS mnemonic, generally `TICKER:XJSE:EQU`. `ticker` is only a syntactically parsed prefix; it is not a permanent company identifier. Source names are provider labels repeated over source rows, not a verified historical name series.

`close_raw` is nullable Float64. Company `volume` and `number_of_trades` are nullable Int64 after validating exact integral conversion and range. Null means the source did not supply a parsed numeric value. Zero remains zero and is never converted to missing. Any numeric parsing tokens are retained in `parse_issues`/`unparsed_values`.

`has_valid_price` means only finite and strictly positive. It does not certify listing status, genuine trading, economic return validity or adjustment. `is_missing_price`, `is_zero_price`, `invalid_price`, `has_positive_volume`, `is_zero_volume`, `is_missing_volume` and `is_empty_placeholder` separate distinct source states.

`unchanged_adjacent_price` is equality between two valid closes on consecutive observed sessions. It is null when that comparison is unavailable. `trailing_constant_price_sessions` counts the equal-price run **through the current date only**: 1 on the first valid close and 0 for missing/invalid prices. It resets after a gap, missing/invalid close or price change.

`potential_stale_price` requires a valid close, no positive current volume, and either an unchanged valid adjacent close or a trailing constant run of at least 20 sessions. This is a diagnostic convention, not an exclusion or proof of staleness. No future observation determines this flag.

`diagnostic_price_return` is `current / previous - 1` only for finite positive closes on immediately adjacent full-calendar sessions. `extreme_price_change` is true when its absolute value is **strictly greater than 30%**; it is null if the return cannot be formed. `has_valid_adjacent_price` and its complement `missing_or_invalid_adjacent_observation` expose unavailable pairs, including the first row. `previous_price_date`/`price_gap_sessions` expose the nearest earlier valid price, but **a price across a gap is never used for an ordinary daily diagnostic return**.

Flags use rule version `trailing-1.0.0`. Full-period coverage fields and `calendar_complete` are descriptive inventory properties. They must not determine historical eligibility using future information.

## D. Important data quirks and limitations

### 1. Empty observations

There are **3,802,511 entirely blank financial rows (79.47% of the canonical panel)**. 1,275 instruments have no positive price, and 1,271 have no reported financial values at all. Complete placeholder calendars are not proof that securities were listed throughout 2016–2026.

### 2. Stale or unchanged prices

The source includes long constant-price histories, often with zero volume. The approved trailing rule flags **290,385 positive-price rows (29.60% of valid prices)**. There are 387,135 unchanged adjacent valid-price pairs. These are not automatically genuine zero economic returns. Phase 1's full-run descriptive stale count can differ because it used later observations to describe entire runs; final row flags use trailing information only.

### 3. Multiple securities per company

Ordinary shares, preference shares, historical identifiers and other classes may coexist. Source labels can match across different IDs; matching names are not sufficient grounds to merge them. No verified issuer-level mapping exists. `isin`, `issuer_id`, `security_type` and `sector_code` in the master remain unknown.

### 4. Historical listings

`observed_price_start/end` and positive-volume dates describe available source data. **They are not actual listing or delisting dates.** The actual `listing_date` and `delisting_date` fields remain null. Suspensions and off-market or inactive histories require separate evidence.

### 5. Corporate actions and unusual prices

The data retains **1,155 zero closes** and **3,566 extreme diagnostic changes**. Some discontinuities may reflect splits, consolidations, dividends, distributions, rights issues, identifier changes or source errors. The preprocessing did not systematically adjust for corporate actions, and the adjustment basis of the source Close field remains unverified. Nothing was clipped or repaired from price ratios alone.

### 6. Price units

Many equity values appear consistent with JSE cents, but units have not been formally verified. **Do not silently convert to ZAR.** The benchmark's `units` and `return_variant` are null pending provider confirmation. Comparability of equity and market return methodology also requires review.

### 7. Returns

This is not a verified dividend-adjusted or total-economic-return dataset. Raw diagnostic changes must not silently become the thesis return series. Review provider definitions, corporate-action histories and treatment of dividends, illiquidity and terminal prices first.

Do not compute a one-day return with a simple grouped `shift()` on `prices_observed`: removing placeholder rows can hide multi-session gaps. Use the full calendar and validate both endpoints. Stored diagnostic returns were computed before forming the compact subset.

### 8. J203 missing observation

The benchmark contains **2,559 observed daily levels**. Missing company-calendar session dates: **2024-01-02**. In the supplied thesis sources, the gap is 2 January 2024; company trading is recorded that day. No index value was interpolated. The following index observation, 3 January 2024, has `is_adjacent_to_previous_session=false`, preventing a multi-session change from being treated as daily.

Benchmark coverage for each planned event is checked separately:

| Event date | Market estimation returns / 221 | Market -10:+10 returns / 21 | Required market closes complete |
| --- | --- | --- | --- |
| 2017-06-15 | 221 | 21 | True |
| 2018-09-27 | 221 | 21 | True |
| 2023-05-12 | 221 | 21 | True |
| 2025-04-15 | 221 | 21 | True |
| 2026-01-29 | 221 | 21 | True |

A gap outside the required windows does not invalidate complete market-paired windows. This establishes data availability, not an approved final company sample or return methodology.

### 9. Identical duplicates

**4,789,760 original company rows became 4,784,640 unique keys by reducing 5,120 identical extra copies.** There were no conflicting source values. Canonical order is filename, worksheet, then Excel row. The original thesis extraction overlaps were Interhold (`ITH:XJSE:EQU`) and Interleisure (`ITL:XJSE:EQU`) in batches 9 and 10. Every copy remains in lineage, including the chosen copy; `duplicate_copy_count` includes it. A conflicting key stops a future build.

### 10. Possible extraction omissions

The independently captured **2026-11-23 Screener snapshot** has 1,872 distinct IDs and matches all 1,869 historical-price master IDs; three IDs occur only in the snapshot. The historical batch-13 export had 99 rows, but identifier-level reconciliation confirms that its 1,869-ID combined master is covered by this later Screener view. The snapshot cannot prove the exchange's historical universe or survivorship-bias freedom.

### 11. Historical classifications

The dated Screener snapshot supplies raw ISIN fields and current listing labels, but verified historical sectors, ISIN histories, issuer relationships and listing histories remain absent. A current classification must not be applied retrospectively without appropriate historical evidence. Enrichment needs effective dates and publication/availability dates, including statement revisions and vintages.

## E. Processing decisions

Performed: date parsing and consistent names/types; exact preservation of original mnemonics, company labels and numeric values; exact integral quantity conversion; deterministic identical-copy reduction; full original-row lineage; retention of all canonical placeholders; trailing-only diagnostics; creation of the numeric-observed subset; benchmark calendar validation; and schema/value/count/checksum validation.

Not performed: company-level identity resolution, inferred security-type or historical-sector assignment, listing-date inference, dividend/split adjustment, currency conversion, price interpolation, winsorisation, missing-price filling, liquidity-based exclusion, event-study sample construction, abnormal-return estimation, CAR/CAAR, regressions or policy-effect analysis.

The source Excel workbooks and Playwright extraction automation were preserved. This portable package excludes them, browser profiles, authentication material, temporary intermediates and debugging artifacts. Source hashes refer to the separately retained originals; they are not credentials. Underlying source-data distribution permissions continue to apply.

## F. Loading, filtering and joining

Work from this directory, or adapt relative paths to where it is copied. Parquet loading does not require IRESS or rerunning extraction/preprocessing. Python needs `pyarrow`; R needs `arrow` and `dplyr`. Use explicit filenames because the eight datasets have different schemas. Join `data/instrument_metadata_2026-11-23.parquet` to `data/instruments.parquet` on `instrument_id` as one-to-one for the 1,869 master IDs; use a left join from the master to retain its universe. The three Screener-only IDs have no historical-price master row. Never use the 2026 listing label to select firms for earlier dates.

### Python

```python
from datetime import date
import pyarrow.dataset as ds
import pyarrow.parquet as pq

prices = ds.dataset("data/prices_observed.parquet", format="parquet")
one_instrument = prices.to_table(
    filter=(ds.field("instrument_id") == "SHP:XJSE:EQU")
    & (ds.field("date") >= date(2017, 1, 1))
    & (ds.field("date") <= date(2017, 12, 31)),
    columns=["date", "instrument_id", "close_raw", "volume",
             "has_valid_price", "potential_stale_price"],
)
instruments = pq.read_table("data/instruments.parquet")
market = pq.read_table("data/market_index.parquet")
print(one_instrument.num_rows, instruments.num_rows, market.num_rows)
```

### R

```r
library(arrow)
library(dplyr)

prices <- open_dataset("data/prices_observed.parquet", format = "parquet")
one_instrument <- prices |>
  filter(instrument_id == "SHP:XJSE:EQU",
         date >= as.Date("2017-01-01"),
         date <= as.Date("2017-12-31")) |>
  select(date, instrument_id, close_raw, volume,
         has_valid_price, potential_stale_price) |>
  collect()
instruments <- read_parquet("data/instruments.parquet")
market <- read_parquet("data/market_index.parquet")
with_metadata <- left_join(one_instrument, instruments,
                           by = "instrument_id", relationship = "many-to-one")
```

Arrow dates map to R Date values; nullable Int64 values can use R's `integer64` representation. Preserve that representation rather than coercing counts to 32-bit integers. The [official Arrow R dataset documentation](https://arrow.apache.org/docs/r/articles/dataset.html) explains lazy filtering and collecting a selected slice into memory.

Join prices to the master by `instrument_id` (many-to-one). Join company prices to the single market index by `date`, retaining unmatched dates explicitly. Join lineage by `(instrument_id, date)` only when investigating all source copies: this is one-to-many and expands duplicated keys. Filter lineage to `is_canonical` for the selected source reference. None of these joins resolves issuers. Future identifier histories and financial/exposure characteristics require point-in-time-valid joins constrained by both effective date and information availability.

Independent package check:

```bash
python documentation/verify_package.py
```

The verifier checks the manifest checksum, every payload checksum, Parquet readability, exact documented schemas/nullability and dataset counts/coverage. Deep source-to-output, lineage and trailing-rule checks were run before packaging and are recorded in the manifest. The manifest itself uses a checksum sidecar because a file cannot contain its own ordinary SHA-256 digest.

## G. What remains before thesis analysis

Obtain or independently verify: (1) ISIN and instrument-to-issuer histories; (2) ordinary/preference/other security classifications; (3) historical JSE sectors; (4) actual listing, delisting and suspension histories; (5) corporate actions and the correct equity/benchmark return methodology; (6) official policy-announcement dates and times; (7) dated market capitalisation, leverage and book-to-market measures; and (8) B-BBEE/Employment Equity exposure. Resolve the missing benchmark session and reconcile the dated source universe where possible.

Use historically appropriate identifiers and point-in-time-valid information. Effective date alone is insufficient for financial characteristics: record publication/availability dates and retain revised vintages. Do not use later listing status, future coverage, current sectors or later exposures to select earlier firms.

## H. Recommended next research workflow

1. Load the prepared tables and verify package integrity; review flags and the dictionary.
2. Acquire and integrate the missing identifier, issuer and historical metadata.
3. Verify price units, corporate actions and equity/benchmark return methodologies.
4. Confirm policy dates/times and map them to the appropriate market session.
5. Construct event-specific eligible instrument/company samples under explicit rules.
6. Specify liquidity/completeness restrictions and compare sample sensitivity.
7. Calculate approved returns and implement the event-study analysis separately.
8. Run robustness checks for sample composition, liquidity, missingness, return basis and windows.

Those research steps have not been performed by this preprocessing pipeline. The package closes the source-data preparation phase while preserving the unresolved research choices.
## Historical JSE Bulletin classifications

Added `data/jse_bulletin_securities.parquet` (6,255 security/month rows) and `data/event_industry_classifications.parquet` (one accepted instrument/event). [Historical classification documentation](documentation/historical_industry_classifications.md) defines the labels, source dates, matching, mining candidates and provisional event coverage. Historical labels are now partially available; earlier references to absent historical sectors mean verified comprehensive sector/ICB histories remain unavailable. All five event snapshots precede the provisional event by reporting month; publication availability is unverified. The two requested cross-check months are missing. [Coverage](documentation/historical_industry_coverage.csv), [manual review](documentation/historical_industry_manual_review.csv) and [snapshot differences](documentation/historical_industry_bulletin_differences.csv) are included. Select event_id before joining classifications to price data on instrument_id. No original price, market, instrument or metadata dataset changed.
