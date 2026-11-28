testthat::test_that('verified conversion is reversible and leaves all raw fields intact', {
  cfg<-cfg_test;ledger<-read_corporate_actions(cfg)[action_id=='RNI_20171129_10_TO_1']
  x<-data.table(instrument_id='RNI:XJSE:EQU',date=as.Date('2017-11-29'),close_raw=29585,
    return=29585/3000-1,volume=332626)
  a<-apply_corporate_actions(x,ledger)
  testthat::expect_equal(a$returns$return,29585/(3000*10)-1,tolerance=1e-14)
  testthat::expect_equal(a$returns$return_raw,x$return)
  testthat::expect_equal(a$returns$close_raw,x$close_raw)
  testthat::expect_equal(a$returns$volume,x$volume)
  testthat::expect_true(a$returns$extreme_raw)
  testthat::expect_false(a$returns$extreme)
  testthat::expect_true(a$audit$applied)
  testthat::expect_equal(apply_corporate_actions(a$returns,ledger)$returns,a$returns)
  testthat::expect_equal(apply_corporate_actions(a$returns,ledger,enabled=FALSE)$returns$return,x$return)
  ledger[,verification_status:='unresolved']
  testthat::expect_error(apply_corporate_actions(x,ledger),'Unverified')
})

testthat::test_that('a verified cash action with unresolved quote units is never silently adjusted', {
  ledger<-read_corporate_actions(cfg_test)[action_id=='MTNZF_20250723_CAPITAL']
  x<-data.table(instrument_id='MTNZF:XJSE:EQU',date=as.Date('2025-07-23'),close_raw=105,return=105/2110-1)
  out<-apply_corporate_actions(x,ledger)
  testthat::expect_identical(out$returns$return,x$return)
  testthat::expect_false(out$audit$applied)
  testthat::expect_true(is.na(out$returns$adjustment_id))
})

testthat::test_that('full extreme exclusion removes donors while volume policy stays separate', {
  cfg<-cfg_test;calendar<-data.table(date=as.Date('2000-01-01')+0:299)
  returns<-data.table(instrument_id='A',date=calendar$date,session=1:300,close_raw=100,
    return=sin(1:300)*.01,market_return=cos(1:300)*.01,has_positive_volume=TRUE,extreme=FALSE)
  returns[session==170,`:=`(return=.7,extreme=TRUE)] # tau -100
  returns[session==169,has_positive_volume:=FALSE]
  cl<-data.table(event_id='e',instrument_id='A',nature_of_business_raw='Gold',mining_candidate=TRUE,
    likely_non_company_security=FALSE,match_confidence='high_label_concordance',historical_security_name='A',
    historical_share_code='A',bulletin_month=as.Date('1999-12-01'),preannouncement_availability_verified=FALSE)
  inputs<-list(calendar=calendar,master=data.table(instrument_id='A'),classifications=cl)
  event<-data.table(event_id='e',event_date=calendar$date[270])
  base<-select_sample(returns,inputs,event,cfg)
  full<-select_sample(returns,inputs,event,cfg,remove_extreme=TRUE)
  base$data[,ar_raw:=return];full$data[,ar_raw:=return]
  b<-residual_donor_panel(base$data[tau>=-250 & tau<=-30],'A',cfg)
  f<-residual_donor_panel(full$data[tau>=-250 & tau<=-30],'A',cfg)
  testthat::expect_true(-100 %in% b$tau)
  testthat::expect_false(-100 %in% f$tau)
  testthat::expect_false(any(f$E==.7))
  testthat::expect_true(-101 %in% f$tau)
  testthat::expect_false(full$data[tau==-100,usable])
  testthat::expect_false(full$data[tau==-100,donor_valid])
  testthat::expect_false(base$data[tau==-101,usable])
  testthat::expect_true(base$data[tau==-101,donor_valid])
  cfg$bootstrap$null_positive_volume<-TRUE
  active<-residual_donor_panel(base$data[tau>=-250 & tau<=-30],'A',cfg)
  testthat::expect_false(-101 %in% active$tau)
})

