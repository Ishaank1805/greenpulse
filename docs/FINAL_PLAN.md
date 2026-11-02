# Final submission plan

Final presentation: **25 minutes + 5 minutes of questions.** Everything here builds on the mid-eval results, which stay as they are. In particular, **the main model (NDVI, built ≥ 10%, built + elevation + water) does not change.** The new analyses add to the results; they do not redo them, so no mid-eval number needs re-checking.

Read [roles/README.md](roles/README.md) first for file formats, conventions and the verified literature facts.

---

## 1. H6: the heat people actually feel

**Hypothesis (from PLAN.md):** translating surface cooling into felt heat shrinks the benefit most in humid cities.

**Why it matters:** our results are in surface temperature (LST), and the literature warns that LST overstates what people feel. Venter et al. 2021 found satellites overstate the urban heat island about 6×. Du et al. 2024 found tree cooling efficiency about 12× higher in LST than in air temperature. Borah et al. 2026 found that dense canopies in humid Indian cities go with a *higher* Heat Index. H6 asks what our cooling slopes mean for felt heat, city by city.

**This is a scenario, not a measurement.** Say so on every slide. We have no air temperature or humidity data at 1 km. We combine our measured surface cooling slopes with published surface-to-air ratios and each city's ERA5 daily climate.

### Method

1. **Start from the main-spec daytime cooling slope** for each city and season (`cooling_efficiency.csv` via `common.main_spec`, `time = day`). Use pre-monsoon as the main season, and post-monsoon as a second. Skip winter: most winter days are below 80 °F, where the Heat Index equals air temperature by construction.
2. **Choose a greening step.**
   - **Main:** +0.1 NDVI, the same unit as our slopes.
   - **Realistic contrast:** each city's own spread of greenness. Use the 25th to 75th percentile of NDVI across its urban squares (from `data/samples/`, `pre` rows), so each city gets a "typical green vs typical bare" difference.
3. **Convert surface cooling to air cooling:** ΔT_air = ΔLST × r.
   - **Main ratio:** r = 0.08 (Du et al. 2024: 0.006 ÷ 0.075). This is the closest analogue, because it is specifically tree cooling efficiency, air against surface.
   - **Upper bound:** r = 0.18 (Venter et al. 2021: 0.26 ÷ 1.45 °C, for the urban heat island).
   - Report both as a range. Both ratios come from European cities, which is a stated limitation.
4. **Recompute the daily Heat Index** using each city's ERA5-Land daily maximum temperature and dewpoint, for every day in the season, 2019–2024. Use the same NOAA formula as `07_city_climate.py` (import it; do not copy it).
   - **Baseline:** HI(T_max, dewpoint).
   - **Scenario A, cooling only:** HI(T_max + ΔT_air, same dewpoint). Holding the dewpoint fixed keeps the air's moisture fixed, so relative humidity rises a little as the air cools. This is physically right, and part of why felt cooling is smaller than air cooling.
   - **Scenario B, cooling plus extra moisture from leaves:** the same, but with the dewpoint raised by δ = +0.5, +1 and +2 °C.
   - **ΔHI** = mean over days of (scenario − baseline), in °C.
5. **Break-even humidity.** For each city, find the dewpoint increase δ* at which ΔHI reaches 0, meaning greening no longer lowers felt heat. Solve numerically: δ from 0 to 5 °C in 0.05 steps. A small δ* means the felt benefit is fragile, which H6 predicts for humid cities.
6. **Test H6.**
   - **Felt-heat efficiency per city:** ΔHI ÷ ΔT_air. It is about 1 in dry air and below 1 in humid air under scenario A.
   - **Compare across cities:** Spearman correlation of efficiency and δ* with pre-monsoon `rh_pct`, plus a < 1,000 vs ≥ 1,000 mm comparison and the same WLS approach as the main result.
   - **Supported if:** humid cities have clearly lower efficiency and lower δ*.

### Outputs

