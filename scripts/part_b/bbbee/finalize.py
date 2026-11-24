#!/usr/bin/env python3
"""Build analysis-ready CSVs from the scoped local extractions and run checks."""
import csv, pathlib, re, subprocess, collections, hashlib
D=pathlib.Path('data/part_b/processed'); P=pathlib.Path('data/part_b/pilot/bbbee'); DOC=pathlib.Path('docs/part_b'); PDF=pathlib.Path('data/part_b/raw/bbbee_commission/transformation_landscape_2013_2023_published_2026.pdf')
def read(path):
 with path.open(newline='') as f:return list(csv.DictReader(f))
def write(path, rows):
 assert rows,path
 with path.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def flags(*items):return ';'.join(x for x in items if x)
def unique(rows,keys):
 ks=[tuple(str(r[k]) for k in keys) for r in rows];assert len(ks)==len(set(ks)),keys
comp='changing_codes;selected_unbalanced_samples'; population='verification agency certificates and reports'
own=read(D/'bbbee_ownership_preliminary.csv')
coverage=[]
text=subprocess.check_output(['pdftotext','-f','47','-l','47','-layout',str(PDF),'-'],text=True).split('Table 1:',1)[1].split('Source:',1)[0]
for line in text.splitlines():
 m=re.match(r'^\s*(EME|Large|QSE|Unknown|Grand Total)\s+([\d\s-]+)$',line)
 if not m:continue
 vals=m[2].split(); assert len(vals)==12,(m[1],vals)
 for i,v in enumerate(vals[:11]):coverage.append(dict(series_id='retro_2026',reporting_year=2013+i,reporting_population=population,sector_original='All',sector_classification='all',entity_size=m[1],coverage_measure='sample_entries_by_enterprise_size',published_value_original=v,sample_count='' if v=='-' else int(v),numerator='' if v=='-' else int(v),denominator='',eligible_population_count='',reporting_rate_pct='',aggregation_method='published count',source_id='retro_2026',source_table='1',source_page_pdf=47,source_page_printed=45,quality_flag='dash_unspecified' if v=='-' else '',comparability_flag=comp))
assert len(coverage)==55
for x in read(P/'retrospective_sector_coverage.csv'):
 coverage.append(dict(series_id='retro_2026',reporting_year=int(x['reporting_year']),reporting_population=population,sector_original=x['sector_original'],sector_classification='B-BBEE code',entity_size='All',coverage_measure='sample_entries_by_sector',published_value_original=x['published_value_original'],sample_count=x['sample_count'],numerator=x['sample_count'],denominator='',eligible_population_count='',reporting_rate_pct='',aggregation_method='published count',source_id=x['source_id'],source_table='2',source_page_pdf=x['source_page_pdf'],source_page_printed=x['source_page_printed'],quality_flag=x['quality_flag'],comparability_flag=comp))
assert len(coverage)==209
for year in range(2013,2024):
 for table in ['1','2']:
  g=[r for r in coverage if str(r['reporting_year'])==str(year) and r['source_table']==table]; total=next(int(r['sample_count']) for r in g if (r['entity_size'] if table=='1' else r['sector_original'])=='Grand Total'); assert sum(int(r['sample_count']) for r in g if r['sample_count']!='' and (r['entity_size'] if table=='1' else r['sector_original'])!='Grand Total')==total
lookup={(str(r['reporting_year']),r['sector_original']):r['sample_count'] for r in coverage if r['source_table']=='2' and r['sector_original']!='Grand Total'}
for r in own:
 context=lookup.get((str(r['reporting_year']),r['sector_original']),'') if r['series_id']=='retro_2026' and r['sector_original']!='National' else ''
 if r['series_id']=='retro_2026' and r['sector_original']=='National': context=next(x['sample_count'] for x in coverage if x['source_table']=='1' and x['entity_size']=='Grand Total' and str(x['reporting_year'])==str(r['reporting_year']))
 r['contextual_sample_n']=context;r['indicator_sample_n']='';r['quality_flag']=flags(r['quality_flag'],'small_context_sample_lt30' if context!='' and int(context)<30 else '')
 r['comparability_flag']=flags(r['comparability_flag'],'early_period_pre_2016' if r['series_id']=='retro_2026' and int(r['reporting_year'])<2016 else '')
 if r['ownership_pct']!='':assert 0<=float(r['ownership_pct'])<=100
