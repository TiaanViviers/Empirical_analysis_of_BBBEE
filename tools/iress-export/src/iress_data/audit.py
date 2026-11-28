"""Dataset integrity, instrument diagnostics and provisional event coverage."""

import csv
import json
import logging
import platform
from collections import Counter
from datetime import date
from importlib.metadata import version
from itertools import groupby
from pathlib import Path
from typing import Any, Iterable

import duckdb
import pyarrow.parquet as pq

from .config import Config, END, EVENTS, START
from .benchmark import market_event_coverage, return_availability, write_market_source
from .ingest import ingest, sha256
from .validation import adjacent_return, calendar_summary, finite, longest_run, valid_price

LOG = logging.getLogger(__name__)


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: list[str]) -> None:
    staged = path.with_suffix(".pending.csv")
    with staged.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    staged.replace(path)


def query_dicts(con: duckdb.DuckDBPyConnection, sql: str,
                params: list[Any] | None = None) -> list[dict[str, Any]]:
    cursor = con.execute(sql, params or [])
    columns = [d[0] for d in cursor.description]
    return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]


def connect(cfg: Config) -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    con.execute("SET memory_limit = ?", [cfg.memory_limit])
    temp = cfg.intermediate / "duckdb_temp"
    temp.mkdir(parents=True, exist_ok=True)
    con.execute("SET temp_directory = ?", [str(temp)])
    con.execute("SET threads = 2")
    con.execute("SET preserve_insertion_order = false")
    return con


def create_views(con: duckdb.DuckDBPyConnection, paths: list[Path]) -> None:
    # Explicit input list avoids including stale intermediate files on a rerun.
    con.read_parquet([str(p) for p in paths]).create_view("raw")
    con.execute("""
        CREATE TEMP TABLE duplicate_keys AS
        SELECT instrument_id, date, count(*) AS copies,
               count(DISTINCT struct_pack(company_name := company_name,
                 close_raw := close_raw, volume := volume,
                 number_of_trades := number_of_trades,
                 parse_issues := parse_issues, unparsed_values := unparsed_values)) AS variants
        FROM raw GROUP BY instrument_id, date HAVING count(*) > 1
    """)
    # Audit-only reduction: identical duplicates counted once, conflicting keys
    # excluded entirely from numerical diagnostics. Raw Parquet retains all copies.
    con.execute("""
        CREATE VIEW diagnostic AS
        SELECT r.* FROM raw r LEFT JOIN duplicate_keys k USING (instrument_id,date)
        WHERE k.variants IS NULL OR k.variants = 1
        QUALIFY row_number() OVER (
          PARTITION BY r.instrument_id,r.date ORDER BY r.source_file,r.source_sheet,r.source_row) = 1
    """)


def batch_audit(con: duckdb.DuckDBPyConnection, cfg: Config,
                metadata: list[dict[str, Any]], manifest: dict[str, Any],
                failures: dict[str, str]) -> list[dict[str, Any]]:
    records = []
    metas = {m["source_file"]: m for m in metadata}
    baseline = None
    expected_names = {f"jse_prices_{i:02d}.xlsx" for i in range(1, cfg.expected_batches + 1)}
    names = expected_names | {p.name for p in cfg.exports.glob("jse_prices_*.xlsx")}
    for name in sorted(names):
        suffix = Path(name).stem.rsplit("_", 1)[1]
        batch = int(suffix) if suffix.isdigit() else None
        prior = manifest.get(str(batch), {})
        meta = metas.get(name)
        expected = prior.get("expected_instrument_count", prior.get("instrument_count"))
        record: dict[str, Any] = {
            "source_file": name, "source_batch": batch,
            "exists": (cfg.exports / name).exists(), "status": "ok" if meta else "unavailable",
            "error": failures.get(name, ""), "manifest_status": prior.get("status"),
            "manifest_instruments": prior.get("instrument_count"),
            "expected_instruments": expected, "manifest_rows": prior.get("row_count"),
            "missing_companies_manifest": json.dumps(prior.get("missing_companies", [])),
            "unexpected_batch": name not in expected_names,
        }
        if meta:
            stats = query_dicts(con, """
                SELECT count(*) AS rows, count(DISTINCT instrument_id) AS instruments,
                  count(DISTINCT company_name) AS company_names,
                  min(date) AS min_date, max(date) AS max_date,
                  count(DISTINCT date) AS unique_dates,
                  count(*) - count(DISTINCT (instrument_id,date)) AS duplicate_extra_rows,
                  count(*) FILTER (WHERE parse_issues != '') AS numeric_parse_issue_rows,
                  count(*) FILTER (WHERE date < ? OR date > ?) AS outside_requested_period
                FROM raw WHERE source_file = ?
            """, [START, END, name])[0]
            dates = [r[0] for r in con.execute(
                "SELECT DISTINCT date FROM raw WHERE source_file=? ORDER BY date", [name]).fetchall()]
            if baseline is None:
                baseline = dates
            actual_ids = {r[0] for r in con.execute(
                "SELECT DISTINCT instrument_id FROM raw WHERE source_file=?", [name]).fetchall()}
            manifest_ids = set(prior.get("instruments", {}))
            name_mismatches = con.execute("""
                SELECT DISTINCT instrument_id,company_name FROM raw WHERE source_file=?
            """, [name]).fetchall()
            per_instrument = con.execute("""
                SELECT min(n),max(n),min(nd),max(nd) FROM (
                  SELECT count(*) n,count(DISTINCT date) nd FROM raw
                  WHERE source_file=? GROUP BY instrument_id)
            """, [name]).fetchone()
            record.update(stats)
            record.update({
                "frequency": calendar_summary(dates)["frequency"],
                "calendar_matches_first_batch": dates == baseline,
                "weekend_dates": sum(d.weekday() > 4 for d in dates),
                "min_rows_per_instrument": per_instrument[0],
                "max_rows_per_instrument": per_instrument[1],
                "min_dates_per_instrument": per_instrument[2],
                "max_dates_per_instrument": per_instrument[3],
                "manifest_counts_match": stats["rows"] == prior.get("row_count")
                    and stats["instruments"] == prior.get("instrument_count"),
                "manifest_missing_ids": json.dumps(sorted(manifest_ids - actual_ids)),
                "manifest_unexpected_ids": json.dumps(sorted(actual_ids - manifest_ids)),
                "manifest_company_name_mismatches": sum(
                    prior.get("instruments", {}).get(i) != n for i, n in name_mismatches),
                "expected_shortfall": expected - len(actual_ids) if expected is not None else None,
                "columns": json.dumps(meta["columns"]),
                "source_types": json.dumps(meta["source_types"], sort_keys=True),
                "source_sha256": meta["source_sha256"],
            })
        records.append(record)
    fields = list(dict.fromkeys(k for r in records for k in r))
    write_csv(cfg.reports / "batch_audit.csv", records, fields)
    return records


