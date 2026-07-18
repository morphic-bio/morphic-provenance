from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from provenance_service.errors import ConflictError, NotFoundError, UnsafePathError


def artifact_payload(artifact_id: str, name: str, **overrides):
    payload = {
        "artifact_id": artifact_id,
        "name": name,
        "kind": "file",
        "project": "bulk-rna-smoke",
        "status": "verified",
        "metadata": {"assay": "RNA-seq"},
    }
    payload.update(overrides)
    return payload


def register_lineage(service, event_factory):
    events = [
        event_factory(
            "event:raw-artifact",
            "artifact.registered",
            artifact_payload("artifact:raw-fastq", "sample_R1.fastq.gz", status="observed"),
        ),
        event_factory(
            "event:counts-artifact",
            "artifact.registered",
            artifact_payload("artifact:normalized-counts", "normalized-counts.tsv"),
        ),
        event_factory(
            "event:workflow",
            "activity.registered",
            {
                "activity_id": "activity:bulk-rna",
                "name": "Bulk RNA-seq alignment and counting",
                "kind": "workflow",
                "project": "bulk-rna-smoke",
                "run_id": "run:bulk-rna-1",
                "workflow_id": "bulk_rna_seq",
                "status": "complete",
                "started_at": "2026-07-17T11:00:00Z",
                "ended_at": "2026-07-17T12:00:00Z",
            },
        ),
        event_factory(
            "event:derivation",
            "derivation.registered",
            {
                "output_artifact_id": "artifact:normalized-counts",
                "input_artifact_ids": ["artifact:raw-fastq"],
                "activity_id": "activity:bulk-rna",
                "relation": "derived_from",
            },
        ),
    ]
    return service.ingest_batch(events)


def test_ingest_and_bidirectional_lineage(service, event_factory):
    results = register_lineage(service, event_factory)
    assert [item["status"] for item in results] == ["inserted"] * 4

    artifact = service.get_artifact("artifact:normalized-counts")
    assert artifact["project"] == "bulk-rna-smoke"
    assert artifact["metadata"] == {"assay": "RNA-seq"}

    upstream = service.lineage("artifact:normalized-counts", "upstream")
    assert [node["artifact_id"] for node in upstream["nodes"]] == [
        "artifact:normalized-counts",
        "artifact:raw-fastq",
    ]
    assert upstream["edges"][0]["activity_id"] == "activity:bulk-rna"

    downstream = service.lineage("artifact:raw-fastq", "downstream")
    assert {node["artifact_id"] for node in downstream["nodes"]} == {
        "artifact:raw-fastq",
        "artifact:normalized-counts",
    }


def test_duplicate_event_is_idempotent_and_changed_content_conflicts(service, event_factory):
    event = event_factory(
        "event:artifact", "artifact.registered", artifact_payload("artifact:one", "one.tsv")
    )
    assert service.ingest(event)["status"] == "inserted"
    assert service.ingest(event)["status"] == "duplicate"

    changed = event | {"payload": artifact_payload("artifact:one", "renamed.tsv")}
    with pytest.raises(ConflictError, match="different content"):
        service.ingest(changed)
    assert service.health()["event_count"] == 1


def test_batch_projection_failure_rolls_back_event_log_and_views(service, event_factory):
    events = [
        event_factory(
            "event:temporary",
            "artifact.registered",
            artifact_payload("artifact:temporary", "temporary.tsv"),
        ),
        event_factory(
            "event:broken-derivation",
            "derivation.registered",
            {
                "output_artifact_id": "artifact:missing-output",
                "input_artifact_ids": ["artifact:temporary"],
                "activity_id": "activity:missing",
            },
        ),
    ]
    with pytest.raises(ConflictError, match="reference or uniqueness"):
        service.ingest_batch(events)
    with pytest.raises(NotFoundError):
        service.get_event("event:temporary")
    with pytest.raises(NotFoundError):
        service.get_artifact("artifact:temporary")


