"""Task 9: Hyderabad case study. What does 30 m Landsat show that 1 km MODIS squares cannot?

How far does a park's cooling reach, and how strong is it? Compared with Shah et al. 2021
(Bengaluru, Landsat surface temperature: 2.23 C cooler, cooling reaching 347 m).

Steps
  1. Parks and water from OpenStreetMap (osmnx), cached in raw/hyderabad/.
     Parks = leisure park/garden/nature_reserve + landuse recreation_ground (nature_reserve
     is needed for KBR National Park), overlapping polygons merged,
     >= 5 ha, dropped if more than half water.
  2. Rings 30 m wide out to 990 m past each park edge (UTM 44N), with all parks and water
     removed and clipped to the city outline, so a ring measures urban surroundings only.
  3. Landsat 8/9 Collection 2 Level 2, April-May 2019-2024, scene cloud cover < 20%,
     pixel clouds/shadows masked (QA_PIXEL bits 1, 3, 4), median composite at 30 m.
     Mean surface temperature of each park interior and ring via reduceRegions (cached).
  4. Per park: cubic fit of ring temperature against distance; cooling distance = first
     turning point (temperature stops rising); intensity = fitted temperature there minus
     the park interior.
  5. Checks, outputs, figures.

Landsat passes at about 10:30-11:00 local time, before MODIS Aqua's 13:30, so its
temperatures are lower than our MODIS values. That offset is expected.

Usage:  python scripts/18_hyderabad.py [--refresh-osm] [--refresh-ee]
Output: data/results/hyderabad_parks.csv, data/results/hyderabad_ring_profile.csv,
        figures/HYD_ring_profile.png, figures/HYD_map.png
"""
import argparse
import json

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.collections import PolyCollection
from pyproj import Transformer
from scipy.stats import spearmanr

import config as C
from style import MUTED, apply_style, save

UC_ID, NAME = 9524, 'Hyderabad'
UTM = 'EPSG:32644'
CACHE = C.RAW / 'hyderabad'
OUT_PARKS = C.DATA / 'results' / 'hyderabad_parks.csv'
OUT_RINGS = C.DATA / 'results' / 'hyderabad_ring_profile.csv'

PARK_TAGS = {'leisure': ['park', 'garden', 'nature_reserve'], 'landuse': ['recreation_ground']}
WATER_TAGS = {'natural': ['water', 'wetland'], 'water': True,
              'waterway': ['riverbank', 'dock'], 'landuse': ['reservoir', 'basin']}
MIN_PARK_HA = 5.0
FALLBACK_PARK_HA = 2.0
MAX_WATER_SHARE = 0.5
RING_W = 30
RING_MAX = 990                 # outer edge of the last ring, m
MIN_RING_PX = 5                # a ring needs at least this many 30 m pixels
MIN_RINGS = 15                 # a park needs at least this many usable rings for a fit
YEARS = ('2019-01-01', '2025-01-01')
MONTHS = (4, 5)
MAX_SCENE_CLOUD = 20
SHAH = dict(cooling_c=2.23, distance_m=347)

SIN = '+proj=sinu +R=6371007.181 +nadgrids=@null +wktext +units=m'
HALF = 926.625433055833 / 2


# ---------------------------------------------------------------- 1. OpenStreetMap
def city_outline():
    c = gpd.read_file(C.CITIES_FILE)
    return c[c.ID_UC_G0 == UC_ID].geometry.iloc[0]


def osm_layer(name, tags, polygon, refresh):
    import osmnx as ox
    path = CACHE / f'{name}_raw.gpkg'
    if path.exists() and not refresh:
        return gpd.read_file(path)
    ox.settings.timeout = 300
    ox.settings.use_cache = True
    ox.settings.cache_folder = str(C.ROOT / 'cache' / 'osmnx')
    g = ox.features_from_polygon(polygon, tags)
    g = g[g.geom_type.isin(['Polygon', 'MultiPolygon'])].reset_index()
    keep = [c for c in ('osmid', 'name', 'leisure', 'landuse', 'natural', 'water') if c in g.columns]
    g = gpd.GeoDataFrame(g[keep].astype(str), geometry=g.geometry.values, crs=g.crs)
    CACHE.mkdir(parents=True, exist_ok=True)
    g.to_file(path, driver='GPKG')
    return g