def duplicate_reports(con: duckdb.DuckDBPyConnection, cfg: Config) -> dict[str, Any]:
    duplicates = query_dicts(con, """
        SELECT instrument_id, string_agg(DISTINCT company_name,' | ' ORDER BY company_name) company_names,
          string_agg(DISTINCT cast(source_batch AS VARCHAR),',' ORDER BY cast(source_batch AS VARCHAR)) source_batches,
          string_agg(DISTINCT source_file,',' ORDER BY source_file) source_files,
          count(DISTINCT source_file) batch_count, count(*) row_count,
          count(DISTINCT date) distinct_dates,
          count(*) - count(DISTINCT date) extra_rows
        FROM raw GROUP BY instrument_id
        HAVING count(DISTINCT source_file)>1 OR count(*)>count(DISTINCT date)
        ORDER BY instrument_id
    """)
    write_csv(cfg.reports / "duplicate_instruments.csv", duplicates, [
        "instrument_id", "company_names", "source_batches", "source_files", "batch_count",
        "row_count", "distinct_dates", "extra_rows"])
    conflict_fields = ["instrument_id", "company_name", "date", "close_raw", "volume",
                       "number_of_trades", "source_file", "source_sheet", "source_row",
                       "parse_issues", "unparsed_values", "copies", "variants"]
    sql = """
        SELECT r.instrument_id,r.company_name,r.date,r.close_raw,r.volume,r.number_of_trades,
          r.source_file,r.source_sheet,r.source_row,r.parse_issues,r.unparsed_values,k.copies,k.variants
        FROM raw r JOIN duplicate_keys k USING(instrument_id,date)
        WHERE k.variants>1 ORDER BY r.instrument_id,r.date,r.source_file,r.source_row
    """
    # Stream possibly large conflict output rather than fetch it all.
    cursor = con.execute(sql)
    def conflict_rows() -> Iterable[dict[str, Any]]:
        while rows := cursor.fetchmany(10_000):
            yield from (dict(zip(conflict_fields, r, strict=True)) for r in rows)
    write_csv(cfg.reports / "conflicting_observations.csv", conflict_rows(), conflict_fields)
    return query_dicts(con, """
        SELECT count(*) duplicate_keys, coalesce(sum(copies-1),0) duplicate_extra_rows,
          count(*) FILTER(WHERE variants>1) conflicting_keys,
          count(*) FILTER(WHERE variants=1) identical_duplicate_keys
        FROM duplicate_keys
    """)[0] | {"overlapping_or_repeated_instruments": len(duplicates), "examples": duplicates[:10]}


MARKET_ALIGNMENT_FIELDS = ["date", "in_company_calendar", "index_observations",
                           "valid_index_levels", "alignment_status"]


def write_market_alignment(cfg: Config, records: list[dict[str, Any]],
                           company_calendar: list[date]) -> None:
    """Expose each missing, duplicate, invalid or off-calendar benchmark date."""
    company_dates = set(company_calendar)
    counts = Counter(r["date"] for r in records)
    valid_counts = Counter(r["date"] for r in records if valid_price(r["close_raw"]))
    rows = []
    for day in sorted(company_dates | set(counts)):
        if day not in company_dates:
            status = "index_date_outside_company_calendar"
        elif counts[day] == 0:
            status = "missing_index_date"
        elif counts[day] > 1:
            status = "duplicate_index_date"
        elif valid_counts[day] != 1:
            status = "invalid_index_level"
        else:
            status = "aligned_valid"
        rows.append({"date": day, "in_company_calendar": day in company_dates,
                     "index_observations": counts[day], "valid_index_levels": valid_counts[day],
                     "alignment_status": status})
    write_csv(cfg.reports / "market_calendar_alignment.csv", rows, MARKET_ALIGNMENT_FIELDS)


