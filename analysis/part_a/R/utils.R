suppressPackageStartupMessages(library(data.table))
options(stringsAsFactors = FALSE)
data.table::setDTthreads(2)
assert <- function(ok, message) if (!isTRUE(ok)) stop(message, call. = FALSE)
log_message <- function(...) cat(format(Sys.time(), '%H:%M:%S'), ..., '\n')
or_default <- function(x, default) if (is.null(x)) default else x
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
  assert(cfg$bootstrap$alpha>0 && cfg$bootstrap$alpha<1,'Invalid inference alpha')
  assert(or_default(cfg$bootstrap$event_sd_multiplier,1)>0,'Invalid event SD multiplier')
  assert(or_default(cfg$bootstrap$inference_convention,'absolute_tail_inversion')=='absolute_tail_inversion',
    'Primary inference must use the registered absolute-tail inversion convention')
  assert(or_default(cfg$analysis$return_measure,'unit_consistent_price')=='unit_consistent_price',
    'Only unit-consistent price returns are approved; distributions are not silently included')
  headline_family(cfg)
  assert(cfg$analysis$primary_window %in% names(bounds), 'Unknown primary window')
  for (d in c(cfg$paths$derived, file.path(cfg$paths$outputs, c('diagnostics','tables','figures','reports'))))
    dir.create(d, recursive = TRUE, showWarnings = FALSE)
  cfg
}
headline_family <- function(cfg) {
  path<-or_default(cfg$paths$testing_family,'config/headline_hypotheses.csv')
  family<-fread(path)
  assert_key(family,c('event_id','window','group'))
  required<-c('mining_charter_2017','mining_charter_2018','ee_draft_2023','ee_final_2025','bbbee_draft_2026')
  assert(nrow(family)==5L && setequal(family$event_id,required) &&
    all(family$family_id=='part_a_five_events_v1') && all(family$window=='primary'),
    'The predesignated five-test family cannot be changed by execution selection')
  expected<-ifelse(grepl('^mining_charter',family$event_id),'mining_minus_non_mining','all')
  assert(all(family$group==expected),'Unexpected headline hypothesis')
  assert(identical(cfg$analysis$primary_window,'primary') &&
    identical(as.numeric(cfg$analysis$windows$primary),c(0,1)),
    'Registered headline hypotheses require the primary [0,+1] window')
  family
}
headline_indices <- function(inf,cfg) {
  f<-headline_family(cfg)
  key<-function(z) paste(z$event_id,z$window,z$group,sep='|')
  which(key(inf) %in% key(f))
}
adjust_headline_family <- function(inf,cfg) {
  inf<-copy(inf);f<-headline_family(cfg)
  assert_key(inf,c('event_id','window','group'))
  ids<-headline_indices(inf,cfg)
  inf[,holm_primary_p:=NA_real_]
  inf[ids,holm_primary_p:=p.adjust(p_value,'holm',n=nrow(f))]
  inf[,primary_family_id:=f$family_id[1]]
  inf
}
source_modules <- function() for (f in sort(list.files('R', pattern = '^[0-9].*\\.R$', full.names = TRUE))) source(f)
analysis_file_paths <- function(config_path='config/analysis.yml') unique(c(
  list.files('R',pattern='\\.R$',full.names=TRUE),list.files('scripts',pattern='\\.py$',full.names=TRUE),
  list.files('research',pattern='\\.csv$',full.names=TRUE),list.files('config',pattern='\\.(csv|yml)$',full.names=TRUE),
  config_path,'run_analysis.R'))
