from __future__ import annotations

from fastapi.testclient import TestClient

from provenance_service.api import create_app
from provenance_service.config import Settings


def test_http_health_auth_idempotency_and_slash_ids(tmp_path, event_factory):
    settings = Settings(
        database_path=tmp_path / "api.sqlite3",
        artifact_root=tmp_path / "artifacts",
        api_token="test-secret",
    )
    with TestClient(create_app(settings)) as client:
        assert client.get("/healthz").json() == {
            "status": "ok",
            "database": True,
            "event_count": 0,
        }
        config = client.get("/v1/config").json()
        assert config["write_auth_required"] is True
        event_types = client.get("/v1/event-types").json()["event_types"]
        assert "artifact.registered" in event_types
        assert "location.recorded" in event_types
        event = event_factory(
            "producer/run:artifact",
            "artifact.registered",
            {
                "artifact_id": "project/run/artifact:counts",
                "name": "counts.tsv",
                "kind": "file",
                "project": "project",
                "status": "verified",
            },
        )
        assert client.post("/v1/events", json=event).status_code == 401
        response = client.post(
            "/v1/events", json=event, headers={"Authorization": "Bearer test-secret"}
        )
        assert response.status_code == 201
        duplicate = client.post(
            "/v1/events", json=event, headers={"Authorization": "Bearer test-secret"}
        )
        assert duplicate.status_code == 200
        assert duplicate.json()["status"] == "duplicate"
        assert client.get("/v1/events/producer/run:artifact").status_code == 200
        artifact = client.get("/v1/artifacts/project/run/artifact:counts")
        assert artifact.status_code == 200
        assert artifact.json()["name"] == "counts.tsv"


def test_http_conflict_validation_not_found_and_batch(tmp_path, event_factory):
    settings = Settings(
        database_path=tmp_path / "api.sqlite3",
        artifact_root=tmp_path / "artifacts",
    )
    with TestClient(create_app(settings)) as client:
        event = event_factory(
            "event:artifact",
            "artifact.registered",
            {
                "artifact_id": "artifact:one",
                "name": "one.tsv",
                "kind": "file",
                "status": "declared",
            },
        )
        batch = client.post("/v1/events/batch", json={"events": [event, event]})
        assert batch.status_code == 200
        assert batch.json()["inserted"] == 1
        assert batch.json()["duplicates"] == 1

        changed = event | {"payload": event["payload"] | {"name": "different.tsv"}}
        conflict = client.post("/v1/events", json=changed)
        assert conflict.status_code == 409
        assert conflict.json()["error"]["code"] == "conflict"

        invalid = event_factory(
            "event:bad-location",
            "location.recorded",
            {
                "location_id": "location:bad",
                "artifact_id": "artifact:one",
                "kind": "local",
                "status": "declared",
                "mapping_revision": 1,
            },
        )
        assert client.post("/v1/events", json=invalid).status_code == 422
        assert client.get("/v1/artifacts/artifact:missing").status_code == 404


def test_openapi_exposes_versioned_contract(tmp_path):
    settings = Settings(
        database_path=tmp_path / "api.sqlite3",
        artifact_root=tmp_path / "artifacts",
    )
    with TestClient(create_app(settings)) as client:
        schema = client.get("/openapi.json").json()
    assert schema["info"]["version"] == "0.1.0"
    assert "/v1/events/batch" in schema["paths"]
    assert "/v1/event-types" in schema["paths"]
    assert "/v1/artifacts/{artifact_id}/lineage" in schema["paths"]
