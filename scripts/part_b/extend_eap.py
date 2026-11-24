#!/usr/bin/env python3
import re,subprocess
from pathlib import Path
import pandas as pd
R=Path(__file__).resolve().parents[2];out=R/'data/part_b/processed';records=[]
for ed in range(17,27):
 suffix='st' if ed==21 else 'nd' if ed==22 else 'rd' if ed==23 else 'th';year=ed+1999;f=R/f'data/part_b/raw/cee/cee_{ed}{suffix}_annual_report.pdf';pages=subprocess.check_output(['pdftotext','-layout',str(f),'-'],text=True,stderr=subprocess.DEVNULL).split('\f')
 for page,t in enumerate(pages,1):
  if page<8:continue
  if not re.search(r'(?:TABLE\s+\d+:\s+NATIONAL EAP)',t,re.I):continue
  section=re.split(r'TABLE\s+\d+:\s+NATIONAL EAP',t,maxsplit=1,flags=re.I)[1]
  vals={}
  for group in ['African','Coloured','Indian','White']:
   line=next((l for l in section.splitlines() if re.search(r'\b'+group+r'\b',l,re.I) and len(re.findall(r'\d+(?:[.,]\d+)?%',l))>=2),None)
   if line:
    pct=re.findall(r'\d+(?:[.,]\d+)?%',line);vals[group]=[float(v[:-1].replace(',','.')) for v in pct[:2]]
  if len(vals)==4:break
 else:
  print(year,'EAP missing');continue
 for group,values in vals.items():
  for gender,v in zip(['Male','Female'],values):records.append(dict(reporting_year=year,population_group=group,gender=gender,representation_pct=v,source_page_pdf=page,source_id=f'cee_{ed}{suffix}',benchmark_year=year,benchmark_quarter=3,geographic_scope='National',quality_flag='independent_text_checked'))
 print(year,'page',page)
df=pd.DataFrame(records);df.to_csv(out/'cee_eap_benchmarks.csv',index=False);df.to_parquet(out/'cee_eap_benchmarks.parquet',index=False)
