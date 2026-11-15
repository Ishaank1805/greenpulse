"""Role 5 / required task 10: independently check new H6 and height results.

No Earth Engine or network access. Writes data/results/new_checks.csv and a figure.
Usage: python scripts/19_new_checks.py [--require-height]

H6 uses *cooling cities only* (d_tair < 0), exactly as Ishaan's H6 test.
The plan's at-least-10-block threshold and the earlier >5-block check are both kept.
The plan's median water threshold is kept literally. A complementary mean-water
threshold is also reported because city median can be zero for even quite watery cities.
"""
import argparse
import importlib
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from role5_utils import RES, main_cooling, read_csv, spearman, water_intensity
from style import apply_style, save

H6 = importlib.import_module('15_felt_heat') # import Ishaan's NOAA scenario, do not copy formulas


def add_stat(rows, analysis, variant, statistic, value, n, note=''):
    rows.append(dict(analysis=analysis, variant=variant, n_cities=int(n),
                     statistic=statistic, value=value, note=note))


def check_h6(rows, ce, water):
    fh = read_csv('felt_heat.csv', ['uc_id','season','step','r','delta_td','d_tair','d_hi',
                                   'hi_efficiency','delta_star'])
    climate = read_csv('city_climate.csv', ['uc_id','season','rh_pct'])
    climate = climate[climate.season == 'pre'][['uc_id','rh_pct']]
    pre = ce[(ce.season == 'pre') & (ce.time == 'day')][['uc_id','city','ce','n_blocks']]
    if pre.uc_id.duplicated().any(): raise ValueError('Duplicate pre-day main-spec city IDs')
    f = fh[(fh.season=='pre') & (fh.step=='ndvi_0.1') &
           np.isclose(fh.r,0.08) & np.isclose(fh.delta_td,0)]
    if f.uc_id.duplicated().any(): raise ValueError('Duplicate baseline H6 city IDs')
    full = f.merge(pre, on='uc_id', how='inner', suffixes=('', '_main'), validate='one_to_one')
    full = full.merge(climate,on='uc_id',validate='many_to_one').merge(water,on='uc_id',validate='one_to_one')
    full = full[full.d_tair < 0].copy()

    variants = {
        'all': full,
        'n_blocks_ge_10': full[full.n_blocks >= 10],
        'n_blocks_gt_5': full[full.n_blocks > 5],
        'water_median_le_0.05': full[full.water_median <= 0.05],
        'water_mean_le_0.05 (extra)': full[full.water_mean <= 0.05],
    }
    for variant, g in variants.items():
        for metric in ('hi_efficiency','delta_star'):
            n,rho,p = spearman(g.rh_pct,g[metric])
            add_stat(rows,'H6',variant,f'spearman_{metric}_vs_rh',rho,n,
                     f'p={p:.6g}; pre, +0.1 NDVI, r=0.08, dewpoint change=0; '
                     'only greener-is-cooler cities; SCENARIO, not measured air cooling')

    # Verify ALL baseline replicates the earlier published H6 test; fail loudly on mismatch.
    test_path = RES / 'felt_heat_test.csv'
    if test_path.exists():
        tests = pd.read_csv(test_path)
        for metric in ('hi_efficiency','delta_star'):
            ref = tests[(tests.season=='pre')&(tests.step=='ndvi_0.1')&
                        np.isclose(tests.r,0.08)&(tests.metric==metric)&
                        (tests.test=='spearman_rh')&(tests.group=='all')]
            if len(ref)!=1: raise AssertionError(f'Missing/ambiguous benchmark: {metric}')
            result = next(r for r in rows if r['analysis']=='H6' and r['variant']=='all'
                          and r['statistic']==f'spearman_{metric}_vs_rh')
            if (int(ref.iloc[0].n_cities)!=result['n_cities'] or
                not np.isclose(ref.iloc[0].value,result['value'],atol=1e-10,rtol=0)):
                raise AssertionError(f'H6 benchmark mismatch {metric}: computed {result}, '
                                     f'published {ref.to_dict("records")}')
        print('PASS: all-city H6 Spearman results reproduce felt_heat_test.csv exactly')

    # The no-water *slopes* must have their Heat Index recomputed using 15_felt_heat.py.
    all_ce = read_csv('cooling_efficiency.csv', ['uc_id','season','time','index','built_min','control','ce'])
    alt = all_ce[(all_ce.season=='pre')&(all_ce.time=='day')&(all_ce['index']=='ndvi')&
                 np.isclose(all_ce.built_min,0.10)&(all_ce.control=='built_elev')]
    alt = alt.dropna(subset=['ce'])[['uc_id','ce']]
    if alt.uc_id.duplicated().any():raise ValueError('Duplicate built_elev comparison rows')
    daily = read_csv('city_daily_climate.csv', ['uc_id','season','t2m_max_c','td_c'])
    daily = daily[daily.season=='pre']
    dmap = {uc:(g.t2m_max_c.to_numpy(),g.td_c.to_numpy()) for uc,g in daily.groupby('uc_id')}
    alt = alt.merge(climate,on='uc_id',validate='one_to_one').merge(water,on='uc_id',validate='one_to_one')
    alt['d_tair'] = alt.ce / 10 * 0.08
    alt = alt[alt.d_tair < 0].copy()
    if alt.empty: raise ValueError('No negative cooling slopes under the no-water spec')
    calc=[]
    for r in alt.itertuples():
        if r.uc_id not in dmap: raise ValueError(f'No daily climate for city {r.uc_id}')
        T,Td=dmap[r.uc_id]
        delta_hi=float(H6.hi_change(T,Td,r.d_tair,[0.0])[0][0])
        calc.append((r.uc_id, delta_hi/r.d_tair, H6.delta_star(T,Td,r.d_tair)))
    calc=pd.DataFrame(calc,columns=['uc_id','hi_efficiency','delta_star'])
    alt=alt.merge(calc,on='uc_id',validate='one_to_one')
    # A fair comparison of the two slope specifications keeps the *same* city set.
    matched_main=full[full.uc_id.isin(alt.uc_id)]
    for metric in ('hi_efficiency','delta_star'):
        n,rho,p=spearman(matched_main.rh_pct,matched_main[metric])
        add_stat(rows,'H6','main_slope_on_no_water_city_set',
                 f'spearman_{metric}_vs_rh',rho,n,
                 f'p={p:.6g}; main slope evaluated on cities with no-water cooling; '
                 'matched-population comparator to no_water_slope_recomputed')
    alt_matched=alt[alt.uc_id.isin(full.uc_id)]
    for metric in ('hi_efficiency','delta_star'):
        n,rho,p=spearman(alt_matched.rh_pct,alt_matched[metric])
        add_stat(rows,'H6','no_water_same_city_set',f'spearman_{metric}_vs_rh',rho,n,
                 f'p={p:.6g}; no-water slopes on exact main/no-water common cooling cities')
    for metric in ('hi_efficiency','delta_star'):
        n,rho,p=spearman(alt.rh_pct,alt[metric])
        add_stat(rows,'H6','no_water_slope_recomputed',f'spearman_{metric}_vs_rh',rho,n,
                 f'p={p:.6g}; 15_felt_heat.hi_change and delta_star; '
                 'built_elev slopes, r=0.08; cooling cities only; SCENARIO')
    print(f'H6: {len(full)} main-spec cooling cities, {len(alt)} no-water cooling cities; '
          f'median water >0.05: {(full.water_median>0.05).sum()}, '
          f'mean water >0.05: {(full.water_mean>0.05).sum()}')
    return rows


