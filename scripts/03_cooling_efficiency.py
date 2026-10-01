"""Stage 2: cooling efficiency (CE) per city.

Per city, fit   lst ~ vi + built   over its urban 1 km squares. The vi
coefficient is CE, in C per unit of vegetation index: negative = greener
squares are cooler at equal built-up share.

Fits every combination of:
  time       day / night (night only where a square has >= MIN_NIGHTS clear nights)
  index      ndvi / evi (EVI does not saturate over dense canopy)
  built_min  0.10 / 0.20 (what counts as an urban square)
  control    with built (the main result) / without (to show why it matters)

Standard errors are clustered on ~5 km blocks: neighbouring squares are not
independent, and plain OLS would overstate certainty.

Usage: python scripts/03_cooling_efficiency.py [city ...]   (default: all sampled)
Output: data/results/cooling_efficiency.csv
"""
import sys

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

import config as C

BUILT_MIN = (0.10, 0.20)
MIN_NIGHTS = 10
MIN_SQUARES = 30
BLOCK_DEG = 0.045  # ~5 km


def fit(df, time, index, built_min, control):
    lst = f'lst_{time}'
    d = df[df.built >= built_min].dropna(subset=[lst, index, 'built'])
    if time == 'night':
        d = d[d.n_night >= MIN_NIGHTS]
    row = dict(time=time, index=index, built_min=built_min,
               control='built' if control else 'none', n=len(d))
    if len(d) < MIN_SQUARES:
        return row

    blocks = (np.floor(d.lon / BLOCK_DEG).astype(int).astype(str) + '_'
              + np.floor(d.lat / BLOCK_DEG).astype(int).astype(str))
    formula = f'{lst} ~ {index}' + (' + built' if control else '')
    m = smf.ols(formula, data=d).fit(cov_type='cluster',
                                     cov_kwds={'groups': pd.factorize(blocks)[0]})
    lo, hi = m.conf_int().loc[index]
    row.update(ce=m.params[index], se=m.bse[index], ci_lo=lo, ci_hi=hi,
               p=m.pvalues[index], r2=m.rsquared, n_blocks=blocks.nunique(),
               vi_sd=d[index].std(), built_coef=m.params.get('built', np.nan))
    return row


def city_results(path):
    df = pd.read_csv(path)
    rows = [fit(df, t, i, b, c)
            for t in ('day', 'night') for i in ('ndvi', 'evi')
            for b in BUILT_MIN for c in (True, False)]
    out = pd.DataFrame(rows)
    out.insert(0, 'city', df.city.iloc[0])
    out.insert(1, 'uc_id', df.uc_id.iloc[0])
    return out


def main(names):
    paths = ([C.SAMPLES_DIR / f'{n.lower()}.csv' for n in names] if names
             else sorted(C.SAMPLES_DIR.glob('*.csv')))
    res = pd.concat([city_results(p) for p in paths], ignore_index=True)
    res['ce_per_0.1'] = res.ce / 10

    out = C.DATA / 'results' / 'cooling_efficiency.csv'
    out.parent.mkdir(parents=True, exist_ok=True)
    res.to_csv(out, index=False)
    print(f'{len(paths)} cities -> {out.relative_to(C.ROOT)}')


if __name__ == '__main__':
    main(sys.argv[1:])
