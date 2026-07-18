# MSK 30polyKO Revised DRACC Processed v3

Packet released: `2026-07-06`

Documentation updated: `2026-07-18`

## Release status

This README documents the nine-sample MSK 30polyKO dataset released at:

```text
MorPhiC Internal Releases/
  MorPhiC_Release_June_2026/
    MSK_30polyKO_revised_DRACC_processed_v3/
```

The June release did not include a dataset-level README. The current corrected
dataset is the June v3 base **plus** the 2026-07-06 correction overlay:

```text
Morphic Processing/
  MSK-feature-h5ad-top-feature-repair-20260706/processed/
```

Apply the overlay using the same relative paths. It replaces both feature
H5ADs for all nine samples. For `30_KO_DE_XM` it also replaces `counts.h5ad`
and the counts QC plots. The immediate DE_XM-only handoff contains the same
DE_XM replacements, but its README is a patch note rather than a complete
dataset guide.

## Sample folders

The nine folders match the nine provider groups in `/mnt/pikachu/df.meta.rds`.
The provider metadata was used for validation and RF model training but was not
copied into the released H5AD files.

| Release folder | Provider group | Stage | Chemistry and interpretation |
| --- | --- | --- | --- |
| `30_KO_ES` | `ES` | S0 | February 2018 3M chemistry. |
| `30_KO_DE` | `DE` | S1 | Separate non-GEM-X DE group retained in the nine-sample reference. |
| `30_KO_DE_XM` | `DE_GemX` | S1 | GEM-X DE data with LARRY; supersedes earlier versions of this GEM-X dataset. |
| `30_KO_PP1` | `PP1` | S3 | February 2018 3M chemistry. |
| `30_KO_PP2` | `PP2` | S4 | February 2018 3M chemistry. |
| `30_KO_S5_1` | `S5_1` | S5 | February 2018 3M chemistry. |
| `30_KO_S5_2` | `S5_2` | S5 | February 2018 3M chemistry. |
| `30_KO_S6_1` | `S6_1` | S6 | February 2018 3M chemistry. |
| `30_KO_S6_2` | `S6_2` | S6 | February 2018 3M chemistry. |

`30_KO_DE` and `30_KO_DE_XM` are both intentional members of the reference
set. The latter is the `DE_GemX` provider group; it is not a duplicate folder
for `30_KO_DE`.

## Directory layout

```text
processed/
  <sample>/
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

- `counts.h5ad` contains the raw nonzero GEX barcode universe, GeneFull counts,
  Velocyto layers, CellBender denoised counts, cell/QC masks, and integrated
  CRISPR PolyIII and LARRY feature summaries.
- `features/gene/features.h5ad` contains the 30-feature CRISPR PolyIII matrix.
- `features/larry/features.h5ad` contains the 245,979-feature LARRY matrix.
- `QC/counts/` contains the per-sample gene-count QC histogram.

FASTQs, BAMs, raw MEX directories, and CellBender's standalone output H5 are
not included in this compact release. FASTQs were retained as source inputs but
were not uploaded. Retained BAMs were archived/uploaded separately as large
files.

## Recommended cell selection

`counts.h5ad` is **not** a cell-only object. It contains approximately two
million nonzero barcodes per sample. Cell and QC status are represented by
boolean masks in `obs`.

For the default strict analysis set, use:

```python
import anndata as ad

adata = ad.read_h5ad("counts.h5ad")
cells = adata[adata.obs["singlet_filtered"].astype(bool)].copy()
```

Other useful views are:

```python
# All STAR-called cells, before doublet and downstream QC exclusion
star_cells = adata[adata.obs["is_cell"].astype(bool)].copy()

