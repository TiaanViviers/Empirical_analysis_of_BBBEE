"""Approved conservative company processing, reusing streamed audit intermediates."""

import json
import logging
import platform
import shutil
from importlib.metadata import version
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any

import duckdb
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

from .artifacts import (dataset_inventory, implementation_fingerprint,
                        processing_clock, write_json)
from .audit import connect, create_views, index_audit, query_dicts, write_csv
from .benchmark import write_market_source
from .config import Config, END, START
from .ingest import ingest, sha256
from .schemas import (CONFIGURATION_VERSION, DATA_VERSION, INSTRUMENT_SCHEMA,
                      LINEAGE_SCHEMA, PRICE_SCHEMA, QUALITY_RULE_VERSION)
from .transform import transform_records

LOG = logging.getLogger(__name__)
DATASET_NAMES = ("prices_daily.parquet", "prices_observed.parquet", "instruments.parquet",
                 "market_index.parquet", "observation_lineage.parquet")
REFERENCE_COUNTS = {
    "raw_source_rows":4_789_760,"canonical_rows":4_784_640,"unique_instruments":1_869,
    "observed_rows":982_129,"empty_placeholders":3_802_511,"identical_duplicate_extra_rows":5_120,
    "conflicting_keys":0,"calendar_sessions":2_560,"valid_price_observations":980_974,
    "instruments_with_valid_prices":594,"instruments_with_positive_volume":495,
    "instruments_with_no_valid_prices":1_275,"zero_close_observations":1_155,
    "extreme_price_changes":3_566,"market_rows":2_559,
}


def stream_query(con: duckdb.DuckDBPyConnection, sql: str, size: int) -> Iterator[dict[str, Any]]:
    reader = con.sql(sql).to_arrow_reader(size)
    for batch in reader:
        yield from batch.to_pylist()


def write_query(con: duckdb.DuckDBPyConnection, sql: str, path: Path,
                schema: pa.Schema, chunk_rows: int) -> None:
    with pq.ParquetWriter(path, schema, compression="zstd") as writer:
        for batch in con.sql(sql).to_arrow_reader(chunk_rows):
            writer.write_batch(batch.cast(schema))


def validate_quantities(con: duckdb.DuckDBPyConnection) -> None:
    for name in ("volume", "number_of_trades"):
        examples = con.execute(f"""
            SELECT instrument_id,date,{name},source_file,source_row FROM raw
            WHERE {name} IS NOT NULL AND (NOT isfinite({name}) OR {name} != trunc({name})
                OR {name} >= 9223372036854775808 OR {name} < -9223372036854775808) LIMIT 5
        """).fetchall()
        if examples:
            raise ValueError(f"Cannot preserve {name} as Int64 without rounding/overflow: {examples}")


def write_prices(con: duckdb.DuckDBPyConnection, cfg: Config, stage: Path,
                 calendar: list[Any]) -> None:
    columns = "r.*,s.source_sha256,cast(coalesce(k.copies,1) AS INTEGER) duplicate_copy_count"
    query = f"""SELECT {columns} FROM diagnostic r JOIN source_inventory s USING(source_file)
                LEFT JOIN duplicate_keys k USING(instrument_id,date) ORDER BY r.instrument_id,r.date"""
    records = transform_records(stream_query(con, query, cfg.chunk_rows), calendar, cfg)
    with (pq.ParquetWriter(stage/"prices_daily.parquet", PRICE_SCHEMA, compression="zstd") as full,
          pq.ParquetWriter(stage/"prices_observed.parquet", PRICE_SCHEMA, compression="zstd") as observed):
        buffer = []
        total = 0
        def flush() -> None:
            nonlocal total
            table = pa.Table.from_pylist(buffer, schema=PRICE_SCHEMA)
            full.write_table(table)
            mask = pc.or_(pc.or_(pc.is_valid(table["close_raw"]), pc.is_valid(table["volume"])),
                          pc.is_valid(table["number_of_trades"]))
            selected = table.filter(mask)
            if selected.num_rows:
                observed.write_table(selected)
            total += len(buffer)
            buffer.clear()
        for row in records:
            buffer.append(row)
            if len(buffer) >= cfg.chunk_rows:
                flush()
                if total % 1_000_000 == 0:
                    LOG.info("Wrote %s canonical company observations", f"{total:,}")
        if buffer:
            flush()


def write_lineage(con: duckdb.DuckDBPyConnection, cfg: Config, stage: Path) -> None:
    query = """
        SELECT instrument_id,date,source_batch,source_file,source_sheet,source_row,source_sha256,
          cast(row_number() OVER w AS INTEGER) copy_rank,
          cast(count(*) OVER w AS INTEGER) duplicate_copy_count,
          row_number() OVER w=1 is_canonical,
          first_value(source_file) OVER w canonical_source_file,
          first_value(source_sheet) OVER w canonical_source_sheet,
          cast(first_value(source_row) OVER w AS INTEGER) canonical_source_row
        FROM raw JOIN source_inventory USING(source_file)
        WINDOW w AS (PARTITION BY instrument_id,date ORDER BY source_file,source_sheet,source_row
                     ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)
        ORDER BY instrument_id,date,source_file,source_sheet,source_row
    """
    write_query(con, query, stage/"observation_lineage.parquet", LINEAGE_SCHEMA, cfg.chunk_rows)


