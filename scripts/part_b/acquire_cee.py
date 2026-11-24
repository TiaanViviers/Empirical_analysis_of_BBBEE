#!/usr/bin/env python3
"""Acquire original CEE reports; preserve existing documents, check PDF readability."""
from pathlib import Path
import subprocess, tempfile
ROOT=Path(__file__).resolve().parents[2]
base='https://eecms.co.za/wp-content/uploads/'
urls={17:base+'17th-CEE-Annual-Report-2016-to-2017.pdf',18:base+'18th-CEE-Annual-Report-2017-to-2018.pdf',19:base+'19th-CEE-Annual-Report_.pdf',20:'https://www.labour.gov.za/DocumentCenter/PublishingImages/20th-commission-for-employment-equity-report/20th%20Commission%20for%20Employment%20Equity%20Report.pdf',21:base+'21st-CEE-Annual-Report-2020-to-2021.pdf',22:'https://www.labour.gov.za/DocumentCenter/Reports/Annual%20Reports/Employment%20Equity/2021/22nd%20CEE%20Annual%20Report.pdf',23:base+'23rd-CEE-Annual-Report-2022-to-2023.pdf',24:'https://www.labour.gov.za/DocumentCenter/Reports/Annual%20Reports/Employment%20Equity/2024/24th%20Commission%20for%20Employment%20Equity%20Annual%20Report.pdf',25:'https://www.labour.gov.za/DocumentCenter/Reports/Annual%20Reports/Employment%20Equity/2025/25th%20CEE%20Annual%20Report%20Final%2016%20May%202025%20%28Website%29%20%283%29.pdf',26:'https://www.labour.gov.za/DocumentCenter/Reports/Annual%20Reports/Employment%20Equity/2026/26th%20CEE%20Report.pdf'}
def main():
 dest=ROOT/'data/part_b/raw/cee';dest.mkdir(parents=True,exist_ok=True)
 for edition,url in urls.items():
  suffix='st' if edition==21 else 'nd' if edition==22 else 'rd' if edition==23 else 'th'
  path=dest/f'cee_{edition}{suffix}_annual_report.pdf'
  if path.exists(): print(edition,'existing',flush=True);continue
  with tempfile.NamedTemporaryFile(dir=dest) as f:
   p=subprocess.run(['curl','-fsSL','--connect-timeout','20','--max-time','150','-o',f.name,url])
   if p.returncode or subprocess.run(['pdfinfo',f.name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode: print(edition,'FAILED',url,flush=True);continue
   Path(f.name).replace(path);print(edition,'downloaded',flush=True)

if __name__ == '__main__': main()
