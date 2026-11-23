"""Historical JSE Bulletin processing. No acquisition or inferred corporate histories.

Run: python -m iress_data.historical_industry [--root ROOT] [--package]
"""
from __future__ import annotations

import argparse
import calendar
from collections import Counter, defaultdict
from datetime import date
import csv
from functools import lru_cache
import json
from pathlib import Path
import re
import shutil

import openpyxl
import pyarrow as pa
import pyarrow.parquet as pq

from .config import EVENTS
from .ingest import sha256

VERSION = '1.0.0'
EVENT_MONTHS = dict(zip([e[0] for e in EVENTS], ['2017-05', '2018-08', '2023-04', '2025-03', '2025-12'], strict=True))
EXPECTED_MONTHS = ['2017-05', '2018-08', '2018-09', '2023-04', '2025-03', '2025-04', '2025-12']
MINING_LABELS = {'Coal', 'Diamonds & Gems', 'Gen Mining', 'Gold', 'Plat & Prec. Met', 'Copper', 'Aluminium', 'Aluminum', 'Nom-ferr Metals'}
PRODUCT_LABELS = {'Inv. Prod', 'Exchange Traded Funds', 'Exchange Traded Notes', 'Actively Managed Certificates', 'Actively Managed ETF', 'Warrants', 'Kruger Rands', 'Corp Debt'}
OTHER_LABELS = {'Pref Shares', 'Other Sec', 'Non-eq Inv Instr'}
ABBREVIATIONS = {'hldgs':'holdings', 'hldg':'holdings', 'hlds':'holdings', 'grp':'group', 'ltd':'limited', 'co':'company', 'corp':'corporation', 'prop':'property'}


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, default=str, sort_keys=True)+'\n')


def write_csv(path, rows, fields=None):
    fields = fields or list(rows[0])
    with path.open('w', newline='', encoding='utf-8') as f:
        w=csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(rows)


@lru_cache(maxsize=20000)
def name_key(value):
    """Case, punctuation and enumerated abbreviation changes only; retain classes."""
    value=value.casefold().replace('&', ' and ')
    for short, full in ABBREVIATIONS.items():
        value=re.sub(r'\b'+short+r'\b', full, value)
    return re.sub('[^a-z0-9]', '', value)


def security_flags(name, label):
    product = label in PRODUCT_LABELS
    reasons=[]
    if product: reasons.append('source_product_label:'+label)
    if label in OTHER_LABELS: reasons.append('source_other_security_label:'+label)
    # Class suffixes remain in the identity key. These flags never delete rows.
    if re.search(r'\b(pref\w*|warrants?|options?|opt|nil paid|npl|rights)\b', name, re.I):
        reasons.append('name_security_class_marker')
    return product, bool(reasons), ';'.join(reasons), label in MINING_LABELS


def reporting_month(sheet, rows):
    matches=[]
    for text in [sheet]+[str(v) for row in rows[:8] for v in row if v is not None]:
        for m in re.finditer(r'\b('+'|'.join(calendar.month_name[1:])+r')\s+(20\d{2})\b', text, re.I):
            month=list(calendar.month_name).index(m[1].capitalize())
            matches.append(f'{m[2]}-{month:02}')
    if not matches or len(set(matches)) != 1:
        raise ValueError(f'Conflicting/missing reporting month: {sheet}: {matches}')
    return matches[0]