| File | Content |
| --- | --- |
| `data/results/city_daily_climate.csv` | uc_id, city, season, date, t2m_max_c, td_c (export from the ERA5 cache) |
| `data/results/felt_heat.csv` | uc_id, city, season, step (`ndvi_0.1` / `iqr`), r, delta_td, d_lst, d_tair, d_hi, hi_efficiency, delta_star |
| `figures/H6_felt_vs_surface.png` | For each city, surface cooling against felt (Heat Index) cooling, coloured by humidity |
| `figures/H6_breakeven.png` | Break-even dewpoint rise δ* against pre-monsoon humidity, one dot per city |

### Checks

- [ ] **Zero inputs give zero change:** with ΔT_air = 0 and δ = 0, ΔHI is exactly 0 for every city.
- [ ] **Dry cities:** in Jodhpur (pre-monsoon RH ~25–35%), scenario-A ΔHI is close to ΔT_air, because the Heat Index ≈ air temperature in dry air.
- [ ] **Humid cities:** in Kochi, Chennai and Kolkata, ΔHI is smaller than ΔT_air, and δ* is smaller than in Jodhpur.
- [ ] **Sign:** greener (negative slope) gives negative ΔT_air and, under scenario A, negative ΔHI.
- [ ] **Sanity bound:** no city's ΔT_air exceeds the 3.1–5.8 °C maximum tree cooling of air modelled by Meili et al. 2021. With r = 0.08 it should be tenths of a degree.
- [ ] **Re-derivation:** the baseline mean HI per city and season reproduces `hi_c` in `city_climate.csv` to within 0.05 °C.

### What not to claim

- Not "greening raises felt heat in Kochi". The claim is: "under plausible surface-to-air ratios, the felt benefit is smaller in humid cities and disappears if leaves add about X °C of dewpoint."
- Not an air-temperature measurement. It is a scenario built from measured surface slopes and published ratios.

---

## 2. Other new analyses

**Building height (urban form).**
- Add GHSL building height (2018, `JRC/GHSL/P2023A/GHS_BUILT_H`) to the samples as a static `height` column, using one Earth Engine pass per city.
- **Do not change the main model.** Instead:
  - Re-estimate the cooling slope within building-height terciles (low, mid, tall) for each city and season.
  - Add `height` as an extra robustness control.
- **Question:** do tall, dense areas get less cooling from the same greenness?

**Who receives the cooling (Lorenz curve).**
- For each city, rank urban squares from least to most green. Plot the cumulative share of people against the cumulative share of greenness (NDVI), and compute a Gini coefficient.
- Do the same for "cooling received" = −slope × (square NDVI − city 10th-percentile NDVI) × 10.
- Report the median Gini across cities, and the 5 most and least unequal cities.
- Compare with Chen et al. 2022 (Gini 0.47 South vs 0.27 North), but **note that their Gini measures greenspace exposure across cities worldwide, not the same thing.**

**Seasonal "more sun" idea (explaining H4).**
- Add ERA5-Land `surface_solar_radiation_downwards_sum` per city and season.
- Test whether the post-minus-pre change in cooling slope tracks the change in solar radiation, in the same way the soil-moisture test was done.

**Hyderabad case study (Prajna).**
- Landsat 8/9 surface temperature at 30 m (`LANDSAT/LC08/C02/T1_L2`, `LANDSAT/LC09/C02/T1_L2`, band ST_B10), pre-monsoon, clear scenes 2019–2024.
- **Park-edge cooling distance:** temperature in rings out to 1 km from OSM parks larger than 5 ha. Compare with Shah et al. 2021 (Bengaluru: 2.23 °C, 347 m).
- **Main point:** what 1 km MODIS squares cannot see.

---

## 3. Tasks and owners

**Hard gates (G for gate):**
- **G-H6a:** `city_daily_climate.csv` exists. H6 waits on this.
- **G-H:** the `height` column exists in all samples. The height analysis waits on this.
- **G-S:** solar radiation is in `city_climate.csv`. The sun test waits on this.

Everything else can start at once.

