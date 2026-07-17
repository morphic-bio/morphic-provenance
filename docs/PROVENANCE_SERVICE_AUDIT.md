# Provenance Service Audit

Audit date: 2026-07-17

## Scope

This review covered the repository state before the provenance index service,
the existing tracked run-record corpus and schema, the newly added standalone
service, and the Pikachu artifact-root configuration. Workbench integration was
excluded by design.

## Original Repository Review

The original repository was a static, append-only provenance corpus. It had one
JSON Schema for canonical run records, human-facing policy documentation, and
heterogeneous TSV/JSON transfer evidence. It had no query process, database,
idempotent ingest contract, lineage traversal, or mutable location index.

Findings:

1. All eight Git-tracked `runs/*/*/run.json` records validate against
   `schemas/run.schema.json`, including the pre-existing modified MSK 40KO
   record in the current worktree.
2. Two pre-existing untracked feature-repair `run.json` files use an operation
   record shape rather than the canonical run schema. The importer reports and
   skips them. They need either a separate operation schema or conversion before
   they can be indexed as canonical runs.
3. Dataset release manifests use several incompatible column layouts. Some are
   conventional headered TSV files; two SLAM-seq manifests are file inventories
   without a common artifact header. Inferring a complete release index from
   those files would be unsafe without format-specific adapters.
4. Several records contain destination paths described as Globus paths but no
   collection UUID. A path alone cannot identify a Globus location. The importer
   preserves these as unresolved archive URIs and does not invent mappings.
5. Existing top-level input and output records are sufficient to construct
   conservative run-level lineage. They are not always sufficient to recover
   sample-level or command-level derivations.

No existing completed run record, release manifest, or handoff file was changed
by the service implementation.

## New Service Review

The service uses an immutable event log and transactionally maintained SQLite
views. The following properties were reviewed and tested:

- identical event retries are idempotent;
- conflicting content under an existing event ID is rejected;
- a failed event projection rolls back the entire batch and event log;
- artifact identity is immutable after registration;
- location and transfer reports require increasing revisions;
- transfer and release status regressions are rejected;
- derivation traversal is cycle-bounded and depth-bounded;
- local reconciliation resolves symlinks and rejects paths outside the artifact
  root before reading them;
- bearer-token comparison uses constant-time comparison;
- SQL query interpolation is limited to internally selected column names and
  generated placeholders; caller values remain bound parameters;
- the wheel contains only the service package and includes `schema.sql`;
- source records are read-only inputs to the deterministic importer.

## Verification

- Repository test suite: 14 passed.
- Clean Python 3.10 virtual environment: 14 passed.
- Host Python 3.11 environment: 14 passed.
- Wheel build: passed; `provenance_service/schema.sql` present.
- Live Uvicorn smoke test: health, event schemas, search, release lookup, and
  lineage lookup returned HTTP 200 against 220 imported events.
- Globus visibility: endpoint
  `07446cad-33b8-11f0-8c0c-0afffb017b7d` listed the new artifact root and its
  three managed subdirectories.

The host's unmanaged Python 3.10 site-packages contains FastAPI 0.115.8 with
incompatible Starlette 1.0.0. The project therefore pins compatible dependency
ranges and must be installed in its virtual environment as documented.

## Residual Limits

These are deliberate integration or production follow-ups, not hidden service
behavior:

- SQLite supports one standalone service instance; multi-replica production
  requires a PostgreSQL adapter and migration plan.
- Read-side authorization is limited to loopback/network controls in this
  phase. Workbench identity forwarding and per-project ACLs are not implemented.
- Globus task polling and Globus Search projection are not implemented yet.
- Existing release manifests are not exhaustively imported; run-linked releases
  enter as conservative `candidate` records with top-level output membership.
- The two noncanonical repair records are skipped pending an operation schema.
- Search is a relational substring query and is not intended as the final
  high-volume text index.

## Review Result

The standalone service is suitable for repository-local testing and the next
Workbench integration phase. It should not be promoted to a multi-user or
multi-replica production deployment until the residual authorization and
PostgreSQL work is complete.
