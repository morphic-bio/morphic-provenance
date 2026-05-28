# MSK 30KO DE Old-Layout Packet Provenance

Generated UTC: 2026-05-26T16:41:27Z

This addendum documents the missing `30_KO_DE` old-layout packet added to the
existing MSK 30KO revised Globus delivery.

## Packet

- Local packet: `/mnt/pikachu/MSK_30_KO_revised/30_KO_DE`
- Globus destination: `/MSK-KO-5-18-26-revised/30_KO_DE`
- Transfer task: `a69c399b-591d-11f1-affc-0e9d40238285`
- Transfer completion: 2026-05-26T16:39:15Z

## Original Processing Folders

The complete DE production archive found for this repair is:

```text
/mnt/pikachu/msk30ko-production-sample-archive/MSK-05-13-26-large-files/DE
```

Important subfolders:

```text
run/
run/Solo.out/
run/cr_assign/
run/outs/
downstream_genefull_velocyto_cellbender/
downstream_genefull_velocyto_cellbender/cellbender/
downstream_genefull_velocyto_cellbender/feature_libraries/grna_de/
downstream_genefull_velocyto_cellbender/feature_libraries/larry_de/
staged_fastqs/
```

The older live production root checked for the original sample directory was:

```text
/storage/MSK-perturb-comparison/msk30ko_8sample_prod_20260513_231007/samples
```

The `DE` sample directory was not present there at repair time, so the packet
was built from the archived completed sample directory above.

## Files Used

| Packet path | Processing source |
| --- | --- |
| `30_KO_DE/counts.h5ad` | `downstream_genefull_velocyto_cellbender/final_counts.h5ad` |
| `30_KO_DE/QC/counts/gene_quantile_histogram.html` | `downstream_genefull_velocyto_cellbender/gene_quantile_histogram.html` |
| `30_KO_DE/QC/counts/gene_quantile_histogram.png` | `downstream_genefull_velocyto_cellbender/gene_quantile_histogram.png` |
| `30_KO_DE/features/gene/features.h5ad` | `downstream_genefull_velocyto_cellbender/feature_libraries/grna_de/raw_feature_library.h5ad` |
| `30_KO_DE/features/larry/features.h5ad` | `downstream_genefull_velocyto_cellbender/feature_libraries/larry_de/raw_feature_library.h5ad` |

Additional QC/provenance files available in the original processing archive,
but not copied into the old-layout packet because the neighboring old-layout
sample folders do not include them:

```text
downstream_genefull_velocyto_cellbender/adaptive_qc_threshold.json
downstream_genefull_velocyto_cellbender/adaptive_qc_threshold.json.pre_mt_adaptive
downstream_genefull_velocyto_cellbender/cellbender/cellbender_counts_report.html
run/outs/crispr_analysis/protospacer_umi_thresholds.json
```

## Local Audit Files

```text
/mnt/pikachu/STAR-suite/plans/artifacts/msk_30ko_de_old_layout_packet_20260526/README.txt
/mnt/pikachu/STAR-suite/plans/artifacts/msk_30ko_de_old_layout_packet_20260526/manifest.tsv
/mnt/pikachu/STAR-suite/plans/artifacts/msk_30ko_de_old_layout_packet_20260526/globus_batch.tsv
/mnt/pikachu/STAR-suite/plans/artifacts/msk_30ko_de_old_layout_packet_20260526/globus_task_id.txt
/mnt/pikachu/STAR-suite/plans/artifacts/msk_30ko_de_old_layout_packet_20260526/globus_task_final.txt
```
