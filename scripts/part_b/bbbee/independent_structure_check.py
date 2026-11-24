#!/usr/bin/env python3
"""Independently check output keys, source-value preservation and calculations."""
import csv,collections
from pathlib import Path
D=Path('data/part_b/processed')
def read(name):
 with (D/name).open(newline='') as f:return list(csv.DictReader(f))
def key(rows,cols):
 k=[tuple(r[x] for x in cols) for r in rows];assert len(k)==len(set(k))
a=read('bbbee_ownership.csv');b=read('bbbee_compliance_levels.csv');c=read('bbbee_compliance_summary.csv');d=read('bbbee_reporting_coverage.csv')
assert (len(a),len(b),len(c),len(d),len(read('bbbee_sector_reference.csv')),len(read('bbbee_validation_results.csv')))==(606,1170,117,209,22,170)
owners={'16':('National',66),'23':('Forestry',79),'28':('Transport',84),'35':('ICT',90),'42':('Generic',95),'50':('MAC',100),'60':('Property',108),'67':('Tourism',113),'74':('Agri-BEE',120),'81':('Financial Services',125),'88':('Construction',132)}
compliance={'4':('National','5',55,55),'20':('Forestry','21',76,76),'26':('Transport','27',82,82),'32':('ICT','33',87,88),'39':('Generic','40',92,93),'47':('MAC','48',98,98),'57':('Property','58',105,106),'64':('Tourism','65',111,111),'71':('Agri-BEE','72',117,118),'78':('Financial Services','79',123,123),'85':('Construction','86',129,129)}
for rows,cols in [(a,['series_id','reporting_year','sector_original','ownership_measure']),(b,['series_id','reporting_year','sector_original','entity_size','compliance_level']),(c,['series_id','reporting_year','sector_original','entity_size','indicator_definition']),(d,['series_id','reporting_year','coverage_measure','sector_original','entity_size'])]:key(rows,cols)
for x in a:
 assert not x['indicator_sample_n'] and not x['denominator'] and not x['numerator']
 if x['ownership_pct']:
  assert 0<=float(x['ownership_pct'])<=100 and float(x['ownership_pct'])==float(x['published_value_original'].replace(',','.').rstrip('%'))
 else:assert 'blank_in_source' in x['quality_flag'] or 'not_analysed_printed_zero' in x['quality_flag']
 assert x['source_id']==x['series_id']
 if x['series_id']=='retro_2026':
  sector,page=owners[x['source_table']];assert (x['sector_original'],int(x['source_page_pdf']),int(x['source_page_printed']))==(sector,page,page-2)
  assert x['ownership_measure'] in ('black_voting_rights','black_female_voting_rights','black_economic_interest','black_female_economic_interest')
  if '_female_' in x['ownership_measure'] and x['ownership_pct']:
   peer=next(z for z in a if z['series_id']==x['series_id'] and z['reporting_year']==x['reporting_year'] and z['sector_original']==sector and z['ownership_measure']==x['ownership_measure'].replace('_female',''))
   assert (float(x['ownership_pct'])>float(peer['ownership_pct']))==('female_average_exceeds_overall_unresolved' in x['quality_flag'])
for x in d:
 assert not x['denominator'] and not x['eligible_population_count'] and not x['reporting_rate_pct']
 assert (x['sample_count']=='' and x['published_value_original']=='-') or (x['sample_count']==x['published_value_original']==x['numerator'] and int(x['sample_count'])>=0)
groups=collections.defaultdict(list)
for x in b:
 assert x['series_id']=='retro_2026' and x['source_id']=='retro_2026'
 sector,pt,cp,pp=compliance[x['source_count_table']];assert (x['sector_original'],x['source_pct_table'],int(x['source_count_page_pdf']),int(x['source_pct_page_pdf']),int(x['source_page_printed']))==(sector,pt,cp,pp,cp-2)
 assert (not x['entity_count'] and x['published_count_original']=='-') or (x['entity_count']==x['published_count_original']==x['numerator'] and int(x['entity_count'])>=0)
 if x['published_pct']:assert 0<=float(x['published_pct'])<=100 and float(x['published_pct'])==float(x['published_pct_original'].rstrip('%'))
 groups[x['sector_original'],x['reporting_year']].append(x)
bad=[]
for k,g in groups.items():
 assert len(g)==10 and len({x['compliance_level'] for x in g})==10
 total=int(g[0]['valid_status_denominator']); assert total>0 and all(int(x['valid_status_denominator'])==total for x in g)
 assert int(next(x['entity_count'] for x in g if x['compliance_level']=='Grand Total'))==total
 count=sum(int(x['entity_count']) for x in g if x['compliance_level']!='Grand Total' and x['entity_count']);fail=count!=total
 if fail:bad.append((k,count,total))
 for x in g:
  if fail or not x['entity_count']:assert not x['calculated_pct']
  else:assert abs(float(x['calculated_pct'])-100*int(x['entity_count'])/total)<0.000051
assert set(bad)=={(('National','2018'),2473,2605),(('Financial Services','2016'),9,10)}
for x in c:
 g=groups[x['sector_original'],x['reporting_year']]; selected=[z for z in g if z['compliance_level'] in ('Level 1','Level 2','Level 3','Level 4')]; assert int(x['denominator'])==int(g[0]['valid_status_denominator'])
 if x['analytical_value']:
  assert all(z['entity_count'] or z['published_pct']=='0' for z in selected)
  n=sum(int(z['entity_count']) for z in selected if z['entity_count']);assert int(x['numerator'])==n and abs(float(x['analytical_value'])-100*n/int(x['denominator']))<0.000051
 else:assert not x['numerator']
assert {(x['sector_original'],x['reporting_year']) for x in c if not x['analytical_value']}=={('National','2018'),('Financial Services','2016')}
print('Independent structure and arithmetic checks passed; distributions with discrepancies:',bad)
