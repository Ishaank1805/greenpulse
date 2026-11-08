"""H6: the heat people actually feel (FINAL_PLAN section 1; role_2_climate.md, final phase).

Hypothesis (PLAN.md): translating surface cooling into felt heat shrinks the benefit most in
humid cities. THIS IS A SCENARIO, NOT A MEASUREMENT: measured surface cooling slopes x published
surface-to-air ratios (both European) x each city's ERA5-Land daily climate.

Inputs
  cooling_efficiency.csv (R3)  -> common.main_spec, time = day, seasons pre (main) and post
  city_daily_climate.csv (R2)  -> daily Tmax and daily-mean dewpoint, 2019-2024 (gate G-H6a)
  city_climate.csv (R2)        -> rh_pct, rain_annual_mm, hi_c (for the tests and checks)
  data/samples/*.csv           -> each city's NDVI p25..p75 (pre rows, built >= 0.10)
Per city x season x step x r:
  d_lst  = ce_per_0.1 (step ndvi_0.1)  or  ce_per_0.1 x (NDVI p75 - p25) / 0.1 (step iqr)
  d_tair = d_lst x r                         r = 0.08 (Du 2024), 0.18 (Venter 2021)
  hi0    = HI(T, RH(T, Td))                  baseline, every day of the season
  hi1    = HI(T + d_tair, RH(T + d_tair, Td + delta))   delta = 0 (scenario A), 0.5, 1, 2 (B)
  d_hi   = mean over days of (hi1 - hi0)
  hi_efficiency = d_hi(delta = 0) / d_tair   (same value on every delta row of the group)
  delta_star    = smallest delta on the 0..5 C grid (0.05 steps) with d_hi >= 0, interpolated linearly
                  inside that step (config H6_DELTA_STAR_INTERP); 0 if d_tair >= 0; NaN if never
                  reached within 5 C. Stored on the delta = 0 rows only.
The Heat Index and Magnus formulas are imported from 07_city_climate.py, not copied.
Td + delta is capped at T + d_tair (RH <= 100%); the share of capped days is printed.

Usage:  python scripts/15_felt_heat.py
Output: data/results/felt_heat.csv          (README 6.1 contract)
        data/results/felt_heat_test.csv     (H6 test statistics, all variants)
        figures/H6_felt_vs_surface.png, figures/H6_breakeven.png
        printed checks and draft observation lines for docs/observations.md
"""
import importlib

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

import config as C
from common import DRY_MM, MAIN_BUILT_MIN, main_spec
from style import DRY_COLOR, MUTED, WET_COLOR, apply_style, save

clim07 = importlib.import_module('07_city_climate')   # one formula, one set of checks
heat_index_c, rh_magnus = clim07.heat_index_c, clim07.rh_magnus

RES = C.DATA / 'results'
OUT = RES / 'felt_heat.csv'
TEST_OUT = RES / 'felt_heat_test.csv'
COLS = ['uc_id', 'city', 'season', 'step', 'r', 'delta_td', 'd_lst', 'd_tair', 'd_hi',
        'hi_efficiency', 'delta_star']
STEPS = ('ndvi_0.1', 'iqr')
GRID = np.round(np.arange(0, C.H6_DELTA_STAR_MAX + 1e-9, C.H6_DELTA_STAR_STEP), 4)
MAIN = dict(season='pre', step='ndvi_0.1', r=0.08)   # the headline variant
LABEL = ['Jodhpur', 'New Delhi', 'Hyderabad', 'Kochi', 'Chennai', 'Kolkata', 'Mumbai']
HUMID = ['Kochi', 'Chennai', 'Kolkata']
SCENARIO_NOTE = 'SCENARIO, not a measurement: measured surface slopes × published air/surface ratios'


