"""Researcher-facing documentation generated from the validated release inventory."""

from typing import Any

from .config import EVENTS
from .schemas import DATASET_SCHEMAS

PURPOSES={
    "prices_daily.parquet":"Complete canonical source panel, including financial placeholders",
    "prices_observed.parquet":"Exact subset with at least one reported numeric financial value",
    "instruments.parquet":"All extracted instruments and descriptive coverage/provenance",
    "market_index.parquet":"Observed daily FTSE/JSE All Share levels with an explicit gap flag",
    "observation_lineage.parquet":"Every original company Excel row, including identical copies",
}
PRIMARY_KEYS={
    "prices_daily.parquet":["instrument_id","date"],
    "prices_observed.parquet":["instrument_id","date"],
    "instruments.parquet":["instrument_id"],
    "market_index.parquet":["index_id","date"],
    "observation_lineage.parquet":["source_file","source_sheet","source_row"],
}
LIMITATIONS=[
    "Price units and source corporate-action adjustments have not been independently verified; no unit conversion or return adjustment was applied.",
    "The exact IRESS J203 price-versus-total-return variant remains unverified.",
    "A mnemonic is not a verified permanent security or issuer identifier; distinct share classes and source IDs remain separate.",
    "Actual listing/delisting/suspension histories, ISINs, issuer mappings and historical sectors are unavailable.",
    "A complete observed date calendar contains placeholders and does not establish historical listing status.",
    "Unchanged closes, zero volume, extreme changes and stale-price flags do not by themselves identify valid economic returns or errors.",
    "The source universe has not been reconciled against an authoritative dated identifier list; survivorship-bias freedom is not established.",
    "All policy event dates are provisional. No final event-specific eligibility, abnormal returns, CAR/CAAR, regressions or policy effects were estimated.",
    "Full-period instrument coverage is descriptive and must not determine earlier historical eligibility or characteristics.",
    "The calendar is the observed company-date union, corroborated by daily J203 except documented gaps; no independent official exchange-calendar reconciliation has been completed.",
]


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    def cell(x: Any) -> str:
        return str(x if x is not None else "unknown").replace("|"," / ")
    return "\n".join(["| "+" | ".join(headers)+" |","| "+" | ".join("---" for _ in headers)+" |",
                       *["| "+" | ".join(cell(x) for x in r)+" |" for r in rows]])


