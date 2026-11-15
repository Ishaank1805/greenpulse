"""Role 5 final-plan Task 10: exclude mapped-water *squares*, not just cities.

Runs a new sensitivity analysis; does not overwrite cooling_efficiency.csv or H6.
For each sampled city, pre-monsoon daytime NDVI slopes are refit using the exact
model from 03_cooling_efficiency.fit, after excluding either all positive mapped
water or squares with >5% mapped water. A positive zero-water filter makes the
water covariate constant; statsmodels still estimates the other coefficients.

H6 is recomputed from these slopes with Ishaan's imported HI scenario functions.
All primary H6 comparisons use the same set of cooling cities across the original
and restricted refits. The >=10-block sensitivity requires both fits to pass.

Outputs:
  data/results/role5_dry_square_city_slopes.csv
  data/results/role5_water_square_checks.csv

Run from repository root: python scripts/22_water_square_exclusion.py
"""
import importlib
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

import config as C
from role5_utils import RES, main_cooling, read_csv, spearman

FIT = importlib.import_module('03_cooling_efficiency')
H6 = importlib.import_module('15_felt_heat')

THRESHOLDS = {'exclude_any_mapped_water': 0.0, 'exclude_water_gt_5pct': 0.05}


def refit_one(path, original):
    """Fit one city at both dry-square thresholds and verify the unfiltered fit."""
    sample, has_water = FIT.load_city(path)
    if not has_water:
        raise FileNotFoundError(f'No OSM water data for {path.name}')
    pre = sample[sample.season.eq('pre')].copy()
    urban = pre[pre.built >= 0.10].copy()
    if urban.water_frac.isna().any():
        raise ValueError(f'{path.name}: {urban.water_frac.isna().sum()} urban cells lack mapped water')
    if not urban.water_frac.between(0, 1).all():
        raise ValueError(f'{path.name}: invalid water_frac')
    uc_id = int(sample.uc_id.iloc[0]); city = str(sample.city.iloc[0])
    full = FIT.fit(pre, 'day', 'ndvi', 0.10, 'built_elev_water')
    baseline = original[original.uc_id.eq(uc_id)]
    if len(baseline) > 1:
        raise ValueError(f'Duplicate main-spec baseline uc_id {uc_id}')
    if len(baseline):
        ref = baseline.iloc[0]
        if not np.isclose(full.get('ce', np.nan), ref.ce, atol=1e-7, rtol=1e-7) or int(full['n']) != int(ref.n):
            raise AssertionError(f'{city}: refit does not reproduce committed main slope (script 03)')
    elif np.isfinite(full.get('ce', np.nan)):
        raise AssertionError(f'{city}: valid new refit but missing committed main-spec baseline')

    rows=[]
    for key, threshold in THRESHOLDS.items():
        subset = pre[pre.water_frac <= threshold].copy()
        # One cluster is not enough for a cluster-robust uncertainty estimate.
        chosen = subset[subset.built >= 0.10].dropna(subset=['lst_day','ndvi','built','elev','water_frac'])
        blocks = (np.floor(chosen.lon / FIT.BLOCK_DEG).astype(int).astype(str) + '_'
                  + np.floor(chosen.lat / FIT.BLOCK_DEG).astype(int).astype(str))
        if len(chosen) >= FIT.MIN_SQUARES and blocks.nunique() >= 2:
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', RuntimeWarning)
                calc = FIT.fit(subset, 'day', 'ndvi', 0.10, 'built_elev_water')
        else:
            calc = {'n': len(chosen), 'n_blocks': int(blocks.nunique())}
        ce = calc.get('ce', np.nan)
        rows.append(dict(uc_id=uc_id,city=city,variant=key,water_threshold=threshold,
                         n_urban=int(len(urban)),n_removed_urban=int((urban.water_frac>threshold).sum()),
                         baseline_n=int(full['n']),baseline_n_blocks=full.get('n_blocks',np.nan),
                         baseline_ce_per_0_1=full.get('ce',np.nan)/10,
                         restricted_n=int(calc['n']),restricted_n_blocks=calc.get('n_blocks',np.nan),
                         restricted_ce_per_0_1=ce/10,
                         delta_restricted_minus_baseline=(ce-full.get('ce',np.nan))/10))
    return rows


