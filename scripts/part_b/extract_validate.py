#!/usr/bin/env python3
"""Extract PDF text with Poppler, map visually verified rows, validate and export."""
import hashlib, pathlib, re, subprocess
from decimal import Decimal
import pandas as pd
ROOT = pathlib.Path(__file__).resolve().parents[2]
pdf = ROOT/'data/part_b/raw/cee/cee_25th_annual_report.pdf'
assert hashlib.sha256(pdf.read_bytes()).hexdigest() == '96de924bb89b77cb3b2a02537b6c2e207247b5ec09ea7d802b4f44f37358fcde'
text = subprocess.check_output(['pdftotext','-layout','-f','34','-l','35',str(pdf),'-'], text=True)
title = 'Table 7: Workforce profile at the Top Management Level by Sector, Population Group and Gender'
assert text.count(title) == 2
part1, part2 = text.split(title)[1:]
part1 = part1[part1.index('EAP'):]
part2 = part2[part2.index('Manufacturing'):part2.index('Table 7 shows')]
# All numeric tokens in these table regions are table cells; row labels are mapped
# in source order after visual inspection, because their lines wrap around values.
tokens = re.findall(r'\b(?:\d+(?:\.\d+)?%|NA)\b|\b\d+(?:\.\d+)?%', part1 + '\n' + part2)
sectors = ['EAP','Accommodation and food service activities','Administrative and support activities','Agriculture, forestry & fishing','Arts, entertainment and recreation','Construction','Education','Electricity, gas, steam and air conditioning supply','Financial and insurance activities','Human health and social work activities','Information and communication','Manufacturing','Mining and quarrying','Professional, scientific and technical activities','Public administration and defence; compulsory social security','Real estate activities','Transportation and storage','Water supply sewerage, waste management and remediation activities','Wholesale and retail trade; repair of motor vehicles and motorcycles']
codes = ['AM','CM','IM','WM','AF','CF','IF','WF','FM','FF','TOTAL']
assert len(tokens) == len(sectors)*len(codes), (len(tokens),len(sectors)*len(codes))
# Check each name against text independently of the manually established row order.
compact = lambda s: re.sub(r'\s+', ' ', s).strip().lower()
for sector, page in zip(sectors, [part1]*11+[part2]*8):
    # Text layout interleaves numbers with wrapped names, so check ordered words.
    words = re.findall(r'[a-z]+', sector.lower())
    assert re.search(r'.*?'.join(map(re.escape,words)), compact(page)), sector
mapping = {'AM':('African','Male'),'CM':('Coloured','Male'),'IM':('Indian','Male'),'WM':('White','Male'),'AF':('African','Female'),'CF':('Coloured','Female'),'IF':('Indian','Female'),'WF':('White','Female'),'FM':('Foreign national','Male'),'FF':('Foreign national','Female'),'TOTAL':('All','All')}
rows=[]
for i,sector in enumerate(sectors):
    vals = dict(zip(codes,tokens[i*11:(i+1)*11]))
    dec = lambda c: Decimal(vals[c][:-1])
    black = sum((dec(c) for c in ['AM','CM','IM','AF','CF','IF']),Decimal(0))
    black_female = sum((dec(c) for c in ['AF','CF','IF']),Decimal(0))
    for code in codes:
        raw=vals[code]; population,gender=mapping[code]
        rows.append(dict(reporting_year=2024, row_type='EAP benchmark' if i==0 else 'sector', sector=sector, population_group=population, gender=gender, source_code=code, source_value=raw, percentage=None if raw=='NA' else float(raw[:-1]), black_representation_pct=float(black), black_female_representation_pct=float(black_female), pdf_page=34 if i<=10 else 35))
df=pd.DataFrame(rows)
assert len(df)==209 and not df.duplicated(['sector','source_code']).any()
assert df.percentage.dropna().between(0,100).all()
assert df.percentage.isna().sum()==2 and set(df.loc[df.percentage.isna(),'source_value'])=={'NA'}
assert all((df.groupby('sector').size()==11))
out=ROOT/'data/part_b/processed'; out.mkdir(parents=True,exist_ok=True)
df.to_csv(out/'cee_top_management_2024.csv',index=False,na_rep='')
df.to_parquet(out/'cee_top_management_2024.parquet',index=False)
print('Rows:',len(df),'sectors:',len(sectors)-1,'missing:',df.percentage.isna().sum())
for sector,group in df.groupby('sector',sort=False):
    components = group[group.source_code!='TOTAL'].percentage.sum()
    total = group.loc[group.source_code=='TOTAL','percentage'].iloc[0]
    print(f'{sector}: components={components:.1f}, total={total:.1f}, difference={components-total:+.1f} pp')
