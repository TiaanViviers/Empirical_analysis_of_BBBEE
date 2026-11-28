testthat::test_that('published CSV mean CAR and inference estimates agree with derived CARs', {
  root<-getOption('part_a.root')
  withr::with_dir(root,{
    cfg<-load_config()
    # This check is intentionally required after the end-to-end output run.
    testthat::expect_true(file.exists('../../data/part_a/derived/firm_event_cars.parquet'))
    cars<-read_pq('../../data/part_a/derived/firm_event_cars.parquet',cfg)
    summary<-fread('../../outputs/part_a/tables/event_car_summary.csv')
    inf<-fread('../../outputs/part_a/tables/event_study_inference.csv')
    for(k in seq_len(nrow(summary))) {
      z<-summary[k];v<-cars[event_id==z$event_id & window==z$window & complete==TRUE]
      if(z$group!='all')v<-v[group==z$group]
      testthat::expect_equal(nrow(v),z$n)
      if(nrow(v))testthat::expect_equal(mean(v$car),z$mean_car,tolerance=1e-12)
    }
    daily<-read_pq('../../data/part_a/derived/daily_event_aggregates.parquet',cfg)
    for(k in seq_len(nrow(unique(daily[,.(event_id,group)])))) {
      key<-unique(daily[,.(event_id,group)])[k]
      d<-daily[event_id==key$event_id & group==key$group][order(tau)]
      c<-cars[event_id==key$event_id & window=='plot' & complete==TRUE]
      if(key$group=='mining_minus_non_mining') {
        estimate<-mean(c[group=='mining',car])-mean(c[group=='non_mining',car])
        count<-sum(c$group %in% c('mining','non_mining'))
      } else {
        if(key$group!='all')c<-c[group==key$group]
        estimate<-mean(c$car);count<-nrow(c)
      }
      testthat::expect_equal(tail(d$caar,1),estimate,tolerance=1e-12)
      testthat::expect_equal(unique(d$n),count)
    }
    heads<-inf[window=='primary' & ((grepl('^mining_charter',event_id) & group=='mining_minus_non_mining') |
             (!grepl('^mining_charter',event_id) & group=='all'))]
    testthat::expect_equal(heads$holm_primary_p,p.adjust(heads$p_value,'holm',n=5))
    percent<-fread('../../outputs/part_a/tables/headline_results_percent.csv')
    testthat::expect_identical(percent$event_id,heads$event_id)
    testthat::expect_equal(percent$headline_estimate_pct,100*heads$estimate,tolerance=1e-12)
    testthat::expect_equal(percent$ci_lower_pct,100*heads$ci_lower,tolerance=1e-12)
    testthat::expect_equal(percent$ci_upper_pct,100*heads$ci_upper,tolerance=1e-12)
    testthat::expect_equal(percent$p_value,heads$p_value,tolerance=1e-12)
    testthat::expect_equal(percent$holm_primary_p,heads$holm_primary_p,tolerance=1e-12)
    allcars<-summary[window==cfg$analysis$primary_window & group=='all']
    testthat::expect_equal(percent$all_caar_pct,100*allcars$mean_car,tolerance=1e-12)
    testthat::expect_equal(percent$n_all,allcars$n)
    for(k in which(inf$group=='mining_minus_non_mining')) {
      z<-inf[k];s<-summary[event_id==z$event_id & window==z$window]
      testthat::expect_equal(z$estimate,s[group=='mining',mean_car]-s[group=='non_mining',mean_car],tolerance=1e-12)
    }
  })
})
testthat::test_that('percentage headline export creates and refreshes its own output', {
  cfg<-cfg_test;cfg$paths$outputs<-tempfile('headline-export-')
  dir.create(file.path(cfg$paths$outputs,'tables'),recursive=TRUE)
  on.exit(unlink(cfg$paths$outputs,recursive=TRUE))
  inf<-data.table(event_id=c('bbbee_draft_2026','mining_charter_2017'),window='primary',
    group=c('all','mining_minus_non_mining'),n_mining=c(0L,2L),n_control=c(0L,4L),
    estimate=c(.015,-.03),ci_lower=c(.005,-.09),ci_upper=c(.025,.01),
    p_value=c(.0134,.17),holm_primary_p=c(.067,.68),null_dates=221L)
  summary<-data.table(event_id=inf$event_id,window='primary',group='all',n=c(10L,7L),mean_car=c(.015,-.01))
  path<-file.path(cfg$paths$outputs,'tables/headline_results_percent.csv')
  testthat::expect_false(file.exists(path))
  write_headline_results(inf,summary,cfg)
  first<-fread(path)
  testthat::expect_identical(first$event_id,c('mining_charter_2017','bbbee_draft_2026'))
  testthat::expect_equal(first$headline_estimate_pct,c(-3,1.5))
  testthat::expect_equal(first$all_caar_pct,c(-1,1.5))
  testthat::expect_equal(first$p_value,c(.17,.0134))
  inf[event_id=='bbbee_draft_2026',`:=`(estimate=.02,ci_lower=.01,ci_upper=.03,p_value=.5,holm_primary_p=1)]
  summary[event_id=='bbbee_draft_2026',mean_car:=.02]
  write_headline_results(inf,summary,cfg)
  current<-fread(path)[event_id=='bbbee_draft_2026']
  testthat::expect_equal(current$headline_estimate_pct,2)
  testthat::expect_equal(current$all_caar_pct,2)
  testthat::expect_equal(c(current$ci_lower_pct,current$ci_upper_pct),c(1,3))
  testthat::expect_equal(c(current$p_value,current$holm_primary_p),c(.5,1))
})