# --------------------------------------------------------------------------- inputs
def load_inputs():
    ce = main_spec(pd.read_csv(RES / 'cooling_efficiency.csv'))
    ce = ce[(ce.time == C.H6_TIME) & ce.season.isin(C.H6_SEASONS)].dropna(subset=['ce'])
    daily_path = RES / 'city_daily_climate.csv'
    if not daily_path.exists():
        raise SystemExit('data/results/city_daily_climate.csv is missing (gate G-H6a). '
                         'Run: python scripts/07_city_climate.py --export-daily')
    daily = pd.read_csv(daily_path)
    clim = pd.read_csv(RES / 'city_climate.csv')
    s = pd.concat([pd.read_csv(p, usecols=['uc_id', 'season', 'built', 'ndvi'])
                   for p in sorted(C.SAMPLES_DIR.glob('*.csv'))], ignore_index=True)
    u = s[(s.season == 'pre') & (s.built >= MAIN_BUILT_MIN)].dropna(subset=['ndvi'])
    lo, hi = C.H6_IQR_PCT
    iqr = u.groupby('uc_id').ndvi.agg(ndvi_p25=lambda x: np.percentile(x, lo),
                                      ndvi_p75=lambda x: np.percentile(x, hi),
                                      n_urban='size').reset_index()
    iqr['ndvi_iqr'] = iqr.ndvi_p75 - iqr.ndvi_p25
    return ce, daily, clim, iqr


# --------------------------------------------------------------------------- core
def hi_change(T, Td, d_tair, delta):
    """Mean over days of HI(scenario) - HI(baseline), degC. delta may be an array (grid).
    Returns (d_hi, share of days where Td + delta was capped at T + d_tair)."""
    T, Td = np.asarray(T, float), np.asarray(Td, float)
    delta = np.atleast_1d(np.asarray(delta, float))[:, None]          # (G, 1)
    hi0 = heat_index_c(T, rh_magnus(T, Td))                           # (n,)
    T1 = T + d_tair
    Td1 = Td + delta                                                  # (G, n)
    capped = Td1 > T1
    Td1 = np.minimum(Td1, T1)
    hi1 = heat_index_c(T1, rh_magnus(T1, Td1))                        # (G, n)
    return (hi1 - hi0).mean(axis=1), capped.mean(axis=1)


def delta_star(T, Td, d_tair):
    """Break-even dewpoint rise: first delta on GRID (0.05 C steps) with d_hi >= 0, then (if
    C.H6_DELTA_STAR_INTERP) linear interpolation inside that step, since delta* is often only a
    few grid steps above 0 at r = 0.08."""
    if d_tair >= 0:
        return 0.0
    d_hi, _ = hi_change(T, Td, d_tair, GRID)
    hit = np.flatnonzero(d_hi >= 0)
    if not hit.size:
        return np.nan
    k = hit[0]
    if k == 0 or not C.H6_DELTA_STAR_INTERP:
        return float(GRID[k])
    x0, x1, y0, y1 = GRID[k - 1], GRID[k], d_hi[k - 1], d_hi[k]
    return float(x0 + (x1 - x0) * (-y0) / (y1 - y0))