def index_audit(cfg: Config, metadata: dict[str, Any] | None,
                company_calendar: list[date], error: str | None) -> dict[str, Any]:
    if metadata is None:
        write_market_alignment(cfg, [], company_calendar)
        return {"daily_benchmark_validated": False, "status": "unavailable", "error": error}
    con = connect(cfg)
    try:
        con.read_parquet(str(cfg.intermediate / "J203_prices.parquet")).create_view("market")
        rows = query_dicts(con, "SELECT * FROM market ORDER BY date,source_row")
    finally:
        con.close()
    write_market_alignment(cfg, rows, company_calendar)
    dates = [r["date"] for r in rows]
    levels = [r["close_raw"] for r in rows]
    ids = sorted({r["instrument_id"] for r in rows})
    calendar = calendar_summary(dates)
    valid_dates = sorted({r["date"] for r in rows if valid_price(r["close_raw"])})
    duplicate_dates = len(dates) - len(set(dates))
    unmatched_company = sorted(set(company_calendar) - set(dates))
    daily_frequency_ok = (calendar["frequency"] == "daily_like" and ids == ["J203:XJSE:IND"]
                and not duplicate_dates and all(valid_price(x) for x in levels)
                and not (set(dates) - set(company_calendar)))
    complete = valid_dates == company_calendar and not duplicate_dates
    daily_ok = daily_frequency_ok and complete
    return {
        **calendar, "rows": len(rows), "instrument_ids": ids,
        "names": sorted({r["company_name"] for r in rows}),
        "duplicate_dates": duplicate_dates,
        "missing_levels": sum(v is None for v in levels),
        "invalid_levels": sum(not valid_price(v) for v in levels),
        "negative_levels": sum(finite(v) and v < 0 for v in levels),
        "zero_levels": sum(v == 0 for v in levels),
        "numeric_parse_issue_rows": sum(bool(r["parse_issues"]) for r in rows),
        "min_level": min((v for v in levels if valid_price(v)), default=None),
        "max_level": max((v for v in levels if valid_price(v)), default=None),
        "company_dates_missing_from_index": len(unmatched_company),
        "company_date_matches": len(set(company_calendar) & set(dates)),
        "index_dates_outside_company_calendar": len(set(dates) - set(company_calendar)),
        "daily_benchmark_validated": daily_ok,
        "daily_frequency_validated": daily_frequency_ok,
        "calendar_complete": complete,
        "missing_company_dates": [d.isoformat() for d in unmatched_company],
        "company_calendar_dates": [d.isoformat() for d in company_calendar],
        "status": "validated_daily" if daily_ok else "validated_daily_with_gaps" if daily_frequency_ok else "requires_reexport_or_validation",
        "return_variant": "unverified_in_IRESS_export",
        "identity_reference": "https://www.jse.co.za/all-share-j203",
        "variant_reference": "https://www.jse.co.za/market-data/our-market-data-products/index-market-data",
        "source_columns": metadata["columns"],
        "source_sha256": metadata["source_sha256"],
    }