testthat::test_that('unavailable group inference remains labelled beside supported groups', {
  d<-synthetic_ar(seed=77,shock=0)[instrument_id=='M']
  cfg<-cfg_test;cfg$analysis$windows<-cfg$analysis$windows['primary']
  cars<-complete_cars(d,0,1);cars[,window:='primary']
  inf<-infer_event(d,cars,data.table(event_id='mining_charter_2017'),cfg)
  testthat::expect_equal(nrow(inf),4)
  testthat::expect_true(all(inf[group %in% c('all','mining'),status]=='ok'))
  testthat::expect_true(all(is.na(inf[group %in% c('non_mining','mining_minus_non_mining'),p_value])))
})

testthat::test_that('absolute-tail interval inverts the stated strict rejection rule under skewness and ties', {
  error<-c(rep(1,970),rep(-97/3,30))
  z<-bootstrap_summary(error,-2,.05)
  testthat::expect_lt(z$p_value,.05)
  testthat::expect_lt(z$ci_upper,0)
  testthat::expect_gt(z$legacy_basic_ci_upper,0)
  decisions<-vapply(seq(-35,35,by=.5),function(observed) {
    row<-bootstrap_summary(error,observed,.05)
    identical(row$p_value<.05,row$ci_lower>0 || row$ci_upper<0)
  },TRUE)
  testthat::expect_true(all(decisions))
  zero<-bootstrap_summary(rep(0,99),0,.05)
  testthat::expect_equal(c(zero$ci_lower,zero$ci_upper,zero$p_value),c(0,0,1))
})

testthat::test_that('custom execution selection cannot shrink the registered headline family', {
  cfg<-cfg_test;cfg$analysis$events<-'bbbee_draft_2026'
  inf<-data.table(event_id='bbbee_draft_2026',window='primary',group='all',p_value=.0134)
  testthat::expect_equal(adjust_headline_family(inf,cfg)$holm_primary_p,.067)
  inf[,window:='short']
  testthat::expect_true(is.na(adjust_headline_family(inf,cfg)$holm_primary_p))
  testthat::expect_equal(nrow(headline_family(cfg)),5)
  cfg$analysis$windows$primary<-c(0,5)
  testthat::expect_error(headline_family(cfg),'primary')
})

testthat::test_that('an explicit event result is exported even outside the configured execution list', {
  cfg<-cfg_test;cfg$analysis$events<-'bbbee_draft_2026'
  cfg$paths$outputs<-tempfile('headline-override-');dir.create(file.path(cfg$paths$outputs,'tables'),recursive=TRUE)
  on.exit(unlink(cfg$paths$outputs,recursive=TRUE))
  inf<-data.table(event_id='mining_charter_2017',window='primary',group='mining_minus_non_mining',
    n_mining=2L,n_control=4L,estimate=-.03,ci_lower=-.09,ci_upper=.03,p_value=.17,holm_primary_p=.85,null_dates=221L)
  summary<-data.table(event_id='mining_charter_2017',window='primary',group='all',n=7L,mean_car=-.01)
  out<-write_headline_results(inf,summary,cfg)
  testthat::expect_identical(out$event_id,'mining_charter_2017')
  testthat::expect_equal(out$headline_estimate_pct,-3)
})

