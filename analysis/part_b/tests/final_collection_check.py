import pandas as pd
from pathlib import Path
p=Path('data/part_b/processed')
raw=pd.read_parquet(p/'cee_management_representation_raw.parquet');d=pd.read_parquet(p/'cee_management_representation.parquet');c=pd.read_parquet(p/'cee_reporting_coverage.parquet');e=pd.read_parquet(p/'cee_eap_benchmarks.parquet')
assert len(raw)==3380 and len(d)==338 and len(c)==169 and len(e)==80
assert not c.duplicated(['reporting_year','geographic_scope','sector_original','reporting_population']).any()
assert not e.duplicated(['reporting_year','geographic_scope','population_group','gender']).any()
assert not c[c.geographic_scope.eq('Sector')].sector_original.isna().any()
for year in range(2016,2026):
 q=c[c.reporting_year.eq(year)]; n=q[q.geographic_scope.eq('National')];s=q[q.geographic_scope.eq('Sector')]; assert len(n)==1 and len(s)==(11 if year<=2018 else 18)
 assert s.reports_received.sum()==n.reports_received.iloc[0]
 gap=int(s.employees_covered.sum()-n.employees_covered.iloc[0]);assert gap==(300 if year==2023 else 0),(year,gap)
 assert len(e[e.reporting_year.eq(year)])==8
for name,frame in [('raw',raw),('derived',d),('coverage',c)]:
 q=frame[frame.reporting_year.eq(2025)];assert q.comparability_flag.str.contains('2025_reporting_regime_break').all(),name
for name in ['cee_management_representation_raw','cee_management_representation','cee_reporting_coverage','cee_eap_benchmarks']:
 x=pd.read_csv(p/(name+'.csv'));y=pd.read_parquet(p/(name+'.parquet'));assert len(x)==len(y) and list(x.columns)==list(y.columns)
print('All ten years: coverage keys, coverage sums, EAP keys, row counts and 2025 flags pass; 2023 coverage gap retained (+300).')
