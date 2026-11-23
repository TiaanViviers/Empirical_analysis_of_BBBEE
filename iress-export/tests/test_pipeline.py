"""Synthetic tests target financial-data failure modes, not implementation mirrors."""

from dataclasses import replace
import csv
from datetime import date, datetime, timedelta
from pathlib import Path

import pyarrow.parquet as pq
import pytest
from openpyxl import Workbook
from openpyxl.utils.datetime import CALENDAR_WINDOWS_1900

from iress_data.audit import (create_views, connect, event_diagnostics,
                              index_audit, instrument_diagnostics, run_audit)
from iress_data.benchmark import MARKET_SCHEMA, return_availability, write_market_source
from iress_data.config import Config
from iress_data.ingest import SCHEMA, ingest, parse_date, parse_number, sha256
from iress_data.validation import adjacent_return, calendar_summary
from iress_data.verify import verify

HEADERS = ["Mnemonic", "Company", "Date", "Close", "Number Of Trades", "Volume"]


def workbook(path: Path, rows: list[list], headers: list[str] = HEADERS) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    w = Workbook()
    s = w.active
    s.append(headers)
    for row in rows:
        s.append(row)
    w.save(path)
    w.close()


def record(d: date, price: float | None, volume: float | None,
           ident: str = "A:XJSE:EQU") -> dict:
    return {"instrument_id": ident, "company_name": "A", "date": d,
            "close_raw": price, "volume": volume, "number_of_trades": None,
            "source_file": "jse_prices_01.xlsx", "source_sheet": "Sheet", "source_batch": 1,
            "source_row": 2, "parse_issues": "", "unparsed_values": ""}


def test_date_and_numeric_parser() -> None:
    assert parse_number(None) == (None, None)
    assert parse_number(0) == (0., None)
    assert parse_number("NA") == (None, "invalid_numeric")
    assert parse_number("1,000") == (None, "invalid_numeric")  # no locale guess
    assert parse_number(float("inf"))[1] == "nonfinite_numeric"
    assert parse_date(42373, CALENDAR_WINDOWS_1900) == date(2016,1,4)
    with pytest.raises(ValueError):
        parse_date(datetime(2020,1,1,12), CALENDAR_WINDOWS_1900)
    with pytest.raises(ValueError):
        parse_date("01/02/03", CALENDAR_WINDOWS_1900)


def test_ingestion_retains_zeros_tokens_placeholders_and_cache(tmp_path: Path) -> None:
    cfg = Config.from_root(tmp_path)
    p = cfg.exports / "jse_prices_01.xlsx"
    workbook(p, [["A:XJSE:EQU", "A", date(2020,1,2), None, None, None],
                 ["A:XJSE:EQU", "A", date(2020,1,3), 0, 0, 0],
                 ["A:XJSE:EQU", "A", date(2020,1,6), "bad", -1, -10]])
    digest = sha256(p)
    first = ingest(p, cfg)
    output = cfg.intermediate / "jse_prices_01.parquet"
    rows = pq.read_table(output).to_pylist()
    assert pq.read_schema(output).equals(SCHEMA)
    assert rows[0]["close_raw"] is None and rows[1]["close_raw"] == 0
    assert rows[2]["volume"] == -10 and "bad" in rows[2]["unparsed_values"]
    assert [r["source_row"] for r in rows] == [2,3,4]
    stamp = output.stat().st_mtime_ns
    assert ingest(p, cfg) == first
    assert output.stat().st_mtime_ns == stamp
    assert sha256(p) == digest
    # Corrupt a cached artifact: a new read repairs it rather than trusting it.
    output.write_bytes(b"corrupt")
    ingest(p, cfg)
    assert pq.ParquetFile(output).metadata.num_rows == 3


def test_invalid_workbook_not_accepted(tmp_path: Path) -> None:
    cfg = Config.from_root(tmp_path)
    p = cfg.exports / "jse_prices_01.xlsx"
    workbook(p, [[None,"A",date(2020,1,2),1,1,1]])
    with pytest.raises(ValueError, match="Mnemonic"):
        ingest(p, cfg)
    assert not list(cfg.intermediate.glob("*.pending.parquet"))
    workbook(p, [], headers=["unexpected"])
    with pytest.raises(ValueError, match="headers"):
        ingest(p, cfg)