def parks_and_water(refresh):
    outline = city_outline()
    raw_parks = osm_layer('parks', PARK_TAGS, outline, refresh).to_crs(UTM)
    water = osm_layer('water', WATER_TAGS, outline, refresh).to_crs(UTM)
    water_union = water.geometry.make_valid().union_all()

    merged = gpd.GeoDataFrame(geometry=[raw_parks.geometry.make_valid().union_all()],
                              crs=UTM).explode(index_parts=False).reset_index(drop=True)
    merged['area_ha'] = merged.area / 1e4
    merged['water_share'] = merged.geometry.intersection(water_union).area / merged.area

    # name = name of the largest OSM polygon inside each merged park
    named = raw_parks[raw_parks['name'].notna() & (raw_parks['name'] != 'None')].copy()
    named['a'] = named.area
    j = gpd.sjoin(named[['name', 'a', 'geometry']], merged[['geometry']],
                  predicate='intersects', how='inner')
    best = j.sort_values('a').groupby('index_right')['name'].last()
    merged['name'] = merged.index.map(best)
    named_parts = merged[merged['name'].notna()].dissolve(by='name').reset_index()
    merged = pd.concat([named_parts, merged[merged['name'].isna()]], ignore_index=True)
    merged = gpd.GeoDataFrame(merged[['name', 'geometry']], geometry='geometry', crs=UTM)
    merged['area_ha'] = merged.area / 1e4
    merged['water_share'] = merged.geometry.intersection(water_union).area / merged.area

    def select(min_ha):
        p = merged[(merged.area_ha >= min_ha) & (merged.water_share <= MAX_WATER_SHARE)]
        return p.reset_index(drop=True)
    parks, min_ha = select(MIN_PARK_HA), MIN_PARK_HA
    if len(parks) < 10:
        parks, min_ha = select(FALLBACK_PARK_HA), FALLBACK_PARK_HA
        print(f'Fewer than 10 parks of >= {MIN_PARK_HA} ha, so the threshold is relaxed to {min_ha} ha.')
    parks['park_id'] = np.arange(len(parks))
    print(f'OSM: {len(raw_parks)} park polygons -> {len(merged)} merged parks -> '
          f'{len(parks)} kept (>= {min_ha} ha, <= {MAX_WATER_SHARE:.0%} water); '
          f'{len(water)} water polygons')
    return parks, water_union, gpd.GeoSeries([outline], crs='EPSG:4326').to_crs(UTM).iloc[0], min_ha


# ---------------------------------------------------------------- 2. rings
def build_rings(parks, water_union, outline_utm):
    exclude = parks.geometry.union_all().union(water_union)
    rows = []
    for p in parks.itertuples():
        interior = p.geometry.difference(water_union)
        rows.append(dict(park_id=p.park_id, ring_m=0, geometry=interior))
        inner = p.geometry
        for outer_d in range(RING_W, RING_MAX + 1, RING_W):
            outer = p.geometry.buffer(outer_d)
            ring = outer.difference(inner).difference(exclude).intersection(outline_utm)
            inner = outer
            if ring.area >= MIN_RING_PX * RING_W * RING_W:
                rows.append(dict(park_id=p.park_id, ring_m=outer_d, geometry=ring))
    rings = gpd.GeoDataFrame(rows, crs=UTM)
    rings['geometry'] = rings.geometry.simplify(5)
    print(f'Rings: {len(rings)} features (park interiors + rings) for {parks.park_id.nunique()} parks')
    return rings


# ---------------------------------------------------------------- 3. Earth Engine
def ee_init():
    import ee
    ee.Initialize(project=C.PROJECT)
    return ee


