#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
input_root="/mnt/pikachu/MSK_Perturbseq06_Cardiac_pilot_inputs_20260917"
work_root="/storage/MSK_Perturbseq06_Cardiac_pilot_control_20260917"
result_root="/mnt/pikachu/MSK_Perturbseq06_Cardiac_pilot_results_20260917"
genome_dir="/storage/autoindex_110_44/bulk_index"
gex_whitelist="/storage/scRNAseq_output/whitelists/3M-february-2018_TRU.txt"
guide_whitelist="/storage/scRNAseq_output/whitelists/3M-february-2018_NXT.txt"
feature_ref="${script_dir}/../inputs/MSK_LEG_star_suite_feature_reference.csv"
source_archive="/mnt/pikachu/tmp/bridges2_stage_20260917/STAR-suite-v1.9.4-1c9ddb9.tar.gz"
source_sha256="0ed560291908b2a045c34a5200907c3d07d6dd423c1d99adcbc1b105b94df0bc"
provider_checksums="${input_root}/cp.checksums.md5"
star_bin="${work_root}/tools/STAR"

for path in "${input_root}" "${work_root}" "${result_root}" "${genome_dir}" \
  "${gex_whitelist}" "${guide_whitelist}" "${feature_ref}" "${source_archive}"; do
  if [[ "${path}" == *zshard* ]]; then
    echo "FATAL: zshard path is forbidden: ${path}" >&2
    exit 1
  fi
done

test -s "${provider_checksums}"
[[ "$(head -n 1 "${genome_dir}/geneInfo.tab")" == "38606" ]]
[[ "$(head -n 1 "${genome_dir}/transcriptInfo.tab")" == "226005" ]]
grep -q -- '--cellrangerRefRelease 2024-A' "${genome_dir}/genomeParameters.txt"
echo "${source_sha256}  ${source_archive}" | sha256sum -c -

mkdir -p "${work_root}/tools" "${result_root}"
if [[ ! -x "${star_bin}" ]]; then
  build_root="${work_root}/build-v1.9.4"
  test ! -e "${build_root}"
  mkdir -p "${build_root}"
  tar -xzf "${source_archive}" -C "${build_root}"
  make -C "${build_root}/core/legacy/source" clean
  make -C "${build_root}/core/legacy/source" -j8 STAR
  install -m 0755 "${build_root}/core/legacy/source/STAR" "${star_bin}"
  {
    printf 'star_suite_version=1.9.4\n'
    printf 'commit=1c9ddb9a5a2a3e62748e8e4ef28e553582affeed\n'
    printf 'source_archive_sha256=%s\n' "${source_sha256}"
    printf 'with_chromap=1\n'
    printf 'binary_sha256=%s\n' "$(sha256sum "${star_bin}" | awk '{print $1}')"
    printf 'compiler=%s\n' "$(g++ --version | head -n 1)"
    printf 'built_utc=%s\n' "$(date -u +%FT%TZ)"
  } > "${work_root}/tools/BUILD_MANIFEST.txt"
fi

declare -A gex_r1=(
  [CP_R1]="CP_R1_mRNA_IGO_18593_2_S45_L007_R1_001.fastq.gz"
  [CP_R2]="CP_R2_mRNA_IGO_17967_2_S11_L001_R1_001.fastq.gz"
)
declare -A gex_r2=(
  [CP_R1]="CP_R1_mRNA_IGO_18593_2_S45_L007_R2_001.fastq.gz"
  [CP_R2]="CP_R2_mRNA_IGO_17967_2_S11_L001_R2_001.fastq.gz"
)
declare -A guide_r1=(
  [CP_R1]="CP_gRNA_IGO_17967_B_4_S38_L005_R1_001.fastq.gz"
  [CP_R2]="CP_R2_gRNA_IGO_17967_4_S39_L005_R1_001.fastq.gz"
)
declare -A guide_r2=(
  [CP_R1]="CP_gRNA_IGO_17967_B_4_S38_L005_R2_001.fastq.gz"
  [CP_R2]="CP_R2_gRNA_IGO_17967_4_S39_L005_R2_001.fastq.gz"
)

stage_one() {
  local destination_dir="$1"
  local name="$2"
  local staged_name="${3:-${name}}"
  local expected_md5 destination
  expected_md5="$(awk -v name="${name}" '$2 == name {print $1}' "${provider_checksums}")"
  [[ -n "${expected_md5}" ]]
  destination="${destination_dir}/${staged_name}"
  cp "${input_root}/${name}" "${destination}"
  echo "${expected_md5}  ${destination}" | md5sum -c -
  gzip -t "${destination}"
}

