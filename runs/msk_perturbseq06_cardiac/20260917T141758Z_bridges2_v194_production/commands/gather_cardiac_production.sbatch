#!/usr/bin/env bash
#SBATCH --job-name=msk-cardiac-validate
#SBATCH --account=bio230034p
#SBATCH --partition=RM-shared
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --output=/ocean/projects/bio230034p/lhung2/msk-perturbseq06-cardiac-20260917/logs/%x-%j.out
#SBATCH --error=/ocean/projects/bio230034p/lhung2/msk-perturbseq06-cardiac-20260917/logs/%x-%j.err

set -euo pipefail

readonly PILOT_COMMANDS="/ocean/projects/bio230034p/lhung2/msk-perturbseq06-cardiac-20260917/provenance/commands"
readonly PRODUCTION_COMMANDS="/ocean/projects/bio230034p/lhung2/msk-perturbseq06-cardiac-20260917/provenance-production/20260917T141758Z_bridges2_v194_production/commands"
source "${PILOT_COMMANDS}/common.sh"

validate_python
validate_reference
validate_assay_references
validate_star_binary
"${PYTHON_BIN}" "${PRODUCTION_COMMANDS}/validate_cardiac_production.py" \
  --production-root "${RESULT_ROOT}/production" \
  --tru-whitelist "${GEX_WHITELIST}" \
  --output "${RESULT_ROOT}/production/PRODUCTION_GATHER.json"
