# Read-only inference audit. Outputs are confined to independent_review.
args0 <- commandArgs(FALSE)
script <- sub('^--file=', '', args0[grepl('^--file=', args0)])
setwd(normalizePath(file.path(dirname(script), '../..')))
source('R/utils.R'); source_modules()
cfg <- yaml::read_yaml('config/analysis.yml')
outdir <- 'outputs/diagnostics/independent_review'
dir.create(outdir, recursive=TRUE, showWarnings=FALSE)
save_csv <- function(x, name) fwrite(x, file.path(outdir,paste0(name,'.csv')), na='')
ar <- read_pq('data/derived/abnormal_returns.parquet',cfg)
cars <- read_pq('data/derived/firm_event_cars.parquet',cfg)
pub <- fread('outputs/tables/event_study_inference.csv')
returns <- read_pq('data/derived/returns_daily.parquet',cfg)
inputs <- list(events=fread('research/events.csv'),
  calendar=fread('data/thesis_data/documentation/trading_calendar.csv')[,.(date=as.Date(date))],
  master=read_pq('data/thesis_data/data/instruments.parquet',cfg,
    c('instrument_id','ticker','company_name','issuer_id','security_type')),
  classifications=read_pq('data/thesis_data/data/event_industry_classifications.parquet',cfg))
inputs$events[,event_date:=as.Date(event_date)]
inputs$calendar[,session:=.I]

tail_stats <- function(error, estimate) {
  B <- length(error)
  q <- quantile(error,c(.025,.975),names=FALSE)
  data.table(p_absolute=(1+sum(abs(error)>=abs(estimate)))/(B+1),
    p_equal_tail=min(1,2*min((1+sum(error>=estimate))/(B+1),(1+sum(error<=estimate))/(B+1))),
    ci_lower=estimate-q[2],ci_upper=estimate-q[1],
    ci_excludes_zero=(estimate-q[2]>0 || estimate-q[1]<0),
    se=sd(error),skewness=mean((error/sd(error))^3),
    null_q025=q[1],null_q975=q[2],null_min=min(error),null_max=max(error),
    symmetric_ci_lower=estimate-unname(quantile(abs(error),.95)),
    symmetric_ci_upper=estimate+unname(quantile(abs(error),.95)))
}
# Avoid data.table's column/argument shadowing explicitly.
get_portfolio <- function(cc,target_group) {
  if(target_group=='mining_minus_non_mining') {
    m<-cc[complete==TRUE & group=='mining',instrument_id]
    control<-cc[complete==TRUE & group=='non_mining',instrument_id]
    list(ids=c(m,control),weights=c(rep(1/length(m),length(m)),rep(-1/length(control),length(control))))
  } else {
    ids<-if(target_group=='all') cc[complete==TRUE,instrument_id] else cc[complete==TRUE & group==target_group,instrument_id]
    list(ids=ids,weights=rep(1/length(ids),length(ids)))
  }
}
tails <- list(); extremes <- list(); contributors <- list(); variance_scales <- list()
for(k in seq_len(nrow(pub))) {
  row<-pub[k]; eid<-row$event_id; window_id<-row$window
  bounds<-cfg$analysis$windows[[window_id]]
  portfolio<-get_portfolio(cars[event_id==eid & window==window_id],row$group)
  group_order<-if(grepl('^mining_charter',eid)) c('all','mining','non_mining','mining_minus_non_mining') else 'all'
  offset<-100*match(window_id,names(cfg$analysis$windows))+match(row$group,group_order)
  d<-ar[event_id==eid]
  boot<-bootstrap_portfolio(d,portfolio$ids,portfolio$weights,bounds[1],bounds[2],cfg,offset)
  z<-tail_stats(boot$error,row$estimate)
  stopifnot(abs(z$p_absolute-row$p_value)<1e-12, abs(z$ci_lower-row$ci_lower)<1e-12,
    abs(z$ci_upper-row$ci_upper)<1e-12,abs(z$se-row$se)<1e-12)
  z[,`:=`(event_id=eid,window=window_id,group=row$group,estimate=row$estimate,
    p_ci_disagreement=(p_absolute<.05)!=ci_excludes_zero)]
  tails[[k]]<-z
  if(window_id!='primary' || !(row$group %in% c('all','mining_minus_non_mining')) ||
     (grepl('^mining_charter',eid) && row$group!='mining_minus_non_mining')) next
  pre<-d[instrument_id %in% portfolio$ids & tau>=-250 & tau<=-30]
  wide<-dcast(pre,tau~instrument_id,value.var='ar_raw')
  ids<-portfolio$ids
  E<-as.matrix(wide[,..ids])
  complete<-apply(is.finite(E),1,all); E<-E[complete,,drop=FALSE]
  zpre<-as.vector(E%*%portfolio$weights)
  ext<-pre[extreme %in% TRUE]
  ext[,portfolio_weight:=portfolio$weights[match(instrument_id,portfolio$ids)]]
  ext[,weighted_residual:=ar_raw*portfolio_weight]
  extremes[[eid]]<-ext[order(-abs(weighted_residual))]
  component<-vapply(seq_along(portfolio$ids),function(j) cov(E[,j]*portfolio$weights[j],zpre)/var(zpre),0.)
  contributors[[eid]]<-data.table(event_id=eid,instrument_id=portfolio$ids,
    weight=portfolio$weights,variance_contribution=component)[order(-abs(variance_contribution))]
  # Sensitivity only: rescale the full prediction-error distribution. This
  # includes OLS error and is explicitly not an event-only variance estimator.
  variance_scales[[eid]]<-rbindlist(lapply(c(1,1.25,1.5,2),function(factor) {
    z<-tail_stats(boot$error*factor,row$estimate)
    z[,`:=`(event_id=eid,error_sd_multiplier=factor)];z
  }))
}
tails<-rbindlist(tails); save_csv(tails,'null_distribution_diagnostics')
save_csv(rbindlist(extremes,fill=TRUE),'headline_pre_event_extremes')
save_csv(rbindlist(contributors),'null_variance_contributions')
save_csv(rbindlist(variance_scales),'prediction_error_scale_sensitivity')
print(tails[p_ci_disagreement==TRUE,.(event_id,window,group,p_absolute,p_equal_tail,ci_lower,ci_upper)])

