testthat::test_that('many-to-one joins fail rather than multiply prices', {
  x<-data.table(instrument_id=c('A','A','B'),n=1:3)
  y<-data.table(instrument_id=c('A','B'),v=c(1,2))
  testthat::expect_equal(nrow(join_checked(x,y,'instrument_id')),3)
  testthat::expect_error(join_checked(x,rbind(y,y[1]),'instrument_id'),'Duplicate')
})
testthat::test_that('event-specific classifications retain unknowns and historical attributes', {
  master<-data.table(instrument_id=c('A','B'),company_name=c('later A','later B'))
  cl<-data.table(event_id=c('e1','e2'),instrument_id='A',nature_of_business_raw=c('Gold','Bank'),
    mining_candidate=c(TRUE,FALSE),likely_non_company_security=FALSE,match_confidence='high_label_concordance',
    historical_security_name='old A',historical_share_code='A',bulletin_month=as.Date('2017-05-01'),preannouncement_availability_verified=FALSE)
  z<-classify_event(master,cl,'e1')
  testthat::expect_equal(nrow(z),2)
  testthat::expect_equal(z[instrument_id=='A',group],'mining')
  testthat::expect_equal(z[instrument_id=='B',group],'unknown')
  testthat::expect_equal(z[instrument_id=='A',historical_security_name],'old A')
})
