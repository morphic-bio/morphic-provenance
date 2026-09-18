#!/usr/bin/env python3
from __future__ import annotations

import csv
import gzip
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import h5py


RUN_ROOT = Path("/mnt/pikachu/MSK_Perturbseq06_Cardiac_temporal_pilot_20260917T193023Z")
PROVENANCE_ROOT = Path(__file__).resolve().parents[1]
GPU_ROOT = RUN_ROOT / "gpu"
SLURM_ROOT = RUN_ROOT / "slurm"
EXPECTED_GPU_FILES = {
    "cellbender_counts.h5",
    "cellbender_counts.log",
    "cellbender_counts.pdf",
    "cellbender_counts_cell_barcodes.csv",
    "cellbender_counts_filtered.h5",
    "cellbender_counts_metrics.csv",
    "cellbender_counts_posterior.h5",
    "cellbender_counts_report.html",
    "ckpt.tar.gz",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_mex_shape(path: Path) -> list[int]:
    with gzip.open(path, "rt") as handle:
        for line in handle:
            if not line.startswith("%"):
                return [int(value) for value in line.split()]
    raise RuntimeError(f"Matrix Market dimensions not found in {path}")


def read_cellbender(path: Path) -> dict:
    with h5py.File(path, "r") as handle:
        estimator = handle["metadata/estimator"][0].decode()
        return {
            "matrix_shape": handle["matrix/shape"][()].astype(int).tolist(),
            "matrix_nnz": int(handle["matrix/data"].shape[0]),
            "estimator": estimator,
            "analyzed_barcodes": int(handle["metadata/barcodes_analyzed"].shape[0]),
            "analyzed_features": int(handle["metadata/features_analyzed_inds"].shape[0]),
        }


def main() -> None:
    output_root = PROVENANCE_ROOT / "outputs"
    output_root.mkdir(parents=True, exist_ok=True)
    gpu_files = {path.name for path in GPU_ROOT.iterdir() if path.is_file()}
    if gpu_files != EXPECTED_GPU_FILES:
        raise RuntimeError(
            f"Unexpected GPU artifact set: missing={EXPECTED_GPU_FILES - gpu_files} "
            f"extra={gpu_files - EXPECTED_GPU_FILES}"
        )

    raw_mex_shape = read_mex_shape(SLURM_ROOT / "raw_feature_bc_matrix/matrix.mtx.gz")
    if raw_mex_shape != [54262, 97789, 801269]:
        raise RuntimeError(f"Unexpected raw MEX shape: {raw_mex_shape}")

    full = read_cellbender(GPU_ROOT / "cellbender_counts.h5")
    filtered = read_cellbender(GPU_ROOT / "cellbender_counts_filtered.h5")
    if full["matrix_shape"] != [54262, 97789] or filtered["matrix_shape"] != [54262, 629]:
        raise RuntimeError(f"Unexpected CellBender dimensions: full={full} filtered={filtered}")
    if full["estimator"] != "mean" or filtered["estimator"] != "mean":
        raise RuntimeError(f"Unexpected CellBender estimator: full={full} filtered={filtered}")

    cellbender_log = (GPU_ROOT / "cellbender_counts.log").read_text()
    for marker in ("--cuda", "[epoch 010]", "Completed remove-background"):
        if marker not in cellbender_log:
            raise RuntimeError(f"Missing CellBender completion marker: {marker}")

    complete = json.loads((SLURM_ROOT / "SLURM_COMPLETE.json").read_text())
    if complete.get("status") != "PASS" or complete.get("slurm_job_id") != "46275807":
        raise RuntimeError(f"Unexpected Slurm completion record: {complete}")

    manifest_path = output_root / "final_artifact_manifest.tsv"
    with manifest_path.open("w", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(["relative_path", "size_bytes", "sha256"])
        for path in sorted(GPU_ROOT.iterdir()):
            if path.is_file():
                writer.writerow([f"gpu/{path.name}", path.stat().st_size, sha256(path)])

    report = {
        "validated_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "status": "PASS",
        "slurm": complete,
        "stage_back_globus_task": "be2140af-b2d2-11f1-be05-02ffe792127d",
        "publish_globus_task": "9b6d8577-b2dc-11f1-9987-0effcb3df825",
        "raw_mex_shape": raw_mex_shape,
        "cellbender_full": full,
        "cellbender_filtered": filtered,
        "gpu_artifact_count": len(gpu_files),
        "gpu_artifact_bytes": sum((GPU_ROOT / name).stat().st_size for name in gpu_files),
        "manifest": str(manifest_path.relative_to(PROVENANCE_ROOT)),
    }
    (output_root / "final_validation.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
