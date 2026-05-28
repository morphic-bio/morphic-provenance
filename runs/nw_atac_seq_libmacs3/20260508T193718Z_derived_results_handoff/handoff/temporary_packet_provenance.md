# NW ATAC-seq libMACS3 Submission Provenance

Prepared for Globus handoff: 2026-05-08T19:37:18Z UTC
Provenance split from README: 2026-05-19T22:35:40Z UTC

This file records execution parameters, source repositories, script versions,
binary hashes, Docker image identifiers, and Globus transfer details for the
`NW-ATAC-SEQ-results-libmacs3-05-05-26` derived-results submission.

## Globus Destination

Remote destination for the non-large-file submission:

```text
Morphic Processing endpoint 61fb8b9a-9b52-456e-928c-30c0fb0140bf
/NW-ATAC-SEQ-results-libmacs3-05-05-26/
```

The non-large-file Globus transfer submitted on 2026-05-19 used checksum
verification and preserved mtimes:

```text
task_id: 123a3645-53b9-11f1-bc84-02535127e3d7
source:   07446cad-33b8-11f0-8c0c-0afffb017b7d:/mnt/pikachu/globus_uploads/NW-ATAC-SEQ-results-libmacs3-05-05-26/
dest:     61fb8b9a-9b52-456e-928c-30c0fb0140bf:/NW-ATAC-SEQ-results-libmacs3-05-05-26/
options:  --recursive --preserve-mtime --verify-checksum
label:    NW ATAC non-large results libmacs3 2026-05-19
status:   SUCCEEDED, 3564/3564 files
```

After this provenance split, `README.md`, `provenance.md`, and
`MANIFEST.files.tsv` were transferred as a small follow-up update. See the
latest task metadata in the working notes or Globus task history.

Large BAM/BAI and Y/noY FASTQ outputs were transferred separately during
production to:

```text
/ATAC-results-05-05-26/<target>/<timepoint>/<sample>_large_files/
```

Each full sample directory includes:

```text
<sample>.large_files.globus_transfer.json
<sample>.large_files.globus_task_id.txt
<sample>.large_files.globus_monitor.log
```

These files are the per-sample pointers to the separate large-file Globus tasks.

## Package Construction Sources

The staging package was constructed from these sources:

```text
/mnt/pikachu/NW-ATAC-SEQ-results-libmacs3-05-05-26/final
  -> final/ as hardlinks

/mnt/pikachu/NW-ATAC-SEQ-results-libmacs3-05-05-26
  -> metadata/local_run_root/ as copied run metadata, with final/ excluded

/storage/atac-libmacs3-05-05-26/NW_ATACseq_1
  -> metadata/storage_temp/NW_ATACseq_1/

10.159.4.53:/home/lhhung/NW-ATAC-SEQ-results-libmacs3-05-05-26
  -> metadata/remote_server/NW-ATAC-SEQ-results-libmacs3-05-05-26/

/home/lhhung/morphic-atac-seq
  -> scripts/local_morphic_atac_seq/

10.159.4.53:/home/lhhung/morphic-atac-seq
  -> scripts/remote_morphic_atac_seq/
```

See `MANIFEST.sources.tsv` for the same source list in tabular form.

## Run Parameters

The common per-sample Chromap/libMACS3 command was rendered by
`runChromap_libmacs3.sh`. The relevant Chromap argv pattern was:

```text
chromap
  -x <chromap index>
  -r <reference FASTA>
  -t <threads>
  --temp-dir <sample tmp dir>
  -1 <R1 FASTQ or comma-joined lane list>
  -2 <R2 FASTQ or comma-joined lane list>
  --trim-adapters
  --min-frag-length 30
  -l 2000
  --remove-pcr-duplicates
  --Tn5-shift-mode symmetric
  --BAM -o <sample>.bam
  --sort-bam
  --write-index
  --atac-fragments <sample>.fragments.bed
  --emit-Y-bam
  --Y-output <sample>.Y.bam
  --emit-noY-bam
  --noY-output <sample>.noY.bam
  --emit-Y-read-names
  --Y-read-names-output <sample>.y_readnames.txt
  --emit-Y-noY-fastq
  --Y-fastq-output-prefix <sample>.Y.
  --noY-fastq-output-prefix <sample>.noY.
  --summary <sample>.summary.txt
  --call-macs3-frag-peaks
  --macs3-frag-peaks-source memory
  --macs3-frag-pvalue 0.01
  --macs3-frag-min-length 200
  --macs3-frag-max-gap 30
  --macs3-frag-peaks-output <sample>.peaks.narrowPeak
  --macs3-frag-summits-output <sample>.peaks.summits.bed
  --low-mem
```