def write_instruments(con: duckdb.DuckDBPyConnection, stage: Path, calendar_size: int) -> None:
    con.read_parquet(str(stage/"prices_daily.parquet")).create_view("built_prices")
    rows = query_dicts(con, f"""
        WITH coverage AS (
          SELECT instrument_id,min(ticker) ticker,
            first(company_name ORDER BY source_file,source_sheet,source_row) company_name,
            list(DISTINCT company_name ORDER BY company_name) FILTER(WHERE company_name IS NOT NULL) company_names,
            min(date) FILTER(WHERE has_valid_price) observed_price_start,
            max(date) FILTER(WHERE has_valid_price) observed_price_end,
            min(date) FILTER(WHERE has_positive_volume) observed_positive_volume_start,
            max(date) FILTER(WHERE has_positive_volume) observed_positive_volume_end,
            count(*) total_observations,
            count(*) FILTER(WHERE close_raw IS NOT NULL OR volume IS NOT NULL OR number_of_trades IS NOT NULL) reported_financial_observations,
            count(*) FILTER(WHERE has_valid_price) valid_price_observations,
            count(*) FILTER(WHERE has_positive_volume) positive_volume_observations,
            count(*) FILTER(WHERE close_raw IS NULL) missing_price_observations,
            {calendar_size}::BIGINT calendar_sessions,
            100.0*count(*) FILTER(WHERE has_valid_price)/{calendar_size} valid_price_coverage_pct
          FROM built_prices GROUP BY instrument_id
        ), provenance AS (
          SELECT instrument_id,count(*) raw_source_rows,
            list(DISTINCT source_batch ORDER BY source_batch) source_batches,
            list(DISTINCT source_file ORDER BY source_file) source_files
          FROM raw GROUP BY instrument_id
        )
        SELECT *,raw_source_rows-total_observations duplicate_extra_rows
        FROM coverage JOIN provenance USING(instrument_id) ORDER BY instrument_id
    """)
    for row in rows:
        row["company_names"] = row["company_names"] or []
        row.update({k:None for k in ("isin","issuer_id","security_type","sector_code","listing_date","delisting_date")})
    pq.write_table(pa.Table.from_pylist(rows, schema=INSTRUMENT_SCHEMA), stage/"instruments.parquet", compression="zstd")


