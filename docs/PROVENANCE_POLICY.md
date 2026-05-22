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
