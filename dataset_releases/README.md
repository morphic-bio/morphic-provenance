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
