from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from .config import Settings
from .database import Database
from .errors import ConflictError, NotFoundError, UnsafePathError
from .models import (
    ActivityRegistered,
    ArtifactRegistered,
    DerivationRegistered,
    EventEnvelope,
    LocationRecorded,
    ReleaseArtifactAdded,
    ReleaseRegistered,
    ReleaseStatusChanged,
    SearchRequest,
    TransferRecorded,
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _row(row: sqlite3.Row) -> dict[str, Any]:
    result = dict(row)
    for key in tuple(result):
        if key.endswith("_json"):
            result[key.removesuffix("_json")] = json.loads(result.pop(key))
    return result


class ProvenanceService:
    RELEASE_TRANSITIONS: dict[str, set[str]] = {
        "candidate": {"staged", "failed"},
        "staged": {"validated", "failed"},
        "validated": {"internal", "failed"},
        "internal": {"publishing", "failed"},
        "publishing": {"available", "failed"},
        "available": set(),
        "failed": {"staged"},
    }
    TRANSFER_TRANSITIONS: dict[str, set[str]] = {
        "requested": {"requested", "active", "succeeded", "failed", "cancelled"},
        "active": {"active", "succeeded", "failed", "cancelled"},
        "succeeded": {"succeeded"},
        "failed": {"failed"},
        "cancelled": {"cancelled"},
    }

    def __init__(self, settings: Settings, database: Database | None = None):
        self.settings = settings
        self.database = database or Database(settings.database_path)

    def initialize(self) -> None:
        self.settings.initialize_artifact_root()
        self.database.initialize()

    def health(self) -> dict[str, Any]:
        with self.database.read() as connection:
            event_count = connection.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        return {"status": "ok", "database": self.database.health(), "event_count": event_count}

    def ingest(self, envelope: EventEnvelope | dict[str, Any]) -> dict[str, Any]:
        return self.ingest_batch([envelope])[0]

    def ingest_batch(
        self, envelopes: list[EventEnvelope | dict[str, Any]]
    ) -> list[dict[str, Any]]:
        if not envelopes:
            raise ValueError("event batch cannot be empty")
        parsed = [
            envelope if isinstance(envelope, EventEnvelope) else EventEnvelope.model_validate(envelope)
            for envelope in envelopes
        ]
        prepared = [
            (event, event.parsed_payload(), event.normalized(), event.content_hash())
            for event in parsed
        ]

        results: list[dict[str, Any]] = []
        try:
            with self.database.write() as connection:
                for event, payload, normalized, content_hash in prepared:
                    existing = connection.execute(
                        "SELECT content_sha256 FROM events WHERE event_id = ?", (event.event_id,)
                    ).fetchone()
                    if existing:
                        if existing["content_sha256"] != content_hash:
                            raise ConflictError(
                                f"event_id {event.event_id!r} already has different content"
                            )
                        results.append({"event_id": event.event_id, "status": "duplicate"})
                        continue

                    connection.execute(
                        """
                        INSERT INTO events(
                            event_id, event_type, occurred_at, actor, source,
                            payload_json, envelope_json, content_sha256, ingested_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            event.event_id,
                            event.event_type,
                            normalized["occurred_at"],
                            event.actor,
                            event.source,
                            _json(normalized["payload"]),
                            _json(normalized),
                            content_hash,
                            _utc_now(),
                        ),
                    )
                    self._project(connection, event, payload)
                    results.append({"event_id": event.event_id, "status": "inserted"})
        except sqlite3.IntegrityError as exc:
            raise ConflictError(f"event projection violates a reference or uniqueness rule: {exc}") from exc
        return results

    def _project(self, connection: sqlite3.Connection, event: EventEnvelope, payload: Any) -> None:
        if isinstance(payload, ArtifactRegistered):
            self._register_artifact(connection, event, payload)
        elif isinstance(payload, ActivityRegistered):
            self._register_activity(connection, event, payload)
        elif isinstance(payload, DerivationRegistered):
            self._register_derivation(connection, event, payload)
        elif isinstance(payload, LocationRecorded):
            self._record_location(connection, event, payload)
        elif isinstance(payload, TransferRecorded):
            self._record_transfer(connection, event, payload)
        elif isinstance(payload, ReleaseRegistered):
            self._register_release(connection, event, payload)
        elif isinstance(payload, ReleaseArtifactAdded):
            self._add_release_artifact(connection, event, payload)
        elif isinstance(payload, ReleaseStatusChanged):
            self._change_release_status(connection, event, payload)
        else:
            raise TypeError(f"unsupported payload model: {type(payload).__name__}")

    def _register_artifact(
        self, connection: sqlite3.Connection, event: EventEnvelope, payload: ArtifactRegistered
    ) -> None:
        existing = connection.execute(
            "SELECT * FROM artifacts WHERE artifact_id = ?", (payload.artifact_id,)
        ).fetchone()
        values = (
            payload.name,
            payload.kind,
            payload.project,
            payload.sha256.lower() if payload.sha256 else None,
            payload.size_bytes,
            payload.media_type,
            payload.status,
            _json(payload.metadata),
        )
        if existing:
            current = (
                existing["name"],
                existing["kind"],
                existing["project"],
                existing["sha256"],
                existing["bytes"],
                existing["media_type"],
                existing["status"],
                existing["metadata_json"],
            )
            if current != values:
                raise ConflictError(
                    f"artifact_id {payload.artifact_id!r} is already registered differently"
                )
            return
        connection.execute(
            """
            INSERT INTO artifacts(
                artifact_id, name, kind, project, sha256, bytes, media_type,
                status, metadata_json, created_at, created_event_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (payload.artifact_id, *values, event.normalized()["occurred_at"], event.event_id),
        )

    def _register_activity(
        self, connection: sqlite3.Connection, event: EventEnvelope, payload: ActivityRegistered
    ) -> None:
        existing = connection.execute(
            "SELECT activity_id FROM activities WHERE activity_id = ?", (payload.activity_id,)
        ).fetchone()
        if existing:
            raise ConflictError(f"activity_id {payload.activity_id!r} is already registered")
        connection.execute(
            """
            INSERT INTO activities(
                activity_id, name, kind, project, run_id, workflow_id, status,
                started_at, ended_at, metadata_json, created_at, created_event_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.activity_id,
                payload.name,
                payload.kind,
                payload.project,
                payload.run_id,
                payload.workflow_id,
                payload.status,
                payload.started_at.isoformat() if payload.started_at else None,
                payload.ended_at.isoformat() if payload.ended_at else None,
                _json(payload.metadata),
                event.normalized()["occurred_at"],
                event.event_id,
            ),
        )

    def _register_derivation(
        self, connection: sqlite3.Connection, event: EventEnvelope, payload: DerivationRegistered
    ) -> None:
        for input_id in payload.input_artifact_ids:
            connection.execute(
                """
                INSERT INTO derivations(
                    output_artifact_id, input_artifact_id, activity_id, relation, event_id
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    payload.output_artifact_id,
                    input_id,
                    payload.activity_id,
                    payload.relation,
                    event.event_id,
                ),
            )

    def _record_location(
        self, connection: sqlite3.Connection, event: EventEnvelope, payload: LocationRecorded
    ) -> None:
        existing = connection.execute(
            "SELECT * FROM locations WHERE location_id = ?", (payload.location_id,)
        ).fetchone()
        uri = payload.uri
        if uri is None and payload.kind == "local":
            uri = f"file://{payload.local_path}"
        elif uri is None and payload.kind == "globus":
            uri = f"globus://{payload.collection_id}{payload.collection_path}"
        values = (
            uri,
            payload.local_path,
            payload.collection_id,
            payload.collection_path,
            payload.status,
            payload.mapping_revision,
            payload.sha256.lower() if payload.sha256 else None,
            payload.size_bytes,
            payload.verified_at.isoformat() if payload.verified_at else None,
            _json(payload.metadata),
            event.normalized()["occurred_at"],
            event.event_id,
        )
        if existing:
            if existing["artifact_id"] != payload.artifact_id or existing["kind"] != payload.kind:
                raise ConflictError("location identity cannot change artifact or kind")
            if payload.mapping_revision <= existing["mapping_revision"]:
                raise ConflictError(
                    "location mapping_revision must be greater than the current revision"
                )
            connection.execute(
                """
                UPDATE locations SET
                    uri = ?, local_path = ?, collection_id = ?, collection_path = ?,
                    status = ?, mapping_revision = ?, sha256 = ?, bytes = ?, verified_at = ?,
                    metadata_json = ?, updated_at = ?, event_id = ?
                WHERE location_id = ?
                """,
                (*values, payload.location_id),
            )
        else:
            connection.execute(
                """
                INSERT INTO locations(
                    location_id, artifact_id, kind, uri, local_path, collection_id,
                    collection_path, status, mapping_revision, sha256, bytes,
                    verified_at, metadata_json, updated_at, event_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (payload.location_id, payload.artifact_id, payload.kind, *values),
            )

    def _record_transfer(
        self, connection: sqlite3.Connection, event: EventEnvelope, payload: TransferRecorded
    ) -> None:
        existing = connection.execute(
            "SELECT * FROM transfers WHERE transfer_id = ?", (payload.transfer_id,)
        ).fetchone()
        values = (
            payload.report_revision,
            payload.mapping_revision,
            payload.status,
            payload.task_id,
            payload.sha256.lower() if payload.sha256 else None,
            payload.size_bytes,
            payload.started_at.isoformat() if payload.started_at else None,
            payload.completed_at.isoformat() if payload.completed_at else None,
            _json(payload.metadata),
            event.normalized()["occurred_at"],
            event.event_id,
        )
        if existing:
            immutable = (
                existing["artifact_id"],
                existing["source_location_id"],
                existing["destination_location_id"],
            )
            requested = (
                payload.artifact_id,
                payload.source_location_id,
                payload.destination_location_id,
            )
            if immutable != requested:
                raise ConflictError("transfer identity cannot change artifact or locations")
            if payload.report_revision <= existing["report_revision"]:
                raise ConflictError("transfer report_revision must increase")
            if payload.status not in self.TRANSFER_TRANSITIONS[existing["status"]]:
                raise ConflictError(
                    f"invalid transfer transition: {existing['status']} -> {payload.status}"
                )
            connection.execute(
                """
                UPDATE transfers SET
                    report_revision = ?, mapping_revision = ?, status = ?, task_id = ?,
                    sha256 = ?, bytes = ?, started_at = ?, completed_at = ?,
                    metadata_json = ?, updated_at = ?, event_id = ?
                WHERE transfer_id = ?
                """,
                (*values, payload.transfer_id),
            )
        else:
            connection.execute(
                """
                INSERT INTO transfers(
                    transfer_id, artifact_id, source_location_id, destination_location_id,
                    report_revision, mapping_revision, status, task_id, sha256, bytes,
                    started_at, completed_at, metadata_json, updated_at, event_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload.transfer_id,
                    payload.artifact_id,
                    payload.source_location_id,
                    payload.destination_location_id,
                    *values,
                ),
            )

    def _register_release(
        self, connection: sqlite3.Connection, event: EventEnvelope, payload: ReleaseRegistered
    ) -> None:
        if connection.execute(
            "SELECT release_id FROM releases WHERE release_id = ?", (payload.release_id,)
        ).fetchone():
            raise ConflictError(f"release_id {payload.release_id!r} is already registered")
        occurred_at = event.normalized()["occurred_at"]
        connection.execute(
            """
            INSERT INTO releases(
                release_id, project, name, status, status_reason, metadata_json,
                created_at, updated_at, event_id
            ) VALUES (?, ?, ?, ?, NULL, ?, ?, ?, ?)
            """,
            (
                payload.release_id,
                payload.project,
                payload.name,
                payload.status,
                _json(payload.metadata),
                occurred_at,
                occurred_at,
                event.event_id,
            ),
        )

    def _add_release_artifact(
        self, connection: sqlite3.Connection, event: EventEnvelope, payload: ReleaseArtifactAdded
    ) -> None:
        connection.execute(
            """
            INSERT INTO release_memberships(release_id, artifact_id, role, event_id, added_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                payload.release_id,
                payload.artifact_id,
                payload.role,
                event.event_id,
                event.normalized()["occurred_at"],
            ),
        )

    def _change_release_status(
        self, connection: sqlite3.Connection, event: EventEnvelope, payload: ReleaseStatusChanged
    ) -> None:
        existing = connection.execute(
            "SELECT status FROM releases WHERE release_id = ?", (payload.release_id,)
        ).fetchone()
        if not existing:
            raise ConflictError(f"release_id {payload.release_id!r} is not registered")
        current = existing["status"]
        if payload.status not in self.RELEASE_TRANSITIONS[current]:
            raise ConflictError(f"invalid release transition: {current} -> {payload.status}")
        connection.execute(
            """
            UPDATE releases
            SET status = ?, status_reason = ?, updated_at = ?, event_id = ?
            WHERE release_id = ?
            """,
            (
                payload.status,
                payload.reason,
                event.normalized()["occurred_at"],
                event.event_id,
                payload.release_id,
            ),
        )

    def get_event(self, event_id: str) -> dict[str, Any]:
        with self.database.read() as connection:
            record = connection.execute(
                "SELECT envelope_json, ingested_at, content_sha256 FROM events WHERE event_id = ?",
                (event_id,),
            ).fetchone()
        if not record:
            raise NotFoundError(f"event {event_id!r} was not found")
        result = json.loads(record["envelope_json"])
        result["ingested_at"] = record["ingested_at"]
        result["content_sha256"] = record["content_sha256"]
        return result

    def get_artifact(self, artifact_id: str) -> dict[str, Any]:
        with self.database.read() as connection:
            artifact = connection.execute(
                "SELECT * FROM artifacts WHERE artifact_id = ?", (artifact_id,)
            ).fetchone()
            if not artifact:
                raise NotFoundError(f"artifact {artifact_id!r} was not found")
            locations = connection.execute(
                "SELECT * FROM locations WHERE artifact_id = ? ORDER BY kind, location_id",
                (artifact_id,),
            ).fetchall()
            transfers = connection.execute(
                "SELECT * FROM transfers WHERE artifact_id = ? ORDER BY transfer_id",
                (artifact_id,),
            ).fetchall()
            releases = connection.execute(
                """
                SELECT r.release_id, r.project, r.name, r.status, m.role, m.added_at
                FROM release_memberships m
                JOIN releases r ON r.release_id = m.release_id
                WHERE m.artifact_id = ?
                ORDER BY r.release_id, m.role
                """,
                (artifact_id,),
            ).fetchall()
        result = _row(artifact)
        result["locations"] = [_row(item) for item in locations]
        result["transfers"] = [_row(item) for item in transfers]
        result["releases"] = [dict(item) for item in releases]
        return result

    def lineage(
        self,
        artifact_id: str,
        direction: Literal["upstream", "downstream"] = "upstream",
        max_depth: int = 10,
    ) -> dict[str, Any]:
        if max_depth < 1 or max_depth > 20:
            raise ValueError("max_depth must be between 1 and 20")
        with self.database.read() as connection:
            if not connection.execute(
                "SELECT 1 FROM artifacts WHERE artifact_id = ?", (artifact_id,)
            ).fetchone():
                raise NotFoundError(f"artifact {artifact_id!r} was not found")

            seen = {artifact_id}
            frontier = {artifact_id}
            edges: dict[tuple[str, str, str, str], dict[str, Any]] = {}
            depth_by_id = {artifact_id: 0}
            for depth in range(1, max_depth + 1):
                if not frontier:
                    break
                placeholders = ",".join("?" for _ in frontier)
                field = "output_artifact_id" if direction == "upstream" else "input_artifact_id"
                rows = connection.execute(
                    f"SELECT * FROM derivations WHERE {field} IN ({placeholders})",
                    tuple(sorted(frontier)),
                ).fetchall()
                next_frontier: set[str] = set()
                for item in rows:
                    edge = dict(item)
                    key = (
                        edge["input_artifact_id"],
                        edge["output_artifact_id"],
                        edge["activity_id"],
                        edge["relation"],
                    )
                    edges[key] = edge
                    next_id = (
                        edge["input_artifact_id"]
                        if direction == "upstream"
                        else edge["output_artifact_id"]
                    )
                    if next_id not in seen:
                        seen.add(next_id)
                        depth_by_id[next_id] = depth
                        next_frontier.add(next_id)
                frontier = next_frontier

            placeholders = ",".join("?" for _ in seen)
            nodes = connection.execute(
                f"""
                SELECT artifact_id, name, kind, project, sha256, bytes, media_type, status
                FROM artifacts WHERE artifact_id IN ({placeholders})
                """,
                tuple(sorted(seen)),
            ).fetchall()
        node_list = [dict(item) | {"depth": depth_by_id[item["artifact_id"]]} for item in nodes]
        node_list.sort(key=lambda item: (item["depth"], item["artifact_id"]))
        return {
            "root_artifact_id": artifact_id,
            "direction": direction,
            "max_depth": max_depth,
            "nodes": node_list,
            "edges": sorted(edges.values(), key=lambda item: tuple(str(v) for v in item.values())),
        }

    def search(self, request: SearchRequest | dict[str, Any]) -> dict[str, Any]:
        query = request if isinstance(request, SearchRequest) else SearchRequest.model_validate(request)
        escaped = query.query.lower().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        pattern = f"%{escaped}%"
        items: list[dict[str, Any]] = []
        with self.database.read() as connection:
            if "artifact" in query.entity_types:
                parameters: list[Any] = [pattern, pattern, pattern, pattern]
                project_clause = ""
                if query.project:
                    project_clause = " AND project = ?"
                    parameters.append(query.project)
                rows = connection.execute(
                    f"""
                    SELECT artifact_id AS entity_id, name, project, kind AS subtype,
                           status, sha256, bytes, created_at
                    FROM artifacts
                    WHERE (
                        lower(artifact_id) LIKE ? ESCAPE '\\'
                        OR lower(name) LIKE ? ESCAPE '\\'
                        OR lower(COALESCE(project, '')) LIKE ? ESCAPE '\\'
                        OR lower(metadata_json) LIKE ? ESCAPE '\\'
                    ){project_clause}
                    ORDER BY created_at DESC, artifact_id
                    """,
                    parameters,
                ).fetchall()
                items.extend({"entity_type": "artifact", **dict(item)} for item in rows)
            if "release" in query.entity_types:
                parameters = [pattern, pattern, pattern, pattern]
                project_clause = ""
                if query.project:
                    project_clause = " AND project = ?"
                    parameters.append(query.project)
                rows = connection.execute(
                    f"""
                    SELECT release_id AS entity_id, name, project, 'dataset_release' AS subtype,
                           status, NULL AS sha256, NULL AS bytes, created_at
                    FROM releases
                    WHERE (
                        lower(release_id) LIKE ? ESCAPE '\\'
                        OR lower(name) LIKE ? ESCAPE '\\'
                        OR lower(project) LIKE ? ESCAPE '\\'
                        OR lower(metadata_json) LIKE ? ESCAPE '\\'
                    ){project_clause}
                    ORDER BY created_at DESC, release_id
                    """,
                    parameters,
                ).fetchall()
                items.extend({"entity_type": "release", **dict(item)} for item in rows)
        items.sort(key=lambda item: (item["created_at"], item["entity_type"], item["entity_id"]), reverse=True)
        total = len(items)
        return {"total": total, "items": items[query.offset : query.offset + query.limit]}

    def get_release(self, release_id: str) -> dict[str, Any]:
        with self.database.read() as connection:
            release = connection.execute(
                "SELECT * FROM releases WHERE release_id = ?", (release_id,)
            ).fetchone()
            if not release:
                raise NotFoundError(f"release {release_id!r} was not found")
            members = connection.execute(
                """
                SELECT m.role, m.added_at, a.artifact_id, a.name, a.kind, a.project,
                       a.sha256, a.bytes, a.status
                FROM release_memberships m
                JOIN artifacts a ON a.artifact_id = m.artifact_id
                WHERE m.release_id = ?
                ORDER BY m.role, a.artifact_id
                """,
                (release_id,),
            ).fetchall()
        result = _row(release)
        result["artifacts"] = [dict(item) for item in members]
        return result

    def reconcile_location(self, location_id: str, compute_sha256: bool = False) -> dict[str, Any]:
        with self.database.read() as connection:
            location = connection.execute(
                """
                SELECT l.*, a.sha256 AS artifact_sha256
                FROM locations l JOIN artifacts a ON a.artifact_id = l.artifact_id
                WHERE l.location_id = ?
                """,
                (location_id,),
            ).fetchone()
        if not location:
            raise NotFoundError(f"location {location_id!r} was not found")
        if location["kind"] != "local":
            raise UnsafePathError("only local locations can be reconciled by this adapter")

        root = self.settings.artifact_root.resolve()
        candidate = Path(location["local_path"])
        path = (candidate if candidate.is_absolute() else root / candidate).resolve()
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise UnsafePathError(f"location resolves outside artifact root: {path}") from exc

        exists = path.exists()
        result: dict[str, Any] = {
            "location_id": location_id,
            "artifact_id": location["artifact_id"],
            "path": str(path),
            "exists": exists,
            "kind": "missing",
            "bytes": None,
            "modified_at": None,
            "sha256": None,
            "checksum_match": None,
        }
        if not exists:
            return result
        stat = path.stat()
        result["kind"] = "file" if path.is_file() else "directory" if path.is_dir() else "other"
        result["bytes"] = stat.st_size if path.is_file() else None
        result["modified_at"] = datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat()
        expected = location["sha256"] or location["artifact_sha256"]
        if compute_sha256 and path.is_file():
            digest = hashlib.sha256()
            with path.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
            result["sha256"] = digest.hexdigest()
            result["checksum_match"] = expected is None or digest.hexdigest() == expected.lower()
        return result
