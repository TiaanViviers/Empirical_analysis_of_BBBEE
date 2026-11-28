"""Portable inventories and deterministic artifact metadata."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

from .ingest import sha256


def write_json(path: Path, value: Any) -> None:
    pending = path.with_suffix(".pending.json")
    pending.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False, default=str)+"\n")
    pending.replace(path)


def processing_clock() -> dict[str, str]:
    now = datetime.now(timezone.utc)
    return {"processed_at_utc": now.isoformat(),
            "processing_date": now.astimezone(ZoneInfo("Africa/Johannesburg")).date().isoformat(),
            "processing_timezone": "Africa/Johannesburg"}


def schema_inventory(schema: pa.Schema) -> list[dict[str, Any]]:
    return [{"name": f.name, "type": str(f.type), "nullable": f.nullable,
             "description": (f.metadata or {}).get(b"description",b"").decode()}
            for f in schema]


def dataset_inventory(path: Path, con: duckdb.DuckDBPyConnection) -> dict[str, Any]:
    schema = pq.read_schema(path)
    key = "index_id" if path.name == "market_index.parquet" else "instrument_id"
    count, distinct = con.execute(
        f"SELECT count(*),count(DISTINCT {key}) FROM read_parquet(?)", [str(path)]).fetchall()[0]
    date_column = "date" if "date" in schema.names else "observed_price_start"
    end_column = "date" if "date" in schema.names else "observed_price_end"
    start, end = con.execute(
        f"SELECT min({date_column}),max({end_column}) FROM read_parquet(?)", [str(path)]).fetchall()[0]
    return {"filename": path.name, "rows": count, "unique_instruments": distinct,
            "date_start": str(start) if start else None, "date_end": str(end) if end else None,
            "date_coverage_basis": "observed_price_coverage" if path.name == "instruments.parquet" else "date",
            "size_bytes": path.stat().st_size, "sha256": sha256(path),
            "columns": schema_inventory(schema)}


def implementation_fingerprint() -> dict[str, str]:
    return {p.name:sha256(p) for p in sorted(Path(__file__).parent.glob("*.py"))}
