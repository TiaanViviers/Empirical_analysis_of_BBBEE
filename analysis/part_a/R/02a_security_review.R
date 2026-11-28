# The source classifications are never rewritten. Reviewed alternatives and
# partial issuer links are explicit, event-specific analysis inputs.
read_security_review <- function(cfg) {
  path<-cfg$paths$security_review
  if(is.null(path)) return(data.table())
  ledger<-fread(path,na.strings=c('','NA'))
  ledger[,event_date:=as.Date(event_date)]
  assert_key(ledger,c('event_id','instrument_id'))
  assert(!anyNA(ledger$event_date),'Security review requires explicit event dates')
  assert(all(ledger$reviewed_group %in% c('mining','non_mining','unknown')),'Invalid reviewed group')
  assert(all(!ledger$apply_group_sensitivity | ledger$industry_verified),'Unverified classification cannot be applied')
  assert(all(!ledger$issuer_link_verified | !is.na(ledger$reviewed_issuer_id)),'Verified issuer ID missing')
  ledger
}
apply_security_review <- function(sample,event_id,cfg) {
  ledger<-read_security_review(cfg);target<-event_id
  sample<-copy(sample)
  sample[,`:=`(source_group=group,reviewed_issuer_id=NA_character_,identity_review_status='not reviewed')]
  if(!nrow(ledger)) return(sample)
  review<-ledger[event_id==target]
  hit<-match(sample$instrument_id,review$instrument_id)
  verified_issuer<-!is.na(hit) & review$issuer_link_verified[hit] %in% TRUE
  sample[verified_issuer,reviewed_issuer_id:=review$reviewed_issuer_id[hit[verified_issuer]]]
  sample[!is.na(hit),identity_review_status:=review$review_status[hit[!is.na(hit)]]]
  definition<-or_default(cfg$analysis$exposure_definition,'source_industry_proxy')
  assert(definition %in% c('source_industry_proxy','reviewed_industry_proxy'),'Unknown exposure definition')
  if(definition=='reviewed_industry_proxy') {
    apply<-!is.na(hit) & review$apply_group_sensitivity[hit] %in% TRUE & review$industry_verified[hit] %in% TRUE
    sample[apply,`:=`(group=review$reviewed_group[hit[apply]],classified=review$reviewed_group[hit[apply]]!='unknown')]
  }
  sample
}