Reference and index paths:

```text
local reference FASTA: /storage/scRNAseq_output/indices-110-44/chromap/genome.fa
local chrom sizes:     /storage/scRNAseq_output/indices-110-44/chromap/chrNameLength.txt
local Chromap index:   /storage/scRNAseq_output/indices-110-44/chromap/index

remote reference FASTA: /home/lhhung/chromap-ref/genome.fa
remote chrom sizes:     /home/lhhung/chromap-ref/chrNameLength.txt
remote Chromap index:   /home/lhhung/chromap-ref/index
```

Remote NW-5-21 worker parameters:

```text
script: scripts/local_morphic_atac_seq/run_nw_5_21_remote_2026_05_05.sh
remote host: 10.159.4.53
remote app root: /home/lhhung/morphic-atac-seq
remote run root: /home/lhhung/NW-ATAC-SEQ-results-libmacs3-05-05-26
remote FASTQ dir: /home/lhhung/NW-5-21/ATAC-Seq
remote Chromap binary: /home/lhhung/Chromap-suite/chromap
Docker image: morphic-atac-libmacs3:2026-05-05-debian-slim
THREADS: 12
WORKERS: 2
CHROMAP_LOW_MEM: 1
DELETE_PROCESSED_FASTQS: 1
DEFER_SAMPLE_IDS: ATAC-SSU72-0h-1
```

Local NW_ATACseq_1 storage/Docker worker parameters:

```text
script: scripts/local_morphic_atac_seq/run_nw_atacseq_1_storage_docker_2026_05_05.sh
run root: /mnt/pikachu/NW-ATAC-SEQ-results-libmacs3-05-05-26
source: /storage/atac-libmacs3-05-05-26/NW_ATACseq_1/source_direct
storage root: /storage/atac-libmacs3-05-05-26/NW_ATACseq_1
storage output: /storage/atac-libmacs3-05-05-26/NW_ATACseq_1/final_pending_copyback
host output: /mnt/pikachu/NW-ATAC-SEQ-results-libmacs3-05-05-26/final
Docker image: morphic-atac-libmacs3:2026-05-05-debian-slim
THREADS: 16
JOBS: 1
CHROMAP_LOW_MEM: 1
USE_FASTQ_CACHE: 0
DELETE_PROCESSED_STORAGE_FASTQS: 1
```

Large-file Globus parameters used by the production scripts:

```text
GLOBUS_UPLOAD_LARGE_FILES=1
GLOBUS_SOURCE_ENDPOINT=07446cad-33b8-11f0-8c0c-0afffb017b7d
GLOBUS_DEST_ENDPOINT=61fb8b9a-9b52-456e-928c-30c0fb0140bf
GLOBUS_DEST_BASE_PATH=/ATAC-results-05-05-26
GLOBUS_DELETE_AFTER_TRANSFER=1
large-file transfer options: --recursive --verify-checksum --sync-level checksum
large-file destination pattern: /ATAC-results-05-05-26/<target>/<timepoint>/<sample>_large_files/
```

## Script Provenance

Key production scripts:

```text
scripts/local_morphic_atac_seq/runChromap_libmacs3.sh
scripts/local_morphic_atac_seq/run_nw_5_21_remote_2026_05_05.sh
scripts/local_morphic_atac_seq/run_nw_atacseq_1_storage_docker_2026_05_05.sh
scripts/local_morphic_atac_seq/scripts/bw_from_fragments.sh
scripts/local_morphic_atac_seq/scripts/copyback_and_globus_large_files.sh
scripts/local_morphic_atac_seq/scripts/remote_nw_5_21_copyback_monitor.sh
scripts/local_morphic_atac_seq/scripts/remote_nw_5_21_worker.sh
scripts/remote_morphic_atac_seq/scripts/remote_nw_5_21_worker.sh
```

Selected script checksums:

