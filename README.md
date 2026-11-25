# Empirical analysis of B-BBEE

The implemented R event-study project is in [mon_thesis/](mon_thesis/README.md). It supports Part A of Monique van Eeden's Stellenbosch University Economics thesis and preserves the existing licensed IRESS handover unchanged.

Run the full analysis from this repository root:

```sh
Rscript mon_thesis/run_analysis.R --all
Rscript mon_thesis/tests/testthat.R
```

Read the [preliminary results](mon_thesis/outputs/reports/part_a_preliminary_results.md), [methodology](mon_thesis/docs/event_study_methodology.md), and [research handover](mon_thesis/docs/research_progress.md). Findings require methodological review; raw prices are not verified total returns and policy effects are not causally identified.

`iress-export/` contains the existing collection/engineering project. The analysis does not restart IRESS extraction or upload licensed data.


The [methodological correction handover](mon_thesis/outputs/reports/methodological_corrections_report.md)
records revised results, source-backed return corrections, inference conventions,
validation and unresolved research decisions. See the
[decision register](mon_thesis/docs/research_decisions.md) before thesis use.

## Part B descriptive analysis

```sh
Rscript --vanilla scripts/part_b/run_analysis.R
```

The R entry point reads the reviewed Part B collection and generates management, ownership, status, Employment Equity and QLFS tables under `mon_thesis/outputs/part_b/`. It also writes three primary figures and runs the analytical checks. [Preliminary results](mon_thesis/outputs/part_b/reports/part_b_preliminary_results.md) · [Analysis handover](docs/part_b/analysis_handover.md)
