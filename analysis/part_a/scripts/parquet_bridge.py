"""Local Parquet I/O and contracts only; all financial calculations are in R."""
import argparse
import hashlib
import json
import sys
from importlib.metadata import version
from pathlib import Path
import pyarrow as pa
import pyarrow.csv as csv
import pyarrow.parquet as pq


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1048576), b''):
            h.update(chunk)
    return h.hexdigest()


def audit(root, out):
    root = Path(root)
    tables = {}
    keys = {'prices_daily': ['instrument_id', 'date'],
            'instruments': ['instrument_id'],
            'market_index': ['index_id', 'date'],
            'event_industry_classifications': ['event_id', 'instrument_id'],
            'instrument_metadata_2026-11-23': ['instrument_id']}
    for name, key in keys.items():
        path = root / 'data' / (name + '.parquet')
        pf = pq.ParquetFile(path)
        t = pf.read(columns=key)
        # Pandas only handles key uniqueness, never financial analysis.
        d = t.to_pandas()
        if d.isna().any().any() or d.duplicated(key).any():
            raise ValueError('Null/duplicate primary key: ' + name)
        tables[name] = {'rows': len(d), 'key': key, 'sha256': sha(path),
                        'schema': {f.name: str(f.type) for f in pf.schema_arrow}}
    Path(out).write_text(json.dumps({'pyarrow': pa.__version__, 'pandas': version('pandas'), 'python': sys.version, 'tables': tables}, indent=2) + '\n')


p = argparse.ArgumentParser()
p.add_argument('action', choices=['read', 'write', 'audit', 'fingerprint'])
p.add_argument('source')
p.add_argument('target')
p.add_argument('--columns', default='')
a = p.parse_args()
if a.action == 'read':
    t = pq.read_table(a.source, columns=a.columns.split(',') if a.columns else None)
    csv.write_csv(t, a.target)
elif a.action == 'write':
    # R writes explicit ISO dates. Typed date32 is retained in derived Parquet.
    header = Path(a.source).open().readline().strip().replace('"', '').split(',')
    date_cols = {c: pa.date32() for c in header if c == 'date' or c.endswith('_date') or c == 'bulletin_month'}
    t = csv.read_csv(a.source, convert_options=csv.ConvertOptions(
        column_types=date_cols, strings_can_be_null=True,
        null_values=['', 'NA'], true_values=['TRUE'], false_values=['FALSE']))
    pq.write_table(t, a.target, compression='zstd')
elif a.action == 'audit':
    audit(a.source, a.target)
else:
    root = Path(a.source)
    files = sorted(p for p in root.rglob('*') if p.is_file())
    Path(a.target).write_text(json.dumps({str(p.relative_to(root)): sha(p) for p in files}, indent=2) + '\n')
