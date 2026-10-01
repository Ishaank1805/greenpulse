# Role 1: Pipeline

Read [README.md](README.md) first. It defines the file formats (§3), the gates (§2) and the shared rules (§4) that this file assumes.

**You own:** `scripts/02_sample_city.py`, `scripts/04_run_all_cities.py`, `scripts/05_monsoon_availability.py` and `scripts/06_water_share.py`, plus the existing lines of `scripts/config.py`.

**You produce:** `data/samples/*.csv`, `data/water/*.csv`, `data/results/run_log.csv`, `data/results/b2_checks.csv`, `data/results/lst_availability_by_month.csv` and the figures `figures/B_city_map.png` and `figures/M_lst_availability.png`.

**You present:** the **Data** section (datasets, the 303 cities, seasons, quality filtering, monsoon availability) and the sampling step of the **Method**.

**Everyone else is waiting on you.** Do B1 first and announce gate G1 the moment it passes. Then start B2 running in the background. M and G fit around B2, because B2 is mostly waiting.

## Order of work

| Step | Task | Waits on | Unblocks |
| --- | --- | --- | --- |
| 1 | Stage 0 setup | Nothing | Everything |
| 2 | **B1:** extend `02_sample_city.py`, validate | Nothing | **G1** → R3's script 03 test, R4's exposure test, your B2 and G |
| 3 | **B2:** start `04_run_all_cities.py` in the background | G1 | G4 (via R3), F (R4) |
| 4 | **M:** monsoon availability (while B2 runs) | Nothing (can even go before B1 if B1 is blocked) | A Data slide |
| 5 | **G (pilot):** water share for Jodhpur and Kochi | G1 | R3 tests the water control |
| 6 | **G (all):** water share for all sampled cities | G1; best after B2 | Final run of 03 with `built_elev_water` |
| 7 | B2 checks, final commit, Data slides | B2 done | Final results |

Do not run M and B2 at exactly the same moment, because they share the Earth Engine quota. Start B2, check it is progressing, then run M. If you see quota errors, pause M.

---

## Step 1: Stage 0 setup

```bash
git clone https://github.com/prajpenmetsa/greenpulse.git && cd greenpulse
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
earthengine authenticate
python scripts/00_check_setup.py
```

`00_check_setup.py` must print a non-zero image count and plausible Jodhpur values for every dataset. If it fails, ask Himani to add your Google account to the Earth Engine project `greenpulse-510209`.

---

## Step 2, B1: three seasons in one pass, plus elevation

**Goal:** `02_sample_city.py` writes one long-format CSV per city, matching README §3.1 exactly. Each city must take **one `sample()` call** that carries all three seasons, not three runs. This saves the shared quota.

### 2a. Archive the pilot files (do this first)

```bash
mkdir -p data/samples/_pilot_v1
git mv data/samples/jodhpur.csv data/samples/_pilot_v1/jodhpur.csv
git mv data/samples/kochi.csv   data/samples/_pilot_v1/kochi.csv
```

### 2b. `config.py` additions

Keep `MONTHS` (other code may read it). Add:

```python
# Seasons: name -> list of calendar months. Winter wraps the year end.
SEASONS = {'pre': [4, 5], 'post': [10, 11], 'winter': [12, 1, 2]}
SRTM_ID = 'USGS/SRTMGL1_003'
```

### 2c. Changes to `02_sample_city.py`

1. **Season filter.** Build it from a month list with `ee.Filter.Or(*[ee.Filter.calendarRange(m, m, 'month') for m in months])`. Do not use `calendarRange(12, 2)`, because the wrap-around behaviour is easy to get wrong. Then pass the filter into the functions as a parameter: `lst_mean(band, qc_band, season_filter)` and `vi_mean(season_filter)`. **Keep the existing QC logic exactly as it is.** It was validated.
2. **Stack.** In `build_stack()`, loop over `C.SEASONS` and add bands with a season suffix: `lst_day_pre`, `lst_night_pre`, `n_day_pre`, `n_night_pre`, `ndvi_pre`, `evi_pre`, and the same for `_post` and `_winter`. The bands `built`, `pop` and the new `elev` are added once, with no suffix.
3. **Elevation.** Use the same aggregation pattern as built-up share:
   ```python
   elev = (ee.Image(C.SRTM_ID).select('elevation')
           .reduceResolution(ee.Reducer.mean(), maxPixels=1024)
           .reproject(grid).rename('elev'))
   ```
