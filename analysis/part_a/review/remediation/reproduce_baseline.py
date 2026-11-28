"""Reproduce the archived original implementation without changing current outputs.

Use the Python/PyArrow environment. --restore-derived restores only missing local
baseline Parquet copies after checking their archived SHA-256, never overwriting
an existing baseline file.
"""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'../../archive/part_a/pre_remediation_2026-11-24'
OUT=ROOT/'../../outputs/part_a/diagnostics/remediation'
OUT.mkdir(parents=True,exist_ok=True)
source=json.loads((BASE/'source_fingerprints.json').read_text())
sha=lambda p:hashlib.file_digest(p.open('rb'),'sha256').hexdigest()
for name,digest in source.items():
    assert sha((ROOT/'../../data/part_a/source/thesis_data').resolve()/name)==digest, 'Original source version differs: '+name
temp=Path(tempfile.mkdtemp(prefix='bbbee-original-reproduction-'))
shutil.copytree(BASE/'project',temp,dirs_exist_ok=True)
(temp/'data').mkdir()
(temp/'data/thesis_data').symlink_to((ROOT/'../../data/part_a/source/thesis_data').resolve(),target_is_directory=True)
env=os.environ.copy()
env['PART_A_PYTHON']=sys.executable  # Keep virtual-environment path intact.
env['TZ']='Africa/Johannesburg'
for command,log in [(['Rscript',str(temp/'run_analysis.R'),'--all'],'original_pipeline_rerun.log'),
                    (['Rscript',str(temp/'tests/testthat.R')],'original_tests_rerun.log')]:
    with (OUT/log).open('w') as f:
        subprocess.run(command,env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
comparison={p.name:p.read_bytes()==(temp/'outputs/tables'/p.name).read_bytes()
            for p in (BASE/'tables').glob('*.csv')}
assert all(comparison.values()), comparison
manifest=json.loads((BASE/'archive_manifest.json').read_text())
restored=[]
if '--restore-derived' in sys.argv:
    (BASE/'derived').mkdir(exist_ok=True)
    for p in (temp/'data/derived').glob('*.parquet'):
        target=BASE/'derived'/p.name
        if target.exists():
            assert sha(target)==manifest['derived/'+p.name], 'Existing baseline differs; refusing overwrite'
            continue
        assert sha(p)==manifest['derived/'+p.name], 'Physical Parquet differs; use original recorded environment'
        shutil.copy2(p,target)
        restored.append(p.name)
(OUT/'baseline_reproduction.json').write_text(json.dumps(dict(workspace=str(temp),
    statistical_tables_identical=comparison,restored_missing_derived=restored),indent=2)+'\n')
print('Original nine tables and tests reproduced in',temp)
