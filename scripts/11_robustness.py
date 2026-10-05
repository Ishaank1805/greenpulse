"""Task H: robustness. Would the result change if...?

Each variant is compared with the main spec (common.main_spec), per season x time:
  main               reference
  evi                index = evi
  built_min_0.20     built_min = 0.20
  no_water_control   control = built_elev  (identical to main until water files exist)
  no_elev_control    control = built       (the pilot's spec)
  no_controls        control = none
  min_nights_6       night only: refit main spec with min_nights = 6 (recovers humid cities)
  drop_water_squares refit main spec without squares with water_frac > 0.5 (needs data/water/)
Plus, if city_climate.csv exists:
  night_warming_dry / night_warming_wet (and *_mn6): share of cities with greener-is-warmer
  night slopes (ci_lo > 0), < 1000 vs >= 1000 mm. Tests whether Jodhpur's warm nights
  are a dry-city pattern.

Columns (README 3.5): variant, season, time, n_cities, share_cooling_sig, median_ce_per_0.1,
spearman_vs_main, rain_slope, rain_slope_p, plus share_warming_sig (appended).
rain_slope: WLS ce_per_0.1 ~ log10(rain_annual_mm), weights 1/(se/10)^2, HC3 (as R2's D).

Also: NDVI vs EVI disagreement (pre/day) vs the city's NDVI-built correlation and rainfall
-> data/results/robustness_ndvi_evi.csv.

Usage: python scripts/11_robustness.py
Output: data/results/robustness.csv, robustness_ndvi_evi.csv, figures/H_*.png
"""
import importlib

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import fisher_exact, spearmanr

import config as C
from common import (CONTROL_PRIORITY, DRY_MM, MAIN_BUILT_MIN, SEASONS, load_climate, main_spec,
                    sample_paths)
from style import CE_LABEL, DRY_COLOR, MUTED, WET_COLOR, apply_style, save

ce03 = importlib.import_module('03_cooling_efficiency')
OUT = C.DATA / 'results' / 'robustness.csv'
COLS = ['variant', 'season', 'time', 'n_cities', 'share_cooling_sig', 'median_ce_per_0.1',
        'spearman_vs_main', 'rain_slope', 'rain_slope_p', 'share_warming_sig']
LABELS = {'main': 'Main (NDVI, built ≥ 10%, built + elev. + water)', 'evi': 'EVI instead of NDVI',
          'built_min_0.20': 'Built-up cut-off 20%', 'no_water_control': 'No water control',
          'no_elev_control': 'No elevation control (pilot spec)', 'no_controls': 'No controls',
          'min_nights_6': '6 clear nights (night only)',
          'drop_water_squares': 'Water squares dropped'}


def pick(ce, index='ndvi', built_min=MAIN_BUILT_MIN, control=None):
    """Like main_spec, with one choice changed. control=None uses the main-spec priority."""
    d = ce[(ce['index'] == index) & ((ce.built_min - built_min).abs() < 1e-9)]
    if control is not None:
        return d[d.control == control]
    d = d[d.control.isin(CONTROL_PRIORITY)]
    rank = {c: i for i, c in enumerate(CONTROL_PRIORITY)}
    d = d.assign(_r=d.control.map(rank)).sort_values('_r')
    return d.drop_duplicates(['uc_id', 'season', 'time']).drop(columns='_r')


def refit(paths, min_nights=ce03.MIN_NIGHTS, drop_water=False, times=('day', 'night')):
    """Refit the main spec with script 03's own fit()."""
    rows = []
    for p in paths:
        df, has_water = ce03.load_city(p)
        if drop_water:
            if not has_water:
                continue
            df = df[~(df.water_frac > 0.5)]
        ctrl = next(c for c in CONTROL_PRIORITY if c != 'built_elev_water' or has_water)
        for s in SEASONS:
            for t in times:
                r = ce03.fit(df[df.season == s], t, 'ndvi', MAIN_BUILT_MIN, ctrl, min_nights)
                rows.append(dict(r, season=s, city=df.city.iloc[0], uc_id=df.uc_id.iloc[0]))
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out['ce_per_0.1'] = out.ce / 10
    return out


