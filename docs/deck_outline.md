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
  - Under hot extremes, trees cool less in dry southern Europe (0–4 K) than in central Europe (8–12 K) (Schwaab et al. 2021, 293 cities).
- **Stronger:**
  - Greening is more efficient in dry regions, but only with irrigation (Manoli et al. 2019).
  - Tree cooling efficiency is higher in hot, dry cities (Yang et al. 2022, 510 cities).

**Humid cities: a new warning.**
- In 138 Indian cities, at pre-monsoon midday, high canopy activity goes with a higher Heat Index in humid cores (Borah et al. 2026; a machine-learning association, not a measured mechanism).

**The metric problem.**
- Satellites overstate the urban heat island about 6× compared with air temperature (Venter et al. 2021).
- Tree cooling efficiency from surface temperature is about 12× that from air temperature (Du et al. 2024).

**The geography gap.**
- Most of this evidence comes from Europe, China and North America.

*Speaker notes:* India spans the whole moisture range, from Jodhpur (desert) to Kochi (very wet), so it is a natural place to test the dry-climate disagreement.

*Cheat sheet for every presenter, for "which paper does this follow?":*

| What we do | Where it comes from |
| --- | --- |
| The cooling slope (cooling per unit of greenness) | Yang 2022 (cooling efficiency); Schwaab 2021 (LST against tree cover) |
| Background climate as the explanation | Zhao 2014; Manoli 2019; Guo 2026 |
| The 1,000 mm threshold | Guo 2026; Manoli 2019 |
| Day vs night | Yang 2022 and Du 2024 (night ≈ 0); Ibsen 2021 (night air temperature) |
| Heat Index and humidity | Borah 2026 |
| People-weighting | Chakraborty 2019; Chen 2022; Li 2024 |
| No monsoon season | Kumar 2017 |
| Surface temperature overstates felt heat | Venter 2021 (~6×); Du 2024 (~12×) |

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

### Slide 6. 303 Indian cities across the full moisture range, in 3 seasons (R1, READY)
- **Cities:** every Indian urban centre with more than 3 lakh people (GHS Urban Centre Database outlines). That is 303 cities.
- **Rainfall:** annual rainfall ranges from **262 mm (Bikaner)** to **3,792 mm (Darjeeling)**; the pilot cities are Jodhpur 411 mm and Kochi 3,131 mm. 72 cities get under 1,000 mm a year (`city_climate.csv`).
- **Seasons:**
  - Pre-monsoon (Apr–May): hot, and dry in most cities (median 67 mm of rain; Kerala is already wet, Kochi 622 mm)
  - Post-monsoon (Oct–Nov): wet soils
  - Winter (Dec–Feb): cool and dry
- **Years:** 2019–2024 averages, so no single year dominates.
- **Figure:** `figures/B_city_map.png`: city centres sized by population and coloured by annual rainfall. Caption: "City outlines: GHS-UCDB R2024A. Country boundary: Natural Earth (India point of view). Rainfall: ERA5-Land 2019–2024 (`city_climate.csv`)."

*Speaker points (R1):*
- A "city" is a GHSL urban centre: connected 1 km cells with at least 1,500 people/km² and 50,000 people in total. That gives the same rule in every state, unlike municipal boundaries. We use the 2020 outlines to match our 2020 built-up and population data.
- 303 cities, 53,614 squares of 1 km, about 297 million people (WorldPop 2020). Source: `data/results/b2_checks.csv`, `data/samples/`.
- Seasons really do differ: the median square is 39.7 °C by day before the monsoon, 31.2 °C after it and 27.9 °C in winter. Each season is averaged over 2019–2024.