primary_cfg<-cfg;primary_cfg$analysis$windows<-cfg$analysis$windows['primary']
sens<-list(); retained_extremes<-list()
base_bootstrap<-bootstrap_portfolio
for(eid in cfg$analysis$events) {
  ev<-inputs$events[event_id==eid]
  r<-analyse_event(returns,inputs,ev,primary_cfg,remove_extreme=TRUE)
  original<-headline(r,'supplied_extreme_deletion_fit_only')
  sens[[paste0(eid,'supplied')]]<-original
  ids<-get_portfolio(r$cars[window=='primary'],original$group)$ids
  pre<-r$ar[instrument_id %in% ids & tau>=-250 & tau<=-30]
  retained_extremes[[eid]]<-pre[extreme %in% TRUE & is.finite(ar_raw),
    .(event_id,instrument_id,date,tau,return,usable,ar_raw)]
  # Hypothetical deletion of flagged dates from the bootstrap donor panel too.
  # Other usability masks and model coefficients remain those of the supplied
  # extreme-deletion specification; no fabricated price adjustments are made.
  patched<-copy(r$ar);patched[extreme %in% TRUE,ar_raw:=NA_real_]
  z<-infer_event(patched,r$cars,ev,primary_cfg)
  rr<-r;rr$inference<-z
  sens[[paste0(eid,'null')]]<-headline(rr,'extreme_deletion_in_fit_and_null')
  flagged_ids<-pre[extreme %in% TRUE,unique(instrument_id)]
  if(length(flagged_ids)) {
    rr<-analyse_event(returns[!(instrument_id %in% flagged_ids)],inputs,ev,primary_cfg)
    sens[[paste0(eid,'security')]]<-headline(rr,'exclude_any_pre_event_extreme_security')
  }
  # Public-information-date diagnostics do not replace the registered t0.
  if(eid=='mining_charter_2018') for(date in c('2018-09-20','2018-09-21','2018-09-26')) {
    e2<-copy(ev);e2[,event_date:=as.Date(date)]
    rr<-analyse_event(returns,inputs,e2,primary_cfg)
    sens[[paste0(eid,date)]]<-headline(rr,paste0('review_date_',date))
  }
  if(grepl('^mining_charter',eid)) {
    # Targeted diagnostics of classifications and historically backfilled IDs.
    # These are hypotheses for manual identity review, never automatic fixes.
    for(label in c('KIO_mining','omit_KIO','VAL_mining','omit_investment_labels')) {
      inp<-inputs;inp$classifications<-copy(inputs$classifications);dat<-returns
      if(label=='KIO_mining') inp$classifications[event_id==eid & instrument_id=='KIO:XJSE:EQU',mining_candidate:=TRUE]
      if(label=='omit_KIO') dat<-dat[instrument_id!='KIO:XJSE:EQU']
      if(label=='VAL_mining') inp$classifications<-rbind(inp$classifications[!(event_id==eid & instrument_id=='VAL:XJSE:EQU')],
        data.table(event_id=eid,instrument_id='VAL:XJSE:EQU',nature_of_business_raw='Plat & Prec. Met',
          mining_candidate=TRUE,likely_non_company_security=FALSE,match_confidence='high_label_concordance',
          historical_security_name='REVIEW CANDIDATE: Anglo American Platinum',historical_share_code='AMS',
          bulletin_month=as.Date(ev$event_date)-31,preannouncement_availability_verified=FALSE),fill=TRUE)
      if(label=='omit_investment_labels') {
        bad<-r$selected$sample[grepl('Equity inv|Closed End|Open End',nature_of_business_raw,ignore.case=TRUE),instrument_id]
        dat<-dat[!(instrument_id %in% bad)]
      }
      rr<-analyse_event(dat,inp,ev,primary_cfg)
      sens[[paste0(eid,label)]]<-headline(rr,paste0('review_',label))
    }
  } else {
    for(label in 'omit_investment_labels') {
      bad<-r$selected$sample[grepl('Equity inv|Closed End|Open End',nature_of_business_raw,ignore.case=TRUE),instrument_id]
      if(label=='omit_investment_labels') {
        rr<-analyse_event(returns[!(instrument_id %in% bad)],inputs,ev,primary_cfg)
        sens[[paste0(eid,label)]]<-headline(rr,paste0('review_',label))
      }
    }
  }
}
save_csv(rbindlist(sens,fill=TRUE),'targeted_sensitivities')
save_csv(rbindlist(retained_extremes,fill=TRUE),'extremes_retained_in_deletion_null')

