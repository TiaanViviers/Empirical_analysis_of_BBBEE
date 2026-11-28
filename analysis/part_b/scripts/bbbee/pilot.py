#!/usr/bin/env python3
"""Reproduce scoped pilots from local PDFs and transcribed printed chart tables."""
import csv,re,subprocess,pathlib
R=pathlib.Path('data/part_b/raw/bbbee_commission'); O=pathlib.Path('data/part_b/pilot/bbbee');O.mkdir(parents=True,exist_ok=True)
def page(n):return subprocess.check_output(['pdftotext','-f',str(n),'-l',str(n),'-layout',str(R/'transformation_landscape_2013_2023_published_2026.pdf'),'-'],text=True)
def save(name,rows):
 with (O/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
def base(source,table,pdf,printed,year):return dict(source_id=source,source_table=table,source_page_pdf=pdf,source_page_printed=printed,reporting_year=year)
measures=['black_voting_rights','black_female_voting_rights','black_economic_interest','black_female_economic_interest']; own=[]
for pdf,printed,table,sector in [(66,64,'16','National'),(125,123,'81','Financial Services')]:
 s=page(pdf)
 for line in s.splitlines():
  m=re.match(r'^\s*(20(?:1[3-9]|2[0-3]))\s+((?:\d+,\d+%\s*){4})$',line)
  if not m:continue
  for name,val in zip(measures,re.findall(r'\d+,\d+%',m[2])):
   own.append(dict(**base('retro_2026',table,pdf,printed,int(m[1])),sector_original=sector,ownership_measure=name,published_value_original=val,ownership_pct=float(val[:-1].replace(',','.'))))
assert len(own)==88
for row in own:
 row['quality_flag']=''
 if 'female' in row['ownership_measure']:
  overall=row['ownership_measure'].replace('_female','')
  peer=next(x for x in own if x['reporting_year']==row['reporting_year'] and x['sector_original']==row['sector_original'] and x['ownership_measure']==overall)
  if row['ownership_pct']>peer['ownership_pct']:row['quality_flag']='female_average_exceeds_overall'
save('retrospective_ownership.csv',own)
s=page(55); a=s.split('Table 4:')[1].split('Table 5:')[0]; b=s.split('Table 5:')[1].split('Tables 4 and 5')[0]
def comp(block,percent=False):
 out={}
 for line in block.splitlines():
  m=re.match(r'\s*(Level [1-8]|Non-Compliant|Grand Total)\s+(.*)',line)
  if m:
   vals=re.findall(r'\d+'+(r'(?=%)' if percent else r''),m[2]);
   if len(vals)==11:out[m[1]]=[int(v) for v in vals]
 return out
counts=comp(a);pcts=comp(b,True);assert len(counts)==10 and len(pcts)==9
rows=[]
for level,vals in counts.items():
 for i,v in enumerate(vals):
  denom=counts['Grand Total'][i];pub=pcts.get(level,[None]*11)[i];calc=100*v/denom
  rows.append(dict(**base('retro_2026','4-5',55,53,2013+i),compliance_level=level,entity_count=v,valid_status_denominator=denom,published_pct=pub,calculated_pct=round(calc,4),quality_flag='pct_discrepancy' if pub is not None and abs(pub-calc)>0.51 else ''))
save('retrospective_compliance.csv',rows)
s=re.sub(r'Financial\s*\n\s*([0-9 ]+)\n\s*Services', r'Financial Services \1', page(48)); sector=[]
for line in s.splitlines():
 m=re.match(r'^\s*(Agri-BEE|Construction|CA|Defence|Financial\s+Services|Forestry|Generic|ICT|Transport|MAC|Property|Tourism|Unknown|Grand Total)\s+([\d\s-]+)$',line)
 if not m:continue
 vals=m[2].split()
 if len(vals)!=12:continue
 for i,val in enumerate(vals[:11]):sector.append(dict(**base('retro_2026','2',48,46,2013+i),sector_original=' '.join(m[1].split()),published_value_original=val,sample_count='' if val=='-' else int(val),quality_flag='dash_unspecified' if val=='-' else ''))
assert len(sector)==154,len(sector)
for year in range(2013,2024):
 group=[x for x in sector if x['reporting_year']==year]
 published=next(x['sample_count'] for x in group if x['sector_original']=='Grand Total')
 known=sum(x['sample_count'] for x in group if x['sector_original']!='Grand Total' and x['sample_count']!='')
 assert known==published,(year,known,published)
save('retrospective_sector_coverage.csv',sector)
sectors=['Agri-BEE','Construction','Financial','Forestry','ICT','Transport','MAC','Property','Tourism','Generic']
fig7=['4.90 32.00 31.80 15.40 31.30 36.90 26.70 34.10 14.60 0.00','11.20 48.00 21.60 33.70 32.00 40.50 19.60 30.50 23.80 0.00','24.30 50.10 26.00 32.60 30.80 48.60 27.00 37.20 23.80 21.70','23.60 56.40 25.20 54.70 24.30 36.90 40.20 9.90 18.50 33.40','12.27 47.27 19.80 40.95 29.67 46.90 37.45 17.77 36.33 27.20','15.56 52.80 22.39 50.43 26.51 38.80 29.18 9.95 56.39 31.66']
fig10=['1.50 3.30 10.00 4.50 8.90 11.50 12.10 12.80 3.90 0.00','4.50 16.90 7.60 10.80 15.10 15.50 7.50 10.10 12.70 0.00','10.60 16.70 9.60 11.40 14.50 20.00 14.40 11.40 9.90 9.70','10.10 15.50 11.20 25.50 12.10 14.70 29.70 3.70 10.50 14.60','6.07 15.53 8.10 14.60 14.50 20.37 23.70 11.30 6.63 19.57','5.29 15.59 8.66 19.89 12.05 19.47 22.33 5.60 30.02 13.80']
fig8=['27.83 25.20 29.04 30.56 29.46 33.87','18.41 15.10 17.35 15.96 17.03 19.70','9.42 10.10 11.69 14.60 12.43 14.17']
rows=[]
for number,arr,measure in [(7,fig7,'reported_black_ownership'),(10,fig10,'reported_black_female_ownership')]:
 for i,line in enumerate(arr):
  for sector,val in zip(sectors,line.split()):
   missing=sector=='Generic' and i<2
   rows.append(dict(**base('status_2022',f'Figure {number}',19 if number==7 else 21,19 if number==7 else 21,2017+i),sector_original=sector,ownership_measure=measure,published_value_original=val.replace('.',',')+'%',ownership_pct='' if missing else val,quality_flag='not_analysed_printed_zero' if missing else ''))
for measure,line in zip(['reported_black_ownership','reported_black_male_ownership','reported_black_female_ownership'],fig8):
 for i,val in enumerate(line.split()):rows.append(dict(**base('status_2022','Figure 8',20,20,2017+i),sector_original='National',ownership_measure=measure,published_value_original=val.replace('.',',')+'%',ownership_pct=val,quality_flag=''))
save('status_2022_ownership.csv',rows)
keys=[(r['source_table'],r['reporting_year'],r['sector_original'],r['ownership_measure']) for r in own+rows];assert len(keys)==len(set(keys))
for i in range(11):
 total=counts['Grand Total'][i]; actual=sum(v[i] for k,v in counts.items() if k!='Grand Total')
 if total!=actual:print('count discrepancy',2013+i,'sum',actual,'total',total)
for year in range(2017,2023):
 vals={x['ownership_measure']:float(x['ownership_pct']) for x in rows if x['source_table']=='Figure 8' and x['reporting_year']==year}
 assert abs(vals['reported_black_ownership']-vals['reported_black_male_ownership']-vals['reported_black_female_ownership'])<0.011
for row in rows:
 if row['quality_flag']:continue
 if row['sector_original']!='National' and row['ownership_measure']=='reported_black_female_ownership':
  peer=next(x for x in rows if x['source_table']=='Figure 7' and x['sector_original']==row['sector_original'] and x['reporting_year']==row['reporting_year'])
  if peer['ownership_pct'] and float(row['ownership_pct'])>float(peer['ownership_pct']):print('female exceeds total 2022',row['reporting_year'],row['sector_original'])
for sectorname in ['National','Financial Services']:
 for y in range(2013,2024):
  d={x['ownership_measure']:x['ownership_pct'] for x in own if x['sector_original']==sectorname and x['reporting_year']==y}
  for typ in ['voting_rights','economic_interest']:
   if d['black_female_'+typ]>d['black_'+typ]:print('female exceeds total retrospective',sectorname,y,typ)
print('rows:',len(own),len(counts)*11,154,len(rows));print('percentage discrepancies:',[(x['reporting_year'],x['compliance_level'],x['entity_count'],x['published_pct'],x['calculated_pct']) for x in rows_unused] if False else [(x['reporting_year'],x['compliance_level'],x['entity_count'],x['published_pct'],x['calculated_pct']) for x in list(csv.DictReader((O/'retrospective_compliance.csv').open())) if x['quality_flag']])
