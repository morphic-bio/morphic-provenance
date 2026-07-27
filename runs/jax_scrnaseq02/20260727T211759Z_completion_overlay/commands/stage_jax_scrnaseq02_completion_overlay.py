#!/usr/bin/env python3
"""Stage the 12-sample JAX scRNAseq02 completion overlay using hard links."""

from __future__ import annotations

import csv
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path


GENERATED_UTC = "2026-07-27T21:17:59Z"
DATASET = "JAX scRNAseq02"
PACKET_NAME = "JAX-scRNAseq02-5-22-26-completion-7-27-26"
PRODUCTION_ROOT = Path(
    "/mnt/pikachu/JAX_scRNAseq02_processed/"
    "ocm_prod_batch_flex_native_yremove_trace_20260521T034223Z"
)
PACKET_ROOT = Path("/mnt/pikachu/JAX_scRNAseq02_handoff") / PACKET_NAME
BASE_GLOBUS_ROOT = "/JAX_scRNAseq02_processed/JAX-scRNAseq02-5-22-26"
DESTINATION_ROOT = f"/JAX_scRNAseq02_processed/{PACKET_NAME}"

SAMPLES = {
    "25E34-L4": [
        "EPAS1-Day-5",
        "ISL1-Day-5",
        "WT-ExM-Day-5",
        "WT-PrS-3pct-Day-5",
    ],
    "25E35-L3": [
        "GCM1-Day-6",
        "GRHL1-Day-6",
        "OVOL1-Day-6",
        "WT-PrS-20pct-Day-6",
    ],
    "25E35-L4": [
        "EPAS1-Day-6",
        "ISL1-Day-6",
        "WT-ExM-Day-6",
        "WT-PrS-3pct-Day-6",
    ],
}

PAYLOAD_FILES = [
    "adaptive_qc_threshold.json",
    "cellbender/cellbender_counts.log",
    "cellbender/cellbender_counts.pdf",
    "cellbender/cellbender_counts_cell_barcodes.csv",
    "cellbender/cellbender_counts_metrics.csv",
    "cellbender/cellbender_counts_report.html",
    "counts.h5ad",
    "default_singlet_filtered_counts.h5ad",
    "doublet_barcodes.txt",
    "filtered_barcodes_with_scores.txt",
    "filtered_counts.h5ad",
    "final_counts.h5ad",
    "gene_quantile_histogram.html",
    "gene_quantile_histogram.png",
    "non_empty_barcodes.txt",
    "summary.txt",
    "unfiltered_counts.h5ad",
]

MANIFEST_COLUMNS = [
    "dataset",
    "sample",
    "relative_path",
    "bytes",
    "source",
    "source_mtime_utc",
    "destination",
]


