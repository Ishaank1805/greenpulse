"""Tasks C + E: city climate (ERA5-Land) and Heat Index, one row per city x season.

Per city (one at a time, 1 s apart; the Earth Engine quota is shared):
  monthly  ECMWF/ERA5_LAND/MONTHLY_AGGR, 2019-2024 = 72 months, reduceRegion(mean,
           city polygon, scale=1000), one getInfo per city
  daily    ECMWF/ERA5_LAND/DAILY_AGGR, season months only (temperature_2m_max and
           daily-mean dewpoint), one getInfo per city per season
If a polygon returns nulls (small or coastal city missing every land cell), the city is
redone on centroid().buffer(10 km) and listed as a fallback.
Raw results are cached in cache/era5/{uc_id}.json (gitignored), so a rerun resumes and
never re-downloads a finished city.

Output (README 3.4): data/results/city_climate.csv
  city, uc_id, season, rain_annual_mm, rain_season_mm, t2m_c, t2m_max_c, rh_pct, swvl1,
  wind10_ms, hi_c
  rain_*    precipitation clipped at 0, m -> mm. Annual = mean month x 12.
  rh_pct    Magnus per month from monthly mean T and Td, then the season mean
  wind10_ms per month sqrt(u^2 + v^2) of the monthly mean components (approximate)
  t2m_max_c mean daily maximum temperature over the season
  hi_c      mean over days of the NOAA Heat Index from that day's Tmax and mean dewpoint
            (dewpoint changes slowly over a day, so this approximates the hottest hour)
ERA5-Land is ~9 km: one value per city, i.e. the background climate the city sits in.

Usage:
  python scripts/07_city_climate.py Jodhpur Kochi   # test on two cities first
  python scripts/07_city_climate.py                 # all 303 (tell R1/R5 first)
  python scripts/07_city_climate.py --build-only    # rebuild the CSV from the cache
Also writes figures/C_climate_overview.png.
"""
import argparse
import json
import time

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import config as C

CACHE = C.ROOT / 'cache' / 'era5'
OUT = C.DATA / 'results' / 'city_climate.csv'
COLS = ['city', 'uc_id', 'season', 'rain_annual_mm', 'rain_season_mm', 't2m_c', 't2m_max_c',
        'rh_pct', 'swvl1', 'wind10_ms', 'hi_c']
MONTHLY_BANDS = ['total_precipitation_sum', 'temperature_2m', 'dewpoint_temperature_2m',
                 'volumetric_soil_water_layer_1', 'u_component_of_wind_10m',
                 'v_component_of_wind_10m']
DAILY_BANDS = ['temperature_2m_max', 'dewpoint_temperature_2m']
PAUSE = 1
BACKOFF = (60, 60, 60)


# --------------------------------------------------------------------------- formulas
def rh_magnus(t_c, td_c):
    """Relative humidity (%) from T and dewpoint (degC), Magnus (Alduchov & Eskridge 1996)."""
    t_c, td_c = np.asarray(t_c, float), np.asarray(td_c, float)
    return 100 * np.exp(17.625 * td_c / (243.04 + td_c)) / np.exp(17.625 * t_c / (243.04 + t_c))


def heat_index_f(T, RH):
    """NOAA Heat Index (degF) from T (degF) and RH (%), vectorised.
    https://www.wpc.ncep.noaa.gov/html/heatindex_equation.shtml"""
    T, RH = np.broadcast_arrays(np.asarray(T, float), np.asarray(RH, float))
    simple = 0.5 * (T + 61.0 + (T - 68.0) * 1.2 + RH * 0.094)
    HI = (-42.379 + 2.04901523 * T + 10.14333127 * RH - 0.22475541 * T * RH
          - 0.00683783 * T * T - 0.05481717 * RH * RH + 0.00122874 * T * T * RH
          + 0.00085282 * T * RH * RH - 0.00000199 * T * T * RH * RH)
    low = (RH < 13) & (T >= 80) & (T <= 112)
    HI = np.where(low, HI - ((13 - RH) / 4) * np.sqrt(np.clip(17 - np.abs(T - 95), 0, None) / 17), HI)
    high = (RH > 85) & (T >= 80) & (T <= 87)
    HI = np.where(high, HI + ((RH - 85) / 10) * ((87 - T) / 5), HI)
    out = np.where((simple + T) / 2 < 80, simple, HI)
    return out if out.ndim else float(out)


