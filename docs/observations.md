# Observations

One sentence per finding, with numbers and the CSV it comes from. Associations, not causes. Write only under your own role's heading. Role 4 turns these into the Observations slide.

Slide deck (Google Slides): [https://docs.google.com/presentation/d/1EnrZBA81aB5Bg3Xh8cWKhd4n5jQbhlmhK1_tqBOnO0I](https://docs.google.com/presentation/d/1EnrZBA81aB5Bg3Xh8cWKhd4n5jQbhlmhK1_tqBOnO0I/edit?usp=sharing)

## Role 1 (sampling)

Sources: `data/results/b2_checks.csv`, `data/results/run_log.csv`, `data/samples/*.csv`.

- **All 303 cities were sampled in 3 seasons with no failures:** 53,614 squares of 1 km, of which 26,341 are urban (built ≥ 10%) with a daytime temperature. 202 cities have at least 30 such squares.
- **Sampling matches the grid:** the median city has exactly the number of squares its area predicts (ratio 1.00), and the pre-monsoon values reproduce the Jodhpur/Kochi pilot exactly.
- **Cloud thins the data but rarely empties a square.** The median city has a clear daytime image 98% of the time before the monsoon, 95% after it and 94% in winter. Each season has its own cloudy region: Kerala before the monsoon (Kottayam 46%), Tamil Nadu after it (Viluppuram 37%), and the Gangetic plain in winter (Jaunpur 60%, likely fog).
- **Squares with no temperature are water, not cloud:** the missing share is identical in all three seasons in every city (worst Vadakara 19%, Thalassery 18%, Mangaluru 17%, all coastal).
- **Seasons differ strongly overall but not everywhere:** the median square is 39.7 °C by day before the monsoon, 31.2 °C after it and 27.9 °C in winter. In Kochi, winter (34.1 °C) is slightly warmer than pre-monsoon (33.7 °C), because Kerala's April–May is already wet. Role 2's `city_climate.csv` can confirm the rainfall.
- **Hill cities reach sub-zero surfaces:** winter night surface temperature falls to −12.8 °C (Khansahib), −7.9 °C (Kralpora) and −6.5 °C (Srinagar) in the Kashmir valley, at 1,600–2,000 m. These were flagged by the range checks and confirmed as real.

## Role 2 (climate)

## Role 3 (pilot, seasons, robustness)

## Role 4 (exposure)

Source: `data/results/exposure.csv`. 202 cities with ≥ 30 urban squares (built ≥ 10%).

- **Crowded squares are less green almost everywhere.** People-weighted NDVI is below the area average in 90% (pre), 95% (post) and 96% (winter) of 202 cities.
- **At night, people live in hotter squares in almost every city:** 96% (pre, n = 135), 96% (post, n = 141) and 97% (winter, n = 157). The median gap is +0.18 to +0.22 °C. Humid cities are under-represented at night because of cloud.
- **By day, the pattern is weaker and depends on season:** people live in hotter squares in 63% (pre), 87% (post) and 73% (winter) of cities. The median gap is +0.09, +0.18 and +0.12 °C.
- **The pre-monsoon exceptions include hot, dry-season cities.** Among the 20 largest, people live in *cooler*-than-average squares in Jaipur, Nagpur, Indore, Pune, Surat, Mumbai and Kozhikode. This matches the pilot, where bare outskirts heat up more than the city by day (Jodhpur). It is not yet tested by rainfall; that needs Role 2's `city_climate.csv`.
- **Gaps are small on average** (tenths of a degree) **but reach about 1 °C** in some cities (Kolkata +1.08 °C pre-monsoon day). Kolkata is also the city where crowded squares are least green (−0.05 NDVI).
- **Comparison with the literature:** Chakraborty et al. 2019 found poorer neighbourhoods hotter in 72% of 25 cities, using surface temperature. We use population density, not income, so we can say "more crowded squares", not "poorer". Our 63–87% by day is in the same range.

## Role 5 (water and data quality)
