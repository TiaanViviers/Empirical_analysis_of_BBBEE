#!/usr/bin/env python3
import csv,hashlib,re,subprocess
from pathlib import Path
from acquire_cee import urls
R=Path(__file__).resolve().parents[3];doc=R/'docs/part_b';out=R/'data/part_b/processed'
rows=[];availability=[]
for edition,url in urls.items():
 suffix='st' if edition==21 else 'nd' if edition==22 else 'rd' if edition==23 else 'th';p=R/f'data/part_b/raw/cee/cee_{edition}{suffix}_annual_report.pdf';year=edition+1999
 info=subprocess.check_output(['pdfinfo',str(p)],text=True,stderr=subprocess.DEVNULL);pg=int(re.search(r'^Pages:\s+(\d+)',info,re.M).group(1));pages=subprocess.check_output(['pdftotext','-layout',str(p),'-'],text=True,stderr=subprocess.DEVNULL).split('\f')
 hits={}
 for letter in ['A','C']:
  hits[letter]=[i for i,s in enumerate(pages,1) if re.search(r'appendix\s+'+letter+r'\s*:',s,re.I) and i>10]
 rows.append(dict(source_id=f'cee_{edition}{suffix}',title=f'{edition}{suffix} Commission for Employment Equity Annual Report {year}/{str(year+1)[-2:]}',publisher='South African Department of Employment and Labour',report_period=f'{year}/{str(year+1)[-2:]}',workforce_reporting_year=year,publication_date='',publication_year=year+1,original_publisher_url=url if 'labour.gov.za' in url else '',acquisition_url=url,acquisition_date='2026-11-24',local_path=str(p.relative_to(R)),file_size_bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),pdf_pages=pg,acquisition_status='acquired',limitations='Mirrored government publication; completeness and identity require further verification' if 'eecms' in url else 'Exact publication date not verified'))
 availability.append(dict(reporting_year=year,source_id=f'cee_{edition}{suffix}',appendix_a_pdf_pages=';'.join(map(str,hits['A'])),appendix_c_pdf_pages=';'.join(map(str,hits['C'])),count_availability='Yes' if edition==25 else 'Not audited',sector_coverage='18' if edition==25 else 'Not audited',extraction_status='Counts extracted; visual checks incomplete' if edition==25 else 'Not extracted',notes='Automated appendix-title search only; absence of match does not establish absence of table'))
for name,records in [('source_inventory.csv',rows),('cee_data_availability.csv',availability)]:
 with (doc/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=records[0].keys());w.writeheader();w.writerows(records)
import pandas as pd
c=pd.read_csv(R/'data/part_b/intermediate/cee_2024_coverage_transcribed.csv');c['reporting_year']=2024;c['geographic_scope']='Sector';c['source_id']='cee_25th';c['source_page_pdf']=30;c['source_table']='Table 6';c['quality_flag']='manual_transcription_visually_checked';c['reporting_population']='All reporting employers';c['sector_standardised']=None;c['employer_eligibility_definition']='Designated employers; consult report'
extra=pd.DataFrame([dict(reporting_year=y,geographic_scope='National',reports_received=n,employees_covered=e,source_id=s,source_page_pdf=p,source_table='Table 3',quality_flag='text_checked_visual_review_pending',reporting_population='All reporting employers') for y,n,e,s,p in [(2022,27532,7215960,'cee_25th',29),(2023,28015,7382213,'cee_25th',29),(2024,29269,7699665,'cee_25th',29),(2025,15090,6896041,'cee_26th',35)]])
assert c.reports_received.sum()==29269 and c.employees_covered.sum()==7699665
c=pd.concat([c,extra],ignore_index=True);c.to_csv(out/'cee_reporting_coverage.csv',index=False);c.to_parquet(out/'cee_reporting_coverage.parquet',index=False)
e=pd.read_parquet(out/'cee_eap_benchmarks.parquet');e['benchmark_year']=2024;e['benchmark_quarter']=3;e['quality_flag']='2024 Q3 QLFS reference; values visually checked in PoC';e.to_csv(out/'cee_eap_benchmarks.csv',index=False);e.to_parquet(out/'cee_eap_benchmarks.parquet',index=False)
print('inventory',len(rows),'availability',len(availability),'coverage',len(c))
