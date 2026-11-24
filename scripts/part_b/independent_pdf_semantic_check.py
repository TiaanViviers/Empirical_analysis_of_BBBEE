import pandas as pd,pymupdf,re
r=pd.read_csv('data/part_b/processed/cee_management_representation_raw.csv')
for y,f in [(2019,'20th'),(2023,'24th'),(2024,'25th')]:
 d=pymupdf.open('data/part_b/raw/cee/cee_'+f+'_annual_report.pdf');z=r[r.reporting_year==y];bad=[]
 for p,g in z.groupby('source_page_pdf'):
  t=' '.join(d[int(p)-1].get_text().split());pattern=r'Male Female Foreign National Total A C I W A C I W Male Female Top Management';
  if not re.search(pattern,t,re.I):bad.append((p,'header',t[:400]));continue
  for level in ['Top management','Senior management']:
   m=re.search(re.escape(level)+r'\s+((?:\d+\s+){11})((?:\d+(?:[.,]\d+)?%\s*){11})',t,re.I)
   if not m:bad.append((p,level,'pattern'));continue
   a=list(map(int,m.group(1).split()));b=[float(v[:-1].replace(',','.')) for v in m.group(2).split()];q=g[g.occupational_level==level];
   if a[:10]!=q.employee_count.tolist() or a[10]!=q.total_employees.iloc[0] or b[:10]!=q.published_representation_pct.tolist():bad.append((p,level,'values'))
 print(y,'management rows',38-len(bad),'fail',len(bad),bad[:3]); assert not bad
coverage=pd.read_csv('data/part_b/processed/cee_reporting_coverage.csv')
eap=pd.read_csv('data/part_b/processed/cee_eap_benchmarks.csv')
for y,f,cp,ep in [(2019,'20th',24,19),(2023,'24th',28,25),(2024,'25th',30,27)]:
 d=pymupdf.open('data/part_b/raw/cee/cee_'+f+'_annual_report.pdf');t=' '.join(d[cp-1].get_text().split());bad=[]
 for _,row in coverage[(coverage.reporting_year==y)&(coverage.geographic_scope=='Sector')].iterrows():
  label=r'\s+'.join(map(re.escape,row.sector_original.split()));m=re.search(label+r'\s+([\d ]+)\s+\d+[.,]\d+%\s+([\d ]+)\s+\d+[.,]\d+%',t,re.I)
  if not m or int(m.group(1).replace(' ',''))!=row.reports_received or int(m.group(2).replace(' ',''))!=row.employees_covered:bad.append(row.sector_original)
 print(y,'coverage sector rows matched',18-len(bad),'fail',bad); assert not bad
 t=' '.join(d[ep-1].get_text().split());bad=[]
 for _,row in eap[eap.reporting_year==y].iterrows():
  m=re.search(re.escape(row.population_group+' '+row.gender)+r'\s+(\d+[.,]\d+)%',t,re.I)
  if not m or float(m.group(1).replace(',','.'))!=row.representation_pct:bad.append((row.population_group,row.gender))
 print(y,'EAP cells matched',8-len(bad),'fail',bad); assert not bad
