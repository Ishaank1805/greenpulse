"""Task 8: who receives greenness, and the cooling it brings? Lorenz curves and Gini.

Per city x season, over urban squares (built >= 0.10, with day LST, NDVI and people),
the same squares as 12_exposure.py and the cooling slope:

  gini_ndvi     inequality of greenness across people: every person gets their square's
                NDVI (clipped at 0, since water squares can be slightly negative)
  gini_cooling  inequality of the cooling greenery provides across people, for cities
                whose main-spec daytime slope is negative (greener is cooler):
                cooling = -ce_per_0.1 x (NDVI - city 10th-percentile NDVI) / 0.1, clipped at 0
                i.e. how much cooler a square is than the city's barest squares,
                by the city's own slope

Gini 0 = everyone gets the same; close to 1 = a few squares get it all.

  *_area        the same Gini with every square counted once (not weighted by people).
  people_gap_*  people-weighted minus area Gini. Positive = greenness / cooling is shared
                more unequally among people than across the city's land, i.e. it sits
                away from where most people live. This is the comparison that matters:
                the raw Gini values depend on the scale of NDVI and on the 10th-percentile
                baseline, so they are not comparable with greenspace-access Gini values
                such as Chen et al. 2022.

Usage: python scripts/17_lorenz.py
Output: data/results/lorenz.csv, figures/L_lorenz_examples.png, figures/L_people_gap.png
"""
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

import config as C
from common import load_climate, load_samples, main_spec
from style import (DRY_COLOR, DRY_MM, MUTED, SEASON_LABELS, SEASONS, WET_COLOR,
                   apply_style, save)

BUILT_MIN = 0.10
MIN_SQUARES = 30
P_BARE = 10        # percentile of NDVI that counts as the city's "barest" squares
OUT = C.DATA / 'results' / 'lorenz.csv'
COLS = ['uc_id', 'city', 'season', 'gini_ndvi', 'gini_cooling', 'n_cells', 'pop_total',
        'gini_ndvi_area', 'gini_cooling_area', 'people_gap_ndvi', 'people_gap_cooling']
EXAMPLES = ['New Delhi', 'Mumbai', 'Kolkata', 'Bengaluru', 'Jodhpur', 'Kochi']


# ---------------------------------------------------------------- core maths
def lorenz(values, weights):
    """Weighted Lorenz curve. Returns (x, y): cumulative share of people, of the total.
    Both start at 0 and end at 1."""
    v = np.asarray(values, float)
    w = np.asarray(weights, float)
    order = np.argsort(v, kind='stable')
    v, w = v[order], w[order]
    x = np.concatenate([[0.0], np.cumsum(w) / w.sum()])
    y = np.concatenate([[0.0], np.cumsum(v * w) / (v * w).sum()])
    return x, y


def gini(values, weights):
    """Gini = 1 - 2 x (area under the Lorenz curve), trapezoid rule."""
    x, y = lorenz(values, weights)
    return 1.0 - np.sum(np.diff(x) * (y[1:] + y[:-1]))


def gini_mad(values, weights):
    """Same Gini by a different formula, the weighted mean absolute difference:
    G = sum_ij w_i w_j |x_i - x_j| / (2 mean W^2). Used only as a check."""
    v = np.asarray(values, float)
    w = np.asarray(weights, float)
    W = w.sum()
    mean = (v * w).sum() / W
    return (w[:, None] * w[None, :] * np.abs(v[:, None] - v[None, :])).sum() / (2 * mean * W ** 2)


# ---------------------------------------------------------------- per city
def urban(samples):
    d = samples[samples.built >= BUILT_MIN].dropna(subset=['lst_day', 'ndvi', 'pop'])
    return d[d['pop'] >= 0]


def cooling_received(ndvi, slope_per_01):
    bare = np.percentile(ndvi, P_BARE)
    return np.clip(-slope_per_01 * (ndvi - bare) / 0.1, 0, None)