def parse_workbook(path):
    """Detect repeated/reordered headers; account for every worksheet row.

    At least a name or code under a recognized header preserves an identifiable
    row, including incomplete identities. Payment-only rows are audited separately.
    """
    rows_out=[]; audit=[]; sheets=[]
    digest=sha256(path)
    workbook=openpyxl.load_workbook(path, read_only=True, data_only=True)
    for sheet in workbook:
        rows=list(sheet.values)
        # Every supplied sheet has a reporting month; fail closed on new layouts.
        month=reporting_month(sheet.title, rows)
        columns=None; header_row=None; count=0
        for number, cells in enumerate(rows, 1):
            normalized=[str(v).strip().upper() if v is not None else '' for v in cells]
            if all(h in normalized for h in ('SECURITY','SHARE CODE','NATURE OF BUSINESS')):
                columns={h:normalized.index(h) for h in ('SECURITY','SHARE CODE','NATURE OF BUSINESS')}
                header_row=number; kind='header'
            elif columns is None:
                kind='explanatory_before_header' if any(v is not None for v in cells) else 'blank'
            else:
                name, code, label=[cells[columns[h]] if columns[h]<len(cells) else None for h in columns]
                if name is not None or code is not None:
                    name=None if name is None else str(name)
                    code=None if code is None else str(code)
                    label=None if label is None else str(label)
                    product, other, reason, mining=security_flags(name or '',label)
                    rows_out.append(dict(bulletin_month=date.fromisoformat(month+'-01'),
                        historical_security_name=name, historical_share_code=code,
                        nature_of_business_raw=label, source_file=path.name, source_sha256=digest,
                        worksheet=sheet.title, source_row=number, header_row=header_row,
                        identity_incomplete=not bool(name and code), industry_missing=not bool(label),
                        likely_investment_product=product, likely_non_company_security=other,
                        security_type_rule=reason, mining_candidate=mining))
                    count+=1; kind='security'
                elif label is not None:
                    kind='ambiguous_label_only'
                else:
                    kind='continuation_without_identity' if any(v is not None for v in cells) else 'blank'
            audit.append(dict(source_file=path.name, worksheet=sheet.title, source_row=number,
                row_disposition=kind, cells_json=json.dumps(cells,default=str,ensure_ascii=False)))
        if columns is None: raise ValueError(f'No security header: {path.name}/{sheet.title}')
        sheets.append(dict(worksheet=sheet.title, bulletin_month=month, total_rows=len(rows),
                           securities=count, row_dispositions=dict(Counter(a['row_disposition'] for a in audit if a['worksheet']==sheet.title))))
    workbook.close()
    return rows_out, audit, dict(source_file=path.name, sha256=digest, sheets=sheets,
                                publication_date=None, preannouncement_availability_verified=False)


def reference_records(processed):
    master=pq.read_table(processed/'instruments.parquet').to_pylist()
    snapshot=pq.read_table(processed/'instrument_metadata_2026-11-23.parquet').to_pylist()
    refs={r['instrument_id']:dict(instrument_id=r['instrument_id'], ticker=r['ticker'], names=set(r.get('company_names') or [r['company_name']]), has_historical_prices_record=True) for r in master}
    for row in snapshot:
        record=refs.setdefault(row['instrument_id'], dict(instrument_id=row['instrument_id'], ticker=row['ticker'], names=set(),has_historical_prices_record=False))
        record['names'].add(row['company_name'])
    return refs


def load_variants(path):
    return list(csv.DictReader(path.open())) if path.exists() else []


def match_record(row, refs, variants=()):
    code=(row['historical_share_code'] or '').strip().upper()
    name=row['historical_security_name'] or ''
    # _DEL is a provider mnemonic variant, never a reason to choose between IDs.
    ticker_candidates=[r for r in refs.values() if r['ticker'].upper() in {code,code+'_DEL'}]
    valid=[]; evidence={}
    for ref in ticker_candidates:
        for candidate in sorted(ref['names']):
            if name_key(name) and name_key(name)==name_key(candidate):
                valid.append(ref['instrument_id']); evidence[ref['instrument_id']]=('exact_ticker_validated_name' if ref['ticker'].upper()==code else 'ticker_del_suffix_validated_name', f'Bulletin name {name!r}; IRESS source/snapshot label {candidate!r}; enumerated normalization only')
        for variant in variants:
            if (variant['historical_share_code']==code and variant['historical_security_name']==name
                and variant['instrument_id']==ref['instrument_id'] and variant['reference_name'] in ref['names']):
                valid.append(ref['instrument_id']); evidence[ref['instrument_id']]=('exact_ticker_documented_name_variant', variant['evidence'])
    valid=sorted(set(valid))
    candidates=sorted(r['instrument_id'] for r in ticker_candidates)
    # Name-only candidates are suggestions, not accepted identifier histories.
    if not candidates and name_key(name):
        candidates=sorted(r['instrument_id'] for r in refs.values() if any(name_key(name)==name_key(n) for n in r['names']))
    if len(valid)==1:
        ident=valid[0]; method, why=evidence[ident]
        return dict(instrument_id=ident,match_status='matched',match_method=method,
                    match_confidence='high_label_concordance',match_evidence=why,
                    candidate_instrument_ids=';'.join(candidates),has_historical_prices_record=refs[ident]['has_historical_prices_record'])
    return dict(instrument_id=None,match_status='ambiguous' if candidates else 'unmatched',
                match_method='manual_review_required' if candidates else 'no_supported_candidate',
                match_confidence='unresolved', match_evidence=('Multiple validated IDs; possible ticker reuse' if len(valid)>1 else 'Ticker/name identity not established; no inferred rename or historical status'),
                candidate_instrument_ids=';'.join(candidates),has_historical_prices_record=False)


