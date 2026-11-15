# Role 5 final handoff (outside presentation)

This report is generated from local results by `scripts/23_finalize_role5.py`.

**Height check:** COMPLETE (review against Johar’s numbers before presenting).

## Verified findings

**Final-phase robustness (verified from CSVs):**
- **H6 (scenario, not measured felt heat):** Pre-monsoon +0.1 NDVI, fixed dewpoint, r=0.08. Across 191 greener-is-cooler cities, humidity correlates positively with felt-heat efficiency (Spearman ρ=+0.865) and negatively with break-even dewpoint rise (ρ=-0.403). Restricting to ≥10 spatial blocks leaves 80 cities (ρ=+0.875 and -0.523, respectively). The efficiency direction contradicts the original H6 expectation, while break-even fragility supports it.
- **Actual exclusion of water-covered squares:** Refitting the pre-monsoon NDVI slope after excluding squares with >5% OSM mapped water retains 176 matched cooling cities. Humidity-efficiency ρ changes +0.861 → +0.861; humidity-break-even ρ changes -0.410 → -0.390. The ≥10-block restricted comparison contains 80 cities (restricted efficiency ρ=+0.875). An even stricter exclusion of all positive mapped water gives 137 matched cities (ρ=+0.827 → +0.826). This is a separate within-city refit; excluding entire high-water cities is not the same test.
- **City-level water sensitivity:** The mean-water >5% city exclusion retains 176 H6 cities; the median-water >5% city exclusion excludes none. Adding water to the city-level LST regression changes the median paired pre-monsoon daytime slope by -0.0074 °C per 0.1 NDVI (bootstrap 95% interval -0.0196 to -0.0001). Absolute slope shifts are associated with mean mapped water (Spearman ρ=+0.472), without a causal interpretation.
- **Nighttime selection check:** Of 202 pre-monsoon daytime-estimable cities, only 135 also have usable nighttime slopes. An exploratory model adjusting for daytime sample count gives an odds ratio 0.91 per +10 percentage points RH (95% CI 0.72–1.17; p=0.47); there is no clear adjusted humidity association. This tests sample availability, not a pure cloud-only mechanism.
- **Building-height check (Johar input received):** 69 paired pre-monsoon daytime cities; significantly positive interaction share 18.8%, median tall-minus-low +0.064 °C per 0.1 NDVI. Among ≥10-block cities (n=65), positive-share 16.9%. Confirm the all-city definition matches Johar’s own headline before presenting the comparison.

**Interpretation:** LST slopes are observational cross-sectional associations; H6 results are modelled Heat Index scenarios based on published conversion ratios and ERA5.

## Files to keep

- `scripts/19_new_checks.py`: original H6 + ≥10 and legacy >5 block checks; height when available
- `scripts/20_water_sensitivity.py`, `scripts/21_night_selection_bias.py`: additional experiments
- `scripts/22_water_square_exclusion.py`: actual removal of water-containing squares and refit
- `scripts/23_finalize_role5.py`: safe observation/handoff update
- `data/results/new_checks.csv`, `role5_water_sensitivity.csv`, `role5_night_selection.csv`, `role5_dry_square_city_slopes.csv`, `role5_water_square_checks.csv`
- `figures/R5_h6_checks.png`, `figures/R5_water_sensitivity.png`, `figures/R5_night_selection.png`

## Remaining work

- Final presentation and group rehearsal remain.

## Role 5 handoff points

1. The H6 scenario efficiency/humidity association stays positive under stricter sample quality and dry-square exclusions, contrary to the originally expected direction.
2. More humid cities reach their modelled moisture break-even earlier; the negative correlation survives water-square exclusion.
3. Control-for-water and nighttime selection checks identify possible sources of bias but do not justify causal claims.
