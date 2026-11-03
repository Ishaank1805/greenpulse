# Final talk, block 2 (Himani, Role 1): slide text and speaker points

For **Nidhi** (deck and script). About 4 minutes, 4 slides. Every number comes from the CSVs named under each slide. Sign convention for anything mentioning slopes: negative = greener squares are cooler.

---

## Slide A. Seven open datasets on one 1 km grid (kept short from the mid-eval)

| Dataset | Resolution | Used for |
| --- | --- | --- |
| MODIS LST (Aqua, MYD11A2) | ~1 km, 8-day, ~13:30 / ~01:30 | Day and night surface temperature |
| MODIS vegetation (MOD13A1) | 500 m → 1 km | NDVI (main), EVI (check) |
| GHSL built-up (2020) | 100 m | Built-up share: control and urban filter |
| **GHSL building height (2018), new** | 100 m → 1 km | Urban form: does height change cooling? |
| WorldPop (2020) | 100 m | People per square |
| SRTM | 30 m | Elevation, a control |
| ERA5-Land | ~9 km | City climate, incl. **solar radiation, new** |
| OpenStreetMap | Vector | Water share per square |

*Speaker points:*
- Everything finer than 1 km is averaged **up** to the MODIS temperature grid, never the other way round: 1 km is what the satellite actually resolves.
- Temperature is quality-filtered (cloudy readings removed) and averaged over 2019–2024 for three seasons: pre-monsoon, post-monsoon and winter. The monsoon is excluded for cloud (Nidhi's slide).
- Two layers are new since the mid-eval: building height and solar radiation (slide D).

*Likely TA question:* "Why surface and not air temperature?" It is the only temperature measured everywhere at 1 km. It overstates what people feel (Venter et al. 2021; Du et al. 2024), which is why H6 converts it to felt heat.

---

## Slide B. 303 Indian cities across the full moisture range

- **Figure:** `figures/B_city_map.png` (dots sized by population, coloured by annual rainfall).
- Every Indian urban centre with more than 3 lakh people: **303 cities, 53,614 squares of ~1 km**, about 297 million people.
- Rainfall from **262 mm (Bikaner) to 3,792 mm (Darjeeling)**; 72 cities under 1,000 mm.

*Speaker points:*
- A city is a GHSL urban centre, one rule for every state. 2020 outlines, to match the 2020 built-up and population data.
- **202 cities** have at least 30 urban squares (built ≥ 10%) and get a cooling slope; the other 101 are listed as too small.

*Sources:* `b2_checks.csv`, `city_climate.csv`, `data/samples/`.

---

## Slide C. Each city becomes a grid of checked 1 km squares

- **Figure:** `figures/B_grid_example.png` (Jodhpur: daytime surface temperature next to NDVI, 254 squares).
- Checks: the 3-season pipeline reproduces the pilot exactly; population matches WorldPop's own total to 0.02%; our own MODIS-grid count matches Earth Engine's; all 303 cities sampled, 0 failures.

*Speaker points:*
- In Jodhpur the greener centre is the cooler part and the bare outskirts are the hottest: the raw pattern the cooling slope measures.
- Missing squares are water, not cloud: exactly the same squares are missing in every season, in every city.

*Likely TA question:* "How do you know the data are right?" Four independent checks (above), and every flagged value explained, e.g. Kashmir's −12.8 °C winter nights are real at 1,600–2,000 m.

---

## Slide D. Two new layers: building height and solar radiation (new)

- **Figure:** `figures/B_new_layers.png`. Left: median urban building height per city. Right: each city's sunshine before the monsoon against after it and in winter.
- **Building height** (GHSL 2018, weighted by built-up surface so empty cells do not dilute tall blocks): urban squares are mostly low-rise, median **7.9 m**, 98.9% between 3 and 30 m. Tallest city: Mumbai (15.1 m); lowest: dense Gangetic towns (~2.5–3 m).
- **Solar radiation** (ERA5-Land, MJ/m² per day): lower after the monsoon than before it in **all 303 cities** (median 24.2 → 16.1, −32%). Pre-monsoon is the sunniest season everywhere except **11 Kerala cities**, where cloudy April–May gets less sun than winter.

*Speaker points:*
- **Why height:** does the same greenness cool less in tall, dense areas? Johar re-estimates the cooling slope within height terciles. Height and built-up share overlap (correlation 0.56 across urban squares), so it adds urban form but is not independent of built-up share.
- **Why solar radiation:** cooling is weaker after the monsoon in most cities (H4). One explanation is that there is simply less sun to offset; Johar tests whether the change in cooling tracks the change in sunshine.
- **Both were added without touching the validated data:** height was appended as a new column, and every original value is byte-identical to the mid-eval files. Solar radiation is a separate city-level file.

*Likely TA questions:*
- "Height is 2018 but built-up is 2020?" GHSL's height layer exists only for 2018; it is the closest available match, and stated in the method.
- "Why is Kerala different?" Its pre-monsoon storms cut April–May sunshine (Kochi 18.4 vs 19.9 MJ/m² per day in winter), the same reason Kochi's winter surface is slightly warmer than its pre-monsoon one.

*Sources:* `data/samples/*.csv` (`height`), `data/results/height_log.csv`, `data/results/city_solar.csv`.
