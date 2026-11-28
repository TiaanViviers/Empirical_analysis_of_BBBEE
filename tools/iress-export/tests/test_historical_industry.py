"""Historical source preservation, conservative identity and temporal safeguards."""
from collections import Counter
from datetime import date
import csv
import json
from pathlib import Path
import shutil

import openpyxl
import pyarrow.parquet as pq
import pytest

from iress_data.historical_industry import (
    EVENTS, EVENT_MONTHS, parse_workbook, match_record, construct_events,
    reference_records, load_variants, check_baseline, name_key, arrow_table,
)
from iress_data.historical_industry_package import preflight_sync, sync_package, regenerate_inventory, NAMES
from iress_data.package_verifier import verify, verify_historical

ROOT=Path(__file__).resolve().parents[1]
THESIS_PACKAGE = (ROOT / '../../data/part_a/source/thesis_data').resolve()


def test_all_real_workbook_rows_preserved():
    count=0
    for path in sorted((ROOT/'data/raw/jse_bulletins').glob('*.xlsx')):
        rows,audit,source=parse_workbook(path)
        book=openpyxl.load_workbook(path,read_only=True,data_only=True)
        assert len(audit)==sum(s.max_row for s in book)
        assert len(rows)==sum(a['row_disposition']=='security' for a in audit)
        actual_sheets={s.title:list(s.values) for s in book}
        for row in rows:
            actual=actual_sheets[row['worksheet']][row['source_row']-1]
            assert tuple(row[k] for k in ['historical_security_name','historical_share_code','nature_of_business_raw'])==actual[:3]
            assert row['source_sha256']==source['sha256']
        assert len({(r['worksheet'],r['source_row']) for r in rows})==len(rows)
        count+=len(rows);book.close()
    assert count==6255


def test_parser_sections_reordered_headers_and_incomplete_rows(tmp_path):
    p=tmp_path/'test.xlsx';w=openpyxl.Workbook();s=w.active;s.title='May 2017'
    s.append(['TRADING STATISTICS FOR MAY 2017'])
    s.append(['SHARE CODE','NATURE OF BUSINESS','SECURITY'])
    s.append(['ETF','Exchange Traded Funds','Some ETF'])
    s.append([None,None,None,'extra payment'])
    s.append(['SECURITY','SHARE CODE','NATURE OF BUSINESS'])
    s.append(['Operating Ltd','OPR','Gold'])
    s.append(['Unnamed code',None,None])
    s.append([None,None,'ambiguous label'])
    w.save(p)
    rows,audit,_=parse_workbook(p)
    assert len(rows)==3 and len(audit)==8
    assert rows[0]['likely_investment_product']
    assert rows[1]['mining_candidate'] and rows[1]['header_row']==5
    assert rows[2]['identity_incomplete'] and rows[2]['industry_missing']
    assert audit[-1]['row_disposition']=='ambiguous_label_only'


def test_parser_rejects_inconsistent_source_month(tmp_path):
    p=tmp_path/'bad.xlsx';w=openpyxl.Workbook();s=w.active;s.title='May 2017'
    s.append(['TRADING STATISTICS FOR JUNE 2017']);s.append(['SECURITY','SHARE CODE','NATURE OF BUSINESS']);w.save(p)
    with pytest.raises(ValueError,match='reporting month'):parse_workbook(p)


def reference(ident,name,ticker=None):
    return dict(instrument_id=ident,ticker=ticker or ident.split(':')[0],names={name},has_historical_prices_record=True)


def test_exact_ticker_needs_name_validation_and_retains_classes():
    row=dict(historical_share_code='ABC',historical_security_name='Alpha Hldgs Ltd')
    refs={'ABC:XJSE:EQU':reference('ABC:XJSE:EQU','Alpha Holdings Limited')}
    assert match_record(row,refs)['match_status']=='matched'
    row['historical_security_name']='Different Ltd'
    assert match_record(row,refs)['match_status']=='ambiguous'
    row['historical_security_name']='Alpha Hldgs Ltd Pref'
    assert match_record(row,refs)['instrument_id'] is None
    assert name_key('Alpha A')!=name_key('Alpha B')


