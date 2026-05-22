# Morphic Provenance Agent Guide

This repo is for run provenance, not source code or analysis development.

## Rules

- Do not commit large payloads such as h5ad, h5, h5mu, BAM, FASTQ, Matrix
  Market matrices, or bulky logs.
- Commit manifests, checksums, rendered commands, environment summaries,
  package locks, image digests, and small handoff summaries.
- Treat completed run folders as append-only.
- Corrections must be explicit and timestamped.
- Every CellBender production/handoff record must state whether CUDA was used;
  production CellBender without CUDA is a failed/mislaunched run.

## Run Folder

Use `templates/run/` as the starting point for each new run:

```text
runs/<project>/<run_id>/
  README.md
  run.json
  inputs/
  commands/
  environment/
  outputs/
  logs/
  handoff/
```

Large logs can live outside git, but record their path, bytes, checksum, and
retention policy.
