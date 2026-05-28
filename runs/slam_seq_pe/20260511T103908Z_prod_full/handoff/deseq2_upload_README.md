# STAR-SLAM PE Production Results README

Generated for the SLAM-seq PE production run:

`/mnt/pikachu/SLAM-Seq-PE-results/prod_full_20260511T103908Z`

Curated Globus staging tree:

`/mnt/pikachu/SLAM-Seq-PE-results/prod_full_20260511T103908Z_remaining_globus_upload_20260512T184310Z`

DESeq2-only Globus staging tree:

`/mnt/pikachu/SLAM-Seq-PE-results/prod_full_20260511T103908Z_deseq2_globus_upload_20260515T061311Z`

Globus destination root recorded by the runner:

`SLAM-seq-PE-results/prod_full_20260511T103908Z`

This README describes the result layout, the STAR-SLAM methodology used for the
paired-end production run, the main changes from the earlier single-end workflow,
the output file types, and the completed DESeq2 differential-expression run.

## Run Summary

- Input FASTQs: `/mnt/pikachu/SLAM-Seq`
- Samples processed: 290 paired-end samples
- Run date: 2026-05-11 to 2026-05-12 UTC
- Runner checkout: `/mnt/pikachu/STAR-suite-slam-pe-prod`
- Runner script: `scripts/run_slam_prod_set.sh`
- STAR binary: `/mnt/pikachu/STAR-suite-slam-pe-prod/core/legacy/source/STAR`
- Genome index: `/storage/autoindex_110_44/bulk_index`
- SNP mask: `/mnt/pikachu/slam_blank_artifacts_20260201/mask/snps_from_vcf.bed.gz`
- Threads per sample: 16
- BAM order requested: `SortedByCoordinate`
- SLAM strandness: `Sense`
- SLAM count-binomial output format: `star`
- Minimum callable length: 30
- Globus source endpoint: `07446cad-33b8-11f0-8c0c-0afffb017b7d`
- Globus destination endpoint: `61fb8b9a-9b52-456e-928c-30c0fb0140bf`

The complete per-sample manifest is in `manifests/samples.tsv`. The runner wrote
one STAR command per sample to `manifests/commands.tsv` and to each sample's
`RUN_COMMAND.sh`.

## Result Layout

Top-level files and directories:

- `README.md`: this file.
- `manifests/run_config.env`: exact run configuration values.
- `manifests/samples.tsv`: one row per sample with mode, R1, R2, and output paths.
- `manifests/commands.tsv`: rendered STAR command for each sample.
- `manifests/r1_files.txt`: R1 FASTQs used.
- `manifests/r2_files.txt`: R2 FASTQs used.
- `manifests/pairing_warnings.tsv`: files paired by sample index despite name mismatches.
- `manifests/globus_tasks.tsv`: per-sample Globus task IDs from the original upload.
- `logs/*.globus_submit.log`: Globus CLI submission output per sample.
- `samples/<sample>/`: per-sample outputs.

Per-sample layout:

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

The curated `_remaining_globus_upload_...` staging tree was made for smaller
results handoff and explicitly excludes `*.bam`, `*.bai`, `*.fastq.gz`, and
`*.fq.gz`. The original per-sample Globus batches are recorded in each
`samples/<sample>/manifests/globus_batch.tsv`; those manifests are the authority
for what each per-sample upload attempted.

The production runner cleaned transferred large local outputs after Globus
success. Local zero-byte BAM placeholders may remain in `run/`; use the Globus
task records and batch manifests rather than local placeholder size to infer
whether large outputs were transferred.

## Sample Groupings

Most targets have a time-course layout with three replicates at each of 0h, 6h,
and 24h:

```text
<target>-0h-1/2/3
<target>-6h-1/2/3
<target>-24h-1/2/3
```

Examples include `ARID3B`, `ATR`, `CHAF1A`, `FOXA1`, `FOXM1`, `INO80`,
`NUP_133`, `NUP_153_`, `NUP_210`, `NUP_214`, `NUP_62`, `NUP_88`, `RBBP7`,
`SMARCA1`, `SMARCA4`, `SMARCA5`, `SMARCB1`, `SMARCC1`, `SMARCD1`, `TFDP1`,
`WDHD1`, `YRDC`, `YY1`, and `prmt5`.

Some groups are intentionally incomplete or have special naming:

- `ARID1A`: 0h/6h/24h triplicates plus `ARID1A-no4su_S50`.
- `Rad21_naid22`: 0h/6h/24h triplicates plus `Rad21_naid22_nos4u_S44`.
- `CCNC`, `CHD4`, `CPSF2`, `SSU72`, and `U2AF2`: no 24h triplicate group in this run.
- `HDAC3` and `NAT10`: 24h group has two recorded samples.
- `RAD21`: only the 6h triplicate is present.
- `MYC`: uses `MYC_D1/D2/D3` and `MYC_T1/T2` naming rather than the standard time labels.

