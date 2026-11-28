thesis_theme <- function(base_size = 11) {
  theme_minimal(base_size = base_size, base_family = "sans") +
    theme(
      plot.title.position = "plot", plot.caption.position = "plot",
      plot.title = element_text(size = 15, face = "bold", colour = "#172C3B", margin = margin(b = 5)),
      plot.subtitle = element_text(size = 10, colour = "#344B5A", margin = margin(b = 12)),
      plot.caption = element_text(hjust = 0, size = 8.5, colour = "#344B5A", lineheight = 1.2,
                                  margin = margin(t = 11)),
      axis.title = element_text(colour = "#172C3B"),
      axis.text = element_text(colour = "#344B5A"),
      strip.text = element_text(face = "bold", hjust = 0, colour = "#172C3B"),
      panel.grid.minor = element_blank(),
      panel.grid.major = element_line(colour = "#DCE3E8", linewidth = 0.32),
      panel.spacing = grid::unit(15, "pt"),
      legend.position = "bottom", legend.title = element_blank(),
      legend.text = element_text(colour = "#172C3B"),
      plot.margin = margin(12, 14, 10, 14)
    )
}

management_figure <- function(national) {
  data <- management_long(national)
  require_grid(data, "Figure 1 CEE primary data", reporting_year = 2016:2024,
               occupational_level = cee_levels, indicator = c("Black", "Black female"))
  endpoint <- data[reporting_year == 2024]
  endpoint[, label := sprintf("%.1f%%", share_pct)]
  ggplot(data, aes(reporting_year, share_pct, colour = occupational_level)) +
    geom_line(aes(linetype = occupational_level), linewidth = 0.8) +
    geom_point(data = data[reporting_year > 2016], size = 1.7) +
    geom_point(data = data[reporting_year == 2016], shape = 21, fill = "white", size = 2.1,
               stroke = 0.75, show.legend = FALSE) +
    geom_text(data = endpoint, aes(label = label), nudge_x = 0.22, hjust = 0,
              size = 3.2, show.legend = FALSE) +
    facet_wrap(vars(indicator), nrow = 1) +
    scale_colour_manual(values = c("Top management" = "#AB4713", "Senior management" = "#00658D"),
                        breaks = cee_levels) +
    scale_linetype_manual(values = c("Top management" = "dashed", "Senior management" = "solid"),
                          breaks = cee_levels) +
    scale_x_continuous(breaks = seq(2016, 2024, 2), limits = c(2015.7, 2025.35)) +
    scale_y_continuous(breaks = seq(0, 60, 10), limits = c(0, 60), expand = expansion(mult = c(0, 0.02))) +
    labs(title = "Black representation in management rose from 2016 to 2024",
         subtitle = "National share of all managers at each occupational level",
         x = "Workforce reporting year", y = "Share of managers (%)",
         caption = paste(
           "Source is the Commission for Employment Equity, national workforce tables.",
           "Both shares use all managers at each level, including foreign nationals.",
           "Open markers denote 2016 retrospective counts. Reporting employers change over time.",
           sep = "\n"
         )) +
    thesis_theme() + theme(panel.grid.major.x = element_blank())
}

