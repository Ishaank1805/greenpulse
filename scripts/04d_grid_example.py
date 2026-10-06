"""Figure B: one city as the analysis sees it, a grid of 1 km MODIS squares.

Draws Jodhpur's sampled squares as their true MODIS sinusoidal cells inside the
city outline, coloured by pre-monsoon daytime surface temperature and by NDVI.

Usage: python scripts/04d_grid_example.py  ->  figures/B_grid_example.png
"""
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.collections import PolyCollection
from pyproj import Transformer

import config as C
from style import apply_style, save, INK, MUTED

UC_ID, NAME = 5315, 'jodhpur'
SIN = '+proj=sinu +R=6371007.181 +nadgrids=@null +wktext +units=m'
HALF = 926.625433055833 / 2   # half a MODIS 1 km cell, in metres
to_sin = Transformer.from_crs('EPSG:4326', SIN, always_xy=True)
to_ll = Transformer.from_crs(SIN, 'EPSG:4326', always_xy=True)


def cell_polygons(lons, lats):
    """The four corners of each square's MODIS cell, back in lon/lat."""
    xs, ys = to_sin.transform(lons, lats)
    polys = []
    for x, y in zip(xs, ys):
        cx = [x - HALF, x + HALF, x + HALF, x - HALF]
        cy = [y - HALF, y - HALF, y + HALF, y + HALF]
        polys.append(list(zip(*to_ll.transform(cx, cy))))
    return polys


def main():
    apply_style()
    df = pd.read_csv(C.SAMPLES_DIR / f'{UC_ID}_{NAME}.csv')
    pre = df[df.season == 'pre']
    outline = gpd.read_file(C.CITIES_FILE)
    outline = outline[outline.ID_UC_G0 == UC_ID]
    polys = cell_polygons(pre.lon.values, pre.lat.values)

    panels = [('lst_day', 'Daytime surface temperature (°C)', 'YlOrRd'),
              ('ndvi', 'Greenness (NDVI)', 'YlGn')]
    fig, axes = plt.subplots(1, 2, figsize=(11, 5.2), layout='constrained')
    for ax, (col, label, cmap) in zip(axes, panels):
        pc = PolyCollection(polys, array=pre[col].values, cmap=cmap,
                            edgecolors='white', linewidths=0.4)
        ax.add_collection(pc)
        outline.boundary.plot(ax=ax, color=INK, linewidth=1.2)
        ax.autoscale_view()
        ax.set_aspect('equal')
        ax.set_title(label, loc='left', color=INK)
        ax.set_xlabel('Longitude (°E)', color=MUTED)
        ax.set_ylabel('')
        ax.grid(False)
        cb = fig.colorbar(pc, ax=ax, shrink=0.85, pad=0.02)
        cb.outline.set_visible(False)
    axes[0].set_ylabel('Latitude (°N)', color=MUTED)
    fig.suptitle(f'Jodhpur, pre-monsoon (Apr–May) 2019–2024: {len(pre)} squares of 1 km '
                 '(MODIS grid) inside the city outline', x=0.01, ha='left', color=INK)
    out = save(fig, 'B_grid_example')
    print(f'{len(pre)} squares -> {out.relative_to(C.ROOT)}')


if __name__ == '__main__':
    main()
