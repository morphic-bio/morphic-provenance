from __future__ import annotations

import json
from pathlib import Path

from provenance_service.importer import build_repository_events


def test_importer_builds_queryable_lineage_and_release(tmp_path, service):
    repository = tmp_path / "repository"
    run_dir = repository / "runs/project-one/run-one"
    run_dir.mkdir(parents=True)
    source = run_dir / "source.fastq.gz"
    output = run_dir / "counts.tsv"
    source.write_bytes(b"fastq")
    output.write_text("gene\tcount\n", encoding="utf-8")
    record = {
        "schema_version": "0.1",
        "run_id": "run-one",
        "project": "project-one",
        "created_utc": "2026-07-17T12:00:00Z",
        "status": "complete",
        "star_suite": {"repo": "STAR-suite", "commit": "abc"},
        "recipes": {"repo": "morphic-recipes", "commit": "def", "workflow_id": "bulk"},
        "environment": {},
        "inputs": [{"name": "raw", "path": "source.fastq.gz", "bytes": 5}],
        "outputs": [{"name": "counts", "path": "counts.tsv", "bytes": 11}],
        "dataset_releases": [
            {
                "release_key": "project-one/2026-07-17",
                "release_date": "2026-07-17",
                "path": "dataset_releases/project-one/2026-07-17",
            }
        ],
    }
    (run_dir / "run.json").write_text(json.dumps(record), encoding="utf-8")

    incompatible = repository / "runs/project-two/repair/run.json"
    incompatible.parent.mkdir(parents=True)
    incompatible.write_text(json.dumps({"run_id": "repair", "outputs": {}}), encoding="utf-8")

    plan = build_repository_events(repository)
    assert plan.records == 1
    assert len(plan.events) == 8
    assert plan.skipped[0]["record"] == "runs/project-two/repair/run.json"
    assert service.ingest_batch(plan.events)[0]["status"] == "inserted"

    output_id = "artifact:run/project-one/run-one/output/0"
    lineage = service.lineage(output_id)
    assert {node["name"] for node in lineage["nodes"]} == {"raw", "counts"}
    release = service.get_release("project-one/2026-07-17")
    assert release["artifacts"][0]["artifact_id"] == output_id

    duplicate_results = service.ingest_batch(plan.events)
    assert {item["status"] for item in duplicate_results} == {"duplicate"}


def test_current_repository_can_be_planned_and_ingested(tmp_path):
    from provenance_service.config import Settings
    from provenance_service.service import ProvenanceService

    repository = Path(__file__).resolve().parents[1]
    plan = build_repository_events(repository)
    assert plan.records >= 8
    assert len(plan.events) >= 40
    service = ProvenanceService(
        Settings(
            database_path=tmp_path / "repository.sqlite3",
            artifact_root=tmp_path / "artifacts",
        )
    )
    service.initialize()
    results = service.ingest_batch(plan.events)
    assert len(results) == len(plan.events)
    assert {result["status"] for result in results} == {"inserted"}
    assert service.search({"query": "jax", "limit": 200})["total"] > 0
