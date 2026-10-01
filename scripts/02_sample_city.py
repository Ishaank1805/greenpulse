"""Stage 1: one row per 1 km MODIS cell x season inside a city (long format).

All three seasons come from a single sample() call per city, to save the
shared Earth Engine quota. Output columns (docs/roles/README.md section 3.1):
  city, uc_id, season, cell_id, lon, lat,
  lst_day, lst_night  mean seasonal surface temperature (C), good-quality obs only
  n_day, n_night      how many 8-day composites passed the quality mask
  ndvi, evi           mean seasonal vegetation index, cloud-free obs only
  built               fraction of the 1 km cell covered by buildings (0-1)
  pop                 people living in the cell (WorldPop 2020)
  elev                mean elevation (m, SRTM)
built, pop and elev are the same in every season.

Usage: python scripts/02_sample_city.py [name or uc_id ...]   (default: Jodhpur Kochi)
"""
import json
import sys

import ee
import pandas as pd

import config as C

ee.Initialize(project=C.PROJECT)

PER_SEASON = ['lst_day', 'lst_night', 'n_day', 'n_night', 'ndvi', 'evi']
STATIC = ['built', 'pop', 'elev']
COLUMNS = (['city', 'uc_id', 'season', 'cell_id', 'lon', 'lat']
           + PER_SEASON + STATIC)


def season_filter(months):
    """Images whose month is in `months`. Listing months avoids calendarRange
    wrap-around ambiguity for winter (Dec, Jan, Feb)."""
    return ee.Filter.Or(*[ee.Filter.calendarRange(m, m, 'month') for m in months])


def bits(img, start, end):
    """Extract bits start..end (inclusive) from a QA band."""
    width = end - start + 1
    return img.rightShift(start).bitwiseAnd((1 << width) - 1)


def lst_mean(band, qc_band, season):
    """Mean LST in C, keeping only pixels the QC band rates as reliable.

    MYD11A2 QC bits 0-1: 0 = good, 1 = other quality (check error flag).
    Bits 6-7: LST error, 0 = <=1 K, 1 = <=2 K. We keep good pixels, plus
    'other quality' pixels whose error is at most 2 K.
    """
    def mask(img):
        qc = img.select(qc_band)
        qa, err = bits(qc, 0, 1), bits(qc, 6, 7)
        ok = qa.eq(0).Or(qa.eq(1).And(err.lte(1)))
        return img.select(band).updateMask(ok)

    coll = (ee.ImageCollection(C.LST_ID)
            .filterDate(C.START, C.END).filter(season).map(mask))
    mean = coll.mean().multiply(0.02).subtract(273.15)
    return mean, coll.count()


def vi_mean(season):
    """Mean NDVI and EVI. SummaryQA 0 = good, 1 = marginal; 2-3 = snow/cloud."""
    def mask(img):
        return img.select(['NDVI', 'EVI']).updateMask(img.select('SummaryQA').lte(1))

    coll = (ee.ImageCollection(C.VI_ID)
            .filterDate(C.START, C.END).filter(season).map(mask))
    return coll.mean().multiply(0.0001).rename(['ndvi', 'evi'])