def test_location_revisions_reconcile_inside_root(service, settings, event_factory):
    payload_path = settings.artifact_root / "incoming/counts.tsv"
    payload_path.write_text("gene\tcount\nA\t2\n", encoding="utf-8")
    checksum = hashlib.sha256(payload_path.read_bytes()).hexdigest()
    service.ingest(
        event_factory(
            "event:artifact",
            "artifact.registered",
            artifact_payload(
                "artifact:counts",
                "counts.tsv",
                sha256=checksum,
                bytes=payload_path.stat().st_size,
            ),
        )
    )
    service.ingest(
        event_factory(
            "event:location-1",
            "location.recorded",
            {
                "location_id": "location:counts-local",
                "artifact_id": "artifact:counts",
                "kind": "local",
                "local_path": "incoming/counts.tsv",
                "status": "available",
                "mapping_revision": 1,
                "sha256": checksum,
                "bytes": payload_path.stat().st_size,
            },
        )
    )

    reconciliation = service.reconcile_location("location:counts-local", compute_sha256=True)
    assert reconciliation["exists"] is True
    assert reconciliation["checksum_match"] is True
    assert reconciliation["sha256"] == checksum

    stale = event_factory(
        "event:location-stale",
        "location.recorded",
        {
            "location_id": "location:counts-local",
            "artifact_id": "artifact:counts",
            "kind": "local",
            "local_path": "incoming/counts.tsv",
            "status": "available",
            "mapping_revision": 1,
        },
    )
    with pytest.raises(ConflictError, match="mapping_revision"):
        service.ingest(stale)
    with pytest.raises(NotFoundError):
        service.get_event("event:location-stale")

    service.ingest(
        event_factory(
            "event:location-unsafe",
            "location.recorded",
            {
                "location_id": "location:counts-local",
                "artifact_id": "artifact:counts",
                "kind": "local",
                "local_path": "/tmp/outside-provenance-root.tsv",
                "status": "declared",
                "mapping_revision": 2,
            },
        )
    )
    with pytest.raises(UnsafePathError, match="outside artifact root"):
        service.reconcile_location("location:counts-local")


def test_transfer_reports_preserve_identity_and_increase_revision(service, event_factory):
    service.ingest(
        event_factory(
            "event:artifact",
            "artifact.registered",
            artifact_payload("artifact:transfer", "payload.h5ad"),
        )
    )
    for suffix, location in (
        (
            "source",
            {
                "kind": "local",
                "local_path": "incoming/payload.h5ad",
            },
        ),
        (
            "destination",
            {
                "kind": "globus",
                "collection_id": "00000000-0000-0000-0000-000000000001",
                "collection_path": "/releases/payload.h5ad",
            },
        ),
    ):
        service.ingest(
            event_factory(
                f"event:location-{suffix}",
                "location.recorded",
                {
                    "location_id": f"location:{suffix}",
                    "artifact_id": "artifact:transfer",
                    "status": "available" if suffix == "source" else "declared",
                    "mapping_revision": 1,
                    **location,
                },
            )
        )

    base = {
        "transfer_id": "transfer:one",
        "artifact_id": "artifact:transfer",
        "source_location_id": "location:source",
        "destination_location_id": "location:destination",
        "mapping_revision": 1,
        "task_id": "globus-task-1",
    }
    service.ingest(
        event_factory(
            "event:transfer-1",
            "transfer.recorded",
            base | {"report_revision": 1, "status": "active"},
        )
    )
    service.ingest(
        event_factory(
            "event:transfer-2",
            "transfer.recorded",
            base | {"report_revision": 2, "status": "succeeded"},
        )
    )
    artifact = service.get_artifact("artifact:transfer")
    assert artifact["transfers"][0]["report_revision"] == 2
    assert artifact["transfers"][0]["status"] == "succeeded"

    with pytest.raises(ConflictError, match="report_revision"):
        service.ingest(
            event_factory(
                "event:transfer-stale",
                "transfer.recorded",
                base | {"report_revision": 1, "status": "failed"},
            )
        )
    with pytest.raises(ConflictError, match="succeeded -> active"):
        service.ingest(
            event_factory(
                "event:transfer-regression",
                "transfer.recorded",
                base | {"report_revision": 3, "status": "active"},
            )
        )
    service.ingest(
        event_factory(
            "event:transfer-mapping-2",
            "transfer.recorded",
            base | {"report_revision": 3, "mapping_revision": 2, "status": "succeeded"},
        )
    )
    with pytest.raises(ConflictError, match="mapping_revision cannot decrease"):
        service.ingest(
            event_factory(
                "event:transfer-mapping-regression",
                "transfer.recorded",
                base | {"report_revision": 4, "mapping_revision": 1, "status": "succeeded"},
            )
        )


