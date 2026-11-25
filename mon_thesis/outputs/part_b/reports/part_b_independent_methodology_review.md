# Part B independent methodological review

24 November 2026

## Readiness and sign-off

**Part B passes the methodological quality gate for inclusion in the combined Part A/B report as qualified descriptive evidence.** I independently reproduced the principal numbers from the reviewed inputs. The strongest findings are the broad rise in reported management representation, the increase in the B-BBEE Commission’s sampled ownership averages and the substantial variation in the May 2023 draft target gaps. The evidence concerns different reporting populations, units and periods. The combined discussion can examine market reactions alongside these equity outcomes. A causal efficiency–equity tradeoff would require credible policy counterfactuals and measures of realised efficiency.

| Severity | Finding | Disposition |
| --- | --- | --- |
| Critical or major | No material calculation, selection or matching error was demonstrated in the principal estimates. | Headline values and approved analysis windows stand. |
| Moderate | Connecting the flagged ownership points made the sharp Construction and Tourism movements look like ordinary annual changes. | Figure 2 keeps the published points visible and breaks the lines in the affected years. |
| Moderate | The original 2016 CEE report publishes separate national management counts. The retrospective coverage warning alone did not show the effect of choosing that baseline. | Compared the two sets of counts. The largest effect on a headline change is 0.11 percentage points. The approved retrospective series remains primary. |
| Moderate | Changes in the CEE reporting population and the B-BBEE sample limit interpretation even where the arithmetic is exact. | Quantified the CEE sector-mix sensitivity and the B-BBEE sample shifts. Clarified the populations and publication timing in the results. |
| Minor | Sector management changes were available in CSV, while the reader-facing report showed mainly national movements and selected examples. Figure 1 also showed retrospective marker styling in the general legend. | Added the complete sector change table to the results and corrected the legend. Clarified that Figure 3 shows total BLACK gaps in both panels and uses a common ordering. |

The review used the handover and source reviews as the basis for data selection. The independent calculations use Python’s standard library and exact fractions up to display, with tables matched to the R exports after calculation. Existing source extraction was used, with targeted PDF checks for the original 2016 alternative and the 2019 water/waste alias. [Analysis handover](../../../../docs/part_b/analysis_handover.md) · [CEE source review](../../../../docs/part_b/cee_independent_review.md) · [B-BBEE source review](../../../../docs/part_b/bbbee_independent_review.md) · [Supporting source review](../../../../docs/part_b/supporting_independent_review.md) · [Independent calculation](../../../../scripts/part_b/review/verify_methodology.py)

## CEE management representation

### National changes and the 2016 baseline

| Level and group | 2016 count and share | 2024 count and share | Primary change (pp) | Change using original 2016 counts (pp) | 2017–2024 change (pp) |
| --- | ---: | ---: | ---: | ---: | ---: |
| Top management, Black | 16,962 / 60,037 = 28.25% | 21,159 / 58,554 = 36.14% | +7.88 | +7.97 | +7.31 |
| Top management, Black female | 5,172 / 60,037 = 8.61% | 8,048 / 58,554 = 13.74% | +5.13 | +5.15 | +4.58 |
| Senior management, Black | 57,342 / 143,706 = 39.90% | 76,858 / 154,982 = 49.59% | +9.69 | +9.80 | +8.88 |
| Senior management, Black female | 20,632 / 143,706 = 14.36% | 31,619 / 154,982 = 20.40% | +6.04 | +6.10 | +5.40 |

Black combines the CEE’s African, Coloured and Indian categories. The Black female share uses women in those categories and the same denominator as the overall measure. Each count is divided by all managers at the relevant level, including foreign nationals, whose counts are recorded separately. All ten demographic cells sum to each published denominator in all 272 selected national and sector profiles. Count-derived shares avoid rounding from printed component percentages. The largest aggregate difference between a 2024 count-derived share and the corresponding sum of printed components is 0.17 points in education senior management. All displayed changes use the unrounded endpoint shares. [Independent calculations](../diagnostics/independent_methodology/verification.json) · [CEE endpoint changes](../diagnostics/independent_methodology/cee_endpoint_changes.csv)

