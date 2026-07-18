from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator


Identifier = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=512)]
Sha256 = Annotated[str, StringConstraints(pattern=r"^[0-9a-fA-F]{64}$")]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, populate_by_name=True)


class ArtifactRegistered(StrictModel):
    artifact_id: Identifier
    name: Annotated[str, StringConstraints(min_length=1, max_length=1024)]
    kind: Literal["file", "directory", "bundle", "metadata"]
    project: str | None = None
    sha256: Sha256 | None = None
    size_bytes: int | None = Field(default=None, alias="bytes", ge=0)
    media_type: str | None = None
    status: Literal["declared", "observed", "verified"] = "declared"
    metadata: dict[str, Any] = Field(default_factory=dict)


class ActivityRegistered(StrictModel):
    activity_id: Identifier
    name: Annotated[str, StringConstraints(min_length=1, max_length=1024)]
    kind: Literal["workflow", "command", "transfer", "import", "validation"]
    project: str | None = None
    run_id: str | None = None
    workflow_id: str | None = None
    status: Literal["planned", "running", "complete", "failed"]
    started_at: datetime | None = None
    ended_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_datetimes(self) -> "ActivityRegistered":
        for name in ("started_at", "ended_at"):
            value = getattr(self, name)
            if value is not None and value.utcoffset() is None:
                raise ValueError(f"{name} must include a UTC offset")
        if self.started_at and self.ended_at and self.ended_at < self.started_at:
            raise ValueError("ended_at cannot precede started_at")
        return self


class DerivationRegistered(StrictModel):
    output_artifact_id: Identifier
    input_artifact_ids: list[Identifier] = Field(min_length=1)
    activity_id: Identifier
    relation: Literal["derived_from", "copied_from", "packaged_from"] = "derived_from"

    @model_validator(mode="after")
    def validate_inputs(self) -> "DerivationRegistered":
        if len(self.input_artifact_ids) != len(set(self.input_artifact_ids)):
            raise ValueError("input_artifact_ids must be unique")
        if self.output_artifact_id in self.input_artifact_ids:
            raise ValueError("an artifact cannot derive directly from itself")
        return self


class LocationRecorded(StrictModel):
    location_id: Identifier
    artifact_id: Identifier
    kind: Literal["local", "globus", "object", "archive"]
    uri: str | None = None
    local_path: str | None = None
    collection_id: str | None = None
    collection_path: str | None = None
    status: Literal["declared", "available", "missing", "transferring", "quarantined", "retired"]
    mapping_revision: int = Field(ge=1)
    sha256: Sha256 | None = None
    size_bytes: int | None = Field(default=None, alias="bytes", ge=0)
    verified_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_coordinates(self) -> "LocationRecorded":
        if self.kind == "local" and not self.local_path:
            raise ValueError("local locations require local_path")
        if self.kind == "globus" and not (self.collection_id and self.collection_path):
            raise ValueError("globus locations require collection_id and collection_path")
        if self.verified_at is not None and self.verified_at.utcoffset() is None:
            raise ValueError("verified_at must include a UTC offset")
        return self


class TransferRecorded(StrictModel):
    transfer_id: Identifier
    report_revision: int = Field(ge=1)
    artifact_id: Identifier
    source_location_id: Identifier
    destination_location_id: Identifier
    mapping_revision: int = Field(ge=1)
    status: Literal["requested", "active", "succeeded", "failed", "cancelled"]
    task_id: str | None = None
    sha256: Sha256 | None = None
    size_bytes: int | None = Field(default=None, alias="bytes", ge=0)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_datetimes(self) -> "TransferRecorded":
        for name in ("started_at", "completed_at"):
            value = getattr(self, name)
            if value is not None and value.utcoffset() is None:
                raise ValueError(f"{name} must include a UTC offset")
        if self.started_at and self.completed_at and self.completed_at < self.started_at:
            raise ValueError("completed_at cannot precede started_at")
        if self.source_location_id == self.destination_location_id:
            raise ValueError("source and destination locations must differ")
        return self


ReleaseStatus = Literal[
    "candidate", "staged", "validated", "internal", "publishing", "available", "failed"
]


class ReleaseRegistered(StrictModel):
    release_id: Identifier
    project: Annotated[str, StringConstraints(min_length=1, max_length=512)]
    name: Annotated[str, StringConstraints(min_length=1, max_length=1024)]
    status: Literal["candidate"] = "candidate"
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReleaseArtifactAdded(StrictModel):
    release_id: Identifier
    artifact_id: Identifier
    role: Annotated[str, StringConstraints(min_length=1, max_length=256)] = "payload"


class ReleaseStatusChanged(StrictModel):
    release_id: Identifier
    status: ReleaseStatus
    reason: str | None = None


PayloadModel = (
    ArtifactRegistered
    | ActivityRegistered
    | DerivationRegistered
    | LocationRecorded
    | TransferRecorded
    | ReleaseRegistered
    | ReleaseArtifactAdded
    | ReleaseStatusChanged
)


PAYLOAD_MODELS: dict[str, type[StrictModel]] = {
    "artifact.registered": ArtifactRegistered,
    "activity.registered": ActivityRegistered,
    "derivation.registered": DerivationRegistered,
    "location.recorded": LocationRecorded,
    "transfer.recorded": TransferRecorded,
    "release.registered": ReleaseRegistered,
    "release.artifact_added": ReleaseArtifactAdded,
    "release.status_changed": ReleaseStatusChanged,
}


class EventEnvelope(StrictModel):
    event_id: Identifier
    event_type: Literal[
        "artifact.registered",
        "activity.registered",
        "derivation.registered",
        "location.recorded",
        "transfer.recorded",
        "release.registered",
        "release.artifact_added",
        "release.status_changed",
    ]
    occurred_at: datetime
    actor: Annotated[str, StringConstraints(min_length=1, max_length=512)]
    source: Annotated[str, StringConstraints(min_length=1, max_length=512)]
    payload: dict[str, Any]

    @model_validator(mode="after")
    def validate_occurred_at(self) -> "EventEnvelope":
        if self.occurred_at.utcoffset() is None:
            raise ValueError("occurred_at must include a UTC offset")
        self.parsed_payload()
        return self

    def parsed_payload(self) -> PayloadModel:
        return PAYLOAD_MODELS[self.event_type].model_validate(self.payload)

    def normalized(self) -> dict[str, Any]:
        payload = self.parsed_payload()
        data = self.model_dump(mode="json", exclude={"payload"})
        data["payload"] = payload.model_dump(mode="json", by_alias=True, exclude_none=True)
        return data

    def content_hash(self) -> str:
        canonical = json.dumps(
            self.normalized(), sort_keys=True, separators=(",", ":"), ensure_ascii=True
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class EventBatch(StrictModel):
    events: list[EventEnvelope] = Field(min_length=1, max_length=1000)


class SearchRequest(StrictModel):
    query: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=512)]
    entity_types: list[Literal["artifact", "release"]] = Field(
        default_factory=lambda: ["artifact", "release"]
    )
    project: str | None = None
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def validate_entity_types(self) -> "SearchRequest":
        if not self.entity_types:
            raise ValueError("entity_types cannot be empty")
        self.entity_types = list(dict.fromkeys(self.entity_types))
        return self
