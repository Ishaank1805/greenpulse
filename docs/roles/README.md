# GreenPulse work guide: read this first

This folder tells each of the five team members exactly what to build, in what order, and what to wait for. Read this file, then your own role file:

| Role | File | Owns |
| --- | --- | --- |
| 1. Pipeline | [role_1_pipeline.md](role_1_pipeline.md) | Sampling all cities in 3 seasons (B1, B2), sampling checks, city map |
| 2. Climate | [role_2_climate.md](role_2_climate.md) | City climate and Heat Index (C, E), the main result: cooling vs climate (D) |
| 3. Analysis | [role_3_analysis.md](role_3_analysis.md) | Pilot charts (A), extending script 03 and running it on all cities, seasons (S), robustness (H) |
| 4. Exposure and story | [role_4_exposure_story.md](role_4_exposure_story.md) | Who gets the cooling (F), literature-review accuracy (L), the slide deck (I) |
| 5. Water and data quality | [role_5_water_quality.md](role_5_water_quality.md) | Monsoon data availability (M), OSM water share (G), the water effect |

The approved plan is in [../PLAN.md](../PLAN.md). The pilot facts you need are in §5 below.

---

## 1. The project in five lines

- **Question:** Can existing urban vegetation measurably reduce heat exposure, and under what environmental conditions is the cooling effect strongest?
- **Unit:** the 1 km MODIS square inside each of 303 Indian cities (more than 3 lakh people each, GHS-UCDB outlines).
- **Key number:** the **cooling slope** for each city × season × day/night, from `LST ~ NDVI + built + elev + water`.
  - The slope is the NDVI coefficient. `ce` is in °C per 1.0 NDVI, and `ce_per_0.1` = `ce / 10` is in °C per 0.1 NDVI.
  - **Negative means greener squares are cooler.** Use this sign everywhere, in code, tables and slides.
- **Seasons:**
  - `pre`: Apr–May, hot and dry
  - `post`: Oct–Nov, wet soils after the monsoon
  - `winter`: Dec–Feb, cool and dry
  - The monsoon (Jun–Sep) is excluded because cloud leaves too few usable MODIS pixels. Role 1 measures this and reports it.
- **Explaining the slopes:** the slopes are explained with ERA5-Land climate (one value per city per season), GHSL built-up share and WorldPop population.

**Mid-sem:** a presentation to the TA (no written submission) covering about 50–60% of the project. It has five sections, in order: **Problem → Data → Method → Results → Observations**. Each person presents their own part, and the TA may ask anyone "what did you do, why, and how did you check it?"

**Out of scope for mid-sem:** the perceived-heat scenario (H6), Lorenz curves and building height. Do not start them.

---

## 2. Who waits for whom

There are no dates. Work moves in **stages**. Within a stage, everything runs in parallel. A task moves to the next stage only when the file it needs exists **and has passed its checks**.

```
STAGE 0 (first hour, everyone)
  - clone repo, pip install -r requirements.txt, earthengine authenticate,
    get added to EE project greenpulse-510209 (Himani), run scripts/00_check_setup.py
  - R4 commits scripts/style.py (figure style) — done; see §4 Figures

STAGE 1 (start immediately, no waiting)
  R1  B1  extend 02_sample_city.py: 3 seasons in one pass + elevation; long format;
          validate against pilot v1 CSVs                       ──► GATE G1: "sample format frozen"
  R5  M   monsoon availability (05_monsoon_availability.py)   (independent; agree EE time with R1/R2)
  R5  G   write 06_water_share.py, test OSM download on a city outline
  R2  C+E city climate + Heat Index for all 303 (07_city_climate.py)  ──► GATE G2: city_climate.csv
  R3  A   pilot charts from the EXISTING pilot CSVs (09_pilot_charts.py)
  R3      extend 03_cooling_efficiency.py for seasons + new controls, coding against the
          frozen schema in section 3 (test on R1's B1 output as soon as G1 passes)
  R4  L   literature-review accuracy notes for the slides
  R4  I   slide skeleton: Problem, Data, Method slides drafted
  R4  F   write 12_exposure.py against the schema, test on pilot CSVs

STAGE 2 (after GATE G1)
  R1  B2  run all 303 cities (04_run_all_cities.py), in the background, ~hours
          — results land city by city; others may use partial results
  R5  G   OSM water share for the pilot cities (06_water_share.py) → "G pilot ready"
  R3      run extended 03 on B1's two cities → confirm pre/day/ndvi/built matches pilot
          numbers                                                ──► GATE G3: "03 validated"

STAGE 3 (as B2 progresses — rerun on whatever cities exist; final run when B2 is done)
  R3      run 03 on all sampled cities → data/results/cooling_efficiency.csv
          (final run once B2 is done AND R5 posts "G complete")      ──► GATE G4
  R5  G   water share for all sampled cities → "G complete"; R3 reruns 03 with the water control
  R2  D   main result (needs G2 + G4)       08_main_result.py
  R3  S   seasons (needs G4, and G2 for soil moisture)   10_seasons.py
  R3  H   robustness (needs G4; water variant needs G)   11_robustness.py
  R4  F   exposure on all cities (needs B2 samples only, not 03)   12_exposure.py

STAGE 4 (everything above done)
  R5        water-effect figure (with vs without the water control)
  everyone  write the observation lines for your own results; R4 assembles Results +
            Observations slides; one full rehearsal with each person presenting their part
```