In the 19th report’s retrospective 2016 profile, the workforce grand total is 7,105,662, compared with 7,071,449 employees covered in the original 17th report. The reason for the difference of 34,213 is unresolved. The original report’s rendered all-employee rows give management totals of 59,695 and 142,863 and Black shares of 28.17% and 39.79%, with Black female shares of 8.59% and 14.30%. Both baseline choices and a 2017 start give the same direction and ordering of gains. The retrospective rows match the workforce-profile format used in the later series and remain explicitly labelled. [Original 17th CEE report, Tables 10 and 15](https://www.labour.gov.za/DocumentCenter/Reports/Annual%20Reports/Employment%20Equity/2016-2017/17th%20CEE%20Annual%20Report.pdf#page=30) · [CEE source review](../../../../docs/part_b/cee_independent_review.md#completed-focused-review-2016-2017-and-2018)

### Sector changes and historical comparability

| 2019–2024 change | Increases | Decreases | Unchanged | Largest increase (pp) |
| --- | ---: | ---: | ---: | --- |
| Top management, Black | 15 | 3 | 0 | Water and waste (+11.48) |
| Top management, Black female | 18 | 0 | 0 | Public administration and defence (+5.97) |
| Senior management, Black | 17 | 1 | 0 | Transport and storage (+17.00) |
| Senior management, Black female | 18 | 0 | 0 | Health and social work (+6.89) |

The Black share declined in administrative and support, arts and recreation, and real estate in top management, and in arts and recreation in senior management. All 18 sectors reported a higher Black share and a higher Black female share at senior than at top management in 2024. Nationally the senior-minus-top gaps increased from 11.65 to 13.46 points for Black managers and from 5.74 to 6.66 points for Black women. The Black female share rose in each year at both levels. The 2024 top-management contrast between agriculture and public administration also reconciles, at 15.3% and 81.6% Black and 5.7% and 29.5% Black female. [Annual sector gaps](../tables/cee_sector_management_level_gaps.csv) · [Detailed management changes](../diagnostics/independent_methodology/cee_endpoint_changes.csv)

The 18 detailed headings form a one-to-one mapping in every year from 2019 through 2025. The punctuation-only agriculture variant preserves the same sector. In the 20th CEE report, the 2019 Appendix C heading ends in “premeditation activities.” Both occupational rows have the same ten percentages and printed total as the body’s water, sewerage, waste and remediation rows. This supports a within-report alias. The earlier 11-sector records have no verified bridge into this series. The reviewed labels enable comparisons of published sector aggregates and give no evidence about individual employers’ sector assignments over time. [20th CEE report, PDF pp. 28, 31 and 78](https://www.labour.gov.za/DocumentCenter/PublishingImages/20th-commission-for-employment-equity-report/20th%20Commission%20for%20Employment%20Equity%20Report.pdf) · [Full label mapping](../tables/cee_sector_label_mapping.csv)

The 2019 sector sums are 31 top and 256 senior managers below the independently published national counts. Using pooled sector counts changes the 2019 shares by at most 0.021 percentage points. The 2024 sector counts sum to their national denominators. Holding each sector’s 2019 share of reported management posts fixed gives the following sensitivity. The average still rises for all four comparisons, while employer turnover and changing workforce composition within a sector remain possible. National coverage is kept as published, including the separate 300-employee difference between the 2023 sector sum and the national coverage total. [Sector weighting and coverage diagnostics](../diagnostics/independent_methodology/verification.json)

| 2019–2024 change (pp) | Published national counts | Pooled sector counts | Sector shares with fixed 2019 weights |
| --- | ---: | ---: | ---: |
| Top management, Black | +5.08 | +5.08 | +4.75 |
| Top management, Black female | +3.10 | +3.10 | +3.02 |
| Senior management, Black | +6.69 | +6.67 | +6.51 |
| Senior management, Black female | +4.02 | +4.02 | +3.97 |

The 2025 national shares reconcile to 39.8% and 15.5% in top management and 52.7% and 21.9% in senior management, for Black and Black female managers respectively. Reports fell from 29,269 to 15,090 and employee coverage from 7,699,665 to 6,896,041. The change in designated-employer rules, including removal of turnover-based designation for employers below 50 employees, warrants a separate 2025 series. The aggregate data do not identify a like-for-like employer subset. The Q3 2024 EAP figures of 92.5% Black and 42.7% Black female are sums of published demographic shares of the economically active population across occupations. Use them as context, with a different population from either management level and a different role from the gazetted benchmarks. [Separate 2025 results](../tables/cee_management_2025_separate_regime.csv) · [National EAP](../tables/cee_national_eap.csv) · [Department reporting coverage](https://admin.labour.gov.za/DocumentCenter/Publications/Newsletter-%20I-%20DEAL/2026%20Newsletter%20I-DEAL/I-DEAL%2009_2026.pdf)

## B-BBEE ownership and contributor levels

### Ownership averages and pair exclusions

| Published national average | 2016 | 2023 | Change (pp) | Codes with increase, published | Codes with increase, pairs excluded |
| --- | ---: | ---: | ---: | ---: | ---: |
| Black economic interest | 15.71% | 39.79% | +24.08 | 9 / 9 | 8 / 8 |
| Black female economic interest | 9.46% | 24.57% | +15.11 | 8 / 9 | 8 / 8 |
| Black voting rights | 19.31% | 45.77% | +26.46 | 8 / 9 | 7 / 8 |
| Black female voting rights | 2.62% | 13.55% | +10.93 | 9 / 9 | 8 / 8 |

The eligible series is the Commission’s single retrospective dataset, restricted to 2016–2023 and all entity sizes. The independent check reconstructed the percentages from the published strings and matched contextual counts to the Commission’s coverage table. Economic interest describes participation in economic benefits, and voting rights describe governance participation. Contributor levels reflect several scorecard elements. National ownership values are the Commission’s published averages from verification submissions, with unknown indicator denominators and weights. The series cannot estimate the share of South African business wealth. The separate, unauthenticated 2022 portal series uses a different reporting population and is excluded. [Commission report, methodology and ownership tables](https://www.thedtic.gov.za/wp-content/uploads/South-Africas-Transformation-Landscape-2013-2023.pdf#page=47) · [Independent endpoints by code and measure](../diagnostics/independent_methodology/bbbee_ownership_endpoints.csv)

The independent comparison generated ten female-overall inversions directly from the published values and recovered the eight affected pairs in 2016–2023. Keeping all published values as the starting point is appropriate because the valid samples and weights may differ. Removing both values in each affected pair is a conservative sensitivity, since the source gives no basis for attributing the anomaly to one measurement. Exactly 16 cells are masked. No national average or retained fixed-endpoint comparison changes. MAC has no 2016 observation to begin with. Without the two affected 2016 pairs, the 2016–2023 changes for both Generic economic-interest measures and both Financial Services voting-rights measures are missing. The separately labelled 2017–2023 changes are +1.53 and −2.45 points for Generic economic interest and −7.47 and −1.89 points for Financial Services voting rights, overall and female respectively. Those are different windows. The analysis uses no imputation. The national female economic-interest average peaks in 2020 at 26.13%. Annual code paths are more sensitive than endpoints. [Matched anomaly pairs](../tables/bbbee_ownership_anomaly_pairs.csv) · [Annual sensitivity](../tables/bbbee_ownership_annual_sensitivity.csv)

Sample composition changes substantially. Overall national entries increase from 920 to 4,143. Large enterprises rise from 110 of 920 entries (12.0%) to 1,965 of 4,143 (47.4%), while entries with unknown size fall from 338 to 29. Generic and Construction alone account for 2,860 of the 4,143 entries in 2023. Changes in applicable Codes and size thresholds compound the sample limitation. Overall counts cannot be used to reweight ownership averages by size or sector because the indicator denominators and weight rules are unavailable. [Commission report, sample Tables 1–2 and methodology](https://www.thedtic.gov.za/wp-content/uploads/South-Africas-Transformation-Landscape-2013-2023.pdf#page=47) · [Composition diagnostics](../diagnostics/independent_methodology/verification.json)

| Code in Figure 2 | 2016 sample entries | 2023 sample entries | Black economic interest change (pp) |
| --- | ---: | ---: | ---: |
| Construction | 48 | 1,383 | +18.51 |
| ICT | 231 | 259 | +22.93 |
| Tourism | 31 | 48 | +5.90 |
| Transport | 35 | 528 | +26.72 |

These are all four codes meeting the stated endpoint and 30-entry screen. An endpoint screen of 20 selects the same four. A screen of 50 keeps only ICT. The displayed set covers different reported movements, and the screen measures only contextual sample size. Generic is omitted because of the flagged start. Among the eight codes with usable endpoints under pair exclusion, the other four are Agri-BEE, Financial Services, Forestry and Property. Forestry has the largest published economic-interest increase (+27.47 points), with only 3 and 15 contextual entries. All nine codes with published endpoints rose, with changes ranging from +1.21 to +27.47 points. Use the full endpoint table when discussing breadth or rankings, and refer to these groups by B-BBEE Code. CEE sectors and QLFS industries reflect different classifications. [Screen and sample diagnostics](../diagnostics/independent_methodology/verification.json) · [All code-level results](../diagnostics/independent_methodology/bbbee_ownership_endpoints.csv)

### Contributor distributions

I rebuilt the distributions from the printed counts. National 2018 sums to 2,473 against 2,605 published, and Financial Services 2016 sums to 9 against 10. Both distributions are excluded from count-derived shares. The 85 retained distributions contain 765 rows at Levels 1–8 and Non-Compliant. There are 70 valid count dashes, retained as missing at level detail. In 17 summaries the Levels 1–4 calculation uses a zero for one or more dashes with a printed zero percentage in an otherwise reconciled distribution. Levels 5–8 remain contributor levels. National Levels 1–4 shares are 607/909 (66.8%) in 2016, 790/1,787 (44.2%) in 2017 and 2,507/4,106 (61.1%) in 2023. The 2023 Construction and Tourism values are 1,128/1,381 (81.7%) and 9/48 (18.8%). These are sampled status distributions on their own published denominators. [Valid distributions](../tables/bbbee_compliance_levels_valid.csv) · [Status summaries](../tables/bbbee_compliance_levels_1_to_4.csv) · [Exclusions](../tables/bbbee_compliance_exclusions.csv)

## Employment Equity targets

### May 2023 draft against its same-gazette 2022 profile

All 108 rows reconcile exactly at the paper’s one-decimal precision. Target and baseline match on sector, occupation, sex, source page and national BLACK category. BLACK comprises African, Coloured and Indian employees. Male and female shares use the full occupational-level denominator and add to the published total. The 2022 profile is labelled “All employers” and supplies neither underlying counts nor an explicit foreign-national breakdown. The comparison uses the printed BLACK shares and their published occupational basis, without normalisation. A positive value means the target exceeds the observed share. A negative value means the published share exceeds the proposal. The draft’s choice of national or provincial EAP and the absence of employer-level profiles rule out interpreting these distances as firm compliance gaps, percentages of firms failing, or headcount shortfalls. [Gazette 48589, notice 3407](https://www.gov.za/sites/default/files/gcis_document/202305/48589gon3407.pdf) · [Independent calculation of all target gaps](../diagnostics/independent_methodology/ee_draft_shortfalls.csv)

| Level | Group | Largest gap (pp) | Smallest signed gap (pp) | Positive / negative |
| --- | --- | --- | --- | ---: |
| Top | Total | Accommodation and food, 45.0 − 23.5 = +21.5 | Administrative and support, 50.0 − 45.7 = +4.3 | 18 / 0 |
| Top | Male | Education (+12.4) | Water and waste (−2.5) | 15 / 3 |
| Top | Female | Public administration and defence (+12.4) | Administrative and support (+1.6) | 18 / 0 |
| Senior | Total | Education, 61.0 − 40.2 = +20.8 | Health and social work, 60.0 − 54.9 = +5.1 | 18 / 0 |
| Senior | Male | Education and Information and communication (both +10.7) | Water and waste (−2.0) | 17 / 1 |
| Senior | Female | Water and waste (+12.5) | Health and social work (−3.0) | 17 / 1 |

### April 2025 final targets and supplementary proxy

All 108 final targets and 216 proxy comparisons reconcile. The five-year total targets run from 34.0% to 91.7% for top management and 52.6% to 95.9% for senior management. Agriculture is lowest and public administration highest at both levels. These targets apply to designated groups, whose statutory definition covers qualifying Black people, women and people with disabilities, counted once, subject to citizenship rules. The supplementary proxy counts African, Coloured and Indian men and African, Coloured, Indian and White women once each over every manager in the sector and occupational level, including foreign nationals in the denominator. It cannot establish qualifying citizenship or identify qualifying White men with disabilities. Repeated and inconsistent disability cells in the 24th CEE report make a disability adjustment especially unsuitable. The disability benchmark is separate. [Final gazette](https://www.gov.za/sites/default/files/gcis_document/202504/52514gon6124.pdf) · [Administrative regulations and workforce templates](https://ee.labour.gov.za/DMISO/Employment%20Equity%20Regulations.pdf) · [Independent proxy comparisons](../diagnostics/independent_methodology/ee_final_proxy.csv)

For agriculture top management, the 2023 proxy is 1,467/5,055 = 29.02%, compared with the 34.0% final target, a difference of 4.98 points. The 2024 proxy is 1,532/5,144 = 29.78%, giving 4.22 points. The 2023 workforce release was public before 15 April 2025. The 2024 workforce tables are retrospective for this event even though their reporting year precedes it. The 2025 workforce returns are in a separate reporting regime. Keep the signed proxy comparisons supplementary and describe figures such as these as distances from a proxy. Comparing them to the 2023 draft gaps as a time series, ranking legal shortfalls or classifying employers’ attainment would require a common eligible population and suitable employer data. [Source chronology and disability review](../../../../docs/part_b/supporting_independent_review.md#publication-timing)

## QLFS employment context

| Q3 workforce year | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Published national total (millions of people) | 15.833 | 16.192 | 16.380 | 16.375 | 14.691 | 14.282 | 15.765 | 16.745 | 16.946 | 17.055 |

The ten published national totals and 100 industry estimates reconcile. The national total exceeds the ten listed industries by 3,000–15,000 people, consistent with the inclusion of Other and independent rounding. The published point estimates show a broad contraction and recovery. Use the paired release vintages and flag the 2020–2021 telephone collection, the 2022 return to mainly in-person interviewing, and the 2025 questionnaire revision, which especially affects formal and informal classifications. Differences across vintages and survey modes warrant caution, especially for small changes. QLFS covers employed people aged 15–64 in a household survey and supplies no denominator for management representation or ownership. [National employment](../tables/qlfs_q3_national_employment.csv) · [Industry employment](../tables/qlfs_q3_industry_employment.csv) · [Stats SA 2025 update](https://www.statssa.gov.za/publications/P0211/P02113rdQuarter2025.pdf)

## Primary figures and supporting tables

I rendered and inspected the original and final one-page PDFs. At approximately 160 mm text width, the axes, data labels, sector labels and source notes were legible, with the smallest text in the captions. I checked the final PDF geometry against the tables. All 36 management markers, 48 ownership markers and 36 draft-gap segments reconciled within 0.01 units on their respective axes. Each of the three open ownership markers sits in a gap in its line. Keep the vector files and place them at full text width, especially the 18-sector figure. [PDF geometry diagnostics](../diagnostics/independent_methodology/figure_geometry.json)

| Figure | Assessment and placement |
| --- | --- |
| **1. National management representation** | Both panels use a 0–60% scale. The 2024 endpoint labels reconcile to 36.1%, 49.6%, 13.7% and 20.4%. Solid and dashed lines distinguish levels independent of colour. Open markers identify the retrospective 2016 counts only. Use beside the 2019–2024 sector change table to show the distribution of observed management changes. [PDF](../figures/national_management_representation.pdf) |
| **2. Reported black economic interest** | Both panels share a zero-based scale extending to 66%. The national and code endpoints reconcile to the published values at display precision. Direct labels identify each series. The open Construction 2017 and Tourism 2020–2021 points are published values. The final lines break at those observations, with no interpolation across them. Use the full code table and sample counts beside any discussion of rankings or sensitivity. [PDF](../figures/reported_black_economic_interest.pdf) |
| **3. May 2023 draft target shortfalls** | Both panels use the same zero-based percentage-point scale and top-management sector order. All 36 total gaps match the independently calculated signs and range. Senior management uses the same order to preserve sector alignment. The two panels show proposed benchmark gaps; include the observed CEE sector movement table for actual changes in representation and keep the six-by-18 signed target grid in the appendix or linked tables. [PDF](../figures/draft_ee_target_shortfalls.pdf) |

Together the figures and the 18-sector management change table supply national representation, actual sector representation changes, selected code-level ownership patterns and sector differences in the proposed benchmarks. Retain annual CEE and full ownership paths, all four ownership measures, pair and status diagnostics, the separate 2025 series and final-target table, and QLFS industry detail as supporting tables. The final-target proxy should stay supplementary. [Reader-facing results and sector table](part_b_preliminary_results.md)

## Approved economic interpretation for the combined report

- Between 2016 and 2024, the Black and Black female shares of reported management posts rose, with larger national gains in senior management. Most detailed sectors reported increases in their Black management share between 2019 and 2024, and all reported increases in their Black female share at both levels. Changes in the set and employment mix of reporting employers can contribute to these movements.
- The Commission’s national sample recorded higher average Black and Black female economic interest and voting rights in 2023 than in 2016. The strongest cross-code result is the increase in Black economic interest among all codes with usable fixed endpoints. National wealth ownership, within-firm changes and policy effects lie outside this evidence.
- The May 2023 notice reveals differences in how far published sector profiles were from the proposed benchmarks. This is information available in the announcement and can contextualise the May 2023 market event. Its first public disclosure hour remains uncertain, and the distances cannot be assigned to JSE issuers from these aggregate tables. The April 2025 benchmarks cover designated groups. The retrospective B-BBEE ownership series was published in 2026 after the January 2026 Part A event, so use it as historical context for the reader.
- Part A describes benchmark-relative JSE price behaviour around policy announcements in a selected sample. The May 2023 and April 2025 short-window aggregate estimates are close to zero with intervals spanning both signs. No registered headline test rejects after Holm adjustment at 5%. Interpret the estimates with the Part A review’s timing, overlapping-news, return-convention and conditional-inference qualifications. Realised efficiency, productivity and profitability are separate outcomes. A coherent combined report places these conditional market observations alongside the Part B equity measures without combining them into an estimated tradeoff. [Part A final methodology review](../../reports/final_methodology_review.md)

## Reproducibility and outstanding limitations

Run from the repository root.

```sh
Rscript --vanilla scripts/part_b/run_analysis.R
python3 scripts/part_b/review/verify_methodology.py
```

The revised R run passed **89 automated checks**, including the new guard on Figure 2 line values and gaps. The checks cover uniqueness and completeness, count reconciliation, selection periods, sector labels, ownership exclusions and endpoint availability, gazette pairings, proxy construction and figure inputs. They catch internal errors and drift. They cannot establish source coverage, stable populations, unknown weights or legal eligibility. The independent calculation reconciled **2,876 keyed rows across all 23 R tables**, with up to 0.00005 percentage points of expected B-BBEE status rounding and less than 10⁻¹² numerical disagreement elsewhere. Two final R runs produced 30 byte-identical outputs and three identical PDF renders. SHA-256 fingerprints matched for all 330 pre-existing Part A output files and all 60 Part B collection files, including local publications. [Validation log](../diagnostics/validation_checks.csv) · [R session](../diagnostics/session_info.txt) · [Independent verification diagnostics](../diagnostics/independent_methodology/verification.json) · [Preservation and rerun record](../diagnostics/independent_methodology/preservation_and_rerun.json)

**Part B has no outstanding analytical blocker for descriptive integration.** Carry the source and reporting-population limits into the combined report itself. The Part A qualifications and supervisor decisions in its final review still govern the scope of thesis claims. The combined report remains the next distinct deliverable.