def heat_index_c(t_c, rh):
    return (heat_index_f(np.asarray(t_c) * 9 / 5 + 32, rh) - 32) * 5 / 9


# Unit tests (README role 2, step 2c). NOAA's table gives 95 F at 90 F / 50%,
# and 109 F at 100 F / 40%.
assert 94 <= heat_index_f(90, 50) <= 96, heat_index_f(90, 50)
assert abs(heat_index_f(70, 50) - 70) < 1.5, heat_index_f(70, 50)
assert abs(heat_index_f(100, 40) - 109) <= 1, heat_index_f(100, 40)
assert abs(rh_magnus(30, 20) - 55.1) < 0.5


# --------------------------------------------------------------------------- Earth Engine
def season_filter(ee, months):
    return ee.Filter.Or(*[ee.Filter.calendarRange(m, m, 'month') for m in months])


def fetch_city(ee, geom):
    """Monthly (72 features) and daily (per season) values for one geometry."""
    def reduce(img, bands):
        return img.select(bands).reduceRegion(ee.Reducer.mean(), geom, C.CLIMATE_SCALE)

    mon = (ee.ImageCollection(C.ERA5_ID).filterDate(C.START, C.END).select(MONTHLY_BANDS)
           .map(lambda img: ee.Feature(None, reduce(img, MONTHLY_BANDS))
                .set({'year': img.date().get('year'), 'month': img.date().get('month')})))
    monthly = [f['properties'] for f in mon.getInfo()['features']]
    daily = {}
    for s, months in C.SEASONS.items():
        day = (ee.ImageCollection(C.ERA5_DAILY_ID).filterDate(C.START, C.END)
               .filter(season_filter(ee, months)).select(DAILY_BANDS)
               .map(lambda img: ee.Feature(None, reduce(img, DAILY_BANDS))
                    .set('date', img.date().format('YYYY-MM-dd'))))
        daily[s] = [f['properties'] for f in day.getInfo()['features']]
    return monthly, daily


def has_nulls(monthly, daily):
    return (any(m.get('temperature_2m') is None for m in monthly)
            or any(d.get('temperature_2m_max') is None for v in daily.values() for d in v))


def pull_city(ee, feature):
    props = feature['properties']
    path = CACHE / f"{props['ID_UC_G0']}.json"
    if path.exists():
        return 'cached'
    geom = ee.Geometry(feature['geometry'])
    for attempt, wait in enumerate(BACKOFF, 1):
        try:
            monthly, daily = fetch_city(ee, geom)
            fallback = False
            if has_nulls(monthly, daily):
                print(f"\n  fallback: {props['name']} -> centroid + {C.CLIMATE_FALLBACK_BUFFER / 1000:.0f} km")
                monthly, daily = fetch_city(ee, geom.centroid(100).buffer(C.CLIMATE_FALLBACK_BUFFER))
                fallback = True
            tmp = path.with_suffix('.tmp')
            tmp.write_text(json.dumps({'uc_id': props['ID_UC_G0'], 'city': props['name'],
                                       'fallback': fallback, 'monthly': monthly, 'daily': daily}))
            tmp.replace(path)
            return 'fallback' if fallback else 'ok'
        except Exception as e:  # quota / concurrency / network
            msg = str(e)
            print(f"\n  {props['name']} attempt {attempt}: {type(e).__name__}: {msg[:200]}")
            if attempt == len(BACKOFF):
                return 'failed'
            time.sleep(wait)


