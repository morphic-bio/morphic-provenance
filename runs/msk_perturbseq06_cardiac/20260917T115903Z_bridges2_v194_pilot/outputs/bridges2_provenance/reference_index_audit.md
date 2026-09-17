# Reference Index Audit

Date: 2026-09-17

## Finding

The pre-existing Ocean index at
`/ocean/projects/bio230034p/shared/processing/genome` is a coherent
GRCh38 2020-A-style index. It is not corrupt, but it is not the annotation
vintage used for MSK-30 and current PPARG controls.

| Property | Existing Ocean index | Required MSK-30 index |
| --- | ---: | ---: |
| Annotation vintage | 2020-A style | 2024-A / GENCODE v44 |
| Genes | 36,601 | 38,606 |
| Transcripts | 199,138 | 226,005 |
| GTF splice-junction rows | 362,172 | 386,504 |
| `Genome` bytes | 3,211,173,485 | 3,216,071,051 |
| `SA` bytes | 24,900,747,856 | 24,940,951,756 |

Both indexes contain 194 chromosomes. `chrName.txt`, `chrLength.txt`,
`chrNameLength.txt`, and `chrStart.txt` are byte-identical, so the mismatch is
annotation content rather than chromosome assembly or naming.

Gene-ID comparison found 36,300 shared genes, 2,306 genes present only in the
2024-A index, and 301 genes present only in the 2020-A index. Transcript-ID
comparison found 195,210 shared, 30,795 2024-A-only, and 3,928 2020-A-only
transcripts. Those coherent release-level changes argue against a truncated or
malformed index.

## Prior Use

- CAT-ATAC used a 2020-A index intentionally to match its Cell Ranger ARC
  2020-A comparator.
- Archived MSK-30 rendered commands use
  `/storage/autoindex_110_44/bulk_index` (2024-A).
- Current PPARG benchmark commands use that same 2024-A index.

## Decision

Use the exact MSK-30 2024-A index for Cardiac. The older Ocean index explains
why a valid index was present but must be rejected for this workflow because it
would change the gene universe and break comparability.

The required non-zshard Ocean path is:

```text
/ocean/projects/bio230034p/shared/processing/references/
  GRCh38-2024-A-star-msk30/
```
