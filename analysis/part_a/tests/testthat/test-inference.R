testthat::test_that('blocks never bridge missing sessions and are deterministic', {
  tau<-c(1:20,30:50)
  ix<-block_indices(tau,25,50,5,99)
  for(k in seq(1,25,5)) testthat::expect_true(all(apply(matrix(tau[ix[,k:(k+4)]],50),1,function(z) all(diff(z)==1))))
  testthat::expect_identical(ix,block_indices(tau,25,50,5,99))
})
testthat::test_that('a single admissible block start is sampled as a position', {
  tau<-c(1L,3L,5L,7L:11L)
  ix<-block_indices(tau,10,100,5,99)
  expected<-matrix(rep(rep(4L:8L,2),each=100),nrow=100)
  testthat::expect_identical(ix,expected)
  for(k in c(1L,6L))
    testthat::expect_true(all(apply(matrix(tau[ix[,k:(k+4L)]],100),1,function(z)all(diff(z)==1))))
  testthat::expect_error(block_indices(c(1,3,5,7,9),5,100,5,99),'No contiguous')
})
testthat::test_that('synchronous common shocks cancel exactly in a spread', {
  d<-synthetic_ar(common=TRUE,shock=0)
  cfg<-cfg_test
  b<-bootstrap_portfolio(d,c('M','C'),c(1,-1),0,1,cfg)
  testthat::expect_lt(max(abs(b$error)),1e-12)
  p<-bootstrap_portfolio(d,'M',1,0,1,cfg)
  testthat::expect_gt(sd(p$error),.005)
})
testthat::test_that('bootstrap OLS prediction error agrees with explicit refitting', {
  d<-synthetic_ar(seed=19,shock=0)[instrument_id=='M']
  cfg<-cfg_test;cfg$bootstrap$replications<-99L;cfg$bootstrap$block_length<-1L
  b<-bootstrap_portfolio(d,'M',1,0,1,cfg)
  pre<-d[tau<=-30];e<-(pre$ar_raw-mean(pre$ar_raw))*sqrt(nrow(pre)/(nrow(pre)-2))
  simulated_tau<-seq.int(cfg$analysis$estimation[1],1L)
  event_columns<-which(simulated_tau %in% 0:1)
  ix<-block_indices(pre$tau,length(simulated_tau),99,1,cfg$bootstrap$seed)
  X<-cbind(1,pre$market_return);xe<-d[tau %in% 0:1,market_return]
  manual<-vapply(1:99,function(k) {
    f<-lm.fit(X,e[ix[k,1:nrow(pre)]]);sum(e[ix[k,event_columns]])-sum(cbind(1,xe)%*%f$coefficients)
  },0.)
  manual<-manual-mean(manual)
  testthat::expect_equal(b$error,manual,tolerance=1e-12)
})
testthat::test_that('five-session bootstrap preserves configured estimation-to-event gaps', {
  d<-synthetic_ar(seed=19,shock=0)[instrument_id=='M']
  cfg<-cfg_test;cfg$bootstrap$replications<-99L;cfg$bootstrap$block_length<-5L
  # Includes anticipation and longer CAR windows, plus a non-baseline fit end.
  cases<-list(c(-30L,0L,1L),c(-30L,-10L,-1L),c(-30L,0L,5L),c(-29L,0L,1L))
  for(case in cases) {
    cfg$analysis$estimation[2]<-case[1];a<-case[2];b<-case[3]
    pre<-d[tau>=cfg$analysis$estimation[1] & tau<=cfg$analysis$estimation[2]]
    e<-(pre$ar_raw-mean(pre$ar_raw))*sqrt(nrow(pre)/(nrow(pre)-2))
    simulated_tau<-seq.int(cfg$analysis$estimation[1],b)
    fit_columns<-which(simulated_tau<=cfg$analysis$estimation[2])
    event_columns<-which(simulated_tau>=a)
    testthat::expect_equal(event_columns[1]-tail(fit_columns,1)-1,a-case[1]-1)
    ix<-block_indices(pre$tau,length(simulated_tau),99,5,cfg$bootstrap$seed)
    X<-cbind(1,pre$market_return);xe<-d[tau>=a & tau<=b,market_return]
    manual<-vapply(seq_len(99),function(k) {
      f<-lm.fit(X,e[ix[k,fit_columns]])
      sum(e[ix[k,event_columns]])-sum(cbind(1,xe)%*%f$coefficients)
    },0.)
    manual<-manual-mean(manual)
    actual<-bootstrap_portfolio(d,'M',1,a,b,cfg)
    testthat::expect_equal(actual$error,manual,tolerance=1e-12)
  }
  testthat::expect_error(bootstrap_portfolio(d,'M',1,-30,-29,cfg_test),'must follow')
})
testthat::test_that('null synthetic simulations have a plausible rejection rate', {
  cfg<-cfg_test;cfg$bootstrap$replications<-199L;cfg$bootstrap$block_length<-1L
  ps<-vapply(1:60,function(k) {
    d<-synthetic_ar(seed=700+k,shock=0)
    b<-bootstrap_portfolio(d,c('M','C'),c(1,-1),0,1,cfg,seed_offset=k)
    cc<-complete_cars(d,0,1);obs<-cc[instrument_id=='M',car]-cc[instrument_id=='C',car]
    (1+sum(abs(b$error)>=abs(obs)))/200
  },0.)
  rate<-mean(ps<.05)
  fwrite(data.table(simulations=60,seed_start=701,replications=199,rejection_rate=rate),
      file.path(getOption('part_a.root'),'../../outputs/part_a/diagnostics/null_calibration.csv'))
  testthat::expect_lte(rate,.15)
})
testthat::test_that('moving blocks retain persistent time-series variability', {
  set.seed(830);tau<- -250:10
  e<-as.numeric(stats::arima.sim(list(ar=.8),n=length(tau),sd=.01))
  d<-data.table(instrument_id='A',tau=tau,date=as.Date('2000-01-01')+seq_along(tau),
    ar_raw=e,ar=e,market_return=rnorm(length(tau),sd=.01),usable=TRUE)
  cfg<-cfg_test;cfg$bootstrap$replications<-999L;cfg$bootstrap$block_length<-1L
  iid<-bootstrap_portfolio(d,'A',1,0,5,cfg,normal_model='market_adjusted')
  cfg$bootstrap$block_length<-5L
  block<-bootstrap_portfolio(d,'A',1,0,5,cfg,normal_model='market_adjusted')
  testthat::expect_gt(sd(block$error),1.3*sd(iid$error))
})
