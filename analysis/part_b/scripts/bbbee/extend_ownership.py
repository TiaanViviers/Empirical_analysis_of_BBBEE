#!/usr/bin/env python3
"""Extract retrospective ownership and retain pilot supplementary data; preliminary."""
import csv, pathlib, re, subprocess
R=pathlib.Path('data/part_b/raw/bbbee_commission/transformation_landscape_2013_2023_published_2026.pdf')
O=pathlib.Path('data/part_b/processed'); O.mkdir(parents=True,exist_ok=True)
spec=[(16,66,'National'),(23,79,'Forestry'),(28,84,'Transport'),(35,90,'ICT'),(42,95,'Generic'),(50,100,'MAC'),(60,108,'Property'),(67,113,'Tourism'),(74,120,'Agri-BEE'),(81,125,'Financial Services'),(88,132,'Construction')]
measures=['black_voting_rights','black_female_voting_rights','black_economic_interest','black_female_economic_interest']
rows=[]
for table,pdf,sector in spec:
 text=subprocess.check_output(['pdftotext','-f',str(pdf),'-l',str(pdf),'-layout',str(R),'-'],text=True)
 section=text.split(f'Table {table}:',1)[1].split('Source:',1)[0]
 found=[]
 for line in section.splitlines():
  m=re.match(r'^\s*(20\d\d)\s+(.*)$',line)
  if not m:continue
  year=int(m[1]); vals=re.findall(r'\d+,\d+%',m[2]); found.append(year)
  if table==60 and year==2013:
   assert len(vals)==3; vals.append('')
  assert len(vals)==4,(table,year,vals)
  for measure,val in zip(measures,vals):
   rows.append(dict(series_id='retro_2026',reporting_year=year,publication_year=2026,reporting_population='verification agency certificates and reports',sector_original=sector,sector_classification='national' if sector=='National' else 'B-BBEE code',entity_size='All',ownership_measure=measure,published_value_original=val,ownership_pct=float(val[:-1].replace(',','.')) if val else '',numerator='',denominator='',aggregation_method='reported average; weighting unspecified',source_id='retro_2026',source_page_pdf=pdf,source_page_printed=pdf-2,source_table=str(table),quality_flag='blank_in_source' if not val else '',comparability_flag='changing codes and selected sample'))
 assert found==list(range(2017 if table==50 else 2013,2024)),(table,found)
for row in rows:
 if '_female_' in row['ownership_measure'] and row['ownership_pct']!='':
  peer=next(x for x in rows if x['source_table']==row['source_table'] and x['reporting_year']==row['reporting_year'] and x['ownership_measure']==row['ownership_measure'].replace('_female',''))
  if peer['ownership_pct']!='' and row['ownership_pct']>peer['ownership_pct']:row['quality_flag']='female_average_exceeds_overall_unresolved'
with open('data/part_b/pilot/bbbee/status_2022_ownership.csv',newline='') as f:
 for x in csv.DictReader(f):
  rows.append(dict(series_id='status_2022',reporting_year=int(x['reporting_year']),publication_year=2024,reporting_population='voluntary verification agency portal uploads',sector_original=x['sector_original'],sector_classification='national' if x['sector_original']=='National' else 'B-BBEE code',entity_size='All',ownership_measure=x['ownership_measure'],published_value_original=x['published_value_original'],ownership_pct=x['ownership_pct'],numerator='',denominator='',aggregation_method='reported ownership; weighting unspecified',source_id=x['source_id'],source_page_pdf=x['source_page_pdf'],source_page_printed=x['source_page_printed'],source_table=x['source_table'],quality_flag=x['quality_flag'],comparability_flag='separate series; definitions and sample differ;source_authentication_unresolved'))
assert len({(r['series_id'],r['reporting_year'],r['sector_original'],r['ownership_measure']) for r in rows})==len(rows)
with (O/'bbbee_ownership_preliminary.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
print('ownership rows',len(rows),'flagged female',sum('female_average_exceeds' in r['quality_flag'] for r in rows))