def utc_mtime(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(16 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_tsv(path: Path, columns: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=columns, delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    if PACKET_ROOT.exists():
        raise SystemExit(f"Refusing to overwrite existing packet: {PACKET_ROOT}")

    PACKET_ROOT.mkdir(parents=True)
    payload_rows: list[dict[str, object]] = []
    summary_rows: list[dict[str, object]] = []

    for library_id, sample_names in SAMPLES.items():
        for sample in sample_names:
            source_dir = (
                PRODUCTION_ROOT
                / library_id
                / "samples"
                / sample
                / "downstream_genefull_velocyto_cellbender_remote"
            )
            staged_dir = (
                PACKET_ROOT / sample / "downstream_genefull_velocyto_cellbender"
            )
            sample_bytes = 0

            for payload_rel in PAYLOAD_FILES:
                source = source_dir / payload_rel
                if not source.is_file():
                    raise FileNotFoundError(source)

                staged = staged_dir / payload_rel
                staged.parent.mkdir(parents=True, exist_ok=True)
                os.link(source, staged)

                source_stat = source.stat()
                staged_stat = staged.stat()
                if (source_stat.st_dev, source_stat.st_ino) != (
                    staged_stat.st_dev,
                    staged_stat.st_ino,
                ):
                    raise RuntimeError(f"Staged file is not a hard link: {staged}")

                relative_path = str(staged.relative_to(PACKET_ROOT))
                sample_bytes += source_stat.st_size
                payload_rows.append(
                    {
                        "dataset": DATASET,
                        "sample": sample,
                        "relative_path": relative_path,
                        "bytes": source_stat.st_size,
                        "source": str(source),
                        "source_mtime_utc": utc_mtime(source),
                        "destination": f"{DESTINATION_ROOT}/{relative_path}",
                    }
                )

            summary_rows.append(
                {
                    "library_id": library_id,
                    "sample": sample,
                    "file_count": len(PAYLOAD_FILES),
                    "bytes": sample_bytes,
                }
            )

    expected_payloads = len(PAYLOAD_FILES) * sum(map(len, SAMPLES.values()))
    if len(payload_rows) != expected_payloads:
        raise RuntimeError(
            f"Expected {expected_payloads} payloads, staged {len(payload_rows)}"
        )

    payload_bytes = sum(int(row["bytes"]) for row in payload_rows)
    write_tsv(PACKET_ROOT / "MANIFEST.tsv", MANIFEST_COLUMNS, payload_rows)
    write_tsv(
        PACKET_ROOT / "sample_summary.tsv",
        ["library_id", "sample", "file_count", "bytes"],
        summary_rows,
    )

    sample_table = "\n".join(
        f"| `{row['library_id']}` | `{row['sample']}` | {row['file_count']} | "
        f"{int(row['bytes']):,} |"
        for row in summary_rows
    )
    readme = f"""# JAX scRNAseq02 completion overlay

Generated UTC: `{GENERATED_UTC}`

## Scope

This is an additive completion overlay for the original JAX scRNAseq02 packet:

```text
{BASE_GLOBUS_ROOT}
```

The original packet was built while production was still running and contained
10 of 22 expected samples. This overlay contains the remaining 12 completed
samples from library preparations `25E34-L4`, `25E35-L3`, and `25E35-L4`.
Together, the base packet and this overlay provide all 22 expected samples.

This overlay is not a standalone copy of the original 10 samples. To construct
one complete local tree, copy or merge the 12 sample directories from this
overlay into the root of the base packet. No existing relative paths are
replaced.

Destination:

```text
{DESTINATION_ROOT}
```

Source production run:

```text
{PRODUCTION_ROOT}
```

## Packet summary

- Samples: 12
- Payload files: {len(payload_rows)}
- Payload bytes: {payload_bytes}
- Feature files: excluded, matching the original packet
- CellBender: GPU/CUDA production outputs

| Library preparation | Sample | Files | Bytes |
|---|---|---:|---:|
{sample_table}

## Directory layout

```text
<sample>/downstream_genefull_velocyto_cellbender/
```

Each sample contains the same 17-file selection as the original packet:

- five H5AD deliverables;
- adaptive QC metadata and gene-QC plots;
- CellBender report, log, metrics, PDF, and called-barcode CSV;
- barcode filtering/doublet lists; and
- `summary.txt`.

Excluded by design: raw CellBender H5 payloads, checkpoints, matplotlib font
caches, FASTQs, BAMs, raw Matrix Market matrices, and feature files.

## Recommended cell selection

For analysis, use `default_singlet_filtered_counts.h5ad`. Equivalently, subset
`unfiltered_counts.h5ad` or `final_counts.h5ad` where
`obs["singlet_filtered"] == True`. This mask combines the singlet call with the
adaptive gene-complexity and mitochondrial-percentage QC mask.

`filtered_counts.h5ad` contains QC-passing cells before doublet exclusion.
`counts.h5ad` is the preliminary full-barcode matrix with the STAR cell-call
and basic filter fields. `unfiltered_counts.h5ad` and `final_counts.h5ad`
retain the full barcode space and all QC annotations.

## H5AD data dictionary

### Matrices and layers

- `X`: CSR sparse `float32` STAR GeneFull counts, including exonic and intronic
  reads assigned to gene bodies.
- `layers["denoised"]`: sparse CellBender ambient-RNA-corrected counts.
- `layers["spliced"]`, `layers["unspliced"]`, and `layers["ambiguous"]`:
  present for schema compatibility but all-zero in all 60 H5AD files in this
  overlay; do not use these layers for velocity analysis.
- `obsm`, `varm`, and `obsp`: intentionally empty.

### `obs`

`counts.h5ad` contains only `is_cell` and `filter`. The other four H5AD files
contain all fields below.

| Field | Type | Meaning |
|---|---|---|
| `is_cell` | bool | STAR EmptyDrops_CR cell call. |
| `filter` | bool | Passes adaptive gene-count and mitochondrial-percentage QC. |
| `non_empty` | int64 | Non-empty-barcode indicator from STAR. |
| `doublet` | int64 | scDblFinder prediction: 1 doublet, 0 singlet. |
| `doublet_scores` | float64 | scDblFinder doublet score. |
| `singlet` | bool | Cell call excluding predicted doublets. |
| `n_genes` | int64 | Number of detected genes. |
| `mt_counts` | float32 | Mitochondrial UMI count. |
| `total_counts` | float32 | Total GeneFull UMI count. |
| `mt_pct` | float32 | Mitochondrial UMI percentage. |
| `singlet_filtered` | bool | Recommended usable-cell mask: `singlet & filter`. |
| `filter_strict_mt5` | bool | Legacy strict-5% mitochondrial QC mask. |
| `singlet_filtered_strict_mt5` | bool | Legacy strict-5% singlet/QC mask. |

The observation index is the cell barcode.

### `var`

| Field | Type | Meaning |
|---|---|---|
| `gene_symbols` | category | Gene symbol. |
| `feature_types` | category | `Gene Expression`. |

The variable index is the Ensembl gene identifier.

### `uns`

- `gene_expression_feature_kind`: gene-expression feature identifier.
- `gene_expression_source`: source gene-expression matrix.
- `velocyto_source`: recorded source Velocyto matrix.
- `mt_adaptive_filter`: per-sample adaptive QC settings; absent only from the
  preliminary `counts.h5ad`.

## Packet files

- `MANIFEST.tsv`: payload inventory with source and destination paths.
- `sample_summary.tsv`: per-library/per-sample file and byte counts.
- `PROVENANCE.tsv`: payload plus packet-metadata provenance.
- `PROVENANCE.md`: packet-level provenance summary.
- `SHA256SUMS.tsv`: checksums for payload and packet metadata files.
- `globus_batch.tsv`: submitted source-to-destination transfer pairs.

Canonical run and release documentation is maintained in
`morphic-bio/morphic-provenance`.
"""
    (PACKET_ROOT / "README.md").write_text(readme, encoding="utf-8")

    provenance_document = {
        "dataset": DATASET,
        "generated_utc": GENERATED_UTC,
        "packet_kind": "additive_completion_overlay",
        "base_globus_root": BASE_GLOBUS_ROOT,
        "destination_root": DESTINATION_ROOT,
        "source_run_root": str(PRODUCTION_ROOT),
        "packet_root": str(PACKET_ROOT),
        "libraries": list(SAMPLES),
        "samples": [row["sample"] for row in summary_rows],
        "payload_files": len(payload_rows),
        "payload_bytes": payload_bytes,
        "feature_files": "excluded",
        "cellbender_cuda": True,
        "source_endpoint": "07446cad-33b8-11f0-8c0c-0afffb017b7d",
        "destination_endpoint": "61fb8b9a-9b52-456e-928c-30c0fb0140bf",
    }
    provenance_md = """# Packet provenance

This file is packet-local handoff context. The canonical record is the
corresponding run and dataset release in `morphic-bio/morphic-provenance`.

```json
""" + json.dumps(provenance_document, indent=2, sort_keys=True) + """
```
"""
    (PACKET_ROOT / "PROVENANCE.md").write_text(
        provenance_md, encoding="utf-8"
    )

    metadata_names = [
        "README.md",
        "MANIFEST.tsv",
        "sample_summary.tsv",
        "PROVENANCE.md",
    ]
    provenance_rows = list(payload_rows)
    for name in metadata_names:
        path = PACKET_ROOT / name
        provenance_rows.append(
            {
                "dataset": DATASET,
                "sample": "",
                "relative_path": name,
                "bytes": path.stat().st_size,
                "source": str(path),
                "source_mtime_utc": utc_mtime(path),
                "destination": f"{DESTINATION_ROOT}/{name}",
            }
        )
    write_tsv(PACKET_ROOT / "PROVENANCE.tsv", MANIFEST_COLUMNS, provenance_rows)

    checksum_names = [
        str(row["relative_path"]) for row in payload_rows
    ] + metadata_names + ["PROVENANCE.tsv"]
    checksum_rows: list[dict[str, object]] = []
    for relative_path in checksum_names:
        path = PACKET_ROOT / relative_path
        checksum_rows.append(
            {
                "relative_path": relative_path,
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        )
    write_tsv(
        PACKET_ROOT / "SHA256SUMS.tsv",
        ["relative_path", "bytes", "sha256"],
        checksum_rows,
    )

    transfer_names = checksum_names + ["SHA256SUMS.tsv"]
    with (PACKET_ROOT / "globus_batch.tsv").open("w", encoding="utf-8") as handle:
        for relative_path in transfer_names:
            handle.write(
                f"{PACKET_ROOT / relative_path} "
                f"{DESTINATION_ROOT}/{relative_path}\n"
            )

    build_summary = {
        **provenance_document,
        "transferred_files_planned": len(transfer_names),
        "sha256_rows": len(checksum_rows),
    }
    print(json.dumps(build_summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