def test_transfer_locations_must_belong_to_the_transferred_artifact(service, event_factory):
    for artifact_id in ("artifact:expected", "artifact:other"):
        service.ingest(
            event_factory(
                f"event:{artifact_id}",
                "artifact.registered",
                artifact_payload(artifact_id, f"{artifact_id}.h5ad"),
            )
        )
    for location_id, artifact_id in (
        ("location:source", "artifact:expected"),
        ("location:destination", "artifact:other"),
    ):
        service.ingest(
            event_factory(
                f"event:{location_id}",
                "location.recorded",
                {
                    "location_id": location_id,
                    "artifact_id": artifact_id,
                    "kind": "archive",
                    "uri": f"archive:/{location_id}",
                    "status": "declared",
                    "mapping_revision": 1,
                },
            )
        )

    with pytest.raises(ConflictError, match="does not belong"):
        service.ingest(
            event_factory(
                "event:cross-artifact-transfer",
                "transfer.recorded",
                {
                    "transfer_id": "transfer:cross-artifact",
                    "report_revision": 1,
                    "artifact_id": "artifact:expected",
                    "source_location_id": "location:source",
                    "destination_location_id": "location:destination",
                    "mapping_revision": 1,
                    "status": "requested",
                },
            )
        )
    with pytest.raises(NotFoundError):
        service.get_event("event:cross-artifact-transfer")


def test_release_membership_transitions_and_search(service, event_factory):
    service.ingest(
        event_factory(
            "event:artifact",
            "artifact.registered",
            artifact_payload("artifact:release-counts", "normalized-counts.tsv"),
        )
    )
    service.ingest(
        event_factory(
            "event:release",
            "release.registered",
            {
                "release_id": "bulk-rna-smoke/2026-07-17",
                "project": "bulk-rna-smoke",
                "name": "Bulk RNA smoke internal release",
                "status": "candidate",
            },
        )
    )
    service.ingest(
        event_factory(
            "event:release-member",
            "release.artifact_added",
            {
                "release_id": "bulk-rna-smoke/2026-07-17",
                "artifact_id": "artifact:release-counts",
                "role": "counts",
            },
        )
    )

    with pytest.raises(ConflictError, match="candidate -> available"):
        service.ingest(
            event_factory(
                "event:release-invalid",
                "release.status_changed",
                {"release_id": "bulk-rna-smoke/2026-07-17", "status": "available"},
            )
        )

    for index, status in enumerate(
        ("staged", "validated", "internal", "publishing", "available"), start=1
    ):
        service.ingest(
            event_factory(
                f"event:release-status-{index}",
                "release.status_changed",
                {"release_id": "bulk-rna-smoke/2026-07-17", "status": status},
            )
        )

    release = service.get_release("bulk-rna-smoke/2026-07-17")
    assert release["status"] == "available"
    assert release["artifacts"][0]["role"] == "counts"
    search = service.search({"query": "normalized", "project": "bulk-rna-smoke"})
    assert search["total"] == 1
    assert search["items"][0]["entity_type"] == "artifact"
    release_search = service.search({"query": "internal release", "entity_types": ["release"]})
    assert release_search["items"][0]["entity_id"] == "bulk-rna-smoke/2026-07-17"
