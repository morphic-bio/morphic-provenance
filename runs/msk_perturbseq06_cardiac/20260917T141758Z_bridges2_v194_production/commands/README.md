# Commands

- `SUBMISSION_COMMAND.sh`: exact original, corrected, validation, and node-local
  cleanup submission commands.
- `run_cardiac_production_array_v2.sbatch`: active v1.9.4 production array with
  reversible provider-prefix aliases and an R1/R2 mate-count gate.
- `gather_cardiac_production.sbatch`: whole-set validation job.
- `validate_cardiac_production.py`: validates all eight durable production
  capture directories.
- `run_ocean_gpu_h5ad_pipeline.py`: Ocean to Pikachu/GPU downstream
  orchestrator, including checksum transfers and CUDA CellBender.
- `validate_cardiac_h5ads.py`: validates counts, CellBender, Velocyto, and guide
  H5AD surfaces.
- `launch_downstream_watcher.sh`: preflight and service launch wrapper.

The superseded first-submission array entrypoint remains in the preceding pilot
record at `../20260917T115903Z_bridges2_v194_pilot/commands/`.