def run(ce, daily, clim, iqr):
    days = {k: (g.t2m_max_c.to_numpy(), g.td_c.to_numpy())
            for k, g in daily.groupby(['uc_id', 'season'])}
    iqr_map = iqr.set_index('uc_id').ndvi_iqr
    rows, caps, skipped = [], [], []
    for r_ in ce.itertuples():
        key = (r_.uc_id, r_.season)
        if key not in days:
            skipped.append((r_.city, r_.season, 'no daily climate'))
            continue
        T, Td = days[key]
        for step in STEPS:
            if step == 'ndvi_0.1':
                d_lst = r_.ce / 10                     # = ce_per_0.1 (README 3.3)
            else:
                if r_.uc_id not in iqr_map.index:
                    skipped.append((r_.city, r_.season, 'no NDVI spread'))
                    continue
                d_lst = (r_.ce / 10) * iqr_map[r_.uc_id] / C.H6_NDVI_STEP
            for r in C.H6_R:
                d_tair = d_lst * r
                d_hi, cap = hi_change(T, Td, d_tair, C.H6_DELTA_TD)
                caps.append(cap.max())
                eff = d_hi[0] / d_tair if d_tair != 0 else np.nan
                ds = delta_star(T, Td, d_tair)
                for k, dl in enumerate(C.H6_DELTA_TD):
                    rows.append(dict(uc_id=r_.uc_id, city=r_.city, season=r_.season, step=step, r=r,
                                     delta_td=dl, d_lst=d_lst, d_tair=d_tair, d_hi=d_hi[k],
                                     hi_efficiency=eff, delta_star=ds if dl == 0 else np.nan))
    fh = pd.DataFrame(rows)[COLS]
    if skipped:
        print(f'Skipped {len(skipped)} city x season x step: {skipped[:8]}')
    print(f'Days with Td + delta capped at T + d_tair (RH 100%): at most {max(caps):.2%} of a '
          'city-season (only at the larger delta values)')
    return fh


