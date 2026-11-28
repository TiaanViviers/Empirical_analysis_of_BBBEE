primary_daily_decomposition <- function(r,cfg) {
  cc<-r$cars[window==cfg$analysis$primary_window]
  bounds<-cfg$analysis$windows[[cfg$analysis$primary_window]]
  groups<-if(grepl('^mining_charter',r$event$event_id)) c('all','mining','non_mining','mining_minus_non_mining') else 'all'
  rbindlist(lapply(groups,function(g) {
    p<-portfolio_definition(cc,g,r$selected$sample,or_default(cfg$analysis$weighting,'equal_security'))
    if(!length(p$ids)) return(NULL)
    d<-copy(r$ar[instrument_id %in% p$ids & tau>=bounds[1] & tau<=bounds[2]])
    d[,weight:=p$weights[match(instrument_id,p$ids)]]
    if(!'return_raw' %in% names(d)) d[,return_raw:=return]
    d[,.(n=.N,raw_quote_return=sum(weight*return_raw),analytical_price_return=sum(weight*return),
      predicted_return=sum(weight*expected),abnormal_return=sum(weight*ar)),
      by=.(event_id,date,tau,market_return)][,portfolio:=g]
  }),fill=TRUE)
}

fixed_sample_timing <- function(r,inputs,cfg) {
  dates<-as.Date(c(unlist(cfg$robustness$timing_2018),as.character(r$event$event_date)))
  dates<-sort(unique(dates));bounds<-cfg$analysis$windows[[cfg$analysis$primary_window]]
  cars<-lapply(dates,function(date) {
    shift<-match(as.Date(date,origin='1970-01-01'),inputs$calendar$date)-r$selected$t0
    d<-copy(r$ar);d[,tau:=tau-shift]
    complete_cars(d,bounds[1],bounds[2])
  })
  common<-Reduce(intersect,lapply(cars,function(z) z[complete==TRUE & group %in% c('mining','non_mining'),instrument_id]))
  rbindlist(lapply(seq_along(dates),function(k) {
    cc<-cars[[k]][instrument_id %in% common]
    p<-portfolio_definition(cc,'mining_minus_non_mining',r$selected$sample)
    start<-match(dates[k],inputs$calendar$date)
    data.table(event_id=r$event$event_id,anchor_date=dates[k],
      last_return_date=inputs$calendar$date[start+bounds[2]],n_mining=length(p$mining),n_control=length(p$controls),
      estimate=sum(cc$car[match(p$ids,cc$instrument_id)]*p$weights),
      method='point estimates only; common constituents and baseline OLS coefficients frozen')
  }))
}