def build(samples, slopes):
    rows, skipped = [], 0
    for (uc_id, city, season), d in urban(samples).groupby(['uc_id', 'city', 'season']):
        if len(d) < MIN_SQUARES or d['pop'].sum() <= 0:
            continue
        ndvi = d.ndvi.clip(lower=0).values
        ones = np.ones(len(d))
        row = dict(uc_id=uc_id, city=city, season=season, n_cells=len(d),
                   pop_total=d['pop'].sum(), gini_ndvi=gini(ndvi, d['pop'].values),
                   gini_ndvi_area=gini(ndvi, ones), gini_cooling=np.nan, gini_cooling_area=np.nan)
        row['people_gap_ndvi'] = row['gini_ndvi'] - row['gini_ndvi_area']
        s = slopes.get((uc_id, season))
        if s is not None and s < 0:
            cool = cooling_received(d.ndvi.values, s)
            if (cool * d['pop'].values).sum() > 0:
                row['gini_cooling'] = gini(cool, d['pop'].values)
                row['gini_cooling_area'] = gini(cool, ones)
                row['people_gap_cooling'] = row['gini_cooling'] - row['gini_cooling_area']
        else:
            skipped += 1
        rows.append(row)
    return pd.DataFrame(rows).reindex(columns=COLS), skipped


# ---------------------------------------------------------------- checks
def checks(samples, out):
    n = 50
    equal = gini(np.full(n, 0.4), np.full(n, 1000.0))
    assert abs(equal) < 1e-12, f'equal case gave {equal}'
    one = np.zeros(n); one[7] = 0.8
    conc = gini(one, np.full(n, 1000.0))
    assert abs(conc - (1 - 1 / n)) < 1e-12, f'concentrated case gave {conc}, expected {1 - 1 / n}'

    d = urban(samples)
    d = d[(d.city == 'Jodhpur') & (d.season == 'pre')]
    ndvi = d.ndvi.clip(lower=0).values
    a, b = gini(ndvi, d['pop'].values), gini_mad(ndvi, d['pop'].values)
    assert abs(a - b) < 1e-6, f'Jodhpur: trapezoid {a} vs mean-absolute-difference {b}'
    got = out[(out.city == 'Jodhpur') & (out.season == 'pre')].gini_ndvi.item()
    assert abs(got - a) < 1e-12

    g = out[['gini_ndvi', 'gini_cooling', 'gini_ndvi_area', 'gini_cooling_area']].stack().dropna()
    assert ((g >= 0) & (g <= 1)).all(), 'a Gini is outside 0-1'
    print(f'Checks passed: equal case 0, concentrated case {conc:.4f} (= 1 - 1/{n}), '
          f'Jodhpur trapezoid {a:.6f} = mean-absolute-difference {b:.6f}, all Gini in 0-1.')


# ---------------------------------------------------------------- summary
def summarise(out, skipped):
    print(f'\n{out.uc_id.nunique()} cities with >= {MIN_SQUARES} urban squares; '
          f'{skipped} city-seasons skipped for cooling (daytime slope not negative)')
    print('\nMedian Gini by season (people-weighted, and with every square counted once):')
    print(out.groupby('season')[['gini_ndvi', 'gini_ndvi_area', 'gini_cooling', 'gini_cooling_area']]
          .median().reindex(SEASONS).round(3).to_string())
    print('\nPeople gap (people-weighted minus area Gini); share > 0 = shared more unequally among people:')
    for season in SEASONS:
        e = out[out.season == season]
        for col in ('people_gap_ndvi', 'people_gap_cooling'):
            v = e[col].dropna()
            print(f'  {season:6s} {col:19s} median {v.median():+.3f}, > 0 in {(v > 0).mean():.0%} of {len(v)} cities')
    pre = out[out.season == 'pre'].dropna(subset=['gini_cooling'])
    print('\nPre-monsoon, most unequal cooling:')
    print(pre.nlargest(5, 'gini_cooling')[['city', 'gini_ndvi', 'gini_cooling', 'n_cells']]
          .round(3).to_string(index=False))
    print('Pre-monsoon, least unequal cooling:')
    print(pre.nsmallest(5, 'gini_cooling')[['city', 'gini_ndvi', 'gini_cooling', 'n_cells']]
          .round(3).to_string(index=False))
    print('\nSpearman, pre-monsoon (rho, p):')
    for col in ('gini_ndvi', 'gini_cooling'):
        p = out[out.season == 'pre'].dropna(subset=[col])
        for other in ('n_cells', 'rain_annual_mm'):
            q = p.dropna(subset=[other])
            r = spearmanr(q[col], q[other])
            print(f'  {col} vs {other}: {r.statistic:+.2f}, p = {r.pvalue:.3g}, n = {len(q)}')
    for col in ('gini_ndvi', 'gini_cooling'):
        p = out[out.season == 'pre'].dropna(subset=[col, 'rain_annual_mm'])
        dry, wet = p[p.rain_annual_mm < DRY_MM][col], p[p.rain_annual_mm >= DRY_MM][col]
        print(f'  {col} median: < {DRY_MM} mm {dry.median():.3f} (n {len(dry)}), '
              f'>= {DRY_MM} mm {wet.median():.3f} (n {len(wet)})')


