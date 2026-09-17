#!/usr/bin/env bash
set -euo pipefail

readonly scheduler_root="/mnt/pikachu/temporal-scheduler-cardiac-pipeline-20260917"
readonly run_root="/mnt/pikachu/morphic-provenance-card-prod/runs/msk_perturbseq06_cardiac/20260917T193023Z_temporal_staged_pilot"
readonly python="${scheduler_root}/.venv/bin/python"
readonly worker="${scheduler_root}/bwb/scheduling_service/worker.py"
readonly temporal_endpoint="localhost:7233"
readonly path_env="/home/lhhung/.local/bin:/usr/local/bin:/usr/bin:/bin"

start_unit() {
  local unit="$1"
  shift
  systemd-run --user --unit "${unit}" --collect \
    --property=Restart=on-failure \
    --property=RestartSec=5 \
    --working-directory="${scheduler_root}" \
    --setenv="TEMPORAL_ENDPOINT_URL=${temporal_endpoint}" \
    --setenv="PATH=${path_env}" \
    "$@"
}

start_unit cardiac-temporal-control-20260917T193023Z \
  "${python}" "${worker}" staged-pipeline --config "${run_root}/commands/worker_config.json"
start_unit cardiac-temporal-slurm-20260917T193023Z \
  "${python}" "${worker}" slurm --config "${run_root}/commands/site_config.json"
start_unit cardiac-temporal-gpu-20260917T193023Z \
  "${python}" "${worker}" ssh-docker --config "${run_root}/commands/site_config.json"
start_unit cardiac-temporal-api-20260917T193023Z \
  "${python}" -m uvicorn bwb.scheduling_service.main:app --host 127.0.0.1 --port 8010

systemctl --user --no-pager --full status \
  cardiac-temporal-control-20260917T193023Z.service \
  cardiac-temporal-slurm-20260917T193023Z.service \
  cardiac-temporal-gpu-20260917T193023Z.service \
  cardiac-temporal-api-20260917T193023Z.service
