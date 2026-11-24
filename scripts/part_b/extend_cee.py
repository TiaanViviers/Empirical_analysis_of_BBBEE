#!/usr/bin/env python3
"""Append report-specific 2019-2023 and 2025 appendix extractions to 2024 outputs."""
from pathlib import Path
import re,subprocess,hashlib
import pandas as pd
R=Path(__file__).resolve().parents[2];out=R/'data/part_b/processed'
configs={2017:(18,'th',63,76),2023:(24,'th',70,82),2025:(26,'th',75,89),2022:(23,'rd',86,98),2021:(22,'nd',84,98),2020:(21,'st',69,81),2019:(20,'th',50,62)}
codes=[('African','Male'),('Coloured','Male'),('Indian','Male'),('White','Male'),('African','Female'),('Coloured','Female'),('Indian','Female'),('White','Female'),('Foreign national','Male'),('Foreign national','Female')]
import sys
y=int(sys.argv[1]);ed,suf,nat,sec=configs[y]; pdf=R/f'data/part_b/raw/cee/cee_{ed}{suf}_annual_report.pdf';pages=subprocess.check_output(['pdftotext','-layout',str(pdf),'-'],text=True,stderr=subprocess.DEVNULL).split('\f');source=f'cee_{ed}{suf}'
raw=[];derived=[];checks=[]
for page in [nat]+list(range(sec,sec+(11 if y==2017 else 18))):
 t=pages[page-1]; head=t[:t.upper().find('WORKFORCE')];
 if page==nat: sector=None
 else:
  if page==sec:
   if y==2017: head=t[t.upper().find('AGRICULTURE'):t.upper().find('WORKFORCE PROFILE FOR ALL',t.upper().find('AGRICULTURE'))]
   else: head=t[t.upper().find('FOR '+str(y))+len('FOR '+str(y)):t.upper().find('WORKFORCE',t.upper().find('FOR '+str(y)))]
  sector=' '.join(head.split()).strip();assert sector and len(sector)<150,(y,page,repr(sector))
 nums=[]
 for line in t.splitlines():
  tok=re.findall(r'(?<![\w.,])\d+(?:[.,]\d+)?%?(?![\w.,])',line)
  if y in (2017,2020):
   cells=re.split(r' {2,}',line.strip());tok=[x.replace(' ','') for x in cells if re.fullmatch(r'\d[\d ]*(?:[.,]\d+)?%?',x)]
  if len(tok)==11 and (all(re.fullmatch(r'\d+',x) for x in tok) or all(x.endswith('%') for x in tok)):
   nums.append(tok)
   if len(nums)==4:break
 assert len(nums)==4 and [x[0].endswith('%') for x in nums]==[False,True,False,True],(y,page,nums)
 for level,a,b in [('Top management',nums[0],nums[1]),('Senior management',nums[2],nums[3])]:
  vals=list(map(int,a));pct=[float(x[:-1].replace(',','.')) for x in b];total=vals[-1];ok=sum(vals[:-1])==total and total>0;flag='ok' if ok else 'count_total_mismatch'; checks.append(dict(reporting_year=y,page=page,sector=sector or 'National',level=level,check='count_reconciliation',observed=sum(vals[:-1])-total,passed=ok))
  for (group,gender),count,p in zip(codes,vals,pct):
   calc=100*count/total if total else None
   raw.append(dict(reporting_year=y,publication_year=y+1,geographic_scope='National' if sector is None else 'Sector',sector_original=sector,sector_standardised=None,reporting_population='All reporting employers',occupational_level=level,population_group=group,gender=gender,employee_count=count,total_employees=total,published_representation_pct=p,calculated_representation_pct=calc,source_id=source,source_page_pdf=page,source_page_printed=None,source_table='Appendix A' if sector is None else 'Appendix C',source_value_original=f'{count}; {p}%',quality_flag=flag))
   checks.append(dict(reporting_year=y,page=page,sector=sector or 'National',level=level,check='percentage_difference_pp',observed=p-calc if calc is not None else None,passed=abs(p-calc)<=.051 if calc is not None else False))
  black=sum(vals[i] for i in [0,1,2,4,5,6]);female=sum(vals[i] for i in [4,5,6])
  derived.append(dict(reporting_year=y,publication_year=y+1,geographic_scope='National' if sector is None else 'Sector',sector_original=sector,sector_standardised=None,reporting_population='All reporting employers',occupational_level=level,total_managers=total,black_manager_count=black,black_female_manager_count=female,black_representation_pct=100*black/total if ok else None,black_female_representation_pct=100*female/total if ok else None,calculation_method='count_based',source_id=source,source_page_pdf=page,quality_flag=flag,comparability_flag='2025_reporting_regime_break' if y==2025 else 'sector_mapping_unverified' if sector else 'reporting_employers_only'))
d=pd.DataFrame(derived)
if y==2019:
 d['comparability_flag']=d['comparability_flag']+';sector_totals_below_national_31_top_256_senior'
for level in ['Top management','Senior management']:
 subset=d[d.occupational_level==level];v=int(subset[subset.geographic_scope=='Sector'].total_managers.sum()-subset[subset.geographic_scope=='National'].total_managers.iloc[0]);checks.append(dict(reporting_year=y,page=nat,sector='National',level=level,check='sector_total_minus_national',observed=v,passed=v==0))
for name,new in [('cee_management_representation_raw',pd.DataFrame(raw)),('cee_management_representation',d),('cee_validation_results',pd.DataFrame(checks))]:
 old=pd.read_parquet(out/(name+'.parquet'))
 if name=='cee_validation_results' and 'reporting_year' not in old:old['reporting_year']=2024
 df=pd.concat([old[old.reporting_year!=y],new],ignore_index=True);df.to_csv(out/(name+'.csv'),index=False);df.to_parquet(out/(name+'.parquet'),index=False)
print(y,'sectors',d.sector_original.dropna().nunique(),'reconcile failures',sum(x['check']=='count_reconciliation' and not x['passed'] for x in checks),'sector checks',[(x['level'],x['observed']) for x in checks if x['check']=='sector_total_minus_national'])
