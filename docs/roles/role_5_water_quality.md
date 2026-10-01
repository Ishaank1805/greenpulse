# Role 5: Water and data quality

Read [README.md](README.md) first. It defines the file formats (§3), the gates (§2) and the shared rules (§4) that this file assumes.

**You own:** `scripts/05_monsoon_availability.py` and `scripts/06_water_share.py`.

**You produce:** `data/results/lst_availability_by_month.csv`, `data/water/*.csv`, and the figures `figures/M_lst_availability.png` and `figures/G_water_effect.png`.

**You present:**
- **Why there is no monsoon season**, on the Data slides, right after Role 1's study-area slide.
- **Whether water explains part of the vegetation effect**, a Results slide. The key question is whether it explains Jodhpur's warm green nights.

**Who depends on you:** Role 3's final run of script 03 (gate G4) waits for your "G complete". Do the water pilot as soon as gate G1 passes, so Role 3 can test the water control early.

## Order of work

| Step | Task | Waits on | Unblocks |
| --- | --- | --- | --- |
| 1 | Stage 0 setup, **including** `earthengine authenticate` (M uses Earth Engine) | Nothing | |
| 2 | **M:** monsoon availability | Nothing. Agree a time with R1 and R2 for the quota. | Data slide |
| 3 | **G (code):** write `06_water_share.py`, and test the OSM download and overlap on Jodhpur's **outline** from the geojson | Nothing | |
| 3b | **G (pilot):** water share for Jodhpur and Kochi, using the new sample files | **G1** (R1) | R3 tests the water control |
| 4 | **G (all):** water share for every sampled city, as B2 progresses | B2 sample files (R1) | **"G complete"** → R3's final 03 run (G4) |
| 5 | Water effect figure, observation lines, slides | R3's 03 runs with and without water | |

G does **not** use Earth Engine (OpenStreetMap comes from the Overpass API), so it never competes with B2 for quota. Only M does, and it is just 6 calls.

---

## Step 1: Stage 0 setup

Follow [role_1_pipeline.md](role_1_pipeline.md#step-1-stage-0-setup): clone, venv, `pip install -r requirements.txt`, `earthengine authenticate`, then `python scripts/00_check_setup.py`.

---

## Step 2, M: monsoon availability (`05_monsoon_availability.py`)

**Why:** we exclude June–September. The TA will ask "why no monsoon?", so we show the data limitation instead of just asserting it.

- **Cities:** Jodhpur (5315), New Delhi (7963), Hyderabad (9524), Mumbai (7599), Kolkata (11352), Kochi (9386).
- **For each city and each calendar month 1–12, over 2019–2024:**
  - `frac_day_ok` = mean over the city's squares of (QC-passing composites in that month ÷ all composites in that month).
  - `frac_night_ok` is the same, for night.
  - Use exactly the same QC rule as `02_sample_city.py`: keep QC bits 0–1 = 0, or bits 0–1 = 1 with bits 6–7 ≤ 1. Copy those few lines with a comment pointing to `02_sample_city.py`, and do not change them. That file is Role 1's, and you don't need to wait for it.
- **Efficiency:** build one multi-band image per city (24 bands: 12 months × day/night) and run **one** `reduceRegion(mean, scale=1000)` per city. That is 6 calls in total.
- **Output:** `data/results/lst_availability_by_month.csv` (README §3.5).
- **Figure:** `figures/M_lst_availability.png`. Draw one line per city, with month on the x axis and the fraction of usable composites (0–1) on the y axis. Shade June–September. Use separate panels for day and night.
- **Checks:**
  - [ ] Jun–Sep is clearly lower than Apr–May in every city, and lowest in Mumbai and Kochi. If it isn't, re-check the mask.
  - [ ] **Cross-check against Role 1's samples.** For Jodhpur, the April and May usable fractions × the number of composites in those months should be close to the median `n_day` in `data/samples/_pilot_v1/jodhpur.csv` (41). The file is at `data/samples/jodhpur.csv` until R1 moves it. A big mismatch means the mask differs from `02_sample_city.py`.
- **Slide line (fill in the numbers):** "In June–September only about X% of 8-day composites are usable in Mumbai, versus Y% in April–May, so we compare pre-monsoon, post-monsoon and winter (as Kumar et al. 2017 did)."

---

## Steps 3–4, G: OSM water share (`06_water_share.py`)

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
5. **Output:** `data/water/{uc_id}_{slug}.csv` (create `data/water/` if needed) with `uc_id, cell_id, water_frac`, including squares where the share is 0.
6. **Pace:** for the all-city run, sleep 1–2 s between cities and skip cities that are already done, as in B2. Log failures.

### Order

- **First do Jodhpur and Kochi**, as soon as R1 announces G1, since you need the new pilot sample files for `cell_id`. Commit them and tell R3 ("G pilot ready"). R3 then tests the `built_elev_water` control.
- Then run all cities. Work through whatever sample files R1 has committed (`git pull --rebase` first), skipping cities already done, and rerun at the end. When every sampled city has a water file, post "**G complete**". R3's final script-03 run waits for this.

### Checks

- [ ] **Kochi.** The pilot sample has 185 squares with no LST, which are open water. Most of those should have `water_frac > 0.5`. Report how many do.
- [ ] **Low NDVI over water.** For squares with `water_frac > 0.5` that do have LST, pre-season NDVI should mostly be below 0.2. Report the median.
- [ ] **Small water share in dry cities.** Jodhpur should have only a few squares with any water: a handful of lakes and tanks.
- [ ] **Sea is a known gap.** In OSM the sea is a coastline line, not a water polygon. Coastal squares that are partly sea get `water_frac` ≈ 0. Most such squares are below 10% built-up and are excluded anyway. Count the coastal squares that have built ≥ 0.10 and NaN LST, and note this as a limitation.

---

## Step 5: water effect, observations and slides

When R3 has run script 03 with and without the water control (for the pilot first, then all cities), make **`figures/G_water_effect.png`**:

- Plot each city's pre-monsoon cooling slope **with** the water control (`built_elev_water`) against the slope **without** it (`built_elev`), with day and night as separate panels.
- Add the 1:1 line and label Jodhpur and Kochi.
- Points far from the line are cities where water was hiding or faking part of the vegetation effect.

Write one sentence each, with numbers, under `## Role 5 (water and data quality)` in `docs/observations.md`:

- **Monsoon:** "In June–September only X% of composites are usable in Mumbai (Y% in April–May)."
- **Water:** "Controlling for water share changes the median daytime slope from X to Y. Jodhpur's warm green nights [remain / disappear] (night slope X → Y)."
- **Data limit:** the number of coastal squares where the sea is not counted as water.

**Your slides:**

1. **Data, why no monsoon:** `M_lst_availability.png` and the one-line finding.
2. **Result, water:** `G_water_effect.png`, with one line on Jodhpur's nights.

**Be ready for these TA questions:**

- Why OSM and not a satellite water map? OSM is one of the assigned datasets, and it maps small tanks and lakes.
- How is water share computed? By overlaying OSM polygons on the true MODIS square footprint, in the sinusoidal projection.
- What about the sea? It is a known gap. Most partly-sea squares fall below the 10% built-up cut-off anyway.
- Why does water matter for a vegetation study? It is cool by day and warm at night, like vegetation, so it could be confused with it.
