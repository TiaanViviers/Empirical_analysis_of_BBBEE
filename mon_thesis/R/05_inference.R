# Resample whole residual-date vectors. No independent-security resampling.
block_indices <- function(tau,n_out,B,block_length,seed) {
  n<-length(tau); l<-as.integer(block_length)
  assert(n>=l && l>=1,'Invalid block length')
  starts<-which(vapply(seq_len(n-l+1L),function(i) all(diff(tau[i:(i+l-1L)])==1),logical(1)))
  assert(length(starts)>0,'No contiguous pre-event residual blocks')
  set.seed(seed)
  blocks<-matrix(starts[sample.int(length(starts),B*ceiling(n_out/l),replace=TRUE)],nrow=B)
  out<-matrix(0L,B,ncol(blocks)*l)
  for(k in seq_len(ncol(blocks))) for(j in seq_len(l)) out[,(k-1L)*l+j]<-blocks[,k]+j-1L
  out[,seq_len(n_out),drop=FALSE]
}
residual_donor_panel <- function(pre,ids,cfg) {
  donor<-copy(pre)
  if(!'donor_valid' %in% names(donor)) donor[,donor_valid:=TRUE]
  if(isTRUE(cfg$bootstrap$null_positive_volume)) {
    assert('has_positive_volume' %in% names(donor) || 'volume' %in% names(donor),
      'Active-date donor policy requires volume evidence')
    active<-if('has_positive_volume' %in% names(donor)) donor$has_positive_volume else donor$volume>0
    donor[,donor_valid:=donor_valid & active %in% TRUE]
  }
  donor[,donor_residual:=fifelse(donor_valid %in% TRUE,ar_raw,NA_real_)]
  if(!is.null(cfg$bootstrap$donor_window)) {
    bounds<-cfg$bootstrap$donor_window
    donor<-donor[tau>=bounds[1] & tau<=bounds[2]]
  }
  wide<-dcast(donor,tau~instrument_id,value.var='donor_residual')
  assert(all(ids %in% names(wide)),'Null portfolio missing constituent')
  E<-as.matrix(wide[,..ids]);complete<-apply(is.finite(E),1,all)
  list(E=E[complete,,drop=FALSE],tau=wide$tau[complete])
}

