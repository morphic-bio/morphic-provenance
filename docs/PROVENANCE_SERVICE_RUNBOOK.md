# Provenance Index Service Runbook

## Purpose

The provenance index service makes the append-only records in this repository
queryable without changing their role as the human-auditable source records. It
accepts idempotent provenance events, materializes an artifact and derivation
index, tracks mutable storage locations separately from artifact identity, and
coordinates artifacts with internal dataset releases.

This first implementation is standalone. Workbench integration is deliberately
out of scope until the service API, persistence behavior, and failure handling
have passed their repository-local tests.

## Ownership and Process Model

`morphic-provenance` owns:

- event and API contracts;
- the canonical event log and materialized provenance index;
- artifact, activity, derivation, location, transfer, and release records;
- local-path and Globus-location reconciliation;
- future Globus Search projections and post-hoc record importers.

The service is started **with** callers, not as their child process. For local
development it may be one service in a Compose stack. In production, systemd,
Compose, or Kubernetes should independently supervise it and the Workbench.

The intended integration path is:

```text
agent or UI -> Workbench MCP -> provenance HTTP API -> canonical index
                                            |-------> Globus Search projection
```

Workbench must eventually use a durable outbox. A provenance outage must not
stop ordinary workflow execution; events are retried with the same `event_id`.
Release publication may require the provenance service and can fail closed.

## Record Model

The service keeps two layers:

1. An immutable event log containing exactly what a producer reported.
2. Transactionally updated relational views used for queries.

Artifact identity and checksums are immutable once registered. Storage
locations are mutable projections. Every location update remains auditable
because it is driven by an immutable event and requires an increasing
`mapping_revision`. A transfer's source and destination locations must both
belong to the transferred artifact, and later transfer reports cannot decrease
the recorded mapping revision.

The initial event types are:

| Event type | Effect |
| --- | --- |
| `artifact.registered` | Registers immutable artifact identity and metadata. |
| `activity.registered` | Registers a workflow, command, or transfer activity. |
| `derivation.registered` | Connects input artifacts to an output and activity. |
| `location.recorded` | Creates or revises a local, Globus, or other location. |
| `transfer.recorded` | Records an immutable transfer receipt or status report. |
| `release.registered` | Creates an internal dataset release. |
| `release.artifact_added` | Adds an artifact to a release with a role. |
| `release.status_changed` | Advances or fails a release. |

Release states advance through:

```text
candidate -> staged -> validated -> internal -> publishing -> available
```

Any nonterminal state may move to `failed`. A failed release may return to
`staged` after an explicit new status event. Membership and transfer receipts
are append-only.

## Event Envelope

Producers POST one envelope or a batch of envelopes. Timestamps must include a
UTC offset. IDs are producer-assigned and stable across retries.

```json
{
  "event_id": "run-42:counts:artifact",
  "event_type": "artifact.registered",
  "occurred_at": "2026-07-17T12:00:00Z",
  "actor": "bulk-rna-build",
  "source": "morphic-recipes",
  "payload": {
    "artifact_id": "sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
    "name": "gene-counts.tsv",
    "kind": "file",
    "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
    "bytes": 1024,
    "status": "verified",
    "project": "bulk-rna-smoke",
    "metadata": {}
  }
}
```

Reposting the same `event_id` and content is a successful duplicate. Reusing an
ID with different content returns HTTP 409. A batch is one transaction: either
all new events and projections commit or none do.

Build and transfer scripts should also write the same envelopes as JSON Lines.
That sidecar is the recovery path when the service is unavailable. Scripts must
not write directly to the service database.

## HTTP API

The initial API is versioned under `/v1`:

- `GET /healthz`: process and database readiness.
- `GET /v1/config`: nonsecret runtime paths and feature state.
- `GET /v1/event-types`: producer-facing payload schemas.
- `POST /v1/events`: ingest one event.
- `POST /v1/events/batch`: transactionally ingest a batch.
- `GET /v1/events/{event_id}`: inspect an immutable event.
- `GET /v1/artifacts/{artifact_id}`: artifact plus current locations.
- `GET /v1/artifacts/{artifact_id}/lineage`: upstream or downstream lineage.
- `POST /v1/search`: search artifacts and releases.
- `GET /v1/releases/{release_id}`: release and artifact membership.
- `POST /v1/locations/{location_id}/reconcile`: check a local location.

The service does not serve artifact payloads. It returns paths and collection
coordinates subject to authorization; Globus or the underlying storage system
serves bytes.

## Configuration

Configuration is supplied through environment variables:

| Variable | Default | Meaning |
| --- | --- | --- |
| `PROVENANCE_DATABASE_PATH` | `./var/provenance.sqlite3` | SQLite index path for this standalone phase. |
| `PROVENANCE_ARTIFACT_ROOT` | `./var/globus-artifacts` | Local root exposed by a Globus collection. |
| `PROVENANCE_API_TOKEN` | unset | Bearer token required for mutation endpoints when set. |
| `PROVENANCE_BIND_HOST` | `127.0.0.1` | HTTP listen address. |
| `PROVENANCE_PORT` | `8090` | HTTP listen port. |

SQLite is intentional for repository-local development and tests. Before a
multi-replica production deployment, persistence must move to PostgreSQL while
preserving the event contract and idempotency tests.

## Install and Start

