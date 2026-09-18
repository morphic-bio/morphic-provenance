# Final Validation Report

## Outcome

The CP_R1 one-million-read scheduler pilot passed all execution boundaries.
Attempts 1-3 failed before scientific execution while hardening Slurm batch
transport and site-resource diagnostics. Attempt 4 completed the one allowed
scientific Slurm submission and stage-back. Attempt 5 resumed at GPU and
publication without resubmitting Slurm.

## Durable identifiers

| Item | Identifier | Result |
|---|---|---|
| Initial stage-in | `e4a17fc9-b2ce-11f1-bf7b-0affd5e180af` | 4 files, 3,049,085,471 bytes, zero faults |
| Idempotent stage-in check | `bb27895e-b2d0-11f1-b4ab-0effcb3df825` | 4 checksum-identical files skipped, zero faults |
| Slurm job | `46275807` | `COMPLETED`, exit `0:0`, `00:57:16`, node `r243` |
| Stage-back | `be2140af-b2d2-11f1-be05-02ffe792127d` | 7 files, 4,455,273 bytes, zero faults |
| GPU recovery workflow | `f9ac18d7-149e-413f-b11b-4bbcb0b9d29a` | `Finished`; Slurm explicitly `SKIPPED` |
| GPU child | `rdjob_rdiac_staged_pilot_20260917T193023Z_attempt5_gpu` | 9 output artifacts, CUDA device 0 |
| Publication | `9b6d8577-b2dc-11f1-9987-0effcb3df825` | 9 files, 1,086,539,425 bytes, zero faults |

## Scientific smoke checks

- STAR Suite v1.9.4 processed exactly 1,000,000 reads with 94.13% uniquely
  mapped. Peak Slurm batch RSS was 29,637,216 KiB under the 62G request.
- Raw combined GeneFull + CRISPR MEX: 54,262 features x 97,789 barcodes and
  801,269 non-zero entries.
- CRISPR calling emitted 25,168 cell rows plus the CSV header.
- Raw Velocyto: 38,606 genes x 3,686,400 barcode universe; filtered Velocyto:
  38,606 genes x 25,168 barcodes. Spliced, unspliced, and ambiguous layers are
  present on Ocean.
- CellBender 0.3.2 ran 10 CUDA epochs using the `mean` estimator. Full output:
  54,262 x 97,789. Filtered output: 54,262 x 629. The checkpoint and all report
  artifacts are present locally and on Ocean.

## Artifact locations

```text
Local Slurm stage-back:
  /mnt/pikachu/MSK_Perturbseq06_Cardiac_temporal_pilot_20260917T193023Z/slurm/

Local CellBender outputs:
  /mnt/pikachu/MSK_Perturbseq06_Cardiac_temporal_pilot_20260917T193023Z/gpu/

Ocean Slurm results:
  /ocean/projects/bio230034p/lhung2/temporal-cardiac-pilot-20260917T193023Z/results/slurm/

Ocean published GPU outputs:
  /ocean/projects/bio230034p/lhung2/temporal-cardiac-pilot-20260917T193023Z/results/published/
```

`final_validation.json` records the machine-checked dimensions and completion
markers. `final_artifact_manifest.tsv` records local sizes and SHA-256 hashes;
the Globus publication used checksum verification and completed with zero
faults.