def readme(manifest: dict[str,Any]) -> str:
    v=manifest["validation"]
    datasets=manifest["datasets"]
    missing=manifest["market_index"]["missing_company_dates"]
    overview=md_table(["File","Rows","Distinct instruments/indexes","Coverage","Primary key"],[
        [f"[data/{name}](data/{name})",f"{entry['rows']:,}",f"{entry['unique_instruments']:,}",
         f"{entry['date_start']} to {entry['date_end']}",", ".join(PRIMARY_KEYS[name])]
        for name,entry in datasets.items()])
    events=md_table(["Proposed event","Working date"],[[name,d] for _,name,d in EVENTS])
    market_events=md_table(["Event date","Market estimation returns / 221","Market -10:+10 returns / 21","Required market closes complete"],
        [[r["event_date"],r["available_estimation_returns"],r["available_visualisation_returns"],r["all_required_benchmark_sessions_present"]]
         for r in manifest["market_event_coverage"]])
    stale_pct=100*v["potential_stale_price_observations"]/max(v["valid_price_observations"],1)
    zero_pct=100*v["empty_placeholders"]/max(v["canonical_rows"],1)
    return f"""# IRESS JSE historical data: thesis research handover

Data version **{manifest['dataset_version']}**. This package contains validated research source data for the Stellenbosch University economics thesis on the efficiency/equity trade-off associated with B-BBEE and Employment Equity policies. It supports **Part A: the JSE stock-market event study**, to be analysed by Monique and subsequent researchers. It contains no estimated policy effects.

## A. Background and scope

IRESS Expert Comparison exports were collected daily for the requested period 1 January 2016–31 March 2026. Actual company observation dates run from **{datasets['prices_daily.parquet']['date_start']} to {datasets['prices_daily.parquet']['date_end']}**, across **{v['calendar_sessions']:,} observed company-calendar sessions**. The extraction included historical instruments to retain potentially relevant delisted securities, rather than restricting the source to currently trading firms. This does not establish a survivorship-bias-free universe.

The five planned events are:

{events}

**These dates remain provisional.** Official announcement dates, times and trading-session alignment require verification before analysis. The working design uses estimation return dates -250:-30 inclusive (221 dates), event windows [0,+1], [-1,+3] and [0,+5], anticipation [-10,-1], and a visualisation window [-10,+10]. A return at the start of a window also needs the previous session's close.

## B. Dataset overview

{overview}

Coverage for the instrument master describes observed positive-price coverage across the master, not a date column or listing history. All instruments, including entirely empty histories, remain in the master. Physical company/lineage order is instrument, date, and then original source order where applicable; the benchmark is ordered by date. Sorting is a storage convention, not evidence that every row is a usable return.

- **prices_daily** preserves every unique extracted instrument-date, including placeholders, zeros, inactive histories and flagged observations.
- **prices_observed** has precisely the same columns and values, retaining only rows where close, volume or trade count is numerically non-null. **Numeric zero is an observed value.** It is reproducible from the full table using that predicate.
- **instruments** supplies one descriptive record per original mnemonic, with all source batches/files and unknown identifiers represented as nulls.
- **market_index** preserves the reported J203 levels with provenance and adjacency flags. Its missing dates are documented below.
- **observation_lineage** retains every original company source row. Each full-panel key has one canonical source and potentially several identical source copies.

**Neither price table is the final econometric sample.** {v['instruments_with_valid_prices']:,} instruments have at least one finite positive close; {v['instruments_with_positive_volume']:,} ever report positive volume. The compact table also retains zero-only financial histories. An instrument is not necessarily a distinct company.

Other package files:

- [documentation/data_dictionary.md](documentation/data_dictionary.md): exhaustive fields, exact Arrow types, nullability, units and flag definitions.
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

`potential_stale_price` requires a valid close, no positive current volume, and either an unchanged valid adjacent close or a trailing constant run of at least {manifest['configuration']['stale_run']} sessions. This is a diagnostic convention, not an exclusion or proof of staleness. No future observation determines this flag.

`diagnostic_price_return` is `current / previous - 1` only for finite positive closes on immediately adjacent full-calendar sessions. `extreme_price_change` is true when its absolute value is **strictly greater than {manifest['configuration']['extreme_threshold']:.0%}**; it is null if the return cannot be formed. `has_valid_adjacent_price` and its complement `missing_or_invalid_adjacent_observation` expose unavailable pairs, including the first row. `previous_price_date`/`price_gap_sessions` expose the nearest earlier valid price, but **a price across a gap is never used for an ordinary daily diagnostic return**.

Flags use rule version `{manifest['quality_rule_version']}`. Full-period coverage fields and `calendar_complete` are descriptive inventory properties. They must not determine historical eligibility using future information.

## D. Important data quirks and limitations

### 1. Empty observations

There are **{v['empty_placeholders']:,} entirely blank financial rows ({zero_pct:.2f}% of the canonical panel)**. {v['instruments_with_no_valid_prices']:,} instruments have no positive price, and {v['instruments_all_fields_missing']:,} have no reported financial values at all. Complete placeholder calendars are not proof that securities were listed throughout 2016–2026.

### 2. Stale or unchanged prices

The source includes long constant-price histories, often with zero volume. The approved trailing rule flags **{v['potential_stale_price_observations']:,} positive-price rows ({stale_pct:.2f}% of valid prices)**. There are {v['unchanged_adjacent_price_observations']:,} unchanged adjacent valid-price pairs. These are not automatically genuine zero economic returns. Phase 1's full-run descriptive stale count can differ because it used later observations to describe entire runs; final row flags use trailing information only.

### 3. Multiple securities per company

Ordinary shares, preference shares, historical identifiers and other classes may coexist. Source labels can match across different IDs; matching names are not sufficient grounds to merge them. No verified issuer-level mapping exists. `isin`, `issuer_id`, `security_type` and `sector_code` in the master remain unknown.

### 4. Historical listings

`observed_price_start/end` and positive-volume dates describe available source data. **They are not actual listing or delisting dates.** The actual `listing_date` and `delisting_date` fields remain null. Suspensions and off-market or inactive histories require separate evidence.

### 5. Corporate actions and unusual prices

The data retains **{v['zero_close_observations']:,} zero closes** and **{v['extreme_price_changes']:,} extreme diagnostic changes**. Some discontinuities may reflect splits, consolidations, dividends, distributions, rights issues, identifier changes or source errors. The preprocessing did not systematically adjust for corporate actions, and the adjustment basis of the source Close field remains unverified. Nothing was clipped or repaired from price ratios alone.

### 6. Price units

Many equity values appear consistent with JSE cents, but units have not been formally verified. **Do not silently convert to ZAR.** The benchmark's `units` and `return_variant` are null pending provider confirmation. Comparability of equity and market return methodology also requires review.

### 7. Returns

This is not a verified dividend-adjusted or total-economic-return dataset. Raw diagnostic changes must not silently become the thesis return series. Review provider definitions, corporate-action histories and treatment of dividends, illiquidity and terminal prices first.

Do not compute a one-day return with a simple grouped `shift()` on `prices_observed`: removing placeholder rows can hide multi-session gaps. Use the full calendar and validate both endpoints. Stored diagnostic returns were computed before forming the compact subset.

### 8. J203 missing observation

The benchmark contains **{v['market_rows']:,} observed daily levels**. Missing company-calendar session dates: **{', '.join(missing) if missing else 'none'}**. In the supplied thesis sources, the gap is 2 January 2024; company trading is recorded that day. No index value was interpolated. The following index observation, 3 January 2024, has `is_adjacent_to_previous_session=false`, preventing a multi-session change from being treated as daily.

Benchmark coverage for each planned event is checked separately:

{market_events}

A gap outside the required windows does not invalidate complete market-paired windows. This establishes data availability, not an approved final company sample or return methodology.

### 9. Identical duplicates

**{v['raw_source_rows']:,} original company rows became {v['canonical_rows']:,} unique keys by reducing {v['identical_duplicate_extra_rows']:,} identical extra copies.** There were no conflicting source values. Canonical order is filename, worksheet, then Excel row. The original thesis extraction overlaps were Interhold (`ITH:XJSE:EQU`) and Interleisure (`ITL:XJSE:EQU`) in batches 9 and 10. Every copy remains in lineage, including the chosen copy; `duplicate_copy_count` includes it. A conflicting key stops a future build.

### 10. Possible extraction omissions

The source screener later reported 1,872 results, while the audited extraction has 1,869 distinct IDs and 1,871 batch-level appearances. Batch 13 has 99 IDs. The manifest's purported missing “Pbt Group Limited” requires reconciliation: `PBT:XJSE:EQU` is actually present as “Pbt Holdings Limited.” Counts and name discrepancies do not identify omitted securities without a dated authoritative identifier snapshot. Universe completeness and survivorship-bias freedom remain unverified.

### 11. Historical classifications

Verified historical sectors, ISIN mappings, issuer relationships and listing histories are absent. A current classification must not be applied retrospectively without appropriate historical evidence. Enrichment needs effective dates and publication/availability dates, including statement revisions and vintages.

## E. Processing decisions

Performed: date parsing and consistent names/types; exact preservation of original mnemonics, company labels and numeric values; exact integral quantity conversion; deterministic identical-copy reduction; full original-row lineage; retention of all canonical placeholders; trailing-only diagnostics; creation of the numeric-observed subset; benchmark calendar validation; and schema/value/count/checksum validation.

Not performed: company-level identity resolution, inferred security-type or historical-sector assignment, listing-date inference, dividend/split adjustment, currency conversion, price interpolation, winsorisation, missing-price filling, liquidity-based exclusion, event-study sample construction, abnormal-return estimation, CAR/CAAR, regressions or policy-effect analysis.

The source Excel workbooks and Playwright extraction automation were preserved. This portable package excludes them, browser profiles, authentication material, temporary intermediates and debugging artifacts. Source hashes refer to the separately retained originals; they are not credentials. Underlying source-data distribution permissions continue to apply.

## F. Loading, filtering and joining

Work from this directory, or adapt relative paths to where it is copied. Parquet loading does not require IRESS or rerunning extraction/preprocessing. Python needs `pyarrow`; R needs `arrow` and `dplyr`. Use explicit filenames because the five datasets have different schemas.

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
"""


