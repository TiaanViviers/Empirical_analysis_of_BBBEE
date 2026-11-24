#!/usr/bin/env python3
"""Download the official immutable source; refuse to overwrite differing bytes."""
import hashlib, pathlib, subprocess, tempfile
ROOT = pathlib.Path(__file__).resolve().parents[2]
URL = 'https://www.labour.gov.za/DocumentCenter/Reports/Annual%20Reports/Employment%20Equity/2025/25th%20CEE%20Annual%20Report%20Final%2016%20May%202025%20%28Website%29%20%283%29.pdf'
EXPECTED = '96de924bb89b77cb3b2a02537b6c2e207247b5ec09ea7d802b4f44f37358fcde'
target = ROOT / 'data/part_b/raw/cee/cee_25th_annual_report.pdf'
target.parent.mkdir(parents=True, exist_ok=True)
with tempfile.NamedTemporaryFile(dir=target.parent) as f:
    subprocess.run(['curl', '-fL', '--retry', '2', '-o', f.name, URL], check=True)
    data = pathlib.Path(f.name).read_bytes()
    if hashlib.sha256(data).hexdigest() != EXPECTED: raise ValueError('Source checksum changed; inspect before accepting')
    if target.exists() and target.read_bytes() != data: raise ValueError('Existing PDF differs; refusing overwrite')
    if not target.exists(): target.write_bytes(data)
subprocess.run(['pdfinfo', str(target)], check=True)
print('SHA-256 verified:', EXPECTED)
