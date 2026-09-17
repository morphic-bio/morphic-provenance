#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${script_dir}/common.sh"

reject_zshard_paths "${DATA_ROOT}" "${RUN_ROOT}" "${PROVENANCE_ROOT}"
test -d "${DATA_ROOT}"
test -s "${PROVIDER_CHECKSUMS}"

mkdir -p "${PROVENANCE_ROOT}/inputs" "${PROVENANCE_ROOT}/outputs" \
  "${PROVENANCE_ROOT}/logs" "${RESULT_ROOT}"

validate_python
"${PYTHON_BIN}" "${script_dir}/build_cardiac_execution_manifest.py" \
  --file-manifest "${PROVENANCE_ROOT}/inputs/Cardiac_corrected_file_manifest.tsv" \
  --provider-checksums "${PROVIDER_CHECKSUMS}" \
  --fastq-root "${DATA_ROOT}" \
  --output-files "${EXECUTION_MANIFEST}" \
  --output-libraries "${LIBRARY_SUMMARY}" \
  --output-audit "${PROVENANCE_ROOT}/outputs/input_inventory_audit.json"

validate_reference
validate_assay_references

echo "Input preparation passed: ${EXECUTION_MANIFEST}"
