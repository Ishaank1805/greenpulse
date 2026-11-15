#!/bin/bash
#SBATCH --job-name=greenpulse-r5-final
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=00:40:00
#SBATCH --output=r5-final-%j.out
#SBATCH --error=r5-final-%j.err
set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
source .venv/bin/activate
export MPLBACKEND=Agg
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=2

echo '=== Updated H6 checks: >=10 blocks ==='
python -u scripts/19_new_checks.py
echo '=== Real water-square exclusion/refits ==='
python -u scripts/22_water_square_exclusion.py
echo '=== All Role 5 tests ==='
python -m unittest discover -s tests -p 'test_role5.py' -v
echo '=== Save verified observations and handoff ==='
python scripts/23_finalize_role5.py
echo '=== ROLE 5 OFFLINE WORK COMPLETED (height depends on Johar) ==='
