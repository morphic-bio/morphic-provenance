# JAX scRNAseq01 STAR-suite Flex Rerun Provenance

Generated UTC: 2026-05-24T09:28:57Z

## Source Inputs

Raw FASTQ root:
  /mnt/pikachu/JAX_sequences/JAX_scRNAseq01

Metadata workbook:
  /mnt/pikachu/JAX_sequences/JAX_scRNAseq01/DPC_metadata_template_scRNAseq1_completed.xlsx

Sample probe catalog:
  /mnt/pikachu/JAX_sequences/JAX_scRNAseq01/probe-barcodes-fixed-rna-profiling-rna.txt

Previous delivered release:
  /mnt/pikachu/JAX_scRNAseq01-12-28-25

Previous production roots:
  /mnt/pikachu/prod-12-28/SC2300771
  /mnt/pikachu/prod-12-28/SC2300772

## STAR-suite And Build

Repository:
  /mnt/pikachu/STAR-suite

STAR binary:
  /mnt/pikachu/STAR-suite/core/legacy/source/STAR

Git commit:
  d70a03e407f45b743efa60c7d032d6d2e1a80123

STAR version:
  1.0.0

Git status capture:
  metadata/star_suite_git_status.txt

Clean build commands:
  make -C core/legacy/source clean
  make -C core/legacy/source -j8 STAR

## Reference And Probe Inputs

STAR index:
  /storage/flex_filtered_reference_2024/star_index

2024-A probe list:
  /storage/flex_filtered_reference_2024/star_index/flex_probe_artifacts/probe_list.txt

2024-A probe-set CSV:
  /mnt/pikachu/process_features/tables/Chromium_Human_Transcriptome_Probe_Set_v1.1.0_GRCh38-2024-A.csv

Cell barcode whitelist:
  /storage/scRNAseq_output/whitelists/737K-fixed-rna-profiling.txt

Full sample-tag whitelist:
  /mnt/pikachu/flex/tables/sample_whitelist_full_16.tsv

Hash cache:
  /storage/downsampled_100K/SC2300771/results/flex_h01_2024_20260320_081246/h01_cache.bin

The count runs used the 18,129-entry 2024-A probe list. The raw-folder
2020-A probe CSV was not used.

## Count-Run Mode

Both libraries used STAR-suite Flex hash/no-align mode:
  --soloHashScreenFile /storage/downsampled_100K/SC2300771/results/flex_h01_2024_20260320_081246/h01_cache.bin
  --flexPipeline yes
  --flexPipelineNTriage 0
  --flexPipelineNSolo 0
  --flexNoAlign 1
  --outSAMtype None

Y-removal was not enabled. Release copies of STAR logs, command files,
completion markers, and flexfilter_summary.tsv are under
metadata/SC230077*_hash_noalign/.

## CellBender

CellBender outputs, if present, were generated through the remote GPU path only.
The launcher included --cellbender-gpu; the remote helper adds Docker --gpus all
and CellBender --cuda when that flag is present.

Remote host:
  10.159.4.53

Remote root:
  /home/lhhung/jax_scrnaseq01_remote_cellbender

Per-sample logs:
  counts/<sample>/remote_cellbender*.log

## Validation And QC

QC manifest:
  validation/qc_manifest.tsv

SC2300771 CR9 parity:
  validation/SC2300771_flex_parity_cr9/

H5AD comparison:
  validation/jax_scrnaseq01_h5ad_compare.tsv

## Globus

Source endpoint:
  07446cad-33b8-11f0-8c0c-0afffb017b7d

Destination endpoint:
  61fb8b9a-9b52-456e-928c-30c0fb0140bf

Destination root:
  /JAX_scRNAseq01_2024_STAR_suite/JAX_scRNAseq01_2024_star_suite_20260524_080700

Release transfer task:
  905a80c5-5752-11f1-9000-0affd989f133

Release transfer status:
  SUCCEEDED

Globus task JSON, when available, is copied to validation/globus_transfer_task_final.json.

## Checksums

Checksums for release payload files are in CHECKSUMS.sha256. The checksum file
does not include itself.
