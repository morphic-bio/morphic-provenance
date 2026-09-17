# MSK Perturb-seq 06 Cardiac Bridges-2 Pilot

Run ID: `20260917T115903Z_bridges2_v194_pilot`
Created UTC: 2026-09-17T11:59:03Z
Status: pilot and Pikachu host control passed
Production status: not submitted

## Purpose

Prepare and execute a production-shaped preflight for the completed MSK
Perturb-seq 06 Cardiac delivery before launching all eight captures.

The pilot runs `CP_R1` and `CP_R2` as two one-element submissions of the same
Slurm array script on two distinct Bridges-2 nodes, then gathers both outputs.
The same two captures run sequentially on Pikachu as a host control. Each
capture uses one GEX FASTQ pair, one guide FASTQ pair, and a 250,000-read cap.

Each Bridges pilot task reserves 64 CPUs and 120 GB to satisfy the
`RM-shared` 2-GB-per-allocated-CPU rule; STAR itself uses 32 threads. The
submitter pins the two one-element array submissions to distinct idle nodes,
and the dependent gather verifies the node names.

## Fixed Policies

- STAR Suite v1.9.4, commit
  `1c9ddb9a5a2a3e62748e8e4ef28e553582affeed`.
- Bridges-2 uses the v1.9.4 portable `WITH_CHROMAP=0` build because Ocean has
  no non-zshard Chromap development tree and Pikachu binaries are not ABI
  portable to Bridges-2. Pikachu uses the normal `WITH_CHROMAP=1` build;
  Chromap is not invoked by either scRNA pilot.
- The pinned v1.9.4 archive needs two Bridges portability adjustments: use its
  bundled HTSlib headers and omit duplicate BGZF reader objects from the
  integrated `process_features` link. The durable repository fix was pushed to
  STAR Suite `master` as commit `99a6536`; this run remains on the pinned
  v1.9.4 source plus the recorded build-only adjustments.
- Bridges orchestration and validation use the installed `python3.11`; the
  login-node default is Python 3.6 and is not compatible with these scripts.
- GRCh38 2024-A / GENCODE v44 index matching MSK-30.
- No `zshard-*` path, code, reference, input, scratch, or output.
- Native gzip input; no BGZF/CBQ conversion and no other FASTQ transcode.
- GEX uses February-2018 TRU.
- PolyIII guides use February-2018 NXT input. Assignment-layer `cr_assign`
  MEX files remain NXT by design; integrated `outs/*feature_bc_matrix` files
  are canonical TRU.
- No Y removal.
- Pilot emits GeneFull plus CR-compatible guide outputs, without BAM or
  Velocyto.
- Full production is prepared but cannot be submitted until the pilot and host
  comparison pass.

## Data

Bridges-2 input:

```text
/ocean/projects/bio230034p/lhung2/incoming/MSK_Perturbseq_20260910/
  MSK_Perturbseq06_Cardiac_20260910/
```

The Globus delivery task completed successfully with 2,232 files and
1,353,334,473,146 transferred bytes across the PFP and Cardiac folders. The
Cardiac folder contains 1,020 FASTQs and `cp.checksums.md5`.

See `inputs/Cardiac_corrected_library_manifest.tsv` and
`inputs/Cardiac_corrected_file_manifest.tsv` for the corrected eight-capture
grouping. Historical presence fields in the September 4 file manifest describe
the earlier partial delivery; `build_cardiac_execution_manifest.py` rechecks
the current Ocean directory and writes a current execution manifest.

The selected CP_R1 guide pair retains the provider basenames
`CP_gRNA_IGO_17967_B_4_S38_L005_R{1,2}_001.fastq.gz`. The names omit `R1`, but
the corrected manifest assigns these files to logical library `CP_R1_gRNA`;
that manifest assignment is authoritative.

## Reference Decision

`outputs/reference_index_audit.md` records why the pre-existing Ocean 2020-A
index is coherent but not appropriate for this run. The pilot is hard-gated on
the exact 2024-A/MSK-30 index under the non-zshard path:

```text
/ocean/projects/bio230034p/shared/processing/references/
  GRCh38-2024-A-star-msk30/
```

## Commands