# --------------------------------------------------------------------------- checks
def checks(fh, ce, daily, clim):
    print('\n=== Checks (FINAL_PLAN 1, role 2 final phase) ===')
    ok = True
    days = {k: g for k, g in daily.groupby(['uc_id', 'season'])}

    # 1. zero inputs -> exactly zero change, every city x season
    zero = [hi_change(g.t2m_max_c, g.td_c, 0.0, [0.0])[0][0] for g in days.values()]
    good = all(z == 0 for z in zero)
    ok &= good
    print(f"  Zero inputs (d_tair = 0, delta = 0) give d_hi exactly 0 in all {len(zero)} city-seasons: "
          f"{'ok' if good else 'CHECK, max ' + str(max(map(abs, zero)))}")

    # 2. baseline reproduces hi_c (within 0.05 C) for the H6 seasons
    b = (daily[daily.season.isin(C.H6_SEASONS)]
         .assign(hi=lambda d: heat_index_c(d.t2m_max_c, rh_magnus(d.t2m_max_c, d.td_c)))
         .groupby(['uc_id', 'season']).hi.mean().reset_index()
         .merge(clim[['uc_id', 'season', 'hi_c', 'city']], on=['uc_id', 'season']))
    diff = (b.hi - b.hi_c).abs()
    good = diff.max() <= 0.05
    ok &= good
    print(f"  Baseline mean HI reproduces hi_c in city_climate.csv: max diff {diff.max():.4f} C "
          f"over {len(b)} city-seasons {'ok' if good else 'CHECK (worst ' + b.city[diff.idxmax()] + ')'}")

    m = fh[(fh.season == 'pre') & (fh.step == 'ndvi_0.1') & (fh.r == 0.08) & (fh.delta_td == 0)]
    m = m.merge(clim[clim.season == 'pre'][['uc_id', 'rh_pct']], on='uc_id')

    def city(name):
        r = m[m.city == name]
        return None if r.empty else r.iloc[0]

    # 3. dry city: efficiency ~ 1 (HI ~ T in dry air)
    j = city('Jodhpur')
    if j is not None:
        good = abs(j.hi_efficiency - 1) <= 0.15
        ok &= good
        print(f"  Dry: Jodhpur pre (RH {j.rh_pct:.0f}%) d_tair {j.d_tair:+.3f}, d_hi {j.d_hi:+.3f}, "
              f"efficiency {j.hi_efficiency:.2f} (expect ~1) {'ok' if good else 'CHECK'}")

    # 4. humid cities vs Jodhpur. Reported, not asserted: see the note on scenario A below.
    if j is not None:
        for name in HUMID:
            h = city(name)
            if h is None:
                print(f'  Humid: {name} has no main-spec slope')
                continue
            e_lower = h.hi_efficiency < j.hi_efficiency
            d_lower = h.delta_star < j.delta_star
            print(f"  Humid: {name:8s} (RH {h.rh_pct:.0f}%) efficiency {h.hi_efficiency:.2f} "
                  f"[{'below' if e_lower else 'ABOVE'} Jodhpur], |d_hi| {'<' if abs(h.d_hi) < abs(h.d_tair) else '>'} "
                  f"|d_tair|, delta* {h.delta_star:.2f} C [{'below' if d_lower else 'NOT below'} "
                  f"Jodhpur's {j.delta_star:.2f}]")
        print('  NOTE scenario A: with dewpoint held fixed, the NOAA Heat Index is steeper in T in humid\n'
              '       air (~1.3-1.4 C of HI per C of air), so humid cities can show efficiency ABOVE 1.\n'
              '       FINAL_PLAN expected below 1. Report what the data show; see the H6 test.')

    # 5. sign: negative slope -> negative d_tair and negative scenario-A d_hi
    a = fh[fh.delta_td == 0]
    neg = a[a.d_lst < 0]
    bad = neg[(neg.d_tair >= 0) | (neg.d_hi >= 0)]
    ok &= bad.empty
    print(f"  Sign: rows with greener-is-cooler slopes and d_tair or scenario-A d_hi >= 0: {len(bad)} "
          f"of {len(neg)} {'ok' if bad.empty else 'CHECK ' + str(bad.city.unique()[:8].tolist())}")
    pos = a[a.d_lst >= 0]
    print(f'  ({pos.uc_id.nunique()} city-seasons have greener-is-warmer days; their delta* is 0 by '
          'definition and they are kept in the file)')

    # 6. size: d_tair stays far below Meili 2021's 3.1-5.8 C maximum
    for r in C.H6_R:
        x = a[a.r == r].d_tair.abs()
        print(f'  Size: r = {r}: |d_tair| median {x.median():.3f} C, max {x.max():.3f} C '
              '(Meili 2021 max tree air cooling 3.1-5.8 C)')
    good = a.d_tair.abs().max() < 3.1
    ok &= good
    m8 = a[(a.r == 0.08) & (a.step == 'ndvi_0.1')].d_tair.abs().max()
    print(f"  At r = 0.08 and +0.1 NDVI the largest |d_tair| is {m8:.2f} C (expect tenths) "
          f"{'ok' if good and m8 < 1 else 'CHECK'}")

    # 7. delta* never reached
    ds = a[a.delta_star.isna() & (a.d_tair < 0)]
    print(f'  delta* not reached within {C.H6_DELTA_STAR_MAX} C: {len(ds)} groups '
          f'{ds.city.unique()[:8].tolist() if len(ds) else ""}')
    n_main = m.uc_id.nunique()
    print(f"  Cities in the headline variant (pre, +0.1 NDVI, r = 0.08): {n_main} "
          f"(main-spec daytime slopes: {ce[ce.season == 'pre'].uc_id.nunique()})")
    print('ALL CHECKS OK' if ok else 'SOME CHECKS NEED A LOOK (see above)')
    return ok


# --------------------------------------------------------------------------- H6 test (task 3)
def wls(y, x, w):
    X = sm.add_constant(pd.Series(x, name='x'))
    return sm.WLS(np.asarray(y), X, weights=np.asarray(w)).fit(cov_type='HC3')


