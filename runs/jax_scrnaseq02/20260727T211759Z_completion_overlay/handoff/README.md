# Handoff

This handoff is an additive completion overlay for:

```text
/JAX_scRNAseq02_processed/JAX-scRNAseq02-5-22-26
```

The overlay destination is:

```text
/JAX_scRNAseq02_processed/JAX-scRNAseq02-5-22-26-completion-7-27-26
```

It contains 12 new sample directories and replaces no existing paths. The
overlay is not standalone; merge its sample directories at the root of the
10-sample base release to obtain all 22 expected samples.

The transfer submitted 210 files under Globus task
`6d5e713a-8a01-11f1-881a-02ce27bde401`, with checksum synchronization and
destination checksum verification enabled.

Final transfer status: `SUCCEEDED` at `2026-07-27T22:04:41Z`.

A recursive destination listing confirmed 210 files totaling 54,830,077,298
bytes. The root contained the 12 expected sample directories and six packet
metadata files.

`packet_README.md` is the README delivered with the packet.
`globus_batch.tsv` is the exact transfer batch.
`globus_task_submit.json` and `globus_task_final.json` preserve the submission
and final task records.
