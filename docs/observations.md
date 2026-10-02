# Observations

One sentence per finding, with numbers and the CSV it comes from. Associations, not causes. Write only under your own role's heading. Role 4 turns these into the Observations slide.

Slide deck: *(link to be added)*

## Role 1 (sampling)

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
