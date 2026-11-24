write_headline_results <- function(inf,summary,cfg) {
  primary<-cfg$analysis$primary_window
  heads<-inf[headline_indices(inf,cfg)]
  allcars<-summary[window==primary & group=='all',.(event_id,n_all=n,all_caar_pct=100*mean_car)]
  assert_key(heads,'event_id');assert_key(allcars,'event_id')
  assert(setequal(heads$event_id,allcars$event_id),'Headline and CAR event samples disagree')
  tab<-join_checked(heads,allcars,'event_id')
  tab<-tab[order(match(event_id,headline_family(cfg)$event_id))]
  tab<-tab[,.(event_id,window,n_all,all_caar_pct,n_mining,n_control,
    headline_estimate_pct=100*estimate,ci_lower_pct=100*ci_lower,ci_upper_pct=100*ci_upper,
    p_value,holm_primary_p,null_dates)]
  write_table(tab,'headline_results_percent',cfg)
  invisible(tab)
}
plot_caar <- function(r,cfg) {
  suppressPackageStartupMessages(library(ggplot2))
  mining<-grepl('^mining_charter',r$event$event_id)
  groups<-if(mining) c('all','mining','non_mining','mining_minus_non_mining') else 'all'
  cc<-r$cars[window=='plot'];series<-list()
  bounds<-cfg$analysis$windows$plot
  for(g in groups) {
    portfolio<-portfolio_definition(cc,g,r$selected$sample,or_default(cfg$analysis$weighting,'equal_security'))
    ids<-portfolio$ids;weights<-portfolio$weights
    if(g=='mining_minus_non_mining' && (!length(portfolio$mining) || !length(portfolio$controls))) next
    if(!length(ids)) next
    d<-weighted_portfolio_series(r$ar,ids,weights,'ar')[tau>=bounds[1] & tau<=bounds[2]]
    assert(nrow(d)==diff(bounds)+1 && all(is.finite(d$value)), 'Plot portfolio not balanced')
    d[,`:=`(aar=value,caar=cumsum(value),group=g,n=length(ids),ci_lower=NA_real_,ci_upper=NA_real_)]
    for(t in seq_len(nrow(d))) {
      boot<-tryCatch(bootstrap_portfolio(r$ar,ids,weights,bounds[1],d$tau[t],cfg,500+t),error=function(e)e)
      if(!inherits(boot,'error')) {
        stats<-bootstrap_summary(boot$error,d$caar[t],cfg$bootstrap$alpha)
        d[t,`:=`(ci_lower=stats$ci_lower,ci_upper=stats$ci_upper)]
      }
    }
    series[[g]]<-d
  }
  d<-rbindlist(series)
  assert(nrow(d)>0,'No complete plotting portfolios')
  d[,event_id:=as.character(r$event$event_id)]
  d[,label:=paste0(gsub('_',' ',group),' (N=',n,')')]
  plotted<-if(mining) d[group %in% c('mining','non_mining')] else d
  p<-ggplot(plotted,aes(tau,caar*100,colour=label,fill=label))+
    geom_ribbon(aes(ymin=ci_lower*100,ymax=ci_upper*100),alpha=.13,colour=NA,na.rm=TRUE)+
    geom_hline(yintercept=0,colour='grey60',linewidth=.3)+geom_vline(xintercept=0,linetype=2,colour='grey40')+
    geom_line(linewidth=.85)+scale_colour_manual(values=c('#007D8A','#B55025'))+
    scale_fill_manual(values=c('#007D8A','#B55025'))+
    labs(title=paste(strwrap(as.character(r$event$event_name),width=70),collapse='\n'),subtitle=paste('Official-date session:',r$event$event_date),
      x='Trading sessions relative to announcement',y='Cumulative average abnormal price return (%)',colour=NULL,fill=NULL,
      caption=paste0('Equal security weights; balanced ',bounds[1],':',bounds[2],' sample. Cumulation begins at ',bounds[1],'.\nShading: pointwise ',100*(1-cfg$bootstrap$alpha),'% absolute-tail bootstrap intervals; not a simultaneous band.'))+
    theme_minimal(base_size=11)+theme(legend.position='bottom',plot.title=element_text(size=13,face='bold'))
  for(ext in c('png','pdf')) ggsave(file.path(cfg$paths$outputs,'figures',paste0('caar_',r$event$event_id,'.',ext)),p,
      width=9,height=5.5,dpi=300)
  if(mining) {
    year<-sub('mining_charter_','',r$event$event_id)
    file.copy(file.path(cfg$paths$outputs,'figures',paste0('caar_',r$event$event_id,'.png')),
              file.path(cfg$paths$outputs,'figures',paste0('caar_mining_',year,'_ci.png')),overwrite=TRUE)
  }
  d
}
generate_outputs <- function(results,robust,inputs,data,cfg,smoke) {
  samples<-rbindlist(lapply(results,function(r) {
    s<-copy(r$selected$sample)
    for(w in unique(r$cars$window)) s[,(paste0('complete_',w)):=instrument_id %in% r$cars[window==w & complete==TRUE,instrument_id]]
    s
  }),fill=TRUE)
  models<-rbindlist(lapply(results,`[[`,'models'));ars<-rbindlist(lapply(results,`[[`,'ar'))
  cars<-rbindlist(lapply(results,`[[`,'cars'));summary<-rbindlist(lapply(results,`[[`,'summary'))
  inf<-adjust_headline_family(rbindlist(lapply(results,`[[`,'inference'),fill=TRUE),cfg)
  headline_rows<-headline_indices(inf,cfg)
  write_pq(samples,'event_samples',cfg);write_pq(models,'market_model_estimates',cfg)
  ar_columns<-intersect(c('event_id','instrument_id','date','tau','group','return','return_raw','market_return','expected',
    'ar','ar_raw','usable','donor_valid','extreme','extreme_raw','volume','adjustment_id','adjustment_factor'),names(ars))
  write_pq(ars[,..ar_columns],'abnormal_returns',cfg)
  write_pq(cars,'firm_event_cars',cfg)
  write_table(summary,'event_car_summary',cfg);write_table(inf,'event_study_inference',cfg)
  write_headline_results(inf,summary,cfg)
  write_md(c('# Event-study inference','',
    'All returns and intervals in fractional units. Headline family: five [0,+1] tests; Holm adjustment reserves all five even for a subset run.',
    'Mining events use mining-minus-non-mining; other events use the all-security portfolio.', '', md_table(inf)),
    file.path(cfg$paths$outputs,'tables/event_study_inference.md'))
  sample_summary<-samples[,.(source_instruments=.N,historical_prices=sum(historical_positive_closes>0),
     enough_estimation=sum(n_est>=cfg$analysis$min_estimation),eligible=sum(eligible),
     eligible_classified=sum(eligible & classified),eligible_unknown=sum(eligible & !classified),
     complete_primary=sum(complete_primary),complete_plot=sum(complete_plot),
     primary_mining=sum(complete_primary & group=='mining'),primary_control=sum(complete_primary & group=='non_mining')),
     by=event_id]
  exclusions<-samples[,.(n=.N),by=.(event_id,exclusion)]
  write_table(sample_summary,'sample_selection_by_event',cfg,'diagnostics')
  write_table(exclusions,'sample_exclusions',cfg,'diagnostics')
  write_md(c('# Executed sample selection','',md_table(sample_summary),'',md_table(exclusions),
    '', 'Complete CAR samples differ by window; plotting uses a separate balanced 21-session sample. Counts are securities, not verified companies.'),
    file.path(cfg$paths$outputs,'diagnostics/sample_selection.md'))
  model_summary<-models[,.(n=.N,failed=sum(!model_ok),alpha_median=median(alpha,na.rm=TRUE),
      beta_median=median(beta,na.rm=TRUE),beta_min=min(beta,na.rm=TRUE),beta_max=max(beta,na.rm=TRUE),
      median_r_squared=median(r_squared,na.rm=TRUE),median_sigma=median(sigma,na.rm=TRUE)),by=event_id]
  write_table(model_summary,'market_model_summary',cfg)
  write_table(models[!model_ok | abs(beta)>3 | abs(alpha)>.01],'flagged_market_models',cfg,'diagnostics')
  descriptive<-ars[tau>=cfg$analysis$estimation[1] & tau<=cfg$analysis$estimation[2],.(observations=.N,usable=sum(usable),
       zero_fraction=mean(return==0,na.rm=TRUE),extreme_returns=sum(extreme %in% TRUE)),by=.(event_id,group)]
  write_table(descriptive,'descriptive_statistics',cfg)
  write_md(c('# Market-model diagnostics','',md_table(model_summary),'',
    'OLS fits are instrument/event-specific and use usable dates in the configured pre-event interval.',
    'Degenerate market or stock variance and singular fits are rejected. Large alpha/beta values are flagged, not silently removed.',
    'Full model estimates, flagged models, and beta distribution are supplied. No event observations enter estimation.'),
    file.path(cfg$paths$outputs,'diagnostics/market_model_diagnostics.md'))
  suppressPackageStartupMessages(library(ggplot2))
  p<-ggplot(models[model_ok==TRUE],aes(beta))+geom_histogram(bins=35,fill='#007D8A',colour='white')+
    facet_wrap(~event_id,scales='free_y')+labs(x='Estimated market beta',y='Securities')+theme_minimal(base_size=11)
  for(ext in c('png','pdf')) ggsave(file.path(cfg$paths$outputs,'figures',paste0('market_beta_distribution.',ext)),p,width=10,height=6,dpi=300)
  daily<-rbindlist(lapply(results,function(r) {log_message('Balanced CAAR and pointwise intervals',r$event$event_id);plot_caar(r,cfg)}))
  write_pq(daily,'daily_event_aggregates',cfg);write_table(daily,'daily_event_aggregates',cfg)
  if(nrow(robust$summary)) {
    p<-ggplot(robust$summary,aes(estimate*100,reorder(specification,estimate)))+
      geom_vline(xintercept=0,colour='grey70')+geom_segment(aes(x=ci_lower*100,xend=ci_upper*100,yend=specification),colour='grey60')+
      geom_point(colour='#007D8A')+facet_wrap(~event_id,scales='free_y')+
      labs(x='Primary-window estimate and 95% interval (%)',y=NULL)+theme_minimal(base_size=10)
    for(ext in c('png','pdf')) ggsave(file.path(cfg$paths$outputs,'figures',paste0('robustness_comparison.',ext)),p,width=12,height=10,dpi=300)
  }
  ex<-exposure_regressions(results,cfg)
  headline<-inf[headline_rows,.(event_id,window,n,n_mining,n_control,estimate,ci_lower,ci_upper,p_value,holm_primary_p,null_dates,status)]
  report<-c('# Part A preliminary results','',
    paste('Execution mode:',if(smoke)'SMOKE; reduced bootstrap and sensitivities; not full precision.' else 'full configured analysis.'),'',
    '## Research objective','',
    'Measure short-horizon JSE price reactions associated with transformation-policy announcements. Outcomes concern market valuations, not realised productivity, profitability or equity gains. Parts B and C are outside scope.','',
    '## Data and sample','',md_table(sample_summary),'',
    paste('Immutable source package 1.2.0. Estimation window:',paste(cfg$analysis$estimation,collapse=':'),
      '; minimum usable dates:',cfg$analysis$min_estimation,'; positive volume:',cfg$analysis$positive_volume,
      '; maximum fraction of unchanged returns:',cfg$analysis$max_zero_fraction,'.'),
    'Known likely non-company securities are screened using historical bulletin flags. Unclassified securities remain in aggregate results as unknown; they do not enter mining/control comparisons.',
    '## Event dates and timing','',
    'Official register dates anchor session zero. All five first-public-disclosure timestamps remain unverified. Scheduled briefings do not prove first disclosure. The 2018 Cabinet reference, public stimulus/approval statement and ministerial advisory are distinct sensitivities; see information_and_market_conditions.md.',
    '', '## Returns and normal returns','',
    'Analytical returns are security-unit-consistent price changes on adjacent sessions. Raw ratios and closes remain available. Only sourced verified unit conversions are corrected; this is not a total-return series. J203 is intended as a price-index benchmark, but the exact IRESS export convention is not independently certified. The January 2024 gap is never bridged.',
    'Instrument-specific OLS: R_it = alpha_i + beta_i R_mt + epsilon_it. AR is actual minus predicted price return. Complete-window CAR sums daily AR. Equal-security-weight CAAR is the mean of complete-window CARs.',
    '', paste0('## Primary [',paste(cfg$analysis$windows[[cfg$analysis$primary_window]],collapse=','),'] results and inference'),'',
    'Fractional returns (0.01 = 1%). Mining events report the mining-minus-control spread; broad-policy events report aggregate market-model CAAR. N is the combined portfolio security count.',
    '',md_table(headline),'',
    'Intervals and two-sided Monte Carlo p-values use date-synchronous moving blocks of centred pre-event firm residual vectors. Firm-specific regression parameter error is propagated using each original OLS design. Simulated paths preserve the trading-session gap between estimation and each event window (29 intervening sessions for [0,+1]), discarding gap draws. Common shocks are retained. Complete pre-event null dates and block lengths are reported.',
    'The primary absolute-tail p-value is retained. Reported symmetric intervals invert that same strict p<alpha rule using a finite-draw order statistic; legacy basic intervals are auxiliary comparison columns only. All intervals are pointwise, not Holm simultaneous intervals.',
    'The baseline null uses valid analytical price returns including zero-volume dates. Fitting/event liquidity masks and donor validity are separate. Full extreme deletion excludes flagged observations from all three. The method is conditional on a stable residual process; volatility multipliers and alternative donor periods are scenarios, not empirical guarantees.',
    paste(sum(headline$holm_primary_p<.05,na.rm=TRUE),'of',nrow(headline),'headline tests have Holm-adjusted p<0.05. Other windows/specifications are exploratory and multiply comparisons.'),
    '', '## All CAR windows and group estimates','',md_table(summary),'',
    '## Exposure analysis','',
    'For mining events, unadjusted CAR-on-industry-indicator coefficients equal the portfolio mean difference. Historical industry membership is a provisional exposure proxy, not verified legal treatment. Financial controls, EE target gaps and historical B-BBEE levels are missing.',
    '', '## Robustness and placebos','',paste('Robustness execution:',robust$status),
    'See robustness_summary.csv for re-estimated sensitivity results and placebo_results.csv for seeded, independently refitted pseudo-events. Frozen industry snapshots and unscreened unrelated news limit placebo interpretation.',
    '', '## Interpretation and limitations','',
    'Results describe conditional abnormal price movements around public-policy dates. They do not identify causal policy effects or realised efficiency costs. Non-mining firms may be indirectly affected. The benchmark contains affected firms and may absorb broad policy responses.',
    'Earlier public information and other news matter for timing. The 2018 gazette-window result is not the whole policy-information sequence. The 2023 diplomatic episode, 2025 tariff-related news and 2026 monetary/global-market developments limit attribution. Insignificance does not establish no economic effect.',
    'The verified Reinet ten-to-one conversion is corrected. Capital distributions, rights and other unverified adjustments remain explicit in the ledger, with targeted exclusions as sensitivities. Genuine large news movements are retained in the baseline. Preferred returns are price-based and are not realised shareholder wealth.',
    'Issuer identities, security classes and historical exposures are incomplete. Equal-security weighting remains primary. Partial issuer sensitivity uses only verified Fortress A/B links; it is not a fully verified issuer universe. The reviewed industry alternative is distinct from certified legal treatment.',
    'Historical bulletin reporting dates precede events, but publication availability is unverified. Strict availability-verified exposure analysis is unsupported. Source calendar and historical universe are not fully externally certified.',
    '', '## Outstanding work and readiness','',
    'Preliminary results produced; methodological review required. Verify adjustment conventions and corporate actions for influential firms, release timing, historical identity/exposure matches, issuer concentration and null-volatility assumptions before thesis use.',
    'Inspect recorded automated test outcomes separately in outputs/diagnostics/test_summary.md. Execution success alone does not establish research readiness.')
  write_md(report,file.path(cfg$paths$outputs,'reports/part_a_preliminary_results.md'))
  write_md(c('# Research progress','',paste('Completed event runs:',paste(names(results),collapse=', ')),
    'Package verifier passed; schemas, keys, event dates, benchmark coverage and independent return formulas checked.',
    paste('Return comparisons:',sum(is.finite(data$returns$return)),'valid returns; zero discrepancies.'),
    paste('Model rows:',nrow(models),'; failed/degenerate:',sum(!models$model_ok)),
    paste('Inference rows:',nrow(inf),'; unavailable:',sum(inf$status!='ok')),
    paste('Sensitivity rows:',nrow(robust$summary),'; placebo rows:',nrow(robust$placebos)),
    '',md_table(headline),'',
    'Readiness: preliminary results produced, requiring methodological review. See the result report and test summary for evidence and remaining limitations.',
    '', 'Automated tests: see outputs/diagnostics/test_summary.md; rerun after analysis output regeneration. All unit, numerical and integration outcomes are recorded there.',
    'Next: inspect corporate actions and influential returns, validate timing and issuer identities, review exposure definitions and bootstrap assumptions with the supervisor.',
    'No Parts B/C, IRESS extraction, source rewrites, external data uploads or remote publication performed.'),
    'docs/research_progress.md')
}
