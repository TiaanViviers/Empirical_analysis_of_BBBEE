headline <- function(r,label) {
  target<-if(grepl('^mining_charter',r$event$event_id)) 'mining_minus_non_mining' else 'all'
  z<-copy(r$inference[window==r$primary_window & group==target]);z[,specification:=label];z
}
placebo_positions <- function(anchor,inputs,cfg,n) {
  calendar<-inputs$calendar;policy<-match(inputs$events$event_date,calendar$date)
  seq_safe<-function(a,b) if(a<=b) seq.int(a,b) else integer()
  eligible<-function(candidates) {
    if(!length(candidates)) return(candidates)
    keep<-vapply(candidates,function(t) all(abs(t-policy)>cfg$robustness$placebo_event_buffer),TRUE)
    if(isTRUE(cfg$robustness$placebo_exclude_own_event_from_fit)) {
      est<-cfg$analysis$estimation
      keep<-keep & !(anchor>=candidates+est[1] & anchor<=candidates+est[2])
    }
    candidates[keep]
  }
  past<-eligible(seq_safe(max(2L-cfg$analysis$estimation[1],anchor-cfg$robustness$placebo_lookback_sessions),anchor-31L))
  future<-eligible(seq_safe(anchor+31L,min(nrow(calendar)-11L,anchor+cfg$robustness$placebo_lookahead_sessions)))
  set.seed(cfg$robustness$seed+anchor)
  shuffle<-function(x) if(length(x)) x[sample.int(length(x))] else integer()
  order_candidates<-c(shuffle(past),shuffle(future))
  chosen<-integer()
  for(t in order_candidates) {
    if(all(abs(t-chosen)>=cfg$robustness$placebo_min_spacing)) chosen<-c(chosen,t)
    if(length(chosen)>=n) break
  }
  sort(chosen)
}
run_robustness <- function(results,returns,inputs,cfg,smoke=FALSE) {
  all<-list();placebos<-list();errors<-list();design<-list()
  for(eid in names(results)) {
    base<-results[[eid]];event<-copy(base$event)
    all[[paste0(eid,'baseline')]]<-headline(base,'baseline')
    cases<-c('min_200','no_volume_screen','no_zero_restriction','market_adjusted',
      'drop_flagged_extremes','next_session','previous_session','strict_mining','balanced_plot_sample',
      'block_1','block_10','mineral_value_chain','event_no_volume_screen','null_active_dates',
      'event_sd_1p5','event_sd_2','donor_early','donor_late','exclude_unresolved_action_securities',
      'reviewed_industry_proxy','partial_verified_issuer','legacy_raw_price')
    if(eid=='mining_charter_2018') cases<-c(cases,'cabinet_2018_09_19','public_stimulus_2018_09_21','advisory_2018_09_26')
    if(!grepl('^mining_charter',eid)) cases<-setdiff(cases,c('strict_mining','mineral_value_chain','reviewed_industry_proxy'))
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
      if(label=='no_volume_screen') {alt$analysis$positive_volume<-FALSE;alt$analysis$event_positive_volume<-FALSE}
      if(label=='event_no_volume_screen') alt$analysis$event_positive_volume<-FALSE
      if(label=='null_active_dates') alt$bootstrap$null_positive_volume<-TRUE
      if(label=='event_sd_1p5') alt$bootstrap$event_sd_multiplier<-1.5
      if(label=='event_sd_2') alt$bootstrap$event_sd_multiplier<-2
      if(label %in% c('donor_early','donor_late')) {
        est<-cfg$analysis$estimation;mid<-floor(mean(est))
        alt$bootstrap$donor_window<-if(label=='donor_early') c(est[1],mid) else c(mid+1,est[2])
      }
      if(label=='legacy_raw_price') {
        rr<-copy(returns);rr[,`:=`(return=return_raw,extreme=abs(return_raw)>cfg$analysis$extreme_threshold)]
      }
      if(label=='exclude_unresolved_action_securities') {
        ledger<-read_corporate_actions(cfg)
        dates<-inputs$calendar$date[base$selected$t0+range(c(cfg$analysis$estimation,unlist(cfg$analysis$windows))) ]
        excluded<-ledger[requires_sensitivity %in% TRUE & effective_date>=dates[1] & effective_date<=dates[2],unique(instrument_id)]
        rr<-returns[!(instrument_id %in% excluded)]
      }
      if(label=='reviewed_industry_proxy') alt$analysis$exposure_definition<-'reviewed_industry_proxy'
      if(label=='partial_verified_issuer') alt$analysis$weighting<-'partial_verified_issuer'
      if(label=='no_zero_restriction') alt$analysis$max_zero_fraction<-1
      if(label=='next_session') ev[,event_date:=inputs$calendar$date[base$selected$t0+cfg$robustness$timing_shift]]
      if(label=='previous_session') ev[,event_date:=inputs$calendar$date[base$selected$t0-1L]]
      if(label=='cabinet_2018_09_19') ev[,event_date:=as.Date(cfg$robustness$earlier_2018_date)]
      if(label=='public_stimulus_2018_09_21') ev[,event_date:=as.Date(cfg$robustness$timing_2018$public_stimulus_approval)]
      if(label=='advisory_2018_09_26') ev[,event_date:=as.Date(cfg$robustness$timing_2018$ministerial_advisory)]
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
    chosen<-placebo_positions(anchor,inputs,cfg,n)
    design[[eid]]<-data.table(event_id=eid,target=n,selected=length(chosen),shortfall=n-length(chosen),
      own_event_excluded_from_fit=isTRUE(cfg$robustness$placebo_exclude_own_event_from_fit),
      classification_status='frozen event snapshot; historical pseudo-date availability not verified')
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
  write_table(rbindlist(design),'placebo_design_summary',cfg,'diagnostics')
  write_table(summary,'robustness_summary',cfg);write_table(p,'placebo_results',cfg)
  if(nrow(failures)) write_table(failures,'robustness_failures',cfg,'diagnostics')
  write_md(c('# Robustness findings','',
    'Estimation threshold, volume screen, unchanged-price threshold, normal-return model, extreme-return exclusion, timing, mining definition, balanced event sample and block length are varied one at a time.',
    'Full extreme-return exclusion removes flagged analytical returns from fitting, event windows AND bootstrap donors. It is deliberately severe and diagnostic, not evidence that every >30% move is erroneous.',
    'Strict mining drops Aluminium/Aluminum from the mining group and leaves those securities unknown, rather than moving them into controls.',
    'Primary-window sensitivities below use full re-estimation and their own complete-window samples.',
    'Placebos refit market models using their own past; they are not resampled in-sample CARs. Dates are seeded, spaced >=22 sessions and exclude ±30 sessions around registered events.',
    'Only the five registered policy events are excluded; unrelated news is not exhaustively screened.',
    'Pseudo-events use the original event classification snapshot, potentially retrospective. They assess portfolio behaviour, not valid historical regulatory assignment.',
    'Pseudo-event fitting windows exclude the real event being studied. Shortfalls are reported rather than filling the sample with contaminated dates. Other news and frozen exposures still limit inference.',
    'Partial issuer weighting combines only the verified Fortress A/B link; every unlinked security stays separate. It is not full issuer-universe verification.',
    'Event SD multipliers and early/late donor windows are uncertainty scenarios, not estimated event-volatility corrections. Legacy raw-price results are a measurement comparison, not preferred economic returns.',
    '',md_table(summary[,.(event_id,specification,estimate,ci_lower,ci_upper,p_value,n,status)])),
    file.path(cfg$paths$outputs,'reports/robustness_findings.md'))
  list(summary=summary,placebos=p,failures=failures,status=if(smoke)'reduced smoke checks' else 'full configured checks')
}
