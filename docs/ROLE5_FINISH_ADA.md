# Finish Role 5 on ADA (Termius) without the final presentation

This update is intended to be **extracted on top of the existing GreenPulse repository** that already contains the previous Role 5 code-only ZIP, all samples, water maps, and H6 outputs. The update intentionally does **not** contain or overwrite the shared `docs/observations.md` document; the finalization script updates only the marked Role 5 section.

## Why this update

The final submission plan asks for sensitivity checks on **cities with at least 10 spatial blocks** and **excluding water squares**. The earlier Role 5 implementation used only the older >5-block rule and water-**city** filtering. Both have been preserved as secondary comparisons, but the missing checks now run separately.

## Files added or changed

- `scripts/19_new_checks.py` (updated): adds `n_blocks_ge_10` to H6 and the pending height analysis. Retains `n_blocks_gt_5` as a legacy check.
- `scripts/22_water_square_exclusion.py` (new): refits pre-monsoon daytime slopes with the original `03_cooling_efficiency.py` estimator after excluding mapped-water **squares**. It tests water fractions >0% and >5%; validates original unfiltered slopes, recomputes the H6 scenario with `15_felt_heat.py`, and compares matched cooling cities (and matched ≥10-block cities).
- `scripts/23_finalize_role5.py` (new): reads actual CSV results, inserts an idempotent, marked Role 5 subsection in `docs/observations.md`, and writes `docs/ROLE5_FINAL_HANDOFF.md`. It does not invent missing height results.
- `tests/test_role5.py` (updated): 8 regression/unit tests.
- `run_role5_finish.sbatch` (new): one Slurm CPU job for the remaining offline analyses, tests and observations.
- `run_role5_height.sbatch` (new): strict final job to use only when Johar delivers the real height file.

## Termius / ADA steps

1. In Termius **SFTP**, upload `greenpulse_role5_finish_patch.zip` to `/home2/nidhiv/`. Your previous `greenpulse_role5_code_only.zip` should already have been extracted into `~/greenpulse_role5_run/greenpulse-main/`.
2. In the SSH terminal, extract the update **into that same folder**, not into a new nested folder:

   ```bash
   unzip -o ~/greenpulse_role5_finish_patch.zip -d ~/greenpulse_role5_run/greenpulse-main
   ```

3. Change to the repository, then submit the CPU job:

   ```bash
   cd ~/greenpulse_role5_run/greenpulse-main
   sbatch run_role5_finish.sbatch
   ```

4. Find your job number and read the log after it finishes:

   ```bash
   squeue -u "$USER"
   tail -n 50 "$(ls -t r5-final-*.out | head -1)"
   tail -n 40 "$(ls -t r5-final-*.err | head -1)"
   ```

5. Outputs and documentation will be in:
   - `data/results/new_checks.csv` (includes the ≥10-block H6 checks)
   - `data/results/role5_dry_square_city_slopes.csv` (city-level refit details)
   - `data/results/role5_water_square_checks.csv` (matched-cities H6 correlations)
   - `docs/observations.md` (only the Role 5 managed block is updated)
   - `docs/ROLE5_FINAL_HANDOFF.md` (the up-to-date handoff)
   - `figures/R5_h6_checks.png` (includes the ≥10-block variant)
   - `role5_handoff_bundle.zip` (all Role 5 scripts, outcomes, figures and updated docs to download via Termius SFTP; merge `docs/observations.md` with teammates rather than overwriting a newer version)

6. After Johar delivers `height_effect.csv`, put it in `data/results/` and rerun the height checks and observations. Use these commands **only after the file exists**:

   ```bash
   cd ~/greenpulse_role5_run/greenpulse-main
   sbatch run_role5_height.sbatch
   ```

**Do not overwrite or redo other teammates' work**: do not rerun `03_cooling_efficiency.py` on the full dataset, or modify `cooling_efficiency.csv` / `felt_heat.csv`. Task 10 outputs are separate sensitivity files.

## Scientific interpretation

- Original H6 efficiency is positively associated with humidity; moisture break-even is negatively associated. Do not claim both are negative.
- The original pre-monsoon scenario has 191 cooling cities; restricting to ≥10 blocks leaves 80.
- Excluding >5% mapped water **squares** leaves 176 matched cooling cities (humidity/efficiency ρ +0.861 before and +0.861 after refit, rounded). Removing **all** nonzero-water squares leaves 137; the association still remains positive.
- The dataset supports **observational** cooling slopes and **modelled** Heat Index scenarios, not causal greening effects or measured perceived temperatures.
- The height result cannot be declared complete before Johar's actual file is received and checked.
