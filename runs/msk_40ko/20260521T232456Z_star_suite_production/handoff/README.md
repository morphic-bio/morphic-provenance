# MSK 40KO Handoff

The 2026-05-22 Globus handoff found for this production run is the large BAM
upload to `/MSK-40KO-large-files`. One transfer task was used per sample:

- `40_KO_ES`: `3f3b77a8-5589-11f1-9dfe-02c81e62ebf9`, succeeded, 37,232,599,246 bytes.
- `40_KO_DE`: `7971397a-5592-11f1-bfea-02c81e62ebf9`, succeeded, 42,415,547,622 bytes.

Per-sample Globus batch files and final task JSON are preserved under
`handoff/samples/`. The upload inventory is `handoff/bam_upload_manifest.tsv`.

No standalone collaborator packet `provenance.md` was found for this 40KO
upload. This run record is therefore the canonical provenance record.
