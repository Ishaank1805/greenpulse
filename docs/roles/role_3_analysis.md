# Role 3: Analysis

Read [README.md](README.md) first. It defines the file formats (§3), the gates (§2) and the shared rules (§4) that this file assumes.

**You own:** `scripts/03_cooling_efficiency.py`, `scripts/common.py`, `scripts/09_pilot_charts.py`, `scripts/10_seasons.py` and `scripts/11_robustness.py`.

**You produce:**
- `data/results/cooling_efficiency.csv`, which is **gate G4**: R2 and R4's Observations depend on it
- `data/results/dropped_cities.csv`, `data/results/seasons.csv` and `data/results/robustness.csv`
- the figures `figures/A_*.png`, `figures/S_*.png` and `figures/H_*.png`

**You present:** the regression part of the **Method** (the cooling slope, the controls, the clustered uncertainty), the **pilot result**, the **seasons result** and **robustness**.

**You do not need Earth Engine.** Everything you do runs on CSVs, so none of your work uses the shared quota.

## Order of work

| Step | Task | Waits on | Unblocks |
| --- | --- | --- | --- |
| 1 | Stage 0 setup (no `earthengine authenticate` needed) | Nothing | |
| 2 | **A:** pilot charts from `data/samples/_pilot_v1/` (or the current pilot CSVs, if R1 hasn't moved them yet) | Nothing | First Results slide |
| 3 | Write `common.py`, and extend `03_cooling_efficiency.py` against README §3.1 | Nothing (you code against the frozen format) | |
| 4 | **Validate 03** on R1's new pilot files | **G1** (R1) | **G3** |
| 5 | Add the water control, tested on the pilot water files | R1's "G pilot ready" | |
| 6 | Run 03 on all sampled cities, repeatedly as B2 progresses, with a final run at the end | G3 + B2 progress | **G4** → R2's D, your S and H, R4's Observations |
| 7 | **S:** seasons | G4 + G2 (R2's `city_climate.csv`, for soil moisture) | Seasons slide |
| 8 | **H:** robustness | G4 (+ G2 for the rainfall slope; + water files for the water variant) | Robustness slide |
| 9 | Observation lines and slides | 7, 8 | |

Steps 2 and 3 run in parallel right now. Do A first, because it is small and gives the team its first result figure. Then write the 03 extension while R1 is still doing B1.

---

## Step 1: Stage 0 setup

```bash
git clone https://github.com/prajpenmetsa/greenpulse.git && cd greenpulse
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Read `scripts/03_cooling_efficiency.py` fully before changing it. It already fits day/night × NDVI/EVI × built ≥ 0.10 or 0.20 × with/without the built control. Its standard errors are clustered on ~5 km blocks, so neighbouring squares are not treated as independent. **Keep all of that.**

---

## Step 2, A: pilot charts (`09_pilot_charts.py`)

**Goal:** someone who has never seen the project looks at it and says "greener = cooler (by day)".

**Data:**
- Pre-monsoon, built ≥ 0.10, Jodhpur and Kochi.
- Use `data/samples/_pilot_v1/{jodhpur,kochi}.csv`. If R1 hasn't moved the files yet, they are still at `data/samples/{jodhpur,kochi}.csv`. Both are in the old wide format, with no `season` column.
- After G1, the new pilot files (`5315_jodhpur.csv`, `9386_kochi.csv`, filtered to `season == 'pre'`) are identical in content.
- For night, keep only squares with `n_night >= 10`, as script 03 does.

**Why a raw scatter is not enough:**
- In Jodhpur, more built-up squares are *cooler* by day, because bare desert rock on the outskirts heats up more than the city.
- So the raw NDVI–LST cloud looks weak: the slope without the built control is −0.59 per 0.1 and not significant.
- With the built control it is −1.32. A raw scatter alone would contradict our own result.

**Figure `figures/A_pilot_scatter.png`:**
- **Layout:** 2 rows (Jodhpur, Kochi) × 2 columns (day, night).
- **Points:** in each panel, draw a **partial-residual (added-variable) plot** using Frisch–Waugh–Lovell:
  - y = residuals of `lst ~ built`, plus the mean of `lst`.
  - x = residuals of `ndvi ~ built`, plus the mean of `ndvi`.
  - Colour the points by `built` (`viridis`).
  - The slope of this cloud equals the `ce` from script 03 **exactly**. That is your check.
- **Line:** add the fitted line, plus a text box such as "−1.32 °C per 0.1 NDVI (95%: −1.98 to −0.67), n = 203". Take the numbers from `data/results/cooling_efficiency.csv` (rows with `index = ndvi`, `built_min = 0.10`, `control = built`).
- **Axes:** "Greenness (NDVI), adjusted for built-up share" and "Land-surface temperature (°C), adjusted for built-up share".

**Figure `figures/A_pilot_raw_vs_adjusted.png`:**
- Jodhpur day only, two panels: the raw scatter with its slope (−0.59, n.s.) next to the adjusted plot (−1.32).
- This is the "accounting for buildings matters" slide, a good teaching moment for the TA.

**Checks:**
- [ ] The slope fitted to each partial-residual cloud equals the `ce` in `cooling_efficiency.csv` to 4 decimal places.
- [ ] The `n` in each panel matches the `n` column (Jodhpur day 203, Kochi day 617).

**Optional, after G1:** `figures/A_pilot_seasons.png`, with the same adjusted day plot for pre, post and winter side by side for both cities.

Commit the script and figures, then post "A done" in chat with the image.

---

## Step 3: `common.py` and extending script 03

### 3a. `scripts/common.py` (shared helpers; R2 and R4 import from here)

```python
MAIN_INDEX = 'ndvi'
MAIN_BUILT_MIN = 0.10
CONTROL_PRIORITY = ['built_elev_water', 'built_elev', 'built']   # first one present wins
SEASONS = ['pre', 'post', 'winter']
DRY_MM = 1000   # Guo 2026 / Manoli 2019 threshold

def load_samples(pattern='*.csv') -> pd.DataFrame        # all data/samples/*.csv (NOT _pilot_v1/), concatenated
def load_water() -> pd.DataFrame                          # all data/water/*.csv, or empty DataFrame
def main_spec(ce: pd.DataFrame) -> pd.DataFrame
```

- **`main_spec`** filters to `MAIN_INDEX` and `MAIN_BUILT_MIN`. Then, for each `(uc_id, season, time)`, it keeps the row whose `control` comes first in `CONTROL_PRIORITY` among the rows **present**. A row counts as present even when its `ce` is NaN, and the caller drops NaN afterwards. It should also handle the old pilot file, which has no `season` column, by treating that as `season = 'pre'`.
- Add a docstring that repeats the sign convention: **negative = greener squares are cooler**.

Commit `common.py` early (in Stage 1) and tell R2 and R4 it exists.

### 3b. Changes to `03_cooling_efficiency.py`

1. **Archive the pilot results first:**
   ```bash
   mkdir -p data/results/_pilot_v1
   git mv data/results/cooling_efficiency.csv data/results/_pilot_v1/cooling_efficiency.csv
   ```
2. **Input:** the long-format samples (README §3.1), using `common.load_samples()`.
   - With city arguments, match a file by `uc_id` or by name (`*_{slug}.csv`).
   - Never read `_pilot_v1/`.
3. **Water:** if `data/water/{same file name}` exists, left-join `water_frac` on `cell_id`. Otherwise set `water_frac = NaN` for that city.
4. **Season loop:** loop `season in ('pre', 'post', 'winter')` outside the existing loops. Add `season` as the third output column, after `uc_id`.
5. **Controls:** replace the `control` True/False switch with these four specs:
   ```python
   CONTROLS = {'none': '', 'built': ' + built', 'built_elev': ' + built + elev',
               'built_elev_water': ' + built + elev + water_frac'}
   ```
   - Skip `built_elev_water` (write no row) when the city has no water file.
   - Inside `fit`, drop NaN on **all variables in that formula**.
   - Keep `built_coef` in the output.
6. **Keep everything else unchanged:** `MIN_NIGHTS = 10`, `MIN_SQUARES = 30`, `BLOCK_DEG = 0.045`, clustered standard errors and `ce_per_0.1 = ce / 10`. This applies to every season. Winter has ~67 composites and pre/post ~45, so 10 nights is a lenient bar in all of them.
7. **Output:** `data/results/cooling_efficiency.csv` with exactly the columns in README §3.3.
8. **Dropped cities:** also write `data/results/dropped_cities.csv`, one row per city × season × time that has no estimate under the main spec, with the columns `uc_id, city, season, time, n, reason`.
   - `reason` is one of: `fewer than 30 urban squares`, `fewer than 30 squares with clear nights`, or `no sample file`.
   - The pilot handover notes that the median city is only 73 km², so expect many small cities to drop. Report the count; it goes on a slide.
9. **Speed:** about 303 × 3 × 2 × 2 × 2 × 4 ≈ 29,000 small OLS fits. That should take minutes. Print progress every 25 cities.

### 3c. Validation, then announce gate G3 (after G1)

- [ ] Run 03 on `5315_jodhpur.csv` and `9386_kochi.csv`.
- [ ] Every `season == 'pre'` row with `control = 'built'` or `'none'` must match `data/results/_pilot_v1/cooling_efficiency.csv` to 1e-9 on `ce`, `se`, `n` and `n_blocks`. For example, Jodhpur `pre/day/ndvi/0.10/built` gives ce = −13.2328, and Kochi gives −10.4187.
- [ ] `built_elev` is close to `built` in Kochi, because Kochi is nearly flat. It may move a little in Jodhpur. If it changes the sign anywhere, inspect that case before going further.
- [ ] Post-monsoon and winter rows exist, with sensible `n`.

Post "**G3 passed:** script 03 reproduces the pilot; seasons and elev control added."

---

## Step 5: water control

When R1 posts "G pilot ready", rerun 03 on the two pilot cities and compare `built_elev_water` with `built_elev`. Post one line in chat, for example: "Adding water share changes Kochi pre/day from X to Y; Jodhpur night from X to Y."

The second number matters, because it tests whether water explains Jodhpur's warm green nights.

---

## Step 6: running on all cities (gate G4)

- Each time R1 commits more samples:
  1. `git pull --rebase`.
  2. Run `python scripts/03_cooling_efficiency.py`, which runs every sampled city.
  3. Commit `cooling_efficiency.csv` and `dropped_cities.csv`, then push.
  4. Post "03 rerun: N cities". R2 reruns D from this.
- **Final run:** after B2 is complete **and** R1's water files exist for all cities. Post "**G4 passed:** final cooling_efficiency.csv, N cities with main-spec estimates (pre/day), N dropped".

**Checks on the full run:**
- [ ] Every city with a sample file appears in the output, or has an entry in `dropped_cities.csv`.
- [ ] Pre/day, main spec: report the share of cities with `ci_hi < 0` (significant cooling). H1 expects most of them. Also report the median `ce_per_0.1`.
- [ ] No `ce_per_0.1` has an absolute value above 10 °C per 0.1 NDVI. Any such value means a degenerate fit, such as almost no NDVI variation: check `vi_sd` and list those cities.

---

## Step 7, S: same-city seasonal comparison (`10_seasons.py`)

**Why:** this is our natural experiment for "under what conditions". The vegetation in a city stays roughly the same between April–May and October–November, but the soils go from dry to wet. Comparing the **same city** removes everything fixed about it: layout, size and region. This tests H4.

**Data:**
- `main_spec(cooling_efficiency)`. All values below are per 0.1 NDVI.
- `city_climate.csv`, from R2.

**Steps:**

1. For each city × time, pivot to `ce_pre`, `ce_post` and `ce_winter`, and their standard errors.
2. Compute the differences and their standard errors:
   - `d_post_pre = ce_post − ce_pre`, with `se_d_post_pre = sqrt(se_post² + se_pre²)`.
   - `d_winter_pre` and its standard error in the same way.
   - This treats the seasons as independent. It is conservative, because the squares are shared between seasons. Say so.
   - A **negative `d_post_pre`** means cooling is **stronger after the monsoon**.
3. Write these to `data/results/seasons.csv` (README §3.5). Keep only cities with estimates in both seasons, and report how many there are.
4. Across cities, for each time:
   - the median `d_post_pre`
   - the share of cities with `d_post_pre < 0`
   - a Wilcoxon signed-rank test of `ce_post` vs `ce_pre`, using `scipy.stats.wilcoxon`
   - the same three for winter vs pre
5. **The moisture link:**
   - Join `Δswvl1 = swvl1_post − swvl1_pre` from `city_climate.csv`.
   - Fit `d_post_pre ~ Δswvl1` by WLS with weights `1/se_d²`.
   - Does a bigger wetting go with a bigger strengthening of cooling?
   - Also split cities into < 1000 and ≥ 1000 mm (`DRY_MM`). Guo would predict that dry cities gain the most cooling when the soil is wet.

**Figures:**
- **`figures/S_season_paired.png`:**
  - A slope chart, with day and night as separate panels.
  - The x axis is pre, post and winter. Draw one thin grey line per city, plus a thick line for the median.
  - Colour the lines by rainfall group (< 1000 vs ≥ 1000 mm).
  - Label Jodhpur and Kochi.
- **`figures/S_dce_vs_dsoil.png`:**
  - `d_post_pre` (y) against `Δswvl1` (x), day only, with the WLS line.
  - Add a horizontal line at 0. The y label reads "Change in cooling slope, post − pre (°C per 0.1 NDVI); negative = stronger cooling after monsoon".

**Checks:**
- [ ] For Jodhpur and Kochi, the computed `d_post_pre` equals `ce_post − ce_pre` taken by hand from `cooling_efficiency.csv`.
- [ ] Report how many cities were lost because of missing post-monsoon estimates (cloud in coastal cities). If more than a third are lost, flag it in Observations.

---

## Step 8, H: robustness (`11_robustness.py`)

**Why:** the TA will ask "would your result change if…?" Answer before they ask.

**Variants**, each compared with the main spec. Write one row per variant × season × time to `data/results/robustness.csv` (README §3.5).

| Variant | How |
| --- | --- |
| `main` | `main_spec(...)`, the reference row |
| `evi` | `index = evi`, otherwise the main spec |
| `built_min_0.20` | `built_min = 0.20` |
| `no_water_control` | `control = built_elev` |
| `no_elev_control` | `control = built` |
| `no_controls` | `control = none` |
| `drop_water_squares` | Refit with the main spec, after dropping squares with `water_frac > 0.5`. Import the `fit` function from 03 (`importlib.import_module('03_cooling_efficiency')`) and run it on filtered samples. |

**Columns:**

| Column | Meaning |
| --- | --- |
| `n_cities` | Cities with an estimate |
| `share_cooling_sig` | Share of cities with `ci_hi < 0` |
| `median_ce_per_0.1` | Median slope across cities |
| `spearman_vs_main` | Rank correlation of the city slopes with the main spec, over the cities present in both |
| `rain_slope`, `rain_slope_p` | WLS of `ce_per_0.1 ~ log10(rain_annual_mm)`, with weights `1/(se/10)²` and HC3 standard errors. This is **the same method R2 uses** in D. Check that the `main` row matches R2's pre/day number. |

**Two specific questions from the pilot:**

1. **Does Jodhpur's warm-night pattern appear in other dry cities?**
   - For night and the main spec, report the share of cities under 1000 mm with `ci_lo > 0` (greener squares significantly warmer), against the share among cities at or above 1000 mm.
   - Do this for each season.
   - Write it as an extra block of rows with `variant = night_warming_dry` and `variant = night_warming_wet`.
2. **NDVI vs EVI disagreement:**
   - Per city (pre/day), mark "disagree" if exactly one of the two indices gives `ci_hi < 0`.
   - Compute each city's correlation between NDVI and built share from the samples.
   - Test whether disagreement is more common when that correlation is strongly negative (the pilot explanation, collinearity) or in humid cities.
   - Report shares in the two rainfall groups.

**Figures:**
- **`figures/H_ndvi_vs_evi.png`:** city slopes with NDVI (x) against EVI (y), pre/day, with the 1:1 line. Colour the points by rainfall.
- **`figures/H_robustness_table.png`:** a rendered table for the slide, pre/day only. Give `share_cooling_sig`, `median_ce_per_0.1`, `spearman_vs_main` and `rain_slope` for each variant. Also write it as a Markdown table in `docs/observations.md` under `## Role 3`.

**Check:**
- [ ] The `main` row's `rain_slope` matches R2's pre/day slope in `main_result_regressions.csv` to 3 decimal places. If it doesn't, one of you has a different filter. Resolve it together.

---

## Step 9: observations and slides

Write one sentence each, with numbers, under `## Role 3` in `docs/observations.md`:

- **H1:** "By day before the monsoon, N of M cities (X%) show significantly cooler greener squares; the median slope is X °C per 0.1 NDVI."
- **H4:** "Within the same city, cooling is [stronger / weaker / no different] after the monsoon in X% of cities (median change X; Wilcoxon p = …), [and more so where soils wetted most]."
- **H3 (dry nights):** "At night, X% of dry cities show greener-is-warmer slopes, against Y% of wet cities."
- **Robustness:** "The pattern holds / changes when …". Name the one variant that matters most.
- **Data limits:** the number of dropped cities and why. If the post-monsoon losses are large, say so.

Compare with the literature, using only the README §5 table. For example, Yang 2022 reports 0.063 °C per 1% tree cover by day. Our metric is per NDVI, so compare **direction and pattern**, not magnitude.

**Your slides:**

1. **Method, the regression:** the formula `LST = b0 + b1·NDVI + b2·built + b3·elev + b4·water`. The cooling slope = b1 ÷ 10, and negative means greener is cooler. Show the main spec, why the controls matter (the raw vs adjusted figure) and why the standard errors are clustered (neighbouring squares are alike).
2. **Result, pilot:** `A_pilot_scatter.png`.
3. **Result, seasons:** `S_season_paired.png` and the one-line finding.
4. **Result, robustness:** `H_robustness_table.png`.

**Be ready for these TA questions:**

- Why control for built-up share? It is shown on the raw vs adjusted slide.
- Why are the standard errors clustered? Neighbouring squares share weather and soil, so treating them as independent overstates certainty.
- Is NDVI the same as trees? No. It measures greenness and cannot separate trees from irrigated grass or crops, which matters for Guo's finding about grassland and cropland.
- Is this causal? No. It is an association, with observed confounders controlled.
