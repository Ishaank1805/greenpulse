# Role 2: Climate and main result

Read [README.md](README.md) first. It defines the file formats (§3), the gates (§2) and the shared rules (§4) that this file assumes.

**You own:** `scripts/07_city_climate.py` and `scripts/08_main_result.py`.

**You produce:**
- `data/results/city_climate.csv`
- `data/results/main_result_regressions.csv`
- `data/results/main_result_bins.csv`
- the figures `figures/C_climate_overview.png`, `figures/D_ce_vs_rain.png`, `figures/D_ce_vs_humidity.png` and `figures/D_ce_map_pre_day.png`, plus the other season/time maps

**You present:** the climate part of **Data** and **Method** (ERA5-Land as a city-level condition, and the Heat Index), and the **main Result**: under what conditions cooling is strongest. This is the answer to the second half of the research question, so it is the most important slide in the deck.

## Order of work

| Step | Task | Waits on | Unblocks |
| --- | --- | --- | --- |
| 1 | Stage 0 setup | Nothing | Everything |
| 2 | **C + E:** `07_city_climate.py` for all 303 cities × 3 seasons | Nothing. Needs only `data/cities/india_cities.geojson`. | **G2** → your D, R3's S, R1's city-map colours |
| 3 | Write `08_main_result.py` and test it on the pilot | G2 (your own). Uses the pilot `cooling_efficiency.csv` for the code test. | |
| 4 | **D (partial):** rerun on whatever cities R3 has fitted | G2 + partial G4 | Early look at the pattern |
| 5 | **D (final):** run on the final `cooling_efficiency.csv` | **G4** (R3), ideally with the water control done | Results slides |
| 6 | Write the observation lines and your slides | Step 5 | |

**Earth Engine coordination.** Role 1's B2 is also using the shared quota. Tell R1 in chat before you start your full 303-city run. Run one city at a time with a 1 s sleep. If you hit "Too many concurrent aggregations" or a 429 error, back off for 60 s and retry (3 attempts). Test on Jodhpur and Kochi first.

---

## Step 1: Stage 0 setup

