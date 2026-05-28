# MSK 30KO Revised Delivery Provenance

Generated: 2026-05-19

This file records run parameters, source archive locations, script content
hashes, Git provenance, and Docker image provenance for the MSK 30KO revised
delivery. The compact file layout and h5ad schema are documented in
`README.md`.

## Source Archives

The compact files in `MSK_30_KO_revised` are historical-style outputs. The May
2026 sample-wise production provenance for the revision is captured in:

```text
/mnt/pikachu/msk30ko-production-sample-archive/MSK-05-13-26-large-files
/mnt/pikachu/msk30ko-h5ad-qc-delivery/MSK-05-13-26-large-files
/storage/MSK-perturb-comparison/msk30ko_DE_GemX_velocyto_downstream_trial_20260513_190549
```

The staged sample-wise delivery manifest is:

```text
/mnt/pikachu/msk30ko-h5ad-qc-delivery/MSK-05-13-26-large-files/STAGED_MANIFEST.tsv
```

It contains 604 rows covering sample QC, STAR logs, Solo QC, feature assignment
QC, CellBender QC, feature h5ads, 18 primary h5ads
(`filtered_counts.h5ad` and `default_singlet_filtered_counts.h5ad` for each of
the nine provider groups), RF cell-typing model artifacts, and provider
comparison tables.

Detailed production documentation and comparison results are in:

```text
/mnt/pikachu/msk30ko-h5ad-qc-delivery/MSK-05-13-26-large-files/documentation/README.md
/mnt/pikachu/msk30ko-h5ad-qc-delivery/MSK-05-13-26-large-files/documentation/docs/RUNBOOK_MSK_30KO_PRODUCTION_AND_CELL_TYPING.md
/mnt/pikachu/STAR-suite/docs/RUNBOOK_MSK_30KO_GEMX_PRODUCTION_DRAFT.md
```

## STAR-Suite Binary

Production STAR logs report:

- Binary path: `/mnt/pikachu/STAR-suite/core/legacy/source/STAR`
- STAR version: `2.7.11b`
- Compile time: `2026-05-13T17:47:16+00:00`
- Git commit recorded by STAR logs:
  `c082c6582cca229032c7bb34a157e97511561da8`
- GitHub tree:
  `https://github.com/morphic-bio/STAR-suite/tree/c082c6582cca229032c7bb34a157e97511561da8`
- STAR logs also recorded a dirty working tree at compile/run time; therefore
  the binary is best treated as commit `c082c658...` plus local modifications
  listed in each sample `run/Log.out`.

Current local STAR-suite checkout at provenance generation time:

- Path: `/mnt/pikachu/STAR-suite`
- Remote: `git@github.com:morphic-bio/STAR-suite.git`
- HEAD: `c535e327f626a61a601b5472b1589511ad6a8d9e`
- GitHub tree:
  `https://github.com/morphic-bio/STAR-suite/tree/c535e327f626a61a601b5472b1589511ad6a8d9e`

## STAR Parameters

The production launcher for the eight non-GEM-X samples was:

```bash
python3 scripts/run_msk30ko_pipeline_from_manifest.py \
  --out-root /storage/MSK-perturb-comparison/msk30ko_8sample_prod_20260513_231007 \
  --exclude-samples DE_GemX \
  --threads 32 \
  --star-bin /mnt/pikachu/STAR-suite/core/legacy/source/STAR \
  --genome-dir /storage/autoindex_110_44/bulk_index \
  --out-samtype BAM\ Unsorted \
  --remote-host 10.159.4.53 \
  --remote-root /tmp/msk30ko_cellbender \
  --gpu-slots 0,1 \
  --cellbender-cpu-cores 8 \
  --cellbender-layer denoised \
  --scimilarity-model-path /home/lhhung/model_v1.1 \
  --globus-dst-root /MSK-05-13-26-large-files \
  --bam-archive-root /mnt/pikachu/msk30ko-bam-archive/MSK-05-13-26-large-files \
  --completed-sample-archive-root /mnt/pikachu/msk30ko-production-sample-archive/MSK-05-13-26-large-files \
  --skip-existing
```

The `DE_GemX` sample was processed first as a separate trial and then retained
as the production `DE_GemX` output:

```text
/storage/MSK-perturb-comparison/msk30ko_DE_GemX_velocyto_downstream_trial_20260513_190549/samples/DE_GemX
```

Common STAR options used in the production commands:

```text
--runThreadN 32
--genomeDir /storage/autoindex_110_44/bulk_index
--readFilesCommand zcat
--clipAdapterType CellRanger4
--clip3pPolyG yes
--alignEndsType Local
--chimSegmentMin 1000000
--soloType CB_UMI_Simple
--soloCBstart 1
--soloCBlen 16
--soloUMIstart 17
--soloUMIlen 12
--soloBarcodeReadLength 0
--soloInlineHashMode no
--soloStrand Forward
--soloFeatures GeneFull Velocyto
--soloUMIdedup 1MM_CR
--soloCBmatchWLtype 1MM_multi_Nbase_pseudocounts
--soloCellFilter EmptyDrops_CR
--soloUMIfiltering MultiGeneUMI_CR
--soloMultiMappers Unique
--soloCbUbRequireTogether no
--soloCrGexFeature genefull
--soloCrMultimapRescue yes
--crChemistry auto
--crMinUmi 2
--crAssignMaxHamming 1
--crAssignFeatureOffset 0
--crAssignLimitSearch -1
--crAssignMinCounts 0
--crAssignMaxBarcodeMismatches 5
--crAssignFeatureN 0
--crAssignBarcodeN 1
--crAssignConsumerThreads -1
--crAssignSearchThreads 1
--crAssignSkipQcOutputs 1
--defaultCrCompat yes
--dynamicThreadInterface 1
--dynamicThreadConstMapPermits 32
--dynamicThreadTelemetry 1
```

Output BAM policy:

- Non-GEM-X production samples used `--outSAMtype BAM Unsorted`.
- `DE_GemX` retained trial used `--outSAMtype None`.
- No Y-chromosome removal was applied for MSK.

Whitelist policy:

- Non-GEM-X samples used
  `/storage/scRNAseq_output/whitelists/3M-february-2018_TRU.txt`.
- `DE_GemX` used
  `/storage/scRNAseq_output/whitelists/3M-3pgex-may-2023_TRU.txt`.
- Per-sample `pf_multi_config.csv` files record the GEX, CRISPR PolyIII, and
  LARRY feature libraries and their feature references.

Reference:

- Genome/index: `/storage/autoindex_110_44/bulk_index`
- Index generation command in STAR logs references Cell Ranger-style GRCh38
  `2024-A` resources and `gencode.v44.primary_assembly.annotation.gtf`.

## Downstream, Adaptive MT, And CellBender Parameters

Downstream h5ad generation command pattern:

```bash
/mnt/pikachu/STAR-suite/scripts/run_scrna_downstream_gene_full_velocyto.sh \
  --run-dir <sample>/run \
  --output-dir <sample>/downstream_genefull_velocyto_cellbender \
  --adaptive-filter
```

Adaptive mitochondrial conversion was applied once to the sample-wise production
h5ads before staging the revised h5ad/QC delivery. The conversion uses:

```bash
/mnt/pikachu/STAR-suite/scripts/convert_h5ad_mt_adaptive.py \
  --sample-dir <sample>/downstream_genefull_velocyto_cellbender
```

Default adaptive MT policy:

- `--n-mad 3`
- `--mt-floor 5.0`
- Effective threshold is `max(5%, median(mt_pct over singlets) + 3*MAD)`.
- The strict 5% fields are preserved as `*_strict_mt5` before rewriting
  `filter` and `singlet_filtered`.

CellBender command pattern:

```bash
/mnt/pikachu/STAR-suite/scripts/run_remote_cellbender_rsync.sh \
  --downstream-dir <sample>/downstream_genefull_velocyto_cellbender \
  --remote-host 10.159.4.53 \
  --remote-root /tmp/msk30ko_cellbender \
  --cellbender-image biodepot/cellbender:0.3.2 \
  --cellbender-gpu-device <0-or-1> \
  --cellbender-cpu-cores 8 \
  --cellbender-layer denoised \
  --no-sync-image
```

CellBender itself ran:

