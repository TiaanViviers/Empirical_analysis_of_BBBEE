"""Preserve daily benchmark observations and expose gaps without interpolation."""

import json
from collections import Counter
from datetime import date
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from .config import Config, EVENTS
from .ingest import sha256
from .validation import valid_price

MARKET_SCHEMA = pa.schema([
    ("date", pa.date32()), ("index_id", pa.string()), ("index_name", pa.string()),
    ("close_raw", pa.float64()), ("source_file", pa.string()),
    ("source_sheet", pa.string()), ("source_row", pa.int32()),
    ("source_sha256", pa.string()), ("frequency", pa.string()),
    ("return_variant", pa.string()), ("units", pa.string()),
    ("has_valid_price", pa.bool_()), ("previous_observed_date", pa.date32()),
    ("is_adjacent_to_previous_session", pa.bool_()),
    ("calendar_complete", pa.bool_()),
])


def return_availability(records: list[dict[str, Any]], calendar: list[date]) -> list[bool]:
    """A missing session invalidates its own return and the following return."""
    counts = Counter(r["date"] for r in records)
    valid = {r["date"] for r in records if valid_price(r["close_raw"]) and counts[r["date"]] == 1}
    return [i > 0 and day in valid and calendar[i-1] in valid for i, day in enumerate(calendar)]


def market_event_coverage(calendar: list[date], available: list[bool] | None) -> list[dict[str, Any]]:
    rows = []
    for event_id, name, event_date in EVENTS:
        origin = next((i for i,d in enumerate(calendar) if d >= event_date), None)
        def day(offset: int) -> date | None:
            i = origin + offset if origin is not None else -1
            return calendar[i] if 0 <= i < len(calendar) else None
        def count(lo: int, hi: int) -> int | None:
            if available is None or origin is None:
                return None
            return sum(0 <= origin+j < len(calendar) and available[origin+j] for j in range(lo,hi+1))
        estimation_n = count(-250,-30)
        event_n = count(-10,10)
        rows.append({
            "event_id": event_id, "event_name": name, "event_date": event_date,
            "aligned_event_date": day(0), "estimation_first_required_close": day(-251),
            "estimation_start": day(-250), "estimation_end": day(-30),
            "visualisation_first_required_close": day(-11),
            "visualisation_start": day(-10), "visualisation_end": day(10),
            "expected_estimation_returns": 221, "available_estimation_returns": estimation_n,
            "expected_visualisation_returns": 21, "available_visualisation_returns": event_n,
            "all_required_benchmark_sessions_present": None if available is None else
                estimation_n == 221 and event_n == 21,
        })
    return rows


def write_market_source(cfg: Config, market: dict[str, Any]) -> dict[str, Any] | None:
    """No filtering/adjustment: publish observed valid daily levels with gap metadata."""
    destination = cfg.root / "data/processed/market_index.parquet"
    metadata_path = destination.with_suffix(".metadata.json")
    if not market.get("daily_frequency_validated", False):
        # Avoid leaving an obsolete daily artifact after replacement by invalid data.
        destination.unlink(missing_ok=True)
        metadata_path.unlink(missing_ok=True)
        return None
    records = pq.read_table(cfg.intermediate / "J203_prices.parquet").to_pylist()
    records.sort(key=lambda r: (r["date"],r["source_row"]))
    positions = {date.fromisoformat(d): i for i,d in enumerate(market["company_calendar_dates"])}
    output = []
    previous = None
    for r in records:
        current = r["date"]
        output.append({
            "date": current, "index_id": r["instrument_id"], "index_name": r["company_name"],
            "close_raw": r["close_raw"], "source_file": r["source_file"],
            "source_sheet": r["source_sheet"], "source_row": r["source_row"],
            "source_sha256": market["source_sha256"], "frequency": "daily",
            "return_variant": None, "units": None, "has_valid_price": valid_price(r["close_raw"]),
            "previous_observed_date": previous,
            "is_adjacent_to_previous_session": previous is not None and
                positions[current] == positions[previous]+1,
            "calendar_complete": market["calendar_complete"],
        })
        previous = current
    destination.parent.mkdir(parents=True, exist_ok=True)
    staged = destination.with_suffix(".pending.parquet")
    pq.write_table(pa.Table.from_pylist(output, schema=MARKET_SCHEMA), staged, compression="zstd")
    staged.replace(destination)
    metadata = {
        "path": str(destination.relative_to(cfg.root)), "rows": len(output),
        "sha256": sha256(destination), "source_sha256": market["source_sha256"],
        "daily_frequency_validated": True, "calendar_complete": market["calendar_complete"],
        "missing_session_dates": market["missing_company_dates"],
        "units": None, "return_variant": None,
        "transformations": "Sorted observed rows; no filling, exclusions, conversions or return adjustments",
        "status": market["status"],
    }
    pending_meta = metadata_path.with_suffix(".pending.json")
    pending_meta.write_text(json.dumps(metadata,indent=2,sort_keys=True)+"\n")
    pending_meta.replace(metadata_path)
    return metadata
