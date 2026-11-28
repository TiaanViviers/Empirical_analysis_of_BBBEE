import pandas as pd,pymupdf,re
r=pd.read_csv('data/part_b/processed/cee_management_representation_raw.csv'); m=str.maketrans({'=':'1','>':'2','?':'3','@':'4','A':'5','B':'6','C':'7','D':'8','E':'9','∂':'','6':'0'})
def decode(v):
 v=v.strip().replace(' ','');return int(v.translate(m)) if '∂' in v or re.search(r'[=>?@A-E]',v) else int(v)
def pct(v):return float(v.rstrip('%').replace(',','.'))
for y,f,pages in [(2016,'17th',range(87,93)),(2017,'18th',[63]+list(range(76,87))),(2018,'19th',[74]+list(range(86,97)))]:
 d=pymupdf.open('data/part_b/raw/cee/cee_'+f+'_annual_report.pdf');bad=[];matched=0
 for p in pages:
  text=d[p-1].get_text().replace('Senior MaVnagement','Senior Management');g=r[(r.reporting_year==y)&(r.source_page_pdf==p)&(r.source_id=='cee_'+f)];
  if y==2016:
   for _,q in g.groupby(['sector_original','occupational_level']):
    row=q.iloc[0];match=re.search(r'TABLE\s+\d+:\s*WORKFORCE PROFILE FOR\s+'+re.escape(row.sector_original)+r'\s+BY RACE AND GENDER(.*?)(?=TABLE\s+\d+:|\Z)',text,re.I|re.S)
    if not match:bad.append((p,row.sector_original,'table'));continue
    sub=match.group(1);assert re.search(r'MALE\s+FEMALE\s+FOREIGN\s+NATIONAL\s+TOTAL\s+A\s+C\s+I\s+W\s+A\s+C\s+I\s+W\s+Male\s+Female',sub,re.I);level=row.occupational_level; mm=re.search(re.escape(level)+r'\s+2014\s+(?:[\d.]+%\s+){11}2015\s+(?:[\d.]+%\s+){11}2016\s+((?:[\d.]+%\s*){11})',sub,re.I)
    if not mm or [pct(x) for x in mm.group(1).split()][:10]!=q.published_representation_pct.tolist():bad.append((p,row.sector_original,level,'pct'));continue
    matched+=1
  else:
   lines=[x.strip() for x in text.splitlines() if x.strip()];flat=' '.join(lines);head=r'MALE FEMALE FOREIGN NATIONAL TOTAL A C I W A C I W MALE FEMALE TOP MANAGEMENT'
   if not re.search(head,flat,re.I):bad.append((p,'header'));continue
   for level in ['Top management','Senior management']:
    starts=[i for i,l in enumerate(lines) if re.fullmatch(level,l,re.I) or (l.lower()=='senior' and level=='Senior management' and i+1<len(lines) and lines[i+1].lower()=='management')]
    if not starts:bad.append((p,level,'heading'));continue
    i=starts[0]+1
    if lines[i].lower()=='management':i+=1
    nums=lines[i:i+11];ps=lines[i+11:i+22];q=g[g.occupational_level==level]
    try:a=[decode(x) for x in nums];b=[pct(x) for x in ps]
    except Exception as e:bad.append((p,level,'parse',nums,str(e)));continue
    if a[:10]!=q.employee_count.tolist() or a[10]!=q.total_employees.iloc[0] or b[:10]!=q.published_representation_pct.tolist():bad.append((p,level,'mismatch',a,b));continue
    matched+=1
 print(y,'matched',matched,'bad',len(bad));print(*bad[:8],sep='\n');assert not bad and matched== (22 if y==2016 else 24)
# Retrospective 2016 national counts use the alternate font glyph mapping.
d=pymupdf.open('data/part_b/raw/cee/cee_19th_annual_report.pdf');t=d[105].get_text();assert re.search(r'GENDER FOR 2016',t,re.I)
ls=[x.strip() for x in t.splitlines() if x.strip()];assert re.search(r'MALE FEMALE FOREIGN NATIONAL TOTAL A C I W A C I W MALE FEMALE TOP MANAGEMENT',' '.join(ls),re.I)
for level in ['Top management','Senior management']:
 i=next(i for i,l in enumerate(ls) if l.lower()==level.lower())+1;a=[decode(v) for v in ls[i:i+11]];b=[pct(v) for v in ls[i+11:i+22]];q=r[(r.reporting_year==2016)&(r.geographic_scope=='National')&(r.occupational_level==level)];assert a[:10]==q.employee_count.tolist() and a[10]==q.total_employees.iloc[0] and b[:10]==q.published_representation_pct.tolist()
