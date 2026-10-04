"""Task D: the main result. Under what conditions is the cooling slope strongest? (H2, H3)

Inputs
  cooling_efficiency.csv (R3) -> common.main_spec, rows with ce = NaN dropped
  city_climate.csv (R2)       -> joined on uc_id + season
  data/samples/*.csv          -> built_mean, n_cells per city (pre rows, built >= 0.10)
Per season x time (6 panels), response ce_per_0.1 (se_per_0.1 = se / 10):
  single predictors  log10_rain (headline), rh_pct, swvl1, t2m_c, hi_c, built_mean
                     WLS, weights 1/se_per_0.1^2, HC3 errors; OLS rows ('ols:...') as a check
  multiple           ce_per_0.1 ~ log10_rain + t2m_c + built_mean   ('multi:...')
  threshold bins     < 1000 / >= 1000 mm, and < 750 / 750-1500 / > 1500 mm
  city size          'size:' rows: ce ~ log10_rain + log10(n_cells)
  sensitivity        'capped:log10_rain' (weights capped at 95th pct) and 'min6blocks:log10_rain'
                     (fits with >= 6 cluster blocks): clustered se from very few blocks is unreliable
Sign: negative slope = greener is cooler. So a POSITIVE coefficient on log10_rain means
cooling is weaker in wetter cities, i.e. STRONGER in drier cities (Manoli w/ irrigation, Yang);
a NEGATIVE one means cooling is stronger in wetter cities (Guo, Schwaab).

Usage: python scripts/08_main_result.py   (rerun whenever R3 commits a new cooling_efficiency.csv)
Output: data/results/main_result_regressions.csv, main_result_bins.csv,
        figures/D_ce_vs_rain.png, D_ce_vs_humidity.png, D_ce_map_{season}_{time}.png
"""
import json

import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
import numpy as np
import pandas as pd
import statsmodels.api as sm

import config as C
from common import DRY_MM, MAIN_BUILT_MIN, SEASONS, load_samples, main_spec
from style import (CE_LABEL, DIVERGING, MUTED, SEASON_COLORS, SEASON_LABELS, apply_style, save)

RES = C.DATA / 'results'
LABEL = ['Jodhpur', 'Kochi', 'New Delhi', 'Mumbai', 'Hyderabad', 'Bengaluru']
SINGLE = ['log10_rain', 'rh_pct', 'swvl1', 't2m_c', 'hi_c', 'built_mean']
MULTI = ['log10_rain', 't2m_c', 'built_mean']
TIMES = ['day', 'night']
OUTLINE = C.RAW / 'ne_admin0'


def load(climate_path=RES / 'city_climate.csv'):
    ce = pd.read_csv(RES / 'cooling_efficiency.csv')
    ms = main_spec(ce).dropna(subset=['ce'])
    clim = pd.read_csv(climate_path)
    s = load_samples()
    u = s[(s.season == 'pre') & (s.built >= MAIN_BUILT_MIN)]
    dens = u.groupby('uc_id').agg(built_mean=('built', 'mean'), n_cells=('built', 'size')).reset_index()
    with open(C.CITIES_FILE) as f:
        geo = pd.DataFrame([ft['properties'] for ft in json.load(f)['features']])
    geo = geo.rename(columns={'ID_UC_G0': 'uc_id'})[['uc_id', 'lon', 'lat', 'pop_2025']]
    d = (ms.merge(clim.drop(columns='city'), on=['uc_id', 'season'], how='left')
           .merge(dens, on='uc_id', how='left').merge(geo, on='uc_id', how='left'))
    miss = d[d.rain_annual_mm.isna()].city.unique()
    if len(miss):
        print(f'WARNING: {len(miss)} cities have no climate row: {list(miss)[:10]}')
    d = d.dropna(subset=['rain_annual_mm'])
    d['log10_rain'] = np.log10(d.rain_annual_mm)
    d['se_per_0.1'] = d.se / 10
    d['w'] = 1 / d['se_per_0.1'] ** 2
    return d, ce


