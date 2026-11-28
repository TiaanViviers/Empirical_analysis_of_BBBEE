detailed_sector_map <- function(management, reference, crosswalk) {
  labels <- unique(management[, .(reporting_year, sector_original, source_id, source_page_pdf)])
  classifications <- crosswalk[, .(reporting_year, sector_original, classification_system)]
  labels <- merge(labels, classifications, by = c("reporting_year", "sector_original"), all.x = TRUE)
  check("CEE sector input uses only the detailed classification",
        isTRUE(all(labels$classification_system == "CEE 18-sector system")))

  reference_labels <- c("draft_2023_sector_original", "final_2025_sector_original",
                        "cee_2023_sector_original", "cee_2024_sector_original")
  aliases <- unique(melt(reference, id.vars = "sector_id", measure.vars = reference_labels,
                         value.name = "sector_original")[, .(sector_id, sector_original)])
  aliases[, mapping_basis := "Exact label in reviewed EE/CEE 18-sector reference"]
  aliases <- rbind(aliases, data.table(
    sector_id = c("agriculture", "water_waste"),
    sector_original = c("AGRICULTURE FORESTRY & FISHING",
                        "WATER SUPPLY, SEWERAGE, WASTE MANAGEMENT AND PREMEDITATION ACTIVITIES"),
    mapping_basis = c("Punctuation variant of the reviewed agriculture label",
                      "CEE 20th report PDF pp. 28 and 31 match both Appendix C percentage vectors on p. 78")
  ))
  require_key(aliases, "sector_original", "CEE detailed-sector label reference")
  labels <- merge(labels, aliases, by = "sector_original", all.x = TRUE)
  require_grid(labels, "CEE detailed-sector mapping", reporting_year = 2019:2025,
               sector_id = reference$sector_id)
  for (year in 2023:2024) {
    source_column <- paste0("cee_", year, "_sector_original")
    index <- match(reference$sector_id, labels[reporting_year == year, sector_id])
    check(paste("CEE agrees with the exact reviewed reference for", year),
          identical(labels[reporting_year == year, sector_original][index], reference[[source_column]]))
  }
  labels[, sector_label := unname(sector_labels[sector_id])]
  setorder(labels, reporting_year, sector_id)
  labels[]
}

management_long <- function(data) {
  melt(data, measure.vars = c("black_representation_pct", "black_female_representation_pct"),
       variable.name = "indicator", value.name = "share_pct", variable.factor = FALSE)[
         , indicator := fifelse(indicator == "black_representation_pct", "Black", "Black female")]
}

management_level_gaps <- function(data, keys) {
  formula <- as.formula(paste(paste(c(keys, "indicator"), collapse = " + "), "~ occupational_level"))
  gaps <- dcast(data, formula, value.var = "share_pct")
  setnames(gaps, cee_levels, c("top_pct", "senior_pct"))
  gaps[, senior_minus_top_pp := senior_pct - top_pct]
  gaps[]
}

