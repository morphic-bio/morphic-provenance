#!/usr/bin/env python3
"""Validate one Cardiac GEX/guide integration pilot capture."""

from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--tru-whitelist", required=True, type=Path)
    parser.add_argument("--capture", required=True)
    parser.add_argument("--guide-library-id", required=True)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def line_count(path: Path) -> int:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt") as handle:
        return sum(1 for _ in handle)


def read_barcodes(path: Path) -> list[str]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt") as handle:
        return [line.strip().removesuffix("-1") for line in handle if line.strip()]


def missing_from_whitelist(barcodes: list[str], whitelist: Path) -> list[str]:
    missing = set(barcodes)
    with whitelist.open() as handle:
        for line in handle:
            missing.discard(line.strip())
            if not missing:
                break
    return sorted(missing)


def nxt_to_tru(barcode: str) -> str:
    complement = str.maketrans("ACGT", "TGCA")
    if len(barcode) < 9:
        return barcode
    return barcode[:7] + barcode[7:9].translate(complement) + barcode[9:]


def matrix_dimensions_and_sum(path: Path) -> tuple[tuple[int, int, int], int]:
    opener = gzip.open if path.suffix == ".gz" else open
    dimensions = None
    total = 0
    with opener(path, "rt") as handle:
        for line in handle:
            if line.startswith("%"):
                continue
            fields = line.split()
            if dimensions is None:
                if len(fields) != 3:
                    raise ValueError(f"invalid Matrix Market dimensions in {path}")
                dimensions = tuple(int(value) for value in fields)
            else:
                total += int(float(fields[2]))
    if dimensions is None:
        raise ValueError(f"no Matrix Market dimensions in {path}")
    return dimensions, total


