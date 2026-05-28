# SLAM-seq PE Production Full Run

Project: `slam_seq_pe`

Run ID: `20260511T103908Z_prod_full`

Status: complete

Created UTC: 2026-05-11T10:39:08Z

## Purpose

Canonical provenance record for the full paired-end SLAM-seq production run and
its Globus handoffs.

The source `provenance.md` included with the production tree is preserved under
`handoff/temporary_packet_provenance.md` and is superseded by this repo record.

## Code

- STAR-suite production checkout: `/mnt/pikachu/STAR-suite-slam-pe-prod`
- STAR-suite commit: `9758a2697b8e9e753584d1d095f8f44695db0c14`
- STAR binary SHA256: `76e1fdd481785123d6dca961483283ca93fee41a9fde5faab5ca1b277568edf8`
- Production launcher: `scripts/run_slam_prod_set.sh`

## Inputs And Commands

Run configuration is in `inputs/run_config.env`. Per-sample rendered commands
are preserved in `commands/commands.tsv`.

## Outputs

The production root is:

```text
/mnt/pikachu/SLAM-Seq-PE-results/prod_full_20260511T103908Z
```

The full file inventory is `outputs/MANIFEST.files.tsv`. DESeq2 runtime details
and upload manifests are in `handoff/`.

## Handoff

See `handoff/README.md`.

## Dataset Release Notes

```text
dataset_releases/slam_seq_pe/2026-05-12/
dataset_releases/slam_seq_pe/2026-05-15/
```

## Reproduction Entrypoint

No single `run_all.sh` reproduction wrapper has been mirrored for this delivery
yet. Reproduction should start from `inputs/run_config.env`,
`commands/commands.tsv`, and the script/hash provenance in
`handoff/temporary_packet_provenance.md`.
