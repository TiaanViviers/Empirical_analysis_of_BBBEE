#!/usr/bin/env Rscript
# Synchronous security-level calibration; no production tables are overwritten.
args0<-commandArgs(FALSE);script<-sub('^--file=','',args0[grepl('^--file=',args0)])
setwd(normalizePath(file.path(dirname(script),'../..')))
source('R/utils.R');source_modules();cfg<-load_config()
outdir<-file.path(cfg$paths$outputs,'diagnostics/remediation');dir.create(outdir,recursive=TRUE,showWarnings=FALSE)
N<-cfg$calibration$trials;B<-cfg$calibration$replications;S<-cfg$calibration$securities
if('--quick' %in% commandArgs(TRUE)) {N<-40L;B<-199L}
cfg$bootstrap$replications<-B
tau<-seq(cfg$analysis$estimation[1],1);T<-length(tau);est<-tau<=cfg$analysis$estimation[2]
first<-seq_len(floor(S/2));last<-setdiff(seq_len(S),first)
ids<-paste0('S',seq_len(S));weights<-list(all=rep(1/S,S),
  mining_minus_control=c(rep(1/length(first),length(first)),rep(-1/length(last),length(last))))
scenarios<-c('stable_gaussian','serial_AR06','heavy_tails_t5','centered_lognormal',
  'event_all_residual_sd2','event_factor_sd2')
rows<-list()
for(s in seq_along(scenarios)) {
  name<-scenarios[s];cat('Calibrating',name,'trials',N,'draws',B,'\n')
  for(k in seq_len(N)) {
    set.seed(cfg$calibration$seed+k) # paired scenarios; independent across trials
    x<-rnorm(T,sd=.01)
    z<-matrix(rnorm((T+400)*(S+2)),T+400,S+2)
    if(name=='heavy_tails_t5') z<-matrix(rt((T+400)*(S+2),5)*sqrt(3/5),T+400,S+2)
    if(name=='centered_lognormal') z<-(exp(z)-exp(.5))/sqrt((exp(1)-1)*exp(1))
    if(name=='serial_AR06') for(t in 2:nrow(z)) z[t,]<-.6*z[t-1,]+sqrt(1-.6^2)*z[t,]
    z<-tail(z,T)
    common<-matrix(z[,1],T,S)*.004
    sector<-matrix(0,T,S);sector[,first]<-z[,2]*.006
    idio<-z[,2+seq_len(S),drop=FALSE]*.008
    if(name=='event_factor_sd2') {common[tau>=0,]<-common[tau>=0,]*2;sector[tau>=0,]<-sector[tau>=0,]*2}
    e<-common+sector+idio
    if(name=='event_all_residual_sd2') e[tau>=0,]<-e[tau>=0,]*2
    models<-list();series<-list()
    for(j in seq_len(S)) {
      usable<-rep(TRUE,T)
      usable[which(est)[seq(j,210,by=17)]]<-FALSE
      y<-.0001+(.6+j/S)*x+e[,j]
      X<-cbind(1,x[est & usable]);fit<-lm.fit(X,y[est & usable])
      residual<-y-as.vector(cbind(1,x)%*%fit$coefficients)
      models[[j]]<-data.table(instrument_id=ids[j],sigma=sqrt(sum(fit$residuals^2)/(nrow(X)-2)))
      series[[j]]<-data.table(instrument_id=ids[j],tau=tau,market_return=x,usable=usable,
        ar_raw=residual,ar=fifelse(usable,residual,NA_real_),donor_valid=TRUE,
        group=if(j %in% first)'mining' else 'non_mining')
    }
    d<-rbindlist(series);mm<-rbindlist(models)
    cc<-d[tau %in% 0:1,.(car=sum(ar)),by=.(instrument_id,group)]
    record<-data.table(scenario=name,trial=k,seed=cfg$calibration$seed+k)
    for(port in names(weights)) {
      observed<-sum(cc$car[match(ids,cc$instrument_id)]*weights[[port]])
      boot<-bootstrap_portfolio(d,ids,weights[[port]],0,1,cfg,k)
      stat<-bootstrap_summary(boot$error,observed,cfg$bootstrap$alpha)
      record[,(paste0(port,'_p')):=stat$p_value]
      record[,(paste0(port,'_coverage')):=stat$ci_lower<=0 & stat$ci_upper>=0]
      record[,(paste0(port,'_legacy_basic_coverage')):=stat$legacy_basic_ci_lower<=0 & stat$legacy_basic_ci_upper>=0]
    }
    pre<-d[tau<=-30];wide<-dcast(pre,tau~instrument_id,value.var='ar_raw')
    E<-as.matrix(wide[,..ids]);C<-cor(E);rbar<-mean(C[upper.tri(C)])
    q<-c(2,sum(x[tau %in% 0:1]))
    scales<-vapply(seq_len(S),function(j) {
      dd<-pre[instrument_id==ids[j] & usable==TRUE];X<-cbind(1,dd$market_return)
      mm[instrument_id==ids[j],sigma]*sqrt(2+as.numeric(t(q)%*%solve(crossprod(X),q)))
    },0.)
    kp<-standardized_car_test(cc$car[match(ids,cc$instrument_id)]/scales,rbar)
    record[,`:=`(bmp_all_p=kp$bmp_p,kp_style_all_p=kp$kp_style_p,
      kp_style_all_coverage=kp$standardized_ci_lower<=0 & kp$standardized_ci_upper>=0)]
    rows[[paste(s,k)]]<-record
  }
}
trials<-rbindlist(rows)
summary<-rbindlist(lapply(c('all','mining_minus_control','bmp_all','kp_style_all'),function(method) {
  pcol<-paste0(method,'_p');coverage<-paste0(method,'_coverage')
  z<-trials[,.(trials=.N,rejection_rate=mean(get(pcol)<.05),
    interval_coverage=if(coverage %in% names(trials)) mean(get(coverage)) else NA_real_),by=scenario]
  z[,`:=`(method=method,bootstrap_draws=B,securities=S)]
  z
}))
wilson<-function(p,n,sign) (p+1.96^2/(2*n)+sign*1.96*sqrt(p*(1-p)/n+1.96^2/(4*n^2)))/(1+1.96^2/n)
summary[,`:=`(rejection_mc_lower=wilson(rejection_rate,trials,-1),rejection_mc_upper=wilson(rejection_rate,trials,1),
  coverage_mc_lower=wilson(interval_coverage,trials,-1),coverage_mc_upper=wilson(interval_coverage,trials,1))]
fwrite(trials,file.path(outdir,'synchronous_calibration_trials.csv'))
fwrite(summary,file.path(outdir,'synchronous_calibration_summary.csv'))
files<-c('review/remediation/calibrate_inference.R','R/05_inference.R','R/11_standardized_diagnostics.R','config/analysis.yml')
jsonlite::write_json(list(trials_per_scenario=N,replications=B,securities=S,
  seed=cfg$calibration$seed,mode=if(N<cfg$calibration$trials)'quick' else 'full',
  code_sha256=setNames(lapply(files,function(f)digest::digest(file=f,algo='sha256')),files)),
  file.path(outdir,'calibration_metadata.json'),pretty=TRUE,auto_unbox=TRUE)
print(summary)
