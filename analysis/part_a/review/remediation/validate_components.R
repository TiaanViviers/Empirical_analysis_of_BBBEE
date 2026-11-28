#!/usr/bin/env Rscript
# Isolate inference conventions and the donor-mask defect on preserved old data.
args0<-commandArgs(FALSE);script<-sub('^--file=','',args0[grepl('^--file=',args0)])
setwd(normalizePath(file.path(dirname(script),'../..')))
source('R/utils.R');source_modules();cfg<-load_config()
outdir<-file.path(cfg$paths$outputs,'diagnostics/remediation');dir.create(outdir,recursive=TRUE,showWarnings=FALSE)
baseline<-cfg$paths$comparison_baseline
inputs<-list(events=fread(cfg$paths$events),
  calendar=fread(file.path(cfg$paths$source,'documentation/trading_calendar.csv'))[,.(date=as.Date(date))],
  master=read_pq(file.path(cfg$paths$source,'data/instruments.parquet'),cfg,c('instrument_id','ticker','company_name','issuer_id','security_type')),
  classifications=read_pq(file.path(cfg$paths$source,'data/event_industry_classifications.parquet'),cfg))
inputs$events[,event_date:=as.Date(event_date)];inputs$calendar[,session:=.I]
old_ar<-read_pq(file.path(baseline,'derived/abnormal_returns.parquet'),cfg)
old_cars<-read_pq(file.path(baseline,'derived/firm_event_cars.parquet'),cfg)
old_inf<-fread(file.path(baseline,'tables/event_study_inference.csv'))
inference_only<-rbindlist(lapply(unique(old_inf$event_id),function(eid)
  infer_event(old_ar[event_id==eid],old_cars[event_id==eid],inputs$events[event_id==eid],cfg)))
ref<-merge(old_inf,inference_only,by=c('event_id','window','group'),suffixes=c('_before','_coherent'))
stopifnot(max(abs(ref$p_value_before-ref$p_value_coherent))<1e-12,
  max(abs(ref$estimate_before-ref$estimate_coherent))<1e-12,
  max(abs(ref$ci_lower_before-ref$legacy_basic_ci_lower))<1e-12,
  max(abs(ref$ci_upper_before-ref$legacy_basic_ci_upper))<1e-12)
fwrite(ref,file.path(outdir,'interval_only_comparison_on_original_data.csv'))

old_returns<-read_pq(file.path(baseline,'derived/returns_daily.parquet'),cfg)
review_reference<-fread(file.path(baseline,'diagnostics/independent_review/targeted_sensitivities.csv'))
primary_cfg<-cfg;primary_cfg$analysis$windows<-cfg$analysis$windows['primary']
rows<-list()
for(eid in cfg$analysis$events) {
  ev<-inputs$events[event_id==eid]
  full<-analyse_event(old_returns,inputs,ev,primary_cfg,remove_extreme=TRUE)
  corrected<-headline(full,'full_mask_original_prices')
  legacy_ar<-copy(full$ar);legacy_ar[,donor_valid:=TRUE]
  legacy<-full;legacy$inference<-infer_event(legacy_ar,full$cars,ev,primary_cfg,sample=full$selected$sample)
  before<-headline(legacy,'legacy_fit_event_only_mask_original_prices')
  expected<-review_reference[event_id==eid & specification=='extreme_deletion_in_fit_and_null']
  expected_before<-review_reference[event_id==eid & specification=='supplied_extreme_deletion_fit_only']
  stopifnot(abs(corrected$se-expected$se)<1e-12,abs(corrected$p_value-expected$p_value)<1e-12,
    abs(before$se-expected_before$se)<1e-12,abs(before$p_value-expected_before$p_value)<1e-12)
  rows[[eid]]<-data.table(event_id=eid,legacy_se=before$se,full_exclusion_se=corrected$se,
    legacy_p=before$p_value,full_exclusion_p=corrected$p_value,
    null_dates_before=before$null_dates,null_dates_after=corrected$null_dates,
    reference_se_error=corrected$se-expected$se,status='reviewer diagnostic reproduced on preserved raw-price input')
}
fwrite(rbindlist(rows),file.path(outdir,'extreme_mask_regression_comparison.csv'))

decisions<-rbindlist(lapply(c('event_study_inference','robustness_summary','placebo_results'),function(name) {
  z<-fread(file.path(cfg$paths$outputs,'tables',paste0(name,'.csv')))
  z<-z[is.finite(p_value) & is.finite(ci_lower) & is.finite(ci_upper)]
  inconsistent<-sum((z$p_value<cfg$bootstrap$alpha)!=(z$ci_lower>0 | z$ci_upper<0))
  stopifnot(inconsistent==0)
  data.table(table=name,valid_rows=nrow(z),p_interval_disagreements=inconsistent)
}))
fwrite(decisions,file.path(outdir,'p_interval_consistency.csv'))
placebos<-fread(file.path(cfg$paths$outputs,'tables/placebo_results.csv'))
placebos[,placebo_date:=as.Date(placebo_date)]
own<-inputs$events$event_date[match(placebos$event_id,inputs$events$event_id)]
anchor<-match(own,inputs$calendar$date);pseudo<-match(placebos$placebo_date,inputs$calendar$date)
stopifnot(!any(anchor>=pseudo+cfg$analysis$estimation[1] & anchor<=pseudo+cfg$analysis$estimation[2]))
missing<-placebos[event_id=='ee_final_2025' & placebo_date==as.Date('2023-12-29')]
stopifnot(nrow(missing)==1,missing$n==0,is.na(missing$p_value),missing$status=='Empty event group')
fwrite(data.table(event_id=placebos$event_id,placebo_date=placebos$placebo_date,
  own_event_inside_fit=anchor>=pseudo+cfg$analysis$estimation[1] & anchor<=pseudo+cfg$analysis$estimation[2]),
  file.path(outdir,'placebo_own_event_audit.csv'))
cat('All 55 legacy p-values reproduced; all five mask diagnostics match the independent review; current p/CI decisions coherent.\n')
