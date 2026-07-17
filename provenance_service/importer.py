from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .models import EventEnvelope


REQUIRED_RUN_FIELDS = {
    "schema_version",
    "run_id",
    "project",
    "created_utc",
    "status",
    "star_suite",
    "recipes",
    "environment",
    "inputs",
    "outputs",
}
SHA256_PATTERN = re.compile(r"^[0-9a-fA-F]{64}$")


@dataclass(frozen=True)
class ImportPlan:
    events: list[EventEnvelope]
    records: int
    skipped: list[dict[str, str]]


def _event(event_id: str, event_type: str, occurred_at: str, payload: dict[str, Any]) -> dict:
    return {
        "event_id": event_id,
        "event_type": event_type,
        "occurred_at": occurred_at,
        "actor": "repository-importer",
        "source": "morphic-provenance",
        "payload": payload,
    }


def _is_globus_destination(name: str, path: str, retention: str) -> bool:
    description = f"{name} {retention}".lower()
    if "globus" in description:
        return True
    local_prefixes = ("/mnt/", "/home/", "/tmp/", "/data/", "/srv/", "/scratch/")
    return path.startswith("/") and not path.startswith(local_prefixes)


def _artifact_kind(path: str, checksum: str | None, size: int | None) -> str:
    if checksum or size is not None or Path(path).suffix:
        return "file"
    return "directory"


def _activity_status(status: str) -> str:
    if status == "corrected":
        return "complete"
    if status in {"planned", "running", "complete", "failed"}:
        return status
    return "failed"


def _canonical_record(record: Any) -> tuple[bool, str]:
    if not isinstance(record, dict):
        return False, "record is not a JSON object"
    missing = sorted(REQUIRED_RUN_FIELDS - record.keys())
    if missing:
        return False, f"missing required fields: {', '.join(missing)}"
    if not isinstance(record["inputs"], list) or not isinstance(record["outputs"], list):
        return False, "inputs and outputs must be arrays"
    return True, ""


