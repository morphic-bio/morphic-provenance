# JAX scRNAseq02 completion-overlay handoff

## Summary

This run record documents staging, validating, and transferring the 12
completed sample outputs that were absent from the original 2026-05-22
JAX scRNAseq02 packet. It is a handoff-only record: no biological processing
was rerun.

The original release contains 10 samples. This additive overlay contains the
remaining 12 samples, so the base release plus this overlay provide all 22
expected samples. The overlay replaces no paths and is not standalone.

## Lineage

- Canonical production run:
  `runs/jax_scrnaseq02/20260522T135526Z_ocm_prod_handoff/`
- Production output root:
  `/mnt/pikachu/JAX_scRNAseq02_processed/ocm_prod_batch_flex_native_yremove_trace_20260521T034223Z`
- Base Globus release:
  `/JAX_scRNAseq02_processed/JAX-scRNAseq02-5-22-26`
- Completion overlay:
  `/JAX_scRNAseq02_processed/JAX-scRNAseq02-5-22-26-completion-7-27-26`

## Included samples

| Library preparation | Samples |
|---|---|
| `25E34-L4` | `EPAS1-Day-5`, `ISL1-Day-5`, `WT-ExM-Day-5`, `WT-PrS-3pct-Day-5` |
| `25E35-L3` | `GCM1-Day-6`, `GRHL1-Day-6`, `OVOL1-Day-6`, `WT-PrS-20pct-Day-6` |
| `25E35-L4` | `EPAS1-Day-6`, `ISL1-Day-6`, `WT-ExM-Day-6`, `WT-PrS-3pct-Day-6` |

The library preparation identifier for Day 6 pool 5 is `25E35-L3`.
`25E5-L3` is not a production library identifier for this dataset.

## Staging and validation

The packet was staged at:

```text
/mnt/pikachu/JAX_scRNAseq02_handoff/JAX-scRNAseq02-5-22-26-completion-7-27-26
```

The staging script was:

```text
/mnt/pikachu/JAX_scRNAseq02/scripts/stage_jax_scrnaseq02_completion_overlay.py
```

Its SHA-256 was
`30d1642063097b42ef3939822287153aa7d6cc548a8092ef320d6181a4a85810`.
The packet used hard links, matching the original release packet. Every staged
source-to-packet pair was checked for identical device and inode.

Validation confirmed:

- 12 sample directories;
- 17 payload files per sample;
- 204 payload files totaling 54,829,837,018 bytes;
- 210 transferred files including packet documentation;
- no duplicate payload-relative paths;
- all sources listed in the transfer batch existed;
- all 60 H5AD files were readable;
- H5AD structure and observation fields were consistent with the packet
  data dictionary; and
- the `spliced`, `unspliced`, and `ambiguous` layers were present but all-zero
  in every overlay H5AD file.

CellBender outputs in this packet are the GPU/CUDA production outputs.

## Transfer

The transfer used checksum-level synchronization and destination checksum
verification. The exact argument vector is preserved in
`commands/globus_transfer.argv.json`.

Globus task:

```text
6d5e713a-8a01-11f1-881a-02ce27bde401
```

Final status: `SUCCEEDED` at `2026-07-27T22:04:41Z`.

A recursive destination listing independently confirmed 210 files,
54,830,077,298 bytes, 12 top-level sample directories, and the six packet
metadata files.

## Output records

- `outputs/MANIFEST.tsv`: 204 payload files.
- `outputs/SHA256SUMS.tsv`: packet checksums captured before transfer.
- `outputs/sample_summary.tsv`: per-library and per-sample totals.
- `handoff/globus_batch.tsv`: exact 210-file transfer batch.
- `handoff/globus_task_submit.json`: accepted Globus submission.
- `handoff/globus_task_final.json`: final Globus task record.
- `handoff/remote_inventory_summary.json`: independent recursive destination
  count after transfer.
- `handoff/remote_root_listing.txt`: destination root listing after transfer.
- `handoff/packet_README.md`: collaborator-facing packet instructions and
  H5AD data dictionary.

The dated release record is
`dataset_releases/jax_scrnaseq02/2026-07-27/`.
