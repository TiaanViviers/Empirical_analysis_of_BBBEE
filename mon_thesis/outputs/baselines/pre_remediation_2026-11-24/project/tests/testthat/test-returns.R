testthat::test_that('adjacent returns distinguish missing, zero, stale and extreme values', {
  cal<-data.table(date=as.Date('2024-01-01')+0:10)
  x<-data.table(instrument_id='A',date=cal$date[c(1:7,9:11)],
     close_raw=c(100,110,NA,120,0,120,120,130,65,260),volume=0)
  z<-compute_returns(x,cal)
  testthat::expect_equal(z$return[2],.1)
  testthat::expect_true(all(is.na(z$return[c(1,3,4,5,6,8)])))
  testthat::expect_equal(z$return[c(7,9,10)],c(0,-.5,3))
  testthat::expect_equal(z$volume,rep(0,10))
  testthat::expect_error(compute_returns(rbind(x,x[1]),cal),'Duplicate')
})
testthat::test_that('missing J203 session does not yield a multi-day daily return', {
  cal<-data.table(date=as.Date(c('2023-12-29','2024-01-02','2024-01-03','2024-01-04')))
  x<-data.table(index_id='J203',date=cal$date[c(1,3,4)],close_raw=c(100,110,121))
  z<-compute_returns(x,cal,'index_id')
  testthat::expect_true(is.na(z$return[2]))
  testthat::expect_equal(z$return[3],.1)
})