def build(cfg: Config) -> dict[str, Any]:
    """Stage a complete generation; a manifest is installed only after validation."""
    cfg.reports.mkdir(parents=True, exist_ok=True)
    expected = [cfg.exports/f"jse_prices_{i:02d}.xlsx" for i in range(1,cfg.expected_batches+1)]
    actual = set(cfg.exports.glob("jse_prices_*.xlsx"))
    if set(expected) != actual:
        raise ValueError(f"Company input inventory mismatch: missing={sorted(set(expected)-actual)}, unexpected={sorted(actual-set(expected))}")
    inputs = [ingest(path,cfg) for path in expected+[cfg.exports/"J203_prices.xlsx"]]
    company_inputs = [m for m in inputs if m["source_batch"] is not None]
    destination = cfg.root/"data/processed"
    stage = cfg.root/"data/.processed-build"
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)
    con = connect(cfg)
    try:
        create_views(con,[cfg.intermediate/f"{Path(m['source_file']).stem}.parquet" for m in company_inputs])
        conflict_count = con.execute("SELECT count(*) FROM duplicate_keys WHERE variants>1").fetchall()[0][0]
        conflict_query = """SELECT r.* FROM raw r JOIN duplicate_keys k USING(instrument_id,date)
                            WHERE k.variants>1 ORDER BY r.instrument_id,r.date,r.source_file,r.source_row"""
        fields = [f.name for f in pq.read_schema(cfg.intermediate/f"{Path(company_inputs[0]['source_file']).stem}.parquet")]
        write_csv(cfg.reports/"build_conflicting_observations.csv",
                  stream_query(con,conflict_query,cfg.chunk_rows),fields)
        if conflict_count:
            raise ValueError(f"Build stopped: {conflict_count} conflicting instrument-date keys; see reports/build_conflicting_observations.csv")
        validate_quantities(con)
        con.register("source_inventory",pa.Table.from_pylist([
            {"source_file":m["source_file"],"source_sha256":m["source_sha256"]} for m in company_inputs]))
        calendar = [r[0] for r in con.execute("SELECT DISTINCT date FROM raw ORDER BY date").fetchall()]
        LOG.info("Building canonical and observed prices; placeholders retained")
        write_prices(con,cfg,stage,calendar)
        LOG.info("Building complete original-row lineage")
        write_lineage(con,cfg,stage)
        write_instruments(con,stage,len(calendar))
        market = index_audit(cfg,inputs[-1],calendar,None)
        if not market.get("daily_frequency_validated"):
            raise ValueError(f"Daily benchmark is unsuitable: {market['status']}")
        # Preserve the existing implementation and, when unchanged, its exact bytes.
        benchmark_path = destination/"market_index.parquet"
        benchmark_meta_path = destination/"market_index.metadata.json"
        current = json.loads(benchmark_meta_path.read_text()) if benchmark_meta_path.exists() else {}
        if (not benchmark_path.exists() or current.get("source_sha256") != inputs[-1]["source_sha256"]
                or current.get("sha256") != sha256(benchmark_path)):
            from dataclasses import replace
            temp_root=stage/"benchmark_build"
            write_market_source(replace(cfg,root=temp_root),market)
            benchmark_path=temp_root/"data/processed/market_index.parquet"
            benchmark_meta_path=benchmark_path.with_suffix(".metadata.json")
        shutil.copy2(benchmark_path,stage/"market_index.parquet")
        shutil.copy2(benchmark_meta_path,stage/"market_index.metadata.json")
        if (stage/"benchmark_build").exists():
            shutil.rmtree(stage/"benchmark_build")
        inventory = {name:dataset_inventory(stage/name,con) for name in DATASET_NAMES}
        from .processed_validation import validate_tables
        checks = validate_tables(con,stage,calendar,source_view="raw",input_inventory=inputs,
                                 stale_run=cfg.stale_run,extreme_threshold=cfg.extreme_threshold)
        reference={"applied":False}
        audit_path=cfg.reports/"audit_summary.json"
        if cfg.expected_batches==19 and audit_path.exists():
            audit=json.loads(audit_path.read_text())
            before={s["source_file"]:s["source_sha256"] for s in audit["inputs"]}
            after={s["source_file"]:s["source_sha256"] for s in inputs}
            if before!=after:
                raise ValueError("Source inventory differs from audited references; investigate before final handover")
            expected=dict(REFERENCE_COUNTS)
            if cfg.extreme_threshold != .30:
                expected.pop("extreme_price_changes")
            for key,value in expected.items():
                if checks[key]!=value:
                    raise ValueError(f"Audited reference mismatch {key}: expected {value}, found {checks[key]}")
            reference={"applied":True,"audit_summary_sha256":sha256(audit_path),"expected":expected,
                       "phase1_potential_stale_prices":audit["diagnostic_totals"]["potential_stale_price"],
                       "event_coverage":audit["events"],"market_event_coverage":audit["market_event_coverage"],
                       "same_name_examples":audit["same_name_examples"],
                       "manifest_missing_name_candidates":audit["manifest_missing_name_candidates"]}
        for name in DATASET_NAMES:
            inventory[name]["dataset_version"] = DATA_VERSION
        summary = {
            "dataset_version":DATA_VERSION, "quality_rule_version":QUALITY_RULE_VERSION,
            "configuration_version":CONFIGURATION_VERSION, **processing_clock(),
            "implementation_sha256":implementation_fingerprint(),
            "software":{"python":platform.python_version(),**{name:version(name) for name in ("pyarrow","duckdb","openpyxl")}},
            "uv_lock_sha256":sha256(cfg.root/"uv.lock") if (cfg.root/"uv.lock").exists() else None,
            "configuration":{"stale_run":cfg.stale_run,"extreme_threshold":cfg.extreme_threshold,
                             "chunk_rows":cfg.chunk_rows,"duplicate_order":["source_file","source_sheet","source_row"],
                             "placeholder_policy":"retain_all","requested_start":START,"requested_end":END},
            "calendar":{"dates":[d.isoformat() for d in calendar],"sessions":len(calendar),
                        "basis":"Observed company-calendar union; J203 independently supplied and missing listed sessions",
                        "exchange_calendar_independently_verified":False},
            "sources":inputs, "datasets":inventory, "validation":checks,
            "reference_reconciliation":reference,
            "market_index":{k:v for k,v in market.items() if k!="company_calendar_dates"},
            "metadata_variability":"Processing timestamps change on each build; data files and documentation are deterministic for fixed sources/code/configuration.",
        }
        write_json(stage/"build_manifest.json",summary)
        destination.mkdir(parents=True,exist_ok=True)
        (destination/"build_manifest.json").unlink(missing_ok=True)
        for path in sorted(stage.iterdir()):
            if path.name != "build_manifest.json":
                path.replace(destination/path.name)
        (stage/"build_manifest.json").replace(destination/"build_manifest.json")
        stage.rmdir()
        LOG.info("Validated build complete: %s",destination)
        return summary
    finally:
        con.close()
        if stage.exists():
            shutil.rmtree(stage)