MARKET_DESCRIPTIONS={
    "date":"Observed source index session date; the missing session is not synthesized.",
    "index_id":"Original IRESS index mnemonic, J203:XJSE:IND.",
    "index_name":"Original source index name.",
    "close_raw":"Reported numeric index level; source return methodology remains unverified.",
    "source_file":"Original index workbook filename.",
    "source_sheet":"Original index worksheet name.",
    "source_row":"Original Excel row, including header row 1.",
    "source_sha256":"SHA-256 of the original index workbook.",
    "frequency":"daily, after identity, frequency, uniqueness and level checks.",
    "return_variant":"Unknown/null until price-versus-total-return methodology is verified.",
    "units":"Unknown/null pending provider definition.",
    "has_valid_price":"Finite strictly positive reported level.",
    "previous_observed_date":"Previous index source observation, which may precede a missing session.",
    "is_adjacent_to_previous_session":"True only when the previous index observation is the immediately preceding full company-calendar session; false after a gap and on the first row.",
    "calendar_complete":"Whether the full-period observed company calendar is covered. Descriptive global metadata, not historical eligibility.",
}


def units(name: str, filename: str) -> str:
    if name=="close_raw":
        return "Unverified source quote/level units; no conversion"
    if name=="diagnostic_price_return":
        return "Fractional raw price change; 0.30 means 30%"
    if name=="valid_price_coverage_pct":
        return "Percent of observed calendar sessions"
    if name=="volume":
        return "Reported source volume; provider unit definition unverified"
    if name in ("price_gap_sessions","trailing_constant_price_sessions","calendar_sessions"):
        return "Observed company-calendar sessions"
    if "date" in name or name.endswith(("_start","_end")):
        return "Native date (no time-of-day)" if name not in ("quality_rule_version",) else "Not applicable"
    if name in ("number_of_trades","source_row","canonical_source_row","copy_rank","duplicate_copy_count") or name.endswith(("observations","rows")):
        return "Count / row position as defined"
    return "Not applicable"


