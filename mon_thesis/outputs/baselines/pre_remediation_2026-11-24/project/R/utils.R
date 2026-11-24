suppressPackageStartupMessages(library(data.table))
options(stringsAsFactors = FALSE)
data.table::setDTthreads(2)
assert <- function(ok, message) if (!isTRUE(ok)) stop(message, call. = FALSE)
log_message <- function(...) cat(format(Sys.time(), '%H:%M:%S'), ..., '\n')
assert_key <- function(x, key) {
  assert(all(key %in% names(x)), paste('Missing key', paste(key, collapse = ',')))
  assert(!anyNA(x[, ..key]), 'Null primary key')
  assert(!anyDuplicated(x, by = key), paste('Duplicate key', paste(key, collapse = ',')))
  invisible(TRUE)
}
join_checked <- function(x, y, by) {
  assert_key(y, by)
  n <- nrow(x)
  z <- merge(x, y, by = by, all.x = TRUE, sort = FALSE)
  assert(nrow(z) == n, 'Join multiplied rows')
  z
}
python_command <- function(cfg) {
  candidates <- c(Sys.getenv('PART_A_PYTHON'), cfg$paths$python, Sys.which('python3'))
  candidates <- candidates[nzchar(candidates) & file.exists(candidates)]
  assert(length(candidates) > 0L, 'Python with PyArrow required; set PART_A_PYTHON')
  candidates[1]
}
run_python <- function(cfg, args, stdout = "") {
  status <- system2(python_command(cfg), vapply(args, shQuote, ''), stdout = stdout, stderr = '')
  assert(identical(status, 0L), paste('Python command failed:', paste(args, collapse = ' ')))
}
read_pq <- function(path, cfg, columns = NULL) {
  tmp <- tempfile(fileext = '.csv'); on.exit(unlink(tmp))
  args <- c('scripts/parquet_bridge.py', 'read', path, tmp)
  if (!is.null(columns)) args <- c(args, '--columns', paste(columns, collapse = ','))
  run_python(cfg, args)
  z <- fread(tmp, na.strings = c('', 'NA'), showProgress = FALSE)
  for (nm in names(z)) if (nm == 'date' || endsWith(nm, '_date') || nm == 'bulletin_month') {
    if (!inherits(z[[nm]], 'POSIXct')) set(z, j = nm, value = as.Date(z[[nm]]))
  }
  z
}
write_pq <- function(x, name, cfg) {
  path <- file.path(cfg$paths$derived, paste0(name, '.parquet'))
  tmp <- tempfile(fileext = '.csv'); on.exit(unlink(tmp))
  fwrite(x, tmp, na = '', logical01 = FALSE)
  run_python(cfg, c('scripts/parquet_bridge.py', 'write', tmp, path))
}
write_table <- function(x, name, cfg, directory = 'tables') {
  path <- file.path(cfg$paths$outputs, directory, paste0(name, '.csv'))
  fwrite(x, path, na = '', logical01 = FALSE)
  invisible(path)
}
write_md <- function(lines, path) writeLines(lines, path, useBytes = TRUE)
md_table <- function(x, digits = 5) {
  x <- as.data.frame(x)
  if (!nrow(x)) return('No supported estimates.')
  for (nm in names(x)) {
    if (is.numeric(x[[nm]])) x[[nm]] <- format(round(x[[nm]], digits), trim = TRUE)
    x[[nm]][is.na(x[[nm]])] <- ''
    x[[nm]] <- gsub('|', '/', as.character(x[[nm]]), fixed = TRUE)
  }
  c(paste0('| ', paste(names(x), collapse = ' | '), ' |'),
    paste0('| ', paste(rep('---', ncol(x)), collapse = ' | '), ' |'),
    apply(x, 1, function(r) paste0('| ', paste(r, collapse = ' | '), ' |')))
}
load_config <- function(path = 'config/analysis.yml') {
  cfg <- yaml::read_yaml(path)
  est <- cfg$analysis$estimation
  bounds <- cfg$analysis$windows
  assert(length(est)==2 && all(is.finite(est)) && est[1] <= est[2], 'Invalid estimation window')
  assert(all(vapply(bounds,function(w)length(w)==2 && all(is.finite(w)) && w[1]<=w[2],logical(1))), 'Invalid event windows')
  assert(est[2] < min(unlist(bounds)), 'Estimation window overlaps event period')
  assert(cfg$analysis$min_estimation>=3 && cfg$analysis$min_estimation<=diff(est)+1,'Invalid estimation threshold')
  assert(cfg$analysis$max_zero_fraction>=0 && cfg$analysis$max_zero_fraction<=1,'Invalid unchanged-return limit')
  assert(cfg$bootstrap$replications>=99 && cfg$bootstrap$block_length>=1 && cfg$bootstrap$min_null_dates>=3,'Invalid bootstrap settings')
  assert(cfg$analysis$primary_window %in% names(bounds), 'Unknown primary window')
  for (d in c(cfg$paths$derived, file.path(cfg$paths$outputs, c('diagnostics','tables','figures','reports'))))
    dir.create(d, recursive = TRUE, showWarnings = FALSE)
  cfg
}
source_modules <- function() for (f in sort(list.files('R', pattern = '^[0-9].*\\.R$', full.names = TRUE))) source(f)
