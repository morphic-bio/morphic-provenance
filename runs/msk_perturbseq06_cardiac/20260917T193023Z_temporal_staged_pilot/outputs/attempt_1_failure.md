# Attempt 1 Failure

- Workflow ID: `msk-cardiac-staged-pilot-20260917T193023Z`
- Temporal run ID: `dbccd42b-9ed5-406e-80d1-3473b0ae2120`
- Globus stage-in task: `e4a17fc9-b2ce-11f1-bf7b-0affd5e180af`
- Stage-in result: `SUCCEEDED`, 4 files, 3,049,085,471 bytes, zero faults.
- Failure stage: generated Slurm batch-script upload.
- Failure: the Bridges-2 login node does not provide `rsync`.
- Slurm state: `sbatch` was not invoked and no pilot job ID was assigned.
- Correction: temporal-scheduler commit `4ae1fa4` writes generated batch
  scripts over the existing Paramiko SFTP connection.
