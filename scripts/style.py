"""Shared figure style, so every chart in the deck looks like one set.

Usage:
    from style import apply_style, save, SEASON_COLORS, SEASON_LABELS, DIVERGING, CE_LABEL
    apply_style()
    fig, ax = plt.subplots()
    ...
    save(fig, 'F_exposure_gap_hist')   # -> figures/F_exposure_gap_hist.png
"""
from pathlib import Path

import matplotlib as mpl

SEASONS = ['pre', 'post', 'winter']
SEASON_COLORS = {'pre': '#E07B00', 'post': '#1B9E77', 'winter': '#7570B3'}   # orange, blue-green, purple
SEASON_LABELS = {'pre': 'Pre-monsoon (Apr–May)', 'post': 'Post-monsoon (Oct–Nov)',
                 'winter': 'Winter (Dec–Feb)'}

# Cooling-slope maps: negative (greener is cooler) = blue, positive = red. Centre on 0.
DIVERGING = 'RdBu_r'
SEQUENTIAL = 'viridis'
CE_LABEL = 'Cooling slope (°C per 0.1 NDVI); negative = greener is cooler'

# Rainfall groups, split at 1000 mm/yr (Guo 2026; Manoli 2019).
DRY_MM = 1000
DRY_COLOR, WET_COLOR = '#B8860B', '#1F78B4'

INK, MUTED = '#1f2328', '#6b7280'


def apply_style():
    mpl.rcParams.update({'figure.dpi': 110, 'savefig.dpi': 200, 'savefig.bbox': 'tight',
                         'font.size': 11, 'axes.titlesize': 12, 'axes.labelsize': 11,
                         'axes.spines.top': False, 'axes.spines.right': False,
                         'axes.grid': True, 'grid.alpha': 0.25, 'legend.frameon': False,
                         'text.color': INK, 'axes.labelcolor': INK,
                         'xtick.color': INK, 'ytick.color': INK})


def save(fig, name):
    """Save to figures/{name}.png at 200 dpi and return the path."""
    out = Path(__file__).resolve().parents[1] / 'figures' / f'{name}.png'
    out.parent.mkdir(exist_ok=True)
    fig.savefig(out)
    return out
