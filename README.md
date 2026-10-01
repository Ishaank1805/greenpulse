# GreenPulse: Nature-Based Solutions for Urban Heat

**Research question:** Can existing urban vegetation measurably reduce heat exposure, and under what environmental conditions is the cooling effect strongest?

We estimate a *cooling slope* (°C per 0.1 NDVI) for 303 Indian cities with more than 3 lakh people. Each city gets a slope for three seasons (pre-monsoon Apr–May, post-monsoon Oct–Nov, winter Dec–Feb), by day and by night. We then explain the variation using climate (ERA5-Land), urban form (GHSL) and population (WorldPop).

Team: Atharv Johar, Himani Das, Ishaan Karan, Nidhi Vaidya, Prajna Penmetsa

## Layout

```
scripts/          Earth Engine sampling and analysis scripts; settings in scripts/config.py
data/cities/      city boundaries (india_cities.geojson)
data/samples/     per-city 1 km square CSVs (not committed; regenerate with script 1)
data/results/     cooling_efficiency.csv, city_climate.csv, etc.
figures/          charts for the slides and report
docs/             literature review, plans
```

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
earthengine authenticate
```

The Earth Engine project is `greenpulse-510209`. Ask Himani to add you. The free quota is shared by the whole team, so do not re-run big jobs without a reason.

## Data

| Dataset | Earth Engine ID |
| --- | --- |
| MODIS LST (Aqua) | `MODIS/061/MYD11A2` |
| MODIS NDVI/EVI | `MODIS/061/MOD13A2` |
| ERA5-Land | `ECMWF/ERA5_LAND/MONTHLY_AGGR` |
| GHSL built-up / height | `JRC/GHSL/P2023A/GHS_BUILT_S`, `JRC/GHSL/P2023A/GHS_BUILT_H` (2018 only) |
| WorldPop | `WorldPop/GP/100m/pop` (latest year 2020) |
| Elevation | `USGS/SRTMGL1_003` |
| OpenStreetMap | per-city water polygons via Overpass / OSMnx |

## Ground rules

- Change settings in `scripts/config.py`, not inside scripts.
- Check every result against a second calculation or known real-world values before passing it on.
- Results go in `data/results/` and figures in `figures/`, with clear names.
