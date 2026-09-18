#!/usr/bin/env python3
"""Validate the rendered request with the pinned temporal-scheduler parser."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scheduler-repo", type=Path, required=True)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    os.environ.setdefault("TEMPORAL_ENDPOINT_URL", "localhost:7233")
    sys.path.insert(0, str(args.scheduler_repo.resolve()))
    from bwb.scheduling_service.main import _staged_slurm_gpu_params

    payload = json.loads(args.request.read_text())
    params = _staged_slurm_gpu_params(payload)
    checks = {
        "stage_in_item_count": len(params.stage_in.items) == 5,
        "slurm_present": params.slurm is not None,
        "slurm_cpus": params.slurm.job.resource_req.cpus == 32,
        "stage_back_item_count": len(params.stage_back.items) == 5,
        "gpu_present": params.gpu is not None,
        "gpu_cuda": "--cuda" in params.gpu.job.cmd,
        "publish_item_count": len(params.publish.items) == 1,
    }
    result = {
        "schema": "morphic.scheduler-payload-parser-validation/v1",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "scheduler_commit": "2e35bcc",
        "submitted": False,
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
