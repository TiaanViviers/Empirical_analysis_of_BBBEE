#!/usr/bin/env python3
"""Cross-check extracted cells against independently grouped PDF bounding-box words."""
import subprocess,xml.etree.ElementTree as ET,csv,re,collections,pathlib
P='data/part_b/raw/bbbee_commission/transformation_landscape_2013_2023_published_2026.pdf';D=pathlib.Path('data/part_b/processed'); cache={}
def words(page):
 if page not in cache:
  s=subprocess.check_output(['pdftotext','-f',str(page),'-l',str(page),'-bbox',P,'-'],text=True)
  root=ET.fromstring(s); cache[page]=[(float(x.get('xMin')),float(x.get('yMin')),float(x.get('xMax')),''.join(x.itertext())) for x in root.iter() if x.tag.endswith('word')]
 return cache[page]
def bounds(page,table):
 w=words(page); matches=[a for a in w if a[3]=='Table' and any(b[3]==f'{table}:' and abs(a[1]-b[1])<2 and 0<b[0]-a[2]<12 for b in w)]
 assert len(matches)==1,(page,table,'heading',len(matches))
 top=matches[0][1]; ends=[a[1] for a in w if a[3]=='Source:' and a[1]>top];assert ends,(page,table)
 return top,min(ends)
def load(n):
 with (D/n).open(newline='') as f:return list(csv.DictReader(f))
own=load('bbbee_ownership.csv');lev=load('bbbee_compliance_levels.csv');results=[]
for table in sorted({int(r['source_table']) for r in own if r['series_id']=='retro_2026'}):
 group=[r for r in own if r['series_id']=='retro_2026' and r['source_table']==str(table)];page=int(group[0]['source_page_pdf']);top,end=bounds(page,table);w=words(page);n=0
 for y in sorted({int(r['reporting_year']) for r in group}):
  year=[a for a in w if a[3]==str(y) and top<a[1]<end and a[0]<130];assert len(year)==1,(table,y,year)
  cells=sorted([a for a in w if abs(a[1]-year[0][1])<2 and re.fullmatch(r'\d+,\d+%',a[3])],key=lambda a:a[0]);expected=[r['published_value_original'] for r in group if int(r['reporting_year'])==y]
  actual=[a[3] for a in cells];expected=[x for x in expected if x];assert actual==expected,(table,y,actual,expected);n+=len(expected)
 results.append(('retro_2026',str(table),page,'ownership',n,'pass'))
for t in sorted({int(r['source_count_table']) for r in lev}|{int(r['source_pct_table']) for r in lev}):
 iscount=any(r['source_count_table']==str(t) for r in lev);g=[r for r in lev if r['source_count_table' if iscount else 'source_pct_table']==str(t)];page=int(g[0]['source_count_page_pdf' if iscount else 'source_pct_page_pdf']);top,end=bounds(page,t);w=words(page)
 yy=sorted({int(r['reporting_year']) for r in g});headers={}
 for y in yy:
  cand=[a for a in w if a[3]==str(y) and top<a[1]<end];assert len(cand)==1,(t,'header',y,cand);headers[y]=(cand[0][0]+cand[0][2])/2
 n=0
 for level in ['Level '+str(i) for i in range(1,9)]+['Non-Compliant']+(['Grand Total'] if iscount else []):
  if level.startswith('Level '):
   digit=level[-1]; labels=[a for a in w if a[3]=='Level' and top<a[1]<end and any(b[3]==digit and abs(a[1]-b[1])<2 and 0<b[0]-a[2]<12 for b in w)]
  elif level=='Grand Total':labels=[a for a in w if a[3]=='Grand' and top<a[1]<end and any(b[3]=='Total' and abs(a[1]-b[1])<2 and 0<b[0]-a[2]<12 for b in w)]
  else:labels=[a for a in w if a[3] in ('Non-Compliant','Non') and top<a[1]<end and a[0]<min(headers.values())-5]
  assert len(labels)==1,(t,level,'label',labels)
  line=labels[0]; vals=[a for a in w if abs(a[1]-line[1])<4 and a[0]>min(headers.values())-15 and re.fullmatch(r'\d+%?|-',a[3])]
  actual={}
  for a in vals:
   center=(a[0]+a[2])/2;year=min(headers,key=lambda y:abs(headers[y]-center));assert year not in actual,(t,level,year,vals);actual[year]=a[3]
  for row in [r for r in g if r['compliance_level']==level]:
   year=int(row['reporting_year']);expected=row['published_count_original' if iscount else 'published_pct_original'];assert actual.get(year)==expected,(t,level,year,actual.get(year),expected,headers,vals);n+=1
 results.append(('retro_2026',str(t),page,'compliance counts' if iscount else 'compliance percentages',n,'pass'))
coverage=load('bbbee_reporting_coverage.csv')
for table,page in [(1,47),(2,48)]:
 top,end=bounds(page,table);w=words(page);group=[r for r in coverage if r['source_table']==str(table)];headers={}
 for y in range(2013,2024):
  cand=[a for a in w if a[3]==str(y) and top<a[1]<end];assert len(cand)==1,(table,y,cand);headers[y]=(cand[0][0]+cand[0][2])/2
 n=0
 for label in sorted({r['entity_size'] if table==1 else r['sector_original'] for r in group}):
  target={'Grand Total':'Grand','Financial Services':'Financial'}.get(label,label)
  loc=[a for a in w if a[3]==target and top<a[1]<end and a[0]<min(headers.values())-10];assert len(loc)==1,(table,label,loc)
  y=loc[0][1]+(6 if label=='Financial Services' else 0)
  vals=[a for a in w if abs(a[1]-y)<4 and a[0]>min(headers.values())-15 and re.fullmatch(r'\d+|-',a[3])]
  actual={}
  for a in vals:
   center=(a[0]+a[2])/2; year=min(headers,key=lambda z:abs(headers[z]-center))
   # Skip the rightmost all-years total column.
   if center>max(headers.values())+(headers[2023]-headers[2022])/2:continue
   assert year not in actual,(table,label,year,vals);actual[year]=a[3]
  for row in [r for r in group if (r['entity_size'] if table==1 else r['sector_original'])==label]:
   year=int(row['reporting_year']);assert actual.get(year)==row['published_value_original'],(table,label,year,actual.get(year),row['published_value_original']);n+=1
 results.append(('retro_2026',str(table),page,'sample composition',n,'pass'))
with open('docs/part_b/bbbee_coordinate_checks.csv','w',newline='') as f:
 writer=csv.writer(f);writer.writerow(['source_id','source_table','source_page_pdf','group','cells_checked','result']);writer.writerows(results)
print('coordinate checks passed',len(results),'tables',sum(r[4] for r in results),'cells')
