"""Deep relational validation of preserved source values and trailing diagnostics."""

import json
from datetime import date
from pathlib import Path
from typing import Any

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

from .artifacts import implementation_fingerprint
from .audit import connect, create_views, query_dicts
from .config import Config
from .ingest import sha256
from .schemas import DATASET_SCHEMAS, QUALITY_RULE_VERSION


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(f"Processed validation failed: {message}")


def zero(con: duckdb.DuckDBPyConnection, query: str, label: str) -> None:
    result = con.execute(query).fetchall()[0][0]
    require(result == 0, f"{label}: {result:,} discrepancies")


def validate_quality(con: duckdb.DuckDBPyConnection, stale_run: int, extreme_threshold: float) -> None:
    """Independent SQL reconstruction; all state windows end at the current row."""
    con.execute("""
        CREATE OR REPLACE TEMP VIEW quality_base AS
        SELECT p.*, c.position,
          lag(close_raw) OVER w previous_close,
          lag(p.date) OVER w previous_row_date,
          lag(c.position) OVER w previous_row_position,
          max(p.date) FILTER(WHERE close_raw>0 AND isfinite(close_raw)) OVER earlier nearest_price_date,
          max(c.position) FILTER(WHERE close_raw>0 AND isfinite(close_raw)) OVER earlier nearest_price_position
        FROM p JOIN verification_calendar c USING(date)
        WINDOW w AS (PARTITION BY instrument_id ORDER BY p.date),
          earlier AS (PARTITION BY instrument_id ORDER BY p.date ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING)
    """)
    con.execute("""
        CREATE OR REPLACE TEMP VIEW quality_pairs AS
        SELECT *,coalesce(close_raw>0 AND isfinite(close_raw),false) expected_valid,
          coalesce(position=previous_row_position+1,false) adjacent,
          coalesce(position=previous_row_position+1 AND close_raw>0 AND isfinite(close_raw)
            AND previous_close>0 AND isfinite(previous_close),false) pair_valid
        FROM quality_base
    """)
    con.execute("""
        CREATE OR REPLACE TEMP VIEW quality_runs AS
        SELECT *,sum(CASE WHEN pair_valid AND close_raw=previous_close THEN 0 ELSE 1 END)
          OVER(PARTITION BY instrument_id ORDER BY date ROWS UNBOUNDED PRECEDING) run_id
        FROM quality_pairs
    """)
    con.execute("""
        CREATE OR REPLACE TEMP VIEW quality_expected AS
        SELECT *,CASE WHEN expected_valid THEN row_number() OVER(PARTITION BY instrument_id,run_id ORDER BY date)
                     ELSE 0 END expected_trailing,
          CASE WHEN pair_valid THEN close_raw=previous_close END expected_unchanged,
          CASE WHEN pair_valid AND isfinite(close_raw/previous_close-1) THEN close_raw/previous_close-1 END expected_return
        FROM quality_runs
    """)
    zero(con,f"""
        SELECT count(*) FROM quality_expected WHERE
          has_valid_price IS DISTINCT FROM expected_valid OR
          is_missing_price IS DISTINCT FROM (close_raw IS NULL) OR
          is_zero_price IS DISTINCT FROM coalesce(close_raw=0,false) OR
          is_negative_price IS DISTINCT FROM coalesce(close_raw<0 AND isfinite(close_raw),false) OR
          is_nonfinite_price IS DISTINCT FROM (close_raw IS NOT NULL AND NOT isfinite(close_raw)) OR
          invalid_price IS DISTINCT FROM ((close_raw IS NOT NULL AND NOT expected_valid) OR contains(parse_issues,'close_raw:')) OR
          has_positive_volume IS DISTINCT FROM coalesce(volume>0,false) OR
          is_zero_volume IS DISTINCT FROM coalesce(volume=0,false) OR
          is_missing_volume IS DISTINCT FROM (volume IS NULL) OR
          is_negative_volume IS DISTINCT FROM coalesce(volume<0,false) OR
          is_missing_trade_count IS DISTINCT FROM (number_of_trades IS NULL) OR
          is_negative_trade_count IS DISTINCT FROM coalesce(number_of_trades<0,false) OR
          is_empty_placeholder IS DISTINCT FROM (close_raw IS NULL AND volume IS NULL AND number_of_trades IS NULL AND parse_issues='') OR
          numeric_parse_issue IS DISTINCT FROM (parse_issues!='') OR
          previous_observed_date IS DISTINCT FROM previous_row_date OR
          previous_price_date IS DISTINCT FROM nearest_price_date OR
          price_gap_sessions IS DISTINCT FROM (position-nearest_price_position) OR
          is_adjacent_to_previous_session IS DISTINCT FROM adjacent OR
          has_valid_adjacent_price IS DISTINCT FROM pair_valid OR
          missing_or_invalid_adjacent_observation IS DISTINCT FROM (NOT pair_valid) OR
          unchanged_adjacent_price IS DISTINCT FROM expected_unchanged OR
          trailing_constant_price_sessions IS DISTINCT FROM expected_trailing OR
          diagnostic_price_return IS DISTINCT FROM expected_return OR
          extreme_price_change IS DISTINCT FROM (CASE WHEN expected_return IS NOT NULL THEN abs(expected_return)>{extreme_threshold!r} END) OR
          potential_stale_price IS DISTINCT FROM (expected_valid AND NOT coalesce(volume>0,false) AND
            (coalesce(expected_unchanged,false) OR expected_trailing>={int(stale_run)})) OR
          quality_rule_version!='{QUALITY_RULE_VERSION}' OR
          ticker IS DISTINCT FROM (CASE WHEN regexp_full_match(instrument_id,'[^:[:space:]]+:XJSE:EQU')
                                    THEN split_part(instrument_id,':',1) END)
    """, "trailing-only quality flags and return adjacency")