- `commands/prepare_inputs.sh`: current delivery and reference preflight.
- `commands/build_star_v194.sbatch`: clean v1.9.4 build.
- `commands/run_two_capture_pilot.sbatch`: two-node CP_R1/CP_R2 pilot array.
- `commands/gather_two_node_pilot.sbatch`: dependent cross-node gather.
- `commands/run_pikachu_control.sh`: matched Pikachu control.
- `commands/compare_pilot_hosts.py`: Pikachu versus Bridges result comparison.
- `commands/run_cardiac_production_array.sbatch`: prepared eight-capture
  production array; do not submit before pilot acceptance.

## Output Roots

Bridges-2:

```text
/ocean/projects/bio230034p/lhung2/msk-perturbseq06-cardiac-20260917/
```

Pikachu control:

```text
/mnt/pikachu/MSK_Perturbseq06_Cardiac_pilot_results_20260917/
```

CellBender is not part of this pilot. Any later production
CellBender run must use CUDA and record the GPU validation separately.

## Pilot Result

The Bridges two-node pilot, Pikachu control, and host comparison all passed.
Production was not submitted.

| Stage | Slurm job | Node | Elapsed | Result |
| --- | ---: | --- | ---: | --- |
| v1.9.4 portable build | `46246773` | `r290` | 00:01:28 | PASS |
| `CP_R1` pilot | `46246783` | `r039` | 00:23:31 | PASS |
| `CP_R2` pilot | `46246784` | `r067` | 00:17:42 | PASS |
| Two-node gather | `46246785` | `r055` | 00:00:04 | PASS |

| Capture | Raw GeneFull | Filtered GeneFull | Guide MEX | Combined raw | Combined filtered |
| --- | --- | --- | --- | --- | --- |
| `CP_R1` | 38,606 x 3,686,400; 150,628 UMIs | 38,606 x 24,542; 127,431 UMIs | 15,656 x 43,020; 108,271 UMIs | 54,262 x 47,739; 233,824 UMIs | 54,262 x 24,542; 203,346 UMIs |
| `CP_R2` | 38,606 x 3,686,400; 141,421 UMIs | 38,606 x 54,452; 120,022 UMIs | 15,656 x 74,822; 134,618 UMIs | 54,262 x 75,851; 220,950 UMIs | 54,262 x 54,452; 187,641 UMIs |

All listed dimensions and UMI totals are identical on Pikachu and Bridges-2.
The integrated raw and filtered MEX matrices are also byte-identical. The
assignment-layer guide MEX files have host-dependent barcode column order, so
their raw byte hashes differ; sorted barcode-set hashes and barcode-keyed
`(barcode, feature row, count)` matrix hashes are identical for both captures.
See `outputs/PILOT_HOST_COMPARISON.json` and the two
`outputs/*_GUIDE_MEX_SEMANTICS.json` reports.

## Pre-Validation Attempt

The first Pikachu CP_R1 invocation on 2026-09-17 was stopped before validation
after confirming native gzip input, 250,000-read limiting on both arms, NXT
guide recognition, and automatic feature offset 30. Its guide staging directory
was named `guide`, which made the feature output leaf `guide/` instead of the
release convention `PolyIII/`. The unpublished work tree is retained at:

```text
/storage/MSK_Perturbseq06_Cardiac_pilot_control_20260917/attempts/
  CP_R1_preflight_guide_dir_20260917T1241Z/
```

The accepted scripts stage guide FASTQs under `fastqs/PolyIII`; no assignment
or filtering parameter changed.

A subsequent CP_R2 control attempt failed before feature reads were processed
because provider basenames beginning `CP_R2_` contain an extra `_R2_` token
before the terminal read-role token. Feature FASTQ discovery interpreted that
prefix as a read role. The accepted scripts stage only CP_R2 guide basenames
with the reversible prefix rewrite `CP_R2_` to `CPR2_` and emit
`STAGING_MAP.tsv`; source files and checksums remain unchanged.

The first Bridges submission (`build` job 46245961) failed before compilation
because Slurm copied the batch script to `/var/spool/slurm` and a
`BASH_SOURCE`-relative lookup could not find `common.sh`. No pilot task ran.
The accepted batch entrypoints use the fixed deployed provenance command path;
the failed submission JSON and Slurm logs are retained.

Two later build-only attempts also failed before any pilot task ran. Job
`46246203` found that Bridges lacks system HTSlib development headers; job
`46246652` then exposed duplicate BGZF reader symbols in the v1.9.4 portable
link. The accepted build job `46246773` uses the v1.9.4 bundled headers and
de-duplicates those integrated-link objects. All three failed submission JSON
records are retained under `outputs/bridges2_provenance/`.
