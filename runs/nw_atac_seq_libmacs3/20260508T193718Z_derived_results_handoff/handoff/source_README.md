# NW ATAC-seq libMACS3 Result Submission

Prepared for Globus handoff: 2026-05-08T19:37:18Z UTC
README updated: 2026-05-19T22:35:40Z UTC

This directory contains the Northwestern/Morphic ATAC-seq production result
package named `NW-ATAC-SEQ-results-libmacs3-05-05-26`. It is a derived-results
submission, not a raw-data submission.

Raw FASTQs, BAM/BAI files, and Y/noY FASTQ payloads are intentionally absent
from this non-large-file package. Per-sample metadata records the separate
Globus transfers for those large files.

Detailed run provenance, script versions, GitHub hashes, Chromap binary hashes,
Docker image identifiers, and transfer parameters are in `provenance.md`.

## Directory Structure

```text
.
  README.md
  provenance.md
  MANIFEST.files.tsv
  MANIFEST.final_samples.tsv
  MANIFEST.final_extension_counts.tsv
  MANIFEST.metadata_scripts.sha256
  MANIFEST.sources.tsv
  MANIFEST.summary.tsv
  final/
    <target>/<timepoint>/<sample>/
  metadata/
    local_run_root/
    remote_server/NW-ATAC-SEQ-results-libmacs3-05-05-26/
    storage_temp/NW_ATACseq_1/
  scripts/
    SHA256SUMS
    local_morphic_atac_seq/
    remote_morphic_atac_seq/
```

## Top-Level Files

- `README.md`: this submission guide.
- `provenance.md`: run parameters, script/binary/container provenance, GitHub
  hashes, and Globus transfer details.
- `MANIFEST.files.tsv`: full file listing for this submission, with relative
  path, size in bytes, and mtime.
- `MANIFEST.final_samples.tsv`: one row per directory under `final/`, with file
  count and byte size.
- `MANIFEST.final_extension_counts.tsv`: file-type counts under `final/`.
- `MANIFEST.metadata_scripts.sha256`: SHA256 checksums for files under
  `metadata/` and `scripts/`.
- `MANIFEST.sources.tsv`: source locations used to construct this package.
- `MANIFEST.summary.tsv`: package-level counts and staging metadata.

## Result Files

Most completed sample result directories have this shape:

```text
final/<target>/<timepoint>/<sample>/
  <sample>.fragments.bed
  <sample>_unstranded.bw
  <sample>.peaks.narrowPeak
  <sample>.peaks.summits.bed
  <sample>.summary.txt
  <sample>.summary.txt.macs3_frag_peaks.tsv
  <sample>.y_readnames.txt
  <sample>.chromap.stderr.log
  <sample>.chromap.stdout.log
  <sample>.large_files.globus_transfer.json
  <sample>.large_files.globus_task_id.txt
  <sample>.large_files.globus_monitor.log
```

File meanings:

- `*.fragments.bed`: Tn5-shifted fragment intervals emitted by Chromap.
- `*_unstranded.bw`: bigWig coverage built from shifted fragments.
- `*.peaks.narrowPeak`: in-process libMACS3 FRAG peak calls from Chromap.
- `*.peaks.summits.bed`: peak summits from the same libMACS3 FRAG run.
- `*.summary.txt`: Chromap per-sample mapping summary.
- `*.summary.txt.macs3_frag_peaks.tsv`: sidecar metadata for the FRAG peak call.
- `*.y_readnames.txt`: names of reads assigned to chrY.
- `*.chromap.stderr.log` and `*.chromap.stdout.log`: per-sample Chromap logs.
- `*.large_files.globus_*`: metadata for the separate large-file transfer
  containing BAM/BAI and Y/noY FASTQs.

## Counts

Counts from the submitted manifests:

```text
final sample directories: 201
full result sample directories: 200
marker-only reused sample directories: 1
final files: 2401
final du: 212G
metadata files: 1082
script files: 73
FASTQ files in this package: 0
BAM/BAI files under final/: 0
```

Final file-type counts:

```text
fragments.bed                    200
unstranded.bw                    200
peaks.narrowPeak                 200
peaks.summits.bed                200
summary.txt                      200
summary.txt.macs3_frag_peaks.tsv 200
y_readnames.txt                  200
chromap logs                     400 stderr/stdout files
large-file Globus logs/json/txt  600 files
SKIPPED_REUSED_EXISTING_RESULT   1
```

The marker-only directory is:

```text
final/NUP133/0h/ATAC-NUP133-0h-1/SKIPPED_REUSED_EXISTING_RESULT.txt
```

That file records that `ATAC-NUP133-0h-1` was skipped in the later bulk run
because it had already been run as the final validation sample before the bulk
job started.

## Metadata Directories

`metadata/local_run_root/` contains local production run metadata from:

```text
/mnt/pikachu/NW-ATAC-SEQ-results-libmacs3-05-05-26
```

Important files in that tree include:

- `nw_5_21.remote_samples.tsv`
- `nw_5_21.remote.manifest.tsv`
- `nw_5_21.remote_copyback_monitor.status`
- `nw_atacseq_1.storage_docker.manifest.tsv`
- `nw_atacseq_1.storage_docker.status`
- `copyback_logs/*.copyback_globus.log`
- `remote_copyback_rows/*.manifest_row.tsv`
- `remote_copyback_status/*.ready.done`
- `input_stability*`

`metadata/remote_server/NW-ATAC-SEQ-results-libmacs3-05-05-26/` contains
metadata copied from:

```text
10.159.4.53:/home/lhhung/NW-ATAC-SEQ-results-libmacs3-05-05-26
```

The remote `final/` payload was drained after copyback, so remote final payloads
are not duplicated in metadata.

`metadata/storage_temp/NW_ATACseq_1/` contains surviving `/storage` temporary
provenance from the local storage/Docker path. Processed FASTQs were deleted
after successful processing by the production runner and are not included.

## Script Directories

`scripts/local_morphic_atac_seq/` contains the local production copy of the
Morphic ATAC-seq scripts, Dockerfiles, docs, helper AWK scripts, and tests.

`scripts/remote_morphic_atac_seq/` contains the script subset deployed to the
remote worker host for the NW-5-21 portion of the run.

`scripts/SHA256SUMS` contains SHA256 checksums for copied scripts and docs.
Selected checksums and script source details are in `provenance.md`.

## Notes

- `final/` is a hardlinked view of the source result tree and should be treated
  as read-only.
- No raw FASTQs are included in this package.
- No BAM or BAI files are included under `final/`; those were moved to
  per-sample `_large_files` directories and transferred separately.
- The `*.large_files.globus_task_id.txt` and
  `*.large_files.globus_transfer.json` files under each full sample directory are
  the pointers to the separate large-file transfers.
- The full file manifest is intentionally externalized to `MANIFEST.files.tsv`
  rather than repeated inline in this README.
