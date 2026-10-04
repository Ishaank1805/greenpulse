"""Task S: same-city seasonal comparison of the cooling slope (H4).

Main spec (common.main_spec), all values per 0.1 NDVI. Negative slope = greener is cooler.
    d_post_pre   = ce_post - ce_pre,   se = sqrt(se_post^2 + se_pre^2)
    d_winter_pre = ce_winter - ce_pre, likewise
    d_post_pre < 0 -> cooling is STRONGER after the monsoon.
The se treats the two seasons as independent. That is conservative: the same squares
are used in both seasons, so the true se of the difference is usually smaller.

If data/results/city_climate.csv exists (Role 2), also fits
    d_post_pre ~ delta_swvl1 (WLS, weights 1/se_d^2, HC3)  and splits by < / >= 1000 mm.

Usage: python scripts/10_seasons.py
Output: data/results/seasons.csv, figures/S_season_paired.png, figures/S_dce_vs_dsoil.png
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import wilcoxon

import config as C
from common import DRY_MM, load_climate, main_spec
from style import (CE_LABEL, DRY_COLOR, MUTED, SEASON_COLORS, SEASON_LABELS, SEASONS, WET_COLOR,
                   apply_style, save)

OUT = C.DATA / 'results' / 'seasons.csv'
COLS = ['uc_id', 'city', 'time', 'ce_pre', 'ce_post', 'ce_winter', 'd_post_pre', 'se_d_post_pre',
        'd_winter_pre', 'se_d_winter_pre']
LABEL = ['Jodhpur', 'Kochi']


def build(ce):
    ms = main_spec(ce).dropna(subset=['ce'])
    ms = ms.assign(c=ms['ce_per_0.1'], s=ms.se / 10)
    w = ms.pivot_table(index=['uc_id', 'city', 'time'], columns='season', values=['c', 's'])
    w.columns = [f'{a}_{b}' for a, b in w.columns]
    w = w.reset_index()
    out = pd.DataFrame({'uc_id': w.uc_id, 'city': w.city, 'time': w.time,
                        'ce_pre': w.get('c_pre'), 'ce_post': w.get('c_post'),
                        'ce_winter': w.get('c_winter')})
    out['d_post_pre'] = out.ce_post - out.ce_pre
    out['se_d_post_pre'] = np.sqrt(w.s_post ** 2 + w.s_pre ** 2)
    out['d_winter_pre'] = out.ce_winter - out.ce_pre
    out['se_d_winter_pre'] = np.sqrt(w.s_winter ** 2 + w.s_pre ** 2)
    n_any = out.groupby('time').size()
    kept = out.dropna(subset=['ce_pre', 'ce_post'])
    return kept[COLS].reset_index(drop=True), n_any


def summarise(s, n_any):
    lines = []
    for time, g in s.groupby('time'):
        for d, a, b in (('d_post_pre', 'ce_post', 'ce_pre'), ('d_winter_pre', 'ce_winter', 'ce_pre')):
            gg = g.dropna(subset=[d])
            p = wilcoxon(gg[a], gg[b]).pvalue if len(gg) > 5 else np.nan
            sig_str = ((gg[d] + 1.96 * gg['se_' + d]) < 0).mean()
            sig_weak = ((gg[d] - 1.96 * gg['se_' + d]) > 0).mean()
            lines.append(dict(time=time, contrast=d, n_cities=len(gg), median_d=gg[d].median(),
                              share_d_neg=(gg[d] < 0).mean(), wilcoxon_p=p,
                              share_sig_stronger=sig_str, share_sig_weaker=sig_weak))
    t = pd.DataFrame(lines)
    print('\n=== H4: same-city change in cooling slope (°C per 0.1 NDVI; d < 0 = stronger cooling) ===')
    for _, r in t.iterrows():
        print(f"  {r.time:5s} {r.contrast:13s} n={r.n_cities:3d}  median {r.median_d:+.2f}  "
              f"d<0 in {r.share_d_neg:.0%}  Wilcoxon p={r.wilcoxon_p:.2g}  "
              f"sig stronger {r.share_sig_stronger:.0%} / weaker {r.share_sig_weaker:.0%}")
    for time in ('day', 'night'):
        lost = n_any.get(time, 0) - (s.time == time).sum()
        print(f'  {time}: {(s.time == time).sum()} cities with pre and post; {lost} lost to a '
              f'missing pre or post estimate')
    return t


def moisture_link(s, clim):
    if clim is None:
        print('\n(city_climate.csv not found: skipping the soil-moisture link and rainfall colours)')
        return None
    sw = clim.pivot_table(index='uc_id', columns='season', values='swvl1')
    rain = clim.groupby('uc_id').rain_annual_mm.first()
    d = s[s.time == 'day'].merge((sw['post'] - sw['pre']).rename('d_swvl1'), on='uc_id')
    d = d.merge(rain.rename('rain'), on='uc_id').dropna(subset=['d_post_pre', 'd_swvl1'])
    X = sm.add_constant(d[['d_swvl1']])
    m = sm.WLS(d.d_post_pre, X, weights=1 / d.se_d_post_pre ** 2).fit(cov_type='HC3')
    lo, hi = m.conf_int().loc['d_swvl1']
    print(f'\nMoisture link (day): d_post_pre ~ Δswvl1, slope {m.params.d_swvl1:+.2f} per m³/m³ '
          f'(95% {lo:+.2f} to {hi:+.2f}), p={m.pvalues.d_swvl1:.2g}, n={len(d)}')
    for grp, g in d.groupby(d.rain < DRY_MM):
        print(f"  {'< ' if grp else '≥ '}{DRY_MM} mm: n={len(g)}, median d_post_pre "
              f"{g.d_post_pre.median():+.2f}, d<0 in {(g.d_post_pre < 0).mean():.0%}")
    return d, m


def fig_paired(s, rain):
    fig, axes = plt.subplots(1, 2, figsize=(11, 5.2), layout='constrained')
    x = np.arange(3)
    for ax, time in zip(axes, ('day', 'night')):
        g = s[s.time == time]
        for _, r in g.iterrows():
            ys = [r.ce_pre, r.ce_post, r.ce_winter]
            col = MUTED
            if rain is not None and r.uc_id in rain.index:
                col = DRY_COLOR if rain[r.uc_id] < DRY_MM else WET_COLOR
            ax.plot(x, ys, color=col, lw=0.6, alpha=0.3)
        med = [g.ce_pre.median(), g.ce_post.median(), g.ce_winter.median()]
        ax.plot(x, med, color='k', lw=3, marker='o', label='median city')
        for name, ls in zip(LABEL, ('-', '--')):
            r = g[g.city == name]
            if len(r):
                r = r.iloc[0]
                ax.plot(x, [r.ce_pre, r.ce_post, r.ce_winter], color='crimson', lw=1.8, ls=ls)
        ax.axhline(0, color='k', lw=0.8)
        ax.set_xticks(x, [SEASON_LABELS[k].replace(' (', '\n(') for k in SEASONS])
        for t, k in zip(ax.get_xticklabels(), SEASONS):
            t.set_color(SEASON_COLORS[k])
        ax.set_title(f"{'Day (~13:30)' if time == 'day' else 'Night (~01:30)'}: {len(g)} cities")
        ax.set_ylim(np.nanpercentile(g[['ce_pre', 'ce_post', 'ce_winter']], 1) - 0.3,
                    np.nanpercentile(g[['ce_pre', 'ce_post', 'ce_winter']], 99) + 0.3)
    axes[0].set_ylabel(CE_LABEL)
    handles = [plt.Line2D([], [], color='k', lw=3, label='median city'),
               plt.Line2D([], [], color='crimson', lw=1.8, label='Jodhpur'),
               plt.Line2D([], [], color='crimson', lw=1.8, ls='--', label='Kochi')]
    if rain is not None:
        handles += [plt.Line2D([], [], color=DRY_COLOR, label=f'< {DRY_MM} mm/yr rain'),
                    plt.Line2D([], [], color=WET_COLOR, label=f'≥ {DRY_MM} mm/yr rain')]
    axes[1].legend(handles=handles, loc='lower right', fontsize=9)
    fig.suptitle('The same city in three seasons (one line per city; y axis clipped at 1st–99th percentile)')
    print(' ', save(fig, 'S_season_paired').relative_to(C.ROOT))
    plt.close(fig)


def fig_dsoil(d, m):
    fig, ax = plt.subplots(figsize=(7, 5), layout='constrained')
    col = np.where(d.rain < DRY_MM, DRY_COLOR, WET_COLOR)
    ax.errorbar(d.d_swvl1, d.d_post_pre, yerr=1.96 * d.se_d_post_pre, fmt='none',
                ecolor=MUTED, alpha=0.25, lw=0.6)
    ax.scatter(d.d_swvl1, d.d_post_pre, c=col, s=16, zorder=3)
    xs = np.linspace(d.d_swvl1.min(), d.d_swvl1.max(), 50)
    pr = m.get_prediction(sm.add_constant(pd.DataFrame({'d_swvl1': xs}))).summary_frame()
    ax.plot(xs, pr['mean'], color='k')
    ax.fill_between(xs, pr.mean_ci_lower, pr.mean_ci_upper, color='k', alpha=0.12, lw=0)
    ax.axhline(0, color='k', lw=0.8)
    lo, hi = m.conf_int().loc['d_swvl1']
    ax.set_title(f'Day: slope {m.params.d_swvl1:+.2f} (95% {lo:+.2f} to {hi:+.2f}), n = {len(d)}')
    ax.set_xlabel('Soil wetting, post − pre (Δ swvl1, m³/m³)')
    ax.set_ylabel('Change in cooling slope, post − pre\n(°C per 0.1 NDVI); negative = stronger '
                  'cooling after monsoon')
    print(' ', save(fig, 'S_dce_vs_dsoil').relative_to(C.ROOT))
    plt.close(fig)


def checks(s, ce):
    ok = True
    ms = main_spec(ce)
    for name in LABEL:
        for time in ('day', 'night'):
            r = s[(s.city == name) & (s.time == time)]
            if r.empty:
                continue
            g = ms[(ms.city == name) & (ms.time == time)].set_index('season')['ce_per_0.1']
            hand = g['post'] - g['pre']
            good = abs(hand - r.d_post_pre.iloc[0]) < 1e-12
            ok &= good
            print(f'  check {name} {time}: d_post_pre {r.d_post_pre.iloc[0]:+.4f} = by hand '
                  f'{hand:+.4f}: {"ok" if good else "FAIL"}')
    return ok


def main():
    apply_style()
    ce = pd.read_csv(C.DATA / 'results' / 'cooling_efficiency.csv')
    s, n_any = build(ce)
    s.to_csv(OUT, index=False)
    print(f'{len(s)} city x time rows -> {OUT.relative_to(C.ROOT)}')
    ok = checks(s, ce)
    t = summarise(s, n_any)
    t.to_csv(C.DATA / 'results' / 'seasons_summary.csv', index=False)
    clim = load_climate()
    rain = None if clim is None else clim.groupby('uc_id').rain_annual_mm.first()
    fig_paired(s, rain)
    ml = moisture_link(s, clim)
    if ml is not None:
        fig_dsoil(*ml)
    print('checks:', 'ALL OK' if ok else 'FAILED')
    return ok


if __name__ == '__main__':
    raise SystemExit(0 if main() else 1)