# --------------------------------------------------------------------------- pandas
def city_rows(raw):
    m = pd.DataFrame(raw['monthly'])
    precip = m.total_precipitation_sum.clip(lower=0)
    rain_annual = precip.mean() * 12 * 1000
    m['t_c'] = m.temperature_2m - 273.15
    m['td_c'] = m.dewpoint_temperature_2m - 273.15
    m['rh'] = rh_magnus(m.t_c, m.td_c)
    m['wind'] = np.hypot(m.u_component_of_wind_10m, m.v_component_of_wind_10m)
    m['p'] = precip
    rows = []
    for s, months in C.SEASONS.items():
        ms = m[m.month.isin(months)]
        d = pd.DataFrame(raw['daily'][s])
        tmax = d.temperature_2m_max - 273.15
        td = d.dewpoint_temperature_2m - 273.15
        hi = heat_index_c(tmax, rh_magnus(tmax, td))
        rows.append(dict(city=raw['city'], uc_id=raw['uc_id'], season=s,
                         rain_annual_mm=rain_annual,
                         rain_season_mm=ms.p.mean() * len(months) * 1000,
                         t2m_c=ms.t_c.mean(), t2m_max_c=tmax.mean(), rh_pct=ms.rh.mean(),
                         swvl1=ms.volumetric_soil_water_layer_1.mean(), wind10_ms=ms.wind.mean(),
                         hi_c=float(np.mean(hi)), _n_months=len(ms), _n_days=len(d),
                         _fallback=raw.get('fallback', False)))
    return rows


def build(uc_ids=None):
    files = sorted(CACHE.glob('*.json'))
    raws = [json.loads(p.read_text()) for p in files]
    if uc_ids is not None:
        raws = [r for r in raws if r['uc_id'] in uc_ids]
    df = pd.DataFrame([row for r in raws for row in city_rows(r)])
    return df


# --------------------------------------------------------------------------- checks
def checks(df, full):
    print('\n=== Checks (role 2, step 2c) ===')
    ok = True

    def get(city, season, col):
        r = df[(df.city == city) & (df.season == season)]
        return None if r.empty else r[col].iloc[0]

    def rng(label, v, lo, hi, soft=None):
        nonlocal ok
        if v is None:
            print(f'  {label}: city not in this run')
            return
        good = lo <= v <= hi
        note = ''
        if not good and soft and soft[0] <= v <= soft[1]:
            note, good = ' (accepted: ERA5 underestimates coastal rain; note it)', True
        ok &= good
        print(f"  {label}: {v:.1f} (expect {lo}-{hi}) {'ok' if good else 'CHECK'}{note}")

    print('HI unit tests: passed (asserts at import)')
    rng('Rain Jodhpur mm/yr', get('Jodhpur', 'pre', 'rain_annual_mm'), 300, 450)
    rng('Rain Kochi mm/yr', get('Kochi', 'pre', 'rain_annual_mm'), 2500, 3500, soft=(2000, 2500))
    rng('Pre t2m Jodhpur', get('Jodhpur', 'pre', 't2m_c'), 32, 36)
    rng('Pre t2m Kochi', get('Kochi', 'pre', 't2m_c'), 28, 30)
    rng('Pre RH Kochi', get('Kochi', 'pre', 'rh_pct'), 70, 85)
    rng('Pre RH Jodhpur', get('Jodhpur', 'pre', 'rh_pct'), 20, 40)
    p = df.pivot_table(index='uc_id', columns='season', values=['t2m_c', 'swvl1'])
    if {'pre', 'winter'} <= set(p['t2m_c'].columns):
        bad = p.index[p['t2m_c']['winter'] >= p['t2m_c']['pre']]
        names = df[df.uc_id.isin(bad)].city.unique().tolist()
        ok &= len(bad) == 0
        print(f"  Winter cooler than pre in every city: {'ok' if not len(bad) else f'NO, {names}'}")
        share = (p['swvl1']['post'] > p['swvl1']['pre']).mean()
        ok &= share >= 0.8
        print(f"  swvl1 post > pre in {share:.0%} of cities (need >= 80%) {'ok' if share >= .8 else 'CHECK'}")
    for city in ('Kochi', 'Chennai', 'Mumbai', 'Kolkata', 'Jodhpur'):
        hi, tx = get(city, 'pre', 'hi_c'), get(city, 'pre', 't2m_max_c')
        if hi is not None:
            print(f'  {city:8s} pre hi_c {hi:.1f} vs t2m_max_c {tx:.1f} (diff {hi - tx:+.1f}; humid '
                  f'coast should be clearly above, Jodhpur close)')
    n_nan = df[COLS].isna().sum().sum()
    ok &= n_nan == 0
    exp = 303 * 3 if full else None
    print(f"  Rows {len(df)}{f' (expect {exp})' if exp else ''}, NaNs {n_nan} {'ok' if n_nan == 0 else 'CHECK'}")
    if full:
        ok &= len(df) == exp
    print(f"  Months per season: {df.groupby('season')._n_months.unique().to_dict()}; "
          f"days per season: {df.groupby('season')._n_days.median().to_dict()}")
    fb = df[df._fallback].city.unique().tolist()
    print(f'  Fallback cities ({len(fb)}): {fb}')
    print('ALL CHECKS OK' if ok else 'SOME CHECKS NEED A LOOK (see above)')
    return ok


