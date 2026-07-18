from __future__ import annotations

import json
import subprocess
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


def test_existing_run_records_match_the_repository_schema():
    repo_root = Path(__file__).resolve().parents[1]
    schema = json.loads((repo_root / "schemas/run.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    tracked = subprocess.run(
        ["git", "ls-files", "runs/*/*/run.json"],
        cwd=repo_root,
        check=True,
        text=True,
        capture_output=True,
    ).stdout.splitlines()
    records = [repo_root / path for path in tracked]
    assert records, "expected at least one run record"
    failures = []
    for record in records:
        errors = sorted(
            validator.iter_errors(json.loads(record.read_text(encoding="utf-8"))),
            key=lambda error: list(error.path),
        )
        failures.extend(
            f"{record.relative_to(repo_root)}:{'/'.join(map(str, error.path))}: {error.message}"
            for error in errors
        )
    assert not failures, "\n".join(failures)
