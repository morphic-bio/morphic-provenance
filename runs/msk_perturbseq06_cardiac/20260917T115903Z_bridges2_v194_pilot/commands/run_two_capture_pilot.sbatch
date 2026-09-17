#!/usr/bin/env bash
#SBATCH --job-name=msk-cardiac-pilot
#SBATCH --account=bio230034p
#SBATCH --partition=RM-shared
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=64
#SBATCH --mem=120G
#SBATCH --time=04:00:00
#SBATCH --array=0-1%2
#SBATCH --output=/ocean/projects/bio230034p/lhung2/msk-perturbseq06-cardiac-20260917/logs/%x-%A_%a.out
#SBATCH --error=/ocean/projects/bio230034p/lhung2/msk-perturbseq06-cardiac-20260917/logs/%x-%A_%a.err

set -euo pipefail

script_dir="${PROVENANCE_COMMANDS_DIR:-/ocean/projects/bio230034p/lhung2/msk-perturbseq06-cardiac-20260917/provenance/commands}"
source "${script_dir}/common.sh"

validate_reference
validate_assay_references
validate_star_binary
validate_python
test -s "${EXECUTION_MANIFEST}"

captures=(CP_R1 CP_R2)
capture="${captures[${SLURM_ARRAY_TASK_ID}]}"
guide_library_id="grna_${capture,,}"

case "${capture}" in
  CP_R1)
    gex_r1="CP_R1_mRNA_IGO_18593_2_S45_L007_R1_001.fastq.gz"
    gex_r2="CP_R1_mRNA_IGO_18593_2_S45_L007_R2_001.fastq.gz"
    guide_r1="CP_gRNA_IGO_17967_B_4_S38_L005_R1_001.fastq.gz"
    guide_r2="CP_gRNA_IGO_17967_B_4_S38_L005_R2_001.fastq.gz"
    ;;
  CP_R2)
    gex_r1="CP_R2_mRNA_IGO_17967_2_S11_L001_R1_001.fastq.gz"
    gex_r2="CP_R2_mRNA_IGO_17967_2_S11_L001_R2_001.fastq.gz"
    guide_r1="CP_R2_gRNA_IGO_17967_4_S39_L005_R1_001.fastq.gz"
    guide_r2="CP_R2_gRNA_IGO_17967_4_S39_L005_R2_001.fastq.gz"
    ;;
  *)
    echo "FATAL: unsupported pilot capture ${capture}" >&2
    exit 1
    ;;
esac

guide_r1_staged="${guide_r1}"
guide_r2_staged="${guide_r2}"
if [[ "${capture}" == "CP_R2" ]]; then
  guide_r1_staged="CPR2_${guide_r1#CP_R2_}"
  guide_r2_staged="CPR2_${guide_r2#CP_R2_}"
fi

scratch_base="${LOCAL:-/tmp}"
work="${scratch_base}/msk-cardiac-${capture,,}-pilot-${SLURM_JOB_ID}"
gex_dir="${work}/fastqs/gex"
guide_dir="${work}/fastqs/PolyIII"
run_dir="${work}/run"
durable="${RESULT_ROOT}/pilot_nodes/${capture}"
partial="${RESULT_ROOT}/pilot_nodes/.${capture}.partial.${SLURM_JOB_ID}"
test ! -e "${durable}"
test ! -e "${partial}"
mkdir -p "${gex_dir}" "${guide_dir}" "${run_dir}" "${partial}/run"

stage_one() {
  local destination_dir="$1"
  local name="$2"
  local staged_name="${3:-${name}}"
  local record source expected_md5 destination
  record="$(awk -F '\t' -v name="${name}" 'NR > 1 && $13 == name {print $14 "\t" $16}' "${EXECUTION_MANIFEST}")"
  [[ -n "${record}" ]] || {
    echo "FATAL: pilot file absent from execution manifest: ${name}" >&2
    return 1
  }
  IFS=$'\t' read -r source expected_md5 <<< "${record}"
  reject_zshard_paths "${source}" "${destination_dir}"
  destination="${destination_dir}/${staged_name}"
  cp "${source}" "${destination}"
  echo "${expected_md5}  ${destination}" | md5sum -c -
  gzip -t "${destination}"
}

stage_one "${gex_dir}" "${gex_r1}" &
p1=$!
stage_one "${gex_dir}" "${gex_r2}" &
p2=$!
stage_one "${guide_dir}" "${guide_r1}" "${guide_r1_staged}" &
p3=$!
stage_one "${guide_dir}" "${guide_r2}" "${guide_r2_staged}" &
p4=$!
wait "${p1}" "${p2}" "${p3}" "${p4}"

staging_map="${work}/STAGING_MAP.tsv"
{
  printf 'library\tsource_basename\tstaged_basename\n'
  printf 'gex\t%s\t%s\n' "${gex_r1}" "${gex_r1}"
  printf 'gex\t%s\t%s\n' "${gex_r2}" "${gex_r2}"
  printf 'PolyIII\t%s\t%s\n' "${guide_r1}" "${guide_r1_staged}"
  printf 'PolyIII\t%s\t%s\n' "${guide_r2}" "${guide_r2_staged}"
} > "${staging_map}"

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
  --runThreadN 32
  --genomeDir "${GENOME_DIR}"
  --readFilesIn
  "${gex_dir}/${gex_r2}"
  "${gex_dir}/${gex_r1}"
  --readFilesBgzfMode auto
  --outFileNamePrefix "${run_dir}/"
  --outTmpDir "${work}/tmp_STAR"
  --outSAMtype None
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
  --soloFeatures GeneFull
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
  --dynamicThreadConstMapPermits 32
  --dynamicThreadTelemetry 1
  --readMapNumber 250000
)

printf '%q ' "${cmd[@]}" > "${work}/RUN_COMMAND.sh"
printf '\n' >> "${work}/RUN_COMMAND.sh"
/usr/bin/time -v -o "${work}/time.txt" "${cmd[@]}"

"${PYTHON_BIN}" "${script_dir}/validate_cardiac_pilot.py" \
  --run-dir "${run_dir}" \
  --tru-whitelist "${GEX_WHITELIST}" \
  --capture "${capture}" \
  --guide-library-id "${guide_library_id}" \
  --output "${work}/PILOT_VALIDATION.json"

cp -a "${run_dir}/." "${partial}/run/"
cp "${pf_config}" "${staging_map}" "${work}/RUN_COMMAND.sh" "${work}/time.txt" \
  "${work}/PILOT_VALIDATION.json" "${partial}/"
{
  printf 'status=COMPLETE\n'
  printf 'capture=%s\n' "${capture}"
  printf 'slurm_job_id=%s\n' "${SLURM_JOB_ID}"
  printf 'slurm_array_task_id=%s\n' "${SLURM_ARRAY_TASK_ID}"
  printf 'node=%s\n' "${SLURMD_NODENAME:-unknown}"
  printf 'completed_utc=%s\n' "$(date -u +%FT%TZ)"
} > "${partial}/PILOT_COMPLETE.txt"

mv "${partial}" "${durable}"

cat "${durable}/PILOT_VALIDATION.json"
