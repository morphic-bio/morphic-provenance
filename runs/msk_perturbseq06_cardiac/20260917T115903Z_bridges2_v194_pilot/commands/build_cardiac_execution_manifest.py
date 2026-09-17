#!/usr/bin/env python3
"""Validate the Cardiac delivery and render an execution manifest."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


PAIR_RE = re.compile(r"_(R[12])_001\.fastq\.gz$")
CAPTURES = ("CP_A1", "CP_A2", "CP_A3", "CP_B1", "CP_B2", "CP_B3", "CP_R1", "CP_R2")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file-manifest", required=True, type=Path)
    parser.add_argument("--provider-checksums", required=True, type=Path)
    parser.add_argument("--fastq-root", required=True, type=Path)
    parser.add_argument("--output-files", required=True, type=Path)
    parser.add_argument("--output-libraries", required=True, type=Path)
    parser.add_argument("--output-audit", required=True, type=Path)
    return parser.parse_args()


def read_checksums(path: Path) -> dict[str, str]:
    checksums: dict[str, str] = {}
    for line_number, line in enumerate(path.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2 or len(parts[0]) != 32:
            raise ValueError(f"invalid checksum line {line_number}: {line!r}")
        name = Path(parts[1].lstrip("* ")).name
        if name in checksums:
            raise ValueError(f"duplicate checksum basename: {name}")
        checksums[name] = parts[0].lower()
    return checksums


def pair_key(name: str) -> str:
    match = PAIR_RE.search(name)
    if not match:
        raise ValueError(f"not an R1/R2 FASTQ basename: {name}")
    return name[: match.start()] + "_PAIR_001.fastq.gz"


def main() -> int:
    args = parse_args()
    if "zshard" in str(args.fastq_root):
        raise ValueError(f"zshard path is forbidden: {args.fastq_root}")

    with args.file_manifest.open(newline="") as handle:
        source_rows = list(csv.DictReader(handle, delimiter="\t"))
    if len(source_rows) != 1020:
        raise ValueError(f"expected 1020 manifest rows, found {len(source_rows)}")

    expected_names = [row["file_name"] for row in source_rows]
    if len(set(expected_names)) != len(expected_names):
        raise ValueError("corrected manifest contains duplicate basenames")

    observed = {path.name: path for path in args.fastq_root.glob("*.fastq.gz")}
    expected = set(expected_names)
    missing = sorted(expected - observed.keys())
    extra = sorted(observed.keys() - expected)
    if missing or extra:
        raise ValueError(f"FASTQ inventory mismatch: missing={missing[:10]} extra={extra[:10]}")

    checksums = read_checksums(args.provider_checksums)
    missing_checksums = sorted(expected - checksums.keys())
    extra_checksums = sorted(checksums.keys() - expected)
    if missing_checksums or extra_checksums:
        raise ValueError(
            "provider checksum inventory mismatch: "
            f"missing={missing_checksums[:10]} extra={extra_checksums[:10]}"
        )

    output_rows: list[dict[str, str | int]] = []
    library_pairs: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    library_bytes: Counter[str] = Counter()
    library_files: Counter[str] = Counter()

    for row in source_rows:
        name = row["file_name"]
        path = observed[name]
        size = path.stat().st_size
        recorded_size = int(row["size_bytes"] or 0)
        if recorded_size and recorded_size != size:
            raise ValueError(f"size mismatch for {name}: manifest={recorded_size} observed={size}")

        library_id = row["library_preparation_id"]
        suffix = library_id.rsplit("_", 1)[-1]
        if suffix not in {"mRNA", "gRNA"}:
            raise ValueError(f"unexpected library suffix: {library_id}")
        capture = library_id[: -(len(suffix) + 1)]
        if capture not in CAPTURES:
            raise ValueError(f"unexpected logical capture: {capture}")

        if suffix == "mRNA":
            expected_route = ("TRU", "TRU", "Gene Expression")
        else:
            expected_route = ("NXT", "TRU", "CRISPR Guide Capture")
        route = (
            row["input_barcode_namespace"],
            row["canonical_output_namespace"],
            row["library_type"],
        )
        if route != expected_route:
            raise ValueError(f"unexpected chemistry route for {library_id}: {route}")

        read_role = row["read_role"]
        include = read_role in {"read1", "read2"}
        if include:
            key = pair_key(name)
            library_pairs[library_id][key].add(read_role)
        library_bytes[library_id] += size
        library_files[library_id] += 1

        output_rows.append(
            {
                "dataset": row["dataset"],
                "logical_capture": capture,
                "library_preparation_id": library_id,
                "library_type": row["library_type"],
                "protocol_id": row["protocol_id"],
                "whitelist_family": row["whitelist_family"],
                "input_barcode_namespace": row["input_barcode_namespace"],
                "canonical_output_namespace": row["canonical_output_namespace"],
                "run_id": row["run_id"],
                "lane_index": row["lane_index"],
                "read_role": read_role,
                "read_length": row["read_length"],
                "file_name": name,
                "source_path": str(path.resolve()),
                "size_bytes": size,
                "md5": checksums[name],
                "include_for_processing": "true" if include else "false",
            }
        )

    libraries_by_capture: dict[str, set[str]] = defaultdict(set)
    for library_id, pairs in library_pairs.items():
        bad = {key: roles for key, roles in pairs.items() if roles != {"read1", "read2"}}
        if bad:
            raise ValueError(f"unpaired reads in {library_id}: {list(bad.items())[:5]}")
        libraries_by_capture[library_id.rsplit("_", 1)[0]].add(library_id.rsplit("_", 1)[1])

    for capture in CAPTURES:
        if libraries_by_capture[capture] != {"mRNA", "gRNA"}:
            raise ValueError(f"capture {capture} does not have exactly mRNA and gRNA libraries")

    args.output_files.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(output_rows[0])
    with args.output_files.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(output_rows)

    library_rows = []
    by_library = {row["library_preparation_id"]: row for row in output_rows}
    for library_id in sorted(library_files):
        row = by_library[library_id]
        pair_count = len(library_pairs[library_id])
        library_rows.append(
            {
                "logical_capture": row["logical_capture"],
                "library_preparation_id": library_id,
                "library_type": row["library_type"],
                "input_barcode_namespace": row["input_barcode_namespace"],
                "canonical_output_namespace": row["canonical_output_namespace"],
                "all_fastq_count": library_files[library_id],
                "processing_pair_count": pair_count,
                "all_bytes": library_bytes[library_id],
            }
        )
    with args.output_libraries.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(library_rows[0]),
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(library_rows)

    audit = {
        "status": "PASS",
        "fastq_root": str(args.fastq_root.resolve()),
        "expected_fastqs": len(expected),
        "observed_fastqs": len(observed),
        "provider_checksums": len(checksums),
        "logical_captures": list(CAPTURES),
        "libraries": len(library_rows),
        "processing_read_pairs": sum(len(pairs) for pairs in library_pairs.values()),
        "total_bytes": sum(path.stat().st_size for path in observed.values()),
        "gzip_policy": "native gzip; byte-preserving node-local copy; no transcode",
        "zshard_allowed": False,
    }
    args.output_audit.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    print(json.dumps(audit, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