```text
7d91b137d46bd45376384bd661d3637fabe66907456df6059b8185c610512766  runChromap_libmacs3.sh
6c7734f56dac8e02c6595c9e6082b762b2a92faa943ec8bd15af0fcedd9ea346  run_nw_5_21_remote_2026_05_05.sh
7d0cf3ad45522e68cc31d07256ab7c3a625cdb3921bbd78111a5de8282c1624f  run_nw_atacseq_1_storage_docker_2026_05_05.sh
0e970f8fd02ac47b1afc1d407a979910fb2d57595f61e669d6339ef9da33de08  bw_from_fragments.sh
ad29e383d94200f784b6713b2b7dbf73773f334811c4b88eb60b7745908c5565  copyback_and_globus_large_files.sh
0eb6ee56e52a2d3a176db30a86969bb527c7dd826a058c72ffec778a362c4716  remote_nw_5_21_copyback_monitor.sh
e1935eb265be743b1eddc5c681f4e548b1ea395fa4da0386280050d60309df63  remote_nw_5_21_worker.sh
ed14c5a9599de5155448164c741e5c47ccce7f83fbdb22f797ffb1da93219e6d  Dockerfile.libmacs3-runner
```

The full script checksum list is `scripts/SHA256SUMS`.

Script source repository:

```text
repository: https://github.com/morphic-bio/atac-seq
local source path: /home/lhhung/morphic-atac-seq
base git hash observed at documentation time: 839ae2c31189547a460de963143e4604804b8f53
commit link: https://github.com/morphic-bio/atac-seq/commit/839ae2c31189547a460de963143e4604804b8f53
```

The production wrapper scripts copied into this submission include local
production files that were not all cleanly represented by the base git hash at
documentation time. For exact script identity, use `scripts/SHA256SUMS` and the
copied files in this submission.

## Chromap Binary Provenance

Chromap production binary paths:

```text
local host path used by local Docker worker: /mnt/pikachu/Chromap-suite/chromap
remote worker path used by NW-5-21 worker: /home/lhhung/Chromap-suite/chromap
Chromap version string observed in the remote production Docker image mount: 0.3.3-r519
```

Exact remote worker executable identity:

```text
path: /home/lhhung/Chromap-suite/chromap
mtime: 2026-05-05 09:52:22 UTC
size: 2476000 bytes
sha256: 68d8d47ff3d690966297a4723b6ff0f684f6f5a97ba2c4ac8eb87d3c76b02481
ELF build ID: 94616c279ee89a5454a15421a6f0d00331f14cad
```

The local `/mnt/pikachu/Chromap-suite/chromap` binary has been rebuilt since the
May 5 production run. Its current hash is not treated as production provenance.
The remote worker copy above is the preserved production executable identity for
the NW-5-21 remote portion and was copied from the Chromap-suite host path during
remote deployment.

Chromap source repository:

```text
repository: https://github.com/morphic-bio/Chromap-suite
production-era source hash in local history: 0d41b6350a66f3add2dc9e6f195f64586119909e
commit link: https://github.com/morphic-bio/Chromap-suite/commit/0d41b6350a66f3add2dc9e6f195f64586119909e
```

The production executable does not embed a git commit hash. Use the executable
SHA256 above as the exact binary identifier. The source hash above is the
Chromap-suite git state in local history immediately before the May 5 production
run and contains the bulk ATAC inline FRAG peak path used by the scripts.

## Docker Provenance

Runtime Docker image:

```text
name: morphic-atac-libmacs3:2026-05-05-debian-slim
image ID: sha256:463072f98cb0e638186d6f402f8de27252f7b354d0db53f53d3e80194ee5042e
created: 2026-05-05T16:24:13.398622557Z
RepoDigests: none recorded for this local image
labels: none
Dockerfile: scripts/local_morphic_atac_seq/Dockerfile.libmacs3-runner
Dockerfile sha256: ed14c5a9599de5155448164c741e5c47ccce7f83fbdb22f797ffb1da93219e6d
base image as written: debian:bookworm-slim
```

Chromap was mounted into the container from the host; it was not baked into this
runtime image. The image provided the OS and helper toolchain.

Selected tool versions observed in the image:

```text
samtools 1.16.1
bedtools v2.30.0
bedGraphToBigWig v 2.10
bedGraphToBigWig sha256: 1a1527cf364e1e572a81c7284fc9ccd2b3690b5896baa5b57399864f85ad7771
python3 package: 3.11.2-1+b1
libhts3 package: 1.16+ds-3
```