| # | Task | Owner | Waits on | Size | Output |
| --- | --- | --- | --- | --- | --- |
| 1 | Export daily ERA5 (T max, dewpoint) from the local cache to `city_daily_climate.csv`. Only if the cache is gone, re-fetch: 303 calls, agree a time for the shared quota. | **Ishaan** | — | S | G-H6a |
| 2 | H6 script `15_felt_heat.py`: scenarios A and B, both steps, both ratios, break-even δ*, checks, figures | **Ishaan** | 1 | L | `felt_heat.csv`, H6 figures |
| 3 | H6 test: efficiency and δ* against humidity and rainfall, write-up lines | **Ishaan** | 2 | M | observations |
| 4 | Add `height` (GHSL 2018) to all sample files in one Earth Engine pass. Re-check that the pilot rows are unchanged. | **Himani** | — | M | G-H |
| 5 | Add solar radiation per city and season (monthly ERA5-Land, 303 calls), coordinated with Ishaan's `city_climate.csv` | **Himani** | — | S | G-S |
| 6 | Cooling slope by building-height tercile, plus height as a robustness control | **Johar** | 4 | M | `height_effect.csv`, figure |
| 7 | "More sun" test for the seasonal change (H4) | **Johar** | 5 | S | lines in `seasons_summary.csv`, figure |
| 8 | Lorenz curves and Gini for greenness and for cooling received | **Prajna** | — (samples and slopes exist) | M | `lorenz.csv`, figure |
| 9 | Hyderabad Landsat case study: scene selection, park rings, comparison with Shah 2021 | **Prajna** | — | L | `hyderabad_parks.csv`, figure |
| 10 | Water-and-data-quality check on the new analyses: do H6 and height results hold without water squares and in cities with ≥ 10 blocks? | **Nidhi** | 2, 6 | S | robustness lines |
| 11 | Final deck (about 25 slides) and speaker script | **Nidhi** | all | L | deck, script |
| 12 | Each person writes their observation lines in `docs/observations.md` and sends 2–3 speaker points to Nidhi | **Everyone** | own tasks | S | — |
| 13 | Rehearsal, timed to 25 minutes | **Everyone** | 11 | — | — |

**Order of work:**

```
NOW (parallel): 1 (Ishaan) · 4, 5 (Himani) · 8, 9 (Prajna) · 11 skeleton (Nidhi)
NEXT:           2 → 3 (Ishaan) · 6 after G-H, 7 after G-S (Johar)
THEN:           10 (Nidhi) · 12 (everyone) · 11 final (Nidhi)
LAST:           13 rehearsal
```

If time runs short, **cut the extra parts of task 9 first** (keep Hyderabad to one park-ring figure), then task 7. H6 (tasks 1–3) is the priority: it is the hypothesis we promised at the mid-eval.

---

## 4. Final presentation: 25 minutes + 5 minutes of questions

About 25 slides at about 1 minute each. Each person gets about 5 minutes, in one block, as at the mid-eval.

| Block | Presenter | Minutes | Content |
| --- | --- | --- | --- |
| 1 | Prajna | 4 | Problem, literature disagreement, hypotheses H1–H6 |
| 2 | Himani | 4 | Data, cities, the 1 km grid, new layers (building height, solar radiation) |
| 3 | Johar | 5 | Cooling slope, pilot, robustness, **building height**, the "more sun" test |
| 4 | Ishaan | 5 | Rainfall result, map, dry cities vs Guo, seasons, **H6 felt heat** |
| 5 | Nidhi | 3 | Monsoon, water, checks on the new results |
| 6 | Prajna | 4 | Exposure, **Lorenz curve**, **Hyderabad**, conclusion, limitations |

That totals 25 minutes. Keep the mid-eval results short (about 8 of the 25 minutes), and give the new results the space. Nidhi builds the deck and script, but each person still presents their own block.

---

## 5. Open questions

- [ ] What is the date of the final presentation?
- [ ] Is there a written report as well, or is it a presentation only?
- [ ] Does Ishaan still have `cache/era5/`? If not, task 1 needs 303 Earth Engine calls.