def test_identical_duplicates_and_conflicts(tmp_path: Path) -> None:
    cfg = replace(Config.from_root(tmp_path), expected_batches=2)
    a = cfg.exports / "jse_prices_01.xlsx"
    b = cfg.exports / "jse_prices_02.xlsx"
    rows = [["A:XJSE:EQU","A",date(2020,1,2),10,1,100],
            ["A:XJSE:EQU","A",date(2020,1,3),11,1,100]]
    workbook(a, rows)
    workbook(b, [rows[0], ["A:XJSE:EQU","A",date(2020,1,3),12,1,100]])
    ingest(a,cfg)
    ingest(b,cfg)
    con = connect(cfg)
    try:
        create_views(con, sorted(cfg.intermediate.glob("*.parquet")))
        assert con.execute("SELECT variants FROM duplicate_keys ORDER BY date").fetchall() == [(1,),(2,)]
        assert con.execute("SELECT count(*) FROM raw").fetchone()[0] == 4
        assert con.execute("SELECT count(*) FROM diagnostic").fetchone()[0] == 1
        assert con.execute("SELECT source_file FROM diagnostic").fetchone()[0] == a.name
    finally:
        con.close()
    run_audit(cfg)
    with (cfg.reports/'instrument_coverage.csv').open() as handle:
        audited = next(csv.DictReader(handle))
    assert audited['source_batches'] == '1,2'
    assert audited['raw_source_rows'] == '4' and audited['observations'] == '1'
    assert audited['conflicting_date_keys'] == '1'


def test_missing_gap_stale_and_constant_prices(tmp_path: Path) -> None:
    cfg = replace(Config.from_root(tmp_path), stale_run=3)
    days = [date(2020,1,6)+timedelta(days=i) for i in range(6)]
    rows = [record(days[0],10.,100.), record(days[1],10.,0.), record(days[2],10.,0.),
            record(days[3],None,None), record(days[4],30.,0.), record(days[5],60.,0.)]
    coverage, suspicious, series = instrument_diagnostics(rows,days,cfg)
    assert series["returns"] == [None,0.,0.,None,None,1.]
    assert coverage["longest_constant_price_sessions"] == 3
    assert coverage["constant_price_run"] == 3
    assert coverage["potential_stale_price"] == 2
    assert coverage["price_change_zero_volume"] == 1
    assert coverage["missing_close"] == 1 and coverage["zero_volume_days"] == 4
    assert adjacent_return(10.,30.,0,2) is None
    assert adjacent_return(0.,30.,0,1) is None
    assert any("extreme_price_change" in r["flags"] for r in suspicious)


def test_absent_calendar_session_breaks_returns(tmp_path: Path) -> None:
    days = [date(2020,1,6),date(2020,1,7),date(2020,1,8)]
    coverage, _, series = instrument_diagnostics([record(days[0],10.,1.),record(days[2],20.,1.)],days,Config.from_root(tmp_path))
    assert series["returns"] == [None,None,None]
    assert coverage["absent_calendar_sessions"] == 1


def test_bad_values_flagged_and_never_adjusted(tmp_path: Path) -> None:
    days = [date(2020,1,6)+timedelta(days=i) for i in range(4)]
    rows = [record(days[0],-10.,-1.),record(days[1],0.,0.),
            record(days[2],float('inf'),0.),record(days[3],20.,1.)]
    coverage, suspicious, series = instrument_diagnostics(rows,days,Config.from_root(tmp_path))
    assert coverage['negative_price'] == 1 and coverage['negative_volume'] == 1
    assert coverage['zero_price'] == 1 and coverage['nonfinite_price'] == 1
    assert coverage['valid_price_observations'] == 1
    assert series['returns'] == [None]*4
    assert suspicious[0]['close_raw'] == -10.