unique(own,['series_id','reporting_year','sector_original','ownership_measure']);write(D/'bbbee_ownership.csv',own)
levels=[]
for x in read(P/'retrospective_compliance.csv'):
 y=int(x['reporting_year']);unreliable=y==2018
 levels.append(dict(series_id='retro_2026',reporting_year=y,reporting_population=population,sector_original='National',sector_classification='national',entity_size='All',compliance_level=x['compliance_level'],published_count_original=x['entity_count'],entity_count=x['entity_count'],numerator=x['entity_count'],valid_status_denominator=x['valid_status_denominator'],published_pct_original=(x['published_pct']+'%' if x['published_pct'] else ''),published_pct=x['published_pct'],calculated_pct='' if unreliable else x['calculated_pct'],aggregation_method='count divided by published total where reconciled',source_id='retro_2026',source_count_table='4',source_pct_table='5',source_count_page_pdf=55,source_pct_page_pdf=55,source_page_printed=53,quality_flag=flags('unreliable_distribution_count_sum' if unreliable else '',x['quality_flag']),comparability_flag=comp))
for x in read(D/'bbbee_sector_compliance_preliminary.csv'):
 unreliable='count_sum_discrepancy' in x['quality_flag'];count=x['entity_count'];total=x['valid_status_denominator']
 levels.append(dict(series_id=x['series_id'],reporting_year=int(x['reporting_year']),reporting_population=population,sector_original=x['sector_original'],sector_classification='B-BBEE code',entity_size='All',compliance_level=x['compliance_level'],published_count_original=x['published_count_original'],entity_count=count,numerator=count,valid_status_denominator=total,published_pct_original=x['published_pct_original'],published_pct=x['published_pct'],calculated_pct='' if unreliable else x['calculated_pct'],aggregation_method='count divided by published total where reconciled',source_id=x['source_id'],source_count_table=x['source_table'].split('-')[0],source_pct_table=x['source_table'].split('-')[1],source_count_page_pdf=x['source_count_page_pdf'],source_pct_page_pdf=x['source_pct_page_pdf'],source_page_printed=int(x['source_count_page_pdf'])-2,quality_flag=flags(x['quality_flag'],'unreliable_distribution_count_sum' if unreliable else '', 'small_status_denominator_lt30' if int(total)<30 else ''),comparability_flag=comp))
unique(levels,['series_id','reporting_year','sector_original','entity_size','compliance_level'])
unique(coverage,['series_id','reporting_year','coverage_measure','sector_original','entity_size'])
for x in levels:
 if x['compliance_level']=='Grand Total' or x['published_pct']=='' or x['entity_count']=='':continue
 delta=abs(float(x['published_pct'])-100*int(x['entity_count'])/int(x['valid_status_denominator']))
 if delta>0.51:assert 'pct_discrepancy' in x['quality_flag'],(x,delta)

for x in levels:
 for key in ['entity_count','valid_status_denominator']:
  if x[key]!='':assert int(x[key])>=0
 for key in ['published_pct','calculated_pct']:
  if x[key]!='':assert 0<=float(x[key])<=100
