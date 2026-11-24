"""Independent verification of remediated returns, sample screens, OLS and CARs.

Run from any directory with the project's Python/PyArrow environment. Writes only
outputs/diagnostics/remediation; never invokes or edits the analysis.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'outputs/diagnostics/remediation'
OUT.mkdir(parents=True, exist_ok=True)
SRC = ROOT / 'data/thesis_data'
checks = {}


def read(name, derived=False, columns=None):
    folder = ROOT / 'data/derived' if derived else SRC / 'data'
    return pq.read_table(folder / (name + '.parquet'), columns=columns).to_pandas()


def dates(df):
    df['date'] = pd.to_datetime(df['date'])
    return df


cal = pd.read_csv(SRC / 'documentation/trading_calendar.csv', parse_dates=['date'])
cal['session'] = np.arange(1, len(cal) + 1)
session = cal.set_index('date').session


def independent_returns(df, key):
    df = dates(df)
    df['session'] = df.date.map(session)
    assert df.session.notna().all()
    assert not df.duplicated([key, 'date']).any()
    df = df.sort_values([key, 'session']).reset_index(drop=True)
    last = df.groupby(key, sort=False)[['close_raw', 'session']].shift()
    valid = (np.isfinite(df.close_raw) & df.close_raw.gt(0) &
             np.isfinite(last.close_raw) & last.close_raw.gt(0) &
             df.session.eq(last.session + 1))
    df['independent_return'] = np.where(valid, df.close_raw / last.close_raw - 1, np.nan)
    return df


# Removing placeholder rows is safe here only because consecutive session IDs
# are explicitly checked, including when the missing row had a positive close.
p = independent_returns(read('prices_observed', columns=[
    'date', 'instrument_id', 'close_raw', 'volume', 'has_positive_volume',
    'diagnostic_price_return', 'potential_stale_price']), 'instrument_id')
m = independent_returns(read('market_index', columns=['date', 'index_id', 'close_raw']), 'index_id')
p['market_return'] = p.date.map(m.set_index('date').independent_return)
ref = p.diagnostic_price_return.to_numpy()
own = p.independent_return.to_numpy()
assert np.array_equal(np.isfinite(ref), np.isfinite(own))
assert np.allclose(ref[np.isfinite(ref)], own[np.isfinite(own)], atol=1e-12, rtol=0)
checks['valid_source_stock_returns'] = int(np.isfinite(own).sum())
checks['source_return_max_error'] = float(np.nanmax(np.abs(ref - own)))
# Reconstruct the approved analytical series independently from raw source
# ratios and the CSV ledger, retaining a separate raw-return reference.
p['return_raw'] = p.independent_return
ledger=pd.read_csv(ROOT/'research/corporate_actions_v1.csv',parse_dates=['effective_date'])
applied_count=0
for action in ledger[ledger.apply_price_correction].itertuples():
    assert action.verification_status=='verified_conversion' and action.action_type=='security_unit_conversion'
    mask=p.instrument_id.eq(action.instrument_id)&p.date.eq(action.effective_date)
    assert mask.sum()==1 and action.price_multiplier>0
    p.loc[mask,'independent_return']=(p.loc[mask,'return_raw']+1)/action.price_multiplier-1
    applied_count+=int(mask.sum())
checks['independently_applied_verified_conversions']=applied_count

dr = dates(read('returns_daily', True, ['instrument_id', 'date', 'return', 'return_raw', 'close_raw', 'volume', 'market_return']))
j = p[['instrument_id', 'date', 'independent_return', 'market_return']].merge(
    dr, on=['instrument_id', 'date'], validate='one_to_one', suffixes=('_own', '_stored'))
assert len(j) == len(p) == len(dr)
assert np.nanmax(np.abs(j.return_raw-p.return_raw)) < 1e-12
checks['raw_close_max_error']=float(np.nanmax(np.abs(j.close_raw-p.close_raw)))
checks['raw_volume_max_error']=float(np.nanmax(np.abs(j.volume-p.volume)))
assert checks['raw_close_max_error'] < 1e-9 and checks['raw_volume_max_error']==0
assert np.array_equal(np.isfinite(j.independent_return), np.isfinite(j['return']))
assert np.nanmax(np.abs(j.independent_return-j['return'])) < 1e-12
assert np.nanmax(np.abs(j.market_return_own-j.market_return_stored)) < 1e-12
checks['derived_return_rows_reconciled'] = len(j)
gap = m[m.date.between('2023-12-29', '2024-01-04')][['date', 'independent_return']]
gap.to_csv(OUT / 'benchmark_gap.csv', index=False)

samples = read('event_samples', True)
cl = read('event_industry_classifications')
master = read('instruments', columns=['instrument_id', 'company_name'])
events = pd.read_csv(ROOT / 'research/events.csv', parse_dates=['event_date'])
models = read('market_model_estimates', True)
cars = read('firm_event_cars', True)
published = pd.read_csv(ROOT / 'outputs/tables/event_study_inference.csv')
daily = read('daily_event_aggregates', True)
windows = {'primary': (0, 1), 'short': (-1, 3), 'week': (0, 5),
           'anticipation': (-10, -1), 'plot': (-10, 10)}
own_models, own_cars, daily_checks, sample_checks = [], [], [], []
car_errors, model_errors, spread_checks, deletion_rows, event_daily = [], [], [], [], []

for ev in events.itertuples():
    eid = ev.event_id
    t0 = int(session.loc[ev.event_date])
    d = p[p.session.between(t0-250, t0+10)].copy()
    d['tau'] = d.session-t0
    d['usable'] = (np.isfinite(d.independent_return) & np.isfinite(d.market_return) & d.has_positive_volume)
    pre = d[d.tau.between(-250, -30)].copy()
    pre['has_price'] = np.isfinite(pre.close_raw) & pre.close_raw.gt(0)
    stats = pre.groupby('instrument_id').agg(n_est=('usable','sum'), historical_positive_closes=('has_price','sum'))
    zf = pre.loc[np.isfinite(pre.independent_return)].groupby('instrument_id').independent_return.agg(lambda a: a.eq(0).mean())
    stats['zero_fraction'] = zf
    ss = samples[samples.event_id.eq(eid)].set_index('instrument_id')
    reconstructed = stats.reindex(ss.index)
    reconstructed[['n_est','historical_positive_closes']] = reconstructed[['n_est','historical_positive_closes']].fillna(0)
    eligible = (reconstructed.n_est.ge(180) & reconstructed.historical_positive_closes.gt(0) &
                reconstructed.zero_fraction.le(.2) & ~ss.likely_non_company_security.fillna(False).astype(bool))
    assert np.array_equal(eligible.to_numpy(), ss.eligible.to_numpy())
    assert np.array_equal(reconstructed.n_est, ss.n_est)
    sample_checks.append({'event_id':eid,'screening_rows':len(ss),'eligible':int(eligible.sum()),
                          'primary_complete':int(ss.complete_primary.sum()),
                          'model_fit_failures':int((~models[models.event_id.eq(eid)].model_ok).sum())})
    groups = ss.group.to_dict()
    own_event_ar = []
    for mm in models[models.event_id.eq(eid)].itertuples():
        est = pre[pre.instrument_id.eq(mm.instrument_id) & pre.usable]
        X = np.column_stack([np.ones(len(est)), est.market_return])
        alpha, beta = np.linalg.lstsq(X, est.independent_return, rcond=None)[0]
        res = est.independent_return.to_numpy()-X @ [alpha,beta]
        sigma = np.sqrt(np.sum(res**2)/(len(est)-2))
        model_errors.append(max(abs(alpha-mm.alpha),abs(beta-mm.beta),abs(sigma-mm.sigma)))
        own_models.append({'event_id':eid,'instrument_id':mm.instrument_id,'alpha':alpha,'beta':beta,'sigma':sigma,'n':len(est)})
        a = d[d.instrument_id.eq(mm.instrument_id)].copy()
        a['ar'] = a.independent_return-alpha-beta*a.market_return
        a.loc[~a.usable, 'ar'] = np.nan
        a['group'] = groups[mm.instrument_id]
        own_event_ar.append(a[['instrument_id','tau','date','group','ar','market_return','independent_return']])
        for w,(lo,hi) in windows.items():
            e = a[a.tau.between(lo,hi)]
            if len(e) == 0:
                continue
            complete = len(e)==hi-lo+1 and np.isfinite(e.ar).all()
            car = e.ar.sum() if complete else np.nan
            match = cars[cars.event_id.eq(eid) & cars.instrument_id.eq(mm.instrument_id) & cars.window.eq(w)]
            assert len(match)==1
            assert complete == bool(match.iloc[0].complete)
            if complete:
                car_errors.append(abs(car-match.iloc[0].car))
            own_cars.append({'event_id':eid,'instrument_id':mm.instrument_id,'group':groups[mm.instrument_id],
                             'window':w,'complete':complete,'car':car})
    ed = pd.concat(own_event_ar, ignore_index=True)
    ec = pd.DataFrame([x for x in own_cars if x['event_id']==eid])
    for row in published[published.event_id.eq(eid)].itertuples():
        a = ec[ec.window.eq(row.window) & ec.complete]
        if row.group=='mining_minus_non_mining':
            v = a[a.group.eq('mining')].car.mean()-a[a.group.eq('non_mining')].car.mean()
        else:
            if row.group!='all':
                a = a[a.group.eq(row.group)]
            v = a.car.mean()
        spread_checks.append({'event_id':eid,'window':row.window,'group':row.group,
                              'estimate_own':v,'estimate_published':row.estimate,'absolute_error':abs(v-row.estimate)})
    plot_ids = ec[ec.window.eq('plot') & ec.complete]
    for g in daily[daily.event_id.eq(eid)].group.unique():
        z = ed[ed.instrument_id.isin(plot_ids.instrument_id) & ed.tau.between(-10,10)]
        if g=='mining_minus_non_mining':
            series = z[z.group.eq('mining')].groupby('tau').ar.mean()-z[z.group.eq('non_mining')].groupby('tau').ar.mean()
        else:
            if g!='all':
                z = z[z.group.eq(g)]
            series = z.groupby('tau').ar.mean()
        expected = daily[daily.event_id.eq(eid) & daily.group.eq(g)].sort_values('tau')
        err = np.max(np.abs(series.sort_index().cumsum().to_numpy()-expected.caar.to_numpy()))
        daily_checks.append({'event_id':eid,'group':g,'maximum_cumulative_error':err})
    primary = ec[ec.window.eq('primary') & ec.complete]
    mining = eid.startswith('mining_charter')
    base = (primary[primary.group.eq('mining')].car.mean()-primary[primary.group.eq('non_mining')].car.mean()
            if mining else primary.car.mean())
    target = primary[primary.group.isin(['mining','non_mining'])] if mining else primary
    for row in target.itertuples():
        sub = primary[primary.instrument_id.ne(row.instrument_id)]
        value = (sub[sub.group.eq('mining')].car.mean()-sub[sub.group.eq('non_mining')].car.mean()
                 if mining else sub.car.mean())
        deletion_rows.append({'event_id':eid,'removed':row.instrument_id,'group':row.group,
                              'baseline':base,'leave_one_out_estimate':value,'change':value-base})
    for tau in range(-2,4):
        e = ed[ed.instrument_id.isin(target.instrument_id) & ed.tau.eq(tau)]
        r_market = e.market_return.iloc[0] if len(e) else np.nan
        event_daily.append({'event_id':eid,'tau':tau,'date':str(e.date.iloc[0].date()) if len(e) else '',
                            'market_return':r_market,'mean_raw_stock_return':e.independent_return.mean(),
                            'aar_all_target':e.ar.mean(),
                            'mining_minus_control_aar':e[e.group.eq('mining')].ar.mean()-e[e.group.eq('non_mining')].ar.mean()})

checks['sample_rows_independently_screened'] = sum(x['screening_rows'] for x in sample_checks)
checks['independent_ols_fits'] = len(own_models)
checks['model_max_coefficient_or_sigma_error'] = max(model_errors)
checks['car_rows_checked'] = len(own_cars)
checks['complete_car_max_error'] = max(car_errors)
checks['inference_estimate_max_error'] = max(x['absolute_error'] for x in spread_checks)
checks['plotted_caar_max_error'] = max(x['maximum_cumulative_error'] for x in daily_checks)
assert checks['model_max_coefficient_or_sigma_error'] < 1e-10
assert checks['inference_estimate_max_error'] < 1e-12
assert checks['plotted_caar_max_error'] < 1e-12
for name,rows in [('independent_models',own_models),('independent_cars',own_cars),
                  ('sample_screening',sample_checks),('headline_and_window_reconciliation',spread_checks),
                  ('figure_reconciliation',daily_checks),('leave_one_out',deletion_rows),('event_daily_returns',event_daily)]:
    pd.DataFrame(rows).to_csv(OUT / (name+'.csv'),index=False)
constituents = samples[samples.complete_primary].copy()
source_class = cl.set_index(['event_id','instrument_id']).reindex(
    pd.MultiIndex.from_frame(samples[['event_id','instrument_id']]))
known = source_class.nature_of_business_raw.notna() & source_class.match_confidence.eq('high_label_concordance')
expected_group = np.where(known & source_class.mining_candidate.eq(True), 'mining',
    np.where(known & source_class.mining_candidate.eq(False), 'non_mining', 'unknown'))
assert np.array_equal(expected_group, samples.group.to_numpy())
checks['classification_rows_reconciled_to_event_specific_source'] = len(samples)
constituents.to_csv(OUT/'primary_constituents.csv',index=False)
constituents[constituents.group.eq('unknown')].to_csv(OUT/'unclassified_primary.csv',index=False)
candidate_labels = constituents[constituents.nature_of_business_raw.fillna('').str.contains('Inv|Pref',case=False)]
candidate_labels.to_csv(OUT/'investment_label_review.csv',index=False)
dup = constituents[constituents.instrument_id.isin(['FFA:XJSE:EQU','FFB:XJSE:EQU'])]
dup.to_csv(OUT/'fortress_share_classes.csv',index=False)
checks['null_issuer_ids_in_primary'] = int(constituents.issuer_id.isna().sum())
checks['null_security_types_in_primary'] = int(constituents.security_type.isna().sum())
checks['primary_total_security_event_rows'] = len(constituents)
(OUT/'independent_numeric_checks.json').write_text(json.dumps(checks,indent=2)+'\n')
print(json.dumps(checks,indent=2))
print(pd.DataFrame(event_daily).query('tau in [0,1]').to_string(index=False))

# Bind independent verification to the exact current input/output artifacts.
import hashlib
from datetime import datetime, timezone
import pyarrow
files=['data/derived/returns_daily.parquet','data/derived/event_samples.parquet',
       'data/derived/market_model_estimates.parquet','data/derived/firm_event_cars.parquet',
       'data/derived/abnormal_returns.parquet','data/derived/daily_event_aggregates.parquet',
       'outputs/tables/event_study_inference.csv','outputs/tables/headline_results_percent.csv',
       'research/corporate_actions_v1.csv','config/analysis.yml',
       'review/remediation/verify_corrected.py']
fingerprints={f:hashlib.file_digest((ROOT/f).open('rb'),'sha256').hexdigest() for f in files}
(OUT/'independent_verification_metadata.json').write_text(json.dumps(dict(
    run_time_utc=datetime.now(timezone.utc).isoformat(),numpy=np.__version__,pandas=pd.__version__,
    pyarrow=pyarrow.__version__,sha256=fingerprints),indent=2)+'\n')
