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

*Speaker points (R1):*
- All seven are free, open datasets. The professor assigned five; we added SRTM elevation as a control (hills are cooler and often greener) and use OpenStreetMap only for water.
- We use the Aqua satellite (MYD11A2), not Terra, because its ~13:30 overpass is closer to the hottest part of the day.
- LST is *surface* temperature (roofs, roads, leaves), not the air temperature people feel. That is a known limitation (Venter et al. 2021; Du et al. 2024), which is why the Heat Index comes later.

*Likely TA question:* "Why 1 km, when GHSL and WorldPop are 100 m?" Because 1 km is the native MODIS LST resolution. Shrinking temperature to 100 m would invent detail the satellite never measured, so the finer layers are averaged up to it.

### Slide 6. 303 Indian cities across the full moisture range, in 3 seasons (R1, DRAFT)
- **Cities:** every Indian urban centre with more than 3 lakh people (GHS Urban Centre Database outlines). That is 303 cities.
- **Seasons:**
  - Pre-monsoon (Apr–May): hot and dry
  - Post-monsoon (Oct–Nov): wet soils
  - Winter (Dec–Feb): cool and dry
- **Years:** 2019–2024 averages, so no single year dominates.
- **Figure:** `figures/B_city_map.png`. Replace it with the rainfall-coloured version after Role 2's climate run.
- **To fill in:** "Annual rainfall ranges from about X mm (Jodhpur) to Y mm (Kochi)". Take the numbers from `city_climate.csv`.

*Speaker points (R1):*
- A "city" is a GHSL urban centre: connected 1 km cells with at least 1,500 people/km² and 50,000 people in total. That gives the same rule in every state, unlike municipal boundaries. We use the 2020 outlines to match our 2020 built-up and population data.
- 303 cities, 53,614 squares of 1 km, about 297 million people (WorldPop 2020). Source: `data/results/b2_checks.csv`, `data/samples/`.
- Seasons really do differ: the median square is 39.7 °C by day before the monsoon, 31.2 °C after it and 27.9 °C in winter. Each season is averaged over 2019–2024.

