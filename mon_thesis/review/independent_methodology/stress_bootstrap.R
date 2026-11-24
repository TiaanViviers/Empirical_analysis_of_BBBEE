# Controlled null experiments, distinct from the project's unit-test DGP.
# This uses a scalar portfolio regression: one security is enough to test the
# temporal null/forecast-error calibration. Multivariate mask algebra is tested
# separately in audit_inference.R. No claim of real-world size control follows.
args0<-commandArgs(FALSE);script<-sub('^--file=','',args0[grepl('^--file=',args0)])
setwd(normalizePath(file.path(dirname(script),'../..')))
source('R/utils.R');source_modules()
cfg<-yaml::read_yaml('config/analysis.yml');cfg$bootstrap$replications<-999L
outdir<-'outputs/diagnostics/independent_review'
N<-500L;B<-cfg$bootstrap$replications;tau<- -250:1
scenarios<-data.table(name=c('iid_gaussian','ar_0.6_block5','ar_0.6_block10',
  'student_t5','centered_lognormal','event_sd_doubled'),
  distribution=c('gaussian','ar','ar','student','lognormal','gaussian'),
  block=c(5,5,10,5,5,5),event_scale=c(1,1,1,1,1,2))
rows<-list()
for(s in seq_len(nrow(scenarios))) {
  scenario<-scenarios[s]
  cat('Scenario',scenario$name,'\n')
  ccfg<-cfg;ccfg$bootstrap$block_length<-scenario$block
  for(k in seq_len(N)) {
    set.seed(640000+k)
    x<-rnorm(length(tau),sd=.01)
    dist<-scenario$distribution
    e<-if(dist=='student') rt(length(tau),5)*sqrt(3/5)*.01 else if(dist=='lognormal')
      (exp(rnorm(length(tau)))-exp(.5))/sqrt((exp(1)-1)*exp(1))*.01 else if(dist=='ar') {
        shocks<-rnorm(length(tau)+400,sd=.01*sqrt(1-.6^2));z<-numeric(length(shocks))
        for(j in 2:length(z)) z[j]<-.6*z[j-1]+shocks[j]
        tail(z,length(tau))
      } else rnorm(length(tau),sd=.01)
    e[tau>=0]<-e[tau>=0]*scenario$event_scale
    y<-.0003+.8*x+e
    fitmask<-tau<=-30
    f<-lm.fit(cbind(1,x[fitmask]),y[fitmask])
    residual<-as.vector(y-cbind(1,x)%*%f$coefficients)
    d<-data.table(instrument_id='P',tau=tau,market_return=x,usable=TRUE,ar_raw=residual)
    observed<-sum(residual[tau %in% 0:1])
    boot<-bootstrap_portfolio(d,'P',1,0,1,ccfg,seed_offset=k)
    pabs<-(1+sum(abs(boot$error)>=abs(observed)))/(B+1)
    peq<-min(1,2*min((1+sum(boot$error>=observed))/(B+1),(1+sum(boot$error<=observed))/(B+1)))
    q<-quantile(boot$error,c(.025,.975),names=FALSE)
    rows[[paste(s,k)]]<-data.table(scenario=scenario$name,trial=k,seed=640000+k,
      observed=observed,p_absolute=pabs,p_equal_tail=peq,ci_covers_zero=(observed-q[2]<=0 && observed-q[1]>=0))
  }
}
draws<-rbindlist(rows)
summary<-draws[,.(simulations=.N,bootstrap_draws=B,rejection_absolute=mean(p_absolute<.05),
  rejection_equal_tail=mean(p_equal_tail<.05),coverage_basic=mean(ci_covers_zero)),by=scenario]
# Wilson interval quantifies Monte Carlo uncertainty of the size experiment.
summary[,`:=`(mc_lower=(rejection_absolute+1.96^2/(2*simulations)-1.96*sqrt(rejection_absolute*(1-rejection_absolute)/simulations+1.96^2/(4*simulations^2)))/(1+1.96^2/simulations),
  mc_upper=(rejection_absolute+1.96^2/(2*simulations)+1.96*sqrt(rejection_absolute*(1-rejection_absolute)/simulations+1.96^2/(4*simulations^2)))/(1+1.96^2/simulations))]
fwrite(draws,file.path(outdir,'synthetic_null_trials.csv'))
fwrite(summary,file.path(outdir,'synthetic_null_summary.csv'))
print(summary)
