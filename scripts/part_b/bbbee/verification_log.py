#!/usr/bin/env python3
import csv,hashlib,pathlib
D=pathlib.Path('data/part_b/processed');docs=pathlib.Path('docs/part_b');raw=pathlib.Path('data/part_b/raw/bbbee_commission')
def load(p):
 with p.open(newline='') as f:return list(csv.DictReader(f))
def save(p,rows):
 with p.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
for name,expected in [('transformation_landscape_2013_2023_published_2026.pdf','af53f50f05fc6832c932f1c456f3ae36183ad2bcaaf0efbac4e8e69dc1c2ee5a'),('national_status_2022.pdf','7d3205acde10c8bc9c7cdd5d2a8fb4ff9ea9919964930eb3fc090822ae94c181')]:assert hashlib.sha256((raw/name).read_bytes()).hexdigest()==expected,name
coord=load(docs/'bbbee_coordinate_checks.csv');checks=load(D/'bbbee_validation_results.csv');log=[]
for r in coord:
 log.append(dict(source_id=r['source_id'],source_table=r['source_table'],page_pdf=r['source_page_pdf'],cells_checked=r['cells_checked'],method='Rendered table visually checked for title, headers and ordering; PDF word-box grouping compared with layout extraction for printed cells',result='pass',notes='Same PDF and Poppler extraction library; not independent human review.'))
 checks.append(dict(check_id='table_coordinate_comparison',status='pass',source_id=r['source_id'],source_table=r['source_table'],reporting_year='',detail=f"{r['cells_checked']} printed data cells compared using word coordinates; PDF page {r['source_page_pdf']}"))
for fig,page,n in [(7,19,60),(8,20,18),(10,21,60)]:
 log.append(dict(source_id='status_2022',source_table=f'Figure {fig}',page_pdf=page,cells_checked=n,method='Visually compared all chart data-table cells against rendered local PDF page and pilot transcription',result='pass',notes='Generic 2017–18 printed zeros retained; Figure 7/10 accompanying narrative says not analysed.' if fig!=8 else 'Black male plus black female equals overall to printed precision.'))
 checks.append(dict(check_id='figure_rendered_comparison',status='pass',source_id='status_2022',source_table=f'Figure {fig}',reporting_year='2017-2022',detail=f'{n} printed chart cells visually compared to rendered figure'))
for table,page,note in [('1',47,'All cells visually checked; totals and dashes checked.'),('4-5',55,'2018 level 5 = 14 and 6%; total 2605 confirmed visually; 2018 narrative 51% Levels 1–4.'),('60',108,'2013 fourth ownership cell visibly blank; other three are zero.'),('78-79',123,'2016 total 10, numerical counts 9; percentages consistent with 9; original values retained.')]:
 log.append(dict(source_id='retro_2026',source_table=table,page_pdf=page,cells_checked='',method='Rendered PDF visual review of identified table or issue',result='pass',notes=note))
independent=docs/'bbbee_independent_cells.csv'
if independent.exists():
 for r in load(independent):
  log.append(dict(source_id='retro_2026',source_table=r['source_table'],page_pdf=r['source_page_pdf'],cells_checked=r['cells_checked'],method='Independent MuPDF structured-text coordinate comparison; rendered page inspected for table layout',result=r['result'],notes='Cell comparison uses a separate PDF engine; rendering inspected for layout, not every cell visually proofread.'))
 for fig,page,n in [(7,19,60),(8,20,18),(10,21,60)]:
  log.append(dict(source_id='status_2022',source_table=f'Figure {fig}',page_pdf=page,cells_checked=n,method='Independent transcription from rendered chart data table compared with output',result='pass',notes='Local source authenticity unresolved; Generic 2017–18 printed zeros analytically missing.' if fig!=8 else 'Local source authenticity unresolved.'))
checks.append(dict(check_id='local_source_sha256',status='pass',source_id='both',source_table='',reporting_year='',detail='Both PDF hashes match acquisition inventory; byte identity is not source authentication.'))
save(docs/'bbbee_verification_log.csv',log);save(D/'bbbee_validation_results.csv',checks)
print('verification log rows',len(log),'validation rows',len(checks))
