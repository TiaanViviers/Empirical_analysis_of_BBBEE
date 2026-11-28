#!/usr/bin/env Rscript
args0<-commandArgs(FALSE);script<-sub('^--file=','',args0[grepl('^--file=',args0)])
if(length(script)) setwd(file.path(dirname(normalizePath(script)),'..'))
# Keep testthat language-state restoration independent of a forced LC_ALL.
Sys.unsetenv('LC_ALL')
# Preload glue: system waldo 0.5.2 otherwise registers the newer glue method
# during its own incomplete namespace load (circular dependency).
suppressPackageStartupMessages(library(glue))
source('R/utils.R');source_modules()
options(part_a.root=getwd())
cfg_test<-load_config();cfg_test$bootstrap$replications<-399L
for(nm in c('corporate_actions','security_review','testing_family','chronology','news'))
  cfg_test$paths[[nm]]<-normalizePath(cfg_test$paths[[nm]])
result<-testthat::test_dir('tests/testthat',reporter='summary',stop_on_failure=FALSE)
tab<-as.data.frame(result)
failed<-sum(tab$failed);errors<-sum(tab$error);skips<-sum(tab$skipped);passed<-sum(tab$passed)
write_md(c('# Executed automated tests','',paste('Test cases:',nrow(tab)),paste('Expectations passed:',passed),
  paste('Failed expectations:',failed),paste('Errors:',errors),paste('Skipped cases:',skips),'',
  'Executed in a clean Rscript session. Includes real-input integration, independent lm/CAR checks, synthetic shocks, synchronous dependence, null calibration and block-gap handling.',
  '',md_table(tab[,intersect(c('file','test','nb','passed','failed','skipped','error'),names(tab))])),
  '../../outputs/part_a/diagnostics/test_summary.md')
fwrite(tab[,intersect(c('file','test','nb','passed','failed','skipped','error'),names(tab)),drop=FALSE],
       '../../outputs/part_a/diagnostics/test_results.csv')
jsonlite::write_json(list(run_time_utc=format(Sys.time(),tz='UTC',usetz=TRUE),
  cases=nrow(tab),passed=passed,failed=failed,errors=errors,skipped=skips,
  inference_sha256=digest::digest(file='../../outputs/part_a/tables/event_study_inference.csv',algo='sha256'),
  analysis_code_sha256=setNames(lapply(analysis_file_paths(),function(f)digest::digest(file=f,algo='sha256')),analysis_file_paths()),
  test_code_sha256=setNames(lapply(list.files('tests',pattern='\\.R$',recursive=TRUE,full.names=TRUE),
    function(f)digest::digest(file=f,algo='sha256')),list.files('tests',pattern='\\.R$',recursive=TRUE,full.names=TRUE))),
  '../../outputs/part_a/diagnostics/test_run_metadata.json',pretty=TRUE,auto_unbox=TRUE)
if(failed+errors==0) write_corrections_report(yaml::read_yaml('config/analysis.yml'))
if(failed+errors>0)quit(status=1)
