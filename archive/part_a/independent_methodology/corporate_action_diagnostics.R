# Hypothetical source-backed return corrections in memory only; NOT a repair
# of the source data or a substitute for a complete adjustment history.
args0<-commandArgs(FALSE);script<-sub('^--file=','',args0[grepl('^--file=',args0)])
setwd(normalizePath(file.path(dirname(script),'../..')))
source('R/utils.R');source_modules()
cfg<-yaml::read_yaml('config/analysis.yml');cfg$analysis$windows<-cfg$analysis$windows['primary']
outdir<-'outputs/diagnostics/independent_review'
returns<-read_pq('data/derived/returns_daily.parquet',cfg)
inputs<-list(events=fread('research/events.csv'),
  calendar=fread('data/thesis_data/documentation/trading_calendar.csv')[,.(date=as.Date(date))],
  master=read_pq('data/thesis_data/data/instruments.parquet',cfg,
    c('instrument_id','ticker','company_name','issuer_id','security_type')),
  classifications=read_pq('data/thesis_data/data/event_industry_classifications.parquet',cfg))
inputs$events[,event_date:=as.Date(event_date)];inputs$calendar[,session:=.I]
results<-list();details<-list()
for(eid in c('mining_charter_2018','bbbee_draft_2026')) {
  ev<-inputs$events[event_id==eid]
  base<-analyse_event(returns,inputs,ev,cfg)
  results[[paste0(eid,'base')]]<-headline(base,'baseline')
  revised<-copy(returns)
  if(eid=='mining_charter_2018') {
    # JSE/FTSE notice of 22 November 2017: 10 depositary receipts replaced
    # by 1 underlying ordinary share on 29 November. Unit-free correction.
    id<-'RNI:XJSE:EQU';day<-as.Date('2017-11-29')
    before<-revised[instrument_id==id & date==day,return]
    revised[instrument_id==id & date==day,return:=(return+1)/10-1]
    assumption<-'10 old depositary receipts = 1 new share; price units cancel'
  } else {
    # Issuer announcement confirms R20 ex-capital distribution 23 July 2025.
    # This illustration explicitly assumes Close is in cents, consistent with
    # observed 2110 -> 105. Provider units are NOT independently certified.
    id<-'MTNZF:XJSE:EQU';day<-as.Date('2025-07-23')
    before<-revised[instrument_id==id & date==day,return]
    previous<-revised[instrument_id==id & date==as.Date('2025-07-22'),close_raw]
    revised[instrument_id==id & date==day,return:=(close_raw+2000)/previous-1]
    assumption<-'R20 capital return = 2000 Close units; cents assumption unverified'
  }
  revised[instrument_id==id & date==day,extreme:=abs(return)>.3]
  after<-revised[instrument_id==id & date==day,return]
  adjusted<-analyse_event(revised,inputs,ev,cfg)
  z<-headline(adjusted,'single_source_backed_action_diagnostic');z[,assumption:=assumption]
  results[[paste0(eid,'adj')]]<-z
  z<-merge(base$models[instrument_id==id],adjusted$models[instrument_id==id],
    by=c('event_id','instrument_id'),suffixes=c('_before','_after'))
  z[,`:=`(action_date=day,raw_return=before,diagnostic_return=after,assumption=assumption)]
  details[[eid]]<-z
  no_id<-analyse_event(returns[instrument_id!=id],inputs,ev,cfg)
  results[[paste0(eid,'omit')]]<-headline(no_id,paste0('omit_',id))
}
fwrite(rbindlist(results,fill=TRUE),file.path(outdir,'corporate_action_sensitivities.csv'))
fwrite(rbindlist(details,fill=TRUE),file.path(outdir,'corporate_action_model_changes.csv'))
print(rbindlist(results,fill=TRUE)[,.(event_id,specification,n,estimate,se,p_value,ci_lower,ci_upper)])
