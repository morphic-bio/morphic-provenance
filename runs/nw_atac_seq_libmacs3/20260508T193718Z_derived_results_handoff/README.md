# NW ATAC-seq libMACS3 Derived Results Handoff

Project: `nw_atac_seq_libmacs3`

Run ID: `20260508T193718Z_derived_results_handoff`

Status: complete

Created UTC: 2026-05-08T19:37:18Z

## Purpose

Canonical provenance record for the NW ATAC-seq libMACS3 derived-results
submission staged under:

```text
/mnt/pikachu/globus_uploads/NW-ATAC-SEQ-results-libmacs3-05-05-26
```

The package `provenance.md` is preserved under `handoff/` as temporary handoff
context and is superseded by this run record.

## Code

This was a Chromap/libMACS3 ATAC-seq workflow, not a STAR-suite run.

- ATAC script repository: `https://github.com/morphic-bio/atac-seq`
- Base git hash observed at documentation time: `839ae2c31189547a460de963143e4604804b8f53`
- Chromap-suite source hash in local history: `0d41b6350a66f3add2dc9e6f195f64586119909e`
- Preserved Chromap executable SHA256: `68d8d47ff3d690966297a4723b6ff0f684f6f5a97ba2c4ac8eb87d3c76b02481`

## Inputs And Commands

Package construction sources are recorded in `outputs/MANIFEST.sources.tsv`.
Script hashes are in `commands/SHA256SUMS` and in the temporary packet
provenance.

## Outputs

The derived-results package manifest lists 3,565 file records including the
manifests themselves. The package summary records 2,401 final files, 201 final
sample directories, and 1,082 metadata files. See `outputs/`.

## Handoff

See `handoff/README.md`.

## Dataset Release Notes

```text
dataset_releases/nw_atac_seq_libmacs3/2026-05-19/
```

## Reproduction Entrypoint

No `run_all.sh` reproduction wrapper has been mirrored in `morphic-recipes` for
this delivery. Use the copied package manifests, script checksums, and the
source packet provenance.