testthat::test_that('only verified issuer links change partial issuer weighting', {
  ids<-c('FFA','FFB','OTHER')
  sample<-data.table(instrument_id=ids,reviewed_issuer_id=c('FORTRESS','FORTRESS',NA_character_))
  w<-security_weights(ids,sample,'partial_verified_issuer')
  testthat::expect_equal(w,c(.25,.25,.5))
  testthat::expect_equal(sum(w),1)
  testthat::expect_equal(security_weights(ids,sample),rep(1/3,3))
  source<-data.table(instrument_id='KIO:XJSE:EQU',group='non_mining',classified=TRUE)
  cfg<-cfg_test
  testthat::expect_equal(apply_security_review(source,'mining_charter_2017',cfg)$group,'non_mining')
  cfg$analysis$exposure_definition<-'reviewed_industry_proxy'
  testthat::expect_equal(apply_security_review(source,'mining_charter_2017',cfg)$group,'mining')
  testthat::expect_equal(source$group,'non_mining')
  manufacturer<-data.table(instrument_id='HLM:XJSE:EQU',group='mining',classified=TRUE)
  reviewed<-apply_security_review(manufacturer,'mining_charter_2017',cfg)
  testthat::expect_equal(reviewed$group,'unknown')
  testthat::expect_false(reviewed$classified)
})

testthat::test_that('volatility stress scales event innovations and not OLS estimation error', {
  d<-synthetic_ar(seed=44,shock=0)
  cfg<-cfg_test;cfg$bootstrap$event_sd_multiplier<-1
  a<-bootstrap_portfolio(d,c('M','C'),c(1,-1),0,1,cfg)
  cfg$bootstrap$event_sd_multiplier<-2
  b<-bootstrap_portfolio(d,c('M','C'),c(1,-1),0,1,cfg)
  testthat::expect_equal(b$error,2*a$event_error+a$estimation_error,tolerance=1e-12)
  testthat::expect_equal(a$estimation_error,b$estimation_error)
})

testthat::test_that('placebos cannot fit across their own real event and report feasible counts', {
  cfg<-cfg_test;calendar<-data.table(date=as.Date('2000-01-01')+0:1199)
  events<-data.table(event_id=c('own','other'),event_date=calendar$date[c(364,900)])
  inputs<-list(calendar=calendar,events=events)
  positions<-placebo_positions(364,inputs,cfg,10)
  testthat::expect_false(any(364>=positions-250 & 364<=positions-30))
  testthat::expect_true(all(abs(positions-364)>30))
  testthat::expect_true(all(diff(positions)>=22))
  testthat::expect_identical(positions,placebo_positions(364,inputs,cfg,10))
  testthat::expect_lt(length(positions),10)
})

testthat::test_that('standardized diagnostic matches closed-form correlation adjustment and its interval', {
  scar<-c(-1.4,.3,.7,1.2,-.2,2.1)
  out<-standardized_car_test(scar,.2)
  bmp<-sqrt(length(scar))*mean(scar)/sd(scar)
  factor<-sqrt((1-.2)/(1+(length(scar)-1)*.2))
  testthat::expect_equal(out$bmp_statistic,bmp)
  testthat::expect_equal(out$kp_style_statistic,bmp*factor)
  testthat::expect_equal(out$kp_style_p,2*pt(-abs(bmp*factor),df=length(scar)-1))
  testthat::expect_equal(standardized_car_test(scar,0)$kp_style_statistic,bmp)
  testthat::expect_identical(out$kp_style_p<.05,out$standardized_ci_lower>0 || out$standardized_ci_upper<0)
})

