# MSK 40KO Globus Release 2026-05-28

## Summary

This release records the compact MSK 40KO h5ad/QC packet pushed to Globus on
2026-05-28 from the STAR-suite production run:

```text
runs/msk_40ko/20260521T232456Z_star_suite_production/
```

The packet included a human-facing provenance document and a machine-readable
run snapshot:

```text
/MSK-40KO-revised/provenance.md
/MSK-40KO-revised/provenance/run.json
```

The repository run record remains the updated source of truth. The packet
provenance files are collaborator-facing snapshots generated before this
release note was committed.

## Globus Destination

```text
/MSK-40KO-revised
```

Destination endpoint:

```text
61fb8b9a-9b52-456e-928c-30c0fb0140bf
```

Source endpoint:

```text
07446cad-33b8-11f0-8c0c-0afffb017b7d
```

## Upload Summary

Globus task:

```text
46b34ad4-5ac3-11f1-8e36-0affd989f133
```

Status: `SUCCEEDED`

Requested: `2026-05-28T18:30:18+00:00`

Completed: `2026-05-28T19:12:23+00:00`

Files transferred: 22

Bytes transferred: 19719172769

Checksum verification: `True`

The packet contains two sample count h5ads, count QC plots, gene and LARRY
feature h5ads, RF cell-typing provenance, runbook/manifest documentation,
checksums, and provenance files. Source FASTQs, BAMs, raw MEX matrices,
CellBender raw h5 payloads/checkpoints/posteriors, runtime caches, and
temporary logs are intentionally excluded.

See `upload_manifest.tsv` for per-file source, destination, size, SHA256, and
Globus checksum details.

## Updates

Append release-specific additions and corrections in `updates.md`.
