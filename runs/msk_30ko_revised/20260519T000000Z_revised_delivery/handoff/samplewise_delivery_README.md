# MSK 30KO h5ad and QC delivery staging

This tree mirrors the previous MSK sample-wise organization:

```text
MSK-05-13-26-large-files/<sample>/
MSK-05-13-26-large-files/<sample>/downstream_genefull_velocyto_cellbender/
```

Intentional exclusions: BAM files, FASTQ files, raw MEX matrices, CellBender raw `.h5` payloads,
per-cell provider `.rds` metadata exports, and obsolete provisional scimilarity label-count TSVs.

Primary AnnData deliverables per sample:

- `downstream_genefull_velocyto_cellbender/filtered_counts.h5ad`
- `downstream_genefull_velocyto_cellbender/default_singlet_filtered_counts.h5ad`
- `downstream_genefull_velocyto_cellbender/feature_libraries/*/*.h5ad`

The main h5ads contain the corrected MSK annotation surface: UCSF-style obs/layers,
Velocyto layers, CellBender `denoised`, CRISPR/LARRY obs fields, `X_scimilarity`,
and provider-seeded RF label fields (`rf_celltype`, `rf_subcelltype`, confidence, margin).
They do not contain copied provider `.rds` per-cell metadata.

Project-level RF model and concordance summaries are under `analysis/`.
See `STAGED_MANIFEST.tsv` for source paths and byte counts.

## Contents by sample

| Sample | Files | Bytes |
| --- | ---: | ---: |
| PROJECT | 15 | 444288506 |
| ES | 66 | 5982817059 |
| DE | 66 | 9244129740 |
| DE_GemX | 61 | 14749145696 |
| PP1 | 66 | 5961125826 |
| PP2 | 66 | 8248449423 |
| S5_1 | 66 | 8795443206 |
| S5_2 | 66 | 7628961329 |
| S6_1 | 66 | 6504655395 |
| S6_2 | 66 | 6952435614 |
