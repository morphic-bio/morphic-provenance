from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import pytest

from provenance_service.config import Settings
from provenance_service.service import ProvenanceService


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        database_path=tmp_path / "index.sqlite3",
        artifact_root=tmp_path / "globus-artifacts",
    )


@pytest.fixture
def service(settings: Settings) -> ProvenanceService:
    instance = ProvenanceService(settings)
    instance.initialize()
    return instance


@pytest.fixture
def event_factory() -> Callable[[str, str, dict[str, Any]], dict[str, Any]]:
    def make(event_id: str, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "event_id": event_id,
            "event_type": event_type,
            "occurred_at": "2026-07-17T12:00:00Z",
            "actor": "pytest",
            "source": "morphic-provenance-tests",
            "payload": payload,
        }

    return make