def wls(g, xs, weights=None):
    X = sm.add_constant(g[xs])
    w = g.w if weights is None else weights
    return sm.WLS(g['ce_per_0.1'], X, weights=w).fit(cov_type='HC3')


def regressions(d):
    rows = []
    for s in SEASONS:
        for t in TIMES:
            g = d[(d.season == s) & (d.time == t)].dropna(subset=SINGLE)
            if len(g) < 8:
                continue
            for x in SINGLE:
                for tag, m in (('', wls(g, [x])),
                               ('ols:', sm.OLS(g['ce_per_0.1'], sm.add_constant(g[[x]])).fit(cov_type='HC3'))):
                    lo, hi = m.conf_int().loc[x]
                    rows.append(dict(season=s, time=t, predictor=tag + x, slope=m.params[x], ci_lo=lo,
                                     ci_hi=hi, p=m.pvalues[x], r2=m.rsquared, n_cities=len(g)))
            # Sensitivity of the headline to fits whose clustered se rests on few blocks:
            # capped weights (95th pct) and dropping fits with < 6 blocks.
            sens = {'capped:': wls(g, ['log10_rain'], weights=g.w.clip(upper=g.w.quantile(0.95)))}
            g6 = g[g.n_blocks >= 6]
            if len(g6) >= 8:
                sens['min6blocks:'] = wls(g6, ['log10_rain'])
            for tag, m in sens.items():
                lo, hi = m.conf_int().loc['log10_rain']
                rows.append(dict(season=s, time=t, predictor=tag + 'log10_rain', slope=m.params.log10_rain,
                                 ci_lo=lo, ci_hi=hi, p=m.pvalues.log10_rain, r2=m.rsquared,
                                 n_cities=int(m.nobs)))
            # TA question "couldn't it be city size?": add log10(number of urban squares)
            ms_ = wls(g.assign(log10_n_cells=np.log10(g.n_cells)), ['log10_rain', 'log10_n_cells'])
            for x in ('log10_rain', 'log10_n_cells'):
                lo, hi = ms_.conf_int().loc[x]
                rows.append(dict(season=s, time=t, predictor='size:' + x, slope=ms_.params[x], ci_lo=lo,
                                 ci_hi=hi, p=ms_.pvalues[x], r2=ms_.rsquared, n_cities=len(g)))
            m = wls(g, MULTI)
            for x in MULTI:
                lo, hi = m.conf_int().loc[x]
                rows.append(dict(season=s, time=t, predictor='multi:' + x, slope=m.params[x], ci_lo=lo,
                                 ci_hi=hi, p=m.pvalues[x], r2=m.rsquared, n_cities=len(g)))
    r = pd.DataFrame(rows)
    # WLS vs OLS sign check
    for _, a in r[~r.predictor.str.contains(':')].iterrows():
        b = r[(r.season == a.season) & (r.time == a.time) & (r.predictor == 'ols:' + a.predictor)]
        if len(b) and np.sign(b.slope.iloc[0]) != np.sign(a.slope) and (a.p < 0.1 or b.p.iloc[0] < 0.1):
            print(f'  NOTE: WLS and OLS disagree in sign for {a.season}/{a.time}/{a.predictor} '
                  f'({a.slope:+.2f} vs {b.slope.iloc[0]:+.2f}); report both')
    return r