def test_ticker_reuse_and_del_suffix_ambiguity():
    row=dict(historical_share_code='ABC',historical_security_name='Alpha Ltd')
    refs={k:reference(k,'Alpha Ltd') for k in ['ABC:XJSE:EQU','ABC_DEL:XJSE:EQU']}
    assert match_record(row,refs)['match_status']=='ambiguous'
    assert match_record(row,{'ABC_DEL:XJSE:EQU':refs['ABC_DEL:XJSE:EQU']})['match_method']=='ticker_del_suffix_validated_name'


def test_names_under_different_tickers_are_only_suggestions():
    row=dict(historical_share_code='OLD',historical_security_name='Alpha Ltd')
    result=match_record(row,{'NEW:XJSE:EQU':reference('NEW:XJSE:EQU','Alpha Ltd')})
    assert result['instrument_id'] is None and result['candidate_instrument_ids']=='NEW:XJSE:EQU'


def test_documented_variants_and_no_unlisted_rename():
    refs=reference_records(ROOT/'data/processed')
    variants=load_variants(ROOT/'metadata/historical_industry_name_variants.csv')
    row=dict(historical_share_code='AFH',historical_security_name='Alexander Forbes Grp Hldgs')
    assert match_record(row,refs)['instrument_id'] is None
    assert match_record(row,refs,variants)['match_method']=='exact_ticker_documented_name_variant'
    row=dict(historical_share_code='AEL',historical_security_name='Allied Electronics Corp A')
    assert match_record(row,refs,variants)['instrument_id'] is None


def test_source_month_event_dates_and_no_future_filling(monkeypatch):
    import iress_data.historical_industry as module
    rows=pq.read_table(ROOT/'data/processed/jse_bulletin_securities.parquet').to_pylist()
    actual=construct_events(rows)
    assert actual
    for r in actual:
        assert str(r['bulletin_month'])[:7]==EVENT_MONTHS[r['event_id']]
        assert r['bulletin_month']<r['event_date']
        assert not r['is_retrospective'] and not r['preannouncement_availability_verified']
        assert r['publication_date'] is None
    # Later snapshot cannot fill all removed 2018 observations.
    assert not [r for r in construct_events([r for r in rows if str(r['bulletin_month'])!='2018-08-01']) if r['event_id']=='mining_charter_2018']
    monkeypatch.setitem(module.EVENT_MONTHS,'mining_charter_2018','2018-09')
    with pytest.raises(ValueError,match='Post-event'):construct_events(rows)


def test_duplicate_event_instrument_never_chooses_a_label():
    rows=pq.read_table(ROOT/'data/processed/jse_bulletin_securities.parquet').to_pylist()
    r=next(r for r in rows if r['match_status']=='matched' and str(r['bulletin_month'])=='2017-05-01')
    other={**r,'nature_of_business_raw':'conflicting label','source_row':99999}
    assert not construct_events([r,other])


def test_output_unique_keys_provenance_eligible_coverage_and_baseline(tmp_path):
    manifest=json.loads((THESIS_PACKAGE/'manifest.json').read_text())
    verify_historical(THESIS_PACKAGE,manifest)
    # Recreate the immutable manifest's package-relative layout for this check.
    for folder in ("metadata", "data"):
        (tmp_path / folder).symlink_to(ROOT / folder, target_is_directory=True)
    (tmp_path / "dist").mkdir()
    (tmp_path / "dist/thesis_data").symlink_to(THESIS_PACKAGE, target_is_directory=True)
    assert check_baseline(tmp_path)
    rows=list(csv.DictReader((ROOT/'reports/historical_industry_eligible_instruments.csv').open()))
    assert len(rows)==len({(r['event_id'],r['instrument_id']) for r in rows})
    for r in rows:assert int(r['estimation_usable_returns'])>=180 and r['definition']=='current_positive_volume'
    assert json.loads((ROOT/'reports/historical_industry_summary.json').read_text())['missing_months']==['2018-09','2025-04']


def test_package_original_datasets_and_semantic_corruption(tmp_path):
    source=THESIS_PACKAGE;manifest=verify(source)
    # Only classification files are needed to exercise semantic leakage checks.
    # Symlink unchanged payloads across filesystems; replace only the test table.
    import os
    shutil.copytree(source,tmp_path/'package',copy_function=os.symlink)
    copied=tmp_path/'package'
    path=copied/'data/event_industry_classifications.parquet'
    rows=pq.read_table(path).to_pylist();rows[0]['event_date']=date(2017,5,15)
    path.unlink();pq.write_table(arrow_table(rows,event=True),path)
    with pytest.raises(ValueError,match='event/source month association|leakage'):
        verify_historical(copied,manifest)


