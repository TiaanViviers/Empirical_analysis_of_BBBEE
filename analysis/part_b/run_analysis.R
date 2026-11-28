#!/usr/bin/env Rscript
file_arg <- grep("^--file=", commandArgs(FALSE), value = TRUE)
script <- normalizePath(sub("^--file=", "", file_arg), mustWork = TRUE)
setwd(file.path(dirname(script), "..", ".."))
Sys.setenv(TZ = "Africa/Johannesburg")

suppressPackageStartupMessages({
  library(data.table)
  library(ggplot2)
})

for (module in c("common", "management", "ownership", "targets_employment", "figures", "report")) {
  source(file.path("analysis", "part_b", "R", paste0(module, ".R")))
}

input_names <- c(
  "cee_management_representation", "cee_management_representation_raw",
  "cee_reporting_coverage", "cee_eap_benchmarks", "cee_sector_crosswalk",
  "bbbee_ownership", "bbbee_compliance_levels", "bbbee_compliance_summary",
  "ee_sector_targets", "ee_gazette_workforce_baseline_2022", "ee_sector_reference",
  "statssa_sector_employment"
)
input_paths <- file.path("data", "part_b", "processed", paste0(input_names, ".csv"))
input_hashes <- tools::md5sum(input_paths)
check("All reviewed analysis inputs exist", !anyNA(input_hashes))
check("Cairo graphics is available for vector PDF export", capabilities("cairo"))
inputs <- setNames(lapply(input_paths, fread, na.strings = c("", "NA")), input_names)

message("Checking CEE management, sector mappings and EAP")
management <- analyse_management(inputs)
message("Checking B-BBEE ownership, anomaly sensitivity and level distributions")
ownership <- analyse_ownership(inputs)
compliance <- analyse_compliance(inputs)
message("Checking EE gazette pairings, CEE proxy and QLFS context")
targets <- analyse_targets(inputs, management)
employment <- analyse_employment(inputs)

tables <- c(management$tables, ownership$tables, compliance, targets, employment)
figures <- build_figures(tables, ownership$figure_sectors)
report <- build_report(tables, ownership$figure_sectors)
check("Processed inputs unchanged during analysis", identical(input_hashes, tools::md5sum(input_paths)))

output <- file.path("outputs", "part_b")
for (folder in c("tables", "figures", "reports", "diagnostics")) {
  dir.create(file.path(output, folder), recursive = TRUE, showWarnings = FALSE)
}
for (name in names(tables)) {
  fwrite(tables[[name]], file.path(output, "tables", paste0(name, ".csv")), na = "NA")
}
for (name in names(figures)) {
  save_figure(figures[[name]], file.path(output, "figures", name))
}
writeLines(report, file.path(output, "reports", "part_b_preliminary_results.md"))
fwrite(rbindlist(check_log), file.path(output, "diagnostics", "validation_checks.csv"))
fwrite(data.table(input = input_paths, md5 = unname(input_hashes)),
       file.path(output, "diagnostics", "input_fingerprints.csv"))
writeLines(capture.output(sessionInfo()), file.path(output, "diagnostics", "session_info.txt"))
message(sprintf("Part B complete. %d checks passed. Outputs in %s.", length(check_log), output))
