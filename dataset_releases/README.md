# Dataset Release Notes

This directory tracks collaborator-facing dataset deliveries by project and
Globus analysis push date.

Release notes answer a different question than run records:

- Run records under `runs/` document exactly what ran.
- Dataset release notes document what was uploaded, where it went, and what
  release-specific updates or corrections were made after the upload.

Use this layout:

```text
dataset_releases/<project>/<YYYY-MM-DD>/
  README.md
  upload_manifest.tsv
  updates.md
```

The date key should be the date the analysis packet was pushed to Globus. If
supporting large-file transfers complete later, keep them in the same release
and state their final completion dates in the release README and manifest.

## Date And Update Policy

- Use the first successful Globus push date for the analysis packet as
  `<YYYY-MM-DD>`.
- Do not create a new dated release merely because a README, validation note,
  checksum, or correction explanation was added later. Add a dated entry to
  the existing `updates.md` instead.
- Create a new dated release when a distinct analysis packet is pushed. If the
  packet is a correction overlay, say which base release it updates and list
  the relative paths it replaces.
- When one Globus packet contains multiple projects, keep each project's
  release note scoped to that project and include only that project's rows in
  its `upload_manifest.tsv`.

## Required Contents

### `README.md`

Include:

- dataset/release name and the exact Globus endpoint and path;
- whether the packet is complete or is an overlay on an earlier release;
- sample/folder mapping and the release-facing directory layout;
- processing summary from source inputs through released products;
- recommended filtering/cell-selection semantics;
- an H5AD data dictionary covering every released `obs` field and the relevant
  `X`, `layers`, `var`, `obsm`, and `uns` contents;
- corrections, known limitations, and intentionally omitted information; and
- links to canonical run records that are already tracked in this repository.

Do not point collaborators to a patch note when they need the dataset-level
workflow or schema. Patch notes supplement the release README; they do not
replace it.

### `upload_manifest.tsv`

Inventory the analysis files uploaded for this project. At minimum record the
relative or destination path, byte size, checksum when available, and Globus
destination. Record transfer task IDs/status either per row or in the README
when one task covers the whole manifest. Documentation-only uploads may be
recorded in `updates.md`, but must not be the only rows in the packet manifest.

### `updates.md`

Append timestamped entries for documentation additions, transfer completion,
validation, corrections, supersession, and changes in interpretation. Do not
rewrite older entries to make later activity appear part of the original push.

## Pre-Push Check

Before publishing release documentation:

1. Confirm the directory date against the analysis packet's Globus task.
2. Confirm the manifest inventories the packet and is scoped to the project.
3. Confirm every repository provenance path is tracked on the target branch.
4. Run `git diff --check` and review the staged file list.
5. Commit only the intended release/provenance records; use a clean worktree if
   the primary checkout has unrelated changes.