def rain_fit(g, rain):
    if rain is None:
        return np.nan, np.nan
    d = g.merge(rain, on='uc_id').dropna(subset=['ce', 'rain_annual_mm'])
    if len(d) < 5:
        return np.nan, np.nan
    X = sm.add_constant(np.log10(d.rain_annual_mm).rename('log10_rain'))
    m = sm.WLS(d['ce_per_0.1'], X, weights=1 / (d.se / 10) ** 2).fit(cov_type='HC3')
    return m.params['log10_rain'], m.pvalues['log10_rain']


def summarise(name, v, main, rain):
    rows = []
    v = v.dropna(subset=['ce'])
    for (s, t), g in v.groupby(['season', 'time']):
        mref = main[(main.season == s) & (main.time == t)][['uc_id', 'ce_per_0.1']]
        j = g.merge(mref, on='uc_id', suffixes=('', '_main'))
        rho = spearmanr(j['ce_per_0.1'], j['ce_per_0.1_main'])[0] if len(j) > 2 else np.nan
        rs, rp = rain_fit(g, rain)
        rows.append(dict(variant=name, season=s, time=t, n_cities=len(g),
                         share_cooling_sig=(g.ci_hi < 0).mean(), share_warming_sig=(g.ci_lo > 0).mean(),
                         **{'median_ce_per_0.1': g['ce_per_0.1'].median()},
                         spearman_vs_main=rho, rain_slope=rs, rain_slope_p=rp))
    return rows


def night_warming(main_night, mn6, rain):
    rows = []
    for tag, v in (('', main_night), ('_mn6', mn6)):
        d = v.dropna(subset=['ce']).merge(rain, on='uc_id')
        for s, g in d.groupby('season'):
            for grp, gg in (('dry', g[g.rain_annual_mm < DRY_MM]), ('wet', g[g.rain_annual_mm >= DRY_MM])):
                rows.append(dict(variant=f'night_warming_{grp}{tag}', season=s, time='night',
                                 n_cities=len(gg), share_cooling_sig=(gg.ci_hi < 0).mean(),
                                 share_warming_sig=(gg.ci_lo > 0).mean(),
                                 **{'median_ce_per_0.1': gg['ce_per_0.1'].median()},
                                 spearman_vs_main=np.nan, rain_slope=np.nan, rain_slope_p=np.nan))
    return rows


def ndvi_evi(ce, rain):
    n = pick(ce)
    e = pick(ce, index='evi')
    key = ['uc_id', 'city', 'season', 'time']
    j = n[(n.season == 'pre') & (n.time == 'day')].dropna(subset=['ce'])[key + ['ce_per_0.1', 'ci_hi']].merge(
        e.dropna(subset=['ce'])[key + ['ce_per_0.1', 'ci_hi']], on=key, suffixes=('_ndvi', '_evi'))
    j['disagree'] = (j.ci_hi_ndvi < 0) != (j.ci_hi_evi < 0)
    r = []
    for p in sample_paths():
        df = pd.read_csv(p)
        d = df[(df.season == 'pre') & (df.built >= MAIN_BUILT_MIN)].dropna(subset=['lst_day', 'ndvi'])
        r.append(dict(uc_id=df.uc_id.iloc[0], r_ndvi_built=d.ndvi.corr(d.built) if len(d) > 2 else np.nan))
    j = j.merge(pd.DataFrame(r), on='uc_id')
    if rain is not None:
        j = j.merge(rain, on='uc_id', how='left')
    print(f'\nNDVI vs EVI, pre/day: {len(j)} cities, disagree on significance in {j.disagree.mean():.0%}')
    strong = j.r_ndvi_built < -0.7
    tab = [[(strong & j.disagree).sum(), (strong & ~j.disagree).sum()],
           [(~strong & j.disagree).sum(), (~strong & ~j.disagree).sum()]]
    print(f'  r(NDVI, built) < -0.7: disagree {j[strong].disagree.mean():.0%} of {strong.sum()}; '
          f'otherwise {j[~strong].disagree.mean():.0%} of {(~strong).sum()} '
          f'(Fisher p = {fisher_exact(tab)[1]:.2g})')
    print(f'  rank correlation of disagreement with r(NDVI, built): '
          f'{spearmanr(j.r_ndvi_built, j.disagree)[0]:+.2f}')
    if rain is not None:
        for grp, g in j.groupby(j.rain_annual_mm < DRY_MM):
            print(f"  {'< ' if grp else '≥ '}{DRY_MM} mm: disagree {g.disagree.mean():.0%} of {len(g)}")
    return j


