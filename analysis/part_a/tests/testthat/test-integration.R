testthat::test_that('real 2017 models and CARs independently reconcile to outputs', {
  root<-getOption('part_a.root')
  withr::with_dir(root,{
    cfg<-load_config();cfg$bootstrap$replications<-199L
    # Real source validation is rerun; integration is never skipped for convenience.
    inputs<-validate_inputs(cfg)
    returns<-read_pq('../../data/part_a/derived/returns_daily.parquet',cfg)
    r<-analyse_event(returns,inputs,inputs$events[event_id=='mining_charter_2017'],cfg)
    testthat::expect_gt(sum(r$selected$sample$eligible),20)
    testthat::expect_true(all(r$inference[window=='primary',status]=='ok'))
    for(id in head(r$models[model_ok==TRUE,instrument_id],10)) {
      d<-r$selected$data[instrument_id==id & tau>=-250 & tau<=-30 & usable==TRUE]
      f<-lm(return~market_return,data=d)
      testthat::expect_equal(c(r$models[instrument_id==id,alpha],r$models[instrument_id==id,beta]),unname(coef(f)),tolerance=1e-12)
      e<-r$ar[instrument_id==id & tau %in% 0:1]
      if(nrow(e)==2 && all(is.finite(e$ar)))
        testthat::expect_equal(r$cars[instrument_id==id & window=='primary',car],sum(e$return-predict(f,newdata=e)),tolerance=1e-12)
    }
    testthat::expect_true(all(r$selected$data[usable==TRUE,tau>=-250 & tau<=10]))
  })
})
