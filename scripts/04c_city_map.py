"""Figure B: the 303 study cities, sized by population.

Points are coloured by annual rainfall once Role 2's
data/results/city_climate.csv exists; until then they are one colour.
If an India outline exists at raw/ne_admin0/ (Natural Earth admin-0), it is drawn.

Usage: python scripts/04c_city_map.py  ->  figures/B_city_map.png
"""
import math

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd

import config as C

OUT = C.ROOT / 'figures' / 'B_city_map.png'
CLIMATE = C.DATA / 'results' / 'city_climate.csv'
OUTLINE = C.RAW / 'ne_admin0'
LABEL = ['New Delhi', 'Kolkata', 'Mumbai', 'Bengaluru', 'Chennai', 'Hyderabad',
         'Ahmedabad', 'Jodhpur', 'Kochi', 'Guwahati']
INK, MUTED, GRID = '#1f2328', '#6b7280', '#e5e7eb'


def main():
    cities = gpd.read_file(C.CITIES_FILE)
    size = 6 + 260 * (cities.pop_2025 / cities.pop_2025.max()) ** 0.5  # area ~ population

    fig, ax = plt.subplots(figsize=(7, 8))
    shp = next(OUTLINE.glob('*.shp'), None) if OUTLINE.exists() else None
    if shp:
        world = gpd.read_file(shp)
        world[world.ADMIN == 'India'].boundary.plot(ax=ax, color=MUTED, linewidth=0.6)

    if CLIMATE.exists():
        rain = (pd.read_csv(CLIMATE).groupby('uc_id').rain_annual_mm.first())
        colour = cities.ID_UC_G0.map(rain)
        sc = ax.scatter(cities.lon, cities.lat, s=size, c=colour, cmap='YlGnBu',
                        edgecolor='white', linewidth=0.6, alpha=0.9, zorder=3)
        cb = fig.colorbar(sc, ax=ax, shrink=0.5, pad=0.02)
        cb.set_label('Annual rainfall, 2019–2024 mean (mm/yr)', color=INK)
        cb.outline.set_visible(False)
    else:
        ax.scatter(cities.lon, cities.lat, s=size, color='#2a78b5', edgecolor='white',
                   linewidth=0.6, alpha=0.85, zorder=3)

    left = {'Bengaluru', 'Kochi'}  # label left of the dot to avoid neighbours
    for _, r in cities[cities.name.isin(LABEL)].iterrows():
        ax.annotate(r['name'], (r.lon, r.lat), xytext=(-8 if r['name'] in left else 6, 3),
                    textcoords='offset points', ha='right' if r['name'] in left else 'left',
                    fontsize=8, color=INK, zorder=4)

    # Size key
    for pop in (1e6, 5e6, 2e7):
        ax.scatter([], [], s=6 + 260 * (pop / cities.pop_2025.max()) ** 0.5, color='#2a78b5',
                   edgecolor='white', label=f'{pop / 1e6:g} million')
    ax.legend(title='Population (2025)', loc='upper right', frameon=False,
              labelcolor=INK, title_fontsize=9, fontsize=8, labelspacing=1.2)

    ax.set_aspect(1 / math.cos(math.radians(22)))  # degrees roughly to scale at India's mid-latitude
    ax.set_xlabel('Longitude (°E)', color=MUTED)
    ax.set_ylabel('Latitude (°N)', color=MUTED)
    ax.set_title(f'{len(cities)} study cities: GHS urban centres with ≥ 300,000 people',
                 color=INK, fontsize=11, loc='left')
    ax.grid(color=GRID, linewidth=0.6, zorder=0)
    ax.tick_params(colors=MUTED, labelsize=8)
    for side in ax.spines.values():
        side.set_visible(False)

    OUT.parent.mkdir(exist_ok=True)
    fig.savefig(OUT, dpi=200, bbox_inches='tight', facecolor='white')
    print(f'{len(cities)} cities -> {OUT.relative_to(C.ROOT)}'
          + (' (coloured by rainfall)' if CLIMATE.exists() else ' (rainfall colour added once city_climate.csv exists)')
          + (' with India outline' if shp else ''))


if __name__ == '__main__':
    main()
