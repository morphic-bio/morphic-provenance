# SLAM-seq PE Result Submission

Prepared for Globus handoff: 2026-05-12T18:59:15Z UTC
README updated: 2026-05-19T22:47:44Z UTC

This directory contains the STAR-SLAM paired-end production results for the
Northwestern SLAM-seq panel, rooted locally at:

```text
/mnt/pikachu/SLAM-Seq-PE-results/prod_full_20260511T103908Z
```

The Globus destination is:

```text
Morphic Processing endpoint 61fb8b9a-9b52-456e-928c-30c0fb0140bf
/SLAM-seq-PE-results/prod_full_20260511T103908Z/
```

This is a derived-results submission. Original input FASTQs are not included.
Large Y/noY BAM and FASTQ side outputs were transferred by per-sample Globus
tasks during production and then cleaned locally after successful transfer.

Detailed run parameters, script versions, GitHub commit links, executable
hashes, Docker image identifiers, and transfer provenance are in
`provenance.md`.

## Directory Structure

```text
.
  README.md
  provenance.md
  MANIFEST.files.tsv
  DESEQ2_GLOBUS_BATCH.tsv
  DESEQ2_GLOBUS_TASK.tsv
  DESEQ2_UPLOAD_FILELIST.txt
  DESEQ2_UPLOAD_FILE_SIZES.tsv
  de/
    input/
    jobs/
    scripts/
    full_modes_20260515T033955Z/
  samples/
    <sample>/
      RUN_COMMAND.sh
      TRANSFER_SUBMITTED.ok
      TRANSFER_TASK.txt
      TRANSFER_CLEANED.ok
      counts/
      logs/
      manifests/
      qc/
      run/
```

The local production root also contains `manifests/`, `logs/`, `runner.pid`,
and `runner.nohup.log`. The per-sample directories are the main result payload.

## Top-Level Files

- `README.md`: this submission guide.
- `provenance.md`: run parameters, source commits, script and binary hashes,
  Docker image identifiers, and Globus transfer details.
- `MANIFEST.files.tsv`: file listing for the local production root, with
  relative path, byte size, and modification time.
- `DESEQ2_GLOBUS_BATCH.tsv`: Globus batch used for the DESeq2 result upload.
- `DESEQ2_GLOBUS_TASK.tsv`: completed DESeq2 upload task metadata.
- `DESEQ2_UPLOAD_FILELIST.txt`: files selected for the DESeq2 handoff.
- `DESEQ2_UPLOAD_FILE_SIZES.tsv`: sizes for the DESeq2 handoff files.

Local-only production manifests are under `manifests/`:

- `run_config.env`: exact production runner settings.
- `samples.tsv`: one row per sample with mode, source FASTQs, and output paths.
- `commands.tsv`: rendered STAR-SLAM command for each sample.
- `r1_files.txt` and `r2_files.txt`: input FASTQ lists.
- `pairing_warnings.tsv`: R1/R2 pairs matched by sample index despite name
  differences.
- `globus_tasks.tsv`: per-sample Globus task IDs from the original upload.

## Result Files

Each sample directory has this general layout:

```text
samples/<sample>/
  RUN_COMMAND.sh
  TRANSFER_SUBMITTED.ok
  TRANSFER_TASK.txt
  TRANSFER_CLEANED.ok
  counts/
    <sample>.SlamQuant.out
    <sample>.SlamQuant.cB.tsv
    <sample>.SlamQuant.out.diagnostics
    <sample>.SlamQuant.out.transitions.tsv
    <sample>.SlamQuant.out.mismatches.tsv
    <sample>.SlamQuant.out.mismatchdetails.tsv
    <sample>.SlamQuant.out.top_mismatches
  qc/
    <sample>.slam_qc.html
    <sample>.slam_qc.json
  run/
    star_Log.out
    star_Log.final.out
    star_Log.progress.out
    star_SJ.out.tab
    star_SlamQuant.grandslam.tsv
    star_slam_qc.html
    star_slam_qc.json
    star_quant.sf
    star_quant.genes.sf
    star_quant.genes.tximport.sf
  logs/
    star.stdout.log
    star.stderr.log
    star.time.log
  manifests/
    globus_batch.tsv
    submit_globus.sh
```

File meanings:

- `SlamQuant.out`: primary per-gene STAR-SLAM table with read counts,
  conversions, callable coverage, NTR, MAP, sigma, and log-likelihood.
- `SlamQuant.cB.tsv`: compact count-binomial SLAM evidence table with columns
  `sample`, `feature_id`, `feature_name`, `nT`, `TC`, and `n`.