def check_height(rows, ce, water, require_height=False):
    path=RES/'height_effect.csv'
    if not path.exists():
        msg='height_effect.csv absent: Johar has not delivered the height analysis. Skipping height checks.'
        if require_height: raise FileNotFoundError(msg)
        warnings.warn(msg)
        return False
    d=read_csv('height_effect.csv',['uc_id','season','time','tercile','ce_per_0.1',
                                    'interaction','interaction_p'])
    d=d[(d.season=='pre')&(d.time=='day')].copy()
    labels=d.tercile.astype(str).str.lower().str.strip()
    d['tercile_norm']=labels.replace({'lower':'low','lowest':'low','upper':'tall',
                                     'high':'tall','highest':'tall','short':'low',
                                     'medium':'mid','middle':'mid'})
    unknown=set(d.tercile_norm.unique())-{'low','mid','tall'}
    if unknown:raise ValueError(f'Unrecognized height terciles: {unknown}')
    if d.duplicated(['uc_id','tercile_norm']).any():
        raise ValueError('Duplicate city/tercile in height_effect.csv')
    piv=d.pivot(index='uc_id',columns='tercile_norm',values='ce_per_0.1')
    if not {'low','tall'}.issubset(piv.columns):raise ValueError('Height data lacks low or tall terciles')
    pair=piv[['low','tall']].dropna().copy()
    pair['tall_minus_low']=pair.tall-pair.low
    # Use the tall row's interaction test, if present, otherwise unique per-city test.
    interactions=[]
    for uc,g in d.groupby('uc_id'):
        z=g[g.tercile_norm=='tall'][['interaction','interaction_p']].dropna()
        if z.empty:
            z=g[['interaction','interaction_p']].dropna().drop_duplicates()
        if len(z)>1:raise ValueError(f'Ambiguous height interaction for city {uc}')
        if len(z)==1:
            interactions.append(dict(uc_id=uc,interaction=float(z.iloc[0].interaction),
                                     interaction_p=float(z.iloc[0].interaction_p)))
    inter=pd.DataFrame(interactions)
    if inter.empty: raise ValueError('No height interaction estimates; ask Johar for height_effect.csv')
    pair=pair.reset_index().merge(inter,on='uc_id',validate='one_to_one')
    pre=ce[(ce.season=='pre')&(ce.time=='day')][['uc_id','n_blocks']]
    pair=pair.merge(pre,on='uc_id',validate='one_to_one').merge(water,on='uc_id',validate='one_to_one')
    variants={'all':pair,
              'n_blocks_ge_10':pair[pair.n_blocks>=10],
              'n_blocks_gt_5':pair[pair.n_blocks>5],
              'water_median_le_0.05':pair[pair.water_median<=0.05],
              'water_mean_le_0.05 (extra)':pair[pair.water_mean<=0.05]}
    for variant,g in variants.items():
        add_stat(rows,'height',variant,'share_positive_interaction_p_lt_0.05',
                 float(((g.interaction>0)&(g.interaction_p<0.05)).mean()) if len(g) else np.nan,
                 len(g),'Positive interaction means a less negative / more positive slope in tall areas')
        add_stat(rows,'height',variant,'median_tall_minus_low_ce_per_0.1',
                 float(g.tall_minus_low.median()) if len(g) else np.nan,len(g),
                 '°C per 0.1 NDVI; computed from tall and low tercile slopes')
    print(f'Height checks: {len(pair)} paired cities; all-city positive interaction share '
          f'{((pair.interaction>0)&(pair.interaction_p<0.05)).mean():.1%}')
    return True