def fig_ndvi_evi(j, rain):
    fig, ax = plt.subplots(figsize=(6.5, 6), layout='constrained')
    if rain is not None and 'rain_annual_mm' in j:
        col = np.where(j.rain_annual_mm < DRY_MM, DRY_COLOR, WET_COLOR)
        ax.scatter(j['ce_per_0.1_ndvi'], j['ce_per_0.1_evi'], c=col, s=16)
        ax.scatter([], [], c=DRY_COLOR, label=f'< {DRY_MM} mm/yr')
        ax.scatter([], [], c=WET_COLOR, label=f'≥ {DRY_MM} mm/yr')
        ax.legend(loc='upper left')
    else:
        sc = ax.scatter(j['ce_per_0.1_ndvi'], j['ce_per_0.1_evi'], c=j.r_ndvi_built, cmap='viridis_r', s=16)
        fig.colorbar(sc, ax=ax, label='Correlation of NDVI with built-up share in the city')
    lim = np.nanpercentile(np.r_[j['ce_per_0.1_ndvi'], j['ce_per_0.1_evi']], [1, 99]) + [-0.3, 0.3]
    ax.plot(lim, lim, color=MUTED, lw=1, label='1:1')
    ax.axhline(0, color='k', lw=0.6)
    ax.axvline(0, color='k', lw=0.6)
    ax.set_xlim(lim)
    ax.set_ylim(lim)
    ax.set_xlabel('Cooling slope with NDVI (°C per 0.1 NDVI)')
    ax.set_ylabel('Cooling slope with EVI (°C per 0.1 EVI)')
    rho = spearmanr(j['ce_per_0.1_ndvi'], j['ce_per_0.1_evi'])[0]
    ax.set_title(f'Pre-monsoon, day: {len(j)} cities, rank correlation {rho:.2f}\n'
                 '(EVI has a smaller range than NDVI, so compare ranks, not sizes)', fontsize=10)
    print(' ', save(fig, 'H_ndvi_vs_evi').relative_to(C.ROOT))
    plt.close(fig)


def table(res):
    t = res[(res.season == 'pre') & (res.time == 'day') & res.variant.isin(LABELS)].copy()
    t['order'] = t.variant.map({k: i for i, k in enumerate(LABELS)})
    t = t.sort_values('order')
    out = pd.DataFrame({
        'Variant\n(pre-monsoon, day)': t.variant.map(LABELS),
        'Cities': t.n_cities.astype(int).astype(str),
        'Significant\ncooling': t.share_cooling_sig.map('{:.0%}'.format),
        'Median\nslope': t['median_ce_per_0.1'].map('{:+.2f}'.format),
        'Rank corr.\nwith main': t.spearman_vs_main.map(lambda x: '—' if pd.isna(x) else f'{x:.2f}'),
        'Rainfall slope\n(per 10× rain)': [('not yet (needs city_climate.csv)' if pd.isna(a) else
                                           f'{a:+.2f} (p = {b:.2g})') for a, b in zip(t.rain_slope, t.rain_slope_p)],
    })
    return out


