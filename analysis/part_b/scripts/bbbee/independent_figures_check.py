import csv
r=list(csv.DictReader(open('data/part_b/processed/bbbee_ownership.csv')))
sectors='Agri-BEE|Construction|Financial|Forestry|ICT|Transport|MAC|Property|Tourism|Generic'.split('|')
f7=['4.90 32.00 31.80 15.40 31.30 36.90 26.70 34.10 14.60 0.00','11.20 48.00 21.60 33.70 32.00 40.50 19.60 30.50 23.80 0.00','24.30 50.10 26.00 32.60 30.80 48.60 27.00 37.20 23.80 21.70','23.60 56.40 25.20 54.70 24.30 36.90 40.20 9.90 18.50 33.40','12.27 47.27 19.80 40.95 29.67 46.90 37.45 17.77 36.33 27.20','15.56 52.80 22.39 50.43 26.51 38.80 29.18 9.95 56.39 31.66']
f10=['1.50 3.30 10.00 4.50 8.90 11.50 12.10 12.80 3.90 0.00','4.50 16.90 7.60 10.80 15.10 15.50 7.50 10.10 12.70 0.00','10.60 16.70 9.60 11.40 14.50 20.00 14.40 11.40 9.90 9.70','10.10 15.50 11.20 25.50 12.10 14.70 29.70 3.70 10.50 14.60','6.07 15.53 8.10 14.60 14.50 20.37 23.70 11.30 6.63 19.57','5.29 15.59 8.66 19.89 12.05 19.47 22.33 5.60 30.02 13.80']
f8=['27.83 25.20 29.04 30.56 29.46 33.87','18.41 15.10 17.35 15.96 17.03 19.70','9.42 10.10 11.69 14.60 12.43 14.17']
for fig,table in [(7,f7),(10,f10)]:
 for y,row in enumerate(table,2017):
  for sector,v in zip(sectors,row.split()):
   g=[x for x in r if x['series_id']=='status_2022' and x['source_table']==f'Figure {fig}' and x['reporting_year']==str(y) and x['sector_original']==sector];assert len(g)==1; x=g[0];assert float(x['published_value_original'].replace(',','.').rstrip('%'))==float(v); assert x['source_page_pdf']==str(19 if fig==7 else 21);assert x['ownership_measure']==('reported_black_ownership' if fig==7 else 'reported_black_female_ownership');assert (not x['ownership_pct'])==(sector=='Generic' and y in (2017,2018))
for m,row in zip(['reported_black_ownership','reported_black_male_ownership','reported_black_female_ownership'],f8):
 for y,v in enumerate(row.split(),2017):
  g=[x for x in r if x['series_id']=='status_2022' and x['source_table']=='Figure 8' and x['reporting_year']==str(y) and x['ownership_measure']==m];assert len(g)==1 and g[0]['sector_original']=='National' and g[0]['source_page_pdf']=='20'; assert float(g[0]['published_value_original'].replace(',','.').rstrip('%'))==float(v) and float(g[0]['ownership_pct'])==float(v)
print('Figure 7: 60; Figure 8: 18; Figure 10: 60 — match')
