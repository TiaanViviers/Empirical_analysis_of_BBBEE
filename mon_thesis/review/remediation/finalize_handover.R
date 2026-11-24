#!/usr/bin/env Rscript
args0<-commandArgs(FALSE);script<-sub('^--file=','',args0[grepl('^--file=',args0)])
setwd(normalizePath(file.path(dirname(script),'../..')))
source('R/utils.R');source_modules();cfg<-load_config()
outdir<-file.path(cfg$paths$outputs,'diagnostics/remediation');dir.create(outdir,recursive=TRUE,showWarnings=FALSE)
baseline<-cfg$paths$comparison_baseline
hash<-function(path) digest::digest(file=path,algo='sha256')
original<-jsonlite::read_json(file.path(baseline,'source_fingerprints.json'),simplifyVector=TRUE)
source_ok<-all(vapply(names(original),function(name)
  identical(hash(file.path(cfg$paths$source,name)),original[[name]]),TRUE))
archive<-jsonlite::read_json(file.path(baseline,'archive_manifest.json'),simplifyVector=TRUE)
missing<-names(archive)[!file.exists(file.path(baseline,names(archive)))]
changed<-names(archive)[vapply(names(archive),function(name) {
  path<-file.path(baseline,name)
  file.exists(path) && !identical(hash(path),archive[[name]])
},TRUE)]
events_ok<-identical(hash(cfg$paths$events),hash(file.path(baseline,'project/research/events.csv')))
metadata<-jsonlite::read_json(file.path(cfg$paths$outputs,'diagnostics/run_metadata.json'),simplifyVector=TRUE)
code_ok<-all(vapply(names(metadata$code_sha256),function(name)identical(hash(name),metadata$code_sha256[[name]]),TRUE))
preservation<-list(source_package_unchanged=source_ok,event_register_unchanged=events_ok,
  baseline_archive_files_checked=length(archive),baseline_files_missing=missing,baseline_files_changed=changed,
  current_run_code_config_ledgers_match=code_ok)
jsonlite::write_json(preservation,file.path(outdir,'preservation_and_provenance.json'),pretty=TRUE,auto_unbox=TRUE)
assert(source_ok && events_ok && !length(missing) && !length(changed) && code_ok,
  'Preservation/provenance check failed; inspect diagnostics/remediation/preservation_and_provenance.json')
status<-write_corrections_report(cfg)
assert(status$tests_current,'Tests do not match current code/results: rerun tests/testthat.R')
assert(status$complete,'Full handover requires --all')
cat('Full corrected output, matched tests, original-source preservation and baseline archive verified.\n')
