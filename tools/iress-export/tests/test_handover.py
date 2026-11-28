"""Portable package checks, corruption detection and reader examples."""

import shutil
import json
import subprocess
import sys
from pathlib import Path

import pytest

from test_build import source_project
from iress_data.build import build
from iress_data.handover import package, verify_package


def test_portable_package_and_integrity(source_project) -> None:
    cfg=source_project
    build(cfg)
    result=package(cfg)
    root=cfg.root/"dist/thesis_data"
    manifest=verify_package(root)
    assert result==manifest
    assert manifest["package_type"]=="iress-thesis-data"
    assert len(manifest["datasets"])==5
    metadata=json.loads((root/"data/market_index.metadata.json").read_text())
    assert metadata["path"]=="data/market_index.parquet"
    assert metadata["original_processing_path"]=="data/processed/market_index.parquet"
    assert not any(p.suffix in (".xlsx",".png",".pyc") for p in root.rglob("*"))
    for name in ("README.md","documentation/data_dictionary.md","documentation/known_limitations.md"):
        assert str(cfg.root) not in (root/name).read_text()
    # Relocate the package and use the copied verifier, with no source access.
    relocated=cfg.root.parent/(cfg.root.name+"-relocated")
    shutil.copytree(root,relocated)
    output=subprocess.run([sys.executable,"documentation/verify_package.py"],cwd=relocated,
                          check=True,capture_output=True,text=True)
    assert "PASS:" in output.stdout
    # Instrument selection returns zero rows for synthetic fixture but still reads
    # and filters Parquet and loads the master/benchmark without the repository.
    subprocess.run([sys.executable,"documentation/example_python.py"],cwd=relocated,
                   check=True,capture_output=True,text=True)
    r=shutil.which("Rscript")
    if r:
        subprocess.run([r,"-e","invisible(parse(file='documentation/example_r.R'))"],cwd=relocated,
                       check=True,capture_output=True,text=True)
    second=package(cfg)
    assert result["files"]==second["files"]
    (root/"documentation/known_limitations.md").write_text("tampered")
    with pytest.raises(ValueError,match="file size|checksum"):
        verify_package(root)


def test_package_refuses_existing_unrelated_directory(source_project) -> None:
    cfg=source_project
    build(cfg)
    destination=cfg.root/"unrelated"
    destination.mkdir()
    (destination/"keep.txt").write_text("existing user data")
    with pytest.raises(ValueError,match="not an existing IRESS"):
        package(cfg,destination)
    assert (destination/"keep.txt").read_text()=="existing user data"
