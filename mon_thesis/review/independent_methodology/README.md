# Independent methodology diagnostics

These are historical audit scripts for the pre-remediation implementation. Use the archived project/input snapshot to reproduce that review; do not interpret a mismatch against corrected current tables as a new failure. Current supported checks are in [../remediation/README.md](../remediation/README.md).

These scripts audit the submitted Part A implementation. They do not change
`R/`, configuration, source data, the event register, derived datasets or the
existing headline tables. Results are written only to
`outputs/diagnostics/independent_review/`.

Run from the repository root in the existing R/Python environment:

```sh
iress-export/.venv/bin/python mon_thesis/review/independent_methodology/verify_data.py
Rscript mon_thesis/review/independent_methodology/audit_inference.R
Rscript mon_thesis/review/independent_methodology/stress_bootstrap.R
Rscript mon_thesis/review/independent_methodology/corporate_action_diagnostics.R
iress-export/.venv/bin/python mon_thesis/review/independent_methodology/audit_design.py
```

- `verify_data.py`: independent NumPy OLS, returns and CAR calculations using
  source observations; all-event sample screens, figure endpoints and leave-one-out estimates.
- `audit_inference.R`: numerical bootstrap reproduction, asymmetric tail/interval
  checks, explicit multivariate refits with different fitting masks, donor-panel
  contamination checks, date and classification sensitivities.
- `stress_bootstrap.R`: 500 null trials under each of six DGPs, 999 bootstrap
  draws per trial. The scalar-portfolio experiment evaluates temporal calibration;
  it does not certify the real-data selection, exposure or causal design.
- `corporate_action_diagnostics.R`: in-memory illustration of the documented
  Reinet ten-to-one conversion and MTNZF capital distribution. The latter assumes
  Close is in cents; it is not an approved production adjustment.
- `audit_design.py`: placebo calendars/overlap, null-process diagnostics, an
  independent Holm implementation and interval/p-value decision comparisons.

The reviewer also copied the analysis code, config, documentation, register,
tests and dependency specifications into the temporary workspace recorded in
`outputs/diagnostics/independent_review/audit_workspace.txt`. Only the immutable
source package was symlinked there. Full `--all` and tests ran in that copy with
`PART_A_PYTHON` set to the absolute existing virtual-environment interpreter.
Their logs and the nine-table byte comparisons are retained in the diagnostic
directory. Original project files were fingerprinted before and after review.

The synthetic and targeted outputs are review evidence, not replacement
headline results. Specification changes and selective data adjustments require
a complete, documented research decision and a new production run.
