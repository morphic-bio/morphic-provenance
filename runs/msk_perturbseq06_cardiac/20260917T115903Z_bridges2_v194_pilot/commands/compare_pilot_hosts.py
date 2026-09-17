#!/usr/bin/env python3
"""Compare gathered Pikachu and Bridges-2 pilot reports."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


METRIC_KEYS = (
    "raw_gene_dimensions",
    "raw_gene_umi_sum",
    "filtered_gene_dimensions",
    "filtered_gene_umi_sum",
    "guide_dimensions",
    "guide_umi_sum",
    "guide_features",
    "guide_barcodes_checked",
    "combined_raw_dimensions",
    "combined_raw_umi_sum",
    "combined_filtered_dimensions",
    "combined_filtered_umi_sum",
    "combined_raw_barcodes_checked",
    "combined_filtered_barcodes_checked",
    "translated_guide_overlap_combined_raw",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pikachu-gather", required=True, type=Path)
    parser.add_argument("--bridges-gather", required=True, type=Path)
    parser.add_argument("--pikachu-guide-semantics", required=True, type=Path)
    parser.add_argument("--bridges-guide-semantics", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def by_capture(report: dict) -> dict[str, dict]:
    return {row["pilot_capture"]: row for row in report["reports"]}


def semantics_by_capture(report: dict) -> dict[str, dict]:
    return {row["capture"]: row for row in report["captures"]}


def main() -> int:
    args = parse_args()
    pikachu = json.loads(args.pikachu_gather.read_text())
    bridges = json.loads(args.bridges_gather.read_text())
    p_rows = by_capture(pikachu)
    b_rows = by_capture(bridges)
    p_semantics = semantics_by_capture(json.loads(args.pikachu_guide_semantics.read_text()))
    b_semantics = semantics_by_capture(json.loads(args.bridges_guide_semantics.read_text()))
    if set(p_rows) != {"CP_R1", "CP_R2"} or set(b_rows) != set(p_rows):
        raise ValueError("host reports do not contain the same two captures")
    if set(p_semantics) != set(p_rows) or set(b_semantics) != set(p_rows):
        raise ValueError("guide semantic reports do not contain the same two captures")

    comparisons = []
    for capture in ("CP_R1", "CP_R2"):
        metric_equal = {key: p_rows[capture][key] == b_rows[capture][key] for key in METRIC_KEYS}
        artifact_equal = {
            key: value == b_rows[capture]["artifact_sha256"].get(key)
            for key, value in p_rows[capture]["artifact_sha256"].items()
        }
        semantic_keys = (
            "dimensions",
            "value_sum",
            "barcode_set_sha256",
            "barcode_keyed_matrix_sha256",
        )
        guide_semantic_equal = {
            key: p_semantics[capture][key] == b_semantics[capture][key]
            for key in semantic_keys
        }
        comparisons.append(
            {
                "capture": capture,
                "metric_equal": metric_equal,
                "all_metrics_equal": all(metric_equal.values()),
                "artifact_sha256_equal": artifact_equal,
                "all_artifact_sha256_equal": all(artifact_equal.values()),
                "guide_semantic_equal": guide_semantic_equal,
                "all_guide_semantics_equal": all(guide_semantic_equal.values()),
            }
        )

    status = (
        "PASS"
        if all(
            row["all_metrics_equal"] and row["all_guide_semantics_equal"]
            for row in comparisons
        )
        else "FAIL"
    )
    result = {
        "status": status,
        "method": "same FASTQs, 250000-read cap, STAR Suite v1.9.4, GRCh38 2024-A, native gzip",
        "build_modes": {
            "pikachu": "WITH_CHROMAP=1",
            "bridges2": "WITH_CHROMAP=0",
            "scope": "same GEX/Solo/process_features code; Chromap is not invoked",
        },
        "comparisons": comparisons,
        "note": (
            "Metric and barcode-keyed guide MEX equality are required; raw artifact byte "
            "equality is reported separately because assignment columns may be reordered."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