write(D/'bbbee_compliance_levels.csv',levels)
summary=[]
for sector,year in sorted({(r['sector_original'],r['reporting_year']) for r in levels}):
 group=[r for r in levels if r['sector_original']==sector and r['reporting_year']==year]; by={r['compliance_level']:r for r in group};den=int(by['Grand Total']['valid_status_denominator']); valid=not any('unreliable_distribution' in r['quality_flag'] for r in group)
 # Only infer a zero from a dash when numeric status cells already sum to the published total and the corresponding published share is zero.
 selected=[by[f'Level {i}'] for i in range(1,5)]; missing=[r for r in selected if r['entity_count']=='']; safe=all(r['published_pct']!='' and float(r['published_pct'])==0 for r in missing)
 reliable=valid and den>0 and safe;num=sum(int(r['entity_count']) for r in selected if r['entity_count']!='') if reliable else ''
 summary.append(dict(series_id='retro_2026',reporting_year=year,reporting_population=population,sector_original=sector,sector_classification='national' if sector=='National' else 'B-BBEE code',entity_size='All',indicator_definition='Levels 1-4 share of published status total',published_value_original='',analytical_value=round(100*num/den,4) if reliable else '',numerator=num,denominator=den,aggregation_method='sum Levels 1-4 divided by published total; dash inferred zero only when reconciled and published share is zero',source_id='retro_2026',source_table=by['Grand Total']['source_count_table']+'-'+by['Grand Total']['source_pct_table'],source_page_pdf=by['Grand Total']['source_count_page_pdf'],source_page_printed=by['Grand Total']['source_page_printed'],quality_flag=flags('unreliable_distribution' if not valid else '', 'ambiguous_dash' if valid and not safe else '', 'inferred_zero_for_dash' if reliable and missing else '', 'small_status_denominator_lt30' if den<30 else ''),comparability_flag=comp))
write(D/'bbbee_compliance_summary.csv',summary);write(D/'bbbee_reporting_coverage.csv',coverage)
sectors=sorted({r['sector_original'] for r in coverage if r['source_table']=='2' and r['sector_original'] not in ['Grand Total','Unknown']})
ref=[dict(series_id='retro_2026',sector_original=s,sector_classification='B-BBEE code',source_id='retro_2026',source_table='2',source_page_pdf=48,source_page_printed=46,effective_period='',notes='Generic is a code category, not an industry; labels need not map to CEE sectors.' if s=='Generic' else 'Original retrospective classification; no CEE crosswalk.') for s in sectors]
ref += [dict(series_id='status_2022',sector_original=s,sector_classification='B-BBEE code',source_id='status_2022',source_table='Figure 7 and 10',source_page_pdf='19;21',source_page_printed='19;21',effective_period='',notes='Original portal chart label; no asserted equivalence to other classifications.') for s in sorted({x['sector_original'] for x in own if x['series_id']=='status_2022' and x['sector_original']!='National'})]
write(D/'bbbee_sector_reference.csv',ref)
checks=[]
def check(name,status,detail,source='',table='',year=''):checks.append(dict(check_id=name,status=status,source_id=source,source_table=table,reporting_year=year,detail=detail))
check('unique_keys','pass','Ownership and compliance keys unique; coverage reconciled by year.')
check('ranges','pass','Ownership and compliance percentages 0–100; count integers nonnegative.')
for sector,year in sorted({(r['sector_original'],r['reporting_year']) for r in levels}):
 g=[r for r in levels if r['sector_original']==sector and r['reporting_year']==year]; bad=any('unreliable_distribution' in r['quality_flag'] for r in g);check('compliance_reconciliation','issue' if bad else 'pass',f"{sector}: numeric status sum {sum(int(r['entity_count']) for r in g if r['compliance_level']!='Grand Total' and r['entity_count']!='')} vs published {g[0]['valid_status_denominator']}; dashes not assigned values",'retro_2026',g[0]['source_count_table'],year)
for r in own:
 if 'female_average_exceeds_overall' in r['quality_flag']:check('female_exceeds_overall','issue',f"{r['sector_original']} {r['ownership_measure']} {r['ownership_pct']}; denominators unknown",r['source_id'],r['source_table'],r['reporting_year'])
check('supplementary_generic','pass','Four printed zeros preserved, analytical values missing: narrative says not analysed.','status_2022','Figures 7,10','2017-2018')
check('source_authentication','issue','Retrospective original acquisition recorded verified TLS; 2022 local acquisition TLS verification bypassed and independent match not established. Hashes verify local identity only.')
write(D/'bbbee_validation_results.csv',checks)
print('final rows:',{n:len(v) for n,v in [('ownership',own),('levels',levels),('summary',summary),('coverage',coverage),('sector reference',ref),('validation',checks)]})