def build_stack():
    # The 1 km MODIS grid everything is aggregated onto. mean() drops the
    # native projection, so take it from a raw image.
    grid = ee.ImageCollection(C.LST_ID).first().select('LST_Day_1km').projection()
    vi_proj = ee.ImageCollection(C.VI_ID).first().projection()

    bands = []
    for name, months in C.SEASONS.items():
        season = season_filter(months)
        day, n_day = lst_mean('LST_Day_1km', 'QC_Day', season)
        night, n_night = lst_mean('LST_Night_1km', 'QC_Night', season)
        # Finer layers are averaged/summed up to 1 km, never LST down to them.
        vi = (vi_mean(season).setDefaultProjection(vi_proj)
              .reduceResolution(ee.Reducer.mean(), maxPixels=64)
              .reproject(grid))
        bands += [day.rename(f'lst_day_{name}'),
                  night.rename(f'lst_night_{name}'),
                  n_day.rename(f'n_day_{name}'),
                  n_night.rename(f'n_night_{name}'),
                  vi.rename([f'ndvi_{name}', f'evi_{name}'])]

    built_img = ee.Image(C.BUILT_ID).select('built_surface')
    built = (built_img.divide(10000)  # m2 built per 100 m cell -> fraction
             .reduceResolution(ee.Reducer.mean(), maxPixels=1024)
             .reproject(grid).rename('built'))

    pop_img = (ee.ImageCollection(C.POP_ID)
               .filter(ee.Filter.eq('country', 'IND'))
               .filter(ee.Filter.eq('year', 2020)).first())
    # reduceResolution with a weighted sum returns a mean here, and unmask()
    # drops the native projection. So: people -> density, average density to
    # 1 km, multiply by cell area. Checked against the native-grid total for a
    # 30 km circle around Jodhpur: 1,845,471 vs 1,845,106.
    pop = (pop_img.divide(ee.Image.pixelArea())
           .reduceResolution(ee.Reducer.mean(), maxPixels=1024)
           .reproject(grid)
           .multiply(ee.Image.pixelArea().reproject(grid))
           .rename('pop'))

    # SRTM is 1 arc-second; cells narrow with latitude, so a 1 km square holds
    # >1024 of them north of ~28 N (New Delhi needs 1026). 4096 covers India.
    elev = (ee.Image(C.SRTM_ID).select('elevation')
            .reduceResolution(ee.Reducer.mean(), maxPixels=4096)
            .reproject(grid).rename('elev'))

    stack = ee.Image.cat(bands + [built, pop, elev]).reproject(grid)
    return stack, grid


def load_city(key):
    """Find one city by name (case-insensitive) or by numeric uc_id."""
    with open(C.CITIES_FILE) as f:
        features = json.load(f)['features']
    key = str(key)
    if key.isdigit():
        matches = [ft for ft in features if ft['properties']['ID_UC_G0'] == int(key)]
    else:
        matches = [ft for ft in features
                   if ft['properties']['name'].lower() == key.lower()]
    if len(matches) != 1:
        sys.exit(f'Expected exactly one city for {key!r}, found {len(matches)}')
    return matches[0]


def output_path(feature):
    props = feature['properties']
    slug = props['name'].lower().replace(' ', '_')
    return C.SAMPLES_DIR / f"{props['ID_UC_G0']}_{slug}.csv"


def to_long(wide):
    """Wide (one row per cell, season-suffixed bands) -> long (cell x season)."""
    parts = []
    for name in C.SEASONS:
        part = wide[['cell_id', 'lon', 'lat']].copy()
        part.insert(0, 'season', name)
        for col in PER_SEASON:
            part[col] = wide.get(f'{col}_{name}')  # NaN if masked everywhere
        for col in STATIC:
            part[col] = wide.get(col)
        parts.append(part)
    long = pd.concat(parts, ignore_index=True)
    for col in ('n_day', 'n_night'):
        long[col] = pd.to_numeric(long[col]).fillna(0).astype('Int64')
    return long


def sample_one(feature, stack, grid):
    """Sample all seasons for one city with a single sample() call."""
    region = ee.Geometry(feature['geometry'])
    # Keep masked cells (dropNulls=False) so missing data can be counted.
    fc = stack.sample(region=region, projection=grid, scale=grid.nominalScale(),
                      geometries=True, dropNulls=False)
    rows = []
    for ft in fc.getInfo()['features']:
        props = ft['properties']
        props['lon'], props['lat'] = ft['geometry']['coordinates']
        rows.append(props)
    wide = pd.DataFrame(rows)
    wide['cell_id'] = [f'{lon:.5f}_{lat:.5f}' for lon, lat in zip(wide.lon, wide.lat)]

    long = to_long(wide)
    long.insert(0, 'city', feature['properties']['name'])
    long.insert(1, 'uc_id', feature['properties']['ID_UC_G0'])
    return long[COLUMNS]


def main(keys):
    C.SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    stack, grid = build_stack()
    for key in keys:
        feature = load_city(key)
        df = sample_one(feature, stack, grid)
        out = output_path(feature)
        df.to_csv(out, index=False)
        n_cells = df.cell_id.nunique()
        print(f"{feature['properties']['name']}: {n_cells} cells x "
              f"{len(C.SEASONS)} seasons = {len(df)} rows -> {out.relative_to(C.ROOT)}")


if __name__ == '__main__':
    main(sys.argv[1:] or ['Jodhpur', 'Kochi'])
