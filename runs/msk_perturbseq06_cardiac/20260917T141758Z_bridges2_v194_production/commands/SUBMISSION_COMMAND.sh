#!/usr/bin/env bash

set -euo pipefail

# Superseded first submission; array 46249747 failed in task 0 and dependent
# validator 46250387 was canceled.
sbatch --parsable \
  /ocean/projects/bio230034p/lhung2/msk-perturbseq06-cardiac-20260917/provenance/commands/run_cardiac_production_array.sbatch

# Corrected CP_A1 gate and remaining captures.
sbatch --parsable --array=0 \
  /ocean/projects/bio230034p/lhung2/msk-perturbseq06-cardiac-20260917/provenance-production/20260917T141758Z_bridges2_v194_production/commands/run_cardiac_production_array_v2.sbatch

sbatch --parsable --array=1-7%1 --dependency=afterok:46251625 \
  /ocean/projects/bio230034p/lhung2/msk-perturbseq06-cardiac-20260917/provenance-production/20260917T141758Z_bridges2_v194_production/commands/run_cardiac_production_array_v2.sbatch

sbatch --parsable --dependency=afterok:46251625:46251626 \
  /ocean/projects/bio230034p/lhung2/msk-perturbseq06-cardiac-20260917/provenance-production/20260917T141758Z_bridges2_v194_production/commands/gather_cardiac_production.sbatch

# Exact stale scratch paths from the failed/canceled tasks only.
sbatch --parsable --job-name=clean-msk-r225 --nodelist=r225 --nodes=1 \
  --ntasks=1 --cpus-per-task=1 --mem=1900M --time=00:05:00 \
  --output=/ocean/projects/bio230034p/lhung2/msk-perturbseq06-cardiac-20260917/logs/cleanup-r225-%j.out \
  --wrap='set -euo pipefail; d=/local/msk-cardiac-cp_a1-46249925; if [[ -e $d ]]; then du -sh $d; rm -rf -- $d; fi; test ! -e $d; echo CLEANED:$d'

sbatch --parsable --job-name=clean-msk-r203 --nodelist=r203 --nodes=1 \
  --ntasks=1 --cpus-per-task=1 --mem=1900M --time=00:05:00 \
  --output=/ocean/projects/bio230034p/lhung2/msk-perturbseq06-cardiac-20260917/logs/cleanup-r203-%j.out \
  --wrap='set -euo pipefail; d=/local/msk-cardiac-cp_a2-46251382; if [[ -e $d ]]; then du -sh $d; rm -rf -- $d; fi; test ! -e $d; echo CLEANED:$d'
