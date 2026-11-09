# Role 4: Exposure and story

Read [README.md](README.md) first. It defines the file formats (§3), the gates (§2) and the shared rules (§4) that this file assumes.

**You own:** `scripts/style.py`, `scripts/12_exposure.py`, `docs/observations.md` (you create it; everyone writes under their own heading) and the slide deck.

**You produce:**
- `data/results/exposure.csv`
- the figures `figures/F_*.png`
- the deck itself

**You present:** the **Problem statement** (question, why it matters, the literature disagreement, hypotheses), the **exposure result** and the **Observations**, plus the closing slide on what is done and what is next.

**You are also the deck's editor and fact-checker.** Every number on every slide must trace back to a results CSV or the verified literature table in README §5.

**You do not need Earth Engine.** Everything you do runs on CSVs.

## Order of work

| Step | Task | Waits on | Unblocks |
| --- | --- | --- | --- |
| 1 | Stage 0 setup (no `earthengine authenticate` needed) | Nothing | |
| 2 | **`style.py`**, committed in the first hour | Nothing | Consistent figures from everyone |
| 3 | **`docs/observations.md`** skeleton | Nothing | Everyone's observation lines |
| 4 | **I:** deck skeleton, plus the Problem slides (fully) and Data/Method slides (drafts) | Nothing | |
| 5 | **L:** literature accuracy pass over the Problem slides | Nothing | |
| 6 | **F:** write `12_exposure.py` and test it on the pilot CSVs | Nothing (code against README §3.1) | |
| 7 | **F:** run on all cities, rerunning as B2 progresses | B2 samples (R1). Does **not** need script 03 or G4. | Exposure slide |
| 8 | Collect figures and observations, build the Results and Observations slides | G4-based results from R2 and R3 | |
| 9 | Fact-check pass and rehearsal | Everything | Presentation |

Steps 2–6 can all happen in Stage 1. You are the person least blocked by others, so use that time to get the story and the deck in shape early.

---

## Step 1: Stage 0 setup

```bash
git clone https://github.com/prajpenmetsa/greenpulse.git && cd greenpulse
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Read [../PLAN.md](../PLAN.md), the literature review (`docs/literature_review.pdf`) and README §5 (the verified facts).

---

## Step 2: `scripts/style.py` (commit this first)

```python
import matplotlib as mpl

SEASON_COLORS = {'pre': '#E07B00', 'post': '#1B9E77', 'winter': '#7570B3'}   # orange, blue-green, purple
SEASON_LABELS = {'pre': 'Pre-monsoon (Apr–May)', 'post': 'Post-monsoon (Oct–Nov)',
                 'winter': 'Winter (Dec–Feb)'}
DIVERGING = 'RdBu_r'     # cooling slope maps: negative (cooling) = blue, positive (warming) = red; centre on 0
SEQUENTIAL = 'viridis'
CE_LABEL = 'Cooling slope (°C per 0.1 NDVI); negative = greener is cooler'
DRY_COLOR, WET_COLOR = '#B8860B', '#1F78B4'   # < 1000 mm vs ≥ 1000 mm rainfall groups

def apply_style():
    mpl.rcParams.update({'figure.dpi': 110, 'savefig.dpi': 200, 'savefig.bbox': 'tight',
                         'font.size': 11, 'axes.titlesize': 12, 'axes.labelsize': 11,
                         'axes.spines.top': False, 'axes.spines.right': False,
                         'axes.grid': True, 'grid.alpha': 0.25, 'legend.frameon': False})

def save(fig, name):            # name like 'F_exposure_gap'
    from pathlib import Path
    out = Path(__file__).resolve().parents[1] / 'figures' / f'{name}.png'
    out.parent.mkdir(exist_ok=True)
    fig.savefig(out)
    return out
```

Commit it, push, and post "style.py is in: use `from style import apply_style, save, SEASON_COLORS, DIVERGING, CE_LABEL`".

---

## Step 3: `docs/observations.md` skeleton

Create the file with these headings, so each person writes only under their own: `## Role 1 (sampling)`, `## Role 2 (climate)`, `## Role 3 (pilot, seasons, robustness)`, `## Role 4 (exposure)` and `## Role 5 (water and data quality)`.

