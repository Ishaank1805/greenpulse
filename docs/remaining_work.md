

# GreenPulse: Remaining Work

## Quick recap: what's done ✅

- **Earth Engine is set up** (project `greenpulse-510209`). Ask Himani to add you.
- **All 5 datasets are checked** and give sensible numbers.
- **303 Indian cities** (3 lakh+ people) are ready in `data/cities/india_cities.geojson`.
- **Script 1** (`02_sample_city.py`) cuts a city into 1 km squares and saves temperature (day and night), greenness (NDVI, EVI), built-up share and population for each square. It's been checked against independent calculations.
- **Script 2** (`03_cooling_efficiency.py`) fits the "cooling slope" for each city: how much cooler greener squares are.
- **Pilot, Jodhpur (dry) vs Kochi (wet):** greener = ~1 °C cooler per 0.1 NDVI during the day in both. At night, greener areas in Jodhpur are *warmer* (reason not confirmed yet).

Full details: `pj_explanation.md`

---

## Remaining tasks

Each task says what it is, why it matters, what you need, what you produce, and when it's done.
**Size:** 🟢 small · 🟡 medium · 🔴 large

### Can start right now (no waiting)

---

**Task A: Pilot chart** 🟢
- **What:** a scatter plot for Jodhpur and Kochi: greenness (x) vs temperature (y), one dot per square, with the fitted line. Day and night.
- **Why:** it's the first result slide, and it shows the method visually.
- **Needs:** `data/samples/jodhpur.csv` and `kochi.csv` (already there).
- **Produces:** 2–4 chart images in `figures/`.
- **Done when:** someone who's never seen the project can look at the chart and say "greener = cooler".

---

**Task B: Run all 303 cities** 🟡 *(the most urgent task; D, F and H wait on it)*
- **What:** run `02_sample_city.py` for all 303 cities, then `03_cooling_efficiency.py`.
- **Why:** two cities can't answer "under what conditions"; we need many cities.
- **How:** write a small loop that skips cities already done, so a crash doesn't mean starting over. Big cities take longer.
- **Check:**
  - Every city has a CSV.
  - Square count ≈ city area ÷ 0.86.
  - Values are realistic (temperature 20–55 °C, NDVI 0–0.9).
  - Note any city with lots of empty squares.
- **Produces:** 303 CSVs in `data/samples/`, plus `data/results/cooling_efficiency.csv`, plus a short list of **cities dropped** (fewer than 30 usable squares) and why.
- **Careful:** our free Earth Engine limit is **shared by the whole team**. Run the full job once, not repeatedly.

---

**Task C: Climate for each city** 🟡
- **What:** from ERA5-Land, get each city's climate:
  - **annual rainfall**: the whole year, averaged over 2019–2024, *not* April–May, which is near zero everywhere
  - April–May air temperature
  - humidity (from dewpoint)
  - soil moisture
- **Why:** these are the "environmental conditions" in the question.
- **Needs:** only the city list. It doesn't depend on Task B.
- **Produces:** `data/results/city_climate.csv`, one row per city.
- **Check:** Jodhpur ≈ 300–450 mm rain a year and Kochi ≈ 2,500–3,500 mm. If not, something's wrong.

---

**Task E: Heat Index per city** 🟡
- **What:** convert ERA5-Land temperature and dewpoint into a **"feels-like" Heat Index** for each city (April–May):
  - dewpoint → relative humidity (Magnus formula)
  - → Heat Index (Rothfusz formula; it needs °F, so convert)
- **Why:** the question says heat *exposure*, and humidity changes how hot it feels (Borah 2026).
- **Important limitation:** ERA5-Land squares are **9 km**, bigger than our 1 km squares. So the Heat Index is **one value per city**, used as a *condition*, not per square. Say this clearly on the slides.
- **Needs:** only the city list. It pairs well with Task C (same dataset), so the same person could take both.
- **Produces:** a Heat Index column added to `city_climate.csv`.
- **Check:** humid coastal cities (Kochi, Chennai) should have a Heat Index well above their air temperature; dry cities (Jodhpur) close to or below it.

---

