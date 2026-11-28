# Repository restructuring and verification

The combined report is now the first entry point. The submitted files in
[report/](../../report/) match the original delivery byte for byte. The
[baseline manifest](baseline_manifest.json) records the intake commit,
environment, commands, source and output hashes, and headline estimates. The
[analytical comparison](analytical_comparison.json) records before and after
hashes, including which regenerated PDFs had equivalent page images. The
[integrity verification](integrity_verification.json) records source, archive,
report and test results.

## Inventory and layout

The original workspace combined analysis, report, licensed source data and
historical development artifacts under `mon_thesis/`. Part B was already
partway through a user-initiated move and used three compatibility symlinks.
The IRESS tool had another symlink from its build destination to the immutable
thesis data. Intake was on branch `main` at
`db551d6a1bdfba33b7811b16054796a4bc521d3a`, with existing README, ignore rules,
Part B moves and IRESS metadata deletions. The index was clean. No submodule or
nested Git repository was found. The starting status, ignored paths, complete
filesystem inventory, tracked paths and prior documentation edits were captured
under `archive/local/maintenance/`.

| Material | Former path | Current path and treatment |
| --- | --- | --- |
| Submitted report, editable source and report support | `mon_thesis/report/` | `report/`, with a second exact local delivery backup |
| Event study, configuration, ledgers, tests and locked environment | `mon_thesis/` | `analysis/part_a/` |
| Immutable validated package and generated return panel | `mon_thesis/data/` | `data/part_a/source/thesis_data/` and `data/part_a/derived/` |
| Equity analysis and collection | `part_b/scripts/` through a symlink | `analysis/part_b/`, with collection under `scripts/` and current checks under `tests/` |
| Publications, reviewed extracts and dictionaries | `part_b/data/` and `part_b/docs/` | Real directories at `data/part_b/` and `docs/part_b/` |
| Current result tables, figures and diagnostics | `mon_thesis/outputs/` | `outputs/part_a/` and `outputs/part_b/` |
| Event-study methodology | `mon_thesis/docs/` | `docs/part_a/`. Generated research progress is under Part A reports. |
| IRESS extraction, original workbooks and JSE Bulletins | `iress-export/` | `tools/iress-export/`, retaining its internal tool layout |
| Prior baseline, review and audit evidence | Mixed with active code and results | `archive/part_a/` and `archive/local/` |

The migration kept code, configurations and tests active, preserved current
research inputs and outputs, kept methodological documentation accessible,
archived superseded evidence, and removed verified cache files. The
[archive manifest](../../archive/archive_manifest.csv) identifies the archived
files and the places where rights or size limit their distribution. The
pre-remediation baseline was kept as an expanded directory because Part A
still reads its comparison tables. Its original manifest and separate local
Parquet copies were retained. IRESS workbooks and JSE Bulletins were kept as
original files. Historical browser state, failed extraction evidence and
earlier IRESS outputs of uncertain archival value were kept locally. Only
untracked Python bytecode, pytest cache files, an empty DuckDB temporary
directory and four obsolete repository symlinks were removed. Virtual
environment internals are outside the project source layout.

## Before and after

See the [inventory totals](inventory_totals.json) for counts and payload
sizes. The primary-tree measure excludes the virtual environment, browser
profiles and the new archive. The full workspace measure includes all three.
Moving evidence out of the daily workflow reduced the primary tree. Retained
archives, render backups and maintenance evidence account for the full
workspace size. Git object history and the index were untouched. The
candidate snapshot is a projection of tracked paths still present on disk
plus versionable new paths under the current ignore rules.

The relocated IRESS thesis package and Part A firm-level Parquet outputs are
ignored. The old IRESS package is still present in existing Git history. Original
tool workbooks and JSE Bulletins were already local-only, as were the acquired
B-BBEE Commission PDFs. The ignore rules preserve those distinctions. Public
source publications, curated extracts and current research results remain in
the proposed tracked tree. The [reproduction guide](../reproducibility.md)
documents the local setup and redistribution constraints.

No files were staged or committed because the intake included user changes.
The new layout and preserved user work remain in the working tree. No history
rewrite or remote push was performed.

## Verification

The full R analyses were run in fresh `Rscript --vanilla` processes using
absolute entry-point paths from outside the repository. The commands below
show the equivalent repository-root invocations.

