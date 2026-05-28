# SLAM-seq PE Submission Provenance

Prepared for Globus handoff: 2026-05-12T18:59:15Z UTC
Provenance split from README: 2026-05-19T22:47:44Z UTC

This file records execution parameters, source repositories, script versions,
binary hashes, Docker image identifiers, and Globus transfer details for:

```text
/mnt/pikachu/SLAM-Seq-PE-results/prod_full_20260511T103908Z
```

## Globus Destination

Remote destination:

```text
Morphic Processing endpoint 61fb8b9a-9b52-456e-928c-30c0fb0140bf
/SLAM-seq-PE-results/prod_full_20260511T103908Z/
```

Source endpoint:

```text
pikachu endpoint 07446cad-33b8-11f0-8c0c-0afffb017b7d
```

Completed upload tasks already associated with this submission:

```text
task_id: 0c11644c-4e33-11f1-a502-0afffe4617ab
label:   SLAM PE remaining results prod_full_20260511T103908Z
source:  prod_full_20260511T103908Z_remaining_globus_upload_20260512T184310Z
dest:    /SLAM-seq-PE-results/prod_full_20260511T103908Z/
status:  SUCCEEDED, 8421/8421 files, 9530222552 bytes
options: verify_checksum=true, preserve_timestamp=true, sync_level=3

task_id: 8dd10a29-5025-11f1-b61f-0ea3589134b3
label:   STAR-suite SLAM PE DESeq2 prod_full_20260511T103908Z
source:  prod_full_20260511T103908Z_deseq2_globus_upload_20260515T061311Z
dest:    /SLAM-seq-PE-results/prod_full_20260511T103908Z/
status:  SUCCEEDED, 2202/2202 files, 1762703149 bytes

task_id: e2facbfe-5025-11f1-b5c2-02535127e3d7
label:   STAR-suite SLAM PE DESeq2 upload metadata prod_full_20260511T103908Z
status:  SUCCEEDED, 3/3 files, 797725 bytes
```

Per-sample large-output upload tasks are recorded in:

```text
manifests/globus_tasks.tsv
samples/<sample>/TRANSFER_TASK.txt
samples/<sample>/manifests/globus_batch.tsv
```

There are 290 per-sample `TRANSFER_CLEANED.ok` markers, indicating that the
runner observed successful transfer before local cleanup.

## Production Run Parameters

The production runner settings are recorded in `manifests/run_config.env`:

```text
FASTQ_DIR=/mnt/pikachu/SLAM-Seq
OUT_BASE=/mnt/pikachu/SLAM-Seq-PE-results/prod_full_20260511T103908Z
STAR_BIN=/mnt/pikachu/STAR-suite-slam-pe-prod/core/legacy/source/STAR
STAR_INDEX=/storage/autoindex_110_44/bulk_index
SNP_MASK=/mnt/pikachu/slam_blank_artifacts_20260201/mask/snps_from_vcf.bed.gz
THREADS=16
OUT_SAM_ORDER=SortedByCoordinate
SLAM_STRANDNESS=Sense
SLAM_CB_FORMAT=star
SLAM_MIN_CALLABLE_LENGTH=30
SE_ONLY=0
SE_TRIM5P=8
SE_TRIM3P=12
PE_TRIM5P_M1=8
PE_TRIM3P_M1=13
PE_TRIM5P_M2=19
PE_TRIM3P_M2=14
GLOBUS_SRC_ENDPOINT=07446cad-33b8-11f0-8c0c-0afffb017b7d
GLOBUS_DST_ENDPOINT=61fb8b9a-9b52-456e-928c-30c0fb0140bf
GLOBUS_DST_ROOT=SLAM-seq-PE-results
WAIT_FOR_FINAL_GLOBUS=1
CLEANUP_AFTER_GLOBUS=1
```

The production command was:

```bash
bash scripts/run_slam_prod_set.sh \
  --outdir /mnt/pikachu/SLAM-Seq-PE-results/prod_full_20260511T103908Z \
  --threads 16 \
  --globus-dst-endpoint 61fb8b9a-9b52-456e-928c-30c0fb0140bf \
  --globus-dst-root SLAM-seq-PE-results
```

Core STAR-SLAM argv pattern:

```text
STAR
  --runThreadN 16
  --genomeDir /storage/autoindex_110_44/bulk_index
  --readFilesIn <R1.fastq.gz> <R2.fastq.gz>
  --readFilesCommand zcat
  --outSAMtype BAM SortedByCoordinate
  --outSAMattributes NH HI AS nM MD
  --outSAMprimaryFlag OneBestScore
  --emitNoYBAM yes
  --keepBAM no
  --emitYNoYFastq yes
  --emitYNoYFastqCompression gz
  --quantMode TranscriptVB
  --quantTranscriptomeSAMoutput BanSingleEnd
  --quantVBgcBias 1
  --quantVBgenes 1
  --quantVBgenesMode Tximport
  --quantVBLibType A
  --slamQuantMode 1
  --slamGrandSlamOut 1
  --slamCbOut 1
  --slamCbFormat star
  --slamStrandness Sense
  --slamSnpMaskIn /mnt/pikachu/slam_blank_artifacts_20260201/mask/snps_from_vcf.bed.gz
  --slamMinCallableLength 30
  --slamCompatTrim5pMate1 8
  --slamCompatTrim3pMate1 13
  --slamCompatTrim5pMate2 19
  --slamCompatTrim3pMate2 14
```

The exact rendered command for each sample is in:

```text
samples/<sample>/RUN_COMMAND.sh
manifests/commands.tsv
```

## STAR-suite Source Provenance

The production run was launched from an isolated checkout:

```text
local path: /mnt/pikachu/STAR-suite-slam-pe-prod
repository: https://github.com/morphic-bio/STAR-suite
commit: 9758a2697b8e9e753584d1d095f8f44695db0c14
commit link: https://github.com/morphic-bio/STAR-suite/commit/9758a2697b8e9e753584d1d095f8f44695db0c14
commit date: 2026-05-11 08:12:57 +0000
commit subject: Wait for final SLAM Globus cleanup
working tree at documentation time: clean
```

The runbook and later MCP workflow references used for documentation checks are
in a newer STAR-suite checkout:

```text
local path: /mnt/pikachu/STAR-suite-ocm-prod-c535e32
repository: https://github.com/morphic-bio/STAR-suite
commit: c535e327f626a61a601b5472b1589511ad6a8d9e
commit link: https://github.com/morphic-bio/STAR-suite/commit/c535e327f626a61a601b5472b1589511ad6a8d9e
commit date: 2026-05-19 07:05:53 +0000
commit subject: Add native OCM multi MEX materializer
documentation checkout status: dirty in unrelated OCM files
```

## Binary Provenance

STAR production binary:

```text
path: /mnt/pikachu/STAR-suite-slam-pe-prod/core/legacy/source/STAR
STAR version: 2.7.11b
size: 8716384 bytes
mtime: 2026-05-11 08:13:38.881404244 +0000
sha256: 76e1fdd481785123d6dca961483283ca93fee41a9fde5faab5ca1b277568edf8
source commit: 9758a2697b8e9e753584d1d095f8f44695db0c14
```

The STAR executable does not embed the source commit in the version string; the
SHA256 above is the exact executable identifier.

## Script Provenance

Production scripts and checksums:

```text
b4e22a2230a84fc2a6d591fa339cfb27d93ba5db33431c13fe064fb2a568cd28  /mnt/pikachu/STAR-suite-slam-pe-prod/scripts/run_slam_prod_set.sh
7ccc644346c955b34563615c286dcf9dacda865545e648e776475e63fb15b840  /mnt/pikachu/STAR-suite-slam-pe-prod/scripts/docker/build_slam_deseq2_image.sh
8d165bb37e45d4152fc55fbeacabc2df6a881b963b7ce04edd8111ea1e5caa95  /mnt/pikachu/STAR-suite-slam-pe-prod/docker/slam-deseq2/Dockerfile
```

Documentation and workflow reference checksums:

```text
410c379d61012e2cd93a7898c4e30716b473c880a4dfe02391800a4a483483f6  /mnt/pikachu/STAR-suite-ocm-prod-c535e32/mcp_server/workflows/slam_pe_production.yaml
77a24ded3e99352355ad939f8911edc5032356b589afb454ee83b99e7e4c6b0d  /mnt/pikachu/STAR-suite-ocm-prod-c535e32/mcp_server/workflows/slam_deseq2_container.yaml
```

DESeq2 analysis scripts copied into the handoff:

```text
19a648a201e52e653d4b44974446205a469bc5c04a52374ee0e94cde5635568a  de/scripts/run_deseq2_target.R
888a9372ddfdcdc9f9e59f3f6b7cdbbb25e74d7bdfc15a1de94cd64dcd8853a0  de/scripts/run_pairwise_deseq2_target.R
84d46c787ec5997cc880a0102375c7b6ee4b3f4db91248a3c62291a8705085fe  de/scripts/run_collapsed_technical_target.R
93c4c87d0d6ed7f2b07280dd502fe1249ddc347b8af85ec82aa8af6d7a93003e  de/scripts/run_full_deseq2_modes.sh
c54664a9ebcddf4bdff3867c43aa46a38162be20400f2b2dcc4710a39d0aac03  de/scripts/run_deseq2_remote_target.sh
```

## Docker Provenance

DESeq2 analysis image:

```text
image tag: star-suite/slam-deseq2:bioc3.23-deseq2-1.52.0-tximport-1.40.0
image id: sha256:f459b07c514becf527e3e151c486c161f4ecee5b628474f6d0a224bc6537664e
created: 2026-05-11T03:24:41.234692157Z
architecture: amd64
os: linux
repo digests: []
```

Dockerfile parameters:

```text
base image: bioconductor/bioconductor_docker:RELEASE_3_23-r-4.6.0
Bioconductor: 3.23
DESeq2: 1.52.0
tximport: 1.40.0
```

The base image was not present locally at documentation time as a separate
Docker image tag, so the local image ID above is the exact recorded container
identifier for this handoff.

## DESeq2 Runtime

The completed DESeq2 run is recorded in
`de/full_modes_20260515T033955Z/run_config.tsv`:

```text
run_root=/mnt/pikachu/SLAM-Seq-PE-results/prod_full_20260511T103908Z/de/full_modes_20260515T033955Z
out_root=/mnt/pikachu/SLAM-Seq-PE-results/prod_full_20260511T103908Z
de_root=/mnt/pikachu/SLAM-Seq-PE-results/prod_full_20260511T103908Z/de
threads_per_job=16
image=star-suite/slam-deseq2:bioc3.23-deseq2-1.52.0-tximport-1.40.0
remote_hosts=10.159.4.53 128.208.252.232
created_utc=2026-05-15T03:48:50Z
finished_utc=2026-05-15T04:00:10Z
status=complete
samples=290
ready_targets=33
jobs_total=99
```

`de/jobs/deseq2_job_summary.txt` records:

```text
samples=290
targets=35
ready_targets=33
review_targets=2
pilot_target=ARID1A
primary_design=per-target fallback ~ time; no4SU controls excluded from primary model
```

DESeq2 result transfer metadata is in `DESEQ2_GLOBUS_TASK.tsv`.