**Soft vs hard waits.** Most waits are soft. Write your code now against the file formats in section 3 and test it on the pilot cities (Jodhpur, Kochi), then rerun when the real files arrive. Only two waits are hard:

1. **G1 (sample format frozen).** Nobody runs anything over all 303 cities until Role 1 says G1 has passed. A format change after B2 would waste the shared Earth Engine quota.
2. **G4 (cooling_efficiency.csv for all cities).** D, S and H need the slopes. While B2 is still running, rerun on the partial set, so the final run is just "press go".

**How to announce a gate:** commit the file to `main`, push, and post one line in the team chat. For example: "G1 passed: data/samples/ is now long format, see docs/roles/README.md §3". If a gate fails, say so in the chat too.

---

## 3. File contracts (frozen formats)

Code against these exactly. If you think a format must change, ask in the chat **before** changing it. The owner of a file is the only person who writes it.

### 3.1 `data/samples/{uc_id}_{slug}.csv`: written by R1 (B1/B2)

One row per **1 km square × season**, in long format. `slug` is the lowercased city name with spaces replaced by `_`, e.g. `5315_jodhpur.csv`, `7963_new_delhi.csv`.

| Column | Type | Meaning |
| --- | --- | --- |
| `city` | str | City name from the geojson |
| `uc_id` | int | GHS-UCDB `ID_UC_G0`. **Join key across all files.** |
| `season` | str | `pre`, `post` or `winter` |
| `cell_id` | str | `f"{lon:.5f}_{lat:.5f}"`, the square-centre coordinates. Stable across seasons. Join key with water. |
| `lon`, `lat` | float | Square centre, EPSG:4326 |
| `lst_day`, `lst_night` | float, °C | Mean QC-filtered MODIS Aqua LST for that season, 2019–2024 (~13:30 / ~01:30) |
| `n_day`, `n_night` | int | Number of 8-day composites that passed QC |
| `ndvi`, `evi` | float, 0–1 | Mean QC-filtered MOD13A1 for that season, averaged to 1 km |
| `built` | float, 0–1 | GHSL 2020 built-up fraction. Same in every season. |
| `pop` | float | WorldPop 2020 people in the square. Same in every season. |
| `elev` | float, m | SRTM mean elevation. Same in every season. |

Rows with missing LST or NDVI are **kept** (as NaN), so missing data can be counted. The built-up threshold (≥ 0.10) is applied in script 03, **not** here.

The original pilot files (April–May only, old one-row-per-square format) are archived in `data/samples/_pilot_v1/` (`jodhpur.csv`, `kochi.csv`). They are used only for validation. Scripts that glob `data/samples/*.csv` will not pick them up, because they sit in a subfolder.

### 3.2 `data/water/{uc_id}_{slug}.csv`: written by R5 (G)

| Column | Meaning |
| --- | --- |
| `uc_id`, `cell_id` | Join keys (same as samples) |
| `water_frac` | 0–1 share of the 1 km square covered by OSM water polygons |

### 3.3 `data/results/cooling_efficiency.csv`: written by R3 (script 03)

One row per city × season × time × index × built_min × control. These columns are the existing ones plus `season`:

`city, uc_id, season, time, index, built_min, control, n, ce, se, ci_lo, ci_hi, p, r2, n_blocks, vi_sd, built_coef, ce_per_0.1`

