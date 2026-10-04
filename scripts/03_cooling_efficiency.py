"""Stage 2: cooling efficiency (CE) per city x season.

Per city and season, fit   lst ~ vi + controls   over its urban 1 km squares. The vi
coefficient is CE, in C per unit of vegetation index: negative = greener
squares are cooler, other things equal.

Fits every combination of:
  season     pre (Apr-May) / post (Oct-Nov) / winter (Dec-Feb)
  time       day / night (night only where a square has >= MIN_NIGHTS clear nights)
  index      ndvi / evi (EVI does not saturate over dense canopy)
  built_min  0.10 / 0.20 (what counts as an urban square)
  control    none / built / built_elev / built_elev_water (see CONTROLS;
             built_elev_water only when data/water/ has a file for the city)

Standard errors are clustered on ~5 km blocks: neighbouring squares are not
independent, and plain OLS would overstate certainty.

Main specification (use common.main_spec): ndvi, built_min 0.10, and
built_elev_water where it exists, otherwise built_elev.

Usage: python scripts/03_cooling_efficiency.py [uc_id or city ...]   (default: all sampled)
Output: data/results/cooling_efficiency.csv, data/results/dropped_cities.csv
"""
import json
import sys
import time as _time

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

import config as C
from common import SEASONS, main_spec, sample_paths, WATER_DIR

BUILT_MIN = (0.10, 0.20)
MIN_NIGHTS = 10
MIN_SQUARES = 30
BLOCK_DEG = 0.045  # ~5 km
CONTROLS = {'none': '', 'built': ' + built', 'built_elev': ' + built + elev',
            'built_elev_water': ' + built + elev + water_frac'}
COLS = ['city', 'uc_id', 'season', 'time', 'index', 'built_min', 'control', 'n', 'ce', 'se',
        'ci_lo', 'ci_hi', 'p', 'r2', 'n_blocks', 'vi_sd', 'built_coef', 'ce_per_0.1']
OUT = C.DATA / 'results' / 'cooling_efficiency.csv'
DROPPED = C.DATA / 'results' / 'dropped_cities.csv'


def fit(df, time, index, built_min, control, min_nights=MIN_NIGHTS):
    lst = f'lst_{time}'
    rhs = CONTROLS[control]
    vars_ = [lst, index] + [v.strip() for v in rhs.split('+') if v.strip()]
    d = df[df.built >= built_min].dropna(subset=vars_)
    if time == 'night':
        d = d[d.n_night >= min_nights]
    row = dict(time=time, index=index, built_min=built_min, control=control, n=len(d))
    if len(d) < MIN_SQUARES:
        return row

    blocks = (np.floor(d.lon / BLOCK_DEG).astype(int).astype(str) + '_'
              + np.floor(d.lat / BLOCK_DEG).astype(int).astype(str))
    formula = f'{lst} ~ {index}' + rhs
    m = smf.ols(formula, data=d).fit(cov_type='cluster',
                                     cov_kwds={'groups': pd.factorize(blocks)[0]})
    lo, hi = m.conf_int().loc[index]
    row.update(ce=m.params[index], se=m.bse[index], ci_lo=lo, ci_hi=hi,
               p=m.pvalues[index], r2=m.rsquared, n_blocks=blocks.nunique(),
               vi_sd=d[index].std(), built_coef=m.params.get('built', np.nan))
    return row


def load_city(path):
    """One city's samples, with water_frac joined if data/water/ has the same file name."""
    df = pd.read_csv(path)
    wpath = WATER_DIR / path.name
    has_water = wpath.exists()
    if has_water:
        w = pd.read_csv(wpath)[['cell_id', 'water_frac']]
        df = df.merge(w, on='cell_id', how='left')
    else:
        df['water_frac'] = np.nan
    return df, has_water


def city_results(path, min_nights=MIN_NIGHTS):
    df, has_water = load_city(path)
    controls = [c for c in CONTROLS if c != 'built_elev_water' or has_water]
    rows = []
    for s in SEASONS:
        ds = df[df.season == s]
        for t in ('day', 'night'):
            for i in ('ndvi', 'evi'):
                for b in BUILT_MIN:
                    for c in controls:
                        r = fit(ds, t, i, b, c, min_nights)
                        r['season'] = s
                        rows.append(r)
    out = pd.DataFrame(rows)
    out['city'] = df.city.iloc[0]
    out['uc_id'] = df.uc_id.iloc[0]
    return out


def dropped_list(res, paths):
    """City x season x time with no main-spec estimate, with the reason."""
    ms = main_spec(res)
    rows = []
    for _, r in ms[ms.ce.isna()].iterrows():
        if r.time == 'day':
            reason = 'fewer than 30 urban squares'
        else:
            day_n = ms[(ms.uc_id == r.uc_id) & (ms.season == r.season) & (ms.time == 'day')].n
            urban = int(day_n.iloc[0]) if len(day_n) else 0
            reason = ('fewer than 30 urban squares' if urban < MIN_SQUARES
                      else 'fewer than 30 squares with clear nights')
        rows.append(dict(uc_id=r.uc_id, city=r.city, season=r.season, time=r.time,
                         n=r.n, reason=reason))
    # cities in the geojson with no sample file
    sampled = {int(p.stem.split('_', 1)[0]) for p in paths}
    with open(C.CITIES_FILE) as f:
        feats = json.load(f)['features']
    for ft in feats:
        uc, name = ft['properties']['ID_UC_G0'], ft['properties']['name']
        if uc not in sampled:
            rows += [dict(uc_id=uc, city=name, season=s, time=t, n=0, reason='no sample file')
                     for s in SEASONS for t in ('day', 'night')]
    return pd.DataFrame(rows, columns=['uc_id', 'city', 'season', 'time', 'n', 'reason'])


def run(paths, min_nights=MIN_NIGHTS, verbose=True):
    parts, t0 = [], _time.time()
    for k, p in enumerate(paths, 1):
        parts.append(city_results(p, min_nights))
        if verbose and (k % 25 == 0 or k == len(paths)):
            print(f'  {k}/{len(paths)} cities ({_time.time() - t0:.0f} s)')
    res = pd.concat(parts, ignore_index=True)
    res['ce_per_0.1'] = res.ce / 10
    return res[COLS]


def main(names):
    paths = sample_paths(names)
    res = run(paths)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    res.to_csv(OUT, index=False)
    drop = dropped_list(res, sample_paths())   # 'no sample file' = not on disk at all
    drop.to_csv(DROPPED, index=False)
    ms = main_spec(res)
    print(f'{len(paths)} cities, {len(res)} fits -> {OUT.relative_to(C.ROOT)}')
    print(f'main spec: {ms.ce.notna().sum()} estimates; {len(drop)} city x season x time '
          f'dropped -> {DROPPED.relative_to(C.ROOT)}')


if __name__ == '__main__':
    main(sys.argv[1:])
