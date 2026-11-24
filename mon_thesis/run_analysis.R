#!/usr/bin/env Rscript
# Works from the research project root or by absolute/relative path from elsewhere.
args0<-commandArgs(FALSE);script<-sub('^--file=','',args0[grepl('^--file=',args0)])
if(length(script)) setwd(dirname(normalizePath(script)))
Sys.setenv(TZ='Africa/Johannesburg')
source('R/utils.R');source_modules()
args<-commandArgs(TRUE)
assert(length(args)>0,'Usage: Rscript run_analysis.R --event ID | --all | --smoke')
assert(all(args %in% c('--all','--smoke','--event','--config','--no-robustness') | !startsWith(args,'--')),'Unknown argument')
config_path<-if('--config' %in% args) args[match('--config',args)+1L] else 'config/analysis.yml'
cfg<-load_config(config_path)
smoke<-'--smoke' %in% args
if(smoke) cfg$bootstrap$replications<-199L
log_message('Validating immutable package and event register')
inputs<-validate_inputs(cfg)
log_message('Constructing and independently checking calendar-adjacent returns')
data<-construct_returns(cfg,inputs)
events<-if('--all' %in% args) cfg$analysis$events else if('--event' %in% args) args[match('--event',args)+1L] else if(smoke) 'mining_charter_2017' else stop('No analysis mode supplied')
assert(length(events)>0 && all(events %in% inputs$events$event_id),'Unknown/missing event')
results<-list();statuses<-list()
for(eid in events) {
  log_message('Estimating',eid)
  event<-inputs$events[event_id==eid]
  result<-tryCatch(analyse_event(data$returns,inputs,event,cfg),error=function(e)e)
  if(inherits(result,'error')) {
    statuses[[eid]]<-data.table(event_id=eid,status='failed',detail=conditionMessage(result))
    log_message('FAILED',eid,conditionMessage(result))
  } else {
    results[[eid]]<-result
    statuses[[eid]]<-data.table(event_id=eid,status='estimated',detail=paste(sum(result$selected$sample$eligible),'estimation-eligible securities'))
    log_message(eid, statuses[[eid]]$detail,'; primary inference:',paste(result$inference[window==cfg$analysis$primary_window,status],collapse='; '))
  }
}
write_table(rbindlist(statuses),'event_run_status',cfg,'diagnostics')
assert(length(results)>0,'All selected events failed; see event_run_status.csv')
robust<-if('--no-robustness' %in% args) list(summary=data.table(),placebos=data.table(),status='explicitly disabled') else run_robustness(results,data$returns,inputs,cfg,smoke)
if('--no-robustness' %in% args) {
  empty <- headline(results[[1]],'disabled')[0]
  write_table(empty,'robustness_summary',cfg)
  write_table(empty,'placebo_results',cfg)
  write_md(c('# Robustness findings','','Explicitly disabled for this run.'),file.path(cfg$paths$outputs,'reports/robustness_findings.md'))
}
log_message('Generating tables, figures and research handover')
generate_outputs(results,robust,inputs,data,cfg,smoke)
quality_diagnostics(results,inputs,cfg)
write_research_diagnostics(results,robust,inputs,data,cfg)
standardized<-rbindlist(lapply(results,function(r) tryCatch(standardized_car_diagnostic(r,cfg),
  error=function(e)data.table(event_id=r$event$event_id,status=conditionMessage(e)))),fill=TRUE)
write_table(standardized,'standardized_car_diagnostics',cfg)
run_python(cfg,c('scripts/parquet_bridge.py','fingerprint',cfg$paths$source,file.path(cfg$paths$outputs,'diagnostics/source_fingerprints_after.json')))
assert(identical(readLines(file.path(cfg$paths$outputs,'diagnostics/source_fingerprints_before.json')),
                 readLines(file.path(cfg$paths$outputs,'diagnostics/source_fingerprints_after.json'))),'SOURCE MODIFICATION DETECTED')
writeLines(capture.output(sessionInfo()),file.path(cfg$paths$outputs,'diagnostics/session_info.txt'))
writeLines(yaml::as.yaml(cfg),file.path(cfg$paths$outputs,'diagnostics/effective_configuration.yml'))
files<-analysis_file_paths(config_path)
meta<-list(run_time_utc=format(Sys.time(),tz='UTC',usetz=TRUE),mode=if(smoke)'smoke' else 'full',events=events,
  source_manifest_sha256=digest::digest(file=file.path(cfg$paths$source,'manifest.json'),algo='sha256'),
  code_sha256=setNames(lapply(files,function(f)digest::digest(file=f,algo='sha256')),files),
  effective_config=cfg,R=R.version.string)
jsonlite::write_json(meta,file.path(cfg$paths$outputs,'diagnostics/run_metadata.json'),pretty=TRUE,auto_unbox=TRUE)
write_corrections_report(cfg)
log_message('Finished. Source fingerprints unchanged. See outputs/reports/part_a_preliminary_results.md')
if(any(vapply(statuses,function(x)x$status=='failed',logical(1)))) quit(status=1)
