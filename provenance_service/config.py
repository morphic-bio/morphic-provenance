from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from . import __version__


@dataclass(frozen=True)
class Settings:
    database_path: Path
    artifact_root: Path
    api_token: str | None = None
    bind_host: str = "127.0.0.1"
    port: int = 8090

    @classmethod
    def from_env(cls, base_dir: Path | None = None) -> "Settings":
        base = (base_dir or Path.cwd()).resolve()
        database_path = Path(
            os.environ.get("PROVENANCE_DATABASE_PATH", base / "var/provenance.sqlite3")
        ).expanduser()
        artifact_root = Path(
            os.environ.get("PROVENANCE_ARTIFACT_ROOT", base / "var/globus-artifacts")
        ).expanduser()
        return cls(
            database_path=database_path,
            artifact_root=artifact_root,
            api_token=os.environ.get("PROVENANCE_API_TOKEN") or None,
            bind_host=os.environ.get("PROVENANCE_BIND_HOST", "127.0.0.1"),
            port=int(os.environ.get("PROVENANCE_PORT", "8090")),
        )

    def initialize_artifact_root(self) -> Path:
        root = self.artifact_root.resolve()
        if root.exists() and not root.is_dir():
            raise RuntimeError(f"artifact root is not a directory: {root}")
        root.mkdir(parents=True, exist_ok=True)
        for name in ("incoming", "releases", "quarantine"):
            (root / name).mkdir(exist_ok=True)

        marker = root / ".provenance-root.json"
        marker_payload = {
            "schema_version": "1",
            "service": "morphic-provenance",
            "service_version": __version__,
        }
        if marker.exists():
            existing = json.loads(marker.read_text(encoding="utf-8"))
            if existing.get("service") != "morphic-provenance":
                raise RuntimeError(f"artifact root has an incompatible marker: {marker}")
        else:
            marker.write_text(
                json.dumps(marker_payload, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        return root

    def public_dict(self) -> dict[str, object]:
        return {
            "database_path": str(self.database_path.resolve()),
            "artifact_root": str(self.artifact_root.resolve()),
            "write_auth_required": self.api_token is not None,
            "bind_host": self.bind_host,
            "port": self.port,
        }