4. **Sampling.** Keep one `stack.sample(..., dropNulls=False, geometries=True)` and one `getInfo()` per city, as now. The largest city (Hajipur, ~2,823 km²) is ~3,300 squares, which is under the 5,000-element `getInfo` limit. If a city ever errors with "collection query aborted after accumulating over 5000 elements", split its polygon into 4 bounding-box quadrants, sample each and concatenate.
5. **Reshape to long format** in pandas:
   - Build a wide DataFrame first.
   - Add `cell_id = f"{lon:.5f}_{lat:.5f}"`.
   - For each season, select the suffixed columns, strip the suffix, add `season`, and concatenate.
   - Order the columns exactly as in README §3.1: `city, uc_id, season, cell_id, lon, lat, lst_day, lst_night, n_day, n_night, ndvi, evi, built, pop, elev`.
   - Cells where a band is entirely masked arrive without that key. Pandas turns them into NaN, and they must be kept.
   - Cast `n_day` and `n_night` to nullable int (`Int64`), with masked counts set to 0.
6. **City lookup and file name.** Let `load_city` accept either a name or a numeric `uc_id` (match on `ID_UC_G0`). Write the output to `data/samples/{uc_id}_{slug}.csv`, where `slug = name.lower().replace(' ', '_')`. Expose a function `sample_one(feature, stack, grid) -> DataFrame` so that `04_run_all_cities.py` can import it.
7. **Default run.** With no arguments, the script samples Jodhpur and Kochi.

### 2d. B1 validation (all must pass before G1)

Write these as a small block at the end of the script or as a throwaway notebook. They are not committed as a separate script.

- [ ] **Season image counts.** Print the number of MYD11A2 images per season over 2019–2024:
  - Expect roughly 6 years × (61 days ÷ 8) ≈ **45 for pre and post**.
  - Expect ≈ 6 × (90 ÷ 8) ≈ **67 for winter**.
  - The pilot documentation notes one 2022 image is missing, so a count one lower is fine.
  - If winter reads ~0 or ~270, the season filter is wrong.
- [ ] **Pilot reproduced.**
  - For Jodhpur and Kochi, take the `season == 'pre'` rows and join them to `_pilot_v1/*.csv` on `cell_id`, computing `cell_id` for v1 from its lon/lat with the same formatting.
  - Row counts must match: Jodhpur **254**, Kochi **1,238** (the data rows in v1).
  - The max absolute difference must be < 1e-6 for `lst_day`, `lst_night`, `ndvi`, `evi`, `built` and `pop`. They are the same computation, so they should be identical.
  - If they differ, find out why before going further.
- [ ] **New columns are sensible.**
  - `elev`: Jodhpur roughly 200–350 m, Kochi roughly 0–50 m.
  - Winter `lst_day` is lower than pre-monsoon `lst_day` for the median square in both cities.
  - Post-monsoon `ndvi` is higher than pre-monsoon in Jodhpur, because the monsoon greens it.
- [ ] **Format.** The columns match README §3.1 exactly, `season` takes only the values {pre, post, winter}, and each city has 3 × (number of squares) rows.

### 2e. Announce G1

Commit `scripts/02_sample_city.py`, `scripts/config.py`, the two new pilot files (`5315_jodhpur.csv`, `9386_kochi.csv`) and the archived v1 files. Push, and post in the team chat:

> **G1 passed.** `data/samples/` is long format (README §3.1). Pilot files: `5315_jodhpur.csv`, `9386_kochi.csv`. Pre-season rows reproduce the v1 pilot exactly.

---

## Step 3, B2: run all 303 cities

### 3a. `04_run_all_cities.py`

- Import the sampler with `importlib.import_module('02_sample_city')`. Python cannot `import` a name that starts with a digit, but `importlib` can.
- Build the stack **once** and reuse it for every city.
- **Order:** loop over cities sorted by `pop_2025` descending, so the big, interesting cities are done first and partial results are useful early.
- **Skip** any city whose output file already exists. This makes reruns resume where they left off.
- **Retry.** Wrap each city in a retry loop with 3 attempts and backoff waits of 30 s, 120 s and 300 s. Catch `ee.EEException` and also generic exceptions such as timeouts.
- **Log.** Append one row per attempt to `data/results/run_log.csv`: `uc_id, city, status, n_rows, seconds, error`. On final failure, log it and **move on**. Never let one city stop the loop.
- **Pace.** Sleep 2 s between cities. Run one city at a time (no parallel threads), because the quota is shared.
- **Summary.** At the end, print counts of ok / failed / skipped and the slowest five cities.

