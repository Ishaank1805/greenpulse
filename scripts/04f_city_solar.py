"""Final phase, task 5 (gate G-S): mean daily solar radiation per city and season.

ERA5-Land monthly (C.ERA5_ID), band surface_solar_radiation_downwards_sum, 2019-2024.
The monthly _sum band is J/m2 accumulated over the month, so each month is divided
by 1e6 and by its number of days (MJ/m2 per day), then averaged over the season's
months and years (C.SEASONS). --crosscheck confirms the unit against the daily
collection for one month.

City reducer as in 07_city_climate.py (Role 2): reduceRegion(mean, city polygon,
scale = C.CLIMATE_SCALE), one getInfo per city (72 months). If the polygon returns
nulls, the city is redone on centroid().buffer(C.CLIMATE_FALLBACK_BUFFER).
Raw results are cached in cache/solar/{uc_id}.json (gitignored), so a rerun resumes.

Output: data/results/city_solar.csv  uc_id, city, season, ssrd_mj_m2_day   (909 rows)
A run on fewer than all 303 cities writes cache/solar/city_solar_test.csv instead.

Usage:
  python scripts/04f_city_solar.py Jodhpur Kochi   # test on two cities first
  python scripts/04f_city_solar.py --all           # all 303 (agree a time in chat first)
  python scripts/04f_city_solar.py --build-only    # rebuild the CSV from the cache
  python scripts/04f_city_solar.py --crosscheck    # monthly vs daily unit check (2 calls)
"""
import argparse
import calendar
import json
import time

import pandas as pd

import config as C

CACHE = C.ROOT / 'cache' / 'solar'
OUT = C.DATA / 'results' / 'city_solar.csv'
COLS = ['uc_id', 'city', 'season', 'ssrd_mj_m2_day']
PAUSE = 1
WAITS = (60, 60)   # seconds after the 1st and 2nd failed attempt


# --------------------------------------------------------------------------- Earth Engine
def fetch(ee, geom):
    """72 dicts {year, month, ssrd} (J/m2 over the month) for one geometry."""
    coll = ee.ImageCollection(C.ERA5_ID).filterDate(C.START, C.END).select(C.SSRD_BAND)
    fc = coll.map(lambda img: ee.Feature(None, img.reduceRegion(
        ee.Reducer.mean(), geom, C.CLIMATE_SCALE)).set(
        {'year': img.date().get('year'), 'month': img.date().get('month')}))
    return [{'year': f['properties']['year'], 'month': f['properties']['month'],
             'ssrd': f['properties'].get(C.SSRD_BAND)} for f in fc.getInfo()['features']]


def pull_city(ee, feature):
    props = feature['properties']
    path = CACHE / f"{props['ID_UC_G0']}.json"
    if path.exists():
        return 'cached'
    geom = ee.Geometry(feature['geometry'])
    for attempt in range(1, len(WAITS) + 2):
        try:
            monthly, fallback = fetch(ee, geom), False
            if any(m['ssrd'] is None for m in monthly):
                print(f"  fallback: {props['name']} -> centroid + "
                      f"{C.CLIMATE_FALLBACK_BUFFER / 1000:.0f} km")
                monthly = fetch(ee, geom.centroid(100).buffer(C.CLIMATE_FALLBACK_BUFFER))
                fallback = True
            tmp = path.with_suffix('.tmp')
            tmp.write_text(json.dumps({'uc_id': props['ID_UC_G0'], 'city': props['name'],
                                       'fallback': fallback, 'monthly': monthly}))
            tmp.replace(path)
            return 'fallback' if fallback else 'ok'
        except Exception as e:  # quota / concurrency / network
            print(f"  {props['name']} attempt {attempt}: {type(e).__name__}: {str(e)[:200]}")
            if attempt > len(WAITS):
                return 'failed'
            time.sleep(WAITS[attempt - 1])


def crosscheck(ee):
    """Jodhpur, May 2023: monthly sum / 31 should equal the mean of the daily sums."""
    with open(C.CITIES_FILE) as f:
        ft = next(x for x in json.load(f)['features'] if x['properties']['ID_UC_G0'] == 5315)
    geom = ee.Geometry(ft['geometry'])

    def reduce(img):
        return img.reduceRegion(ee.Reducer.mean(), geom, C.CLIMATE_SCALE).get(C.SSRD_BAND)

    mon = ee.ImageCollection(C.ERA5_ID).filterDate('2023-05-01', '2023-06-01').select(C.SSRD_BAND)
    day = ee.ImageCollection(C.ERA5_DAILY_ID).filterDate('2023-05-01', '2023-06-01').select(C.SSRD_BAND)
    m = ee.Number(reduce(mon.first())).getInfo()
    d = day.map(lambda img: ee.Feature(None, {'v': reduce(img)})).aggregate_mean('v').getInfo()
    a, b = m / 31 / 1e6, d / 1e6
    good = abs(a - b) <= 0.02 * b
    print(f'Crosscheck Jodhpur May 2023: monthly/31 = {a:.2f} MJ/m2/day, mean of daily sums = '
          f'{b:.2f}: {"ok" if good else "MISMATCH, check the unit"}')
    return good