def data_dictionary(manifest: dict[str,Any]) -> str:
    sections=["# Exhaustive data dictionary",
        "Schemas below are taken from the final Parquet inventory. The two company price files have identical schemas. "
        "A nullable field can contain null; this differs from a numeric zero. Non-nullable fields are enforced during verification. "
        "All original numeric values are retained, including zeros and flagged values. Unknown metadata is represented by null, not guessed from names."]
    for filename in ("prices_daily.parquet","instruments.parquet","market_index.parquet","observation_lineage.parquet"):
        title=filename+" and prices_observed.parquet" if filename=="prices_daily.parquet" else filename
        sections.extend([f"## {title}",PURPOSES[filename]+". Primary key: `"+", ".join(PRIMARY_KEYS[filename])+"`."])
        entries=manifest["datasets"][filename]["columns"]
        schema=DATASET_SCHEMAS[filename]
        rows=[]
        for entry in entries:
            name=entry["name"]
            description=entry.get("description") or MARKET_DESCRIPTIONS.get(name) or (
                (schema.field(name).metadata or {}).get(b"description",b"").decode())
            rows.append([f"`{name}`",f"`{entry['type']}`","yes" if entry["nullable"] else "no",units(name,filename),description])
        sections.append(md_table(["Column","Arrow type","Nullable","Units","Definition and caveat"],rows))
    sections.extend(["## Missing values and derivations",
        "Parsed blank financial cells remain null. Explicit numeric zero is preserved and counts as an observed financial value. "
        "A missing close alone sets is_missing_price; invalid_price separately identifies zero, negative, nonfinite or unparsed closes. "
        "has_valid_price is numerical validity only. Boolean unchanged/extreme flags are null when their adjacent comparison cannot be made; they are not silently set to false. "
        "Unparseable source numeric tokens, if any, remain in unparsed_values/parse_issues alongside the parsed numeric null. The supplied audited inputs contain no numeric parsing issues.",
        f"Quality rule version: `{manifest['quality_rule_version']}`. Trailing constant-price threshold: {manifest['configuration']['stale_run']} sessions. "
        f"Extreme raw-change threshold: strict absolute change >{manifest['configuration']['extreme_threshold']}. "
        "Diagnostics use the full observed company-session calendar and immediately adjacent valid positive prices. "
        "No forward fill, unit conversion, dividend/split adjustment, clipping or extrapolation is performed.",
        "## Relationships and cardinality",
        "prices_daily → instruments is many-to-one on instrument_id. prices_observed is an exact row subset of prices_daily. "
        "prices_daily → observation_lineage is one-to-many on instrument_id,date; is_canonical selects exactly one original copy. "
        "Company prices → market_index is many-to-one on date for the single J203 ID, with unmatched dates retained explicitly. "
        "Instrument IDs are not issuer IDs. Source files may have source labels repeated across historical dates; these do not establish name validity at each date."])
    return "\n\n".join(sections)+"\n"


