#!/usr/bin/env bash
set -euo pipefail

readonly run_stamp="20260918T213950Z"
readonly unit_prefix="msk-cardiac-workbench-${run_stamp}"
readonly run_root="/mnt/pikachu/morphic-provenance-msk-temporal-workbench/runs/msk_perturbseq06_cardiac/${run_stamp}_temporal_workbench_pilot"
readonly scheduler_root="/mnt/pikachu/temporal-scheduler-cardiac-pipeline-20260917"
readonly adapter_root="/mnt/pikachu/bwb-nextflow-utils-staged-recipe-20260918"
readonly scheduler_python="${scheduler_root}/.venv/bin/python"
readonly workbench_python="/mnt/pikachu/.venvs/bwb-workbench-staged/bin/python"
readonly worker="${scheduler_root}/bwb/scheduling_service/worker.py"
readonly temporal_endpoint="localhost:7233"
readonly path_env="/home/lhhung/.local/bin:/usr/local/bin:/usr/bin:/bin"

start_unit() {
  local unit="$1"
  local working_directory="$2"
  shift 2
  systemd-run --user --unit "${unit_prefix}-${unit}" --collect \
    --property=Restart=on-failure \
    --property=RestartSec=5 \
    --working-directory="${working_directory}" \
    --setenv="TEMPORAL_ENDPOINT_URL=${temporal_endpoint}" \
    --setenv="PATH=${path_env}" \
    "$@"
}

start_unit control "${scheduler_root}" \
  "${scheduler_python}" "${worker}" staged-pipeline --config "${run_root}/commands/worker-config.json"
start_unit slurm "${scheduler_root}" \
  "${scheduler_python}" "${worker}" slurm --config "${run_root}/commands/site-config.json"
start_unit gpu "${scheduler_root}" \
  "${scheduler_python}" "${worker}" ssh-docker --config "${run_root}/commands/site-config.json"
start_unit scheduler-api "${scheduler_root}" \
  "${scheduler_python}" -m uvicorn bwb.scheduling_service.main:app --host 127.0.0.1 --port 8010
start_unit workbench "${adapter_root}" \
  "${workbench_python}" -m uvicorn tools.web.app:app --host 128.208.252.233 --port 8894

systemctl --user --no-pager --full status \
  "${unit_prefix}-control.service" \
  "${unit_prefix}-slurm.service" \
  "${unit_prefix}-gpu.service" \
  "${unit_prefix}-scheduler-api.service" \
  "${unit_prefix}-workbench.service"

"${run_root}/commands/print_workbench_url.py"
