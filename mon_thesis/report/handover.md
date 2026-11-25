# Combined empirical report handover

**Stellenbosch University · 24 November 2026**  
Prepared for independent report review and discussion.

Read the [17-page PDF](combined.pdf) or the [self-contained HTML report](combined.html). The [editable R Markdown](combined.Rmd), [bibliography](references.bib), [citation style](report.csl), [PDF settings](report.tex) and [HTML stylesheet](report.css) are in the same directory.

## Reading guide and findings

| PDF pages | Contents |
| --- | --- |
| 1–2 | Executive summary, research objectives, economic interpretation of the measures and event-study design |
| 3–4 | Five announcements, conditional pointwise inference, Holm adjustment, the 2018 information sequence and January 2026 daily decomposition |
| 5–10 | National management representation, observed levels and changes in all 18 sectors, economic interest and voting rights, valid contributor status distributions, the draft target shortfalls, final targets and the separate 2025 reporting population |
| 11–12 | Combined economic discussion, QLFS employment context, limitations and conclusion |
| 13–15 | Appendices on market-model inference and sensitivity, signed draft shortfalls by sex, and the supplementary 2025 demographic proxy |
| 16–17 | Thirty-four references covering the gazettes, data publications, market context and statistical methods |

The 2017 and 2018 mining-minus-control differences were −3.49 and −2.22 percentage points. The aggregate two-session estimates for the 2023 draft and 2025 final EE targets were −0.20% and −0.12%. The January 2026 draft Codes estimate was +1.58% relative to the model, alongside a fall in the portfolio’s observed prices. Its raw p-value was 0.0134 and its Holm p-value was 0.0670. None of the five primary tests reached the 5% family-wise threshold.

Between 2016 and 2024, Black representation rose by 7.9 pp in top and 9.7 pp in senior management. Black women’s shares rose by 5.1 and 6.0 pp respectively. Reported national Black economic interest rose from 15.71% to 39.79% in the 2016–2023 verification samples. All 18 sectors had positive total shortfalls against the May 2023 draft at both management levels. These observations describe the reporting populations and the information in the notices. Quantifying a causal tradeoff would require realised efficiency outcomes, policy exposure and a credible counterfactual.

## Rebuild

From the repository root, run

```sh
Rscript --vanilla -e 'rmarkdown::render("mon_thesis/report/combined.Rmd", output_format = "all")'
```

This writes `combined.pdf` and `combined.html` beside the source. The render reads aggregate CSVs and figure exports under `mon_thesis/outputs/`, the event register and the five-hypothesis registry. Both analysis pipelines and the collection scripts are independent of this command. Rendering works offline and requires no licensed raw observations or copies of restricted publications.

The verified environment used R 4.3.3, data.table 1.18.2.1, knitr 1.51, rmarkdown 2.31, bookdown 0.37, Pandoc 3.1.3 and XeLaTeX from TeX Live 2023, with the TeX Gyre Pagella and Heros fonts. The existing packages were sufficient. The Part A lockfile records the analysis environment. The report also requires the rendering software listed here.

## Sources and editorial choices

| Display | Authoritative material and treatment |
| --- | --- |
| Table 1, Figure 1 and Appendix A | Corrected percentage export, daily portfolio decomposition, fixed-sample timing and robustness results. The two spreads use mining/control counts and pp. The three aggregate CAARs use total security counts and percent. Only the five primary tests receive the Holm adjustment. [Final Part A review](../outputs/reports/final_methodology_review.md) · [Corrections](../outputs/reports/methodological_corrections_report.md) |
| Figures 2–4 and Tables 2–6 | Latest approved vector figures in PDF and corresponding PNGs in HTML. Table 3 shows each sector’s 2024 share beside its unrounded-endpoint change from 2019. Figure 3 retains open flagged observations and breaks its lines at those years. The status distribution uses its reconciled denominator. [Final Part B review](../outputs/part_b/reports/part_b_independent_methodology_review.md) · [Analysis handover](../../docs/part_b/analysis_handover.md) |
| Targets and proxy | Figure 4 and Appendix B use the 2022 workforce profiles printed with the May 2023 BLACK proposal. Table 6 presents the April 2025 designated-group targets separately. Appendix C identifies when the 2023 and 2024 workforce profiles became available relative to the announcement. Its proxy cannot establish statutory attainment. [Supporting data review](../../docs/part_b/supporting_independent_review.md) |
| Equity and employment sources | The national CEE series ends in 2024. Workforce year 2025 is treated separately. The 2026 ownership retrospective was linked in May and officially launched in July. It provides historical context after the January announcement. QLFS national totals retain their paired publication vintages. Sector comparisons remain within the reviewed classifications. [CEE review](../../docs/part_b/cee_independent_review.md) · [Ownership review](../../docs/part_b/bbbee_independent_review.md) · [Source inventories](../../docs/part_b/) |

## Validation and reviewer decisions

- Both outputs rendered from the R Markdown. An isolated build containing only the report sources, aggregate inputs and two registries produced byte-identical HTML and identical text and page images on all 17 PDF pages.
- All 100 displayed table rows matched the reviewed source tables at their stated precision in both formats. The five headline estimates, ten interval bounds and ten raw/adjusted p-values also reconciled to the final Part A review. The report uses source changes calculated before rounding.
- All PDF pages were inspected. The four figures remained vector graphics, the nine tables fitted the page, and figure, table and bibliography numbering resolved. The HTML opened in Chrome, all internal links resolved and all four embedded PNGs matched the reviewed exports byte-for-byte.
- All 33 public bibliography links returned successful responses in the final review. The Reinet citation uses FTSE Russell’s copy of the index notice. The report needs no external assets to display.
- Before-and-after SHA-256 inventories matched for all 466 files under `mon_thesis/outputs`, `mon_thesis/data` and `data`, including the reviewed outputs and original collections. This assignment created files only in `mon_thesis/report` within the repository. Nothing was committed or pushed.

The remaining review is substantive. The supervisor should assess whether the price-return convention, equal-security weighting, historical mining proxy and conditional inference answer the intended market question. For the equity discussion, the material boundaries are changing employer populations, unknown ownership weights and statutory eligibility. These limit claims about firms and policy effects even where the reported aggregate changes are clear.

The [final independent academic and methodological review](final_independent_review.md) records the subsequent verification, corrections and submission decision.
