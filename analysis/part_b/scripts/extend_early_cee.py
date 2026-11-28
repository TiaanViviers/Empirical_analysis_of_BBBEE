#!/usr/bin/env python3
"""Extract 2016 sector percentages and 2018 appendix percentages with 2018 national counts."""
import sys,re,subprocess
from pathlib import Path
import pandas as pd
R=Path(__file__).resolve().parents[3];out=R/'data/part_b/processed';year=int(sys.argv[1]);ed=17 if year==2016 else 19;pdf=R/f'data/part_b/raw/cee/cee_{ed}th_annual_report.pdf';pages=subprocess.check_output(['pdftotext','-layout',str(pdf),'-'],text=True,stderr=subprocess.DEVNULL).split('\f')
codes=[('African','Male'),('Coloured','Male'),('Indian','Male'),('White','Male'),('African','Female'),('Coloured','Female'),('Indian','Female'),('White','Female'),('Foreign national','Male'),('Foreign national','Female')]
tables=[]
if year==2016:
 for page in range(87,93):
  t=pages[page-1];parts=re.split(r'(?=TABLE\s+\d+:\s+WORKFORCE PROFILE FOR )',t,flags=re.I)
  for part in parts[1:]:
   match=re.search(r'TABLE\s+(\d+):\s+WORKFORCE PROFILE FOR\s+(.+?)\s+BY RACE AND GENDER',part,re.I|re.S)
   if not match:continue
   num,sector=match.groups();sector=' '.join(sector.split());lines=[line for line in part.splitlines() if re.search(r'\b2016\b',line)];
   for level,line in zip(['Top management','Senior management'],lines[:2]):
    pct=re.findall(r'\d+(?:[.,]\d+)?%',line);assert len(pct)==11,(page,sector,line);tables.append((page,sector,level,pct,None,'Table '+num))
 # Retrospective national 2016 percentages in the 19th report, Appendix E.
 retrospective=R/'data/part_b/raw/cee/cee_19th_annual_report.pdf'
 txt=subprocess.check_output(['pdftotext','-layout','-f','106','-l','106',str(retrospective),'-'],text=True,stderr=subprocess.DEVNULL)
 lines=[re.findall(r'\d+(?:[.,]\d+)?%',line) for line in txt.splitlines()]
 lines=[line for line in lines if len(line)==11]
 # Rendered 19th report PDF page 106: the PDF's count glyphs are not
 # reliably decoded by pdftotext. Transcribed in source column order.
 retrospective_counts = [
  [5938,1938,3914,33339,2731,1035,1406,7716,1706,314,60037],
  [20122,6682,9906,55923,11287,4242,5103,26199,3230,1012,143706],
 ]
 for level,vals,counts in zip(['Top management','Senior management'],lines[:2],retrospective_counts):tables.append((106,None,level,vals,counts,'Appendix E retrospective'))
else:
 for page in [74]+list(range(86,97)):
  t=pages[page-1];head=t[:t.upper().find('WORKFORCE')]
  sector=None if page==74 else ('AGRICULTURE' if page==86 else re.sub(r'\s+FOREIGN\s*$','', ' '.join(head.split())))
  pcts=[]; counts=[]
  for line in t.splitlines():
   pp=re.findall(r'\d+(?:[.,]\d+)?%',line)
   if len(pp)==11:pcts.append(pp)
   if page==74:
    cells=re.split(r' {2,}',line.strip());cs=[x.replace(' ','') for x in cells if re.fullmatch(r'\d[\d ]*',x)]
    if len(cs)==11:counts.append(list(map(int,cs)))
   else:
    cells=re.split(r' {2,}',line.strip()); cs=[]
    mapping=str.maketrans({"/":"0", "'":"1", "!":"2", "#":"3", "$":"4", "*":"5", ")":"6", "(":"7", "&":"8", "+":"9"})
    for cell in cells:
     if re.fullmatch(r"[0-9!#$*/'()&+\"]+",cell):
      cs.append(int(cell.replace('"','').translate(mapping)))
    if page==89 and len(cs)==10: cs.append([6342,11057][len(counts)] if len(counts)<2 else 0)
    if len(cs)==11:counts.append(cs)
   if len(pcts)==2 and len(counts)>=2:break
  assert len(pcts)>=2,(year,page)
  for i,level in enumerate(['Top management','Senior management']):tables.append((page,sector,level,pcts[i],counts[i] if len(counts)>=2 else None,'Appendix A' if sector is None else 'Appendix C'))
raw=[];derived=[];checks=[]
for page,sector,level,pctstr,counts,table in tables:
 source_id='cee_19th' if table=='Appendix E retrospective' else f'cee_{ed}th'
 pct=[float(p[:-1].replace(',','.')) for p in pctstr];total=counts[-1] if counts else None;ok=sum(counts[:-1])==total if counts else None;flag=('ok' if ok else 'count_total_mismatch') if counts else 'percentage_only_counts_not_reliably_extracted'
 for j,((group,gender),p) in enumerate(zip(codes,pct)):
  v=counts[j] if counts else None;raw.append(dict(reporting_year=year,publication_year=2019 if table=='Appendix E retrospective' else year+1,geographic_scope='National' if sector is None else 'Sector',sector_original=sector,sector_standardised=None,reporting_population='All reporting employers',occupational_level=level,population_group=group,gender=gender,employee_count=v,total_employees=total,published_representation_pct=p,calculated_representation_pct=100*v/total if total else None,source_id=source_id,source_page_pdf=page,source_page_printed=None,source_table=table,source_value_original=pctstr[j] if v is None else f'{v}; {pctstr[j]}',quality_flag=flag))
 black=sum(counts[i] for i in [0,1,2,4,5,6]) if counts else None;female=sum(counts[i] for i in [4,5,6]) if counts else None
 derived.append(dict(reporting_year=year,publication_year=2019 if table=='Appendix E retrospective' else year+1,geographic_scope='National' if sector is None else 'Sector',sector_original=sector,sector_standardised=None,reporting_population='All reporting employers',occupational_level=level,total_managers=total,black_manager_count=black,black_female_manager_count=female,black_representation_pct=100*black/total if counts and ok else sum(pct[i] for i in [0,1,2,4,5,6]) if not counts else None,black_female_representation_pct=100*female/total if counts and ok else sum(pct[i] for i in [4,5,6]) if not counts else None,calculation_method='count_based' if counts else 'published_percentage_sum',source_id=source_id,source_page_pdf=page,quality_flag=flag,comparability_flag='historical_broad_sector_classification' if sector else 'reporting_employers_only'))
 if counts:checks.append(dict(reporting_year=year,page=page,sector=sector or 'National',level=level,check='count_reconciliation',observed=sum(counts[:-1])-total,passed=ok))
if year==2016:
 for row in derived:
  if row['geographic_scope']=='National':
   row['comparability_flag']+=';retrospective_2016_workforce_total_differs_from_original_coverage_34213'
for name,new in [('cee_management_representation_raw',pd.DataFrame(raw)),('cee_management_representation',pd.DataFrame(derived)),('cee_validation_results',pd.DataFrame(checks))]:
 old=pd.read_parquet(out/(name+'.parquet'));df=pd.concat([old[old.reporting_year!=year],new],ignore_index=True);df.to_csv(out/(name+'.csv'),index=False);df.to_parquet(out/(name+'.parquet'),index=False)
print(year,'observations',len(derived),'sectors',len(set(x[1] for x in tables if x[1])))
