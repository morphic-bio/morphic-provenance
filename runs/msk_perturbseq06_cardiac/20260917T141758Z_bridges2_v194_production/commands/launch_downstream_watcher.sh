#!/usr/bin/env bash

set -euo pipefail

readonly RUN_ID="20260917T141758Z_bridges2_v194_production"
readonly PROVENANCE_ROOT="/mnt/pikachu/morphic-provenance-card-prod/runs/msk_perturbseq06_cardiac/${RUN_ID}"
readonly PIPELINE_ROOT="/mnt/pikachu/MSK_Perturbseq06_Cardiac_20260917"
readonly LOG="${PIPELINE_ROOT}/logs/downstream_orchestrator.log"
readonly PID_FILE="${PIPELINE_ROOT}/downstream_orchestrator.pid"

mkdir -p "${PIPELINE_ROOT}/logs"
nohup python3 "${PROVENANCE_ROOT}/commands/run_ocean_gpu_h5ad_pipeline.py" \
  --ocean-run-root /ocean/projects/bio230034p/lhung2/msk-perturbseq06-cardiac-20260917 \
  --local-root "${PIPELINE_ROOT}" \
  --recipes-root /mnt/pikachu/morphic-recipes-msk-cardiac-e27f174 \
  --bridges-host bridges2 \
  --gpu-host 10.159.4.53 \
  --gpu-root /tmp/msk_perturbseq06_cardiac_cellbender \
  --gpu-slots 0,1 \
  --poll-seconds 60 \
  --max-wait-hours 240 \
  --min-free-gib 1024 \
  >> "${LOG}" 2>&1 < /dev/null &
pid=$!
printf '%s\n' "${pid}" > "${PID_FILE}"
printf 'pid=%s\nlog=%s\n' "${pid}" "${LOG}"