*Likely TA question:* "Why these three seasons and not the monsoon?" Jun–Sep cloud leaves too few usable images (Role 5's slide 6b, and Kumar et al. 2017 excluded it for the same reason). The other three still keep 94–98% of 8-day images after quality filtering (median over **land** squares, median city; `b2_checks.csv`). This is a different measure from slide 6b's, which averages over all squares including water.

*Second likely TA question:* "Why is Kochi warmer in winter than before the monsoon?" Kerala's April–May is already wet (622 mm in Kochi), so the ground is cooled by evaporation, while winter is dry and sunny. Kochi's winter surface is 34.1 °C against 33.7 °C pre-monsoon. The same code gives the expected order in Jodhpur, so it is not a bug.

### Slide 6b. No monsoon season: too few usable satellite images (R5, READY)
- **Figure:** `figures/M_lst_availability.png`.
- **Text:** "In Mumbai, only **25.2%** of daytime 8-day LST composites are usable in June–September, against **85.0%** in April–May." Kumar et al. (2017) also excluded June–September because of cloud-limited satellite coverage.
- Across the six cities checked, monsoon daytime availability is lower than pre-monsoon availability; Kolkata is lowest at **19.1%**.
- **Measure:** the share of 8-day images that pass the quality filter, averaged over **every** square in the city outline, with water squares counting as unusable. That is why Mumbai's April–May figure (85%) is lower than slide 6's land-only figure (~98%). Compare months **within** this chart, not with slide 6.

*Speaker points (R5):*
- We used the same MODIS LST quality mask as the main pipeline and measured usable observations month-by-month over 2019–2024 in six cities.
- The loss is substantial and geographically uneven: Mumbai drops from 85.0% before the monsoon to 25.2% during it, while Kolkata reaches 19.1%.
- So we exclude June–September because cloud leaves much less comparable LST coverage across cities, not because we assume vegetation has no effect during the monsoon.

*Likely TA question:* "Why not keep monsoon with fewer observations?" Because the missing coverage is large and uneven between cities, so estimates would be based on very different amounts of usable satellite data.

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

*Likely TA question:* "How do you know missing squares are water and not cloud?" A cloudy square would be missing in some seasons and not others. In every one of the 303 cities, exactly the same squares are missing in all three seasons, and in Kochi the missing squares never had a single reading in 6 years.

### Slide 8. The cooling slope: how much cooler greener squares are, other things equal (R3, READY)
- For each city × season × day/night:
  `LST = b0 + b1·NDVI + b2·built + b3·elevation + b4·water`
- **Cooling slope** = b1 ÷ 10, in °C per 0.1 NDVI. **Negative = greener squares are cooler.**
- **Why controls:** in Jodhpur, the raw slope is −0.59 and not significant. Controlling for built-up share gives −1.32, because bare desert outskirts are hotter than the city.
- **Why clustered uncertainty:** neighbouring squares are alike, so the 95% ranges use ~5 km blocks.
- **Figure:** `figures/A_pilot_raw_vs_adjusted.png` (Role 3).

*Speaker points (R3):*
- One regression per city × season × day/night, about 29,000 fits in all (including the robustness variants). Each takes all urban squares (built ≥ 10%) of one city. The cooling slope compares squares **within** a city, so the city's climate is held fixed.
- Why controls: in Jodhpur by day the raw slope is −0.59 and not significant; holding built-up share fixed gives −1.32. Bare desert outskirts are hotter than the city, which hides the effect. The figure shows both.
- Why clustered uncertainty: neighbouring squares share weather and soil. Treating them as independent would make the 95% ranges too narrow, so we treat each ~5 km block as one unit of evidence.

*Likely TA question:* "Is this causal?" No. It is an association with the observed confounders (built-up share, elevation and water) held fixed.

### Slide 9. Climate is one value per city, and exposure is weighted by people (R2 + R4, READY)
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

### Slide 10. Pilot: greener squares are cooler by day in both a desert and a wet city (R3, READY)
- **Jodhpur (desert):** −1.32 °C per 0.1 NDVI (95%: −1.98 to −0.67).
- **Kochi (wet):** −1.04 °C per 0.1 NDVI (95%: −1.57 to −0.51).
- **At night, Jodhpur reverses:** greener squares are warmer (+0.62). This shows only once built-up share is controlled.
- **Figure:** `figures/A_pilot_scatter.png` (Role 3).

*Speaker points (R3):*
- Each dot is one 1 km square, with built-up share removed from both axes. The slope of the red line equals the regression's NDVI coefficient exactly (checked to 4 decimals).
- The 3-season pipeline reproduces these pilot numbers exactly. With elevation and water added (our final spec), Jodhpur is −1.45 and Kochi −1.90. The sign never changes.
- Jodhpur's warm green nights (+0.62; +0.94 in the final spec) are not unusual: before the monsoon, 24% of 135 cities have significantly greener-is-warmer nights, mostly dry ones.

*Likely TA question:* "Why does Kochi change so much with the controls?" Water. Kochi's water squares are cool and have low NDVI, so without a water control low greenery looks cooler and the cooling is understated. Adding water moves Kochi from −1.44 to −1.90; in Jodhpur, with little water, it changes nothing.

### Slide 11. By day, cooling does not depend on rainfall; at night, wetter cities cool more (R2, READY)
- **Figure:** `figures/D_ce_vs_rain.png` (top row day, bottom row night; one column per season).
- **Text:** "Across 202 cities, the daytime slope shows no clear trend with rainfall in any season (pre-monsoon +0.17 per 10× rain, 95% CI −0.73 to +1.07). At night, wetter cities cool clearly more (pre −1.16, post −0.98 per 10× rain)." By day this supports neither side of the slide-3 debate; at night it sides with Guo / Schwaab (weaker cooling in dry places).

*Speaker points (R2):*
- Each dot is one city's cooling slope; the line is a regression across cities, weighting precise cities more. A flat line by day means greener squares are about as much cooler in Jodhpur's climate as in Kochi's. Humidity, soil moisture and temperature show no clear daytime link either.
- The night trend holds every way we fit it: unweighted, capped weights, dropping cities with few blocks, adding city size, and adding air temperature and density (pre −0.92, post −0.77, both clear). Dry cities' green squares stay warm at night (Jodhpur's pattern); wet cities' cool.
- By day the honest summary is "no robust pattern": dropping the cities with few blocks gives a small wetter-cools-more slope after the monsoon and in winter, and one coastal city alone can flip the pre-monsoon sign.