def validate_tables(con: duckdb.DuckDBPyConnection, directory: Path, calendar: list[date],
                    source_view: str | None = None, input_inventory: list[dict[str, Any]] | None = None,
                    stale_run: int = 20, extreme_threshold: float = .30) -> dict[str, Any]:
    for filename,schema in DATASET_SCHEMAS.items():
        path=directory/filename
        require(path.exists(),f"missing dataset {filename}")
        require(pq.read_schema(path).equals(schema,check_metadata=False),f"schema mismatch {filename}")
        # Read every compressed page, and enforce documented non-null fields.
        for batch in pq.ParquetFile(path).iter_batches(batch_size=50_000):
            for f,col in zip(batch.schema,batch.columns,strict=True):
                if not schema.field(f.name).nullable:
                    require(col.null_count==0,f"null in required {filename}/{f.name}")
    for filename,name in (("prices_daily.parquet","p"),("prices_observed.parquet","o"),
                          ("instruments.parquet","i"),("market_index.parquet","m"),
                          ("observation_lineage.parquet","l")):
        con.read_parquet(str(directory/filename)).create_view(name,replace=True)
    con.register("verification_calendar",pa.table({"date":pa.array(calendar,type=pa.date32()),
                                                  "position":list(range(len(calendar)))}))
    rows = con.execute("SELECT count(*),count(DISTINCT(instrument_id,date)) FROM p").fetchall()[0]
    require(rows[0]==rows[1],"canonical instrument-date uniqueness")
    masters=con.execute("SELECT count(*),count(DISTINCT instrument_id) FROM i").fetchall()[0]
    require(masters[0]==masters[1],"instrument-master identifier uniqueness")
    zero(con,"SELECT count(*) FROM ((SELECT instrument_id FROM p EXCEPT SELECT instrument_id FROM i) UNION ALL (SELECT instrument_id FROM i EXCEPT SELECT instrument_id FROM p))","master universe")
    predicate="close_raw IS NOT NULL OR volume IS NOT NULL OR number_of_trades IS NOT NULL"
    zero(con,f"SELECT count(*) FROM ((SELECT * FROM p WHERE {predicate} EXCEPT ALL SELECT * FROM o) UNION ALL (SELECT * FROM o EXCEPT ALL SELECT * FROM p WHERE {predicate}))","observed subset exact values and multiplicities")
    lineage_count=con.execute("SELECT count(*) FROM l").fetchall()[0][0]
    zero(con,"SELECT count(*) FROM (SELECT source_file,source_sheet,source_row,count(*) n FROM l GROUP BY ALL HAVING n!=1)","original source-row lineage uniqueness")
    zero(con,"""
        SELECT count(*) FROM p LEFT JOIN (
          SELECT instrument_id,date,count(*) n,count(*) FILTER(WHERE is_canonical) selected,
            min(duplicate_copy_count) lo,max(duplicate_copy_count) hi FROM l GROUP BY instrument_id,date
        ) x USING(instrument_id,date)
        WHERE n IS NULL OR n!=p.duplicate_copy_count OR selected!=1 OR lo!=n OR hi!=n
    ""","lineage copy counts and canonical selection")
    zero(con,"""
        SELECT count(*) FROM (
          SELECT l.*,row_number() OVER(PARTITION BY instrument_id,date ORDER BY source_file,source_sheet,source_row) expected_rank FROM l
        ) WHERE copy_rank!=expected_rank OR is_canonical!=(expected_rank=1)
    ""","deterministic original-copy rank")
    zero(con,"""
        SELECT count(*) FROM l LEFT JOIN p USING(instrument_id,date)
        WHERE p.instrument_id IS NULL OR l.canonical_source_file!=p.source_file
          OR l.canonical_source_sheet!=p.source_sheet OR l.canonical_source_row!=p.source_row
          OR (l.is_canonical AND (l.source_file!=p.source_file OR l.source_sheet!=p.source_sheet OR l.source_row!=p.source_row OR l.source_sha256!=p.source_sha256))
    ""","lineage links to canonical provenance")
    if input_inventory:
        company=[m for m in input_inventory if m["source_batch"] is not None]
        require(lineage_count==sum(m["rows"] for m in company),"source-to-lineage row count")
        con.register("expected_sources",pa.Table.from_pylist([
            {"source_file":m["source_file"],"source_sha256":m["source_sha256"],"source_batch":m["source_batch"],"rows":m["rows"]} for m in company]))
        zero(con,"""
            SELECT count(*) FROM l LEFT JOIN expected_sources s USING(source_file)
            WHERE s.source_file IS NULL OR l.source_sha256!=s.source_sha256 OR l.source_batch!=s.source_batch
        ""","source inventory references")
        zero(con,"SELECT count(*) FROM expected_sources s LEFT JOIN (SELECT source_file,count(*) n FROM l GROUP BY source_file) x USING(source_file) WHERE n IS NULL OR n!=s.rows","each workbook's source-row reconciliation")
    if source_view is not None:
        require(source_view=="raw","only the explicitly prepared raw view is supported")
        zero(con,"""
            SELECT count(*) FROM raw r LEFT JOIN p ON r.instrument_id=p.instrument_id AND r.date=p.date
            WHERE p.instrument_id IS NULL OR r.company_name IS DISTINCT FROM p.company_name
              OR r.close_raw IS DISTINCT FROM p.close_raw OR r.volume IS DISTINCT FROM p.volume
              OR r.number_of_trades IS DISTINCT FROM p.number_of_trades
              OR r.parse_issues IS DISTINCT FROM p.parse_issues OR r.unparsed_values IS DISTINCT FROM p.unparsed_values
        ""","all original financial values, nulls, identifiers and names preserved")
        zero(con,"""
            SELECT count(*) FROM raw r LEFT JOIN l ON r.source_file=l.source_file AND r.source_sheet=l.source_sheet AND r.source_row=l.source_row
            WHERE l.instrument_id IS NULL OR r.instrument_id!=l.instrument_id OR r.date!=l.date
        ""","every original Excel row has exact lineage")
    zero(con,f"""
        SELECT count(*) FROM i LEFT JOIN (
          SELECT instrument_id,count(*) total,
            count(*) FILTER(WHERE has_valid_price) valid,count(*) FILTER(WHERE has_positive_volume) positive,
            count(*) FILTER(WHERE close_raw IS NULL) missing,
            count(*) FILTER(WHERE {predicate}) reported,
            min(date) FILTER(WHERE has_valid_price) start_price,max(date) FILTER(WHERE has_valid_price) end_price,
            min(date) FILTER(WHERE has_positive_volume) start_volume,max(date) FILTER(WHERE has_positive_volume) end_volume
          FROM p GROUP BY instrument_id
        ) x USING(instrument_id)
        WHERE total_observations!=total OR valid_price_observations!=valid OR positive_volume_observations!=positive
          OR missing_price_observations!=missing OR reported_financial_observations!=reported
          OR observed_price_start IS DISTINCT FROM start_price OR observed_price_end IS DISTINCT FROM end_price
          OR observed_positive_volume_start IS DISTINCT FROM start_volume OR observed_positive_volume_end IS DISTINCT FROM end_volume
          OR calendar_sessions!={len(calendar)} OR abs(valid_price_coverage_pct-100.0*valid/{len(calendar)})>1e-10
          OR isin IS NOT NULL OR issuer_id IS NOT NULL OR security_type IS NOT NULL OR sector_code IS NOT NULL
          OR listing_date IS NOT NULL OR delisting_date IS NOT NULL
    ""","master coverage and unknown enrichment fields")
    zero(con,"""
        SELECT count(*) FROM i JOIN (
          SELECT instrument_id,count(*) n,list(DISTINCT source_file ORDER BY source_file) files,
            list(DISTINCT source_batch ORDER BY source_batch) batches FROM l GROUP BY instrument_id
        ) x USING(instrument_id)
        WHERE raw_source_rows!=n OR duplicate_extra_rows!=n-total_observations OR source_files!=files OR source_batches!=batches
    ""","master full-source provenance")
    validate_quality(con,stale_run,extreme_threshold)
    zero(con,"SELECT count(*) FROM m WHERE index_id!='J203:XJSE:IND' OR close_raw IS NULL OR close_raw<=0 OR NOT isfinite(close_raw) OR units IS NOT NULL OR return_variant IS NOT NULL","benchmark identity, levels and unverified definitions")
    require(con.execute("SELECT count(*) FROM m").fetchall()[0][0]==con.execute("SELECT count(DISTINCT date) FROM m").fetchall()[0][0],"benchmark date uniqueness")
    zero(con,"""
        SELECT count(*) FROM (
          SELECT m.*,c.position,lag(c.position) OVER(ORDER BY m.date) prev_pos,
            lag(m.date) OVER(ORDER BY m.date) prev_date FROM m LEFT JOIN verification_calendar c USING(date)
        ) WHERE position IS NULL OR previous_observed_date IS DISTINCT FROM prev_date
          OR is_adjacent_to_previous_session IS DISTINCT FROM coalesce(position=prev_pos+1,false)
    ""","benchmark gap flags")
    if input_inventory:
        benchmark=[m for m in input_inventory if m["source_batch"] is None][0]
        require(con.execute("SELECT count(*) FROM m").fetchall()[0][0]==benchmark["rows"],"benchmark original row preservation")
    metrics=query_dicts(con,"""
        SELECT count(*) canonical_rows,count(DISTINCT instrument_id) unique_instruments,
          count(DISTINCT date) calendar_sessions,count(*) FILTER(WHERE is_empty_placeholder) empty_placeholders,
          count(*) FILTER(WHERE has_valid_price) valid_price_observations,
          count(*) FILTER(WHERE has_positive_volume) positive_volume_observations,
          count(*) FILTER(WHERE is_zero_price) zero_close_observations,
          count(*) FILTER(WHERE is_zero_volume) zero_volume_observations,
          count(*) FILTER(WHERE potential_stale_price) potential_stale_price_observations,
          count(*) FILTER(WHERE unchanged_adjacent_price) unchanged_adjacent_price_observations,
          count(*) FILTER(WHERE extreme_price_change) extreme_price_changes,
          count(diagnostic_price_return) diagnostic_price_returns
        FROM p
    """)[0]
    metrics.update({"raw_source_rows":lineage_count,"identical_duplicate_extra_rows":lineage_count-rows[0],
                    "conflicting_keys":0,"observed_rows":con.execute("SELECT count(*) FROM o").fetchall()[0][0],
                    "instruments_with_valid_prices":con.execute("SELECT count(*) FROM i WHERE valid_price_observations>0").fetchall()[0][0],
                    "instruments_with_positive_volume":con.execute("SELECT count(*) FROM i WHERE positive_volume_observations>0").fetchall()[0][0],
                    "instruments_with_no_valid_prices":con.execute("SELECT count(*) FROM i WHERE valid_price_observations=0").fetchall()[0][0],
                    "instruments_all_fields_missing":con.execute("SELECT count(*) FROM i WHERE reported_financial_observations=0").fetchall()[0][0],
                    "market_rows":con.execute("SELECT count(*) FROM m").fetchall()[0][0],
                    "market_missing_dates":[str(r[0]) for r in con.execute("SELECT date FROM verification_calendar EXCEPT SELECT date FROM m ORDER BY date").fetchall()],
                    "checks_passed":["schemas/readability","canonical and master uniqueness","exact observed subset",
                        "complete deterministic lineage","source values and nulls","master coverage/metadata",
                        "independent trailing-only flags","benchmark levels/calendar"]})
    return metrics


