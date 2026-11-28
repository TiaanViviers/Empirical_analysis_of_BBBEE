"""Process the dated IRESS Screener snapshot and extend the portable handover."""

from __future__ import annotations

import base64
import csv
from datetime import date, datetime, timezone
import json
from pathlib import Path
import re
import shutil
from zoneinfo import ZoneInfo

import pyarrow as pa
import pyarrow.parquet as pq

from .artifacts import schema_inventory, write_json
from .ingest import sha256
from .package_verifier import verify as verify_package


SNAPSHOT_DATE = date(2026, 11, 23)
FILENAME = "instrument_metadata_2026-11-23.parquet"
SCREENER_ONLY = {"IMRP17:XJSE:EQU", "IMRP18:XJSE:EQU", "PBT_DEL:XJSE:EQU"}
SOURCE_FIELDS = {
    "captured_at", "position", "instrument_id", "company_name", "ticker", "isin",
    "isin_format_valid", "instrument_type", "exchange", "country", "listing_status",
    "landing_href",
}


def field(name: str, datatype: pa.DataType, description: str, nullable: bool = False) -> pa.Field:
    return pa.field(name, datatype, nullable=nullable,
                    metadata={b"description": description.encode("utf-8")})


SCHEMA = pa.schema([
    field("instrument_id", pa.string(), "Full decoded IRESS mnemonic; primary key."),
    field("ticker", pa.string(), "Original Screener ticker; not a permanent issuer identifier."),
    field("company_name", pa.string(), "Original Screener company name at capture."),
    field("isin_raw", pa.string(), "Original Screener ISIN field, unchanged, including placeholders.", True),
    field("isin_valid", pa.bool_(), "Strict ISO 6166 format and Luhn check digit both pass."),
    field("isin_format_valid_source", pa.bool_(), "Format-only flag in the extraction CSV."),
    field("instrument_type", pa.string(), "Original IRESS instrument-type label."),
    field("exchange", pa.string(), "Original IRESS exchange label."),
    field("country", pa.string(), "Original IRESS country label."),
    field("listing_status_snapshot", pa.string(), "Listed/Delisted on snapshot date only."),
    field("snapshot_date", pa.date32(), "Local date of this Screener snapshot."),
    field("captured_at", pa.timestamp("us", tz="Africa/Johannesburg"),
          "Actual extraction timestamp from the validated summary."),
    field("has_historical_prices_record", pa.bool_(),
          "Instrument ID occurs in the 1,869-row historical instrument master."),
    field("screener_position", pa.int32(), "1-based row position in the 1,872-result snapshot."),
    field("landing_href", pa.string(), "Original IRESS InstrumentLanding href; provenance only."),
])


def valid_isin(value: str | None) -> bool:
    """ISO 6166 structure plus Luhn modulus 10 on expanded alphanumeric text."""
    if not value or re.fullmatch(r"[A-Z]{2}[A-Z0-9]{9}[0-9]", value) is None:
        return False
    digits = "".join(str(ord(char) - 55) if char.isalpha() else char for char in value)
    total = 0
    for position, char in enumerate(reversed(digits)):
        number = int(char) * (2 if position % 2 else 1)
        total += number // 10 + number % 10
    return total % 10 == 0


def decode_href(href: str) -> str:
    prefix = "#/InstrumentLanding/"
    if not href.startswith(prefix):
        raise ValueError(f"Unexpected IRESS href: {href!r}")
    token = href[len(prefix):].split("?", 1)[0]
    token += "=" * (-len(token) % 4)
    return base64.b64decode(token, validate=True).decode("utf-8")


