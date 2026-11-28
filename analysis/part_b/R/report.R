pct <- function(x, digits = 1) sprintf("%.*f%%", digits, x)
points <- function(x, digits = 1) sprintf("%+.*f", digits, x)
count_label <- function(x) format(x, big.mark = ",", scientific = FALSE, trim = TRUE)

ownership_labels <- c(
  black_economic_interest = "Black economic interest",
  black_female_economic_interest = "Black female economic interest",
  black_voting_rights = "Black voting rights",
  black_female_voting_rights = "Black female voting rights"
)

build_report <- function(tables, code_groups) {
  national <- tables$cee_national_management_change[order(match(occupational_level, cee_levels), indicator)]
  national_rows <- national[, sprintf("| %s | %s | %s | %s | %s |",
                                      occupational_level, indicator, pct(start_pct), pct(end_pct), points(change_pp))]
  level_gap <- tables$cee_national_management_level_gaps
  eap <- tables$cee_national_eap[reporting_year == 2024]
  sectors <- tables$cee_sector_management_change
  top_black <- sectors[occupational_level == "Top management" & indicator == "Black"]
  senior_black <- sectors[occupational_level == "Senior management" & indicator == "Black"]
  female <- sectors[indicator == "Black female"]
  sector_table <- dcast(sectors, sector_label ~ occupational_level + indicator, value.var = "change_pp")
  sector_rows <- sector_table[order(sector_label), sprintf("| %s | %s | %s | %s | %s |",
    sector_label, points(`Top management_Black`), points(`Top management_Black female`),
    points(`Senior management_Black`), points(`Senior management_Black female`))]
  sector_gaps <- tables$cee_sector_management_level_gaps[reporting_year == 2024]
  agriculture <- top_black[sector_id == "agriculture"]
  public <- top_black[sector_id == "public_administration"]
  regime <- tables$cee_management_2025_separate_regime[geographic_scope == "National"]
  coverage <- tables$cee_national_reporting_coverage[reporting_year %in% 2024:2025]

  ownership <- tables$bbbee_ownership_change_and_sensitivity
  ownership_national <- ownership[sector_original == "National"][match(ownership_measures, ownership_measure)]
  ownership_rows <- ownership_national[, sprintf("| %s | %s | %s | %s |",
                                                  ownership_labels[ownership_measure], pct(start_pct, 2),
                                                  pct(end_pct, 2), points(change_pp, 2))]
  selected <- ownership[ownership_measure == "black_economic_interest" & sector_original %in% code_groups]
  selected <- selected[order(-change_pp)]
  selected_summary <- selected[, paste(sprintf("%s (%s pp)", sector_original, points(change_pp, 2)),
                                       collapse = ", ")]
  plotted <- tables$bbbee_ownership_annual[sector_original == "National" &
                                           ownership_measure == "black_female_economic_interest"]
  excluded <- ownership[!is.na(change_pp) & is.na(change_pp_pair_excluded)]
  endpoint_sensitivity <- tables$bbbee_ownership_sector_direction_sensitivity[match(ownership_measures, ownership_measure)]
  sensitivity_rows <- endpoint_sensitivity[, sprintf("| %s | %d of %d | %d of %d |",
    ownership_labels[ownership_measure], published_increases, published_sectors,
    pair_excluded_increases, pair_excluded_sectors)]
  compliance <- tables$bbbee_compliance_levels_1_to_4[sector_original == "National"]
  compliance_codes <- tables$bbbee_compliance_levels_1_to_4[reporting_year == 2023 & sector_original != "National"]
  anomaly_pairs <- tables$bbbee_ownership_anomaly_pairs

  draft <- tables$ee_draft_2023_target_shortfalls
  draft_extremes <- draft[, .(
    largest = paste(sector_label[shortfall_pp == max(shortfall_pp)], collapse = ", "),
    hi = max(shortfall_pp), smallest = paste(sector_label[shortfall_pp == min(shortfall_pp)], collapse = ", "),
    lo = min(shortfall_pp), above = sum(shortfall_pp < 0)
  ), by = .(occupational_level, gender)]
  draft_extremes <- draft_extremes[order(match(occupational_level, ee_levels), match(gender, c("total", "male", "female")))]
  draft_rows <- draft_extremes[, sprintf("| %s | %s | %s (%s) | %s (%s) | %d |",
    cee_levels[match(occupational_level, ee_levels)], tools::toTitleCase(gender),
    largest, points(hi), smallest, points(lo), above)]
  final <- tables$ee_final_2025_targets[gender == "total"]
  employment <- tables$qlfs_q3_national_employment

  c(
    "# Part B preliminary descriptive results",
    "",
    "## Management representation",
    "",
    "| Management level | Population | 2016 share | 2024 share | Change (pp) |",
    "| --- | --- | ---: | ---: | ---: |",
    national_rows,
    "",
    "Percentage-point changes use the underlying count-derived shares before rounding.",
    "",
    sprintf(paste(
      "Black representation rose at both levels, with larger gains in senior management.",
      "The senior-minus-top gap widened from %.1f to %.1f percentage points for black managers and from %.1f to %.1f for black women.",
      "Black female representation rose throughout the series, while remaining well below overall black representation.",
      "For context, the CEE’s Q3 2024 national economically active population (EAP) components sum to %s black and %s black female.",
      "The EAP describes the economically active population across occupations. Management shares describe jobs at a specific occupational level among reporting employers."
    ),
    level_gap[reporting_year == 2016 & indicator == "Black", senior_minus_top_pp],
    level_gap[reporting_year == 2024 & indicator == "Black", senior_minus_top_pp],
    level_gap[reporting_year == 2016 & indicator == "Black female", senior_minus_top_pp],
    level_gap[reporting_year == 2024 & indicator == "Black female", senior_minus_top_pp],
    pct(eap$black_eap_pct), pct(eap$black_female_eap_pct)),
    "",
    sprintf(paste(
      "From 2019 to 2024, black representation rose in %d of 18 sectors in top management and %d of 18 in senior management.",
      "Black female representation rose in all %d sector-by-level comparisons.",
      "The largest gains in black representation were in %s in top management (%s pp) and %s in senior management (%s pp).",
      "The 2024 levels still differed widely. Agriculture, forestry and fishing reported %s black and %s black female in top management,",
      "compared with %s and %s in public administration and defence.",
      "In 2024 senior management shares were higher in %d of 18 sectors for black managers and %d of 18 for black women.",
      "These differences describe the composition of reported jobs. Employer composition, the mix of jobs and movement into management can all matter."
    ),
    top_black[, sum(change_pp > 0)], senior_black[, sum(change_pp > 0)], female[, sum(change_pp > 0)],
    top_black[which.max(change_pp), sector_label], points(max(top_black$change_pp)),
    senior_black[which.max(change_pp), sector_label], points(max(senior_black$change_pp)),
    pct(agriculture$end_pct), pct(female[sector_id == "agriculture" & occupational_level == "Top management", end_pct]),
    pct(public$end_pct), pct(female[sector_id == "public_administration" & occupational_level == "Top management", end_pct]),
    sector_gaps[indicator == "Black", sum(senior_minus_top_pp > 0)],
    sector_gaps[indicator == "Black female", sum(senior_minus_top_pp > 0)]),
    "",
    paste(
      "The analysis divides source-defined African, Coloured and Indian counts by all managers at the relevant level, including foreign nationals.",
      "The black female numerator uses women in those three groups with the same full denominator.",
      "The 2016 baseline uses the retrospective 19th CEE report, whose workforce grand total exceeds the original coverage total by 34,213.",
      "Using the original 17th report’s separate national counts changes the four estimated gains by at most 0.11 percentage points.",
      "Published 2019 sector counts fall short of the national counts by 31 top and 256 senior managers.",
      "For 2024 the count-based shares take precedence over discrepant printed percentages.",
      "The six-year sector comparison uses the detailed 18-sector labels and documented aliases. Each year describes the employers that reported in that cycle.",
      "[CEE independent review](../../../docs/part_b/cee_independent_review.md) ·",
      "[Baseline and sector-mix sensitivities](../diagnostics/independent_methodology/verification.json) ·",
      "[Annual sector table](../tables/cee_sector_management.csv) ·",
      "[Sector changes](../tables/cee_sector_management_change.csv) ·",
      "[Sector gaps by level](../tables/cee_sector_management_level_gaps.csv) ·",
      "[EAP benchmarks](../tables/cee_national_eap.csv)"
    ),
    "",
    "**Change in reported management shares by sector, 2019–2024 (percentage points)**",
    "",
    "| Sector | Top Black | Top Black female | Senior Black | Senior Black female |",
    "| --- | ---: | ---: | ---: | ---: |",
    sector_rows,
    "",
    "### Separate 2025 reporting regime",
    "",
    sprintf(paste(
      "In 2025, the national return reported black shares of %s in top management and %s in senior management.",
      "The corresponding black female shares were %s and %s.",
      "Reports received fell from %s in 2024 to %s in 2025, and covered employees from %s to %s.",
      "The amended designated-employer definition changed which employers report, including removing turnover-based designation for employers with fewer than 50 employees.",
      "The 2025 percentages describe that reporting population. The historical trend ends in 2024.",
      "[Separate management table](../tables/cee_management_2025_separate_regime.csv) ·",
      "[National reporting coverage](../tables/cee_national_reporting_coverage.csv)"
    ),
    pct(regime[occupational_level == "Top management", black_representation_pct]),
    pct(regime[occupational_level == "Senior management", black_representation_pct]),
    pct(regime[occupational_level == "Top management", black_female_representation_pct]),
    pct(regime[occupational_level == "Senior management", black_female_representation_pct]),
    count_label(coverage$reports_received[1]), count_label(coverage$reports_received[2]),
    count_label(coverage$employees_covered[1]), count_label(coverage$employees_covered[2])),
    "",
    "## Reported ownership and B-BBEE levels",
    "",
    "| Published national average | 2016 | 2023 | Change (pp) |",
    "| --- | ---: | ---: | ---: |",
    ownership_rows,
    "",
    sprintf(paste(
      "Economic interest is the primary ownership indicator because it describes reported participation in economic benefits.",
      "Voting rights describe a distinct governance dimension. All four national averages rose over the period.",
      "The female economic-interest average peaked at %s in %d before ending at %s.",
      "Black economic interest rose across all nine code groups with published 2016 and 2023 endpoints, with gains ranging from %s to %s pp.",
      "The largest published gain was Forestry, where the contextual sample had %d entries in 2016 and %d in 2023.",
      "Among the four codes shown in Figure 2, the endpoint gains were %s.",
      "The number and mix of sampled entries changed, including a rise in national sample entries from %s to %s."
    ),
    pct(max(plotted$ownership_pct), 2), plotted[which.max(ownership_pct), reporting_year],
    pct(plotted[reporting_year == 2023, ownership_pct], 2),
    points(ownership[ownership_measure == "black_economic_interest" & sector_original != "National", min(change_pp, na.rm = TRUE)], 2),
    points(ownership[ownership_measure == "black_economic_interest" & sector_original != "National", max(change_pp, na.rm = TRUE)], 2),
    ownership[ownership_measure == "black_economic_interest" & sector_original == "Forestry", start_context_n],
    ownership[ownership_measure == "black_economic_interest" & sector_original == "Forestry", end_context_n],
    selected_summary, count_label(ownership_national$start_context_n[1]), count_label(ownership_national$end_context_n[1])),
    "",
    paste(
      "National values are the Commission’s published averages. Each year draws on a selective sample of verification certificates and reports.",
      "Unknown weighting and ownership-specific denominators, changes to code rules, and shifts in the mix of enterprise sizes and codes limit interpretation.",
      "These averages describe the Commission’s sample. The historical series was published in 2026, after the January 2026 event studied in Part A.",
      "The unauthenticated 2022 portal series is excluded. The MAC code first appears in 2017 and has no 2016 endpoint.",
      "[B-BBEE independent review](../../../docs/part_b/bbbee_independent_review.md) ·",
      "[All ownership series](../tables/bbbee_ownership_annual.csv) ·",
      "[Code-level changes and sample context](../tables/bbbee_ownership_change_and_sensitivity.csv)"
    ),
    "",
    "### Sensitivity to flagged ownership pairs",
    "",
    sprintf(paste(
      "The source review flagged %d cases where the published female average exceeds the corresponding overall average.",
      "Within 2016–2023 there are %d such cases. The sensitivity removes both published values in each of those pairs and preserves them in the primary results.",
      "The remaining %d cases are Financial Services observations from 2015, outside the primary period.",
      "All national results and all remaining fixed-endpoint changes are identical.",
      "The exclusion removes the 2016 economic-interest baseline for Generic and the 2016 voting-rights baseline for Financial Services.",
      "Starting those series in 2017 gives a different comparison window. Generic economic interest changes by %s pp overall and %s pp for women.",
      "Financial Services voting rights change by %s pp overall and %s pp for women over that shorter window.",
      "The annual paths for Construction, Tourism, Agri-BEE and Financial Services have some flagged intermediate observations.",
      "[Ten source pairs](../tables/bbbee_ownership_anomaly_pairs.csv) ·",
      "[Annual comparison](../tables/bbbee_ownership_annual_sensitivity.csv)"
    ),
    nrow(anomaly_pairs), sum(anomaly_pairs$in_primary_period), sum(!anomaly_pairs$in_primary_period),
    points(excluded[ownership_measure == "black_economic_interest", change_from_first_retained_pp], 2),
    points(excluded[ownership_measure == "black_female_economic_interest", change_from_first_retained_pp], 2),
    points(excluded[ownership_measure == "black_voting_rights", change_from_first_retained_pp], 2),
    points(excluded[ownership_measure == "black_female_voting_rights", change_from_first_retained_pp], 2)),
    "",
    "| Indicator | Codes with a 2016–2023 increase, published values | Codes with an increase after pair exclusion |",
    "| --- | ---: | ---: |",
    sensitivity_rows,
    "",
    "### Supplementary status evidence",
    "",
    sprintf(paste(
      "Levels 1–4 accounted for %s of the valid national status denominator in 2016, %s in 2017 and %s in 2023.",
      "The national shares show a different pattern from the ownership averages.",
      "In 2023 these levels accounted for %s of Construction entries and %s of Tourism entries with valid status denominators.",
      "Status combines multiple scorecard elements and is sensitive to rules and sample mix.",
      "The analysis excludes the National 2018 and Financial Services 2016 distributions because the status counts fail to reconcile.",
      "Levels 5–8 are contributor levels. The report publishes a separate Non-Compliant category.",
      "Dashes remain missing at level detail. The Levels 1–4 summary allows a zero only where the printed percentage is zero and the counts already reconcile.",
      "[Levels 1–4 shares](../tables/bbbee_compliance_levels_1_to_4.csv) ·",
      "[Valid distributions](../tables/bbbee_compliance_levels_valid.csv) ·",
      "[Excluded distributions](../tables/bbbee_compliance_exclusions.csv)"
    ),
    pct(compliance[reporting_year == 2016, analytical_value]),
    pct(compliance[reporting_year == 2017, analytical_value]),
    pct(compliance[reporting_year == 2023, analytical_value]),
    pct(compliance_codes[sector_original == "Construction", analytical_value]),
    pct(compliance_codes[sector_original == "Tourism", analytical_value])),
    "",
    "## Employment Equity sector targets",
    "",
    "### May 2023 draft",
    "",
    paste(
      "The signed shortfall is the published national BLACK target minus the 2022 BLACK workforce share in the same gazette.",
      "The observed profile was available when the draft was announced on 12 May 2023.",
      "All 18 sectors had positive total shortfalls at both management levels. Some gender-specific shares exceeded the proposed benchmark.",
      "Each gender share uses the full management level. The signed gender gaps add to the total and a negative gap means the observed share exceeded the proposed target.",
      "The distances describe how far each published sector profile was from the national proposal. Employer-level requirements depend on the applicable benchmark and employer circumstances.",
      "[All draft target and baseline pairs](../tables/ee_draft_2023_target_shortfalls.csv) ·",
      "[Supporting independent review](../../../docs/part_b/supporting_independent_review.md)"
    ),
    "",
    "| Management level | Gender | Largest shortfall (pp) | Smallest signed gap (pp) | Sectors above target |",
    "| --- | --- | --- | --- | ---: |",
    draft_rows,
    "",
    "### April 2025 final targets",
    "",
    sprintf(paste(
      "The published five-year designated-group targets range from %s to %s in top management and from %s to %s in senior management.",
      "Agriculture, forestry and fishing has the lowest target at both levels and public administration and defence the highest.",
      "The designated-group definition includes qualifying Black people, women and persons with disabilities subject to citizenship criteria.",
      "Its composition differs from the 2023 BLACK definition, so the 2025 targets are presented in their own table.",
      "[Published final targets](../tables/ee_final_2025_targets.csv)"
    ),
    pct(final[occupational_level == "top_management", min(target_pct)]),
    pct(final[occupational_level == "top_management", max(target_pct)]),
    pct(final[occupational_level == "senior_management", min(target_pct)]),
    pct(final[occupational_level == "senior_management", max(target_pct)])),
    "",
    paste(
      "The supplementary CEE race-by-sex proxy combines African, Coloured and Indian men with African, Coloured, Indian and White women.",
      "The denominator includes all managers at each level, including foreign nationals. The proxy omits qualifying White men with disabilities and cannot verify statutory citizenship.",
      "The CEE disability counts are excluded from the construction because they contain repeated and internally inconsistent observations.",
      "Workforce year 2023 was public at the April 2025 announcement. The 2024 tables appeared later and are retrospective context.",
      "The signed differences describe distances between the published targets and the proxy. Statutory attainment requires data on the eligible population and the applicable employer requirements.",
      "[Supplementary proxy comparisons](../tables/ee_final_2025_cee_proxy_supplement.csv)"
    ),
    "",
    "## Employment context and relationship to Part A",
    "",
    sprintf(paste(
      "Stats SA’s published Q3 employment total was %.3f million in 2016, %.3f million in 2019, %.3f million in 2021 and %.3f million in 2025.",
      "The published series places the representation results alongside a broad employment contraction and subsequent recovery.",
      "The household survey tables retain their paired publication vintages, telephone-interview flags for 2020–2021, return to mainly in-person collection in 2022 and questionnaire revision in 2025.",
      "CEE management and B-BBEE ownership use their own populations. The QLFS industry definitions are retained for context.",
      "[Published national totals](../tables/qlfs_q3_national_employment.csv) ·",
      "[QLFS industry estimates](../tables/qlfs_q3_industry_employment.csv)"
    ), employment[observation_year == 2016, employment_persons] / 1e6,
    employment[observation_year == 2019, employment_persons] / 1e6,
    employment[observation_year == 2021, employment_persons] / 1e6,
    employment[observation_year == 2025, employment_persons] / 1e6),
    "",
    paste(
      "Part A estimates short-window JSE price reactions around announcements. The May 2023 draft gaps describe differences across sectors in the same notice.",
      "The reports also place those announcements in the context of changes in management composition and reported ownership.",
      "Market reactions capture a different outcome from realised efficiency. The transformation series describes reporting populations and policy benchmarks.",
      "The two parts together support a descriptive discussion of market reactions and equity outcomes. Estimating a causal efficiency–equity tradeoff would require evidence on realised efficiency, policy effects and a counterfactual.",
      "[Part A corrected analysis](../../reports/methodological_corrections_report.md)"
    ),
    "",
    "## Primary figures",
    "",
    "- **National management representation** shows both management levels and the two representation measures on a common scale. The primary figure ends in 2024. [PDF](../figures/national_management_representation.pdf) · [PNG](../figures/national_management_representation.png)",
    "- **Reported black economic interest** shows national averages and the four codes with usable fixed endpoints and at least 30 sample entries at each. This screen uses overall sample counts. Open points retain flagged published values and the lines break at those years. [PDF](../figures/reported_black_economic_interest.pdf) · [PNG](../figures/reported_black_economic_interest.png)",
    "- **May 2023 draft shortfalls** compares all 18 sectors across management levels and directly contextualises the 2023 announcement. The CEE sector tables give the annual representation series and comparisons by level. [PDF](../figures/draft_ee_target_shortfalls.pdf) · [PNG](../figures/draft_ee_target_shortfalls.png)"
  )
}