def fig_table(tab):
    fig, ax = plt.subplots(figsize=(13, 0.6 + 0.45 * (len(tab) + 1)))
    ax.axis('off')
    w = [0.31, 0.08, 0.11, 0.09, 0.11, 0.30]
    tb = ax.table(cellText=tab.values, colLabels=tab.columns, colWidths=w, loc='center',
                  cellLoc='center')
    tb.auto_set_font_size(False)
    tb.set_fontsize(9.5)
    tb.scale(1, 1.55)
    for (r, c), cell in tb.get_celld().items():
        cell.set_edgecolor('#d0d4d9')
        if r == 0:
            cell.set_height(cell.get_height() * 1.8)
            cell.set_facecolor('#eef1f5')
            cell.set_text_props(weight='bold')
        if c == 0:
            cell.set_text_props(ha='left')
            cell.PAD = 0.03
    ax.set_title(f'Robustness of the cooling slope. {CE_LABEL}', fontsize=10)
    print(' ', save(fig, 'H_robustness_table').relative_to(C.ROOT))
    plt.close(fig)


def check_against_d(res):
    p = C.DATA / 'results' / 'main_result_regressions.csv'
    m = res[(res.variant == 'main') & (res.season == 'pre') & (res.time == 'day')]
    if not p.exists() or m.rain_slope.isna().all():
        print('  (check vs R2 skipped: main_result_regressions.csv or climate not available)')
        return True
    d = pd.read_csv(p)
    d = d[(d.season == 'pre') & (d.time == 'day') & (d.predictor == 'log10_rain')]
    good = len(d) and abs(d.slope.iloc[0] - m.rain_slope.iloc[0]) < 5e-4
    print(f"  check: main rain_slope {m.rain_slope.iloc[0]:+.3f} vs R2 {d.slope.iloc[0]:+.3f}: "
          f"{'ok' if good else 'MISMATCH, resolve with R2'}")
    return bool(good)


def main():
    apply_style()
    ce = pd.read_csv(C.DATA / 'results' / 'cooling_efficiency.csv')
    clim = load_climate()
    rain = None if clim is None else clim.groupby('uc_id').rain_annual_mm.first().reset_index()
    main_ = main_spec(ce)
    paths = sample_paths()

    variants = {'main': main_, 'evi': pick(ce, index='evi'), 'built_min_0.20': pick(ce, built_min=0.20),
                'no_water_control': pick(ce, control='built_elev'),
                'no_elev_control': pick(ce, control='built'), 'no_controls': pick(ce, control='none')}
    print('Refitting night with min_nights = 6 ...')
    mn6 = refit(paths, min_nights=6, times=('night',))
    variants['min_nights_6'] = mn6
    dw = refit(paths, drop_water=True)
    if dw.empty:
        print('  drop_water_squares skipped: no data/water/ files yet (Role 5, task G)')
    else:
        variants['drop_water_squares'] = dw

    rows = []
    md = main_.dropna(subset=['ce'])
    for name, v in variants.items():
        rows += summarise(name, v, md, rain)
    if rain is not None:
        rows += night_warming(main_[main_.time == 'night'], mn6, rain)
    else:
        print('  night_warming_dry/wet skipped: city_climate.csv not found (Role 2)')
    res = pd.DataFrame(rows)[COLS]
    res.to_csv(OUT, index=False)
    print(f'{len(res)} rows -> {OUT.relative_to(C.ROOT)}')

    gained = (mn6.dropna(subset=['ce']).groupby('season').size()
              - md[md.time == 'night'].groupby('season').size())
    print('Night cities gained with 6 clear nights:', gained.to_dict())
    nm = (variants['no_water_control'].dropna(subset=['ce']).merge(md, on=['uc_id', 'season', 'time']))
    if (nm['ce_x'] - nm['ce_y']).abs().max() < 1e-12:
        print('Note: no_water_control is identical to main (no water files yet).')
        LABELS['no_water_control'] = 'No water control (= main, no water data yet)'

    j = ndvi_evi(ce, rain)
    j.to_csv(C.DATA / 'results' / 'robustness_ndvi_evi.csv', index=False)
    fig_ndvi_evi(j, rain)
    tab = table(res)
    fig_table(tab)
    print('\n' + tab.rename(columns=lambda c: c.replace('\n', ' ')).to_markdown(index=False))
    ok = check_against_d(res)
    return res, tab, ok


if __name__ == '__main__':
    main()
