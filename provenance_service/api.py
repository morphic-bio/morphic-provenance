from __future__ import annotations

import hmac
from typing import Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Response
from fastapi.responses import JSONResponse

from .config import Settings
from .errors import ServiceError
from .models import EventBatch, EventEnvelope, SearchRequest
from .models import PAYLOAD_MODELS
from .service import ProvenanceService


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or Settings.from_env()
    service = ProvenanceService(resolved_settings)
    service.initialize()

    app = FastAPI(
        title="Morphic Provenance Index",
        version="0.1.0",
        description="Append-only provenance events and queryable artifact lineage.",
    )
    app.state.service = service
    app.state.settings = resolved_settings

    @app.exception_handler(ServiceError)
    async def service_error_handler(_request, exc: ServiceError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    def get_service() -> ProvenanceService:
        return app.state.service

    def require_writer(authorization: str | None = Header(default=None)) -> None:
        expected = resolved_settings.api_token
        if expected is None:
            return
        scheme, _, supplied = (authorization or "").partition(" ")
        if scheme.lower() != "bearer" or not hmac.compare_digest(supplied, expected):
            raise HTTPException(status_code=401, detail="valid bearer token required")

    @app.get("/healthz")
    def health(current: ProvenanceService = Depends(get_service)) -> dict:
        return current.health()

    @app.get("/v1/config")
    def config() -> dict:
        return resolved_settings.public_dict()

    @app.get("/v1/event-types")
    def event_types() -> dict:
        return {
            "event_types": {
                event_type: model.model_json_schema()
                for event_type, model in sorted(PAYLOAD_MODELS.items())
            }
        }

    @app.post("/v1/events", dependencies=[Depends(require_writer)])
    def ingest_event(
        event: EventEnvelope,
        response: Response,
        current: ProvenanceService = Depends(get_service),
    ) -> dict:
        result = current.ingest(event)
        response.status_code = 201 if result["status"] == "inserted" else 200
        return result

    @app.post("/v1/events/batch", dependencies=[Depends(require_writer)])
    def ingest_batch(
        batch: EventBatch, current: ProvenanceService = Depends(get_service)
    ) -> dict:
        results = current.ingest_batch(batch.events)
        return {
            "results": results,
            "inserted": sum(result["status"] == "inserted" for result in results),
            "duplicates": sum(result["status"] == "duplicate" for result in results),
        }

    @app.get("/v1/events/{event_id:path}")
    def get_event(event_id: str, current: ProvenanceService = Depends(get_service)) -> dict:
        return current.get_event(event_id)

    @app.get("/v1/artifacts/{artifact_id:path}/lineage")
    def get_lineage(
        artifact_id: str,
        direction: Literal["upstream", "downstream"] = "upstream",
        max_depth: int = Query(default=10, ge=1, le=20),
        current: ProvenanceService = Depends(get_service),
    ) -> dict:
        return current.lineage(artifact_id, direction, max_depth)

    @app.get("/v1/artifacts/{artifact_id:path}")
    def get_artifact(artifact_id: str, current: ProvenanceService = Depends(get_service)) -> dict:
        return current.get_artifact(artifact_id)

    @app.post("/v1/search")
    def search(request: SearchRequest, current: ProvenanceService = Depends(get_service)) -> dict:
        return current.search(request)

    @app.get("/v1/releases/{release_id:path}")
    def get_release(release_id: str, current: ProvenanceService = Depends(get_service)) -> dict:
        return current.get_release(release_id)

    @app.post(
        "/v1/locations/{location_id:path}/reconcile", dependencies=[Depends(require_writer)]
    )
    def reconcile_location(
        location_id: str,
        compute_sha256: bool = False,
        current: ProvenanceService = Depends(get_service),
    ) -> dict:
        return current.reconcile_location(location_id, compute_sha256=compute_sha256)

    return app