def construct_events(rows):
    output=[]
    for event_id, _, event_date in EVENTS:
        month=EVENT_MONTHS[event_id]
        month_date=date.fromisoformat(month+'-01')
        month_end=date(month_date.year,month_date.month,calendar.monthrange(month_date.year,month_date.month)[1])
        if month_end>=event_date: raise ValueError('Post-event or event-month snapshot forbidden')
        group=[r for r in rows if r['bulletin_month']==month_date and r['match_status']=='matched' and not r['industry_missing']]
        counts=Counter(r['instrument_id'] for r in group)
        for r in group:
            if counts[r['instrument_id']]!=1:
                # Preserve conflicts in bulletin table/review, never choose a label.
                continue
            output.append(dict(event_id=event_id,event_date=event_date,**r,
                publication_date=None,preannouncement_availability_verified=False,
                is_retrospective=False,event_date_provisional=True,
                quality_flags='publication_date_unknown;historical_identity_not_independently_verified'+(';likely_non_company_security' if r['likely_non_company_security'] else '')))
    return output


def arrow_table(rows, event=False):
    strings=['historical_security_name','historical_share_code','nature_of_business_raw','source_file','source_sha256','worksheet','security_type_rule','instrument_id','match_status','match_method','match_confidence','match_evidence','candidate_instrument_ids']
    dates=['bulletin_month']
    bools=['identity_incomplete','industry_missing','likely_investment_product','likely_non_company_security','mining_candidate','has_historical_prices_record']
    if event:
        strings+=['event_id','quality_flags'];dates+=['event_date','publication_date'];bools+=['preannouncement_availability_verified','is_retrospective','event_date_provisional']
    fields=[pa.field(k,pa.string()) for k in strings]+[pa.field(k,pa.date32()) for k in dates]+[pa.field(k,pa.bool_(),nullable=False) for k in bools]+[pa.field(k,pa.int64(),nullable=False) for k in ['source_row','header_row']]
    return pa.Table.from_pylist(rows,schema=pa.schema(fields,metadata={b'pipeline_version':VERSION.encode(),b'industry_terminology':b'Historical JSE Bulletin labels; not asserted ICB'}))


def eligible_samples(root):
    """Reuse existing audited, benchmark-paired current-positive-volume diagnostic."""
    path=root/'reports/event_instrument_coverage.csv'
    rows=list(csv.DictReader(path.open()))
    samples={e[0]:set() for e in EVENTS}
    for r in rows:
        if (r['definition']=='current_positive_volume' and r['benchmark_daily_frequency_validated']=='True'
            and r['benchmark_required_sessions_complete']=='True'
            and int(r['benchmark_estimation_usable_returns'] or 0)>=180
            and r['benchmark_complete_caar_m10_10']=='True'):
            samples[r['event_id']].add(r['instrument_id'])
    return samples


def adjacent_differences(rows):
    months=sorted({r['bulletin_month'] for r in rows})
    groups={m:defaultdict(list) for m in months}
    for r in rows:groups[r['bulletin_month']][r['historical_share_code']].append(r)
    output=[]
    for before,after in zip(months,months[1:]):
        for code in sorted(set(groups[before])|set(groups[after]),key=lambda v:v or ''):
            a=groups[before].get(code,[]);b=groups[after].get(code,[])
            old=sorted({(r['historical_security_name'],r['nature_of_business_raw']) for r in a})
            new=sorted({(r['historical_security_name'],r['nature_of_business_raw']) for r in b})
            if old!=new:
                output.append(dict(before_month=before,after_month=after,historical_share_code=code,
                    difference='absent_in_earlier' if not a else 'absent_in_later' if not b else 'name_or_label_changed',
                    earlier_values=json.dumps(old),later_values=json.dumps(new),
                    interpretation='Observed snapshot difference only; neither listing change nor identity continuity established'))
    return output


