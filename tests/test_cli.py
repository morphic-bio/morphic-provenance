from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def run_cli(repo_root: Path, env: dict[str, str], *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "provenance_service", *args],
        cwd=repo_root,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_cli_init_check_and_idempotent_jsonl_ingest(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PROVENANCE_DATABASE_PATH"] = str(tmp_path / "cli.sqlite3")
    env["PROVENANCE_ARTIFACT_ROOT"] = str(tmp_path / "globus-artifacts")

    initialized = run_cli(repo_root, env, "init")
    assert initialized.returncode == 0, initialized.stderr
    assert json.loads(initialized.stdout)["status"] == "initialized"
    assert (tmp_path / "globus-artifacts/.provenance-root.json").is_file()

    fixture = repo_root / "tests/fixtures/example.events.jsonl"
    first = run_cli(repo_root, env, "ingest-jsonl", str(fixture))
    assert first.returncode == 0, first.stderr
    assert json.loads(first.stdout) == {"events": 4, "inserted": 4, "duplicates": 0}
    second = run_cli(repo_root, env, "ingest-jsonl", str(fixture))
    assert second.returncode == 0, second.stderr
    assert json.loads(second.stdout) == {"events": 4, "inserted": 0, "duplicates": 4}

    checked = run_cli(repo_root, env, "check")
    assert checked.returncode == 0, checked.stderr
    assert json.loads(checked.stdout)["event_count"] == 4


def test_cli_rejects_invalid_jsonl_without_partial_ingest(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PROVENANCE_DATABASE_PATH"] = str(tmp_path / "cli.sqlite3")
    env["PROVENANCE_ARTIFACT_ROOT"] = str(tmp_path / "globus-artifacts")
    invalid = tmp_path / "invalid.jsonl"
    invalid.write_text(
        (repo_root / "tests/fixtures/example.events.jsonl").read_text(encoding="utf-8")
        + "{not json}\n",
        encoding="utf-8",
    )
    failed = run_cli(repo_root, env, "ingest-jsonl", str(invalid))
    assert failed.returncode == 1
    checked = run_cli(repo_root, env, "check")
    assert json.loads(checked.stdout)["event_count"] == 0