def processing_summary(manifest: dict[str,Any]) -> str:
    v=manifest["validation"]
    rows=[[key,f"{v[key]:,}"] for key in (
        "raw_source_rows","canonical_rows","identical_duplicate_extra_rows","conflicting_keys",
        "empty_placeholders","observed_rows","unique_instruments","calendar_sessions",
        "valid_price_observations","positive_volume_observations","zero_close_observations",
        "zero_volume_observations","diagnostic_price_returns","unchanged_adjacent_price_observations",
        "potential_stale_price_observations","extreme_price_changes","market_rows")]
    reference=manifest.get("reference_reconciliation",{})
    legacy=reference.get("phase1_potential_stale_prices")
    return "\n\n".join([
        "# Processing and validation summary",
        f"Dataset version {manifest['dataset_version']}; configuration {manifest['configuration_version']}; quality rules {manifest['quality_rule_version']}. "
        "The processing date and exact source/software/code fingerprints are recorded in manifest.json. All paths in the package are relative.",
        md_table(["Measured quantity","Final count"],rows),
        "## Approved transformations",
        "1. Reuse only source-hash and intermediate-hash verified streaming XLSX imports. Retain exact mnemonic/name spellings, source numeric values and nulls.\n"
        "2. Compare all meaningful values on repeated instrument/date keys. Stop on any conflict. Reduce only identical copies, selecting filename, worksheet, then source-row order. Retain all source copies in lineage.\n"
        "3. Validate that volume/trade counts are finite, integral and within Int64 range before conversion. Never round fractional values or convert blanks to zero. Negative integral values, if supplied, are preserved and flagged.\n"
        "4. Keep all unique instrument-date keys and financial placeholders. Derive the compact table using close IS NOT NULL OR volume IS NOT NULL OR number_of_trades IS NOT NULL.\n"
        "5. Process one chronologically ordered instrument stream with bounded Arrow chunks. Use only earlier/current observations for diagnostic flags; no return bridges a missing/invalid session.\n"
        "6. Build descriptive instrument coverage and preserve all original batch/file provenance. Leave unverified identity/classification/listing fields null.\n"
        "7. Preserve the existing J203 implementation and source levels. Keep the missing session absent and mark the next observed row as non-adjacent.\n"
        "8. Validate all files before installing the build manifest; create the portable package only from validated outputs.",
        "## Phase 1 versus final stale-price definitions",
        (f"Phase 1 described full constant-price runs and flagged {legacy:,} potential-stale rows. " if legacy is not None else "Phase 1 used descriptive full-run diagnostics. ")+
        f"The final trailing-only rule flags {v['potential_stale_price_observations']:,} rows. "
        "A run's first row cannot be flagged merely because later prices remain constant. This intentional difference prevents future information from entering row flags; it changes no source value and removes no observation.",
        "## Verification performed",
        "The full private-project verifier reads every Parquet page, validates schemas and non-nullability, canonical/master uniqueness, "
        "original-copy ranks, selected source ordering, every source-row lineage link, source and output hashes, null/value preservation, "
        "exact compact-subset equality including multiplicities, master coverage and unknown metadata, independent SQL reconstructions of trailing flags, "
        "and benchmark identity/values/calendar flags. Original XLSX files are checked against their before-build hashes. "
        "The audited reference counts are enforced when the audited source inventory matches; conflicting sources stop the build.",
        "## Reproducibility",
        "For fixed source workbooks, processing code/configuration and locked dependencies, the five Parquet datasets and generated documentation "
        "have deterministic contents and ordering. Processing/package timestamps intentionally change and therefore manifest bytes/checksums can change. "
        "manifest.json identifies this metadata variability separately from dataset checksums. The package verifier is self-contained and does not import preprocessing code or read original source workbooks.",
        "The retained preprocessing repository provides `uv run python -m iress_data build`, `verify`, `package`, `verify-package` and `release` "
        "(build plus validated packaging). The existing `audit` and Playwright extraction commands remain available there. "
        "Researchers only loading this handover do not need that repository, the raw exports, a browser session or IRESS credentials.",
        "## Source provenance",
        "Source workbook filenames, SHA-256 digests, row counts, worksheet names, headers and observed cell types appear in "
        "documentation/source_inventory.json and the manifest. Each canonical company record points to its selected source file/sheet/row/hash. "
        "observation_lineage preserves the same information for every original company row, including duplicate copies. "
        "Market records carry their original row references and workbook hash. The original licensed files remain in the private extraction project.",
    ])+"\n"


