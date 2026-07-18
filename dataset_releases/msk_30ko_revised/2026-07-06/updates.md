# Updates

## 2026-07-18

- Added the missing release-level README for the June 2026 MSK 30polyKO v3
  dataset.
- Documented the FASTQ-to-H5AD workflow, cell-calling and adaptive-QC masks,
  all 27 `counts.h5ad` observation columns, feature-H5AD columns, sample
  mapping, and July correction overlay.
- Verified the schema and cell-mask counts against all nine current local
  release sources, using the corrected DE_XM counts object.
- Staged the README on Morphic Processing at:
  `/MSK-feature-h5ad-top-feature-repair-20260706/README.MSK_30POLYKO_REVISED_V3.md`
  (Globus task `ea1edfc9-82a1-11f1-9068-0ee7ef9370d9`, succeeded).
- Staged the same README with the immediate DE_XM correction at:
  `/MSK-KO-5-18-26-revised/corrected_release/processed/30_KO_DE_XM/README.MSK_30POLYKO_REVISED_V3.md`
  (Globus task `eae494f9-82a1-11f1-88b0-02ce27bde401`, succeeded).

## 2026-07-06

- Uploaded the feature-H5AD correction packet to Morphic Processing at
  `/MSK-feature-h5ad-top-feature-repair-20260706/processed/`.
- Consolidated the corrected DE_XM counts and counts-derived QC files into the
  same overlay, so one relative-path overlay contains all MSK 30KO repairs.
