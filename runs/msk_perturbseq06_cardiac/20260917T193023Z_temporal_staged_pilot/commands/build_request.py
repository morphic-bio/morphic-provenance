#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


RUN_STAMP = "20260917T193023Z"
PIKACHU_ENDPOINT = "07446cad-33b8-11f0-8c0c-0afffb017b7d"
BRIDGES_ENDPOINT = "d9e522d3-c51e-4037-b375-55ffd155c715"
INPUT_ROOT = Path("/mnt/pikachu/MSK_Perturbseq06_Cardiac_pilot_inputs_20260917")
LOCAL_ROOT = Path(f"/mnt/pikachu/MSK_Perturbseq06_Cardiac_temporal_pilot_{RUN_STAMP}")
OCEAN_ROOT = Path(f"/ocean/projects/bio230034p/lhung2/temporal-cardiac-pilot-{RUN_STAMP}")
GLOBUS = "/home/lhhung/.local/bin/globus"
FASTQS = (
    "CP_R1_mRNA_IGO_18593_2_S45_L007_R1_001.fastq.gz",
    "CP_R1_mRNA_IGO_18593_2_S45_L007_R2_001.fastq.gz",
    "CP_gRNA_IGO_17967_B_4_S38_L005_R1_001.fastq.gz",
    "CP_gRNA_IGO_17967_B_4_S38_L005_R2_001.fastq.gz",
)


def submission_id() -> str:
    return subprocess.check_output(
        [GLOBUS, "task", "generate-submission-id"], text=True
    ).strip()


def transfer(source: str, destination: str, recursive: bool = False) -> dict:
    return {
        "source_path": source,
        "destination_path": destination,
        "recursive": recursive,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--attempt", type=int, default=1)
    parser.add_argument("--skip-stage-in", action="store_true")
    args = parser.parse_args()
    if args.attempt < 1:
        raise SystemExit("--attempt must be at least 1")
    commands_dir = Path(__file__).resolve().parent
    slurm_script = (commands_dir / "slurm_cardiac_subsample.sh").read_text()

    stage_in_items = [
        transfer(str(INPUT_ROOT / name), str(OCEAN_ROOT / "input" / name))
        for name in FASTQS
    ]
    stage_back_items = [
        transfer(
            str(OCEAN_ROOT / "results/slurm/run/outs/raw_feature_bc_matrix/") ,
            str(LOCAL_ROOT / "slurm/raw_feature_bc_matrix/"),
            True,
        ),
        transfer(
            str(OCEAN_ROOT / "results/slurm/SLURM_COMPLETE.json"),
            str(LOCAL_ROOT / "slurm/SLURM_COMPLETE.json"),
        ),
        transfer(
            str(OCEAN_ROOT / "results/slurm/run/Log.final.out"),
            str(LOCAL_ROOT / "slurm/Log.final.out"),
        ),
        transfer(
            str(OCEAN_ROOT / "results/slurm/RUN_COMMAND.sh"),
            str(LOCAL_ROOT / "slurm/RUN_COMMAND.sh"),
        ),
        transfer(
            str(OCEAN_ROOT / "results/slurm/time.txt"),
            str(LOCAL_ROOT / "slurm/time.txt"),
        ),
    ]

    attempt_suffix = "" if args.attempt == 1 else f"-attempt{args.attempt}"
    stage_in_submission_id = None if args.skip_stage_in else submission_id()
    payload = {
        "workflow_id": f"msk-cardiac-staged-pilot-{RUN_STAMP}{attempt_suffix}",
        "task_queue": f"cardiac-staged-pilot-{RUN_STAMP}",
        "stage_in": {
            "source_endpoint_id": PIKACHU_ENDPOINT,
            "destination_endpoint_id": BRIDGES_ENDPOINT,
            "items": stage_in_items,
            "label": f"MSK Cardiac Temporal pilot stage-in {RUN_STAMP}{attempt_suffix}",
            "submission_id": stage_in_submission_id,
            "poll_interval_seconds": 15,
            "timeout_seconds": 21600,
        },
        "slurm": {
            "task_queue": "lhung2@bridges2.psc.edu:22",
            "poll_interval_seconds": 15,
            "timeout_seconds": 21600,
            "job": {
                "name": "cardiac-temporal-pilot",
                "script": slurm_script,
                "resources": {"cpus": 32, "gpus": 0, "mem_mb": 65536},
                "config": {
                    "partition": "RM-shared",
                    "time": "04:00:00",
                    "nodes": 1,
                    "ntasks": 1,
                    "cpus_per_task": 32,
                    "mem": "64G",
                },
            },
        },
        "stage_back": {
            "source_endpoint_id": BRIDGES_ENDPOINT,
            "destination_endpoint_id": PIKACHU_ENDPOINT,
            "items": stage_back_items,
            "label": f"MSK Cardiac Temporal pilot stage-back {RUN_STAMP}{attempt_suffix}",
            "submission_id": submission_id(),
            "poll_interval_seconds": 15,
            "timeout_seconds": 21600,
        },
        "gpu": {
            "task_queue": "lhhung@localhost:22",
            "job": {
                "image": "biodepot/cellbender:0.3.2",
                "cmd": [
                    "cellbender",
                    "remove-background",
                    "--input",
                    "raw_feature_bc_matrix",
                    "--output",
                    "output/cellbender_counts.h5",
                    "--checkpoint",
                    "output/ckpt.tar.gz",
                    "--cuda",
                    "--expected-cells",
                    "300",
                    "--total-droplets-included",
                    "3000",
                    "--epochs",
                    "10",
                    "--low-count-threshold",
                    "2",
                    "--exclude-feature-types",
                    "CRISPR Guide Capture",
                ],
                "input_files": {
                    str(LOCAL_ROOT / "slurm/raw_feature_bc_matrix"): "raw_feature_bc_matrix"
                },
                "use_gpu": True,
                "gpu_device": "0",
                "min_gpu_free_mb": 6000,
                "gpu_wait_timeout_seconds": 7200,
                "timeout_seconds": 7200,
                "local_output_dir": str(LOCAL_ROOT / "gpu"),
                "cleanup": True,
            },
        },
        "publish": {
            "source_endpoint_id": PIKACHU_ENDPOINT,
            "destination_endpoint_id": BRIDGES_ENDPOINT,
            "items": [
                transfer(
                    str(LOCAL_ROOT / "gpu/"),
                    str(OCEAN_ROOT / "results/published/"),
                    True,
                )
            ],
            "label": f"MSK Cardiac Temporal pilot publish {RUN_STAMP}{attempt_suffix}",
            "submission_id": submission_id(),
            "poll_interval_seconds": 15,
            "timeout_seconds": 21600,
        },
    }
    if args.skip_stage_in:
        del payload["stage_in"]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(args.output)


if __name__ == "__main__":
    main()
