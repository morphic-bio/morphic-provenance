# MSK 40KO STAR-suite Production Run

Project: `msk_40ko`

Run ID: `20260521T232456Z_star_suite_production`

Status: complete

Created UTC: 2026-05-21T23:24:56Z

## Purpose

Canonical provenance record for the MSK 40KO STAR-suite two-sample production
run and the 2026-05-22 Globus large-BAM upload.

No standalone packet `provenance.md` was found for this upload, so this
repository entry is the source of truth.

## Code

- STAR binary run commit from `Log.out`: `87a45d34e7c9ea08a34507adbde4cfcb360a6c11`
- STAR runtime branch from `Log.out`: `master`
- STAR diff files from `Log.out`: empty
- STAR version: `2.7.11b`
- STAR compile time: `2026-05-21T03:39:11+00:00`
- First committed STAR-suite 40KO launcher copy: `d55a1a7d27c85df0f780a0e50039392e83a31260`
- Initial morphic-recipes mirror with matching launcher content: `682f55493e9342aaed425dd89fb87b0148e8c258`
- Current morphic-recipes head when this record was created: `c41c2fd11f9bedd0f8b2b6e81a726a9da12b5d0f`

The launcher was not present at STAR-suite commit `87a45d3`; it was committed
shortly after this run. The exact launch commands, preserved run manifests, and
first committed launcher source are kept under `commands/`.

## Inputs

See `inputs/manifest.tsv`, `inputs/checksums.tsv`, and
`inputs/MSK_40KO_FASTQ_MANIFEST.tsv`. The run used:

- FASTQ root: `/mnt/pikachu/scRNAseq_40KO`
- Genome index: `/storage/autoindex_110_44/bulk_index`
- STAR-suite manifest: `/mnt/pikachu/STAR-suite/docs/MSK_40KO_FASTQ_MANIFEST.tsv`

## Commands

The initial ES/DE serial launch is in `commands/LAUNCH_COMMAND.txt`. The DE
async resume launch is in `commands/LAUNCH_COMMAND_20260522T024507Z.txt`.
Rendered argv JSON files and per-sample `RUN_COMMAND.sh`/`RUN_MANIFEST.txt`
files are also preserved under `commands/`.

The observed event stream is `commands/RUNS.tsv`; process-control notes are
`commands/PROCESS_CONTROL.tsv`.

## Outputs

The local production root is:

```text
/mnt/pikachu/MSK_40KO_processed/msk40ko_prod_20260521T232456Z_setsid
```

The run record inventories 526 files totaling 359,406,952,337 bytes. The two
sample trees are summarized in `outputs/summary.tsv`, and h5ad/QC/BAM outputs
are listed in `outputs/manifest.tsv`.

Provider RF cell typing provenance and label counts are preserved under
`analysis/`.

## Handoff

The Globus large-BAM destination was:

```text
/MSK-40KO-large-files
```

Both sample BAM transfers succeeded on 2026-05-22. See
`handoff/bam_upload_manifest.tsv` and `handoff/samples/`.

## Dataset Release Notes

The collaborator-facing Globus release notes keyed by push date are:

```text
dataset_releases/msk_40ko/2026-05-22/
```

## Reproduction Entrypoint

No single `run_all.sh` wrapper has been mirrored for MSK 40KO yet. Reproduction
should start from the preserved runbook and launcher:

```text
inputs/RUNBOOK_MSK_40KO_PRODUCTION.md
commands/run_msk_40ko_pipeline_from_manifest.initial_morphic_recipes.py
```

The current maintained recipe script lives in `morphic-recipes` at:

```text
scripts/run_msk_40ko_pipeline_from_manifest.py
```