From the repository root:

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[test]'
export PROVENANCE_DATABASE_PATH="$PWD/var/provenance.sqlite3"
export PROVENANCE_ARTIFACT_ROOT=/mnt/pikachu/globus_uploads/morphic-provenance-artifacts
.venv/bin/morphic-provenance init
.venv/bin/morphic-provenance serve
```

The `init` command creates the database schema and artifact-root marker. It
refuses to use a non-directory path. The service also initializes an empty
database on startup, but explicit initialization is preferred operationally.

## Globus Artifact Root

On Pikachu, the standalone service uses:

```text
/mnt/pikachu/globus_uploads/morphic-provenance-artifacts
```

This is a **collection-visible local directory**, not a FUSE mount and not a
new filesystem mount. A Globus administrator must include it in an existing
collection's permitted paths or configure a collection rooted there. Record the
resulting collection UUID in location events; do not infer it from the local
path.

The current Pikachu Globus Connect Personal endpoint is:

```text
collection UUID: 07446cad-33b8-11f0-8c0c-0afffb017b7d
collection path: /mnt/pikachu/globus_uploads/morphic-provenance-artifacts/
```

Its local path policy includes `/mnt/pikachu/`. The collection path was verified
with `globus ls`; it returned `incoming/`, `quarantine/`, and `releases/`. The
endpoint may normally be disconnected and must be running before transfer or
listing operations.

Initialize and verify the directory with:

```bash
PROVENANCE_ARTIFACT_ROOT=/mnt/pikachu/globus_uploads/morphic-provenance-artifacts \
  morphic-provenance init
test -w /mnt/pikachu/globus_uploads/morphic-provenance-artifacts
globus ls '07446cad-33b8-11f0-8c0c-0afffb017b7d:/mnt/pikachu/globus_uploads/morphic-provenance-artifacts/'
```

Recommended layout:

```text
morphic-provenance-artifacts/
  incoming/       transfer staging before validation
  releases/       immutable release payload layouts
  quarantine/     failed checksum or policy validation
  .provenance-root.json
```

Payloads and database files are excluded from Git.

## Ingest JSONL

To recover sidecars or test a producer contract:

```bash
morphic-provenance ingest-jsonl path/to/provenance.events.jsonl
```

The command uses the same validation, transaction, and idempotency behavior as
the HTTP batch endpoint.

## Import Existing Repository Records

Canonical `runs/*/*/run.json` records can be indexed post-hoc:

```bash
morphic-provenance import-repository . --dry-run
morphic-provenance import-repository .
```

The importer is deterministic, so rerunning it produces duplicate event IDs
rather than duplicate records. It creates one workflow activity per run,
artifacts and locations for the top-level input/output inventories, derivations
from every recorded input to each output, and candidate release memberships
from `dataset_releases` references.

An absolute path described as a Globus destination but lacking a collection
UUID is indexed as an unresolved archive URI. The importer does not invent a
collection identity. A later `location.recorded` event should add a distinct
proper Globus location once the collection UUID is known.

Files that do not have the canonical run-record shape are reported and skipped.
The importer never modifies source records.

## Smoke Test

```bash
pytest
morphic-provenance init
uvicorn provenance_service.api:create_app --factory --host 127.0.0.1 --port 8090
curl -fsS http://127.0.0.1:8090/healthz
```

Then ingest a fixture and query it:

```bash
morphic-provenance ingest-jsonl tests/fixtures/example.events.jsonl
curl -fsS http://127.0.0.1:8090/v1/artifacts/artifact:normalized-counts
curl -fsS 'http://127.0.0.1:8090/v1/artifacts/artifact:normalized-counts/lineage?direction=upstream'
```

## Reconciliation

Local reconciliation resolves a `file://` location, verifies that it is inside
the configured artifact root, and reports existence, byte size, modification
time, and an optional SHA-256 comparison. It never mutates the artifact record
silently. Its result is returned to the caller; a producer records any desired
status change with a new `location.recorded` revision.

Globus task polling and Globus Search projection are later adapters. They must
write ordinary transfer and location events rather than bypassing the event
log.

## Backup and Recovery

For standalone SQLite deployments:

1. Stop writes or use SQLite's online backup API.
2. Back up `PROVENANCE_DATABASE_PATH` and its permissions.
3. Preserve producer JSONL sidecars with the associated run record.
4. Restore the database, start the service, and replay missing sidecars.
5. Compare event counts and reconcile release locations.

The Git run records remain independently readable if the index is lost. The
index can be rebuilt by future post-hoc importers plus producer sidecars.

## Security

- Bind to loopback unless a trusted reverse proxy provides TLS and identity.
- Set `PROVENANCE_API_TOKEN` for any shared deployment.
- Treat artifact paths, collection IDs, and release membership as potentially
  restricted metadata.
- Do not place tokens, Globus refresh tokens, or endpoint secrets in events.
- Restrict artifact-root permissions to service and transfer identities.
- Do not expose SQLite over a shared network filesystem.

## Promotion Gates

Workbench integration starts only after all of these pass:

1. Unit and API tests pass from a clean checkout.
2. Duplicate delivery and conflicting-ID behavior are verified.
3. Location revisions and path-containment checks are verified.
4. Lineage traversal and release transitions are verified.
5. The Pikachu artifact root is writable and marked.
6. A manual HTTP smoke test starts and stops cleanly.
7. Review confirms existing completed run records were not modified.