def overview_figure(df):
    from style import apply_style, save
    apply_style()
    pre = df[df.season == 'pre']
    fig, ax = plt.subplots(figsize=(7.5, 5.2), layout='constrained')
    sc = ax.scatter(pre.rain_annual_mm, pre.rh_pct, c=pre.t2m_c, cmap='inferno_r', s=22,
                    edgecolor='white', linewidth=0.4)
    ax.set_xscale('log')
    ax.axvline(1000, color='0.5', ls='--', lw=0.8)
    for name in ('Jodhpur', 'Kochi', 'New Delhi', 'Mumbai', 'Chennai', 'Kolkata', 'Bengaluru', 'Guwahati'):
        r = pre[pre.city == name]
        if len(r):
            ax.annotate(name, (r.rain_annual_mm.iloc[0], r.rh_pct.iloc[0]), xytext=(4, 3),
                        textcoords='offset points', fontsize=8)
    fig.colorbar(sc, ax=ax, label='Pre-monsoon mean air temperature (°C)')
    ax.set_xlabel('Annual rainfall, 2019–2024 mean (mm/yr, log scale)')
    ax.set_ylabel('Pre-monsoon relative humidity (%)')
    ax.set_title(f'The climate range our {pre.uc_id.nunique()} cities cover (ERA5-Land, one value per city)',
                 fontsize=11)
    print(' ', save(fig, 'C_climate_overview').relative_to(C.ROOT))
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cities', nargs='*', help='names or uc_ids (default: all)')
    ap.add_argument('--build-only', action='store_true')
    a = ap.parse_args()
    with open(C.CITIES_FILE) as f:
        feats = json.load(f)['features']
    if a.cities:
        keys = {str(k).lower() for k in a.cities}
        feats = [ft for ft in feats if str(ft['properties']['ID_UC_G0']) in keys
                 or ft['properties']['name'].lower() in keys]
    CACHE.mkdir(parents=True, exist_ok=True)

    if not a.build_only:
        import ee
        ee.Initialize(project=C.PROJECT)
        status = {}
        todo = sorted(feats, key=lambda f: -f['properties']['pop_2025'])
        try:
            from tqdm import tqdm
            bar = tqdm(todo, unit='city', desc='ERA5')
        except ImportError:   # pip install tqdm for a progress bar
            bar = None
        for k, ft in enumerate(bar if bar is not None else todo, 1):
            st = pull_city(ee, ft)
            status[st] = status.get(st, 0) + 1
            if st != 'cached':
                time.sleep(PAUSE)
            if bar is not None:
                bar.set_postfix(city=ft['properties']['name'][:14], **status)
            elif k % 25 == 0:
                print(f'  {k}/{len(feats)} {status}')
        print(f'Pull done: {status}')

    ids = {ft['properties']['ID_UC_G0'] for ft in feats}
    df = build(ids)
    if df.empty:
        raise SystemExit('No cached cities to build from.')
    full = len(ids) == 303
    out = OUT if full else OUT.with_name(f'city_climate_test_{len(ids)}cities.csv')
    df[COLS].sort_values(['uc_id', 'season']).to_csv(out, index=False)
    print(f"{df.uc_id.nunique()} cities x {df.season.nunique()} seasons -> {out.relative_to(C.ROOT)}")
    checks(df, full)
    if full:
        overview_figure(df)


if __name__ == '__main__':
    main()