for capture in CP_R1 CP_R2; do
  durable="${result_root}/${capture}"
  partial="${result_root}/.${capture}.partial.$$"
  if [[ -s "${durable}/PILOT_COMPLETE.txt" ]] && \
     grep -q '^status=COMPLETE$' "${durable}/PILOT_COMPLETE.txt"; then
    echo "Skipping already completed control capture: ${capture}"
    continue
  fi
  test ! -e "${durable}"
  test ! -e "${partial}"
  work="${work_root}/${capture}"
  gex_dir="${work}/fastqs/gex"
  guide_dir="${work}/fastqs/PolyIII"
  run_dir="${work}/run"
  mkdir -p "${gex_dir}" "${guide_dir}" "${run_dir}" "${partial}/run"

  stage_one "${gex_dir}" "${gex_r1[${capture}]}" & p1=$!
  stage_one "${gex_dir}" "${gex_r2[${capture}]}" & p2=$!
  staged_guide_r1="${guide_r1[${capture}]}"
  staged_guide_r2="${guide_r2[${capture}]}"
  if [[ "${capture}" == "CP_R2" ]]; then
    staged_guide_r1="CPR2_${staged_guide_r1#CP_R2_}"
    staged_guide_r2="CPR2_${staged_guide_r2#CP_R2_}"
  fi
  stage_one "${guide_dir}" "${guide_r1[${capture}]}" "${staged_guide_r1}" & p3=$!
  stage_one "${guide_dir}" "${guide_r2[${capture}]}" "${staged_guide_r2}" & p4=$!
  wait "${p1}" "${p2}" "${p3}" "${p4}"

  staging_map="${work}/STAGING_MAP.tsv"
  {
    printf 'library\tsource_basename\tstaged_basename\n'
    printf 'gex\t%s\t%s\n' "${gex_r1[${capture}]}" "${gex_r1[${capture}]}"
    printf 'gex\t%s\t%s\n' "${gex_r2[${capture}]}" "${gex_r2[${capture}]}"
    printf 'PolyIII\t%s\t%s\n' "${guide_r1[${capture}]}" "${staged_guide_r1}"
    printf 'PolyIII\t%s\t%s\n' "${guide_r2[${capture}]}" "${staged_guide_r2}"
  } > "${staging_map}"

  guide_library_id="grna_${capture,,}"
  pf_config="${work}/pf_multi_config.csv"
  cat > "${pf_config}" <<EOF
[libraries]
fastqs,sample,library_type,feature_types,star_chemistry,star_whitelist,star_feature_ref,star_library_id,star_max_hamming
${gex_dir},${capture},Gene Expression,Gene Expression,TRU,,,gex_${capture,,},
${guide_dir},${capture},CRISPR Guide Capture,CRISPR Guide Capture,NXT,${guide_whitelist},${feature_ref},${guide_library_id},1
EOF

  unset STAR_SOLO_NONFLEX_HASH_BRIDGE
  export STAR_VELOCYTO_LOW_MEM=1
  export STAR_SOLO_BINARY_SPOOL=1

  cmd=(
    "${star_bin}"
    --runThreadN 32
    --genomeDir "${genome_dir}"
    --readFilesIn "${gex_dir}/${gex_r2[${capture}]}" "${gex_dir}/${gex_r1[${capture}]}"
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
    --soloCBwhitelist "${gex_whitelist}"
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
    --crFeatureRef "${feature_ref}"
    --crWhitelist "${guide_whitelist}"
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

  python3 "${script_dir}/validate_cardiac_pilot.py" \
    --run-dir "${run_dir}" \
    --tru-whitelist "${gex_whitelist}" \
    --capture "${capture}" \
    --guide-library-id "${guide_library_id}" \
    --output "${work}/PILOT_VALIDATION.json"

  cp -a "${run_dir}/." "${partial}/run/"
  cp "${pf_config}" "${staging_map}" "${work}/RUN_COMMAND.sh" "${work}/time.txt" \
    "${work}/PILOT_VALIDATION.json" "${partial}/"
  {
    printf 'status=COMPLETE\n'
    printf 'capture=%s\n' "${capture}"
    printf 'node=pikachu\n'
    printf 'completed_utc=%s\n' "$(date -u +%FT%TZ)"
  } > "${partial}/PILOT_COMPLETE.txt"

  mv "${partial}" "${durable}"
done

python3 "${script_dir}/gather_pilot_results.py" \
  --pilot-root "${result_root}" \
  --host pikachu \
  --output "${result_root}/PILOT_GATHER.json"
