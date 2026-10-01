# Role 1: Pipeline

Read [README.md](README.md) first. It defines the file formats (§3), the gates (§2) and the shared rules (§4) that this file assumes.

**You own:** `scripts/02_sample_city.py` and `scripts/04_run_all_cities.py`, plus the existing lines of `scripts/config.py`.

**You produce:** `data/samples/*.csv`, `data/results/run_log.csv`, `data/results/b2_checks.csv` and the figure `figures/B_city_map.png`.

**You present:** the **Data** section (datasets, the 303 cities, seasons, quality filtering) and the sampling step of the **Method**. Role 5 presents monsoon availability and water.

**Everyone else is waiting on you.** Do B1 first and announce gate G1 the moment it passes. Then start B2 running in the background. While it runs, do the B2 checks on finished cities and draft your slides. Role 5 (water and data quality) depends on your sample files, so commit partial results regularly.

## Order of work

| Step | Task | Waits on | Unblocks |
| --- | --- | --- | --- |
| 1 | Stage 0 setup | Nothing | Everything |
| 2 | **B1:** extend `02_sample_city.py`, validate | Nothing | **G1** → R3's script 03 test, R4's exposure test, R5's water pilot, your B2 |
| 3 | **B2:** start `04_run_all_cities.py` in the background, and commit samples in batches | G1 | G4 (via R3), F (R4), G for all cities (R5) |
| 4 | B2 checks, final commit, city map, Data slides | B2 done | Final results |

**Earth Engine coordination:** Role 5's monsoon check (M) and Role 2's climate run (C + E) also use the shared quota. Agree in chat who runs when. Never have two big loops running at once. B2 has priority, because everyone waits on it.

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

About every 50 cities (or every couple of hours), commit what exists so R3, R4 and R5 can work on real data:

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

## Step 4: final hand-off and your slides

When B2 is done:

1. Post "B2 complete: N cities sampled, N failed (list)" in chat. R5 then finishes water for all cities, and R3 runs the final 03 (G4) once water is in.
2. Make `figures/B_city_map.png`: the 303 city centres (`lon`, `lat` from the geojson), with points sized by `pop_2025`. Add a light India outline if it is easy: Natural Earth admin-0, downloaded once to `raw/`. Otherwise use points only. Colour the points by `rain_annual_mm` from R2's `city_climate.csv` once it exists. That shows the moisture range in one picture.

**Your slides:**

1. **Data:** a table of the datasets (MODIS LST, MODIS NDVI/EVI, ERA5-Land, GHSL, WorldPop, OSM, SRTM), giving each one's resolution and what it is used for. Copy the IDs from the main README.
2. **Study area:** the city map and the three seasons. Role 5 follows with the monsoon availability figure.
3. **Method, sampling:** a 1 km MODIS grid, QC filtering (what the QC bits mean), 2019–2024 seasonal means, finer layers averaged up to 1 km (never LST down), and the built ≥ 10% urban filter.

**Be ready for these TA questions:**

- Why Aqua, not Terra? Its overpass is closer to peak heat (~13:30).
- Why 1 km? It is the native MODIS LST resolution.
- How did you check the sampling? The pilot reproduction, WorldPop totals checked against a native-grid sum, and value-range checks.
- What gets dropped, and why? Squares with no LST are open water. Squares below 10% built-up are not urban. Cities with fewer than 30 usable squares get no estimate.
