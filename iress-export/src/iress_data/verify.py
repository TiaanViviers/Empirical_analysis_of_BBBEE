"""Verify source immutability, report schemas, counts and instrument uniqueness."""

import csv
import json
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

from .audit import connect, create_views, query_dicts
from .config import Config
from .ingest import SCHEMA, sha256
from .benchmark import MARKET_SCHEMA
from .validation import calendar_summary, valid_price

REQUIRED_REPORT_COLUMNS = {
    "batch_audit.csv": {"source_file", "rows", "instruments", "unique_dates", "status"},
    "instrument_coverage.csv": {"instrument_id", "observations", "valid_price_observations", "missing_close"},
    "duplicate_instruments.csv": {"instrument_id", "source_files", "extra_rows"},
    "conflicting_observations.csv": {"instrument_id", "date", "source_file", "source_row", "variants"},
    "suspicious_prices.csv": {"instrument_id", "date", "flags", "source_file", "source_row"},
    "event_coverage.csv": {"event_id", "definition", "estimation_ge_150", "estimation_ge_180", "estimation_ge_200"},
    "event_instrument_coverage.csv": {"event_id", "instrument_id", "definition", "estimation_usable_returns"},
    "market_calendar_alignment.csv": {"date", "in_company_calendar", "index_observations", "alignment_status"},
    "market_event_coverage.csv": {"event_id", "available_estimation_returns", "available_visualisation_returns"},
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(f"Verification failed: {message}")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def verify(cfg: Config) -> list[str]:
    summary_path = cfg.reports / "audit_summary.json"
    require(summary_path.exists(), "missing completion marker audit_summary.json; run audit")
    s: dict[str, Any] = json.loads(summary_path.read_text())
    require(not s["input_failures"] and not s["missing_batches"], "audit has missing or rejected inputs")
    for name, digest in s.get("implementation_sha256", {}).items():
        require(sha256(Path(__file__).parent / name) == digest, f"pipeline code changed: {name}; rerun audit")
    if s.get("uv_lock_sha256") is not None:
        require(sha256(cfg.root / "uv.lock") == s["uv_lock_sha256"], "uv.lock changed; rerun audit")
    if s["manifest_sha256"] is not None:
        require(sha256(cfg.exports / "export_manifest.json") == s["manifest_sha256"], "manifest changed")
    for name, digest in s["report_sha256"].items():
        require(sha256(cfg.reports / name) == digest, f"report modified: {name}")
    for name, required in REQUIRED_REPORT_COLUMNS.items():
        with (cfg.reports / name).open(newline="", encoding="utf-8") as handle:
            header = next(csv.reader(handle), [])
        require(required <= set(header), f"missing columns: {name}")
    paths = []
    for meta in s["inputs"]:
        path = cfg.exports / meta["source_file"]
        require(sha256(path) == meta["source_sha256"], f"source changed: {path.name}")
        target = cfg.intermediate / f"{path.stem}.parquet"
        require(sha256(target) == meta["parquet_sha256"], f"intermediate modified: {target.name}")
        require(pq.read_schema(target).equals(SCHEMA), f"intermediate schema: {target.name}")
        require(pq.ParquetFile(target).metadata.num_rows == meta["rows"], f"row count: {target.name}")
        if meta["source_batch"] is not None:
            paths.append(target)
    con = connect(cfg)
    try:
        create_views(con, paths)
        actual = query_dicts(con, """
          SELECT count(*) rows,count(DISTINCT instrument_id) instruments,
            count(DISTINCT company_name) names FROM raw
        """)[0]
        require(actual["rows"] == s["global"]["raw_rows"], "raw row total")
        require(actual["instruments"] == s["global"]["unique_instruments"], "unique instrument total")
        require(actual["names"] == s["global"]["unique_company_names"], "company name total")
        diagnosed = query_dicts(con, """
          SELECT count(*) rows,count(DISTINCT instrument_id) instruments,
            count(*) FILTER(WHERE close_raw>0 AND isfinite(close_raw)) valid_prices,
            count(*) FILTER(WHERE volume>0 AND isfinite(volume)) positive_volume
          FROM diagnostic
        """)[0]
        require(diagnosed["rows"] == s["diagnostic_totals"]["observations"], "diagnostic row reconciliation")
        require(diagnosed["valid_prices"] == s["diagnostic_totals"]["valid_price_observations"], "valid price total")
        require(diagnosed["positive_volume"] == s["diagnostic_totals"]["positive_volume_days"], "positive volume total")
        conflicts = con.execute("SELECT count(*) FROM duplicate_keys WHERE variants>1").fetchone()[0]
        require(conflicts == s["duplicates"]["conflicting_keys"], "conflict count")
        returns = query_dicts(con, """
          WITH calendar AS (
            SELECT date,row_number() OVER(ORDER BY date) position FROM (SELECT DISTINCT date FROM raw)
          ), lagged AS (
            SELECT r.close_raw,c.position,
              lag(r.close_raw) OVER w previous_close,lag(c.position) OVER w previous_position
            FROM diagnostic r JOIN calendar c USING(date)
            WINDOW w AS (PARTITION BY instrument_id ORDER BY date)
          ), changes AS (
            SELECT CASE WHEN close_raw>0 AND previous_close>0 AND isfinite(close_raw)
              AND isfinite(previous_close) AND position=previous_position+1
              THEN close_raw/previous_close-1 END ret FROM lagged
          )
          SELECT count(*) FILTER(WHERE ret IS NOT NULL AND isfinite(ret)) adjacent_price_returns,
            count(*) FILTER(WHERE isfinite(ret) AND abs(ret)>.1) abs_return_gt_10pct,
            count(*) FILTER(WHERE isfinite(ret) AND abs(ret)>.2) abs_return_gt_20pct,
            count(*) FILTER(WHERE isfinite(ret) AND abs(ret)>.3) abs_return_gt_30pct,
            count(*) FILTER(WHERE isfinite(ret) AND abs(ret)>.5) abs_return_gt_50pct,
            count(*) FILTER(WHERE isfinite(ret) AND abs(ret)>1.) abs_return_gt_100pct
          FROM changes
        """)[0]
        for key,value in returns.items():
            require(value == s["diagnostic_totals"][key], f"independent SQL return check: {key}")
        company_calendar = [r[0] for r in con.execute("SELECT DISTINCT date FROM raw ORDER BY date").fetchall()]
    finally:
        con.close()
    market_rows = pq.read_table(cfg.intermediate/'J203_prices.parquet').to_pylist()
    market_dates = [r['date'] for r in market_rows]
    calendar_set = set(company_calendar)
    market_set = set(market_dates)
    benchmark = s['market_index']
    require(len(market_rows) == benchmark['rows'], 'benchmark source row count')
    require(sorted({r['instrument_id'] for r in market_rows}) == benchmark['instrument_ids'], 'benchmark identity')
    require(len(calendar_set-market_set) == benchmark['company_dates_missing_from_index'], 'benchmark missing sessions')
    require(len(market_set-calendar_set) == benchmark['index_dates_outside_company_calendar'], 'benchmark extra sessions')
    daily = (calendar_summary(market_dates)['frequency'] == 'daily_like'
             and benchmark['instrument_ids'] == ['J203:XJSE:IND']
             and len(market_dates) == len(market_set)
             and all(valid_price(r['close_raw']) for r in market_rows)
             and not market_set-calendar_set)
    require(daily == benchmark['daily_frequency_validated'], 'benchmark daily validation')
    alignment = read_csv(cfg.reports/'market_calendar_alignment.csv')
    require(len(alignment) == len(calendar_set|market_set), 'benchmark alignment row count')
    require(len({r['date'] for r in alignment}) == len(alignment), 'benchmark alignment date uniqueness')
    output = s.get('market_index_processed')
    if output:
        path = cfg.root/output['path']
        require(pq.read_schema(path).equals(MARKET_SCHEMA), 'processed benchmark schema')
        require(sha256(path) == output['sha256'], 'processed benchmark hash')
        require(json.loads(path.with_suffix('.metadata.json').read_text()) == output, 'benchmark metadata sidecar')
        curated = pq.read_table(path).to_pylist()
        require(len(curated) == len(market_rows), 'processed benchmark row preservation')
        original = {r['date']:r for r in market_rows}
        positions = {d:i for i,d in enumerate(company_calendar)}
        for i,row in enumerate(curated):
            source = original[row['date']]
            require(row['close_raw'] == source['close_raw'] and row['source_row'] == source['source_row'],
                    'processed benchmark value/lineage preservation')
            previous = curated[i-1]['date'] if i else None
            adjacent = previous is not None and positions[row['date']] == positions[previous]+1
            require(row['is_adjacent_to_previous_session'] == adjacent, 'benchmark gap flag')
            require(row['return_variant'] is None and row['units'] is None, 'unverified benchmark definitions')
    coverage = read_csv(cfg.reports / "instrument_coverage.csv")
    require(len(coverage) == diagnosed["instruments"], "coverage instrument count")
    require(len({r["instrument_id"] for r in coverage}) == len(coverage), "coverage instrument uniqueness")
    require(sum(int(r["observations"]) for r in coverage) == diagnosed["rows"], "coverage row reconciliation")
    events = read_csv(cfg.reports / "event_coverage.csv")
    require(len(events) == 15, "five events times three return definitions")
    require(len({(r["event_id"],r["definition"]) for r in events}) == 15, "event summary uniqueness")
    details = read_csv(cfg.reports / "event_instrument_coverage.csv")
    require(len(details) == len(coverage)*15, "instrument-event reconciliation")
    require(len({(r["instrument_id"],r["event_id"],r["definition"]) for r in details}) == len(details),
            "instrument-event uniqueness")
    for row in events:
        group = [r for r in details if r["event_id"] == row["event_id"] and r["definition"] == row["definition"]]
        for threshold in (150,180,200):
            require(sum(int(r["estimation_usable_returns"]) >= threshold for r in group) == int(row[f"estimation_ge_{threshold}"]),
                    f"event threshold reconciliation: {row['event_id']}/{threshold}")
        if row['benchmark_paired_usable_count']:
            expected = sum(int(r['benchmark_estimation_usable_returns'] or 0) >= 180
                           and r['benchmark_complete_caar_m10_10'] == 'True' for r in group)
            require(expected == int(row['benchmark_paired_usable_count']), 'market-paired event reconciliation')
    return [
        f"PASS: {len(s['inputs'])} source hashes, intermediate schemas and row counts verified.",
        f"PASS: {actual['rows']:,} raw rows, {actual['instruments']:,} instruments; diagnostic counts reconcile.",
        "PASS: report hashes, required CSV schemas, instrument/event uniqueness and event counts verified.",
        "PASS: independent SQL reproduces adjacent-session return counts and all five extreme-return thresholds.",
        "PASS: benchmark calendar alignment and any processed benchmark values/provenance/gap flags verified.",
        f"BENCHMARK STATUS: {s['market_index']['status']}; daily validation = {s['market_index']['daily_benchmark_validated']}.",
        "Integrity verification does not certify research eligibility or resolve benchmark/metadata limitations.",
    ]
