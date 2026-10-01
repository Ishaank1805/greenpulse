# GreenPulse — Project Handover

**Read this first.** It explains the project from the beginning: what we are trying to find out, where the data comes from, how we process it, what is finished, what the first results say, and what is still left. You do not need any earlier conversation or document to follow it.

Last updated: 30 September 2026

---

## 1. The project in one paragraph

Cities are hotter than the countryside around them. A common recommendation is to "plant more trees" because vegetation cools the air through shade and evaporation. But recent research shows this does **not always work** — in very dry cities, and in very humid cities, vegetation can cool much less, or even make things feel hotter. Our project measures, for **303 Indian cities**, how much cooler the greener parts of each city actually are, and then asks whether that cooling is **stronger or weaker depending on the city's climate** (dry vs wet, humid vs not).

### The official problem statement (from the professor)

> *Research question:* Can existing urban vegetation measurably reduce heat exposure, and under what environmental conditions is the cooling effect strongest? The project evaluates ecosystem-based climate adaptation rather than simply mapping green space.
>
> *Open datasets:* MODIS land-surface temperature; ERA5-Land; OpenStreetMap; GHSL; WorldPop.

Only this statement is official. Everything else (choosing India, the method, the 303 cities) is our team's design, explained and justified below.

---

## 2. Basic ideas you need (plain words)

