#!/usr/bin/env bash
set -euo pipefail

readonly run_record="/mnt/pikachu/morphic-provenance-card-prod/runs/msk_perturbseq06_cardiac/20260917T193023Z_temporal_staged_pilot"
readonly scheduler_root="/mnt/pikachu/temporal-scheduler-cardiac-pipeline-20260917"
readonly local_root="/mnt/pikachu/MSK_Perturbseq06_Cardiac_temporal_pilot_20260917T193023Z"
readonly ocean_root="/ocean/projects/bio230034p/lhung2/temporal-cardiac-pilot-20260917T193023Z"
readonly globus="/home/lhhung/.local/bin/globus"
readonly pikachu_endpoint="07446cad-33b8-11f0-8c0c-0afffb017b7d"
readonly bridges_endpoint="d9e522d3-c51e-4037-b375-55ffd155c715"

mkdir -p "${run_record}/outputs"
exec > >(tee "${run_record}/outputs/preflight.log") 2>&1

[[ "$(git -C "${scheduler_root}" rev-parse HEAD)" == "a4fdc15b38766b9e3c4ecfc16c12dd68ba40b1b4" ]]
test -z "$(git -C "${scheduler_root}" status --porcelain)"
test -x "${scheduler_root}/.venv/bin/python"
curl --fail --silent http://127.0.0.1:8080 >/dev/null
timeout 2 bash -c '</dev/tcp/127.0.0.1/7233'

[[ "$("${globus}" endpoint local-id)" == "${pikachu_endpoint}" ]]
"${globus}" ls "${pikachu_endpoint}:/mnt/pikachu/MSK_Perturbseq06_Cardiac_pilot_inputs_20260917/" >/dev/null
"${globus}" ls "${bridges_endpoint}:/ocean/projects/bio230034p/lhung2/" >/dev/null

test ! -e "${local_root}"
if ssh bridges2.psc.edu "test -e '${ocean_root}'"; then
  echo "FATAL: Ocean pilot root already exists: ${ocean_root}" >&2
  exit 1
fi
mkdir -p "${local_root}" "${run_record}/outputs/runtime"
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
df -h /storage /mnt/pikachu

printf 'preflight_status=PASS\ncompleted_utc=%s\n' "$(date -u +%FT%TZ)"
