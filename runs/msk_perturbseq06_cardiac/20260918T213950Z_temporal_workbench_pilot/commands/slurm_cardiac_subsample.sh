set -euo pipefail

readonly run_root="/ocean/projects/bio230034p/lhung2/temporal-cardiac-workbench-20260918T213950Z"
readonly input_root="${run_root}/input"
readonly result_root="${run_root}/results/slurm"
readonly star_bin="/ocean/projects/bio230034p/shared/processing/tools/star-suite-v1.9.4/bin/STAR"
readonly genome_dir="/ocean/projects/bio230034p/shared/processing/references/GRCh38-2024-A-star-msk30"
readonly reference_root="/ocean/projects/bio230034p/shared/processing/references/MSK_Perturbseq_LEG"
readonly gex_whitelist="${reference_root}/3M-february-2018_TRU.txt"
readonly guide_whitelist="${reference_root}/3M-february-2018_NXT.txt"
readonly feature_ref="${reference_root}/MSK_LEG_star_suite_feature_reference.csv"

readonly gex_r1_name="CP_R1_mRNA_IGO_18593_2_S45_L007_R1_001.fastq.gz"
readonly gex_r2_name="CP_R1_mRNA_IGO_18593_2_S45_L007_R2_001.fastq.gz"
readonly guide_r1_name="CP_gRNA_IGO_17967_B_4_S38_L005_R1_001.fastq.gz"
readonly guide_r2_name="CP_gRNA_IGO_17967_B_4_S38_L005_R2_001.fastq.gz"

test ! -e "${result_root}"
for path in \
  "${star_bin}" \
  "${genome_dir}/Genome" \
  "${gex_whitelist}" \
  "${guide_whitelist}" \
  "${feature_ref}" \
  "${input_root}/${gex_r1_name}" \
  "${input_root}/${gex_r2_name}" \
  "${input_root}/${guide_r1_name}" \
  "${input_root}/${guide_r2_name}"; do
  test -s "${path}"
done
[[ "$("${star_bin}" --version)" == "1.9.4" ]]

scratch_root="${LOCAL:-/tmp}/temporal-cardiac-pilot-${SLURM_JOB_ID}"
gex_dir="${scratch_root}/fastqs/gex"
guide_dir="${scratch_root}/fastqs/PolyIII"
run_dir="${scratch_root}/run"
partial="${run_root}/results/.slurm.partial.${SLURM_JOB_ID}"
trap 'rm -rf "${scratch_root}" "${partial}"' EXIT
mkdir -p "${gex_dir}" "${guide_dir}" "${run_dir}" "${partial}"

cp_checked() {
  local source="$1"
  local destination="$2"
  local expected_md5="$3"
  cp "${source}" "${destination}"
  printf '%s  %s\n' "${expected_md5}" "${destination}" | md5sum -c -
  gzip -t "${destination}"
}

cp_checked "${input_root}/${gex_r1_name}" "${gex_dir}/${gex_r1_name}" fbf09717ce4445eb179156cfde7cb63d &
p1=$!
cp_checked "${input_root}/${gex_r2_name}" "${gex_dir}/${gex_r2_name}" 1df1bf3d60bb87e4b40845208360b5eb &
p2=$!
cp_checked "${input_root}/${guide_r1_name}" "${guide_dir}/${guide_r1_name}" 7cba6a93df74b135faf7e5b2d857b875 &
p3=$!
cp_checked "${input_root}/${guide_r2_name}" "${guide_dir}/${guide_r2_name}" 1f93718c2b0f89d417df2f359def2264 &
p4=$!
wait "${p1}" "${p2}" "${p3}" "${p4}"

pf_config="${scratch_root}/pf_multi_config.csv"
cat > "${pf_config}" <<EOF
[libraries]
fastqs,sample,library_type,feature_types,star_chemistry,star_whitelist,star_feature_ref,star_library_id,star_max_hamming
${gex_dir},CP_R1,Gene Expression,Gene Expression,TRU,,,gex_cp_r1,
${guide_dir},CP_R1,CRISPR Guide Capture,CRISPR Guide Capture,NXT,${guide_whitelist},${feature_ref},grna_cp_r1,1
EOF

unset STAR_SOLO_NONFLEX_HASH_BRIDGE
export STAR_VELOCYTO_LOW_MEM=1
export STAR_SOLO_BINARY_SPOOL=1

cmd=(
  "${star_bin}"
  --runThreadN 32
  --genomeDir "${genome_dir}"
  --readFilesIn "${gex_dir}/${gex_r2_name}" "${gex_dir}/${gex_r1_name}"
  --readFilesBgzfMode auto
  --outFileNamePrefix "${run_dir}/"
  --outTmpDir "${scratch_root}/tmp_STAR"
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
  --readMapNumber 1000000
)

printf '%q ' "${cmd[@]}" > "${scratch_root}/RUN_COMMAND.sh"
printf '\n' >> "${scratch_root}/RUN_COMMAND.sh"
/usr/bin/time -v -o "${scratch_root}/time.txt" "${cmd[@]}"

test -s "${run_dir}/Log.final.out"
test -s "${run_dir}/outs/raw_feature_bc_matrix/matrix.mtx.gz"
test -s "${run_dir}/outs/filtered_feature_bc_matrix/matrix.mtx.gz"
test -s "${run_dir}/outs/raw_velocyto_feature_bc_matrix/spliced.mtx.gz"
test -s "${run_dir}/cr_assign/CRISPR_Guide_Capture/grna_cp_r1/PolyIII/matrix.mtx"

mkdir -p "${partial}/run"
cp -a "${run_dir}/." "${partial}/run/"
cp "${pf_config}" "${scratch_root}/RUN_COMMAND.sh" "${scratch_root}/time.txt" "${partial}/"
python3 - "${partial}/SLURM_COMPLETE.json" <<'PY'
import json
import os
import sys
from datetime import datetime, timezone

payload = {
    "completed_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    "node": os.environ.get("SLURMD_NODENAME", "unknown"),
    "read_map_number": 1000000,
    "slurm_job_id": os.environ["SLURM_JOB_ID"],
    "star_suite_version": "1.9.4",
    "status": "PASS",
}
with open(sys.argv[1], "w") as handle:
    json.dump(payload, handle, indent=2, sort_keys=True)
    handle.write("\n")
PY

mv "${partial}" "${result_root}"
trap 'rm -rf "${scratch_root}"' EXIT
cat "${result_root}/SLURM_COMPLETE.json"
