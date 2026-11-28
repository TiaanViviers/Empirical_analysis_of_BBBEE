# Empirical analysis of South African B-BBEE policies

This repository supports Monique van Eeden’s Stellenbosch University economics
master’s thesis on the efficiency–equity tradeoff associated with South African
transformation policies.

**Read the submitted report** · [PDF](report/combined.pdf) ·
[HTML](report/combined.html) · [R Markdown](report/combined.Rmd) ·
[Independent report review](report/final_independent_review.md)

- **Part A** uses IRESS/JSE prices, historical classifications and source-backed
  corporate-action adjustments to estimate abnormal returns around five
  transformation-policy announcements. It uses market models and synchronous
  block-bootstrap inference, with robustness and placebo analyses.
- **Part B** describes management representation, ownership and reporting
  coverage using Commission for Employment Equity and B-BBEE Commission
  publications. It compares statutory sector targets with the relevant workforce
  profiles and uses Statistics South Africa’s QLFS for employment context.

## Repository map

| Path | Contents |
| --- | --- |
| [report/](report/) | Submitted artifacts, editable source, render command and report review |
| [analysis/part_a/](analysis/part_a/) | Event-study modules, configuration, ledgers and tests |
| [analysis/part_b/](analysis/part_b/) | Descriptive analyses, source collection and independent checks |
| [data/](data/) | Original research inputs and reviewed Part B extracts |
| [outputs/](outputs/) | Current tables, figures, diagnostics and methodology reviews |
| [docs/](docs/) | Reproduction guide, methods, source inventories and data dictionaries |
| [tools/iress-export/](tools/iress-export/) | IRESS extraction and packaging tool, with its Python lockfile and tests |
| [archive/](archive/) | Pre-remediation snapshot and earlier audit evidence |

## Reproduce the research

Install R and Python dependencies and obtain authorised local inputs as described
in the [reproduction guide](docs/reproducibility.md). The offline report build
needs only the preserved aggregate outputs, registries and rendering tools.
Part A requires the validated IRESS package. Part B analysis uses the reviewed
CSV extracts. Its collection workflows also need the original publications.

From the repository root, after setup:

```sh
Rscript --vanilla analysis/part_a/run_analysis.R --all
Rscript --vanilla analysis/part_a/tests/testthat.R
Rscript --vanilla analysis/part_b/run_analysis.R
python3 analysis/part_b/tests/verify_methodology.py
sh report/render.sh "$(mktemp -d)"
```

The final command prints the location of the rebuilt report and preserves the
submitted files. IRESS workbooks, JSE Bulletin workbooks, the validated package
and locally acquired B-BBEE Commission PDFs require appropriate permissions.
The earlier IRESS package is still in existing Git history.

## Methods and provenance

- Part A [event-study methods](docs/part_a/event_study_methodology.md),
  [inference](docs/part_a/statistical_inference.md), and
  [final methodology review](outputs/part_a/reports/final_methodology_review.md).
- Part B [analysis handover](docs/part_b/analysis_handover.md),
  [CEE dictionary](docs/part_b/cee_data_dictionary.md),
  [B-BBEE dictionary](docs/part_b/bbbee_data_dictionary.md),
  [supporting-data dictionary](docs/part_b/supporting_data_dictionary.md), and
  [final methodology review](outputs/part_b/reports/part_b_independent_methodology_review.md).
- [Historical archive](archive/README.md) and
  [restructuring verification](docs/maintenance/restructuring_report.md).

Event-window returns describe market-model-relative movements among selected
listed securities. The equity series describe the employers and entities in
each reporting population. Causal conclusions about realised efficiency or an
efficiency–equity tradeoff require a credible counterfactual and direct measures
of realised efficiency.
