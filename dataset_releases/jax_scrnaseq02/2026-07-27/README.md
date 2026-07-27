# JAX scRNAseq02 completion overlay 2026-07-27

## Summary

This release is an additive completion overlay for the JAX scRNAseq02 Globus
release dated 2026-05-22.

Base release:

```text
/JAX_scRNAseq02_processed/JAX-scRNAseq02-5-22-26
```

Completion overlay:

```text
/JAX_scRNAseq02_processed/JAX-scRNAseq02-5-22-26-completion-7-27-26
```

The base release contains 10 samples. This overlay contains the remaining 12
completed samples from library preparations `25E34-L4`, `25E35-L3`, and
`25E35-L4`. Together they provide all 22 expected samples.

This overlay is not standalone. Merge the 12 sample directories from the
overlay into the root of the base release. No existing relative paths are
replaced.

Canonical run provenance:

```text
runs/jax_scrnaseq02/20260727T211759Z_completion_overlay/
```

## Transfer

- Globus task: `6d5e713a-8a01-11f1-881a-02ce27bde401`
- Final status: `SUCCEEDED` at `2026-07-27T22:04:41Z`
- Synchronization: checksum
- Destination checksum verification: enabled
- Transferred files: 210
- Transferred bytes: 54,830,077,298

See `upload_manifest.tsv` for the exact uploaded paths, sizes, source paths,
checksums when available, and task status.

A recursive post-transfer listing independently confirmed 210 files,
54,830,077,298 bytes, the 12 expected top-level sample directories, and the six
packet metadata files.

## Samples

| Library preparation | Sample | Files | Bytes |
|---|---|---:|---:|
| `25E34-L4` | `EPAS1-Day-5` | 17 | 3,009,076,149 |
| `25E34-L4` | `ISL1-Day-5` | 17 | 3,312,894,350 |
| `25E34-L4` | `WT-ExM-Day-5` | 17 | 4,120,074,015 |
| `25E34-L4` | `WT-PrS-3pct-Day-5` | 17 | 3,824,529,829 |
| `25E35-L3` | `GCM1-Day-6` | 17 | 3,021,779,352 |
| `25E35-L3` | `GRHL1-Day-6` | 17 | 6,627,729,196 |
| `25E35-L3` | `OVOL1-Day-6` | 17 | 6,752,971,133 |
| `25E35-L3` | `WT-PrS-20pct-Day-6` | 17 | 2,712,138,639 |
| `25E35-L4` | `EPAS1-Day-6` | 17 | 6,283,709,520 |
| `25E35-L4` | `ISL1-Day-6` | 17 | 3,938,913,231 |
| `25E35-L4` | `WT-ExM-Day-6` | 17 | 4,831,452,235 |
| `25E35-L4` | `WT-PrS-3pct-Day-6` | 17 | 6,394,569,369 |

The Day 6 pool 5 library preparation is `25E35-L3`; `25E5-L3` is not the
corresponding production library identifier.

## Directory layout

```text
<sample>/downstream_genefull_velocyto_cellbender/
```

Each sample contains the same 17-file selection as the original packet:

- five H5AD deliverables;
- adaptive QC metadata and gene-QC plots;
- CellBender report, log, metrics, PDF, and called-barcode CSV;
- barcode filtering/doublet lists; and
- `summary.txt`.

Feature files, raw CellBender H5 payloads, checkpoints, matplotlib font caches,
FASTQs, BAMs, and raw Matrix Market matrices are excluded, matching the base
release.

## Recommended cell selection

For analysis, use `default_singlet_filtered_counts.h5ad`. Equivalently, subset
`unfiltered_counts.h5ad` or `final_counts.h5ad` where
`obs["singlet_filtered"] == True`. This mask combines the singlet call with the
adaptive gene-complexity and mitochondrial-percentage QC mask.

`filtered_counts.h5ad` contains QC-passing cells before doublet exclusion.
`counts.h5ad` is the preliminary full-barcode matrix with the STAR cell-call
and basic filter fields. `unfiltered_counts.h5ad` and `final_counts.h5ad`
retain the full barcode space and all QC annotations.

## H5AD data dictionary

### Matrices and layers

- `X`: CSR sparse `float32` STAR GeneFull counts, including exonic and intronic
  reads assigned to gene bodies.
- `layers["denoised"]`: sparse CellBender ambient-RNA-corrected counts.
- `layers["spliced"]`, `layers["unspliced"]`, and `layers["ambiguous"]`:
  present for schema compatibility but all-zero in all 60 H5AD files in this
  overlay; do not use these layers for velocity analysis.
- `obsm`, `varm`, and `obsp`: intentionally empty.

CellBender outputs are the GPU/CUDA production outputs.

### `obs`

`counts.h5ad` contains only `is_cell` and `filter`. The other four H5AD files
contain all fields below.

| Field | Type | Meaning |
|---|---|---|
| `is_cell` | bool | STAR EmptyDrops_CR cell call. |
| `filter` | bool | Passes adaptive gene-count and mitochondrial-percentage QC. |
| `non_empty` | int64 | Non-empty-barcode indicator from STAR. |
| `doublet` | int64 | scDblFinder prediction: 1 doublet, 0 singlet. |
| `doublet_scores` | float64 | scDblFinder doublet score. |
| `singlet` | bool | Cell call excluding predicted doublets. |
| `n_genes` | int64 | Number of detected genes. |
| `mt_counts` | float32 | Mitochondrial UMI count. |
| `total_counts` | float32 | Total GeneFull UMI count. |
| `mt_pct` | float32 | Mitochondrial UMI percentage. |
| `singlet_filtered` | bool | Recommended usable-cell mask: `singlet & filter`. |
| `filter_strict_mt5` | bool | Legacy strict-5% mitochondrial QC mask. |
| `singlet_filtered_strict_mt5` | bool | Legacy strict-5% singlet/QC mask. |

The observation index is the cell barcode.

### `var`

| Field | Type | Meaning |
|---|---|---|
| `gene_symbols` | category | Gene symbol. |
| `feature_types` | category | `Gene Expression`. |

The variable index is the Ensembl gene identifier.

### `uns`

- `gene_expression_feature_kind`: gene-expression feature identifier.
- `gene_expression_source`: source gene-expression matrix.
- `velocyto_source`: recorded source Velocyto matrix.
- `mt_adaptive_filter`: per-sample adaptive QC settings; absent only from the
  preliminary `counts.h5ad`.