ownership_figure <- function(annual, sensitivity, code_groups) {
  data <- annual[(sector_original == "National" &
                    ownership_measure %in% c("black_economic_interest", "black_female_economic_interest")) |
                   (sector_original %in% code_groups & ownership_measure == "black_economic_interest")]
  require_grid(data[sector_original == "National"], "Figure 2 national economic-interest data",
               reporting_year = 2016:2023,
               ownership_measure = c("black_economic_interest", "black_female_economic_interest"))
  require_grid(data[sector_original != "National"], "Figure 2 selected code-group data",
               reporting_year = 2016:2023, sector_original = code_groups)
  data[, panel := factor(fifelse(sector_original == "National", "National", "Selected B-BBEE codes"),
                         levels = c("National", "Selected B-BBEE codes"))]
  data[, series := fcase(ownership_measure == "black_female_economic_interest", "Black female",
                        sector_original == "National", "Black", default = sector_original)]
  keys <- c("series_id", "reporting_year", "sector_original", "ownership_measure")
  data[sensitivity, on = keys, `:=`(flagged_pair = i.excluded_as_anomaly_pair,
                                    published_check = i.published_pct,
                                    line_pct = i.pair_excluded_pct)]
  check("Figure 2 shows the published ownership values and marks three affected code-group observations",
        !anyNA(data$flagged_pair) && sum(data$flagged_pair) == 3L &&
          near(data$ownership_pct, data$published_check))
  check("Figure 2 breaks the lines at flagged points while retaining every unflagged value",
        identical(is.na(data$line_pct), data$flagged_pair) &&
          near(data[flagged_pair == FALSE, line_pct], data[flagged_pair == FALSE, ownership_pct]) &&
          all(data[flagged_pair == TRUE, reporting_year] %in% 2017:2022))
  endpoint <- data[reporting_year == 2023]
  endpoint[, label := sprintf("%s\n%.1f%%", series, ownership_pct)]
  colours <- c(Black = "#00658D", "Black female" = "#AB4713", Construction = "#00658D",
               Transport = "#14745D", ICT = "#6E5492", Tourism = "#AB4713")
  lines <- c(Black = "solid", "Black female" = "dashed", Construction = "solid",
             Transport = "longdash", ICT = "dotdash", Tourism = "dashed")
  ggplot(data, aes(reporting_year, ownership_pct, colour = series, group = series)) +
    geom_line(aes(y = line_pct, linetype = series), linewidth = 0.75, na.rm = TRUE) +
    geom_point(data = data[flagged_pair == FALSE], size = 1.55) +
    geom_point(data = data[flagged_pair == TRUE], shape = 21, fill = "white", size = 2.05, stroke = 0.75) +
    geom_text(data = endpoint, aes(label = label), nudge_x = 0.24, hjust = 0,
              lineheight = 0.98, size = 3.05) +
    facet_wrap(vars(panel), nrow = 1) +
    scale_colour_manual(values = colours) +
    scale_linetype_manual(values = lines) +
    scale_x_continuous(breaks = c(2016, 2018, 2020, 2023), limits = c(2015.72, 2025.75),
                       expand = expansion(mult = c(0, 0))) +
    scale_y_continuous(breaks = seq(0, 60, 10), limits = c(0, 66), expand = expansion(mult = c(0, 0))) +
    labs(title = "Reported black economic interest was higher in 2023 than in 2016",
         subtitle = "Annual national and selected B-BBEE code averages from verification submissions",
         x = "Verification reporting year", y = "Reported economic interest (%)",
         caption = paste(
           "Source is the B-BBEE Commission, South Africa’s Transformation Landscape (2013–2023).",
           "The sample changes over time. Ownership-specific denominators and weighting are unpublished.",
           "Shown codes have both endpoints after exclusions and at least 30 sample entries at each.",
           "Open markers show published values from flagged female-overall pairs. Lines break at these years.",
           sep = "\n"
         )) +
    thesis_theme() + theme(legend.position = "none", panel.grid.major.x = element_blank())
}

shortfall_figure <- function(paired) {
  data <- copy(paired[gender == "total"])
  require_grid(data, "Figure 3 paired 2023 BLACK total target data", sector_id = names(sector_labels),
               occupational_level = ee_levels)
  check("Figure 3 plotted distances reproduce signed target-minus-baseline values",
        near(data$shortfall_pp, data$target_pct - data$observed_pct))
  order <- data[occupational_level == "top_management"][order(shortfall_pp, sector_label), sector_label]
  data[, sector := factor(sector_label, levels = order)]
  data[, level := factor(occupational_level, levels = ee_levels, labels = cee_levels)]
  ggplot(data, aes(shortfall_pp, sector, colour = level)) +
    geom_vline(xintercept = 0, colour = "#526571", linewidth = 0.45) +
    geom_segment(aes(x = 0, xend = shortfall_pp, yend = sector), linewidth = 0.6, alpha = 0.53) +
    geom_point(aes(shape = level), size = 2.35) +
    facet_wrap(vars(level), nrow = 1) +
    scale_colour_manual(values = c("Top management" = "#AB4713", "Senior management" = "#00658D")) +
    scale_shape_manual(values = c("Top management" = 17, "Senior management" = 16)) +
    scale_x_continuous(breaks = seq(0, 20, 5), expand = expansion(add = c(0.7, 1))) +
    labs(title = "Shortfalls against the proposed 2023 targets varied by sector",
         subtitle = "Proposed national BLACK target (both sexes) less the 2022 profile in the same gazette",
         x = "Target shortfall (percentage points)", y = NULL,
         caption = paste(
           "Source is Government Gazette 48589 (12 May 2023). BLACK comprises African, Coloured and Indian employees.",
           "Points show sector-level differences. Both panels use the top-management ordering.",
           sep = "\n"
         )) +
    thesis_theme() + theme(legend.position = "none", axis.text.y = element_text(size = 9.4))
}

build_figures <- function(tables, code_groups) {
  list(
    national_management_representation = list(plot = management_figure(tables$cee_national_management),
                                              width = 7.8, height = 4.55),
    reported_black_economic_interest = list(plot = ownership_figure(tables$bbbee_ownership_annual,
                                                                     tables$bbbee_ownership_annual_sensitivity,
                                                                     code_groups),
                                            width = 8.1, height = 4.55),
    draft_ee_target_shortfalls = list(plot = shortfall_figure(tables$ee_draft_2023_target_shortfalls),
                                      width = 8.6, height = 6.3)
  )
}

save_figure <- function(figure, path) {
  ggsave(paste0(path, ".png"), figure$plot, width = figure$width, height = figure$height,
         dpi = 300, bg = "white", device = "png")
  ggsave(paste0(path, ".pdf"), figure$plot, width = figure$width, height = figure$height,
         bg = "white", device = grDevices::cairo_pdf)
}