def draw(rows):
    d=pd.DataFrame(rows)
    d=d[(d.analysis=='H6')&d.statistic.str.startswith('spearman_')]
    if d.empty:return
    apply_style()
    fig,axes=plt.subplots(1,2,figsize=(13.6,6.7),sharex=True)
    order=['all','n_blocks_ge_10','n_blocks_gt_5','water_median_le_0.05',
           'water_mean_le_0.05 (extra)','main_slope_on_no_water_city_set','no_water_same_city_set','no_water_slope_recomputed']
    names=['All cooling cities','At least 10 blocks','More than 5 blocks (legacy)','Median water ≤ 5%',
           'Mean water ≤ 5%','Main, same city set','No-water, same set','No-water slopes']
    for ax,metric,ttl in zip(axes,['hi_efficiency','delta_star'],
                             ['Felt-heat efficiency','Break-even dewpoint increase']):
        s=d[d.statistic==f'spearman_{metric}_vs_rh'].set_index('variant')
        for i,(key,label) in enumerate(zip(order,names)):
            if key not in s.index:continue
            r=s.loc[key]
            ax.scatter(r.value,i,s=58,color='#1F4D3A' if key=='all' else '#C8640A',zorder=3)
            ax.text(r.value+0.035,i,f'{r.value:+.2f} (n={r.n_cities})',fontsize=8,va='center')
        ax.axvline(0,color='black',lw=0.8,alpha=0.6)
        ax.set_xlim(-1,1.27)
        ax.set_yticks(range(len(order)),names)
        ax.invert_yaxis()
        ax.set_xlabel('Spearman ρ against pre-monsoon relative humidity')
        ax.set_title(ttl)
    fig.suptitle('H6 sensitivity to small samples and mapped water\nSCENARIO, not measured air cooling',fontsize=13)
    fig.tight_layout()
    save(fig,'R5_h6_checks')
    plt.close(fig)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--require-height',action='store_true')
    args=ap.parse_args()
    ce=main_cooling();water=water_intensity()
    rows=[]
    check_h6(rows,ce,water)
    did_height=check_height(rows,ce,water,args.require_height)
    out=pd.DataFrame(rows,columns=['analysis','variant','n_cities','statistic','value','note'])
    out.to_csv(RES/'new_checks.csv',index=False)
    draw(rows)
    print(out.to_string(index=False))
    print(f'Saved {len(out)} statistics to data/results/new_checks.csv; height: '
          f'{"complete" if did_height else "PENDING"}')

if __name__=='__main__':main()
