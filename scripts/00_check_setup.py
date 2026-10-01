"""Step 0: confirm Earth Engine connects and every dataset path returns data.

Checks each collection has images in the April-May 2019-2024 window and that
values at one point in Jodhpur are physically plausible after scaling.
"""
import ee

PROJECT = 'greenpulse-510209'
ee.Initialize(project=PROJECT)

JODHPUR = ee.Geometry.Point([73.02, 26.29])
START, END = '2019-01-01', '2025-01-01'
APR_MAY = ee.Filter.calendarRange(4, 5, 'month')


def window(coll_id):
    return ee.ImageCollection(coll_id).filterDate(START, END).filter(APR_MAY)


def value_at(img, scale):
    return img.reduceRegion(ee.Reducer.first(), JODHPUR, scale).getInfo()


print(f'Connected to project: {PROJECT}\n')

# MODIS Aqua LST (8-day, 1 km)
lst_c = window('MODIS/061/MYD11A2')
lst = lst_c.select('LST_Day_1km').mean().multiply(0.02).subtract(273.15)
print('MYD11A2 LST       images:', lst_c.size().getInfo(),
      '| Jodhpur Apr-May mean LST (C):', value_at(lst, 1000))

# MODIS Terra vegetation indices (16-day, 500 m)
vi_c = window('MODIS/061/MOD13A1')
vi = vi_c.select(['NDVI', 'EVI']).mean().multiply(0.0001)
print('MOD13A1 NDVI/EVI  images:', vi_c.size().getInfo(),
      '| Jodhpur:', value_at(vi, 500))

# GHSL built-up surface, epoch 2020 (100 m, m2 per cell)
built = ee.Image('JRC/GHSL/P2023A/GHS_BUILT_S/2020').select('built_surface')
print('GHSL BUILT_S 2020 bands:', built.bandNames().getInfo(),
      '| Jodhpur built fraction:',
      value_at(built.divide(10000), 100))

# ERA5-Land monthly aggregates (~9 km)
era_c = window('ECMWF/ERA5_LAND/MONTHLY_AGGR')
era_bands = ['temperature_2m', 'dewpoint_temperature_2m',
             'total_precipitation_sum', 'volumetric_soil_water_layer_1']
era = era_c.select(era_bands).mean()
print('ERA5-Land monthly images:', era_c.size().getInfo(),
      '| Jodhpur:', value_at(era, 11132))

# WorldPop 100 m, India 2020
pop_c = (ee.ImageCollection('WorldPop/GP/100m/pop')
         .filter(ee.Filter.eq('country', 'IND'))
         .filter(ee.Filter.eq('year', 2020)))
print('WorldPop IND 2020 images:', pop_c.size().getInfo(),
      '| Jodhpur people per 100 m cell:', value_at(pop_c.first(), 100))