Six samples in `manifests/pairing_warnings.tsv` were paired by sample index
because the R2 gene label did not match the R1 gene label:

- `SSU72-0h-2_S35` paired with `SSU73-0h-2_S35_R2_001.fastq.gz`
- `SSU72-0h-3_S36` paired with `SSU74-0h-3_S36_R2_001.fastq.gz`
- `SSU72-6h-1_S37` paired with `SSU75-6h-1_S37_R2_001.fastq.gz`
- `SSU72-6h-2_S38` paired with `SSU76-6h-2_S38_R2_001.fastq.gz`
- `SSU72-6h-3_S39` paired with `SSU77-6h-3_S39_R2_001.fastq.gz`
- `TFDP1-24h-3_S198` paired with `TFDP2-24h-3_S198_R2_001.fastq.gz`

The pairing rule was to preserve the shared sample index when exactly one R2
candidate existed for that index.

## STAR-SLAM Methodology

Each sample was processed as an independent paired-end STAR run. This avoids a
single monolithic batch job and allows each sample's results and Globus transfer
to complete independently.

Core STAR-SLAM settings:

```text
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
--slamSnpMaskIn /mnt/pikachu/slam_blank_artifacts_20260201/mask/snps_from_vcf.bed.gz
--slamStrandness Sense
--slamMinCallableLength 30
```

Fixed trims used in this production run:

```text
single-end fallback: 5p=8, 3p=12
paired-end mate 1:  5p=8, 3p=13
paired-end mate 2:  5p=19, 3p=14
```

These paired-end trims were fixed from the no-sU 100K smoke performed on
2026-05-11 and then applied consistently across the PE production set.

The SLAM quantification model counts T-to-C conversion evidence after applying
strandness, SNP masking, mate-specific trimming, and the callable-length gate.
The primary biological endpoint in `SlamQuant.out` is NTR. The count-binomial
file preserves the underlying binned evidence for downstream models.

## Methodology Changes Since The Earlier SE Workflow

The earlier SLAM workflow was single-end oriented. The production PE workflow
differs in these important ways:

- Reads are supplied as paired mates (`R1 R2`) instead of R1-only input.
- Mate-specific SLAM trimming is used:
  `--slamCompatTrim5pMate1`, `--slamCompatTrim3pMate1`,
  `--slamCompatTrim5pMate2`, and `--slamCompatTrim3pMate2`.
- PE transition coordinates were fixed so mate 2 positions and overlap status
  are represented correctly in mismatch summaries.
- TranscriptVB paired-end autodetection was repaired before this run; the
  production command uses `--quantVBLibType A`, which now resolves PE geometry
  correctly instead of dropping compatible alignments.
- `--quantTranscriptomeSAMoutput BanSingleEnd` was added so transcriptome
  quantification does not admit singleton fragments after PE filtering.
- The count-binomial output (`--slamCbOut 1`) is new relative to the older
  SE-oriented results.
- `--slamMinCallableLength 30` was added to drop reads or pairs with too little
  callable T context after trimming and SNP masking.
- The production runner now submits Globus transfers sample-by-sample and reaps
  successful transfers, allowing local large BAM/FASTQ outputs to be cleaned
  without waiting for the entire panel.

## Output Files

### `counts/<sample>.SlamQuant.out`

Primary STAR-SLAM gene table. Columns:

```text
Gene, Symbol, ReadCount, Conversions, Coverage, NTR, MAP, Sigma, LogLikelihood
```

Use this for per-gene NTR summaries, conversion totals, and basic STAR-SLAM
interpretation.

### `run/star_SlamQuant.grandslam.tsv`

GRAND-SLAM-compatible table. It contains per-gene read count, NTR-like summary
columns, conversion coverage, double-hit fields, and gene length fields using a
schema expected by tools or notebooks written around GRAND-SLAM output.

### `counts/<sample>.SlamQuant.cB.tsv`

New count-binomial output. This is the most useful model-ready SLAM evidence
table because it preserves the distribution of observed conversion counts per
gene instead of only reporting aggregate NTR.

STAR schema used here:

```text
sample, feature_id, feature_name, nT, TC, n
```

Field meanings:

- `sample`: sample label as written by STAR-SLAM. In this production run the
  internal label is `star`.
- `feature_id`: gene identifier.
- `feature_name`: gene symbol, or the gene identifier if no symbol is available.
- `nT`: callable T sites in the read or read pair after filters.
- `TC`: observed T-to-C conversions in that read or read-pair bin.
- `n`: weighted number of reads or fragments in the `(feature_id, nT, TC)` bin;
  this can be fractional because multimapping and gene-assignment weights are
  retained.

