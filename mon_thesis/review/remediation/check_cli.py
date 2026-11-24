"""Exercise preserved CLI interfaces in an isolated copy, never main outputs."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import tempfile
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'outputs/diagnostics/remediation'
OUT.mkdir(parents=True,exist_ok=True)
temp=Path(tempfile.mkdtemp(prefix='bbbee-corrected-cli-'))
for name in ['R','config','scripts','research','docs']:
    shutil.copytree(ROOT/name,temp/name)
shutil.copy2(ROOT/'run_analysis.R',temp/'run_analysis.R')
(temp/'data').mkdir()
(temp/'data/thesis_data').symlink_to(ROOT/'data/thesis_data',target_is_directory=True)
env=os.environ.copy();env['PART_A_PYTHON']=sys.executable
# A narrow execution list intentionally excludes the explicit 2017 override.
text=(temp/'config/analysis.yml').read_text().replace(
    'events: [mining_charter_2017, mining_charter_2018, ee_draft_2023, ee_final_2025, bbbee_draft_2026]',
    'events: [bbbee_draft_2026]').replace('replications: 4999','replications: 199')
(temp/'config/narrow.yml').write_text(text)
cases=[('single_event_override',['--event','mining_charter_2017','--config','config/narrow.yml','--no-robustness'],'mining_charter_2017'),
       ('narrow_all',['--all','--config','config/narrow.yml','--no-robustness'],'bbbee_draft_2026'),
       ('smoke',['--smoke'],'mining_charter_2017')]
results=[]
for label,args,eid in cases:
    with (OUT/('cli_'+label+'.log')).open('w') as f:
        subprocess.run(['Rscript',str(temp/'run_analysis.R'),*args],env=env,
                       stdout=f,stderr=subprocess.STDOUT,check=True)
    h=pd.read_csv(temp/'outputs/tables/headline_results_percent.csv')
    assert h.event_id.tolist()==[eid]
    assert abs(h.holm_primary_p.iloc[0]-min(1,5*h.p_value.iloc[0]))<1e-12
    meta=json.loads((temp/'outputs/diagnostics/run_metadata.json').read_text())
    selected=meta['events'] if isinstance(meta['events'],list) else [meta['events']]
    assert selected==[eid]
    results.append(dict(case=label,event=eid,p=float(h.p_value.iloc[0]),holm=float(h.holm_primary_p.iloc[0]),
                        reserved_family=5,mode=meta['mode'],status='passed'))
(OUT/'cli_checks.json').write_text(json.dumps(dict(workspace=str(temp),checks=results),indent=2)+'\n')
print(json.dumps(results,indent=2))
