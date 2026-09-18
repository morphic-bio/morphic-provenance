#!/usr/bin/env bash
set -euo pipefail

readonly run_stamp="20260918T213950Z"
readonly run_root="/mnt/pikachu/morphic-provenance-msk-temporal-workbench/runs/msk_perturbseq06_cardiac/${run_stamp}_temporal_workbench_pilot"
readonly scheduler_root="/mnt/pikachu/temporal-scheduler-cardiac-pipeline-20260917"
readonly adapter_root="/mnt/pikachu/bwb-nextflow-utils-staged-recipe-20260918"
readonly local_root="/mnt/pikachu/MSK_Perturbseq06_Cardiac_temporal_workbench_${run_stamp}"
readonly ocean_root="/ocean/projects/bio230034p/lhung2/temporal-cardiac-workbench-${run_stamp}"
readonly globus="/home/lhhung/.local/bin/globus"
readonly pikachu_endpoint="07446cad-33b8-11f0-8c0c-0afffb017b7d"
readonly bridges_endpoint="d9e522d3-c51e-4037-b375-55ffd155c715"

exec > >(tee "${run_root}/logs/runtime-preflight.log") 2>&1

test -x "${scheduler_root}/.venv/bin/python"
test -x "/mnt/pikachu/.venvs/bwb-workbench-staged/bin/python"
test -s "${adapter_root}/tools/web_react/dist/index.html"
test -s "${run_root}/outputs/workbench-bundle.json"
jq -e '.status == "ready"' "${run_root}/outputs/preflight.json" >/dev/null
jq -e '.status == "PASS" and .cellbender_cuda == true and .slurm_cpus == 32' \
  "${run_root}/outputs/validation.json" >/dev/null

timeout 2 bash -c '</dev/tcp/127.0.0.1/7233'
curl --fail --silent http://127.0.0.1:8080 >/dev/null
[[ "$("${globus}" endpoint local-id)" == "${pikachu_endpoint}" ]]
"${globus}" ls "${pikachu_endpoint}:/mnt/pikachu/MSK_Perturbseq06_Cardiac_pilot_inputs_20260917/" >/dev/null
"${globus}" ls "${bridges_endpoint}:/ocean/projects/bio230034p/lhung2/" >/dev/null

test ! -e "${local_root}"
if ssh bridges2.psc.edu "test -e '${ocean_root}'"; then
  echo "FATAL: Ocean workbench root already exists: ${ocean_root}" >&2
  exit 1
fi
mkdir -p "${local_root}" "${run_root}/logs"
ssh bridges2.psc.edu \
  "mkdir -p '${ocean_root}/input' '${ocean_root}/results' '${ocean_root}/scheduler/slurm' '${ocean_root}/scheduler/tmp'"

ssh bridges2.psc.edu "
  set -e
  test -s /ocean/projects/bio230034p/shared/processing/references/GRCh38-2024-A-star-msk30/Genome
  test -s /ocean/projects/bio230034p/shared/processing/references/MSK_Perturbseq_LEG/3M-february-2018_TRU.txt
  test -s /ocean/projects/bio230034p/shared/processing/references/MSK_Perturbseq_LEG/3M-february-2018_NXT.txt
  test -s /ocean/projects/bio230034p/shared/processing/references/MSK_Perturbseq_LEG/MSK_LEG_star_suite_feature_reference.csv
  test \"\$(/ocean/projects/bio230034p/shared/processing/tools/star-suite-v1.9.4/bin/STAR --version)\" = 1.9.4
  command -v sbatch
  command -v sacct
"

docker image inspect biodepot/cellbender:0.3.2 --format '{{.Id}}'
docker run --rm --gpus device=0 biodepot/cellbender:0.3.2 \
  python -c 'import torch; assert torch.cuda.is_available(); print(torch.cuda.get_device_name(0))'
nvidia-smi --query-gpu=index,name,memory.total,memory.free --format=csv,noheader,nounits

printf 'runtime_preflight=PASS\ncompleted_utc=%s\n' "$(date -u +%FT%TZ)"
