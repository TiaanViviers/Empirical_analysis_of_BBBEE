# IRESS JSE historical data processing and handover

The approved conservative pipeline audits, standardises and packages the supplied company exports and benchmark for Monique's thesis research. It preserves the existing Playwright exporter and original licensed workbooks. It does not build the final event-study sample or estimate CAR/CAAR, regressions or policy effects. The principal researcher-facing guide is [validated package README](../../data/part_a/source/thesis_data/README.md).

Use Python 3.12 and the locked `uv` environment:

```bash
uv sync --locked
uv run python -m iress_data audit
uv run python -m iress_data build
uv run python -m iress_data verify
uv run python -m iress_data package
uv run python -m iress_data verify-package
uv run pytest -q
```

The completed Phase 1 audit is retained as evidence. Re-running EDA is unnecessary for the approved build: `build` reuses source/hash-verified intermediates, validates conflicts and quantities, retains all placeholders, and runs deep source/output verification. `verify` validates the processed generation when its build manifest exists; before the first build it verifies the audit. `release` combines the build and validated packaging commands. `package --destination /path/to/thesis_data` changes the destination; `verify-package --destination /path/to/thesis_data` checks a relocated package. Existing unrelated directories are never overwritten as packages.

The source build creates 4,784,640 canonical company rows, 982,129 numeric-observed rows, 1,869 master instruments and 4,789,760 original-row lineage records, alongside the existing 2,559-row J203 benchmark. Dataset manifests are written last, after validation; failed staged builds do not publish partial company generations. Package data/documentation checksums are deterministic for fixed sources/code/configuration; intentionally variable processing and packaging timestamps are recorded separately.

