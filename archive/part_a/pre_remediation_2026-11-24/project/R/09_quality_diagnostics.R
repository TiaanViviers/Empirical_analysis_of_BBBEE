# Inspection aids: labels/ISINs identify review candidates, never historical issuer merges.
quality_diagnostics <- function(results,inputs,cfg) {
  samples<-rbindlist(lapply(results,function(r)r$selected$sample[eligible==TRUE]))
  same_names<-samples[!is.na(company_name),.(n_securities=.N,instruments=paste(instrument_id,collapse=';')),
    by=.(event_id,company_name)][n_securities>1]
  write_table(same_names,'repeated_source_labels',cfg,'diagnostics')
  metadata<-read_pq(file.path(cfg$paths$source,'data/instrument_metadata_2026-11-23.parquet'),cfg,
     c('instrument_id','isin_raw','isin_valid','snapshot_date'))
  linked<-join_checked(samples[,.(event_id,instrument_id)],metadata,'instrument_id')
  isin<-linked[isin_valid==TRUE,.(n_securities=.N,instruments=paste(instrument_id,collapse=';')),
    by=.(event_id,isin_raw)][n_securities>1]
  write_table(isin,'current_isin_review_candidates',cfg,'diagnostics')
  top<-rbindlist(lapply(results,function(r) {
    z<-copy(r$cars[window==cfg$analysis$primary_window & complete==TRUE])
    z[,rank_abs:=frank(-abs(car),ties.method='first')]
    z<-join_checked(z,r$selected$sample[,.(instrument_id,company_name,historical_security_name,nature_of_business_raw)],'instrument_id')
    z[rank_abs<=20]
  }),fill=TRUE)
  write_table(top,'influential_primary_cars',cfg,'diagnostics')
  extreme<-rbindlist(lapply(results,function(r) {
    z<-r$ar[extreme %in% TRUE,.(event_id,instrument_id,date,tau,return,ar_raw,group,volume)]
    if(nrow(z)) z<-join_checked(z,r$selected$sample[,.(instrument_id,historical_security_name,nature_of_business_raw)],'instrument_id')
    z
  }),fill=TRUE)
  write_table(extreme,'event_sample_extreme_returns',cfg,'diagnostics')
  suspicious_controls<-samples[group=='non_mining' & nature_of_business_raw %in% c('Iron & Steel','Iron & Steel Prod')]
  write_table(suspicious_controls[,.(event_id,instrument_id,historical_security_name,nature_of_business_raw)],
      'mineral_value_chain_controls',cfg,'diagnostics')
  null_peaks<-rbindlist(lapply(results,function(r) {
    cc<-r$cars[window==cfg$analysis$primary_window];mining<-grepl('^mining_charter',r$event$event_id)
    if(mining) {
      m<-group_ids(cc,'mining');c<-group_ids(cc,'non_mining');ids<-c(m,c)
      w<-c(rep(1/length(m),length(m)),rep(-1/length(c),length(c)))
    } else {ids<-group_ids(cc,'all');w<-rep(1/length(ids),length(ids))}
    d<-r$ar[instrument_id %in% ids & tau>=cfg$analysis$estimation[1] & tau<=cfg$analysis$estimation[2]]
    d[,weight:=w[match(instrument_id,ids)]]
    z<-d[,.(spread=sum(ar_raw*weight),n=.N),by=.(event_id,date,tau)][order(-abs(spread))]
    head(z,10)
  }))
  write_table(null_peaks,'largest_null_portfolio_shocks',cfg,'diagnostics')
  # Representative OLS residual figures use median-beta member of each group.
  representatives<-list()
  for(r in results) for(g in c('mining','non_mining')) {
    ids<-r$selected$sample[eligible==TRUE & group==g,instrument_id]
    mm<-r$models[instrument_id %in% ids & model_ok==TRUE][order(beta)]
    if(!nrow(mm)) next
    id<-mm$instrument_id[ceiling(nrow(mm)/2)]
    z<-r$ar[instrument_id==id & tau>=cfg$analysis$estimation[1] & tau<=cfg$analysis$estimation[2],
      .(event_id,instrument_id,date,ar_raw,usable)]
    z[,group:=g];representatives[[paste(r$event$event_id,g)]]<-z
  }
  rep<-rbindlist(representatives)
  write_table(rep,'representative_model_residuals',cfg,'diagnostics')
  if(nrow(rep)) {
    p<-ggplot2::ggplot(rep,ggplot2::aes(date,ar_raw*100,colour=group))+
      ggplot2::geom_hline(yintercept=0,colour='grey70')+ggplot2::geom_line(linewidth=.35)+
      ggplot2::facet_wrap(~event_id,scales='free_x')+
      ggplot2::labs(x=NULL,y='Market-model residual price return (%)',
        title='Representative pre-event residuals',subtitle='Median-beta security in each historical industry group',colour=NULL)+
      ggplot2::theme_minimal(base_size=10)+ggplot2::theme(legend.position='bottom')
    for(ext in c('png','pdf')) ggplot2::ggsave(file.path(cfg$paths$outputs,'figures',paste0('representative_residuals.',ext)),p,width=11,height=7,dpi=300)
  }
  write_md(c('# Data-quality and identity review','',
    'Extreme-return counts and full-year distributions are recorded in return_quality_summary.csv. event_sample_extreme_returns.csv isolates every flagged change among fitted event samples, preserving date, security, volume and historical industry.',
    'influential_primary_cars.csv ranks the 20 largest absolute [0,+1] CARs per event. largest_null_portfolio_shocks.csv identifies pre-event common dates that dominate portfolio variability. Neither list establishes corporate actions or data error.',
    'The source-wide audit retains every >30% valid price ratio. No source movement is adjusted or deleted in the baseline. Severe deletion sensitivity is only diagnostic; source corporate-action records are still needed.',
    '', '## Exposure contamination requiring review','',
    'The supplied exact-label proxy places Iron & Steel instruments in non-mining, including KIO:XJSE:EQU. Such categories can contain mineral-related firms and weaken a legal-treatment interpretation. mineral_value_chain_controls.csv lists affected sample members. A broader mineral-value-chain sensitivity reassigns these labels provisionally, without asserting direct Mining Charter applicability.',
    '',md_table(suspicious_controls[,.(event_id,instrument_id,historical_security_name,nature_of_business_raw)]),
    '', '## Multiple-security evidence','',
    paste('Repeated historical source-label groups:',nrow(same_names),'; repeated valid contemporary ISIN groups:',nrow(isin)),
    'Repeated labels/current ISINs are review candidates only, not confirmed historical issuer links. No current listing status enters eligibility. Verified historical issuer consolidation remains unsupported.',
    '',md_table(same_names),'',md_table(isin)),
    file.path(cfg$paths$outputs,'diagnostics/data_quality_review.md'))
}
