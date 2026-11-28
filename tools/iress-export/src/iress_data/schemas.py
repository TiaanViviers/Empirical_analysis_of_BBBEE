"""Versioned analytical schemas, shared by writers, validation and documentation."""

import pyarrow as pa

from .benchmark import MARKET_SCHEMA

DATA_VERSION = "1.0.0"
QUALITY_RULE_VERSION = "trailing-1.0.0"
CONFIGURATION_VERSION = "conservative-source-1.0.0"


def field(name: str, dtype: pa.DataType, description: str, nullable: bool = True) -> pa.Field:
    return pa.field(name, dtype, nullable=nullable, metadata={"description": description})


S, I, B, D, F = pa.string(), pa.int64(), pa.bool_(), pa.date32(), pa.float64()
PRICE_SCHEMA = pa.schema([
    field("date", D, "Observed source session date; no generated dates.", False),
    field("instrument_id", S, "Original IRESS Mnemonic; not a permanent issuer identifier.", False),
    field("ticker", S, "Mnemonic prefix only when the full identifier matches ticker:XJSE:EQU."),
    field("company_name", S, "Original source label; not independently verified historical name."),
    field("close_raw", F, "Reported numeric close; units and adjustment basis unverified."),
    field("volume", I, "Reported volume; integer conversion validated without rounding; null differs from zero."),
    field("number_of_trades", I, "Reported trade count; integer conversion validated without rounding."),
    field("source_batch", pa.int16(), "Canonical source company workbook number.", False),
    field("source_file", S, "Canonical original workbook filename.", False),
    field("source_sheet", S, "Canonical original worksheet name.", False),
    field("source_row", pa.int32(), "Canonical original Excel row; header is row 1.", False),
    field("source_sha256", S, "SHA-256 of the canonical original workbook.", False),
    field("duplicate_copy_count", pa.int32(), "Number of source copies, including the canonical copy.", False),
    field("has_valid_price", B, "Close is finite and strictly positive; not proof of active trading.", False),
    field("is_missing_price", B, "Parsed close is null.", False),
    field("is_zero_price", B, "Reported close is explicitly numeric zero.", False),
    field("is_negative_price", B, "Reported close is finite and negative.", False),
    field("is_nonfinite_price", B, "Reported close is NaN or infinity.", False),
    field("invalid_price", B, "Non-null close is nonpositive/nonfinite, or close has a parse issue; missing alone is separate.", False),
    field("has_positive_volume", B, "Reported volume is strictly positive.", False),
    field("is_zero_volume", B, "Reported volume is explicitly zero.", False),
    field("is_missing_volume", B, "Reported volume is null.", False),
    field("is_negative_volume", B, "Reported volume is negative; retained unchanged.", False),
    field("is_missing_trade_count", B, "Reported number_of_trades is null.", False),
    field("is_negative_trade_count", B, "Reported number_of_trades is negative; retained unchanged.", False),
    field("is_empty_placeholder", B, "All three financial fields null and no numeric parse issue.", False),
    field("numeric_parse_issue", B, "At least one source financial field has a parsing/nonfinite issue.", False),
    field("parse_issues", S, "Semicolon-separated source parsing issue codes; empty string means none.", False),
    field("unparsed_values", S, "Original problematic tokens encoded as JSON, or empty string.", False),
    field("previous_observed_date", D, "Previous canonical row date for the same instrument; may have blank financial fields."),
    field("previous_price_date", D, "Nearest earlier finite positive close date, even across gaps; never a listing date."),
    field("price_gap_sessions", pa.int32(), "Current session position minus nearest earlier valid-price position; null if none."),
    field("is_adjacent_to_previous_session", B, "Previous canonical row is the immediately preceding full-calendar session.", False),
    field("has_valid_adjacent_price", B, "Current and immediately preceding session both have finite positive closes.", False),
    field("missing_or_invalid_adjacent_observation", B, "Complement of has_valid_adjacent_price, including each series' first row.", False),
    field("unchanged_adjacent_price", B, "Equality of adjacent valid positive closes; null if the pair is unusable; not a verified zero economic return."),
    field("trailing_constant_price_sessions", pa.int32(), "Consecutive equal positive closes through this date only; 1 on first valid price, 0 on missing/invalid price.", False),
    field("potential_stale_price", B, "Valid close with no positive current volume and either unchanged adjacent close or trailing run >= configured threshold; diagnostic only.", False),
    field("extreme_price_change", B, "Absolute diagnostic raw price change strictly exceeds configured threshold (0.30); null without a usable adjacent pair."),
    field("diagnostic_price_return", F, "close_raw / immediately previous session close - 1; only finite positive adjacent pairs; unverified economic interpretation."),
    field("quality_rule_version", S, "Version binding all derived flags to the processing rules.", False),
])