def process_metadata(csv_path: Path, summary_path: Path, master_path: Path,
                     output_path: Path) -> dict:
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if summary.get("final_status") != "PASS":
        raise ValueError("Screener source summary is not validated PASS")
    if sha256(csv_path) != summary["csv_sha256"]:
        raise ValueError("Screener source CSV checksum differs from validated summary")
    captured_raw = summary["captured_at"]
    captured_at = datetime.fromisoformat(captured_raw)
    if captured_at.tzinfo is None:
        raise ValueError("Screener capture timestamp has no timezone")
    captured_at = captured_at.astimezone(ZoneInfo("Africa/Johannesburg"))
    if captured_at.date() != SNAPSHOT_DATE:
        raise ValueError(f"Expected snapshot date {SNAPSHOT_DATE}, got {captured_at.date()}")
    master_ids = set(pq.read_table(master_path, columns=["instrument_id"])
                     .column("instrument_id").to_pylist())
    if len(master_ids) != 1869:
        raise ValueError(f"Historical instrument master has {len(master_ids)} IDs, expected 1869")
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if set(reader.fieldnames or ()) != SOURCE_FIELDS:
            raise ValueError(f"Unexpected Screener CSV schema: {reader.fieldnames}")
        source_rows = list(reader)
    if len(source_rows) != summary["rows"] or len(source_rows) != 1872:
        raise ValueError("Screener CSV row count differs from validated 1,872-row summary")
    records = []
    seen = set()
    for position, source in enumerate(source_rows, 1):
        instrument_id = source["instrument_id"]
        if not instrument_id or instrument_id in seen:
            raise ValueError(f"Blank or duplicate instrument ID at Screener row {position}")
        seen.add(instrument_id)
        if source["position"] != str(position):
            raise ValueError(f"Screener position mismatch at row {position}")
        if source["captured_at"] != captured_raw:
            raise ValueError(f"Screener capture timestamp changed at row {position}")
        if decode_href(source["landing_href"]) != instrument_id:
            raise ValueError(f"IRESS href does not decode to {instrument_id}")
        isin = source["isin"]
        source_format = source["isin_format_valid"]
        if source_format not in ("True", "False"):
            raise ValueError(f"Unexpected source ISIN format flag: {source_format!r}")
        format_valid = re.fullmatch(r"[A-Z]{2}[A-Z0-9]{9}[0-9]", isin) is not None
        if format_valid != (source_format == "True"):
            raise ValueError(f"Source ISIN format flag differs at row {position}")
        records.append({
            "instrument_id": instrument_id,
            "ticker": source["ticker"],
            "company_name": source["company_name"],
            "isin_raw": isin,
            "isin_valid": valid_isin(isin),
            "isin_format_valid_source": format_valid,
            "instrument_type": source["instrument_type"],
            "exchange": source["exchange"],
            "country": source["country"],
            "listing_status_snapshot": source["listing_status"],
            "snapshot_date": SNAPSHOT_DATE,
            "captured_at": captured_at,
            "has_historical_prices_record": instrument_id in master_ids,
            "screener_position": position,
            "landing_href": source["landing_href"],
        })
    if seen - master_ids != SCREENER_ONLY or master_ids - seen:
        raise ValueError("Screener/master ID reconciliation differs from validated result")
    valid_count = sum(row["isin_valid"] for row in records)
    if valid_count != 1492 or len(records) - valid_count != 380:
        raise ValueError(f"ISIN validity count differs: {valid_count} valid")
    table = pa.Table.from_pylist(records, schema=SCHEMA.with_metadata({
        b"source": b"IRESS Expert Screener visible UI",
        b"source_csv_sha256": summary["csv_sha256"].encode(),
        b"snapshot_date": SNAPSHOT_DATE.isoformat().encode(),
    }))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(".pending.parquet")
    pq.write_table(table, temporary, compression="zstd", version="2.6")
    check = pq.read_table(temporary)
    if not check.equals(table, check_metadata=True):
        temporary.unlink(missing_ok=True)
        raise ValueError("Metadata Parquet round-trip differs from transformed source")
    # Recheck every original provider value after serialisation.
    for source, saved in zip(source_rows, check.to_pylist(), strict=True):
        for source_name, saved_name in (("instrument_id", "instrument_id"),
                                        ("ticker", "ticker"),
                                        ("company_name", "company_name"),
                                        ("isin", "isin_raw"),
                                        ("instrument_type", "instrument_type"),
                                        ("exchange", "exchange"),
                                        ("country", "country"),
                                        ("listing_status", "listing_status_snapshot"),
                                        ("landing_href", "landing_href")):
            if source[source_name] != saved[saved_name]:
                temporary.unlink(missing_ok=True)
                raise ValueError(f"Source value changed in Parquet: {source_name}")
    temporary.replace(output_path)
    return {"rows": len(records), "unique_instruments": len(seen),
            "valid_isins": valid_count, "nonstandard_isins": len(records) - valid_count,
            "historical_master_matches": len(master_ids),
            "screener_only_ids": sorted(SCREENER_ONLY),
            "captured_at": captured_raw, "source_csv_sha256": summary["csv_sha256"],
            "processed_parquet_sha256": sha256(output_path)}


