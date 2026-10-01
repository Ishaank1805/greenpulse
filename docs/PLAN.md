# GreenPulse: Project Plan (approved)

This is the repo copy of the team's approved plan. The detailed work instructions are in [roles/](roles/README.md).

We measure how much vegetation cools 303 Indian cities in three seasons, then explain where cooling is strongest using climate and urban form. For the mid-sem we aim to have all the core results, about 50–60% of the project.

## Problem statement

**Question:** Can existing urban vegetation measurably reduce heat exposure, and under what environmental conditions is the cooling effect strongest?

**Why it matters:**
- Most evidence comes from Europe, China and North America, and uses daytime surface temperature.
- Recent studies find vegetation can *warm* arid cities (Guo et al. 2026) and raise the felt heat in humid Indian cities (Borah et al. 2026).
- The literature disagrees on dry climates. Guo and Schwaab find weaker cooling; Manoli (with irrigation) and Yang find stronger cooling.
- India covers the whole moisture range, so it is a good place to test this.

| # | Hypothesis | From | Mid-sem? |
| --- | --- | --- | --- |
| H1 | Greener squares are cooler by day in most cities. | Bowler; Schwaab; Kim | Yes |
| H2 | The cooling slope changes with background moisture (rainfall, humidity, soil moisture). We test which way. | Guo, Schwaab vs Manoli, Yang | Yes |
| H3 | Night cooling is weaker than day cooling, and may reverse in dry cities. | Yang; Du; Meili; pilot | Yes |
| H4 | The cooling slope differs between seasons in the same city. | Ibsen; Borah | Yes |
| H5 | Crowded squares get less cooling, so people-weighted heat is higher than area-weighted heat. | Chakraborty; Chen; Li | Yes |
| H6 | Translating surface cooling into felt heat shrinks the benefit most in humid cities. | Venter; Du; Borah | After mid-sem |

All results are associations, not causal effects.

## Data

**Cities:** 303 Indian cities with more than 3 lakh people (GHS-UCDB R2024A outlines). **Years:** 2019–2024. **Unit:** the 1 km MODIS square.

**Seasons:**
- **Pre-monsoon:** Apr–May.
- **Post-monsoon:** Oct–Nov.
- **Winter:** Dec–Feb.
- **The monsoon (Jun–Sep) is excluded** because of cloud (Kumar et al. 2017). We show usable-pixel shares as an observation.

| Dataset | Earth Engine ID | Resolution | Use |
| --- | --- | --- | --- |
| MODIS LST (Aqua) | `MODIS/061/MYD11A2` | 1 km, 8-day | Day (~13:30) and night (~01:30) temperature, QC-filtered |
| MODIS vegetation | `MODIS/061/MOD13A1` | 500 m → 1 km | NDVI (main), EVI (check) |
| ERA5-Land | `ECMWF/ERA5_LAND/MONTHLY_AGGR`, `DAILY_AGGR` | ~9 km | One value per city per season: rainfall, temperature, humidity, soil moisture, wind, Heat Index |
| GHSL | `JRC/GHSL/P2023A/GHS_BUILT_S` (2020) | 100 m | Built-up share (control, urban filter) |
| WorldPop | `WorldPop/GP/100m/pop` (2020) | ~100 m | People per square |
| OpenStreetMap | Overpass / osmnx, per city | Vector | Water share per square |
| SRTM | `USGS/SRTMGL1_003` | 30 m | Elevation control |

**ERA5 caveats:** evaporation values are negative by convention, and potential evaporation is unreliable in arid areas. So rainfall is the dryness measure and soil moisture is the second one.

## Methodology

1. **Sample each city:** every 1 km square × season gets day and night LST, NDVI, EVI, built-up share, population, elevation and water share. Only squares that are at least 10% built count as urban. All three seasons are pulled in one Earth Engine pass per city.
2. **Cooling slope** for each city × season × day/night:
   - Fit `LST = b0 + b1·NDVI + b2·built + b3·elev + b4·water`.
   - The cooling slope is b1 ÷ 10, in °C per 0.1 NDVI. **Negative means greener squares are cooler.**
   - 95% intervals use standard errors clustered on ~5 km blocks.
   - Cities with fewer than 30 usable squares are dropped and listed.
3. **City climate** from ERA5-Land, one value per city per season (it is too coarse for anything finer).
4. **Main result:** the cooling slope against rainfall, humidity, soil moisture, temperature and built density, using WLS across cities. Includes a < 1000 mm vs ≥ 1000 mm comparison against Guo's 22%, and a map of India.
5. **Seasons:** the change in the same city's slope from pre-monsoon to post-monsoon and winter, linked to the change in soil moisture.
6. **Exposure:** people-weighted vs area-weighted temperature and NDVI.
7. **Robustness:** EVI instead of NDVI, a 20% built-up cut-off, each control removed, water squares dropped, and night warming in dry vs wet cities.

## Pilot so far (Jodhpur vs Kochi, Apr–May)

- **By day, greener squares are cooler.** The slope is −1.3 °C per 0.1 NDVI in Jodhpur and −1.0 in Kochi, with built-up share controlled.
- **At night, greener squares in Jodhpur are warmer,** but this shows only once built-up share is controlled. It fits Yang et al. and Du et al. (night cooling near zero) and Guo's heat-storage mechanism.

## Roles

| Role | Tasks | Presents |
| --- | --- | --- |
| 1. Pipeline | B1 three-season sampling, B2 all cities, M monsoon availability, G OSM water | Data, sampling method |
| 2. Climate | C + E city climate and Heat Index, D main result | Climate method, the headline result, map, threshold |
| 3. Analysis | A pilot charts, extending and running script 03, S seasons, H robustness | Regression method, pilot, seasons, robustness |
| 4. Exposure and story | F exposure, L literature accuracy, I deck (editor) | Problem, exposure, Observations, limitations and next steps |

## Decisions

- **Pre-monsoon window:** April–May, the same as the pilot.
- **Mid-sem format:** a presentation to the TA (no written submission). Each person presents their own part.
- **Roles:** the team assigns people to roles.

## Risks and fallbacks

| Risk | Fallback |
| --- | --- |
| Earth Engine quota runs out during B2 | Finish pre-monsoon for all 303 cities first. Then do the other seasons for 12 cities that span dry to humid: Jodhpur, Jaipur, Ahmedabad, New Delhi, Hyderabad, Nagpur, Pune, Bengaluru, Chennai, Mumbai, Kolkata, Kochi. |
| Post-monsoon is cloudy in coastal cities | Report pixel counts, and drop cities with fewer than 30 squares in that season |
| Changing script 02 breaks validated output | B1 must reproduce the pilot exactly before B2 starts |
| Greenness tracks water, elevation or low density | Controls, robustness checks, association language |
| ERA5 is too coarse inside cities | City-level condition only, stated on the slides |
| NDVI saturates in dense canopy | EVI check |
| Rainfall misses irrigation (Manoli) | Soil moisture as a second dryness measure |

## After the mid-sem

- H6, the perceived-heat scenario
- Lorenz curve of who receives the cooling
- Building height (GHSL 2018)
- Optional Hyderabad case study with Landsat at 30 m
