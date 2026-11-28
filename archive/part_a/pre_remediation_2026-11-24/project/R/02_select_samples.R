classify_event <- function(master, classifications, event_id, strict = FALSE, strict_labels = character()) {
  # data.table .. is unambiguous in j but not i across versions.
  target_event <- event_id
  cl <- classifications[classifications$event_id == target_event]
  keep <- c('instrument_id','nature_of_business_raw','mining_candidate','likely_non_company_security',
            'match_confidence','historical_security_name','historical_share_code','bulletin_month','preannouncement_availability_verified')
  z <- join_checked(master, cl[, ..keep], 'instrument_id')
  z[, classified := !is.na(nature_of_business_raw) & match_confidence == 'high_label_concordance']
  z[, group := 'unknown']
  z[classified == TRUE & mining_candidate == FALSE, group := 'non_mining']
  z[classified == TRUE & mining_candidate == TRUE, group := 'mining']
  if (strict) z[group == 'mining' & !(nature_of_business_raw %in% strict_labels), group := 'unknown']
  z
}
select_sample <- function(returns, inputs, event, cfg, strict = FALSE, remove_extreme = FALSE) {
  t0 <- match(as.Date(event$event_date), inputs$calendar$date)
  assert(length(t0)==1 && !is.na(t0), 'Invalid event session')
  est <- cfg$analysis$estimation
  range_tau <- range(c(est,unlist(cfg$analysis$windows)))
  d <- copy(returns[session >= t0+range_tau[1] & session <= t0+range_tau[2]])
  d[, tau := session - t0]
  d[, usable := is.finite(return) & is.finite(market_return)]
  if (isTRUE(cfg$analysis$positive_volume)) d[, usable := usable & has_positive_volume]
  if (remove_extreme) d[, usable := usable & !(extreme %in% TRUE)]
  pre <- d[tau >= est[1] & tau <= est[2]]
  stats <- pre[, .(historical_positive_closes=sum(is.finite(close_raw) & close_raw>0),
    paired_returns=sum(is.finite(return) & is.finite(market_return)),
    n_est=sum(usable), zero_fraction=if(sum(is.finite(return))>0) mean(return[is.finite(return)]==0) else NA_real_,
    positive_volume_fraction=mean(has_positive_volume),
    extreme_estimation=sum(extreme %in% TRUE)), by=instrument_id]
  sample <- join_checked(classify_event(inputs$master,inputs$classifications,as.character(event$event_id),strict,cfg$analysis$strict_mining_labels),stats,'instrument_id')
  for (nm in c('historical_positive_closes','paired_returns','n_est','extreme_estimation')) sample[is.na(get(nm)), (nm):=0L]
  sample[, exclusion := 'included']
  sample[historical_positive_closes == 0, exclusion := 'no_historical_positive_close']
  sample[exclusion == 'included' & n_est < cfg$analysis$min_estimation, exclusion := 'insufficient_estimation_returns']
  sample[exclusion == 'included' & (is.na(zero_fraction) | zero_fraction > cfg$analysis$max_zero_fraction), exclusion := 'excess_unchanged_closes']
  if (isTRUE(cfg$analysis$exclude_known_noncompany)) sample[exclusion == 'included' & likely_non_company_security %in% TRUE, exclusion := 'known_likely_noncompany']
  sample[, eligible := exclusion == 'included']
  sample[, event_id := as.character(event$event_id)]
  sample[, analysis_t0_date := as.Date(event$event_date)]
  list(sample=sample, data=d, t0=t0)
}
