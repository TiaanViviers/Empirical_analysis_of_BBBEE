#!/usr/bin/env python3
"""Safely install the verified metadata handover into the thesis repository."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "dist/thesis_data"

OLD_MANIFEST = ROOT / "metadata/handover_manifest_before_metadata.json"
DATASETS = {
    "instruments.parquet", "instrument_metadata_2026-11-23.parquet",
    "prices_daily.parquet", "prices_observed.parquet",
    "market_index.parquet", "observation_lineage.parquet",
}


def sha256(path: Path) -> str:
    import hashlib
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_standalone(package: Path) -> None:
    subprocess.run([sys.executable, str(package / "documentation/verify_package.py")],
                   cwd=package, check=True)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: transfer_metadata_handover.py PATH_TO_PREVIOUS_HANDOVER_COPY")
    destination = Path(sys.argv[1]).resolve()
    if destination == (ROOT / "../../data/part_a/source/thesis_data").resolve():
        raise SystemExit("Use a separate working copy of the previous handover.")
    stage = destination.with_name(destination.name + ".metadata_staging")
    backup = destination.with_name(destination.name + ".before_metadata")
    if not destination.is_dir() or stage.exists() or backup.exists():
        raise RuntimeError("Thesis package missing or staging/backup path already exists")
    old = json.loads(OLD_MANIFEST.read_text(encoding="utf-8"))
    new = json.loads((SOURCE / "manifest.json").read_text(encoding="utf-8"))
    if sha256(destination / "manifest.json") != sha256(OLD_MANIFEST):
        raise RuntimeError("Thesis package manifest differs from the previous handover")
    verify_standalone(destination)
    verify_standalone(SOURCE)
    if set(new["datasets"]) != DATASETS:
        raise RuntimeError("Updated handover does not contain exactly the six expected Parquet datasets")
    for name in old["datasets"]:
        if new["datasets"][name]["sha256"] != old["datasets"][name]["sha256"]:
            raise RuntimeError(f"Original historical dataset changed: {name}")
    for path in (SOURCE / "documentation/instrument_metadata.md",
                 SOURCE / "documentation/data_dictionary.md",
                 SOURCE / "documentation/known_limitations.md"):
        if not path.is_file():
            raise RuntimeError(f"Missing updated documentation: {path}")
    print("Preflight PASS: thesis files match previous handover; source has six validated datasets")
    shutil.copytree(SOURCE, stage)
    try:
        verify_standalone(stage)
        destination.rename(backup)
        try:
            stage.rename(destination)
            verify_standalone(destination)
        except Exception:
            if destination.exists():
                destination.rename(stage)
            backup.rename(destination)
            raise
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    print(f"Thesis package installed and independently verified: {destination}")
    print(f"Previous thesis package preserved at: {backup}")


if __name__ == "__main__":
    main()