def landsat_composite(ee, region):
    def prep(img):
        qa = img.select('QA_PIXEL')
        clear = (qa.bitwiseAnd(1 << 1).eq(0)          # dilated cloud
                 .And(qa.bitwiseAnd(1 << 3).eq(0))   # cloud
                 .And(qa.bitwiseAnd(1 << 4).eq(0)))  # cloud shadow
        st = img.select('ST_B10')
        lst = st.multiply(0.00341802).add(149).subtract(273.15).rename('lst')
        sr = img.select(['SR_B5', 'SR_B4']).multiply(0.0000275).add(-0.2)
        ndvi = sr.normalizedDifference(['SR_B5', 'SR_B4']).rename('ndvi')
        return lst.addBands(ndvi).updateMask(clear.And(st.gt(0)))

    months = ee.Filter.Or(*[ee.Filter.calendarRange(m, m, 'month') for m in MONTHS])
    coll = (ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
            .merge(ee.ImageCollection('LANDSAT/LC09/C02/T1_L2'))
            .filterBounds(region).filterDate(*YEARS).filter(months)
            .filter(ee.Filter.lt('CLOUD_COVER', MAX_SCENE_CLOUD)))
    n = coll.size().getInfo()
    comp = coll.map(prep).median().setDefaultProjection(UTM, None, 30)
    return comp, n


def ring_stats(rings, refresh):
    """All Earth Engine work. Each piece is cached as soon as it arrives, so a failure
    late in the run never repeats (or wastes) the earlier requests."""
    CACHE.mkdir(parents=True, exist_ok=True)
    p_stats, p_meta = CACHE / 'ring_stats.csv', CACHE / 'ee_meta.json'
    p_cmp, p_map = CACHE / 'modis_compare.csv', CACHE / 'map_90m.npy'
    p_ndvi = CACHE / 'park_ndvi.csv'
    if refresh:
        for p in (p_stats, p_meta, p_cmp, p_map, p_ndvi):
            p.unlink(missing_ok=True)
    if all(p.exists() for p in (p_stats, p_meta, p_cmp, p_map, p_ndvi)):
        return pd.read_csv(p_stats), json.loads(p_meta.read_text())

    ee = ee_init()
    outline = gpd.GeoSeries([city_outline()], crs='EPSG:4326')
    margin = outline.to_crs(UTM).buffer(1500).to_crs('EPSG:4326')
    region = ee.Geometry(json.loads(margin.to_json())['features'][0]['geometry'])
    comp, n_scenes = landsat_composite(ee, region)
    lst = comp.select('lst')
    bounds = outline.to_crs(UTM).total_bounds

    if not p_stats.exists():
        reducer = ee.Reducer.mean().combine(ee.Reducer.count(), sharedInputs=True)
        feats = json.loads(rings.to_crs('EPSG:4326').to_json())['features']
        out, batch = [], 250
        for i in range(0, len(feats), batch):
            fc = ee.FeatureCollection([ee.Feature(ee.Geometry(f['geometry']),
                                                  {'park_id': f['properties']['park_id'],
                                                   'ring_m': f['properties']['ring_m']})
                                       for f in feats[i:i + batch]])
            res = lst.reduceRegions(collection=fc, reducer=reducer, scale=30, crs=UTM).getInfo()
            out += [f['properties'] for f in res['features']]
            print(f'  reduceRegions {min(i + batch, len(feats))}/{len(feats)}')
        pd.DataFrame(out).rename(columns={'mean': 'lst_c', 'count': 'n_pixels'}).to_csv(p_stats, index=False)

    if not p_meta.exists():
        # pixel-value range over the city (plausibility check) at 90 m
        pct = lst.reduceRegion(ee.Reducer.percentile([5, 50, 95]), region, scale=90,
                               maxPixels=1e8).getInfo()
        p_meta.write_text(json.dumps(dict(n_scenes=n_scenes, pct=pct, bounds=[float(b) for b in bounds])))

    if not p_cmp.exists():
        # Landsat averaged into MODIS 1 km squares, sampled at Hyderabad's sample-square centres
        grid = ee.ImageCollection(C.LST_ID).first().select('LST_Day_1km').projection()
        l1km = lst.reduceResolution(ee.Reducer.mean(), maxPixels=2048).reproject(grid)
        s = pd.read_csv(C.SAMPLES_DIR / '9524_hyderabad.csv')
        s = s[s.season == 'pre']
        pts = ee.FeatureCollection([ee.Feature(ee.Geometry.Point([lo, la]), {'cell_id': cid})
                                    for lo, la, cid in zip(s.lon, s.lat, s.cell_id)])
        modis = l1km.sampleRegions(collection=pts, scale=grid.nominalScale()).getInfo()
        pd.DataFrame([f['properties'] for f in modis['features']]).to_csv(p_cmp, index=False)

    if not p_ndvi.exists():
        # mean NDVI of each park interior: are the parks that do not cool the dry ones?
        inter = rings[rings.ring_m == 0].to_crs('EPSG:4326')
        feats = json.loads(inter.to_json())['features']
        fc = ee.FeatureCollection([ee.Feature(ee.Geometry(f['geometry']),
                                              {'park_id': f['properties']['park_id']}) for f in feats])
        res = comp.select('ndvi').reduceRegions(collection=fc, reducer=ee.Reducer.mean(),
                                                scale=30, crs=UTM).getInfo()
        pd.DataFrame([f['properties'] for f in res['features']]).rename(
            columns={'mean': 'ndvi_park'}).to_csv(p_ndvi, index=False)

    if not p_map.exists():
        # 90 m map for the figure; masked pixels become -999, then NaN when plotted
        rect = ee.Geometry.Rectangle(list(bounds), UTM, False)
        img = lst.toFloat().unmask(-999).reproject(UTM, None, 90)
        arr = img.sampleRectangle(region=rect).get('lst').getInfo()
        np.save(p_map, np.array(arr, dtype=float))

    return pd.read_csv(p_stats), json.loads(p_meta.read_text())


