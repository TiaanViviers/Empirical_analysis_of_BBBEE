"""Standalone package integrity checker, copied verbatim into the handover.

Only Python's standard library and PyArrow are required. There are deliberately
no imports from the preprocessing repository and no original source reads.
"""

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

import pyarrow.compute as pc
import pyarrow.parquet as pq


def digest(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda:handle.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()


def check(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(f"Package verification failed: {message}")


def valid_isin(value: str | None) -> bool:
    if not value or re.fullmatch(r"[A-Z]{2}[A-Z0-9]{9}[0-9]", value) is None:
        return False
    digits="".join(str(ord(char)-55) if char.isalpha() else char for char in value)
    total=0
    for position,char in enumerate(reversed(digits)):
        number=int(char)*(2 if position%2 else 1)
        total+=number//10+number%10
    return total%10==0



def verify_historical(root: Path, manifest: dict) -> None:
    """Semantic checks independent of the processing repository or raw Excel."""
    from datetime import date
    import calendar
    from collections import Counter
    bulletin=pq.read_table(root/'data/jse_bulletin_securities.parquet').to_pylist()
    events=pq.read_table(root/'data/event_industry_classifications.parquet').to_pylist()
    provenance=manifest['historical_industry']
    expected={
        'mining_charter_2017':('2017-06-15','2017-05-01'),
        'mining_charter_2018':('2018-09-27','2018-08-01'),
        'ee_draft_2023':('2023-05-12','2023-04-01'),
        'ee_final_2025':('2025-04-15','2025-03-01'),
        'bbbee_draft_2026':('2026-01-29','2025-12-01'),
    }
    metadata_ids=set(pq.read_table(root/'data/instrument_metadata_2026-11-23.parquet',columns=['instrument_id']).column('instrument_id').to_pylist())
    master_ids=set(pq.read_table(root/'data/instruments.parquet',columns=['instrument_id']).column('instrument_id').to_pylist())
    sources={s['source_file']:s for s in provenance['sources']}
    inventory=json.loads((root/'documentation/source_inventory.json').read_text())
    check(inventory['historical_jse_bulletins']['sources']==provenance['sources'],'historical source inventory')
    keys={}; status_counts=Counter()
    for row in bulletin:
        key=(row['source_file'],row['worksheet'],row['source_row'])
        check(key not in keys,'unique bulletin source rows');keys[key]=row
        source=sources.get(row['source_file'])
        check(source is not None and row['source_sha256']==source['sha256'],'source workbook hash provenance')
        sheets={s['worksheet']:s for s in source['sheets']}
        sheet=sheets.get(row['worksheet'])
        check(sheet is not None,'source worksheet provenance')
        check(str(row['bulletin_month'])[:7]==sheet['bulletin_month'],'source reporting month')
        check(1<=row['header_row']<row['source_row']<=sheet['total_rows'],'source row bounds')
        check(bool(row['historical_security_name'] or row['historical_share_code']),'identifiable security preserved')
        check(row['identity_incomplete']==(not bool(row['historical_security_name'] and row['historical_share_code'])),'identity flag')
        check(row['industry_missing']==(not bool(row['nature_of_business_raw'])),'industry missing flag')
        check(row['match_status'] in {'matched','ambiguous','unmatched'},'match status vocabulary')
        if row['match_status']=='matched':
            check(row['instrument_id'] in metadata_ids,'accepted ID in metadata universe')
            check(bool(row['match_method'] and row['match_evidence']),'match evidence')
        else:check(row['instrument_id'] is None,'unresolved match excluded')
        check(row['has_historical_prices_record']==(row['instrument_id'] in master_ids),'historical-master flag')
        status_counts[row['match_status']]+=1
    check(len(bulletin)==provenance['source_securities'],'all parsed source securities')
    for source in sources.values():
        for sheet in source['sheets']:
            count=sum(r['source_file']==source['source_file'] and r['worksheet']==sheet['worksheet'] for r in bulletin)
            check(count==sheet['securities'],'worksheet record preservation')
            check(sum(sheet['row_dispositions'].values())==sheet['total_rows'],'worksheet row accounting')
    event_keys=set()
    eligible_candidates={(r['source_file'],r['worksheet'],r['source_row']):r for r in bulletin if r['match_status']=='matched' and not r['industry_missing']}
    duplicates=Counter((r['bulletin_month'],r['instrument_id']) for r in eligible_candidates.values())
    expected_keys={(eid,r['instrument_id']) for eid,(_,month) in expected.items() for r in eligible_candidates.values()
                   if str(r['bulletin_month'])==month and duplicates[(r['bulletin_month'],r['instrument_id'])]==1}
    for row in events:
        key=(row['event_id'],row['instrument_id'])
        check(key not in event_keys,'unique event/instrument');event_keys.add(key)
        check(row['event_id'] in expected,'known event')
        day,month=expected[row['event_id']]
        check(str(row['event_date'])==day and str(row['bulletin_month'])==month,'designated event/source month association')
        m=row['bulletin_month'];end=date(m.year,m.month,calendar.monthrange(m.year,m.month)[1])
        check(end<row['event_date'] and not row['is_retrospective'],'post-event classification leakage')
        check(row['publication_date'] is None and not row['preannouncement_availability_verified'],'unknown publication availability explicit')
        source=keys.get((row['source_file'],row['worksheet'],row['source_row']))
        check(source is not None,'event source row exists')
        check(all(row[k]==v for k,v in source.items()),'event values equal historical source match')
    check(event_keys==expected_keys,'all and only unambiguous designated snapshot matches')
    for name,digest_value in provenance['original_dataset_sha256'].items():
        check(digest(root/'data'/name)==digest_value,'original dataset unchanged: '+name)
    import csv
    coverage=list(csv.DictReader((root/'documentation/historical_industry_coverage.csv').open()))
    check(len(coverage)==5,'five event coverage rows')
    eligible=list(csv.DictReader((root/'documentation/historical_industry_eligible_instruments.csv').open()))
    eligible_keys=[(r['event_id'],r['instrument_id']) for r in eligible]
    check(len(eligible_keys)==len(set(eligible_keys)),'unique eligibility keys')
    for r in eligible:
        check(r['instrument_id'] in master_ids and r['event_id'] in expected,'eligible historical-price ID/event')
        check(r['definition']=='current_positive_volume' and int(r['estimation_usable_returns'])>=180 and r['benchmark_complete_caar_m10_10']=='True' and r['benchmark_required_sessions_complete']=='True','provisional denominator rules')
        check((r['has_classification']=='True')==((r['event_id'],r['instrument_id']) in event_keys),'eligible classification flag')
    for row in coverage:
        eid=row['event_id'];month=expected[eid][1]
        records=[r for r in bulletin if str(r['bulletin_month'])==month]
        check(len(records)==int(row['source_securities']),'coverage source count')
        check(sum(r['match_status']=='matched' for r in records)==int(row['securities_matched']),'coverage match count')
        denominator=int(row['eligible_price_instruments']);numerator=int(row['eligible_with_classification'])
        eligible_for_event={r['instrument_id'] for r in eligible if r['event_id']==eid}
        check(denominator==len(eligible_for_event),'provisional denominator ID count')
        check(numerator==sum((eid,ident) in event_keys for ident in eligible_for_event),'eligible classified ID count')
        check(0<=numerator<=denominator,'coverage numerator bounds')
        check(abs(float(row['coverage_pct'])-100*numerator/denominator)<0.0001,'coverage percentage')

def verify(root: Path) -> dict[str, Any]:
    root=root.resolve()
    manifest_path=root/"manifest.json"
    expected=(root/"manifest.sha256").read_text().split()[0]
    check(digest(manifest_path)==expected,"manifest checksum")
    manifest=json.loads(manifest_path.read_text())
    inventory=manifest["files"]
    actual={p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}
    check(actual==set(inventory)|{"manifest.json","manifest.sha256"},"payload inventory mismatch")
    for relative,entry in inventory.items():
        p=Path(relative)
        check(not p.is_absolute() and ".." not in p.parts,"non-portable payload path")
        path=root/p
        check(path.stat().st_size==entry["size_bytes"],f"file size: {relative}")
        check(digest(path)==entry["sha256"],f"checksum: {relative}")
    market_metadata=json.loads((root/"data/market_index.metadata.json").read_text())
    check(market_metadata["path"]=="data/market_index.parquet","portable benchmark metadata path")
    check(market_metadata["sha256"]==digest(root/market_metadata["path"]),"benchmark metadata checksum")
    for name,entry in manifest["datasets"].items():
        path=root/"data"/name
        parquet=pq.ParquetFile(path)
        schema=parquet.schema_arrow
        recorded=[{"name":f.name,"type":str(f.type),"nullable":f.nullable} for f in schema]
        described=[{k:f[k] for k in ("name","type","nullable")} for f in entry["columns"]]
        check(recorded==described,f"schema: {name}")
        check(parquet.metadata.num_rows==entry["rows"],f"Parquet row count: {name}")
        check(digest(path)==entry["sha256"],f"dataset checksum: {name}")
        identifiers=set()
        rows=0
        start=end=None
        key="index_id" if name=="market_index.parquet" else "instrument_id"
        historical=name in {"jse_bulletin_securities.parquet", "event_industry_classifications.parquet"}
        first=("event_date" if name=="event_industry_classifications.parquet" else
               "bulletin_month" if historical else
               "snapshot_date" if name.startswith("instrument_metadata_") else
               "date" if "date" in schema.names else "observed_price_start")
        last=("event_date" if name=="event_industry_classifications.parquet" else
              "bulletin_month" if historical else
              "snapshot_date" if name.startswith("instrument_metadata_") else
              "date" if "date" in schema.names else "observed_price_end")
        for batch in parquet.iter_batches(batch_size=50_000):
            rows+=batch.num_rows
            for field,column in zip(schema,batch.columns,strict=True):
                if not field.nullable:
                    check(column.null_count==0,f"required column: {name}/{field.name}")
            identifiers.update(pc.unique(batch.column(schema.get_field_index(key))).to_pylist())
            lo=pc.min(batch.column(schema.get_field_index(first))).as_py()
            hi=pc.max(batch.column(schema.get_field_index(last))).as_py()
            if lo is not None:
                start=lo if start is None else min(lo,start)
            if hi is not None:
                end=hi if end is None else max(hi,end)
        check(rows==entry["rows"],f"readable rows: {name}")
        identifiers.discard(None)
        check(len(identifiers)==entry["unique_instruments"],f"distinct instrument count: {name}")
        check((str(start) if start else None)==entry["date_start"],f"start date: {name}")
        check((str(end) if end else None)==entry["date_end"],f"end date: {name}")
    metadata_names=[name for name in manifest["datasets"] if name.startswith("instrument_metadata_")]
    check(len(metadata_names)<=1,"multiple dated metadata datasets in one package")
    if metadata_names:
        name=metadata_names[0]
        table=pq.read_table(root/"data"/name)
        rows=table.to_pylist()
        master=set(pq.read_table(root/"data/instruments.parquet",columns=["instrument_id"])
                   .column("instrument_id").to_pylist())
        ids=[row["instrument_id"] for row in rows]
        check(len(rows)==1872 and len(set(ids))==1872 and None not in ids,
              "metadata row count and primary key")
        check(len(master)==1869 and master.issubset(ids),"metadata covers historical master")
        extra=set(ids)-master
        expected_extra={"IMRP17:XJSE:EQU","IMRP18:XJSE:EQU","PBT_DEL:XJSE:EQU"}
        check(extra==expected_extra,"three Screener-only IDs")
        check(all(row["has_historical_prices_record"]==(row["instrument_id"] in master)
                  for row in rows),"historical-master match flags")
        check(all(row["isin_valid"]==valid_isin(row["isin_raw"]) for row in rows),
              "ISIN format and check digit flags")
        check(sum(row["isin_valid"] for row in rows)==1492,"valid ISIN count")
        check(sum(not row["isin_valid"] for row in rows)==380,"nonstandard ISIN count")
        check(all(str(row["snapshot_date"])=="2026-11-23" for row in rows),
              "metadata snapshot date")
        provenance=manifest["instrument_metadata_snapshot"]
        check(provenance["source_csv_sha256"]==
              (table.schema.metadata or {}).get(b"source_csv_sha256",b"").decode(),
              "metadata source CSV provenance")
    if "historical_industry" in manifest:
        verify_historical(root,manifest)
    print(f"PASS: {len(inventory)} payload files; {len(manifest['datasets'])} readable Parquet datasets; all checksums, schemas, counts and date coverage agree.")
    return manifest


if __name__=="__main__":
    package_root=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
    verify(package_root)