def bins(d):
    rows = []
    groups = {f'< {DRY_MM}': lambda x: x < DRY_MM, f'≥ {DRY_MM}': lambda x: x >= DRY_MM,
              '< 750': lambda x: x < 750, '750–1500': lambda x: (x >= 750) & (x <= 1500),
              '> 1500': lambda x: x > 1500}
    for s in SEASONS:
        for t in TIMES:
            g = d[(d.season == s) & (d.time == t)]
            for name, f in groups.items():
                gg = g[f(g.rain_annual_mm)]
                rows.append(dict(season=s, time=t, rain_group=name + ' mm', n_cities=len(gg),
                                 median_ce_per_01=gg['ce_per_0.1'].median(),
                                 share_cooling_sig=(gg.ci_hi < 0).mean() if len(gg) else np.nan,
                                 share_warming_sig=(gg.ci_lo > 0).mean() if len(gg) else np.nan))
    return pd.DataFrame(rows).rename(columns={'median_ce_per_01': 'median_ce_per_0.1'})


def fig_vs(d, xcol, name, xlabel, logx=False):
    fig, axes = plt.subplots(2, 3, figsize=(15, 8.6), layout='constrained', sharex=True)
    for i, t in enumerate(TIMES):
        for j, s in enumerate(SEASONS):
            ax = axes[i, j]
            g = d[(d.season == s) & (d.time == t)].dropna(subset=[xcol])
            ax.axhline(0, color='k', lw=0.8)
            if xcol == 'rain_annual_mm':
                ax.axvline(DRY_MM, color=MUTED, ls='--', lw=0.9)
            ax.errorbar(g[xcol], g['ce_per_0.1'], yerr=1.96 * g['se_per_0.1'], fmt='none',
                        ecolor=MUTED, alpha=0.2, lw=0.6)
            sig = (g.ci_hi < 0) | (g.ci_lo > 0)
            ax.scatter(g.loc[sig, xcol], g.loc[sig, 'ce_per_0.1'], s=14, color=SEASON_COLORS[s], zorder=3)
            ax.scatter(g.loc[~sig, xcol], g.loc[~sig, 'ce_per_0.1'], s=14, facecolors='white',
                       edgecolors=SEASON_COLORS[s], zorder=3)
            xv = np.log10(g[xcol]) if logx else g[xcol]
            if len(g) >= 8:
                gx = g.assign(_x=xv)
                m = wls(gx, ['_x'])
                xs = np.linspace(xv.min(), xv.max(), 60)
                pr = m.get_prediction(sm.add_constant(pd.DataFrame({'_x': xs}))).summary_frame()
                xp = 10 ** xs if logx else xs
                ax.plot(xp, pr['mean'], color='k', lw=1.6)
                ax.fill_between(xp, pr.mean_ci_lower, pr.mean_ci_upper, color='k', alpha=0.12, lw=0)
                lo, hi = m.conf_int().loc['_x']
                unit = 'per 10× rain' if logx else 'per 1 % RH' if xcol == 'rh_pct' else ''
                ax.text(0.02, 0.97, f'n = {len(g)}\nslope {m.params["_x"]:+.2f} {unit}\n'
                        f'(95%: {lo:+.2f} to {hi:+.2f})', transform=ax.transAxes, va='top',
                        fontsize=8.5, bbox=dict(fc='white', ec='none', alpha=0.85))
            for nm in LABEL:
                r = g[g.city == nm]
                if len(r):
                    ax.annotate(nm, (r[xcol].iloc[0], r['ce_per_0.1'].iloc[0]), xytext=(4, 3),
                                textcoords='offset points', fontsize=7.5)
            lo_, hi_ = np.nanpercentile(d[d.time == t]['ce_per_0.1'], [1, 99])
            ax.set_ylim(lo_ - 0.5, hi_ + 0.5)
            if logx:
                ax.set_xscale('log')
                ax.set_xlim(d[xcol].min() * 0.85, d[xcol].max() * 1.2)
                ticks = [v for v in (250, 500, 1000, 2000, 4000) if d[xcol].min() * 0.85 <= v <= d[xcol].max() * 1.2]
                ax.set_xticks(ticks, [f'{v:,}' for v in ticks])
                ax.minorticks_off()
            if i == 0:
                ax.set_title(SEASON_LABELS[s], color=SEASON_COLORS[s])
            if j == 0:
                ax.set_ylabel(f"{'DAY' if t == 'day' else 'NIGHT'}\n{CE_LABEL}", fontsize=9)
            if i == 1:
                ax.set_xlabel(xlabel)
    fig.suptitle('Cooling slope vs background climate, one point per city (filled = 95% range '
                 'excludes 0; line = weighted fit; y clipped at 1st–99th pct)', fontsize=11)
    print(' ', save(fig, name).relative_to(C.ROOT))
    plt.close(fig)


