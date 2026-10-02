# Mid-sem deck: outline and slide text

**Deck:** [Google Slides](https://docs.google.com/presentation/d/1EnrZBA81aB5Bg3Xh8cWKhd4n5jQbhlmhK1_tqBOnO0I/edit?usp=sharing)

**Owner: Role 4.** This is a presentation to the TA. Each person presents their own slides. Paste the text into Google Slides, and update this file when a slide's text changes, so the repo and the deck stay in step.

**Rules:**
- **Titles state the finding.**
- **Every number** comes from a CSV in `data/results/` or the verified facts table (docs/roles/README.md §5).
- **Sign convention, every time:** negative cooling slope = greener squares are cooler.
- **Wording:** associations, not causes.

**Status:**
- **READY:** the text is final.
- **DRAFT:** the text is written, but numbers or figures are still to come.
- **PLACEHOLDER:** waiting on another role. Put a grey box on the slide saying what is coming and from whom.

---

## Part 1: Problem statement

### Slide 1. Title (R4, READY)
- **GreenPulse: Does urban vegetation cool Indian cities, and when?**
- Nature-based solutions for urban heat. Mid-semester evaluation.
- Atharv Johar · Himani Das · Ishaan Karan · Nidhi Vaidya · Prajna Penmetsa

### Slide 2. Cities are hotter than their surroundings, and greening is the go-to fix (R4, READY)
- Cities run hotter than the land around them, because of dense buildings, sealed surfaces and waste heat. Across 419 big cities, MODIS satellites see surfaces 1.5 °C hotter by day and 1.1 °C at night (Peng et al. 2012).
- Trees, parks and green space are promoted as low-cost cooling. They cool through shade and through evaporation from leaves (evapotranspiration, or ET). For example:
  - Parks are about 0.94 °C cooler by day (Bowler et al. 2010).
  - Trees cool 2–3× more than grass or green roofs (Kim et al. 2024).
- **Our question:** can existing urban vegetation measurably reduce heat exposure, and under what environmental conditions is the cooling effect strongest?

*Speaker notes:* The question has two halves. Half one is "does it cool at all?"; half two is "where and when does it cool most?". The second half is the interesting one, and it is where the literature disagrees.

### Slide 3. The evidence disagrees on dry climates, and mostly measures surface heat (R4, READY)

**Dry cities: weaker cooling, or stronger?**
- **Weaker:**
  - In 22% of the driest cities (under 1000 mm/yr of rain), vegetation causes net warming (Guo et al. 2026, 761 cities).
  - Tree cooling is weaker in dry southern Europe than in central Europe (Schwaab et al. 2021).
- **Stronger:**
  - Greening is more efficient in dry regions, but only with irrigation (Manoli et al. 2019).
  - Tree cooling efficiency is higher in hot, dry cities (Yang et al. 2022, 510 cities).

**Humid cities: a new warning.**
- In 138 Indian cities, high canopy activity goes with a higher Heat Index in humid cores (Borah et al. 2026, an association).

**The metric problem.**
- Satellites overstate the urban heat island about 6× compared with air temperature (Venter et al. 2021).
- Tree cooling efficiency from surface temperature is about 12× that from air temperature (Du et al. 2024).

**The geography gap.**
- Most of this evidence comes from Europe, China and North America.

*Speaker notes:* India spans the whole moisture range, from Jodhpur (desert) to Kochi (very wet), so it is a natural place to test the dry-climate disagreement.

### Slide 4. What we test (R4, READY)
- **H1:** greener squares are cooler by day in most cities.
- **H2:** the cooling slope changes with background moisture. We test which way.
- **H3:** night cooling is weaker, and may reverse in dry cities.
- **H4:** the same city cools differently before and after the monsoon.
- **H5:** crowded squares are less green and hotter, so people feel more heat than the city average suggests.
- *After mid-sem:* **H6**, converting surface cooling into felt heat (Heat Index).

---

## Part 2: Data

### Slide 5. Seven open datasets, all in Google Earth Engine except OpenStreetMap (R1, READY)

| Dataset | Resolution | Used for |
| --- | --- | --- |
| MODIS LST (Aqua, MYD11A2) | 1 km, 8-day, ~13:30 and ~01:30 | Day and night surface temperature |
| MODIS vegetation (MOD13A1) | 500 m → 1 km | Greenness: NDVI (main) and EVI (check) |
| ERA5-Land | ~9 km | City climate: rainfall, temperature, humidity, soil moisture, Heat Index |
| GHSL built-up (2020) | 100 m | Built-up share, a control and the urban filter |
| WorldPop (2020) | 100 m | People per square |
| OpenStreetMap | Vector | Water share per square |
| SRTM | 30 m | Elevation, a control |

*Speaker notes:* Everything finer than 1 km is averaged up to the 1 km temperature grid, never the other way round.

### Slide 6. 303 Indian cities across the full moisture range, in 3 seasons (R1, DRAFT)
- **Cities:** every Indian urban centre with more than 3 lakh people (GHS Urban Centre Database outlines). That is 303 cities.
- **Seasons:**
  - Pre-monsoon (Apr–May): hot and dry
  - Post-monsoon (Oct–Nov): wet soils
  - Winter (Dec–Feb): cool and dry
- **Years:** 2019–2024 averages, so no single year dominates.
- **Figure:** `figures/B_city_map.png`. Replace it with the rainfall-coloured version after Role 2's climate run.
- **To fill in:** "Annual rainfall ranges from about X mm (Jodhpur) to Y mm (Kochi)". Take the numbers from `city_climate.csv`.

### Slide 6b. No monsoon season: too few usable satellite images (R5, PLACEHOLDER)
- **Figure:** `figures/M_lst_availability.png`.
- **Text:** "In June–September only X% of 8-day composites are usable in Mumbai, against Y% in April–May." Kumar et al. (2017) also excluded June–September for this reason.
- **Early evidence from Role 1's samples:** Chennai has a median of 21 usable composites after the monsoon, against 36 before it, because its rains come in Oct–Dec.

---

## Part 3: Methodology

### Slide 7. Each city becomes a grid of 1 km squares (R1, READY)
- **Squares:** the 1 km MODIS grid. We keep only urban squares (at least 10% built-up).
- **Quality filtering:** only satellite readings rated reliable (quality flags, error ≤ 2 K). Squares with no reading are open water and are dropped.
- **Seasonal means:** each square gets a seasonal mean for 2019–2024 of day and night temperature, NDVI, EVI, built-up share, population and elevation.
- **Checked:** the new 3-season pipeline reproduces the pilot exactly (Jodhpur 254 squares, Kochi 1,238).
- **Coverage:** 202 of 303 cities have at least 30 urban squares, which is our minimum for a reliable estimate.

### Slide 8. The cooling slope: how much cooler greener squares are, other things equal (R3, DRAFT)
- For each city × season × day/night:
  `LST = b0 + b1·NDVI + b2·built + b3·elevation + b4·water`
- **Cooling slope** = b1 ÷ 10, in °C per 0.1 NDVI. **Negative = greener squares are cooler.**
- **Why controls:** in Jodhpur, the raw slope is −0.59 and not significant. Controlling for built-up share gives −1.32, because bare desert outskirts are hotter than the city.
- **Why clustered uncertainty:** neighbouring squares are alike, so the 95% ranges use ~5 km blocks.
- **Figure:** `figures/A_pilot_raw_vs_adjusted.png` (Role 3).

### Slide 9. Climate is one value per city, and exposure is weighted by people (R2 + R4, DRAFT)
- **ERA5-Land is ~9 km,** too coarse to vary within a city, so it describes the **background climate** each city sits in.
- **Dryness measure:** annual rainfall is the main one, and soil moisture is the second. Potential evaporation is unreliable in arid areas, so we don't use it.
- **Heat Index:** daily, NOAA formula, from the daily maximum temperature and the dewpoint.
- **People-weighting:** each square's temperature is weighted by the number of people living there (WorldPop). Comparing this with the plain average shows whether the heat is where people are.

---

## Part 4: Results

### Slide 10. Pilot: greener squares are cooler by day in both a desert and a wet city (R3, DRAFT)
- **Jodhpur (desert):** −1.32 °C per 0.1 NDVI (95%: −1.98 to −0.67).
- **Kochi (wet):** −1.04 °C per 0.1 NDVI (95%: −1.57 to −0.51).
- **At night, Jodhpur reverses:** greener squares are warmer (+0.62). This shows only once built-up share is controlled.
- **Figure:** `figures/A_pilot_scatter.png` (Role 3).

### Slide 11. [Headline: how the cooling slope changes with rainfall] (R2, PLACEHOLDER)
- **Figure:** `figures/D_ce_vs_rain.png`.
- **Title to write** once the result exists, e.g. "Cooling is [stronger / weaker] in wetter cities."
- **Text:** "Across N cities, the daytime slope changes by X per 10× rainfall (95% CI …)". Then say which side of the slide-3 debate this supports.

### Slide 12. [Map of cooling slopes across India] (R2, PLACEHOLDER)
- **Figure:** `figures/D_ce_map_pre_day.png`. Blue = cooling, red = warming; hollow markers = not significant.

### Slide 13. [Dry cities vs Guo's 22%] (R2, PLACEHOLDER)
- A small table: cities under 1000 mm vs at or above 1000 mm. For each group: number of cities, median slope, % significantly cooling, % greener-is-warmer.
- Compare with Guo et al. 2026: 22% net warming under 1000 mm.

### Slide 14. [Same city, before vs after the monsoon] (R3, PLACEHOLDER)
- **Figures:** `figures/S_season_paired.png` and `figures/S_dce_vs_dsoil.png`.
- **Text:** "Cooling is [stronger / weaker] after the monsoon in X% of cities; [more so where soils wetted most]."

### Slide 15. People live in less green, hotter squares, especially at night (R4, READY)
- **Less green:** crowded squares are less green in **90–96%** of 202 cities, depending on season.
- **At night:** people live in hotter-than-average squares in **96–97%** of cities (135–157 cities, depending on season; humid cities are under-represented because of cloud).
- **By day:** the pattern is weaker and depends on season: **63%** pre-monsoon, **87%** post-monsoon, **73%** winter.
  - The pre-monsoon exceptions include Surat, Pune, Mumbai, Indore, Nagpur and Jaipur, where bare outskirts heat up more than the city (as in Jodhpur).
- **Size of the gap:** small on average (median +0.1 to +0.2 °C), but up to about 1 °C, as in Kolkata (+1.08 °C).
- **Figures:** `figures/F_exposure_by_season.png` (main) and `figures/F_exposure_dumbbell.png` (backup or a second panel).

*Speaker notes:*
- This uses population density, not income, so say "crowded", never "poor". Chakraborty et al. 2019 found poorer neighbourhoods hotter in 72% of 25 cities.
- **Source:** `data/results/exposure.csv`.

### Slide 15b. [Does water explain part of the effect?] (R5, PLACEHOLDER)
- **Figure:** `figures/G_water_effect.png`.
- **Text:** "Controlling for water share changes the median daytime slope from X to Y. Jodhpur's warm green nights [remain / disappear]."

### Slide 16. [What changes the answer, and what doesn't] (R3, PLACEHOLDER)
- **Figure:** `figures/H_robustness_table.png`. The variants are EVI, a 20% built-up cut-off, each control removed, water squares dropped, and a 6-night cut-off.
- Name the one variant that matters most.

---

## Part 5: Observations

### Slide 17. What we observe so far (R4 collects, each person reads their own line; DRAFT)
One line per hypothesis, each with a number and a paper. Fill from `docs/observations.md`.
- **H1** (R3): …
- **H2** (R2): …
- **H3** (R2 / R3): … (give the number of dry and wet cities; humid cities have less night data)
- **H4** (R3): …
- **H5** (R4): crowded squares are less green in 90–96% of cities. People live in hotter squares at night in 96–97% of cities, and by day in 63–87%.
- **Data** (R1 / R5): no monsoon season, 101 cities too small for an estimate, and humid cities under-represented at night.

### Slide 18. Limitations, and what is left for the final (R4, READY)
- **Done (about 50–60%):** the pipeline, 303 cities × 3 seasons sampled, the cooling slopes, climate, exposure and the main results.
- **Left for the final:**
  - **H6:** converting surface cooling into felt heat (Heat Index), using the surface-to-air ratios from Venter and Du
  - who receives the cooling: a Lorenz curve
  - building height as an urban-form control
  - optionally, a Hyderabad case study with Landsat at 30 m
- **Limitations:**
  - surface temperature, not felt heat
  - ERA5 gives city-level values only
  - associations, not causes
  - no monsoon season
  - OSM misses the sea
  - NDVI cannot separate trees from grass or crops
