"""Read-only audit of placebos, residual dates, test families and decision rules."""
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'outputs/diagnostics/independent_review'
p=pd.read_csv(ROOT/'outputs/tables/placebo_results.csv',parse_dates=['placebo_date'])
cal=pd.read_csv(ROOT/'data/thesis_data/documentation/trading_calendar.csv',parse_dates=['date'])
positions=pd.Series(np.arange(len(cal)),index=cal.date)
ev=pd.read_csv(ROOT/'research/events.csv',parse_dates=['event_date'])
eventpos=ev.set_index('event_id').event_date.map(positions)
rows=[]
for eid,z in p.groupby('event_id',sort=False):
    ix=np.sort(z.placebo_date.map(positions).to_numpy())
    valid=z.status.eq('ok'); anchor=eventpos[eid]; own_pos=z.placebo_date.map(positions)
    overlap=((own_pos-250<=anchor)&(own_pos-30>=anchor)).sum()
    closest=np.min(np.abs(ix[:,None]-eventpos.to_numpy()[None,:]))
    assert np.diff(ix).min()>=22 and closest>30
    rows.append(dict(event_id=eid,attempted=len(z),valid=int(valid.sum()),
        raw_rejections=int(z.loc[valid,'p_value'].lt(.05).sum()),
        minimum_policy_buffer=int(closest),minimum_spacing=int(np.diff(ix).min()),
        fit_contains_own_event=int(overlap),future_dates=int((own_pos>anchor).sum())))
pd.DataFrame(rows).to_csv(OUT/'placebo_selection_audit.csv',index=False)
s=pq.read_table(ROOT/'data/derived/event_samples.parquet').to_pandas()
ars=pq.read_table(ROOT/'data/derived/abnormal_returns.parquet').to_pandas()
heads=[]
for eid in ev.event_id:
    q=s[s.event_id.eq(eid)&s.complete_primary]
    if eid.startswith('mining'):
        q=q[q.group.isin(['mining','non_mining'])]
        w=q.group.map({'mining':1/(q.group=='mining').sum(),'non_mining':-1/(q.group=='non_mining').sum()})
    else:
        w=pd.Series(1/len(q),index=q.index)
    weights=pd.Series(w.to_numpy(),index=q.instrument_id)
    d=ars[ars.event_id.eq(eid)&ars.instrument_id.isin(q.instrument_id)&ars.tau.between(-250,-30)]
    E=d.pivot(index='tau',columns='instrument_id',values='ar_raw').reindex(columns=q.instrument_id)
    z=(E@weights).reindex(np.arange(-250,-29))
    active=d.assign(active=d.volume.gt(0)).pivot(index='tau',columns='instrument_id',values='active').reindex(columns=q.instrument_id).fillna(False).all(axis=1)
    heads.append(dict(event_id=eid,zero_volume_row_fraction=d.volume.le(0).mean(),
        all_active_dates=int(active.sum()),null_complete_dates=int(z.notna().sum()),
        acf1=z.corr(z.shift(1)),acf5=z.corr(z.shift(5)),
        early_sd=z[z.index<=-140].std(),late_sd=z[z.index>-140].std()))
pd.DataFrame(heads).to_csv(OUT/'null_process_diagnostics.csv',index=False)

def holm(values):
    values=np.asarray(values); order=np.argsort(values); result=np.empty(len(values))
    result[order]=np.minimum(1,np.maximum.accumulate(values[order]*np.arange(len(values),0,-1)))
    return result

inf=pd.read_csv(ROOT/'outputs/tables/event_study_inference.csv')
h=inf[inf.window.eq('primary')&((inf.event_id.str.startswith('mining')&inf.group.eq('mining_minus_non_mining'))|
    (~inf.event_id.str.startswith('mining')&inf.group.eq('all')))].copy()
h['independent_holm']=holm(h.p_value)
assert np.allclose(h.independent_holm,h.holm_primary_p,atol=1e-12,rtol=0)
h.to_csv(OUT/'independent_holm.csv',index=False)
rob=pd.read_csv(ROOT/'outputs/tables/robustness_summary.csv')
families=[]
for spec,z in rob.groupby('specification'):
    if len(z)==5:
        z=z.copy();z['five_event_holm_for_this_specification']=holm(z.p_value);families.append(z)
pd.concat(families).to_csv(OUT/'exploratory_holm_by_specification.csv',index=False)
for name,df in [('baseline',inf),('robustness',rob),('placebo',p)]:
    valid=df.p_value.notna();z=df[valid].copy()
    z['interval_excludes_zero']=z.ci_lower.gt(0)|z.ci_upper.lt(0)
    z['p_rejects']=z.p_value.lt(.05)
    z[z.interval_excludes_zero.ne(z.p_rejects)].to_csv(OUT/f'{name}_p_interval_disagreements.csv',index=False)
print(pd.DataFrame(rows).to_string(index=False))
print(h[['event_id','p_value','independent_holm']].to_string(index=False))

# Isolate timing from sample/model drift: freeze 2018 baseline coefficients and
# use a common constituent set complete across every evaluated date window.
returns=pq.read_table(ROOT/'data/derived/returns_daily.parquet',
    columns=['instrument_id','date','return','market_return','has_positive_volume']).to_pandas()
returns['date']=pd.to_datetime(returns.date)
model=pd.read_csv(OUT/'independent_models.csv')
model=model[model.event_id.eq('mining_charter_2018')]
base=s[s.event_id.eq('mining_charter_2018') & s.complete_primary & s.group.isin(['mining','non_mining'])]
windows={}
for date in ['2018-09-19','2018-09-20','2018-09-21','2018-09-26','2018-09-27']:
    index=int(positions.loc[pd.Timestamp(date)])
    windows[date]=cal.date.iloc[index:index+2].tolist()
all_dates=set(d for dates in windows.values() for d in dates)
d=returns[returns.instrument_id.isin(base.instrument_id)&returns.date.isin(all_dates)].copy()
d=d.merge(model[['instrument_id','alpha','beta']],on='instrument_id',validate='many_to_one')
d['ar']=d['return']-d.alpha-d.beta*d.market_return
d.loc[~d.has_positive_volume | ~np.isfinite(d['return']) | ~np.isfinite(d.market_return),'ar']=np.nan
common=d.groupby('instrument_id').ar.agg(lambda z:len(z)==len(all_dates) and np.isfinite(z).all())
common_ids=common[common].index
fixed=[]
for date,days in windows.items():
    z=d[d.instrument_id.isin(common_ids)&d.date.isin(days)]
    c=z.groupby('instrument_id').ar.sum().rename('car').to_frame().join(base.set_index('instrument_id').group)
    fixed.append(dict(anchor=date,last_session=str(days[-1].date()),n_mining=int(c.group.eq('mining').sum()),
        n_control=int(c.group.eq('non_mining').sum()),
        spread=c[c.group.eq('mining')].car.mean()-c[c.group.eq('non_mining')].car.mean(),
        description='2018 baseline models frozen; common complete constituents; point estimates only'))
pd.DataFrame(fixed).to_csv(OUT/'fixed_sample_2018_timing.csv',index=False)
print(pd.DataFrame(fixed).to_string(index=False))