LINEAGE_SCHEMA = pa.schema([
    field("instrument_id", S, "Canonical observation instrument key.", False),
    field("date", D, "Canonical observation date key.", False),
    field("source_batch", pa.int16(), "Original workbook batch, including secondary duplicate copies.", False),
    field("source_file", S, "Original workbook filename.", False),
    field("source_sheet", S, "Original worksheet name.", False),
    field("source_row", pa.int32(), "Original Excel row, counting the header as row 1.", False),
    field("source_sha256", S, "SHA-256 of this source workbook.", False),
    field("copy_rank", pa.int32(), "1-based order by filename, sheet, source row within the instrument-date.", False),
    field("duplicate_copy_count", pa.int32(), "Total original copies of the instrument-date, including the canonical one.", False),
    field("is_canonical", B, "True exactly for copy_rank=1.", False),
    field("canonical_source_file", S, "Selected canonical workbook filename.", False),
    field("canonical_source_sheet", S, "Selected canonical worksheet name.", False),
    field("canonical_source_row", pa.int32(), "Selected canonical Excel source row.", False),
])

INSTRUMENT_SCHEMA = pa.schema([
    field("instrument_id", S, "Original IRESS Mnemonic; includes empty histories and distinct share classes.", False),
    field("ticker", S, "Syntactically parsed mnemonic prefix, not a permanent identifier."),
    field("company_name", S, "First source label ordered by source file, sheet and row; not issuer identity."),
    field("company_names", pa.list_(S), "Sorted distinct observed source labels.", False),
    field("observed_price_start", D, "First finite positive source close; not listing date."),
    field("observed_price_end", D, "Last finite positive source close; not delisting date."),
    field("observed_positive_volume_start", D, "First positive reported volume date; not listing date."),
    field("observed_positive_volume_end", D, "Last positive reported volume date; not delisting date."),
    field("total_observations", I, "Canonical rows including placeholders.", False),
    field("reported_financial_observations", I, "Canonical rows with at least one non-null numeric financial field.", False),
    field("valid_price_observations", I, "Finite positive closing-price rows.", False),
    field("positive_volume_observations", I, "Strictly positive reported-volume rows.", False),
    field("missing_price_observations", I, "Rows whose parsed close is null; zero/negative prices are separate.", False),
    field("calendar_sessions", I, "Size of the complete observed company-calendar union; coverage denominator.", False),
    field("valid_price_coverage_pct", F, "100 * valid_price_observations / calendar_sessions; full-period description, not eligibility.", False),
    field("raw_source_rows", I, "Original row count across all source copies.", False),
    field("duplicate_extra_rows", I, "raw_source_rows minus total_observations.", False),
    field("source_batches", pa.list_(pa.int16()), "All original source batch numbers, sorted, including duplicates.", False),
    field("source_files", pa.list_(S), "All original workbook filenames, sorted.", False),
    field("isin", S, "Unknown: no verified ISIN mapping supplied."),
    field("issuer_id", S, "Unknown: no verified instrument-to-issuer mapping supplied."),
    field("security_type", S, "Unknown: no classification inferred from name or EQU suffix."),
    field("sector_code", S, "Unknown: historical sector membership requires effective-dated enrichment."),
    field("listing_date", D, "Unknown: actual listing date requires independent source."),
    field("delisting_date", D, "Unknown: actual delisting date requires independent source."),
])

DATASET_SCHEMAS = {
    "prices_daily.parquet": PRICE_SCHEMA,
    "prices_observed.parquet": PRICE_SCHEMA,
    "instruments.parquet": INSTRUMENT_SCHEMA,
    "market_index.parquet": MARKET_SCHEMA,
    "observation_lineage.parquet": LINEAGE_SCHEMA,
}
