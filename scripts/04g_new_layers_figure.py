"""Figure B: the two layers added in the final phase.

Left: the 303 cities coloured by median urban building height (GHSL 2018,
built-surface weighted; squares with built >= 0.10, pre rows).
Right: daily solar radiation per city, pre-monsoon (x) against post-monsoon
and winter (y), with the 1:1 line (city_solar.csv).

Usage: python scripts/04g_new_layers_figure.py  ->  figures/B_new_layers.png
"""
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import config as C
from common import load_samples
from style import apply_style, save, INK, MUTED, SEASON_COLORS, SEASON_LABELS

OUTLINE = C.RAW / 'ne_admin0'


def main():
    apply_style()
    cities = gpd.read_file(C.CITIES_FILE)
    s = load_samples()
    urban = s[(s.season == 'pre') & (s.built >= 0.10)]
    height = urban.groupby('uc_id').height.median()
    cities['height'] = cities.ID_UC_G0.map(height)
    solar = pd.read_csv(C.DATA / 'results' / 'city_solar.csv').pivot(
        index='uc_id', columns='season', values='ssrd_mj_m2_day')

    fig, (a, b) = plt.subplots(1, 2, figsize=(13, 6.2), layout='constrained',
                               gridspec_kw={'width_ratios': [1, 1.05]})

    shp = next(OUTLINE.glob('*.shp'), None) if OUTLINE.exists() else None
    if shp:
        w = gpd.read_file(shp)
        w[w.ADMIN == 'India'].boundary.plot(ax=a, color=MUTED, linewidth=0.6)
    c = cities.dropna(subset=['height']).sort_values('height')
    sc = a.scatter(c.lon, c.lat, c=c.height, cmap='viridis', s=28, edgecolor='white', linewidth=0.4, zorder=3)
    cb = fig.colorbar(sc, ax=a, shrink=0.7, pad=0.01)
    cb.set_label('Median urban building height (m)')
    cb.outline.set_visible(False)
    for name in ('Mumbai', 'New Delhi', 'Jodhpur', 'Kochi'):
        r = cities[cities.name == name].iloc[0]
        a.annotate(f"{name} {r.height:.1f} m", (r.lon, r.lat), xytext=(6, 4),
                   textcoords='offset points', fontsize=9, color=INK,
                   bbox=dict(boxstyle='round,pad=0.15', fc='white', ec='none', alpha=0.8))
    a.set_aspect(1 / np.cos(np.radians(22)))
    a.set_xlabel('Longitude (°E)')
    a.set_ylabel('Latitude (°N)')
    a.grid(False)
    a.set_title(f'Building height: {len(c)} cities, GHSL 2018 (built-surface weighted)', loc='left')

    lo, hi = 9, 27.5
    b.plot([lo, hi], [lo, hi], color=MUTED, linewidth=1, linestyle='--', zorder=1)
    b.text(hi - 0.3, hi - 1.2, 'same sun as\npre-monsoon', ha='right', color=MUTED, fontsize=9)
    for season in ('post', 'winter'):
        b.scatter(solar.pre, solar[season], s=18, color=SEASON_COLORS[season],
                  label=SEASON_LABELS[season], alpha=0.85, edgecolor='white', linewidth=0.3, zorder=3)
    for uid, name in ((5315, 'Jodhpur'), (9386, 'Kochi')):
        b.annotate(name, (solar.loc[uid, 'pre'], solar.loc[uid, 'winter']), xytext=(6, -2),
                   textcoords='offset points', fontsize=9, color=INK,
                   bbox=dict(boxstyle='round,pad=0.15', fc='white', ec='none', alpha=0.8))
    b.set_xlim(lo, hi)
    b.set_ylim(lo, hi)
    b.set_aspect('equal')
    b.set_xlabel('Pre-monsoon (Apr–May) solar radiation (MJ/m² per day)')
    b.set_ylabel('Same city, other season (MJ/m² per day)')
    b.legend(loc='upper left')
    b.set_title('Solar radiation: 303 cities, ERA5-Land 2019–2024', loc='left')

    out = save(fig, 'B_new_layers')
    print(f'{len(c)} cities with height, {len(solar)} with solar -> {out.relative_to(C.ROOT)}')


if __name__ == '__main__':
    main()
