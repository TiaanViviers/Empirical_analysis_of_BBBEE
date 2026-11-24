headline <- function(r,label) {
  target<-if(grepl('^mining_charter',r$event$event_id)) 'mining_minus_non_mining' else 'all'
  z<-copy(r$inference[window==r$primary_window & group==target]);z[,specification:=label];z
}
run_robustness <- function(results,returns,inputs,cfg,smoke=FALSE) {
  all<-list();placebos<-list();errors<-list()
  for(eid in names(results)) {
    base<-results[[eid]];event<-copy(base$event)
    all[[paste0(eid,'baseline')]]<-headline(base,'baseline')
    cases<-c('min_200','no_volume_screen','no_zero_restriction','market_adjusted',
      'drop_flagged_extremes','next_session','previous_session','strict_mining','balanced_plot_sample',
      'block_1','block_10','mineral_value_chain')
    if(eid=='mining_charter_2018') cases<-c(cases,'cabinet_2018_09_19')
    if(!grepl('^mining_charter',eid)) cases<-setdiff(cases,c('strict_mining','mineral_value_chain'))
    if(smoke) cases<-c('min_200','market_adjusted','next_session')
    for(label in cases) {
      log_message('Sensitivity',eid,label)
      alt<-cfg;alt$analysis$windows<-cfg$analysis$windows[cfg$analysis$primary_window]
      ev<-copy(event);rr<-returns;alt_inputs<-inputs
      if(label=='mineral_value_chain') {
        alt_inputs$classifications<-copy(inputs$classifications)
        alt_inputs$classifications[event_id==eid & nature_of_business_raw %in% cfg$robustness$broad_mineral_labels,mining_candidate:=TRUE]
      }
      if(label=='min_200') alt$analysis$min_estimation<-cfg$robustness$min_estimation
      if(label=='no_volume_screen') alt$analysis$positive_volume<-FALSE
      if(label=='no_zero_restriction') alt$analysis$max_zero_fraction<-1
      if(label=='next_session') ev[,event_date:=inputs$calendar$date[base$selected$t0+cfg$robustness$timing_shift]]
      if(label=='previous_session') ev[,event_date:=inputs$calendar$date[base$selected$t0-1L]]
      if(label=='cabinet_2018_09_19') ev[,event_date:=as.Date(cfg$robustness$earlier_2018_date)]
      if(label=='block_1') alt$bootstrap$block_length<-cfg$robustness$block_lengths[1]
      if(label=='block_10') alt$bootstrap$block_length<-cfg$robustness$block_lengths[2]
      if(label=='balanced_plot_sample') {
        ids<-base$cars[window=='plot' & complete==TRUE,instrument_id]
        rr<-rr[instrument_id %in% ids]
      }
      r<-tryCatch(analyse_event(rr,alt_inputs,ev,alt,
         normal_model=if(label=='market_adjusted') 'market_adjusted' else 'market_model',
         strict=label=='strict_mining',remove_extreme=label=='drop_flagged_extremes'),error=function(e)e)
      if(inherits(r,'error')) {
        errors[[paste(eid,label)]]<-data.table(event_id=eid,specification=label,status=conditionMessage(r))
      } else all[[paste(eid,label)]]<-headline(r,label)
    }
    # Actual out-of-sample pseudo-events: refit models and reselect samples using
    # ONLY each pseudo-event's past. Original event snapshot is a fixed descriptive
    # grouping and may be retrospective for these pseudo-dates, explicitly marked.
    n<-if(smoke) 2L else cfg$robustness$placebo_count
    anchor<-base$selected$t0
    candidates<-seq(max(252L,anchor-cfg$robustness$placebo_lookback_sessions),anchor-31L)
    policy_positions<-match(inputs$events$event_date,inputs$calendar$date)
    candidates<-candidates[vapply(candidates,function(t) all(abs(t-policy_positions)>cfg$robustness$placebo_event_buffer),logical(1))]
    set.seed(cfg$robustness$seed+anchor)
    order_candidates<-sample(candidates)
    chosen<-integer()
    for(t in order_candidates) {
      if(all(abs(t-chosen)>=cfg$robustness$placebo_min_spacing)) chosen<-c(chosen,t)
      if(length(chosen)>=n) break
    }
    # If the early 2017 horizon cannot supply ten spaced dates, extend forward
    # into pre-specified dates at least 31 sessions after the real event.
    if(length(chosen)<n) {
      future<-seq(anchor+31L,min(nrow(inputs$calendar)-11L,anchor+cfg$robustness$placebo_lookahead_sessions))
      future<-future[vapply(future,function(t) all(abs(t-policy_positions)>cfg$robustness$placebo_event_buffer),logical(1))]
      for(t in sample(future)) {
        if(all(abs(t-chosen)>=cfg$robustness$placebo_min_spacing)) chosen<-c(chosen,t)
        if(length(chosen)>=n) break
      }
    }
    for(t in sort(chosen)) {
      ev<-copy(event);ev[,event_date:=inputs$calendar$date[t]]
      log_message('Refitted placebo',eid,as.character(ev$event_date))
      placebo_cfg<-cfg;placebo_cfg$analysis$windows<-cfg$analysis$windows[cfg$analysis$primary_window]
      r<-tryCatch(analyse_event(returns,inputs,ev,placebo_cfg),error=function(e)e)
      key<-paste(eid,t)
      if(inherits(r,'error')) placebos[[key]]<-data.table(event_id=eid,placebo_date=ev$event_date,status=conditionMessage(r)) else {
        z<-headline(r,'refitted_pseudo_event');z[,placebo_date:=ev$event_date]
        z[,classification_caveat:='Original event snapshot frozen; not pseudo-date exposure evidence']
        placebos[[key]]<-z
      }
    }
  }
  summary<-rbindlist(all,fill=TRUE);p<-rbindlist(placebos,fill=TRUE);failures<-rbindlist(errors,fill=TRUE)
  write_table(summary,'robustness_summary',cfg);write_table(p,'placebo_results',cfg)
  if(nrow(failures)) write_table(failures,'robustness_failures',cfg,'diagnostics')
  write_md(c('# Robustness findings','',
    'Estimation threshold, volume screen, unchanged-price threshold, normal-return model, extreme-return exclusion, timing, mining definition, balanced event sample and block length are varied one at a time.',
    'Extreme-return exclusion is deliberately severe and diagnostic. It is not an assertion that every >30% move is a data error.',
    'Strict mining drops Aluminium/Aluminum from the mining group and leaves those securities unknown, rather than moving them into controls.',
    'Primary-window sensitivities below use full re-estimation and their own complete-window samples.',
    'Placebos refit market models using their own past; they are not resampled in-sample CARs. Dates are seeded, spaced >=22 sessions and exclude ±30 sessions around registered events.',
    'Only the five registered policy events are excluded; unrelated news is not exhaustively screened.',
    'Pseudo-events use the original event classification snapshot, potentially retrospective. They assess portfolio behaviour, not valid historical regulatory assignment.',
    'Some later pseudo-event estimation periods may contain the real event; their null calibration is exploratory.',
    'Verified issuer links are unavailable. No name-based consolidation or 2026-ISIN historical de-duplication was attempted.',
    '',md_table(summary[,.(event_id,specification,estimate,ci_lower,ci_upper,p_value,n,status)])),
    file.path(cfg$paths$outputs,'reports/robustness_findings.md'))
  list(summary=summary,placebos=p,failures=failures,status=if(smoke)'reduced smoke checks' else 'full configured checks')
}