| Term | What it means | Why we care |
|---|---|---|
| **Land-surface temperature (LST)** | How hot the *ground surface* is (roofs, roads, soil, leaves), measured by a satellite from space. Not the air temperature you feel. | It is the only temperature measured everywhere, every few days, at 1 km detail. |
| **NDVI** | A greenness score from satellite images, from about 0 (bare ground, concrete) to about 0.9 (dense forest). | Tells us how much vegetation each part of the city has. |
| **EVI** | Another greenness score, similar to NDVI. | NDVI "maxes out" over very dense vegetation; EVI does not. We use EVI as a check. |
| **Built-up fraction** | The share of the ground covered by buildings (0 = none, 1 = fully covered). | Needed to separate "cooler because of trees" from "cooler because there are fewer buildings". |
| **1 km square (cell)** | We cut each city into squares about 1 km × 1 km (exactly 926 m, the satellite's pixel size). | The satellite temperature cannot see anything smaller than this, so every dataset is brought to this size. |
| **Cooling efficiency (CE)** | The slope of a line: how much temperature changes as greenness goes up, for squares with the same amount of building. Unit: °C per unit of NDVI. | **This is the main number of the project.** Negative = greener squares are cooler. More negative = stronger cooling. |
| **Heat exposure** | How much heat *people* actually experience — depends on humidity (how hot it feels) and where people live. | The professor's question says "heat *exposure*", not just temperature. |
| **Pre-monsoon (April–May)** | The hottest months in most of India, before the rains. | Hottest time = most relevant. Mostly cloud-free = satellite can see the ground. |

### How cooling efficiency works — a simple picture

Imagine plotting every 1 km square of a city as a dot: greenness along the bottom, temperature up the side. Greener dots tend to sit lower (cooler). Draw the best straight line through the dots. **The slope of that line is the cooling efficiency.** A steep downward line = vegetation cools a lot. A flat line = vegetation does little. An upward line = greener places are *hotter*.

We also give the line a second input — built-up fraction — so that the slope reflects greenness *at the same level of building*. Without this, the line would partly measure "fewer buildings" instead of "more vegetation" (in most cities, green squares and less-built squares are largely the same squares).

---

## 3. How we are answering the problem statement

We split the professor's question into its parts and answer each one with a specific measurement:

| Part of the question | What it asks | How we answer it | Status |
|---|---|---|---|
| "Can existing urban vegetation **measurably reduce heat**…" | Is there a real, measured cooling effect? | Cooling efficiency (CE) per city, with an uncertainty range, so we can say whether the effect is real or just noise. | ✅ Method done, tested on 2 cities |
| "…heat **exposure**…" | Heat as people experience it. | (a) **Heat Index** — combines temperature and humidity into "how hot it feels"; (b) **population weighting** — does the cooling happen where people actually live? | ⏳ Left to do |
| "…under what **environmental conditions** is the cooling effect strongest?" | Where does vegetation work best? | Compare CE across 303 cities against each city's climate: annual rainfall, humidity, soil moisture, and built density. | ⏳ Left to do |
| "…**ecosystem-based climate adaptation** rather than simply mapping green space." | Judge *how well* vegetation performs, not just *where* it is. | CE measures performance (°C of cooling per unit of greenness), not coverage. Two cities with the same amount of green can have very different CE. | ✅ Built into the method |
| **Existing** urban vegetation | Only vegetation that is actually in the city. | We only analyse squares that are at least 10% built-up, to exclude farmland and plantations that fall inside city outlines. | ✅ Done |

### Why India?

The professor did not specify a region, so this was our choice. The reasons:

1. **Huge climate range within one country.** From under 300 mm of rain a year (Thar desert — Jodhpur, Bikaner) to over 3000 mm (Kerala, the Northeast). The question asks *"under what environmental conditions"* — so we need cities in very different climates. India gives desert, semi-arid, tropical wet and humid coastal cities all in one country.
2. **One country holds other things roughly constant.** Comparing, say, a Spanish city with an Indian city would mix climate with differences in building styles, planning rules, tree species and wealth. Within India those differences are smaller, so a difference in cooling is more likely to be due to climate.
3. **It fills the gap our literature review found.** The review concludes that research is *"skewed toward Europe, China and North America"* and that future work should test the humidity effect *"across tropical Asia and Africa"*. India is tropical Asia.
4. **It is the only way to test the humid-city reversal.** Borah et al. (2026) found vegetation can make hot, humid Indian cities *feel* hotter. Testing this needs many hot *and* humid cities — India has many (Kochi, Chennai, Kolkata, Mumbai).
5. **Relevance.** Indian cities face some of the most dangerous heat in the world, and urban greening is actively promoted in Indian heat action plans. Knowing where it works matters.
6. **Local knowledge.** We are at IIIT Hyderabad, so we can sense-check results.

### Why not somewhere else?

| Alternative | Why we did not choose it |
|---|---|
| **Europe** | Already done: Schwaab et al. (2021) — one of our 20 references — measured tree cooling across 293 European cities, including how it changes with dryness. We would mostly be repeating them. Europe also has almost no hot-humid cities, so the humid reversal (Borah 2026) cannot be tested there. Europe does have cleaner data — but we have already checked India's data problems (Section 11) and they are manageable. |
| **China / USA** | Also heavily studied (our review names them as over-represented). The USA has a wide climate range, but it is not tropical, and Ibsen et al. (2021) already compared US cities from Miami to Las Vegas. |
| **Global (all countries)** | Already done at global scale by Guo et al. (2026, 761 cities) and Li et al. (2024). A global study also mixes climate with very different countries (point 2 above), and would be much more computing for our free Earth Engine tier. |
| **Africa** | Also a gap in the literature — but OpenStreetMap and population data are less reliable in many African cities, and fewer African cities are large enough for our method (≥ 30 usable 1 km squares). |
| **One Indian city only** | Cannot answer *"under what environmental conditions"* — one city has one climate. We need many cities to compare. |

**Optional check using Europe:** once the 303-city run works, the same scripts can be run on a few European cities to see if we reproduce Schwaab et al.'s published result. Matching a published study would confirm our method is correct.

---

## 4. How the literature review was used

Yes — our literature review (`Urban_Heat_NbS_Literature_Review_v4.docx`) directly shaped the project. The review ends by naming a research gap:

> *"Future work could test whether the humidity mechanism generalises across tropical Asia and Africa, and whether built density and street morphology modify it, by pairing humidity-adjusted metrics with urban form and gridded population data rather than city-mean surface temperature."*

The analysis is designed to test exactly that. Section by section:

| Review section | What the papers found | How it shaped our project |
|---|---|---|
| **What is measured, and why it matters** | Satellite surface temperature overstates heat ~6× compared to air temperature (Venter 2021); the same inflation applies to vegetation cooling (Du 2024); Heat Index captures humidity effects (Borah 2026). "These metrics can differ in sign." | We use satellite LST (the only option at this scale) **but** we plan a Heat Index version, and we will state openly that LST overstates cooling. |
| **What cools, and by how much** | Cooling efficiency as a metric (Yang 2022); trees beat grass (Schwaab 2021, Kim 2024); Indian park cooling ~2.2 °C (Shah 2021, Bengaluru). | Our **cooling efficiency slope follows Yang et al. (2022)**. Difference: Yang used tree fraction; we use NDVI, because it is available for every city from MODIS. |
| **Where and when cooling weakens or reverses** | Cooling weakens as aridity rises (Guo 2026, Manoli 2019) — but Schwaab found the opposite in Europe; humid Indian cities can reverse (Borah 2026); night cooling behaves differently from day (Ibsen 2021); mechanisms shift with climate and hour (Meili 2021). | This is **the core hypothesis**: does CE get weaker in dry cities, in humid cities, or both? It is also why we measure **day and night separately**. |
| **Who receives the cooling** | Poorer neighbourhoods are hotter (Chakraborty 2019); greenspace exposure is unequal (Chen 2022, Li 2024). | Why we plan **population weighting** with WorldPop: city-average cooling may not reach where people live. |
| **Research gap** | Most studies use daytime LST only; coverage skewed away from tropical Asia. | Our design: **tropical Asia (India)** + **humidity metric (Heat Index)** + **urban form (built-up fraction)** + **gridded population (WorldPop)**. |

---

## 5. The data — what, where from, and why

We use all five datasets the professor listed. Only the **city boundaries** are downloaded; everything else is processed inside **Google Earth Engine** (Section 6), so we never download large satellite files.

| Professor's dataset | Exact product | Who makes it | What it tells us | Detail | How we get it |
|---|---|---|---|---|---|
| **MODIS land-surface temperature** | `MODIS/061/MYD11A2` | NASA / USGS (Aqua satellite) | Ground temperature, day (~1:30 pm) and night (~1:30 am) | 1 km, every 8 days | Earth Engine |
| MODIS (vegetation) | `MODIS/061/MOD13A1` | NASA / USGS (Terra satellite) | Greenness (NDVI, EVI) | 500 m, every 16 days | Earth Engine |
| **GHSL** (buildings) | `JRC/GHSL/P2023A/GHS_BUILT_S/2020` | European Commission, Joint Research Centre (JRC) | m² of each 100 m cell covered by buildings, in 2020 | 100 m | Earth Engine |
| **GHSL** (city boundaries) | GHS Urban Centre Database R2024A v1.2 | European Commission, JRC | Outline, name and population of every city | vector | **Downloaded** (see below) |
| **WorldPop** | `WorldPop/GP/100m/pop` (India, 2020) | WorldPop, University of Southampton | Number of people in each 100 m cell | 100 m | Earth Engine |
| **ERA5-Land** | `ECMWF/ERA5_LAND/MONTHLY_AGGR` | ECMWF / EU Copernicus | Climate: air temperature, humidity (dewpoint), rainfall, soil moisture | ~9 km, monthly | Earth Engine |
| **OpenStreetMap** | not used yet | OSM volunteers | Mapped lakes, rivers, sea — to remove water squares | varies | Later (step 15) |

**Time period:** April–May of each year, 2019–2024 (six seasons), averaged.

### The city boundaries (the only download)

- **What:** the *GHS Urban Centre Database* — a list of every city in the world with its outline, name and population. It is part of **GHSL**, one of the professor's datasets.
- **How a "city" is defined:** the UN-endorsed *Degree of Urbanisation* method — a connected group of 1 km squares with at least 1,500 people per km² and at least 50,000 people in total. The same rule for every city, so comparisons are fair (Indian municipal boundaries are drawn differently in each state).
- **Two files used** (both from JRC's official server `jeodpp.jrc.ec.europa.eu`, product page https://human-settlement.emergency.copernicus.eu/ghs_ucdb_2024.php):

| File | Size | Used for | Download link |
|---|---|---|---|
| Central & Southern Asia regional file (2025 outlines) | 71 MB | City **names and populations** | [link](https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_UCDB_GLOBE_R2024A/GHS_UCDB_REGION_GLOBE_R2024A/GHS_UCDB_REGION_CENTRAL_AND_SOUTHERN_ASIA_R2024A/V1-2/GHS_UCDB_REGION_CENTRAL_AND_SOUTHERN_ASIA_R2024A_V1_2.zip) |
| Multi-temporal global file (outlines for each year) | 37 MB | Each city's **2020 outline** | [link](https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_UCDB_GLOBE_R2024A/GHS_UCDB_MTUC_GLOBE_R2024A/V1-2/GHS_UCDB_MTUC_GLOBE_R2024A_V1_2.zip) |

- **Why 2020 outlines?** Our building and population data are from 2020, so the city outlines should match that year. (A 2025 outline would include land that was only built on after 2020.)
- **You only need these files if you want to re-run step 8.** The finished city list (`data/cities/india_cities.geojson`) is already made.

**Citation:** Mari Rivero, I., Melchiorri, M., Florio, P., et al. (2024). *GHS-UCDB R2024A — GHS Urban Centre Database 2025.* European Commission, JRC. doi:10.2905/1a338be6-7eaf-480c-9664-3a8ade88cbcd

Other citations to use: MODIS LST doi:10.5067/MODIS/MYD11A2.061 · MODIS NDVI doi:10.5067/MODIS/MOD13A1.061 · ERA5-Land: Muñoz-Sabater et al. (2021), *Earth System Science Data* 13, 4349–4383. For GHSL BUILT-S and WorldPop, copy the citation from each dataset's page in the Earth Engine catalogue (https://developers.google.com/earth-engine/datasets).

---

## 6. Google Earth Engine — what it is and how we use it

**What it is:** a free Google service (for academic, non-commercial use) that stores petabytes of satellite and climate data — including all of ours — and lets you run calculations on Google's computers.

**Why we use it:** six years of MODIS images for all of India would be hundreds of gigabytes to download. With Earth Engine we send a small Python instruction ("average all April–May temperature images over Jodhpur"), Google does the work, and we receive back only a small table — a few hundred rows per city.

**How our scripts use it, step by step:**
1. Python connects to Earth Engine using our project, **`greenpulse-510209`**.
2. We tell it which datasets, which months (April–May) and which years (2019–2024).
3. We remove bad satellite readings (cloud) using the quality flags that come with the data.
4. We average all the good images into one picture per dataset.
5. We bring every dataset to the same 1 km squares (fine 100 m data is averaged or added *up* to 1 km — we never stretch the 1 km temperature *down*, which would invent detail).
6. We send a city's outline and get back one row per 1 km square, saved as a CSV on our computer.

**Our Earth Engine project:** `greenpulse-510209`, registered for non-commercial academic use (organisation: IIIT Hyderabad; tier: **Community**, free, no billing account). The Community tier has a computing limit of 150 EECU-hours, **shared by everyone using the project**. Our work so far used a tiny fraction of that — but avoid running the full 303-city job many times over without reason.

---

## 7. Getting set up (for a new team member)

### 7a. Get access to the `greenpulse-510209` project

The project owner (Himani) adds you:

1. Go to https://console.cloud.google.com/iam-admin/iam?project=greenpulse-510209
2. Click **Grant access**.
3. Under *New principals*, enter your Google account email.
4. Add two roles: **Earth Engine Resource Viewer** and **Service Usage Consumer**. (Use *Earth Engine Resource Writer* instead of Viewer if you will need to upload files to Earth Engine.)
5. Click **Save**.

*Alternative:* register your own free Earth Engine project at https://console.cloud.google.com/earth-engine (choose academic organisation, non-commercial, Community tier), then change `PROJECT` in `scripts/config.py` to your project ID. Results are identical either way.

### 7b. Install the software

You need Python 3 (we used 3.13, via Miniconda). Then install the libraries (about 70 MB in total, from the internet):

```bash
pip install earthengine-api geopandas pandas statsmodels matplotlib
```

### 7c. Log in to Earth Engine

```bash
earthengine authenticate
```

A browser opens; sign in with the Google account that has access to the project, and allow the permissions. It should end with *"Successfully saved authorization token."* This is done once per computer.

### 7d. Check that everything works

From the `greenpulse` folder:

```bash
python3 scripts/00_check_setup.py
```

It should print `Connected to project: greenpulse-510209` followed by one line per dataset with values for Jodhpur (e.g. LST about 44.8 °C, NDVI about 0.14). If you get a "permission" or "not registered" error, your access from step 7a is not set up yet.

---

## 8. What is in the folder

```
greenpulse/
├── pj_explanation.md                 ← this file
├── project_topic.md                  ← the professor's official brief
├── Urban_Heat_NbS_Literature_Review_v4.docx  ← our literature review
├── initial_assistant_suggestions.md     ← early design notes (NOT official; superseded by this file)
├── raw/                              ← downloaded city boundary files (~200 MB; only needed to re-run step 8)
├── scripts/
│   ├── config.py                     ← shared settings: project ID, dates, dataset IDs, 300k threshold
│   ├── 00_check_setup.py             ← checks Earth Engine works and all datasets return data
│   ├── 01_prepare_cities.py          ← builds the list of 303 cities with 2020 outlines
│   ├── 02_sample_city.py             ← Stage 1: one row per 1 km square for a city
│   └── 03_cooling_efficiency.py      ← Stage 2: cooling efficiency per city
└── data/
    ├── cities/india_cities.geojson   ← 303 cities: ID, name, population, area, 2020 outline
    ├── samples/jodhpur.csv, kochi.csv ← 1 km squares for the two pilot cities
    └── results/cooling_efficiency.csv ← cooling efficiency results
```

**How to run** (from the `greenpulse` folder):

```bash
python3 scripts/01_prepare_cities.py            # only if you need to rebuild the city list
python3 scripts/02_sample_city.py Jodhpur Kochi # extract 1 km squares for named cities
python3 scripts/03_cooling_efficiency.py        # cooling efficiency for every city in data/samples/
```

**Columns in a city CSV** (`data/samples/*.csv`):

| Column | Meaning |
|---|---|
| `city`, `uc_id` | City name and its ID in the GHSL database |
| `lst_day`, `lst_night` | Average April–May ground temperature (°C), ~1:30 pm and ~1:30 am |
| `n_day`, `n_night` | How many of the 41 satellite images were clear enough to use for that square |
| `ndvi`, `evi` | Average April–May greenness |
| `built` | Share of the square covered by buildings (0–1) |
| `pop` | Number of people living in the square (2020) |
| `lon`, `lat` | Centre of the square |

---

## 9. What is done (and how each step was checked)

Every step was checked before moving to the next. "Checked" means we compared against an independent calculation or against known real-world values.

| # | Step | Result | How we know it is right |
|---|---|---|---|
| 1 | Installed Earth Engine for Python | Works | Imports without error |
| 2 | Registered project `greenpulse-510209` (academic, Community tier) | Connected | Queries succeed |
| 3 | Checked all five datasets exist for April–May 2019–2024 | All return data | Values at Jodhpur are realistic: ground 44.8 °C, NDVI 0.14, 55% built, 70 people per 100 m cell |
| 4 | Counted satellite images | 7 per April–May per year (41 total); 2022 has 6 | The satellite's 8-day schedule gives exactly 7 in April–May; one 2022 image is missing from NASA's record |
| 5 | Downloaded and inspected city boundaries | 1,925 Indian cities; **303 with ≥ 300,000 people** | Opened the files; names, populations and outlines present |
| 6 | Chose 2020 outlines | All 303 cities have one | IDs match between the two files; outlines sensible (Jodhpur 219 km², Kochi 1,068 km²) |
| 7 | Wrote and tested the 1 km extraction script on a 5 km circle in Jodhpur | Correct after one bug fix | Script vs direct calculation: NDVI 0.226 vs 0.227; built 0.259 vs 0.262; people 480,338 vs 478,148 |
| 8 | Built the 303-city file | Done | 303 cities, all inside India, no duplicate names, areas unchanged by conversion; 16 broken outlines (broken in JRC's own file) repaired with 0% area change |
| 9 | Extracted 1 km squares for Jodhpur and Kochi | 254 and 1,238 squares | Square counts match city area ÷ square size; Kochi's 185 empty squares confirmed as water (never any reading in 6 years), not cloud |
| 10 | Cooling efficiency for Jodhpur and Kochi | See Section 10 | Robust to the built-up threshold (10% vs 20%); uncertainty computed honestly (see Section 11) |

**A bug we found and fixed (worth knowing):** the first version of the extraction script reported ~47 people per 1 km square in Jodhpur instead of ~5,000. Earth Engine's "sum" in this step was silently returning an average. The fix converts people to density, averages density up to 1 km, then multiplies by the square's area. The check in step 7 caught this — which is why every step is checked.

---

## 10. Results so far (pilot: Jodhpur vs Kochi)

We started with two cities at opposite ends of India's climate range before running all 303 — a cheap way to check the method works.

- **Jodhpur** — dry desert city, Rajasthan (~1 million people in 2020 outline)
- **Kochi** — wet, humid coastal city, Kerala (~3.4 million)

### What the squares look like (April–May)

| | Jodhpur | Kochi |
|---|---|---|
| Usable 1 km squares | 254 | 1,053 (185 are water) |
| Ground temperature, day (median) | **46.5 °C** | **33.7 °C** |
| Ground temperature, night (median) | 26.0 °C | 23.3 °C |
| Greenness NDVI (median) | 0.21 — sparse | 0.65 — very green |
| Built-up (median) | 21% | 10% |

### Main result — daytime cooling efficiency

(NDVI, squares ≥ 10% built, accounting for built-up fraction)

| | Cooling efficiency | Meaning | 95% range | Statistically clear? |
|---|---|---|---|---|
| **Jodhpur** | −13.2 °C per NDVI | 0.1 more NDVI → **1.3 °C cooler** | −19.8 to −6.7 | Yes (p < 0.001) |
| **Kochi** | −10.4 °C per NDVI | 0.1 more NDVI → **1.0 °C cooler** | −15.7 to −5.1 | Yes (p < 0.001) |

**In both cities, greener squares are clearly cooler during the day.** The two cities are **not clearly different** — their ranges overlap a lot. Two cities cannot answer the dry-vs-wet question; that needs all 303.

### Observations

1. **Accounting for buildings matters — and works in opposite directions.** In Jodhpur, more built-up squares are *cooler* by day (bare desert rock on the outskirts heats up more than the city). Without accounting for buildings, Jodhpur's cooling looks only half as strong (−5.9, not statistically clear). In Kochi, built-up squares are hotter, as usually expected.
2. **At night, Jodhpur reverses.** Greener squares are *warmer* at night (+6.2 °C per NDVI, statistically clear). Kochi still shows slight cooling at night. A likely reason: dry desert ground loses heat quickly after sunset, while watered gardens and moist soil hold heat. This connects to the day/night differences in our review (Ibsen 2021, Meili 2021) — but note Ibsen measured *air* temperature, we measure *surface* temperature. To be tested across all cities.
3. **The built-up threshold hardly matters.** 10% vs 20% built gives nearly the same answer (Jodhpur −13.2 vs −13.2; Kochi −10.4 vs −9.5). Good — the result is not an artefact of that choice.
4. **In Kochi, NDVI and EVI disagree.** With EVI, Kochi's daytime cooling almost disappears (−1.6, not clear). Reason: in Kochi, greenness and buildings are tightly linked (greener squares are almost always less built, correlation −0.79), so the model struggles to separate the two. In Jodhpur the two indices agree. To be checked across all cities — if this happens mainly in humid cities, it is itself a finding.

Full results (32 fitted lines: day/night × NDVI/EVI × 10%/20% built × with/without the built-up control) are in `data/results/cooling_efficiency.csv`.

---

## 11. Important decisions and known issues

| Topic | What we decided / found | Why |
|---|---|---|
| **"Urban" squares only** | Only squares ≥ 10% built (and 20% as a check) | City outlines in Kerala and Bihar include dense villages, plantations and farmland (e.g. Kochi's outline is 1,068 km²). The question is about *urban* vegetation. |
| **Water** | Squares with no temperature reading are water and are dropped | Satellite does not measure land temperature over water. |
| **Partly-water squares** | Still in the data — **known limitation** | A square that is 40% lake is cooler because of water, not trees. To be fixed with OpenStreetMap (step 15). Matters more for coastal/lake cities. |
| **Night data** | A square's night value is used only if ≥ 10 clear nights | Night data is patchy (Kochi median: 12 clear nights of 41). |
| **Honest uncertainty** | Uncertainty is calculated on ~5 km blocks of squares | Neighbouring squares are similar, not independent. Treating them as independent makes results look more certain than they are. |
| **Small cities** | A city needs ≥ 30 usable squares to get a result | Fewer squares give an unreliable line. Median city is only 73 km², so some cities will be dropped — report how many. |
| **Surface vs air temperature** | We use surface temperature (LST) | It is the only temperature available at 1 km for all cities. Our literature review warns it overstates cooling (Venter 2021, Du 2024) — state this as a limitation. |
| **Population figures** | Our totals are lower than the city file's (Jodhpur 0.98 M vs 1.54 M) | The file's figure is for 2025 over a larger 2025 outline, from a different population model. |
| **Missing 2022 image** | One 8-day LST image missing in 2022 (6 instead of 7) | Gap in NASA's record; negligible effect. |

---

## 12. What is left

In order — later steps depend on earlier ones. Steps 11–13 are the most important for the mid-evaluation; 14–15 complete the project.

| # | What | Why | Depends on |
|---|---|---|---|
| **11** | **Write up the pilot** — a chart of Jodhpur vs Kochi (temperature vs greenness, with the fitted lines), day and night. | First result to present; shows the method works. Numbers are already in Section 10. | — |
| **12** | **Run all 303 cities** — `02_sample_city.py` then `03_cooling_efficiency.py`. Check the output the same way as for Jodhpur and Kochi. Report how many cities are dropped (too few squares). | Two cities cannot answer the climate question. | — |
| **13** | **Cooling vs climate (main result)** — get each city's climate from ERA5-Land (annual rainfall — *not* April–May, which is near zero everywhere; humidity; soil moisture), then test whether CE is stronger or weaker in wet/dry/humid cities. Include built density as a condition too. Map CE across India. | Answers "under what environmental conditions". Tests Guo 2026 / Manoli 2019 vs Schwaab 2021. | 12 |
| **14** | **Heat exposure** — (a) Heat Index from ERA5-Land temperature and dewpoint (humidity → relative humidity by the Magnus formula → Heat Index by the Rothfusz equation) and compare with LST-based results; (b) population-weighted cooling with WorldPop — which cities change rank? | Answers "heat *exposure*". Tests Borah 2026 (humid-city reversal) and the "who receives the cooling" theme. | 12 |
| **15** | **OpenStreetMap water mask** — get lake/river/sea outlines, compute each square's water share, drop mostly-water squares, re-run, check results hold. | Removes the partly-water limitation; uses the fifth assigned dataset. | 12 |
| — | **Maps, charts and slides** for the mid-evaluation, organised as: Problem Statement, Data Used, Methodology, Results, Observations. | Required format. | 11–13 |
| — | **Everyone reads the key papers** — at least the abstracts of all 20, and the results sections of Guo (2026), Borah (2026), Ibsen (2021) and Meili (2021). | Examiners ask "which paper does your method follow?" and "does this agree with the literature?" | — |

**Mid-evaluation target (50–60% of the project):** steps 11–13 done → we can present all five headings with real results.

---

## 13. Glossary

| Term | Meaning |
|---|---|
| **Earth Engine** | Google's free service for processing satellite data on Google's computers |
| **MODIS** | NASA instrument on the Terra and Aqua satellites; measures temperature and greenness worldwide every day |
| **Composite** | An image combining several days of satellite passes (8-day for temperature, 16-day for greenness), keeping the best readings |
| **QC / quality flags** | Labels NASA attaches to each pixel saying how reliable it is; we use them to remove cloudy readings |
| **Projection / CRS** | The way the round Earth is drawn on a flat map. The city files use "Mollweide" (metres, equal-area); Earth Engine needs latitude/longitude |
| **GeoJSON / GeoPackage** | File formats for map shapes (outlines) |
| **Regression / fitted line** | Finding the straight line that best fits a cloud of points |
| **Slope / coefficient** | How steep the line is — here, °C per unit of greenness |
| **95% range (confidence interval)** | The range the true slope very likely lies in. If it does not include 0, the effect is "statistically clear" |
| **p-value** | How likely we would see a slope this strong by chance if there were really no effect. Below 0.05 = statistically clear |
| **R²** | Share of the temperature differences between squares that the line explains (0–1) |
| **Aridity** | How dry a climate is — low rainfall, dry air, dry soil |
| **Heat Index** | "Feels-like" temperature combining air temperature and humidity |
| **Reanalysis (ERA5-Land)** | A weather model corrected with real observations, giving a complete climate record everywhere |
| **EECU-hour** | Earth Engine's unit of computing time; our free tier allows 150 |