def instrument_diagnostics(records: list[dict[str, Any]], calendar: list[date],
                           cfg: Config) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    """One instrument at a time; calendar positions prevent bridging missing sessions."""
    positions = {d: i for i, d in enumerate(calendar)}
    by_date = {r["date"]: r for r in records}
    prices = [by_date.get(d, {}).get("close_raw") for d in calendar]
    volumes = [by_date.get(d, {}).get("volume") for d in calendar]
    trades = [by_date.get(d, {}).get("number_of_trades") for d in calendar]
    valid = [valid_price(v) for v in prices]
    positive_volume = [finite(v) and v > 0 for v in volumes]
    missing_prices = [v is None for v in prices]
    # Constant positive-price runs; a calendar gap or missing price breaks a run.
    constant_lengths = [0] * len(calendar)
    runs = []
    start = 0
    for i in range(len(calendar) + 1):
        if i == len(calendar) or not (i > start and valid[i] and valid[i - 1]
                                      and prices[i] == prices[i - 1]):
            if i > start and valid[start]:
                length = i - start
                runs.append(length)
                for j in range(start, i):
                    constant_lengths[j] = length
            start = i
    returns = [None] * len(calendar)
    stale = [False] * len(calendar)
    suspicious = []
    counter: Counter[str] = Counter()
    for r in records:
        i = positions[r["date"]]
        current = prices[i]
        previous = prices[i - 1] if i else None
        ret = adjacent_return(previous, current, i - 1 if i else None, i)
        returns[i] = ret
        flags = []
        if r["parse_issues"]:
            flags.append("numeric_parse_issue")
        for name, v in (("price", current), ("volume", volumes[i]), ("trade_count", trades[i])):
            if v is not None:
                if not finite(v):
                    flags.append(f"nonfinite_{name}")
                elif v < 0:
                    flags.append(f"negative_{name}")
                elif name == "price" and v == 0:
                    flags.append("zero_price")
                elif name != "price" and not v.is_integer():
                    flags.append(f"fractional_{name}")
        if ret is not None:
            counter["adjacent_price_returns"] += 1
            if abs(ret) > cfg.extreme_threshold:
                flags.append("extreme_price_change")
            for threshold in (.10, .20, .30, .50, 1.0):
                if abs(ret) > threshold:
                    counter[f"abs_return_gt_{int(threshold * 100)}pct"] += 1
            if volumes[i] == 0 and ret != 0:
                flags.append("price_change_zero_volume")
            if not positive_volume[i] and ret != 0:
                counter["price_change_without_positive_volume"] += 1
            if prices[i] == previous:
                counter["unchanged_adjacent_price_pairs"] += 1
                if volumes[i] == 0:
                    counter["unchanged_pairs_zero_volume"] += 1
                if not positive_volume[i]:
                    stale[i] = True
            ratio = current / previous
            factors = (.01, .02, .05, .1, .2, .25, 1/3, .5, 2., 3., 4., 5., 10., 20., 50., 100.)
            # A ratio near a round factor is only a candidate, never an adjustment.
            if abs(ret) > cfg.extreme_threshold and any(abs(ratio / f - 1) <= .02 for f in factors):
                flags.append("round_factor_corporate_action_candidate")
        if constant_lengths[i] >= cfg.stale_run:
            flags.append("constant_price_run")
            if not positive_volume[i]:
                stale[i] = True
        if stale[i]:
            flags.append("potential_stale_price")
        counter.update(flags)
        if flags:
            suspicious.append({
                "instrument_id": r["instrument_id"], "company_name": r["company_name"],
                "date": r["date"], "close_raw": current,
                "previous_close_raw": previous,
                "previous_date": calendar[i - 1] if i else None,
                "diagnostic_price_return": ret, "volume": volumes[i],
                "number_of_trades": trades[i], "constant_run_sessions": constant_lengths[i],
                "flags": ";".join(flags), "source_file": r["source_file"],
                "source_sheet": r["source_sheet"], "source_row": r["source_row"],
                "parse_issues": r["parse_issues"], "unparsed_values": r["unparsed_values"],
            })
    def edge(flags: list[bool], first: bool) -> date | None:
        indices = [i for i, value in enumerate(flags) if value]
        return calendar[indices[0 if first else -1]] if indices else None
    n = len(records)
    missing_close = sum(r["close_raw"] is None for r in records)
    missing_volume = sum(r["volume"] is None for r in records)
    missing_trades = sum(r["number_of_trades"] is None for r in records)
    valid_n = sum(valid)
    close_zero_volume = sum(ok and v == 0 for ok, v in zip(valid, volumes))
    close_missing_volume = sum(ok and v is None for ok, v in zip(valid, volumes))
    empty = sum(r["close_raw"] is None and r["volume"] is None and r["number_of_trades"] is None
                and not r["parse_issues"] for r in records)
    summary = {
        "instrument_id": records[0]["instrument_id"],
        "company_names": " | ".join(sorted({r["company_name"] or "" for r in records})),
        "observations": n, "calendar_sessions": len(calendar),
        "absent_calendar_sessions": len(calendar) - n,
        "missing_close": missing_close, "missing_close_pct": missing_close / n * 100,
        "missing_volume": missing_volume, "missing_volume_pct": missing_volume / n * 100,
        "missing_trade_count": missing_trades, "missing_trade_count_pct": missing_trades / n * 100,
        "valid_price_observations": valid_n,
        "valid_price_coverage_pct": valid_n / len(calendar) * 100,
        "first_valid_price_date": edge(valid, True), "last_valid_price_date": edge(valid, False),
        "first_positive_volume_date": edge(positive_volume, True),
        "last_positive_volume_date": edge(positive_volume, False),
        "positive_volume_days": sum(positive_volume),
        "zero_volume_days": sum(v == 0 for v in volumes),
        "longest_without_positive_volume_sessions": longest_run([not v for v in positive_volume]),
        "longest_missing_price_sessions": longest_run(missing_prices),
        "longest_constant_price_sessions": max(runs, default=0),
        "all_fields_missing_rows": empty, "effectively_empty_no_valid_prices": valid_n == 0,
        "valid_price_zero_volume_rows": close_zero_volume,
        "valid_price_missing_volume_rows": close_missing_volume,
        "source_batches": ",".join(str(v) for v in sorted({r["source_batch"] for r in records})),
        **{k: counter[k] for k in [
            "adjacent_price_returns", "unchanged_adjacent_price_pairs", "unchanged_pairs_zero_volume",
            "price_change_without_positive_volume", "price_change_zero_volume",
            "constant_price_run", "potential_stale_price", "extreme_price_change",
            "round_factor_corporate_action_candidate", "zero_price", "negative_price",
            "negative_volume", "negative_trade_count", "nonfinite_price",
            "numeric_parse_issue", "fractional_volume", "fractional_trade_count",
            "abs_return_gt_10pct", "abs_return_gt_20pct", "abs_return_gt_30pct",
            "abs_return_gt_50pct", "abs_return_gt_100pct"]},
    }
    series = {"valid": valid, "positive_volume": positive_volume, "returns": returns}
    return summary, suspicious, series


DEFINITIONS = ("adjacent_prices", "current_positive_volume", "both_positive_volume")
WINDOWS = {"event_0_1": (0, 1), "event_m1_3": (-1, 3), "event_0_5": (0, 5),
           "anticipation_m10_m1": (-10, -1), "caar_m10_10": (-10, 10)}