def h6_test(fh, ce, clim):
    """Efficiency and delta* against humidity and rainfall, for every variant (delta = 0 rows)."""
    se = ce[['uc_id', 'season', 'se']].assign(w=lambda d: 1 / (d.se / 10) ** 2)
    a = (fh[fh.delta_td == 0].merge(clim[['uc_id', 'season', 'rh_pct']], on=['uc_id', 'season'])
         .merge(clim[clim.season == 'pre'][['uc_id', 'rain_annual_mm']], on='uc_id')
         .merge(se[['uc_id', 'season', 'w']], on=['uc_id', 'season']))
    # break-even per degree of air cooling: removes the slope's size, leaves the climate's part
    a['delta_star_per_c'] = a.delta_star / a.d_tair.abs()
    a = a[a.d_tair < 0]   # efficiency and delta* only mean something where greener is cooler
    rows = []
    for (s, step, r), g in a.groupby(['season', 'step', 'r']):
        for metric in ('hi_efficiency', 'delta_star', 'delta_star_per_c'):
            v = g.dropna(subset=[metric])
            base = dict(season=s, step=step, r=r, metric=metric)
            rho, p = stats.spearmanr(v.rh_pct, v[metric])
            rows.append(dict(base, test='spearman_rh', group='all', n_cities=len(v), value=rho,
                             ci_lo=np.nan, ci_hi=np.nan, p=p))
            rho, p = stats.spearmanr(np.log10(v.rain_annual_mm), v[metric])
            rows.append(dict(base, test='spearman_log10_rain', group='all', n_cities=len(v), value=rho,
                             ci_lo=np.nan, ci_hi=np.nan, p=p))
            dry, wet = v[v.rain_annual_mm < DRY_MM][metric], v[v.rain_annual_mm >= DRY_MM][metric]
            p_mw = stats.mannwhitneyu(dry, wet).pvalue if len(dry) and len(wet) else np.nan
            for name, x in ((f'< {DRY_MM} mm', dry), (f'≥ {DRY_MM} mm', wet)):
                rows.append(dict(base, test='median', group=name, n_cities=len(x), value=x.median(),
                                 ci_lo=np.nan, ci_hi=np.nan, p=p_mw))
            m = wls(v[metric], v.rh_pct, v.w)
            lo, hi = m.conf_int().loc['x']
            rows.append(dict(base, test='wls_rh_slope_per_10pct', group='all', n_cities=len(v),
                             value=m.params.x * 10, ci_lo=lo * 10, ci_hi=hi * 10, p=m.pvalues.x))
    return pd.DataFrame(rows), a


def verdict(t, a):
    def get(metric, test, group='all', **kw):
        q = t[(t.metric == metric) & (t.test == test) & (t.group == group)]
        for k, v in {**MAIN, **kw}.items():
            q = q[q[k] == v]
        return q.iloc[0]

    print('\n=== H6 test (task 3) ===')
    print(f"Headline variant: {MAIN['season']}-monsoon, +0.1 NDVI, r = {MAIN['r']}, cities with "
          'greener-is-cooler days')
    out = {}
    for metric, label in (('hi_efficiency', 'felt-heat efficiency'), ('delta_star', 'break-even delta*'),
                          ('delta_star_per_c', 'delta* per C of air cooling')):
        sp = get(metric, 'spearman_rh')
        dry, wet = get(metric, 'median', f'< {DRY_MM} mm'), get(metric, 'median', f'≥ {DRY_MM} mm')
        w = get(metric, 'wls_rh_slope_per_10pct')
        out[metric] = dict(rho=sp.value, p=sp.p, n=sp.n_cities, dry=dry.value, wet=wet.value,
                           n_dry=dry.n_cities, n_wet=wet.n_cities, p_mw=dry.p, wls=w.value,
                           wls_lo=w.ci_lo, wls_hi=w.ci_hi)
        print(f'  {label:28s} Spearman vs RH {sp.value:+.2f} (p {sp.p:.1g}, n {sp.n_cities}); median dry '
              f'{dry.value:.3f} ({dry.n_cities}) vs wet {wet.value:.3f} ({wet.n_cities}), MW p {dry.p:.1g}; '
              f'WLS per +10% RH {w.value:+.3f} ({w.ci_lo:+.3f} to {w.ci_hi:+.3f})')
    e, d = out['hi_efficiency'], out['delta_star']
    eff_lower = e['rho'] < 0 and e['p'] < 0.05
    ds_lower = d['rho'] < 0 and d['p'] < 0.05
    print(f"\n  H6 part 1, humid cities have LOWER efficiency: {'YES' if eff_lower else 'NO'}"
          f"{'' if eff_lower else ' (efficiency rises with humidity)' if e['rho'] > 0 and e['p'] < 0.05 else ''}")
    print(f"  H6 part 2, humid cities have LOWER delta*:     {'YES' if ds_lower else 'NO'}")
    print('  FINAL_PLAN rule: supported only if both are YES.')

    print('\n  Robustness of the two Spearman correlations with RH:')
    for (s, step, r), g in t[(t.test == 'spearman_rh') & t.metric.isin(['hi_efficiency', 'delta_star'])
                             ].groupby(['season', 'step', 'r']):
        e_, d_ = g[g.metric == 'hi_efficiency'].iloc[0], g[g.metric == 'delta_star'].iloc[0]
        print(f'    {s:4s} {step:8s} r={r:<5} efficiency {e_.value:+.2f} (p {e_.p:.1g})   '
              f'delta* {d_.value:+.2f} (p {d_.p:.1g})   n {e_.n_cities}')
    return out


