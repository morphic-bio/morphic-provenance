# JAX Multiome01 Globus Release 2026-05-18

## Summary

This release records the revised JAX Multiome01 h5mu analysis packet pushed to
Globus on 2026-05-18, plus the supporting large-file transfers that completed
through 2026-05-19.

The canonical run provenance is:

```text
runs/jax_multiome01/20260517T183219Z_star_multiome_prod_globus/
```

The temporary `provenance.md` included in the Globus packet is superseded by
the run record above and by these release notes.

## Globus Destinations

Compact h5mu analysis packet:

```text
/JAX_Multiome01_processed/JAX-Multiome01-5-18-26-revised/h5mu
```

Large-file support packet:

```text
/JAX_Multiome01_processed/large_files/star_multiome_prod_globus_20260517T183219Z
```

Destination endpoint:

```text
61fb8b9a-9b52-456e-928c-30c0fb0140bf
```

## Upload Summary

Compact h5mu task:

```text
3ac95aae-5321-11f1-b294-0ea3589134b3
```

The compact handoff task reported `succeeded` with 20 files transferred. The
upload manifest lists the 18 h5mu data files with checksums plus the two
packet-level documents preserved from the local production root.

Large-file support uploads used one Globus task per sample. All nine sample
tasks transferred successfully; generated local BAM/Y-noY FASTQ artifacts were
deleted after their corresponding task succeeded. Raw input FASTQs were
preserved locally.

Known manifest totals:

- Compact h5mu data files: 18 files, 93,032,562,506 bytes.
- Compact h5mu data files plus packet documents: 20 files, 93,032,582,550 bytes.
- Large-file sample bundles: 9 tasks, 2,825,306,707,194 bytes.

See `upload_manifest.tsv` for per-file and per-task details.

## Recipe Documentation

Human-facing recipe READMEs are in `morphic-recipes`:

```text
docs/production_recipes/jax_multiome01_star_multiome/
docs/production_recipes/jax_multiome01_remote_post_mex/
docs/production_recipes/jax_multiome01_mt_adaptive_retrofit/
docs/production_recipes/jax_multiome01_globus_large_files/
```

The executed script hashes and source commits are in:

```text
runs/jax_multiome01/20260517T183219Z_star_multiome_prod_globus/commands/script_hashes.tsv
```

## Updates

Append release-specific additions and corrections in `updates.md`.
