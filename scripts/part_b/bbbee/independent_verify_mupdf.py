import csv, subprocess, re, xml.etree.ElementTree as ET, collections
from pathlib import Path
p='data/part_b/raw/bbbee_commission/transformation_landscape_2013_2023_published_2026.pdf'; D=Path('data/part_b/processed'); cache={}
def rd(n):
 with (D/n).open(newline='') as f:return list(csv.DictReader(f))
def lines(page):
 if page not in cache:
  root=ET.fromstring(subprocess.check_output(['mutool','draw','-F','stext',p,str(page)],stderr=subprocess.DEVNULL)); out=[]
  for l in root.iter('line'):
   ch=list(l.iter('char')); s=''.join(c.get('c') for c in ch)
   for m in re.finditer(r'\S+',s):
    cs=ch[m.start():m.end()]; xs=[float(c.get('x')) for c in cs]; ys=[float(c.get('y')) for c in cs];out.append((min(xs),min(ys),max(xs),m.group()))
  cache[page]=out
 return cache[page]
def bounds(page,t):
 w=lines(page); pairs=[a for a in w if a[3]=='Table' and any(b[3].startswith(str(t)+':') and abs(a[1]-b[1])<3 and 0<b[0]-a[0]<40 for b in w)];assert len(pairs)==1,(t,page,pairs)
 top=pairs[0][1]; end=min(x[1] for x in w if x[3]=='Source:' and x[1]>top);return top,end
out=[]
def add(t,page,typ,n):
 out.append([t,page,typ,n,'pass']);print(t,page,typ,n,flush=True)
 with open('docs/part_b/bbbee_independent_cells.csv','w',newline='') as f:
  c=csv.writer(f);c.writerow(['source_table','source_page_pdf','type','cells_checked','result']);c.writerows(out)
own=rd('bbbee_ownership.csv')
for t in sorted({int(x['source_table']) for x in own if x['series_id']=='retro_2026'}):
 g=[x for x in own if x['series_id']=='retro_2026' and x['source_table']==str(t)];page=int(g[0]['source_page_pdf']);top,end=bounds(page,t);w=lines(page);n=0
 for y in sorted({x['reporting_year'] for x in g}):
  assert [x['ownership_measure'] for x in g if x['reporting_year']==y]==['black_voting_rights','black_female_voting_rights','black_economic_interest','black_female_economic_interest'],(t,y,'measure ordering')
  yr=[x for x in w if x[3]==y and top<x[1]<end and x[0]<130];assert len(yr)==1,(t,y,yr)
  cells=sorted([x for x in w if abs(x[1]-yr[0][1])<4 and re.fullmatch(r'\d+,\d+%',x[3])],key=lambda x:x[0]); actual=[x[3] for x in cells];expected=[x['published_value_original'] for x in g if x['reporting_year']==y];assert actual==[x for x in expected if x],(t,y,actual,expected);n+=len(actual)
 add(t,page,'ownership',n)
lev=rd('bbbee_compliance_levels.csv')
for t in sorted({int(x['source_count_table']) for x in lev}|{int(x['source_pct_table']) for x in lev}):
 count=any(x['source_count_table']==str(t) for x in lev);g=[x for x in lev if x['source_count_table' if count else 'source_pct_table']==str(t)];page=int(g[0]['source_count_page_pdf' if count else 'source_pct_page_pdf']);top,end=bounds(page,t);w=lines(page);hdr={}
 for y in sorted({x['reporting_year'] for x in g}):
  z=[x for x in w if x[3]==y and top<x[1]<end];assert len(z)==1,(t,y,z);hdr[y]=(z[0][0]+z[0][2])/2
 n=0
 for level in ['Level '+str(i) for i in range(1,9)]+['Non-Compliant']+(['Grand Total'] if count else []):
  if level.startswith('Level '):z=[x for x in w if x[3]=='Level' and top<x[1]<end and any(b[3]==level[-1] and abs(x[1]-b[1])<3 and 0<b[0]-x[0]<35 for b in w)]
  elif level=='Grand Total':z=[x for x in w if x[3]=='Grand' and top<x[1]<end]
  else:z=[x for x in w if x[3] in ('Non-Compliant','Non') and top<x[1]<end and x[0]<min(hdr.values())-5]
  assert len(z)==1,(t,level,z)
  vals=[x for x in w if abs(x[1]-z[0][1])<5 and x[0]>min(hdr.values())-20 and re.fullmatch(r'\d+%?|-',x[3])];actual={}
  for x in vals:
   y=min(hdr,key=lambda y:abs(hdr[y]-(x[0]+x[2])/2));assert y not in actual,(t,level,y,vals);actual[y]=x[3]
  for x in g:
   if x['compliance_level']!=level:continue
   y=x['reporting_year'];exp=x['published_count_original' if count else 'published_pct_original'];assert actual.get(y)==exp,(t,level,y,actual.get(y),exp);n+=1
 add(t,page,'counts' if count else 'percentages',n)
coverage=rd('bbbee_reporting_coverage.csv')
for t,page in [(1,47),(2,48)]:
 top,end=bounds(page,t);w=lines(page);g=[x for x in coverage if x['source_table']==str(t)];hdr={}
 for y in map(str,range(2013,2024)):
  z=[x for x in w if x[3]==y and top<x[1]<end];assert len(z)==1,(t,y,z);hdr[y]=(z[0][0]+z[0][2])/2
 n=0
 for label in sorted({x['entity_size'] if t==1 else x['sector_original'] for x in g}):
  target={'Grand Total':'Grand','Financial Services':'Financial'}.get(label,label);z=[x for x in w if x[3]==target and top<x[1]<end and x[0]<min(hdr.values())-10];assert len(z)==1,(t,label,z)
  yy=z[0][1]+(6 if label=='Financial Services' else 0);vals=[x for x in w if abs(x[1]-yy)<5 and x[0]>min(hdr.values())-20 and re.fullmatch(r'\d+|-',x[3])]; actual={}
  for x in vals:
   center=(x[0]+x[2])/2
   if center>max(hdr.values())+(hdr['2023']-hdr['2022'])/2:continue
   y=min(hdr,key=lambda y:abs(hdr[y]-center));assert y not in actual,(t,label,y,vals);actual[y]=x[3]
  for x in g:
   if (x['entity_size'] if t==1 else x['sector_original'])!=label:continue
   y=x['reporting_year'];assert actual.get(y)==x['published_value_original'],(t,label,y,actual.get(y),x['published_value_original']);n+=1
 add(t,page,'sample composition',n)