def process(root):
    processed=root/'data/processed';reports=root/'reports';reports.mkdir(exist_ok=True)
    refs=reference_records(processed); variants=load_variants(root/'metadata/historical_industry_name_variants.csv')
    rows=[];audit=[];sources=[]
    files=sorted((root/'data/raw/jse_bulletins').glob('*'))
    for path in files:
        if path.suffix.lower() not in {'.xlsx','.xlsm'}:
            raise ValueError(f'Unexpected file requires explicit parser support: {path.name}')
        r,a,s=parse_workbook(path);rows+=r;audit+=a;sources.append(s)
    duplicate_codes=Counter((r['bulletin_month'],r['historical_share_code']) for r in rows if r['historical_share_code'])
    for r in rows:
        r.update(match_record(r,refs,variants))
        if duplicate_codes[(r['bulletin_month'],r['historical_share_code'])]>1:
            r.update(instrument_id=None,match_status='ambiguous',match_method='duplicate_bulletin_code_review',match_confidence='unresolved',match_evidence='Repeated share code within bulletin; no automatic resolution',has_historical_prices_record=False)
    instrument_counts=Counter((r['bulletin_month'],r['instrument_id']) for r in rows if r['match_status']=='matched')
    for r in rows:
        if r['match_status']=='matched' and instrument_counts[(r['bulletin_month'],r['instrument_id'])]>1:
            r.update(instrument_id=None,match_status='ambiguous',match_method='duplicate_instrument_mapping_review',match_confidence='unresolved',match_evidence='Multiple source securities map to same ID/month; no automatic conflict resolution',has_historical_prices_record=False)
    events=construct_events(rows)
    for name,data,is_event in [('jse_bulletin_securities',rows,False),('event_industry_classifications',events,True)]:
        pq.write_table(arrow_table(data,is_event),processed/(name+'.parquet'),compression='zstd')
    samples=eligible_samples(root)
    coverage=[];review=[];eligibility=[]
    price_audit=list(csv.DictReader((reports/'event_instrument_coverage.csv').open()))
    review_fields=['record_type','event_id','bulletin_month','source_file','worksheet','source_row','historical_share_code','historical_security_name','nature_of_business_raw','match_status','candidate_instrument_ids','match_evidence','likely_non_company_security','mining_candidate','instrument_id','reference_ticker','reference_security_names','review_priority']
    for r in rows:
        if r['match_status']!='matched' or r['industry_missing']:
            review.append({k:({'record_type':'bulletin_security',**r,'review_priority':'medium' if r['match_status']=='ambiguous' or not r['likely_non_company_security'] else 'low'}).get(k,'') for k in review_fields})
    for a in audit:
        if a['row_disposition']=='ambiguous_label_only':
            review.append({k:({'record_type':'ambiguous_source_row',**a,'match_status':'ambiguous','match_evidence':a['cells_json']}).get(k,'') for k in review_fields})
    for event_id,_,event_date in EVENTS:
        month=date.fromisoformat(EVENT_MONTHS[event_id]+'-01')
        source=[r for r in rows if r['bulletin_month']==month];classified=[r for r in events if r['event_id']==event_id]
        ids={r['instrument_id'] for r in classified};eligible=samples[event_id];num=len(ids&eligible)
        price_rows=[r for r in price_audit if r['event_id']==event_id and r['definition']=='current_positive_volume']
        for pr in price_rows:
            if pr['instrument_id'] in eligible:
                eligibility.append(dict(event_id=event_id,event_date=event_date,instrument_id=pr['instrument_id'],
                    definition=pr['definition'],estimation_usable_returns=int(pr['benchmark_estimation_usable_returns']),
                    benchmark_complete_caar_m10_10=True,benchmark_required_sessions_complete=True,
                    has_classification=pr['instrument_id'] in ids,denominator_status='provisional'))
        near_ids={r['instrument_id'] for r in price_rows if r['any_near_price']=='True'}
        coverage.append(dict(event_id=event_id,event_date=event_date,bulletin_month=month,
            source_securities=len(source),distinct_industry_labels=len({r['nature_of_business_raw'] for r in source if r['nature_of_business_raw']}),
            securities_matched=sum(r['match_status']=='matched' for r in source),
            ambiguous_securities=sum(r['match_status']=='ambiguous' for r in source),unmatched_securities=sum(r['match_status']=='unmatched' for r in source),
            matched_historical_master=sum(r['has_historical_prices_record'] for r in classified),
            eligible_price_instruments=len(eligible),eligible_with_classification=num,
            near_event_valid_price_instruments=len(near_ids),near_event_valid_price_with_classification=len(near_ids&ids),
            unmatched_company_candidate_securities=sum(r['match_status']=='unmatched' and not r['likely_non_company_security'] for r in source),
            coverage_pct=round(100*num/len(eligible),4) if eligible else None,
            eligible_company_candidate_with_classification=sum(r['instrument_id'] in eligible and not r['likely_non_company_security'] for r in classified),
            mining_candidate_matches=sum(r['mining_candidate'] for r in classified),
            eligible_mining_candidate_matches=sum(r['mining_candidate'] and r['instrument_id'] in eligible for r in classified),
            denominator_status='provisional_current_positive_volume_est180_benchmark_complete_m10_10',
            preannouncement_availability_verified=False))
        for ident in sorted(eligible-ids):
            r=refs[ident]
            review.append({k:({'record_type':'eligible_instrument_without_classification','event_id':event_id,'bulletin_month':month,'instrument_id':ident,'reference_ticker':r['ticker'],'reference_security_names':'; '.join(sorted(r['names'])),'review_priority':'high','match_status':'unresolved_event_coverage','match_evidence':'IRESS reference labels (not verified historical names): '+ '; '.join(sorted(r['names']))}).get(k,'') for k in review_fields})
    write_csv(reports/'historical_industry_coverage.csv',coverage)
    write_csv(reports/'historical_industry_eligible_instruments.csv',eligibility)
    review.sort(key=lambda r:({'high':0,'medium':1,'low':2}.get(r['review_priority'],1),str(r['event_id']),str(r['bulletin_month']),str(r['source_file']),str(r['source_row'])))
    write_csv(reports/'historical_industry_manual_review.csv',review,review_fields)
    write_csv(reports/'historical_industry_row_audit.csv',audit)
    diffs=adjacent_differences(rows)
    write_csv(reports/'historical_industry_bulletin_differences.csv',diffs,['before_month','after_month','historical_share_code','difference','earlier_values','later_values','interpretation'])
    present=sorted({str(r['bulletin_month'])[:7] for r in rows})
    metrics=dict(pipeline_version=VERSION,implementation_sha256=sha256(Path(__file__)),
        bulletins_processed=len(files),source_securities=len(rows),distinct_industry_labels=len({r['nature_of_business_raw'] for r in rows if r['nature_of_business_raw']}),
        ambiguous_matches=sum(r['match_status']=='ambiguous' for r in rows),unmatched_securities=sum(r['match_status']=='unmatched' for r in rows),
        potential_mining_instruments=len({r['instrument_id'] for r in events if r['mining_candidate']}),
        unmatched_likely_non_company_records=sum(r['match_status']=='unmatched' and r['likely_non_company_security'] for r in rows),
        unmatched_company_candidate_records=sum(r['match_status']=='unmatched' and not r['likely_non_company_security'] for r in rows),
        present_months=present,missing_months=sorted(set(EXPECTED_MONTHS)-set(present)),sources=sources,coverage=coverage,
        price_coverage_source_sha256=sha256(root/'reports/event_instrument_coverage.csv'),
        name_variants=variants,manual_review_records=len(review),row_dispositions=dict(Counter(a['row_disposition'] for a in audit)))
    write_json(reports/'historical_industry_summary.json',metrics)
    (reports/'historical_industry_matching.md').write_text(documentation(metrics,rows,diffs))
    return metrics


