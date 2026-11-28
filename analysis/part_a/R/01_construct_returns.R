# Rows can be sparse, but the lag must have the immediately preceding calendar ID.
compute_returns <- function(x, calendar, id = 'instrument_id') {
  x <- copy(x); assert_key(x, c(id, 'date'))
  x[, session := match(date, calendar$date)]
  assert(!anyNA(x$session), 'Observation outside supplied calendar')
  setorderv(x, c(id, 'session'))
  x[, `:=`(lag_close = shift(close_raw), lag_session = shift(session)), by = id]
  x[, valid_pair := is.finite(close_raw) & close_raw > 0 & is.finite(lag_close) &
       lag_close > 0 & !is.na(lag_session) & session == lag_session + 1L]
  x[, return := NA_real_]
  x[valid_pair == TRUE, return := close_raw / lag_close - 1]
  x[, unchanged := fifelse(valid_pair, close_raw == lag_close, NA)]
  x[, c('lag_close','lag_session') := NULL]
  x
}
construct_returns <- function(cfg, inputs) {
  cols <- c('instrument_id','date','close_raw','volume','diagnostic_price_return',
            'is_missing_price','is_zero_price','invalid_price','is_zero_volume','is_missing_volume',
            'has_positive_volume','potential_stale_price','is_empty_placeholder')
  prices <- read_pq(file.path(cfg$paths$source,'data/prices_daily.parquet'), cfg, cols)
  returns <- compute_returns(prices, inputs$calendar)
  ref <- returns$diagnostic_price_return; own <- returns$return
  mismatches <- sum(xor(is.na(ref),is.na(own))) + sum(abs(ref-own) > 1e-12, na.rm=TRUE)
  assert(mismatches == 0, 'Independent return calculation disagrees with stored diagnostics')
  returns[, extreme := abs(return) > cfg$analysis$extreme_threshold]
  market <- read_pq(file.path(cfg$paths$source,'data/market_index.parquet'), cfg, c('index_id','date','close_raw'))
  assert(uniqueN(market$index_id) == 1 && unique(market$index_id) == 'J203:XJSE:IND', 'Wrong benchmark')
  market <- compute_returns(market, inputs$calendar, 'index_id')
  market <- merge(inputs$calendar, market[, .(date,market_return = return,market_close = close_raw)], by='date', all.x=TRUE)
  assert(all(is.na(market[date %in% as.Date(c('2024-01-02','2024-01-03')), market_return])), 'Benchmark gap bridged')
  for (i in seq_len(nrow(inputs$events))) {
    t0 <- match(inputs$events$event_date[i], inputs$calendar$date)
    required <- c(seq(cfg$analysis$estimation[1], cfg$analysis$estimation[2]), unlist(lapply(cfg$analysis$windows,function(w)seq(w[1],w[2])))) + t0
    assert(all(required >= 2 & required <= nrow(market)) && all(is.finite(market$market_return[required])), 'Incomplete benchmark event coverage')
  }
  returns <- join_checked(returns, market[, .(date, market_return)], 'date')
  quality <- returns[, .(rows=.N, valid_returns=sum(is.finite(return)), missing_close=sum(is_missing_price),
    zero_close=sum(is_zero_price), invalid_close=sum(invalid_price), zero_volume=sum(is_zero_volume),
    missing_volume=sum(is_missing_volume), unchanged=sum(unchanged,na.rm=TRUE), stale=sum(potential_stale_price),
    extreme=sum(extreme,na.rm=TRUE)), by=.(year=format(date,'%Y'))]
  write_table(quality,'return_quality_summary',cfg,'diagnostics')
  write_table(returns[extreme==TRUE, .(instrument_id,date,close_raw,return,volume,potential_stale_price)],'extreme_return_audit',cfg,'diagnostics')
  write_md(c('# Return validation','',paste('Compared', sum(is.finite(own)), 'computed returns; discrepancies:',mismatches),
    'Formula: current / previous - 1; finite positive endpoints and adjacent supplied-calendar sessions required.',
    'Raw source diagnostic returns are reconciled before any analytical conversion correction. No filling or clipping.',
    'Analytical returns correct only verified security-unit conversions in the versioned ledger; see corporate_action_application.csv.',
    'These are unit-consistent price returns, not dividend-reinvested total shareholder returns. Cash actions with unresolved units are not applied.',
    '2024-01-02 is missing in J203; both 2 and 3 January returns are NA.',
    'Full placeholder panel used for calculation; only non-placeholder rows stored in derived returns.',
    'Missing derived rows never imply zero returns; session IDs retain adjacency semantics.'),
    file.path(cfg$paths$outputs,'diagnostics/return_validation.md'))
  adjusted<-apply_corporate_actions(returns[is_empty_placeholder==FALSE],read_corporate_actions(cfg),
    enabled=or_default(cfg$analysis$apply_verified_conversions,TRUE),extreme_threshold=cfg$analysis$extreme_threshold)
  compact<-adjusted$returns
  write_table(adjusted$audit,'corporate_action_application',cfg,'diagnostics')
  write_pq(compact,'returns_daily',cfg); write_pq(market,'market_returns',cfg)
  list(returns=compact,market=market)
}
