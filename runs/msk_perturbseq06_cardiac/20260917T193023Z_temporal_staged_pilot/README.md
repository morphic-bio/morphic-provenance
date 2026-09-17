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
- Temporal scheduler staged-runtime implementation: commit
  `a4fdc15b38766b9e3c4ecfc16c12dd68ba40b1b4`.
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
