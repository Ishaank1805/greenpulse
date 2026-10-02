"""Task F: who gets the cooling? People-weighted vs area-weighted heat and greenness.

Per city x season, over urban squares (built >= 0.10):
  area_*  plain mean over squares
  pop_*   mean weighted by WorldPop 2020 people per square
  gap_*   pop_* - area_*
          gap_lst > 0  -> people live in hotter-than-average squares
          gap_ndvi < 0 -> people live in less-green-than-average squares
Night uses squares with >= MIN_NIGHTS clear nights, as script 03 does.
A city (or its night value) is skipped below MIN_SQUARES squares, as in script 03.

Usage: python scripts/12_exposure.py
Output: data/results/exposure.csv, figures/F_*.png
"""
import json

import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np
import pandas as pd

import config as C
from style import (DRY_COLOR, DRY_MM, MUTED, SEASON_COLORS, SEASON_LABELS, SEASONS,
                   WET_COLOR, apply_style, save)

BUILT_MIN = 0.10
MIN_NIGHTS = 10
MIN_SQUARES = 30
OUT = C.DATA / 'results' / 'exposure.csv'
CLIMATE = C.DATA / 'results' / 'city_climate.csv'
COLS = ['uc_id', 'city', 'season', 'area_lst_day', 'pop_lst_day', 'gap_lst_day',
        'area_lst_night', 'pop_lst_night', 'gap_lst_night',
        'area_ndvi', 'pop_ndvi', 'gap_ndvi', 'n_cells', 'pop_total']


def load_samples():
    """All long-format city samples. The archived pilot (_pilot_v1/) is not matched."""
    paths = sorted(C.SAMPLES_DIR.glob('*.csv'))
    return pd.concat([pd.read_csv(p) for p in paths], ignore_index=True)


def weighted(values, weights):
    return (values * weights).sum() / weights.sum()


def city_season(d):
    """One exposure row for one city x season of urban squares."""
    day = d.dropna(subset=['lst_day', 'ndvi', 'pop'])
    if len(day) < MIN_SQUARES or day['pop'].sum() <= 0:
        return None
    row = dict(n_cells=len(day), pop_total=day['pop'].sum())
    for col in ('lst_day', 'ndvi'):
        row[f'area_{col}'] = day[col].mean()
        row[f'pop_{col}'] = weighted(day[col], day['pop'])
        row[f'gap_{col}'] = row[f'pop_{col}'] - row[f'area_{col}']

    night = d[d.n_night >= MIN_NIGHTS].dropna(subset=['lst_night', 'pop'])
    if len(night) >= MIN_SQUARES and night['pop'].sum() > 0:
        row['area_lst_night'] = night.lst_night.mean()
        row['pop_lst_night'] = weighted(night.lst_night, night['pop'])
        row['gap_lst_night'] = row['pop_lst_night'] - row['area_lst_night']
    return row


def build(samples):
    urban = samples[samples.built >= BUILT_MIN]
    rows = []
    for (uc_id, city, season), d in urban.groupby(['uc_id', 'city', 'season']):
        row = city_season(d)
        if row:
            rows.append(dict(uc_id=uc_id, city=city, season=season, **row))
    return pd.DataFrame(rows).reindex(columns=COLS)


def add_rain(ex):
    if not CLIMATE.exists():
        return ex.assign(rain_annual_mm=np.nan)
    rain = pd.read_csv(CLIMATE).groupby('uc_id').rain_annual_mm.first()
    return ex.assign(rain_annual_mm=ex.uc_id.map(rain))


