#!/usr/bin/env python3
"""Gather the two-node pilot and require distinct Slurm nodes."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


CAPTURES = ("CP_R1", "CP_R2")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pilot-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--host", required=True)
    parser.add_argument("--require-distinct-nodes", action="store_true")
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def read_kv(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in path.read_text().splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            result[key] = value
    return result


def main() -> int:
    args = parse_args()
    if "zshard" in str(args.pilot_root):
        raise ValueError(f"zshard path is forbidden: {args.pilot_root}")

    reports = []
    nodes = []
    for capture in CAPTURES:
        capture_root = args.pilot_root / capture
        report_path = capture_root / "PILOT_VALIDATION.json"
        complete_path = capture_root / "PILOT_COMPLETE.txt"
        report = json.loads(report_path.read_text())
        complete = read_kv(complete_path)
        if report.get("status") != "PASS" or complete.get("status") != "COMPLETE":
            raise ValueError(f"pilot did not pass for {capture}")
        if report.get("pilot_capture") != capture:
            raise ValueError(f"capture mismatch in {report_path}")
        node = complete.get("node", args.host)
        nodes.append(node)

        guide_id = f"grna_{capture.lower()}"
        run = capture_root / "run"
        artifacts = {
            "gene_raw_features": run / "Solo.out/GeneFull/raw/features.tsv",
            "gene_raw_barcodes": run / "Solo.out/GeneFull/raw/barcodes.tsv",
            "gene_raw_matrix": run / "Solo.out/GeneFull/raw/matrix.mtx",
            "guide_features": run
            / f"cr_assign/CRISPR_Guide_Capture/{guide_id}/PolyIII/features.tsv",
            "guide_barcodes": run
            / f"cr_assign/CRISPR_Guide_Capture/{guide_id}/PolyIII/barcodes.tsv",
            "guide_matrix": run
            / f"cr_assign/CRISPR_Guide_Capture/{guide_id}/PolyIII/matrix.mtx",
            "combined_raw_barcodes": run / "outs/raw_feature_bc_matrix/barcodes.tsv.gz",
            "combined_raw_matrix": run / "outs/raw_feature_bc_matrix/matrix.mtx.gz",
            "combined_filtered_barcodes": run
            / "outs/filtered_feature_bc_matrix/barcodes.tsv.gz",
            "combined_filtered_matrix": run / "outs/filtered_feature_bc_matrix/matrix.mtx.gz",
        }
        report["host"] = args.host
        report["node"] = node
        report["artifact_sha256"] = {name: sha256(path) for name, path in artifacts.items()}
        reports.append(report)

    if args.require_distinct_nodes and len(set(nodes)) != len(CAPTURES):
        raise ValueError(f"two-node pilot landed on fewer than two nodes: {nodes}")

    gathered = {
        "status": "PASS",
        "host": args.host,
        "captures": list(CAPTURES),
        "nodes": nodes,
        "distinct_nodes": len(set(nodes)),
        "reports": reports,
        "gzip_policy": "native gzip, no transcode",
        "zshard_used": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(gathered, indent=2, sort_keys=True) + "\n")
    print(json.dumps(gathered, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
