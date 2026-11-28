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
bootstrap_portfolio <- function(ar,ids,weights,a,b,cfg,seed_offset=0L,normal_model='market_model') {
  assert(length(ids)==length(weights) && length(ids)>0 && !anyDuplicated(ids),'Invalid portfolio weights')
  est<-cfg$analysis$estimation; T<-diff(est)+1L; L<-b-a+1L
  gap<-a-est[2]-1L
  assert(L>=1 && gap>=0,'Event window must follow the estimation window')
  pre<-ar[instrument_id %in% ids & tau>=est[1] & tau<=est[2]]
  wide<-dcast(pre,tau~instrument_id,value.var='ar_raw')
  assert(all(ids %in% names(wide)),'Null portfolio missing constituent')
  E<-as.matrix(wide[,..ids]); complete<-apply(is.finite(E),1,all)
  E<-E[complete,,drop=FALSE]; tau<-wide$tau[complete]
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
  err<-rowSums(matrix(z[indices[,event_columns,drop=FALSE]],nrow=nrow(indices)))
  if(normal_model=='market_model') for(t in seq_len(T)) err<-err-Q[cbind(indices[,t],t)]
  err<-err-mean(err)
  list(error=err,null_dates=nrow(E),block_starts=sum(vapply(seq_len(length(tau)-cfg$bootstrap$block_length+1L),
      function(i) all(diff(tau[i:(i+cfg$bootstrap$block_length-1L)])==1),logical(1))),
      block_length=cfg$bootstrap$block_length)
}
infer_event <- function(ar,cars,event,cfg,normal_model='market_model') {
  mining<-grepl('^mining_charter',as.character(event$event_id))
  groups<-if(mining) c('all','mining','non_mining','mining_minus_non_mining') else 'all'
  rbindlist(lapply(seq_along(cfg$analysis$windows),function(k) {
    w<-names(cfg$analysis$windows)[k]; bounds<-cfg$analysis$windows[[w]]; cc<-cars[window==w]
    rbindlist(lapply(seq_along(groups),function(g) {
      group<-groups[g]
      if(group=='mining_minus_non_mining') {
        m<-group_ids(cc,'mining'); c<-group_ids(cc,'non_mining'); ids<-c(m,c)
        weights<-c(rep(1/max(1,length(m)),length(m)),rep(-1/max(1,length(c)),length(c)))
      } else {
        ids<-group_ids(cc,group);weights<-rep(1/max(1,length(ids)),length(ids))
        m<-if(group=='mining') ids else character();c<-if(group=='non_mining') ids else character()
      }
      observed<-if(length(ids)) sum(cc$car[match(ids,cc$instrument_id)]*weights) else NA_real_
      row<-data.table(event_id=as.character(event$event_id),window=w,group=group,n=length(ids),
        n_mining=length(m),n_control=length(c),estimate=observed,se=NA_real_,ci_lower=NA_real_,ci_upper=NA_real_,p_value=NA_real_,
        null_dates=NA_integer_,block_length=cfg$bootstrap$block_length,replications=cfg$bootstrap$replications,
        method='synchronous_residual_moving_blocks_with_firm_refit_error',status='ok')
      out<-tryCatch({
        assert(length(ids)>0 && (group!='mining_minus_non_mining' || (length(m)>0 && length(c)>0)),'Empty event group')
        bootstrap_portfolio(ar,ids,weights,bounds[1],bounds[2],cfg,100*k+g,normal_model)
      },error=function(e) e)
      if(inherits(out,'error')) row[,status:=conditionMessage(out)] else {
        q<-quantile(out$error,c(cfg$bootstrap$alpha/2,1-cfg$bootstrap$alpha/2),names=FALSE)
        row[,`:=`(se=sd(out$error),ci_lower=observed-q[2],ci_upper=observed-q[1],
          p_value=(1+sum(abs(out$error)>=abs(observed)))/(length(out$error)+1),null_dates=out$null_dates)]
      }
      row
    }))
  }))
}