def event_diagnostics(instrument_id: str, series: dict[str, Any], calendar: list[date],
                      calendar_source: str,
                      market_available: list[bool] | None = None) -> list[dict[str, Any]]:
    rows = []
    for event_id, name, event_date in EVENTS:
        candidates = [i for i, d in enumerate(calendar) if d >= event_date]
        origin = candidates[0] if candidates else None
        for definition in DEFINITIONS:
            def usable(i: int) -> bool:
                if not 0 <= i < len(calendar) or series["returns"][i] is None:
                    return False
                if definition in ("current_positive_volume", "both_positive_volume"):
                    if not series["positive_volume"][i]:
                        return False
                if definition == "both_positive_volume" and (i == 0 or not series["positive_volume"][i-1]):
                    return False
                return True
            row = {"event_id": event_id, "event_name": name, "event_date": event_date,
                   "aligned_event_date": calendar[origin] if origin is not None else None,
                   "instrument_id": instrument_id, "definition": definition,
                   "calendar_source": calendar_source,
                   "calendar_validated_by_daily_benchmark": calendar_source == "validated_daily_J203"}
            if origin is None:
                row.update({"any_near_price": False, "any_near_positive_volume": False,
                            "any_near_price_and_positive_volume": False,
                            "estimation_usable_returns": 0, "estimation_valid_prices": 0,
                            "estimation_positive_volume_days": 0,
                            "estimation_window_in_bounds": False})
                row.update({f"complete_{k}": False for k in WINDOWS})
            else:
                near = range(max(0, origin - 10), min(len(calendar), origin + 11))
                est = range(max(0, origin - 250), max(0, origin - 29))
                row.update({
                    "any_near_price": any(series["valid"][i] for i in near),
                    "any_near_positive_volume": any(series["positive_volume"][i] for i in near),
                    "any_near_price_and_positive_volume": any(
                        series["valid"][i] and series["positive_volume"][i] for i in near),
                    "estimation_usable_returns": sum(usable(i) for i in est),
                    "estimation_valid_prices": sum(series["valid"][i] for i in est),
                    "estimation_positive_volume_days": sum(series["positive_volume"][i] for i in est),
                    "estimation_window_in_bounds": origin - 251 >= 0 and origin - 30 < len(calendar),
                })
                for key, (lo, hi) in WINDOWS.items():
                    row[f"complete_{key}"] = all(usable(origin + relative) for relative in range(lo, hi + 1))
            row["benchmark_daily_frequency_validated"] = market_available is not None
            if market_available is None or origin is None:
                row["benchmark_estimation_usable_returns"] = None
                row["benchmark_required_sessions_complete"] = None
                row.update({f"benchmark_complete_{key}": None for key in WINDOWS})
            else:
                def paired(i: int) -> bool:
                    return 0 <= i < len(calendar) and market_available[i] and usable(i)
                est_indices = range(max(0,origin-250),max(0,origin-29))
                row["benchmark_estimation_usable_returns"] = sum(paired(i) for i in est_indices)
                required = [origin+j for lo,hi in ((-250,-30),(-10,10)) for j in range(lo,hi+1)]
                row["benchmark_required_sessions_complete"] = all(
                    0 <= i < len(calendar) and market_available[i] for i in required)
                row.update({f"benchmark_complete_{key}": all(paired(origin+j) for j in range(lo,hi+1))
                            for key,(lo,hi) in WINDOWS.items()})
            rows.append(row)
    return rows


def summarize_events(details: list[dict[str, Any]], cfg: Config) -> list[dict[str, Any]]:
    rows = []
    for event_id, name, event_date in EVENTS:
        for definition in DEFINITIONS:
            group = [r for r in details if r["event_id"] == event_id and r["definition"] == definition]
            if not group:
                continue
            rows.append({
                "event_id": event_id, "event_name": name, "event_date": event_date,
                "aligned_event_date": group[0]["aligned_event_date"], "definition": definition,
                "calendar_source": group[0]["calendar_source"],
                "calendar_validated_by_daily_benchmark": group[0]["calendar_validated_by_daily_benchmark"],
                "benchmark_daily_frequency_validated": group[0]["benchmark_daily_frequency_validated"],
                "benchmark_required_sessions_complete": group[0]["benchmark_required_sessions_complete"],
                "total_instruments": len(group),
                "any_near_price": sum(r["any_near_price"] for r in group),
                "any_near_positive_volume": sum(r["any_near_positive_volume"] for r in group),
                "any_near_price_and_positive_volume": sum(r["any_near_price_and_positive_volume"] for r in group),
                **{f"estimation_ge_{n}": sum(r["estimation_usable_returns"] >= n for r in group)
                   for n in (150, 180, 200)},
                **{f"complete_{key}": sum(r[f"complete_{key}"] for r in group) for key in WINDOWS},
                "est180_and_all_event_windows": sum(r["estimation_usable_returns"] >= 180 and
                    all(r[f"complete_{k}"] for k in ("event_0_1", "event_m1_3", "event_0_5")) for r in group),
                "est180_and_complete_m10_10": sum(r["estimation_usable_returns"] >= 180 and
                    r["complete_caar_m10_10"] for r in group),
                **{f"benchmark_estimation_ge_{n}": None if not group[0]["benchmark_daily_frequency_validated"] else
                    sum((r["benchmark_estimation_usable_returns"] or 0) >= n for r in group) for n in (150,180,200)},
                "benchmark_paired_usable_count": None if not group[0]["benchmark_daily_frequency_validated"] else
                    sum((r["benchmark_estimation_usable_returns"] or 0) >= 180 and
                        bool(r["benchmark_complete_caar_m10_10"]) for r in group),
            })
    write_csv(cfg.reports / "event_coverage.csv", rows, list(rows[0]) if rows else ["event_id", "definition"])
    return rows