*Likely TA question:* "Isn't rainfall just standing in for something else?" We tested heat, density and city size; the night effect survives all three.

*Likely TA question:* "Couldn't it be city size?" No. With city size added, the night results don't move (−1.19 before the monsoon, −1.03 after, both clear), and size itself is never significant.

### Slide 12. Greener is cooler by day almost everywhere in India (R2, READY)
- **Figure:** `figures/D_ce_map_pre_day.png`. Blue = cooling, red = warming; hollow markers = not significant; size = population. Optional backup: `D_ce_map_pre_night.png` for the night contrast.

*Speaker points (R2):*
- 151 of 202 cities (75%) are significantly blue before the monsoon; red dots are rare (2%) and scattered, with no region where greenery warms by day.
- Hollow markers lean towards small cities (65% of the non-significant ones have fewer than 60 squares, against 40% of the significant ones): fewer squares, wider 95% range. The most extreme slopes on both ends also come from small cities.
- Missing cities (101) are too small to have 30 urban 1 km squares.

*Likely TA question:* "Is there a regional pattern?" Not by day; that is what slide 11 tests formally.

### Slide 13. Dry Indian cities do not warm by day; their green squares warm at night (R2, READY)
- **Table** (pre-monsoon, from `data/results/main_result_bins.csv`):

| | Cities | Median slope | Significant cooling | Greener-is-warmer |
|:--|--:|--:|--:|--:|
| **Day**, < 1,000 mm | 56 | −1.06 | 77% | 0% |
| **Day**, ≥ 1,000 mm | 146 | −1.18 | 74% | 3% |
| **Night**, < 1,000 mm | 39 | +0.46 | 5% | 38% |
| **Night**, ≥ 1,000 mm | 96 | −0.03 | 24% | 18% |

- **Text:** "Guo et al. 2026 found 22% net warming under 1,000 mm. By day we find none (0 of 56 dry cities). At night, 38% of dry cities have warmer green squares, twice the share of wet ones (18%)."

