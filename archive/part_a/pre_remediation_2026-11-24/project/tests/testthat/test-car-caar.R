testthat::test_that('known shock gives correct AR, CAR, CAAR and spread', {
  d<-synthetic_ar(5,shock=0);shock<-copy(d);shock[instrument_id=='M' & tau==0,`:=`(ar=ar+.05,ar_raw=ar_raw+.05)]
  a<-complete_cars(d,0,1);b<-complete_cars(shock,0,1)
  testthat::expect_equal(b[instrument_id=='M',car]-a[instrument_id=='M',car],.05)
  testthat::expect_equal(mean(b$car)-mean(a$car),.025)
  testthat::expect_equal(diff(b$car[match(c('C','M'),b$instrument_id)])-diff(a$car[match(c('C','M'),a$instrument_id)]),.05)
  p<-portfolio_series(shock,b$instrument_id,'ar')[tau %in% 0:1]
  testthat::expect_equal(sum(p$value),mean(b$car))
  shock[instrument_id=='M' & tau==1,ar:=NA_real_]
  testthat::expect_false(complete_cars(shock,0,1)[instrument_id=='M',complete])
  testthat::expect_true(is.na(complete_cars(shock,0,1)[instrument_id=='M',car]))
})
