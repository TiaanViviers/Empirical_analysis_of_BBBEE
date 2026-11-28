check_triplets <- function(data, value, label) {
  triplets <- dcast(data, sector_id + occupational_level ~ gender, value.var = value)
  check(paste(label, "preserves the published sex shares and totals"),
        is_pct(data[[value]]) && near(triplets$total, triplets$male + triplets$female))
}

analyse_targets <- function(inputs, management) {
  targets <- inputs$ee_sector_targets
  reference <- inputs$ee_sector_reference
  baseline <- inputs$ee_gazette_workforce_baseline_2022[reporting_year == 2022 & population_group == "black" &
                                                        occupational_level %in% ee_levels]
  draft <- targets[policy_version == "draft_2023" & geographic_scope == "national" &
                     target_population == "black" & occupational_level %in% ee_levels]
  final <- targets[policy_version == "final_2025" & geographic_scope == "national" &
                     target_population == "designated_groups" & occupational_level %in% ee_levels]
  keys <- c("sector_id", "occupational_level", "gender")
  require_key(reference, "sector_id", "EE reviewed sector reference")
  check("EE analysis uses only the 18 reviewed detailed sectors",
        setequal(reference$sector_id, names(sector_labels)) &&
          all(reference$mapping_status %in% c("matched_label", "matched_within_report_evidence")))
  require_grid(draft, "Gazette 48589 BLACK draft targets", sector_id = reference$sector_id,
               occupational_level = ee_levels, gender = ee_genders)
  require_grid(baseline, "Gazette 48589 observed BLACK baseline", sector_id = reference$sector_id,
               occupational_level = ee_levels, gender = ee_genders)
  require_grid(final, "Gazette 52514 final designated-group targets", sector_id = reference$sector_id,
               occupational_level = ee_levels, gender = ee_genders)
  check_triplets(draft, "target_pct", "May 2023 BLACK targets")
  check_triplets(baseline, "observed_pct", "Gazette 2022 BLACK baseline")
  check_triplets(final, "target_pct", "April 2025 designated-group targets")

  paired <- merge(draft, baseline, by = keys, suffixes = c("_target", "_baseline"))
  paired <- merge(paired, reference[, .(sector_id, sector_name, draft_2023_sector_original, mapping_status)],
                  by = "sector_id")
  final <- merge(final, reference[, .(sector_id, sector_name, final_2025_sector_original, mapping_status)],
                 by = "sector_id")
  check("EE 2023 target and baseline pair one-to-one on the same gazette page and scale",
        nrow(paired) == nrow(draft) && nrow(paired) == nrow(baseline) &&
          all(paired$sector_original_target == paired$sector_original_baseline &
                paired$sector_original_target == paired$draft_2023_sector_original &
                paired$source_id_target == "EE2023" & paired$source_id_target == paired$source_id_baseline &
                paired$source_page_pdf_target == paired$source_page_pdf_baseline &
                paired$source_page_printed_target == paired$source_page_printed_baseline &
                paired$announcement_date == "2023-05-12" & paired$announcement_date == paired$publication_date))
  check("EE 2025 targets use the matching reviewed gazette labels and final notice",
        nrow(final) == 108L && all(final$sector_original == final$final_2025_sector_original &
                                   final$source_id == "EE2025" & final$announcement_date == "2025-04-15"))
  paired[, `:=`(shortfall_pp = round(target_pct - observed_pct, 1),
                sector_label = unname(sector_labels[sector_id]))]
  paired[, shortfall_rank := frank(-shortfall_pp, ties.method = "min"), by = .(occupational_level, gender)]
  final[, sector_label := unname(sector_labels[sector_id])]
  check("Signed 2023 shortfalls equal target minus published baseline, including negatives",
        near(paired$shortfall_pp, paired$target_pct - paired$observed_pct) &&
          near(paired[sector_id == "agriculture" & occupational_level == "top_management" &
                        gender == "total", shortfall_pp], 18.9) &&
          all(sign(paired$shortfall_pp) == sign(paired$target_pct - paired$observed_pct)))
  triplets <- dcast(paired, sector_id + occupational_level ~ gender, value.var = "shortfall_pp")
  check("The signed gender shortfalls add to the total shortfall within each sector and level",
        near(triplets$total, triplets$male + triplets$female))

  # The raw CEE rows were already checked against their ten-cell occupation totals.
  eligible <- management$demographics[reporting_year %in% 2023:2024 & geographic_scope == "Sector" &
                                       reporting_population == "All reporting employers"]
  proxy <- eligible[, .(
    total_managers = first(total_employees),
    male = sum(employee_count[gender == "Male" & population_group %in% black_groups]),
    female = sum(employee_count[gender == "Female" & population_group %in% c(black_groups, "White")])
  ), by = .(reporting_year, sector_original, occupational_level, source_id, source_page_pdf, reporting_population)]
  source_labels <- rbindlist(lapply(2023:2024, function(year) {
    data.table(reporting_year = year, sector_id = reference$sector_id,
               sector_original = reference[[paste0("cee_", year, "_sector_original")]])
  }))
  proxy <- merge(proxy, source_labels, by = c("reporting_year", "sector_original"), all.x = TRUE)
  proxy[, `:=`(total = male + female, occupational_level = ee_levels[match(occupational_level, cee_levels)])]
  proxy <- melt(proxy, measure.vars = ee_genders, variable.name = "gender", value.name = "proxy_count",
                variable.factor = FALSE)
  require_grid(proxy, "Supplementary CEE proxy", reporting_year = 2023:2024, sector_id = reference$sector_id,
               occupational_level = ee_levels, gender = ee_genders)
  proxy[, `:=`(proxy_pct = 100 * proxy_count / total_managers,
                workforce_timing = fifelse(reporting_year == 2023L, "Pre-announcement context", "Retrospective context"),
                proxy_definition = "CEE race-by-sex proxy; qualifying citizenship and disability union unavailable")]
  check_triplets(proxy[reporting_year == 2023], "proxy_pct", "Workforce year 2023 CEE proxy")
  check_triplets(proxy[reporting_year == 2024], "proxy_pct", "Workforce year 2024 CEE proxy")
  proxy <- merge(proxy, final[, .(sector_id, occupational_level, gender, target_pct, sector_label,
                                  target_population, announcement_date, source_id, source_page_pdf)],
                 by = keys, suffixes = c("_cee", "_target"), all.x = TRUE)
  proxy[, difference_from_cee_proxy_pp := target_pct - proxy_pct]
  check("Final targets join both qualified proxy years without expanding or dropping observations",
        nrow(proxy) == 216L && !anyNA(proxy$target_pct) &&
          near(proxy[gender == "total", proxy_pct],
               100 * proxy[gender == "total", proxy_count / total_managers]))
  setorder(paired, occupational_level, gender, shortfall_rank, sector_id)
  setorder(final, sector_id, occupational_level, gender)
  setorder(proxy, reporting_year, sector_id, occupational_level, gender)
  list(ee_draft_2023_target_shortfalls = paired, ee_final_2025_targets = final,
       ee_final_2025_cee_proxy_supplement = proxy)
}

