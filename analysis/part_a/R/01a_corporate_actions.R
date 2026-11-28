# Versioned, reversible corrections to analytical returns; source prices stay raw.
read_corporate_actions <- function(cfg) {
  path<-cfg$paths$corporate_actions
  if(is.null(path)) return(data.table())
  ledger<-fread(path,na.strings=c('','NA'))
  ledger[,effective_date:=as.Date(effective_date)]
  assert_key(ledger,'action_id');assert_key(ledger,c('instrument_id','effective_date'))
  applied<-ledger[apply_price_correction %in% TRUE]
  assert(all(applied$verification_status=='verified_conversion') &&
    all(applied$action_type=='security_unit_conversion'),'Only verified unit conversions may be applied')
  assert(all(is.finite(applied$price_multiplier) & applied$price_multiplier>0),'Invalid conversion factor')
  assert(all(!is.na(applied$evidence_url) & startsWith(applied$evidence_url,'https://')),'Verified conversion needs a source')
  assert(all(is.na(applied$cash_distribution)),'Cash distributions are not silently included in price returns')
  ledger
}
apply_corporate_actions <- function(returns,ledger,enabled=TRUE,extreme_threshold=.30) {
  x<-copy(returns)
  if(!'return_raw' %in% names(x)) x[,return_raw:=return]
  x[,`:=`(return=return_raw,adjustment_id=NA_character_,adjustment_factor=1)]
  audit<-copy(ledger)
  if(nrow(audit)) {
    audit[,`:=`(observed_raw_return=NA_real_,analytical_return=NA_real_,applied=FALSE)]
    for(k in seq_len(nrow(audit))) {
      row<-audit[k]
      index<-which(x$instrument_id==row$instrument_id & x$date==row$effective_date)
      if(!length(index)) {
        assert(!enabled || !isTRUE(row$apply_price_correction),'Approved conversion observation is missing')
        next
      }
      assert(length(index)==1,'Conversion key is not unique')
      audit[k,observed_raw_return:=x$return_raw[index]]
      if(enabled && isTRUE(row$apply_price_correction)) {
        assert(row$verification_status=='verified_conversion' && row$action_type=='security_unit_conversion' &&
          is.finite(row$price_multiplier) && row$price_multiplier>0 && !is.na(row$evidence_url) &&
          startsWith(row$evidence_url,'https://') && is.na(row$cash_distribution),
          'Unverified adjustment cannot be applied')
        assert(is.finite(x$return_raw[index]),'Cannot adjust a missing/nonadjacent return')
        x[index,`:=`(return=(return_raw+1)/row$price_multiplier-1,
          adjustment_id=row$action_id,adjustment_factor=row$price_multiplier)]
        audit[k,applied:=TRUE]
      }
      audit[k,analytical_return:=x$return[index]]
    }
  }
  x[,`:=`(extreme_raw=abs(return_raw)>extreme_threshold,extreme=abs(return)>extreme_threshold)]
  list(returns=x,audit=audit)
}
