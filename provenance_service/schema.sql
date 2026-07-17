PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);

INSERT OR IGNORE INTO schema_migrations(version, applied_at)
VALUES (1, strftime('%Y-%m-%dT%H:%M:%fZ', 'now'));

CREATE TABLE IF NOT EXISTS events (
    event_id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    actor TEXT NOT NULL,
    source TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    envelope_json TEXT NOT NULL,
    content_sha256 TEXT NOT NULL,
    ingested_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_events_type_time ON events(event_type, occurred_at);
CREATE INDEX IF NOT EXISTS idx_events_source_time ON events(source, occurred_at);

CREATE TABLE IF NOT EXISTS artifacts (
    artifact_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    kind TEXT NOT NULL,
    project TEXT,
    sha256 TEXT,
    bytes INTEGER,
    media_type TEXT,
    status TEXT NOT NULL,
    metadata_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    created_event_id TEXT NOT NULL REFERENCES events(event_id)
);

CREATE INDEX IF NOT EXISTS idx_artifacts_name ON artifacts(name);
CREATE INDEX IF NOT EXISTS idx_artifacts_project ON artifacts(project);
CREATE INDEX IF NOT EXISTS idx_artifacts_sha256 ON artifacts(sha256);

CREATE TABLE IF NOT EXISTS activities (
    activity_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    kind TEXT NOT NULL,
    project TEXT,
    run_id TEXT,
    workflow_id TEXT,
    status TEXT NOT NULL,
    started_at TEXT,
    ended_at TEXT,
    metadata_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    created_event_id TEXT NOT NULL REFERENCES events(event_id)
);

CREATE INDEX IF NOT EXISTS idx_activities_run ON activities(run_id);
CREATE INDEX IF NOT EXISTS idx_activities_workflow ON activities(workflow_id);

CREATE TABLE IF NOT EXISTS derivations (
    output_artifact_id TEXT NOT NULL REFERENCES artifacts(artifact_id),
    input_artifact_id TEXT NOT NULL REFERENCES artifacts(artifact_id),
    activity_id TEXT NOT NULL REFERENCES activities(activity_id),
    relation TEXT NOT NULL,
    event_id TEXT NOT NULL REFERENCES events(event_id),
    PRIMARY KEY (output_artifact_id, input_artifact_id, activity_id, relation)
);

CREATE INDEX IF NOT EXISTS idx_derivations_input ON derivations(input_artifact_id);
CREATE INDEX IF NOT EXISTS idx_derivations_activity ON derivations(activity_id);

CREATE TABLE IF NOT EXISTS locations (
    location_id TEXT PRIMARY KEY,
    artifact_id TEXT NOT NULL REFERENCES artifacts(artifact_id),
    kind TEXT NOT NULL,
    uri TEXT,
    local_path TEXT,
    collection_id TEXT,
    collection_path TEXT,
    status TEXT NOT NULL,
    mapping_revision INTEGER NOT NULL,
    sha256 TEXT,
    bytes INTEGER,
    verified_at TEXT,
    metadata_json TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    event_id TEXT NOT NULL REFERENCES events(event_id)
);

CREATE INDEX IF NOT EXISTS idx_locations_artifact ON locations(artifact_id);
CREATE INDEX IF NOT EXISTS idx_locations_collection ON locations(collection_id, collection_path);

CREATE TABLE IF NOT EXISTS transfers (
    transfer_id TEXT PRIMARY KEY,
    report_revision INTEGER NOT NULL,
    artifact_id TEXT NOT NULL REFERENCES artifacts(artifact_id),
    source_location_id TEXT NOT NULL REFERENCES locations(location_id),
    destination_location_id TEXT NOT NULL REFERENCES locations(location_id),
    mapping_revision INTEGER NOT NULL,
    status TEXT NOT NULL,
    task_id TEXT,
    sha256 TEXT,
    bytes INTEGER,
    started_at TEXT,
    completed_at TEXT,
    metadata_json TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    event_id TEXT NOT NULL REFERENCES events(event_id)
);

CREATE INDEX IF NOT EXISTS idx_transfers_artifact ON transfers(artifact_id);
CREATE INDEX IF NOT EXISTS idx_transfers_task ON transfers(task_id);

CREATE TABLE IF NOT EXISTS releases (
    release_id TEXT PRIMARY KEY,
    project TEXT NOT NULL,
    name TEXT NOT NULL,
    status TEXT NOT NULL,
    status_reason TEXT,
    metadata_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    event_id TEXT NOT NULL REFERENCES events(event_id)
);

CREATE INDEX IF NOT EXISTS idx_releases_project ON releases(project);
CREATE INDEX IF NOT EXISTS idx_releases_status ON releases(status);

CREATE TABLE IF NOT EXISTS release_memberships (
    release_id TEXT NOT NULL REFERENCES releases(release_id),
    artifact_id TEXT NOT NULL REFERENCES artifacts(artifact_id),
    role TEXT NOT NULL,
    event_id TEXT NOT NULL REFERENCES events(event_id),
    added_at TEXT NOT NULL,
    PRIMARY KEY (release_id, artifact_id, role)
);

CREATE INDEX IF NOT EXISTS idx_release_memberships_artifact
ON release_memberships(artifact_id);