```bash
cellbender remove-background \
  --input <remote>/work/unfiltered_counts.h5ad \
  --output <remote>/work/cellbender/cellbender_counts.h5 \
  --cpu-threads 8 \
  --cuda
```

## Container Provenance

| Purpose | Image | Digest / image ID |
| --- | --- | --- |
| CellBender remote GPU | `biodepot/cellbender:0.3.2` | Repo digest `sha256:4e6e41ed6366d9d6a3e10435851d8c2acbd0083f456630fb87e6029a23f379a5`; image ID `sha256:f31f1e993f3d87659c3dd541a22f505fec7ee4366f6d5da1324061c2c09dcb2a` |
| Downstream matrix builder | `biodepot/scrna-matrices:latest` | Repo digest `sha256:913e58708fad05d58cf557b60972a27d248d4252aecb07f4688ccffe61cc9ac1`; local tag also `biodepot/scrna-matrices:20260330-ce24c46cbaf9`; image ID `sha256:c052c1568727f24a6e2c8ec793357ccfdf1ffdf5622542a7b2da40d8df47825b` |
| Feature gather helper | `biodepot/gather_features:latest` | No repo digest recorded locally; image ID `sha256:973d04f6442765e745e7d5d5c41183bf4e2ef4c00c37c13a27802955ccce4d6e` |

## Script Locations And Content Hashes

The MSK-specific production planning checkout was:

```text
/mnt/pikachu/msk-30ko-production-planning
```

Its local HEAD at provenance generation time:

```text
a7587d1b4fc7a27bd9d563d34744c1ff386cd462
```

The planning checkout had local uncommitted changes and untracked helper
scripts. For reproducibility, use the script content hashes below in addition
to Git commit hashes.

| Script | Location | SHA256 |
| --- | --- | --- |
| Production launcher | `/mnt/pikachu/msk-30ko-production-planning/scripts/run_msk30ko_pipeline_from_manifest.py` | `106081ec90dabb2b5aed45a945da58fb528b23d3a3cad50fd29b43d31413f7a8` |
| Delivery staging | `/mnt/pikachu/msk-30ko-production-planning/scripts/stage_msk30ko_h5ad_qc_delivery.py` | `5a2151d797a5f8f225745c3e9ebdd447a931e4522f642229317d599a7064c751` |
| Provider RF cell typing | `/mnt/pikachu/msk-30ko-production-planning/scripts/annotate_provider_rf_celltypes_h5ad.py` | `39acf75b765dfb7fbde47a910b730920d6b31904c2b92e9f434ba34e32e19ebd` |
| Provider comparison | `/mnt/pikachu/msk-30ko-production-planning/scripts/compare_msk30ko_outputs_to_provider_rds.py` | `a307af7d3811388b0fd37dee739a6f95fd70a60edf0c0e1351a8b910aee0de19` |
| Downstream h5ad builder | `/mnt/pikachu/STAR-suite/scripts/run_scrna_downstream_gene_full_velocyto.sh` | `a2cd44735ac95c537df59f4d6868f2bbdecb1e02667675dd1243201c9e476299` |
| Remote CellBender runner | `/mnt/pikachu/STAR-suite/scripts/run_remote_cellbender_rsync.sh` | `b3b817da126ef05656f85db649314dea91826ffa8226efbf87a370406ea009d9` |
| Adaptive MT converter | `/mnt/pikachu/STAR-suite/scripts/convert_h5ad_mt_adaptive.py` | `a7f565da324e3c9c3a7775e7d0a096a0973cfa9eeb53bc709cbdcb1e89aaeb3d` |
| Adaptive QC plotter | `/mnt/pikachu/STAR-suite/scripts/generate_qc_histogram_mt_adaptive.py` | `79672f99e5faaecf7cddd6e05f29b6a19130d542e4828de8867658990d1c8960` |
| Adaptive filter helper | `/mnt/pikachu/STAR-suite/scripts/apply_adaptive_mt_filter.py` | `91e88eb2eb8e50fb473dd34ea000965181c3eb9936fbacdc175b3d2080aa613a` |
| Adaptive MT library | `/mnt/pikachu/STAR-suite/scripts/scrna_mt_adaptive.py` | `603235d8a0e5e0c9b6d5ae2dd4b009a9bef2837ca20f610b101b527ce6bd8c74` |
