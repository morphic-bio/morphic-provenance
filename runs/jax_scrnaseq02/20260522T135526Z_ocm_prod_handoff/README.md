# JAX scRNAseq02 OCM Production Handoff

Project: `jax_scrnaseq02`

Run ID: `20260522T135526Z_ocm_prod_handoff`

Status: complete

Created UTC: 2026-05-22T13:55:26Z

## Purpose

Canonical provenance record for the JAX scRNAseq02 completed h5ad/QC handoff
packet built from:

```text
/mnt/pikachu/JAX_scRNAseq02_processed/ocm_prod_batch_flex_native_yremove_trace_20260521T034223Z
```

The packet `PROVENANCE.md` is preserved under `handoff/` as temporary handoff
context and is superseded by this record.

## Code

- STAR-suite commit recorded in the packet: `d55a1a7d27c85df0f780a0e50039392e83a31260`
- Production launcher: `scripts/run_jax_scrnaseq02_ocm_production_batch.sh`
- Recipe/runbook material currently mirrored in `morphic-recipes`, including
  `docs/RUNBOOK_JAX_SCRNASEQ02_OCM_20260518.md`.

## Inputs And Commands

Rendered launch, per-library STAR command scripts, OCM configs, and downsample
manifests are preserved under `commands/` and `inputs/`.

## Outputs

The h5ad/QC packet contains 170 payload files totaling 41,251,425,950 bytes.
It includes 10 completed samples; feature files were excluded by design. See
`outputs/MANIFEST.tsv`, `outputs/PROVENANCE.tsv`, and `outputs/sample_summary.tsv`.

## Handoff

See `handoff/README.md` and `handoff/globus_task.json`.

## Dataset Release Notes

```text
dataset_releases/jax_scrnaseq02/2026-05-22/
```

## Reproduction Entrypoint

No single `run_all.sh` reproduction wrapper has been mirrored for this delivery
yet. Start from `commands/LAUNCH_COMMAND.sh`, the per-library `RUN_STAR.sh`
scripts, and the JAX scRNAseq02 runbook mirrored in `morphic-recipes`.
