abnormal_returns <- function(selected,models,normal_model='market_model') {
  d<-join_checked(selected$data[instrument_id %in% models[model_ok==TRUE,instrument_id]],
       models[,.(instrument_id,alpha,beta)],'instrument_id')
  d<-join_checked(d,selected$sample[,.(instrument_id,group)],'instrument_id')
  d[, expected:=if(normal_model=='market_adjusted') market_return else alpha+beta*market_return]
  d[, ar_raw:=return-expected]
  d[, ar:=fifelse(usable,ar_raw,NA_real_)]
  d[, event_id:=unique(selected$sample$event_id)]
  d
}
complete_cars <- function(ar,a,b,value='ar') {
  out<-ar[tau>=a & tau<=b, .(n_sessions=sum(is.finite(get(value))),
    car=if(.N==b-a+1 && all(is.finite(get(value)))) sum(get(value)) else NA_real_),by=.(instrument_id,group)]
  out[, complete:=n_sessions==b-a+1 & is.finite(car)]
  out
}
group_ids <- function(cars,group_name) {
  if(group_name=='all') return(cars[complete==TRUE,instrument_id])
  cars[complete==TRUE & group==group_name,instrument_id]
}
security_weights <- function(ids,sample=NULL,weighting='equal_security') {
  if(!length(ids)) return(numeric())
  if(weighting=='equal_security') return(rep(1/length(ids),length(ids)))
  assert(weighting=='partial_verified_issuer','Unknown portfolio weighting')
  assert(!is.null(sample) && 'reviewed_issuer_id' %in% names(sample),'Verified issuer mapping required')
  issuer<-sample$reviewed_issuer_id[match(ids,sample$instrument_id)]
  issuer[is.na(issuer) | !nzchar(issuer)]<-paste0('unmapped_security:',ids[is.na(issuer) | !nzchar(issuer)])
  count<-table(issuer)
  as.numeric(1/(length(count)*count[issuer]))
}
portfolio_definition <- function(cars,target_group,sample=NULL,weighting='equal_security') {
  m<-control<-character()
  if(target_group=='mining_minus_non_mining') {
    m<-group_ids(cars,'mining');control<-group_ids(cars,'non_mining')
    ids<-c(m,control)
    weights<-c(security_weights(m,sample,weighting),-security_weights(control,sample,weighting))
  } else {
    ids<-group_ids(cars,target_group);weights<-security_weights(ids,sample,weighting)
    if(target_group=='mining') m<-ids
    if(target_group=='non_mining') control<-ids
  }
  list(ids=ids,weights=weights,mining=m,controls=control)
}
portfolio_series <- function(ar,ids,value='ar_raw') {
  assert(length(ids)>0,'Empty portfolio')
  ar[instrument_id %in% ids,.(value=if(.N==length(ids) && all(is.finite(get(value)))) mean(get(value)) else NA_real_,
    constituents=.N,valid_constituents=sum(is.finite(get(value)))),by=.(tau,date,market_return)][order(tau)]
}
weighted_portfolio_series <- function(ar,ids,weights,value='ar') {
  assert(length(ids)>0 && length(ids)==length(weights),'Invalid portfolio')
  d<-copy(ar[instrument_id %in% ids]);d[,portfolio_weight:=weights[match(instrument_id,ids)]]
  d[,.(value=if(.N==length(ids) && all(is.finite(get(value)))) sum(get(value)*portfolio_weight) else NA_real_,
    constituents=.N,valid_constituents=sum(is.finite(get(value)))),by=.(tau,date,market_return)][order(tau)]
}
# This orchestration is also used by re-estimated placebo and sensitivity analyses.
analyse_event <- function(returns,inputs,event,cfg,normal_model='market_model',strict=FALSE,remove_extreme=FALSE,inference=TRUE) {
  selected<-select_sample(returns,inputs,event,cfg,strict,remove_extreme)
  models<-estimate_models(selected,cfg)
  ar<-abnormal_returns(selected,models,normal_model)
  cars<-rbindlist(lapply(names(cfg$analysis$windows),function(w) {
    bounds<-cfg$analysis$windows[[w]]; z<-complete_cars(ar,bounds[1],bounds[2]);z[,window:=w];z
  }))
  cars[,event_id:=as.character(event$event_id)]
  summaries<-rbindlist(lapply(names(cfg$analysis$windows),function(w) {
    cc<-cars[window==w]
    rbindlist(lapply(c('all','mining','non_mining','unknown'),function(g) {
      ids<-group_ids(cc,g); vals<-cc[instrument_id %in% ids,car]
      data.table(window=w,group=g,n=length(ids),mean_car=if(length(ids)) sum(vals*security_weights(ids,selected$sample,or_default(cfg$analysis$weighting,'equal_security'))) else NA_real_,
        median_car=if(length(ids)) median(vals) else NA_real_,sd_car=if(length(ids)>1) sd(vals) else NA_real_)
    }))
  }))
  summaries[,event_id:=as.character(event$event_id)]
  inf<-if(inference) infer_event(ar,cars,event,cfg,normal_model,selected$sample) else data.table()
  list(selected=selected,models=models,ar=ar,cars=cars,summary=summaries,inference=inf,event=event,primary_window=cfg$analysis$primary_window)
}
