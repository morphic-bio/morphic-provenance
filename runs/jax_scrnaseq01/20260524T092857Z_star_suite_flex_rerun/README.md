# JAX scRNAseq01 STAR-suite Flex Rerun

Project: `jax_scrnaseq01`

Run ID: `20260524T092857Z_star_suite_flex_rerun`

Status: complete

Created UTC: 2026-05-24T09:28:57Z

## Purpose

Canonical provenance record for the JAX scRNAseq01 GRCh38-2024-A Flex rerun
and Globus handoff produced from
`/mnt/pikachu/JAX_scRNAseq01_2024_star_suite_20260524_080700`.

The `Provenance.md` included in the Globus packet is preserved under
`handoff/temporary_packet_provenance.md` and is superseded by this repo record.

## Code

- STAR-suite runtime checkout: `/mnt/pikachu/STAR-suite`
- STAR-suite commit: `d70a03e407f45b743efa60c7d032d6d2e1a80123`
- STAR version: `1.0.0`
- Binary: `/mnt/pikachu/STAR-suite/core/legacy/source/STAR`
- Build commands: `make -C core/legacy/source clean` and
  `make -C core/legacy/source -j8 STAR`

## Inputs

See `inputs/fastq_manifest.txt` and `inputs/tag_to_sample.tsv`.

Primary source inputs were `/mnt/pikachu/JAX_sequences/JAX_scRNAseq01`, the
completed metadata workbook, the 2024-A Flex probe list, the fixed RNA sample
probe barcode catalog, and the full 16-tag whitelist.

## Commands

Exact rendered STAR commands for both count libraries are preserved in
`commands/SC2300771_hash_noalign.RUN_COMMAND.sh` and
`commands/SC2300772_hash_noalign.RUN_COMMAND.sh`.

Both count stages used Flex hash/no-align mode with `--flexNoAlign 1` and no
Y-removal.

## Outputs

The release payload contains 137 checksum entries totaling 2,207,614,024 bytes,
including 6 h5ad files totaling 1,679,125,108 bytes. See
`outputs/manifest.tsv`, `outputs/CHECKSUMS.sha256`, and the QC comparison files.

## Handoff

See `handoff/README.md` and the copied Globus task JSON files.

## Dataset Release Notes

```text
dataset_releases/jax_scrnaseq01/2026-05-24/
```

## Reproduction Entrypoint

No single `run_all.sh` reproduction wrapper has been mirrored for this delivery
yet. Reproduction should start from the rendered command files and packet
provenance in this run record.