Add one line at the top: "One sentence per finding, with numbers and the CSV it comes from. Associations, not causes."

You turn these lines into the Observations slide.

---

## Step 4, I: the deck

**Format:** a presentation to the TA, with no written submission. Each person presents their own part.
- Use a shared Google Slides deck so all five people can edit, or whatever tool the team prefers. Put the link in the team chat and at the top of `docs/observations.md`.
- **Confirm the time limit with the TA.** Until you know it, plan about 1 minute per slide.

**Slide rules:**
- **Titles state the finding.** Every title is a full sentence, e.g. "Greener squares are cooler by day in 8 of 10 cities", not "Results".
- **One idea per slide.** Each figure carries a one-line caption that gives its source CSV.
- **Units on everything.** State the sign convention once on the method slide, and again in the caption of every cooling-slope figure.
- **Associations, not causal claims.**
- **Speaker notes.** Each slide's presenter writes 3–5 bullets in the notes.

**Outline (owner presents):**

| # | Slide (finding-style title to fill in) | Owner | Source |
| --- | --- | --- | --- |
| 1 | Title: project, team, course | R4 | |
| 2 | **Problem:** cities are hotter, and greening is the go-to fix. Does it work, and where? | R4 | Literature review introduction; Peng, Manoli (README §5) |
| 3 | **The literature disagrees on dry climates, and mostly measures surface heat** | R4 | Guo and Schwaab vs Manoli and Yang; Venter (~6×), Du (~12×); the evidence is mostly from Europe, China and North America |
| 4 | **Our question and hypotheses H1–H5** (H6 is listed as after mid-sem) | R4 | PLAN.md |
| 5 | **Data:** seven open datasets, each with its resolution and use | R1 | Main README data table |
| 6 | **Study area:** 303 cities from ~350 to ~3,000 mm of rain, in 3 seasons | R1 (+ R2's figure) | `B_city_map.png`, `C_climate_overview.png` |
| 6b | **Why no monsoon:** too few usable satellite pixels in Jun–Sep | R5 | `M_lst_availability.png` |
| 7 | **Method 1:** 1 km squares, QC-filtered, 2019–2024 seasonal means | R1 | role_1 slides |
| 8 | **Method 2:** the cooling slope from a regression with controls and clustered uncertainty | R3 | `A_pilot_raw_vs_adjusted.png` |
| 9 | **Method 3:** city climate from ERA5-Land, daily Heat Index, people-weighting | R2 (+ one line from R4) | |
| 10 | **Pilot:** greener is cooler by day in Jodhpur and Kochi, and Jodhpur reverses at night | R3 | `A_pilot_scatter.png` |
| 11 | **Headline:** how the cooling slope changes with rainfall | R2 | `D_ce_vs_rain.png` |
| 12 | **Map** of cooling slopes across India | R2 | `D_ce_map_pre_day.png` |
| 13 | **Threshold:** cities under 1000 mm vs Guo's 22% | R2 | `main_result_bins.csv` |
| 14 | **Seasons:** the same city before and after the monsoon | R3 | `S_season_paired.png`, `S_dce_vs_dsoil.png` |
| 15 | **Exposure:** people live in hotter, less green squares | R4 | `F_*.png` |
| 15b | **Water:** does water explain part of the effect, and Jodhpur's warm nights? | R5 | `G_water_effect.png` |
| 16 | **Robustness:** what changes the answer and what doesn't | R3 | `H_robustness_table.png` |
| 17 | **Observations:** 5–7 one-line findings, each linked to H1–H5 and to a paper | R4 (each person reads their own line) | `docs/observations.md` |
| 18 | **Limitations, and what is left for the final** | R4 | See below |

**Slide 18 content:**
- **Done (about 50–60%):** the pipeline, 303 cities × 3 seasons, the main results.
- **Left for the final:**
  - H6, the perceived-heat scenario: turning surface cooling into Heat Index terms with the LST-to-air ratio from Venter and Du
  - a Lorenz curve of who gets the cooling
  - building height (GHSL, 2018) as an urban-form control
  - optionally, a Hyderabad case study with Landsat at 30 m
- **Limitations:**
  - LST is surface temperature, not felt heat
  - ERA5 gives city-level values only
  - associations only
  - no monsoon season
  - OSM misses the sea as a water polygon
  - NDVI cannot separate trees from grass or crops

**Draft slides 1–4 fully, and 5–9 as drafts, in Stage 1.** Fill 10–17 as figures arrive.

---

## Step 5, L: literature accuracy (for the slides)

The literature review PDF is the team's submitted version and does not need to be rewritten for the mid-sem. But the **slides must not repeat its imprecise claims**. Use the README §5 wording for these:

| Review says | Slides must say |
| --- | --- |
| Bowler: ~0.9 °C from "parks and street trees" | **Parks**, ~0.94 °C cooler **by day** |
| Manoli: "greening is more efficient in drier regions" | More efficient in dry regions **with irrigation**. Warns about water scarcity. ~1000 mm threshold. |
| Schwaab: weaker cooling in the drier south | The same, **under hot extremes** (0–4 K south vs 8–12 K central Europe) |
| Borah: canopy activity raises the Heat Index in humid, poorly ventilated cores | ML **associations**, pre-monsoon midday. "Poorly ventilated" is the authors' interpretation, not a measurement. |
| Du: "much higher" | ~**12×** (0.075 vs 0.006 °C per 1% tree cover) |
| Venter: "roughly six times larger" | Correct as stated (1.45 vs 0.26 °C) |
| (missing from the review) | **Yang 2022: tree cooling efficiency is higher in hot, dry cities.** Present it as the opposite side of the Guo debate. |

Also prepare a **"which paper does this follow?" cheat sheet** in your speaker notes. The TA may ask any presenter:

| What we do | Where it comes from |
| --- | --- |
| The cooling slope idea | Yang 2022 (cooling efficiency); Schwaab 2021 (LST vs tree cover) |
| Background climate as the explanation | Zhao 2014; Manoli 2019; Guo 2026 |
| The 1000 mm threshold | Guo 2026; Manoli 2019 |
| Day vs night | Yang 2022, Du 2024 (night ≈ 0); Ibsen 2021 (air temperature at night) |
| Heat Index | Borah 2026 |
| People-weighting | Chakraborty 2019; Chen 2022; Li 2024 |
| No monsoon | Kumar 2017 |

---

## Steps 6–7, F: who gets the cooling (`12_exposure.py`)

**Question:** are the cool, green squares where people live? This tests H5. Heat **exposure** depends on where people are, not on the city's area average.

**Data:**
- Use `common.load_samples()` (R3's helper) if it exists, otherwise read `data/samples/*.csv` directly, excluding `_pilot_v1/`.
- For testing before G1, use `data/samples/_pilot_v1/*.csv`. These are in the old format: one row per square, pre-monsoon only, no `season` or `elev`. Write a small adapter that adds `season = 'pre'`.

**Per city × season:**
- Use urban squares only (`built >= 0.10`), and drop NaN `lst_day`.
- For night values, use squares with `n_night >= 10` and non-NaN `lst_night`.
- Compute:

| Column | Formula |
| --- | --- |
| `area_lst_day` | `lst_day.mean()` |
| `pop_lst_day` | `(pop * lst_day).sum() / pop.sum()` |
| `gap_lst_day` | `pop_lst_day − area_lst_day`. **Positive means people live in hotter-than-average squares.** |
| `area_lst_night`, `pop_lst_night`, `gap_lst_night` | The same, at night |
| `area_ndvi`, `pop_ndvi`, `gap_ndvi` | The same for NDVI. **Negative means people live in less-green squares.** |
| `n_cells`, `pop_total` | Number of urban squares, and the sum of `pop` |

- Write `data/results/exposure.csv` with the columns in README §3.5.
- Skip cities with fewer than 30 urban squares, using the same rule as script 03.

**Across cities, for each season:**
- the share of cities with `gap_lst_day > 0`, and the median gap
- the share with `gap_ndvi < 0`
- the same, split into < 1000 and ≥ 1000 mm groups, using `rain_annual_mm` from R2's `city_climate.csv` once it exists
- the 10 cities with the largest positive daytime gap
- a comparison: Chakraborty 2019 found poorer neighbourhoods hotter in 72% of 25 cities

  We use **population density, not income**, so say "more crowded squares", not "poorer". WorldPop has no income data.

**Figures:**
- **`figures/F_exposure_gap_hist.png`:** a histogram of `gap_lst_day` across cities, pre-monsoon, with a vertical line at 0 and the share > 0 written on the plot.
- **`figures/F_exposure_dumbbell.png`:** the 20 most populous cities, pre-monsoon day. For each city draw two dots, area-average LST and people-weighted LST, joined by a line, and sort by gap.
- **`figures/F_crowded_vs_green.png` (optional):** across cities, `gap_ndvi` (x) against `gap_lst_day` (y). Do the cities where people sit in less-green squares also have the largest heat gaps?

**Checks:**
- [ ] **Population total.** Jodhpur's total over **all** squares (no built filter) is about **0.98 million** (979,491 in the pilot file). The city file's 1.54 M is for 2025, over a larger outline, from a different model. If your number differs a lot, look at how `pop` is read.
- [ ] **Bounds.** Every `pop_lst_day` lies between that city's min and max `lst_day`.
- [ ] **Hand check.** For Jodhpur pre-monsoon, recompute `pop_lst_day` in a separate notebook cell with `numpy.average(lst_day, weights=pop)`. It must match to 1e-9.
- [ ] **Expectation, not a requirement.** In most cities, crowded squares should be hotter and less green than average, so `gap_lst_day > 0` and `gap_ndvi < 0`. If not, that is a finding. Check it is not a bug before reporting it.

**Run order:** run on the pilot now. Rerun whenever R1 commits more samples (`git pull --rebase` first), and commit `exposure.csv` and the figures each time. You do **not** need to wait for script 03 or G4.

**Observation line**, under `## Role 4 (exposure)` in `docs/observations.md`:

> "In X% of N cities, people-weighted daytime surface temperature is higher than the area average (median +Y °C); crowded squares are less green in Z%. Greening that exists is not where most people live."

Adjust the wording to what the numbers show.

---

## Steps 8–9: assembly, fact-check, rehearsal

**Collect.** As each gate passes, pull and drop the new figures into the deck. Ask each owner for their speaker notes.

**Fact-check every slide:**
- [ ] Each number on the slide can be found in a CSV in `data/results/` or in README §5. Write the source in small text under the figure.
- [ ] The sign convention is consistent: negative means greener is cooler.
- [ ] The city count is consistent across slides. If a slide uses a subset, such as cities with both pre and post estimates, the title or caption says so.
- [ ] No causal language.
- [ ] The hypotheses on slide 4 match the observations on slide 17.

**Rehearsal.** Do one full run-through, with each person presenting their own slides, and time it. Then each person answers two practice TA questions from their role file's "Be ready for" list.

**What "done" looks like for the mid-sem:**
- Slides 1–18 are filled.
- Every figure comes from committed scripts.
- `docs/observations.md` has at least one numbered finding from every role.
- Every presenter can explain their part, why they did it, and how they checked it.

---

## Final phase (Prajna)

**Your tasks:** 8 (Lorenz curve and Gini) and 9 (the Hyderabad Landsat case study), from [../FINAL_PLAN.md](../FINAL_PLAN.md) §3. Both are code. **Nidhi now builds the deck and script**, so send her your speaker points and figures.

| Step | Task | Waits on | Unblocks |
| --- | --- | --- | --- |
| 1 | `17_lorenz.py`: who receives greenness and cooling | Nothing (samples and slopes exist) | Deck |
| 2 | `18_hyderabad.py`: park cooling at 30 m | Nothing; agree Earth Engine time with Himani and Ishaan | Deck |
| 3 | Observation lines, speaker points to Nidhi | 1, 2 | Deck |

Step 1 is pure Python. Start it now, while Earth Engine time gets agreed for step 2.

### Step 1: Lorenz curve and Gini (`17_lorenz.py`)

**Question:** within each city, how unevenly are greenery, and the cooling it brings, shared among people? This builds on the exposure analysis (`12_exposure.py`).

**Data:**
- `data/samples/` (urban squares, `built ≥ 0.10`, with non-NaN `ndvi` and `pop`).
- The main-spec day slopes from `common.main_spec(cooling_efficiency.csv)`.
- Same city rule as before: at least 30 urban squares.

**Greenness inequality, per city × season:**
1. Give every person their square's NDVI, so each square is weighted by its `pop`.
2. Sort squares by NDVI, from least to most green.
3. Lorenz curve: x = cumulative share of people, y = cumulative share of total "person-NDVI" (Σ pop·NDVI).
4. Gini = 1 − 2 × (area under the Lorenz curve), using the trapezoid rule with the point (0, 0) added.
   - A Gini of 0 means everyone gets the same greenness; 1 means one square has it all.

**Cooling inequality,** for cities whose day slope is negative (greener is cooler):
1. Cooling received per square = −`ce_per_0.1` × (NDVI − the city's 10th-percentile NDVI) / 0.1, clipped at 0.
   - This is how much cooler a square is than the city's barest squares, according to the city's own slope.
2. Compute the Gini of cooling received across people, in the same way.
3. Skip cities whose slope is not negative, and count them.

**Output:** `data/results/lorenz.csv` (README §6.1).

**Across cities:**
- the median Gini for greenness and for cooling, by season
- the 5 most and 5 least unequal cities (pre-monsoon)
- a test of whether larger or wetter cities are more unequal: Spearman of Gini against `n_cells` and against `rain_annual_mm`

**Figures:**
- **`figures/L_lorenz_examples.png`:** Lorenz curves for 6 cities (the 3 most and 3 least unequal, or Delhi, Mumbai, Kolkata, Bengaluru, Jodhpur and Kochi), with the diagonal for perfect equality.
- **`figures/L_people_gap.png`:** people-weighted minus area Gini, per city and season. Above 0 means greenness or cooling sits away from where people live. This replaces a histogram of raw Gini values, which can't be compared between greenness and cooling (see the note in `17_lorenz.py`).

**Checks** (build them in):
- [ ] **Equal case:** a fake city with equal NDVI and equal population gives a Gini of exactly 0.
- [ ] **Concentrated case:** a fake city where one square has all the NDVI gives a Gini close to 1 − 1/n.
- [ ] **Hand check:** recompute one real city's Gini by hand with numpy, using a different formula, the mean absolute difference: G = ΣΣ|xᵢ − xⱼ|·wᵢ·wⱼ / (2·mean·W²). The two must agree to 1e-6.
- [ ] **Range:** every Gini is between 0 and 1.

**The literature link, stated carefully:** Chen et al. 2022 found greenspace exposure inequality of Gini 0.47 in the Global South against 0.27 in the North. That is across cities worldwide with a different greenspace measure, so compare direction and scale, not the exact value.

### Step 2: Hyderabad case study (`18_hyderabad.py`)

**Question:** what does 30 m data show that 1 km squares cannot? Specifically: how far does a park's cooling reach, and how strong is it? Compare with Shah et al. 2021: Bengaluru, Landsat surface temperature, 2.23 °C cooler, cooling reaching 347 m.

**The city:** Hyderabad, `uc_id 9524`, about 861 km², from `data/cities/india_cities.geojson`.

**Landsat surface temperature (Earth Engine):**
- Collections `LANDSAT/LC08/C02/T1_L2` and `LANDSAT/LC09/C02/T1_L2`, merged.
  - Filter: Hyderabad outline, April–May 2019–2024, `CLOUD_COVER < 20`.
- **Mask clouds** with `QA_PIXEL`. Drop pixels with bit 1 (dilated cloud), bit 3 (cloud) or bit 4 (cloud shadow) set.
- **Convert units:**
  - Surface temperature: `ST_B10 × 0.00341802 + 149 − 273.15` (°C).
  - NDVI: from `SR_B5` and `SR_B4`, after scaling each by `× 0.0000275 − 0.2`.
- **Composite:** take the median over all clear scenes. Report the number of scenes; there should be at least 5.
- Landsat passes at about 10:30–11:00 local time, earlier than MODIS Aqua's 13:30. So its temperatures will be lower than MODIS values, which is expected. State it.

**Parks (OpenStreetMap, osmnx):**
- Tags: `{'leisure': ['park', 'garden', 'nature_reserve'], 'landuse': ['recreation_ground']}`. `nature_reserve` is needed because OSM tags KBR National Park that way.
- Keep polygons of at least 5 ha.
- Drop parks that are mostly water, such as lakeside promenades, using Nidhi's OSM water approach. Cache the download in `raw/osm/`.
- Report how many parks are left, with their names where OSM has them.

**Rings:**
- For each park, build outward rings 30 m wide, from 0 to 1,000 m past the park edge. Work in a metric projection, such as UTM zone 44N, `EPSG:32644`.
- Remove other parks and water from each ring, so a ring measures built-up surroundings only.
- Compute the mean surface temperature of the park interior and of each ring inside Earth Engine, using `reduceRegions(mean, scale=30)` on the composite. Upload the rings as a FeatureCollection, in batches of about 1,000 features.
  - This keeps the output small: one number per ring, instead of downloading the 30 m raster.

**Cooling distance and intensity, per park:**
1. Fit a cubic polynomial to ring temperature against distance (0–1,000 m).
2. **Cooling distance:** the first turning point, where temperature stops rising. If there is none within 1,000 m, record 1,000 m and flag it.
3. **Cooling intensity:** temperature at that distance minus the park interior.
4. This turning-point approach is common in park-cooling studies. Check Shah et al. 2021's methods section before saying it is the same method as theirs.

**Outputs:** `data/results/hyderabad_parks.csv` and `hyderabad_ring_profile.csv` (README §6.1).

**Figures:**
- **`figures/HYD_ring_profile.png`:** the median temperature against distance across parks, with the inter-quartile band, and a dashed line at Shah's 347 m.
- **`figures/HYD_map.png`:** the 30 m surface temperature map of Hyderabad with park outlines, next to the 1 km MODIS squares (`data/samples/9524_hyderabad.csv`, pre-monsoon). This makes the resolution point visible.

**Checks:**
- [ ] **Parks are cooler:** the interior is cooler than the 500–1,000 m ring in most parks. Report the share.
- [ ] **Plausible temperatures:** composite values mostly 30–50 °C before the monsoon.
- [ ] **Agrees with MODIS:** averaging the 30 m composite into each MODIS 1 km square gives a pattern that correlates positively with the MODIS daytime temperature for Hyderabad. Values will be offset, because of the different overpass time.
- [ ] **Enough parks:** at least 10. If there are fewer, relax the size threshold to 2 ha and say so.

### Step 3: observations and slides

**Observation lines** go under `## Role 4` in `docs/observations.md`:
- **Lorenz:** "Within cities, greenness is shared unequally (median Gini X), and the cooling it provides even more so (Y)."
- **Hyderabad:** "At 30 m, Hyderabad's parks are X °C cooler than their surroundings, with cooling reaching about Y m (Shah et al. 2021, Bengaluru: 2.23 °C, 347 m). Our 1 km squares cannot see this."

Your block in the final talk is about 4 minutes: exposure (short), the Lorenz curve, Hyderabad, and the conclusion and limitations. Send speaker points to **Nidhi**.