# ---------------------------------------------------------------- 4. cooling per park
def cooling(parks, stats):
    rows, prof = [], []
    for p in parks.itertuples():
        st = stats[stats.park_id == p.park_id]
        interior = st[st.ring_m == 0]
        r = st[(st.ring_m > 0) & (st.n_pixels >= MIN_RING_PX)].dropna(subset=['lst_c']).sort_values('ring_m')
        if interior.empty or interior.lst_c.isna().all() or len(r) < MIN_RINGS:
            continue
        lst_park = float(interior.lst_c.iloc[0])
        d = r.ring_m.values - RING_W / 2
        coef = np.polyfit(d, r.lst_c.values, 3)
        deriv, second = np.polyder(coef), np.polyder(coef, 2)
        roots = [x.real for x in np.roots(deriv) if abs(x.imag) < 1e-9 and 0 < x.real <= RING_MAX]
        maxima = sorted(x for x in roots if np.polyval(second, x) < 0)
        flag = ''
        if maxima:
            dist = maxima[0]
        else:
            dist, flag = float(RING_MAX), 'no turning point within 990 m'
        plateau = float(np.polyval(coef, dist))
        rows.append(dict(park_id=p.park_id, name=p.name if isinstance(p.name, str) else '',
                         area_ha=round(p.area_ha, 2), lst_park_c=lst_park,
                         lst_plateau_c=plateau, cooling_c=plateau - lst_park,
                         distance_m=dist, flag=flag,
                         far_ring_c=float(r[r.ring_m > 500].lst_c.mean())))
        prof += [dict(park_id=p.park_id, ring_m=0, lst_c=lst_park,
                      n_pixels=int(interior.n_pixels.iloc[0]))]
        prof += [dict(park_id=p.park_id, ring_m=int(m), lst_c=v, n_pixels=int(n))
                 for m, v, n in zip(r.ring_m, r.lst_c, r.n_pixels)]
    return pd.DataFrame(rows), pd.DataFrame(prof)


