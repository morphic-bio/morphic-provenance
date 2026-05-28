# Handoff

The production tree includes a `provenance.md` file that was later split out
from the collaborator README. It is preserved here as
`temporary_packet_provenance.md`; this run folder is the canonical provenance
record.

Globus destination:

```text
/SLAM-seq-PE-results/prod_full_20260511T103908Z/
```

Recorded completed upload tasks:

- `0c11644c-4e33-11f1-a502-0afffe4617ab`: remaining results upload,
  `SUCCEEDED`, 8,421 files, 9,530,222,552 bytes.
- `8dd10a29-5025-11f1-b61f-0ea3589134b3`: DESeq2 results upload,
  `SUCCEEDED`, 2,202 files, 1,762,703,149 bytes.
- `e2facbfe-5025-11f1-b5c2-02535127e3d7`: DESeq2 upload metadata,
  `SUCCEEDED`, 3 files, 797,725 bytes.

Per-sample large-output task IDs are preserved in
`per_sample_globus_tasks.tsv`; the source provenance reports 290
`TRANSFER_CLEANED.ok` markers.