# A deterministic asymmetric-null example shows why an absolute-value test
# and an equal-tailed interval need not give the same decision.
asym<-c(rep(1,970),rep(-97/3,30)); stopifnot(abs(mean(asym))<1e-12)
demo<-tail_stats(asym,-2);demo[,example:='970 draws at 1; 30 draws at -97/3; observed=-2']
save_csv(demo,'asymmetric_null_example')

# Recalculate one sensitivity with reported p/CI disagreement independently.
ev<-inputs$events[event_id=='mining_charter_2018'];ev[,event_date:=as.Date('2018-09-26')]
r<-analyse_event(returns,inputs,ev,primary_cfg)
h<-headline(r,'previous_session');p<-get_portfolio(r$cars[window=='primary'],h$group)
b<-bootstrap_portfolio(r$ar,p$ids,p$weights,0,1,primary_cfg,104)
z<-tail_stats(b$error,h$estimate);z[,specification:='mining_charter_2018 previous_session']
save_csv(z,'previous_session_tail_comparison')

# Explicit multivariate refits with unequal actual OLS masks, common shocks,
# negative portfolio weights, a calendar gap and serially correlated errors.
set.seed(8301); tau<- -250:1; x<-rnorm(length(tau),sd=.01)
common<-as.numeric(arima.sim(list(ar=.5),n=length(tau),sd=.01))
syn<-rbindlist(lapply(1:3,function(j) {
  e<-common*(j/3)+rnorm(length(tau),sd=.004)
  usable<-rep(TRUE,length(tau));usable[which(tau<=-30)[seq(j,210,by=13)]]<-FALSE
  y<-.001+j*.3*x+e; fit<-lm(y[tau<=-30 & usable]~x[tau<=-30 & usable])
  data.table(instrument_id=paste0('S',j),tau=tau,market_return=x,usable=usable,
    ar_raw=y-coef(fit)[1]-coef(fit)[2]*x)
}))
ids<-c('S1','S2','S3');w<-c(.5,.5,-1)
ccfg<-cfg;ccfg$bootstrap$replications<-199L
actual<-bootstrap_portfolio(syn,ids,w,0,1,ccfg)
pre<-syn[tau<=-30];wide<-dcast(pre,tau~instrument_id,value.var='ar_raw')
E<-as.matrix(wide[,..ids]);E<-sweep(E,2,colMeans(E),'-')
for(j in 1:3) E[,j]<-E[,j]*sqrt(sum(pre[instrument_id==ids[j],usable])/(sum(pre[instrument_id==ids[j],usable])-2))
starts<-which(vapply(seq_len(nrow(E)-4),function(i)all(diff(wide$tau[i:(i+4)])==1),TRUE))
set.seed(cfg$bootstrap$seed)
block_starts<-matrix(starts[sample.int(length(starts),199*ceiling(252/5),replace=TRUE)],199)
idx<-matrix(NA_integer_,199,ncol(block_starts)*5)
for(k in seq_len(ncol(block_starts))) idx[,(5*k-4):(5*k)]<-outer(block_starts[,k],0:4,'+')
idx<-idx[,1:252]
manual<-vapply(1:199,function(k) {
  sum(vapply(1:3,function(j) {
    fitdays<-pre[instrument_id==ids[j] & usable==TRUE]
    fitpos<-match(fitdays$tau,-250:-30)
    X<-cbind(1,fitdays$market_return)
    f<-lm.fit(X,E[idx[k,fitpos],j])
    w[j]*(sum(E[idx[k,251:252],j])-sum(cbind(1,x[tau %in% 0:1])%*%f$coefficients))
  },0.))
},0.)
manual<-manual-mean(manual)
err<-max(abs(manual-actual$error));stopifnot(err<1e-12)
save_csv(data.table(draws=199,maximum_explicit_refit_error=err,common_shocks=TRUE,
  different_fit_masks=TRUE,negative_weights=TRUE,gap=29),'explicit_multivariate_refit')
cat('All 55 inference rows reproduced; multivariate explicit-refit maximum error:',err,'\n')