*Speaker points (R2):*
- By day dry and wet cities look alike: about three quarters cool significantly, with similar median slopes. Rainfall does not split them.
- At night it does, and the share of warm green nights falls steadily with rainfall: 50% under 750 mm, 28% at 750–1,500 mm, 3% over 1,500 mm.
- Why not Guo's daytime warming? Guo's cities are arid worldwide; India's dry cities are semi-arid, and much urban greenery is watered (Manoli 2019), which rainfall cannot see. Different metric and method, so this is a contrast, not a replication.

*Likely TA question:* "Are the night numbers reliable with so few dry cities?" Only 39 dry cities have night estimates. With a 6-night cut-off (48 dry cities) the result gets stronger, 54% vs 18%.

### Slide 14. In the same city, daytime cooling is weaker after the monsoon, night cooling stronger (R3, READY)
- **Figures:** `figures/S_season_paired.png` and `figures/S_dce_vs_dsoil.png`.
- **Text:** "By day, cooling is weaker after the monsoon in 81% of 202 cities (median change +0.43 °C per 0.1 NDVI); at night it is stronger in 69% of 127 cities (median −0.16)." Add: "Soil wetting does not clearly explain this (`S_dce_vs_dsoil.png`: −1.71, 95% CI −3.65 to +0.24)."

*Speaker points (R3):*
- Same city, same squares, different season. Everything fixed about the city (layout, size, region) cancels out. That is why this is our cleanest test of conditions (H4).
- By day the pre-monsoon slope is the strongest (median −1.13, against −0.67 post and −0.81 winter). One possible reading, not yet tested: there is the most sun and the hottest surfaces in Apr–May, so there is more heat for vegetation to offset.
- At night the change goes the other way: greener squares are relatively cooler after the monsoon.

*Likely TA question:* "Is the change just noise?" Wilcoxon p ≈ 7e-19 by day across 202 cities. Per city, 30% are significantly weaker and only 2% significantly stronger, using a conservative standard error that treats the seasons as independent.

### Slide 15. Crowded squares are less green, and the less green they are, the hotter (R4, READY)
- **Less green:** crowded squares are less green than the city average in **90–96%** of 202 cities, depending on season.
- **Hotter at night:** people live in hotter-than-average squares in **96–97%** of cities (135–157 cities with night data; humid cities are under-represented because of cloud).
- **Hotter by day, less consistently:** **63%** pre-monsoon, **87%** post-monsoon, **73%** winter. The gap is small on average (median +0.1 to +0.2 °C) but reaches **+1.08 °C in Kolkata**.
- **The link to vegetation:** across cities, the less green the crowded squares are, the bigger their heat gap (Spearman **ρ ≈ −0.73** in every season).
- **Figures:** `figures/F_exposure_by_season.png` (main) and `figures/F_crowded_vs_green.png` (the vegetation link). Backup: `figures/F_exposure_dumbbell.png`.

*Speaker points (R4):*
- People-weighting: each 1 km square's temperature is weighted by the number of people living there (WorldPop 2020). Comparing with the plain average shows whether the heat sits where people are.
- Night is the clearest result. By day, before the monsoon, some large cities go the other way: Surat, Pune, Mumbai, Kozhikode, Indore, Nagpur, Jaipur. Most of them are wet, so it is not simply a dry-city effect, and the reason is not established.
- Rainfall makes only a small difference, and only before the monsoon (55% of dry vs 66% of wet cities; none in other seasons).
- We use population density, not income, so say "crowded", never "poor". Chakraborty et al. 2019 found poorer neighbourhoods hotter in 72% of 25 cities, using surface temperature, which is the same range as our 63–87% by day.

*Likely TA question:* "Is +0.1 °C meaningful?" On average it is small; the point is the direction (almost every city at night) and the link to greenness (ρ ≈ −0.73). In some cities it is about 1 °C. It is surface temperature, which overstates what people feel (Venter et al. 2021).

*Source:* `data/results/exposure.csv`; rainfall from `city_climate.csv`.

