from pathlib import Path
import hashlib,json
import numpy as np,pandas as pd
root=Path(__file__).resolve().parents[2]
d=pd.read_parquet(root/'../../data/part_a/derived/abnormal_returns.parquet')
c=pd.read_parquet(root/'../../data/part_a/derived/firm_event_cars.parquet')
eid='mining_charter_2018'
c=c[(c.event_id==eid)&(c.window=='primary')&c.complete&c.group.isin(['mining','non_mining'])].sort_values('instrument_id')
ids=c.instrument_id.to_list(); w=np.where(c.group=='mining',1/sum(c.group=='mining'),-1/sum(c.group=='non_mining'))
a=d[(d.event_id==eid)&d.instrument_id.isin(ids)].copy()
pre=a[a.tau.between(-250,-30)].copy(); pre.loc[~pre.donor_valid,'ar_raw']=np.nan
panel=pre.pivot(index='tau',columns='instrument_id',values='ar_raw').reindex(columns=ids).dropna(); tau=panel.index.to_numpy(); E=panel.to_numpy().copy(); E-=E.mean(axis=0)
H=np.zeros((221,len(ids))); event=a[a.tau.between(0,1)].drop_duplicates('tau').sort_values('tau'); q=np.array([2,event.market_return.sum()])
for j,i in enumerate(ids):
 f=pre[(pre.instrument_id==i)&pre.usable].sort_values('tau'); X=np.c_[np.ones(len(f)),f.market_return]; E[:,j]*=np.sqrt(len(f)/(len(f)-2)); H[f.tau.to_numpy()+250,j]=w[j]*(X@np.linalg.solve(X.T@X,q))
starts=np.array([i for i in range(len(tau)-4) if np.all(np.diff(tau[i:i+5])==1)])
rng=np.random.default_rng(275); B=19999; z=E@w; Q=E@H.T; vals=[]
for _ in range(B):
 ix=(rng.choice(starts,51)[:,None]+np.arange(5)).ravel()[:252]
 vals.append(z[ix[250:252]].sum()-Q[ix[:221],np.arange(221)].sum())
vals=np.array(vals); vals-=vals.mean(); est=float(c.car.to_numpy()@w); p=(1+sum(abs(vals)>=abs(est)))/(B+1); crit=np.sort(abs(vals))[B+2-int(np.ceil(.05*(B+1)))-1]
print(json.dumps(dict(n_mining=int(sum(c.group=='mining')),n_control=int(sum(c.group=='non_mining')),donor_dates=len(tau),estimate=est,se=float(vals.std(ddof=1)),p=float(p),ci=[float(est-crit),float(est+crit)],draws=B),indent=2))
base=root/'../../archive/part_a/pre_remediation_2026-11-24'
for file,directory in [('source_fingerprints.json',root/'../../data/part_a/source/thesis_data'),('archive_manifest.json',base)]:
 manifest=json.loads((base/file).read_text()); bad=[k for k,v in manifest.items() if not (directory/k).exists() or hashlib.sha256((directory/k).read_bytes()).hexdigest()!=v]
 print(file,'checked',len(manifest),'mismatches',len(bad),bad[:5])