def _replace(text: str, old: str, new: str) -> str:
    if old not in text:
        raise ValueError(f"Package documentation anchor missing: {old[:80]!r}")
    return text.replace(old, new, 1)


def update_documentation(stage: Path, metrics: dict) -> None:
    readme = stage / "README.md"
    text = readme.read_text(encoding="utf-8")
    text = _replace(text, "Data version **1.0.0**", "Data version **1.1.0**")
    text = _replace(text,
        "| [data/instruments.parquet](data/instruments.parquet) | 1,869 | 1,869 | 2016-01-04 to 2026-03-31 | instrument_id |",
        "| [data/instruments.parquet](data/instruments.parquet) | 1,869 | 1,869 | 2016-01-04 to 2026-03-31 | instrument_id |\n"
        "| [data/instrument_metadata_2026-11-23.parquet](data/instrument_metadata_2026-11-23.parquet) | 1,872 | 1,872 | Snapshot: 2026-11-23 | instrument_id |")
    text = _replace(text, "- **instruments** supplies one descriptive record per original mnemonic, with all source batches/files and unknown identifiers represented as nulls.",
        "- **instruments** supplies one descriptive record per original mnemonic, with all source batches/files and unknown identifiers represented as nulls.\n"
        "- **instrument_metadata_2026-11-23** supplies dated Screener labels and raw ISINs; it is a later snapshot, not historical classification. All 1,869 master IDs match, and three additional Screener IDs have no historical price master record.")
    text = _replace(text, "- [documentation/data_dictionary.md](documentation/data_dictionary.md): exhaustive fields, exact Arrow types, nullability, units and flag definitions.",
        "- [documentation/data_dictionary.md](documentation/data_dictionary.md): exhaustive fields, exact Arrow types, nullability, units and flag definitions.\n"
        "- [documentation/instrument_metadata.md](documentation/instrument_metadata.md): capture, ISIN checks, reconciliation, joins and point-in-time limits.")
    text = _replace(text, "The source screener later reported 1,872 results, while the audited extraction has 1,869 distinct IDs and 1,871 batch-level appearances. Batch 13 has 99 IDs. The manifest's purported missing “Pbt Group Limited” requires reconciliation: `PBT:XJSE:EQU` is actually present as “Pbt Holdings Limited.” Counts and name discrepancies do not identify omitted securities without a dated authoritative identifier snapshot. Universe completeness and survivorship-bias freedom remain unverified.",
        "The independently captured **2026-11-23 Screener snapshot** has 1,872 distinct IDs and matches all 1,869 historical-price master IDs; three IDs occur only in the snapshot. The historical batch-13 export had 99 rows, but identifier-level reconciliation confirms that its 1,869-ID combined master is covered by this later Screener view. The snapshot cannot prove the exchange's historical universe or survivorship-bias freedom.")
    text = _replace(text, "Verified historical sectors, ISIN mappings, issuer relationships and listing histories are absent.",
        "The dated Screener snapshot supplies raw ISIN fields and current listing labels, but verified historical sectors, ISIN histories, issuer relationships and listing histories remain absent.")
    text = _replace(text, "Use explicit filenames because the five datasets have different schemas.",
        "Use explicit filenames because the six datasets have different schemas. Join `data/instrument_metadata_2026-11-23.parquet` to `data/instruments.parquet` on `instrument_id` as one-to-one for the 1,869 master IDs; use a left join from the master to retain its universe. The three Screener-only IDs have no historical-price master row. Never use the 2026 listing label to select firms for earlier dates.")
    readme.write_text(text, encoding="utf-8")

    dictionary = stage / "documentation/data_dictionary.md"
    text = dictionary.read_text(encoding="utf-8")
    section = ["## instrument_metadata_2026-11-23.parquet", "",
               "IRESS Expert Screener snapshot captured 2026-11-23. One row per instrument ID; join to `instruments.parquet` on `instrument_id`. Snapshot labels are not historical attributes. Primary key: `instrument_id`.", "",
               "| Column | Arrow type | Nullable | Units | Definition and caveat |",
               "| --- | --- | --- | --- | --- |"]
    for item in schema_inventory(SCHEMA):
        section.append(f"| `{item['name']}` | `{item['type']}` | {'yes' if item['nullable'] else 'no'} | Not applicable | {item['description']} |")
    section.append("")
    text = _replace(text, "## market_index.parquet", "\n".join(section) + "\n## market_index.parquet")
    text = _replace(text, "prices_daily → instruments is many-to-one on instrument_id.",
        "prices_daily → instruments is many-to-one on instrument_id. instruments → instrument_metadata_2026-11-23 is one-to-one on instrument_id for all 1,869 master IDs; three metadata IDs have no master row. Snapshot status must not be backdated.")
    dictionary.write_text(text, encoding="utf-8")

    limitations = stage / "documentation/known_limitations.md"
    text = limitations.read_text(encoding="utf-8")
    text = _replace(text,
        "4. Actual listing/delisting/suspension histories, ISINs, issuer mappings and historical sectors are unavailable.",
        "4. Actual listing/delisting/suspension histories, issuer mappings, historical ISIN validity and historical sectors are unavailable. The 2026-11-23 snapshot supplies raw ISIN fields and current labels only; 380 ISIN fields are nonstandard or placeholders.")
    text = _replace(text,
        "The original screener count and PBT name discrepancy require an identifier-level reconciliation, not name-based merging.",
        "The 2026-11-23 Screener snapshot matches all 1,869 historical master IDs and has three additional IDs; this is a dated source comparison, not proof of historical universe completeness. PBT name differences still require identifier-level treatment, not name-based merging.")
    limitations.write_text(text, encoding="utf-8")

    (stage / "documentation/instrument_metadata.md").write_text(
        "# IRESS Screener instrument metadata — 2026-11-23\n\n"
        "This file describes `data/instrument_metadata_2026-11-23.parquet`, a dated capture of the user-visible IRESS Expert Screener table. "
        f"Capture time: `{metrics['captured_at']}`. The extraction used Type=Equities and Companies, Exchange=Jse Securities Exchange, "
        "Listing Status=Listed and Delisted, 100 results per page. Nineteen pages were validated against their visible ranges and instrument IDs before collection. "
        "The source CSV is retained in the data engineering repository; it is intentionally outside this portable handover. "
        f"Source CSV SHA-256: `{metrics['source_csv_sha256']}`.\n\n"
        "## Scope and reconciliation\n\n"
        "The snapshot has 1,872 rows and 1,872 unique `instrument_id` values. It covers every ID in the 1,869-row historical-price `instruments.parquet` master. "
        "The three snapshot-only IDs are `IMRP17:XJSE:EQU`, `IMRP18:XJSE:EQU`, and `PBT_DEL:XJSE:EQU`; "
        "`has_historical_prices_record` is false for those rows. Use an exact `instrument_id` join, not company names or ticker alone. "
        "From the master, the join is one-to-one with no missing metadata; from metadata, the three extra rows are unmatched.\n\n"
        "## ISIN handling\n\n"
        "`isin_raw` reproduces the provider field exactly. `isin_valid` requires strict ISO 6166 structure and a passing Luhn check digit. "
        "1,492 values pass both; 380 are nonstandard or placeholders and remain unchanged. "
        "A passing check digit checks syntax and internal consistency, not whether the ISIN belongs to that security at any date. "
        "`isin_format_valid_source` preserves the extractor's format-only flag.\n\n"
        "## Time and interpretation\n\n"
        "`snapshot_date` is the local capture date and `captured_at` records the actual timezone-aware extraction time. "
        "`listing_status_snapshot`, `company_name`, `instrument_type`, `exchange`, `country`, and `isin_raw` describe the Screener display on that date. "
        "They do not establish values at earlier event dates. Do not use the snapshot's Listed/Delisted label to build historical samples, infer listing dates, or assign ordinary/preference share classes. "
        "No sector, issuer mapping, or historical status was inferred.\n\n"
        "## Join example\n\n"
        "```python\n"
        "import pyarrow.parquet as pq\n"
        "master = pq.read_table('data/instruments.parquet').select(['instrument_id', 'ticker', 'company_name'])\n"
        "snapshot = pq.read_table('data/instrument_metadata_2026-11-23.parquet')\n"
        "# Exact-key one-to-one join. Select master columns needed for analysis;\n"
        "# Arrow joins do not support the master's list-valued company_names field.\n"
        "enriched = master.join(snapshot, keys='instrument_id', join_type='left outer', right_suffix='_snapshot')\n"
        "```\n\n"
        "The package verifier checks the Parquet schema, checksums, counts, ISIN flags, and master reconciliation.\n",
        encoding="utf-8",
    )


