check_log <- list()

check <- function(description, passed) {
  if (!isTRUE(passed)) stop(description, call. = FALSE)
  check_log[[length(check_log) + 1L]] <<- data.table(check = description, status = "pass")
}

require_key <- function(data, columns, label) {
  check(paste(label, "has complete and unique keys"),
        !anyNA(data[, ..columns]) && !anyDuplicated(data, by = columns))
}

require_grid <- function(data, label, ...) {
  expected <- do.call(CJ, c(list(...), list(sorted = FALSE)))
  columns <- names(expected)
  require_key(data, columns, label)
  check(paste(label, "has the expected coverage"),
        fsetequal(expected, data[, ..columns]))
}

near <- function(a, b, tolerance = 1e-8) {
  length(a) == length(b) && !anyNA(a) && !anyNA(b) && all(abs(a - b) <= tolerance)
}

is_pct <- function(x) all(is.finite(x) & x >= 0 & x <= 100)

has_flag <- function(x, flag) !is.na(x) & grepl(flag, x, fixed = TRUE)

cee_levels <- c("Top management", "Senior management")
ee_levels <- c("top_management", "senior_management")
ee_genders <- c("male", "female", "total")
black_groups <- c("African", "Coloured", "Indian")

sector_labels <- c(
  accommodation_food = "Accommodation and food", administrative_support = "Administrative and support",
  agriculture = "Agriculture, forestry and fishing", arts_recreation = "Arts, entertainment and recreation",
  construction = "Construction", education = "Education", electricity_gas = "Electricity and gas",
  financial_insurance = "Finance and insurance", health_social_work = "Health and social work",
  information_communication = "Information and communication", manufacturing = "Manufacturing",
  mining = "Mining and quarrying", professional_technical = "Professional, scientific and technical",
  public_administration = "Public administration and defence", real_estate = "Real estate",
  transport_storage = "Transport and storage", water_waste = "Water and waste",
  trade_repair = "Wholesale, retail and vehicle repair"
)

percentage_change <- function(data, keys, start_year, end_year) {
  start <- data[reporting_year == start_year, c(keys, "share_pct"), with = FALSE]
  end <- data[reporting_year == end_year, c(keys, "share_pct"), with = FALSE]
  setnames(start, "share_pct", "start_pct")
  setnames(end, "share_pct", "end_pct")
  result <- merge(start, end, by = keys, all = TRUE)
  result[, `:=`(start_year = start_year, end_year = end_year, change_pp = end_pct - start_pct)]
  result[]
}