def draft_observations(out, fh, clim):
    m = fh[(fh.season == 'pre') & (fh.step == 'ndvi_0.1') & (fh.delta_td == 0)]

    def v(city, r, col):
        x = m[(m.city == city) & (m.r == r)]
        return np.nan if x.empty else x[col].iloc[0]

    e, d, dc = out['hi_efficiency'], out['delta_star'], out['delta_star_per_c']
    a8 = m[(m.r == 0.08) & (m.d_tair < 0)]
    a18 = m[(m.r == 0.18) & (m.d_tair < 0)]
    print('\n=== Draft observation lines (check every number, then paste under ## Role 2) ===\n')
    print(f"- **H6 is a scenario, not a measurement.** Measured daytime surface slopes × published "
          f"air/surface ratios (r = 0.08 from Du 2024, 0.18 from Venter 2021; both European) × each "
          f"city's ERA5-Land daily Tmax and dewpoint, 2019–2024. Source: `felt_heat.csv`.")
    print(f"- **Size:** before the monsoon, +0.1 NDVI goes with a median {a8.d_lst.median():+.2f} °C of "
          f"surface temperature, which becomes {a8.d_tair.median():+.2f} °C of air temperature at r = 0.08 "
          f"({a18.d_tair.median():+.2f} °C at r = 0.18) and {a8.d_hi.median():+.2f} °C of Heat Index "
          f"({a8.uc_id.nunique()} cities). Jodhpur: {v('Jodhpur', 0.08, 'd_lst'):+.2f} → "
          f"{v('Jodhpur', 0.08, 'd_tair'):+.2f} → {v('Jodhpur', 0.08, 'd_hi'):+.2f} °C; Kochi: "
          f"{v('Kochi', 0.08, 'd_lst'):+.2f} → {v('Kochi', 0.08, 'd_tair'):+.2f} → "
          f"{v('Kochi', 0.08, 'd_hi'):+.2f} °C.")
    print(f"- **Felt-heat efficiency (scenario A, dewpoint fixed):** median {e['dry']:.2f} in "
          f"{e['n_dry']} dry cities vs {e['wet']:.2f} in {e['n_wet']} wet ones (Spearman with RH "
          f"ρ = {e['rho']:+.2f}, p = {e['p']:.1g}). [EDIT: if efficiency RISES with humidity, say: the "
          f"Heat Index is steeper in humid air, so each degree of air cooling is felt MORE there, as long "
          f"as leaves add no moisture.]")
    print(f"- **Break-even:** leaves adding about {d['wet']:.2f} °C of dewpoint would cancel the felt "
          f"benefit in wet cities, against {d['dry']:.2f} °C in dry ones (Spearman with RH ρ = "
          f"{d['rho']:+.2f}, p = {d['p']:.1g}). Per degree of air cooling: {dc['wet']:.1f} vs "
          f"{dc['dry']:.1f} °C of dewpoint (ρ = {dc['rho']:+.2f}). In Kochi δ* = "
          f"{v('Kochi', 0.08, 'delta_star'):.2f} °C, in Jodhpur {v('Jodhpur', 0.08, 'delta_star'):.2f} °C.")
    print("- **H6 verdict:** [EDIT from the printed test: supported / partly supported (fragile, not "
          "smaller) / not supported], and whether r = 0.18, the iqr step and post-monsoon agree.")
    print("- **Caveat (always):** both ratios come from European cities; this connects to Borah 2026 "
          "(dense, active canopies with a higher Heat Index in humid Indian cities) but does not measure it.")