Aggregating the cB table by `feature_id` reconstructs the main SLAM quantities:

```text
ReadCount   = sum(n)
Conversions = sum(TC * n)
Coverage    = sum(nT * n)
```

An EZbakR-like cB format is supported by STAR-SLAM (`--slamCbFormat ezbakr`),
but this production run used the compact STAR format.

### `counts/<sample>.SlamQuant.out.diagnostics`

Run diagnostics for SLAM counting, including processed reads and drops from SNP
masking, strandness filtering, callable-length filtering, missing genes, and
assignment-weight conditions.

### `counts/<sample>.SlamQuant.out.transitions.tsv`

Global mismatch transition matrix by genomic base and read base.

### `counts/<sample>.SlamQuant.out.mismatches.tsv`

Mismatch summary stratified by category, condition, orientation, genomic base,
and read base.

### `counts/<sample>.SlamQuant.out.mismatchdetails.tsv`

Position-level mismatch details. For PE data this includes overlap and opposite
strand flags; this file is mainly for QC and debugging positional artifacts.

### `qc/<sample>.slam_qc.html` and `qc/<sample>.slam_qc.json`

Self-contained SLAM QC report and its JSON backing data. These summarize
position-specific T-to-C rates, trim choices, and mismatch/quality behavior.

### `run/star_quant.sf`

Transcript-level TranscriptVB quantification in Salmon-compatible `quant.sf`
schema.

### `run/star_quant.genes.sf`

Gene-level TranscriptVB quantification before tximport-compatible summarization.

### `run/star_quant.genes.tximport.sf`

Gene-level TranscriptVB output prepared for downstream `tximport` and DESeq2
workflows. This is the preferred expression-count input for DESeq2.

### STAR Logs

- `run/star_Log.final.out`: standard STAR completion and alignment summary.
- `run/star_Log.out`: full STAR parameter and runtime log.
- `run/star_Log.progress.out`: progress log.
- `logs/star.stdout.log`: stdout captured by the runner.
- `logs/star.stderr.log`: stderr captured by the runner.
- `logs/star.time.log`: `/usr/bin/time -v` resource report.

## DESeq2 Analysis Setup And Covariates

DESeq2 was run on 2026-05-15 from the Salmon-compatible STAR TranscriptVB
expression outputs. The production DESeq2 results are under:

```text
de/full_modes_20260515T033955Z/
```

The DESeq2-only Globus handoff package includes this README and a curated `de/`
tree with DESeq2 inputs, runnable scripts, run logs, per-target outputs, and
core combined summaries. It intentionally excludes the later exploratory
biological interpretation analyses, including `known_correlate*`,
`literature_*`, `tier1_*`, and target-mRNA self-check tables.

Pinned runtime:

- Build script: `/mnt/pikachu/STAR-suite-slam-pe-prod/scripts/docker/build_slam_deseq2_image.sh`
- Dockerfile: `/mnt/pikachu/STAR-suite-slam-pe-prod/docker/slam-deseq2/Dockerfile`
- Image tag: `star-suite/slam-deseq2:bioc3.23-deseq2-1.52.0-tximport-1.40.0`
- Base image: `bioconductor/bioconductor_docker:RELEASE_3_23-r-4.6.0`
- Bioconductor: 3.23
- DESeq2: 1.52.0
- tximport: 1.40.0

Expression DESeq2 input surface:

- Use `samples/<sample>/run/star_quant.genes.tximport.sf`.
- Import with `tximport`, using gene IDs in the `Name` column.
- Construct `colData` from the sample name and `manifests/samples.tsv`.
- Exclude no-sU/no4sU blanks from expression differential tests unless the
  contrast is explicitly about background controls.

Core covariates to parse:

- `target`: perturbation or target label, e.g. `ARID1A`, `SMARCA4`, `prmt5`.
- `timepoint`: `0h`, `6h`, `24h`, or special labels for nonstandard groups.
- `replicate`: replicate number where present.
- `sample_index`: the sequencing sample suffix, e.g. `S43`.
- `protocol_group`: standard time-course, no-sU/no4sU blank, MYC D/T group, or
  other nonstandard naming group.
- `pairing_warning`: true for samples listed in `manifests/pairing_warnings.tsv`.
- Optional `batch`: only include if an external batch annotation is provided;
  the run manifest itself does not define multiple technical batches.

Completed DESeq2 modes:

1. `blocked_pairwise`: primary p-value model for each target/contrast.

   ```r
   design <- ~ set_id + time
   ```

   This treats the split plates/sets as a blocking covariate where possible and
   tests timepoint differences within a target. The primary contrasts are
   `6h_vs_0h`, `24h_vs_0h`, and `24h_vs_6h` when those timepoints exist.

