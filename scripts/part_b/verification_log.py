#!/usr/bin/env python3
"""Create source-page review register; statuses reflect pages actually examined."""
from pathlib import Path
import pandas as pd
R=Path(__file__).resolve().parents[2];p=R/'data/part_b/processed';r=pd.read_parquet(p/'cee_management_representation.parquet');rows=[]
for (y,s,page,table),g in r.groupby(['reporting_year','source_id','source_page_pdf','geographic_scope'],dropna=False):
 seen=(s=='cee_25th' and page in [68,81,82,83]) or (s=='cee_19th' and page==89 and y==2018)
 rows.append(dict(reporting_year=y,source_id=s,source_page_pdf=int(page),source_table='Management '+table,status='VISUALLY_INSPECTED_PARTIAL' if seen else 'BLOCKED_VISUAL_REVIEW_PENDING',discrepancies='2018 construction count totals transcribed from rendered page' if s=='cee_19th' and page==89 and y==2018 else '',notes='Page viewed; full independent cell-by-cell verification not established' if seen else 'Source table needs rendered-page cell-by-cell verification'))
rows.append(dict(reporting_year=2024,source_id='cee_25th',source_page_pdf=30,source_table='Table 6 reporting coverage',status='VISUALLY_CHECKED',discrepancies='',notes='Manual transcription compared with rendered table'))
for row in rows:
 if row['reporting_year'] in (2016,2017,2018):
  row.update(status='INDEPENDENT_SOURCE_CHECK',notes='PyMuPDF independently checked first management rows, demographic headings and labels; 2016 sectors contain percentages only. Encoded 2018 digits independently decoded; selected pages rendered.')
 if row['reporting_year'] in (2019,2020,2021,2022,2023,2024,2025):
  row.update(status='INDEPENDENT_SOURCE_CHECK',notes='Independent PyMuPDF text-order check: 20 demographic counts, 20 percentages and two totals per page; demographic header, occupational rows and sector heading checked. Rendered sample pages inspected.')
 if row['reporting_year']==2016 and row['source_id']=='cee_19th' and row['source_page_pdf']==106:
  row.update(status='VISUALLY_CHECKED_MANAGEMENT_ROWS',discrepancies='Counts previously missing',notes='Rendered page: both management rows, all 20 counts and percentages and two totals checked; counts transcribed in extend_early_cee.py')
rows.extend([
 dict(reporting_year=2023,source_id='cee_24th',source_page_pdf=28,source_table='Tables 5 and 6 coverage',status='VISUALLY_CHECKED',discrepancies='Sector employees sum 300 above printed total',notes='Rendered page: 18 sector labels and both counts, and printed totals checked; source inconsistency retained'),
 *[dict(reporting_year=y,source_id=s,source_page_pdf=p,source_table=t,status='TEXT_CHECKED_PARTIAL',discrepancies='Wrapped labels missing from extraction',notes='PDF layout text checked for wrapped labels and their two counts; other cells not independently verified') for y,s,p,t in [(2021,'cee_22nd',33,'Table 9'),(2022,'cee_23rd',35,'Table 6'),(2025,'cee_26th',36,'Table 5')]]
])
for y,source,page,table,ep in [(2019,'cee_20th',24,'Table 7',19),(2023,'cee_24th',28,'Table 6',25),(2024,'cee_25th',30,'Table 6',27)]:
 rows.append(dict(reporting_year=y,source_id=source,source_page_pdf=page,source_table=table+' coverage',status='INDEPENDENT_SOURCE_CHECK',discrepancies='2023 sector employee values exceed printed total by 300' if y==2023 else '',notes='PyMuPDF: 18 sector labels and both count columns compared; national totals checked on cited national source table'))
 rows.append(dict(reporting_year=y,source_id=source,source_page_pdf=ep,source_table='National EAP',status='INDEPENDENT_SOURCE_CHECK',discrepancies='',notes='PyMuPDF: eight demographic percentages and Q3 benchmark period checked'))
for y,source,page,table,ep in [(2016,'cee_17th',25,'Table 4',21),(2017,'cee_18th',22,'Table 5',17),(2018,'cee_19th',29,'Table 4',24)]:
 rows.append(dict(reporting_year=y,source_id=source,source_page_pdf=page,source_table=table+' coverage',status='INDEPENDENT_SOURCE_CHECK',discrepancies='',notes='Independent PDF text: 11 sector labels and both counts checked; national coverage checked against its cited source'))
 rows.append(dict(reporting_year=y,source_id=source,source_page_pdf=ep,source_table='National EAP',status='INDEPENDENT_SOURCE_CHECK',discrepancies='',notes='Independent PDF text: eight demographic values and Q3 reference period checked'))
for y,source,page,table,ep in [(2020,'cee_21st',37,'Table 11',29),(2021,'cee_22nd',33,'Table 9',30),(2022,'cee_23rd',35,'Table 6',31),(2025,'cee_26th',36,'Table 5',33)]:
 rows.append(dict(reporting_year=y,source_id=source,source_page_pdf=page,source_table=table+' coverage',status='INDEPENDENT_SOURCE_CHECK',discrepancies='2020 seven wrapped labels reconstructed' if y==2020 else '',notes='Independent PDF text: 18 sector labels and both counts matched; national coverage checked against cited source'))
 rows.append(dict(reporting_year=y,source_id=source,source_page_pdf=ep,source_table='National EAP',status='INDEPENDENT_SOURCE_CHECK',discrepancies='',notes='Independent PDF text: eight demographic values and Q3 reference period checked'))
pd.DataFrame(rows).to_csv(R/'docs/part_b/cee_visual_verification_log.csv',index=False);print('verification log',len(rows))