# ---------------------------------------------------------------- figures
def fig_examples(samples, slopes):
    d = urban(samples)
    d = d[d.season == 'pre']
    fig, axes = plt.subplots(2, 3, figsize=(10, 6.6), sharex=True, sharey=True)
    for ax, name in zip(axes.flat, EXAMPLES):
        c = d[d.city == name]
        ax.plot([0, 1], [0, 1], color=MUTED, lw=1, ls='--', label='Perfect equality')
        x, y = lorenz(c.ndvi.clip(lower=0), c['pop'])
        ax.plot(x, y, color='#1B7F3B', lw=2, label=f'Greenness (Gini {gini(c.ndvi.clip(lower=0), c["pop"]):.2f})')
        s = slopes.get((c.uc_id.iloc[0], 'pre'))
        if s is not None and s < 0:
            cool = cooling_received(c.ndvi.values, s)
            x, y = lorenz(cool, c['pop'])
            ax.plot(x, y, color='#E07B00', lw=2, label=f'Cooling (Gini {gini(cool, c["pop"]):.2f})')
        ax.set_title(name)
        ax.legend(loc='upper left', fontsize=8)
        ax.set_aspect('equal')
    for ax in axes[-1]:
        ax.set_xlabel('Share of people\n(least to most green)')
    for ax in axes[:, 0]:
        ax.set_ylabel('Share of total received')
    fig.suptitle(f'Who receives greenness and cooling, {SEASON_LABELS["pre"]}', y=1.0)
    fig.tight_layout()
    return save(fig, 'L_lorenz_examples')


def fig_people_gap(out):
    """People-weighted minus area Gini, per city: > 0 = sits away from where people live."""
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), sharey=True)
    for ax, col, colour, label in ((axes[0], 'people_gap_ndvi', '#1B7F3B', 'Greenness'),
                                   (axes[1], 'people_gap_cooling', '#E07B00', 'Cooling')):
        rows = []
        for season in SEASONS:
            v = out[out.season == season][col].dropna()
            rows.append(v)
        ticks = [f"{SEASON_LABELS[s].split(' (')[0]}\n{(v > 0).mean():.0%} above 0"
                 for s, v in zip(SEASONS, rows)]
        ax.boxplot(rows, tick_labels=ticks,
                   widths=0.5, showfliers=False, patch_artist=True,
                   boxprops=dict(facecolor=colour, alpha=0.35, edgecolor=colour),
                   medianprops=dict(color=colour, lw=2), whiskerprops=dict(color=colour),
                   capprops=dict(color=colour))
        ax.axhline(0, color='black', lw=1)
        ax.set_title(label)
        ax.grid(axis='x', visible=False)
    axes[0].set_ylabel('People-weighted minus area Gini\n(above 0 = away from people)')
    fig.suptitle('Is greenness, and its cooling, shared more unequally among people than across land?', y=1.02)
    fig.tight_layout()
    return save(fig, 'L_people_gap')


def main():
    apply_style()
    samples = load_samples()
    ce = main_spec(pd.read_csv(C.DATA / 'results' / 'cooling_efficiency.csv'))
    day = ce[(ce.time == 'day')].dropna(subset=['ce'])
    slopes = {(u, s): v for u, s, v in zip(day.uc_id, day.season, day['ce_per_0.1'])}

    out, skipped = build(samples, slopes)
    checks(samples, out)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)
    print(f'{len(out)} rows -> {OUT.relative_to(C.ROOT)}')

    clim = load_climate()
    rain = clim.groupby('uc_id').rain_annual_mm.first() if clim is not None else pd.Series(dtype=float)
    summarise(out.assign(rain_annual_mm=out.uc_id.map(rain)), skipped)
    for path in (fig_examples(samples, slopes), fig_people_gap(out)):
        print('figure ->', path.relative_to(C.ROOT))


if __name__ == '__main__':
    main()
