from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError

from .api import create_app
from .config import Settings
from .errors import ServiceError
from .importer import build_repository_events
from .models import EventEnvelope
from .service import ProvenanceService


def _load_jsonl(path: Path) -> list[EventEnvelope]:
    events: list[EventEnvelope] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            try:
                events.append(EventEnvelope.model_validate_json(line))
            except (ValueError, ValidationError) as exc:
                raise ValueError(f"{path}:{line_number}: invalid event: {exc}") from exc
    if not events:
        raise ValueError(f"{path}: no events found")
    return events


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="morphic-provenance")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("init", help="initialize the database and artifact root")
    subparsers.add_parser("check", help="check database and artifact-root readiness")
    ingest = subparsers.add_parser("ingest-jsonl", help="ingest an event JSONL sidecar")
    ingest.add_argument("path", type=Path)
    repository_import = subparsers.add_parser(
        "import-repository", help="index canonical run records from this repository"
    )
    repository_import.add_argument("path", nargs="?", type=Path, default=Path.cwd())
    repository_import.add_argument("--dry-run", action="store_true")
    subparsers.add_parser("serve", help="run the HTTP service")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    settings = Settings.from_env()
    service = ProvenanceService(settings)
    try:
        if args.command == "init":
            service.initialize()
            print(json.dumps({"status": "initialized", **settings.public_dict()}, indent=2))
        elif args.command == "check":
            service.initialize()
            print(json.dumps({**service.health(), **settings.public_dict()}, indent=2))
        elif args.command == "ingest-jsonl":
            service.initialize()
            events = _load_jsonl(args.path)
            results = service.ingest_batch(events)
            print(
                json.dumps(
                    {
                        "events": len(results),
                        "inserted": sum(item["status"] == "inserted" for item in results),
                        "duplicates": sum(item["status"] == "duplicate" for item in results),
                    },
                    indent=2,
                )
            )
        elif args.command == "import-repository":
            plan = build_repository_events(args.path)
            if args.dry_run:
                results = []
            else:
                service.initialize()
                results = service.ingest_batch(plan.events) if plan.events else []
            print(
                json.dumps(
                    {
                        "records": plan.records,
                        "events": len(plan.events),
                        "inserted": sum(item["status"] == "inserted" for item in results),
                        "duplicates": sum(item["status"] == "duplicate" for item in results),
                        "skipped": plan.skipped,
                        "dry_run": args.dry_run,
                    },
                    indent=2,
                )
            )
        elif args.command == "serve":
            import uvicorn

            uvicorn.run(create_app(settings), host=settings.bind_host, port=settings.port)
    except (OSError, RuntimeError, ServiceError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