# ---------------------------------------------------------------- 5. checks + figures
def checks(res, meta, min_ha):
    cooler = (res.lst_park_c < res.far_ring_c).mean()
    p = meta['pct']
    mc = pd.read_csv(CACHE / 'modis_compare.csv').merge(
        pd.read_csv(C.SAMPLES_DIR / '9524_hyderabad.csv').query("season == 'pre'")[['cell_id', 'lst_day']],
        on='cell_id').dropna(subset=['lst', 'lst_day'])
    rho = spearmanr(mc.lst, mc.lst_day)
    print('\nChecks')
    print(f'  Landsat scenes (Apr-May 2019-2024, < {MAX_SCENE_CLOUD}% cloud): {meta["n_scenes"]} '
          f'({"OK" if meta["n_scenes"] >= 5 else "FEWER THAN 5"})')
    print(f'  Parks analysed: {len(res)} (>= {min_ha} ha) ({"OK" if len(res) >= 10 else "FEWER THAN 10"})')
    print(f'  Parks cooler inside than their 500-990 m surroundings: {cooler:.0%}')
    print(f'  Composite surface temperature over the city, 5th/50th/95th percentile: '
          f'{p.get("lst_p5"):.1f} / {p.get("lst_p50"):.1f} / {p.get("lst_p95"):.1f} C')
    print(f'  Landsat averaged to MODIS squares vs MODIS daytime (pre-monsoon): Spearman '
          f'{rho.statistic:+.2f} (p = {rho.pvalue:.2g}, n = {len(mc)}); mean offset '
          f'{(mc.lst - mc.lst_day).mean():+.1f} C (Landsat ~10:30 vs MODIS 13:30)')
    return dict(cooler=cooler, rho=rho.statistic, n_cmp=len(mc))


def fig_profile(prof, res):
    rel = prof.merge(res[['park_id', 'lst_park_c', 'ndvi_park']], on='park_id')
    rel['d'] = rel.lst_c - rel.lst_park_c
    rings = rel[rel.ring_m > 0]
    cut = res.ndvi_park.median()
    fig, ax = plt.subplots(figsize=(7, 4.2))
    for greener, colour, label in ((True, '#1B7F3B', 'Greener half of parks'),
                                   (False, '#B8860B', 'Drier half of parks')):
        part = rings[(rings.ndvi_park >= cut) == greener]
        g = part.groupby('ring_m').d
        q = pd.DataFrame({'med': g.median(), 'q1': g.quantile(0.25), 'q3': g.quantile(0.75),
                          'n': g.size()})
        q = q[q.n >= 4]
        x = q.index.values - RING_W / 2
        n = part.park_id.nunique()
        ax.fill_between(x, q.q1, q.q3, color=colour, alpha=0.15)
        ax.plot(x, q.med, color=colour, lw=2.2,
                label=f'{label} (NDVI {"≥" if greener else "<"} {cut:.2f}, n = {n}), median and middle half')
    ax.axhline(0, color='black', lw=1, label='Park interior')
    ax.axvline(SHAH['distance_m'], color=MUTED, ls='--', lw=1.2,
               label=f'Shah et al. 2021, Bengaluru: {SHAH["distance_m"]} m')
    ok = res[res.flag == '']
    ax.axvline(ok.distance_m.median(), color='black', ls=':', lw=1.2,
               label=f'Median cooling distance here: {ok.distance_m.median():.0f} m '
                     f'({len(ok)} of {len(res)} parks)')
    ax.set_xlabel('Distance from park edge (m)')
    ax.set_ylabel('Surface temperature minus park interior (°C)')
    ax.set_title('Hyderabad parks, Landsat 30 m, April-May 2019-2024')
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.17), fontsize=8.5, ncol=1)
    return save(fig, 'HYD_ring_profile')