def test_monthly_benchmark_detected() -> None:
    result = calendar_summary([date(2020,1,31),date(2020,2,29),date(2020,3,31)])
    assert result["frequency"] == "monthly"
    assert result["weekend_dates"] == 1 and result["calendar_month_ends"] == 3


def test_event_estimation_window_and_no_future_eligibility() -> None:
    start = date(2016,1,1)
    days = [start+timedelta(days=i) for i in range(1000) if (start+timedelta(days=i)).weekday()<5]
    def series(n: int) -> dict:
        return {"valid": [True]*n, "positive_volume": [True]*n, "returns": [None]+[0.01]*(n-1)}
    records = event_diagnostics("A",series(len(days)),days,"proxy")
    event = next(r for r in records if r["event_id"] == "mining_charter_2017" and r["definition"] == "both_positive_volume")
    assert event["estimation_usable_returns"] == 221
    assert event["complete_event_0_5"]
    origin = days.index(date(2017,6,15))
    cut = days[:origin+11]
    shorter = event_diagnostics("A",series(len(cut)),cut,"proxy")
    earlier = next(r for r in shorter if r["event_id"] == event["event_id"] and r["definition"] == event["definition"])
    assert earlier == event
    bad = series(len(days))
    bad["positive_volume"][origin-1] = False
    limited = event_diagnostics("A",bad,days,"proxy")
    both = next(r for r in limited if r["event_id"] == event["event_id"] and r["definition"] == "both_positive_volume")
    price = next(r for r in limited if r["event_id"] == event["event_id"] and r["definition"] == "adjacent_prices")
    assert not both["complete_event_0_1"] and price["complete_event_0_1"]


def test_small_end_to_end_reports_and_verification(tmp_path: Path) -> None:
    cfg = replace(Config.from_root(tmp_path), expected_batches=1)
    days = [date(2017,6,14),date(2017,6,15),date(2017,6,16)]
    workbook(cfg.exports/"jse_prices_01.xlsx",[
        [ident,ident,d,10 if ident=="A" else None,1 if ident=="A" else None,100 if ident=="A" else None]
        for ident in ("A","B") for d in days])
    workbook(cfg.exports/"J203_prices.xlsx",[["J203:XJSE:IND","All Share",date(2017,6,30),100,101,99,100,1]],
             ["Mnemonic","Company","Date","Close","High","Low","Open","Volume"])
    first = run_audit(cfg)
    assert first["global"]["raw_rows"] == 6
    assert first["instruments_all_fields_missing"] == 1
    assert not first["market_index"]["daily_benchmark_validated"]
    assert any("PASS" in message for message in verify(cfg))
    assert (cfg.reports/"conflicting_observations.csv").read_text().count("\n") == 1
    second = run_audit(cfg)
    assert second == first
    (cfg.reports/"instrument_coverage.csv").write_text("modified")
    with pytest.raises(ValueError,match="report modified"):
        verify(cfg)


def test_missing_input_is_reported_not_silently_accepted(tmp_path: Path) -> None:
    cfg = replace(Config.from_root(tmp_path), expected_batches=2)
    workbook(cfg.exports/'jse_prices_01.xlsx',[
        ['A','A',date(2017,6,14),10,1,1],['A','A',date(2017,6,15),11,1,1],
        ['A','A',date(2017,6,16),12,1,1]])
    summary = run_audit(cfg)
    assert summary['missing_batches'] == ['jse_prices_02.xlsx']
    assert 'J203_prices.xlsx' in summary['input_failures']
    assert not summary['market_index']['daily_benchmark_validated']
    with pytest.raises(ValueError,match='missing or rejected inputs'):
        verify(cfg)


