import pandas as pd,pymupdf,re
r=pd.read_csv('data/part_b/processed/cee_management_representation_raw.csv');c=pd.read_csv('data/part_b/processed/cee_reporting_coverage.csv');e=pd.read_csv('data/part_b/processed/cee_eap_benchmarks.csv')
for y,f in [(2020,'21st'),(2021,'22nd'),(2022,'23rd'),(2025,'26th')]:
 doc=pymupdf.open('data/part_b/raw/cee/cee_'+f+'_annual_report.pdf');z=r[r.reporting_year==y];bad=[];count=0
 for page,g in z.groupby('source_page_pdf'):
  text=doc[int(page)-1].get_text().replace('\u00ad\n','').replace('\u00ad','');lines=[s.strip() for s in text.splitlines() if s.strip()];flat=' '.join(lines)
  if not re.search(r'Male Female Foreign National Total A C I W A C I W Male Female Top Management',flat,re.I):bad.append((page,'header'));continue
  if g.geographic_scope.iloc[0]=='Sector':
   norm=lambda s:re.sub(r'[^a-z0-9]','',s.lower())
   if norm(g.sector_original.iloc[0]) not in norm(text):bad.append((page,'sector',g.sector_original.iloc[0]));continue
  for level in ['Top management','Senior management']:
   i=next((i for i,v in enumerate(lines) if v.lower()==level.lower() or (v.lower()==level.split()[0].lower() and i+1<len(lines) and lines[i+1].lower()=='management')),None)
   if i is None:bad.append((page,level,'label'));continue
   i+=1
   if lines[i].lower()=='management':i+=1
   try:
    nums=[int(v.replace(' ','')) for v in lines[i:i+11]];ps=[float(v.strip('%').replace(',','.')) for v in lines[i+11:i+22]]
   except Exception as exc:bad.append((page,level,str(exc)));continue
   q=g[g.occupational_level==level]
   if nums[:10]!=q.employee_count.tolist() or nums[10]!=q.total_employees.iloc[0] or ps[:10]!=q.published_representation_pct.tolist():bad.append((page,level,'values'));continue
   count+=1
 print(y,'management rows',count,'errors',bad);assert count==38 and not bad
for y,f,cp,ep in [(2020,'21st',37,29),(2021,'22nd',33,30),(2022,'23rd',35,31),(2025,'26th',36,33)]:
 doc=pymupdf.open('data/part_b/raw/cee/cee_'+f+'_annual_report.pdf');t=' '.join(doc[cp-1].get_text().replace('\u00ad\n','').split());bad=[]
 for _,row in c[(c.reporting_year==y)&(c.geographic_scope=='Sector')].iterrows():
  label=r'\s+'.join(map(re.escape,row.sector_original.split()));m=re.search(label+r'\s+([\d ]+)\s+\d+(?:[.,]\d+)?%\s+([\d ]+?)(?=\s+\d+(?:[.,]\d+)?%)',t,re.I)
  if not m or int(m.group(1).replace(' ',''))!=row.reports_received or int(m.group(2).replace(' ',''))!=row.employees_covered:bad.append(row.sector_original)
 print(y,'coverage rows matched',18-len(bad),'errors',bad);assert not bad
 t=' '.join(doc[ep-1].get_text().split());bad=[]
 for _,row in e[e.reporting_year==y].iterrows():
  m=re.search(re.escape(row.population_group+' '+row.gender)+r'\s+(\d+[.,]\d+)%',t,re.I)
  if not m or float(m.group(1).replace(',','.'))!=row.representation_pct or row.benchmark_year!=y or row.benchmark_quarter!=3:bad.append((row.population_group,row.gender))
 assert re.search(r'Quarter\s+3[., ]+%s'%y,t,re.I)
 print(y,'EAP cells matched',8-len(bad),'errors',bad);assert not bad
for y,f,p,n,emp in [(2020,'21st',36,26635,7056059),(2021,'22nd',32,27017,7079355),(2022,'25th',29,27532,7215960),(2025,'26th',35,15090,6896041)]:
 t=' '.join(pymupdf.open('data/part_b/raw/cee/cee_'+f+'_annual_report.pdf')[p-1].get_text().split());q=c[(c.reporting_year==y)&(c.geographic_scope=='National')].iloc[0];assert q.reports_received==n and q.employees_covered==emp
 pattern=str(y)+r'\s+([\d ]+)\s+(?:-?\d+(?:[.,]\d+)?%|Base)\s+([\d ]+?)(?=\s+(?:-?\d+(?:[.,]\d+)?%|Base))';m=re.search(pattern,t,re.I);assert m and int(m.group(1).replace(' ',''))==n and int(m.group(2).replace(' ',''))==emp,(y,m.groups() if m else None)
 print(y,'national coverage matched')