- `SlamQuant.out.diagnostics`: SLAM counting diagnostics, including filter and
  assignment summaries.
- `SlamQuant.out.transitions.tsv`, `mismatches.tsv`, and
  `mismatchdetails.tsv`: global and position-level mismatch QC outputs.
- `SlamQuant.grandslam.tsv`: GRAND-SLAM-compatible per-gene SLAM table.
- `slam_qc.html` and `slam_qc.json`: self-contained SLAM QC report and backing
  data.
- `star_quant.sf`: TranscriptVB transcript-level quantification in
  Salmon-compatible schema.
- `star_quant.genes.sf`: gene-level TranscriptVB quantification.
- `star_quant.genes.tximport.sf`: preferred expression-count input for tximport
  and DESeq2.
- `star_Log.final.out`, `star_Log.out`, and `star_Log.progress.out`: STAR run
  logs.
- `star.stdout.log`, `star.stderr.log`, and `star.time.log`: runner-captured
  stdout, stderr, and `/usr/bin/time -v` resource report.
- `globus_batch.tsv`, `TRANSFER_TASK.txt`, and `TRANSFER_CLEANED.ok`: transfer
  provenance for the per-sample upload and local cleanup.

Local `run/star_Aligned.sortedByCoord.out.bam` files are zero-byte placeholders
after cleanup. Use the per-sample Globus task records for large-file provenance.

## DESeq2 Results

DESeq2 expression analysis results are under:

```text
de/full_modes_20260515T033955Z/
```

The DESeq2 analysis used the full TranscriptVB/tximport expression surface:

```text
samples/<sample>/run/star_quant.genes.tximport.sf
```

It did not use `ReadsPerGene.out.tab`, `SlamQuant.out`, or `SlamQuant.cB.tsv`
as ordinary DESeq2 count matrices. SLAM cB and NTR files should be used for
conversion/NTR analyses or count-binomial modeling.

Completed DESeq2 modes:

- `blocked_pairwise`: primary p-value model with `design <- ~ set_id + time`.
- `unblocked_pairwise`: sensitivity model with `design <- ~ time`.
- `collapsed_pairwise`: conservative descriptive model after collapsing split
  samples by timepoint.

Core DESeq2 outputs:

```text
de/full_modes_20260515T033955Z/
  run_config.tsv
  RUN_NOTES.tsv
  jobs/
  logs/
  blocked_pairwise/<target>/<contrast>/
  unblocked_pairwise/<target>/<contrast>/
  collapsed_pairwise/<target>/
  combined_summaries/
```

The combined summaries include `run_inventory.tsv`,
`padj_counts_by_mode_contrast.tsv`, mode-specific contrast summaries, and
`gene_level_consensus.tsv.gz`.

## Counts

Counts from the local production root at documentation time:

```text
samples: 290
samples with STAR final logs: 290
samples with SlamQuant.out: 290
samples with SlamQuant.cB.tsv: 290
samples with star_quant.genes.tximport.sf: 290
samples with TRANSFER_CLEANED.ok: 290
local production-root files: 11106
local curated remaining-results staging files: 8422
local DESeq2 staging files: 2203
```

Representative local file-type counts:

```text
.sf files:     870
.tsv files:    2945
.tsv.gz files: 560
.html files:   580
.json files:   580
.log files:    1376
.ok files:     580
.sh files:     582
.bam files:    290 zero-byte local placeholders after cleanup
```

## Sample Notes

Most targets have three replicates at 0h, 6h, and 24h. Special or incomplete
groups include:

- `ARID1A`: 0h/6h/24h triplicates plus `ARID1A-no4su_S50`.
- `Rad21_naid22`: 0h/6h/24h triplicates plus `Rad21_naid22_nos4u_S44`.
- `CCNC`, `CHD4`, `CPSF2`, `SSU72`, and `U2AF2`: no 24h triplicate group in
  this run.
- `HDAC3` and `NAT10`: 24h group has two recorded samples.
- `RAD21`: only the 6h triplicate is present.
- `MYC`: uses `MYC_D1/D2/D3` and `MYC_T1/T2` naming rather than standard time
  labels.

Six samples in `manifests/pairing_warnings.tsv` were paired by sample index
because the R2 gene label did not match the R1 gene label. Review those samples
before downstream biological interpretation of SSU72 or TFDP1.

## Notes

- Treat this directory as read-only result provenance.
- Original FASTQs are not part of this submission.
- Per-sample `RUN_COMMAND.sh` files are the most direct command provenance.
- `MANIFEST.files.tsv` is the full file manifest and is intentionally not
  duplicated inline in this README.