### 3b. Run it in the background

```bash
nohup python scripts/04_run_all_cities.py > run_all.log 2>&1 &
tail -f run_all.log
```

Add `*.log` to `.gitignore`. Test the script first on 3 small cities, by passing a `--limit 3` flag or a list of names. The full run will probably take hours: roughly 10–60 s per city is a guess, so time the first 10 cities and estimate the total.

### 3c. Share partial results

About every 50 cities (or every couple of hours), commit what exists so R3 and R4 can work on real data:

```bash
git pull --rebase
git add data/samples/*.csv data/results/run_log.csv
git commit -m "B2: samples for N cities"
git push
```

### 3d. Rerun failures

When the loop ends, run it again. Existing files are skipped, so only the failures retry. If a city fails three times, look at the error. Common causes:

- an invalid geometry: try `.buffer(0)` on the polygon
- the 5,000-element limit: split the polygon into quadrants
- a memory error: split the polygon as well

### 3e. B2 checks, written to `data/results/b2_checks.csv`, one row per city

- [ ] Every one of the 303 cities has either a sample file or a `failed` entry with a reason.
- [ ] Rows equal 3 × the number of squares, and squares are within ±20% of `area_km2 / 0.86`. Flag any city outside this range.
- [ ] Value ranges hold:
  - `lst_day` between 5 and 65 °C (winter is lower)
  - `lst_night` between −5 and 40 °C
  - `ndvi` between −0.3 and 1
  - `built` between 0 and 1
  - `pop` ≥ 0
  - `elev` between −10 and 3,000 m
  - Count any value outside these ranges.
- [ ] Missing share per city × season: the fraction of squares with NaN `lst_day`. **Expect post-monsoon to be worst in coastal cities.** Flag cities where more than 50% are missing.
- [ ] Spot check 3 well-known cities against common knowledge:
  - New Delhi pre-monsoon median day LST roughly 40–48 °C.
  - Bengaluru cooler than Hyderabad.
  - Kolkata greener than Jaipur.

Post the summary in chat: N cities ok, N failed, and the worst cities for missing data.

---

## Step 4, M: monsoon availability (`05_monsoon_availability.py`)

**Why:** we exclude June–September. The TA will ask "why no monsoon?", so we show the data limitation instead of just asserting it.

- **Cities:** Jodhpur (5315), New Delhi (7963), Hyderabad (9524), Mumbai (7599), Kolkata (11352), Kochi (9386).
- **For each city and each calendar month 1–12, over 2019–2024:**
  - `frac_day_ok` = mean over the city's squares of (QC-passing composites in that month ÷ all composites in that month).
  - `frac_night_ok` is the same, for night.
  - Use the same QC mask as `02_sample_city.py`: import its masking function rather than copying it.
- **Efficiency:** build one multi-band image per city (24 bands: 12 months × day/night) and run **one** `reduceRegion(mean, scale=1000)` per city. That is 6 calls in total.
- **Output:** `data/results/lst_availability_by_month.csv` (README §3.5).
- **Figure:** `figures/M_lst_availability.png`. Draw one line per city, with month on the x axis and the fraction of usable composites (0–1) on the y axis. Shade June–September. Use separate panels for day and night.
- **Check:** Jun–Sep should be clearly lower than Apr–May in every city, and lowest in Mumbai and Kochi. If it isn't, re-check the mask.
- **Slide line (fill in the numbers):** "In June–September only about X% of 8-day composites are usable in Mumbai, versus Y% in April–May, so we compare pre-monsoon, post-monsoon and winter (as Kumar et al. 2017 did)."

---

## Steps 5–6, G: OSM water share (`06_water_share.py`)

**Why:** water is cool by day and warm at night, like vegetation, so partly-water squares can fake or hide the vegetation effect. It might explain Jodhpur's warm green nights. It also uses the assigned OpenStreetMap dataset.

