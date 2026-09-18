# MSK Cardiac Recipe Interchange Validation

Project: `msk_perturbseq06_cardiac`

Run ID: `20260918T002739Z_recipe_interchange_validation`

Status: validated dry-run; no scientific job or transfer was submitted

Created UTC: 2026-09-18T00:27:39Z

## Purpose

Validate the staged execution-recipe to Workflow IR to Temporal request path
against the completed CP_R1 one-million-read cardiac pilot. This reuses the
archived pilot's real transfer lists, Slurm resources, STAR Suite wrapper,
CellBender CUDA command, and publication paths.

The source pilot remains the execution evidence:

```text
runs/msk_perturbseq06_cardiac/20260917T193023Z_temporal_staged_pilot/
```

## Result

The adapter produced a valid `biodepot.staged-execution-plan/v1`, a schema-driven
Workbench bundle, and the specialized scheduler request. Preflight was ready.
The staged plan contains no endpoint IDs or task queues; those appear only in
the reviewable executor form data and final request.

The generated request preserves:

- four native `.fastq.gz` inputs plus the tracked STAR wrapper;
- 32 Slurm CPUs and the archived Bridges-2 directives;
- the five-item stage-back set;
- CellBender 0.3.2 with `--cuda` and the raw MEX handoff;
- the archived publication path.

See `outputs/validation.json`. Approval remains false and this validation did
not call Globus, Slurm, Docker, or Temporal.

`outputs/scheduler-parser-validation.json` records an additional PASS from the
pinned scheduler's typed request parser.

## Code

- `bwb-nextflow-utils`: `577c27f39e1dc3c83cf133eaf489dde37d85752e`
- `temporal-scheduler`: `2e35bcc`
- STAR Suite in source wrapper: `1.9.4`
- CellBender image: `biodepot/cellbender:0.3.2`

## Method

Run `commands/build_and_validate.py` as documented in `commands/README.md`.
The script derives deployment details from the archived pilot request files,
then writes the recipe, IRs, profile, workbench bundle, staged plan, dry-run
request, preflight result, and validation checks into this run record.
