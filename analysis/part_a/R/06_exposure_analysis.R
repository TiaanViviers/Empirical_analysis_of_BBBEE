exposure_regressions <- function(results,cfg) {
  out<-rbindlist(lapply(results,function(r) {
    if(!grepl('^mining_charter',r$event$event_id)) return(NULL)
    rbindlist(lapply(unique(r$cars$window),function(w) {
      d<-r$cars[window==w & complete==TRUE & group %in% c('mining','non_mining')]
      if(!all(c('mining','non_mining') %in% d$group)) return(NULL)
      fit<-lm(car~I(group=='mining'),data=d)
      data.table(event_id=r$event$event_id,window=w,n=nrow(d),intercept=unname(coef(fit)[1]),
        mining_coefficient=unname(coef(fit)[2]),specification='unadjusted descriptive CAR on mining indicator',
        inference='use synchronous spread inference; no cross-sectional OLS p-values')
    }))
  }))
  write_table(out,'exposure_regressions',cfg)
  write_md(c('# Exposure analysis','',
    'Mining indicator OLS coefficients are unadjusted descriptive differences of group mean CARs.',
    'Their uncertainty is assessed using the synchronous portfolio spread; ordinary independent-firm standard errors are omitted.',
    'EE target-gap regressions are blocked: historical workforce composition and sector-specific regulatory target gaps are absent.',
    'B-BBEE exposure regressions are blocked: historical compliance levels and a credible unaffected group are absent.',
    'Controlled models require event-dated market capitalisation, book-to-market and leverage; these were not fabricated.',
    'Historical nature-of-business labels describe industries; they do not establish EE regulatory target exposure.'),
    file.path(cfg$paths$outputs,'reports/exposure_analysis.md'))
  out
}
