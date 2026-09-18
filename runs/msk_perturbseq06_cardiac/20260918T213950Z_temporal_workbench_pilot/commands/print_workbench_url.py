#!/usr/bin/env python3
from pathlib import Path
from urllib.parse import urlencode

bundle = Path(
    "/mnt/pikachu/morphic-provenance-msk-temporal-workbench/runs/"
    "msk_perturbseq06_cardiac/20260918T213950Z_temporal_workbench_pilot/"
    "outputs/workbench-bundle.json"
)
query = urlencode(
    {
        "bundle_path": str(bundle),
        "scheduler_url": "http://127.0.0.1:8010",
    }
)
print(f"http://128.208.252.233:8894/react?{query}")
