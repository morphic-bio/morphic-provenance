JAX scRNAseq02 h5ad/QC handoff packet
generated_utc=2026-05-22T13:55:26Z
source_run_root=/mnt/pikachu/JAX_scRNAseq02_processed/ocm_prod_batch_flex_native_yremove_trace_20260521T034223Z
destination_root=/JAX_scRNAseq02_processed/JAX-scRNAseq02-5-22-26
feature_files=excluded
payload_files=170
payload_bytes=41251425950

This packet contains the completed downstream sample outputs present at build time. The live production run still has later libraries queued behind generated-large-file Globus cleanup.

Layout mirrors the MSK 30KO h5ad/QC delivery tree:

  <sample>/downstream_genefull_velocyto_cellbender/

Included per completed sample: h5ad deliverables, adaptive QC metadata,
gene QC plots, CellBender reports/logs/metrics, and barcode lists.
Excluded: raw CellBender .h5 payloads, checkpoints, matplotlib font caches,
FASTQs, BAMs, and raw MEX matrices.

Files:
- MANIFEST.tsv: payload files only.
- PROVENANCE.tsv: payload plus packet metadata files, with source paths and destinations.
- PROVENANCE.md: packet-level provenance summary.
- globus_batch.tsv: batch submitted to Globus.

Contents by sample:

sample	files	bytes
EPAS1-Day-4	17	6453433461
GCM1-Day-4	17	3713887221
GCM1-Day-5	17	4127229611
GRHL1-Day-4	17	2969970998
GRHL1-Day-5	17	4829631249
OVOL1-Day-4	17	3123337415
OVOL1-Day-5	17	3884291541
WT-PrS-20pct-Day-4	17	3080854969
WT-PrS-20pct-Day-5	17	3017215853
WT-PrS-3pct-Day-4	17	6051573632