def fig_maps(d):
    import geopandas as gpd
    shp = next(OUTLINE.glob('*.shp'), None) if OUTLINE.exists() else None
    india = None
    if shp:
        w = gpd.read_file(shp)
        india = w[w.ADMIN == 'India']
    lim = np.nanpercentile(d['ce_per_0.1'].abs(), 95)
    norm = TwoSlopeNorm(vmin=-lim, vcenter=0, vmax=lim)
    for s in SEASONS:
        for t in TIMES:
            g = d[(d.season == s) & (d.time == t)]
            fig, ax = plt.subplots(figsize=(7, 8), layout='constrained')
            if india is not None:
                india.boundary.plot(ax=ax, color=MUTED, lw=0.6)
            size = 8 + 220 * (g.pop_2025 / d.pop_2025.max()) ** 0.5
            sig = (g.ci_hi < 0) | (g.ci_lo > 0)
            ax.scatter(g.lon[~sig], g.lat[~sig], s=size[~sig], facecolors='none',
                       edgecolors=plt.get_cmap(DIVERGING)(norm(g['ce_per_0.1'][~sig])), lw=1.1)
            sc = ax.scatter(g.lon[sig], g.lat[sig], s=size[sig], c=g['ce_per_0.1'][sig], cmap=DIVERGING,
                            norm=norm, edgecolor='white', lw=0.4)
            fig.colorbar(sc, ax=ax, shrink=0.5, label=CE_LABEL.replace('; ', '\n'), extend='both')
            ax.set_aspect(1 / np.cos(np.radians(22)))
            ax.set_xlabel('Longitude (°E)')
            ax.set_ylabel('Latitude (°N)')
            ax.set_title(f"{SEASON_LABELS[s]}, {t}: {len(g)} cities\n(blue = greener is cooler, "
                         'hollow = 95% range crosses 0, size = population)', fontsize=10)
            print(' ', save(fig, f'D_ce_map_{s}_{t}').relative_to(C.ROOT))
            plt.close(fig)


def checks(d, ce):
    print('\n=== Checks ===')
    pil = ce[(ce.season == 'pre') & (ce.time == 'day') & (ce['index'] == 'ndvi') & (ce.control == 'built')
             & ((ce.built_min - MAIN_BUILT_MIN).abs() < 1e-9) & ce.city.isin(['Jodhpur', 'Kochi'])]
    for _, r in pil.iterrows():
        m = d[(d.city == r.city) & (d.season == 'pre') & (d.time == 'day')]
        print(f"  pilot {r.city}: pilot spec {r['ce_per_0.1']:+.2f}; main spec "
              f"{m['ce_per_0.1'].iloc[0] if len(m) else float('nan'):+.2f}")
    print('  n_cities per panel:\n' + d.groupby(['season', 'time']).size().unstack().to_string())
    nd = d[d.time == 'night']
    print('  night cities by rainfall group:\n' + nd.groupby(['season', nd.rain_annual_mm < DRY_MM])
          .size().unstack().rename(columns={True: f'< {DRY_MM}', False: f'≥ {DRY_MM}'}).to_string())
    g = d[(d.season == 'pre') & (d.time == 'day')].reset_index(drop=True)
    full = wls(g, ['log10_rain']).params['log10_rain']
    loo = pd.Series([wls(g.drop(i), ['log10_rain']).params['log10_rain'] for i in g.index], index=g.city)
    ch = (loo - full).abs()
    print(f'  leave-one-out (pre/day rain slope {full:+.3f}): largest change {ch.max():.3f} '
          f'({ch.idxmax()}); sign flips: {list(loo[np.sign(loo) != np.sign(full)].index) or "none"}')
    few = g.n_blocks <= 5
    print(f'  fits with <= 5 cluster blocks: {few.mean():.0%} of cities, {(g.w[few].sum() / g.w.sum()):.0%} '
          'of the weight (their se is least reliable; see capped: and min6blocks: rows)')
    share = (g.w / g.w.sum())
    print(f'  largest WLS weight share: {share.max():.1%} ({g.city[share.idxmax()]})')
    if share.max() > 0.10:
        cap = g.w.clip(upper=g.w.quantile(0.95))
        mc = wls(g, ['log10_rain'], weights=cap)
        lo, hi = mc.conf_int().loc['log10_rain']
        print(f'  -> capped weights (95th pct): rain slope {mc.params.log10_rain:+.3f} ({lo:+.3f} to {hi:+.3f})')
    srt = g.sort_values('ce_per_0.1')
    print('  5 most negative (city, n):', [(r.city, int(r.n)) for r in srt.head(5).itertuples()])
    print('  5 most positive (city, n):', [(r.city, int(r.n)) for r in srt.tail(5).itertuples()])