def summarise(ex):
    print(f'\n{ex.uc_id.nunique()} cities with >= {MIN_SQUARES} urban squares')
    for season in SEASONS:
        e = ex[ex.season == season]
        night = e.dropna(subset=['gap_lst_night'])
        print(f'\n[{season}] n = {len(e)} cities')
        print(f'  day   gap_lst > 0: {(e.gap_lst_day > 0).mean():.0%}  '
              f'median {e.gap_lst_day.median():+.2f} C  (IQR {e.gap_lst_day.quantile(.25):+.2f} '
              f'to {e.gap_lst_day.quantile(.75):+.2f})')
        print(f'  ndvi  gap < 0:     {(e.gap_ndvi < 0).mean():.0%}  median {e.gap_ndvi.median():+.3f}')
        print(f'  night gap_lst > 0: {(night.gap_lst_night > 0).mean():.0%}  '
              f'median {night.gap_lst_night.median():+.2f} C  (n = {len(night)})')
        if e.rain_annual_mm.notna().any():
            for label, g in (('< 1000 mm', e[e.rain_annual_mm < DRY_MM]),
                             ('>= 1000 mm', e[e.rain_annual_mm >= DRY_MM])):
                print(f'  {label:>10}: n = {len(g)}, day gap > 0 {(g.gap_lst_day > 0).mean():.0%}, '
                      f'median {g.gap_lst_day.median():+.2f} C')
    top = ex[ex.season == 'pre'].nlargest(10, 'gap_lst_day')
    print('\nLargest pre-monsoon daytime gaps:')
    print(top[['city', 'gap_lst_day', 'gap_ndvi', 'n_cells']].round(2).to_string(index=False))


def fig_hist(ex):
    e = ex[ex.season == 'pre']
    fig, ax = plt.subplots(figsize=(6.5, 4))
    ax.hist(e.gap_lst_day, bins=30, color=SEASON_COLORS['pre'], alpha=0.85)
    ax.axvline(0, color='black', lw=1)
    share = (e.gap_lst_day > 0).mean()
    ax.text(0.98, 0.95, f'{share:.0%} of {len(e)} cities:\npeople live in hotter squares',
            transform=ax.transAxes, ha='right', va='top')
    ax.set_xlabel('People-weighted minus area-average surface temperature (°C)\n'
                  'positive = people live in hotter-than-average squares')
    ax.set_ylabel('Number of cities')
    ax.set_title(f'{SEASON_LABELS["pre"]}, daytime')
    return save(fig, 'F_exposure_gap_hist')


def fig_dumbbell(ex, n=20):
    with open(C.CITIES_FILE) as f:
        pop25 = {ft['properties']['ID_UC_G0']: ft['properties']['pop_2025']
                 for ft in json.load(f)['features']}
    e = ex[ex.season == 'pre'].assign(pop_2025=lambda d: d.uc_id.map(pop25))
    e = e.nlargest(n, 'pop_2025').sort_values('gap_lst_day')
    fig, ax = plt.subplots(figsize=(6.5, 7))
    y = np.arange(len(e))
    ax.hlines(y, e.area_lst_day, e.pop_lst_day, color=MUTED, lw=2)
    ax.scatter(e.area_lst_day, y, color='white', edgecolor='black', zorder=3, label='Area average')
    ax.scatter(e.pop_lst_day, y, color=SEASON_COLORS['pre'], zorder=3, label='People-weighted')
    ax.set_yticks(y, e.city)
    ax.set_xlabel('Daytime land-surface temperature (°C), urban squares')
    ax.set_title(f'{n} most populous cities, {SEASON_LABELS["pre"]}\nsorted by gap (largest at top)')
    ax.legend(loc='upper right')
    ax.grid(axis='y', visible=False)
    return save(fig, 'F_exposure_dumbbell')


