#!/usr/bin/env python3
"""Update crosswalk, nullable counts and availability after year adapters."""
from pathlib import Path
import pandas as pd
R=Path(__file__).resolve().parents[3];o=R/'data/part_b/processed';docs=R/'docs/part_b'
for name,cols in [('cee_management_representation_raw',['employee_count','total_employees']),('cee_management_representation',['total_managers','black_manager_count','black_female_manager_count']),('cee_reporting_coverage',['reports_received','employees_covered'])]:
 d=pd.read_parquet(o/(name+'.parquet'))
 for col in cols:d[col]=d[col].astype('Int64')
 if name in ('cee_management_representation_raw','cee_reporting_coverage'):
  d['comparability_flag']=d.reporting_year.map(lambda y:'2025_reporting_regime_break' if y==2025 else None)
 d.to_csv(o/(name+'.csv'),index=False);d.to_parquet(o/(name+'.parquet'),index=False)
d=pd.read_parquet(o/'cee_management_representation.parquet');x=d[d.geographic_scope=='Sector'][['reporting_year','sector_original','source_id']].drop_duplicates().copy();x['sector_standardised']=None;x['classification_system']=x.reporting_year.map(lambda y:'CEE broad sector system' if y<=2018 else 'CEE 18-sector system');x['mapping_method']='unmapped';x['mapping_confidence']='not assessed';x['comparable_across_years']=None;x['notes']='Original label retained; no definition-level mapping established';x.to_csv(o/'cee_sector_crosswalk.csv',index=False)
a=pd.read_csv(docs/'cee_data_availability.csv');a['sector_coverage']=a['sector_coverage'].astype('object')
for i,row in a.iterrows():
 y=int(row.reporting_year);z=d[d.reporting_year==y];a.loc[i,'sector_coverage']=str(z[z.geographic_scope=='Sector'].sector_original.nunique());a.loc[i,'count_availability']='National counts; sector percentages only' if y==2016 else 'National and sector';a.loc[i,'extraction_status']='Independently checked in PDF text; rendered pages sampled';a.loc[i,'notes']='2016 national counts transcribed from 19th report retrospective Appendix E; sectors percentage only' if y==2016 else '2018 encoded digit glyphs independently decoded; construction totals checked against rendered page' if y==2018 else '2019 published sector totals fall below published national totals' if y==2019 else 'Counts and published percentages independently checked; rendered pages sampled'
a.to_csv(docs/'cee_data_availability.csv',index=False)
print(d.groupby(['reporting_year','geographic_scope','calculation_method']).size().to_string());print('derived',len(d),'crosswalk',len(x))
