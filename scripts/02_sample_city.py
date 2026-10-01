"""Stage 1: one row per 1 km MODIS cell inside a city, saved as CSV.

Columns:
  lst_day, lst_night  mean Apr-May surface temperature (C), good-quality obs only
  n_day, n_night      how many 8-day composites passed the quality mask
  ndvi, evi           mean Apr-May vegetation index, cloud-free obs only
  built               fraction of the 1 km cell covered by buildings (0-1)
  pop                 people living in the cell (WorldPop 2020)
  lon, lat            cell centre

Usage: python scripts/02_sample_city.py Jodhpur Kochi
"""
import json
import sys

import ee
import pandas as pd

import config as C

ee.Initialize(project=C.PROJECT)

SEASON = ee.Filter.calendarRange(C.MONTHS[0], C.MONTHS[1], 'month')


def bits(img, start, end):
    """Extract bits start..end (inclusive) from a QA band."""
    width = end - start + 1
    return img.rightShift(start).bitwiseAnd((1 << width) - 1)


def lst_mean(band, qc_band):
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
            .filterDate(C.START, C.END).filter(SEASON).map(mask))
    mean = coll.mean().multiply(0.02).subtract(273.15)
    return mean, coll.count()


def vi_mean():
    """Mean NDVI and EVI. SummaryQA 0 = good, 1 = marginal; 2-3 = snow/cloud."""
    def mask(img):
        return img.select(['NDVI', 'EVI']).updateMask(img.select('SummaryQA').lte(1))

    coll = (ee.ImageCollection(C.VI_ID)
            .filterDate(C.START, C.END).filter(SEASON).map(mask))
    return coll.mean().multiply(0.0001).rename(['ndvi', 'evi'])


def build_stack():
    # The 1 km MODIS grid everything is aggregated onto. mean() drops the
    # native projection, so take it from a raw image.
    grid = ee.ImageCollection(C.LST_ID).first().select('LST_Day_1km').projection()

    day, n_day = lst_mean('LST_Day_1km', 'QC_Day')
    night, n_night = lst_mean('LST_Night_1km', 'QC_Night')

    # Finer layers are averaged/summed up to 1 km, never LST down to them.
    vi = (vi_mean().setDefaultProjection(
              ee.ImageCollection(C.VI_ID).first().projection())
          .reduceResolution(ee.Reducer.mean(), maxPixels=64)
          .reproject(grid))

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

    return (day.rename('lst_day')
            .addBands(night.rename('lst_night'))
            .addBands(n_day.rename('n_day'))
            .addBands(n_night.rename('n_night'))
            .addBands(vi).addBands(built).addBands(pop)
            .reproject(grid)), grid


def load_city(name):
    with open(C.CITIES_FILE) as f:
        features = json.load(f)['features']
    matches = [ft for ft in features if ft['properties']['name'].lower() == name.lower()]
    if len(matches) != 1:
        sys.exit(f'Expected exactly one city named {name!r}, found {len(matches)}')
    return matches[0]


def sample_city(name, stack, grid):
    feature = load_city(name)
    region = ee.Geometry(feature['geometry'])
    # Keep masked cells (dropNulls=False) so we can report how many were lost.
    fc = stack.sample(region=region, projection=grid, scale=grid.nominalScale(),
                      geometries=True, dropNulls=False)
    rows = []
    for ft in fc.getInfo()['features']:
        props = ft['properties']
        props['lon'], props['lat'] = ft['geometry']['coordinates']
        rows.append(props)
    df = pd.DataFrame(rows)
    df.insert(0, 'city', feature['properties']['name'])
    df.insert(1, 'uc_id', feature['properties']['ID_UC_G0'])
    return df


def main(names):
    C.SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    stack, grid = build_stack()
    for name in names:
        df = sample_city(name, stack, grid)
        out = C.SAMPLES_DIR / f'{name.lower()}.csv'
        df.to_csv(out, index=False)
        print(f'{name}: {len(df)} cells -> {out.relative_to(C.ROOT)}')


if __name__ == '__main__':
    main(sys.argv[1:] or ['Jodhpur', 'Kochi'])
