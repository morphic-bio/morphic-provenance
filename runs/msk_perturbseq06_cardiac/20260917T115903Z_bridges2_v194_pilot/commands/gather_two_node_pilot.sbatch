#!/usr/bin/env bash
#SBATCH --job-name=msk-cardiac-gather
#SBATCH --account=bio230034p
#SBATCH --partition=RM-shared
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --output=/ocean/projects/bio230034p/lhung2/msk-perturbseq06-cardiac-20260917/logs/%x-%j.out
#SBATCH --error=/ocean/projects/bio230034p/lhung2/msk-perturbseq06-cardiac-20260917/logs/%x-%j.err

set -euo pipefail

script_dir="${PROVENANCE_COMMANDS_DIR:-/ocean/projects/bio230034p/lhung2/msk-perturbseq06-cardiac-20260917/provenance/commands}"
source "${script_dir}/common.sh"

validate_python
"${PYTHON_BIN}" "${script_dir}/gather_pilot_results.py" \
  --pilot-root "${RESULT_ROOT}/pilot_nodes" \
  --host bridges2 \
  --require-distinct-nodes \
  --output "${RESULT_ROOT}/pilot_nodes/PILOT_GATHER.json"
