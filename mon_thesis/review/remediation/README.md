# Remediation validation and reproducibility

The full 24 November 2026 handover passed 31 test cases / 395 expectations,
independent reconstruction of 980,380 raw returns, 844 OLS fits and 4,179 CARs,
and all three CLI checks. A separate full run reproduced all 17 statistical CSVs
and seven derived Parquet files byte-for-byte. All 28 source-package files, the
event register and 157 archived baseline files remained unchanged. Six
synchronous calibration scenarios used 400 trials each; their rejection and
coverage results include Monte Carlo intervals. These are execution facts, not
evidence that remaining economic/inferential assumptions are resolved.
`outputs/diagnostics/remediation/validation_summary.json` records the matched
validation fingerprints and links these counts to the underlying evidence.

The scripts here validate the current corrected implementation. The older
`../independent_methodology/` scripts describe the historical review and should
run against its archived code/data snapshot, not current corrected tables.

From the repository root:

```sh
Rscript mon_thesis/run_analysis.R --all
Rscript mon_thesis/tests/testthat.R
iress-export/.venv/bin/python mon_thesis/review/remediation/verify_corrected.py
Rscript mon_thesis/review/remediation/validate_components.R
Rscript mon_thesis/review/remediation/calibrate_inference.R
iress-export/.venv/bin/python mon_thesis/review/remediation/check_cli.py
iress-export/.venv/bin/python mon_thesis/review/remediation/reproduce_corrected.py
Rscript mon_thesis/review/remediation/finalize_handover.R
```

Use the configured/`PART_A_PYTHON` interpreter for Python checks if the extraction
virtual environment is unavailable. It must provide PyArrow, Pandas and NumPy;
the existing requirements already provide these dependencies. R uses the
existing locked packages; no new R dependency was introduced.

- `verify_corrected.py` independently reconstructs source-adjacent raw returns,
  applies only approved ledger conversions, fits every model with NumPy and
  reconciles screening, CAR, CAAR, figures and Holm-related source estimates.
  It writes only `outputs/diagnostics/remediation/`.
- `validate_components.R` isolates the interval change and the full extreme
  donor mask on the original archived prices. It reproduces all 55 original
  p-values and the independent review's five mask diagnostics, then checks
  current p/interval consistency and placebo fitting-window restrictions.
- `calibrate_inference.R` runs synchronous 12-security zero-effect DGPs with
  common/sector shocks, different fitting masks, serial dependence, tails and
  changing event variance/correlation. The configured full run is 400 trials per
  scenario, 999 draws per trial. `--quick` is a labelled smoke calibration and
  overwrites only calibration artifacts; rerun full calibration for handover.
  BMP/KP-style standardized aggregate results remain exploratory and target a
  different estimand from the raw headline portfolios.
- `finalize_handover.R` verifies source/event-register preservation, the archived
  original files and current analysis/config/ledger hashes. It requires matched
  post-run tests and all five events before refreshing the handover report.
- `check_cli.py` exercises single-event overrides, a narrow custom configuration
  and smoke execution in an isolated project. Each retains the five-test family.
- `reproduce_corrected.py` runs all five corrected events in a separate temporary
  project and compares every statistical table and derived Parquet file
  byte-for-byte with the main run. It records both hashes for each file.

## Original baseline

`outputs/baselines/pre_remediation_2026-11-24/` contains original project code,
configuration, tests, research documents, tables, diagnostics, figures, the
independent review and source/archive fingerprints. All nine original tables
and 331 test expectations reproduced before corrections. The local 21 MB
`derived/` copy is ignored by Git.

To reproduce the original from the immutable source, without overwriting current
results, or restore missing local archived Parquet files after a checkout:

```sh
iress-export/.venv/bin/python mon_thesis/review/remediation/reproduce_baseline.py --restore-derived
```

The reproducer runs the archived code in a new temporary copy, compares the nine
tables byte-for-byte and restores **only missing** Parquet copies with matching
archived hashes. It refuses to overwrite an existing baseline file or use a
different source package. Exact physical Parquet restoration may require the
recorded package versions. The original statistical tables/code stay available
even if local ignored Parquet copies have been removed.

Normal `--all`, `--event`, `--smoke` and `--config` interfaces remain supported.
They overwrite latest-run aggregate outputs and the generated progress/handover;
use an isolated project copy to compare CLI paths. A narrow custom event list
does not change the registered five-hypothesis Holm family. First run `--all`
again before calling the final handover verifier on the main working project.

Raw data and `research/events.csv` are never rewritten. No diagnostic uses an
invented corporate-action factor, fills the benchmark gap, imports an unrelated
large return panel, publishes data or contacts another person.
