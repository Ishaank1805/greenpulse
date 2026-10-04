"""Shared helpers for the analysis scripts (owner: Role 3). R2 and R4 import from here.

Sign convention, everywhere: ce / ce_per_0.1 < 0 means GREENER SQUARES ARE COOLER.
ce is in degC per 1.0 NDVI (or EVI); ce_per_0.1 = ce / 10.

Main specification (README section 3.3): index = ndvi, built_min = 0.10, and the first
control in CONTROL_PRIORITY that is present for that city x season x time.
"""
import pandas as pd

import config as C

MAIN_INDEX = 'ndvi'
MAIN_BUILT_MIN = 0.10
CONTROL_PRIORITY = ['built_elev_water', 'built_elev', 'built']   # first one present wins
SEASONS = ['pre', 'post', 'winter']
DRY_MM = 1000   # Guo 2026 / Manoli 2019 threshold

WATER_DIR = C.DATA / 'water'
RESULTS = C.DATA / 'results'


def sample_paths(names=None):
    """Sample files in data/samples/ (never _pilot_v1/). names: uc_ids or city names."""
    paths = sorted(C.SAMPLES_DIR.glob('*.csv'))
    if not names:
        return paths
    out = []
    for n in names:
        n = str(n).strip()
        slug = n.lower().replace(' ', '_')
        hit = [p for p in paths if p.stem.split('_', 1)[0] == n or p.stem.split('_', 1)[1] == slug]
        if not hit:
            raise FileNotFoundError(f'No sample file for {n!r} in {C.SAMPLES_DIR}')
        out += hit
    return out


def load_samples(pattern='*.csv'):
    """All data/samples/{pattern} files (not _pilot_v1/), concatenated."""
    paths = sorted(C.SAMPLES_DIR.glob(pattern))
    return pd.concat([pd.read_csv(p) for p in paths], ignore_index=True)


def load_water():
    """All data/water/*.csv (uc_id, cell_id, water_frac), or an empty DataFrame."""
    paths = sorted(WATER_DIR.glob('*.csv')) if WATER_DIR.exists() else []
    if not paths:
        return pd.DataFrame(columns=['uc_id', 'cell_id', 'water_frac'])
    return pd.concat([pd.read_csv(p) for p in paths], ignore_index=True)


def main_spec(ce):
    """Rows of cooling_efficiency.csv for the main specification.

    Filters to MAIN_INDEX and MAIN_BUILT_MIN, then per (uc_id, season, time) keeps the
    row whose control comes first in CONTROL_PRIORITY among the rows present. A row
    counts as present even if its ce is NaN; callers drop NaN afterwards.
    The old pilot file has no season column and is treated as season = 'pre'.
    Negative ce = greener squares are cooler.
    """
    d = ce.copy()
    if 'season' not in d.columns:
        d['season'] = 'pre'
    d = d[(d['index'] == MAIN_INDEX) & ((d['built_min'] - MAIN_BUILT_MIN).abs() < 1e-9)]
    d = d[d['control'].isin(CONTROL_PRIORITY)]
    rank = {c: i for i, c in enumerate(CONTROL_PRIORITY)}
    d = d.assign(_rank=d['control'].map(rank)).sort_values('_rank')
    d = d.drop_duplicates(['uc_id', 'season', 'time'], keep='first')
    return d.drop(columns='_rank').sort_values(['uc_id', 'season', 'time']).reset_index(drop=True)


def load_climate():
    """data/results/city_climate.csv (Role 2), or None if it does not exist yet."""
    p = RESULTS / 'city_climate.csv'
    return pd.read_csv(p) if p.exists() else None


def rain_group(mm):
    """'< 1000 mm' / '>= 1000 mm' (DRY_MM)."""
    return pd.Series(mm).map(lambda x: None if pd.isna(x) else
                             (f'< {DRY_MM} mm' if x < DRY_MM else f'≥ {DRY_MM} mm')).values
