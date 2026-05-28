# Provenance Policy

## Required Files

Every completed run should include:

- `README.md`: concise human-readable run summary.
- `run.json`: machine-readable run record matching `schemas/run.schema.json`.
- `inputs/manifest.tsv`: input files or directories.
- `inputs/checksums.tsv`: checksums for immutable input files when practical.
- `commands/*.argv.json`: rendered command arrays and environment overrides.
- `environment/`: image digests, package locks, host/GPU summaries.
- `outputs/manifest.tsv`: output files or directories.
- `outputs/checksums.tsv`: checksums for handoff payloads.
- `handoff/transfer-status.json`: transfer task ids and final status when used.

## Dataset Release Notes

Every collaborator-facing dataset push should also have a dated release note
under:

```text
dataset_releases/<project>/<YYYY-MM-DD>/
```

Use the date the analysis packet was pushed to Globus as the release key. If
supporting large-file transfers continue after that date, keep them in the
same release note and record their final completion dates explicitly.

Each release note should include:

- `README.md`: human-facing summary of the delivery, destination paths,
  linked run records, status, and known caveats.
- `upload_manifest.tsv`: files or upload bundles sent to Globus, with task
  IDs, destination paths, byte counts, checksums when available, and status.
- `updates.md`: append-only additions, corrections, or later clarifications for
  that release.

Run records remain the canonical source for exact commands and environment.
Dataset release notes are the canonical source for what was delivered to
collaborators on a given Globus release date.

## Environment

Record resolved image digests, not just tags. For GPU workflows also record
`nvidia-smi`, CUDA, driver, PyTorch, CellBender, Scanpy, AnnData,
scikit-learn, and scvi-tools versions when present.

## Corrections

For a completed run, add corrections instead of editing history silently:

```json
{
  "corrections": [
    {
      "created_utc": "2026-05-22T00:00:00Z",
      "author": "name",
      "reason": "what was wrong",
      "changed_fields": ["outputs[0].sha256"]
    }
  ]
}
```
