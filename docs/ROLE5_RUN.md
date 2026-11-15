# Role 5 final implementation: required task + two additional experiments

All files work **offline** with the GreenPulse repository CSVs; no Earth Engine, Overpass, credentials, or changes to the original cooling model are needed. Run from the **root of the repository**, not from `scripts/`.

## What is implemented

1. **Required:** `scripts/19_new_checks.py` computes pre-monsoon H6 Spearman checks vs humidity for all eligible cooling cities; excludes small-block and high-**median**-water cities; recomputes H6 with the **no-water** slope by importing Ishaan's original `hi_change` and `delta_star` functions. It cross-checks the baseline against `felt_heat_test.csv`. It also runs height checks (positive significant interaction and tall-minus-low median) when Johar adds `data/results/height_effect.csv`.
2. **Extra A:** `scripts/20_water_sensitivity.py` matches each city's slope before and after adding OSM water, for each season/day/night. It reports the **median paired change**, bootstrap CI, Wilcoxon test, and correlation of **absolute** change with mean mapped water share. Outputs 6 summaries and a city detail table.
3. **Extra B:** `scripts/21_night_selection_bias.py` compares climates of cities with and without valid nighttime cooling slopes among cities that have valid daytime estimates. It reports sample sizes, descriptive comparisons, Mann-Whitney tests, and a logistic model adjusting for day sample count (estimated association only).
4. `scripts/role5_utils.py` implements robust CSV loading, main-spec reuse, OSM city summaries, city bootstrap, and Spearman helpers. `tests/test_role5.py` contains five offline tests, including a **synthetic** height-file test.

## Step by step (Windows PowerShell)

**Step 1 - Install required libraries.** Use pip for these *local CSV analysis* scripts; installing the full project's Earth Engine/geospatial stack is unnecessary if you only need Role 5.

```powershell
python -m pip install numpy pandas scipy statsmodels matplotlib
```

**Step 2 - Add the patch.** Extract `greenpulse_role5_patch.zip` **into the root folder** of `greenpulse-main` (the same folder containing `README.md`), merging `scripts/`, `docs/`, `figures/`, `tests/`, and `data/results/`. Keep your existing samples and water files.

**Step 3 - Run the assigned H6 and height robustness checks.** The script reads the committed inputs and writes `new_checks.csv` and `R5_h6_checks.png`. Missing height input is warned about and skipped; do not invent Johar's results.

```powershell
python scripts/19_new_checks.py
```

**Step 4 - Run additional experiment A (water sensitivity).** Produces a paired city-level CSV, six-panel summary CSV, and a figure.

```powershell
python scripts/20_water_sensitivity.py
```

**Step 5 - Run additional experiment B (night missingness).** Produces retained-versus-missing city CSV, three-season summary, and a figure.

```powershell
python scripts/21_night_selection_bias.py
```

**Step 6 - Run automated checks.** Uses Python's standard `unittest` runner; no pytest dependency.

```powershell
python -m unittest discover -s tests -p "test_role5.py" -v
```

**Step 7 - When Johar sends `height_effect.csv`, rerun and require height.** Put the received file at `data/results/height_effect.csv` and run with `--require-height` to prohibit accidentally submitting H6-only checks.

```powershell
python scripts/19_new_checks.py --require-height
```

**Step 8 - Share the results.** Commit `scripts/role5_utils.py`, `scripts/19_new_checks.py`, `scripts/20_water_sensitivity.py`, `scripts/21_night_selection_bias.py`, the five-test file, the new Role 5 CSVs and three figures. Do not commit temporary synthetic test files. The height results must be rerun and reviewed before claims about the height interaction.

## Files produced

| File | Purpose |
|---|---|
| `data/results/new_checks.csv` | Required H6/height checks: `analysis, variant, n_cities, statistic, value, note` |
| `figures/R5_h6_checks.png` | H6 sensitivity side-by-side |
| `data/results/role5_water_city_shifts.csv` | Paired within-city slope differences, all seasons and times |
| `data/results/role5_water_sensitivity.csv` | Six city-level experiment summaries |
| `figures/R5_water_sensitivity.png` | Differences vs mean mapped water |
| `data/results/role5_night_city_selection.csv` | Nighttime retention indicators and city covariates |
| `data/results/role5_night_selection.csv` | Seasonal missingness comparisons, adjusted OR |
| `figures/R5_night_selection.png` | Humidity distributions of retained/missing cities |

## Checks and scientific cautions

- **The main cooling specification stays the same:** NDVI, built-up ≥ 0.10, `built_elev_water`, via `common.main_spec`. The only intentional alternative is `built_elev` for a robustness check.
- The pre/day all-city H6 Spearman coefficients are independently verified against Ishaan's `felt_heat_test.csv` to numerical precision. **H6 is a scenario, not measured air cooling.** It assumes ratios from European studies and a NOAA heat-index formula.
- Only cities with **negative** daytime slopes enter the H6 efficiency and break-even test (191 cities in the current data). The no-water alternative has a slightly different city set; the CSV also includes common-city comparisons.
- The **plan-prescribed median-water > 0.05 filter excludes 0 of those 191 cities**. A supplemental **mean-water > 0.05** filter excludes 15, giving a real stress test. Do not present the median filter as evidence of general robustness by itself.
- **Do not confuse** the difference of two group medians with the **median of paired within-city differences**; these are different estimands. The new water experiment explicitly reports both.
- The 95% bootstrap interval describes cross-city variation under resampling; it does not establish causal effects or fix spatial confounding.
- The night selection analysis is conditional on cities with a valid **daytime** slope (202), not all 303 originally sampled cities. The nighttime selection mechanism includes the >=30-cell requirement; it is not a pure cloud-only diagnostic. Logistic results are exploratory, with three seasonal tests; avoid strong claims from one nominal p-value.
- If the height file uses a schema different from the one frozen in `docs/roles/README.md`, stop and reconcile with Johar instead of guessing. `interaction` is assessed separately from the `tall-low` slope difference.
- Original weather/NDVI LST slopes are **observational associations**, not causal treatment effects. All new conclusions inherit this limit.

## Slide and speaking material

See `docs/ROLE5_SLIDES_AND_SCRIPT.md`. The final deck is not included in the upload, so these are ready-to-transfer content and timing, rather than a purported edit of the team's existing PowerPoint. Make sure the final H6 and height figures from the relevant team members are available before the 25-minute rehearsal.
