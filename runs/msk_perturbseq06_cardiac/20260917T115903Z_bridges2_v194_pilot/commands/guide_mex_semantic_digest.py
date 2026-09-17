#!/usr/bin/env python3
"""Hash guide MEX counts independently of barcode column ordering."""

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
    return parser.parse_args()


def digest_lines(lines: list[str]) -> str:
    digest = hashlib.sha256()
    for line in lines:
        digest.update(line.encode())
        digest.update(b"\n")
    return digest.hexdigest()


def capture_digest(pilot_root: Path, capture: str) -> dict:
    guide_id = f"grna_{capture.lower()}"
    guide_root = (
        pilot_root
        / capture
        / "run"
        / "cr_assign"
        / "CRISPR_Guide_Capture"
        / guide_id
        / "PolyIII"
    )
    barcodes = [line.strip() for line in (guide_root / "barcodes.tsv").read_text().splitlines()]
    if len(barcodes) != len(set(barcodes)):
        raise ValueError(f"duplicate guide barcodes in {capture}")

    dimensions = None
    entries = []
    value_sum = 0
    with (guide_root / "matrix.mtx").open() as handle:
        for line in handle:
            if line.startswith("%"):
                continue
            fields = line.split()
            if dimensions is None:
                dimensions = tuple(int(value) for value in fields)
                continue
            feature_row, barcode_column, value_text = fields
            value = int(value_text)
            barcode = barcodes[int(barcode_column) - 1]
            entries.append((barcode, int(feature_row), value))
            value_sum += value

    if dimensions is None or dimensions[1] != len(barcodes) or dimensions[2] != len(entries):
        raise ValueError(f"guide MEX dimensions do not match data in {capture}")

    canonical_lines = [
        f"{barcode}\t{feature_row}\t{value}"
        for barcode, feature_row, value in sorted(entries)
    ]
    return {
        "capture": capture,
        "dimensions": list(dimensions),
        "value_sum": value_sum,
        "barcode_set_sha256": digest_lines(sorted(barcodes)),
        "barcode_keyed_matrix_sha256": digest_lines(canonical_lines),
    }


def main() -> int:
    args = parse_args()
    result = {
        "status": "PASS",
        "method": "sort barcodes; hash sorted (barcode, feature row, integer count) tuples",
        "captures": [capture_digest(args.pilot_root, capture) for capture in CAPTURES],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