write_research_diagnostics <- function(results,robust,inputs,data,cfg) {
  daily<-rbindlist(lapply(results,primary_daily_decomposition,cfg=cfg),fill=TRUE)
  write_table(daily,'primary_daily_decomposition',cfg)
  if('bbbee_draft_2026' %in% names(results)) {
    display<-daily[event_id=='bbbee_draft_2026' & portfolio=='all']
    display<-melt(display,id.vars=c('date','n'),measure.vars=c('market_return','analytical_price_return',
      'predicted_return','abnormal_return'),variable.name='series',value.name='daily_return')
    display[,series:=factor(series,levels=c('market_return','analytical_price_return','predicted_return','abnormal_return'),
      labels=c('J203','Actual portfolio','Fitted normal return','Abnormal return'))]
    p<-ggplot2::ggplot(display,ggplot2::aes(series,100*daily_return,fill=series))+
      ggplot2::geom_hline(yintercept=0,colour='grey60')+ggplot2::geom_col(width=.65)+
      ggplot2::facet_wrap(~date)+ggplot2::scale_fill_manual(values=c('#777777','#007D8A','#9467BD','#B55025'))+
      ggplot2::labs(x=NULL,y='Daily price return (%)',title='2026: actual, predicted and abnormal performance',
        subtitle=paste('Same fixed primary portfolio;',unique(display$n),'securities'),
        caption='Abnormal return is actual minus fitted normal return. Positive relative performance need not mean a price gain.')+
      ggplot2::theme_minimal(base_size=11)+ggplot2::theme(legend.position='none',axis.text.x=ggplot2::element_text(angle=20,hjust=1))
    for(ext in c('png','pdf')) ggplot2::ggsave(file.path(cfg$paths$outputs,'figures',paste0('daily_decomposition_2026.',ext)),p,width=10,height=5,dpi=300)
  }
  contributions<-rbindlist(lapply(results,function(r) {
    cc<-copy(r$cars[window==cfg$analysis$primary_window & complete==TRUE])
    cc<-join_checked(cc,r$selected$sample[,.(instrument_id,company_name,nature_of_business_raw,reviewed_issuer_id)],'instrument_id')
    cc[,contribution_to_all_caar:=car*security_weights(instrument_id,r$selected$sample,or_default(cfg$analysis$weighting,'equal_security'))]
    cc
  }),fill=TRUE)
  write_table(contributions,'primary_security_contributions',cfg)
  sectors<-contributions[,.(n=.N,mean_car=mean(car),contribution_to_all_caar=sum(contribution_to_all_caar)),
    by=.(event_id,nature_of_business_raw)]
  write_table(sectors,'primary_industry_contributions',cfg)
  write_table(contributions[,.(n=.N,mean_car=mean(car),contribution_to_all_caar=sum(contribution_to_all_caar)),
    by=.(event_id,group)],'primary_group_contributions',cfg)
  for(r in results) {
    h<-headline(r,'baseline')
    observed<-daily[event_id==r$event$event_id & portfolio==h$group,sum(abnormal_return)]
    assert(abs(observed-h$estimate)<1e-12,'Daily decomposition does not reconcile to headline')
  }
  chron<-fread(cfg$paths$chronology);news<-fread(cfg$paths$news)
  write_table(chron,'event_information_chronology',cfg,'diagnostics')
  write_table(news,'contemporaneous_news',cfg,'diagnostics')
  review<-read_security_review(cfg)
  write_table(review,'security_exposure_review',cfg,'diagnostics')
  if('mining_charter_2018' %in% names(results))
    write_table(fixed_sample_timing(results$mining_charter_2018,inputs,cfg),'fixed_sample_2018_timing',cfg)
  timing_labels<-c('baseline','cabinet_2018_09_19','public_stimulus_2018_09_21','advisory_2018_09_26','previous_session','next_session')
  if(nrow(robust$summary)) write_table(robust$summary[specification %in% timing_labels],
    'timing_comparisons',cfg)

  vol<-rbindlist(lapply(results,function(r) {
    h<-headline(r,'baseline');cc<-r$cars[window==cfg$analysis$primary_window]
    p<-portfolio_definition(cc,h$group,r$selected$sample,or_default(cfg$analysis$weighting,'equal_security'))
    pre<-r$ar[instrument_id %in% p$ids & tau>=cfg$analysis$estimation[1] & tau<=cfg$analysis$estimation[2]]
    panel<-residual_donor_panel(pre,p$ids,cfg)
    z<-as.vector(panel$E%*%p$weights)
    ev<-daily[event_id==r$event$event_id & portfolio==h$group]
    middle<-median(panel$tau)
    data.table(event_id=r$event$event_id,null_dates=length(z),pre_daily_residual_sd=sd(z),
      pre_early_sd=sd(z[panel$tau<=middle]),pre_late_sd=sd(z[panel$tau>middle]),
      event_max_absolute_aar=max(abs(ev$abnormal_return)),
      event_max_aar_over_pre_sd=max(abs(ev$abnormal_return))/sd(z),
      event_market_max_abs=max(abs(ev$market_return)),
      caveat='two event days do not identify an event variance; these are descriptive diagnostics')
  }))
  write_table(vol,'event_volatility_diagnostics',cfg,'diagnostics')
  benchmark<-data.table(index_id='J203:XJSE:IND',preferred_equity_return='security-unit-consistent price return',
    reference_evidence='JSE identifies J203 All Share and separately J203T All Share Total Return',
    j203_url='https://www.jse.co.za/all-share-j203',j203t_url='https://www.jse.co.za/jse/instruments/3416',
    provider_series_status='IRESS export return variant and adjustment convention not independently certified',
    cash_distributions='not added in price-only baseline; verified/unresolved actions and exclusions reported separately',
    overall_status='price-index-compatible intent; provider-level match remains partial')
  write_table(benchmark,'benchmark_convention_audit',cfg,'diagnostics')

  baseline<-cfg$paths$comparison_baseline
  current<-fread(file.path(cfg$paths$outputs,'tables/headline_results_percent.csv'))
  if(!is.null(baseline) && file.exists(file.path(baseline,'tables/headline_results_percent.csv'))) {
    old<-fread(file.path(baseline,'tables/headline_results_percent.csv'))
    compare<-merge(old,current,by=c('event_id','window'),all=FALSE,suffixes=c('_before','_after'))
    compare[,estimate_change_pp:=headline_estimate_pct_after-headline_estimate_pct_before]
    compare[,`:=`(before_interval='equal-tailed basic bootstrap',after_interval='absolute-tail test inversion')]
    write_table(compare,'headline_before_after',cfg)
    oldmodels_path<-file.path(baseline,'derived/market_model_estimates.parquet')
    if(file.exists(oldmodels_path)) {
      oldmodels<-read_pq(oldmodels_path,cfg)
      newmodels<-rbindlist(lapply(results,`[[`,'models'))
      changes<-merge(oldmodels,newmodels,by=c('event_id','instrument_id'),suffixes=c('_before','_after'))
      write_table(changes[abs(alpha_after-alpha_before)>1e-12 | abs(beta_after-beta_before)>1e-12],
        'changed_market_models',cfg,'diagnostics')
    }
  }
  write_md(c('# Information timing and market conditions','',
    'Registered official publication dates remain the baseline. Earlier dates are distinct information events, never selected by significance.',
    'The 2017 [0,+1] sessions are 15 and 19 June. The 2018 21 September window ends 25 September after the holiday/weekend.',
    'The 2018 baseline measures incremental gazette-window relative performance, not the complete information sequence. Approval was public by the presidential stimulus statement of 21 September.',
    'The 2023 diplomatic episode, 2025 tariff-related outlook news and 2026 monetary/global-market developments prevent isolated causal attribution. Dated overlap alone does not establish an intraday causal effect.',
    '',md_table(chron),'',md_table(news),'',
    'Daily raw, unit-consistent, predicted and abnormal returns are in primary_daily_decomposition.csv. Industry/security contributions use the fixed complete [0,+1] all-security portfolio.',
    '',md_table(daily[event_id=='bbbee_draft_2026'])),
    file.path(cfg$paths$outputs,'reports/information_and_market_conditions.md'))
}
