#!/usr/bin/env python3
"""Preliminary table extraction; dashes remain missing, not silently zeroed."""
import csv,pathlib,re,subprocess
p='data/part_b/raw/bbbee_commission/transformation_landscape_2013_2023_published_2026.pdf'; out=pathlib.Path('data/part_b/processed');out.mkdir(exist_ok=True,parents=True)
spec=[('Forestry',20,76,21,76),('Transport',26,82,27,82),('ICT',32,87,33,88),('Generic',39,92,40,93),('MAC',47,98,48,98),('Property',57,105,58,106),('Tourism',64,111,65,111),('Agri-BEE',71,117,72,118),('Financial Services',78,123,79,123),('Construction',85,129,86,129)]
def extract(table,page,years):
 text=subprocess.check_output(['pdftotext','-f',str(page),'-l',str(page),'-layout',p,'-'],text=True).split(f'Table {table}:',1)[1].split('Source:',1)[0]
 assert all(str(y) in text for y in years),(table,'headers')
 d={}
 for line in text.splitlines():
  m=re.match(r'^\s*(Level [1-8]|Non[- ]Compliant|Grand Total)\s+(.*)$',line,re.I)
  if not m: continue
  key=m[1].replace('Non Compliant','Non-Compliant');vals=m[2].split()
  assert len(vals)==len(years),(table,key,vals)
  assert all(re.fullmatch(r'\d+%?|-',x) for x in vals),(table,key,vals)
  d[key]=vals
 return d
rows=[]
for sector,ct,cp,pt,pp in spec:
 years=list(range(2017 if sector=='MAC' else 2013,2024));counts=extract(ct,cp,years);pcts=extract(pt,pp,years)
 assert len(counts)==10 and len(pcts)==9,(sector,counts.keys(),pcts.keys())
 for i,year in enumerate(years):
  total=int(counts['Grand Total'][i]); known=sum(int(v[i]) for k,v in counts.items() if k!='Grand Total' and v[i]!='-'); reconciles=known==total
  for level,vals in counts.items():
   raw=vals[i]; pct=pcts.get(level,['']*len(years))[i]; num=int(raw) if raw!='-' else None
   calc=round(100*num/total,4) if num is not None and total else ''
   flags=[]
   if raw=='-':flags.append('dash_unspecified')
   if not reconciles:flags.append('count_sum_discrepancy')
   if pct and calc!='' and abs(float(pct[:-1])-calc)>0.51:flags.append('published_pct_discrepancy')
   rows.append(dict(series_id='retro_2026',reporting_year=year,reporting_population='verification agency certificates and reports',sector_original=sector,entity_size='All',compliance_level=level,published_count_original=raw,entity_count=num if num is not None else '',valid_status_denominator=total,published_pct_original=pct,published_pct=pct.rstrip('%'),calculated_pct=calc,source_id='retro_2026',source_table=f'{ct}-{pt}',source_count_page_pdf=cp,source_pct_page_pdf=pp,quality_flag=';'.join(flags),comparability_flag='changing codes and selected sample'))
with (out/'bbbee_sector_compliance_preliminary.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
print('sector compliance rows',len(rows)); print('unreconciled distributions',sorted({(x['sector_original'],x['reporting_year']) for x in rows if 'count_sum_discrepancy' in x['quality_flag']}));print('percentage discrepancy cells',sum('published_pct_discrepancy' in x['quality_flag'] for x in rows))
