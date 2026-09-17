#!/usr/bin/env bash
#SBATCH --job-name=msk-cardiac-prod
#SBATCH --account=bio230034p
#SBATCH --partition=RM-shared
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=64
#SBATCH --mem=120G
#SBATCH --time=24:00:00
#SBATCH --array=0-7%1
#SBATCH --output=/ocean/projects/bio230034p/lhung2/msk-perturbseq06-cardiac-20260917/logs/%x-%A_%a.out
#SBATCH --error=/ocean/projects/bio230034p/lhung2/msk-perturbseq06-cardiac-20260917/logs/%x-%A_%a.err

set -euo pipefail

script_dir="${PROVENANCE_COMMANDS_DIR:-/ocean/projects/bio230034p/lhung2/msk-perturbseq06-cardiac-20260917/provenance/commands}"
source "${script_dir}/common.sh"

validate_reference
validate_assay_references
validate_star_binary
test -s "${EXECUTION_MANIFEST}"
test -s "${RESULT_ROOT}/pilot_nodes/PILOT_GATHER.json"
grep -q '"status": "PASS"' "${RESULT_ROOT}/pilot_nodes/PILOT_GATHER.json"

capture="${CARDIAC_CAPTURES[${SLURM_ARRAY_TASK_ID}]}"
guide_library_id="grna_${capture,,}"
scratch_base="${LOCAL:-/tmp}"
work="${scratch_base}/msk-cardiac-${capture,,}-${SLURM_JOB_ID}"
gex_dir="${work}/fastqs/gex"
guide_dir="${work}/fastqs/PolyIII"
run_dir="${work}/run"
mkdir -p "${gex_dir}" "${guide_dir}" "${run_dir}"

stage_manifest="${work}/stage.tsv"
awk -F '\t' -v capture="${capture}" -v gex="${gex_dir}" -v guide="${guide_dir}" '
  NR > 1 && $2 == capture && $17 == "true" {
    staged_name = $13
    if ($3 ~ /_gRNA$/ && staged_name ~ /^CP_R2_/) {
      sub(/^CP_R2_/, "CPR2_", staged_name)
    }
    destination = ($3 ~ /_mRNA$/ ? gex : guide) "/" staged_name
    print $14 "\t" destination "\t" $16 "\t" $15 "\t" $13
  }
' "${EXECUTION_MANIFEST}" > "${stage_manifest}"

expected_stage_files="$(awk -F '\t' -v capture="${capture}" 'NR > 1 && $2 == capture && $17 == "true" {n++} END {print n+0}' "${EXECUTION_MANIFEST}")"
[[ "$(wc -l < "${stage_manifest}")" == "${expected_stage_files}" ]]

input_bytes="$(awk -F '\t' '{sum += $4} END {printf "%.0f", sum}' "${stage_manifest}")"
available_bytes="$(df -PB1 "${scratch_base}" | awk 'NR == 2 {print $4}')"
required_bytes="$((input_bytes * 3 + 100 * 1024 * 1024 * 1024))"
if (( available_bytes < required_bytes )); then
  echo "FATAL: insufficient node-local space: required=${required_bytes} available=${available_bytes}" >&2
  exit 1
fi

stage_file() {
  local source="$1"
  local destination="$2"
  local expected_md5="$3"
  reject_zshard_paths "${source}" "${destination}"
  cp "${source}" "${destination}"
  echo "${expected_md5}  ${destination}" | md5sum -c -
  gzip -t "${destination}"
}

