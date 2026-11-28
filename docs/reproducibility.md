# Reproducing the research

Run commands from the repository root unless a command explicitly changes
directories. Both R analysis entry points locate the project through their
script path and were also verified from a different working directory.

## Environment

The verified environment used R 4.3.3 and Python 3.12.3 on Linux. Part A’s
[renv lockfile](../analysis/part_a/renv.lock) records analysis and testing
packages. Restore it from the Part A directory using an R installation with
`renv` available.

```sh
(cd analysis/part_a && Rscript --vanilla -e 'renv::restore(prompt = FALSE)')
```

Use the restored R library for analysis by setting `R_LIBS_USER` to the project
library when using `--vanilla`, or activate the restored library explicitly in
your R session. The verification used the existing installed libraries. A clean
network restore of the lockfile was outside the verified execution.

Configure the Parquet bridge using the interpreter’s absolute path. Keep the
virtual environment’s executable path intact.

```sh
python3 -m venv .venv-io
.venv-io/bin/python -m pip install -r analysis/part_a/requirements-io.txt
export PART_A_PYTHON="$PWD/.venv-io/bin/python"
```

The relocated IRESS tool’s Python environment was used for verification and is
the default in the Part A config. To recreate that environment from the lockfile,
run `(cd tools/iress-export && uv sync --locked)`. The full IRESS tests also need
the data and audit artifacts described in the [tool README](../tools/iress-export/README.md).
For a new copy of the project, recover the retained
`tools/iress-export/data/processed/` and `tools/iress-export/reports/` artifacts
from the authorised handover to run the local historical-industry tests.

Part B uses R `data.table`, `ggplot2` and Cairo graphics support. The independent
table check uses Python’s standard library. Offline collection needs Poppler
and the packages in `analysis/part_b/scripts/requirements.txt`. Independent
source checks also use PyMuPDF. For report rendering, install R packages
`data.table`, `knitr`, `rmarkdown`, `bookdown`, Pandoc with citeproc, XeLaTeX with
the supporting LaTeX packages, and TeX Gyre Pagella and Heros fonts.
The verified versions are recorded in the
[baseline manifest](maintenance/baseline_manifest.json).

## Local data setup

| Path | Setup |
| --- | --- |
| `data/part_a/source/thesis_data/` | Copy the intact authorised IRESS thesis-data package v1.2.0 here, including `manifest.json`, `manifest.sha256` and `documentation/`. |
| `data/part_b/processed/` | Use the reviewed CSVs for routine Part B reproduction. `intermediate/` also contains the manually reviewed CEE transcription used during extraction. |
| `data/part_b/raw/` | CEE, Stats SA and gazette PDFs already in Git belong here. Restore B-BBEE Commission PDFs in `raw/bbbee_commission/` from an authorised copy. See the [Commission source inventory](part_b/bbbee_source_inventory.csv). |
| `tools/iress-export/exports/` and `tools/iress-export/data/raw/jse_bulletins/` | Restore original IRESS exports and JSE Bulletins locally for extraction work. The analysis uses the validated package above. |

The package, raw market workbooks, Commission PDFs, intermediate IRESS datasets
and local archive are excluded from the proposed Git tree. The IRESS package was
already tracked at the previous path and remains in the existing Git history.
Review institutional and publisher permissions before sharing any clone or data
bundle. Current checked-in aggregates and review files also warrant a rights
review before public redistribution.

Verify the exact package with both checks.

```sh
PART_A_PYTHON="${PART_A_PYTHON:-$PWD/tools/iress-export/.venv/bin/python}"
export PART_A_PYTHON
(cd data/part_a/source/thesis_data &&
  sha256sum -c manifest.sha256 &&
  "$PART_A_PYTHON" documentation/verify_package.py)
```

## Analysis and tests

```sh
Rscript --vanilla analysis/part_a/run_analysis.R --all
Rscript --vanilla analysis/part_a/tests/testthat.R
Rscript --vanilla analysis/part_b/run_analysis.R
python3 analysis/part_b/tests/verify_methodology.py
(cd tools/iress-export && .venv/bin/python -m pytest -q)
```

Part A writes tables and figures under `outputs/part_a/` and local Parquet
under `data/part_a/derived/`. Tests read those derived outputs and refresh
test diagnostics. Single-event and smoke runs replace latest-run aggregate
tables. Use a disposable project copy for those modes if the full results are
needed for rendering. The [Part A audit guide](../analysis/part_a/review/remediation/README.md)
lists the independent verifiers.

Part B writes its tables, figures, report and 89 automated checks under
`outputs/part_b/`. Its independent verifier recalculates the results against
the reviewed inputs and writes diagnostics in the same output tree.

## Optional Part B extraction and source checks

Run extraction in a disposable copy containing `analysis/`, `data/` and
`docs/` when comparing with the reviewed inputs. These commands regenerate
intermediate datasets and documentation logs. Run source checks from the
repository root with an environment containing pandas, PyArrow and PyMuPDF.

```sh
sh analysis/part_b/scripts/reproduce_cee.sh
sh analysis/part_b/scripts/bbbee/reproduce_bbbee.sh
sh analysis/part_b/scripts/supporting/reproduce_supporting.sh
for check in independent_early_source_check independent_pdf_semantic_check \
    independent_remaining_source_check independent_check_cee final_collection_check
do
    python3 "analysis/part_b/tests/$check.py"
done
for check in independent_verify_mupdf independent_structure_check independent_figures_check
do
    python3 "analysis/part_b/scripts/bbbee/$check.py"
done
```

## Combined report

```sh
sh report/render.sh "$(mktemp -d)"
(cd report && sha256sum -c submitted.sha256)
```

The render command uses the reviewed outputs and design registries. It builds
both formats in isolation and copies them into the selected destination. Use
[the submitted PDF](../report/combined.pdf) or [HTML](../report/combined.html)
for the exact delivered files. The
[maintenance comparison](maintenance/restructuring_report.md) describes
verification of the figures, tables, references and text.
