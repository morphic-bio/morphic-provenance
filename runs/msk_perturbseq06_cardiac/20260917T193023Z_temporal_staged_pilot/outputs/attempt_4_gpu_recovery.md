# Attempt 4 GPU Recovery

- Workflow ID: `msk-cardiac-staged-pilot-20260917T193023Z-attempt4`
- Temporal run ID: `8814456d-bbf4-4f35-86d2-2452a9d8c8de`
- Slurm job: `46275807`, `COMPLETED`, exit `0:0`, elapsed `00:57:16`.
- Stage-back Globus task: `be2140af-b2d2-11f1-be05-02ffe792127d`,
  `SUCCEEDED`, 7 files, 4,455,273 bytes, zero faults.
- Initial GPU issue: directory rsync nested the mapped MEX path one level too
  deep. The live staging directory was flattened and scheduler commit
  `97e6411` fixes directory-content semantics.
- CellBender then completed 10 CUDA training epochs on GPU 0. Its default MCKP
  output estimator failed on a zero-entry gene chunk in this deliberately
  low-depth one-million-read pilot. The checkpoint and diagnostic outputs were
  retained in the remote work directory.
- The parent was explicitly terminated to stop deterministic activity retries.
  Attempt 5 resumes from the already validated local MEX with `--estimator
  mean`; it does not rerun or resubmit Slurm.
