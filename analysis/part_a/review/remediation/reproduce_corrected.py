"""Reproduce corrected full-run tables in isolation without replacing main outputs."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "../../outputs/part_a/diagnostics/remediation"
OUT.mkdir(parents=True, exist_ok=True)
workspace = Path(tempfile.mkdtemp(prefix="bbbee-corrected-reproduction-"))
for name in ("R", "config", "scripts", "research"):
    shutil.copytree(ROOT / name, workspace / name)
shutil.copy2(ROOT / "run_analysis.R", workspace / "run_analysis.R")
(workspace / "data").mkdir()
(workspace / "data/thesis_data").symlink_to((ROOT / "../../data/part_a/source/thesis_data").resolve(), target_is_directory=True)
(workspace / "outputs/baselines").mkdir(parents=True)
baseline = (ROOT / "../../archive/part_a/pre_remediation_2026-11-24").resolve()
(workspace / "outputs/baselines" / baseline.name).symlink_to(baseline, target_is_directory=True)
config = workspace / 'config/analysis.yml'
text = config.read_text()
text = text.replace('../../data/part_a/source/thesis_data', 'data/thesis_data')
text = text.replace('../../data/part_a/derived', 'data/derived')
text = text.replace('../../outputs/part_a', 'outputs')
text = text.replace('../../archive/part_a/pre_remediation_2026-11-24', 'outputs/baselines/pre_remediation_2026-11-24')
config.write_text(text)
env = os.environ.copy()
env["PART_A_PYTHON"] = sys.executable
with (OUT / "corrected_reproduction.log").open("w") as log:
    subprocess.run(["Rscript", str(workspace / "run_analysis.R"), "--all"],
                   env=env, stdout=log, stderr=subprocess.STDOUT, check=True)

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

checks = {}
for directory, pattern in (("outputs/tables", "*.csv"), ("data/derived", "*.parquet")):
    original_dir = ROOT / ("../../" + ("outputs/part_a/tables" if directory == "outputs/tables" else "data/part_a/derived"))
    original = {p.name: p for p in original_dir.glob(pattern)}
    reproduced = {p.name: p for p in (workspace / directory).glob(pattern)}
    assert original and original.keys() == reproduced.keys(), directory
    for name, path in sorted(original.items()):
        checks[f"{directory}/{name}"] = {
            "original_sha256": digest(path), "reproduced_sha256": digest(reproduced[name])}
        checks[f"{directory}/{name}"]["identical"] = (
            checks[f"{directory}/{name}"]["original_sha256"] ==
            checks[f"{directory}/{name}"]["reproduced_sha256"])
result = {"workspace": str(workspace), "checks": checks,
          "all_identical": all(row["identical"] for row in checks.values())}
(OUT / "revised_reproduction.json").write_text(json.dumps(result, indent=2) + "\n")
assert result["all_identical"], "Reproduction differs: inspect revised_reproduction.json"
print(f"Reproduced {len(checks)} table/Parquet files byte-for-byte in {workspace}.")