print('2016 retrospective national: 2 management rows matched')
c=pd.read_csv('data/part_b/processed/cee_reporting_coverage.csv'); e=pd.read_csv('data/part_b/processed/cee_eap_benchmarks.csv')
for y,f,cp,ep in [(2016,'17th',25,21),(2017,'18th',22,17),(2018,'19th',29,24)]:
 doc=pymupdf.open('data/part_b/raw/cee/cee_'+f+'_annual_report.pdf'); t=' '.join(doc[cp-1].get_text().split()); t=t[t.upper().find('AGRICULTURE'):];bad=[]
 for _,z in c[(c.reporting_year==y)&(c.geographic_scope=='Sector')].iterrows():
  pattern=r'\b'+re.escape(z.sector_original)+r'\s+([\d ]+)\s+\d+(?:[.,]\d+)?%\s+([\d ]+?)(?=\s+\d+(?:[.,]\d+)?%|\s+[A-Za-z])';match=re.search(pattern,t,re.I)
  if not match or int(match.group(1).replace(' ',''))!=z.reports_received or int(match.group(2).replace(' ',''))!=z.employees_covered:bad.append(z.sector_original)
 assert not bad,(y,bad)
 t=' '.join(doc[ep-1].get_text().split()); bad=[]
 for _,z in e[e.reporting_year==y].iterrows():
  pat=(re.escape(z.population_group)+r'\s+(\d+(?:[.,]\d+)?%)\s+(\d+(?:[.,]\d+)?%)' if y==2016 else re.escape(z.population_group+' '+z.gender)+r'\s+(\d+(?:[.,]\d+)?%)')
  match=re.search(pat,t,re.I); v=match.group(1 if z.gender=='Male' or y!=2016 else 2) if match else ''
  if not v or pct(v)!=z.representation_pct or z.benchmark_year!=y or z.benchmark_quarter!=3:bad.append((z.population_group,z.gender))
 assert not bad,(y,bad)
 assert re.search(r'(?:3rd Quarter|Quarter 3)[, ]*'+str(y),t,re.I),(y,'reference period')
 print(y,'coverage sector 11 rows; EAP 8 cells and Q3 reference matched')
for y,f in [(2017,'18th'),(2018,'19th')]:
 doc=pymupdf.open('data/part_b/raw/cee/cee_'+f+'_annual_report.pdf'); q=r[(r.reporting_year==y)&(r.geographic_scope=='Sector')].drop_duplicates('source_page_pdf')
 norm=lambda s:re.sub(r'[^a-z0-9]','',s.lower())
 for _,z in q.iterrows():assert norm(z.sector_original) in norm(doc[int(z.source_page_pdf)-1].get_text()),(y,z.sector_original)
 print(y,'11 sector headings matched')
# National coverage uses 2016 Table 3 and retrospective 2017/2018 Table 4.
for y,f,p in [(2016,'17th',25),(2017,'20th',23),(2018,'20th',23)]:
 doc=pymupdf.open('data/part_b/raw/cee/cee_'+f+'_annual_report.pdf');t=' '.join(doc[p-1].get_text().split());z=c[(c.reporting_year==y)&(c.geographic_scope=='National')].iloc[0]
 if y==2016:
  s=t[t.find('TABLE 3:'):t.find('Table 4 Number')];assert '26 255' in s and '7 071 449' in s and z.reports_received==26255 and z.employees_covered==7071449
 else:
  s=t[t.find('Table 4:'):t.find('Table 5:')];pat=str(y)+r'\s+([\d ]+)\s+\d+(?:[.,]\d+)?%\s+([\d ]+?)(?=\s+\d+(?:[.,]\d+)?%)'; match=re.search(pat,s)
  if y==2017:
   assert re.search(r'2017\s+27163\s+Base figure\s+7 299 428',s) and z.reports_received==27163 and z.employees_covered==7299428
  else:assert match and int(match.group(1).replace(' ',''))==z.reports_received and int(match.group(2).replace(' ',''))==z.employees_covered
 print(y,'national coverage counts matched')