The tool builds a separate working package at **`dist/thesis_data/`**. The thesis uses the reviewed v1.2.0 package at `../../data/part_a/source/thesis_data/`; see the [local data setup](../../docs/reproducibility.md#local-data-setup). The full test suite uses the reviewed package and the retained local extraction artifacts. The browser profiles and earlier handover are in the [local archive](../../archive/README.md). It includes five Parquet datasets, benchmark metadata, exhaustive documentation, source fingerprints, a session calendar, coverage evidence, executable reading examples, a manifest/checksum and a standalone verifier. It excludes raw workbooks, extraction/browser/authentication material and temporary intermediates. The recipient can load Parquet directly and run `python documentation/verify_package.py` without the extraction project. In the private preprocessing repository, [data/processed/build_manifest.json](data/processed/build_manifest.json) records the exact build inventory and full validation results.

If a managed environment makes the usual uv cache read-only, prefix commands with `UV_CACHE_DIR=/tmp/iress-uv-cache`. Installation requires access to PyPI; after synchronization, `uv run --offline ...` works without network access. The existing exporter still runs with `uv run python iress_batch_export.py ...`.

The audit creates [reports/data_audit.md](reports/data_audit.md), the eight requested report artifacts, extra identity/calendar diagnostics, a standalone SVG coverage chart, and [reports/processing_specification.md](reports/processing_specification.md). The latter contains proposed company Parquet schemas, the implemented benchmark schema and effective-dated metadata tables. Read [reports/market_index_validation.md](reports/market_index_validation.md) for the benchmark handover. A monthly benchmark is rejected for daily use. For valid daily levels, the audit also writes `data/processed/market_index.parquet` and its hash-bound metadata JSON. Missing sessions stay absent: the row following a gap has `is_adjacent_to_previous_session=false`. The date-by-date alignment and event-specific benchmark checks are exported separately. An unrelated full-period gap does not erase otherwise complete market-paired event coverage.

```text
src/iress_data/
  config.py       Explicit dates, thresholds and paths
  ingest.py       Read-only streaming XLSX → standardised per-source Parquet
  validation.py   Numerical validity, calendar frequency and return adjacency
  benchmark.py    Daily index source dataset, gap flags and market-window coverage
  schemas.py      Versioned field definitions, types and nullability
  transform.py    Trailing-only company diagnostics and exact integer conversion
  build.py        Canonical prices, observed subset, instrument master and lineage
  processed_validation.py  Source/value/null/uniqueness/lineage/flag verification
  handover.py     Validated portable package and checksummed manifest
  handover_docs.py  Researcher README, dictionary and limitations
  audit.py        Integrity, instrument diagnostics and exploratory event coverage
  reporting.py    Researcher report, chart and proposed schema/handover
  verify.py       Source/artifact hashes, schemas, counts and uniqueness
  __main__.py     audit / build / verify / package / verify-package / release CLI
tests/            Synthetic financial-data failure cases and end-to-end checks
```

`data/intermediate/<workbook>.parquet` retains all source rows, placeholders and duplicates. Each sibling JSON binds the input and output SHA-256 hashes, parser version, row count, headers and observed cell types. Both six-column Flat Data Table and eight-column OHLC benchmark exports are accepted, with daily frequency checked separately. The original workbook retains any source columns outside the standardised core (benchmark Open/High/Low when supplied). Invalid numeric tokens are retained explicitly; invalid dates or identifiers reject the workbook rather than silently discarding observations. No authentication files are used by this pipeline.

The reader buffers 20,000 rows; DuckDB is limited to 512 MB with disk spilling; Python diagnostics handle one instrument at a time. Reports and per-instrument/event summaries are modest in size, while `suspicious_prices.csv` deliberately retains every flagged observation and may be larger. No pandas frame containing the entire collection is created. Free disk space is needed for intermediates, report staging and SQL spill files.

Paths and resources can be changed:

```bash
uv run python -m iress_data audit --root /path/to/project --memory-limit 512MB
uv run python -m iress_data audit --exports /path/to/exports --intermediate /tmp/iress-intermediate --reports /tmp/iress-reports
uv run python -m iress_data audit --force
```

Use the same path options for `verify`. Audit runs only reuse intermediates after both source and artifact hashes match. `--force` re-reads Excel. Reports are deterministically overwritten; `audit_summary.json` is installed last and is the completion marker. A failure partway through report generation removes that marker; rerun the audit before relying on the output collection. Source files, code and `uv.lock` are fingerprinted for reproducibility. `verify` checks integrity; it does not certify scientific eligibility or turn an invalid benchmark into a usable one.

Missing or malformed inputs are recorded and an incomplete audit exits with status 2. If no company files are usable, the audit fails explicitly. An unexpected workbook schema or multiple sheets is rejected. If duplicate keys conflict, raw copies and the conflict report retain all values; those keys are omitted from numerical audit diagnostics. Identical duplicate keys count once in diagnostics by filename/sheet/row order. Neither convention changes the intermediate observations.

Returns are diagnostic raw price changes between adjacent sessions on the stated calendar, with two finite positive closes. Missing/invalid prices and absent sessions break returns. Repeated closes are observed equalities, and volume-dependent return counts are shown separately. Historical full-period summaries and constant-run lengths are descriptive; future processing must use trailing-only flags and explicit as-of metadata. First/last observed price dates are never labelled listing/delisting dates.

The approved `build` keeps every unique company-date and blank placeholder, reduces only identical duplicate copies and records all original rows in lineage. It preserves values regardless of flags and creates the observed subset using the explicit non-null financial-field predicate. Price units and corporate-action adjustments remain unverified. Trailing-only stale flags intentionally differ from Phase 1's descriptive full-run flags; the handover processing summary records both counts. Security/issuer resolution, return methodology, and future event-specific liquidity/completeness criteria remain research decisions. No synthetic prices or unverified listing dates are introduced.

The repository has no Git history at setup. `.gitignore` excludes exports, intermediate data, reports and common browser/authentication state patterns to reduce accidental publication of licensed data or secrets. Do not distribute source data or research outputs outside their permitted licence. No credentials or browser state are required for audit/verify.