Follow the steps in [role_1_pipeline.md](role_1_pipeline.md#step-1-stage-0-setup): clone, venv, `pip install -r requirements.txt`, `earthengine authenticate`, then `python scripts/00_check_setup.py`.

---

## Step 2, C + E: city climate and Heat Index (`07_city_climate.py`)

**Output:** `data/results/city_climate.csv`, with 909 rows (303 cities × 3 seasons) and the columns exactly as in README §3.4.

**Seasons:** use `C.SEASONS` from `config.py`: pre = [4, 5], post = [10, 11], winter = [12, 1, 2].
- If R1 has not added it yet, add `SEASONS` yourself under a `# --- Role 2 ---` comment, and tell R1.
- Build the month filter with `ee.Filter.Or(*[ee.Filter.calendarRange(m, m, 'month') for m in months])`, the same way R1 does.

**Years:** 2019-01-01 to 2025-01-01 (end exclusive). Use `C.START` and `C.END`.

**Why one value per city:** ERA5-Land is ~9 km (0.1°), coarser than our 1 km squares. It cannot tell one neighbourhood from another, so it describes the **background climate a city sits in**. Say this on the slides. It is a deliberate design choice, not a weakness we are hiding.

### 2a. Monthly variables (`ECMWF/ERA5_LAND/MONTHLY_AGGR`)

For each city, reduce over the city polygon with `reduceRegion(ee.Reducer.mean(), geometry, scale=1000)`.
- `scale=1000` lets Earth Engine area-weight the 9 km cells over even small city polygons.
- If the result is null (a tiny or coastal polygon that misses all land cells), retry on `polygon.centroid().buffer(10000)` and note it in a `fallback` print.

Pull each month as a feature, which gives 72 per city. Use `collection.map(lambda img: ee.Feature(None, img.reduceRegion(...)).set('month', img.date().get('month')))`, then one `getInfo()` per city. Then in pandas:

| Column | Formula |
| --- | --- |
| `rain_annual_mm` | Mean over all 72 months of `total_precipitation_sum` (m) × 12 × 1000 |
| `rain_season_mm` | Mean over that season's months × the number of months in the season × 1000 |
| `t2m_c` | Mean `temperature_2m` over the season's months, − 273.15 |
| `rh_pct` | Per month, Magnus from monthly mean T and Td (in °C), then the mean over the season's months |
| `swvl1` | Mean `volumetric_soil_water_layer_1` over the season's months |
| `wind10_ms` | Per month √(u² + v²) of `u_component_of_wind_10m` and `v_component_of_wind_10m`, then the mean. Label it "approximate (from monthly mean components)" because it is a secondary variable. |

The Magnus formula, with T and Td in °C:

```
RH = 100 * exp(17.625*Td/(243.04+Td)) / exp(17.625*T/(243.04+T))
```

**Known ERA5-Land quirks (from our verification):**
- **Evaporation sign:** evaporation and potential evaporation are **negative** by ECMWF convention.
- **Potential evaporation is unreliable in arid areas.** So we do **not** use an aridity index of rain ÷ potential evaporation. Rainfall is the dryness measure, and soil moisture is the second one.
- **Odd precipitation months:** precipitation can rarely be slightly negative because of packing. Clip monthly values at 0 before summing.

### 2b. Daily maximum temperature and Heat Index (`ECMWF/ERA5_LAND/DAILY_AGGR`)

The Heat Index must come from daily values. A Heat Index computed from a monthly mean temperature understates the hot afternoons.

1. Filter `DAILY_AGGR` to the season months and 2019–2024. That gives about 366 days for pre, 366 for post and 540 for winter.
2. Select the bands `temperature_2m_max` and `dewpoint_temperature_2m`. Reduce each day over the city with the same reducer, so you get one feature per day.
   - That is about 1,270 features per city in total, under the 5,000 `getInfo` limit.
   - Do one call per city per season if that is simpler.
3. In pandas, for each day:
   - T = `temperature_2m_max` in °C, and Td = the daily mean dewpoint in °C.
   - Compute RH with Magnus.
   - This approximates the humidity at the hottest hour, because dewpoint changes slowly over a day. State the approximation in your method slide.
4. Compute the Heat Index with the **NOAA algorithm** (https://www.wpc.ncep.noaa.gov/html/heatindex_equation.shtml). Work in **°F**, then convert back to °C.

```python
def heat_index_f(T, RH):            # T in °F, RH in %
    simple = 0.5 * (T + 61.0 + (T - 68.0) * 1.2 + RH * 0.094)
    if (simple + T) / 2 < 80:
        return simple
    HI = (-42.379 + 2.04901523*T + 10.14333127*RH - 0.22475541*T*RH
          - 0.00683783*T*T - 0.05481717*RH*RH + 0.00122874*T*T*RH
          + 0.00085282*T*RH*RH - 0.00000199*T*T*RH*RH)
    if RH < 13 and 80 <= T <= 112:
        HI -= ((13 - RH) / 4) * ((17 - abs(T - 95)) / 17) ** 0.5
    elif RH > 85 and 80 <= T <= 87:
        HI += ((RH - 85) / 10) * ((87 - T) / 5)
    return HI
```

Vectorise it with numpy (`np.where`) for speed. Most winter days fall below 80 °F, which is why the simple formula branch matters.

5. `t2m_max_c` is the mean of the daily T over the season, and `hi_c` is the mean of the daily Heat Index over the season, in °C.

### 2c. Checks (all must pass before G2)

- [ ] **Heat Index unit tests.** Add these as `assert`s in the script:
  - `heat_index_f(90, 50)` is about **95 °F**. NOAA's table gives 95, so accept 94–96.
  - `heat_index_f(70, 50)` is close to 70 °F (the simple branch).
  - Our function and NOAA's online calculator agree within 1 °F at T = 100 °F, RH = 40%.
- [ ] **Rainfall.** Jodhpur `rain_annual_mm` is roughly **300–450**, and Kochi roughly **2,500–3,500**. ERA5 can underestimate coastal rain, so if Kochi comes out at 2,000–2,500, accept it and note it. If either is badly off, check the ×1000 conversion and the ×12 step.
- [ ] **Temperature.** Pre-monsoon `t2m_c`: Jodhpur about 32–36 °C, Kochi about 28–30 °C. Winter is cooler than pre-monsoon in every city.
- [ ] **Humidity.** Pre-monsoon `rh_pct`: Kochi about 70–85%, Jodhpur about 20–40%.
- [ ] **Soil moisture.** Post-monsoon `swvl1` is higher than pre-monsoon `swvl1` in at least 80% of cities. Wet soils after the monsoon are the whole point of the season comparison.
- [ ] **Heat Index vs temperature.** In humid coastal cities (Kochi, Chennai, Mumbai, Kolkata), pre-monsoon `hi_c` is clearly **above** `t2m_max_c`. In Jodhpur it is close to it.
- [ ] **Completeness.** There are no NaNs in the 909 rows. List any fallback cities.

### 2d. Announce G2

Commit `scripts/07_city_climate.py` and `data/results/city_climate.csv`, then push. Post: "**G2 passed:** city_climate.csv, 909 rows, checks OK (Jodhpur X mm, Kochi Y mm)".

Also make `figures/C_climate_overview.png`: a scatter of the 303 cities with `rain_annual_mm` (log x) against pre-monsoon `rh_pct`, coloured by pre-monsoon `t2m_c`. This shows the climate range we cover, and it goes on the Data slide.

---

## Steps 3–5, D: the main result (`08_main_result.py`)

**Question answered:** under what environmental conditions is the cooling slope strongest? This tests H2 and H3.

### Inputs

- `data/results/cooling_efficiency.csv`, written by R3. Filter it to the **main specification** with `from common import main_spec` (README §3.3).
  - If `common.py` does not exist yet, filter inline: `index == 'ndvi'`, `built_min == 0.10`, and `control == 'built_elev_water'` where it exists for that city × season × time, else `built_elev`, else `built` for the pilot file. Switch to `main_spec` once R3 commits it.
- Drop rows where `ce` is NaN (fewer than 30 squares).
- `data/results/city_climate.csv`. Join on `uc_id` and `season`.
- **City built-up density:**
  - From `data/samples/*.csv`, take each city's `pre` rows with `built >= 0.10`.
  - Compute `built_mean` (mean built share) and `n_cells`.
  - Join on `uc_id`.

### Analysis

All of this is done separately for each **season × time (day/night)**, which gives 6 panels.

- **Response:** `ce_per_0.1`, with standard error `se / 10`. Negative means greener squares are cooler.
- **Single-predictor regressions:**
  - **Rainfall:** `ce_per_0.1 ~ log10(rain_annual_mm)`. This is the headline.
  - **Others, one at a time:** `rh_pct`, `swvl1`, `t2m_c`, `hi_c`, `built_mean`.
  - **Weighting:** use WLS with weights `1 / se_per_0.1**2`, with robust (HC3) standard errors.
  - Also fit unweighted OLS as a check. If the two disagree in sign, report both and say so.
- **Multiple regression (one per panel):** `ce_per_0.1 ~ log10(rain_annual_mm) + t2m_c + built_mean`. This separates dryness from heat and density.
- **Write** all coefficients to `data/results/main_result_regressions.csv`, with the columns `season, time, predictor, slope, ci_lo, ci_hi, p, r2, n_cities` (README §3.5). For the multiple regression, write one row per predictor and set `predictor` to e.g. `multi:log10_rain`.
- **Threshold test (links us straight to Guo and Manoli, who both use ~1000 mm):**
  - Split the cities into **< 1000 mm** and **≥ 1000 mm** of annual rain.
  - For each group, report the number of cities, the median `ce_per_0.1`, the share with a significant cooling slope (`ci_hi < 0`), and the share with a **positive** slope (`ci_lo > 0`, greener is warmer).
  - Guo found net warming in 22% of cities under 1000 mm, so compare our share with that.
  - Also give three rainfall bins (< 750, 750–1500, > 1500 mm) for the figure.
  - Write the results to `data/results/main_result_bins.csv`.

### Figures

1. **`figures/D_ce_vs_rain.png` (the headline figure).**
   - Layout: 2 rows (day, night) × 3 columns (pre, post, winter).
   - X axis: annual rainfall on a log scale. Y axis: `ce_per_0.1`.
   - Draw one point per city, with thin 95% error bars at low alpha.
   - Add the WLS fit line with its confidence band, a horizontal line at 0 and a dashed vertical line at 1000 mm.
   - Label Jodhpur, Kochi, New Delhi, Mumbai, Hyderabad and Bengaluru.
   - The y label reads "Cooling slope (°C per 0.1 NDVI); negative = greener is cooler".
2. **`figures/D_ce_vs_humidity.png`.** The same layout, with `rh_pct` on the x axis.
3. **`figures/D_ce_map_pre_day.png` (and one per season × time).**
   - Plot the city centres (`lon`, `lat` from the geojson), coloured by `ce_per_0.1`.
   - Use a **diverging** colour map centred on 0 (`DIVERGING` from `style.py`), with blue for cooling and red for warming.
   - Size the points by population.
   - Use hollow markers for cities whose 95% interval crosses 0.
   - Add a light India outline if R1 has one in `raw/`; otherwise use points only.

### Checks

- [ ] **Pilot numbers.** Jodhpur and Kochi, pre/day, match R3's numbers in `cooling_efficiency.csv` (about −1.3 and −1.0 at the pilot spec).
- [ ] **Number of cities.** Report `n_cities` in every panel. If one season has far fewer (post-monsoon cloud), say so.
- [ ] **No single city drives the slope.** Do a leave-one-out on the rainfall slope (pre/day). Report the largest change, and if dropping one city flips the sign, report that city.
- [ ] **No extreme weights.** Check that no city carries more than 10% of the total WLS weight. If one does, report the fit with weights capped at the 95th percentile as well.
- [ ] **Sanity of the direction.** Look at the 5 most negative and 5 most positive cities by `ce_per_0.1` and check that they are not all tiny cities with n near 30.

### Partial runs

While B2 and the script-03 runs are still in progress, rerun `08_main_result.py` whenever R3 commits a new `cooling_efficiency.csv`. Write the script so the final run is the same command. Post the early pattern in chat, e.g. "with 120 cities, pre/day slope vs log rain = X", so R4 can draft the Observations.

---

## Step 6: observations and slides

Write one sentence each, with numbers, in `docs/observations.md` under a `## Role 2` heading. R4 collects them.

- **H2:** "Across N cities, the daytime cooling slope [strengthens / weakens / shows no clear trend] with annual rainfall (slope X per 10× rain, 95% CI …)." Then say which papers this agrees with, from the README §5 table. Guo and Schwaab predict weaker cooling in dry climates; Manoli (with irrigation) and Yang predict stronger cooling.
- **Threshold:** "In cities under 1000 mm, X% show greener-is-warmer slopes (Guo et al. found 22% net warming)."
- **H3:** "At night, the slope is [weaker / reversed] in [dry / all] cities."
- **Season contrast:** one line on whether the rainfall pattern is the same in all three seasons. R3 does the within-city test.
- **Limits:** state that ERA5 is a city-level condition, that rainfall does not capture irrigation (Manoli), and that these are associations.

"No clear pattern" is a valid result if it comes with a confidence interval.

**Your slides:**

1. **Method, climate:** ERA5-Land variables, why one value per city (9 km), the daily Heat Index with the NOAA formula, and why rainfall and not P/PET (unreliable in arid areas).
2. **Result, the headline:** `D_ce_vs_rain.png` (or its pre/day panel enlarged), with the slope and CI written on it.
3. **Result, map:** `D_ce_map_pre_day.png`.
4. **Result, threshold:** a small table of < 1000 mm vs ≥ 1000 mm against Guo's 22%.

**Be ready for these TA questions:**

- Why log rainfall? Rainfall spans 10×, from ~350 to ~3,000 mm.
- Why weight by 1/SE²? Precise slopes should count more.
- Couldn't the pattern be city size? We checked `built_mean` in the multiple regression, and city size is in `n_cells`, so try adding it as a check.
- Why surface temperature, not air temperature? It is the only 1 km temperature available for all cities, and our review notes it overstates cooling (Venter: ~6× for the urban heat island; Du: ~12× for tree cooling efficiency).