SUSPICIOUS_FIELDS = ["instrument_id", "company_name", "date", "close_raw", "previous_close_raw",
                     "previous_date", "diagnostic_price_return", "volume", "number_of_trades",
                     "constant_run_sessions", "flags", "source_file", "source_sheet", "source_row",
                     "parse_issues", "unparsed_values"]


def run_audit(cfg: Config, force: bool = False) -> dict[str, Any]:
    cfg.reports.mkdir(parents=True, exist_ok=True)
    # A completion marker is installed only after the whole report generation succeeds.
    (cfg.reports / "audit_summary.json").unlink(missing_ok=True)
    manifest_path = cfg.exports / "export_manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    paths = sorted(cfg.exports.glob("jse_prices_*.xlsx"))
    metadata = []
    failures = {}
    index_meta = None
    for path in paths + [cfg.exports / "J203_prices.xlsx"]:
        try:
            meta = ingest(path, cfg, force)
            if path.name == "J203_prices.xlsx":
                index_meta = meta
            else:
                metadata.append(meta)
        except Exception as exc:
            LOG.exception("Input rejected: %s", path.name)
            failures[path.name] = f"{type(exc).__name__}: {exc}"
    if not metadata:
        raise ValueError("No readable company workbooks; no numerical audit can be produced")
    con = connect(cfg)
    try:
        create_views(con, [cfg.intermediate / f"{Path(m['source_file']).stem}.parquet" for m in metadata])
        LOG.info("Checking batch integrity and duplicate keys")
        batches = batch_audit(con, cfg, metadata, manifest, failures)
        duplicates = duplicate_reports(con, cfg)
        calendar = [r[0] for r in con.execute("SELECT DISTINCT date FROM raw ORDER BY date").fetchall()]
        market = index_audit(cfg, index_meta, calendar, failures.get("J203_prices.xlsx"))
        missing_activity = query_dicts(con, """
            SELECT date,count(DISTINCT instrument_id) instruments,
              count(*) FILTER(WHERE close_raw>0 AND isfinite(close_raw)) valid_price_observations,
              count(DISTINCT instrument_id) FILTER(WHERE volume>0 AND isfinite(volume)) positive_volume_instruments,
              sum(volume) FILTER(WHERE isfinite(volume)) total_reported_volume
            FROM raw WHERE date IN (SELECT unnest(?::DATE[])) GROUP BY date ORDER BY date
        """, [market.get("missing_company_dates", [])])
        write_csv(cfg.reports / "market_missing_session_activity.csv", missing_activity,
                  ["date","instruments","valid_price_observations","positive_volume_instruments","total_reported_volume"])
        calendar_source = ("validated_daily_J203" if market["daily_benchmark_validated"] else
            "daily_J203_with_company_calendar_gap" if market.get("daily_frequency_validated") else
            "company_calendar_proxy_unvalidated")
        market_available = (return_availability(
            pq.read_table(cfg.intermediate / "J203_prices.parquet").to_pylist(), calendar)
            if market.get("daily_frequency_validated") else None)
        market_events = market_event_coverage(calendar, market_available)
        write_csv(cfg.reports / "market_event_coverage.csv", market_events, list(market_events[0]))
        market_output = write_market_source(cfg, market)
        global_stats = query_dicts(con, """
            SELECT count(*) raw_rows,count(DISTINCT instrument_id) unique_instruments,
              count(DISTINCT company_name) unique_company_names,
              count(DISTINCT (instrument_id,date)) unique_instrument_dates,
              max(volume) FILTER(WHERE isfinite(volume)) max_reported_volume,
              max(number_of_trades) FILTER(WHERE isfinite(number_of_trades)) max_reported_trade_count,
              count(*) FILTER (WHERE parse_issues!='') numeric_parse_issue_rows,
              count(*) FILTER (WHERE trim(instrument_id)!=instrument_id) identifier_whitespace_rows,
              count(*) FILTER (WHERE close_raw IS NULL AND volume IS NULL AND
                number_of_trades IS NULL AND parse_issues='') raw_all_fields_missing_rows
            FROM raw
        """)[0]
        names = query_dicts(con, """
            SELECT company_name,count(DISTINCT instrument_id) instrument_count,
              string_agg(DISTINCT instrument_id,',' ORDER BY instrument_id) instrument_ids
            FROM raw GROUP BY company_name HAVING count(DISTINCT instrument_id)>1
            ORDER BY instrument_count DESC,company_name
        """)
        write_csv(cfg.reports / "company_identity_candidates.csv", names,
                  ["company_name", "instrument_count", "instrument_ids"])
        multi_names = query_dicts(con, """
            SELECT instrument_id,count(DISTINCT company_name) name_count,
              string_agg(DISTINCT company_name,' | ' ORDER BY company_name) company_names
            FROM raw GROUP BY instrument_id HAVING count(DISTINCT company_name)>1
            ORDER BY instrument_id
        """)
        write_csv(cfg.reports / "instrument_name_variants.csv", multi_names,
                  ["instrument_id", "name_count", "company_names"])
        suffixes = query_dicts(con, """
            SELECT regexp_extract(instrument_id, ':[^:]+$') suffix,
              count(DISTINCT instrument_id) instruments FROM raw GROUP BY suffix ORDER BY suffix
        """)
        missing_name_candidates = []
        # A shared first name token is a review lead, never an identity match.
        name_inventory = con.execute("SELECT DISTINCT instrument_id,company_name FROM raw ORDER BY instrument_id,company_name").fetchall()
        for batch, entry in sorted(manifest.items(), key=lambda x: int(x[0])):
            for missing_name in entry.get("missing_companies", []):
                token = missing_name.casefold().split()[0] if missing_name.split() else ""
                for ident, name in name_inventory:
                    if len(token) >= 3 and name and name.casefold().split()[0] == token:
                        missing_name_candidates.append({"manifest_batch": batch,
                            "manifest_missing_name": missing_name, "observed_instrument_id": ident,
                            "observed_company_name": name, "match_basis": "shared_first_name_token_unverified"})
        write_csv(cfg.reports / "manifest_name_candidates.csv", missing_name_candidates,
                  ["manifest_batch", "manifest_missing_name", "observed_instrument_id",
                   "observed_company_name", "match_basis"])
        fractional_closes = query_dicts(con, """
            SELECT instrument_id, min(company_name) company_name,
              count(*) observations, min(close_raw) min_fractional_close,max(close_raw) max_fractional_close
            FROM diagnostic WHERE isfinite(close_raw) AND close_raw != trunc(close_raw)
            GROUP BY instrument_id ORDER BY instrument_id
        """)
        write_csv(cfg.reports / "fractional_close_instruments.csv", fractional_closes,
                  ["instrument_id", "company_name", "observations", "min_fractional_close", "max_fractional_close"])
        # One external sort; DuckDB may spill, Python retains one instrument only.
        LOG.info("Computing instrument and event diagnostics using %s", calendar_source)
        provenance = {r["instrument_id"]: r for r in query_dicts(con, """
            SELECT instrument_id,count(*) raw_source_rows,
              list(DISTINCT source_batch ORDER BY source_batch) source_batches,
              string_agg(DISTINCT source_file,',' ORDER BY source_file) source_files
            FROM raw GROUP BY instrument_id
        """)}
        conflict_counts = dict(con.execute("""
            SELECT instrument_id,count(*) FROM duplicate_keys WHERE variants>1 GROUP BY instrument_id
        """).fetchall())
        cursor = con.execute("SELECT * FROM diagnostic ORDER BY instrument_id,date")
        columns = [d[0] for d in cursor.description]
        def iter_records() -> Iterable[dict[str, Any]]:
            while block := cursor.fetchmany(10_000):
                yield from (dict(zip(columns, r, strict=True)) for r in block)
        coverages = []
        events = []
        totals: Counter[str] = Counter()
        staged = cfg.reports / "suspicious_prices.pending.csv"
        with staged.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=SUSPICIOUS_FIELDS)
            writer.writeheader()
            for ident, group in groupby(iter_records(), key=lambda r: r["instrument_id"]):
                coverage, suspicious, series = instrument_diagnostics(list(group), calendar, cfg)
                sources = provenance[ident]
                coverage.update({
                    "source_batches": ",".join(str(b) for b in sources["source_batches"]),
                    "source_files": sources["source_files"],
                    "raw_source_rows": sources["raw_source_rows"],
                    "raw_rows_excluded_from_numeric_diagnostics": sources["raw_source_rows"] - coverage["observations"],
                    "conflicting_date_keys": conflict_counts.get(ident, 0),
                })
                coverages.append(coverage)
                writer.writerows(suspicious)
                events.extend(event_diagnostics(ident, series, calendar, calendar_source, market_available))
                totals["suspicious_rows"] += len(suspicious)
                for key, value in coverage.items():
                    if isinstance(value, int) and not isinstance(value, bool):
                        totals[key] += value
                if len(coverages) % 200 == 0:
                    LOG.info("Diagnosed %d instruments", len(coverages))
        staged.replace(cfg.reports / "suspicious_prices.csv")
        if not coverages:
            raise ValueError("All instrument-date keys conflict; numerical audit unavailable")
        write_csv(cfg.reports / "instrument_coverage.csv", coverages, list(coverages[0]))
        write_csv(cfg.reports / "event_instrument_coverage.csv", events, list(events[0]))
        event_summary = summarize_events(events, cfg)
        # Read the completed output for concrete discontinuity examples.
        extreme_examples = query_dicts(con, """
            SELECT instrument_id,date,close_raw,previous_close_raw,
              try_cast(diagnostic_price_return AS DOUBLE) diagnostic_price_return,
              volume,source_file,source_row FROM read_csv(?,header=true)
            WHERE try_cast(diagnostic_price_return AS DOUBLE) IS NOT NULL
            ORDER BY abs(try_cast(diagnostic_price_return AS DOUBLE)) DESC,instrument_id,date LIMIT 12
        """, [str(cfg.reports / "suspicious_prices.csv")])
        write_csv(cfg.reports / "calendar_audit.csv", [{
            "date": d, "weekday": d.strftime("%A"),
            "calendar_source": calendar_source,
        } for d in calendar], ["date", "weekday", "calendar_source"])
        valid_counts = sorted(r["valid_price_observations"] for r in coverages)
        distribution = Counter()
        for row in coverages:
            n = row["valid_price_observations"]
            bucket = "0" if n == 0 else "1-149" if n < 150 else "150-999" if n < 1000 else "1000-2499" if n < 2500 else "2500+"
            distribution[bucket] += 1
        summary = {
            "audit_version": 1, "scope": "Phase 1; no final cleaning or sample selection",
            "software": {"python": platform.python_version(), **{
                name: version(name) for name in ("openpyxl", "pyarrow", "duckdb", "matplotlib")}},
            "implementation_sha256": {p.name: sha256(p) for p in sorted(Path(__file__).parent.glob("*.py"))},
            "uv_lock_sha256": sha256(cfg.root / "uv.lock") if (cfg.root / "uv.lock").exists() else None,
            "requested_start": START.isoformat(), "requested_end": END.isoformat(),
            "manifest_sha256": sha256(manifest_path) if manifest_path.exists() else None,
            "manifest_missing": not manifest_path.exists(),
            "inputs": metadata + ([index_meta] if index_meta else []),
            "input_failures": failures,
            "missing_batches": [r["source_file"] for r in batches if not r["exists"]],
            "unexpected_batches": [r["source_file"] for r in batches if r["unexpected_batch"]],
            "all_batch_calendars_match": all(r.get("calendar_matches_first_batch", False) for r in batches),
            "manifest_all_counts_match": all(r.get("manifest_counts_match", False) for r in batches),
            "calendar": calendar_summary(calendar), "calendar_source": calendar_source,
            "batch_audit": batches, "global": global_stats, "duplicates": duplicates,
            "batch_instrument_appearances": sum(r.get("instruments", 0) for r in batches),
            "latest_recorded_screener_total": next((manifest[k]["screener_total"]
                for k in sorted(manifest, key=int, reverse=True) if "screener_total" in manifest[k]), None),
            "market_index": market, "diagnostic_totals": dict(totals),
            "market_event_coverage": market_events, "market_index_processed": market_output,
            "market_missing_session_activity": missing_activity,
            "instruments_diagnosed": len(coverages),
            "instruments_without_valid_prices": sum(r["valid_price_observations"] == 0 for r in coverages),
            "instruments_all_fields_missing": sum(r["all_fields_missing_rows"] == r["observations"] for r in coverages),
            "instruments_without_positive_volume": sum(r["positive_volume_days"] == 0 for r in coverages),
            "instruments_with_valid_prices": sum(r["valid_price_observations"] > 0 for r in coverages),
            "instruments_with_positive_volume": sum(r["positive_volume_days"] > 0 for r in coverages),
            "instruments_with_prices_but_no_positive_volume": sum(
                r["valid_price_observations"] > 0 and r["positive_volume_days"] == 0 for r in coverages),
            "manifest_missing_name_candidates": missing_name_candidates,
            "fractional_close_observations": sum(r["observations"] for r in fractional_closes),
            "fractional_close_instruments": len(fractional_closes),
            "extreme_examples": extreme_examples,
            "price_coverage_distribution": dict(distribution),
            "median_valid_price_observations": valid_counts[len(valid_counts)//2],
            "same_name_multiple_instrument_groups": len(names), "same_name_examples": names[:15],
            "instruments_with_multiple_names": len(multi_names), "instrument_suffixes": suffixes,
            "events": event_summary,
            "assumptions": {
                "price_validity": "finite and strictly positive; numerical validity only",
                "stale_run_sessions": cfg.stale_run, "extreme_absolute_return": cfg.extreme_threshold,
                "return_thresholds": [.1, .2, .3, .5, 1.],
                "returns": "Adjacent calendar sessions, two valid closes; no gap bridging; diagnostic raw price returns",
                "stale": "Unchanged adjacent positive price with current volume nonpositive/missing, or >=20 constant sessions with current volume nonpositive/missing; a candidate only",
                "duplicates": "Raw copies retained; audit counts identical keys once by file/sheet/row; conflicting keys excluded from numeric diagnostics",
                "events": "Dates provisional; near means [-10,+10]; estimation [-250,-30] inclusive (221 return dates), requiring price at -251; full windows require every return",
                "units": "unverified", "company_price_adjustments": "unverified",
                "eligibility": "No historical eligibility inferred from full-period summaries",
            },
        }
    finally:
        con.close()
    from .reporting import write_report
    write_report(cfg, summary, coverages)
    # Hash report artifacts; summary is the completion marker for this generation.
    summary["report_sha256"] = {p.name: sha256(p) for p in sorted(cfg.reports.iterdir())
                                if p.suffix in {".csv", ".md", ".svg", ".png"}}
    pending = cfg.reports / "audit_summary.pending.json"
    pending.write_text(json.dumps(summary, indent=2, sort_keys=True, default=str, allow_nan=False) + "\n")
    pending.replace(cfg.reports / "audit_summary.json")
    LOG.info("Audit complete. Main report: %s", cfg.reports / "data_audit.md")
    return summary