| Command | Baseline and post-migration result |
| --- | --- |
| `Rscript --vanilla analysis/part_a/run_analysis.R --all` | All five events, robustness fits and placebos completed. The 17 statistical CSVs and seven derived Parquet files matched intake bytes. |
| `Rscript --vanilla analysis/part_a/tests/testthat.R` | 31 cases and 395 expectations passed, including real-data integration. |
| `Rscript --vanilla analysis/part_b/run_analysis.R` | 89 checks passed and all 23 analytical CSVs were byte-identical. |
| `python3 analysis/part_b/tests/verify_methodology.py` | The independent comparison reconciled all 2,876 keyed rows across 23 R tables. |
| Part B offline collection scripts and independent source checks in the [reproduction guide](../reproducibility.md#optional-part-b-extraction-and-source-checks) | CEE, B-BBEE Commission and supporting reproduction succeeded in a disposable copy. Reviewed data files regenerated byte-for-byte. Independent source-check output matched across layouts. |
| `sha256sum -c manifest.sha256` and `python documentation/verify_package.py` from the Part A source package | The standalone verifier passed 26 payload files and eight readable Parquet datasets. An independent SHA-256 inventory also matched every file in the original 28-file package, all 29 Part B publications and the original IRESS workbooks and bulletins. |
| `(cd tools/iress-export && .venv/bin/python -m pytest -q -p no:cacheprovider)` | All 51 tests passed, including package verification and rollback tests. |
| `sh report/render.sh OUTPUT_DIRECTORY` | Both formats rendered. HTML matched the submitted bytes. The PDF matched extracted layout text and 120 dpi page images on all 17 pages. The HTML contains nine tables, four embedded PNGs and 34 bibliography entries, and all internal anchors resolve. |
| `(cd report && sha256sum -c submitted.sha256)` | Both submitted files and their second local copies match the recorded delivery hashes. |

The five headline estimates round to −3.49 pp, −2.22 pp, −0.20%, −0.12% and
+1.58% in the registered announcement order. The January 2026 raw and Holm
p-values round to 0.0134 and 0.0670. The full-precision table matched. Part B’s
reported top- and senior-management changes of 7.9 pp and 9.7 pp, and its
national economic-interest figures of 15.71% and 39.79%, also match the
submitted report. All 26 analytical figures reproduced. Twelve regenerated PDF
figures differed in file bytes, with identical page images. The original
reviewed figure versions are retained in the primary results.

The first baseline CEE command hit a missing system-Python dependency and
passed with the existing IRESS environment. The first baseline R Markdown
attempt passed a separate Pandoc output directory. XeLaTeX could not resolve
relative figures and left a partial PDF in the working report folder. The
untouched delivery copy was captured before this attempt and matched the
original Git PDF. It was restored as the primary PDF. The failed log and
partial output were archived separately. The new render wrapper builds inside an
isolated layout and checks the destination before copying results. An initial
post-migration run exposed one old generated-document path and one obsolete
IRESS test fixture path. The next run also exposed an output path in the Part A test harness. All three
paths were corrected. The affected workflows were rerun to successful completion.

The historical IRESS processed build manifest fingerprints earlier versions
of four modules and is retained as evidence. The corresponding production
Python modules match the intake Git source byte for byte. The existing output tree still reports its earlier fingerprint. From a
disposable copy of the tool with the local input workbooks mounted, we ran
`python -m iress_data build`, `verify`, `package` and `verify-package`.
All passed, including deep verification of 4,784,640 canonical observations
and 4,789,760 source rows. The disposable build was separate from the submitted
package.

The independent Part A NumPy verifier reconciled 844 model fits and 4,179
CAR rows, and component validation and the final preservation check passed.
The CLI checks passed for single-event, narrow and smoke modes. A separate
all-event run reproduced the 24 table and Parquet files, and the archived
original implementation reran its nine table comparisons and tests. A
candidate snapshot that omitted all ignored licensed inputs successfully
reproduced Part B and rendered the report offline. Local command logs and
the final verification render are in `archive/local/maintenance/`.

Environment restoration from an empty package library and live authenticated
IRESS extraction were outside the verified runs. The original capture and
archived history remain available locally to authorised users. The raw
material under `archive/local/` requires separate preservation when copying
the project.