### Slide 15b. Water does not explain away the vegetation effect (R5, READY)
- **Figure:** `figures/G_water_effect.png`.
- **Text:** Across **202 cities**, controlling for mapped water changes the median pre-monsoon daytime slope only from **−1.052 to −1.129 °C per 0.1 NDVI**.
- **Jodhpur night:** **+0.944 → +0.944 °C per 0.1 NDVI**; the warm-green-night association remains after controlling for water.

*Speaker points (R5):*
- Water is a possible confounder because water-rich squares can also be cooler, so we calculated the mapped water fraction of every 1 km MODIS square from OpenStreetMap.
- We compare the same regression with built-up share and elevation (`built_elev`) against one that additionally controls for water (`built_elev_water`).
- The overall daytime slope changes only slightly, and Jodhpur's nighttime slope is unchanged, so mapped water does not explain the main vegetation-temperature association.

*Likely TA question:* "How was water share calculated?" We intersected OpenStreetMap water polygons with each MODIS square and used the fraction of the square covered by mapped water. A known limitation is that OSM coastlines do not represent the sea in the same way as inland water polygons.

### Slide 16. Daytime cooling survives every check; controls are what matter (R3, READY)
- **Figure:** `figures/H_robustness_table.png`. The variants are EVI, a 20% built-up cut-off, each control removed, water squares dropped, and a 6-night cut-off.
- **Text:** "70–77% of cities show significant daytime cooling under every variant. Dropping the controls matters most (city ranking ρ = 0.56 with the main spec); EVI gives a similar ranking (ρ = 0.83), and the water control changes little (ρ = 0.91)."

*Speaker points (R3):*
- What we changed: the greenness index (EVI), the urban cut-off (20%), each control (including water), water squares dropped, and the night cut-off (6 clear nights). The rainfall slope changes sign across variants and is never significant at 5%, so "no clear daytime rainfall pattern" is the safe reading.
- The night result depends on the built-up control: without it, greener squares look cooler at night in 53–75% of cities; with it, the night slope centres on zero. Built-up surfaces hold heat at night.
- A 6-night cut-off adds 24–32 cities at night, about three-quarters of them wet (`robustness.csv`), and does not change the picture (ρ = 0.91–0.95).

*Likely TA question:* "Why do NDVI and EVI disagree in some cities?" They disagree on significance in 14% of cities. It is not explained by NDVI being tied to built-up share (16% vs 13%, p = 0.54), so we report it as an open point.

---

## Part 5: Observations

### Slide 17. What we observe so far (each person reads their own line; READY)
- **H1, greener is cooler by day (R3):** yes, almost everywhere. 75% of 202 cities cool significantly before the monsoon (median −1.13 °C per 0.1 NDVI), and 70–74% in the other seasons. Fits Bowler 2010, Schwaab 2021 and Kim 2024.
- **H2, depends on moisture? (R2):** not by day. The daytime slope shows no clear trend with rainfall (+0.17 per 10× rain, 95% CI −0.73 to +1.07), and no dry city warms by day (0 of 56, against Guo's 22%). So neither side of the dry-climate debate is supported by day.
- **H3, nights (R2/R3):** night slopes centre on zero (as in Yang 2022 and Du 2024). Wetter cities cool more at night (−1.16 per 10× rain, 135 cities): 38% of 39 dry cities have warmer green nights, against 18% of 96 wet ones. This fits Guo's heat-storage idea. Humid cities have less night data, but the result holds with a 6-night cut-off (54% vs 18%).
- **H4, seasons in the same city (R3):** daytime cooling is weaker after the monsoon in 81% of 202 cities (median change +0.43). Night cooling is stronger in 69% of 127. Soil wetting does not clearly explain the change (p = 0.09).
- **H5, exposure (R4):** crowded squares are less green in 90–96% of cities. People live in hotter squares at night in 96–97% of cities and by day in 63–87%, and the less green the crowded squares, the hotter (ρ ≈ −0.73).
- **Data (R1/R5):**
  - The monsoon is excluded: usable images in Mumbai fall from 85% to 25%.
  - 101 of 303 cities are too small for an estimate.
  - Controlling for water barely moves the result (median −1.05 → −1.13).

*Speaker notes:* Every line here is an association, not a cause. Each presenter reads their own line, so keep to one breath each.

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
