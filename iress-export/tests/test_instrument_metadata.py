"""Dated Screener metadata transformation and integrity checks."""

from __future__ import annotations

import csv
from pathlib import Path
import shutil
import tempfile

import pyarrow.parquet as pq
import pytest

from iress_data.instrument_metadata import process_metadata, valid_isin


ROOT = Path(__file__).resolve().parents[1]


def test_isin_format_and_check_digit() -> None:
    assert valid_isin("US0378331005")
    assert valid_isin("ZAE000102026")
    assert not valid_isin("US0378331004")
    assert not valid_isin("ABC")
    assert not valid_isin("")
    assert not valid_isin(None)


def test_transform_preserves_source_and_reconciles(tmp_path: Path) -> None:
    csv_path = ROOT / "metadata/jse_screener_snapshot.csv"
    summary = ROOT / "metadata/jse_screener_snapshot.summary.json"
    master = ROOT / "data/processed/instruments.parquet"
    output = tmp_path / "instrument_metadata_2026-11-23.parquet"
    metrics = process_metadata(csv_path, summary, master, output)
    rows = pq.read_table(output).to_pylist()
    assert metrics["rows"] == len(rows) == len({r["instrument_id"] for r in rows}) == 1872
    assert metrics["valid_isins"] == sum(r["isin_valid"] for r in rows) == 1492
    assert sum(r["has_historical_prices_record"] for r in rows) == 1869
    assert {r["instrument_id"] for r in rows if not r["has_historical_prices_record"]} == {
        "IMRP17:XJSE:EQU", "IMRP18:XJSE:EQU", "PBT_DEL:XJSE:EQU",
    }
    with csv_path.open(newline="", encoding="utf-8") as f:
        source_rows = list(csv.DictReader(f))
    assert [r["instrument_id"] for r in rows] == [r["instrument_id"] for r in source_rows]
    assert [r["isin_raw"] for r in rows] == [r["isin"] for r in source_rows]
    assert [r["company_name"] for r in rows] == [r["company_name"] for r in source_rows]
    assert all(r["snapshot_date"].isoformat() == "2026-11-23" for r in rows)


def test_source_csv_checksum_guard(tmp_path: Path) -> None:
    changed_csv = tmp_path / "changed.csv"
    shutil.copy2(ROOT / "metadata/jse_screener_snapshot.csv", changed_csv)
    changed_csv.write_text(changed_csv.read_text() + "\n")
    with pytest.raises(ValueError, match="checksum"):
        process_metadata(changed_csv,
                         ROOT / "metadata/jse_screener_snapshot.summary.json",
                         ROOT / "data/processed/instruments.parquet",
                         tmp_path / "out.parquet")