**Task G: OpenStreetMap water mask** 🔴
- **What:** get lakes, rivers and sea from OpenStreetMap, work out **what share of each 1 km square is water**, drop mostly-water squares, and re-run the cooling slope.
- **Why:**
  - Water is cool by day and warm at night, like greenery, so it can fake or hide the vegetation effect. It might even explain Jodhpur's warm nights.
  - It also uses the 5th dataset the professor gave us.
- **Start with:** Jodhpur and Kochi only, then all cities once Task B is done.
- **Careful:** the OSM data for all of India is large (over 1 GB). Look for a smaller way first (per-city download or an online query service).
- **Produces:**
  - a water-share column for each square
  - cooling slopes with and without water squares
  - one line of conclusion: "results hold" or "results change"

---

**Task I: Slides and write-up** 🟡 *(ongoing)*
- **What:** the mid-evaluation slides in the required order: **Problem → Data → Method → Results → Observations**.
- **Why:** it's what gets marked.
- **Can start now:**
  - Problem: from `project_topic.md` and the literature review.
  - Data: table in `pj_explanation.md` Section 5.
  - Method: Section 2.
- **Fill in later:** Results and Observations, from Tasks A, D, F and H.

---

### Start after Task B is finished

---

**Task D: Cooling vs climate: the main result** 🟡 *(needs B + C)*
- **What:** plot each city's cooling slope against its climate (rainfall, humidity, Heat Index, soil moisture, built density), and test whether the pattern is real (a simple regression across cities).
- **Why:** this directly answers **"under what environmental conditions is the cooling effect strongest?"**
- **Compare with the literature:**
  - Guo 2026 and Manoli 2019: expect weaker cooling in dry cities.
  - Schwaab 2021 found the opposite.
  - Borah 2026: expect trouble in humid cities.
- **Produces:**
  - scatter plots of cooling slope vs rainfall and vs humidity
  - **a map of India** coloured by cooling slope
  - 2–3 sentences of findings
- **Done when:** you can say, in one sentence, whether dry, wet or humid cities cool best, even if the answer is "no clear pattern" (that's a valid result).

---

**Task F: Who gets the cooling (population)** 🟡 *(needs B)*
- **What:** for each city, compare:
  - the **average** greenness and temperature over all squares
  - the **people-weighted** average, which counts squares where more people live more heavily
- **Why:**
  - Heat *exposure* depends on where people live.
  - If the green, cool parts are empty and the crowded parts are hot, the city's cooling isn't reaching people (Chakraborty 2019, Chen 2022).
- **Produces:**
  - a table per city: area-average vs people-average temperature
  - which cities change rank most
  - one chart
- **Check:** in most cities, crowded squares should be hotter and less green than average.

---

**Task H: Robustness checks** 🟢 *(needs B)*
- **What:** across all cities, check whether the answers hold when we change our choices:
  - NDVI vs EVI (they disagreed in Kochi; is that common in humid cities?)
  - 10% vs 20% built-up cut-off
  - day vs night: does the Jodhpur "warm nights" pattern show up in other dry cities?
- **Why:** examiners will ask "would your result change if…?"
- **Produces:** a short table and 2–3 sentences.

---

### Everyone
- Read the **abstracts of all 20 papers**, and the **results sections of Guo 2026, Borah 2026, Ibsen 2021 and Meili 2021**.
- **Be able to explain your own task:** what, why and how you checked it. Examiners ask each person.

---

## Order at a glance

```
NOW:        A (chart)   B (303 cities)   C+E (climate + Heat Index)   G (water, pilot)   I (slides)
                           │                    │
AFTER B:     F (population)   H (robustness)    │
                           └────────┬───────────┘
AFTER B+C:              D (MAIN RESULT: cooling vs climate + India map)
```

**For mid-eval (must have):** A, B, C, D and the slides.
**Good to have:** E, F, H.
**Can be "in progress":** G.

## Ground rules
- Settings (project ID, dates, datasets) live in `scripts/config.py`. Change them there, not inside scripts.
- **Check every result before passing it on**: compare with a second calculation or with known real-world values. That's how we caught a big population bug earlier.
- Save outputs in `data/results/` and figures in `figures/`, with clear names.
- Earth Engine limit is shared, so avoid re-running big jobs without reason.

---