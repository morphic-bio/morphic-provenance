# Morphic Provenance Agent Guide

This repo is for run provenance, not source code or analysis development.

## Rules

- Do not commit large payloads such as h5ad, h5, h5mu, BAM, FASTQ, Matrix
  Market matrices, or bulky logs.
- Commit manifests, checksums, rendered commands, environment summaries,
  package locks, image digests, and small handoff summaries.
- Treat completed run folders as append-only.
- Corrections must be explicit and timestamped.
- Every CellBender production/handoff record must state whether CUDA was used;
  production CellBender without CUDA is a failed/mislaunched run.

## Run Folder

Use `templates/run/` as the starting point for each new run:

```text
runs/<project>/<run_id>/
  README.md
  run.json
  inputs/
  commands/
  environment/
  outputs/
  logs/
  handoff/
```

Large logs can live outside git, but record their path, bytes, checksum, and
retention policy.

## Compose-up: recipes referenced by these runs (TODO)

Provenance is the **oracle for parameter values**. A complementary contract —
**compose-up** — governs *which output layers* a recipe emits: start from a
minimal functional core and add only the layers a target needs, rather than
running a maximal recipe blindly (see `morphic-recipes/AGENTS.md` "Compose to the
target" and `STAR-suite`/`Chromap-suite` `mcp_server/workflows/AUTHORING.md`).

The multiome recipe (`run_star_multiome_lane_smoke.sh` / `run_multiome_minimal.sh`)
now implements this. **TODO:** the recipes behind the other runs here
(`jax_scrnaseq01`, `jax_scrnaseq02`, `msk_30ko_revised`, `msk_40ko`,
`nw_atac_seq_libmacs3`, `slam_seq_pe`) emit similar optional supersets (Velocyto,
CellBender/remote downstream, extra BAMs) and should be reviewed and retrofitted
the same way. Tracked in `morphic-recipes/AGENTS.md` "Compose-up retrofit backlog".
Retrofits must not change the recorded parameter values — only make the optional
output layers explicit and composable.