def fig_by_season(ex):
    """Share of cities where people live in hotter squares, by season, day vs night."""
    rows = []
    for season in SEASONS:
        e = ex[ex.season == season]
        night = e.gap_lst_night.dropna()
        rows.append((season, (e.gap_lst_day > 0).mean(), len(e), (night > 0).mean(), len(night)))
    fig, ax = plt.subplots(figsize=(6.5, 4))
    x = np.arange(len(rows))
    for i, (season, day, n_day, night, n_night) in enumerate(rows):
        c = SEASON_COLORS[season]
        ax.bar(i - 0.2, day * 100, 0.38, color=c, alpha=0.55)
        ax.bar(i + 0.2, night * 100, 0.38, color=c)
        ax.text(i - 0.2, day * 100 + 1.5, f'{day:.0%}\nn={n_day}', ha='center', va='bottom', fontsize=9)
        ax.text(i + 0.2, night * 100 + 1.5, f'{night:.0%}\nn={n_night}', ha='center', va='bottom', fontsize=9)
    ax.set_xticks(x, [SEASON_LABELS[r[0]].replace(' (', '\n(') for r in rows])
    ax.set_ylim(0, 112)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.axhline(50, color=MUTED, lw=0.8, ls='--')
    ax.set_ylabel('Cities where people live in\nhotter-than-average squares (%)')
    ax.legend(handles=[Patch(color=MUTED, alpha=0.45, label='Day (lighter bar)'),
                       Patch(color=MUTED, label='Night (darker bar)')],
              loc='upper center', bbox_to_anchor=(0.5, -0.2), ncol=2)
    ax.grid(axis='x', visible=False)
    return save(fig, 'F_exposure_by_season')


def fig_crowded_vs_green(ex):
    e = ex[ex.season == 'pre']
    colour = np.where(e.rain_annual_mm < DRY_MM, DRY_COLOR,
                      np.where(e.rain_annual_mm >= DRY_MM, WET_COLOR, MUTED))
    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.scatter(e.gap_ndvi, e.gap_lst_day, c=colour, s=18, alpha=0.8)
    ax.axhline(0, color='black', lw=0.8)
    ax.axvline(0, color='black', lw=0.8)
    if e.rain_annual_mm.notna().any():
        for c, label in ((DRY_COLOR, f'< {DRY_MM} mm/yr'), (WET_COLOR, f'≥ {DRY_MM} mm/yr')):
            ax.scatter([], [], c=c, label=label)
        ax.legend(loc='upper right')
    ax.set_xlabel('People-weighted minus area-average NDVI\nnegative = people live in less-green squares')
    ax.set_ylabel('People-weighted minus area-average\ndaytime surface temperature (°C)')
    ax.set_title(f'{SEASON_LABELS["pre"]}: one point per city')
    return save(fig, 'F_crowded_vs_green')


def checks(samples, ex):
    """Checks from role_4_exposure_story.md, step F."""
    jod = samples[(samples.city == 'Jodhpur') & (samples.season == 'pre')]
    total = jod['pop'].sum()
    assert 0.95e6 < total < 1.0e6, f'Jodhpur population {total:,.0f}, expected ~979,491'

    d = jod[jod.built >= BUILT_MIN].dropna(subset=['lst_day', 'ndvi', 'pop'])
    hand = np.average(d.lst_day, weights=d['pop'])
    got = ex[(ex.city == 'Jodhpur') & (ex.season == 'pre')].pop_lst_day.item()
    assert abs(hand - got) < 1e-9, (hand, got)

    urban = samples[samples.built >= BUILT_MIN]
    lo = urban.groupby(['uc_id', 'season']).lst_day.min()
    hi = urban.groupby(['uc_id', 'season']).lst_day.max()
    key = pd.MultiIndex.from_frame(ex[['uc_id', 'season']])
    assert ((ex.pop_lst_day.values >= lo.reindex(key).values)
            & (ex.pop_lst_day.values <= hi.reindex(key).values)).all()
    print(f'Checks passed: Jodhpur total {total:,.0f} people; hand-computed weighted mean matches; '
          'every weighted mean lies within its city range.')


def main():
    apply_style()
    samples = load_samples()
    ex = build(samples)
    checks(samples, ex)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    ex.to_csv(OUT, index=False)
    print(f'{len(ex)} rows -> {OUT.relative_to(C.ROOT)}')

    ex = add_rain(ex)
    summarise(ex)
    for path in (fig_hist(ex), fig_dumbbell(ex), fig_by_season(ex), fig_crowded_vs_green(ex)):
        print('figure ->', path.relative_to(C.ROOT))


if __name__ == '__main__':
    main()
