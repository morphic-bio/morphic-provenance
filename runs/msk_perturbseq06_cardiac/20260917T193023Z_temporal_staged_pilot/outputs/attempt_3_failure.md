# Attempt 3 Failure

- Workflow ID: `msk-cardiac-staged-pilot-20260917T193023Z-attempt3`
- Temporal run ID: `255a53ce-fea7-45ed-b213-28e9e5a619b9`
- Globus stage-in: intentionally omitted because attempts 1 and 2 completed
  and checksum-validated the same four immutable inputs.
- Failure stage: Slurm submission.
- Failure: Bridges-2 RM-shared limits memory requests to 2000 MB/core; Slurm
  interpreted 64G as 65536 MB, or 2048 MB/core at 32 CPUs.
- Slurm state: `sbatch` rejected the request and assigned no job ID.
- Correction: request 62G (63488 MB), or 1984 MB/core, and retain the full
  remote `sbatch` diagnostic through temporal-scheduler commit `0b9c7fd`.