analyse_management <- function(inputs) {
  source <- inputs$cee_management_representation
  raw <- inputs$cee_management_representation_raw
  national <- source[geographic_scope == "National" & reporting_year %in% 2016:2024 &
                       occupational_level %in% cee_levels & calculation_method == "count_based"]
  sectors <- source[geographic_scope == "Sector" & reporting_year %in% 2019:2024 &
                      occupational_level %in% cee_levels & calculation_method == "count_based"]
  regime <- source[reporting_year == 2025 & geographic_scope %in% c("National", "Sector") &
                     occupational_level %in% cee_levels & calculation_method == "count_based"]

  require_grid(national, "CEE primary national management", reporting_year = 2016:2024,
               occupational_level = cee_levels)
  check("CEE 2016 national baseline retains retrospective count source and flag",
        all(national[reporting_year == 2016, source_id] == "cee_19th") &&
          all(has_flag(national[reporting_year == 2016, comparability_flag], "retrospective_2016")))
  require_grid(regime[geographic_scope == "National"], "CEE 2025 national management",
               reporting_year = 2025L, occupational_level = cee_levels)
  check("CEE 2025 is reported with the separate regime flag",
        nrow(regime) == 38L && all(has_flag(regime$comparability_flag, "2025_reporting_regime_break")))
  panel <- rbind(sectors, regime[geographic_scope == "Sector"])
  mapping <- detailed_sector_map(panel, inputs$ee_sector_reference, inputs$cee_sector_crosswalk)
  panel <- merge(panel, mapping[, .(reporting_year, sector_original, sector_id, sector_label)],
                 by = c("reporting_year", "sector_original"))
  require_grid(panel, "CEE detailed sector management", reporting_year = 2019:2025,
               sector_id = inputs$ee_sector_reference$sector_id, occupational_level = cee_levels)

  validated <- rbindlist(list(national, panel, regime[geographic_scope == "National"]), fill = TRUE)
  validated[geographic_scope == "National", sector_original := "National"]
  keys <- c("reporting_year", "geographic_scope", "sector_original", "reporting_population", "occupational_level")
  require_key(validated, keys, "Selected CEE management")
  demographics <- copy(raw)
  demographics[geographic_scope == "National", sector_original := "National"]
  demographics <- demographics[validated[, ..keys], on = keys, nomatch = NULL]
  require_key(demographics, c(keys, "population_group", "gender"), "Selected CEE demographic cells")
  check("CEE demographic inputs have count and category coverage",
        !anyNA(demographics$employee_count) && all(demographics$employee_count >= 0) &&
          all(demographics$employee_count == trunc(demographics$employee_count)) &&
          setequal(demographics$population_group, c(black_groups, "White", "Foreign national")) &&
          setequal(demographics$gender, c("Male", "Female")))
  recount <- demographics[, .(
    n_cells = .N, distinct_total = uniqueN(total_employees),
    demographic_total = sum(employee_count), published_total = first(total_employees),
    black_count = sum(employee_count[population_group %in% black_groups]),
    black_female_count = sum(employee_count[population_group %in% black_groups & gender == "Female"])
  ), by = keys]
  checked <- merge(validated, recount, by = keys, all = TRUE)
  check("CEE ten demographic cells and full occupation denominators reconcile",
        nrow(checked) == nrow(validated) && isTRUE(all(checked$n_cells == 10L &
          checked$distinct_total == 1L & checked$total_managers > 0 &
          checked$demographic_total == checked$published_total &
          checked$published_total == checked$total_managers)))
  check("CEE black and black female counts and shares reproduce from the raw cells",
        near(checked$black_manager_count, checked$black_count) &&
          near(checked$black_female_manager_count, checked$black_female_count) &&
          near(checked$black_representation_pct, 100 * checked$black_count / checked$total_managers) &&
          near(checked$black_female_representation_pct,
               100 * checked$black_female_count / checked$total_managers))

  sectors <- panel[reporting_year <= 2024]
  regime <- rbindlist(list(regime[geographic_scope == "National"], panel[reporting_year == 2025]),
                     fill = TRUE)
  gaps_2019 <- sectors[reporting_year == 2019, .(sector_total = sum(total_managers)),
                       by = occupational_level][national[reporting_year == 2019], on = "occupational_level"]
  check("CEE 2019 published sector counts remain 31 top and 256 senior managers below national",
        near(gaps_2019[match(cee_levels, occupational_level), total_managers - sector_total], c(31, 256)))

  eap <- inputs$cee_eap_benchmarks[geographic_scope == "National" & reporting_year %in% 2016:2025]
  require_grid(eap, "CEE national EAP", reporting_year = 2016:2025,
               population_group = c(black_groups, "White"), gender = c("Male", "Female"))
  check("CEE national EAP retains Q3 reference years and reported shares",
        is_pct(eap$representation_pct) && all(eap$reporting_year == eap$benchmark_year) &&
          all(eap$benchmark_quarter == 3L))
  eap <- eap[, .(
    black_eap_pct = sum(representation_pct[population_group %in% black_groups]),
    black_female_eap_pct = sum(representation_pct[population_group %in% black_groups & gender == "Female"]),
    source_quality_flag = paste(sort(unique(quality_flag)), collapse = ";")
  ), by = .(reporting_year, benchmark_year, benchmark_quarter, geographic_scope,
            source_id, source_page_pdf)]
  setorder(eap, reporting_year)
  check("CEE derived EAP benchmarks have one bounded observation per year",
        nrow(eap) == 10L && is_pct(eap$black_eap_pct) && is_pct(eap$black_female_eap_pct))

  coverage <- inputs$cee_reporting_coverage
  coverage_national <- coverage[geographic_scope == "National" & reporting_year %in% 2016:2025]
  require_grid(coverage_national, "CEE national reporting coverage", reporting_year = 2016:2025)
  check("CEE 2023 national coverage is retained despite the sector total discrepancy",
        coverage[geographic_scope == "Sector" & reporting_year == 2023, sum(employees_covered)] -
          coverage_national[reporting_year == 2023, employees_covered] == 300L)
  check("CEE coverage reproduces the 2025 reporting break",
        near(coverage_national[match(2024:2025, reporting_year), reports_received], c(29269, 15090)) &&
          near(coverage_national[match(2024:2025, reporting_year), employees_covered], c(7699665, 6896041)) &&
          has_flag(coverage_national[reporting_year == 2025, comparability_flag], "2025_reporting_regime_break"))

  national_long <- management_long(national)
  sector_long <- management_long(sectors)
  national_change <- percentage_change(national_long, c("occupational_level", "indicator"), 2016, 2024)
  sector_change <- percentage_change(sector_long, c("sector_id", "sector_label", "occupational_level", "indicator"),
                                     2019, 2024)
  national_gaps <- management_level_gaps(national_long, "reporting_year")
  sector_gaps <- management_level_gaps(sector_long, c("reporting_year", "sector_id", "sector_label"))
  check("CEE management change and level-gap tables are complete with correct percentage-point units",
        nrow(national_change) == 4L && nrow(sector_change) == 72L && nrow(sector_gaps) == 216L &&
          near(national_change[occupational_level == "Top management" & indicator == "Black", change_pp],
               100 * (21159 / 58554 - national[reporting_year == 2016 &
                   occupational_level == "Top management", black_manager_count] / 60037)) &&
          near(sector_gaps$senior_minus_top_pp, sector_gaps$senior_pct - sector_gaps$top_pct))

  setorder(national, reporting_year, occupational_level)
  setorder(sectors, sector_id, reporting_year, occupational_level)
  setorder(regime, geographic_scope, sector_id, occupational_level)
  list(tables = list(
    cee_national_management = national,
    cee_national_management_change = national_change,
    cee_national_management_level_gaps = national_gaps,
    cee_sector_management = sectors,
    cee_sector_management_change = sector_change,
    cee_sector_management_level_gaps = sector_gaps,
    cee_management_2025_separate_regime = regime,
    cee_sector_label_mapping = mapping,
    cee_national_eap = eap,
    cee_national_reporting_coverage = coverage_national[order(reporting_year)]
  ), demographics = demographics)
}