# --------------------------------------------------------------------------- figures
def fig_felt_vs_surface(fh, clim):
    apply_style()
    pre_rh = clim[clim.season == 'pre'][['uc_id', 'rh_pct']]
    base = fh[(fh.season == 'pre') & (fh.step == 'ndvi_0.1') & (fh.r == 0.08)].merge(pre_rh, on='uc_id')
    panels = [(0.0, 'Scenario A: cooling only (dewpoint unchanged)'),
              (0.5, 'Scenario B: cooling + leaves add 0.5 °C of dewpoint')]
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.6), layout='constrained', sharex=True, sharey=True)
    vmin, vmax = np.nanpercentile(base.rh_pct, [2, 98])
    for ax, (dl, title) in zip(axes, panels):
        g = base[base.delta_td == dl]
        xs = np.linspace(g.d_lst.min(), g.d_lst.max(), 2)
        ax.plot(xs, 0.08 * xs, ls='--', color=MUTED, lw=1.1,
                label='felt = air cooling (y = 0.08·x, if humidity did not matter)')
        ax.axhline(0, color='k', lw=0.8)
        ax.axvline(0, color='k', lw=0.5, alpha=0.5)
        sc = ax.scatter(g.d_lst, g.d_hi, c=g.rh_pct, cmap='viridis_r', vmin=vmin, vmax=vmax, s=22,
                        edgecolor='white', linewidth=0.4, zorder=3)
        offsets = {
            'Jodhpur': (-42, 6),
            'New Delhi': (4, -11),
            'Hyderabad': (-46, 6) if dl == 0.0 else (4, 4),
            'Chennai': (4, -11) if dl == 0.0 else (-40, 6),
            'Kolkata': (4, 4),
            'Mumbai': (4, 4),
            'Kochi': (4, -10) if dl == 0.0 else (4, 4),
        }
        for nm in LABEL:
            r = g[g.city == nm]
            if len(r):
                ax.annotate(nm, (r.d_lst.iloc[0], r.d_hi.iloc[0]), xytext=offsets.get(nm, (4, 3)),
                            textcoords='offset points', fontsize=8)
        up = (g.d_hi > 0) & (g.d_lst < 0)
        ax.set_title(f'{title}\n{up.sum()} of {(g.d_lst < 0).sum()} greener-is-cooler cities feel hotter',
                     fontsize=10.5)
        ax.set_xlabel('Surface cooling for +0.1 NDVI, ΔLST (°C)')
        ax.legend(loc='upper left', fontsize=8.5)
    axes[0].set_ylabel('Change in felt heat, ΔHeat Index (°C)\nnegative = feels cooler')
    fig.colorbar(sc, ax=axes, label='Pre-monsoon relative humidity (%)', shrink=0.85)
    fig.suptitle(f'H6, pre-monsoon days, r = 0.08 (Du 2024). {SCENARIO_NOTE}.', fontsize=11)
    print(' ', save(fig, 'H6_felt_vs_surface').relative_to(C.ROOT))
    plt.close(fig)


