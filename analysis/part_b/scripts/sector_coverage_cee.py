#!/usr/bin/env python3
"""Extract sector reporting tables; preserve incomplete labels as fragments for review."""
import re,subprocess
from pathlib import Path
import pandas as pd
R=Path(__file__).resolve().parents[3];o=R/'data/part_b/processed';d=pd.read_parquet(o/'cee_reporting_coverage.parquet');rows=[]
# Wrapped labels read from the cited source tables, keyed by both published
# counts rather than inferred from the position of the row.
wrapped={
 (2020,1171,189658):'Accommodation and Food Service Activities',
 (2020,416,116942):'Electricity, Gas, Steam and Air Conditioning Supply',
 (2020,1040,556431):'Human Health and Social Work Activities',
 (2020,711,95070):'Professional, Scientific and Technical Activities',
 (2020,278,617422):'Public Administration and Defence, Compulsory Social Security',
 (2020,292,93494):'Water Supply, Sewerage, Waste Management and Remediation Activities',
 (2020,3844,862152):'Wholesale and Retail Trade, Repair of Motor Vehicles and Motorcycles',
 (2021,401,101903):'Electricity, Gas, Steam and Air Conditioning Supply',
 (2021,293,528932):'Public Administration and Defence, Compulsory Social Security',
 (2021,291,97531):'Water Supply, Sewerage, Waste Management and Remediation Activities',
 (2021,3959,895047):'Wholesale and Retail Trade, Repair of Motor Vehicles and Motorcycles',
 (2022,312,537944):'Public Administration and Defence. Compulsory Social Security',
 (2022,295,100047):'Water Supply, Sewerage, Waste Management and Remediation Activities',
 (2022,4076,933555):'Wholesale and Retail Trade, Repair of Motor Vehicles and Motorcycles',
 (2025,341,986670):'Public Administration and Defence, Compulsory Social Security',
 (2025,214,107992):'Water Supply, Sewerage, Waste Management and Remediation Activities',
 (2025,2250,980018):'Wholesale and Retail Trade, Repair of Motor Vehicles and Motorcycles',
}
settings={2016:(17,'th',25,4,11),2017:(18,'th',22,5,11),2018:(19,'th',29,4,11),2019:(20,'th',24,7,18),2020:(21,'st',37,11,18),2021:(22,'nd',33,9,18),2022:(23,'rd',35,6,18),2023:(24,'th',28,6,18),2025:(26,'th',36,5,18)}
for y,(ed,suf,page,table,n) in settings.items():
 f=R/f'data/part_b/raw/cee/cee_{ed}{suf}_annual_report.pdf';t=subprocess.check_output(['pdftotext','-layout','-f',str(page),'-l',str(page),str(f),'-'],text=True,stderr=subprocess.DEVNULL)
 m=re.search(r'Table\s*'+str(table)+r'\s*:.*(?:sector)',t,re.I);assert m,(y,page);t=t[m.start():];found=[]
 for line in t.splitlines():
  cells=re.split(r' {2,}',line.strip());nums=[c for c in cells if re.fullmatch(r'[\d ]+',c)];pcts=[c for c in cells if re.fullmatch(r'\d+(?:[.,]\d+)?%',c)]
  if len(nums)>=2 and len(pcts)>=(1 if y==2016 else 2):
   name=cells[0] if not re.fullmatch(r'[\d ]+',cells[0]) else None
   if name and name.strip().lower()=='total':break
   found.append((name,int(nums[0].replace(' ','')),int(nums[1].replace(' ',''))))
 assert len(found)==n,(y,len(found))
 for i,(fragment,reports,employees) in enumerate(found):
  label=wrapped.get((y,reports,employees),fragment)
  rows.append(dict(reporting_year=y,geographic_scope='Sector',sector_original=label,source_sector_fragment=fragment,sector_row_number=i+1,reports_received=reports,employees_covered=employees,source_id=f'cee_{ed}{suf}',source_page_pdf=page,source_table=f'Table {table}',quality_flag='independent_text_checked;sector_employees_exceed_national_300' if y==2023 else 'independent_text_checked',reporting_population='All reporting employers'))
 existing=d[(d.reporting_year==y)&(d.geographic_scope=='National')];print(y,'sector sums',sum(z[1] for z in found),sum(z[2] for z in found),'national',existing.reports_received.iloc[0],existing.employees_covered.iloc[0]); assert len(existing)==1
d=pd.concat([d[~((d.geographic_scope=='Sector') & d.reporting_year.isin(settings))],pd.DataFrame(rows)],ignore_index=True)
for c in ['reports_received','employees_covered','sector_row_number']:d[c]=d[c].astype('Int64')
d.to_csv(o/'cee_reporting_coverage.csv',index=False);d.to_parquet(o/'cee_reporting_coverage.parquet',index=False);print('coverage',len(d),'added',len(rows))