*Likely TA question:* "Why these three seasons and not the monsoon?" Jun–Sep cloud leaves too few usable images (Role 5's slide 6b, and Kumar et al. 2017 excluded it for the same reason). The other three each still have a clear daytime image 94–98% of the time in the median city.

*Note for R4 (wording):* "Pre-monsoon: hot and dry" is true for most cities but not Kerala, where April–May is already wet. In Kochi, winter (34.1 °C) is slightly warmer than pre-monsoon (33.7 °C) for that reason. Suggest "hot, and dry in most cities".

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

*Speaker points (R1):*
- Quality filter: MODIS gives every pixel a quality code. We keep "good" readings, plus "other quality" readings whose error is at most 2 K. Cloudy readings are thrown out before averaging.
- How we checked it: (1) the 3-season pipeline reproduces the pilot values exactly; (2) the population per square matches WorldPop's own total to within 0.02% (30 km circle around Jodhpur); (3) our own count of MODIS grid squares matches Earth Engine's for every city tested; (4) range checks on every value in all 303 cities (`b2_checks.csv`).
- What gets dropped and why: squares with no temperature are open water (the missing share is identical in every season, so it is not cloud). Squares under 10% built-up are not urban. Cities with fewer than 30 urban squares get no estimate (101 of 303).

*Likely TA question:* "How do you know missing squares are water and not cloud?" A cloudy square would be missing in some seasons and not others. In every city the missing share is the same in all three seasons, and in Kochi the missing squares never had a single reading in 6 years.

### Slide 8. The cooling slope: how much cooler greener squares are, other things equal (R3, DRAFT)
- For each city × season × day/night:
  `LST = b0 + b1·NDVI + b2·built + b3·elevation + b4·water`
- **Cooling slope** = b1 ÷ 10, in °C per 0.1 NDVI. **Negative = greener squares are cooler.**
- **Why controls:** in Jodhpur, the raw slope is −0.59 and not significant. Controlling for built-up share gives −1.32, because bare desert outskirts are hotter than the city.
- **Why clustered uncertainty:** neighbouring squares are alike, so the 95% ranges use ~5 km blocks.
- **Figure:** `figures/A_pilot_raw_vs_adjusted.png` (Role 3).

*Speaker points (R3):*
- One regression per city × season × day/night, about 22,000 fits in all. Each takes all urban squares (built ≥ 10%) of one city. The cooling slope compares squares **within** a city, so the city's climate is held fixed.
- Why controls: in Jodhpur by day the raw slope is −0.59 and not significant; holding built-up share fixed gives −1.32. Bare desert outskirts are hotter than the city, which hides the effect. The figure shows both.
- Why clustered uncertainty: neighbouring squares share weather and soil. Treating them as independent would make the 95% ranges too narrow, so we treat each ~5 km block as one unit of evidence.

*Likely TA question:* "Is this causal?" No. It is an association with the observed confounders (built-up share, elevation, and water once Role 5's data are in) held fixed.

### Slide 9. Climate is one value per city, and exposure is weighted by people (R2 + R4, DRAFT)
- **ERA5-Land is ~9 km,** too coarse to vary within a city, so it describes the **background climate** each city sits in.
- **Dryness measure:** annual rainfall is the main one, and soil moisture is the second. Potential evaporation is unreliable in arid areas, so we don't use it.
- **Heat Index:** daily, NOAA formula, from the daily maximum temperature and the dewpoint.
- **People-weighting:** each square's temperature is weighted by the number of people living there (WorldPop). Comparing this with the plain average shows whether the heat is where people are.

*Speaker points (R2, climate part):*
- ERA5-Land, 2019–2024, averaged over each city outline: rainfall, air temperature, humidity (from dewpoint, Magnus formula), top-layer soil moisture and wind. One value per city per season, because 9 km cannot resolve neighbourhoods.
- The Heat Index is computed **daily** from the day's maximum temperature and mean dewpoint, using the NOAA formula, then averaged. A monthly-mean Heat Index would understate the hot afternoons.
- Rainfall, not rain ÷ potential evaporation: ERA5 potential evaporation is unreliable in arid areas. Soil moisture is the second dryness measure. Neither captures irrigation (Manoli 2019).

*Likely TA question:* "Can one climate value describe a whole city?" It describes the background climate the city sits in, which is exactly what we compare across cities. Differences inside a city come from the 1 km squares.

---

## Part 4: Results

### Slide 10. Pilot: greener squares are cooler by day in both a desert and a wet city (R3, DRAFT)
- **Jodhpur (desert):** −1.32 °C per 0.1 NDVI (95%: −1.98 to −0.67).
- **Kochi (wet):** −1.04 °C per 0.1 NDVI (95%: −1.57 to −0.51).
- **At night, Jodhpur reverses:** greener squares are warmer (+0.62). This shows only once built-up share is controlled.
- **Figure:** `figures/A_pilot_scatter.png` (Role 3).

*Speaker points (R3):*
- Each dot is one 1 km square, with built-up share removed from both axes. The slope of the red line equals the regression's NDVI coefficient exactly (checked to 4 decimals).
- The 3-season pipeline reproduces these pilot numbers exactly. Adding elevation (our main spec) moves both cities to −1.44, and the sign never changes.
- Jodhpur's warm green nights (+0.62) are not unusual: before the monsoon, 25% of 135 cities have significantly greener-is-warmer nights.

*Likely TA question:* "Why does Kochi move when you add elevation, if it's flat?" Kochi spans only 1–38 m, so elevation there stands in for distance from the backwaters (low squares are by the water and cooler). Role 5's water control tests this.

### Slide 11. By day, cooling does not depend on rainfall; at night, wetter cities cool more (R2, DRAFT)
- **Figure:** `figures/D_ce_vs_rain.png` (top row day, bottom row night; one column per season).
- **Text:** "Across 202 cities, the daytime slope shows no clear trend with rainfall in any season (pre-monsoon +0.41 per 10× rain, 95% CI −0.56 to +1.37). At night, wetter cities cool clearly more (pre −1.11, post −1.02 per 10× rain)." By day this supports neither side of the slide-3 debate; at night it sides with Guo / Schwaab (weaker cooling in dry places).

*Speaker points (R2):*
- Each dot is one city's cooling slope; the line is a regression across cities, weighting precise cities more. A flat line by day means greener squares are about as much cooler in Jodhpur's climate as in Kochi's.
- The daytime result holds every way we fit it: unweighted, capped weights, dropping cities with few blocks, adding temperature and density. "No clear pattern" is a result here, because the intervals are narrow enough to rule out large effects.
- At night the trend is clear and holds the same checks. Dry cities' green squares stay warm at night (Jodhpur's pattern), wet cities' cool, which fits Guo's heat-storage idea.

*Likely TA question:* "Isn't rainfall just standing in for something else?" Partly, before the monsoon: adding air temperature and density shrinks the night effect to unclear (−0.51). After the monsoon it survives (−0.89, 95% CI −1.70 to −0.07).

*Likely TA question:* "Couldn't it be city size?" No. With city size added, the rainfall results don't move (night −1.10 before and after the monsoon, both clear), and size itself is never significant.

### Slide 12. Greener is cooler by day almost everywhere in India (R2, DRAFT)
- **Figure:** `figures/D_ce_map_pre_day.png`. Blue = cooling, red = warming; hollow markers = not significant; size = population. Optional backup: `D_ce_map_pre_night.png` for the night contrast.

*Speaker points (R2):*
- 141 of 202 cities (70%) are significantly blue before the monsoon; red dots are rare (2%) and scattered, with no region where greenery warms by day.
- Hollow markers lean towards small cities (60% of the non-significant ones have fewer than 60 squares, against 40% of the significant ones): fewer squares, wider 95% range. The most extreme slopes on both ends also come from small cities.
- Missing cities (101) are too small to have 30 urban 1 km squares.

*Likely TA question:* "Is there a regional pattern?" Not by day; that is what slide 11 tests formally.

### Slide 13. Dry Indian cities do not warm by day; their green squares warm at night (R2, DRAFT)
- **Table** (pre-monsoon, from `data/results/main_result_bins.csv`):

| | Cities | Median slope | Significant cooling | Greener-is-warmer |
|:--|--:|--:|--:|--:|
| **Day**, < 1,000 mm | 56 | −1.02 | 73% | 0% |
| **Day**, ≥ 1,000 mm | 146 | −1.10 | 68% | 3% |
| **Night**, < 1,000 mm | 39 | +0.48 | 5% | 49% |
| **Night**, ≥ 1,000 mm | 96 | −0.11 | 29% | 16% |

- **Text:** "Guo et al. 2026 found 22% net warming under 1,000 mm. By day we find none (0 of 56 dry cities). At night, half the dry cities (49%) have warmer green squares, against 16% of wet ones."

*Speaker points (R2):*
- By day dry and wet cities look alike: about 70% cool significantly, with almost identical median slopes. Rainfall does not split them.
- At night it does, and the share of warm green nights falls steadily with rainfall: 50% under 750 mm, 30% at 750–1,500 mm, 3% over 1,500 mm.
- Why not Guo's daytime warming? Guo's cities are arid worldwide; India's dry cities are semi-arid, and much urban greenery is watered (Manoli 2019), which rainfall cannot see. Different metric and method, so this is a contrast, not a replication.

*Likely TA question:* "Are the night numbers reliable with so few dry cities?" Only 39 dry cities have night estimates. With a 6-night cut-off (48 dry cities) the result gets stronger, 60% vs 16%.

### Slide 14. In the same city, daytime cooling is weaker after the monsoon, night cooling stronger (R3, DRAFT)
- **Figures:** `figures/S_season_paired.png` and `figures/S_dce_vs_dsoil.png`.
- **Text:** "Cooling is [stronger / weaker] after the monsoon in X% of cities; [more so where soils wetted most]."
- **Draft text:** "By day, cooling is weaker after the monsoon in 79% of 202 cities (median change +0.45 °C per 0.1 NDVI); at night it is stronger in 73% of 127 cities (median −0.18)." Add: "This is not explained by soil wetting (`S_dce_vs_dsoil.png`: no relation, 202 cities)."

*Speaker points (R3):*
- Same city, same squares, different season. Everything fixed about the city (layout, size, region) cancels out. That is why this is our cleanest test of conditions (H4).
- By day the pre-monsoon slope is the strongest (median −1.05, against −0.63 post and −0.77 winter). One possible reading, not yet tested: there is the most sun and the hottest surfaces in Apr–May, so there is more heat for vegetation to offset.
- At night the change goes the other way: greener squares are relatively cooler after the monsoon.

*Likely TA question:* "Is the change just noise?" Wilcoxon p ≈ 2e-17 by day across 202 cities. Per city, 26% are significantly weaker and only 4% significantly stronger, using a conservative standard error that treats the seasons as independent.

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

### Slide 16. Daytime cooling survives every check; controls are what matter (R3, DRAFT)
- **Figure:** `figures/H_robustness_table.png`. The variants are EVI, a 20% built-up cut-off, each control removed, water squares dropped, and a 6-night cut-off.
- Name the one variant that matters most.
- **Draft text:** "66–77% of cities show significant daytime cooling under every variant. Dropping the controls matters most (city ranking ρ = 0.60 with the main spec); EVI gives the same ranking (ρ = 0.85)."

*Speaker points (R3):*
- What we changed: the greenness index (EVI), the urban cut-off (20%), each control, and the night cut-off (6 clear nights). The rainfall column: the rainfall slope changes sign across variants and is significant only with EVI, so "no clear daytime pattern" is the safe reading. Water rows arrive with Role 5's files.
- The night result depends on the built-up control: without it, greener squares look cooler at night in 53–75% of cities; with it, the night slope centres on zero. Built-up surfaces hold heat at night.
- A 6-night cut-off adds 24–32 humid cities at night and does not change the picture (ρ = 0.93–0.94).

*Likely TA question:* "Why do NDVI and EVI disagree in some cities?" They disagree on significance in 13% of cities. It is not explained by NDVI being tied to built-up share (14% vs 12%, p = 0.83), so we report it as an open point.

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
