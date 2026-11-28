testthat::test_that('trading windows use supplied sessions and correct inclusive lengths', {
  root<-getOption('part_a.root')
  cal<-fread(file.path(root,'../../data/part_a/source/thesis_data/documentation/trading_calendar.csv'))
  t0<-match(as.Date('2017-06-15'),cal$date)
  testthat::expect_equal(as.character(cal$date[t0]),'2017-06-15')
  testthat::expect_equal(as.character(cal$date[t0+2]),'2017-06-20') # Youth Day then weekend
  testthat::expect_equal(t0+(-250:-30),seq(t0-250,t0-30))
  testthat::expect_length(-250:-30,221)
  testthat::expect_equal(vapply(list(0:1,-1:3,0:5,-10:-1,-10:10),length,1L),c(2L,5L,6L,10L,21L))
  testthat::expect_true(t0-251>=1)
})
