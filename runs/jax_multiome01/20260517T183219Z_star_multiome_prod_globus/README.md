# JAX Multiome01 STAR/Chromap Production Run

Project: `jax_multiome01`

Run ID: `20260517T183219Z_star_multiome_prod_globus`

Status: complete

Created UTC: 2026-05-17T18:32:19Z

## Purpose

Canonical provenance record for the nine-sample JAX Multiome01 STAR-suite RNA
plus Chromap ATAC production run and revised h5mu delivery.

This repository entry is the source of truth for provenance. The provenance
file included in the Globus packet was a temporary handoff file and is
superseded by this run record.

## Code

- STAR-suite repo: `git@github.com:morphic-bio/STAR-suite.git`
- STAR-suite run commit recorded in STAR logs: `a29406301d681af39373aa280ef9f110ead80294`
- STAR-suite runtime branch: `feature/native-multiome-atac-barcode`
- STAR-suite working tree: dirty at build/run time; dirty file lists are in
  per-sample `star_sample/run/Log.out`
- Canonical recipes repo: `git@github.com:morphic-bio/morphic-recipes.git`
- Recipe commit containing the executed production scripts:
  `682f55493e9342aaed425dd89fb87b0148e8c258`
- Current canonical recipes HEAD when this record was created:
  `2552631cc822697cca69134952ca8d58f8cbd5c4`

## Inputs

See `inputs/manifest.tsv`, `inputs/checksums.tsv`, and
`inputs/sample_manifest.tsv`.

The run used `/mnt/pikachu/JAX_Multiome01/raw` plus the metadata workbook
`/mnt/pikachu/DPC_metadata_template_Multiome1-complete.xlsx`. The generated
sample manifest contains nine ATAC/GEX library pairs.

## Commands

The top-level production launch shape is recorded in
`commands/production_launch.argv.json`.

Exact rendered per-sample STAR workflow scripts are preserved under
`commands/samples/`.

Script provenance and SHA256 hashes are in `commands/script_hashes.tsv`.

## Outputs

See `outputs/manifest.tsv` and `outputs/checksums.tsv`.

The local production root is:

`/mnt/pikachu/JAX_Multiome01_processed/star_multiome_prod_globus_20260517T183219Z`

The compact h5mu Globus handoff was:

`/JAX_Multiome01_processed/JAX-Multiome01-5-18-26-revised/h5mu`

The large-file Globus handoff was:

`/JAX_Multiome01_processed/large_files/star_multiome_prod_globus_20260517T183219Z`

## Environment

Container image provenance is in `environment/container_images.tsv`.

The local runner built STAR with Chromap support once before processing:

```bash
make -C /mnt/pikachu/STAR-suite/core/legacy/source clean
make -C /mnt/pikachu/STAR-suite/core/legacy/source -j8 STAR WITH_CHROMAP=1
make -C /mnt/pikachu/STAR-suite/core/features/libchromap_contract star_multiome_atac_peak_mex
```

## Handoff

Globus transfer state is preserved in
`handoff/globus_large_files_upload_state.tsv`.

Handoff notes, task ids, and the temporary packet provenance status are in
`handoff/README.md` and `handoff/transfer-status.json`.

## Dataset Release Notes

The collaborator-facing Globus release notes keyed by analysis push date are:

```text
dataset_releases/jax_multiome01/2026-05-18/
```

Those notes track what was uploaded, release-specific updates, and the status
of the temporary packet provenance file.
