validate_inputs <- function(cfg) {
  root <- cfg$paths$source
  required <- c('README.md','manifest.json','manifest.sha256','documentation/verify_package.py',
                'documentation/trading_calendar.csv', paste0('data/', c('prices_daily','instruments',
                'market_index','event_industry_classifications','instrument_metadata_2026-11-23'), '.parquet'))
  assert(all(file.exists(file.path(root, required))), 'Missing required source file')
  assert(file.exists(cfg$paths$events), 'Missing event register')
  verifier <- normalizePath(file.path(root, 'documentation/verify_package.py'))
  old <- getwd(); py <- python_command(cfg)
  if (!startsWith(py, '/')) py <- file.path(old, py)
  setwd(root)
  v <- tryCatch(system2(py,
                       shQuote(verifier), stdout = TRUE, stderr = TRUE), finally = setwd(old))
  assert(is.null(attr(v, 'status')), paste('Source package verification failed:', paste(v, collapse='\n')))
  write_md(v, file.path(cfg$paths$outputs,'diagnostics/package_verification.txt'))
  audit_path <- file.path(cfg$paths$outputs, 'diagnostics/source_contract.json')
  run_python(cfg, c('scripts/parquet_bridge.py', 'audit', root, audit_path))
  contract <- jsonlite::read_json(audit_path, simplifyVector = TRUE)
  schemas <- list(prices_daily = c(date='date32[day]',instrument_id='string',close_raw='double',volume='int64',diagnostic_price_return='double'),
                  market_index = c(date='date32[day]',index_id='string',close_raw='double'),
                  event_industry_classifications = c(event_id='string',instrument_id='string',event_date='date32[day]',mining_candidate='bool'))
  for (nm in names(schemas)) for (col in names(schemas[[nm]]))
    assert(identical(contract$tables[[nm]]$schema[[col]], unname(schemas[[nm]][col])), paste('Schema violation', nm, col))
  events <- fread(cfg$paths$events)
  required_e <- c('event_id','event_date','event_date_verified','first_public_disclosure_verified','time_zone')
  assert(all(required_e %in% names(events)), 'Event register schema violation')
  events[, event_date := as.Date(event_date)]
  assert_key(events, 'event_id')
  assert(!anyNA(events$event_date) && all(events$event_date_verified) && all(events$time_zone == 'Africa/Johannesburg'), 'Unverified/invalid event dates')
  review<-read_security_review(cfg)
  if(nrow(review)) assert(all(review$event_date==events$event_date[match(review$event_id,events$event_id)]),
    'Security-review event dates contradict the immutable register')
  if ('analysis_t0_date' %in% names(events)) assert(all(is.na(events$analysis_t0_date) | events$analysis_t0_date == ''),
       'Explicit analysis_t0_date present: reconcile with configurable timing before running')
  cal <- fread(file.path(root, 'documentation/trading_calendar.csv'))[, .(date = as.Date(date))]
  assert_key(cal, 'date'); setorder(cal, date); cal[, session := .I]
  assert(all(diff(cal$date) > 0) && !any(weekdays(cal$date) %in% c('Saturday','Sunday')), 'Invalid calendar')
  assert(all(range(cal$date) == as.Date(c('2016-01-04','2026-03-31'))), 'Unexpected calendar coverage')
  master <- read_pq(file.path(root,'data/instruments.parquet'), cfg, c('instrument_id','ticker','company_name','issuer_id','security_type'))
  cl <- read_pq(file.path(root,'data/event_industry_classifications.parquet'), cfg)
  assert_key(master,'instrument_id'); assert_key(cl,c('event_id','instrument_id'))
  assert(setequal(unique(cl$event_id), events$event_id), 'Event IDs contradict classifications')
  cd <- unique(cl[, .(event_id, classification_date = event_date)])
  audit <- merge(events, cd, by = 'event_id')
  assert(nrow(audit) == nrow(events) && all(audit$event_date == audit$classification_date), 'Contradictory classification dates')
  assert(all(cl$bulletin_month < cl$event_date) && !any(cl$is_retrospective), 'Historical classification leakage')
  audit[, analysis_t0_date := cal$date[match(event_date, cal$date)]]
  assert(!anyNA(audit$analysis_t0_date), 'Event not a calendar session: explicit mapping needed')
  audit[, date_reconciliation := 'register verified; source provisional flag superseded; release hour unverified']
  write_table(audit, 'event_register_audit', cfg, 'diagnostics')
  run_python(cfg, c('scripts/parquet_bridge.py','fingerprint',root,file.path(cfg$paths$outputs,'diagnostics/source_fingerprints_before.json')))
  write_md(c('# Input validation', '', paste(v, collapse='\n'), '',
    'All required schemas and unique keys validated. Event register agrees with classification dates.',
    'README version 1.2.0 supersedes processing_summary 1.0.0; source documents are preserved.',
    'Dates are officially verified in the research register; exact public release timestamps remain unverified.',
    'Classification reporting months precede events; their publication availability remains unverified.',
    'The supplied calendar is observed, not independently exchange-certified. Source contract and hashes are recorded.'),
    file.path(cfg$paths$outputs,'diagnostics/input_validation.md'))
  list(events = events, calendar = cal, master = master, classifications = cl, contract = contract)
}
