# Morphic Provenance

Immutable run records for STAR-suite and Morphic recipe executions.

This repo records what actually ran: exact commits, rendered commands,
parameters, input/output inventories, checksums, environment pins, logs, and
handoff transfer status. It should not contain large data payloads.

## Layout

```text
runs/<project>/<run_id>/  One immutable production or handoff run record
schemas/                  Machine-readable provenance schemas
templates/run/            Starter files for a new run record
docs/                     Provenance policy and conventions
```

## Lookup Order

When reproducing a STAR-suite processing pipeline:

1. Start from `runs/<project>/<run_id>/README.md` and `run.json`.
2. Follow the recorded recipes repo commit and workflow id.
3. Follow the recorded STAR-suite commit and binary checksum.
4. Use the handoff packet only as a collaborator-facing convenience view.

## Large Data Policy

Do not commit h5ad, h5, h5mu, BAM, FASTQ, Matrix Market payloads, or large logs.
Reference them by path or URI with size, checksum, and retention policy.

## Correction Policy

Completed run records are append-only. If a mistake is found, add a
`corrections` entry to `run.json` and update the run README with the reason.
Do not rewrite history silently.