pids=()
while IFS=$'\t' read -r source destination expected_md5 size_bytes source_basename; do
  stage_file "${source}" "${destination}" "${expected_md5}" &
  pids+=("$!")
  if (( ${#pids[@]} == 8 )); then
    for pid in "${pids[@]}"; do
      wait "${pid}"
    done
    pids=()
  fi
done < "${stage_manifest}"
for pid in "${pids[@]}"; do
  wait "${pid}"
done

mapfile -t gex_r1_files < <(find "${gex_dir}" -maxdepth 1 -type f -name '*_R1_001.fastq.gz' | sort)
mapfile -t gex_r2_files < <(find "${gex_dir}" -maxdepth 1 -type f -name '*_R2_001.fastq.gz' | sort)
[[ "${#gex_r1_files[@]}" -gt 0 && "${#gex_r1_files[@]}" == "${#gex_r2_files[@]}" ]]

join_by_comma() {
  local IFS=,
  printf '%s' "$*"
}
gex_r1="$(join_by_comma "${gex_r1_files[@]}")"
gex_r2="$(join_by_comma "${gex_r2_files[@]}")"

pf_config="${work}/pf_multi_config.csv"
cat > "${pf_config}" <<EOF
[libraries]
fastqs,sample,library_type,feature_types,star_chemistry,star_whitelist,star_feature_ref,star_library_id,star_max_hamming
${gex_dir},${capture},Gene Expression,Gene Expression,TRU,,,gex_${capture,,},
${guide_dir},${capture},CRISPR Guide Capture,CRISPR Guide Capture,NXT,${GUIDE_WHITELIST},${FEATURE_REF},${guide_library_id},1
EOF

unset STAR_SOLO_NONFLEX_HASH_BRIDGE
export STAR_VELOCYTO_LOW_MEM=1
export STAR_SOLO_BINARY_SPOOL=1

cmd=(
  "${STAR_BIN}"
  --runThreadN 64
  --genomeDir "${GENOME_DIR}"
  --readFilesIn "${gex_r2}" "${gex_r1}"
  --readFilesBgzfMode auto
  --outFileNamePrefix "${run_dir}/"
  --outTmpDir "${work}/tmp_STAR"
  --outSAMtype BAM Unsorted
  --clipAdapterType CellRanger4
  --alignEndsType Local
  --chimSegmentMin 1000000
  --clip3pPolyG yes
  --soloType CB_UMI_Simple
  --soloCBstart 1
  --soloCBlen 16
  --soloUMIstart 17
  --soloUMIlen 12
  --soloBarcodeReadLength 0
  --soloInlineHashMode no
  --soloCBwhitelist "${GEX_WHITELIST}"
  --soloStrand Forward
  --soloFeatures GeneFull Velocyto
  --soloUMIdedup 1MM_CR
  --soloCBmatchWLtype 1MM_multi_Nbase_pseudocounts
  --soloCellFilter EmptyDrops_CR
  --soloUMIfiltering MultiGeneUMI_CR
  --soloMultiMappers Unique
  --soloCbUbRequireTogether no
  --soloCrGexFeature genefull
  --soloCrMultimapRescue yes
  --pfMultiConfig "${pf_config}"
  --crFeatureRef "${FEATURE_REF}"
  --crWhitelist "${GUIDE_WHITELIST}"
  --crChemistry auto
  --crOutputChemistry TRU
  --crMinUmi 2
  --crAssignMaxHamming 1
  --crAssignFeatureOffset -1
  --crAssignLimitSearch -1
  --crAssignMinCounts 0
  --crAssignMaxBarcodeMismatches 5
  --crAssignFeatureN 0
  --crAssignBarcodeN 1
  --crAssignConsumerThreads -1
  --crAssignSearchThreads 1
  --crAssignSkipQcOutputs 0
  --crAssignBgzfMode auto
  --defaultCrCompat yes
  --dynamicThreadInterface 1
  --dynamicThreadConstMapPermits 64
  --dynamicThreadTelemetry 1
)

printf '%q ' "${cmd[@]}" > "${work}/RUN_COMMAND.sh"
printf '\n' >> "${work}/RUN_COMMAND.sh"
/usr/bin/time -v -o "${work}/time.txt" "${cmd[@]}"
test -s "${run_dir}/Log.final.out"
test -s "${run_dir}/Solo.out/GeneFull/filtered/matrix.mtx"
test -s "${run_dir}/Solo.out/Velocyto/filtered/spliced.mtx"
test -s "${run_dir}/cr_assign/CRISPR_Guide_Capture/${guide_library_id}/PolyIII/matrix.mtx"
test -s "${run_dir}/Aligned.out.bam"

durable="${RESULT_ROOT}/production/${capture}"
partial="${RESULT_ROOT}/production/.${capture}.partial.${SLURM_JOB_ID}"
mkdir -p "${partial}"
mkdir -p "${partial}/run"
cp -a "${run_dir}/." "${partial}/run/"
cp "${pf_config}" "${stage_manifest}" "${work}/RUN_COMMAND.sh" "${work}/time.txt" "${partial}/"
{
  printf 'status=COMPLETE\n'
  printf 'capture=%s\n' "${capture}"
  printf 'slurm_job_id=%s\n' "${SLURM_JOB_ID}"
  printf 'slurm_array_task_id=%s\n' "${SLURM_ARRAY_TASK_ID}"
  printf 'node=%s\n' "${SLURMD_NODENAME:-unknown}"
  printf 'completed_utc=%s\n' "$(date -u +%FT%TZ)"
} > "${partial}/UPSTREAM_COMPLETE.txt"
test ! -e "${durable}"
mv "${partial}" "${durable}"