**What already happens:** squares with no LST reading are open water and are already dropped. Partly-water squares remain, and this task handles them.

### Method

1. **City polygon.** Read it from `data/cities/india_cities.geojson`.
2. **Download water with osmnx.** Do **not** download the 1 GB India extract.
   ```python
   import osmnx as ox
   ox.settings.timeout = 300
   ox.settings.use_cache = True          # caches under ./cache/ — add cache/ to .gitignore
   TAGS = {'natural': ['water', 'wetland'], 'water': True,
           'waterway': ['riverbank', 'dock'], 'landuse': ['reservoir', 'basin']}
   gdf = ox.features_from_polygon(city_polygon, TAGS)
   gdf = gdf[gdf.geom_type.isin(['Polygon', 'MultiPolygon'])]
   ```
   Save the raw result to `raw/osm/{uc_id}.gpkg`. `raw/` is git-ignored. If Overpass times out on a big city, split the polygon into 4 quadrants and combine the results.
3. **Square polygons.**
   - Take the unique `cell_id`, `lon`, `lat` from that city's sample CSV (`season == 'pre'`).
   - Project the centres to the MODIS sinusoidal CRS: `+proj=sinu +lon_0=0 +x_0=0 +y_0=0 +R=6371007.181 +units=m +no_defs`.
   - Build a square of ±463.313 m around each centre. The MODIS 1 km pixel is 926.625 m wide.
   - This reproduces the real MODIS footprint. A lat/lon box would not.
4. **Overlap.** Project the water polygons to the same CRS, dissolve them (`unary_union`), intersect them with each square, and compute `water_frac = intersection area / square area`, clipped to 0–1.
5. **Output:** `data/water/{uc_id}_{slug}.csv` with `uc_id, cell_id, water_frac`, including squares where the share is 0.
6. **Pace:** for the all-city run, sleep 1–2 s between cities and skip cities that are already done, as in B2. Log failures.

### Order

- **First do Jodhpur and Kochi**, commit them and tell R3 ("G pilot ready"). R3 then tests the `built_elev_water` control.
- Then run all cities. Start after B2 has produced the sample files: run on whatever exists, then rerun at the end.

### Checks

- [ ] **Kochi.** The pilot handover says 185 squares are open water (no LST). Most of those should have `water_frac > 0.5`. Report how many do.
- [ ] **Low NDVI over water.** For squares with `water_frac > 0.5` that do have LST, pre-season NDVI should mostly be below 0.2. Report the median.
- [ ] **Small water share in dry cities.** Jodhpur should have only a few squares with any water: a handful of lakes and tanks.
- [ ] **Sea is a known gap.** In OSM the sea is a coastline line, not a water polygon. Coastal squares that are partly sea get `water_frac` ≈ 0. Most such squares are below 10% built-up and are excluded anyway. Count the coastal squares that have built ≥ 0.10 and NaN LST, and note this as a limitation.

---

## Step 7: final hand-off and your slides

When B2 and G are done:

1. Post "B2 complete: N cities sampled, N failed (list)" and "G complete" in chat. R3 then runs the final 03, which produces G4.
2. Make `figures/B_city_map.png`: the 303 city centres (`lon`, `lat` from the geojson), with points sized by `pop_2025`. Add a light India outline if it is easy: Natural Earth admin-0, downloaded once to `raw/`. Otherwise use points only. Colour the points by `rain_annual_mm` from R2's `city_climate.csv` once it exists. That shows the moisture range in one picture.

**Your slides:**

1. **Data:** a table of the datasets (MODIS LST, MODIS NDVI/EVI, ERA5-Land, GHSL, WorldPop, OSM, SRTM), giving each one's resolution and what it is used for. Copy the IDs from the main README.
2. **Study area:** the city map and the three seasons, plus one line on why the monsoon is excluded, using the M figure.
3. **Method, sampling:** a 1 km MODIS grid, QC filtering (what the QC bits mean), 2019–2024 seasonal means, finer layers averaged up to 1 km (never LST down), and the built ≥ 10% urban filter.

**Be ready for these TA questions:**

- Why Aqua, not Terra? Its overpass is closer to peak heat (~13:30).
- Why 1 km? It is the native MODIS LST resolution.
- How did you check the sampling? The pilot reproduction, WorldPop totals checked against a native-grid sum, and value-range checks.
- What gets dropped, and why?