def main() -> int:
    args = parse_args()
    run_dir = args.run_dir.resolve()
    if "zshard" in str(run_dir):
        raise ValueError(f"zshard path is forbidden: {run_dir}")

    log_final = run_dir / "Log.final.out"
    gene_raw = run_dir / "Solo.out/GeneFull/raw"
    gene_filtered = run_dir / "Solo.out/GeneFull/filtered"
    guide = run_dir / f"cr_assign/CRISPR_Guide_Capture/{args.guide_library_id}/PolyIII"
    combined_raw = run_dir / "outs/raw_feature_bc_matrix"
    combined_filtered = run_dir / "outs/filtered_feature_bc_matrix"

    required = [
        log_final,
        gene_raw / "matrix.mtx",
        gene_raw / "barcodes.tsv",
        gene_raw / "features.tsv",
        gene_filtered / "matrix.mtx",
        gene_filtered / "barcodes.tsv",
        gene_filtered / "features.tsv",
        guide / "matrix.mtx",
        guide / "barcodes.tsv",
        guide / "features.tsv",
        combined_raw / "matrix.mtx.gz",
        combined_raw / "barcodes.tsv.gz",
        combined_raw / "features.tsv.gz",
        combined_filtered / "matrix.mtx.gz",
        combined_filtered / "barcodes.tsv.gz",
        combined_filtered / "features.tsv.gz",
    ]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise ValueError(f"missing pilot outputs: {missing}")

    guide_features = line_count(guide / "features.tsv")
    if guide_features != 15656:
        raise ValueError(f"expected 15,656 guide features, found {guide_features}")

    raw_gene_dims, raw_gene_umis = matrix_dimensions_and_sum(gene_raw / "matrix.mtx")
    filtered_gene_dims, filtered_gene_umis = matrix_dimensions_and_sum(gene_filtered / "matrix.mtx")
    guide_dims, guide_umis = matrix_dimensions_and_sum(guide / "matrix.mtx")
    combined_raw_dims, combined_raw_umis = matrix_dimensions_and_sum(
        combined_raw / "matrix.mtx.gz"
    )
    combined_filtered_dims, combined_filtered_umis = matrix_dimensions_and_sum(
        combined_filtered / "matrix.mtx.gz"
    )
    if raw_gene_dims[0] != 38606 or filtered_gene_dims[0] != 38606:
        raise ValueError(
            f"wrong GEX feature universe: raw={raw_gene_dims[0]} filtered={filtered_gene_dims[0]}"
        )
    if filtered_gene_dims[1] == 0:
        raise ValueError("pilot produced no filtered GEX cells")
    if guide_dims[0] != 15656 or guide_umis <= 0:
        raise ValueError(f"guide assignment failed: dimensions={guide_dims}, UMI sum={guide_umis}")
    expected_combined_features = 38606 + 15656
    if combined_raw_dims[0] != expected_combined_features:
        raise ValueError(f"wrong combined raw feature universe: {combined_raw_dims[0]}")
    if combined_filtered_dims[0] != expected_combined_features:
        raise ValueError(f"wrong combined filtered feature universe: {combined_filtered_dims[0]}")

    guide_barcodes = read_barcodes(guide / "barcodes.tsv")
    combined_raw_barcodes = read_barcodes(combined_raw / "barcodes.tsv.gz")
    combined_filtered_barcodes = read_barcodes(combined_filtered / "barcodes.tsv.gz")
    if len(guide_barcodes) != guide_dims[1]:
        raise ValueError("guide barcode count does not match matrix dimensions")
    if len(combined_raw_barcodes) != combined_raw_dims[1]:
        raise ValueError("combined raw barcode count does not match matrix dimensions")
    if len(combined_filtered_barcodes) != combined_filtered_dims[1]:
        raise ValueError("combined filtered barcode count does not match matrix dimensions")

    nxt_whitelist = Path(str(args.tru_whitelist).replace("_TRU.txt", "_NXT.txt"))
    if not nxt_whitelist.is_file():
        raise ValueError(f"paired NXT whitelist not found: {nxt_whitelist}")
    invalid_assignment = missing_from_whitelist(guide_barcodes, nxt_whitelist)
    if invalid_assignment:
        raise ValueError(
            f"assignment-layer guide MEX contains non-NXT barcodes: {invalid_assignment[:10]}"
        )
    invalid_combined = missing_from_whitelist(
        combined_raw_barcodes + combined_filtered_barcodes, args.tru_whitelist
    )
    if invalid_combined:
        raise ValueError(f"combined MEX contains non-TRU barcodes: {invalid_combined[:10]}")

    translated_guide_barcodes = {nxt_to_tru(barcode) for barcode in guide_barcodes}
    translated_overlap = len(translated_guide_barcodes.intersection(combined_raw_barcodes))
    if translated_overlap == 0:
        raise ValueError("NXT-to-TRU guide barcodes do not overlap the combined raw MEX")

    report = {
        "status": "PASS",
        "run_dir": str(run_dir),
        "reference": "GRCh38-2024-A/Gencode-v44 MSK-30 index",
        "star_suite_version": "1.9.4",
        "star_suite_commit": "1c9ddb9a5a2a3e62748e8e4ef28e553582affeed",
        "pilot_capture": args.capture,
        "read_limit": 250000,
        "gex_input_namespace": "TRU",
        "guide_input_namespace": "NXT",
        "canonical_output_namespace": "TRU",
        "raw_gene_dimensions": raw_gene_dims,
        "raw_gene_umi_sum": raw_gene_umis,
        "filtered_gene_dimensions": filtered_gene_dims,
        "filtered_gene_umi_sum": filtered_gene_umis,
        "guide_dimensions": guide_dims,
        "guide_umi_sum": guide_umis,
        "guide_features": guide_features,
        "guide_barcodes_checked": len(guide_barcodes),
        "guide_assignment_namespace": "NXT",
        "combined_raw_dimensions": combined_raw_dims,
        "combined_raw_umi_sum": combined_raw_umis,
        "combined_filtered_dimensions": combined_filtered_dims,
        "combined_filtered_umi_sum": combined_filtered_umis,
        "combined_raw_barcodes_checked": len(combined_raw_barcodes),
        "combined_filtered_barcodes_checked": len(combined_filtered_barcodes),
        "translated_guide_overlap_combined_raw": translated_overlap,
        "combined_output_namespace": "TRU",
        "gzip_policy": "native gzip, no transcode",
        "zshard_used": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