2. `unblocked_pairwise`: optimistic sensitivity model.

   ```r
   design <- ~ time
   ```

   This treats the replicate samples as independent observations. Use it as a
   sensitivity bound, not as the sole inference layer when split plates are not
   true biological replicates.

3. `collapsed_pairwise`: conservative descriptive model.

   Technical/split samples were collapsed by timepoint before comparison. This
   emits fold-change and count summaries but no DESeq2 p-values.

Run scope and status:

- Input samples in DE manifest: 290.
- Target labels in DE job table: 35.
- Distinct perturbed genes after normalizing `RAD21`/`Rad21_naid22`: 34.
- Ready targets run through the full panel: 33.
- Review-only targets kept out of the full run: `MYC`, `RAD21`.
- Valid pairwise contrasts per mode: 89.
- Skipped p-value contrasts: 10, caused by targets lacking a 24h group.
- Failed jobs: 0.
- Local lane: `blocked_pairwise`.
- Remote lane `10.159.4.53`: `unblocked_pairwise`.
- Remote lane `128.208.252.232`: `collapsed_pairwise`.
- Remote jobs staged to `~/remotes/...` and copied back; NFS was not used.

DESeq2 file layout:

```text
de/
  input/
    sample_manifest.tsv
    tx2gene.tsv
    gene_id_symbol.tsv
  jobs/
    deseq2_target_jobs.tsv
    deseq2_dual_mode_jobs.tsv
    deseq2_job_summary.txt
  scripts/
    run_deseq2_target.R
    run_collapsed_technical_target.R
    run_pairwise_deseq2_target.R
    run_deseq2_remote_target.sh
    run_full_deseq2_modes.sh
  full_modes_20260515T033955Z/
    run_config.tsv
    RUN_NOTES.tsv
    jobs/
    logs/
    blocked_pairwise/<target>/<contrast>/
    unblocked_pairwise/<target>/<contrast>/
    collapsed_pairwise/<target>/
    combined_summaries/
```

Per-target p-value model outputs:

```text
blocked_pairwise/<target>/<contrast>/
unblocked_pairwise/<target>/<contrast>/
  <contrast>.deseq2.tsv.gz
  <contrast>.summary.tsv
  dds.rds
  input_manifest.tsv
  normalized_counts.tsv.gz
  size_factors.tsv
```

Per-target collapsed outputs:

```text
collapsed_pairwise/<target>/
  <contrast>.collapsed_descriptive.tsv.gz
  collapsed_counts.lengthScaledTPM.tsv.gz
  collapsed_normalized_counts.tsv.gz
  contrast_summaries.collapsed.tsv
  sample_counts_by_time.tsv
  size_factors.collapsed.tsv
```

Core combined summaries included in the DESeq2 handoff:

```text
combined_summaries/
  run_inventory.tsv
  padj_counts_by_mode_contrast.tsv
  blocked_pairwise.contrast_summaries.tsv
  unblocked_pairwise.contrast_summaries.tsv
  collapsed_pairwise.contrast_summaries.collapsed.tsv
  gene_level_consensus.tsv.gz
```

The full `gene_level_consensus.tsv.gz` joins blocked, unblocked, and collapsed
pairwise results by target, contrast, and gene ID. It is a DESeq2 result
aggregation, not a biological interpretation table.

SLAM-specific cB/NTR outputs should not be used as ordinary DESeq2 count
matrices. Use DESeq2 for expression abundance from `star_quant.genes.tximport.sf`.
Use `SlamQuant.out` and `SlamQuant.cB.tsv` for SLAM conversion/NTR analyses or
count-binomial modeling.

## QC And Validation Notes

- Each sample has `RUN_COMMAND.sh`; this is the most direct provenance record
  for the STAR command.
- Each sample has `star_Log.final.out`; use it to confirm STAR completion.
- The runner captured resource use in `logs/star.time.log`.
- `manifests/pairing_warnings.tsv` should be reviewed before downstream
  biological interpretation of the affected SSU72 and TFDP1 samples.
- The cB output is large: across 290 samples, `*.SlamQuant.cB.tsv` totals about
  4.0 GiB locally.
- The TranscriptVB transcript-level outputs across 290 samples total about
  2.7 GiB locally.
- The curated upload staging tree excludes large BAM/FASTQ files by design;
  use the original Globus per-sample task records for large-file provenance.

## Re-running Or Reconstructing Commands

To reconstruct the exact command for one sample:

```bash
less samples/<sample>/RUN_COMMAND.sh
```

To list all samples and source FASTQs:

```bash
cut -f1-4 manifests/samples.tsv | column -t -s $'\t'
```

To inspect run configuration:

```bash
cat manifests/run_config.env
```

To inspect Globus task IDs:

```bash
cut -f1,3 manifests/globus_tasks.tsv
```