def known_limitations(manifest: dict[str,Any]) -> str:
    missing=manifest["market_index"]["missing_company_dates"]
    return "\n\n".join(["# Known limitations and unresolved research decisions",
        "These limits remain after successful source preservation and technical validation. They do not justify undocumented repairs or automatic sample exclusions.",
        "\n".join(f"{i}. {text}" for i,text in enumerate(LIMITATIONS,1)),
        f"Documented benchmark missing sessions: {', '.join(missing) if missing else 'none'}. "
        "The supplied thesis benchmark lacks 2024-01-02, while all five current planned estimation/event windows are fully covered. "
        "Obtain and verify missing source observations separately; do not interpolate or bridge a gap.",
        "The original screener count and PBT name discrepancy require an identifier-level reconciliation, not name-based merging. "
        "Interhold/Interleisure identical overlaps were reduced deterministically with all copies in lineage. "
        "Preference-share-looking labels and the provider EQU suffix are insufficient verification of security class.",
        "Prioritise provider quote/adjustment definitions and corporate actions, dated identifier/issuer/security-class histories, actual listing and suspension histories, "
        "historical sectors, dated financial statements/market values and B-BBEE/EE exposure. Keep effective and publication/availability dates separately. "
        "Verify policy announcement dates and times before choosing session zero. Final liquidity/completeness criteria and event-specific samples belong to the later research layer.",
    ])+"\n"
