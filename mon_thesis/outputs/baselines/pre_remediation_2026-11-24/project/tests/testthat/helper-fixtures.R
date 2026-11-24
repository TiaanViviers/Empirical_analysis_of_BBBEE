synthetic_ar <- function(seed=1,shock=.05,common=FALSE) {
  set.seed(seed)
  tau<- -250:10;x<-rnorm(length(tau),0,.01)
  common_e<-rnorm(length(tau),0,.01)
  d<-rbindlist(lapply(c('M','C'),function(id) {
    e<-if(common) common_e else .5*common_e+rnorm(length(tau),0,.005)
    y<-.001+1.2*x+e+ifelse(tau==0 & id=='M',shock,0)
    fit<-fit_market_model(y[tau<=-30],x[tau<=-30])
    data.table(instrument_id=id,tau=tau,date=as.Date('2000-01-01')+seq_along(tau),
      group=if(id=='M')'mining' else 'non_mining',return=y,market_return=x,
      ar_raw=y-fit$alpha-fit$beta*x,ar=y-fit$alpha-fit$beta*x,usable=TRUE)
  }))
  d
}
