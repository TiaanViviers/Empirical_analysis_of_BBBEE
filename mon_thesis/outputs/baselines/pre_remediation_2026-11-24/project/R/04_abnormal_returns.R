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
      data.table(window=w,group=g,n=length(ids),mean_car=if(length(ids)) mean(vals) else NA_real_,
        median_car=if(length(ids)) median(vals) else NA_real_,sd_car=if(length(ids)>1) sd(vals) else NA_real_)
    }))
  }))
  summaries[,event_id:=as.character(event$event_id)]
  inf<-if(inference) infer_event(ar,cars,event,cfg,normal_model) else data.table()
  list(selected=selected,models=models,ar=ar,cars=cars,summary=summaries,inference=inf,event=event,primary_window=cfg$analysis$primary_window)
}