def observation_lines(reg, bn):
    print('\n=== Draft observation lines (check wording before pasting into docs/observations.md) ===')
    for t in TIMES:
        for s in SEASONS:
            r = reg[(reg.season == s) & (reg.time == t) & (reg.predictor == 'log10_rain')]
            if r.empty:
                continue
            r = r.iloc[0]
            if r.ci_lo <= 0 <= r.ci_hi:
                verdict = 'shows no clear trend with annual rainfall'
            elif r.slope > 0:
                verdict = 'is weaker in wetter cities, i.e. stronger in drier ones (Manoli with irrigation, Yang)'
            else:
                verdict = 'is stronger in wetter cities (Guo, Schwaab)'
            print(f'- {SEASON_LABELS[s]}, {t}: across {r.n_cities} cities the cooling slope {verdict} '
                  f'({r.slope:+.2f} °C per 0.1 NDVI per 10× rain, 95% CI {r.ci_lo:+.2f} to {r.ci_hi:+.2f}).')
    b = bn[(bn.season == 'pre') & (bn.time == 'day') & (bn.rain_group == f'< {DRY_MM} mm')].iloc[0]
    print(f'- Threshold (pre, day): in {b.n_cities} cities under {DRY_MM} mm, {b.share_warming_sig:.0%} '
          f'show significant greener-is-warmer slopes (Guo et al. 2026: 22% net warming under 1000 mm).')


def main(climate_path=RES / 'city_climate.csv'):
    apply_style()
    d, ce = load(climate_path)
    reg = regressions(d)
    reg.to_csv(RES / 'main_result_regressions.csv', index=False)
    bn = bins(d)
    bn.to_csv(RES / 'main_result_bins.csv', index=False)
    print(f'{d.uc_id.nunique()} cities -> main_result_regressions.csv ({len(reg)} rows), '
          f'main_result_bins.csv ({len(bn)} rows)')
    print(reg[reg.predictor.isin(['log10_rain', 'ols:log10_rain', 'capped:log10_rain', 'min6blocks:log10_rain',
                                  'multi:log10_rain', 'size:log10_rain', 'size:log10_n_cells'])]
          .round(3).to_string(index=False))
    fig_vs(d, 'rain_annual_mm', 'D_ce_vs_rain', 'Annual rainfall, 2019–2024 mean (mm/yr, log scale)', logx=True)
    fig_vs(d, 'rh_pct', 'D_ce_vs_humidity', 'Season-mean relative humidity (%)')
    fig_maps(d)
    checks(d, ce)
    observation_lines(reg, bn)


if __name__ == '__main__':
    main()