- `time` is `day` or `night`.
- `index` is `ndvi` or `evi`.
- `built_min` is `0.10` or `0.20`.
- `control` has four values:
  - `none`: LST ~ vi
  - `built`: LST ~ vi + built (the pilot's spec)
  - `built_elev`: LST ~ vi + built + elev
  - `built_elev_water`: LST ~ vi + built + elev + water_frac (only when water exists for that city)
- Rows with `n < 30` have NaN estimates. Keep them so the dropped cities can be listed.
- `ci_lo` and `ci_hi` are 95% intervals with standard errors clustered on ~5 km blocks (already implemented).

**Main specification (use this unless you are doing robustness):** `index = ndvi`, `built_min = 0.10`, and `control = built_elev_water` where it exists, otherwise `built_elev`. To keep this rule in one place, use `main_spec(df)` from `scripts/common.py` (written by R3, see the role 3 file).

### 3.4 `data/results/city_climate.csv`: written by R2 (C+E)

One row per city × season (303 × 3 = 909 rows).

| Column | Unit | Meaning |
| --- | --- | --- |
| `city`, `uc_id`, `season` | | Keys |
| `rain_annual_mm` | mm/yr | Mean annual total, 2019–2024. Same in every season. **The main dryness measure.** |
| `rain_season_mm` | mm | Mean total over the season's months |
| `t2m_c` | °C | Mean 2 m air temperature over the season |
| `t2m_max_c` | °C | Mean daily maximum 2 m temperature |
| `rh_pct` | % | Mean relative humidity, from mean T and dewpoint (Magnus) |
| `swvl1` | m³/m³ | Mean top-layer soil moisture, the second dryness measure |
| `wind10_ms` | m/s | Mean 10 m wind speed, √(u² + v²) |
| `hi_c` | °C | Mean daily-maximum Heat Index (NOAA) |

### 3.5 Other result files

| File | Owner | Content |
| --- | --- | --- |
| `data/results/run_log.csv` | R1 | One row per city attempt: uc_id, city, status (ok/failed/skipped), n_rows, seconds, error |
| `data/results/dropped_cities.csv` | R3 | uc_id, city, season, time, n, reason. These are cities with < 30 usable squares under the main spec. |
| `data/results/lst_availability_by_month.csv` | R5 | city, uc_id, month (1–12), frac_day_ok, frac_night_ok |
| `data/results/main_result_regressions.csv` | R2 | season, time, predictor, slope, ci_lo, ci_hi, p, r2, n_cities |
| `data/results/main_result_bins.csv` | R2 | season, time, rain_group (<1000 / ≥1000, and <750 / 750–1500 / >1500), n_cities, median_ce_per_0.1, share_cooling_sig, share_warming_sig |
| `data/results/b2_checks.csv` | R1 | One row per city: n_squares, expected_squares, flags, missing share per season |
| `data/results/seasons.csv` | R3 | uc_id, city, time, ce_pre, ce_post, ce_winter, d_post_pre, se_d_post_pre, d_winter_pre, se_d_winter_pre |
| `data/results/robustness.csv` | R3 | variant, season, time, n_cities, share_cooling_sig, median_ce_per_0.1, spearman_vs_main, rain_slope, rain_slope_p |
| `data/results/exposure.csv` | R4 | uc_id, city, season, area_lst_day, pop_lst_day, gap_lst_day, area_lst_night, pop_lst_night, gap_lst_night, area_ndvi, pop_ndvi, gap_ndvi, n_cells, pop_total |

---

## 4. Shared conventions

**Scripts and ownership.** Edit only scripts you own. If you need a change in someone else's script, ask them.

| Script | Owner | Task |
| --- | --- | --- |
| `00_check_setup.py`, `01_prepare_cities.py` | R1 | Existing. Do not change. |
| `02_sample_city.py` | R1 | B1 |
| `03_cooling_efficiency.py`, `common.py` | R3 | Extended for seasons and controls |
| `04_run_all_cities.py` | R1 | B2 |
| `05_monsoon_availability.py` | R5 | M |
| `06_water_share.py` | R5 | G |
| `07_city_climate.py` | R2 | C + E |
| `08_main_result.py` | R2 | D |
| `09_pilot_charts.py` | R3 | A |
| `10_seasons.py` | R3 | S |
| `11_robustness.py` | R3 | H |
| `12_exposure.py` | R4 | F |
| `style.py` | R4 | Figure style |

**`scripts/config.py`** is shared. R1 owns the existing lines. Anyone may **add** new constants at the bottom under a comment with their role (e.g. `# --- Role 2 ---`). Never change or delete someone else's constant.

**Earth Engine quota is shared by all five of us** (non-commercial free tier):

- Test on 1–2 cities before any loop.
- Never run two big loops at once.
- Use one `sample()` or `reduceRegion()` per city, not one per square.
- On "Too many concurrent aggregations" or a 429 error, wait and retry with backoff. Do not hammer the server.
- Only R1 (B1, B2), R2 (C+E) and R5 (M, only 6 calls) need Earth Engine at all. R3 and R4 work only from CSVs, and R5's water task uses OpenStreetMap, not Earth Engine. B2 has priority.

**Git:**

- `git pull --rebase` before you start and before you push.
- Make small commits, each with a clear message.
- Commit straight to `main` (five people, separate files, so conflicts are rare).
- Never commit `raw/`, credentials or `.venv/`.
- Results CSVs and figures **are** committed.
- If a push is rejected, pull with rebase, then push again. Never force-push.

**Figures:**

- Save as `figures/{task}_{short_name}.png`, e.g. `figures/A_pilot_scatter.png` or `figures/D_ce_vs_rain.png`, at 200 dpi.
- **style.py is in.** Use it for every figure:
  ```python
  from style import apply_style, save, SEASON_COLORS, DIVERGING, CE_LABEL
  apply_style()
  ...
  save(fig, 'D_ce_vs_rain')   # -> figures/D_ce_vs_rain.png at 200 dpi
  ```
  It also provides `SEASONS`, `SEASON_LABELS`, `DRY_MM` (1000), `DRY_COLOR`, `WET_COLOR` and `MUTED`. Scripts run from `scripts/`, so `import style` works directly.
- Every axis has a label with units.
- Cooling slope axes always read "Cooling slope (°C per 0.1 NDVI); negative = greener is cooler".
- Season colours are fixed: pre = orange, post = blue-green, winter = purple (defined in style.py).

**Checks before you hand anything on.** Every task file lists its checks. The rule from the pilot still applies: compare against a second calculation or a known real-world value. This is how a big population bug was caught earlier.

**Observations file.** `docs/observations.md` is created by R4. Each person writes only under their own `## Role N` heading: one sentence per finding, with numbers and the CSV it came from. R4 turns these into the Observations slide.

**The slide deck.** Role 4 builds and formats the whole deck: [Google Slides](https://docs.google.com/presentation/d/1EnrZBA81aB5Bg3Xh8cWKhd4n5jQbhlmhK1_tqBOnO0I/edit?usp=sharing). Role 4 tells each person which slides they present. **Every role still hands Role 4 three things** once their part is done:

1. **Observation lines** in `docs/observations.md`, under your role's heading: one sentence per finding, with the numbers and the CSV they come from.
2. **Figures** committed to `figures/`, with the names in your role file.
3. **2–3 speaker points per slide**, sent to Role 4. Include the one thing the TA is most likely to question.

You still present your own slides, so check them in the deck before the rehearsal.

**Language on slides.** Results are **associations, not causal effects**. Say "greener squares are cooler", not "vegetation causes X °C cooling".

---

## 5. Verified literature facts (safe to put on slides)

Every number below was checked against the original paper. Use these numbers and do not invent others. If you need a fact that is not here, check the paper itself first.

| Paper | Verified fact |
| --- | --- |
| Bowler et al. 2010 | Meta-analysis: **parks** about **0.94 °C cooler by day** (air temperature). Street trees were not part of the pooled figure. |
| Peng et al. 2012 | MODIS surface UHI in **419** big cities. Mean day 1.5 ± 1.2 °C, night 1.1 ± 0.5 °C. |
| Zhao et al. 2014 | Background climate controls daytime UHI through convection efficiency: +3.0 K in humid climates, −1.5 K in dry ones (North America). Supports albedo management. |
| Manoli et al. 2019 | Greening and albedo are **more efficient in dry regions, but only with irrigation**. Warns about water scarcity. Above ~1000 mm/yr rain, greening alone cannot reach large cooling. |
| Schwaab et al. 2021 | **293** European cities. Treeless green is **2–4×** less cooling than trees. Under hot extremes, trees are 0–4 K cooler than built-up land in **southern** Europe and 8–12 K in **central** Europe. Weaker in the dry south. |
| Venter et al. 2021 | More than 50,000 citizen weather stations, **342** European clusters (2019 heatwave). Satellites overstate UHI about **6×** (surface 1.45 °C vs air 0.26 °C). |
| Du et al. 2024 | 392 European clusters. Tree cooling efficiency is **0.075 °C per 1% tree cover from LST vs 0.006 from air temperature** (~12×). Near zero at night for both. |
| Kim et al. 2024 | **265** air-temperature measurements from **58** studies. Trees cool **2–3×** more than grass or green roofs and walls. |
| Yang et al. 2022 | **510** cities. Tree cooling efficiency 0.063 °C per 1% by day, 0.007 by night (surface). **Higher in hot, dry cities.** |
| Zhou et al. 2017 | Baltimore: tree cover amount matters most. Sacramento (hotter, drier): spatial configuration matters more. |
| Shah et al. 2021 | **Bengaluru**, 262 green spaces (Landsat **surface** temperature). **2.23 °C** cooler, effect reaches **347 m**. |
| Ibsen et al. 2021 | 8 US cities, air temperature. **Night** vegetation cooling rises with aridity: **1.4 °C Miami → 5.6 °C Las Vegas**. |
| Meili et al. 2021 | Model (Phoenix, Singapore, Melbourne, Zurich). Separates tree shading, evapotranspiration (ET) and roughness effects. Tree ET lowers air temperature by at most 3.1–5.8 °C. Radiation trapping can warm by up to 1.6–2.1 °C at some hours. |
| Guo et al. 2026 | **761** megacities. Cooling weakens with aridity. In **22%** of cities under 1000 mm/yr, vegetation causes **net warming** (mostly grass and cropland), because albedo and heat-storage effects outweigh limited ET. Under extreme heat, trees fail to cool **25%** of cities (grass 71%, cropland 82%). |
| Borah et al. 2026 | **138 Indian cities**, pre-monsoon midday, machine-learning **associations**. Dense structure (EVI ≥ 0.4) goes with a lower Heat Index. High canopy activity (fPAR ≥ 0.5) goes with a **higher** Heat Index, starting earlier in humid cores. |
| Chakraborty et al. 2019 | **25** cities. Poorer neighbourhoods are hotter in **72%** (surface UHI). Vegetation is the strongest driver. |
| Chen et al. 2022 | Global South greenspace exposure is **one-third** of the North's. Inequality is about 2× higher (Gini 0.47 vs 0.27). |
| Li et al. 2024 | About 500 cities. The Global South has **~70%** of the North's green cooling capacity (2.5 vs 3.6 °C). |
| Iungman et al. 2023 | **93** European cities (2015). 30% tree cover would cool by 0.4 °C and avoid **2,644 deaths** (~1/3 of UHI-attributable deaths). |
| Kumar et al. 2017 | India-wide MODIS UHI study. **Excluded Jun–Sep** for cloud. This supports our monsoon exclusion. |

**The open question we test:** in dry climates the literature disagrees. Guo and Schwaab find weaker cooling. Manoli (with irrigation) and Yang find stronger cooling. India spans the whole range from Jodhpur (~350 mm/yr) to Kochi (~3,000 mm/yr).

**Hypotheses (from PLAN.md):**
- **H1:** greener squares are cooler by day in most cities.
- **H2:** the cooling slope changes with background moisture (direction tested).
- **H3:** night cooling is weaker and may reverse in dry cities.
- **H4:** the slope differs between seasons in the same city.
- **H5:** crowded squares get less cooling, so people-weighted heat is higher than area-weighted heat.
- **H6** (after mid-sem): converting surface cooling into felt heat shrinks the benefit most in humid cities.

**Pilot facts (Apr–May, NDVI, built ≥ 0.10, built control):**
- **Jodhpur:** −1.32 °C per 0.1 NDVI by day (95% range −1.98 to −0.67).
- **Kochi:** −1.04 °C per 0.1 NDVI by day (95% range −1.57 to −0.51).
- **Jodhpur at night:** +0.62, so greener squares are warmer. This shows only once built-up share is controlled.
- **Kochi with EVI:** the daytime cooling largely disappears, because NDVI and built-up share are tightly correlated there (r = −0.79).
