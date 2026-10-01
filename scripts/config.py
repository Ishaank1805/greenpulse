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