def fig_breakeven(a, t):
    apply_style()
    g = a[(a.season == MAIN['season']) & (a.step == MAIN['step']) & (a.r == MAIN['r'])]
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.2), layout='constrained', sharex=True)
    for ax, col, ylab, metric in (
            (axes[0], 'delta_star', 'Break-even dewpoint rise δ* (°C)\nsmaller = felt benefit more fragile',
             'delta_star'),
            (axes[1], 'delta_star_per_c', 'δ* per °C of air cooling (°C / °C)\nthe climate part only',
             'delta_star_per_c')):
        dry = g.rain_annual_mm < DRY_MM
        ax.scatter(g.rh_pct[dry], g[col][dry], s=22, color=DRY_COLOR, edgecolor='white', lw=0.4,
                   label=f'< {DRY_MM:,} mm/yr ({dry.sum()})', zorder=3)
        ax.scatter(g.rh_pct[~dry], g[col][~dry], s=22, color=WET_COLOR, edgecolor='white', lw=0.4,
                   label=f'≥ {DRY_MM:,} mm/yr ({(~dry).sum()})', zorder=3)
        offsets = {
            'Mumbai': (4, 8) if col == 'delta_star_per_c' else (4, 3),
            'Kolkata': (4, -2) if col == 'delta_star_per_c' else (4, 3),
            'Chennai': (-38, -10) if col == 'delta_star_per_c' else (4, 3),
        }
        for nm in LABEL:
            r = g[g.city == nm]
            if len(r):
                ax.annotate(nm, (r.rh_pct.iloc[0], r[col].iloc[0]), xytext=offsets.get(nm, (4, 3)),
                            textcoords='offset points', fontsize=8)
        q = t[(t.metric == metric) & (t.test == 'spearman_rh')]
        for k, v in MAIN.items():
            q = q[q[k] == v]
        if len(q):
            ax.text(0.98, 0.97, f'Spearman ρ = {q.value.iloc[0]:+.2f} (p = {q.p.iloc[0]:.1g})\n'
                    f'n = {q.n_cities.iloc[0]} cities', transform=ax.transAxes, ha='right', va='top',
                    fontsize=9, bbox=dict(fc='white', ec='none', alpha=0.85))
        ax.set_yscale('log')
        ax.set_ylabel(ylab)
        ax.set_xlabel('Pre-monsoon relative humidity (%)')
        ax.legend(loc='lower left', fontsize=8.5)
    nan = g.delta_star.isna().sum()
    fig.suptitle(f"H6 break-even: the dewpoint rise from leaves that cancels the felt benefit "
                 f"(pre-monsoon, +0.1 NDVI, r = 0.08{'; ' + str(nan) + ' cities never break even' if nan else ''})."
                 f"\n{SCENARIO_NOTE}.", fontsize=10.5)
    print(' ', save(fig, 'H6_breakeven').relative_to(C.ROOT))
    plt.close(fig)


def main():
    ce, daily, clim, iqr = load_inputs()
    print(f"{ce.uc_id.nunique()} cities with main-spec daytime slopes ({', '.join(C.H6_SEASONS)}); "
          f"daily climate for {daily.uc_id.nunique()} cities; NDVI spread for {len(iqr)} cities "
          f"(median p25→p75 {iqr.ndvi_iqr.median():.3f})")
    fh = run(ce, daily, clim, iqr)
    fh.sort_values(['uc_id', 'season', 'step', 'r', 'delta_td']).to_csv(OUT, index=False)
    print(f'{len(fh):,} rows -> {OUT.relative_to(C.ROOT)}')
    checks(fh, ce, daily, clim)
    t, a = h6_test(fh, ce, clim)
    t.to_csv(TEST_OUT, index=False)
    print(f'{len(t)} rows -> {TEST_OUT.relative_to(C.ROOT)}')
    out = verdict(t, a)
    draft_observations(out, fh, clim)
    print('\nFigures:')
    fig_felt_vs_surface(fh, clim)
    fig_breakeven(a, t)


if __name__ == '__main__':
    main()