def documentation(metrics,rows,diffs):
    text=['# Historical JSE Bulletin industry classifications','',
        f"Processed {metrics['bulletins_processed']} local workbooks, {metrics['source_securities']:,} identifiable security rows and {metrics['distinct_industry_labels']} distinct raw labels. Missing requested cross-check months: {', '.join(metrics['missing_months']) or 'none'}. No additional acquisition was performed.",
        f"Of {metrics['unmatched_securities']:,} unmatched security/month rows, {metrics['unmatched_likely_non_company_records']:,} carry explicit likely-non-company flags and {metrics['unmatched_company_candidate_records']} do not. The manual queue prioritizes eligible instruments with missing event classifications; current reference names/tickers are kept in separate reference fields, never presented as verified historical labels.",
        '', '## Interpretation and dates','',
        'These are historical JSE Monthly Bulletin NATURE OF BUSINESS descriptions. No formal equivalence to ICB or ICB codes is asserted. Abbreviations, spelling and changes over time remain unchanged in the raw label. All original workbooks are unchanged and retained outside the package.',
        'Bulletin month is the reporting month, stored as its first day for sorting, not a publication date. Sheet names and TRADING STATISTICS FOR headings agree. Actual publication dates and pre-announcement availability are unknown for every supplied source. All event dates are provisional and reused from the existing event configuration without new research. Event classifications are provisional prior-reporting-month snapshots, not certified information sets available at announcement. No publication date is invented.',
        '', '## Matching and scope','',
        'All identifiable security rows are retained, including ETFs, notes, warrants, preference shares, investment products and incomplete identities. Rows without name/code (payment continuations, blanks and explanatory/header rows) are individually accounted for in historical_industry_row_audit.csv in the engineering reports. No payment amount creates a security. Label-only rows enter manual review. Repeated share codes in a month block matching. Conflicting event/instrument records are excluded rather than collapsed.',
        'Automatic matches require a ticker candidate AND the same normalized security name, or an enumerated source-supported display variant. Normalization removes punctuation/case and expands only: '+json.dumps(ABBREVIATIONS,sort_keys=True)+'. It does not remove security-class markers. Exact names alone under different tickers are review suggestions. The provider _DEL suffix is considered a ticker candidate only with validated name; multiple validated IDs remain ambiguous. No fuzzy match, inferred rename or unsupported ticker change enters the event dataset.',
        'Reference labels come from historical-price export labels and the 2026-11-23 Screener snapshot. Their agreement supports an instrument mapping, not verified historical legal identity. Renames, reorganizations and ticker reuse with incompatible names remain unresolved. Current Listed/Delisted status is never used to match, filter or establish historical status. All 1,869 price IDs and 1,872 metadata IDs are considered, including the three metadata-only IDs.',
        'match_confidence=high_label_concordance denotes agreement under these conservative label rules, not independent identifier-history verification. Every accepted match records method and evidence. The engineering manual-review CSV includes every ambiguous/unmatched bulletin row and each eligible price instrument lacking an event classification; counts refer to security/month records unless described as distinct instruments.',
        '', '## Explicit display variants','',
        'The following variants use only visible source-label spelling, abbreviation or truncation evidence. They establish no corporate-action history. Substantive name changes remain in review.', '',
        '| Code | Bulletin name | Reference label | Evidence |','| --- | --- | --- | --- |']
    for v in metrics['name_variants']:text.append(f"| {v['historical_share_code']} | {v['historical_security_name']} | {v['reference_name']} | {v['evidence']} |")
    text+=['','## Event coverage and denominator','',
        'The packaged historical_industry_eligible_instruments.csv lists the exact provisional denominator IDs and their audited return counts; historical_industry_coverage.csv also reports matched instruments with any valid price in −10:+10. No final econometric eligibility sample exists. Provisional eligible instrument denominator reuses reports/event_instrument_coverage.csv: definition=current_positive_volume (finite positive adjacent closes with positive volume at the return date), at least 180 benchmark-paired usable returns in sessions −250:−30 inclusive, benchmark required closes complete, and all benchmark-paired returns in −10:+10 complete. These are descriptive diagnostic returns with unverified adjustment basis. Full-period coverage and 2026 listing status play no role. Instruments are not verified unique issuers; company-candidate counts only remove explicitly flagged likely non-company securities. No issuer-level or legal exposure sample is claimed.',
        f"Eligibility input SHA-256: `{metrics['price_coverage_source_sha256']}`.", '',
        '| Event | Date (provisional) | Bulletin | Source rows | Labels | Matched | Ambiguous | Unmatched | Classified / eligible | % | Mining candidates matched |',
        '| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |']
    for c in metrics['coverage']:text.append(f"| {c['event_id']} | {c['event_date']} | {c['bulletin_month']} | {c['source_securities']} | {c['distinct_industry_labels']} | {c['securities_matched']} | {c['ambiguous_securities']} | {c['unmatched_securities']} | {c['eligible_with_classification']} / {c['eligible_price_instruments']} | {c['coverage_pct']} | {c['mining_candidate_matches']} |")
    text+=['','The designated May 2017, August 2018, April 2023, March 2025 and December 2025 snapshots alone feed their corresponding events. September 2018 and April 2025 are cross-check-only; both are absent. The parser may ingest them later but event selection never substitutes them. Month-end must strictly precede the event; no retrospective filling is performed. is_retrospective is false for all event rows; preannouncement_availability_verified is also false. A strict availability-verified subset is currently empty.',
        '', '## Security and mining flags','',
        'likely_investment_product is true only for these exact source labels: '+', '.join(sorted(PRODUCT_LABELS))+'. likely_non_company_security also includes '+', '.join(sorted(OTHER_LABELS))+' and names containing explicit preference/warrant/option/nil-paid/rights markers. These are transparent screening flags, not verified security classes; in particular Non-eq Inv Instr may describe an operating company. No rows are dropped by these flags.',
        'mining_candidate uses only exact source labels: '+', '.join(sorted(MINING_LABELS))+'. The broad candidate list includes metal producers and does not establish direct mining activity or Mining Charter legal applicability. Iron & Steel and investment products are not inferred to be mining companies. Names alone do not set this flag.',
        '', '## Adjacent snapshot checks','',
        'Every observed adjacent pair is compared by historical share code, preserving old/new names and labels in historical_industry_bulletin_differences.csv. A shared ticker is only a comparison key, not proof of continuity. Added/absent rows do not establish listing/delisting. Differences across 2018–2023 may include terminology revisions, business changes or identity changes; none is automatically reconciled. The requested September 2018 and April 2025 consistency checks cannot be run without those files.', '',
        '| Earlier | Later | Difference | Securities |','| --- | --- | --- | --- |']
    for key,count in sorted(Counter((str(d['before_month'])[:7],str(d['after_month'])[:7],d['difference']) for d in diffs).items()):text.append('| '+' | '.join(key)+f' | {count} |')
    text+=['','## Sources and row preservation','', '| Filename | Reporting month | Worksheet | Security rows | Worksheet rows | SHA-256 |','| --- | --- | --- | --- | --- | --- |']
    for s in metrics['sources']:
        for sh in s['sheets']:text.append(f"| {s['source_file']} | {sh['bulletin_month']} | {sh['worksheet']} | {sh['securities']} | {sh['total_rows']} | `{s['sha256']}` |")
    text+=['', 'Row dispositions: '+json.dumps(metrics['row_dispositions'],sort_keys=True)+'. Source-row provenance is 1-based Excel row number; header_row identifies the applicable section header.',
        '', '## Joining and remaining gaps','',
        'Join event_industry_classifications to prices by instrument_id after selecting event_id. Its unique key is (event_id, instrument_id); joining all events on instrument_id alone multiplies price rows. The bulletin table key is (source_file, worksheet, source_row); instrument_id is nullable. Multiple securities for an issuer remain distinct. has_historical_prices_record distinguishes the metadata-only IDs. Keep nature_of_business_raw event-specific instead of writing a single sector into instruments.parquet.',
        'The supplied months provide substantial but incomplete provisional coverage; coverage varies by event and is measured above. The manual queue separates source absence from incompatible labels. Most early eligible-sample gaps involve differing names/tickers rather than absence of an industry in the source. Additional nearby months are therefore likely to add fewer primary matches than resolving supported identity histories. More months can improve temporal checks around listings or identifier changes, but cannot establish identity continuity or historical publication availability by themselves. Prioritize resolving the existing eligible-instrument queue and obtaining the two missing cross-check files if later authorized. Additional acquisition is not necessary to use this provisional handover, and no claim of sufficient final policy-exposure coverage is made.',
        '', '## Reproduction and validation','',
        'Engineering command: `.venv/bin/python -m iress_data.historical_industry --package`. It parses only local files, uses enumerated variants in metadata/historical_industry_name_variants.csv, rewrites the two derived datasets/reports, verifies all baseline raw/original dataset hashes, and augments the portable package. Original datasets remain byte-identical. The standalone package verifier checks schemas, checksums, unique keys, source linkage, event/month mapping and prevention of post-event leakage. Tests cover parser preservation, ambiguous identities, source dates, event selection, integrity and synchronization conflicts. No econometric analysis was performed.', '']
    return '\n'.join(text)


def check_baseline(root):
    baseline=json.loads((root/'metadata/historical_industry_baseline.json').read_text())
    for relative,digest in baseline.items():
        if sha256(root/relative)!=digest:raise ValueError('Original source/dataset changed: '+relative)
    return True


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path.cwd());parser.add_argument('--package',action='store_true')
    args=parser.parse_args();metrics=process(args.root)
    check_baseline(args.root)
    if args.package:
        from .historical_industry_package import augment_package
        augment_package(args.root,metrics)
    print(json.dumps({k:v for k,v in metrics.items() if k not in {'sources','name_variants'}},indent=2,default=str))


if __name__=='__main__':main()
