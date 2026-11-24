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
OUT = ROOT / "outputs/diagnostics/remediation"
OUT.mkdir(parents=True, exist_ok=True)
workspace = Path(tempfile.mkdtemp(prefix="bbbee-corrected-reproduction-"))
for name in ("R", "config", "scripts", "research", "docs"):
    shutil.copytree(ROOT / name, workspace / name)
shutil.copy2(ROOT / "run_analysis.R", workspace / "run_analysis.R")
(workspace / "data").mkdir()
(workspace / "data/thesis_data").symlink_to(ROOT / "data/thesis_data", target_is_directory=True)
(workspace / "outputs/baselines").mkdir(parents=True)
baseline = ROOT / "outputs/baselines/pre_remediation_2026-11-24"
(workspace / "outputs/baselines" / baseline.name).symlink_to(baseline, target_is_directory=True)
env = os.environ.copy()
env["PART_A_PYTHON"] = sys.executable
with (OUT / "corrected_reproduction.log").open("w") as log:
    subprocess.run(["Rscript", str(workspace / "run_analysis.R"), "--all"],
                   env=env, stdout=log, stderr=subprocess.STDOUT, check=True)

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

checks = {}
for directory, pattern in (("outputs/tables", "*.csv"), ("data/derived", "*.parquet")):
    original = {p.name: p for p in (ROOT / directory).glob(pattern)}
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
