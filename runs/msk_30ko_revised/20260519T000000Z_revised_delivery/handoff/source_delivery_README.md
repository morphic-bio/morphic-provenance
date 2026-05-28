# MSK 30KO Revised Delivery

Generated: 2026-05-19

This directory contains the revised compact MSK 30KO delivery arranged in the
same layout as the earlier `MSK_30_KO/30_KO_ES` tree. It is a compact
legacy-style AnnData delivery, not the full sample-wise STAR production archive.
Processing parameters, script versions, Git hashes, and container provenance
are documented separately in `provenance.md`.

## Directory Structure

```text
MSK_30_KO_revised/
  README.md
  provenance.md
  30_KO_ES/
    counts.h5ad
    features/
      gene/
        features.h5ad
      larry/
        features.h5ad
    QC/
      counts/
        gene_quantile_histogram.html
        gene_quantile_histogram.png
```

## File Manifest

| Relative path | Size | Contents |
| --- | ---: | --- |
| `30_KO_ES/counts.h5ad` | 6,493,766,536 bytes (6.0 GiB) | Main barcode-by-gene AnnData object. Includes gene expression, Velocyto layers, CellBender `denoised`, QC obs fields, gene barcode calls, LARRY barcode calls, and predicted cell type. |
| `30_KO_ES/features/gene/features.h5ad` | 39,718,280 bytes (37.9 MiB) | Feature-call matrix for the 30 gene perturbation features. |
| `30_KO_ES/features/larry/features.h5ad` | 89,018,595 bytes (84.9 MiB) | Feature-call matrix for LARRY barcodes. |
| `30_KO_ES/QC/counts/gene_quantile_histogram.html` | 3,837,993 bytes (3.7 MiB) | Interactive QC histogram for gene-count filtering. |
| `30_KO_ES/QC/counts/gene_quantile_histogram.png` | 186,446 bytes (182.1 KiB) | PNG copy of the gene-count QC histogram. |
| `README.md` | generated in place | Directory, manifest, sample context, and h5ad schema. |
| `provenance.md` | generated in place | Run parameters, Git/script hashes, container digests, and source archive pointers. |

No FASTQs, BAMs, raw MEX directories, CellBender raw `.h5` files, or provider
`.rds` metadata are included in this compact delivery.

## Samples And Biological Context

The compact directory name is `30_KO_ES`. The `counts.h5ad` itself does not
store a per-cell `sample`, `orig.ident`, or `stage` column, so downstream users
should treat the compact object as the `30_KO_ES` delivery surface unless they
join external metadata.

The May 2026 sample-wise MSK production set used for provenance contains these
provider groups:

| Provider group | Stage | Notes |
| --- | --- | --- |
| `ES` | `S0` | February 2018 chemistry. |
| `DE` | `S1` | Older DE/XM surface retained as a separate provider group. |
| `DE_GemX` | `S1` | Corrected GEM-X DE source with LARRY barcodes; this supersedes older GEM-X material when there is a conflict. |
| `PP1` | `S3` | February 2018 chemistry. |
| `PP2` | `S4` | February 2018 chemistry. |
| `S5_1` | `S5` | February 2018 chemistry. |
| `S5_2` | `S5` | February 2018 chemistry. |
| `S6_1` | `S6` | February 2018 chemistry. |
| `S6_2` | `S6` | February 2018 chemistry. |

The provider metadata source for production comparisons was
`/mnt/pikachu/df.meta.rds`. Provider metadata was not copied into the compact
delivery h5ad.

## AnnData Structure

### `30_KO_ES/counts.h5ad`

Shape: `6,794,880 obs x 38,592 vars`

Stored matrix:

- `X`: CSR sparse matrix, `float32`
- Layers:
  - `spliced`
  - `unspliced`
  - `ambiguous`
  - `denoised`

Observation columns:

| Column | Type | Meaning |
| --- | --- | --- |
| `filter` | `bool` | QC filter flag in this compact object. |
| `non_empty` | `int64` | Non-empty barcode flag. |
| `doublet` | `int64` | Doublet flag. |
| `doublet_scores` | `float64` | Doublet score for non-empty/called barcodes. |
| `singlet` | `bool` | Singlet flag. |
| `n_genes` | `int64` | Number of detected genes per barcode. |
| `mt_counts` | `float32` | Mitochondrial counts per barcode. |
| `total_counts` | `float32` | Total counts per barcode. |
| `mt_pct` | `float32` | Mitochondrial percent per barcode. |
| `singlet_filtered` | `bool` | Combined singlet and QC-filtered flag. |
| `is_denoised` | `bool` | Indicates denoised layer is present for the object. |
| `gene_barcode` | `category` | Called gene perturbation barcode/status. |
| `larry_barcode` | `category` | Called LARRY barcode/status. |
| `predicted_cell_type` | `category` | Predicted cell type in the compact object. |

Selected obs counts:

| Field | Counts |
| --- | --- |
| `non_empty` | `32,599` true, `6,762,281` false |
| `filter` | `16,635` true, `6,778,245` false |
| `singlet` | `27,607` true, `6,767,273` false |
| `singlet_filtered` | `11,868` true, `6,783,012` false |
| `doublet` | `4,992` true, `6,789,888` false |

Selected categorical summaries:

- `gene_barcode`: 34 categories. Most rows are `filtered`; observed calls include
  perturbation labels such as `INSM1`, `PAX6`, `PDX1`, `NKX6-1`, `HNF4A`,
  `ISL1`, `HNF1A`, and others, plus status values such as `ambiguous` and
  `doublets`.
- `larry_barcode`: 245,983 categories. Most rows are missing/filtered; called
  examples include `BC40319`, `BC201125`, `BC174848`, `BC3288`, and others.
- `predicted_cell_type`: 13 categories. Counts include `ESC` 26,462, `DE`
  4,568, `ESC_DE` 1,120, `Ductal` 179, `PP` 112, plus smaller categories.
  Most rows are `Not_Predicted`, matching the large raw barcode universe.

`var` has Ensembl-style gene identifiers as the index and no stored `var`
columns in this compact object. `obsm`, `varm`, `obsp`, `varp`, and `uns` are
empty in this compact object.

### `30_KO_ES/features/gene/features.h5ad`

Shape: `286,491 obs x 30 vars`

- `X`: CSC sparse matrix, `float64`
- `var` columns: `gene_ids`, `feature_types`, `gene_symbols`
- `feature_types`: all 30 variables are stored as `Gene Expression`
- Example variables: `EOMES`, `PAX6`, `MEIS1`, `SIX3`, `HES1`, `HNF1A`,
  `NEUROG3`, `ONECUT1`, `INSM1`, `MAFB`
- No layers, `obsm`, `varm`, `obsp`, `varp`, or `uns`

### `30_KO_ES/features/larry/features.h5ad`

Shape: `290,723 obs x 245,979 vars`

- `X`: CSC sparse matrix, `float64`
- `var` columns: `gene_ids`, `feature_types`, `gene_symbols`
- `feature_types`: all 245,979 variables are stored as `Gene Expression`
- Example variables: `BC1`, `BC2`, `BC3`, `BC4`, `BC5`, `BC6`, `BC7`, `BC8`,
  `BC9`, `BC10`
- No layers, `obsm`, `varm`, `obsp`, `varp`, or `uns`

## Provenance

Processing parameters, source archive locations, STAR-suite Git hashes, script
content hashes, and Docker image digests are in `provenance.md`.

The sample-wise h5ads in the May 2026 archive include UCSF-style downstream
layers and RF cell-typing fields. The compact `30_KO_ES/counts.h5ad` documented
above does not include `X_scimilarity`, `rf_celltype`, `rf_subcelltype`, or the
provider RF provenance stored in the newer sample-wise h5ads.
