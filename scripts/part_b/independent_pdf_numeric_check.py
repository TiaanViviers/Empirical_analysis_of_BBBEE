import pymupdf,pandas as pd,re
r=pd.read_csv('data/part_b/processed/cee_management_representation_raw.csv')
for y,f in [(2019,'20th'),(2023,'24th'),(2024,'25th')]:
 d=pymupdf.open('data/part_b/raw/cee/cee_'+f+'_annual_report.pdf');g=r[r.reporting_year.eq(y)];ok=0;failed=[]
 for p,z in g.groupby('source_page_pdf'):
  text=d[int(p)-1].get_text(sort=True); arr=[]
  for line in text.splitlines():
   ns=re.findall(r'(?<![\w.,])\d+(?:[.,]\d+)?%?(?![\w.,])',line)
   if len(ns)==11 and (all(re.fullmatch(r'\d+',n) for n in ns) or all(n.endswith('%') for n in ns)):arr.append(ns)
   if len(arr)==4:break
  if len(arr)!=4:failed.append((p,'rows',arr));continue
  for i,level in enumerate(['Top management','Senior management']):
   q=z[z.occupational_level.eq(level)]; a,b=arr[2*i:2*i+2];
   if [int(v) for v in a[:10]]==q.employee_count.tolist() and [float(v[:-1].replace(',','.')) for v in b[:10]]==q.published_representation_pct.tolist() and int(a[10])==q.total_employees.iloc[0]:ok+=1
   else:failed.append((p,level,'mismatch'))
 print(y,ok,'fail',len(failed),failed[:8])
