fit_market_model <- function(y, x) {
  good <- is.finite(y) & is.finite(x); y<-y[good];x<-x[good]
  if (length(y)<3 || var(x)<1e-14 || var(y)<1e-14)
    return(data.table(alpha=NA_real_,beta=NA_real_,n=length(y),sigma=NA_real_,r_squared=NA_real_,model_ok=FALSE))
  fit<-lm.fit(cbind(1,x),y); res<-fit$residuals
  data.table(alpha=unname(fit$coefficients[1]),beta=unname(fit$coefficients[2]),n=length(y),
    sigma=sqrt(sum(res^2)/(length(y)-2)),r_squared=1-sum(res^2)/sum((y-mean(y))^2),model_ok=fit$rank==2)
}
estimate_models <- function(selected,cfg) {
  ids<-selected$sample[eligible==TRUE,instrument_id]
  assert(length(ids)>0,'No eligible securities')
  est<-cfg$analysis$estimation
  z<-selected$data[instrument_id %in% ids & tau>=est[1] & tau<=est[2] & usable==TRUE,
     fit_market_model(return,market_return),by=instrument_id]
  z[, event_id:=unique(selected$sample$event_id)]
  assert(any(z$model_ok),'All market models degenerate')
  z
}