def fig_map(parks, meta):
    arr = np.load(CACHE / 'map_90m.npy')
    arr[arr <= -900] = np.nan
    x0, y0, x1, y1 = meta['bounds']
    s = pd.read_csv(C.SAMPLES_DIR / '9524_hyderabad.csv').query("season == 'pre'").dropna(subset=['lst_day'])
    to_sin = Transformer.from_crs('EPSG:4326', SIN, always_xy=True)
    sin_to_utm = Transformer.from_crs(SIN, UTM, always_xy=True)
    polys = []
    for lo, la in zip(s.lon, s.lat):
        x, y = to_sin.transform(lo, la)
        cx = [x - HALF, x + HALF, x + HALF, x - HALF]
        cy = [y - HALF, y - HALF, y + HALF, y + HALF]
        ux, uy = sin_to_utm.transform(cx, cy)
        polys.append(list(zip(np.array(ux) / 1000, np.array(uy) / 1000)))

    fig, axes = plt.subplots(1, 2, figsize=(12, 5.6), sharex=True, sharey=True)
    vmin, vmax = np.nanpercentile(arr, 2), np.nanpercentile(arr, 98)
    im = axes[0].imshow(arr, extent=[x0 / 1000, x1 / 1000, y0 / 1000, y1 / 1000],
                        cmap='inferno', vmin=vmin, vmax=vmax, origin='upper')
    outline = gpd.GeoSeries([city_outline()], crs='EPSG:4326').to_crs(UTM)
    outline.scale(1e-3, 1e-3, origin=(0, 0)).boundary.plot(ax=axes[0], color='white', lw=0.9)
    parks.to_crs(UTM).geometry.scale(1e-3, 1e-3, origin=(0, 0)).boundary.plot(
        ax=axes[0], color='#7CFC00', lw=1.4)
    axes[0].set_title('Landsat, 30 m (shown at 90 m), ~10:30\nparks in green, city outline in white')
    fig.colorbar(im, ax=axes[0], shrink=0.8, label='Surface temperature (°C)')
    pc = PolyCollection(polys, array=s.lst_day.values, cmap='inferno', edgecolor='none')
    axes[1].add_collection(pc)
    axes[1].set_title('MODIS, 1 km squares, ~13:30 (our main data)')
    fig.colorbar(pc, ax=axes[1], shrink=0.8, label='Surface temperature (°C)')
    for ax in axes:
        ax.set_aspect('equal')
        ax.set_xlabel('km (UTM 44N)')
        ax.grid(False)
    axes[0].set_ylabel('km (UTM 44N)')
    axes[1].autoscale_view()
    fig.suptitle('Hyderabad before the monsoon: what 30 m shows that 1 km cannot', y=1.0)
    fig.tight_layout()
    return save(fig, 'HYD_map')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--refresh-osm', action='store_true')
    ap.add_argument('--refresh-ee', action='store_true')
    a = ap.parse_args()
    apply_style()

    parks, water_union, outline_utm, min_ha = parks_and_water(a.refresh_osm)
    rings = build_rings(parks, water_union, outline_utm)
    stats, meta = ring_stats(rings, a.refresh_ee or a.refresh_osm)
    res, prof = cooling(parks, stats)
    ndvi = pd.read_csv(CACHE / 'park_ndvi.csv')[['park_id', 'ndvi_park']]
    res = res.merge(ndvi, on='park_id', how='left')

    cols = ['park_id', 'name', 'area_ha', 'lst_park_c', 'lst_plateau_c', 'cooling_c', 'distance_m']
    res[cols + ['ndvi_park', 'flag']].to_csv(OUT_PARKS, index=False)
    prof[['park_id', 'ring_m', 'lst_c', 'n_pixels']].to_csv(OUT_RINGS, index=False)
    print(f'{len(res)} parks -> {OUT_PARKS.relative_to(C.ROOT)}; profile -> {OUT_RINGS.relative_to(C.ROOT)}')

    checks(res, meta, min_ha)
    ok = res[res.flag == '']
    print(f'\nCooling (parks with a turning point, n = {len(ok)} of {len(res)}): '
          f'median {ok.cooling_c.median():.2f} C (IQR {ok.cooling_c.quantile(.25):.2f}-'
          f'{ok.cooling_c.quantile(.75):.2f}), median distance {ok.distance_m.median():.0f} m '
          f'(IQR {ok.distance_m.quantile(.25):.0f}-{ok.distance_m.quantile(.75):.0f}). '
          f'Shah et al. 2021, Bengaluru: {SHAH["cooling_c"]} C, {SHAH["distance_m"]} m.')
    r = spearmanr(res.ndvi_park, res.cooling_c)
    green = res.ndvi_park >= res.ndvi_park.median()
    print(f'\nDo greener parks cool more? Spearman(park NDVI, cooling) = {r.statistic:+.2f} '
          f'(p = {r.pvalue:.2g}, n = {len(res)}). Median cooling: greener half '
          f'{res[green].cooling_c.median():.2f} C, drier half {res[~green].cooling_c.median():.2f} C.')
    big = res.sort_values('area_ha', ascending=False).head(8)
    print('\nLargest parks:')
    print(big[['name', 'area_ha', 'ndvi_park', 'lst_park_c', 'cooling_c', 'distance_m', 'flag']].round(2).to_string(index=False))
    for path in (fig_profile(prof, res), fig_map(parks, meta)):
        print('figure ->', path.relative_to(C.ROOT))


if __name__ == '__main__':
    main()
