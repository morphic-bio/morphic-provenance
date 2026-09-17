#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def post(url: str, payload: dict) -> dict:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--api", default="http://127.0.0.1:8010")
    parser.add_argument("--poll-seconds", type=int, default=15)
    parser.add_argument("--timeout-seconds", type=int, default=28800)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    payload = json.loads(args.request.read_text())
    started = post(f"{args.api}/start_staged_slurm_gpu_workflow", payload)
    (args.output_dir / "start_response.json").write_text(
        json.dumps(started, indent=2, sort_keys=True) + "\n"
    )

    query = {
        "workflow_id": started["workflow_id"],
        "run_id": started.get("run_id"),
    }
    deadline = time.monotonic() + args.timeout_seconds
    history = args.output_dir / "status_history.jsonl"
    while True:
        status = post(f"{args.api}/staged_slurm_gpu_workflow_status", query)
        record = {"observed_utc": utc_now(), "status": status}
        with history.open("a") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
        (args.output_dir / "final_status.json").write_text(
            json.dumps(record, indent=2, sort_keys=True) + "\n"
        )
        state = status.get("workflow_status")
        stage = status.get("current_stage", "")
        print(f"{record['observed_utc']} state={state} stage={stage}", flush=True)
        if state == "Finished":
            return
        if state in {"Failed", "Canceled", "Terminated", "TimedOut"}:
            raise SystemExit(f"workflow ended in {state}")
        if time.monotonic() >= deadline:
            raise SystemExit("monitor timeout")
        time.sleep(args.poll_seconds)


if __name__ == "__main__":
    main()
