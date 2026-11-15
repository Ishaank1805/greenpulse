#!/bin/bash
#SBATCH --job-name=greenpulse-r5-height
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=00:20:00
#SBATCH --output=r5-height-%j.out
#SBATCH --error=r5-height-%j.err
set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
source .venv/bin/activate
export MPLBACKEND=Agg
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=2

if [[ ! -f data/results/height_effect.csv ]]; then
  echo 'ERROR: waiting for Johar: data/results/height_effect.csv not found' >&2
  exit 2
fi
python scripts/19_new_checks.py --require-height
python -m unittest discover -s tests -p 'test_role5.py' -v
python scripts/23_finalize_role5.py --require-height
echo '=== ROLE 5 HEIGHT CHECKS COMPLETED ==='
