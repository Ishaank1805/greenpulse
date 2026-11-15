"""Role 5 utilities. All computations use existing, local GreenPulse CSVs."""
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
import config as C
from common import main_spec

RES = C.DATA / 'results'


def read_csv(name, required):
    path = RES / name
    if not path.exists():
        raise FileNotFoundError(f'{path} missing. Ask the owner to generate it; do not invent inputs.')
    d = pd.read_csv(path)
    missing = set(required) - set(d.columns)
    if missing:
        raise ValueError(f'{name} lacks required columns: {sorted(missing)}')
    return d


def main_cooling():
    d = read_csv('cooling_efficiency.csv', ['uc_id','season','time','index','built_min','control','ce','se','n_blocks'])
    return main_spec(d).dropna(subset=['ce']).copy()


def water_intensity():
    """Static OSM water over all pre-monsoon urban squares (built >= 0.10).

    A missing water mapping for an urban cell is a data error, *not* zero water.
    Each city is streamed separately to keep memory low.
    """
    rows = []
    for sample in sorted(C.SAMPLES_DIR.glob('*.csv')):
        s = pd.read_csv(sample, usecols=['uc_id', 'season', 'cell_id', 'built'])
        s = s[(s.season == 'pre') & (s.built >= 0.10)]
        if s.empty:
            continue
        uc_id = int(s.uc_id.iloc[0])
        if s.cell_id.duplicated().any():
            raise ValueError(f'Duplicate pre-monsoon cell_id in {sample.name}')
        water_file = C.DATA / 'water' / sample.name
        if not water_file.exists():
            raise FileNotFoundError(f'Missing {water_file}; cannot treat missing OSM mapping as dry.')
        w = pd.read_csv(water_file, usecols=['uc_id', 'cell_id', 'water_frac'])
        if w.duplicated(['uc_id','cell_id']).any():
            raise ValueError(f'Duplicate water cell IDs in {water_file.name}')
        merged = s.merge(w, on=['uc_id','cell_id'], how='left', validate='one_to_one')
        if merged.water_frac.isna().any():
            raise ValueError(f'{water_file.name}: {merged.water_frac.isna().sum()} urban cells unmatched')
        if not merged.water_frac.between(0,1).all():
            raise ValueError(f'{water_file.name}: water_frac outside 0..1')
        v = merged.water_frac
        rows.append(dict(uc_id=uc_id, n_urban=int(len(s)), water_median=float(v.median()),
                         water_mean=float(v.mean()), water_p90=float(v.quantile(0.90)),
                         water_share_ge_5pct=float((v >= 0.05).mean())))
    d = pd.DataFrame(rows)
    if d.uc_id.duplicated().any():
        raise ValueError('Duplicate city IDs in aggregated water intensity')
    return d


def spearman(x, y):
    good = pd.DataFrame({'x':x, 'y':y}).replace([np.inf,-np.inf], np.nan).dropna()
    if len(good) < 4 or good.x.nunique() < 2 or good.y.nunique() < 2:
        return len(good), np.nan, np.nan
    rho,p = stats.spearmanr(good.x,good.y)
    return len(good),float(rho),float(p)


def median_ci(a, seed=2026, boots=3000):
    """IID city bootstrap for a descriptive CI on a median (not a causal CI)."""
    a = np.asarray(a, dtype=float)
    a = a[np.isfinite(a)]
    if len(a) == 0: return (np.nan,np.nan,np.nan)
    rng = np.random.default_rng(seed)
    med = np.median(a)
    sims = np.median(a[rng.integers(0, len(a), size=(boots,len(a)))], axis=1)
    lo,hi = np.percentile(sims,[2.5,97.5])
    return float(med),float(lo),float(hi)
