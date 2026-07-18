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

## Dataset Release Documentation

- Follow `dataset_releases/README.md` for every collaborator-facing delivery.
- Key `dataset_releases/<project>/<YYYY-MM-DD>/` by the date the analysis
  packet was first pushed to Globus, not the date its documentation was added.
- Record later documentation, validation, and correction-overlay activity in
  that release's `updates.md`. Create a new date only for a newly pushed
  analysis packet.
- Every release directory must contain `README.md`, `upload_manifest.tsv`, and
  `updates.md`. The manifest must inventory the analysis packet, not only its
  README or other documentation files.
- Link only to run records and repository paths that are tracked on the branch
  being published. Never describe an untracked local path as canonical
  repository provenance.
- A replacement overlay must identify its base release, exact Globus path,
  replacement-relative paths, scope, and transfer task/status. State whether
  it is a complete packet or must be applied over a base release.
- H5AD release documentation must define the recommended cell-selection mask
  and every released `obs` field. Also describe relevant `X`, `layers`, `var`,
  `obsm`, and `uns` contents, including fields intentionally omitted.
- Before pushing, run `git diff --check`, verify release dates and repository
  links, and stage only the intended release/provenance files. Use a clean
  worktree when the main checkout contains unrelated work.

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