# --------------------------------------------------------------------------- pandas
def city_rows(raw):
    m = pd.DataFrame(raw['monthly'])
    days = [calendar.monthrange(int(y), int(mo))[1] for y, mo in zip(m.year, m.month)]
    m['mj_day'] = m.ssrd / 1e6 / days
    rows = []
    for s, months in C.SEASONS.items():
        ms = m[m.month.isin(months)]
        rows.append(dict(uc_id=raw['uc_id'], city=raw['city'], season=s,
                         ssrd_mj_m2_day=ms.mj_day.mean(), _n_months=len(ms),
                         _fallback=raw.get('fallback', False)))
    return rows


def build(uc_ids):
    raws = [json.loads(p.read_text()) for p in sorted(CACHE.glob('*.json'))]
    return pd.DataFrame([r for raw in raws if raw['uc_id'] in uc_ids for r in city_rows(raw)])


# --------------------------------------------------------------------------- checks (G-S)
def checks(df, lat, full):
    print('\n=== Checks (role 1, final phase step 2) ===')
    ok = True
    p = df.pivot_table(index='uc_id', columns='season', values='ssrd_mj_m2_day')
    v = df.ssrd_mj_m2_day
    odd = df[(v < 5) | (v > 35)]
    print(f'  all values {v.min():.1f}-{v.max():.1f} MJ/m2/day; outside 5-35 (unit error?): {len(odd)}')
    ok &= odd.empty
    if 'pre' in p:
        share = p['pre'].between(15, 28).mean()
        print(f'  pre-monsoon 15-28 MJ/m2/day in {share:.0%} of cities (median {p["pre"].median():.1f})')
        ok &= share >= 0.8
    if {'pre', 'winter'} <= set(p.columns):
        north = p.index.map(lat) >= 23.5
        sh, shn = (p.pre > p.winter).mean(), (p.pre > p.winter)[north].mean()
        print(f'  pre > winter in {sh:.0%} of cities; {shn:.0%} of {int(north.sum())} cities north of 23.5 N')
        ok &= sh >= 0.8
    for name in ('Jodhpur', 'Kochi', 'New Delhi', 'Chennai', 'Shillong'):
        r = df[df.city == name].set_index('season').ssrd_mj_m2_day
        if len(r):
            print(f'  {name:9s} ' + '  '.join(f'{s} {r[s]:.1f}' for s in C.SEASONS))
    print(f'  months per season: {df.groupby("season")._n_months.unique().to_dict()}')
    n_nan = int(df[COLS].isna().sum().sum())
    exp = 303 * 3
    print(f'  rows {len(df)}{f" (expect {exp})" if full else ""}, NaNs {n_nan}')
    ok &= n_nan == 0 and (not full or len(df) == exp)
    fb = df[df._fallback].city.unique().tolist()
    print(f'  fallback cities ({len(fb)}): {fb}')
    print('G-S CHECKS PASSED' if ok and full else 'ALL CHECKS OK (test run)' if ok
          else 'SOME CHECKS NEED A LOOK (see above)')
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cities', nargs='*', help='names or uc_ids (default with --all: every city)')
    ap.add_argument('--all', action='store_true', help='all 303 cities')
    ap.add_argument('--build-only', action='store_true', help='rebuild the CSV from the cache')
    ap.add_argument('--crosscheck', action='store_true', help='monthly vs daily unit check')
    a = ap.parse_args()
    with open(C.CITIES_FILE) as f:
        feats = json.load(f)['features']
    if not a.all:
        keys = {str(k).lower() for k in (a.cities or ['Jodhpur', 'Kochi'])}
        feats = [ft for ft in feats if str(ft['properties']['ID_UC_G0']) in keys
                 or ft['properties']['name'].lower() in keys]
    CACHE.mkdir(parents=True, exist_ok=True)

    if a.crosscheck or not a.build_only:
        import ee
        ee.Initialize(project=C.PROJECT)
    if a.crosscheck:
        raise SystemExit(0 if crosscheck(ee) else 1)
    if not a.build_only:
        status = {}
        todo = sorted(feats, key=lambda f: -f['properties']['pop_2025'])
        for k, ft in enumerate(todo, 1):
            st = pull_city(ee, ft)
            status[st] = status.get(st, 0) + 1
            if st != 'cached':
                time.sleep(PAUSE)
            if k % 25 == 0 or k == len(todo):
                print(f'  {k}/{len(todo)} {status}', flush=True)

    ids = {ft['properties']['ID_UC_G0'] for ft in feats}
    df = build(ids)
    if df.empty:
        raise SystemExit('No cached cities to build from.')
    full = df.uc_id.nunique() == 303
    out = OUT if full else CACHE / 'city_solar_test.csv'
    df[COLS].sort_values(['uc_id', 'season']).to_csv(out, index=False)
    print(f'{df.uc_id.nunique()} cities x {df.season.nunique()} seasons -> {out.relative_to(C.ROOT)}')
    lat = {ft['properties']['ID_UC_G0']: ft['properties']['lat'] for ft in feats}
    checks(df, lat, full)


if __name__ == '__main__':
    main()
