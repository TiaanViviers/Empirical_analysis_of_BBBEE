# A restricted BMP/KP-style standardized-CAR diagnostic. It is NOT primary
# inference for raw equal-security CAAR or the signed mining/control contrast.
# Conditions: approximately independent time innovations, comparable standardized
# loadings, representative pre-event correlations, and stable correlation shape.
standardized_car_test <- function(scar,rbar,alpha=.05) {
  n<-length(scar)
  assert(n>2 && all(is.finite(scar)) && is.finite(rbar),'Invalid standardized CAR sample')
  assert(sd(scar)>0 && rbar<1 && 1+(n-1)*rbar>0,'Degenerate cross-correlation adjustment')
  bmp<-sqrt(n)*mean(scar)/sd(scar)
  factor<-sqrt((1-rbar)/(1+(n-1)*rbar))
  kp<-bmp*factor
  se<-sd(scar)/sqrt(n)/factor
  critical<-qt(1-alpha/2,n-1)
  data.table(n=n,mean_standardized_car=mean(scar),bmp_statistic=bmp,
    bmp_p=2*pt(-abs(bmp),df=n-1),average_pre_correlation=rbar,kp_factor=factor,
    kp_style_statistic=kp,kp_style_p=2*pt(-abs(kp),df=n-1),
    standardized_ci_lower=mean(scar)-critical*se,standardized_ci_upper=mean(scar)+critical*se)
}
standardized_car_diagnostic <- function(r,cfg) {
  cc<-r$cars[window==cfg$analysis$primary_window & complete==TRUE]
  ids<-cc$instrument_id
  pre<-r$ar[instrument_id %in% ids & tau>=cfg$analysis$estimation[1] & tau<=cfg$analysis$estimation[2]]
  panel<-residual_donor_panel(pre,ids,cfg)
  assert(nrow(panel$E)>=cfg$bootstrap$min_null_dates,'Insufficient common residual dates for diagnostic')
  correlation<-cor(panel$E)
  rbar<-mean(correlation[upper.tri(correlation)])
  bounds<-cfg$analysis$windows[[cfg$analysis$primary_window]];L<-diff(bounds)+1
  market<-unique(r$ar[tau>=bounds[1] & tau<=bounds[2],.(tau,market_return)])
  q<-c(L,sum(market$market_return))
  scale<-vapply(ids,function(id) {
    fitdays<-pre[instrument_id==id & usable==TRUE];X<-cbind(1,fitdays$market_return)
    sigma<-r$models[instrument_id==id,sigma]
    sigma*sqrt(L+as.numeric(t(q)%*%solve(crossprod(X),q)))
  },0.)
  out<-standardized_car_test(cc$car/scale,rbar,cfg$bootstrap$alpha)
  out[,`:=`(event_id=as.character(r$event$event_id),window=cfg$analysis$primary_window,
    group='all',estimand='mean firm-standardized CAR; NOT raw CAAR or mining/control spread',
    status='exploratory; not a headline replacement or guarantee under changing correlation',
    method='BMP/KP-style standardized CAR with OLS forecast-error scaling; temporal independence assumption')]
  out
}