def build_repository_events(repository_root: Path) -> ImportPlan:
    root = repository_root.resolve()
    run_root = root / "runs"
    if not run_root.is_dir():
        raise ValueError(f"repository has no runs directory: {run_root}")

    raw_events: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    records = 0
    registered_releases: set[str] = set()
    for record_path in sorted(run_root.glob("*/*/run.json")):
        relative_record = record_path.relative_to(root).as_posix()
        try:
            record = json.loads(record_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            skipped.append({"record": relative_record, "reason": str(exc)})
            continue
        canonical, reason = _canonical_record(record)
        if not canonical:
            skipped.append({"record": relative_record, "reason": reason})
            continue
        records += 1

        project = str(record["project"])
        run_id = str(record["run_id"])
        occurred_at = str(record["created_utc"])
        activity_id = f"activity:run/{project}/{run_id}"
        prefix = f"repo-import:{relative_record}"
        recipes = record.get("recipes") or {}
        raw_events.append(
            _event(
                f"{prefix}:activity",
                "activity.registered",
                occurred_at,
                {
                    "activity_id": activity_id,
                    "name": f"{project} {run_id}",
                    "kind": "workflow",
                    "project": project,
                    "run_id": run_id,
                    "workflow_id": recipes.get("workflow_id") or None,
                    "status": _activity_status(str(record["status"])),
                    "metadata": {
                        "source_record": relative_record,
                        "star_suite": record.get("star_suite", {}),
                        "recipes": recipes,
                        "environment": record.get("environment", {}),
                    },
                },
            )
        )

        artifact_ids: dict[str, list[str]] = {"input": [], "output": []}
        for role, field in (("input", "inputs"), ("output", "outputs")):
            for index, file_record in enumerate(record[field]):
                if not isinstance(file_record, dict) or not file_record.get("path"):
                    skipped.append(
                        {
                            "record": relative_record,
                            "reason": f"skipped malformed {role} entry {index}",
                        }
                    )
                    continue
                path_text = str(file_record["path"])
                name = str(file_record.get("name") or Path(path_text).name or f"{role}-{index}")
                checksum_value = file_record.get("sha256")
                checksum = (
                    str(checksum_value).lower()
                    if checksum_value and SHA256_PATTERN.fullmatch(str(checksum_value))
                    else None
                )
                size_value = file_record.get("bytes")
                size = size_value if isinstance(size_value, int) and size_value >= 0 else None
                retention = str(file_record.get("retention") or file_record.get("notes") or "")
                artifact_id = f"artifact:run/{project}/{run_id}/{role}/{index}"
                artifact_ids[role].append(artifact_id)
                artifact_payload: dict[str, Any] = {
                    "artifact_id": artifact_id,
                    "name": name,
                    "kind": _artifact_kind(path_text, checksum, size),
                    "project": project,
                    "status": "verified" if checksum else "observed",
                    "metadata": {
                        "source_record": relative_record,
                        "inventory_role": role,
                        "inventory_ordinal": index,
                        "retention": retention,
                    },
                }
                if checksum:
                    artifact_payload["sha256"] = checksum
                if size is not None:
                    artifact_payload["bytes"] = size
                raw_events.append(
                    _event(
                        f"{prefix}:artifact:{role}:{index}",
                        "artifact.registered",
                        occurred_at,
                        artifact_payload,
                    )
                )

                globus_destination = _is_globus_destination(name, path_text, retention)
                location_payload: dict[str, Any] = {
                    "location_id": f"location:run/{project}/{run_id}/{role}/{index}",
                    "artifact_id": artifact_id,
                    "mapping_revision": 1,
                    "metadata": {"source_record": relative_record},
                }
                if globus_destination:
                    location_payload.update(
                        {
                            "kind": "archive",
                            "uri": f"globus-path:{path_text}",
                            "status": "declared",
                            "metadata": {
                                "source_record": relative_record,
                                "requires_collection_mapping": True,
                            },
                        }
                    )
                else:
                    local_path = Path(path_text)
                    if not local_path.is_absolute():
                        local_path = (record_path.parent / local_path).resolve()
                    location_payload.update(
                        {
                            "kind": "local",
                            "local_path": str(local_path),
                            "status": "available" if local_path.exists() else "missing",
                        }
                    )
                if checksum:
                    location_payload["sha256"] = checksum
                if size is not None:
                    location_payload["bytes"] = size
                raw_events.append(
                    _event(
                        f"{prefix}:location:{role}:{index}",
                        "location.recorded",
                        occurred_at,
                        location_payload,
                    )
                )

        if artifact_ids["input"]:
            for index, output_id in enumerate(artifact_ids["output"]):
                raw_events.append(
                    _event(
                        f"{prefix}:derivation:{index}",
                        "derivation.registered",
                        occurred_at,
                        {
                            "output_artifact_id": output_id,
                            "input_artifact_ids": artifact_ids["input"],
                            "activity_id": activity_id,
                            "relation": "derived_from",
                        },
                    )
                )

        releases = record.get("dataset_releases") or []
        if not isinstance(releases, list):
            skipped.append({"record": relative_record, "reason": "dataset_releases is not an array"})
            continue
        for release in releases:
            if not isinstance(release, dict) or not release.get("release_key"):
                skipped.append({"record": relative_record, "reason": "malformed dataset release"})
                continue
            release_id = str(release["release_key"])
            if release_id not in registered_releases:
                registered_releases.add(release_id)
                release_metadata = {
                    key: value
                    for key, value in release.items()
                    if key not in {"release_key", "release_date"}
                }
                raw_events.append(
                    _event(
                        f"repo-import:release:{release_id}:registered",
                        "release.registered",
                        occurred_at,
                        {
                            "release_id": release_id,
                            "project": project,
                            "name": f"{project} dataset release {release.get('release_date', release_id)}",
                            "status": "candidate",
                            "metadata": release_metadata,
                        },
                    )
                )
            for output_index, output_id in enumerate(artifact_ids["output"]):
                raw_events.append(
                    _event(
                        f"{prefix}:release:{release_id}:output:{output_index}",
                        "release.artifact_added",
                        occurred_at,
                        {
                            "release_id": release_id,
                            "artifact_id": output_id,
                            "role": "recorded_output",
                        },
                    )
                )

    events_by_id: dict[str, EventEnvelope] = {}
    for raw_event in raw_events:
        event = EventEnvelope.model_validate(raw_event)
        previous = events_by_id.get(event.event_id)
        if previous and previous.content_hash() != event.content_hash():
            raise ValueError(f"import generated conflicting event_id: {event.event_id}")
        events_by_id[event.event_id] = event
    return ImportPlan(events=list(events_by_id.values()), records=records, skipped=skipped)
