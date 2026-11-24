#!/usr/bin/env python3
"""National reporting totals from the specified original report tables."""
from pathlib import Path
import pandas as pd
R=Path(__file__).resolve().parents[2];out=R/'data/part_b/processed';df=pd.read_parquet(out/'cee_reporting_coverage.parquet')
rows=[(2016,26255,7071449,'cee_17th',25,'Table 3'),(2017,27163,7299428,'cee_20th',23,'Table 4 retrospective'),(2018,27485,7415876,'cee_20th',23,'Table 4 retrospective'),(2019,27127,7332072,'cee_20th',23,'Table 4'),(2020,26635,7056059,'cee_21st',36,'Table 8'),(2021,27017,7079355,'cee_22nd',32,'Table 6')]
new=pd.DataFrame([dict(reporting_year=y,geographic_scope='National',reports_received=n,employees_covered=e,source_id=s,source_page_pdf=p,source_table=t,quality_flag='text_checked_visual_review_pending',reporting_population='All reporting employers') for y,n,e,s,p,t in rows]);df=pd.concat([df[~(df.reporting_year.isin([r[0] for r in rows]) & (df.geographic_scope=='National'))],new],ignore_index=True)
for col in ['reports_received','employees_covered']:df[col]=df[col].astype('Int64')
df.to_csv(out/'cee_reporting_coverage.csv',index=False);df.to_parquet(out/'cee_reporting_coverage.parquet',index=False);print('coverage records',len(df))