@pytest.mark.parametrize('layout',['flat','ohlc'])
def test_daily_benchmark_layouts_and_source_preservation(tmp_path: Path, layout: str) -> None:
    cfg=Config.from_root(tmp_path)
    cfg.reports.mkdir(parents=True)
    days=[date(2020,1,6),date(2020,1,7),date(2020,1,8)]
    if layout=='flat':
        headers=HEADERS
        rows=[['J203:XJSE:IND','All Share',d,100+i,0,1000] for i,d in enumerate(days)]
    else:
        headers=['Mnemonic','Company','Date','Close','High','Low','Open','Volume']
        rows=[['J203:XJSE:IND','All Share',d,100+i,105,99,100,1000] for i,d in enumerate(days)]
    p=cfg.exports/'J203_prices.xlsx'
    workbook(p,rows,headers)
    digest=sha256(p)
    metadata=ingest(p,cfg)
    audit=index_audit(cfg,metadata,days,None)
    assert audit['daily_frequency_validated'] and audit['daily_benchmark_validated']
    output=write_market_source(cfg,audit)
    result=pq.read_table(cfg.root/output['path'])
    assert result.schema.equals(MARKET_SCHEMA)
    values=result.to_pylist()
    assert [r['close_raw'] for r in values]==[100,101,102]
    assert [r['is_adjacent_to_previous_session'] for r in values]==[False,True,True]
    assert all(r['return_variant'] is None for r in values)
    assert sha256(p)==digest


def test_daily_benchmark_gap_is_preserved_without_bridging(tmp_path: Path) -> None:
    cfg=Config.from_root(tmp_path)
    cfg.reports.mkdir(parents=True)
    days=[date(2020,1,6)+timedelta(days=i) for i in range(5)]
    observed=[days[0],days[1],days[3],days[4]]
    p=cfg.exports/'J203_prices.xlsx'
    workbook(p,[['J203:XJSE:IND','All Share',d,100+i,0,1000] for i,d in enumerate(observed)])
    metadata=ingest(p,cfg)
    audit=index_audit(cfg,metadata,days,None)
    assert audit['daily_frequency_validated'] and not audit['calendar_complete']
    assert audit['status']=='validated_daily_with_gaps'
    assert audit['missing_company_dates']==['2020-01-08']
    output=write_market_source(cfg,audit)
    values=pq.read_table(cfg.root/output['path']).to_pylist()
    assert len(values)==4
    assert [r['is_adjacent_to_previous_session'] for r in values]==[False,True,False,True]
    records=pq.read_table(cfg.intermediate/'J203_prices.parquet').to_pylist()
    assert return_availability(records,days)==[False,True,False,False,True]


@pytest.mark.parametrize('problem',['monthly','duplicate','wrong_identity','invalid_level'])
def test_unsuitable_benchmark_never_produced_as_daily(tmp_path: Path,problem: str) -> None:
    cfg=Config.from_root(tmp_path)
    cfg.reports.mkdir(parents=True)
    days=[date(2020,1,6),date(2020,1,7),date(2020,1,8)]
    observed=[date(2020,1,31),date(2020,2,29),date(2020,3,31)] if problem=='monthly' else days
    rows=[['OTHER' if problem=='wrong_identity' else 'J203:XJSE:IND','All Share',d,
           None if problem=='invalid_level' and i==1 else 100+i,0,1000] for i,d in enumerate(observed)]
    if problem=='duplicate': rows.append(rows[-1])
    p=cfg.exports/'J203_prices.xlsx'
    workbook(p,rows)
    metadata=ingest(p,cfg)
    audit=index_audit(cfg,metadata,days,None)
    assert not audit['daily_frequency_validated']
    assert write_market_source(cfg,audit) is None
    assert not (cfg.root/'data/processed/market_index.parquet').exists()


def test_market_pairing_needs_close_before_window() -> None:
    start=date(2016,1,1)
    days=[start+timedelta(days=i) for i in range(1000) if (start+timedelta(days=i)).weekday()<5]
    origin=days.index(date(2017,6,15))
    rows=[record(d,100.,0.,'J203:XJSE:IND') for i,d in enumerate(days) if i!=origin-11]
    available=return_availability(rows,days)
    series={'valid':[True]*len(days),'positive_volume':[True]*len(days),'returns':[None]+[.01]*(len(days)-1)}
    event=next(r for r in event_diagnostics('A',series,days,'partial',available)
               if r['event_id']=='mining_charter_2017' and r['definition']=='adjacent_prices')
    assert event['complete_caar_m10_10']
    assert not event['benchmark_complete_caar_m10_10']
    assert event['benchmark_estimation_usable_returns']==221
