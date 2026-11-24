#!/usr/bin/env python3
"""Extract 2024 Appendix A/C counts; fail closed if source layouts differ."""
import hashlib,re,subprocess
from pathlib import Path
import pandas as pd
R=Path(__file__).resolve().parents[2]; pdf=R/'data/part_b/raw/cee/cee_25th_annual_report.pdf';out=R/'data/part_b/processed';out.mkdir(exist_ok=True)
assert hashlib.sha256(pdf.read_bytes()).hexdigest()=='96de924bb89b77cb3b2a02537b6c2e207247b5ec09ea7d802b4f44f37358fcde'
pages=subprocess.check_output(['pdftotext','-layout',str(pdf),'-'],text=True).split('\f')
sectors=['ACCOMMODATION AND FOOD SERVICE ACTIVITIES','ADMINISTRATIVE AND SUPPORT ACTIVITIES','AGRICULTURE, FORESTRY AND FISHING','ARTS, ENTERTAINMENT AND RECREATION','CONSTRUCTION','EDUCATION','ELECTRICITY, GAS, STEAM AND AIR CONDITIONING SUPPLY','FINANCIAL AND INSURANCE ACTIVITIES','HUMAN HEALTH AND SOCIAL WORK ACTIVITIES','INFORMATION AND COMMUNICATION','MANUFACTURING','MINING AND QUARRYING','PROFESSIONAL, SCIENTIFIC AND TECHNICAL ACTIVITIES','PUBLIC ADMINISTRATION AND DEFENCE, COMPULSORY SOCIAL SECURITY','REAL ESTATE ACTIVITIES','TRANSPORT AND STORAGE','WATER SUPPLY, SEWERAGE, WASTE MANAGEMENT AND REMEDIATION ACTIVITIES','WHOLESALE TRADE, COMMERCIAL AGENTS AND ALLIED SERVICES']
codes=[('African','Male'),('Coloured','Male'),('Indian','Male'),('White','Male'),('African','Female'),('Coloured','Female'),('Indian','Female'),('White','Female'),('Foreign national','Male'),('Foreign national','Female')]
rows=[]; derived=[]; checks=[]
for page,sector in [(68,None)]+list(zip(range(81,99),sectors)):
 text=pages[page-1]; assert ('Appendix A:' in text if sector is None else sector in re.sub(r'\s+',' ',text)),(page,sector)
 # Only first two rows of the first workforce table; numeric lines have 11 cells.
 lines=[]
 for line in text.splitlines():
  nums=re.findall(r'(?<![\w.])\d+(?:\.\d+)?%?(?![\w.])',line)
  if len(nums)==11 and (all(re.fullmatch(r'\d+',x) for x in nums) or all(x.endswith('%') for x in nums)):
   lines.append(nums)
   if len(lines)==4: break
 assert len(lines)==4,(page,lines)
 assert [x[0].endswith('%') for x in lines]==[False,True,False,True],page
 for level,counts,pcts in [('Top management',lines[0],lines[1]),('Senior management',lines[2],lines[3])]:
  nums=list(map(int,counts));pct=[float(x[:-1]) for x in pcts];total=nums[-1]; reconciled=sum(nums[:-1])==total
  flag='ok' if reconciled else 'count_total_mismatch'
  checks.append(dict(page=page,sector=sector or 'National',level=level,check='count_reconciliation',observed=sum(nums[:-1])-total,passed=reconciled))
  for (group,gender),count,published in zip(codes,nums,pct):
   calc=100*count/total if total else None
   rows.append(dict(reporting_year=2024,publication_year=2025,geographic_scope='National' if sector is None else 'Sector',sector_original=sector,sector_standardised=None,reporting_population='All reporting employers',occupational_level=level,population_group=group,gender=gender,employee_count=count,total_employees=total,published_representation_pct=published,calculated_representation_pct=calc,source_id='cee_25th',source_page_pdf=page,source_page_printed=page-12,source_table='Appendix A' if sector is None else 'Appendix C',source_value_original=str(count)+'; '+str(published)+'%',quality_flag=flag))
   checks.append(dict(page=page,sector=sector or 'National',level=level,check='percentage_difference_pp',observed=published-calc,passed=abs(published-calc)<=0.051))
  black=sum(nums[i] for i in [0,1,2,4,5,6]);female=sum(nums[i] for i in [4,5,6])
  derived.append(dict(reporting_year=2024,publication_year=2025,geographic_scope='National' if sector is None else 'Sector',sector_original=sector,sector_standardised=None,reporting_population='All reporting employers',occupational_level=level,total_managers=total,black_manager_count=black,black_female_manager_count=female,black_representation_pct=100*black/total if reconciled and total else None,black_female_representation_pct=100*female/total if reconciled and total else None,calculation_method='count_based',source_id='cee_25th',source_page_pdf=page,quality_flag=flag,comparability_flag='sector_mapping_unverified' if sector else 'reporting_employers_only'))
raw=pd.DataFrame(rows);d=pd.DataFrame(derived);v=pd.DataFrame(checks)
assert not raw.duplicated(['reporting_year','geographic_scope','sector_original','occupational_level','population_group','gender']).any()
assert (raw.employee_count>=0).all() and raw.published_representation_pct.between(0,100).all()
for level in ['Top management','Senior management']:
 a=d[(d.occupational_level==level)&(d.geographic_scope=='National')].total_managers.iloc[0];b=d[(d.occupational_level==level)&(d.geographic_scope=='Sector')].total_managers.sum()
 v.loc[len(v)]=[68,'National',level,'sector_total_minus_national',int(b-a),b==a]
for name,df in [('cee_management_representation_raw',raw),('cee_management_representation',d),('cee_validation_results',v)]:
 df.to_csv(out/(name+'.csv'),index=False);df.to_parquet(out/(name+'.parquet'),index=False)
poc=pd.read_csv(out/'cee_top_management_2024.csv');e=poc[poc.row_type=='EAP benchmark'].copy();e=e[e.population_group!='All'].copy();e=e.rename(columns={'percentage':'representation_pct','pdf_page':'source_page_pdf'});e=e[['reporting_year','population_group','gender','representation_pct','source_page_pdf']];e['source_id']='cee_25th';e['benchmark_year']=pd.NA;e['benchmark_quarter']=pd.NA;e['geographic_scope']='National';e['quality_flag']='reference_period_unverified';e.to_csv(out/'cee_eap_benchmarks.csv',index=False);e.to_parquet(out/'cee_eap_benchmarks.parquet',index=False)
cross=d[d.geographic_scope=='Sector'][['reporting_year','sector_original']].drop_duplicates().copy();cross['sector_standardised']=None;cross['classification_system']='CEE report appendix C';cross['mapping_method']='unmapped';cross['mapping_confidence']='unverified';cross['comparable_across_years']=None;cross['notes']='Original appendix label; historical equivalence not established';cross['source_id']='cee_25th';cross.to_csv(out/'cee_sector_crosswalk.csv',index=False)
print('raw',len(raw),'derived',len(d),'checks',len(v),'reconciliation failures',len(v[(v.check=='count_reconciliation')&(~v.passed)]),'percentage deviations >0.051pp',len(v[(v.check=='percentage_difference_pp')&(~v.passed)]));print(v[v.check=='sector_total_minus_national'].to_string(index=False))