analyse_employment <- function(inputs) {
  employment <- inputs$statssa_sector_employment[geographic_scope == "national" & observation_quarter == 3 &
                                                  observation_year %in% 2016:2025]
  require_grid(employment, "QLFS Q3 Table B", observation_period = paste0(2016:2025, "Q3"),
               industry_standardised = unique(employment$industry_standardised))
  check("QLFS original units, vintage and methodology flags are complete",
        nrow(employment) == 110L && all(employment$published_unit == "Thousand") &&
          near(employment$employment_persons, 1000 * employment$published_employment_value) &&
          !anyNA(employment$publication_vintage) && !anyNA(employment$comparability_flag) &&
          all(has_flag(employment[observation_year %in% 2020:2021, comparability_flag], "pandemic_phone")) &&
          all(has_flag(employment[observation_year == 2022, comparability_flag], "in_person")) &&
          all(has_flag(employment[observation_year == 2025, comparability_flag], "questionnaire_revision")))
  national <- employment[industry_standardised == "national_total"][order(observation_year)]
  industries <- employment[industry_standardised != "national_total"][order(industry_standardised, observation_year)]
  industry_sums <- industries[, .(industry_sum = sum(employment_persons)), by = observation_year]
  differences <- industry_sums[national, on = "observation_year", employment_persons - industry_sum]
  check("QLFS national totals use published Table B rows, independently of rounded industry estimates",
        uniqueN(national$observation_year) == 10L && all(differences >= 3000 & differences <= 15000) &&
          near(national[match(c(2016L, 2025L), observation_year), employment_persons], c(15833000, 17055000)))
  national[, change_from_prior_q3_persons := employment_persons - shift(employment_persons)]
  list(qlfs_q3_national_employment = national, qlfs_q3_industry_employment = industries)
}
