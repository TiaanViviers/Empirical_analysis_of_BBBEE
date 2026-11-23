"""Incremental, verified historical-classification handover and guarded synchronization."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import tempfile

import pyarrow.parquet as pq

from .historical_industry import check_baseline, write_json
from .ingest import sha256
from .package_verifier import verify

NAMES=('jse_bulletin_securities.parquet','event_industry_classifications.parquet')
REPORT_NAMES=('historical_industry_coverage.csv','historical_industry_manual_review.csv','historical_industry_bulletin_differences.csv','historical_industry_eligible_instruments.csv')


def dataset_entry(path):
    table=pq.read_table(path);event=path.name==NAMES[1]
    dates=table.column('event_date' if event else 'bulletin_month').to_pylist()
    ids=set(table.column('instrument_id').to_pylist())-{None}
    return dict(filename=path.name,path='data/'+path.name,dataset_version='1.0.0',rows=len(table),
        unique_instruments=len(ids),date_coverage_basis='event_date' if event else 'bulletin_month',
        date_start=str(min(dates)) if dates else None,date_end=str(max(dates)) if dates else None,
        primary_key=['event_id','instrument_id'] if event else ['source_file','worksheet','source_row'],
        purpose='Provisional pre-event historical JSE Bulletin labels' if event else 'All identifiable historical Bulletin security records and reconciliation',
        sha256=sha256(path),size_bytes=path.stat().st_size,
        columns=[dict(name=f.name,type=str(f.type),nullable=f.nullable,description=FIELD_DOCS[f.name]) for f in table.schema])


FIELD_DOCS={
    'historical_security_name':'Exact source SECURITY cell, including original case/spacing; null if absent.',
    'historical_share_code':'Exact source SHARE CODE cell; not a permanent identifier.',
    'nature_of_business_raw':'Exact historical JSE Bulletin label; no asserted ICB equivalence.',
    'source_file':'Original workbook filename; raw workbook excluded from portable package.',
    'source_sha256':'SHA-256 of unchanged original workbook, also recorded in source inventory.',
    'worksheet':'Exact original worksheet title.', 'source_row':'1-based original Excel row.',
    'header_row':'1-based applicable section header row.',
    'security_type_rule':'Semicolon-separated explicit source-label/name rules; empty means no rule fired.',
    'instrument_id':'Accepted exact IRESS mnemonic; null for unresolved bulletin rows.',
    'match_status':'matched, ambiguous or unmatched; no inferred historical status.',
    'match_method':'Exact ticker plus validated normalized name or documented display variant; _DEL variant requires validation; unresolved methods and duplicate-ID/code conflicts enter review.',
    'match_confidence':'high_label_concordance or unresolved; not independent historical identity verification.',
    'match_evidence':'Human-readable accepted label evidence or unresolved reason.',
    'candidate_instrument_ids':'Semicolon-separated candidates, including unaccepted review suggestions.',
    'bulletin_month':'Reporting month encoded as first day; not publication date.',
    'identity_incomplete':'Missing name or share code; preserved for review.',
    'industry_missing':'No nonempty raw industry label.',
    'likely_investment_product':'Exact explicit product-label rule; no row exclusion.',
    'likely_non_company_security':'Product, preference, other security labels or explicit name class marker; diagnostic only.',
    'mining_candidate':'Exact enumerated mining/metal source labels; not confirmed policy applicability.',
    'has_historical_prices_record':'Accepted ID occurs in 1,869-row historical-price master; false if unresolved or metadata-only.',
    'event_id':'Provisional event key reused from existing event audit.',
    'event_date':'Provisional event date; no new date research performed.',
    'publication_date':'Unknown (all null); no publication dates invented.',
    'preannouncement_availability_verified':'False throughout; reporting month precedes event but publication availability is unverified.',
    'is_retrospective':'False; no post-event classifications included or used for filling.',
    'event_date_provisional':'True; existing event dates require separate confirmation.',
    'quality_flags':'Semicolon-separated publication/identity limitations and non-company screening flags.',
}


def regenerate_inventory(stage,manifest):
    manifest['files']={p.relative_to(stage).as_posix():dict(size_bytes=p.stat().st_size,sha256=sha256(p))
        for p in sorted(stage.rglob('*')) if p.is_file() and p.name not in {'manifest.json','manifest.sha256'}}
    write_json(stage/'manifest.json',manifest)
    (stage/'manifest.sha256').write_text(sha256(stage/'manifest.json')+'  manifest.json\n')


def append_section(path,title,body):
    content=path.read_text()
    marker='\n## '+title+'\n'
    if marker in content:content=content.split(marker)[0]
    path.write_text(content.rstrip()+marker+'\n'+body.rstrip()+'\n')


def augment_package(root,metrics):
    check_baseline(root)
    package=root/'dist/thesis_data';old=verify(package)
    stage=package.with_name(package.name+'.historical_staging')
    previous=package.with_name(package.name+'.historical_swap')
    if stage.exists() or previous.exists():raise ValueError('Historical staging/swap path already exists')
    def copy_file(source,dest):
        # Large unchanged data files share storage during staging; docs are copied.
        if Path(source).parent.name=='data':os.link(source,dest)
        else:shutil.copy2(source,dest)
    shutil.copytree(package,stage,copy_function=copy_file)
    try:
        for name in NAMES:
            target=stage/'data'/name
            target.unlink(missing_ok=True)
            shutil.copy2(root/'data/processed'/name,target)
        docs=stage/'documentation'
        shutil.copy2(root/'reports/historical_industry_matching.md',docs/'historical_industry_classifications.md')
        for name in REPORT_NAMES:shutil.copy2(root/'reports'/name,docs/name)
        shutil.copy2(Path(__file__).with_name('package_verifier.py'),docs/'verify_package.py')
        manifest=json.loads((stage/'manifest.json').read_text())
        manifest['dataset_version']='1.2.0'
        manifest['package_created_at_utc']=datetime.now(timezone.utc).isoformat()
        manifest['historical_industry']={**metrics,'events':[
            dict(event_id=c['event_id'],event_date=str(c['event_date']),bulletin_month=str(c['bulletin_month'])) for c in metrics['coverage']],
            'original_dataset_sha256':{n:e['sha256'] for n,e in old['datasets'].items() if n not in NAMES},
            'availability_verified':False}
        for name in NAMES:manifest['datasets'][name]=dataset_entry(stage/'data'/name)
        inventory=json.loads((docs/'source_inventory.json').read_text())
        inventory['historical_jse_bulletins']=dict(provider='JSE Monthly Bulletin',raw_workbooks_included=False,sources=metrics['sources'],missing_requested_months=metrics['missing_months'])
        write_json(docs/'source_inventory.json',inventory)
        readme=stage/'README.md'
        readme.write_text(readme.read_text().replace('Data version **1.1.0**','Data version **1.2.0**').replace('because the six datasets have different schemas','because the eight datasets have different schemas'))
        append_section(readme,'Historical JSE Bulletin classifications',
            f"Added `data/{NAMES[0]}` ({metrics['source_securities']:,} security/month rows) and `data/{NAMES[1]}` (one accepted instrument/event). "
            "[Historical classification documentation](documentation/historical_industry_classifications.md) defines the labels, source dates, matching, mining candidates and provisional event coverage. "
            "Historical labels are now partially available; earlier references to absent historical sectors mean verified comprehensive sector/ICB histories remain unavailable. "
            "All five event snapshots precede the provisional event by reporting month; publication availability is unverified. The two requested cross-check months are missing. "
            "[Coverage](documentation/historical_industry_coverage.csv), [manual review](documentation/historical_industry_manual_review.csv) and [snapshot differences](documentation/historical_industry_bulletin_differences.csv) are included. "
            "Select event_id before joining classifications to price data on instrument_id. No original price, market, instrument or metadata dataset changed.")
        sections=[]
        for name in NAMES:
            entry=manifest['datasets'][name]
            sections+=[f'### {name}', '', 'Key: '+', '.join(entry['primary_key'])+'. Dates are Arrow date32; flags are Boolean. All identity and industry labels preserve source text.', '', '| Column | Arrow type | Nullable | Meaning |','| --- | --- | --- | --- |']
            sections += [f"| {f['name']} | {f['type']} | {f['nullable']} | {f['description']} |" for f in entry['columns']]
        append_section(docs/'data_dictionary.md','Historical Bulletin datasets','\n'.join(sections))
        append_section(docs/'known_limitations.md','Historical classification limitations',
            'Partial historical JSE Bulletin labels are available for five reporting months; they are not asserted equivalent to ICB. Publication dates/pre-announcement availability remain unverified; a strict availability-verified sample is empty. '
            'The September 2018 and April 2025 cross-check files are missing. Identity matching uses conservative ticker/name concordance and enumerated display variants; substantive renames and ticker reuse require review. '
            'Coverage denominators are provisional event-specific instrument samples under existing price-quality diagnostics; no final issuer sample or policy applicability has been established. '
            'Classifications may change by event and must not overwrite a single timeless sector field. No absence establishes delisting. See historical_industry_classifications.md and the manual-review queue.')
        regenerate_inventory(stage,manifest);verify(stage)
        package.rename(previous)
        try:stage.rename(package)
        except Exception:previous.rename(package);raise
        shutil.rmtree(previous)
    finally:
        if stage.exists():shutil.rmtree(stage)
    check_baseline(root)
    return manifest


def preflight_sync(source,destination,baseline_manifest):
    """Reject independently modified or added thesis payloads before any write."""
    old=json.loads(baseline_manifest.read_text())
    if sha256(destination/'manifest.json')!=sha256(baseline_manifest):
        raise ValueError('Independently changed thesis manifest; refusing overwrite')
    verify(destination);new=verify(source)
    for name,entry in old['datasets'].items():
        if name not in NAMES and new['datasets'][name]['sha256']!=entry['sha256']:
            raise ValueError('Original dataset changed: '+name)
    old_files=set(old['files'])|{'manifest.json','manifest.sha256'}
    new_files=set(new['files'])|{'manifest.json','manifest.sha256'}
    if not old_files.issubset(new_files):raise ValueError('Unexpected package deletion')
    changed=[]
    for name in sorted(new_files):
        dest=destination/name
        if dest.exists() and name not in old_files:raise ValueError('Independent thesis file conflicts: '+name)
        if not dest.exists() or sha256(dest)!=sha256(source/name):changed.append(name)
    return changed


def sync_package(source,destination,baseline_manifest):
    """Replace only verified changed files; rollback from small in-memory originals.

    Original large Parquet datasets are not copied or touched; existing backup is
    preserved. Every destination payload is checked before writing anything.
    """
    changed=preflight_sync(source,destination,baseline_manifest)
    originals={name:(destination/name).read_bytes() if (destination/name).exists() else None for name in changed}
    def replace_bytes(path,data):
        fd,temp=tempfile.mkstemp(prefix='.historical-',dir=path.parent)
        try:
            with os.fdopen(fd,'wb') as f:f.write(data)
            os.replace(temp,path)
        finally:
            if os.path.exists(temp):os.unlink(temp)
    try:
        for name in sorted(changed,key=lambda n:n in {'manifest.json','manifest.sha256'}):
            replace_bytes(destination/name,(source/name).read_bytes())
        verify(destination)
    except Exception:
        for name,content in originals.items():
            if content is None:(destination/name).unlink(missing_ok=True)
            else:replace_bytes(destination/name,content)
        raise
    return changed


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path.cwd())
    parser.add_argument('--destination',type=Path,required=True)
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    source=args.root/'dist/thesis_data';baseline=args.root/'metadata/handover_manifest_before_historical_industry.json'
    changed=preflight_sync(source,args.destination,baseline)
    print('Verified changed files:',json.dumps(changed,indent=2))
    if args.apply:
        sync_package(source,args.destination,baseline)
        print('Thesis synchronization: PASS (only changed files; original datasets and existing backup preserved)')


if __name__=='__main__':main()
