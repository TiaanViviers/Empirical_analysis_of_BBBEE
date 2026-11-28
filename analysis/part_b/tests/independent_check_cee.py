import pandas as pd
p='data/part_b/processed/'
r=pd.read_csv(p+'cee_management_representation_raw.csv');d=pd.read_csv(p+'cee_management_representation.csv')
k=['reporting_year','geographic_scope','sector_original','reporting_population','occupational_level'];print('duplicate keys raw/derived',r.duplicated(k+['population_group','gender']).sum(),d.duplicated(k).sum())
errors=[]
for key,g in r.groupby(k,dropna=False):
 mask=pd.Series(True,index=d.index)
 for col,val in zip(k,key): mask &= d[col].isna() if pd.isna(val) else d[col].eq(val)
 z=d[mask]
 if len(z)!=1: errors.append((key,'missing or duplicate derived'));continue
 z=z.iloc[0]; black=g.population_group.isin(['African','Coloured','Indian']);female=black & g.gender.eq('Female'); count=z.calculation_method=='count_based'; col='employee_count' if count else 'published_representation_pct'; denom=g.total_employees.iloc[0] if count else 100
 for field,sel in [('black_representation_pct',black),('black_female_representation_pct',female)]:
  v=100*g.loc[sel,col].sum()/denom
  if abs(v-z[field])>1e-8:errors.append((key,field,v,z[field]))
 if count and (g.employee_count.isna().any() or g.total_employees.nunique()!=1 or g.employee_count.sum()!=denom): errors.append((key,'counts'))
 if len(g)!=10 or g[['population_group','gender']].drop_duplicates().shape[0]!=10:errors.append((key,'components'))
 if z.source_id != g.source_id.iloc[0] or z.source_page_pdf != g.source_page_pdf.iloc[0]:errors.append((key,'provenance'))
print('raw/derived rows',len(r),len(d),'errors',len(errors));print(errors[:20])
assert not errors and not r.duplicated(k+['population_group','gender']).any() and not d.duplicated(k).any()
