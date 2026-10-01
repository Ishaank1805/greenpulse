"""B2 checks: one row per city in data/results/b2_checks.csv.

Checks (role_1_pipeline.md section 3e, plus internal consistency):
  - every city has a sample file or a logged failure
  - rows = 3 x squares; squares within +-20% of area / MODIS cell area
  - value ranges (counts of out-of-range values)
  - LST is missing exactly when its clear-image count is 0, and counts never
    exceed the number of images in the season
  - share of squares with no daytime LST, per season (flag > 50%)
  - spot checks of well-known cities against common knowledge

Usage: python scripts/04b_check_samples.py
"""
import json

import pandas as pd

import config as C
import importlib

sampler = importlib.import_module('02_sample_city')

CELL_KM2 = 0.926625 ** 2  # MODIS sinusoidal 1 km cell, 0.8586 km2
# Images per season, 2019-2024, counted in Earth Engine (2022 lacks one Apr-May image).
MAX_IMAGES = {'pre': 41, 'post': 42, 'winter': 72}
RANGES = {'lst_day': (5, 65), 'lst_night': (-5, 40), 'ndvi': (-0.3, 1),
          'built': (0, 1), 'pop': (0, None), 'elev': (-10, 3000)}
MISSING_FLAG = 0.5
# Flags that were investigated and found to be real, not errors.
EXPLAINED = {
    1991: 'Kashmir valley, ~1,590 m: winter nights below -5 C are real',
    1639: 'Kashmir valley, ~2,040 m: cold winter days and nights are real',
    164: 'Kashmir valley, ~1,720 m: winter nights below -5 C are real',
    10462: 'thin jagged outline catches extra cell centres; an independent '
           'sinusoidal-grid count also gives 65',
}
OUT = C.DATA / 'results' / 'b2_checks.csv'


def out_of_range(df):
    n = 0
    for col, (lo, hi) in RANGES.items():
        v = df[col].dropna()
        if lo is not None:
            n += int((v < lo).sum())
        if hi is not None:
            n += int((v > hi).sum())
    return n


def consistent(df):
    """LST NaN <=> count 0, and 0 <= count <= images in the season."""
    for lst, n in (('lst_day', 'n_day'), ('lst_night', 'n_night')):
        if not (df[lst].isna() == (df[n] == 0)).all():
            return False
        cap = df.season.map(MAX_IMAGES)
        if ((df[n] < 0) | (df[n] > cap)).any():
            return False
    return True


def check_city(feature, log):
    p = feature['properties']
    row = {'uc_id': p['ID_UC_G0'], 'city': p['name'], 'area_km2': round(p['area_km2'], 1),
           'expected_squares': round(p['area_km2'] / CELL_KM2)}
    path = sampler.output_path(feature)
    if not path.exists():
        last = log[log.uc_id == p['ID_UC_G0']].tail(1)
        row['status'] = 'failed' if len(last) else 'missing'
        row['flags'] = (last.error.iloc[0] if len(last) else 'no file and no log entry')
        return row

    df = pd.read_csv(path)
    n_sq = df.cell_id.nunique()
    ratio = n_sq / row['expected_squares']
    flags = []
    if len(df) != 3 * n_sq or not df.groupby('season').cell_id.nunique().eq(n_sq).all():
        flags.append('rows != 3 x squares')
    if not 0.8 <= ratio <= 1.2:
        flags.append(f'squares {ratio:.2f} x expected')
    n_bad = out_of_range(df)
    if n_bad:
        flags.append(f'{n_bad} values out of range')
    ok = consistent(df)
    if not ok:
        flags.append('count/NaN inconsistency')
    missing = df.groupby('season').lst_day.apply(lambda s: s.isna().mean())
    for season, share in missing.items():
        if share > MISSING_FLAG:
            flags.append(f'{season} {share:.0%} missing')

    # Cloud shows up as fewer clear images, not as empty squares (one clear
    # image in six years is enough for a value), so report the clear share too.
    land = df[df.n_day > 0]
    clear = (land.n_day / land.season.map(MAX_IMAGES)).groupby(land.season).median()
    row.update(status='ok', n_squares=n_sq, squares_ratio=round(ratio, 3), n_rows=len(df),
               n_out_of_range=n_bad, consistent=ok,
               **{f'missing_{s}': round(missing.get(s, float('nan')), 3) for s in MAX_IMAGES},
               **{f'clear_day_{s}': round(clear.get(s, float('nan')), 3) for s in MAX_IMAGES},
               flags='; '.join(flags), explained=EXPLAINED.get(p['ID_UC_G0'], ''))
    return row


