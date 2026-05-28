# MSK 30KO Revised Delivery

Project: `msk_30ko_revised`

Run ID: `20260519T000000Z_revised_delivery`

Status: complete

Created UTC: 2026-05-19T00:00:00Z

## Purpose

Canonical provenance record for the May 2026 MSK 30KO revised delivery and its
2026-05-19 Globus pushes.

The compact delivery `provenance.md` is preserved under `handoff/` as temporary
handoff context and is superseded by this run record.

## Code

- STAR-suite production commit recorded in STAR logs:
  `c082c6582cca229032c7bb34a157e97511561da8`
- Local STAR-suite checkout at provenance generation:
  `c535e327f626a61a601b5472b1589511ad6a8d9e`
- MSK production planning checkout HEAD:
  `a7587d1b4fc7a27bd9d563d34744c1ff386cd462`

## Inputs And Commands

The production source archives and exact script hashes are documented in
`handoff/temporary_packet_provenance.md`. The full sample-wise staged manifest
is preserved as `outputs/STAGED_MANIFEST.tsv`.

## Outputs

The compact old-layout delivery root is:

```text
/mnt/pikachu/MSK_30_KO_revised
```

The sample-wise h5ad/QC delivery staging root is:

```text
/mnt/pikachu/msk30ko-h5ad-qc-delivery/MSK-05-13-26-large-files
```

The compact local tree contains 47 files totaling 58,834,006,490 bytes. The
sample-wise staged manifest contains 604 rows totaling 74,511,451,794 bytes.

## Handoff

See `handoff/README.md`.

## Dataset Release Notes

```text
dataset_releases/msk_30ko_revised/2026-05-19/
dataset_releases/msk_30ko_revised/2026-05-26/
```

## Reproduction Entrypoint

No single `run_all.sh` reproduction wrapper has been mirrored for this delivery
yet. Reproduction should start from the MSK production planning runbook, the
script hashes in the packet provenance, and the manifests copied here.
