# MSK Cardiac Temporal Staged Pilot

Run ID: `20260917T193023Z_temporal_staged_pilot`

This pilot validates one durable Temporal workflow across these execution
boundaries:

1. Globus stage-in from Pikachu to Bridges-2 Ocean;
2. a STAR Suite v1.9.4 Slurm job on Bridges-2;
3. Globus stage-back of the raw MEX to Pikachu;
4. CellBender 0.3.2 with CUDA on Pikachu's RTX 4060;
5. Globus publication of the CellBender outputs to Ocean.

The input is a one-million-read subsample selected by STAR's
`--readMapNumber 1000000` from the CP_R1 Cardiac GEX and guide lane pair. The
source files remain native gzip. No zshard or gzip transcoding is used.

## Fixed assay and software surface

- STAR Suite: v1.9.4, commit
  `1c9ddb9a5a2a3e62748e8e4ef28e553582affeed`.
- Temporal scheduler staged-runtime implementation: commits
  `a4fdc15b38766b9e3c4ecfc16c12dd68ba40b1b4` and
  `97e64118bdfec80bf42a3e2361e738afa852b1ab`.
- Genome index: GRCh38 2024-A / GENCODE v44 at
  `/ocean/projects/bio230034p/shared/processing/references/GRCh38-2024-A-star-msk30`.
- GEX chemistry and whitelist: TRU, February 2018 3M.
- Guide chemistry and whitelist: NXT input, February 2018 3M, canonical TRU
  output, LEG feature reference, maximum Hamming distance 1.
- STAR outputs: GeneFull, Velocyto, integrated CRISPR guide assignments, no
  BAM for this scheduler smoke pilot.
- CellBender: `biodepot/cellbender:0.3.2`, CUDA required, GPU device 0,
  minimum 6000 MB free at launch.
- Scimilarity and cell-type assignment are out of scope because no Cardiac
  reference labels are available yet.

## Paths

```text
Pikachu input:
  /mnt/pikachu/MSK_Perturbseq06_Cardiac_pilot_inputs_20260917/

Pikachu result:
  /mnt/pikachu/MSK_Perturbseq06_Cardiac_temporal_pilot_20260917T193023Z/

Ocean run root:
  /ocean/projects/bio230034p/lhung2/temporal-cardiac-pilot-20260917T193023Z/
```

`commands/build_request.py` generates fresh retry-safe Globus submission IDs
and embeds `commands/slurm_cardiac_subsample.sh` in the Temporal request.
`commands/start_workers.sh` starts isolated host workers and an API on port
8010 against the existing local Temporal server. `commands/submit_and_monitor.py`
submits and records the complete status history.

This pilot is separate from the active eight-capture production run and writes
only to the dedicated paths above.

## Attempts

Attempt 1 completed the four-file Globus stage-in, then failed before `sbatch`:
Bridges-2 has no login-node `rsync`, and the inherited Slurm transport used
rsync to upload only the generated batch script. Scheduler commit `4ae1fa4`
changed that internal batch-script write to Paramiko SFTP. Bridges-2 also
disables its SFTP subsystem, so attempt 2 failed at the same pre-submission
boundary after checksum-validating and skipping all four staged inputs.
Scheduler commit `b661511` uses the existing SSH exec channel and streams the
script on stdin, which was tested directly against this Ocean run directory.
No Slurm job was submitted in attempts 1 or 2. Attempt 3 reached `sbatch`, which
rejected the 64G request because 65536 MB / 32 CPUs exceeds RM-shared's 2000
MB/core site limit. Scheduler commit `0b9c7fd` preserves remote submission
diagnostics, and attempt 4 requests 62G / 32 CPUs (1984 MB/core). It resumes at
the Slurm stage because Globus stage-in succeeded and was checksum-validated
twice. Attempt 4 completed Slurm and stage-back, then exposed directory nesting
in SSH/Docker rsync and a CellBender MCKP edge case on the deliberately
low-depth pilot. Scheduler commit `97e6411` fixes mapped-directory semantics and
supports an explicit GPU-and-publish recovery mode. Attempt 5 uses that mode
with CellBender's `mean` estimator and does not submit a second Slurm job.

## Final result

The staged pilot passed as a two-part durable recovery sequence:

- attempt 4: Slurm job `46275807` completed on `r243` in `00:57:16`, then
  Globus stage-back task `be2140af-b2d2-11f1-be05-02ffe792127d` transferred 7
  files / 4,455,273 bytes with zero faults;
- attempt 5: GPU-and-publish recovery run
  `f9ac18d7-149e-413f-b11b-4bbcb0b9d29a` ran CellBender with CUDA on Pikachu,
  produced 9 output artifacts, and published them with Globus task
  `9b6d8577-b2dc-11f1-9987-0effcb3df825` (1,086,539,425 bytes, zero faults).

Validation passed for the raw combined MEX (`54,262 x 97,789`, 801,269
entries), CellBender full output (`54,262 x 97,789`), and CellBender filtered
output (`54,262 x 629`). Ocean retains GeneFull, raw/filtered Velocyto layers,
and the integrated CRISPR call outputs. See `outputs/final_validation.json`,
`outputs/final_artifact_manifest.tsv`, and `outputs/final_report.md`.

This is an orchestration smoke test on one million reads. Its 629-cell
CellBender result is not a scientific Cardiac release or a substitute for the
independent full-capture production run.
