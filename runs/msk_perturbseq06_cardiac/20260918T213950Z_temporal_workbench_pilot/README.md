# MSK Cardiac Temporal Workbench Pilot

Run ID: `20260918T213950Z_temporal_workbench_pilot`

Status: Workbench and staged Temporal services active; dry run passed; no live
workflow submitted

This record connects the schema-driven Workbench to the proven staged Temporal
path for the MSK Perturb-seq 06 Cardiac CP_R1 one-million-read pilot:

1. native-gzip FASTQs are staged from Pikachu to Bridges-2 Ocean with Globus;
2. STAR Suite 1.9.4 runs on Bridges-2 Slurm with 32 CPUs;
3. the raw MEX is staged back to Pikachu;
4. CellBender 0.3.2 runs in Docker with CUDA on Pikachu;
5. outputs are published back to Ocean with Globus.

The Workbench exposes all paths, endpoint IDs, queue names, Slurm resources,
and GPU settings for user review. Live submit remains blocked behind its
explicit approval dialog. Starting the services does not submit a workflow.

## Inputs and constraints

- GEX chemistry: TRU.
- guide input chemistry: NXT; guide output is canonical TRU.
- compressed inputs remain native `.fastq.gz`; no zshard or transcoding.
- STAR index: GRCh38 2024-A / GENCODE v44.
- STAR Suite: 1.9.4.
- Slurm: one node, 32 CPUs, 64 GiB, `RM-shared`, four-hour request.
- CellBender: `biodepot/cellbender:0.3.2`, `--cuda`, 10 pilot epochs.
- Scimilarity is outside this pilot.

## Code paths

- recipe/Workbench adapter: `/mnt/pikachu/bwb-nextflow-utils-staged-recipe-20260918`
- recipe/Workbench commit: `3725358d8bc93d99c0990a9bae8f055b20a389a5`
- staged Temporal scheduler: `/mnt/pikachu/temporal-scheduler-cardiac-pipeline-20260917`
- staged Temporal scheduler commit: `2e35bccfb65f6d3a5f9f81cde09c96dde53b1539`
- source execution evidence: `../20260917T193023Z_temporal_staged_pilot/`
- source adapter validation: `../20260918T002739Z_recipe_interchange_validation/`

The staged Python Temporal scheduler is used because it implements the full
Globus -> Bridges-2 Slurm -> Pikachu GPU -> Globus contract. The Go scheduler's
single-Slurm executor contract does not yet represent this multi-site handoff.

## Operation

`commands/prepare_workbench.py` generated a fresh bundle and dry-run scheduler
request. `commands/runtime_preflight.sh` checks credentials, endpoints,
references, STAR, Slurm, Docker CUDA, and path collision guards. After that,
`commands/start_services.sh` starts isolated workers, the staged scheduler API
on `127.0.0.1:8010`, and the Workbench on port `8894`.

Use `commands/print_workbench_url.py` for the preloaded URL. Review the bundle,
run Workbench preflight, inspect the submission preview, and use **Submit** only
after explicitly approving the pilot. `commands/stop_services.sh` stops this
record's services.

The live browser check passed at `2026-09-18T21:49:00Z`: the UI identified the
two recipe stages, Workbench preflight returned `ready`, and **Dry Run** produced
the scheduler payload without posting a workflow. See
`outputs/workbench-live-validation.json`.