# The primary p-value retains the previous absolute-tail ordering. Its symmetric
# interval now inverts that SAME finite-Monte-Carlo rule, with strict p < alpha.
bootstrap_summary <- function(error,estimate,alpha=.05) {
  assert(length(error)>0 && all(is.finite(error)) && is.finite(estimate),'Invalid bootstrap summary')
  B<-length(error)
  k<-B+2L-ceiling(alpha*(B+1))
  critical<-if(k>B) Inf else sort(abs(error),partial=max(1,k))[max(1,k)]
  q<-quantile(error,c(alpha/2,1-alpha/2),names=FALSE)
  data.table(se=sd(error),ci_lower=estimate-critical,ci_upper=estimate+critical,
    p_value=(1+sum(abs(error)>=abs(estimate)))/(B+1),critical_absolute=critical,
    legacy_basic_ci_lower=estimate-q[2],legacy_basic_ci_upper=estimate-q[1],
    exploratory_equal_tail_p=min(1,2*min((1+sum(error>=estimate))/(B+1),(1+sum(error<=estimate))/(B+1))),
    interval_method='symmetric_absolute_tail_inversion',rejection_rule='p_value < alpha')
}
bootstrap_portfolio <- function(ar,ids,weights,a,b,cfg,seed_offset=0L,normal_model='market_model') {
  assert(length(ids)==length(weights) && length(ids)>0 && !anyDuplicated(ids),'Invalid portfolio weights')
  est<-cfg$analysis$estimation; T<-diff(est)+1L; L<-b-a+1L
  gap<-a-est[2]-1L
  assert(L>=1 && gap>=0,'Event window must follow the estimation window')
  pre<-ar[instrument_id %in% ids & tau>=est[1] & tau<=est[2]]
  panel<-residual_donor_panel(pre,ids,cfg)
  E<-panel$E;tau<-panel$tau
  assert(nrow(E)>=cfg$bootstrap$min_null_dates,paste('Insufficient complete synchronous null dates:',nrow(E)))
  # Zero-centre each firm's null residual distribution, not the observed event.
  E<-sweep(E,2,colMeans(E),'-')
  # Regression parameter error is propagated for each firm's ACTUAL fit dates.
  H<-matrix(0,T,length(ids))
  event_market<-unique(ar[tau>=a & tau<=b,.(tau,market_return)])[order(tau)]
  assert(nrow(event_market)==L && all(is.finite(event_market$market_return)),'Incomplete market event window')
  for(j in seq_along(ids)) {
    fitdays<-pre[instrument_id==ids[j] & usable==TRUE]
    if(normal_model=='market_model') {
      X<-cbind(1,fitdays$market_return)
      assert(nrow(X)>2 && qr(X)$rank==2,'Singular inference design')
      h<-as.vector(X %*% solve(crossprod(X),c(L,sum(event_market$market_return))))
      H[match(fitdays$tau,est[1]:est[2]),j]<-weights[j]*h
      E[,j]<-E[,j]*sqrt(nrow(X)/(nrow(X)-2))
    }
  }
  Q<-E %*% t(H)
  z<-as.vector(E %*% weights)
  # Simulate the intervening sessions as well, then discard them. Appending the
  # event directly to the fit period creates spurious short-lag dependence.
  indices<-block_indices(tau,T+gap+L,cfg$bootstrap$replications,cfg$bootstrap$block_length,
                         cfg$bootstrap$seed+seed_offset)
  event_columns<-T+gap+seq_len(L)
  event_error<-rowSums(matrix(z[indices[,event_columns,drop=FALSE]],nrow=nrow(indices)))
  estimation_error<-numeric(nrow(indices))
  if(normal_model=='market_model') for(t in seq_len(T)) estimation_error<-estimation_error-Q[cbind(indices[,t],t)]
  err<-or_default(cfg$bootstrap$event_sd_multiplier,1)*event_error+estimation_error
  err<-err-mean(err)
  list(error=err,null_dates=nrow(E),block_starts=sum(vapply(seq_len(length(tau)-cfg$bootstrap$block_length+1L),
      function(i) all(diff(tau[i:(i+cfg$bootstrap$block_length-1L)])==1),logical(1))),
      block_length=cfg$bootstrap$block_length,donor_tau=tau,
      event_error=event_error-mean(event_error),estimation_error=estimation_error-mean(estimation_error))
}
infer_event <- function(ar,cars,event,cfg,normal_model='market_model',sample=NULL) {
  mining<-grepl('^mining_charter',as.character(event$event_id))
  groups<-if(mining) c('all','mining','non_mining','mining_minus_non_mining') else 'all'
  rbindlist(lapply(seq_along(cfg$analysis$windows),function(k) {
    w<-names(cfg$analysis$windows)[k]; bounds<-cfg$analysis$windows[[w]]; cc<-cars[window==w]
    rbindlist(lapply(seq_along(groups),function(g) {
      group<-groups[g]
      portfolio<-portfolio_definition(cc,group,sample,or_default(cfg$analysis$weighting,'equal_security'))
      ids<-portfolio$ids;weights<-portfolio$weights;m<-portfolio$mining;c<-portfolio$controls
      observed<-if(length(ids)) sum(cc$car[match(ids,cc$instrument_id)]*weights) else NA_real_
      row<-data.table(event_id=as.character(event$event_id),window=w,group=group,n=length(ids),
        n_mining=length(m),n_control=length(c),estimate=observed,se=NA_real_,ci_lower=NA_real_,ci_upper=NA_real_,p_value=NA_real_,
        critical_absolute=NA_real_,legacy_basic_ci_lower=NA_real_,legacy_basic_ci_upper=NA_real_,
        exploratory_equal_tail_p=NA_real_,interval_method='symmetric_absolute_tail_inversion',rejection_rule='p_value < alpha',
        null_dates=NA_integer_,block_length=cfg$bootstrap$block_length,replications=cfg$bootstrap$replications,
        method='synchronous_residual_moving_blocks_with_firm_refit_error',status='ok')
      out<-tryCatch({
        assert(length(ids)>0 && (group!='mining_minus_non_mining' || (length(m)>0 && length(c)>0)),'Empty event group')
        bootstrap_portfolio(ar,ids,weights,bounds[1],bounds[2],cfg,100*k+g,normal_model)
      },error=function(e) e)
      if(inherits(out,'error')) row[,status:=conditionMessage(out)] else {
        stats<-bootstrap_summary(out$error,observed,cfg$bootstrap$alpha)
        row[, (names(stats)):=stats]
        row[,null_dates:=out$null_dates]
      }
      row[,`:=`(weighting=or_default(cfg$analysis$weighting,'equal_security'),
        event_sd_multiplier=or_default(cfg$bootstrap$event_sd_multiplier,1))]
      row
    }))
  }))
}
