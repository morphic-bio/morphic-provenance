#!/usr/bin/env python3
"""Validate Cardiac H5AD/QC outputs after CUDA CellBender integration."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import anndata as ad


H5ADS = (
    "counts.h5ad",
    "unfiltered_counts.h5ad",
    "filtered_counts.h5ad",
    "default_singlet_filtered_counts.h5ad",
    "final_counts.h5ad",
)
REQUIRED_LAYERS = {"spliced", "unspliced", "ambiguous", "denoised"}
REQUIRED_OBS = {
    "is_cell",
    "filter",
    "non_empty",
    "doublet",
    "doublet_scores",
    "singlet",
    "n_genes",
    "mt_counts",
    "total_counts",
    "mt_pct",
    "singlet_filtered",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--downstream-dir", required=True, type=Path)
    parser.add_argument("--capture", required=True)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def require_file(path: Path) -> None:
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f"missing or empty output: {path}")


def inspect_h5ad(path: Path, guide_prefix: str) -> dict[str, object]:
    require_file(path)
    obj = ad.read_h5ad(path, backed="r")
    try:
        if obj.n_obs == 0 or obj.n_vars != 38606:
            raise ValueError(f"unexpected shape for {path}: {obj.shape}")
        layers = set(obj.layers.keys())
        missing_layers = sorted(REQUIRED_LAYERS.difference(layers))
        if missing_layers:
            raise ValueError(f"{path} is missing layers: {missing_layers}")
        missing_obs = sorted(REQUIRED_OBS.difference(obj.obs.columns))
        if missing_obs:
            raise ValueError(f"{path} is missing obs columns: {missing_obs}")
        guide_fields = {
            f"{guide_prefix}__num_features",
            f"{guide_prefix}__num_umis",
            f"{guide_prefix}__feature_call",
            f"{guide_prefix}__is_featured",
            f"{guide_prefix}__feature1_count",
            f"{guide_prefix}__feature2_count",
            f"{guide_prefix}__feature_call_category",
        }
        missing_guide = sorted(guide_fields.difference(obj.obs.columns))
        if missing_guide:
            raise ValueError(f"{path} is missing guide obs columns: {missing_guide}")
        required_uns = {"feature_libraries", "mt_adaptive_filter", "velocyto_source"}
        missing_uns = sorted(required_uns.difference(obj.uns.keys()))
        if missing_uns:
            raise ValueError(f"{path} is missing uns entries: {missing_uns}")
        if "X_scimilarity" in obj.obsm:
            raise ValueError(f"{path} unexpectedly contains X_scimilarity")
        disallowed_obs = [
            name
            for name in obj.obs.columns
            if name.startswith("rf_") or name in {"celltype", "subcelltype"}
        ]
        if disallowed_obs:
            raise ValueError(f"{path} unexpectedly contains cell-type labels: {disallowed_obs}")
        return {
            "path": str(path),
            "bytes": path.stat().st_size,
            "shape": [obj.n_obs, obj.n_vars],
            "layers": sorted(layers),
            "obs_columns": len(obj.obs.columns),
            "obsm": sorted(obj.obsm.keys()),
            "uns": sorted(obj.uns.keys()),
        }
    finally:
        obj.file.close()


def main() -> int:
    args = parse_args()
    downstream = args.downstream_dir.resolve()
    if "zshard" in str(downstream):
        raise ValueError(f"zshard path is forbidden: {downstream}")
    capture_lower = args.capture.lower()
    guide_id = f"grna_{capture_lower}"
    guide_prefix = f"CRISPR_Guide_Capture_{guide_id}"

    required = [
        downstream / "adaptive_qc_threshold.json",
        downstream / "gene_quantile_histogram.html",
        downstream / "gene_quantile_histogram.png",
        downstream / "summary.txt",
        downstream / "cellbender/cellbender_counts.h5",
        downstream / "cellbender/cellbender_counts_report.html",
        downstream / f"feature_libraries/{guide_id}/raw_feature_library.h5ad",
        downstream / f"feature_libraries/{guide_id}/filtered_feature_library.h5ad",
        downstream / f"feature_libraries/{guide_id}/manifest.json",
    ]
    for path in required:
        require_file(path)
    failure_note = downstream / "cellbender/CELLBENDER_FAILED.txt"
    if failure_note.exists():
        raise ValueError(f"CellBender failure marker exists: {failure_note}")

    h5ads = {
        name: inspect_h5ad(downstream / name, guide_prefix)
        for name in H5ADS
    }
    if h5ads["final_counts.h5ad"]["shape"] != h5ads["unfiltered_counts.h5ad"]["shape"]:
        raise ValueError("final_counts.h5ad does not match the unfiltered barcode universe")
    if h5ads["filtered_counts.h5ad"]["shape"][0] == 0:
        raise ValueError("filtered_counts.h5ad contains no cells")
    if h5ads["default_singlet_filtered_counts.h5ad"]["shape"][0] == 0:
        raise ValueError("default_singlet_filtered_counts.h5ad contains no cells")

    feature_h5ads = {}
    for kind in ("raw", "filtered"):
        path = downstream / f"feature_libraries/{guide_id}/{kind}_feature_library.h5ad"
        obj = ad.read_h5ad(path, backed="r")
        try:
            if obj.n_obs == 0 or obj.n_vars != 15656:
                raise ValueError(f"unexpected guide feature H5AD shape for {path}: {obj.shape}")
            feature_h5ads[kind] = {
                "path": str(path),
                "bytes": path.stat().st_size,
                "shape": [obj.n_obs, obj.n_vars],
            }
        finally:
            obj.file.close()

    report = {
        "status": "PASS",
        "capture": args.capture,
        "downstream_dir": str(downstream),
        "h5ads": h5ads,
        "guide_feature_h5ads": feature_h5ads,
        "cellbender": {
            "image": "biodepot/cellbender:0.3.2",
            "image_id": "sha256:f31f1e993f3d87659c3dd541a22f505fec7ee4366f6d5da1324061c2c09dcb2a",
            "cuda_required": True,
            "output": str(downstream / "cellbender/cellbender_counts.h5"),
            "layer": "denoised",
        },
        "adaptive_mt_filter": True,
        "scimilarity_run": False,
        "provider_labels_added": False,
        "larry_expected": False,
    }
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
