ownership_measures <- c("black_economic_interest", "black_female_economic_interest",
                        "black_voting_rights", "black_female_voting_rights")

analyse_ownership <- function(inputs) {
  source <- inputs$bbbee_ownership[series_id == "retro_2026" & entity_size == "All" &
                                    ownership_measure %in% ownership_measures]
  keys <- c("series_id", "reporting_year", "sector_original", "ownership_measure")
  require_key(source, keys, "Retrospective ownership")
  check("Ownership includes all four measures with ownership-specific counts and weights unavailable",
        setequal(source$ownership_measure, ownership_measures) &&
          all(is.na(source$indicator_sample_n) & is.na(source$numerator) & is.na(source$denominator)))
  check("Retrospective ownership preserves the single blank in Property 2013",
        identical(source[is.na(ownership_pct), .(reporting_year, sector_original, ownership_measure)],
                  data.table(reporting_year = 2013L, sector_original = "Property",
                             ownership_measure = "black_female_economic_interest")))
  primary <- source[reporting_year %in% 2016:2023 & !is.na(ownership_pct)]
  require_grid(primary[sector_original == "National"], "National ownership",
               reporting_year = 2016:2023, ownership_measure = ownership_measures)
  check("Ownership primary years have ten published code groups with MAC starting in 2017",
        nrow(primary) == 348L && uniqueN(primary[sector_original != "National", sector_original]) == 10L &&
          identical(sort(unique(primary[sector_original == "MAC", reporting_year])), 2017:2023) &&
          all(primary[, .N, by = .(sector_original, reporting_year)]$N == 4L) &&
          is_pct(primary$ownership_pct) && all(primary$contextual_sample_n > 0))
  check("Primary ownership percentages match the printed values",
        near(primary$ownership_pct, as.numeric(sub(",", ".", sub("%$", "", primary$published_value_original)))))

  flagged <- source[has_flag(quality_flag, "female_average_exceeds_overall_unresolved")]
  pairs <- flagged[, .(
    series_id, reporting_year, sector_original,
    ownership_measure = sub("^black_female_", "black_", ownership_measure),
    female_measure = ownership_measure, female_pct = ownership_pct,
    female_published_value = published_value_original, female_quality_flag = quality_flag,
    contextual_sample_n, source_id, source_table, source_page_pdf
  )]
  overall <- source[, .(series_id, reporting_year, sector_original, ownership_measure,
                        overall_pct = ownership_pct, overall_published_value = published_value_original)]
  pairs <- merge(pairs, overall, by = keys, all.x = TRUE)
  pairs[, in_primary_period := reporting_year %in% 2016:2023]
  check("Ownership anomaly audit matches ten female observations to their overall values",
        nrow(pairs) == 10L && sum(pairs$in_primary_period) == 8L &&
          isTRUE(all(pairs$female_pct > pairs$overall_pct)) &&
          all(pairs[in_primary_period == FALSE, reporting_year] == 2015L))
  require_key(pairs, keys, "Matched ownership anomaly pairs")

  removals <- rbind(pairs[in_primary_period == TRUE, ..keys], pairs[in_primary_period == TRUE, .(
    series_id, reporting_year, sector_original, ownership_measure = female_measure
  )])
  require_key(removals, keys, "Anomaly sensitivity exclusions")
  sensitivity <- primary[, .(series_id, reporting_year, sector_original, ownership_measure,
                             published_pct = ownership_pct, contextual_sample_n, quality_flag,
                             comparability_flag, source_id, source_table, source_page_pdf)]
  sensitivity[, excluded_as_anomaly_pair := FALSE]
  sensitivity[removals, on = keys, excluded_as_anomaly_pair := TRUE]
  sensitivity[, pair_excluded_pct := fifelse(excluded_as_anomaly_pair, NA_real_, published_pct)]
  check("Pair exclusion masks both measures in eight pairs and leaves all national values intact",
        sum(sensitivity$excluded_as_anomaly_pair) == 16L &&
          all(sensitivity[excluded_as_anomaly_pair == TRUE, sector_original] != "National") &&
          identical(is.na(sensitivity$pair_excluded_pct), sensitivity$excluded_as_anomaly_pair) &&
          near(sensitivity[excluded_as_anomaly_pair == FALSE, pair_excluded_pct],
               sensitivity[excluded_as_anomaly_pair == FALSE, published_pct]))

  group_keys <- c("sector_original", "ownership_measure")
  setorder(sensitivity, sector_original, ownership_measure, reporting_year)
  endpoints <- sensitivity[, .(
    start_year = 2016L, end_year = 2023L,
    start_pct = published_pct[match(2016L, reporting_year)],
    end_pct = published_pct[match(2023L, reporting_year)],
    start_context_n = contextual_sample_n[match(2016L, reporting_year)],
    end_context_n = contextual_sample_n[match(2023L, reporting_year)],
    start_pct_pair_excluded = pair_excluded_pct[match(2016L, reporting_year)],
    end_pct_pair_excluded = pair_excluded_pct[match(2023L, reporting_year)],
    years_observed = .N, years_excluded = sum(excluded_as_anomaly_pair),
    first_observed_year = first(reporting_year), first_observed_pct = first(published_pct),
    first_retained_year = first(reporting_year[!excluded_as_anomaly_pair]),
    first_retained_pct = first(pair_excluded_pct[!excluded_as_anomaly_pair])
  ), by = group_keys]
  endpoints[, `:=`(
    change_pp = end_pct - start_pct,
    change_pp_pair_excluded = end_pct_pair_excluded - start_pct_pair_excluded,
    change_from_first_observed_pp = end_pct - first_observed_pct,
    change_from_first_retained_pp = end_pct_pair_excluded - first_retained_pct
  )]
  check("No ownership change is calculated for a missing fixed endpoint",
        nrow(endpoints) == 44L && sum(is.na(endpoints$change_pp)) == 4L &&
          sum(is.na(endpoints$change_pp_pair_excluded)) == 8L &&
          setequal(endpoints[!is.na(change_pp) & is.na(change_pp_pair_excluded), sector_original],
                   c("Generic", "Financial Services")) &&
          all(endpoints[sector_original == "MAC", first_observed_year] == 2017L))
  check("Ownership change calculations reproduce the four published national comparisons",
        near(endpoints[sector_original == "National"][match(ownership_measures, ownership_measure), change_pp],
             c(24.08, 15.11, 26.46, 10.93)))

  counts <- endpoints[sector_original != "National", .(
    published_sectors = sum(!is.na(change_pp)),
    published_increases = sum(change_pp > 0, na.rm = TRUE),
    pair_excluded_sectors = sum(!is.na(change_pp_pair_excluded)),
    pair_excluded_increases = sum(change_pp_pair_excluded > 0, na.rm = TRUE),
    common_endpoint_increases = sum(change_pp[!is.na(change_pp_pair_excluded)] > 0)
  ), by = ownership_measure]
  check("Ownership changes for every retained fixed-endpoint comparison are identical",
        near(endpoints[!is.na(change_pp_pair_excluded), change_pp_pair_excluded],
             endpoints[!is.na(change_pp_pair_excluded), change_pp]) &&
          all(counts$pair_excluded_increases == counts$common_endpoint_increases))

  figure_sectors <- endpoints[ownership_measure == "black_economic_interest" & sector_original != "National" &
                                !is.na(change_pp_pair_excluded) & start_context_n >= 30L & end_context_n >= 30L,
                              sector_original]
  check("Ownership figure uses all four code groups with available endpoints and at least 30 contextual entries at each",
        setequal(figure_sectors, c("Construction", "Transport", "ICT", "Tourism")))
  setorder(primary, sector_original, reporting_year, ownership_measure)
  setorder(pairs, reporting_year, sector_original, ownership_measure)
  list(tables = list(
    bbbee_ownership_annual = primary,
    bbbee_ownership_change_and_sensitivity = endpoints,
    bbbee_ownership_anomaly_pairs = pairs,
    bbbee_ownership_annual_sensitivity = sensitivity,
    bbbee_ownership_sector_direction_sensitivity = counts
  ), figure_sectors = figure_sectors)
}

