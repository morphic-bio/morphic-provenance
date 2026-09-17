#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${script_dir}/common.sh"

mkdir -p "${RUN_ROOT}/logs" "${RESULT_ROOT}"
bash "${script_dir}/prepare_inputs.sh"

build_job="$(sbatch --parsable "${script_dir}/build_star_v194.sbatch")"
mapfile -t pilot_nodes < <(
  sinfo -h -N -p RM-shared -o '%N|%C|%e|%T' \
    | sort -u \
    | awk -F '|' '
        ($4 == "idle" || $4 == "mixed") {
          split($2, cpu, "/")
          if (cpu[2] >= 64 && $3 >= 122880) print $1
        }
      ' \
    | sed -n '1,2p'
)
if [[ "${#pilot_nodes[@]}" -ne 2 || "${pilot_nodes[0]}" == "${pilot_nodes[1]}" ]]; then
  echo "FATAL: could not select two distinct idle RM-shared nodes" >&2
  exit 1
fi

pilot_r1_job="$(sbatch --parsable --dependency="afterok:${build_job}" \
  --array=0 --nodelist="${pilot_nodes[0]}" "${script_dir}/run_two_capture_pilot.sbatch")"
pilot_r2_job="$(sbatch --parsable --dependency="afterok:${build_job}" \
  --array=1 --nodelist="${pilot_nodes[1]}" "${script_dir}/run_two_capture_pilot.sbatch")"
gather_job="$(sbatch --parsable \
  --dependency="afterok:${pilot_r1_job}:${pilot_r2_job}" \
  "${script_dir}/gather_two_node_pilot.sbatch")"

cat > "${PROVENANCE_ROOT}/outputs/pilot_submission.json" <<EOF
{
  "submitted_utc": "$(date -u +%FT%TZ)",
  "build_job": "${build_job}",
  "pilot_cp_r1_job": "${pilot_r1_job}",
  "pilot_cp_r2_job": "${pilot_r2_job}",
  "pilot_array": "two one-element submissions: 0 and 1",
  "pilot_captures": ["CP_R1", "CP_R2"],
  "pilot_nodes": ["${pilot_nodes[0]}", "${pilot_nodes[1]}"],
  "gather_job": "${gather_job}",
  "production_submitted": false,
  "zshard_used": false
}
EOF

cat "${PROVENANCE_ROOT}/outputs/pilot_submission.json"