def verify_processed(cfg: Config) -> dict[str, Any]:
    directory=cfg.root/"data/processed"
    path=directory/"build_manifest.json"
    require(path.exists(),"no completed build; run build")
    manifest=json.loads(path.read_text())
    require(manifest["implementation_sha256"]==implementation_fingerprint(),"processing code changed; rebuild")
    if manifest["uv_lock_sha256"] is not None:
        require(sha256(cfg.root/"uv.lock")==manifest["uv_lock_sha256"],"uv.lock changed")
    sources=manifest["sources"]
    for source in sources:
        require(sha256(cfg.exports/source["source_file"])==source["source_sha256"],f"source changed {source['source_file']}")
        intermediate=cfg.intermediate/f"{Path(source['source_file']).stem}.parquet"
        require(sha256(intermediate)==source["parquet_sha256"],f"intermediate changed {intermediate.name}")
    for name,entry in manifest["datasets"].items():
        require(sha256(directory/name)==entry["sha256"],f"processed dataset changed {name}")
    market_meta=json.loads((directory/"market_index.metadata.json").read_text())
    require(market_meta["sha256"]==sha256(directory/"market_index.parquet"),"benchmark metadata checksum")
    con=connect(cfg)
    try:
        create_views(con,[cfg.intermediate/f"{Path(s['source_file']).stem}.parquet" for s in sources if s["source_batch"] is not None])
        require(con.execute("SELECT count(*) FROM duplicate_keys WHERE variants>1").fetchall()[0][0]==0,"new source conflicts")
        result=validate_tables(con,directory,[date.fromisoformat(d) for d in manifest["calendar"]["dates"]],
            source_view="raw",input_inventory=sources,stale_run=manifest["configuration"]["stale_run"],
            extreme_threshold=manifest["configuration"]["extreme_threshold"])
        # Independently compare the preserved benchmark with its standardized source.
        con.read_parquet(str(cfg.intermediate/"J203_prices.parquet")).create_view("original_market")
        zero(con,"""
            SELECT count(*) FROM original_market s FULL JOIN m ON s.date=m.date
            WHERE s.date IS NULL OR m.date IS NULL OR s.instrument_id!=m.index_id OR s.company_name!=m.index_name
              OR s.close_raw IS DISTINCT FROM m.close_raw OR s.source_file!=m.source_file
              OR s.source_sheet!=m.source_sheet OR s.source_row!=m.source_row
        ""","benchmark original values and provenance")
    finally:
        con.close()
    require(result==manifest["validation"],"build/verify statistical reconciliation")
    return result
