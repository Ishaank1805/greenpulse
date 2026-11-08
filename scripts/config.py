"""Settings shared by every script, so a change is made in one place."""
from pathlib import Path

PROJECT = 'greenpulse-510209'

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'raw'
DATA = ROOT / 'data'
CITIES_FILE = DATA / 'cities' / 'india_cities.geojson'
SAMPLES_DIR = DATA / 'samples'

# Pre-monsoon peak heat, mostly cloud-free. End date is exclusive.
START, END = '2019-01-01', '2025-01-01'
MONTHS = (4, 5)

MIN_POP = 300_000

LST_ID = 'MODIS/061/MYD11A2'   # Aqua, ~13:30 and ~01:30 overpass, 1 km, 8-day
VI_ID = 'MODIS/061/MOD13A1'    # NDVI/EVI, 500 m, 16-day
BUILT_ID = 'JRC/GHSL/P2023A/GHS_BUILT_S/2020'
POP_ID = 'WorldPop/GP/100m/pop'
ERA5_ID = 'ECMWF/ERA5_LAND/MONTHLY_AGGR'

# --- Role 1 ---
# Seasons: name -> list of calendar months. Winter wraps the year end.
SEASONS = {'pre': [4, 5], 'post': [10, 11], 'winter': [12, 1, 2]}
SRTM_ID = 'USGS/SRTMGL1_003'

# --- Role 2 ---
ERA5_DAILY_ID = 'ECMWF/ERA5_LAND/DAILY_AGGR'
CLIMATE_SCALE = 1000          # m; lets EE area-weight 9 km ERA5 cells over small city polygons
CLIMATE_FALLBACK_BUFFER = 10_000   # m; centroid buffer when a polygon misses every land cell

# --- Role 1 (final phase) ---
HEIGHT_ID = 'JRC/GHSL/P2023A/GHS_BUILT_H/2018'   # building height (m), 100 m; only epoch is 2018
SSRD_BAND = 'surface_solar_radiation_downwards_sum'   # in ERA5_ID (monthly), J/m2

# --- Role 2 (final phase, H6 felt heat) ---
H6_SEASONS = ['pre', 'post']          # pre = main, post = second; winter skipped (HI = T below 80 F)
H6_TIME = 'day'
H6_NDVI_STEP = 0.1                    # main greening step, same unit as ce_per_0.1
H6_IQR_PCT = (25, 75)                 # realistic step: each city's NDVI p25 -> p75 (pre, urban squares)
H6_R = (0.08, 0.18)                   # air/surface ratio: Du 2024 (0.006 / 0.075), Venter 2021 (0.26 / 1.45)
H6_DELTA_TD = (0.0, 0.5, 1.0, 2.0)    # extra dewpoint from leaves (degC), scenario B
H6_DELTA_STAR_MAX, H6_DELTA_STAR_STEP = 5.0, 0.05   # break-even search grid (degC)
H6_DELTA_STAR_INTERP = True           # interpolate linearly inside the 0.05 C step where d_hi crosses 0