analyse_compliance <- function(inputs) {
  keys <- c("series_id", "reporting_year", "sector_original", "entity_size")
  levels <- inputs$bbbee_compliance_levels[series_id == "retro_2026" &
                                           reporting_year %in% 2016:2023 & entity_size == "All"]
  summary <- inputs$bbbee_compliance_summary[series_id == "retro_2026" &
                                              reporting_year %in% 2016:2023 & entity_size == "All"]
  require_key(levels, c(keys, "compliance_level"), "B-BBEE status levels")
  require_key(summary, keys, "B-BBEE Levels 1–4 summary")
  invalid <- summary[is.na(analytical_value), ..keys]
  check("The two excluded B-BBEE status distributions are exactly National 2018 and Financial Services 2016",
        nrow(invalid) == 2L && setequal(paste(invalid$sector_original, invalid$reporting_year),
                                       c("National 2018", "Financial Services 2016")) &&
          all(is.na(levels[invalid, on = keys]$calculated_pct)) &&
          nrow(levels[invalid, on = keys]) == 20L)
  excluded <- summary[invalid, on = keys]
  summary <- summary[!invalid, on = keys]
  levels <- levels[!invalid, on = keys]
  totals <- levels[compliance_level == "Grand Total", c(keys, "entity_count"), with = FALSE]
  setnames(totals, "entity_count", "total")
  levels <- levels[compliance_level != "Grand Total"]
  check("B-BBEE retained level distributions keep all nine published categories",
        nrow(summary) == 85L &&
          setequal(levels$compliance_level, c(paste("Level", 1:8), "Non-Compliant")) &&
          all(levels[, .N, by = keys]$N == 9L))
  known <- levels[!is.na(entity_count)]
  dashes <- levels[is.na(entity_count)]
  check("Valid level shares use the published status denominator and original dashes stay missing",
        all(known$valid_status_denominator > 0) &&
          near(known$calculated_pct, 100 * known$entity_count / known$valid_status_denominator, 0.000051) &&
          all(is.na(dashes$calculated_pct) & dashes$published_count_original == "-"))

  reconciled <- known[, .(sum_reported_counts = sum(entity_count)), by = keys][totals, on = keys]
  check("All retained B-BBEE distributions with recorded counts reconcile to the printed total",
        nrow(reconciled) == nrow(summary) && near(reconciled$sum_reported_counts, reconciled$total))
  top <- copy(levels[compliance_level %in% paste("Level", 1:4)])
  top[, inferred_zero := is.na(entity_count) & !is.na(published_pct) & published_pct == 0]
  top_counts <- top[, .(count_levels_1_to_4 = sum(fifelse(inferred_zero, 0, entity_count)),
                        any_inferred_zero = any(inferred_zero)), by = keys]
  validation <- top_counts[reconciled, on = keys][summary, on = keys]
  check("Levels 1–4 shares reproduce with zero inference confined to reconciled, published-zero dashes",
        near(validation$numerator, validation$count_levels_1_to_4) &&
          near(validation$denominator, validation$total) &&
          near(validation$analytical_value, 100 * validation$numerator / validation$denominator, 0.000051) &&
          identical(validation$any_inferred_zero, has_flag(validation$quality_flag, "inferred_zero_for_dash")))
  setorder(summary, sector_original, reporting_year)
  setorder(levels, sector_original, reporting_year, compliance_level)
  list(bbbee_compliance_levels_valid = levels, bbbee_compliance_levels_1_to_4 = summary,
       bbbee_compliance_exclusions = excluded)
}
