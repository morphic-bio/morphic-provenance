#!/usr/bin/env python3
"""Validate the complete MSK Perturb-seq 06 Cardiac upstream production set."""

from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path


CAPTURES = ("CP_A1", "CP_A2", "CP_A3", "CP_B1", "CP_B2", "CP_B3", "CP_R1", "CP_R2")
EXPECTED_GEX_FEATURES = 38606
EXPECTED_GUIDE_FEATURES = 15656


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--production-root", required=True, type=Path)
    parser.add_argument("--tru-whitelist", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def open_text(path: Path):
    return gzip.open(path, "rt") if path.suffix == ".gz" else path.open()


def line_count(path: Path) -> int:
    with open_text(path) as handle:
        return sum(1 for _ in handle)


def read_barcodes(path: Path) -> list[str]:
    with open_text(path) as handle:
        return [line.strip().removesuffix("-1") for line in handle if line.strip()]


def read_whitelist(path: Path) -> set[str]:
    with path.open() as handle:
        return {line.strip() for line in handle if line.strip()}


def matrix_dimensions(path: Path) -> tuple[int, int, int]:
    with open_text(path) as handle:
        for line in handle:
            if line.startswith("%"):
                continue
            fields = line.split()
            if len(fields) != 3:
                raise ValueError(f"invalid Matrix Market dimensions in {path}")
            return tuple(int(value) for value in fields)
    raise ValueError(f"no Matrix Market dimensions in {path}")


def nxt_to_tru(barcode: str) -> str:
    if len(barcode) < 9:
        return barcode
    complement = str.maketrans("ACGT", "TGCA")
    return barcode[:7] + barcode[7:9].translate(complement) + barcode[9:]


def require_files(paths: list[Path]) -> None:
    missing = [str(path) for path in paths if not path.is_file() or path.stat().st_size == 0]
    if missing:
        raise ValueError(f"missing or empty production outputs: {missing}")


def validate_capture(
    root: Path,
    capture: str,
    tru_whitelist: set[str],
    nxt_whitelist: set[str],
) -> dict[str, object]:
    capture_root = root / capture
    run_dir = capture_root / "run"
    gene_raw = run_dir / "Solo.out/GeneFull/raw"
    gene_filtered = run_dir / "Solo.out/GeneFull/filtered"
    velocity_filtered = run_dir / "Solo.out/Velocyto/filtered"
    guide_id = f"grna_{capture.lower()}"
    guide = run_dir / f"cr_assign/CRISPR_Guide_Capture/{guide_id}/PolyIII"
    combined_raw = run_dir / "outs/raw_feature_bc_matrix"
    combined_filtered = run_dir / "outs/filtered_feature_bc_matrix"

    required = [
        capture_root / "UPSTREAM_COMPLETE.txt",
        capture_root / "RUN_COMMAND.sh",
        capture_root / "stage.tsv",
        capture_root / "time.txt",
        run_dir / "Log.final.out",
        run_dir / "Aligned.out.bam",
        gene_raw / "matrix.mtx",
        gene_raw / "barcodes.tsv",
        gene_raw / "features.tsv",
        gene_filtered / "matrix.mtx",
        gene_filtered / "barcodes.tsv",
        gene_filtered / "features.tsv",
        velocity_filtered / "spliced.mtx",
        velocity_filtered / "unspliced.mtx",
        velocity_filtered / "ambiguous.mtx",
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
    require_files(required)

    completion = (capture_root / "UPSTREAM_COMPLETE.txt").read_text()
    if "status=COMPLETE" not in completion or f"capture={capture}" not in completion:
        raise ValueError(f"invalid completion marker for {capture}")
    command = (capture_root / "RUN_COMMAND.sh").read_text()
    for required_arg in (
        "--readFilesBgzfMode auto",
        "--soloFeatures GeneFull Velocyto",
        "--crChemistry auto",
        "--crOutputChemistry TRU",
        "--dynamicThreadInterface 1",
        "--crAssignConsumerThreads -1",
        "--crAssignSearchThreads 1",
    ):
        if required_arg not in command:
            raise ValueError(f"{capture} command is missing {required_arg}")
    if "zshard" in command:
        raise ValueError(f"{capture} command contains a forbidden zshard path")

    raw_gene_dims = matrix_dimensions(gene_raw / "matrix.mtx")
    filtered_gene_dims = matrix_dimensions(gene_filtered / "matrix.mtx")
    velocity_dims = {
        layer: matrix_dimensions(velocity_filtered / f"{layer}.mtx")
        for layer in ("spliced", "unspliced", "ambiguous")
    }
    guide_dims = matrix_dimensions(guide / "matrix.mtx")
    combined_raw_dims = matrix_dimensions(combined_raw / "matrix.mtx.gz")
    combined_filtered_dims = matrix_dimensions(combined_filtered / "matrix.mtx.gz")

    if raw_gene_dims[0] != EXPECTED_GEX_FEATURES:
        raise ValueError(f"{capture} raw GEX has {raw_gene_dims[0]} features")
    if filtered_gene_dims[0] != EXPECTED_GEX_FEATURES or filtered_gene_dims[1] == 0:
        raise ValueError(f"{capture} filtered GEX dimensions are {filtered_gene_dims}")
    if line_count(gene_filtered / "features.tsv") != EXPECTED_GEX_FEATURES:
        raise ValueError(f"{capture} filtered GEX feature table is incomplete")
    if line_count(gene_filtered / "barcodes.tsv") != filtered_gene_dims[1]:
        raise ValueError(f"{capture} filtered GEX barcode count does not match matrix")
    for layer, dims in velocity_dims.items():
        if dims[:2] != filtered_gene_dims[:2]:
            raise ValueError(f"{capture} {layer} dimensions {dims} do not match GEX")

    if guide_dims[0] != EXPECTED_GUIDE_FEATURES or guide_dims[1] == 0:
        raise ValueError(f"{capture} guide dimensions are {guide_dims}")
    if line_count(guide / "features.tsv") != EXPECTED_GUIDE_FEATURES:
        raise ValueError(f"{capture} guide feature table is incomplete")
    guide_barcodes = read_barcodes(guide / "barcodes.tsv")
    if len(guide_barcodes) != guide_dims[1]:
        raise ValueError(f"{capture} guide barcode count does not match matrix")
    invalid_guide = sorted(set(guide_barcodes).difference(nxt_whitelist))
    if invalid_guide:
        raise ValueError(f"{capture} assignment MEX has non-NXT barcodes: {invalid_guide[:10]}")

    expected_combined_features = EXPECTED_GEX_FEATURES + EXPECTED_GUIDE_FEATURES
    if combined_raw_dims[0] != expected_combined_features:
        raise ValueError(f"{capture} combined raw dimensions are {combined_raw_dims}")
    if combined_filtered_dims[0] != expected_combined_features:
        raise ValueError(f"{capture} combined filtered dimensions are {combined_filtered_dims}")
    if combined_filtered_dims[1] != filtered_gene_dims[1]:
        raise ValueError(f"{capture} combined filtered cells do not match filtered GEX")
    if line_count(combined_filtered / "features.tsv.gz") != expected_combined_features:
        raise ValueError(f"{capture} combined filtered feature table is incomplete")

    combined_raw_barcodes = read_barcodes(combined_raw / "barcodes.tsv.gz")
    combined_filtered_barcodes = read_barcodes(combined_filtered / "barcodes.tsv.gz")
    if len(combined_raw_barcodes) != combined_raw_dims[1]:
        raise ValueError(f"{capture} combined raw barcode count does not match matrix")
    if len(combined_filtered_barcodes) != combined_filtered_dims[1]:
        raise ValueError(f"{capture} combined filtered barcode count does not match matrix")
    invalid_combined = sorted(
        set(combined_raw_barcodes).union(combined_filtered_barcodes).difference(tru_whitelist)
    )
    if invalid_combined:
        raise ValueError(f"{capture} combined MEX has non-TRU barcodes: {invalid_combined[:10]}")
    translated_overlap = len(
        {nxt_to_tru(barcode) for barcode in guide_barcodes}.intersection(combined_raw_barcodes)
    )
    if translated_overlap == 0:
        raise ValueError(f"{capture} NXT guide barcodes do not overlap canonical TRU output")

    return {
        "capture": capture,
        "raw_gene_dimensions": raw_gene_dims,
        "filtered_gene_dimensions": filtered_gene_dims,
        "velocyto_filtered_dimensions": velocity_dims,
        "guide_dimensions": guide_dims,
        "combined_raw_dimensions": combined_raw_dims,
        "combined_filtered_dimensions": combined_filtered_dims,
        "translated_guide_overlap_combined_raw": translated_overlap,
        "bam_bytes": (run_dir / "Aligned.out.bam").stat().st_size,
        "completion_marker": completion.strip().splitlines(),
    }


def main() -> int:
    args = parse_args()
    root = args.production_root.resolve()
    if "zshard" in str(root):
        raise ValueError(f"zshard path is forbidden: {root}")
    nxt_path = Path(str(args.tru_whitelist).replace("_TRU.txt", "_NXT.txt"))
    if not nxt_path.is_file():
        raise ValueError(f"paired NXT whitelist not found: {nxt_path}")

    tru_whitelist = read_whitelist(args.tru_whitelist)
    nxt_whitelist = read_whitelist(nxt_path)
    captures = [
        validate_capture(root, capture, tru_whitelist, nxt_whitelist)
        for capture in CAPTURES
    ]
    report = {
        "status": "PASS",
        "production_root": str(root),
        "capture_count": len(captures),
        "captures": captures,
        "reference": "GRCh38-2024-A/Gencode-v44 MSK-30 index",
        "star_suite_version": "1.9.4",
        "star_suite_commit": "1c9ddb9a5a2a3e62748e8e4ef28e553582affeed",
        "gex_input_namespace": "TRU",
        "guide_input_namespace": "NXT",
        "canonical_output_namespace": "TRU",
        "gzip_policy": "native gzip, no transcode",
        "zshard_used": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