# QC-passing STAR-called cells, retaining predicted doublets
qc_cells = adata[
    adata.obs["is_cell"].astype(bool)
    & adata.obs["filter"].astype(bool)
].copy()
```

Do not use `filter == True` by itself as a cell call. `filter` records whether
a barcode passes gene/mitochondrial thresholds and is computed over the full
barcode universe. `singlet_filtered` combines the STAR call, doublet status,
and QC mask.

### Cell counts in the corrected release

| Folder | All rows | `is_cell` | `singlet_filtered` |
| --- | ---: | ---: | ---: |
| `30_KO_DE` | 2,092,397 | 33,123 | 20,220 |
| `30_KO_DE_XM` | 1,997,730 | 43,352 | 31,296 |
| `30_KO_ES` | 2,056,015 | 33,236 | 23,016 |
| `30_KO_PP1` | 2,036,796 | 13,261 | 10,107 |
| `30_KO_PP2` | 2,288,041 | 26,394 | 17,991 |
| `30_KO_S5_1` | 2,471,927 | 29,096 | 20,398 |
| `30_KO_S5_2` | 2,120,758 | 33,253 | 22,104 |
| `30_KO_S6_1` | 2,152,424 | 25,435 | 16,144 |
| `30_KO_S6_2` | 2,348,359 | 23,078 | 16,240 |

## Processing workflow

### Inputs and whitelist policy

The release was regenerated from FASTQs; historical H5AD files were not used
as analysis inputs.

| Component | Non-GEM-X samples | `30_KO_DE_XM` / `DE_GemX` |
| --- | --- | --- |
| GEX and LARRY whitelist | 3M February 2018, TRU | 3M May 2023 GEM-X, TRU |
| CRISPR PolyIII assignment | February 2018 NXT family | May 2023 GEM-X NXT-to-TRU translation |
| Released barcode namespace | TRU | TRU after NXT-to-TRU conversion |

The July DE_XM correction repaired a downstream namespace mismatch so that
GEX, CRISPR PolyIII, and LARRY annotations use the same released TRU barcode
namespace.

### STAR and feature processing

1. FASTQs were grouped by sample and library type: GEX, CRISPR PolyIII, and
   LARRY.
2. STAR-Suite ran GeneFull GEX quantification, Velocyto quantification, and
   CR-compatible multi-feature assignment with 32 threads.
3. GEX cells were called with STARsolo `EmptyDrops_CR`.
4. CRISPR PolyIII and LARRY counts were integrated by canonical 10x barcode.
5. `scDblFinder` was run on STAR-called cells to assign doublet status and
   scores.
6. Per-sample gene-count and mitochondrial QC masks were calculated.
7. CellBender 0.3.2 ran with CUDA on the remote GPU server; its output was
   added as `layers["denoised"]` without replacing the original counts.
8. Feature and counts H5ADs were packaged in the compact release layout.

Important production settings included:

```text
STAR 2.7.11b / STAR-Suite production binary
GRCh38 2024-A reference (GENCODE v44; autoindex_110_44)
--soloFeatures GeneFull Velocyto
--soloCellFilter EmptyDrops_CR
--soloCBlen 16
--soloUMIlen 12
--soloUMIdedup 1MM_CR
--soloCrGexFeature genefull
--soloCrMultimapRescue yes
--crMinUmi 2
--clipAdapterType CellRanger4
--clip3pPolyG yes
```

No Y-chromosome removal was applied to the MSK dataset.

### Downstream QC masks

The gene-count bounds were calculated per sample:

```text
minimum genes = 200
maximum genes = median(n_genes among singlets) + 3 * MAD
```

The adaptive mitochondrial threshold was:

```text
max(5%, median(mt_pct among singlets) + 3 * MAD)
```

The original strict 5% mitochondrial masks were retained in
`filter_strict_mt5` and `singlet_filtered_strict_mt5`.

## `counts.h5ad` schema

All nine corrected objects have 38,606 genes. Gene identifiers are the `var`
index; `var["gene_symbols"]` provides symbols and `var["feature_types"]`
identifies the GEX feature type.

### Matrices and layers

| Location | Meaning |
| --- | --- |
| `X` | STAR GeneFull UMI count matrix for the full nonzero barcode universe. |
| `layers["spliced"]` | Velocyto spliced UMI counts. |
| `layers["unspliced"]` | Velocyto unspliced UMI counts. |
| `layers["ambiguous"]` | Velocyto ambiguous UMI counts. |
| `layers["denoised"]` | CellBender ambient-RNA-corrected counts aligned to the same rows and genes. |

### Core `obs` columns

| Column | Type | Meaning |
| --- | --- | --- |
| `is_cell` | boolean | Initial STARsolo `EmptyDrops_CR` cell call. |
| `non_empty` | integer 0/1 | STAR-called/non-empty barcode flag; equivalent to `is_cell` in these files. |
| `filter` | boolean | Passes adaptive gene-count and mitochondrial QC. This does not by itself imply `is_cell`. |
| `doublet` | integer 0/1 | `scDblFinder` predicted-doublet flag among called cells. |
| `doublet_scores` | float | `scDblFinder` doublet score; missing outside the scored called-cell set. |
| `singlet` | boolean | `is_cell` and not `doublet`. |
| `singlet_filtered` | boolean | `singlet` and `filter`; recommended default strict analysis mask. |
| `filter_strict_mt5` | boolean | QC mask using the historical fixed 5% mitochondrial cutoff. |
| `singlet_filtered_strict_mt5` | boolean | `singlet` combined with the historical strict-5% QC mask. |
| `n_genes` | integer | Number of genes with nonzero GeneFull UMI counts for the barcode. |
| `total_counts` | float | Total GeneFull UMI counts for the barcode. |
| `mt_counts` | float | UMI counts assigned to mitochondrial genes. |
| `mt_pct` | float | `100 * mt_counts / total_counts`. |

### Feature-call `obs` columns

Each file contains seven columns for the CRISPR PolyIII library and seven for
the LARRY library. The sample-specific prefixes are:

```text
CRISPR_Guide_Capture_grna_<sample>
Custom_larry_<sample>
```

For example, ES uses `CRISPR_Guide_Capture_grna_es__feature_call` and
`Custom_larry_es__feature_call`. For either prefix `P`, the columns are:

| Column pattern | Type | Meaning |
| --- | --- | --- |
| `P__num_features` | integer | Number of feature identities detected for the barcode by the feature-assignment output. |
| `P__num_umis` | integer | Total deduplicated feature UMIs for the barcode. |
| `P__feature_call` | categorical | Unambiguous dominant feature by UMI count; blank when none or tied. |
| `P__is_featured` | boolean | At least one feature was detected (`num_features > 0`). |
| `P__feature1_count` | integer | UMI count for the most abundant feature. |
| `P__feature2_count` | integer | UMI count for the second-most abundant feature. |
| `P__feature_call_category` | categorical | `none`, `ambiguous`, `single`, or `multi`. |

Category definitions are:

- `none`: no detected feature.
- `ambiguous`: one or more features detected but no unique top feature.
- `single`: exactly one detected feature with a unique top feature.
- `multi`: multiple detected features with a unique dominant feature.

These are DRACC-derived feature summaries. They are not columns copied from the
provider's `.rds` file.

### `uns` metadata

| Key | Meaning |
| --- | --- |
| `feature_libraries` | Library names, feature types, barcode transform, call source, and integrated column names. |
| `gene_expression_feature_kind` | GEX matrix selected for integration (`GeneFull`). |
| `gene_expression_source` | Original STAR raw GEX matrix path. |
| `velocyto_source` | Original STAR Velocyto matrix path. |
| `mt_adaptive_filter` | Per-sample gene and mitochondrial thresholds and cell counts. |

The compact v3 `counts.h5ad` files have no `obsm` entries. In particular,
they do not contain `X_scimilarity`, provider metadata, or RF cell-type labels.

## Cell typing and provider metadata

Cell typing was developed and validated separately using all nine samples:

1. Scimilarity model v1.1 was used to embed filtered expression profiles.
2. Provider `celltype_20250623` and `subcelltype` labels from
   `/mnt/pikachu/df.meta.rds` were joined transiently for model training.
3. One Random Forest model set was trained across the full nine-sample MSK
   dataset and saved for reuse.
4. The saved model was applied to the sample-wise filtered H5AD objects.

Scimilarity supplied the embedding, not the final label names. The RF label
names were seeded from the provider data. Provider metadata was intentionally
kept out of the compact release to avoid mixing provider annotations with
DRACC-derived fields.

The compact June v3 `counts.h5ad` objects documented here do **not** include
the RF columns. If cell-type labels are required, use a separately released RF
annotation sidecar or the sample-wise filtered H5AD products rather than
assuming a cell-type column exists in these compact files.

## Feature-library H5AD schema

The corrected feature H5ADs contain the nonzero feature-library barcode
universe, which is broader than the final GEX cell set. A feature H5AD may
therefore have more rows than the number of feature assignments present after
joining to `counts.h5ad` and applying a cell mask. This is expected.

| Location | Meaning |
| --- | --- |
| `X` | Barcode-by-feature deduplicated UMI matrix. |
| `obs["barcode_feature_namespace"]` | Barcode namespace/mapping selected during integration. |
| `obs["num_features"]` | Number of detected feature identities. |
| `obs["total_deduped_umi"]` | Total deduplicated feature UMIs. |
| `obs["is_featured"]` | At least one feature detected; true for rows retained in these feature objects. |
| `obs["top_feature_index"]` | One-based feature-row index; zero means no unambiguous top feature. |
| `obs["top_feature_name"]` | Feature name corresponding to `top_feature_index`; blank when the index is zero. |
| `var` index / `var["feature_name"]` | Feature identifier/name. |

The gene feature H5ADs have 30 variables. The LARRY H5ADs have 245,979
variables. They contain no Velocyto or CellBender layers.

## July 2026 corrections

### DE_XM namespace correction

The June v3 `30_KO_DE_XM/counts.h5ad` had empty/inconsistent CRISPR PolyIII
assignments because the feature metadata and GEX barcodes were joined across
the wrong NXT/TRU namespace. The 2026-07-06 replacement:

- rewrote the GEM-X CRISPR feature surface into the released TRU namespace;
- rebuilt the integrated CRISPR columns in `counts.h5ad`;
- regenerated counts-derived QC plots; and
- retained the existing GEX matrix, Velocyto layers, CellBender layer, cell
  calls, and QC masks.

### Feature `top_feature_name` correction

All 18 feature H5ADs (gene and LARRY for nine samples) were corrected so that:

```text
top_feature_index == 0  -> top_feature_name == ""
top_feature_index >= 1  -> top_feature_name == var_names[top_feature_index - 1]
```

This was a feature-H5AD metadata-only repair. It did not change feature count
matrices or the eight non-DE_XM counts H5ADs.

## Provenance references

Tracked base-production provenance and this release record:

```text
morphic-provenance/
  runs/msk_30ko_revised/20260519T000000Z_revised_delivery/
  dataset_releases/msk_30ko_revised/2026-07-06/
```

The correction overlay's project-scoped file checksums, destinations, and
source paths are recorded in this release directory's `upload_manifest.tsv`.
Its Globus feature-repair transfer was task
`6cf6db59-7951-11f1-9530-0e9f7c26f401` (`SUCCEEDED`). The subsequent DE_XM
counts/QC consolidation used task
`ab3ea3fe-7956-11f1-a5c1-02f0d340f1a1` (`SUCCEEDED`).

The production STAR logs recorded STAR 2.7.11b and STAR-Suite commit
`c082c6582cca229032c7bb34a157e97511561da8`, with a dirty working tree at
compile/run time. CellBender used `biodepot/cellbender:0.3.2` with CUDA.
