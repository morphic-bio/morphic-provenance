# MSK Perturb-seq 06 Cardiac Bridges-2 Production

Run ID: `20260917T141758Z_bridges2_v194_production`
Created UTC: 2026-09-17T14:17:58Z
Status: in progress

## Purpose

Run all eight completed Cardiac captures after the two-node Bridges-2 pilot and
matched Pikachu control passed. This record is separate from the immutable
pilot record at `../20260917T115903Z_bridges2_v194_pilot/`.

## Production Scope

| Array task | Capture | GEX | Guides |
| ---: | --- | --- | --- |
| 0 | `CP_A1` | TRU | NXT |
| 1 | `CP_A2` | TRU | NXT |
| 2 | `CP_A3` | TRU | NXT |
| 3 | `CP_B1` | TRU | NXT |
| 4 | `CP_B2` | TRU | NXT |
| 5 | `CP_B3` | TRU | NXT |
| 6 | `CP_R1` | TRU | NXT |
| 7 | `CP_R2` | TRU | NXT |

The Slurm array is `0-7%1`: captures run serially to limit filesystem pressure,
while each capture uses 64 STAR threads and eight parallel native-gzip staging
copies. Inputs are copied byte-for-byte to node-local storage and validated by
provider MD5 plus `gzip -t`. No transcode and no zshard path are used.

## Fixed Analysis Surface

- STAR Suite v1.9.4, commit
  `1c9ddb9a5a2a3e62748e8e4ef28e553582affeed`.
- GRCh38 2024-A / GENCODE v44 index used for MSK-30.
- GEX: February-2018 TRU whitelist, `GeneFull` and `Velocyto`.
- Guides: February-2018 NXT whitelist, 15,656-feature LEG reference, maximum
  Hamming distance 1, and canonical integrated TRU output.
- CR-compatible EmptyDrops cell calling and multimapper rescue.
- Unsorted BAM retained for each capture.
- No Y removal.

The active production array script is
`commands/run_cardiac_production_array_v2.sbatch`, SHA-256
`6528a29d85320f72020f53a7b4372498581e1e5c68d6081e117e5cf1d0c2e076`.

## FASTQ Read-Token Correction

The first CP_A1 task failed before durable output because `process_features`
v1.9.4 classified every `_R3_` substring as a reverse-read marker. In these
provider filenames, `CP_R3_` is a library/run prefix; the delivered guide data
contain only terminal `_R1_` and `_R2_` reads.

The active v1.9.4 run uses a reversible node-local filename alias only for
guide staging: leading `CP_R1_`, `CP_R2_`, or `CP_R3_` becomes `CPR1_`,
`CPR2_`, or `CPR3_`. File bytes are unchanged, the provider basename remains
in `stage.tsv`, and a pre-run gate requires complete terminal R1/R2 pairs and
zero terminal R3 files.

The underlying STAR Suite parser was fixed separately in commit `e9c1ff7`:
each candidate R1-token position is resolved by the exact mate filename it
produces. This production run does not use that post-v1.9.4 source change.

## Inputs And Outputs

Input:

```text
/ocean/projects/bio230034p/lhung2/incoming/MSK_Perturbseq_20260910/
  MSK_Perturbseq06_Cardiac_20260910/
```

Production output:

```text
/ocean/projects/bio230034p/lhung2/msk-perturbseq06-cardiac-20260917/
  results/production/<capture>/
```

The refreshed input audit passed with 1,020 FASTQs, 16 libraries, eight logical
captures, 255 processing read pairs, and 707,990,121,243 delivered bytes.

## Jobs

- Initial production array `46249747`: failed task 0, remaining tasks canceled.
- Initial validator `46250387`: canceled with the failed array.
- Corrected CP_A1 gate: `46251625` (`--array=0`).
- Remaining captures: `46251626`, submitted as `--array=1-7%1` after
  `46251625`, then corrected in place to `--array=1-7%7`. The CP_A1 gate
  already prevents a failed configuration from reaching the other captures;
  after that gate, all seven captures are independent and can use separate
  nodes as scheduler capacity permits.
- Whole-set validator: `46251627` (after `46251625` and `46251626`).
- Exact failed-job scratch cleanup: `46251631` on `r225` and `46251632` on
  `r203`; these target only `/local/msk-cardiac-cp_a1-46249925` and
  `/local/msk-cardiac-cp_a2-46251382`.

The validator writes `results/production/PRODUCTION_GATHER.json` only after all
eight array tasks finish successfully and the expected GEX, Velocyto, guide,
combined MEX, BAM, namespace, staging, and completion artifacts pass.

## Downstream H5AD Pipeline

The user service `msk-cardiac-downstream-20260917.service` runs
`commands/run_ocean_gpu_h5ad_pipeline.py` and waits for each accepted upstream
capture. It transfers only required outputs from Ocean, creates GeneFull and
Velocyto H5ADs, runs CellBender 0.3.2 on the remote CUDA host, validates layers
and guide metadata, and checksum-transfers results back to
`results/downstream/<capture>` on Ocean. Scimilarity and cell-type assignment
are intentionally skipped because no reference labels are available yet.