def spot_checks():
    def median(name, col, season='pre'):
        df = pd.read_csv(sampler.output_path(sampler.load_city(name)))
        return df.loc[df.season == season, col].median()

    print('\nSpot checks (pre-monsoon medians):')
    try:
        d = median('New Delhi', 'lst_day')
        print(f'  New Delhi day LST {d:.1f} C, expected 40-48: {"PASS" if 40 <= d <= 48 else "FAIL"}')
        b, h = median('Bengaluru', 'lst_day'), median('Hyderabad', 'lst_day')
        print(f'  Bengaluru {b:.1f} C < Hyderabad {h:.1f} C: {"PASS" if b < h else "FAIL"}')
        k, j = median('Kolkata', 'ndvi'), median('Jaipur', 'ndvi')
        print(f'  Kolkata NDVI {k:.3f} > Jaipur {j:.3f}: {"PASS" if k > j else "FAIL"}')
    except (FileNotFoundError, SystemExit) as e:
        print(f'  skipped, a city is not sampled yet: {e}')


def main():
    with open(C.CITIES_FILE) as f:
        features = json.load(f)['features']
    log = (pd.read_csv(C.DATA / 'results' / 'run_log.csv')
           if (C.DATA / 'results' / 'run_log.csv').exists() else pd.DataFrame(columns=['uc_id', 'error']))
    res = pd.DataFrame([check_city(ft, log) for ft in features])
    res.to_csv(OUT, index=False)

    ok = res[res.status == 'ok']
    print(f'{len(res)} cities: {len(ok)} sampled, {(res.status == "failed").sum()} failed, '
          f'{(res.status == "missing").sum()} not yet run -> {OUT.relative_to(C.ROOT)}')
    print(f'Cities with any flag: {(ok['flags'] != "").sum()}')
    print(f'Square count vs expected: median ratio {ok.squares_ratio.median():.3f}, '
          f'range {ok.squares_ratio.min():.3f}-{ok.squares_ratio.max():.3f}')
    print(f'Out-of-range values (all cities): {int(ok.n_out_of_range.sum())} | '
          f'inconsistent cities: {(~ok.consistent.astype(bool)).sum()}')
    for s in MAX_IMAGES:
        col = ok[f'missing_{s}']
        print(f'Missing day LST, {s:<6}: median {col.median():.1%}, worst: '
              + ', '.join(f'{city} {share:.0%}' for city, share in
                          ok.nlargest(3, f'missing_{s}')[['city', f'missing_{s}']].values))
    for s in MAX_IMAGES:
        col = ok[f'clear_day_{s}']
        print(f'Clear-sky share of daytime images, {s:<6}: median city {col.median():.0%}, cloudiest: '
              + ', '.join(f'{city} {share:.0%}' for city, share in
                          ok.nsmallest(3, f'clear_day_{s}')[['city', f'clear_day_{s}']].values))
    flagged = ok[ok['flags'] != '']
    if len(flagged):
        print('\nFlagged cities:')
        print(flagged[['uc_id', 'city', 'flags', 'explained']].to_string(index=False))
        unexplained = flagged[flagged.explained == '']
        print(f'Unexplained flags: {len(unexplained)}')
    spot_checks()


if __name__ == '__main__':
    main()
