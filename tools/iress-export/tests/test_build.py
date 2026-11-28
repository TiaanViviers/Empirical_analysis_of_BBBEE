"""Approved transformation invariants and build failure modes on synthetic sources."""

from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path

import pyarrow.parquet as pq
import pytest
from openpyxl import Workbook

from iress_data.build import build
from iress_data.config import Config
from iress_data.ingest import sha256
from iress_data.processed_validation import verify_processed
from iress_data.transform import as_int64, transform_records

HEADERS=["Mnemonic","Company","Date","Close","Number Of Trades","Volume"]


def save(path: Path, rows: list[list]) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    w=Workbook()
    for row in [HEADERS]+rows:
        w.active.append(row)
    w.save(path)
    w.close()


@pytest.fixture
def source_project(tmp_path: Path) -> Config:
    cfg=replace(Config.from_root(tmp_path),expected_batches=2,chunk_rows=7)
    days=[date(2017,6,1)+timedelta(days=i) for i in range(32)
          if (date(2017,6,1)+timedelta(days=i)).weekday()<5]
    a=[]
    for i,d in enumerate(days):
        price=None if i==3 else 0 if i==5 else -2 if i==6 else 10 if i<10 else 25
        a.append(["A:XJSE:EQU","A original",d,price,0,0])
    b=[["B:XJSE:EQU","B entirely empty",d,None,None,None] for d in days]
    c=[["C:XJSE:EQU","C zero history",d,0,-1,0] for d in days]
    drows=[["D:XJSE:EQU","D positive",d,100+i,1,100] for i,d in enumerate(days)]
    save(cfg.exports/"jse_prices_01.xlsx",a+b+c)
    save(cfg.exports/"jse_prices_02.xlsx",a+drows)
    save(cfg.exports/"J203_prices.xlsx",[["J203:XJSE:IND","All Share",d,1000+i,0,100] for i,d in enumerate(days)])
    return cfg


def test_approved_build_reconciliation_and_repeat(source_project: Config) -> None:
    cfg=source_project
    originals={p.name:sha256(p) for p in cfg.exports.glob("*.xlsx")}
    first=build(cfg)
    v=verify_processed(cfg)
    n=len(first["calendar"]["dates"])
    assert v["canonical_rows"]==4*n and v["raw_source_rows"]==5*n
    assert v["identical_duplicate_extra_rows"]==n
    assert v["observed_rows"]==3*n and v["empty_placeholders"]==n
    assert v["instruments_with_no_valid_prices"]==2
    instruments=pq.read_table(cfg.root/"data/processed/instruments.parquet").to_pylist()
    a=next(r for r in instruments if r["instrument_id"]=="A:XJSE:EQU")
    assert a["source_batches"]==[1,2] and a["duplicate_extra_rows"]==n
    assert all(r["listing_date"] is None and r["isin"] is None for r in instruments)
    observed=pq.read_table(cfg.root/"data/processed/prices_observed.parquet").to_pylist()
    assert any(r["close_raw"]==0 and r["volume"]==0 for r in observed)
    assert any(r["number_of_trades"]==-1 for r in observed)
    assert {p.name:sha256(p) for p in cfg.exports.glob("*.xlsx")}==originals
    second=build(cfg)
    assert {k:v["sha256"] for k,v in first["datasets"].items()}=={k:v["sha256"] for k,v in second["datasets"].items()}
    assert first["validation"]==second["validation"]


def test_conflicting_values_stop_before_publication(source_project: Config) -> None:
    cfg=source_project
    path=cfg.exports/"jse_prices_02.xlsx"
    from openpyxl import load_workbook
    w=load_workbook(path)
    w.active.cell(2,4,999)
    w.save(path)
    w.close()
    with pytest.raises(ValueError,match="conflicting instrument-date"):
        build(cfg)
    assert not (cfg.root/"data/processed/build_manifest.json").exists()
    assert (cfg.reports/"build_conflicting_observations.csv").stat().st_size>200


def test_quantities_never_rounded(source_project: Config) -> None:
    for value in (1.5,float("nan"),float("inf"),2**63):
        with pytest.raises(ValueError):
            as_int64(value)
    assert as_int64(None) is None and as_int64(0)==0 and as_int64(-3)==-3
    cfg=source_project
    path=cfg.exports/"jse_prices_01.xlsx"
    from openpyxl import load_workbook
    w=load_workbook(path)
    # The empty instrument has no duplicate copies, isolating quantity conversion.
    n=22
    w.active.cell(n+2,6,1.5)
    w.save(path)
    w.close()
    with pytest.raises(ValueError,match="Int64 without rounding"):
        build(cfg)


def test_trailing_flags_have_no_future_dependence(tmp_path: Path) -> None:
    cfg=replace(Config.from_root(tmp_path),stale_run=3)
    days=[date(2020,1,1)+timedelta(days=i) for i in range(25)]
    rows=[{"instrument_id":"A:XJSE:EQU","company_name":"A","date":d,"close_raw":10.,
           "volume":0.,"number_of_trades":0.,"source_batch":1,"source_file":"a.xlsx",
           "source_sheet":"Sheet","source_row":i+2,"source_sha256":"test",
           "duplicate_copy_count":1,"parse_issues":"","unparsed_values":""} for i,d in enumerate(days)]
    full=list(transform_records(rows,days,cfg))
    prefix=list(transform_records(rows[:2],days[:2],cfg))
    assert full[:2]==prefix
    assert [r["trailing_constant_price_sessions"] for r in full[:4]]==[1,2,3,4]
    assert not full[0]["potential_stale_price"] and full[1]["potential_stale_price"]
    rows[3]["close_raw"]=None
    gap=list(transform_records(rows[:5],days[:5],cfg))
    assert gap[4]["diagnostic_price_return"] is None
    assert gap[4]["previous_price_date"]==days[2] and gap[4]["price_gap_sessions"]==2
    assert gap[4]["trailing_constant_price_sessions"]==1
