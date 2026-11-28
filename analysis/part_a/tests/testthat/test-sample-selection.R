testthat::test_that('actual sample screens use only pre-event historical information', {
  root<-getOption('part_a.root')
  withr::with_dir(root,{
    cfg<-load_config()
    inp<-list(calendar=fread('../../data/part_a/source/thesis_data/documentation/trading_calendar.csv')[,.(date=as.Date(date))],
      master=read_pq('../../data/part_a/source/thesis_data/data/instruments.parquet',cfg,c('instrument_id','company_name')),
      classifications=read_pq('../../data/part_a/source/thesis_data/data/event_industry_classifications.parquet',cfg))
    event<-data.table(event_id='mining_charter_2017',event_date=as.Date('2017-06-15'))
    d<-read_pq('../../data/part_a/derived/returns_daily.parquet',cfg)
    a<-select_sample(d,inp,event,cfg)
    modified<-copy(d);modified[date>event$event_date,return:=99]
    b<-select_sample(modified,inp,event,cfg)
    testthat::expect_identical(a$sample$eligible,b$sample$eligible)
    testthat::expect_true(all(a$sample[eligible==TRUE,n_est]>=180))
    testthat::expect_true(all(a$sample[eligible==TRUE,zero_fraction]<=.2))
    testthat::expect_false(any(a$sample[eligible==TRUE,likely_non_company_security] %in% TRUE))
  })
})