testthat::test_that('the real conversion propagates through OLS, donor residuals and the Reinet CAR', {
  withr::with_dir(getOption('part_a.root'),{
    cfg<-load_config()
    d<-read_pq('../../data/part_a/derived/returns_daily.parquet',cfg)
    d<-d[instrument_id=='RNI:XJSE:EQU']
    cal<-fread('../../data/part_a/source/thesis_data/documentation/trading_calendar.csv')
    t0<-match(as.Date('2018-09-27'),cal$date);d[,tau:=session-t0]
    testthat::expect_equal(d[date==as.Date('2017-11-29'),return_raw],29585/3000-1)
    testthat::expect_equal(d[date==as.Date('2017-11-29'),return],29585/30000-1)
    fit<-lm(return~market_return,data=d[tau>=-250 & tau<=-30 & has_positive_volume==TRUE])
    models<-read_pq('../../data/part_a/derived/market_model_estimates.parquet',cfg)
    stored<-models[event_id=='mining_charter_2018' & instrument_id=='RNI:XJSE:EQU']
    testthat::expect_equal(unname(coef(fit)),c(stored$alpha,stored$beta),tolerance=1e-12)
    testthat::expect_lt(stored$sigma,.02)
    ar<-read_pq('../../data/part_a/derived/abnormal_returns.parquet',cfg)
    ar<-ar[event_id=='mining_charter_2018' & instrument_id=='RNI:XJSE:EQU']
    panel<-residual_donor_panel(ar[tau>=-250 & tau<=-30],'RNI:XJSE:EQU',cfg)
    testthat::expect_lt(max(abs(panel$E)),.2)
    own_car<-d[tau %in% 0:1,sum(return-predict(fit,newdata=.SD))]
    cars<-read_pq('../../data/part_a/derived/firm_event_cars.parquet',cfg)
    testthat::expect_equal(cars[event_id=='mining_charter_2018' & instrument_id=='RNI:XJSE:EQU' & window=='primary',car],own_car,tolerance=1e-12)
  })
})

testthat::test_that('multivariate masked bootstrap agrees with independent explicit refits', {
  set.seed(8301);tau<- -250:1;x<-rnorm(length(tau),sd=.01)
  common<-as.numeric(arima.sim(list(ar=.5),n=length(tau),sd=.01))
  d<-rbindlist(lapply(1:3,function(j) {
    e<-common*j/3+rnorm(length(tau),sd=.004)
    usable<-rep(TRUE,length(tau));usable[which(tau<=-30)[seq(j,210,by=13)]]<-FALSE
    usable[tau==-100]<-FALSE
    y<-.001+j*.3*x+e;fit<-lm(y[tau<=-30 & usable]~x[tau<=-30 & usable])
    data.table(instrument_id=paste0('S',j),tau=tau,market_return=x,usable=usable,
      donor_valid=tau!=-100,ar_raw=y-coef(fit)[1]-coef(fit)[2]*x)
  }))
  ids<-c('S1','S2','S3');w<-c(.5,.5,-1);cfg<-cfg_test;cfg$bootstrap$replications<-199L
  actual<-bootstrap_portfolio(d,ids,w,0,1,cfg)
  pre<-d[tau<=-30];wide<-dcast(pre[donor_valid==TRUE],tau~instrument_id,value.var='ar_raw')
  E<-as.matrix(wide[,..ids]);E<-sweep(E,2,colMeans(E),'-')
  for(j in 1:3) {n<-sum(pre[instrument_id==ids[j],usable]);E[,j]<-E[,j]*sqrt(n/(n-2))}
  starts<-which(vapply(seq_len(nrow(E)-4),function(i)all(diff(wide$tau[i:(i+4)])==1),TRUE))
  set.seed(cfg$bootstrap$seed)
  bs<-matrix(starts[sample.int(length(starts),199*ceiling(252/5),replace=TRUE)],199)
  ix<-matrix(NA_integer_,199,ncol(bs)*5)
  for(k in seq_len(ncol(bs))) ix[,(5*k-4):(5*k)]<-outer(bs[,k],0:4,'+')
  ix<-ix[,1:252]
  manual<-vapply(1:199,function(k) sum(vapply(1:3,function(j) {
    z<-pre[instrument_id==ids[j] & usable==TRUE];position<-match(z$tau,-250:-30)
    fit<-lm.fit(cbind(1,z$market_return),E[ix[k,position],j])
    w[j]*(sum(E[ix[k,251:252],j])-sum(cbind(1,x[tau %in% 0:1])%*%fit$coefficients))
  },0.)),0.)
  testthat::expect_equal(actual$error,manual-mean(manual),tolerance=1e-12)
  testthat::expect_false(-100 %in% actual$donor_tau)
})
