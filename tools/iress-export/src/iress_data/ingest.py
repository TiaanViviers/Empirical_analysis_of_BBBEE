"""Stream each workbook to bounded Arrow chunks; retain every nonblank row."""

import hashlib
import json
import logging
import math
import re
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq
from openpyxl import load_workbook
from openpyxl.utils.datetime import from_excel

from .config import Config

LOG = logging.getLogger(__name__)
PARSER_VERSION = 1
COMPANY_COLUMNS = {"Mnemonic", "Company", "Date", "Close", "Number Of Trades", "Volume"}
INDEX_COLUMNS = {"Mnemonic", "Company", "Date", "Close", "High", "Low", "Open", "Volume"}
SCHEMA = pa.schema([
    ("instrument_id", pa.string()), ("company_name", pa.string()),
    ("date", pa.date32()), ("close_raw", pa.float64()),
    ("number_of_trades", pa.float64()), ("volume", pa.float64()),
    ("source_file", pa.string()), ("source_sheet", pa.string()),
    ("source_batch", pa.int16()), ("source_row", pa.int32()),
    ("parse_issues", pa.string()), ("unparsed_values", pa.string()),
])


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def parse_date(value: Any, epoch: datetime) -> date:
    if isinstance(value, datetime):
        if value.time() != datetime.min.time():
            raise ValueError(f"Non-midnight date: {value!r}")
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return parse_date(from_excel(value, epoch), epoch)
    if isinstance(value, str):
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y"):
            try:
                return datetime.strptime(value.strip(), fmt).date()
            except ValueError:
                pass
    raise ValueError(f"Unrecognised date: {value!r}")


def parse_number(value: Any) -> tuple[float | None, str | None]:
    """Only blank cells are missing; do not guess locale or sentinel meanings."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return None, None
    if isinstance(value, bool):
        return None, "invalid_numeric"
    try:
        number = float(value)
    except (ValueError, TypeError, OverflowError):
        return None, "invalid_numeric"
    return number, None if math.isfinite(number) else "nonfinite_numeric"


def ingest(path: Path, cfg: Config, force: bool = False) -> dict[str, Any]:
    cfg.intermediate.mkdir(parents=True, exist_ok=True)
    target = cfg.intermediate / f"{path.stem}.parquet"
    meta_path = target.with_suffix(".json")
    digest = sha256(path)
    if not force and meta_path.exists() and target.exists():
        meta = json.loads(meta_path.read_text())
        if (meta.get("source_sha256") == digest and meta.get("parser_version") == PARSER_VERSION
                and meta.get("parquet_sha256") == sha256(target)):
            LOG.info("Reusing verified intermediate: %s", path.name)
            return meta
    LOG.info("Streaming workbook: %s", path.name)
    match = re.fullmatch(r"jse_prices_(\d+)\.xlsx", path.name)
    batch = int(match[1]) if match else None
    workbook = load_workbook(path, read_only=True, data_only=False)
    staged = target.with_suffix(".pending.parquet")
    type_counts: dict[str, Counter[str]] = defaultdict(Counter)
    blank_rows = 0
    total = 0
    buffer: list[dict[str, Any]] = []
    try:
        if len(workbook.worksheets) != 1:
            raise ValueError(f"Expected one sheet, found {workbook.sheetnames}")
        sheet = workbook.active
        assert sheet is not None
        iterator = sheet.iter_rows(values_only=True)
        header = next(iterator, None)
        labels = [str(x).strip() if x is not None else "" for x in header or ()]
        # IRESS supports both Flat Data Table and OHLC layouts for the index.
        # Layout acceptance is separate from daily-frequency validation.
        layouts = (COMPANY_COLUMNS,) if batch is not None else (INDEX_COLUMNS, COMPANY_COLUMNS)
        if not any(len(labels) == len(layout) and set(labels) == layout for layout in layouts):
            raise ValueError(f"Unexpected headers: {labels}; expected one of {[sorted(x) for x in layouts]}")
        with pq.ParquetWriter(staged, SCHEMA, compression="zstd") as writer:
            for row_number, values in enumerate(iterator, 2):
                if all(v is None for v in values):
                    blank_rows += 1
                    continue
                row = dict(zip(labels, values, strict=True))
                for key, value in row.items():
                    type_counts[key][type(value).__name__] += 1
                if not isinstance(row["Mnemonic"], str) or not row["Mnemonic"].strip():
                    raise ValueError(f"Missing/invalid Mnemonic at source row {row_number}")
                if row["Company"] is not None and not isinstance(row["Company"], str):
                    raise ValueError(f"Invalid company name at source row {row_number}")
                issues = []
                unparsed = {}
                numbers = {}
                for source, dest in (("Close", "close_raw"), ("Volume", "volume"),
                                     ("Number Of Trades", "number_of_trades")):
                    number, problem = parse_number(row.get(source))
                    numbers[dest] = number
                    if problem:
                        issues.append(f"{dest}:{problem}")
                        unparsed[source] = repr(row.get(source))
                record = {
                    "instrument_id": row["Mnemonic"], "company_name": row["Company"],
                    "date": parse_date(row["Date"], workbook.epoch), **numbers,
                    "source_file": path.name, "source_sheet": sheet.title,
                    "source_batch": batch, "source_row": row_number,
                    "parse_issues": ";".join(issues),
                    "unparsed_values": json.dumps(unparsed, sort_keys=True) if unparsed else "",
                }
                buffer.append(record)
                total += 1
                if len(buffer) >= cfg.chunk_rows:
                    writer.write_table(pa.Table.from_pylist(buffer, schema=SCHEMA))
                    buffer.clear()
            if buffer:
                writer.write_table(pa.Table.from_pylist(buffer, schema=SCHEMA))
        if not total:
            raise ValueError("Workbook has no data rows")
        if sha256(path) != digest:
            raise ValueError("Source changed during ingestion; retry with a stable export")
        staged.replace(target)
        meta = {
            "source_file": path.name, "source_sha256": digest,
            "source_size_bytes": path.stat().st_size, "parser_version": PARSER_VERSION,
            "source_batch": batch, "sheet": sheet.title, "columns": labels,
            "source_types": {k: dict(v) for k, v in type_counts.items()},
            "rows": total, "blank_rows_skipped": blank_rows,
            "parquet_sha256": sha256(target),
        }
        pending_meta = meta_path.with_suffix(".pending.json")
        pending_meta.write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n")
        pending_meta.replace(meta_path)
        LOG.info("Completed %s: %s rows", path.name, f"{total:,}")
        return meta
    except Exception:
        staged.unlink(missing_ok=True)
        raise
    finally:
        workbook.close()
