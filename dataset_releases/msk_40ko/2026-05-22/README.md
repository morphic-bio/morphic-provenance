# MSK 40KO Globus Release 2026-05-22

## Summary

This release records the MSK 40KO large-BAM upload pushed to Globus on
2026-05-22 from the STAR-suite production run:

```text
runs/msk_40ko/20260521T232456Z_star_suite_production/
```

No standalone packet `provenance.md` was found for this upload. The run record
above and these release notes are the canonical provenance and release record.

## Globus Destination

```text
/MSK-40KO-large-files
```

Destination endpoint:

```text
61fb8b9a-9b52-456e-928c-30c0fb0140bf
```

Source endpoint:

```text
07446cad-33b8-11f0-8c0c-0afffb017b7d
```

## Upload Summary

Two Globus transfer tasks were found, one per sample BAM. Both succeeded on
2026-05-22 with checksum verification enabled.

- `40_KO_ES`: `3f3b77a8-5589-11f1-9dfe-02c81e62ebf9`, 37,232,599,246 bytes.
- `40_KO_DE`: `7971397a-5592-11f1-bfea-02c81e62ebf9`, 42,415,547,622 bytes.

Total uploaded BAM payload: 79,648,146,868 bytes.

See `upload_manifest.tsv` for per-task details.

## Recipe Documentation

The preserved production runbook is copied into the run record at:

```text
runs/msk_40ko/20260521T232456Z_star_suite_production/inputs/RUNBOOK_MSK_40KO_PRODUCTION.md
```

The maintained recipe script is in `morphic-recipes`:

```text
scripts/run_msk_40ko_pipeline_from_manifest.py
```

A single `run_all.sh` wrapper has not yet been mirrored for this production
set.

## Updates

Append release-specific additions and corrections in `updates.md`.
