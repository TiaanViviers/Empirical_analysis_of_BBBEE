"""Validated, portable thesis package with a whitelist of allowed payloads."""

import json
import logging
import re
import shutil
from datetime import date
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

from .artifacts import processing_clock, write_json
from .audit import write_csv
from .benchmark import market_event_coverage, return_availability
from .build import DATASET_NAMES
from .config import Config
from .handover_docs import (LIMITATIONS, PRIMARY_KEYS, PURPOSES, data_dictionary,
                            known_limitations, processing_summary, readme)
from .ingest import sha256
from .processed_validation import verify_processed

LOG=logging.getLogger(__name__)


def verify_package(directory: Path) -> dict[str,Any]:
    from .package_verifier import verify
    return verify(directory)


def package(cfg: Config, destination: Path | None = None) -> dict[str, Any]:
    """Validate, stage, verify independently, then replace only the chosen package."""
    verify_processed(cfg)
    processed=cfg.root/"data/processed"
    manifest=json.loads((processed/"build_manifest.json").read_text())
    destination=(destination or cfg.root/"dist/thesis_data").resolve()
    # Do not allow output staging to clobber source or processed directories.
    protected=(cfg.root,cfg.exports,cfg.intermediate,processed,cfg.reports)
    if any(destination==p.resolve() or p.resolve().is_relative_to(destination) or destination.is_relative_to(p.resolve())
           for p in protected[1:]) or destination==cfg.root:
        raise ValueError("Package destination must be separate from source, intermediate, processed and report directories")
    stage=destination.with_name(destination.name+".staging")
    backup=destination.with_name(destination.name+".previous")
    def owned(path: Path) -> bool:
        try:
            return json.loads((path/"manifest.json").read_text()).get("package_type")=="iress-thesis-data"
        except (OSError,ValueError):
            return False
    if destination.exists() and not owned(destination):
        raise ValueError("Refusing to replace a directory that is not an existing IRESS thesis package")
    if stage.exists():
        if not (stage/".iress-staging").exists() and not owned(stage):
            raise ValueError("Refusing to remove an unrecognized staging directory")
        shutil.rmtree(stage)
    stage.mkdir(parents=True)
    (stage/".iress-staging").write_text("iress-thesis-data\n")
    try:
        (stage/"data").mkdir()
        docs=stage/"documentation"
        docs.mkdir()
        for filename in DATASET_NAMES+("market_index.metadata.json",):
            shutil.copy2(processed/filename,stage/"data"/filename)
        # Retain every provenance value, while making the data reference portable.
        market_metadata_path=stage/"data/market_index.metadata.json"
        market_metadata=json.loads(market_metadata_path.read_text())
        market_metadata["original_processing_path"]=market_metadata["path"]
        market_metadata["path"]="data/market_index.parquet"
        write_json(market_metadata_path,market_metadata)
        calendar=[date.fromisoformat(d) for d in manifest["calendar"]["dates"]]
        market=pq.read_table(processed/"market_index.parquet").to_pylist()
        manifest["market_event_coverage"]=market_event_coverage(calendar,return_availability(market,calendar))
        manifest["package_created_at_utc"]=processing_clock()["processed_at_utc"]
        manifest["package_type"]="iress-thesis-data"
        manifest["known_limitations"]=LIMITATIONS+[
            f"Missing benchmark sessions: {manifest['market_index']['missing_company_dates']}."]
        manifest["licence_note"]="IRESS-sourced data; underlying distribution permissions continue to apply."
        for name,entry in manifest["datasets"].items():
            entry.update({"path":"data/"+name,"purpose":PURPOSES[name],"primary_key":PRIMARY_KEYS[name]})
        write_json(docs/"source_inventory.json",{
            "provider":"IRESS Expert","requested_start":manifest["configuration"]["requested_start"],
            "requested_end":manifest["configuration"]["requested_end"],
            "source_workbooks_included":False,"sources":manifest["sources"]})
        write_csv(docs/"trading_calendar.csv",[{"date":d,"source":"observed_company_calendar"} for d in calendar],["date","source"])
        market_events=manifest["market_event_coverage"]
        write_csv(docs/"market_event_coverage.csv",market_events,list(market_events[0]))
        events=manifest["reference_reconciliation"].get("event_coverage",[])
        if events:
            write_csv(docs/"event_coverage.csv",events,list(events[0]))
        else:
            write_csv(docs/"event_coverage.csv",[],["event_id","definition","benchmark_paired_usable_count"])
        (stage/"README.md").write_text(readme(manifest))
        (docs/"data_dictionary.md").write_text(data_dictionary(manifest))
        (docs/"processing_summary.md").write_text(processing_summary(manifest))
        (docs/"known_limitations.md").write_text(known_limitations(manifest))
        shutil.copy2(Path(__file__).with_name("package_verifier.py"),docs/"verify_package.py")
        content=(stage/"README.md").read_text()
        for language,filename in (("python","example_python.py"),("r","example_r.R")):
            snippet=re.search(rf"```{language}\n(.*?)\n```",content,re.DOTALL)
            if snippet is None:
                raise ValueError(f"Missing executable {language} documentation example")
            (docs/filename).write_text(snippet[1]+"\n")
        # The generated documents must never embed this machine's absolute path.
        for path in stage.rglob("*"):
            if path.is_file() and path.suffix in (".md",".json",".py",".R",".csv"):
                if str(cfg.root) in path.read_text():
                    raise ValueError(f"Non-portable path in {path.relative_to(stage)}")
        (stage/".iress-staging").unlink()
        manifest["files"]={p.relative_to(stage).as_posix():{"size_bytes":p.stat().st_size,"sha256":sha256(p)}
                           for p in sorted(stage.rglob("*")) if p.is_file()}
        manifest["manifest_checksum_sidecar"]="manifest.sha256"
        write_json(stage/"manifest.json",manifest)
        (stage/"manifest.sha256").write_text(sha256(stage/"manifest.json")+"  manifest.json\n")
        verify_package(stage)
        if backup.exists():
            if not owned(backup):
                raise ValueError("Refusing to remove an unrecognized backup directory")
            shutil.rmtree(backup)
        if destination.exists():
            destination.replace(backup)
        try:
            stage.replace(destination)
        except Exception:
            if backup.exists() and not destination.exists():
                backup.replace(destination)
            raise
        if backup.exists():
            shutil.rmtree(backup)
        LOG.info("Thesis handover ready: %s",destination)
        return json.loads((destination/"manifest.json").read_text())
    finally:
        if stage.exists():
            shutil.rmtree(stage)
