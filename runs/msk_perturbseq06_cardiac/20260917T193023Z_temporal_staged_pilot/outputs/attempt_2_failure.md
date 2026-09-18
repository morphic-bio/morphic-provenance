# Attempt 2 Failure

- Workflow ID: `msk-cardiac-staged-pilot-20260917T193023Z-attempt2`
- Temporal run ID: `4dfdb295-fcc8-4637-bab8-565ee486a8d0`
- Globus stage-in task: `bb27895e-b2d0-11f1-b4ab-0effcb3df825`
- Stage-in result: `SUCCEEDED`, 4 checksum-identical files skipped, zero
  transferred bytes, and zero faults.
- Failure stage: generated Slurm batch-script upload.
- Failure: the Bridges-2 SSH service disables its SFTP subsystem.
- Slurm state: `sbatch` was not invoked and no pilot job ID was assigned.
- Correction: temporal-scheduler commit `b661511` streams the batch script to
  `cat > file` over an SSH exec channel. A direct write/read/delete probe in
  this run's Ocean scheduler directory passed before attempt 3.
