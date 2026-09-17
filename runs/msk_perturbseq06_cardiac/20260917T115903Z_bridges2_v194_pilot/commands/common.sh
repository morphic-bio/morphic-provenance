#!/usr/bin/env bash

set -euo pipefail

readonly PROJECT_ACCOUNT="bio230034p"
readonly DATA_ROOT="/ocean/projects/bio230034p/lhung2/incoming/MSK_Perturbseq_20260910/MSK_Perturbseq06_Cardiac_20260910"
readonly RUN_ROOT="/ocean/projects/bio230034p/lhung2/msk-perturbseq06-cardiac-20260917"
readonly PROVENANCE_ROOT="${RUN_ROOT}/provenance"
readonly RESULT_ROOT="${RUN_ROOT}/results"
readonly REFERENCE_ROOT="/ocean/projects/bio230034p/shared/processing/references"
readonly GENOME_DIR="${REFERENCE_ROOT}/GRCh38-2024-A-star-msk30"
readonly ASSAY_REF_ROOT="${REFERENCE_ROOT}/MSK_Perturbseq_LEG"
readonly GEX_WHITELIST="${ASSAY_REF_ROOT}/3M-february-2018_TRU.txt"
readonly GUIDE_WHITELIST="${ASSAY_REF_ROOT}/3M-february-2018_NXT.txt"
readonly FEATURE_REF="${ASSAY_REF_ROOT}/MSK_LEG_star_suite_feature_reference.csv"
readonly TOOL_ROOT="/ocean/projects/bio230034p/shared/processing/tools/star-suite-v1.9.4"
readonly STAR_BIN="${TOOL_ROOT}/bin/STAR"
readonly STAR_SOURCE_ARCHIVE="${TOOL_ROOT}/source/STAR-suite-v1.9.4-1c9ddb9.tar.gz"
readonly STAR_SOURCE_SHA256="0ed560291908b2a045c34a5200907c3d07d6dd423c1d99adcbc1b105b94df0bc"
readonly STAR_SUITE_COMMIT="1c9ddb9a5a2a3e62748e8e4ef28e553582affeed"
readonly EXECUTION_MANIFEST="${PROVENANCE_ROOT}/inputs/cardiac_execution_files.tsv"
readonly LIBRARY_SUMMARY="${PROVENANCE_ROOT}/inputs/cardiac_execution_libraries.tsv"
readonly PROVIDER_CHECKSUMS="${DATA_ROOT}/cp.checksums.md5"
readonly PYTHON_BIN="${PYTHON_BIN:-python3.11}"

declare -ar CARDIAC_CAPTURES=(CP_A1 CP_A2 CP_A3 CP_B1 CP_B2 CP_B3 CP_R1 CP_R2)

reject_zshard_paths() {
  local value
  for value in "$@"; do
    if [[ "${value}" == *zshard* ]]; then
      echo "FATAL: zshard path is forbidden for this workflow: ${value}" >&2
      return 1
    fi
  done
}

validate_reference() {
  reject_zshard_paths "${GENOME_DIR}"

  local required
  for required in Genome SA SAindex genomeParameters.txt chrName.txt \
    chrLength.txt chrNameLength.txt chrStart.txt geneInfo.tab transcriptInfo.tab; do
    test -s "${GENOME_DIR}/${required}" || {
      echo "FATAL: missing reference file ${GENOME_DIR}/${required}" >&2
      return 1
    }
  done

  [[ "$(stat -c %s "${GENOME_DIR}/Genome")" == "3216071051" ]]
  [[ "$(stat -c %s "${GENOME_DIR}/SA")" == "24940951756" ]]
  [[ "$(stat -c %s "${GENOME_DIR}/SAindex")" == "1565873619" ]]
  [[ "$(head -n 1 "${GENOME_DIR}/geneInfo.tab")" == "38606" ]]
  [[ "$(head -n 1 "${GENOME_DIR}/transcriptInfo.tab")" == "226005" ]]
  grep -q -- '--cellrangerRefRelease 2024-A' "${GENOME_DIR}/genomeParameters.txt"

  cat <<'EOF' | sha256sum -c -
8b4b8c2255f2e8eab40cdd87dcae2dec3937309ec5d76b0ceeff96e6311d213a  /ocean/projects/bio230034p/shared/processing/references/GRCh38-2024-A-star-msk30/genomeParameters.txt
12d83750559b9ae7d273b4b7ce6077e6f24c43eb65672d1fbcfa2e1593fd3ee8  /ocean/projects/bio230034p/shared/processing/references/GRCh38-2024-A-star-msk30/chrName.txt
b297c2398f93cd3d4c8aa1d4e10d6148c9550a1c2175139c29f9aab505422a17  /ocean/projects/bio230034p/shared/processing/references/GRCh38-2024-A-star-msk30/chrLength.txt
d525ee20551f34768f4017c7a779a3f3c7b947dacdea27838a5776508834b306  /ocean/projects/bio230034p/shared/processing/references/GRCh38-2024-A-star-msk30/chrNameLength.txt
09e1d0f13d91fd4540be6e87c62f05c57bb54e465ea67bc1e24d347f623ea121  /ocean/projects/bio230034p/shared/processing/references/GRCh38-2024-A-star-msk30/chrStart.txt
40f6ac3112cdb0c36ccef1543eb40c075904f02efc2aae33644f1d90424a6e08  /ocean/projects/bio230034p/shared/processing/references/GRCh38-2024-A-star-msk30/geneInfo.tab
575664d55782dc3209837b8783daf3fe000eea89ab5f531883d2aacbd91d1666  /ocean/projects/bio230034p/shared/processing/references/GRCh38-2024-A-star-msk30/transcriptInfo.tab
EOF
}

validate_assay_references() {
  reject_zshard_paths "${GEX_WHITELIST}" "${GUIDE_WHITELIST}" "${FEATURE_REF}"
  cat <<'EOF' | sha256sum -c -
5e3969f11d28615ca47efd409205c6a17972edd7d1b2a756aaaccf36e6fd5c84  /ocean/projects/bio230034p/shared/processing/references/MSK_Perturbseq_LEG/3M-february-2018_TRU.txt
f898a606b7b6a9f7e538e7f22da776094b4a25e8804c88d66023a70bbf9fbb1e  /ocean/projects/bio230034p/shared/processing/references/MSK_Perturbseq_LEG/3M-february-2018_NXT.txt
a25c4dabc5c4011925fdee7fcf1cebc0b982ebfcfa6e37d530592c37baf16f06  /ocean/projects/bio230034p/shared/processing/references/MSK_Perturbseq_LEG/MSK_LEG_star_suite_feature_reference.csv
EOF
  [[ "$(( $(wc -l < "${FEATURE_REF}") - 1 ))" -eq 15656 ]]
}

validate_star_binary() {
  reject_zshard_paths "${STAR_BIN}"
  test -x "${STAR_BIN}"
  test -s "${TOOL_ROOT}/BUILD_MANIFEST.txt"
  grep -q "commit=${STAR_SUITE_COMMIT}" "${TOOL_ROOT}/BUILD_MANIFEST.txt"
  grep -q '^with_chromap=0$' "${TOOL_ROOT}/BUILD_MANIFEST.txt"
}

validate_python() {
  command -v "${PYTHON_BIN}" >/dev/null
  "${PYTHON_BIN}" -c 'import sys; assert sys.version_info >= (3, 9)'
}
