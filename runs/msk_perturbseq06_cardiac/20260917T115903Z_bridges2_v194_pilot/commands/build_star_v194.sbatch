#!/usr/bin/env bash
#SBATCH --job-name=star-v194-build
#SBATCH --account=bio230034p
#SBATCH --partition=RM-shared
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=20
#SBATCH --mem=32G
#SBATCH --time=01:00:00
#SBATCH --output=/ocean/projects/bio230034p/lhung2/msk-perturbseq06-cardiac-20260917/logs/%x-%j.out
#SBATCH --error=/ocean/projects/bio230034p/lhung2/msk-perturbseq06-cardiac-20260917/logs/%x-%j.err

set -euo pipefail

script_dir="${PROVENANCE_COMMANDS_DIR:-/ocean/projects/bio230034p/lhung2/msk-perturbseq06-cardiac-20260917/provenance/commands}"
source "${script_dir}/common.sh"

reject_zshard_paths "${STAR_SOURCE_ARCHIVE}" "${TOOL_ROOT}"
echo "${STAR_SOURCE_SHA256}  ${STAR_SOURCE_ARCHIVE}" | sha256sum -c -

scratch_base="${LOCAL:-/tmp}"
build_root="${scratch_base}/star-suite-v1.9.4-build-${SLURM_JOB_ID}"
mkdir -p "${build_root}" "${TOOL_ROOT}/bin" "${TOOL_ROOT}/source"
tar -xzf "${STAR_SOURCE_ARCHIVE}" -C "${build_root}"

# process_features includes <htslib/...> headers directly. Pikachu provides
# those headers system-wide, but Bridges-2 does not, so use the copy bundled
# with this exact STAR Suite source archive.
export CPATH="${build_root}/core/legacy/source/htslib${CPATH:+:${CPATH}}"

# The v1.9.4 portable link otherwise pulls duplicate BGZF reader definitions
# from both STAR's OBJECTS and libprocess_features.a. Keep the feature adapter,
# but let it resolve against the copies already linked into STAR.
pf_makefile="${build_root}/core/features/process_features/Makefile"
grep -q '^CORE_OBJS=.*pf_bgzf_input.o pf_BgzfRangeReader.o pf_BgzfBlockReader.o$' "${pf_makefile}"
sed -i \
  's/ pf_bgzf_input.o pf_BgzfRangeReader.o pf_BgzfBlockReader.o$/ pf_bgzf_input.o/' \
  "${pf_makefile}"

# A clean build is mandatory after materializing a source archive.
make -C "${build_root}/core/legacy/source" WITH_CHROMAP=0 clean
make -C "${build_root}/core/legacy/source" WITH_CHROMAP=0 -j8 STAR

install -m 0755 "${build_root}/core/legacy/source/STAR" "${STAR_BIN}.tmp.${SLURM_JOB_ID}"
mv "${STAR_BIN}.tmp.${SLURM_JOB_ID}" "${STAR_BIN}"

{
  printf 'star_suite_version=1.9.4\n'
  printf 'commit=%s\n' "${STAR_SUITE_COMMIT}"
  printf 'source_archive=%s\n' "${STAR_SOURCE_ARCHIVE}"
  printf 'source_archive_sha256=%s\n' "${STAR_SOURCE_SHA256}"
  printf 'with_chromap=0\n'
  printf 'build_scope=scRNA-only portable Bridges-2 build\n'
  printf 'htslib_headers=%s\n' "${build_root}/core/legacy/source/htslib"
  printf 'portable_link_adjustment=deduplicate process_features BGZF reader objects\n'
  printf 'binary_sha256=%s\n' "$(sha256sum "${STAR_BIN}" | awk '{print $1}')"
  printf 'compiler=%s\n' "$(g++ --version | head -n 1)"
  printf 'built_utc=%s\n' "$(date -u +%FT%TZ)"
  printf 'slurm_job_id=%s\n' "${SLURM_JOB_ID}"
} > "${TOOL_ROOT}/BUILD_MANIFEST.txt"

"${STAR_BIN}" --version
cat "${TOOL_ROOT}/BUILD_MANIFEST.txt"