def augment_handover(package_root: Path, processed_path: Path, metrics: dict) -> dict:
    """Stage and verify the extended package, preserving the previous handover."""
    package_root = package_root.resolve()
    verify_package(package_root)
    if (package_root / "data" / FILENAME).exists():
        raise ValueError("Handover already includes dated metadata; refusing to overwrite")
    stage = package_root.with_name(package_root.name + ".metadata_staging")
    backup = package_root.with_name(package_root.name + ".before_metadata")
    if stage.exists() or backup.exists():
        raise ValueError("Metadata staging or previous-package path already exists")
    shutil.copytree(package_root, stage)
    try:
        shutil.copy2(processed_path, stage / "data" / FILENAME)
        update_documentation(stage, metrics)
        verifier_source = Path(__file__).with_name("package_verifier.py")
        shutil.copy2(verifier_source, stage / "documentation/verify_package.py")
        manifest = json.loads((stage / "manifest.json").read_text(encoding="utf-8"))
        manifest["dataset_version"] = "1.1.0"
        manifest["package_created_at_utc"] = datetime.now(timezone.utc).isoformat()
        manifest["instrument_metadata_snapshot"] = {
            "snapshot_date": SNAPSHOT_DATE.isoformat(),
            "captured_at": metrics["captured_at"],
            "source_system": "IRESS Expert Screener visible UI",
            "source_csv_sha256": metrics["source_csv_sha256"],
            "isin_validation": "ISO 6166 structure and Luhn check digit",
            "valid_isins": metrics["valid_isins"],
            "nonstandard_isins": metrics["nonstandard_isins"],
            "historical_master_matches": metrics["historical_master_matches"],
            "screener_only_ids": metrics["screener_only_ids"],
            "implementation_sha256": sha256(Path(__file__)),
        }
        manifest["datasets"][FILENAME] = {
            "filename": FILENAME, "path": "data/" + FILENAME,
            "dataset_version": "1.0.0", "rows": metrics["rows"],
            "unique_instruments": metrics["unique_instruments"],
            "date_coverage_basis": "snapshot_date",
            "date_start": SNAPSHOT_DATE.isoformat(), "date_end": SNAPSHOT_DATE.isoformat(),
            "primary_key": ["instrument_id"],
            "purpose": "Dated IRESS Screener labels, raw ISINs and reconciliation to historical master",
            "size_bytes": (stage / "data" / FILENAME).stat().st_size,
            "sha256": sha256(stage / "data" / FILENAME),
            "columns": schema_inventory(pq.read_schema(stage / "data" / FILENAME)),
        }
        manifest["files"] = {
            p.relative_to(stage).as_posix(): {"size_bytes": p.stat().st_size,
                                              "sha256": sha256(p)}
            for p in sorted(stage.rglob("*"))
            if p.is_file() and p.name not in ("manifest.json", "manifest.sha256")
        }
        write_json(stage / "manifest.json", manifest)
        (stage / "manifest.sha256").write_text(
            sha256(stage / "manifest.json") + "  manifest.json\n", encoding="utf-8"
        )
        verify_package(stage)
        package_root.rename(backup)
        try:
            stage.rename(package_root)
        except Exception:
            backup.rename(package_root)
            raise
        return manifest
    finally:
        if stage.exists():
            shutil.rmtree(stage)
