#!/bin/bash
#SBATCH --job-name=greenpulse-r5
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=00:30:00
#SBATCH --output=role5-%j.out
#SBATCH --error=role5-%j.err

set -euo pipefail

cd "$HOME/greenpulse_role5_run/greenpulse-main"
source .venv/bin/activate
export MPLBACKEND=Agg
export OMP_NUM_THREADS=2

echo "========== ROLE 5: REQUIRED CHECKS =========="
python -u scripts/19_new_checks.py

echo "========== EXPERIMENT 1: WATER SENSITIVITY =========="
python -u scripts/20_water_sensitivity.py

echo "========== EXPERIMENT 2: NIGHT SELECTION BIAS =========="
python -u scripts/21_night_selection_bias.py

echo "========== UNIT TESTS =========="
python -m unittest discover -s tests -p "test_role5.py" -v

echo "========== ALL TASKS COMPLETED =========="