def test_sync_rejects_independent_thesis_changes_before_writing(tmp_path):
    source=THESIS_PACKAGE
    destination=tmp_path/'thesis';destination.mkdir()
    (destination/'manifest.json').write_text('independent thesis manifest')
    baseline=ROOT/'metadata/handover_manifest_before_historical_industry.json'
    with pytest.raises(ValueError,match='Independently changed thesis'):
        preflight_sync(source,destination,baseline)
    assert (destination/'manifest.json').read_text()=='independent thesis manifest'


def test_sync_changed_files_only_and_rollback(tmp_path,monkeypatch):
    import os
    import iress_data.historical_industry_package as packaging
    source=THESIS_PACKAGE
    destination=tmp_path/'thesis'
    shutil.copytree(source,destination,copy_function=os.symlink)
    # Build a portable prior-version fixture without copying large datasets.
    for name in NAMES:(destination/'data'/name).unlink()
    for path in (destination/'documentation').glob('historical_industry*'):path.unlink()
    old=json.loads((source/'manifest.json').read_text())
    old.pop('historical_industry')
    for name in NAMES:old['datasets'].pop(name)
    (destination/'manifest.json').unlink()
    (destination/'manifest.sha256').unlink()
    regenerate_inventory(destination,old)
    baseline=tmp_path/'baseline.json';baseline.write_bytes((destination/'manifest.json').read_bytes())
    changes=preflight_sync(source,destination,baseline)
    original_names=set(json.loads(baseline.read_text())['datasets'])
    assert not any('data/'+name in changes for name in original_names)
    original_verify=packaging.verify
    calls=0
    def fail_after_transfer(path):
        nonlocal calls
        calls+=1
        if calls==3:raise RuntimeError('simulated verification failure')
        return original_verify(path)
    monkeypatch.setattr(packaging,'verify',fail_after_transfer)
    with pytest.raises(RuntimeError,match='simulated'):sync_package(source,destination,baseline)
    assert (destination/'manifest.json').read_bytes()==baseline.read_bytes()
    original_verify(destination)
    monkeypatch.setattr(packaging,'verify',original_verify)
    applied=sync_package(source,destination,baseline)
    assert applied==changes
    assert (destination/'manifest.json').read_bytes()==(source/'manifest.json').read_bytes()
    assert all((destination/'data'/name).is_symlink() for name in original_names)


def test_delisted_snapshot_does_not_exclude_historical_matches():
    snapshot=pq.read_table(ROOT/'data/processed/instrument_metadata_2026-11-23.parquet').to_pylist()
    delisted={r['instrument_id'] for r in snapshot if r['listing_status_snapshot']=='Delisted'}
    events=pq.read_table(ROOT/'data/processed/event_industry_classifications.parquet').to_pylist()
    assert '1TM:XJSE:EQU' in delisted
    assert any(r['instrument_id']=='1TM:XJSE:EQU' and r['event_id']=='mining_charter_2017' for r in events)
    assert len({r['instrument_id'] for r in events}&delisted)>50
    aee=[r for r in events if r['instrument_id']=='AEE:XJSE:EQU']
    assert len({r['nature_of_business_raw'] for r in aee})>1


@pytest.mark.parametrize('event_id,after_month',[('mining_charter_2018',date(2018,9,1)),('ee_final_2025',date(2025,4,1))])
def test_crosscheck_snapshot_never_substitutes_for_pre_event(event_id,after_month):
    rows=pq.read_table(ROOT/'data/processed/jse_bulletin_securities.parquet').to_pylist()
    earlier=next(r for r in rows if r['match_status']=='matched' and str(r['bulletin_month'])[:7]==EVENT_MONTHS[event_id])
    later={**earlier,'bulletin_month':after_month,'nature_of_business_raw':'later changed label'}
    assert not [r for r in construct_events([later]) if r['event_id']==event_id]
    both=[r for r in construct_events([earlier,later]) if r['event_id']==event_id]
    assert len(both)==1 and both[0]['nature_of_business_raw']==earlier['nature_of_business_raw']
