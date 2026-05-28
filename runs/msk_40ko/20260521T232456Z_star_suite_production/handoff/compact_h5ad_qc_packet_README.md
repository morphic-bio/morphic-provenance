# MSK 40KO h5ad and QC Globus packet

This packet mirrors the compact MSK 30KO revised Globus layout:

```text
MSK_40_KO_revised/<sample>/counts.h5ad
MSK_40_KO_revised/<sample>/QC/counts/gene_quantile_histogram.html
MSK_40_KO_revised/<sample>/QC/counts/gene_quantile_histogram.png
MSK_40_KO_revised/<sample>/features/gene/features.h5ad
MSK_40_KO_revised/<sample>/features/larry/features.h5ad
```

Samples included:

| Sample | Files | Bytes |
| --- | ---: | ---: |
| 40_KO_DE | 5 | 10586966785 |
| 40_KO_ES | 5 | 9132178324 |
| PROJECT | 6 | 18880 |

Primary AnnData files are `counts.h5ad`, hard-linked from the STAR-suite downstream `final_counts.h5ad` outputs. Feature files are included and are hard-linked from the raw guide and LARRY feature-library h5ads.

Intentional exclusions: source FASTQs, BAM files, raw MEX matrices, CellBender raw `.h5` payloads/checkpoints/posteriors, and temporary runtime caches/logs.

See `STAGED_MANIFEST.tsv` for source paths and byte counts. See `SHA256SUMS.tsv` for checksums.

Created: 2026-05-28T18:27:08Z