def h6_comparison(city_rows, baseline):
    """Calculate fixed-dewpoint H6 correlations using matched, cooling-only cities."""
    climate=read_csv('city_climate.csv',['uc_id','season','rh_pct'])
    climate=climate[climate.season.eq('pre')][['uc_id','rh_pct']]
    daily=read_csv('city_daily_climate.csv',['uc_id','season','t2m_max_c','td_c'])
    daily=daily[daily.season.eq('pre')]
    daily_map={int(uc):(g.t2m_max_c.to_numpy(float),g.td_c.to_numpy(float))
               for uc,g in daily.groupby('uc_id')}
    old=read_csv('felt_heat.csv',['uc_id','season','step','r','delta_td','d_tair',
                                  'hi_efficiency','delta_star'])
    old=old[(old.season=='pre')&(old.step=='ndvi_0.1')&np.isclose(old.r,0.08)&
            np.isclose(old.delta_td,0)&(old.d_tair<0)]
    if old.uc_id.duplicated().any(): raise ValueError('Duplicate original H6 city IDs')
    old=old[['uc_id','hi_efficiency','delta_star']].rename(columns={
        'hi_efficiency':'original_hi_efficiency','delta_star':'original_delta_star'})

    all_rows=[]
    for variant,g in city_rows.groupby('variant'):
        g=g.merge(climate,on='uc_id',validate='one_to_one').merge(old,on='uc_id',validate='one_to_one')
        g=g[g.restricted_ce_per_0_1.lt(0) & g.baseline_ce_per_0_1.lt(0)].copy()
        if len(g)==0:raise ValueError(f'No matched cooling cities for {variant}')
        eff=[];star=[]
        for row in g.itertuples(index=False):
            d_tair=float(row.restricted_ce_per_0_1)*0.08
            T,Td=daily_map[int(row.uc_id)]
            d_hi=float(H6.hi_change(T,Td,d_tair,[0.0])[0][0])
            eff.append(d_hi/d_tair)
            star.append(float(H6.delta_star(T,Td,d_tair)))
        g['restricted_hi_efficiency']=eff
        g['restricted_delta_star']=star
        for selection, sub in [('matched_cooling_cities',g),
                               ('matched_both_ge_10_blocks',g[(g.baseline_n_blocks>=10)&
                                                               (g.restricted_n_blocks>=10)])]:
            for metric in ('hi_efficiency','delta_star'):
                for src in ('original','restricted'):
                    n,rho,p=spearman(sub.rh_pct,sub[f'{src}_{metric}'])
                    all_rows.append(dict(analysis='H6_water_square_exclusion',
                                         variant=variant,selection=selection,
                                         statistic=f'spearman_{src}_{metric}_vs_rh',
                                         n_cities=n,value=rho,p=p,
                                         note='Pre-monsoon +0.1 NDVI, ratio r=0.08, fixed dewpoint. '
                                              'Matched negative-slope cities; modelled HI, not measured air heat'))
        all_rows.append(dict(analysis='water_square_exclusion',variant=variant,
                             selection='all_cities_with_baseline',statistic='median_urban_squares_removed',
                             n_cities=len(city_rows[city_rows.variant.eq(variant)]),
                             value=float(city_rows[city_rows.variant.eq(variant)].n_removed_urban.median()),
                             p=np.nan,note='OSM mapped water in urban squares; not an ERA5 or causal outcome'))
    return pd.DataFrame(all_rows)


def calculate():
    original=main_cooling()
    original=original[(original.season=='pre') & (original.time=='day')]
    all_rows=[]
    paths=sorted(C.SAMPLES_DIR.glob('*.csv'))
    if not paths: raise FileNotFoundError('data/samples/*.csv not found')
    for i,path in enumerate(paths,1):
        all_rows.extend(refit_one(path,original))
        if i%60==0: print(f'Refit checked {i}/{len(paths)} cities')
    city=pd.DataFrame(all_rows)
    summary=h6_comparison(city,original)
    return city,summary


def main():
    city,summary=calculate()
    RES.mkdir(parents=True,exist_ok=True)
    city.to_csv(RES/'role5_dry_square_city_slopes.csv',index=False)
    summary.to_csv(RES/'role5_water_square_checks.csv',index=False)
    print(f'Saved {len(city)} refit comparisons and {len(summary)} summary statistics')
    print(summary[['variant','selection','statistic','n_cities','value','p']].to_string(index=False))
    print('SCENARIO ONLY: no newly measured air temperatures or causal intervention')


if __name__=='__main__':main()
